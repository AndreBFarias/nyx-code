"""Design Tokens Nyx -- fonte única da linguagem visual (v2).

Esta versão expande o sistema atual para suportar:

  - 5 estéticos visuais (arcano, cyber, brutalist, mecha, editorial)
  - 7 entidades do panteão (nyx, eris, juno, lars, luna, mars, somn)
  - Hot-reload em runtime (sem reiniciar o REPL)
  - Composição (aesthetic × entity) preservando a identidade estrutural

Compatível com a API atual de ``themes/design_tokens.py``: todas as constantes
exportadas (ANSI_ACCENT_FG, BOX_CHARS, BULLETS, SPINNER_FRAMES) continuam
disponíveis e retornam o tema ATIVO no momento da importação.

Ver ADR-023 (design tokens) e ADR-NEW-025 (multi-aesthetic).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


# ──────────────────────────────────────────────────────────────────────────────
# 1. UTILIDADES ANSI
# ──────────────────────────────────────────────────────────────────────────────


def hex_to_ansi_fg(hex_str: str) -> str:
    """Converte ``#RRGGBB`` para escape ANSI 24-bit foreground."""
    h = hex_str.lstrip("#")
    r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    return f"\033[38;2;{r};{g};{b}m"


def hex_to_ansi_bg(hex_str: str) -> str:
    """Converte ``#RRGGBB`` para escape ANSI 24-bit background."""
    h = hex_str.lstrip("#")
    r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    return f"\033[48;2;{r};{g};{b}m"


ANSI_DIM = "\033[2m"
ANSI_BOLD = "\033[1m"
ANSI_RESET = "\033[0m"


# ──────────────────────────────────────────────────────────────────────────────
# 2. PALETAS POR ESTÉTICO
# ──────────────────────────────────────────────────────────────────────────────


@dataclass(frozen=True)
class Palette:
    """Paleta de cores hex. ``ember`` é o destaque secundário do estético."""

    bg: str
    bg_soft: str
    bg_inset: str
    ink: str
    ink_dim: str
    ink_muted: str
    accent: str
    accent_lo: str
    ember: str
    success: str
    warning: str
    error: str
    info: str


@dataclass(frozen=True)
class Typography:
    mono: str
    display: str
    body: str
    mono_weight: int
    mono_track: str  # CSS letter-spacing equivalent — usado por front-end shadow
    mono_leading: float


@dataclass(frozen=True)
class Motion:
    typewriter_ms_per_char: int
    breathe: bool = False
    scanlines: bool = False
    grain: float = 0.0
    gauge_animation: bool = False
    glow_pulse: bool = False


@dataclass(frozen=True)
class Aesthetic:
    """Uma linguagem visual completa."""

    id: str
    name: str
    tagline: str
    description: str
    palette: Palette
    typography: Typography
    motion: Motion
    metaphor: str


AESTHETICS: dict[str, Aesthetic] = {
    "arcano": Aesthetic(
        id="arcano",
        name="Arcano",
        tagline="Invocando. Sussurrando. Traçando círculos.",
        description=(
            "Tipografia que respira. Bordas com leve halo. Ruído sutil de "
            "pergaminho. Sensação de estar lendo um grimório que pensa em código."
        ),
        palette=Palette(
            bg="#0E0820",
            bg_soft="#16102B",
            bg_inset="#08051A",
            ink="#E8E0D0",
            ink_dim="#9C8FB0",
            ink_muted="#5A4F70",
            accent="#9D4EDD",
            accent_lo="#5A189A",
            ember="#FFB454",
            success="#7DD3A0",
            warning="#FFB454",
            error="#E5484D",
            info="#86C5FF",
        ),
        typography=Typography(
            mono="JetBrains Mono",
            display="Cormorant Garamond",
            body="Cormorant Garamond",
            mono_weight=400,
            mono_track="0.01em",
            mono_leading=1.55,
        ),
        motion=Motion(typewriter_ms_per_char=18, breathe=True, glow_pulse=True, grain=0.04),
        metaphor="A interface é um altar. Cada comando, uma invocação.",
    ),
    "cyber": Aesthetic(
        id="cyber",
        name="Cyberpunk",
        tagline="Saturação calculada. ASCII como adrenalina.",
        description=(
            "Preto absoluto. Cyan e magenta gritando. Glitch sutil em transições. "
            "Tipografia geometricamente afiada."
        ),
        palette=Palette(
            bg="#000000",
            bg_soft="#0A0612",
            bg_inset="#050008",
            ink="#E0FFF7",
            ink_dim="#7AB8B0",
            ink_muted="#3A5856",
            accent="#00F5FF",
            accent_lo="#0088AA",
            ember="#FF00AA",
            success="#39FF14",
            warning="#FFE500",
            error="#FF003C",
            info="#00F5FF",
        ),
        typography=Typography(
            mono="JetBrains Mono",
            display="Space Grotesk",
            body="Inter",
            mono_weight=500,
            mono_track="0.02em",
            mono_leading=1.40,
        ),
        motion=Motion(typewriter_ms_per_char=8, scanlines=True),
        metaphor="Um console arrombado num cofre que não existe.",
    ),
    "brutalist": Aesthetic(
        id="brutalist",
        name="Brutalist",
        tagline="Uma cor de tinta. Tipografia como protagonista.",
        description=(
            "Papel branco. Tinta preta. Uma única cor de destaque (vermelho de "
            "errata). Nenhum efeito. Apenas tipografia, espaço e proporção."
        ),
        palette=Palette(
            bg="#FAFAF7",
            bg_soft="#F2F0E8",
            bg_inset="#E8E6DE",
            ink="#0A0A0A",
            ink_dim="#454545",
            ink_muted="#8A8A85",
            accent="#C8102E",
            accent_lo="#7A0A1C",
            ember="#1E3A8A",
            success="#0F5F2E",
            warning="#A05A00",
            error="#C8102E",
            info="#1E3A8A",
        ),
        typography=Typography(
            mono="iA Writer Quattro",
            display="Spectral",
            body="Spectral",
            mono_weight=400,
            mono_track="0",
            mono_leading=1.50,
        ),
        motion=Motion(typewriter_ms_per_char=22),  # tudo cuts, sem fade
        metaphor="Um livro técnico que decidiu rodar comandos.",
    ),
    "mecha": Aesthetic(
        id="mecha",
        name="Mecha",
        tagline="Instrumentação. Medidores. Aviso. Confirmado.",
        description=(
            "Aço escuro com grid sutil. Âmbar HUD para confirmação, vermelho-alarme "
            "para perigo. Sensação de mission control."
        ),
        palette=Palette(
            bg="#0C1117",
            bg_soft="#141B25",
            bg_inset="#070A0F",
            ink="#D1E8F2",
            ink_dim="#7A95A8",
            ink_muted="#3E5260",
            accent="#FFAB00",
            accent_lo="#B07600",
            ember="#FF3D3D",
            success="#00E676",
            warning="#FFAB00",
            error="#FF3D3D",
            info="#4A9EFF",
        ),
        typography=Typography(
            mono="JetBrains Mono",
            display="JetBrains Mono",
            body="Inter",
            mono_weight=500,
            mono_track="0.04em",
            mono_leading=1.45,
        ),
        motion=Motion(typewriter_ms_per_char=12, gauge_animation=True),
        metaphor="Um cockpit. Você é piloto.",
    ),
    "editorial": Aesthetic(
        id="editorial",
        name="Editorial",
        tagline="Marginalia. Notas de rodapé. Tipografia.",
        description=(
            "Papel creme. Serif elegante para títulos, mono para código. Margens "
            "largas, linhas numeradas, notas laterais."
        ),
        palette=Palette(
            bg="#F5F1E8",
            bg_soft="#EAE4D2",
            bg_inset="#2A2620",
            ink="#2A2A1F",
            ink_dim="#5C5848",
            ink_muted="#8C7D5F",
            accent="#9C2A1A",
            accent_lo="#5C1A10",
            ember="#1E3A8A",
            success="#2D5A0F",
            warning="#8B4500",
            error="#9C2A1A",
            info="#1E3A8A",
        ),
        typography=Typography(
            mono="Fira Code",
            display="Source Serif 4",
            body="Source Serif 4",
            mono_weight=450,
            mono_track="0",
            mono_leading=1.60,
        ),
        motion=Motion(typewriter_ms_per_char=20),
        metaphor="Um livro técnico que aprendeu a rodar comandos.",
    ),
}


# ──────────────────────────────────────────────────────────────────────────────
# 3. ENTIDADES (overrides de accent + glow)
# ──────────────────────────────────────────────────────────────────────────────


@dataclass(frozen=True)
class Entity:
    id: str
    name: str
    description: str
    accent: str
    accent_lo: str
    glow: str  # CSS rgba string
    mood: str  # palavras-chave da personalidade


ENTITIES: dict[str, Entity] = {
    "nyx": Entity(
        id="nyx",
        name="Nyx",
        description="Codificadora silenciosa. Cinza cirúrgico + turquesa técnica.",
        accent="#00D4AA",
        accent_lo="#007A63",
        glow="rgba(0, 212, 170, 0.35)",
        mood="silenciosa, precisa, monástica",
    ),
    "eris": Entity(
        id="eris",
        name="Eris",
        description="Caos púrpura. Vermelho + rosa sobre fundo profundo.",
        accent="#FF79C6",
        accent_lo="#B84785",
        glow="rgba(255, 121, 198, 0.40)",
        mood="caótica, provocadora, brilhante",
    ),
    "juno": Entity(
        id="juno",
        name="Juno",
        description="Verde orgânico + laranja quente. Natureza digital.",
        accent="#A4CB58",
        accent_lo="#6F8B3A",
        glow="rgba(164, 203, 88, 0.30)",
        mood="fértil, generosa, paciente",
    ),
    "lars": Entity(
        id="lars",
        name="Lars",
        description="Verde matrix + cyan. Terminal clássico.",
        accent="#50FA7B",
        accent_lo="#2A8C44",
        glow="rgba(80, 250, 123, 0.35)",
        mood="veterana, direta, old-school",
    ),
    "luna": Entity(
        id="luna",
        name="Luna",
        description="Dracula gótico. Roxo profundo + rosa neon.",
        accent="#BD93F9",
        accent_lo="#7A5BC9",
        glow="rgba(189, 147, 249, 0.40)",
        mood="melancólica, lúcida, romântica",
    ),
    "mars": Entity(
        id="mars",
        name="Mars",
        description="Vermelho agressivo sobre negro absoluto.",
        accent="#FF5555",
        accent_lo="#992F2F",
        glow="rgba(255, 85, 85, 0.40)",
        mood="guerreira, urgente, decidida",
    ),
    "somn": Entity(
        id="somn",
        name="Somn",
        description="Azul profundo noturno. Cyan + roxo sobre escuridão.",
        accent="#8BE9FD",
        accent_lo="#4A8AA0",
        glow="rgba(139, 233, 253, 0.35)",
        mood="onírica, fluida, telepática",
    ),
}


# ──────────────────────────────────────────────────────────────────────────────
# 4. THEME = AESTHETIC × ENTITY (composto)
# ──────────────────────────────────────────────────────────────────────────────


@dataclass
class Theme:
    """Tema composto. Imutável após criação; troque via ``apply_theme()``.

    Entity sobrescreve APENAS accent/accent_lo/glow — a identidade estrutural
    (background, ember, tipografia, motion) pertence ao estético.
    """

    aesthetic: Aesthetic
    entity: Entity
    palette: Palette
    typography: Typography
    motion: Motion

    @classmethod
    def compose(cls, aesthetic_id: str, entity_id: str) -> "Theme":
        a = AESTHETICS[aesthetic_id]
        e = ENTITIES[entity_id]
        # entity override
        p = Palette(
            bg=a.palette.bg,
            bg_soft=a.palette.bg_soft,
            bg_inset=a.palette.bg_inset,
            ink=a.palette.ink,
            ink_dim=a.palette.ink_dim,
            ink_muted=a.palette.ink_muted,
            accent=e.accent,
            accent_lo=e.accent_lo,
            ember=a.palette.ember,
            success=a.palette.success,
            warning=a.palette.warning,
            error=a.palette.error,
            info=a.palette.info,
        )
        return cls(aesthetic=a, entity=e, palette=p, typography=a.typography, motion=a.motion)

    # ── ANSI helpers (mais conveniente que reescrever em todo callsite) ──

    @property
    def ansi_accent_fg(self) -> str:
        return hex_to_ansi_fg(self.palette.accent)

    @property
    def ansi_ember_fg(self) -> str:
        return hex_to_ansi_fg(self.palette.ember)

    @property
    def ansi_primary_fg(self) -> str:
        return hex_to_ansi_fg(self.palette.ink)

    @property
    def ansi_muted_fg(self) -> str:
        return hex_to_ansi_fg(self.palette.ink_dim)

    @property
    def ansi_error_fg(self) -> str:
        return hex_to_ansi_fg(self.palette.error)

    @property
    def ansi_success_fg(self) -> str:
        return hex_to_ansi_fg(self.palette.success)

    @property
    def ansi_warning_fg(self) -> str:
        return hex_to_ansi_fg(self.palette.warning)


# ──────────────────────────────────────────────────────────────────────────────
# 5. SINGLETON DO TEMA ATIVO
# ──────────────────────────────────────────────────────────────────────────────


_active_theme: Theme = Theme.compose("arcano", "nyx")
_observers: list[Any] = []


def get_active_theme() -> Theme:
    return _active_theme


def apply_theme(aesthetic_id: str | None = None, entity_id: str | None = None) -> Theme:
    """Troca o tema ativo. Hot-reload: notifica observadores registrados.

    Pode passar só um dos dois — o outro fica preservado.
    """
    global _active_theme
    current = _active_theme
    a = aesthetic_id or current.aesthetic.id
    e = entity_id or current.entity.id
    _active_theme = Theme.compose(a, e)
    for obs in _observers:
        try:
            obs(_active_theme)
        except Exception:  # noqa: BLE001 — observers não devem derrubar swap
            pass
    return _active_theme


def subscribe(observer: Any) -> None:
    """Registra função ``observer(theme: Theme)`` chamada em todo swap."""
    _observers.append(observer)


def unsubscribe(observer: Any) -> None:
    if observer in _observers:
        _observers.remove(observer)


# ──────────────────────────────────────────────────────────────────────────────
# 6. RETRO-COMPATIBILIDADE
# Mantém a API antiga (constantes globais) apontando para o tema ATIVO no
# momento da importação. Código legado continua funcionando.
# ──────────────────────────────────────────────────────────────────────────────


NYX_ACCENT = _active_theme.palette.accent
NYX_ACCENT_DIM = _active_theme.palette.accent_lo
NYX_PURPLE = "#9D4EDD"
NYX_PURPLE_DIM = "#5A189A"
NYX_PRIMARY = _active_theme.palette.ink
NYX_MUTED = _active_theme.palette.ink_dim
NYX_BG = _active_theme.palette.bg
NYX_BG_SOFT = _active_theme.palette.bg_soft
NYX_SUCCESS = _active_theme.palette.success
NYX_WARNING = _active_theme.palette.warning
NYX_ERROR = _active_theme.palette.error

ANSI_ACCENT_FG = _active_theme.ansi_accent_fg
ANSI_PURPLE_FG = hex_to_ansi_fg(NYX_PURPLE)
ANSI_PRIMARY_FG = _active_theme.ansi_primary_fg
ANSI_MUTED_FG = _active_theme.ansi_muted_fg
ANSI_ERROR_FG = _active_theme.ansi_error_fg
ANSI_SUCCESS_FG = _active_theme.ansi_success_fg
ANSI_WARNING_FG = _active_theme.ansi_warning_fg


__all__ = [
    # composição
    "Theme", "Aesthetic", "Entity", "Palette", "Typography", "Motion",
    "AESTHETICS", "ENTITIES",
    "get_active_theme", "apply_theme", "subscribe", "unsubscribe",
    # ANSI utils
    "hex_to_ansi_fg", "hex_to_ansi_bg",
    "ANSI_DIM", "ANSI_BOLD", "ANSI_RESET",
    # retro-compat
    "NYX_ACCENT", "NYX_ACCENT_DIM", "NYX_PURPLE", "NYX_PURPLE_DIM",
    "NYX_PRIMARY", "NYX_MUTED", "NYX_BG", "NYX_BG_SOFT",
    "NYX_SUCCESS", "NYX_WARNING", "NYX_ERROR",
    "ANSI_ACCENT_FG", "ANSI_PURPLE_FG", "ANSI_PRIMARY_FG", "ANSI_MUTED_FG",
    "ANSI_ERROR_FG", "ANSI_SUCCESS_FG", "ANSI_WARNING_FG",
]


# "A linguagem do produto começa pela consistência de seus tokens." -- anônimo
