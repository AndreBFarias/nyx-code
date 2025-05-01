#!/bin/bash
# Stress test do Nyx-Code - simula uso real via proxy
# Testa: Read, Write, Edit, Bash, Glob, Grep + chat

set -uo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/../.." && pwd)"
cd "$PROJECT_DIR"

# Cores Nyx
PRIMARY='\033[38;2;0;212;170m'
RED='\033[38;2;255;107;107m'
GREEN='\033[38;2;0;212;170m'
FG='\033[38;2;232;232;232m'
NC='\033[0m'
BOLD='\033[1m'

PROXY_URL="http://127.0.0.1:11436/v1/chat/completions"
MODEL="qwen3:4b"
LOG_DIR="$PROJECT_DIR/logs/stress"
RESULTS_FILE="$LOG_DIR/results.txt"

mkdir -p "$LOG_DIR"
echo "" > "$RESULTS_FILE"

TOTAL=0
PASSED=0
FAILED=0

log_test() { echo -e "${PRIMARY}[stress]${NC} $1"; }
log_pass() { echo -e "${GREEN}[PASS]${NC} $1"; echo "PASS: $1" >> "$RESULTS_FILE"; PASSED=$((PASSED + 1)); TOTAL=$((TOTAL + 1)); }
log_fail() { echo -e "${RED}[FAIL]${NC} $1"; echo "FAIL: $1" >> "$RESULTS_FILE"; FAILED=$((FAILED + 1)); TOTAL=$((TOTAL + 1)); }

send_request() {
    local description="$1"
    local payload="$2"
    local timeout="${3:-120}"

    log_test "Enviando: $description..."

    local response
    response=$(curl -sf --max-time "$timeout" "$PROXY_URL" \
        -H "Content-Type: application/json" \
        -d "$payload" 2>&1)
    local exit_code=$?

    if [ $exit_code -ne 0 ]; then
        log_fail "$description (curl timeout/erro: $exit_code)"
        echo "  Detalhes: curl exit=$exit_code" >> "$RESULTS_FILE"
        return 1
    fi

    # Extrair info da resposta
    local analysis
    analysis=$(echo "$response" | python3 -c "
import json, sys
try:
    d = json.load(sys.stdin)
    msg = d['choices'][0]['message']
    tc = msg.get('tool_calls', [])
    content = msg.get('content', '')
    finish = d['choices'][0].get('finish_reason', '')
    tokens = d.get('usage', {}).get('total_tokens', 0)

    if tc:
        tools = [t['function']['name'] for t in tc]
        args_list = [t['function']['arguments'] for t in tc]
        print(f'TOOL_CALL|{tools}|{args_list}|{tokens}')
    else:
        clean = content.replace(chr(10), ' ')[:150]
        print(f'TEXT|{clean}|{finish}|{tokens}')
except Exception as e:
    print(f'ERROR|{e}')
" 2>/dev/null)

    local tipo=$(echo "$analysis" | cut -d'|' -f1)
    local info=$(echo "$analysis" | cut -d'|' -f2)
    local extra=$(echo "$analysis" | cut -d'|' -f3)
    local tokens=$(echo "$analysis" | cut -d'|' -f4)

    # Salvar resposta raw
    echo "$response" > "$LOG_DIR/$(echo "$description" | tr ' ' '_').json"

    echo "  Tipo: $tipo | Info: ${info:0:80} | Tokens: $tokens"
    echo "  Tipo=$tipo Info=${info:0:80} Tokens=$tokens" >> "$RESULTS_FILE"

    if [ "$tipo" = "ERROR" ]; then
        log_fail "$description (parse error: $info)"
        return 1
    fi

    # Retornar o tipo para verificação pelo chamador
    echo "$tipo|$info|$extra|$tokens"
    return 0
}

# ═══════════════════════════════════════════════════════════
echo ""
echo -e "${PRIMARY}${BOLD}Nyx-Code Stress Test${NC}"
echo -e "${FG}Simulando uso real via proxy${NC}"
echo ""

# ─── TESTE 1: Chat simples ────────────────────────────────
log_test "1/8 - Chat simples (sem tools)"
result=$(send_request "chat_simples" \
    "{\"model\":\"$MODEL\",\"messages\":[{\"role\":\"user\",\"content\":\"responda apenas: Nyx operacional\"}],\"max_tokens\":30}" \
    60)
if echo "$result" | grep -q "TEXT"; then
    log_pass "Chat simples - modelo respondeu"
else
    log_fail "Chat simples - sem resposta"
fi

# ─── TESTE 2: Read (ler arquivo) ─────────────────────────
log_test "2/8 - Tool Read (ler README.md)"
result=$(send_request "tool_read" \
    "{\"model\":\"$MODEL\",\"messages\":[{\"role\":\"user\",\"content\":\"leia o arquivo README.md\"}],\"tools\":[{\"type\":\"function\",\"function\":{\"name\":\"Read\",\"description\":\"Leia um arquivo\",\"parameters\":{\"type\":\"object\",\"properties\":{\"file_path\":{\"type\":\"string\",\"description\":\"Caminho do arquivo\"}},\"required\":[\"file_path\"]}}}],\"max_tokens\":500}" \
    120)
if echo "$result" | grep -q "TOOL_CALL.*Read"; then
    log_pass "Tool Read - chamou Read corretamente"
else
    log_fail "Tool Read - não chamou a tool"
fi

# ─── TESTE 3: Bash (executar comando) ────────────────────
log_test "3/8 - Tool Bash (ls da raiz)"
result=$(send_request "tool_bash" \
    "{\"model\":\"$MODEL\",\"messages\":[{\"role\":\"user\",\"content\":\"execute o comando: ls -la README.md\"}],\"tools\":[{\"type\":\"function\",\"function\":{\"name\":\"Bash\",\"description\":\"Executa comando no terminal\",\"parameters\":{\"type\":\"object\",\"properties\":{\"command\":{\"type\":\"string\",\"description\":\"Comando a executar\"}},\"required\":[\"command\"]}}}],\"max_tokens\":500}" \
    120)
if echo "$result" | grep -q "TOOL_CALL.*Bash"; then
    log_pass "Tool Bash - chamou Bash corretamente"
else
    log_fail "Tool Bash - não chamou a tool"
fi

# ─── TESTE 4: Glob (buscar arquivos) ─────────────────────
log_test "4/8 - Tool Glob (buscar .py)"
result=$(send_request "tool_glob" \
    "{\"model\":\"$MODEL\",\"messages\":[{\"role\":\"user\",\"content\":\"encontre todos os arquivos .py do projeto\"}],\"tools\":[{\"type\":\"function\",\"function\":{\"name\":\"Glob\",\"description\":\"Busca arquivos por padrão\",\"parameters\":{\"type\":\"object\",\"properties\":{\"pattern\":{\"type\":\"string\",\"description\":\"Glob pattern\"}},\"required\":[\"pattern\"]}}}],\"max_tokens\":500}" \
    120)
if echo "$result" | grep -q "TOOL_CALL.*Glob"; then
    log_pass "Tool Glob - chamou Glob corretamente"
else
    log_fail "Tool Glob - não chamou a tool"
fi

# ─── TESTE 5: Grep (buscar conteúdo) ─────────────────────
log_test "5/8 - Tool Grep (buscar 'think=false')"
result=$(send_request "tool_grep" \
    "{\"model\":\"$MODEL\",\"messages\":[{\"role\":\"user\",\"content\":\"busque a string think=false nos arquivos do projeto\"}],\"tools\":[{\"type\":\"function\",\"function\":{\"name\":\"Grep\",\"description\":\"Busca texto em arquivos\",\"parameters\":{\"type\":\"object\",\"properties\":{\"pattern\":{\"type\":\"string\",\"description\":\"Regex pattern\"},\"path\":{\"type\":\"string\",\"description\":\"Diretório\"}},\"required\":[\"pattern\"]}}}],\"max_tokens\":500}" \
    120)
if echo "$result" | grep -q "TOOL_CALL.*Grep"; then
    log_pass "Tool Grep - chamou Grep corretamente"
else
    log_fail "Tool Grep - não chamou a tool"
fi

# ─── TESTE 6: Write (criar arquivo) ──────────────────────
log_test "6/8 - Tool Write (criar /tmp/nyx_test.py)"
result=$(send_request "tool_write" \
    "{\"model\":\"$MODEL\",\"messages\":[{\"role\":\"user\",\"content\":\"crie o arquivo /tmp/nyx_stress_test.py com uma função hello() que retorna 'Nyx funciona'\"}],\"tools\":[{\"type\":\"function\",\"function\":{\"name\":\"Write\",\"description\":\"Cria ou sobrescreve arquivo\",\"parameters\":{\"type\":\"object\",\"properties\":{\"file_path\":{\"type\":\"string\",\"description\":\"Caminho do arquivo\"},\"content\":{\"type\":\"string\",\"description\":\"Conteúdo\"}},\"required\":[\"file_path\",\"content\"]}}}],\"max_tokens\":500}" \
    180)
if echo "$result" | grep -q "TOOL_CALL.*Write"; then
    log_pass "Tool Write - chamou Write corretamente"
else
    log_fail "Tool Write - não chamou a tool"
fi

# ─── TESTE 7: Análise de código (prompt complexo) ────────
log_test "7/8 - Análise de código bugado"
result=$(send_request "analise_bugs" \
    "{\"model\":\"$MODEL\",\"messages\":[{\"role\":\"user\",\"content\":\"leia tests/stress/buggy_service.py e liste os 3 bugs mais críticos\"}],\"tools\":[{\"type\":\"function\",\"function\":{\"name\":\"Read\",\"description\":\"Leia um arquivo\",\"parameters\":{\"type\":\"object\",\"properties\":{\"file_path\":{\"type\":\"string\",\"description\":\"Caminho do arquivo\"}},\"required\":[\"file_path\"]}}}],\"max_tokens\":500}" \
    120)
if echo "$result" | grep -q "TOOL_CALL.*Read"; then
    log_pass "Análise - chamou Read para ler o arquivo"
else
    log_fail "Análise - não chamou Read"
fi

# ─── TESTE 8: Resumo de diretório ────────────────────────
log_test "8/8 - Resumo do diretório nyx/"
result=$(send_request "resumo_dir" \
    "{\"model\":\"$MODEL\",\"messages\":[{\"role\":\"user\",\"content\":\"liste os arquivos do diretório nyx/ e descreva o que cada um faz\"}],\"tools\":[{\"type\":\"function\",\"function\":{\"name\":\"Bash\",\"description\":\"Executa comando\",\"parameters\":{\"type\":\"object\",\"properties\":{\"command\":{\"type\":\"string\"}},\"required\":[\"command\"]}}},{\"type\":\"function\",\"function\":{\"name\":\"Glob\",\"description\":\"Busca arquivos\",\"parameters\":{\"type\":\"object\",\"properties\":{\"pattern\":{\"type\":\"string\"}},\"required\":[\"pattern\"]}}}],\"max_tokens\":500}" \
    120)
if echo "$result" | grep -q "TOOL_CALL"; then
    log_pass "Resumo dir - chamou tool para explorar"
else
    log_fail "Resumo dir - não chamou nenhuma tool"
fi

# ═══════════════════════════════════════════════════════════
echo ""
echo -e "${PRIMARY}${BOLD}Resultados${NC}"
echo -e "  Total:   $TOTAL"
echo -e "  ${GREEN}Passou:  $PASSED${NC}"
echo -e "  ${RED}Falhou:  $FAILED${NC}"
echo ""
echo -e "  Logs em: $LOG_DIR/"
echo -e "  Resultados: $RESULTS_FILE"

# Salvar resumo
echo "" >> "$RESULTS_FILE"
echo "=== RESUMO ===" >> "$RESULTS_FILE"
echo "Total: $TOTAL | Passou: $PASSED | Falhou: $FAILED" >> "$RESULTS_FILE"
echo "Data: $(date)" >> "$RESULTS_FILE"

# "A disciplina é a ponte entre metas e realizações." -- Jim Rohn
