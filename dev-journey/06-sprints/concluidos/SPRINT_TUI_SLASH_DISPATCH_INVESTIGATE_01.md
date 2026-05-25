# SPRINT 223 — TUI-SLASH-DISPATCH-INVESTIGATE-01

## 0. SPEC (machine-readable)

```yaml
sprint:
  id: TUI-SLASH-DISPATCH-INVESTIGATE-01
  title: "Reproduzir + corrigir slash commands não responsivos no REPL Application"
  onda: 31
  prioridade: ALTA
  tipo: Bugfix
  dependencias: []
  desbloqueia: []

  touches:
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/agent/repl_app.py
      reason: "Provável site do bug (linhas 299-308 _slash + 297 validate_and_handle)"
      linhas_alvo: "270-330"
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/cli_handlers.py
      reason: "Dispatcher pode não acionar sentinelas no caminho Application"
      linhas_alvo: "920-960"
  creates: []
  removes: []

  forbidden:
    - "Tocar em sprints 184-207 da ONDA-29/30 (já CONCLUIDAS)"
    - "Marcar CONCLUIDA sem reproduzir o bug 1 vez + sem ver fix passando"
    - "Adicionar emoji"
    - "Mencao a IA proprietaria em codigo/commit"   # noqa-anonimato

  tests:
    - cmd: "./run.sh --smoke"
      timeout: 10
      deve_passar: true
    - cmd: "./run.sh --gauntlet --only rapido"
      timeout: 120
      deve_passar: true

  acceptance_criteria:
    - "Fase 1: causa-raiz documentada com file:line ANTES de qualquer Edit"
    - "/help renderiza tabela de commands em REPL interativo"
    - "/status mostra runtime info"
    - "/quit dispara __quit__ sentinela + shutdown gracioso (não regredir 188)"
    - "Captura visual (3 screenshots: /help, /status, /quit) demonstra"
    - "Smoke boot ok"
    - "Invariantes 14/14 PASS"
    - "Gauntlet --only rapido APROVADO"
```

---

# Sprint 223 — TUI-SLASH-DISPATCH-INVESTIGATE-01

**Status:** CONCLUIDA
**Data criação:** 2026-05-25
**Data conclusão:** 2026-05-25
**Modelo obrigatório:** claude-opus-4-7 (sem subagentes)

---

## Causa-raiz (Fase 1)

Em modo Application (`nyx/agent/repl_app.py:523` -- `full_screen=True`), `sys.stdout`
fica capturado pela tela do prompt_toolkit. Handlers de slash em
`nyx/cli_handlers.py` (`_handle_status:85`, `_handle_clear:64`, `_handle_context:102`,
etc.) e `RichOutput._render` em `nyx/agent/output.py:233-266` escrevem via
`print()`/`Console.print()` direto em stdout -- **resultado: output invisível**
enquanto `dispatch_sync`/`dispatch_async` rodam dentro do loop
`await repl_app.run_async()` em `nyx/cli.py:530`.

Reprodução empírica via tmux:
- `tmux send-keys -t nyx_repro "/help" Enter` -> input limpo pós-Enter (Application
  fez submit, próximo turno iterando), **mas nenhum output renderizado** no buffer.
- Mesmo pattern em `/status`. `/quit` "parece funcionar" porque tem path próprio
  (`render_quit_card` + `run_quit_shutdown` em `cli.py:587-591`) e Application
  já saiu quando o card desenha.

Função canônica de roteamento `_emit` em `output.py:115-143` JÁ EXISTE e detecta
corretamente `repl_app_active=True` para rotear via `append_to_buffer`, mas
**NÃO é usada por RichOutput._render nem pelos handlers que fazem print() direto**.

## Fix cirúrgico (Fase 2)

Em vez de refatorar ~20 handlers individualmente (risco enorme), 2 arquivos:

1. `nyx/agent/output.py` +92L: classe `_StdoutToBufferProxy` (file-like que captura
   writes e roteia via `append_to_buffer`) + context manager `_RedirectStdoutToEmit`
   + função pública `redirect_stdout_to_emit()`. Guarda anti-recursão usa
   `sys.__stdout__` para fallback (nunca `sys.stdout`, que aponta para self).

2. `nyx/cli.py`: import + `with redirect_stdout_to_emit():` em volta do bloco
   de dispatch slash (linhas 595-643 originais). No-op fora de Application mode
   preserva semântica legacy/PromptSession/headless.

## Validação (Fase 3)

- `/help`: tabela 3 colunas (Sessão/Contexto/Modelo) + 39 comandos extras render OK.
- `/status`: painel Rich `╭ sessão ╮` com 6 métricas render OK.
- `/quit`: `/admin/shutdown` em proxy.log + Application encerra (sprint 188 preservada).
- Smoke `./run.sh --smoke` exit 0 `boot ok`.
- Invariantes `FAIL_AFTER==FAIL_BEFORE==2` (pré-existentes #10 ruff + #14 anti-sanitizer).
- Gauntlet `./run.sh --gauntlet --only rapido` 19/19 (100%) APROVADO.
- Acentuação `--paths nyx/agent/output.py nyx/cli.py` rc=0.
- Cleanup: zero processos residuais, VRAM 3706 MiB livres.

---

## Contexto do projeto (snapshot)

> **ADRs relevantes:**
> - ADR-024 Render Layer: print() só em cli*.py e output.py.
> - ADR-026 Agência: usuário sempre controla.
> - ADR-029 Layout Parity: estrutura visual de Claude Code com identidade Nyx. <!-- noqa-anonimato -->
>
> **Estado do sistema:**
> - 67 commands registrados em `nyx/agent/commands/`. Dispatcher em `nyx/cli_handlers.py`.
> - Keybinding `/` em 2 sites: `cli_keybindings.py:161` (legacy PromptSession) e `repl_app.py:303` (Application path).
> - Sprint 188 TUI-CTRL-Q-OLLAMA-STOP-04 ligou `__quit__` ao shutdown ordenado.
> - Sprint anterior: 222 INFRA-PRELOAD-VRAM (esperando CONCLUIDA primeiro para evitar OOM durante a sessão de repro).

---

## Problema

Usuário reportou em 2026-05-25 durante validação pré-sprint: **"não consegui rodar nenhum comando de barra lá dentro"**. Captura de tela mostra REPL Application rodando normalmente (banner OK, balão user OK, label Nyx OK, toolbar OK), mas slash commands não disparam.

Código aparenta estar correto:
- `nyx/agent/repl_app.py:303-308`: `@kb.add("/")` insere `/` e chama `buf.start_completion(select_first=True)`.
- `nyx/agent/repl_app.py:294-297`: `_submit` chama `buf.validate_and_handle()` quando texto começa com `/`.
- `nyx/cli_handlers.py:922 dispatch_sync` + `:942 dispatch_async`: rotas para sentinelas.

Causa-raiz **desconhecida**. Possibilidades:
- (a) Completer não aparece visualmente (estado do popup).
- (b) Enter não dispara `validate_and_handle` no Application path.
- (c) Handler ignora sentinela `__slash_*__` ou retorna sem efeito.
- (d) app_state com flag bloqueante (`permission_pending`, `summarize_in_progress`).
- (e) Output do handler vai para destino que não renderiza (logger.debug em vez de output.print).

### Sintoma observável

Imagem 2 do feedback do usuário (2026-05-25 16:11): REPL Application visível, banner OK, mas resposta de `/help` ausente em qualquer captura — usuário não vê output algum ao digitar slash.

---

## Solução proposta

**Fase 1 — Reprodução (obrigatória, antes de qualquer Edit):**

1. Iniciar `./run.sh` em sessão interativa com `tail -f logs/proxy.log` em paralelo.
2. Digitar `/help` + Enter. Observar:
   - Popup do completer aparece?
   - Enter submete?
   - Algum output em `logs/repl_app.log` ou `logs/cli.log` (se existir)?
   - `app_state["mode"]` durante o digito?
3. Repetir para `/status`, `/quit`.
4. Documentar causa-raiz no spec (file:line).

**Fase 2 — Fix cirúrgico:**

Depende da causa-raiz encontrada na Fase 1. Touches mínimos. Sem mudança estrutural.

**Fase 3 — Validação:**

3 screenshots do REPL: `/help` renderiza tabela, `/status` mostra info, `/quit` dispara shutdown.

---

## Arquivos alvo

A definir na Fase 1 (dependente de causa).

**Localizações suspeitas (drift tolerado):**

### `nyx/agent/repl_app.py:303-308` `_slash`
```python
@kb.add("/")
def _slash(event: Any) -> None:
    buf = event.current_buffer
    buf.insert_text("/")
    if buf.document.text_before_cursor.lstrip() == "/":
        buf.start_completion(select_first=True)
```

### `nyx/agent/repl_app.py:294-297` `_submit`
```python
elif buf.document.text.strip() == "/" and not state:
    buf.start_completion(select_first=True)
    return
buf.validate_and_handle()
```

### `nyx/cli_handlers.py:922-960` `dispatch_sync` / `dispatch_async`
A inspecionar.

---

## Diff esperado (resumo)

A definir após Fase 1. Estimativa: 5-30 linhas, 1-3 arquivos.

---

## Comandos de verificação

```bash
# Fase 1 — Reprodução (manual, interativa)
./run.sh
# Em outra janela:
tail -f logs/proxy.log
# Digitar /help, /status, /quit. Capturar screenshots:
import -window $(xdotool search --name './run.sh' | head -1) /tmp/repl_slash_help.png
# (repetir após cada slash)

# Fase 2 — Fix (depende da causa)

# Fase 3 — Validação
./run.sh --smoke
bash scripts/sprint_invariants.sh
./run.sh --gauntlet --only rapido
# Visual final:
./run.sh
# /help -> ver tabela; /status -> ver info; /quit -> shutdown gracioso
python3 ~/.config/zsh/scripts/validar-acentuacao.py --paths <arquivos_modificados>
```

---

## Critério binário de aceite

- [ ] Fase 1: causa-raiz com `file:line` registrada neste spec ANTES de Edits.
- [ ] Fase 2: Edits cirúrgicos (touches explícitos).
- [ ] Fase 3: 3 screenshots demonstrando /help, /status, /quit funcionais.
- [ ] Sprint 188 (Ctrl+Q + ollama stop) NÃO regrediu.
- [ ] Smoke boot ok.
- [ ] Invariantes 14/14 PASS.
- [ ] Gauntlet --only rapido APROVADO.
- [ ] Acentuação rc=0.
- [ ] Spec movida producao/ → concluidos/.
- [ ] MASTER entry 223 PENDENTE → CONCLUIDA.

---

## Proof-of-work (4 passos)

```bash
bash scripts/sprint_invariants.sh > /tmp/inv_before.txt 2>&1
# Fase 1, 2, 3
bash scripts/sprint_invariants.sh > /tmp/inv_after.txt 2>&1
diff /tmp/inv_before.txt /tmp/inv_after.txt
ls /tmp/repl_slash_*.png   # 3 imagens
```

---

## Riscos

| Risco | Mitigação |
|---|---|
| Bug interativo difícil de reproduzir consistentemente | Spec deve descrever cenário literal antes de mexer no código |
| Regressão na sprint 188 (Ctrl+Q + ollama stop) | Re-validar `/quit` dispara shutdown completo via captura |
| Causa pode estar fora dos sites suspeitos | Fase 1 obrigatória; sem ela, sprint vira BLOQUEADA |

---

*"Reproduzir antes de consertar. Conserto sem reprodução é palpite." — princípio de debug*
