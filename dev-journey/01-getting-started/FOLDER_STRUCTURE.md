# Estrutura do Projeto

```
Nyx-Code/
├── bin/                           # Binários
│   ├── nyx                        # Entry point Node.js (TUI)
│   └── ollama                     # Binário Ollama local
├── dist -> reference/dist         # Symlink para bundle da TUI
│
├── nyx/                           # Pacote Python principal
│   ├── proxy.py                   # Proxy OpenAI -> Ollama nativa (think=false) <!-- noqa-anonimato -->
│   ├── config/                    # Configuração centralizada
│   │   ├── settings.py            # NyxSettings (carrega .env + CLI)
│   │   └── defaults.py            # Constantes padrão
│   ├── themes/                    # Sistema de temas por entidade
│   │   ├── __init__.py            # ThemeManager
│   │   ├── constants.py           # Fallback Dracula
│   │   ├── utils.py               # hex_to_rgb, lighten, darken, hex_to_ansi
│   │   └── entities/              # JSONs de cores (7 entidades)
│   │       ├── nyx.json           # Tema padrão (cyan #00D4AA)
│   │       ├── luna.json          # Dracula Gothic (roxo #BD93F9)
│   │       ├── mars.json          # Vermelho sobre negro
│   │       ├── eris.json          # Caos púrpura
│   │       ├── juno.json          # Verde orgânico
│   │       ├── lars.json          # Terminal clássico
│   │       └── somn.json          # Azul noturno
│   ├── agent/                     # [backlog] Loop do agente
│   ├── tools/                     # [backlog] Ferramentas
│   ├── providers/                 # [backlog] Clients LLM
│   ├── context/                   # [backlog] Gerenciamento de contexto
│   ├── interface/                 # [backlog] TUI customizada
│   └── integration/               # [backlog] Protocolo Luna
│
├── scripts/                       # Scripts de automação
│   ├── sync.py                    # Verificação de consistência do projeto
│   └── gauntlet/                  # Framework de validação (ADR-007)
│       ├── nyx_gauntlet.py        # Script único de testes (62 features)
│       ├── run_stress.sh          # Stress test legado
│       └── fixtures/              # Arquivos de teste
│
├── dev-journey/                   # Documentação técnica
│   ├── 00-INDEX.md                # Índice geral
│   ├── 01-getting-started/        # Guias iniciais
│   ├── 02-architecture/           # Diagramas
│   ├── 03-decisions/              # ADRs (001-009)
│   ├── 04-features/               # Mapeamento de features
│   ├── 06-sprints/                # Sprints (produção/concluídos/backlog)
│   ├── 07-reports/gauntlet/       # Reports do Gauntlet (histórico)
│   ├── 08-templates/              # Templates de sprint
│   └── 09-legacy/                 # Testes expect legados
│
├── .github/                       # CI/CD
│   └── workflows/ci.yml           # Lint + smoke tests
│
├── reference/                     # Fonte original da TUI (intocável)
│
├── tests/                         # Testes unitários Python (lógica pura)
├── logs/                          # Logs rotacionados (gitignore)
├── sessions/                      # Sessões persistidas (gitignore)
├── models/                        # Modelos Ollama (gitignore)
│
├── run.sh                         # Launcher (Ollama + Proxy + TUI/Gauntlet)
├── install.sh                     # Instalação completa
├── uninstall.sh                   # Remoção limpa
├── GUIDE.md                      # Regras e identidade Nyx
├── README.md                      # Documentação principal
├── .env.example                   # Template de configuração
├── pyproject.toml                 # Metadata Python
├── requirements.txt               # Dependências Python
└── package.json                   # Dependências Node.js
```
