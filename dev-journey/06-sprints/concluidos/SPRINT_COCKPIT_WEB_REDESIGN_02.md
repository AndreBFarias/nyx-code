# SPRINT COCKPIT-WEB-REDESIGN-02 — Auto-start REPL Nyx ao conectar WS /repl

## 0. SPEC

```yaml
sprint:
  id: COCKPIT-WEB-REDESIGN-02
  title: "WS /repl spawna ./venv/bin/python nyx/cli.py (não ./run.sh) reusando Ollama/proxy do cockpit"
  onda: 26
  bloco: 26.2 Cockpit --web reformulado
  prioridade: ALTA
  tipo: Refactor
  dependencias: [COCKPIT-WEB-REDESIGN-01]
  desbloqueia: [COCKPIT-WEB-REDESIGN-03]
  origem: "Hoje WS /repl spawna ./run.sh completo (Ollama + proxy + cli), mas se cockpit já gerencia esses processos, há duplicação. REPL puro reusa o stack já bootado."

  touches:
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/cockpit/server.py
      reason: "WS /repl detecta se Ollama/proxy já estão UP (curl health). Se sim, spawna ./venv/bin/python nyx/cli.py. Se não, fallback para ./run.sh (mantém compat)."
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/cockpit/pty_bridge.py
      reason: "Aceita command list configurável (sem hardcode RUN_SH)"

  forbidden:
    - "Duplicar Ollama: nunca spawnar ./run.sh quando proxy já responde em :11436"
    - "Hardcode de portas (usar config/defaults.py)"

  tests:
    - cmd: "bash scripts/sprint_invariants.sh"
      timeout: 60
      deve_passar: "14/14"
    - cmd: "curl -sf http://127.0.0.1:11436/v1/models > /dev/null && echo PROXY_UP || echo PROXY_DOWN"
      timeout: 5
      deve_passar: "PROXY_UP (com cockpit já rodando full)"

  acceptance_criteria:
    - "Detector: se proxy responde em :11436, spawna REPL puro"
    - "Fallback: senão, spawna ./run.sh completo (compat com browser standalone)"
    - "Env vars passadas: NYX_SCHEMA, NYX_AESTHETIC, NYX_ENTITY, NYX_USER_DISPLAY_NAME"
    - "Sem duplicação de Ollama/proxy"
    - "Smoke ok + invariantes 14/14"
```

---

# Sprint COCKPIT-WEB-REDESIGN-02

**Status:** CONCLUIDA
**Data criação:** 2026-05-18
**Data conclusão:** 2026-05-18 (sincronizado em SPRINT_ORDER-REFRESH-01 2026-05-19)
**Modelo obrigatório:** claude-opus-4-7

## Critério binário

- [ ] Detector de proxy/ollama funcional
- [ ] REPL puro spawnado quando stack já UP
- [ ] Env vars propagadas
- [ ] Smoke + invariantes 14/14

## Anti-débito

- Persistência de sessão entre conexões WS fica fora (cada nova conexão = nova sessão).

## Rollback

`git reset --hard HEAD~1`
