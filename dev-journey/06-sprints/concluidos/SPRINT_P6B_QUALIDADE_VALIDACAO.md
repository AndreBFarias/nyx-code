## 0. SPEC (machine-readable)

```yaml
sprint:
  id: P6-B
  title: "PromptSuggestion + Preflight + PostValidator"
  touches:
    - path: nyx/agent/services/suggestions.py
      reason: "Novo service: sugestões de próximo passo"
    - path: nyx/agent/preflight.py
      reason: "Novo módulo: validação pré-execução"
    - path: nyx/agent/validator.py
      reason: "Novo módulo: validação pós-execução"
    - path: scripts/gauntlet/nyx_gauntlet.py
      reason: "3 testes novos"
  origin:
    primary: "openclaud/src/services/PromptSuggestion/"
    secondary: "Luna/src/skills/code_agent/preflight.py"
  tests:
    - cmd: "./run.sh --gauntlet --only p6_qualidade"
      timeout: 30
  acceptance_criteria:
    - "PromptSuggestion sugere próximos passos"
    - "Preflight valida ação antes de executar"
    - "PostValidator verifica resultado após execução"
```

---

# Sprint P6-B -- Qualidade e Validação

**Status:** PENDENTE
**Data:** 2026-04-05
**Prioridade:** MÉDIA
**Tipo:** Port (TS -> Python + Luna)
**Dependências:** P5-D
**Desbloqueia:** --

---

## Implementação

### PromptSuggestion (`nyx/agent/services/suggestions.py`)
- Analisa histórico da sessão
- Sugere próximos passos baseado em padrões
- Regras: se leu arquivo -> sugerir edit; se editou -> sugerir test; etc.
- `suggest(session) -> list[str]`

### Preflight (`nyx/agent/preflight.py`)
- Validação antes de executar tool
- Verifica: path existe? permissão? disco? arquivo grande demais?
- `check(tool_name, args, project_root) -> PreflightResult`
- PreflightResult: ok, warnings, errors
- Integra no loop como hook pre

### PostValidator (`nyx/agent/validator.py`)
- Validação após executar tool
- Verifica: output válido? arquivo criado corretamente? syntax ok?
- `validate(tool_name, args, result) -> ValidationResult`
- Integra no loop como hook post

### Testes Gauntlet

| ID | Nome | Validação |
|----|------|-----------|
| P6Q-01 | Suggestion gera sugestão | Lista não vazia após sessão com ações |
| P6Q-02 | Preflight valida path | Retorna warning para path inexistente |
| P6Q-03 | PostValidator verifica | Retorna ok para write bem-sucedido |

## Verificação

- [ ] Sugestões fazem sentido para o contexto
- [ ] Preflight previne erros comuns
- [ ] PostValidator detecta problemas
- [ ] 3 testes Gauntlet passando

---

*"Prevenir é melhor que remediar." -- Erasmo de Rotterdam*
