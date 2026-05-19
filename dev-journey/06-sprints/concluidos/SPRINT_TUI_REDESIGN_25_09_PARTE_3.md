# SPRINT TUI-REDESIGN-25-09-PARTE-3 — Captura real do thinking via proxy + loop

## 0. SPEC

```yaml
sprint:
  id: TUI-REDESIGN-25-09-PARTE-3
  title: "proxy preserva field thinking no response; loop/_iteration extrai e propaga"
  onda: 25
  bloco: 25.meta (parte 3 de TUI-REDESIGN-25-09)
  prioridade: BAIXA
  tipo: Feature
  dependencias: [TUI-REDESIGN-25-09-PARTE-2]
  desbloqueia: []
  origem: "PARTE-2 implementou Tab keybinding + helper visual. Captura real do thinking exige que proxy preserve o field e que loop o extraia. Hoje proxy.py:296 ativamente apaga o reasoning."

  touches:
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/proxy.py
      reason: "Preservar field 'thinking' (qwen3) no message do response; antes era apagado"
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/agent/loop/_iteration.py
      reason: "Detectar response.message.thinking e propagar via callback on_thinking"
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/cli.py
      reason: "Registrar callback on_thinking que seta app_state['last_thinking_block']"

  forbidden:
    - "Forçar thinking em modelo que não suporta (qwen2.5-coder não emite think)"
    - "Quebrar tool_calls (proxy linha 296 limpa content; mudar com cuidado)"

  tests:
    - cmd: "bash scripts/sprint_invariants.sh"
      timeout: 60
      deve_passar: "14/14"

  acceptance_criteria:
    - "qwen3:4b emite thinking; proxy preserva; loop extrai; app_state setado"
    - "qwen2.5-coder: surrogate (texto entre tool calls) capturado"
    - "Tab no REPL com prompt vazio mostra thinking real (não placeholder)"
    - "Smoke ok + invariantes 14/14"

  status: DEFERIDA (BAIXA prioridade)
  motivo_deferida: "Helper UI e Tab keybinding já funcionam (PARTE-2). Captura real é nice-to-have; exige mudança no proxy.py que limpa content em tool_calls (linha 296) e teste com qwen3:4b (não é o default qwen2.5-coder:3b)."
```

---

# Sprint TUI-REDESIGN-25-09-PARTE-3

**Status:** DEFERIDA
**Data criação:** 2026-05-18 (decomposta de M3 PARTE-2 durante Onda 26)
**Modelo obrigatório:** claude-opus-4-7

## Rollback

`git reset --hard HEAD~1`
