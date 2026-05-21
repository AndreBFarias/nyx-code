## 0. SPEC

```yaml
sprint:
  id: TUI-REDESIGN-25-12-PARTE-2
  title: "Integração pós-stream do parser de thinking no consumer (output.py)"
  onda: 25
  bloco: "25.4 Thinking/tools/estrutura"
  prioridade: MÉDIA
  tipo: Feature
  dependencias: [TUI-REDESIGN-25-12]
  desbloqueia: []

  touches:
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/agent/output.py
      reason: "Após stream completar, consumir parser de thinking (já existe em 25-12) e renderizar bloco visual recolhível"
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/cli.py
      reason: "OPCIONAL: passar callback on_thinking_complete ao agent loop"

  creates: []
  removes: []

  forbidden:
    - "Alterar lógica do parser de thinking (já estável em 25-12)"
    - "Adicionar emoji ou menção a IA externa"
    - "Quebrar render layer ADR-024 (print só em cli/output)"
    - "Tocar proxy.py ou loop/*"

  tests:
    - cmd: "./run.sh --smoke"
      timeout: 10
    - cmd: "bash scripts/sprint_invariants.sh"
      timeout: 30
      assert: "PASS=14"

  acceptance_criteria:
    - "output.py tem nova função render_thinking_block(text) que renderiza thinking em bloco recolhível"
    - "Chamado uma vez por turn quando há thinking parsed"
    - "Default: thinking colapsado; usuário pode expandir via Tab (já em 25-09-PARTE-2)"
    - "Smoke + invariantes 14/14"
    - "Acentuação rc=0"
    - "MASTER linha 159 (25-12) ganha nota de fechamento + nova linha 25-12-PARTE-2 CONCLUIDA"
```

---

**Status:** CONCLUIDA (2026-05-21, commit pendente)
**Data criação:** 2026-05-21
**Data conclusão:** 2026-05-21
**Modelo obrigatório:** claude-opus-4-7

---

## Solução

Já existe parser em 25-12 (CONCLUIDA_PARCIAL). Esta sprint amarra o output:

```python
# output.py
def render_thinking_block(text: str, collapsed: bool = True) -> None:
    """Renderiza thinking em bloco recolhível (default colapsado)."""
    if not text.strip():
        return
    # render compact + chip de expansão
    ...
```

## Proof-of-work

```bash
bash scripts/sprint_invariants.sh > /tmp/inv_before_c3.txt 2>&1
# IMPLEMENTAR
./run.sh --smoke
bash scripts/sprint_invariants.sh > /tmp/inv_after_c3.txt 2>&1
python3 ~/.config/zsh/scripts/validar-acentuacao.py --paths nyx/agent/output.py
```

## Critério binário

- [ ] `render_thinking_block(text, collapsed)` em output.py
- [ ] Chamado após stream pelo cli (callback ou inline)
- [ ] Default colapsado
- [ ] Smoke + invariantes 14/14
- [ ] MASTER 159 + nova entry

---

*"O pensamento que se esconde tem o tamanho do botão que o revela."*
