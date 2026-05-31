# SPRINT 305 — TUI-FOOTER-CAPITALIZE-TERMS-01

## 0. SPEC (machine-readable)

```yaml
sprint:
  id: TUI-FOOTER-CAPITALIZE-TERMS-01
  title: "Capitalizar termos do footer da TUI (estado do modelo + Shift+Tab/modos)"
  onda: 35
  prioridade: BAIXA
  tipo: Bugfix
  touches:
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/agent/tui/widgets/toolbar.py
      reason: "render(): capitalizar model_state e os labels de modo (display only)"
  acceptance_criteria:
    - "○ cold -> ○ Cold (e Warming/Warm)"
    - "shift+tab: normal/plan/sudo/bypass -> Shift+Tab: Normal/Plan/Sudo/Bypass"
    - "self.mode (logica) e model_state (chave) seguem minusculos"
    - "smoke + invariantes 14/14 + gauntlet rapido APROVADO"
```

---

**Status:** CONCLUIDA
**Data criação:** 2026-05-30
**Data conclusão:** 2026-05-30
**Modelo obrigatório:** claude-opus-4-7 (sem subagentes)

---

## Problema

Footer/toolbar com termos minúsculos: `○ cold` e `shift+tab: normal/plan/sudo/bypass` (e os labels de modo ativo).

## Fix

`toolbar.py render()`: `self.model_state.capitalize()` no display (Cold/Warming/Warm) — o reactive segue minúsculo (chave de `STATE_GLYPHS` e da lógica). Bloco do modo capitalizado: `Shift+Tab: Normal/Plan/Sudo/Bypass`, ` Bypass ON (Shift+Tab) `, ` [Plan] read-only (Shift+Tab) `, ` [Sudo] elevado (Shift+Tab) `. O reactive `self.mode` (usado pela lógica da 308) permanece minúsculo; só o texto exibido muda.

## Proof-of-work

```
FAIL_BEFORE=0 -> FAIL_AFTER=0 (14/14)   ruff: All checks passed!   acentuacao: rc=0
gauntlet --only rapido: 19/19 (100%) APROVADO
```
**--web real (buffer `.xterm-rows`):** footer = `Ctx 0% | qwen2.5-coder:3b | Iter 0 | Lidos 0 | Modif 0 | ○ Cold | VRAM 64/4096 MiB    Shift+Tab: Normal/Plan/Sudo/Bypass`. Ciclo de modo (308) confirmado capitalizado: `[Plan] read-only`, `[Sudo] elevado`, `Bypass ON`.

## Critério de aceite

- [x] `○ Cold` e `Shift+Tab: Normal/Plan/Sudo/Bypass` no footer (validado --web).
- [x] Lógica intacta (mode/model_state minúsculos); gauntlet 19/19; ruff/acentuação limpos.

---

*"Maiúscula é respeito pela leitura." -- anônimo*
