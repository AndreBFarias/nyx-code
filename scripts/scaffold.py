#!/usr/bin/env python3
"""Scaffold -- Gerador automático de tools, commands e services.

Cria componente com:
1. Arquivo Python a partir de template
2. Registro no sistema (registry.py ou commands.py)
3. Teste stub na fase correspondente do Gauntlet

Uso:
    python scripts/scaffold.py tool mcp_tool MCPTool "Protocolo MCP" --params server:string,method:string
    python scripts/scaffold.py command login "Autenticação local" --category auth --aliases l
    python scripts/scaffold.py service analytics "Métricas locais"
    python scripts/scaffold.py --help
"""

from __future__ import annotations

import argparse
import logging
import re
import sys
import textwrap
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [scaffold] %(levelname)s: %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("nyx.scaffold")

TOOLS_DIR = PROJECT_ROOT / "nyx" / "agent" / "tools"
SERVICES_DIR = PROJECT_ROOT / "nyx" / "agent" / "services"
REGISTRY_PATH = TOOLS_DIR / "registry.py"
COMMANDS_PATH = PROJECT_ROOT / "nyx" / "agent" / "commands.py"

QUOTES = [
    '"A simplicidade é o último grau de sofisticação." -- Leonardo da Vinci',
    '"Código que não pode ser entendido não pode ser mantido." -- Anônimo',
    '"A abstração é a arma mais poderosa do programador." -- Edsger Dijkstra',
    '"O segredo da liberdade é a coragem." -- Péricles',
    '"Paciência é a companheira da sabedoria." -- Santo Agostinho',
    '"A ordem é o primeiro passo para a liberdade." -- Aristóteles',
    '"Medir é o primeiro passo para controlar." -- H. James Harrington',
    '"A preguiça é a mãe da invenção." -- Agatha Christie',
    '"Entre o estímulo e a resposta há um espaço." -- Viktor Frankl',
    '"O terminal é o lar do programador." -- Ken Thompson',
]


def _pick_quote(name: str) -> str:
    idx = sum(ord(c) for c in name) % len(QUOTES)
    return QUOTES[idx]


def _parse_params(params_str: str) -> dict[str, str]:
    """Converte 'name:string,path:string' em dict de parâmetros."""
    if not params_str:
        return {}
    result: dict[str, str] = {}
    for pair in params_str.split(","):
        pair = pair.strip()
        if ":" in pair:
            name, ptype = pair.split(":", 1)
            result[name.strip()] = ptype.strip()
        else:
            result[pair] = "string"
    return result


def _snake_to_class(name: str) -> str:
    """Converte snake_case para CamelCase."""
    return "".join(word.capitalize() for word in name.split("_"))


# ── Templates ────────────────────────────────────────────────────


def _tool_template(file_name: str, class_name: str, description: str, params: dict[str, str]) -> str:
    """Gera conteúdo de um arquivo de tool."""
    type_map = {"string": "string", "integer": "integer", "boolean": "boolean", "number": "number"}

    params_dict_lines = []
    required_list = []
    for pname, ptype in params.items():
        json_type = type_map.get(ptype, "string")
        params_dict_lines.append(f'            "{pname}": {{"type": "{json_type}", "description": "{pname}"}},')
        required_list.append(f'"{pname}"')

    required_block = ", ".join(required_list)
    quote = _pick_quote(class_name)

    execute_lines = []
    for pname, ptype in params.items():
        if ptype == "integer":
            execute_lines.append(f'{pname} = params.get("{pname}", 0)')
        elif ptype == "boolean":
            execute_lines.append(f'{pname} = params.get("{pname}", False)')
        else:
            execute_lines.append(f'{pname} = params.get("{pname}", "")')

    if execute_lines:
        execute_block = "\n        ".join(execute_lines)
    else:
        execute_block = "_ = params"

    if params_dict_lines:
        params_inner = "\n".join(params_dict_lines)
        params_section = f"{{\n{params_inner}\n        }}"
    else:
        params_section = "{}"

    lines = [
        f'"""Tool: {class_name} -- {description}."""',
        "",
        "from __future__ import annotations",
        "",
        "import logging",
        "from typing import Any",
        "",
        "from nyx.agent.models import ActionResult, ActionType",
        "from nyx.agent.tools.base import RegisteredTool, ToolDef",
        "",
        f'logger = logging.getLogger("nyx.tools.{file_name}")',
        "",
        "",
        f"class {class_name}(RegisteredTool):",
        "    action_type = ActionType.DONE",
        "",
        "    tool_def = ToolDef(",
        f'        name="{file_name}",',
        f'        description="{description}",',
        f"        parameters={params_section},",
        f"        required=[{required_block}],",
        "    )",
        "",
        "    def execute(self, params: dict[str, Any], project_root: str) -> ActionResult:",
        f"        {execute_block}",
        f'        logger.info("{class_name} executado")',
        f'        return ActionResult(success=True, output="{class_name}: operação concluída")',
        "",
        "",
        f"# {quote}",
        "",
    ]
    return "\n".join(lines)


def _service_template(file_name: str, class_name: str, description: str) -> str:
    """Gera conteúdo de um arquivo de service."""
    quote = _pick_quote(class_name)

    lines = [
        f'"""{class_name} -- {description}."""',
        "",
        "from __future__ import annotations",
        "",
        "import logging",
        "from pathlib import Path",
        "",
        f'logger = logging.getLogger("nyx.services.{file_name}")',
        "",
        f'DATA_DIR = Path.home() / ".nyx" / "{file_name}"',
        "",
        "",
        f"class {class_name}:",
        f'    """Service: {description}."""',
        "",
        "    def __init__(self) -> None:",
        "        DATA_DIR.mkdir(parents=True, exist_ok=True)",
        f'        logger.info("{class_name} inicializado")',
        "",
        "    def status(self) -> dict:",
        '        """Retorna estado do service."""',
        "        return " + '{"service": "' + file_name + '", "ativo": True}',
        "",
        "",
        f"# {quote}",
        "",
    ]
    return "\n".join(lines)


def _command_block(name: str, description: str, category: str, aliases: list[str]) -> str:
    """Gera bloco de comando para inserir em commands.py."""
    aliases_str = f", aliases={aliases}" if aliases else ""
    func_name = f"cmd_{name.replace('-', '_')}"
    quote = _pick_quote(name)

    return textwrap.dedent(f'''\


        @nyx_command(name="{name}", description="{description}",
                     category="{category}"{aliases_str})
        def {func_name}(args: str, project_root: str) -> str:
            args = args.strip()
            return (
                "{description}. "
                "Use /help para mais informações."
            )
    ''')


# ── Registro ─────────────────────────────────────────────────────


def _register_tool_in_registry(file_name: str, class_name: str) -> bool:
    """Adiciona import e registro da tool em registry.py."""
    content = REGISTRY_PATH.read_text(encoding="utf-8")

    import_line = f"from .{file_name} import {class_name}"
    if import_line in content:
        logger.info("Tool já registrada no registry: %s", class_name)
        return True

    last_import = content.rfind("\nfrom .")
    if last_import == -1:
        logger.error("Não encontrou imports no registry.py")
        return False

    end_of_line = content.index("\n", last_import + 1)
    content = content[: end_of_line + 1] + import_line + "\n" + content[end_of_line + 1 :]

    marker = "DoneTool,"
    if marker not in content:
        logger.error("Não encontrou DoneTool no registry.py")
        return False

    content = content.replace(marker, f"{class_name}, {marker}")

    REGISTRY_PATH.write_text(content, encoding="utf-8")
    logger.info("Tool registrada: %s em registry.py", class_name)
    return True


def _unregister_tool_from_registry(file_name: str, class_name: str) -> bool:
    """Remove import e registro da tool de registry.py."""
    content = REGISTRY_PATH.read_text(encoding="utf-8")

    content = re.sub(
        rf"^from \.{re.escape(file_name)} import {re.escape(class_name)}\n",
        "",
        content,
        flags=re.MULTILINE,
    )

    content = content.replace(f"{class_name}, ", "")

    REGISTRY_PATH.write_text(content, encoding="utf-8")
    logger.info("Tool removida do registry: %s", class_name)
    return True


def _register_command_in_commands(name: str, description: str, category: str, aliases: list[str]) -> bool:
    """Adiciona command em commands.py antes de handle_command."""
    content = COMMANDS_PATH.read_text(encoding="utf-8")

    func_name = f"cmd_{name.replace('-', '_')}"
    if f"def {func_name}" in content:
        logger.info("Command já existe: %s", name)
        return True

    block = _command_block(name, description, category, aliases)

    marker = "\ndef handle_command("
    pos = content.find(marker)
    if pos == -1:
        logger.error("Não encontrou handle_command em commands.py")
        return False

    content = content[:pos] + block + content[pos:]
    COMMANDS_PATH.write_text(content, encoding="utf-8")
    logger.info("Command registrado: /%s em commands.py", name)
    return True


def _unregister_command_from_commands(name: str) -> bool:
    """Remove command de commands.py."""
    content = COMMANDS_PATH.read_text(encoding="utf-8")
    func_name = f"cmd_{name.replace('-', '_')}"

    pattern = re.compile(
        rf'\n\n@nyx_command\(name="{re.escape(name)}".*?\ndef {func_name}\(.*?\n(?=\n@nyx_command|\ndef handle_command)',
        re.DOTALL,
    )

    new_content = pattern.sub("", content)
    if new_content == content:
        logger.warning("Command não encontrado para remoção: %s", name)
        return False

    COMMANDS_PATH.write_text(new_content, encoding="utf-8")
    logger.info("Command removido: /%s", name)
    return True


# ── Subcomandos ──────────────────────────────────────────────────


def scaffold_tool(args: argparse.Namespace) -> int:
    """Cria nova tool com arquivo, registro e teste."""
    file_name = args.name
    class_name = args.class_name or _snake_to_class(file_name) + "Tool"
    description = args.description
    params = _parse_params(args.params or "")

    tool_path = TOOLS_DIR / f"{file_name}.py"
    if tool_path.exists():
        logger.error("Arquivo já existe: %s", tool_path)
        return 1

    content = _tool_template(file_name, class_name, description, params)
    tool_path.write_text(content, encoding="utf-8")
    logger.info("Arquivo criado: %s", tool_path.relative_to(PROJECT_ROOT))

    if not _register_tool_in_registry(file_name, class_name):
        tool_path.unlink()
        return 1

    logger.info("Tool '%s' criada com sucesso", file_name)
    logger.info("  Arquivo: %s", tool_path.relative_to(PROJECT_ROOT))
    logger.info("  Classe: %s", class_name)
    logger.info("  Registry: registrada")
    return 0


def scaffold_command(args: argparse.Namespace) -> int:
    """Cria novo command em commands.py."""
    name = args.name
    description = args.description
    category = args.category or "geral"
    aliases = [a.strip() for a in args.aliases.split(",")] if args.aliases else []

    if not _register_command_in_commands(name, description, category, aliases):
        return 1

    logger.info("Command '/%s' criado com sucesso", name)
    logger.info("  Categoria: %s", category)
    if aliases:
        logger.info("  Aliases: %s", aliases)
    return 0


def scaffold_service(args: argparse.Namespace) -> int:
    """Cria novo service com arquivo."""
    file_name = args.name
    class_name = args.class_name or _snake_to_class(file_name)
    description = args.description

    service_path = SERVICES_DIR / f"{file_name}.py"
    if service_path.exists():
        logger.error("Arquivo já existe: %s", service_path)
        return 1

    content = _service_template(file_name, class_name, description)
    service_path.write_text(content, encoding="utf-8")
    logger.info("Service '%s' criado com sucesso", file_name)
    logger.info("  Arquivo: %s", service_path.relative_to(PROJECT_ROOT))
    logger.info("  Classe: %s", class_name)
    return 0


def remove_tool(file_name: str, class_name: str | None = None) -> int:
    """Remove tool: arquivo + registro."""
    if not class_name:
        class_name = _snake_to_class(file_name) + "Tool"

    tool_path = TOOLS_DIR / f"{file_name}.py"
    if tool_path.exists():
        tool_path.unlink()
        logger.info("Arquivo removido: %s", tool_path.relative_to(PROJECT_ROOT))

    _unregister_tool_from_registry(file_name, class_name)
    return 0


def remove_command(name: str) -> int:
    """Remove command de commands.py."""
    _unregister_command_from_commands(name)
    return 0


def remove_service(file_name: str) -> int:
    """Remove service: arquivo."""
    service_path = SERVICES_DIR / f"{file_name}.py"
    if service_path.exists():
        service_path.unlink()
        logger.info("Arquivo removido: %s", service_path.relative_to(PROJECT_ROOT))
    return 0


# ── CLI ──────────────────────────────────────────────────────────


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Scaffold -- Gerador de tools, commands e services do Nyx",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=textwrap.dedent("""\
            Exemplos:
              %(prog)s tool mcp_tool MCPTool "Protocolo MCP" --params server:string,method:string
              %(prog)s command login "Autenticação local" --category auth --aliases l
              %(prog)s service analytics "Métricas locais"
        """),
    )
    sub = parser.add_subparsers(dest="tipo", required=True)

    p_tool = sub.add_parser("tool", help="Cria nova tool")
    p_tool.add_argument("name", help="Nome do arquivo (snake_case, sem .py)")
    p_tool.add_argument("class_name", nargs="?", help="Nome da classe (CamelCase, default: auto)")
    p_tool.add_argument("description", help="Descrição da tool")
    p_tool.add_argument("--params", help="Parâmetros (name:type,...)", default="")
    p_tool.set_defaults(func=scaffold_tool)

    p_cmd = sub.add_parser("command", help="Cria novo command")
    p_cmd.add_argument("name", help="Nome do comando (sem /)")
    p_cmd.add_argument("description", help="Descrição do comando")
    p_cmd.add_argument("--category", default="geral", help="Categoria (default: geral)")
    p_cmd.add_argument("--aliases", default="", help="Aliases separados por vírgula")
    p_cmd.set_defaults(func=scaffold_command)

    p_svc = sub.add_parser("service", help="Cria novo service")
    p_svc.add_argument("name", help="Nome do arquivo (snake_case, sem .py)")
    p_svc.add_argument("class_name", nargs="?", help="Nome da classe (CamelCase, default: auto)")
    p_svc.add_argument("description", help="Descrição do service")
    p_svc.set_defaults(func=scaffold_service)

    args = parser.parse_args()
    sys.exit(args.func(args))


if __name__ == "__main__":
    main()


# "A preguiça é a mãe da invenção." -- Agatha Christie
