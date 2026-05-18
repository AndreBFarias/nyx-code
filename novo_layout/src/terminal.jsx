// =============================================================================
// NYX TERMINAL — Simulador renderizado como React
// Recebe um array de "lines" (frames declarativos) e desenha como terminal.
// Cada tema injeta CSS vars; o terminal é agnóstico ao tema.
// =============================================================================

const { useEffect, useState, useRef, useMemo, createContext, useContext } = React;

// ─── Context do tema ──────────────────────────────────────────────────────────
const ThemeCtx = createContext(null);

function ThemeProvider({ aesthetic = "arcano", entity = "nyx", children }) {
  const theme = useMemo(
    () => window.NYX_COMPOSE(aesthetic, entity),
    [aesthetic, entity]
  );
  return <ThemeCtx.Provider value={theme}>{children}</ThemeCtx.Provider>;
}

function useTheme() {
  return useContext(ThemeCtx);
}

// ─── Util: aplica tema como CSS vars num elemento ────────────────────────────
function themeVars(theme) {
  const p = theme.palette;
  return {
    "--bg": p.bg,
    "--bg-soft": p.bg_soft,
    "--bg-inset": p.bg_inset,
    "--ink": p.ink,
    "--ink-dim": p.ink_dim,
    "--ink-muted": p.ink_muted,
    "--accent": p.accent,
    "--accent-lo": p.accent_lo,
    "--ember": p.ember,
    "--success": p.success,
    "--warning": p.warning,
    "--error": p.error,
    "--info": p.info,
    "--glow": p.glow,
    "--glow-soft": p.glow_soft,
    "--mono": theme.type.mono,
    "--display": theme.type.display,
    "--body": theme.type.body,
    "--mono-weight": theme.type.mono_weight,
    "--mono-track": theme.type.mono_track,
    "--mono-leading": theme.type.mono_leading,
  };
}

// ─── Renderiza segmentos coloridos numa linha ────────────────────────────────
// Aceita string OU array de {t, c, b} (texto, classe de cor, bold?)
function renderSegments(content) {
  if (typeof content === "string") return content;
  if (!Array.isArray(content)) return String(content);
  return content.map((seg, i) => {
    if (typeof seg === "string") return <span key={i}>{seg}</span>;
    const { t, c, b, dim, blink } = seg;
    const cls = [
      c ? `c-${c}` : "",
      b ? "bold" : "",
      dim ? "dim" : "",
      blink ? "blink" : "",
    ]
      .filter(Boolean)
      .join(" ");
    return (
      <span key={i} className={cls}>
        {t}
      </span>
    );
  });
}

// ─── Linha estática ──────────────────────────────────────────────────────────
function Line({ content, className = "" }) {
  return (
    <div className={`line ${className}`}>
      {renderSegments(content)}
      {"\u200B" /* zero-width to preserve empty-line height */}
    </div>
  );
}

// ─── Linha com typewriter ────────────────────────────────────────────────────
function TypeLine({ text, speed = 18, delay = 0, className = "", onDone, cursor = true }) {
  const [shown, setShown] = useState(0);
  const [started, setStarted] = useState(delay === 0);

  useEffect(() => {
    if (!started) {
      const t = setTimeout(() => setStarted(true), delay);
      return () => clearTimeout(t);
    }
  }, [delay, started]);

  useEffect(() => {
    if (!started) return;
    if (shown >= text.length) {
      onDone && onDone();
      return;
    }
    const t = setTimeout(() => setShown((s) => s + 1), speed);
    return () => clearTimeout(t);
  }, [shown, started, text.length, speed, onDone]);

  const done = shown >= text.length;
  return (
    <div className={`line ${className}`}>
      {text.slice(0, shown)}
      {!done && cursor && <span className="cursor">▍</span>}
    </div>
  );
}

// ─── Spinner Braille animado ─────────────────────────────────────────────────
function BrailleSpinner({ label = "pensando", color = "accent" }) {
  const [frame, setFrame] = useState(0);
  const frames = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"];
  useEffect(() => {
    const t = setInterval(() => setFrame((f) => (f + 1) % frames.length), 80);
    return () => clearInterval(t);
  }, []);
  return (
    <span className="spinner">
      <span className={`c-${color}`}>{frames[frame]}</span>
      <span className="dim"> {label}</span>
    </span>
  );
}

// ─── Progress meter (bar) ────────────────────────────────────────────────────
function Meter({ value = 0.5, width = 24, color = "accent", glyphs }) {
  const filled = Math.round(value * width);
  const empty = width - filled;
  const full = glyphs?.meter_full || "█";
  const emp = glyphs?.meter_empty || "░";
  return (
    <span className="meter">
      <span className={`c-${color}`}>{full.repeat(filled)}</span>
      <span className="dim">{emp.repeat(empty)}</span>
    </span>
  );
}

// ─── O terminal em si — wrapper estilizado ───────────────────────────────────
function Terminal({ children, height, scrollable = false, label, dense = false, scanlines = false }) {
  const theme = useTheme();
  const style = themeVars(theme);
  const cls = [
    "term",
    `term-${theme.aestheticKey}`,
    dense ? "term-dense" : "",
    scanlines ? "term-scanlines" : "",
    scrollable ? "term-scroll" : "",
  ]
    .filter(Boolean)
    .join(" ");

  return (
    <div className={cls} style={{ ...style, height: height || undefined }}>
      {label && <div className="term-label">{label}</div>}
      <div className="term-body">{children}</div>
    </div>
  );
}

// ─── Empty line ──────────────────────────────────────────────────────────────
function Empty() {
  return <Line content="" />;
}

// ─── Block: usa box drawing pra desenhar uma caixa em torno de filhos ────────
// Helper que pega glyphs do tema atual
function useGlyphs() {
  return useTheme().glyphs;
}

function BoxTop({ width = 70, label, status, color = "accent" }) {
  const g = useGlyphs();
  const labelStr = label ? ` ${label} ` : "";
  const statusStr = status ? ` ${status} ` : "";
  const inner = width - 4 - labelStr.length - statusStr.length;
  const left = labelStr ? `${g.tl}${g.h}${labelStr}` : `${g.tl}${g.h.repeat(2)}`;
  const right = statusStr ? `${statusStr}${g.h}${g.tr}` : `${g.h.repeat(2)}${g.tr}`;
  return (
    <Line
      content={[
        { t: "  ", c: "" },
        { t: left, c: color },
        { t: g.h.repeat(Math.max(2, inner)), c: color, dim: true },
        { t: right, c: color },
      ]}
    />
  );
}

function BoxBottom({ width = 70, label, color = "accent" }) {
  const g = useGlyphs();
  const labelStr = label ? ` ${label} ` : "";
  const inner = width - 4 - labelStr.length;
  return (
    <Line
      content={[
        { t: "  ", c: "" },
        { t: `${g.bl}${g.h.repeat(2)}`, c: color, dim: true },
        ...(labelStr ? [{ t: labelStr, c: color, dim: true }] : []),
        { t: g.h.repeat(Math.max(2, inner)), c: color, dim: true },
        { t: `${g.h.repeat(2)}${g.br}`, c: color, dim: true },
      ]}
    />
  );
}

function BoxLine({ children, color = "accent" }) {
  const g = useGlyphs();
  return (
    <div className="line">
      <span>{"  "}</span>
      <span className={`c-${color} dim`}>{g.v}</span>
      <span>{"  "}</span>
      {Array.isArray(children) ? renderSegments(children) : children}
    </div>
  );
}

// ─── Footer status bar (— ctx 42% — modelo — iter 3 —) ────────────────────────
function FooterBar({ pct = 42, model = "qwen3:4b", iter = 3, reads = 4, mods = 1, width = 76 }) {
  const g = useGlyphs();
  const body = `ctx ${pct}% · ${model} · iter ${iter} · lidos ${reads} · modif ${mods}`;
  const pad = Math.max(2, width - body.length - 4);
  return (
    <Line
      content={[
        { t: `${g.h.repeat(2)} `, c: "accent", dim: true },
        { t: body, c: "accent", dim: true },
        { t: ` ${g.h.repeat(pad)}`, c: "accent", dim: true },
      ]}
    />
  );
}

// Export to window
Object.assign(window, {
  ThemeProvider,
  useTheme,
  useGlyphs,
  Terminal,
  Line,
  Empty,
  TypeLine,
  BrailleSpinner,
  Meter,
  BoxTop,
  BoxBottom,
  BoxLine,
  FooterBar,
  themeVars,
});
