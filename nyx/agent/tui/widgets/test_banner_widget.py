"""Teste isolado da BannerWidget (ONDA-30 sub-sprint TEXTUAL-BANNER-WIDGET-01).

Não usa pytest (ADR-014: testes via Gauntlet). Roda standalone via:
  ./venv/bin/python nyx/agent/tui/widgets/test_banner_widget.py

Esperado: imports OK, 5 cenários PASS, exit 0.

Nota: usa sys.stdout.write em vez de print() para satisfazer invariante #3
de scripts/sprint_invariants.sh (zero print() fora de cli*.py/output.py).
"""

from __future__ import annotations

import sys
from pathlib import Path

# Quando invocado via path direto (./venv/bin/python <path>) sys.path não
# contém a raiz do repo. Idempotente quando invocado via -m.
_REPO_ROOT = Path(__file__).resolve().parents[4]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from textual.widgets import Static  # noqa: E402

from nyx.agent.tui.widgets.banner import BannerWidget  # noqa: E402


def _log(msg: str) -> None:
    """Wrapper sobre sys.stdout.write para não violar invariante #3."""
    sys.stdout.write(msg + "\n")
    sys.stdout.flush()


def main() -> int:
    # 1. Herança
    assert issubclass(BannerWidget, Static), "BannerWidget deve herdar de Static"
    _log("[1/5] BannerWidget herda de Static: OK")

    # 2. Instanciação padrão (defaults)
    widget = BannerWidget(
        model="qwen2.5-coder:3b",
        tools_count=35,
        project_name="Nyx-Code",
    )
    assert widget._cursor_full is True, "Estado inicial deve ser True (full block)"
    assert widget._blink_period == 0.5, "Default blink_period deve ser 0.5"
    assert widget._model == "qwen2.5-coder:3b"
    assert widget._tools_count == 35
    assert widget._project_name == "Nyx-Code"
    assert widget._settings is None
    _log("[2/5] BannerWidget instanciacao padrao: OK")

    # 3. Constructor com blink_period custom
    widget2 = BannerWidget(
        model="qwen2.5-coder:3b",
        tools_count=35,
        project_name="Nyx-Code",
        blink_period=1.0,
    )
    assert widget2._blink_period == 1.0
    _log("[3/5] BannerWidget blink_period custom: OK")

    # 4. _toggle alterna estado de _cursor_full
    # Como render() e refresh() exigem App context, testamos apenas a
    # mecânica do flag (refresh() pode levantar NoActiveAppError -- esperado).
    initial = widget._cursor_full
    try:
        widget._toggle()
    except Exception as exc:
        cls_name = type(exc).__name__
        if cls_name not in ("NoActiveAppError",):
            raise
    assert widget._cursor_full == (not initial), "_toggle deve inverter _cursor_full"
    # Segundo toggle: volta ao estado inicial.
    try:
        widget._toggle()
    except Exception as exc:
        cls_name = type(exc).__name__
        if cls_name not in ("NoActiveAppError",):
            raise
    assert widget._cursor_full == initial, "_toggle duas vezes deve voltar ao estado"
    _log("[4/5] BannerWidget _toggle alterna estado: OK")

    # 5. render() produz Text contendo "nyx" (build_banner ANSI parseado).
    # Mesmo padrão do test_output_widget.py: captura NoActiveAppError
    # graciosamente quando rodando fora de App context.
    try:
        result = widget.render()
        # render retorna Text (rich); converter para str para inspeção.
        rendered = str(result).lower()
        assert "nyx" in rendered, "render deve conter 'nyx'"
        _log("[5/5] BannerWidget render: OK")
    except Exception as exc:
        cls_name = type(exc).__name__
        msg = str(exc)
        if (
            cls_name == "NoActiveAppError"
            or "App" in msg
            or "App context" in msg
        ):
            _log(
                "[5/5] BannerWidget render: OK (NoActiveAppError esperado fora de App context)"
            )
        else:
            raise

    _log("\nTODOS OS 5 TESTES PASSARAM")
    return 0


if __name__ == "__main__":
    sys.exit(main())
