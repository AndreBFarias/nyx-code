# ADR-030 — Nyx como cliente MCP (Model Context Protocol) via stdio

**Status:** ACEITO
**Data:** 2026-05-17
**Contexto da Onda:** 23, Bloco 23.5 Feature parity, MCP-SERVER-01

## Contexto

MCP (Model Context Protocol) é o protocolo aberto para agentes consumirem
tools, prompts e resources de servidores externos via JSON-RPC stdio ou
SSE. Ecossistema de servers MCP cresce rápido (filesystem, git, postgres,
github, etc.) e a CLI de referência consome esse ecossistema nativamente.

Sem suporte MCP, o Nyx fica isolado do catálogo de extensões da
comunidade. Auditoria estratégica 2026-05-16 confirmou: zero ocorrências
de "mcp" em `nyx/` antes desta sprint.

ADR-001 (Local First) restringe: aceitar APENAS servers locais.

## Decisão

Nyx atua como **cliente MCP** via stdio (JSON-RPC sobre pipe). Servidores
remotos via HTTP só são aceitos se ligados a `127.0.0.1` (loopback);
cloud é proibido.

Implementação MVP (MCP-SERVER-01):

1. **`nyx/agent/services/mcp_client.py`** — `McpClient` async que lê
   `~/.nyx/mcp.json`, spawn cada server como subprocess pipe, executa
   handshake `initialize` + `tools/list`, e expõe `call_tool`/`ping`/
   `close_all`. Timeout de 5s por server no boot (`CONNECT_TIMEOUT_S`)
   e 30s por chamada (`CALL_TIMEOUT_S`).
2. **`nyx/agent/commands/mcp.py`** — slash commands `/mcp list`,
   `/mcp reload`, `/mcp test <name>` que delegam para sentinelas
   processadas em `cli.py` (precisam de event loop ativo).
3. **`nyx/config/defaults.py`** — `NYX_MCP_CONFIG` constante (fonte
   única do path), override via env var.

## Schema de configuração

`~/.nyx/mcp.json`:

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

Servers mal-formados (sem `command`) são pulados com warning. Server
que falha no spawn ou no handshake é marcado com `error` e NÃO bloqueia
boot — o fluxo continua para os demais.

## Tolerância e isolamento

- **Boot tolerante:** ausência de `~/.nyx/mcp.json` é normal; falha de
  spawn de um server não derruba os outros; cada timeout é local.
- **Permissões:** `PermissionChecker` valida `call_tool` antes da
  invocação (mesma política das tools nativas). Tools MCP NÃO bypassam
  o anel de permissão.
- **Namespace:** tools MCP devem aparecer no `ToolRegistry` (integração
  completa em MCP-SERVER-02) com prefixo `mcp_<server>_<tool>` para
  evitar conflito com tools nativas.
- **Sem deps novas:** implementação JSON-RPC puro com `asyncio` nativo;
  nenhuma dependência adicionada ao `requirements.txt`.

## Escopo desta sprint (MVP)

- [ok] McpClient async com connect/list/call/ping/close
- [ok] Slash commands /mcp list, /mcp reload, /mcp test
- [ok] Boot tolera ausência de mcp.json
- [ok] Permission gate explícito (call_tool roda só via cliente, não tool nativa)
- [pendente MCP-SERVER-02] Integração automática no ToolRegistry
- [pendente MCP-SERVER-02] HTTP loopback transport
- [pendente MCP-SERVER-02] Fase Gauntlet dedicada com server de exemplo

## Consequências

- **Positiva:** ecossistema MCP acessível offline (filesystem, git, etc.).
- **Positiva:** zero deps novas; footprint mantido.
- **Positiva:** isolamento por server (um morto não derruba outros).
- **Negativa:** integração com `ToolRegistry` fica para MCP-SERVER-02 —
  hoje as tools MCP são descobertas pelo `/mcp list` mas o agente
  ainda não as invoca automaticamente em response.
- **Negativa:** HTTP loopback transport não implementado neste MVP.

## Referências

- ADR-001 Local First.
- ADR-013 Integração Obrigatória.
- PERF-INFERENCE-01 (pré-requisito: model swap rápido).
- PLUGINS-01 (desbloqueado por esta sprint).

*"Padrão aberto é a única forma de não-recompetir." — princípio de ecossistema*
