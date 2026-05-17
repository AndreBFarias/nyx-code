"""Comandos de sistema -- config, env, doctor, version, model, theme, permissions, hooks, init, add-dir, break-cache."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

from nyx.agent.commands._registry import nyx_command
from nyx.agent.services.logging_service import get_logger
from nyx.config.defaults import (
    DEFAULT_MODEL as _DEFAULT_MODEL,
)
from nyx.config.defaults import (
    OLLAMA_HOST as _OLLAMA_HOST,
)
from nyx.config.defaults import (
    OLLAMA_PORT as _OLLAMA_PORT,
)
from nyx.config.defaults import (
    OLLAMA_URL as _OLLAMA_URL,
)
from nyx.config.defaults import (
    PROXY_PORT as _PROXY_PORT,
)
from nyx.config.defaults import (
    PROXY_V1_URL as _PROXY_V1_URL,
)

logger = get_logger("nyx.commands")


@nyx_command(name="config", description="Mostra ou edita configuração", category="sistema")
def cmd_config(args: str, project_root: str) -> str:
    args = args.strip()
    if not args:
        proxy = os.environ.get("OPENAI_BASE_URL", _PROXY_V1_URL)
        model = os.environ.get("OPENAI_MODEL", os.environ.get("NYX_MODEL", _DEFAULT_MODEL))
        ollama_host = os.environ.get("NYX_OLLAMA_HOST", _OLLAMA_HOST)
        ollama_port = os.environ.get("NYX_OLLAMA_PORT", str(_OLLAMA_PORT))
        ollama = f"http://{ollama_host}:{ollama_port}"
        return (
            "  Configuração atual:\n"
            f"    modelo: {model}\n"
            f"    proxy: {proxy}\n"
            f"    ollama: {ollama}\n"
            f"    projeto: {project_root}"
        )
    parts = args.split(" ", 1)
    if len(parts) == 1:
        val = os.environ.get(parts[0].upper(), None)
        if val:
            return f"  {parts[0]}: {val}"
        return (
            f"__error__Chave '{parts[0]}' não está definida no ambiente."
            "||Defina com: export {KEY}=<valor> ou use /env para ver as ativas."
        )
    return f"  Configuração via env: export {parts[0].upper()}={parts[1]}"


@nyx_command(name="env", description="Mostra variáveis de ambiente relevantes", category="sistema")
def cmd_env(_args: str, _root: str) -> str:
    prefixes = ("OPENAI_", "NYX_", "OLLAMA_", "ANTHROPIC_API")
    lines = ["  Variáveis de ambiente:"]
    for key, val in sorted(os.environ.items()):
        if any(key.startswith(p) for p in prefixes):
            display = val[:40] + "..." if len(val) > 40 else val
            lines.append(f"    {key}={display}")
    if len(lines) == 1:
        lines.append("    (nenhuma variável NYX/OPENAI/OLLAMA definida)")
    return "\n".join(lines)


@nyx_command(name="doctor", description="Diagnóstico do sistema", aliases=["dr"], category="sistema")
def cmd_doctor(_args: str, project_root: str) -> str:
    checks: list[str] = []

    try:
        import httpx

        r = httpx.get(f"{_OLLAMA_URL}/api/version", timeout=5)
        ver = r.json().get("version", "?")
        checks.append(f"[OK] Ollama: v{ver} (porta {_OLLAMA_PORT})")
    except Exception as e:
        logger.debug("Ollama health check falhou: %s", e)
        checks.append(f"[ERRO] Ollama: não responde na porta {_OLLAMA_PORT}")

    try:
        import httpx

        r = httpx.get(f"{_PROXY_V1_URL}/models", timeout=5)
        models = r.json().get("data", [])
        checks.append(f"[OK] Proxy: {len(models)} modelo(s) (porta {_PROXY_PORT})")
    except Exception as e:
        logger.debug("Proxy health check falhou: %s", e)
        checks.append(f"[ERRO] Proxy: não responde na porta {_PROXY_PORT}")

    try:
        out = subprocess.check_output(
            ["nvidia-smi", "--query-gpu=name,memory.used,memory.total", "--format=csv,noheader,nounits"],
            text=True,
            timeout=5,
        ).strip()
        parts = out.split(",")
        gpu = parts[0].strip()
        used = parts[1].strip()
        total = parts[2].strip()
        checks.append(f"[OK] GPU: {gpu} ({used}/{total} MiB)")
    except Exception as e:
        logger.debug("nvidia-smi indisponível: %s", e)
        checks.append("[AVISO] GPU: nvidia-smi indisponível")

    root = Path(project_root)
    checks.append(f"[OK] Projeto: {root.name}" if root.exists() else f"[ERRO] Projeto: {root} não existe")

    venv = root / "venv"
    checks.append(f"[OK] Venv: {venv}" if venv.exists() else "[AVISO] Venv: não encontrado")

    env = root / ".env"
    checks.append("[OK] .env: presente" if env.exists() else "[AVISO] .env: não encontrado")

    return "Diagnóstico Nyx:\n" + "\n".join(f"  {c}" for c in checks)


@nyx_command(name="version", description="Mostra versão do Nyx", category="projeto", aliases=["v"])
def cmd_version(_args: str, _root: str) -> str:
    from nyx.__version__ import __version__

    model = os.environ.get("OPENAI_MODEL", os.environ.get("NYX_MODEL", _DEFAULT_MODEL))
    proxy = os.environ.get("OPENAI_BASE_URL", _PROXY_V1_URL)
    return (
        f"  Nyx v{__version__}\n"
        f"  Modelo: {model}\n"
        f"  Proxy: {proxy}\n"
        f"  Python: {sys.version.split()[0]}\n"
        f"  Local First. Zero Emojis."
    )


@nyx_command(name="model", description="Mostra ou troca o modelo", aliases=["m"], category="sistema")
def cmd_model(model_name: str, _root: str) -> str:
    if not model_name.strip():
        current = os.environ.get("OPENAI_MODEL", os.environ.get("NYX_MODEL", _DEFAULT_MODEL))
        return f"  Modelo atual: {current}\n  Use /model <nome> para trocar."
    return f"__model__{model_name.strip()}"


@nyx_command(name="theme", description="Lista ou troca tema de cores", category="sistema")
def cmd_theme(args: str, _root: str) -> str:
    try:
        from nyx.themes import ThemeManager

        tm = ThemeManager()
        args = args.strip()
        if not args or args == "list":
            temas = tm.list_themes()
            lines = ["  Temas disponíveis:"]
            for t in temas:
                tid = t.get("id", "?")
                tname = t.get("name", tid)
                tdesc = t.get("description", "").strip()
                if tdesc:
                    lines.append(f"    - {tid}: {tname} — {tdesc}")
                else:
                    lines.append(f"    - {tid}: {tname}")
            return "\n".join(lines)
        ids_validos = {t["id"] for t in tm.list_themes()}
        if args not in ids_validos:
            return (
                f"__error__Tema '{args}' não existe no ThemeManager."
                "||Liste os temas disponíveis com /theme list."
            )
        theme = tm.load_theme(args)
        return f"  Tema '{args}' carregado. Primary: {theme.get('primary', '?')}"
    except ImportError as exc:
        return (
            f"__error__Módulo de temas indisponível: {type(exc).__name__}."
            "||Reinstale dependências com: ./run.sh --install"
        )


@nyx_command(name="permissions", description="Mostra permissões por tool", aliases=["perms"], category="sistema")
def cmd_permissions(_args: str, _root: str) -> str:
    from nyx.agent.permissions import PermissionChecker

    pc = PermissionChecker()
    tools_by_level: dict[str, list[str]] = {}
    for tool in [
        "read_file",
        "write_file",
        "edit_file",
        "run_command",
        "glob",
        "search",
        "list_files",
        "done",
        "agent",
        "todo_write",
        "web_fetch",
        "web_search",
        "notebook_edit",
    ]:
        level = str(pc.check(tool))
        tools_by_level.setdefault(level, []).append(tool)

    lines = ["  Permissões por nível:"]
    for level, tools in sorted(tools_by_level.items()):
        lines.append(f"    [{level}]")
        for t in tools:
            lines.append(f"      - {t}")
    return "\n".join(lines)


@nyx_command(name="hooks", description="Lista hooks registrados", category="sistema")
def cmd_hooks(_args: str, _root: str) -> str:
    return (
        "  Hooks são registrados via ToolRegistry.\n"
        "  Tipos: pre (antes da tool), post (depois da tool)\n"
        "  Exemplo: path_guard bloqueia acesso a .env\n"
        "  Use /doctor para verificar estado do sistema."
    )


@nyx_command(name="init", description="Inicializa projeto Nyx", category="projeto")
def cmd_init(_args: str, project_root: str) -> str:
    nyx_dir = Path.home() / ".nyx"
    dirs = [nyx_dir, nyx_dir / "memory", nyx_dir / "sessions", nyx_dir / "logs", nyx_dir / "analytics"]
    created = []
    for d in dirs:
        if not d.exists():
            d.mkdir(parents=True, exist_ok=True)
            created.append(str(d.relative_to(Path.home())))
    if created:
        return "  Diretórios criados:\n" + "\n".join(f"    ~/{c}" for c in created)
    return "  Nyx já inicializado. Diretórios existem."


@nyx_command(name="add-dir", description="Adiciona diretório ao contexto do agent", category="projeto")
def cmd_add_dir(args: str, project_root: str) -> str:
    target = args.strip()
    if not target:
        return (
            "__error__Argumento obrigatório ausente em /add-dir."
            "||Uso correto: /add-dir <caminho relativo ao projeto>."
        )
    full = Path(project_root) / target
    if not full.is_dir():
        return (
            f"__error__Diretório '{target}' não existe em {project_root}."
            "||Confira o caminho com: ls -la ou tab-completion."
        )
    return (
        f"Adicione o diretório '{target}' ao seu contexto de trabalho.\n"
        f"Use list_files(path='{target}') para ver o conteúdo.\n"
        "Considere este diretório parte do projeto para análises futuras."
    )


@nyx_command(name="tune", description="Re-calcula num_gpu via VRAM atual", category="sistema")
def cmd_tune(_args: str, _root: str) -> str:
    """PROXY-NUMGPU-RUNTIME-01: dispara GET /admin/tune (loopback) e mostra
    o resultado em PT-BR. Útil quando a VRAM mudou durante a sessão (usuário
    fechou browser, abriu outro app) e o usuário quer re-tunar proativamente
    sem esperar OOM.
    """
    try:
        import httpx

        proxy_base = os.environ.get("OPENAI_BASE_URL", _PROXY_V1_URL).rstrip("/")
        # /v1/... vira raiz para /admin/tune; aceita ambas as formas.
        if proxy_base.endswith("/v1"):
            proxy_base = proxy_base[: -len("/v1")]
        url = f"{proxy_base}/admin/tune"
        r = httpx.get(url, timeout=20.0)
    except Exception as exc:
        logger.debug("/tune falhou ao contactar proxy: %s", exc)
        return (
            f"__error__Proxy não respondeu em /admin/tune: {type(exc).__name__}."
            "||Verifique se o proxy está rodando com /doctor."
        )

    if r.status_code != 200:
        return (
            f"__error__/admin/tune retornou HTTP {r.status_code}."
            "||Veja logs do proxy em logs/proxy.log para diagnóstico."
        )

    try:
        data = r.json()
    except ValueError as exc:
        return (
            f"__error__Resposta inválida do /admin/tune: {type(exc).__name__}."
            "||O proxy retornou conteúdo não-JSON; veja logs/proxy.log."
        )

    old = data.get("old_num_gpu", "?")
    new = data.get("new_num_gpu", "?")
    vram_free = data.get("vram_free_mb")
    changed = data.get("changed", False)
    oom_degraded = data.get("oom_degraded", False)

    vram_txt = f"{vram_free} MB" if vram_free is not None else "desconhecido"
    if oom_degraded:
        suggested = data.get("suggested", "?")
        return (
            f"  num_gpu: {old} (preservado por fail-safe OOM)\n"
            f"  VRAM livre: {vram_txt}\n"
            f"  Sugestão atual: {suggested} (não aplicada; reinicie o proxy para reativar GPU)"
        )

    estado = "alterado" if changed else "inalterado"
    return (
        f"  num_gpu: {old} -> {new} ({estado})\n"
        f"  VRAM livre: {vram_txt}"
    )


@nyx_command(name="break-cache", description="Limpa caches internos", category="debug")
def cmd_break_cache(_args: str, _root: str) -> str:
    sessions_dir = Path.home() / ".nyx" / "sessions"
    removed = 0
    if sessions_dir.exists():
        for f in sessions_dir.glob("session_*.json"):
            f.unlink()
            removed += 1
    return f"  Cache limpo. {removed} sessão(ões) removida(s)."


# "Configurar é legislar para si mesmo." -- Marcus Aurelius (paráfrase)
