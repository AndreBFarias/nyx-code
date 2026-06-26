## 0. SPEC (machine-readable)

```yaml
sprint:
  id: EXEC-CONTRACT-NO-HALLUCINATED-RESULT-01
  title: "Contrato de execução (esqueleto): apresentar o resultado real + nada de sucesso alucinado + parser-fail honesto"
  onda: 48
  prioridade: ALTA
  tipo: Feature
  dependencias: [TOOL-GATING-NO-SUPPRESS-01]
  desbloqueia: [EXEC-CONTRACT-TOOLCALL-SANITIZE-01, LOOP-RESULT-NOT-AS-INPUT-01, EXEC-CONTRACT-TOOL-MATCH-01, SEQ-EDIT-ENFORCE-EDITFILE-01]

  touches:
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/agent/loop/_core.py
      reason: "run() e o único ponto de saida de todos os caminhos -- compor a apresentacao aqui (parte 1) e tratar o parser-fail cru (parte 3, _core.py:459-471)"
      linhas_alvo: "279-334, 459-471"
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/agent/loop/_iteration.py
      reason: "rastrear tools apresentaveis por turno (parte 1) + generalizar o guard de done para ler/listar/rodar (parte 2)"
      linhas_alvo: "163-228, 360-362, 465-467"
  creates: []
  removes: []

  n_to_n_pairs:
    - descrição: "O append de _turn_presentables existe em DOIS caminhos de execução (tool_calls nativo e parser fallback) -- atualizar AMBOS"  # noqa-acento
      paths: [nyx/agent/loop/_iteration.py (_execute_tool_calls), nyx/agent/loop/_iteration.py (_execute_parsed_action)]
    - descrição: "O guard de done e checado em DOIS caminhos (_execute_tool_calls e _execute_parsed_action) -- a generalizacao precisa valer nos dois"  # noqa-acento
      paths: [nyx/agent/loop/_iteration.py (_execute_tool_calls:216), nyx/agent/loop/_iteration.py (_execute_parsed_action:372)]

  forbidden:
    - "Adicionar emoji"
    - "Usar 'print()' fora de cli.py/output.py (ADR-024 render layer)"
    - "Mencao a IA proprietaria (ADR-005)"
    - "Tornar a apresentacao CONDICIONAL a heuristica de 'isto e generico?' -- o dono escolheu FORTE: sempre mostra os dados crus da tool"
    - "Tocar o cap de 5 tools, o gating de saudacao/comando, o bloqueio de segredos, o write_memory ou a cascata OOM (escopo de outras sprints / não quebrar o que funciona)"
    - "Repetir 1 reminder a cada done indefinidamente -- a rejeicao de done e NO MAXIMO 1x por turno (MAX_ITERATIONS e a rede final)"

  tests:
    - cmd: "./run.sh --gauntlet --only rapido"
      timeout: 300
      deve_passar: true
    - cmd: "./run.sh --gauntlet --only contexto"
      timeout: 300
      deve_passar: true

  acceptance_criteria:
    - "PARTE 1 (apresentacao FORTE): apos run_command/list_files/read_file/search/glob com sucesso, o summary final CONTEM a saida real da tool (não a divagacao do 3b)"
    - "PARTE 2 (sem sucesso alucinado): turno que pediu ação e conclui com ZERO tool executada no turno -> done rejeitado 1x + re-emite hint forte; não afirma sucesso sem executar"
    - "PARTE 3 (parser-fail honesto): tool_call cru que o parser não extrai não vaza no summary -- vira mensagem honesta em PT-BR"
    - "Proof runtime as-user: V04 (ler ~/.bashrc mostra conteudo REAL), V14 (fastfetch mostra specs REAIS, não 'executado com sucesso' vazio), V07 (sem JSON cru no chat)"
    - "Acentuacao PT-BR correta em tudo novo; ruff limpo; FAIL_AFTER <= FAIL_BEFORE"
    - "Gauntlet --only rapido E contexto passam 100%"
```

---

# Sprint EXEC-CONTRACT-NO-HALLUCINATED-RESULT-01 — Contrato de execução (esqueleto)

**Status:** CONCLUIDA (2026-06-26)
**Data criação:** 2026-06-26
**Modelo obrigatório:** claude-opus-4-7 (executor-sprint autorizado pelo dono nesta onda)

---

## Contexto do projeto (snapshot — não referência)

> **ADRs relevantes (inline):**
> - **ADR-032 A INFRA CARREGA O MODELO:** a infra GARANTE o comportamento certo do 3b -- não confia nele. "Confiar é barato; garantir é o trabalho." Esta sprint é o coração disso.
> - **ADR-033 A CADEIA NUNCA QUEBRA:** alucinação/formato interno que chega ao usuário = cadeia com buraco.
> - **ADR-034:** feito para quem não tem A100 (RTX 3050 4GB, qwen2.5-coder:3b). O resultado tem de ser garantido pela infra, não pela capacidade do modelo.
> - ADR-009 Acesso Universal, ADR-001 Local First, ADR-006 PT-BR acentuado, ADR-005 Anonimato, ADR-024 Render layer (print só em cli.py/output.py), ADR-014 Testes via Gauntlet, ADR-010 Zero Mocks.
>
> **Estado (2026-06-26):** Python 3.10+, `qwen2.5-coder:3b` no Ollama :11435, proxy :11436. 35 tools, 16 services. ONDA-48: quick wins 393-396 fechadas (gating, identidade, vazamentos de saída, banner). Desenho coeso: `dev-journey/02-architecture/DESENHO_CONTRATO_EXECUCAO.md`. Achados: `dev-journey/07-reports/AUDIT_VALIDACAO_2026_06_26.md` (V04, V07, V14).

---

## Problema

A validação as-user pós-quick-wins (Checkpoint ONDA-48) confirmou: a Nyx agora **age** (fastfetch dispara, cria arquivo no lugar certo), mas **não apresenta** o resultado -- rodou fastfetch e divagou sobre memória; listou e não mostrou os arquivos. E ainda **afirma** resultado sem executar, e **vaza** tool_call cru quando o parser falha.

Três achados runtime literais (AUDIT_VALIDACAO_2026_06_26):

- **V04 READ-HALLUCINATED [ALTA]** -- "leia ~/.bashrc" -> **nenhum** `read_file` (`files_read=0`), descrição genérica do que "um .bashrc faz". O modelo conclui sem ler.
- **V14 DONE-FALSE-SUCCESS [ALTA]** -- "Comando executado com sucesso" / `done` **sem tool call real** no turno. O guard de done (351/363) só cobre criar/escrever -- leitura/comando passam.
- **V07 TOOLCALL-LEAK-RAW [ALTA]** -- o tool_call cru vaza no summary e **nem executa**: `{"name": read_file, "arguments": {...}}` / `read_file(file_path="...")`. O parser não extraiu -> virou texto user-facing.

**Causa-raiz comum (verificada no código):** a cadeia `parser -> loop -> tool -> resposta` confia no que o 3b cospe. Não há um **contrato de execução** que garanta: (a) todo resultado produzido é apresentado; (b) sucesso afirmado = execução real; (c) parser-fail vira falha honesta, não formato interno cru.

Pontos no código (lidos e confirmados nesta sessão):
- **[C] guard de saída:** `_core.py:312-333` (run() saneia o summary) + done guard `_iteration.py:171-228` (`_init_done_guard`/`_turn_create_unmet`/`_should_reject_done` -- hoje SÓ cobrem intent 'code'/criar).
- **[D] parser-fail:** `_core.py:446-471` -- quando `parse_result.success` é False, cai em `detect_forged_success` e devolve o `content` cru como summary (V07).
- **[B->C] apresentação:** os outputs de tool entram no contexto (`_iteration.py:335-344`) mas o summary final é a fala do 3b (done/content), que omite o dado.

---

## Solução proposta

Implantar o **esqueleto do contrato** em 3 partes coordenadas, todas aditivas (não removem o que funciona):

1. **Apresentação FORTE (G3)** -- decisão do dono: para `run_command`/`list_files`/`read_file`/`search`/`glob`, a resposta final SEMPRE inclui a saída real da tool, abaixo da fala do modelo. Rastrear por turno (`_turn_presentables`) e compor no único ponto de saída (`run()`).
2. **Sem sucesso alucinado (G2)** -- generalizar o guard de done: turno que pediu ação (intent 'code' OU 'tool-needed') e tenta concluir com **zero tools executadas no turno** -> rejeitar o done **1x** + re-emitir hint forte forçando a execução real. Cobre V04 e V14.
3. **Parser-fail honesto (G2)** -- no ramo parser-fail (`_core.py:459-471`), se o `content` é um tool_call cru que o parser não conseguiu extrair, NÃO devolvê-lo -- virar mensagem honesta em PT-BR.

Princípios (DESENHO §6): não regex-frágil (intenção é só **sinal** de re-emissão, nunca gate único; a rejeição é 1x); enforcement, não confiança; honestidade na falha.

---

## Arquivos alvo (paths absolutos)

### `/home/andrefarias/Desenvolvimento/Nyx-Code/nyx/agent/loop/_core.py`

#### Edit 1 — constante PRESENTABLE_TOOLS (após `_TOOL_HINT_BRACKET_RE`, ~linha 70)

# Localização aproximada: logo após `_TOOL_HINT_BRACKET_RE = re.compile(...)` (linha 67-70)
**Depois (adicionar):**
```python
# EXEC-CONTRACT-NO-HALLUCINATED-RESULT-01 (V04/V14, G3 apresentacao FORTE): tools
# cuja SAIDA o usuário quer ver crua. Decisao do dono: a resposta final SEMPRE
# inclui o output real destas tools (não a divagacao do 3b). write_file/edit_file
# ficam de fora -- o "OK: criado" delas e status, coberto pelo guard de done (G2).
PRESENTABLE_TOOLS = frozenset(
    {"run_command", "list_files", "read_file", "search", "glob"}
)
```

#### Edit 2 — reset do rastreio por turno em `run()`

# Localização aproximada: dentro de run(), junto do `_init_done_guard` (linha 292-293)
**Antes:**
```python
        # LOOP-DONE-VERIFY-ARTIFACTS-01 (#351): arma o guard de done alucinado.
        self._init_done_guard(user_input)
```
**Depois:**
```python
        # LOOP-DONE-VERIFY-ARTIFACTS-01 (#351): arma o guard de done alucinado.
        self._init_done_guard(user_input)
        # EXEC-CONTRACT-NO-HALLUCINATED-RESULT-01 (G3): saidas apresentaveis
        # produzidas neste turno (tool_name, output). Resetado por turno; consumido
        # por _compose_presentation_summary no único ponto de saida (abaixo).
        self._turn_presentables = []
```

#### Edit 3 — compor apresentação no ponto de saída de `run()`

# Localização aproximada: logo após `status = await self._run_iterations(user_input)` (linha 312), ANTES do guard de saída existente (linha 330)
**Antes:**
```python
            status = await self._run_iterations(user_input)
            # LOOP-REMINDER-LEAK-SUMMARY-01 (#381): guard de SAIDA único. Cobre
```
**Depois:**
```python
            status = await self._run_iterations(user_input)
            # EXEC-CONTRACT-NO-HALLUCINATED-RESULT-01 (G3): APRESENTACAO FORTE.
            # Antes do guard de saida (que so saneia), garantir que a saida real das
            # tools apresentaveis chegue ao usuário -- mesmo que o 3b tenha divagado.
            # Decisao do dono: sempre mostra os dados crus. Os hints de controle
            # eventualmente colados no output (run_command/read_file) sao removidos
            # logo abaixo pelo guard de saida ja existente (_DONE_HINT_RE etc).
            status.summary = self._compose_presentation_summary(status)
            # LOOP-REMINDER-LEAK-SUMMARY-01 (#381): guard de SAIDA único. Cobre
```

#### Edit 4 — método `_compose_presentation_summary` (novo, em AgentLoop)

# Localização aproximada: adicionar como método de AgentLoop, junto de `_build_force_done_summary` (após linha 523)
**Depois (adicionar método):**
```python
    def _compose_presentation_summary(self, status: SessionStatus) -> str:
        """EXEC-CONTRACT-NO-HALLUCINATED-RESULT-01 (G3): anexa a saida real das
        tools apresentaveis do turno ao summary.

        Decisao do dono (FORTE): para run_command/list_files/read_file/search/glob,
        a resposta SEMPRE mostra os dados crus -- a infra não confia que o 3b vai
        apresentar (ADR-032). Unico skip: dedup de substring exata (não re-colar um
        output ja literalmente presente no texto do modelo). Hints de controle no
        output sao limpos pelo guard de saida que roda logo apos esta chamada.
        """
        presentables = getattr(self, "_turn_presentables", None)
        if not presentables:
            return status.summary
        if status.state not in (SessionState.DONE, SessionState.MAX_ITERATIONS):
            return status.summary

        base = (status.summary or "").strip()
        blocks: list[str] = []
        for _name, output in presentables:
            out = (output or "").strip()
            if not out:
                continue
            # Dedup exato: se o modelo ja colou este output, não duplicar.
            if out in base:
                continue
            blocks.append(out[:8000])
        if not blocks:
            return base

        resultado = "\n\n".join(blocks)
        if base:
            return f"{base}\n\nResultado:\n{resultado}"
        return f"Resultado:\n{resultado}"
```

#### Edit 5 — parser-fail honesto (V07)

# Localização aproximada: ramo onde parse falhou e o content vira summary (linha 459-471)
**Antes:**
```python
                forge = detect_forged_success(content, self._session.history)
                final_content = content
                if forge.warnings:
                    self._diagnostics.record_warning("forge", forge.warnings[0])
                    aviso = "[atenção: resposta não verificada por tool]"
                    final_content = f"{content}\n\n{aviso}"
                self._session.add_assistant(final_content)
```
**Depois:**
```python
                forge = detect_forged_success(content, self._session.history)
                final_content = content
                # EXEC-CONTRACT-NO-HALLUCINATED-RESULT-01 (V07, G2 ponto D): o parser
                # falhou em todos os niveis. Se o content e um tool_call cru (JSON
                # `{"name":...}` ou `tool(args)`), não devolve-lo como resposta --
                # vira mensagem honesta. Falhar honesto > vazar formato interno.
                if _looks_like_raw_toolcall(content):
                    self._diagnostics.record_warning("parser", "tool_call cru não executavel")
                    final_content = (
                        "Tentei executar uma ação mas não consegui interpretar o "
                        "formato da chamada. Pode reformular o pedido?"
                    )
                elif forge.warnings:
                    self._diagnostics.record_warning("forge", forge.warnings[0])
                    aviso = "[atenção: resposta não verificada por tool]"
                    final_content = f"{content}\n\n{aviso}"
                self._session.add_assistant(final_content)
```

#### Edit 6 — detector `_looks_like_raw_toolcall` (módulo, junto dos regexes do topo de `_core.py`)

# Localização aproximada: junto de `_TOOL_HINT_BRACKET_RE` / `PRESENTABLE_TOOLS` (topo do arquivo)
**Depois (adicionar):**
```python
# EXEC-CONTRACT-NO-HALLUCINATED-RESULT-01 (V07): heuristica para detectar quando o
# content e um tool_call CRU que o parser não conseguiu extrair (malformado). So
# dispara no ramo parser-fail; ancorada em sinais estruturais fortes, não em prosa.
_RAW_TOOLCALL_NAMES = (
    "read_file|write_file|edit_file|run_command|list_files|search|glob|create_file"
)
_RAW_TOOLCALL_RE = re.compile(
    r'(\{\s*["\']?(?:name|tool|function)["\']?\s*:.*?(?:arguments|args|parameters|file_path|command|path)'
    rf'|\b(?:{_RAW_TOOLCALL_NAMES})\s*\(\s*(?:file_path|path|command|cmd|pattern)?\s*=?)',
    re.IGNORECASE | re.DOTALL,
)


def _looks_like_raw_toolcall(text: str) -> bool:
    """True se o texto e majoritariamente um tool_call cru não-executavel."""
    if not text:
        return False
    return bool(_RAW_TOOLCALL_RE.search(text.strip()))
```

---

### `/home/andrefarias/Desenvolvimento/Nyx-Code/nyx/agent/loop/_iteration.py`

#### Edit 7 — generalizar o guard de done (PARTE 2)

# Localização aproximada: _init_done_guard / _turn_create_unmet / _should_reject_done (linhas 171-197)
**Antes:**
```python
    def _init_done_guard(self, user_input: str) -> None:
        """Arma o guard de done no início do turno: baseline de writes + se o
        pedido é de criar/escrever arquivo (intent 'code')."""
        self._turn_writes_baseline = self._session.files_modified_count
        self._turn_wants_create = _classify_intent(user_input) == "code"
        self._done_rejected = False
```
**Depois:**
```python
    def _init_done_guard(self, user_input: str) -> None:
        """Arma o guard de done no início do turno: baseline de writes + se o
        pedido é de criar/escrever (intent 'code') ou de qualquer ação de tool
        (intent 'tool-needed': ler/listar/rodar/buscar)."""
        self._turn_writes_baseline = self._session.files_modified_count
        intent = _classify_intent(user_input)
        self._turn_wants_create = intent == "code"
        # EXEC-CONTRACT-NO-HALLUCINATED-RESULT-01 (V04/V14): o turno pediu uma ação
        # de ferramenta (ler/listar/rodar/buscar/criar). Intencao e so SINAL de
        # re-emissao (DESENHO §6), nunca gate único -- a rejeicao e 1x/turno.
        self._turn_wants_action = intent in ("code", "tool-needed")
        # Contador de execuções de tool NO TURNO (persiste entre iteracoes, diferente
        # de _tool_calls_this_turn que reseta por iteracao). 0 ao concluir = alucinou.
        self._turn_tool_count = 0
        self._done_rejected = False
```

**Antes (`_should_reject_done`):**
```python
    def _should_reject_done(self) -> bool:
        """Rejeita o done UMA vez se o turno pediu criar/escrever e nenhum write
        efetivou. Rejeita no máximo 1x/turno; MAX_ITERATIONS é a rede final."""
        if getattr(self, "_done_rejected", False):
            return False
        return self._turn_create_unmet()
```
**Depois:**
```python
    def _should_reject_done(self) -> str | None:
        """Rejeita o done UMA vez quando o turno pediu ação mas nada executou de
        verdade. Retorna o HINT a re-emitir, ou None se não deve rejeitar.

        Dois casos (EXEC-CONTRACT-NO-HALLUCINATED-RESULT-01):
        - criar/escrever pedido + nenhum write efetivou (351, existente);
        - QUALQUER ação pedida + ZERO tools executadas no turno (V04/V14 novo):
          ler ~/.bashrc sem read_file, "executado com sucesso" sem run_command.
        Rejeita no maximo 1x/turno; MAX_ITERATIONS e a rede final."""
        if getattr(self, "_done_rejected", False):
            return None
        if self._turn_create_unmet():
            return self._DONE_REJECT_HINT
        if getattr(self, "_turn_wants_action", False) and getattr(self, "_turn_tool_count", 0) == 0:
            return self._ACTION_REJECT_HINT
        return None
```

#### Edit 8 — novo hint + atualizar os 2 callers do guard

# Localização: junto de `_DONE_REJECT_HINT` (linha 165-169)
**Depois (adicionar constante):**
```python
    # EXEC-CONTRACT-NO-HALLUCINATED-RESULT-01 (V04/V14): turno pediu ação e o 3b
    # tenta concluir sem ter executado NENHUMA tool. Forca a execução real.
    _ACTION_REJECT_HINT = (
        "Você ainda NÃO executou nenhuma ferramenta neste turno. NÃO afirme nem "
        "conclua sem agir. Chame a ferramenta apropriada (read_file, list_files, "
        "run_command ou search) com os parâmetros reais primeiro; só conclua depois "
        "que a ferramenta retornar o resultado de verdade."
    )
```

# Caller 1 -- _execute_tool_calls, done handling (linha 215-228)
**Antes:**
```python
            if self._tools.is_done(name):
                if self._should_reject_done():
                    self._done_rejected = True
                    self._session.add_tool_call(name, args, self._DONE_REJECT_HINT)
                    continue
```
**Depois:**
```python
            if self._tools.is_done(name):
                reject_hint = self._should_reject_done()
                if reject_hint:
                    self._done_rejected = True
                    self._session.add_tool_call(name, args, reject_hint)
                    continue
```

# Caller 2 -- _execute_parsed_action, done handling (linha 371-375)
**Antes:**
```python
        if action.action_type == ActionType.DONE:
            if self._should_reject_done():
                self._done_rejected = True
                self._session.add_tool_call("done", action.params, self._DONE_REJECT_HINT)
                return None  # continua o loop -- força o write_file antes do done
```
**Depois:**
```python
        if action.action_type == ActionType.DONE:
            reject_hint = self._should_reject_done()
            if reject_hint:
                self._done_rejected = True
                self._session.add_tool_call("done", action.params, reject_hint)
                return None  # continua o loop -- força a execução antes do done
```

#### Edit 9 — alimentar `_turn_presentables` + `_turn_tool_count` (os 2 caminhos)

# Caminho A -- _execute_tool_calls, apos execução bem-sucedida (linha 359-362)
**Antes:**
```python
            self._consecutive_skips = 0
            if result.success:
                self._has_results = True

        return None
```
**Depois:**
```python
            self._consecutive_skips = 0
            # EXEC-CONTRACT-NO-HALLUCINATED-RESULT-01: contador de execuções do
            # turno (guard de done V04/V14) -- conta toda tool real executada.
            self._turn_tool_count = getattr(self, "_turn_tool_count", 0) + 1
            if result.success:
                self._has_results = True
                # G3: registra a saida apresentavel para o ponto de saida compor.
                if name in PRESENTABLE_TOOLS:
                    self._turn_presentables.append((name, result.output or ""))

        return None
```

# Caminho B -- _execute_parsed_action, apos execução (linha 465-469)
**Antes:**
```python
        self._last_action_name = tool_name
        self._consecutive_skips = 0
        if result.success:
            self._has_results = True

        return None
```
**Depois:**
```python
        self._last_action_name = tool_name
        self._consecutive_skips = 0
        # EXEC-CONTRACT-NO-HALLUCINATED-RESULT-01: idem caminho A (parser fallback).
        self._turn_tool_count = getattr(self, "_turn_tool_count", 0) + 1
        if result.success:
            self._has_results = True
            if tool_name in PRESENTABLE_TOOLS:
                self._turn_presentables.append((tool_name, result.output or ""))

        return None
```

> **Import:** `PRESENTABLE_TOOLS` é definido em `_core.py`. Em `_iteration.py` (mixin), importar
> de `nyx.agent.loop._core` causaria ciclo (`_core` importa `_iteration`). **Definir
> `PRESENTABLE_TOOLS` em `nyx/agent/loop/_constants.py`** (sem ciclo -- `_constants` não importa
> nada do loop) e importar nos dois (`_core.py` e `_iteration.py`). Ajustar os Edits 1/9 para
> importar de `_constants`. Mesma escolha vale para o reset de `_turn_presentables`/`_turn_tool_count`.

---

## Diff esperado (resumo)

```
~ 3 arquivos modificados (nyx/agent/loop/_core.py, _iteration.py, _constants.py)
+ ~75 linhas líquidas (1 metodo novo, 1 helper, 2 constantes, generalizacao do guard)
- 0 removidos
```

---

## Comandos de verificação (literais, copy-paste)

```bash
# 1. Estatica
python -m ruff check nyx/

# 2. Invariantes (antes/depois -- ver proof-of-work)
bash scripts/sprint_invariants.sh

# 3. Acentuacao PT-BR
python3 ~/.config/zsh/scripts/validar-acentuacao.py --paths \
  nyx/agent/loop/_core.py nyx/agent/loop/_iteration.py nyx/agent/loop/_constants.py

# 4. Gauntlet (não pode regredir)
./run.sh --gauntlet --only rapido
./run.sh --gauntlet --only contexto

# 5. PROOF RUNTIME-REAL as-user (o coracao da sprint). Rodar a Nyx de verdade.
#    headless: foreground via pipe (background/sleep dao exit 144).

# V14 -- fastfetch agora MOSTRA as specs reais (não "executado com sucesso" vazio):
printf '%s\n' '{"type":"request","content":"da um fastfetch e me fala as specs do pc atual"}' \
  | NYX_AUTO_APPROVE=1 ./run.sh --headless 2>/dev/null
# ESPERADO: summary com bloco "Resultado:" + specs REAIS (Ryzen 5 7535HS / RTX 3050 / Pop!_OS).

# V04 -- leitura mostra o conteudo REAL do arquivo:
printf '%s\n' '{"type":"request","content":"leia o arquivo ~/.bashrc e me mostre o conteudo"}' \
  | NYX_AUTO_APPROVE=1 ./run.sh --headless 2>/dev/null
# ESPERADO: files_read>=1 E summary com "Resultado:" + linhas REAIS do ~/.bashrc.

# V07 -- nenhum JSON/tool_call cru no summary (sessão acumulada favorece o parser-fail):
#   (rodar uma sequencia de 3-4 pedidos no mesmo processo headless; conferir que
#    nenhum summary contem `{"name":` nem `read_file(file_path=`)

# Cross-check no log (metodo do AUDIT): tools chamadas de verdade
tail -50 ~/.nyx/logs/nyx.log | grep -E "tools selecionadas|FORCE_DONE|parser fallback"
```

---

## Critério binário de aceite (IA executora)

- [ ] `PRESENTABLE_TOOLS` em `_constants.py`; importado em `_core.py` e `_iteration.py` (sem ciclo)
- [ ] `_compose_presentation_summary` chamado em `run()` ANTES do guard de saída existente
- [ ] `_turn_presentables`/`_turn_tool_count` resetados em `run()` e alimentados nos DOIS caminhos de execução
- [ ] `_should_reject_done` retorna hint (str|None); os 2 callers atualizados; rejeição 1x/turno preservada
- [ ] `_looks_like_raw_toolcall` aplicado SÓ no ramo parser-fail; tool_call cru vira mensagem honesta
- [ ] Proof runtime V14 (fastfetch real) e V04 (.bashrc real) colados literalmente; V07 sem JSON cru
- [ ] `ruff` limpo, acentuação rc=0, `FAIL_AFTER <= FAIL_BEFORE`
- [ ] Gauntlet `--only rapido` E `--only contexto` 100%
- [ ] `SPRINT_ORDER_MASTER.md` marca 399 CONCLUIDA; spec movida para `concluidos/`
- [ ] Commit atômico `feat(loop): 399 EXEC-CONTRACT-NO-HALLUCINATED-RESULT-01 -- apresentar resultado real (V04/V07/V14)`

---

## Guardrails anti-engodo (obrigatórios)

NÃO marcar concluída se:
- O proof runtime (fastfetch + .bashrc) não foi colado com **dados reais** (não inventados).
- Tornou a apresentação condicional a "isto é genérico?" (o dono escolheu FORTE: sempre mostra cru).
- "Consertou" V04/V14 endurecendo o regex de intent (a lição da onda: regex não escala; intenção é só sinal de re-emissão).
- Rejeitou o done mais de 1x/turno (loop de reminder) ou quebrou a convergência do FORCE_DONE (344).
- Gauntlet "passou" sem output real; ou regrediu `rapido`/`contexto`.

Se algo falhar: `[SPRINT 399] BLOQUEADA: <motivo 1 linha>`.

---

## Proof-of-work obrigatório (4 passos)

```bash
bash scripts/sprint_invariants.sh > /tmp/inv_before.txt 2>&1
FAIL_BEFORE=$(grep -c "^\[FAIL\]" /tmp/inv_before.txt)
# implementar (Edits 1-9; PRESENTABLE_TOOLS em _constants.py)
bash scripts/sprint_invariants.sh > /tmp/inv_after.txt 2>&1
FAIL_AFTER=$(grep -c "^\[FAIL\]" /tmp/inv_after.txt)
diff /tmp/inv_before.txt /tmp/inv_after.txt
```
Colar: inv_before/inv_after (tail), diff, os JSON dos proofs runtime V14/V04, o grep do log, e `git show --stat HEAD`.

---

## Gambiarras específicas desta sprint

- **Dedup que vira omissão:** o skip "out in base" deve ser substring EXATA -- nunca um "parece presente" fuzzy (re-introduziria a omissão que a sprint mata). Default = mostrar.
- **Reset esquecido:** se `_turn_presentables` não resetar por turno, o turno N mostra o resultado do turno N-1 (alucinação de localização). Resetar em `run()`, sempre.
- **Contador de iteração vs turno:** `_tool_calls_this_turn` reseta por ITERAÇÃO (`_run_iterations:350`) -- NÃO usar para o guard. Usar `_turn_tool_count` (turno inteiro).
- **Ciclo de import:** `_core` importa `_iteration`; definir `PRESENTABLE_TOOLS` em `_core` e importar em `_iteration` quebra. Fonte única = `_constants.py`.

---

## Validação humana (checklist do usuário)

```bash
cd /home/andrefarias/Desenvolvimento/Nyx-Code
git show --stat HEAD
# Rodar a Nyx e pedir "da um fastfetch" e "leia ~/.bashrc":
./run.sh
# ESPERADO: a resposta MOSTRA as specs reais e o conteudo real do arquivo (bloco "Resultado:").
ls dev-journey/06-sprints/concluidos/SPRINT_EXEC_CONTRACT_NO_HALLUCINATED_RESULT_01.md  # existe
ls dev-journey/06-sprints/produção/SPRINT_EXEC_CONTRACT_NO_HALLUCINATED_RESULT_01.md     # não existe
```

---

## Riscos

| Risco | Mitigação |
|-------|-----------|
| Verborragia em pedidos de síntese ("resuma o README" anexa o README cru) | Trade-off ACEITO pelo dono (escolha FORTE). A síntese do 3b é preservada acima do "Resultado:". |
| Duplicação se o 3b já colou o output | Dedup de substring exata (`out in base`) evita re-colar idêntico; divergência sempre mostra. |
| Guard de ação re-emite em chat legítimo misclassificado como tool-needed | Custo = 1 re-emit no máximo (rejeição 1x/turno); intenção é sinal, não gate. |
| `_looks_like_raw_toolcall` falso-positivo em prosa que cita uma tool | Ancorado em sinais estruturais fortes (`{"name":...`, `tool(arg=`); só roda no ramo parser-fail (raro). |
| read_file grande infla o summary | Cap de 8000 por bloco (espelha o cap do run_command). |

---

*"Confiar é barato; garantir é o trabalho. A infra que serve quem não tem A100 garante." -- princípio de execução (dev-journey/02-architecture/DESENHO_CONTRATO_EXECUCAO.md)*
