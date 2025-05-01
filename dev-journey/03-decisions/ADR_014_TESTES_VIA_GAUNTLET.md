# ADR-014: Testes exclusivamente via Gauntlet

**Data:** 2026-04-05
**Status:** Aceita
**Contexto:** Estratégia de testes do projeto

---

## Decisão

Todos os testes do Nyx-Code rodam exclusivamente dentro do Gauntlet (`scripts/gauntlet/nyx_gauntlet.py`). Nenhum framework de testes externo (pytest, unittest) é usado.

## Motivo

1. **Um único mecanismo** -- simplifica CI, validação e onboarding
2. **Zero mocks** (ADR-010) -- Gauntlet testa contra infraestrutura real
3. **Verificação de conteúdo** (ADR-011) -- testes validam output, não só success
4. **Fases isoladas** -- cada sprint tem sua fase no Gauntlet
5. **Report automático** -- `GAUNTLET_REPORT.md` gerado a cada execução

## Regras

1. Nenhum `test_*.py`, `*_test.py`, `conftest.py` no projeto
2. Nenhum `import pytest` ou `import unittest` no código
3. Cada feature nova adiciona teste(s) na fase correspondente do Gauntlet
4. Fase nova = método `_phase_nome()` na classe `NyxGauntlet`
5. Cada teste usa `self._add(id, nome, fase, passed, elapsed, ...)`

## Execução

```bash
./run.sh --gauntlet                      # Completo
./run.sh --gauntlet --only <fase>        # Fase específica
./run.sh --gauntlet --only rapido        # Infra+proxy+visual+config
```

## Validação

- `find . -name "test_*.py" -not -path "*/venv/*"` retorna vazio
- `grep -r "import pytest" nyx/` retorna vazio
- Gauntlet é o único arquivo com assertivas de teste

---

*"A simplicidade é o último grau de sofisticação." -- Leonardo da Vinci*
