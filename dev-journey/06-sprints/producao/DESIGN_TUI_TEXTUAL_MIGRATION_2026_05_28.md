# DESIGN -- Migração TUI Nyx-Code para Textual (template Luna)

- Data: 2026-05-28
- Autor: sessão Opus 4.7 (1M, max effort, fast mode)
- Predecessor: `dev-journey/07-reports/AUDIT_LAYOUT_2026_05_28.md`
- Status: APROVADO para writing-plans (decisões consolidadas via brainstorming)

## 1. Motivação

A captura reportada pelo usuário em 2026-05-28 mostrou 3 bugs estruturais no
caminho default da REPL (`nyx/agent/repl_app.py`, prompt_toolkit
`full_screen=True`):

- **L1** -- toolbar inferior empilhada (3-4 cópias persistidas)
- **L2** -- banner não fica fixo (rola junto com a conversa)
- **L3** -- scrollbar inerte (mouse wheel sobre input engolido, ScrollbarMargin decorativa)

Todos os 3 bugs são estruturais à escolha prompt_toolkit + HSplit + banner-no-buffer +
manual scrollbar simulation. O projeto **já decidiu** migrar para Textual: ONDA-30
fez scaffold (5 sub-sprints CONCLUIDAS: 197 SCAFFOLD, 198 OUTPUT, 202 INPUT, 205
BANNER, 206 TOOLBAR, 207 CUTOVER opt-in) + dispatch via env
`NYX_TUI_TEXTUAL=1`. A ONDA-31 prometia cutover real mas nunca completou.

Luna (`/home/andrefarias/Desenvolvimento/Luna`) é referência canônica de Textual
puro. Seu `templo_de_nyx.css` (200L) define paleta+layout+scrollbar prontos.

Este design completa a migração em **7 sprints** com fallback legacy seguro.

## 2. Decisões consolidadas (brainstorming 2026-05-28)

| Decisão                                        | Valor                                                                                                                    |
|------------------------------------------------|--------------------------------------------------------------------------------------------------------------------------|
| Caminho                                        | A -- Migrar para Textual usando Luna como template                                                                       |
| Layout estrutural                              | 1 coluna (banner top + chat 1fr + input bottom + toolbar bottom)                                                         |
| Paleta                                         | Manter atual: NYX_ACCENT #00D4AA (turquesa), NYX_PURPLE #9D4EDD (roxo), NYX_SUCCESS #4ADE80 (preserva ADR-023)           |
| Toolbar inferior                               | Mantida com 6 campos (ctx%, model, iter, lidos, modif, state+glyph, mode)                                                |
| Rollout                                        | 6 sprints de componentes + 1 de deprecate; fallback `NYX_LEGACY_REPL=1` durante transição                                |
| Modais (`run_select_modal`)                    | ScreenModal Textual nativo entra na sprint dedicada (não fica para depois)                                               |
| Deprecate                                      | Deletar arquivos legacy completamente (~800L) na última sprint após validação visual                                     |

## 3. Arquitetura alvo

### 3.1 Árvore de composição

```
NyxTUI (App)
├── BannerWidget (dock: top, height: auto)
│   ├── render(): $ nyx.code{cursor} | MODELO {m} | TOOLS {t} | COMANDOS {c} | MEMÓRIA {mem}
│   └── set_interval(0.5, _toggle_cursor)  # blink local, sem app.invalidate global
├── ChatScroll = VerticalScroll(id="chat")  # height: 1fr (ocupa middle)
│   ├── ChatMessage role=user                # turquesa, border-left heavy
│   ├── ChatMessage role=assistant           # roxo, border-left heavy
│   ├── ChatMessage role=tool                # dim, sem borda
│   └── ChatMessage role=system              # dim italic, info de boot/error
├── InputWidget (dock: bottom, height: 5)
│   ├── TextArea multiline
│   └── slash_completer (já existe em widgets/input.py)
└── Toolbar (dock: bottom, height: 1)
    └── reactive props (já existe em widgets/toolbar.py)
        + 1 reactive nova: inflight: bool (substitui parts.append "executando")
```

Ordem do `compose()`: Banner → ChatScroll → Toolbar → Input. Dock final via CSS.

### 3.2 CSS alvo (`nyx/agent/tui/styles/nyx.tcss`)

Expansão de 50L → ~200L estendendo padrão `templo_de_nyx.css`:

```css
App { background: $surface; color: $foreground; }

BannerWidget {
    dock: top;
    height: auto;
    background: $surface;
    padding: 0 1;
    color: $accent;  /* turquesa NYX_ACCENT */
}

#chat {
    height: 1fr;
    background: $surface;
    padding: 1;
    scrollbar-background: $surface;
    scrollbar-color: $primary 30%;          /* roxo dim */
    scrollbar-color-hover: $primary;        /* roxo */
    scrollbar-color-active: $accent;        /* turquesa hover-active */
    scrollbar-corner-color: $surface;
}

ChatMessage.user {
    color: $accent;
    border-left: heavy $accent;
    padding: 0 1 0 2;
    margin: 1 0 0 0;
}
ChatMessage.assistant {
    color: $primary;
    border-left: heavy $primary;
    padding: 0 1 0 2;
    margin: 1 0 0 0;
}
ChatMessage.tool {
    color: $muted;
    padding: 0 1 0 4;
    margin: 0;
}
ChatMessage.system {
    color: $muted;
    text-style: italic;
    padding: 0 1;
    margin: 0;
}

InputWidget {
    dock: bottom;
    height: 5;
    background: $surface;
    border: round $accent;
    padding: 0 1;
}
InputWidget > TextArea {
    background: $surface;
    color: $foreground;
    border: none;
}

Toolbar {
    dock: bottom;
    height: 1;
    background: $surface;
    color: $muted;
    padding: 0 1;
}
```

Tokens `$accent`/`$primary`/`$muted`/`$surface` vêm de
`design_tokens.py` via `App.CSS = ` ou definição inline (decisão de
implementação: usar CSS vars `$accent: #00D4AA` no topo do tcss; equivalência
com Luna `templo_de_nyx.css` que usa hex literal).

### 3.3 ChatMessage (widget novo)

```python
class ChatMessage(Static):
    """Mensagem individual da conversa. Role determina cor e borda."""

    DEFAULT_CSS = ""  # CSS no nyx.tcss

    def __init__(self, role: str, content: str = "") -> None:
        super().__init__(classes=role)
        self._role = role
        self._content = content
        self.update(self._render())

    def append_text(self, token: str) -> None:
        self._content += token
        self.update(self._render())

    def _render(self) -> str:
        if self._role == "user":
            prefix = "> "
            return f"{prefix}{self._content}"
        if self._role == "assistant":
            return f"◆ NyxCode\n{self._content}"
        if self._role == "tool":
            return f"  {self._content}"
        return self._content
```

Renderização rica (markdown, code blocks, syntax highlight) fica para sprint
futura via `Markdown` widget do Textual ou `Syntax` do Rich. Por enquanto
texto puro com cores via CSS classes.

### 3.4 BannerWidget (já existe, ajustar)

`nyx/agent/tui/widgets/banner.py` já tem refresh local via timer. Ajustes:
- `dock: top` no DEFAULT_CSS (não fica no fluxo do chat)
- Manter `height: auto` para que banner_compact (1-2 linhas) e banner_wide
  (5+ linhas ASCII) coexistam. Decisão de qual usar fica em
  `nyx/agent/banner.py::build_banner` que já tem detecção
  `_use_wide(columns)` interna. NyxTUI consulta `self.size.width` no
  `on_resize` e re-renderiza o banner via `BannerWidget.refresh()`.

### 3.5 AgentLoop bridge

```python
class NyxTUI(App):
    def __init__(self, ..., agent: AgentLoop):
        super().__init__()
        self._agent = agent
        self._current_assistant: ChatMessage | None = None

        # Registra callbacks na bridge ANTES de run_async
        agent.on_token = self._on_token
        agent.on_tool = self._on_tool
        agent.on_tool_result = self._on_tool_result
        agent.on_model_state = self._on_model_state
        agent.on_thinking = self._on_thinking

    def _on_input_submit(self, text: str) -> None:
        if not text.strip():
            return
        if text.startswith("/"):
            self._dispatch_slash(text)
            return
        chat = self.query_one("#chat", VerticalScroll)
        user_msg = ChatMessage("user", text)
        assistant_msg = ChatMessage("assistant", "")
        chat.mount(user_msg)
        chat.mount(assistant_msg)
        chat.scroll_end(animate=False)
        self._current_assistant = assistant_msg
        self.query_one(Toolbar).inflight = True
        self.run_worker(self._process_turn(text), thread=True, exclusive=True)

    async def _process_turn(self, user_input: str) -> None:
        try:
            await self._agent.run(user_input)
        finally:
            self.call_from_thread(setattr, self.query_one(Toolbar), "inflight", False)
            self.call_from_thread(self.query_one("#chat").scroll_end, animate=False)

    def _on_token(self, token: str) -> None:
        if self._current_assistant is not None:
            self.call_from_thread(self._current_assistant.append_text, token)

    def _on_tool(self, name: str, args: dict) -> None:
        chat = self.query_one("#chat", VerticalScroll)
        tool_msg = ChatMessage("tool", f"{name}({args})")
        self.call_from_thread(chat.mount, tool_msg)
```

Closure sobre `self._current_assistant` é state holder mutável (mesmo padrão
de Luna `add_chat_entry` com `retries = {"count": 0}` para evitar mutação de
nonlocal). `run_worker(thread=True, exclusive=True)` garante que turnos não
intercalam.

### 3.6 Slash command dispatch + redirect

```python
def _dispatch_slash(self, text: str) -> None:
    from nyx.agent.commands import handle_command
    from nyx.cli_handlers import HandlerCtx, dispatch_sync, dispatch_async
    chat = self.query_one("#chat", VerticalScroll)
    result = handle_command(text, self._project_root)
    if result == "__quit__":
        self.exit(result="__quit__")
        return
    handler_ctx = HandlerCtx(result=result, agent=self._agent, ...)
    with self._redirect_to_chat(chat):
        if dispatch_sync(handler_ctx):
            return
        self.run_worker(self._dispatch_async_worker(handler_ctx, chat), thread=True)

@contextmanager
def _redirect_to_chat(self, chat: VerticalScroll):
    """Context manager: substitui sys.stdout por proxy que mounta tool msgs."""
    class _Proxy:
        def write(_self, s):
            if s.strip():
                msg = ChatMessage("tool", s.rstrip())
                self.call_from_thread(chat.mount, msg)
            return len(s)
        def flush(_self): pass
        def isatty(_self): return True
        def fileno(_self): return sys.__stdout__.fileno()
    saved = sys.stdout
    sys.stdout = _Proxy()
    try: yield
    finally: sys.stdout = saved
```

Substitui `_StdoutToBufferProxy` + `_RedirectStdoutToEmit` de `output.py:121-194`.

### 3.7 ScreenModal Textual (substituto run_select_modal)

```python
class SelectScreen(ModalScreen[str]):
    """Modal de seleção (aesthetic_select, theme_select, schema_select)."""

    BINDINGS = [("escape", "dismiss(None)")]

    def __init__(self, title: str, options: list[tuple[str, str]]) -> None:
        super().__init__()
        self._title = title
        self._options = options  # [(value, label)]

    def compose(self) -> ComposeResult:
        with Container(id="modal-content"):
            yield Static(self._title, id="modal-title")
            for value, label in self._options:
                yield Button(label, id=f"opt-{value}")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        value = event.button.id.removeprefix("opt-")
        self.dismiss(value)
```

Uso: `selected = await self.push_screen_wait(SelectScreen("Tema", [(v, lbl) for v, lbl in themes]))`.

Substitui `nyx/cli_boot.py:run_select_modal` que usa `radiolist_dialog` do prompt_toolkit.

## 4. Sequência de sprints

Ordem topológica: cada sprint depende apenas de anteriores. IDs propostos
seguindo convenção do projeto. Todas as sprints terminam com `./run.sh --smoke`
boot ok + `bash scripts/sprint_invariants.sh` 14/14 PASS.

| Ordem | ID                              | Escopo                                                                                              | Risco | Dep |
|-------|---------------------------------|-----------------------------------------------------------------------------------------------------|-------|-----|
| 1     | `TUI-CSS-LUNA-ADOPT-01`         | Expandir nyx.tcss: scrollbar, dock top/bottom, ChatMessage classes, paleta tokens                   | Baixo | -   |
| 2     | `TUI-CHATMESSAGE-WIDGET-01`     | Novo `widgets/chat_message.py`. Static com role-based CSS classes + append_text + render            | Baixo | 1   |
| 3     | `TUI-VERTICAL-SCROLL-ADOPT-01`  | Trocar OutputWidget(RichLog) por VerticalScroll(id="chat") + ChatMessage mountado. PgUp/PgDn/wheel native | Médio | 2   |
| 4     | `TUI-BANNER-DOCK-TOP-01`        | BannerWidget recebe `dock: top` no CSS. Banner sai do compose simples para fixed top                | Baixo | 1   |
| 5     | `TUI-AGENT-BRIDGE-01`           | `_on_input_submit` + `_process_turn` + callbacks via call_from_thread. Toolbar.inflight reactive    | Alto  | 3   |
| 6     | `TUI-SLASH-DISPATCH-MODAL-01`   | `_dispatch_slash` + `_redirect_to_chat` + SelectScreen ModalScreen para run_select_modal            | Médio | 5   |
| 7     | `TUI-DEFAULT-FLIP-LEGACY-RM-01` | Flip default + deletar repl_app.py + cli_keybindings.py + helpers (~800L)                           | Alto  | 6   |

Total: ~7 sprints, estimativa de 2-3 sessões fortes.

## 5. Critérios de validação por sprint

Universais (todas):
- `./run.sh --smoke` -> `boot ok`
- `bash scripts/sprint_invariants.sh` -> PASS 14/14 FAIL 0
- Acentuação correta (`~/.config/zsh/scripts/validar-acentuacao.py --paths <files>`)
- Sem mention de IA externa em `.py`
- Ruff limpo

Específicos por sprint:

- **Sprint 1 (CSS):** `NYX_TUI_TEXTUAL=1 ./run.sh` sobe sem CSS parse error;
  screenshot via `import` da janela mostra classes carregadas.

- **Sprint 2 (ChatMessage):** unit test isolado mounta 3 instances (user,
  assistant, tool), assert classes corretas e render() output.

- **Sprint 3 (VerticalScroll):** `NYX_TUI_TEXTUAL=1 ./run.sh` permite digitar
  Enter 30x; scrollbar aparece; PgUp rola para cima; mouse wheel sobre
  área do chat rola; sobre input não move cursor.

- **Sprint 4 (Banner dock):** capturar 2 screenshots -- conversa curta e
  conversa longa (30 mensagens). Banner aparece no topo em ambos.

- **Sprint 5 (Agent bridge):** `NYX_TUI_TEXTUAL=1 ./run.sh`, enviar
  "Olá", aguardar resposta streaming chegar em ChatMessage assistant.
  Toolbar mostra "executando" durante o turno e "cold" ao fim.

- **Sprint 6 (Slash + Modal):** rodar `/help`, `/status`, `/quit`. Output
  aparece como ChatMessage tool. `/theme` abre SelectScreen modal,
  ESC fecha, Enter aplica.

- **Sprint 7 (Flip + RM):** `./run.sh` (sem env) sobe NyxTUI. `NYX_LEGACY_REPL=1
  ./run.sh` retorna ImportError (arquivos removidos) -- aceitável pois
  decisão da brainstorm foi deletar. Gauntlet rapido + proxy passa.

## 6. Riscos e mitigações

| Risco                                                                | Mitigação                                                                                          |
|----------------------------------------------------------------------|----------------------------------------------------------------------------------------------------|
| AgentLoop callbacks síncronos vs Textual async                       | Worker thread + `call_from_thread`; closure sobre `_current_assistant`                             |
| `Rich.Console.print` em handlers escreve direto em stdout            | `_redirect_to_chat` context manager substitui stdout por proxy que mounta `ChatMessage("tool", ...)` |
| `radiolist_dialog` do prompt_toolkit removido sem equivalente Textual | Sprint 6 implementa SelectScreen ModalScreen nativo                                                |
| Banner blink causa race com streaming (sprint 187 revertida pela 193) | `BannerWidget` usa `set_interval(0.5)` + refresh LOCAL via `self.refresh()`, sem `app.invalidate` global |
| Default flip quebra usuário em produção                              | Sprint 7 entrega flip + delete na mesma sprint (decisão do brainstorming). Validação visual obrigatória pelo usuário ANTES do commit final da sprint 7 -- se algo regredir, reverter via `git revert` sem ambiguidade |
| Validação visual no ambiente real do usuário pode revelar bug residual | Validação manual obrigatória pelo usuário antes de marcar sprint 5/6/7 CONCLUIDA (memória `feedback_validacao_visual_ambiente_real`) |
| Resume prompt (`maybe_offer_resume`) usa stdout                      | Adaptar para mountar ChatMessage system antes de NyxTUI iniciar OU usar push_screen para wizard       |

## 7. Pontos abertos para sprint posterior (não bloqueiam migração)

Catalogados aqui por princípio do "nenhum débito implícito" (memória
`feedback_nenhum_debito`):

- **TUI-MARKDOWN-RENDER-01** -- ChatMessage assistant suporta Markdown via
  `Markdown` widget. Hoje texto puro.
- **TUI-CODE-SYNTAX-01** -- Code blocks dentro de ChatMessage usam `Syntax`
  do Rich (já existe em `output.py:_render_code`).
- **TUI-DIFF-PANEL-01** -- Diff boxes em ChatMessage tool quando tool result
  é um diff.
- **TUI-VOICE-INTEGRATION-01** -- bindings para colar imagem/voz (paridade
  Luna `VoiceActionsMixin`). Ctrl+Shift+V já existe via VISION-02.
- **TUI-FIRST-RUN-WIZARD-01** -- wizard de primeiro boot estilo Luna
  `OnboardingProcess`.

## 8. Apêndice -- arquivos tocados por sprint

### Sprint 1 -- CSS Luna adopt

- M: `nyx/agent/tui/styles/nyx.tcss` (50L → ~200L)

### Sprint 2 -- ChatMessage widget

- A: `nyx/agent/tui/widgets/chat_message.py` (~80L)
- M: `nyx/agent/tui/widgets/__init__.py` (export)

### Sprint 3 -- VerticalScroll

- M: `nyx/agent/tui/app.py` (substituir OutputWidget por VerticalScroll)
- D: `nyx/agent/tui/widgets/output.py` (OutputWidget RichLog não mais necessário; conversa é ChatMessage mountado no VerticalScroll)
- M: `nyx/agent/tui/widgets/__init__.py` (remove export)

### Sprint 4 -- Banner dock top

- M: `nyx/agent/tui/widgets/banner.py` (DEFAULT_CSS dock: top)
- M: `nyx/agent/tui/styles/nyx.tcss` (ajuste height)

### Sprint 5 -- Agent bridge

- M: `nyx/agent/tui/app.py` (+ _process_turn + callbacks)
- M: `nyx/agent/tui/widgets/toolbar.py` (+ reactive inflight)
- M: `nyx/cli.py:419-439` (passar agent ao NyxTUI)

### Sprint 6 -- Slash dispatch + Modal

- A: `nyx/agent/tui/screens/select_screen.py` (~50L)
- M: `nyx/agent/tui/app.py` (+ _dispatch_slash + _redirect_to_chat)

### Sprint 7 -- Default flip + legacy RM

- M: `nyx/cli.py` (`use_application` -> dispatch NyxTUI sempre; remove
  branches legacy + blink loop + redirect_stdout_to_emit setup)
- D: `nyx/agent/repl_app.py` (778L)
- D: `nyx/cli_keybindings.py`
- M: `nyx/agent/output.py` (remove `_StdoutToBufferProxy`, `_RedirectStdoutToEmit`, `set_repl_app_output`, `clear_repl_app_output`, `_emit` routing buffer; mantém `RichOutput`, `render_assistant_*`, `render_user_input`, `nyx_spinner`, `_get_console`, etc. -- usados por headless e Console.print neutro)
- D: `nyx/agent/banner_blink.py` (`blink_cursor_at` substituído por `BannerWidget.set_interval` Textual nativo)
- D: função `run_select_modal` em `nyx/cli_boot.py` (substituída por `SelectScreen.push_screen_wait`)
