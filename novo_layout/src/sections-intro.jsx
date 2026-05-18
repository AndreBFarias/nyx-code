// =============================================================================
// SECTIONS — INTRO (Hero · Manifesto · Aesthetics Gallery)
// =============================================================================

const { useState: useState_i, useEffect: useEffect_i } = React;

// ─── HERO ─────────────────────────────────────────────────────────────────────
function HeroSection({ aesthetic, entity }) {
  return (
    <section className="section hero" data-screen-label="01 Hero">
      <div className="hero-grid">
        <div>
          <div className="h-eyebrow">
            <span>Nyx Code</span>
            <span style={{ opacity: 0.4 }}>·</span>
            <span>Redesenho do terminal</span>
          </div>

          <h1 className="h-display">
            Uma <em>presença</em><br />
            no terminal,<br />
            não um chatbot.
          </h1>

          <div className="spacer-md" />

          <p className="lede">
            Documento de design + protótipo navegável para o terminal do
            <strong style={{ color: "#f0e8d8" }}> Nyx Code</strong>.
            Cinco linguagens visuais. Sete entidades. Quinze telas. Um modelo
            local. Zero menção a IA.
          </p>

          <div className="spacer-md" />

          <div style={{ display: "flex", gap: 12, flexWrap: "wrap" }}>
            <span className="badge">100% offline</span>
            <span className="badge badge-ember">PT-BR · ADR-006</span>
            <span className="badge">zero emoji · ADR-004</span>
            <span className="badge">Box Drawing + Braille</span>
            <span className="badge">prompt-toolkit + Rich</span>
          </div>

          <div className="spacer-lg" />

          <div className="kicker">
            role o documento
            <span style={{ marginLeft: 16 }}>↓</span>
          </div>
        </div>

        <div>
          <ThemeProvider aesthetic={aesthetic} entity={entity}>
            <Terminal label="boot · ao vivo" height={420} scanlines={false}>
              <BootScreen animated={true} />
            </Terminal>
          </ThemeProvider>
          <div className="spacer-sm" />
          <p className="mono" style={{ color: "#7a6e90", fontSize: 11 }}>
            ↑ esse terminal está respeitando o tema selecionado no canto
            inferior direito. troque ele e veja o boot todo se redesenhar.
          </p>
        </div>
      </div>
    </section>
  );
}

// ─── MANIFESTO ────────────────────────────────────────────────────────────────
function ManifestoSection() {
  return (
    <section className="section bg-tone-2" data-screen-label="02 Manifesto">
      <div className="section-inner">
        <div className="section-head">
          <div className="ttl">
            <div className="h-eyebrow">
              <span>I.</span>
              <span>Manifesto</span>
            </div>
            <h2 className="h-sub">
              <em style={{ fontStyle: "italic", color: "#9D4EDD" }}>
                Código limpo não é arte.
              </em>{" "}
              É higiene.
            </h2>
          </div>
          <div className="meta">
            <p className="kicker">14 pontos · 1 minuto de leitura</p>
          </div>
        </div>

        <div className="grid-2 gap-xl">
          <div className="stack" style={{ gap: 32 }}>
            <div>
              <div className="kicker" style={{ marginBottom: 8 }}>01 · presença</div>
              <p>
                Nyx <strong style={{ color: "#f0e8d8" }}>não fala</strong> que é
                inteligência artificial. Nyx é. Vive no terminal. Não pede
                desculpa por isso. Os termos "modelo", "assistente" e
                "treinada" estão proibidos no copy. (ADR-005)
              </p>
            </div>
            <div>
              <div className="kicker" style={{ marginBottom: 8 }}>02 · silêncio</div>
              <p>
                Cada palavra mostrada custa atenção do dev. O default é não
                falar. Quando fala, fala curto. Frases sem floreio. Verbos no
                imperativo. Sem reticências automáticas.
              </p>
            </div>
            <div>
              <div className="kicker" style={{ marginBottom: 8 }}>03 · respiração</div>
              <p>
                Os accents respiram (opacity cycle 4s). O cursor pulsa. Os
                gauges sobem em easing. Nada se move sem motivo, mas nada está
                <strong style={{ color: "#f0e8d8" }}> morto</strong>.
              </p>
            </div>
            <div>
              <div className="kicker" style={{ marginBottom: 8 }}>04 · ritual</div>
              <p>
                Comandos destrutivos exigem traçar um sigilo. Não é fricção
                gratuita — é cerimônia. Você lembra que está pedindo algo
                irreversível.
              </p>
            </div>
            <div>
              <div className="kicker" style={{ marginBottom: 8 }}>05 · marginalia</div>
              <p>
                Anotações de Nyx vivem na margem direita, em itálico claro.
                Não interrompem a leitura. Você lê quando quer.
              </p>
            </div>
            <div>
              <div className="kicker" style={{ marginBottom: 8 }}>06 · trilha</div>
              <p>
                Cada arquivo tocado deixa um rastro Braille que apaga em 12s.
                Você vê para onde Nyx foi sem precisar pedir{" "}
                <code style={{ color: "#ffb454" }}>/files</code>.
              </p>
            </div>
            <div>
              <div className="kicker" style={{ marginBottom: 8 }}>07 · panteão</div>
              <p>
                Sete entidades, sete acentos. Eris, Juno, Lars, Luna, Mars,
                Somn, Nyx. Você escolhe com quem quer trabalhar — a
                personalidade da accent muda, o resto continua sendo Nyx Code.
              </p>
            </div>
          </div>

          <div className="stack" style={{ gap: 32 }}>
            <div>
              <div className="kicker" style={{ marginBottom: 8 }}>08 · cinco línguas</div>
              <p>
                Arcano (ritual), Cyberpunk (saturado), Brutalist (Knuth),
                Mecha (HUD), Editorial (livro). O dev escolhe a língua. A
                interface se traduz inteira — não só a paleta.
              </p>
            </div>
            <div>
              <div className="kicker" style={{ marginBottom: 8 }}>09 · zero glop</div>
              <p>
                Emojis estão proibidos por contrato (ADR-004). Sem , sem ,
                sem . Box Drawing (U+2500–257F), Braille (U+2800–28FF) e
                ASCII seguro. Mais tipografia que iconografia.
              </p>
            </div>
            <div>
              <div className="kicker" style={{ marginBottom: 8 }}>10 · fallback</div>
              <p>
                Terminal sem UTF-8? Os glifos viram ASCII puro
                (<code>+-+| | / \ |</code>). O spinner braille vira{" "}
                <code>|/-\</code>. A interface degrada graciosamente, nunca
                quebra.
              </p>
            </div>
            <div>
              <div className="kicker" style={{ marginBottom: 8 }}>11 · telemetria honesta</div>
              <p>
                ctx %, tokens, latência, VRAM — tudo no footer, sempre
                visível. Você não tem que adivinhar quando o contexto vai
                estourar.
              </p>
            </div>
            <div>
              <div className="kicker" style={{ marginBottom: 8 }}>12 · plano antes de ação</div>
              <p>
                Mudanças em mais de 1 arquivo abrem auto-plan. Você vê o que
                vai acontecer antes que aconteça. Pode refinar. Pode abortar.
              </p>
            </div>
            <div>
              <div className="kicker" style={{ marginBottom: 8 }}>13 · sessão recuperável</div>
              <p>
                Tudo persiste em <code>~/.nyx/sessions/</code>. Crash, kill,
                reboot — <code>/resume</code> traz exatamente de onde você
                parou, inclusive memórias e diff em curso.
              </p>
            </div>
            <div>
              <div className="kicker" style={{ marginBottom: 8 }}>14 · quote no fim</div>
              <p>
                Toda sessão fecha com uma frase. Antoine de Saint-Exupéry,
                Sartre, Louis Sullivan, Aristóteles — quem combinar. Pequena
                cerimônia de despedida. Não é IA fazendo charme. É hábito
                literário.
              </p>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}

// ─── AESTHETICS GALLERY (5 estéticos lado a lado) ────────────────────────────
function AestheticsGallerySection({ entity }) {
  const aesthetics = ["arcano", "cyber", "brutalist", "mecha", "editorial"];
  return (
    <section className="section bg-tone-1" data-screen-label="03 Os Cinco Estéticos">
      <div className="section-wide-inner">
        <div className="section-head">
          <div className="ttl">
            <div className="h-eyebrow">
              <span>II.</span>
              <span>Os cinco estéticos</span>
            </div>
            <h2 className="h-sub">
              Cinco línguas visuais.<br />
              Um único terminal.
            </h2>
            <div className="spacer-md" />
            <p className="lede">
              Mesma mensagem, cinco gramáticas. O dev escolhe pelo
              <code style={{ color: "#ffb454", fontFamily: "JetBrains Mono", fontSize: 14, padding: "0 6px" }}>/aesthetic</code>
              ou pelo <code style={{ color: "#ffb454", fontFamily: "JetBrains Mono", fontSize: 14, padding: "0 6px" }}>NYX_AESTHETIC</code>
              env. Nada além do tema muda.
            </p>
          </div>
          <div className="meta">
            <p className="kicker">role lateral · clique pra trocar entidade</p>
          </div>
        </div>

        <div className="grid-5" style={{ gap: 18 }}>
          {aesthetics.map((aes) => {
            const a = window.NYX_AESTHETICS[aes];
            return (
              <div key={aes} className="stack" style={{ gap: 12 }}>
                <div style={{ display: "flex", alignItems: "baseline", justifyContent: "space-between" }}>
                  <h3 style={{
                    fontFamily: "'Cormorant Garamond', serif",
                    fontSize: 22,
                    color: "#f0e8d8",
                    fontWeight: 400,
                  }}>
                    {a.name}
                  </h3>
                  <span className="kicker">{aes}</span>
                </div>
                <p style={{
                  fontFamily: "'Cormorant Garamond', serif",
                  fontStyle: "italic",
                  fontSize: 15,
                  color: "#9c8fb0",
                  margin: 0,
                  lineHeight: 1.35,
                  minHeight: 60,
                }}>
                  {a.tagline}
                </p>

                <ThemeProvider aesthetic={aes} entity={entity}>
                  <Terminal dense={true} height={280}>
                    <Empty />
                    <Line content={[
                      { t: "  ", c: "" },
                      { t: a.glyphs.tl + a.glyphs.h, c: "accent" },
                      { t: " Nyx ", c: "accent", b: true },
                      { t: a.glyphs.h.repeat(28), c: "accent", dim: true },
                      { t: a.glyphs.h + a.glyphs.tr, c: "accent" },
                    ]} />
                    <Line content={[
                      { t: "  ", c: "" },
                      { t: a.glyphs.v, c: "accent" },
                      { t: "  qwen3:4b  · 100% offline   ", c: "ink-dim" },
                      { t: a.glyphs.v, c: "accent" },
                    ]} />
                    <Line content={[
                      { t: "  ", c: "" },
                      { t: a.glyphs.bl + a.glyphs.h.repeat(34) + a.glyphs.br, c: "accent", dim: true },
                    ]} />
                    <Empty />
                    <Line content={[
                      { t: "  ", c: "" },
                      { t: a.glyphs.arrow + " ", c: "ember" },
                      { t: "refator parser.py", c: "ink" },
                    ]} />
                    <Empty />
                    <Line content={[
                      { t: "  ", c: "" },
                      { t: "Nyx ", c: "accent", b: true },
                      { t: a.glyphs.h.repeat(3), c: "accent" },
                    ]} />
                    <Line content={[
                      { t: "  ", c: "" },
                      <BrailleSpinner key="s" label="lendo arquivo" color="accent" />,
                    ]} />
                    <Empty />
                    <Line content={[
                      { t: "  ", c: "" },
                      { t: a.glyphs.tl + a.glyphs.h + " ", c: "accent" },
                      { t: a.glyphs.bullet + " ", c: "accent" },
                      { t: "read_file", c: "accent", b: true },
                      { t: a.glyphs.h.repeat(8), c: "accent", dim: true },
                      { t: " ok ", c: "success" },
                      { t: a.glyphs.h + a.glyphs.tr, c: "accent" },
                    ]} />
                    <Line content={[
                      { t: "  ", c: "" },
                      { t: a.glyphs.v, c: "accent", dim: true },
                      { t: "  parser.py · 620 ln", c: "ink-dim" },
                    ]} />
                  </Terminal>
                </ThemeProvider>

                <div style={{ display: "flex", gap: 4 }}>
                  {Object.entries(a.palette).slice(0, 4).filter(([k]) => ["bg", "accent", "ember", "ink"].includes(k)).map(([k, v]) => (
                    <div key={k} style={{
                      flex: 1,
                      height: 8,
                      background: v,
                      borderRadius: 2,
                      border: "1px solid rgba(255,255,255,0.05)",
                    }} title={k + " " + v} />
                  ))}
                </div>

                <p className="mono" style={{ fontSize: 10, color: "#7a6e90", lineHeight: 1.5 }}>
                  {a.description}
                </p>
                <p className="mono" style={{
                  fontSize: 10,
                  color: "#9D4EDD",
                  fontStyle: "italic",
                  fontFamily: "'Cormorant Garamond', serif",
                  fontSize: 14,
                }}>
                  "{a.metaphor}"
                </p>
              </div>
            );
          })}
        </div>
      </div>
    </section>
  );
}

Object.assign(window, { HeroSection, ManifestoSection, AestheticsGallerySection });
