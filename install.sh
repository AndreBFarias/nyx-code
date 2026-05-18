#!/usr/bin/env bash
# ===========================================================
# Nyx-Code -- Instalação idempotente local-first (DEPLOY-01A)
# Rode múltiplas vezes sem efeito colateral. Sem Docker, sem README,
# sem fase Gauntlet -- escopo de DEPLOY-01B.
# ===========================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# --- CORES (paleta Nyx) ------------------------------------
if [ -t 1 ]; then
    PRIMARY='\033[38;2;0;212;170m'
    SECONDARY='\033[38;2;108;122;137m'
    ACCENT='\033[38;2;232;232;232m'
    GREEN='\033[38;2;0;212;170m'
    ORANGE='\033[38;2;255;184;108m'
    RED='\033[38;2;255;107;107m'
    BOLD='\033[1m'
    NC='\033[0m'
else
    PRIMARY='' SECONDARY='' ACCENT='' GREEN='' ORANGE='' RED='' BOLD='' NC=''
fi

# --- FLAGS -------------------------------------------------
NO_VISION=0
NO_KITTY=0
DEV_MODE=0
DRY_RUN=0
NO_PROMPT=0

while [[ $# -gt 0 ]]; do
    case "$1" in
        --no-vision) NO_VISION=1; shift ;;
        --no-kitty)  NO_KITTY=1; shift ;;
        --dev)       DEV_MODE=1; shift ;;
        --dry-run)   DRY_RUN=1; shift ;;
        --no-prompt) NO_PROMPT=1; shift ;;
        -h|--help)
            cat <<EOF
Uso: ./install.sh [flags]

Flags:
  --no-vision   Pula download do moondream (sem capacidade de visão)
  --no-kitty    Não pergunta sobre instalar kitty terminal
  --dev         Instala também requirements-dev.txt
  --dry-run     Mostra o que faria sem executar comandos destrutivos
  --no-prompt   Modo não-interativo (CI); usa defaults seguros
  -h, --help    Esta mensagem

11 fases:
  0  Requisitos mínimos (Python >=3.10, distro)
  1  Cria venv (se ausente)
  2  pip install -r requirements.txt
  3  Instala Ollama via script oficial (se ausente)
  4  Pull do modelo padrão (qwen2.5-coder:3b)
  5  Pull moondream (respeita --no-vision)
  6  Instala xclip (respeita pkg manager)
  7  Pergunta sobre kitty (respeita --no-kitty)
  8  chmod +x em run.sh e scripts/*.sh|.py
  9  Smoke test (import nyx via venv)
 10  Controle OOM (chmod bin/nyx-runtime-limits.sh + scripts/check_oom.sh)
 11  Ícones XDG + desktop entry (hicolor + applications)

Variáveis de ambiente:
  NYX_SUDO_PASSWORD   senha sudo para CI/replicação (NÃO commit; lida só em runtime)
  NYX_INSTALL_SKIP_PULL=1   pula 'ollama pull' (uso em Docker, DEPLOY-01B)
EOF
            exit 0
            ;;
        *) echo "Flag desconhecida: $1 (use --help)" >&2; exit 1 ;;
    esac
done

# --- HELPERS -----------------------------------------------
TOTAL=11
print_header() {
    echo -e "${PRIMARY}${BOLD}"
    echo "  _   _                ____          _      "
    echo " | \\ | |_   ___  __   / ___|___   __| | ___ "
    echo " |  \\| | | | \\ \\/ /  | |   / _ \\ / _\` |/ _ \\"
    echo " | |\\  | |_| |>  <   | |__| (_) | (_| |  __/"
    echo " |_| \\_|\\__, /_/\\_\\   \\____\\___/ \\__,_|\\___|"
    echo "        |___/                                "
    echo -e "${NC}"
    echo -e "${ACCENT}Instalador idempotente Nyx-Code (DEPLOY-01A)${NC}"
    if [ $DRY_RUN -eq 1 ]; then
        echo -e "${ORANGE}    [dry-run] nenhum comando destrutivo será executado${NC}"
    fi
    echo ""
}

print_step() { echo -e "${PRIMARY}${BOLD}[$1/$TOTAL]${NC} $2"; }
print_ok()   { echo -e "    ${GREEN}OK${NC}   $1"; }
print_skip() { echo -e "    ${SECONDARY}SKIP${NC} $1"; }
print_err()  { echo -e "    ${RED}ERRO${NC} $1"; }
print_warn() { echo -e "    ${ORANGE}AVISO${NC} $1"; }

have_cmd() { command -v "$1" &>/dev/null; }

detect_pkg_manager() {
    for pm in apt-get dnf pacman zypper; do
        if have_cmd "$pm"; then echo "$pm"; return; fi
    done
    echo ""
}

run_or_skip() {
    # Executa comando ou skip se --dry-run; ecoa sempre o comando.
    local desc="$1"; shift
    if [ $DRY_RUN -eq 1 ]; then
        print_skip "$desc (dry-run: $*)"
        return 0
    fi
    "$@"
}

# INSTALL-SUDO-01: wrapper de sudo que aceita NYX_SUDO_PASSWORD via env var
# (apenas para replicação em outros PCs / CI sem TTY). Default mantém
# comportamento atual (prompt interativo do sudo).
# NUNCA hardcode da senha; SEMPRE via env. Documentado em README.
sudo_run() {
    if [ -n "${NYX_SUDO_PASSWORD:-}" ]; then
        echo "$NYX_SUDO_PASSWORD" | sudo -S -p "" "$@"
    else
        sudo "$@"
    fi
}

ask_or_default() {
    local prompt="$1"; local default_answer="$2"; local out_var="$3"
    if [ $NO_PROMPT -eq 1 ] || [ $DRY_RUN -eq 1 ]; then
        eval "$out_var='$default_answer'"
    else
        read -rp "$prompt" "$out_var"
    fi
}

PKG_MANAGER="$(detect_pkg_manager)"
DEFAULT_MODEL="qwen2.5-coder:3b"
VISION_MODEL="moondream"

print_header

# ===========================================================
# FASE 0 -- Requisitos mínimos
# ===========================================================
print_step 0 "Requisitos mínimos (Python >=3.10, distro)"

if ! have_cmd python3; then
    print_err "python3 não encontrado. Instale Python >= 3.10 antes de continuar."
    exit 1
fi

PY_VER="$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')"
PY_MAJOR="${PY_VER%%.*}"
PY_MINOR="${PY_VER##*.}"
if [ "$PY_MAJOR" -lt 3 ] || { [ "$PY_MAJOR" -eq 3 ] && [ "$PY_MINOR" -lt 10 ]; }; then
    print_err "Python $PY_VER encontrado, mas >= 3.10 é necessário."
    exit 1
fi
print_ok "Python $PY_VER"

if [ -z "$PKG_MANAGER" ]; then
    print_warn "Nenhum gerenciador de pacotes suportado (apt/dnf/pacman/zypper). Fases 6 podem falhar."
else
    print_ok "Distro: gerenciador $PKG_MANAGER"
fi

# ===========================================================
# FASE 1 -- venv
# ===========================================================
print_step 1 "Ambiente virtual Python"

if [ -d "$SCRIPT_DIR/venv" ]; then
    print_skip "venv já existe"
else
    run_or_skip "criar venv" python3 -m venv "$SCRIPT_DIR/venv"
    print_ok "venv criado"
fi

# ===========================================================
# FASE 2 -- pip install
# ===========================================================
print_step 2 "Dependências Python (pip install)"

if [ -f "$SCRIPT_DIR/requirements.txt" ]; then
    run_or_skip "pip upgrade" "$SCRIPT_DIR/venv/bin/pip" install --quiet --upgrade pip
    run_or_skip "pip install -r requirements.txt" \
        "$SCRIPT_DIR/venv/bin/pip" install --quiet -r "$SCRIPT_DIR/requirements.txt"
    [ $DRY_RUN -eq 0 ] && print_ok "requirements.txt instalado"
else
    print_warn "requirements.txt ausente -- pulado"
fi

if [ $DEV_MODE -eq 1 ] && [ -f "$SCRIPT_DIR/requirements-dev.txt" ]; then
    run_or_skip "pip install -r requirements-dev.txt" \
        "$SCRIPT_DIR/venv/bin/pip" install --quiet -r "$SCRIPT_DIR/requirements-dev.txt"
    [ $DRY_RUN -eq 0 ] && print_ok "requirements-dev.txt instalado"
elif [ $DEV_MODE -eq 1 ]; then
    print_warn "--dev passado mas requirements-dev.txt ausente"
fi

# ===========================================================
# FASE 3 -- Ollama (instalar se ausente)
# ===========================================================
print_step 3 "Instalação do Ollama"

if have_cmd ollama; then
    print_skip "ollama já instalado ($(ollama --version 2>&1 | head -1))"
else
    print_warn "ollama ausente -- instalando via script oficial"
    if [ $DRY_RUN -eq 1 ]; then
        print_skip "curl -fsSL https://ollama.com/install.sh | sh (dry-run)"
    else
        if ! curl -fsSL https://ollama.com/install.sh | sh; then
            print_err "Falha ao instalar Ollama. Veja https://ollama.com/download"
            exit 1
        fi
        print_ok "Ollama instalado"
    fi
fi

# ===========================================================
# FASE 4 -- modelo padrão
# ===========================================================
print_step 4 "Modelo padrão ($DEFAULT_MODEL)"

# DEPLOY-01B: NYX_INSTALL_SKIP_PULL=1 pula FASES 4 e 5 quando o ambiente
# nao tem `ollama serve` rodando (ex.: container Docker no Gauntlet).
if [ "${NYX_INSTALL_SKIP_PULL:-0}" = "1" ]; then
    print_skip "NYX_INSTALL_SKIP_PULL=1 -- pull pulado"
elif have_cmd ollama && ollama list 2>/dev/null | awk '{print $1}' | grep -q "^${DEFAULT_MODEL}$"; then
    print_skip "$DEFAULT_MODEL já baixado"
elif ! have_cmd ollama; then
    print_warn "ollama ausente -- pull pulado (rodar novamente após FASE 3)"
else
    run_or_skip "ollama pull $DEFAULT_MODEL" ollama pull "$DEFAULT_MODEL"
    print_ok "$DEFAULT_MODEL baixado"
fi

# ===========================================================
# FASE 5 -- moondream (visão)
# ===========================================================
print_step 5 "Modelo de visão ($VISION_MODEL)"

if [ "${NYX_INSTALL_SKIP_PULL:-0}" = "1" ]; then
    print_skip "NYX_INSTALL_SKIP_PULL=1 -- pull pulado"
elif [ $NO_VISION -eq 1 ]; then
    print_skip "--no-vision passado"
elif have_cmd ollama && ollama list 2>/dev/null | awk '{print $1}' | grep -q "^${VISION_MODEL}"; then
    print_skip "$VISION_MODEL já baixado"
elif ! have_cmd ollama; then
    print_warn "ollama ausente -- pull pulado"
else
    run_or_skip "ollama pull $VISION_MODEL" ollama pull "$VISION_MODEL"
    print_ok "$VISION_MODEL baixado (ADR-022: CPU puro)"
fi

# ===========================================================
# FASE 6 -- xclip (clipboard)
# ===========================================================
print_step 6 "xclip (clipboard para Ctrl+V de imagens)"

if have_cmd xclip; then
    print_skip "xclip já instalado"
elif [ -z "$PKG_MANAGER" ]; then
    print_warn "Sem gerenciador suportado -- instale xclip manualmente"
else
    case "$PKG_MANAGER" in
        apt-get) run_or_skip "apt install xclip" sudo_run apt-get install -y xclip ;;
        dnf)     run_or_skip "dnf install xclip" sudo_run dnf install -y xclip ;;
        pacman)  run_or_skip "pacman -S xclip"   sudo_run pacman -S --noconfirm xclip ;;
        zypper)  run_or_skip "zypper install xclip" sudo_run zypper install -y xclip ;;
    esac
    print_ok "xclip instalado"
fi

# ===========================================================
# FASE 7 -- kitty (opcional)
# ===========================================================
print_step 7 "Kitty terminal (opcional)"

if have_cmd kitty; then
    print_skip "kitty já instalado"
elif [ $NO_KITTY -eq 1 ]; then
    print_skip "--no-kitty passado"
else
    ask_or_default "  Instalar kitty terminal? [s/N] " "n" KITTY_ANS
    if [[ "$KITTY_ANS" =~ ^[sS]$ ]] && [ -n "$PKG_MANAGER" ]; then
        case "$PKG_MANAGER" in
            apt-get) run_or_skip "apt install kitty" sudo_run apt-get install -y kitty ;;
            dnf)     run_or_skip "dnf install kitty" sudo_run dnf install -y kitty ;;
            pacman)  run_or_skip "pacman -S kitty"   sudo_run pacman -S --noconfirm kitty ;;
            zypper)  run_or_skip "zypper install kitty" sudo_run zypper install -y kitty ;;
        esac
        print_ok "kitty instalado"
    else
        print_skip "kitty não instalado por escolha do usuário"
    fi
fi

# ===========================================================
# FASE 8 -- permissões (chmod +x sempre)
# ===========================================================
print_step 8 "Permissões executáveis"

if [ $DRY_RUN -eq 1 ]; then
    print_skip "chmod +x (dry-run)"
else
    chmod +x "$SCRIPT_DIR/run.sh" 2>/dev/null || true
    find "$SCRIPT_DIR/scripts" -maxdepth 1 -type f \( -name "*.sh" -o -name "*.py" \) -exec chmod +x {} \; 2>/dev/null || true
    print_ok "run.sh e scripts/*.{sh,py} marcados executáveis"
fi

# ===========================================================
# FASE 9 -- smoke test
# ===========================================================
print_step 9 "Smoke test (import nyx)"

if [ -x "$SCRIPT_DIR/venv/bin/python" ]; then
    if [ $DRY_RUN -eq 1 ]; then
        print_skip "import smoke (dry-run)"
    elif "$SCRIPT_DIR/venv/bin/python" -c "from nyx.agent.loop import AgentLoop" 2>/dev/null; then
        print_ok "import nyx.agent.loop OK"
    else
        print_err "Falha no smoke import. Investigue venv + dependências."
        exit 1
    fi
else
    print_warn "venv/bin/python ausente -- smoke pulado"
fi

# ===========================================================
# FASE 10 -- Controle OOM (INFRA-OOM-01)
# ===========================================================
print_step 10 "Controle OOM (ulimit + oom_score_adj)"

LIMITS_SH="$SCRIPT_DIR/bin/nyx-runtime-limits.sh"
if [ -f "$LIMITS_SH" ]; then
    run_or_skip "chmod +x bin/nyx-runtime-limits.sh" chmod +x "$LIMITS_SH"
    if [ -f "$SCRIPT_DIR/scripts/check_oom.sh" ]; then
        run_or_skip "chmod +x scripts/check_oom.sh" chmod +x "$SCRIPT_DIR/scripts/check_oom.sh"
    fi
    print_ok "nyx-runtime-limits.sh executavel"
    print_ok "scripts/check_oom.sh disponivel para diagnostico OOM"
else
    print_warn "bin/nyx-runtime-limits.sh ausente -- INFRA-OOM-01 pulado"
fi

# ===========================================================
# FASE 11 -- Ícones XDG + desktop entry (BRANDING-MONO-STENCIL)
# ===========================================================
print_step 11 "Ícones XDG (hicolor) + entry no menu"

XDG_ICONS="${XDG_DATA_HOME:-$HOME/.local/share}/icons/hicolor"
XDG_APPS="${XDG_DATA_HOME:-$HOME/.local/share}/applications"

if [ -d "$SCRIPT_DIR/assets/icons/hicolor" ]; then
    for size in 16 22 24 32 48 64 128 256 512; do
        src="$SCRIPT_DIR/assets/icons/hicolor/${size}x${size}/apps/nyx.png"
        dest="$XDG_ICONS/${size}x${size}/apps/nyx.png"
        if [ -f "$src" ]; then
            mkdir -p "$(dirname "$dest")"
            if [ $DRY_RUN -eq 1 ]; then
                print_skip "cp -u $src (dry-run)"
            else
                cp -u "$src" "$dest"
            fi
        fi
    done

    mkdir -p "$XDG_ICONS/scalable/apps" "$XDG_ICONS/symbolic/apps"
    if [ -f "$SCRIPT_DIR/assets/icons/hicolor/scalable/apps/nyx.svg" ]; then
        cp -u "$SCRIPT_DIR/assets/icons/hicolor/scalable/apps/nyx.svg" "$XDG_ICONS/scalable/apps/nyx.svg"
    fi
    if [ -f "$SCRIPT_DIR/assets/icons/hicolor/symbolic/apps/nyx-symbolic.svg" ]; then
        cp -u "$SCRIPT_DIR/assets/icons/hicolor/symbolic/apps/nyx-symbolic.svg" "$XDG_ICONS/symbolic/apps/nyx-symbolic.svg"
    fi
    print_ok "ícones instalados em $XDG_ICONS"
else
    print_warn "assets/icons/hicolor ausente -- pulando ícones"
fi

if [ -f "$SCRIPT_DIR/assets/desktop/nyx.desktop" ]; then
    mkdir -p "$XDG_APPS"
    if [ $DRY_RUN -eq 1 ]; then
        print_skip "instalar nyx.desktop (dry-run)"
    else
        cp -u "$SCRIPT_DIR/assets/desktop/nyx.desktop" "$XDG_APPS/nyx.desktop"
        # Reescreve Exec= para o SCRIPT_DIR real (substitui placeholder absoluto)
        sed -i "s|^Exec=.*$|Exec=$SCRIPT_DIR/run.sh|" "$XDG_APPS/nyx.desktop"
        print_ok "desktop entry em $XDG_APPS/nyx.desktop"
    fi
else
    print_warn "assets/desktop/nyx.desktop ausente -- pulando entry"
fi

if command -v gtk-update-icon-cache >/dev/null 2>&1; then
    gtk-update-icon-cache -q -t "$XDG_ICONS" 2>/dev/null || true
fi
if command -v update-desktop-database >/dev/null 2>&1; then
    update-desktop-database -q "$XDG_APPS" 2>/dev/null || true
fi

echo ""
echo -e "${GREEN}${BOLD}Instalação concluída. Rode: ./run.sh${NC}"
echo ""
