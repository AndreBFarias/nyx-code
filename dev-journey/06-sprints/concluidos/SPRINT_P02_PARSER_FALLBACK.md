## 0. SPEC (machine-readable)

```yaml
sprint:
  id: P-02
  title: "Parser com fallback (7 níveis da Luna)"
  touches:
    - path: nyx/agent/parser.py
      reason: "Parser de ações com 7 níveis de fallback"
  tests:
    - cmd: "./run.sh --gauntlet"
      timeout: 900
  acceptance_criteria:
    - "7 níveis de parse implementados"
    - "qwen3:4b consegue chamar tools via texto quando function_call falha"
    - "Aliases PT-BR: ler, criar, editar, executar, buscar"
```

---

# Sprint P-02 -- Parser com Fallback

**Status:** CONCLUIDA (header corrigido em MASTER-CLEANUP-02 2026-05-20; presença em concluidos/ implica CONCLUIDA conforme convenção do projeto)
**Data:** 2026-04-04
**Prioridade:** ALTA
**Tipo:** Feature
**Dependências:** P-01
**Desbloqueia:** P-03, P-04, P-05

---

## Problema

qwen3:4b nem sempre gera tool_calls perfeitos. Às vezes responde com texto
descrevendo a ação. Precisamos de um parser robusto que extraia ações de
qualquer formato de resposta.

## Referência Luna

`src/skills/code_agent/parser.py` -- 7 níveis de fallback:

1. **EXACT:** blocos ACTION/PATH com separador `---`
2. **FUNCTION_CALL:** `tool_name("path")` ou `tool_name(path="value")`
3. **RELAXED:** regex relaxado (minúsculas, sem `---`)
4. **BARE_TOOL:** `tool_name path/to/file` (sem parênteses)
5. **CODE_BLOCK:** extrai code blocks markdown como create_file
6. **PATH_INTENT:** "Vou ler o arquivo X" -> read_file
7. **IMPLICIT_DONE:** "pronto", "concluído" -> done

## Implementação

Aliases obrigatórios PT-BR:
```python
_ACTION_ALIASES = {
    "read_file": ActionType.READ_FILE,
    "read": ActionType.READ_FILE,
    "ler": ActionType.READ_FILE,
    "write_file": ActionType.WRITE_FILE,
    "criar": ActionType.CREATE_FILE,
    "edit": ActionType.EDIT_FILE,
    "editar": ActionType.EDIT_FILE,
    "run_command": ActionType.RUN_COMMAND,
    "executar": ActionType.RUN_COMMAND,
    "glob": ActionType.GLOB,
    "search": ActionType.SEARCH,
    "buscar": ActionType.SEARCH,
    "grep": ActionType.SEARCH,
    "done": ActionType.DONE,
    "pronto": ActionType.DONE,
    "concluído": ActionType.DONE,
}
```

## Verificação

- [ ] qwen3 responde com texto "vou ler README.md" -> parser extrai READ_FILE
- [ ] qwen3 responde com code block -> parser extrai CREATE_FILE
- [ ] qwen3 responde "pronto" -> parser extrai DONE
- [ ] Gauntlet testa os 7 níveis

---

*"A robustez não é elegância. É sobrevivência." -- Nassim Taleb*
