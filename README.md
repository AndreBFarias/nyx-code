![CI](https://github.com/AndreBFarias/nyx-code/actions/workflows/ci.yml/badge.svg)

# Nyx-Code

Agente de código local. 100% offline.

Roda qwen2.5-coder:3b via Ollama com 34 tools funcionais, 47 commands, 10 services.
Projeto standalone, otimizado para RTX 3050 4GB.

## Instalação rápida

```bash
git clone <este-repo> Nyx-Code
cd Nyx-Code
./install.sh                  # instalação completa idempotente
./install.sh --no-vision      # sem moondream (pula descrição de imagens)
./install.sh --no-kitty       # não pergunta sobre kitty terminal
./install.sh --dev            # inclui requirements-dev.txt
./install.sh --dry-run        # mostra o que faria, sem executar
./run.sh                      # sobe o agente local
```

**Distros suportadas pelo `detect_pkg_manager`:**

- Ubuntu/Debian (`apt-get`) — automatizado via fase Gauntlet `install` em Docker `ubuntu:22.04`
- Fedora/RHEL (`dnf`) — manual
- Arch (`pacman`) — manual
- openSUSE (`zypper`) — manual

`install.sh` é idempotente: rodar duas vezes produz a mesma saída (cada fase faz SKIP se já aplicada). Veja `./install.sh --help` para a lista completa das 11 fases.

### Replicação em outro PC (sem TTY / CI)

Para instalar sem interação manual (útil em containers, scripts de provisão, segundo computador):

```bash
export NYX_SUDO_PASSWORD='sua-senha-sudo-aqui'
./install.sh --no-prompt
unset NYX_SUDO_PASSWORD
```

**Segurança:** a senha é lida **só em runtime** via env var. Nunca é gravada em arquivo do repositório nem em log. Após instalar, considere `history -d <N>` para apagar o `export` do histórico do shell.

`NYX_INSTALL_SKIP_PULL=1` pula `ollama pull` (útil em Docker, ver DEPLOY-01B).

### Controle OOM (INFRA-OOM-01)

`run.sh` agora aplica automaticamente `ulimit -v 8GB` + `oom_score_adj -100` ao processo Nyx via `bin/nyx-runtime-limits.sh`. Em sessões longas com cockpit + Chrome MCP, isso reduz a chance do OOM-killer derrubar o Ollama.

Diagnóstico ao primeiro sinal de degradação:

```bash
bash scripts/check_oom.sh    # memória, swap, OOM kernel, top procs, oom_score do Nyx/Ollama
```

## Arquitetura

```
Usuário
  |
  v
run.sh ─────> Ollama (:11435) ──> GPU (num_gpu=12, qwen2.5-coder:3b)
  |
  +────────> Proxy (:11436)
  |           - /v1/chat/completions -> /api/chat
  |           - Injeta think=false (obrigatório para tool calling)
  |           - Controla num_gpu e num_ctx
  |
  +────────> Nyx CLI (nyx/cli.py)
              - REPL interativo com Rich output + prompt-toolkit
              - 34 tools via ToolRegistry
              - 61 slash commands
              - AgentLoop: plan-execute-observe (até 30 iterações)
              - ActionParser: 7 níveis de fallback
              - ContextBudget: compactação progressiva
              - Modo headless (--headless): JSON stdin/stdout
```

## Começando

```bash
./install.sh             # Ollama, venv, modelos (~8GB)
./run.sh                 # Inicia com qwen2.5-coder:3b (default, ADR-031)
./run.sh --menu          # Wizard interativo (aesthetic, modelo, banner, auto-approve)
./run.sh --web           # Sobe Cockpit + abre browser em 127.0.0.1:11437
./run.sh --7b            # qwen2.5-coder:7b
./run.sh --4b            # qwen3:4b (legacy, thinking)
./run.sh --debug         # Logs detalhados
./run.sh --gauntlet      # Validação completa
./run.sh --auto-approve  # Pula CONFIRM_ONCE (CI/automação)
./run.sh --aesthetic arcano  # Paleta arcana
./run.sh --aesthetic arcano:luna  # arcano + entidade luna (#BD93F9)
```

### Wizard (`--menu`)

Configura antes de bootar:

- **Aesthetic** (5 alternativas + default): arcano, cyberpunk, brutalist, mecha, editorial
- **Entidade** (7 opções): nyx, eris, juno, lars, luna, mars, somn (sobrescreve accent)
- **Banner**: compact | wide | neofetch
- **Modelo**: qwen2.5-coder:3b (padrão) | qwen3:4b | qwen2.5-coder:7b
- **Auto-aprovar permissões**: sim | não

Persiste em `~/.nyx/config.toml`. Próximo boot já adota.

### Cockpit Web (`--web`)

Sobe o servidor FastAPI local (`127.0.0.1:11437`, ADR-001 Local First) e abre o browser default:

- `/` -- dashboard com 62 features (cards reativos via Alpine.js + HTMX)
- `/static/terminal.html` -- REPL Nyx embedded via PTY + xterm.js
- `/api/{features,tokens,microcopy,aesthetics,evidencia}` -- introspecção
- `/control/{gauntlet,feature,repl,registry}` -- automação por agente externo

Documentação completa: [dev-journey/05-guides/COCKPIT_API.md](dev-journey/05-guides/COCKPIT_API.md).

## Validação

```bash
./run.sh --gauntlet                      # Completo
./run.sh --gauntlet --only rapido        # Infra+proxy+visual+config
./run.sh --gauntlet --only coverage      # Cobertura de componentes
./run.sh --gauntlet --only gpu_tune      # Auto-tune de GPU (PORT-01)
./run.sh --gauntlet --only portabilidade # Harness Docker existe (PORT-02)
python scripts/sync.py                   # Consistência N-para-N
```

## Portabilidade

Para validar que o projeto funciona em máquina limpa:

```bash
./docker/test-clean-boot.sh
```

Builda uma imagem Ubuntu 22.04 mínima, roda `./install.sh --no-prompt` e
executa `./run.sh --gauntlet --only coverage` dentro dela. Requer Docker +
NVIDIA Container Toolkit no host (se quiser validar caminho GPU). Sem GPU no
container, o auto-tune detecta e usa CPU (num_gpu=0).

`install.sh --no-prompt` é não-interativo: preserva binários existentes
sem perguntar, ideal para CI/container.

## Tools (35 registradas -- todas funcionais)

| Categoria | Tools |
|-----------|-------|
| Arquivo | read_file, write_file, edit_file, list_files, glob, search, notebook_edit |
| Execução | run_command, repl |
| Web | web_fetch, web_search |
| Tarefas | task_create, task_update, task_list, task_get, task_output, task_stop, todo_write |
| Planejamento | enter_plan_mode, exit_plan_mode, agent, done |
| Git | enter_worktree, exit_worktree |
| Edição avançada | analyze, patch, multi_edit |
| Utilidade | sleep, config, brief, tool_search, skill, send_message, ask_user |

## Commands (61 registrados)

| Categoria | Commands |
|-----------|----------|
| Geral | /help, /quit, /clear, /status, /? |
| Código | /explain, /plan, /test, /summary |
| Git | /commit, /diff, /review, /branch, /issue, /pr, /rewind |
| Sistema | /doctor, /model, /config, /env, /permissions, /hooks, /theme, /aesthetic, /output-style |
| Sessão | /compact, /context, /session, /resume, /export, /copy, /stats, /usage |
| Execução | /tasks, /skills, /files, /cancel |
| Projeto | /add-dir, /init, /version |
| Debug | /trace, /ctx-viz, /break-cache |
| Memória | /memory |
| Plugins/MCP | /plugin, /mcp |
| Avançado | /btw, /pr-comments |
| Root | /advisor, /brief-cmd, /commit-push-pr, /insights, /security-review |

## Services (14)

tokens, compact, hooks, memory, summary, suggestions, analytics, diagnostics, logging_service, tool_use_summary, plugin_manager, mcp_client, hook_runtime, lifecycle.

## Cockpit (Onda 23-24, COCKPIT-01..05 + UX-COCKPIT-EXPERIENCE-01)

Servidor local FastAPI em `127.0.0.1:11437` (bind loopback-only, ADR-001):

| Endpoint | O que faz |
|---|---|
| `GET /` | Dashboard reativo com 62 cards (Alpine.js + HTMX vendored, sem CDN) |
| `GET /static/terminal.html` | REPL Nyx embedded via PTY + xterm.js |
| `WS /repl` | Bridge PTY ↔ WebSocket (bidirecional, com resize JSON-meta) |
| `GET /api/features` | REGISTRY.yaml (62 features) |
| `GET /api/tokens` | Paleta D do design_tokens.py (frontend hidrata CSS vars) |
| `GET /api/microcopy` | MICROCOPY.md + 25 strings PT-BR canônicas |
| `GET /api/aesthetics` | 6 aesthetics × 7 entities + ativo |
| `GET /api/evidencia` | Lista evidências PNG por feature |
| `POST /api/screenshot` | Recebe PNG do canvas (form-data; rotação 5/feature) |
| `POST /api/features/{id}/run` | Dispara gauntlet single-feature |
| `GET /api/features/{id}/status/{job_id}` | Poll de progresso |
| `POST /control/gauntlet/run` | Gauntlet completo (cap 600s) |
| `POST /control/feature/{id}/run` | Alias do anterior |
| `GET /control/gauntlet/status/{job_id}` | Estado de qualquer job |
| `POST /control/repl/send` | Envia bytes pro PTY ativo |
| `GET /control/repl/snapshot` | Buffer (anti-débito COCKPIT-05-SNAPSHOT-BUFFER-01) |
| `GET /control/registry` | REGISTRY.yaml completo (introspecção MCP) |

Documentação completa: [`dev-journey/05-guides/COCKPIT_API.md`](dev-journey/05-guides/COCKPIT_API.md).

## Aesthetics & Entities (Onda 24, VISUAL-LAYOUT-01..08)

5 estéticos × 7 entidades = 35 combinações visuais opcionais.

| Aesthetic | Cor base | Características |
|---|---|---|
| `default` | turquesa `#00D4AA` + roxo `#9D4EDD` | Paleta D canônica (ADR-023) |
| `arcano` | roxo `#9D4EDD` profundo | Noite violeta com glow |
| `cyberpunk` | ciano neon `#00F5FF` + magenta | Scanlines, typewriter |
| `brutalist` | preto `#0A0A0A` em papel | Knuth-style, sem efeitos |
| `mecha` | âmbar `#FFAB00` HUD | Grid background |
| `editorial` | marrom `#7A4A1A` serif | Marginalia O'Reilly |

Entidades (override de accent): `nyx` (turquesa), `eris` (rosa), `juno` (verde), `lars` (matrix), `luna` (violeta), `mars` (vermelho), `somn` (ciano).

Uso:
```bash
./run.sh --menu                    # Wizard (5 perguntas)
./run.sh --aesthetic arcano        # Direto
./run.sh --aesthetic arcano:luna   # Combinado
# Em runtime:
/aesthetic list                    # ver opções
/aesthetic set cyberpunk:mars      # mudar
```

## ADRs (32)

| # | Título | Status |
|---|---|---|
| 001 | Local First -- 100% offline | ACEITO |
| 002 | Proxy think=false | ACEITO |
| 003 | VRAM Management (RTX 3050 4GB) | ACEITO |
| 004 | Zero Emojis | ACEITO |
| 005 | Anonimato (sem menção a IA externa) | ACEITO |
| 006 | PT-BR obrigatório | ACEITO |
| 007 | Gauntlet (1 teste por feature) | ACEITO |
| 008 | Performance KPIs | ACEITO |
| 009 | Acesso Universal (sandbox) | ACEITO |
| 010 | Zero Mocks | ACEITO |
| 011 | Gauntlet Obrigatório | ACEITO |
| 012 | Cobertura 100% fonte TS original | ACEITO |
| 013 | Integração Obrigatória (nada solto) | ACEITO |
| 014 | Testes via Gauntlet (sem pytest) | ACEITO |
| 015 | Documentação para continuidade | ACEITO |
| 016 | Luna no backlog | ACEITO |
| 017 | Scaffold-first | ACEITO |
| 018 | Stubs progressivos | ACEITO |
| 019 | Gauntlet coverage | ACEITO |
| 020 | Testes via run.sh | ACEITO |
| 021 | Dependências opcionais (tree-sitter) | ACEITO |
| 022 | Visão moondream CPU puro | ACEITO |
| 023 | Design System paleta D | ACEITO |
| 024 | Render Layer | ACEITO |
| 025 | Loop de experiência | ACEITO |
| 026 | Agência (usuário sempre controla) | ACEITO (Onda 24) |
| 027 | Progressão & Identidade Nyx | ACEITO (Onda 24) |
| 028 | SBOM Registry | ACEITO |
| 029 | Layout Parity com Claude Code | ACEITO |
| 030 | MCP cliente stdio | ACEITO |
| 031 | Modelo padrão qwen2.5-coder:3b | ACEITO |

## Status atual (2026-05-18, Onda 24)

- **Gauntlet**: 304 testes registrados; `--only rapido` 11/11 APROVADO
- **Smoke**: `boot ok` em ~0.14s (10x abaixo do critério v1.0 de 1.5s)
- **Invariantes**: 14/14 PASS
- **Cockpit**: operacional em `127.0.0.1:11437` com 17 endpoints HTTP + 2 WS
- **Tag v1.0**: aguarda `VALIDATE-FINAL-01-PARTE-2` (screenshots + Docker + 47 commands manuais)
- **Sprints pendentes**: 12 anti-débito materializadas em `dev-journey/06-sprints/producao/` (NYX-AUTO-APPROVE-01, COCKPIT-LIFECYCLE-FIX-01, NYX-NO-HALLUCINATE-TOOL-01, PROJECT-ROOTS-MULTI-01, SHIFT-TAB-CYCLE-01, SUDO-MODE-01, NYX-GSD-CHECKPOINTS-01, NYX-PROMPT-REINJECT-01, NYX-OUTPUT-LIMITS-01, PTY-PERMISSION-FLOW-01, HELP-COVERAGE-FIX-02, VALIDATE-FINAL-01-PARTE-2) + 51 RASCUNHOs SBOM em fila

## Requisitos

- Linux (x86_64)
- Python 3.10+
- GPU NVIDIA (RTX 3050 4GB recomendado)
- ~8 GB de disco (modelos Ollama)

### Dependências opcionais (regeneração de ícones)

Os ícones em `assets/icons/` já vêm pré-renderizados no repositório. Para
regenerar a partir do SVG mestre (`assets/branding/nyx-mono-stencil.svg`):

```bash
sudo apt-get install -y librsvg2-bin icoutils icnsutils
./venv/bin/pip install Pillow cairosvg
```

`librsvg2-bin` provê `rsvg-convert`; `icoutils` provê `icotool` (favicon.ico
multi-resolução); `icnsutils` provê `png2icns` (bundle macOS `.icns`).

## Branding

A identidade visual do Nyx é a logo **Mono Stencil**: hastes verticais do N
mais diagonal interrompida (efeito stencil), com pupila central violeta
(`#BD93F9`) sobre disco gradiente. Arquivos em:

- `assets/branding/nyx-mono-stencil.svg` -- mestre 256x256 colorido
- `assets/branding/nyx-mono-stencil-symbolic.svg` -- monocromático 16x16 (currentColor)
- `assets/branding/nyx-mono-stencil-light.svg` -- variante para fundo claro
- `assets/icons/favicon/favicon.ico` -- bundle 16/32/48/64/256
- `assets/icons/hicolor/<size>x<size>/apps/nyx.png` -- Linux app menu (XDG)
- `assets/icons/tray/nyx-tray-*.png` -- system tray (StatusNotifier)
- `assets/icons/dock/nyx-dock-*.png` -- dock/launcher (64..1024)
- `assets/icons/macos/nyx.icns` -- bundle macOS
- `assets/icons/windows/nyx.ico` -- ícone Windows multi-res

A FASE 12 do `install.sh` copia ícones para `~/.local/share/icons/hicolor/`
e o `.desktop` para `~/.local/share/applications/`, com cache atualizado
via `gtk-update-icon-cache` e `update-desktop-database` quando presentes.

## Estrutura

```
nyx/
  cli.py               # REPL + modo headless + prompt-toolkit
  cli_helpers.py       # Helpers extraídos do cli.py (INFRA-CLI-SPLIT-01)
  proxy.py             # Proxy think=false + num_predict adaptativo
  agent/
    loop/              # AgentLoop split (_core + _iteration)
    parser.py          # ActionParser (7 níveis)
    banner.py          # 3 modos (compact/wide/neofetch)
    commands/          # 61 slash commands (incl. /aesthetic, /cancel)
    output.py          # Rich + theme_manager
    tools/             # 35 tools registradas
    services/          # 14 services (incl. hook_runtime, plugin_manager, mcp_client)
  cockpit/             # FastAPI server local (COCKPIT-01..05)
    server.py          # 17 endpoints HTTP + 2 WS
    pty_bridge.py      # PTY bridge para terminal embedded
    evidencia.py       # Captura PNG por feature (rotação 5)
    static/            # index.html (dashboard), terminal.html (xterm.js)
    static/vendor/     # xterm.js 5.3.0 + HTMX 1.9 + Alpine.js 3.13 vendored
  themes/
    design_tokens.py             # Paleta D (ADR-023)
    design_tokens_extended.py    # 6 aesthetics x 7 entities (Onda 24)
    theme_manager.py             # Resolve runtime (VL-CLI-CONSUME-01)
  providers/ollama.py
  config/defaults.py   # NYX_AESTHETIC, NYX_ENTITY, COCKPIT_PORT, etc.
scripts/
  gauntlet/nyx_gauntlet.py  # 304 testes; --only fase|feature_id
  menu_wizard.py            # TUI wizard (NYX-MENU-WIZARD-01)
  check_oom.sh              # Diagnóstico OOM (INFRA-OOM-01)
  sprint_invariants.sh      # 14 invariantes
  scaffold.py / sync.py     # Scaffold + verificação
bin/
  nyx-runtime-limits.sh     # ulimit + oom_score_adj (sourced pelo run.sh)
dev-journey/
  03-decisions/       # 32 ADRs
  04-features/        # REGISTRY.yaml (62 features SBOM)
  05-guides/          # MICROCOPY.md, COCKPIT_API.md, etc.
  06-sprints/         # producao/ + concluidos/ + SPRINT_ORDER_MASTER
  07-reports/         # RELATORIO_*.md + proofs/ + evidencia/
  08-templates/       # SPRINT_TEMPLATE_V2 + GAMBIARRAS_POR_SPRINT
novo_layout/          # Mockups de referência visual (HTML/JSX/CSS)
  src/                # 5 aesthetics x 7 entities em JS
  v2_referencias/     # Iteração 2 de design
```


<!-- "Perfeição não é quando não há mais nada para adicionar, mas quando não há mais nada para remover." -- Antoine de Saint-Exupéry -->
