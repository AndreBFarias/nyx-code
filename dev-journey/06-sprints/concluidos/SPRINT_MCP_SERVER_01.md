# SPRINT MCP-SERVER-01 — Suporte ao Model Context Protocol (cliente)

## 0. SPEC (machine-readable)

```yaml
sprint:
  id: MCP-SERVER-01
  title: "Nyx atua como cliente MCP: descobre tools e prompts de servidores MCP locais (stdio) e os disponibiliza no ToolRegistry"
  onda: 23
  bloco: 23.5 Feature parity Claude Code
  prioridade: ALTA
  tipo: Feature
  dependencias: [PERF-INFERENCE-01]
  desbloqueia: [PLUGINS-01]
  origem: "Auditoria estratégica 2026-05-16 — gap real vs Claude Code: zero ocorrências de 'mcp' em nyx/. Meta de release v1.0 (Claude Code offline) inviável sem MCP."

  touches:
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/agent/tools/registry.py
      reason: "ToolRegistry recebe lista de tools MCP no boot e os mescla com tools nativas"
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/config/defaults.py
      reason: "NYX_MCP_CONFIG = ~/.nyx/mcp.json (fonte única do path)"
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/config/settings.py
      reason: "Carrega mcp.json se existir; expõe lista de servers para registry"

  creates:
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/agent/services/mcp_client.py
      reason: "Cliente MCP via stdio (JSON-RPC). Suporta initialize, list_tools, call_tool. Async."
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/agent/commands/mcp.py
      reason: "Slash commands: /mcp list, /mcp reload, /mcp test <name>"
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/dev-journey/03-decisions/ADR_030_MCP.md
      reason: "Decisão: Nyx como cliente MCP, stdio prioritário, Local First respeitado"

  removes: []

  n_to_n_pairs:
    - descricao: "Path NYX_MCP_CONFIG aparece em defaults.py + mcp_client.py + commands/mcp.py"
      paths:
        - /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/config/defaults.py
        - /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/agent/services/mcp_client.py
        - /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/agent/commands/mcp.py

  forbidden:
    - "MCP via HTTP remoto (sem servidor cloud — ADR-001 Local First). Stdio prioritário; HTTP SOMENTE 127.0.0.1"
    - "Auto-execução de tool MCP sem passar pelo PermissionChecker"
    - "Carregar tool MCP que tem nome igual a tool nativa sem namespace (conflito silencioso)"
    - "Bloquear boot por timeout em server MCP morto (graceful skip + warning)"
    - "Emoji, menção a IA"

  tests:
    - cmd: "test -f nyx/agent/services/mcp_client.py && ./venv/bin/python -c 'from nyx.agent.services.mcp_client import McpClient; print(McpClient)'"
      timeout: 30
      deve_passar: true
    - cmd: "./run.sh --gauntlet --only rapido"
      timeout: 300
      deve_passar: true
    - cmd: "NYX_MCP_CONFIG=/tmp/test_mcp_inexistente.json ./run.sh --smoke"
      timeout: 60
      deve_passar: true
      nota: "Boot tolera ausência de mcp.json sem crashar"
    - cmd: "bash scripts/sprint_invariants.sh"
      timeout: 60
      deve_passar: "FAIL_AFTER <= FAIL_BEFORE"

  acceptance_criteria:
    - "~/.nyx/mcp.json define servers (schema: {servers: {<name>: {command, args, env}}})"
    - "McpClient async: connect via stdio (usa asyncio subprocess primitives), initialize, list_tools, call_tool"
    - "ToolRegistry no boot: lista MCP tools com prefixo 'mcp_<server>_<tool>' (namespace)"
    - "Boot tolera server MCP morto/timeout (5s timeout por server, warning, segue)"
    - "PermissionChecker valida tool MCP antes de call_tool (mesma política de tools nativas)"
    - "/mcp list mostra servers e tools descobertas"
    - "/mcp reload re-conecta servers sem restart do Nyx"
    - "/mcp test <name> ping no server"
    - "ADR-030 criado documentando: stdio prioritário, namespace mcp_<server>_<tool>, política de permissões"
    - "Tool MCP aparece no Gauntlet --only tools-mcp (nova fase, opcional na primeira release)"
    - "PT-BR; zero emoji; zero menção a IA"
```

---

**Status:** CONCLUIDA (header corrigido em MASTER-CLEANUP-02 2026-05-20; presença em concluidos/ implica CONCLUIDA conforme convenção do projeto)
**Data criação:** 2026-05-16
**Modelo obrigatório:** claude-opus-4-7 (sem subagentes)

---

# Sprint MCP-SERVER-01

## Contexto

MCP (Model Context Protocol) é o protocolo da Anthropic para permitir agentes (Claude Code, Cursor, etc.) consumirem tools/prompts/resources de servidores externos via JSON-RPC stdio ou SSE. Claude Code suporta MCP nativamente; sem isso, Nyx perde o ecossistema de servidores MCP (filesystem extra, git, postgres, etc.).

ADR-001 (Local First) restringe: aceitar APENAS servers locais (stdio) ou HTTP em 127.0.0.1. Sem cloud.

## Solução conceitual (pseudo-código)

### `nyx/agent/services/mcp_client.py` (esqueleto)

```
class McpClient:
    - lista de McpServer (name, command, args, env, handle do processo filho)
    - método async connect_all: para cada server, usa asyncio.create_subprocess_*
      primitives para spawn como pipe stdio, envia handshake initialize
    - método async list_tools(server): JSON-RPC tools/list
    - método async call_tool(server, name, args): JSON-RPC tools/call
    - error path: timeout 5s por server no boot; warning + skip se falha
```

Detalhes de implementação ficam para o executor; o ponto é: cliente JSON-RPC pure-Python (sem dependência nova), respeitando timeouts e logger.warning em erro.

### Schema `~/.nyx/mcp.json` (exemplo)

```json
{
  "servers": {
    "filesystem": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-filesystem", "/home/user/projects"],
      "env": {}
    },
    "git": {
      "command": "python",
      "args": ["-m", "mcp_server_git"],
      "env": {"REPO_PATH": "/home/user/repo"}
    }
  }
}
```

### Integração no ToolRegistry (esqueleto)

```
discover_mcp_tools:
  client = McpClient(load_mcp_servers())
  await client.connect_all()
  para cada server conectado:
    tools = await client.list_tools(server)
    para cada tool:
      qualified_name = "mcp_" + server.name + "_" + tool.name
      registry.register(qualified_name, factory que chama call_tool)
```

## Verificação

```bash
# Sem mcp.json: boot normal, zero tool MCP
./run.sh --smoke

# Com mcp.json de exemplo: detecta tools
mkdir -p ~/.nyx
cat > ~/.nyx/mcp.json <<EOF
{"servers":{"everything":{"command":"npx","args":["-y","@modelcontextprotocol/server-everything"]}}}
EOF
./run.sh --smoke
# logs/nyx.log deve mostrar "MCP server everything conectado, N tools"

# /mcp list dentro do REPL
./run.sh
# nyx> /mcp list
# Esperado: lista de servers + tools
```

## Riscos

| Risco | Mitigação |
|---|---|
| MCP server malicioso consome FS | PermissionChecker valida call_tool antes de invocar |
| Stdio buffer enche em respostas longas | drain explícito + timeout por chamada (30s default) |
| Server demora a iniciar (npx pull pesado) | Timeout 5s por server no boot; warning + skip |
| MCP tool com mesmo nome de tool nativa | Namespace obrigatório: `mcp_<server>_<tool>` |
| Dependência nova (mcp python sdk) infla footprint | Implementar JSON-RPC stdio puro com asyncio nativo; zero deps novas |

---

*"Padrão aberto é a única forma de não-recompetir." -- princípio de ecossistema*
