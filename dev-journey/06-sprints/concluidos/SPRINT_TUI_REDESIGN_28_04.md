# SPRINT TUI-REDESIGN-28-04 — Suggester Enter abre lista quando vazio

## 0. SPEC

```yaml
sprint:
  id: TUI-REDESIGN-28-04
  title: "Digitar '/' + Enter abre popup de completion (com 1º item selecionado) em vez de submeter '/' inválido"
  onda: 28
  bloco: 28.1 TUI paridade Claude Code
  prioridade: MÉDIA
  tipo: UX
  dependencias: []
  desbloqueia: []
  origem: "Feedback do usuário 2026-05-18: 'o command suggester se eu der enter e não tiver nada selecionado, ele então vai pra seleção padrão ativa a lista pra eu escolher'."

  touches:
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/cli.py
      reason: "_submit handler (linhas 212-231): adicionar branch quando texto.lstrip()=='/' e sem completion ativa -> buf.start_completion(select_first=True) e return (não validate_and_handle)"

  forbidden:
    - "Quebrar caminho atual (texto='/comando args' + Enter aplica completion + submete)"
    - "Auto-abrir popup quando texto sem '/' (não-comando)"
    - "Submeter '/' literal como comando inválido"

  tests:
    - cmd: "./run.sh --smoke"
      timeout: 60
      deve_passar: "boot ok"
    - cmd: "bash scripts/sprint_invariants.sh | tail -3"
      timeout: 60
      deve_passar: "PASS=14 FAIL=0"
    - cmd: "grep -A 20 '@kb.add(\"enter\")' nyx/cli.py | head -25"
      timeout: 5
      deve_passar: "código contém branch para texto == '/' OR sem completions"

  acceptance_criteria:
    - "Sessão real: digitar '/' + Enter -> popup abre com primeiro comando selecionado (ex: /aesthetic em accent)"
    - "Sessão real: digitar '/he' + Enter -> submete '/help' (comportamento atual preservado)"
    - "Sessão real: digitar 'olá' + Enter -> submete 'olá' como mensagem normal (não abre popup)"
    - "Smoke + invariantes ok"

  proof_of_work:
    - "Capture xdotool simulando digitar '/' + Return; capturar tela via 'import -window'; conferir presença do popup visível com primeiro item em accent"
    - "Capture xdotool digitando '/he' + Return; conferir tela mostra '/help' executando (não popup)"
```

---

# Sprint TUI-REDESIGN-28-04

**Status:** CONCLUIDA
**Data criação:** 2026-05-18
**Data conclusão:** 2026-05-18
**Modelo obrigatório:** claude-opus-4-7

## Rollback

`git reset --hard HEAD~1`
