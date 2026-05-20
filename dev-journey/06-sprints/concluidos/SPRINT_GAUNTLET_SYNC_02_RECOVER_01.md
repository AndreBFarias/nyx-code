# SPRINT GAUNTLET-SYNC-02-RECOVER-01

**Status:** CONCLUIDA
**Data:** 2026-05-19 (terceira sessão, ~23h28)

## Contexto

Gauntlet SYNC-02 FAIL com `details=""` (vazio). Verificava `"tools registradas" in r.stdout.lower() or "Todas" in r.stdout`. Output real de `scripts/sync.py` contém `"Todos 29 arquivos de tool importados em registry.py"` — **masculino** (refere-se a "arquivos"), não "Todas" (feminino) nem "tools registradas".

## Fix

`scripts/gauntlet/nyx_gauntlet.py:3619-3621`: aceitar 3 formas observadas:

```python
ok = (
    "tools registradas" in stdout_lower
    or "arquivos de tool importados" in stdout_lower
    or "Todas" in r.stdout
    or "Todos" in r.stdout
)
```

## Proof-of-work

- `./run.sh --gauntlet --only infra_sync` -> **5/5 (100%) APROVADO** (era 4/5 com SYNC-02 FAIL)
- SYNC-02 OK
- smoke + invariantes 14/14 PASS

---

*"Strings literais quebram quando microcopy muda; gauntlet aceita os formatos reais." -- GAUNTLET-SYNC-02-RECOVER-01*
