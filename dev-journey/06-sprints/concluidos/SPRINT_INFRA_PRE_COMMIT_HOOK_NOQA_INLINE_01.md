## 0. SPEC (machine-readable)

```yaml
sprint:
  id: INFRA-PRE-COMMIT-HOOK-NOQA-INLINE-01
  title: "Hook local respeita marcadores noqa-* inline em vez de excluir arquivos inteiros (refina sprint 200)"
  onda: 29
  prioridade: MÉDIA
  tipo: Bugfix
  dependencias: [INFRA-PRE-COMMIT-HOOK-EXCEPTIONS-01]
  desbloqueia: []

  touches:
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/scripts/hooks/pre-commit
      reason: "Adicionar suporte a noqa-acento/noqa-anonimato/noqa-cli-externo inline; reverter exceções globais da 200 (MASTER/Checkpoint/README)"
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/scripts/hooks/test_noqa_inline.sh
      reason: "Testar suporte a noqa inline (3 cenários: linha com noqa = pass, sem noqa = bloqueio, ASCII puro = pass silencioso)"

  creates:
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/scripts/hooks/test_noqa_inline.sh
      reason: "Teste end-to-end da heurística noqa inline"

  forbidden:
    - "Mudar regex dos checks (ACCENT_PATTERNS, AI_PATTERN)"
    - "Quebrar checks de Emojis ou sanitizer_attack (regras absolutas, sem noqa)"
    - "Permitir noqa-emoji ou noqa-sanitizer-attack"
    - "Adicionar emoji"

  tests:
    - cmd: "bash scripts/hooks/test_noqa_inline.sh"
      timeout: 30
      deve_passar: true
    - cmd: "bash scripts/sprint_invariants.sh"
      timeout: 30
      deve_passar: true
    - cmd: "./run.sh --smoke"
      timeout: 60
      deve_passar: true

  acceptance_criteria:
    - "Linha contendo `<!-- noqa-acento -->` é IGNORADA pelo check Acentuacao"
    - "Linha contendo `<!-- noqa-anonimato -->` é IGNORADA pelo check Anonimato"
    - "Linha contendo `<!-- noqa-cli-externo -->` é IGNORADA pelo check OpenClaude residual"  <!-- noqa-anonimato --><!-- noqa-cli-externo -->
    - "Linhas SEM marcadores continuam validadas normalmente"
    - "Marcadores em comentários Python `# noqa-acento` também funcionam (mesma heurística)"
    - "Exceções globais da 200 podem ser revertidas (MASTER + Checkpoint + README voltam a ser scanned, agora com suporte inline)"
    - "Smoke + invariantes 14/14 PASS"
```

---

# Sprint INFRA-PRE-COMMIT-HOOK-NOQA-INLINE-01 — Granularidade noqa

**Status:** PENDENTE
**Data criação:** 2026-05-22
**Modelo obrigatório:** claude-opus-4-7 (sem subagentes)

---

## Contexto

> Sprint 200 (commit b08cd60) adicionou MASTER + Checkpoint + README às exceções globais dos checks Acentuacao/Anonimato/OpenClaude do hook local. Funciona, mas é grosseiro: arquivos inteiros ficam isentos.  <!-- noqa-anonimato --><!-- noqa-cli-externo -->
> Solução mais granular: o hook respeitar marcadores `<!-- noqa-acento -->`, `<!-- noqa-anonimato -->`, `<!-- noqa-cli-externo -->` em linhas específicas, igual o `validar-acentuacao.py` já faz (BRIEF §[CORE] Sintaxe correta de utilitários externos).

---

## Problema

`scripts/hooks/pre-commit` linhas 81/120/186 excluem 6 paths globais:
- `dev-journey/06-sprints/SPRINT_ORDER_MASTER.md`
- `Checkpoint.md`
- `README.md`

Risco: arquivo inteiro fica "buraco" — qualquer menção indevida a IA passa. Idealmente cada LINHA decide se é débito narrativo legítimo (com marcador) ou bug real (sem marcador).

`validar-acentuacao.py` já implementa essa convenção. O hook local deveria seguir o mesmo padrão.

---

## Solução

### 1. Adicionar função `_has_noqa_marker()` no hook

```bash
# Retorna 0 se a linha contém marcador noqa para o check especificado.
# Suporta: <!-- noqa-acento --> em .md/.sh
#          # noqa-acento em .py/.sh
#          // noqa-acento em .js (futuro)
_has_noqa_marker() {
    local line="$1"
    local marker="$2"  # "acento", "anonimato", "cli-externo"
    # Cobertura: HTML comment, Python comment, shell comment
    if echo "$line" | grep -qE "(<!--|#|//)[[:space:]]*noqa-${marker}([[:space:]]|-->|$)"; then
        return 0
    fi
    return 1
}
```

### 2. Modificar check Acentuacao (linha ~90-100)

```bash
# ANTES (loop simples):
HITS=$(echo "$CONTENT" | grep -niE "$pattern" 2>/dev/null \
    | grep -vE '[├└│/]|```' \
    | head -3 || true)

# DEPOIS (filtra linhas com noqa-acento):
HITS=$(echo "$CONTENT" | grep -niE "$pattern" 2>/dev/null \
    | grep -vE '[├└│/]|```' \
    | while IFS=: read -r linenum linecontent; do
        if ! _has_noqa_marker "$linecontent" "acento"; then
            echo "$linenum:$linecontent"
        fi
    done \
    | head -3 || true)
```

### 3. Modificar check Anonimato (linha ~125)

Mesma lógica: pipe pelo `_has_noqa_marker "$line" "anonimato"`.

### 4. Modificar check OpenClaude (linha ~190)  <!-- noqa-anonimato --><!-- noqa-cli-externo -->

Mesma lógica: pipe pelo `_has_noqa_marker "$line" "cli-externo"`.

### 5. Reverter exceções globais da 200 (opcional mas recomendado)

`scripts/hooks/pre-commit` linhas 81/120/186 — REMOVER os 3 paths que a 200 adicionou (`dev-journey/06-sprints/SPRINT_ORDER_MASTER.md|Checkpoint.md|README.md`). Agora que noqa inline funciona, exceções globais perdem sentido.

### 6. Adicionar marcadores noqa nas linhas relevantes do MASTER/Checkpoint/README

Pós-reversão das exceções globais, o guard vai re-flagar as 7 violações pré-existentes. Para cada uma, adicionar `<!-- noqa-anonimato -->` ou `<!-- noqa-cli-externo -->` no fim da linha.

Linhas catalogadas pela sprint 199:
- `README.md:326` — provável referência a Layout Parity com CLI externo → `<!-- noqa-cli-externo -->`
- `SPRINT_ORDER_MASTER.md:21, :33, :174` — texto narrativo histórico → `<!-- noqa-cli-externo -->` ou `<!-- noqa-anonimato -->`
- MASTER:398 — "verificacao" como código antigo citado → já tem `<!-- noqa-acento -->`, agora vai funcionar

---

## Teste end-to-end

`scripts/hooks/test_noqa_inline.sh`:

```bash
#!/usr/bin/env bash
set -euo pipefail
SCRIPT="scripts/hooks/pre-commit"
TMPDIR=$(mktemp -d)
trap "rm -rf $TMPDIR" EXIT

# Cenário 1: linha com noqa-acento NÃO bloqueia
echo "# Texto com validacao [^_a-z/] <!-- noqa-acento -->" > "$TMPDIR/file1.md"
# Cenário 2: linha sem noqa-acento BLOQUEIA
echo "# Texto com validacao [^_a-z/]" > "$TMPDIR/file2.md"
# Cenário 3: linha ASCII puro (sem violacao) PASS silencioso
echo "# Texto sem nada de errado" > "$TMPDIR/file3.md"

# (Setup git repo temp + stage + invocar hook + asserts)
# Esperado:
#   - file1 + file3: hook exit 0
#   - file2: hook exit 1 com FAIL Acentuacao
```

---

## Diff esperado

```
~ 1 arquivo modificado (scripts/hooks/pre-commit) — +30L função + 3 loops modificados − 3L exceções
+ 1 arquivo criado (test_noqa_inline.sh) ~80L
~ 5-7 linhas marcadas com noqa no MASTER/Checkpoint/README
+ ~120 linhas líquidas
```

---

## Critério binário de aceite

- [ ] Função `_has_noqa_marker` implementada no hook
- [ ] 3 checks (Acentuacao, Anonimato, OpenClaude) filtram linhas via noqa  <!-- noqa-anonimato --><!-- noqa-cli-externo -->
- [ ] `bash scripts/hooks/test_noqa_inline.sh` PASS (3 cenários)
- [ ] Exceções globais da 200 revertidas (MASTER/Checkpoint/README voltam ao scan)
- [ ] Marcadores noqa adicionados nas 7 violações pré-existentes flagged pela 199
- [ ] Smoke + invariantes 14/14 PASS
- [ ] Acentuação rc=0
- [ ] Nenhuma violação de forbidden[]

---

## Riscos

| Risco | Mitigação |
|-------|-----------|
| Regex de noqa permissivo demais (casa em texto que menciona "noqa-acento" como palavra) | Regex requer prefixo de comentário (`<!--|#|//`) antes do marker |
| Reverter exceções e re-bloquear commits enquanto adiciona noqa nas 7 violações | Fazer em ordem: adicionar marcadores ANTES de remover exceções; staged como 2 passos |
| MASTER:398 já tem noqa mas estava sendo ignorado pelo guard antigo | Agora respeitar — verificar empiricamente que aquela linha não falha |
| Marcadores noqa "esquecidos" — desenvolvedor não saberia que existe | Documentar em VALIDATOR_BRIEF.md §[CORE] e nos comentários dos checks |

---

## Pós-condição

Hook fica mais granular: cada LINHA decide via marcador inline. Arquivos não precisam mais de exceção global. Defense-in-depth do invariante #14 segue intacta (Emojis e sanitizer_attack permanecem sem noqa — regras absolutas).

---

*"Granular é melhor que global." -- princípio refactor Nyx-Code.*
