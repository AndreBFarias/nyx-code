> **Status:** ABSORVIDA_POR_UX-LAYOUT-01A, UX-LAYOUT-01B (2026-04-19)
>
> **Nota de absorção:** sprint original misturava 3 responsabilidades (banner, toolbar, paste). Dividida:
> - Banner + BOX_CHARS + modo compacto → `SPRINT_UX_LAYOUT_01A.md`.
> - Toolbar + ctx N/M tok + bypass roxo + schema de secções → `SPRINT_UX_LAYOUT_01B.md` (deps: 01A + OBSERVABILITY-01).
> - Paste colapsado preservando contexto → migrado para `SPRINT_TUI_FIX_07B.md` (junto do resto de paste-longo).
>
> Arquivo preservado em `producao/` como referência histórica.

---

## 0. SPEC

```yaml
sprint:
  id: UX-LAYOUT-01
  title: "[ABSORVIDA] Banner + toolbar repaginados + colapso de paste preservando contexto + ctx em N/M tok"
  onda: 22
  bloco: 4
  prioridade: ALTA
  tipo: Feature
  dependencias: [UX-DESIGN-01]
  desbloqueia: [UX-LAYOUT-02]

  touches:
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/cli.py
      reason: "_build_banner e _bottom_toolbar reescritos consumindo design_tokens"
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/agent/output.py
      reason: "render_user_input trata colapso preservando início e fim do paste"

  absorve:
    - "A-10 (colapso paste perdia miolo)"
    - "O-06 (ctx % agora mostra N/M tokens no toolbar)"

  forbidden:
    - "Hex hardcoded (vem de design_tokens)"
    - "Quebrar o modo estreito (cols<60) — deve continuar legível"
    - "Usar emoji"

  tests:
    - cmd: "python -c 'from nyx.cli import _build_banner; print(_build_banner(\"qwen3:4b\", 35, \"Nyx-Code\")[:50])'"
      deve_passar: true
    - cmd: "./run.sh --gauntlet --only tui"
      deve_passar: true

  acceptance_criteria:
    - "Banner renderiza linhas corretas (box chars via BOX_CHARS), sem hex hardcoded"
    - "Toolbar mostra ctx como 'X% (Ntok/Mtok)' em vez de só 'X%'"
    - "Toolbar: bypass ON usa roxo NYX_PURPLE; bypass OFF usa NYX_MUTED"
    - "Paste > 8 linhas: mostra primeiras 3 + últimas 2 + '[N linhas ocultas no meio]'"
    - "Modo estreito (cols<60) permanece funcional"
    - "Gauntlet fase tui passa"
    - "Visual: screenshot aprovado pelo usuário (checkpoint)"
```

---

# Sprint UX-LAYOUT-01 — Banner, toolbar, colapso de paste

## Contexto

- Depende de UX-DESIGN-01 (design_tokens existe, glifos canônicos definidos).
- Findings:
  - A-10: `USER_INPUT_COLLAPSE_LINES=8` descarta linhas do meio; usuário perde contexto.
  - O-06: toolbar mostra só `ctx X%` sem dizer limite absoluto.
- Decisão D2 (paleta mista D): bypass ON em roxo.

## Problema

1. Banner e toolbar usam hex hardcoded (será eliminado por design_tokens).
2. Paste longo colapsa 3 primeiras + resto oculto — a pergunta geralmente está no fim.
3. Toolbar `ctx 11%` não responde "11% de quanto?".

## Solução

### `nyx/cli.py` — `_build_banner`

Reescrever consumindo BOX_CHARS e cores do design_tokens. Modelo visual:

```
  ╭─ Nyx · v1.2.0 ──────────────────────────────── 100% offline ─╮
  │                                                              │
  │   modelo    qwen3:4b          visão    moondream  (cold)     │
  │   projeto   Nyx-Code          tools    35                    │
  │   rede      :11435 ollama  ·  :11436 proxy                   │
  │   memória   3 entradas                                       │
  │                                                              │
  ╰── /help para comandos · Ctrl+D para sair ────────────────────╯
```

Observações:
- Linha "visão" mostra "(cold)" se moondream não pullado, "(pronto)" se sim. Sprint VISION-01 adiciona isto — por ora, mostrar "(indisponível)" se vision_service ausente.
- Modo estreito (cols < 80): banner compacto 2-3 linhas.

### `nyx/cli.py` — `_bottom_toolbar`

```python
def _bottom_toolbar() -> list:
    from prompt_toolkit.formatted_text import FormattedText
    from nyx.themes.design_tokens import NYX_ACCENT, NYX_MUTED, NYX_PURPLE, BULLETS

    ctx_pct = app_state.get("ctx_pct", 0)
    total_tok = app_state.get("total_tokens", 0)
    max_tok = app_state.get("max_tokens", 0)
    iter_n = app_state.get("iter_n", 0)
    reads = app_state.get("reads", 0)
    mods = app_state.get("mods", 0)

    parts: list[tuple[str, str]] = []
    ctx_label = f"ctx {ctx_pct}%"
    if max_tok:
        ctx_label += f" ({total_tok}/{max_tok}tok)"
    parts.append((f"fg:{NYX_ACCENT}", f"{ctx_label} "))
    parts.append((f"fg:{NYX_MUTED}", f"· {model} · iter {iter_n} · lidos {reads} · modif {mods}"))

    if app_state.get("bypass"):
        parts.append(("", "  "))
        parts.append((f"bg:{NYX_PURPLE} fg:#ffffff bold", f" {BULLETS['bypass_on']} bypass ON "))
    else:
        parts.append((f"fg:{NYX_MUTED}", f"   {BULLETS['bypass_off']} shift+tab: bypass"))
    return FormattedText(parts)
```

E alimentar o `app_state` com `total_tokens` e `max_tokens` vindos de `agent.get_context_info()`:

```python
ctx_info = agent.get_context_info()
app_state["ctx_pct"] = int(ctx_info.get("pct", 0) * 100)
app_state["total_tokens"] = ctx_info.get("total_tokens", 0)
app_state["max_tokens"] = ctx_info.get("max_tokens", 0)
```

### `nyx/agent/output.py` — `render_user_input`

**Antes:** colapsa 3 primeiras + resto oculto.

**Depois:**
```python
USER_INPUT_COLLAPSE_LINES = 8
USER_INPUT_HEAD = 3
USER_INPUT_TAIL = 2

def render_user_input(text: str, console_width: int | None = None) -> None:
    import shutil
    from nyx.themes.design_tokens import ANSI_ACCENT_FG, ANSI_RESET, BOX_CHARS, BULLETS

    if console_width is None:
        console_width = shutil.get_terminal_size(fallback=(80, 24)).columns

    lines = text.splitlines() or [text]
    if len(lines) > USER_INPUT_COLLAPSE_LINES:
        head = lines[:USER_INPUT_HEAD]
        tail = lines[-USER_INPUT_TAIL:]
        hidden = len(lines) - USER_INPUT_HEAD - USER_INPUT_TAIL
        middle_line = f"... [{hidden} linhas ocultas no meio — use /paste para ver completo]"
        display_lines = head + [middle_line] + tail
        display_text = "\n".join(display_lines)
    else:
        display_text = text

    # resto do render (Rich Panel ou fallback ANSI) consome display_text ...
```

## Comando de verificação

```bash
cd /home/andrefarias/Desenvolvimento/Nyx-Code

# 1. Banner importável e sem crash
python -c "
from nyx.cli import _build_banner
b = _build_banner('qwen3:4b', 35, 'Nyx-Code')
assert '╭' in b and '╰' in b
print('banner OK, len=', len(b))
"

# 2. render_user_input preserva head+tail
python -c "
from nyx.agent.output import render_user_input
import io, sys
orig = sys.stdout; sys.stdout = io.StringIO()
text = '\n'.join(f'linha {i}' for i in range(20))
render_user_input(text, console_width=100)
out = sys.stdout.getvalue(); sys.stdout = orig
assert 'linha 0' in out and 'linha 19' in out, 'head ou tail perdidos'
assert 'linhas ocultas no meio' in out
print('colapso OK')
"

# 3. Toolbar exibe N/M
grep -n "max_tokens\|total_tokens" nyx/cli.py

# 4. Zero hex no cli/output
grep -rn '#[0-9A-Fa-f]\{6\}' nyx/cli.py nyx/agent/output.py
# esperado: vazio

# 5. Gauntlet
./run.sh --gauntlet --only tui
```

## Critério binário

- [ ] Banner usa BOX_CHARS, sem hex direto
- [ ] Toolbar mostra `ctx X% (Ntok/Mtok)`
- [ ] Bypass ON em roxo; OFF em muted
- [ ] Paste > 8 linhas mostra head + tail + middle placeholder
- [ ] Modo estreito funcional
- [ ] Gauntlet tui passa
- [ ] Screenshot aprovado pelo usuário
- [ ] Commit: `feat: banner+toolbar repaginados, paste preserva contexto, ctx em tokens`

## Guardrails anti-engodo

**NÃO marque como concluída se:**
- IA esqueceu de propagar `total_tokens`/`max_tokens` do agent para o app_state.
- Colapso só testou com 10 linhas e não revalidou com 20+.
- Manteve ⚡ em alguma posição.

## Validação humana

```bash
./run.sh
# 1. Ver banner com cores e ╭╮╯╰
# 2. Toolbar aparece embaixo com ctx N/M tok
# 3. Shift+Tab liga bypass — vira roxo
# 4. Cole texto com 20 linhas, submeta — box mostra início e fim
```

## Riscos

| Risco | Mitigação |
|-------|-----------|
| Toolbar com "tok" muito largo em 60 cols | Se width < 80, omitir N/M e deixar só X% |
| Roxo fica ilegível em tema claro | Nyx é dark-first (ADR implícita); documentar |

---

*"O primeiro frame define a expectativa da sessão inteira." -- anônimo UX*
