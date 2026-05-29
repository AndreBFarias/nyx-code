# SPEC

```yaml
sprint:
  id: TUI-DEFAULT-FLIP-LEGACY-RM-01
  title: "Flip NyxTUI como default + deletar legacy prompt_toolkit (~800L)"
  onda: 32
  prioridade: CRITICA
  tipo: Refactor
  dependencias: [TUI-SLASH-DISPATCH-MODAL-01]
  desbloqueia: []

  touches:
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/cli.py
      reason: "use_application dispara NyxTUI sempre; remove blink_loop, redirect setup, fallback PromptSession"
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/agent/output.py
      reason: "Remove _StdoutToBufferProxy, _RedirectStdoutToEmit, set_repl_app_output, clear_repl_app_output, _emit routing buffer"
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/cli_boot.py
      reason: "Remove run_select_modal (substituido por SelectScreen)"

  creates: []

  removes:
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/agent/repl_app.py
      reason: "Application prompt_toolkit substituida por NyxTUI Textual"
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/cli_keybindings.py
      reason: "KeyBindings prompt_toolkit substituidos por Textual BINDINGS"
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/agent/banner_blink.py
      reason: "blink_cursor_at substituido por BannerWidget.set_interval"

  forbidden:
    - "Manter import de Application/PromptSession em cli.py (exceto histórico mas removido)"
    - "Deixar referência a NYX_TUI_TEXTUAL (env removido; default é Textual)"
    - "Adicionar emoji"
    - "Mencionar IA externa" <!-- noqa-anonimato -->

  tests:
    - cmd: "./run.sh --smoke"
      timeout: 60
      deve_passar: true
    - cmd: "./venv/bin/python -c 'import os; assert not os.path.exists(\"nyx/agent/repl_app.py\"); assert not os.path.exists(\"nyx/cli_keybindings.py\"); assert not os.path.exists(\"nyx/agent/banner_blink.py\"); print(\"OK 3 legacy files deletados\")'"
      timeout: 30
      deve_passar: true
    - cmd: "./run.sh --gauntlet --only rapido"
      timeout: 300
      deve_passar: true
    - cmd: "./run.sh --gauntlet --only proxy"
      timeout: 300
      deve_passar: true

  acceptance_criteria:
    - "nyx/agent/repl_app.py deletado"
    - "nyx/cli_keybindings.py deletado"
    - "nyx/agent/banner_blink.py deletado"
    - "cli.py sem import de repl_app, cli_keybindings, banner_blink"
    - "cli.py default dispara NyxTUI (sem env NYX_TUI_TEXTUAL)"
    - "output.py sem _StdoutToBufferProxy, _RedirectStdoutToEmit, set_repl_app_output, clear_repl_app_output"
    - "cli_boot.py sem run_select_modal"
    - "Smoke ok + gauntlet rapido + gauntlet proxy + invariantes 14/14"
```

---

# Sprint TUI-DEFAULT-FLIP-LEGACY-RM-01 — Flip + delete legacy

**Status:** PENDENTE
**Data criação:** 2026-05-28
**Modelo obrigatório:** Modelo Opus 4.7 (1M) (sem subagentes)

---

## Contexto

> Sprints anteriores (1-6) entregaram NyxTUI Textual completo: CSS,
> ChatMessage, VerticalScroll, banner dock-top, agent bridge, slash dispatch
> + modais.
>
> Esta sprint troca default para NyxTUI e DELETA todos os arquivos legacy
> prompt_toolkit (~800L). Decisão do brainstorming: sem fallback NYX_LEGACY_REPL=1.
> Se algo regredir, `git revert` é a saída.

---

## Problema

cli.py ainda decide `use_application` baseado em `prompt_session is not None`
e dispatcha Application do prompt_toolkit. Caminhos legacy convivem como
fallback. Após esta sprint, NyxTUI é o caminho único.

---

## Solução proposta

1. `nyx/cli.py`:
   - Remover imports de `prompt_toolkit`, `cli_keybindings`, `build_app`,
     `set_repl_app_output`, etc.
   - Substituir bloco `use_application = ... ` por chamada direta a NyxTUI
   - Remover `_banner_blink_loop` async function
   - Remover bloco `if use_application and _tui_textual` (deixa só caminho NyxTUI)
   - Caminho default: instanciar NyxTUI(agent=agent, model=model, ...) e `await nyx_tui_app.run_async()`
2. Deletar:
   - `nyx/agent/repl_app.py`
   - `nyx/cli_keybindings.py`
   - `nyx/agent/banner_blink.py`
3. `nyx/agent/output.py`:
   - Remover classes `_StdoutToBufferProxy`, `_RedirectStdoutToEmit`
   - Remover funções `set_repl_app_output`, `clear_repl_app_output`, `redirect_stdout_to_emit`
   - Remover globais `_OUTPUT_BUFFER_REF`, `_APP_STATE_REF`
   - Simplificar `_emit` para sempre escrever em stdout (sem routing buffer)
   - Manter: RichOutput, render_*, NyxSpinner, _get_console, etc.
4. `nyx/cli_boot.py`:
   - Remover `run_select_modal` (SelectScreen na sprint 6 substitui)

---

## Arquivos alvo

### `/home/andrefarias/Desenvolvimento/Nyx-Code/nyx/cli.py`

Remoções principais:

**Remover imports:**
```python
from nyx.cli_keybindings import build_bottom_toolbar, build_keybindings, build_prompt_style
from nyx.cli_boot import run_select_modal
# ... outros imports prompt_toolkit indireto
```

**Remover variáveis e bloco PromptSession (linhas ~211-265):**
```python
prompt_session = None
history_path = Path.home() / ".nyx" / "history"
completer = None
kb = None
try:
    from prompt_toolkit import PromptSession
    ...
    prompt_session = PromptSession(...)
except ImportError:
    ...
```

**Remover dispatch `use_application` block (linhas 322-601) e substituir por:**

```python
# ONDA-32: NyxTUI é único caminho. Sem fallback prompt_toolkit.
from nyx.agent.tui.app import NyxTUI

if sys.stdin.isatty():
    nyx_tui_app = NyxTUI(
        model=model,
        tools_count=agent.tools_count,
        project_name=PROJECT_ROOT.name,
        slash_completer=[],
        settings=settings,
        agent=agent,
    )
    tui_result = await nyx_tui_app.run_async()
    if tui_result == "__quit__":
        render_quit_card(agent, app_state, PROJECT_ROOT)
        await run_quit_shutdown(proxy_url, logger)
    return
else:
    # Headless: cai no run_headless já existente (cli_headless.py)
    return await run_headless(agent, app_state, settings)
```

(Detalhes de cleanup e ordem de chamadas precisam preservar warmup,
maybe_offer_resume, etc. O executor deve agir cirurgicamente -- ler o cli.py
atual entre linhas 134 e 1054 antes de remover.)

### `/home/andrefarias/Desenvolvimento/Nyx-Code/nyx/agent/output.py`

Remover:
- `_OUTPUT_BUFFER_REF`, `_APP_STATE_REF` (globais)
- `set_repl_app_output`, `clear_repl_app_output` (funções)
- `_StdoutToBufferProxy`, `_RedirectStdoutToEmit` (classes)
- `redirect_stdout_to_emit` (função pública)
- Branches em `_emit` que verificam `repl_app_active` (deixa só stdout.write)

Manter intactos:
- `RichOutput`, `_fallback_output`, `_get_console`
- `render_user_input`, `render_assistant_start`, `render_assistant_end`
- `NyxSpinner`, `nyx_spinner`, `build_warming_label`
- `make_ask_permission`
- `print_error`
- `render_thinking_block`

### `/home/andrefarias/Desenvolvimento/Nyx-Code/nyx/cli_boot.py`

Remover função `run_select_modal` inteira. Outras funções (init_sandbox_roots,
render_quit_card, run_quit_shutdown, compute_prompt_str, shutdown_repl) ficam.

### Arquivos DELETADOS

```bash
rm nyx/agent/repl_app.py        # 778L
rm nyx/cli_keybindings.py       # ~tamanho a verificar
rm nyx/agent/banner_blink.py    # ~50L
```

---

## Diff esperado

```
- 3 arquivos removidos (~900L total)
~ 3 arquivos modificados (cli.py ~-300L; output.py ~-100L; cli_boot.py ~-50L)
~ Liquido: -1300 a -1500 linhas
```

---

## Comandos de verificação

```bash
cd /home/andrefarias/Desenvolvimento/Nyx-Code

# 1. Arquivos deletados
for f in nyx/agent/repl_app.py nyx/cli_keybindings.py nyx/agent/banner_blink.py; do
    test ! -f "$f" && echo "OK deletado: $f" || (echo "FAIL ainda existe: $f"; exit 1)
done

# 2. cli.py sem referências legacy
./venv/bin/python -c "
from pathlib import Path
src = Path('nyx/cli.py').read_text()
for tok in ('from nyx.cli_keybindings', 'from nyx.agent.repl_app', 'from nyx.agent.banner_blink', 'build_app(', '_banner_blink_loop', 'set_repl_app_output', 'NYX_TUI_TEXTUAL'):
    assert tok not in src, f'cli.py ainda referencia: {tok}'
print('OK cli.py sem legacy refs')
"

# 3. output.py sem proxies/redirect
./venv/bin/python -c "
from pathlib import Path
src = Path('nyx/agent/output.py').read_text()
for tok in ('_StdoutToBufferProxy', '_RedirectStdoutToEmit', 'set_repl_app_output', 'clear_repl_app_output', 'redirect_stdout_to_emit', '_OUTPUT_BUFFER_REF', '_APP_STATE_REF'):
    assert tok not in src, f'output.py ainda tem: {tok}'
print('OK output.py limpo')
"

# 4. cli_boot.py sem run_select_modal
./venv/bin/python -c "
from pathlib import Path
src = Path('nyx/cli_boot.py').read_text()
assert 'run_select_modal' not in src
print('OK cli_boot.py sem run_select_modal')
"

# 5. Smoke
./run.sh --smoke

# 6. Gauntlet por fase
./run.sh --gauntlet --only rapido
./run.sh --gauntlet --only proxy

# 7. Invariantes
bash scripts/sprint_invariants.sh

# 8. Acentuação
python3 ~/.config/zsh/scripts/validar-acentuacao.py --paths \
    nyx/cli.py nyx/agent/output.py nyx/cli_boot.py

# 9. Ruff
/home/andrefarias/.local/bin/ruff check nyx/
```

---

## Critério binário de aceite

- [ ] 3 arquivos deletados (repl_app.py, cli_keybindings.py, banner_blink.py)
- [ ] cli.py sem imports/refs legacy listados no comando #2
- [ ] cli.py default dispara NyxTUI (sem env)
- [ ] output.py sem proxies/redirect (comando #3)
- [ ] cli_boot.py sem run_select_modal
- [ ] Smoke ok + gauntlet rapido + gauntlet proxy
- [ ] Invariantes 14/14 PASS

---

## Proof-of-work obrigatório

Conforme template V2. Antes/Depois invariantes + outputs dos 5 gauntlets/comandos.

---

## Riscos

| Risco | Mitigação |
|-------|-----------|
| cli.py tem 1054 linhas; remoção surgical complexa | Executor deve ler cli.py inteiro antes de editar; preservar warmup + maybe_offer_resume + render_quit_card + shutdown_repl |
| run_headless (cli_headless.py) ainda usa PromptSession indireto | Validar separadamente; se sim, sprint follow-up TUI-HEADLESS-DETACH-01 |
| Algum import circular esconde dependência | `./venv/bin/python -c "import nyx.cli"` antes/depois para detectar |
| Gauntlet --only proxy falha por VRAM (flake conhecido RTX 3050) | Aceitar 13-18/18 conforme padrão INFRA-OOM-PATTERNS-KV-CACHE-01 |
| Após delete, alguns testes do gauntlet referem mock de repl_app | grep antes; se sim, ajustar fixtures |

---

*"O que não serve mais à vida deve cair." -- Heráclito (paráfrase)*
