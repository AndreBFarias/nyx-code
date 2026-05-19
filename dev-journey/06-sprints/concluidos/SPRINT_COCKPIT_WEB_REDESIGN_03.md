# SPRINT COCKPIT-WEB-REDESIGN-03 — Guide Playwright + control API documentado

## 0. SPEC

```yaml
sprint:
  id: COCKPIT-WEB-REDESIGN-03
  title: "Documenta workflow Claude valida TUI via Playwright (browser_navigate + browser_take_screenshot + POST /control/repl/send)"
  onda: 26
  bloco: 26.2 Cockpit --web reformulado
  prioridade: MÉDIA
  tipo: Documentação
  dependencias: [COCKPIT-WEB-REDESIGN-02]
  desbloqueia: [TUI-REDESIGN-26-01..04 (validação visual via guide)]
  origem: "Workflow novo (--web vira terminal real) precisa de doc para Claude saber como validar visualmente as próximas sprints."

  touches:
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/dev-journey/05-guides/COCKPIT_WEB_GUIDE.md
      reason: "Novo arquivo: guia step-by-step com curl + Playwright examples"

  forbidden:
    - "Mencionar IA externa (ADR-005)"
    - "Hardcode portas (citar via config/defaults.py)"

  tests:
    - cmd: "test -f dev-journey/05-guides/COCKPIT_WEB_GUIDE.md && wc -l dev-journey/05-guides/COCKPIT_WEB_GUIDE.md"
      timeout: 5
      deve_passar: "arquivo existe, > 50 linhas"
    - cmd: "bash scripts/sprint_invariants.sh"
      timeout: 60
      deve_passar: "14/14"

  acceptance_criteria:
    - "Guide com seções: Iniciar, Navegar, Interagir, Validar, Encerrar"
    - "Exemplos curl funcionais para /control/repl/send"
    - "Smoke test final que valida endpoint"
    - "Smoke ok + invariantes 14/14"
```

---

# Sprint COCKPIT-WEB-REDESIGN-03

**Status:** CONCLUIDA
**Data criação:** 2026-05-18
**Data conclusão:** 2026-05-18 (sincronizado em SPRINT_ORDER-REFRESH-01 2026-05-19)
**Modelo obrigatório:** claude-opus-4-7

## Critério binário

- [ ] COCKPIT_WEB_GUIDE.md criado
- [ ] 5 seções cobertas
- [ ] Exemplos curl validados
- [ ] Smoke + invariantes 14/14

## Rollback

`git reset --hard HEAD~1`
