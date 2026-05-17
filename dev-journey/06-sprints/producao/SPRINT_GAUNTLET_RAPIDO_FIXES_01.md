# SPRINT GAUNTLET-RAPIDO-FIXES-01 — Fix 3 FAILs pré-existentes em gauntlet --only rapido

## 0. SPEC (machine-readable)

```yaml
sprint:
  id: GAUNTLET-RAPIDO-FIXES-01
  title: "Corrige 3 FAILs pré-existentes em gauntlet --only rapido (P-07, C-03, C-04)"
  onda: 23
  bloco: 23.0 Performance
  prioridade: ALTA
  tipo: Bugfix
  dependencias: []
  desbloqueia: []
  origem: "Achado colateral de SLASH-BYPASS-AUDIT-01 (commit 5eb0730): gauntlet --only rapido tem 3 FAILs crônicos não-regressão: P-07 tool_calls propagam (proxy), C-03 settings.json dark+pt-BR (Arquivo não existe), C-04 GUIDE.md contém Nyx (Arquivo não existe). Não bloqueia mas suja baseline."

  touches:
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/scripts/gauntlet/nyx_gauntlet.py
      reason: "Investigar fixtures P-07, C-03, C-04. Ajustar paths ou criar arquivos faltantes."

  creates: []
  removes: []

  n_to_n_pairs: []

  forbidden:
    - "Pular teste em vez de corrigir (ADR-014: testes via Gauntlet, sem skip)"
    - "Adicionar arquivo dummy só pra teste passar (precisa refletir realidade)"
    - "Quebrar outros testes da fase config/proxy"
    - "Emoji"

  tests:
    - cmd: "./run.sh --gauntlet --only rapido"
      timeout: 300
      deve_passar: "18/18 (100%)"
    - cmd: "bash scripts/sprint_invariants.sh"
      timeout: 60
      deve_passar: "FAIL_AFTER <= FAIL_BEFORE"
    - cmd: "./run.sh --smoke"
      timeout: 60
      deve_passar: true

  acceptance_criteria:
    - "P-07 tool_calls propagam: investigar causa do FAIL com qwen2.5-coder:3b; ajustar fixture se necessário ou documentar limite"
    - "C-03 settings.json dark+pt-BR: arquivo existe ou fixture aponta para path correto"
    - "C-04 GUIDE.md contém Nyx: GUIDE.md existe e tem 'Nyx' — fixture pode estar buscando em path errado"
    - "Após fix: gauntlet --only rapido passa 18/18 (100%)"
    - "Smoke + invariants passam"
    - "Documentação de cada fix em commit body"
    - "PT-BR; zero emoji; zero menção a IA"
```

---

**Status:** PENDENTE
**Data criação:** 2026-05-17
**Modelo obrigatório:** claude-opus-4-7 (sem subagentes)
**Origem:** achado colateral de SLASH-BYPASS-AUDIT-01

---

# Sprint GAUNTLET-RAPIDO-FIXES-01

## Contexto

Auditoria pós-SLASH-BYPASS-AUDIT-01 revelou 3 testes do gauntlet `--only rapido` falhando consistentemente:

```
P-07 tool_calls propagam      → fase proxy   → falha após troca para qwen2.5-coder:3b?
C-03 settings.json dark+pt-BR → fase config  → "Arquivo não existe"
C-04 GUIDE.md contém Nyx      → fase config  → "Arquivo não existe"
```

Pré-existentes (não introduzidos por nenhuma sprint atual). Bloqueia gate `Gauntlet rapido 100%` de futuras sprints e suja baseline. AC binário "FAIL_AFTER ≤ FAIL_BEFORE" não detecta pois é constante.

## Investigação

Para cada FAIL:

### P-07 tool_calls propagam

Provável causa: qwen2.5-coder:3b emite tool_call em formato JSON-content (não tool_calls API), por isso parser do Nyx faz fallback. Mas fixture verifica `result['tool_calls']` no response do proxy, que pode estar vazio. Verificar:

```bash
grep -A 10 "P-07" scripts/gauntlet/nyx_gauntlet.py
```

### C-03 settings.json dark+pt-BR

Provável causa: fixture lê `~/.claude/settings.json` que não existe na máquina/CI. Verificar path:

```bash
grep -B 2 -A 10 "C-03" scripts/gauntlet/nyx_gauntlet.py
```

### C-04 GUIDE.md contém Nyx

GUIDE.md EXISTE no root. Fixture pode buscar em path errado (CLAUDE.md? path absoluto fixo?):

```bash
grep -B 2 -A 10 "C-04" scripts/gauntlet/nyx_gauntlet.py
ls -la GUIDE.md
```

## Verificação

```bash
./run.sh --gauntlet --only rapido
# Antes: 15/18 (3 FAILs)
# Depois: 18/18 (0 FAILs)
```

---

*"Baseline sujo é débito invisível." -- princípio de testes verdes*
