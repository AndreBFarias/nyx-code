# Guia do Projeto Nyx-Code para LLMs

**Versão:** v1.0
**Data:** 2026-04-04

Este guia explica o projeto Nyx-Code de forma clara para qualquer modelo de linguagem, incluindo modelos pequenos (3B). Se conseguir ler este arquivo, consegue contribuir.

---

## O que é o Nyx-Code

Agente de código local. Roda 100% offline usando Ollama com modelos open-source (qwen3:4b). Funciona como assistente de programação no terminal.

## Arquitetura

```
Usuário -> run.sh -> Ollama (:11435) -> GPU (num_gpu=12)
                  -> Proxy  (:11436) -> think=false -> Ollama
                  -> Nyx (TUI)        -> Proxy -> Ollama
```

- **Ollama** (porta 11435): servidor de inferência local
- **Proxy** (porta 11436): intercepta requests, injeta `think=false`, normaliza formato /v1/chat
- **TUI**: interface de terminal (Node.js + TypeScript)

## Estrutura de diretórios

```
Nyx-Code/
├── bin/nyx                  # Ponto de entrada da TUI
├── run.sh                   # Launcher principal (inicia tudo)
├── install.sh               # Instalação
├── uninstall.sh             # Desinstalação
├── GUIDE.md                # Instruções para agentes de IA
├── GAUNTLET_REPORT.md       # Resultado do último teste
├── nyx/                     # Código Python do agente
│   ├── proxy.py             # Proxy HTTP (Ollama <-> /v1/chat)
│   ├── config/              # Configurações
│   │   ├── defaults.py      # Constantes padrão
│   │   └── settings.py      # Carregamento de .env
│   └── themes/              # Sistema de temas visuais
│       ├── __init__.py       # ThemeManager
│       ├── constants.py      # Fallback Dracula, cores ANSI
│       ├── utils.py          # hex_to_rgb, lighten, darken
│       └── entities/         # 7 temas JSON (nyx, luna, mars...)
├── scripts/
│   ├── gauntlet/
│   │   └── nyx_gauntlet.py  # Gauntlet (todos os testes)
│   └── sync.py              # Verificação de consistência
├── dev-journey/              # Documentação do projeto
│   ├── 03-decisions/         # ADRs (decisões arquiteturais)
│   ├── 04-features/          # Mapa de features
│   ├── 05-guides/            # Guias (este arquivo)
│   ├── 06-sprints/           # Sprints de produção
│   │   ├── producao/         # Sprints ativas (diretório sem acento)
│   │   └── concluidos/       # Sprints concluídas
│   ├── 07-reports/           # Relatórios
│   │   └── gauntlet/         # Reports, baselines, flags
│   ├── 08-templates/         # Templates
│   └── 09-legacy/            # Código legado
└── .github/workflows/        # CI (lint + smoke tests)
```

## Comandos disponíveis

```bash
# Iniciar tudo (Ollama + Proxy + TUI)
./run.sh

# Rodar Gauntlet completo (~15min)
./run.sh --gauntlet

# Rodar Gauntlet parcial (~2min)
./run.sh --gauntlet --only rapido

# Rodar apenas uma fase
./run.sh --gauntlet --only tools

# Verificar consistência do projeto
python scripts/sync.py

# Opções do Gauntlet
# rapido    = infra + proxy + visual + config
# completo  = todas as 8 fases
# infra, proxy, tools, qualidade, performance, visual, config, resiliencia
```

## Fluxo do Gauntlet

O Gauntlet é o único mecanismo de teste (ADR-007). Zero testes unitários.

1. Detecta hardware (GPU, VRAM)
2. Para cada fase, verifica se Ollama está respondendo
3. Executa testes reais (requests HTTP, inferência LLM)
4. Salva checkpoint JSON a cada teste
5. Atualiza GAUNTLET_REPORT.md em tempo real
6. Compara com baseline anterior (detecção de regressão)
7. Salva baseline JSON no final
8. Exit code 0 = 100% passou, exit code 1 = falhas

**Fases:** infra(5) -> proxy(6) -> tools(6) -> qualidade(5) -> performance(5) -> visual(3) -> config(4) -> resiliência(2) = 36 testes

## Convenções obrigatórias

1. **PT-BR** com acentuação correta (á, é, í, ó, ú, â, ê, ô, ã, õ, ç)
2. **Zero emojis** em código, commits, docs, respostas
3. **Zero menções a IA** em código ou commits (ver GUIDE.md para detalhes)
4. **Type hints** em todo Python
5. **Logging** (nunca `print()`)
6. **Paths relativos** via `Path` (nunca hardcoded)
7. **Citação de filósofo** no final de cada script
8. **Commits em PT-BR**: `tipo: descrição imperativa`

## Decisões arquiteturais (ADRs)

- ADR-001: Local First (tudo offline)
- ADR-002: Proxy think=false (evita raciocínio desperdiçado)
- ADR-003: VRAM management (RTX 3050 4GB, num_gpu=12)
- ADR-004: Zero emojis
- ADR-005: Anonimato (sem nomes de IA)
- ADR-006: PT-BR obrigatório
- ADR-007: Gauntlet (1 teste por feature, 100% para push)
- ADR-008: KPIs de performance (baselines)
- ADR-009: Acesso universal (hardware limitado, sem limites artificiais)

## Como contribuir

1. Ler GUIDE.md
2. Ler este guia
3. Rodar `python scripts/sync.py` para verificar estado
4. Fazer alterações
5. Rodar `./run.sh --gauntlet` (100% obrigatório para push)
6. Commit em PT-BR sem emojis e sem menção a IA

---

*"O conhecimento é a única riqueza que cresce quando compartilhada." -- Sêneca*
