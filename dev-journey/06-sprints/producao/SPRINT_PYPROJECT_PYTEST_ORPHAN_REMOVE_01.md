# SPRINT 259 — PYPROJECT-PYTEST-ORPHAN-REMOVE-01

## 0. SPEC

```yaml
sprint:
  id: PYPROJECT-PYTEST-ORPHAN-REMOVE-01
  title: "Remover [tool.pytest.ini_options] orfao do pyproject.toml (ADR-014 proibe pytest, sem tests/)"
  onda: 31
  prioridade: BAIXA
  tipo: Hygiene
  dependencias: []
  desbloqueia: []

  touches:
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/pyproject.toml
      reason: "Linhas 65-69 declaram [tool.pytest.ini_options] (testpaths=['tests']), mas ADR-014 proibe pytest/unittest (testes so via Gauntlet) e nao existe diretorio tests/. Config morta que contradiz o ADR."
  creates: []
  removes: []

  forbidden:
    - "Remover [tool.ruff] ou [build-system] ou qualquer config viva"
    - "Adicionar dependencia pytest"
    - "Adicionar emoji ou mencao a IA externa"

  tests:
    - cmd: "./run.sh --smoke"
      timeout: 10
      deve_passar: true
    - cmd: "python3 -c \"import tomllib; tomllib.load(open('pyproject.toml','rb'))\""
      timeout: 10
      deve_passar: true

  acceptance_criteria:
    - "[tool.pytest.ini_options] removido do pyproject.toml"
    - "pyproject.toml continua TOML valido (parse OK)"
    - "Build/version dinamica continua funcionando (nyx.__version__)"
    - "Smoke boot ok"
```

---

# Sprint 259 — PYPROJECT-PYTEST-ORPHAN-REMOVE-01

**Status:** PENDENTE
**Data criacao:** 2026-05-25

## Contexto

Auditoria de 2026-05-25: `pyproject.toml` (linhas 65-69) tem:

```toml
[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = "test_*.py"
python_functions = "test_*"
addopts = "-v --tb=short"
```

Mas o ADR-014 ("Testes via Gauntlet, sem pytest/unittest") proibe pytest, e nao
existe diretorio `tests/` no repo (`ls tests/` -> ausente). Config morta e
contraditoria com o ADR canonico. Pequena divida de coerencia.

## Solucao

Remover o bloco `[tool.pytest.ini_options]`. Verificar que o TOML continua
valido e que a versao dinamica (`[tool.setuptools.dynamic] version = attr
nyx.__version__.__version__`) segue resolvendo.

## Acceptance

- [ ] Bloco pytest removido.
- [ ] TOML valido (tomllib parse).
- [ ] Smoke ok.

## Proof-of-work

```
grep -c "tool.pytest" pyproject.toml   # ANTES: 1 ; DEPOIS: 0
python3 -c "import tomllib; print('TOML OK' if tomllib.load(open('pyproject.toml','rb')) else 'FAIL')"
./run.sh --smoke   # boot ok
```
