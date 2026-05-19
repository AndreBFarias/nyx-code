# SPRINT TUI-REDESIGN-27-01 — Suggester theme Nyx (Style.from_dict)

## 0. SPEC

```yaml
sprint:
  id: TUI-REDESIGN-27-01
  title: "PromptSession ganha style=_build_prompt_style() mapeando theme_manager hex para completion-menu + bottom-toolbar"
  onda: 27
  bloco: 27.1 Refinamento visual prompt_toolkit
  prioridade: ALTA
  tipo: UX
  dependencias: [TUI-REDESIGN-26-05]
  desbloqueia: [TUI-REDESIGN-27-03]
  origem: "Feedback do usuário pós-Onda 26 (imagem 6): popup de slash command com cores amarelo/cinza padrão; deveria usar accent turquesa + roxo Nyx."

  touches:
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/cli.py
      reason: "Importar Style; novo helper _build_prompt_style() que monta dict a partir de theme_manager; passar style= no PromptSession(...)"

  forbidden:
    - "Hardcode hex fora de design_tokens*"
    - "Quebrar bottom toolbar atual (FormattedText)"

  tests:
    - cmd: "bash scripts/sprint_invariants.sh"
      timeout: 60
      deve_passar: "14/14"
    - cmd: "./venv/bin/python -c 'from prompt_toolkit.styles import Style; print(Style.from_dict({\"completion-menu.completion\":\"bg:#007a63 fg:#e8e8e8\"}))'"
      timeout: 5
      deve_passar: "Style instanciado sem erro"

  acceptance_criteria:
    - "PromptSession recebe style= compatível com Style.from_dict"
    - "Classes mapeadas: completion-menu.completion, completion-menu.completion.current, completion-menu.meta.*, bottom-toolbar"
    - "Cores vêm de theme_manager.resolve_palette() (NYX_AESTHETIC + NYX_ENTITY)"
    - "Popup do completer mostra fundo accent_lo + selecionado em accent forte (não amarelo)"
    - "Smoke ok + invariantes 14/14"
```

---

# Sprint TUI-REDESIGN-27-01

**Status:** CONCLUIDA
**Data criação:** 2026-05-18
**Data conclusão:** 2026-05-18
**Modelo obrigatório:** claude-opus-4-7

## Rollback

`git reset --hard HEAD~1`
