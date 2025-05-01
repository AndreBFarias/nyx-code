"""Git Operations -- Operações git para o Nyx Agent.

Port de Luna src/skills/code_agent/git_ops.py.
Wrappers seguros sobre subprocess para git. Nunca lançam exceção.
"""

from __future__ import annotations

import logging
import subprocess
from pathlib import Path

logger = logging.getLogger("nyx.git_ops")

GIT_TIMEOUT = 15


def _run_git(args: list[str], cwd: str | Path) -> tuple[bool, str]:
    try:
        result = subprocess.run(
            ["git", *args],
            capture_output=True, text=True,
            timeout=GIT_TIMEOUT, cwd=str(cwd),
        )
        output = result.stdout.strip()
        if result.returncode != 0:
            return False, result.stderr.strip() or output
        return True, output
    except FileNotFoundError:
        return False, "git não encontrado no sistema"
    except subprocess.TimeoutExpired:
        return False, f"git timeout ({GIT_TIMEOUT}s)"
    except Exception as e:
        logger.error("Erro git: %s", e)
        return False, str(e)


run_git = _run_git


def is_git_repo(project_root: str | Path) -> bool:
    ok, _ = _run_git(["rev-parse", "--is-inside-work-tree"], project_root)
    return ok


def git_status(project_root: str | Path) -> tuple[bool, str]:
    return _run_git(["status", "--short"], project_root)


def git_diff(project_root: str | Path, staged: bool = False) -> tuple[bool, str]:
    args = ["diff", "--stat"]
    if staged:
        args.append("--staged")
    return _run_git(args, project_root)


def git_diff_file(project_root: str | Path, file_path: str) -> tuple[bool, str]:
    return _run_git(["diff", "--", file_path], project_root)


def git_diff_full(project_root: str | Path, file_path: str = "") -> tuple[bool, str]:
    args = ["diff"]
    if file_path:
        args.extend(["--", file_path])
    return _run_git(args, project_root)


def git_add_files(project_root: str | Path, files: list[str]) -> tuple[bool, str]:
    if not files:
        return False, "Nenhum arquivo para adicionar"
    return _run_git(["add", "--", *files], project_root)


def git_commit(project_root: str | Path, message: str) -> tuple[bool, str]:
    if not message.strip():
        return False, "Mensagem de commit vazia"
    return _run_git(["commit", "-m", message], project_root)


def git_add_and_commit(project_root: str | Path, files: list[str], message: str) -> tuple[bool, str]:
    ok, output = git_add_files(project_root, files)
    if not ok:
        return False, f"Falha no git add: {output}"
    return git_commit(project_root, message)


def git_log(project_root: str | Path, count: int = 20, oneline: bool = True) -> tuple[bool, str]:
    args = ["log", f"-{count}"]
    if oneline:
        args.append("--oneline")
    return _run_git(args, project_root)


def git_current_branch(project_root: str | Path) -> tuple[bool, str]:
    return _run_git(["rev-parse", "--abbrev-ref", "HEAD"], project_root)


def git_diff_summary(project_root: str | Path) -> str:
    ok, output = git_diff(project_root)
    return output if ok else ""


# "Quem controla o histórico controla o futuro." -- George Orwell
