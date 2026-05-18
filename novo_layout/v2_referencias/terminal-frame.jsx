// terminal-frame.jsx — GNOME Terminal window chrome (Wayland/Adwaita style).
// Wraps content in a believable terminal window with title bar, hamburger,
// close button, and an optional scrollback area with play/replay controls.

const TerminalFrame = ({
  title = "André@nitro-5: ~/Desenvolvimento/Nyx-Code",
  bg = "#282a36",         // Dracula by default
  fg = "#f8f8f2",
  chromeBg = "#2d2b3a",   // titlebar
  chromeFg = "#d8d8e2",
  chromeBorder = "#1a1822",
  width = 1300,
  height = 820,
  children,
  // Optional rolling play
  onPlay,
  onReset,
  isPlaying,
  playLabel = "Reproduzir sessão",
}) => {
  const scrollRef = React.useRef(null);

  // Expose scroll API
  React.useImperativeHandle(
    null, // no ref but kept for clarity
    () => ({ scrollTo: (y) => scrollRef.current?.scrollTo({ top: y, behavior: "smooth" }) }),
    []
  );

  return (
    <div
      style={{
        width,
        height,
        background: chromeBg,
        borderRadius: 12,
        overflow: "hidden",
        boxShadow:
          "0 1px 0 rgba(255,255,255,0.06) inset, 0 30px 60px -20px rgba(0,0,0,0.55), 0 12px 30px -10px rgba(0,0,0,0.4)",
        border: `1px solid ${chromeBorder}`,
        display: "flex",
        flexDirection: "column",
        fontFamily: "'Fira Mono', 'JetBrains Mono', 'DejaVu Sans Mono', ui-monospace, monospace",
        color: fg,
      }}
    >
      {/* Titlebar — GNOME 42 Adwaita style: title centered, hamburger left, close right */}
      <div
        style={{
          height: 40,
          background: chromeBg,
          borderBottom: `1px solid ${chromeBorder}`,
          display: "grid",
          gridTemplateColumns: "auto 1fr auto",
          alignItems: "center",
          padding: "0 12px",
          gap: 8,
          flex: "0 0 auto",
          userSelect: "none",
        }}
      >
        {/* Left: hamburger + new tab */}
        <div style={{ display: "flex", gap: 8, alignItems: "center" }}>
          <TitlebarIcon>
            <svg viewBox="0 0 16 16" width="14" height="14"><rect x="2" y="3" width="12" height="1.6" rx="0.6" fill="currentColor"/><rect x="2" y="7.2" width="12" height="1.6" rx="0.6" fill="currentColor"/><rect x="2" y="11.4" width="12" height="1.6" rx="0.6" fill="currentColor"/></svg>
          </TitlebarIcon>
          <TitlebarIcon>
            <svg viewBox="0 0 16 16" width="14" height="14"><path d="M8 3v10M3 8h10" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round"/></svg>
          </TitlebarIcon>
        </div>

        {/* Center: title */}
        <div style={{
          textAlign: "center",
          fontFamily: "'Inter', 'Cantarell', system-ui, sans-serif",
          fontSize: 13,
          fontWeight: 600,
          color: chromeFg,
          letterSpacing: 0.1,
          overflow: "hidden",
          textOverflow: "ellipsis",
          whiteSpace: "nowrap",
        }}>{title}</div>

        {/* Right: play + close */}
        <div style={{ display: "flex", gap: 6, alignItems: "center" }}>
          {onPlay && (
            <button
              onClick={isPlaying ? onReset : onPlay}
              style={{
                background: isPlaying ? "rgba(255,255,255,0.08)" : "rgba(255,255,255,0.04)",
                border: `1px solid ${chromeBorder}`,
                color: chromeFg,
                fontFamily: "'Inter', system-ui, sans-serif",
                fontSize: 11,
                fontWeight: 500,
                padding: "4px 10px",
                borderRadius: 6,
                cursor: "pointer",
                display: "flex",
                alignItems: "center",
                gap: 6,
              }}
              title={isPlaying ? "Reiniciar" : playLabel}
            >
              {isPlaying ? (
                <>
                  <svg viewBox="0 0 12 12" width="10" height="10"><path d="M2 2l8 8M10 2l-8 8" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round"/></svg>
                  Reiniciar
                </>
              ) : (
                <>
                  <svg viewBox="0 0 12 12" width="10" height="10"><path d="M3 2l7 4-7 4z" fill="currentColor"/></svg>
                  Reproduzir
                </>
              )}
            </button>
          )}
          <TitlebarIcon>
            <svg viewBox="0 0 16 16" width="14" height="14"><path d="M4 4l8 8M12 4l-8 8" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round"/></svg>
          </TitlebarIcon>
        </div>
      </div>

      {/* Terminal content area */}
      <div
        ref={scrollRef}
        className="nyx-scroll"
        style={{
          flex: "1 1 auto",
          background: bg,
          overflow: "auto",
          padding: "20px 28px 28px 28px",
          fontSize: 13.5,
          lineHeight: 1.55,
          color: fg,
        }}
      >
        {children}
      </div>
    </div>
  );
};

const TitlebarIcon = ({ children }) => (
  <div
    style={{
      width: 28,
      height: 28,
      borderRadius: 6,
      display: "grid",
      placeItems: "center",
      color: "#b8b8c8",
      cursor: "default",
    }}
  >{children}</div>
);

Object.assign(window, { TerminalFrame });
