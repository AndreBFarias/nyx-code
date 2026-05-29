# AUDIT_LAYOUT_2026_05_28 -- Auditoria do layout TUI Nyx-Code vs Luna

Sessão: 2026-05-28
Modelo: Opus 4.7 (1M, fast=true, /effort max)
Escopo: caminho default da REPL (prompt_toolkit / `nyx/agent/repl_app.py`) comparado
ao layout do projeto Luna (`/home/andrefarias/Desenvolvimento/Luna`, Textual puro).

## 1. Sumário executivo

A imagem reportada pelo usuário mostra **3 bugs estruturais** todos no caminho
default `prompt_toolkit` da REPL (`repl_app.py`):

| ID | Bug                                                | Sintoma na captura                                            |
|----|----------------------------------------------------|---------------------------------------------------------------|
| L1 | Toolbar inferior empilhada (3-4 cópias persistidas) | Rodapé mostra 4 linhas de bottom-toolbar, 3 com "executando"  |
| L2 | Banner não fica fixo                               | Banner some quando a conversa rola; topo da tela "limpo"      |
| L3 | Scrollbar inerte                                   | Barra desenhada na lateral direita não responde a roda/clique |

Causa-raiz comum a todos: a arquitetura `prompt_toolkit + full_screen=True +
HSplit + ScrollbarMargin` não foi desenhada para o padrão "chat persistente com
rolagem grande + banner fixo", e a sub-sprint 249 (UX-COCKPIT-FLASH-PRETO-01)
que tentou consertar a sintaxe via in-app está marcada CONCLUIDA mas **a
validação visual no ambiente real do usuário ficou pendente** (Checkpoint.md,
linha 23). O projeto **já decidiu** migrar para Textual (ADR/ONDA-30 fez
scaffold + 4 widgets + dispatch opt-in via `NYX_TUI_TEXTUAL=1`), mas a
ONDA-31 nunca completou o cutover. O Luna é a referência canônica de Textual
puro e seu CSS `templo_de_nyx.css` (sim, esse é o nome do template no
repositório do Luna) já mostra o padrão alvo.

**Recomendação:** migrar para Textual usando Luna como template. Resolve os 3
bugs estruturalmente, dá continuidade ao trabalho já iniciado, e evita
investir em arquitetura abandonada.

## 2. Estado atual da arquitetura

### 2.1 Dois caminhos coexistindo

`nyx/cli.py:322-325` decide entre dois caminhos a cada boot:

```python
_legacy_env = os.environ.get("NYX_LEGACY_REPL", "").strip() == "1"
use_application = (
    sys.stdin.isatty() and not _legacy_env and prompt_session is not None
)
```

- **`use_application=True` (default em TTY real)** -> usa `Application`
  full-screen do prompt_toolkit (`nyx/agent/repl_app.py:208 build_app`).
  **Este é o caminho da captura reportada.**
- **`use_application=False` (fallback legacy)** -> usa `PromptSession` com
  `bottom_toolbar` callable. Per-turn `prompt_async()`.

Adicionalmente, `cli.py:419-439` adiciona um terceiro caminho **opt-in**:

```python
_tui_textual = os.environ.get("NYX_TUI_TEXTUAL", "").strip() == "1"
if use_application and _tui_textual:
    from nyx.agent.tui.app import NyxTUI
    nyx_tui_app = NyxTUI(...)
    tui_result = await nyx_tui_app.run_async()
```

Esse caminho usa a app Textual nova de `nyx/agent/tui/app.py` (179L, scaffold
da ONDA-30), mas a integração com o `AgentLoop` **não está feita**: o
`_on_input_submit` (linha 117) só registra o texto no OutputWidget sem
processar via `agent.run()`. É shell estrutural, não app funcional.

### 2.2 Layout HSplit do prompt_toolkit (caminho default)

`repl_app.py:648-656`:

```python
layout = Layout(
    HSplit([
        output_window,      # FormattedTextControl(ANSI), ScrollbarMargin
        separator_window,   # 1 linha "─"
        input_window,       # BufferControl, Dimension(min=5, max=5)
        toolbar_window,     # FormattedTextControl(toolbar_callable)
    ]),
    focused_element=input_window,
)
app = Application(
    layout=layout,
    key_bindings=kb,
    full_screen=True,
    style=_build_style(),
    mouse_support=True,
)
```

Banner é pré-populado **dentro do output_buffer** (cli.py:477):

```python
append_to_buffer(repl_output_buffer, _banner_str + "\n")
```

Toolbar é um callable que lê app_state e devolve `FormattedText`
(`_build_toolbar_callable` em `repl_app.py:92-161`). Renderizado a cada
`invalidate()` do app.

## 3. Bugs detalhados

### L1 -- Toolbar inferior empilhada (3-4 cópias persistidas)

**Sintoma (captura do usuário):**

```
ctx 0% | iter 0 | lidos 0 | modif 0 | o cold |   shift+tab: normal/plan/sudo/bypass
9  (1162/12000tok) | iter 0 | lidos 0 | modif 0 | o w rml ... executando (Ctrl+C cancela) | shift+tab: ...
71 ... | executando (Ctrl+C cancela) | shift+tab: ...
84 ... | executando (Ctrl+C cancela) | hift+tab: normal/plan/sudo/bypass
```

A linha 1 é a toolbar **atual** (sem inflight). As linhas 2-4 são **snapshots
preservados de turnos anteriores** com `executando (Ctrl+C cancela)` ativo --
caracteres do `shift+tab` cortados na borda direita do terminal sugerem
re-rendering parcial.

**Código suspeito:**

1. `repl_app.py:289-296` -- caminho fallback **per-turn** que ainda existe:
   ```python
   # Fallback legacy (per-turn run_async): exit com o texto submetido.
   try:
       app = get_app()
       app.exit(result=buf.text)
   ```
   Quando a sprint 249 foi adicionada, este fallback ficou para o caso de
   `on_submit` não estar registrado. Mas se por algum motivo
   `app_state["on_submit"]` não estiver setado em algum turno (ex.: race com
   `set_repl_app_output`), o turno cai aqui -> Application sai -> ao voltar
   via `run_async()` novamente, o frame anterior já foi flushed no main
   screen do terminal.

2. `repl_app.py:471-484` -- Ctrl+Q faz `app.exit(result="__quit__")`. Cada
   exit em modo `full_screen=True` faz o terminal sair do alternate buffer.
   Se o exit não restaurar o alternate de forma limpa antes do próximo
   `run_async`, deixa rastro.

3. `cli.py:617-749 process_turn` -- coroutine in-app. Mas dentro dela,
   `handle_command` (linha 647) faz dispatch de slash commands com
   `redirect_stdout_to_emit()` (linha 679). Se algum handler dentro do
   dispatch lança/captura exceção e o redirect não restaura stdout direito,
   o `_emit` cai no fallback `sys.stdout.write` (`output.py:231`). Isso
   imprime no terminal main screen, deixando uma cópia da toolbar.

**Hipótese mais provável:** o spinner em modo buffer (output.py:485-499)
escreve a linha "aquecendo" via `_emit` no output_buffer. Mas há outro path:
`output.py:131-151 _StdoutToBufferProxy.write` rotea quando
`repl_app_active=True`. Se `repl_app_active` for resetado por algum erro
(`app_state["repl_app_active"] = False` em cli.py:601 quando build_app
falha), o stdout volta a ir para terminal cru -> cada turno deixa snapshot
parcial.

**Confirmação:** a sprint 249 foi marcada CONCLUIDA, mas o Checkpoint.md:23
diz literalmente:

> "validação VISUAL de 260 SCROLL + 249 FLASH no ambiente REAL do usuário
> (claude-in-chrome estava DESCONECTADO -- igual ao 247; validei só
> estruturalmente)"

A captura do usuário **é exatamente essa validação visual pendente**, e o
resultado mostra que 249 **não funcionou** -- temos toolbar empilhada, que é
o sintoma do per-turn `app.exit()` que 249 deveria ter eliminado.

### L2 -- Banner não fica fixo

**Sintoma:** ao crescer a conversa, o banner some do topo. A imagem ainda
mostra ele porque a conversa é curta ("Olá / Boa tarde"), mas a rolagem
qualquer leva ele para fora da viewport.

**Código:** `cli.py:474-481` pré-popula banner **dentro** do output_buffer:

```python
_banner_str = _bb(model, agent.tools_count, PROJECT_ROOT.name, settings=settings)
append_to_buffer(repl_output_buffer, _banner_str + "\n")
app_state["_banner_str"] = _banner_str
```

`repl_app.py:648-656` (HSplit) tem `output_window` ocupando todo o espaço
acima do separator/input/toolbar. O banner está no fluxo do scroll do
output, não em uma Window separada.

O blink timer (`cli.py:497-591`) reescreve o **prefixo** do output_buffer
com novo banner a cada 0.5s:

```python
current = repl_output_buffer.text
prefix_len = len(prev_banner) + 1
if current.startswith(prev_banner):
    suffix = current[prefix_len:]
    novo = new_banner + "\n" + suffix
    repl_output_buffer.document = Document(text=novo, cursor_position=len(novo))
```

Isso mantém o banner **vivo no buffer**, mas não muda sua **posição visível**.
Se o output_window rolou para baixo, o banner já está fora da viewport e o
blink é invisível.

**Comparação Luna:** `luna_app.py:265-296` compõe banner em
`Vertical(id="ascii-container")` que tem `width: 44%; height: 100%; dock:
left` no CSS `templo_de_nyx.css:16-27`. O banner vive em um **container
distinto** do `#chat-area` (que tem `VerticalScroll`). Rolagem do chat não
afeta o banner.

### L3 -- Scrollbar inerte

**Sintoma:** barra desenhada na lateral direita do output_window não
responde a roda do mouse nem a clique-arrastar.

**Código:** `repl_app.py:629` adiciona `ScrollbarMargin`:

```python
output_window = _ScrollableOutputWindow(
    content=output_control,
    wrap_lines=True,
    always_hide_cursor=True,
    style="class:output",
    get_vertical_scroll=_scroll_to_bottom,
    right_margins=[ScrollbarMargin(display_arrows=True)],
)
```

Problemas observados:

1. **`ScrollbarMargin` em prompt_toolkit é puramente visual.** Ela renderiza
   uma barra proporcional ao scroll, mas não captura mouse events. Não
   suporta click-to-jump nem drag.

2. **Mouse wheel só funciona sobre o output_window.** `_ScrollableOutputWindow._mouse_handler`
   (repl_app.py:599-607) intercepta SCROLL_UP/SCROLL_DOWN, mas só quando o
   mouse está sobre a área dele. Quando o mouse passa sobre o input
   (focado), cai em `_NoScrollInputWindow` (linhas 614-621) que
   **engole o scroll silenciosamente** -- usuário rola e nada acontece.

3. **`get_vertical_scroll=_scroll_to_bottom`** força auto-scroll mesmo
   quando `_user_scrolled_up=True`, **subtraindo** o offset (linha 583):
   ```python
   step = max(1, visible - 1) if visible else 1
   return max(0, bottom - offset * step)
   ```
   Isso é uma simulação manual de scrollback. Cada PgUp incrementa offset.
   Mas o cálculo `offset * step` é em **páginas**, então roda do mouse
   (que gera SCROLL_UP, não PgUp) ainda incrementa offset por 1, que é
   multiplicado por `step` (~30 linhas) -> uma única tick da roda pula
   30 linhas. UX confuso.

4. **Reset em accept_handler** (linha 260-261):
   ```python
   app_state["_user_scrolled_up"] = False
   app_state["_output_scroll_offset"] = 0
   ```
   Cada Enter zera o scroll. Se usuário rolou para revisar conversa
   anterior e digita algo, perde a posição.

**Comparação Luna:** `templo_de_nyx.css:102-112`:

```css
#chat-area {
    height: 1fr;
    border: heavy #8A6FD1;
    background: #0A0E14;
    scrollbar-background: #0A0E14;
    scrollbar-color: #2A2E3E;
    scrollbar-color-hover: #8A6FD1;
    scrollbar-color-active: #D4A95C;
}
```

Mais `luna_app.py:284`: `yield VerticalScroll(id="chat-list")`. Uma linha.
`VerticalScroll` é widget nativo do Textual que gerencia scrollbar com
mouse wheel, click-to-jump, drag, PgUp/PgDn, Home/End -- tudo de graça.

## 4. Comparação Luna vs Nyx

| Aspecto                       | Luna (Textual)                                          | Nyx default (prompt_toolkit)                                          |
|-------------------------------|---------------------------------------------------------|-----------------------------------------------------------------------|
| Layout container raiz         | `Horizontal()` 2 colunas (44%/56%)                      | `HSplit([output, sep, input, toolbar])`                               |
| Banner                        | `BannerGlitchWidget` em `#ascii-container` (dock left)  | Texto append no output_buffer (rola com conversa)                     |
| Banner stays put?             | Sim (container distinto)                                | Não (parte do scroll)                                                 |
| Chat area                     | `VerticalScroll(id="chat-list")` em `#chat-area`        | `_ScrollableOutputWindow` (Window subclasse)                          |
| Mensagens                     | Widgets `ChatMessage` montados                          | Texto ANSI no buffer + box drawing chars                              |
| Scrollbar funcional?          | Sim (nativa Textual: wheel, click, drag, PgUp/PgDn/End) | Parcial (apenas wheel sobre output + PgUp/PgDn)                       |
| Scrollbar visual              | CSS `scrollbar-color`/`-hover`/`-active`                | `ScrollbarMargin(display_arrows=True)` -- decorativa                  |
| Input                         | `Input` widget em `#input-container`                    | `BufferControl` em Window altura 5                                    |
| Bottom toolbar                | Sem (não existe no Luna)                                | `FormattedTextControl(callable)` + 1 Window                           |
| Lifecycle por turno           | App roda continuamente, eventos disparam handlers       | Per-turn `prompt_async()` legacy OU `create_background_task` (sprint 249) |
| Multi-turno deixa rastro?     | Nunca (Textual driver gerencia render)                  | Sim (toolbar empilhada quando app sai/volta)                          |
| CSS lines                     | 200 (templo_de_nyx) + outras entidades                  | 50 (nyx.tcss, ainda placeholder)                                      |
| Mouse handlers                | Nativos do Textual                                      | Subclasses custom de Window com `_mouse_handler`                      |
| Foco                          | Textual auto-gerencia                                   | `focused_element=input_window` fixo                                   |

## 5. Estimativa de esforço

### Caminho A -- Migrar para Textual usando Luna como template

**Sprints estimadas: 6-7**, ~2-3 sessões fortes (Opus 4.7 max).

| ID                                 | Escopo                                                                                                | Risco | Dependências   |
|------------------------------------|-------------------------------------------------------------------------------------------------------|-------|----------------|
| `TUI-CSS-LUNA-ADOPT-01`            | Expandir `nyx.tcss` (50L -> ~200L) seguindo `templo_de_nyx.css`. Add scrollbar styles, dock top/bottom | Baixo | -              |
| `TUI-CHAT-MESSAGE-WIDGET-01`       | Widget `ChatMessage(role, content)` análogo a Luna `src/ui/widgets.py:ChatMessage`. User box turquesa, Nyx box roxo | Médio | CSS-LUNA       |
| `TUI-VERTICAL-SCROLL-ADOPT-01`     | Trocar `OutputWidget(RichLog)` por `VerticalScroll` + ChatMessage mountado. Scrollbar nativa.         | Baixo | CHAT-MESSAGE   |
| `TUI-BANNER-DOCK-TOP-01`           | Banner sai do output, vai para Widget `BannerWidget` com `dock: top` (ou container distinto à la Luna) | Baixo | CSS-LUNA       |
| `TUI-AGENT-INTEGRATION-01`         | `NyxTUI._on_input_submit` chama `agent.run()` em `run_worker(thread=True)`. Bridge `on_token`/`on_tool` para Output. | Alto  | CHAT-MESSAGE   |
| `TUI-DEFAULT-FLIP-01`              | Flip default: `use_application` agora dispara NyxTUI; legacy via `NYX_LEGACY_REPL=1`                  | Médio | AGENT-INT      |
| `TUI-PROMPT-TOOLKIT-DEPRECATE-01`  | Marcar `repl_app.py` como deprecated; remover blink_loop, _StdoutToBufferProxy, _RedirectStdoutToEmit | Baixo | DEFAULT-FLIP   |

**Ganhos estruturais:**
- Banner fixo de graça (`dock: top`)
- Scrollbar nativa (`VerticalScroll`)
- Toolbar nunca empilha (App vive de start a end, Textual gerencia render)
- CSS único maintainable
- Alinhamento com Luna -> trocar tema é só CSS

**Riscos:**
- `AGENT-INTEGRATION-01` é o maior: precisa bridge entre `AgentLoop` (que
  hoje fala com prompt_toolkit via callbacks `on_token`/`on_tool`) e Textual
  worker threads. Luna fez isso via `ThreadingController` (`src/controllers/`).
- Slash command dispatch precisa adaptar (hoje usa `redirect_stdout_to_emit`,
  precisa virar `app.call_from_thread(output.write_*)`).

### Caminho B -- Conserto cirúrgico do prompt_toolkit atual

**Sprints estimadas: 4-5**, ~1-2 sessões.

| ID                              | Escopo                                                                  | Risco | Comentário                                          |
|---------------------------------|-------------------------------------------------------------------------|-------|-----------------------------------------------------|
| `TUI-APP-SINGLE-INSTANCE-01`    | Garantir `process_turn` sempre via `create_background_task`; nunca exit | Alto  | É a re-execução de 249 que já foi marcada CONCLUIDA |
| `TUI-BANNER-FIXED-HSPLIT-01`    | Banner em Window separada acima de output_window (HSplit 4 -> 5)        | Médio | Quebra paridade legacy (banner some no fallback)    |
| `TUI-MOUSE-SCROLL-GLOBAL-01`    | Mouse scroll sobre input redirecionado para output_window               | Médio | Engenharia em cima de `_NoScrollInputWindow`        |
| `TUI-TOOLBAR-DEDUP-01`          | Eliminar `_emit` -> stdout fallback durante turno; alt-buffer cleanup   | Alto  | Investigação profunda                               |

**Ganhos:**
- Diff menor
- Sem risco de regressão de testes existentes (Gauntlet)

**Perdas:**
- Investimento em arquitetura cujo cutover já foi planejado (ONDA-30/31)
- Bugs futuros do prompt_toolkit (alt-buffer, mouse, scrollbar) voltam
- Não alinha com diretriz "use Luna como padrão"

## 6. Recomendação

**Caminho A: migrar para Textual usando Luna como template.**

Razões:

1. **A decisão arquitetural já foi tomada.** ONDA-30 fez scaffold (5 sprints
   CONCLUIDAS: 197, 198, 202, 205, 206, 207). A ONDA-31 deveria ter feito
   cutover mas parou. Conservar prompt_toolkit é manter o purgatório.

2. **Luna é referência canônica.** O usuário disse "use ela como padrão".
   `templo_de_nyx.css` é literalmente um template pronto para Nyx.
   `luna_app.py` mostra o padrão de compose, mensagens, scroll.

3. **Os 3 bugs são estruturais.** Conserto no prompt_toolkit não muda o fato
   de que `ScrollbarMargin` é decorativa, banner está no fluxo do scroll, e
   `full_screen=True + run_async per-turn` é frágil. Textual resolve por
   construção.

4. **Esforço comparável.** A=6-7 sprints, B=4-5. A diferença (~2 sprints) é
   investimento que se paga -- arquitetura limpa, código pequeno, CSS único.

5. **Risco controlado.** Caminho A mantém prompt_toolkit como fallback
   (`NYX_LEGACY_REPL=1`) até validação visual completa da Textual no
   ambiente real do usuário. Sem deletar nada antes de validar.

## 7. Próximos passos sugeridos

Se o usuário aprovar caminho A:

1. Brainstorming -> design doc curto consolidando decisões abertas:
   - Qual cor base para Nyx? `templo_de_nyx.css` usa `#8A6FD1` (violeta). O
     `nyx.tcss` atual usa `#9D4EDD`. Manter o atual ou adotar Luna?
   - Manter layout 2 colunas estilo Luna (44/56 ascii + chat) ou layout
     1 coluna estilo CLI de codigo agentico? A captura do usuário sugere 1 coluna.
   - Toolbar inferior mantém? Luna não tem toolbar (preferência por
     `welcome-pane` com info). Nyx tem 6 campos (ctx/iter/lidos/modif/state/mode).
2. Spec da SPRINT-NOVA-01 (TUI-CSS-LUNA-ADOPT-01)
3. Writing-plans para sequência das 6-7 sprints
4. Execução em ordem topológica

Se o usuário escolher caminho B:

1. Reproduzir L1 com instrumentação (env var `NYX_DEBUG_TOOLBAR=1` que loga
   cada chamada de `_accept`/`process_turn`/`app.exit` para identificar
   qual disparo deixa rastro)
2. SPRINT-NOVA TUI-APP-SINGLE-INSTANCE-02 -- versão hardened da 249
3. Em paralelo: SPRINT-NOVA TUI-MOUSE-SCROLL-GLOBAL-01

## 8. Apêndice -- mapeamento file:line

### Caminho default (prompt_toolkit)

- `nyx/cli.py:322-325` -- decisão `use_application`
- `nyx/cli.py:419-439` -- dispatch opt-in NyxTUI (env `NYX_TUI_TEXTUAL=1`)
- `nyx/cli.py:451-484` -- build_app + banner pré-populado + routing global
- `nyx/cli.py:497-591` -- banner blink loop (re-escreve prefixo a cada 0.5s)
- `nyx/cli.py:617-749` -- `process_turn` (corpo do turno como coroutine)
- `nyx/agent/repl_app.py:92-161` -- `_build_toolbar_callable` (bottom toolbar)
- `nyx/agent/repl_app.py:208-676` -- `build_app` (Application + Layout)
- `nyx/agent/repl_app.py:255-298` -- `_accept` (in-app vs per-turn fallback)
- `nyx/agent/repl_app.py:289-296` -- fallback per-turn (`app.exit(result=...)`)
- `nyx/agent/repl_app.py:471-484` -- Ctrl+Q sentinel `__quit__`
- `nyx/agent/repl_app.py:512-543` -- `_scroll_up/down_step` + `_scroll_reset`
- `nyx/agent/repl_app.py:570-588` -- `_scroll_to_bottom` (auto-scroll + offset)
- `nyx/agent/repl_app.py:599-621` -- `_ScrollableOutputWindow` + `_NoScrollInputWindow`
- `nyx/agent/repl_app.py:623-646` -- output_window, separator, input_window, toolbar_window
- `nyx/agent/repl_app.py:663-669` -- Application(full_screen=True, mouse_support=True)
- `nyx/agent/output.py:121-194` -- `_StdoutToBufferProxy` + `_RedirectStdoutToEmit`
- `nyx/agent/output.py:207-245` -- `_emit` (routing buffer vs stdout)
- `nyx/agent/output.py:485-499` -- spinner buffer mode (escreve "aquecendo" no buffer)

### Caminho Textual opt-in (incompleto)

- `nyx/agent/tui/app.py:40-179` -- `NyxTUI` class
- `nyx/agent/tui/app.py:117-128` -- `_on_input_submit` (sem agent integration)
- `nyx/agent/tui/styles/nyx.tcss:1-50` -- CSS placeholder
- `nyx/agent/tui/widgets/banner.py` -- `BannerWidget` (refresh local, sem race)
- `nyx/agent/tui/widgets/output.py:21-66` -- `OutputWidget(RichLog)` com write_user/write_assistant/write_tool
- `nyx/agent/tui/widgets/input.py` -- `InputWidget` com slash_completer
- `nyx/agent/tui/widgets/toolbar.py:32-128` -- `Toolbar(Static)` com 6 reactives

### Referência Luna

- `/home/andrefarias/Desenvolvimento/Luna/src/app/luna_app.py:250-296` -- `compose()` Horizontal + 2 colunas
- `/home/andrefarias/Desenvolvimento/Luna/src/app/luna_app.py:284` -- `yield VerticalScroll(id="chat-list")`
- `/home/andrefarias/Desenvolvimento/Luna/src/app/luna_app.py:421-466` -- `add_chat_entry` (mount ChatMessage + scroll_end)
- `/home/andrefarias/Desenvolvimento/Luna/novo_css/templo_de_nyx.css:102-112` -- `#chat-area` com scrollbar nativa
- `/home/andrefarias/Desenvolvimento/Luna/novo_css/templo_de_nyx.css:114-125` -- `#input-container`
- `/home/andrefarias/Desenvolvimento/Luna/novo_css/templo_de_nyx.css:138-162` -- mensagens user/entity
