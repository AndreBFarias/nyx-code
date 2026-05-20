## 0. SPEC (machine-readable)

```yaml
sprint:
  id: P8-A
  title: "Edição avançada -- Analyze, Patch, MultiEdit"
  touches:
    - path: nyx/agent/tools/analyze_tool.py
      reason: "Nova tool: análise de código"
    - path: nyx/agent/tools/patch_tool.py
      reason: "Nova tool: aplicação de patches unified diff"
    - path: nyx/agent/tools/multi_edit.py
      reason: "Nova tool: edição de múltiplos arquivos"
    - path: nyx/agent/tools/registry.py
      reason: "Registrar 3 novas tools"
    - path: scripts/gauntlet/nyx_gauntlet.py
      reason: "3 testes novos"
  origin:
    primary: "Luna/src/skills/code_agent/tools/analyze.py"
    secondary: "Luna/src/skills/code_agent/tools/patch.py"
    tertiary: "Luna/src/skills/code_agent/multi_edit.py"
  tests:
    - cmd: "./run.sh --gauntlet --only p8_edicao"
      timeout: 30
  acceptance_criteria:
    - "AnalyzeTool analisa estrutura de arquivo Python"
    - "PatchTool aplica unified diff"
    - "MultiEditTool edita múltiplos arquivos em uma chamada"
```

---

# Sprint P8-A -- Edição avançada

**Status:** CONCLUIDA (header corrigido em MASTER-CLEANUP-02 2026-05-20; presença em concluidos/ implica CONCLUIDA conforme convenção do projeto)
**Data:** 2026-04-05
**Prioridade:** BAIXA
**Tipo:** Port (Luna + TS -> Python)
**Dependências:** P6-B
**Desbloqueia:** --

---

## Implementação

### AnalyzeTool (`nyx/agent/tools/analyze_tool.py`)
- Parâmetro: `file_path` (str)
- Analisa: imports, classes, funções, linhas, complexidade
- Usa `ast` module para Python
- Retorna estrutura formatada
- Para não-Python: contagem básica (linhas, funções por regex)

### PatchTool (`nyx/agent/tools/patch_tool.py`)
- Parâmetro: `file_path` (str), `patch` (str, unified diff format)
- Aplica patch via `difflib` ou subprocess `patch`
- Verifica se patch aplica limpo
- Retorna resultado (linhas modificadas)

### MultiEditTool (`nyx/agent/tools/multi_edit.py`)
- Parâmetro: `edits` (list of {file_path, old_string, new_string})
- Aplica múltiplas edições atomicamente
- Se uma falha, reverte todas (transação)
- Retorna resumo: N arquivos, N edições

### Testes Gauntlet

| ID | Nome | Validação |
|----|------|-----------|
| P8E-01 | Analyze retorna estrutura | Analisa models.py, verifica classes/funções |
| P8E-02 | Patch aplica diff | Cria arquivo, aplica patch, verifica |
| P8E-03 | MultiEdit atômico | Edita 2 arquivos, verifica ambos |

## Verificação

- [ ] AnalyzeTool funciona com Python real
- [ ] PatchTool aplica unified diff
- [ ] MultiEdit reverte se falha parcial
- [ ] 3 testes Gauntlet passando

---

*"A parte é mais complexa que o todo." -- Blaise Pascal*
