# SPRINT INFRA-OOM-RETRY-STEP-01 — Retry intermediário num_gpu // 2 antes de cair para 0 no graceful degradation OOM

## 0. SPEC (machine-readable)

```yaml
sprint:
  id: INFRA-OOM-RETRY-STEP-01
  title: "Retry intermediario num_gpu // 2 antes de cair direto para num_gpu=0 no graceful degradation do proxy (cap 2 retries total)"
  onda: 24
  bloco: 24.1 Infra resiliente
  prioridade: BAIXA
  tipo: Hardening+Resilience
  dependencias: [INFRA-OOM-02]
  desbloqueia: []

  touches:
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/proxy.py
      reason: "Helper modulo-level _next_num_gpu_step + reestrutura do bloco OOM em handle_chat (linhas 421-441) para tentar passo intermediario antes de num_gpu=0. Novo log 'OOM degradation step: N -> M'. Cap 2 retries total."
      linhas_alvo: "apos linha 92 (helper); 421-441 (bloco OOM em handle_chat)"
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/scripts/gauntlet/nyx_gauntlet.py
      reason: "Novo check RB-05 fase robustez_boot validando presenca de _next_num_gpu_step, log 'OOM degradation step', e cap 2 retries via grep no source. Mesmo idioma de RB-03/RB-04."
      linhas_alvo: "apos linha 4152 (apos RB-04 atual)"

  creates: []
  removes: []

  n_to_n_pairs:
    - descricao: "Cada novo simbolo publico em proxy.py espelha-se em assert no gauntlet (RB-05)"
      paths:
        - /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/proxy.py
        - /home/andrefarias/Desenvolvimento/Nyx-Code/scripts/gauntlet/nyx_gauntlet.py

  forbidden:
    - "Quebrar fail-safe permanente: apos 2o retry com num_gpu=0 falhar, retornar 500 ao cliente, NAO entrar em loop"
    - "Mexer em _OOM_DEGRADED (continua module-global, setado True no primeiro hit OOM)"
    - "Adicionar caminho de OOM em outras rotas /api/* (so handle_chat onde tool calling acontece)"
    - "Tornar passo intermediario configuravel (always // 2, sem env var)"
    - "Persistir step entre OOMs entre sessoes (state in-memory ja basta; persistencia e INFRA-OOM-HISTORY-01)"
    - "Algoritmo adaptativo baseado em historico de VRAM (out-of-scope, hipotetico)"
    - "Mock httpx (gauntlet declara 'Zero mocks. 100% real.' linha 2 do nyx_gauntlet.py)"
    - "Refactor amplo de handle_chat (~840L de proxy.py) — apenas linhas 421-441 do bloco OOM"

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
      deve_passar: "100% (regression-free; rapido = {infra,proxy,visual,config}, RB-05 nao aparece aqui)"
    - cmd: "./run.sh --gauntlet --only robustez_boot"
      timeout: 300
      deve_passar: "100% (RB-05 novo PASS; RB-01..RB-04 mantidos)"
    - cmd: "curl -s http://127.0.0.1:11436/admin/stats | python -m json.tool"
      timeout: 10
      deve_passar: "JSON valido (sem regressao no contrato de INFRA-OOM-02)"
    - cmd: "./venv/bin/python -c 'from nyx.proxy import _next_num_gpu_step; assert _next_num_gpu_step(15) == 7; assert _next_num_gpu_step(12) == 6; assert _next_num_gpu_step(2) == 1; assert _next_num_gpu_step(1) == 0; assert _next_num_gpu_step(0) == 0; print(\"helper ok\")'"
      timeout: 10
      deve_passar: "imprime 'helper ok' (contrato do helper preservado)"
    - cmd: "./venv/bin/python -m ruff check nyx/proxy.py scripts/gauntlet/nyx_gauntlet.py"
      timeout: 30
      deve_passar: "All checks passed"
    - cmd: "~/.config/zsh/scripts/validar-acentuacao.py nyx/proxy.py scripts/gauntlet/nyx_gauntlet.py"
      timeout: 10
      deve_passar: "exit 0"

  acceptance_criteria:
    - "Helper _next_num_gpu_step(current: int) -> int adicionado em proxy.py modulo-level apos _is_oom_error (apos linha 92); contrato: current > 1 retorna current // 2; current <= 1 retorna 0; current <= 0 retorna 0 (defensivo)"
    - "handle_chat bloco OOM (linhas 421-441) reestruturado: ao detectar _is_oom_error E nao _OOM_DEGRADED, calcular intermediate = _next_num_gpu_step(num_gpu); se intermediate > 0, primeiro retry com num_gpu=intermediate; se intermediate <= 0 OU se 1o retry tambem retornar OOM, fallback para num_gpu=0 (2o retry); se 2o retry falhar, retornar 500 ao cliente"
    - "Log novo 'OOM degradation step: %d -> %d' emitido com (num_gpu_atual, intermediate) ANTES do 1o retry (apenas quando intermediate > 0)"
    - "_OOM_DEGRADED so eh setado True quando state['num_gpu'] efetivamente vai para 0 (fim da cadeia de degradacao, nao no passo intermediario)"
    - "state['oom_recovery_count'] incrementa +1 por OOM event (nao +1 por retry individual); aumenta apenas uma vez na cadeia toda, apos sucesso final"
    - "state['num_gpu'] reflete o nivel atual ao final do recovery: intermediate (se 1o retry deu OK) ou 0 (se caiu para CPU)"
    - "Cap 2 retries total estritamente respeitado: 1o retry intermediario + 2o retry CPU; sem 3o retry; se 2o retry falhar, return 500 ao cliente com mensagem clara"
    - "RB-05 no gauntlet (fase robustez_boot, apos RB-04): grep no source confirma _next_num_gpu_step definido + log 'OOM degradation step' presente + cap de 2 retries (count de 'session.post' no bloco OOM em handle_chat <= 3, sendo 1 inicial + 2 retries); helper importavel via importlib + assert contrato (_next_num_gpu_step(15)==7, _next_num_gpu_step(2)==1, _next_num_gpu_step(1)==0, _next_num_gpu_step(0)==0)"
    - "Contrato de /admin/stats (INFRA-OOM-02) preservado: JSON segue com oom_recovery_count, num_gpu_current, num_gpu_initial, oom_degraded; num_gpu_current reflete o valor degradado (intermediate ou 0); num_gpu_initial continua imutavel"
    - "RB-03 e RB-04 mantem PASS sem alteracao (regression-free)"
    - "Smoke ok"
    - "Invariantes 14/14"
    - "Gauntlet proxy + rapido + robustez_boot 100% (RB-05 PASS novo, RB-04 PASS, RB-03 PASS)"
    - "Helper passa no contrato unitario via python -c (ver tests)"
    - "Acentuacao PT-BR correta (validador ~/.config/zsh/scripts/validar-acentuacao.py exit 0)"
    - "Ruff All checks passed"
    - "Sem emojis em codigo, commit, doc"
    - "Sem mencao a IA externa em .py"
```

---

**Status:** RASCUNHO (este spec promove de RASCUNHO para PRONTO_PARA_EXECUTAR após validação humana; entrada 125aa no MASTER)
**Data criação:** 2026-05-20
**Modelo obrigatório:** claude-opus-4-7 (sem subagentes; Read/Grep/Glob direto)

---

## Contexto

INFRA-OOM-02 (linha 125y do MASTER, concluída em 2026-05-20) endureceu a graceful degradation OOM existente em `nyx/proxy.py:handle_chat` com docstring + contador `state["oom_recovery_count"]` + endpoint `/admin/stats`. O comportamento atual ao detectar OOM em resposta 500 do Ollama é **degradar direto para `num_gpu=0` (CPU permanente)** sem tentar passos intermediários.

Esta sprint adiciona um **passo intermediário `num_gpu // 2`** antes do fallback final para CPU, reduzindo downgrade abrupto quando VRAM oscila no limite. Justificativa concreta: o modelo padrão `qwen2.5-coder:3b` tem 35 layers; se VRAM tight não permite rodar 15 layers na GPU, rodar 7 ainda pode ser mais rápido que CPU pura (split GPU/CPU).

### Sequência proposta

Sessão inicial com `num_gpu=15` recebe OOM:

1. Detecta `_is_oom_error(text)` em resposta 500 → calcula `intermediate = _next_num_gpu_step(15) = 7`.
2. Log: `"OOM degradation step: 15 -> 7"`.
3. Re-tenta request com `num_gpu=7`.
4. **Se 1o retry OK**: log `"OOM recovery OK"`, `state["num_gpu"]=7`, incrementa `oom_recovery_count`, **mantém `_OOM_DEGRADED=False`** (GPU parcial ainda funciona).
5. **Se 1o retry tambem retornar OOM**: log `"OOM no passo intermediario; degradando para CPU"`, re-tenta com `num_gpu=0` (2o retry), seta `_OOM_DEGRADED=True`, `state["num_gpu"]=0`.
6. **Se 2o retry falhar**: retorna 500 ao cliente com mensagem clara, sem 3o retry.

### Sintoma resolvido

Hoje, OOM em VRAM oscilante força `num_gpu=0` sem chance de operar parcialmente. Sessões longas com hardware limítrofe sofrem throughput de CPU mesmo quando metade da GPU caberia. A degradação fica mais "gradiente" e menos "binária".

### Por que mexer

- VRAM ambiente pode liberar 50% entre requests (browser fecha tab, GPU compartilhada com outras apps).
- Custo de implementação baixo (~25-35L) com cap rígido de 2 retries.
- Anti-débito explícito do INFRA-OOM-02 (linha 433 do spec arquivado), entrada 125aa do MASTER.

---

## Escopo (touches autorizados)

### Arquivos a modificar

- `/home/andrefarias/Desenvolvimento/Nyx-Code/nyx/proxy.py` (atualmente 886 linhas, confirmado via `wc -l`)
  - **Após linha 92** (após `_is_oom_error`): inserir helper `_next_num_gpu_step(current: int) -> int` (~6-8L).
  - **Linhas 421-441** (bloco OOM em `handle_chat`): reestruturar de 1-retry-direto para até 2-retries-em-cadeia (~15-25L delta líquido).

- `/home/andrefarias/Desenvolvimento/Nyx-Code/scripts/gauntlet/nyx_gauntlet.py` (atualmente >4611L)
  - **Após linha 4152** (após bloco RB-04): inserir RB-05 (~30-35L) seguindo idioma de RB-03/RB-04 (import módulo-level + grep no source + assert contrato via `_next_num_gpu_step`).

### Arquivos a criar

Nenhum.

### Arquivos NÃO a tocar

Do `VALIDATOR_BRIEF.md` (CORE - Checks universais ativados) e padrão do INFRA-OOM-02:

- `nyx/agent/commands/stats.py` — `/stats` CLI consome `/admin/stats` (INFRA-OOM-STATS-CLI-01); contrato JSON preservado por esta sprint; não tocar.
- `nyx/config/defaults.py` — `_DEFAULT_NUM_GPU` continua única fonte para `_INITIAL_NUM_GPU`.
- `nyx/agent/services/logging_service.py` — proxy usa `logger = logging.getLogger("proxy")` próprio, não há nível custom.
- Qualquer outro `nyx/**/*.py` — refactor amplo de `handle_chat` ou outras rotas NÃO é objetivo.
- Outras rotas `/api/*` no proxy — só `handle_chat` (rota `/v1/chat/completions`) detecta e degrada OOM hoje; não introduzir caminho de degradação em `/v1/models`, `/health`, `/admin/*`.

### Invariantes a preservar

Do `VALIDATOR_BRIEF.md` (CORE - Checks universais):

1. Smoke boot obrigatório antes de marcar CONCLUIDA.
2. Sem emojis em código/commit/doc.
3. Sem menção a IA externa em `.py`.
4. Acentuação PT-BR correta (validador `~/.config/zsh/scripts/validar-acentuacao.py`).
5. Cleanup explícito após teste com modelo (`pkill nyx/proxy.py`, `pkill ollama serve`, `nvidia-smi`).
6. Nenhum débito implícito — achado colateral vira sprint nova.

Do código existente (acoplamentos descobertos via grep):

7. **`_OOM_DEGRADED` é módulo-global em `handle_chat`** (linha 404 atual: `global _OOM_DEGRADED`) — preservar referência. Não converter para `state[]` (quebraria docstring linhas 60-76 + `handle_tune` linhas 763, 770).
8. **`handle_tune` linha 770 lê `_OOM_DEGRADED` para fail-safe**: tune não reanima GPU após OOM. Esta sprint **só** deve setar `_OOM_DEGRADED=True` quando `num_gpu` efetivamente vai para 0 (fim da cadeia), **não** no passo intermediário. Caso contrário, `handle_tune` ficaria capado em 0 mesmo quando GPU parcial ainda funciona.
9. **`state["oom_recovery_count"]` é incrementado uma vez por OOM event** (não por retry individual). Esta sprint preserva a semântica: incrementar +1 apenas após sucesso final do recovery (não +1 no intermediário + outro +1 no fallback CPU).
10. **`state["num_gpu_initial"]` continua imutável** após OOM (snapshot de `args.num_gpu` em `main()` linha 867). `/admin/stats` JSON contract preserved (INFRA-OOM-02 acceptance #4).
11. **Cap de 2 retries é estrito**: 1 request inicial + 1 retry intermediário + 1 retry CPU = 3 chamadas máximas a `session.post`. Sem 3o retry, sem loop adaptativo.
12. **Política gauntlet "Zero mocks. 100% real."** (linha 2 do `nyx_gauntlet.py`) — RB-05 NÃO pode usar mock httpx. Padrão obrigatório: grep no source + importlib + assert helper unit (mesmo idioma RB-03/RB-04 atuais).
13. **`_is_oom_error` e `_OOM_PATTERNS` inalterados** — esta sprint não altera como OOM é detectado, só como é tratado.
14. **Rota `/admin/stats` registrada em `main()` linha 878** — preservar; contrato JSON inalterado.

---

## Acceptance criteria

1. Helper `_next_num_gpu_step(current: int) -> int` definido em `proxy.py` módulo-level após `_is_oom_error` (após linha 92). Contrato:
   - `current > 1` → retorna `current // 2`
   - `current == 1` → retorna `0` (não pode dividir mais)
   - `current <= 0` → retorna `0` (defensivo)

2. `handle_chat` bloco OOM (linhas 421-441 atuais) reestruturado em cadeia de até 2 retries:
   - Detecta `_is_oom_error(text)` e `not _OOM_DEGRADED` (mantém guard).
   - Calcula `intermediate = _next_num_gpu_step(num_gpu)`.
   - Se `intermediate > 0`:
     - Log: `"OOM degradation step: %d -> %d"` com `(num_gpu, intermediate)`.
     - `state["num_gpu"] = intermediate`, `ollama_body["options"]["num_gpu"] = intermediate`.
     - 1o retry: re-emite request.
     - Se 1o retry OK (status 200): `data = await resp.json()`, log `"OOM recovery OK: resposta via GPU parcial"`, incrementa `oom_recovery_count`, **NÃO seta `_OOM_DEGRADED`**.
     - Se 1o retry retorna 500 com `_is_oom_error(retry_text)`: cai para fallback CPU (próximo passo).
     - Se 1o retry falha por outro motivo (não-OOM 500): retorna 500 ao cliente (sem fallback CPU; é erro distinto).
   - Fallback CPU (acionado quando `intermediate <= 0` OU quando 1o retry também retornou OOM):
     - `_OOM_DEGRADED = True`, `state["num_gpu"] = 0`, `ollama_body["options"]["num_gpu"] = 0`.
     - Log: `"OOM detectado. Degradando num_gpu=0 (CPU) para esta sessao"` (preservado).
     - 2o retry: re-emite request com `num_gpu=0`.
     - Se 2o retry OK: log `"OOM recovery OK: resposta via CPU"`, incrementa `oom_recovery_count`.
     - Se 2o retry falha: retorna 500 ao cliente com mensagem do Ollama (sem 3o retry).

3. Log novo `"OOM degradation step: %d -> %d"` emitido apenas quando `intermediate > 0` (não duplicado para CPU direto). Caminho CPU direto preserva log existente `"OOM detectado. Degradando num_gpu=0..."`.

4. `_OOM_DEGRADED` setado `True` **apenas no fallback CPU**, não no intermediário. Razão: handle_tune linha 770 deve permitir tune quando GPU parcial ainda funciona.

5. `state["oom_recovery_count"]` incrementa +1 por OOM event:
   - Recovery via intermediário OK: +1.
   - Recovery via fallback CPU (após intermediário falhar OU intermediário <= 0): +1.
   - Cadeia não pode contar +2 quando passa por intermediário e CPU (apenas o sucesso final conta).

6. `state["num_gpu"]` reflete nível atual ao final:
   - Intermediário OK: `state["num_gpu"] = intermediate` (ex.: 7).
   - CPU OK: `state["num_gpu"] = 0`.
   - 2o retry falhou: `state["num_gpu"] = 0` (já setado), retorna 500 mas mantém `_OOM_DEGRADED=True`.

7. Cap de 2 retries estrito. Implementação não pode introduzir loop while/for sobre retries. Sequência é linear e finita.

8. RB-05 no gauntlet PASS:
   - `hasattr(mod, "_next_num_gpu_step")`.
   - `_next_num_gpu_step(15) == 7`, `_next_num_gpu_step(12) == 6`, `_next_num_gpu_step(2) == 1`, `_next_num_gpu_step(1) == 0`, `_next_num_gpu_step(0) == 0`.
   - `"OOM degradation step" in src`.
   - Bloco OOM em `handle_chat` (entre `if _is_oom_error(text)` linha 421 e o `else` de handle_chat) tem no máximo **3 chamadas** a `session.post` (1 inicial + 2 retries).
   - RB-03 e RB-04 continuam PASS sem alteração.

9. `./venv/bin/python -c 'from nyx.proxy import _next_num_gpu_step; ...'` retorna `"helper ok"` (contrato unit teste no command line, fora do gauntlet).

10. Smoke + invariantes 14/14 + gauntlet proxy 100% + rapido 100% + robustez_boot 100% (RB-05 PASS novo).

11. Validador de acentuação `exit 0` em `nyx/proxy.py` e `scripts/gauntlet/nyx_gauntlet.py`.

12. `ruff check nyx/proxy.py scripts/gauntlet/nyx_gauntlet.py` → `All checks passed`.

---

## Plano de implementação

### Passo 1 — Conferir baseline

```bash
wc -l /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/proxy.py
# Esperado: 886

wc -l /home/andrefarias/Desenvolvimento/Nyx-Code/scripts/gauntlet/nyx_gauntlet.py
# Esperado: >=4611

bash /home/andrefarias/Desenvolvimento/Nyx-Code/scripts/sprint_invariants.sh > /tmp/inv_before.txt 2>&1
tail -5 /tmp/inv_before.txt
# Esperado: PASS 14, FAIL 0

./run.sh --gauntlet --only robustez_boot 2>&1 | tail -10 > /tmp/rb_before.txt
# Anota baseline: RB-01..RB-04 todos PASS (4 checks). Após sprint: 5 checks, RB-05 novo.
```

### Passo 2 — Helper `_next_num_gpu_step` em proxy.py

Em `nyx/proxy.py` após linha 92 (final de `_is_oom_error`), inserir:

```python
def _next_num_gpu_step(current: int) -> int:
    """Calcula proximo passo de degradacao OOM: current // 2 ou 0.

    Sequencia esperada (INFRA-OOM-RETRY-STEP-01): 15 -> 7 -> 0.
    Quando current <= 1, retorna 0 (fim da cadeia, fallback CPU).
    Quando current <= 0, retorna 0 (defensivo; nao chamado em runtime).
    """
    if current <= 1:
        return 0
    return current // 2
```

Posicionamento: após `_is_oom_error` (linha 92), antes de `_normalize_content` (linha 95). Mantém agrupamento de helpers OOM/runtime no topo do módulo.

### Passo 3 — Reestruturar bloco OOM em handle_chat

Em `nyx/proxy.py` linhas 421-441 (bloco OOM atual), substituir por estrutura em cadeia.

**Antes** (estrutura atual):

```python
if _is_oom_error(text) and not _OOM_DEGRADED:
    _OOM_DEGRADED = True
    state["num_gpu"] = 0
    logger.warning("OOM detectado. Degradando num_gpu=0 (CPU) para esta sessao")
    ollama_body["options"]["num_gpu"] = 0
    async with session.post(f"{OLLAMA_URL}/api/chat", json=ollama_body) as retry_resp:
        if retry_resp.status != 200:
            retry_text = await retry_resp.text()
            logger.error("Retry CPU falhou: %d %s", retry_resp.status, retry_text[:200])
            return web.json_response(
                {"error": {"message": retry_text, "type": "api_error"}},
                status=retry_resp.status,
            )
        data = await retry_resp.json()
        logger.info("OOM recovery OK: resposta via CPU")
        state["oom_recovery_count"] = state.get("oom_recovery_count", 0) + 1
else:
    return web.json_response(...)
```

**Depois** (cadeia até 2 retries):

```python
if _is_oom_error(text) and not _OOM_DEGRADED:
    intermediate = _next_num_gpu_step(num_gpu)
    recovered = False  # marca se algum retry teve sucesso

    # 1o retry: passo intermediario (GPU parcial), apenas se intermediate > 0
    if intermediate > 0:
        logger.warning("OOM degradation step: %d -> %d", num_gpu, intermediate)
        state["num_gpu"] = intermediate
        ollama_body["options"]["num_gpu"] = intermediate
        async with session.post(f"{OLLAMA_URL}/api/chat", json=ollama_body) as inter_resp:
            if inter_resp.status == 200:
                data = await inter_resp.json()
                logger.info("OOM recovery OK: resposta via GPU parcial (num_gpu=%d)", intermediate)
                state["oom_recovery_count"] = state.get("oom_recovery_count", 0) + 1
                recovered = True
            else:
                inter_text = await inter_resp.text()
                if not _is_oom_error(inter_text):
                    # Falha nao-OOM no retry intermediario: nao tenta CPU, retorna erro
                    logger.error("Retry intermediario falhou (nao-OOM): %d %s", inter_resp.status, inter_text[:200])
                    return web.json_response(
                        {"error": {"message": inter_text, "type": "api_error"}},
                        status=inter_resp.status,
                    )
                # OOM tambem no intermediario: cai para fallback CPU abaixo

    # 2o retry: fallback CPU (acionado se intermediate <= 0 OU se 1o retry tambem deu OOM)
    if not recovered:
        _OOM_DEGRADED = True
        state["num_gpu"] = 0
        logger.warning("OOM detectado. Degradando num_gpu=0 (CPU) para esta sessao")
        ollama_body["options"]["num_gpu"] = 0
        async with session.post(f"{OLLAMA_URL}/api/chat", json=ollama_body) as retry_resp:
            if retry_resp.status != 200:
                retry_text = await retry_resp.text()
                logger.error("Retry CPU falhou: %d %s", retry_resp.status, retry_text[:200])
                return web.json_response(
                    {"error": {"message": retry_text, "type": "api_error"}},
                    status=retry_resp.status,
                )
            data = await retry_resp.json()
            logger.info("OOM recovery OK: resposta via CPU")
            state["oom_recovery_count"] = state.get("oom_recovery_count", 0) + 1
else:
    return web.json_response(
        {"error": {"message": text, "type": "api_error"}},
        status=ollama_resp.status,
    )
```

Pontos de atenção:

- `data` precisa estar definido para o fluxo continuar (linhas 445+ chamam `data.get(...)`). Em ambos caminhos de sucesso, `data` é setado.
- Se intermediate retornou OK, `_OOM_DEGRADED` permanece `False`. Próximo OOM ainda entra no `if` e pode tentar intermediate novamente (ex.: 7 → 3 → 0). Comportamento aceitável (a sequência continua descendo até CPU em sessões hostis).
- Cap de 2 retries: contar `session.post` no bloco — 1 (intermediário, condicional) + 1 (CPU, condicional) ≤ 2 retries dentro do branch OOM. Mais o `session.post` inicial fora do branch (linha 416) = 3 totais no pior caso.

### Passo 4 — Atualizar docstring do bloco _OOM_DEGRADED

Em `nyx/proxy.py` linhas 60-76, atualizar comentário-cabeçalho para refletir o passo intermediário. Substituir linhas 66-69:

**Antes** (linhas 66-69 atuais):

```
# Acao: ao primeiro hit, handle_chat seta _OOM_DEGRADED=True (modulo-global)
# e state["num_gpu"]=0, depois re-emite a requisicao com num_gpu=0 e loga
# "OOM recovery OK". Incrementa state["oom_recovery_count"] (observabilidade
# via GET /admin/stats — INFRA-OOM-02).
```

**Depois**:

```
# Acao: ao primeiro hit, handle_chat tenta passo intermediario num_gpu // 2
# antes do fallback CPU (INFRA-OOM-RETRY-STEP-01). Sequencia: 15 -> 7 -> 0.
# Se intermediario (GPU parcial) tambem retornar OOM, cai para num_gpu=0
# e seta _OOM_DEGRADED=True. Cap de 2 retries total (sem loop).
# Incrementa state["oom_recovery_count"] uma vez por OOM event (nao por retry).
# Observabilidade via GET /admin/stats (INFRA-OOM-02).
```

### Passo 5 — Adicionar RB-05 no gauntlet

Em `scripts/gauntlet/nyx_gauntlet.py` após linha 4152 (após bloco `RB-04`), inserir:

```python
        # RB-05: handle_chat tem retry intermediario num_gpu // 2 antes de CPU (INFRA-OOM-RETRY-STEP-01)
        t = time.monotonic()
        try:
            import importlib as _imp

            mod = _imp.import_module("nyx.proxy")
            tem_helper = hasattr(mod, "_next_num_gpu_step")
            helper_ok = False
            if tem_helper:
                step = mod._next_num_gpu_step
                helper_ok = (
                    step(15) == 7
                    and step(12) == 6
                    and step(2) == 1
                    and step(1) == 0
                    and step(0) == 0
                )
            src = proxy_py.read_text(encoding="utf-8")
            tem_log_step = "OOM degradation step" in src
            tem_chain = "GPU parcial" in src and "Degradando num_gpu=0" in src
            # Cap 2 retries: contar session.post chamadas dentro do branch OOM
            # (linha "if _is_oom_error(text) and not _OOM_DEGRADED:" ate proximo "else:")
            posts_no_branch_oom = 0
            in_branch = False
            for line in src.splitlines():
                if "if _is_oom_error(text)" in line and "_OOM_DEGRADED" in line:
                    in_branch = True
                    continue
                if in_branch and line.lstrip().startswith("else:") and "if _is_oom_error" not in line:
                    in_branch = False
                if in_branch and "session.post" in line:
                    posts_no_branch_oom += 1
            cap_ok = posts_no_branch_oom <= 2  # max 2 retries dentro do branch OOM
            ok = bool(tem_helper and helper_ok and tem_log_step and tem_chain and cap_ok)
            self._add(
                "RB-05",
                "Proxy tenta num_gpu intermediario antes de CPU (INFRA-OOM-RETRY-STEP-01)",
                "robustez_boot",
                ok,
                time.monotonic() - t,
                details=(
                    f"helper={tem_helper} helper_ok={helper_ok} log_step={tem_log_step} "
                    f"chain={tem_chain} posts_oom={posts_no_branch_oom} cap_ok={cap_ok}"
                ),
            )
        except Exception as e:
            self._add(
                "RB-05",
                "Proxy tenta num_gpu intermediario antes de CPU (INFRA-OOM-RETRY-STEP-01)",
                "robustez_boot",
                False,
                time.monotonic() - t,
                error=str(e),
            )
```

Notas:

- Padrão idêntico ao RB-04 (linhas 4120-4152): importlib + grep + assert. Zero mocks (política gauntlet).
- Contar `session.post` dentro do branch OOM é heurística robusta para o cap de 2 retries (não usa AST, suficiente para grep cosmético).

### Passo 6 — Validação runtime real (helper isolado)

Antes do boot, validar helper via Python diretamente:

```bash
./venv/bin/python -c "
from nyx.proxy import _next_num_gpu_step
assert _next_num_gpu_step(15) == 7, f'15 -> {_next_num_gpu_step(15)}'
assert _next_num_gpu_step(12) == 6, f'12 -> {_next_num_gpu_step(12)}'
assert _next_num_gpu_step(7) == 3, f'7 -> {_next_num_gpu_step(7)}'
assert _next_num_gpu_step(2) == 1, f'2 -> {_next_num_gpu_step(2)}'
assert _next_num_gpu_step(1) == 0, f'1 -> {_next_num_gpu_step(1)}'
assert _next_num_gpu_step(0) == 0, f'0 -> {_next_num_gpu_step(0)}'
print('helper ok')
"
# Esperado: helper ok
```

### Passo 7 — Validação runtime real (proxy boot + /admin/stats sem OOM)

OOM real não é forçado sintetico (gauntlet "zero mocks"). Validar que o proxy boot continua íntegro e contrato `/admin/stats` preservado:

```bash
./run.sh --smoke
# Esperado: boot ok

# Boot proxy isolado
./run.sh --headless &
PID=$!
sleep 5

# Stats inicial (sem OOM ainda) — contrato INFRA-OOM-02 preservado
curl -s http://127.0.0.1:11436/admin/stats | python -m json.tool
# Esperado: {oom_recovery_count: 0, num_gpu_current: 15, num_gpu_initial: 15, oom_degraded: false}

# Tune para validar que GPU parcial nao trava handle_tune (acoplamento)
curl -s "http://127.0.0.1:11436/admin/tune" | python -m json.tool
# Esperado: changed pode ser true/false, mas oom_degraded: false

# Cleanup
kill $PID 2>/dev/null
pkill -f "nyx/proxy.py" 2>/dev/null
pkill -f "ollama serve" 2>/dev/null
nvidia-smi | head -10
```

### Passo 8 — Invariantes e gauntlet

```bash
bash scripts/sprint_invariants.sh > /tmp/inv_after.txt 2>&1
diff /tmp/inv_before.txt /tmp/inv_after.txt
tail -5 /tmp/inv_after.txt
# Esperado: FAIL_AFTER <= FAIL_BEFORE (0)

./run.sh --gauntlet --only proxy 2>&1 | tail -15
# Esperado: 100% (regression-free)

./run.sh --gauntlet --only rapido 2>&1 | tail -15
# Esperado: 100% (RB-05 nao aparece aqui; rapido = {infra,proxy,visual,config})

./run.sh --gauntlet --only robustez_boot 2>&1 | tail -15
# Esperado: 5 PASS (RB-01, RB-02, RB-03, RB-04, RB-05); RB-04 e RB-03 inalterados
```

### Passo 9 — Acentuação e ruff

```bash
~/.config/zsh/scripts/validar-acentuacao.py \
  /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/proxy.py \
  /home/andrefarias/Desenvolvimento/Nyx-Code/scripts/gauntlet/nyx_gauntlet.py
# Esperado: exit 0

./venv/bin/python -m ruff check \
  /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/proxy.py \
  /home/andrefarias/Desenvolvimento/Nyx-Code/scripts/gauntlet/nyx_gauntlet.py
# Esperado: All checks passed
```

### Passo 10 — Commit + atualização do MASTER

```
feat(INFRA-OOM-RETRY-STEP-01): retry intermediario num_gpu // 2 antes de CPU no proxy
```

Atualizar `dev-journey/06-sprints/SPRINT_ORDER_MASTER.md` linha 125aa: trocar `RASCUNHO` por `CONCLUIDA (2026-05-20, ...)` com referência ao commit.

### Passo 11 — Mover spec para concluidos

```bash
mv /home/andrefarias/Desenvolvimento/Nyx-Code/dev-journey/06-sprints/producao/SPRINT_INFRA_OOM_RETRY_STEP_01.md \
   /home/andrefarias/Desenvolvimento/Nyx-Code/dev-journey/06-sprints/concluidos/
```

Atualizar header do spec movido para `Status: CONCLUIDA`.

---

## Aritmética

Sprint expande funcionalidade (passo intermediário); não tem meta numérica de redução de linhas. Estimativa de delta:

### nyx/proxy.py

- **Atual**: 886 linhas (confirmado via `wc -l`).
- **Adições**:
  - Helper `_next_num_gpu_step`: ~8L (def + docstring + return).
  - Atualização docstring `_OOM_DEGRADED` (linhas 66-69 atuais → 71L): delta +2L (5L vs 4L).
  - Reestrutura bloco OOM em `handle_chat` (linhas 421-441 atuais = 21L → ~42L após cadeia): delta +21L.
- **Delta total**: ~+31L.
- **Projetado**: 886 + 31 = **917 linhas**.
- **Sem teto crítico** (limite de aviso interno: 1000L; ainda confortável; INFRA-OOM-02 já levou de 841 → 886).

### scripts/gauntlet/nyx_gauntlet.py

- **Atual**: 4611+ linhas (confirmado em `wc -l` durante exploração).
- **Adições**:
  - RB-05 (após linha 4152): ~32L (try/except + helper unit + grep + self._add success + self._add error).
- **Delta total**: ~+32L.
- **Sem teto** (gauntlet cresce com fases; nenhuma sprint anterior estabeleceu limite).

### Verificação pré-execução

Executor deve rodar `wc -l` nos dois arquivos ANTES de modificar para confirmar baseline (lição 7: aritmética declarada).

---

## Testes

### Baseline a coletar antes de iniciar

```bash
# Aritmética
wc -l /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/proxy.py
# Esperado: 886
wc -l /home/andrefarias/Desenvolvimento/Nyx-Code/scripts/gauntlet/nyx_gauntlet.py
# Esperado: >=4611

# Invariantes baseline
bash scripts/sprint_invariants.sh > /tmp/inv_before.txt 2>&1
tail -5 /tmp/inv_before.txt
# FAIL_BEFORE = 0 esperado

# Gauntlet baseline
./run.sh --gauntlet --only proxy 2>&1 | grep -E "PASS|FAIL|Total" | tail -5
./run.sh --gauntlet --only robustez_boot 2>&1 | grep -E "PASS|FAIL|Total" | tail -5
# Esperado: RB-01..RB-04 = 4 PASS em robustez_boot; gauntlet proxy passes ja existente
```

### Esperado após implementação

- `FAIL_AFTER` == `FAIL_BEFORE` (0).
- Gauntlet `proxy`: passes ≥ baseline (idealmente +0; sprint não modifica testes proxy/*).
- Gauntlet `rapido`: passes ≥ baseline (RB-05 NÃO aparece em `rapido`; vive em `robustez_boot`).
- Gauntlet `robustez_boot`: passes = baseline + 1 (RB-05 novo PASS; RB-01..RB-04 inalterados).
- Helper unit: `python -c 'from nyx.proxy import _next_num_gpu_step; ...'` → `"helper ok"`.

### Testes que NÃO existem (e por que)

- **Mock httpx para forçar OOM em runtime**: violaria política do gauntlet ("Zero mocks. 100% real." linha 2 do `nyx_gauntlet.py`). Validação via RB-05 grep + assert helper é suficiente para confirmar implementação cirúrgica.
- **OOM real injetado**: forçar OOM via VRAM real é instável e não-determinístico em CI. Anti-débito futuro: se necessário, criar sprint `INFRA-OOM-CHAOS-01` com VRAM hog controlado.
- **Test_proxy.py pytest**: política do projeto proíbe `test_*.py` solto (feedback `feedback_integracao_obrigatoria.md`); testes exclusivamente via gauntlet.

---

## Proof-of-work esperado

- **Diff final**: `git diff` cobrindo `nyx/proxy.py` (+31L) + `scripts/gauntlet/nyx_gauntlet.py` (+32L).
- **Runtime real** (do `VALIDATOR_BRIEF.md` CORE):
  - `./run.sh --smoke` → boot ok.
  - `bash scripts/sprint_invariants.sh` → PASS 14, FAIL 0.
  - `./run.sh --gauntlet --only proxy` → 100%.
  - `./run.sh --gauntlet --only rapido` → 100% (regression-free).
  - `./run.sh --gauntlet --only robustez_boot` → 100% (RB-05 PASS novo).
- **Helper unit** (proof do contrato):
  ```bash
  ./venv/bin/python -c "from nyx.proxy import _next_num_gpu_step; assert _next_num_gpu_step(15) == 7; assert _next_num_gpu_step(12) == 6; assert _next_num_gpu_step(2) == 1; assert _next_num_gpu_step(1) == 0; assert _next_num_gpu_step(0) == 0; print('helper ok')"
  ```
- **Endpoint live** (regressão INFRA-OOM-02):
  - `curl -s http://127.0.0.1:11436/admin/stats | python -m json.tool` → JSON com 4 chaves esperadas, `oom_recovery_count=0` em boot fresco.
- **Acentuação periférica**: `~/.config/zsh/scripts/validar-acentuacao.py` em `nyx/proxy.py` + `scripts/gauntlet/nyx_gauntlet.py` → exit 0.
- **Ruff**: `./venv/bin/python -m ruff check nyx/proxy.py scripts/gauntlet/nyx_gauntlet.py` → `All checks passed`.
- **Hipótese verificada via rg** (pré-implementação, **confirmado pelo planejador**):
  - `_OOM_DEGRADED`: confirmado linhas 60, 66, 71, 76, 404, 421, 422, 763, 770, 822 (10 ocorrências, todos esperados).
  - `_OOM_PATTERNS`: confirmado linhas 63, 77, 92.
  - `_is_oom_error`: confirmado linhas 63, 88, 421.
  - `_LOOPBACK_HOSTS`: confirmado linhas 659, 676, 745, 812 (4 ocorrências; RB-04 valida `>= 4`).
  - `_INITIAL_NUM_GPU`: confirmado linhas 58, 834.
  - `handle_chat` async def: confirmado linha 403.
  - `state["num_gpu"]` mutation: confirmado linhas 423 (atual fallback CPU).
  - `state["oom_recovery_count"]` increment: confirmado linha 436 (atual).
  - `logger.warning` "OOM detectado": confirmado linha 424.
  - `_next_num_gpu_step`: **NÃO existe** (confirmado via grep no projeto; helper é novo).
  - `"OOM degradation step"`: **NÃO existe** (confirmado; log é novo).
- **Cleanup pós-teste**: `pkill -f "nyx/proxy.py"`, `pkill -f "ollama serve"`, `nvidia-smi` confirmando VRAM livre.

---

## Riscos e mitigações

| Risco | Mitigação |
|---|---|
| Reestrutura de handle_chat introduz regressão em fluxo não-OOM | Edição cirúrgica: apenas linhas 421-441 (branch OOM); fluxo 200 normal (linhas 442+) inalterado. Diff revisável. |
| `_OOM_DEGRADED` setado prematuramente no intermediário trava handle_tune | Acceptance criterion #4 explícito: setar `_OOM_DEGRADED=True` **só** no fallback CPU. RB-05 valida via grep do trecho `chain="GPU parcial" in src AND "Degradando num_gpu=0" in src`. |
| Sequência 15 → 7 → 3 → 0 em sessões hostis (degradação contínua sem `_OOM_DEGRADED`) | Comportamento aceitável e desejado: cada OOM tenta intermediário ainda mais baixo até CPU. Cap de 2 retries por request preservado; sessões com OOM crônico convergem para CPU naturalmente. |
| `data` undefined em algum caminho do bloco OOM (NameError em linha 445+) | Acceptance criterion #2: ambos caminhos de sucesso (intermediário OK + CPU OK) setam `data`. Todos os caminhos de falha retornam `web.json_response` antes de atingir linha 445. Diff review obrigatório. |
| RB-05 cap-counting (`session.post` no branch) falha por edição cirúrgica em comentários | Implementação preserva mesmo padrão de `async with session.post`. Heurística de grep tolera espaços/quebras. Alternativa de fallback: contar via AST se grep falhar (out-of-scope para esta sprint). |
| Política "zero mocks" do gauntlet bloqueia validação completa | RB-05 valida 100% do que é validável estaticamente (helper unit + grep + estrutura). OOM real fica para INFRA-OOM-CHAOS-01 futuro (anti-débito declarado). |
| Acoplamento com INFRA-OOM-HISTORY-01 (out-of-scope) | Persistência cross-session de `oom_recovery_count` é sprint distinta (linha 125cc do MASTER). Esta sprint não toca persistência. |

---

## Out-of-scope (anti-débito)

Se durante execução surgir qualquer um destes, registrar como sprint nova com ID e mover para o MASTER:

1. **OOM real injetado via VRAM hog controlado** → `INFRA-OOM-CHAOS-01` (BAIXA). Cenário de teste e2e forçando OOM real para validar cadeia 15 → 7 → 0 em runtime.
2. **Configuração de step custom (não // 2)** → `INFRA-OOM-RETRY-STEP-CONFIG-01` (BAIXA, hipotético). Env var ou /admin/tune param para definir step ratio.
3. **Persistência de cadeia entre sessões** → já é `INFRA-OOM-HISTORY-01` (linha 125cc do MASTER, RASCUNHO).
4. **Algoritmo adaptativo baseado em histórico de VRAM** → `PROXY-VRAM-PREDICT-01` (BAIXA, hipotético). Mencionado no enunciado original do INFRA-OOM-02; fora dessa sprint.
5. **Aplicar passo intermediário em outras rotas /api/*** → `PROXY-OOM-MULTIROUTE-01` (BAIXA, hipotético). Atualmente só `/v1/chat/completions` faz tool calling; outras rotas não disparam OOM no tooling path.
6. **Refactor de handle_chat para extrair bloco OOM como função** → `PROXY-OOM-EXTRACT-01` (BAIXA, anti-débito declarado pelo INFRA-OOM-02 linha 437 do spec original). Sprint cirúrgica de refactor sem mudança comportamental.
7. **Exposição CLI da cadeia atual de degradação** → `INFRA-OOM-STATS-CLI-CHAIN-01` (BAIXA, hipotético). `/stats` mostraria histórico de steps (ex.: `15 -> 7 active`).

---

## Referências

- VALIDATOR_BRIEF: `/home/andrefarias/Desenvolvimento/Nyx-Code/VALIDATOR_BRIEF.md`
- Sprint precedente (dependência direta): `dev-journey/06-sprints/concluidos/SPRINT_INFRA_OOM_02.md` — estabeleceu `state["oom_recovery_count"]`, `/admin/stats`, docstring `_OOM_DEGRADED`; out-of-scope item #1 (linha 433) é exatamente esta sprint.
- Sprint relacionada: `dev-journey/06-sprints/concluidos/SPRINT_INFRA_OOM_STATS_CLI_01.md` — `/stats` slash command; contrato JSON preservado por esta sprint.
- Sprint relacionada: `dev-journey/06-sprints/concluidos/SPRINT_PROXY_NUMGPU_RUNTIME_01.md` — estabeleceu `app["state"]`, `handle_tune`, `_LOOPBACK_HOSTS` (acoplamentos #7-#10).
- Entrada MASTER: `dev-journey/06-sprints/SPRINT_ORDER_MASTER.md` linha 125aa (RASCUNHO).
- Gauntlet RB-03 (referência de idioma): `scripts/gauntlet/nyx_gauntlet.py` linhas 4083-4118.
- Gauntlet RB-04 (referência de idioma): `scripts/gauntlet/nyx_gauntlet.py` linhas 4120-4152.
- ADR-001 Local First (referenciado no bloco `_OOM_DEGRADED` linha 61).
- Política "Zero mocks. 100% real.": `scripts/gauntlet/nyx_gauntlet.py` linha 2.
- Política "integração obrigatória": `~/.claude/projects/-home-andrefarias-Desenvolvimento-Nyx-Code/memory/feedback_integracao_obrigatoria.md`.

---

*"Cair de 15 para 0 é binário. Cair de 15 para 7 e só depois para 0 é gradiente. O hardware adora gradientes." — INFRA-OOM-RETRY-STEP-01*
