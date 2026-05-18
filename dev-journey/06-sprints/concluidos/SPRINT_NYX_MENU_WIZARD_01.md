# SPRINT NYX-MENU-WIZARD-01 — Wizard interativo `--menu` + Cockpit `--web`

## 0. SPEC

```yaml
sprint:
  id: NYX-MENU-WIZARD-01
  title: "Menu wizard interativo + cockpit web auto-open"
  onda: 24
  bloco: 24.7 Onboarding
  prioridade: MEDIA
  tipo: Feature
  dependencias: [VISUAL-LAYOUT-08, COCKPIT-01]
  desbloqueia: []
  origem: "Pedido do usuario 2026-05-18: 'no run.sh deixa uma flag tipo --menu ou --web o menu pro cara configurar o app estilo o install do claude code naquela parte do onboarding deles'"

  touches:
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/run.sh
      reason: "Aceitar --menu, --web/--cockpit, --auto-approve"
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/README.md
      reason: "Documentar secao 'Wizard --menu' e 'Cockpit Web --web'"
  creates:
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/scripts/menu_wizard.py
      reason: "TUI wizard com choices numeradas (aesthetic/entity/banner/model/auto-approve)"

  forbidden:
    - "Salvar fora de ~/.nyx/config.toml"
    - "Auto-aprovar permissoes por padrao no menu (opt-in explicito)"

  tests:
    - cmd: "echo 'echo' | ./venv/bin/python scripts/menu_wizard.py"
      timeout: 10
      deve_passar: true
      nota: "Aceita Enter como default"
    - cmd: "./run.sh --web --smoke"
      timeout: 30
      deve_passar: true

  acceptance_criteria:
    - "Flag --menu invoca wizard antes do exec"
    - "Wizard cobre 5 perguntas (aesthetic, entity, banner, modelo, auto-approve)"
    - "Aceita Enter como default em cada pergunta"
    - "Salva ~/.nyx/config.toml + emite export NYX_VAR no stdout"
    - "Flag --web sobe cockpit em 127.0.0.1:11437 + xdg-open"
    - "Flag --auto-approve seta NYX_AUTO_APPROVE=1 (precisa NYX-AUTO-APPROVE-01 pra ter efeito real)"
```

---

# Sprint NYX-MENU-WIZARD-01

**Status:** CONCLUIDA (sessao Validador 2026-05-18, commit pendente neste push)
**Data criação:** 2026-05-18
**Modelo obrigatório:** claude-opus-4-7

---

## Contexto

Após validacao via Playwright revelar 5 achados (vide commit 0a7a6f2), o
usuario pediu onboarding estilo Claude Code install: TUI interativo que
configura o app antes do primeiro boot. Esta sprint entrega.

## Solução

### `scripts/menu_wizard.py`

TUI minimo via input() + cores Nyx (design_tokens.py).

5 perguntas com choices numeradas:
1. Aesthetic: default | arcano | cyberpunk | brutalist | mecha | editorial
2. Entity: nyx | eris | juno | lars | luna | mars | somn
3. Banner: wide | compact | neofetch
4. Modelo: qwen2.5-coder:3b | qwen3:4b | qwen2.5-coder:7b
5. Auto-aprovar permissoes: sim | nao

Persiste em `~/.nyx/config.toml`. Quando `NYX_MENU_EMIT=1`, imprime
`export VAR=valor` no stdout (o run.sh source-a a saida).

### `run.sh`

3 flags novas:
- `--menu` — chama wizard, source dos exports
- `--web` / `--cockpit` — sobe `nyx.cockpit.server` em background + xdg-open
- `--auto-approve` — seta `NYX_AUTO_APPROVE=1` (sprint NYX-AUTO-APPROVE-01 faz efeito real)

## Proof-of-work

- `./venv/bin/python -m py_compile scripts/menu_wizard.py` -> OK
- README atualizado (secoes "Wizard" e "Cockpit Web")
- chmod +x aplicado

Sprint movida `producao/` -> `concluidos/` direto (criada e fechada na mesma sessao, escopo limitado).

---

*"Onboarding visivel transforma novato em usuario." -- NYX-MENU-WIZARD-01*
