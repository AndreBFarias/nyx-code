// session-data.jsx — Estrutura de eventos da sessão Nyx redesenhada.
// Cada item descreve um bloco que o renderizador da variação consome.
// Os textos aqui são o "ideal final" — capitalização correta, acentuação
// preservada, sem duplicações, com chain-of-thought e ferramentas claras.

const USER_NAME = "André";

const NYX_SESSION = [
  // ───────────────────────────────────────────────────────────────────
  // FASE 1 — Boot / Santuário
  // ───────────────────────────────────────────────────────────────────
  {
    type: "boot",
    title: "Santuário · Nyx-Code",
    rows: [
      { k: "Path",     v: "~/Desenvolvimento/Nyx-Code" },
      { k: "Venv",     v: "venv · Python 3.11.8" },
      { k: "Git",      v: "AndreBFarias · branch main" },
      { k: "Modelo",   v: "qwen2.5-coder:3b · 100% offline" },
    ],
    checks: [
      { ok: true,  label: "Requisitos detectados",        detail: "1 arquivo" },
      { ok: true,  label: "Repositórios alinhados",       detail: "padrão anti-IA" },
      { ok: true,  label: "Validador",                    detail: "BRIEF ativo · 44 linhas · atualizado há 1d" },
      { ok: true,  label: "Emojis varridos",              detail: "51 arquivos limpos" },
    ],
    ready: "Santuário pronto.",
  },

  // ───────────────────────────────────────────────────────────────────
  // FASE 2 — Wizard de onboarding (--menu)
  // ───────────────────────────────────────────────────────────────────
  {
    type: "wizard",
    welcome: {
      title: "Bem-vindo, André.",
      sub:   "Configure a Nyx em 5 passos. Enter aceita o destacado.",
    },
    steps: [
      {
        n: 1, total: 5,
        question: "Estética visual",
        hint: "define paleta base do terminal",
        options: [
          { id: "default",   label: "Default",   desc: "Turquesa + roxo, paleta canônica" },
          { id: "arcano",    label: "Arcano",    desc: "Noite violeta com glow sutil" },
          { id: "cyberpunk", label: "Cyberpunk", desc: "Neon saturado, scanlines" },
          { id: "brutalist", label: "Brutalist", desc: "Papel branco, tinta preta" },
          { id: "mecha",     label: "Mecha",     desc: "HUD âmbar, monoespaçado" },
          { id: "editorial", label: "Editorial", desc: "Papel creme, serifa" },
        ],
        chosen: "mecha",
      },
      {
        n: 2, total: 5,
        question: "Entidade",
        hint: "sobrescreve cor de destaque",
        options: [
          { id: "nyx",  label: "Nyx",  desc: "Turquesa · #00D4AA" },
          { id: "eris", label: "Eris", desc: "Rosa · #FF79C6" },
          { id: "juno", label: "Juno", desc: "Verde · #A4CB58" },
          { id: "lars", label: "Lars", desc: "Matrix · #50FA7B" },
          { id: "luna", label: "Luna", desc: "Violeta · #BD93F9" },
          { id: "mars", label: "Mars", desc: "Vermelho · #FF5555" },
          { id: "somn", label: "Somn", desc: "Ciano · #8BE9FD" },
        ],
        chosen: "luna",
      },
      {
        n: 3, total: 5,
        question: "Banner",
        hint: "como aparece o cabeçalho ao bootar",
        options: [
          { id: "wide",     label: "Wide",     desc: "3 linhas, ADR-029 (padrão)" },
          { id: "compact",  label: "Compact",  desc: "1 linha mínima" },
          { id: "neofetch", label: "Neofetch", desc: "Info-rich estilo neofetch" },
        ],
        chosen: "neofetch",
      },
      {
        n: 4, total: 5,
        question: "Modelo Ollama",
        hint: "qual modelo carregar na inicialização",
        options: [
          { id: "q25c3b", label: "qwen2.5-coder:3b", desc: "Rápido · PT-BR 100% · ~2 GB VRAM" },
          { id: "q34b",   label: "qwen3:4b",        desc: "Thinking · pode degradar PT-BR" },
          { id: "q25c7b", label: "qwen2.5-coder:7b", desc: "Qualidade maior · ~3 GB · P95 alto" },
        ],
        chosen: "q25c3b",
      },
      {
        n: 5, total: 5,
        question: "Aprovação automática de ferramentas",
        hint: "CONFIRM_ONCE — pula confirmações em ferramentas seguras",
        options: [
          { id: "no",  label: "Não", desc: "Pergunta a cada execução (recomendado)" },
          { id: "yes", label: "Sim", desc: "Modo automação — confirma apenas operações destrutivas" },
        ],
        chosen: "yes",
      },
    ],
    summary: {
      title: "Pronto, André. Sua configuração:",
      rows: [
        { k: "Estética",        v: "Mecha" },
        { k: "Entidade",        v: "Luna · violeta #BD93F9" },
        { k: "Banner",          v: "Neofetch" },
        { k: "Modelo",          v: "qwen2.5-coder:3b" },
        { k: "Auto-aprovar",    v: "Sim · CONFIRM_ONCE ativo" },
      ],
      foot: "Salvar em ~/.nyx/config.toml e iniciar?",
    },
  },

  // ───────────────────────────────────────────────────────────────────
  // FASE 3 — Header de sessão (substitui a linha-única confusa)
  // ───────────────────────────────────────────────────────────────────
  {
    type: "header",
    name: "Nyx",
    version: "v1.2.0",
    tag: "100% offline",
    groups: [
      { label: "Modelo",  v: "qwen2.5-coder:3b · Luna" },
      { label: "Projeto", v: "Nyx-Code · branch main" },
      { label: "Rede",    v: "ollama :11435 · proxy :11436" },
      { label: "Sessão",  v: "35 ferramentas · memória ativa · auto-aprovar" },
    ],
    hint: "/help para comandos  ·  Ctrl+D para sair",
  },

  // ───────────────────────────────────────────────────────────────────
  // FASE 4 — Saudação inicial (simples, sem chain-of-thought)
  // ───────────────────────────────────────────────────────────────────
  {
    type: "exchange",
    user: { name: USER_NAME, text: "Olá, tudo bem?" },
    nyx: {
      thinking: null,
      tools: [],
      body: [
        { kind: "p", text: "Olá, André. Tudo certo por aqui — Luna ativa, contexto Nyx-Code carregado." },
        { kind: "p", text: "Em que posso te ajudar?" },
      ],
      meta: { time: "0.8s", tokens: 32 },
    },
  },

  // ───────────────────────────────────────────────────────────────────
  // FASE 5 — Pedido complexo: arquivo .md com estrutura e to-do
  // ───────────────────────────────────────────────────────────────────
  {
    type: "exchange",
    user: {
      name: USER_NAME,
      text:
        "Pode criar um arquivo .md em ~/Documentos explicando regras de indentação em Python? " +
        "Umas 100 linhas, conceito complexo em linguagem simples.",
    },
    nyx: {
      thinking: {
        duration: "4.2s",
        preview: "Estruturar como guia — começar pelo princípio (PEP 8), depois exemplos progressivos…",
        expanded: false,
        full: [
          "O pedido pede profundidade conceitual com linguagem simples. Vou estruturar em 5 seções:",
          "  1. Por que o Python usa indentação ao invés de chaves (decisão de design)",
          "  2. Regras mecânicas — espaços vs tabs, PEP 8, 4 espaços",
          "  3. Blocos compostos — if/for/while/def/class/try",
          "  4. Erros comuns — IndentationError, TabError, mistura de níveis",
          "  5. Ferramentas — black, ruff, .editorconfig",
          "Vou usar exemplos curtos comentados. Acentuação preservada. ~100 linhas.",
        ],
      },
      tools: [
        {
          name: "write_file",
          args: "~/Documentos/indentacao-python.md",
          status: "ok",
          time: "12ms",
          detail: "112 linhas escritas",
        },
      ],
      body: [
        { kind: "p", text: "Criei o guia em ~/Documentos/indentacao-python.md (112 linhas)." },
        {
          kind: "todo",
          title: "Cobertura do documento",
          items: [
            { done: true,  text: "Por que Python usa indentação (decisão de design)" },
            { done: true,  text: "PEP 8 · 4 espaços, sem tabs misturadas" },
            { done: true,  text: "Blocos: if · for · while · def · class · try" },
            { done: true,  text: "IndentationError vs TabError — diagnóstico" },
            { done: true,  text: "Ferramentas: black, ruff, .editorconfig" },
          ],
        },
        { kind: "p", text: "Quer que eu adicione uma seção sobre context managers (with) ou está bom assim?" },
      ],
      meta: { time: "4.9s", tokens: 487 },
    },
  },

  // ───────────────────────────────────────────────────────────────────
  // FASE 6 — Tool call que ERRA (arquivo fora do projeto)
  // ───────────────────────────────────────────────────────────────────
  {
    type: "exchange",
    user: {
      name: USER_NAME,
      text:
        "Lê o Checkpoint.md de ~/Desenvolvimento/Protocolo-Mob-Ouroboros e me descreve qualitativamente, " +
        "não só os benchmarks.",
    },
    nyx: {
      thinking: {
        duration: "1.1s",
        preview: "Caminho fora do projeto ativo — tentar leitura, se falhar oferecer permissão explícita.",
        expanded: false,
        full: [
          "Caminho está fora do escopo do projeto ativo (Nyx-Code).",
          "Vou tentar a leitura — se a sandbox bloquear, ofereço o comando para liberar o caminho temporariamente.",
        ],
      },
      tools: [
        {
          name: "read_file",
          args: "~/Desenvolvimento/Protocolo-Mob-Ouroboros/Checkpoint.md",
          status: "error",
          time: "1ms",
          detail: "Caminho fora do projeto Nyx-Code (sandbox)",
        },
      ],
      body: [
        { kind: "p", text: "Não consegui ler — o arquivo está fora do projeto ativo e a sandbox bloqueou o acesso." },
        {
          kind: "actions",
          intro: "Posso fazer um destes:",
          items: [
            { key: "a", text: "Liberar o caminho nesta sessão", cmd: "/allow ~/Desenvolvimento/Protocolo-Mob-Ouroboros" },
            { key: "b", text: "Trocar o projeto ativo",         cmd: "/cd ~/Desenvolvimento/Protocolo-Mob-Ouroboros" },
            { key: "c", text: "Você cola o conteúdo aqui",      cmd: "(paste no prompt)" },
          ],
        },
        { kind: "p", text: "Qual você prefere?" },
      ],
      meta: { time: "1.4s", tokens: 78 },
    },
  },

  // ───────────────────────────────────────────────────────────────────
  // FASE 7 — Comando /help (slash command)
  // ───────────────────────────────────────────────────────────────────
  {
    type: "slash",
    cmd: "/help",
    groups: [
      {
        title: "Sessão",
        items: [
          { c: "/resume",      d: "Retoma a última sessão salva" },
          { c: "/save <nome>", d: "Salva a sessão com nome" },
          { c: "/quit",        d: "Encerra com estatísticas" },
        ],
      },
      {
        title: "Contexto",
        items: [
          { c: "/cd <path>",     d: "Troca o projeto ativo" },
          { c: "/allow <path>",  d: "Permite leitura fora do escopo" },
          { c: "/output-style",  d: "Tom: default · concise · learning" },
        ],
      },
      {
        title: "Modelo",
        items: [
          { c: "/model <id>",  d: "Troca o modelo Ollama" },
          { c: "/entity <id>", d: "Troca a entidade (Luna, Nyx, Eris…)" },
          { c: "/tools",       d: "Lista as 35 ferramentas disponíveis" },
        ],
      },
    ],
  },

  // ───────────────────────────────────────────────────────────────────
  // FASE 8 — Encerramento (/quit + estatísticas)
  // ───────────────────────────────────────────────────────────────────
  {
    type: "quit",
    title: "Sessão encerrada",
    sub:   "Salva em ~/.nyx/sessions/session_Nyx-Code_1779131272.json — use /resume para retomar.",
    stats: [
      { k: "Iterações",          v: "4" },
      { k: "Arquivos lidos",     v: "0" },
      { k: "Arquivos escritos",  v: "1" },
      { k: "Ferramentas",        v: "2 chamadas · 1 erro" },
      { k: "Tempo total",        v: "18min 9s" },
      { k: "Tokens",             v: "597 entrada · 519 saída" },
    ],
    shutdown: [
      "Desconectando proxy (:11436)",
      "Parando Ollama (PID 496852)",
      "Sessão salva. Até logo, André.",
    ],
  },
];

window.NYX_SESSION = NYX_SESSION;
window.NYX_USER_NAME = USER_NAME;
