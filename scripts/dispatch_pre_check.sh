#!/usr/bin/env bash
# Pre-flight check para specs de sprint. Avalia acceptance_criteria parseaveis
# antes do dispatch do executor. Se TODOS criterios parseaveis ja satisfeitos,
# emite PRE-SATISFEITA (exit 0) -- caller pode pular o dispatch.
#
# Uso: bash scripts/dispatch_pre_check.sh <path-spec.md>
#
# Compatibilidade: parser não depende de gawk (terceiro argumento de match()).
# Usa mawk + sed -E para extracao, funcionando no awk default do Debian/Ubuntu.

set -u

spec="${1:?uso: $0 <spec.md>}"
[ -f "$spec" ] || { echo "spec não encontrada: $spec"; exit 2; }

# 1. Extrai bloco YAML entre ```yaml ... ``` da spec.
yaml_block=$(awk '
    /^```yaml$/ { flag=1; next }
    /^```$/     { flag=0 }
    flag        { print }
' "$spec")

if [ -z "$yaml_block" ]; then
    echo "spec sem bloco yaml: $spec"
    exit 1
fi

# 2. Extrai linhas de acceptance_criteria. Estrategia:
#    - liga flag ao ver `^  acceptance_criteria:` (2 espacos)
#    - aceita linhas filhas `^    - "..."` (4+ espacos + hifen + aspas)
#    - desliga ao encontrar nova chave de mesmo nivel `^  [a-z_]+:`
#      (2 espacos + identificador YAML + dois pontos)
criteria_raw=$(echo "$yaml_block" | awk '
    /^  acceptance_criteria:/ { flag=1; next }
    flag && /^  [a-z_]+:/     { flag=0 }
    flag                      { print }
')

# 3. Para cada linha, extrai conteudo entre aspas duplas via sed.
criteria=$(echo "$criteria_raw" | sed -nE 's/^[[:space:]]+-[[:space:]]+"(.+)"[[:space:]]*$/\1/p')

if [ -z "$criteria" ]; then
    echo "sem acceptance_criteria parseaveis em $spec"
    exit 1
fi

parseaveis=0
satisfeitos=0
nao_parseaveis=0

# Avalia cada criterio
while IFS= read -r crit; do
    [ -z "$crit" ] && continue

    # Tipo A: critério começa com comando shell direto (grep/wc/awk/test -f).
    if echo "$crit" | grep -qE '^(grep|wc|awk|test -f)'; then
        # Heuristica 1: "<cmd> retorna 0 linhas" ou "<cmd> retorna 0".
        if echo "$crit" | grep -qE 'retorna 0( linhas)?$'; then
            cmd=$(echo "$crit" | sed -E 's/[[:space:]]+retorna 0( linhas)?[[:space:]]*$//')
            parseaveis=$((parseaveis+1))
            out=$(bash -c "$cmd" 2>/dev/null || true)
            if [ -z "$out" ]; then
                echo "  [OK]       $crit"
                satisfeitos=$((satisfeitos+1))
            else
                echo "  [PENDENTE] $crit"
            fi
        # Heuristica 2: critério é comando direto, avalia exit code.
        else
            parseaveis=$((parseaveis+1))
            if bash -c "$crit" >/dev/null 2>&1; then
                echo "  [OK]       $crit"
                satisfeitos=$((satisfeitos+1))
            else
                echo "  [PENDENTE] $crit"
            fi
        fi
    # Tipo B: critério narrativo com sufixo "rc=0" / "exit 0".
    elif echo "$crit" | grep -qE '(rc=0|exit 0)$'; then
        cmd=$(echo "$crit" | sed -E 's/[[:space:]]+(rc=0|exit 0)[[:space:]]*$//')
        # So tenta rodar se o que sobrou parece comando shell razoavel.
        if echo "$cmd" | grep -qE '^[a-z./_-]'; then
            parseaveis=$((parseaveis+1))
            if bash -c "$cmd" >/dev/null 2>&1; then
                echo "  [OK]       $crit"
                satisfeitos=$((satisfeitos+1))
            else
                echo "  [PENDENTE] $crit"
            fi
        else
            echo "  [N/A]      $crit"
            nao_parseaveis=$((nao_parseaveis+1))
        fi
    else
        echo "  [N/A]      $crit"
        nao_parseaveis=$((nao_parseaveis+1))
    fi
done <<< "$criteria"

# --- Fenced-block check para Refactor cirúrgico (INFRA-PLANEJADOR-FENCED-CHECK-01) ---
# Lição empírica BUNDLE-01: specs do tipo Refactor com touches=1 (cirúrgico)
# precisam carregar trecho de código antes/depois em fenced block para evitar
# narrativa-orientada-a-linha que diverge da realidade do arquivo-alvo.
# Compatibilidade: mawk-only (sem captura 3-arg de gawk); usa sed -nE e grep -cE.

spec_tipo=$(echo "$yaml_block" | sed -nE 's/^[[:space:]]+tipo:[[:space:]]+(.+)$/\1/p' | head -1 | tr -d '"')

# Conta itens da lista touches:. O bloco YAML começa em coluna 2 (2 espaços),
# então touches: aparece como `^  touches:`. Itens filhos começam com `^    -`
# (4+ espaços + hífen). Encerra ao achar nova chave de mesmo nível.
touches_count=$(echo "$yaml_block" | awk '
    /^  touches:/             { flag=1; next }
    flag && /^  [a-z_]+:/     { flag=0 }
    flag && /^[[:space:]]+- / { count++ }
    END                       { print count+0 }
')

if echo "$spec_tipo" | grep -qiE 'Refactor' && [ "${touches_count:-0}" -eq 1 ]; then
    # Conta marcadores ``` totais. O bloco YAML do header consome 2 marcadores
    # (```yaml ... ```), então para garantir 1 fenced block ADICIONAL (antes/depois)
    # exige-se >=4 marcadores totais.
    fenced_total=$(grep -cE '^[[:space:]]*```[a-zA-Z]*$' "$spec")
    if [ "${fenced_total:-0}" -lt 4 ]; then
        echo ""
        echo "[REJEITADA] Refactor cirúrgico requer fenced code block (lição BUNDLE-01)"
        echo "  tipo=$spec_tipo touches=1 mas spec não contém fenced code block além do YAML em $spec"
        exit 3
    fi
fi
# --- Fim fenced-block check ---

echo ""
echo "Resumo: $satisfeitos/$parseaveis criterios parseaveis satisfeitos ($nao_parseaveis não-parseaveis)"

if [ "$parseaveis" -gt 0 ] && [ "$satisfeitos" -eq "$parseaveis" ]; then
    echo "PRE-SATISFEITA"
    exit 0
else
    exit 1
fi
