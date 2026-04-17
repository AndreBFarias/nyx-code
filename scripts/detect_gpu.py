#!/usr/bin/env python3
"""Detecta GPU NVIDIA disponível e calcula num_gpu ideal por modelo.

Uso:
    python scripts/detect_gpu.py --dry-run
        Imprime JSON com diagnóstico completo, não escreve em disco.

    python scripts/detect_gpu.py --write-env
        Escreve NYX_NUM_GPU no .env se NYX_AUTO_TUNE=1 (ou ausente).
        Respeita NYX_AUTO_TUNE=0 e não sobrescreve.

    python scripts/detect_gpu.py --for-model qwen3:4b
        Imprime apenas o inteiro num_gpu calculado para o modelo dado.
        Usado pelo run.sh para exportar NYX_NUM_GPU em tempo de boot.

Estratégia:
    - Lê VRAM livre via nvidia-smi (se ausente -> num_gpu=0, fallback CPU)
    - Reserva RESERVED_MB para contexto + buffers internos do Ollama
    - num_gpu = min(total_layers, floor((vram_free_mb - RESERVED_MB) / mb_per_layer))
    - Clamp em [0, total_layers]

Logs em logs/gpu_tune.log.
"""

from __future__ import annotations

import argparse
import json
import logging
import re
import shutil
import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
LOG_DIR = PROJECT_ROOT / "logs"
LOG_DIR.mkdir(exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [gpu_tune] %(levelname)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[
        logging.FileHandler(LOG_DIR / "gpu_tune.log"),
        logging.StreamHandler(sys.stderr),
    ],
)
logger = logging.getLogger("nyx.gpu_tune")


RESERVED_MB = 1024

MODEL_TABLE: dict[str, dict[str, int]] = {
    "qwen3:4b": {"total_layers": 40, "mb_per_layer": 115},
    "qwen2.5-coder:3b": {"total_layers": 36, "mb_per_layer": 85},
    "qwen2.5-coder:7b": {"total_layers": 28, "mb_per_layer": 230},
}

DEFAULT_MODEL = "qwen3:4b"


def detect_gpu() -> dict[str, object]:
    """Retorna dict com gpu_name, vram_total_mb, vram_free_mb, has_gpu."""
    info: dict[str, object] = {
        "has_gpu": False,
        "gpu_name": None,
        "vram_total_mb": 0,
        "vram_free_mb": 0,
        "error": None,
    }

    if shutil.which("nvidia-smi") is None:
        info["error"] = "nvidia-smi não encontrado no PATH"
        return info

    try:
        proc = subprocess.run(
            [
                "nvidia-smi",
                "--query-gpu=name,memory.total,memory.free",
                "--format=csv,noheader,nounits",
            ],
            capture_output=True,
            text=True,
            timeout=10,
        )
    except subprocess.TimeoutExpired:
        info["error"] = "nvidia-smi timeout (>10s)"
        return info
    except OSError as exc:
        info["error"] = f"nvidia-smi falhou: {exc}"
        return info

    if proc.returncode != 0:
        info["error"] = f"nvidia-smi exit {proc.returncode}: {proc.stderr.strip()}"
        return info

    first_line = proc.stdout.strip().splitlines()[0] if proc.stdout.strip() else ""
    parts = [p.strip() for p in first_line.split(",")]
    if len(parts) < 3:
        info["error"] = f"saída inesperada: {first_line!r}"
        return info

    try:
        info["gpu_name"] = parts[0]
        info["vram_total_mb"] = int(re.sub(r"\D", "", parts[1]) or 0)
        info["vram_free_mb"] = int(re.sub(r"\D", "", parts[2]) or 0)
        info["has_gpu"] = info["vram_total_mb"] > 0
    except ValueError as exc:
        info["error"] = f"parse falhou: {exc}"
    return info


def calc_num_gpu(model: str, vram_free_mb: int) -> int:
    entry = MODEL_TABLE.get(model)
    if entry is None:
        for known in MODEL_TABLE:
            if known.split(":")[0] in model:
                entry = MODEL_TABLE[known]
                break
    if entry is None:
        entry = MODEL_TABLE[DEFAULT_MODEL]

    usable = vram_free_mb - RESERVED_MB
    if usable <= 0:
        return 0

    layers = usable // entry["mb_per_layer"]
    return max(0, min(entry["total_layers"], int(layers)))


def build_report(gpu: dict[str, object]) -> dict[str, object]:
    vram_free = int(gpu.get("vram_free_mb") or 0)
    per_model = {m: calc_num_gpu(m, vram_free) for m in MODEL_TABLE}
    return {
        "has_gpu": gpu["has_gpu"],
        "gpu_name": gpu["gpu_name"],
        "vram_total_mb": gpu["vram_total_mb"],
        "vram_free_mb": gpu["vram_free_mb"],
        "reserved_mb": RESERVED_MB,
        "num_gpu_per_model": per_model,
        "error": gpu["error"],
    }


def read_env(env_path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    if not env_path.exists():
        return values
    for raw in env_path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, _, v = line.partition("=")
        values[k.strip()] = v.strip()
    return values


def write_env_var(env_path: Path, key: str, value: str) -> None:
    lines: list[str] = []
    if env_path.exists():
        lines = env_path.read_text(encoding="utf-8").splitlines()

    pattern = re.compile(rf"^\s*#?\s*{re.escape(key)}\s*=")
    replaced = False
    for idx, raw in enumerate(lines):
        if pattern.match(raw):
            lines[idx] = f"{key}={value}"
            replaced = True
            break

    if not replaced:
        if lines and lines[-1] != "":
            lines.append("")
        lines.append(f"{key}={value}")

    env_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def auto_tune_enabled(env_vars: dict[str, str]) -> bool:
    raw = env_vars.get("NYX_AUTO_TUNE", "1").strip().strip('"').strip("'")
    return raw not in {"0", "false", "False", "no", "off", ""}


def cmd_dry_run(model_filter: str | None) -> int:
    gpu = detect_gpu()
    report = build_report(gpu)
    if model_filter:
        report["selected_model"] = model_filter
        report["selected_num_gpu"] = calc_num_gpu(model_filter, int(gpu.get("vram_free_mb") or 0))
    print(json.dumps(report, indent=2, ensure_ascii=False))
    logger.info(
        "dry-run: gpu=%s vram_free=%sMB per_model=%s",
        gpu.get("gpu_name"),
        gpu.get("vram_free_mb"),
        report["num_gpu_per_model"],
    )
    return 0


def cmd_write_env(env_path: Path, model: str) -> int:
    env_vars = read_env(env_path)
    if not auto_tune_enabled(env_vars):
        logger.info("NYX_AUTO_TUNE=0: preservando .env existente (não escrevo)")
        return 0

    gpu = detect_gpu()
    num_gpu = calc_num_gpu(model, int(gpu.get("vram_free_mb") or 0))
    write_env_var(env_path, "NYX_NUM_GPU", str(num_gpu))
    logger.info(
        "write-env: modelo=%s num_gpu=%s gpu=%s vram_free=%sMB -> %s",
        model,
        num_gpu,
        gpu.get("gpu_name"),
        gpu.get("vram_free_mb"),
        env_path,
    )
    if gpu.get("error"):
        logger.warning("detalhe GPU: %s", gpu["error"])
    return 0


def cmd_for_model(model: str) -> int:
    gpu = detect_gpu()
    num_gpu = calc_num_gpu(model, int(gpu.get("vram_free_mb") or 0))
    logger.info(
        "for-model %s: num_gpu=%s (vram_free=%sMB, gpu=%s)",
        model,
        num_gpu,
        gpu.get("vram_free_mb"),
        gpu.get("gpu_name"),
    )
    print(num_gpu)
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Auto-tune de num_gpu por modelo")
    parser.add_argument("--dry-run", action="store_true", help="imprime JSON sem escrever")
    parser.add_argument("--write-env", action="store_true", help="escreve NYX_NUM_GPU no .env")
    parser.add_argument("--for-model", metavar="MODEL", help="imprime apenas num_gpu para o modelo")
    parser.add_argument("--env-path", default=str(PROJECT_ROOT / ".env"), help="caminho do .env")
    parser.add_argument("--model", default=DEFAULT_MODEL, help="modelo para --write-env")
    args = parser.parse_args()

    actions = [args.dry_run, args.write_env, bool(args.for_model)]
    if sum(1 for a in actions if a) != 1:
        parser.error("escolha exatamente um: --dry-run, --write-env, --for-model MODEL")

    if args.dry_run:
        return cmd_dry_run(args.for_model)
    if args.for_model:
        return cmd_for_model(args.for_model)
    return cmd_write_env(Path(args.env_path), args.model)


if __name__ == "__main__":
    sys.exit(main())


# "Conhece-te a ti mesmo." -- Sócrates
