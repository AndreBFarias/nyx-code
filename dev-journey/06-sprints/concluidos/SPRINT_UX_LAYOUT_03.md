## 0. SPEC

```yaml
sprint:
  id: UX-LAYOUT-03
  title: "Streaming suave + spinner sem flicker + Ctrl+C limpa linha residual"
  onda: 22
  bloco: 4
  prioridade: ALTA
  tipo: Bugfix
  dependencias: [UX-LAYOUT-02]
  desbloqueia: [UX-BUG-01]

  touches:
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/cli.py
      reason: "on_token com buffer+flush; _stop_spinner emite \\r\\x1b[2K; KeyboardInterrupt limpa linha"
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/agent/output.py
      reason: "nyx_spinner usa SPINNER_FRAMES; render_assistant_start/end com espaçamento fixo"

  absorve:
    - "A-07 (spinner compete com on_token, gera flicker)"
    - "O-08 (Ctrl+C deixa resquício de texto na linha)"

  forbidden:
    - "Remover streaming (é feature core, ADR-008)"
    - "Trocar spinner ASCII — deve usar SPINNER_FRAMES do design_tokens"
    - "Eliminar handler de Ctrl+C (mata afordância de cancelar turno)"

  tests:
    - cmd: "./run.sh --gauntlet --only tui"
      deve_passar: true
    - cmd: "python -c 'from nyx.themes.design_tokens import SPINNER_FRAMES; print(len(SPINNER_FRAMES))'"
      esperado: "10"

  acceptance_criteria:
    - "on_token limpa linha do spinner (\\r\\x1b[2K) antes do primeiro caractere de cada turno"
    - "Buffer de streaming: flush só a cada 32 chars ou \\n (reduz flicker em CPU lenta)"
    - "render_assistant_start imprime exatamente 1 linha em branco acima"
    - "render_assistant_end imprime exatamente 1 linha em branco abaixo"
    - "Quando status.state==DONE e summary==streamed: suprime segunda renderização"
    - "Ctrl+C durante streaming imprime \\r\\x1b[2K + '[cancelado]' e volta ao prompt limpo"
    - "Spinner usa frames SPINNER_FRAMES em loop"
    - "Gauntlet tui passa"
```

---

# Sprint UX-LAYOUT-03 — Streaming + spinner + Ctrl+C limpos

## Contexto

- Findings:
  - A-07: `on_token` escreve direto em `sys.stdout` enquanto spinner ainda pode estar ativo → flicker.
  - O-08: `KeyboardInterrupt` imprime `\n  [cancelado]` mas não limpa a linha onde o token parou; resíduo aparece.
- Decisão D2 (design system): spinner usa frames Braille de `SPINNER_FRAMES` (já em design_tokens).

## Problema

1. Streaming fica "tremido" — tokens entram e o spinner pisca embaixo.
2. Final do turno pode duplicar texto quando streamed_text e summary se sobrepõem parcialmente (`already_shown` cobre só o caso exato).
3. Ctrl+C imprime `[cancelado]` mas não limpa a linha residual.

## Solução

### `nyx/cli.py` — `on_token` com limpeza e buffer

```python
def on_token(token: str) -> None:
    # Primeiro token do turno: limpa linha do spinner
    if not turn_state["streamed_text"]:
        _stop_spinner()
        sys.stdout.write("\r\x1b[2K")
    turn_state["streamed_text"] += token
    turn_state["token_buffer"] += token
    if len(turn_state["token_buffer"]) >= 32 or "\n" in token:
        sys.stdout.write(turn_state["token_buffer"])
        sys.stdout.flush()
        turn_state["token_buffer"] = ""
```

E no fim do turno (após loop de run):
```python
if turn_state["token_buffer"]:
    sys.stdout.write(turn_state["token_buffer"])
    sys.stdout.flush()
    turn_state["token_buffer"] = ""
```

### `nyx/cli.py` — Ctrl+C limpa linha

```python
except KeyboardInterrupt:
    _stop_spinner()
    if turn_state.get("token_buffer"):
        sys.stdout.write(turn_state["token_buffer"])
        sys.stdout.flush()
        turn_state["token_buffer"] = ""
    sys.stdout.write("\r\x1b[2K")  # limpa linha atual
    sys.stdout.flush()
    print(f"\n  {ACCENT}[cancelado]{NC}")
```

### `nyx/cli.py` — supressão de duplicata

A lógica `already_shown` atual confere igualdade estrita ou endswith. Ampliar:

```python
streamed = turn_state["streamed_text"].strip()
summary = (status.summary or "").strip()

def _is_subset(a: str, b: str) -> bool:
    """Retorna True se a é essencialmente contida em b (ignorando whitespace)."""
    ca = " ".join(a.split()); cb = " ".join(b.split())
    return ca in cb or cb in ca

already_shown = bool(streamed) and bool(summary) and _is_subset(streamed, summary)

if summary and not already_shown:
    # render
elif streamed:
    print()  # newline de encerramento
```

### `nyx/cli.py` — state_label oculto em DONE

```python
state_label = status.state.value
if status.state != status.state.DONE:
    print(f"  {DIM}[{state_label}]{NC}")
# Quando DONE: nada. Turno termina limpo.
```

### `nyx/agent/output.py` — nyx_spinner com SPINNER_FRAMES

Se já existe `nyx_spinner`, refatorar para usar:

```python
from nyx.themes.design_tokens import SPINNER_FRAMES, ANSI_ACCENT_FG, ANSI_RESET

class NyxSpinner:
    def __init__(self, message: str = "pensando..."):
        self.message = message
        self._thread = None
        self._stop = threading.Event()
        self._frame_idx = 0

    def __enter__(self):
        import threading, time, sys
        def _loop():
            while not self._stop.is_set():
                frame = SPINNER_FRAMES[self._frame_idx % len(SPINNER_FRAMES)]
                sys.stdout.write(f"\r  {ANSI_ACCENT_FG}{frame}{ANSI_RESET}   {self.message}")
                sys.stdout.flush()
                self._frame_idx += 1
                self._stop.wait(0.08)
        self._thread = threading.Thread(target=_loop, daemon=True)
        self._thread.start()
        return self

    def stop(self):
        self._stop.set()
        if self._thread:
            self._thread.join(timeout=0.2)
        sys.stdout.write("\r\x1b[2K")  # limpa linha
        sys.stdout.flush()

    def __exit__(self, *args):
        self.stop()

def nyx_spinner(msg: str = "pensando...") -> NyxSpinner:
    return NyxSpinner(msg)
```

### `render_assistant_start/end` com espaçamento fixo

```python
def render_assistant_start() -> None:
    print()  # exatamente 1 linha em branco acima
    print(f"  {ANSI_ACCENT_FG}{ANSI_BOLD}Nyx{ANSI_RESET}")
    print(f"  {ANSI_ACCENT_FG}───{ANSI_RESET}")

def render_assistant_end() -> None:
    print()  # exatamente 1 linha em branco abaixo
```

## Comando de verificação

```bash
cd /home/andrefarias/Desenvolvimento/Nyx-Code

# 1. Spinner frames consome design_tokens
python -c "
from nyx.agent.output import nyx_spinner
import time
with nyx_spinner('teste...') as sp:
    time.sleep(0.3)
print('OK')
"

# 2. on_token tem lógica de buffer
grep -c "token_buffer" nyx/cli.py
# esperado: >= 3

# 3. Ctrl+C limpa linha
grep -A3 "except KeyboardInterrupt" nyx/cli.py | grep "\\\\x1b\\[2K"

# 4. Supressão ampla de duplicata
grep "_is_subset\|is_subset" nyx/cli.py

./run.sh --gauntlet --only tui
```

## Critério binário

- [ ] Streaming com buffer 32 chars / \n
- [ ] Spinner consome SPINNER_FRAMES
- [ ] on_token emite `\r\x1b[2K` no primeiro token
- [ ] Ctrl+C limpa linha e imprime `[cancelado]` sem resíduo
- [ ] `render_assistant_start` imprime 1 linha em branco acima, nome "Nyx" e régua
- [ ] `render_assistant_end` imprime 1 linha em branco abaixo
- [ ] DONE sem `[done]` label
- [ ] Gauntlet tui passa
- [ ] Visual: streaming de 200 tokens fluído; Ctrl+C limpo
- [ ] Commit: `fix: streaming suave + spinner sem flicker + Ctrl+C limpo`

## Guardrails anti-engodo

**NÃO marque como concluída se:**
- IA mudou spinner mas deixou ACCENT_FG hardcoded (deveria vir de tokens).
- Buffer nunca é esvaziado → usuário vê resposta só no fim (quebra streaming).
- `_is_subset` implementado mas `already_shown` não usa.

## Validação humana

```bash
./run.sh
# digitar uma pergunta longa; ver streaming fluído
# durante streaming, Ctrl+C → linha limpa, "[cancelado]"
# enviar outra pergunta imediatamente — prompt aparece limpo
```

## Riscos

| Risco | Mitigação |
|-------|-----------|
| Buffer atrasa exibição perceptivelmente | Flush também quando token contém `\n` |
| \x1b[2K não funciona em terminais antigos | Aceitável — Nyx depende de terminais modernos; kitty é o target |

---

*"Fluência é ausência de reação involuntária." -- anônimo jazz*
