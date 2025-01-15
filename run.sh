#!/bin/bash
# run.sh - Nyx-Code Launcher
# Gerencia Ollama dedicado, venv, modelos e a aplicação
# Estilo run_luna.sh: cuida de TUDO - inicia, aquece, executa, limpa

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
        log_info "Parando Ollama existente na porta $NYX_OLLAMA_PORT (PID: $existing_pid)..."
        kill "$existing_pid" 2>/dev/null || true
        sleep 1
        kill -9 "$existing_pid" 2>/dev/null || true
        sleep 1
    fi

    # Matar processos ollama serve órfãos do Nyx-Code
    pkill -f "$OLLAMA_BIN serve" 2>/dev/null || true

    log_info "Limpando cache..."
    sleep 1
}

# ─── INICIAR OLLAMA ──────────────────────────────────────
start_ollama() {
    log_info "Iniciando Ollama na porta $NYX_OLLAMA_PORT..."
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
        log_info "Parando Ollama (PID: $OLLAMA_PID)..."
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

# ─── WARMUP DO MODELO ────────────────────────────────────
warmup_model() {
    log_info "Aquecendo modelo $MODEL..."
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
            log_info "Resposta: $response"
        fi
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
    # Parar proxy
    if [ -n "${PROXY_PID:-}" ] && kill -0 "$PROXY_PID" 2>/dev/null; then
        kill "$PROXY_PID" 2>/dev/null
    fi
    pkill -f "nyx/proxy.py" 2>/dev/null || true
    stop_ollama
    log_ok "Encerrado."
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
log_info "Pré-carregando modelo (num_gpu=$NYX_NUM_GPU)..."
curl -sf --max-time 120 "http://${NYX_OLLAMA_HOST}/api/chat" \
    -H "Content-Type: application/json" \
    -d "{\"model\":\"$MODEL\",\"messages\":[{\"role\":\"user\",\"content\":\"hi\"}],\"stream\":false,\"think\":false,\"options\":{\"num_gpu\":$NYX_NUM_GPU,\"num_ctx\":4096}}" \
    > /dev/null 2>&1
log_ok "Modelo pré-carregado"

# ─── INICIAR PROXY (think=false para tool calling) ───────
log_info "Iniciando proxy na porta $NYX_PROXY_PORT..."
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

NYX_SYSTEM_PROMPT="Voce e Nyx, um agente de codigo local. Regras:
- Responda SEMPRE em PT-BR
- Quando pedirem para ler, criar, editar arquivos ou executar comandos, USE as tools disponiveis (Read, Write, Edit, Bash, Glob, Grep)
- Voce TEM acesso total ao sistema de arquivos local
- Seja direto e conciso
- Diretorio de trabalho: $(pwd)"

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
