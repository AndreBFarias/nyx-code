// =============================================================================
// SECTIONS — SCREENS (15+ telas mockadas, com ficha técnica ao lado)
// =============================================================================

const screensList = [
  {
    id: "boot",
    group: "fluxo principal",
    name: "Boot · Banner",
    tagline: "Primeira impressão da entidade.",
    Component: () => <BootScreen animated={false} />,
    height: 320,
    notes: {
      file: "nyx/agent/banner.py",
      composes: "build_banner() · _build_wide() · _build_compact()",
      idea: "Animação progressiva por linha (~250ms cada). Em modo compacto (cols<80), pula a animação. O accent respira (opacity cycle). Em arcano, partículas Braille caem dos cantos por 1.4s.",
      kpi: "Render completo em <600ms. Nunca bloqueia stdin.",
    },
  },
  {
    id: "loop",
    group: "fluxo principal",
    name: "Loop principal",
    tagline: "Você fala. Nyx pensa. Nyx age. Nyx responde.",
    Component: () => <LoopScreen />,
    height: 480,
    notes: {
      file: "nyx/agent/loop/_iteration.py · output.py:render_user_input/render_assistant_start",
      composes: "user box → assistant header → spinner → tool card → resposta",
      idea: "User echo numa box dedicada (já existe, ADR-024). Streaming de resposta acontece após '───'. Spinner Braille substitui-se in-place pela próxima linha do output. Tools renderizam em cards independentes ENTRE turnos de assistant.",
      kpi: "Time-to-first-token visível em <300ms. Cursor em ANSI hide/show pra não piscar durante stream.",
    },
  },
  {
    id: "toolcards",
    group: "fluxo principal",
    name: "Tool cards",
    tagline: "Cada tool é uma carta com começo, meio e fim.",
    Component: () => <ToolCardsScreen />,
    height: 540,
    notes: {
      file: "nyx/agent/output.py:render_tool_card_start/render_tool_card_end",
      composes: "header (nome+args+status+duração) → body lines → footer rule",
      idea: "Card abre com spinner ao executar e fecha com ok/erro + duração. Body line 1 = sumário (`620 linhas, 7 fallbacks`). Erros pintam border em error. Atalhos contextuais [Ctrl+D] aparecem no rodapé do card de edit_file.",
      kpi: "Cards <200ms vão direto ao end (sem flicker). Cards >200ms mostram start + spinner. Erro nunca passa sem 1 sugestão acionável.",
    },
  },
  {
    id: "diff",
    group: "inspeção & edição",
    name: "Diff viewer",
    tagline: "Mudança em arquivo, vista antes de aceita.",
    Component: () => <DiffScreen />,
    height: 580,
    notes: {
      file: "nyx/agent/output.py:render_diff · novo módulo diff_viewer.py",
      composes: "hunk header → linhas numeradas → atalhos [a]ceitar/[r]ejeitar/[e]ditar/[t]este",
      idea: "Cada hunk em sua própria seção. Linhas removidas em error, adicionadas em success. Linhas omitidas mostradas como `···` clicável (Tab abre). Atalho [t] roda os testes que tocam esse arquivo. [e] abre o $EDITOR pra edição manual antes do apply.",
      kpi: "Renderiza diff de 500 linhas em <80ms. Aceitar é write atômico (tmp + rename).",
    },
  },
  {
    id: "plan",
    group: "inspeção & edição",
    name: "Modo plano",
    tagline: "Pensa antes de mexer.",
    Component: () => <PlanModeScreen />,
    height: 540,
    notes: {
      file: "nyx/agent/commands/code.py · enter_plan_mode tool",
      composes: "header de modo (banda âmbar) → narrativa do plano → riscos → escolha [s/r/n]",
      idea: "Entrou no plan mode? Tools ficam READ-ONLY automaticamente. Só read/list/grep podem rodar. Quando o usuário aceita [s], muda pra modo execução e replay do plano. Plan mode é UM banner âmbar persistente no topo durante toda a fase.",
      kpi: "Loop continua respondendo. Plan tem timeout de 5min de inatividade — depois fecha sozinho preservando o plano em /tmp/.",
    },
  },
  {
    id: "permission",
    group: "inspeção & edição",
    name: "Permission prompt",
    tagline: "4 níveis: uma vez, sempre, bypass, não.",
    Component: () => <PermissionScreen />,
    height: 420,
    notes: {
      file: "nyx/agent/permissions.py · output.py:make_ask_permission",
      composes: "banda âmbar 'PERMISSÃO' → resumo da tool → 4 opções",
      idea: "Categoriza tool em 4 níveis: READ_ONLY (auto-aprovado) · WRITE (confirm_once) · EXEC (always_confirm) · DESTRUCTIVE (ritual). Bypass até /quit é guardado em runtime, NUNCA persistido. Atalho [b] mostra warning antes de ativar.",
      kpi: "Permission decision viaja em 1 tecla. Tempo do prompt = tempo de leitura do contexto, sem timeout.",
    },
  },
  {
    id: "help",
    group: "comandos",
    name: "/help",
    tagline: "47 comandos organizados em 7 categorias.",
    Component: () => <HelpScreen />,
    height: 480,
    notes: {
      file: "nyx/agent/commands/_registry.py · system.py:_help",
      composes: "header → 7 categorias compactas → atalhos teclado",
      idea: "Categorias herdadas do README. Cada linha é uma categoria inteira, lista compacta separada por `·`. Atalhos Ctrl+ ficam num bloco separado abaixo. Tab autocompleta categoria→comando→arg.",
      kpi: "Help completo em 1 viewport (24 linhas). Sem scroll. Sem paginação.",
    },
  },
  {
    id: "status",
    group: "comandos",
    name: "/status",
    tagline: "Telemetria com medidores HUD.",
    Component: () => <StatusScreen />,
    height: 500,
    notes: {
      file: "nyx/agent/commands/system.py:_status · novo: telemetry.py",
      composes: "barras horizontais com block elements + percentuais",
      idea: "3 medidores principais (VRAM, contexto, iter) com cores graduadas (success<70%, warning<90%, error). Tools count = histograma das últimas N. Latência p50/p95 via janela móvel. Atualiza ao vivo se /status --watch.",
      kpi: "Snapshot em <50ms. Watch mode atualiza a 2Hz, custa <2% CPU.",
    },
  },
  {
    id: "memory",
    group: "comandos",
    name: "/memory",
    tagline: "Memória persistente categorizada.",
    Component: () => <MemoryScreen />,
    height: 480,
    notes: {
      file: "nyx/agent/memory.py · commands/session.py",
      composes: "header → categorias com entradas + data → CRUD inline",
      idea: "Memórias agrupadas por arquivo (ambiente.md, estilo.md, decisões.md em ~/.nyx/memory/). Cada uma é uma linha + data ISO. /memory add detecta categoria automaticamente. /memory edit abre $EDITOR. Recall é semântico (top-k via embedding local).",
      kpi: "Recall em <20ms (cache em RAM). Persiste imediatamente após /memory add.",
    },
  },
  {
    id: "theme",
    group: "comandos",
    name: "/theme",
    tagline: "Trocar estético × entidade ao vivo.",
    Component: () => <ThemeSwitcherScreen />,
    height: 480,
    notes: {
      file: "nyx/themes/__init__.py · novo: commands/theme.py",
      composes: "seletor estético (5) → seletor entidade (7) → preview ao vivo",
      idea: "Tab navega; Enter aplica; Esc cancela. Trocas são hot-reload (re-render do banner + footer sem reiniciar loop). Persiste em ~/.nyx/config.toml. Atalho rápido: /theme cyber+luna.",
      kpi: "Apply em <100ms. Re-render preserva scroll e histórico.",
    },
  },
  {
    id: "footer",
    group: "estados especiais",
    name: "Footer bar",
    tagline: "Sempre visível, acima do prompt.",
    Component: () => <FooterScreen />,
    height: 180,
    notes: {
      file: "nyx/agent/output.py:render_footer",
      composes: "linha em dim accent: `── ctx X% · modelo · iter N · lidos · modif ──`",
      idea: "Largura responsiva (≥80, 60-79, <60). Atualiza a cada turn. Pisca em ember por 600ms quando compactação roda. Em scanline mode (cyber), tem suave overlay de noise.",
      kpi: "Render em <2ms. Não conta tokens duas vezes.",
    },
  },
  {
    id: "panic",
    group: "estados especiais",
    name: "Erro / panic",
    tagline: "Falha técnica, recuperação narrativa.",
    Component: () => <PanicScreen />,
    height: 450,
    notes: {
      file: "nyx/agent/output.py:print_error",
      composes: "banda vermelha 'falha' → erro → 3 sugestões → sussurro",
      idea: "Toda mensagem de erro inclui 1+ ações acionáveis. Sessão é AUTO-SALVA antes do panic. Última linha sempre é Nyx sussurrando em ink-dim. NYX_DEBUG=1 adiciona stack trace, mas só por opt-in.",
      kpi: "Panic → console em <500ms. Sessão recuperável 100% das vezes.",
    },
  },
  {
    id: "doctor",
    group: "estados especiais",
    name: "/doctor",
    tagline: "18 checagens em <1s.",
    Component: () => <DoctorScreen />,
    height: 580,
    notes: {
      file: "nyx/agent/services/diagnostics.py · commands/system.py:_doctor",
      composes: "3 seções (infra, hardware, projeto) → veredito final",
      idea: "Cada check tem 3 estados (ok=success, warn=warning, fail=error). Roda em paralelo (asyncio.gather). Veredito = AND de todos os críticos. Em fail crítico, sugere comando de recovery. /doctor --fix tenta auto-recovery.",
      kpi: "<1s pra suite completa. Async-friendly. Falhas isoladas — 1 timeout não bloqueia outros.",
    },
  },
  {
    id: "session",
    group: "estados especiais",
    name: "Sessão summary",
    tagline: "Card de fechamento da sessão.",
    Component: () => <SessionSummaryScreen />,
    height: 380,
    notes: {
      file: "nyx/agent/services/tool_use_summary.py · output.py:_render_session_summary",
      composes: "card largo com 6 linhas: objetivo, feito, diff, tokens, próximo",
      idea: "Auto-renderiza no /quit (depois do quote literário). Também em /summary. 'Objetivo' inferido do 1º turno. 'Feito' = lista de tools agrupadas. 'Próximo' = sugestão contextual (se tem mudanças, /commit; se passou nos testes, /pr).",
      kpi: "Render <30ms. Funde com /export -> markdown que vira PR description.",
    },
  },
  {
    id: "compaction",
    group: "estados especiais",
    name: "Auto-compactação",
    tagline: "Contexto respira antes de estourar.",
    Component: () => <CompactionScreen />,
    height: 320,
    notes: {
      file: "nyx/agent/services/compact.py · output.py:render_compaction_event",
      composes: "barras antes/depois → o que foi resumido → linha de Nyx",
      idea: "3 níveis (1=sumarizar tool calls antigas; 2=sumarizar turns inteiros; 3=last-resort de hard-trim). Dispara automaticamente em 80%, 90%, 95% do contexto. Mostra DELTA em barras pra dev sentir confiança. /compact --force força nível 2 a qualquer momento.",
      kpi: "Roda em <300ms, não interrompe geração. Preserva sempre os últimos 3 turns + diffs ativos + plano em curso.",
    },
  },
  {
    id: "onboarding",
    group: "estados especiais",
    name: "Onboarding · 1ª vez",
    tagline: "3 passos, então Nyx está em casa.",
    Component: () => <OnboardingScreen />,
    height: 430,
    notes: {
      file: "novo: nyx/onboarding.py · executado se ~/.nyx/config.toml não existe",
      composes: "1/3 modelo · 2/3 entidade · 3/3 nível de permissão",
      idea: "3 telas máximo. Cada uma é um seletor radio com 4 opções. Esc em qualquer ponto pula tudo (defaults). Resultado escrito em ~/.nyx/config.toml. Onboarding NUNCA mostra warning antes da primeira invocação real. Detecta GPU e ajusta a recomendação default em runtime.",
      kpi: "<30s pra dev impaciente. Esc imediato funciona com sane defaults.",
    },
  },
  {
    id: "tasks",
    group: "estados especiais",
    name: "Task queue",
    tagline: "Múltiplas tarefas em background.",
    Component: () => <TasksScreen />,
    height: 320,
    notes: {
      file: "nyx/agent/commands/_observability.py · novo: task_queue.py",
      composes: "header → linhas por task com spinner inline + status + duração",
      idea: "Tasks são tools long-running (test runs, builds, gauntlet) que rodam em paralelo. Cada task tem id T-NN, status (correndo/feito/falha/fila), output streamado. /tasks output T-01 mostra o stdout. Esc Esc interrompe a tarefa em foco.",
      kpi: "Até 4 tasks concorrentes default (configurável). VRAM compartilhada via semáforo. Auto-promote pra foco se só 1 ativa.",
    },
  },
];

// ─── SCREEN CARD ──────────────────────────────────────────────────────────────
function ScreenCard({ screen, aesthetic, entity }) {
  return (
    <div style={{
      display: "grid",
      gridTemplateColumns: "1fr 380px",
      gap: 48,
      padding: "48px 0",
      borderBottom: "1px solid rgba(157, 78, 221, 0.1)",
      alignItems: "start",
    }}>
      <div>
        <div style={{
          display: "flex",
          alignItems: "baseline",
          justifyContent: "space-between",
          marginBottom: 20,
        }}>
          <div>
            <p className="kicker" style={{ color: "#7a6e90" }}>{screen.group}</p>
            <h3 style={{
              fontFamily: "'Cormorant Garamond', serif",
              fontSize: 38,
              fontWeight: 400,
              color: "#f0e8d8",
              marginTop: 6,
            }}>{screen.name}</h3>
          </div>
          <span className="kicker">id · {screen.id}</span>
        </div>
        <p style={{
          fontFamily: "'Cormorant Garamond', serif",
          fontStyle: "italic",
          fontSize: 20,
          color: "#c4b8d4",
          marginBottom: 24,
          maxWidth: "50ch",
        }}>{screen.tagline}</p>

        <ThemeProvider aesthetic={aesthetic} entity={entity}>
          <Terminal height={screen.height}>
            <screen.Component />
          </Terminal>
        </ThemeProvider>
      </div>

      <div className="spec" style={{ position: "sticky", top: 88 }}>
        <div className="spec-head">
          <div>
            <div className="spec-name">ficha técnica</div>
            <div className="spec-id">screen-{screen.id}</div>
          </div>
        </div>

        <div className="spec-block">
          <div className="spec-block-label">arquivo</div>
          <div className="spec-block-body">
            <code>{screen.notes.file}</code>
          </div>
        </div>

        <div className="spec-block">
          <div className="spec-block-label">composição</div>
          <div className="spec-block-body">{screen.notes.composes}</div>
        </div>

        <div className="spec-block">
          <div className="spec-block-label">como programar</div>
          <div className="spec-block-body">{screen.notes.idea}</div>
        </div>

        <div className="spec-block">
          <div className="spec-block-label">KPI</div>
          <div className="spec-block-body" style={{ color: "#7dd3a0" }}>{screen.notes.kpi}</div>
        </div>
      </div>
    </div>
  );
}

// ─── SCREENS SECTION (com mini theme picker no header) ────────────────────────
function ScreensSection({ aesthetic, entity, setAesthetic, setEntity }) {
  return (
    <section className="section bg-tone-2" data-screen-label="07 As Telas">
      <div className="section-inner">
        <div className="section-head">
          <div className="ttl">
            <div className="h-eyebrow">
              <span>VI.</span>
              <span>Quinze telas mockadas</span>
            </div>
            <h2 className="h-sub">
              Cada tela.<br />
              Cada estado.<br />
              <em style={{ fontStyle: "italic", color: "#9D4EDD" }}>Cada ficha técnica.</em>
            </h2>
            <div className="spacer-md" />
            <p className="lede">
              Todas as telas abaixo respeitam o tema atual (estético + entidade).
              Use o painel <strong style={{ color: "#f0e8d8" }}>tweaks</strong> no canto
              inferior direito pra trocar tudo ao vivo. Ao lado de cada mockup, a
              ficha técnica: arquivo no repo, composição, ideia de implementação, KPI.
            </p>
          </div>
          <div className="meta" style={{ textAlign: "right" }}>
            <p className="kicker" style={{ marginBottom: 12 }}>
              tema atual: <strong style={{ color: window.NYX_ENTITIES[entity].accent }}>{aesthetic}+{entity}</strong>
            </p>
            <div style={{
              display: "flex",
              flexDirection: "column",
              alignItems: "flex-end",
              gap: 6,
              fontFamily: "'JetBrains Mono', monospace",
              fontSize: 11,
              color: "#9c8fb0",
            }}>
              <span>{screensList.length} telas</span>
              <span>{new Set(screensList.map(s => s.group)).size} grupos</span>
            </div>
          </div>
        </div>

        <div>
          {screensList.map((s) => (
            <ScreenCard key={s.id} screen={s} aesthetic={aesthetic} entity={entity} />
          ))}
        </div>
      </div>
    </section>
  );
}

Object.assign(window, { ScreensSection });
