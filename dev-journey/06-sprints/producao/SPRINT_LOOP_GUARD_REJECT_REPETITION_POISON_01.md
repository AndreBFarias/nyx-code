## 0. SPEC (machine-readable)

```yaml
sprint:
  id: LOOP-GUARD-REJECT-REPETITION-POISON-01
  numero: 418
  title: "Rejeição de guard não deve envenenar o detector de repetição -- a re-emissão pedida pelo hint morria em FORCE_DONE"
  onda: 48
  prioridade: ALTA
  tipo: Bugfix
  dependencias: []
  desbloqueia: []
  absorve: []

  touches:
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/agent/session.py
      reason: "HistoryEntry ganha campo is_reject: bool = False; add_tool_call ganha param is_reject repassado ao entry -- marca entradas que são rejeição de guard (não execução real)"
      linhas_alvo: "14-21 (dataclass HistoryEntry), 57-70 (add_tool_call)"
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/agent/repetition.py
      reason: "is_in_recent (primário), is_semantic_repeat e is_cycle pulam entradas com is_reject=True -- uma rejeição nunca é uma ação anterior"
      linhas_alvo: "74 (loop de is_semantic_repeat), 108-111 (loop de is_in_recent), 119 (comprehension de is_cycle)"
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/agent/loop/_iteration.py
      reason: "os add_tool_call de rejeição de guard (echo, tool-match, seq-edit, done-reject) passam is_reject=True nos dois caminhos (nativo + parser fallback)"
      linhas_alvo: "343, 352, 361, 371 (caminho nativo _execute_tool_calls); 538, 575, 583, 591 (parser _execute_parsed_action)"
  creates: []
  removes: []

  forbidden:
    - "Adicionar emoji"
    - "Usar 'print()' fora de cli.py/output.py"
    - "Mencao a ferramenta de IA externa"
    - "Marcar is_reject=True nos bloqueios DUROS (plan_mode, permissão negada, preflight, hook PreToolUse) -- esses DEVEM contar para a detecção de repetição (anti-spam de tool bloqueada)"
    - "Alterar a chave de identidade do detector (tool_name + sorted args) -- LOOP-ACTIONTYPE-FALLBACK-DONE-01 intocado"
    - "Mexer em is_exact_repeat (usa _last_action, já imune -- rejeição não atualiza _last_action)"
    - "Alterar os thresholds (force_done_threshold, consecutive_skips >= 3) ou a lógica de has_results"
    - "Mexer nos textos dos hints de rejeição (_ECHO_REJECT_HINT, _TOOL_MATCH_HINT, _SEQ_OVERWRITE_HINT, _SEQ_SHELL_HINT, _DONE_REJECT_HINT, _ACTION_REJECT_HINT)"

  tests:
    - cmd: "/home/andrefarias/.local/bin/ruff check nyx/agent/session.py nyx/agent/repetition.py nyx/agent/loop/_iteration.py"
      deve_passar: true
    - cmd: "bash scripts/sprint_invariants.sh"
      deve_passar: true
    - cmd: "./run.sh --smoke"
      deve_passar: true
    - cmd: "./run.sh --gauntlet --only loop"
      timeout: 300
      deve_passar: true
      nota: "DEFERIDO para GPU exclusiva (contenção). Proof runtime-real SEM GPU no passo 3."

  acceptance_criteria:
    - "HistoryEntry tem campo is_reject: bool = False; add_tool_call aceita is_reject e repassa ao entry (default False -- todas as chamadas atuais seguem byte-idênticas em comportamento)"
    - "is_in_recent ignora entradas com is_reject=True: a re-emissão de write_file idêntica após uma rejeição de seq-edit NÃO casa mais com a entrada de rejeição -> não vira SKIP -> não escala para FORCE_DONE"
    - "is_semantic_repeat e is_cycle também pulam entradas com is_reject=True (defesa coerente: rejeição não é ação anterior em nenhum detector de histórico)"
    - "Os 8 add_tool_call de rejeição de guard (echo/tool-match/seq-edit/done-reject, nos 2 caminhos) passam is_reject=True; os bloqueios DUROS (plan_mode/permissão/preflight/hook) seguem SEM a flag (contam para repetição)"
    - "Regressão preservada: repetição REAL (entradas executadas, is_reject=False) segue disparando SKIP/FORCE_DONE normalmente -- o proof afirma os DOIS lados"
    - "is_exact_repeat intocado (usa _last_action, já imune); LOOP-ACTIONTYPE-FALLBACK-DONE-01 e os thresholds preservados"
    - "ruff limpo, acentuação rc=0, invariantes FAIL_AFTER <= FAIL_BEFORE, smoke boot ok"
```

---

# Sprint LOOP-GUARD-REJECT-REPETITION-POISON-01 — a rejeição de guard não pode matar a re-emissão que ela mesma pediu

**Status:** PENDENTE
**Data criação:** 2026-07-12
**Modelo obrigatório:** claude-opus-4-7 (executor-sprint autorizado pelo dono nesta onda)

---

## Contexto do projeto (snapshot — não referência)

> **ADRs relevantes (inline):**
> - **ADR-032/033 A INFRA CARREGA O MODELO / ENFORCEMENT, NÃO CONFIANÇA:** a robustez pertence à infra, não ao modelo. O pior LLM local (qwen 3b) na pior máquina deve parecer o Claude Code offline. Quando a infra manda o modelo corrigir e re-emitir, ela não pode punir a obediência. <!-- noqa-anonimato -->
> - **ADR-034:** a infra corrige a estrutura do 3b sem adivinhar intenção. Um guard que rejeita 1x e pede re-emissão é enforcement legítimo; matar o turno porque a re-emissão "parece repetição" é a infra sabotando o próprio contrato.
>
> **Estado (2026-07-12):** `qwen2.5-coder:3b`. ONDA-48 fase raiz do contrato de execução CONCLUIDA. Este é um achado da auditoria de prontidão 2026-07-12 (verificado adversarialmente com evidência file:line). Os guards do contrato (echo/tool-match/seq-edit/done) foram introduzidos em 397-401 e LOOP-*; o detector de repetição vem de Luna (344) e do LOOP-ACTIONTYPE-FALLBACK-DONE-01. O achado é a **interação** entre os dois subsistemas, não um bug isolado de nenhum deles.

---

## Problema

**Achado (auditoria 2026-07-12, severidade ALTA):** a tarefa mais básica do agente — editar um arquivo que já existe — falha de forma **determinística** quando o modelo obedece o próprio guard da infra.

Cenário obediente, passo a passo (o "poison"):

1. O usuário pede para editar um arquivo existente. O modelo chama `write_file` com o novo conteúdo.
2. O guard **SEQ-EDIT-ENFORCE-EDITFILE-01** (overwrite cego: arquivo existe e não foi lido nesta sessão) rejeita 1x e emite `_SEQ_OVERWRITE_HINT` ("leia primeiro com read_file..."). A rejeição é gravada no histórico via `add_tool_call(name, args, se_hint)` — **com o `tool_name` e os `tool_args` reais da chamada rejeitada**.
3. O modelo obedece: chama `read_file` (agora `has_results=True`).
4. O modelo re-emite o **mesmo** `write_file` — agora legítimo, porque leu o arquivo (o guard seq-edit não rejeita de novo: é 1x/turno e o arquivo agora está em `_files_read`).
5. Mas `is_in_recent` compara `(tool_name, sorted(args))` da re-emissão contra as últimas 3 entradas do histórico — e **casa com a entrada de rejeição do passo 2** (mesmo nome, mesmos args) → `SkipStrategy.SKIP`.
6. Na iteração seguinte: `consecutive_skips (1) >= force_done_threshold (1)` **e** `has_results=True` → `SkipStrategy.FORCE_DONE`. O turno morre com "Não consegui completar a criação/edição pedida".

O modelo fez **exatamente** o que a infra mandou (leu antes de escrever) e a infra matou o turno.

**Causa-raiz (verificada no código — as âncoras do briefing bateram, sem drift):**

- `nyx/agent/loop/_iteration.py:361` — `self._session.add_tool_call(name, args, se_hint)` grava a rejeição de seq-edit com `name`/`args` idênticos aos da chamada. O mesmo padrão está em L343 (echo), L352 (tool-match) e L371 (done-reject), além do espelho no parser fallback (L575/L583/L591/L538).
- `nyx/agent/session.py:57-70` — `add_tool_call` cria um `HistoryEntry` com `tool_name` e `tool_args` reais; **não há como distinguir uma execução de uma rejeição** — o campo não existe.
- `nyx/agent/repetition.py:108-113` — `is_in_recent` monta `entry_key = (entry.tool_name, tuple(sorted(entry.tool_args.items())))` para cada uma das últimas `window=3` entradas e compara com a ação nova, **sem distinguir execução de rejeição**.
- `nyx/agent/repetition.py:159-160` — `if consecutive_skips >= force_done_threshold and has_results: return SkipStrategy.FORCE_DONE`, com `force_done_threshold=1` no tier do 3b (`nyx/agent/model_tier.py:114`). Um único SKIP envenenado basta para o FORCE_DONE.

**Por que `is_exact_repeat` NÃO é o vetor (verificado):** `is_exact_repeat` usa `self._last_action`, que só é atualizado após uma execução real (`_iteration.py:508` e `:653`). Uma rejeição de guard usa `continue`/`return None` sem tocar `_last_action`. Logo `is_exact_repeat` já é imune — o poison é especificamente `is_in_recent`, que lê o histórico bruto.

Isso fere **ADR-032/033/034**: a robustez está na infra, mas aqui a infra pune a obediência ao próprio guard. É o oposto de "fazer o 3b parecer o Claude Code". <!-- noqa-anonimato -->

### Divergência do briefing

**Nenhuma divergência de fato.** As três âncoras do briefing (`_iteration.py:361`, `repetition.py:110-113`, `repetition.py:159-160`) bateram exatamente no código atual. O briefing propôs duas opções de fix ("tool_name sintético" **ou** "is_in_recent ignora entradas cujo tool_result é hint conhecido"); esta spec escolhe uma **terceira via, mais limpa e desacoplada**: um campo booleano `is_reject` no `HistoryEntry`, filtrado nos detectores de histórico. Justificativa em "Solução proposta". Além disso, o achado é de um único mecanismo (a interação guard×detector), então a sprint é única com ACs por faceta — não há mecanismos distintos demais para separar.

---

## Solução proposta

**Invariante que estabelecemos:** uma entrada de rejeição de guard representa uma chamada que **NÃO foi executada** — é a infra pedindo re-emissão. Os detectores de repetição por histórico não podem tratá-la como uma ação anterior.

Descartadas as duas opções do briefing:
- **`tool_name` sintético** (ex.: `"seq_edit_reject"`): mudaria o que o modelo vê em `to_messages` (`[resultado de seq_edit_reject]`) e contaminaria `is_semantic_repeat`/`is_cycle` de forma imprevisível — acopla a correção à nomenclatura.
- **`is_in_recent` inspeciona `tool_result` contra os textos dos hints:** acopla `repetition.py` às constantes de string que vivem em `_iteration.py` — frágil (qualquer ajuste de texto de hint quebraria o detector).

Via escolhida — **campo `is_reject` no `HistoryEntry`** (dado estrutural, desacoplado de texto e de nome):

1. **`session.py`** — `HistoryEntry` ganha `is_reject: bool = False`; `add_tool_call` ganha `is_reject: bool = False` repassado ao entry. Default `False`: todas as chamadas atuais seguem idênticas.
2. **`repetition.py`** — `is_in_recent` (primário), `is_semantic_repeat` e `is_cycle` pulam entradas com `is_reject=True`. Uma linha de guarda por loop.
3. **`_iteration.py`** — os 8 `add_tool_call` de rejeição de guard (echo/tool-match/seq-edit/done-reject, nos dois caminhos) passam `is_reject=True`. Os bloqueios **duros** (plan_mode, permissão negada, preflight, hook) ficam **sem** a flag: um modelo que insiste numa tool bloqueada DEVE ser pego pela repetição (anti-spam).

**Por que é seguro contra loop infinito:** cada guard rejeita no máximo 1x/turno (flags `_seq_edit_rejected`, `_tool_match_rejected`, `_done_rejected`). Logo há no máximo uma entrada `is_reject=True` por guard por turno. Excluí-la de `is_in_recent` não pode criar loop — a rede anti-repetição continua ativa para todas as entradas **executadas** (`is_reject=False`), que é onde a repetição real acontece.

---

## Arquivos alvo (paths absolutos)

### `/home/andrefarias/Desenvolvimento/Nyx-Code/nyx/agent/session.py`

#### Edit 1 — campo `is_reject` no `HistoryEntry` (dataclass, ~L14-21)

**Antes:**
```python
@dataclass
class HistoryEntry:
    role: str
    content: str
    tool_name: str = ""
    tool_args: dict[str, Any] = field(default_factory=dict)
    tool_result: str = ""
    is_key_decision: bool = False
```
**Depois:**
```python
@dataclass
class HistoryEntry:
    role: str
    content: str
    tool_name: str = ""
    tool_args: dict[str, Any] = field(default_factory=dict)
    tool_result: str = ""
    is_key_decision: bool = False
    # LOOP-GUARD-REJECT-REPETITION-POISON-01: True quando a entrada é uma
    # rejeição de guard (echo/tool-match/seq-edit/done) -- a chamada NÃO foi
    # executada, a infra só pediu re-emissão. Os detectores de repetição por
    # histórico (is_in_recent/is_semantic_repeat/is_cycle) ignoram estas
    # entradas: senão a re-emissão obediente casaria com a rejeição e o turno
    # morreria em FORCE_DONE (ADR-032/033: não punir a obediência ao guard).
    is_reject: bool = False
```

#### Edit 2 — `add_tool_call` aceita e repassa `is_reject` (~L57-70)

**Antes:**
```python
    def add_tool_call(self, tool_name: str, args: dict[str, Any], result: str, is_key: bool = False) -> None:
        truncated = result[: self.TOOL_RESULT_LIMIT]
        if len(result) > self.TOOL_RESULT_LIMIT:
            truncated += f"\n[... truncado, {len(result)} chars total]"
        self.history.append(
            HistoryEntry(
                role="tool",
                content=truncated,
                tool_name=tool_name,
                tool_args=args,
                tool_result=truncated,
                is_key_decision=is_key,
            )
        )
```
**Depois:**
```python
    def add_tool_call(
        self,
        tool_name: str,
        args: dict[str, Any],
        result: str,
        is_key: bool = False,
        is_reject: bool = False,
    ) -> None:
        truncated = result[: self.TOOL_RESULT_LIMIT]
        if len(result) > self.TOOL_RESULT_LIMIT:
            truncated += f"\n[... truncado, {len(result)} chars total]"
        self.history.append(
            HistoryEntry(
                role="tool",
                content=truncated,
                tool_name=tool_name,
                tool_args=args,
                tool_result=truncated,
                is_key_decision=is_key,
                is_reject=is_reject,
            )
        )
```

### `/home/andrefarias/Desenvolvimento/Nyx-Code/nyx/agent/repetition.py`

#### Edit 3 — `is_in_recent` pula rejeições (loop ~L108-111)

**Antes:**
```python
    cur = key if key is not None else action.action_type.value
    new_key = (cur, tuple(sorted(action.params.items())))
    for entry in history[-window:]:
        if not entry.tool_name:
            continue
        entry_key = (entry.tool_name, tuple(sorted(entry.tool_args.items())))
        if new_key == entry_key:
            return True
    return False
```
**Depois:**
```python
    cur = key if key is not None else action.action_type.value
    new_key = (cur, tuple(sorted(action.params.items())))
    for entry in history[-window:]:
        if not entry.tool_name:
            continue
        # LOOP-GUARD-REJECT-REPETITION-POISON-01: uma rejeição de guard NÃO é
        # execução -- a infra pediu re-emissão. Contá-la aqui fazia a re-emissão
        # obediente virar SKIP e, com force_done_threshold=1, FORCE_DONE.
        if getattr(entry, "is_reject", False):
            continue
        entry_key = (entry.tool_name, tuple(sorted(entry.tool_args.items())))
        if new_key == entry_key:
            return True
    return False
```

#### Edit 4 — `is_semantic_repeat` pula rejeições (loop ~L74)

**Antes:**
```python
    window = history[-5:] if len(history) >= 5 else history
    for entry in window:
        if not entry.tool_name:
            continue
        entry_path = entry.tool_args.get("path", entry.tool_args.get("file_path", ""))
```
**Depois:**
```python
    window = history[-5:] if len(history) >= 5 else history
    for entry in window:
        if not entry.tool_name:
            continue
        # LOOP-GUARD-REJECT-REPETITION-POISON-01: idem is_in_recent -- rejeição
        # de guard não conta como ação anterior em nenhum detector de histórico.
        if getattr(entry, "is_reject", False):
            continue
        entry_path = entry.tool_args.get("path", entry.tool_args.get("file_path", ""))
```

#### Edit 5 — `is_cycle` pula rejeições (comprehension ~L119)

**Antes:**
```python
def is_cycle(history: list[HistoryEntry], window: int = 6) -> bool:
    """Detecta padrões A->B->A->B em janela de histórico."""
    tool_entries = [e for e in history if e.tool_name]
```
**Depois:**
```python
def is_cycle(history: list[HistoryEntry], window: int = 6) -> bool:
    """Detecta padrões A->B->A->B em janela de histórico."""
    # LOOP-GUARD-REJECT-REPETITION-POISON-01: rejeições de guard fora do ciclo
    # (não foram executadas -- não compõem um padrão A->B real).
    tool_entries = [e for e in history if e.tool_name and not getattr(e, "is_reject", False)]
```

### `/home/andrefarias/Desenvolvimento/Nyx-Code/nyx/agent/loop/_iteration.py`

Marcar `is_reject=True` nos **8** `add_tool_call` de rejeição de guard. Caminho nativo (`_execute_tool_calls`): L343 echo, L352 tool-match, L361 seq-edit, L371 done-reject. Parser fallback (`_execute_parsed_action`): L575 echo, L583 tool-match, L591 seq-edit, L538 done-reject.

#### Edit 6 — caminho nativo (echo/tool-match/seq-edit/done)

**Antes (echo, ~L343):**
```python
                self._session.add_tool_call(name, args, self._ECHO_REJECT_HINT)
```
**Depois:**
```python
                self._session.add_tool_call(name, args, self._ECHO_REJECT_HINT, is_reject=True)
```

**Antes (tool-match, ~L352):**
```python
                self._session.add_tool_call(name, args, tm_hint)
```
**Depois:**
```python
                self._session.add_tool_call(name, args, tm_hint, is_reject=True)
```

**Antes (seq-edit, ~L361):**
```python
                self._session.add_tool_call(name, args, se_hint)
```
**Depois:**
```python
                self._session.add_tool_call(name, args, se_hint, is_reject=True)
```

**Antes (done-reject, ~L371):**
```python
                    self._session.add_tool_call(name, args, reject_hint)
```
**Depois:**
```python
                    self._session.add_tool_call(name, args, reject_hint, is_reject=True)
```

#### Edit 7 — parser fallback (done/echo/tool-match/seq-edit)

**Antes (done-reject, ~L538):**
```python
                self._session.add_tool_call("done", action.params, reject_hint)
```
**Depois:**
```python
                self._session.add_tool_call("done", action.params, reject_hint, is_reject=True)
```

**Antes (echo, ~L575):**
```python
            self._session.add_tool_call(tool_name, remapped, self._ECHO_REJECT_HINT)
```
**Depois:**
```python
            self._session.add_tool_call(tool_name, remapped, self._ECHO_REJECT_HINT, is_reject=True)
```

**Antes (tool-match, ~L583):**
```python
            self._session.add_tool_call(tool_name, remapped, tm_hint)
```
**Depois:**
```python
            self._session.add_tool_call(tool_name, remapped, tm_hint, is_reject=True)
```

**Antes (seq-edit, ~L591):**
```python
            self._session.add_tool_call(tool_name, remapped, se_hint)
```
**Depois:**
```python
            self._session.add_tool_call(tool_name, remapped, se_hint, is_reject=True)
```

> **NÃO marcar (bloqueios duros — devem contar para repetição):** plan_mode (`~L385-387`), permissão negada (`~L393`, `~L600`), usuário negou (`~L406`, `~L607`), preflight (`~L436`, `~L622`), hook PreToolUse (`~L454-456`), ação não roteável (`~L557-561`), e o `add_tool_call` de SKIP dentro de `_check_repetition` (`~L719`). Um modelo que insiste numa tool bloqueada tem que ser pego pela repetição.

---

## Diff esperado (resumo)

```
~ 3 arquivos modificados:
  - nyx/agent/session.py         (+ campo + param, ~10L com comentário)
  - nyx/agent/repetition.py      (+ 3 guardas de 2-4L cada com comentário)
  - nyx/agent/loop/_iteration.py (8 call-sites: + ", is_reject=True")
+ ~25 linhas líquidas, sem meta numérica de tamanho (fix aditivo)
```

Sem aritmética de extração: esta sprint **não** tem meta `arquivo < NNNL`. O único número relevante é o net-add (~25L) distribuído em 3 arquivos; nenhum arquivo cruza limite de tamanho.

---

## Comandos de verificação (literais, copy-paste)

```bash
cd /home/andrefarias/Desenvolvimento/Nyx-Code

# 1. Estatica + acentuacao (ruff via binario direto -- não ha modulo ruff no venv, ver BRIEF)
/home/andrefarias/.local/bin/ruff check nyx/agent/session.py nyx/agent/repetition.py nyx/agent/loop/_iteration.py
python3 ~/.config/zsh/scripts/validar-acentuacao.py --paths nyx/agent/session.py nyx/agent/repetition.py nyx/agent/loop/_iteration.py

# 2. Confirmar a hipotese das ancoras (linhas podem ter deslizado -- reconferir):
rg -n "add_tool_call\(" nyx/agent/loop/_iteration.py     # os 8 de rejeição devem ter is_reject=True
rg -n "is_reject" nyx/agent/session.py nyx/agent/repetition.py nyx/agent/loop/_iteration.py

# 3. PROOF RUNTIME-REAL sem GPU (detectores de repetição reais, CodeSession real).
#    Reproduz o poison ANTES/DEPOIS: entrada de rejeição de write_file no
#    histórico + re-emissão idêntica. Afirma os DOIS lados (rejeição NÃO conta;
#    execução real AINDA conta -- regressão preservada).
./venv/bin/python - <<'PY'
from nyx.agent.session import CodeSession
from nyx.agent.models import ActionType, AgentAction
from nyx.agent.repetition import is_in_recent, get_skip_strategy, SkipStrategy

WARGS = {"file_path": "/proj/config.py", "content": "x = 1\n"}

# --- Lado 1: a rejeição de guard NÃO deve envenenar (o fix) ---
s = CodeSession()
# preenche a janela (window=3) com contexto neutro + a rejeição de seq-edit
s.add_tool_call("list_files", {"path": "/proj"}, "config.py")
s.add_tool_call("read_file", {"file_path": "/proj/config.py"}, "x = 0")
s.add_tool_call("write_file", WARGS, "leia primeiro...", is_reject=True)  # rejeição
reemit = AgentAction(action_type=ActionType.WRITE_FILE, params=WARGS)
assert is_in_recent(reemit, s.history, key="write_file") is False, "poison: rejeição casou como repetição"
strat = get_skip_strategy(
    action=reemit, last_action=None, history=s.history,
    files_modified=set(), consecutive_skips=0, has_results=True,
    force_done_threshold=1, key="write_file",
)
assert strat == SkipStrategy.CONTINUE, f"esperava CONTINUE, veio {strat}"
print("OK lado 1: re-emissão após rejeição -> CONTINUE (não SKIP, não FORCE_DONE)")

# --- Lado 2: repetição REAL (executada) AINDA deve ser pega (regressão) ---
s2 = CodeSession()
s2.add_tool_call("list_files", {"path": "/proj"}, "config.py")
s2.add_tool_call("read_file", {"file_path": "/proj/config.py"}, "x = 0")
s2.add_tool_call("write_file", WARGS, "arquivo escrito")  # is_reject=False (execução)
assert is_in_recent(reemit, s2.history, key="write_file") is True, "regressão: repetição real escapou"
print("OK lado 2: repetição de execução real -> ainda detectada (SKIP intacto)")
print("PROOF OK: rejeição imune, execução real ainda pega")
PY

# 4. Invariantes (baseline -> pós), FAIL_AFTER <= FAIL_BEFORE:
bash scripts/sprint_invariants.sh > /tmp/inv_before.txt 2>&1   # rodar ANTES de editar
# ... implementar ...
bash scripts/sprint_invariants.sh > /tmp/inv_after.txt 2>&1
diff /tmp/inv_before.txt /tmp/inv_after.txt || true

# 5. Smoke boot:
./run.sh --smoke     # deve imprimir 'boot ok' e exit 0

# 6. [DEFERIDO GPU] end-to-end do loop (write em arquivo existente -> read -> re-emit
#    deve CONCLUIR, não FORCE_DONE). Rodar só com GPU exclusiva (sem contenção):
./run.sh --gauntlet --only loop
```

> Nota GPU: os passos 1-5 rodam SEM Ollama/GPU (detectores puros + smoke de imports). O passo 6 (gauntlet `--only loop`) exige GPU exclusiva -- executar só quando `pgrep -af "Luna.*driver|valida_sprint"` estiver vazio (protocolo anti-contenção do BRIEF). Como as specs 403/407, o proof de GPU fica DEFERIDO; o passo 3 já prova a correção de forma determinística sem GPU.

---

## Critério binário de aceite (IA executora)

- [ ] `HistoryEntry.is_reject: bool = False` adicionado; `add_tool_call` aceita `is_reject` e repassa ao entry
- [ ] `is_in_recent` pula entradas com `is_reject=True` (fix primário)
- [ ] `is_semantic_repeat` e `is_cycle` pulam entradas com `is_reject=True` (defesa coerente)
- [ ] Os 8 `add_tool_call` de rejeição de guard (echo/tool-match/seq-edit/done, nos 2 caminhos) passam `is_reject=True`
- [ ] Bloqueios DUROS (plan_mode/permissão/preflight/hook/não-roteável/SKIP) seguem SEM `is_reject`
- [ ] Proof runtime-real colado (passo 3): lado 1 CONTINUE + lado 2 SKIP detectado
- [ ] `is_exact_repeat` intocado; thresholds e LOOP-ACTIONTYPE-FALLBACK-DONE-01 preservados
- [ ] `ruff` limpo, acentuação rc=0, `FAIL_AFTER <= FAIL_BEFORE`, smoke boot ok
- [ ] Gauntlet `--only loop` DEFERIDO para GPU exclusiva (registrar no proof que ficou pendente de GPU)
- [ ] `SPRINT_ORDER_MASTER.md` marca 418 CONCLUIDA; spec movida para `concluidos/`
- [ ] NÃO commitar; NÃO tocar Checkpoint.md

---

## Guardrails anti-engodo (obrigatórios)

NÃO marcar concluída se:
- O fix marcou `is_reject=True` em algum bloqueio DURO (plan_mode/permissão/preflight/hook) — isso abriria buraco anti-spam de tool bloqueada.
- Alterou a chave de identidade do detector (`tool_name` + `sorted(args)`) ou os thresholds (`force_done_threshold`, `>= 3`).
- O proof do passo 3 não foi colado, ou o lado 2 (regressão de repetição real) não passou — o fix TEM que preservar a detecção de repetição executada.
- Mexeu em `is_exact_repeat` (desnecessário — já imune via `_last_action`) ou nos textos dos hints.
- Usou a via "tool_name sintético" ou "inspecionar tool_result contra strings de hint" (rejeitadas em Solução proposta — acoplam a correção a texto/nome).

Se algo falhar: `[SPRINT 418] BLOQUEADA: <motivo 1 linha>`.

---

## Proof-of-work obrigatório

```bash
bash scripts/sprint_invariants.sh > /tmp/inv_before.txt 2>&1
FAIL_BEFORE=$(grep -c "^\[FAIL\]" /tmp/inv_before.txt)
# implementar
bash scripts/sprint_invariants.sh > /tmp/inv_after.txt 2>&1
FAIL_AFTER=$(grep -c "^\[FAIL\]" /tmp/inv_after.txt)
diff /tmp/inv_before.txt /tmp/inv_after.txt
```
Baseline esperado: `FAIL_BEFORE = 0`, `FAIL_AFTER <= 0`. Colar: inv_before/inv_after (tail), diff, o output do proof runtime-real (passo 3, com os dois "OK"), o `rg` do passo 2, `git --no-pager diff --stat` e `./run.sh --smoke` (deve imprimir `boot ok`). O gauntlet `--only loop` fica DEFERIDO para GPU exclusiva (declarar explicitamente).

---

## Gambiarras específicas desta sprint

- **`getattr(entry, "is_reject", False)` em vez de `entry.is_reject` direto:** defensivo contra entries construídos por caminhos que não passem pelo default (ex.: histórico desserializado de sessão antiga). Custo nulo, robustez a mais.
- **`force_done_threshold=1` no tier do 3b (`model_tier.py:114`):** é o que torna o poison determinístico (um único SKIP basta). Não mexer no threshold — o fix é na origem (não contar a rejeição), não no threshold.
- **Rejeição é 1x/turno por guard:** as flags `_seq_edit_rejected`/`_tool_match_rejected`/`_done_rejected` garantem no máximo uma entrada `is_reject=True` por guard por turno — por isso excluí-la não pode gerar loop.
- **`to_messages` inalterado:** o modelo continua vendo a rejeição como `[resultado de write_file]\n<hint>` — o campo `is_reject` é só metadado interno do detector, não muda o que chega ao LLM.

---

## Validação humana (checklist do usuário)

```bash
cd /home/andrefarias/Desenvolvimento/Nyx-Code
git --no-pager show --stat HEAD

# Com o stack real (GPU exclusiva): pedir para editar um arquivo que já existe.
# A Nyx deve: rejeitar 1x ('leia primeiro'), ler, re-emitir a escrita e CONCLUIR
# com o arquivo alterado -- NÃO 'Não consegui completar a criação/edição pedida'.

ls dev-journey/06-sprints/concluidos/SPRINT_LOOP_GUARD_REJECT_REPETITION_POISON_01.md  # existe
```

---

## Riscos e não-objetivos

| Risco / não-objetivo | Decisão |
|-------|-----------|
| Reduzir `force_done_threshold` ou mexer na lógica de `has_results` | **NÃO-OBJETIVO.** O fix é na origem (não contar a rejeição como ação). O threshold é intencional para o 3b. |
| Marcar bloqueios duros (plan_mode/permissão/preflight/hook) como `is_reject` | **PROIBIDO.** Esses devem contar para repetição (anti-spam de tool bloqueada). |
| Tornar `is_exact_repeat` ciente de `is_reject` | Desnecessário — usa `_last_action`, que a rejeição não atualiza (já imune). Não tocar. |
| Persistir `is_reject` na serialização de sessão (`to_messages`/dump) | Fora de escopo — é metadado interno do detector; `getattr` cobre entries sem o campo. Se o dono quiser persistência, sprint nova (anti-débito, `feedback_nenhum_debito`). |
| Cobrir o mesmo poison via `is_semantic_repeat` para tools de LEITURA re-emitidas após tool-match | Já coberto pela filtragem em `is_semantic_repeat` (Edit 4); sem cenário adicional pendente. |

---

## Referências

- BRIEF: `/home/andrefarias/Desenvolvimento/Nyx-Code/VALIDATOR_BRIEF.md`
- Origem: auditoria de prontidão 2026-07-12, relatório durável `dev-journey/07-reports/AUDIT_2026_07_12.md` §3 (briefing efêmero da sessão de auditoria)
- Detector de repetição (origem): `dev-journey/06-sprints/concluidos/SPRINT_P05_REPETITION_DETECTOR.md`
- Guards do contrato: SEQ-EDIT-ENFORCE-EDITFILE-01 (401), EXEC-CONTRACT-TOOL-MATCH-01, LOOP-RESULT-NOT-AS-INPUT-01, LOOP-ACTIONTYPE-FALLBACK-DONE-01 (comentários inline em `nyx/agent/loop/_iteration.py`)
- Origem: auditoria de prontidão 2026-07-12 (achado verificado adversarialmente, evidência file:line)

---

*"A infra manda o modelo corrigir e re-emitir; se ela mata o turno porque a re-emissão obediente 'parece repetição', a infra está sabotando o próprio contrato. Não punir a obediência." -- ADR-032/033/034*
