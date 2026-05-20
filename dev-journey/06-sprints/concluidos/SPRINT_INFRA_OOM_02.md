# SPRINT INFRA-OOM-02 — Endurecimento + observabilidade da graceful degradation OOM no proxy

## 0. SPEC (machine-readable)

```yaml
sprint:
  id: INFRA-OOM-02
  title: "Endurecer e instrumentar graceful degradation OOM existente no proxy (docstring + contador + /admin/stats)"
  onda: 24
  bloco: 24.1 Infra resiliente
  prioridade: ALTA
  tipo: Hardening+Observability
  dependencias: [INFRA-OOM-01, PROXY-NUMGPU-RUNTIME-01]
  desbloqueia: [VALIDATE-FINAL-01]

  touches:
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/proxy.py
      reason: "Docstring no bloco _OOM_DEGRADED (linhas 60-78), contador app['state']['oom_recovery_count'] em handle_chat (linhas 407-421), novo handler handle_stats + rota /admin/stats (após handle_tune, próximo de linha 786), registro de rota em main() (linha 833)"
      linhas_alvo: "60-78, 389-421, ~786 (insert), 833 (insert)"
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/scripts/gauntlet/nyx_gauntlet.py
      reason: "Adicionar check RB-04: /admin/stats responde JSON válido + contador presente após simulação de OOM (módulo-level _OOM_DEGRADED toggling). Mesmo padrão de RB-03 (linhas 4064-4099) — sem boot real, apenas import + assert"
      linhas_alvo: "após 4099 (insert)"

  creates: []
  removes: []

  n_to_n_pairs:
    - descricao: "Cada novo símbolo público em proxy.py espelha-se em assert no gauntlet (RB-04)"
      paths:
        - /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/proxy.py
        - /home/andrefarias/Desenvolvimento/Nyx-Code/scripts/gauntlet/nyx_gauntlet.py

  forbidden:
    - "Sobrescrever ou remover _OOM_DEGRADED, _OOM_PATTERNS, _is_oom_error existentes — apenas instrumentar"
    - "Quebrar fail-safe permanente (após OOM, num_gpu permanece 0 até fim da sessão; /admin/stats NÃO pode reanimar)"
    - "Adicionar rota /admin/stats sem bind loopback (ADR-001 Local First; ver _LOOPBACK_HOSTS:644 e padrão em handle_shutdown:658-674 + handle_tune:722-786)"
    - "Spawn de subprocess no caminho de handle_stats (apenas leitura de state in-memory)"
    - "Refactor amplo de handle_chat (~840L) — apenas linhas 407-421 do bloco OOM"
    - "Adicionar logging verbose no hot path; apenas info log uma vez por recovery (já existe linha 421)"

  tests:
    - cmd: "./run.sh --smoke"
      timeout: 30
      deve_passar: "boot ok"
    - cmd: "bash scripts/sprint_invariants.sh"
      timeout: 60
      deve_passar: "FAIL_AFTER <= FAIL_BEFORE (baseline 0)"
    - cmd: "./run.sh --gauntlet --only proxy"
      timeout: 300
      deve_passar: "100% (regression-free)"
    - cmd: "./run.sh --gauntlet --only rapido"
      timeout: 300
      deve_passar: "100% (regression-free; RB-04 novo PASS)"
    - cmd: "curl -s http://127.0.0.1:11436/admin/stats | python -m json.tool"
      timeout: 10
      deve_passar: "JSON válido com chaves oom_recovery_count (int), num_gpu_current (int), num_gpu_initial (int), oom_degraded (bool)"
    - cmd: "curl -sw '%{http_code}' --resolve fake.local:11436:8.8.8.8 -o /dev/null http://fake.local:11436/admin/stats || echo loopback-only-guard-ok"
      timeout: 10
      deve_passar: "403 ou erro de conexão (loopback guard ativo)"

  acceptance_criteria:
    - "Bloco linhas 60-78 de proxy.py ganha docstring em PT-BR explicando: (a) trigger via _is_oom_error contra _OOM_PATTERNS, (b) ação set state['num_gpu']=0 + _OOM_DEGRADED=True, (c) caráter permanente na sessão até restart do proxy (não reanima via /admin/tune — ver handle_tune:755-767)"
    - "handle_chat (linhas 389-421) incrementa state['oom_recovery_count'] após log 'OOM recovery OK' (linha 421). Contador é int começando em 0, inicializado em main() linha 825 ao lado de num_gpu"
    - "Novo handle_stats async def aceita GET, retorna JSON {oom_recovery_count, num_gpu_current, num_gpu_initial, oom_degraded}, rejeita 403 quando request.remote not in _LOOPBACK_HOSTS, segue mesmo padrão de handle_shutdown e handle_tune"
    - "Rota app.router.add_get('/admin/stats', handle_stats) registrada em main() após /admin/tune (linha 833)"
    - "_INITIAL_NUM_GPU continua imutável após OOM; num_gpu_initial em /admin/stats reflete snapshot inicial via args.num_gpu armazenado em main() ANTES de mutações"
    - "RB-04 no gauntlet: import nyx.proxy + assert hasattr(handle_stats) + simular toggle de _OOM_DEGRADED via setattr + assert _OOM_DEGRADED reset para próximos testes (cleanup pattern de RB-03)"
    - "Smoke ok"
    - "Invariantes 14/14"
    - "Gauntlet proxy + rapido 100% (sem regressão; RB-04 PASS novo)"
    - "Acentuação PT-BR correta nos arquivos tocados (validador ~/.config/zsh/scripts/validar-acentuacao.py)"
    - "Sem emojis em código, commit, doc"
    - "Sem menção a IA externa em .py"
```

---

**Status:** PENDENTE
**Data criação:** 2026-05-19
**Modelo obrigatório:** claude-opus-4-7 (sem subagentes; Read/Grep/Glob direto)

---

## Contexto

Sessão 2026-05-19 (logs/proxy.log) registrou disparo real do mecanismo de graceful degradation:

```
22:36:07 [proxy] ERROR: Ollama 500: {"error":"llama runner process has terminated: cudaMalloc failed: out of memory ...
22:36:07 [proxy] WARNING: OOM detectado. Degradando num_gpu=0 (CPU) para esta sessão
22:36:10 [proxy] INFO: OOM recovery OK: resposta via CPU
```

O recovery **já existe e funcionou** — está implementado em `nyx/proxy.py:handle_chat` (linhas 389-421) detectando `cudaMalloc`/`out of memory` em resposta 500 do Ollama via `_is_oom_error` (linhas 74-78) contra `_OOM_PATTERNS` (linhas 63-71), re-tentando com `num_gpu=0` e tornando a degradação permanente via flag módulo-global `_OOM_DEGRADED` (linha 62). `handle_tune` (linhas 755-767) respeita o fail-safe e não reanima GPU após degradação.

Gauntlet hoje cobre o mecanismo via RB-03 (linhas 4064-4099 de `nyx_gauntlet.py`) checando presença dos símbolos. **Não há contador, nem endpoint para inspeção de estado, nem docstring que ensine por que a degradação é permanente.** Em sessões longas com OOM múltiplo, ninguém sabe se aconteceu 1 ou 5 vezes, e por que não voltou a tentar GPU.

### Sintoma observável

`logs/proxy.log` mostra recovery — mas não há forma programática de saber:

1. Se OOM já aconteceu nesta sessão (sem grep no log).
2. Quantas vezes recovery foi acionado.
3. Qual era o `num_gpu` antes da degradação.

### Nota de ID

`INFRA-OOM-01` (entry 141 do MASTER) já foi consumida para um escopo distinto (controle OOM via `ulimit` + `oom_score_adj` + `scripts/check_oom.sh`, fora do proxy). Esta sprint é nova entidade — `INFRA-OOM-02` — focada exclusivamente no proxy.

---

## Escopo (touches autorizados)

### Arquivos a modificar

- `/home/andrefarias/Desenvolvimento/Nyx-Code/nyx/proxy.py` (atualmente 841 linhas)
  - Linhas 60-78: docstring no bloco `_OOM_DEGRADED`/`_OOM_PATTERNS`.
  - Linhas 389-421: contador `state['oom_recovery_count']` após log de recovery.
  - Inserção após linha 786: novo `handle_stats` async function.
  - Linha 825: incluir `oom_recovery_count: 0` em `app["state"]`.
  - Inserção após linha 833: registro `app.router.add_get('/admin/stats', handle_stats)`.

- `/home/andrefarias/Desenvolvimento/Nyx-Code/scripts/gauntlet/nyx_gauntlet.py`
  - Inserção após linha 4099 (após RB-03): novo check `RB-04` validando presença de `handle_stats` e contrato JSON via import módulo-level (mesmo padrão de RB-03, sem boot real).

### Arquivos NÃO a tocar

- `nyx/agent/services/logging_service.py` — proxy já usa `logger` próprio (`logging.getLogger("proxy")`), não há necessidade de nível custom.
- `nyx/cli.py` / `cli_handlers.py` — exposição CLI do `/admin/stats` fica out-of-scope desta sprint (anti-débito INFRA-OOM-STATS-CLI-01 se ressurgir).
- `nyx/config/defaults.py` — `PROXY_PORT` continua única fonte.
- Qualquer outro `nyx/**/*.py` — refatorar handle_chat ou _on_startup amplos NÃO é objetivo.

### Invariantes a preservar

Do `VALIDATOR_BRIEF.md` (CORE - Checks universais):

1. Smoke boot obrigatório antes de marcar CONCLUIDA.
2. Sem emojis em código/commit/doc.
3. Sem menção a IA externa em `.py`.
4. Acentuação PT-BR correta (validador `~/.config/zsh/scripts/validar-acentuacao.py`).
5. Cleanup explícito após teste com modelo (`pkill nyx/proxy.py`, `pkill ollama serve`, `nvidia-smi`).
6. Nenhum débito implícito.

Do código existente (acoplamentos descobertos via grep):

7. `_OOM_DEGRADED` é `global` em `handle_chat` (linha 390) — preservar referência. Não converter para `state[]` (quebraria `_is_oom_error` API atual).
8. `_LOOPBACK_HOSTS` (linha 644) é tupla módulo-level usada por `handle_shutdown` (661) e `handle_tune` (730) — `handle_stats` deve seguir mesmo padrão.
9. `app["state"]` (linha 795) substituiu mutação direta de `app[]` em runtime (deprecated em aiohttp moderno) — todos novos campos vão dentro de `state`.
10. `handle_tune` (linhas 722-786) já trata caso `_OOM_DEGRADED` preservando 0 — usar mesma lógica para validar consistência em testes.
11. RB-03 (gauntlet linhas 4064-4099) faz import módulo-level + `getattr(mod, "_is_oom_error", None)` — RB-04 deve seguir mesmo idioma (não exigir boot real do proxy).

---

## Acceptance criteria

1. Bloco `_OOM_DEGRADED` (linhas 60-78 de `nyx/proxy.py`) ganha docstring PT-BR explicando trigger, ação e permanência.
2. `handle_chat` incrementa `state["oom_recovery_count"]` após recovery OK (linha 421 atual).
3. `handle_stats` existe, decorada async, responde GET, rejeita não-loopback com 403.
4. `/admin/stats` retorna JSON `{oom_recovery_count: int, num_gpu_current: int, num_gpu_initial: int, oom_degraded: bool}`.
5. `state["oom_recovery_count"]` inicializado em 0 em `main()` (linha 825) e `_on_startup` (linha 796).
6. `num_gpu_initial` reflete `_INITIAL_NUM_GPU` ou snapshot de `args.num_gpu` antes de mutações — não muda após OOM.
7. RB-04 no gauntlet PASS validando símbolos + cleanup do `_OOM_DEGRADED` para outros testes.
8. Fail-safe preservado: após OOM, `/admin/stats` mostra `oom_degraded: true` e `num_gpu_current: 0`, mas `/admin/tune` não reanima (linha 755-767 inalterada).
9. Smoke + invariantes 14/14 + gauntlet proxy 100% + rapido 100%.
10. Validador de acentuação exit 0 nos arquivos tocados.

---

## Plano de implementação

### Passo 1 — Conferir baseline

```bash
wc -l /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/proxy.py
bash /home/andrefarias/Desenvolvimento/Nyx-Code/scripts/sprint_invariants.sh > /tmp/inv_before.txt 2>&1
tail -5 /tmp/inv_before.txt
```

Esperado: `841 nyx/proxy.py`, FAIL=0.

### Passo 2 — Docstring no bloco _OOM_DEGRADED

Em `nyx/proxy.py` linhas 60-78, transformar comentário em docstring de módulo descrevendo:

```python
# Graceful degradation: quando Ollama retorna OOM, cai pra CPU permanente
# até o fim da sessão. Evita loop de retry e mantém o serviço vivo (ADR-001).
#
# Trigger: _is_oom_error casa _OOM_PATTERNS contra texto da resposta 500
# de /api/chat do Ollama (ex.: "cudaMalloc failed", "out of memory").
#
# Ação: ao primeiro hit, handle_chat seta _OOM_DEGRADED=True (módulo-global)
# e state["num_gpu"]=0, depois re-emite a requisição com num_gpu=0 e loga
# "OOM recovery OK". Incrementa state["oom_recovery_count"] (observabilidade
# via GET /admin/stats).
#
# Permanência: a degradação é PERMANENTE até restart do proxy. handle_tune
# respeita o fail-safe e NÃO reanima GPU após OOM (ver linhas 755-767).
# Justificativa: evitar oscilação CPU<->GPU em loop quando VRAM oscila no
# limite. ADR-001 Local First prioriza serviço vivo sobre throughput.
_OOM_DEGRADED = False
```

### Passo 3 — Contador em handle_chat

Em `nyx/proxy.py` linha 421 (após `logger.info("OOM recovery OK: resposta via CPU")`), adicionar:

```python
                    state["oom_recovery_count"] = state.get("oom_recovery_count", 0) + 1
```

Notar: usar `.get(..., 0)` por defensividade (sprint considera que `state` pode estar pré-startup em edge cases).

### Passo 4 — Inicializar contador em main() e _on_startup

Em `main()` linha 825:

```python
    app["state"] = {
        "num_gpu": args.num_gpu,
        "num_gpu_initial": args.num_gpu,  # snapshot imutável
        "oom_recovery_count": 0,
    }
```

Em `_on_startup` linha 795-797, garantir defaults:

```python
    state = app.setdefault("state", {})
    state.setdefault("num_gpu", _INITIAL_NUM_GPU)
    state.setdefault("num_gpu_initial", state["num_gpu"])
    state.setdefault("oom_recovery_count", 0)
```

### Passo 5 — handle_stats

Inserir após `handle_tune` (após linha 786), antes de `_on_startup`:

```python
async def handle_stats(request: web.Request) -> web.Response:
    """Retorna snapshot de estado do proxy (loopback-only).

    JSON: {oom_recovery_count, num_gpu_current, num_gpu_initial, oom_degraded}.
    Leitura pura; não muta estado. Útil para diagnosticar sessões longas
    sem grep no log (ver INFRA-OOM-02).
    """
    remote = request.remote or ""
    if remote not in _LOOPBACK_HOSTS:
        logger.warning("stats rejeitado: remote=%s não-loopback", remote)
        return web.json_response({"error": "loopback only"}, status=403)

    state = request.app["state"]
    return web.json_response(
        {
            "oom_recovery_count": state.get("oom_recovery_count", 0),
            "num_gpu_current": state.get("num_gpu", 0),
            "num_gpu_initial": state.get("num_gpu_initial", state.get("num_gpu", 0)),
            "oom_degraded": _OOM_DEGRADED,
        }
    )
```

### Passo 6 — Registro de rota

Em `main()` após linha 833 (`app.router.add_get("/admin/tune", handle_tune)`):

```python
    app.router.add_get("/admin/stats", handle_stats)
```

### Passo 7 — Check RB-04 no gauntlet

Em `scripts/gauntlet/nyx_gauntlet.py` após linha 4099 (após bloco RB-03), inserir RB-04 seguindo o mesmo idioma:

```python
        # RB-04: handle_stats existe e contrato JSON via state in-memory (INFRA-OOM-02)
        t = time.monotonic()
        try:
            import importlib as _imp

            mod = _imp.import_module("nyx.proxy")
            tem_handler = hasattr(mod, "handle_stats")
            src = proxy_py.read_text(encoding="utf-8")
            tem_rota = 'add_get("/admin/stats"' in src
            tem_contador = 'oom_recovery_count' in src
            tem_initial = 'num_gpu_initial' in src
            tem_loopback_guard = src.count("_LOOPBACK_HOSTS") >= 4  # handle_shutdown, handle_tune, handle_stats, def
            ok = bool(tem_handler and tem_rota and tem_contador and tem_initial and tem_loopback_guard)
            self._add(
                "RB-04",
                "Proxy expõe /admin/stats com contador OOM (INFRA-OOM-02)",
                "robustez_boot",
                ok,
                time.monotonic() - t,
                details=f"handler={tem_handler} rota={tem_rota} contador={tem_contador} initial={tem_initial} loopback={tem_loopback_guard}",
            )
        except Exception as e:
            self._add(
                "RB-04",
                "Proxy expõe /admin/stats com contador OOM (INFRA-OOM-02)",
                "robustez_boot",
                False,
                time.monotonic() - t,
                error=str(e),
            )
```

### Passo 8 — Validação runtime real

```bash
# Smoke
./run.sh --smoke

# Boot proxy em background isolado
./run.sh --headless &
PID=$!
sleep 5

# Stats inicial — sem OOM
curl -s http://127.0.0.1:11436/admin/stats | python -m json.tool
# Esperado: oom_recovery_count=0, oom_degraded=false, num_gpu_initial==num_gpu_current

# Loopback guard (deve retornar 403 ou conexão recusada)
curl -sw '%{http_code}\n' -o /tmp/stats_remote.json http://192.168.1.100:11436/admin/stats 2>&1 | tail -3

# Cleanup
kill $PID
pkill -f "nyx/proxy.py" 2>/dev/null
pkill -f "ollama serve" 2>/dev/null
nvidia-smi | head -10

# Invariantes
bash scripts/sprint_invariants.sh > /tmp/inv_after.txt 2>&1
diff /tmp/inv_before.txt /tmp/inv_after.txt
tail -5 /tmp/inv_after.txt

# Gauntlet
./run.sh --gauntlet --only proxy
./run.sh --gauntlet --only rapido
```

Esperado: smoke OK, stats JSON válido, loopback guard rejeita, invariantes 14/14, RB-04 PASS, sem regressão.

### Passo 9 — Validador de acentuação

```bash
~/.config/zsh/scripts/validar-acentuacao.py /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/proxy.py /home/andrefarias/Desenvolvimento/Nyx-Code/scripts/gauntlet/nyx_gauntlet.py
```

Esperado: exit 0.

### Passo 10 — Commit

```
feat(INFRA-OOM-02): endurece graceful degradation OOM no proxy (docstring + contador + /admin/stats)
```

---

## Aritmética

Sprint expande funcionalidade (observabilidade); não tem meta numérica de redução.

- `nyx/proxy.py` atual: 841 linhas.
- Adições previstas:
  - Docstring expandida no bloco `_OOM_DEGRADED`: ~13L (substitui 4L de comentário existente; delta +9L).
  - Incremento de contador em `handle_chat`: 1L.
  - `app["state"]` em `main()` expandido de 1L para 5L (delta +4L).
  - `state.setdefault` em `_on_startup`: 2L adicionais (delta +2L).
  - `handle_stats` completa: ~20L.
  - Registro de rota em `main()`: 1L.
- Delta esperado: ~37L. Projetado: ~878 linhas. Sem teto crítico (limite de aviso interno: 1000L; ainda confortável).

- `scripts/gauntlet/nyx_gauntlet.py` atual: maior que 4099 linhas. Adição: ~28L para RB-04. Sem teto.

---

## Testes

### Baseline a coletar antes de iniciar

```bash
wc -l nyx/proxy.py
bash scripts/sprint_invariants.sh | tail -5    # FAIL_BEFORE = 0 (baseline)
./run.sh --gauntlet --only proxy 2>&1 | tail -10  # contagem PASS proxy
./run.sh --gauntlet --only rapido 2>&1 | tail -10  # contagem PASS rapido
```

### Esperado após implementação

- `FAIL_AFTER` == `FAIL_BEFORE` (0).
- Gauntlet proxy: passes ≥ baseline (idealmente +0; sprint não modifica testes proxy/*).
- Gauntlet rapido: passes ≥ baseline + 1 (RB-04 novo PASS adicionado a `robustez_boot`).

---

## Proof-of-work esperado

- **Diff final**: git diff cobrindo `nyx/proxy.py` + `scripts/gauntlet/nyx_gauntlet.py`.
- **Runtime real** (do `VALIDATOR_BRIEF.md` CORE):
  - `./run.sh --smoke` → boot ok.
  - `bash scripts/sprint_invariants.sh` → PASS 14, FAIL 0.
  - `./run.sh --gauntlet --only proxy` → 100%.
  - `./run.sh --gauntlet --only rapido` → 100% (RB-04 incluído).
- **Endpoint live**:
  - `curl -s http://127.0.0.1:11436/admin/stats | python -m json.tool` → JSON com 4 chaves esperadas.
  - `curl -sw '%{http_code}' http://<não-loopback>:11436/admin/stats` → 403.
- **Acentuação periférica**: `~/.config/zsh/scripts/validar-acentuacao.py` em `nyx/proxy.py` + `scripts/gauntlet/nyx_gauntlet.py` → exit 0.
- **Hipótese verificada via rg**: confirmar pré-implementação que `_OOM_DEGRADED`, `_OOM_PATTERNS`, `_is_oom_error`, `_LOOPBACK_HOSTS`, `handle_tune`, `handle_chat`, `_on_startup`, `_INITIAL_NUM_GPU` existem no proxy (já confirmados via grep do planejador).
- **Cleanup pós-teste**: `pkill -f "nyx/proxy.py"`, `pkill -f "ollama serve"`, `nvidia-smi` confirmando VRAM livre.

---

## Riscos e mitigações

| Risco | Mitigação |
|---|---|
| Refactor de handle_chat (840L) introduz regressão | Edição cirúrgica: apenas 1L adicionada após linha 421. Diff revisável. |
| Contador conflita com `_OOM_DEGRADED` global | Contador vive em `state[]` (per-app), flag continua módulo-global. Sem acoplamento direto. |
| RB-04 quebra outros checks do gauntlet por mutar `_OOM_DEGRADED` | RB-04 NÃO toggla flag em runtime (apenas leitura via `hasattr` + source grep). Padrão idêntico ao RB-03. |
| `/admin/stats` expõe estado sensível em portas abertas | Loopback guard via `_LOOPBACK_HOSTS` (padrão estabelecido por handle_shutdown e handle_tune). |
| OPCIONAL retry intermediário (12→6→0) complicar a sprint | OUT-OF-SCOPE explícito (ver abaixo). Cria sprint anti-débito se ressurgir. |

---

## Out-of-scope (anti-débito)

Se durante execução surgir qualquer um destes, registrar como sprint nova:

1. **Retry intermediário num_gpu // 2 (12→6→0)** → `INFRA-OOM-RETRY-STEP-01` (MÉDIA). Modificar handle_chat para tentar 2 camadas antes de 0.
2. **Exposição CLI de /admin/stats** → `INFRA-OOM-STATS-CLI-01` (BAIXA). Slash `/stats` em `nyx/agent/commands/system.py` consumindo o endpoint.
3. **Persistência de oom_recovery_count entre sessões** → `INFRA-OOM-HISTORY-01` (BAIXA). Append em `~/.nyx/oom_history.jsonl`.
4. **Tunagem dinâmica baseada em prediction de VRAM** → `PROXY-VRAM-PREDICT-01` (BAIXA, hipotética). Mencionada no enunciado original; fora dessa sprint.
5. **Refactor de handle_chat para extrair bloco OOM como função** → `PROXY-OOM-EXTRACT-01` (BAIXA). Sprint cirúrgica de refactor sem mudança comportamental.
6. **Suporte a novos modelos / mudança de behavior user-facing** → fora desta sprint (proibido por enunciado).

---

## Referências

- VALIDATOR_BRIEF: `/home/andrefarias/Desenvolvimento/Nyx-Code/VALIDATOR_BRIEF.md`
- ADR-001 Local First (referenciado em proxy.py linha 61 e PROXY-NUMGPU-RUNTIME-01)
- ADR-003 VRAM Management (referenciado no enunciado)
- Sprint precedente: `dev-journey/06-sprints/concluidos/SPRINT_PROXY_NUMGPU_RUNTIME_01.md` — estabeleceu `app["state"]`, `handle_tune`, `_LOOPBACK_HOSTS` reutilizados aqui.
- Sprint precedente: `dev-journey/06-sprints/concluidos/SPRINT_INFRA_OOM_01.md` — controle OOM via ulimit/oom_score_adj (escopo distinto, complementar).
- Gauntlet RB-03 (referência de idioma): `scripts/gauntlet/nyx_gauntlet.py` linhas 4064-4099.

---

*"Recovery sem contador é folclore. Contador sem endpoint é dado morto. /admin/stats fecha o ciclo." — INFRA-OOM-02*
