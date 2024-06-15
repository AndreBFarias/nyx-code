#!/bin/bash
# uninstall.sh - Remoção do Nyx-Code
# Remove modelos, venv, binário Ollama, logs e sessões

set -uo pipefail

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

log_ok()   { echo -e "  ${GREEN}[OK]${NC} $1"; }
log_info() { echo -e "  ${CYAN}[INFO]${NC} $1"; }
log_warn() { echo -e "  ${YELLOW}[AVISO]${NC} $1"; }

# --- PARSE FLAGS ------------------------------------------
FULL_REMOVE=0
FORCE=0

while [[ $# -gt 0 ]]; do
    case "$1" in
        --full) FULL_REMOVE=1; shift ;;
        --force|-f) FORCE=1; shift ;;
        *) shift ;;
    esac
done

# --- BANNER -----------------------------------------------
echo ""
echo -e "${MAGENTA}${BOLD}Nyx-Code - Desinstalação${NC}"
echo ""

# --- PARAR OLLAMA SE RODANDO -----------------------------
NYX_OLLAMA_PORT="${NYX_OLLAMA_PORT:-11435}"
PID_FILE="$SCRIPT_DIR/logs/.ollama.pid"

if [ -f "$PID_FILE" ]; then
    PID=$(cat "$PID_FILE" 2>/dev/null)
    if [ -n "$PID" ] && kill -0 "$PID" 2>/dev/null; then
        log_info "Parando Ollama (PID: $PID)..."
        kill "$PID" 2>/dev/null
        wait "$PID" 2>/dev/null || true
        log_ok "Ollama parado"
    fi
    rm -f "$PID_FILE"
fi

# --- LISTAR O QUE SERÁ REMOVIDO --------------------------
echo -e "  Será removido:"

TOTAL_SIZE=0

for ITEM in models venv logs sessions; do
    DIR="$SCRIPT_DIR/$ITEM"
    if [ -d "$DIR" ] && [ "$(ls -A "$DIR" 2>/dev/null)" ]; then
        SIZE=$(du -sh "$DIR" 2>/dev/null | cut -f1)
        echo -e "    ${RED}$ITEM/${NC} ($SIZE)"
    elif [ -d "$DIR" ]; then
        echo -e "    ${RED}$ITEM/${NC} (vazio)"
    fi
done

if [ -x "$SCRIPT_DIR/bin/ollama" ]; then
    SIZE=$(du -sh "$SCRIPT_DIR/bin/ollama" 2>/dev/null | cut -f1)
    echo -e "    ${RED}bin/ollama${NC} ($SIZE)"
fi

if [ "$FULL_REMOVE" -eq 1 ] && [ -f "$SCRIPT_DIR/.env" ]; then
    echo -e "    ${RED}.env${NC}"
fi

echo ""

# --- CONFIRMAÇÃO ------------------------------------------
if [ "$FORCE" -eq 0 ]; then
    read -rp "  Confirmar remoção? [s/N] " CONFIRM
    if [[ ! "$CONFIRM" =~ ^[sS]$ ]]; then
        echo ""
        log_info "Cancelado."
        exit 0
    fi
fi

echo ""

# --- REMOVER ----------------------------------------------
if [ -d "$SCRIPT_DIR/models" ]; then
    rm -rf "$SCRIPT_DIR/models"
    log_ok "models/ removido"
fi

if [ -d "$SCRIPT_DIR/venv" ]; then
    rm -rf "$SCRIPT_DIR/venv"
    log_ok "venv/ removido"
fi

if [ -x "$SCRIPT_DIR/bin/ollama" ]; then
    rm -f "$SCRIPT_DIR/bin/ollama"
    log_ok "bin/ollama removido"
fi

if [ -d "$SCRIPT_DIR/logs" ]; then
    rm -rf "$SCRIPT_DIR/logs"
    log_ok "logs/ removido"
fi

if [ -d "$SCRIPT_DIR/sessions" ]; then
    rm -rf "$SCRIPT_DIR/sessions"
    log_ok "sessions/ removido"
fi

if [ "$FULL_REMOVE" -eq 1 ]; then
    if [ -f "$SCRIPT_DIR/.env" ]; then
        rm -f "$SCRIPT_DIR/.env"
        log_ok ".env removido"
    fi
fi

echo ""
echo -e "${GREEN}${BOLD}Remoção concluída.${NC}"

if [ "$FULL_REMOVE" -eq 0 ]; then
    echo -e "  ${CYAN}Código fonte, configurações e sprints foram mantidos.${NC}"
    echo -e "  Para reinstalar: ${MAGENTA}./install.sh${NC}"
fi
echo ""


# "Destruir é sempre o primeiro passo da criação." -- E. E. Cummings
