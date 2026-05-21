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


def _count_cockpit_endpoints() -> tuple[int, int]:
    """Conta endpoints HTTP (@app.get/post/...) e WebSocket no cockpit.

    Retorna (http_endpoints, ws_endpoints).
    """
    server = PROJECT_ROOT / "nyx" / "cockpit" / "server.py"
    if not server.exists():
        return (0, 0)
    src = server.read_text(encoding="utf-8")
    total = len(re.findall(r"@app\.(get|post|put|delete|patch|websocket)", src))
    ws = len(re.findall(r"@app\.websocket", src))
    return (total - ws, ws)


def _count_cli_lines() -> int:
    """Conta linhas de nyx/cli.py."""
    cli = PROJECT_ROOT / "nyx" / "cli.py"
    if not cli.exists():
        return 0
    return len(cli.read_text(encoding="utf-8").splitlines())


def _count_tool_files() -> int:
    """Conta arquivos .py em nyx/agent/tools/ (excluindo __init__)."""
    tools_dir = PROJECT_ROOT / "nyx" / "agent" / "tools"
    if not tools_dir.exists():
        return 0
    return sum(1 for f in tools_dir.glob("*.py") if f.stem != "__init__")


def _count_invariants() -> int:
    """Conta checks numerados em scripts/sprint_invariants.sh."""
    inv = PROJECT_ROOT / "scripts" / "sprint_invariants.sh"
    if not inv.exists():
        return 0
    src = inv.read_text(encoding="utf-8")
    # Pattern: linhas começando com "# N. " (descrição do check).
    return len(re.findall(r"^# \d+\. ", src, re.MULTILINE))


def _default_model() -> str:
    """Lê DEFAULT_MODEL de nyx/config/defaults.py."""
    defaults = PROJECT_ROOT / "nyx" / "config" / "defaults.py"
    if not defaults.exists():
        return "qwen2.5-coder:3b"
    src = defaults.read_text(encoding="utf-8")
    m = re.search(r'^DEFAULT_MODEL[^=]*=\s*"([^"]+)"', src, re.MULTILINE)
    return m.group(1) if m else "qwen2.5-coder:3b"


def _read_version() -> str:
    """Lê nyx/__version__.py."""
    vf = PROJECT_ROOT / "nyx" / "__version__.py"
    if not vf.exists():
        return "0.0.0"
    src = vf.read_text(encoding="utf-8")
    m = re.search(r'__version__\s*=\s*"([^"]+)"', src)
    return m.group(1) if m else "0.0.0"


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

    sprint_line = f"Sprints pendentes em `producao/`: {sprints['producao']}\nSprints concluídas em `concluidos/`: {sprints['concluidos']}"  # noqa: E501
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


def update_readme(
    tools: int,
    commands: int,
    services: int,
    tests: int,
    cockpit_http: int,
    cockpit_ws: int,
    sprints_done: int,
    check: bool,
) -> bool:
    """Atualiza README.md com números reais."""
    path = PROJECT_ROOT / "README.md"
    if not path.exists():
        return False

    content = path.read_text(encoding="utf-8")
    original = content

    replacements = [
        (
            r"Roda qwen\S+ via Ollama com \d+ tools(?: funcionais)?, \d+ commands, \d+ services",
            f"Roda qwen2.5-coder:3b via Ollama com {tools} tools, {commands} commands, {services} services",
        ),
        (r"Tools \| 40 \| \d+ \| \d+%", f"Tools | 40 | {tools} | {tools * 100 // 40}%"),
        (r"Commands \| 98 \| \d+ \| \d+%", f"Commands | 98 | {commands} | {commands * 100 // 98}%"),
        (r"Services \| 35 \| \d+ \| \d+%", f"Services | 35 | {services} | {services * 100 // 35}%"),
        (r"\d+ tools registradas", f"{tools} tools registradas"),
        (r"\d+ tools via ToolRegistry", f"{tools} tools via ToolRegistry"),
        (r"\d+ slash commands", f"{commands} slash commands"),
        # NB: ajuste de mensagem — diz "catalogados" porque self._add count >= runtime gated.
        (
            r"# \d+ testes(?: em \d+ fases)?; --only fase\|feature_id",
            f"# {tests} testes catalogados; --only fase|feature_id",
        ),
        (
            r"# \d+ services \(incl\.",
            f"# {services} services (incl.",
        ),
        (
            r"# \d+ endpoints HTTP \+ \d+ WS",
            f"# {cockpit_http} endpoints HTTP + {cockpit_ws} WS",
        ),
        (
            r"`127\.0\.0\.1:11437` com \d+ endpoints HTTP \+ \d+ WS",
            f"`127.0.0.1:11437` com {cockpit_http} endpoints HTTP + {cockpit_ws} WS",
        ),
        (
            r"\d+ sprints concluídas, \d+ em produção",
            f"{sprints_done} sprints concluídas, 1 em produção",
        ),
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
            f"| **TOTAL** | **173** | **{tools + commands + services}** | **{173 - (tools + commands + services)}** | **{(tools + commands + services) * 100 // 173}%** |",  # noqa: E501
        ),
        (
            r"## 1\. TOOLS \(40 OpenClaude -> \d+ Nyx\)",
            f"## 1. TOOLS (40 OpenClaude -> {tools} Nyx)",
        ),
        (
            r"### Portadas \(\d+\)",
            f"### Portadas ({tools})",
        ),
        (
            r"\| Commands \| `agent/commands\.py` \| Luna commands\.py \| OK \(\d+ cmds\) \|",
            f"| Commands | `agent/commands.py` | Luna commands.py | OK ({commands} cmds) |",
        ),
        (
            r"\| ToolRegistry \| `agent/tools/registry\.py` \| Luna tools/registry\.py \| OK \(\d+ tools\) \|",
            f"| ToolRegistry | `agent/tools/registry.py` | Luna tools/registry.py | OK ({tools} tools) |",
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


def update_architecture(tools: int, commands: int, services: int, check: bool) -> bool:
    """Atualiza ARCHITECTURE.md diagrama ASCII com contagens reais.

    Cuidado: preserva alinhamento das linhas verticais do diagrama
    (cada célula tem largura fixa). Substitui apenas o miolo "(N)".
    """
    path = PROJECT_ROOT / "dev-journey" / "02-architecture" / "ARCHITECTURE.md"
    if not path.exists():
        return False

    content = path.read_text(encoding="utf-8")
    original = content

    replacements = [
        (r"Commands \(\d+\)\s*\|", f"Commands ({commands})  |"),
        (r"Services \(\d+\)\s*\|", f"Services ({services})   |"),
        (r"ToolRegistry \(\d+\)\s*\|", f"ToolRegistry ({tools})  |"),
    ]

    for pattern, replacement in replacements:
        content = re.sub(pattern, replacement, content)

    changed = content != original
    if changed and not check:
        path.write_text(content, encoding="utf-8")
        logger.info("ARCHITECTURE.md atualizado")
    elif changed:
        logger.info("ARCHITECTURE.md precisa de atualização")

    return changed


def update_project_snapshot(
    tools: int,
    commands: int,
    services: int,
    tests: int,
    adrs: int,
    sprints_done: int,
    tool_files: int,
    invariants: int,
    default_model: str,
    version: str,
    check: bool,
) -> bool:
    """Atualiza dev-journey/08-templates/PROJECT_SNAPSHOT.md (contagens + LLM + versão).

    Mantém intencionalmente partes narrativas (gate v1.0 status, ondas em execução,
    histórico de sprints fechadas) — só toca células de tabela e linhas de inventário
    que são auto-deriváveis do runtime.
    """
    path = PROJECT_ROOT / "dev-journey" / "08-templates" / "PROJECT_SNAPSHOT.md"
    if not path.exists():
        return False

    content = path.read_text(encoding="utf-8")
    original = content

    replacements = [
        # Tabela "Contagens" (linhas 64-69).
        (
            r"(\| Tools no registry \(runtime\) \| )\d+( \|)",
            rf"\g<1>{tools}\g<2>",
        ),
        (
            r"(\| Commands únicos \(sem aliases\) \| )\d+( \|)",
            rf"\g<1>{commands}\g<2>",
        ),
        (
            r"(\| Services \| )\d+( \| `find nyx/agent/services)",
            rf"\g<1>{services}\g<2>",
        ),
        (
            r"(\| ADRs vigentes \| )\d+( \|)",
            rf"\g<1>{adrs}\g<2>",
        ),
        (
            r"\| Testes no Gauntlet \| \d+(?: \(\d+ fases\))? \|",
            f"| Testes no Gauntlet | {tests} (catalogados) |",
        ),
        (
            r"\| Sprints concluídas \| \d+ \|",
            f"| Sprints concluídas | {sprints_done} |",
        ),
        # Linha 29 do gate v1.0.
        (
            r"OK via update_docs\.py \(\d+ tools, \d+ commands\)",
            f"OK via update_docs.py ({tools} tools, {commands} commands)",
        ),
        # Stack (linha 39) — LLM principal.
        (
            r"(\| LLM principal \| )`[^`]+`( via Ollama \|)",
            rf"\g<1>`{default_model}`\g<2>",
        ),
        # Diretórios do código (linhas 99-101).
        (
            r"(`nyx/agent/commands/` \| )\d+ commands únicos",
            rf"\g<1>{commands} commands únicos",
        ),
        (
            r"(`nyx/agent/tools/` \| )\d+ arquivos, \d+ tools no registry",
            rf"\g<1>{tool_files} arquivos, {tools} tools no registry",
        ),
        (
            r"(`nyx/agent/services/` \| )\d+ services",
            rf"\g<1>{services} services",
        ),
        # Scripts utilitários (linha ~150) — número de invariants.
        (
            r"\| `bash scripts/sprint_invariants\.sh` \| \d+ checks binários \|",
            f"| `bash scripts/sprint_invariants.sh` | {invariants} checks binários |",
        ),
        # Versão do projeto (linha 4) — só atualiza o ponto-versão, preserva o sufixo descritivo.
        (
            r"(\*\*Versão do projeto:\*\* \*\*v)[0-9]+\.[0-9]+\.[0-9]+(?:-rc\d+)?(\s)",
            rf"\g<1>{version}\g<2>",
        ),
    ]

    for pattern, replacement in replacements:
        content = re.sub(pattern, replacement, content)

    changed = content != original
    if changed and not check:
        path.write_text(content, encoding="utf-8")
        logger.info("PROJECT_SNAPSHOT.md atualizado")
    elif changed:
        logger.info("PROJECT_SNAPSHOT.md precisa de atualização")

    return changed


def update_gambiarras(tools: int, commands: int, check: bool) -> bool:
    """Atualiza dev-journey/08-templates/GAMBIARRAS_POR_SPRINT.md.

    Mantém o exemplo do anti-pattern de contagens preguiçosas, mas com
    valores atuais. O ponto pedagógico permanece (não copiar sem verificar),
    e os números ficam coerentes com runtime real.
    """
    path = PROJECT_ROOT / "dev-journey" / "08-templates" / "GAMBIARRAS_POR_SPRINT.md"
    if not path.exists():
        return False

    content = path.read_text(encoding="utf-8")
    original = content

    content = re.sub(
        r'Copiar "\d+ tools, \d+ comandos" do GUIDE\.md sem verificar',
        f'Copiar "{tools} tools, {commands} comandos" do GUIDE.md sem verificar',
        content,
    )

    changed = content != original
    if changed and not check:
        path.write_text(content, encoding="utf-8")
        logger.info("GAMBIARRAS_POR_SPRINT.md atualizado")
    elif changed:
        logger.info("GAMBIARRAS_POR_SPRINT.md precisa de atualização")

    return changed


def update_sprint_template(tools: int, commands: int, services: int, cli_lines: int, check: bool) -> bool:
    """Atualiza dev-journey/08-templates/SPRINT_TEMPLATE_V2.md."""
    path = PROJECT_ROOT / "dev-journey" / "08-templates" / "SPRINT_TEMPLATE_V2.md"
    if not path.exists():
        return False

    content = path.read_text(encoding="utf-8")
    original = content

    # Aproxima cli.py para multiplo de 10 (estabilidade idempotente).
    cli_rounded = round(cli_lines / 10) * 10

    content = re.sub(
        r"> - \d+ tools, \d+ commands, \d+ services\. `cli\.py` ~?\d+ linhas\.",
        f"> - {tools} tools, {commands} commands, {services} services. `cli.py` ~{cli_rounded} linhas.",
        content,
    )

    changed = content != original
    if changed and not check:
        path.write_text(content, encoding="utf-8")
        logger.info("SPRINT_TEMPLATE_V2.md atualizado")
    elif changed:
        logger.info("SPRINT_TEMPLATE_V2.md precisa de atualização")

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
    cockpit_http, cockpit_ws = _count_cockpit_endpoints()
    cli_lines = _count_cli_lines()
    tool_files = _count_tool_files()
    invariants = _count_invariants()
    default_model = _default_model()
    version = _read_version()

    print()
    print("=" * 50)
    print("  Estado real do código")
    print("=" * 50)
    print(f"  Tools:     {tools}")
    print(f"  Commands:  {commands}")
    print(f"  Services:  {services}")
    print(f"  Testes:    {tests} (catalogados em self._add)")
    print(f"  ADRs:      {adrs}")
    print(f"  Cockpit:   {cockpit_http} HTTP + {cockpit_ws} WS")
    print(f"  cli.py:    {cli_lines} linhas")
    print(f"  tools/:    {tool_files} arquivos")
    print(f"  invariants:{invariants} checks")
    print(f"  Modelo:    {default_model}")
    print(f"  Versão:    {version}")
    print(
        f"  Sprints:   {sprints['concluidos']} concluídas | {sprints['producao']} pendentes | {sprints['backlog']} backlog"  # noqa: E501
    )
    print(f"  Próxima:   {next_sprint}")
    print()

    changes = []
    if update_guide_md(tools, commands, services, tests, adrs, sprints, args.check):
        changes.append("GUIDE.md")
    if update_readme(tools, commands, services, tests, cockpit_http, cockpit_ws, sprints["concluidos"], args.check):
        changes.append("README.md")
    if update_port_status(tools, commands, services, args.check):
        changes.append("PORT_STATUS.md")
    if update_architecture(tools, commands, services, args.check):
        changes.append("ARCHITECTURE.md")
    if update_sprint_template(tools, commands, services, cli_lines, args.check):
        changes.append("SPRINT_TEMPLATE_V2.md")
    if update_project_snapshot(
        tools, commands, services, tests, adrs, sprints["concluidos"],
        tool_files, invariants, default_model, version, args.check,
    ):
        changes.append("PROJECT_SNAPSHOT.md")
    if update_gambiarras(tools, commands, args.check):
        changes.append("GAMBIARRAS_POR_SPRINT.md")

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
