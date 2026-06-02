"""Toolbar -- bottom bar da TUI Textual com reactive properties.

ONDA-30 sub-sprint TEXTUAL-TOOLBAR-01. Substituirá o build_bottom_toolbar
atual do PromptSession (`nyx/cli_keybindings.py:build_bottom_toolbar`) após
a sub-sprint TEXTUAL-CUTOVER-01.

Reactive properties + watch_* são o equivalente Textual ao FormattedText
callable do prompt_toolkit -- quando o state muda, o widget re-renderiza
LOCALMENTE (via `self.refresh()`), sem race com `app.invalidate()` global.

Padrão referenciado: BannerWidget (sub-sprint 205) -- refresh por-widget,
sem invalidação global. Tokens de cor consumidos via design_tokens.
"""

from __future__ import annotations

import asyncio
import logging

from rich.text import Text
from textual.app import RenderResult
from textual.reactive import reactive
from textual.widgets import Static

from nyx.config.defaults import DEFAULT_MODEL
from nyx.themes.design_tokens import (
    NYX_ACCENT,
    NYX_ERROR,
    NYX_MUTED,
    NYX_PURPLE,
    NYX_PURPLE_DIM,
    STATE_GLYPHS,
)

logger = logging.getLogger(__name__)


class Toolbar(Static):
    """Bottom toolbar com ctx/iter/lidos/modif/model_state/mode.

    Reactive properties:
      ctx_pct: % de contexto consumido (0-100).
      iter_n: iterações do turno atual.
      reads: arquivos lidos no turno.
      mods: arquivos modificados no turno.
      model_state: cold/warming/warm.
      mode: normal/plan/sudo/bypass.
      vram: string já formatada de uso de VRAM (ex.: "VRAM 1234/4096 MiB"),
        atualizada por polling leve de nvidia-smi a cada ~2s. Vazia ("")
        quando não há GPU ou nvidia-smi está ausente -- nesse caso o campo
        é OMITIDO do render (degradação graciosa, sem exceção).

    Constructor:
      model: nome do modelo Ollama (display fixo após init).

    Lifecycle:
      Cada watch_* dispara `self.refresh()` LOCAL ao widget. Crucial:
      mesma lição do BannerWidget (185 BLINK_SOFT revertida pela 193) --
      refresh por-widget evita race com streaming de output e outros
      redraws orquestrados pelo Textual driver.
    """

    DEFAULT_CSS = """
    Toolbar {
        dock: bottom;
        height: 1;
        background: $surface;
        color: $foreground;
    }
    """

    ctx_pct: reactive[int] = reactive(0)
    iter_n: reactive[int] = reactive(0)
    reads: reactive[int] = reactive(0)
    mods: reactive[int] = reactive(0)
    model_state: reactive[str] = reactive("cold")
    mode: reactive[str] = reactive("normal")
    # TUI-AGENT-BRIDGE-01: True enquanto worker do turno esta rodando.
    # NyxTUI seta antes de run_worker e reseta no finally do _process_turn.
    inflight: reactive[bool] = reactive(False)
    # TUI-FOOTER-VRAM-REALTIME-01: string já formatada de uso de VRAM
    # ("VRAM <used>/<total> MiB") atualizada pelo poll de nvidia-smi. Vazia
    # quando não há GPU/nvidia-smi -- render omite o campo (degradação graciosa).
    vram: reactive[str] = reactive("")

    def __init__(self, *, model: str = DEFAULT_MODEL) -> None:
        super().__init__()
        self._model = model

    def on_mount(self) -> None:
        """Agenda o polling leve de VRAM e dispara o primeiro frame.

        Precedente exato: BannerWidget.on_mount (`banner.py:106`) -- timer
        local ao widget via `set_interval`, refresh por-widget. O Toolbar não
        tinha `on_mount`; Static não exige `super()`. A primeira chamada é
        agendada via `call_after_refresh` para o campo aparecer já no boot,
        sem esperar o primeiro tick.

        TUI-FOOTER-VRAM-REALTIME-FASTER-01 (ONDA-37): intervalo baixado de 2.0s para
        1.0s -- a VRAM/% reflete o uso em tempo (quase) real conforme o modelo carrega
        na GPU e libera. O poll é leve (nvidia-smi async, não-bloqueante, timeout 3s).
        """
        self.set_interval(1.0, self._poll_vram)
        self.call_after_refresh(self._poll_vram)

    async def _poll_vram(self) -> None:
        """Consulta nvidia-smi em subprocess async e atualiza o reactive `vram`.

        NÃO-BLOQUEANTE: usa `asyncio.create_subprocess_exec` + `asyncio.wait_for`
        (timeout 3s) + `proc.kill()` no timeout, agendado NO event loop corrente
        do Textual (loop-affinity ONDA-33, sem loop/thread novos). Mesmo padrão
        de `proxy.py:_detect_num_gpu_async`. Degradação graciosa: ausência de
        GPU/nvidia-smi (`FileNotFoundError`), timeout ou parsing inválido zeram
        o reactive (`""`) e o render omite o campo -- estado normal, não erro.
        """
        try:
            proc = await asyncio.create_subprocess_exec(
                "nvidia-smi",
                "--query-gpu=memory.used,memory.total",
                "--format=csv,noheader,nounits",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
        except FileNotFoundError:
            # nvidia-smi ausente do PATH: ambiente sem GPU NVIDIA.
            logger.debug("nvidia-smi ausente; campo VRAM omitido")
            self.vram = ""
            return
        try:
            stdout, _ = await asyncio.wait_for(proc.communicate(), timeout=3.0)
        except asyncio.TimeoutError:
            proc.kill()
            await proc.wait()
            logger.debug("nvidia-smi timeout; campo VRAM omitido")
            self.vram = ""
            return
        if proc.returncode != 0:
            logger.debug("nvidia-smi rc=%s; campo VRAM omitido", proc.returncode)
            self.vram = ""
            return
        raw = stdout.decode("utf-8", errors="replace").strip()
        first = raw.splitlines()[0] if raw else ""
        try:
            used_s, total_s = first.split(",")
            used = int(used_s.strip())
            total = int(total_s.strip())
        except (ValueError, IndexError):
            logger.debug("nvidia-smi saída inesperada: %r", first[:80])
            self.vram = ""
            return
        # TUI-FOOTER-VRAM-PERCENT-01 (BLOCO 3): inclui o PERCENTUAL de uso, que
        # faltava no footer. Guarda total>0 (defensivo contra divisão por zero;
        # nvidia-smi reporta total>0 quando há GPU). O poll de 2s mantém o valor
        # em tempo real -- quando o modelo está na GPU o % sobe, quando degradou
        # para CPU o % fica baixo (sinal honesto de que NÃO está usando a GPU).
        pct = (used * 100 // total) if total > 0 else 0
        self.vram = f"VRAM {used}/{total} MiB ({pct}%)"

    def render(self) -> RenderResult:
        """Constrói Text com layout:

            Ctx X% | model | Iter N | Lidos M | Modif K | glyph state | [VRAM] | modo

        Fallback do glyph: `STATE_GLYPHS.get(state, STATE_GLYPHS["cold"])`
        garante render mesmo se reactive `model_state` receber valor fora
        do conjunto canônico (cold/warming/warm).

        O campo VRAM aparece após o glyph de estado e antes do bloco do modo,
        apenas quando `self.vram` é não-vazio (GPU presente). Sem GPU o campo
        é OMITIDO e o footer fica idêntico ao anterior.
        """
        msg = Text()
        msg.append(f"Ctx {self.ctx_pct}%", style=NYX_ACCENT)
        msg.append("  |  ", style=NYX_MUTED)
        msg.append(self._model, style=NYX_MUTED)
        msg.append("  |  ", style=NYX_MUTED)
        msg.append(f"Iter {self.iter_n}", style=NYX_MUTED)
        msg.append("  |  ", style=NYX_MUTED)
        msg.append(f"Lidos {self.reads}", style=NYX_MUTED)
        msg.append("  |  ", style=NYX_MUTED)
        msg.append(f"Modif {self.mods}", style=NYX_MUTED)
        msg.append("  |  ", style=NYX_MUTED)
        glyph = STATE_GLYPHS.get(self.model_state, STATE_GLYPHS["cold"])
        # TUI-FOOTER-CAPITALIZE-TERMS-01 (SPRINT 305): estado capitalizado para
        # exibição (Cold/Warming/Warm). O reactive model_state segue minúsculo
        # (chave de STATE_GLYPHS e da lógica); só o texto mostrado capitaliza.
        msg.append(f"{glyph} {self.model_state.capitalize()}", style=NYX_MUTED)
        # TUI-FOOTER-VRAM-REALTIME-01: campo VRAM em tempo real. Omitido
        # quando vazio (sem GPU / nvidia-smi ausente) -- degradação graciosa.
        # Rótulo/separador em NYX_MUTED, valor em NYX_ACCENT (zero hex).
        if self.vram:
            msg.append("  |  ", style=NYX_MUTED)
            msg.append(self.vram, style=NYX_ACCENT)
        # TUI-AGENT-BRIDGE-01: indicador de turno em execução com hint
        # de cancelamento via Ctrl+C. Inserido antes da secao do modo
        # para preservar legibilidade da extrema direita (modo) intacta.
        if self.inflight:
            msg.append("  |  ", style=NYX_MUTED)
            msg.append("executando (Ctrl+C cancela)", style=NYX_ACCENT)
        msg.append("    ", style=NYX_MUTED)
        # TUI-FOOTER-CAPITALIZE-TERMS-01 (SPRINT 305): termos do footer
        # capitalizados (Shift+Tab e os nomes dos modos). self.mode (a lógica)
        # segue minúsculo; só o display muda.
        if self.mode == "bypass":
            msg.append(" Bypass ON (Shift+Tab) ", style=f"bold {NYX_PURPLE_DIM}")
        elif self.mode == "plan":
            msg.append(" [Plan] read-only (Shift+Tab) ", style=f"bold {NYX_PURPLE}")
        elif self.mode == "sudo":
            msg.append(" [Sudo] elevado (Shift+Tab) ", style=f"bold {NYX_ERROR}")
        else:
            msg.append("Shift+Tab: Normal/Plan/Sudo/Bypass", style=NYX_MUTED)
        return msg

    # Watch handlers: cada mudança de reactive property dispara
    # self.refresh() automaticamente, mas declaramos explícitos para
    # clareza + extensibilidade (logging futuro, hooks de telemetria).
    def watch_ctx_pct(self, old: int, new: int) -> None:
        self.refresh()

    def watch_iter_n(self, old: int, new: int) -> None:
        self.refresh()

    def watch_reads(self, old: int, new: int) -> None:
        self.refresh()

    def watch_mods(self, old: int, new: int) -> None:
        self.refresh()

    def watch_model_state(self, old: str, new: str) -> None:
        self.refresh()

    def watch_mode(self, old: str, new: str) -> None:
        self.refresh()

    def watch_inflight(self, old: bool, new: bool) -> None:
        self.refresh()

    def watch_vram(self, old: str, new: str) -> None:
        self.refresh()


__all__ = ["Toolbar"]
