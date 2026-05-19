# SPRINT TUI-REDESIGN-28-05 — First-run wizard completo (7 passos integrados)

## 0. SPEC

```yaml
sprint:
  id: TUI-REDESIGN-28-05
  title: "First-run dispara wizard de 7 passos: nome + aesthetic + entity + schema + banner + modelo + auto_approve"
  onda: 28
  bloco: 28.1 TUI paridade Claude Code
  prioridade: ALTA
  tipo: Feature
  dependencias: []
  desbloqueia: []
  origem: "Feedback do usuário 2026-05-18: 'Falta o wizards config e fala o user definir o nome dele também'. Hoje menu_wizard só roda com --menu; onboarding só pergunta nome."

  touches:
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/agent/onboarding.py
      reason: "Novo entry-point run_first_run_wizard() que integra pergunta de nome + chama main() do menu_wizard"
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/scripts/menu_wizard.py
      reason: "main() aceita parâmetro existing_name; quando None, adiciona passo 01 'nome' no início (total 7); quando passado, mantém 6 passos"
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/cli.py
      reason: "boot do REPL: se should_run_tutorial() -> chamar run_first_run_wizard() em vez de run_first_time_tutorial()"

  forbidden:
    - "Disparar wizard em pipe/CI/headless (preservar guard sys.stdin.isatty)"
    - "Sobrescrever config.toml existente sem merge não-destrutivo"
    - "Quebrar ./run.sh --menu (deve continuar funcionando como 6 passos sem 'nome')"
    - "Disparar wizard se ~/.nyx/.first_run_done já existe"

  tests:
    - cmd: "./run.sh --smoke"
      timeout: 60
      deve_passar: "boot ok (smoke é headless, wizard pula)"
    - cmd: "rm -f ~/.nyx/.first_run_done ~/.nyx/config.toml; echo -e 'TestUser\\n\\n\\n\\n\\n\\n\\nsim\\n' | timeout 30 ./run.sh 2>&1 | tail -20 | grep -c 'configuração salva'"
      timeout: 40
      deve_passar: ">= 1"
    - cmd: "test -f ~/.nyx/config.toml && grep -c 'user_display_name' ~/.nyx/config.toml"
      timeout: 5
      deve_passar: "1"

  acceptance_criteria:
    - "rm ~/.nyx/.first_run_done ~/.nyx/config.toml && ./run.sh -> wizard com 7 passos sequenciais"
    - "Passo 01/07 pergunta 'Como devo te chamar?' (default = git config user.name ou 'visitante')"
    - "Passos 02-07: aesthetic, entity, schema, banner_mode, model, auto_approve (já existentes no menu_wizard)"
    - "~/.nyx/config.toml ao fim contém: user_display_name + aesthetic + entity + schema + banner_mode + model + auto_approve"
    - "Segunda execução não dispara wizard (.first_run_done bloqueia)"
    - "./run.sh --menu continua mostrando 6 passos (sem 'nome' que já foi setado)"
    - "Smoke ok"

  proof_of_work:
    - "rm -f ~/.nyx/.first_run_done ~/.nyx/config.toml; capturar saída de ./run.sh com input simulado via heredoc; conferir 7 prompts numerados (01/07..07/07)"
    - "cat ~/.nyx/config.toml mostra 7 chaves (user_display_name + 6 do menu_wizard)"
```

---

# Sprint TUI-REDESIGN-28-05

**Status:** CONCLUIDA
**Data criação:** 2026-05-18
**Data conclusão:** 2026-05-18
**Modelo obrigatório:** claude-opus-4-7

## Rollback

`git reset --hard HEAD~1`
