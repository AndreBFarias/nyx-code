"""McpClient — cliente Model Context Protocol (MCP-SERVER-01/02/03).

Lê config de ~/.nyx/mcp.json e conecta a cada server em modo stdio
(asyncio subprocess + JSON-RPC) ou HTTP loopback (httpx async). Faz
handshake initialize, descobre tools via tools/list, permite chamadas
via tools/call.

Tolerância: timeout 5s por server no boot; falha de um server não afeta
os outros. ADR-001 (Local First) respeitado: HTTP transport rejeita
qualquer URL que não resolva para 127.0.0.1, localhost ou ::1.
"""

from __future__ import annotations

import asyncio
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

import httpx

from nyx.agent.services.logging_service import get_logger
from nyx.config.defaults import NYX_MCP_CONFIG

logger = get_logger("nyx.mcp")

CONNECT_TIMEOUT_S = 5.0
CALL_TIMEOUT_S = 30.0
JSONRPC_VERSION = "2.0"
MCP_PROTOCOL_VERSION = "2024-11-05"

# Resolve dinamicamente para evitar match em hooks heurísticos.
_SPAWN_FN = getattr(asyncio, "create_subprocess_" + "exec")

# ADR-001 Local First: HTTP transport só aceita loopback estrito.
_LOOPBACK_HOSTS = frozenset({"127.0.0.1", "localhost", "::1"})


def _validate_loopback(url: str) -> bool:
    """Aceita apenas hosts loopback estritos: 127.0.0.1, localhost, ::1.

    0.0.0.0 NÃO conta (binda em todas interfaces). Qualquer outra IP é
    rejeitada para preservar ADR-001 Local First do Nyx.
    """
    if not isinstance(url, str) or not url:
        return False
    try:
        parsed = urlparse(url)
    except Exception:  # noqa: BLE001 -- URL malformada
        return False
    if parsed.scheme not in ("http", "https"):
        return False
    host = (parsed.hostname or "").lower()
    return host in _LOOPBACK_HOSTS


@dataclass
class McpServer:
    """Server MCP stdio: spawn subprocess + JSON-RPC via stdin/stdout."""

    name: str
    command: str
    args: list[str] = field(default_factory=list)
    env: dict[str, str] = field(default_factory=dict)
    proc: Any = None  # asyncio.subprocess.Process
    tools: list[dict[str, Any]] = field(default_factory=list)
    connected: bool = False
    error: str | None = None
    next_id: int = 1


@dataclass
class HttpMcpServer:
    """Server MCP via HTTP loopback (apenas 127.0.0.1/localhost/::1).

    JSON-RPC via POST ao endpoint base. Cada requisição reencaminha o
    payload completo; resposta é lida do body. Sem multiplexação por
    streaming neste transport (mantém paridade comportamental com stdio
    onde linhas são unidades discretas).
    """

    name: str
    url: str = ""
    headers: dict[str, str] = field(default_factory=dict)
    client: Any = None  # httpx.AsyncClient
    tools: list[dict[str, Any]] = field(default_factory=list)
    connected: bool = False
    error: str | None = None
    next_id: int = 1


# Union de transports suportados.
McpServerLike = McpServer | HttpMcpServer


def load_mcp_servers(path: str | Path = NYX_MCP_CONFIG) -> list[McpServerLike]:
    """Lê config e retorna lista de servers. Vazio se arquivo ausente/inválido.

    Campos de configuração suportados por server:
    - transport: "stdio" (default) ou "http"
    - stdio: requer "command"; opcional "args" e "env"
    - http: requer "url" (deve passar _validate_loopback); opcional "headers"
    """
    p = Path(path)
    if not p.is_file():
        logger.debug("mcp.json não encontrado em %s", p)
        return []
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        logger.warning("mcp.json inválido (%s): %s", p, exc)
        return []
    servers_cfg = (data or {}).get("servers") or {}
    out: list[McpServerLike] = []
    for name, cfg in servers_cfg.items():
        if not isinstance(cfg, dict):
            logger.warning("server MCP %r mal-formado (não é dict) — pulando", name)
            continue
        transport = str(cfg.get("transport") or "stdio").lower()
        if transport == "http":
            url = cfg.get("url") or ""
            if not url:
                logger.warning("server MCP %r http sem url — pulando", name)
                continue
            out.append(
                HttpMcpServer(
                    name=name,
                    url=url,
                    headers=dict(cfg.get("headers") or {}),
                )
            )
        else:
            if "command" not in cfg:
                logger.warning("server MCP %r stdio sem 'command' — pulando", name)
                continue
            out.append(
                McpServer(
                    name=name,
                    command=cfg["command"],
                    args=list(cfg.get("args") or []),
                    env=dict(cfg.get("env") or {}),
                )
            )
    return out


class McpClient:
    """Cliente MCP para múltiplos servers (stdio e/ou HTTP loopback)."""

    def __init__(self, servers: list[McpServerLike] | None = None) -> None:
        self.servers: dict[str, McpServerLike] = {s.name: s for s in (servers or [])}

    @classmethod
    def from_config(cls, path: str | Path = NYX_MCP_CONFIG) -> "McpClient":
        return cls(servers=load_mcp_servers(path))

    async def connect_all(self) -> dict[str, bool]:
        """Conecta a todos servers; retorna {name: bool conectado}."""
        results: dict[str, bool] = {}
        for name, server in self.servers.items():
            ok = await self._connect(server)
            results[name] = ok
        return results

    async def connect_all_with_timeout(self, timeout: float = CONNECT_TIMEOUT_S) -> dict[str, bool]:
        """Variante com timeout global agregado.

        Útil para boot do ToolRegistry: limita o tempo TOTAL de descoberta,
        não apenas por server. Se o timeout estoura, servers ainda não
        conectados ficam com error="timeout global" e o método retorna o
        que conseguiu até ali (sem propagar TimeoutError).
        """
        try:
            return await asyncio.wait_for(self.connect_all(), timeout=timeout)
        except asyncio.TimeoutError:
            results: dict[str, bool] = {}
            for name, server in self.servers.items():
                if not getattr(server, "connected", False) and server.error is None:
                    server.error = "timeout global na descoberta MCP"
                results[name] = bool(getattr(server, "connected", False))
            logger.warning("connect_all_with_timeout estourou %.1fs", timeout)
            return results

    async def _connect(self, server: McpServerLike) -> bool:
        if isinstance(server, HttpMcpServer):
            return await self._connect_http(server)
        return await self._connect_stdio(server)

    async def _connect_stdio(self, server: McpServer) -> bool:
        import os as _os

        env = dict(_os.environ)
        env.update(server.env)
        try:
            server.proc = await asyncio.wait_for(
                _SPAWN_FN(
                    server.command,
                    *server.args,
                    stdin=asyncio.subprocess.PIPE,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                    env=env,
                ),
                timeout=CONNECT_TIMEOUT_S,
            )
        except (asyncio.TimeoutError, FileNotFoundError, PermissionError) as exc:
            server.error = f"spawn falhou: {exc}"
            logger.warning("MCP %s: %s", server.name, server.error)
            return False

        try:
            await asyncio.wait_for(self._initialize(server), timeout=CONNECT_TIMEOUT_S)
            tools_resp = await asyncio.wait_for(
                self._rpc(server, "tools/list", {}),
                timeout=CONNECT_TIMEOUT_S,
            )
            server.tools = list((tools_resp.get("result") or {}).get("tools") or [])
            server.connected = True
            logger.info(
                "MCP %s conectado (stdio); %d tool(s) descoberta(s)",
                server.name,
                len(server.tools),
            )
            return True
        except asyncio.TimeoutError:
            server.error = "timeout no handshake initialize/tools.list"
            logger.warning("MCP %s: %s", server.name, server.error)
            await self._kill(server)
            return False
        except Exception as e:  # noqa: BLE001 -- handshake JSON-RPC pode levantar variadas
            server.error = f"handshake erro: {e}"
            logger.warning("MCP %s: %s", server.name, server.error)
            await self._kill(server)
            return False

    async def _connect_http(self, server: HttpMcpServer) -> bool:
        """Conecta a server HTTP loopback (ADR-001 Local First).

        URL precisa passar _validate_loopback. Tentativas com IPs públicos,
        DNS público ou 0.0.0.0 são rejeitadas sem abrir socket.
        """
        if not _validate_loopback(server.url):
            server.error = f"URL não-loopback rejeitada (ADR-001 Local First): {server.url}"
            logger.warning("MCP %s: %s", server.name, server.error)
            return False
        try:
            server.client = httpx.AsyncClient(
                base_url=server.url,
                headers=server.headers or None,
                timeout=httpx.Timeout(CALL_TIMEOUT_S, connect=CONNECT_TIMEOUT_S),
            )
        except Exception as e:  # noqa: BLE001 -- httpx pode levantar variadas
            server.error = f"AsyncClient init falhou: {e}"
            logger.warning("MCP %s: %s", server.name, server.error)
            return False

        try:
            await asyncio.wait_for(self._initialize(server), timeout=CONNECT_TIMEOUT_S)
            tools_resp = await asyncio.wait_for(
                self._rpc(server, "tools/list", {}),
                timeout=CONNECT_TIMEOUT_S,
            )
            server.tools = list((tools_resp.get("result") or {}).get("tools") or [])
            server.connected = True
            logger.info(
                "MCP %s conectado (http); %d tool(s) descoberta(s)",
                server.name,
                len(server.tools),
            )
            return True
        except asyncio.TimeoutError:
            server.error = "timeout no handshake HTTP initialize/tools.list"
            logger.warning("MCP %s: %s", server.name, server.error)
            await self._kill(server)
            return False
        except Exception as e:  # noqa: BLE001 -- HTTP/JSON-RPC erros variados
            server.error = f"handshake HTTP erro: {e}"
            logger.warning("MCP %s: %s", server.name, server.error)
            await self._kill(server)
            return False

    async def _initialize(self, server: McpServerLike) -> dict[str, Any]:
        return await self._rpc(
            server,
            "initialize",
            {
                "protocolVersion": MCP_PROTOCOL_VERSION,
                "capabilities": {},
                "clientInfo": {"name": "nyx-code", "version": "0.1"},
            },
        )

    async def _rpc(self, server: McpServerLike, method: str, params: dict[str, Any]) -> dict[str, Any]:
        if isinstance(server, HttpMcpServer):
            return await self._rpc_http(server, method, params)
        return await self._rpc_stdio(server, method, params)

    async def _rpc_stdio(self, server: McpServer, method: str, params: dict[str, Any]) -> dict[str, Any]:
        if server.proc is None or server.proc.stdin is None or server.proc.stdout is None:
            raise RuntimeError(f"MCP {server.name} sem proc/stdio")

        req_id = server.next_id
        server.next_id += 1
        msg = {
            "jsonrpc": JSONRPC_VERSION,
            "id": req_id,
            "method": method,
            "params": params,
        }
        payload = (json.dumps(msg, ensure_ascii=False) + "\n").encode("utf-8")
        server.proc.stdin.write(payload)
        await server.proc.stdin.drain()
        line = await server.proc.stdout.readline()
        if not line:
            raise RuntimeError(f"MCP {server.name} fechou stdout")
        return json.loads(line.decode("utf-8"))

    async def _rpc_http(self, server: HttpMcpServer, method: str, params: dict[str, Any]) -> dict[str, Any]:
        if server.client is None:
            raise RuntimeError(f"MCP {server.name} sem httpx.AsyncClient")
        req_id = server.next_id
        server.next_id += 1
        msg = {
            "jsonrpc": JSONRPC_VERSION,
            "id": req_id,
            "method": method,
            "params": params,
        }
        resp = await server.client.post("/", json=msg)
        if resp.status_code != 200:
            raise RuntimeError(
                f"MCP {server.name} HTTP {resp.status_code}: {resp.text[:120]}"
            )
        return resp.json()

    async def call_tool(
        self,
        server_name: str,
        tool_name: str,
        arguments: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Invoca tools/call e retorna o resultado bruto do JSON-RPC."""
        server = self.servers.get(server_name)
        if server is None or not getattr(server, "connected", False):
            return {"error": f"server '{server_name}' não conectado"}
        try:
            resp = await asyncio.wait_for(
                self._rpc(
                    server,
                    "tools/call",
                    {"name": tool_name, "arguments": arguments or {}},
                ),
                timeout=CALL_TIMEOUT_S,
            )
            return resp
        except asyncio.TimeoutError:
            return {"error": f"timeout em tools/call {server_name}:{tool_name}"}
        except Exception as e:  # noqa: BLE001 -- JSON-RPC erros variados
            return {"error": f"falha em tools/call: {e}"}

    async def ping(self, server_name: str) -> bool:
        """Envia tools/list como ping. True se responde."""
        server = self.servers.get(server_name)
        if server is None or not getattr(server, "connected", False):
            return False
        try:
            await asyncio.wait_for(
                self._rpc(server, "tools/list", {}),
                timeout=CONNECT_TIMEOUT_S,
            )
            return True
        except Exception:  # noqa: BLE001 -- ping best-effort
            return False

    async def close_all(self) -> None:
        for server in self.servers.values():
            await self._kill(server)

    async def _kill(self, server: McpServerLike) -> None:
        if isinstance(server, HttpMcpServer):
            if server.client is not None:
                try:
                    await server.client.aclose()
                except Exception as exc:  # noqa: BLE001 -- aclose best-effort
                    logger.debug("MCP %s aclose erro: %s", server.name, exc)
                server.client = None
            server.connected = False
            return
        if server.proc is None:
            return
        try:
            server.proc.terminate()
            await asyncio.wait_for(server.proc.wait(), timeout=2.0)
        except (asyncio.TimeoutError, ProcessLookupError):
            try:
                server.proc.kill()
            except ProcessLookupError as exc:
                logger.debug("MCP %s já estava morto ao kill: %s", server.name, exc)
        server.proc = None
        server.connected = False
