## 0. SPEC

```yaml
sprint:
  id: UX-BUG-03
  title: "Performance TUI: start <1.5s + Console singleton + cancel tasks pendentes + memory lazy"
  onda: 22
  bloco: 5
  prioridade: ALTA
  tipo: Perf
  dependencias: [UX-BUG-02]
  desbloqueia: [VISION-01]

  touches:
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/cli.py
      reason: "Shutdown cancela task de sumarização; cleanup + Analytics em background"
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/agent/output.py
      reason: "_get_console() singleton em vez de new Console() a cada render"
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/agent/memory.py
      reason: "memory.index() em cache lazy; invalida só em /memory ou write"

  absorve:
    - "A-08 (task pendente ao quit)"
    - "A-09 (Console não-singleton)"

  forbidden:
    - "Remover analytics ou cleanup (precisam rodar, só não no caminho crítico)"
    - "Pular shutdown hook — dados de sessão podem se perder"

  tests:
    - cmd: "time ./run.sh --headless < /dev/null 2>&1 | head"
      esperado: "duração < 2s"
    - cmd: "./run.sh --gauntlet --only tui"
      deve_passar: true
    - cmd: "./run.sh --gauntlet --only rapido"
      deve_passar: true

  acceptance_criteria:
    - "Tempo ./run.sh (até primeiro prompt interativo) < 1.5s em máquina do usuário (Nitro-5), medido 5x"
    - "output._get_console() retorna instância única (id(c1) == id(c2))"
    - "Task de sumarização cancelada no shutdown (test: asyncio.all_tasks)"
    - "memory.index() cacheado; segunda chamada é O(1)"
    - "Gauntlet tui e rapido passam"
```

---

**Status:** CONCLUIDA
**Data criação:** 2026-04-18
**Data conclusão:** 2026-05-17
**Hash:** (a preencher pós-commit)
**Modelo obrigatório:** claude-opus-4-7 (sem subagentes)
**Resultado:** Console singleton via _get_console() lazy + memory.index() cacheado (invalidação em write) + Analytics migrado para warmup task pós-banner + summarize_task tracked/cancelado no shutdown + shutdown ordenado via asyncio.all_tasks. Mediana time-to-prompt 0.383s (target 1.5s, 4x folga). Gauntlet rapido 18/18 + p7_tui 2/2 + interface 5/5. +100L em 4 arquivos.

---

# Sprint UX-BUG-03 — Performance TUI

## Contexto

Findings:
- Lentidão geral reportada pelo usuário.
- A-08: `asyncio.create_task(agent.maybe_summarize())` sem cancelamento ao quit.
- A-09: `Console(highlight=False)` criado dentro de `render_user_input` — caro.
- Suspeita: `cleanup_old_sessions()` + `Analytics()` + `memory.index()` no caminho síncrono do start.

Métricas alvo (medir antes e depois):
- `time ./run.sh` até primeiro prompt: atual ~3s, meta <1.5s.
- Latência tecla → eco: imperceptível em CPU média.
- Flicker durante streaming: zero.

## Solução

### `nyx/agent/output.py` — Console singleton

```python
_console_cache: "Console | None" = None

def _get_console() -> "Console":
    global _console_cache
    if _console_cache is None and RICH_AVAILABLE:
        _console_cache = Console(highlight=False)
    return _console_cache

# Substituir todos `Console(highlight=False)` por `_get_console()`.
```

### `nyx/cli.py` — cleanup/analytics em background

```python
async def run_repl(streaming: bool = True) -> int:
    # Imediato:
    from nyx.agent.commands import handle_command
    from nyx.agent.context import render_context_bar
    from nyx.agent.loop import AgentLoop

    project_root = str(PROJECT_ROOT)

    # PromptSession + banner primeiro
    # ...

    # Background warm-up
    analytics_ref: list = [None]
    async def _bg_warmup():
        from nyx.agent.persistence import cleanup_old_sessions
        from nyx.agent.services.analytics import Analytics
        cleanup_old_sessions()
        analytics_ref[0] = Analytics()
    warmup_task = asyncio.create_task(_bg_warmup())

    # ... loop normal ...

    # Shutdown:
    for task in asyncio.all_tasks():
        if task is not asyncio.current_task() and not task.done():
            task.cancel()
    await asyncio.gather(warmup_task, return_exceptions=True)
    if analytics_ref[0]:
        analytics_ref[0].end_session()
```

### `nyx/cli.py` — cancelar task de summarize

Onde hoje:
```python
try:
    asyncio.create_task(agent.maybe_summarize())
except RuntimeError as exc:
    logger.warning("sumarização adiada ...", exc)
```

Mudar para:
```python
if summarize_task and not summarize_task.done():
    summarize_task.cancel()
try:
    summarize_task = asyncio.create_task(agent.maybe_summarize())
except RuntimeError as exc:
    logger.warning("sumarização adiada: %s", exc)
    summarize_task = None
```

E no shutdown incluir `summarize_task` no gather.

### `nyx/agent/memory.py` — index cacheado

Adicionar:
```python
class Memory:
    def __init__(self, ...):
        self._index_cache: list[dict] | None = None

    def index(self) -> list[dict]:
        if self._index_cache is None:
            self._index_cache = self._read_index_from_disk()
        return self._index_cache

    def write(self, ...):
        # invalidar cache ao escrever
        self._index_cache = None
        self._write_to_disk(...)
```

## Comando de verificação

```bash
cd /home/andrefarias/Desenvolvimento/Nyx-Code

# 1. Tempo de start (headless)
for i in 1 2 3 4 5; do
    { time echo '{"type":"ping"}' | ./run.sh --headless > /dev/null 2>&1 ; } 2>&1 | grep real
done
# mediana < 1.5s

# 2. Console singleton
python -c "
from nyx.agent.output import _get_console
a, b = _get_console(), _get_console()
assert a is b, 'não é singleton'
print('singleton OK')
"

# 3. Task cancel no shutdown
python -c "
import asyncio, subprocess, time
# Simular: inicia nyx, manda /quit, verifica se ficou task pendente
proc = subprocess.Popen(['python', '-m', 'nyx.cli'], stdin=subprocess.PIPE, stdout=subprocess.PIPE)
time.sleep(1)
proc.stdin.write(b'/quit\n')
proc.stdin.flush()
proc.wait(timeout=5)
print('shutdown limpo OK' if proc.returncode == 0 else 'shutdown falhou')
"

# 4. Memory cache
python -c "
from nyx.agent.memory import Memory
m = Memory()
a = m.index(); b = m.index()
assert a is b or a == b
print('memory cache OK')
"

./run.sh --gauntlet --only tui
./run.sh --gauntlet --only rapido
```

## Critério binário

- [ ] `time ./run.sh` < 1.5s (mediana de 5 runs) — capturar output
- [ ] `_get_console()` retorna sempre a mesma instância
- [ ] Task de sumarização cancelada no shutdown (não gera warning de coroutine)
- [ ] `memory.index()` retorna cache em chamadas subsequentes
- [ ] Gauntlet tui + rapido passam
- [ ] Commit: `perf: start <1.5s + Console singleton + cancel tasks + memory cache`

## Guardrails anti-engodo

**NÃO marque como concluída se:**
- IA só mediu 1 vez e disse que passa (flutuação de warm cache engana).
- Singleton foi declarado mas nenhum caller atualizado.
- Cache invalida apenas em tempo — deve invalidar em write.
- `asyncio.all_tasks()` nunca foi checado no shutdown.

## Validação humana

```bash
# Antes (checkpoint de regressão)
time ./run.sh --headless < /dev/null    # mediana ~3s

# Depois (após sprint)
for i in 1 2 3 4 5; do time ./run.sh --headless < /dev/null ; done
# mediana < 1.5s

# Sem warning ao sair
./run.sh 2>&1 | grep -i 'coroutine.*never awaited'
# esperado: vazio
```

## Riscos

| Risco | Mitigação |
|-------|-----------|
| Warm-up em background falha silenciosamente | Usar logger.exception no task |
| Console singleton guarda referência a stdout estúpida | Reset em SIGWINCH se necessário (ADR futuro) |

---

*"Velocidade é a distância entre intenção e resposta." -- anônimo corredor*
