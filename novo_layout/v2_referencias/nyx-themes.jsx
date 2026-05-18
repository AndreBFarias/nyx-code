// nyx-themes.jsx — Token sets for each variation.
// A theme is a complete styling spec consumed by the shared renderer.
// Differences: chrome colors, accents, block styles (user/nyx/tool/thinking),
// heading capitalization, prefix glyphs.

const THEME_EDITORIAL = {
  id: "editorial",
  name: "Editorial",
  blurb: "Tipografia primeiro. Sem caixas. Hierarquia por cor e espaço.",
  // Chrome (terminal window)
  chromeBg: "#1f1d2a",
  chromeBorder: "#13111c",
  chromeFg: "#d8d8e2",
  // Content
  bg: "#1e1c28",
  fg: "#e8e6f0",
  muted: "#8a87a3",
  faint: "#5d5b75",
  accent: "#bd93f9",       // Luna violet
  accent2: "#8be9fd",       // Somn cyan
  ok: "#7ed29a",
  err: "#ff7a8a",
  warn: "#f1c878",
  // Block treatments
  userPrefix: "›",
  nyxPrefix: "◆",
  // Bubbles
  userBubble: { kind: "subtle-line", color: "#8be9fd" },
  nyxBubble:  { kind: "header-bar",  color: "#bd93f9" },
  // Tool calls / thinking
  toolStyle: "inline",       // ≡ name args · time · ok
  thinkingStyle: "row",      // single collapsed row
  divider: "thin",
  headingCase: "sentence",
  bannerStyle: "type",
};

const THEME_ARCANO = {
  id: "arcano",
  name: "Arcano",
  blurb: "Violeta noturno, turquesa ritualística, glyphs ornamentais.",
  chromeBg: "#1a1428",
  chromeBorder: "#0c0814",
  chromeFg: "#d4cdf0",
  bg: "#150f23",
  fg: "#ece6ff",
  muted: "#8a82b8",
  faint: "#5c557d",
  accent: "#bd93f9",
  accent2: "#00d4aa",
  ok: "#00d4aa",
  err: "#ff5e7a",
  warn: "#ffb86c",
  userPrefix: "❯",
  nyxPrefix: "✦",
  userBubble: { kind: "ornament-box", color: "#00d4aa" },
  nyxBubble:  { kind: "glow-bar",     color: "#bd93f9" },
  toolStyle: "ornament-chip",
  thinkingStyle: "ornament-row",
  divider: "ornament",
  headingCase: "sentence",
  bannerStyle: "ascii-glow",
};

const THEME_BRUTALIST = {
  id: "brutalist",
  name: "Brutalist Mono",
  blurb: "Densidade máxima. Sem cor exceto status. Tudo maiúsculo nos rótulos.",
  chromeBg: "#0a0a0a",
  chromeBorder: "#000",
  chromeFg: "#d8d8d8",
  bg: "#0a0a0a",
  fg: "#e6e6e6",
  muted: "#8a8a8a",
  faint: "#4a4a4a",
  accent: "#e6e6e6",
  accent2: "#bd93f9",
  ok: "#9be08b",
  err: "#ff5e5e",
  warn: "#e6c870",
  userPrefix: "›",
  nyxPrefix: "›",
  userBubble: { kind: "bracket-label", color: "#e6e6e6" },
  nyxBubble:  { kind: "bracket-label", color: "#e6e6e6" },
  toolStyle: "table-row",
  thinkingStyle: "bracket-row",
  divider: "rule",
  headingCase: "upper",
  bannerStyle: "rule",
};

const THEME_HYBRID = {
  id: "hybrid",
  name: "Hybrid · recomendada",
  blurb: "Refinamento da paleta Dracula com afetos da Nyx. Equilíbrio entre densidade e respiro.",
  chromeBg: "#252434",
  chromeBorder: "#16151f",
  chromeFg: "#d8d8e2",
  bg: "#1f1e2b",
  fg: "#f0eef8",
  muted: "#9590b3",
  faint: "#5d5b75",
  accent: "#bd93f9",
  accent2: "#8be9fd",
  ok: "#7ed29a",
  err: "#ff7a8a",
  warn: "#f1c878",
  userPrefix: "›",
  nyxPrefix: "◆",
  userBubble: { kind: "soft-box",  color: "#8be9fd" },
  nyxBubble:  { kind: "side-rule", color: "#bd93f9" },
  toolStyle: "chip",
  thinkingStyle: "collapsible",
  divider: "thin",
  headingCase: "sentence",
  bannerStyle: "card",
};

window.NYX_THEMES = {
  editorial: THEME_EDITORIAL,
  arcano:    THEME_ARCANO,
  brutalist: THEME_BRUTALIST,
  hybrid:    THEME_HYBRID,
};
