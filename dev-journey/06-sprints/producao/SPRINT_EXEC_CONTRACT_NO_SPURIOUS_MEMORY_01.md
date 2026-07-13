## 0. SPEC (machine-readable)

```yaml
sprint:
  id: EXEC-CONTRACT-NO-SPURIOUS-MEMORY-01
  title: "Contrato G-higiene: suprimir write_memory espontâneo em turno de leitura pura sem intent de memória"
  onda: 48
  prioridade: MEDIA
  tipo: Feature
  dependencias: [EXEC-CONTRACT-TOOL-MATCH-01, EXEC-CONTRACT-NO-HALLUCINATED-RESULT-01]
  desbloqueia: []

  touches:
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/agent/loop/_iteration.py
      reason: "import de wants_save_memory a nivel de modulo; constante _SPURIOUS_MEMORY_NOTE; helper _spurious_memory_reject; wiring nos 2 caminhos de execução de tool (nativo + parser fallback), junto dos guards irmaos (tool-match, seq-edit)"
      linhas_alvo: "topo de imports (apos linha 22, wants_read_only); bloco de constantes _IterationMixin (junto de _TOOL_MATCH_HINT ~207); helper novo (junto de _tool_match_reject ~288); _execute_tool_calls apos o bloco tm_hint (~353); _execute_parsed_action apos o bloco tm_hint (~584)"
  creates: []
  removes: []

  forbidden:
    - "Adicionar emoji"
    - "Usar 'print()' fora de cli.py/output.py"
    - "Menção a IA proprietária"
    - "Quebrar o few-shot legítimo de write_memory (368/404/MEMORY-INTENT-ENFORCE-01): o guard só suprime quando wants_read_only(original)=True E wants_save_memory(original)=False"
    - "Aplicar o guard a qualquer tool que não seja write_memory"
    - "Suprimir write_memory em turno que NÃO seja leitura pura (chat, code, tool-needed com escrita) -- alta precisão, baixo falso-positivo"
    - "Tocar: apresentação da 399, sanitize da 397, anti-recursão da 400, tool-match da EXEC-CONTRACT-TOOL-MATCH-01, seq-edit da SEQ-EDIT-ENFORCE-EDITFILE-01, gating de tools, priorização do cap (linha 1090), cascata OOM, o forcing do proxy MEMORY-INTENT-ENFORCE-01 (proxy.py:777)"

  tests:
    - cmd: "./run.sh --gauntlet --only rapido"
      timeout: 300
      deve_passar: true
    - cmd: "python -m ruff check nyx/agent/loop/_iteration.py"
      timeout: 60
      deve_passar: true

  acceptance_criteria:
    - "Turno de leitura pura (wants_read_only=True) SEM intent de memória (wants_save_memory=False) + write_memory chamado -> write_memory é suprimido (não executa, não grava em ~/.nyx/memory/, files_modified fica 0), registrado como nota benigna visível (ADR-026)"
    - "Turno com intent de memória (wants_save_memory=True, ex: 'lembra que X') -> write_memory PRESERVADO e executado (guard não dispara; few-shot 368/404 intacto)"
    - "Turno de escrita/código ou chat (wants_read_only=False) -> write_memory PRESERVADO (guard não dispara)"
    - "Guard aplicado nos DOIS caminhos de execução (nativo + parser fallback), na mesma posição dos guards irmãos"
    - "Proof runtime: 'liste os arquivos em ~/Desktop' -> list_files mostra a lista real; write_memory NÃO executa; files_modified=0; nenhum arquivo novo em ~/.nyx/memory/<projeto>/"
    - "ruff limpo; acentuação rc=0; smoke boot exit 0; invariantes 14/14; gauntlet rapido 100%"
```

---

# Sprint EXEC-CONTRACT-NO-SPURIOUS-MEMORY-01 — Contrato G-higiene: nada de memória espontânea

**Status:** PENDENTE
**Data criação:** 2026-07-12
**Modelo obrigatório:** claude-opus-4-7 (executor-sprint autorizado pelo dono nesta onda)

---

## Contexto do projeto (snapshot — não referência)

> **ADRs relevantes (inline):**
> - **ADR-032 A INFRA CARREGA O MODELO:** quando o 3b faz mais do que foi pedido (pediram LISTAR, ele lista E salva memória), a infra apara a verbosidade sem quebrar o comportamento legítimo.
> - **ADR-026 NADA SILENCIOSO:** o descarte da tool espontânea vira evento visível no histórico, nunca some só no log.
> - **ADR-033 A CADEIA NUNCA QUEBRA.** ADR-009, ADR-001, ADR-006, ADR-005, ADR-024.
>
> **Estado (2026-07-12):** `qwen2.5-coder:3b`, Ollama :11435, proxy :11436. ONDA-48 núcleo do contrato CONCLUIDO: 399 (`f0883a1`), 397 (`6c61f1d`), 400 (`b1a17fe`), 398 (`2e15c81`), 401 (`2a89e19`). Guards irmãos já no loop: tool-match (EXEC-CONTRACT-TOOL-MATCH-01), seq-edit (SEQ-EDIT-ENFORCE-EDITFILE-01). Esta sprint é um achado colateral catalogado: **COL-398-A**.

---

## Problema

**Achado COL-398-A SPURIOUS-WRITE-MEMORY [MEDIA]** (runtime da validação as-user da 398, turno "listar"):

- ao pedir **só** "liste os arquivos em ~/Desktop" o 3b chamou `list_files` (correto) **E TAMBÉM** `write_memory` espontâneo, gerando `files_modified=1` sem o usuário pedir para lembrar de nada.
- **Não é a V03** (WRONG-TOOL-SELECTED): a V03 criava lixo arbitrário no workspace do usuário via `write_file`. Aqui a tool é `write_memory`, que grava em `~/.nyx/memory/<projeto>/` (diretório protegido de memória — ver `nyx/agent/tools/write_memory.py:56-67`), **não** no workspace. Ainda assim é um efeito colateral **não solicitado**: grava um arquivo de memória e incrementa o contador `files_modified` para 1.
- É **verbosidade do modelo**: o 3b acrescentou uma ação a mais além da que resolvia o pedido.

**Causa-raiz:** o loop executa toda tool que o modelo emite. Quando o pedido é **leitura pura** e não há **nenhum sinal de intent de memória**, uma chamada de `write_memory` é ruído — a infra deveria apará-la (como já apara `write_file` contraditório na EXEC-CONTRACT-TOOL-MATCH-01), sem tocar no caminho legítimo de `write_memory` ("lembra que X"), que foi endurecido nas sprints 368/404 (MEMORY-INTENT-ENFORCE-01).

**Por que `write_memory` incrementa `files_modified`:** `WriteMemoryTool.execute` retorna `ActionResult(..., files_modified=[str(path)])` (`write_memory.py:67`); esse resultado é agregado por `Session.track_files` → `self._files_modified.update(...)` (`session.py:72-74`), fazendo `files_modified_count` = 1. Suprimir a tool **antes** do `execute` zera os dois efeitos (gravação + contador).

---

## Solução proposta

**Guard de higiene, alta precisão, mesmo padrão dos guards irmãos (ponto A do loop):**

1. `nyx/agent/loop/_iteration.py`: novo helper `_spurious_memory_reject(name)` que retorna uma **nota benigna** (str) a registrar, ou `None`. Dispara **somente** quando **todas** as condições valem:
   - `name == "write_memory"`;
   - `_wants_read_only(self._original_input)` — o pedido é leitura pura (verbo de leitura/listagem/busca E nenhum verbo de mutação);
   - `not _wants_save_memory(self._original_input)` — o pedido **não** tem intent de memória.
2. Quando dispara: registra a nota via `add_tool_call(name, args, nota)` e faz `continue`/`return None` **antes** de `self._on_tool`/`execute` — a tool não roda, não grava, não incrementa `files_modified`. O evento fica visível no histórico (ADR-026).

**Sem flag 1x/turno (diferença deliberada face aos guards irmãos):** tool-match e seq-edit usam flag de rejeição-1x porque **re-emitem** um hint esperando o modelo refazer com a tool certa. Aqui **não há tool certa para refazer** — o comportamento correto é simplesmente **não salvar memória**. Logo o guard **descarta toda** chamada de `write_memory` que se qualifique no turno (dropar de novo é inócuo: não grava nada, não incrementa contador). A nota é **terminal/benigna** (não um "refaça"), para não convidar retry; `MAX_ITERATIONS` continua sendo a rede.

**Blindagem do caminho legítimo (368/404):** dupla condição. Em "lembra que meu nome é Andre": `wants_read_only`=False (sem verbo de leitura) **e** `wants_save_memory`=True → guard **não** dispara. O forcing do proxy (`proxy.py:777`, MEMORY-INTENT-ENFORCE-01) e a priorização do cap (`_iteration.py:1090`) só atuam com `wants_save_memory`=True, cenário em que o guard nunca dispara — zero conflito.

---

## Arquivos alvo (paths absolutos)

### `/home/andrefarias/Desenvolvimento/Nyx-Code/nyx/agent/loop/_iteration.py`

#### Edit 1 — import de `wants_save_memory` a nível de módulo (após linha 22)

**Antes:**
```python
from nyx.agent.intent import classify as _classify_intent
from nyx.agent.intent import wants_read_only as _wants_read_only
```
**Depois:**
```python
from nyx.agent.intent import classify as _classify_intent
from nyx.agent.intent import wants_read_only as _wants_read_only
from nyx.agent.intent import wants_save_memory as _wants_save_memory
```

> Nota: `wants_save_memory` hoje é importado inline dentro de `_select_tools` (linha 1088, `as _wsm`). O import a nível de módulo não conflita — mantenha o inline como está (fora de escopo); apenas adicione o import no topo para o novo helper.

#### Edit 2 — constante `_SPURIOUS_MEMORY_NOTE` (junto de `_TOOL_MATCH_HINT`, ~linha 207, na classe `_IterationMixin`)

**Depois (adicionar após o bloco `_TOOL_MATCH_HINT`):**
```python
    # EXEC-CONTRACT-NO-SPURIOUS-MEMORY-01 (COL-398-A): write_memory espontâneo
    # num turno de leitura pura SEM pedido de memória. Nota benigna/terminal
    # (não convida retry) -- a tool é descartada antes de executar.
    _SPURIOUS_MEMORY_NOTE = (
        "write_memory ignorado: o pedido é de leitura e você não pediu para "
        "lembrar nada. Não salve memória; conclua com o resultado da leitura."
    )
```

#### Edit 3 — helper `_spurious_memory_reject` (método de `_IterationMixin`, junto de `_tool_match_reject`, ~linha 288)

**Depois (adicionar):**
```python
    def _spurious_memory_reject(self, name: str) -> str | None:
        """EXEC-CONTRACT-NO-SPURIOUS-MEMORY-01 (COL-398-A): nota a registrar quando
        o modelo chama write_memory de forma espontânea -- pedido de leitura pura
        E sem intent de memória. None se deve deixar passar.

        Blindagem do few-shot legítimo (368/404): exige wants_read_only=True E
        wants_save_memory=False. Em 'lembra que X' ambos falham -> passa.
        Sem flag 1x: descarta toda chamada que se qualifique no turno (dropar de
        novo é inócuo -- não grava nem incrementa files_modified)."""
        if name != "write_memory":
            return None
        original = getattr(self, "_original_input", "") or ""
        if _wants_read_only(original) and not _wants_save_memory(original):
            return self._SPURIOUS_MEMORY_NOTE
        return None
```

#### Edit 4 — wiring em `_execute_tool_calls` (após o bloco `tm_hint`, ~linha 353)

# Localização: logo após o bloco `if tm_hint:` (tool-match), antes do bloco `se_hint` (seq-edit)
**Antes:**
```python
            tm_hint = self._tool_match_reject(name)
            if tm_hint:
                self._tool_match_rejected = True
                logger.warning("[loop] tool-match: pedido de leitura, tool mutante %s", name)
                self._session.add_tool_call(name, args, tm_hint)
                continue

            # SEQ-EDIT-ENFORCE-EDITFILE-01 (V05): edição sequencial insegura
```
**Depois:**
```python
            tm_hint = self._tool_match_reject(name)
            if tm_hint:
                self._tool_match_rejected = True
                logger.warning("[loop] tool-match: pedido de leitura, tool mutante %s", name)
                self._session.add_tool_call(name, args, tm_hint)
                continue

            # EXEC-CONTRACT-NO-SPURIOUS-MEMORY-01 (COL-398-A): write_memory espontâneo
            # em leitura pura sem pedido de memória -> descarta (não grava, não conta).
            sm_note = self._spurious_memory_reject(name)
            if sm_note:
                logger.info("[loop] write_memory espontâneo suprimido (leitura pura, sem intent de memória)")
                self._session.add_tool_call(name, args, sm_note)
                continue

            # SEQ-EDIT-ENFORCE-EDITFILE-01 (V05): edição sequencial insegura
```

#### Edit 5 — wiring em `_execute_parsed_action` (após o bloco `tm_hint` do parser, ~linha 584)

# Localização: logo após o bloco `if tm_hint:` do parser fallback, antes do bloco `se_hint`
**Antes:**
```python
        tm_hint = self._tool_match_reject(tool_name)
        if tm_hint:
            self._tool_match_rejected = True
            logger.warning("[loop] tool-match (parser): pedido leitura, tool mutante %s", tool_name)
            self._session.add_tool_call(tool_name, remapped, tm_hint)
            return None

        # SEQ-EDIT-ENFORCE-EDITFILE-01 (V05): idem caminho nativo, no parser fallback.
```
**Depois:**
```python
        tm_hint = self._tool_match_reject(tool_name)
        if tm_hint:
            self._tool_match_rejected = True
            logger.warning("[loop] tool-match (parser): pedido leitura, tool mutante %s", tool_name)
            self._session.add_tool_call(tool_name, remapped, tm_hint)
            return None

        # EXEC-CONTRACT-NO-SPURIOUS-MEMORY-01 (COL-398-A): idem caminho nativo, no
        # parser fallback -- write_memory espontâneo em leitura pura é descartado.
        sm_note = self._spurious_memory_reject(tool_name)
        if sm_note:
            logger.info("[loop] write_memory espontâneo suprimido (parser)")
            self._session.add_tool_call(tool_name, remapped, sm_note)
            return None

        # SEQ-EDIT-ENFORCE-EDITFILE-01 (V05): idem caminho nativo, no parser fallback.
```

---

## Aritmética (diff, não meta de linhas)

Sprint **sem meta numérica** de linhas de arquivo (não há alvo `_iteration.py <NL`). Estimativa de diff:

```
~ 1 arquivo modificado (nyx/agent/loop/_iteration.py)
+ ~30 linhas líquidas (1 import + 1 constante ~6L + 1 helper ~14L + 2 wirings ~6L cada)
- 0 linhas removidas
```

Sem mudança em `intent.py`: `wants_read_only` (EXEC-CONTRACT-TOOL-MATCH-01) e `wants_save_memory` (MEMORY-INTENT-ENFORCE-01) **já existem** e são reusados — o executor deve confirmar via grep antes de iniciar (lição 4).

---

## Comandos de verificação (literais, copy-paste)

```bash
cd /home/andrefarias/Desenvolvimento/Nyx-Code

# 1. Confirmar que os identificadores reusados EXISTEM (lição 4 -- pré-passo)
rg -n "def wants_read_only|def wants_save_memory" nyx/agent/intent.py
rg -n "_original_input" nyx/agent/loop/_core.py          # setado em run (linha ~308)

# 2. Estática + acentuação
python -m ruff check nyx/agent/loop/_iteration.py
python3 ~/.config/zsh/scripts/validar-acentuacao.py --paths nyx/agent/loop/_iteration.py

# 3. Unit sanity das condições do guard (funções puras -- inline)
venv/bin/python -c "
from nyx.agent.intent import wants_read_only as r, wants_save_memory as s
def fires(u): return r(u) and not s(u)
print('leitura pura:', fires('liste os arquivos em ~/Desktop'))            # True  -> SUPRIME
print('lembra que X:', fires('lembra que meu nome é Andre'))               # False -> PRESERVA
print('leitura + memória:', fires('liste e lembra que revisei o Desktop')) # False -> PRESERVA
print('escrita:', fires('crie um arquivo x.py'))                           # False -> PRESERVA
print('chat:', fires('explique recursividade'))                            # False -> PRESERVA
"
# ESPERADO: True, False, False, False, False

# 4. Invariantes + smoke
bash scripts/sprint_invariants.sh          # PASS 14/14, FAIL 0
./run.sh --smoke                            # boot ok, exit 0

# 5. Gauntlet (higiene não deve regredir nada)
./run.sh --gauntlet --only rapido           # 100%
```

---

## Proof-of-work esperado

Comandos runtime-reais que o executor deve colar (contratos do VALIDATOR_BRIEF seção [CORE]):

```bash
cd /home/andrefarias/Desenvolvimento/Nyx-Code

# --- Baseline de invariantes (antes/depois) ---
bash scripts/sprint_invariants.sh > /tmp/inv_before.txt 2>&1
FAIL_BEFORE=$(grep -c "^\[FAIL\]" /tmp/inv_before.txt)
# ... implementar ...
bash scripts/sprint_invariants.sh > /tmp/inv_after.txt 2>&1
FAIL_AFTER=$(grep -c "^\[FAIL\]" /tmp/inv_after.txt)
diff /tmp/inv_before.txt /tmp/inv_after.txt   # esperado: sem novos FAIL

# --- Smoke boot (check #13, obrigatório antes de CONCLUIDA) ---
./run.sh --smoke                              # boot ok, exit 0

# --- PROOF RUNTIME-REAL as-user (COL-398-A) ---
# memória antes (para provar que nada novo foi gravado)
ls -la ~/.nyx/memory/Nyx-Code/ 2>/dev/null > /tmp/mem_antes.txt || echo "sem dir" > /tmp/mem_antes.txt
printf '%s\n' 'liste os arquivos em ~/Desktop' \
  | NYX_AUTO_APPROVE=1 ./run.sh --headless 2>/dev/null
ls -la ~/.nyx/memory/Nyx-Code/ 2>/dev/null > /tmp/mem_depois.txt || echo "sem dir" > /tmp/mem_depois.txt
diff /tmp/mem_antes.txt /tmp/mem_depois.txt   # ESPERADO: vazio (nenhuma memória nova)
# ESPERADO na saída: list_files chamado, lista REAL sob "Resultado:"; write_memory
#   NÃO executado (aparece nota "write_memory ignorado" no histórico); files_modified=0.

# --- Regressão do caminho legítimo (368/404 NÃO pode quebrar) ---
printf '%s\n' 'lembra que meu apelido é Nyx-dev' \
  | NYX_AUTO_APPROVE=1 ./run.sh --headless 2>/dev/null
# ESPERADO: write_memory EXECUTA; grava em ~/.nyx/memory/Nyx-Code/; files_modified=1.

# --- Estática + acentuação + gauntlet ---
python -m ruff check nyx/agent/loop/_iteration.py                                  # All checks passed
python3 ~/.config/zsh/scripts/validar-acentuacao.py --paths nyx/agent/loop/_iteration.py  # rc=0
./run.sh --gauntlet --only rapido                                                  # 100%
git --no-pager diff --stat                                                         # 1 arquivo
```

Colar: `inv_before`/`inv_after` (tail) + diff, `./run.sh --smoke` (últimas linhas), unit sanity (passo 3), os DOIS proofs runtime (leitura pura suprime / memória legítima preserva) com `diff /tmp/mem_*`, ruff, acentuação rc=0, gauntlet rapido, `git diff --stat`.

- Acentuação periférica: varredura em todos arquivos modificados (`validar-acentuacao.py --paths`).
- Hipótese verificada: `rg` de `wants_read_only`, `wants_save_memory`, `_original_input` (passo 1) antes de codar.
- Sem validação visual (mudança headless de loop, sem UI).

---

## Critério binário de aceite (IA executora)

- [ ] `_spurious_memory_reject` em `_iteration.py`; dispara SÓ com `name=="write_memory"` E `wants_read_only(original)` E `not wants_save_memory(original)`
- [ ] Guard aplicado nos DOIS caminhos (nativo + parser), na mesma posição dos guards irmãos (após tool-match)
- [ ] Import de `wants_save_memory` a nível de módulo; constante `_SPURIOUS_MEMORY_NOTE` na classe
- [ ] Unit sanity colado: leitura pura True; lembra/leitura+memória/escrita/chat False
- [ ] Proof runtime as-user colado: leitura pura NÃO grava memória (`diff /tmp/mem_*` vazio, files_modified=0); "lembra que X" AINDA grava (regressão 368/404 ok)
- [ ] `ruff` limpo, acentuação rc=0, smoke boot exit 0, invariantes 14/14, gauntlet rapido 100%, `FAIL_AFTER <= FAIL_BEFORE`
- [ ] `SPRINT_ORDER_MASTER.md` marca 411 CONCLUIDA; spec movida para `concluidos/`
- [ ] NÃO commitar; NÃO tocar Checkpoint.md

---

## Guardrails anti-engodo (obrigatórios)

NÃO marcar concluída se:
- O guard dispara com `wants_save_memory`=True (quebra o few-shot legítimo 368/404 -- write_memory nunca mais grava por pedido explícito).
- O guard dispara fora de leitura pura (suprime write_memory num turno de código/chat onde o modelo salvaria memória por decisão razoável).
- O guard afeta qualquer tool que não `write_memory`.
- Proof runtime não colado, ou a memória legítima ("lembra que X") deixou de gravar.

Se algo falhar: `[SPRINT 411] BLOQUEADA: <motivo 1 linha>`.

---

## Gambiarras específicas desta sprint

- **Quebrar o legítimo:** dupla condição obrigatória (`wants_read_only` E `not wants_save_memory`). O teste "lembra que X" e o "liste E lembra" devem dar False (preservam).
- **Sem flag 1x:** ao contrário de tool-match/seq-edit, o guard descarta TODA chamada qualificada no turno (não há tool certa para re-emitir). Dropar de novo é inócuo. A nota é benigna/terminal, não um "refaça".
- **Só write_memory:** o guard não é um gate genérico. Nenhuma outra tool entra em escopo.
- **Efeito colateral real:** confirme que a supressão acontece ANTES de `execute` (o `continue`/`return None` precede `self._on_tool`/`self._tools.execute`), senão a memória grava e `files_modified` incrementa mesmo assim.

---

## Validação humana (checklist do usuário)

```bash
cd /home/andrefarias/Desenvolvimento/Nyx-Code
git --no-pager diff --stat
ls -la ~/.nyx/memory/Nyx-Code/ > /tmp/mem_antes.txt 2>/dev/null || echo "sem dir" > /tmp/mem_antes.txt
./run.sh   # peça: "liste os arquivos em ~/Desktop"
ls -la ~/.nyx/memory/Nyx-Code/ > /tmp/mem_depois.txt 2>/dev/null || echo "sem dir" > /tmp/mem_depois.txt
diff /tmp/mem_antes.txt /tmp/mem_depois.txt   # ESPERADO: vazio (nada gravado)
./run.sh   # agora peça: "lembra que meu apelido é Nyx-dev" -> DEVE gravar memória
ls dev-journey/06-sprints/concluidos/SPRINT_EXEC_CONTRACT_NO_SPURIOUS_MEMORY_01.md  # existe
```

---

## Riscos

| Risco | Mitigação |
|-------|-----------|
| Guard suprime write_memory legítimo ("lembra que X") | Dupla condição: `wants_save_memory`=True o desarma. Em "lembra que X", `wants_read_only`=False também. Dupla blindagem. |
| Turno de leitura em que salvar memória seria útil | Não há caso legítimo: leitura pura sem pedido de memória não deveria gravar nada. Falso-positivo aqui é o comportamento desejado (aparar verbosidade). |
| Nota registrada convida o modelo a re-tentar em loop | Nota é benigna/terminal ("conclua com o resultado da leitura"), não "refaça". Dropar de novo é inócuo; `MAX_ITERATIONS` é a rede. |
| `_original_input` ausente numa iteração | `getattr(self, "_original_input", "") or ""` -- string vazia -> `wants_read_only`=False -> não dispara (fail-safe). |

---

## Referências

- BRIEF: `/home/andrefarias/Desenvolvimento/Nyx-Code/VALIDATOR_BRIEF.md`
- Precedente direto (mesmo padrão de guard, ponto A do loop): `dev-journey/06-sprints/concluidos/SPRINT_EXEC_CONTRACT_TOOL_MATCH_01.md`
- Caminho legítimo a preservar: `dev-journey/06-sprints/concluidos/SPRINT_MEMORY_INTENT_ENFORCE_01.md` (368/404, forcing em `proxy.py:777`)
- Achado: `SPRINT_ORDER_MASTER.md` linha 411 (bloco ONDA-48), COL-398-A; evidência runtime 398, turno "listar"
- Código-âncora: `nyx/agent/tools/write_memory.py:43-68` (execute grava + `files_modified`), `nyx/agent/session.py:72-74` (track_files), `nyx/agent/intent.py:112/157` (`wants_save_memory`/`wants_read_only`)

---

*"A ferramenta a mais não erra sozinha -- a infra que a deixa agir junto é que suja o resultado." -- princípio de execução (dev-journey/02-architecture/DESENHO_CONTRATO_EXECUCAO.md)*
