## 0. SPEC (machine-readable)

```yaml
sprint:
  id: EXEC-CONTRACT-PATH-DRIFT-01
  numero: 437
  title: "Guard de path-drift: quando o 3b re-resolve ~/X para <project_root>/X em contexto acumulado, rejeita 1x + re-emite com o path do pedido"
  onda: 48
  prioridade: ALTA
  tipo: Bugfix
  dependencias: []
  desbloqueia: []
  absorve: []

  touches:
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/agent/loop/_iteration.py
      reason: "novo guard _path_drift_reject (irmão de _seq_edit_reject/_tool_match_reject), armado em _init_done_guard e ligado nos dois caminhos de execução (nativo e parser fallback); regex de extração de path do pedido + hint"
      linhas_alvo: "227-246 (_init_done_guard), 290-317 (bloco dos guards de rejeição), 355-362 (wiring nativo), 586-592 (wiring parser fallback), topo do bloco de constantes de guard (~200-225)"
  creates: []
  removes: []

  forbidden:
    - "Adicionar emoji"
    - "Usar 'print()' fora de cli.py/output.py"
    - "Mencao a IA proprietaria"
    - "Tocar validate_path em nyx/agent/tools/base.py (a resolução de path está CORRETA -- o drift é do modelo, o fix é o guard que o detecta)"
    - "Tocar os guards existentes (397/398/399/400/401): _tool_match_reject, _seq_edit_reject, _should_reject_done ficam byte-identicos"
    - "Rejeitar mais de 1x/turno (o guard é SINAL, não gate -- DESENHO §6)"
    - "Disparar quando o arg já aponta FORA do repo (path correto) ou quando o alvo in-repo EXISTE (escrita in-repo plausível)"
    - "Tocar nyx/proxy.py, a cascata OOM, gating ou write_memory"

  tests:
    - cmd: "/home/andrefarias/.local/bin/ruff check nyx/agent/loop/_iteration.py"
      deve_passar: true
    - cmd: "bash scripts/sprint_invariants.sh"
      deve_passar: true
    - cmd: "./run.sh --gauntlet --only rapido"
      timeout: 300
      deve_passar: true
      nota: "DEFERIDO para GPU exclusiva -- exige Ollama/GPU; rodar só quando pgrep de contenção estiver vazio"

  acceptance_criteria:
    - "Novo método _path_drift_reject(name, args) -> str | None: dispara SOMENTE quando (a) a tool é mutante; (b) o pedido do turno (_original_input) cita um path ~/X ou /abs/X que resolve para FORA do project_root e cujo alvo real EXISTE (ou está em session._files_modified); (c) o arg resolve para DENTRO do project_root, com o MESMO basename, e esse alvo NÃO existe"
    - "O hint devolvido cita o path EXATO do pedido e recomenda edit_file (edição sequencial cirúrgica); não inventa conteúdo nem executa a tool"
    - "Rejeição 1x/turno: flag self._path_drift_rejected armada em _init_done_guard (=False), consumida no wiring; segunda ocorrência no mesmo turno NÃO dispara"
    - "Ligado nos DOIS caminhos: _execute_tool_calls (nativo) e _execute_parsed_action (parser fallback), espelhando o padrão de _seq_edit_reject"
    - "Negativos garantidos (zero falso-positivo): (1) arg com o path absoluto/til CORRETO (fora do repo) -> None; (2) alvo in-repo com mesmo basename que EXISTE -> None; (3) pedido sem path ~/ ou /abs -> None; (4) basename do arg != basename do pedido -> None"
    - "Proof runtime-real SEM GPU: AgentLoop real + _path_drift_reject chamado direto -> pedido '~/Desktop/<f>' existente + arg relativo 'Desktop/<f>' (drift) devolve hint citando '~/Desktop/<f>' e 'edit_file'; os 4 negativos devolvem None"
    - "validate_path (base.py) intacto; guards existentes byte-identicos; ruff limpo; acentuação rc=0; FAIL_AFTER <= FAIL_BEFORE; smoke boot ok"
```

---

# Sprint EXEC-CONTRACT-PATH-DRIFT-01 — Guard de path-drift na edição sequencial

**Status:** PENDENTE
**Data criação:** 2026-07-13
**Modelo obrigatório:** claude-opus-4-7 (executor-sprint autorizado pelo dono nesta onda)

---

## Contexto do projeto (snapshot — não referência)

> **Missão (calibra a decisão):** o Nyx-Code faz o pior LLM local (qwen 3b) na pior máquina possível parecer um agente de código profissional offline. Robustez pertence à INFRA, não ao modelo (ADR-032/033/034). O usuário-alvo é leigo e sem hardware bom: quando o 3b erra o caminho de um arquivo, a infra tem que perceber e corrigir o rumo, não deixar o append sumir com um summary de falso sucesso.
>
> **ADRs relevantes (inline):**
> - **ADR-032 A INFRA CARREGA O MODELO:** a infra valida/sanitiza/rejeita+re-emite o tool_call; não confia que o 3b acerte o arg.
> - **ADR-033 ENFORCEMENT, NÃO CONFIANÇA:** forçar o rumo certo é aceitável; deixar o modelo criar lixo silencioso e mentir sobre o fim, não.
>
> **Estado (2026-07-13):** `qwen2.5-coder:3b`. ONDA-48 fase raiz: núcleo do contrato (399/397/400/398/401) CONCLUIDO. Este é satélite de robustez da edição sequencial (achado da validação holística 2026-07-12 T5), na mesma família de guards da 401. Desenho: `dev-journey/02-architecture/DESENHO_CONTRATO_EXECUCAO.md` (§6, "SINAL não gate" / "Honestidade na falha"). Ports: Ollama `11435`, proxy `11436`.

---

## Problema

**Achado (validação holística 2026-07-12, turno 5 — verificado adversarialmente):** em contexto acumulado (conversa longa), o 3b **re-resolve** o caminho `~/X` do pedido para `<project_root>/X`, cria um arquivo espúrio dentro do repositório e a edição nunca chega ao alvo real — com summary de falso sucesso.

Evidência literal (log `/tmp/claude-1000/holistica_log.jsonl` turno 5):

- Pedido do usuário: *"adicione ao final do arquivo `~/Desktop/nyx_hol_2026_07_12.py` ..."*.
- O 3b emitiu **3x `write_file`** para `/home/andrefarias/Desenvolvimento/Nyx-Code/Desktop/nyx_hol_2026_07_12.py` (path inexistente DENTRO do repo); **`edit_file` nunca foi emitido**.
- O alvo real `~/Desktop/nyx_hol_2026_07_12.py` ficou com sha256 idêntico antes/depois (`8b0ba853...`) — o append não aconteceu.
- Um arquivo espúrio de 36 bytes apareceu no `git status` como `?? Desktop/`.
- Summary de falso sucesso: *"OK: Arquivo criado: .../Nyx-Code/Desktop/nyx_hol_2026_07_12.py (36 bytes)..."*.
- No **T2 (contexto curto)** o MESMO `~/Desktop` foi resolvido corretamente — o drift **emerge com contexto acumulado**.

**Causa-raiz (verificada no código, sem divergência do briefing):**

`nyx/agent/tools/base.py`, `validate_path` (linha 157), resolve o caminho recebido do tool_call. Nas linhas 184-191:

```python
raw = Path(file_path.strip()).expanduser()
if raw.is_absolute():
    resolved = raw.resolve()
else:
    base = _ACTIVE_ROOT if _ACTIVE_ROOT is not None else _resolve(project_root)
    resolved = (base / raw).resolve()
```

A resolução está **CORRETA**: quando o 3b larga o prefixo `~/` (ou `/home/andrefarias/`) e emite o path **relativo** `Desktop/nyx_hol_2026_07_12.py`, `raw.is_absolute()` é `False`, então o path resolve contra `_ACTIVE_ROOT`/`project_root` e vira `<project_root>/Desktop/nyx_hol_2026_07_12.py`. **O erro é do modelo, não da infra** — mas hoje nada o detecta.

Por que os guards existentes NÃO cobrem:

- `_seq_edit_reject` (`_iteration.py:290`) — o ramo de overwrite cego (linhas 307-316) só dispara quando `resolved.exists()` é `True`. No path-drift o path errado **não existe**, então a âncora estrutural da 401 (arquivo existe + não-lido) **não casa exatamente no caso em que mais precisava**. É o ponto cego que o briefing aponta: *"A garantia da 401 não se sustenta end-to-end."*
- `_tool_match_reject` (`_iteration.py:278`) — só dispara quando o pedido é leitura pura e a tool é mutante; aqui o pedido É de escrita (append), então não se aplica.

Resultado: o `write_file` executa contra o path drifted, cria arquivo espúrio no working tree do projeto, o append ao alvo real do usuário se perde e o summary mente. Fere **"Honestidade na falha"** e o modelo de "a infra corrige o rumo" (DESENHO §6).

---

## Solução proposta

Um guard determinístico novo — `_path_drift_reject` — irmão de `_seq_edit_reject` e `_tool_match_reject`, com o mesmo formato de rejeição **1x/turno + hint forte** (SINAL, não gate — DESENHO §6). Ele dispara SOMENTE quando o drift é inequívoco:

1. A tool é **mutante** (`_MUTATING_TOOLS`, já definido: `write_file`, `create_file`, `edit_file`, `multi_edit`, `patch`).
2. O arg (`file_path`/`path`) resolve para **DENTRO** do `project_root` e esse alvo **NÃO existe**.
3. O pedido do turno (`_original_input`) cita um path `~/X` ou `/abs/X` que resolve para **FORA** do `project_root`, com o **MESMO basename** do arg, e cujo alvo real **EXISTE** (ou está em `session._files_modified` — cobre o caso do alvo criado antes na sessão, como o T2).

Quando as três condições batem, rejeita e devolve o hint citando o **path exato do pedido** e recomendando **`edit_file`** (append cirúrgico). O modelo re-emite; se errar de novo no mesmo turno, o cap de 1x deixa `MAX_ITERATIONS` como rede final (idêntico aos irmãos).

Zero falso-positivo por construção: se o arg já aponta fora do repo (path correto), a condição (2) falha; se o alvo in-repo existe (escrita in-repo plausível), a condição (2) falha; se o pedido não cita path absoluto/til, a condição (3) falha; se os basenames diferem, a condição (3) falha.

**Fronteira com a sprint 354 (CONV-CONTEXT-LOCATION-HALLUCINATION-01, PENDENTE, MASTER ~linha 1032):** a 354 trata alucinação de localização na **RESPOSTA textual** do modelo (ao perguntar "em qual arquivo está a função X?", o 3b inventa `nyx/agent/banner.py`). Esta sprint trata **drift de path nos ARGS de um tool_call mutante** em contexto acumulado. Mecanismos e superfícies distintos: 354 é sobre o que o modelo **fala**; 437 é sobre o que o modelo **executa**. São complementares e não se sobrepõem.

---

## Arquivos alvo (paths absolutos)

### `/home/andrefarias/Desenvolvimento/Nyx-Code/nyx/agent/loop/_iteration.py`

#### Edit 1 — constantes do guard (regex de extração + hint)

Localização: no bloco de constantes de guard, junto de `_SEQ_OVERWRITE_HINT`/`_SEQ_SHELL_HINT` (linhas ~216-225). Adicionar como atributos de classe:

```python
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
```

#### Edit 2 — armar a flag em `_init_done_guard`

Localização: fim de `_init_done_guard` (após `self._seq_edit_rejected = False`, linha 245):

```python
        # SEQ-EDIT-ENFORCE-EDITFILE-01: arma o guard de edição sequencial (1x/turno).
        self._seq_edit_rejected = False
        # EXEC-CONTRACT-PATH-DRIFT-01: arma o guard de path-drift (1x/turno).
        self._path_drift_rejected = False
```

#### Edit 3 — o método do guard

Localização: logo após `_seq_edit_reject` (após a linha 317, antes de `_execute_tool_calls`):

```python
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
```

> Nota de reconciliação de `root`: `validate_path` usa `_ACTIVE_ROOT` (módulo `tools/base`) para resolver relativos; `os.path.realpath(self._project_root)` deve coincidir com `_ACTIVE_ROOT` no runtime (o boot injeta o mesmo project_root). Se o executor confirmar divergência via `rg "_ACTIVE_ROOT" nyx/agent/tools/base.py`, usar `str(_validate_path(".", self._project_root))` como `root` (resolve a raiz pela MESMA função, garantindo comparação consistente). Registrar a escolha no proof.

#### Edit 4 — wiring no caminho nativo (`_execute_tool_calls`)

Localização: logo após o bloco de `_seq_edit_reject` (linhas 355-362), antes de `if self._on_tool:`:

```python
            # EXEC-CONTRACT-PATH-DRIFT-01: o 3b drifta ~/X (pedido) para
            # <project_root>/X (arg) em contexto acumulado -> rejeita 1x + re-emite
            # com o path do pedido e edit_file (não deixa criar arquivo espúrio).
            pd_hint = self._path_drift_reject(name, args)
            if pd_hint:
                self._path_drift_rejected = True
                logger.warning("[loop] path-drift: arg fora do pedido em %s", name)
                self._session.add_tool_call(name, args, pd_hint)
                continue
```

#### Edit 5 — wiring no parser fallback (`_execute_parsed_action`)

Localização: logo após o bloco de `_seq_edit_reject` do parser (linhas 586-592), antes de `if self._on_tool:`:

```python
        # EXEC-CONTRACT-PATH-DRIFT-01: idem caminho nativo, no parser fallback.
        pd_hint = self._path_drift_reject(tool_name, remapped)
        if pd_hint:
            self._path_drift_rejected = True
            logger.warning("[loop] path-drift (parser): arg fora do pedido em %s", tool_name)
            self._session.add_tool_call(tool_name, remapped, pd_hint)
            return None
```

---

## Diff esperado (resumo)

```
~ 1 arquivo modificado (nyx/agent/loop/_iteration.py)
+ ~50 linhas líquidas (guard + 2 constantes + flag + 2 wirings)
```

Sem aritmética de extração: esta sprint não tem meta `arquivo < NNNL`. O `_iteration.py` sai de 1106L para ~1156L (fix aditivo; o arquivo já cresceu acima do teto histórico de 400L por acúmulo dos guards do contrato — não é objetivo desta sprint fatiá-lo). O único número relevante é o net-add (~50L) num único arquivo.

---

## Comandos de verificação (literais, copy-paste)

```bash
cd /home/andrefarias/Desenvolvimento/Nyx-Code

# 1. Confirmar as âncoras (linhas podem ter deslizado -- reconferir ANTES de editar):
rg -n "_seq_edit_rejected|_seq_edit_reject|_SEQ_OVERWRITE_HINT|_MUTATING_TOOLS|_original_input|def _init_done_guard" nyx/agent/loop/_iteration.py
rg -n "_ACTIVE_ROOT|def validate_path" nyx/agent/tools/base.py

# 2. Estatica + acentuacao (ruff via binario direto -- não ha modulo ruff no venv, ver BRIEF)
/home/andrefarias/.local/bin/ruff check nyx/agent/loop/_iteration.py
python3 ~/.config/zsh/scripts/validar-acentuacao.py --paths nyx/agent/loop/_iteration.py

# 3. PROOF RUNTIME-REAL sem GPU (guard puro -- não sobe Ollama). AgentLoop real,
#    _path_drift_reject chamado direto. 1 positivo (drift) + 4 negativos.
./venv/bin/python - <<'PY'
import os
from nyx.agent.loop._core import AgentLoop

loop = AgentLoop(project_root="/home/andrefarias/Desenvolvimento/Nyx-Code")
loop._path_drift_rejected = False

# alvo real FORA do repo, que EXISTE (simula o ~/Desktop/... do T5)
home_file = os.path.expanduser("~/Desktop/nyx_drift_proof.py")
os.makedirs(os.path.dirname(home_file), exist_ok=True)
open(home_file, "a").close()

# POSITIVO: pedido cita ~/Desktop/<f>; arg relativo 'Desktop/<f>' drifta p/ dentro do repo
loop._original_input = "adicione ao final do arquivo ~/Desktop/nyx_drift_proof.py um print"
hint = loop._path_drift_reject("write_file", {"file_path": "Desktop/nyx_drift_proof.py", "content": "x"})
assert hint and "~/Desktop/nyx_drift_proof.py" in hint, ("POSITIVO falhou", hint)
assert "edit_file" in hint, ("hint sem edit_file", hint)
print("POSITIVO ok:", hint[:70], "...")

# NEG 1: arg com o path absoluto CORRETO (fora do repo) -> None
loop._path_drift_rejected = False
assert loop._path_drift_reject("write_file", {"file_path": home_file, "content": "x"}) is None, "NEG1"
# NEG 2: pedido sem path absoluto/til -> None
loop._path_drift_rejected = False
loop._original_input = "cria um arquivo de teste"
assert loop._path_drift_reject("write_file", {"file_path": "Desktop/nyx_drift_proof.py", "content": "x"}) is None, "NEG2"
# NEG 3: basename do arg != basename do pedido -> None
loop._path_drift_rejected = False
loop._original_input = "edite ~/Desktop/nyx_drift_proof.py"
assert loop._path_drift_reject("write_file", {"file_path": "Desktop/outro_nome.py", "content": "x"}) is None, "NEG3"
# NEG 4: cap 1x/turno -> segunda ocorrencia não dispara
loop._original_input = "adicione ao final do arquivo ~/Desktop/nyx_drift_proof.py um print"
loop._path_drift_rejected = True
assert loop._path_drift_reject("write_file", {"file_path": "Desktop/nyx_drift_proof.py", "content": "x"}) is None, "NEG4(cap)"

os.remove(home_file)
print("OK: 1 positivo (drift detectado, hint cita ~/ e edit_file) + 4 negativos (None)")
PY

# 4. Confirmar que o guard esta ligado nos DOIS caminhos e armado no turno:
rg -n "_path_drift_reject|_path_drift_rejected" nyx/agent/loop/_iteration.py

# 5. Guards existentes intactos (byte-identicos -- diff so adiciona):
git --no-pager diff nyx/agent/loop/_iteration.py | rg "^-" | rg -v "^---" || echo "OK: zero linhas removidas (fix so aditivo)"

# 6. Gauntlet rapido (regressao geral do loop) -- DEFERIDO p/ GPU exclusiva:
./run.sh --gauntlet --only rapido
```

> Nota GPU: o passo 3 roda SEM Ollama/GPU (guard puro, chamada direta). O passo 6 (gauntlet) exige GPU exclusiva -- executar só quando `pgrep -af "Luna.*driver|valida_sprint"` estiver vazio (protocolo anti-contenção do BRIEF); pode ficar DEFERIDO como as specs 403/407.

---

## Critério binário de aceite (IA executora)

- [ ] `_path_drift_reject(name, args)` implementado com as 3 condições (tool mutante; arg drifta para dentro do repo e não existe; pedido cita path fora do repo com mesmo basename que existe/foi modificado)
- [ ] Hint cita o path EXATO do pedido e recomenda `edit_file`
- [ ] Flag `self._path_drift_rejected` armada em `_init_done_guard`; rejeição no máximo 1x/turno
- [ ] Ligado nos DOIS caminhos: `_execute_tool_calls` (nativo) e `_execute_parsed_action` (parser fallback)
- [ ] Proof runtime-real colado (passo 3): 1 positivo com hint citando `~/` + `edit_file`, 4 negativos `None`
- [ ] `validate_path` (base.py) e os guards existentes (`_tool_match_reject`, `_seq_edit_reject`, `_should_reject_done`) intactos
- [ ] `ruff` limpo, acentuação rc=0, `FAIL_AFTER <= FAIL_BEFORE`, smoke boot ok
- [ ] `SPRINT_ORDER_MASTER.md` marca 437 CONCLUIDA; spec movida para `concluidos/` (integração do orquestrador)
- [ ] NÃO commitar; NÃO tocar Checkpoint.md; NÃO tocar `nyx/proxy.py` nem `nyx/agent/tools/base.py`

---

## Guardrails anti-engodo (obrigatórios)

NÃO marcar concluída se:
- O guard dispara quando o arg aponta FORA do repo (path correto) — isso quebraria toda escrita legítima em `~/...`; a condição `resolved.relative_to(root)` tem que FALHAR nesse caso (return None).
- O guard dispara quando o alvo in-repo com mesmo basename EXISTE — escrita in-repo é plausível; a condição `resolved.exists()` tem que curto-circuitar (return None).
- A rejeição não respeita o cap de 1x/turno (loop de rejeição infinito é regressão).
- Alterou `validate_path` em `base.py` (a resolução está correta; o fix é detectar o drift do MODELO, não mudar a infra que resolve).
- Algum guard existente foi removido, reordenado ou teve a mensagem alterada.
- Proof runtime-real não colado, ou o positivo não cita `~/` e `edit_file`, ou algum negativo devolveu hint em vez de `None`.
- Tocou `nyx/proxy.py`.

Se algo falhar: `[SPRINT 437] BLOQUEADA: <motivo 1 linha>`.

---

## Proof-of-work esperado (comandos runtime-reais do VALIDATOR_BRIEF)

```bash
cd /home/andrefarias/Desenvolvimento/Nyx-Code
bash scripts/sprint_invariants.sh > /tmp/inv_before.txt 2>&1
FAIL_BEFORE=$(grep -c "^\[FAIL\]" /tmp/inv_before.txt)
# implementar
bash scripts/sprint_invariants.sh > /tmp/inv_after.txt 2>&1
FAIL_AFTER=$(grep -c "^\[FAIL\]" /tmp/inv_after.txt)
diff /tmp/inv_before.txt /tmp/inv_after.txt
```

Colar no relato:
- `inv_before`/`inv_after` (tail) + `diff` — baseline esperado `FAIL_BEFORE = 0`, `FAIL_AFTER <= 0`.
- Output do proof runtime-real (passo 3): 1 positivo + 4 negativos.
- `rg` do passo 4 (guard ligado nos dois caminhos + armado).
- `git --no-pager diff --stat` (1 arquivo) e verificação do passo 5 (zero linhas removidas).
- `./run.sh --smoke` deve imprimir `boot ok` (check #13, obrigatório antes de CONCLUIDA — `feedback_smoke_boot`).
- **DEFERIDO para GPU exclusiva** (como 403/407): `./run.sh --gauntlet --only rapido` — rodar só quando a GPU estiver livre de contenção; se DEFERIDO, registrar explicitamente no relato e no MASTER.

---

## Gambiarras específicas desta sprint

- **`os.path.realpath` nos dois lados:** normaliza symlinks para que a comparação `startswith(root + os.sep)` não vaze por um symlink de `~/` ou do project_root. O `os.sep` no sufixo evita o falso-positivo de prefixo (`/repo` casando `/repo-outro`).
- **`_USER_PATH_RE` conservador:** só casa tokens que começam com `~/` ou `/` (lookbehind `(?<![\w/])` evita casar o meio de uma URL ou de outro path) e param no primeiro espaço/aspa/crase. Não tenta entender semântica — extrai candidatos e o guard filtra por basename + existência.
- **`_files_modified` cobre o alvo criado na sessão:** o T5 do achado só drifta porque o alvo já fora criado (T2). Cruzar com `session._files_modified` garante o disparo mesmo quando o alvo real ainda não existe no disco no instante do guard mas foi materializado antes no mesmo fluxo.
- **`except Exception` no `_validate_path`:** resolver falho (path inválido, permissão) NÃO pode derrubar o guard — degrada para `None` (deixa o fluxo normal seguir), consistente com `_seq_edit_reject` (linha 312).
- **Ordem dos guards:** path-drift entra ANTES de `_seq_edit_reject`. Faz sentido: se o path está drifted (não existe), o ramo de overwrite cego do seq-edit nem dispararia (exige `resolved.exists()`); tratar o drift primeiro dá o hint mais preciso.

---

## Validação humana (checklist do usuário)

```bash
cd /home/andrefarias/Desenvolvimento/Nyx-Code
git --no-pager show --stat HEAD

# Repro do T5 com o stack real (GPU exclusiva): em conversa LONGA, criar
# ~/Desktop/x.py num turno e, alguns turnos depois, pedir "adicione ao final
# do arquivo ~/Desktop/x.py ...". A Nyx deve re-emitir apontando ~/Desktop/x.py
# e usar edit_file -- não criar <repo>/Desktop/x.py nem dar summary de falso
# sucesso. Conferir git status: ZERO arquivo espurio '?? Desktop/'.

ls dev-journey/06-sprints/concluidos/SPRINT_EXEC_CONTRACT_PATH_DRIFT_01.md  # existe
```

---

## Fora de escopo (anti-débito)

| Item | Decisão |
|------|---------|
| Ancorar formalmente o "arquivo-alvo do turno" na sessão (estrutura que rastreia o alvo pretendido do pedido, para além de `files_modified`) | **NÃO-OBJETIVO.** O briefing lista como candidato ("avaliar também ancorar o arquivo-alvo do turno"). Esta sprint resolve o achado com o cruzamento `_files_modified` + basename, suficiente para o T5. Se a auditoria mostrar drift que o basename não pega (ex.: mesmo basename em pastas distintas), registrar sprint própria `EXEC-CONTRACT-TURN-TARGET-ANCHOR-01` (`feedback_nenhum_debito`). |
| Alucinação de localização na RESPOSTA textual (perguntar "onde está X" e o 3b inventar um path) | **Sprint 354 (PENDENTE).** Mecanismo e superfície distintos (fala vs execução). Esta sprint cita e delimita a fronteira; não absorve nem toca a 354. |
| Middleware de erro no `nyx/proxy.py` | Fora de escopo — sem relação com path-drift. |
| Fatiar `_iteration.py` (1106L, acima do teto histórico de 400L) | Débito de refactor pré-existente; registrar sprint própria se for atacar. Esta é aditiva. |

---

## Referências

- BRIEF: `/home/andrefarias/Desenvolvimento/Nyx-Code/VALIDATOR_BRIEF.md`
- Desenho do contrato: `dev-journey/02-architecture/DESENHO_CONTRATO_EXECUCAO.md` (§6, "SINAL não gate" / "Honestidade na falha")
- Guard irmão (padrão de rejeição 1x/turno): `nyx/agent/loop/_iteration.py` `_seq_edit_reject` (linha 290) — sprint 401 SEQ-EDIT-ENFORCE-EDITFILE-01 (commit `2a89e19`)
- Resolução de path (intacta): `nyx/agent/tools/base.py` `validate_path` (linha 157)
- Fronteira: sprint 354 CONV-CONTEXT-LOCATION-HALLUCINATION-01 (PENDENTE, `SPRINT_ORDER_MASTER.md` ~linha 1032)
- Origem do achado: validação holística 2026-07-12 T5 -- log efêmero da sessão; registro durável em `dev-journey/07-reports/AUDIT_2026_07_12.md` §2

---

*"Quando o modelo erra o caminho, a infra tem que perceber o rumo errado e corrigir -- não deixar o append sumir num arquivo espúrio com um summary de falso sucesso." -- princípio de execução (DESENHO_CONTRATO_EXECUCAO.md §6)* <!-- noqa-acento -->
