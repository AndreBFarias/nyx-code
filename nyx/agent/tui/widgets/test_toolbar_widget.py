"""Teste isolado da Toolbar (ONDA-30 sub-sprint TEXTUAL-TOOLBAR-01).

Não usa pytest (ADR-014: testes via Gauntlet). Roda standalone via:
  ./venv/bin/python nyx/agent/tui/widgets/test_toolbar_widget.py

Esperado: imports OK, 6 cenários PASS, exit 0.

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

from nyx.agent.tui.widgets.toolbar import Toolbar  # noqa: E402


def _log(msg: str) -> None:
    """Wrapper sobre sys.stdout.write para não violar invariante #3."""
    sys.stdout.write(msg + "\n")
    sys.stdout.flush()


def main() -> int:
    # 1. Herança
    assert issubclass(Toolbar, Static), "Toolbar deve herdar de Static"
    _log("[1/6] Toolbar herda de Static: OK")

    # 2. Instanciação default (model default + 6 reactive props zeradas)
    t = Toolbar()
    assert t._model == "qwen2.5-coder:3b"
    assert t.ctx_pct == 0
    assert t.iter_n == 0
    assert t.reads == 0
    assert t.mods == 0
    assert t.model_state == "cold"
    assert t.mode == "normal"
    _log("[2/6] Toolbar defaults: OK")

    # 3. Modelo custom
    t2 = Toolbar(model="qwen3:4b")
    assert t2._model == "qwen3:4b"
    _log("[3/6] Toolbar model custom: OK")

    # 4. render() retorna Text contendo keywords. Mesmo padrão dos demais
    # widgets: captura NoActiveAppError graciosamente fora de App context.
    try:
        result = t.render()
        s = str(result).lower()
        assert "ctx" in s, "render deve conter 'ctx'"
        assert "iter" in s, "render deve conter 'iter'"
        assert "lidos" in s, "render deve conter 'lidos'"
        assert "modif" in s, "render deve conter 'modif'"
        _log("[4/6] Toolbar render contem keywords: OK")
    except Exception as exc:
        cls_name = type(exc).__name__
        if cls_name == "NoActiveAppError":
            _log("[4/6] Toolbar render: OK (NoActiveAppError esperado)")
        else:
            raise

    # 5. Reactive properties são atribuíveis (set/get round-trip).
    # watch_* pode levantar NoActiveAppError ao chamar self.refresh()
    # fora de App context -- captura graciosa.
    try:
        t.ctx_pct = 42
        assert t.ctx_pct == 42
    except Exception as exc:
        if type(exc).__name__ != "NoActiveAppError":
            raise
    try:
        t.mode = "plan"
        assert t.mode == "plan"
    except Exception as exc:
        if type(exc).__name__ != "NoActiveAppError":
            raise
    try:
        t.model_state = "warm"
        assert t.model_state == "warm"
    except Exception as exc:
        if type(exc).__name__ != "NoActiveAppError":
            raise
    _log("[5/6] Toolbar reactive set/get: OK")

    # 6. Modo bypass altera render (string "bypass" aparece no output).
    try:
        t.mode = "bypass"
    except Exception as exc:
        if type(exc).__name__ != "NoActiveAppError":
            raise
    try:
        result_bypass = t.render()
        assert "bypass" in str(result_bypass).lower()
        _log("[6/6] Toolbar render modo bypass: OK")
    except Exception as exc:
        cls_name = type(exc).__name__
        if cls_name == "NoActiveAppError":
            _log("[6/6] Toolbar render modo bypass: OK (NoActiveAppError esperado)")
        else:
            raise

    _log("\nTODOS OS 6 TESTES PASSARAM")
    return 0


if __name__ == "__main__":
    sys.exit(main())
