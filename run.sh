#!/bin/bash
# run.sh - Nyx-Code Launcher
# Gerencia Ollama dedicado, venv, modelos e a aplicação
# Estilo run_luna.sh: cuida de TUDO - inicia, aquece, executa, limpa

set -uo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# INFRA-OOM-01: aplica limites de runtime (ulimit + oom_score_adj) se o
# helper estiver presente. Sem efeito colateral se ausente.
if [ -f "$SCRIPT_DIR/bin/nyx-runtime-limits.sh" ]; then
    # shellcheck source=bin/nyx-runtime-limits.sh
    source "$SCRIPT_DIR/bin/nyx-runtime-limits.sh"
fi

# ─── CORES (Paleta Nyx - entidade do panteão Luna) ──────────
if [ -t 1 ]; then
    PRIMARY=$'\033[38;2;0;212;170m'      # #00D4AA - cor principal Nyx (cyan/teal)
    SECONDARY=$'\033[38;2;108;122;137m'  # #6C7A89 - secundária
    ACCENT=$'\033[38;2;232;232;232m'     # #E8E8E8 - destaque/texto
    GREEN=$'\033[38;2;0;212;170m'        # #00D4AA - sucesso (= primary)
    ORANGE=$'\033[38;2;255;184;108m'     # #FFB86C - avisos
    RED=$'\033[38;2;255;107;107m'        # #FF6B6B - erros (Nyx)
    PURPLE=$'\033[38;2;157;78;221m'      # #9D4EDD - roxo Nyx (sprint 237 boot spinner)
    COMMENT=$'\033[38;2;108;122;137m'    # #6C7A89 - secundário
    FG=$'\033[38;2;232;232;232m'         # #E8E8E8 - texto primário
    BOLD=$'\033[1m'
    DIM=$'\033[2m'
    NC=$'\033[0m'
else
    PRIMARY='' SECONDARY='' ACCENT='' GREEN='' ORANGE='' RED='' PURPLE='' COMMENT='' FG='' BOLD='' DIM='' NC=''
fi

log_nyx()  { echo -e "  ${PRIMARY}[nyx]${NC} $1"; }
log_ok()   { echo -e "  ${GREEN}[nyx]${NC} $1"; }
# SPRINT 237 UX-BOOT-SILENT-SPINNER-01: warn/err emitem em stderr para
# sobreviver ao silenciamento de stdout durante boot. Mensagens criticas
# continuam visiveis mesmo com spinner ativo.
log_warn() { echo -e "  ${ORANGE}[nyx]${NC} $1" >&2; }
log_err()  { echo -e "  ${RED}[nyx]${NC} $1" >&2; }

# Mensagens de fase de boot (pré-TUI) vão só pro arquivo logs/boot.log.
# Warnings e erros permanecem em stderr via log_warn/log_err.
mkdir -p "$SCRIPT_DIR/logs" 2>/dev/null
log_boot() { echo "$(date +%H:%M:%S) [nyx] $1" >> "$SCRIPT_DIR/logs/boot.log"; }

# SPRINT 237 UX-BOOT-SILENT-SPINNER-01: spinner único durante todo o boot.
# stdout do bloco principal vai para boot.log (via tee implicito do
# log_boot); stderr (log_warn/log_err) permanece visivel.
BOOT_SPINNER_PID=""
BOOT_SPINNER_ACTIVE=0
start_boot_spinner() {
    # Skip em headless, gauntlet ou non-TTY (CI, pipe, redirect).
    if [ ! -t 1 ] || [ "${HEADLESS:-0}" -eq 1 ] || [ "${GAUNTLET:-0}" -eq 1 ]; then
        return 0
    fi
    BOOT_SPINNER_ACTIVE=1
    # SPRINT 237 hotfix3: sem exec >> logs/boot.log (era fragil, quebrava
    # comandos do boot que dependem do stdout). Em vez disso, log_nyx/log_ok
    # sao redefinidas como silenciosas (so logam pra boot.log). log_warn /
    # log_err continuam visiveis em stderr.
    log_nyx() { echo "$(date +%H:%M:%S) [nyx] $1" >> "$SCRIPT_DIR/logs/boot.log"; }
    log_ok()  { echo "$(date +%H:%M:%S) [nyx] $1" >> "$SCRIPT_DIR/logs/boot.log"; }
    # Hide cursor + imprime header FIXO uma vez + 1 espaco placeholder.
    # Loop usa \b (backspace) para voltar 1 char e sobrescrever -- funciona
    # em qualquer terminal. Paleta espelha banner.py:_build_wide.
    printf "\x1b[?25l\r  ${PURPLE}\$${NC} ${PRIMARY}nyx${PURPLE}.${PRIMARY}code${NC}  ${DIM}aquecendo${NC}   "
    # SPRINT 241 hotfix spinner-anim: removido `local` em subshell.
    # Em bash, `local` SO funciona dentro de função -- subshell ( ... )
    # nao herda esse escopo. Com `set -u`, `local` em subshell aborta
    # silenciosamente, congelando o spinner no primeiro frame.
    (
        _frames='|/-\'
        _i=0
        while :; do
            _s=${_frames:$_i:1}
            printf "\b${DIM}%s${NC}" "$_s"
            _i=$(( (_i+1) % 4 ))
            sleep 0.5
        done
    ) &
    BOOT_SPINNER_PID=$!
    disown "$BOOT_SPINNER_PID" 2>/dev/null || true
}
stop_boot_spinner() {
    [ "$BOOT_SPINNER_ACTIVE" -eq 0 ] && return 0
    BOOT_SPINNER_ACTIVE=0
    # Mata spinner com TERM primeiro, depois KILL se sobreviver. Sem wait
    # porque PID disowned pode travar `wait` no shell pai.
    [ -n "$BOOT_SPINNER_PID" ] && kill -TERM "$BOOT_SPINNER_PID" 2>/dev/null || true
    [ -n "$BOOT_SPINNER_PID" ] && kill -KILL "$BOOT_SPINNER_PID" 2>/dev/null || true
    BOOT_SPINNER_PID=""
    # Restaura log_nyx/log_ok visiveis (para cleanup ao sair do CLI).
    log_nyx()  { echo -e "  ${PRIMARY}[nyx]${NC} $1"; }
    log_ok()   { echo -e "  ${GREEN}[nyx]${NC} $1"; }
    # Mostra cursor de volta e limpa linha do spinner.
    printf "\r\x1b[2K\x1b[?25h"
}

# ─── CARREGAR .env ────────────────────────────────────────
if [ -f "$SCRIPT_DIR/.env" ]; then
    set -a
    source "$SCRIPT_DIR/.env"
    set +a
fi

# ─── CARREGAR ~/.config/nyx/secrets (precedência sobre .env) ─
# Padrão XDG: secrets em ~/.config/nyx/secrets chmod 600.
# Carregado depois para sobrescrever valores do .env (precedência secrets).
SECRETS_FILE="${XDG_CONFIG_HOME:-$HOME/.config}/nyx/secrets"
if [ -f "$SECRETS_FILE" ]; then
    set -a
    # shellcheck source=/dev/null
    source "$SECRETS_FILE"
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
# UX-LIFECYCLE-01: lock file de single-instance. Fonte única vem do
# defaults.py via env var. Sem fallback divergente — mesmo path.
NYX_PID_FILE="${NYX_PID_FILE:-/tmp/nyx.pid}"

# ─── PARSE FLAGS ──────────────────────────────────────────
MODEL="${NYX_MODEL:-qwen2.5-coder:3b}"
DEBUG=0
HEADLESS=0
GAUNTLET=0
GAUNTLET_ONLY="completo"
# K08-VRAM-RUNNER-ISOLATION-01: comportamento do pre-flight K-08.
GAUNTLET_STRICT_VRAM=0
GAUNTLET_ISOLATE_VRAM=0
GAUNTLET_WITH_QWEN3=0
COCKPIT_BG=0
EXTRA_ARGS=()

while [[ $# -gt 0 ]]; do
    case "$1" in
        --smoke)
            # Smoke check: prova que imports resolvem sem subir Ollama/proxy.
            exec "$SCRIPT_DIR/venv/bin/python" "$SCRIPT_DIR/nyx/cli.py" --smoke
            ;;
        --onboarding)
            # Replay do wizard de primeiro uso (ONBOARDING-REPLAY-FLAG-01).
            exec "$SCRIPT_DIR/venv/bin/python" "$SCRIPT_DIR/nyx/cli.py" --onboarding
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
        --strict-vram)
            GAUNTLET_STRICT_VRAM=1
            shift ;;
        --isolate-vram)
            GAUNTLET_ISOLATE_VRAM=1
            shift ;;
        --with-qwen3)
            # INFRA-GAUNTLET-E2E-THINKING-01: ativa P-09b (E2E real
            # com qwen3:4b). Gating + VRAM check no nyx_gauntlet.py.
            GAUNTLET_WITH_QWEN3=1
            shift ;;
        --aesthetic)
            # VISUAL-LAYOUT-08: seta aesthetic visual antes do exec.
            # Aceita 'aesthetic' ou 'aesthetic:entity' (ex: arcano:luna).
            if [[ "$2" == *":"* ]]; then
                export NYX_AESTHETIC="${2%%:*}"
                export NYX_ENTITY="${2##*:}"
            else
                export NYX_AESTHETIC="$2"
            fi
            shift 2 ;;
        --entity)
            export NYX_ENTITY="$2"
            shift 2 ;;
        --menu)
            # NYX-MENU-WIZARD-01: TUI wizard interativo antes do exec.
            # Salva config em ~/.nyx/config.toml + exporta env vars.
            NYX_MENU_EMIT=1 "$SCRIPT_DIR/venv/bin/python" "$SCRIPT_DIR/scripts/menu_wizard.py" \
                > /tmp/nyx_menu_exports.sh
            wizard_rc=$?
            if [ $wizard_rc -eq 0 ] && [ -s /tmp/nyx_menu_exports.sh ]; then
                # shellcheck source=/dev/null
                source /tmp/nyx_menu_exports.sh
                rm -f /tmp/nyx_menu_exports.sh
            else
                rm -f /tmp/nyx_menu_exports.sh
                if [ $wizard_rc -ne 0 ]; then
                    echo "  ${ORANGE}[nyx]${NC} menu cancelado; bootando com defaults"
                fi
            fi
            shift ;;
        --web|--cockpit)
            # Sobe o cockpit FastAPI (COCKPIT-01..05) e abre o browser default.
            # Bind 127.0.0.1:11437 (ADR-001 Local First).
            COCKPIT_BG=1
            shift ;;
        --auto-approve)
            export NYX_AUTO_APPROVE=1
            shift ;;
        --num-predict)
            # NYX-OUTPUT-LIMITS-01: override de num_predict para debug.
            # Capado em 8192 dentro do proxy (anti-runaway CPU-bound).
            export NYX_NUM_PREDICT_OVERRIDE="$2"
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
# INFRA-KVCACHE-QUANT-01 (ADR-032): quantiza o KV cache de f16 para 8 bits.
# Com flash attention (acima) ligado, corta ~metade da VRAM do cache, perda de
# qualidade negligenciavel -- faz o qwen2.5-coder:3b caber com mais folga na RTX
# 3050 4GB mesmo com Chrome/Spotify/Discord abertos. A infra carrega o modelo nas
# costas; a solucao nunca e trocar modelo/placa (ADR-031/ADR-034).
export OLLAMA_KV_CACHE_TYPE="${NYX_KV_CACHE_TYPE:-q8_0}"

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
# ANTHROPIC_API_KEY é mantida (necessária para auth da TUI, vem de ~/.config/nyx/secrets ou .env)

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

# ─── SINGLE-INSTANCE LOCK ────────────────────────────────
# UX-LIFECYCLE-01: garante única instância de run.sh.
# Lock vivo (PID respondendo) é morto via SIGTERM com timeout 5s,
# SIGKILL fallback se sobreviver. Lock stale (PID morto) é sobrescrito.
#
# Bash em `wait $CHILD` ou aguardando exec de filho não roda trap até
# o filho retornar — então também encerramos a árvore de descendentes
# diretamente (Ollama + proxy + cli.py) para garantir cleanup completo.
acquire_lock() {
    if [ -f "$NYX_PID_FILE" ]; then
        local OLD_PID
        OLD_PID=$(cat "$NYX_PID_FILE" 2>/dev/null)
        if [ -n "$OLD_PID" ] && kill -0 "$OLD_PID" 2>/dev/null; then
            log_nyx "Matando instância anterior (PID $OLD_PID)..."
            kill -TERM "$OLD_PID" 2>/dev/null || true
            # Encerra descendentes diretamente em paralelo ao trap do shell pai.
            local OLD_DESC
            OLD_DESC=$(pgrep -P "$OLD_PID" 2>/dev/null || true)
            if [ -n "$OLD_DESC" ]; then
                kill -TERM $OLD_DESC 2>/dev/null || true
            fi
            for i in 1 2 3 4 5; do
                kill -0 "$OLD_PID" 2>/dev/null || break
                sleep 1
            done
            if kill -0 "$OLD_PID" 2>/dev/null; then
                log_warn "PID $OLD_PID sobreviveu SIGTERM, enviando SIGKILL"
                # SIGKILL também na árvore para evitar órfãos reparented ao init.
                local OLD_DESC2
                OLD_DESC2=$(pgrep -P "$OLD_PID" 2>/dev/null || true)
                if [ -n "$OLD_DESC2" ]; then
                    kill -KILL $OLD_DESC2 2>/dev/null || true
                fi
                kill -KILL "$OLD_PID" 2>/dev/null || true
            fi
        elif [ -n "$OLD_PID" ]; then
            log_boot "Lock stale (PID $OLD_PID morto), sobrescrevendo"
        fi
    fi
    echo "$$" > "$NYX_PID_FILE"
}

# ─── PARAR OLLAMA EXISTENTE ──────────────────────────────
# INFRA-BOOT-HANG-DIAGNOSE-01 (2026-05-25): lsof -ti:PORT trava
# indefinidamente neste sistema (testado: 5+ rodadas com timeout 2s
# todas estouram em 11435 E 8000 — não é especifico do Ollama). Usar
# `ss -Hltnp` que retorna em <30ms. Fallback timeout em lsof se ss
# falhar por iproute2 ausente. Veja boot.log para histórico de hangs.
_port_owner_pid() {
    local port="$1"
    # ss canônico (iproute2, rápido, POSIX-friendly em Linux moderno)
    if command -v ss >/dev/null 2>&1; then
        ss -Hltnp 2>/dev/null | awk -v p="$port" '
        {
            split($4, a, ":"); lp = a[length(a)]
            if (lp == p && match($0, /pid=[0-9]+/)) {
                s = substr($0, RSTART, RLENGTH); sub("pid=", "", s); print s; exit
            }
        }'
        return 0
    fi
    # Fallback: lsof com timeout 2s (defensivo — sistema sem ss).
    timeout 2 lsof -nP -ti:"$port" 2>/dev/null | head -1 || true
}

kill_existing_ollama() {
    # Parar proxy anterior
    pkill -f "nyx/proxy.py" 2>/dev/null || true

    # TUI-FIX-WEB-SESSION-REAP-01 (ONDA-34): reap de cockpit/CLI órfãos.
    # Em modo --web o cockpit é disowned/reparented (deixa de ser descendente
    # do run.sh anterior), então escapa do acquire_lock (pgrep -P pega só filhos
    # diretos) e some do pid file. Resultado: cockpit.server / cli.py stale
    # bloqueavam a nova sessão com "outra sessão PTY ativa" (amontoamento).
    # pkill por padrão garante slate limpo a cada boot, independente do pid file.
    pkill -f "nyx.cockpit.server" 2>/dev/null || true
    pkill -f "nyx/cli.py" 2>/dev/null || true

    local existing_pid
    existing_pid=$(_port_owner_pid "$NYX_OLLAMA_PORT")
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
    # INFRA-OLLAMA-RUNNER-ORPHAN-CLEANUP-01 (ADR-034): VRAM escassa (RTX 3050 4GB)
    # => UM projeto por vez usa o Ollama. Mata QUALQUER ollama serve/runner de
    # qualquer projeto (Luna etc.) para o Nyx ter a GPU inteira no boot. Os
    # `ollama runner` (filhos do serve) viram ÓRFÃOS quando o serve morre por
    # SIGKILL/crash -- escapam do kill do serve e seguram VRAM/RAM; reapados aqui
    # explicitamente. Achado: 8 runners órfãos acumulados de sessões anteriores.
    pkill -f "ollama serve" 2>/dev/null || true
    pkill -9 -f "ollama runner" 2>/dev/null || true

    log_boot "Limpando cache..."
    sleep 1
}

# ─── INICIAR OLLAMA ──────────────────────────────────────
start_ollama() {
    log_boot "Iniciando Ollama na porta $NYX_OLLAMA_PORT..."
    mkdir -p "$SCRIPT_DIR/logs"

    "$OLLAMA_BIN" serve >> "$SCRIPT_DIR/logs/ollama.log" 2>&1 &
    OLLAMA_PID=$!
    # disown: remove o background da jobs table. Se o OOM-killer matar
    # Ollama durante a pré-carga, bash não vaza "Morto" no stdout do pai.
    # `kill $PID` continua funcional; só `wait` e `kill 0` perdem o PID.
    disown "$OLLAMA_PID" 2>/dev/null || true

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
# TUI-SHUTDOWN-SILENT-01: PID foi disowned no start_ollama, logo `wait` não
# tem o filho na jobs table e retorna 127. Substituído por busy-loop curto
# com kill -0 (poll de morte) — mesma semântica sem ruído de "not a child".
stop_ollama() {
    if [ -n "$OLLAMA_PID" ] && kill -0 "$OLLAMA_PID" 2>/dev/null; then
        log_nyx "Parando Ollama (PID: $OLLAMA_PID)..."
        kill "$OLLAMA_PID" 2>/dev/null || true
        # Aguarda até 5s pela morte do processo (poll de 100ms).
        local n=0
        while kill -0 "$OLLAMA_PID" 2>/dev/null && [ "$n" -lt 50 ]; do
            sleep 0.1
            n=$((n + 1))
        done
    fi
    # Garantir que não ficou nenhum processo do nosso Ollama
    pkill -f "$OLLAMA_BIN serve" 2>/dev/null || true
    # INFRA-OLLAMA-RUNNER-ORPHAN-CLEANUP-01: reap dos runners ao sair -- o Nyx não
    # deixa `ollama runner` órfão segurando VRAM para a próxima sessão/projeto.
    pkill -9 -f "ollama runner" 2>/dev/null || true
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
# Duas chamadas em série via proxy para cobrir cold start de pesos + path
# com tools. Reduz primeira chamada da sessão de ~22s (cold) para <= 8s (P95).
# Em low-VRAM (<1500 MiB livre) faz só a saudação curta com log de warning.
# Pré-condição: proxy precisa estar pronto (NYX_PROXY_PORT respondendo).
warmup_model() {
    local started
    started=$(date +%s)
    log_boot "Aquecendo modelo $MODEL (warmup duplo via proxy)..."

    # Detecta VRAM livre se nvidia-smi disponível
    local vram_free_mib=99999
    if command -v nvidia-smi &> /dev/null; then
        local raw
        raw=$(nvidia-smi --query-gpu=memory.free --format=csv,noheader,nounits 2>/dev/null | head -1)
        if [[ "$raw" =~ ^[0-9]+$ ]]; then
            vram_free_mib="$raw"
        fi
    fi

    # Warmup 1: saudação curta via proxy (exercita o path de chat puro)
    local r1
    r1=$(curl -sf --max-time 30 \
        "http://127.0.0.1:${NYX_PROXY_PORT}/v1/chat/completions" \
        -H "Content-Type: application/json" \
        -d "{\"model\":\"$MODEL\",\"messages\":[{\"role\":\"user\",\"content\":\"oi\"}],\"max_tokens\":5}" 2>&1)

    if ! echo "$r1" | grep -q '"choices"'; then
        log_warn "Warmup 1 (saudação) retornou resposta inesperada"
        if [ "$DEBUG" -eq 1 ]; then
            log_boot "Warmup 1 resposta: $r1"
        fi
    fi

    # Low-VRAM guard: pula warmup 2 (tool-like) para evitar OOM em GPU apertada
    if [ "$vram_free_mib" -lt 1500 ]; then
        log_boot "VRAM livre ${vram_free_mib} MiB < 1500; pulando warmup com tools (low-VRAM)"
        log_boot "Modelo aquecido (modo low-VRAM, $(($(date +%s) - started))s)"
        return 0
    fi

    # Warmup 2: tool-like via proxy (exercita path com tools no proxy + Ollama)
    local r2
    r2=$(curl -sf --max-time 30 \
        "http://127.0.0.1:${NYX_PROXY_PORT}/v1/chat/completions" \
        -H "Content-Type: application/json" \
        -d "{\"model\":\"$MODEL\",\"messages\":[{\"role\":\"user\",\"content\":\"leia README\"}],\"max_tokens\":20,\"tools\":[{\"type\":\"function\",\"function\":{\"name\":\"Read\",\"description\":\"Le arquivo\",\"parameters\":{\"type\":\"object\",\"properties\":{\"path\":{\"type\":\"string\"}},\"required\":[\"path\"]}}}]}" 2>&1)

    if ! echo "$r2" | grep -q '"choices"'; then
        log_warn "Warmup 2 (tool-like) retornou resposta inesperada"
        if [ "$DEBUG" -eq 1 ]; then
            log_boot "Warmup 2 resposta: $r2"
        fi
    fi

    local elapsed=$(($(date +%s) - started))
    log_boot "Modelo aquecido (warmup duplo, ${elapsed}s)"
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
# UX-LIFECYCLE-01: cobre EXIT/SIGINT/SIGTERM/SIGHUP. Idempotente:
# trap EXIT pode reentrar via sub-signals; chamadas a kill com PID
# inexistente são silenciadas.
# TUI-SHUTDOWN-SILENT-01: PIDs foram disowned, então não há report
# implícito de "Morto" no stdout do shell pai. Cleanup permanece intacto.
cleanup() {
    # SPRINT 237: para spinner antes de qualquer log visivel (caso Ctrl+C
    # durante boot, stdout ainda esta silenciado e log_nyx ficaria invisivel).
    stop_boot_spinner 2>/dev/null || true
    echo ""
    log_nyx "Desconectando..."
    # Parar proxy
    if [ -n "${PROXY_PID:-}" ] && kill -0 "$PROXY_PID" 2>/dev/null; then
        kill "$PROXY_PID" 2>/dev/null || true
    fi
    pkill -f "nyx/proxy.py" 2>/dev/null || true
    stop_ollama
    # Remove lock só se ainda for nosso (PID dentro == $$).
    if [ -f "$NYX_PID_FILE" ]; then
        local LOCK_PID
        LOCK_PID=$(cat "$NYX_PID_FILE" 2>/dev/null)
        if [ "$LOCK_PID" = "$$" ] || [ -z "$LOCK_PID" ]; then
            rm -f "$NYX_PID_FILE" 2>/dev/null || true
        fi
    fi
    log_ok "Fim."
}

# SPRINT 237 hotfix: trap separado para SIGINT/SIGTERM/SIGHUP que adiciona
# exit explicito apos cleanup. Sem isso, Ctrl+C durante boot chamava
# cleanup mas shell voltava a executar a linha seguinte (warmup_model
# continuava), CLI abria, Ctrl+C parecia ignorado.
trap cleanup EXIT
trap 'cleanup; exit 130' SIGINT SIGTERM SIGHUP

# ═══════════════════════════════════════════════════════════
# EXECUÇÃO PRINCIPAL
# ═══════════════════════════════════════════════════════════

validate

# SPRINT 237 UX-BOOT-SILENT-SPINNER-01: spinner único `$ nyx.code aquecendo...`
# substitui stream de mensagens `[nyx]` durante boot. Ativado apos validate
# (validate pode imprimir erros criticos via log_err em stderr que devem
# aparecer ANTES do spinner; com spinner ativo, log_err continua visivel).
start_boot_spinner

# UX-LIFECYCLE-01: lock antes de qualquer side effect.
# Mata instância anterior gracefully; instância anterior limpa seu Ollama
# via trap cleanup, então kill_existing_ollama abaixo só limpa órfãos.
acquire_lock

# ─── AUTO-ATUALIZAR EXECUTAR_SPRINT.md ───────────────────
# Não-bloqueante. Lê SPRINT_ORDER_MASTER.md, detecta próxima PENDENTE,
# atualiza EXECUTAR_SPRINT.md se o ID mudou. Falha silencioso (|| true).
# < /dev/null defensivo: subprocess herda stdin do shell; se algum FD
# estiver em estado estranho, isolar evita propagar para o python.
if [ -x "$SCRIPT_DIR/venv/bin/python" ] && [ -f "$SCRIPT_DIR/scripts/update_next_sprint.py" ]; then
    _next_info="$("$SCRIPT_DIR/venv/bin/python" "$SCRIPT_DIR/scripts/update_next_sprint.py" 2>/dev/null < /dev/null || true)"
    if [ -n "$_next_info" ]; then
        log_boot "$_next_info"
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
# ANTHROPIC_API_KEY vem de ~/.config/nyx/secrets (precedência) ou .env (necessária para auth da TUI)

# ─── PRÉ-VERIFICAÇÃO VRAM LIVE (BOOT-VRAM-GUARD-01) ──────
# VRAM livre pode mudar entre auto_tune_gpu (T0) e o momento da pré-carga
# (T0 + alguns segundos): browser/DE consumindo VRAM, daemon de outra
# sessão, etc. detect_gpu.py --strict-low-vram re-mede agora e usa reserva
# ampliada. Retorna 0 em low-VRAM (<1.5 GiB) sinalizando skip seguro.
SKIP_PRELOAD=0
if [ -x "$SCRIPT_DIR/venv/bin/python" ]; then
    log_boot "Pré-verificando VRAM..."
    PRELOAD_NUM_GPU=$("$SCRIPT_DIR/venv/bin/python" \
        "$SCRIPT_DIR/scripts/detect_gpu.py" \
        --for-model "$MODEL" --strict-low-vram 2>/dev/null || echo "0")
    if [[ ! "$PRELOAD_NUM_GPU" =~ ^[0-9]+$ ]]; then
        PRELOAD_NUM_GPU=0
    fi
    if [ "$PRELOAD_NUM_GPU" = "0" ]; then
        log_boot "VRAM insuficiente para pré-carga. Modelo carrega na 1ª requisição."
        SKIP_PRELOAD=1
    elif [ "$PRELOAD_NUM_GPU" != "$NYX_NUM_GPU" ]; then
        log_boot "VRAM mudou: ajustando num_gpu de $NYX_NUM_GPU para $PRELOAD_NUM_GPU"
        NYX_NUM_GPU="$PRELOAD_NUM_GPU"
        export NYX_NUM_GPU
    fi
fi

# ─── PRE-CARGA DELEGADA AO WARMUP VIA PROXY ──────────────
# SPRINT 235 INFRA-PRELOAD-VIA-PROXY-01 (2026-05-25): bloco antigo de
# pré-carga via curl direto ao Ollama (porta 11435) foi REMOVIDO porque
# bypassava toda infra de resiliência do proxy. Fragmentação de VRAM
# (Chrome+X11) fazia `ggml_cuda_pool_vmm5alloc` falhar mesmo com 3.7 GiB
# livres, gerando warning visível ao usuário a cada boot.
#
# Solução estrutural: `warmup_model` abaixo (linha 629+) já faz exatamente
# a mesma coisa MAS via proxy (porta 11436), que tem INFRA-OOM-RETRY-STEP-01
# para degradar num_gpu automaticamente (12→6→3→0 CPU) sem expor erro.
# Redundância eliminada; vetor do warning fechado.
log_boot "Pré-carga delegada ao warmup via proxy (sprint 235)."

# ─── INICIAR PROXY (think=false para tool calling) ───────
log_boot "Iniciando proxy na porta $NYX_PROXY_PORT..."
"$SCRIPT_DIR/venv/bin/python" "$SCRIPT_DIR/nyx/proxy.py" \
    --port "$NYX_PROXY_PORT" \
    --ollama-port "$NYX_OLLAMA_PORT" \
    --num-gpu "$NYX_NUM_GPU" \
    >> "$SCRIPT_DIR/logs/proxy.log" 2>&1 &
PROXY_PID=$!
# disown: idem ao start_ollama. Evita "Morto" no terminal se proxy
# cair em background. Cleanup usa `kill $PROXY_PID` explicitamente.
disown "$PROXY_PID" 2>/dev/null || true
sleep 2

if curl -sf "http://127.0.0.1:${NYX_PROXY_PORT}/v1/models" > /dev/null 2>&1; then
    log_boot "Proxy pronto (PID: $PROXY_PID)"
else
    log_err "Proxy não iniciou. Verifique logs/proxy.log"
    exit 1
fi

# ─── COCKPIT (--web / --cockpit) ──────────────────────────
if [ "$COCKPIT_BG" -eq 1 ]; then
    log_boot "Subindo cockpit em 127.0.0.1:11437..."
    # UX-COCKPIT-CHROME-CLOSE-SHUTDOWN-01: sinaliza ao cockpit que ele foi subido
    # por run.sh --web; ao fechar o navegador (WS disconnect real), o cockpit
    # manda SIGTERM ao grupo do run.sh para shutdown ordenado (trap cleanup).
    export NYX_COCKPIT_FROM_RUN_SH=1
    "$SCRIPT_DIR/venv/bin/python" -m nyx.cockpit.server \
        >> "$SCRIPT_DIR/logs/cockpit.log" 2>&1 &
    COCKPIT_PID=$!
    disown "$COCKPIT_PID" 2>/dev/null || true
    sleep 2
    if curl -sf http://127.0.0.1:11437/health > /dev/null 2>&1; then
        log_boot "Cockpit pronto (PID: $COCKPIT_PID)"
        # TUI-FIX-WEB-PIDFILE-BOOT-RACE-01 (ONDA-34): cede o lock /tmp/nyx.pid
        # AGORA (cockpit UP), não só na linha do sleep loop (pós-warmup, ~6s
        # depois). Causa-raiz do "outra sessão PTY ativa": o cockpit fica healthy
        # antes do rm; se um cliente conecta nessa janela, o PtyBridge.preflight
        # lê o PRÓPRIO PID do run.sh em /tmp/nyx.pid e recusa como "sessão ativa".
        # Cedendo aqui, o preflight vê lock livre e spawna a TUI normalmente.
        rm -f "$NYX_PID_FILE" 2>/dev/null || true
        # SPRINT 239 hotfix3: abre DIRETO em /static/terminal.html (REPL)
        # ao inves de / (dashboard de cards) -- usuario quer conversar com a
        # Nyx imediatamente, nao ver feature catalog.
        if command -v xdg-open >/dev/null 2>&1; then
            xdg-open http://127.0.0.1:11437/static/terminal.html > /dev/null 2>&1 &
            log_nyx "browser aberto em http://127.0.0.1:11437/static/terminal.html"
        else
            log_nyx "abra http://127.0.0.1:11437/static/terminal.html no browser"
        fi
    else
        log_warn "Cockpit falhou. Veja logs/cockpit.log"
    fi
fi

# Warmup duplo via proxy (chamada curta + chamada com tools).
# Reduz cold start da primeira mensagem do usuário de ~22s para <= 8s.
# Pulado em modo gauntlet (próprio gauntlet exercita as fases) e --smoke.
#
# SPRINT 237 UX-BOOT-SILENT-SPINNER-01 reverte 236: warmup volta bloqueante
# para que o spinner único `$ nyx.code aquecendo...` aguarde o aquecimento
# completar antes de abrir o CLI. Usuário quer ver a interface só quando
# tudo estiver pronto, não ver prompt enquanto modelo ainda aquece.
if [ "$GAUNTLET" -eq 0 ]; then
    # SPRINT 241 hotfix warmup-timeout: limita warmup a 6s. Quando proxy
    # degrada para CPU (OOM em GPU fragmentada -- caso comum com Chrome
    # rodando, oom_recovery_count=85 historico), warmup em CPU leva 9-11s
    # gerando UX de "trava na tela aquecendo". Com timeout, boot completa
    # em <8s; primeira mensagem real do usuario absorve cold start via
    # INFRA-OOM-RETRY-STEP-01 (sprint 125aa). Trade-off aceito: 1a msg
    # marginalmente mais lenta vs boot rapido + interface visivel.
    warmup_model &
    _warmup_pid=$!
    # TUI-FIX-WARMUP-KILL-NOISE-01 (ONDA-33): disown tira o job da tabela do
    # shell para que o SIGKILL do timeout abaixo NÃO vaze a mensagem de job
    # control ("linha NNN: PID Morto warmup_model") na tela de boot. kill -0 e
    # kill -9 seguem funcionando por PID mesmo após disown.
    disown "$_warmup_pid" 2>/dev/null || true
    _warmup_done=0
    for _ in $(seq 1 60); do  # 60 * 100ms = 6s ceiling
        if ! kill -0 "$_warmup_pid" 2>/dev/null; then
            _warmup_done=1
            break
        fi
        sleep 0.1
    done
    if [ "$_warmup_done" -eq 0 ]; then
        kill -9 "$_warmup_pid" 2>/dev/null || true
        log_boot "Warmup timeout 6s -- primeira mensagem absorve cold start (INFRA-OOM-RETRY-STEP)"
    fi
fi

NYX_SYSTEM_PROMPT="Sou Nyx. Codificadora. Vivo no terminal.

Regras:
- PT-BR. Frases curtas. Sem emojis. Sem verbosidade.
- Use tools (Read, Write, Edit, Bash, Glob, Grep) para tudo. Não descreva. Execute.
- Formato: diagnóstico -> solução -> verificação.
- Tom: técnico, direto, preciso.
- Acesso total ao sistema de arquivos local.
- Diretório: $(pwd)

Código limpo não é arte. É higiene.
Ler -> Escrever -> Testar -> Terminar."

# ─── GAUNTLET (se --gauntlet) ─────────────────────────────
if [ "$GAUNTLET" -eq 1 ]; then
    log_nyx "Executando Gauntlet (fase: $GAUNTLET_ONLY)..."
    # K08-VRAM-RUNNER-ISOLATION-01: forward dos flags de VRAM.
    GAUNTLET_VRAM_ARGS=()
    [ "$GAUNTLET_STRICT_VRAM" -eq 1 ] && GAUNTLET_VRAM_ARGS+=(--strict-vram)
    [ "$GAUNTLET_ISOLATE_VRAM" -eq 1 ] && GAUNTLET_VRAM_ARGS+=(--isolate-vram)
    # INFRA-GAUNTLET-E2E-THINKING-01: propaga gating de P-09b via env var.
    if [ "$GAUNTLET_WITH_QWEN3" -eq 1 ]; then
        export NYX_GAUNTLET_WITH_QWEN3=1
    fi
    "$SCRIPT_DIR/venv/bin/python" "$SCRIPT_DIR/scripts/gauntlet/nyx_gauntlet.py" \
        --proxy-url "http://127.0.0.1:${NYX_PROXY_PORT}" \
        --ollama-url "http://${NYX_OLLAMA_HOST}:${NYX_OLLAMA_PORT}" \
        --only "$GAUNTLET_ONLY" \
        --model "$MODEL" \
        "${GAUNTLET_VRAM_ARGS[@]}"
    EXIT_CODE=$?

    # Auto-atualizar docs após gauntlet
    log_nyx "Atualizando docs..."
    "$SCRIPT_DIR/venv/bin/python" "$SCRIPT_DIR/scripts/update_docs.py" 2>/dev/null || true

    exit "$EXIT_CODE"
fi

# ─── TUI-REDESIGN-28-09: endmark de boot removido do terminal ───
# Token GLYPHS_BOOT["endmark"] preservado em design_tokens.py para uso
# programático futuro, mas não renderizado mais antes do banner do REPL.

# ─── SINCRONIZAR DOCS (idempotente, best-effort) ───────────
# Roda em todos modos interativos (REPL default, --web, --menu).
# Pulado em --headless (preserva JSON stdout) e --gauntlet (já chama pós-run).
# Custo: ~290ms se nada mudou, ~50ms se houver write. Output suprimido para
# não poluir o banner do REPL — falhas silenciam via `|| true`.
if [ "$HEADLESS" -eq 0 ]; then
    "$SCRIPT_DIR/venv/bin/python" "$SCRIPT_DIR/scripts/update_docs.py" >/dev/null 2>&1 || true
fi

# ─── INICIAR NYX CLI (Python) ─────────────────────────────
log_boot "Iniciando Nyx CLI..."
# SPRINT 237 UX-BOOT-SILENT-SPINNER-01: para spinner e restaura stdout
# antes de entregar o terminal ao CLI Python (que precisa de TTY limpa).
stop_boot_spinner

# SPRINT 239 UX-WEB-NO-LOCAL-CLI-01: em modo --web/--cockpit, o CLI é
# servido via PTY bridge do cockpit em /repl (WebSocket + xterm.js).
# Subir cli.py local aqui duplicaria o consumidor de PTY e dispararia o
# guard de sessão PTY exclusiva do cockpit. Bloqueia o script com
# sleep loop; trap cleanup (linha 590-591) mata cockpit + proxy + ollama
# em Ctrl+C/SIGTERM/SIGHUP. Modo default (sem --web) preserva o exec
# antigo byte-a-byte.
if [ "$COCKPIT_BG" -eq 1 ]; then
    # SPRINT 239 hotfix2: em --web o cockpit é dono do PTY (via PtyBridge.preflight
    # no /repl WS). O lock /tmp/nyx.pid setado por acquire_lock faz o cockpit
    # recusar conexão WS com "outra sessao PTY ativa" (server.py:566). Cedemos
    # o lock após o cockpit subir; o ciclo de vida fica gerenciado pelo trap
    # cleanup do run.sh + pelo próprio cockpit que controla PTY exclusiva.
    rm -f "$NYX_PID_FILE" 2>/dev/null || true
    echo ""
    log_nyx "Cockpit pronto em http://127.0.0.1:11437/"
    log_nyx "Pressione Ctrl+C para encerrar."
    echo ""
    while true; do sleep 60; done
fi

# INFRA-HEADLESS-FLAG-ROUTE-01 (#350): propaga --headless ao cli.py quando o
# usuario pediu modo headless, para honrar o protocolo JSON stdin/stdout
# (cli_headless.run_headless). Antes o exec ia sem a flag e caia no loop input()
# nao-TTY, contrariando o comentario "preserva JSON stdout" e o help do --headless.
# Gauntlet sai antes (linha ~834) e --web fica no while sleep (linha ~874): so o
# headless puro chega aqui com HEADLESS=1; o REPL default segue sem a flag.
if [ "$HEADLESS" -eq 1 ]; then
    "$SCRIPT_DIR/venv/bin/python" "$SCRIPT_DIR/nyx/cli.py" --headless
else
    "$SCRIPT_DIR/venv/bin/python" "$SCRIPT_DIR/nyx/cli.py"
fi
EXIT_CODE=$?

exit "$EXIT_CODE"


# "O segredo da liberdade é a coragem." -- Péricles
