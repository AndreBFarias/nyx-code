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

import re
import time
from pathlib import Path
from typing import Any

from rich.markdown import Markdown
from rich.text import Text
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Vertical, VerticalScroll
from textual.widgets import Collapsible, Static

from nyx.agent.services.logging_service import get_logger
from nyx.agent.tui.widgets.banner import BannerWidget
from nyx.agent.tui.widgets.chat_message import ChatMessage
from nyx.agent.tui.widgets.input import InputWidget
from nyx.agent.tui.widgets.suggestions import SuggestionPanel
from nyx.agent.tui.widgets.toolbar import Toolbar
from nyx.themes.design_tokens import NYX_MUTED, NYX_PURPLE

# TUI-WORKER-CRASH-GUARD-01 (ADR-033): logger que escreve em ~/.nyx/logs/nyx.log
# via logging_service. Usado para PERSISTIR o traceback de turnos que falham --
# antes a exceção subia pelo worker e o traceback ia para stderr, sumindo quando
# o terminal fechava (crash invisível).
logger = get_logger(__name__)

# TUI-THINKING-EXPAND-01: glifo via chr() (anti-sanitizer, padrão do BRIEF) para
# o título do bloco de raciocínio recolhível. U+25D0 = circle half black (in-progress).
_THINKING_GLYPH = chr(0x25D0)

# TUI-CODE-COPY-BUTTON-01: captura o conteúdo interno de um bloco ``` (a 1ª linha
# da fence pode trazer a linguagem, ex.: python). findall retorna todos; usamos o último.
_CODE_FENCE_RE = re.compile(r"```[^\n]*\n(.*?)```", re.DOTALL)


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
        # TUI-CODE-COPY-BUTTON-01: copia o último bloco ``` da última mensagem do
        # NyxCode via OSC52 (copy_to_clipboard nativo do Textual; funciona no
        # terminal e no --web/xterm.js). Ctrl+Y livre (o InputWidget não o consome).
        Binding("ctrl+y", "copy_last_code", "Copiar código", priority=True),
        # TUI-CONVERSATION-SCROLL-TEXTUAL-01 (SPRINT 309): PgUp/PgDn rolam a
        # CONVERSA (#chat) mesmo com o #input focado. O scroll por teclado se
        # perdeu na migração ONDA-32 (vivia no repl_app.py, sprint 228); o
        # VerticalScroll só rola por teclado quando focado, e o foco fica no
        # #input (307). priority=True faz o App capturar antes do TextArea.
        # PgUp/PgDn quase não servem à edição de um input de 5 linhas, então
        # não há perda; Home/End ficam com o input. A roda do mouse já rola o
        # #chat nativamente (VerticalScroll).
        Binding("pageup", "scroll_chat_up", "Rolar conversa (cima)", priority=True),
        Binding("pagedown", "scroll_chat_down", "Rolar conversa (baixo)", priority=True),
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
        slash_commands: list[tuple[str, str]] | None = None,
        settings: Any = None,
        agent: Any = None,
        user_display_name: str = "",
    ) -> None:
        super().__init__()
        self._model = model
        self._tools_count = tools_count
        self._project_name = project_name
        self._slash_completer = slash_completer or []
        # TUI-SLASH-SUGGEST-PANEL-01: lista (nome, descrição) para o painel de
        # sugestões de >=3 linhas (decisão do dono). Vazia => painel desativado.
        self._slash_commands = slash_commands or []
        # TUI-CHAT-LABELS-COLORS-01: nome de exibição do usuário (de
        # resolve_user_display_name, via cli.py) repassado ao ChatMessage("user").
        self._user_display_name = user_display_name
        self._settings = settings
        self._agent = agent
        self._mode_idx = 0
        self._last_input: str = ""
        # TUI-CONVERSATION-SCROLL-TEXTUAL-01 (SPRINT 309): seguimento do fim
        # (auto-scroll). True = novos tokens/tools rolam ao fim; PgUp desliga
        # (usuário lendo histórico), PgDn-até-o-fim e o submit do usuário religam.
        self._follow_output: bool = True
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
        # TUI-THINKING-LIVE-01 (ONDA-37): indicador "pensando... (Ns)" ao vivo durante
        # a inferência (regressão da migração Textual -- existia no prompt_toolkit via
        # build_warming_label + nyx_spinner). Ref ao widget efêmero + t0 + timer de 1s;
        # criado no submit, removido no 1º token de resposta ou no finally do turno.
        self._thinking_indicator: Static | None = None
        self._thinking_t0: float = 0.0
        self._thinking_timer: Any = None
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
            # TUI-THINKING-EXPAND-01: a bridge passa a consumir o reasoning do
            # modelo (antes dropado na TUI Textual). `_on_thinking(reasoning)` é
            # chamado em loop/_iteration.py:517 (1 arg string, loop principal).
            agent._on_thinking = self._on_agent_thinking
            # TUI-FOOTER-MODEL-STATE-LIVE-01 (ONDA-37): consome o estado do modelo
            # (cold/warming/warm) emitido por _emit_state (loop/_core.py:163). Sem
            # este patch o footer ficava "Cold" FIXO -- o app nunca atualizava
            # toolbar.model_state. Agora reflete o aquecimento ao vivo no rodapé.
            agent._on_model_state = self._on_agent_model_state
            # TUI-PERMISSION-CONFIRM-01 (ONDA-37): a Nyx PERGUNTA antes de alterar
            # (write/edit/run) no modo Normal -- callback async abre ConfirmScreen e
            # espera a resposta. Bypass auto-aprova (CONFIRM_ONCE vira AUTO, não chega
            # aqui); Plan bloqueia a escrita antes, no loop. Sobrescreve o callback
            # síncrono do prompt_toolkit que o cli.py passa (não serve à TUI async).
            agent._on_permission = self._on_agent_permission
            collector = getattr(agent, "_collector", None)
            if collector is not None:
                collector._on_token = self._on_agent_token

    def compose(self) -> ComposeResult:
        """Yield #chat (Banner como 1º filho rolável), Input, Toolbar -- ordem crítica.

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

        # TUI-BANNER-SCROLLABLE-01: o banner deixa de ser dock:top fixo e vira o
        # PRIMEIRO filho do #chat -- rola junto com a conversa (os ChatMessages
        # são mountados depois, abaixo dele). A scrollbar do #chat passa a cobrir
        # banner+chat; só o Input/Toolbar (dock:bottom) ficam fora do scroll.
        with VerticalScroll(id="chat"):
            yield banner

        # TUI-INPUT-HEIGHT-5-SCROLL-01 (SPRINT 306): input + toolbar num único
        # container dock:bottom. Dois widgets dock:bottom soltos não reservavam o
        # espaço somado -- o #chat (1fr) descontava só o input e a toolbar caía
        # sobre a borda inferior do input (o "corte" relatado). O Vertical
        # dock:bottom reserva input (7) + toolbar (1) = 8 linhas e o #chat fica
        # com o resto, sem sobreposição. A ordem interna (input acima, toolbar
        # abaixo) deixa a toolbar na última linha, como antes.
        with Vertical(id="bottombar"):
            # TUI-SLASH-SUGGEST-PANEL-01: painel de sugestões ACIMA do input
            # (primeiro filho). Vazio => some (classe -empty, display:none); cresce
            # o #bottombar para cima quando há matches de `/`, sem cobrir a toolbar.
            yield SuggestionPanel(id="suggestions")
            yield InputWidget(
                id="input",
                slash_completer=self._slash_completer,
                slash_commands=self._slash_commands or None,
                on_submit=self._on_input_submit,
                on_suggestions=self._update_suggestions_panel,
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
        # TUI-MODE-BEHAVIOR-01: estado de modo limpo no boot. plan_mode e
        # sudo_session são singletons de módulo; uma sessão anterior poderia ter
        # deixado um ativo. O ciclo começa sempre em normal.
        self._apply_mode("normal")
        self._focus_input()
        self.call_after_refresh(self._focus_input)

    def _focus_input(self) -> None:
        """Foca o #input (TUI-INPUT-AUTOFOCUS-01); chamado no mount e pós-refresh.

        O `on_mount` sozinho não bastava no caminho --web: o mount da TUI no PTY
        pode preceder o layout final e a conexão do xterm.js, e o foco se perdia.
        `call_after_refresh` reaplica após o primeiro refresh (árvore já montada,
        tamanho real resolvido). O #input é sempre yielded em compose(), então
        query_one não falha após o mount -- sem try/except (invariante #4: zero
        except silencioso). O foco no nível do DOM (canvas do xterm.js) é tratado
        em terminal.html (`term.focus()`); este é o foco interno do Textual.
        """
        self.query_one("#input", InputWidget).focus()

    def _update_suggestions_panel(self, matches: list[tuple[str, str]]) -> None:
        """TUI-SLASH-SUGGEST-PANEL-01: atualiza o painel de sugestões.

        Callback passado ao InputWidget; chamado a cada edição com os comandos
        que casam o prefixo digitado (lista de (/nome, descrição)). Lista vazia
        esconde o painel (classe -empty no SuggestionPanel).
        """
        self.query_one("#suggestions", SuggestionPanel).update_items(matches)

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
        # TUI-SLASH-SUGGEST-PANEL-01: some o painel de sugestões ao submeter.
        self._update_suggestions_panel([])
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
        # Enviar religa o auto-scroll e ancora no fim (TUI-CONVERSATION-SCROLL-TEXTUAL-01).
        self._follow_output = True
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
        # TUI-THINKING-LIVE-01: indicador "pensando... (Ns)" ao vivo durante o turno.
        self._start_thinking_indicator()
        # TUI-FIX-HTTPX-LOOP-AFFINITY-01 (ONDA-33): worker async NO LOOP
        # PRINCIPAL (sem thread=True). Antes, thread=True rodava agent.run()
        # via asyncio.run() numa thread descartavel -- o httpx client do agent
        # nascia preso a esse loop e morria com ele, causando "Event loop is
        # closed" no 2o turno e no shutdown. Rodando no loop do Textual, o
        # client vive no mesmo loop o tempo todo. A tool execution bloqueante
        # sai do loop via asyncio.to_thread dentro do AgentLoop.
        # exclusive=True mantem 1 turno por vez (fila implicita).
        # TUI-WORKER-CRASH-GUARD-01 (ADR-033): exit_on_error=False -- a infra
        # absorve a exceção dentro de _process_turn (except abaixo) em vez de deixar
        # o Textual chamar _handle_exception e DERRUBAR a TUI (default é True).
        # exclusive=True mantem 1 turno por vez (fila implicita).
        self.run_worker(
            self._process_turn(text), exclusive=True, exit_on_error=False
        )

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

        Try/except/finally: o finally garante toolbar.inflight = False em qualquer
        caminho; o except (TUI-WORKER-CRASH-GUARD-01, ADR-033) ABSORVE qualquer
        exceção do turno -- loga o traceback completo em ~/.nyx/logs/nyx.log e
        mostra um ChatMessage("system") no chat, mantendo a TUI viva. Combinado
        com exit_on_error=False no run_worker, a cadeia nunca quebra na mão do
        usuário (antes a exceção subia pelo worker e derrubava o app via
        _handle_exception do Textual, com o traceback indo para stderr/devtools
        e sumindo quando o terminal fechava -- o "crash invisível").
        """
        # TUI-TURN-ELAPSED-01: marca o início para medir a duração do turno.
        _t0 = time.monotonic()
        try:
            status = await self._agent.run(text)
            # TUI-DONE-SUMMARY-CLEAN-01 (SPRINT 303): o modelo às vezes emite
            # `done(summary="...")` como TEXTO (parser fallback), que o streaming
            # já exibiu CRU no balão do NyxCode. O summary limpo está no
            # SessionStatus de run(); quando o balão contém a sintaxe crua
            # `done(`, troca pelo summary. Resposta normal (texto puro) não casa
            # a condição -- balão fica intacto.
            if status is not None and self._current_assistant is not None:
                summary = (getattr(status, "summary", "") or "").strip()
                if summary and "done(" in self._current_assistant.content:
                    self._current_assistant.set_content(summary)
        except Exception as exc:  # noqa: BLE001 -- rede de seguranca deliberada
            # TUI-WORKER-CRASH-GUARD-01 (ADR-033): a infra absorve QUALQUER exceção
            # do turno (execução de tool, parsing, callback de UI, recovery) em vez
            # de repassar erro ao usuário. PERSISTE o traceback em
            # ~/.nyx/logs/nyx.log (antes ia para stderr e sumia com o terminal) e
            # mostra uma mensagem honesta no chat. A TUI segue viva.
            logger.exception("[turno] exceção absorvida durante agent.run: %s", exc)
            chat = self.query_one("#chat", VerticalScroll)
            chat.mount(
                ChatMessage(
                    "system",
                    f"[falha absorvida] {type(exc).__name__}: {exc}. "
                    "Detalhes em ~/.nyx/logs/nyx.log -- a sessão continua.",
                )
            )
        finally:
            # TUI-THINKING-LIVE-01: garante a remoção do indicador em qualquer caminho
            # (turnos só-tool/erro que nunca emitem token de texto).
            self._stop_thinking_indicator()
            self.query_one("#toolbar", Toolbar).inflight = False
            self._follow_end(self.query_one("#chat", VerticalScroll))
            # TUI-TURN-ELAPSED-01: registra o tempo do turno no balão do assistant
            # (se houve resposta de texto; turnos só-tool/erro não têm balão, então
            # o tempo é omitido nesses casos). Antes do reset abaixo.
            if self._current_assistant is not None:
                self._current_assistant.set_elapsed(time.monotonic() - _t0)
            # TUI-NYXCODE-GHOST-LAZY-MOUNT-01: reset para None ao fim do turno.
            # Todos os tokens chegam ANTES do finally (agent.run() e awaited no
            # try, mesmo event loop -- loop affinity ONDA-33). Garante que o
            # turno N+1 nunca faça append no balão do turno N antes do próprio
            # lazy-mount disparar no 1o token.
            self._current_assistant = None

    def _start_thinking_indicator(self) -> None:
        """TUI-THINKING-LIVE-01: monta o indicador 'pensando... (Ns)' no chat e agenda
        o tick de 1s. Reusa build_warming_label (output.py) com o model_state real do
        footer. Removido no 1º token (_on_agent_token) ou no finally do turno.
        """
        chat = self.query_one("#chat", VerticalScroll)
        self._thinking_t0 = time.monotonic()
        self._thinking_indicator = Static(classes="thinking-live")
        chat.mount(self._thinking_indicator)
        self._refresh_thinking_label()
        self._thinking_timer = self.set_interval(1.0, self._refresh_thinking_label)
        self._follow_end(chat)

    def _refresh_thinking_label(self) -> None:
        """Atualiza o texto do indicador via build_warming_label (a cada 1s).

        Estado do modelo vem do footer (item 2a): 'aquecendo modelo...' enquanto
        warming nos 1ºs 3s, depois 'pensando...' e 'pensando... (Ns)' com cronômetro.
        """
        if self._thinking_indicator is None:
            return
        from nyx.agent.output import build_warming_label

        state = self.query_one("#toolbar", Toolbar).model_state
        label = build_warming_label(state, self._thinking_t0)
        text = Text(f"{_THINKING_GLYPH} NyxCode", style=NYX_PURPLE)
        text.append(f"  ·  {label}", style=NYX_MUTED)
        self._thinking_indicator.update(text)

    def _stop_thinking_indicator(self) -> None:
        """Para o tick e remove o indicador (idempotente -- seguro chamar 2x)."""
        if self._thinking_timer is not None:
            self._thinking_timer.stop()
            self._thinking_timer = None
        if self._thinking_indicator is not None:
            self._thinking_indicator.remove()
            self._thinking_indicator = None

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
        chat = self.query_one("#chat", VerticalScroll)
        if self._current_assistant is None:
            # TUI-THINKING-LIVE-01: 1º token de resposta -> remove o indicador
            # de carregando antes de materializar o balão do assistant.
            self._stop_thinking_indicator()
            assistant = ChatMessage("assistant", "")
            chat.mount(assistant)
            self._current_assistant = assistant
        self._current_assistant.append_text(token)
        # TUI-CONVERSATION-SCROLL-TEXTUAL-01: acompanha o streaming respeitando
        # o auto-scroll-pause (se o usuário rolou para cima, não puxa de volta).
        self._follow_end(chat)

    def _on_agent_tool(self, name: str, args: Any) -> None:
        """Callback patcheado em agent._on_tool.

        Signature real do AgentLoop: `_on_tool(name, args)` -- 2 args
        posicionais (ver loop/_iteration.py:85). Monta ChatMessage("tool")
        com representacao compacta dos args.
        """
        args_str = "" if args is None else str(args)
        chat = self.query_one("#chat", VerticalScroll)
        chat.mount(ChatMessage("tool", f"{name}({args_str})"))
        self._follow_end(chat)

    def _on_agent_thinking(self, reasoning: str) -> None:
        """Callback patcheado em agent._on_thinking (loop/_iteration.py:517).

        TUI-THINKING-EXPAND-01: monta um Collapsible RECOLHIDO com o raciocínio
        do modelo no #chat. O expand/collapse é nativo do Textual (clique no
        título ou foco+Enter) -- não reusa o Tab (accept-ghost do input, 286). O
        reasoning chega após o stream da resposta; fica recolhido por padrão para
        não poluir a conversa. Antes da migração Textual o reasoning era dropado.
        """
        if not reasoning:
            return
        chat = self.query_one("#chat", VerticalScroll)
        block = Collapsible(
            Static(Markdown(reasoning)),
            title=f"{_THINKING_GLYPH} pensando",
            collapsed=True,
            classes="thinking",
        )
        chat.mount(block)
        self._follow_end(chat)

    async def _on_agent_permission(self, perm: str, name: str, args: Any) -> bool:
        """Callback async patcheado em agent._on_permission (TUI-PERMISSION-CONFIRM-01).

        Abre um ConfirmScreen e ESPERA a resposta (push_screen_wait) -- a Nyx pergunta
        antes de alterar (write/edit/run) no modo Normal. Roda no worker do turno (loop
        do Textual), então push_screen_wait (async) funciona. O loop dá `await` neste
        callback (suporta sync/async via inspect.isawaitable em _iteration.py).
        """
        from nyx.agent.tui.screens.confirm_screen import ConfirmScreen

        detail = self._format_perm_detail(name, args)
        approved = await self.push_screen_wait(ConfirmScreen(name, detail))
        return bool(approved)

    @staticmethod
    def _format_perm_detail(name: str, args: Any) -> str:
        """Resumo legível dos args para o modal de confirmação (path/command/etc.)."""
        if not isinstance(args, dict):
            return str(args)[:200]
        parts = [
            f"{k}: {args[k]}"
            for k in ("file_path", "path", "command", "cmd", "pattern", "url")
            if k in args and args[k]
        ]
        return "  ".join(parts)[:200] if parts else str(args)[:200]

    def _on_agent_model_state(self, state: str) -> None:
        """Callback patcheado em agent._on_model_state (TUI-FOOTER-MODEL-STATE-LIVE-01).

        Reflete o estado do modelo (cold/warming/warm) no footer AO VIVO. Chamado de
        dentro de agent.run() no loop principal (loop affinity ONDA-33) -- toca o
        widget direto. Exceções aqui são absorvidas pelo try/except do _emit_state
        (loop/_core.py:172), então não derrubam o turno.
        """
        self.query_one("#toolbar", Toolbar).model_state = state

    def _on_agent_tool_result(self, name: str, result: Any = "") -> None:
        """Callback patcheado em agent._on_tool_result.

        Signature real do AgentLoop: `_on_tool_result(name, result.output
        if result.success else result.error)` -- 2 args, segundo eh string
        (output ou error). Ver loop/_iteration.py:183.
        """
        chat = self.query_one("#chat", VerticalScroll)
        chat.mount(ChatMessage("tool", f"-> {name}: {result}"))
        self._follow_end(chat)

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
        """Shift+Tab: cicla normal -> plan -> sudo -> bypass -> normal.

        TUI-MODE-BEHAVIOR-01 (SPRINT 308): além do label visual na toolbar, o
        modo passa a ter COMPORTAMENTO real, aplicado por _apply_mode.
        """
        self._mode_idx = (self._mode_idx + 1) % len(self.MODE_CYCLE)
        new_mode = self.MODE_CYCLE[self._mode_idx]
        toolbar = self.query_one("#toolbar", Toolbar)
        toolbar.mode = new_mode
        self._apply_mode(new_mode)

    def _apply_mode(self, mode: str) -> None:
        """Liga o COMPORTAMENTO real de cada modo (TUI-MODE-BEHAVIOR-01).

        Antes da 308, Shift+Tab só mudava o label da toolbar (cosmético). Os
        mecanismos já existiam isolados; aqui o cycle os aciona:
        - plan   -> plan_mode.set_plan_mode(True): o loop bloqueia tools de
          escrita (write/edit/create/patch/run_command) e o agente só explora e
          planeja (is_tool_allowed_in_plan_mode em loop/_iteration.py).
        - sudo   -> sudo_session.set_active(True): habilita a elevação real
          (SUDO-MODE-01); a senha é fornecida via /sudo enable. Sair do sudo
          faz wipe() (apaga o cache de senha -- segurança).
        - bypass -> permissions.set_bypass(True): auto-aprova CONFIRM_ONCE
          (equivalente ao --auto-approve); DENY e ALWAYS_CONFIRM seguem pedindo.
        - normal -> desliga os três.

        Os modos são exclusivos (o cycle troca um pelo outro), então ao entrar
        em um, os outros são desligados. Sem agent (paridade pré-bridge), só
        plan/sudo (estado de módulo) se aplicam; bypass depende do agente.
        """
        from nyx.agent.tools import sudo_session
        from nyx.agent.tools.plan_mode import set_plan_mode

        set_plan_mode(mode == "plan")

        if mode == "sudo":
            sudo_session.set_active(True)
            if not sudo_session.has_password():
                self.notify(
                    "Modo sudo ativo. Forneça a senha com /sudo enable.",
                    severity="warning",
                )
        elif sudo_session.is_active():
            sudo_session.wipe()  # saiu do sudo: apaga o cache de senha

        if self._agent is not None:
            self._agent.permissions.set_bypass(mode == "bypass")

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

    def action_copy_last_code(self) -> None:
        """Copia o último bloco de código (```) da última mensagem do NyxCode.

        TUI-CODE-COPY-BUTTON-01: em vez de um botão por bloco (que exigiria
        rearquitetar o render Markdown da 299 + plumbing de mouse/clipboard), o
        atalho Ctrl+Y copia o último code block via `copy_to_clipboard` (OSC52
        nativo do Textual -- funciona no terminal e no --web/xterm.js). Varre o
        #chat de baixo para cima pela última mensagem assistant com fence ```.
        """
        messages = list(
            self.query_one("#chat", VerticalScroll).query(ChatMessage)
        )
        for msg in reversed(messages):
            if msg.role == "assistant" and "```" in msg.content:
                blocks = _CODE_FENCE_RE.findall(msg.content)
                if blocks:
                    self.copy_to_clipboard(blocks[-1].rstrip("\n"))
                    self.notify("Código copiado para a área de transferência.")
                    return
        self.notify(
            "Nenhum bloco de código para copiar.", severity="warning"
        )

    def action_scroll_chat_up(self) -> None:
        """PgUp: rola a conversa (#chat) uma página para cima.

        TUI-CONVERSATION-SCROLL-TEXTUAL-01. Opera o #chat diretamente -- não
        depende de ele ter foco (o foco fica no #input). Re-porta o scroll por
        teclado da sprint 228, perdido na migração ONDA-32 com o repl_app.py.
        """
        # Usuário quer ler o histórico: pausa o auto-scroll (religado por PgDn
        # até o fim ou pelo próximo envio).
        self._follow_output = False
        self.query_one("#chat", VerticalScroll).scroll_page_up()

    def action_scroll_chat_down(self) -> None:
        """PgDn: rola a conversa (#chat) para baixo; ao chegar no fim, religa o auto-scroll."""
        chat = self.query_one("#chat", VerticalScroll)
        chat.scroll_page_down()
        if chat.scroll_offset.y >= chat.max_scroll_y - 2:
            self._follow_output = True

    def _follow_end(self, chat: VerticalScroll) -> None:
        """Auto-scroll-pause: ancora no fim SÓ enquanto _follow_output está ativo.

        TUI-CONVERSATION-SCROLL-TEXTUAL-01 (re-porta a flag _user_scrolled_up da
        sprint 228, perdida na migração ONDA-32). PgUp desliga o seguimento
        (action_scroll_chat_up) -- o usuário lê o histórico e novos tokens/tools
        NÃO o puxam de volta; PgDn até o fim religa, assim como o submit do
        usuário. Usar uma flag (e não a posição no momento do mount) é robusto:
        mount/append muda max_scroll_y ANTES de medirmos, enganando um teste
        posicional.
        """
        if self._follow_output:
            chat.scroll_end(animate=False)


__all__ = ["NyxTUI"]
