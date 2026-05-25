# SPRINT 224 — TUI-NYX-SOFT-BOX-01

## 0. SPEC (machine-readable)

```yaml
sprint:
  id: TUI-NYX-SOFT-BOX-01
  title: "Balão ANSI soft-box roxo para Nyx (simétrico ao do usuário)"
  onda: 31
  prioridade: ALTA
  tipo: Feature
  dependencias: []
  desbloqueia: [TUI-SPINNER-IN-NYX-BOX-01]

  touches:
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/agent/output.py
      reason: "Extrair _render_user_soft_box para _render_soft_box genérico + novo render_assistant_box"
      linhas_alvo: "1040-1215"
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/cli_callbacks.py
      reason: "on_token bufferiza durante turno; box materializa no render_assistant_end"
  creates: []
  removes: []

  n_to_n_pairs:
    - descricao: "wrap_token_with_side_rule deprecado; flag state['disabled']=True nos call-sites"  # noqa-acento
      paths:
        - nyx/agent/output.py
        - nyx/cli_callbacks.py

  forbidden:
    - "Streaming dentro do box com cursor up/repaint (TUI-REDESIGN-26-02 dissolveu por flicker)"
    - "Quebrar fallback console_width < 80 (manter linha plain 'Nyx: text')"
    - "Tocar em --headless (render_assistant_start no-op fora TTY)"
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
    - "Box roxo aparece após resposta completa da Nyx (não durante stream)"
    - "Largura do box ajusta-se ao maior texto + 2 padding"
    - "Footer '└── 4.5s · 487 tokens' permanece sob o box"
    - "User box turquesa preservado byte-a-byte"
    - "Headless preserva comportamento (render_*  no-op)"
    - "Smoke boot ok"
    - "Invariantes 14/14 PASS"
    - "Acentuação rc=0"
    - "Captura visual mostra user box turquesa + nyx box roxo lado a lado"
```

---

# Sprint 224 — TUI-NYX-SOFT-BOX-01

**Status:** PENDENTE
**Data criação:** 2026-05-25
**Modelo obrigatório:** claude-opus-4-7 (sem subagentes)

---

## Contexto do projeto (snapshot)

> **ADRs relevantes:**
> - ADR-023 Design System Paleta D. ADR-024 Render Layer. ADR-027 Identidade Nyx.
> - ADR-029 Layout Parity com Claude Code: estrutura visual paralela + identidade Nyx. <!-- noqa-anonimato -->
>
> **Estado do sistema:**
> - User render: `output.py:1047 _render_user_soft_box` desenha `╭─ Nome ─╮ │ … │ ╰─╯` em turquesa.
> - Nyx render: `output.py:1174 render_assistant_start` desenha apenas header inline `◆ Nyx`.
> - Side-rule `│` por linha de stream via `wrap_token_with_side_rule` (output.py:1144).
> - Sprint TUI-REDESIGN-26-02 (2026-05-18) intencionalmente removeu box envolvente da Nyx para evitar cursor-up durante streaming.

---

## Problema

Assimetria visual entre user e assistant. User tem box completo turquesa; Nyx tem só header + side-rule.

Feedback do usuário (2026-05-25): **"a nyx deveria estar de fato com um balão de texto na cor roxa e o nome dela Nyx que fica acima do balão Deveriia estar escrito igual o nome dela no banner."**

### Sintoma observável

Imagem 2 do feedback (2026-05-25 16:09):
- User: `╭─ [REDACTED] ─...─╮` em turquesa, conteúdo dentro de borda.
- Nyx: linha `◆ Nyx` solitária em roxo + texto resposta cru abaixo, sem container.

---

## Solução proposta

Construir box ao **final** do turno (não incremental). Streaming durante turno continua linha-a-linha plain; quando turno fecha (token end-of-stream ou tool call completa), `render_assistant_end` desenha:

```
  ◆ Nyx
  ╭───────────────────────────╮
  │ Resposta completa em      │
  │ uma ou mais linhas        │
  ╰───────────────────────────╯
  └── 4.5s · 487 tokens
```

Buffer interno do turno por `cli_callbacks.on_token` acumula texto; `on_turn_end` chama `render_assistant_box(text)`. Side-rule `│` em streaming pode permanecer como afixo visual durante o turno (sem ser box) — depois o box materializa.

**Alternativa secundária (decisão na execução):** box "aberto" com top `╭─ Nyx ─╮` imediato, linhas `│ text │` durante stream sem voltar cursor (apenas calcular largura on-the-fly e padding), bottom `╰─╯` no final. Custo: largura precisa ser pré-definida (ex.: `min(console_width - 4, 100)`). Trade-off: render incremental mais bonito vs largura potencialmente subutilizada se resposta curta.

---

## Arquivos alvo

### `/home/andrefarias/Desenvolvimento/Nyx-Code/nyx/agent/output.py`

**Refactor + adição:**

1. **Extrair** `_render_user_soft_box(text, user_name)` (linha 1047) para função genérica `_render_soft_box(text, label, ansi_color_fg)`. Wrapper antigo `_render_user_soft_box` chama `_render_soft_box(text, user_name, ANSI_ACCENT_FG)`.

2. **Adicionar** `render_assistant_box(text)` que chama `_render_soft_box(text, "Nyx", ANSI_PURPLE_FG)`.

3. **Modificar** `render_assistant_start()` (linha 1174) para começar buffer interno via `_turn_buffer = []` (módulo-global ou via state injetável).

4. **Modificar** `render_assistant_end()` (linha 1187) para chamar `render_assistant_box(buffer_consolidado)` antes do footer `└── 4.5s · 487 tokens`.

5. **Deprecar** `wrap_token_with_side_rule` (linha 1144): aceitar flag `state['disabled']=True` que o callsite ativa quando o box estiver ativo.

### `/home/andrefarias/Desenvolvimento/Nyx-Code/nyx/cli_callbacks.py`

`on_token` aceita o texto e armazena em buffer interno do turno (via closure ou state mutável); `on_turn_end` flush buffer + chama `render_assistant_end`. Sem regressão em --headless (callbacks são no-op fora TTY).

---

## Diff esperado (resumo)

```
~ 2 arquivos modificados
+ ~80 linhas líquidas (refactor + buffer + box)
```

---

## Comandos de verificação

```bash
# 1. Validação estática
python -m ruff check nyx/

# 2. Smoke
./run.sh --smoke

# 3. REPL interativo com captura
./run.sh
# Digitar "oi" e aguardar. Capturar:
import -window $(xdotool search --name './run.sh' | head -1) /tmp/nyx_box_validate.png

# 4. --headless preservado
echo '{"type":"request","input":"oi"}' | ./run.sh --headless | jq .

# 5. Invariantes + gauntlet rapido
bash scripts/sprint_invariants.sh
./run.sh --gauntlet --only rapido

# 6. Acentuação
python3 ~/.config/zsh/scripts/validar-acentuacao.py --paths nyx/agent/output.py nyx/cli_callbacks.py
```

---

## Critério binário de aceite

- [ ] Captura visual mostra **user box turquesa + nyx box roxo** lado a lado.
- [ ] Largura do nyx box = max(linhas) + 2 (mesma heurística do user).
- [ ] Footer permanece sob o box (não dentro).
- [ ] `_render_user_soft_box` preservado byte-a-byte para call-sites antigos.
- [ ] `--headless`: zero regressão (callbacks no-op fora TTY).
- [ ] Console_width < 80: fallback plain `Nyx: text` preservado.
- [ ] Smoke + invariantes + gauntlet rapido OK.
- [ ] Spec movida producao/ → concluidos/.

---

## Proof-of-work (4 passos)

```bash
bash scripts/sprint_invariants.sh > /tmp/inv_before.txt 2>&1
# Edit
bash scripts/sprint_invariants.sh > /tmp/inv_after.txt 2>&1
diff /tmp/inv_before.txt /tmp/inv_after.txt
# Visual:
./run.sh   # digitar "oi" + Enter
import -window $(xdotool search --name './run.sh' | head -1) /tmp/nyx_box.png
sha256sum /tmp/nyx_box.png
```

---

## Riscos

| Risco | Mitigação |
|---|---|
| Box após turno completo "trava" UX (usuário espera box durante stream) | Aceitar trade-off; alternativa incremental documentada na seção Solução |
| Buffer interno em módulo global vaza estado entre turnos | Usar state mutável injetável (dict) que o callsite limpa em `on_turn_end` |
| TUI-REDESIGN-26-02 dissolveu o box anteriormente | Spec referencia a sprint anterior; solução evita cursor-up (causa do flicker) |
| Duplo border (side-rule `│` + box `│`) | Flag `state['disabled']=True` em wrap_token_with_side_rule quando box ativo |
| Footer pode colidir com largura do box | Footer renderiza em linha própria abaixo do `╰─╯` |

---

*"Identidade simétrica reforça presença. Voz tem rosto." — princípio gamedesigner*
