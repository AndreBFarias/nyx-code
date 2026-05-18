// =============================================================================
// SECTIONS — SISTEMA (Entities · Glyphs · Typography)
// =============================================================================

// ─── ENTITIES (7 personalidades de accent) ────────────────────────────────────
function EntitiesSection({ aesthetic, entity: currentEntity }) {
  const entityList = ["nyx", "eris", "juno", "lars", "luna", "mars", "somn"];
  return (
    <section className="section bg-tone-2" data-screen-label="04 As Sete Entidades">
      <div className="section-inner">
        <div className="section-head">
          <div className="ttl">
            <div className="h-eyebrow">
              <span>III.</span>
              <span>O panteão</span>
            </div>
            <h2 className="h-sub">
              Sete entidades.<br />
              Sete <em style={{ fontStyle: "italic", color: "#9D4EDD" }}>vozes</em>.
            </h2>
            <div className="spacer-md" />
            <p className="lede">
              Cada entidade injeta um <strong style={{ color: "#f0e8d8" }}>accent + glow</strong> próprios
              em qualquer estético. A estrutura visual permanece — a personalidade muda.
              É a maneira do dev escolher com quem trabalhar hoje.
            </p>
          </div>
          <div className="meta">
            <p className="kicker">/theme entity &lt;nome&gt;</p>
          </div>
        </div>

        <div className="grid-4" style={{ gap: 18 }}>
          {entityList.map((eid) => {
            const e = window.NYX_ENTITIES[eid];
            const isActive = eid === currentEntity;
            return (
              <div
                key={eid}
                className="card"
                style={{
                  borderColor: isActive ? e.accent : "rgba(157, 78, 221, 0.12)",
                  background: isActive ? `${e.accent}10` : "rgba(157, 78, 221, 0.04)",
                  position: "relative",
                  overflow: "hidden",
                }}
              >
                {/* halo de fundo */}
                <div style={{
                  position: "absolute",
                  top: -60,
                  right: -60,
                  width: 160,
                  height: 160,
                  borderRadius: "50%",
                  background: `radial-gradient(circle, ${e.glow}, transparent 70%)`,
                  pointerEvents: "none",
                }} />
                <div style={{ position: "relative", zIndex: 1 }}>
                  <div style={{
                    display: "flex",
                    alignItems: "baseline",
                    justifyContent: "space-between",
                    marginBottom: 8,
                  }}>
                    <h3 style={{
                      fontFamily: "'Cormorant Garamond', serif",
                      fontSize: 32,
                      fontWeight: 400,
                      color: e.accent,
                      letterSpacing: "0.02em",
                    }}>{e.name}</h3>
                    <span className="kicker" style={{ fontSize: 9 }}>/theme {eid}</span>
                  </div>
                  <p style={{
                    fontFamily: "'Cormorant Garamond', serif",
                    fontSize: 16,
                    fontStyle: "italic",
                    color: "#c4b8d4",
                    lineHeight: 1.4,
                    margin: 0,
                    marginBottom: 16,
                    minHeight: 44,
                  }}>{e.description}</p>
                  {/* color swatches */}
                  <div style={{ display: "flex", gap: 6, marginBottom: 14 }}>
                    <div style={{
                      flex: 2,
                      height: 32,
                      background: e.accent,
                      borderRadius: 3,
                      position: "relative",
                    }}>
                      <span style={{
                        position: "absolute",
                        bottom: -16,
                        left: 0,
                        fontFamily: "'JetBrains Mono', monospace",
                        fontSize: 9,
                        color: "#7a6e90",
                        textTransform: "uppercase",
                      }}>{e.accent}</span>
                    </div>
                    <div style={{
                      flex: 1,
                      height: 32,
                      background: e.accent_lo,
                      borderRadius: 3,
                    }} />
                    <div style={{
                      flex: 1,
                      height: 32,
                      background: e.ember,
                      borderRadius: 3,
                    }} />
                  </div>
                  <div className="spacer-sm" />
                  <p style={{
                    fontFamily: "'JetBrains Mono', monospace",
                    fontSize: 11,
                    color: "#9c8fb0",
                    lineHeight: 1.55,
                    fontStyle: "italic",
                  }}>
                    {e.mood}
                  </p>
                </div>
              </div>
            );
          })}
          {/* "blank slot" para futuras entidades */}
          <div className="card" style={{
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            background: "transparent",
            borderColor: "rgba(157, 78, 221, 0.05)",
            borderStyle: "dashed",
            minHeight: 200,
          }}>
            <p style={{
              fontFamily: "'JetBrains Mono', monospace",
              fontSize: 10,
              color: "#5a4f70",
              letterSpacing: "0.15em",
              textTransform: "uppercase",
              textAlign: "center",
            }}>
              vaga para<br />8ª entidade<br /><br />
              <span style={{ color: "#9D4EDD", fontStyle: "italic", fontFamily: "'Cormorant Garamond', serif", fontSize: 14, letterSpacing: 0, textTransform: "none" }}>
                "ainda a invocar"
              </span>
            </p>
          </div>
        </div>
      </div>
    </section>
  );
}

// ─── GLYPHS / VOCABULÁRIO VISUAL ──────────────────────────────────────────────
function GlyphsSection() {
  const glyphCats = [
    {
      name: "box drawing — cantos",
      sub: "U+2500..257F — arredondados (default) e duplos (mecha)",
      items: [
        ["╭", "tl_round", "U+256D"],
        ["╮", "tr_round", "U+256E"],
        ["╰", "bl_round", "U+2570"],
        ["╯", "br_round", "U+256F"],
        ["┏", "tl_heavy", "U+250F"],
        ["┓", "tr_heavy", "U+2513"],
        ["┗", "bl_heavy", "U+2517"],
        ["┛", "br_heavy", "U+251B"],
      ],
    },
    {
      name: "box drawing — linhas",
      sub: "leves, pesadas, duplas, tracejadas",
      items: [
        ["─", "h_light", "U+2500"],
        ["━", "h_heavy", "U+2501"],
        ["═", "h_double", "U+2550"],
        ["┄", "h_dash", "U+2504"],
        ["│", "v_light", "U+2502"],
        ["┃", "v_heavy", "U+2503"],
        ["║", "v_double", "U+2551"],
        ["┊", "v_dash", "U+250A"],
      ],
    },
    {
      name: "braille — partículas e spinner",
      sub: "U+2800..28FF — não-emoji, técnico, animável",
      items: [
        ["⠋", "spin_1", "U+280B"],
        ["⠙", "spin_2", "U+2819"],
        ["⠹", "spin_3", "U+2839"],
        ["⠸", "spin_4", "U+2838"],
        ["⠼", "spin_5", "U+283C"],
        ["⠴", "spin_6", "U+2834"],
        ["⠦", "spin_7", "U+2826"],
        ["⢿", "particle", "U+28BF"],
      ],
    },
    {
      name: "barras e medidores",
      sub: "para /status, /doctor, footer de ctx",
      items: [
        ["█", "meter_full", "U+2588"],
        ["▓", "meter_3of4", "U+2593"],
        ["▒", "meter_2of4", "U+2592"],
        ["░", "meter_1of4", "U+2591"],
        ["▁", "spark_1", "U+2581"],
        ["▃", "spark_3", "U+2583"],
        ["▅", "spark_5", "U+2585"],
        ["▇", "spark_7", "U+2587"],
      ],
    },
    {
      name: "bullets e setas",
      sub: "indicação de fluxo, status, escolha",
      items: [
        ["·", "note", "U+00B7"],
        ["", "tool", "U+25CF"],
        ["", "tool_idle", "U+25CB"],
        ["", "arrow_play", "U+25B8"],
        ["→", "arrow_r", "U+2192"],
        ["↳", "result", "U+21B3"],
        ["§", "section", "U+00A7"],
        ["¶", "para", "U+00B6"],
      ],
    },
  ];

  return (
    <section className="section bg-tone-3" data-screen-label="05 Vocabulário Visual">
      <div className="section-inner">
        <div className="section-head">
          <div className="ttl">
            <div className="h-eyebrow">
              <span>IV.</span>
              <span>Vocabulário visual</span>
            </div>
            <h2 className="h-sub">
              Box Drawing<br />
              <em style={{ fontStyle: "italic", color: "#9D4EDD" }}>+ Braille</em>.<br />
              Nada além.
            </h2>
            <div className="spacer-md" />
            <p className="lede">
              ADR-004 proíbe emoji (faixas U+1F300..1F9FF e U+2600..27BF).
              O que sobra é mais rico do que parece: Box Drawing (U+2500..257F),
              Braille Patterns (U+2800..28FF), Block Elements (U+2580..259F)
              e ASCII seguro. Combinados, dão para construir uma linguagem
              visual completa.
            </p>
          </div>
          <div className="meta">
            <p className="kicker">themes/design_tokens.py · BOX_CHARS, BULLETS, SPINNER_FRAMES</p>
          </div>
        </div>

        {glyphCats.map((cat) => (
          <div key={cat.name} style={{ marginBottom: 60 }}>
            <div style={{
              display: "flex",
              justifyContent: "space-between",
              alignItems: "baseline",
              marginBottom: 20,
              paddingBottom: 12,
              borderBottom: "1px solid rgba(157, 78, 221, 0.15)",
            }}>
              <h3 style={{
                fontFamily: "'Cormorant Garamond', serif",
                fontSize: 26,
                fontWeight: 400,
                color: "#f0e8d8",
              }}>{cat.name}</h3>
              <span className="kicker" style={{ color: "#9c8fb0" }}>{cat.sub}</span>
            </div>
            <div style={{
              display: "grid",
              gridTemplateColumns: "repeat(8, 1fr)",
              gap: 10,
            }}>
              {cat.items.map(([ch, name, code]) => (
                <div key={name} className="glyph-cell">
                  <div className="glyph-big">{ch}</div>
                  <div className="glyph-name">{name}</div>
                  <div className="glyph-code">{code}</div>
                </div>
              ))}
            </div>
          </div>
        ))}

        <div className="spacer-md" />

        <div style={{
          padding: 32,
          background: "rgba(157, 78, 221, 0.05)",
          borderLeft: "2px solid #9D4EDD",
          borderRadius: "0 6px 6px 0",
        }}>
          <p className="kicker" style={{ marginBottom: 12 }}>fallback ASCII (terminal sem UTF-8)</p>
          <pre style={{
            fontFamily: "'JetBrains Mono', monospace",
            fontSize: 13,
            color: "#c4b8d4",
            lineHeight: 1.6,
            margin: 0,
            whiteSpace: "pre-wrap",
          }}>
{`  +-- nyx · 100% offline -----+
  |  qwen3:4b  ·  34 tools     |
  |  /help  Ctrl+D para sair   |
  +----------------------------+

  > pensando...  | / - \\
`}
          </pre>
          <p style={{ fontSize: 13, color: "#9c8fb0", marginTop: 12, fontFamily: "'Cormorant Garamond', serif", fontStyle: "italic" }}>
            Detectado via LC_ALL + LANG não-UTF-8. Braille vira{" "}
            <code style={{ color: "#ffb454", fontFamily: "JetBrains Mono", fontSize: 12 }}>|/-\</code>,
            cantos viram <code style={{ color: "#ffb454", fontFamily: "JetBrains Mono", fontSize: 12 }}>+ - |</code>.
            A interface degrada mas continua legível.
          </p>
        </div>
      </div>
    </section>
  );
}

// ─── TYPOGRAPHY ───────────────────────────────────────────────────────────────
function TypographySection() {
  const typeShowcase = [
    {
      aes: "arcano",
      mono: "JetBrains Mono",
      display: "Cormorant Garamond",
      sample_display: "Vivo no terminal.",
      sample_mono: "def invoke(self, sigil: str) -> Spell:",
      note: "Serif elegante para narrativa, mono limpo para código. Itálicos ressonantes.",
    },
    {
      aes: "cyber",
      mono: "JetBrains Mono · 500",
      display: "Space Grotesk",
      sample_display: "ACESSO CONCEDIDO",
      sample_mono: "auth.bypass = TRUE;  // root@cyberspace",
      note: "Geometricamente afiada. Track maior. Pesos médios.",
    },
    {
      aes: "brutalist",
      mono: "iA Writer Quattro",
      display: "Spectral",
      sample_display: "Theorem 4.1.",
      sample_mono: "function tex_break(line: String) {",
      note: "Texto serif clássico, mono austero. Sem efeitos. Como um manuscrito.",
    },
    {
      aes: "mecha",
      mono: "JetBrains Mono · 500",
      display: "JetBrains Mono · Bold",
      sample_display: "TARGET ACQUIRED",
      sample_mono: "[SYS] gauge_a = 0.847  STATUS: NOMINAL",
      note: "Tudo mono. Maiúsculas pra labels HUD. Track 0.04em pra dar gravidade.",
    },
    {
      aes: "editorial",
      mono: "Fira Code",
      display: "Source Serif 4",
      sample_display: "Capítulo III — O parser.",
      sample_mono: "// Listing 3.4 — dispatch by level",
      note: "Serif para narrativa, mono para listings. Marginalia em itálico.",
    },
  ];
  return (
    <section className="section bg-tone-1" data-screen-label="06 Tipografia">
      <div className="section-inner">
        <div className="section-head">
          <div className="ttl">
            <div className="h-eyebrow">
              <span>V.</span>
              <span>Tipografia</span>
            </div>
            <h2 className="h-sub">
              A maior parte<br />
              da interface<br />
              é <em style={{ fontStyle: "italic", color: "#9D4EDD" }}>letra</em>.
            </h2>
          </div>
          <div className="meta">
            <p className="kicker">5 pares · cada estético tem display + mono</p>
          </div>
        </div>

        <div className="stack" style={{ gap: 32 }}>
          {typeShowcase.map((t, i) => (
            <div
              key={t.aes}
              style={{
                display: "grid",
                gridTemplateColumns: "180px 1fr 1fr 280px",
                gap: 32,
                alignItems: "center",
                padding: "40px 0",
                borderBottom: i < typeShowcase.length - 1 ? "1px solid rgba(157,78,221,0.1)" : "none",
              }}
            >
              <div>
                <h3 style={{
                  fontFamily: "'Cormorant Garamond', serif",
                  fontSize: 36,
                  fontWeight: 400,
                  color: "#f0e8d8",
                  lineHeight: 1,
                }}>
                  {window.NYX_AESTHETICS[t.aes].name}
                </h3>
                <p className="kicker" style={{ marginTop: 4 }}>0{i+1} / {typeShowcase.length}</p>
              </div>

              <div>
                <p className="kicker" style={{ marginBottom: 8 }}>display · {t.display}</p>
                <p style={{
                  fontFamily:
                    t.aes === "arcano" ? "'Cormorant Garamond', serif" :
                    t.aes === "cyber" ? "'Space Grotesk', sans-serif" :
                    t.aes === "brutalist" ? "'Spectral', serif" :
                    t.aes === "mecha" ? "'JetBrains Mono', monospace" :
                    "'Source Serif 4', serif",
                  fontSize: 38,
                  fontWeight: t.aes === "cyber" ? 600 : t.aes === "mecha" ? 700 : 400,
                  fontStyle: t.aes === "arcano" ? "italic" : "normal",
                  color: "#f0e8d8",
                  lineHeight: 1.1,
                  letterSpacing: t.aes === "mecha" ? "0.05em" : "normal",
                  textTransform: t.aes === "mecha" || t.aes === "cyber" ? "uppercase" : "none",
                }}>{t.sample_display}</p>
              </div>

              <div>
                <p className="kicker" style={{ marginBottom: 8 }}>mono · {t.mono}</p>
                <p style={{
                  fontFamily: "'JetBrains Mono', monospace",
                  fontSize: 14,
                  color: "#c4b8d4",
                  background: "rgba(0,0,0,0.3)",
                  padding: "12px 14px",
                  borderRadius: 4,
                  fontFeatureSettings: "'ss01', 'cv11'",
                  fontWeight: t.aes === "cyber" || t.aes === "mecha" ? 500 : 400,
                  letterSpacing: t.aes === "mecha" ? "0.04em" : "0.01em",
                }}>{t.sample_mono}</p>
              </div>

              <div>
                <p style={{
                  fontFamily: "'Cormorant Garamond', serif",
                  fontStyle: "italic",
                  fontSize: 16,
                  color: "#9c8fb0",
                  lineHeight: 1.5,
                  margin: 0,
                }}>{t.note}</p>
              </div>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}

// ─── SISTEMA ROOT (Entities + Glyphs + Typography) ────────────────────────────
function SystemSection({ aesthetic, entity }) {
  return (
    <>
      <EntitiesSection aesthetic={aesthetic} entity={entity} />
      <GlyphsSection />
      <TypographySection />
    </>
  );
}

Object.assign(window, { EntitiesSection, GlyphsSection, TypographySection, SystemSection });
