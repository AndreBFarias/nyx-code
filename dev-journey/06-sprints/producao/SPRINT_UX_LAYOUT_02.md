## 0. SPEC

```yaml
sprint:
  id: UX-LAYOUT-02
  title: "Tool calls em cards (start/end, duração, erro) + feedback visual de compactação automática"
  onda: 22
  bloco: 4
  prioridade: ALTA
  tipo: Feature
  dependencias: [UX-LAYOUT-01]
  desbloqueia: [UX-LAYOUT-03]

  touches:
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/agent/output.py
      reason: "Novas funções render_tool_card_start, render_tool_card_end, render_tool_card_error, render_compaction_event"
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/cli.py
      reason: "Callbacks on_tool/on_tool_result usam cards; detecta evento de compactação do agent"
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/agent/loop.py
      reason: "Emite hook on_compaction(delta_tokens, level) quando compacta; cli consome"

  absorve:
    - "O-07 (feedback quando compactação automática roda)"

  forbidden:
    - "Usar emoji"
    - "Card quebra se tool_name tiver caracteres especiais"
    - "Deixar a versão antiga de render_tool_call dead-code (remover após migração)"

  tests:
    - cmd: "python -c 'from nyx.agent.output import render_tool_card_start, render_tool_card_end'"
      deve_passar: true
    - cmd: "./run.sh --gauntlet --only tui"
      deve_passar: true

  acceptance_criteria:
    - "render_tool_card_start(name, args_preview) imprime card aberto com spinner frame"
    - "render_tool_card_end(name, duration_ms, summary, is_error) fecha card com duração"
    - "render_compaction_event(level, tokens_removed) imprime linha discreta estilo '· compactação nível 1: -N tokens'"
    - "AgentLoop emite callback on_compaction(level, tokens_removed) antes/depois de compact_history"
    - "Funções antigas render_tool_call e render_tool_result foram removidas ou marcadas @deprecated"
    - "Gauntlet tui passa"
    - "Screenshot aprovado: card de tool + evento de compactação visíveis"
```

---

# Sprint UX-LAYOUT-02 — Tool cards + evento de compactação

## Contexto

- Absorve O-07 (usuário não percebe quando contexto foi compactado automaticamente).
- Tool call atual é linha única truncada em 80 chars — pouca hierarquia.

## Problema

1. `render_tool_call` e `render_tool_result` não mostram **duração** da tool.
2. Erro de tool é distinguível só por prefixo de string.
3. Compactação automática (quando ctx > threshold) é silenciosa — usuário vê "de repente o contexto caiu".

## Solução

### Card visual (modelo)

```
  ╭─ write_file ────────────────────────────────────── 475b · 0.3s ─╮
  │  path  resumo.md                                                 │
  │  ok    Arquivo criado em /home/.../resumo.md                     │
  ╰──────────────────────────────────────────────────────────────────╯
```

Em execução (card aberto):
```
  ╭─ ⠋ write_file ──────────────────────────────────── escrevendo… ─╮
  │  path  resumo.md                                                 │
  │  ...                                                             │
```

Erro (borda vermelha):
```
  ╭─ read_file ─────────────────────────────── ERRO · 0.1s ─╮
  │  path  /etc/shadow                                       │
  │  erro  Acesso negado: fora do projeto                    │
  ╰──────────────────────────────────────────────────────────╯
```

### Evento de compactação (linha discreta)

```
  · compactação nível 1 aplicada: -1240 tokens (ctx 62% → 38%)
```

Cor: `NYX_MUTED`. Aparece depois do último token do turno, antes do prompt volta.

### `nyx/agent/output.py` — novas funções

```python
def render_tool_card_start(name: str, args_preview: str, spinner_frame: str = "") -> None:
    """Abre card de tool (para renders síncronos, pode ser opcional)."""
    # ... usa BOX_CHARS e ANSI_ACCENT_FG

def render_tool_card_end(
    name: str,
    duration_ms: int,
    summary_line: str,
    is_error: bool = False,
    extra_lines: list[str] | None = None,
) -> None:
    """Fecha card com duração e primeira linha do resultado."""
    border = ANSI_ERROR_FG if is_error else ANSI_ACCENT_FG
    label = "ERRO" if is_error else "ok"
    duration_str = f"{duration_ms}ms" if duration_ms < 1000 else f"{duration_ms/1000:.1f}s"
    # desenha card

def render_compaction_event(level: int, tokens_removed: int, pct_before: int, pct_after: int) -> None:
    print(f"  {ANSI_MUTED_FG}{BULLETS['note']} compactação nível {level}: "
          f"-{tokens_removed} tokens (ctx {pct_before}% → {pct_after}%){ANSI_RESET}")
```

### `nyx/cli.py` — integração

```python
def on_tool(name: str, args: dict) -> None:
    _stop_spinner()
    turn_state["streamed_text"] = ""
    import time as _t
    tool_timers[name] = _t.monotonic()
    args_preview = _format_args_preview(args)
    render_tool_card_start(name, args_preview)

def on_tool_result(name: str, result: str) -> None:
    import time as _t
    started = tool_timers.pop(name, None)
    duration_ms = int((_t.monotonic() - started) * 1000) if started else 0
    is_error = any(result.startswith(p) for p in _ERROR_PREFIXES)
    first_line = next((ln.strip() for ln in result.splitlines() if ln.strip()), "")
    render_tool_card_end(name, duration_ms, first_line, is_error=is_error)

def on_compaction(level: int, tokens_removed: int, pct_before: int, pct_after: int) -> None:
    render_compaction_event(level, tokens_removed, pct_before, pct_after)

# Passar on_compaction ao AgentLoop
agent = AgentLoop(
    ...,
    on_compaction=on_compaction,
)
```

### `nyx/agent/loop.py` — emitir evento

Onde hoje `self._budget.compact_history(self._session)` é chamado, medir antes/depois:

```python
info_before = self._budget.estimate(system_prompt, user_prompt)
pct_before = int(info_before["pct"] * 100)
tokens_before = info_before["total_tokens"]
level = self._budget.get_compaction_level(self._session)
self._budget.compact_history(self._session)
info_after = self._budget.estimate(system_prompt, user_prompt)
pct_after = int(info_after["pct"] * 100)
tokens_removed = tokens_before - info_after["total_tokens"]
if self._on_compaction and tokens_removed > 0:
    self._on_compaction(level, tokens_removed, pct_before, pct_after)
```

Adicionar parâmetro `on_compaction: Callable | None = None` ao construtor de AgentLoop.

### Remover antigos

Após validar cards funcionando, **remover** `render_tool_call` e `render_tool_result` antigos de `output.py`. Se ainda há callers, substituir pelos novos.

## Comando de verificação

```bash
# Funções existem
python -c "from nyx.agent.output import render_tool_card_start, render_tool_card_end, render_compaction_event"

# on_compaction wired
grep -c "on_compaction" nyx/agent/loop.py nyx/cli.py
# esperado: >= 4

# antigos removidos
grep -c "def render_tool_call\|def render_tool_result" nyx/agent/output.py
# esperado: 0

./run.sh --gauntlet --only tui
```

## Critério binário

- [ ] Funções `render_tool_card_start/end` e `render_compaction_event` existem
- [ ] `on_compaction` existe no construtor de AgentLoop
- [ ] `render_tool_call` e `render_tool_result` antigos removidos
- [ ] Erro vs sucesso têm cor distinta
- [ ] Duração mostrada em ms ou s
- [ ] Gauntlet tui passa
- [ ] Teste manual: tool write_file → card fechado com OK; tool read_file em /etc/shadow → card em vermelho
- [ ] Teste manual: sessão longa gera evento de compactação visível
- [ ] Commit: `feat: tool calls em cards + evento visual de compactação`

## Guardrails anti-engodo

**NÃO marque como concluída se:**
- IA adicionou card novo mas deixou render_tool_call velho sendo chamado por cli.py.
- Duração sempre aparece como 0ms (timer quebrado).
- Evento de compactação nunca dispara mesmo em sessão longa — o hook não está sendo chamado.

## Validação humana

```bash
./run.sh
# nyx> crie um arquivo hello.txt com "oi"
# → observar card de tool aparecer com duração
# nyx> leia /etc/shadow
# → card vermelho com erro
# Sessão longa (>30 iterações): ver "compactação nível 1..." aparecer
```

---

*"Feedback imediato é a cortesia básica de qualquer máquina." -- anônimo*
