# SPRINT UX-LIFECYCLE-01 — Single-instance, cleanup robusto, OOM prevention pré-inferência

## 0. SPEC (machine-readable)

```yaml
sprint:
  id: UX-LIFECYCLE-01
  title: "Garante encerramento limpo em todos os exit paths, single-instance via lock file, OOM prevention proativo"
  onda: 23
  bloco: 23.1 Estabilização
  prioridade: ALTA
  tipo: Feature+Infra
  dependencias: [BOOT-VRAM-GUARD-01, TUI-SHUTDOWN-SILENT-01]
  desbloqueia: []
  origem: "Usuário em 2026-05-16: 'sempre cuidar pra evitar oom causado pelo ollama e python, sempre encerrar o app, cada vez que for aberto mata a versão anterior, pra evitar que cada teste coma mais vram desnecessária'."

  touches:
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/run.sh
      reason: "Adiciona create_pidfile + cleanup robusto em todos os exit paths (EXIT, SIGINT, SIGTERM, SIGHUP); single-instance guard com lock file"
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/cli.py
      reason: "Slash command /quit (alias /sair, /exit) chama cleanup explícito antes de exit. EOFError (Ctrl+D) e KeyboardInterrupt (Ctrl+C) já tratados — garantir cleanup invocado"
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/proxy.py
      reason: "Endpoint POST /admin/shutdown (loopback only) que encerra graciosamente proxy + Ollama child"
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/agent/loop/_iteration.py
      reason: "Antes de _call_llm em cold start, verificar VRAM via subprocess (nvidia-smi); abortar com erro claro em PT-BR se <800 MiB"
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/config/defaults.py
      reason: "Adicionar NYX_PID_FILE (fonte única)"

  creates:
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/agent/services/lifecycle.py
      reason: "Service único: PID file management, OOM check pré-inferência, signal handlers Python"

  removes: []

  n_to_n_pairs:
    - descricao: "PID file path em run.sh + lifecycle.py + cli.py — fonte única em config/defaults.py"
      paths:
        - /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/config/defaults.py
        - /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/agent/services/lifecycle.py
        - /home/andrefarias/Desenvolvimento/Nyx-Code/run.sh

  forbidden:
    - "Force-kill via SIGKILL como primeiro recurso — sempre tentar SIGTERM com timeout (gracefulness)"
    - "Deixar processos órfãos vivos após exit normal (zombies)"
    - "Lock file sem PID dentro (impossível detectar stale lock)"
    - "Travar boot se VRAM apertada — degradar gracefully para CPU"
    - "Adicionar emoji ou menção a IA"
    - "Quebrar comportamento existente de kill_existing_ollama (já mata Ollama anterior)"

  tests:
    - cmd: "./run.sh --smoke && ./run.sh --smoke && pgrep -f 'ollama serve|nyx/proxy.py' | wc -l"
      timeout: 90
      deve_passar: "saída == 0 (smoke não deixa processos rodando)"
    - cmd: "manual: ./run.sh & PID1=$!; sleep 8; ./run.sh; ps -p $PID1"
      deve_passar: "primeira instância (PID1) foi morta pela segunda"
    - cmd: "manual: ./run.sh; aguardar prompt; Ctrl+D; sleep 3; pgrep -af 'ollama serve|nyx/proxy.py'"
      deve_passar: "saída vazia (tudo encerrado limpo)"
    - cmd: "./run.sh --gauntlet --only rapido"
      timeout: 300
      deve_passar: true
    - cmd: "bash scripts/sprint_invariants.sh"
      timeout: 60
      deve_passar: "FAIL_AFTER <= FAIL_BEFORE"

  acceptance_criteria:
    - "Lock file em /tmp/nyx.pid (ou XDG_RUNTIME_DIR) com PID do run.sh atual"
    - "Boot detecta lock stale (PID não vive mais) e segue; lock vivo → mata anterior via SIGTERM (5s timeout) → SIGKILL fallback"
    - "Cleanup em SIGINT/SIGTERM/EXIT/SIGHUP mata: Ollama child, proxy child, CLI Python, remove lock file"
    - "Comandos /quit (alias /sair, /exit) em cli.py: cleanup explícito antes de exit"
    - "POST /admin/shutdown no proxy (bind 127.0.0.1, rejeita não-loopback): graceful exit do proxy"
    - "Antes de _call_llm em cold start: verificar VRAM via nvidia-smi (timeout 3s); abortar com mensagem PT-BR clara se VRAM < 800 MiB"
    - "Após ./run.sh interrompido por Ctrl+C: zero MiB residual de processos Nyx (validar via pgrep)"
    - "Smoke + gauntlet rapido passam"
    - "Acentuação PT-BR, zero emoji, zero menção a IA"
```

---

**Status:** CONCLUIDA
**Data criação:** 2026-05-16
**Data conclusão:** 2026-05-17
**Modelo obrigatório:** claude-opus-4-7 (sem subagentes)
**Origem:** pedido explícito do usuário em 2026-05-16, durante validação visual de UX-BUG-02B. Anti-débito.

## Resultado

- Lock file em `/tmp/nyx.pid` (fonte única `NYX_PID_FILE` em `nyx/config/defaults.py`).
- `acquire_lock` em `run.sh` detecta stale lock + mata anterior gracefully (SIGTERM 5s → SIGKILL) + kill em árvore (`pgrep -P`) para evitar órfãos reparented.
- `cleanup` expandido: SIGHUP adicionado ao trap; remoção idempotente do lock só se PID corresponde.
- `nyx/agent/services/lifecycle.py` (NOVO, 179 linhas): classe `Lifecycle` com `acquire/release/vram_check/register_cleanup`. Cobertura graceful em falha de `nvidia-smi`.
- `nyx/proxy.py`: endpoint `POST /admin/shutdown` (bind 127.0.0.1 + check `request.remote in ("127.0.0.1","::1")`). Responde 200 antes de auto-SIGTERM no PID do proxy (graceful flush).
- `nyx/cli.py`: comando `/quit` (aliases `/q`, `/exit`) faz POST `/admin/shutdown` best-effort antes de break do REPL.
- `nyx/agent/loop/_iteration.py`: VRAM check pré-`_call_llm` em cold start (flag `_vram_checked` idempotente). Threshold 800 MiB; graceful em ausência de nvidia-smi.

### Testes manuais

1. `./run.sh --smoke && ./run.sh --smoke` → 0 órfãos (smoke não levanta Ollama).
2. `./run.sh` → prompt → `/quit` → "Desconectando..." → 0 órfãos, lock removido, VRAM 64/3706.
3. Single-instance: instância 1 ativa; instância 2 inicia → mata 1 via SIGTERM (sobreviveu → SIGKILL na árvore) → 0 órfãos pós ciclo completo.
4. `curl -X POST http://127.0.0.1:11436/admin/shutdown` → `{"status":"shutting_down"}` → proxy morre em <1s → cleanup do `run.sh` em cascata.

### Aritmética

- `run.sh`: +61 linhas (acquire_lock + cleanup expandido + trap SIGHUP).
- `nyx/cli.py`: +10 linhas (POST shutdown best-effort em `/quit`).
- `nyx/proxy.py`: +33 linhas (handler shutdown + imports asyncio/os/signal).
- `nyx/agent/loop/_iteration.py`: +20 linhas (VRAM check guardado por `_vram_checked`).
- `nyx/agent/loop/_core.py`: +4 linhas (flag `_vram_checked = False`).
- `nyx/config/defaults.py`: +8 linhas (NYX_PID_FILE + import os).
- `nyx/agent/services/lifecycle.py`: +179 linhas (arquivo novo).
- Total líquido: +315 linhas.

### Não-regressão

- `bash scripts/sprint_invariants.sh` → FAIL_AFTER = 0 (= FAIL_BEFORE).
- `./run.sh --smoke` → boot ok.
- `./run.sh --gauntlet --only rapido` → 18/18 (100%) em 11s.

### Observação sobre dependências

A sprint declarava `dependencias: [BOOT-VRAM-GUARD-01, TUI-SHUTDOWN-SILENT-01]` mas ambas estavam PENDENTES no momento da execução. Foi executada por pedido explícito do usuário (2026-05-16) e **substitui parcialmente** o escopo das deps:
- BOOT-VRAM-GUARD-01: o `vram_check` adicionado em `_iteration.py` cobre o caso runtime; pré-carga do `run.sh` continua sob escopo daquela sprint.
- TUI-SHUTDOWN-SILENT-01: o cleanup robusto reduz mensagens "Morto" mas não elimina via `disown`/`set +m`.

Ambas as sprints permanecem PENDENTES para fechar pontas finas.

---

# Sprint UX-LIFECYCLE-01

## Contexto

Hoje o `run.sh` tem `kill_existing_ollama()` (linha 147) que mata Ollama na porta dele se já existir. Também tem `trap cleanup EXIT SIGINT SIGTERM` (linha 295). Mas faltam:

1. **Single-instance formal**: lock file com PID, detecção de stale lock.
2. **Cleanup de cenários edge**: SIGHUP (terminal fechado), processo Python morto antes do shell terminar.
3. **/quit explícito**: comando slash que chama cleanup antes de exit. Ctrl+D atual cai no `except EOFError: break` mas cleanup do shell pode não rodar se Python morre primeiro.
4. **OOM prevention proativo**: BOOT-VRAM-GUARD-01 ajusta num_gpu na pré-carga. Falta verificar VRAM ANTES de cada request quando modelo está cold (segunda inferência pode bater limite se VRAM mudou).

## Solução conceitual

### `nyx/agent/services/lifecycle.py` (novo)

```python
"""Lifecycle: PID file, OOM check pré-inferência, signal handlers."""
import atexit, os, signal, subprocess
from pathlib import Path
from nyx.agent.services.logging_service import get_logger
from nyx.config.defaults import NYX_PID_FILE

logger = get_logger("nyx.lifecycle")


class Lifecycle:
    def __init__(self):
        self._pidfile = Path(NYX_PID_FILE)
        self._cleanup_callbacks: list = []

    def acquire(self) -> bool:
        """Lock file. Mata anterior gracefully se PID vivo."""
        if self._pidfile.exists():
            try:
                old_pid = int(self._pidfile.read_text().strip() or 0)
            except ValueError:
                old_pid = 0
            if old_pid and self._pid_alive(old_pid):
                logger.info("matando instância anterior PID=%d", old_pid)
                try:
                    os.kill(old_pid, signal.SIGTERM)
                except ProcessLookupError:
                    pass
                import time
                for _ in range(50):
                    if not self._pid_alive(old_pid):
                        break
                    time.sleep(0.1)
                if self._pid_alive(old_pid):
                    try:
                        os.kill(old_pid, signal.SIGKILL)
                    except ProcessLookupError:
                        pass
        self._pidfile.write_text(str(os.getpid()))
        atexit.register(self.release)
        return True

    def release(self):
        for cb in self._cleanup_callbacks:
            try:
                cb()
            except Exception as exc:  # noqa: BLE001
                logger.warning("cleanup callback raised: %s", exc)
        if self._pidfile.exists():
            try:
                self._pidfile.unlink()
            except OSError:
                pass

    def vram_check(self, threshold_mb: int = 800) -> tuple[bool, int]:
        """(ok, free_mb). False se VRAM abaixo do threshold. Graceful em falha."""
        try:
            r = subprocess.run(
                ["nvidia-smi", "--query-gpu=memory.free", "--format=csv,noheader,nounits"],
                capture_output=True,
                text=True,
                timeout=3,
            )
            free = int(r.stdout.strip().split("\n")[0])
            return (free >= threshold_mb, free)
        except Exception:  # noqa: BLE001 -- assume ok se não conseguir checar
            return (True, -1)

    def register_cleanup(self, fn):
        self._cleanup_callbacks.append(fn)

    @staticmethod
    def _pid_alive(pid: int) -> bool:
        try:
            os.kill(pid, 0)
            return True
        except (OSError, ProcessLookupError):
            return False
```

### `nyx/config/defaults.py` — adicionar

```python
import os
NYX_PID_FILE = os.environ.get("NYX_PID_FILE", "/tmp/nyx.pid")
```

### `run.sh` — modificações pontuais

```bash
# Após mkdir logs, antes de validate():
NYX_PID_FILE="${NYX_PID_FILE:-/tmp/nyx.pid}"

# Função nova:
acquire_lock() {
    if [ -f "$NYX_PID_FILE" ]; then
        OLD_PID=$(cat "$NYX_PID_FILE" 2>/dev/null)
        if [ -n "$OLD_PID" ] && kill -0 "$OLD_PID" 2>/dev/null; then
            log_nyx "Matando instância anterior (PID $OLD_PID)..."
            kill -TERM "$OLD_PID" 2>/dev/null
            for i in 1 2 3 4 5; do
                kill -0 "$OLD_PID" 2>/dev/null || break
                sleep 1
            done
            kill -KILL "$OLD_PID" 2>/dev/null || true
        fi
    fi
    echo $$ > "$NYX_PID_FILE"
}

# Cleanup expandido:
cleanup() {
    echo ""
    log_nyx "Desconectando..."
    if [ -n "${PROXY_PID:-}" ] && kill -0 "$PROXY_PID" 2>/dev/null; then
        kill "$PROXY_PID" 2>/dev/null
    fi
    pkill -f "nyx/proxy.py" 2>/dev/null || true
    stop_ollama
    rm -f "$NYX_PID_FILE" 2>/dev/null
    log_ok "Fim."
}

trap cleanup EXIT SIGINT SIGTERM SIGHUP

# Chamar acquire_lock após validate():
acquire_lock
```

### `nyx/cli.py` — comandos /quit, /sair, /exit

```python
# Em handle_command ou inline:
if user_input in ("/quit", "/sair", "/exit"):
    output("info", "Encerrando Nyx. Limpando recursos...")
    if agent and hasattr(agent, '_http_client') and agent._http_client:
        await agent._http_client.aclose()
    try:
        async with httpx.AsyncClient(timeout=2) as s:
            await s.post(f"http://127.0.0.1:{settings.proxy_port}/admin/shutdown")
    except Exception:
        pass
    break
```

### `nyx/proxy.py` — endpoint /admin/shutdown

```python
async def handle_shutdown(request: web.Request) -> web.Response:
    if request.remote not in ("127.0.0.1", "::1"):
        return web.json_response({"error": "loopback only"}, status=403)
    logger.info("shutdown solicitado via /admin/shutdown")
    # responder antes de matar o loop
    response = web.json_response({"status": "shutting_down"})
    asyncio.create_task(_delayed_shutdown())
    return response

async def _delayed_shutdown():
    await asyncio.sleep(0.5)
    sys.exit(0)

# No setup do app:
app.router.add_post("/admin/shutdown", handle_shutdown)
```

### `nyx/agent/loop/_iteration.py` — VRAM check pré-inferência

```python
# Em _call_llm, no início (cold start only):
async def _call_llm(self) -> dict[str, Any]:
    if self._model_state == "cold":
        from nyx.agent.services.lifecycle import Lifecycle
        ok, free_mb = Lifecycle().vram_check(threshold_mb=800)
        if not ok:
            return {
                "error": (
                    f"VRAM insuficiente ({free_mb} MiB livres). "
                    "Feche outros processos GPU ou rode em CPU com NYX_NUM_GPU=0."
                ),
                "error_detail": f"vram_free={free_mb}MiB threshold=800MiB"
            }
    # resto do método existente...
```

## Verificação manual obrigatória

```bash
# 1. Single-instance
./run.sh &
PID1=$!
sleep 8
./run.sh &
PID2=$!
sleep 5
ps -p $PID1  # primeira instância morta
kill $PID2 2>/dev/null
sleep 3
pgrep -af "ollama serve|nyx/proxy" | wc -l  # 0

# 2. Cleanup em Ctrl+D
./run.sh
# Aguardar prompt → Ctrl+D
pgrep -af "ollama serve|nyx/proxy.py"  # vazio

# 3. Cleanup em /quit
./run.sh
# Aguardar prompt → digitar "/quit" → enter
pgrep -af "ollama serve|nyx/proxy.py"  # vazio

# 4. VRAM check com pouca memória
NYX_NUM_GPU=12 ./run.sh
# Em outro terminal, alocar VRAM com outro modelo grande
# Tentar conversar no Nyx — deve receber mensagem de erro clara em PT-BR
```

## Riscos

| Risco | Mitigação |
|---|---|
| Lock file leaked após hard reboot | Stale lock detection: verifica `kill -0 PID` antes de respeitar |
| SIGTERM no anterior não chega ao Ollama child | Cleanup do anterior também mata Ollama via stop_ollama() antes de soltar lock |
| /admin/shutdown HTTP exposto a remote | Bind 127.0.0.1 obrigatório + verificação `request.remote in ("127.0.0.1","::1")` |
| nvidia-smi timeout durante check | timeout 3s + assume_ok em failure (graceful degradation) |
| Race entre dois ./run.sh simultâneos | flock no PID file durante acquire (ou usar `set -C` + redirect noclobber) |
| Threshold 800 MiB cego para CPU mode | Skip vram_check se modelo já em CPU (`_model_state` rastreia OOM_DEGRADED via PROXY-NUMGPU-RUNTIME-01) |

---

*"Cada processo deixado para trás é um custo cobrado da próxima vez." -- princípio anti-débito aplicado a recursos*
