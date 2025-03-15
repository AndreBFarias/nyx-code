# Nyx-Code

Agente de código local. 100% offline. Terminal.

Roda qwen3:4b via Ollama com tool calling real (Read, Write, Edit, Bash, Glob, Grep).
Projeto standalone que será integrado ao projeto Luna como agente coder da entidade Nyx.

## Arquitetura

```
                    ┌─────────────────────────────────┐
                    │          Nyx-Code (TUI)          │
                    │        openclaude v0.1.7          │
                    └──────────┬──────────────────────┘
                               │
                    ┌────────────────────────────────┐
                    │      Proxy  (:11436)             │
                    │  nyx/proxy.py                     │
                    │  - Converte /v1/ -> /api/chat     │
                    │  - Injeta think=false              │
                    │  - Controla num_gpu e num_ctx      │
                    └──────────┬──────────────────────┘
                               │
                    ┌────────────────────────────────┐
                    │      Ollama  (:11435)             │
                    │  qwen3:4b (num_gpu=12)            │
                    │  RTX 3050 ~1.2GB VRAM             │
                    └─────────────────────────────────┘
```

## Começando

### Instalar

```bash
./install.sh
```

Baixa o binário do Ollama, cria venv Python, instala dependências,
baixa qwen3:4b + qwen2.5-coder:3b + 7b para `./models/`.

### Usar

```bash
./run.sh          # Inicia com qwen3:4b (padrão)
./run.sh --3b     # qwen2.5-coder:3b (sem tool calling)
./run.sh --7b     # qwen2.5-coder:7b
./run.sh --debug  # Logs detalhados
```

O `run.sh` cuida de tudo: mata Ollama anterior, inicia novo, aquece modelo,
sobe proxy, abre interface. Ao sair (Ctrl+C), limpa tudo.

### Remover

```bash
./uninstall.sh        # Remove modelos (~6GB), venv, binário Ollama
./uninstall.sh --full # Remove tudo incluindo .env
```

## Estrutura

```
nyx/
├── proxy.py         # Proxy OpenAI -> Ollama nativa (think=false)
├── config/          # Configuração centralizada (settings, defaults)
├── agent/           # [backlog] Loop do agente, parser, sessão
├── tools/           # [backlog] Read, Write, Edit, Bash, Glob, Grep
├── providers/       # [backlog] Ollama client
├── context/         # [backlog] Gerenciamento de contexto e tokens
├── interface/       # [backlog] Interface terminal customizada
└── integration/     # [backlog] Protocolo de integração com Luna
```

## Decisões (ADRs)

| ADR | Título | Resumo |
|-----|--------|--------|
| 001 | Local First | 100% offline, zero dependência de cloud |
| 002 | Proxy think=false | Resolve tool calling via conversão de API |
| 003 | Gerenciamento VRAM | num_gpu=12 para RTX 3050 sem OOM |
| 004 | Zero Emojis | Estética limpa, sem genéricos |
| 005 | Anonimato | Sem menção a IA em commits/código |
| 006 | PT-BR | Acentuação correta obrigatória |

## Requisitos

- Linux (x86_64 ou arm64)
- Python 3.10+
- Node.js 18+
- GPU NVIDIA (opcional, melhora performance)
- ~8 GB de disco (modelos)

## Relação com Luna

Nyx-Code será integrado ao projeto Luna (`~/Desenvolvimento/Luna`) como
agente de código da entidade Nyx. A integração é via modo headless
com protocolo JSON (Sprint 09 no backlog).
