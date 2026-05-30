"""NyxTUI -- App Textual principal compondo os 4 widgets da ONDA-30/32.

Compose:
  - BannerWidget (top, com cursor blink local).
  - VerticalScroll(id="chat") (middle, container de ChatMessage widgets).
  - Toolbar (bottom-1, status).
  - InputWidget (bottom, prompt ancorado).

Bindings:
  - Ctrl+Q: quit (paridade sprint 188).
  - Ctrl+D: quit_if_empty (paridade sprint 189).
  - Shift+Tab: cycle_mode (paridade SHIFT-TAB-CYCLE-01).
  - Ctrl+V: paste (paridade VISION-02).
  - Ctrl+O: recall_last_input (paridade UX-EXTRA-01).

Dispatch:
  - Default: NUNCA dispatched (CLI continua usando repl_app.py).
  - Opt-in: env NYX_TUI_TEXTUAL=1 em cli.py dispara branch dedicado.

Sub-sprint TUI-VERTICAL-SCROLL-ADOPT-01 da ONDA-32 trocou o widget de
output legado (RichLog placeholder) por VerticalScroll nativo + ChatMessage
widgets mountados dinamicamente. Integração com Agent loop fica para
sub-sprint TUI-AGENT-BRIDGE-01. Por enquanto _on_input_submit apenas
monta a mensagem do usuário no chat scroll.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import VerticalScroll

from nyx.agent.tui.widgets.banner import BannerWidget
from nyx.agent.tui.widgets.chat_message import ChatMessage
from nyx.agent.tui.widgets.input import InputWidget
from nyx.agent.tui.widgets.toolbar import Toolbar


class NyxTUI(App):
    """App Textual principal -- sub-sprint TEXTUAL-CUTOVER-01.

    Composição em quatro widgets que reproduzem a estrutura visual da
    REPL prompt_toolkit existente. Ordem de yield definida pelo spec
    (Banner, Output, Toolbar, Input). O empilhamento final do layout
    é governado pelo CSS (`dock: bottom` em Input/Toolbar; `height: 1fr`
    em Output) -- compose() apenas registra os filhos.
    """

    CSS_PATH = Path(__file__).parent / "styles" / "nyx.tcss"

    # priority=True garante que o App captura o key event antes do widget
    # focado (InputWidget consome shift+tab/ctrl+v/ctrl+o por padrão). Sem
    # priority, atalhos globais ficam refens do focus -- comportamento
    # incompatível com a paridade prompt_toolkit dos sprints 188-189 e
    # SHIFT-TAB-CYCLE-01.
    BINDINGS = [
        Binding("ctrl+q", "quit", "Quit", priority=True),
        Binding("ctrl+d", "quit_if_empty", "Quit (EOF)", priority=True),
        Binding("shift+tab", "cycle_mode", "Trocar modo", priority=True),
        Binding("ctrl+v", "paste", "Colar", priority=True),
        Binding("ctrl+o", "recall_last", "Recall último input", priority=True),
        # TUI-INPUT-HISTORY-NAV-01: navegação do histórico de inputs. Ctrl+Up
        # recua para submissões mais antigas, Ctrl+Down avança de volta para
        # as mais recentes (e restaura o rascunho ao passar do mais recente).
        # priority=True (mesmo padrão dos atalhos acima) garante que o App
        # captura a tecla antes do InputWidget focado -- e como o TextArea NÃO
        # liga Ctrl+Up/Ctrl+Down (só `up`/`down` nuas = cursor_up/cursor_down),
        # não há colisão com o movimento de cursor multiline da sprint 286.
        Binding("ctrl+up", "history_prev", "Histórico anterior", priority=True),
        Binding("ctrl+down", "history_next", "Histórico próximo", priority=True),
    ]

    # Atenção: `App.MODES` em Textual é dict[str, Screen] -- redefinir como
    # tupla aqui colide com a metaclasse e crasha em class-creation. Mantemos
    # o ciclo de modos em um atributo distinto.
    MODE_CYCLE = ("normal", "plan", "sudo", "bypass")

    def __init__(
        self,
        *,
        model: str = "qwen2.5-coder:3b",
        tools_count: int = 35,
        project_name: str = "Nyx-Code",
        slash_completer: list[str] | None = None,
        settings: Any = None,
        agent: Any = None,
        user_display_name: str = "",
    ) -> None:
        super().__init__()
        self._model = model
        self._tools_count = tools_count
        self._project_name = project_name
        self._slash_completer = slash_completer or []
        # TUI-CHAT-LABELS-COLORS-01: nome de exibição do usuário (de
        # resolve_user_display_name, via cli.py) repassado ao ChatMessage("user").
        self._user_display_name = user_display_name
        self._settings = settings
        self._agent = agent
        self._mode_idx = 0
        self._last_input: str = ""
        # TUI-INPUT-HISTORY-NAV-01: store de histórico navegável (Ctrl+Up/Down).
        # `_input_history` guarda as submissões NÃO-slash em ordem cronológica
        # (mais antigo primeiro, mais recente no fim) -- paridade de semântica
        # com `_last_input`, que só é setado no ramo não-slash de
        # `_on_input_submit`. `_history_idx` é o cursor de navegação: a
        # convenção `idx == len(_input_history)` significa "fora do histórico"
        # (mostrando o rascunho do usuário); após cada submit volta a esse
        # valor. `_history_draft` preserva o buffer que estava sendo digitado
        # quando a navegação começou, para restaurá-lo ao sair pelo lado
        # recente (Ctrl+Down além do mais recente).
        self._input_history: list[str] = []
        self._history_idx: int = len(self._input_history)
        self._history_draft: str = ""
        # TUI-NYXCODE-GHOST-LAZY-MOUNT-01: ref ao ChatMessage("assistant")
        # do turno corrente -- destino do streaming de tokens. Lazy-mount:
        # fica None até o 1o token truthy chegar em `_on_agent_token`, que
        # então cria e monta o widget. Antes era mountado vazio no início de
        # cada turno em `_on_input_submit`, deixando um balão fantasma só com o
        # cabeçalho "NyxCode" (render() do ChatMessage assistant-vazio) visível
        # até o 1o token -- e persistente em turnos só-tool/erro. `_process_turn`
        # reseta para None no finally, garantindo turno limpo.
        self._current_assistant: Any = None
        # TUI-AGENT-BRIDGE-01: patch dos atributos privados do AgentLoop.
        # FORBIDDEN explicito do spec: não modificar AgentLoop signature.
        # AgentLoop expõe internamente `_on_token`, `_on_tool`,
        # `_on_tool_result` (loop/_core.py:84-86) -- atributos públicos
        # `on_token` etc. não existem. Setar `agent.on_token = ...` só
        # cria atributo morto. Patchamos os privados.
        # Para tokens: StreamingCollector é construído no __init__ do
        # AgentLoop com o on_token capturado (loop/_core.py:119) -- sem
        # patchar também `agent._collector._on_token`, o stream segue indo
        # para o callback original (build_render_callbacks). Patch duplo
        # garante que o NyxTUI recebe tokens via `_on_agent_token`.
        if agent is not None:
            agent._on_token = self._on_agent_token
            agent._on_tool = self._on_agent_tool
            agent._on_tool_result = self._on_agent_tool_result
            collector = getattr(agent, "_collector", None)
            if collector is not None:
                collector._on_token = self._on_agent_token

    def compose(self) -> ComposeResult:
        """Yield Banner, VerticalScroll, Input, Toolbar -- ordem é crítica.

        BannerWidget e Toolbar não aceitam `id=` no construtor (não
        repassam ao super). Atribuímos `.id` após instanciar -- atributo
        público herdado de `textual.widget.Widget`.

        Ordem de dock importa: widgets com `dock: bottom` empilham na
        ordem em que são yielded -- o último fica MAIS PERTO da borda
        inferior. Queremos Toolbar (h:1) na última linha e o Input
        (TextArea de altura crescente, min-height 3) logo acima dela;
        portanto Input PRIMEIRO, Toolbar POR ÚLTIMO. Sem isso a Toolbar
        fica coberta pelo Input (colisão de Y observada em viewport
        120x36: Input y=31..35 vs Toolbar y=35).
        """
        banner = BannerWidget(
            model=self._model,
            tools_count=self._tools_count,
            project_name=self._project_name,
            settings=self._settings,
        )
        banner.id = "banner"
        yield banner

        yield VerticalScroll(id="chat")

        yield InputWidget(
            id="input",
            slash_completer=self._slash_completer,
            on_submit=self._on_input_submit,
        )

        toolbar = Toolbar(model=self._model)
        toolbar.id = "toolbar"
        yield toolbar

    def on_mount(self) -> None:
        """Foca o InputWidget ao montar -- TUI-FIX-INPUT-FOCUS-ON-MOUNT-01.

        Sem isto, o Textual foca o primeiro widget focável da árvore, que é o
        VerticalScroll(#chat) -- as teclas de texto vão para o container de
        scroll (que as ignora) em vez do prompt. Efeito: a TUI parece "morta"
        ao digitar (input nunca recebe caractere), embora bindings globais
        como shift+tab funcionem. Reproduzido no caminho --web (cockpit/PTY +
        xterm.js); focar o input explicitamente conserta os dois caminhos.
        """
        self.query_one("#input", InputWidget).focus()

    def _on_input_submit(self, text: str) -> None:
        """Callback do InputWidget.

        Slash command (text.lstrip() começa com "/"): roteia para
        `_dispatch_slash` ANTES de qualquer dispatch de turno do agent.
        Sem agent: paridade sub-sprint anterior -- só monta ChatMessage("user").
        Com agent: monta APENAS o ChatMessage("user"), seta
        `self._current_assistant = None`, toolbar.inflight=True e dispara o
        worker para await agent.run() em background. O ChatMessage("assistant")
        NÃO é mountado aqui -- TUI-NYXCODE-GHOST-LAZY-MOUNT-01: o lazy-mount
        ocorre no 1o token truthy em `_on_agent_token`, evitando o balão
        fantasma "NyxCode" vazio entre o envio e o 1o token (e em turnos
        só-tool/erro, que nunca produzem texto de assistant).

        Streaming de tokens, tool calls e tool results retornam pelo bridge
        de callbacks instalado no __init__ (`_on_agent_token`, `_on_agent_tool`,
        `_on_agent_tool_result`). Como o turno roda como worker async no loop
        principal (TUI-FIX-HTTPX-LOOP-AFFINITY-01), os callbacks tocam os
        widgets direto -- sem `call_from_thread`.
        """
        if not text.strip():
            return
        # TUI-SLASH-DISPATCH-MODAL-01: slash commands precedem o dispatch
        # do agent. handle_command devolve None se não for comando, string
        # se for, ou um sentinel específico ("__quit__", "__aesthetic_select__",
        # etc.) -- _dispatch_slash isola toda essa lógica.
        if text.lstrip().startswith("/"):
            self._dispatch_slash(text)
            return
        self._last_input = text
        # TUI-INPUT-HISTORY-NAV-01: alimenta o histórico navegável no mesmo
        # ponto (ramo não-slash) onde `_last_input` é setado, garantindo que
        # slash commands ficam de fora (o ramo slash retorna antes, acima).
        # Dedup só do consecutivo (não global) para não poluir com Enter
        # repetido do mesmo comando, preservando a ordem de uso. Cada submit
        # reposiciona o cursor de navegação para "fora do histórico" e limpa
        # o rascunho preservado.
        if not self._input_history or self._input_history[-1] != text:
            self._input_history.append(text)
        self._history_idx = len(self._input_history)
        self._history_draft = ""
        chat = self.query_one("#chat", VerticalScroll)
        chat.mount(ChatMessage("user", text, display_name=self._user_display_name))
        chat.scroll_end(animate=False)
        if self._agent is None:
            return
        # TUI-NYXCODE-GHOST-LAZY-MOUNT-01: NÃO montar o assistant aqui. O
        # balão "assistant" só é criado/mountado quando o 1o token truthy
        # chega em `_on_agent_token`. Partir de None deixa explicito que o
        # lazy-mount ocorre no callback de token, nunca no início do turno.
        self._current_assistant = None
        toolbar = self.query_one("#toolbar", Toolbar)
        toolbar.inflight = True
        # TUI-FIX-HTTPX-LOOP-AFFINITY-01 (ONDA-33): worker async NO LOOP
        # PRINCIPAL (sem thread=True). Antes, thread=True rodava agent.run()
        # via asyncio.run() numa thread descartavel -- o httpx client do agent
        # nascia preso a esse loop e morria com ele, causando "Event loop is
        # closed" no 2o turno e no shutdown. Rodando no loop do Textual, o
        # client vive no mesmo loop o tempo todo. A tool execution bloqueante
        # sai do loop via asyncio.to_thread dentro do AgentLoop.
        # exclusive=True mantem 1 turno por vez (fila implicita).
        self.run_worker(self._process_turn(text), exclusive=True)

    def _dispatch_slash(self, text: str) -> None:
        """Roteia slash command via handle_command e trata sentinels.

        Sentinels reconhecidos:
          - `__quit__`           -> self.exit(result="__quit__")
          - `__aesthetic_select__`/`__theme_select__`/`__schema_select__`
                                -> run_worker(_open_select_modal(kind))
          - outros               -> mountados como ChatMessage("tool", result)

        Exceções do handler viram ChatMessage("tool", "[erro] ...") -- não
        crasham a TUI. handle_command devolve None apenas quando o input não
        começa com "/" (filtrado antes), então aqui um None significaria
        comando sem retorno explícito (no-op silencioso).
        """
        from nyx.agent.commands import handle_command

        chat = self.query_one("#chat", VerticalScroll)
        chat.mount(ChatMessage("user", text, display_name=self._user_display_name))
        chat.scroll_end(animate=False)
        project_root = str(getattr(self._settings, "project_root", "."))
        try:
            result = handle_command(text, project_root)
        except Exception as exc:
            chat.mount(ChatMessage("tool", f"[erro] {exc}"))
            return
        if result is None:
            return
        if result == "__quit__":
            self.exit(result="__quit__")
            return
        if result in (
            "__aesthetic_select__",
            "__theme_select__",
            "__schema_select__",
        ):
            self.run_worker(
                self._open_select_modal(result), exclusive=False
            )
            return
        # Outros retornos (texto, sentinels de erro, etc.) viram ChatMessage tool.
        chat.mount(ChatMessage("tool", str(result)))
        chat.scroll_end(animate=False)

    async def _open_select_modal(self, kind: str) -> None:
        """Push SelectScreen e mounta resultado como ChatMessage("tool").

        Stub mínimo: opções vêm de settings/theme_manager; sprint dedicada
        popula. Aqui basta provar que push_screen_wait funciona e o ciclo
        chega ao chat scroll com o valor escolhido (ou None se ESC cancelou).
        """
        from nyx.agent.tui.screens.select_screen import SelectScreen

        options = [("opt1", "Opção 1"), ("opt2", "Opção 2")]
        title = {
            "__aesthetic_select__": "Estética",
            "__theme_select__": "Tema",
            "__schema_select__": "Schema",
        }[kind]
        selected = await self.push_screen_wait(SelectScreen(title, options))
        chat = self.query_one("#chat", VerticalScroll)
        chat.mount(ChatMessage("tool", f"{kind}: {selected}"))
        chat.scroll_end(animate=False)

    async def _process_turn(self, text: str) -> None:
        """Worker async (loop principal): aguarda agent.run() e reseta inflight.

        TUI-FIX-HTTPX-LOOP-AFFINITY-01 (ONDA-33): roda no event loop do
        Textual. Como estamos no loop main, widgets são tocados DIRETO --
        `call_from_thread` aqui lançaria RuntimeError. Antes, o finally usava
        `call_from_thread(chat.scroll_end, False)`, passando `False` como
        argumento posicional para `scroll_end`, que só aceita `animate` por
        keyword -- TypeError a cada turno (TUI-FIX-SCROLL-END-KWARG-01).

        Try/finally garante toolbar.inflight = False em qualquer caminho.
        Exceções do agent sobem para o handler global do Textual (loga e
        mostra; não crasha a TUI).
        """
        try:
            await self._agent.run(text)
        finally:
            self.query_one("#toolbar", Toolbar).inflight = False
            self.query_one("#chat", VerticalScroll).scroll_end(animate=False)
            # TUI-NYXCODE-GHOST-LAZY-MOUNT-01: reset para None ao fim do turno.
            # Todos os tokens chegam ANTES do finally (agent.run() e awaited no
            # try, mesmo event loop -- loop affinity ONDA-33). Garante que o
            # turno N+1 nunca faça append no balão do turno N antes do próprio
            # lazy-mount disparar no 1o token.
            self._current_assistant = None

    def _on_agent_token(self, token: str) -> None:
        """Callback patcheado em agent._on_token (e collector._on_token).

        TUI-FIX-HTTPX-LOOP-AFFINITY-01: chamado de dentro de agent.run() no
        loop principal -- toca o widget direto (sem call_from_thread); aqui
        `call_from_thread` lançaria RuntimeError.

        TUI-NYXCODE-GHOST-LAZY-MOUNT-01 (lazy-mount):
          - Token falsy (`not token`): retorna sem montar nada -- evita
            materializar um balão vazio por token vazio.
          - `_current_assistant is None` (1o token truthy do turno): cria e
            monta o ChatMessage("assistant") no #chat AGORA, na posição
            cronológica correta (após eventuais ChatMessage("tool") já
            mountados), guarda a ref e ancora o scroll. scroll_end por keyword
            (TUI-FIX-SCROLL-END-KWARG-01).
          - Em seguida, com `_current_assistant` garantido, faz append_text --
            tokens subsequentes do mesmo turno reusam o mesmo widget, que cresce
            em altura via refresh(layout=True) (TUI-FIX-CHATMESSAGE-RELAYOUT-01).
        """
        if not token:
            return
        if self._current_assistant is None:
            chat = self.query_one("#chat", VerticalScroll)
            assistant = ChatMessage("assistant", "")
            chat.mount(assistant)
            self._current_assistant = assistant
            chat.scroll_end(animate=False)
        self._current_assistant.append_text(token)

    def _on_agent_tool(self, name: str, args: Any) -> None:
        """Callback patcheado em agent._on_tool.

        Signature real do AgentLoop: `_on_tool(name, args)` -- 2 args
        posicionais (ver loop/_iteration.py:85). Monta ChatMessage("tool")
        com representacao compacta dos args.
        """
        args_str = "" if args is None else str(args)
        chat = self.query_one("#chat", VerticalScroll)
        chat.mount(ChatMessage("tool", f"{name}({args_str})"))
        chat.scroll_end(animate=False)

    def _on_agent_tool_result(self, name: str, result: Any = "") -> None:
        """Callback patcheado em agent._on_tool_result.

        Signature real do AgentLoop: `_on_tool_result(name, result.output
        if result.success else result.error)` -- 2 args, segundo eh string
        (output ou error). Ver loop/_iteration.py:183.
        """
        chat = self.query_one("#chat", VerticalScroll)
        chat.mount(ChatMessage("tool", f"-> {name}: {result}"))
        chat.scroll_end(animate=False)

    async def action_quit(self) -> None:
        """Ctrl+Q: fecha app via Application.exit(result=__quit__).

        Paridade sprint 188: cli.py reconhece o sentinel `__quit__` e
        dispara `render_quit_card` + `run_quit_shutdown`. A integração
        completa (chamada explícita do shutdown_repl) será feita quando
        ONDA-31 fizer o cutover real.
        """
        self.exit(result="__quit__")

    async def action_quit_if_empty(self) -> None:
        """Ctrl+D: quit se input vazio, senão deleta caractere forward."""
        input_widget = self.query_one("#input", InputWidget)
        if not input_widget.text:
            self.exit(result="__quit__")
        else:
            input_widget.action_delete_right()

    async def action_cycle_mode(self) -> None:
        """Shift+Tab: cicla normal -> plan -> sudo -> bypass -> normal."""
        self._mode_idx = (self._mode_idx + 1) % len(self.MODE_CYCLE)
        new_mode = self.MODE_CYCLE[self._mode_idx]
        toolbar = self.query_one("#toolbar", Toolbar)
        toolbar.mode = new_mode

    async def action_paste(self) -> None:
        """Ctrl+V: cola texto do clipboard (lazy import VISION-02).

        Falhas (clipboard inacessível fora de TTY, X11 ausente, etc.)
        viram no-op silencioso -- o agent não pode crashar por causa
        de um colar best-effort.
        """
        try:
            from nyx.agent.clipboard import capture_text

            text = capture_text() or ""
        except Exception:
            text = ""
        if text:
            input_widget = self.query_one("#input", InputWidget)
            input_widget.paste_text(text)

    async def action_recall_last(self) -> None:
        """Ctrl+O: recarrega último input no buffer (UX-EXTRA-01)."""
        if self._last_input:
            input_widget = self.query_one("#input", InputWidget)
            input_widget.text = self._last_input

    async def action_history_prev(self) -> None:
        """Ctrl+Up: recua para submissões mais antigas do histórico.

        TUI-INPUT-HISTORY-NAV-01. Convenção: `_history_idx == len(history)`
        significa "fora do histórico". Ao entrar na navegação (primeiro
        Ctrl+Up vindo de fora), o rascunho corrente é salvo em
        `_history_draft` para poder ser restaurado depois por Ctrl+Down. No
        topo (índice 0, item mais antigo) a tecla é um no-op -- o índice não
        estoura. Após reescrever o buffer, o cursor vai para o fim do
        documento (UX: comando recuperado pronto para editar/reenviar).
        """
        if not self._input_history:
            return
        input_widget = self.query_one("#input", InputWidget)
        if self._history_idx == len(self._input_history):
            self._history_draft = input_widget.text
        if self._history_idx > 0:
            self._history_idx -= 1
        input_widget.text = self._input_history[self._history_idx]
        input_widget.move_cursor(input_widget.document.end)

    async def action_history_next(self) -> None:
        """Ctrl+Down: avança para submissões mais recentes (ou ao rascunho).

        TUI-INPUT-HISTORY-NAV-01. Espelho de `action_history_prev`. Quando já
        está fora do histórico (`_history_idx >= len(history)`) é no-op. Ao
        avançar além do mais recente, `_history_idx` reatinge `len(history)`
        e o buffer é restaurado para `_history_draft` (string vazia se nada
        estava sendo digitado quando a navegação começou). Cursor vai para o
        fim do documento, idem `action_history_prev`.
        """
        if not self._input_history:
            return
        input_widget = self.query_one("#input", InputWidget)
        if self._history_idx >= len(self._input_history):
            return
        self._history_idx += 1
        if self._history_idx == len(self._input_history):
            input_widget.text = self._history_draft
        else:
            input_widget.text = self._input_history[self._history_idx]
        input_widget.move_cursor(input_widget.document.end)


__all__ = ["NyxTUI"]
