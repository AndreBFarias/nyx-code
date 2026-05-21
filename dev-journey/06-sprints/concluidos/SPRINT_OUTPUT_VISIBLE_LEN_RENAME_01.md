# SPRINT OUTPUT-VISIBLE-LEN-RENAME-01 — Renomear `_strip_ansi` → `_visible_len` (nome semântico)

## 0. SPEC

```yaml
sprint:
  id: OUTPUT-VISIBLE-LEN-RENAME-01
  title: "Renomear `_strip_ansi(text) -> int` para `_visible_len` (nome correto) preservando alias"
  onda: 25
  bloco: "25.meta Anti-débito de pipeline"
  prioridade: BAIXA
  tipo: Refactor
  dependencias: []
  desbloqueia: []

  touches:
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/agent/output.py
      reason: "Função `_strip_ansi` em output.py:845-847 tem nome enganoso (retorna int, não str). Renomear para `_visible_len` e adicionar alias retrocompatível"

  forbidden:
    - "Quebrar callsites existentes — alias `_strip_ansi = _visible_len` preserva retro-compat"
    - "Tocar outros arquivos que não output.py"
    - "Mudar lógica da função (apenas rename + alias)"
    - "Emoji ou menção a IA externa"

  tests:
    - cmd: "./run.sh --smoke"
      timeout: 10
    - cmd: "bash scripts/sprint_invariants.sh"
      timeout: 30
      assert: "PASS=14"
    - cmd: "python3 -c 'from nyx.agent.output import _visible_len, _strip_ansi; assert _visible_len is _strip_ansi or _visible_len(\"a\") == _strip_ansi(\"a\")'"
      timeout: 5

  acceptance_criteria:
    - "grep `_visible_len` em output.py retorna ≥1 hit"
    - "grep `_strip_ansi` em output.py retorna ≥1 hit (alias preservado)"
    - "Callsites internos (4) continuam funcionando"
    - "Smoke + invariantes 14/14"
    - "Acentuação rc=0"
```

---

**Status:** CONCLUIDA
**Data criação:** 2026-05-21
**Data conclusão:** 2026-05-21
**Commit:** 522fed0
**Modelo obrigatório:** claude-opus-4-7
**Validador:** APROVADO_COM_RESSALVAS (achado colateral catalogado em 125uu — INFRA-RUFF-NOQA-FIX-01)

---

## Solução

```python
def _visible_len(text: str) -> int:
    """Comprimento visível ignorando escapes ANSI (TUI-REDESIGN-26-03-PARTE-2)."""
    return len(re.sub(r"\033\[[0-9;]*[A-Za-z]", "", text))


# Alias retrocompatível (será removido em sprint futura quando callsites migrarem).
_strip_ansi = _visible_len
```

## Critério binário

- [ ] `_visible_len` definida em output.py
- [ ] `_strip_ansi = _visible_len` (alias) preservado
- [ ] Smoke + invariantes 14/14
