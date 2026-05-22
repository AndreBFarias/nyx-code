## 0. SPEC (machine-readable)

```yaml
sprint:
  id: TUI-INPUT-DEADLOCK-01
  title: "Destravar input do BufferControl no REPL Application (input não aceita digitação)"
  onda: 29
  prioridade: CRÍTICA
  tipo: Bugfix
  dependencias: [TUI-STATE-GLYPHS-SYNC-06]
  desbloqueia: []

  touches:
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/agent/repl_app.py
      reason: "Garantir foco e drenagem de stdin antes do run_async; possível ajuste no Layout"
      linhas_alvo: "229-486"
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/cli.py
      reason: "Mover termios.tcflush para antes do Application.run_async() (atualmente roda antes do banner)"
      linhas_alvo: "385-460"

  forbidden:
    - "Mudar layout visual da TUI (banner, prompt, toolbar)"
    - "Quebrar fallback PromptSession (NYX_LEGACY_REPL=1)"
    - "Adicionar emoji"
    - "Menção a IA externa em código"

  tests:
    - cmd: "./run.sh --smoke"
      timeout: 60
      deve_passar: true
    - cmd: "./run.sh --gauntlet --only rapido"
      timeout: 600
      deve_passar: true

  acceptance_criteria:
    - "Usuário consegue digitar texto no prompt > do REPL Application imediatamente após boot"
    - "xdotool type 'oi' captura no input_buffer e visualmente aparece no rodapé"
    - "Fallback NYX_LEGACY_REPL=1 continua funcionando (smoke pass com essa env)"
    - "Smoke + invariantes 14/14 + gauntlet rapido PASS"
```

---

# Sprint TUI-INPUT-DEADLOCK-01 — Destravar input do REPL

**Status:** PENDENTE
**Data criação:** 2026-05-21
**Modelo obrigatório:** claude-opus-4-7 (sem subagentes)

---

## Contexto do projeto (snapshot)

> - Python 3.10+, modelo qwen2.5-coder:3b porta 11435, proxy 11436.
> - 35 tools, 67 commands. `nyx/agent/repl_app.py` ~510 linhas (Application full-screen via prompt_toolkit, sub-sprint TUI-REDESIGN-28-08c-PARTE-3).
> - Sprint anterior: TUI-STATE-GLYPHS-SYNC-06 (resolve divergência _STATE_GLYPHS, candidato a causa raiz deste bug).

---

## Problema

Ao iniciar `./run.sh`, a TUI sobe corretamente, banner aparece, mas o usuário **não consegue digitar nada** no prompt `>` do rodapé. Teclas pressionadas não aparecem no `BufferControl`. A TUI fica visualmente inerte até `Ctrl+C` ou kill externo.

**Sintoma observável (screenshot 2026-05-21):**
- Status bar: `ctx 9% (1162/12000tok) | iter 0 | lidos 0 | modif 0 | cold`
- Cursor visível no rodapé (`> ▌`) — mas não responde ao teclado.

**Investigação prévia (Explore agent 2026-05-21):**
- `BufferControl` definido em `repl_app.py:425-429` com `focusable=True`.
- `input_buffer` em `repl_app.py:229-235`.
- Layout HSplit com `focused_element=input_window` (linha 476) — correto.
- Hipótese 1 (mais forte): `_STATE_GLYPHS = {"cold": " ", ...}` (linha 95) com **espaços vazios** corrompe encoding do toolbar e bloqueia render → resolvido em `TUI-STATE-GLYPHS-SYNC-06`.
- Hipótese 2: `termios.tcflush` em `cli.py:391` roda **antes** do banner (linha 311), e descarta keystrokes do cold-start; precisa rodar **antes** do `Application.run_async()` (linha após 480).
- Hipótese 3: race de foco — em startup lento, layout pronto antes do run_async, primeiras teclas perdidas.

---

## Solução proposta

Investigação em 3 passos:

1. **Passo 1:** após TUI-STATE-GLYPHS-SYNC-06 estar CONCLUIDA, repro em runtime via `./run.sh` + captura `validacao-visual` (xdotool type "ola" + scrot). Se input aceitar, esta sprint vira "sprint de verificação" — apenas documenta o fix indireto.  <!-- noqa-acento (validacao-visual nome canônico do plugin, BRIEF §CORE) -->

2. **Passo 2 (se ainda falha):** mover `termios.tcflush(sys.stdin.fileno(), termios.TCIFLUSH)` de `cli.py:391` para **imediatamente antes** de `await repl_app.run_async()` (linha após 480), preservando o tratamento de não-tty.

3. **Passo 3 (se ainda falha):** adicionar callback `on_app_ready` que força `app.layout.focus(input_window)` quando a Application monta.

---

## Arquivos alvo

### `/home/andrefarias/Desenvolvimento/Nyx-Code/nyx/cli.py` (linhas ~385-455)

**Antes (linha 386-398):**
```python
if sys.stdin.isatty():
    try:
        import termios
        try:
            termios.tcflush(sys.stdin.fileno(), termios.TCIFLUSH)
        except (termios.error, OSError) as exc:
            logger.warning("termios.tcflush falhou: %s", exc)
    except ImportError as exc:
        logger.debug("termios indisponível (plataforma não-POSIX): %s", exc)
```

**Depois (mover este bloco para imediatamente antes de `repl_app.run_async()`):**
```python
if use_application:
    try:
        from prompt_toolkit.history import FileHistory as _FH
        from nyx.agent.output import set_repl_app_output
        from nyx.agent.repl_app import append_to_buffer, build_app
        repl_app, repl_output_buffer, repl_input_buffer = build_app(...)
        # ... pre-popula banner ...
        # NOVO: drenar stdin imediatamente antes de transferir controle pro prompt_toolkit
        if sys.stdin.isatty():
            try:
                import termios
                termios.tcflush(sys.stdin.fileno(), termios.TCIFLUSH)
            except (termios.error, OSError, ImportError) as exc:
                logger.warning("termios.tcflush pré-run_async falhou: %s", exc)
```

### `/home/andrefarias/Desenvolvimento/Nyx-Code/nyx/agent/repl_app.py` (linhas ~470-486)

**Se passo 3 for necessário, adicionar antes do `return app, output_buffer, input_buffer`:**

```python
def _force_focus() -> None:
    try:
        app.layout.focus(input_window)
    except Exception as exc:
        logger.debug("force focus on app_ready falhou: %s", exc)

# Registrar callback que dispara assim que a Application está pronta.
# Idempotente: se foco já está no input_window, no-op silencioso.
app.before_render += lambda _app: _force_focus()
```

---

## Diff esperado

```
~ 2 arquivos modificados
+ ~15 linhas (drenagem reposicionada + possível callback de foco)
- ~10 linhas (drenagem antiga)
```

---

## Comandos de verificação

```bash
# 1. Smoke
./run.sh --smoke

# 2. Validação visual: digitar e ver aparecer
./run.sh &
sleep 5
xdotool type "ola mundo"
sleep 1
scrot /tmp/input_test.png
# inspecionar /tmp/input_test.png — deve mostrar "ola mundo" no prompt

# 3. Fallback legacy
NYX_LEGACY_REPL=1 ./run.sh --smoke

# 4. Gauntlet rapido
./run.sh --gauntlet --only rapido

# 5. Invariantes
bash scripts/sprint_invariants.sh

# 6. Acentuação
python3 ~/.config/zsh/scripts/validar-acentuacao.py --paths nyx/agent/repl_app.py nyx/cli.py
```

---

## Critério binário de aceite

- [ ] `xdotool type "ola"` após boot mostra texto no input_buffer (validação visual)
- [ ] `./run.sh --smoke` boot ok exit 0
- [ ] `NYX_LEGACY_REPL=1 ./run.sh --smoke` boot ok exit 0 (fallback preservado)
- [ ] `./run.sh --gauntlet --only rapido` PASS 100%
- [ ] `bash scripts/sprint_invariants.sh` PASS 14/14
- [ ] Acentuação PT-BR rc=0
- [ ] Nenhuma violação de forbidden[]

---

## Riscos

| Risco | Mitigação |
|-------|-----------|
| Após SYNC-06 o bug some sozinho | Esta sprint vira "verificação" — só documenta no SPRINT_ORDER_MASTER que SYNC-06 resolveu |
| Mudar drenagem de stdin quebra cold-start em CI/headless | Manter check `sys.stdin.isatty()` antes |
| `app.before_render` não existir nesta versão de prompt_toolkit | Fallback: registrar callback via `app.invalidate()` no `Application.__init__` |
| Foco já estar correto antes do callback | Idempotente — `app.layout.focus()` é no-op se já está no destino |

---

*"A primeira tecla deve ser sagrada." -- princípio TUI Nyx-Code.*
