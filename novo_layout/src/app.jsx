// =============================================================================
// APP ROOT — orquestra tudo, gerencia tema global, monta tweaks panel
// =============================================================================

const { useState: useStateA } = React;

// ─── TWEAKS PANEL ─────────────────────────────────────────────────────────────
function TweaksPanel({ aesthetic, setAesthetic, entity, setEntity }) {
  const aesthetics = ["arcano", "cyber", "brutalist", "mecha", "editorial"];
  const entities = ["nyx", "eris", "juno", "lars", "luna", "mars", "somn"];
  return (
    <div className="tweaks">
      <div className="t-title">
        <span>tweaks</span>
        <span style={{
          fontFamily: "'JetBrains Mono', monospace",
          fontSize: 10,
          color: "#9D4EDD",
          letterSpacing: "0.2em",
          opacity: 0.7,
        }}>LIVE</span>
      </div>
      <div className="t-label">estético</div>
      <div className="t-row">
        {aesthetics.map(a => (
          <button
            key={a}
            className={`t-chip ${a === aesthetic ? "active" : ""}`}
            onClick={() => setAesthetic(a)}
          >{a}</button>
        ))}
      </div>
      <div className="t-label">entidade · cor de accent</div>
      <div className="t-row">
        {entities.map(e => {
          const ent = window.NYX_ENTITIES[e];
          return (
            <button
              key={e}
              className={`t-chip ${e === entity ? "active" : ""}`}
              onClick={() => setEntity(e)}
              style={{
                borderLeft: `3px solid ${ent.accent}`,
              }}
            >{e}</button>
          );
        })}
      </div>
      <div style={{
        marginTop: 14,
        paddingTop: 12,
        borderTop: "1px solid rgba(157, 78, 221, 0.15)",
        fontSize: 10,
        color: "#7a6e90",
        lineHeight: 1.5,
      }}>
        os 35 terminais nesta página obedecem em tempo real.
      </div>
    </div>
  );
}

// ─── TOP NAV ──────────────────────────────────────────────────────────────────
function TopNav() {
  return (
    <nav className="topnav">
      <div className="logo">
        <em>Nyx</em> Code
        <span style={{
          marginLeft: 12,
          fontFamily: "'JetBrains Mono', monospace",
          fontSize: 10,
          letterSpacing: "0.2em",
          color: "#7a6e90",
        }}>· redesign doc</span>
      </div>
      <div className="menu">
        <a href="#manifesto">manifesto</a>
        <a href="#aesthetics">estéticos</a>
        <a href="#system">sistema</a>
        <a href="#screens">telas</a>
        <a href="#workflow">workflow</a>
        <a href="#features">fichas</a>
        <a href="#novel">novel</a>
        <a href="#roadmap">roadmap</a>
      </div>
    </nav>
  );
}

// ─── APP ──────────────────────────────────────────────────────────────────────
function App() {
  const [aesthetic, setAesthetic] = useStateA("arcano");
  const [entity, setEntity] = useStateA("nyx");

  return (
    <div className="page">
      <TopNav />

      <span id="hero"></span>
      <HeroSection aesthetic={aesthetic} entity={entity} />

      <span id="manifesto"></span>
      <ManifestoSection />

      <span id="aesthetics"></span>
      <AestheticsGallerySection entity={entity} />

      {window.SystemSection && (
        <>
          <span id="system"></span>
          <window.SystemSection aesthetic={aesthetic} entity={entity} />
        </>
      )}

      {window.ScreensSection && (
        <>
          <span id="screens"></span>
          <window.ScreensSection aesthetic={aesthetic} entity={entity} setAesthetic={setAesthetic} setEntity={setEntity} />
        </>
      )}

      {window.WorkflowSection && (
        <>
          <span id="workflow"></span>
          <window.WorkflowSection aesthetic={aesthetic} entity={entity} />
        </>
      )}

      {window.FeaturesSection && (
        <>
          <span id="features"></span>
          <window.FeaturesSection />
        </>
      )}

      {window.NovelSection && (
        <>
          <span id="novel"></span>
          <window.NovelSection aesthetic={aesthetic} entity={entity} />
        </>
      )}

      {window.RoadmapSection && (
        <>
          <span id="roadmap"></span>
          <window.RoadmapSection />
        </>
      )}

      <TweaksPanel
        aesthetic={aesthetic}
        setAesthetic={setAesthetic}
        entity={entity}
        setEntity={setEntity}
      />

      {/* Closing colophon */}
      <section className="section bg-tone-2" style={{ padding: "120px 40px 80px" }}>
        <div className="section-inner" style={{ textAlign: "center", maxWidth: 720, margin: "0 auto" }}>
          <p style={{
            fontFamily: "'Cormorant Garamond', serif",
            fontStyle: "italic",
            fontSize: 32,
            lineHeight: 1.3,
            color: "#c4b8d4",
            textWrap: "balance",
            margin: "0 auto 24px",
            maxWidth: "100%",
          }}>
            "Perfeição não é quando não há mais nada para adicionar,
            mas quando não há mais nada para remover."
          </p>
          <p className="kicker">— Antoine de Saint-Exupéry, no rodapé do README.md</p>
          <div style={{
            margin: "60px auto 0",
            width: 1,
            height: 60,
            background: "linear-gradient(180deg, rgba(157,78,221,0.4), transparent)",
          }} />
        </div>
      </section>
    </div>
  );
}

const root = ReactDOM.createRoot(document.getElementById("root"));
root.render(<App />);
