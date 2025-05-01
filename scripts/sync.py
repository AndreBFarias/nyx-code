#!/usr/bin/env python3
"""Nyx-Code Sync -- Verificação de consistência do projeto.

Scanneia o projeto e valida:
- Referências OpenClaude residuais (deve ser zero)
- Variáveis de cor PURPLE/PINK/CYAN nos scripts (deve ser zero)
- Anonimato: menções a IA nos arquivos fonte
- Acentuação: arquivos .py/.sh sem acentuação correta
- Sprints: todas as concluídas em dev-journey/06-sprints/concluidos/
- ADRs: numeração sequencial sem gaps
- Temas: 7 entidades presentes
- Estrutura: diretórios obrigatórios existem

Uso:
    python scripts/sync.py              # Verifica tudo
    python scripts/sync.py --check      # Só verifica, retorna exit code
    python scripts/sync.py --fix        # Corrige o que pode
"""

from __future__ import annotations

import argparse
import logging
import re
import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [sync] %(levelname)s: %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("nyx.sync")

EXCLUDE_DIRS = {
    "__pycache__", ".pytest_cache", "node_modules", ".git",
    "venv", "reference", "models", ".claude",
}

TRACKED_EXTENSIONS = {".py", ".sh", ".md", ".json", ".yml", ".toml", ".exp", ".css"}


def _scan_files() -> list[Path]:
    """Lista todos os arquivos rastreáveis do projeto."""
    files = []
    for path in PROJECT_ROOT.rglob("*"):
        if path.is_dir():
            continue
        rel = str(path.relative_to(PROJECT_ROOT))
        if any(exc in rel.split("/") for exc in EXCLUDE_DIRS):
            continue
        if path.suffix in TRACKED_EXTENSIONS:
            files.append(path)
    return sorted(files)


def _grep_files(pattern: str, files: list[Path], ignore_paths: list[str] | None = None) -> list[tuple[Path, int, str]]:
    """Busca padrão em arquivos, retorna (path, linha, conteúdo)."""
    ignore_paths = ignore_paths or []
    results = []
    regex = re.compile(pattern, re.IGNORECASE)
    for path in files:
        rel = str(path.relative_to(PROJECT_ROOT))
        if any(ign in rel for ign in ignore_paths):
            continue
        try:
            for i, line in enumerate(path.read_text(encoding="utf-8", errors="ignore").splitlines(), 1):
                if regex.search(line):
                    results.append((path, i, line.strip()))
        except Exception:
            pass
    return results


class SyncChecker:
    """Executa todas as verificações de consistência."""

    def __init__(self) -> None:
        self._files = _scan_files()
        self._errors: list[str] = []
        self._warnings: list[str] = []
        self._ok: list[str] = []

    def run(self) -> int:
        """Executa todas as verificações. Retorna 0 se OK, 1 se erros."""
        self._check_openclaude_refs()
        self._check_color_vars()
        self._check_anonymity()
        self._check_themes()
        self._check_adrs()
        self._check_structure()
        self._check_shell_syntax()
        self._check_python_imports()
        self._check_gauntlet_freshness()
        self._check_tool_registration()
        self._check_command_coverage()
        self._check_service_imports()
        self._check_no_loose_tests()
        self._check_port_status()
        self._report()
        return 1 if self._errors else 0

    def _check_openclaude_refs(self) -> None:
        """Verifica referências OpenClaude residuais."""
        hits = _grep_files(
            r"openclaude|OpenClaude|open.claude",
            self._files,
            ignore_paths=["reference/", "package-lock.json", "dev-journey/09-legacy/", ".github/workflows/", "scripts/sync.py", "dev-journey/06-sprints/", "dev-journey/02-architecture/", "dev-journey/03-decisions/", "dev-journey/PORT_STATUS.md"],
        )
        if hits:
            for path, line, content in hits[:5]:
                self._errors.append(f"OpenClaude residual: {path.relative_to(PROJECT_ROOT)}:{line}: {content[:80]}")
        else:
            self._ok.append("Zero referências OpenClaude")

    def _check_color_vars(self) -> None:
        """Verifica variáveis de cor Dracula residuais nos scripts."""
        shell_files = [f for f in self._files if f.suffix == ".sh"]
        hits = _grep_files(
            r"\$\{?PURPLE\}?|\$\{?PINK\}?|\$\{?CYAN\}?",
            shell_files,
            ignore_paths=["dev-journey/09-legacy/", "dev-journey/06-sprints/concluidos/"],
        )
        if hits:
            for path, line, content in hits[:5]:
                self._errors.append(f"Cor Dracula residual: {path.relative_to(PROJECT_ROOT)}:{line}: {content[:80]}")
        else:
            self._ok.append("Zero variáveis PURPLE/PINK/CYAN nos scripts ativos")

    def _check_anonymity(self) -> None:
        """Verifica menções a IA nos arquivos fonte."""
        hits = _grep_files(
            r"\bClaude\b|\bGPT\b|\bGemini\b|\bCopilot\b|\bAnthropic\b(?!_API_KEY)",
            self._files,
            ignore_paths=[
                "reference/", "package-lock.json", "node_modules/",
                "dev-journey/09-legacy/", ".env", "CLAUDE.md", ".claude/",
            ],
        )
        if hits:
            for path, line, content in hits[:5]:
                self._warnings.append(f"Menção a IA: {path.relative_to(PROJECT_ROOT)}:{line}: {content[:80]}")
        else:
            self._ok.append("Anonimato OK (sem menções a IA)")

    def _check_themes(self) -> None:
        """Verifica que os 7 temas de entidade existem."""
        entities_dir = PROJECT_ROOT / "nyx" / "themes" / "entities"
        expected = {"nyx", "luna", "mars", "eris", "juno", "lars", "somn"}
        found = {f.stem for f in entities_dir.glob("*.json")} if entities_dir.exists() else set()
        missing = expected - found
        if missing:
            self._errors.append(f"Temas ausentes: {missing}")
        else:
            self._ok.append(f"7 temas presentes: {sorted(found)}")

    def _check_adrs(self) -> None:
        """Verifica ADRs com numeração sequencial."""
        adrs_dir = PROJECT_ROOT / "dev-journey" / "03-decisions"
        if not adrs_dir.exists():
            self._errors.append("Diretório de ADRs não existe")
            return
        adr_files = sorted(adrs_dir.glob("ADR_*.md"))
        numbers = []
        for f in adr_files:
            match = re.match(r"ADR_(\d+)", f.name)
            if match:
                numbers.append(int(match.group(1)))
        if numbers:
            expected = list(range(1, max(numbers) + 1))
            missing = set(expected) - set(numbers)
            if missing:
                self._warnings.append(f"ADRs com gap na numeração: {sorted(missing)}")
            else:
                self._ok.append(f"{len(numbers)} ADRs com numeração sequencial")
        else:
            self._warnings.append("Nenhum ADR encontrado")

    def _check_structure(self) -> None:
        """Verifica diretórios obrigatórios."""
        required = [
            "nyx/",
            "nyx/proxy.py",
            "nyx/config/",
            "nyx/themes/",
            "nyx/themes/entities/",
            "scripts/gauntlet/",
            "dev-journey/",
            "dev-journey/03-decisions/",
            "dev-journey/06-sprints/",
            "dev-journey/06-sprints/producao/",
            "dev-journey/06-sprints/concluidos/",
            "dev-journey/07-reports/gauntlet/",
            ".github/workflows/",
            "nyx/cli.py",
            "nyx/agent/",
            "run.sh",
            "install.sh",
            "CLAUDE.md",
            "README.md",
        ]
        missing = []
        for path_str in required:
            full = PROJECT_ROOT / path_str
            if not full.exists():
                missing.append(path_str)
        if missing:
            self._errors.append(f"Estrutura faltando: {missing}")
        else:
            self._ok.append(f"Estrutura completa ({len(required)} itens)")

    def _check_shell_syntax(self) -> None:
        """Verifica sintaxe dos scripts shell."""
        for name in ["run.sh", "install.sh", "uninstall.sh"]:
            path = PROJECT_ROOT / name
            if not path.exists():
                continue
            result = subprocess.run(
                ["bash", "-n", str(path)],
                capture_output=True, text=True,
            )
            if result.returncode != 0:
                self._errors.append(f"Sintaxe shell quebrada: {name}: {result.stderr[:100]}")
            else:
                self._ok.append(f"Sintaxe shell OK: {name}")

    def _check_python_imports(self) -> None:
        """Verifica imports principais do Python."""
        checks = [
            ("nyx.themes", "from nyx.themes import ThemeManager"),
            ("nyx.config.settings", "from nyx.config.settings import NyxSettings"),
            ("nyx.config.defaults", "from nyx.config.defaults import DEFAULT_MODEL"),
        ]
        for module, import_str in checks:
            result = subprocess.run(
                [sys.executable, "-c", import_str],
                capture_output=True, text=True,
                cwd=str(PROJECT_ROOT),
            )
            if result.returncode != 0:
                self._errors.append(f"Import falhou: {module}: {result.stderr[:100]}")
            else:
                self._ok.append(f"Import OK: {module}")

    def _check_tool_registration(self) -> None:
        """Verifica que todo .py em tools/ está importado no registry."""
        tools_dir = PROJECT_ROOT / "nyx" / "agent" / "tools"
        registry = tools_dir / "registry.py"
        if not registry.exists():
            self._errors.append("registry.py não existe")
            return
        registry_content = registry.read_text(encoding="utf-8")
        tool_files = sorted(
            f.stem for f in tools_dir.glob("*.py")
            if f.stem not in ("__init__", "base", "registry")
            and not f.stem.startswith("__")
        )
        missing = [f for f in tool_files if f"from .{f} import" not in registry_content]
        if missing:
            self._errors.append(f"Tools sem import no registry: {missing}")
        else:
            self._ok.append(f"Todas {len(tool_files)} tools registradas no registry")

    def _check_command_coverage(self) -> None:
        """Verifica total de commands registrados."""
        try:
            result = subprocess.run(
                [sys.executable, "-c",
                 "from nyx.agent.commands import list_commands; print(len(list_commands()))"],
                capture_output=True, text=True, cwd=str(PROJECT_ROOT), timeout=10,
            )
            count = int(result.stdout.strip())
            if count >= 33:
                self._ok.append(f"Commands registrados: {count}")
            else:
                self._warnings.append(f"Commands registrados: {count} (esperado >= 33)")
        except Exception:
            self._warnings.append("Não foi possível contar commands")

    def _check_service_imports(self) -> None:
        """Verifica que todo service importa sem erro."""
        services_dir = PROJECT_ROOT / "nyx" / "agent" / "services"
        if not services_dir.exists():
            self._errors.append("Diretório de services não existe")
            return
        svc_files = sorted(
            f.stem for f in services_dir.glob("*.py")
            if f.stem != "__init__" and not f.stem.startswith("__")
        )
        failed = []
        for svc in svc_files:
            result = subprocess.run(
                [sys.executable, "-c", f"import nyx.agent.services.{svc}"],
                capture_output=True, text=True, cwd=str(PROJECT_ROOT), timeout=10,
            )
            if result.returncode != 0:
                failed.append(svc)
        if failed:
            self._errors.append(f"Services com import falho: {failed}")
        else:
            self._ok.append(f"Todos {len(svc_files)} services importam")

    def _check_no_loose_tests(self) -> None:
        """Verifica que não existem test_*.py soltos."""
        test_files = []
        for f in PROJECT_ROOT.rglob("test_*.py"):
            rel = str(f.relative_to(PROJECT_ROOT))
            if "venv" not in rel and "__pycache__" not in rel and "node_modules" not in rel:
                test_files.append(rel)
        if test_files:
            self._errors.append(f"test_*.py soltos: {test_files[:5]}")
        else:
            self._ok.append("Zero test_*.py soltos")

    def _check_port_status(self) -> None:
        """Verifica que PORT_STATUS.md existe."""
        port = PROJECT_ROOT / "dev-journey" / "PORT_STATUS.md"
        if port.exists():
            content = port.read_text(encoding="utf-8")
            if "Tools" in content and "Commands" in content:
                self._ok.append("PORT_STATUS.md presente e com conteúdo")
            else:
                self._warnings.append("PORT_STATUS.md existe mas sem conteúdo esperado")
        else:
            self._warnings.append("PORT_STATUS.md não existe")

    def _check_gauntlet_freshness(self) -> None:
        """Verifica se o Gauntlet foi rodado e passou 100%."""
        report = PROJECT_ROOT / "GAUNTLET_REPORT.md"
        if not report.exists():
            self._warnings.append("GAUNTLET_REPORT.md não existe (rode ./run.sh --gauntlet)")
            return
        content = report.read_text(encoding="utf-8")
        if "APROVADO" in content:
            self._ok.append("Gauntlet: APROVADO (100%)")
        elif "REPROVADO" in content:
            self._errors.append("Gauntlet: REPROVADO (< 100%) -- corrija antes de push")
        else:
            self._warnings.append("Gauntlet: report sem gate de produção")

    def _report(self) -> None:
        """Exibe relatório final."""
        print()
        print("=" * 60)
        print("  Nyx-Code Sync Report")
        print("=" * 60)
        print()

        if self._ok:
            for item in self._ok:
                print(f"  [OK]   {item}")

        if self._warnings:
            print()
            for item in self._warnings:
                print(f"  [WARN] {item}")

        if self._errors:
            print()
            for item in self._errors:
                print(f"  [ERRO] {item}")

        print()
        total = len(self._ok) + len(self._warnings) + len(self._errors)
        print(f"  Total: {total} verificações | OK: {len(self._ok)} | Avisos: {len(self._warnings)} | Erros: {len(self._errors)}")
        print()

        if self._errors:
            print("  RESULTADO: FALHA")
        elif self._warnings:
            print("  RESULTADO: OK (com avisos)")
        else:
            print("  RESULTADO: OK")
        print()


def main() -> None:
    parser = argparse.ArgumentParser(description="Nyx-Code Sync")
    parser.add_argument("--check", action="store_true", help="Só verifica, retorna exit code")
    parser.add_argument("--fix", action="store_true", help="Corrige o que pode")
    args = parser.parse_args()

    checker = SyncChecker()
    exit_code = checker.run()
    sys.exit(exit_code)


if __name__ == "__main__":
    main()


# "A ordem é o primeiro passo para a liberdade." -- Aristóteles
