# SPRINT INFRA-PLANEJADOR-FENCED-CHECK-01 — Fenced-block check em dispatch_pre_check.sh

## 0. SPEC

```yaml
sprint:
  id: INFRA-PLANEJADOR-FENCED-CHECK-01
  title: "Estender scripts/dispatch_pre_check.sh para rejeitar spec Refactor sem fenced code block"
  onda: 25
  bloco: "25.meta Anti-débito de pipeline"
  prioridade: BAIXA
  tipo: Feature (infra)
  dependencias: [INFRA-PLANEJADOR-CODE-EXCERPT-IN-SPECS-01, INFRA-VALIDATOR-PRE-DISPATCH-RECHECK-01]
  desbloqueia: []

  touches:
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/scripts/dispatch_pre_check.sh
      reason: "Adicionar bloco de validação estrutural: quando spec tem `type: Refactor` e `touches.length == 1`, exige fenced code block na seção Antes/Depois antes do dispatch. Complementa 125xx (template) com check executável."

  forbidden:
    - "Tocar SPRINT_TEMPLATE_V2.md já endurecido em 125xx"
    - "Tocar ~/.claude/agents/planejador-sprint.md externo"
    - "Quebrar comportamento atual de PRE-SATISFEITA (testes existentes devem continuar passando)"
    - "Emoji ou menção a IA externa"

  tests:
    - cmd: "./run.sh --smoke"
      timeout: 10
    - cmd: "bash scripts/sprint_invariants.sh"
      timeout: 30
      assert: "PASS=14"
    - cmd: "bash scripts/dispatch_pre_check.sh dev-journey/06-sprints/concluidos/SPRINT_MASTER_IDS_DEDUP_02.md"
      assert: "exit 0 com PRE-SATISFEITA (não regrediu comportamento prévio)"
    - cmd: "bash scripts/dispatch_pre_check.sh dev-journey/06-sprints/concluidos/SPRINT_OUTPUT_VISIBLE_LEN_RENAME_01.md"
      assert: "exit 0 ou 1 (sprint Refactor com touches=1 mas concluída — fenced ou não, não bloqueia spec concluída)"
    - cmd: "python3 ~/.config/zsh/scripts/validar-acentuacao.py --paths scripts/dispatch_pre_check.sh"
      assert: "rc=0"

  acceptance_criteria:
    - "Nova função/bloco em dispatch_pre_check.sh detecta `type: Refactor` no YAML"
    - "Se type==Refactor E touches.length==1, exige presença de fenced code block (regex de 3+ linhas entre ``` e ```) em qualquer seção do spec markdown"
    - "Falha com mensagem clara `[REJEITADA] Refactor cirúrgico requer fenced code block (lição BUNDLE-01)` e exit !=0 quando ausente"
    - "Comportamento PRE-SATISFEITA existente preservado para outros casos"
    - "Self-test: rodar contra spec própria (que tem fenced code blocks) deve passar"
    - "Smoke + invariantes 14/14"
    - "Acentuação rc=0"
```

---

**Status:** PENDENTE
**Data criação:** 2026-05-21
**Modelo obrigatório:** claude-opus-4-7

---

## Solução proposta

Adicionar bloco após o parser de `acceptance_criteria` (ou em função auxiliar) no `scripts/dispatch_pre_check.sh`:

```bash
# Antes:
# (final do loop while IFS= read -r crit; do ... done)
# ...
# echo "Resumo: ..."

# Depois (adicionar antes do echo de Resumo):
# --- Fenced-block check para Refactor cirúrgico (125yy) ---
spec_type=$(echo "$yaml_block" | sed -nE 's/^[[:space:]]+tipo:[[:space:]]+(.+)$/\1/p' | head -1 | tr -d '"')
touches_count=$(echo "$yaml_block" | awk '/^[[:space:]]+touches:/{flag=1; next} flag && /^[a-z_]+:/{exit} flag && /^[[:space:]]+-/{count++} END{print count+0}')

if echo "$spec_type" | grep -qiE 'Refactor' && [ "${touches_count:-0}" -eq 1 ]; then
    # Contar fenced code blocks na spec inteira (não apenas YAML).
    fenced=$(grep -cE '^[[:space:]]*```[a-z]*$' "$spec")
    # >=2 marcadores ``` = pelo menos 1 fenced block completo.
    if [ "$fenced" -lt 2 ]; then
        echo ""
        echo "[REJEITADA] Refactor cirúrgico requer fenced code block (lição BUNDLE-01)"
        echo "  type=$spec_type touches=1 mas zero fenced blocks encontrados"
        exit 3
    fi
fi
# --- Fim fenced-block check ---
```

Exit code 3 distingue de 1 (acceptance não satisfeito) e 2 (spec inexistente).

## Critério binário

- [ ] Fenced check adicionado ao script
- [ ] Spec própria (com fenced code) passa o self-test
- [ ] DEDUP-02 continua PRE-SATISFEITA (não regrediu)
- [ ] Smoke + invariantes 14/14
- [ ] Acentuação rc=0
