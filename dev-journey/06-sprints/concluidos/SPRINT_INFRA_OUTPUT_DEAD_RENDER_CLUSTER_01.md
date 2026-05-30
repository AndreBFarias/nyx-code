# SPRINT 293 — INFRA-OUTPUT-DEAD-RENDER-CLUSTER-01

## 0. SPEC

```yaml
sprint:
  id: INFRA-OUTPUT-DEAD-RENDER-CLUSTER-01
  title: "Reverificar e marcar como legado o cluster de funções render_* de módulo órfãs em nyx/agent/output.py descoberto durante a SPRINT 292 — incluindo agora scripts/ na varredura (a 292 só cobriu nyx/)"
  onda: 34
  prioridade: BAIXA
  tipo: Infra/Auditoria
  dependencias: [TUI-OUTPUT-CAPITALIZATION-AUDIT-01]
  desbloqueia: []

  origem: "Achado colateral da SPRINT 292: a auditoria-irmã de render_footer apontou +5 funções render_* candidatas a órfãs em output.py. A estimativa da 292 só varreu nyx/."

  touches:
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/agent/output.py
      reason: "Marcar [MORTO — zero chamadores] na docstring das 3 funções confirmadas mortas (render_progress_bar, render_todo_block, render_tool_card_end); nenhuma mudança em código executável."
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/dev-journey/06-sprints/concluidos/SPRINT_TUI_OUTPUT_CAPITALIZATION_AUDIT_01.md
      reason: "Corrigir o registro da 292 (+5 → +3) com nota da reverificação."
  creates: []
  removes: []

  forbidden:
    - "Tocar render_tool_card_start ou render_diff — REVERIFICADAS como VIVAS (usadas pelo gauntlet em scripts/); marcá-las de morto seria falso"
    - "Deletar qualquer função — GUIDE #3: código morto se menciona, não se deleta"
    - "Tocar qualquer arquivo de scripts/ (gauntlet) — só leitura para confirmar uso"
    - "Tocar código executável de output.py (só docstrings)"

  tests:
    - cmd: "./run.sh --smoke"
      timeout: 15
      deve_passar: true
    - cmd: "bash scripts/sprint_invariants.sh"
      timeout: 60
      deve_passar: true
    - cmd: "./run.sh --gauntlet --only rapido"
      timeout: 300
      deve_passar: true

  acceptance_criteria:
    - "render_tool_card_start e render_diff NÃO tocadas (confirmadas vivas no gauntlet)"
    - "render_progress_bar, render_todo_block, render_tool_card_end marcadas [MORTO — zero chamadores]"
    - "Registro da 292 corrigido de +5 para +3 com a nota de reverificação"
    - "py_compile output.py OK; zero código executável tocado; gauntlet P7V-01 (render_diff) continua verde"
```

## 1. AUDITORIA (CONCLUIDA — 2026-05-30)

**Reverificação (varredura `nyx/` + `scripts/`, exclui `def` e símbolos `_render_*`):**

| Função | Refs externas | Veredito |
|--------|---------------|----------|
| `render_progress_bar` | 0 | **MORTA** → marcada |
| `render_todo_block` | 0 | **MORTA** → marcada |
| `render_tool_card_end` | 0 (já `[DEPRECATED]`) | **MORTA** → marcador aditado |
| `render_tool_card_start` | 3 (scripts/gauntlet/fixtures/loop_benchmark.py) | **VIVA** → intocada |
| `render_diff` | 5 (scripts/gauntlet/nyx_gauntlet.py P7V-01) | **VIVA** → intocada |

**Lição:** a estimativa "+5" da 292 era um falso-positivo de escopo — varrer só `nyx/`
ignora os consumidores em `scripts/gauntlet/`. A varredura de deadness DEVE incluir
`scripts/`. (O `render_footer` da 292 foi reconfirmado morto também contra `scripts/`.)

**Ação:** as 3 mortas receberam `[MORTO — zero chamadores; mantido por GUIDE #3]` na
primeira linha da docstring (consistente com o marcador de render_footer na 292).
`render_tool_card_end` já tinha `[DEPRECATED em TUI-REDESIGN-25-10]`; o marcador de
morte foi aditado ao existente. Zero código executável tocado.

**Validação:**
- `python3 -m py_compile nyx/agent/output.py`: OK.
- `validar-acentuacao.py --paths nyx/agent/output.py`: rc 0.
- `git diff output.py`: 3+/3- (só primeira linha de 3 docstrings).
- `./run.sh --smoke`: boot OK.
- `bash scripts/sprint_invariants.sh`: 14/14 (FAIL=0).
- `./run.sh --gauntlet --only rapido`: APROVADO. `render_tool_card_start` e
  `render_diff` ficaram **byte-idênticas** (não tocadas — só docstrings de SIBLINGS
  mudaram), logo seus testes de gauntlet (loop_benchmark, P7V-01) ficam inalterados
  por construção. (P7V-01 vive na suíte visual, fora do `--only rapido`.)
