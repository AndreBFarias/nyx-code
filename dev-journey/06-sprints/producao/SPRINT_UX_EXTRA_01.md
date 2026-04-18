## 0. SPEC

```yaml
sprint:
  id: UX-EXTRA-01
  title: "Editar último user input (atalho Ctrl+Up ou / edit)"
  onda: 22
  bloco: 8
  prioridade: BAIXA
  tipo: Feature
  dependencias: [DEPLOY-02]

  touches:
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/cli.py
      reason: "Keybinding Ctrl+Up puxa último user input para edição"
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/agent/commands/session.py (ou onde estiver)
      reason: "Novo /edit carrega último user_input no buffer"

  absorve:
    - "O-09 (editar último user input)"

  forbidden:
    - "Corromper o histórico prompt_toolkit (FileHistory)"
    - "Permitir editar input já processado pelo agent (só reedita ANTES de reenviar)"

  tests:
    - cmd: "python -c 'from nyx.agent.commands import get_command; print(get_command(\"edit\") is not None)'"
      esperado: "True"
    - cmd: "./run.sh --gauntlet --only tui"
      deve_passar: true

  acceptance_criteria:
    - "Ctrl+Up no prompt vazio carrega último input no buffer (editável)"
    - "/edit ou /e também carrega último input no buffer"
    - "Se não há último input: mensagem 'Nenhum input anterior' (não crasha)"
    - "Enter envia texto editado como NOVA mensagem (mantendo histórico)"
    - "Gauntlet tui passa"
```

---

# Sprint UX-EXTRA-01 — Editar último user input

## Contexto

- Oportunidade O-09: usuário digita frase longa, percebe erro, quer editar em vez de redigitar.
- Bash tem `!!`; Claude Code tem seta-pra-cima com edição. Nyx deve ter.

## Solução

### `nyx/cli.py` — keybinding Ctrl+Up

Manter registro do último user_input em `app_state`:

```python
app_state["last_user_input"] = ""
# depois do prompt_session.prompt_async retornar:
if user_input and not user_input.startswith("/"):
    app_state["last_user_input"] = user_input
```

Keybinding:

```python
@kb.add("c-up")
def _load_last_input(event: object) -> None:
    buf = event.current_buffer
    last = app_state.get("last_user_input", "")
    if not last:
        # feedback via bottom_toolbar seria ideal; alternativa:
        from prompt_toolkit.application import run_in_terminal
        run_in_terminal(lambda: print(f"  {DIM}Nenhum input anterior{NC}"))
        return
    if buf.document.text.strip():
        # preservar: anexar, não substituir
        return
    buf.text = last
    buf.cursor_position = len(last)
```

### Comando `/edit`

```python
@nyx_command(name="edit", description="Edita seu último input antes de reenviar", aliases=["e"], category="sessão")
def cmd_edit(_args: str, _root: str) -> str:
    return "__edit_last__"
```

Em `cli.py`, tratar result:

```python
if result == "__edit_last__":
    last = app_state.get("last_user_input", "")
    if not last:
        print(f"  {DIM}Nenhum input anterior para editar.{NC}")
        continue
    # Próximo loop: pré-popula buffer
    app_state["prefill"] = last
    continue
```

E no prompt async, usar `default=` quando prefill existe:

```python
prefill = app_state.pop("prefill", None)
if prompt_session:
    user_input = (await prompt_session.prompt_async(ANSI(prompt_str), default=prefill or "")).strip()
```

## Comando de verificação

```bash
cd /home/andrefarias/Desenvolvimento/Nyx-Code

# 1. Comando /edit registrado
python -c "
from nyx.agent.commands import get_command
c = get_command('edit')
assert c is not None, '/edit não registrado'
print('edit OK')
"

# 2. Keybinding existe
grep -c 'c-up\|c_up' nyx/cli.py
# esperado: >= 1

./run.sh --gauntlet --only tui
```

## Critério binário

- [ ] `/edit` e `/e` registrados
- [ ] Keybinding Ctrl+Up no cli.py
- [ ] `app_state["last_user_input"]` atualizado após submit
- [ ] Teste manual: digitar "oi mundo", enviar; novo prompt vazio; Ctrl+Up → "oi mundo" aparece
- [ ] Teste manual: `/edit` → prompt prefillado com último input
- [ ] Se não há input anterior: mensagem "Nenhum input anterior"
- [ ] Gauntlet tui passa
- [ ] Commit: `feat: edita ultimo user input via Ctrl+Up ou /edit`

## Guardrails anti-engodo

**NÃO marque como concluída se:**
- `/edit` dá "Comando desconhecido".
- Ctrl+Up insere `^[[1;5A` literal em vez de trigger.
- Last input nunca persiste (app_state não atualizado).

## Validação humana

```bash
./run.sh
# nyx> oi mundo
# (aguardar resposta)
# nyx> (prompt vazio) Ctrl+Up
# → "oi mundo" aparece no prompt
# editar para "oi mundo!" e enter → nova pergunta

# nyx> /edit
# → "oi mundo!" prefillado
```

---

*"A melhor pergunta raramente é a primeira — é a primeira editada." -- anônimo*
