## 0. SPEC (machine-readable)

```yaml
sprint:
  id: D-01
  title: "CI GitHub Actions -- lint, smoke tests, validação de anonimato"
  touches:
    - path: .github/workflows/ci.yml
      reason: "Workflow principal de CI"
    - path: .github/actions/setup-nyx/action.yml
      reason: "Action reutilizável de setup"
  tests:
    - cmd: "bash -n run.sh && bash -n install.sh && bash -n uninstall.sh"
      timeout: 10
    - cmd: "python -c 'from nyx.themes import ThemeManager; print(len(ThemeManager().list_themes()))'"
      timeout: 10
  acceptance_criteria:
    - "CI roda em PR para main"
    - "Lint verifica sintaxe shell e imports Python"
    - "Smoke tests validam temas, config, utils"
    - "Check de anonimato bloqueia menções a IA"
    - "Check de referências legadas bloqueia resíduos"
```

---

# Sprint D-01 -- CI GitHub Actions

**Status:** PENDENTE
**Data:** 2026-04-04
**Prioridade:** MÉDIA
**Tipo:** Infra/DevOps
**Dependências:** G-01
**Desbloqueia:** --

---

## Contexto

Replicar a infraestrutura de CI da Luna (ci.yml + quality-gates.yml)
adaptada para o Nyx-Code. Sem GPU no CI, o Gauntlet não roda --
mas lint, smoke tests e validações estruturais sim.

## Implementação

1. `.github/workflows/ci.yml` -- já criado, precisa de ajustes finais
2. `.github/actions/setup-nyx/action.yml` -- action reutilizável
3. Smoke tests Python inline (sem pytest por enquanto)

## Verificação

- [ ] CI roda sem erros em PR
- [ ] Lint shell passa
- [ ] Smoke tests temas/config passam
- [ ] Check anonimato detecta violações

---

*"Automatize o que pode ser automatizado." -- Bill Gates*
