# SPRINT INFRA-PLANEJADOR-CODE-EXCERPT-IN-SPECS-01 — Template exige trecho de código em refactor

## 0. SPEC

```yaml
sprint:
  id: INFRA-PLANEJADOR-CODE-EXCERPT-IN-SPECS-01
  title: "Endurecer SPRINT_TEMPLATE_V2.md exigindo trecho de código para refactor cirúrgico"
  onda: 25
  bloco: "25.meta Anti-débito de pipeline"
  prioridade: BAIXA
  tipo: Refactor doc
  dependencias: [INFRA-GAUNTLET-CLEANUP-BUNDLE-01]
  desbloqueia: []

  touches:
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/dev-journey/08-templates/SPRINT_TEMPLATE_V2.md
      reason: "Adicionar seção obrigatória 'Antes/Depois com trecho' para sprints type=Refactor com touches.length==1 quando alvo é literal/padrão/substring. Lição empírica: BUNDLE-01 teve 2/3 fixes com número de linha errado; texto-alvo inequívoco salvou."

  forbidden:
    - "Tocar `~/.claude/agents/planejador-sprint.md` (path externo, mantido global)"
    - "Tocar outros templates ou specs concluídas"
    - "Emoji ou menção a IA externa"

  tests:
    - cmd: "./run.sh --smoke"
      timeout: 10
    - cmd: "bash scripts/sprint_invariants.sh"
      timeout: 30
      assert: "PASS=14"
    - cmd: "python3 ~/.config/zsh/scripts/validar-acentuacao.py --paths dev-journey/08-templates/SPRINT_TEMPLATE_V2.md"
      assert: "rc=0"
    - cmd: "grep -cE '^##|trecho|antes/depois|fenced' dev-journey/08-templates/SPRINT_TEMPLATE_V2.md"
      assert: "número aumentou pós-edit (template ganhou conteúdo)"

  acceptance_criteria:
    - "SPRINT_TEMPLATE_V2.md tem nova seção (ou parágrafo) 'Antes/Depois com trecho' OU equivalente"
    - "Texto da seção: para refactor cirúrgico em código existente, spec deve incluir fenced code block (>=3 linhas) citando alvo literal além do número de linha"
    - "Cita lição empírica do BUNDLE-01 (linhas 859/861→968/970, 700-701→809-811)"
    - "Smoke + invariantes 14/14"
    - "Acentuação rc=0"
```

---

**Status:** PENDENTE
**Data criação:** 2026-05-21
**Modelo obrigatório:** claude-opus-4-7

---

## Solução

Verificar primeiro se `dev-journey/08-templates/SPRINT_TEMPLATE_V2.md` existe. Se não existir, criar versão mínima com a seção. Se existir, adicionar seção/parágrafo ao final ou em local apropriado.

Conteúdo a adicionar:

```markdown
### Antes/Depois com trecho (obrigatório para Refactor cirúrgico)

Para sprints `type: Refactor` com `touches.length == 1` e alvo do tipo literal/padrão/substring,
a spec DEVE incluir fenced code block (>=3 linhas) com o trecho EXATO além do número de linha.

**Justificativa empírica:** INFRA-GAUNTLET-CLEANUP-BUNDLE-01 (2026-05-21) teve 2/3 fixes com
número de linha errado na spec (cited 859/861 e 700-701 — reais eram 968/970 e 809-811).
Resolveu via texto-alvo inequívoco, mas só porque planejador teve presença de mente de citar
padrão `"qwen" in content` + frase `"Processos externos ocupando VRAM"`.

**Formato sugerido:**

```python
# Localização aproximada: linha NNN
# Antes:
<TRECHO LITERAL DO CÓDIGO ATUAL, >=3 linhas>

# Depois:
<TRECHO ESPERADO PÓS-FIX, >=3 linhas>
```

Esse formato deixa o executor seguro mesmo quando linhas drift por edits intermediários.
```

## Critério binário

- [ ] SPRINT_TEMPLATE_V2.md tem seção 'Antes/Depois com trecho' (ou equivalente)
- [ ] Cita lição empírica do BUNDLE-01
- [ ] Smoke + invariantes 14/14
- [ ] Acentuação rc=0
