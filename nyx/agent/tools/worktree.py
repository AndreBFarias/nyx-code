"""Tools: Worktree -- Git worktree create/cleanup."""

from __future__ import annotations

import subprocess
import tempfile
import time
from pathlib import Path
from typing import Any

from nyx.agent.models import ActionResult, ActionType
from nyx.agent.services.logging_service import get_logger
from nyx.agent.tools.base import RegisteredTool, ToolDef

logger = get_logger("nyx.tools.worktree")

_active_worktree: dict[str, str] = {}


class EnterWorktreeTool(RegisteredTool):
    action_type = ActionType.RUN_COMMAND

    tool_def = ToolDef(
        name="enter_worktree",
        description=("Cria um git worktree isolado para trabalhar em mudanças sem afetar a árvore principal."),
        parameters={
            "branch_name": {
                "type": "string",
                "description": "Nome da branch (opcional, gera automaticamente)",
            },
        },
        required=[],
    )

    def execute(self, params: dict[str, Any], project_root: str) -> ActionResult:
        if _active_worktree.get("path"):
            return ActionResult(
                success=False,
                error=f"Worktree já ativo: {_active_worktree['path']}. Use exit_worktree primeiro.",
            )

        ts = str(int(time.time()))
        branch = str(params.get("branch_name", "")).strip()
        if not branch:
            branch = f"nyx-worktree-{ts}"

        wt_dir = Path(tempfile.gettempdir()) / f"nyx-wt-{ts}"

        try:
            subprocess.run(
                ["git", "worktree", "add", str(wt_dir), "-b", branch],
                cwd=project_root,
                capture_output=True,
                text=True,
                timeout=30,
                check=True,
            )
        except subprocess.CalledProcessError as e:
            return ActionResult(
                success=False,
                error=f"Falha ao criar worktree: {e.stderr.strip()}",
            )
        except FileNotFoundError:
            return ActionResult(success=False, error="Git não encontrado")

        _active_worktree["path"] = str(wt_dir)
        _active_worktree["branch"] = branch
        _active_worktree["original"] = project_root

        logger.info("Worktree criado: %s (branch: %s)", wt_dir, branch)
        return ActionResult(
            success=True,
            output=f"Worktree criado: {wt_dir}\nBranch: {branch}",
        )


class ExitWorktreeTool(RegisteredTool):
    action_type = ActionType.RUN_COMMAND

    tool_def = ToolDef(
        name="exit_worktree",
        description=("Remove o git worktree ativo e limpa a branch temporária. Se houver mudanças, retorna o diff."),
        parameters={},
        required=[],
    )

    def execute(self, params: dict[str, Any], project_root: str) -> ActionResult:
        wt_path = _active_worktree.get("path")
        branch = _active_worktree.get("branch", "")
        original = _active_worktree.get("original", project_root)

        if not wt_path:
            return ActionResult(success=False, error="Nenhum worktree ativo")

        diff_output = ""
        try:
            diff = subprocess.run(
                ["git", "diff", "--stat"],
                cwd=wt_path,
                capture_output=True,
                text=True,
                timeout=10,
            )
            diff_output = diff.stdout.strip()
        except Exception as e:
            logger.debug("Falha ao obter diff do worktree: %s", e)

        try:
            subprocess.run(
                ["git", "worktree", "remove", wt_path, "--force"],
                cwd=original,
                capture_output=True,
                text=True,
                timeout=30,
            )
        except Exception as e:
            logger.warning("Falha ao remover worktree: %s", e)

        if branch and not diff_output:
            try:
                subprocess.run(
                    ["git", "branch", "-d", branch],
                    cwd=original,
                    capture_output=True,
                    text=True,
                    timeout=10,
                )
            except Exception as e:
                logger.debug("Falha ao deletar branch do worktree: %s", e)

        _active_worktree.clear()

        result = f"Worktree removido: {wt_path}"
        if diff_output:
            result += f"\nMudanças pendentes (branch {branch} mantida):\n{diff_output}"
        else:
            result += f"\nBranch {branch} removida (sem mudanças)"

        logger.info("Worktree removido: %s", wt_path)
        return ActionResult(success=True, output=result)


# "Isolar para proteger." -- princípio de engenharia
