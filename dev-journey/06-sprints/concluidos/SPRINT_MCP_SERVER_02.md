# SPRINT MCP-SERVER-02 — Integração ToolRegistry + HTTP loopback + Gauntlet (anti-débito)

## 0. SPEC (machine-readable)

```yaml
sprint:
  id: MCP-SERVER-02
  title: "Integrar tools MCP no ToolRegistry com namespace + HTTP loopback transport + fase Gauntlet dedicada"
  onda: 23
  bloco: 23.5 Feature parity
  prioridade: ALTA
  tipo: Feature
  dependencias: [MCP-SERVER-01]
  desbloqueia: []
  origem: "Anti-débito de MCP-SERVER-01 — MVP entregue (cliente + commands + ADR-030) mas integração ToolRegistry + HTTP transport ficaram fora do escopo do MVP."

  touches:
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/agent/tools/registry.py
      reason: "Discover tools MCP no boot e mesclar com tools nativas via prefixo mcp_<server>_<tool>"
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/agent/services/mcp_client.py
      reason: "Adicionar transport HTTP loopback (127.0.0.1) além de stdio"
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/scripts/gauntlet/nyx_gauntlet.py
      reason: "Fase 'mcp' com server de exemplo (echo trivial) testando descoberta + call_tool"

  creates: []
  removes: []

  forbidden:
    - "HTTP MCP fora de 127.0.0.1 (ADR-001 Local First; ADR-030)"
    - "Auto-invocar tool MCP sem passar pelo PermissionChecker"
    - "Tool MCP que colide nome com tool nativa sem prefixo namespace"

  acceptance_criteria:
    - "ToolRegistry no boot expõe tools MCP com prefixo mcp_<server>_<tool>"
    - "Conflito de nome entre MCP e nativa é resolvido por prefixo (nativa vence sem prefixo)"
    - "McpClient suporta HTTP loopback transport (validador rejeita non-127.0.0.1)"
    - "Fase Gauntlet 'mcp' com 3 testes: discovery, call_tool echo, ping após server morto"
    - "Smoke + invariants passam"
    - "PT-BR, zero emoji, zero menção a IA"

  tests:
    - cmd: "./run.sh --gauntlet --only mcp"
      timeout: 120
      deve_passar: true
    - cmd: "./run.sh --gauntlet --only rapido"
      timeout: 300
      deve_passar: true
```

---

**Status:** CONCLUIDA (header corrigido em MASTER-CLEANUP-02 2026-05-20; presença em concluidos/ implica CONCLUIDA conforme convenção do projeto)
**Data criação:** 2026-05-17
**Origem:** anti-débito de MCP-SERVER-01.
**Modelo obrigatório:** claude-opus-4-7 (sem subagentes)
