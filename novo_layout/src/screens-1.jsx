// =============================================================================
// SCREENS PART 1 — Boot, Loop principal, Tool cards
// Cada screen retorna o conteúdo do <Terminal>; o caller envolve.
// =============================================================================

// ─── BOOT / BANNER ────────────────────────────────────────────────────────────
function BootScreen({ animated = false }) {
  const g = useGlyphs();
  const theme = useTheme();
  const [step, setStep] = useState(animated ? 0 : 999);

  useEffect(() => {
    if (!animated) return;
    const steps = [350, 250, 200, 300, 250, 400, 350, 600, 800];
    let i = 0;
    const tick = () => {
      i++;
      setStep(i);
      if (i < steps.length) setTimeout(tick, steps[i]);
    };
    setTimeout(tick, steps[0]);
  }, [animated]);

  const show = (n) => step >= n;

  return (
    <>
      <Empty />
      {show(0) && (
        <Line
          content={[
            { t: "  ", c: "" },
            { t: g.tl + g.h, c: "accent" },
            { t: " Nyx · v0.4.2 ", c: "accent", b: true },
            { t: g.h.repeat(38), c: "accent", dim: true },
            { t: " 100% offline ", c: "ember" },
            { t: g.h + g.tr, c: "accent" },
          ]}
        />
      )}
      {show(1) && (
        <Line
          content={[
            { t: "  ", c: "" },
            { t: g.v, c: "accent" },
            { t: "                                                              ", c: "" },
            { t: g.v, c: "accent" },
          ]}
        />
      )}
      {show(2) && (
        <Line
          content={[
            { t: "  ", c: "" },
            { t: g.v, c: "accent" },
            { t: "   modelo    ", c: "ink-dim" },
            { t: "qwen3:4b           ", c: "ink", b: true },
            { t: "tools    ", c: "ink-dim" },
            { t: "34", c: "ink", b: true },
            { t: "                ", c: "" },
            { t: g.v, c: "accent" },
          ]}
        />
      )}
      {show(3) && (
        <Line
          content={[
            { t: "  ", c: "" },
            { t: g.v, c: "accent" },
            { t: "   projeto   ", c: "ink-dim" },
            { t: "nyx-code           ", c: "ink", b: true },
            { t: "visão    ", c: "ink-dim" },
            { t: "moondream ", c: "ink" },
            { t: "(fria)        ", c: "ink-muted" },
            { t: g.v, c: "accent" },
          ]}
        />
      )}
      {show(4) && (
        <Line
          content={[
            { t: "  ", c: "" },
            { t: g.v, c: "accent" },
            { t: "   rede      ", c: "ink-dim" },
            { t: ":11435 ", c: "ember" },
            { t: "ollama  ", c: "ink-dim" },
            { t: g.bullet, c: "accent" },
            { t: "  :11436 ", c: "ember" },
            { t: "proxy            ", c: "ink-dim" },
            { t: g.v, c: "accent" },
          ]}
        />
      )}
      {show(5) && (
        <Line
          content={[
            { t: "  ", c: "" },
            { t: g.v, c: "accent" },
            { t: "   memória   ", c: "ink-dim" },
            { t: "12 entradas        ", c: "ink", b: true },
            { t: "skills   ", c: "ink-dim" },
            { t: "47 ", c: "ink" },
            { t: "registradas       ", c: "ink-muted" },
            { t: g.v, c: "accent" },
          ]}
        />
      )}
      {show(6) && (
        <Line
          content={[
            { t: "  ", c: "" },
            { t: g.v, c: "accent" },
            { t: "                                                              ", c: "" },
            { t: g.v, c: "accent" },
          ]}
        />
      )}
      {show(7) && (
        <Line
          content={[
            { t: "  ", c: "" },
            { t: g.bl + g.h, c: "accent" },
            { t: " /help para comandos ", c: "ink-dim" },
            { t: g.bullet, c: "ink-muted" },
            { t: " Ctrl+D para sair ", c: "ink-dim" },
            { t: g.h.repeat(22), c: "accent", dim: true },
            { t: g.h + g.br, c: "accent" },
          ]}
        />
      )}
      {show(8) && (
        <>
          <Empty />
          <Line
            content={[
              { t: "  ", c: "" },
              { t: "Sou Nyx.", c: "accent", b: true },
              { t: " Codificadora silenciosa. Vivo no terminal.", c: "ink-dim" },
            ]}
          />
          <Line
            content={[
              { t: "  ", c: "" },
              { t: g.arrow + " ", c: "ember" },
              { t: "diga o que precisa.", c: "ink-dim" },
            ]}
          />
        </>
      )}
      <Empty />
    </>
  );
}

// ─── LOOP PRINCIPAL ──────────────────────────────────────────────────────────
function LoopScreen() {
  const g = useGlyphs();
  return (
    <>
      <Empty />
      {/* user input box */}
      <Line content={[{ t: "  ", c: "" }, { t: `${g.tl}${g.h} `, c: "accent" }, { t: "você ", c: "accent", b: true }, { t: g.h.repeat(56), c: "accent", dim: true }, { t: ` ${g.h}${g.tr}`, c: "accent" }]} />
      <Line content={[{ t: "  ", c: "" }, { t: g.v, c: "accent", dim: true }, { t: "  refatora ", c: "ink" }, { t: "agent/parser.py", c: "ember" }, { t: " — tirar os 7 fallbacks duplicados,    ", c: "ink" }, { t: g.v, c: "accent", dim: true }]} />
      <Line content={[{ t: "  ", c: "" }, { t: g.v, c: "accent", dim: true }, { t: "  unifica num só dispatcher. mantém os contratos.        ", c: "ink" }, { t: g.v, c: "accent", dim: true }]} />
      <Line content={[{ t: "  ", c: "" }, { t: `${g.bl}${g.h.repeat(64)}${g.br}`, c: "accent", dim: true }]} />
      <Empty />
      {/* assistant header */}
      <Line content={[{ t: "  ", c: "" }, { t: "Nyx", c: "accent", b: true }]} />
      <Line content={[{ t: "  ", c: "" }, { t: g.h.repeat(3), c: "accent" }]} />
      <Line content={[{ t: "  ", c: "" }, { t: "Vou ler o parser antes de propor. Os fallbacks parecem ", c: "ink" }]} />
      <Line content={[{ t: "  ", c: "" }, { t: "concêntricos — quero confirmar quais bate em qual nível.", c: "ink" }]} />
      <Empty />
      {/* tool call */}
      <Line content={[{ t: "  ", c: "" }, { t: `${g.tl}${g.h} `, c: "accent" }, { t: g.bullet + " ", c: "accent" }, { t: "read_file", c: "accent", b: true }, { t: g.h.repeat(38), c: "accent", dim: true }, { t: " ok · 12ms ", c: "success" }, { t: `${g.h}${g.tr}`, c: "accent" }]} />
      <Line content={[{ t: "  ", c: "" }, { t: g.v, c: "accent", dim: true }, { t: "  ", c: "" }, { t: "agent/parser.py", c: "ember" }, { t: "  ", c: "" }, { t: g.bullet, c: "muted" }, { t: " 620 linhas, 7 níveis de fallback detectados", c: "ink-dim" }]} />
      <Line content={[{ t: "  ", c: "" }, { t: `${g.bl}${g.h.repeat(64)}${g.br}`, c: "accent", dim: true }]} />
      <Empty />
      {/* spinner thinking */}
      <Line content={[{ t: "  ", c: "" }, <BrailleSpinner key="s" label="propondo refatoração" color="accent" />]} />
      <Empty />
    </>
  );
}

// ─── TOOL CARDS (variações) ───────────────────────────────────────────────────
function ToolCardsScreen() {
  const g = useGlyphs();
  return (
    <>
      <Empty />
      {/* card 1: read_file */}
      <Line content={[{ t: "  ", c: "" }, { t: `${g.tl}${g.h} `, c: "accent" }, { t: g.bullet + " ", c: "accent" }, { t: "read_file", c: "accent", b: true }, { t: "(agent/parser.py)", c: "ink-dim" }, { t: g.h.repeat(22), c: "accent", dim: true }, { t: " ok · 12ms ", c: "success" }, { t: `${g.h}${g.tr}`, c: "accent" }]} />
      <Line content={[{ t: "  ", c: "" }, { t: g.v, c: "accent", dim: true }, { t: "  620 linhas · 7 fallback nesteds detectados", c: "ink-dim" }]} />
      <Line content={[{ t: "  ", c: "" }, { t: `${g.bl}${g.h.repeat(64)}${g.br}`, c: "accent", dim: true }]} />
      <Empty />
      {/* card 2: run_command */}
      <Line content={[{ t: "  ", c: "" }, { t: `${g.tl}${g.h} `, c: "ember" }, { t: g.bullet + " ", c: "ember" }, { t: "run_command", c: "ember", b: true }, { t: "(pytest tests/parser/)", c: "ink-dim" }, { t: g.h.repeat(15), c: "ember", dim: true }, { t: " executando ", c: "ember" }, { t: `${g.h}${g.tr}`, c: "ember" }]} />
      <Line content={[{ t: "  ", c: "" }, { t: g.v, c: "ember", dim: true }, { t: "  ", c: "" }, <BrailleSpinner key="s" label="rodando · 4s" color="ember" />]} />
      <Line content={[{ t: "  ", c: "" }, { t: g.v, c: "ember", dim: true }, { t: "  ", c: "" }, { t: "tests/parser/test_dispatcher.py ", c: "ink-dim" }, { t: "...", c: "muted" }, { t: "  12 passed", c: "success" }]} />
      <Line content={[{ t: "  ", c: "" }, { t: g.v, c: "ember", dim: true }, { t: "  ", c: "" }, { t: "tests/parser/test_fallback.py  ", c: "ink-dim" }, { t: "...", c: "muted" }, { t: "   9 passed", c: "success" }]} />
      <Line content={[{ t: "  ", c: "" }, { t: g.v, c: "ember", dim: true }, { t: "  ", c: "" }, { t: "tests/parser/test_repetition.py", c: "ink-dim" }, { t: " ...", c: "muted" }]} />
      <Empty />
      {/* card 3: write_file with diff */}
      <Line content={[{ t: "  ", c: "" }, { t: `${g.tl}${g.h} `, c: "accent" }, { t: g.bullet + " ", c: "accent" }, { t: "edit_file", c: "accent", b: true }, { t: "(agent/parser.py)", c: "ink-dim" }, { t: g.h.repeat(22), c: "accent", dim: true }, { t: " ok · 8ms ", c: "success" }, { t: `${g.h}${g.tr}`, c: "accent" }]} />
      <Line content={[{ t: "  ", c: "" }, { t: g.v, c: "accent", dim: true }, { t: "  ", c: "" }, { t: "−147 ", c: "error" }, { t: g.bullet, c: "muted" }, { t: " +89 ", c: "success" }, { t: g.bullet, c: "muted" }, { t: " net −58 ", c: "ember" }, { t: g.bullet, c: "muted" }, { t: " 1 hunk em 3 escopos", c: "ink-dim" }]} />
      <Line content={[{ t: "  ", c: "" }, { t: g.v, c: "accent", dim: true }, { t: "  ", c: "" }, { t: "[ver diff] ", c: "info", dim: true }, { t: "Ctrl+D · ", c: "muted" }, { t: "[reverter] ", c: "info", dim: true }, { t: "Ctrl+Z · ", c: "muted" }, { t: "[teste] ", c: "info", dim: true }, { t: "Ctrl+T", c: "muted" }]} />
      <Line content={[{ t: "  ", c: "" }, { t: `${g.bl}${g.h.repeat(64)}${g.br}`, c: "accent", dim: true }]} />
      <Empty />
    </>
  );
}

// ─── DIFF VIEWER ─────────────────────────────────────────────────────────────
function DiffScreen() {
  const g = useGlyphs();
  return (
    <>
      <Empty />
      <Line content={[{ t: "  ", c: "" }, { t: `${g.tl}${g.h} `, c: "accent" }, { t: "diff ", c: "accent", b: true }, { t: g.bullet + " ", c: "muted" }, { t: "agent/parser.py", c: "ember" }, { t: g.h.repeat(22), c: "accent", dim: true }, { t: " hunk 1/1 · L142-198 ", c: "ink-dim" }, { t: `${g.h}${g.tr}`, c: "accent" }]} />
      <Line content={[{ t: "  ", c: "" }, { t: g.v, c: "accent", dim: true }, { t: "  ", c: "" }, { t: "@@ -142,28 +142,18 @@", c: "info", b: true }, { t: " ActionParser._dispatch", c: "muted" }]} />
      <Line content={[{ t: "  ", c: "" }, { t: g.v, c: "accent", dim: true }, { t: " 142", c: "muted" }, { t: " " , c: "" }, { t: "    if level == 1:", c: "ink-dim" }]} />
      <Line content={[{ t: "  ", c: "" }, { t: g.v, c: "accent", dim: true }, { t: " 143", c: "muted" }, { t: "-", c: "error", b: true }, { t: "        return self._parse_strict(payload)", c: "error" }]} />
      <Line content={[{ t: "  ", c: "" }, { t: g.v, c: "accent", dim: true }, { t: " 144", c: "muted" }, { t: "-", c: "error", b: true }, { t: "    elif level == 2:", c: "error" }]} />
      <Line content={[{ t: "  ", c: "" }, { t: g.v, c: "accent", dim: true }, { t: " 145", c: "muted" }, { t: "-", c: "error", b: true }, { t: "        return self._parse_fallback(payload)", c: "error" }]} />
      <Line content={[{ t: "  ", c: "" }, { t: g.v, c: "accent", dim: true }, { t: " 146", c: "muted" }, { t: "-", c: "error", b: true }, { t: "    elif level == 3:", c: "error" }]} />
      <Line content={[{ t: "  ", c: "" }, { t: g.v, c: "accent", dim: true }, { t: " 147", c: "muted" }, { t: "-", c: "error", b: true }, { t: "        return self._parse_lenient(payload)", c: "error" }]} />
      <Line content={[{ t: "  ", c: "" }, { t: g.v, c: "accent", dim: true }, { t: " ···", c: "muted" }, { t: " ", c: "" }, { t: "    (4 níveis omitidos · 18 linhas)", c: "muted" }]} />
      <Line content={[{ t: "  ", c: "" }, { t: g.v, c: "accent", dim: true }, { t: " 143", c: "muted" }, { t: "+", c: "success", b: true }, { t: "    parser = self._dispatch_table[level]", c: "success" }]} />
      <Line content={[{ t: "  ", c: "" }, { t: g.v, c: "accent", dim: true }, { t: " 144", c: "muted" }, { t: "+", c: "success", b: true }, { t: "    return parser(payload)", c: "success" }]} />
      <Line content={[{ t: "  ", c: "" }, { t: g.v, c: "accent", dim: true }, { t: " 145", c: "muted" }, { t: " ", c: "" }, { t: " ", c: "" }]} />
      <Line content={[{ t: "  ", c: "" }, { t: g.v, c: "accent", dim: true }, { t: " 146", c: "muted" }, { t: " ", c: "" }, { t: "@@ -180,12 +160,4 @@", c: "info", b: true }]} />
      <Line content={[{ t: "  ", c: "" }, { t: g.v, c: "accent", dim: true }, { t: "   ", c: "muted" }, { t: " ", c: "" }, { t: "    (cleanup de imports não usados)", c: "muted" }]} />
      <Line content={[{ t: "  ", c: "" }, { t: g.v, c: "accent", dim: true }, { t: "                                                            ", c: "" }]} />
      <Line content={[{ t: "  ", c: "" }, { t: `${g.bl}${g.h.repeat(2)} `, c: "accent", dim: true }, { t: "[a]ceitar ", c: "success" }, { t: g.bullet, c: "muted" }, { t: " [r]ejeitar ", c: "error" }, { t: g.bullet, c: "muted" }, { t: " [e]ditar à mão ", c: "ember" }, { t: g.bullet, c: "muted" }, { t: " [t]este ", c: "info" }, { t: g.h.repeat(8), c: "accent", dim: true }, { t: `${g.br}`, c: "accent", dim: true }]} />
      <Empty />
    </>
  );
}

Object.assign(window, { BootScreen, LoopScreen, ToolCardsScreen, DiffScreen });
