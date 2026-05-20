# SPRINT GAUNTLET-LOOP-PY-REF-FIX-01 -- F2-03/F2-06 procuram loop.py inexistente (refactor para pacote)

## 0. SPEC

```yaml
sprint:
  id: GAUNTLET-LOOP-PY-REF-FIX-01
  title: "F2-03 e F2-06 esperam loop.py mas loop virou pacote nyx/agent/loop/"
  onda: 25
  bloco: 25.0 Release (anti-débito derivado de GAUNTLET-FIXTURES-SANDBOX-01)
  prioridade: ALTA
  tipo: Fix de teste (sem mudança em produção)
  dependencias: [GAUNTLET-FIXTURES-SANDBOX-01]
  desbloqueia: [v1.0 (gate gauntlet 100% — encerra 2 das 13 falhas residuais)]

  touches:
    - path: scripts/gauntlet/nyx_gauntlet.py
      reason: "Substituir asserção `'loop.py' in r.output` por arquivo realmente existente em nyx/agent/ após refactor loop.py -> loop/"
      blocos:
        - "linhas 2322-2325: F2-03 (Glob encontra arquivo real)"
        - "linhas 2337-2340: F2-06 (ListFiles diretório real)"

  creates: []
  removes: []

  forbidden:
    - "Recriar arquivo nyx/agent/loop.py (refactor para pacote loop/ foi intencional)"
    - "Modificar nyx/agent/loop/* (produção intocada)"
    - "Mexer em linha 3401 (repo_map fixture do teste CTX-09 é string literal intencional, não toca filesystem)"
    - "Mexer em F2-01/F2-02/F2-04/F2-05/F2-07/F2-08 (já passam)"

  tests:
    - cmd: "./run.sh --smoke"
      timeout: 60
      deve_passar: "boot ok"
    - cmd: "bash scripts/sprint_invariants.sh"
      timeout: 60
      deve_passar: "PASS 14, FAIL 0"
    - cmd: "./run.sh --gauntlet --only e2e_real"
      timeout: 120
      deve_passar: "APROVADO (8/8)"
    - cmd: "./run.sh --gauntlet --only rapido"
      timeout: 120
      deve_passar: "sem regressão vs baseline (P-07 permanece FAIL pré-existente, demais OK)"
    - cmd: "grep -nE \"'loop\\.py' in r\\.output\" scripts/gauntlet/nyx_gauntlet.py"
      timeout: 5
      deve_passar: "vazio (zero referências hardcoded a loop.py em asserções de existência de arquivo)"

  acceptance_criteria:
    - "F2-03 passa: glob('nyx/agent/*.py') verifica arquivo realmente existente (ex.: parser.py)"
    - "F2-06 passa: list_files('nyx/agent') verifica arquivo realmente existente (ex.: parser.py)"
    - "Mensagem de details() atualizada para refletir novo alvo (sem 'has_loop')"
    - "Linha 3401 (CTX-09 repo_map fixture) NÃO tocada — string interna do teste de prompt"
    - "Gauntlet --only rapido sem regressão"
    - "Smoke + invariantes 14/14"
    - "Sprint movida producao/ -> concluidos/"
```

---

**Status:** CONCLUIDA
**Data spec:** 2026-05-19
**Data conclusão:** 2026-05-19 (segunda sessão, ~22h20)
**Modelo execução:** claude-opus-4-7

---

## Proof-of-work executado (2026-05-19)

**Edit aplicado:**
- `scripts/gauntlet/nyx_gauntlet.py:2426-2427` (F2-03): `"loop.py"` -> `"parser.py"`, `has_loop` -> `has_parser`
- `scripts/gauntlet/nyx_gauntlet.py:2441-2442` (F2-06): idem
- Total: 4 linhas em 2 blocos (linhas alvo driftaram de 2322-2340 para 2426-2442 devido a K08-VRAM-RUNNER-ISOLATION-01 ter inserido +176L antes — drift irrelevante para o fix, identifiers literais preservados)

**Verificação binária:**
- `grep -cE "'loop\.py' in r\.output|\"loop\.py\" in r\.output" scripts/gauntlet/nyx_gauntlet.py` = **0** (era 4)
- `grep -cE "'parser\.py' in r\.output|\"parser\.py\" in r\.output" scripts/gauntlet/nyx_gauntlet.py` = **4**
- Linha 3401 (`repo_map` CTX-09 fixture) **NÃO** tocada

**Runtime:**
- `./run.sh --smoke` -> `boot ok` antes e depois
- `bash scripts/sprint_invariants.sh` -> PASS 14 / FAIL 0 antes e depois
- `./run.sh --gauntlet --only e2e_real` -> **8/8 (100%) APROVADO** (relatório `dev-journey/07-reports/gauntlet/GAUNTLET_2026-05-19_2217.md`). F2-03 OK `has_parser=True`, F2-06 OK `has_parser=True`.
- `./run.sh --gauntlet --only rapido` -> 17/18 (94%); único FAIL = **P-07 pré-existente** (out-of-scope explícito da spec linha 181). **Zero regressão.**

**Achado colateral:**
- 13 violações pré-existentes de acentuação em nyx_gauntlet.py (L116/237/1128/1158/1222/1238/1243/1259/1267/1281/1336/1348) detectadas pela validação periférica. **Não introduzidas** por esta sprint — escopo da sprint ortogonal `GAUNTLET-ACENTUACAO-FIX-01` (MASTER linha 349, PENDENTE).

---

## Contexto

Anti-débito materializado durante execução de `GAUNTLET-FIXTURES-SANDBOX-01` (2026-05-19). Após migrar 6 fixtures de `/tmp` para `~/.nyx/gauntlet_tmp/`, F2-01, F2-02 e F2-08 passaram (eram falhas de sandbox). F2-03 e F2-06 continuaram falhando, mas com causa raiz diferente: ambos asseguram `"loop.py" in r.output`, esperando que `glob('nyx/agent/*.py')` e `list_files('nyx/agent')` retornem o arquivo `loop.py`. Esse arquivo **não existe mais**: refactor anterior converteu `nyx/agent/loop.py` em pacote `nyx/agent/loop/` (`__init__.py`, `_constants.py`, `_core.py`, `_iteration.py`).

Evidência:
```
$ ls nyx/agent/loop/
_constants.py
_core.py
__init__.py
_iteration.py
__pycache__

$ ls nyx/agent/*.py | head
nyx/agent/banner.py
nyx/agent/banner_blink.py
nyx/agent/clipboard.py
nyx/agent/completer.py
nyx/agent/context.py
nyx/agent/git_ops.py
nyx/agent/__init__.py
nyx/agent/intent.py
nyx/agent/lang_check.py
nyx/agent/memory.py
nyx/agent/models.py
nyx/agent/model_tier.py
nyx/agent/onboarding.py
nyx/agent/output.py
nyx/agent/output_style.py
nyx/agent/parser.py
nyx/agent/path_resolver.py
nyx/agent/permissions.py
```

`parser.py` é candidato natural: arquivo de produção estável, presente desde o início do projeto, sem chance razoável de virar pacote no curto prazo.

## Diagnóstico do código atual

Grep `'loop\.py' in r\.output` em `scripts/gauntlet/nyx_gauntlet.py`:
- linha 2324 (F2-03 ok)
- linha 2325 (F2-03 details)
- linha 2339 (F2-06 ok)
- linha 2340 (F2-06 details)

Linha 3401 (`repo_map="nyx/agent/loop.py: class AgentLoop",`) é fixture de input para `CTX-09` (testa que `build_system_prompt` injeta corretamente o placeholder `repo_map` no template). É string literal interna, não consulta filesystem; **NÃO mexer**.

## Plano de implementação

### Passo 1 — Atualizar F2-03

```python
# Antes
r = reg.execute("glob", {"pattern": "nyx/agent/*.py"})
ok = r.success and "loop.py" in r.output
self._add("F2-03", "Glob encontra arquivo real", "e2e_real", ok, 0, details=f"has_loop={'loop.py' in r.output}")
```
```python
# Depois
r = reg.execute("glob", {"pattern": "nyx/agent/*.py"})
ok = r.success and "parser.py" in r.output
self._add("F2-03", "Glob encontra arquivo real", "e2e_real", ok, 0, details=f"has_parser={'parser.py' in r.output}")
```

### Passo 2 — Atualizar F2-06

```python
# Antes
r = reg.execute("list_files", {"path": str(PROJECT_ROOT / "nyx" / "agent")})
ok = r.success and "loop.py" in r.output
self._add("F2-06", "ListFiles diretório real", "e2e_real", ok, 0, details=f"has_loop={'loop.py' in r.output}")
```
```python
# Depois
r = reg.execute("list_files", {"path": str(PROJECT_ROOT / "nyx" / "agent")})
ok = r.success and "parser.py" in r.output
self._add("F2-06", "ListFiles diretório real", "e2e_real", ok, 0, details=f"has_parser={'parser.py' in r.output}")
```

### Passo 3 — Validar

```bash
./run.sh --smoke
bash scripts/sprint_invariants.sh
./run.sh --gauntlet --only e2e_real     # esperado: 8/8 APROVADO
./run.sh --gauntlet --only rapido       # esperado: P-07 ainda FAIL (pré-existente), demais OK
grep -nE "'loop\.py' in r\.output" scripts/gauntlet/nyx_gauntlet.py   # esperado: vazio
```

## Verificação binária

Antes:
```bash
grep -cE "'loop\.py' in r\.output" scripts/gauntlet/nyx_gauntlet.py
# Esperado: 4 (linhas 2324, 2325, 2339, 2340)
```

Depois:
```bash
grep -cE "'loop\.py' in r\.output" scripts/gauntlet/nyx_gauntlet.py
# Esperado: 0
grep -cE "'parser\.py' in r\.output" scripts/gauntlet/nyx_gauntlet.py
# Esperado: 4
```

## Riscos e mitigação

- **Risco:** futuro refactor converter `parser.py` em pacote. **Mitigação:** improvável a curto prazo; se ocorrer, sprint análoga (`GAUNTLET-PARSER-PY-REF-FIX-01`).
- **Risco:** quebrar significado semântico do teste. **Mitigação:** F2-03/F2-06 testam funcionalidade de `glob`/`list_files`, não dependem do nome específico do arquivo; qualquer arquivo estável serve.

## Não-objetivos (out-of-scope)

- **NÃO recriar** `nyx/agent/loop.py` (refactor para pacote foi decisão de arquitetura).
- **NÃO modificar** qualquer arquivo em `nyx/agent/loop/` (produção intocada).
- **NÃO mexer** em linha 3401 (`repo_map` fixture do teste CTX-09 — string interna do teste de prompt).
- **NÃO corrigir** P-07 (`tool_calls propagam` — falha pré-existente da fase proxy, fora de escopo; sprint própria se ressurgir).
- **NÃO migrar** referências similares em outros gauntlets/scripts; varredura global fora de escopo.

## Referências

- `VALIDATOR_BRIEF.md` (raiz do repo) — contratos de runtime
- Sprint `GAUNTLET-FIXTURES-SANDBOX-01` — origem do achado colateral
- `nyx/agent/loop/` — pacote que substituiu `loop.py`
- `GUIDE.md` `feedback_nenhum_debito.md` — protocolo anti-débito

---

*"Teste que assume layout de filesystem morto é teste mentindo." -- GAUNTLET-LOOP-PY-REF-FIX-01*
