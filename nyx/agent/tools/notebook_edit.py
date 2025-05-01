"""NotebookEdit -- Edita células de Jupyter notebooks (.ipynb).

Suporta: replace, insert, delete de células.
Notebooks são JSON -- manipulação direta sem dependências.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

from nyx.agent.models import ActionResult, ActionType
from nyx.agent.tools.base import RegisteredTool, ToolDef

logger = logging.getLogger("nyx.tools.notebook")


class NotebookEditTool(RegisteredTool):
    action_type = ActionType.EDIT_FILE

    tool_def = ToolDef(
        name="notebook_edit",
        description=(
            "Edita células de um Jupyter notebook (.ipynb). "
            "Modos: replace (substitui célula), insert (insere após célula), "
            "delete (remove célula). Identifica células pelo índice (0-based)."
        ),
        parameters={
            "notebook_path": {"type": "string", "description": "Caminho do arquivo .ipynb"},
            "cell_index": {
                "type": "integer",
                "description": "Índice da célula (0-based). Para insert, insere após este índice.",
            },
            "new_source": {"type": "string", "description": "Novo conteúdo da célula"},
            "cell_type": {
                "type": "string",
                "enum": ["code", "markdown"],
                "description": "Tipo da célula (padrão: code)",
            },
            "edit_mode": {
                "type": "string",
                "enum": ["replace", "insert", "delete"],
                "description": "Modo de edição (padrão: replace)",
            },
        },
        required=["notebook_path", "cell_index"],
    )

    def execute(self, params: dict[str, Any], project_root: str) -> ActionResult:
        nb_path = str(params.get("notebook_path", "")).strip()
        if not nb_path:
            return ActionResult(success=False, error="Caminho do notebook vazio")

        full_path = Path(project_root) / nb_path if not Path(nb_path).is_absolute() else Path(nb_path)
        if not full_path.exists():
            return ActionResult(success=False, error=f"Notebook não encontrado: {nb_path}")
        if full_path.suffix != ".ipynb":
            return ActionResult(success=False, error=f"Não é um notebook: {nb_path}")

        cell_index = int(params.get("cell_index", 0))
        new_source = str(params.get("new_source", ""))
        cell_type = str(params.get("cell_type", "code"))
        edit_mode = str(params.get("edit_mode", "replace"))

        try:
            nb = json.loads(full_path.read_text(encoding="utf-8"))
        except Exception as e:
            return ActionResult(success=False, error=f"Erro ao ler notebook: {e}")

        cells = nb.get("cells", [])
        total = len(cells)

        if edit_mode == "delete":
            if cell_index < 0 or cell_index >= total:
                return ActionResult(success=False, error=f"Índice {cell_index} fora do range (0-{total - 1})")
            removed = cells.pop(cell_index)
            removed_type = removed.get("cell_type", "?")
            nb["cells"] = cells
            _write_notebook(full_path, nb)
            return ActionResult(
                success=True,
                output=f"Célula {cell_index} ({removed_type}) removida. Total: {len(cells)}",
                files_modified=[str(full_path)],
            )

        if edit_mode == "insert":
            new_cell = _make_cell(new_source, cell_type)
            insert_at = min(cell_index + 1, total)
            cells.insert(insert_at, new_cell)
            nb["cells"] = cells
            _write_notebook(full_path, nb)
            return ActionResult(
                success=True,
                output=f"Célula {cell_type} inserida na posição {insert_at}. Total: {len(cells)}",
                files_modified=[str(full_path)],
            )

        if cell_index < 0 or cell_index >= total:
            return ActionResult(success=False, error=f"Índice {cell_index} fora do range (0-{total - 1})")

        source_lines = new_source.split("\n")
        cells[cell_index]["source"] = [line + "\n" for line in source_lines[:-1]] + [source_lines[-1]]
        if cell_type:
            cells[cell_index]["cell_type"] = cell_type

        nb["cells"] = cells
        _write_notebook(full_path, nb)

        return ActionResult(
            success=True,
            output=f"Célula {cell_index} ({cell_type}) atualizada. {len(source_lines)} linhas.",
            files_modified=[str(full_path)],
        )


def _make_cell(source: str, cell_type: str = "code") -> dict:
    """Cria célula .ipynb no formato padrão."""
    source_lines = source.split("\n")
    formatted = [line + "\n" for line in source_lines[:-1]] + [source_lines[-1]]

    cell: dict[str, Any] = {
        "cell_type": cell_type,
        "metadata": {},
        "source": formatted,
    }
    if cell_type == "code":
        cell["execution_count"] = None
        cell["outputs"] = []

    return cell


def _write_notebook(path: Path, nb: dict) -> None:
    """Salva notebook mantendo formato compatível."""
    path.write_text(
        json.dumps(nb, indent=1, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


# "O notebook é o laboratório do cientista de dados." -- Fernando Pérez
