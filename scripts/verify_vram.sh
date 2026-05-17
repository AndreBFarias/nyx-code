#!/usr/bin/env bash
# VISION-03: confere que chamada de VisionService.describe NÃO descarrega
# o modelo de chat (qwen2.5-coder:3b) da VRAM. Pula gracefully se
# nvidia-smi ausente (CPU-only ou ambiente CI sem GPU).

set -u

if ! command -v nvidia-smi &>/dev/null; then
    echo "[skip] nvidia-smi não encontrado — teste pulado (ambiente sem GPU)"
    exit 0
fi

mem_used() {
    nvidia-smi --query-gpu=memory.used --format=csv,noheader,nounits | head -1
}

BEFORE=$(mem_used)
echo "[verify_vram] VRAM antes:  ${BEFORE} MB"

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT" || exit 2

if [ -x ./venv/bin/python ]; then
    PYBIN="./venv/bin/python"
else
    PYBIN="python3"
fi

"$PYBIN" - <<'PY'
from pathlib import Path
import sys
from nyx.agent.services.vision_service import VisionService
from nyx.providers.vision_client import VisionClient

# Tenta porta padrão Nyx (11435) e fallback Ollama do sistema (11434).
for url in ("http://127.0.0.1:11435", "http://127.0.0.1:11434"):
    svc = VisionService(client=VisionClient(ollama_url=url))
    if svc.is_available():
        break
else:
    print("[skip] moondream não instalado em nenhum Ollama acessível")
    sys.exit(0)

p = Path("assets/nyx-icon.png")
if not p.is_file():
    print("[skip] assets/nyx-icon.png ausente")
    sys.exit(0)

desc = svc.describe(p)
print(f"[vision] descrição OK ({len(desc)} chars)")
PY

PY_RC=$?
if [ $PY_RC -ne 0 ]; then
    echo "[FAIL] inferência vision retornou $PY_RC"
    exit $PY_RC
fi

AFTER=$(mem_used)
echo "[verify_vram] VRAM depois: ${AFTER} MB"

DELTA=$((AFTER - BEFORE))
ABS_DELTA=${DELTA#-}
if [ $ABS_DELTA -gt 200 ]; then
    echo "[FAIL] VRAM variou ${DELTA} MB (esperado <= 200 MB)"
    exit 1
fi
echo "[OK] VRAM estável (delta ${DELTA} MB) — qwen permanece quente"
