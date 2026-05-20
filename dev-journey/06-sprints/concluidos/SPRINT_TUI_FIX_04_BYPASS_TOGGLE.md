## 0. SPEC (machine-readable)

```yaml
sprint:
  id: TUI-FIX-04
  title: "Shift+Tab alterna bypass permissions (toolbar dinâmica)"
  touches:
    - path: nyx/cli.py
      reason: "Keybinding s-tab; estado compartilhado; bottom_toolbar do PromptSession"
    - path: nyx/agent/permissions.py
      reason: "PermissionChecker aceita modo 'bypass' que retorna AUTO para tudo (exceto deny rules)"
    - path: nyx/agent/output.py
      reason: "render_bypass_status opcional"
  n_to_n_pairs:
    - "Se bypass_mode=True, PermissionChecker.check retorna AUTO salvo deny list; se False, comportamento atual"
    - "Toolbar sempre reflete bypass_mode via invalidate()"
  forbidden:
    - "Bypass ignora rules 'deny' (rm -rf *, sudo *) -- nunca ignorar deny"
    - "Persistir bypass entre sessões (deve ser stateful só na sessão atual)"
    - "Shift+Tab capturar focus ou fechar popup aberto"
  tests:
    - cmd: "./run.sh --gauntlet --only controle"
      timeout: 60
    - cmd: "manual: ./run.sh, Shift+Tab, ver toolbar 'bypass permissions on'; Shift+Tab de novo, some"
      timeout: 30
  acceptance_criteria:
    - "Shift+Tab alterna entre bypass_mode True/False"
    - "Bottom toolbar mostra ' bypass permissions ON' em cor distintiva quando ativo"
    - "Sem bypass: prompt de confirmação [S/n] aparece para edit_file/write_file/run_command/write_memory"
    - "Com bypass: sem prompts; tools executam direto"
    - "Rules de deny (rm -rf *, sudo *) continuam bloqueando mesmo com bypass"
    - "Ao sair (Ctrl+D) e reabrir, bypass inicia OFF"
    - "Indicação visual clara (cor ou emoji-like prefixo) pra usuário não esquecer que está ativo"
```

---

# Sprint TUI-FIX-04 -- Shift+Tab toggle de bypass

**Status:** CONCLUIDA (header corrigido em MASTER-CLEANUP-02 2026-05-20; presença em concluidos/ implica CONCLUIDA conforme convenção do projeto)
**Data:** 2026-04-17
**Prioridade:** MÉDIA
**Tipo:** Feature (pedida pelo usuário como padrão Claude Code)
**Dependências:** --
**Desbloqueia:** --

---

## Problema / Contexto

Screenshot 11 do usuário mostra `bypass permissions on (shift+tab to cycle)` aparecendo no rodapé. Essa é uma feature do Claude Code CLI que o usuário usa como referência. No Nyx atual, a feature NÃO está implementada -- a mensagem vista na screenshot vem de outra camada (host shell, provavelmente).

O usuário quer a feature como nativa. É o padrão de Claude Code: dev que confia no agent pressiona Shift+Tab e entra em modo "sem prompts" -- toda tool auto-aprova. Pressiona de novo pra sair.

## Implementação

### Fase 1 -- Estado compartilhado

Adicionar em `cli.py` no escopo do `run_repl`:

```python
app_state = {"bypass_mode": False}
```

### Fase 2 -- Keybinding s-tab

Em `cli.py`, no `KeyBindings` existente:

```python
@kb.add('s-tab')
def _toggle_bypass(event):
    app_state["bypass_mode"] = not app_state["bypass_mode"]
    event.app.invalidate()  # Força redraw do toolbar
```

### Fase 3 -- Bottom toolbar dinâmica

PromptSession aceita `bottom_toolbar=callable`. Criar:

```python
def get_bottom_toolbar():
    if app_state["bypass_mode"]:
        return FormattedText([('fg:ansiyellow bold', '  bypass permissions ON ')])
    return [('', '')]  # vazio quando off

prompt_session = PromptSession(
    ...
    bottom_toolbar=get_bottom_toolbar,
)
```

Nota: isso substitui nosso footer atual? Não -- o footer que mostra `ctx/model/iter` é `render_footer` que é `print()` antes do prompt. Bottom_toolbar é uma linha EXTRA **abaixo** do prompt, dentro do PromptSession. Convivem.

### Fase 4 -- Integrar com on_permission

Em `cli.py`, a callback `on_permission`:

```python
def on_permission(perm_level, tool_name, args) -> bool:
    if app_state["bypass_mode"]:
        logger.info("[bypass] auto-approving %s", tool_name)
        return True  # auto-aprova
    # ... prompt [S/n] atual ...
```

**ATENÇÃO**: deny rules em `permissions.py` (`deny: ["run_command:rm -rf *", "run_command:sudo *"]`) são checadas ANTES do `on_permission`. Ou seja, bypass NÃO anula deny. Isso é segurança obrigatória. Validar que `_is_denied` é chamado primeiro.

### Fase 5 -- Indicador no prompt

Opcional: mudar cor do `nyx>` pra amarelo quando bypass ON, reforçando visualmente.

## Verificação

```bash
./run.sh
# Shift+Tab
# Ver rodapé " bypass permissions ON" em amarelo
# digitar "cria arquivo teste.txt com 'oi'"  -- deve executar SEM prompt [S/n]
# Shift+Tab de novo
# rodapé some
# digitar outra write -- prompt [S/n] volta

# Teste de segurança
# Shift+Tab (bypass on)
# "roda rm -rf ." -- deve SER bloqueado mesmo assim (deny rule)

./run.sh --gauntlet --only controle
```

- [ ] Shift+Tab toggle funciona
- [ ] Rodapé aparece e some
- [ ] Auto-aprovação em bypass
- [ ] Deny rules ainda bloqueiam
- [ ] Bypass reseta entre sessões
- [ ] Cor distintiva
- [ ] Gauntlet controle passa

---

*"A liberdade exige responsabilidade." -- Jean-Paul Sartre*
