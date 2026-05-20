# SPRINT GAUNTLET-IF-05-PLAN-REGRESS-01

**Status:** CONCLUIDA
**Data:** 2026-05-19 (terceira sessão, ~23h28)

## Contexto

Gauntlet 21:48 IF-05 OK com output `"Crie um plano de implementação para: feature X"` (contendo `"list_files"` em texto longo do template). Gauntlet 22:53 IF-05 FAIL com novo output `"Objetivo do plano definido: feature X"` — CTX-04 (commit 669f217) transformou `/plan` de "gerador de template de prompt" para "checklist persistida opt-in". Teste IF-05 ficou desatualizado.

## Fix

`scripts/gauntlet/nyx_gauntlet.py:1729-1737`: aceitar nova semântica do `/plan`:

```python
has_plan_marker = (
    "feature X" in plan_out
    or "Objetivo" in plan_out
    or "plano" in plan_out.lower()
    or "list_files" in plan_out
)
```

Mantém retro-compat com formato antigo (`list_files`) caso `/plan` volte para template.

## Proof-of-work

- `./run.sh --gauntlet --only interface` -> **5/5 (100%) APROVADO** (era 4/5 com IF-05 FAIL)
- IF-05 OK com `details="  Objetivo do plano definido: feature X"`
- smoke + invariantes 14/14 PASS

---

*"Quando o comportamento muda, teste acompanha — não o contrário." -- GAUNTLET-IF-05-PLAN-REGRESS-01*
