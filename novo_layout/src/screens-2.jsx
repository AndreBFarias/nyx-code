// =============================================================================
// SCREENS PART 2 — Plan mode, Permission, Help, Status, Memory, Theme switcher
// =============================================================================

// ─── PLAN MODE ────────────────────────────────────────────────────────────────
function PlanModeScreen() {
  const g = useGlyphs();
  return (
    <>
      <Empty />
      <Line content={[{ t: "  ", c: "" }, { t: g.h.repeat(2), c: "ember" }, { t: " MODO PLANO ", c: "ember", b: true }, { t: g.h.repeat(50), c: "ember", dim: true }, { t: " /exit-plan para sair ", c: "ink-dim" }]} />
      <Empty />
      <Line content={[{ t: "  ", c: "" }, { t: "Nyx ", c: "accent", b: true }, { t: g.bullet, c: "muted" }, { t: " ", c: "" }, { t: "planejando · sem executar tools", c: "ink-dim" }]} />
      <Empty />
      <Line content={[{ t: "  ", c: "" }, { t: "Plano para refatorar ", c: "ink" }, { t: "parser.py", c: "ember" }, { t: ":", c: "ink" }]} />
      <Empty />
      <Line content={[{ t: "  ", c: "" }, { t: "  1. ", c: "ember" }, { t: "Mapear os 7 níveis de fallback atuais", c: "ink" }]} />
      <Line content={[{ t: "  ", c: "" }, { t: "     ", c: "" }, { t: g.bullet, c: "muted" }, { t: " ler parser.py inteiro", c: "ink-dim" }]} />
      <Line content={[{ t: "  ", c: "" }, { t: "     ", c: "" }, { t: g.bullet, c: "muted" }, { t: " identificar predicados de cada nível", c: "ink-dim" }]} />
      <Empty />
      <Line content={[{ t: "  ", c: "" }, { t: "  2. ", c: "ember" }, { t: "Criar dispatch_table como dict[int, Callable]", c: "ink" }]} />
      <Line content={[{ t: "  ", c: "" }, { t: "     ", c: "" }, { t: g.bullet, c: "muted" }, { t: " preserva a ordem de tentativa", c: "ink-dim" }]} />
      <Line content={[{ t: "  ", c: "" }, { t: "     ", c: "" }, { t: g.bullet, c: "muted" }, { t: " mantém os contratos de retorno (ParsedAction)", c: "ink-dim" }]} />
      <Empty />
      <Line content={[{ t: "  ", c: "" }, { t: "  3. ", c: "ember" }, { t: "Cobertura ", c: "ink" }, { t: "ANTES", c: "warning" }, { t: " de mudar", c: "ink" }]} />
      <Line content={[{ t: "  ", c: "" }, { t: "     ", c: "" }, { t: g.bullet, c: "muted" }, { t: " ./run.sh --gauntlet --only parser", c: "ink-dim" }]} />
      <Empty />
      <Line content={[{ t: "  ", c: "" }, { t: "  4. ", c: "ember" }, { t: "Aplicar refactor · testar · diff", c: "ink" }]} />
      <Empty />
      <Line content={[{ t: "  ", c: "" }, { t: "  ", c: "" }, { t: "Risco: ", c: "warning" }, { t: "médio.", c: "ink-dim" }, { t: " 4 testes batem direto no dispatch atual.", c: "ink-dim" }]} />
      <Empty />
      <Line content={[{ t: "  ", c: "" }, { t: `${g.tl}${g.h.repeat(62)}${g.tr}`, c: "accent", dim: true }]} />
      <Line content={[{ t: "  ", c: "" }, { t: g.v, c: "accent", dim: true }, { t: "  ", c: "" }, { t: "[s] ", c: "success" }, { t: "executar plano  ", c: "ink" }, { t: "[r] ", c: "ember" }, { t: "refinar plano  ", c: "ink" }, { t: "[n] ", c: "error" }, { t: "abandonar    ", c: "ink" }, { t: g.v, c: "accent", dim: true }]} />
      <Line content={[{ t: "  ", c: "" }, { t: `${g.bl}${g.h.repeat(62)}${g.br}`, c: "accent", dim: true }]} />
      <Empty />
    </>
  );
}

// ─── PERMISSION PROMPT ────────────────────────────────────────────────────────
function PermissionScreen() {
  const g = useGlyphs();
  return (
    <>
      <Empty />
      <Line content={[{ t: "  ", c: "" }, { t: g.h.repeat(2), c: "ember" }, { t: " PERMISSÃO ", c: "ember", b: true }, { t: g.h.repeat(56), c: "ember", dim: true }]} />
      <Empty />
      <Line content={[{ t: "  ", c: "" }, { t: "Vou executar:", c: "ink-dim" }]} />
      <Empty />
      <Line content={[{ t: "  ", c: "" }, { t: `  ${g.bullet} `, c: "ember" }, { t: "run_command", c: "ember", b: true }, { t: "(rm -rf node_modules)", c: "ink" }]} />
      <Empty />
      <Line content={[{ t: "  ", c: "" }, { t: "Categoria: ", c: "ink-dim" }, { t: "DESTRUTIVO ", c: "error", b: true }, { t: g.bullet, c: "muted" }, { t: " escopo: ", c: "ink-dim" }, { t: "fora do sandbox de leitura", c: "warning" }]} />
      <Line content={[{ t: "  ", c: "" }, { t: "Caminho:   ", c: "ink-dim" }, { t: "~/dev/nyx-code/node_modules", c: "ink" }]} />
      <Line content={[{ t: "  ", c: "" }, { t: "Tamanho:   ", c: "ink-dim" }, { t: "412 MB · 18 247 arquivos", c: "ink" }]} />
      <Empty />
      <Line content={[{ t: "  ", c: "" }, { t: `${g.tl}${g.h.repeat(2)} `, c: "ember", dim: true }, { t: "permissão", c: "ember" }, { t: ` ${g.h.repeat(48)}${g.tr}`, c: "ember", dim: true }]} />
      <Line content={[{ t: "  ", c: "" }, { t: g.v, c: "ember", dim: true }, { t: "  ", c: "" }, { t: "[s] ", c: "success" }, { t: "sim, desta vez       ", c: "ink" }, { t: "[n] ", c: "error" }, { t: "não               ", c: "ink" }, { t: g.v, c: "ember", dim: true }]} />
      <Line content={[{ t: "  ", c: "" }, { t: g.v, c: "ember", dim: true }, { t: "  ", c: "" }, { t: "[a] ", c: "info" }, { t: "sempre p/ run_command ", c: "ink" }, { t: "[b] ", c: "warning" }, { t: "bypass até /quit  ", c: "ink" }, { t: g.v, c: "ember", dim: true }]} />
      <Line content={[{ t: "  ", c: "" }, { t: `${g.bl}${g.h.repeat(62)}${g.br}`, c: "ember", dim: true }]} />
      <Empty />
    </>
  );
}

// ─── /HELP ────────────────────────────────────────────────────────────────────
function HelpScreen() {
  const g = useGlyphs();
  const cats = [
    { name: "geral", items: "/help · /quit · /clear · /status · /version" },
    { name: "código", items: "/explain · /plan · /test · /summary" },
    { name: "git", items: "/commit · /diff · /review · /branch · /pr · /rewind" },
    { name: "sistema", items: "/doctor · /model · /config · /env · /permissions · /theme" },
    { name: "sessão", items: "/compact · /context · /resume · /export · /stats · /usage" },
    { name: "memória", items: "/memory · /skills · /files · /tasks" },
    { name: "debug", items: "/trace · /ctx-viz · /break-cache" },
  ];
  return (
    <>
      <Empty />
      <Line content={[{ t: "  ", c: "" }, { t: "comandos", c: "accent", b: true }, { t: g.h.repeat(2), c: "accent", dim: true }, { t: ` ${g.bullet} 47 registrados ${g.bullet} digite / pra autocompletar`, c: "ink-dim" }]} />
      <Empty />
      {cats.map((cat, i) => (
        <React.Fragment key={i}>
          <Line content={[{ t: "  ", c: "" }, { t: `${cat.name.padEnd(10)}`, c: "ember" }, { t: cat.items, c: "ink" }]} />
        </React.Fragment>
      ))}
      <Empty />
      <Line content={[{ t: "  ", c: "" }, { t: g.h.repeat(2), c: "accent", dim: true }, { t: " atalhos ", c: "accent" }, { t: g.h.repeat(54), c: "accent", dim: true }]} />
      <Empty />
      <Line content={[{ t: "  ", c: "" }, { t: "Ctrl+D    ", c: "ember", b: true }, { t: "sair com elegância", c: "ink-dim" }]} />
      <Line content={[{ t: "  ", c: "" }, { t: "Ctrl+O    ", c: "ember", b: true }, { t: "expandir/colapsar input longo", c: "ink-dim" }]} />
      <Line content={[{ t: "  ", c: "" }, { t: "Ctrl+L    ", c: "ember", b: true }, { t: "limpar tela (preserva histórico)", c: "ink-dim" }]} />
      <Line content={[{ t: "  ", c: "" }, { t: "Esc Esc   ", c: "ember", b: true }, { t: "interromper geração em andamento", c: "ink-dim" }]} />
      <Line content={[{ t: "  ", c: "" }, { t: "Tab       ", c: "ember", b: true }, { t: "autocomplete (arquivos, comandos, memória)", c: "ink-dim" }]} />
      <Empty />
    </>
  );
}

// ─── /STATUS ──────────────────────────────────────────────────────────────────
function StatusScreen() {
  const g = useGlyphs();
  const full = g.meter_full || "█";
  const emp = g.meter_empty || "░";
  return (
    <>
      <Empty />
      <Line content={[{ t: "  ", c: "" }, { t: "telemetria", c: "accent", b: true }, { t: g.h.repeat(2), c: "accent", dim: true }, { t: ` ${g.bullet} 14m 38s ativa ${g.bullet} sessão #4d2`, c: "ink-dim" }]} />
      <Empty />
      <Line content={[{ t: "  ", c: "" }, { t: "modelo    ", c: "ink-dim" }, { t: "qwen3:4b", c: "ink", b: true }, { t: "  ", c: "" }, { t: full.repeat(18), c: "success" }, { t: full.repeat(4), c: "warning" }, { t: emp.repeat(2), c: "muted" }, { t: "  ", c: "" }, { t: "vram 3.7/4.0 GB", c: "ink-dim" }]} />
      <Line content={[{ t: "  ", c: "" }, { t: "contexto  ", c: "ink-dim" }, { t: "qwen3 32k", c: "ink", b: true }, { t: " ", c: "" }, { t: full.repeat(11), c: "accent" }, { t: emp.repeat(13), c: "muted" }, { t: "  ", c: "" }, { t: "13 856 / 32 768 tok (42%)", c: "ink-dim" }]} />
      <Line content={[{ t: "  ", c: "" }, { t: "iteração  ", c: "ink-dim" }, { t: "8/30    ", c: "ink", b: true }, { t: " ", c: "" }, { t: full.repeat(6), c: "ember" }, { t: emp.repeat(18), c: "muted" }, { t: "  ", c: "" }, { t: "27% do limite", c: "ink-dim" }]} />
      <Empty />
      <Line content={[{ t: "  ", c: "" }, { t: "tools     ", c: "ink-dim" }, { t: "read_file ", c: "ink" }, { t: "×7  ", c: "ember" }, { t: "edit_file ", c: "ink" }, { t: "×2  ", c: "ember" }, { t: "run_command ", c: "ink" }, { t: "×3  ", c: "ember" }, { t: "grep ", c: "ink" }, { t: "×4", c: "ember" }]} />
      <Line content={[{ t: "  ", c: "" }, { t: "arquivos  ", c: "ink-dim" }, { t: "lidos ", c: "ink" }, { t: "9  ", c: "ember" }, { t: g.bullet, c: "muted" }, { t: " modificados ", c: "ink" }, { t: "3  ", c: "ember" }, { t: g.bullet, c: "muted" }, { t: " criados ", c: "ink" }, { t: "0", c: "ember" }]} />
      <Line content={[{ t: "  ", c: "" }, { t: "memória   ", c: "ink-dim" }, { t: "12 entradas persistidas ", c: "ink" }, { t: g.bullet, c: "muted" }, { t: " 0 desta sessão", c: "ink-dim" }]} />
      <Empty />
      <Line content={[{ t: "  ", c: "" }, { t: "rede      ", c: "ink-dim" }, { t: g.bullet, c: "success" }, { t: " ollama :11435  ", c: "ink" }, { t: g.bullet, c: "success" }, { t: " proxy :11436  ", c: "ink" }, { t: g.bullet, c: "warning" }, { t: " moondream fria", c: "ink-dim" }]} />
      <Line content={[{ t: "  ", c: "" }, { t: "latência  ", c: "ink-dim" }, { t: "p50 312ms  ", c: "ink" }, { t: g.bullet, c: "muted" }, { t: " p95 1.4s  ", c: "ink" }, { t: g.bullet, c: "muted" }, { t: " erros 0/87", c: "success" }]} />
      <Empty />
    </>
  );
}

// ─── /MEMORY ──────────────────────────────────────────────────────────────────
function MemoryScreen() {
  const g = useGlyphs();
  return (
    <>
      <Empty />
      <Line content={[{ t: "  ", c: "" }, { t: "memória", c: "accent", b: true }, { t: g.h.repeat(2), c: "accent", dim: true }, { t: ` ${g.bullet} 12 entradas ${g.bullet} ~/.nyx/memory/`, c: "ink-dim" }]} />
      <Empty />
      <Line content={[{ t: "  ", c: "" }, { t: "ambiente", c: "ember", b: true }, { t: g.h.repeat(2), c: "ember", dim: true }, { t: " 3 entradas", c: "ink-dim" }]} />
      <Line content={[{ t: "  ", c: "" }, { t: "  ·  ", c: "muted" }, { t: "uso pyenv 3.12 neste projeto", c: "ink" }, { t: "  ", c: "" }, { t: "(2026-04-12)", c: "muted" }]} />
      <Line content={[{ t: "  ", c: "" }, { t: "  ·  ", c: "muted" }, { t: "venv mora em ./.venv (não em ~/.venvs)", c: "ink" }, { t: "  ", c: "" }, { t: "(2026-04-13)", c: "muted" }]} />
      <Line content={[{ t: "  ", c: "" }, { t: "  ·  ", c: "muted" }, { t: "ollama port custom 11435", c: "ink" }, { t: "  ", c: "" }, { t: "(2026-04-13)", c: "muted" }]} />
      <Empty />
      <Line content={[{ t: "  ", c: "" }, { t: "estilo", c: "ember", b: true }, { t: g.h.repeat(2), c: "ember", dim: true }, { t: " 4 entradas", c: "ink-dim" }]} />
      <Line content={[{ t: "  ", c: "" }, { t: "  ·  ", c: "muted" }, { t: "código sempre PT-BR em comentário/docstring", c: "ink" }, { t: "  ", c: "" }, { t: "(2026-04-15)", c: "muted" }]} />
      <Line content={[{ t: "  ", c: "" }, { t: "  ·  ", c: "muted" }, { t: "zero emoji (ADR-004)", c: "ink" }, { t: "  ", c: "" }, { t: "(2026-04-15)", c: "muted" }]} />
      <Line content={[{ t: "  ", c: "" }, { t: "  ·  ", c: "muted" }, { t: "tabs nunca; 4 spaces", c: "ink" }, { t: "  ", c: "" }, { t: "(2026-04-15)", c: "muted" }]} />
      <Line content={[{ t: "  ", c: "" }, { t: "  ·  ", c: "muted" }, { t: "sempre quebra de linha aos 88 col (black)", c: "ink" }, { t: "  ", c: "" }, { t: "(2026-04-18)", c: "muted" }]} />
      <Empty />
      <Line content={[{ t: "  ", c: "" }, { t: "decisões", c: "ember", b: true }, { t: g.h.repeat(2), c: "ember", dim: true }, { t: " 5 entradas", c: "ink-dim" }]} />
      <Line content={[{ t: "  ", c: "" }, { t: "  ·  ", c: "muted" }, { t: "qwen3:4b é o default; 7b só com /model swap", c: "ink" }, { t: "  ", c: "" }, { t: "(2026-04-20)", c: "muted" }]} />
      <Line content={[{ t: "  ", c: "" }, { t: "  ·  ", c: "muted" }, { t: "...", c: "muted" }]} />
      <Empty />
      <Line content={[{ t: "  ", c: "" }, { t: "  /memory ", c: "accent" }, { t: "add", c: "ember", b: true }, { t: " <fato>  ", c: "ink-dim" }, { t: g.bullet, c: "muted" }, { t: "  ", c: "" }, { t: "/memory ", c: "accent" }, { t: "forget", c: "ember", b: true }, { t: " <id>  ", c: "ink-dim" }, { t: g.bullet, c: "muted" }, { t: "  ", c: "" }, { t: "/memory ", c: "accent" }, { t: "edit", c: "ember", b: true }, { t: " <id>", c: "ink-dim" }]} />
      <Empty />
    </>
  );
}

// ─── /THEME ───────────────────────────────────────────────────────────────────
function ThemeSwitcherScreen() {
  const g = useGlyphs();
  const entities = [
    { id: "nyx",  hex: "#00D4AA", desc: "silenciosa, técnica" },
    { id: "eris", hex: "#FF79C6", desc: "caótica, provocadora" },
    { id: "juno", hex: "#A4CB58", desc: "fértil, generosa" },
    { id: "lars", hex: "#50FA7B", desc: "veterana, direta" },
    { id: "luna", hex: "#BD93F9", desc: "melancólica, lúcida" },
    { id: "mars", hex: "#FF5555", desc: "guerreira, urgente" },
    { id: "somn", hex: "#8BE9FD", desc: "onírica, fluida" },
  ];
  return (
    <>
      <Empty />
      <Line content={[{ t: "  ", c: "" }, { t: "tema", c: "accent", b: true }, { t: g.h.repeat(2), c: "accent", dim: true }, { t: ` ${g.bullet} estético + entidade ${g.bullet} hot-reload`, c: "ink-dim" }]} />
      <Empty />
      <Line content={[{ t: "  ", c: "" }, { t: "estético  ", c: "ember", b: true }, { t: g.h.repeat(60), c: "ember", dim: true }]} />
      <Line content={[{ t: "  ", c: "" }, { t: "  [ ] arcano    ", c: "ink-dim" }, { t: "[", c: "muted" }, { t: g.bullet, c: "accent" }, { t: "] cyber    ", c: "ink" }, { t: "[ ] brutalist  [ ] mecha  [ ] editorial", c: "ink-dim" }]} />
      <Empty />
      <Line content={[{ t: "  ", c: "" }, { t: "entidade  ", c: "ember", b: true }, { t: g.h.repeat(60), c: "ember", dim: true }]} />
      <Empty />
      {entities.map((e, i) => (
        <Line
          key={e.id}
          content={[
            { t: "  ", c: "" },
            { t: e.id === "nyx" ? "  [" : "  [ ", c: "muted" },
            ...(e.id === "nyx" ? [{ t: g.bullet, c: "accent" }] : []),
            { t: e.id === "nyx" ? "] " : "] ", c: "muted" },
            { t: e.id.padEnd(6), c: "ink", b: true },
            { t: "  ", c: "" },
            { t: "███ ", c: "accent" },
            { t: e.desc, c: "ink-dim" },
          ]}
        />
      ))}
      <Empty />
      <Line content={[{ t: "  ", c: "" }, { t: "  ", c: "" }, { t: "tab/shift-tab ", c: "ember" }, { t: "alterna · ", c: "ink-dim" }, { t: "enter ", c: "ember" }, { t: "aplica · ", c: "ink-dim" }, { t: "esc ", c: "ember" }, { t: "cancela", c: "ink-dim" }]} />
      <Empty />
    </>
  );
}

Object.assign(window, { PlanModeScreen, PermissionScreen, HelpScreen, StatusScreen, MemoryScreen, ThemeSwitcherScreen });
