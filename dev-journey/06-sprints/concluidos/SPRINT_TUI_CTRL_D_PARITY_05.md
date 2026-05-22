## 0. SPEC (machine-readable)

```yaml
sprint:
  id: TUI-CTRL-D-PARITY-05
  title: "Ctrl+D em prompt vazio fecha TUI (paridade Unix EOF=quit), reusa shutdown de CTRL-Q-04"
  onda: 29
  prioridade: MÉDIA
  tipo: Feature
  dependencias: [TUI-CTRL-Q-OLLAMA-STOP-04]
  desbloqueia: []

  touches:
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/cli_keybindings.py
      reason: "Registrar @kb.add('c-d') condicional ao buffer estar vazio"
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/agent/repl_app.py
      reason: "Replicar binding c-d no KeyBindings local da Application"

  forbidden:
    - "Ctrl+D fechar TUI quando há texto no buffer (deve apenas deletar caractere forward ou ser noop)"
    - "Adicionar emoji"
    - "Menção a IA externa em código"

  tests:
    - cmd: "./run.sh --smoke"
      timeout: 60
      deve_passar: true

  acceptance_criteria:
    - "Ctrl+D em buffer vazio fecha TUI + chama ollama stop (mesmo fluxo de Ctrl+Q)"
    - "Ctrl+D com texto no buffer NÃO fecha TUI (deleta caractere forward ou noop, paridade readline)"
    - "Funciona em ambos os caminhos: Application e PromptSession legacy"
    - "Smoke + invariantes 14/14 PASS"
```

---

# Sprint TUI-CTRL-D-PARITY-05 — Ctrl+D = EOF quando buffer vazio

**Status:** PENDENTE
**Data criação:** 2026-05-21
**Modelo obrigatório:** claude-opus-4-7 (sem subagentes)

---

## Contexto do projeto (snapshot)

> - 35 tools, 67 commands. KeyBindings em `cli_keybindings.py` e `repl_app.py`.
> - Sprint anterior: TUI-CTRL-Q-OLLAMA-STOP-04 — registra Ctrl+Q com sentinel `"__quit__"` que dispara `run_quit_shutdown` (sudo wipe + ollama stop all + save_session).
> - Atualmente Ctrl+D no Application **não é mapeado** — quebra paridade Unix.

---

## Problema

Em terminais Unix, **Ctrl+D em prompt vazio = EOF = encerra o shell**. Padrão de zsh, bash, python REPL, ipython, etc. No Nyx-Code, Ctrl+D não faz nada na Application (atualmente sem binding). Usuários acostumados ao terminal pressionam Ctrl+D e ficam confusos.

Após CTRL-Q-04, temos o sentinel `"__quit__"` + handler completo (Ctrl+Q + ollama stop). Esta sprint reusa esse fluxo, com a condição **somente se buffer está vazio** (paridade readline).

---

## Solução proposta

Registrar `@kb.add("c-d")` que:
- Se `event.current_buffer.text == ""`: dispara `event.app.exit(result="__quit__")` (mesmo fluxo de Ctrl+Q).
- Caso contrário: comportamento default do readline (deleta caractere forward, ou se buffer vazio mas após texto deletado é EOF).

---

## Arquivos alvo

### `/home/andrefarias/Desenvolvimento/Nyx-Code/nyx/cli_keybindings.py`

**Adicionar (após o binding c-q da sprint anterior):**

```python
@kb.add("c-d")
def _quit_if_empty(event: object) -> None:
    """Ctrl+D em buffer vazio = EOF (paridade Unix). Caso contrário, deleta caractere forward."""
    buf = event.current_buffer  # type: ignore[attr-defined]
    if not buf.text:
        event.app.exit(result="__quit__")  # type: ignore[attr-defined]
    else:
        buf.delete()  # comportamento readline padrão
```

### `/home/andrefarias/Desenvolvimento/Nyx-Code/nyx/agent/repl_app.py`

**Adicionar binding paralelo no KeyBindings local (após o c-q da sprint anterior):**

```python
@kb.add("c-d")
def _quit_if_empty_app(event):
    buf = event.current_buffer
    if not buf.text:
        submit_state["submitted"] = True
        submit_state["text"] = "__quit__"
        try:
            get_app().exit(result="__quit__")
        except Exception as exc:
            logger.debug("c-d exit falhou: %s", exc)
    else:
        buf.delete()
```

---

## Diff esperado

```
~ 2 arquivos modificados
+ ~20 linhas (binding x2)
```

---

## Comandos de verificação

```bash
# 1. Smoke
./run.sh --smoke

# 2. Ctrl+D em buffer vazio fecha TUI
./run.sh &
TUI_PID=$!
sleep 5
xdotool key ctrl+d
sleep 3
kill -0 $TUI_PID 2>/dev/null && echo "FAIL: TUI ainda rodando" || echo "OK: TUI fechou"
ollama ps   # esperado: vazio (sprint anterior CTRL-Q-04 fez o stop)

# 3. Ctrl+D com texto NÃO fecha TUI
./run.sh &
TUI_PID=$!
sleep 5
xdotool type "abc"
xdotool key ctrl+d
sleep 2
kill -0 $TUI_PID 2>/dev/null && echo "OK: TUI ainda rodando" || echo "FAIL: TUI fechou indevidamente"
kill $TUI_PID

# 4. Caminho legacy
NYX_LEGACY_REPL=1 ./run.sh &
sleep 3
xdotool key ctrl+d
sleep 2
ollama ps   # esperado: vazio

# 5. Invariantes + acentuação
bash scripts/sprint_invariants.sh
python3 ~/.config/zsh/scripts/validar-acentuacao.py --paths nyx/cli_keybindings.py nyx/agent/repl_app.py
```

---

## Critério binário de aceite

- [ ] Ctrl+D em buffer vazio fecha TUI + executa ollama stop all
- [ ] Ctrl+D com texto NO buffer NÃO fecha TUI (deleta caractere ou noop)
- [ ] Funciona em ambos os caminhos (Application + legacy)
- [ ] `./run.sh --smoke` boot ok exit 0
- [ ] `bash scripts/sprint_invariants.sh` PASS 14/14
- [ ] Acentuação PT-BR rc=0

---

## Riscos

| Risco | Mitigação |
|-------|-----------|
| `buf.delete()` em buffer vazio lançar exceção | Verificar `if not buf.text` antes (já feito) |
| Usuário acostumado a Ctrl+D deletar caractere fica confuso | Comportamento é padrão Unix universal — se buffer vazio = EOF; caso contrário = forward-delete |
| Race: usuário deleta último caractere e Ctrl+D dispara EOF inesperado | Aceito — comportamento idêntico a bash/zsh; usuário se adapta |

---

*"Convenções Unix existem por bons motivos." -- princípio Nyx-Code paridade.*
