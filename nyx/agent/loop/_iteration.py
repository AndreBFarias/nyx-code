"""Mixin com métodos de iteração do AgentLoop.

Separa do _core.py para manter cada arquivo abaixo de 400 linhas.
Este mixin NÃO funciona isolado -- espera atributos injetados por AgentLoop
(_tools, _session, _permissions, _parser, _on_tool, _on_tool_result,
_on_permission, _last_action, _consecutive_skips, _has_results, etc.).
"""

from __future__ import annotations

import asyncio
import inspect
import json
import os
import re
from typing import Any

import httpx

from nyx.agent.context import SUMMARY_REINJECT_PREFIX, cap_summary
from nyx.agent.intent import classify as _classify_intent
from nyx.agent.intent import wants_read_only as _wants_read_only
from nyx.agent.lang_check import is_pt_br
from nyx.agent.loop._constants import (
    ACTION_TO_TOOL,
    CORE_TOOLS,
    LLM_TIMEOUT,
    PRESENTABLE_TOOLS,
    TOOL_KEYWORDS,
    _remap_params,
)
from nyx.agent.models import (
    ActionType,
    AgentAction,
    SessionState,
    SessionStatus,
)
from nyx.agent.permissions import PermissionLevel
from nyx.agent.preflight import check as preflight_check
from nyx.agent.prompt import build_reminder
from nyx.agent.repetition import SkipStrategy, get_skip_strategy
from nyx.agent.sanitize import sanitize_tool_args, strip_result_echo
from nyx.agent.services.logging_service import get_logger
from nyx.agent.tools.base import validate_path as _validate_path
from nyx.agent.tools.plan_mode import is_tool_allowed_in_plan_mode
from nyx.agent.validator import FORGE_PATTERNS
from nyx.agent.validator import validate as post_validate
from nyx.providers.base import ProviderError

logger = get_logger("nyx.agent")


# TUI-AGENT-LOOP-CONVERGE-01: sentinel retornado por _check_repetition no caso
# SkipStrategy.SKIP. O caller PULA a execução e continua o loop (return None)
# SEM passar pelo reset de _consecutive_skips -- a pressão para FORCE_DONE
# acumula. Antes o SKIP retornava None e, como o caller só age em valor truthy,
# a tool executava mesmo (skip morto desde o port) e o reset pós-execução zerava
# o contador, impedindo a convergência (loop até MAX_ITERATIONS).
_SKIP_ACTION = object()


# NYX-OUTPUT-LIMITS-01: heuristica de truncate em resposta de chat.
# Disparada por terminacoes abruptas (virgula, hifen aberto, parenteses aberto)
# em respostas com ao menos 100 caracteres; ignora outputs curtos onde a
# terminacao pode ser legitima ('ok,' '-' rotulos etc.).
_TRUNCATE_SUFFIXES = (",", "-", "(", "—", ":", ";")


def _detect_truncate(text: str) -> bool:
    if not text:
        return False
    stripped = text.rstrip()
    if len(stripped) < 100:
        return False
    return stripped.endswith(_TRUNCATE_SUFFIXES)


# LOOP-REMINDER-LEAK-SUMMARY-01 (#381): guard de SAIDA contra vazamento do bloco
# <system-reminder>...</system-reminder> reinjetado por NYX-PROMPT-REINJECT-01.
# A reinjeção no CONTEXTO é necessária (contra drift do 3b); o que NÃO pode é o
# bloco interno chegar ao texto user-facing (summary/resposta). Quando o modelo
# ecoa o reminder no content, ou o summary é derivado do history bruto, o usuário
# via instruções internas em vez do resultado (achado: Onda de Validação 1, probe c2).
# Regex ancorado nas TAGS EXATAS, não-guloso (cada bloco isolado), DOTALL (o bloco
# é multilinha). Não toca conteudo que apenas contenha '<'/'>' soltos.
# OUTPUT-LEAK-SANITIZE-01 (V08): casa o bloco fechado OU um <system-reminder>
# truncado (sem fechamento) até o fim -- o 3b às vezes regurgita o reminder
# cortado e o `.*?</system-reminder>` antigo não casava (faltava o fecho).
_SYSTEM_REMINDER_BLOCK = re.compile(
    r"<system-reminder>.*?(?:</system-reminder>|\Z)",
    re.DOTALL,
)


def strip_system_reminder(text: str) -> str:
    """Remove qualquer bloco <system-reminder>...</system-reminder> do texto.

    Defesa em profundidade do guard de saida user-facing. Pura e deterministica:
    - input com bloco -> bloco removido, resto preservado (whitespace orfa colapsado);
    - input sem bloco -> retorna identico (mesma string).
    Não desativa a reinjeção no contexto (isso vive em _maybe_inject_reminder).
    """
    if not text or "<system-reminder>" not in text:
        return text
    cleaned = _SYSTEM_REMINDER_BLOCK.sub("", text)
    # Colapsa quebras de linha orfãs deixadas pela remoção do bloco, sem mexer
    # no espacamento interno do texto util restante.
    cleaned = re.sub(r"\n{3,}", "\n\n", cleaned)
    return cleaned.strip()


# OUTPUT-DONE-SUMMARY-RENDER-01 (#388): guard de SAIDA contra o artefato cru do
# done() vazando user-facing. O 3b as vezes emite `done(summary="Lista vazia` sem
# fechar a aspa nem o parêntese; o parser NÃO casa esse malformado e o texto cru
# (`summary="Lista vazia` ou `done(summary="Lista vazia`) cai como content/summary
# final, mostrando o formato interno ao usuário (achado: Onda de Validação 2, img 1).
# Este regex é ANCORADO em ^ -- só dispara quando o texto INTEIRO começa com o
# artefato (`done(`/keyword opcional + `summary=`). Um `summary=` legítimo no MEIO
# de uma resposta natural NÃO casa (^ + ausência de prefixo done/abertura).
# Tolera aspa simples/dupla E aspa não-fechada (pega até o fim via \Z).
_DONE_SUMMARY_ARTIFACT = re.compile(
    r"^\s*(?:done|pronto|feito|concluido|concluído)?\s*\(?\s*"
    r"summary\s*=\s*([\"'])?(.*?)(?:\1|\)|\Z)\s*\)?\s*$",
    re.IGNORECASE | re.DOTALL,
)


def strip_done_summary_artifact(text: str) -> str:
    """Extrai o VALOR do summary quando o texto inteiro e um artefato cru do done().

    Defesa em profundidade, sibling de strip_system_reminder. Pura e deterministica:
    - `summary="Lista vazia`         -> `Lista vazia`   (prefixo + aspa aberta removidos)
    - `done(summary="Lista vazia")`  -> `Lista vazia`
    - `done(summary="X`              -> `X`             (aspa/paren não-fechados)
    - texto normal sem o artefato    -> retorna idêntico (^ não casa)
    - `summary=` vazio               -> retorna idêntico (não apaga o texto)
    Ancorado em ^/$ para nunca tocar um `summary=` legitimo no meio de um texto.
    """
    if not text or "summary" not in text.lower():
        return text
    match = _DONE_SUMMARY_ARTIFACT.match(text)
    if not match:
        return text
    value = (match.group(2) or "").strip().strip("\"'").strip()
    # Valor vazio (ex.: `summary=`) não deve aniquilar a resposta -- preserva o
    # texto original em vez de devolver string vazia.
    return value or text


# NYX-PROMPT-REINJECT-01: cadência default de reinjeção de system-reminder
# canônico no histórico. Sobrescrita via env NYX_REMINDER_EVERY (int > 0).
# Cadência 3 escolhida empiricamente: turnos típicos de qwen2.5-coder:3b com
# tarefa multi-passo encadeiam 3-5 tool calls; reminder a cada 3 mantém
# pedido original e invariantes vivos sem inflar input em chats curtos.
_REMINDER_EVERY_DEFAULT = 3


def _reminder_every() -> int:
    """Lê NYX_REMINDER_EVERY se válido (int >= 1); senão default 3."""
    raw = os.environ.get("NYX_REMINDER_EVERY", "")
    if not raw:
        return _REMINDER_EVERY_DEFAULT
    try:
        n = int(raw)
    except ValueError:
        return _REMINDER_EVERY_DEFAULT
    return n if n >= 1 else _REMINDER_EVERY_DEFAULT


class _IterationMixin:
    """Métodos de iteração/LLM extraídos de AgentLoop."""

    # LOOP-DONE-VERIFY-ARTIFACTS-01 (#351): combate o "done alucinado" -- o 3b
    # declara um arquivo criado sem criar (ex.: README anunciado mas ausente).
    _DONE_REJECT_HINT = (
        "Você ainda NÃO criou nem alterou nenhum arquivo neste turno. NÃO chame "
        "done. Chame a tool write_file (ou edit_file) com o conteúdo de verdade "
        "primeiro; só chame done depois que o arquivo existir."
    )

    # EXEC-CONTRACT-NO-HALLUCINATED-RESULT-01 (V04/V14): o turno pediu ação e o 3b
    # tenta concluir sem ter executado NENHUMA tool. Força a execução real.
    _ACTION_REJECT_HINT = (
        "Você ainda NÃO executou nenhuma ferramenta neste turno. NÃO afirme nem "
        "conclua sem agir. Chame a ferramenta apropriada (read_file, list_files, "
        "run_command ou search) com os parâmetros reais primeiro; só conclua depois "
        "que a ferramenta retornar o resultado de verdade."
    )

    # LOOP-RESULT-NOT-AS-INPUT-01 (V06/C2): o arg reusou o resultado de uma tool
    # anterior como entrada (eco recursivo). Força um arg novo, real.
    _ECHO_REJECT_HINT = (
        "O parâmetro reusa o resultado de uma ferramenta anterior como entrada "
        "(eco). Não cole a saída de uma ferramenta na próxima. Forneça um termo "
        "de busca / comando / conteúdo NOVO e real."
    )

    # EXEC-CONTRACT-TOOL-MATCH-01 (V03): tools que MUTAM o FS. Se o pedido é
    # leitura pura e o modelo chama uma destas, é contradição destrutiva.
    _MUTATING_TOOLS = frozenset(
        {"write_file", "create_file", "edit_file", "multi_edit", "patch"}
    )
    _TOOL_MATCH_HINT = (
        "O pedido é de LEITURA/listagem, não de escrita. Não crie nem sobrescreva "
        "arquivo. Use a ferramenta certa: list_files para listar, read_file para "
        "ler, search para buscar. Refaça com a ferramenta de leitura."
    )

    # SEQ-EDIT-ENFORCE-EDITFILE-01 (V05): content que é um comando shell de
    # redirecionamento (echo '...' >> arquivo) -- o 3b confundiu write_file com
    # run_command. Ancorado no início da linha; exige o redirecionamento.
    _SHELL_AS_CONTENT_RE = re.compile(
        r"^\s*(?:echo|cat|printf|tee|sed|awk)\b.*?(?:>>|>)\s*\S",
        re.IGNORECASE | re.MULTILINE,
    )
    _SEQ_OVERWRITE_HINT = (
        "Esse arquivo JÁ existe e você não o leu nesta sessão. Não sobrescreva às "
        "cegas: leia primeiro com read_file e use edit_file para a alteração "
        "cirúrgica, ou reescreva com o conteúdo COMPLETO (não parcial)."
    )
    _SEQ_SHELL_HINT = (
        "O conteúdo é um comando de shell (redirecionamento), não o conteúdo do "
        "arquivo. Para executar um comando use run_command; para escrever, forneça "
        "o texto real que deve ficar no arquivo."
    )

    # EXEC-CONTRACT-PATH-DRIFT-01: extrai tokens de caminho absoluto/til do
    # pedido do usuário (~/Desktop/x.py, /home/andre/x.py). Conservador: exige
    # a barra e para em espaço/aspas/crase; não casa palavras soltas.
    _USER_PATH_RE = re.compile(r"(?<![\w/])(~/[^\s'\"`]+|/[^\s'\"`]+)")
    _PATH_DRIFT_HINT = (
        "O pedido menciona o arquivo '{pedido}', que fica FORA do projeto. Você "
        "apontou para '{drift}', dentro do repositório, e esse caminho não "
        "existe -- isso cria um arquivo espúrio e a edição não chega ao alvo. "
        "Use o caminho EXATO do pedido ('{pedido}') e edit_file para a alteração "
        "cirúrgica (não sobrescreva às cegas)."
    )

    def _init_done_guard(self, user_input: str) -> None:
        """Arma o guard de done no início do turno: baseline de writes + se o
        pedido é de criar/escrever (intent 'code') ou de qualquer ação de tool
        (intent 'tool-needed': ler/listar/rodar/buscar)."""
        self._turn_writes_baseline = self._session.files_modified_count
        intent = _classify_intent(user_input)
        self._turn_wants_create = intent == "code"
        # EXEC-CONTRACT-NO-HALLUCINATED-RESULT-01 (V04/V14): o turno pediu uma ação
        # de ferramenta (ler/listar/rodar/buscar/criar). Intenção é só SINAL de
        # re-emissão (DESENHO §6), nunca gate único -- a rejeição é 1x/turno.
        self._turn_wants_action = intent in ("code", "tool-needed")
        # Contador de execuções de tool NO TURNO (persiste entre iterações, diferente
        # de _tool_calls_this_turn que reseta por iteração). 0 ao concluir = alucinou.
        self._turn_tool_count = 0
        self._done_rejected = False
        # EXEC-CONTRACT-TOOL-MATCH-01: arma o guard de tool-match (rejeição 1x/turno).
        self._tool_match_rejected = False
        # SEQ-EDIT-ENFORCE-EDITFILE-01: arma o guard de edição sequencial (1x/turno).
        self._seq_edit_rejected = False
        # EXEC-CONTRACT-PATH-DRIFT-01: arma o guard de path-drift (1x/turno).
        self._path_drift_rejected = False

    def _turn_create_unmet(self) -> bool:
        """True se o turno pediu criar/escrever (intent 'code') e nenhum write
        efetivou em relação ao baseline do início do turno.

        Predicado puro de observação -- NÃO consome o gate _done_rejected (que é
        do mecanismo de rejeição-1x do done explícito, 351). Reusado pelo
        FORCE_DONE (344) para tornar o summary honesto sem bloquear o fim do turno
        (ADR-033: forçar o fim é aceitável; mentir sobre o fim, não)."""
        if not getattr(self, "_turn_wants_create", False):
            return False
        baseline = getattr(self, "_turn_writes_baseline", 0)
        wrote = self._session.files_modified_count > baseline
        return not wrote

    def _should_reject_done(self) -> str | None:
        """Rejeita o done UMA vez quando o turno pediu ação mas nada executou de
        verdade. Retorna o HINT a re-emitir, ou None se não deve rejeitar.

        Dois casos (EXEC-CONTRACT-NO-HALLUCINATED-RESULT-01):
        - criar/escrever pedido + nenhum write efetivou (351, existente);
        - QUALQUER ação pedida + ZERO tools executadas no turno (V04/V14 novo):
          ler ~/.bashrc sem read_file, "executado com sucesso" sem run_command.
        Rejeita no máximo 1x/turno; MAX_ITERATIONS é a rede final."""
        if getattr(self, "_done_rejected", False):
            return None
        if self._turn_create_unmet():
            return self._DONE_REJECT_HINT
        if getattr(self, "_turn_wants_action", False) and getattr(self, "_turn_tool_count", 0) == 0:
            return self._ACTION_REJECT_HINT
        return None

    def _tool_match_reject(self, name: str) -> str | None:
        """EXEC-CONTRACT-TOOL-MATCH-01: hint a re-emitir quando o modelo chama uma
        tool MUTANTE mas o pedido era leitura pura. None se não deve rejeitar.
        Rejeita no máximo 1x/turno (flag _tool_match_rejected)."""
        if getattr(self, "_tool_match_rejected", False):
            return None
        if name not in self._MUTATING_TOOLS:
            return None
        if _wants_read_only(getattr(self, "_original_input", "") or ""):
            return self._TOOL_MATCH_HINT
        return None

    def _seq_edit_reject(self, name: str, args: dict) -> str | None:
        """SEQ-EDIT-ENFORCE-EDITFILE-01: hint a re-emitir numa edição sequencial
        insegura. None se não deve rejeitar. Rejeita no máximo 1x/turno.

        Dois casos:
        - shell-como-content: content/new_string é um comando de redirecionamento;
        - overwrite cego: write_file/create_file num arquivo que JÁ existe e não
          foi lido nesta sessão.
        """
        if getattr(self, "_seq_edit_rejected", False):
            return None
        # Shell-como-content (qualquer tool de escrita).
        if name in ("write_file", "create_file", "edit_file"):
            text = args.get("content") or args.get("new_string") or ""
            if isinstance(text, str) and self._SHELL_AS_CONTENT_RE.search(text):
                return self._SEQ_SHELL_HINT
        # Overwrite cego (só write_file/create_file -- edit_file já é cirúrgico).
        if name in ("write_file", "create_file"):
            file_path = args.get("file_path") or args.get("path") or ""
            if isinstance(file_path, str) and file_path.strip():
                try:
                    resolved = _validate_path(file_path, self._project_root)
                except Exception:  # noqa: BLE001 -- resolver falho não deve derrubar o guard
                    return None
                read_set = getattr(self._session, "_files_read", set())
                if resolved.exists() and str(resolved) not in read_set:
                    return self._SEQ_OVERWRITE_HINT
        return None

    def _path_drift_reject(self, name: str, args: dict) -> str | None:
        """EXEC-CONTRACT-PATH-DRIFT-01: em contexto acumulado o 3b re-resolve o
        ~/X do pedido para <project_root>/X, cria arquivo espúrio no repo e a
        edição nunca chega ao alvo. Devolve o HINT a re-emitir, ou None.

        Dispara 1x/turno SOMENTE quando as três condições batem:
        - tool mutante;
        - o arg resolve para DENTRO do project_root e esse alvo NÃO existe;
        - o pedido cita ~/X ou /abs/X FORA do project_root, mesmo basename, cujo
          alvo real EXISTE (ou está em session._files_modified -- criado antes na
          sessão). DESENHO §6: SINAL, nunca gate.
        """
        if getattr(self, "_path_drift_rejected", False):
            return None
        if name not in self._MUTATING_TOOLS:
            return None
        file_path = args.get("file_path") or args.get("path") or ""
        if not isinstance(file_path, str) or not file_path.strip():
            return None
        try:
            resolved = _validate_path(file_path, self._project_root)
        except Exception:  # noqa: BLE001 -- resolver falho não deve derrubar o guard
            return None
        root = os.path.realpath(self._project_root)
        try:
            os.path.realpath(str(resolved))
            resolved.relative_to(root)
        except ValueError:
            return None  # arg já aponta FORA do repo -- path correto, sem drift
        if resolved.exists():
            return None  # alvo in-repo existe -- escrita in-repo plausível
        basename = resolved.name
        modified = getattr(self._session, "_files_modified", set())
        user_input = getattr(self, "_original_input", "") or ""
        for cand in self._USER_PATH_RE.findall(user_input):
            target = os.path.realpath(os.path.expanduser(cand))
            if os.path.basename(target) != basename:
                continue
            if target == root or target.startswith(root + os.sep):
                continue  # o pedido aponta DENTRO do repo -- não há drift
            if os.path.exists(target) or target in modified:
                return self._PATH_DRIFT_HINT.format(pedido=cand, drift=str(resolved))
        return None

    async def _execute_tool_calls(self, tool_calls: list[dict], iteration: int) -> SessionStatus | None:
        """Executa tool calls do LLM. Retorna SessionStatus se done/force_done.

        TUI-FIX-HTTPX-LOOP-AFFINITY-01 (ONDA-33): async para rodar no event
        loop principal do Textual (sem worker thread). A execução bloqueante
        da tool (`self._tools.execute`) vai para `asyncio.to_thread` para não
        congelar a UI; os callbacks (`_on_tool`/`_on_tool_result`) permanecem
        no loop principal -- podem tocar widgets sem `call_from_thread`.
        """
        for tc in tool_calls:
            name = tc["name"]
            # EXEC-CONTRACT-TOOLCALL-SANITIZE-01 (G1, V02/C1): limpa lixo de markdown
            # (crase/aspas/escape `\/`) dos args path-like ANTES de tudo (on_tool,
            # permission, preflight, execute veem o arg ja limpo). Estrutura, não
            # semantica -- a infra corrige o 3b sem adivinhar intencao (ADR-032).
            args = sanitize_tool_args(name, tc["arguments"])
            # LOOP-RESULT-NOT-AS-INPUT-01 (G3): corta o eco -- se o arg reusa o
            # resultado recente de uma tool (V06 write recursivo; C2 pattern=erro),
            # limpa as linhas ecoadas; se a busca/comando virou puro eco, rejeita.
            args, _echo_reject = strip_result_echo(
                name, args, getattr(self, "_recent_tool_outputs", [])
            )
            if _echo_reject:
                logger.warning("[loop] arg é puro eco de resultado anterior: %s", name)
                self._session.add_tool_call(name, args, self._ECHO_REJECT_HINT)
                continue

            # EXEC-CONTRACT-TOOL-MATCH-01 (V03): pediram leitura, o modelo chama
            # escrita -> rejeita 1x + re-emite (não cria lixo nem deixa alucinar).
            tm_hint = self._tool_match_reject(name)
            if tm_hint:
                self._tool_match_rejected = True
                logger.warning("[loop] tool-match: pedido de leitura, tool mutante %s", name)
                self._session.add_tool_call(name, args, tm_hint)
                continue

            # SEQ-EDIT-ENFORCE-EDITFILE-01 (V05): edição sequencial insegura
            # (overwrite cego ou shell-como-content) -> rejeita 1x + re-emite.
            se_hint = self._seq_edit_reject(name, args)
            if se_hint:
                self._seq_edit_rejected = True
                logger.warning("[loop] seq-edit inseguro em %s", name)
                self._session.add_tool_call(name, args, se_hint)
                continue

            # EXEC-CONTRACT-PATH-DRIFT-01: o 3b drifta ~/X (pedido) para
            # <project_root>/X (arg) em contexto acumulado -> rejeita 1x + re-emite
            # com o path do pedido e edit_file (não deixa criar arquivo espúrio).
            pd_hint = self._path_drift_reject(name, args)
            if pd_hint:
                self._path_drift_rejected = True
                logger.warning("[loop] path-drift: arg fora do pedido em %s", name)
                self._session.add_tool_call(name, args, pd_hint)
                continue

            if self._on_tool:
                self._on_tool(name, args)

            if self._tools.is_done(name):
                reject_hint = self._should_reject_done()
                if reject_hint:
                    self._done_rejected = True
                    self._session.add_tool_call(name, args, reject_hint)
                    continue
                summary = strip_done_summary_artifact(
                    strip_system_reminder(args.get("summary", "Tarefa concluída."))
                )
                self._session.add_tool_call(name, args, summary, is_key=True)
                return SessionStatus(
                    state=SessionState.DONE,
                    iterations=iteration,
                    summary=summary,
                )

            if not is_tool_allowed_in_plan_mode(name):
                logger.warning("[loop] bloqueado por plan_mode: %s", name)
                self._session.add_tool_call(
                    name, args, "Bloqueado: modo planejamento ativo. Use exit_plan_mode primeiro."
                )
                continue

            perm = self._permissions.check(name, args)
            if perm == PermissionLevel.DENY:
                logger.warning("[loop] permissão negada: %s", name)
                self._session.add_tool_call(name, args, f"Permissão negada para {name}")
                continue

            if perm in (PermissionLevel.CONFIRM_ONCE, PermissionLevel.ALWAYS_CONFIRM):
                if self._on_permission:
                    approved = self._on_permission(perm, name, args)
                    # TUI-PERMISSION-CONFIRM-01 (ONDA-37): suporta callback ASYNC -- a
                    # TUI abre um ConfirmScreen e espera (push_screen_wait). Callback
                    # síncrono (prompt_toolkit/headless) segue igual. Não muda a
                    # assinatura pública (on_permission já é param de construção).
                    if inspect.isawaitable(approved):
                        approved = await approved
                    if not approved:
                        self._session.add_tool_call(name, args, f"Usuário negou: {name}")
                        continue
                    if perm == PermissionLevel.CONFIRM_ONCE:
                        self._permissions.mark_confirmed(name)

            # LOOP-ACTIONTYPE-FALLBACK-DONE-01: tools fora do enum ActionType
            # (multi_edit, skill, task_*, agent, ask_user, ...) NÃO viram mais
            # ActionType.DONE. Colapsar em DONE quebrava o detector de repetição:
            # is_in_recent/is_semantic chaveiam por action_type.value e o
            # histórico guarda o tool_name real -- "done" nunca casava com
            # "multi_edit", então repetição real passava batido; e tools
            # distintas colapsadas em DONE colidiam falso em is_exact_repeat.
            # Rótulo opaco MCP_TOOL (não-terminal) + o `name` real passado como
            # chave de identidade ao detector. O done que conclui o turno vem SÓ
            # de is_done (tratado acima, ~L129), nunca deste fallback.
            is_canon = name in [a.value for a in ActionType]
            action = AgentAction(
                action_type=ActionType(name) if is_canon else ActionType.MCP_TOOL,
                params=args,
            )
            skip = self._check_repetition(action, tool_name=name)
            if skip is _SKIP_ACTION:
                return None
            if skip:
                return skip

            pf = preflight_check(name, args, self._project_root)
            if not pf.ok:
                reason = "; ".join(pf.errors)
                logger.warning("[loop] preflight bloqueou %s: %s", name, reason)
                self._session.add_tool_call(name, args, f"Bloqueado por validação: {reason}")
                continue
            for warn in pf.warnings:
                logger.info("[loop] preflight aviso para %s: %s", name, warn)

            # HOOKS-DYNAMIC-03: PreToolUse antes da execução. block_on_failure
            # honrado via HookResult.blocked=True -> pula tool (continue).
            hooks = getattr(self, "_hooks", None)
            if hooks is not None:
                try:
                    pre_results = hooks.run(
                        "PreToolUse", {"tool_name": name, "tool_input": args}
                    )
                except Exception as exc:  # noqa: BLE001
                    logger.warning("hook PreToolUse falhou: %s", exc)
                    pre_results = []
                if any(r.blocked for r in pre_results):
                    logger.warning("[loop] hook PreToolUse bloqueou %s", name)
                    self._session.add_tool_call(
                        name, args, f"Bloqueado por hook PreToolUse: {name}"
                    )
                    continue

            import time as _time

            _t0 = _time.monotonic()
            result = await asyncio.to_thread(self._tools.execute, name, args)
            self._tool_durations.setdefault(name, []).append((_time.monotonic() - _t0) * 1000.0)
            self._tool_summary.track(name, args)

            # HOOKS-DYNAMIC-03: PostToolUse com tool_result.
            if hooks is not None:
                try:
                    hooks.run(
                        "PostToolUse",
                        {
                            "tool_name": name,
                            "tool_result": (
                                result.output if result.success else (result.error or "")
                            ),
                        },
                    )
                except Exception as exc:  # noqa: BLE001
                    logger.warning("hook PostToolUse falhou: %s", exc)

            vr = post_validate(name, args, result)
            for warn in vr.warnings:
                logger.info("[loop] validator aviso para %s: %s", name, warn)

            if not result.success:
                self._diagnostics.record_warning("tool", f"{name}: {result.error[:120]}")

            if self._on_tool_result:
                # TUI-ASK-USER-PLUMBING-01: suporta callback ASYNC (espelha
                # _on_permission, ~465-471). A TUI abre um modal e ESPERA a
                # resposta (push_screen_wait, async) no caso ask_user. Callback
                # sync (REPL/headless) retorna None -- isawaitable(None) == False,
                # entao o caminho sync segue byte-identico.
                maybe = self._on_tool_result(
                    name, result.output if result.success else result.error
                )
                if inspect.isawaitable(maybe):
                    await maybe

            self._session.add_tool_call(
                name,
                args,
                result.output if result.success else result.error,
                is_key=name in ("write_file", "edit_file", "create_file", "run_command"),
            )
            self._session.track_files(result.files_read, result.files_modified)
            # NYX-GSD-CHECKPOINTS-01: write-through do tool call em progress.md.
            self._gsd.tool(
                name,
                args,
                result.output if result.success else result.error,
            )
            # NYX-PROMPT-REINJECT-01: contador de tool calls dispara reinjeção
            # periódica em _call_llm. Conta no turno e na sessão.
            self._tool_calls_count = getattr(self, "_tool_calls_count", 0) + 1
            self._tool_calls_this_turn = getattr(self, "_tool_calls_this_turn", 0) + 1
            self._last_action = action
            # LOOP-ACTIONTYPE-FALLBACK-DONE-01: nome real da última ação, usado
            # como `last_key` em is_exact_repeat (distingue tools fora do enum).
            self._last_action_name = name
            self._consecutive_skips = 0
            # EXEC-CONTRACT-NO-HALLUCINATED-RESULT-01: contador de execuções do
            # turno (guard de done V04/V14) -- conta toda tool real executada.
            self._turn_tool_count = getattr(self, "_turn_tool_count", 0) + 1
            if result.success:
                self._has_results = True
                # G3: registra a saída apresentável para o ponto de saída compor.
                if name in PRESENTABLE_TOOLS:
                    self._turn_presentables.append((name, result.output or ""))
                # LOOP-RESULT-NOT-AS-INPUT-01: alimenta o rolling de outputs
                # recentes (cap 3) p/ a detecção de eco no próximo tool_call.
                self._recent_tool_outputs.append(result.output or "")
                self._recent_tool_outputs[:] = self._recent_tool_outputs[-3:]

        return None

    async def _execute_parsed_action(self, action: AgentAction, iteration: int) -> SessionStatus | None:
        """Executa ação extraída pelo parser fallback.

        TUI-FIX-HTTPX-LOOP-AFFINITY-01 (ONDA-33): async pelo mesmo motivo de
        `_execute_tool_calls` -- `self._tools.execute` vai para `to_thread`.
        """
        if action.action_type == ActionType.DONE:
            reject_hint = self._should_reject_done()
            if reject_hint:
                self._done_rejected = True
                self._session.add_tool_call("done", action.params, reject_hint)
                return None  # continua o loop -- força a execução antes do done
            summary = strip_done_summary_artifact(
                strip_system_reminder(action.params.get("summary", "Tarefa concluída."))
            )
            self._session.add_tool_call("done", action.params, summary, is_key=True)
            return SessionStatus(
                state=SessionState.DONE,
                iterations=iteration,
                summary=summary,
            )

        tool_name = ACTION_TO_TOOL.get(action.action_type)
        if not tool_name:
            unrouted = action.action_type.value
            logger.warning("[loop] sem tool para %s", unrouted)
            # ADR-026: nada silencioso. O descarte vira evento visível no chat
            # para que qualquer lacuna futura (enum sem rota) apareça ao
            # usuário/validador, em vez de sumir só no log.
            self._session.add_tool_call(
                unrouted,
                action.params,
                f"ação não roteável: {unrouted} (sem entrada em ACTION_TO_TOOL)",
            )
            return None

        remapped = _remap_params(tool_name, action.params)
        # EXEC-CONTRACT-TOOLCALL-SANITIZE-01 (G1): idem caminho nativo, agora no
        # parser fallback (onde o 3b mais cola lixo de markdown no path).
        remapped = sanitize_tool_args(tool_name, remapped)
        # LOOP-RESULT-NOT-AS-INPUT-01 (G3): idem caminho nativo -- corta o eco no
        # parser fallback antes de executar.
        remapped, _echo_reject = strip_result_echo(
            tool_name, remapped, getattr(self, "_recent_tool_outputs", [])
        )
        if _echo_reject:
            logger.warning("[loop] arg é puro eco (parser): %s", tool_name)
            self._session.add_tool_call(tool_name, remapped, self._ECHO_REJECT_HINT)
            return None

        # EXEC-CONTRACT-TOOL-MATCH-01 (V03): idem caminho nativo, no parser fallback.
        tm_hint = self._tool_match_reject(tool_name)
        if tm_hint:
            self._tool_match_rejected = True
            logger.warning("[loop] tool-match (parser): pedido leitura, tool mutante %s", tool_name)
            self._session.add_tool_call(tool_name, remapped, tm_hint)
            return None

        # SEQ-EDIT-ENFORCE-EDITFILE-01 (V05): idem caminho nativo, no parser fallback.
        se_hint = self._seq_edit_reject(tool_name, remapped)
        if se_hint:
            self._seq_edit_rejected = True
            logger.warning("[loop] seq-edit inseguro (parser) em %s", tool_name)
            self._session.add_tool_call(tool_name, remapped, se_hint)
            return None

        # EXEC-CONTRACT-PATH-DRIFT-01: idem caminho nativo, no parser fallback.
        pd_hint = self._path_drift_reject(tool_name, remapped)
        if pd_hint:
            self._path_drift_rejected = True
            logger.warning("[loop] path-drift (parser): arg fora do pedido em %s", tool_name)
            self._session.add_tool_call(tool_name, remapped, pd_hint)
            return None

        if self._on_tool:
            self._on_tool(tool_name, remapped)

        if not is_tool_allowed_in_plan_mode(tool_name):
            logger.warning("[loop] bloqueado por plan_mode (parser): %s", tool_name)
            self._session.add_tool_call(
                tool_name, remapped, "Bloqueado: modo planejamento ativo. Use exit_plan_mode primeiro."
            )
            return None

        perm = self._permissions.check(tool_name, remapped)
        if perm == PermissionLevel.DENY:
            logger.warning("[loop] permissão negada (parser): %s", tool_name)
            self._session.add_tool_call(tool_name, remapped, f"Permissão negada para {tool_name}")
            return None

        if perm in (PermissionLevel.CONFIRM_ONCE, PermissionLevel.ALWAYS_CONFIRM):
            if self._on_permission:
                approved = self._on_permission(perm, tool_name, remapped)
                # LOOP-FALLBACK-GATES-PARITY-01 (AC1): a TUI instala callback ASYNC
                # (app.py:913). Sem este await, approved era um coroutine truthy --
                # o ConfirmScreen nunca abria e a escrita executava sem confirmação
                # no modo Normal, ainda chamando mark_confirmed e contaminando o
                # caminho nativo pelo resto da sessão. Idêntico ao nativo (L403-404).
                if inspect.isawaitable(approved):
                    approved = await approved
                if not approved:
                    self._session.add_tool_call(tool_name, remapped, f"Usuário negou: {tool_name}")
                    return None
                if perm == PermissionLevel.CONFIRM_ONCE:
                    self._permissions.mark_confirmed(tool_name)

        skip = self._check_repetition(action)
        if skip is _SKIP_ACTION:
            return None
        if skip:
            return skip

        pf = preflight_check(tool_name, remapped, self._project_root)
        if not pf.ok:
            reason = "; ".join(pf.errors)
            logger.warning("[loop] preflight bloqueou %s (parser): %s", tool_name, reason)
            self._session.add_tool_call(tool_name, remapped, f"Bloqueado por validação: {reason}")
            return None
        for warn in pf.warnings:
            logger.info("[loop] preflight aviso para %s: %s", tool_name, warn)

        # LOOP-FALLBACK-GATES-PARITY-01 (AC3): PreToolUse antes da execução, com
        # block_on_failure honrado (HOOKS-DYNAMIC-03). Sem isto, um hook bloqueante
        # do usuário era contornável por qualquer tool_call do parser fallback.
        hooks = getattr(self, "_hooks", None)
        if hooks is not None:
            try:
                pre_results = hooks.run(
                    "PreToolUse", {"tool_name": tool_name, "tool_input": remapped}
                )
            except Exception as exc:  # noqa: BLE001
                logger.warning("hook PreToolUse falhou: %s", exc)
                pre_results = []
            if any(r.blocked for r in pre_results):
                logger.warning("[loop] hook PreToolUse bloqueou %s (parser)", tool_name)
                self._session.add_tool_call(
                    tool_name, remapped, f"Bloqueado por hook PreToolUse: {tool_name}"
                )
                return None

        import time as _time

        _t0 = _time.monotonic()
        result = await asyncio.to_thread(self._tools.execute, tool_name, remapped)
        self._tool_durations.setdefault(tool_name, []).append((_time.monotonic() - _t0) * 1000.0)
        self._tool_summary.track(tool_name, remapped)

        # LOOP-FALLBACK-GATES-PARITY-01 (AC3): PostToolUse com tool_result.
        if hooks is not None:
            try:
                hooks.run(
                    "PostToolUse",
                    {
                        "tool_name": tool_name,
                        "tool_result": (
                            result.output if result.success else (result.error or "")
                        ),
                    },
                )
            except Exception as exc:  # noqa: BLE001
                logger.warning("hook PostToolUse falhou: %s", exc)

        vr = post_validate(tool_name, remapped, result)
        for warn in vr.warnings:
            logger.info("[loop] validator aviso para %s: %s", tool_name, warn)

        if not result.success:
            self._diagnostics.record_warning("tool", f"{tool_name}: {result.error[:120]}")

        if self._on_tool_result:
            self._on_tool_result(tool_name, result.output if result.success else result.error)

        self._session.add_tool_call(
            tool_name,
            remapped,
            result.output if result.success else result.error,
            is_key=tool_name in ("write_file", "edit_file", "create_file", "run_command"),
        )
        self._session.track_files(result.files_read, result.files_modified)
        # NYX-GSD-CHECKPOINTS-01: write-through do tool call (parser fallback).
        self._gsd.tool(
            tool_name,
            remapped,
            result.output if result.success else result.error,
        )
        # NYX-PROMPT-REINJECT-01: contador de tool calls (fallback via parser).
        self._tool_calls_count = getattr(self, "_tool_calls_count", 0) + 1
        self._tool_calls_this_turn = getattr(self, "_tool_calls_this_turn", 0) + 1
        self._last_action = action
        # LOOP-ACTIONTYPE-FALLBACK-DONE-01: no parser fallback o action_type é
        # canônico, então tool_name == action_type.value; mantém last_key coerente.
        self._last_action_name = tool_name
        self._consecutive_skips = 0
        # EXEC-CONTRACT-NO-HALLUCINATED-RESULT-01: idem caminho A (parser fallback).
        self._turn_tool_count = getattr(self, "_turn_tool_count", 0) + 1
        if result.success:
            self._has_results = True
            if tool_name in PRESENTABLE_TOOLS:
                self._turn_presentables.append((tool_name, result.output or ""))
            # LOOP-RESULT-NOT-AS-INPUT-01: idem caminho nativo -- rolling cap 3.
            self._recent_tool_outputs.append(result.output or "")
            self._recent_tool_outputs[:] = self._recent_tool_outputs[-3:]

        return None

    def _check_repetition(
        self, action: AgentAction, tool_name: str | None = None
    ) -> SessionStatus | None:
        """Verifica repetição e retorna FORCE_DONE se necessário.

        LOOP-ACTIONTYPE-FALLBACK-DONE-01: `tool_name` é o nome real da tool. Para
        tools fora do enum ActionType (action_type opaco MCP_TOOL) ele é a chave
        de identidade no detector -- sem isso, repetição real escapava e tools
        distintas colidiam. None (ou caminho do parser, onde tool_name ==
        action_type.value) preserva o comportamento canônico da 344.
        """
        key = tool_name if tool_name is not None else action.action_type.value
        strategy = get_skip_strategy(
            action=action,
            last_action=self._last_action,
            history=self._session.history,
            files_modified=self._session._files_modified,
            consecutive_skips=self._consecutive_skips,
            has_results=self._has_results,
            key=key,
            last_key=getattr(self, "_last_action_name", None),
        )

        if strategy == SkipStrategy.FORCE_DONE:
            # LOOP-FORCE-DONE-HARDENING-01 (A7): o FORCE_DONE fecha o turno mesmo
            # (rede anti-MAX_ITERATIONS, não-bloqueante por design). Mas se o turno
            # pediu criar/escrever e nenhum write efetivou, o summary deve ser
            # HONESTO -- repetir read_file/list_files até o teto e anunciar sucesso
            # é o "done alucinado" que a 351 corta no done explícito, voltando por
            # esta porta. _turn_create_unmet() é o mesmo predicado do guard, sem o
            # gate de rejeição-1x (aqui não rejeitamos nada; ADR-033).
            repeated = key if key is not None else action.action_type.value
            summary = self._build_force_done_summary(
                create_unmet=self._turn_create_unmet(),
                repeated_action=repeated,
            )
            logger.info("[loop] FORCE_DONE por repetição: %s", summary[:80])
            return SessionStatus(
                state=SessionState.DONE,
                iterations=self._session.iteration,
                summary=summary,
            )

        if strategy == SkipStrategy.SKIP:
            self._consecutive_skips += 1
            logger.info("[loop] SKIP repetição (%d consecutivos)", self._consecutive_skips)
            # Loga o nome real da tool (não action_type.value, que para tools
            # fora do enum seria o rótulo opaco) -- histórico fiel e is_in_recent
            # subsequente continua casando.
            self._session.add_tool_call(
                key,
                action.params,
                f"Ação repetida ignorada ({self._consecutive_skips}x)",
            )
            return _SKIP_ACTION

        return None

    def _maybe_inject_reminder(self) -> None:
        """NYX-PROMPT-REINJECT-01: injeta <system-reminder> periodicamente.

        Cadência primaria por tool calls (cada REMINDER_EVERY). Drift detectado
        (idioma ou alucinacao) força injeção imediata via flag _force_reminder.
        Skip se histórico ainda não tem turno fechado (iter==0/sem tool count).
        """
        force = getattr(self, "_force_reminder", False)
        count = getattr(self, "_tool_calls_count", 0)
        every = getattr(self, "_reminder_every", _REMINDER_EVERY_DEFAULT)
        if not force:
            if count == 0:
                return
            if count % every != 0:
                return
            # Evita reinjetar no mesmo tick (idempotente por turno).
            if getattr(self, "_last_reminder_at_count", -1) == count:
                return
        try:
            reminder = build_reminder(
                self._session,
                self._project_root,
                original_input=getattr(self, "_original_input", None),
                extra=getattr(self, "_reminder_extra", None),
            )
        except Exception as exc:  # noqa: BLE001 -- reminder e best-effort, não derruba loop
            logger.warning("[reinject] build_reminder falhou: %s", exc)
            return
        # System role no histórico via add_user evitaria conflito de schema; usamos
        # add_user com prefixo canônico para que to_messages preserve role=user
        # mas o conteúdo entregue ao modelo seja o bloco system-reminder cru.
        # Modelos OpenAI-compatible aceitam role=user com bloco <system-reminder>;  # noqa-anonimato
        # o que importa é a presença visual do bloco no contexto reduzido.
        self._session.add_user(reminder)
        self._last_reminder_at_count = count
        self._force_reminder = False
        self._reminder_extra = None
        if getattr(self, "_gsd", None):
            try:
                origem = "drift" if force else f"cadencia/{count}"
                self._gsd.write("reminder", f"injetado ({origem})")
            except Exception as exc:  # noqa: BLE001 -- gsd e best-effort
                logger.debug("[reinject] gsd write falhou: %s", exc)
        logger.info(
            "[reinject] system-reminder injetado (tool_calls=%d, force=%s)",
            count,
            force,
        )

    def _detect_drift(self, last_assistant_text: str) -> tuple[bool, str | None]:
        """Detecta drift de idioma (2x EN consecutivo) ou alucinação de sucesso.

        Retorna (drift_detectado, hint_extra) para o próximo reminder. hint vazio
        quando não houve drift.
        """
        text = (last_assistant_text or "").strip()
        if not text:
            return (False, None)

        # Lang drift: 2 turnos consecutivos não-PT-BR.
        try:
            pt_ok = is_pt_br(text)
        except Exception:  # noqa: BLE001 -- detector e heuristico
            pt_ok = True
        if not pt_ok:
            self._lang_drift_streak = getattr(self, "_lang_drift_streak", 0) + 1
            if self._lang_drift_streak >= 2:
                return (
                    True,
                    "- DRIFT DE IDIOMA detectado: responda em PT-BR acentuado SEMPRE.",
                )
        else:
            self._lang_drift_streak = 0

        # Hallucination drift: afirma sucesso sem tool no turno.
        tool_calls_this_turn = getattr(self, "_tool_calls_this_turn", 0)
        if tool_calls_this_turn == 0:
            for pattern in FORGE_PATTERNS:
                if pattern.search(text):
                    return (
                        True,
                        "- NYX-NO-HALLUCINATE: não afirme sucesso sem write_file/edit_file/create_file.",
                    )

        return (False, None)

    async def _call_llm(self) -> dict[str, Any]:
        """Envia request ao proxy com histórico e tools.

        Estratégia de contexto para GPU limitada (num_ctx=4096, RTX 3050 4GB):
        - Histórico curto (<= 4 msgs): envia tudo.
        - Histórico longo (> 4 msgs): envia o resumo compactado (se houver) +
          as últimas 4 (user + tool_call + result + resposta). A janela de 4 é
          uma escolha deliberada de sobrevivência em janela apertada; o resumo
          dá memória de longo prazo barata, capada por SUMMARY_REINJECT_MAX_TOKENS.

        LOOP-COMPACTION-SUMMARY-WIRING-01: o resumo de compact_history (calculado
        em _run_iterations) deixou de ser descartado. Quando a compactação dispara
        (nível >= 1), _run_iterations guarda o resumo capado em self._compacted_summary
        e este ponto o reinjeta como UMA mensagem curta antes das 4 recentes. Sem
        isso, em conversa longa o modelo só via 4 mensagens e a 1ª citação (ex.:
        arquivo mencionado cedo) sumia -- raiz da alucinação que 354/355 mitigam
        por prompt. A armadilha da opção (b) ingênua (anexar o histórico inteiro
        re-serializado, ~84% do num_ctx, medida em RELATORIO_LOOP_CONTEXT_WINDOW_AUDIT_01)
        é evitada por dois guards: só injeta quando há resumo de compactação real
        (nível >= 1) e o bloco é capado por cap_summary (ADR-034, RTX 3050 4GB).
        """
        # NYX-PROMPT-REINJECT-01: reinjeta <system-reminder> antes da request,
        # com base em contagem de tool calls ou drift detectado no turno anterior.
        self._maybe_inject_reminder()

        # UX-LIFECYCLE-01: VRAM check pré-inferência em cold start.
        # Só roda uma vez por sessão. Em CPU mode (_OOM_DEGRADED pelo proxy)
        # ou sem nvidia-smi, retorna ok=True silenciosamente.
        if not getattr(self, "_vram_checked", False):
            self._vram_checked = True
            from nyx.agent.services.lifecycle import Lifecycle

            ok, free_mib = Lifecycle().vram_check()
            if not ok:
                logger.warning("[loop] VRAM insuficiente: %d MiB livres", free_mib)
                return {
                    "error": (
                        f"VRAM insuficiente ({free_mib} MiB livres). "
                        "Feche outros processos GPU ou rode em CPU com NYX_NUM_GPU=0."
                    ),
                    "error_detail": f"vram_free={free_mib}MiB threshold=800MiB",
                }
            if free_mib >= 0:
                logger.info("[loop] VRAM OK: %d MiB livres", free_mib)

        history_msgs = self._session.to_messages()

        # Seleção de tools precisa do user real, não do system_prompt;
        # passamos apenas history para a heurística.
        _probe = list(history_msgs)
        selected_tools = self._select_tools_for_context(_probe)

        # System prompt compacto quando não há tools: economiza ~1.5k tokens
        # de input por turno (PERF-INFERENCE-01).
        if not selected_tools and getattr(self, "_system_prompt_compact", None):
            system_content = self._system_prompt_compact
        else:
            system_content = self._system_prompt

        messages = [{"role": "system", "content": system_content}]

        # Janela fixa de 4 quando o histórico é longo, PRECEDIDA do resumo
        # compactado (LOOP-COMPACTION-SUMMARY-WIRING-01). A compactação efetiva
        # mora em _run_iterations, que guarda o resumo capado em
        # self._compacted_summary quando dispara (nível >= 1). Aqui ele entra como
        # UMA mensagem curta role=user (compatível com o formato de chat) com
        # prefixo canônico, dando memória de longo prazo sem estourar o num_ctx.
        if len(history_msgs) > 4:
            summary = cap_summary(getattr(self, "_compacted_summary", "") or "")
            if summary:
                messages.append(
                    {
                        "role": "user",
                        "content": f"{SUMMARY_REINJECT_PREFIX}\n{summary}",
                    }
                )
            messages.extend(history_msgs[-4:])
            logger.info(
                "[loop] contexto reduzido: %d/%d msgs (resumo=%s)",
                4,
                len(history_msgs),
                "sim" if summary else "não",
            )
        else:
            messages.extend(history_msgs)

        payload: dict[str, Any] = {
            "model": self._model,
            "messages": messages,
            "tools": selected_tools,
        }

        try:
            if self._http_client is None:
                self._http_client = httpx.AsyncClient(timeout=LLM_TIMEOUT)

            r = await self._http_client.post(
                f"{self._proxy_url}/v1/chat/completions",
                json=payload,
            )
            # EXEC-CONTRACT-PROXY-STATUS-BEFORE-JSON-01 (absorve 412): checar o
            # status ANTES de r.json(). Quando o Ollama cai, o proxy propaga
            # ClientConnectorError e o aiohttp (sem middleware) devolve HTTP 500
            # com corpo text/plain -- r.json() estourava JSONDecodeError e
            # mascarava a causa real (Ollama fora) num "erro inesperado" que
            # ainda prometia um traceback nunca escrito. Falha honesta: cita o
            # code e aponta o Ollama. DESENHO §6.
            if r.status_code != 200:
                logger.error("[loop] proxy HTTP %d: %s", r.status_code, r.text[:200])
                return {
                    "error": (
                        f"O proxy de inferência retornou HTTP {r.status_code}. "
                        "O Ollama pode estar fora -- confira com "
                        "'ss -ltnp | grep 1143' e reinicie o stack com ./run.sh."
                    ),
                    "error_detail": f"HTTP {r.status_code}: {r.text[:200]}",
                }

            try:
                data = r.json()
            except json.JSONDecodeError as exc:
                logger.error(
                    "[loop] corpo do proxy não é JSON (HTTP %d): %s",
                    r.status_code,
                    r.text[:200],
                )
                return {
                    "error": (
                        "O proxy respondeu HTTP 200 mas o corpo não é JSON. "
                        "Inspecione ~/.nyx/logs/proxy.log."
                    ),
                    "error_detail": f"{type(exc).__name__}: {r.text[:200]}",
                }

            if "choices" not in data:
                return {
                    "error": "Resposta do proxy sem campo 'choices'. "
                    "Reinicie o proxy com ./run.sh ou inspecione ~/.nyx/logs/proxy.log.",
                    "error_detail": str(data)[:200],
                }

            msg = data["choices"][0]["message"]
            tc = msg.get("tool_calls", [])
            content = msg.get("content", "")

            # TUI-REDESIGN-25-09-PARTE-3: thinking capturado pelo proxy chega
            # como campo aditivo `nyx_reasoning`. Propaga via callback opcional
            # `_on_thinking` (mesmo shape de _on_tool/_on_tool_result). Quando
            # ausente, callsite/proxy não injetou — silêncio é correto.
            reasoning = msg.get("nyx_reasoning", "")
            if reasoning:
                on_thinking = getattr(self, "_on_thinking", None)
                if on_thinking:
                    try:
                        on_thinking(reasoning)
                    except Exception as exc:  # noqa: BLE001 -- callback é best-effort
                        logger.warning("[loop] on_thinking callback falhou: %s", exc)

            # NYX-OUTPUT-LIMITS-01: log warning se resposta parece truncada.
            # Heuristica passiva (so loga); não reissue para não bloquear ciclo.
            if content and not tc and _detect_truncate(content):
                logger.warning(
                    "[loop] possivel truncate (sufixo abrupto): '...%s'",
                    content.rstrip()[-50:],
                )

            if self._collector and content:
                self._collector.reset()
                for char in content:
                    self._collector.feed(char)

            result: dict[str, Any] = {"content": content, "tool_calls": []}
            for call in tc:
                fn = call.get("function", {})
                args = fn.get("arguments", {})
                if isinstance(args, str):
                    try:
                        args = json.loads(args)
                    except json.JSONDecodeError:
                        args = {"raw": args}
                result["tool_calls"].append(
                    {
                        "name": fn.get("name", ""),
                        "arguments": args,
                    }
                )

            return result

        except httpx.TimeoutException as e:
            return {
                "error": f"Proxy de inferência não respondeu em {LLM_TIMEOUT}s. "
                "Verifique se o Ollama e o proxy estão vivos: systemctl status ollama && ss -ltnp | grep 1143",
                "error_detail": f"{type(e).__name__}: {e}",
            }
        except httpx.ConnectError as e:
            return {
                "error": "Conexão recusada pelo proxy de inferência. "
                "Reinicie o stack com ./run.sh ou confira ~/.nyx/logs/proxy.log.",
                "error_detail": f"{type(e).__name__}: {e}",
            }
        except ProviderError as e:
            return {
                "error": f"{e.user_message}" + (f" {e.hint}" if e.hint else ""),
                "error_detail": f"{type(e.cause).__name__ if e.cause else type(e).__name__}: {e.cause or e}",
            }
        except Exception as e:
            # EXEC-CONTRACT-PROXY-STATUS-BEFORE-JSON-01: a mensagem prometia o
            # traceback em nyx.log, mas NADA o logava -- promessa vazia (fere
            # "honestidade na falha", DESENHO §6). logger.exception torna a
            # promessa verdadeira: o traceback de fato aterrissa no log.
            logger.exception("[loop] falha inesperada ao contatar o proxy")
            return {
                "error": f"Falha inesperada ao contatar o proxy: {type(e).__name__}. "
                "Abra ~/.nyx/logs/nyx.log para o traceback completo.",
                "error_detail": f"{type(e).__name__}: {e}",
            }

    async def _try_recovery(self) -> bool:
        """Tenta reiniciar o modelo Ollama após crash."""
        import asyncio

        ollama_base = self._proxy_url.replace("/v1", "").rstrip("/")
        logger.info("[recovery] Aguardando Ollama reiniciar...")
        for attempt in range(3):
            await asyncio.sleep(5)
            try:
                async with httpx.AsyncClient(timeout=30) as client:
                    r = await client.get(f"{ollama_base}/v1/models")
                    if r.status_code == 200:
                        logger.info("[recovery] Proxy respondendo, tentando aquecer modelo...")
                        warmup = await client.post(
                            f"{ollama_base}/v1/chat/completions",
                            json={
                                "model": self._model,
                                "messages": [{"role": "user", "content": "hi"}],
                                "max_tokens": 5,
                            },
                            timeout=120,
                        )
                        if warmup.status_code == 200:
                            logger.info("[recovery] Modelo aquecido, retomando")
                            return True
            except Exception as e:
                logger.warning("[recovery] Tentativa %d falhou: %s", attempt + 1, str(e)[:60])
        return False

    def _select_tools_for_context(self, messages: list[dict]) -> list[dict]:
        """Seleciona tools relevantes baseado no contexto.

        Gating agressivo (PERF-INFERENCE-01):
        - intent do último user = saudacao/chat -> retorna [].
        - intent = comando -> retorna [] (slash sai antes do LLM em fluxo normal).
        - intent = tool-needed -> CORE_TOOLS + ativadas por keyword, cap em 5.

        Tools já usadas anteriormente na sessão permanecem ativadas para
        continuidade (ex: leu README, agora pergunta sobre conteúdo).
        """
        last_user = ""
        for msg in reversed(messages):
            if msg.get("role") == "user":
                content = msg.get("content", "")
                if isinstance(content, str):
                    last_user = content
                break
        intent = _classify_intent(last_user)

        # TOOL-GATING-NO-SUPPRESS-01 (V01): 'chat' NÃO zera mais as tools. O regex
        # de intent nunca cobre todo o PT-BR ("da um fastfetch" caía em chat e o
        # modelo perdia run_command -> alucinava). Suprimir tools fere ADR-032 (a
        # infra deve guiar o modelo a agir, não amarrá-lo). Os intents 'saudacao'
        # e 'comando' seguem sem tools (saudação genuína não precisa; slash sai
        # antes do LLM).
        if intent in ("saudacao", "comando"):
            logger.info("[loop] intent=%s -> tools=[]", intent)
            return []

        text_parts: list[str] = []
        for msg in messages[-4:]:
            if msg.get("role") == "system":
                continue
            content = msg.get("content", "")
            if content:
                text_parts.append(content.lower())
        context_text = " ".join(text_parts)

        selected_names = set(CORE_TOOLS)

        for tool_name, keywords in TOOL_KEYWORDS.items():
            if any(kw in context_text for kw in keywords):
                selected_names.add(tool_name)

        for entry in self._session.history[-3:]:
            if entry.role == "user":
                for tool_name, keywords in TOOL_KEYWORDS.items():
                    if any(kw in entry.content.lower() for kw in keywords):
                        selected_names.add(tool_name)

        for entry in self._session.history:
            if entry.tool_name:
                selected_names.add(entry.tool_name)

        all_defs = self._tools.tool_defs
        selected = [td for td in all_defs if td["function"]["name"] in selected_names]

        # Cap em 5 tools por turno: VRAM-limitada, schemas inflam input.
        # Prioridade: CORE primeiro (preserva read/write/edit/run/etc).
        if len(selected) > 5:
            # MEMORY-INTENT-CLASSIFY-01: write_memory é essencial para o pedido de
            # memória ("lembra que X"); sem prioridade o cap a corta (CORE tem 8 > 5)
            # e a memória nunca grava (achado do estresse ONDA-44).
            from nyx.agent.intent import wants_save_memory as _wsm

            must = {"write_memory"} if _wsm(last_user) else set()
            must_defs = [td for td in selected if td["function"]["name"] in must]
            core_ordered = [
                td for td in selected
                if td["function"]["name"] in CORE_TOOLS and td["function"]["name"] not in must
            ]
            extras = [
                td for td in selected
                if td["function"]["name"] not in CORE_TOOLS and td["function"]["name"] not in must
            ]
            selected = (must_defs + core_ordered + extras)[:5]

        logger.info("[loop] tools selecionadas: %d/%d (intent=%s)", len(selected), len(all_defs), intent)
        return selected


# "A iteração revela o que a intenção escondia." -- anônimo
