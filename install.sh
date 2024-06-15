#!/bin/bash
# install.sh - Instalação completa do Nyx-Code
# Baixa Ollama, cria venv, instala dependências, baixa modelos
# Portável: funciona em qualquer máquina Linux com Python 3.10+

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# --- CORES ------------------------------------------------
if [ -t 1 ]; then
    RED='\033[0;31m'
    GREEN='\033[0;32m'
    YELLOW='\033[0;33m'
    MAGENTA='\033[0;35m'
    CYAN='\033[0;36m'
    BOLD='\033[1m'
    NC='\033[0m'
else
    RED='' GREEN='' YELLOW='' MAGENTA='' CYAN='' BOLD='' NC=''
fi

log_ok()   { echo -e "${GREEN}[OK]${NC} $1"; }
log_info() { echo -e "${CYAN}[INFO]${NC} $1"; }
log_warn() { echo -e "${YELLOW}[AVISO]${NC} $1"; }
log_err()  { echo -e "${RED}[ERRO]${NC} $1"; }
log_step() { echo -e "\n${MAGENTA}${BOLD}==> $1${NC}"; }

# --- VERSÕES -----------------------------------------------
OLLAMA_VERSION="0.13.5"
PYTHON_MIN="3.10"
NYX_OLLAMA_PORT="${NYX_OLLAMA_PORT:-11435}"

# --- BANNER ------------------------------------------------
echo -e "${MAGENTA}${BOLD}"
echo "  _   _                ____          _      "
echo " | \\ | |_   ___  __   / ___|___   __| | ___ "
echo " |  \\| | | | \\ \\/ /  | |   / _ \\ / _\` |/ _ \\"
echo " | |\\  | |_| |>  <   | |__| (_) | (_| |  __/"
echo " |_| \\_|\\__, /_/\\_\\   \\____\\___/ \\__,_|\\___|"
echo "        |___/                                "
echo -e "${NC}"
echo -e "${CYAN}Instalador Nyx-Code${NC}"
echo ""

# --- 1. DETECTAR SO E ARQUITETURA -------------------------
log_step "Detectando sistema"

OS="$(uname -s)"
ARCH="$(uname -m)"

if [ "$OS" != "Linux" ]; then
    log_err "Sistema operacional não suportado: $OS (apenas Linux)"
    exit 1
fi

case "$ARCH" in
    x86_64)  OLLAMA_ARCH="amd64" ;;
    aarch64) OLLAMA_ARCH="arm64" ;;
    *)
        log_err "Arquitetura não suportada: $ARCH"
        exit 1
        ;;
esac

log_ok "Sistema: $OS $ARCH (ollama-linux-$OLLAMA_ARCH)"

# --- 2. VERIFICAR PYTHON ----------------------------------
log_step "Verificando Python"

if ! command -v python3 &> /dev/null; then
    log_err "Python3 não encontrado. Instale Python >= $PYTHON_MIN"
    exit 1
fi

PYTHON_VERSION="$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')"
PYTHON_MAJOR="$(echo "$PYTHON_VERSION" | cut -d. -f1)"
PYTHON_MINOR="$(echo "$PYTHON_VERSION" | cut -d. -f2)"
MIN_MAJOR="$(echo "$PYTHON_MIN" | cut -d. -f1)"
MIN_MINOR="$(echo "$PYTHON_MIN" | cut -d. -f2)"

if [ "$PYTHON_MAJOR" -lt "$MIN_MAJOR" ] || { [ "$PYTHON_MAJOR" -eq "$MIN_MAJOR" ] && [ "$PYTHON_MINOR" -lt "$MIN_MINOR" ]; }; then
    log_err "Python $PYTHON_VERSION encontrado, mas >= $PYTHON_MIN é necessário"
    exit 1
fi

log_ok "Python $PYTHON_VERSION"

# --- 3. CRIAR DIRETÓRIOS ---------------------------------
log_step "Criando diretórios"

for DIR in models logs sessions bin; do
    mkdir -p "$SCRIPT_DIR/$DIR"
done

log_ok "Diretórios criados: models/, logs/, sessions/, bin/"

# --- 4. BAIXAR OLLAMA ------------------------------------
log_step "Baixando Ollama $OLLAMA_VERSION"

OLLAMA_BIN="$SCRIPT_DIR/bin/ollama"
OLLAMA_URL="https://github.com/ollama/ollama/releases/download/v${OLLAMA_VERSION}/ollama-linux-${OLLAMA_ARCH}"

if [ -f "$OLLAMA_BIN" ]; then
    EXISTING_VERSION=$("$OLLAMA_BIN" --version 2>&1 | grep -oP '\d+\.\d+\.\d+' || echo "desconhecida")
    log_info "Ollama já existe: versão $EXISTING_VERSION"
    read -rp "  Baixar novamente? [s/N] " REDOWNLOAD
    if [[ ! "$REDOWNLOAD" =~ ^[sS]$ ]]; then
        log_info "Mantendo binário existente"
    else
        log_info "Baixando de $OLLAMA_URL"
        curl -fsSL -o "$OLLAMA_BIN" "$OLLAMA_URL"
        chmod +x "$OLLAMA_BIN"
        log_ok "Ollama $OLLAMA_VERSION baixado"
    fi
else
    log_info "Baixando de $OLLAMA_URL"
    curl -fsSL -o "$OLLAMA_BIN" "$OLLAMA_URL"
    chmod +x "$OLLAMA_BIN"
    log_ok "Ollama $OLLAMA_VERSION baixado para bin/ollama"
fi

# --- 5. CRIAR VENV ----------------------------------------
log_step "Configurando ambiente virtual Python"

if [ -d "$SCRIPT_DIR/venv" ]; then
    log_info "venv já existe"
    read -rp "  Recriar? [s/N] " RECREATE
    if [[ "$RECREATE" =~ ^[sS]$ ]]; then
        rm -rf "$SCRIPT_DIR/venv"
        python3 -m venv "$SCRIPT_DIR/venv"
        log_ok "venv recriado"
    fi
else
    python3 -m venv "$SCRIPT_DIR/venv"
    log_ok "venv criado"
fi

log_info "Instalando dependências..."
"$SCRIPT_DIR/venv/bin/pip" install --quiet --upgrade pip
"$SCRIPT_DIR/venv/bin/pip" install --quiet -r "$SCRIPT_DIR/requirements.txt"
log_ok "Dependências instaladas"

# --- 6. BAIXAR MODELOS ------------------------------------
log_step "Baixando modelos via Ollama"

export OLLAMA_HOST="127.0.0.1:${NYX_OLLAMA_PORT}"
export OLLAMA_MODELS="$SCRIPT_DIR/models"

log_info "Iniciando Ollama temporário na porta $NYX_OLLAMA_PORT..."
"$OLLAMA_BIN" serve > "$SCRIPT_DIR/logs/ollama_install.log" 2>&1 &
OLLAMA_PID=$!

cleanup_ollama() {
    if kill -0 "$OLLAMA_PID" 2>/dev/null; then
        kill "$OLLAMA_PID" 2>/dev/null
        wait "$OLLAMA_PID" 2>/dev/null || true
    fi
}
trap cleanup_ollama EXIT

TIMEOUT=30
ELAPSED=0
while ! curl -sf "http://${OLLAMA_HOST}/api/version" > /dev/null 2>&1; do
    sleep 1
    ELAPSED=$((ELAPSED + 1))
    if [ "$ELAPSED" -ge "$TIMEOUT" ]; then
        log_err "Ollama não iniciou em ${TIMEOUT}s"
        cat "$SCRIPT_DIR/logs/ollama_install.log"
        exit 1
    fi
done
log_ok "Ollama pronto (${ELAPSED}s)"

MODELS=("qwen2.5-coder:3b" "qwen2.5-coder:7b")
for MODEL in "${MODELS[@]}"; do
    if "$OLLAMA_BIN" list 2>/dev/null | grep -q "$MODEL"; then
        log_info "$MODEL já baixado"
    else
        log_info "Baixando $MODEL (pode demorar)..."
        if "$OLLAMA_BIN" pull "$MODEL"; then
            log_ok "$MODEL baixado"
        else
            log_warn "Falha ao baixar $MODEL (pode ser baixado depois via run.sh)"
        fi
    fi
done

log_info "Parando Ollama temporário..."
cleanup_ollama
trap - EXIT

# --- 7. GERAR .env ----------------------------------------
log_step "Configuração"

if [ ! -f "$SCRIPT_DIR/.env" ]; then
    cp "$SCRIPT_DIR/.env.example" "$SCRIPT_DIR/.env"
    log_ok ".env criado a partir de .env.example"
else
    log_info ".env já existe, mantendo"
fi

# --- 8. VERIFICAÇÃO DE SAÚDE ------------------------------
log_step "Verificação final"

CHECKS_OK=0
CHECKS_TOTAL=4

# Binário Ollama
if [ -x "$OLLAMA_BIN" ]; then
    log_ok "Ollama binário: $(du -h "$OLLAMA_BIN" | cut -f1)"
    CHECKS_OK=$((CHECKS_OK + 1))
else
    log_err "Ollama binário não encontrado"
fi

# Modelos
MODELS_DIR="$SCRIPT_DIR/models"
if [ -d "$MODELS_DIR" ] && [ "$(ls -A "$MODELS_DIR" 2>/dev/null)" ]; then
    MODEL_SIZE="$(du -sh "$MODELS_DIR" | cut -f1)"
    log_ok "Modelos: $MODEL_SIZE em $MODELS_DIR"
    CHECKS_OK=$((CHECKS_OK + 1))
else
    log_warn "Diretório de modelos vazio"
fi

# venv
if [ -f "$SCRIPT_DIR/venv/bin/python" ]; then
    VENV_PYTHON="$("$SCRIPT_DIR/venv/bin/python" --version 2>&1)"
    log_ok "venv: $VENV_PYTHON"
    CHECKS_OK=$((CHECKS_OK + 1))
else
    log_err "venv não funcional"
fi

# Deps Python
if "$SCRIPT_DIR/venv/bin/python" -c "import rich, prompt_toolkit, httpx, pydantic, dotenv" 2>/dev/null; then
    log_ok "Dependências Python: todas instaladas"
    CHECKS_OK=$((CHECKS_OK + 1))
else
    log_err "Dependências Python faltando"
fi

echo ""
if [ "$CHECKS_OK" -eq "$CHECKS_TOTAL" ]; then
    echo -e "${GREEN}${BOLD}Instalação completa! ($CHECKS_OK/$CHECKS_TOTAL)${NC}"
    echo -e "Execute ${MAGENTA}./run.sh${NC} para iniciar o Nyx-Code."
else
    echo -e "${YELLOW}${BOLD}Instalação parcial ($CHECKS_OK/$CHECKS_TOTAL)${NC}"
    echo -e "Verifique os erros acima."
fi
echo ""


# "Não há caminho para a liberdade; a liberdade é o caminho." -- Mahatma Gandhi
