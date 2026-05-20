## 0. SPEC (machine-readable)

```yaml
sprint:
  id: P9-A
  title: "MCP + LSP Tools"
  touches:
    - path: nyx/agent/tools/mcp_tool.py
      reason: "MCPTool, McpAuthTool, ListMcpResourcesTool, ReadMcpResourceTool"
    - path: nyx/agent/tools/lsp_tool.py
      reason: "LSPTool -- Language Server Protocol"
    - path: nyx/agent/tools/registry.py
      reason: "Registrar 5 novas tools"
    - path: scripts/gauntlet/nyx_gauntlet.py
      reason: "5 testes novos"
  origin:
    primary: "openclaud/src/tools/MCPTool/"
    secondary: "openclaud/src/tools/LSPTool/"
  tests:
    - cmd: "./run.sh --gauntlet --only p9_mcp"
      timeout: 30
  acceptance_criteria:
    - "MCPTool implementa protocolo MCP local"
    - "LSPTool conecta a Language Servers"
    - "5 tools registradas e testadas"
```

---

# Sprint P9-A -- MCP + LSP Tools

**Status:** CONCLUIDA (header corrigido em MASTER-CLEANUP-02 2026-05-20; presença em concluidos/ implica CONCLUIDA conforme convenção do projeto)
**Data:** 2026-04-05
**Prioridade:** ALTA
**Tipo:** Port (TS -> Python)
**Dependências:** P8-B
**Desbloqueia:** --

---

## Implementação

### MCPTool (`nyx/agent/tools/mcp_tool.py`)
- Protocolo MCP adaptado para local-first
- Comunica com MCP servers locais via stdio
- Parâmetros: server_name, method, params
- Fallback: lista servers disponíveis se nenhum especificado

### McpAuthTool (mesmo arquivo)
- Autenticação para MCP servers que requerem
- Armazena tokens em ~/.nyx/mcp_auth.json

### ListMcpResourcesTool (mesmo arquivo)
- Lista recursos disponíveis no MCP server ativo

### ReadMcpResourceTool (mesmo arquivo)
- Lê recurso específico de um MCP server

### LSPTool (`nyx/agent/tools/lsp_tool.py`)
- Conecta a Language Servers (pylsp, tsserver, gopls)
- Operações: definition, references, completions, hover
- Auto-detecta server baseado no tipo de projeto

### Testes Gauntlet (fase: p9_mcp)

| ID | Nome | Validação |
|----|------|-----------|
| P9M-01 | MCPTool interface | Tool importa, parâmetros corretos |
| P9M-02 | McpAuth interface | Tool importa |
| P9M-03 | ListMcpResources interface | Tool importa |
| P9M-04 | ReadMcpResource interface | Tool importa |
| P9M-05 | LSPTool interface | Tool importa, parâmetros corretos |

---

*"Todo protocolo é uma promessa." -- David Clark*
