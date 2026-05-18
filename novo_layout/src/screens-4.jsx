// =============================================================================
// SCREENS PART 4 — Telas inspiradas nas referências do dev (Claude Code-like).
// Neofetch boot, boas-vindas, sprint tracker, sessão de coding, multi-tab,
// bypass, cost telemetry, multi-agent paralelo.
// =============================================================================

// ─── 1. NEOFETCH BOOT — ASCII art + system info ───────────────────────────────
function NeofetchBootScreen() {
  const g = useGlyphs();
  // Arte ASCII própria de "NYX" usando Block Elements (U+2580..259F) e Braille.
  // Respeita ADR-004 (sem emoji).
  const art = [
    "                              ",
    "   ███▄    █  ▓██   ██▓  ▒██   ██▒",
    "   ██ ▀█   █   ▒██  ██▒  ▒▒ █ █ ▒░",
    "  ▓██  ▀█ ██▒   ▒██ ██░  ░░  █   ░",
    "  ▓██▒  ▐▌██▒    ░ ▐██▓░  ░ █ █ ▒ ",
    "  ▒██░   ▓██░    ░ ██▒▓░ ░░  █   ░",
    "  ░ ▒░   ▒ ▒    ██▒▒▒     ░     ░ ",
    "  ░ ░░   ░ ▒░ ▓██ ░▒░    ░     ░  ",
    "     ░   ░ ░  ▒ ▒ ░░          ░   ",
    "           ░  ░ ░                 ",
    "              ░ ░                 ",
    "                              ",
  ];
  return (
    <>
      <Empty />
      {/* layout em 2 colunas — ascii art à esquerda, info à direita */}
      {art.map((line, i) => {
        const info = [
          ["", ""],
          ["sistema",    ["Pop!_OS 22.04 LTS", "x86_64"]],
          ["kernel",     ["Linux 6.17.9-generic", ""]],
          ["tempo ativo", ["1h 43min", "desde 09:42"]],
          ["pacotes",    ["2 736 dpkg ", "· 8 snap"]],
          ["shell",      ["zsh 5.8.1", ""]],
          ["GPU",        ["RTX 3050 Mobile", "4 GB VRAM"]],
          ["VRAM",       ["3.7 / 4.0 GiB ", "uso 92%"]],
          ["memória",    ["9.8 / 14.8 GiB", "uso 66%"]],
          ["bateria",    ["100% ", "conectado"]],
          ["", ""],
          ["", ""],
        ];
        const [label, vals] = info[i];
        return (
          <Line
            key={i}
            content={[
              { t: " ", c: "" },
              { t: line.padEnd(38), c: i % 2 === 0 ? "accent" : "ember" },
              { t: label ? label.padEnd(14) : "              ", c: "ember", b: true },
              ...(Array.isArray(vals) && vals[0] ? [
                { t: vals[0], c: "ink", b: true },
                { t: " ", c: "" },
                { t: vals[1], c: "ink-dim" },
              ] : []),
            ]}
          />
        );
      })}
      <Line content={[
        { t: "                              ", c: "" },
        { t: "Nyx Code ", c: "accent", b: true },
        { t: "v0.4.2  ", c: "ink-dim" },
        { t: g.bullet, c: "muted" },
        { t: " ", c: "" },
        { t: "qwen3:4b ", c: "ember" },
        { t: "(32k ctx)", c: "ink-dim" },
      ]} />
      <Line content={[
        { t: "                              ", c: "" },
        { t: "100% offline ", c: "success" },
        { t: g.bullet, c: "muted" },
        { t: " ", c: "" },
        { t: "PT-BR ", c: "ink" },
        { t: g.bullet, c: "muted" },
        { t: " ", c: "" },
        { t: "~/dev/nyx-code", c: "ink-dim" },
      ]} />
      <Empty />
      {/* paleta visual no canto inferior */}
      <Line content={[
        { t: "                              ", c: "" },
        { t: "█", c: "accent" },
        { t: "█", c: "ember" },
        { t: "█", c: "success" },
        { t: "█", c: "warning" },
        { t: "█", c: "error" },
        { t: "█", c: "info" },
        { t: "  ", c: "" },
        { t: "▓", c: "accent", dim: true },
        { t: "▓", c: "ember", dim: true },
        { t: "▓", c: "success", dim: true },
        { t: "▓", c: "warning", dim: true },
        { t: "▓", c: "error", dim: true },
        { t: "▓", c: "info", dim: true },
        { t: "  ", c: "" },
        { t: "░", c: "ink" },
        { t: "░", c: "ink-dim" },
        { t: "░", c: "muted" },
      ]} />
      <Empty />
      <Line content={[
        { t: g.arrow + " ", c: "ember" },
        { t: "diga o que precisa.", c: "ink-dim" },
      ]} />
      <Empty />
    </>
  );
}

// ─── 2. WELCOME / FIRST SIGHT (antes do onboarding técnico) ───────────────────
function WelcomeScreen() {
  const g = useGlyphs();
  return (
    <>
      <Empty />
      <Empty />
      <Line content={[
        { t: "                      ", c: "" },
        { t: g.h.repeat(3), c: "accent" },
        { t: " primeira vez aqui ", c: "accent" },
        { t: g.h.repeat(3), c: "accent" },
      ]} />
      <Empty />
      <Empty />
      <Line content={[
        { t: "      ", c: "" },
        { t: "Sou Nyx.", c: "accent", b: true },
      ]} />
      <Empty />
      <Line content={[
        { t: "      ", c: "" },
        { t: "Vivo neste terminal. ", c: "ink" },
        { t: "100% offline.", c: "ink-dim" },
      ]} />
      <Line content={[
        { t: "      ", c: "" },
        { t: "Não falo com servidor. Não envio sua sessão.", c: "ink" },
      ]} />
      <Line content={[
        { t: "      ", c: "" },
        { t: "Nada do que conversarmos sai daqui.", c: "ink-dim" },
      ]} />
      <Empty />
      <Empty />
      <Line content={[
        { t: "      ", c: "" },
        { t: "Antes de começarmos, três escolhas.", c: "ember" },
      ]} />
      <Line content={[
        { t: "      ", c: "" },
        { t: "Trinta segundos. ", c: "ink-dim" },
        { t: "Você pode pular tudo com ", c: "ink-dim" },
        { t: "Esc", c: "ember", b: true },
        { t: ".", c: "ink-dim" },
      ]} />
      <Empty />
      <Empty />
      <Line content={[
        { t: "      ", c: "" },
        { t: "  ", c: "" },
        { t: "[", c: "muted" },
        { t: "Enter", c: "accent", b: true },
        { t: "]", c: "muted" },
        { t: " seguir  ", c: "ink" },
        { t: g.bullet, c: "muted" },
        { t: "  [", c: "muted" },
        { t: "Esc", c: "accent", b: true },
        { t: "]", c: "muted" },
        { t: " usar padrões  ", c: "ink" },
        { t: g.bullet, c: "muted" },
        { t: "  [", c: "muted" },
        { t: "Ctrl+D", c: "accent", b: true },
        { t: "]", c: "muted" },
        { t: " sair", c: "ink" },
      ]} />
      <Empty />
      <Empty />
    </>
  );
}

// ─── 3. SPRINT TRACKER (multi-task, recap narrativo) ──────────────────────────
function SprintTrackerScreen() {
  const g = useGlyphs();
  return (
    <>
      <Empty />
      {/* tabela de sprints */}
      <Line content={[
        { t: "  ", c: "" },
        { t: g.tl + g.h.repeat(20) + g.tjoin + g.h.repeat(12) + g.tjoin + g.h.repeat(20) + g.tr, c: "accent", dim: true },
      ]} />
      <Line content={[
        { t: "  ", c: "" },
        { t: g.v, c: "accent", dim: true },
        { t: "  Sprint            ", c: "ember", b: true },
        { t: g.v, c: "accent", dim: true },
        { t: " Status     ", c: "ember", b: true },
        { t: g.v, c: "accent", dim: true },
        { t: " Hash               ", c: "ember", b: true },
        { t: g.v, c: "accent", dim: true },
      ]} />
      <Line content={[
        { t: "  ", c: "" },
        { t: g.ljoin + g.h.repeat(20) + g.cross + g.h.repeat(12) + g.cross + g.h.repeat(20) + g.rjoin, c: "accent", dim: true },
      ]} />
      <Line content={[
        { t: "  ", c: "" },
        { t: g.v, c: "accent", dim: true },
        { t: "  R-FAB-2           ", c: "ink" },
        { t: g.v, c: "accent", dim: true },
        { t: " mergeado   ", c: "success" },
        { t: g.v, c: "accent", dim: true },
        { t: " 46efafa            ", c: "ink-dim" },
        { t: g.v, c: "accent", dim: true },
      ]} />
      <Line content={[
        { t: "  ", c: "" },
        { t: g.v, c: "accent", dim: true },
        { t: "  R-VAULT-A         ", c: "ink" },
        { t: g.v, c: "accent", dim: true },
        { t: " mergeado   ", c: "success" },
        { t: g.v, c: "accent", dim: true },
        { t: " 81d4bad            ", c: "ink-dim" },
        { t: g.v, c: "accent", dim: true },
      ]} />
      <Line content={[
        { t: "  ", c: "" },
        { t: g.v, c: "accent", dim: true },
        { t: "  R-RECAP-1         ", c: "ink" },
        { t: g.v, c: "accent", dim: true },
        { t: " mergeado   ", c: "success" },
        { t: g.v, c: "accent", dim: true },
        { t: " bb25a6b            ", c: "ink-dim" },
        { t: g.v, c: "accent", dim: true },
      ]} />
      <Line content={[
        { t: "  ", c: "" },
        { t: g.v, c: "accent", dim: true },
        { t: "  R-MEDIA-1 ", c: "ink" },
        { t: "(re-dispatch)", c: "ember", dim: true },
        { t: g.v, c: "accent", dim: true },
        { t: " rodando    ", c: "ember", b: true },
        { t: g.v, c: "accent", dim: true },
        { t: " ", c: "" },
        { t: "agente aa84bc25", c: "ember" },
        { t: "    ", c: "" },
        { t: g.v, c: "accent", dim: true },
      ]} />
      <Line content={[
        { t: "  ", c: "" },
        { t: g.bl + g.h.repeat(20) + g.bjoin + g.h.repeat(12) + g.bjoin + g.h.repeat(20) + g.br, c: "accent", dim: true },
      ]} />
      <Empty />
      {/* insight callout */}
      <Line content={[
        { t: "  ", c: "" },
        { t: g.mark_safe + " Insight ", c: "ember", b: true },
        { t: g.h.repeat(58), c: "ember", dim: true },
      ]} />
      <Line content={[
        { t: "  ", c: "" },
        { t: "- R-RECAP-1 reportou padrão importante: spec usou nomenclatura", c: "ink" },
      ]} />
      <Line content={[
        { t: "  ", c: "" },
        { t: "  conceitual (", c: "ink" },
        { t: "CardConquistas, /conquista/[id]", c: "ember" },
        { t: ") que não existia.", c: "ink" },
      ]} />
      <Line content={[
        { t: "  ", c: "" },
        { t: "  Agente fez sanity check via grep, reformulou via mapa central.", c: "ink" },
      ]} />
      <Line content={[
        { t: "  ", c: "" },
        { t: "  ", c: "" },
        { t: "Lição: ", c: "ember", b: true },
        { t: "referenciar arquivos concretos, não conceitos.", c: "ink-dim" },
      ]} />
      <Empty />
      <Line content={[
        { t: "  ", c: "" },
        { t: "- 2 agentes consecutivos HONRARAM worktree isolation. Reforça", c: "ink" },
      ]} />
      <Line content={[
        { t: "  ", c: "" },
        { t: "  R-DX-EXECUTOR-WORKTREE-ENFORCE é P2 (não P0).", c: "ink-dim" },
      ]} />
      <Empty />
      <Line content={[
        { t: "  ", c: "" },
        { t: g.h.repeat(70), c: "ember", dim: true },
      ]} />
      <Empty />
      <Line content={[
        { t: "  ", c: "" },
        { t: "Aguardando R-MEDIA-1.", c: "ink-dim" },
      ]} />
      <Empty />
      <Line content={[
        { t: "  ", c: "" },
        { t: g.mark_safe, c: "ember" },
        { t: " Baked for ", c: "ink-dim" },
        { t: "1min 28s", c: "ember", b: true },
        { t: "  ", c: "" },
        { t: g.bullet, c: "muted" },
        { t: "  1 agente local ainda rodando", c: "ink-dim" },
      ]} />
      <Empty />
      <Line content={[
        { t: "  ", c: "" },
        { t: g.mark_safe, c: "ember" },
        { t: " recap: ", c: "ember", b: true },
        { t: "Executando Onda 2A da refundação v1.0. 3 de 4 sprints", c: "ink" },
      ]} />
      <Line content={[
        { t: "  ", c: "" },
        { t: "  mergeadas (R-FAB-2, R-VAULT-A, R-RECAP-1). Próxima ação:", c: "ink" },
      ]} />
      <Line content={[
        { t: "  ", c: "" },
        { t: "  aguardar R-MEDIA-1 terminar pra mergear e abrir Onda 2B.", c: "ink" },
      ]} />
      <Empty />
      {/* task list */}
      <Line content={[
        { t: "  ", c: "" },
        { t: "6 tarefas ", c: "ink-dim" },
        { t: "(", c: "muted" },
        { t: "1 feita", c: "success", b: true },
        { t: ", ", c: "muted" },
        { t: "1 em curso", c: "ember", b: true },
        { t: ", ", c: "muted" },
        { t: "4 abertas", c: "ink", b: true },
        { t: ")", c: "muted" },
      ]} />
      <Line content={[{ t: "  ", c: "" }, { t: "■ ", c: "ember", b: true }, { t: "Onda 2A: dispatch de 4 agentes paralelos", c: "ink", b: true }]} />
      <Line content={[{ t: "  ", c: "" }, { t: "□ ", c: "muted" }, { t: "Onda 2B: dispatch de 4 agentes paralelos", c: "ink" }]} />
      <Line content={[{ t: "  ", c: "" }, { t: "□ ", c: "muted" }, { t: "Onda 2C: dispatch de 5 agentes paralelos", c: "ink" }]} />
      <Line content={[{ t: "  ", c: "" }, { t: "□ ", c: "muted" }, { t: "Onda 2D: cross-flow fixes", c: "ink" }]} />
      <Line content={[{ t: "  ", c: "" }, { t: "□ ", c: "muted" }, { t: "Build alpha-12 + validação ao vivo", c: "ink" }]} />
      <Line content={[{ t: "  ", c: "" }, { t: "  …", c: "muted" }, { t: " +1 concluída", c: "ink-dim" }]} />
      <Empty />
    </>
  );
}

// ─── 4. SESSÃO DE CODING — sequência realista do dev usando o Nyx ─────────────
function CodingSessionScreen() {
  const g = useGlyphs();
  return (
    <>
      <Empty />
      <Line content={[
        { t: "  ", c: "" },
        { t: g.h.repeat(2), c: "accent", dim: true },
        { t: " 09:42 ", c: "ink-dim" },
        { t: g.h.repeat(64), c: "accent", dim: true },
      ]} />
      <Empty />
      <Line content={[{ t: "  ", c: "" }, { t: g.arrow + " ", c: "ember" }, { t: "achei um bug no parser. quando o payload vem com BOM, o nível 3", c: "ink" }]} />
      <Line content={[{ t: "  ", c: "" }, { t: "  ", c: "" }, { t: "explode com UnicodeDecodeError. dá pra investigar e arrumar?", c: "ink" }]} />
      <Empty />
      <Line content={[{ t: "  ", c: "" }, { t: "Nyx ", c: "accent", b: true }]} />
      <Line content={[{ t: "  ", c: "" }, { t: g.h.repeat(3), c: "accent" }]} />
      <Line content={[{ t: "  ", c: "" }, { t: "Vou começar lendo o parser e procurando a chamada de decode.", c: "ink" }]} />
      <Empty />
      <Line content={[
        { t: "  ", c: "" },
        { t: g.tl + g.h + " ", c: "accent" },
        { t: g.bullet + " ", c: "accent" },
        { t: "grep", c: "accent", b: true },
        { t: "('decode', 'parser.py')", c: "ink-dim" },
        { t: g.h.repeat(14), c: "accent", dim: true },
        { t: " ok · 4ms ", c: "success" },
        { t: g.h + g.tr, c: "accent" },
      ]} />
      <Line content={[{ t: "  ", c: "" }, { t: g.v, c: "accent", dim: true }, { t: "  3 ocorrências em L42, L189, L312", c: "ink-dim" }]} />
      <Line content={[{ t: "  ", c: "" }, { t: g.bl + g.h.repeat(64) + g.br, c: "accent", dim: true }]} />
      <Empty />
      <Line content={[
        { t: "  ", c: "" },
        { t: g.tl + g.h + " ", c: "accent" },
        { t: g.bullet + " ", c: "accent" },
        { t: "read_file", c: "accent", b: true },
        { t: "(parser.py, L180-200)", c: "ink-dim" },
        { t: g.h.repeat(8), c: "accent", dim: true },
        { t: " ok · 6ms ", c: "success" },
        { t: g.h + g.tr, c: "accent" },
      ]} />
      <Line content={[{ t: "  ", c: "" }, { t: g.v, c: "accent", dim: true }, { t: "  achei. linha 189 usa payload.decode('utf-8') sem errors=.", c: "ink-dim" }]} />
      <Line content={[{ t: "  ", c: "" }, { t: g.bl + g.h.repeat(64) + g.br, c: "accent", dim: true }]} />
      <Empty />
      <Line content={[{ t: "  ", c: "" }, { t: "Confirmado. BOM (U+FEFF) sobrevive ao split mas quebra o JSON.", c: "ink" }]} />
      <Line content={[{ t: "  ", c: "" }, { t: "Vou aplicar ", c: "ink" }, { t: "utf-8-sig", c: "ember" }, { t: " que strip o BOM, e adicionar testes.", c: "ink" }]} />
      <Empty />
      <Line content={[
        { t: "  ", c: "" },
        { t: g.tl + g.h + " ", c: "ember" },
        { t: g.bullet + " ", c: "ember" },
        { t: "edit_file", c: "ember", b: true },
        { t: "(parser.py)", c: "ink-dim" },
        { t: g.h.repeat(20), c: "ember", dim: true },
        { t: " ok · 12ms ", c: "success" },
        { t: g.h + g.tr, c: "ember" },
      ]} />
      <Line content={[{ t: "  ", c: "" }, { t: g.v, c: "ember", dim: true }, { t: "  ", c: "" }, { t: "−1 ", c: "error" }, { t: g.bullet, c: "muted" }, { t: " +1 ", c: "success" }, { t: g.bullet, c: "muted" }, { t: " L189 ", c: "ink-dim" }, { t: "(payload.decode('utf-8-sig'))", c: "ember" }]} />
      <Line content={[{ t: "  ", c: "" }, { t: g.bl + g.h.repeat(64) + g.br, c: "ember", dim: true }]} />
      <Empty />
      <Line content={[
        { t: "  ", c: "" },
        { t: g.tl + g.h + " ", c: "ember" },
        { t: g.bullet + " ", c: "ember" },
        { t: "write_file", c: "ember", b: true },
        { t: "(tests/parser/test_bom.py)", c: "ink-dim" },
        { t: g.h.repeat(8), c: "ember", dim: true },
        { t: " ok · 8ms ", c: "success" },
        { t: g.h + g.tr, c: "ember" },
      ]} />
      <Line content={[{ t: "  ", c: "" }, { t: g.v, c: "ember", dim: true }, { t: "  +24 linhas — 3 testes (BOM puro, BOM+BOM, BOM no meio)", c: "ink-dim" }]} />
      <Line content={[{ t: "  ", c: "" }, { t: g.bl + g.h.repeat(64) + g.br, c: "ember", dim: true }]} />
      <Empty />
      <Line content={[
        { t: "  ", c: "" },
        { t: g.tl + g.h + " ", c: "info" },
        { t: g.bullet + " ", c: "info" },
        { t: "run_command", c: "info", b: true },
        { t: "(pytest tests/parser/test_bom.py)", c: "ink-dim" },
        { t: g.h.repeat(4), c: "info", dim: true },
        { t: " ok · 612ms ", c: "success" },
        { t: g.h + g.tr, c: "info" },
      ]} />
      <Line content={[{ t: "  ", c: "" }, { t: g.v, c: "info", dim: true }, { t: "  ", c: "" }, { t: "3 passed ", c: "success" }, { t: g.bullet, c: "muted" }, { t: " 0 failed ", c: "ink-dim" }, { t: g.bullet, c: "muted" }, { t: " 0 skipped", c: "ink-dim" }]} />
      <Line content={[{ t: "  ", c: "" }, { t: g.bl + g.h.repeat(64) + g.br, c: "info", dim: true }]} />
      <Empty />
      <Line content={[{ t: "  ", c: "" }, { t: "Resolvido. ", c: "success", b: true }, { t: "Os 3 testes passaram. ", c: "ink" }, { t: "Faço o commit?", c: "ink-dim" }]} />
      <Empty />
      <Line content={[{ t: "  ", c: "" }, { t: g.arrow + " ", c: "ember" }, { t: "sim, com mensagem padrão", c: "ink" }]} />
      <Empty />
      <Line content={[
        { t: "  ", c: "" },
        { t: g.tl + g.h + " ", c: "ember" },
        { t: g.bullet + " ", c: "ember" },
        { t: "/commit", c: "ember", b: true },
        { t: g.h.repeat(46), c: "ember", dim: true },
        { t: " ok · 240ms ", c: "success" },
        { t: g.h + g.tr, c: "ember" },
      ]} />
      <Line content={[{ t: "  ", c: "" }, { t: g.v, c: "ember", dim: true }, { t: "  ", c: "" }, { t: "[main 8f3a2e1] ", c: "info" }, { t: "fix(parser): strip BOM no nível 3 de decode", c: "ink" }]} />
      <Line content={[{ t: "  ", c: "" }, { t: g.v, c: "ember", dim: true }, { t: "  ", c: "" }, { t: "  2 arquivos alterados, 25 inserções, 1 exclusão", c: "ink-dim" }]} />
      <Line content={[{ t: "  ", c: "" }, { t: g.bl + g.h.repeat(64) + g.br, c: "ember", dim: true }]} />
      <Empty />
      <FooterBar pct={28} model="qwen3:4b" iter={7} reads={3} mods={2} width={78} />
      <Empty />
    </>
  );
}

// ─── 5. MULTI-TAB — múltiplas sessões nomeadas ────────────────────────────────
function MultiTabScreen() {
  const g = useGlyphs();
  return (
    <>
      <Empty />
      {/* barra de tabs */}
      <Line content={[
        { t: " ", c: "" },
        { t: g.h.repeat(2), c: "accent", dim: true },
        { t: " ", c: "" },
        { t: g.bullet, c: "accent" },
        { t: " resume-onda-r-phase-2 ", c: "accent", b: true },
        { t: " ", c: "" },
        { t: g.bullet, c: "muted" },
        { t: " audit-remediation ", c: "ink-dim" },
        { t: " ", c: "" },
        { t: g.bullet, c: "muted" },
        { t: " restaurar-teleporte ", c: "ink-dim" },
        { t: " ", c: "" },
        { t: "+", c: "muted" },
      ]} />
      <Line content={[
        { t: " ", c: "" },
        { t: g.h.repeat(2) + g.bjoin + g.h.repeat(24) + g.tjoin + g.h.repeat(42), c: "accent", dim: true },
      ]} />
      <Empty />
      {/* conteúdo da tab ativa — versão reduzida do sprint tracker */}
      <Line content={[
        { t: "   ", c: "" },
        { t: "tab ativa: ", c: "ink-dim" },
        { t: "resume-onda-r-phase-2", c: "accent", b: true },
      ]} />
      <Line content={[
        { t: "   ", c: "" },
        { t: "iniciada 09:42 ", c: "ink-dim" },
        { t: g.bullet, c: "muted" },
        { t: " 1h 23min ativa ", c: "ink-dim" },
        { t: g.bullet, c: "muted" },
        { t: " 14 turns ", c: "ink-dim" },
        { t: g.bullet, c: "muted" },
        { t: " 188.7k tokens", c: "ink-dim" },
      ]} />
      <Empty />
      <Line content={[
        { t: "   ", c: "" },
        { t: "objetivo  ", c: "ember" },
        { t: "Onda 2A: dispatch de 4 agentes paralelos pra fase R", c: "ink" },
      ]} />
      <Empty />
      <Line content={[
        { t: "   ", c: "" },
        { t: "estado    ", c: "ember" },
        { t: "3 de 4 sprints mergeadas, 1 em re-dispatch", c: "ink" },
      ]} />
      <Line content={[
        { t: "   ", c: "" },
        { t: "          ", c: "" },
        { t: g.bullet, c: "success" },
        { t: " R-FAB-2  ", c: "ink-dim" },
        { t: g.bullet, c: "success" },
        { t: " R-VAULT-A  ", c: "ink-dim" },
        { t: g.bullet, c: "success" },
        { t: " R-RECAP-1  ", c: "ink-dim" },
        { t: g.bullet, c: "ember" },
        { t: " R-MEDIA-1", c: "ember" },
      ]} />
      <Empty />
      <Line content={[
        { t: "   ", c: "" },
        { t: "outras    ", c: "ember" },
        { t: "Ctrl+Tab alterna ", c: "ink-dim" },
        { t: g.bullet, c: "muted" },
        { t: " Ctrl+N nova ", c: "ink-dim" },
        { t: g.bullet, c: "muted" },
        { t: " Ctrl+W fecha", c: "ink-dim" },
      ]} />
      <Empty />
      <Line content={[
        { t: "   ", c: "" },
        { t: g.h.repeat(2), c: "accent", dim: true },
        { t: " tabs em segundo plano ", c: "ink-dim" },
        { t: g.h.repeat(46), c: "accent", dim: true },
      ]} />
      <Empty />
      <Line content={[
        { t: "   ", c: "" },
        { t: "  ", c: "" },
        { t: "audit-remediation-pipeline-progress  ", c: "ink-dim" },
        { t: "23 turns ", c: "muted" },
        { t: g.bullet, c: "muted" },
        { t: " ", c: "" },
        { t: "última 11min atrás", c: "muted" },
      ]} />
      <Line content={[
        { t: "   ", c: "" },
        { t: "  ", c: "" },
        { t: "restaurar-sessão-de-teleporte        ", c: "ink-dim" },
        { t: " 8 turns ", c: "muted" },
        { t: g.bullet, c: "muted" },
        { t: " ", c: "" },
        { t: "última 1h atrás",  c: "muted" },
      ]} />
      <Empty />
    </>
  );
}

// ─── 6. BYPASS MODE — pemissões dispensadas ───────────────────────────────────
function BypassModeScreen() {
  const g = useGlyphs();
  return (
    <>
      <Empty />
      <Line content={[
        { t: "  ", c: "" },
        { t: g.h.repeat(2), c: "ember" },
        { t: " BYPASS PERMISSIONS ", c: "ember", b: true },
        { t: g.h.repeat(48), c: "ember", dim: true },
      ]} />
      <Empty />
      <Line content={[{ t: "  ", c: "" }, { t: "Nyx ", c: "accent", b: true }, { t: "(pausada): ", c: "muted" }, { t: "Você pediu modo ", c: "ink-dim" }, { t: "bypass", c: "ember", b: true }, { t: ".", c: "ink-dim" }]} />
      <Empty />
      <Line content={[{ t: "  ", c: "" }, { t: "Nesse modo, vou rodar tools sem te perguntar antes.", c: "ink" }]} />
      <Line content={[{ t: "  ", c: "" }, { t: "Inclui ", c: "ink" }, { t: "run_command", c: "ember", b: true }, { t: ", ", c: "ink" }, { t: "edit_file", c: "ember", b: true }, { t: ", ", c: "ink" }, { t: "write_file", c: "ember", b: true }, { t: ".", c: "ink" }]} />
      <Empty />
      <Line content={[{ t: "  ", c: "" }, { t: "Continuo respeitando:", c: "ink" }]} />
      <Line content={[{ t: "  ", c: "" }, { t: "  ", c: "" }, { t: g.bullet, c: "success" }, { t: " operações fora da pasta do projeto ainda pedem confirmação", c: "ink-dim" }]} />
      <Line content={[{ t: "  ", c: "" }, { t: "  ", c: "" }, { t: g.bullet, c: "success" }, { t: " comandos destrutivos (rm -rf, drop, etc.) ainda pedem ritual", c: "ink-dim" }]} />
      <Line content={[{ t: "  ", c: "" }, { t: "  ", c: "" }, { t: g.bullet, c: "success" }, { t: " git push --force ainda pede ritual", c: "ink-dim" }]} />
      <Empty />
      <Line content={[{ t: "  ", c: "" }, { t: "Bypass dura até ", c: "ink-dim" }, { t: "/quit", c: "ember", b: true }, { t: " ou ", c: "ink-dim" }, { t: "shift+tab", c: "ember", b: true }, { t: ".", c: "ink-dim" }]} />
      <Line content={[{ t: "  ", c: "" }, { t: "Não persiste entre sessões.", c: "ink-dim" }]} />
      <Empty />
      <Line content={[
        { t: "  ", c: "" },
        { t: g.tl + g.h.repeat(2), c: "ember", dim: true },
        { t: " confirma? ", c: "ember" },
        { t: g.h.repeat(54), c: "ember", dim: true },
        { t: g.tr, c: "ember", dim: true },
      ]} />
      <Line content={[
        { t: "  ", c: "" },
        { t: g.v, c: "ember", dim: true },
        { t: "  ", c: "" },
        { t: "[s] ", c: "success" },
        { t: "ativar bypass até /quit  ", c: "ink" },
        { t: "[n] ", c: "error" },
        { t: "cancelar       ", c: "ink" },
        { t: g.v, c: "ember", dim: true },
      ]} />
      <Line content={[
        { t: "  ", c: "" },
        { t: g.bl + g.h.repeat(66) + g.br, c: "ember", dim: true },
      ]} />
      <Empty />
      <Line content={[{ t: "  ", c: "" }, { t: g.arrow + g.arrow + " ", c: "ember" }, { t: "bypass permissions on", c: "ember" }, { t: "  ", c: "" }, { t: "(shift+tab pra alternar)", c: "ink-dim" }]} />
      <Empty />
    </>
  );
}

// ─── 7. COST TELEMETRY — footer expandido ─────────────────────────────────────
function CostTelemetryScreen() {
  const g = useGlyphs();
  return (
    <>
      <Empty />
      <Line content={[
        { t: "  ", c: "" },
        { t: "telemetria de custo", c: "accent", b: true },
        { t: g.h.repeat(2), c: "accent", dim: true },
        { t: " ", c: "" },
        { t: g.bullet, c: "muted" },
        { t: " 100% offline · custo declarado = zero", c: "ink-dim" },
      ]} />
      <Empty />
      <Line content={[
        { t: "  ", c: "" },
        { t: "sessão atual", c: "ember", b: true },
        { t: g.h.repeat(60), c: "ember", dim: true },
      ]} />
      <Line content={[
        { t: "  ", c: "" },
        { t: "  duração       ", c: "ink-dim" },
        { t: "25min 31s", c: "ink", b: true },
      ]} />
      <Line content={[
        { t: "  ", c: "" },
        { t: "  tokens lidos  ", c: "ink-dim" },
        { t: "↓ 188 712 ", c: "ink", b: true },
        { t: "(qwen3 input)", c: "muted" },
      ]} />
      <Line content={[
        { t: "  ", c: "" },
        { t: "  tokens gerados ", c: "ink-dim" },
        { t: "↑  42 318 ", c: "ink", b: true },
        { t: "(qwen3 output)", c: "muted" },
      ]} />
      <Line content={[
        { t: "  ", c: "" },
        { t: "  iterações    ", c: "ink-dim" },
        { t: "12 / 30 ", c: "ink", b: true },
        { t: "(40% do orçamento)", c: "muted" },
      ]} />
      <Empty />
      <Line content={[
        { t: "  ", c: "" },
        { t: "custo equivalente", c: "ember", b: true },
        { t: g.h.repeat(57), c: "ember", dim: true },
      ]} />
      <Line content={[
        { t: "  ", c: "" },
        { t: "  ", c: "" },
        { t: "se rodasse via Claude Sonnet ", c: "ink-dim" },
        { t: "≈ ", c: "muted" },
        { t: "US$ 1,12", c: "warning", b: true },
      ]} />
      <Line content={[
        { t: "  ", c: "" },
        { t: "  ", c: "" },
        { t: "se rodasse via GPT-4o      ", c: "ink-dim" },
        { t: "    ≈ ", c: "muted" },
        { t: "US$ 1,87", c: "warning", b: true },
      ]} />
      <Line content={[
        { t: "  ", c: "" },
        { t: "  ", c: "" },
        { t: "rodando local (qwen3:4b)   ", c: "ink-dim" },
        { t: "    = ", c: "muted" },
        { t: "R$ 0,00", c: "success", b: true },
        { t: "  ", c: "" },
        { t: "+ ", c: "muted" },
        { t: "12 Wh elétrica", c: "ink-dim" },
      ]} />
      <Empty />
      <Line content={[
        { t: "  ", c: "" },
        { t: "acumulado hoje", c: "ember", b: true },
        { t: g.h.repeat(59), c: "ember", dim: true },
      ]} />
      <Line content={[
        { t: "  ", c: "" },
        { t: "  4 sessões    ", c: "ink-dim" },
        { t: "1h 47min  ", c: "ink" },
        { t: g.bullet, c: "muted" },
        { t: " 612k tokens  ", c: "ink" },
        { t: g.bullet, c: "muted" },
        { t: " ", c: "" },
        { t: "custo cloud equivalente ≈ ", c: "ink-dim" },
        { t: "US$ 4,30", c: "warning" },
      ]} />
      <Empty />
      <Line content={[
        { t: "  ", c: "" },
        { t: g.bullet, c: "muted" },
        { t: " ", c: "" },
        { t: "Nyx ", c: "accent", b: true },
        { t: ": ", c: "muted" },
        { t: "Custo é uma quantia que você economiza, não que paga.", c: "ink-dim" },
      ]} />
      <Empty />
    </>
  );
}

// ─── 8. MULTI-AGENT — sub-agentes paralelos ──────────────────────────────────
function MultiAgentScreen() {
  const g = useGlyphs();
  return (
    <>
      <Empty />
      <Line content={[
        { t: "  ", c: "" },
        { t: "agentes paralelos", c: "accent", b: true },
        { t: g.h.repeat(2), c: "accent", dim: true },
        { t: " ", c: "" },
        { t: g.bullet, c: "muted" },
        { t: " 4 sub-agentes ativos · 1 supervisor (você)", c: "ink-dim" },
      ]} />
      <Empty />
      {/* árvore de agentes */}
      <Line content={[{ t: "  ", c: "" }, { t: g.bullet, c: "accent" }, { t: " ", c: "" }, { t: "supervisor", c: "accent", b: true }, { t: "  ", c: "" }, { t: g.bullet, c: "muted" }, { t: " ", c: "" }, { t: "main · você", c: "ink-dim" }]} />
      <Line content={[{ t: "  ", c: "" }, { t: g.v + "  ", c: "accent", dim: true }, { t: g.tl + g.h + " ", c: "ember", dim: true }, <BrailleSpinner key="s1" label="" color="ember" />, { t: " ", c: "" }, { t: "agente-aa84bc25 ", c: "ember", b: true }, { t: "R-MEDIA-1 ", c: "ink-dim" }, { t: g.bullet, c: "muted" }, { t: " 1min 28s ", c: "ink-dim" }, { t: g.bullet, c: "muted" }, { t: " ", c: "" }, { t: "edit_file × 3", c: "ink" }]} />
      <Line content={[{ t: "  ", c: "" }, { t: g.v + "  ", c: "accent", dim: true }, { t: g.v + " ", c: "ember", dim: true }, { t: "  └  ", c: "ink-dim" }, { t: "última ação: ", c: "ink-dim" }, { t: "write_file(src/media/dispatcher.ts)", c: "ember" }]} />
      <Line content={[{ t: "  ", c: "" }, { t: g.v + "  ", c: "accent", dim: true }, { t: g.ljoin + g.h + " ", c: "info", dim: true }, <BrailleSpinner key="s2" label="" color="info" />, { t: " ", c: "" }, { t: "agente-c2f1d903 ", c: "info", b: true }, { t: "R-AUDIT-3 ", c: "ink-dim" }, { t: g.bullet, c: "muted" }, { t: "    24s ", c: "ink-dim" }, { t: g.bullet, c: "muted" }, { t: " ", c: "" }, { t: "grep × 8 · read × 12", c: "ink" }]} />
      <Line content={[{ t: "  ", c: "" }, { t: g.v + "  ", c: "accent", dim: true }, { t: g.v + " ", c: "info", dim: true }, { t: "  └  ", c: "ink-dim" }, { t: "última ação: ", c: "ink-dim" }, { t: "read_file(src/audit/scanner.ts)", c: "info" }]} />
      <Line content={[{ t: "  ", c: "" }, { t: g.v + "  ", c: "accent", dim: true }, { t: g.ljoin + g.h + " ", c: "success", dim: true }, { t: g.bullet, c: "success" }, { t: " ", c: "" }, { t: "agente-91ef7a44 ", c: "success", b: true }, { t: "R-VAULT-A ", c: "ink-dim" }, { t: g.bullet, c: "muted" }, { t: " ", c: "" }, { t: "concluído ", c: "success" }, { t: g.bullet, c: "muted" }, { t: " mergeado", c: "ink-dim" }]} />
      <Line content={[{ t: "  ", c: "" }, { t: g.v + "  ", c: "accent", dim: true }, { t: g.bl + g.h + " ", c: "muted", dim: true }, { t: " ", c: "muted" }, { t: "agente-7b2c0e88 ", c: "muted" }, { t: "R-DOCS-1  ", c: "ink-dim" }, { t: g.bullet, c: "muted" }, { t: " fila      ", c: "muted" }, { t: g.bullet, c: "muted" }, { t: " ", c: "" }, { t: "aguarda VRAM", c: "ink-dim" }]} />
      <Empty />
      <Line content={[
        { t: "  ", c: "" },
        { t: "VRAM compartilhada ", c: "ember", b: true },
        { t: "█".repeat(18), c: "warning" },
        { t: "░".repeat(6), c: "muted" },
        { t: "  ", c: "" },
        { t: "3 modelos ativos · 1 swap aguardando", c: "ink-dim" },
      ]} />
      <Empty />
      <Line content={[
        { t: "  ", c: "" },
        { t: "saída agregada", c: "ember", b: true },
        { t: g.h.repeat(60), c: "ember", dim: true },
      ]} />
      <Line content={[{ t: "  ", c: "" }, { t: "[aa84bc25] ", c: "ember" }, { t: "modificando src/media/dispatcher.ts...", c: "ink-dim" }]} />
      <Line content={[{ t: "  ", c: "" }, { t: "[c2f1d903] ", c: "info" }, { t: "encontrou 4 chamadas órfãs em scanner.ts", c: "ink-dim" }]} />
      <Line content={[{ t: "  ", c: "" }, { t: "[91ef7a44] ", c: "success" }, { t: "OK — mergeado em main como 81d4bad", c: "ink-dim" }]} />
      <Empty />
      <Line content={[
        { t: "  ", c: "" },
        { t: "  ", c: "" },
        { t: "/agents stop <id>", c: "ember", b: true },
        { t: " para uma  ", c: "ink-dim" },
        { t: g.bullet, c: "muted" },
        { t: "  ", c: "" },
        { t: "esc esc", c: "ember", b: true },
        { t: " interrompe todas", c: "ink-dim" },
      ]} />
      <Empty />
    </>
  );
}

Object.assign(window, {
  NeofetchBootScreen, WelcomeScreen, SprintTrackerScreen, CodingSessionScreen,
  MultiTabScreen, BypassModeScreen, CostTelemetryScreen, MultiAgentScreen,
});
