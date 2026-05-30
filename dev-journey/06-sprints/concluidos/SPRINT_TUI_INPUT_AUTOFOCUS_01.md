# SPRINT 307 — TUI-INPUT-AUTOFOCUS-01

## 0. SPEC (machine-readable)

```yaml
sprint:
  id: TUI-INPUT-AUTOFOCUS-01
  title: "Input inicia focado no terminal e no --web (digitar sem clicar)"
  onda: 35
  prioridade: ALTA
  tipo: Bugfix
  dependencias: []
  desbloqueia: []

  touches:
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/agent/tui/app.py
      reason: "Reaplicar foco do #input apos o primeiro refresh (call_after_refresh) -- timing do mount no PTY"
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/cockpit/static/terminal.html
      reason: "Focar o xterm.js no DOM (term.focus) ao abrir, ao conectar e ao recriar no resize"
  creates: []
  removes: []

  forbidden:
    - "Adicionar emoji"
    - "Mencao a IA externa em codigo/commit"  # noqa-anonimato
    - "except silencioso (invariante #4)"
    - "print() fora de cli.py/output.py"

  acceptance_criteria:
    - "Ao abrir ./run.sh e --web, digitar IMEDIATAMENTE (sem clicar) faz o texto aparecer no input"
    - "Foco resiste ao primeiro refresh (call_after_refresh)"
    - "Smoke boot ok + invariantes 14/14 + gauntlet --only rapido APROVADO"
```

---

**Status:** CONCLUIDA
**Data criação:** 2026-05-30
**Data conclusão:** 2026-05-30
**Modelo obrigatório:** claude-opus-4-7 (sem subagentes)

---

## Problema

Relato do usuário (ONDA-35): ao abrir a TUI, o input **não** está focado — é preciso clicar nele antes de digitar; e enquanto não focado, "a digitação não aparece". Invisível à validação por injeção (`/control/repl/send`), que não exercita o foco/teclado.

## Causa-raiz (dois níveis de foco)

1. **`--web` (DOM):** `nyx/cockpit/static/terminal.html` chamava `term.open(termContainer)` mas **nunca `term.focus()`**. Sem foco no canvas do xterm.js, as teclas do browser não chegam ao PTY até o usuário clicar. Esse era o bug do `--web`.
2. **Textual (`#input`):** o `on_mount` já focava o `#input`, mas no caminho --web o mount da TUI no PTY pode preceder o layout final / a conexão do xterm.js, e o foco se perdia (sem reforço pós-refresh).

## Fix

- `terminal.html`: `term.focus()` em 3 pontos — após `term.open()` inicial, no `ws.onopen` (conexão) e no `recreateTerminal()` (resize). Comentários em ASCII (estilo do arquivo).
- `app.py`: `on_mount` passa a chamar `self._focus_input()` **e** `self.call_after_refresh(self._focus_input)`; novo helper `_focus_input()` sem try/except (o `#input` é sempre yielded em compose → `query_one` não falha; respeita invariante #4).

## Proof-of-work

```
FAIL_BEFORE=0  (14/14 PASS)  ->  FAIL_AFTER=0  (14/14 PASS)
ruff nyx/agent/tui/app.py: All checks passed!
acentuacao --paths app.py terminal.html: rc=0
gauntlet --only rapido: 19/19 (100%) APROVADO (infra 5/5, proxy 7/7, visual 3/3, config 4/4)
```

**Validação Textual (Pilot, `/tmp/val_307_focus.py`):**
```
focused id (mount): input | type: InputWidget
input.text apos digitar 'oi' sem clicar: 'oi'
focused id (pos-refresh): input
OK 307 (Textual): input focado no mount, digitacao aparece sem clicar, foco resiste a refresh
```

**Validação --web real (playwright, digitando sem clicar):** subiu `./run.sh --web`, navegou a `/static/terminal.html`, e via `page.keyboard.press` digitou "oi nyx" **sem nenhum clique** — o texto apareceu no input (evidência: `nyx_307_web_digitado.png`). Encerrado por PID; VRAM 64/4096 ao fim, zero órfãos.

## Critério de aceite

- [x] Digitar sem clicar funciona no terminal (Pilot) e no --web (playwright).
- [x] Foco resiste ao refresh.
- [x] Smoke + invariantes 14/14 + gauntlet rápido APROVADO; ruff e acentuação limpos.

---

*"O cursor onde a mão espera: o software some, resta a intenção." -- anônimo*
