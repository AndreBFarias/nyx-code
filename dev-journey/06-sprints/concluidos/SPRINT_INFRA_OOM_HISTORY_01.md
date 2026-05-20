# SPRINT INFRA-OOM-HISTORY-01 — Persistência cross-session do contador OOM em ~/.nyx/proxy_stats.json

## 0. SPEC (machine-readable)

```yaml
sprint:
  id: INFRA-OOM-HISTORY-01
  title: "Persistir oom_recovery_count em ~/.nyx/proxy_stats.json para auditoria longitudinal de instabilidade"
  onda: 24
  bloco: 24.1 Infra resiliente
  prioridade: BAIXA
  tipo: Hardening+Observability+Persistencia
  dependencias: [INFRA-OOM-02, INFRA-OOM-RETRY-STEP-01, INFRA-OOM-STATS-CLI-01]
  desbloqueia: []

  touches:
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/proxy.py
      reason: "Adicionar 2 helpers privados (_load_persisted_stats, _persist_stats), modificar _on_startup (linhas 871-881) para hidratar state['oom_recovery_count'] a partir do JSON, modificar handle_chat (linhas 448 e 480) para invocar _persist_stats após incrementar contador. Import Path ja existe (linha 21)."
      linhas_alvo: "~88 (helpers novos perto de _is_oom_error), 448 e 480 (handle_chat OOM recovery), 871-881 (_on_startup)"
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/config/defaults.py
      reason: "Constante PROXY_STATS_PATH = Path.home() / '.nyx' / 'proxy_stats.json' espelhando padrao de NYX_MCP_CONFIG (linhas 15-18)"
      linhas_alvo: "~25 (apos NYX_PLUGINS_DIR, antes de COCKPIT_PORT)"
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/scripts/gauntlet/nyx_gauntlet.py
      reason: "Novo RB-06 espelhando RB-04/RB-05: import nyx.proxy + assert hasattr(_load_persisted_stats, _persist_stats) + grep no source para confirmar chamadas em _on_startup e handle_chat. Sem boot real, sem escrita real em disco — apenas getattr/hasattr/grep igual RB-04 e RB-05."
      linhas_alvo: "apos linha 4207 (fim do RB-05 em _phase_robustez_boot)"

  creates: []
  removes: []

  n_to_n_pairs:
    - descricao: "Cada novo helper publico em proxy.py espelha-se em assert no gauntlet (RB-06)"
      paths:
        - /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/proxy.py
        - /home/andrefarias/Desenvolvimento/Nyx-Code/scripts/gauntlet/nyx_gauntlet.py

  forbidden:
    - "Mudar contrato de /admin/stats — handle_stats continua retornando exatamente as 4 chaves (oom_recovery_count, num_gpu_current, num_gpu_initial, oom_degraded). first_session e last_recovery sao detalhes do arquivo persistido, NAO do endpoint."
    - "Adicionar I/O bloqueante em hot path de handle_chat — _persist_stats e chamado apos resposta enviada (linha 448 e 480 ja estao apos log 'OOM recovery OK', sem mais await de cliente HTTP). E escrita pequena (<200B), atomica via tmp+replace; ainda assim, falha de I/O nao deve quebrar o recovery."
    - "Falhar boot por erro de persistencia — _on_startup com JSON corrompido/permissao negada/disco cheio loga warning e segue com count=0 em memoria. ADR-001 Local First exige servico vivo."
    - "Sobrescrever _OOM_DEGRADED, _OOM_PATTERNS, _is_oom_error, _next_num_gpu_step existentes — apenas adicionar helpers novos."
    - "Mudar formato de num_gpu_initial — continua snapshot imutavel injetado em main()."
    - "Persistir num_gpu_current ou num_gpu_initial — apenas oom_recovery_count + metadados first_session/last_recovery. num_gpu eh efemero por execucao."
    - "Sincronizar entre multiplas instancias do proxy — sem lock; ultima escrita vence (single-instance via NYX_PID_FILE ja garante 1 proxy por vez)."
    - "Migracao de schema — versao 1 fixa. Se version != '1' no JSON, tratar como corrompido (mover .bak + count=0)."
    - "Rotacao/cleanup automatico do .bak — fica para sprint futura se ressurgir."
    - "Spawn de subprocess ou rede em _load_persisted_stats / _persist_stats — apenas open/read/write/replace puros."

  tests:
    - cmd: "./run.sh --smoke"
      timeout: 30
      deve_passar: "boot ok"
    - cmd: "bash scripts/sprint_invariants.sh"
      timeout: 60
      deve_passar: "PASS: 14, FAIL: 0 (baseline preservada)"
    - cmd: "./run.sh --gauntlet --only rapido"
      timeout: 300
      deve_passar: "100% (regression-free)"
    - cmd: "./run.sh --gauntlet --only proxy"
      timeout: 300
      deve_passar: "100% (regression-free)"
    - cmd: "./run.sh --gauntlet --only robustez_boot"
      timeout: 300
      deve_passar: "100% (RB-06 novo PASS; RB-03/04/05 preservados)"
    - cmd: "/home/andrefarias/.local/bin/ruff check nyx/ scripts/gauntlet/nyx_gauntlet.py"
      timeout: 30
      deve_passar: "All checks passed."
    - cmd: "python3 ~/.config/zsh/scripts/validar-acentuacao.py --paths nyx/proxy.py nyx/config/defaults.py scripts/gauntlet/nyx_gauntlet.py dev-journey/06-sprints/producao/SPRINT_INFRA_OOM_HISTORY_01.md"
      timeout: 30
      deve_passar: "exit 0 (zero violacoes)"
    - cmd: "./venv/bin/python -c \"from nyx.proxy import _load_persisted_stats, _persist_stats; import json, pathlib; p=pathlib.Path.home()/'.nyx'/'proxy_stats_test.json'; _persist_stats({'oom_recovery_count': 42}, path=p); d=_load_persisted_stats(path=p); assert d['oom_recovery_count']==42, d; p.unlink()\""
      timeout: 15
      deve_passar: "helper unit roundtrip OK"
    - cmd: "echo '{invalid json' > ~/.nyx/proxy_stats.json && ./venv/bin/python -c \"from nyx.proxy import _load_persisted_stats; d=_load_persisted_stats(); assert d['oom_recovery_count']==0\" && ls ~/.nyx/proxy_stats.json.bak"
      timeout: 15
      deve_passar: "JSON corrompido detectado, .bak criado, count=0 retornado"
    - cmd: "rm -f ~/.nyx/proxy_stats.json ~/.nyx/proxy_stats.json.bak && echo '{\"version\":\"1\",\"oom_recovery_count\":5,\"first_session\":\"2026-05-20T00:00:00\",\"last_recovery\":\"2026-05-20T01:00:00\"}' > ~/.nyx/proxy_stats.json && ./run.sh --proxy & sleep 3 && curl -s http://127.0.0.1:11436/admin/stats | python3 -c 'import json,sys; d=json.load(sys.stdin); assert d[\"oom_recovery_count\"]==5, d' && pkill -f 'nyx/proxy.py' && rm -f ~/.nyx/proxy_stats.json"
      timeout: 30
      deve_passar: "Proxy hidrata count=5 do arquivo no startup, /admin/stats retorna 5"

  acceptance_criteria:
    - "nyx/config/defaults.py declara PROXY_STATS_PATH = Path.home() / '.nyx' / 'proxy_stats.json' como str ou Path; espelha padrao de NYX_MCP_CONFIG (linhas 15-18)."
    - "nyx/proxy.py importa PROXY_STATS_PATH de nyx.config.defaults (apos linha 50, ordenado alfabeticamente)."
    - "Helper _load_persisted_stats(path: Path | None = None) -> dict, retorna dict com chave 'oom_recovery_count' (int). Path opcional para teste; default PROXY_STATS_PATH. Em sucesso, retorna conteudo lido + valida schema minimo (chave oom_recovery_count int)."
    - "Helper _persist_stats(state: dict, path: Path | None = None) -> None, escreve JSON {version, oom_recovery_count, first_session, last_recovery} via tmp + os.replace atomico. Path opcional. Cria diretorio pai (~/.nyx) se ausente via mkdir(parents=True, exist_ok=True)."
    - "Tratamento de erro em _load_persisted_stats: (a) arquivo ausente -> retorna {'oom_recovery_count': 0} sem warning; (b) JSON parse fail -> log warning + move corrompido para .bak (Path.rename) + retorna {'oom_recovery_count': 0}; (c) schema invalido (chave faltando ou nao-int ou version != '1') -> log warning + .bak + count=0; (d) permissao negada -> log warning + count=0."
    - "Tratamento de erro em _persist_stats: (a) permissao negada / disco cheio -> log warning + continua sem raise (NAO falha o caminho de recovery do OOM); (b) tmp file lixo de execucao anterior -> sobrescreve sem reclamar."
    - "_on_startup (linhas 871-881) ganha chamada inicial a _load_persisted_stats(); se 'oom_recovery_count' retornado > 0, log info 'Hidratando oom_recovery_count=%d do arquivo persistido' e state['oom_recovery_count'] = valor lido. Caso contrario, state['oom_recovery_count'] = 0 (atual)."
    - "handle_chat linhas 448 e 480 (apos cada incremento de state['oom_recovery_count']): chamada a _persist_stats(state). Como sao 2 sitios, validar via grep que ambos invocam. NAO mover incremento — apenas adicionar a chamada de persistencia na linha seguinte."
    - "Estrutura JSON gravado: {'version': '1', 'oom_recovery_count': int, 'first_session': iso8601 str, 'last_recovery': iso8601 str ou null}. first_session preserva valor existente se ja gravado; novo apenas na criacao. last_recovery atualiza a cada chamada de _persist_stats."
    - "Contrato de /admin/stats preservado: handle_stats (linhas 848-868) continua retornando exatamente as 4 chaves originais (oom_recovery_count, num_gpu_current, num_gpu_initial, oom_degraded). Nao expoe first_session/last_recovery (esses sao detalhes internos do arquivo)."
    - "RB-06 no gauntlet (fase robustez_boot, apos RB-05): import nyx.proxy + hasattr(_load_persisted_stats) + hasattr(_persist_stats) + grep 'PROXY_STATS_PATH' em proxy.py + grep '_load_persisted_stats(' em _on_startup + grep '_persist_stats(state' apos cada 'OOM recovery OK' em handle_chat. Mesma estrutura de RB-04 (linhas 4120-4152)."
    - "Smoke ok"
    - "Invariantes PASS 14, FAIL 0"
    - "Gauntlet rapido + proxy + robustez_boot 100%"
    - "Ruff All checks passed em nyx/ + scripts/gauntlet/nyx_gauntlet.py"
    - "Acentuacao PT-BR correta nos arquivos tocados (validador via --paths)"
    - "Sem emojis em codigo, commit, doc"
    - "Sem mencao a IA externa em .py"
```

---

**Status:** RASCUNHO -> EM_EXECUCAO assim que /sprint disparar
**Data criacao:** 2026-05-20 (quarta sessao)
**Modelo obrigatorio:** claude-opus-4-7 (sem subagentes; Read/Grep/Glob direto)

---

## 1. Contexto

INFRA-OOM-02 instalou contador `state["oom_recovery_count"]` em memoria + endpoint GET /admin/stats. INFRA-OOM-RETRY-STEP-01 enriqueceu a cadeia para 2 retries (15 -> 7 -> 0) preservando o contador (+1 por OOM event, nao por retry). INFRA-OOM-STATS-CLI-01 trouxe slash `/stats` que consome o endpoint.

**Lacuna:** o contador zera a cada restart do proxy. Em sessao longa rodando dias (ADR-001 Local First, dev em RTX 3050 4GB onde OOM e fenomeno frequente), perdemos a serie temporal de "quantas vezes degradou hoje, esta semana, este mes". Sem isso, fica impossivel correlacionar OOM crescente com hardware envelhecendo, ou validar que um upgrade de hardware reduziu efetivamente os eventos.

**Acao:** persistir `oom_recovery_count` em `~/.nyx/proxy_stats.json` (mesmo padrao de outros artefatos locais — `image_index.json`, `sessions/`, `tasks.json`, `cache/repomap.json`). Hidratar em `_on_startup`, gravar a cada incremento em `handle_chat`.

**Filosofia:** ADR-001 Local First, write-through. Sem servico externo, sem telemetria. Apenas um JSON pequeno mantido proximo do usuario para inspecao via `cat`/`jq`/`/stats` ao longo do tempo.

---

## 2. Hipoteses verificadas via grep PRE-0.3

Confirmadas no codigo atual (apos INFRA-OOM-STATS-CLI-01 e INFRA-OOM-RETRY-STEP-01):

- **`_on_startup`** existe em `nyx/proxy.py:871-881`. Popula `state.setdefault("oom_recovery_count", 0)` na linha 880.
- **`handle_stats`** vive em `nyx/proxy.py:848-868`. Retorna JSON com 4 chaves. Loopback-guard via `_LOOPBACK_HOSTS`.
- **`state["oom_recovery_count"]` mutacao** em `handle_chat`:
  - Linha 448: `state["oom_recovery_count"] = state.get("oom_recovery_count", 0) + 1` (apos log "OOM recovery OK: resposta via GPU parcial")
  - Linha 480: `state["oom_recovery_count"] = state.get("oom_recovery_count", 0) + 1` (apos log "OOM recovery OK: resposta via CPU")
- **`Path.home() / ".nyx"`** ja e padrao consagrado no projeto: `image_index.json` (cli_helpers.py:18), `sessions/` (agent/persistence.py:19), `skills/` (skill_tool.py:15), `cache/repomap.json` (repomap.py:21), `pastes/` (clipboard.py:18), `tasks.json` (tools/task_manager.py:23).
- **`Path` ja importado** em `nyx/proxy.py:21` (`from pathlib import Path`).
- **`PROJECT_ROOT`** no gauntlet `scripts/gauntlet/nyx_gauntlet.py:4021` define `proxy_py = PROJECT_ROOT / "nyx" / "proxy.py"`, ja consumido por RB-03/04/05.
- **`main()`** em proxy.py:909 inicializa `app["state"]` com 3 chaves; `_on_startup` complementa via `setdefault`. Hidratacao do JSON cabe em `_on_startup` apos os `setdefault`.
- **Constante de path em config**: `NYX_MCP_CONFIG` (defaults.py:15-18) demonstra o idioma — `os.environ.get(...) or str(Path.home() / ".nyx" / "<file>")`. Para `PROXY_STATS_PATH` nao precisa env override (uso interno fixo), mas se quiser consistencia: env var `NYX_PROXY_STATS_PATH` opcional.

Conclusao: spec viavel, todas as superficies de modificacao confirmadas. Sem risco de hipotese divergente no passo 0.3.

---

## 3. Escopo (touches autorizados)

### Arquivos a modificar

1. **`/home/andrefarias/Desenvolvimento/Nyx-Code/nyx/proxy.py`** (930L atual)
   - Adicionar import `PROXY_STATS_PATH` apos linha 50 (ordenacao alfabetica preservada).
   - Adicionar 2 helpers privados (`_load_persisted_stats`, `_persist_stats`) apos `_next_num_gpu_step` (linha 106). Estimativa: ~40L.
   - Modificar `_on_startup` (linhas 871-881): apos `setdefault("oom_recovery_count", 0)`, chamar `_load_persisted_stats()` e sobrescrever se valor > 0 + log info. Estimativa: ~6L.
   - Modificar `handle_chat`:
     - Apos linha 448 (incremento GPU parcial): chamar `_persist_stats(state)`.
     - Apos linha 480 (incremento CPU): chamar `_persist_stats(state)`.
     - Estimativa: ~4L (2 linhas + 2 comentarios).

2. **`/home/andrefarias/Desenvolvimento/Nyx-Code/nyx/config/defaults.py`** (135L atual)
   - Adicionar constante `PROXY_STATS_PATH` apos `NYX_PLUGINS_DIR` (linha 24), antes de `COCKPIT_PORT`. Estimativa: ~4L (incluindo comentario explicativo + env override opcional espelhando NYX_MCP_CONFIG).

3. **`/home/andrefarias/Desenvolvimento/Nyx-Code/scripts/gauntlet/nyx_gauntlet.py`** (~4685L atual)
   - Adicionar novo RB-06 em `_phase_robustez_boot` apos RB-05 (linha 4207). Estimativa: ~50L (espelha estrutura completa de RB-05).

### Arquivos a criar
Nenhum (apenas modificacoes).

### Arquivos NAO a tocar (invariantes)

- `nyx/agent/commands/stats.py` (consumer do endpoint; nao precisa mudar, contrato preservado).
- `nyx/cli_handlers.py:709` (`_handle_stats` sentinela `__stats__`; sem relacao com persistencia).
- Qualquer arquivo em `nyx/agent/`, `nyx/themes/`, `nyx/cli*.py` exceto `proxy.py`.
- `nyx/config/defaults.py` fora da regiao apontada (sem mover constantes existentes).
- `handle_tune`, `handle_health`, `handle_shutdown`, `handle_models`, `handle_model`, `handle_chat` exceto linhas 448 e 480.
- RB-01/02/03/04/05 do gauntlet (apenas adicionar RB-06, nao tocar nos existentes).

---

## 4. Plano de implementacao (passos numerados)

### Passo 1 — config/defaults.py

Inserir apos linha 24 (apos `NYX_PLUGINS_DIR`):

```python
# Stats persistidos do proxy (INFRA-OOM-HISTORY-01). Mantem oom_recovery_count
# cross-session para auditoria longitudinal de instabilidade. JSON pequeno,
# atomico via tmp + os.replace. Override via NYX_PROXY_STATS_PATH (test isolation).
PROXY_STATS_PATH: str = os.environ.get(
    "NYX_PROXY_STATS_PATH",
    str(__import__("pathlib").Path.home() / ".nyx" / "proxy_stats.json"),
)
```

Espelha exatamente o padrao de `NYX_MCP_CONFIG` linhas 15-18.

### Passo 2 — proxy.py imports

Inserir nova linha apos linha 50 (apos `num_predict_for as _num_predict_for`):

```python
from nyx.config.defaults import PROXY_STATS_PATH as _PROXY_STATS_PATH  # noqa: E402
```

### Passo 3 — proxy.py helpers (apos linha 106)

```python
def _load_persisted_stats(path: Path | None = None) -> dict:
    """Le ~/.nyx/proxy_stats.json. Retorna {'oom_recovery_count': int}.

    Tratamento defensivo: arquivo ausente -> count=0 sem warning. Parse fail,
    schema invalido ou version != '1' -> log warning + move para .bak +
    count=0. Permissao negada -> log warning + count=0. NUNCA propaga
    excecao para nao quebrar boot (ADR-001 Local First).
    """
    p = path if path is not None else Path(_PROXY_STATS_PATH)
    if not p.exists():
        return {"oom_recovery_count": 0}
    try:
        raw = p.read_text(encoding="utf-8")
        data = json.loads(raw)
        if not isinstance(data, dict):
            raise ValueError("schema: top-level nao e dict")
        if data.get("version") != "1":
            raise ValueError(f"schema: version invalida: {data.get('version')}")
        count = data.get("oom_recovery_count")
        if not isinstance(count, int):
            raise ValueError(f"schema: oom_recovery_count nao e int: {type(count)}")
        return data
    except Exception as e:
        logger.warning("proxy_stats.json invalido (%s); criando .bak e zerando", e)
        try:
            p.rename(p.with_suffix(p.suffix + ".bak"))
        except OSError as bak_err:
            logger.warning("Falha ao criar .bak: %s", bak_err)
        return {"oom_recovery_count": 0}


def _persist_stats(state: dict, path: Path | None = None) -> None:
    """Escreve oom_recovery_count em ~/.nyx/proxy_stats.json atomicamente.

    Atomicidade via write -> os.replace (POSIX). Preserva first_session se
    arquivo ja existia. last_recovery sempre atualiza para now. Falha de I/O
    loga warning e segue (nao bloqueia recovery do OOM).
    """
    from datetime import datetime, timezone

    p = path if path is not None else Path(_PROXY_STATS_PATH)
    try:
        p.parent.mkdir(parents=True, exist_ok=True)
        existing = {}
        if p.exists():
            try:
                existing = json.loads(p.read_text(encoding="utf-8"))
                if not isinstance(existing, dict):
                    existing = {}
            except Exception:
                existing = {}
        now_iso = datetime.now(timezone.utc).isoformat()
        payload = {
            "version": "1",
            "oom_recovery_count": int(state.get("oom_recovery_count", 0)),
            "first_session": existing.get("first_session") or now_iso,
            "last_recovery": now_iso,
        }
        tmp = p.with_suffix(p.suffix + ".tmp")
        tmp.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        os.replace(tmp, p)
    except OSError as e:
        logger.warning("Falha ao persistir proxy_stats.json: %s", e)
```

### Passo 4 — proxy.py _on_startup (linhas 871-881)

Apos linha 880 (`state.setdefault("oom_recovery_count", 0)`):

```python
    # INFRA-OOM-HISTORY-01: hidrata contador cross-session se arquivo existir.
    persisted = _load_persisted_stats()
    if persisted.get("oom_recovery_count", 0) > 0:
        state["oom_recovery_count"] = persisted["oom_recovery_count"]
        logger.info("Hidratando oom_recovery_count=%d do arquivo persistido", state["oom_recovery_count"])
```

### Passo 5 — proxy.py handle_chat (linhas 448 e 480)

Apos linha 448:

```python
                            state["oom_recovery_count"] = state.get("oom_recovery_count", 0) + 1
                            _persist_stats(state)  # INFRA-OOM-HISTORY-01
```

Apos linha 480:

```python
                        state["oom_recovery_count"] = state.get("oom_recovery_count", 0) + 1
                        _persist_stats(state)  # INFRA-OOM-HISTORY-01
```

### Passo 6 — scripts/gauntlet/nyx_gauntlet.py RB-06 (apos linha 4207)

```python
        # RB-06: proxy persiste oom_recovery_count em ~/.nyx/proxy_stats.json (INFRA-OOM-HISTORY-01)
        t = time.monotonic()
        try:
            import importlib as _imp

            mod = _imp.import_module("nyx.proxy")
            tem_load = hasattr(mod, "_load_persisted_stats")
            tem_persist = hasattr(mod, "_persist_stats")
            src = proxy_py.read_text(encoding="utf-8")
            tem_const = "PROXY_STATS_PATH" in src
            tem_load_startup = "_load_persisted_stats()" in src and "Hidratando oom_recovery_count" in src
            # 2 chamadas a _persist_stats no handle_chat (uma por sitio de incremento)
            chamadas_persist = src.count("_persist_stats(state)")
            persist_ok = chamadas_persist >= 2
            ok = bool(tem_load and tem_persist and tem_const and tem_load_startup and persist_ok)
            self._add(
                "RB-06",
                "Proxy persiste oom_recovery_count cross-session (INFRA-OOM-HISTORY-01)",
                "robustez_boot",
                ok,
                time.monotonic() - t,
                details=(
                    f"load={tem_load} persist={tem_persist} const={tem_const} "
                    f"hidrata={tem_load_startup} chamadas_persist={chamadas_persist}"
                ),
            )
        except Exception as e:
            self._add(
                "RB-06",
                "Proxy persiste oom_recovery_count cross-session (INFRA-OOM-HISTORY-01)",
                "robustez_boot",
                False,
                time.monotonic() - t,
                error=str(e),
            )
```

### Passo 7 — Smoke + invariantes + ruff + acentuacao

Rodar em ordem (com cleanup explicito apos cada teste com modelo):

```bash
./run.sh --smoke
bash scripts/sprint_invariants.sh
/home/andrefarias/.local/bin/ruff check nyx/ scripts/gauntlet/nyx_gauntlet.py
python3 ~/.config/zsh/scripts/validar-acentuacao.py --paths nyx/proxy.py nyx/config/defaults.py scripts/gauntlet/nyx_gauntlet.py dev-journey/06-sprints/producao/SPRINT_INFRA_OOM_HISTORY_01.md
```

### Passo 8 — Gauntlet rapido + proxy + robustez_boot

```bash
./run.sh --gauntlet --only rapido
./run.sh --gauntlet --only proxy
./run.sh --gauntlet --only robustez_boot
```

Esperado: 100% nas 3 fases; RB-06 PASS novo, RB-03/04/05 preservados.

### Passo 9 — Proof helper unit

```bash
./venv/bin/python -c "
from nyx.proxy import _load_persisted_stats, _persist_stats
import pathlib
p = pathlib.Path.home() / '.nyx' / 'proxy_stats_test.json'
if p.exists(): p.unlink()
_persist_stats({'oom_recovery_count': 42}, path=p)
d = _load_persisted_stats(path=p)
assert d['oom_recovery_count'] == 42, d
assert d['version'] == '1', d
assert 'first_session' in d
assert 'last_recovery' in d
print('roundtrip OK:', d)
p.unlink()
"
```

### Passo 10 — Proof corrupcao

```bash
rm -f ~/.nyx/proxy_stats.json ~/.nyx/proxy_stats.json.bak
echo '{invalid json' > ~/.nyx/proxy_stats.json
./venv/bin/python -c "
from nyx.proxy import _load_persisted_stats
d = _load_persisted_stats()
assert d['oom_recovery_count'] == 0, d
print('corrupcao OK; count=', d['oom_recovery_count'])
"
ls ~/.nyx/proxy_stats.json.bak  # deve existir
rm -f ~/.nyx/proxy_stats.json ~/.nyx/proxy_stats.json.bak
```

### Passo 11 — Proof restart real

```bash
rm -f ~/.nyx/proxy_stats.json
cat > ~/.nyx/proxy_stats.json <<'EOF'
{
  "version": "1",
  "oom_recovery_count": 5,
  "first_session": "2026-05-20T00:00:00+00:00",
  "last_recovery": "2026-05-20T01:00:00+00:00"
}
EOF
./run.sh --proxy &
PROXY_PID=$!
sleep 3
curl -s http://127.0.0.1:11436/admin/stats | python3 -m json.tool
# Esperar JSON com oom_recovery_count: 5
pkill -f "nyx/proxy.py"
wait $PROXY_PID 2>/dev/null
rm -f ~/.nyx/proxy_stats.json
```

### Passo 12 — Cleanup obrigatorio

```bash
pkill -f "nyx/proxy.py"  # se ainda vivo
pkill -f "ollama serve"  # se foi spawn em algum teste
nvidia-smi  # confirmar VRAM livre
rm -f ~/.nyx/proxy_stats.json ~/.nyx/proxy_stats.json.bak ~/.nyx/proxy_stats_test.json
```

---

## 5. Invariantes a preservar

- **ADR-001 Local First:** sem servico externo, sem telemetria. Apenas JSON local em `~/.nyx`. Falha de I/O nunca quebra boot ou recovery (degradacao graciosa).
- **ADR-010 Zero mocks no proof-of-work:** proof real via subprocess de proxy + curl /admin/stats, nao apenas unit test. Mas RB-06 do gauntlet pode ser estatico (grep + getattr) por simetria com RB-04/RB-05.
- **Contrato /admin/stats:** 4 chaves (`oom_recovery_count, num_gpu_current, num_gpu_initial, oom_degraded`). Consumido por `nyx/agent/commands/stats.py` (INFRA-OOM-STATS-CLI-01). NAO adicionar chaves novas no endpoint.
- **`_OOM_DEGRADED` modulo-global imutavel apos primeiro OOM:** sem reanimacao em runtime. Persistencia nao muda isso (apenas o contador acumula entre sessoes).
- **`num_gpu_initial` snapshot imutavel:** continua sendo args.num_gpu do startup. Persistir num_gpu seria errado (e efemero por execucao com --num-gpu N).
- **Cap-counter robusto em RB-06:** evitar idioma fragil de `line.lstrip().startswith("else:")` que o BRIEF aponta como pegadinha (achado de INFRA-OOM-RETRY-STEP-01). RB-06 usa `src.count("_persist_stats(state)")` que e idempotente e nao depende de indentacao.
- **Acentuacao PT-BR correta:** validador via `--paths arq1 arq2` (sintaxe correta apontada no BRIEF; ver tambem INFRA-VALIDATE-ACENTUACAO-CLI-FIX-01 linha 125ii do MASTER).
- **Ruff invocado via binario direto:** `/home/andrefarias/.local/bin/ruff` (BRIEF — `./venv/bin/python -m ruff` falha).
- **Sem emojis em codigo/commit/doc.**
- **Sem mencao a IA externa em .py.**
- **Smoke ok antes de marcar CONCLUIDA** (`feedback_smoke_boot.md`).
- **Cleanup explicito apos teste com modelo:** pkill + nvidia-smi (BRIEF check #5).
- **Nenhum debito implicito:** achado colateral durante execucao vira sprint nova com ID no MASTER (memoria `feedback_nenhum_debito.md`).
- **Write-through:** atualizar Checkpoint.md ao iniciar e ao concluir (memoria `feedback_checkpoint_md.md`).

---

## 6. Aritmetica (sem meta numerica estrita)

Esta sprint **nao tem meta tipo `arquivo.py <N linhas`** — e adicao incremental, nao refactor.

Ainda assim, registro previsao de delta de linhas:

| Arquivo | Atual | Esperado apos sprint | Delta |
|---|---|---|---|
| `nyx/proxy.py` | 930L | ~980L | +50L |
| `nyx/config/defaults.py` | 135L | ~140L | +5L |
| `scripts/gauntlet/nyx_gauntlet.py` | ~4685L | ~4735L | +50L |
| **Total** | **5750L** | **~5855L** | **+105L** |

Sem hard cap; apenas referencia para auditoria.

---

## 7. Testes

### Baseline
- Invariantes hoje (antes da sprint): PASS 14, FAIL 0 (confirmado pelos relatos de INFRA-OOM-RETRY-STEP-01 + INFRA-OOM-STATS-CLI-01).
- Gauntlet rapido: 18/18 (per MASTER linha 125bb).
- Gauntlet proxy: 6/6 (per MASTER linha 125y).
- Gauntlet robustez_boot: 4/4 com RB-03/04/05 (per MASTER linhas 125y/125aa).

### Esperado
- Invariantes: PASS 14, FAIL 0 (sem regressao).
- Gauntlet rapido: 18/18 (sem regressao).
- Gauntlet proxy: 6/6 (sem regressao).
- Gauntlet robustez_boot: 5/5 (RB-06 novo PASS; RB-03/04/05 preservados).

### Cenarios runtime real (ADR-010 zero-mocks)
1. Helper unit roundtrip (Passo 9).
2. Corrupcao JSON -> .bak + count=0 (Passo 10).
3. Restart real do proxy + hidratacao do count via curl (Passo 11).

---

## 8. Proof-of-work esperado

- Diff final no commit.
- Smoke: `./run.sh --smoke` -> "boot ok".
- Invariantes: `bash scripts/sprint_invariants.sh` -> PASS 14, FAIL 0.
- Ruff: `/home/andrefarias/.local/bin/ruff check nyx/ scripts/gauntlet/nyx_gauntlet.py` -> "All checks passed.".
- Acentuacao: `python3 ~/.config/zsh/scripts/validar-acentuacao.py --paths <arquivos tocados>` -> exit 0.
- Gauntlet: rapido 18/18, proxy 6/6, robustez_boot 5/5.
- Curl real: `curl -s http://127.0.0.1:11436/admin/stats | python3 -m json.tool` -> JSON com 4 chaves + count hidratado se arquivo pre-existia.
- Helper unit: 3 cenarios runtime (Passo 9-11) PASS.
- Hipoteses verificadas: relatorio cita greps confirmados na secao 2.

---

## 9. Riscos e nao-objetivos

### Riscos identificados

- **Race condition entre 2 incrementos em quick succession:** OOM dispara `_persist_stats` 2x se cair em GPU parcial OOM tambem (cap=2 retries). `os.replace` e atomico no POSIX, ultima escrita vence. Aceitavel: contador correto, apenas ordering de last_recovery iso8601 reflete o ultimo evento.
- **Permissao negada em `~/.nyx/`:** se diretorio nao existe e nao pode ser criado (filesystem readonly?), log warning e segue. Nao bloqueia recovery.
- **Disco cheio:** mesmo tratamento — warning + continua em memoria.
- **JSON gigante por corrupcao malicia:** `read_text` carrega o arquivo todo. Mitigacao: schema valida `oom_recovery_count` ser int; se nao for, .bak + reset. Arquivo nunca crescera alem de ~200B em uso normal.

### Nao-objetivos (escopo fora desta sprint)

- Historico estruturado (lista de eventos com timestamps) -> `INFRA-OOM-HISTORY-EVENTS-02` futura se demandar.
- Sync entre multiplas instancias do proxy -> sem necessidade (single-instance via NYX_PID_FILE).
- Migracao de schema (`version` >= 2) -> registrar como sprint quando schema mudar.
- Rotacao/cleanup automatico de `.bak` -> manual via `rm`; se cresce demais, sprint nova.
- Metricas alem das 4 + first_session/last_recovery -> fora.
- Persistir num_gpu_current / num_gpu_initial -> nao faz sentido (efemero por execucao + injetado por CLI).
- CLI flag `--stats-path` no proxy -> override via env var basta (NYX_PROXY_STATS_PATH).

### Protocolo anti-debito

Se durante execucao surgir achado colateral (ex.: invariante #15 desejavel para validar formato JSON, ou bug latente em handle_chat exposto pela leitura do arquivo), **registrar sprint nova com ID `INFRA-OOM-HISTORY-FIX-NN-01` no MASTER**. Nunca absorver implicitamente no escopo desta.

---

## 10. Referencias

- BRIEF: `/home/andrefarias/Desenvolvimento/Nyx-Code/VALIDATOR_BRIEF.md` (atualizado 2026-05-20T01:17).
- MASTER linha 125cc: `dev-journey/06-sprints/SPRINT_ORDER_MASTER.md` — RASCUNHO original deste anti-debito.
- Precedente direto INFRA-OOM-02 (CONCLUIDA): `dev-journey/06-sprints/concluidos/SPRINT_INFRA_OOM_02.md` — endpoint + contador in-memory.
- Precedente direto INFRA-OOM-RETRY-STEP-01 (CONCLUIDA): `dev-journey/06-sprints/concluidos/SPRINT_INFRA_OOM_RETRY_STEP_01.md` — retry intermediario.
- Precedente direto INFRA-OOM-STATS-CLI-01 (CONCLUIDA): `dev-journey/06-sprints/concluidos/SPRINT_INFRA_OOM_STATS_CLI_01.md` — consumer slash `/stats`.
- Padrao `~/.nyx/<file>.json`: `nyx/cli_helpers.py:18` (image_index), `nyx/agent/persistence.py:19` (sessions), `nyx/agent/tools/task_manager.py:23` (tasks).
- Memorias relevantes: `feedback_smoke_boot.md`, `feedback_nenhum_debito.md`, `feedback_checkpoint_md.md`, `feedback_write_through_apagao.md`.

---

*"Persistir o contador e barato; nao persistir e perder a serie temporal que justifica investir em hardware."* — racional desta sprint.
