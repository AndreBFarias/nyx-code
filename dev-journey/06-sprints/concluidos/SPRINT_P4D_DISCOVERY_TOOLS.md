## 0. SPEC (machine-readable)

```yaml
sprint:
  id: P4-D
  title: "Discovery -- REPL, ToolSearch, Skill, SendMessage"
  touches:
    - path: nyx/agent/tools/repl_tool.py
      reason: "Nova tool: REPL Python interativo"
    - path: nyx/agent/tools/tool_search.py
      reason: "Nova tool: busca tools por query"
    - path: nyx/agent/tools/skill_tool.py
      reason: "Nova tool: invoca skills locais"
    - path: nyx/agent/tools/send_message.py
      reason: "Nova tool: mensagem entre agentes"
    - path: nyx/agent/tools/registry.py
      reason: "Registrar 4 novas tools"
    - path: scripts/gauntlet/nyx_gauntlet.py
      reason: "4 testes novos"
  origin:
    primary: "openclaud/src/tools/REPLTool/"
    secondary: "openclaud/src/tools/ToolSearchTool/"
  tests:
    - cmd: "./run.sh --gauntlet --only p4_discovery"
      timeout: 60
  acceptance_criteria:
    - "REPLTool executa Python e retorna output"
    - "ToolSearchTool busca tools por nome/descrição"
    - "SkillTool invoca skills definidos em ~/.nyx/skills/"
    - "SendMessageTool envia mensagem para agent subprocess"
    - "Registry sobe para 31 tools (total pós-P4)"
```

---

# Sprint P4-D -- Discovery e Orquestração

**Status:** CONCLUIDA (header corrigido em MASTER-CLEANUP-02 2026-05-20; presença em concluidos/ implica CONCLUIDA conforme convenção do projeto)
**Data:** 2026-04-05
**Prioridade:** MÉDIA
**Tipo:** Port (TS -> Python)
**Dependências:** P4-B, P4-C
**Desbloqueia:** P5-A

---

## Implementação

### 1. REPLTool (`nyx/agent/tools/repl_tool.py`)
- Parâmetro: `code` (str), `language` (str, default "python")
- Executa via `subprocess` com timeout 30s
- Captura stdout + stderr
- Suporta Python e shell

### 2. ToolSearchTool (`nyx/agent/tools/tool_search.py`)
- Parâmetro: `query` (str)
- Busca por nome e descrição nas tools registradas
- Retorna lista de matches com nome + descrição
- Fuzzy match simples (substring case-insensitive)

### 3. SkillTool (`nyx/agent/tools/skill_tool.py`)
- Parâmetro: `skill_name` (str), `args` (str, opcional)
- Carrega skills de `~/.nyx/skills/*.py`
- Cada skill é um módulo Python com função `execute(args, project_root)`
- Retorna output do skill

### 4. SendMessageTool (`nyx/agent/tools/send_message.py`)
- Parâmetro: `to` (str), `content` (str)
- Envia mensagem para agent subprocess via headless protocol
- Resposta síncrona com timeout
- Simplificado: sem multi-agent real, apenas comunicação 1:1

### Testes Gauntlet

| ID | Nome | Validação |
|----|------|-----------|
| P4D-01 | REPLTool executa Python | `print(1+1)` retorna "2" |
| P4D-02 | ToolSearch encontra | Busca "file", verifica read_file na lista |
| P4D-03 | SkillTool interface | Tool importa e tem parâmetros corretos |
| P4D-04 | SendMessage interface | Tool importa e tem parâmetros corretos |

## Verificação

- [ ] 4 tools importam sem erro
- [ ] REPL executa código real
- [ ] ToolSearch retorna resultados relevantes
- [ ] Registry totaliza 31 tools
- [ ] 4 testes Gauntlet passando

---

*"A curiosidade é a mãe de toda descoberta." -- Sócrates*
