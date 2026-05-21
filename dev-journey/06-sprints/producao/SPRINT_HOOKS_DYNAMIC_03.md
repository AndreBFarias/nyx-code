## 0. SPEC (machine-readable)

```yaml
sprint:
  id: HOOKS-DYNAMIC-03
  title: "HOOKS integração no ciclo de execução do agente (fecha HOOKS-DYNAMIC-02 CONCLUIDA_PARCIAL)"
  onda: 23
  bloco: "23.5 Feature parity"
  prioridade: MÉDIA
  tipo: Feature
  dependencias: [HOOKS-DYNAMIC-02]
  desbloqueia: []

  touches:
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/agent/loop/_core.py
      reason: "Amarrar HookRuntime no AgentLoop: instanciar self._hooks em __init__, chamar UserPromptSubmit no run(), Stop ao final"
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/agent/loop/_iteration.py
      reason: "Chamar PreToolUse/PostToolUse antes/depois de cada tool execution; respeitar block_on_failure"
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/scripts/gauntlet/nyx_gauntlet.py
      reason: "Adicionar HD-03 (ciclo end-to-end com hook real) na fase hooks_dynamic existente"

  creates: []
  removes: []

  forbidden:
    - "Quebrar fluxo do AgentLoop quando ~/.nyx/settings.json ausente"
    - "Bypassar block_on_failure (se hook falhar com flag, deve bloquear)"
    - "Adicionar dependência nova"
    - "Emoji ou menção a IA externa"
    - "Tocar HookRuntime em si (já estável)"

  tests:
    - cmd: "./run.sh --smoke"
      timeout: 10
      deve_passar: true
    - cmd: "bash scripts/sprint_invariants.sh"
      timeout: 30
      deve_passar: true
      assert: "PASS=14 FAIL=0"
    - cmd: "./run.sh --gauntlet --only hooks_dynamic"
      timeout: 60
      deve_passar: true
      assert: "100% incluindo HD-03"

  acceptance_criteria:
    - "AgentLoop.__init__ instancia HookRuntime (tolerante: settings.json ausente OK)"
    - "AgentLoop.run() chama hook UserPromptSubmit antes da primeira iteração"
    - "_execute_tool_calls chama PreToolUse antes; PostToolUse após (com result)"
    - "Stop hook chamado ao final do turn (independente de sucesso)"
    - "block_on_failure=true: hook fail interrompe execução; warning no log"
    - "Boot sem settings.json: zero hooks, fluxo normal"
    - "Gauntlet --only hooks_dynamic 100% APROVADO incluindo HD-03"
    - "Smoke + invariantes 14/14 + acentuação rc=0"
    - "MASTER linha 130 (HOOKS-DYNAMIC-02) ganha nota fechamento; nova linha HOOKS-DYNAMIC-03 CONCLUIDA"
```

---

# Sprint HOOKS-DYNAMIC-03 — Integração no ciclo do AgentLoop

**Status:** PENDENTE
**Data criação:** 2026-05-21
**Modelo obrigatório:** claude-opus-4-7

---

## Contexto

HOOKS-DYNAMIC-02 deixou integração no AgentLoop pendente. HookRuntime existe e funciona (lê ~/.nyx/settings.json, executa hooks com timeout + block_on_failure), mas não é chamado pelo loop. Esta sprint amarra os 4 eventos:

- **UserPromptSubmit**: chamado em `AgentLoop.run()` ao receber input do usuário
- **PreToolUse**: chamado em `_execute_tool_calls` antes de cada tool execution
- **PostToolUse**: chamado após tool execution (com result)
- **Stop**: chamado no final do turn (após DONE ou MAX_ITERATIONS)

## Solução

Em `nyx/agent/loop/_core.py` (AgentLoop):
```python
def __init__(self, ...):
    ...
    # HOOKS-DYNAMIC-03: instanciar HookRuntime tolerante
    try:
        from nyx.agent.services.hook_runtime import HookRuntime
        self._hooks = HookRuntime()
    except Exception as e:
        logger.warning(f"HookRuntime falhou: {e}; sem hooks dinâmicos")
        self._hooks = None

async def run(self, user_input: str) -> SessionStatus:
    if self._hooks:
        await self._hooks.run("UserPromptSubmit", {"content": user_input})
    try:
        # ... loop existente
    finally:
        if self._hooks:
            await self._hooks.run("Stop", {"turn_summary": ...})
```

Em `nyx/agent/loop/_iteration.py` `_execute_tool_calls`:
```python
async def _execute_tool_calls(self, ...):
    for tool_call in tool_calls:
        if self._hooks:
            blocked = await self._hooks.run(
                "PreToolUse",
                {"tool_name": tool_call.name, "tool_input": tool_call.args},
            )
            if blocked:
                continue  # hook com block_on_failure bloqueou
        result = await self._execute_tool(tool_call)
        if self._hooks:
            await self._hooks.run(
                "PostToolUse",
                {"tool_name": tool_call.name, "tool_result": result.output},
            )
```

## Proof-of-work

```bash
bash scripts/sprint_invariants.sh > /tmp/inv_before_hd.txt 2>&1

# IMPLEMENTAR

./run.sh --smoke
bash scripts/sprint_invariants.sh > /tmp/inv_after_hd.txt 2>&1

# Teste de integração: cria settings.json temporário com hook simples
# e roda gauntlet HD-03

./run.sh --gauntlet --only hooks_dynamic 2>&1 | tail -10

python3 ~/.config/zsh/scripts/validar-acentuacao.py --paths nyx/agent/loop/_core.py nyx/agent/loop/_iteration.py scripts/gauntlet/nyx_gauntlet.py
```

## Critério binário

- [ ] AgentLoop.__init__ instancia HookRuntime tolerante
- [ ] run() chama UserPromptSubmit
- [ ] _execute_tool_calls chama PreToolUse + PostToolUse
- [ ] Stop chamado no finally do run()
- [ ] block_on_failure respeitado (hook fail interrompe se flag true)
- [ ] Boot sem settings.json é tolerante
- [ ] Gauntlet hooks_dynamic 100% (HD-01, HD-02 preservadas + HD-03 nova)
- [ ] MASTER linha 130 (HOOKS-DYNAMIC-02) + nova linha HOOKS-DYNAMIC-03 CONCLUIDA
- [ ] Spec movida producao/ → concluidos/

---

*"Hooks são pontos de extensão, não pontos de quebra."*
