// audit.jsx — Auditoria: lista de problemas identificados na UI atual da Nyx.
// Renderizado como artboard inicial no canvas; serve como guia das decisões.

const PROBLEMS = [
  {
    n: 1,
    title: "Capitalização inconsistente",
    bad: "configure antes de bootar (Enter aceita default)",
    good: "Configure antes de inicializar. ↵ Enter aceita o destaque.",
    note: "Sentenças começam em maiúscula. Substantivos próprios respeitados (Enter, Ollama, Nyx).",
  },
  {
    n: 2,
    title: "Duplicação do prompt do usuário",
    bad: "nyx> Olá, tudo bem?\\n┌─ você ─┐\\n│ Olá, tudo bem? │\\n└────────┘",
    good: "[André] Olá, tudo bem?  ← uma única linha, sem eco redundante",
    note: "O eco da pergunta dentro de uma caixa logo abaixo é ruído visual.",
  },
  {
    n: 3,
    title: "Rótulo \"você\" impessoal",
    bad: "┌─ você ─┐",
    good: "[André] · ler do contexto git ou perguntar no onboarding",
    note: "O usuário tem nome (André) — usar é mais humano e diferenciador.",
  },
  {
    n: 4,
    title: "Sem onboarding real",
    bad: "Wizard hoje é uma lista numerada sem contexto, sem step counter, sem boas-vindas.",
    good: "Welcome → 5 passos numerados (01/05) → resumo lateral → \"Salvar?\"",
    note: "Inspirado no fluxo do Claude Code: cada passo respira, tem hint e cards selecionáveis.",
  },
  {
    n: 5,
    title: "Header da sessão é uma linha entupida",
    bad: "Nyx v1.2.0  |  qwen2.5-coder:3b  |  Nyx-Code  |  :11435  ·  :11436  |  tools 35  |  memória ativa",
    good: "Bloco em 3-4 linhas: Modelo / Projeto / Rede / Sessão — cada par rotulado.",
    note: "Hierarquia tipográfica: nome em destaque, separador fino, dados em colunas.",
  },
  {
    n: 6,
    title: "Sem chain-of-thought visível",
    bad: "\"pensando…\" e depois aparece a resposta. Caixa-preta.",
    good: "Bloco recolhível: ▶ pensando · 4.2s · prévia (uma linha). Tab expande tudo.",
    note: "Mostra que a Nyx pensou, sem poluir. Auditoria opcional.",
  },
  {
    n: 7,
    title: "Sem indicação de duração",
    bad: "Resposta aparece sem custo nem latência.",
    good: "Nyx · 4.9s · 487 tokens — header inline, fonte pequena, cor secundária.",
    note: "Útil para iterar com modelos locais (P95 varia).",
  },
  {
    n: 8,
    title: "Tool calls poluídos e cortados",
    bad: "╭─ read_file ── executando ─╮\\n│  file_path=/home/andre…   │\\n╭─ read_file ── ERRO · 1ms ─╮  ← duas caixas pra um tool",
    good: "● read_file ~/.../Checkpoint.md   1ms   erro — fora do escopo",
    note: "Uma linha, status colorido, sem corte de path, sem duplicação do header.",
  },
  {
    n: 9,
    title: "Acentuação quebrada",
    bad: "configuracao escolhida, permissoes, padrao, automacao",
    good: "configuração, permissões, padrão, automação",
    note: "PT-BR completo. Locale pt_BR.UTF-8 já está ativo no sistema do usuário.",
  },
  {
    n: 10,
    title: "Output da Nyx sem ancoragem visual",
    bad: "Texto solto, sem header, indistinguível do output do shell.",
    good: "◆ Nyx · meta inline · faixa vertical violeta à esquerda do bloco.",
    note: "O usuário precisa saber onde começa e termina cada turno.",
  },
  {
    n: 11,
    title: "Sem estrutura no conteúdo (to-do, ações, listas)",
    bad: "Tudo vira parágrafo. Listas viram bullets numéricos cruzados com **markdown bruto**.",
    good: "To-do real com checkboxes ✓, ações nomeadas (a/b/c) com comandos chip.",
    note: "Quando a Nyx falar de \"tarefas concluídas\", elas viram um TodoBlock visual.",
  },
  {
    n: 12,
    title: "Tratamento de erro sem solução",
    bad: "\"Fora do projeto Nyx-Code\" — e nada mais.",
    good: "Erro + 3 ações: (a) /allow caminho  (b) /cd  (c) colar conteúdo.",
    note: "Toda mensagem de erro vira oportunidade — sempre oferecer próximo passo.",
  },
  {
    n: 13,
    title: "/quit sem fechamento real",
    bad: "Caixa \"sessão\" com 4 linhas e \"Desconectando…\" \"Fim.\" \"[nyx] Proxy não iniciou\" misturados.",
    good: "Card de estatísticas em grid + log de shutdown limpo + caminho do save.",
    note: "Fim de sessão é momento de polish — última impressão.",
  },
  {
    n: 14,
    title: "Banner [nyx] vs nome \"Nyx\" misturados",
    bad: "[nyx] Aquecendo modelo… / Nyx v1.2.0 / nyx> prompt",
    good: "Log lines: rótulo \"santuário\" (boot) → \"Nyx\" (sessão). Prompt: › (sem nome).",
    note: "Separa o log do shell de inicialização do diálogo propriamente dito.",
  },
  {
    n: 15,
    title: "Sem hint de comandos",
    bad: "/help mostra 3 itens sem agrupamento.",
    good: "/help em colunas: Sessão · Contexto · Modelo — cada comando com descrição.",
    note: "Inspirado no painel do Claude Code; ajuda a discoverability.",
  },
];

const AuditArtboard = ({ theme }) => {
  const T = theme || window.NYX_THEMES.hybrid;
  return (
    <div style={{
      width: "100%",
      height: "100%",
      background: "#1a1822",
      color: T.fg,
      padding: "40px 48px",
      fontFamily: "'Inter', system-ui, sans-serif",
      overflow: "hidden",
      display: "flex",
      flexDirection: "column",
    }}>
      <div style={{ flex: "0 0 auto", marginBottom: 24 }}>
        <div style={{
          fontSize: 11,
          color: T.accent,
          letterSpacing: 3,
          textTransform: "uppercase",
          marginBottom: 6,
          fontWeight: 600,
        }}>Diagnóstico · Nyx CLI · v1.2.0</div>
        <h1 style={{
          margin: 0,
          fontSize: 36,
          fontWeight: 700,
          letterSpacing: -0.5,
          color: "#fff",
          lineHeight: 1.1,
        }}>15 problemas na UI do terminal — antes & depois</h1>
        <p style={{
          margin: "10px 0 0",
          color: T.muted,
          fontSize: 14,
          maxWidth: 920,
        }}>
          Os screenshots mostram repetição, falta de hierarquia, locale quebrado e a sensação geral de
          que tudo vive no mesmo plano visual. Abaixo o levantamento; nas variações ao lado, três caminhos
          de redesenho aplicando estas correções.
        </p>
      </div>

      <div style={{
        flex: "1 1 auto",
        display: "grid",
        gridTemplateColumns: "repeat(3, 1fr)",
        gap: 14,
        overflow: "hidden",
        alignContent: "start",
      }}>
        {PROBLEMS.map((p) => (
          <div key={p.n} style={{
            border: `1px solid ${T.faint}55`,
            background: "rgba(255,255,255,0.02)",
            borderRadius: 8,
            padding: "12px 14px",
            display: "flex",
            flexDirection: "column",
            gap: 6,
          }}>
            <div style={{ display: "flex", alignItems: "baseline", gap: 8 }}>
              <span style={{
                color: T.accent,
                fontSize: 11,
                fontVariantNumeric: "tabular-nums",
                fontWeight: 700,
                letterSpacing: 0.5,
              }}>{String(p.n).padStart(2, "0")}</span>
              <span style={{
                color: "#fff",
                fontSize: 13.5,
                fontWeight: 600,
                lineHeight: 1.2,
              }}>{p.title}</span>
            </div>
            <div style={{
              fontFamily: "'Fira Mono', monospace",
              fontSize: 11,
              padding: "6px 8px",
              borderLeft: `2px solid ${T.err}`,
              background: T.err + "10",
              color: T.muted,
              borderRadius: "0 4px 4px 0",
              whiteSpace: "pre-wrap",
              lineHeight: 1.4,
            }}>{p.bad}</div>
            <div style={{
              fontFamily: "'Fira Mono', monospace",
              fontSize: 11,
              padding: "6px 8px",
              borderLeft: `2px solid ${T.ok}`,
              background: T.ok + "10",
              color: T.fg,
              borderRadius: "0 4px 4px 0",
              whiteSpace: "pre-wrap",
              lineHeight: 1.4,
            }}>{p.good}</div>
            <div style={{
              color: T.faint,
              fontSize: 11,
              fontStyle: "italic",
              lineHeight: 1.4,
            }}>{p.note}</div>
          </div>
        ))}
      </div>
    </div>
  );
};

Object.assign(window, { AuditArtboard });
