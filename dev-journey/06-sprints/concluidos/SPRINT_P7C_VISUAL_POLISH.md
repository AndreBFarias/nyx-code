## 0. SPEC (machine-readable)

```yaml
sprint:
  id: P7-C
  title: "Visual polish -- diff boxes, spinners, progress"
  touches:
    - path: nyx/agent/output.py
      reason: "Expandir Rich output com diff panels e spinners"
    - path: nyx/cli.py
      reason: "Integrar spinners durante LLM call"
    - path: scripts/gauntlet/nyx_gauntlet.py
      reason: "2 testes novos"
  origin:
    primary: "openclaud/src/components/"
    secondary: "Luna/src/skills/code_agent/rich_output.py"
  tests:
    - cmd: "./run.sh --gauntlet --only p7_visual"
      timeout: 30
  acceptance_criteria:
    - "Diff boxes formatadas com Rich Panel"
    - "Spinner durante chamada ao LLM"
    - "Barra de progresso para operações longas"
    - "Syntax highlighting em code blocks"
```

---

# Sprint P7-C -- Visual polish

**Status:** PENDENTE
**Data:** 2026-04-05
**Prioridade:** BAIXA
**Tipo:** Feature
**Dependências:** P7-B
**Desbloqueia:** --

---

## Implementação

### Diff boxes (`nyx/agent/output.py`)
- `render_diff(old, new, path)` -- Rich Panel com diff colorido
- Usa `difflib.unified_diff` + Rich Syntax
- Bordas com cores Nyx

### Spinners
- `with nyx_spinner("Pensando...")` context manager
- Rich Spinner durante chamada LLM
- Desaparece quando resposta chega
- Fallback: `...` no stdout se Rich indisponível

### Barra de progresso
- Para operações multi-step (glob em muitos arquivos, etc.)
- Rich Progress com cores Nyx

### Syntax highlighting
- Code blocks em respostas com Rich Syntax
- Detecção automática de linguagem
- Fallback: sem highlight

### Testes Gauntlet

| ID | Nome | Validação |
|----|------|-----------|
| P7V-01 | Diff render | render_diff retorna string não vazia |
| P7V-02 | Spinner importa | nyx_spinner funciona como context manager |

## Verificação

- [ ] Diffs formatados com cores
- [ ] Spinner aparece durante LLM call
- [ ] Code blocks com syntax highlight
- [ ] Fallback funciona sem Rich
- [ ] 2 testes Gauntlet passando

---

*"A beleza é a promessa de utilidade." -- Stendhal*
