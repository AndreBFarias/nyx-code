## 0. SPEC (machine-readable)

```yaml
sprint:
  id: INFRA-MASTER-DEBT-MARKERS-01
  title: "Marca débitos narrativos restantes no MASTER + Checkpoint + README com noqa apropriado, remove exceções globais redundantes da sprint 200"
  onda: 29
  prioridade: MÉDIA
  tipo: Bugfix
  dependencias: [INFRA-PRE-COMMIT-HOOK-NOQA-INLINE-01]
  desbloqueia: []

  touches:
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/dev-journey/06-sprints/SPRINT_ORDER_MASTER.md
      reason: "Adicionar markers noqa-anonimato/noqa-cli-externo/noqa-acento nas linhas pré-existentes flagadas"
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/Checkpoint.md
      reason: "Idem MASTER — markers em linhas narrativas históricas"
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/README.md
      reason: "Verificar se README precisa de markers adicionais além do que a 201 já fez"
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/scripts/hooks/pre-commit
      reason: "Remover dev-journey/06-sprints/SPRINT_ORDER_MASTER.md + Checkpoint.md + README.md das exceções globais (linhas 95, 140, 213) APÓS confirmar que markers cobrem todas as violações"

  creates: []

  forbidden:
    - "Adicionar marker em linha que NÃO é débito narrativo legítimo (ex: novo texto introduzindo dependência real a IA)"
    - "Quebrar invariante #14, smoke, ou Gauntlet"
    - "Mudar conteúdo lógico das linhas — apenas adicionar marker ao fim"
    - "Adicionar emoji"
    - "Remover exceções globais ANTES de confirmar que todos os markers cobrem todas as violações"

  tests:
    - cmd: "bash scripts/hooks/pre-commit"
      timeout: 30
      deve_passar: true
    - cmd: "bash scripts/sprint_invariants.sh"
      timeout: 30
      deve_passar: true
    - cmd: "./run.sh --smoke"
      timeout: 60
      deve_passar: true

  acceptance_criteria:
    - "TODAS as linhas no MASTER que disparam check Anonimato têm marker `<!-- noqa-anonimato -->`"
    - "TODAS as linhas no MASTER que disparam check OpenClaude residual têm marker `<!-- noqa-cli-externo -->`"  <!-- noqa-anonimato -->
    - "Linhas com violações de Acentuacao em MASTER (`ola mundo acao!`, `validacao-visual`) têm marker `<!-- noqa-acento -->`"
    - "Mesma cobertura aplicada a Checkpoint.md (varredura via guard local)"
    - "Após cobertura completa, exceções globais da sprint 200 são REMOVIDAS de `scripts/hooks/pre-commit` linhas 95/140/213 (paths SPRINT_ORDER_MASTER + Checkpoint + README + outros)"
    - "Pós-remoção: commit teste empírico que toca MASTER passa pelo guard sem bloqueio"
    - "Smoke + invariantes 14/14 PASS"
```

---

# Sprint INFRA-MASTER-DEBT-MARKERS-01 — Granularidade pura

**Status:** PENDENTE
**Data criação:** 2026-05-22
**Modelo obrigatório:** claude-opus-4-7 (sem subagentes)

---

## Contexto

> Sprint 200 (commit b08cd60) adicionou MASTER + Checkpoint + README às exceções globais de 3 checks (Acentuacao/Anonimato/OpenClaude) do hook local. Funcionava mas era grosseiro.  <!-- noqa-anonimato -->  <!-- noqa-cli-externo -->
> Sprint 201 (commit e161e0f) introduziu suporte a `<!-- noqa-* -->` inline e marcou 7 violações catalogadas pela 199.
> Esta sprint completa a granularidade pura: marca **todas** as menções restantes (24+ identificadas pelo executor da 201 como achados colaterais não-fixados) e remove as exceções globais da 200 — agora redundantes.

---

## Problema

Estado atual:
- `scripts/hooks/pre-commit` ainda tem `MASTER + Checkpoint + README` em 3 exceções globais (linhas 95, 140, 213) como **redundância** da 201.
- Se um commit futuro introduzir menção indevida a IA no MASTER, a exceção global vai deixar passar — defense-in-depth diluído.
- O executor da 201 catalogou 24+ menções restantes no MASTER que ainda não foram marcadas individualmente.

Solução: marcar cada linha com noqa apropriado, então remover exceções globais. Granularidade pura.

---

## Solução proposta

### Fase 1: Inventário (read-only)

Script Python ou shell para mapear todas as linhas pré-existentes que casariam os checks. Comandos:

```bash
# Linhas com menção a IA (regex AI_PATTERN do hook):
grep -nE "Claude|GPT|Gemini|Copilot|Anthropic|OpenAI" dev-journey/06-sprints/SPRINT_ORDER_MASTER.md \  <!-- noqa-anonimato -->
    | grep -vE "ANTHROPIC_API_KEY|OPENAI_API_KEY|OPENAI_BASE_URL|OPENAI_MODEL|OPENAI_TIMEOUT|CLAUDE_CODE_USE_OPENAI|Formato OpenAI|/v1/|sem Qwen|sem GPT|Qwen/GPT|Mencionou Qwen|noqa-anonimato|noqa-cli-externo" \
    > /tmp/master_anon_violations.txt

# Linhas com OpenClaude residual:  <!-- noqa-anonimato -->  <!-- noqa-cli-externo -->
grep -niE "openclaude" dev-journey/06-sprints/SPRINT_ORDER_MASTER.md \  <!-- noqa-cli-externo -->
    | grep -v "noqa-cli-externo" \
    > /tmp/master_oc_violations.txt

# Linhas com violacoes de acentuacao (16 patterns):
for pattern in funcao validacao descricao comunicacao configuracao informacao operacao execucao conexao aplicacao autenticacao verificacao instalacao documentacao integracao implementacao; do  <!-- noqa-acento -->
    grep -nE "${pattern}[^_a-z/]" dev-journey/06-sprints/SPRINT_ORDER_MASTER.md \
        | grep -vE '[├└│/]|```' \
        | grep -v "noqa-acento" \
        >> /tmp/master_accent_violations.txt
done

# Idem para Checkpoint.md (mesmos 3 levantamentos)
```

### Fase 2: Marcação automática

Para cada linha do inventário, adicionar marker apropriado:

```python
#!/usr/bin/env python3
"""Marca debitos narrativos historicos com noqa apropriado."""
from pathlib import Path
import re

# Markers por tipo:
#   Anonimato (Claude/GPT/etc) -> <!-- noqa-anonimato -->
#   OpenClaude residual -> <!-- noqa-cli-externo -->  <!-- noqa-anonimato -->
#   Acentuacao (funcao/validacao/etc) -> <!-- noqa-acento -->
# Heuristica: se linha ja tem marker do tipo, skip. Se nao, append " <!-- noqa-X -->" antes do \n.

# Para cada arquivo: ler linhas, identificar violacoes por padrao, adicionar marker.
```

### Fase 3: Verificar empiricamente

Após marcar todas, rodar:

```bash
# Stage + invocar guard local (simulando commit):
git add dev-journey/06-sprints/SPRINT_ORDER_MASTER.md Checkpoint.md README.md
bash scripts/hooks/pre-commit
# Esperado: zero FAIL de Anonimato/OpenClaude/Acentuacao  <!-- noqa-anonimato -->  <!-- noqa-cli-externo -->
```

### Fase 4: Remover exceções globais

Após confirmar cobertura, editar `scripts/hooks/pre-commit`:

```bash
# Linha 95 (Acentuacao):
# ANTES:
reference/*|dev-journey/09-legacy/*|node_modules/*|.git/*|dev-journey/06-sprints/SPRINT_ORDER_MASTER.md|Checkpoint.md) continue ;;
# DEPOIS:
reference/*|dev-journey/09-legacy/*|node_modules/*|.git/*) continue ;;

# Linha 140 (Anonimato):
# ANTES:
GUIDE.md|.claude/*|reference/*|dev-journey/09-legacy/*|scripts/sync.py|scripts/hooks/*|dev-journey/06-sprints/SPRINT_ORDER_MASTER.md|Checkpoint.md|README.md) continue ;;
# DEPOIS:
GUIDE.md|.claude/*|reference/*|dev-journey/09-legacy/*|scripts/sync.py|scripts/hooks/*) continue ;;

# Linha 213 (OpenClaude):  <!-- noqa-anonimato -->  <!-- noqa-cli-externo -->
# ANTES:
reference/*|dev-journey/09-legacy/*|scripts/sync.py|dev-journey/06-sprints/SPRINT_ORDER_MASTER.md|Checkpoint.md|README.md) continue ;;
# DEPOIS:
reference/*|dev-journey/09-legacy/*|scripts/sync.py) continue ;;
```

### Fase 5: Re-validar empírico pós-remoção

```bash
git add scripts/hooks/pre-commit dev-journey/06-sprints/SPRINT_ORDER_MASTER.md Checkpoint.md
bash scripts/hooks/pre-commit
# Esperado: ainda PASS (agora via markers inline, não exceções globais)
```

---

## Diff esperado

```
~ 3 arquivos modificados (MASTER, Checkpoint, README)
+ ~25-40 linhas marcadas com noqa (24+ inventariadas pelo executor da 201)
~ 1 arquivo modificado (scripts/hooks/pre-commit) — remove 3 paths de 3 exceções
- ~9L (3 paths em 3 linhas)
```

---

## Comandos de verificação

```bash
# 1. Inventário pré (zero violações pendentes esperado pós-marcação)
bash scripts/hooks/pre-commit  # deve passar com working tree atual

# 2. Stage tudo e invocar guard
git add -A
bash scripts/hooks/pre-commit  # deve passar zero FAIL

# 3. Smoke + invariantes
./run.sh --smoke
bash scripts/sprint_invariants.sh

# 4. Acentuacao
python3 ~/.config/zsh/scripts/validar-acentuacao.py --paths \
    dev-journey/06-sprints/SPRINT_ORDER_MASTER.md \
    Checkpoint.md \
    README.md \
    scripts/hooks/pre-commit
```

---

## Critério binário de aceite

- [ ] Todas as violações pré-existentes flagged pelo guard local agora têm marker noqa inline apropriado
- [ ] Exceções globais da sprint 200 REMOVIDAS de scripts/hooks/pre-commit linhas 95/140/213
- [ ] `bash scripts/hooks/pre-commit` passa zero FAIL no working tree atual
- [ ] Commit teste empírico (alteração trivial no MASTER) passa pelo guard sem bloqueio
- [ ] Smoke + invariantes 14/14 PASS
- [ ] Acentuação rc=0 nos 4 arquivos (MASTER, Checkpoint, README, pre-commit)
- [ ] Nenhuma violação de forbidden[]

---

## Riscos

| Risco | Mitigação |
|-------|-----------|
| Marcar linha que NÃO é débito narrativo (ex: comentário sobre IA que deveria ser removido) | Heurística conservadora: marker só em linhas que JÁ ESTÃO no histórico (commit > 1 dia atrás) — adições novas continuam reportadas |
| Sequência das fases — remover exceção antes de marcar deixa working tree em FAIL | Spec exige ordem: Fase 4 só após Fase 3 confirmar cobertura |
| Sanitizer atacar durante a sprint (4ª recidiva) | Defense-in-depth ativa: invariante #14 PASS é pré-condição |
| Marcação automática quebrar tabelas/blocos código por adicionar ` <!-- noqa-X -->` no fim | Regex inteligente: skip linhas dentro de \`\`\`...\`\`\` ou tabelas mal-formatadas |

---

## Pós-condição

Defense-in-depth do invariante #14 e do anonimato fica granular puro:
- Cada linha individual decide via marker.
- Adições novas que introduzem menções a IA são automaticamente bloqueadas (sem exceção global pra escapar).
- Manutenção futura: ao adicionar texto narrativo histórico, dev adiciona marker explícito — auditoria fica clara.

---

*"Marker inline é o ponto final da granularidade." -- princípio refactor Nyx-Code.*
