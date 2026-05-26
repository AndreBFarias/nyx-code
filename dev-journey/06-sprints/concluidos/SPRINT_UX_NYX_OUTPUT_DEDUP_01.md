# SPRINT 248 — UX-NYX-OUTPUT-DEDUP-01

## 0. SPEC

```yaml
sprint:
  id: UX-NYX-OUTPUT-DEDUP-01
  title: "Eliminar duplicação stream-side-rule + box; header com tempo de resposta"
  onda: 31
  prioridade: ALTA
  tipo: Bugfix
  dependencias: [TUI-NYX-SOFT-BOX-01]
  desbloqueia: []

  touches:
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/agent/output.py
      reason: "render_assistant_start emite header `◆ Nyx`, stream usa wrap_token_with_side_rule (`│ texto`), e render_assistant_end imprime box com mesmo texto — DUPLICAÇÃO visível pelo usuário"
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/cli_callbacks.py
      reason: "wrap_token_with_side_rule chamado em on_token; disable quando box é o renderer final"
  creates: []
  removes: []

  forbidden:
    - "Quebrar fallback console_width<80 (linha plain `Nyx: text`)"
    - "Adicionar emoji"
    - "Tocar em sprint 222-228 commitadas"
```

---

# Sprint 248 — UX-NYX-OUTPUT-DEDUP-01

**Status:** CONCLUIDA (2026-05-26)
**Data criação:** 2026-05-25

## Contexto

Usuário reportou + mostrou exemplo literal:

**Como é (DUPLICADO):**
```
  ◆ Nyx
  │ Claro, estou aqui para ajudar. Por favor, compartilhe mais detalhes...
  ╭─ Nyx ───────────────────────────────────╮
  │ Claro, estou aqui para ajudar. Por favor│
  │ compartilhe mais detalhes...            │
  ╰─────────────────────────────────────────╯
  └── 2.7s
```

**Como deveria ser:**
```
  ◆ NyxCode
  │ Respondeu em apenas 2.7s
  ╭─────────────────────────────────────────╮
  │ Claro, estou aqui para ajudar. Por favor│
  │ compartilhe mais detalhes...            │
  ╰─────────────────────────────────────────╯
```

3 mudanças simultâneas:
1. **Eliminar duplicação stream-side-rule**: o `│ Claro, estou aqui...` antes do box é o stream incremental. Quando o box materializa pós-turno, fica redundante. Desabilitar wrap_token_with_side_rule quando body_text vai materializar box.
2. **Header `◆ Nyx` → `◆ NyxCode`**: identidade do projeto, não só "Nyx" (que é a personagem).
3. **Meta-line entre header e box**: `│ Respondeu em apenas 2.7s` em DIM, substituindo o footer `└── 2.7s` que aparece DEPOIS do box (mover para ANTES).

## Solução

`nyx/agent/output.py`:

1. `render_assistant_start()` linha 1174:
   - Trocar `Nyx` por `NyxCode` (1 caractere mudança no f-string).

2. Novo flag/state em `wrap_token_with_side_rule`:
   - Quando `state["disabled"] = True` → return text sem side-rule.
   - Setado por callsite ANTES do stream começar se vai materializar box.

3. `render_assistant_end(start_monotonic=..., tokens=..., body_text=...)`:
   - Quando `body_text` presente (vai materializar box):
     - Computar `elapsed = time.monotonic() - start_monotonic`.
     - Emitir meta-line `│ Respondeu em apenas {elapsed:.1f}s` em DIM (ANTES do box).
     - Emitir box via `render_assistant_box(body_text)`.
     - NÃO emitir o footer antigo `└── 2.7s` (info já está no header acima do box).

4. `nyx/cli_callbacks.py` callback `on_assistant_start`:
   - Setar `side_rule_state["disabled"] = True` para impedir duplicação.

## Aceitação

- [ ] Captura tmux mostra: `◆ NyxCode` + `│ Respondeu em apenas 2.7s` + box + (sem footer).
- [ ] Stream incremental aparece DENTRO do box durante o turno (ou sem stream visível antes do box, decisão UX).
- [ ] Sem duplicação textual.
- [ ] `--headless`: zero regressão.
- [ ] Smoke + invariantes preservados.

## Riscos

| Risco | Mitigação |
|---|---|
| Mudar `Nyx` → `NyxCode` quebra references textuais em outras sprints | Verificar grep `◆ Nyx` no codebase antes; se houver muitos sites, criar constante |
| Streaming sem feedback visual durante turno = UX pior | Aceitar trade-off OU emitir spinner inline antes do box materializar |
| Cálculo de elapsed em `render_assistant_end` se start_monotonic ausente | Fallback "(tempo indisponível)" ou omitir meta-line |

## Proof-of-work (REAL, runtime cockpit, 2026-05-26)

Reprodução empírica no cockpit (`./run.sh --web` + Playwright dirigindo o xterm,
mensagem real "oi, tudo bem?" enviada à Nyx):

ANTES (bate com "como é" do spec) -- `cockpit_248_resposta.png`:
```
◆ Nyx
│ Oi! Tudo ótimo, obrigado pela pergunta. Como posso ajudar você hoje?   (side-rule)
╭─ Nyx ──────────────────────────────────╮
│ Oi! Tudo ótimo, obrigado pela pergunta...│   (box DUPLICA o texto)
╰──────────────────────────────────────────╯
└── 5.0s   (footer)
```

DEPOIS (bate com "como deveria ser") -- `cockpit_248_depois.png`:
```
◆ NyxCode
│ Respondeu em apenas 0.8s   (meta-line DIM, ACIMA do box)
╭──────────────────────────╮  (box SEM titulo "Nyx")
│ Oi! Tudo ótimo, e você?   │
╰──────────────────────────╯
```

4 mudanças aplicadas:
- `output.py:render_assistant_start` -> header `◆ NyxCode` (era `◆ Nyx`).
- `output.py:render_assistant_box` -> `_render_soft_box(text, "", PURPLE)` (box sem titulo);
  `_render_soft_box` trata label vazio com `title = "─"`.
- `output.py:render_assistant_end` -> quando box materializa (width>=80), meta-line
  `│ Respondeu em apenas {elapsed:.1f}s` DIM ANTES do box; footer `└── Ns` removido
  nesse caminho. Fallback width<80 preserva footer antigo.
- `cli.py` seta `turn_state["suppress_live"]=True` quando width>=80 e
  `cli_callbacks.py:flush_buffer` nao emite stream ao vivo nesse caso (elimina a
  duplicacao stream+box). Texto acumula em `streamed_text`; box o consolida.

Verificação: ruff All checks passed; `./run.sh --smoke` boot ok; invariantes 14/14.
Fallback `console_width<80` (linha plain) e `--headless` (run_headless separado)
NAO afetados. Nota: ha 1 linha em branco entre meta-line e box (leading `_eprint`
de `_render_soft_box`) -- cosmetico, nao bloqueante.
