## 0. SPEC

```yaml
sprint:
  id: AUDIT-FIX-08
  title: "Remover menção a 'Claude Code' de docstring em output.py"
  onda: 22
  bloco: 2.5
  prioridade: ALTA
  tipo: Bugfix
  dependencias: []
  desbloqueia: [UX-DESIGN-01]

  touches:
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/agent/output.py
      reason: "Docstring da função render_tool_call_start menciona 'estilo Claude Code' — violação ADR-005"
      linhas_alvo: "303"

  creates: []
  removes: []

  forbidden:
    - "Manter qualquer forma da string 'Claude Code' / 'Claude' no código"
    - "Introduzir emoji no processo"
    - "Absorver escopo de outras sprints (AUDIT-FIX-09, DEBT-04, etc.)"

  tests:
    - cmd: "grep -rn 'Claude' nyx/ --include='*.py'"
      esperado: "vazio"
    - cmd: "bash scripts/sprint_invariants.sh | grep 'output.py:303'"
      esperado: "sem match (invariante #2 fecha)"
    - cmd: "./run.sh --gauntlet --only rapido"
      deve_passar: true

  acceptance_criteria:
    - "Zero ocorrência de 'Claude' em nyx/**/*.py"
    - "Invariante #2 (menção a IA) cai no sprint_invariants.sh"
    - "Gauntlet rapido passa"
    - "Commit atômico (apenas este arquivo tocado)"
```

---

# Sprint AUDIT-FIX-08 — Docstring output.py sem menção a IA

**Status:** PENDENTE
**Data criação:** 2026-04-19
**Modelo obrigatório:** claude-opus-4-7 (sem subagentes)

---

## Contexto do projeto (snapshot)

> - ADR-004 Zero Emojis; ADR-005 Anonimato; ADR-006 PT-BR; ADR-024 Render Layer.
> - Finding A-05 da AUDIT-EXT-01 (2026-04-18): docstring em `output.py:303` contém `"estilo Claude Code"`.
> - Sprint fantasma: o relatório da auditoria externa propôs AUDIT-FIX-08, mas o arquivo nunca foi criado. Esta sprint materializa o finding.
> - Invariante `#2` do `sprint_invariants.sh` aponta esta linha como FAIL.

---

## Problema

`nyx/agent/output.py:303` tem docstring:

```python
def render_tool_call_start(name: str, args: str) -> None:
    """Imprime tool call estilo Claude Code: '⏺ nome(arg)' em accent color."""
```

Viola ADR-005 (Anonimato). Também viola o catálogo de gambiarras por sprint (linha 48 do GAMBIARRAS_POR_SPRINT.md), que atribui esse fechamento à UX-DESIGN-01 — incorreto, já que a docstring não tem relação com o design system.

---

## Solução proposta

Reescrever a docstring sem referência externa. Descrever o comportamento em termos do próprio sistema.

---

## Arquivos alvo

### `/home/andrefarias/Desenvolvimento/Nyx-Code/nyx/agent/output.py`

**Antes (linha 303):**
```python
    """Imprime tool call estilo Claude Code: '⏺ nome(arg)' em accent color."""
```

**Depois:**
```python
    """Renderiza linha de tool call com bullet ⏺ em accent color."""
```

**Mudanças:**
- Troca `Imprime` → `Renderiza` (alinha com ADR-024 Render Layer).
- Remove `estilo Claude Code`.
- Remove exemplo literal `'⏺ nome(arg)'` (reduz ruído; comportamento está na assinatura).

---

## Diff esperado

```
~ 1 arquivo modificado
+ 0/−0 linhas líquidas (troca de string em 1 linha)
```

---

## Comandos de verificação

```bash
# 1. grep global por "Claude" em código Python
grep -rn 'Claude' nyx/ --include='*.py'
# esperado: vazio

# 2. invariante #2 deve cair
bash scripts/sprint_invariants.sh | grep -E '^\[FAIL\].*2\.'
# esperado: vazio

# 3. smoke test
./run.sh --gauntlet --only rapido
```

---

## Critério binário de aceite

- [ ] `grep -rn 'Claude' nyx/ --include='*.py'` retorna vazio
- [ ] Invariante #2 (menção a IA) sai de FAIL
- [ ] Gauntlet `--only rapido` passa 100%
- [ ] Commit atômico `fix: remove menção a IA em docstring de output.py`
- [ ] Sprint movida de producao/ para concluidos/
- [ ] SPRINT_ORDER_MASTER atualizado com hash do commit
- [ ] GAMBIARRAS_POR_SPRINT.md atualizado (remove docstring de UX-DESIGN-01; adiciona em AUDIT-FIX-08)

---

## Proof-of-work obrigatório

```bash
bash scripts/sprint_invariants.sh > /tmp/inv_before.txt 2>&1
# implementar
bash scripts/sprint_invariants.sh > /tmp/inv_after.txt 2>&1
diff /tmp/inv_before.txt /tmp/inv_after.txt
```

Esperado no diff: linha `[FAIL] 2. menção a IA` desaparece ou entra em PASS.

---

## Gambiarras específicas

- **Mover docstring para arquivo vizinho** em vez de reescrever. Detectar: `grep -rn 'Claude' nyx/` deve ser 0 em **todo** nyx/.
- **Substituir por sinônimo sutil** como "estilo Anthropic-CLI". Proibido: qualquer nome de vendor/produto de IA.
- **Transformar em comentário em vez de docstring** e achar que sai do grep. Proibido: grep não distingue; é busca textual pura.

---

## Riscos

| Risco | Mitigação |
|-------|-----------|
| Renomear função e esquecer caller | Mudança é apenas no corpo da docstring, não na assinatura |
| Pre-commit rejeitar acentuação | Usar `⏺` e palavras com acentos (Renderiza já é PT-BR correto) |

---

*"A palavra não é apenas o que se diz, é o que se lembra." -- Pessoa*
