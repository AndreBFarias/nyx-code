# SPRINT TUI-REDESIGN-28-01 — Boot silencioso + capitalização "Sessão Iniciada"

## 0. SPEC

```yaml
sprint:
  id: TUI-REDESIGN-28-01
  title: "Boot phase 100% silencioso no terminal interativo; mensagens [nyx] viram log-only; endmark capitalizado 'Sessão Iniciada'"
  onda: 28
  bloco: 28.1 TUI paridade Claude Code
  prioridade: ALTA
  tipo: UX
  dependencias: []
  desbloqueia: [TUI-REDESIGN-28-06]
  origem: "Feedback do usuário 2026-05-18: 5 linhas [nyx] no boot poluem terminal ('próxima sprint', 'VRAM insuficiente', 'Aquecendo modelo', 'VRAM livre < 1500', 'Modelo aquecido'). Devem virar log apenas."

  touches:
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/run.sh
      reason: "linhas 355, 384, 386, 406, 506, 542: trocar log_ok/log_warn/log_nyx por log_boot (gravação em logs/boot.log apenas)"
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/run.sh
      reason: "linha 654: endmark vira 'Sessão Iniciada' (capital S, capital I)"
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/themes/design_tokens.py
      reason: "linha 103: GLYPHS_BOOT['endmark'] = '─── Sessão Iniciada ───'"
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/scripts/sprint_invariants.sh
      reason: "se invariante #14 conta codepoint da string antiga, atualizar para nova"

  forbidden:
    - "Silenciar log_err (problemas críticos devem aparecer)"
    - "Remover gravação em logs/boot.log (preservar histórico para debug)"
    - "Quebrar modo --smoke, --gauntlet, --menu"

  tests:
    - cmd: "./run.sh --smoke"
      timeout: 60
      deve_passar: "boot ok"
    - cmd: "bash scripts/sprint_invariants.sh | tail -3"
      timeout: 60
      deve_passar: "PASS=14 FAIL=0 (ou 15/15 se conta da nova string for adicionada)"
    - cmd: "grep -E 'log_(ok|warn|nyx)' run.sh | grep -E 'VRAM|Aquecendo|Modelo aquecido|próxima sprint' || echo 'limpo'"
      timeout: 5
      deve_passar: "limpo (sem matches)"
    - cmd: "grep 'Sessão Iniciada' nyx/themes/design_tokens.py run.sh"
      timeout: 5
      deve_passar: "2 matches mínimo"

  acceptance_criteria:
    - "./run.sh em TTY interativo mostra apenas '─── Sessão Iniciada ───' + banner + prompt (zero linhas [nyx] antes)"
    - "logs/boot.log recebe as 5+ linhas suprimidas (gravação preservada)"
    - "log_err continua falando alto no terminal (não silenciado)"
    - "Endmark capitalizado em 'Sessão Iniciada' (não 'sessão iniciada') tanto em run.sh quanto design_tokens.py"
    - "./run.sh --smoke = boot ok"
    - "bash scripts/sprint_invariants.sh = PASS=14 FAIL=0 (ou 15/15 com bump)"

  proof_of_work:
    - "Antes/depois: capture stdout de ./run.sh em ambiente TTY (use script ou expect) e compare contagem de linhas '[nyx]' (esperado: antes >= 5, depois = 0)"
    - "tail -20 logs/boot.log após boot mostra entries gravadas (Aquecendo, VRAM, próxima sprint)"
```

---

# Sprint TUI-REDESIGN-28-01

**Status:** CONCLUIDA
**Data criação:** 2026-05-18
**Data conclusão:** 2026-05-18
**Modelo obrigatório:** claude-opus-4-7

## Rollback

`git reset --hard HEAD~1`
