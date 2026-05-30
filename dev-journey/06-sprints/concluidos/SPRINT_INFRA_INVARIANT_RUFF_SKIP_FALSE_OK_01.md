# SPRINT 302 — INFRA-INVARIANT-RUFF-SKIP-FALSE-OK-01

## 0. SPEC

```yaml
sprint:
  id: INFRA-INVARIANT-RUFF-SKIP-FALSE-OK-01
  title: "Fechar o falso [OK] do check #10 (ruff) em scripts/sprint_invariants.sh: resolver o ruff como binário (command -v ruff) OU módulo (python3 -m ruff), em vez de só o módulo — que dava 'pulado' (falso verde) quando ausente como módulo apesar do binário existir"
  onda: 34
  prioridade: BAIXA
  tipo: Infra
  dependencias: []
  desbloqueia: []

  origem: "Achado durante a SPRINT 298: o check #10 reportou [OK] 'ruff ausente (pulado)' nas validações das sprints 290-297 porque só tentava `python3 -m ruff` (instável conforme a ativação do venv); isso deixou o E501 introduzido na SPRINT 293 passar batido até o ruff reaparecer e bloquear (corrigido no hotfix `8990e14`)."

  touches:
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/scripts/sprint_invariants.sh
      reason: "Check #10: resolver RUFF_CMD preferindo o binário (command -v ruff), fallback para o módulo (python3 -m ruff); rodar `$RUFF_CMD check nyx/`; só pular (com mensagem honesta 'lint NÃO verificado') se ruff faltar em AMBAS as formas. Edição longe das definições de glifo (#14 self-check intacto)."
  creates: []
  removes: []

  forbidden:
    - "Tornar o check #10 FAIL quando ruff ausente (quebraria ambientes/CI sem ruff) — mantém pulado, mas honesto e raro"
    - "Tocar os glifos canônicos chr(0x25CB/D0/CF) do #14 (self-check anti-sanitizer exige >=3 cada)"
    - "Mudar a contagem de checks (segue 14, FAIL=0 = gate)"

  tests:
    - cmd: "bash -n scripts/sprint_invariants.sh"
      timeout: 10
      deve_passar: true
    - cmd: "bash scripts/sprint_invariants.sh"
      timeout: 60
      deve_passar: true

  acceptance_criteria:
    - "Com o binário ruff no PATH, o #10 RODA o ruff (mensagem 'via ruff'), não 'pulado'"
    - "Fallback para `python3 -m ruff` quando o binário falta mas o módulo existe"
    - "Pula só se ambos faltarem, com mensagem 'lint NÃO verificado; instale ruff'"
    - "#14 self-check preservado (CB/D0/CF >= 3); invariantes 14/14; bash -n OK"
```

## 1. PROOF-OF-WORK (CONCLUIDA — 2026-05-30)

**Causa-raiz:** o check #10 só tentava `python3 -m ruff --version`. Esse caminho depende da
ativação do venv e flutuava entre runs (sprint 291 viu "pulado"; mais tarde "reclama"). O binário
`~/.local/bin/ruff` está sempre no PATH, mas o check o ignorava. Resultado: quando o módulo estava
ausente, dava um falso `[OK] "pulado"` (contava como PASS), e lint-debt (o E501 da 293) passava.

**Fix:** resolver `RUFF_CMD` preferindo `command -v ruff` (binário, estável), com fallback
`python3 -m ruff`; rodar `$RUFF_CMD check nyx/`. Só cai no `else` (pulado, com mensagem honesta
"lint NÃO verificado; instale ruff") se ruff faltar em AMBAS as formas. NÃO vira FAIL no ausente
(preserva portabilidade/CI sem ruff); apenas deixa de ser um falso-verde silencioso.

**Validação:**
- `bash -n scripts/sprint_invariants.sh`: sintaxe OK.
- `bash scripts/sprint_invariants.sh`: **`[OK] 10. ruff check nyx/ (via ruff)`** (resolveu o
  binário e RODOU — antes era "pulado"), PASS 14, FAIL 0.
- `#14` self-check anti-sanitizer preservado: CB=6, D0=6, CF=6 (>=3 cada).
- `validar-acentuacao` (scripts/sprint_invariants.sh): rc 0 (comentário acentuado conforme estilo do script).
- `./run.sh --gauntlet --only rapido`: APROVADO.

**Efeito:** o check #10 passa a ser estável e a cobrir o lint de fato neste ambiente (e em qualquer
um com ruff binário OU módulo), fechando a janela que deixou o E501 da 293 escapar.
