# SPRINT COCKPIT-WEB-REDESIGN-01 — Rota / vira terminal Nyx live (dashboard migra para /dashboard)

## 0. SPEC

```yaml
sprint:
  id: COCKPIT-WEB-REDESIGN-01
  title: "GET / serve terminal.html (TUI Nyx no browser); dashboard de gauntlet vira GET /dashboard"
  onda: 26
  bloco: 26.2 Cockpit --web reformulado
  prioridade: ALTA
  tipo: UX+Refactor
  dependencias: [SPRINT_ORDER-OVERRIDE-FIX-01]
  desbloqueia: [COCKPIT-WEB-REDESIGN-02, COCKPIT-WEB-REDESIGN-03, TUI-REDESIGN-26-01..04]
  origem: "Pedido do usuário 2026-05-18: --web devia abrir o TUI no browser para Claude validar/interagir via Playwright; hoje abre dashboard de gauntlet (não é o terminal)."

  touches:
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/cockpit/server.py
      reason: "Trocar handler GET / para servir terminal.html; novo GET /dashboard servindo index.html"
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/cockpit/static/index.html
      reason: "Header link 'terminal' aponta / em vez de /static/terminal.html"
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/cockpit/static/terminal.html
      reason: "Header ganha link 'dashboard' apontando /dashboard; brand-sub vira 'terminal' (default landing)"

  forbidden:
    - "Remover endpoints /api/* ou /control/*"
    - "Quebrar /static/{path} (servir assets continua igual)"
    - "Mudar bind 127.0.0.1 (ADR-001 Local First)"

  tests:
    - cmd: "curl -s http://127.0.0.1:11437/ | grep -o '<title>.*</title>'"
      timeout: 5
      deve_passar: "<title>Nyx Cockpit -- REPL</title>"
    - cmd: "curl -s http://127.0.0.1:11437/dashboard | grep -o '<title>.*</title>'"
      timeout: 5
      deve_passar: "<title>Nyx Cockpit -- Dashboard</title>"
    - cmd: "bash scripts/sprint_invariants.sh"
      timeout: 60
      deve_passar: "14/14"

  acceptance_criteria:
    - "GET / serve terminal.html (HTML do REPL embedded)"
    - "GET /dashboard serve index.html (dashboard de gauntlet)"
    - "terminal.html header tem link 'dashboard' funcional"
    - "index.html header link 'terminal' aponta / (não /static/terminal.html)"
    - "Smoke ok + invariantes 14/14"
    - "Playwright navega para / e renderiza xterm (validação visual)"
```

---

# Sprint COCKPIT-WEB-REDESIGN-01

**Status:** CONCLUIDA
**Data criação:** 2026-05-18
**Data conclusão:** 2026-05-18
**Modelo obrigatório:** claude-opus-4-7

## Contexto

Pedido explícito do usuário: `--web` devia abrir o TUI da Nyx no browser, não o dashboard de gauntlet. A intenção é permitir que (a) usuário interaja com a Nyx via browser, (b) Claude via Playwright valide visualmente cada sprint da Onda 26.

## Critério binário

- [ ] / serve terminal.html
- [ ] /dashboard serve index.html
- [ ] Links de navegação atualizados
- [ ] Smoke + invariantes 14/14
- [ ] Commit `feat(COCKPIT-WEB-REDESIGN-01): rota / vira terminal Nyx live`

## Invariantes

#2, #14.

## Anti-débito

- Auto-start REPL ao conectar WS fica para COCKPIT-WEB-REDESIGN-02.
- Guide com exemplos Playwright fica para COCKPIT-WEB-REDESIGN-03.

## Rollback

`git reset --hard HEAD~1`
