"""PluginManager — descobre, valida e gerencia plugins (PLUGINS-01).

Estrutura esperada por plugin:

  ~/.nyx/plugins/<name>/
    manifest.toml
    <name>.py   (ou módulos py com tools/@nyx_command registrados)

manifest.toml schema:
  [plugin]
  name = "exemplo"
  version = "0.1.0"
  description = "..."
  tools = ["tool_name_1", "tool_name_2"]
  commands = ["command_name_1"]

Validação AST: top-level do plugin não pode ter expression statements
(só Import, ImportFrom, FunctionDef, ClassDef, Assign). Bloqueia plugin
que tenta executar código arbitrário no import time.
"""

from __future__ import annotations

import ast
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from nyx.agent.services.logging_service import get_logger
from nyx.config.defaults import NYX_PLUGINS_DIR

logger = get_logger("nyx.plugins")

REQUIRED_KEYS = {"name", "version", "description"}
ALLOWED_AST_TOP = (
    ast.Import,
    ast.ImportFrom,
    ast.FunctionDef,
    ast.AsyncFunctionDef,
    ast.ClassDef,
    ast.Assign,
    ast.AnnAssign,
    ast.Expr,  # docstring é Expr/Constant; será inspecionada abaixo
)


@dataclass
class Plugin:
    name: str
    path: Path
    version: str = ""
    description: str = ""
    tools: list[str] = field(default_factory=list)
    commands: list[str] = field(default_factory=list)
    loaded: bool = False
    error: str | None = None
    # PLUGINS-03: referência ao módulo após import. Mantida None até
    # PluginManager.load() concluir importlib.util.spec_from_file_location
    # com sucesso. Usada por discover_plugin_tools() para resolver os
    # callables das tools declaradas em manifest.tools[].
    module: Any = None


def _load_toml(path: Path) -> dict[str, Any]:
    if sys.version_info < (3, 11):
        return {}
    try:
        import tomllib
    except ImportError:
        return {}
    with path.open("rb") as f:
        return tomllib.load(f)


def _validate_module_ast(py_path: Path) -> str | None:
    """Retorna None se OK; mensagem de erro se top-level inseguro."""
    try:
        tree = ast.parse(py_path.read_text(encoding="utf-8"))
    except (OSError, SyntaxError) as exc:
        return f"AST parse falhou: {exc}"
    for node in tree.body:
        if isinstance(node, ALLOWED_AST_TOP):
            if isinstance(node, ast.Expr):
                # Permite somente docstring (Constant string em primeira posição).
                if not (isinstance(node.value, ast.Constant) and isinstance(node.value.value, str)):
                    return f"top-level Expr não-docstring na linha {node.lineno}"
            continue
        return f"top-level {type(node).__name__} proibido na linha {node.lineno}"
    return None


class PluginManager:
    def __init__(self, plugins_dir: str | Path = NYX_PLUGINS_DIR) -> None:
        self.plugins_dir = Path(plugins_dir)
        self.plugins: dict[str, Plugin] = {}

    def discover(self) -> dict[str, Plugin]:
        """Descobre plugins (não importa; só lê manifest)."""
        self.plugins.clear()
        if not self.plugins_dir.is_dir():
            return self.plugins
        for entry in sorted(self.plugins_dir.iterdir()):
            if not entry.is_dir() or entry.name.startswith("."):
                continue
            manifest = entry / "manifest.toml"
            if not manifest.is_file():
                logger.warning("plugin %s sem manifest.toml — pulando", entry.name)
                continue
            try:
                data = _load_toml(manifest)
            except Exception as exc:  # noqa: BLE001 -- toml mal-formado
                logger.warning("manifest inválido %s: %s", manifest, exc)
                continue
            section = (data or {}).get("plugin") or {}
            missing = REQUIRED_KEYS - set(section.keys())
            if missing:
                logger.warning(
                    "plugin %s manifest faltando chaves %s — pulando",
                    entry.name,
                    missing,
                )
                continue
            self.plugins[section["name"]] = Plugin(
                name=section["name"],
                path=entry,
                version=str(section.get("version", "")),
                description=str(section.get("description", "")),
                tools=list(section.get("tools") or []),
                commands=list(section.get("commands") or []),
            )
        return self.plugins

    def load(self, name: str) -> bool:
        """Importa o módulo do plugin (após validação AST)."""
        plugin = self.plugins.get(name)
        if plugin is None:
            return False
        py = plugin.path / f"{plugin.name}.py"
        if not py.is_file():
            plugin.error = f"módulo {py.name} ausente"
            logger.warning("plugin %s: %s", name, plugin.error)
            return False
        verdict = _validate_module_ast(py)
        if verdict is not None:
            plugin.error = f"AST inseguro: {verdict}"
            logger.warning("plugin %s: %s", name, plugin.error)
            return False
        try:
            import importlib.util as _ilu

            spec = _ilu.spec_from_file_location(f"nyx_plugins.{plugin.name}", py)
            if spec is None or spec.loader is None:
                plugin.error = "spec_from_file_location retornou None"
                return False
            mod = _ilu.module_from_spec(spec)
            spec.loader.exec_module(mod)
            plugin.loaded = True
            plugin.module = mod  # PLUGINS-03: necessário para discover_plugin_tools
            logger.info("plugin %s carregado (v%s)", plugin.name, plugin.version)
            return True
        except Exception as exc:  # noqa: BLE001 -- import pode levantar qualquer coisa
            plugin.error = f"import falhou: {exc}"
            logger.warning("plugin %s: %s", name, plugin.error)
            return False

    def load_all(self) -> dict[str, bool]:
        self.discover()
        return {name: self.load(name) for name in self.plugins}

    def list(self) -> list[Plugin]:
        if not self.plugins:
            self.discover()
        return list(self.plugins.values())

    def reload(self) -> dict[str, bool]:
        """Re-descobre e re-carrega tudo (idempotente)."""
        return self.load_all()

    def uninstall(self, name: str) -> bool:
        """Remove o diretório do plugin do disco. Retorna True se removido."""
        import shutil

        plugin = self.plugins.get(name)
        if plugin is None or not plugin.path.is_dir():
            return False
        shutil.rmtree(plugin.path)
        del self.plugins[name]
        return True

    def install(self, src_path: str | Path) -> str | None:
        """Copia um diretório de plugin externo para ~/.nyx/plugins/<name>/.

        Retorna o nome do plugin instalado, ou None se falhar.
        """
        import shutil

        src = Path(src_path)
        if not src.is_dir():
            logger.warning("install: %s não é diretório", src)
            return None
        manifest = src / "manifest.toml"
        if not manifest.is_file():
            logger.warning("install: %s sem manifest.toml", src)
            return None
        try:
            data = _load_toml(manifest)
        except Exception as exc:  # noqa: BLE001
            logger.warning("install: manifest inválido %s", exc)
            return None
        name = (data or {}).get("plugin", {}).get("name")
        if not name:
            logger.warning("install: manifest sem chave 'name'")
            return None
        dst = self.plugins_dir / str(name)
        if dst.exists():
            logger.warning("install: plugin %s já instalado em %s", name, dst)
            return None
        self.plugins_dir.mkdir(parents=True, exist_ok=True)
        shutil.copytree(src, dst)
        return str(name)


def discover_plugin_tools(
    plugins_dir: str | Path = NYX_PLUGINS_DIR,
) -> dict[str, list[dict[str, Any]]]:
    """Descobre tools expostas por plugins instalados (PLUGINS-03).

    Itera ~/.nyx/plugins/, executa load_all() (que aplica AST check
    anti-código-arbitrário do PLUGINS-01/02) e, para cada plugin
    carregado, resolve os nomes em manifest.tools[] como callables no
    módulo. Retorna mapeamento plugin_name -> lista de tool_defs:

        {
          "exemplo": [
            {"name": "soma", "description": "...", "callable": <func>},
            ...
          ],
          ...
        }

    Boot-tolerante: diretório ausente retorna {}. Plugin com erro
    (AST, import, módulo sem o callable) é ignorado individualmente
    sem derrubar a descoberta dos demais.
    """
    pm = PluginManager(plugins_dir=plugins_dir)
    if not pm.plugins_dir.is_dir():
        return {}
    load_results = pm.load_all()
    out: dict[str, list[dict[str, Any]]] = {}
    for name, ok in load_results.items():
        if not ok:
            continue
        plugin = pm.plugins.get(name)
        if plugin is None or plugin.module is None:
            continue
        tool_defs: list[dict[str, Any]] = []
        for tool_name in plugin.tools:
            fn = getattr(plugin.module, tool_name, None)
            if not callable(fn):
                logger.warning(
                    "plugin %s declara tool %s mas módulo não expõe callable",
                    name,
                    tool_name,
                )
                continue
            description = (
                getattr(fn, "__doc__", None)
                or f"Plugin tool {name}.{tool_name}"
            )
            tool_defs.append(
                {
                    "name": tool_name,
                    "description": str(description).strip().split("\n")[0],
                    "callable": fn,
                }
            )
        if tool_defs:
            out[name] = tool_defs
    return out
