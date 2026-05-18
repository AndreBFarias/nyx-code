// =============================================================================
// SECTIONS — FEATURES · NOVEL · ROADMAP
// =============================================================================

// ─── FEATURE SPECS (fichas técnicas além das telas) ───────────────────────────
const featureSpecs = [
  {
    id: "FEAT-01",
    name: "Streaming com cursor managed",
    why: "Streaming sem hide-cursor pisca a barra. Spinner sobre o stream gera lixo visual.",
    how: "Antes do stream: `\\033[?25l` (hide). No fim ou em exception: `\\033[?25h` (show), garantido em try/finally. Spinner usa `\\r\\x1b[2K` pra limpar a linha antes do próximo token chegar.",
    files: "agent/output.py:NyxSpinner · agent/loop/_iteration.py",
    risk: "Crash no meio do stream com cursor escondido = usuário cego. Mitigação: signal handler SIGINT/SIGTERM restaura o cursor.",
  },
  {
    id: "FEAT-02",
    name: "Parser de 7 fallbacks → dispatch table",
    why: "7 if/elif paralelos em parser.py é técnica dívida sentada. Cobertura é dolorosa.",
    how: "`dispatch_table: dict[ParseLevel, Callable[[str], ParsedAction | None]]`. Tenta na ordem; primeira que retorna não-None vence. Cada nível vira função pura testável isoladamente.",
    files: "agent/parser.py",
    risk: "Mudar ordem quebra contratos sutis. Mitigação: snapshot tests com fixtures reais do gauntlet.",
  },
  {
    id: "FEAT-03",
    name: "Tab autocomplete contextual",
    why: "47 comandos + 34 tools + arquivos do projeto. Memorizar tudo é fricção.",
    how: "Em prompt-toolkit, registra um único Completer que despacha por contexto: depois de `/` → slash commands; depois de espaço em /memory → fatos persistidos; argumento de read_file → glob de arquivos; depois de @ → file ref.",
    files: "agent/completer.py",
    risk: "Completer lento bloqueia o prompt. Mitigação: indexar arquivos em background, cache invalidado por fsnotify.",
  },
  {
    id: "FEAT-04",
    name: "Memória persistente com recall semântico",
    why: "Memórias planas viram lista enorme. Procurar com /grep é antiquado.",
    how: "Cada fato armazenado em arquivo markdown por categoria. Embedding local com `all-MiniLM-L6-v2` (CPU, 80MB). Recall = top-k cosine. System prompt recebe os top-3 da query atual, não a lista inteira.",
    files: "agent/memory.py · novo: services/embeddings.py",
    risk: "Modelo de embedding = +80MB de dep. Mitigação: download lazy; flag `--no-recall` desativa.",
  },
  {
    id: "FEAT-05",
    name: "Permission engine de 4 níveis",
    why: "Tools destrutivas precisam de confirmação ritual. Tools só-leitura não.",
    how: "Cada tool declara seu `permission_level` na registry: READ (auto-aprovada), WRITE (confirm_once), EXEC (always_confirm), DESTRUCTIVE (ritual). Bypass até /quit é state em memória, NUNCA escrito em disco. /permissions abre matriz pra revisar.",
    files: "agent/permissions.py · tools/base.py:ToolDef",
    risk: "Esquecer de marcar uma nova tool = default WRITE. Mitigação: registry valida na boot.",
  },
  {
    id: "FEAT-06",
    name: "Hot-reload de temas sem reset",
    why: "Trocar tema pra ver outro estético sem perder a sessão.",
    how: "Tema = singleton com observers. /theme troca → notifica banner, footer, prompt_style. Re-renderiza somente componentes visíveis. Histórico do REPL recolora linhas vivas; linhas antigas mantêm cor (snapshot).",
    files: "themes/__init__.py · novo: agent/runtime_theme.py",
    risk: "Linhas antigas com cores misturadas confundem leitura. Mitigação: separador horizontal automático ao trocar tema.",
  },
  {
    id: "FEAT-07",
    name: "Auto-compactação em 3 níveis",
    why: "Janela de contexto qwen3 = 32k. Sessão longa estoura.",
    how: "Disparo: 80% → nível 1 (sumariza tool calls antigas). 90% → nível 2 (sumariza turns inteiros mantendo últimos 3). 95% → nível 3 (hard-trim, registra perda). Sumarização local via qwen3:1.5b dedicado.",
    files: "services/compact.py · agent/context.py",
    risk: "Sumário ruim perde info importante. Mitigação: sempre preservar diffs ativos + plano + últimos 3 turns sem sumarizar.",
  },
  {
    id: "FEAT-08",
    name: "Persistência de sessão recuperável",
    why: "Crash, kill, reboot — usuário não pode perder contexto.",
    how: "`~/.nyx/sessions/<id>/` contém: messages.jsonl (append-only), state.toml (config + flags), diffs/ (aplicados), notes.md (memórias da sessão). /resume <id> ressincroniza estado. Auto-save após cada turn.",
    files: "agent/persistence.py · agent/session.py",
    risk: "JSONL corrompido por kill no meio da escrita. Mitigação: escrita atômica (tmp + rename), validação na carga.",
  },
  {
    id: "FEAT-09",
    name: "Plan mode com tools read-only enforced",
    why: "Em plan mode, AI não deve poder editar — só pensar.",
    how: "Flag `plan_mode_active` no AgentLoop. Toda tool checa `if plan_mode and self.permission_level != READ: raise PlanModeViolation`. Banner âmbar persistente no topo. Tools tentadas e bloqueadas viram notas no plano.",
    files: "agent/loop/_iteration.py · agent/permissions.py",
    risk: "Tool nova não respeita o flag. Mitigação: assertion central, não decoradores opcionais.",
  },
  {
    id: "FEAT-10",
    name: "Tool timeout + cancellation",
    why: "Tool travada bloqueia o loop pra sempre. Esc Esc deve matar tudo limpo.",
    how: "Cada tool roda em `asyncio.Task` com timeout configurável (default 30s, run_command 120s). 2x Esc envia CancelledError. Tools devem ter cleanup em `__aexit__`. Bloqueadas que não respondem cancellation são SIGKILL após mais 3s.",
    files: "tools/base.py · agent/loop/_core.py",
    risk: "Tool sem cleanup deixa subprocess órfão. Mitigação: process groups + killpg em SIGKILL.",
  },
  {
    id: "FEAT-11",
    name: "ASCII fallback engine",
    why: "Terminais antigos (LANG=C, ssh sem -t, screen em alguns hosts) não suportam UTF-8.",
    how: "Boot detecta `LC_ALL+LANG` upcase contendo 'UTF-8'/'UTF8'. Se ausente, troca tabelas: BOX_CHARS → ASCII (+, -, |, /, \\); BULLETS → text; SPINNER → |/-\\. Todo lugar que renderiza pega de `glyphs_for_locale()`.",
    files: "themes/design_tokens.py · novo: themes/locale_detect.py",
    risk: "Detecção errada deixa interface feia. Mitigação: env override NYX_FORCE_UTF8=1.",
  },
  {
    id: "FEAT-12",
    name: "Headless JSON (Luna integration)",
    why: "Nyx tem que ser embedável em outras CLIs (Luna).",
    how: "Flag `--headless` substitui o REPL por loop JSONL: stdin recebe `{messages: [...], options: {...}}`, stdout emite `{type: 'token'|'tool_call'|'final'|'error', ...}`. Zero ANSI. Tools rodam igual; só a renderização muda.",
    files: "cli.py · novo: agent/headless.py",
    risk: "Drift entre headless e REPL. Mitigação: shared core (AgentLoop), só renderer difere.",
  },
];

function FeaturesSection() {
  return (
    <section className="section bg-tone-1" data-screen-label="08 Fichas de Feature">
      <div className="section-inner">
        <div className="section-head">
          <div className="ttl">
            <div className="h-eyebrow">
              <span>VII.</span>
              <span>Fichas técnicas — features estruturais</span>
            </div>
            <h2 className="h-sub">
              Tudo o que sustenta<br />
              <em style={{ fontStyle: "italic", color: "#9D4EDD" }}>as telas</em>.
            </h2>
            <div className="spacer-md" />
            <p className="lede">
              Doze fichas além das telas — features de infra, parsing, persistência,
              concorrência. Cada uma com <strong style={{ color: "#f0e8d8" }}>por que</strong>,{" "}
              <strong style={{ color: "#f0e8d8" }}>como</strong>, e{" "}
              <strong style={{ color: "#f0e8d8" }}>risco</strong>.
            </p>
          </div>
          <div className="meta">
            <p className="kicker">12 fichas · 6 sprints</p>
          </div>
        </div>

        <div className="grid-2" style={{ gap: 28 }}>
          {featureSpecs.map((f) => (
            <div key={f.id} className="spec">
              <div className="spec-head">
                <div>
                  <div className="spec-name">{f.name}</div>
                  <div className="spec-id">{f.id}</div>
                </div>
              </div>
              <div className="spec-block">
                <div className="spec-block-label">por que</div>
                <div className="spec-block-body">{f.why}</div>
              </div>
              <div className="spec-block">
                <div className="spec-block-label">como</div>
                <div className="spec-block-body">{f.how}</div>
              </div>
              <div className="spec-block">
                <div className="spec-block-label">arquivos</div>
                <div className="spec-block-body">
                  <code>{f.files}</code>
                </div>
              </div>
              <div className="spec-block">
                <div className="spec-block-label">risco</div>
                <div className="spec-block-body" style={{ color: "#FFB454" }}>{f.risk}</div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}

// ─── NOVEL FEATURES (surprise) ────────────────────────────────────────────────
function NovelSection({ aesthetic, entity }) {
  const novels = [
    {
      id: "NOV-01",
      name: "Constelação da sessão",
      Component: () => <ConstellationScreen />,
      height: 360,
      tagline: "Cada tool é um nó. Cada dependência inferida, uma aresta.",
      idea: "/constellation desenha um grafo ASCII ao vivo da sessão. Tools com mesmo arquivo de saída/entrada são conectadas. Ajuda a explicar pro dev o que aconteceu nas últimas N iterações. Nodes coloridos por categoria (leitura/edição/execução/memória). Em arcano vira mapa estelar com pontos Braille; em mecha vira diagrama de fluxo HUD.",
    },
    {
      id: "NOV-02",
      name: "Heartbeat ambiente",
      Component: () => <HeartbeatScreen />,
      height: 280,
      tagline: "Pulso do modelo no canto, sempre vivo.",
      idea: "Sparkline Braille no canto superior direito da TUI inteira. Quando pausada, pulso lento (3s/batida). Quando gerando, acelera com tps real. Quando tps cai abaixo de 20, fica vermelho avisando que algo está travando (VRAM swap, throttling térmico). Custa <0.5% CPU.",
    },
    {
      id: "NOV-03",
      name: "Ritual para destrutivo",
      Component: () => <RitualScreen />,
      height: 420,
      tagline: "Comandos irreversíveis pedem cerimônia.",
      idea: "rm -rf, git push --force, drop table, etc. detectam-se via regex de heurísticas + ML local. Em vez de [s/n], Nyx pede pro dev digitar uma frase composta (`destruir node_modules`). Não é fricção arbitrária — é forçar a consciência do que está prestes a fazer. Configurável: /permissions ritual off pra usuários experientes.",
    },
    {
      id: "NOV-04",
      name: "Phantom completion",
      Component: () => <PhantomScreen />,
      height: 300,
      tagline: "Nyx prevê. Você confirma com Tab.",
      idea: "Enquanto o dev digita, Nyx propõe continuação em ink-muted ao lado do cursor. Calculada por modelo leve (qwen3:1.5b) usando: últimos 3 inputs + branch atual + memórias de estilo. Tab aceita tudo, → aceita uma palavra, Esc descarta. Roda em background sem bloquear digitação.",
    },
    {
      id: "NOV-05",
      name: "Trilha de arquivos (fading)",
      Component: ({ aesthetic }) => null, // mocked below
      height: 200,
      tagline: "Cada arquivo tocado deixa um rastro Braille.",
      idea: "Painel pequeno no canto superior esquerdo lista os últimos 5 arquivos lidos/escritos. Cada um aparece em opacidade 1.0 quando tocado, depois decai linearmente até 0 em 12s. Sumiu = não esquece, mas não polui. Ctrl+F1 abre lista completa da sessão.",
    },
    {
      id: "NOV-06",
      name: "Marginalia · sussurros",
      Component: ({ aesthetic }) => null,
      height: 200,
      tagline: "Dicas em itálico que se apagam sozinhas.",
      idea: "Quando Nyx sente que o dev poderia se beneficiar de um truque (`tip: /rewind 2 desfaz os últimos 2 turnos`), aparece na MARGEM DIREITA em ink-muted itálico, sem som de notificação. Apaga sozinho em 8s. Não interrompe. Não pisca. Marginália respeitosa, como num livro.",
    },
    {
      id: "NOV-07",
      name: "Echo decay (histórico vivo)",
      Component: ({ aesthetic }) => null,
      height: 200,
      tagline: "Turnos antigos literalmente desbotam.",
      idea: "Mensagens antigas (>30 turns atrás) recebem opacity gradual (1.0 → 0.55) baseada em recência. Você ainda lê tudo se rolar, mas o foco visual fica nos turnos vivos. Quando uma compactação acontece, a transição é animada (fade-out dos turns sumarizados, fade-in do resumo).",
    },
    {
      id: "NOV-08",
      name: "Pulse on done",
      Component: ({ aesthetic }) => null,
      height: 200,
      tagline: "Quando termina, o terminal exala.",
      idea: "Após `done()` ser chamado por Nyx, o border do terminal pulsa 1x em success (verde sutil) por 600ms. Confirmação não-textual de que o turn fechou — você pode olhar pro IDE, voltar e ver pelo halo se já acabou. Em arcano, o glow brilha forte; em mecha, vira flash âmbar; em brutalist, nada (é silencioso por design).",
    },
  ];

  return (
    <section className="section bg-tone-3" data-screen-label="09 Novel features">
      <div className="section-inner">
        <div className="section-head">
          <div className="ttl">
            <div className="h-eyebrow">
              <span>VIII.</span>
              <span>Surpresas</span>
            </div>
            <h2 className="h-sub">
              Oito ideias<br />
              que ainda<br />
              <em style={{ fontStyle: "italic", color: "#9D4EDD" }}>não existem</em>.
            </h2>
            <div className="spacer-md" />
            <p className="lede">
              Coisas que pensaram até nisso. Nenhuma é necessária. Todas
              transformam um terminal em uma <strong style={{ color: "#f0e8d8" }}>presença</strong>.
              Quatro delas têm mockup ao vivo abaixo (as outras quatro são descritas em texto).
            </p>
          </div>
          <div className="meta">
            <p className="kicker">8 features · 4 mockadas · 4 conceituais</p>
          </div>
        </div>

        <div style={{ display: "flex", flexDirection: "column", gap: 0 }}>
          {novels.slice(0, 4).map((n) => (
            <div key={n.id} style={{
              display: "grid",
              gridTemplateColumns: "1fr 380px",
              gap: 48,
              padding: "48px 0",
              borderBottom: "1px solid rgba(157, 78, 221, 0.1)",
              alignItems: "start",
            }}>
              <div>
                <div style={{ display: "flex", alignItems: "baseline", justifyContent: "space-between", marginBottom: 16 }}>
                  <h3 style={{
                    fontFamily: "'Cormorant Garamond', serif",
                    fontSize: 36,
                    fontWeight: 400,
                    color: "#f0e8d8",
                  }}>{n.name}</h3>
                  <span className="kicker">{n.id}</span>
                </div>
                <p style={{
                  fontFamily: "'Cormorant Garamond', serif",
                  fontStyle: "italic",
                  fontSize: 19,
                  color: "#c4b8d4",
                  marginBottom: 24,
                  maxWidth: "55ch",
                }}>{n.tagline}</p>
                <ThemeProvider aesthetic={aesthetic} entity={entity}>
                  <Terminal height={n.height}>
                    <n.Component aesthetic={aesthetic} />
                  </Terminal>
                </ThemeProvider>
              </div>
              <div className="spec" style={{ position: "sticky", top: 88 }}>
                <div className="spec-head">
                  <div>
                    <div className="spec-name">conceito</div>
                    <div className="spec-id">{n.id}</div>
                  </div>
                  <span className="badge badge-ember">novel</span>
                </div>
                <div className="spec-block">
                  <div className="spec-block-body" style={{ color: "#c4b8d4" }}>{n.idea}</div>
                </div>
              </div>
            </div>
          ))}
        </div>

        <div className="spacer-lg" />

        <h3 style={{
          fontFamily: "'Cormorant Garamond', serif",
          fontStyle: "italic",
          fontSize: 32,
          fontWeight: 400,
          color: "#9D4EDD",
          marginBottom: 32,
        }}>+ quatro conceituais</h3>

        <div className="grid-2" style={{ gap: 28 }}>
          {novels.slice(4).map((n) => (
            <div key={n.id} className="card">
              <div style={{ display: "flex", alignItems: "baseline", justifyContent: "space-between", marginBottom: 8 }}>
                <h4 className="card-title">{n.name}</h4>
                <span className="kicker">{n.id}</span>
              </div>
              <p className="card-tagline" style={{ fontStyle: "italic", fontFamily: "'Cormorant Garamond', serif", fontSize: 16, color: "#c4b8d4", textTransform: "none", letterSpacing: 0 }}>
                {n.tagline}
              </p>
              <p style={{ fontSize: 14, color: "#a89cbc", lineHeight: 1.6 }}>{n.idea}</p>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}

// ─── ROADMAP / SPRINTS ────────────────────────────────────────────────────────
function RoadmapSection() {
  const sprints = [
    {
      num: "01",
      name: "Fundações tipográficas",
      goal: "Sair do CLI cinza pro CLI vivo.",
      items: [
        "Design tokens (5 estéticos × 7 entidades) em themes/",
        "ASCII fallback detection (locale_detect.py)",
        "Spinner Braille refatorado + cursor management",
        "Footer bar responsivo (3 modos)",
        "Box drawing primitives reutilizáveis",
      ],
      kpi: "Mesmo banner; 5 vezes mais bonito.",
    },
    {
      num: "02",
      name: "Tool cards + diff",
      goal: "Cada ação tem ritual e prova.",
      items: [
        "render_tool_card_start/end com timing real",
        "Diff viewer com atalhos [a/r/e/t]",
        "Permission engine de 4 níveis",
        "Tool timeout + Esc Esc kill",
        "Streaming sem flicker (cursor hide/show)",
      ],
      kpi: "Diff de 500 linhas renderiza em <80ms.",
    },
    {
      num: "03",
      name: "Diagnóstico + Plan",
      goal: "Confiança técnica + segurança humana.",
      items: [
        "/doctor com 18 checagens paralelas",
        "/status com gauges HUD ao vivo",
        "Plan mode com tools read-only enforced",
        "Permission matrix em /permissions",
        "Banner âmbar persistente em plan mode",
      ],
      kpi: "/doctor completo em <1s. 0 falso positivo.",
    },
    {
      num: "04",
      name: "Memória + Sessão",
      goal: "Nyx que lembra. Sessão que sobrevive.",
      items: [
        "Memória semântica (qwen3 + MiniLM)",
        "/resume com replay incremental",
        "Auto-compactação em 3 níveis",
        "Quote literário no /quit",
        "/export markdown → PR description",
      ],
      kpi: "Crash → /resume traz contexto inteiro.",
    },
    {
      num: "05",
      name: "Onboarding + Temas live",
      goal: "Primeira vez = paixão. Trocar tema = ato.",
      items: [
        "Onboarding 3 passos em ~/.nyx/config.toml",
        "Hot-reload de temas (5×7 combinações)",
        "/theme com preview ao vivo",
        "Tasks queue com até 4 paralelas",
        "Headless mode (--headless JSONL)",
      ],
      kpi: "Onboarding <30s. Tema swap <100ms.",
    },
    {
      num: "06",
      name: "Novel + polish",
      goal: "O que os outros terminais não têm.",
      items: [
        "Heartbeat sparkline ambiente",
        "Constelação da sessão (/constellation)",
        "Phantom completion (qwen3:1.5b)",
        "Ritual mode pra destrutivos",
        "Trilha de arquivos fading + marginalia",
      ],
      kpi: "GitHub:  500 em 2 semanas pós-release.",
    },
  ];

  return (
    <section className="section bg-tone-2" data-screen-label="10 Roadmap">
      <div className="section-inner">
        <div className="section-head">
          <div className="ttl">
            <div className="h-eyebrow">
              <span>IX.</span>
              <span>Caminho proposto</span>
            </div>
            <h2 className="h-sub">
              Seis sprints<br />
              até <em style={{ fontStyle: "italic", color: "#9D4EDD" }}>v1.0</em>.
            </h2>
            <div className="spacer-md" />
            <p className="lede">
              Cada sprint é um arco emocional do dev — fundação, ação,
              confiança, persistência, identidade, surpresa. Cada um termina
              com um KPI mensurável. Estimativa: 1-2 semanas por sprint solo,
              ou ~3 semanas total com 2-3 contribuidores em paralelo.
            </p>
          </div>
          <div className="meta">
            <p className="kicker">6 sprints · 30 entregáveis</p>
          </div>
        </div>

        <div className="stack" style={{ gap: 40 }}>
          {sprints.map((s, i) => (
            <div
              key={s.num}
              style={{
                display: "grid",
                gridTemplateColumns: "120px 1fr 320px",
                gap: 48,
                padding: "32px 0",
                borderTop: "1px solid rgba(157,78,221,0.15)",
                alignItems: "start",
              }}
            >
              <div>
                <div style={{
                  fontFamily: "'Cormorant Garamond', serif",
                  fontSize: 84,
                  fontWeight: 300,
                  color: "#9D4EDD",
                  lineHeight: 0.9,
                }}>{s.num}</div>
                <p className="kicker" style={{ marginTop: 4 }}>sprint</p>
              </div>
              <div>
                <h3 style={{
                  fontFamily: "'Cormorant Garamond', serif",
                  fontSize: 36,
                  fontWeight: 400,
                  color: "#f0e8d8",
                  marginBottom: 8,
                }}>{s.name}</h3>
                <p style={{
                  fontFamily: "'Cormorant Garamond', serif",
                  fontStyle: "italic",
                  fontSize: 20,
                  color: "#c4b8d4",
                  marginBottom: 24,
                }}>{s.goal}</p>
                <ul style={{ listStyle: "none", padding: 0 }}>
                  {s.items.map((it, j) => (
                    <li key={j} style={{
                      display: "flex",
                      alignItems: "baseline",
                      gap: 12,
                      padding: "8px 0",
                      borderBottom: j < s.items.length - 1 ? "1px dashed rgba(157,78,221,0.1)" : "none",
                      fontSize: 15,
                      color: "#c4b8d4",
                      fontFamily: "'JetBrains Mono', monospace",
                    }}>
                      <span style={{ color: "#9D4EDD" }}>·</span>
                      <span>{it}</span>
                    </li>
                  ))}
                </ul>
              </div>
              <div style={{ paddingTop: 24 }}>
                <p className="kicker" style={{ color: "#7dd3a0", marginBottom: 8 }}>KPI</p>
                <p style={{
                  fontFamily: "'Cormorant Garamond', serif",
                  fontStyle: "italic",
                  fontSize: 18,
                  color: "#7dd3a0",
                  lineHeight: 1.4,
                }}>{s.kpi}</p>
              </div>
            </div>
          ))}
        </div>

        <div className="spacer-xl" />

        <div style={{
          padding: "48px 56px",
          background: "linear-gradient(135deg, rgba(157,78,221,0.08), rgba(255,180,84,0.03))",
          borderRadius: 8,
          border: "1px solid rgba(157,78,221,0.2)",
          textAlign: "center",
        }}>
          <p className="kicker" style={{ marginBottom: 16 }}>v1.0 — o que precisamos sentir</p>
          <p style={{
            fontFamily: "'Cormorant Garamond', serif",
            fontStyle: "italic",
            fontSize: 28,
            color: "#f0e8d8",
            lineHeight: 1.4,
            maxWidth: 760,
            margin: "0 auto",
          }}>
            "Alguém abre o Nyx Code pela primeira vez e pensa,<br />
            <em style={{ color: "#9D4EDD" }}>cara, foi um game designer que fez isso?</em>"
          </p>
        </div>
      </div>
    </section>
  );
}

Object.assign(window, { FeaturesSection, NovelSection, RoadmapSection });
