## 0. SPEC (machine-readable)

```yaml
sprint:
  id: TUI-02
  title: "Boxes: frame persistente do input, multiline, image paste, eco de mensagem, tool result colapsável"
  touches:
    - path: nyx/cli.py
      reason: "Migrar de PromptSession.prompt_async para Application (layout com frame)"
    - path: nyx/agent/input_frame.py
      reason: "Novo módulo: layout prompt_toolkit com Frame + multiline + image paste"
    - path: nyx/agent/output.py
      reason: "render_user_input (eco), render_assistant_start/end, render_tool_result"
    - path: nyx/agent/loop.py
      reason: "Novo callback on_tool_result expondo output pra UI"
    - path: nyx/agent/clipboard.py
      reason: "Novo módulo: captura de imagem via xclip, salva em ~/.nyx/pastes/"
  n_to_n_pairs:
    - "Se TAG_STYLES ganha 'user_box' então TAG_LABELS também"
    - "Placeholder [Image #N] no texto do user input TAMBÉM aparece no history salvo"
  forbidden:
    - "Render do frame se terminal <80 cols (fallback pra prompt simples)"
    - "Quebrar streaming de tokens (continuam saindo inline)"
    - "Bloquear input se xclip não estiver disponível (image paste degrada silenciosa)"
    - "Enviar imagem pro modelo (qwen3:4b é text-only; só metadata [Image #N])"
  tests:
    - cmd: "./run.sh --gauntlet --only rapido"
      timeout: 120
    - cmd: "manual: ./run.sh, digitar texto, ver frame; Ctrl+J quebra linha; enviar; ver eco"
      timeout: 60
    - cmd: "manual: copiar imagem, Ctrl+Shift+V, verificar [Image #1] no input e arquivo em ~/.nyx/pastes/"
      timeout: 60
    - cmd: "manual: resize -s 24 60, ver fallback sem frame"
      timeout: 60
  acceptance_criteria:
    - "Frame persistente ╭─╮ em volta do campo de input enquanto usuário digita"
    - "Ctrl+J insere quebra de linha (multiline), Enter envia"
    - "Ctrl+Shift+V captura imagem do clipboard, salva em ~/.nyx/pastes/, insere '[Image #N]' no input"
    - "Após Enter, mensagem enviada aparece ecoada num box ╭─ você ─╮"
    - "Resposta do assistant renderizada com prefixo 'Nyx\\n───' (sem box, streaming inline)"
    - "Tool calls: ' nome(arg)' + '    └─ resumo' (1 linha do resultado)"
    - "Ctrl+O expande última tool call inline (se couber na sprint)"
    - "Terminal <80 cols: fallback sem frame, prompt 'nyx> ' simples"
    - "[Image #N] persiste no histórico salvo em ~/.nyx/sessions/"
    - "Se xclip não instalado, Ctrl+Shift+V não crasha; exibe aviso 'xclip não encontrado'"
    - "Acentuação PT-BR correta em labels (você, pensando, etc)"
```

---

# Sprint TUI-02 -- Boxes: input persistente + multiline + image + eco + tool result

**Status:** CONCLUIDA (header corrigido em MASTER-CLEANUP-02 2026-05-20; presença em concluidos/ implica CONCLUIDA conforme convenção do projeto)
**Data:** 2026-04-17
**Prioridade:** ALTA
**Tipo:** Feature (grande)
**Dependências:** TUI-01
**Desbloqueia:** TUI-03

---

## Problema / Contexto

Após TUI-01 (higiene), a TUI ainda não chega ao padrão Claude Code CLI em dois aspectos:

1. **Input:** hoje usamos `PromptSession.prompt_async()` que imprime linha de prompt (`nyx> `) e coleta texto. Claude Code tem um **frame persistente** em volta do campo de digitação, com tag do branch/contexto e toolbar de atalhos. Também suporta `Ctrl+J` pra quebra de linha e `Ctrl+Shift+V` pra colar imagem (mostrando `[Image #N]` como placeholder no texto).

2. **Echo + tool result:** Mock 2 do plano master pede box `╭─ você ─╮` em volta da mensagem enviada (eco visual), prefixo `Nyx ───` antes do streaming, e `└─ resumo` colapsado após cada tool call. Hoje nada disso existe.

Escopo expandido após feedback em 2026-04-17: usuário pediu o frame persistente, multiline e image paste além do que estava mockado originalmente.

## Referência visual

### Frame persistente (durante digitação)

```
  ┌─────────────────────────────────────────── main ─┐
  │ > Como eu testo a sprint CTX-01?                 │
  │   Segunda linha via Ctrl+J, multiline funciona.  │
  └──────────────────────────────────────────────────┘
  ‣‣ bypass permissions on  ·  ctx 12% · qwen3:4b · /help
```

### Eco após envio

```
  ╭─ você ───────────────────────────────────────────╮
  │ Como eu testo a sprint CTX-01?                   │
  │ Segunda linha via Ctrl+J, multiline funciona.    │
  ╰──────────────────────────────────────────────────╯

   read_file(dev-journey/06-sprints/SPRINT_CTX_01_SUMMARIZER.md)
    └─ 1-40  Sprint CTX-01 -- SessionSummarizer

  Nyx
  ───
  Pra testar, roda ./run.sh --gauntlet --only contexto…
```

### Com imagem colada

```
  ┌──────────────────────────────────────────────────┐
  │ > Olha esse erro [Image #1]                      │
  │   O que você acha?                               │
  └──────────────────────────────────────────────────┘
```

Arquivo físico salvo: `~/.nyx/pastes/2026-04-17_134532_1.png`

## Implementação

### Fase 1 -- Frame persistente do input (prompt_toolkit Application)

Migrar de `PromptSession.prompt_async()` pra uma `Application` com layout custom. Arquivo novo:

- `nyx/agent/input_frame.py`:
  ```python
  from prompt_toolkit import Application
  from prompt_toolkit.buffer import Buffer
  from prompt_toolkit.layout import Layout, HSplit, VSplit, Window
  from prompt_toolkit.layout.controls import BufferControl, FormattedTextControl
  from prompt_toolkit.widgets import Frame
  from prompt_toolkit.key_binding import KeyBindings

  class NyxInputFrame:
      def __init__(self, completer, history, get_ctx_info): ...
      async def ask(self) -> str: ...
  ```
- Layout: `Frame(BufferControl)` + bottom toolbar com dicas + tag do branch git no canto superior.
- Multi-line: `Buffer(multiline=True)`.
- Keybindings: `Enter` submete, `Ctrl+J` insere newline, `Ctrl+D` quit, `Ctrl+O` expand last tool, `Ctrl+Shift+V` paste image.

Fallback: se `console.width < 80` ou `stdout.isatty() is False`, usar `PromptSession.prompt_async` simples sem frame.

### Fase 2 -- Multiline via Ctrl+J

- Keybinding em `input_frame.py`:
  ```python
  @kb.add('c-j')
  def _(event):
      event.app.current_buffer.insert_text('\n')

  @kb.add('enter')
  def _(event):
      event.app.exit(result=event.app.current_buffer.text)
  ```

### Fase 3 -- Image paste (Ctrl+Shift+V)

- `nyx/agent/clipboard.py`:
  ```python
  def capture_clipboard_image() -> Path | None:
      """Tenta ler imagem do clipboard via xclip. Retorna path salvo ou None."""
      # subprocess xclip -selection clipboard -t image/png -o
      # Se sucesso: salva em ~/.nyx/pastes/<timestamp>.png
      # Retorna Path ou None
  ```
- Counter de imagem por sessão: `_image_counter: int = 0`. Incrementa a cada paste.
- Keybinding:
  ```python
  @kb.add('c-@')  # Ctrl+Shift+V mapeia varia; testar
  def _(event):
      path = capture_clipboard_image()
      if path is None:
          # msg na toolbar
          return
      nonlocal _image_counter
      _image_counter += 1
      event.app.current_buffer.insert_text(f'[Image #{_image_counter}]')
      # opcional: armazenar mapping #N -> path em estado da sessão
  ```
- Mapping `image_id -> path` persistido no `CodeSession` pra o histórico registrar.
- Se `xclip` não disponível: aviso silencioso na toolbar, sem crash.

### Fase 4 -- Eco ╭─ você ─╮ pós-envio

- `nyx/agent/output.py`: `render_user_input(text: str, console_width: int | None = None) -> None`
  - Se width >= 80: rich.Panel(text, title="você", border_style=NYX_ACCENT, title_align="left")
  - Senão: `print(f"\n  > {text}\n")` simples
  - Se text contém `[Image #N]`, preservar literal (não expandir)

Chamado em `cli.py` logo após `ask()` retornar, antes de enviar pro agent.

### Fase 5 -- Header do assistant e resultado de tool

- `render_assistant_start()`: imprime `\n  Nyx\n  ───\n` em accent color.
- `render_assistant_end()`: imprime `\n`.
- `render_tool_result(result: str, max_chars: int = 80)`: pega 1ª linha significativa, trunca com `…`, prefixa `    └─ ` em dim.
- `AgentLoop`: novo callback `on_tool_result: Callable[[str, str], None]` (tool_name, result).
- `cli.py`: implementar on_tool_result pra chamar render_tool_result.

### Fase 6 -- Ctrl+O expande última tool

- `AgentLoop`: manter `_last_tool_result: str | None` após cada tool executada.
- Keybinding Ctrl+O em input_frame: `run_in_terminal(lambda: print(_last_tool_result))`.
- Se consumir >50 linhas de código, extrair pra TUI-02b.

## Verificação

```bash
./run.sh
# Esperado durante digitação:
#   ┌──────────────────────── main ─┐
#   │ > meu input aqui              │
#   │                               │
#   └───────────────────────────────┘
# Testar:
# - Digitar "linha 1" [Ctrl+J] "linha 2" Enter
# - Ver eco:
#   ╭─ você ──────────────╮
#   │ linha 1             │
#   │ linha 2             │
#   ╰─────────────────────╯
# - Tool calls:  read_file(...) + └─ resumo
# - Resposta sob "Nyx\n───"
# Copiar imagem qualquer (print screen etc), Ctrl+Shift+V:
# - Input mostra: > [Image #1]
# - Ver ~/.nyx/pastes/ tem o arquivo
# Terminal estreito:
resize -s 24 60
./run.sh
# Esperado: sem frame, prompt "nyx> " simples, eco vira "> texto"
./run.sh --gauntlet --only rapido
```

- [ ] Frame persistente em volta do input (>=80 cols)
- [ ] Ctrl+J insere newline
- [ ] Enter envia (não newline)
- [ ] Ctrl+Shift+V captura imagem, salva, insere [Image #N]
- [ ] xclip ausente não crasha
- [ ] Eco ╭─ você ─╮ após envio
- [ ] Resposta prefixada "Nyx\n───"
- [ ] Tool calls com └─ resumo 1-linha
- [ ] Ctrl+O expande última tool (ou marcado como TUI-02b)
- [ ] Fallback em terminal estreito
- [ ] Acentuação PT-BR
- [ ] Gauntlet rapido passa

---

*"A forma segue a função." -- Louis Sullivan*
