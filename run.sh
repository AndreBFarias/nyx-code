#!/bin/bash
# run.sh - Nyx-Code Launcher
# Gerencia Ollama dedicado, venv, modelos e a aplicação
# Estilo run_luna.sh: cuida de TUDO - inicia, aquece, executa, limpa

set -uo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# ─── CORES (Paleta Nyx - entidade do panteão Luna) ──────────
if [ -t 1 ]; then
    PRIMARY=$'\033[38;2;0;212;170m'      # #00D4AA - cor principal Nyx (cyan/teal)
    SECONDARY=$'\033[38;2;108;122;137m'  # #6C7A89 - secundária
    ACCENT=$'\033[38;2;232;232;232m'     # #E8E8E8 - destaque/texto
    GREEN=$'\033[38;2;0;212;170m'        # #00D4AA - sucesso (= primary)
    ORANGE=$'\033[38;2;255;184;108m'     # #FFB86C - avisos
    RED=$'\033[38;2;255;107;107m'        # #FF6B6B - erros (Nyx)
    COMMENT=$'\033[38;2;108;122;137m'    # #6C7A89 - secundário
    FG=$'\033[38;2;232;232;232m'         # #E8E8E8 - texto primário
    BOLD=$'\033[1m'
    DIM=$'\033[2m'
    NC=$'\033[0m'
else
    PRIMARY='' SECONDARY='' ACCENT='' GREEN='' ORANGE='' RED='' COMMENT='' FG='' BOLD='' DIM='' NC=''
fi

log_nyx()  { echo -e "  ${PRIMARY}[nyx]${NC} $1"; }
log_ok()   { echo -e "  ${GREEN}[nyx]${NC} $1"; }
log_warn() { echo -e "  ${ORANGE}[nyx]${NC} $1"; }
log_err()  { echo -e "  ${RED}[nyx]${NC} $1"; }

# Mensagens de fase de boot (pré-TUI) vão só pro arquivo logs/boot.log.
# Warnings e erros permanecem em stdout via log_warn/log_err.
mkdir -p "$SCRIPT_DIR/logs" 2>/dev/null
log_boot() { echo "$(date +%H:%M:%S) [nyx] $1" >> "$SCRIPT_DIR/logs/boot.log"; }

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
# Contrato: NYX_OLLAMA_HOST é host puro (sem porta). OLLAMA_HOST exportado
# para o daemon Ollama compõe host:port (convenção do binário).
NYX_OLLAMA_PORT="${NYX_OLLAMA_PORT:-11435}"
NYX_OLLAMA_HOST="${NYX_OLLAMA_HOST:-127.0.0.1}"
NYX_PROXY_PORT="${NYX_PROXY_PORT:-11436}"

# ─── PARSE FLAGS ──────────────────────────────────────────
MODEL="${NYX_MODEL:-qwen2.5-coder:3b}"
DEBUG=0
HEADLESS=0
GAUNTLET=0
GAUNTLET_ONLY="completo"
EXTRA_ARGS=()

while [[ $# -gt 0 ]]; do
    case "$1" in
        --smoke)
            # Smoke check: prova que imports resolvem sem subir Ollama/proxy.
            exec "$SCRIPT_DIR/venv/bin/python" "$SCRIPT_DIR/nyx/cli.py" --smoke
            ;;
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
            shift 2 ;;
        --debug)
            DEBUG=1
            shift ;;
        --headless)
            HEADLESS=1
            shift ;;
        --gauntlet)
            GAUNTLET=1
            HEADLESS=1
            shift ;;
        --only)
            GAUNTLET_ONLY="$2"
            shift 2 ;;
        *)
            EXTRA_ARGS+=("$1")
            shift ;;
    esac
done

# ─── VARIÁVEIS OLLAMA ────────────────────────────────────
# Daemon Ollama exige host:port em OLLAMA_HOST (convenção upstream).
export OLLAMA_HOST="${NYX_OLLAMA_HOST}:${NYX_OLLAMA_PORT}"
export OLLAMA_MODELS="$SCRIPT_DIR/models"
export OLLAMA_NUM_PARALLEL=1
export OLLAMA_MAX_LOADED_MODELS=1
export OLLAMA_FLASH_ATTENTION=1

# Priorizar Ollama do sistema (tem runners CUDA/GPU)
# Fallback para binário local se não houver instalação global
if command -v ollama &> /dev/null; then
    OLLAMA_BIN="$(command -v ollama)"
else
    OLLAMA_BIN="$SCRIPT_DIR/bin/ollama"
fi
OLLAMA_PID=""

# ─── LIMPAR VARIÁVEIS CONFLITANTES ───────────────────────
# Modelos do shell global interferem na seleção do modelo
unset GEMINI_MODEL 2>/dev/null || true
unset GEMINI_API_KEY 2>/dev/null || true
unset DEEPSEEK_API_KEY 2>/dev/null || true
# ANTHROPIC_API_KEY é mantida (necessária para auth da TUI, vem do .env)

# ─── VALIDAÇÕES ───────────────────────────────────────────
validate() {
    local errors=0

    if [ ! -x "$OLLAMA_BIN" ]; then
        log_err "Ollama não encontrado em bin/ollama. Execute ${PRIMARY}./install.sh${NC} primeiro."
        errors=$((errors + 1))
    fi

    if [ ! -d "$SCRIPT_DIR/venv" ]; then
        log_err "venv não encontrado. Execute ${PRIMARY}./install.sh${NC} primeiro."
        errors=$((errors + 1))
    fi

    if [ "$errors" -gt 0 ]; then
        exit 1
    fi
}

# ─── PARAR OLLAMA EXISTENTE ──────────────────────────────
kill_existing_ollama() {
    # Parar proxy anterior
    pkill -f "nyx/proxy.py" 2>/dev/null || true

    local existing_pid
    existing_pid=$(lsof -ti:"$NYX_OLLAMA_PORT" 2>/dev/null || true)
    if [ -n "$existing_pid" ]; then
        local owner
        owner=$(ps -p "$existing_pid" -o comm= 2>/dev/null || echo "desconhecido")
        if echo "$owner" | grep -qi ollama; then
            log_nyx "Parando Ollama existente na porta $NYX_OLLAMA_PORT (PID: $existing_pid)..."
            kill "$existing_pid" 2>/dev/null || true
            sleep 1
            kill -9 "$existing_pid" 2>/dev/null || true
            sleep 1
        else
            log_err "Porta $NYX_OLLAMA_PORT ocupada por processo não-Ollama (PID $existing_pid, $owner)."
            log_err "Opções:"
            log_err "  1. Matar manualmente: kill $existing_pid"
            log_err "  2. Usar outra porta: NYX_OLLAMA_PORT=11437 ./run.sh"
            log_err "  3. Definir em .env: NYX_OLLAMA_PORT=XXXXX"
            exit 1
        fi
    fi

    # Matar processos ollama serve órfãos do Nyx-Code
    pkill -f "$OLLAMA_BIN serve" 2>/dev/null || true

    log_boot "Limpando cache..."
    sleep 1
}

# ─── INICIAR OLLAMA ──────────────────────────────────────
start_ollama() {
    log_boot "Iniciando Ollama na porta $NYX_OLLAMA_PORT..."
    mkdir -p "$SCRIPT_DIR/logs"

    "$OLLAMA_BIN" serve >> "$SCRIPT_DIR/logs/ollama.log" 2>&1 &
    OLLAMA_PID=$!

    local elapsed=0
    while ! curl -sf "http://${NYX_OLLAMA_HOST}:${NYX_OLLAMA_PORT}/api/version" > /dev/null 2>&1; do
        sleep 1
        elapsed=$((elapsed + 1))
        if [ "$elapsed" -ge "$OLLAMA_START_TIMEOUT" ]; then
            log_err "Ollama não iniciou em ${OLLAMA_START_TIMEOUT}s"
            log_err "Verifique logs/ollama.log"
            exit 1
        fi
    done

    log_boot "Ollama pronto (PID: $OLLAMA_PID, ${elapsed}s)"
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
        log_nyx "Tentando baixar $MODEL..."
        if ! "$OLLAMA_BIN" pull "$MODEL" 2>&1 | tee -a "$SCRIPT_DIR/logs/ollama.log"; then
            log_err "Falha ao baixar modelo: $MODEL"
            log_err "Causas possíveis:"
            log_err "  1. Nome de modelo incorreto (verifique NYX_MODEL no .env)"
            log_err "  2. Sem conexão com registry Ollama"
            log_err "  3. Modelo não existe no registry público"
            log_err "Modelos disponíveis localmente:"
            "$OLLAMA_BIN" list 2>/dev/null | sed 's/^/    /' || true
            exit 1
        fi
        log_ok "$MODEL baixado"
    else
        log_boot "Modelo: $MODEL"
    fi
}

# ─── WARMUP DO MODELO ────────────────────────────────────
warmup_model() {
    log_boot "Aquecendo modelo $MODEL..."
    local response
    response=$(curl -sf --max-time "$WARMUP_TIMEOUT" \
        "http://${NYX_OLLAMA_HOST}:${NYX_OLLAMA_PORT}/v1/chat/completions" \
        -H "Content-Type: application/json" \
        -d "{\"model\":\"$MODEL\",\"messages\":[{\"role\":\"user\",\"content\":\"hi\"}],\"max_tokens\":3}" 2>&1)

    if echo "$response" | grep -q '"choices"'; then
        log_boot "Modelo aquecido e pronto"
    else
        log_warn "Warmup retornou resposta inesperada (modelo pode estar lento na primeira inferência)"
        if [ "$DEBUG" -eq 1 ]; then
            log_boot "Resposta: $response"
        fi
    fi
}

# ─── AUTO-TUNE DE GPU ────────────────────────────────────
auto_tune_gpu() {
    if [ "${NYX_AUTO_TUNE:-1}" != "1" ]; then
        log_boot "Auto-tune desativado (NYX_AUTO_TUNE=${NYX_AUTO_TUNE:-1}). Usando NYX_NUM_GPU=${NYX_NUM_GPU:-12}"
        return 0
    fi
    if [ ! -x "$SCRIPT_DIR/venv/bin/python" ]; then
        return 0
    fi
    local tuned
    tuned=$("$SCRIPT_DIR/venv/bin/python" "$SCRIPT_DIR/scripts/detect_gpu.py" --for-model "$MODEL" 2>/dev/null)
    if [[ "$tuned" =~ ^[0-9]+$ ]]; then
        NYX_NUM_GPU="$tuned"
        export NYX_NUM_GPU
        log_boot "Auto-tune: num_gpu=$NYX_NUM_GPU para $MODEL"
    else
        log_warn "Auto-tune retornou valor inválido ('$tuned'). Mantendo NYX_NUM_GPU=${NYX_NUM_GPU:-12}"
    fi
}

# ─── CONFIGURAÇÃO VRAM (7b) ──────────────────────────────
configure_vram() {
    if [[ "$MODEL" != *"7b"* ]]; then
        return 0
    fi

    local vram_max="${NYX_VRAM_MAX:-2.5}"
    log_boot "Modelo 7b detectado. Limite VRAM: ${vram_max}GB"

    if command -v nvidia-smi &> /dev/null; then
        local vram_total
        vram_total=$(nvidia-smi --query-gpu=memory.total --format=csv,noheader,nounits 2>/dev/null | head -1)
        if [ -n "$vram_total" ]; then
            log_boot "GPU: ${vram_total}MiB VRAM total"
        fi
    fi

    log_boot "num_gpu=${NYX_NUM_GPU:-18} (calibrado pelo auto-tune ou .env)"
}

# ─── BANNER ───────────────────────────────────────────────
# Banner único é renderizado pelo cli.py (_build_banner). Aqui só
# exportamos a info útil (debug=ativo) se aplicável.
show_banner() {
    if [ "$HEADLESS" -eq 1 ]; then
        return 0
    fi
    if [ "$DEBUG" -eq 1 ]; then
        echo -e "  ${COMMENT}debug${NC}   ${ORANGE}ativo${NC}"
    fi
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

# ─── AUTO-ATUALIZAR EXECUTAR_SPRINT.md ───────────────────
# Não-bloqueante. Lê SPRINT_ORDER_MASTER.md, detecta próxima PENDENTE,
# atualiza EXECUTAR_SPRINT.md se o ID mudou. Falha silencioso (|| true).
if [ -x "$SCRIPT_DIR/venv/bin/python" ] && [ -f "$SCRIPT_DIR/scripts/update_next_sprint.py" ]; then
    _next_info="$("$SCRIPT_DIR/venv/bin/python" "$SCRIPT_DIR/scripts/update_next_sprint.py" 2>/dev/null || true)"
    if [ -n "$_next_info" ]; then
        log_nyx "$_next_info"
    fi
fi

kill_existing_ollama
start_ollama
check_model
auto_tune_gpu
configure_vram
show_banner

# ─── CONFIGURAR PROXY + NYX TUI ───────────────────────────
NYX_NUM_GPU="${NYX_NUM_GPU:-12}"

export CLAUDE_CODE_USE_OPENAI=1
export OPENAI_API_KEY=ollama
export OPENAI_BASE_URL="http://127.0.0.1:${NYX_PROXY_PORT}/v1"
export OPENAI_MODEL="$MODEL"
export OPENAI_TIMEOUT=300000
# ANTHROPIC_API_KEY vem do .env (necessária para auth da TUI)

# ─── PRE-CARREGAR MODELO COM NUM_GPU LIMITADO ────────────
log_boot "Pré-carregando modelo (num_gpu=$NYX_NUM_GPU)..."
if curl -sf --max-time 120 "http://${NYX_OLLAMA_HOST}:${NYX_OLLAMA_PORT}/api/chat" \
    -H "Content-Type: application/json" \
    -d "{\"model\":\"$MODEL\",\"messages\":[{\"role\":\"user\",\"content\":\"hi\"}],\"stream\":false,\"think\":false,\"options\":{\"num_gpu\":$NYX_NUM_GPU,\"num_ctx\":4096}}" \
    > /dev/null 2>&1; then
    log_boot "Modelo pré-carregado"
else
    log_warn "Pré-carga falhou (modelo será carregado na primeira requisição)"
fi

# Verificar se Ollama sobreviveu ao pre-load
if ! kill -0 "$OLLAMA_PID" 2>/dev/null; then
    log_warn "Ollama morreu durante pré-carga. Reiniciando..."
    start_ollama
fi

# ─── INICIAR PROXY (think=false para tool calling) ───────
log_boot "Iniciando proxy na porta $NYX_PROXY_PORT..."
"$SCRIPT_DIR/venv/bin/python" "$SCRIPT_DIR/nyx/proxy.py" \
    --port "$NYX_PROXY_PORT" \
    --ollama-port "$NYX_OLLAMA_PORT" \
    --num-gpu "$NYX_NUM_GPU" \
    >> "$SCRIPT_DIR/logs/proxy.log" 2>&1 &
PROXY_PID=$!
sleep 2

if curl -sf "http://127.0.0.1:${NYX_PROXY_PORT}/v1/models" > /dev/null 2>&1; then
    log_boot "Proxy pronto (PID: $PROXY_PID)"
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

Codigo limpo nao e arte. E higiene.
Ler -> Escrever -> Testar -> Terminar."

# ─── GAUNTLET (se --gauntlet) ─────────────────────────────
if [ "$GAUNTLET" -eq 1 ]; then
    log_nyx "Executando Gauntlet (fase: $GAUNTLET_ONLY)..."
    "$SCRIPT_DIR/venv/bin/python" "$SCRIPT_DIR/scripts/gauntlet/nyx_gauntlet.py" \
        --proxy-url "http://127.0.0.1:${NYX_PROXY_PORT}" \
        --ollama-url "http://${NYX_OLLAMA_HOST}:${NYX_OLLAMA_PORT}" \
        --only "$GAUNTLET_ONLY" \
        --model "$MODEL"
    EXIT_CODE=$?

    # Auto-atualizar docs após gauntlet
    log_nyx "Atualizando docs..."
    "$SCRIPT_DIR/venv/bin/python" "$SCRIPT_DIR/scripts/update_docs.py" 2>/dev/null || true

    exit "$EXIT_CODE"
fi

# ─── INICIAR NYX CLI (Python) ─────────────────────────────
log_boot "Iniciando Nyx CLI..."
"$SCRIPT_DIR/venv/bin/python" "$SCRIPT_DIR/nyx/cli.py"
EXIT_CODE=$?

exit "$EXIT_CODE"


# "O segredo da liberdade é a coragem." -- Péricles
