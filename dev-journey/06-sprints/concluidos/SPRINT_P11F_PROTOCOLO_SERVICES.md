## 0. SPEC (machine-readable)

```yaml
sprint:
  id: P11-F
  title: "Protocolo services -- mcp, lsp, api, vcr"
  touches:
    - path: nyx/agent/services/mcp_service.py
    - path: nyx/agent/services/lsp_service.py
    - path: nyx/agent/services/api_service.py
    - path: nyx/agent/services/vcr.py
  origin:
    primary: "openclaud/src/services/mcp/"
  tests:
    - cmd: "./run.sh --gauntlet --only p11_protocolo"
      timeout: 30
```

---

# Sprint P11-F -- Protocolo Services

**Status:** PENDENTE  **Tipo:** Port  **Deps:** P11-B

## Services

| Service | OpenClaude | Adaptação local |
|---------|-----------|----------------|
| mcp_service | mcp/ | Gerenciamento de MCP servers locais |
| lsp_service | lsp/ | Gerenciamento de LSP servers |
| api_service | api/ | API local para integração entre serviços |
| vcr | vcr.ts | Gravação/replay de sessões |

---

*"Protocolos são contratos entre máquinas." -- Vint Cerf*
