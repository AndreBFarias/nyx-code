#!/usr/bin/env python3
"""SBOM-REGISTRY-01: converte FEATURE_MAP.md em REGISTRY.yaml.

Parsing das tabelas markdown (categoria por ## heading). Cada linha de tabela
vira uma entrada YAML. Idempotente: rodar 2x não duplica.

Uso:
    python scripts/sbom_init.py            # gera REGISTRY.yaml
    python scripts/sbom_init.py --check    # exit 1 se REGISTRY.yaml diverge
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent
FEATURE_MAP = REPO_ROOT / "dev-journey" / "04-features" / "FEATURE_MAP.md"
REGISTRY = REPO_ROOT / "dev-journey" / "04-features" / "REGISTRY.yaml"

CATEGORIA_RE = re.compile(r"^##\s+\d+\.\s+(?P<cat>.+?)\s*$")
TABLE_HEADER_RE = re.compile(r"^\|\s*ID\s*\|\s*(Feature|Métrica)\s*\|\s*[^|]+\|\s*[^|]+\|")
ROW_RE = re.compile(r"^\|\s*(?P<id>[A-Z][A-Z0-9\-]+)\s*\|\s*(?:\[[^\]]+\]\s*)?(?P<feat>.+?)\s*\|\s*(?P<comp>.+?)\s*\|\s*(?P<val>.+?)\s*\|\s*$")


def parse_feature_map(path: Path = FEATURE_MAP) -> list[dict[str, object]]:
    if not path.is_file():
        raise FileNotFoundError(f"FEATURE_MAP não encontrado: {path}")
    text = path.read_text(encoding="utf-8")

    features: list[dict[str, object]] = []
    categoria_atual = ""
    in_table = False
    for line in text.splitlines():
        m = CATEGORIA_RE.match(line)
        if m:
            categoria_atual = m.group("cat").strip()
            in_table = False
            continue
        if TABLE_HEADER_RE.match(line):
            in_table = True
            continue
        if not in_table:
            continue
        if line.startswith("|---") or line.startswith("| ---"):
            continue
        if not line.strip():
            # Permitir linha em branco entre header e rows do FEATURE_MAP regenerado.
            continue
        if not line.startswith("|"):
            in_table = False
            continue
        row = ROW_RE.match(line)
        if not row:
            continue
        fid = row.group("id").strip()
        feat = row.group("feat").strip()
        comp = row.group("comp").strip()
        val = row.group("val").strip()
        features.append({
            "id": fid,
            "categoria": categoria_atual,
            "descricao": feat,
            "componente": comp,
            "validacao": val,
            "status": "desconhecido",
            "ultimo_teste": "",
            "evidencia": "",
            "kpi": "",
            "sprint_origem": "",
            "tags": [],
        })
    return features


def write_registry(features: list[dict[str, object]], path: Path = REGISTRY) -> None:
    payload = {
        "schema_version": 1,
        "gerado_de": "FEATURE_MAP.md",
        "total": len(features),
        "features": features,
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        yaml.safe_dump(payload, sort_keys=False, allow_unicode=True, default_flow_style=False),
        encoding="utf-8",
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Gera REGISTRY.yaml de FEATURE_MAP.md")
    parser.add_argument("--check", action="store_true", help="Apenas verifica divergência; exit 1 se diverge")
    args = parser.parse_args()

    features = parse_feature_map()
    if args.check:
        if not REGISTRY.is_file():
            print(f"[diff] REGISTRY.yaml ausente; gere com: python {sys.argv[0]}")
            return 1
        try:
            existing = yaml.safe_load(REGISTRY.read_text(encoding="utf-8"))
        except Exception as exc:  # noqa: BLE001
            print(f"[erro] REGISTRY.yaml mal-formado: {exc}")
            return 1
        ex_features = existing.get("features", [])
        ids_map = {f["id"]: f for f in ex_features}
        ids_parsed = {f["id"] for f in features}
        missing = ids_parsed - set(ids_map)
        extra = set(ids_map) - ids_parsed
        if missing or extra:
            print(f"[diff] missing={sorted(missing)} extra={sorted(extra)}")
            return 1
        print(f"[ok] {len(features)}/{len(ex_features)} features sincronizadas")
        return 0

    write_registry(features)
    print(f"[ok] REGISTRY.yaml gerado com {len(features)} feature(s)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
