#!/usr/bin/env python3
"""Atualiza docs automaticamente com base no estado real do código.

Lê ToolRegistry, commands, services, gauntlet, ADRs e sprints.
Atualiza GUIDE.md, README.md e PORT_STATUS.md com números reais.

Uso:
    python scripts/update_docs.py          # Atualiza tudo
    python scripts/update_docs.py --check  # Só verifica, não escreve

Integração:
    - Rodar após cada sprint concluída
    - Rodar antes de commit (pre-commit hook)
    - Chamado por run.sh --gauntlet no final
"""

from __future__ import annotations

import argparse
import logging
import re
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [update-docs] %(levelname)s: %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("nyx.update_docs")


def _count_tools() -> int:
    """Conta tools registradas no ToolRegistry."""
    try:
        from nyx.agent.tools.registry import ToolRegistry

        reg = ToolRegistry(str(PROJECT_ROOT))
        return reg.tool_count
    except Exception as e:
        logger.warning("Falha ao contar tools: %s", e)
        return 0


def _count_commands() -> int:
    """Conta commands registrados."""
    try:
        from nyx.agent.commands import list_commands

        return len(list_commands())
    except Exception as e:
        logger.warning("Falha ao contar commands: %s", e)
        return 0


def _count_services() -> int:
    """Conta services em nyx/agent/services/."""
    services_dir = PROJECT_ROOT / "nyx" / "agent" / "services"
    if not services_dir.exists():
        return 0
    return sum(1 for f in services_dir.glob("*.py") if f.stem != "__init__")


def _count_gauntlet_tests() -> int:
    """Conta testes no Gauntlet (self._add calls)."""
    gauntlet = PROJECT_ROOT / "scripts" / "gauntlet" / "nyx_gauntlet.py"
    if not gauntlet.exists():
        return 0
    content = gauntlet.read_text(encoding="utf-8")
    return len(re.findall(r"self\._add\(", content))


def _count_adrs() -> int:
    """Conta ADRs."""
    adrs_dir = PROJECT_ROOT / "dev-journey" / "03-decisions"
    if not adrs_dir.exists():
        return 0
    return sum(1 for f in adrs_dir.glob("ADR_*.md"))


def _count_sprints() -> dict[str, int]:
    """Conta sprints por status."""
    base = PROJECT_ROOT / "dev-journey" / "06-sprints"
    return {
        "producao": sum(1 for f in (base / "producao").glob("SPRINT_*.md")) if (base / "producao").exists() else 0,
        "concluidos": sum(1 for f in (base / "concluidos").glob("SPRINT_*.md"))
        if (base / "concluidos").exists()
        else 0,
        "backlog": sum(1 for f in (base / "backlog").glob("SPRINT_*.md")) if (base / "backlog").exists() else 0,
    }


def _get_next_sprint() -> str:
    """Identifica a próxima sprint pendente lendo o SPRINT_ORDER_MASTER."""
    master = PROJECT_ROOT / "dev-journey" / "06-sprints" / "SPRINT_ORDER_MASTER.md"
    if not master.exists():
        return "Desconhecida"

    content = master.read_text(encoding="utf-8")
    producao = PROJECT_ROOT / "dev-journey" / "06-sprints" / "producao"

    for line in content.split("\n"):
        match = re.search(r"\*\*([A-Z0-9-]+)\*\*", line)
        if match and "PENDENTE" in line:
            sprint_id = match.group(1)
            for f in producao.glob("SPRINT_*.md"):
                if sprint_id.replace("-", "") in f.stem.upper().replace("_", "").replace("-", ""):
                    return f.stem
            return sprint_id

    return "Todas concluídas"


def _update_section(content: str, marker_start: str, marker_end: str, new_content: str) -> str:
    """Atualiza seção entre marcadores."""
    pattern = re.compile(
        re.escape(marker_start) + r".*?" + re.escape(marker_end),
        re.DOTALL,
    )
    replacement = marker_start + "\n" + new_content + "\n" + marker_end
    if pattern.search(content):
        return pattern.sub(replacement, content)
    return content


def update_guide_md(
    tools: int, commands: int, services: int, tests: int, adrs: int, sprints: dict[str, int], check: bool
) -> bool:
    """Atualiza GUIDE.md com números reais."""
    path = PROJECT_ROOT / "GUIDE.md"
    if not path.exists():
        return False

    content = path.read_text(encoding="utf-8")
    original = content

    new_table = (
        f"| Componente | Atual | Meta (100%) |\n"
        f"|-----------|-------|-------------|\n"
        f"| Tools | {tools} | 46+ |\n"
        f"| Commands | {commands} | 98+ |\n"
        f"| Services | {services} | 35+ |\n"
        f"| Testes | {tests} | 259+ |\n"
        f"| ADRs | {adrs} | -- |"
    )

    old_table_pattern = re.compile(
        r"\| Componente \| Atual \| Meta.*?\| ADRs \| \d+ \| -- \|",
        re.DOTALL,
    )
    if old_table_pattern.search(content):
        content = old_table_pattern.sub(new_table, content)

    sprint_line = f"Sprints pendentes em `producao/`: {sprints['producao']}\nSprints concluídas em `concluidos/`: {sprints['concluidos']}"
    old_sprint_pattern = re.compile(
        r"Sprints pendentes em `producao/`: \d+\nSprints concluídas em `concluidos/`: \d+",
    )
    if old_sprint_pattern.search(content):
        content = old_sprint_pattern.sub(sprint_line, content)

    changed = content != original
    if changed and not check:
        path.write_text(content, encoding="utf-8")
        logger.info("GUIDE.md atualizado")
    elif changed:
        logger.info("GUIDE.md precisa de atualização")

    return changed


def update_readme(tools: int, commands: int, services: int, tests: int, check: bool) -> bool:
    """Atualiza README.md com números reais."""
    path = PROJECT_ROOT / "README.md"
    if not path.exists():
        return False

    content = path.read_text(encoding="utf-8")
    original = content

    replacements = [
        (
            r"Roda qwen3:4b via Ollama com \d+ tools, \d+ commands, \d+ services",
            f"Roda qwen3:4b via Ollama com {tools} tools, {commands} commands, {services} services",
        ),
        (r"Tools \| 40 \| \d+ \| \d+%", f"Tools | 40 | {tools} | {tools * 100 // 40}%"),
        (r"Commands \| 98 \| \d+ \| \d+%", f"Commands | 98 | {commands} | {commands * 100 // 98}%"),
        (r"Services \| 35 \| \d+ \| \d+%", f"Services | 35 | {services} | {services * 100 // 35}%"),
        (r"\d+ tools registradas", f"{tools} tools registradas"),
        (r"\d+ slash commands", f"{commands} slash commands"),
        (r"\d+ testes", f"{tests} testes"),
    ]

    for pattern, replacement in replacements:
        content = re.sub(pattern, replacement, content)

    changed = content != original
    if changed and not check:
        path.write_text(content, encoding="utf-8")
        logger.info("README.md atualizado")
    elif changed:
        logger.info("README.md precisa de atualização")

    return changed


def update_port_status(tools: int, commands: int, services: int, check: bool) -> bool:
    """Atualiza PORT_STATUS.md com cobertura real."""
    path = PROJECT_ROOT / "dev-journey" / "PORT_STATUS.md"
    if not path.exists():
        return False

    content = path.read_text(encoding="utf-8")
    original = content

    replacements = [
        (
            r"\| Tools \| 40 \| \d+ \| \d+ \| \d+% \|",
            f"| Tools | 40 | {tools} | {40 - min(tools, 40)} | {min(tools, 40) * 100 // 40}% |",
        ),
        (
            r"\| Commands \| 98 \| \d+ \| \d+ \| \d+% \|",
            f"| Commands | 98 | {commands} | {98 - min(commands, 98)} | {min(commands, 98) * 100 // 98}% |",
        ),
        (
            r"\| Services \| 35 \| \d+ \| \d+ \| \d+% \|",
            f"| Services | 35 | {services} | {35 - min(services, 35)} | {min(services, 35) * 100 // 35}% |",
        ),
        (
            r"\| \*\*TOTAL\*\* \| \*\*173\*\* \| \*\*\d+\*\* \| \*\*\d+\*\* \| \*\*\d+%\*\* \|",
            f"| **TOTAL** | **173** | **{tools + commands + services}** | **{173 - (tools + commands + services)}** | **{(tools + commands + services) * 100 // 173}%** |",
        ),
    ]

    for pattern, replacement in replacements:
        content = re.sub(pattern, replacement, content)

    changed = content != original
    if changed and not check:
        path.write_text(content, encoding="utf-8")
        logger.info("PORT_STATUS.md atualizado")
    elif changed:
        logger.info("PORT_STATUS.md precisa de atualização")

    return changed


def main() -> None:
    parser = argparse.ArgumentParser(description="Atualiza docs com estado real do código")
    parser.add_argument("--check", action="store_true", help="Só verifica, não escreve")
    args = parser.parse_args()

    tools = _count_tools()
    commands = _count_commands()
    services = _count_services()
    tests = _count_gauntlet_tests()
    adrs = _count_adrs()
    sprints = _count_sprints()
    next_sprint = _get_next_sprint()

    print()
    print("=" * 50)
    print("  Estado real do código")
    print("=" * 50)
    print(f"  Tools:     {tools}")
    print(f"  Commands:  {commands}")
    print(f"  Services:  {services}")
    print(f"  Testes:    {tests}")
    print(f"  ADRs:      {adrs}")
    print(
        f"  Sprints:   {sprints['concluidos']} concluídas | {sprints['producao']} pendentes | {sprints['backlog']} backlog"
    )
    print(f"  Próxima:   {next_sprint}")
    print()

    changes = []
    if update_guide_md(tools, commands, services, tests, adrs, sprints, args.check):
        changes.append("GUIDE.md")
    if update_readme(tools, commands, services, tests, args.check):
        changes.append("README.md")
    if update_port_status(tools, commands, services, args.check):
        changes.append("PORT_STATUS.md")

    if changes:
        action = "precisam de atualização" if args.check else "atualizados"
        print(f"  Docs {action}: {', '.join(changes)}")
    else:
        print("  Docs já estão atualizados.")
    print()

    if args.check and changes:
        sys.exit(1)


if __name__ == "__main__":
    main()


# "Automatizar o trivial libera para o importante." -- Larry Wall
