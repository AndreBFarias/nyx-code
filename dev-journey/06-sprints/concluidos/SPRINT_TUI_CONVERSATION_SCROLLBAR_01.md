# SPRINT 228 — TUI-CONVERSATION-SCROLLBAR-01

## 0. SPEC (machine-readable)

```yaml
sprint:
  id: TUI-CONVERSATION-SCROLLBAR-01
  title: "Scrollbar visível na área de conversa (output_window)"
  onda: 31
  prioridade: BAIXA
  tipo: Feature
  dependencias: []
  desbloqueia: []

  touches:
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/agent/repl_app.py
      reason: "output_window ganha ScrollbarMargin + lógica de auto-scroll-pause"
      linhas_alvo: "60-90,470-490"
  creates: []
  removes: []

  forbidden:
    - "Tocar em input_window (sprint S6 separada)"
    - "Quebrar auto-scroll do _emit quando cursor já está no fim"
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
    - "Sessão com > 1 tela de conversa mostra scrollbar à direita do output"
    - "Mouse wheel + page-up/down movem scroll"
    - "Auto-scroll preservado quando cursor está no fim"
    - "Quando usuário rola para cima, novo turno não força bottom (pause)"
    - "Smoke boot ok + invariantes 14/14 PASS"
```

---

# Sprint 228 — TUI-CONVERSATION-SCROLLBAR-01

**Status:** PENDENTE
**Data criação:** 2026-05-25
**Modelo obrigatório:** claude-opus-4-7 (sem subagentes)

---

## Contexto do projeto (snapshot)

> **ADRs relevantes:**
> - ADR-024 Render Layer. ADR-026 Agência (rolagem é controle do usuário).
>
> **Estado do sistema:**
> - `nyx/agent/repl_app.py:228 output_buffer = Buffer(read_only=False, multiline=True)`.
> - `nyx/agent/repl_app.py:457 output_control = FormattedTextControl(...)`.
> - `nyx/agent/repl_app.py:482 output_window = Window(content=output_control, ...)`.
> - `nyx/agent/repl_app.py:63-69 _emit` faz auto-scroll via `buffer.document = Document(text=novo, cursor_position=len(novo))`.

---

## Problema

Área de conversa não tem scrollbar visível. Terminal nativo gerencia scroll, mas usuário pediu indicador visual no Application path.

Feedback do usuário (2026-05-25): **"A conversa como um todo pode ser rolada pra cima ou pra baixo então tem que ter uma barra de rolagem na conversa com a nyx."**

---

## Solução proposta

Adicionar `right_margins=[ScrollbarMargin(display_arrows=False)]` ao `output_window`. Para auto-scroll-pause: flag em `app_state["_user_scrolled_up"]` setada quando usuário move cursor manualmente; `_emit` consulta antes de re-posicionar cursor no fim.

---

## Arquivos alvo

### `/home/andrefarias/Desenvolvimento/Nyx-Code/nyx/agent/repl_app.py`

**Localização aproximada:** linha 482-489.

**Antes:**
```python
output_window = Window(
    content=output_control,
    height=Dimension(...),
    ...
)
```

**Depois:**
```python
from prompt_toolkit.layout.margins import ScrollbarMargin   # noqa: E402

output_window = Window(
    content=output_control,
    height=Dimension(...),
    right_margins=[ScrollbarMargin(display_arrows=True)],
    ...
)
```

**Mudança em `_emit` (linha 63-69):**
```python
def _emit(buffer, novo):
    # Auto-scroll-pause: se usuário rolou para cima manualmente, não força bottom
    if app_state.get("_user_scrolled_up", False):
        # Append silencioso sem mover cursor
        buffer.text = novo
    else:
        buffer.document = Document(text=novo, cursor_position=len(novo))
```

Hook em `@kb.add("pageup")` / mouse wheel para setar flag.

---

## Diff esperado (resumo)

```
~ 1 arquivo modificado
+ ~25 linhas líquidas (import + Scrollbar + flag + hook)
```

---

## Comandos de verificação

```bash
# Smoke
./run.sh --smoke

# Visual: forçar > 1 tela de conversa
./run.sh
# Digitar 10+ turnos curtos. Capturar:
import -window $(xdotool search --name './run.sh' | head -1) /tmp/conv_scrollbar.png
# Esperado: scrollbar à direita do output (não do input)

# Auto-scroll-pause: PgUp + novo turno chega → bottom NÃO forçado
# (manual: capturar antes e depois)

# Invariantes + gauntlet
bash scripts/sprint_invariants.sh
./run.sh --gauntlet --only rapido
```

---

## Critério binário de aceite

- [ ] Sessão com > 1 tela mostra scrollbar.
- [ ] Wheel + PgUp/PgDn funcionam.
- [ ] Auto-scroll preservado quando no fim.
- [ ] Auto-scroll pausa quando rolou manualmente.
- [ ] Sprint S6 (input scrollbar) não afetada (margens separadas).
- [ ] Smoke + invariantes + gauntlet OK.

---

## Proof-of-work

```bash
bash scripts/sprint_invariants.sh > /tmp/inv_before.txt 2>&1
# Edit
bash scripts/sprint_invariants.sh > /tmp/inv_after.txt 2>&1
diff /tmp/inv_before.txt /tmp/inv_after.txt
sha256sum /tmp/conv_scrollbar.png
```

---

## Riscos

| Risco | Mitigação |
|---|---|
| Margem direita reduz largura útil em 1 char | Wrap de texto absorve sem regressão observável |
| Auto-scroll-pause complexo (race condition) | Flag simples + hook explícito em PgUp; sem heurística de "cursor está visualmente no fim" |
| ScrollbarMargin pode requerer Window com height variável | output_window já é variável (Dimension via 1fr equivalent); verificar |

---

*"Sem indicador visual de scroll, conteúdo perdido é invisível." — princípio*
