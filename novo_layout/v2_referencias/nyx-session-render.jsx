// nyx-session-render.jsx — Shared renderer that consumes a theme + the
// structured session and produces JSX. The same data is drawn 4 ways.
//
// Public component: <NyxSession theme={THEME} revealUpTo={n} />

const cx = (...xs) => xs.filter(Boolean).join(" ");

// ─── Helpers ──────────────────────────────────────────────────────────
const Pill = ({ tone, label, theme }) => {
  const colors = {
    ok:    { bg: theme.ok + "22",  bd: theme.ok + "55",  fg: theme.ok },
    err:   { bg: theme.err + "22", bd: theme.err + "55", fg: theme.err },
    info:  { bg: theme.accent + "22", bd: theme.accent + "55", fg: theme.accent },
    muted: { bg: "transparent", bd: theme.faint, fg: theme.muted },
  }[tone] || { bg: "transparent", bd: theme.faint, fg: theme.muted };
  return (
    <span style={{
      display: "inline-flex",
      alignItems: "center",
      gap: 6,
      padding: "1px 8px",
      borderRadius: 4,
      border: `1px solid ${colors.bd}`,
      background: colors.bg,
      color: colors.fg,
      fontSize: 11,
      letterSpacing: 0.2,
      fontWeight: 500,
    }}>{label}</span>
  );
};

const Dot = ({ color, size = 7 }) => (
  <span style={{
    display: "inline-block",
    width: size, height: size,
    borderRadius: "50%",
    background: color,
    boxShadow: `0 0 8px ${color}`,
  }}/>
);

const Hr = ({ theme, label }) => {
  const style = theme.divider;
  if (style === "ornament") {
    return (
      <div style={{
        display: "flex", alignItems: "center", gap: 12,
        color: theme.faint, margin: "20px 0", fontSize: 11,
      }}>
        <span style={{ flex: 1, height: 1, background: `linear-gradient(to right, transparent, ${theme.faint})` }}/>
        <span style={{ letterSpacing: 2 }}>✦ {label || ""} ✦</span>
        <span style={{ flex: 1, height: 1, background: `linear-gradient(to left, transparent, ${theme.faint})` }}/>
      </div>
    );
  }
  if (style === "rule") {
    return (
      <div style={{
        margin: "18px 0 10px",
        borderTop: `1px solid ${theme.faint}`,
        color: theme.muted,
        fontSize: 11,
        letterSpacing: 1.5,
        padding: "6px 0 0",
        textTransform: "uppercase",
      }}>{label || ""}</div>
    );
  }
  return (
    <div style={{
      margin: "16px 0",
      display: "flex", alignItems: "center", gap: 10,
      color: theme.faint, fontSize: 11,
    }}>
      {label && <span style={{ color: theme.muted, letterSpacing: 0.5 }}>{label}</span>}
      <span style={{ flex: 1, height: 1, background: theme.faint, opacity: 0.5 }}/>
    </div>
  );
};

const cap = (t, mode) => mode === "upper" ? String(t).toUpperCase() : t;

// ─── BLOCK: boot ─────────────────────────────────────────────────────
const BootBlock = ({ data, theme }) => {
  const ascii = theme.bannerStyle === "ascii-glow"
    ? `╭─────────────────────────────╮\n│   SANTUÁRIO · NYX-CODE     │\n╰─────────────────────────────╯`
    : null;
  return (
    <div style={{ marginBottom: 28 }}>
      {ascii ? (
        <pre style={{
          color: theme.accent2,
          textShadow: `0 0 10px ${theme.accent2}88`,
          margin: "0 0 14px",
          fontSize: 13,
          lineHeight: 1.2,
        }}>{ascii}</pre>
      ) : (
        <div style={{
          fontSize: theme.headingCase === "upper" ? 12 : 16,
          fontWeight: 700,
          letterSpacing: theme.headingCase === "upper" ? 2.5 : 0.2,
          color: theme.fg,
          marginBottom: 4,
        }}>{cap(data.title, theme.headingCase)}</div>
      )}
      {theme.bannerStyle !== "ascii-glow" && (
        <div style={{
          height: 1, width: 88, background: theme.accent, marginBottom: 14, opacity: 0.6,
        }}/>
      )}

      <div style={{
        display: "grid",
        gridTemplateColumns: "auto 1fr",
        columnGap: 18,
        rowGap: 3,
        fontSize: 13,
        marginBottom: 14,
      }}>
        {data.rows.map((r) => (
          <React.Fragment key={r.k}>
            <span style={{ color: theme.muted }}>{r.k}</span>
            <span style={{ color: theme.fg }}>{r.v}</span>
          </React.Fragment>
        ))}
      </div>

      <div style={{ display: "flex", flexDirection: "column", gap: 3 }}>
        {data.checks.map((c, i) => (
          <div key={i} style={{ display: "flex", alignItems: "center", gap: 10, fontSize: 13 }}>
            <span style={{
              display: "inline-grid", placeItems: "center",
              width: 16, height: 16, borderRadius: 4,
              background: c.ok ? theme.ok + "22" : theme.err + "22",
              color: c.ok ? theme.ok : theme.err,
              fontSize: 11, fontWeight: 700,
            }}>{c.ok ? "✓" : "✕"}</span>
            <span style={{ color: theme.fg }}>{c.label}</span>
            <span style={{ color: theme.muted }}>· {c.detail}</span>
          </div>
        ))}
      </div>

      <div style={{
        marginTop: 14,
        color: theme.accent2,
        fontSize: 13,
        fontWeight: 500,
      }}>{data.ready}</div>
    </div>
  );
};

// ─── BLOCK: wizard ────────────────────────────────────────────────────
const WizardBlock = ({ data, theme }) => (
  <div style={{ marginBottom: 28 }}>
    <Hr theme={theme} label={cap("Configuração inicial", theme.headingCase)} />

    {/* Welcome */}
    <div style={{ marginBottom: 18 }}>
      <div style={{
        fontSize: 18,
        fontWeight: 600,
        color: theme.fg,
        letterSpacing: theme.headingCase === "upper" ? 2 : 0,
      }}>{cap(data.welcome.title, theme.headingCase)}</div>
      <div style={{ color: theme.muted, fontSize: 13, marginTop: 2 }}>{data.welcome.sub}</div>
    </div>

    {/* Steps */}
    <div style={{ display: "flex", flexDirection: "column", gap: 16 }}>
      {data.steps.map((s) => <WizardStep key={s.n} s={s} theme={theme}/>)}
    </div>

    {/* Summary */}
    <div style={{
      marginTop: 22,
      border: `1px solid ${theme.faint}`,
      borderLeft: `3px solid ${theme.accent}`,
      borderRadius: theme.id === "brutalist" ? 0 : 8,
      padding: "14px 16px",
      background: "rgba(255,255,255,0.02)",
    }}>
      <div style={{
        fontSize: 13,
        fontWeight: 600,
        color: theme.fg,
        marginBottom: 8,
        letterSpacing: theme.headingCase === "upper" ? 1.5 : 0,
      }}>{cap(data.summary.title, theme.headingCase)}</div>
      <div style={{
        display: "grid",
        gridTemplateColumns: "auto 1fr",
        columnGap: 18,
        rowGap: 3,
        fontSize: 13,
      }}>
        {data.summary.rows.map((r) => (
          <React.Fragment key={r.k}>
            <span style={{ color: theme.muted }}>{r.k}</span>
            <span style={{ color: theme.fg }}>{r.v}</span>
          </React.Fragment>
        ))}
      </div>
      <div style={{ color: theme.muted, fontSize: 12, marginTop: 10 }}>
        {data.summary.foot}  <span style={{
          color: theme.accent2,
          padding: "1px 6px",
          border: `1px solid ${theme.accent2}55`,
          borderRadius: 3,
          marginLeft: 4,
        }}>↵ Enter</span>
      </div>
    </div>
  </div>
);

const WizardStep = ({ s, theme }) => {
  return (
    <div>
      <div style={{ display: "flex", alignItems: "baseline", gap: 10, marginBottom: 6 }}>
        <span style={{
          color: theme.muted,
          fontSize: 11,
          fontVariantNumeric: "tabular-nums",
          letterSpacing: 0.5,
        }}>{String(s.n).padStart(2, "0")}/{String(s.total).padStart(2, "0")}</span>
        <span style={{
          color: theme.fg,
          fontSize: 14,
          fontWeight: 600,
          letterSpacing: theme.headingCase === "upper" ? 1.5 : 0,
        }}>{cap(s.question, theme.headingCase)}</span>
        <span style={{ color: theme.faint, fontSize: 12 }}>· {s.hint}</span>
      </div>
      <div style={{
        display: "grid",
        gridTemplateColumns: "repeat(auto-fill, minmax(220px, 1fr))",
        gap: 6,
      }}>
        {s.options.map((o) => {
          const chosen = o.id === s.chosen;
          return (
            <div key={o.id} style={{
              border: `1px solid ${chosen ? theme.accent : theme.faint + "66"}`,
              background: chosen ? theme.accent + "1a" : "transparent",
              borderRadius: theme.id === "brutalist" ? 0 : 6,
              padding: "6px 10px",
              fontSize: 12.5,
              display: "flex",
              flexDirection: "column",
              gap: 1,
            }}>
              <div style={{ display: "flex", alignItems: "center", gap: 6 }}>
                <span style={{
                  width: 9, height: 9, borderRadius: "50%",
                  border: `1.5px solid ${chosen ? theme.accent : theme.muted}`,
                  background: chosen ? theme.accent : "transparent",
                  display: "inline-block",
                }}/>
                <span style={{ color: theme.fg, fontWeight: chosen ? 600 : 400 }}>{o.label}</span>
              </div>
              <span style={{ color: theme.muted, fontSize: 11.5, marginLeft: 15 }}>{o.desc}</span>
            </div>
          );
        })}
      </div>
    </div>
  );
};

// ─── BLOCK: header (session header) ──────────────────────────────────
const HeaderBlock = ({ data, theme }) => (
  <div style={{ marginBottom: 24 }}>
    <Hr theme={theme} label={cap("Sessão", theme.headingCase)} />
    <div style={{ display: "flex", alignItems: "baseline", gap: 12, marginBottom: 8 }}>
      <span style={{
        fontSize: 18, fontWeight: 700,
        color: theme.accent,
        letterSpacing: theme.headingCase === "upper" ? 2.5 : 0,
      }}>{cap(data.name, theme.headingCase)}</span>
      <span style={{ color: theme.muted, fontSize: 13 }}>{data.version}</span>
      <span style={{ marginLeft: "auto", display: "flex", alignItems: "center", gap: 6, color: theme.ok, fontSize: 12 }}>
        <Dot color={theme.ok} /> {data.tag}
      </span>
    </div>
    <div style={{
      display: "grid",
      gridTemplateColumns: "max-content 1fr",
      columnGap: 18,
      rowGap: 4,
      fontSize: 13,
    }}>
      {data.groups.map((g) => (
        <React.Fragment key={g.label}>
          <span style={{ color: theme.muted }}>{g.label}</span>
          <span style={{ color: theme.fg }}>{g.v}</span>
        </React.Fragment>
      ))}
    </div>
    <div style={{ color: theme.faint, fontSize: 12, marginTop: 10 }}>{data.hint}</div>
  </div>
);

// ─── BLOCK: user bubble ──────────────────────────────────────────────
const UserBubble = ({ user, theme }) => {
  const k = theme.userBubble.kind;
  const color = theme.userBubble.color;
  const label = (theme.headingCase === "upper") ? `[${String(user.name).toUpperCase()}]` : user.name;

  if (k === "bracket-label") {
    return (
      <div style={{ margin: "8px 0 12px" }}>
        <div style={{
          color, fontSize: 11,
          letterSpacing: 2.5, fontWeight: 700, marginBottom: 4,
        }}>{label}</div>
        <div style={{ color: theme.fg, paddingLeft: 0, fontSize: 13.5 }}>{user.text}</div>
      </div>
    );
  }

  // soft-box / ornament-box / subtle-line all share the same shape — differ in border/radius
  const isOrnament = k === "ornament-box";
  const isLine = k === "subtle-line";
  return (
    <div style={{ margin: "10px 0 14px", display: "flex", gap: 12 }}>
      <div style={{
        width: 3,
        borderRadius: 2,
        background: isLine ? color : "transparent",
        flex: "0 0 auto",
      }}/>
      <div style={{
        flex: 1,
        border: isLine ? "none" : `1px solid ${color}55`,
        background: isLine ? "transparent" : color + "10",
        borderRadius: theme.id === "brutalist" ? 0 : (isOrnament ? 4 : 8),
        padding: isLine ? "0 0 0 0" : "8px 12px",
      }}>
        <div style={{
          fontSize: 11, color,
          letterSpacing: 0.5, textTransform: "lowercase",
          fontWeight: 600, marginBottom: 2,
        }}>{theme.userPrefix} {label}</div>
        <div style={{ color: theme.fg, fontSize: 13.5 }}>{user.text}</div>
      </div>
    </div>
  );
};

// ─── BLOCK: nyx response ─────────────────────────────────────────────
const NyxResponse = ({ nyx, theme }) => {
  const isBracket = theme.nyxBubble.kind === "bracket-label";
  const isSideRule = theme.nyxBubble.kind === "side-rule";
  const isGlow = theme.nyxBubble.kind === "glow-bar";
  const accent = theme.nyxBubble.color;
  const label = theme.headingCase === "upper" ? "[NYX]" : "Nyx";

  return (
    <div style={{ margin: "0 0 18px", display: "flex", gap: 12 }}>
      {(isSideRule || isGlow) && (
        <div style={{
          width: 3,
          borderRadius: 2,
          background: accent,
          flex: "0 0 auto",
          boxShadow: isGlow ? `0 0 12px ${accent}aa` : "none",
        }}/>
      )}
      <div style={{ flex: 1 }}>
        {/* Header line */}
        <div style={{
          display: "flex", alignItems: "center", gap: 10, marginBottom: 6,
        }}>
          <span style={{
            color: accent,
            fontSize: isBracket ? 11 : 13,
            fontWeight: 700,
            letterSpacing: isBracket ? 2.5 : 0.2,
          }}>{isBracket ? label : `${theme.nyxPrefix} ${label}`}</span>
          {nyx.meta && (
            <>
              <span style={{ color: theme.faint }}>·</span>
              <span style={{ color: theme.muted, fontSize: 11 }}>{nyx.meta.time}</span>
              <span style={{ color: theme.faint }}>·</span>
              <span style={{ color: theme.muted, fontSize: 11 }}>{nyx.meta.tokens} tokens</span>
            </>
          )}
        </div>

        {/* Thinking (if any) */}
        {nyx.thinking && <ThinkingBlock t={nyx.thinking} theme={theme}/>}

        {/* Tools (if any) */}
        {nyx.tools && nyx.tools.length > 0 && (
          <div style={{ display: "flex", flexDirection: "column", gap: 6, margin: "6px 0 10px" }}>
            {nyx.tools.map((tool, i) => <ToolCall key={i} tool={tool} theme={theme}/>)}
          </div>
        )}

        {/* Body */}
        <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
          {nyx.body.map((b, i) => <BodyChunk key={i} b={b} theme={theme}/>)}
        </div>
      </div>
    </div>
  );
};

// ─── thinking block ──────────────────────────────────────────────────
const ThinkingBlock = ({ t, theme, open: openInit }) => {
  const [open, setOpen] = React.useState(openInit ?? false);

  if (theme.thinkingStyle === "bracket-row") {
    return (
      <div style={{
        fontSize: 11.5,
        color: theme.muted,
        letterSpacing: 1.5,
        marginBottom: 8,
        fontFamily: "inherit",
      }}>
        [PENSANDO · {t.duration}]
        <span style={{ color: theme.faint, marginLeft: 6, textTransform: "none", letterSpacing: 0 }}>
          tab para expandir
        </span>
      </div>
    );
  }

  if (theme.thinkingStyle === "ornament-row") {
    return (
      <div
        onClick={() => setOpen(!open)}
        style={{
          fontSize: 12,
          color: theme.muted,
          marginBottom: 8,
          cursor: "pointer",
          display: "flex", alignItems: "center", gap: 8,
        }}>
        <span style={{ color: theme.accent }}>✦</span>
        <span>pensando · {t.duration}</span>
        <span style={{ color: theme.faint, fontStyle: "italic", flex: 1, marginLeft: 8 }}>
          {t.preview}
        </span>
        <span style={{ color: theme.faint, fontSize: 10 }}>{open ? "tab ▼" : "tab ▶"}</span>
      </div>
    );
  }

  // default: row / collapsible — same UX, different chrome
  const isCollapsible = theme.thinkingStyle === "collapsible";
  return (
    <div style={{ marginBottom: 8 }}>
      <div
        onClick={() => setOpen(!open)}
        style={{
          fontSize: 12,
          color: theme.muted,
          display: "flex", alignItems: "center", gap: 8,
          cursor: "pointer",
          padding: isCollapsible ? "4px 10px" : "0",
          borderRadius: 4,
          background: isCollapsible ? "rgba(255,255,255,0.03)" : "transparent",
          border: isCollapsible ? `1px dashed ${theme.faint}` : "none",
        }}>
        <span style={{ color: theme.muted, fontSize: 10 }}>{open ? "▼" : "▶"}</span>
        <span style={{ color: theme.accent }}>pensando</span>
        <span>· {t.duration}</span>
        <span style={{ color: theme.faint, fontStyle: "italic", flex: 1, marginLeft: 4, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
          {!open && t.preview}
        </span>
        <span style={{ color: theme.faint, fontSize: 10 }}>tab</span>
      </div>
      {open && (
        <div style={{
          padding: "8px 14px 8px 22px",
          color: theme.muted,
          fontSize: 12.5,
          lineHeight: 1.6,
          borderLeft: `1px solid ${theme.faint}`,
          marginLeft: 6,
          marginTop: 6,
          fontStyle: "italic",
        }}>
          {t.full.map((line, i) => <div key={i}>{line}</div>)}
        </div>
      )}
    </div>
  );
};

// ─── tool call ───────────────────────────────────────────────────────
const ToolCall = ({ tool, theme }) => {
  const ok = tool.status === "ok";
  const statusColor = ok ? theme.ok : theme.err;
  const statusLabel = ok ? "ok" : "erro";

  if (theme.toolStyle === "inline") {
    return (
      <div style={{
        display: "flex", alignItems: "center", gap: 10,
        fontSize: 12.5,
        color: theme.muted,
      }}>
        <span style={{ color: theme.faint }}>≡</span>
        <span style={{ color: theme.fg, fontWeight: 600 }}>{tool.name}</span>
        <span style={{ color: theme.muted }}>{tool.args}</span>
        <span style={{ color: theme.faint }}>·</span>
        <span style={{ color: theme.muted }}>{tool.time}</span>
        <span style={{ color: theme.faint }}>·</span>
        <span style={{ color: statusColor, fontWeight: 500 }}>{statusLabel}</span>
        {!ok && <span style={{ color: theme.muted, fontStyle: "italic", marginLeft: 4 }}>— {tool.detail}</span>}
      </div>
    );
  }

  if (theme.toolStyle === "table-row") {
    return (
      <div style={{
        display: "grid",
        gridTemplateColumns: "auto 1fr auto auto",
        gap: 14,
        fontSize: 12.5,
        padding: "4px 0",
        borderTop: `1px solid ${theme.faint}55`,
        fontFamily: "inherit",
      }}>
        <span style={{ color: theme.muted, letterSpacing: 1.5, textTransform: "uppercase" }}>[TOOL]</span>
        <span style={{ color: theme.fg }}>
          <span style={{ fontWeight: 700 }}>{tool.name}</span>
          <span style={{ color: theme.muted }}> {tool.args}</span>
        </span>
        <span style={{ color: theme.muted, fontVariantNumeric: "tabular-nums" }}>{tool.time}</span>
        <span style={{
          color: statusColor,
          textTransform: "uppercase",
          letterSpacing: 1.5,
          fontWeight: 600,
        }}>{ok ? "OK" : "ERROR"}</span>
        {!ok && (
          <span style={{ gridColumn: "2 / -1", color: theme.muted, fontSize: 11.5, marginLeft: 0 }}>↳ {tool.detail}</span>
        )}
      </div>
    );
  }

  if (theme.toolStyle === "ornament-chip") {
    return (
      <div style={{
        display: "inline-flex",
        alignItems: "center",
        gap: 8,
        padding: "4px 12px",
        borderRadius: 999,
        border: `1px solid ${statusColor}66`,
        background: statusColor + "12",
        fontSize: 12,
        alignSelf: "flex-start",
        boxShadow: ok ? `0 0 12px ${statusColor}33` : "none",
      }}>
        <Dot color={statusColor} size={6}/>
        <span style={{ color: theme.fg, fontWeight: 600 }}>{tool.name}</span>
        <span style={{ color: theme.muted }}>{tool.args}</span>
        <span style={{ color: theme.faint }}>·</span>
        <span style={{ color: theme.muted }}>{tool.time}</span>
        {!ok && <span style={{ color: theme.err, fontStyle: "italic" }}>— {tool.detail}</span>}
      </div>
    );
  }

  // default: chip (hybrid)
  return (
    <div style={{
      display: "flex",
      alignItems: "center",
      gap: 10,
      padding: "6px 12px",
      borderRadius: 6,
      background: "rgba(255,255,255,0.03)",
      border: `1px solid ${theme.faint}55`,
      fontSize: 12.5,
      borderLeft: `2px solid ${statusColor}`,
    }}>
      <Dot color={statusColor} size={6}/>
      <span style={{ color: theme.fg, fontWeight: 600 }}>{tool.name}</span>
      <span style={{ color: theme.muted, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
        {tool.args}
      </span>
      <span style={{ flex: 1 }}/>
      <span style={{ color: theme.muted, fontVariantNumeric: "tabular-nums" }}>{tool.time}</span>
      <span style={{ color: statusColor, fontWeight: 500 }}>{statusLabel}</span>
      {!ok && (
        <div style={{ flexBasis: "100%", color: theme.muted, fontSize: 11.5, marginTop: 2 }}>
          ↳ {tool.detail}
        </div>
      )}
    </div>
  );
};

// ─── body chunks ─────────────────────────────────────────────────────
const BodyChunk = ({ b, theme }) => {
  if (b.kind === "p") return <div style={{ color: theme.fg, fontSize: 13.5 }}>{b.text}</div>;

  if (b.kind === "todo") {
    return (
      <div style={{
        marginTop: 4,
        border: `1px solid ${theme.faint}55`,
        borderRadius: theme.id === "brutalist" ? 0 : 6,
        padding: "10px 14px",
        background: "rgba(255,255,255,0.02)",
      }}>
        <div style={{
          fontSize: 12, color: theme.muted, marginBottom: 6,
          letterSpacing: theme.headingCase === "upper" ? 1.5 : 0.2,
          textTransform: theme.headingCase === "upper" ? "uppercase" : "none",
        }}>{b.title}</div>
        <div style={{ display: "flex", flexDirection: "column", gap: 3 }}>
          {b.items.map((it, i) => (
            <div key={i} style={{ display: "flex", alignItems: "center", gap: 10, fontSize: 13 }}>
              <span style={{
                display: "inline-grid", placeItems: "center",
                width: 16, height: 16, borderRadius: theme.id === "brutalist" ? 0 : 3,
                border: `1.5px solid ${it.done ? theme.ok : theme.faint}`,
                background: it.done ? theme.ok + "22" : "transparent",
                color: theme.ok, fontSize: 10, fontWeight: 700,
              }}>{it.done ? "✓" : ""}</span>
              <span style={{
                color: it.done ? theme.fg : theme.muted,
                textDecoration: "none",
              }}>{it.text}</span>
            </div>
          ))}
        </div>
      </div>
    );
  }

  if (b.kind === "actions") {
    return (
      <div style={{ marginTop: 4 }}>
        <div style={{ color: theme.muted, fontSize: 12.5, marginBottom: 6 }}>{b.intro}</div>
        <div style={{ display: "flex", flexDirection: "column", gap: 4 }}>
          {b.items.map((a, i) => (
            <div key={i} style={{ display: "flex", gap: 12, fontSize: 13, alignItems: "baseline" }}>
              <span style={{
                color: theme.accent,
                fontWeight: 700,
                width: 16,
              }}>({a.key})</span>
              <span style={{ color: theme.fg, flex: 1 }}>{a.text}</span>
              <span style={{
                color: theme.accent2,
                fontSize: 12,
                padding: "0 6px",
                border: `1px solid ${theme.accent2}55`,
                borderRadius: 3,
              }}>{a.cmd}</span>
            </div>
          ))}
        </div>
      </div>
    );
  }
  return null;
};

// ─── slash command (/help) ───────────────────────────────────────────
const SlashBlock = ({ data, theme }) => (
  <div style={{ margin: "0 0 22px" }}>
    <div style={{
      display: "flex", alignItems: "center", gap: 8, marginBottom: 10,
    }}>
      <span style={{ color: theme.muted }}>{theme.userPrefix}</span>
      <span style={{
        color: theme.accent,
        fontSize: 13,
        fontWeight: 700,
        fontFamily: "inherit",
      }}>{data.cmd}</span>
    </div>
    <div style={{
      display: "grid",
      gridTemplateColumns: "repeat(3, 1fr)",
      gap: 18,
    }}>
      {data.groups.map((g) => (
        <div key={g.title}>
          <div style={{
            fontSize: 11, color: theme.muted,
            letterSpacing: theme.headingCase === "upper" ? 2 : 1.5,
            marginBottom: 6,
            textTransform: "uppercase",
          }}>{g.title}</div>
          <div style={{ display: "flex", flexDirection: "column", gap: 3 }}>
            {g.items.map((it, i) => (
              <div key={i} style={{ fontSize: 12.5 }}>
                <span style={{ color: theme.accent, fontWeight: 600 }}>{it.c}</span>
                <div style={{ color: theme.muted, fontSize: 11.5, marginTop: 1 }}>{it.d}</div>
              </div>
            ))}
          </div>
        </div>
      ))}
    </div>
  </div>
);

// ─── quit / encerramento ─────────────────────────────────────────────
const QuitBlock = ({ data, theme }) => (
  <div style={{ marginTop: 8 }}>
    <Hr theme={theme} label={cap("Encerramento", theme.headingCase)} />
    <div style={{
      fontSize: 16, fontWeight: 600, color: theme.fg,
      letterSpacing: theme.headingCase === "upper" ? 2 : 0,
    }}>{cap(data.title, theme.headingCase)}</div>
    <div style={{ color: theme.muted, fontSize: 12.5, marginBottom: 14 }}>{data.sub}</div>

    <div style={{
      display: "grid",
      gridTemplateColumns: "repeat(3, 1fr)",
      gap: 14,
      marginBottom: 14,
    }}>
      {data.stats.map((s) => (
        <div key={s.k} style={{
          padding: "8px 12px",
          background: "rgba(255,255,255,0.03)",
          border: `1px solid ${theme.faint}55`,
          borderRadius: theme.id === "brutalist" ? 0 : 6,
        }}>
          <div style={{
            color: theme.muted, fontSize: 10.5,
            letterSpacing: theme.headingCase === "upper" ? 1.8 : 0.5,
            textTransform: "uppercase",
            marginBottom: 2,
          }}>{s.k}</div>
          <div style={{
            color: theme.fg,
            fontSize: 14,
            fontVariantNumeric: "tabular-nums",
            fontWeight: 500,
          }}>{s.v}</div>
        </div>
      ))}
    </div>

    <div style={{ display: "flex", flexDirection: "column", gap: 2 }}>
      {data.shutdown.map((line, i) => (
        <div key={i} style={{ color: theme.muted, fontSize: 12.5 }}>
          <span style={{ color: theme.faint, marginRight: 8 }}>›</span>{line}
        </div>
      ))}
    </div>
  </div>
);

// ─── BLOCK: exchange (user → nyx) ────────────────────────────────────
const ExchangeBlock = ({ ex, theme }) => (
  <>
    <UserBubble user={ex.user} theme={theme}/>
    <NyxResponse nyx={ex.nyx} theme={theme}/>
  </>
);

// ─── Master renderer ─────────────────────────────────────────────────
const NyxSession = ({ theme, revealUpTo = 999, session }) => {
  const blocks = session || window.NYX_SESSION;
  return (
    <div style={{ display: "flex", flexDirection: "column" }}>
      {blocks.slice(0, revealUpTo).map((blk, i) => {
        const wrap = (el) => (
          <div key={i} style={{
            opacity: 0,
            animation: `nyxFadeIn 240ms ease-out ${Math.min(i, 4) * 30}ms forwards`,
          }}>{el}</div>
        );
        switch (blk.type) {
          case "boot":     return wrap(<BootBlock     data={blk} theme={theme}/>);
          case "wizard":   return wrap(<WizardBlock   data={blk} theme={theme}/>);
          case "header":   return wrap(<HeaderBlock   data={blk} theme={theme}/>);
          case "exchange": return wrap(<ExchangeBlock ex={blk}   theme={theme}/>);
          case "slash":    return wrap(<SlashBlock    data={blk} theme={theme}/>);
          case "quit":     return wrap(<QuitBlock     data={blk} theme={theme}/>);
          default: return null;
        }
      })}
    </div>
  );
};

Object.assign(window, { NyxSession });
