// =============================================================================
// SECTION — WORKFLOW DO DEV
// Sequência narrativa de um dia típico: boas-vindas → neofetch → sessão real
// → multi-tab → sprints → multi-agent → bypass → telemetria de custo
// =============================================================================

const workflowSteps = [
  {
    id: "wf-01",
    name: "Boas-vindas",
    moment: "00:00 · primeira vez",
    Component: () => <WelcomeScreen />,
    height: 380,
    narrative:
      "Antes de qualquer pergunta técnica, Nyx se apresenta. Tom calmo, sem checklist. " +
      "Três linhas curtas + três escolhas no rodapé. Pode pular tudo. " +
      "É uma boas-vindas, não um questionário.",
    files: "nyx/welcome.py · roda 1× quando ~/.nyx/config.toml não existe",
  },
  {
    id: "wf-02",
    name: "Boot completo · estilo neofetch",
    moment: "00:30 · segunda vez em diante",
    Component: () => <NeofetchBootScreen />,
    height: 540,
    narrative:
      "Toda execução do nyx começa com este banner. ASCII art próprio (Block Elements " +
      "+ Braille, fora da faixa de emoji). System info no estilo neofetch: SO, kernel, " +
      "uptime, GPU/VRAM, memória. Paleta visível embaixo confirma o tema atual. " +
      "Em <500ms você sabe que está em casa.",
    files: "nyx/agent/banner.py:build_neofetch_banner · nyx/themes/ascii_art.py",
  },
  {
    id: "wf-03",
    name: "Sessão de coding real",
    moment: "09:42 · você tem um bug",
    Component: () => <CodingSessionScreen />,
    height: 900,
    narrative:
      "Você descreve o bug. Nyx pesquisa (grep), confirma (read), aplica fix (edit), " +
      "escreve testes (write), roda (run_command), confirma sucesso e oferece commit. " +
      "Cinco tools, sete linhas de você, três minutos. O footer mostra ctx + iter " +
      "atualizando em tempo real. Esse é o loop principal — sem cerimônia.",
    files: "agent/loop/_iteration.py · agent/output.py · agent/commands/git_cmds.py",
  },
  {
    id: "wf-04",
    name: "Múltiplas tabs · sessões nomeadas",
    moment: "10:15 · você abre outra coisa",
    Component: () => <MultiTabScreen />,
    height: 500,
    narrative:
      "Toda sessão tem um nome (gerado dos primeiros 4 turns, ou definido por " +
      "/session rename). Ctrl+Tab alterna entre elas. As tabs inativas continuam " +
      "vivas em background — Nyx pode ter agentes rodando lá dentro mesmo sem você " +
      "estar olhando. Estado completo persistido em ~/.nyx/sessions/.",
    files: "nyx/agent/session.py · novo: agent/tab_manager.py · commands/session.py",
  },
  {
    id: "wf-05",
    name: "Sprint tracker · trabalho em ondas",
    moment: "10:42 · refundação rolando",
    Component: () => <SprintTrackerScreen />,
    height: 880,
    narrative:
      "Quando o trabalho é grande, Nyx organiza em ondas (sprints). Cada onda lança " +
      "agentes paralelos. A tabela mostra status + hash do commit. O bloco 'Insight' " +
      "é renderizado quando Nyx detecta um padrão importante (ex: nomenclatura conceitual " +
      "que não existia no codebase). O 'recap' é gerado entre ondas — narrativa curta " +
      "de onde está, o que vem.",
    files: "novo: agent/orchestrator/wave.py · services/insight.py · services/recap.py",
  },
  {
    id: "wf-06",
    name: "Agentes paralelos",
    moment: "10:43 · 4 em paralelo",
    Component: () => <MultiAgentScreen />,
    height: 580,
    narrative:
      "Árvore visível: supervisor (você) → sub-agentes (uuid abreviado + sprint). " +
      "Cada agente roda em worktree git isolada — não pisa no de ninguém. VRAM é " +
      "compartilhada via semáforo (max 3 modelos ao mesmo tempo na 3050). Saída " +
      "agregada por id no painel inferior. /agents stop <id> termina um; esc esc " +
      "interrompe todos.",
    files: "novo: agent/orchestrator/dispatcher.py · agent/orchestrator/worktree.py",
  },
  {
    id: "wf-07",
    name: "Modo bypass",
    moment: "11:30 · você confia",
    Component: () => <BypassModeScreen />,
    height: 520,
    narrative:
      "Para sessões intensas, você ativa bypass: Nyx para de pedir permissão " +
      "antes de cada tool. CONTINUA pedindo ritual para destrutivos (rm -rf, " +
      "git push --force) — bypass não anula o ritual, anula só o confirm_once. " +
      "Indicador permanente no footer enquanto ativo. Termina em /quit ou shift+tab.",
    files: "agent/permissions.py:bypass_state · output.py:render_footer (indicador)",
  },
  {
    id: "wf-08",
    name: "Telemetria de custo",
    moment: "12:08 · você fecha sessão",
    Component: () => <CostTelemetryScreen />,
    height: 520,
    narrative:
      "Antes do quote literário de despedida, este painel: quanto você gastou rodando " +
      "local (= zero, exceto eletricidade) versus quanto teria gasto se fosse Claude " +
      "Sonnet ou GPT-4o. Não é vaidade — é prova de valor pra quem está pensando em " +
      "trocar de assinatura. Acumula por dia.",
    files: "novo: agent/services/cost_estimator.py · commands/session.py:_quit",
  },
];

function WorkflowSection({ aesthetic, entity }) {
  return (
    <section className="section bg-tone-3" data-screen-label="11 Workflow do dev">
      <div className="section-inner">
        <div className="section-head">
          <div className="ttl">
            <div className="h-eyebrow">
              <span>X.</span>
              <span>Workflow real do dev</span>
            </div>
            <h2 className="h-sub">
              Um dia<br />
              dentro<br />
              do <em style={{ fontStyle: "italic", color: "#9D4EDD" }}>terminal</em>.
            </h2>
            <div className="spacer-md" />
            <p className="lede">
              As telas anteriores são estados isolados — utilíssimas pra ficha técnica.
              Aqui é diferente: <strong style={{ color: "#f0e8d8" }}>uma narrativa contínua</strong>{" "}
              que mostra como tudo se conecta. Você abre o terminal de manhã,
              tem um bug, abre uma segunda tab pra outro projeto, despacha agentes
              paralelos, ativa bypass, fecha a sessão à hora do almoço.
              Oito telas. Um dia.
            </p>
          </div>
          <div className="meta" style={{ textAlign: "right" }}>
            <p className="kicker" style={{ marginBottom: 12 }}>
              tema atual: <strong style={{ color: window.NYX_ENTITIES[entity].accent }}>{aesthetic}+{entity}</strong>
            </p>
            <p className="kicker">8 telas · 1 dia · 12h08</p>
          </div>
        </div>

        {/* timeline vertical */}
        <div style={{ position: "relative" }}>
          {/* linha conectora */}
          <div style={{
            position: "absolute",
            left: 88,
            top: 0,
            bottom: 0,
            width: 1,
            background: "linear-gradient(180deg, transparent, rgba(157,78,221,0.3) 8%, rgba(157,78,221,0.3) 92%, transparent)",
            zIndex: 0,
          }} />

          {workflowSteps.map((step, i) => (
            <div
              key={step.id}
              style={{
                display: "grid",
                gridTemplateColumns: "180px 1fr 360px",
                gap: 32,
                padding: "56px 0",
                borderBottom: i < workflowSteps.length - 1 ? "1px dashed rgba(157,78,221,0.1)" : "none",
                position: "relative",
                zIndex: 1,
              }}
            >
              {/* coluna esquerda: número + horário */}
              <div style={{ position: "relative" }}>
                {/* nó na timeline */}
                <div style={{
                  position: "absolute",
                  left: 72,
                  top: 18,
                  width: 32,
                  height: 32,
                  borderRadius: "50%",
                  background: "#0E0820",
                  border: "2px solid #9D4EDD",
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "center",
                  fontFamily: "'JetBrains Mono', monospace",
                  fontSize: 11,
                  color: "#9D4EDD",
                  fontWeight: 600,
                  boxShadow: "0 0 24px rgba(157,78,221,0.4)",
                }}>
                  {String(i + 1).padStart(2, "0")}
                </div>
                <div style={{ paddingRight: 80 }}>
                  <p style={{
                    fontFamily: "'JetBrains Mono', monospace",
                    fontSize: 10,
                    letterSpacing: "0.12em",
                    color: "#7a6e90",
                    textTransform: "uppercase",
                    marginBottom: 4,
                  }}>{step.id}</p>
                  <p style={{
                    fontFamily: "'Cormorant Garamond', serif",
                    fontSize: 18,
                    fontStyle: "italic",
                    color: "#c4b8d4",
                    lineHeight: 1.3,
                  }}>{step.moment}</p>
                </div>
              </div>

              {/* coluna central: nome + terminal */}
              <div>
                <h3 style={{
                  fontFamily: "'Cormorant Garamond', serif",
                  fontSize: 38,
                  fontWeight: 400,
                  color: "#f0e8d8",
                  marginBottom: 24,
                  lineHeight: 1,
                }}>{step.name}</h3>
                <ThemeProvider aesthetic={aesthetic} entity={entity}>
                  <Terminal height={step.height}>
                    <step.Component />
                  </Terminal>
                </ThemeProvider>
              </div>

              {/* coluna direita: narrativa + arquivos */}
              <div style={{ paddingTop: 56 }}>
                <p style={{
                  fontFamily: "'Cormorant Garamond', serif",
                  fontSize: 18,
                  lineHeight: 1.6,
                  color: "#c4b8d4",
                  marginBottom: 24,
                }}>{step.narrative}</p>
                <div style={{
                  paddingTop: 16,
                  borderTop: "1px solid rgba(157,78,221,0.15)",
                }}>
                  <p className="kicker" style={{ marginBottom: 6 }}>arquivos</p>
                  <p style={{
                    fontFamily: "'JetBrains Mono', monospace",
                    fontSize: 12,
                    color: "#9c8fb0",
                    lineHeight: 1.5,
                  }}>
                    <code style={{ color: "#ffb454" }}>{step.files}</code>
                  </p>
                </div>
              </div>
            </div>
          ))}
        </div>

        <div className="spacer-lg" />

        <div style={{
          padding: "40px 48px",
          background: "rgba(157,78,221,0.04)",
          borderLeft: "2px solid #9D4EDD",
          borderRadius: "0 6px 6px 0",
        }}>
          <p className="kicker" style={{ marginBottom: 12 }}>nota de design</p>
          <p style={{
            fontFamily: "'Cormorant Garamond', serif",
            fontStyle: "italic",
            fontSize: 22,
            color: "#c4b8d4",
            lineHeight: 1.5,
            maxWidth: 920,
          }}>
            A diferença entre uma CLI boa e uma CLI lembrável é{" "}
            <strong style={{ color: "#f0e8d8" }}>continuidade</strong>. Cada tela do
            fluxo acima nasce do estado anterior. O dev nunca volta ao começo:
            ele desliza por momentos do seu dia, e o terminal anda junto.
          </p>
        </div>
      </div>
    </section>
  );
}

Object.assign(window, { WorkflowSection });
