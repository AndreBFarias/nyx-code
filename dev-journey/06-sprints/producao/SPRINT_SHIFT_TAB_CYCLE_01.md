# SPRINT SHIFT-TAB-CYCLE-01 — Shift+Tab cicla normal → plan → sudo → bypass

## 0. SPEC

```yaml
sprint:
  id: SHIFT-TAB-CYCLE-01
  title: "Tecla Shift+Tab cicla 4 modos (normal/plan/sudo/bypass) em vez de toggle binario"
  onda: 24
  bloco: 24.8 Escopo expandido
  prioridade: ALTA
  tipo: Feature
  dependencias: [UX-CLAUDE-PARITY-01, SUDO-MODE-01]
  desbloqueia: [confianca em automacao]
  origem: "Pedido do usuario 2026-05-18: 'O shift tab Precisa ter o modo /plan e o modo sudo que permite ele executar comandos sudo no terminal'."

  touches:
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/cli.py
      reason: "@kb.add('s-tab') deixa de ser toggle e vira cycle de 4 estados"
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/agent/output.py
      reason: "_bottom_toolbar mostra estado atual com cor distinta"
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/dev-journey/03-decisions/ADR_026_AGENCIA.md
      reason: "Atualizar secao 'Bypass toggle' para descrever os 4 modos"

  forbidden:
    - "Quebrar modo bypass atual (precisa continuar acessivel)"
    - "Ativar sudo mode sem senha (cache de senha eh outra sprint)"
    - "Permitir cycling fora do REPL (headless ignora)"

  tests:
    - cmd: "echo 'manual: rode ./run.sh, aperte shift+tab 4 vezes, veja footer ciclar'"
      timeout: 5

  acceptance_criteria:
    - "Estado 1 (default): normal -- toolbar mostra glifo padrao"
    - "Estado 2: plan mode -- icone roxo, write/exec bloqueados (read-only)"
    - "Estado 3: sudo mode -- icone vermelho, exec aceita 'sudo' (precisa SUDO-MODE-01)"
    - "Estado 4: bypass -- icone amarelo + fundo roxo (ADR-029 atual)"
    - "Shift+Tab cicla 1->2->3->4->1"
    - "Footer reativo mostra modo corrente"
    - "/help shift-tab mostra os 4 modos"
    - "Smoke + invariantes 14/14"
```

---

# Sprint SHIFT-TAB-CYCLE-01

**Status:** PENDENTE
**Data criação:** 2026-05-18
**Modelo obrigatório:** claude-opus-4-7

---

## Contexto

Hoje shift+tab toggles binario bypass on/off (UX-CLAUDE-PARITY-01).
O usuario quer paridade maior com Claude Code: ciclo de modos para
escolher comportamento da proxima request:

1. **Normal**: comportamento padrao (permissoes + sandbox).
2. **Plan**: read-only, agente PLANEJA antes de executar. Equivalente
   a `/plan` command existente, mas via tecla rapida.
3. **Sudo**: agente pode rodar `sudo X` em run_command (precisa
   SUDO-MODE-01 para cachear senha).
4. **Bypass**: comportamento atual; pula CONFIRM_ONCE silenciosamente.

## Solucao proposta

### nyx/cli.py keybinding

```python
_MODES = ["normal", "plan", "sudo", "bypass"]

@kb.add("s-tab")
def _cycle_mode(event):
    cur = app_state.get("mode", "normal")
    idx = _MODES.index(cur)
    nxt = _MODES[(idx + 1) % len(_MODES)]
    app_state["mode"] = nxt
    app_state["bypass"] = (nxt == "bypass")
    app_state["plan_mode"] = (nxt == "plan")
    app_state["sudo_mode"] = (nxt == "sudo")
```

### nyx/agent/output.py::_bottom_toolbar

```python
mode = app_state.get("mode", "normal")
glyph = {"normal": "  ", "plan": "▸▸", "sudo": "▸▸", "bypass": "▸▸"}[mode]
color = {"normal": NYX_MUTED, "plan": NYX_PURPLE, "sudo": NYX_ERROR, "bypass": NYX_PURPLE}[mode]
parts.append((f"bg:{color} fg:{NYX_PRIMARY} bold", f" {glyph} {mode} "))
```

### Help inline

`/?` em qualquer estado mostra: "shift+tab cicla normal->plan->sudo->bypass".

## Criterio binario

- [ ] 4 estados cicleiros
- [ ] Toolbar reativa
- [ ] Mode persistido em app_state
- [ ] Plan integra com `/plan` existente (plan_mode.py)
- [ ] Sudo aguarda SUDO-MODE-01 implementada
- [ ] Smoke + invariantes 14/14
- [ ] Commit `feat(SHIFT-TAB-CYCLE-01): shift+tab cicla 4 modos`

---

*"Tecla unica, mente afiada por contexto." -- SHIFT-TAB-CYCLE-01*
