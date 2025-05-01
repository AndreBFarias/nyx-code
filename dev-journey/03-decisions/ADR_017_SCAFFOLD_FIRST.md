# ADR-017: Scaffold-first

**Data:** 2026-04-05
**Status:** Aceita
**Contexto:** Prevenir código solto e garantir integração automática

---

## Decisão

Antes de implementar qualquer tool, command ou service, usar `scripts/scaffold.py` para gerar o esqueleto. O scaffold cria o arquivo, registra no sistema, e adiciona o teste no Gauntlet -- tudo em um comando.

## Motivo

Criar 98 componentes manualmente (editar 3 arquivos por componente) gera retrabalho e risco de esquecer registro ou teste. O scaffold automatiza isso.

## Uso

```bash
# Nova tool
python scripts/scaffold.py tool mcp_tool MCPTool "Protocolo MCP local"

# Novo command
python scripts/scaffold.py command login "Gerencia autenticação local" --category auth

# Novo service
python scripts/scaffold.py service analytics "Métricas locais de uso"
```

## O que o scaffold gera

**Tool:**
1. `nyx/agent/tools/{nome}.py` -- arquivo com classe e ToolDef
2. Adiciona import + registro em `nyx/agent/tools/registry.py`
3. Adiciona teste interface na fase correspondente do Gauntlet

**Command:**
1. Adiciona `@nyx_command` em `nyx/agent/commands.py`
2. Adiciona teste no Gauntlet

**Service:**
1. `nyx/agent/services/{nome}.py` -- arquivo com classe
2. Adiciona teste de import no Gauntlet

## Regra

Nenhum componente novo deve ser criado manualmente. Se o scaffold não suporta o caso, expandir o scaffold primeiro.

---

*"Automatizar o trivial libera para o importante." -- Larry Wall*
