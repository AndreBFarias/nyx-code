#!/bin/bash
# uninstall.sh - Remoção do Nyx-Code
# Remove modelos, venv, binário Ollama, logs e sessões

set -uo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# --- CORES (Paleta Nyx) ------------------------------------
if [ -t 1 ]; then
    PRIMARY='\033[38;2;0;212;170m'      # #00D4AA - cor principal Nyx
    ACCENT='\033[38;2;232;232;232m'     # #E8E8E8 - destaque
    GREEN='\033[38;2;0;212;170m'        # #00D4AA - sucesso
    ORANGE='\033[38;2;255;184;108m'     # #FFB86C - avisos
    RED='\033[38;2;255;107;107m'        # #FF6B6B - erros
    COMMENT='\033[38;2;108;122;137m'    # #6C7A89 - secundário
    FG='\033[38;2;232;232;232m'         # #E8E8E8 - texto
    BOLD='\033[1m'
    NC='\033[0m'
else
    PRIMARY='' ACCENT='' GREEN='' ORANGE='' RED='' COMMENT='' FG='' BOLD='' NC=''
fi

log_ok()   { echo -e "  ${GREEN}[nyx]${NC} $1"; }
log_nyx()  { echo -e "  ${PRIMARY}[nyx]${NC} $1"; }
log_warn() { echo -e "  ${ORANGE}[nyx]${NC} $1"; }

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
echo -e "${PRIMARY}${BOLD}Nyx-Code - Desinstalação${NC}"
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

# Ícones XDG + desktop entry (BRANDING-MONO-STENCIL)
XDG_ICONS="${XDG_DATA_HOME:-$HOME/.local/share}/icons/hicolor"
XDG_APPS="${XDG_DATA_HOME:-$HOME/.local/share}/applications"
if [ -f "$XDG_APPS/nyx.desktop" ]; then
    rm -f "$XDG_APPS/nyx.desktop"
    log_ok "desktop entry removido"
fi
for size in 16 22 24 32 48 64 128 256 512; do
    rm -f "$XDG_ICONS/${size}x${size}/apps/nyx.png"
done
rm -f "$XDG_ICONS/scalable/apps/nyx.svg" "$XDG_ICONS/symbolic/apps/nyx-symbolic.svg"
if command -v gtk-update-icon-cache >/dev/null 2>&1; then
    gtk-update-icon-cache -q -t "$XDG_ICONS" 2>/dev/null || true
fi
if command -v update-desktop-database >/dev/null 2>&1; then
    update-desktop-database -q "$XDG_APPS" 2>/dev/null || true
fi
log_ok "ícones XDG removidos"

echo ""
echo -e "${GREEN}${BOLD}Remoção concluída.${NC}"

if [ "$FULL_REMOVE" -eq 0 ]; then
    echo -e "  ${ACCENT}Código fonte, configurações e sprints foram mantidos.${NC}"
    echo -e "  Para reinstalar: ${PRIMARY}./install.sh${NC}"
fi
echo ""


# "Destruir é sempre o primeiro passo da criação." -- E. E. Cummings
