# SPRINT REGISTRY-SUDO-IMPORT-01 -- ADR-013 zero-exceção

**Status:** CONCLUIDA
**Data:** 2026-05-19 (terceira sessão, ~23h24)

## Contexto

Gauntlet COV-01 FAIL "1 sem import: ['sudo_session']" — `nyx/agent/tools/sudo_session.py` é singleton module-level (state global de senha cacheada do SUDO-MODE-01) e não tinha import explícito em `registry.py`. ADR-013 (Integração obrigatória) declara invariante absoluto: TODO arquivo em `nyx/agent/tools/` deve estar importado pelo registry — não há cláusula de exceção para singletons.

## Fix

`nyx/agent/tools/registry.py` ganha import explícito de symbol exportado:

```python
from .sudo_session import status as _sudo_session_status  # noqa: F401 -- ADR-013: singleton module-level state (SUDO-MODE-01); sem classe Tool, mantém arquivo carregado conforme integração obrigatória
```

`status` é função do `sudo_session.py:198`. O symbol é referenciado apenas para forçar carregamento do módulo (state global init). `noqa: F401` documenta a intenção (imported but unused é proposital).

Auto-format do ruff reorganizou para multi-line `from .sudo_session import (status as _sudo_session_status,)` — equivalente.

## Proof-of-work

- `./run.sh --smoke` -> `boot ok`
- `bash scripts/sprint_invariants.sh` -> 14/14 PASS
- `python3 -m ruff check nyx/` -> All checks passed!
- `./run.sh --gauntlet --only coverage` -> **6/6 (100%) APROVADO** (era 5/6)
- COV-01 OK: `29 arquivos, 0 sem import`

## Filosofia

ADR-013 é absoluto: zero código solto. Singleton não é exceção — apenas style diferente. Forçar import explícito mantém invariante.

## Referências

- ADR-013 (Integração obrigatória)
- SUDO-MODE-01 (sprint que criou sudo_session.py singleton)
- COV-01 test em `scripts/gauntlet/nyx_gauntlet.py:3657-3689`

---

*"Integração obrigatória é absoluta — singleton ou não, todo .py em tools/ entra no registry." -- REGISTRY-SUDO-IMPORT-01*
