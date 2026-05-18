// =============================================================================
// NYX CODE — SISTEMA DE TEMAS
// 5 estéticos visuais × 7 entidades (overrides de cor)
// Cada estético define: bg, tipografia, glifos, peso, ritmo.
// Cada entidade injeta seu accent + glow característico.
// =============================================================================

// ─── ESTÉTICOS ────────────────────────────────────────────────────────────────
// Cada estético é uma linguagem visual completa. Mesmo banner, mesmo cardr,
// mesmo prompt — mas falando uma língua diferente.

const AESTHETICS = {
  // 1. ARCANO ─ Nyx como deusa da noite. Invocação, ritual.
  arcano: {
    name: "Arcano",
    tagline: "Invocando. Sussurrando. Tracejando círculos.",
    description:
      "Tipografia que respira. Bordas com leve halo. Ruído sutil de pergaminho. " +
      "A sensação é de estar lendo um grimório que pensa em código.",
    palette: {
      bg:        "#0E0820",  // azul-violeta da noite profunda
      bg_soft:   "#16102B",  // painéis levemente elevados
      bg_inset:  "#08051A",  // fundo de code blocks (poço)
      ink:       "#E8E0D0",  // creme antigo — texto primário
      ink_dim:   "#9C8FB0",  // mauve poeirento — secundário
      ink_muted: "#5A4F70",  // sombra de tinta
      accent:    "#9D4EDD",  // violeta-runa
      accent_lo: "#5A189A",  // mesma cor sob brasa
      ember:     "#FFB454",  // âmbar de vela — destaque ritual
      success:   "#7DD3A0",  // verde-musgo
      warning:   "#FFB454",
      error:     "#E5484D",
      info:      "#86C5FF",
      // brilho/halo
      glow:      "rgba(157, 78, 221, 0.35)",
      glow_soft: "rgba(157, 78, 221, 0.15)",
    },
    type: {
      mono:    "'JetBrains Mono', 'Fira Code', monospace",
      display: "'Cormorant Garamond', 'EB Garamond', serif",
      body:    "'Cormorant Garamond', serif",
      mono_weight: 400,
      mono_track: "0.01em",
      mono_leading: 1.55,
    },
    glyphs: {
      // bordas tracejadas, suaves
      tl: "╭", tr: "╮", bl: "╰", br: "╯",
      h: "─", v: "│",
      // junções e cruzamentos
      tjoin: "┬", bjoin: "┴", cross: "┼", ljoin: "├", rjoin: "┤",
      // ornamentos arcanos sem emoji
      bullet: "·",
      mark: "",  // U+2726 Black Four Pointed Star — está em Dingbats, ATENÇÃO emoji range
      // SAFE: trocar por chars seguros
      mark_safe: "*",
      separator: "─ ─ ─",
      whisper: "⢀⢄⢤⣠⣄⣀",  // partículas Braille pra spinner
      pulse: ["⠂", "⠐", "⠠", "⠐", "⠂"],  // batida cardíaca
      arrow: "→",
      heading_rule: "━━━",
      corner_l: "┌",
      corner_r: "┐",
    },
    motion: {
      breathe: true,     // accent breathes (opacity cycle)
      typewriter_speed: 18,  // ms/char
      grain: 0.04,       // film grain alpha
      glow_pulse: true,
    },
    metaphor: "A interface é um altar. Cada comando, uma invocação.",
  },

  // 2. CYBERPUNK ─ Haxxor moderno. Saturado. Rápido. Perigoso.
  cyber: {
    name: "Cyberpunk",
    tagline: "Saturação calculada. ASCII como adrenalina.",
    description:
      "Preto absoluto. Cyan e magenta gritando. Glitch sutil em transições. " +
      "Tipografia geometricamente afiada. Sensação de estar atrás de 7 proxies.",
    palette: {
      bg:        "#000000",
      bg_soft:   "#0A0612",
      bg_inset:  "#050008",
      ink:       "#E0FFF7",
      ink_dim:   "#7AB8B0",
      ink_muted: "#3A5856",
      accent:    "#00F5FF",   // cyan elétrico
      accent_lo: "#0088AA",
      ember:     "#FF00AA",   // magenta neon
      success:   "#39FF14",   // lime irradiando
      warning:   "#FFE500",
      error:     "#FF003C",
      info:      "#00F5FF",
      glow:      "rgba(0, 245, 255, 0.5)",
      glow_soft: "rgba(255, 0, 170, 0.25)",
    },
    type: {
      mono:    "'JetBrains Mono', 'IBM Plex Mono', monospace",
      display: "'Space Grotesk', 'Space Mono', sans-serif",
      body:    "'Inter', sans-serif",
      mono_weight: 500,
      mono_track: "0.02em",
      mono_leading: 1.4,
    },
    glyphs: {
      tl: "┏", tr: "┓", bl: "┗", br: "┛",
      h: "━", v: "┃",
      tjoin: "┳", bjoin: "┻", cross: "╋", ljoin: "┣", rjoin: "┫",
      bullet: "",
      mark_safe: "",
      separator: "━ ━ ━",
      whisper: "⣿⣷⣯⣟⡿⢿",
      pulse: ["", "", ""],
      arrow: "",
      heading_rule: "━━━",
    },
    motion: {
      scanlines: true,
      typewriter_speed: 8,
      glitch_chance: 0.02,
      chromatic_aberration: true,
    },
    metaphor: "Um console arrombado num cofre que não existe.",
  },

  // 3. BRUTALIST ─ Manuscrito de Knuth. Branco. Quieto. Preciso.
  brutalist: {
    name: "Brutalist",
    tagline: "Uma cor de tinta. Tipografia como protagonista.",
    description:
      "Papel branco. Tinta preta. Uma única cor de destaque (vermelho de errata). " +
      "Nenhum efeito. Apenas tipografia, espaço e proporção. Knuth aprovaria.",
    palette: {
      bg:        "#FAFAF7",   // papel cru
      bg_soft:   "#F2F0E8",
      bg_inset:  "#E8E6DE",
      ink:       "#0A0A0A",
      ink_dim:   "#454545",
      ink_muted: "#8A8A85",
      accent:    "#C8102E",   // tinta vermelha de marginalia
      accent_lo: "#7A0A1C",
      ember:     "#1E3A8A",   // azul de carimbo (uso raro)
      success:   "#0F5F2E",
      warning:   "#A05A00",
      error:     "#C8102E",
      info:      "#1E3A8A",
      glow:      "transparent",
      glow_soft: "transparent",
    },
    type: {
      mono:    "'iA Writer Quattro', 'IBM Plex Mono', 'Courier New', monospace",
      display: "'Spectral', 'EB Garamond', serif",
      body:    "'Spectral', serif",
      mono_weight: 400,
      mono_track: "0",
      mono_leading: 1.5,
    },
    glyphs: {
      tl: "+", tr: "+", bl: "+", br: "+",   // canto austero
      h: "-", v: "|",
      tjoin: "+", bjoin: "+", cross: "+", ljoin: "+", rjoin: "+",
      bullet: "—",
      mark_safe: "§",
      separator: "* * *",
      whisper: "....",
      pulse: [".", "·", "•", "·"],
      arrow: "→",
      heading_rule: "═══",
    },
    motion: {
      breathe: false,
      typewriter_speed: 22,
      no_animation: true,    // tudo cuts, sem fade
    },
    metaphor: "Um livro técnico que decidiu rodar comandos.",
  },

  // 4. MECHA ─ HUD de cockpit. Telemetria visível.
  mecha: {
    name: "Mecha",
    tagline: "Instrumentação. Medidores. Aviso. Confirmado.",
    description:
      "Aço escuro com grid sutil. Âmbar HUD para confirmação, vermelho-alarme " +
      "para perigo. Telemetria do modelo sempre visível. Sensação de mission control.",
    palette: {
      bg:        "#0C1117",
      bg_soft:   "#141B25",
      bg_inset:  "#070A0F",
      ink:       "#D1E8F2",
      ink_dim:   "#7A95A8",
      ink_muted: "#3E5260",
      accent:    "#FFAB00",   // âmbar HUD
      accent_lo: "#B07600",
      ember:     "#FF3D3D",   // alarme
      success:   "#00E676",
      warning:   "#FFAB00",
      error:     "#FF3D3D",
      info:      "#4A9EFF",
      glow:      "rgba(255, 171, 0, 0.4)",
      glow_soft: "rgba(74, 158, 255, 0.2)",
    },
    type: {
      mono:    "'JetBrains Mono', 'Berkeley Mono', monospace",
      display: "'JetBrains Mono', monospace",
      body:    "'Inter', 'IBM Plex Sans', sans-serif",
      mono_weight: 500,
      mono_track: "0.04em",
      mono_leading: 1.45,
    },
    glyphs: {
      tl: "┏", tr: "┓", bl: "┗", br: "┛",
      h: "━", v: "┃",
      tjoin: "┳", bjoin: "┻", cross: "╋", ljoin: "┣", rjoin: "┫",
      bullet: "",
      mark_safe: "",
      separator: "━━━",
      whisper: "▁▂▃▄▅▆▇█",
      pulse: ["▁", "▃", "▅", "▇", "▅", "▃"],
      arrow: "",
      heading_rule: "━━━",
      meter_full: "█",
      meter_empty: "░",
      meter_partial: ["░", "▒", "▓", "█"],
    },
    motion: {
      gauge_animation: true,
      typewriter_speed: 12,
      scan_line: true,
      blink_warning: true,
    },
    metaphor: "Um cockpit. Você é piloto.",
  },

  // 5. EDITORIAL ─ Livro técnico aprende a rodar.
  editorial: {
    name: "Editorial",
    tagline: "Marginalia. Notas de rodapé. Tipografia.",
    description:
      "Papel creme. Serif elegante para títulos, mono para código. Margens " +
      "largas, linhas numeradas, notas laterais. O'Reilly se virasse terminal.",
    palette: {
      bg:        "#F5F1E8",   // creme de papel
      bg_soft:   "#EAE4D2",
      bg_inset:  "#2A2620",   // code blocks invertem
      ink:       "#2A2A1F",
      ink_dim:   "#5C5848",
      ink_muted: "#8C7D5F",
      accent:    "#9C2A1A",   // vermelho de capa antiga
      accent_lo: "#5C1A10",
      ember:     "#1E3A8A",   // indigo de link
      success:   "#2D5A0F",
      warning:   "#8B4500",
      error:     "#9C2A1A",
      info:      "#1E3A8A",
      glow:      "transparent",
      glow_soft: "rgba(156, 42, 26, 0.08)",
    },
    type: {
      mono:    "'Fira Code', 'IBM Plex Mono', monospace",
      display: "'Source Serif 4', 'Crimson Pro', serif",
      body:    "'Source Serif 4', 'Crimson Pro', serif",
      mono_weight: 450,
      mono_track: "0",
      mono_leading: 1.6,
    },
    glyphs: {
      tl: "┌", tr: "┐", bl: "└", br: "┘",
      h: "─", v: "│",
      tjoin: "┬", bjoin: "┴", cross: "┼", ljoin: "├", rjoin: "┤",
      bullet: "·",
      mark_safe: "¶",
      separator: "  ",  // ATENÇÃO U+2766 está em Dingbats — pode bater no banimento
      separator_safe: "* * *",
      whisper: "....",
      pulse: [".", "·", "•", "·"],
      arrow: "→",
      heading_rule: "═══",
      footnote_sep: "──────",
    },
    motion: {
      breathe: false,
      typewriter_speed: 20,
      page_turn: true,   // fade entre seções
    },
    metaphor: "Um livro técnico que aprendeu a rodar comandos.",
  },
};

// ─── ENTIDADES ────────────────────────────────────────────────────────────────
// Overrides de accent + glow. Não mudam tipografia ou bg de cada estético.
// Cada entidade reflete uma personalidade do panteão.

const ENTITIES = {
  nyx: {
    name: "Nyx",
    description: "Codificadora silenciosa. Cinza cirúrgico + cyan técnico.",
    accent: "#00D4AA",      // turquesa (default)
    accent_lo: "#007A63",
    ember: "#9D4EDD",       // roxo de memória/skill
    glow: "rgba(0, 212, 170, 0.35)",
    mood: "silenciosa, precisa, monástica",
  },
  eris: {
    name: "Eris",
    description: "Caos púrpura. Vermelho + rosa sobre fundo profundo.",
    accent: "#FF79C6",
    accent_lo: "#B84785",
    ember: "#FFB86C",
    glow: "rgba(255, 121, 198, 0.40)",
    mood: "caótica, provocadora, brilhante",
  },
  juno: {
    name: "Juno",
    description: "Verde orgânico + laranja quente. Natureza digital.",
    accent: "#A4CB58",
    accent_lo: "#6F8B3A",
    ember: "#F4A261",
    glow: "rgba(164, 203, 88, 0.30)",
    mood: "fértil, generosa, paciente",
  },
  lars: {
    name: "Lars",
    description: "Verde matrix + cyan. Terminal clássico.",
    accent: "#50FA7B",
    accent_lo: "#2A8C44",
    ember: "#8BE9FD",
    glow: "rgba(80, 250, 123, 0.35)",
    mood: "veterana, direta, old-school",
  },
  luna: {
    name: "Luna",
    description: "Dracula gothic. Roxo profundo + rosa neon.",
    accent: "#BD93F9",
    accent_lo: "#7A5BC9",
    ember: "#FF79C6",
    glow: "rgba(189, 147, 249, 0.40)",
    mood: "melancólica, lúcida, romântica",
  },
  mars: {
    name: "Mars",
    description: "Vermelho agressivo sobre negro absoluto.",
    accent: "#FF5555",
    accent_lo: "#992F2F",
    ember: "#FFB86C",
    glow: "rgba(255, 85, 85, 0.40)",
    mood: "guerreira, urgente, decidida",
  },
  somn: {
    name: "Somn",
    description: "Azul profundo noturno. Cyan + roxo sobre escuridão.",
    accent: "#8BE9FD",
    accent_lo: "#4A8AA0",
    ember: "#BD93F9",
    glow: "rgba(139, 233, 253, 0.35)",
    mood: "onírica, fluida, telepática",
  },
};

// Helper: compõe um tema final (aesthetic × entity)
// Entity sobrescreve APENAS accent + glow (a "voz" da entidade).
// Ember (cor de alerta/destaque secundário) e bg ficam do estético — são
// parte da identidade estrutural da língua visual.
function composeTheme(aestheticKey, entityKey) {
  const a = AESTHETICS[aestheticKey];
  const e = ENTITIES[entityKey];
  return {
    aestheticKey,
    entityKey,
    ...a,
    palette: {
      ...a.palette,
      accent: e.accent,
      accent_lo: e.accent_lo,
      glow: e.glow,
      // ember mantém-se do estético (amber-HUD pro mecha, magenta pro cyber, etc)
    },
    entity: e,
  };
}

window.NYX_AESTHETICS = AESTHETICS;
window.NYX_ENTITIES = ENTITIES;
window.NYX_COMPOSE = composeTheme;
