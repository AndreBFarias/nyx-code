#!/usr/bin/env bash
# Diagnóstico de OOM (INFRA-OOM-01).
# Reporta:
#   - memória + swap atuais
#   - lista de OOM events do kernel (última hora)
#   - top 10 processos por memória
#   - oom_score dos processos Nyx/Ollama
#
# Uso: bash scripts/check_oom.sh
# Útil em validate sessions ou após apagão de processo.

set -u  # falha em vars não definidas (-e omitido para não abortar em find sem hits)

PRIMARY='\033[38;2;0;212;170m'
MUTED='\033[38;2;160;168;181m'
RED='\033[38;2;255;107;107m'
NC='\033[0m'

echo -e "${PRIMARY}=== nyx-check-oom ===${NC}"
date -Iseconds

echo
echo -e "${PRIMARY}== Memória ==${NC}"
free -h

echo
echo -e "${PRIMARY}== Swap ==${NC}"
swapon --show 2>/dev/null || echo "(nenhum swap configurado)"

echo
echo -e "${PRIMARY}== OOM kernel (última hora) ==${NC}"
if command -v journalctl >/dev/null 2>&1; then
    journalctl --since='1 hour ago' -k 2>/dev/null \
        | grep -iE 'out of memory|oom-killer|killed process' \
        | tail -20 \
        || echo -e "${MUTED}(nenhum OOM no journalctl)${NC}"
else
    dmesg 2>/dev/null | grep -iE 'out of memory|oom-killer|killed process' | tail -20 \
        || echo -e "${MUTED}(nenhum OOM no dmesg)${NC}"
fi

echo
echo -e "${PRIMARY}== Top 10 processos por RAM ==${NC}"
ps aux --sort=-%mem | head -11

echo
echo -e "${PRIMARY}== Nyx / Ollama oom_score ==${NC}"
for pat in 'nyx/cli\|nyx.cli' 'nyx.cockpit' 'ollama serve' 'ollama runner'; do
    pids=$(pgrep -f "$pat" 2>/dev/null | head -3)
    for pid in $pids; do
        if [ -r "/proc/$pid/oom_score" ]; then
            score=$(cat "/proc/$pid/oom_score" 2>/dev/null || echo "?")
            cmd=$(tr '\0' ' ' < "/proc/$pid/cmdline" 2>/dev/null | cut -c1-60)
            echo -e "  pid=${pid} score=${score} ${MUTED}${cmd}${NC}"
        fi
    done
done

echo
echo -e "${MUTED}Hint: oom_score baixo (< 100) = menos likely OOM-kill.${NC}"
echo -e "${MUTED}Cap configurado em bin/nyx-runtime-limits.sh: ulimit -v 8GB + oom_score_adj -100.${NC}"
