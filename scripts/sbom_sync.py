#!/usr/bin/env python3
"""SBOM-REGISTRY-02: regenera FEATURE_MAP.md a partir de REGISTRY.yaml.

REGISTRY.yaml é a fonte única; FEATURE_MAP.md é renderização para humanos.
sync também atualiza status/timestamp/evidência de features testadas via
input json opcional `--from-gauntlet <path>`.

Uso:
    python scripts/sbom_sync.py                              # regen FEATURE_MAP
    python scripts/sbom_sync.py --from-gauntlet checkpoint.json  # update + regen
    python scripts/sbom_sync.py --check                      # valida sem escrever
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent
REGISTRY = REPO_ROOT / "dev-journey" / "04-features" / "REGISTRY.yaml"
FEATURE_MAP = REPO_ROOT / "dev-journey" / "04-features" / "FEATURE_MAP.md"


def load_registry() -> dict:
    if not REGISTRY.is_file():
        raise FileNotFoundError("REGISTRY.yaml ausente — rode sbom_init.py primeiro")
    return yaml.safe_load(REGISTRY.read_text(encoding="utf-8"))


def save_registry(data: dict) -> None:
    REGISTRY.write_text(
        yaml.safe_dump(data, sort_keys=False, allow_unicode=True, default_flow_style=False),
        encoding="utf-8",
    )


def update_from_gauntlet(data: dict, gauntlet_path: Path) -> int:
    """Lê checkpoint.json do gauntlet e atualiza features matching."""
    try:
        ckpt = json.loads(gauntlet_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        print(f"[erro] checkpoint inválido: {exc}", file=sys.stderr)
        return 0
    results = ckpt.get("results", [])
    by_id = {f["id"]: f for f in data.get("features", [])}
    iso_now = datetime.now(timezone.utc).isoformat(timespec="seconds")
    touched = 0
    for r in results:
        fid = r.get("feature_id") or r.get("id")
        if not fid or fid not in by_id:
            continue
        feat = by_id[fid]
        feat["status"] = "verde" if r.get("passed") else "vermelho"
        feat["ultimo_teste"] = iso_now
        feat["evidencia"] = (r.get("details") or r.get("error") or "")[:200]
        kpi = r.get("elapsed_s")
        if kpi:
            feat["kpi"] = f"elapsed_s={kpi}"
        touched += 1
    return touched


CATEGORIA_HEADER_TPL = "## {n}. {nome}\n"
TABLE_HEADER_DEFAULT = "| ID | Feature | Componente | Validação |\n|----|---------|------------|-----------|\n"
TABLE_HEADER_KPI = "| ID | Métrica | Unidade | Baseline |\n|----|---------|---------|----------|\n"


def render_feature_map(data: dict) -> str:
    """Regenera FEATURE_MAP.md a partir de REGISTRY.yaml."""
    features = data.get("features", [])
    # Agrupa por categoria, preservando ordem de aparição
    cats: dict[str, list[dict]] = {}
    cat_order: list[str] = []
    for f in features:
        c = f.get("categoria", "Outros")
        if c not in cats:
            cats[c] = []
            cat_order.append(c)
        cats[c].append(f)

    lines: list[str] = [
        "# Mapeamento Completo de Features -- Nyx-Code",
        "",
        "> **Gerado por `scripts/sbom_sync.py` a partir de REGISTRY.yaml.**",
        "> Não edite este arquivo manualmente; edite REGISTRY.yaml e rode `sbom_sync.py`.",
        "",
    ]
    for n, cat in enumerate(cat_order, start=1):
        lines.append(CATEGORIA_HEADER_TPL.format(n=n, nome=cat))
        is_kpi = "Performance" in cat or "KPI" in cat
        lines.append(TABLE_HEADER_KPI if is_kpi else TABLE_HEADER_DEFAULT)
        for f in cats[cat]:
            fid = f.get("id", "?")
            desc = f.get("descricao", "")
            comp = f.get("componente", "")
            val = f.get("validacao", "")
            status = f.get("status", "desconhecido")
            status_tag = {
                "verde": "[ok]",
                "vermelho": "[x]",
                "amarelo": "[!]",
                "desconhecido": "[?]",
            }.get(status, "[?]")
            lines.append(f"| {fid} | {status_tag} {desc} | {comp} | {val} |")
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


SPRINT_STUB_TEMPLATE = """# SPRINT FEAT-{fid}-TEST-01 — Cobrir feature {fid} com teste no Gauntlet

## 0. SPEC

```yaml
sprint:
  id: FEAT-{fid}-TEST-01
  title: "Cobrir feature {fid} ({descricao}) com teste no Gauntlet"
  onda: 23
  bloco: 23.2 SBOM (auto-proposto)
  prioridade: BAIXA
  tipo: Test
  dependencias: [SBOM-REGISTRY-03]
  desbloqueia: []
  origem: "Auto-proposto por sbom_sync.py --propose-sprints; status era 'desconhecido' em REGISTRY.yaml."

  acceptance_criteria:
    - "Feature {fid} ganha entry de teste no Gauntlet"
    - "REGISTRY.yaml passa a ter status verde ou vermelho (não desconhecido) para {fid}"
    - "Validação: '{validacao}'"
```

---

**Status:** RASCUNHO
**Data criação:** 2026-05-17
**Origem:** sbom_sync.py --propose-sprints
**Modelo obrigatório:** claude-opus-4-7 (sem subagentes)
"""


def propose_sprints(data: dict, dry_run: bool = True) -> tuple[int, list[str]]:
    """Lista features com status 'desconhecido' e propõe sprint stubs."""
    candidates = [
        f for f in data.get("features", [])
        if (f.get("status") or "desconhecido") == "desconhecido"
    ]
    targets: list[str] = []
    producao = REPO_ROOT / "dev-journey" / "06-sprints" / "producao"
    for f in candidates:
        fid = f["id"]
        target = producao / f"SPRINT_FEAT_{fid.replace('-', '_')}_TEST_01.md"
        if target.exists():
            continue
        targets.append(str(target))
        if not dry_run:
            target.write_text(
                SPRINT_STUB_TEMPLATE.format(
                    fid=fid,
                    descricao=f.get("descricao", ""),
                    validacao=f.get("validacao", ""),
                ),
                encoding="utf-8",
            )
    return len(targets), targets


def main() -> int:
    parser = argparse.ArgumentParser(description="Regenera FEATURE_MAP.md de REGISTRY.yaml")
    parser.add_argument("--from-gauntlet", metavar="JSON", help="Atualiza REGISTRY com checkpoint do gauntlet")
    parser.add_argument("--check", action="store_true", help="Apenas valida, não escreve")
    parser.add_argument(
        "--propose-sprints",
        action="store_true",
        help="Cria specs RASCUNHO em producao/ para features 'desconhecido' (SBOM-REGISTRY-03)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Combina com --propose-sprints: lista candidatos sem escrever",
    )
    args = parser.parse_args()

    if args.propose_sprints:
        data = load_registry()
        n, _ = propose_sprints(data, dry_run=args.dry_run)
        if args.dry_run:
            print(f"[dry-run] {n} sprint stub(s) proposta(s) (não escritas)")
        else:
            print(f"[ok] {n} sprint stub(s) criadas em producao/")
        return 0

    data = load_registry()
    if args.from_gauntlet:
        path = Path(args.from_gauntlet)
        touched = update_from_gauntlet(data, path)
        print(f"[update] {touched} feature(s) atualizadas pelo gauntlet")
        if not args.check:
            save_registry(data)

    rendered = render_feature_map(data)
    if args.check:
        existing = FEATURE_MAP.read_text(encoding="utf-8") if FEATURE_MAP.is_file() else ""
        if existing.strip() != rendered.strip():
            print("[diff] FEATURE_MAP.md está dessincronizado de REGISTRY.yaml")
            return 1
        print("[ok] FEATURE_MAP.md sincronizado com REGISTRY.yaml")
        return 0

    FEATURE_MAP.write_text(rendered, encoding="utf-8")
    print(f"[ok] FEATURE_MAP.md regenerado com {len(data.get('features', []))} features")
    return 0


if __name__ == "__main__":
    sys.exit(main())
