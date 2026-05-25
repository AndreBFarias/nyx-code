# SPRINT 237 — UX-BOOT-SILENT-SPINNER-01

## 0. SPEC (machine-readable)

```yaml
sprint:
  id: UX-BOOT-SILENT-SPINNER-01
  title: "Spinner unico durante boot; CLI abre so quando tudo pronto"
  onda: 31
  prioridade: ALTA
  tipo: Refactor
  dependencias: [UX-WARMUP-BACKGROUND-01]
  desbloqueia: []

  touches:
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/run.sh
      reason: "log_nyx visivel no stdout poluia boot; usuario quer spinner unico + CLI so apos warmup"
  creates: []
  removes: []

  forbidden:
    - "Quebrar gauntlet/headless (mantem comportamento sem spinner)"
    - "Esconder erros criticos (log_err deve permanecer visivel)"
    - "Tocar em logs/boot.log estrutura (logs continuam la)"

  tests:
    - cmd: "./run.sh --smoke"
      timeout: 10
      deve_passar: true
    - cmd: "bash scripts/sprint_invariants.sh"
      timeout: 30
      deve_passar: true

  acceptance_criteria:
    - "Funcoes start_boot_spinner + stop_boot_spinner em run.sh"
    - "log_warn + log_err emitem em stderr (sobrevivem ao silenciamento de stdout)"
    - "Spinner ativo entre validate e iniciar Nyx CLI"
    - "stdout do boot redirecionado para logs/boot.log durante o spinner"
    - "warmup_model VOLTA a ser bloqueante (sprint 236 revertida)"
    - "cleanup() chama stop_boot_spinner antes de log_nyx 'Desconectando...'"
    - "Smoke + invariantes preservados"
    - "Proximo `./run.sh` interativo: usuario ve apenas `$ nyx.code aquecendo |/-\\` ate CLI abrir"
```

---

# Sprint 237 — UX-BOOT-SILENT-SPINNER-01

**Status:** CONCLUIDA
**Data criação:** 2026-05-25
**Data conclusão:** 2026-05-25
**Modelo obrigatório:** claude-opus-4-7 (sem subagentes)

---

## Contexto

Observação UX do usuário apos sprint 236:

> "Não, vc tá entendendo errado. rodei o run.sh ele em background deve perguntar pro model. pra pré aquecer ele. Enquanto isso. Aperece na tela de espera no terminal. Iniciando $ Nyx.code... espera o tempo que tiver de esperar até concluir tudo e só aí abre a interface padrão. O processo continua mas o user não tem que saber. E isso tem que aparecer nos logs."

Interpretação correta:
- Sprint 236 paralelizava warmup com CLI (errado — usuario quer ESPERAR).
- Usuario quer **boot silencioso** com **spinner unico** `$ nyx.code aquecendo...`.
- CLI so abre quando warmup termina (interface padrao limpa, instantanea na 1a msg).
- Stream de `[nyx] Iniciando Ollama...` etc deve ir SOMENTE pros logs.
- Erros criticos continuam visiveis (log_err em stderr).

## Solução

### 1. Reverter sprint 236

`warmup_model` volta bloqueante (sem `&`, sem `disown`).

### 2. Funções de spinner

```bash
BOOT_SPINNER_PID=""

start_boot_spinner() {
    # Skip em headless/gauntlet/non-TTY
    if [ ! -t 1 ] || [ "${HEADLESS:-0}" -eq 1 ] || [ "${GAUNTLET:-0}" -eq 1 ]; then
        return 0
    fi
    # Salva stdout em fd 3 e silencia stdout (redireciona para boot.log)
    exec 3>&1
    exec >> "$SCRIPT_DIR/logs/boot.log"
    # Spinner em background imprime via fd 3
    (
        local frames='|/-\'
        local i=0
        while :; do
            local s=${frames:$i:1}
            printf "\r  ${PURPLE}\$${NC} ${PRIMARY}nyx${PURPLE}.${PRIMARY}code${NC}  ${DIM}aquecendo ${s}${NC}" >&3
            i=$(( (i+1) % 4 ))
            sleep 0.15
        done
    ) &
    BOOT_SPINNER_PID=$!
    disown "$BOOT_SPINNER_PID" 2>/dev/null || true
}

stop_boot_spinner() {
    [ -z "$BOOT_SPINNER_PID" ] && return 0
    kill "$BOOT_SPINNER_PID" 2>/dev/null || true
    wait "$BOOT_SPINNER_PID" 2>/dev/null || true
    BOOT_SPINNER_PID=""
    # Restaura stdout e limpa linha
    exec >&3
    exec 3>&-
    printf "\r\x1b[2K"
}
```

### 3. Posicionamento

- `start_boot_spinner` apos `validate` (linha 510): erros de validate aparecem antes.
- `stop_boot_spinner` antes do `cli.py` (linha 732): TTY restaurada para o CLI Python.
- `stop_boot_spinner` no topo de `cleanup()`: trata Ctrl+C durante boot.

### 4. log_warn/log_err em stderr

Mudanca cirurgica:

```bash
log_warn() { echo -e "  ${ORANGE}[nyx]${NC} $1" >&2; }
log_err()  { echo -e "  ${RED}[nyx]${NC} $1" >&2; }
```

Sem isso, warning durante boot iria pro arquivo silenciado e nao apareceria pro usuario.

## Fluxo novo

```
./run.sh
    ↓
validate (erros via stderr visiveis)
    ↓
start_boot_spinner
    ↓
[stdout silenciado para logs/boot.log]
    ↓
acquire_lock + kill_existing_ollama + start_ollama + check_model
+ auto_tune_gpu + start_proxy + warmup_model (bloqueante)
    ↓
[stderr permanece visivel para log_warn/log_err]
    ↓
stop_boot_spinner (limpa linha, restaura stdout)
    ↓
exec cli.py (TTY limpa, prompt "Retomar?" imediato)
```

Usuario ve durante boot:
```
  $ nyx.code  aquecendo |
  $ nyx.code  aquecendo /
  $ nyx.code  aquecendo -
  ...
```

E quando termina:
```
[banner Nyx do CLI]
Retomar última sessão (...)? [s/N]
```

## Proof-of-work

```
./run.sh --smoke    → boot ok exit 0
bash scripts/sprint_invariants.sh → PASS=14/14 FAIL=0
```

Validação interativa final (TTY real) esperada:
- `./run.sh` em terminal: ve so o spinner `$ nyx.code aquecendo |/-\`
- `tail -f logs/boot.log` em paralelo: ve todo o stream `[nyx] Iniciando Ollama...` etc
- Apos warmup terminar (~10s): spinner some, CLI abre com prompt instantaneo
- 1a mensagem real: modelo ja aquecido (latencia baixa)

## Casos protegidos

- `--smoke`: sem TTY tipico (exec); guard `[ ! -t 1 ]` skip spinner. Output normal preservado.
- `--gauntlet`: HEADLESS=1 + GAUNTLET=1; guard skip spinner. Output completo preservado.
- `--headless`: HEADLESS=1; guard skip spinner. JSON stdout preservado.
- Ctrl+C durante boot: trap chama cleanup() que chama stop_boot_spinner antes de log_nyx.
- Erro critico (validate falha, modelo nao baixa): log_err em stderr permanece visivel.

## Riscos

| Risco | Mitigação |
|---|---|
| Spinner zumbi em SIGKILL externo | trap EXIT chama cleanup que chama stop_boot_spinner |
| Race entre stop_boot_spinner e print do CLI Python | wait + sleep imperceptivel; CLI Python toma TTY apos shell limpar |
| logs/boot.log cresce sem rotação | mesmo problema pré-existente; não escopo desta sprint |
| Mensagens de info importantes (browser aberto em http://...) ficam invisíveis em --web | cockpit ja faz xdg-open antes; usuario ve browser abrir; texto era redundante |

---

*"Boot que conta a propria historia eh ruido. Boot que aquieta e entrega eh interface." — princípio UX*
