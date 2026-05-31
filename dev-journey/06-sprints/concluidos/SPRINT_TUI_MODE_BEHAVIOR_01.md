# SPRINT 308 — TUI-MODE-BEHAVIOR-01

## 0. SPEC (machine-readable)

```yaml
sprint:
  id: TUI-MODE-BEHAVIOR-01
  title: "Shift+Tab com comportamento real (normal/plan/sudo/bypass), nao so o label"
  onda: 35
  prioridade: ALTA
  tipo: Bugfix
  dependencias: []
  desbloqueia: []
  decisao_usuario: "4 modos com sentidos distintos (AskUserQuestion 2026-05-30): sudo = elevacao real (SUDO-MODE-01), bypass = auto-aprovar permissao"

  touches:
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/agent/permissions.py
      reason: "PermissionChecker.set_bypass() -- auto-aprova CONFIRM_ONCE em runtime"
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/agent/tui/app.py
      reason: "_apply_mode() liga plan_mode/sudo_session/bypass ao cycle; on_mount reseta para normal"
  creates: []
  removes: []

  forbidden:
    - "Adicionar emoji / mencao a IA / except silencioso / print fora de cli-output"
    - "Quebrar o agente (gauntlet proxy)"

  acceptance_criteria:
    - "plan: agente planeja sem executar (tools de escrita bloqueadas)"
    - "bypass: CONFIRM_ONCE auto-aprovado; ALWAYS_CONFIRM e DENY intactos"
    - "sudo: elevacao real ativada (SUDO-MODE-01)"
    - "Modos exclusivos; boot reseta para normal"
    - "Smoke + invariantes 14/14 + gauntlet rapido APROVADO"
```

---

**Status:** CONCLUIDA
**Data criação:** 2026-05-30
**Data conclusão:** 2026-05-30
**Modelo obrigatório:** claude-opus-4-7 (sem subagentes)

---

## Problema

`Shift+Tab` ciclava o LABEL do modo no footer (normal → plan → sudo → bypass) mas o **comportamento** do agente era sempre "normal" (`action_cycle_mode` só setava `toolbar.mode`). O modo não era propagado ao `AgentLoop`, `PermissionChecker`, `plan_mode` nem `sudo_session`. Invisível à validação por injeção.

## Decisão do usuário (AskUserQuestion 2026-05-30)

**4 modos com sentidos distintos:** `sudo` = elevação real (SUDO-MODE-01, pede senha), `bypass` = auto-aprovar permissões (igual `--auto-approve`). Os dois conceitos são separados.

## Achado-chave

Os três mecanismos **já existiam isolados** — só não estavam ligados ao cycle da TUI Textual (eram acionados por outros caminhos antes da migração ONDA-32): `plan_mode.set_plan_mode` (loop já respeita em `_iteration.py:104` via `is_tool_allowed_in_plan_mode`), `sudo_session.set_active` (SUDO-MODE-01) e o `PermissionChecker`. A 308 é a **religação**.

## Fix

1. `permissions.py`: `PermissionChecker.set_bypass(on)` + flag `_bypass`; no `check()`, `bypass OR NYX_AUTO_APPROVE` promove CONFIRM_ONCE → AUTO. DENY e ALWAYS_CONFIRM intactos (mesma garantia do `--auto-approve`).
2. `app.py`: `_apply_mode(mode)` chamado por `action_cycle_mode` — `plan`→`set_plan_mode(True)`; `sudo`→`sudo_session.set_active(True)` (+ wipe ao sair); `bypass`→`agent.permissions.set_bypass(True)`; `normal`→desliga os três. Modos exclusivos. `on_mount` chama `_apply_mode("normal")` (reseta singletons de módulo de sessões anteriores).

## Proof-of-work

```
FAIL_BEFORE=0 -> FAIL_AFTER=0 (14/14)   ruff: All checks passed!   acentuacao: rc=0
gauntlet --only rapido: 19/19 (100%) APROVADO  (agente/PermissionChecker sem regressao)
```
**Pilot (`/tmp/val_308_modes.py`):** ciclo Shift+Tab → `normal(F,F,F) → plan(plan_mode=T) → sudo(sudo_active=T, plan=F) → bypass(bypass=T, sudo wipe) → normal(tudo F)`; exclusividade confirmada; boot reseta para normal. PermissionChecker real: `edit_file` CONFIRM_ONCE→AUTO sob bypass, `run_command` ALWAYS_CONFIRM intacto; `is_tool_allowed_in_plan_mode`: read_file True / edit_file False.
**--web real (playwright, Shift+Tab digitado):** footer ciclou `shift+tab: normal/plan/sudo/bypass` → `[plan] read-only` → `[sudo] elevado` → `bypass ON` (buffer `.xterm-rows`), disparando `_apply_mode` no caminho real.

## Ressalva / refinamento opcional

A **senha do sudo** continua sendo fornecida pelo fluxo `/sudo enable` (getpass no tty / `NYX_SUDO_PASSWORD` em headless) — o `Shift+Tab` para `sudo` ativa o estado de elevação e, sem senha cacheada, exibe `notify("Forneça a senha com /sudo enable")`. Um **modal de senha Textual dedicado** disparado pelo próprio `Shift+Tab` é um refinamento futuro (não bloqueante: o modo sudo é real, não cosmético). Catalogar como `TUI-SUDO-PASSWORD-MODAL-01` se o usuário quiser a senha pedida diretamente no cycle.

## Critério de aceite

- [x] plan planeja sem executar (escrita bloqueada); bypass auto-aprova CONFIRM_ONCE; sudo ativa elevação.
- [x] Modos exclusivos; boot reseta para normal.
- [x] Smoke + invariantes 14/14 + gauntlet 19/19; ruff/acentuação limpos.
- [x] Validado: Pilot (comportamento) + --web (ciclo digitando Shift+Tab).

---

*"Um modo que não muda o comportamento é só uma etiqueta. Agora a etiqueta tem dentes." -- anônimo*
