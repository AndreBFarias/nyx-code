# SPRINT INFRA-VALIDATOR-PRE-DISPATCH-RECHECK-01 — Pre-flight de acceptance criteria

## 0. SPEC

```yaml
sprint:
  id: INFRA-VALIDATOR-PRE-DISPATCH-RECHECK-01
  title: "Wrapper interno scripts/dispatch_pre_check.sh para avaliar acceptance binário antes do dispatch"
  onda: 25
  bloco: "25.meta Anti-débito de pipeline"
  prioridade: BAIXA
  tipo: Feature (infra)
  dependencias: [MASTER-IDS-DEDUP-02]
  desbloqueia: []

  touches:
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/scripts/dispatch_pre_check.sh
      reason: "Novo script bash que recebe path de spec e tenta rodar acceptance_criteria parseáveis ANTES do dispatch. Se já satisfeito → exit 0 com mensagem 'PRE-SATISFEITA'. Senão → exit 1 (dispatcher prossegue normal)."

  forbidden:
    - "Tocar `~/.claude/agents/planejador-sprint.md` (path externo, mantido global)"
    - "Tocar outros scripts/*.sh existentes"
    - "Mexer em SPRINT_ORDER_MASTER.md"
    - "Emoji ou menção a IA externa"

  tests:
    - cmd: "./run.sh --smoke"
      timeout: 10
    - cmd: "bash scripts/sprint_invariants.sh"
      timeout: 30
      assert: "PASS=14"
    - cmd: "bash scripts/dispatch_pre_check.sh dev-journey/06-sprints/concluidos/SPRINT_MASTER_IDS_DEDUP_02.md"
      assert: "exit 0 com saída contendo 'PRE-SATISFEITA' (sprint historicamente pre-satisfeita)"
    - cmd: "bash scripts/dispatch_pre_check.sh dev-journey/06-sprints/producao/SPRINT_RELEASE_V1_0_CUT_01.md"
      assert: "exit 1 (sprint genuinamente PENDENTE, acceptance não satisfeito)"

  acceptance_criteria:
    - "Script `scripts/dispatch_pre_check.sh` existe e é executável (chmod +x)"
    - "Parser regex simples extrai `acceptance_criteria` da seção YAML da spec"
    - "Para critérios do tipo `grep`/`wc`/`test -f`/`awk uniq -d`, roda o comando e avalia exit code"
    - "Critérios não-parseáveis (descrição livre) são ignorados (não bloqueiam pre-check)"
    - "Output legível com lista de critérios + status (OK / PENDENTE / NÃO-PARSEÁVEL)"
    - "Smoke + invariantes 14/14"
    - "Acentuação rc=0"
```

---

**Status:** PENDENTE
**Data criação:** 2026-05-21
**Modelo obrigatório:** claude-opus-4-7

---

## Solução

Criar `scripts/dispatch_pre_check.sh`:

```bash
#!/usr/bin/env bash
# Pre-flight check para specs de sprint. Avalia acceptance_criteria parseáveis
# antes do dispatch do executor. Se TODOS critérios parseáveis já satisfeitos,
# emite PRE-SATISFEITA (exit 0) — caller pode pular o dispatch.
#
# Uso: bash scripts/dispatch_pre_check.sh <path-spec.md>

set -u
spec="${1:?uso: $0 <spec.md>}"
[ -f "$spec" ] || { echo "spec não encontrada: $spec"; exit 2; }

# Extrai bloco YAML entre ```yaml ... ``` da spec.
yaml_block=$(awk '/^```yaml$/{flag=1; next} /^```$/{flag=0} flag' "$spec")

# Extrai linhas de acceptance_criteria (formato: `    - "criterio aqui"`).
criteria=$(echo "$yaml_block" | awk '
    /^  acceptance_criteria:/{flag=1; next}
    flag && /^[[:space:]]+-[[:space:]]+"/{
        match($0, /"([^"]+)"/, m); if (m[1]) print m[1];
    }
    flag && /^[a-z_]+:/{exit}
')

[ -z "$criteria" ] && { echo "sem acceptance_criteria parseaveis"; exit 1; }

parseaveis=0
satisfeitos=0
nao_parseaveis=0

while IFS= read -r crit; do
    [ -z "$crit" ] && continue
    # Tipos parseáveis: grep, wc, awk uniq -d, test -f.
    if echo "$crit" | grep -qE '^(grep|wc|awk|test -f)'; then
        parseaveis=$((parseaveis+1))
        if bash -c "$crit" >/dev/null 2>&1; then
            echo "  [OK]  $crit"
            satisfeitos=$((satisfeitos+1))
        else
            echo "  [PENDENTE] $crit"
        fi
    elif echo "$crit" | grep -qE 'retorna 0|exit 0|rc=0|sort \| uniq -d.*retorna 0'; then
        # Heurística: extrair comando antes de "retorna 0" e rodar.
        cmd=$(echo "$crit" | sed -E 's/[[:space:]]*retorna 0.*//; s/[[:space:]]*\| sort \| uniq -d[[:space:]]*$/| sort | uniq -d/')
        parseaveis=$((parseaveis+1))
        out=$(bash -c "$cmd 2>/dev/null" || true)
        if [ -z "$out" ]; then
            echo "  [OK]  $crit"
            satisfeitos=$((satisfeitos+1))
        else
            echo "  [PENDENTE] $crit"
        fi
    else
        echo "  [N/A] $crit"
        nao_parseaveis=$((nao_parseaveis+1))
    fi
done <<< "$criteria"

echo ""
echo "Resumo: $satisfeitos/$parseaveis criterios parseaveis satisfeitos ($nao_parseaveis não-parseaveis)"

if [ "$parseaveis" -gt 0 ] && [ "$satisfeitos" -eq "$parseaveis" ]; then
    echo "PRE-SATISFEITA"
    exit 0
else
    exit 1
fi
```

`chmod +x scripts/dispatch_pre_check.sh`.

## Critério binário

- [ ] Script existe, executável e parseia YAML
- [ ] Para DEDUP-02 (sprint pre-satisfeita histórica) retorna exit 0 + "PRE-SATISFEITA"
- [ ] Para RELEASE-V1.0-CUT-01 (sprint genuinamente pendente) retorna exit 1
- [ ] Smoke + invariantes 14/14
- [ ] Acentuação rc=0
