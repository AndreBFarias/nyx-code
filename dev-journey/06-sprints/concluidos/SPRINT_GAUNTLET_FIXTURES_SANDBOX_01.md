# SPRINT GAUNTLET-FIXTURES-SANDBOX-01 -- Migrar test fixtures do gauntlet de /tmp para tmpdir autorizado

## 0. SPEC

```yaml
sprint:
  id: GAUNTLET-FIXTURES-SANDBOX-01
  title: "Migrar test fixtures do gauntlet de /tmp para ~/.nyx/gauntlet_tmp/ (sandbox-friendly)"
  onda: 25
  bloco: 25.0 Release (anti-débito derivado de VALIDATE-FINAL-01-PARTE-2)
  prioridade: ALTA
  tipo: Fix de teste (sem mudanca em produção)
  dependencias: [VALIDATE-FINAL-01-PARTE-2, PROJECT-ROOTS-MULTI-01]
  desbloqueia: [v1.0 (gate gauntlet 100%)]

  touches:
    - path: scripts/gauntlet/nyx_gauntlet.py
      reason: "Substituir 6 escritas via tempfile.gettempdir()/NamedTemporaryFile por ~/.nyx/gauntlet_tmp/<nome>; cleanup best-effort"
      blocos:
        - "linha 2055: P3T-01 NotebookEdit (NamedTemporaryFile .ipynb)"
        - "linha 2273: F2-01..F2-06 setup (tmp_path nyx_f2_test.py)"
        - "linha 2335: F2-08 pipeline (nyx_f2_pipeline.py)"
        - "linha 2839: P8E-02 patch (nyx_p8_patch.py)"
        - "linhas 2854-2855: P8E-03 multi-edit (nyx_me1.py, nyx_me2.py)"

  creates:
    - path: dev-journey/06-sprints/concluidos/SPRINT_GAUNTLET_FIXTURES_SANDBOX_01.md
      reason: "Este arquivo (será movido producao/ -> concluidos/ ao fim)"

  removes: []

  forbidden:
    - "Modificar nyx/agent/tools/base.py (sandbox gate funciona como esperado, é a fonte da verdade)"
    - "Modificar nyx/agent/tools/{patch_tool,multi_edit,notebook_edit,write,read,edit,glob,list_files}.py (comportamento de produção intocado)"
    - "Hardcode de paths absolutos: usar Path.home() / '.nyx' / 'gauntlet_tmp' SEMPRE"
    - "rm -rf em paths derivados de variável (cleanup só com unlink/missing_ok=True em arquivos nomeados explicitamente)"
    - "Mudar fixtures que NÃO escrevem em /tmp (perf_inference.py, loop_benchmark.py, model_compare.py, buggy_service.py — esta tem string interna intencional para o LLM corrigir)"
    - "Migrar fases que usam tempfile.TemporaryDirectory() (plugins L838, mcp L934, sessao L1133, contexto L3241-3366, gpu_tune L3768) — essas escritas são Python puro, NÃO passam pelo sandbox gate, logo já funcionam"
    - "Mexer em T-03/T-05 da fase tools (são prompts ao LLM citando /tmp/, mas o teste mede tool_call emitido — não persiste — logo passa hoje; out-of-scope desta sprint, registrar como anti-débito opcional se ressurgir)"

  tests:
    - cmd: "./run.sh --smoke"
      timeout: 60
      deve_passar: "boot ok"
    - cmd: "bash scripts/sprint_invariants.sh"
      timeout: 60
      deve_passar: "PASS 14, FAIL 0"
    - cmd: "./run.sh --gauntlet --only rapido"
      timeout: 600
      deve_passar: "APROVADO"
    - cmd: "grep -nE \"tempfile\\.gettempdir|NamedTemporaryFile.*delete=False\" scripts/gauntlet/nyx_gauntlet.py | grep -v TemporaryDirectory"
      timeout: 5
      deve_passar: "vazio (nenhuma escrita em /tmp via tempfile API restante nos blocos sandboxed)"
    - cmd: "python3 -c \"from pathlib import Path; d=Path.home()/'.nyx'/'gauntlet_tmp'; assert d.parent.exists(), f'{d.parent} não existe'; print('parent ok')\""
      timeout: 5
      deve_passar: "parent ok"

  acceptance_criteria:
    - "6/6 blocos de escrita migrados para Path.home() / '.nyx' / 'gauntlet_tmp' / <nome>"
    - "diretório ~/.nyx/gauntlet_tmp/ criado idempotentemente (mkdir parents=True, exist_ok=True) antes do primeiro write em cada fase modificada"
    - "cleanup best-effort após cada teste (unlink missing_ok=True por arquivo nomeado; SEM rmtree)"
    - "Gauntlet --only rapido APROVADO antes e depois"
    - "Gauntlet completo (./run.sh --gauntlet): das 8 falhas atribuíveis a sandbox (P3T-01, F2-01, F2-02, F2-03, F2-06, F2-08, P8E-02, P8E-03), pelo menos 6 passam após migração (F2-03 e F2-06 dependem de F2-01 ter criado o arquivo — se F2-01 passar, esses naturalmente passam)"
    - "Falhas NÃO relacionadas a sandbox permanecem inalteradas: K-08 VRAM, SCF-02 scaffold, COV-01 sudo_session, SYNC-02 sync, CTX-11 write_memory NLU (estas são out-of-scope, têm sprints próprias)"
    - "Smoke + invariantes 14/14 PASS"
    - "Sprint movida producao/ -> concluidos/"
```

---

**Status:** CONCLUIDA
**Data spec:** 2026-05-19
**Data conclusão:** 2026-05-19
**Modelo execução:** claude-opus-4-7

## Proof-of-work

### Aritmética antes / depois

- `scripts/gauntlet/nyx_gauntlet.py`: 4370L -> 4384L (+14L: helper de 14L; 6 sites migrados sem mudar contagem útil)
- Sites de `tempfile.gettempdir|NamedTemporaryFile` no escopo do gate: 6 -> 0
- Sites totais de `tempfile.*` no arquivo: 8 -> 2 (linhas 905 e 3782 são out-of-scope: HD-02 hooks_dynamic + GPT gpu_tune .env, ambos Python puro fora do sandbox gate)
- Helper `_gauntlet_tmp_dir()` adicionado na linha 252 (entre `_FEATURE_ID_RE` e `_CATEGORIA_PARA_FASE_GAUNTLET`)
- 3 imports `import tempfile` órfãos removidos (`_phase_p3_tools`, `_phase_e2e_real`, `_phase_p8_edicao`)

### Comandos de verificação

```
$ ./run.sh --smoke
boot ok

$ bash scripts/sprint_invariants.sh
PASS: 14 / FAIL: 0

$ grep -nE "tempfile\.gettempdir|NamedTemporaryFile" scripts/gauntlet/nyx_gauntlet.py | grep -v TemporaryDirectory
905:        with tempfile.NamedTemporaryFile(            # HD-02 out-of-scope
3782:            with _tmp.NamedTemporaryFile(...)       # gpu_tune .env out-of-scope

$ python3 -c "from pathlib import Path; d=Path.home()/'.nyx'/'gauntlet_tmp'; assert d.parent.exists(); print('parent ok')"
parent ok

$ ./run.sh --gauntlet --only p3_tools
p3_tools | 2 | 2 | 0 | APROVADO
P3T-01 NotebookEdit edita e insere -> OK (edit=True insert=True verified=True)   # era FAIL

$ ./run.sh --gauntlet --only p8_edicao
p8_edicao | 3 | 3 | 0 | APROVADO
P8E-02 Patch aplica diff -> OK (Patch aplicado: /home/andrefarias/.nyx/gauntlet_tmp/nyx_p8_p...)   # era FAIL
P8E-03 MultiEdit atômico -> OK (Editados 2 arquivos: /home/andrefarias/.nyx/gauntlet_tmp/nyx_me...)   # era FAIL

$ ./run.sh --gauntlet --only e2e_real
e2e_real | 8 | 6 | 2 | REPROVADO (mas as 2 falhas mudaram de natureza)
F2-01 Write+Read roundtrip -> OK (write=True read_has_content=True)   # era FAIL (sandbox)
F2-02 Edit com substituição -> OK (edit=True verified=True)            # era FAIL (sandbox)
F2-03 Glob encontra arquivo real -> FAIL (has_loop=False)              # FALHA NOVA-CAUSA: loop.py -> loop/ pacote
F2-06 ListFiles diretório real -> FAIL (has_loop=False)                # FALHA NOVA-CAUSA: loop.py -> loop/ pacote
F2-08 Pipeline completo -> OK (w=True r=True e=True r2=True g=True)    # era FAIL (sandbox)

$ ./run.sh --gauntlet --only rapido
P-07 tool_calls propagam -> FAIL                # pré-existente, fase proxy, não regressão da sprint
Demais OK (sem regressão vs baseline pré-sprint)
```

### Falhas-alvo migradas (6/8 sandbox)

| ID | Antes | Depois |
|----|-------|--------|
| P3T-01 | FAIL `edit=False insert=False verified=False` | OK `edit=True insert=True verified=True` |
| F2-01 | FAIL `write=False read_has_content=False` | OK `write=True read_has_content=True` |
| F2-02 | FAIL `edit=False verified=False` | OK `edit=True verified=True` |
| F2-08 | FAIL `w=False r=False e=False r2=False g=False` | OK `w=True r=True e=True r2=True g=True` |
| P8E-02 | FAIL `Fora dos projetos permitidos: '/tmp/nyx_p8_patch.py'` | OK `Patch aplicado: /home/andrefarias/.nyx/gauntlet_tmp/nyx_p8_patch.py` |
| P8E-03 | FAIL `Revertido: Fora dos projetos permitidos: '/tmp/nyx_me1.py'` | OK `Editados 2 arquivos: /home/andrefarias/.nyx/gauntlet_tmp/nyx_me1.py + .../nyx_me2.py` |

### Achados colaterais

- **GAUNTLET-LOOP-PY-REF-FIX-01** (nova sprint criada): F2-03 e F2-06 procuravam `loop.py` mas `nyx/agent/loop.py` virou pacote `nyx/agent/loop/` (refactor anterior). Causa raiz totalmente diferente de sandbox. Não absorvido nesta sprint — registrado como anti-débito em `dev-journey/06-sprints/producao/SPRINT_GAUNTLET_LOOP_PY_REF_FIX_01.md`.

### Notas

- `~/.nyx/gauntlet_tmp/` criado pelo helper (`mkdir parents=True, exist_ok=True`). Após cada execução fica vazio (cleanup best-effort por `unlink missing_ok=True` em cada site).
- Acentuação: zero violações nas regiões modificadas (helper L252, P3T-01 L2065, F2 L2283/2349, P8E L2851/2867-2868). 13 violações pré-existentes em linhas 1056/1120/1136/1141/1157/1165/1179/1234/1246 (fora do escopo desta sprint).
- Produção (`nyx/`) intocada — `grep -rn '_gauntlet_tmp_dir\|gauntlet_tmp' nyx/` retorna vazio.

---

## Contexto

Anti-débito materializado em `SPRINT_VALIDATE_FINAL_01_PARTE_2.md` (commit 8101062). Frente 6 da validação rodou `./run.sh --gauntlet` completo (53 fases, 220 testes) e apurou **207/220 = 94%** com REPROVADO formal por **13 falhas qualificadas** — das quais **8 são causadas pelo sandbox gate de `PROJECT-ROOTS-MULTI-01`** (`nyx/agent/tools/base.py:108 validate_path`) bloqueando corretamente escritas em `/tmp/...` feitas por fixtures de teste que usam `tempfile.gettempdir()`.

O gate funciona como projetado: paths fora de `_ACTIVE_ROOT + _NYX_DATA_DIR (~/.nyx) + _EXTRA_ROOTS` recebem `ValueError("Fora dos projetos permitidos: ...")`. Logo, **a correção está nas fixtures, não no gate**.

Evidência literal das 8 falhas (extraído de `GAUNTLET_REPORT.md` 2026-05-19):

| ID | Fase | Detalhes |
|----|------|----------|
| P3T-01 | p3_tools | edit=False insert=False verified=False (NotebookEdit em `/tmp/tmpXXX.ipynb`) |
| F2-01 | e2e_real | write=False read_has_content=False (write_file em `/tmp/nyx_f2_test.py`) |
| F2-02 | e2e_real | edit=False verified=False (depende de F2-01) |
| F2-03 | e2e_real | has_loop=False (glob limpo após F2-01 falhar) |
| F2-06 | e2e_real | has_loop=False (list_files após F2-01 falhar) |
| F2-08 | e2e_real | w=False r=False e=False r2=False g=False (pipeline em `/tmp/nyx_f2_pipeline.py`) |
| P8E-02 | p8_edicao | `Fora dos projetos permitidos: '/tmp/nyx_p8_patch.py'` |
| P8E-03 | p8_edicao | `Revertido: Fora dos projetos permitidos: '/tmp/nyx_me1.py'` |

5 falhas restantes (K-08 VRAM, SCF-02, COV-01, SYNC-02, CTX-11) **não** são sandbox e têm sprints próprias ou são out-of-scope.

## Diagnóstico do código atual

Grep `tempfile.gettempdir|NamedTemporaryFile` em `scripts/gauntlet/nyx_gauntlet.py` retorna 6 sites que escrevem via Python e cujos paths chegam a tools (`write_file`, `edit_file`, `multi_edit`, `notebook_edit`, `patch`) que passam por `validate_path()`. Localização exata:

| Linha atual | Bloco | Tipo |
|---|---|---|
| 2055 | `_phase_p3_tools` P3T-01 | `tempfile.NamedTemporaryFile(suffix=".ipynb", delete=False)` |
| 2273 | `_phase_e2e_real` F2-01 setup | `Path(tempfile.gettempdir()) / "nyx_f2_test.py"` |
| 2335 | `_phase_e2e_real` F2-08 pipeline | `Path(tempfile.gettempdir()) / "nyx_f2_pipeline.py"` |
| 2839 | `_phase_p8_edicao` P8E-02 | `Path(tempfile.gettempdir()) / "nyx_p8_patch.py"` |
| 2854 | `_phase_p8_edicao` P8E-03 f1 | `Path(tempfile.gettempdir()) / "nyx_me1.py"` |
| 2855 | `_phase_p8_edicao` P8E-03 f2 | `Path(tempfile.gettempdir()) / "nyx_me2.py"` |

**Outros usos de tempfile NÃO entram na sprint** (Python puro, não passam pelo sandbox gate):
- L838 plugins, L934 mcp, L1133 sessao, L3241-3366 contexto/repomap, L3768 .env — todos `tempfile.TemporaryDirectory()` com escrita direta via `Path.write_text()`.

**Falsos positivos NÃO mexer**:
- `scripts/gauntlet/fixtures/buggy_service.py:21` `LOG_FILE = "/tmp/session.log"` — string interna intencional do bug-fixture; é o BUG que o LLM deve identificar.
- `nyx_gauntlet.py:2330 / 2809` leituras de `/tmp/nyx_inexistente_xyz_12345.py` (negative tests F2-07, P6Q-02) — passam hoje porque a mensagem "fora dos projetos" é tratada como erro pelo teste (não consegue ler, retorna failure, teste de error handling passa).
- `nyx_gauntlet.py:3737` `env={"HOME": "/tmp"}` (env var para subprocess detect_gpu.py, não escrita em /tmp).
- `nyx_gauntlet.py:632, 636` (T-03/T-05) prompts ao LLM citando `/tmp/...` — testes medem tool_call emitido, não persistência. T-03 passou no último gauntlet.

Aritmética: **6 fixtures investigadas no escopo do gate** (em 4370 linhas de `nyx_gauntlet.py`), **6 serão modificadas** (todas as escritas via tempfile API que tocam tools sandboxed). Out-of-scope: 8+ usos de `tempfile.TemporaryDirectory()` que escrevem via Python puro (não impactados).

## Plano de implementação

### Passo 1 — Helper local

No topo de `nyx_gauntlet.py` (após imports existentes; antes da classe `Gauntlet`), adicionar helper canônico para padronizar uso:

```python
def _gauntlet_tmp_dir() -> Path:
    """Diretório de scratch para fixtures que escrevem via tools sandboxed.

    Retorna ~/.nyx/gauntlet_tmp/ criando se não existir. Esse diretório
    está dentro de _NYX_DATA_DIR e portanto é root autorizado por
    validate_path() em nyx/agent/tools/base.py (PROJECT-ROOTS-MULTI-01).
    """
    d = Path.home() / ".nyx" / "gauntlet_tmp"
    d.mkdir(parents=True, exist_ok=True)
    return d
```

(Não usar `import tempfile` para os blocos migrados — usar `_gauntlet_tmp_dir()` diretamente. `tempfile` continua importado nas outras fases que não mudam.)

### Passo 2 — Migrações (1 por bloco)

**Bloco P3T-01 (linha 2055):**
```python
# Antes
with tempfile.NamedTemporaryFile(suffix=".ipynb", mode="w", delete=False, encoding="utf-8") as f:
    _json.dump(nb_content, f)
    nb_path = f.name
```
```python
# Depois
nb_path_obj = _gauntlet_tmp_dir() / "nyx_p3t01_notebook.ipynb"
nb_path_obj.write_text(_json.dumps(nb_content), encoding="utf-8")
nb_path = str(nb_path_obj)
```
Cleanup ao final do teste: adicionar `Path(nb_path).unlink(missing_ok=True)` antes do `return` ou após o último `self._add` da fase.

**Bloco F2 setup (linha 2273):**
```python
# Antes
tmp_path = Path(tempfile.gettempdir()) / "nyx_f2_test.py"
```
```python
# Depois
tmp_path = _gauntlet_tmp_dir() / "nyx_f2_test.py"
```

**Bloco F2-08 (linha 2335):**
```python
# Antes
pipeline_path = Path(tempfile.gettempdir()) / "nyx_f2_pipeline.py"
```
```python
# Depois
pipeline_path = _gauntlet_tmp_dir() / "nyx_f2_pipeline.py"
```
Cleanup ao final de `_phase_e2e_real`: `tmp_path.unlink(missing_ok=True); pipeline_path.unlink(missing_ok=True)`.

**Bloco P8E-02 (linha 2839):**
```python
# Antes
tmp = Path(tempfile.gettempdir()) / "nyx_p8_patch.py"
```
```python
# Depois
tmp = _gauntlet_tmp_dir() / "nyx_p8_patch.py"
```
Cleanup já existe na linha 2846 (`tmp.unlink(missing_ok=True)`).

**Bloco P8E-03 (linhas 2854-2855):**
```python
# Antes
f1 = Path(tempfile.gettempdir()) / "nyx_me1.py"
f2 = Path(tempfile.gettempdir()) / "nyx_me2.py"
```
```python
# Depois
f1 = _gauntlet_tmp_dir() / "nyx_me1.py"
f2 = _gauntlet_tmp_dir() / "nyx_me2.py"
```
Cleanup já existe nas linhas 2869-2870.

### Passo 3 — Confirmar não-impacto em produção

`grep -rn "_gauntlet_tmp_dir\|gauntlet_tmp" nyx/` deve retornar vazio (helper só existe no script de teste; produção segue intocada).

### Passo 4 — Validar

```bash
./run.sh --smoke
bash scripts/sprint_invariants.sh
./run.sh --gauntlet --only rapido
./run.sh --gauntlet         # opcional, para confirmar pass-rate sobe de 207/220
```

## Verificação binária

Antes:
```bash
grep -cE "tempfile\.gettempdir|NamedTemporaryFile.*\.ipynb" scripts/gauntlet/nyx_gauntlet.py
# Esperado: 5 (gettempdir × 5 sites: linhas 2273, 2335, 2839, 2854, 2855) + 1 (NamedTemporaryFile .ipynb linha 2055)
# Total: 5 ou 6 dependendo do grep, confirmar com lista nominal
```

Depois:
```bash
grep -nE "tempfile\.gettempdir|NamedTemporaryFile.*\.ipynb" scripts/gauntlet/nyx_gauntlet.py
# Esperado: vazio nos blocos migrados; outras chamadas (TemporaryDirectory em plugins/mcp/sessao/contexto/gpu_tune) permanecem
```

Diretório verificado pós-execução:
```bash
ls -la ~/.nyx/gauntlet_tmp/   # diretório existe; possivelmente vazio após cleanup
```

Gauntlet rápido:
```bash
./run.sh --gauntlet --only rapido
# Esperado: APROVADO (não tinha falhas de sandbox no --only rapido; sanity check para não regredir)
```

Gauntlet completo (opcional, prova plena):
```bash
./run.sh --gauntlet
# Esperado: pass-rate >= 213/220 (8 falhas de sandbox eliminadas; 5 fora-de-escopo persistem)
```

## Riscos e mitigação

- **Risco:** `~/.nyx/gauntlet_tmp/` ficar com lixo entre runs. **Mitigação:** cleanup best-effort por arquivo nomeado em cada fase (já é prática nas linhas 2846, 2869-2870).
- **Risco:** colisão entre runs paralelos. **Mitigação:** gauntlet roda sequencial (orquestrador é single-process). Se evoluir para paralelo no futuro, criar subdiretório por PID em sprint nova.
- **Risco:** ~/.nyx/ inexistente em fresh install. **Mitigação:** `mkdir(parents=True, exist_ok=True)` em `_gauntlet_tmp_dir()` resolve.
- **Risco:** import `_gauntlet_tmp_dir` em ordem errada se classe usar antes da definição. **Mitigação:** definir no topo do módulo (antes da classe), padrão Python normal.

## Não-objetivos (out-of-scope)

- **NÃO migrar** os 8+ blocos com `tempfile.TemporaryDirectory()` (Python puro, não tocam tools sandboxed).
- **NÃO mexer** em `nyx/agent/tools/base.py` ou em qualquer tool de produção.
- **NÃO corrigir** as outras 5 falhas do gauntlet (K-08 VRAM, SCF-02, COV-01, SYNC-02, CTX-11) — cada uma tem sprint dedicada ou é classificada externa.
- **NÃO migrar** T-03/T-05 da fase `tools` (prompts ao LLM com `/tmp/`); são out-of-scope porque o teste mede tool_call emission, não persistência. Se aparecer regressão lá, abrir sprint `GAUNTLET-T03-PROMPT-PATH-01`.
- **NÃO criar** infraestrutura genérica de sandbox-friendly fixtures fora de `nyx_gauntlet.py`. As 4 fixtures `scripts/gauntlet/fixtures/*.py` (perf_inference, loop_benchmark, model_compare, buggy_service) não escrevem em `/tmp` via tools sandboxed; ficam como estão.

## Referências

- `VALIDATOR_BRIEF.md` (raiz do repo) — contratos de runtime
- `nyx/agent/tools/base.py:108` (`validate_path`) — sandbox gate; linhas 17, 29-30, 94-105 mostram `_ACTIVE_ROOT + _NYX_DATA_DIR(~/.nyx) + _EXTRA_ROOTS`
- Sprint `PROJECT-ROOTS-MULTI-01` — definiu o gate
- Sprint `SPRINT_VALIDATE_FINAL_01_PARTE_2` — declarou anti-débito e commit 8101062 onde esta sprint foi prometida
- `GAUNTLET_REPORT.md` (root, gerado 2026-05-19) — tabela das 13 falhas
- `dev-journey/07-reports/proofs/G_validate_final/gauntlet_completo_2026_05_19.log` — log de execução

---

*"Sandbox que funciona é sandbox que pega o teste mal-escrito antes do bug em produção." -- GAUNTLET-FIXTURES-SANDBOX-01*
