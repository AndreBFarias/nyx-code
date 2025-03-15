# Estrutura do Projeto

```
Nyx-Code/
├── bin/                     # Binários (openclaude, Ollama local)
│   └── openclaude           # Entry point Node.js
├── dist -> reference/dist   # Symlink para bundle openclaude
├── models/                  # Modelos Ollama (gitignore)
├── nyx/                     # Pacote Python
│   ├── proxy.py             # Proxy OpenAI -> Ollama nativa
│   ├── config/              # Configuração (settings, defaults)
│   ├── agent/               # [backlog] Loop do agente
│   ├── tools/               # [backlog] Ferramentas
│   ├── providers/           # [backlog] Clients LLM
│   ├── context/             # [backlog] Gerenciamento de contexto
│   ├── interface/           # [backlog] TUI customizada
│   └── integration/         # [backlog] Protocolo Luna
├── reference/               # Fonte openclaude (referência)
│   ├── dist/cli.mjs         # Bundle 19MB (gitignore)
│   ├── package.json
│   └── README.md
├── sprints/                 # Documentação de sprints
│   ├── completas/
│   ├── ativa/
│   └── backlog/
├── dev-journey/             # Arquitetura, decisões, guias
├── tests/                   # Testes E2E (expect)
├── logs/                    # Logs rotacionados (gitignore)
├── sessions/                # Sessões persistidas (gitignore)
├── .claude/                 # Configuração do openclaude
│   └── settings.json
├── CLAUDE.md                # Regras do projeto (carregado pelo openclaude)
├── install.sh               # Instalação completa
├── run.sh                   # Launcher (Ollama + Proxy + OpenClaude)
├── uninstall.sh             # Remoção limpa
├── main.py                  # Entry point Python (esqueleto)
├── .env                     # Configuração local (gitignore)
├── .env.example             # Template de configuração
├── pyproject.toml           # Metadata Python
├── requirements.txt         # Dependências Python
├── package.json             # Dependências Node.js
└── README.md                # Documentação principal
```
