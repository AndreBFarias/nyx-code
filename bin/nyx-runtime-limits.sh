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

# GPU-FULL-OR-CPU-01 (2026-06-03): ulimit -v/-m REMOVIDOS -- eram a CAUSA RAIZ do
# "GPU OOM com VRAM livre" que a 356 e ondas anteriores nunca acharam (sempre
# testaram via run.sh, que aplicava o ulimit; testes diretos/Luna não têm ulimit).
# O CUDA UVA + pool VMM (cuMemAddressReserve) reservam um espaço de endereço
# VIRTUAL muito maior que qualquer ulimit -v razoável (dezenas/centenas de GB),
# SEM consumir RAM/VRAM física. Com ulimit -v limitado (era 16GB), o cudaMalloc
# falha com "CUDA error: out of memory" MESMO com 3.7 GiB de VRAM livre, e o
# Ollama degrada para CPU. Comprovado por teste A/B: a MESMA inferência (full GPU
# + KV f16) roda na GPU SEM ulimit e OOMa COM o `ulimit -v 16000000`. A sprint 234
# (8->16GB) tentou aliviar mas 16GB ainda é insuficiente; o limite é incompatível
# com CUDA e foi eliminado. O OOM-killer é tratado pelo oom_score_adj abaixo (a
# alavanca correta, que não interfere no espaço de endereço do CUDA).

# oom_score_adj negativo (-1000 a 0) = menos likely matar
# Sem sudo: só funciona pra processos do própria usuário, best-effort.
# Inválido em containers restritos ou kernels antigos -- silenciar erros.
echo -100 > /proc/self/oom_score_adj 2>/dev/null || true

# Log discreto pra diagnostico (apenas em DEBUG=1)
if [ "${DEBUG:-0}" = "1" ]; then
    echo "[nyx-runtime-limits] ulimit -v=$(ulimit -v) oom_score_adj=$(cat /proc/self/oom_score_adj 2>/dev/null)"
fi
