#!/bin/bash
# test-clean-boot.sh -- valida portabilidade do Nyx-Code em container limpo.
#
# Requer: Docker + NVIDIA Container Toolkit no host (para --gpus all).
# Tempo estimado: 5-15 min (build + install Ollama + modelos baixados no container).
#
# Fluxo:
#   1. Build da imagem nyx-clean-boot:test a partir do Dockerfile.clean-boot
#   2. Roda ./install.sh --no-prompt dentro do container
#   3. Roda ./run.sh --gauntlet --only coverage dentro do container
#
# Use: ./docker/test-clean-boot.sh

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$PROJECT_ROOT"

IMAGE="nyx-clean-boot:test"

log() { echo "[test-clean-boot] $1"; }
fail() { echo "[test-clean-boot] FAIL: $1" >&2; exit 1; }

command -v docker >/dev/null 2>&1 || fail "docker nao encontrado no PATH"

log "1/3 Build da imagem $IMAGE"
docker build -t "$IMAGE" -f docker/Dockerfile.clean-boot . || fail "docker build falhou"

GPU_FLAG=""
if docker run --rm --gpus all "$IMAGE" -c "command -v nvidia-smi >/dev/null" 2>/dev/null; then
    GPU_FLAG="--gpus all"
    log "NVIDIA Container Toolkit detectado; rodando com GPU"
else
    log "Sem GPU no container (CPU-only); auto-tune deve calcular num_gpu=0"
fi

log "2/3 Rodando install.sh --no-prompt no container"
docker run --rm $GPU_FLAG "$IMAGE" -c "./install.sh --no-prompt" \
    || fail "install.sh falhou no container"

log "3/3 Rodando Gauntlet coverage no container"
docker run --rm $GPU_FLAG "$IMAGE" -c "./run.sh --gauntlet --only coverage" \
    || fail "gauntlet coverage falhou no container"

log "OK -- portabilidade validada em container limpo"


# "A prova do pudim esta em come-lo." -- proverbio ingles
