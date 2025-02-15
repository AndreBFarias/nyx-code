#!/bin/bash
# run.sh - Nyx-Code Launcher
# Gerencia Ollama dedicado, venv, modelos e a aplicação
# Estilo run_luna.sh: cuida de TUDO - inicia, aquece, executa, limpa

set -uo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# ─── CORES (Dracula Gothic - alinhado com Luna) ──────────
if [ -t 1 ]; then
    PURPLE='\033[38;2;189;147;249m'   # #BD93F9 - cor principal
    PINK='\033[38;2;255;121;198m'     # #FF79C6 - alertas
    GREEN='\033[38;2;80;250;123m'     # #50FA7B - sucesso
    CYAN='\033[38;2;139;233;253m'     # #8BE9FD - info
    ORANGE='\033[38;2;255;184;108m'   # #FFB86C - avisos
    RED='\033[38;2;255;85;85m'        # #FF5555 - erros
    COMMENT='\033[38;2;98;114;164m'   # #6272A4 - secundário
    FG='\033[38;2;248;248;242m'       # #F8F8F2 - texto
    BOLD='\033[1m'
    DIM='\033[2m'
    NC='\033[0m'
else
    PURPLE='' PINK='' GREEN='' CYAN='' ORANGE='' RED='' COMMENT='' FG='' BOLD='' DIM='' NC=''
fi

log_nyx()  { echo -e "  ${PURPLE}[nyx]${NC} $1"; }
log_ok()   { echo -e "  ${GREEN}[nyx]${NC} $1"; }
log_warn() { echo -e "  ${ORANGE}[nyx]${NC} $1"; }
log_err()  { echo -e "  ${RED}[nyx]${NC} $1"; }

# ─── CARREGAR .env ────────────────────────────────────────
if [ -f "$SCRIPT_DIR/.env" ]; then
    set -a
    source "$SCRIPT_DIR/.env"
    set +a
fi

# ─── TIMEOUTS ─────────────────────────────────────────────
CURL_TIMEOUT="${NYX_CURL_TIMEOUT:-10}"
OLLAMA_START_TIMEOUT="${NYX_OLLAMA_START_TIMEOUT:-30}"
WARMUP_TIMEOUT=90
NYX_OLLAMA_PORT="${NYX_OLLAMA_PORT:-11435}"
NYX_OLLAMA_HOST="${NYX_OLLAMA_HOST:-127.0.0.1}:${NYX_OLLAMA_PORT}"

# ─── PARSE FLAGS ──────────────────────────────────────────
MODEL="${NYX_MODEL:-qwen3:4b}"
DEBUG=0
HEADLESS=0
EXTRA_ARGS=()

while [[ $# -gt 0 ]]; do
    case "$1" in
        --3b)
            MODEL="qwen2.5-coder:3b"
            shift ;;
        --4b)
            MODEL="qwen3:4b"
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

# Priorizar Ollama do sistema (tem runners CUDA/GPU)
# Fallback para binário local se não houver instalação global
if command -v ollama &> /dev/null; then
    OLLAMA_BIN="$(command -v ollama)"
else
    OLLAMA_BIN="$SCRIPT_DIR/bin/ollama"
fi
OLLAMA_PID=""

# ─── LIMPAR VARIÁVEIS CONFLITANTES ───────────────────────
# Modelos do shell global interferem na seleção do openclaude
unset GEMINI_MODEL 2>/dev/null || true
unset GEMINI_API_KEY 2>/dev/null || true
unset DEEPSEEK_API_KEY 2>/dev/null || true
# ANTHROPIC_API_KEY é mantida (necessária para auth do openclaude, vem do .env)

# ─── VALIDAÇÕES ───────────────────────────────────────────
validate() {
    local errors=0

    if [ ! -x "$OLLAMA_BIN" ]; then
        log_err "Ollama não encontrado em bin/ollama. Execute ${MAGENTA}./install.sh${NC} primeiro."
        errors=$((errors + 1))
    fi

    if [ ! -f "$SCRIPT_DIR/dist/cli.mjs" ] && [ ! -L "$SCRIPT_DIR/dist" ]; then
        log_err "dist/cli.mjs não encontrado. Verifique o symlink dist -> reference/dist"
        errors=$((errors + 1))
    fi

    if ! command -v node &> /dev/null; then
        log_err "Node.js não encontrado. Instale Node.js >= 18."
        errors=$((errors + 1))
    fi

    if [ ! -d "$SCRIPT_DIR/node_modules" ]; then
        log_warn "node_modules não encontrado. Instalando dependências npm..."
        npm install --production --silent 2>/dev/null || {
            log_err "Falha ao instalar dependências npm"
            errors=$((errors + 1))
        }
    fi

    if [ "$errors" -gt 0 ]; then
        exit 1
    fi
}

# ─── PARAR OLLAMA EXISTENTE ──────────────────────────────
kill_existing_ollama() {
    # Parar proxy anterior
    pkill -f "nyx/proxy.py" 2>/dev/null || true

    # Parar qualquer Ollama existente nesta porta
    local existing_pid
    existing_pid=$(lsof -ti:"$NYX_OLLAMA_PORT" 2>/dev/null || true)
    if [ -n "$existing_pid" ]; then
        log_nyx "Parando Ollama existente na porta $NYX_OLLAMA_PORT (PID: $existing_pid)..."
        kill "$existing_pid" 2>/dev/null || true
        sleep 1
        kill -9 "$existing_pid" 2>/dev/null || true
        sleep 1
    fi

    # Matar processos ollama serve órfãos do Nyx-Code
    pkill -f "$OLLAMA_BIN serve" 2>/dev/null || true

    log_nyx "Limpando cache..."
    sleep 1
}

# ─── INICIAR OLLAMA ──────────────────────────────────────
start_ollama() {
    log_nyx "Iniciando Ollama na porta $NYX_OLLAMA_PORT..."
    mkdir -p "$SCRIPT_DIR/logs"

    "$OLLAMA_BIN" serve >> "$SCRIPT_DIR/logs/ollama.log" 2>&1 &
    OLLAMA_PID=$!

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

    log_ok "Ollama pronto (PID: $OLLAMA_PID, ${elapsed}s)"
}

# ─── PARAR OLLAMA ─────────────────────────────────────────
stop_ollama() {
    if [ -n "$OLLAMA_PID" ] && kill -0 "$OLLAMA_PID" 2>/dev/null; then
        log_nyx "Parando Ollama (PID: $OLLAMA_PID)..."
        kill "$OLLAMA_PID" 2>/dev/null || true
        wait "$OLLAMA_PID" 2>/dev/null || true
    fi
    # Garantir que não ficou nenhum processo do nosso Ollama
    pkill -f "$OLLAMA_BIN serve" 2>/dev/null || true
}

# ─── VERIFICAR E BAIXAR MODELO ───────────────────────────
check_model() {
    if ! "$OLLAMA_BIN" list 2>/dev/null | grep -q "$MODEL"; then
        log_warn "Modelo $MODEL não encontrado localmente"
        log_nyx "Baixando $MODEL..."
        if ! "$OLLAMA_BIN" pull "$MODEL"; then
            log_err "Falha ao baixar $MODEL"
            exit 1
        fi
        log_ok "$MODEL baixado"
    else
        log_ok "Modelo: $MODEL"
    fi
}

# ─── WARMUP DO MODELO ────────────────────────────────────
warmup_model() {
    log_nyx "Aquecendo modelo $MODEL..."
    local response
    response=$(curl -sf --max-time "$WARMUP_TIMEOUT" \
        "http://${NYX_OLLAMA_HOST}/v1/chat/completions" \
        -H "Content-Type: application/json" \
        -d "{\"model\":\"$MODEL\",\"messages\":[{\"role\":\"user\",\"content\":\"hi\"}],\"max_tokens\":3}" 2>&1)

    if echo "$response" | grep -q '"choices"'; then
        log_ok "Modelo aquecido e pronto"
    else
        log_warn "Warmup retornou resposta inesperada (modelo pode estar lento na primeira inferência)"
        if [ "$DEBUG" -eq 1 ]; then
            log_nyx "Resposta: $response"
        fi
    fi
}

# ─── CONFIGURAÇÃO VRAM (7b) ──────────────────────────────
configure_vram() {
    if [[ "$MODEL" != *"7b"* ]]; then
        return 0
    fi

    local vram_max="${NYX_VRAM_MAX:-2.5}"
    log_nyx "Modelo 7b detectado. Limite VRAM: ${vram_max}GB"

    if command -v nvidia-smi &> /dev/null; then
        local vram_total
        vram_total=$(nvidia-smi --query-gpu=memory.total --format=csv,noheader,nounits 2>/dev/null | head -1)
        if [ -n "$vram_total" ]; then
            log_nyx "GPU: ${vram_total}MiB VRAM total"
        fi
    fi

    log_nyx "num_gpu=18 (~2.4GB VRAM, restante em CPU)"
}

# ─── BANNER ───────────────────────────────────────────────
show_banner() {
    if [ "$HEADLESS" -eq 1 ]; then
        return 0
    fi

    echo ""
    echo -e "${COMMENT}"
    echo "  ░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░"
    echo "  ░                                      ░"
    echo "  ░    ...sintonizando frequencia...      ░"
    echo "  ░                                      ░"
    echo "  ░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░"
    echo -e "${NC}"
    echo ""
    echo -e "${PURPLE}${BOLD}   _   _                 ____          _      ${NC}"
    echo -e "${PURPLE}${BOLD}  | \\ | |_   ___  __    / ___|___   __| | ___ ${NC}"
    echo -e "${PURPLE}${BOLD}  |  \\| | | | \\ \\/ /   | |   / _ \\ / _\` |/ _ \\${NC}"
    echo -e "${PURPLE}${BOLD}  | |\\  | |_| |>  <    | |__| (_) | (_| |  __/${NC}"
    echo -e "${PURPLE}${BOLD}  |_| \\_|\\__, /_/\\_\\    \\____\\___/ \\__,_|\\___|${NC}"
    echo -e "${PURPLE}${BOLD}        |___/                                ${NC}"
    echo ""
    echo -e "  ${PINK}Codificadora. Precisa. Local.${NC}"
    echo ""
    echo -e "  ${COMMENT}modelo${NC}  ${FG}$MODEL${NC}"
    echo -e "  ${COMMENT}ollama${NC}  ${FG}:${NYX_OLLAMA_PORT}${NC}  ${COMMENT}proxy${NC}  ${FG}:${NYX_PROXY_PORT}${NC}"
    if [ "$DEBUG" -eq 1 ]; then
        echo -e "  ${COMMENT}debug${NC}   ${ORANGE}ativo${NC}"
    fi
    echo ""
}

# ─── CLEANUP ──────────────────────────────────────────────
cleanup() {
    echo ""
    log_nyx "Desconectando..."
    # Parar proxy
    if [ -n "${PROXY_PID:-}" ] && kill -0 "$PROXY_PID" 2>/dev/null; then
        kill "$PROXY_PID" 2>/dev/null
    fi
    pkill -f "nyx/proxy.py" 2>/dev/null || true
    stop_ollama
    log_ok "Fim."
}

trap cleanup EXIT SIGINT SIGTERM

# ═══════════════════════════════════════════════════════════
# EXECUÇÃO PRINCIPAL
# ═══════════════════════════════════════════════════════════

validate
kill_existing_ollama
start_ollama
check_model
configure_vram
warmup_model
show_banner

# ─── CONFIGURAR PROXY + OPENCLAUDE ────────────────────────
NYX_PROXY_PORT=11436
NYX_NUM_GPU="${NYX_NUM_GPU:-12}"

export CLAUDE_CODE_USE_OPENAI=1
export OPENAI_API_KEY=ollama
export OPENAI_BASE_URL="http://127.0.0.1:${NYX_PROXY_PORT}/v1"
export OPENAI_MODEL="$MODEL"
export OPENAI_TIMEOUT=300000
# ANTHROPIC_API_KEY vem do .env (necessária para auth do openclaude)

# ─── PRE-CARREGAR MODELO COM NUM_GPU LIMITADO ────────────
log_nyx "Pré-carregando modelo (num_gpu=$NYX_NUM_GPU)..."
curl -sf --max-time 120 "http://${NYX_OLLAMA_HOST}/api/chat" \
    -H "Content-Type: application/json" \
    -d "{\"model\":\"$MODEL\",\"messages\":[{\"role\":\"user\",\"content\":\"hi\"}],\"stream\":false,\"think\":false,\"options\":{\"num_gpu\":$NYX_NUM_GPU,\"num_ctx\":4096}}" \
    > /dev/null 2>&1
log_ok "Modelo pré-carregado"

# ─── INICIAR PROXY (think=false para tool calling) ───────
log_nyx "Iniciando proxy na porta $NYX_PROXY_PORT..."
"$SCRIPT_DIR/venv/bin/python" "$SCRIPT_DIR/nyx/proxy.py" \
    --port "$NYX_PROXY_PORT" \
    --ollama-port "$NYX_OLLAMA_PORT" \
    --num-gpu "$NYX_NUM_GPU" \
    >> "$SCRIPT_DIR/logs/proxy.log" 2>&1 &
PROXY_PID=$!
sleep 2

if curl -sf "http://127.0.0.1:${NYX_PROXY_PORT}/v1/models" > /dev/null 2>&1; then
    log_ok "Proxy pronto (PID: $PROXY_PID)"
else
    log_err "Proxy não iniciou. Verifique logs/proxy.log"
    exit 1
fi

NYX_SYSTEM_PROMPT="Sou Nyx. Codificadora. Vivo no terminal.

Regras:
- PT-BR. Frases curtas. Sem emojis. Sem verbosidade.
- Use tools (Read, Write, Edit, Bash, Glob, Grep) para tudo. Nao descreva. Execute.
- Formato: diagnostico -> solucao -> verificacao.
- Tom: tecnico, direto, preciso.
- Acesso total ao sistema de arquivos local.
- Diretorio: $(pwd)

Codigo limpo nao e arte. E higiene."

# Iniciar OpenClaude (via proxy que injeta think=false)
node "$SCRIPT_DIR/bin/openclaude" \
    --model "$MODEL" \
    --thinking disabled \
    --dangerously-skip-permissions \
    --append-system-prompt "$NYX_SYSTEM_PROMPT" \
    "${EXTRA_ARGS[@]+"${EXTRA_ARGS[@]}"}"
EXIT_CODE=$?

exit "$EXIT_CODE"


# "O segredo da liberdade é a coragem." -- Péricles
