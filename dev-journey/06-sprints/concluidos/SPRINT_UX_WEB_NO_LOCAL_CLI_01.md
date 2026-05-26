# SPRINT 239 — UX-WEB-NO-LOCAL-CLI-01

## 0. SPEC (machine-readable)

```yaml
sprint:
  id: UX-WEB-NO-LOCAL-CLI-01
  title: "--web nao deve subir CLI local (PTY conflict resolvido)"
  onda: 31
  prioridade: ALTA
  tipo: Bugfix
  dependencias: [UX-BOOT-SILENT-SPINNER-01]
  desbloqueia: []

  touches:
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/run.sh
      reason: "Em --web/--cockpit, exec cli.py local ao final do script duplica PTY que ja esta servido via /repl WS do cockpit"
  creates: []
  removes: []

  forbidden:
    - "Quebrar modo default (sem --web) que continua subindo cli.py"
    - "Quebrar --gauntlet ou --headless ou --smoke"
    - "Mexer no cockpit/server.py (PTY bridge esta correto)"
    - "Adicionar emoji"
    - "Mencao a IA proprietaria em codigo/commit"   # noqa-anonimato

  tests:
    - cmd: "./run.sh --smoke"
      timeout: 10
      deve_passar: true
    - cmd: "bash scripts/sprint_invariants.sh"
      timeout: 30
      deve_passar: true

  acceptance_criteria:
    - "Em --web/--cockpit: cli.py NAO executa localmente"
    - "Em --web: script bloqueia em wait com trap cleanup pra Ctrl+C"
    - "Em --web: Chrome consegue conectar /repl WS sem 'outra sessao PTY ativa'"
    - "Em modo default (sem --web): comportamento preservado byte-a-byte (cli.py local)"
    - "Smoke + invariantes preservados"
```

---

# Sprint 239 — UX-WEB-NO-LOCAL-CLI-01

**Status:** PENDENTE
**Data criação:** 2026-05-25
**Modelo obrigatório:** claude-opus-4-7 (sem subagentes)

---

## Contexto

Usuário rodou `./run.sh --web` e reportou empíricamente:
- Chrome abriu no cockpit `http://127.0.0.1:11437/`
- Mas exibe `[cockpit] outra sessao PTY ativa. Aguarde ela fechar` + `WebSocket fechado`
- Em paralelo, kitty mostra CLI Nyx local funcionando (banner, input, toolbar)

Causa-raiz arquitetural: `run.sh:759 "$SCRIPT_DIR/venv/bin/python" "$SCRIPT_DIR/nyx/cli.py"` é chamada em TODOS os modos, incluindo `--web`. O CLI local consome o PTY que o cockpit pretende servir via `/repl` WebSocket. Sprints COCKPIT-02/03 fizeram PTY exclusivo (uma sessao por vez) — bom para evitar race, ruim quando dois consumidores tentam.

Em `--web`, o design correto é:
- Cockpit web SERVE a CLI via PTY bridge (/static/terminal.html + xterm.js)
- run.sh local NAO sobe CLI; apenas espera e gerencia lifecycle (Ctrl+C limpa tudo)

## Solução

### 1. Detectar modo --web e pular cli.py local

Em `run.sh` antes do `exec cli.py` (~linha 759), branch:

```bash
if [ "$COCKPIT_BG" -eq 1 ]; then
    log_boot "Modo --web: CLI servido via cockpit WS em /repl. Aguardando shutdown..."
    # Bloqueia o script ate Ctrl+C/SIGTERM, mantendo lifecycle.
    # cleanup() ja mata cockpit + proxy + ollama.
    while true; do sleep 60; done
else
    "$SCRIPT_DIR/venv/bin/python" "$SCRIPT_DIR/nyx/cli.py"
    EXIT_CODE=$?
    exit "$EXIT_CODE"
fi
```

### 2. Mensagem no terminal indicando modo

Substituir `stop_boot_spinner` no caminho --web por mensagem clara em vez de abrir TUI:

```bash
stop_boot_spinner
if [ "$COCKPIT_BG" -eq 1 ]; then
    echo ""
    log_nyx "Cockpit pronto em http://127.0.0.1:11437/"
    log_nyx "Pressione Ctrl+C para encerrar."
    echo ""
fi
```

### 3. Cleanup do `wait` infinito

`cleanup()` ja roda em trap EXIT/SIGINT/SIGTERM/SIGHUP. O sleep 60 dentro do while NAO bloqueia traps (bash interrompe sleep em SIGINT). Ctrl+C dispara cleanup → mata ollama + proxy + cockpit + sai.

## Riscos

| Risco | Mitigação |
|---|---|
| User espera CLI local + browser (paradigma anterior implícito) | Mensagem clara "Cockpit pronto em http://... Pressione Ctrl+C para encerrar" |
| Chrome NAO abre automaticamente (xdg-open falha) | Imprimir URL no terminal mesmo (log_nyx) para fallback manual |
| Spinner ja parou antes do `while sleep 60` | OK, stop_boot_spinner termina pre wait |
| --gauntlet ou --headless tem COCKPIT_BG=0 | Branch nao afeta esses modos |

## Aritmetica esperada

~15 linhas liquidas em run.sh.

## Proof-of-work

```bash
./run.sh --smoke   # boot ok exit 0
bash scripts/sprint_invariants.sh   # PASS=14/14 FAIL=0

# Validação interativa do --web:
./run.sh --web &
sleep 12
curl -sf http://127.0.0.1:11437/health  # {"status":"ok"}
# Chrome aberto deve mostrar terminal WS conectado (sem 'outra sessao PTY')
# Ctrl+C no terminal: tudo morre limpo (cockpit + proxy + ollama)
```

---

*"Dois consumidores do mesmo PTY = race condition disfarcada de feature." -- principio*
