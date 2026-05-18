"""Captura de evidência PNG por feature (COCKPIT-04).

Salva blobs PNG enviados pelo frontend (xterm canvas.toBlob) em
dev-journey/07-reports/evidencia/<feature_id>/<ts>.png com rotação
de 5 arquivos por feature. Atualiza REGISTRY.yaml com path da última.
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Optional

from nyx.agent.services.logging_service import get_logger

logger = get_logger("nyx.cockpit.evidencia")

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
EVIDENCIA_DIR = REPO_ROOT / "dev-journey" / "07-reports" / "evidencia"
REGISTRY_PATH = REPO_ROOT / "dev-journey" / "04-features" / "REGISTRY.yaml"
MAX_KEEP = 5
MAX_PNG_BYTES = 1 * 1024 * 1024  # 1 MB hard cap (forbidden de COCKPIT-04)


def save_evidence(feature_id: str, png_bytes: bytes) -> dict[str, object]:
    """Salva PNG, rotaciona até 5, atualiza REGISTRY. Retorna meta."""
    if len(png_bytes) > MAX_PNG_BYTES:
        raise ValueError(
            f"PNG demasiado grande ({len(png_bytes)} bytes; max {MAX_PNG_BYTES})"
        )
    if not feature_id or "/" in feature_id or ".." in feature_id:
        raise ValueError(f"feature_id inválido: {feature_id!r}")

    dest_dir = EVIDENCIA_DIR / feature_id
    dest_dir.mkdir(parents=True, exist_ok=True)
    ts = datetime.utcnow().strftime("%Y%m%dT%H%M%S")
    dest = dest_dir / f"{ts}.png"
    dest.write_bytes(png_bytes)
    logger.info("evidencia salva: %s (%d bytes)", dest, len(png_bytes))

    _rotate(dest_dir, MAX_KEEP)

    rel = dest.relative_to(REPO_ROOT)
    _update_registry_evidence(feature_id, str(rel))

    return {
        "path": str(rel),
        "size_bytes": len(png_bytes),
    }


def _rotate(dest_dir: Path, keep: int) -> None:
    pngs = sorted(dest_dir.glob("*.png"), key=lambda p: p.stat().st_mtime)
    excess = len(pngs) - keep
    for old in pngs[:excess]:
        try:
            old.unlink()
            logger.debug("rotate: removido %s", old)
        except OSError as exc:
            logger.warning("rotate: falha ao remover %s: %s", old, exc)


def _update_registry_evidence(feature_id: str, rel_path: str) -> None:
    """Atualiza REGISTRY.yaml feature[id].evidencia_path."""
    try:
        import yaml
    except ImportError:
        logger.warning("pyyaml ausente; pulando atualizacao de REGISTRY")
        return
    if not REGISTRY_PATH.is_file():
        logger.warning("REGISTRY.yaml ausente; pulando")
        return
    try:
        data = yaml.safe_load(REGISTRY_PATH.read_text(encoding="utf-8")) or {}
    except yaml.YAMLError as exc:
        logger.warning("REGISTRY.yaml malformado: %s", exc)
        return
    feats = data.get("features", [])
    changed = False
    for f in feats:
        if f.get("id") == feature_id:
            f["evidencia_path"] = rel_path
            changed = True
            break
    if not changed:
        logger.warning("feature %s não encontrada em REGISTRY", feature_id)
        return
    try:
        REGISTRY_PATH.write_text(
            yaml.safe_dump(data, sort_keys=False, allow_unicode=True),
            encoding="utf-8",
        )
        logger.info("REGISTRY atualizado: %s.evidencia_path=%s", feature_id, rel_path)
    except OSError as exc:
        logger.warning("Falha ao gravar REGISTRY: %s", exc)


def latest_evidence(feature_id: Optional[str] = None) -> dict[str, object]:
    """Retorna lista das evidências (por feature ou todas)."""
    if feature_id:
        d = EVIDENCIA_DIR / feature_id
        if not d.is_dir():
            return {"feature_id": feature_id, "evidencias": []}
        pngs = sorted(d.glob("*.png"), key=lambda p: p.stat().st_mtime, reverse=True)
        return {
            "feature_id": feature_id,
            "evidencias": [
                {"path": str(p.relative_to(REPO_ROOT)), "size_bytes": p.stat().st_size}
                for p in pngs
            ],
        }
    if not EVIDENCIA_DIR.is_dir():
        return {"total": 0, "por_feature": {}}
    result = {}
    for d in sorted(EVIDENCIA_DIR.iterdir()):
        if d.is_dir():
            pngs = list(d.glob("*.png"))
            result[d.name] = len(pngs)
    return {"total": sum(result.values()), "por_feature": result}
