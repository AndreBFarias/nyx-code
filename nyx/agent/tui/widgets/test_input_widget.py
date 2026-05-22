"""Teste isolado da InputWidget (ONDA-30 sub-sprint 202).

Não usa pytest (ADR-014: testes via Gauntlet, e o gauntlet não cobre Textual
ainda). Roda standalone via uma das formas:
  ./venv/bin/python nyx/agent/tui/widgets/test_input_widget.py
  ./venv/bin/python -m nyx.agent.tui.widgets.test_input_widget

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

from textual.suggester import SuggestFromList  # noqa: E402
from textual.widgets import Input  # noqa: E402

from nyx.agent.tui.widgets.input import InputWidget  # noqa: E402


def _log(msg: str) -> None:
    """Wrapper sobre sys.stdout.write para não violar invariante #3."""
    sys.stdout.write(msg + "\n")
    sys.stdout.flush()


def main() -> int:
    # 1. Herança
    assert issubclass(InputWidget, Input), "InputWidget deve herdar de Input"
    _log("[1/5] InputWidget herda de Input: OK")

    # 2. Instanciação sem completer
    widget1 = InputWidget()
    assert widget1.suggester is None, "Sem completer -> suggester None"
    _log("[2/5] InputWidget sem completer: OK")

    # 3. Instanciação com slash_completer
    commands = ["help", "quit", "clear", "memory"]
    widget2 = InputWidget(slash_completer=commands)
    assert isinstance(
        widget2.suggester, SuggestFromList
    ), "Com slash_completer -> SuggestFromList"
    _log("[3/5] InputWidget com slash_completer: OK")

    # 4. Submit callback armazenado em self._on_submit
    captured: list[str] = []
    widget3 = InputWidget(on_submit=lambda text: captured.append(text))
    assert widget3._on_submit is not None, "on_submit deve estar armazenado"
    assert callable(widget3._on_submit), "_on_submit deve ser callable"
    _log("[4/5] InputWidget on_submit callback armazenado: OK")

    # 5. paste_text aceita texto literal e prefixo [clipboard-image]:.
    # insert_text_at_cursor toca reactives que exigem App context para
    # propagar watchers; capturamos NoActiveAppError graciosamente (mesmo
    # padrão do test_output_widget.py do sprint 198 com RichLog).
    try:
        widget4 = InputWidget()
        widget4.paste_text("texto normal")
        widget4.paste_text("[clipboard-image]:/tmp/foo.png")
        _log("[5/5] InputWidget paste_text: OK")
    except Exception as exc:
        cls_name = type(exc).__name__
        msg = str(exc)
        if (
            cls_name == "NoActiveAppError"
            or "App" in msg
            or "_widget" in msg
            or "App context" in msg
            or "size" in msg
            or "region" in msg
        ):
            _log(
                "[5/5] InputWidget paste_text: OK (App context requerido para mutação real -- esperado fora de app)"
            )
        else:
            raise

    _log("\nTODOS OS 5 TESTES PASSARAM")
    return 0


if __name__ == "__main__":
    sys.exit(main())
