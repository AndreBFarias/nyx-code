# SPRINT PROXY-NUMGPU-RUNTIME-01 — Re-tune proativo do num_gpu no proxy em runtime

## 0. SPEC (machine-readable)

```yaml
sprint:
  id: PROXY-NUMGPU-RUNTIME-01
  title: "Re-tune proativo de num_gpu durante sessão (sem reiniciar proxy)"
  onda: 23
  bloco: 23.1 Estabilização
  prioridade: MÉDIA
  tipo: Refactor+Feature
  dependencias: [BOOT-VRAM-GUARD-01]
  desbloqueia: [COCKPIT-01]

  touches:
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/proxy.py
      reason: "Remover NUM_GPU módulo-global; usar app.state.num_gpu; rota GET /admin/tune"
      linhas_alvo: "42, 110, 187-206, 282-298"
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/cli.py
      reason: "Slash command /tune que chama /admin/tune do proxy"

  creates: []
  removes: []

  n_to_n_pairs:
    - descricao: "num_gpu existe no .env, run.sh, detect_gpu.py, proxy.py — fonte única passa a ser /admin/tune"
      paths:
        - /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/proxy.py
        - /home/andrefarias/Desenvolvimento/Nyx-Code/scripts/detect_gpu.py

  forbidden:
    - "Manter NUM_GPU como módulo-global"
    - "Quebrar fail-safe OOM existente (_OOM_DEGRADED → CPU permanente)"
    - "Adicionar rota /admin/* sem bind 127.0.0.1 (ADR-001 Local First)"
    - "Spawn subprocess no caminho síncrono do handle_chat (latência crítica)"

  tests:
    - cmd: "./run.sh --gauntlet --only proxy"
      timeout: 300
      deve_passar: true
    - cmd: "curl -s http://127.0.0.1:11436/admin/tune"
      timeout: 30
      deve_passar: true
      nota: "Retorna JSON {old_num_gpu, new_num_gpu, vram_free_mb, changed: bool}"
    - cmd: "bash scripts/sprint_invariants.sh"
      timeout: 60
      deve_passar: "FAIL_AFTER <= FAIL_BEFORE"

  acceptance_criteria:
    - "NUM_GPU não é mais módulo-global em proxy.py; vira app.state.num_gpu"
    - "Rota GET /admin/tune existe e re-roda detect_gpu.py + atualiza app.state.num_gpu"
    - "Rota só aceita conexões 127.0.0.1 (rejeita não-loopback)"
    - "Fail-safe OOM (_OOM_DEGRADED) continua funcional"
    - "Comando /tune em cli.py chama o endpoint e mostra resultado em PT-BR"
    - "Gauntlet proxy passa 100%"
    - "Acentuação PT-BR correta"
```

---

**Status:** CONCLUIDA
**Data criação:** 2026-05-15
**Data conclusão:** 2026-05-17
**Hash:** 0ad8e6e
**Modelo obrigatório:** claude-opus-4-7 (sem subagentes)
**Resultado:** NUM_GPU removido como módulo-global; GET /admin/tune (loopback-only) re-tune via detect_gpu.py; slash /tune em commands/system.py mostra resultado em PT-BR. Fail-safe OOM preservado. Gauntlet proxy 6/6 + rapido 18/18.

---

# Sprint PROXY-NUMGPU-RUNTIME-01

## Contexto

Após BOOT-VRAM-GUARD-01, o boot fica resiliente. Mas durante a sessão, se a VRAM mudar (usuário fecha browser ou abre outro programa), o proxy continua enviando `num_gpu` antigo até que ocorra OOM (e aí cai para CPU permanente).

Solução: expor endpoint admin no proxy que re-tune proativamente.

## Solução

### `nyx/proxy.py` — refactor

```python
async def _on_startup(app: web.Application) -> None:
    app["http_session"] = ClientSession(timeout=ClientTimeout(total=600))
    app["num_gpu"] = NUM_GPU  # snapshot inicial
    app["num_ctx"] = NUM_CTX
    app["oom_degraded"] = False

async def handle_tune(request: web.Request) -> web.Response:
    """Re-roda detect_gpu.py e atualiza num_gpu live."""
    if request.remote not in ("127.0.0.1", "::1"):
        return web.json_response({"error": "loopback only"}, status=403)
    import subprocess
    proc = subprocess.run(
        ["python", "scripts/detect_gpu.py", "--for-model", "qwen3:4b"],
        capture_output=True, text=True, timeout=15,
    )
    new = int(proc.stdout.strip() or "0")
    old = request.app["num_gpu"]
    request.app["num_gpu"] = new
    return web.json_response({"old_num_gpu": old, "new_num_gpu": new, "changed": old != new})
```

### `nyx/cli.py` — comando `/tune`

```python
elif cmd == "/tune":
    async with aiohttp.ClientSession() as s:
        async with s.get(f"http://127.0.0.1:{proxy_port}/admin/tune") as r:
            data = await r.json()
    output("info", f"num_gpu: {data['old_num_gpu']} -> {data['new_num_gpu']}")
```

## Verificação

```bash
bash scripts/sprint_invariants.sh > /tmp/inv_before.txt 2>&1
# implementar
bash scripts/sprint_invariants.sh > /tmp/inv_after.txt 2>&1
diff /tmp/inv_before.txt /tmp/inv_after.txt
./run.sh --smoke
./run.sh --gauntlet --only proxy
curl -s http://127.0.0.1:11436/admin/tune | jq .
```

## Gambiarras proibidas

- Spawn em thread pool sem timeout (pode pendurar handle_chat).
- Quebrar fail-safe OOM existente.
- Adicionar logging verbose no caminho crítico (vira ruído).

---

*"Reagir é tarde; antecipar é design." -- anônimo*
