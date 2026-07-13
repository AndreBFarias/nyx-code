## 0. SPEC (machine-readable)

```yaml
sprint:
  id: LOOP-FALLBACK-GATES-PARITY-01
  numero: 416
  title: "Paridade de gates no parser fallback -- permissão async, plan mode e hooks/UI faltantes no caminho preferido do pior modelo"
  onda: 48
  prioridade: ALTA
  tipo: Bugfix
  dependencias: []
  desbloqueia: []
  absorve: []

  touches:
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/agent/loop/_iteration.py
      reason: "replicar em _execute_parsed_action (parser fallback) os gates que só existem no caminho nativo _execute_tool_calls: await do callback de permissão async, gate de plan mode, hooks PreToolUse/PostToolUse, _tool_summary.track, _diagnostics.record_warning e _on_tool_result"
      linhas_alvo: "594-636 (bloco entre on_tool e post_validate do parser fallback)"
  creates: []
  removes: []

  forbidden:
    - "Adicionar emoji"
    - "Usar 'print()' fora de cli.py/output.py"
    - "Mencao a IA proprietaria"
    - "Tocar o caminho nativo _execute_tool_calls (383-524) -- ele já tem os gates; a mudança é SÓ no fallback"
    - "Extrair helper compartilhado nesta sprint (refatoração do caminho nativo é risco de regressão -- ver Fora de escopo)"
    - "Alterar a assinatura de _execute_parsed_action ou de _on_permission"
    - "Tocar plan_mode.py, permissions.py, app.py ou o proxy"
    - "Alterar a ordem/semântica dos guards já presentes no fallback (echo/tool-match/seq-edit)"

  tests:
    - cmd: "/home/andrefarias/.local/bin/ruff check nyx/agent/loop/_iteration.py"
      deve_passar: true
    - cmd: "python3 ~/.config/zsh/scripts/validar-acentuacao.py --paths nyx/agent/loop/_iteration.py"
      deve_passar: true
    - cmd: "bash scripts/sprint_invariants.sh"
      deve_passar: true
    - cmd: "./run.sh --smoke"
      deve_passar: true
    - cmd: "./run.sh --gauntlet --only rapido"
      timeout: 300
      deve_passar: true
      nota: "DEFERIDO para GPU exclusiva -- ver Proof-of-work"

  acceptance_criteria:
    - "AC1 (permissão async): _execute_parsed_action passa a tratar callback awaitable -- `if inspect.isawaitable(approved): approved = await approved` entre a chamada de _on_permission e o `if not approved`, idêntico ao caminho nativo (L403-404). Prova: callback async retorna coroutine -> é aguardado (não é truthy silencioso); com resposta False a tool NÃO executa e NÃO chama mark_confirmed"
    - "AC2 (plan mode): _execute_parsed_action bloqueia tool de escrita em plan mode ANTES da checagem de permissão, com `if not is_tool_allowed_in_plan_mode(tool_name): ... return None`, idêntico ao nativo (L383-388). Prova: com plan mode ATIVO, write_file via parser fallback é bloqueado (add_tool_call com 'Bloqueado: modo planejamento ativo') e NÃO chega a _tools.execute"
    - "AC3 (hooks/UI): _execute_parsed_action roda PreToolUse (com block -> return None), PostToolUse, _tool_summary.track, _diagnostics.record_warning em falha e _on_tool_result, replicando o nativo (L441-489). Prova: hook PreToolUse com blocked=True impede _tools.execute no fallback; _on_tool_result é chamado com o resultado"
    - "Caminho nativo _execute_tool_calls intacto (nenhuma linha 383-524 alterada); guards já presentes no fallback (echo/tool-match/seq-edit) intactos"
    - "ruff limpo, acentuação rc=0, invariantes FAIL_AFTER <= FAIL_BEFORE, smoke boot ok"
```

---

# Sprint LOOP-FALLBACK-GATES-PARITY-01 — Paridade de gates entre o caminho nativo e o parser fallback

**Status:** PENDENTE
**Data criação:** 2026-07-12
**Modelo obrigatório:** claude-opus-4-7 (executor-sprint autorizado pelo dono nesta onda)

---

## Contexto do projeto (snapshot — não referência)

> **Missão (ADR-032/033/034):** o Nyx-Code faz o pior LLM local (qwen2.5-coder:3b) na pior máquina possível parecer o Claude Code offline. Robustez pertence à INFRA, não ao modelo. O usuário-alvo é leigo e sem hardware bom -- ele confia que o modo de permissões e o plan mode o protegem. Uma garantia de segurança que só vale no caminho JSON nativo (que o 3b usa MENOS) e falha no caminho textual (que o 3b usa MAIS) e uma garantia que engana justamente o usuário que mais precisa dela. <!-- noqa-anonimato -->
>
> **Estado (2026-07-12):** `qwen2.5-coder:3b`. Ports: Ollama `11435`, proxy `11436`. O AgentLoop tem DOIS caminhos de execução de tool: (A) nativo, `_execute_tool_calls` (tool_calls estruturados vindos do provider), e (B) fallback, `_execute_parsed_action` (tool_call extraído por parser de texto -- o que o 3b mais emite). Chamados em `nyx/agent/loop/_core.py:462` e `:488`. Ao longo de várias ondas os gates foram adicionados ao caminho A e replicados parcialmente no B (echo/tool-match/seq-edit já vieram); três gates ficaram para trás no B.
>
> **Modelo de permissões (memória do projeto):** leitura livre por default; escrita por modo -- Normal PERGUNTA, Plan PLANEJA (só leitura), Bypass livre. Achado desta sprint: no caminho B, Normal NÃO pergunta e Plan NÃO bloqueia.

---

## Problema

Auditoria de prontidão 2026-07-12 (achados verificados adversarialmente, com evidência file:line, reconferidos no código real -- as linhas NÃO deslizaram). O método `_execute_parsed_action` (`nyx/agent/loop/_iteration.py:528-668`), que executa toda tool_call que cai no parser fallback (o caminho preferido do 3b), diverge do caminho nativo `_execute_tool_calls` (L383-524) em três gates. Todos são o MESMO mecanismo: divergência estrutural entre os dois caminhos. São cobertos como ACs separados por serem falhas independentes e testáveis em separado.

### Achado 1 (ALTA) — callback de permissão async não é aguardado; coroutine truthy vira auto-aprovação silenciosa

Evidência (verificada) `_iteration.py:603-610`:

```python
if perm in (PermissionLevel.CONFIRM_ONCE, PermissionLevel.ALWAYS_CONFIRM):
    if self._on_permission:
        approved = self._on_permission(perm, tool_name, remapped)
        if not approved:
            self._session.add_tool_call(tool_name, remapped, f"Usuário negou: {tool_name}")
            return None
        if perm == PermissionLevel.CONFIRM_ONCE:
            self._permissions.mark_confirmed(tool_name)
```

Falta o tratamento que o caminho nativo tem em `_iteration.py:403-404`:

```python
if inspect.isawaitable(approved):
    approved = await approved
```

A TUI instala um callback ASYNC: `nyx/agent/tui/app.py:266` (`agent._on_permission = self._on_agent_permission`) e `app.py:913` (`async def _on_agent_permission(...)`). O docstring em `app.py:919` afirma "suporta sync/async via inspect.isawaitable em _iteration.py" -- mas isso só existe no caminho A.

**Impacto:** no caminho B, `self._on_permission(...)` retorna um objeto coroutine (sempre truthy), o `ConfirmScreen` NUNCA abre, `if not approved` e False e o write/edit/run executa SEM confirmação no modo Normal. Pior: `_iteration.py:609-610` chama `mark_confirmed(tool_name)`, e `nyx/agent/permissions.py:111` (`if action_type in self._confirmed_actions`) passa a auto-aprovar essa tool pelo resto da sessão TAMBÉM no caminho nativo. Quebra o modelo de permissões ("Normal pergunta") de forma silenciosa, mais um `RuntimeWarning: coroutine never awaited`.

### Achado 2 (ALTA) — plan mode não é checado; escrita/execução vazam em modo planejamento

Evidência (verificada): o caminho A tem o gate em `_iteration.py:383-388` (`if not is_tool_allowed_in_plan_mode(name): ... continue`). Em `_execute_parsed_action` (L528-668) NÃO existe nenhuma chamada a `is_tool_allowed_in_plan_mode`: do guard seq-edit (L586-592) o fluxo vai direto a `perm = self._permissions.check(tool_name, remapped)` (L597) e executa em L630. `nyx/agent/tools/plan_mode.py:17` confirma `PLAN_MODE_BLOCKED = {"write_file", "edit_file", "run_command", "create_file", "patch"}`; `app.py:264` assume "Plan bloqueia a escrita antes, no loop".

**Impacto:** o 3b em modo Plan frequentemente emite tool_call como texto (não JSON nativo) -- exatamente o caminho sem gate. `write_file`/`run_command` executam durante o planejamento, quebrando a garantia "Plan planeja" e mutando o FS do usuário-alvo no momento em que ele pediu explicitamente só leitura.

### Achado 3 (MEDIA) — parser fallback não roda hooks PreToolUse/PostToolUse nem _on_tool_result/_tool_summary/_diagnostics

Evidência (verificada): o caminho A roda hooks PreToolUse com block (`if any(r.blocked for r in pre_results): ... continue`, L452-457), PostToolUse (L466-479), `self._on_tool_result(...)` (L488-489), `self._tool_summary.track(...)` (L464) e `self._diagnostics.record_warning` em falha (L485-486). Em `_execute_parsed_action` (L627-666) NENHUM desses existe: após `result = await asyncio.to_thread(self._tools.execute, tool_name, remapped)` (L630) o fluxo vai direto a `post_validate`/`add_tool_call`.

**Impacto:** um hook do usuário com `block_on_failure` (garantia do HOOKS-DYNAMIC-03) e contornável por qualquer tool_call que caia no parser fallback -- o caminho preferido do pior modelo. E a ausência de `_on_tool_result` significa que na TUI o usuário vê a tool iniciar (`on_tool` dispara em L594) mas nunca vê o resultado ao vivo nesse caminho, dando impressão de travamento; falhas de tool também somem das métricas (`/debug`).

---

## Causa-raiz

Divergência estrutural entre `_execute_tool_calls` (nativo, L383-524) e `_execute_parsed_action` (fallback, L528-668). Cada gate novo foi adicionado primeiro ao nativo e depois replicado -- de forma incompleta -- ao fallback. Três gates ficaram para trás. Os imports necessários para o fix JÁ estão no topo do arquivo: `inspect` (L12) e `is_tool_allowed_in_plan_mode` (L45). Os atributos usados já são inicializados no construtor: `self._tool_summary`/`self._diagnostics` (`_core.py:170-171`), `self._on_tool_result` (`_core.py:127`), `self._hooks` (`_core.py:207/210`, acessado via `getattr(self, "_hooks", None)` no nativo).

**Divergência da investigação em relação ao briefing:** o briefing (fix sugerido do achado 3) recomenda EXTRAIR o pós-processamento comum para um helper compartilhado pelos dois caminhos, eliminando a divergência de raiz. Esta spec adota deliberadamente a REPLICAÇÃO ADITIVA em vez da extração: extrair um helper exige tocar o caminho nativo que HOJE funciona (risco de regressão numa área de segurança/permissões), e a regra de escopo cirúrgico manda o mínimo que fecha os achados. A extração é registrada como sprint follow-up própria (`LOOP-DUAL-PATH-UNIFY-01`, ver Fora de escopo) -- a divergência-raiz vira um ID, não some (feedback_nenhum_debito). Nenhuma outra divergência: as três evidências bateram com o código real linha a linha.

---

## Solução proposta

Três edições aditivas e cirúrgicas, todas dentro de `_execute_parsed_action`, replicando o bloco correspondente do caminho nativo. O caminho nativo NÃO e tocado. Ordem-alvo no fallback (espelha o nativo): on_tool -> plan_mode -> permissão (com await) -> repetição -> preflight -> PreToolUse -> execute -> tool_summary -> PostToolUse -> post_validate -> diagnostics -> on_tool_result -> add_tool_call.

---

## Arquivos alvo (paths absolutos)

### `/home/andrefarias/Desenvolvimento/Nyx-Code/nyx/agent/loop/_iteration.py`

#### Edit 1 — AC2: gate de plan mode, imediatamente antes da checagem de permissão

# Localização: entre o bloco `if self._on_tool:` (L594-595) e `perm = self._permissions.check(...)` (L597)
**Adicionar (espelha o nativo L383-388):**
```python
        if not is_tool_allowed_in_plan_mode(tool_name):
            logger.warning("[loop] bloqueado por plan_mode (parser): %s", tool_name)
            self._session.add_tool_call(
                tool_name, remapped, "Bloqueado: modo planejamento ativo. Use exit_plan_mode primeiro."
            )
            return None

```

#### Edit 2 — AC1: await do callback de permissão async

# Localização: dentro do `if self._on_permission:` do fallback (L604-610)
**Antes:**
```python
        if perm in (PermissionLevel.CONFIRM_ONCE, PermissionLevel.ALWAYS_CONFIRM):
            if self._on_permission:
                approved = self._on_permission(perm, tool_name, remapped)
                if not approved:
                    self._session.add_tool_call(tool_name, remapped, f"Usuário negou: {tool_name}")
                    return None
                if perm == PermissionLevel.CONFIRM_ONCE:
                    self._permissions.mark_confirmed(tool_name)
```
**Depois (adiciona só o bloco isawaitable, espelha o nativo L399-404):**
```python
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
```

#### Edit 3 — AC3: PreToolUse antes do execute; tool_summary/PostToolUse/diagnostics/on_tool_result depois

# Localização A: entre o loop de warnings do preflight (termina em L625) e o `import time as _time` (L627)
**Adicionar (espelha o nativo L441-457):**
```python
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

```

# Localização B: logo após `self._tool_durations.setdefault(...)` do execute (L631), antes de `vr = post_validate(...)` (L633)
**Adicionar (espelha o nativo L464-489):**
```python
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
```

# Localização C: logo após o loop de warnings do post_validate (L634-635), antes de `self._session.add_tool_call(...)` (L637)
**Adicionar (espelha o nativo L485-489):**
```python
        if not result.success:
            self._diagnostics.record_warning("tool", f"{tool_name}: {result.error[:120]}")

        if self._on_tool_result:
            self._on_tool_result(tool_name, result.output if result.success else result.error)

```

---

## Diff esperado (resumo)

```
~ 1 arquivo modificado (nyx/agent/loop/_iteration.py)
+ ~45 linhas líquidas (fix aditivo; sem meta de tamanho -- arquivo segue < 1200L)
```

Sem aritmética de extração: esta sprint não tem meta `arquivo < NNNL`. O único número relevante e o net-add (~45L) num único arquivo, todo dentro de `_execute_parsed_action`.

---

## Comandos de verificação (literais, copy-paste)

```bash
cd /home/andrefarias/Desenvolvimento/Nyx-Code

# 1. Confirmar as âncoras (linhas podem deslizar apos as edições -- reconferir):
rg -n "def _execute_parsed_action|is_tool_allowed_in_plan_mode|inspect.isawaitable|_tool_summary.track|PreToolUse|_on_tool_result|record_warning" nyx/agent/loop/_iteration.py

# 2. Estática + acentuação (ruff via binário direto -- não ha modulo ruff no venv, ver BRIEF):
/home/andrefarias/.local/bin/ruff check nyx/agent/loop/_iteration.py
python3 ~/.config/zsh/scripts/validar-acentuacao.py --paths nyx/agent/loop/_iteration.py

# 3. PROOF RUNTIME-REAL sem GPU (AgentLoop real, _execute_parsed_action real; SÓ o
#    _tools.execute e o _on_permission são faked -- nenhum Ollama/proxy/GPU envolvido).
./venv/bin/python - <<'PY'
import asyncio
from nyx.agent.loop._core import AgentLoop
from nyx.agent.models import AgentAction, ActionType, ActionResult
from nyx.agent.permissions import PermissionLevel
from nyx.agent.tools import plan_mode

# --- Fakes de transporte/execução (nada de rede/GPU) ---
executed = []
class FakeTools:
    def execute(self, name, args):
        executed.append((name, args))
        return ActionResult(success=True, output="ok", files_read=[], files_modified=[])

# on_permission ASYNC (idêntico ao que a TUI instala em app.py:913)
awaited = {"flag": False, "reply": True}
async def async_perm(perm, name, args):
    awaited["flag"] = True
    return awaited["reply"]

on_tool_result_calls = []

def build_loop():
    loop = AgentLoop(project_root=".", on_permission=async_perm,
                     on_tool_result=lambda n, o: on_tool_result_calls.append((n, o)))
    loop._tools = FakeTools()
    # força CONFIRM para o write_file (modo Normal)
    loop._permissions.check = lambda name, params=None: PermissionLevel.CONFIRM_ONCE
    return loop

def write_action():
    return AgentAction(action_type=ActionType.WRITE_FILE,
                       params={"file_path": "x.txt", "content": "a"})

# AC1: callback async NEGA -> não executa, foi AGUARDADO (não é coroutine truthy)
executed.clear(); awaited["flag"] = False; awaited["reply"] = False
loop = build_loop()
asyncio.run(loop._execute_parsed_action(write_action(), 1))
assert awaited["flag"] is True, "callback async NÃO foi aguardado (AC1)"
assert executed == [], f"AC1: negativa async deveria bloquear, mas executou {executed}"
assert "write_file" not in loop._permissions._confirmed_actions, "AC1: mark_confirmed vazou apos negativa"
print("AC1 OK: callback async aguardado; negativa bloqueia; sem mark_confirmed")

# AC2: plan mode ATIVO -> write_file bloqueado, NÃO chega a execute
executed.clear(); awaited["flag"] = False; awaited["reply"] = True
plan_mode.set_plan_mode(True)
try:
    loop = build_loop()
    asyncio.run(loop._execute_parsed_action(write_action(), 1))
    assert executed == [], f"AC2: plan mode deveria bloquear, mas executou {executed}"
    assert awaited["flag"] is False, "AC2: nem deveria chegar na checagem de permissão"
finally:
    plan_mode.set_plan_mode(False)
print("AC2 OK: plan mode bloqueia write_file no parser fallback")

# AC3: hook PreToolUse com blocked=True -> impede execute; on_tool_result não dispara aqui
executed.clear(); on_tool_result_calls.clear(); awaited["reply"] = True
class BlockRes:
    blocked = True
class BlockingHooks:
    def run(self, event, payload):
        return [BlockRes()] if event == "PreToolUse" else []
loop = build_loop()
loop._hooks = BlockingHooks()
asyncio.run(loop._execute_parsed_action(write_action(), 1))
assert executed == [], f"AC3: hook PreToolUse deveria bloquear, mas executou {executed}"
print("AC3a OK: hook PreToolUse bloqueante impede execute no fallback")

# AC3: caminho feliz -> on_tool_result e chamado com o resultado
executed.clear(); on_tool_result_calls.clear()
loop = build_loop()  # sem hooks bloqueantes
asyncio.run(loop._execute_parsed_action(write_action(), 1))
assert executed and executed[0][0] == "write_file", "AC3: deveria ter executado"
assert on_tool_result_calls and on_tool_result_calls[0][0] == "write_file", "AC3: _on_tool_result não chamado"
print("AC3b OK: _on_tool_result chamado com o resultado no fallback")
print("PROOF COMPLETO: paridade de gates restaurada")
PY

# 4. Confirmar que o caminho nativo NÃO foi tocado (diff so no _execute_parsed_action):
git --no-pager diff -U0 nyx/agent/loop/_iteration.py | rg -n "^@@"

# 5. Invariantes + smoke:
bash scripts/sprint_invariants.sh
./run.sh --smoke   # deve imprimir "boot ok"
```

> **Nota GPU / DEFERIDO:** o proof do passo 3 roda SEM Ollama/proxy/GPU (transporte e execução fakeados; o AgentLoop e o `_execute_parsed_action` são reais). O gauntlet (`./run.sh --gauntlet --only rapido`) exige GPU exclusiva -- executar só quando `pgrep -af "Luna.*driver|valida_sprint"` estiver vazio (protocolo anti-contenção do BRIEF). Se a GPU estiver em contenção, marcar o gauntlet como **DEFERIDO para GPU exclusiva** (precedente: specs 403/407) e concluir a sprint com o proof runtime-real + invariantes + smoke.

---

## Critério binário de aceite (IA executora)

- [ ] AC1: `if inspect.isawaitable(approved): approved = await approved` presente em `_execute_parsed_action`; proof passo 3 mostra callback async aguardado, negativa bloqueia, sem `mark_confirmed`
- [ ] AC2: `if not is_tool_allowed_in_plan_mode(tool_name): ... return None` antes da checagem de permissão; proof mostra write_file bloqueado em plan mode
- [ ] AC3: PreToolUse (com block -> return None), PostToolUse, `_tool_summary.track`, `_diagnostics.record_warning` em falha e `_on_tool_result` presentes; proof mostra hook bloqueante impedindo execute e `_on_tool_result` chamado no caminho feliz
- [ ] Caminho nativo `_execute_tool_calls` (L383-524) intacto; guards echo/tool-match/seq-edit do fallback intactos
- [ ] `ruff` limpo, acentuação rc=0, `FAIL_AFTER <= FAIL_BEFORE`, smoke boot ok
- [ ] Gauntlet `--only rapido` 100% OU marcado DEFERIDO para GPU exclusiva (justificar contenção)
- [ ] `SPRINT_ORDER_MASTER.md` marca 416 CONCLUIDA; spec movida para `concluidos/` (ação do orquestrador)
- [ ] NÃO commitar; NÃO tocar Checkpoint.md; NÃO tocar `plan_mode.py`/`permissions.py`/`app.py`/proxy

---

## Guardrails anti-engodo (obrigatórios)

NÃO marcar concluída se:
- O bloco `inspect.isawaitable` ficou DEPOIS do `if not approved` (a ordem importa -- await ANTES de avaliar `approved`).
- O gate de plan mode ficou DEPOIS da execução (`_tools.execute`) -- tem de bloquear ANTES.
- O PreToolUse ficou DEPOIS do `_tools.execute` (block_on_failure só vale se roda ANTES).
- Alguma linha do caminho nativo `_execute_tool_calls` (383-524) foi alterada (o objetivo e SÓ o fallback).
- Extraiu um helper compartilhado e mexeu no nativo (fora de escopo -- ver Fora de escopo; risco de regressão em área de permissões).
- Proof runtime-real (passo 3) não colado, ou algum dos quatro asserts (AC1/AC2/AC3a/AC3b) falhou.

Se algo falhar: `[SPRINT 416] BLOQUEADA: <motivo 1 linha>`.

---

## Proof-of-work obrigatório (4 passos)

```bash
bash scripts/sprint_invariants.sh > /tmp/inv_before.txt 2>&1
FAIL_BEFORE=$(grep -c "^\[FAIL\]" /tmp/inv_before.txt)
# implementar as 3 edições
bash scripts/sprint_invariants.sh > /tmp/inv_after.txt 2>&1
FAIL_AFTER=$(grep -c "^\[FAIL\]" /tmp/inv_after.txt)
diff /tmp/inv_before.txt /tmp/inv_after.txt
```
Baseline esperado: `FAIL_BEFORE = 0`, `FAIL_AFTER <= 0`. Colar: inv_before/inv_after (tail), diff, o output completo do proof runtime-real (passo 3, com os quatro OK), o `git --no-pager diff -U0` do passo 4 (mostrando que os `@@` caem só dentro de `_execute_parsed_action`), `git --no-pager diff --stat` e `./run.sh --smoke` (deve imprimir `boot ok`).

---

## Gambiarras específicas desta sprint

- **`getattr(self, "_hooks", None)`:** o `_hooks` e sempre inicializado no construtor (`_core.py:207/210`), mas o caminho nativo usa `getattr` defensivo -- o fallback espelha exatamente isso para não introduzir divergência de estilo nem quebrar em subclasses/mocks sem `_hooks`.
- **`return None` como equivalente de `continue`:** no nativo os blocos usam `continue` (laço sobre `tool_calls`); o fallback executa UMA ação e devolve `None` ao chamador (`_core.py:488`) para o loop externo prosseguir. `return None` e o análogo correto -- não usar `continue` (não ha laço aqui).
- **`tool_name` vs `name`:** o nativo passa `name` (nome cru da tool_call); o fallback passa `tool_name` (`ACTION_TO_TOOL.get(action.action_type)`, o nome real da tool). `PLAN_MODE_BLOCKED` e as chaves de permissão são o nome real da tool, então `tool_name` e o argumento correto em todos os gates novos.
- **`_permissions.check` fakeado no proof:** o proof substitui `loop._permissions.check` por um lambda que devolve `CONFIRM_ONCE` para forçar o caminho de confirmação sem depender da config de permissões default -- isola o AC exatamente no gate testado.

---

## Validação humana (checklist do usuário)

```bash
cd /home/andrefarias/Desenvolvimento/Nyx-Code
git --no-pager show --stat HEAD

# Com o stack real (GPU exclusiva), no modo Normal, mandar um prompt que force o 3b
# a emitir um write_file COMO TEXTO (parser fallback). A Nyx deve ABRIR o ConfirmScreen
# e ESPERAR -- não escrever silenciosamente. Depois, em Plan mode, o mesmo prompt deve
# ser BLOQUEADO ("modo planejamento ativo"), sem tocar o FS.

ls dev-journey/06-sprints/concluidos/SPRINT_LOOP_FALLBACK_GATES_PARITY_01.md  # existe apos conclusão
```

---

## Fora de escopo (anti-débito)

| Item | Decisão |
|------|---------|
| Extrair o pós-processamento comum (permissão + plan + hooks pre/post + tool_summary + diagnostics + on_tool_result) para um helper único usado pelos DOIS caminhos | **NÃO-OBJETIVO desta sprint.** E o fix-de-raiz da divergência (recomendado pelo briefing), mas exige tocar o caminho nativo que hoje funciona -- risco de regressão numa área de permissões. Registrar sprint própria `LOOP-DUAL-PATH-UNIFY-01` (feedback_nenhum_debito): refatorar os dois caminhos para um helper compartilhado, com o proof desta sprint como rede de segurança. Só depois que esta 416 estabilizar. |
| Hardening do `mark_confirmed` para não vazar entre caminhos | Coberto indiretamente: com AC1, a negativa async nunca mais chega ao `mark_confirmed`. Endurecer o `_confirmed_actions` em si e escopo de `permissions.py`, fora daqui. |
| Adicionar testes unitários permanentes em `tests/` para os dois caminhos | Não ha suíte de unit para `_iteration.py` hoje (confirmado). O proof runtime-real cobre a sprint; criar `tests/loop/test_dual_path_parity.py` e recomendável mas e escopo de `LOOP-DUAL-PATH-UNIFY-01`. |

---

## Referências

- BRIEF: `/home/andrefarias/Desenvolvimento/Nyx-Code/VALIDATOR_BRIEF.md`
- Origem: auditoria de prontidão 2026-07-12, relatório durável `dev-journey/07-reports/AUDIT_2026_07_12.md` §3 (briefing efêmero da sessão de auditoria)
- Caminho nativo (referência dos gates): `nyx/agent/loop/_iteration.py:383-524` (`_execute_tool_calls`)
- Caminho fallback (alvo): `nyx/agent/loop/_iteration.py:528-668` (`_execute_parsed_action`)
- Callbacks async da TUI: `nyx/agent/tui/app.py:266,913,919`; plan mode: `nyx/agent/tools/plan_mode.py:17`; permissões: `nyx/agent/permissions.py:74,111,122`
- Estrutura de spec: `dev-journey/06-sprints/producao/SPRINT_EXEC_CONTRACT_PROXY_STATUS_BEFORE_JSON_01.md`

---

*"Uma garantia de segurança que só vale no caminho que o bom modelo usa, e falha no caminho que o pior modelo prefere, engana justamente o usuário que mais precisa dela. Robustez pertence à infra, e a infra tem dois caminhos -- ambos precisam do mesmo portão."*
