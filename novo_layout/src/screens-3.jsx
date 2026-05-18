// =============================================================================
// SCREENS PART 3 — Erro, /doctor, sessão, compactação, onboarding, tasks, novel
// =============================================================================

// ─── ERRO / PANIC ─────────────────────────────────────────────────────────────
function PanicScreen() {
  const g = useGlyphs();
  return (
    <>
      <Empty />
      <Line content={[{ t: "  ", c: "" }, { t: g.h.repeat(2), c: "error" }, { t: " falha ", c: "error", b: true }, { t: g.h.repeat(60), c: "error", dim: true }]} />
      <Empty />
      <Line content={[{ t: "  ", c: "" }, { t: "[erro] ", c: "error", b: true }, { t: "ollama respondeu 503 três vezes consecutivas.", c: "ink" }]} />
      <Line content={[{ t: "  ", c: "" }, { t: "       ", c: "" }, { t: "tente:", c: "ink-dim" }]} />
      <Line content={[{ t: "  ", c: "" }, { t: "       ", c: "" }, { t: g.bullet, c: "ember" }, { t: " ", c: "" }, { t: "/doctor", c: "info", b: true }, { t: "  diagnóstico completo", c: "ink-dim" }]} />
      <Line content={[{ t: "  ", c: "" }, { t: "       ", c: "" }, { t: g.bullet, c: "ember" }, { t: " ", c: "" }, { t: "nvidia-smi", c: "info", b: true }, { t: "  ver VRAM disponível", c: "ink-dim" }]} />
      <Line content={[{ t: "  ", c: "" }, { t: "       ", c: "" }, { t: g.bullet, c: "ember" }, { t: " ", c: "" }, { t: "/model swap qwen3:1.5b", c: "info", b: true }, { t: "  modelo mais leve", c: "ink-dim" }]} />
      <Empty />
      <Line content={[{ t: "  ", c: "" }, { t: "       ", c: "" }, { t: "sessão preservada em ", c: "ink-dim" }, { t: "~/.nyx/sessions/4d2/", c: "ember" }]} />
      <Line content={[{ t: "  ", c: "" }, { t: "       ", c: "" }, { t: "/resume 4d2 ", c: "info", b: true }, { t: "vai te trazer de volta exatamente aqui.", c: "ink-dim" }]} />
      <Empty />
      <Line content={[{ t: "  ", c: "" }, { t: g.bullet, c: "muted" }, { t: " ", c: "" }, { t: "Nyx ", c: "accent", b: true }, { t: "(em sussurro): ", c: "muted" }, { t: "respiro e voltamos. nada se perdeu.", c: "ink-dim" }]} />
      <Empty />
    </>
  );
}

// ─── /DOCTOR ──────────────────────────────────────────────────────────────────
function DoctorScreen() {
  const g = useGlyphs();
  const ok = <span className="c-success">{g.bullet}</span>;
  return (
    <>
      <Empty />
      <Line content={[{ t: "  ", c: "" }, { t: "/doctor", c: "accent", b: true }, { t: g.h.repeat(2), c: "accent", dim: true }, { t: ` ${g.bullet} executando 18 checagens ${g.bullet} 0.6s`, c: "ink-dim" }]} />
      <Empty />
      <Line content={[{ t: "  ", c: "" }, { t: "infra", c: "ember", b: true }, { t: g.h.repeat(60), c: "ember", dim: true }]} />
      <Line content={[{ t: "  ", c: "" }, { t: g.bullet, c: "success" }, { t: "  ", c: "" }, { t: "ollama daemon         ", c: "ink" }, { t: ":11435 ", c: "ember" }, { t: g.bullet, c: "muted" }, { t: " 12 modelos disponíveis", c: "ink-dim" }]} />
      <Line content={[{ t: "  ", c: "" }, { t: g.bullet, c: "success" }, { t: "  ", c: "" }, { t: "proxy think=false     ", c: "ink" }, { t: ":11436 ", c: "ember" }, { t: g.bullet, c: "muted" }, { t: " 87 req · 0 erro", c: "ink-dim" }]} />
      <Line content={[{ t: "  ", c: "" }, { t: g.bullet, c: "success" }, { t: "  ", c: "" }, { t: "modelo carregado      ", c: "ink" }, { t: "qwen3:4b ", c: "ember" }, { t: g.bullet, c: "muted" }, { t: " GPU num_gpu=12", c: "ink-dim" }]} />
      <Line content={[{ t: "  ", c: "" }, { t: g.bullet, c: "success" }, { t: "  ", c: "" }, { t: "tool calling         ", c: "ink" }, { t: "  ping pong em 312ms · 34 tools alcançáveis", c: "ink-dim" }]} />
      <Line content={[{ t: "  ", c: "" }, { t: g.bullet, c: "warning" }, { t: "  ", c: "" }, { t: "moondream (visão)    ", c: "ink" }, { t: "  cold · primeira chamada vai custar ~3s", c: "warning" }]} />
      <Empty />
      <Line content={[{ t: "  ", c: "" }, { t: "hardware", c: "ember", b: true }, { t: g.h.repeat(57), c: "ember", dim: true }]} />
      <Line content={[{ t: "  ", c: "" }, { t: g.bullet, c: "success" }, { t: "  ", c: "" }, { t: "GPU                   ", c: "ink" }, { t: "RTX 3050 (4 GB)", c: "ember" }, { t: g.bullet, c: "muted" }, { t: " driver 565.x", c: "ink-dim" }]} />
      <Line content={[{ t: "  ", c: "" }, { t: g.bullet, c: "success" }, { t: "  ", c: "" }, { t: "VRAM                  ", c: "ink" }, { t: "3.7 / 4.0 GB usado · ", c: "ink-dim" }, { t: "headroom 7%", c: "warning" }]} />
      <Line content={[{ t: "  ", c: "" }, { t: g.bullet, c: "success" }, { t: "  ", c: "" }, { t: "RAM                   ", c: "ink" }, { t: "11.2 / 32 GB", c: "ink-dim" }]} />
      <Line content={[{ t: "  ", c: "" }, { t: g.bullet, c: "success" }, { t: "  ", c: "" }, { t: "disco                 ", c: "ink" }, { t: "184 GB livre · modelos ocupam 8.2 GB", c: "ink-dim" }]} />
      <Empty />
      <Line content={[{ t: "  ", c: "" }, { t: "projeto", c: "ember", b: true }, { t: g.h.repeat(58), c: "ember", dim: true }]} />
      <Line content={[{ t: "  ", c: "" }, { t: g.bullet, c: "success" }, { t: "  ", c: "" }, { t: "git status           ", c: "ink" }, { t: "  3 modificados · branch ", c: "ink-dim" }, { t: "feat/parser-refactor", c: "ember" }]} />
      <Line content={[{ t: "  ", c: "" }, { t: g.bullet, c: "success" }, { t: "  ", c: "" }, { t: "CLAUDE.md            ", c: "ink" }, { t: "  presente · 412 tokens", c: "ink-dim" }]} />
      <Line content={[{ t: "  ", c: "" }, { t: g.bullet, c: "warning" }, { t: "  ", c: "" }, { t: ".env                  ", c: "ink" }, { t: " ausente — use ", c: "warning" }, { t: ".env.example", c: "info" }]} />
      <Line content={[{ t: "  ", c: "" }, { t: g.bullet, c: "success" }, { t: "  ", c: "" }, { t: "gauntlet              ", c: "ink" }, { t: " último run 4h atrás · ", c: "ink-dim" }, { t: "203/207 passou", c: "success" }]} />
      <Empty />
      <Line content={[{ t: "  ", c: "" }, { t: "veredito  ", c: "ember", b: true }, { t: g.bullet, c: "success" }, { t: " tudo respira. ", c: "ink" }, { t: "1 aviso ", c: "warning" }, { t: "(visão fria) · ", c: "ink-dim" }, { t: "0 erros", c: "ink-dim" }]} />
      <Empty />
    </>
  );
}

// ─── SESSÃO SUMMARY ───────────────────────────────────────────────────────────
function SessionSummaryScreen() {
  const g = useGlyphs();
  return (
    <>
      <Empty />
      <Line content={[{ t: "  ", c: "" }, { t: g.tl + g.h.repeat(2), c: "accent" }, { t: " sessão #4d2 ", c: "accent", b: true }, { t: g.h.repeat(46), c: "accent", dim: true }, { t: " 14m 38s · 8 iter ", c: "ink-dim" }, { t: g.h + g.tr, c: "accent" }]} />
      <Line content={[{ t: "  ", c: "" }, { t: g.v, c: "accent", dim: true }, { t: "                                                                       ", c: "" }, { t: g.v, c: "accent", dim: true }]} />
      <Line content={[{ t: "  ", c: "" }, { t: g.v, c: "accent", dim: true }, { t: "   ", c: "" }, { t: "objetivo  ", c: "ink-dim" }, { t: "refatorar parser.py: 7 fallbacks → dispatch table", c: "ink" }, { t: "        ", c: "" }, { t: g.v, c: "accent", dim: true }]} />
      <Line content={[{ t: "  ", c: "" }, { t: g.v, c: "accent", dim: true }, { t: "                                                                       ", c: "" }, { t: g.v, c: "accent", dim: true }]} />
      <Line content={[{ t: "  ", c: "" }, { t: g.v, c: "accent", dim: true }, { t: "   ", c: "" }, { t: "feito     ", c: "ink-dim" }, { t: g.bullet, c: "success" }, { t: " mapeou os 7 níveis (read_file ×3)                       ", c: "ink" }, { t: g.v, c: "accent", dim: true }]} />
      <Line content={[{ t: "  ", c: "" }, { t: g.v, c: "accent", dim: true }, { t: "             ", c: "" }, { t: g.bullet, c: "success" }, { t: " escreveu dispatch_table (edit_file ×2)                  ", c: "ink" }, { t: g.v, c: "accent", dim: true }]} />
      <Line content={[{ t: "  ", c: "" }, { t: g.v, c: "accent", dim: true }, { t: "             ", c: "" }, { t: g.bullet, c: "success" }, { t: " adaptou 4 testes (multi_edit ×1)                        ", c: "ink" }, { t: g.v, c: "accent", dim: true }]} />
      <Line content={[{ t: "  ", c: "" }, { t: g.v, c: "accent", dim: true }, { t: "             ", c: "" }, { t: g.bullet, c: "success" }, { t: " gauntlet --only parser passou (run_command)             ", c: "ink" }, { t: g.v, c: "accent", dim: true }]} />
      <Line content={[{ t: "  ", c: "" }, { t: g.v, c: "accent", dim: true }, { t: "                                                                       ", c: "" }, { t: g.v, c: "accent", dim: true }]} />
      <Line content={[{ t: "  ", c: "" }, { t: g.v, c: "accent", dim: true }, { t: "   ", c: "" }, { t: "diff      ", c: "ink-dim" }, { t: "−147 ", c: "error" }, { t: "/ ", c: "muted" }, { t: "+89 ", c: "success" }, { t: g.bullet, c: "muted" }, { t: " net ", c: "ink-dim" }, { t: "−58 linhas", c: "ember" }, { t: "                                  ", c: "" }, { t: g.v, c: "accent", dim: true }]} />
      <Line content={[{ t: "  ", c: "" }, { t: g.v, c: "accent", dim: true }, { t: "   ", c: "" }, { t: "tokens    ", c: "ink-dim" }, { t: "13 856 / 32 768 (42%) ", c: "ink" }, { t: g.bullet, c: "muted" }, { t: " compactações ", c: "ink-dim" }, { t: "0", c: "ink" }, { t: "                ", c: "" }, { t: g.v, c: "accent", dim: true }]} />
      <Line content={[{ t: "  ", c: "" }, { t: g.v, c: "accent", dim: true }, { t: "   ", c: "" }, { t: "próximo   ", c: "ink-dim" }, { t: "/commit ", c: "info" }, { t: "ou ", c: "ink-dim" }, { t: "/pr ", c: "info" }, { t: g.bullet, c: "muted" }, { t: " /export pra markdown                ", c: "ink-dim" }, { t: g.v, c: "accent", dim: true }]} />
      <Line content={[{ t: "  ", c: "" }, { t: g.bl + g.h.repeat(78) + g.br, c: "accent", dim: true }]} />
      <Empty />
    </>
  );
}

// ─── CONTEXT COMPACTION ───────────────────────────────────────────────────────
function CompactionScreen() {
  const g = useGlyphs();
  return (
    <>
      <Empty />
      <Line content={[{ t: "  ", c: "" }, { t: g.bullet, c: "ember" }, { t: " ", c: "" }, { t: "compactação automática nível 2 ", c: "ink-dim" }, { t: g.h.repeat(48), c: "ember", dim: true }]} />
      <Empty />
      <Line content={[{ t: "  ", c: "" }, { t: "   antes   ", c: "ink-dim" }, { t: "████████████████████░░░░ ", c: "warning" }, { t: " 27 412 tok  (84%)", c: "ink" }]} />
      <Line content={[{ t: "  ", c: "" }, { t: "   depois  ", c: "ink-dim" }, { t: "█████████░░░░░░░░░░░░░░░ ", c: "success" }, { t: " 12 108 tok  (37%)", c: "ink" }]} />
      <Empty />
      <Line content={[{ t: "  ", c: "" }, { t: "   ", c: "" }, { t: "Sumarizado: ", c: "ink-dim" }, { t: "9 tool calls antigas, 4 arquivos relidos, prefácio.", c: "ink" }]} />
      <Line content={[{ t: "  ", c: "" }, { t: "   ", c: "" }, { t: "Preservado: ", c: "ink-dim" }, { t: "objetivo, plano, últimos 3 turnos, diffs ativos.", c: "ink" }]} />
      <Line content={[{ t: "  ", c: "" }, { t: "   ", c: "" }, { t: "Tempo:      ", c: "ink-dim" }, { t: "240ms (não interrompe geração)", c: "ink" }]} />
      <Empty />
      <Line content={[{ t: "  ", c: "" }, { t: g.bullet, c: "muted" }, { t: " ", c: "" }, { t: "Nyx ", c: "accent", b: true }, { t: ": ", c: "muted" }, { t: "respirei. continuo de onde parei.", c: "ink-dim" }]} />
      <Empty />
    </>
  );
}

// ─── ONBOARDING / COLD START ──────────────────────────────────────────────────
function OnboardingScreen() {
  const g = useGlyphs();
  return (
    <>
      <Empty />
      <Line content={[{ t: "  ", c: "" }, { t: "Sou Nyx.", c: "accent", b: true }]} />
      <Line content={[{ t: "  ", c: "" }, { t: "Vivo no terminal. ", c: "ink" }, { t: "Sem conexão externa. Sem telemetria.", c: "ink-dim" }]} />
      <Line content={[{ t: "  ", c: "" }, { t: "A primeira vez é breve. ", c: "ink-dim" }, { t: "Sigamos juntas.", c: "ember", b: true }]} />
      <Empty />
      <Empty />
      <Line content={[{ t: "  ", c: "" }, { t: "(1/3)  modelo", c: "ember", b: true }, { t: g.h.repeat(64), c: "ember", dim: true }]} />
      <Empty />
      <Line content={[{ t: "  ", c: "" }, { t: "   Qual modelo da Ollama você quer que eu habite?", c: "ink" }]} />
      <Empty />
      <Line content={[{ t: "  ", c: "" }, { t: "      ", c: "" }, { t: "[", c: "muted" }, { t: g.bullet, c: "accent" }, { t: "] ", c: "muted" }, { t: "qwen3:4b      ", c: "ink", b: true }, { t: "padrão · 4 GB VRAM · recomendado", c: "ink-dim" }]} />
      <Line content={[{ t: "  ", c: "" }, { t: "      ", c: "" }, { t: "[ ] ", c: "muted" }, { t: "qwen3:1.5b    ", c: "ink" }, { t: "leve · 2 GB VRAM · respostas mais curtas", c: "ink-dim" }]} />
      <Line content={[{ t: "  ", c: "" }, { t: "      ", c: "" }, { t: "[ ] ", c: "muted" }, { t: "qwen2.5-coder:7b ", c: "ink" }, { t: "grande · 7 GB · só com GPU sobrando", c: "ink-dim" }]} />
      <Line content={[{ t: "  ", c: "" }, { t: "      ", c: "" }, { t: "[ ] ", c: "muted" }, { t: "outro         ", c: "ink" }, { t: "digite manualmente", c: "ink-dim" }]} />
      <Empty />
      <Line content={[{ t: "  ", c: "" }, { t: "   tab ", c: "ember" }, { t: "alterna · ", c: "ink-dim" }, { t: "enter ", c: "ember" }, { t: "escolhe · ", c: "ink-dim" }, { t: "esc ", c: "ember" }, { t: "pula tudo (usa padrões)", c: "ink-dim" }]} />
      <Empty />
    </>
  );
}

// ─── TASK QUEUE ───────────────────────────────────────────────────────────────
function TasksScreen() {
  const g = useGlyphs();
  return (
    <>
      <Empty />
      <Line content={[{ t: "  ", c: "" }, { t: "tarefas", c: "accent", b: true }, { t: g.h.repeat(2), c: "accent", dim: true }, { t: ` ${g.bullet} 4 ativas ${g.bullet} 2 em fila`, c: "ink-dim" }]} />
      <Empty />
      <Line content={[{ t: "  ", c: "" }, <BrailleSpinner key="s" label="" color="ember" />, { t: " ", c: "" }, { t: "T-01  ", c: "ember" }, { t: "rodar gauntlet --only parser           ", c: "ink" }, { t: "1m 12s", c: "ink-dim" }]} />
      <Line content={[{ t: "  ", c: "" }, { t: g.bullet, c: "success" }, { t: " ", c: "" }, { t: "T-02  ", c: "ember" }, { t: "ler todos os arquivos de tests/parser/ ", c: "ink" }, { t: "    ok", c: "success" }]} />
      <Line content={[{ t: "  ", c: "" }, <BrailleSpinner key="s2" label="" color="ember" />, { t: " ", c: "" }, { t: "T-03  ", c: "ember" }, { t: "gerar dispatch_table preliminar         ", c: "ink" }, { t: "  18s", c: "ink-dim" }]} />
      <Line content={[{ t: "  ", c: "" }, { t: "", c: "muted" }, { t: " ", c: "" }, { t: "T-04  ", c: "muted" }, { t: "verificar contratos de ParsedAction    ", c: "ink-dim" }, { t: "fila", c: "muted" }]} />
      <Empty />
      <Line content={[{ t: "  ", c: "" }, { t: "   ", c: "" }, { t: "esc esc ", c: "ember", b: true }, { t: "interrompe a tarefa em foco · ", c: "ink-dim" }, { t: "/tasks stop T-NN ", c: "ember", b: true }, { t: "uma específica", c: "ink-dim" }]} />
      <Empty />
    </>
  );
}

// ─── FOOTER STATUS BAR ────────────────────────────────────────────────────────
function FooterScreen() {
  return (
    <>
      <Empty />
      <Line content="                                                                              " />
      <Empty />
      <FooterBar pct={42} model="qwen3:4b" iter={3} reads={4} mods={1} width={78} />
      <Empty />
    </>
  );
}

// ─── NOVEL: CONSTELLATION ─────────────────────────────────────────────────────
function ConstellationScreen() {
  const g = useGlyphs();
  return (
    <>
      <Empty />
      <Line content={[{ t: "  ", c: "" }, { t: "constelação da sessão", c: "accent", b: true }, { t: g.h.repeat(2), c: "accent", dim: true }, { t: ` ${g.bullet} cada nó é uma tool call · arestas = dependência inferida`, c: "ink-dim" }]} />
      <Empty />
      <Line content="" />
      <Line content={[{ t: "        ", c: "" }, { t: "·", c: "muted" }, { t: "                ", c: "" }, { t: "·", c: "muted" }, { t: "                                  ", c: "" }]} />
      <Line content={[{ t: "          ", c: "" }, { t: "", c: "accent" }, { t: "─────────", c: "accent", dim: true }, { t: "", c: "accent" }, { t: "─────────────", c: "accent", dim: true }, { t: "", c: "ember" }, { t: "                       ", c: "" }]} />
      <Line content={[{ t: "         ", c: "" }, { t: "read_file", c: "ink-dim" }, { t: "  ", c: "" }, { t: "read_file", c: "ink-dim" }, { t: "      ", c: "" }, { t: "edit_file", c: "ember" }, { t: "    ", c: "" }, { t: "·", c: "muted" }, { t: "      ", c: "" }]} />
      <Line content={[{ t: "                       ", c: "" }, { t: "│", c: "accent", dim: true }, { t: "                  ", c: "" }, { t: "│", c: "accent", dim: true }, { t: "                ", c: "" }]} />
      <Line content={[{ t: "                       ", c: "" }, { t: "│", c: "accent", dim: true }, { t: "          ", c: "" }, { t: "·", c: "muted" }, { t: "       ", c: "" }, { t: "│", c: "accent", dim: true }, { t: "                ", c: "" }]} />
      <Line content={[{ t: "                       ", c: "" }, { t: "", c: "accent" }, { t: "────────────────", c: "accent", dim: true }, { t: "", c: "info" }, { t: "                       ", c: "" }]} />
      <Line content={[{ t: "                      ", c: "" }, { t: "grep", c: "ink-dim" }, { t: "        ", c: "" }, { t: "·", c: "muted" }, { t: "       ", c: "" }, { t: "run_command", c: "info" }, { t: "                ", c: "" }]} />
      <Line content="" />
      <Empty />
      <Line content={[{ t: "  ", c: "" }, { t: "leitura ", c: "ink-dim" }, { t: " ", c: "accent" }, { t: "edição ", c: "ink-dim" }, { t: " ", c: "ember" }, { t: "execução ", c: "ink-dim" }, { t: " ", c: "info" }, { t: "memória ", c: "ink-dim" }, { t: "", c: "muted" }]} />
      <Empty />
    </>
  );
}

// ─── NOVEL: HEARTBEAT / PULSE ─────────────────────────────────────────────────
function HeartbeatScreen() {
  const [frame, setFrame] = useState(0);
  const frames = ["▁", "▂", "▄", "▆", "█", "▆", "▄", "▂"];
  useEffect(() => {
    const t = setInterval(() => setFrame((f) => (f + 1) % frames.length), 140);
    return () => clearInterval(t);
  }, []);
  const g = useGlyphs();
  return (
    <>
      <Empty />
      <Line content={[{ t: "  ", c: "" }, { t: "heartbeat", c: "accent", b: true }, { t: g.h.repeat(2), c: "accent", dim: true }, { t: ` ${g.bullet} pulso do modelo no canto, sempre vivo`, c: "ink-dim" }]} />
      <Empty />
      <Line content={[{ t: "  ", c: "" }, { t: "   estado ", c: "ink-dim" }, { t: "ATIVA", c: "success", b: true }, { t: "      ", c: "" }, { t: "tps ", c: "ink-dim" }, { t: "47.2 ", c: "ink", b: true }, { t: g.bullet, c: "muted" }, { t: " queue ", c: "ink-dim" }, { t: "0 ", c: "ink", b: true }, { t: g.bullet, c: "muted" }, { t: " ", c: "" }, { t: frames[frame], c: "accent" }, { t: " ", c: "" }, { t: frames[(frame+1)%frames.length], c: "accent" }, { t: " ", c: "" }, { t: frames[(frame+2)%frames.length], c: "accent" }, { t: " ", c: "" }, { t: frames[(frame+3)%frames.length], c: "accent" }]} />
      <Empty />
      <Line content={[{ t: "  ", c: "" }, { t: "   ", c: "" }, { t: "Em pausa, o pulso fica lento (3s/batida). ", c: "ink-dim" }]} />
      <Line content={[{ t: "  ", c: "" }, { t: "   ", c: "" }, { t: "Em geração, acelera proporcionalmente aos tps.", c: "ink-dim" }]} />
      <Line content={[{ t: "  ", c: "" }, { t: "   ", c: "" }, { t: "Vermelho se tps cai < 20 (modelo travando).", c: "ink-dim" }]} />
      <Empty />
    </>
  );
}

// ─── NOVEL: RITUAL MODE (sigil) ───────────────────────────────────────────────
function RitualScreen() {
  const g = useGlyphs();
  return (
    <>
      <Empty />
      <Line content={[{ t: "  ", c: "" }, { t: "ritual", c: "ember", b: true }, { t: g.h.repeat(2), c: "ember", dim: true }, { t: ` ${g.bullet} comandos destrutivos pedem um traço`, c: "ink-dim" }]} />
      <Empty />
      <Line content={[{ t: "  ", c: "" }, { t: "Você pediu: ", c: "ink-dim" }, { t: "rm -rf node_modules", c: "error", b: true }]} />
      <Empty />
      <Line content={[{ t: "  ", c: "" }, { t: "    Para confirmar, trace este sigilo no campo abaixo:", c: "ink" }]} />
      <Empty />
      <Line content={[{ t: "  ", c: "" }, { t: "                                                            ", c: "" }]} />
      <Line content={[{ t: "  ", c: "" }, { t: "                    ", c: "" }, { t: "╭───────╮", c: "ember" }]} />
      <Line content={[{ t: "  ", c: "" }, { t: "                    ", c: "" }, { t: "│   ", c: "ember" }, { t: "╱", c: "error", b: true }, { t: "   │", c: "ember" }]} />
      <Line content={[{ t: "  ", c: "" }, { t: "                    ", c: "" }, { t: "│  ", c: "ember" }, { t: "╱ ", c: "error", b: true }, { t: "│", c: "error" }, { t: "  │", c: "ember" }]} />
      <Line content={[{ t: "  ", c: "" }, { t: "                    ", c: "" }, { t: "│ ", c: "ember" }, { t: "╱──┴── ", c: "error", b: true }, { t: "│", c: "ember" }]} />
      <Line content={[{ t: "  ", c: "" }, { t: "                    ", c: "" }, { t: "╰───────╯", c: "ember" }]} />
      <Line content={[{ t: "  ", c: "" }, { t: "                                                            ", c: "" }]} />
      <Line content={[{ t: "  ", c: "" }, { t: "    digite: ", c: "ink-dim" }, { t: "destruir node_modules", c: "ember", b: true }, { t: "    para selar.", c: "ink-dim" }]} />
      <Empty />
      <Line content={[{ t: "  ", c: "" }, { t: "    ", c: "" }, { t: g.arrow + " ", c: "ember" }, { t: "destruir node_m", c: "ink" }, <span key="c" className="cursor">▍</span>]} />
      <Empty />
    </>
  );
}

// ─── NOVEL: PHANTOM COMPLETION (sugestão fantasma) ────────────────────────────
function PhantomScreen() {
  const g = useGlyphs();
  return (
    <>
      <Empty />
      <Line content={[{ t: "  ", c: "" }, { t: "phantom", c: "accent", b: true }, { t: g.h.repeat(2), c: "accent", dim: true }, { t: ` ${g.bullet} Nyx prevê. você confirma com tab.`, c: "ink-dim" }]} />
      <Empty />
      <Line content={[{ t: "  ", c: "" }, { t: g.arrow + " ", c: "ember" }, { t: "refator", c: "ink" }, { t: "a o parser e roda os testes", c: "muted", dim: true }, <span key="c" className="cursor">▍</span>]} />
      <Empty />
      <Line content={[{ t: "  ", c: "" }, { t: "      ", c: "" }, { t: "fantasma ", c: "ink-dim" }, { t: "calculada de:", c: "ink-dim" }]} />
      <Line content={[{ t: "  ", c: "" }, { t: "        ", c: "" }, { t: g.bullet, c: "muted" }, { t: " últimos 3 inputs do usuário", c: "ink-dim" }]} />
      <Line content={[{ t: "  ", c: "" }, { t: "        ", c: "" }, { t: g.bullet, c: "muted" }, { t: " contexto da branch (feat/parser-refactor)", c: "ink-dim" }]} />
      <Line content={[{ t: "  ", c: "" }, { t: "        ", c: "" }, { t: g.bullet, c: "muted" }, { t: " memórias de estilo (sempre roda testes)", c: "ink-dim" }]} />
      <Empty />
      <Line content={[{ t: "  ", c: "" }, { t: "   ", c: "" }, { t: "tab ", c: "ember", b: true }, { t: "aceita · ", c: "ink-dim" }, { t: "esc ", c: "ember", b: true }, { t: "ignora · ", c: "ink-dim" }, { t: "→ ", c: "ember", b: true }, { t: "aceita 1 palavra", c: "ink-dim" }]} />
      <Empty />
    </>
  );
}

Object.assign(window, {
  PanicScreen, DoctorScreen, SessionSummaryScreen, CompactionScreen,
  OnboardingScreen, TasksScreen, FooterScreen,
  ConstellationScreen, HeartbeatScreen, RitualScreen, PhantomScreen,
});
