## 0. SPEC (machine-readable)

```yaml
sprint:
  id: I-03
  title: "Mensagens inline [nyx] na TUI Luna"
  touches:
    - path: Luna/src/app/event_handlers.py
      reason: "Handler que consome stdout JSON do subprocess do Nyx-Code"
    - path: Luna/src/skills/code_agent/loop.py
      reason: "Encadear respostas do adapter no fluxo da TUI"
    - path: Luna/src/skills/code_agent/nyx_adapter.py
      reason: "Expor stream de eventos para o handler consumir"
    - path: scripts/gauntlet/fases/i_inline.py
      reason: "Nova fase com 2 testes de formatação"
    - path: scripts/gauntlet/nyx_gauntlet.py
      reason: "Registrar fase i_inline"
  n_to_n_pairs:
    - ["Luna/src/app/event_handlers.py", "Luna/src/skills/code_agent/nyx_adapter.py"]
  forbidden:
    - "Quebrar formatação de mensagens de outras entidades da Luna (kernel, augur, ...)"
    - "Alterar o protocolo JSON do Nyx-Code headless (ele já é contrato I-01)"
    - "Usar cores fora da paleta Nyx (#00D4AA primário, #FF6B6B erro)"
  tests:
    - cmd: "./run.sh --gauntlet --only i_inline"
      timeout: 60
  acceptance_criteria:
    - "Respostas do Nyx aparecem com prefixo [nyx] na TUI"
    - "Tool calls mostram [nyx:tool] nome(args) -> resultado"
    - "Erros formatados como [nyx:erro] em vermelho"
    - "Outras entidades da Luna continuam funcionais"
    - "Acentuação PT-BR correta"
```

> Executar antes de começar: I-02 deve estar CONCLUIDA. Verificar formato de eventos emitidos por outras entidades (kernel/augur) para manter consistência visual.

---

# Sprint I-03 -- Mensagens inline [nyx] na TUI Luna

**Status:** DELEGADA (2026-04-16) -- transferida para o repo Luna
**Delegada para:** `Luna/dev-journey/06-sprints/producao/infra/SPRINT_INFRA53_NYX_INLINE_TUI.md`
**Motivo:** toca arquivos em `Luna/src/ui/`. Sprint no repo correto com código pronto pra copiar.
**Data:** 2026-04-16
**Prioridade:** MÉDIA
**Tipo:** Integração
**Dependências:** I-02
**Desbloqueia:** --

---

## Problema / Contexto

Depois que I-02 troca o backend do code agent, as respostas do Nyx-Code saem em JSON pelo stdout do subprocess (protocolo I-01). A TUI da Luna precisa parsear esse JSON e exibir as mensagens formatadas com prefixo `[nyx]`, similar aos prefixos `[kernel]` e `[augur]` já existentes.

Sem esse handler, as respostas aparecem cruas ou não aparecem na TUI do usuário.

## Implementação

### Fase 1: Formato de mensagens na TUI

Baseado em entidades existentes da Luna:

```
[nyx] Lendo arquivo README.md...
[nyx:tool] read_file(README.md) -> 120 linhas
[nyx:tool] edit_file(README.md) -> 3 linhas modificadas
[nyx] Tarefa concluída: arquivo atualizado com documentação.
[nyx:erro] Permission denied em /etc/passwd
```

Cores (paleta Nyx, já usada no run.sh/install.sh):
- `[nyx]` — primária cyan/teal `#00D4AA`
- `[nyx:tool]` — accent cinza `#6C7A89` (secundária)
- `[nyx:erro]` — vermelho `#FF6B6B`

### Fase 2: Stream de eventos no adapter

Em `Luna/src/skills/code_agent/nyx_adapter.py`, expor um gerador assíncrono:

```python
async def stream_events(self) -> AsyncIterator[dict]:
    """Lê stdout do subprocess linha a linha, yield de cada evento JSON."""
    while self.proc and self.proc.stdout:
        line = await asyncio.to_thread(self.proc.stdout.readline)
        if not line:
            break
        try:
            yield json.loads(line.strip())
        except json.JSONDecodeError:
            logger.warning("Linha não-JSON do Nyx: %r", line)
```

### Fase 3: Handler em `event_handlers.py`

```python
async def handle_nyx_event(event: dict, ui: TuiContext) -> None:
    t = event.get("type", "")
    if t == "response":
        ui.print_entity("nyx", event.get("text", ""), style="primary")
    elif t == "tool_use":
        nome = event.get("name", "?")
        args_str = _summarize_args(event.get("args", {}))
        resultado = event.get("result_summary", "")
        ui.print_entity("nyx:tool", f"{nome}({args_str}) -> {resultado}", style="dim")
    elif t == "error":
        ui.print_entity("nyx:erro", event.get("message", "erro desconhecido"), style="error")
    elif t == "done":
        pass  # final do ciclo, sem output
    else:
        logger.debug("Evento Nyx desconhecido: %s", t)
```

### Fase 4: Integrar no loop

Em `Luna/src/skills/code_agent/loop.py`:

```python
async def run_nyx_turn(prompt: str, ui: TuiContext):
    adapter = get_adapter()
    await adapter.send_request(prompt)
    async for event in adapter.stream_events():
        await handle_nyx_event(event, ui)
        if event.get("type") == "done":
            break
```

### Fase 5: Testes Gauntlet (fase `i_inline`)

| ID | Nome | Validação |
|----|------|-----------|
| I3-01 | Format response | Input `{"type":"response","text":"Feito."}` → saída contém `[nyx]` e `Feito.` |
| I3-02 | Format tool_use | Input `{"type":"tool_use","name":"read_file","args":{"path":"a.py"},"result_summary":"10 linhas"}` → saída contém `[nyx:tool]` e `read_file(path=a.py) -> 10 linhas` |

Testes são unitários do handler (sem TUI real): invocam `handle_nyx_event` com um `ui` fake e validam o que foi "printado".

### Fase 6: Streaming de tokens (fora do escopo)

Se no futuro o Nyx-Code suportar streaming de tokens via headless, o handler já está estruturado para receber `{"type":"token","text":"..."}`. Esta sprint NÃO implementa streaming.

## Verificação

- [ ] `stream_events` funciona com stdout do subprocess
- [ ] Handler formata `response`, `tool_use`, `error` corretamente
- [ ] TUI da Luna mostra mensagens com cores da paleta Nyx
- [ ] Outras entidades continuam funcionais
- [ ] Gauntlet fase `i_inline` passa 2/2

---

*"Clareza é a cortesia do filósofo." -- Ortega y Gasset*
