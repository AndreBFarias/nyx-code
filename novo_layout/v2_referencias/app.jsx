// app.jsx — Main app. Wires audit + four terminal variations into a
// design canvas. Each terminal has Play/Reset that rolls the session.

const { useState, useEffect, useRef } = React;

// ─── PlayableTerminal ────────────────────────────────────────────────
// Wraps TerminalFrame + NyxSession with rolling reveal.
const PlayableTerminal = ({ theme, title }) => {
  const totalBlocks = window.NYX_SESSION.length;
  const [reveal, setReveal] = useState(totalBlocks);  // Show full by default
  const [playing, setPlaying] = useState(false);
  const scrollRef = useRef(null);
  const timerRef = useRef(null);

  const stepDelay = 900;  // ms between blocks during play

  const play = () => {
    setReveal(1);
    setPlaying(true);
  };
  const reset = () => {
    if (timerRef.current) clearTimeout(timerRef.current);
    setReveal(totalBlocks);
    setPlaying(false);
  };

  useEffect(() => {
    if (!playing) return;
    if (reveal >= totalBlocks) { setPlaying(false); return; }
    timerRef.current = setTimeout(() => setReveal((r) => r + 1), stepDelay);
    return () => clearTimeout(timerRef.current);
  }, [playing, reveal, totalBlocks]);

  // Auto-scroll to bottom as new blocks reveal
  useEffect(() => {
    const el = scrollRef.current;
    if (!el) return;
    requestAnimationFrame(() => {
      el.scrollTo({ top: el.scrollHeight, behavior: playing ? "smooth" : "auto" });
    });
  }, [reveal, playing]);

  return (
    <PlayableTerminalChrome
      theme={theme}
      title={title}
      onPlay={play}
      onReset={reset}
      isPlaying={playing}
      progress={`${reveal}/${totalBlocks}`}
      scrollRef={scrollRef}
    >
      <NyxSession theme={theme} revealUpTo={reveal} />
    </PlayableTerminalChrome>
  );
};

// Chrome that keeps a scrollRef and renders the play button inline.
const PlayableTerminalChrome = ({
  theme, title, onPlay, onReset, isPlaying, progress, scrollRef, children,
}) => {
  return (
    <div
      style={{
        width: "100%",
        height: "100%",
        background: theme.chromeBg,
        borderRadius: 12,
        overflow: "hidden",
        boxShadow:
          "0 1px 0 rgba(255,255,255,0.06) inset, 0 30px 60px -20px rgba(0,0,0,0.55), 0 12px 30px -10px rgba(0,0,0,0.4)",
        border: `1px solid ${theme.chromeBorder}`,
        display: "flex",
        flexDirection: "column",
        fontFamily: "'Fira Mono', 'JetBrains Mono', 'DejaVu Sans Mono', ui-monospace, monospace",
        color: theme.fg,
      }}
    >
      {/* Titlebar */}
      <div
        style={{
          height: 40,
          background: theme.chromeBg,
          borderBottom: `1px solid ${theme.chromeBorder}`,
          display: "grid",
          gridTemplateColumns: "auto 1fr auto",
          alignItems: "center",
          padding: "0 12px",
          gap: 8,
          flex: "0 0 auto",
          userSelect: "none",
        }}
      >
        <div style={{ display: "flex", gap: 4, alignItems: "center" }}>
          <ChromeIcon><svg viewBox="0 0 16 16" width="13" height="13"><rect x="2" y="3.5" width="12" height="1.4" rx="0.5" fill="currentColor"/><rect x="2" y="7.3" width="12" height="1.4" rx="0.5" fill="currentColor"/><rect x="2" y="11.1" width="12" height="1.4" rx="0.5" fill="currentColor"/></svg></ChromeIcon>
          <ChromeIcon><svg viewBox="0 0 16 16" width="13" height="13"><path d="M8 3v10M3 8h10" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round"/></svg></ChromeIcon>
          <span style={{
            color: theme.muted,
            fontFamily: "'Inter', system-ui, sans-serif",
            fontSize: 11,
            marginLeft: 6,
            padding: "2px 8px",
            background: theme.accent + "15",
            border: `1px solid ${theme.accent}44`,
            borderRadius: 4,
            letterSpacing: 0.5,
          }}>
            <span style={{ color: theme.accent, fontWeight: 600, marginRight: 4 }}>{theme.name}</span>
            <span style={{ fontFamily: "'Fira Mono', monospace", color: theme.muted }}>{progress}</span>
          </span>
        </div>

        <div style={{
          textAlign: "center",
          fontFamily: "'Inter', 'Cantarell', system-ui, sans-serif",
          fontSize: 12.5,
          fontWeight: 600,
          color: theme.chromeFg,
          letterSpacing: 0.1,
          overflow: "hidden",
          textOverflow: "ellipsis",
          whiteSpace: "nowrap",
          padding: "0 12px",
        }}>{title}</div>

        <div style={{ display: "flex", gap: 6, alignItems: "center" }}>
          <button
            onClick={isPlaying ? onReset : onPlay}
            style={{
              background: isPlaying ? "rgba(255,255,255,0.10)" : theme.accent + "20",
              border: `1px solid ${theme.accent}66`,
              color: isPlaying ? theme.fg : theme.accent,
              fontFamily: "'Inter', system-ui, sans-serif",
              fontSize: 11,
              fontWeight: 600,
              padding: "4px 12px",
              borderRadius: 5,
              cursor: "pointer",
              display: "flex",
              alignItems: "center",
              gap: 6,
              letterSpacing: 0.3,
            }}
            title={isPlaying ? "Reiniciar" : "Reproduzir sessão completa"}
          >
            {isPlaying ? (
              <>
                <svg viewBox="0 0 12 12" width="9" height="9"><path d="M2 2l8 8M10 2l-8 8" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round"/></svg>
                Reiniciar
              </>
            ) : (
              <>
                <svg viewBox="0 0 12 12" width="9" height="9"><path d="M3 2l7 4-7 4z" fill="currentColor"/></svg>
                Reproduzir
              </>
            )}
          </button>
          <ChromeIcon><svg viewBox="0 0 16 16" width="13" height="13"><path d="M4 4l8 8M12 4l-8 8" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round"/></svg></ChromeIcon>
        </div>
      </div>

      {/* Content */}
      <div
        ref={scrollRef}
        className="nyx-scroll"
        style={{
          flex: "1 1 auto",
          background: theme.bg,
          overflow: "auto",
          padding: "22px 30px 32px",
          fontSize: 13.5,
          lineHeight: 1.55,
          color: theme.fg,
        }}
      >
        {children}
      </div>
    </div>
  );
};

const ChromeIcon = ({ children }) => (
  <div style={{
    width: 26, height: 26, borderRadius: 6,
    display: "grid", placeItems: "center",
    color: "#b8b8c8",
  }}>{children}</div>
);

// ─── App ─────────────────────────────────────────────────────────────
const App = () => {
  const T = window.NYX_THEMES;
  return (
    <DesignCanvas>
      <DCSection
        id="audit"
        title="Auditoria"
        subtitle="O diagnóstico antes do redesenho"
      >
        <DCArtboard id="problems" label="15 problemas encontrados" width={1500} height={920}>
          <AuditArtboard />
        </DCArtboard>
      </DCSection>

      <DCSection
        id="variations"
        title="Variações"
        subtitle="Quatro caminhos de redesenho · clique ▶ Reproduzir em cada terminal · ou abra em foco"
      >
        <DCArtboard id="editorial" label="A · Editorial — tipográfico, sem caixas" width={1400} height={920}>
          <PlayableTerminal theme={T.editorial} title={editorialTitle()} />
        </DCArtboard>
        <DCArtboard id="arcano" label="B · Arcano — violeta noturno, glow ritualístico" width={1400} height={920}>
          <PlayableTerminal theme={T.arcano} title={arcanoTitle()} />
        </DCArtboard>
        <DCArtboard id="brutalist" label="C · Brutalist Mono — denso, sem decoração" width={1400} height={920}>
          <PlayableTerminal theme={T.brutalist} title={brutalistTitle()} />
        </DCArtboard>
        <DCArtboard id="hybrid" label="D · Hybrid — recomendada (Dracula refinado)" width={1400} height={920}>
          <PlayableTerminal theme={T.hybrid} title={hybridTitle()} />
        </DCArtboard>
      </DCSection>
    </DesignCanvas>
  );
};

const baseTitle = "andrefarias@nitro-5: ~/Desenvolvimento/Nyx-Code";
const editorialTitle = () => baseTitle;
const arcanoTitle = () => baseTitle;
const brutalistTitle = () => baseTitle;
const hybridTitle = () => baseTitle;

ReactDOM.createRoot(document.getElementById("root")).render(<App />);
