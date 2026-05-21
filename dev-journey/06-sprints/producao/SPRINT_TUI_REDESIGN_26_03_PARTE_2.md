## 0. SPEC

```yaml
sprint:
  id: TUI-REDESIGN-26-03-PARTE-2
  title: "Alinhamento das ações à direita nos tool chips (fecha CONCLUIDA_PARCIAL de 26-03)"
  onda: 26
  bloco: "26.1 Fidelidade visual"
  prioridade: MÉDIA
  tipo: Feature
  dependencias: [TUI-REDESIGN-26-03]
  desbloqueia: []

  touches:
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/agent/output.py
      reason: "Em render_tool_chip (ou função análoga criada em 26-03), alinhar coluna de ações (status + tempo) à direita usando largura do terminal"

  creates: []
  removes: []

  forbidden:
    - "Alterar glyph-per-tool (já entregue em 26-03 CONCLUIDA_PARCIAL)"
    - "Mudar paleta D ou aesthetic"
    - "Emoji ou menção a IA externa"
    - "Tocar fora de output.py"

  tests:
    - cmd: "./run.sh --smoke"
      timeout: 10
    - cmd: "bash scripts/sprint_invariants.sh"
      timeout: 30
      assert: "PASS=14"
    - cmd: "python3 -c 'from nyx.agent.output import render_tool_card_compact, render_tool_card_done; print(\"OK import\")'"
      timeout: 5
      assert: "símbolo presente ou alternativa"

  acceptance_criteria:
    - "Tool chip exibe ações (símbolo estado + tempo) ALINHADAS à direita"
    - "Layout grid 2-col: [glyph + nome do tool] ESPAÇO [ações]"
    - "Largura do terminal respeitada via shutil.get_terminal_size() ou similar"
    - "Smoke + invariantes 14/14"
    - "Acentuação rc=0"
    - "MASTER linha 167 (26-03) ganha nota fechamento + nova linha 26-03-PARTE-2 CONCLUIDA"
```

---

**Status:** PENDENTE
**Data criação:** 2026-05-21
**Modelo obrigatório:** claude-opus-4-7

---

## Solução

Em `output.py`, função que renderiza tool chip ganha cálculo de padding dinâmico:

```python
import shutil

def render_tool_card_compact(name: str, glyph: str, status: str, elapsed_ms: int) -> None:
    width = shutil.get_terminal_size((80, 24)).columns
    left = f"  {glyph} {name}"
    right = f"{status} {elapsed_ms}ms"
    visible_pad = max(1, width - len(strip_ansi(left)) - len(strip_ansi(right)) - 2)
    line = f"{left}{' ' * visible_pad}{right}"
    print(line)
```

## Proof-of-work

```bash
bash scripts/sprint_invariants.sh > /tmp/inv_before_c4.txt 2>&1
# IMPLEMENTAR
./run.sh --smoke
bash scripts/sprint_invariants.sh > /tmp/inv_after_c4.txt 2>&1
python3 ~/.config/zsh/scripts/validar-acentuacao.py --paths nyx/agent/output.py
```

## Critério binário

- [ ] Ações alinhadas à direita
- [ ] Largura dinâmica respeitada
- [ ] Smoke + invariantes 14/14
- [ ] MASTER linha 167 + nova entry

---

*"O olho lê do centro para as bordas; recompense a borda."*
