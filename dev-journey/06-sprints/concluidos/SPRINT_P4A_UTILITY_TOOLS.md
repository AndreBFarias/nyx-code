## 0. SPEC (machine-readable)

```yaml
sprint:
  id: P4-A
  title: "Utility Tools -- Sleep, Config, Brief"
  touches:
    - path: nyx/agent/tools/sleep_tool.py
      reason: "Nova tool: espera controlada"
    - path: nyx/agent/tools/config_tool.py
      reason: "Nova tool: lê/escreve configuração"
    - path: nyx/agent/tools/brief_tool.py
      reason: "Nova tool: gera resumo do contexto"
    - path: nyx/agent/tools/registry.py
      reason: "Registrar 3 novas tools"
    - path: scripts/gauntlet/nyx_gauntlet.py
      reason: "3 testes novos"
  origin:
    primary: "openclaud/src/tools/SleepTool/"
    secondary: "openclaud/src/tools/ConfigTool/"
    tertiary: "openclaud/src/tools/BriefTool/"
  tests:
    - cmd: "./run.sh --gauntlet --only p4_utility"
      timeout: 30
  acceptance_criteria:
    - "SleepTool espera N segundos (max 30)"
    - "ConfigTool lê e escreve .nyx/config.json"
    - "BriefTool gera resumo do contexto atual do agent"
    - "Registry sobe para 22 tools"
```

---

# Sprint P4-A -- Utility Tools

**Status:** CONCLUIDA (header corrigido em MASTER-CLEANUP-02 2026-05-20; presença em concluidos/ implica CONCLUIDA conforme convenção do projeto)
**Data:** 2026-04-05
**Prioridade:** MÉDIA
**Tipo:** Port (TS -> Python)
**Dependências:** P3-D
**Desbloqueia:** P4-B, P4-C

---

## Implementação

### 1. SleepTool (`nyx/agent/tools/sleep_tool.py`)
- Parâmetro: `seconds` (int, max 30)
- Usa `time.sleep()` com cap de segurança
- Retorna "Esperou Xs"

### 2. ConfigTool (`nyx/agent/tools/config_tool.py`)
- Parâmetros: `action` (get/set/list), `key`, `value`
- Persiste em `~/.nyx/config.json`
- get: retorna valor da chave
- set: define chave=valor
- list: retorna todas as chaves

### 3. BriefTool (`nyx/agent/tools/brief_tool.py`)
- Parâmetro: nenhum (usa contexto interno)
- Gera resumo: modelo, tools, arquivos lidos/modificados, iterações
- Retorna string formatada

### Testes Gauntlet

| ID | Nome | Validação |
|----|------|-----------|
| P4U-01 | SleepTool funciona | Espera 1s, verifica tempo real >= 1s |
| P4U-02 | ConfigTool set+get | Define chave, lê de volta, compara |
| P4U-03 | BriefTool gera resumo | Resumo contém "tools" e "modelo" |

## Verificação

- [ ] 3 tools importam sem erro
- [ ] Registry tem 22 tools
- [ ] 3 testes Gauntlet passando
- [ ] `./run.sh --gauntlet --only p4_utility` passa 100%

---

*"As pequenas coisas não são pequenas." -- Séneca*
