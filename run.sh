#!/bin/bash
# run.sh - Nyx-Code Launcher
# Gerencia Ollama dedicado, venv, modelos e a aplicação
# Estilo run_luna.sh: cuida de TUDO

set -uo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# ─── CORES ────────────────────────────────────────────────
if [ -t 1 ]; then
    RED='\033[0;31m'
    GREEN='\033[0;32m'
    YELLOW='\033[0;33m'
    MAGENTA='\033[0;35m'
    CYAN='\033[0;36m'
    BOLD='\033[1m'
    DIM='\033[2m'
    NC='\033[0m'
else
    RED='' GREEN='' YELLOW='' MAGENTA='' CYAN='' BOLD='' DIM='' NC=''
fi

log_ok()   { echo -e "  ${GREEN}[OK]${NC} $1"; }
log_info() { echo -e "  ${CYAN}[INFO]${NC} $1"; }
log_warn() { echo -e "  ${YELLOW}[AVISO]${NC} $1"; }
log_err()  { echo -e "  ${RED}[ERRO]${NC} $1"; }

# ─── CARREGAR .env ────────────────────────────────────────
if [ -f "$SCRIPT_DIR/.env" ]; then
    set -a
    source "$SCRIPT_DIR/.env"
    set +a
fi

# ─── TIMEOUTS ─────────────────────────────────────────────
CURL_TIMEOUT="${NYX_CURL_TIMEOUT:-10}"
CURL_CONNECT_TIMEOUT=3
OLLAMA_START_TIMEOUT="${NYX_OLLAMA_START_TIMEOUT:-30}"
NYX_OLLAMA_PORT="${NYX_OLLAMA_PORT:-11435}"
NYX_OLLAMA_HOST="${NYX_OLLAMA_HOST:-127.0.0.1}:${NYX_OLLAMA_PORT}"

# ─── PARSE FLAGS ──────────────────────────────────────────
MODEL="${NYX_MODEL:-qwen2.5-coder:3b}"
DEBUG=0
HEADLESS=0
EXTRA_ARGS=()

while [[ $# -gt 0 ]]; do
    case "$1" in
        --3b)
            MODEL="qwen2.5-coder:3b"
            shift ;;
        --7b)
            MODEL="qwen2.5-coder:7b"
            shift ;;
        --model)
            MODEL="$2"
            shift 2 ;;
        --port)
            NYX_OLLAMA_PORT="$2"
            NYX_OLLAMA_HOST="${NYX_OLLAMA_HOST%%:*}:${NYX_OLLAMA_PORT}"
            shift 2 ;;
        --debug)
            DEBUG=1
            shift ;;
        --headless)
            HEADLESS=1
            shift ;;
        *)
            EXTRA_ARGS+=("$1")
            shift ;;
    esac
done

# ─── VARIÁVEIS OLLAMA ────────────────────────────────────
export OLLAMA_HOST="$NYX_OLLAMA_HOST"
export OLLAMA_MODELS="$SCRIPT_DIR/models"

OLLAMA_BIN="$SCRIPT_DIR/bin/ollama"
OLLAMA_PID_FILE="$SCRIPT_DIR/logs/.ollama.pid"
NYX_STARTED_OLLAMA=0

# ─── VALIDAÇÕES ───────────────────────────────────────────
validate() {
    local errors=0

    if [ ! -f "$SCRIPT_DIR/venv/bin/python" ]; then
        log_err "venv não encontrado. Execute ${MAGENTA}./install.sh${NC} primeiro."
        errors=$((errors + 1))
    fi

    if [ ! -x "$OLLAMA_BIN" ]; then
        log_err "Ollama não encontrado em bin/ollama. Execute ${MAGENTA}./install.sh${NC} primeiro."
        errors=$((errors + 1))
    fi

    if [ "$errors" -gt 0 ]; then
        exit 1
    fi
}

# ─── GERENCIAMENTO OLLAMA ─────────────────────────────────
start_ollama() {
    if curl -sf "http://${NYX_OLLAMA_HOST}/api/version" > /dev/null 2>&1; then
        log_ok "Ollama já rodando na porta $NYX_OLLAMA_PORT"
        return 0
    fi

    log_info "Iniciando Ollama na porta $NYX_OLLAMA_PORT..."
    mkdir -p "$SCRIPT_DIR/logs"

    "$OLLAMA_BIN" serve >> "$SCRIPT_DIR/logs/ollama.log" 2>&1 &
    local pid=$!
    echo "$pid" > "$OLLAMA_PID_FILE"
    NYX_STARTED_OLLAMA=1

    local elapsed=0
    while ! curl -sf "http://${NYX_OLLAMA_HOST}/api/version" > /dev/null 2>&1; do
        sleep 1
        elapsed=$((elapsed + 1))
        if [ "$elapsed" -ge "$OLLAMA_START_TIMEOUT" ]; then
            log_err "Ollama não iniciou em ${OLLAMA_START_TIMEOUT}s"
            log_err "Verifique logs/ollama.log"
            exit 1
        fi
    done

    log_ok "Ollama pronto (PID: $pid, ${elapsed}s)"
}

stop_ollama() {
    if [ "$NYX_STARTED_OLLAMA" -eq 1 ] && [ -f "$OLLAMA_PID_FILE" ]; then
        local pid
        pid=$(cat "$OLLAMA_PID_FILE" 2>/dev/null)
        if [ -n "$pid" ] && kill -0 "$pid" 2>/dev/null; then
            log_info "Parando Ollama (PID: $pid)..."
            kill "$pid" 2>/dev/null
            wait "$pid" 2>/dev/null || true
        fi
        rm -f "$OLLAMA_PID_FILE"
    fi
}

check_model() {
    if ! "$OLLAMA_BIN" list 2>/dev/null | grep -q "$MODEL"; then
        log_warn "Modelo $MODEL não encontrado localmente"
        log_info "Baixando $MODEL..."
        if ! "$OLLAMA_BIN" pull "$MODEL"; then
            log_err "Falha ao baixar $MODEL"
            exit 1
        fi
        log_ok "$MODEL baixado"
    else
        log_ok "Modelo: $MODEL"
    fi
}

# ─── CONFIGURAÇÃO VRAM (7b) ──────────────────────────────
configure_vram() {
    if [[ "$MODEL" != *"7b"* ]]; then
        return 0
    fi

    local vram_max="${NYX_VRAM_MAX:-2.5}"
    log_info "Modelo 7b detectado. Limite VRAM: ${vram_max}GB"

    if command -v nvidia-smi &> /dev/null; then
        local vram_total
        vram_total=$(nvidia-smi --query-gpu=memory.total --format=csv,noheader,nounits 2>/dev/null | head -1)
        if [ -n "$vram_total" ]; then
            log_info "GPU: ${vram_total}MiB VRAM total"
        fi
    fi

    log_info "num_gpu=18 (~2.4GB VRAM, restante em CPU)"
}

# ─── BANNER ───────────────────────────────────────────────
show_banner() {
    if [ "$HEADLESS" -eq 1 ]; then
        return 0
    fi

    echo ""
    echo -e "${MAGENTA}${BOLD}"
    echo "  ╔══════════════════════════════════════╗"
    echo "  ║                                      ║"
    echo "  ║    _   _                             ║"
    echo "  ║   | \\ | |_   ___  __                 ║"
    echo "  ║   |  \\| | | | \\ \\/ /                 ║"
    echo "  ║   | |\\  | |_| |>  <                  ║"
    echo "  ║   |_| \\_|\\__, /_/\\_\\                 ║"
    echo "  ║          |___/                       ║"
    echo "  ║                                      ║"
    echo "  ║         C O D E   A G E N T          ║"
    echo "  ║                                      ║"
    echo "  ╚══════════════════════════════════════╝"
    echo -e "${NC}"
    echo -e "  ${DIM}Modelo: ${NC}${CYAN}$MODEL${NC}"
    echo -e "  ${DIM}Ollama: ${NC}${CYAN}http://${NYX_OLLAMA_HOST}${NC}"
    if [ "$DEBUG" -eq 1 ]; then
        echo -e "  ${DIM}Debug:  ${NC}${YELLOW}ativado${NC}"
    fi
    echo ""
}

# ─── CLEANUP ──────────────────────────────────────────────
cleanup() {
    echo ""
    log_info "Encerrando Nyx-Code..."
    stop_ollama
    log_ok "Encerrado."
}

trap cleanup EXIT SIGINT SIGTERM

# ═══════════════════════════════════════════════════════════
# EXECUÇÃO PRINCIPAL
# ═══════════════════════════════════════════════════════════

validate
start_ollama
check_model
configure_vram
show_banner

# Construir argumentos do Python
PYTHON_ARGS=("--model" "$MODEL" "--port" "$NYX_OLLAMA_PORT")
if [ "$DEBUG" -eq 1 ]; then
    PYTHON_ARGS+=("--debug")
fi
if [ "$HEADLESS" -eq 1 ]; then
    PYTHON_ARGS+=("--headless")
fi
PYTHON_ARGS+=("${EXTRA_ARGS[@]+"${EXTRA_ARGS[@]}"}")

# Iniciar Nyx-Code
"$SCRIPT_DIR/venv/bin/python" "$SCRIPT_DIR/main.py" "${PYTHON_ARGS[@]}"
EXIT_CODE=$?

exit "$EXIT_CODE"


# "O segredo da liberdade é a coragem." -- Péricles
