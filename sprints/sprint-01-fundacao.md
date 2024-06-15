# Sprint 1: Fundacao e Infraestrutura

**Objetivo:** Projeto rodando na maquina local com Ollama dedicado, modelos baixados,
scripts de lifecycle completos, repo no GitHub.

---

## 1.1 Criar repositorio

```bash
cd ~/Desenvolvimento/Nyx-Code
git init
git config user.email "[REDACTED]"
git config user.name "Andre Farias"
gh repo create nyx-code --public --source=. --push
```

- .gitignore robusto (venv/, models/, bin/ollama, __pycache__/, .env, logs/, *.pyc)
- README.md inicial do projeto
- Push inicial

---

## 1.2 install.sh

Instalacao completa, portavel, idempotente.

```
install.sh
|-- Detectar SO e arquitetura (Linux x86_64, arm64)
|-- Baixar binario Ollama para ./bin/ollama
|   \-- curl -fsSL https://github.com/ollama/ollama/releases/download/v0.13.5/ollama-linux-amd64 -o ./bin/ollama
|-- chmod +x ./bin/ollama
|-- Criar venv Python (./venv/)
|   \-- python3 -m venv venv && source venv/bin/activate && pip install -r requirements.txt
|-- Criar diretorios: models/, logs/, sessions/
|-- Iniciar Ollama temporario para baixar modelos
|   |-- OLLAMA_HOST=127.0.0.1:11435 OLLAMA_MODELS=./models ./bin/ollama serve &
|   |-- Aguardar Ollama pronto (health check loop)
|   |-- ./bin/ollama pull qwen2.5-coder:3b
|   |-- ./bin/ollama pull qwen2.5-coder:7b
|   \-- Parar Ollama temporario
|-- Gerar .env a partir de .env.example (se nao existir)
\-- Verificacao de saude final
    |-- Ollama binario OK
    |-- Modelos baixados OK
    |-- venv OK
    \-- Python deps OK
```

**Portavel:** funciona em qualquer maquina Linux com Python 3.10+ e GPU/CPU.

---

## 1.3 run.sh (estilo run_luna.sh)

Script master que cuida de TUDO. Baseado no padrao do run_luna.sh.

### Estrutura

```bash
#!/bin/bash
# run.sh - Nyx-Code Launcher
# Gerencia Ollama dedicado, venv, modelos e a aplicacao

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# --- CORES ------------------------------------------------
# Paleta Nyx: roxo/violeta como cor primaria
if [ -t 1 ]; then
    RED='\033[0;31m'
    GREEN='\033[0;32m'
    YELLOW='\033[0;33m'
    MAGENTA='\033[0;35m'    # Cor primaria Nyx
    CYAN='\033[0;36m'
    BOLD='\033[1m'
    NC='\033[0m'
fi

# --- TIMEOUTS ---------------------------------------------
CURL_TIMEOUT="${CURL_TIMEOUT:-10}"
CURL_CONNECT_TIMEOUT="${CURL_CONNECT_TIMEOUT:-3}"
OLLAMA_START_TIMEOUT="${OLLAMA_START_TIMEOUT:-30}"
NYX_OLLAMA_PORT="${NYX_OLLAMA_PORT:-11435}"
NYX_OLLAMA_HOST="127.0.0.1:${NYX_OLLAMA_PORT}"

# --- VALIDACOES -------------------------------------------
# 1. Verificar venv
# 2. Verificar binario Ollama local
# 3. Verificar modelos baixados
# 4. Carregar .env

# --- OLLAMA DEDICADO --------------------------------------
# 1. Verificar se ja tem instancia Nyx rodando nessa porta
# 2. Se nao, iniciar: OLLAMA_HOST=... OLLAMA_MODELS=./models ./bin/ollama serve &
# 3. Health check loop (max 30s)
# 4. Verificar modelos disponiveis

# --- SELECAO DE MODELO ------------------------------------
# Flags: --3b (padrao), --7b
# Se --7b: configurar num_gpu para max 2.5GB VRAM
# Criar Modelfile temporario se necessario

# --- INICIAR NYX-CODE ------------------------------------
# source venv/bin/activate
# python main.py --model $MODEL --port $NYX_OLLAMA_PORT $@

# --- CLEANUP ----------------------------------------------
# trap para parar Ollama ao sair (SIGINT, SIGTERM, EXIT)
# Limpar Modelfiles temporarios
# Log de sessao
```

### Funcionalidades

- Banner ASCII da Nyx na inicializacao
- Cores ANSI (roxo/violeta como primaria, estilo Nyx)
- Timeouts configuraveis via .env
- Verificacao de pre-requisitos (venv, ollama, modelos)
- Ollama dedicado: inicia, monitora, para automaticamente
- Selecao de modelo via flags (--3b, --7b)
- Configuracao automatica de VRAM para 7b (num_gpu layers)
- Trap para cleanup gracioso (para Ollama ao sair)
- Logging para ./logs/
- Modo debug (--debug)
- Flags extras: --port, --model, --headless (para integracao Luna)

---

## 1.4 uninstall.sh

```
uninstall.sh
|-- Parar Ollama dedicado se rodando
|-- Remover ./models/ (modelos Ollama)
|-- Remover ./venv/
|-- Remover ./bin/ollama
|-- Remover ./logs/, ./sessions/
|-- Remover .env (com confirmacao)
|-- --full: remover diretorio inteiro
\-- Confirmacao interativa antes de executar
```

---

## 1.5 Configuracao 7b para max 2.5GB VRAM

O qwen2.5-coder:7b em q4_K_M usa ~4.7GB VRAM (todas as layers na GPU).
Para limitar a 2.5GB:

```
# Modelfile customizado
FROM qwen2.5-coder:7b
PARAMETER num_gpu 18
# ~18 de ~32 layers na GPU = ~2.4GB VRAM
# Restante roda em CPU (mais lento, mas funcional)
```

Alternativa: detectar VRAM disponivel e calcular num_gpu automaticamente no run.sh.

---

## 1.6 Estrutura de pastas

```
Nyx-Code/
|-- bin/                    # Binario Ollama local
|   \-- ollama
|-- models/                 # OLLAMA_MODELS (modelos ficam aqui)
|-- nyx/                    # Pacote Python principal
|   \-- __init__.py
|-- sprints/                # Documentacao de sprints
|-- reference/              # Fonte openclaude para consulta
|   |-- cli.mjs
|   |-- package.json
|   \-- README.md
|-- tests/
|-- logs/                   # Logs rotacionados
|-- sessions/               # Sessoes persistidas
|-- .env.example
|-- .gitignore
|-- install.sh
|-- uninstall.sh
|-- run.sh
|-- main.py
|-- pyproject.toml
|-- requirements.txt
\-- README.md
```

---

## 1.7 Mover openclaude para reference/

- Mover `bin/openclaude`, `dist/`, `package.json`, `README.md` original -> `reference/`
- Limpar raiz para o projeto Python

---

## Verificacao

- [ ] `./install.sh` baixa Ollama, cria venv, baixa modelos
- [ ] `./run.sh` inicia Ollama na porta 11435 e abre interface basica
- [ ] `./run.sh --3b` funciona com qwen2.5-coder:3b
- [ ] `./run.sh --7b` funciona com 7b usando max 2.5GB VRAM
- [ ] `./uninstall.sh` limpa tudo
- [ ] Repo no GitHub com push funcionando
- [ ] Funciona em maquina limpa (sem Ollama global)
- [ ] `./run.sh --debug` mostra logs detalhados
