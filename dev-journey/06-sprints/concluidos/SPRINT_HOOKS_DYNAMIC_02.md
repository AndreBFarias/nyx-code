# SPRINT HOOKS-DYNAMIC-02 — Integração no ToolRegistry + loop + skill bridge (anti-débito)

## 0. SPEC

```yaml
sprint:
  id: HOOKS-DYNAMIC-02
  title: "Amarrar HookRuntime no ToolRegistry (Pre/PostToolUse) + loop (UserPromptSubmit/Stop) + bridge real para skill:<name>"
  onda: 23
  bloco: 23.5 Feature parity
  prioridade: MÉDIA
  tipo: Feature
  dependencias: [HOOKS-DYNAMIC-01]
  desbloqueia: []
  origem: "Anti-débito de HOOKS-DYNAMIC-01 — MVP entregue (HookRuntime + load + run + HOOKS.md) sem integração no ciclo do agente."

  touches:
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/agent/tools/registry.py
      reason: "Tool.execute invoca HookRuntime.run('PreToolUse', ...) antes e 'PostToolUse' depois; bloqueia se PreToolUse blocked=True"
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/agent/loop/_core.py
      reason: "add_user dispara 'UserPromptSubmit'; fim de turn dispara 'Stop'"
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/agent/services/hook_runtime.py
      reason: "skill:<name> realmente invoca a Skill tool via Skill API; placeholder MVP virá real"
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/scripts/gauntlet/nyx_gauntlet.py
      reason: "Fase 'hooks' com hook PreToolUse de exemplo que veta uma tool"

  forbidden:
    - "Hook PreToolUse roda DEPOIS de iniciar a tool (deve abortar antes)"
    - "Hook que demora mais que o timeout afeta loop principal (deve ser fire-and-forget pra Stop)"

  acceptance_criteria:
    - "PreToolUse com block_on_failure=True veta tool (não executa)"
    - "PostToolUse recebe tool_result e pode injetar mensagem no contexto"
    - "UserPromptSubmit pode rejeitar input (retorna __error__)"
    - "Stop dispara após shutdown gracioso (não bloqueia)"
    - "skill:<name> realmente invoca Skill tool"
    - "Fase Gauntlet 'hooks' com 3 testes"
    - "Smoke + invariantes passam"

  tests:
    - cmd: "./run.sh --gauntlet --only hooks"
      timeout: 120
      deve_passar: true
```

---

**Status:** CONCLUIDA (header corrigido em MASTER-CLEANUP-02 2026-05-20; presença em concluidos/ implica CONCLUIDA conforme convenção do projeto)
**Data criação:** 2026-05-17
**Origem:** anti-débito de HOOKS-DYNAMIC-01.
**Modelo obrigatório:** claude-opus-4-7 (sem subagentes)
