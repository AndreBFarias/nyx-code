# SPRINT TUI-SHUTDOWN-SILENT-01 — Disown + setsid para silenciar "Morto" do bash

## 0. SPEC (machine-readable)

```yaml
sprint:
  id: TUI-SHUTDOWN-SILENT-01
  title: "disown nos & + setsid no cleanup para suprimir 'Morto' do bash"
  onda: 23
  bloco: 23.1 Estabilização
  prioridade: BAIXA
  tipo: Bugfix+UX
  dependencias: []
  desbloqueia: [COCKPIT-01]

  touches:
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/run.sh
      reason: "Aplica disown em PIDs background e setsid no cleanup"
      linhas_alvo: "184-186, 309-312, 371-377"

  creates: []
  removes: []

  forbidden:
    - "Usar 'set +bm' global (afeta set -uo pipefail)"
    - "Fechar stderr globalmente com 2>&- (perde diagnóstico)"
    - "Trap SIGCHLD silencioso (mascara real death)"

  tests:
    - cmd: "./run.sh --smoke 2>&1 | grep -ci 'morto'"
      timeout: 60
      deve_passar: true
      nota: "Deve retornar 0 (sem ocorrências)"
    - cmd: "./run.sh --smoke && ./run.sh --smoke"
      timeout: 120
      deve_passar: true
      nota: "Boots consecutivos sem leak"
    - cmd: "bash scripts/sprint_invariants.sh"
      timeout: 60
      deve_passar: "FAIL_AFTER <= FAIL_BEFORE"

  acceptance_criteria:
    - "disown aplicado nos 3 background & (linhas ~184 Ollama, ~309 cleanup, ~372 proxy)"
    - "setsid usado para isolar árvore de processos do shell pai"
    - "Stdout do ./run.sh --smoke não contém 'Morto' nem 'Killed'"
    - "Cleanup ainda mata Ollama e proxy corretamente em SIGTERM"
    - "Boot consecutivo (2x ./run.sh) não acumula órfãos"
    - "Acentuação PT-BR correta"
```

---

**Status:** PENDENTE
**Data criação:** 2026-05-15
**Modelo obrigatório:** claude-opus-4-7 (sem subagentes)

---

# Sprint TUI-SHUTDOWN-SILENT-01

## Contexto

"Morto" no terminal não vem dos `kill 2>/dev/null` (já redirecionam). Vem do bash reportando filho `&` morto por SIGKILL externo (OOM-killer). `disown` remove o PID da jobs table; quando ele morre, o bash não reporta.

## Solução

Aplicar nas linhas indicadas:

```bash
"$OLLAMA_BIN" serve >> "$SCRIPT_DIR/logs/ollama.log" 2>&1 &
OLLAMA_PID=$!
disown $OLLAMA_PID 2>/dev/null || true
```

E o mesmo para o proxy. `kill $PID` continua funcional para PIDs disowned (cleanup permanece intacto).

`setsid` opcionalmente isola toda a árvore — útil para cleanup limpo. Pode ser aplicado wrapeando o launch:

```bash
setsid -f "$OLLAMA_BIN" serve >> "$SCRIPT_DIR/logs/ollama.log" 2>&1
```

Avaliar trade-off: `setsid -f` faz fork — perde-se acesso direto ao PID. Para o cleanup atual, manter só `disown` é mais seguro.

## Verificação

```bash
./run.sh --smoke 2>&1 | tee /tmp/smoke.out
grep -ci 'morto\|killed' /tmp/smoke.out  # deve ser 0
```

## Gambiarras proibidas

- `set +bm` (afeta o resto do script).
- `2>&-` global (perde diagnóstico).
- Ignorar OOM-killer real silenciosamente (a sprint BOOT-VRAM-GUARD-01 já corrige a causa raiz; esta sprint só evita o ruído visual).

---

*"Silêncio bem feito é um modo de respeito." -- anônimo*
