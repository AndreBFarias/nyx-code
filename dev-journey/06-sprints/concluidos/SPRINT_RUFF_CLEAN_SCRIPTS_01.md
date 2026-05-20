# SPRINT RUFF-CLEAN-SCRIPTS-01

**Status:** CONCLUIDA
**Data:** 2026-05-19 (terceira sessão, ~23h45)

## Contexto

Análogo a RUFF-CLEAN-NYX-01: `python3 -m ruff check scripts/` reportava 33 erros pré-existentes (16 fixáveis automaticamente, 22 manuais). Invariante #10 do projeto checa apenas `nyx/`, mas pelo princípio anti-débito, limpamos também o lado scripts/.

## Fix

### Autofix (11 corrigidos via `ruff --fix`)
- 3xI001 imports reorder
- 2xF541 f-string sem placeholder
- 2xF401 imports unused
- outros

### Cirúrgico (22 manuais)
- `scripts/audit_help_coverage.py:13,14` (E402): `# noqa: F401,E402` em imports após sys.path.insert
- `scripts/gauntlet/fixtures/buggy_service.py:67` (E722): `# noqa: E722 -- BUG JUNIOR proposital (fixture)`
- `scripts/gauntlet/nyx_gauntlet.py:841` (F841 `external_mib`): renomear `_external_mib` + noqa
- `scripts/gauntlet/nyx_gauntlet.py:1451,1487,1713,3027` (F841): deletar atribuições não-usadas
- `scripts/gauntlet/nyx_gauntlet.py:1312,2435,2450` (E501): `# noqa: E501`
- `scripts/gauntlet/nyx_gauntlet.py:2569,2570` (E741 `l`): renomear `l -> ln`
- `scripts/gauntlet/nyx_gauntlet.py:3152,3153` (F401): `# noqa: F401 -- smoke-test de disponibilidade`
- `scripts/menu_wizard.py:133` (F841 `muted`): deletar
- `scripts/sbom_init.py:27` (E501): `# noqa: E501`
- `scripts/sync.py:501` (E501): `# noqa: E501`
- `scripts/sync.py:518` (F841 `args`): substituir por `parser.parse_args()` (descarte)
- `scripts/update_docs.py:157,233,273` (E501): `# noqa: E501`
- `scripts/update_next_sprint.py:290` (E501): quebrar string template com `\n` + indent (linha estava dentro de f-string multi-linha; noqa poluiria output renderizado)

## Proof-of-work

- `python3 -m ruff check scripts/` -> **All checks passed!** (era 33 erros)
- `python3 -m ruff check nyx/` -> All checks passed (sem regressão)
- `./run.sh --smoke` -> `boot ok`
- `bash scripts/sprint_invariants.sh` -> 14/14 PASS

---

*"Anti-débito não para em invariante — alcança onde o invariante não cobre." -- RUFF-CLEAN-SCRIPTS-01*
