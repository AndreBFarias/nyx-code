## 0. SPEC (machine-readable)

```yaml
sprint:
  id: INFRA-01
  title: "Scaffold automático -- scripts/scaffold.py"
  touches:
    - path: scripts/scaffold.py
      reason: "Script que gera tool/command/service com registro e teste"
  tests:
    - cmd: "./run.sh --gauntlet --only infra"
      timeout: 30
  acceptance_criteria:
    - "scaffold.py tool gera arquivo + registro + teste"
    - "scaffold.py command gera handler + teste"
    - "scaffold.py service gera arquivo + teste"
    - "Tudo integrado automaticamente"
```

---

# Sprint INFRA-01 -- Scaffold automático

**Status:** CONCLUIDA (header corrigido em MASTER-CLEANUP-02 2026-05-20; presença em concluidos/ implica CONCLUIDA conforme convenção do projeto)
**Data:** 2026-04-05
**Prioridade:** CRITICA
**Tipo:** Infra
**Dependências:** --
**Desbloqueia:** P9, P10, P11

---

## Problema

Criar 98 componentes manualmente (3 arquivos por componente) gera retrabalho e risco. Precisamos de automação.

## Implementação

### `scripts/scaffold.py`

```bash
# Nova tool
python scripts/scaffold.py tool mcp_tool MCPTool "Protocolo MCP local" --params server_name:string,method:string

# Novo command
python scripts/scaffold.py command login "Gerencia autenticação local" --category auth --aliases l

# Novo service
python scripts/scaffold.py service analytics "Métricas locais de uso"
```

Cada comando:
1. Cria arquivo Python a partir de template
2. Registra no sistema (registry.py ou commands.py)
3. Adiciona teste stub na fase correspondente do Gauntlet
4. Exibe resumo do que foi criado

### Templates embutidos

- Tool: RegisteredTool com ToolDef, execute() retornando stub
- Command: @nyx_command com handler retornando info
- Service: Classe com __init__ e métodos padrão

## Verificação

- [ ] `python scripts/scaffold.py tool test_scaffold TestScaffold "teste"` cria arquivo
- [ ] Tool aparece no registry
- [ ] Teste aparece no Gauntlet
- [ ] `python scripts/scaffold.py --help` mostra uso
- [ ] Cleanup do teste após verificação

---

*"A preguiça é a mãe da invenção." -- Agatha Christie*
