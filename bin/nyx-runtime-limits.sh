#!/usr/bin/env bash
# Limites de runtime do Nyx-Code (INFRA-OOM-01).
# Sourced por run.sh no início. Aplica:
#   - ulimit -v 8000000  (8GB virtual memory por processo)
#   - ulimit -m 8000000  (8GB physical memory)
#   - oom_score_adj -100 (menos likely OOM-kill; best-effort sem sudo)
#
# Sintoma que motivou: máquina com swap 80% antes do boot;
# Ollama + Nyx + Cockpit em sessão longa pode disparar OOM-killer
# (dmesg "Out of memory: Killed process N (ollama)") com cold start
# subsequente de 20+s por reload.
#
# ADR-001 Local First: roda em userspace, sem alterar config global do kernel.

# 8GB virt mem (qwen2.5-coder:3b consome ~2-3GB; folga p/ cockpit + buffers)
ulimit -v 8000000 2>/dev/null || true

# Memoria fisica preferida (kernel ignora em alguns sistemas, ok)
ulimit -m 8000000 2>/dev/null || true

# oom_score_adj negativo (-1000 a 0) = menos likely matar
# Sem sudo: só funciona pra processos do própria usuário, best-effort.
# Inválido em containers restritos ou kernels antigos -- silenciar erros.
echo -100 > /proc/self/oom_score_adj 2>/dev/null || true

# Log discreto pra diagnostico (apenas em DEBUG=1)
if [ "${DEBUG:-0}" = "1" ]; then
    echo "[nyx-runtime-limits] ulimit -v=$(ulimit -v) oom_score_adj=$(cat /proc/self/oom_score_adj 2>/dev/null)"
fi
