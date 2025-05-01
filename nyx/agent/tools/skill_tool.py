"""Tool: Skill -- Invoca skills locais definidos em ~/.nyx/skills/."""

from __future__ import annotations

import importlib.util
import logging
from pathlib import Path
from typing import Any

from nyx.agent.models import ActionResult, ActionType
from nyx.agent.tools.base import RegisteredTool, ToolDef

logger = logging.getLogger("nyx.tools.skill")

SKILLS_DIR = Path.home() / ".nyx" / "skills"


def _list_skills() -> list[tuple[str, str]]:
    """Lista skills disponíveis: (nome, descrição)."""
    if not SKILLS_DIR.exists():
        return []
    skills = []
    for f in sorted(SKILLS_DIR.glob("*.py")):
        if f.name.startswith("_"):
            continue
        name = f.stem
        desc = ""
        try:
            first_lines = f.read_text(encoding="utf-8").split("\n")[:5]
            for line in first_lines:
                if line.strip().startswith('"""') or line.strip().startswith("'''"):
                    desc = line.strip().strip("\"'").strip()
                    break
        except Exception:
            pass
        skills.append((name, desc or name))
    return skills


class SkillTool(RegisteredTool):
    action_type = ActionType.RUN_COMMAND

    tool_def = ToolDef(
        name="skill",
        description=(
            "Invoca um skill local definido em ~/.nyx/skills/. "
            "Cada skill é um módulo Python com função execute(args, project_root)."
        ),
        parameters={
            "skill_name": {"type": "string", "description": "Nome do skill (sem .py)"},
            "args": {"type": "string", "description": "Argumentos para o skill (opcional)"},
        },
        required=["skill_name"],
    )

    def execute(self, params: dict[str, Any], project_root: str) -> ActionResult:
        skill_name = str(params.get("skill_name", "")).strip()
        args = str(params.get("args", "")).strip()

        if not skill_name:
            skills = _list_skills()
            if not skills:
                return ActionResult(success=True, output="Nenhum skill disponível em ~/.nyx/skills/")
            lines = ["Skills disponíveis:"]
            for name, desc in skills:
                lines.append(f"  - {name}: {desc}")
            return ActionResult(success=True, output="\n".join(lines))

        skill_path = SKILLS_DIR / f"{skill_name}.py"
        if not skill_path.exists():
            available = _list_skills()
            names = [n for n, _ in available]
            return ActionResult(
                success=False,
                error=f"Skill '{skill_name}' não encontrado. Disponíveis: {', '.join(names) or 'nenhum'}",
            )

        try:
            spec = importlib.util.spec_from_file_location(skill_name, skill_path)
            if spec is None or spec.loader is None:
                return ActionResult(success=False, error=f"Falha ao carregar skill: {skill_name}")
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)

            if not hasattr(module, "execute"):
                return ActionResult(
                    success=False,
                    error=f"Skill '{skill_name}' não tem função execute()",
                )

            result = module.execute(args, project_root)
            return ActionResult(success=True, output=str(result))

        except Exception as e:
            logger.warning("Erro ao executar skill %s: %s", skill_name, e)
            return ActionResult(success=False, error=f"Erro no skill '{skill_name}': {e}")


# "Habilidade é conhecimento aplicado." -- Aristóteles
