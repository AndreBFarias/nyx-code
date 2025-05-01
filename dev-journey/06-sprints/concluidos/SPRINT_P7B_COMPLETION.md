## 0. SPEC (machine-readable)

```yaml
sprint:
  id: P7-B
  title: "Tab completion -- paths, commands, tools"
  touches:
    - path: nyx/agent/completer.py
      reason: "Novo módulo: completers para prompt-toolkit"
    - path: nyx/cli.py
      reason: "Integrar completers no PromptSession"
    - path: scripts/gauntlet/nyx_gauntlet.py
      reason: "2 testes novos"
  origin:
    primary: "Luna/src/skills/code_agent/cli_completer.py"
  tests:
    - cmd: "./run.sh --gauntlet --only p7_completion"
      timeout: 30
  acceptance_criteria:
    - "Tab completa paths de arquivos"
    - "Tab completa /commands"
    - "Tab completa nomes de tools"
    - "Completions context-aware (após / sugere commands, senão paths)"
```

---

# Sprint P7-B -- Tab completion

**Status:** PENDENTE
**Data:** 2026-04-05
**Prioridade:** BAIXA
**Tipo:** Feature
**Dependências:** P7-A
**Desbloqueia:** P7-C

---

## Implementação

### NyxCompleter (`nyx/agent/completer.py`)
- Herda de `prompt_toolkit.completion.Completer`
- Context-aware: detecta se input começa com `/`
- Se `/`: completa commands
- Se não: completa paths de arquivo
- Completa nomes de tools quando detecta padrão de tool call

### PathCompleter
- Completa paths relativos ao project_root
- Respeita .gitignore para filtrar
- Mostra tipo (arquivo/diretório) no metadata

### CommandCompleter
- Lista todos os /commands registrados
- Mostra descrição curta como metadata

### ToolCompleter
- Lista tools registradas
- Mostra descrição como metadata

### Testes Gauntlet

| ID | Nome | Validação |
|----|------|-----------|
| P7C-01 | Completer importa | NyxCompleter inicializa sem erro |
| P7C-02 | Commands listados | Completer retorna /help, /quit etc. |

## Verificação

- [ ] Tab completa paths reais
- [ ] Tab completa /commands
- [ ] Context detection funciona
- [ ] 2 testes Gauntlet passando

---

*"A boa ferramenta antecipa a necessidade." -- Miyamoto Musashi*
