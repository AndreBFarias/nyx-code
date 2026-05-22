## 0. SPEC (machine-readable)

```yaml
sprint:
  id: TUI-CTRL-Q-OLLAMA-STOP-04
  title: "Ctrl+Q fecha TUI imediatamente + executa ollama stop em todos os modelos rodando"
  onda: 29
  prioridade: ALTA
  tipo: Feature
  dependencias: []
  desbloqueia: [TUI-CTRL-D-PARITY-05]

  touches:
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/cli_keybindings.py
      reason: "Registrar @kb.add('c-q') que sai com sentinel __quit__"
      linhas_alvo: "237-255"
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/agent/repl_app.py
      reason: "Replicar binding c-q no KeyBindings local da Application"
      linhas_alvo: "252-410"
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/cli_boot.py
      reason: "Adicionar ollama stop all em shutdown_repl() após end_session do Analytics"
      linhas_alvo: "214-260"
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/cli.py
      reason: "Garantir que sentinel __quit__ do Application.exit() entra no handler de quit"
      linhas_alvo: "525-540"

  forbidden:
    - "Pedir confirmação antes de fechar (decisão de design: Ctrl+Q é imediato)"
    - "Parar apenas o modelo da sessão (decisão: TODOS os modelos via ollama ps)"
    - "Bloquear shutdown se ollama stop falhar (best-effort, log warning)"
    - "Adicionar emoji"
    - "Menção a IA externa em código"

  tests:
    - cmd: "./run.sh --smoke"
      timeout: 60
      deve_passar: true

  acceptance_criteria:
    - "Pressionar Ctrl+Q na TUI Application fecha imediatamente (≤300ms)"
    - "Pressionar Ctrl+Q no caminho legacy PromptSession fecha imediatamente"
    - "Após Ctrl+Q, `ollama ps` retorna lista vazia (todos os modelos parados)"
    - "Se ollama CLI não está instalado, shutdown segue sem erro (log warning apenas)"
    - "Smoke + invariantes 14/14 PASS"
```

---

# Sprint TUI-CTRL-Q-OLLAMA-STOP-04 — Ctrl+Q + ollama stop all

**Status:** PENDENTE
**Data criação:** 2026-05-21
**Modelo obrigatório:** claude-opus-4-7 (sem subagentes)

---

## Contexto do projeto (snapshot)

> - 35 tools, 67 commands. Modelo qwen2.5-coder:3b carregado via Ollama porta 11435.
> - KeyBindings da TUI definidas em 2 lugares: `nyx/cli_keybindings.py:build_keybindings()` (PromptSession legacy) e `nyx/agent/repl_app.py:build_app()` (Application full-screen).
> - Atualmente saída é só via `/quit` (sentinel `"__quit__"` retornado pelo command). KeyBindings têm `c-o`, `c-up`, `enter`, `c-j`, `/`, `tab`, `s-tab`, `c-v` — sem `c-q` nem `c-d`.
> - Shutdown ordenado em `nyx/cli_boot.py:shutdown_repl()`: wipe sudo cache → cancela tasks → analytics.end_session → save_session → agent.close. **Não chama ollama stop.**

---

## Problema

Pressionar **Ctrl+Q** não faz nada — convenção Unix universal (fechar app de terminal) está ausente. Pior: o modelo Ollama carregado (`qwen2.5-coder:3b`, ~2GB VRAM) continua na memória mesmo depois de sair via `/quit`, ocupando recurso até `ollama ps` listar e o usuário rodar `ollama stop` manualmente.

**Decisão de design (usuário 2026-05-21):**
- **Ctrl+Q:** imediato, sem confirmação.
- **Escopo do stop:** **todos** os modelos rodando (não só o atual). TUI Nyx-Code é o cliente único do Ollama na máquina-padrão.

---

## Solução proposta

1. Registrar `@kb.add("c-q")` em `cli_keybindings.py` (legacy) e no `KeyBindings` local de `repl_app.py` (Application).
2. Ambos os handlers chamam `event.app.exit(result="__quit__")` — reusa fluxo de `/quit` existente.
3. Em `shutdown_repl()`, após o `analytics.end_session()` e antes do `save_session`, listar modelos via `ollama ps` e parar cada um via `ollama stop <model>`.

---

## Arquivos alvo

### `/home/andrefarias/Desenvolvimento/Nyx-Code/nyx/cli_keybindings.py` (após linha 237)

**Adicionar:**

```python
@kb.add("c-q")
def _quit_immediate(event: object) -> None:
    """Ctrl+Q: fecha REPL imediatamente. Shutdown ordenado roda em cli.py
    (sudo wipe, analytics.end_session, ollama stop all, save_session, agent.close)."""
    event.app.exit(result="__quit__")  # type: ignore[attr-defined]
```

### `/home/andrefarias/Desenvolvimento/Nyx-Code/nyx/agent/repl_app.py` (dentro do `KeyBindings` local linhas 252-409)

**Adicionar binding paralelo:**

```python
@kb.add("c-q")
def _quit_immediate_app(event):
    submit_state["submitted"] = True
    submit_state["text"] = "__quit__"
    try:
        get_app().exit(result="__quit__")
    except Exception as exc:
        logger.debug("c-q exit falhou: %s", exc)
```

### `/home/andrefarias/Desenvolvimento/Nyx-Code/nyx/cli_boot.py` (após `analytics.end_session()` linha ~253)

**Adicionar:**

```python
# Parar TODOS os modelos Ollama rodando no shutdown (libera VRAM).
# Decisão de design: TUI Nyx-Code é cliente único do Ollama na máquina padrão.
try:
    import subprocess
    result = subprocess.run(
        ["ollama", "ps"], capture_output=True, text=True, timeout=3
    )
    lines = result.stdout.splitlines()
    # primeira linha é header (NAME, ID, SIZE, ...); restante são modelos rodando.
    for line in lines[1:]:
        parts = line.split()
        if not parts:
            continue
        model = parts[0]
        try:
            subprocess.run(
                ["ollama", "stop", model], timeout=5, check=False
            )
        except (subprocess.TimeoutExpired, FileNotFoundError, OSError) as exc:
            logger.warning("ollama stop %s falhou: %s", model, exc)
except (subprocess.TimeoutExpired, FileNotFoundError, OSError) as exc:
    logger.warning("ollama ps falhou (modelos não parados): %s", exc)
```

### `/home/andrefarias/Desenvolvimento/Nyx-Code/nyx/cli.py` (linhas ~525-540, handler de `result == "__quit__"`)

**Verificar (não modificar se já correto):**

```python
if result == "__quit__":
    render_quit_card(agent, app_state, PROJECT_ROOT)
    await run_quit_shutdown(proxy_url, logger)
    break
```

**Garantir que** o sentinel vindo de `event.app.exit(result="__quit__")` (Ctrl+Q via Application) chega aqui da mesma forma que vinha do command `/quit`. Caso não chegue (porque `app.exit()` retorna do `run_async` em vez de devolver string via slash command), adicionar branch que mapeia `event.app.exit()` → mesma execução do `__quit__`.

---

## Diff esperado

```
~ 4 arquivos modificados
+ ~40 linhas (binding x2 + ollama stop loop + handler check)
- 0 linhas
```

---

## Comandos de verificação

```bash
# 1. Smoke
./run.sh --smoke

# 2. Modelo Ollama carregado em background
ollama run qwen2.5-coder:3b "ping" &
sleep 3
ollama ps   # deve listar qwen2.5-coder:3b

# 3. TUI + Ctrl+Q
./run.sh &
TUI_PID=$!
sleep 5
xdotool key ctrl+q
sleep 3
ollama ps   # esperado: vazio (zero modelos rodando)
kill -0 $TUI_PID 2>/dev/null && echo "FAIL: TUI ainda rodando" || echo "OK: TUI fechou"

# 4. Caminho legacy
NYX_LEGACY_REPL=1 ./run.sh &
sleep 3
xdotool key ctrl+q
sleep 2
ollama ps   # esperado: vazio

# 5. Sem Ollama instalado (simular FileNotFoundError)
PATH= ./run.sh --smoke   # boot deve passar mesmo sem ollama no PATH

# 6. Invariantes + acentuação
bash scripts/sprint_invariants.sh
python3 ~/.config/zsh/scripts/validar-acentuacao.py --paths nyx/cli_keybindings.py nyx/agent/repl_app.py nyx/cli_boot.py
```

---

## Critério binário de aceite

- [ ] Ctrl+Q na Application fecha em ≤300ms
- [ ] Ctrl+Q no legacy fecha em ≤300ms
- [ ] `ollama ps` após Ctrl+Q lista vazia
- [ ] Shutdown sem `ollama` no PATH não trava (warning no log)
- [ ] `./run.sh --smoke` boot ok exit 0
- [ ] `bash scripts/sprint_invariants.sh` PASS 14/14
- [ ] Acentuação PT-BR rc=0
- [ ] Nenhuma violação de forbidden[]

---

## Riscos

| Risco | Mitigação |
|-------|-----------|
| `ollama ps` formato muda entre versões | Parsing tolerante: split + skip linhas vazias, primeira coluna = nome |
| `ollama stop` em modelo já parado erro | `check=False` ignora exit code; warning não bloqueante |
| Ctrl+Q durante tool em execução perde trabalho | Aceito pela decisão de design "Ctrl+Q imediato". Trabalho em curso é cancelado via `cancel()` em pending tasks (já existe em shutdown_repl) |
| `event.app.exit()` na Application não retornar string para o loop | Caso ocorra, adicionar handler que detecta `KeyboardInterrupt` ou retorno None do run_async e invoca render_quit_card + run_quit_shutdown |
| Modelo carregado por OUTRA sessão Nyx em paralelo for parado | Aceito pela decisão. Comportamento documentado no card de quit |

---

*"Ao deixar, deixe limpo." -- princípio Nyx-Code shutdown.*
