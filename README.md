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
./install.sh          # Ollama, venv, modelos (~8GB)
./run.sh              # Inicia com qwen2.5-coder:3b (default, ADR-031)
./run.sh --7b         # qwen2.5-coder:7b
./run.sh --debug      # Logs detalhados
./run.sh --gauntlet   # Validação completa
```

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

## Tools (34 registradas -- todas funcionais)

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

## Commands (47 registrados)

| Categoria | Commands |
|-----------|----------|
| Geral | /help, /quit, /clear, /status |
| Código | /explain, /plan, /test, /summary |
| Git | /commit, /diff, /review, /branch, /issue, /pr, /rewind |
| Sistema | /doctor, /model, /config, /env, /permissions, /hooks, /theme |
| Sessão | /compact, /context, /session, /resume, /export, /copy, /stats, /usage |
| Execução | /tasks, /skills, /files |
| Projeto | /add-dir, /init, /version |
| Debug | /trace, /ctx-viz, /break-cache |
| Memória | /memory |
| Avançado | /btw, /pr-comments |
| Root | /advisor, /brief-cmd, /commit-push-pr, /insights, /security-review |

## Services (10)

tokens, compact, hooks, memory, summary, suggestions, analytics, diagnostics, logging_service, tool_use_summary

## ADRs (20)

| # | Título |
|---|--------|
| 001 | Local First -- 100% offline |
| 002 | Proxy think=false |
| 003 | VRAM Management (RTX 3050 4GB) |
| 004 | Zero Emojis |
| 005 | Anonimato (sem menção a IA) |
| 006 | PT-BR obrigatório |
| 007 | Gauntlet (1 teste por feature) |
| 008 | Performance KPIs |
| 009 | Acesso Universal |
| 010 | Zero Mocks |
| 011 | Gauntlet Obrigatório |
| 012 | Cobertura 100% fonte TS original |
| 013 | Integração Obrigatória (nada solto) |
| 014 | Testes via Gauntlet (sem pytest) |
| 015 | Documentação para continuidade |
| 016 | Luna no backlog |
| 017 | Scaffold-first |
| 018 | Stubs progressivos |
| 019 | Gauntlet coverage |
| 020 | Testes via run.sh |

## Requisitos

- Linux (x86_64)
- Python 3.10+
- GPU NVIDIA (RTX 3050 4GB recomendado)
- ~8 GB de disco (modelos Ollama)

## Estrutura

```
nyx/
  cli.py             # REPL + modo headless + prompt-toolkit
  proxy.py           # Proxy think=false
  agent/
    loop.py          # AgentLoop (plan-execute-observe)
    parser.py        # ActionParser (7 níveis)
    session.py       # CodeSession
    commands.py      # 61 slash commands
    completer.py     # Tab completion
    output.py        # Rich output + spinner
    tools/
      registry.py    # 35 tools registradas
      base.py        # RegisteredTool + ToolDef
      [34 arquivos]
    services/
      [10 arquivos]
  providers/
    ollama.py        # OllamaProvider
  context/
    project.py       # Detecção de projeto
scripts/
  gauntlet/
    nyx_gauntlet.py  # Validação automatizada
  scaffold.py        # Gerador de componentes
  sync.py            # Verificação de consistência
dev-journey/
  PORT_STATUS.md     # Mapeamento 1:1 fonte TS -> Nyx
  03-decisions/      # 20 ADRs
  06-sprints/        # Sprint files + SPRINT_ORDER_MASTER
```


<!-- "Perfeição não é quando não há mais nada para adicionar, mas quando não há mais nada para remover." -- Antoine de Saint-Exupéry -->
