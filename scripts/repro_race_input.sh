#!/usr/bin/env bash
# Reproduz race de input-readiness no REPL da Nyx.
# Envia stdin imediatamente após start e verifica se o texto foi consumido.
#
# Estratégia: marca única com timestamp (evita falso-positivo se o banner
# já contiver substrings como "oi"). Grep procura a marca no log bruto.
# Saída: [ok] input chegou OU [bug] input perdido — ambas válidas (diagnóstico).
#
# Refs: UX-BUG-02A, ADR-010 (zero mocks: REPL real), ADR-020 (testes via run.sh).
set -eu

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

LOG=/tmp/nyx_repro_$(date +%s).log
MARK="oi-pre-banner-$(date +%s)-$$"

(
  sleep 0.1
  printf '%s\n/quit\n' "$MARK"
) | ./run.sh 2>&1 | tee "$LOG" || true

if grep -q "$MARK" "$LOG"; then
  echo "[ok] input chegou (marca: $MARK)"
  exit 0
else
  echo "[bug] input perdido (marca: $MARK)"
  echo "Log completo: $LOG"
  exit 1
fi
