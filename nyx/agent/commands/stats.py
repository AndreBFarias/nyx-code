"""Slash command /stats -- consome GET /admin/stats do proxy local (INFRA-OOM-STATS-CLI-01)."""

from __future__ import annotations

from nyx.agent.commands._registry import nyx_command
from nyx.config.defaults import PROXY_PORT, PROXY_URL

_CHAVES_OBRIGATORIAS = (
    "oom_recovery_count",
    "num_gpu_current",
    "num_gpu_initial",
    "oom_degraded",
)


@nyx_command(
    name="stats",
    description="Estado do proxy local: OOM recovery, num_gpu, degradação",
    category="debug",
    examples=["/stats"],
)
def cmd_stats_proxy(_args: str, _root: str) -> str:
    """Retorna snapshot do estado do proxy via GET /admin/stats.

    Erros (rede, HTTP, JSON, chave faltante) viram strings amigáveis;
    o REPL nunca crasha. Loopback-only no servidor (proxy.py).
    """
    try:
        import httpx  # noqa: PLC0415
    except ImportError:
        return "[stats] dependência httpx ausente"

    url = f"{PROXY_URL}/admin/stats"
    try:
        r = httpx.get(url, timeout=2.0)
    except (httpx.ConnectError, httpx.TimeoutException):
        return f"[stats] proxy offline (porta {PROXY_PORT} não responde)"
    except httpx.RequestError as exc:
        return f"[stats] proxy inacessível: {type(exc).__name__}"
    except Exception as exc:  # pragma: no cover -- defensivo
        return f"[stats] erro inesperado: {type(exc).__name__}"

    if r.status_code >= 400:
        return f"[stats] proxy retornou erro {r.status_code}"

    try:
        data = r.json()
    except Exception:
        return "[stats] proxy resposta inválida"

    if not isinstance(data, dict) or not all(k in data for k in _CHAVES_OBRIGATORIAS):
        return "[stats] proxy resposta inválida"

    degraded_str = "sim" if data["oom_degraded"] else "não"
    return (
        "[stats]\n"
        f"OOM recovery count: {data['oom_recovery_count']}\n"
        f"num_gpu atual: {data['num_gpu_current']} (inicial: {data['num_gpu_initial']})\n"
        f"degraded: {degraded_str}"
    )


# "Observar o estado é metade de manter o sistema vivo." -- INFRA-OOM-STATS-CLI-01
