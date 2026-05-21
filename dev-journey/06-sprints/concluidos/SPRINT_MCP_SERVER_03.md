## 0. SPEC (machine-readable)

```yaml
sprint:
  id: MCP-SERVER-03
  title: "MCP integração ToolRegistry + HTTP loopback transport (fecha MCP-SERVER-02 CONCLUIDA_PARCIAL)"
  onda: 23
  bloco: "23.5 Feature parity"
  prioridade: ALTA
  tipo: Feature
  dependencias: [MCP-SERVER-02, ADR-030]
  desbloqueia: []

  touches:
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/agent/services/mcp_client.py
      reason: "Adicionar suporte HTTP loopback transport (httpx async); preservar stdio existente"
      linhas_alvo: "Adicionar HttpMcpServer dataclass + connect/call/close para transport HTTP"
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/agent/tools/registry.py
      reason: "Descoberta automática de tools MCP no boot do ToolRegistry com prefix mcp_<server>_<tool>"
      linhas_alvo: "Adicionar método _load_mcp_tools() chamado após _load_tools()"
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/scripts/gauntlet/nyx_gauntlet.py
      reason: "Adicionar fase mcp com testes para HTTP loopback transport + ToolRegistry integration"
      linhas_alvo: "fase mcp existente — adicionar M-04 (HTTP) + M-05 (registry)"

  creates: []
  removes: []

  n_to_n_pairs:
    - descricao: "Schema de config ~/.nyx/mcp.json suporta novos campos transport=http|stdio e url quando transport=http"
      paths: [nyx/agent/services/mcp_client.py]

  forbidden:
    - "Aceitar URLs não-loopback (não-127.0.0.1) em transport HTTP — viola ADR-001 Local First"
    - "Adicionar dependência nova ao requirements.txt (httpx já está)"
    - "Quebrar boot tolerante: server MCP com falha não pode derrubar Nyx"
    - "Bypassar PermissionChecker em tools MCP — devem seguir mesma política das nativas"
    - "Emoji ou menção a IA externa"

  tests:
    - cmd: "./run.sh --smoke"
      timeout: 10
      deve_passar: true
      assert: "boot ok"
    - cmd: "bash scripts/sprint_invariants.sh"
      timeout: 30
      deve_passar: true
      assert: "PASS=14 FAIL=0"
    - cmd: "python3 -c 'from nyx.agent.services.mcp_client import McpClient, load_mcp_servers; print(\"OK import\")'"
      timeout: 5
      deve_passar: true
    - cmd: "python3 -c 'from nyx.agent.tools.registry import ToolRegistry; r = ToolRegistry(\".\"); print(f\"tools={r.tool_count}\")'"
      timeout: 10
      deve_passar: true
      assert: "tool_count >= 35 (nativas; MCP zero se mcp.json ausente — comportamento tolerante)"
    - cmd: "./run.sh --gauntlet --only mcp"
      timeout: 60
      deve_passar: true
      assert: "100% APROVADO; pelo menos M-04 (HTTP) e M-05 (registry) novos"

  acceptance_criteria:
    - "mcp_client.py aceita config com transport=http + url=http://127.0.0.1:PORT (apenas loopback)"
    - "Tentativa de URL não-loopback rejeita com warning e marca server.error sem crash"
    - "ToolRegistry descobre tools MCP no boot com prefix mcp_<server>_<tool>"
    - "PermissionChecker valida call de tool MCP igual às nativas"
    - "Boot sem mcp.json continua tolerante (tool_count das nativas inalterado)"
    - "Fase mcp do gauntlet ganha M-04 e M-05; 100% APROVADO"
    - "Smoke + invariantes 14/14"
    - "Acentuação rc=0 nos arquivos tocados"
    - "MASTER linha 128 (MCP-SERVER-02 CONCLUIDA_PARCIAL) ganha nota de fechamento via MCP-SERVER-03; nova linha para MCP-SERVER-03 CONCLUIDA"
```

---

# Sprint MCP-SERVER-03 — Fechar MCP-SERVER-02 (Registry + HTTP loopback)

**Status:** PENDENTE
**Data criação:** 2026-05-21
**Modelo obrigatório:** claude-opus-4-7 (executor-sprint via Agent tool)

---

## Contexto

ADR-030 estabelece Nyx como cliente MCP. MCP-SERVER-01 implementou MVP (stdio JSON-RPC). MCP-SERVER-02 adicionou fase Gauntlet (3 testes) mas deixou 2 pendências:
1. **Integração ToolRegistry**: tools MCP descobertas pelo `/mcp list` NÃO entram no ToolRegistry — agente ainda não as invoca automaticamente
2. **HTTP loopback transport**: stdio é único modo; HTTP em 127.0.0.1 não implementado

Esta sprint fecha ambas.

## Solução técnica

### Parte 1: HTTP loopback transport

Em `nyx/agent/services/mcp_client.py`:

```python
import httpx

@dataclass
class HttpMcpServer(McpServer):
    """Server MCP via HTTP loopback (apenas 127.0.0.1)."""
    url: str = ""  # ex: "http://127.0.0.1:8765"
    client: Any = None  # httpx.AsyncClient


def _validate_loopback(url: str) -> bool:
    """Aceita apenas 127.0.0.1, localhost, ou ::1."""
    from urllib.parse import urlparse
    try:
        parsed = urlparse(url)
        host = parsed.hostname or ""
        return host in ("127.0.0.1", "localhost", "::1")
    except Exception:
        return False


# Em load_mcp_servers, novo campo "transport":
# - "stdio" (default) → McpServer existente
# - "http" → HttpMcpServer; valida url loopback

# Em McpClient.connect, branch por type(server):
async def _connect_http(self, server: HttpMcpServer) -> bool:
    if not _validate_loopback(server.url):
        server.error = f"URL não-loopback rejeitada: {server.url}"
        logger.warning(server.error)
        return False
    server.client = httpx.AsyncClient(base_url=server.url, timeout=CALL_TIMEOUT_S)
    # handshake initialize via POST /
    ...
```

### Parte 2: ToolRegistry integration

Em `nyx/agent/tools/registry.py`:

```python
class ToolRegistry:
    def __init__(self, project_root: str) -> None:
        # ... código existente
        self._load_tools()      # nativas
        self._load_mcp_tools()  # NOVO: descobre via mcp_client

    def _load_mcp_tools(self) -> None:
        """Descobre tools MCP e adiciona ao registry com prefix mcp_<server>_<tool>.

        Boot tolerante: falha de descoberta NÃO derruba o registry.
        """
        try:
            from nyx.agent.services.mcp_client import McpClient, load_mcp_servers
            servers = load_mcp_servers()
            if not servers:
                return
            # NOTA: descoberta síncrona via asyncio.run em construtor é OK
            # porque _load_mcp_tools roda 1x no boot, não em hot path
            import asyncio
            client = McpClient(servers)
            try:
                asyncio.run(client.connect_all_with_timeout(timeout=CONNECT_TIMEOUT_S))
            except Exception as e:
                logger.warning(f"MCP discovery falhou no boot: {e}")
                return
            for server in client.servers:
                if not server.connected:
                    continue
                for tool_def in server.tools:
                    tool_name = f"mcp_{server.name}_{tool_def['name']}"
                    # Criar McpToolAdapter que delega para client.call_tool
                    adapter = McpToolAdapter(client, server, tool_def, name=tool_name)
                    self._tools[tool_name] = adapter
        except Exception as e:
            logger.warning(f"_load_mcp_tools: falha não-fatal: {e}")


class McpToolAdapter(RegisteredTool):
    """Adapter que faz tool MCP parecer com RegisteredTool nativa."""

    def __init__(self, client, server, tool_def, name):
        self._client = client
        self._server = server
        self._tool_def_mcp = tool_def
        self.tool_def = ToolDef(
            name=name,
            description=tool_def.get("description", ""),
            parameters=tool_def.get("inputSchema", {}),
        )
        self.action_type = ActionType.MCP_TOOL  # nova entry no enum?

    def execute(self, params: dict, project_root: str) -> ActionResult:
        # Delega para mcp_client.call_tool via asyncio.run
        ...
```

### Parte 3: Gauntlet

Em `scripts/gauntlet/nyx_gauntlet.py`, fase mcp existente:
- M-04 (novo): testar HTTP loopback transport — criar mock server local httpx, validar handshake + tools/list
- M-05 (novo): testar ToolRegistry integration — popular `~/.nyx/mcp.json` com stub stdio, verificar `tool_count` aumentou + tool com prefix `mcp_*` presente

## Investigação inicial obrigatória

Antes de tocar código:

```bash
# Estado atual mcp_client
wc -l nyx/agent/services/mcp_client.py  # 226L atual
grep -n "HttpMcpServer\|_validate_loopback\|httpx" nyx/agent/services/mcp_client.py
# (esperado: nenhum match — HTTP ainda não implementado)

# Estado atual ToolRegistry
grep -n "_load_mcp_tools\|McpToolAdapter\|mcp_" nyx/agent/tools/registry.py
# (esperado: nenhum match — integração ausente)

# Verificar ActionType existente
grep -n "MCP_TOOL\|class ActionType\|ActionType\\." nyx/agent/models.py | head -10

# Fase mcp atual no gauntlet
grep -n "fase.*mcp\|_phase_mcp\|M-01\|M-02\|M-03" scripts/gauntlet/nyx_gauntlet.py | head -10
```

## Proof-of-work

```bash
bash scripts/sprint_invariants.sh > /tmp/inv_before_mcp.txt 2>&1
FAIL_BEFORE=$(grep -c "^\[FAIL\]" /tmp/inv_before_mcp.txt)
echo "FAIL inicial: $FAIL_BEFORE"  # 0 esperado

# IMPLEMENTAR

./run.sh --smoke
bash scripts/sprint_invariants.sh > /tmp/inv_after_mcp.txt 2>&1
FAIL_AFTER=$(grep -c "^\[FAIL\]" /tmp/inv_after_mcp.txt)
echo "FAIL final: $FAIL_AFTER"  # 0 esperado

# Asserto import mcp_client com HTTP
python3 -c 'from nyx.agent.services.mcp_client import McpClient, load_mcp_servers, HttpMcpServer, _validate_loopback; assert _validate_loopback("http://127.0.0.1:8765"); assert not _validate_loopback("http://192.168.1.1:8765"); print("OK HTTP loopback validation")'

# Asserto ToolRegistry integration
python3 -c 'from nyx.agent.tools.registry import ToolRegistry; r = ToolRegistry("."); print(f"tool_count={r.tool_count}")'
# esperado: >= 35 (zero MCP se mcp.json ausente; comportamento tolerante)

# Gauntlet fase mcp
./run.sh --gauntlet --only mcp 2>&1 | tail -10

# Acentuação
python3 ~/.config/zsh/scripts/validar-acentuacao.py --paths nyx/agent/services/mcp_client.py nyx/agent/tools/registry.py scripts/gauntlet/nyx_gauntlet.py
echo "rc=$?"
```

## Critério binário

- [ ] HTTP transport aceita 127.0.0.1; rejeita não-loopback com warning sem crash
- [ ] ToolRegistry descobre tools MCP com prefix `mcp_<server>_<tool>`
- [ ] Boot sem mcp.json continua tolerante (tool_count nativas inalterado)
- [ ] PermissionChecker valida MCP tools (mesma política)
- [ ] Fase mcp 100% APROVADO (M-01..M-05)
- [ ] Smoke + invariantes 14/14 + acentuação rc=0
- [ ] MASTER linha 128 ganha nota de fechamento + nova linha para MCP-SERVER-03

## Guardrails

- **#21 (sucesso forjado):** executor DEVE rodar `python3 -c '...HttpMcpServer...'` real, não dizer "passou".
- **HTTP non-loopback:** se executor permitir URL como `http://0.0.0.0`, viola ADR-001.
- **Boot regression:** se `_load_mcp_tools` derrubar o agente quando mcp.json ausente, é falha crítica.

## Riscos

| Risco | Mitigação |
|---|---|
| asyncio.run em construtor de ToolRegistry pode bloquear | Usar timeout curto (5s); fallback gracioso |
| httpx pode não estar em requirements (verificar) | `grep httpx requirements.txt` antes de adicionar import |
| McpToolAdapter precisa de ActionType nova | Verificar `nyx/agent/models.py` antes; reusar action_type existente OU adicionar `MCP_TOOL` |
| Tool MCP com mesmo nome que tool nativa | Prefix `mcp_<server>_<tool>` resolve; documentar |

---

*"Padrão aberto exige o tempo todo aberto." — ecossistema MCP*
