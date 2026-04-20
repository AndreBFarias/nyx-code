# SPRINT UX-LAYOUT-01B — Toolbar repaginada (ctx N/M tok, bypass em roxo, schema de secções)

## 0. SPEC (machine-readable)

```yaml
sprint:
  id: UX-LAYOUT-01B
  title: "_bottom_toolbar reescrito: ctx% + N/M tokens, bypass ON roxo / OFF muted, schema de secções separadas por · para extensão por outras sprints"
  onda: 22
  bloco: 4
  prioridade: ALTA
  tipo: Feature
  dependencias: [UX-LAYOUT-01A, OBSERVABILITY-01]
  desbloqueia: [UX-LAYOUT-02]

  touches:
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/cli.py
      reason: "_bottom_toolbar reescrito consumindo design_tokens; secções padronizadas separadas por ·"

  creates: []
  removes: []

  n_to_n_pairs:
    - descricao: "app_state['total_tokens'] e ['max_tokens'] vêm de agent.get_context_info — atualizar em cli.py alinhado ao método do agent"
      paths:
        - /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/cli.py
        - /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/agent/loop/__init__.py
    - descricao: "OBSERVABILITY-01 fornece on_model_state (warm/cold) que UX-BUG-02B consumirá; esta sprint apenas deixa espaço no schema de secções, não adiciona a secção aqui"
      paths:
        - /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/cli.py

  forbidden:
    - "Hex hardcoded em cli.py"
    - "Adicionar emoji"
    - "Usar 'print()' em modules novos (permitido apenas em cli.py e agent/output.py — ADR-024)"
    - "Menção a Claude/GPT/Anthropic"
    - "Tocar em _build_banner (escopo de UX-LAYOUT-01A)"
    - "Tocar em render_user_input (escopo de TUI-FIX-07B)"
    - "Incluir a secção warm/cold (é trabalho de UX-BUG-02B) — apenas deixar schema preparado"
    - "Sobrescrever bottom_toolbar registrado por TUI-FIX-07A (compor, não colidir)"

  tests:
    - cmd: "python -c 'from nyx.cli import _bottom_toolbar; t = _bottom_toolbar(); print(t)'"
      timeout: 30
      deve_passar: true
    - cmd: "./run.sh --gauntlet --only tui"
      timeout: 300
      deve_passar: true
    - cmd: "./run.sh --smoke"
      timeout: 60
      deve_passar: true

  acceptance_criteria:
    - "Toolbar mostra 'ctx X% (Ntok/Mtok)' quando max_tokens > 0; 'ctx X%' simples quando max_tokens == 0"
    - "Bypass ON: fundo NYX_PURPLE, texto em branco/negrito, separado por 2 espaços"
    - "Bypass OFF: texto em NYX_MUTED com dica 'shift+tab: bypass'"
    - "Secções separadas por ' · ' (bullet muted) em schema documentado em docstring"
    - "Zero hex hardcoded em cli.py (grep retorna 0)"
    - "app_state['total_tokens'] e ['max_tokens'] alimentados por agent.get_context_info no loop"
    - "Gauntlet fase tui passa 100%"
    - "./run.sh --smoke continua PASS"
    - "Acentuação PT-BR correta em tudo novo"
```

---

# Sprint UX-LAYOUT-01B — Toolbar repaginada

**Status:** PENDENTE
**Data criação:** 2026-04-19
**Origem:** split de UX-LAYOUT-01 em 2 sprints. Este arquivo cobre **apenas toolbar**. Banner foi para UX-LAYOUT-01A.
**Modelo obrigatório:** claude-opus-4-7 (sem subagentes)

---

## Contexto do projeto (snapshot — não referência)

> **ADRs relevantes:**
>
> - ADR-001 Local First.
> - ADR-004 Zero Emojis.
> - ADR-005 Anonimato.
> - ADR-006 PT-BR.
> - ADR-013 Integração Obrigatória.
> - ADR-014 Testes via Gauntlet.
> - ADR-020 Testes via run.sh.
> - ADR-023 Design System: tokens em `nyx/themes/design_tokens.py`.
> - ADR-024 Render Layer.
>
> **Estado do sistema:**
> - Sprints anteriores: UX-LAYOUT-01A CONCLUIDA (banner), OBSERVABILITY-01 CONCLUIDA (on_model_state disponível).
> - TUI-FIX-07A pode já ter registrado `bottom_toolbar` no `PromptSession` — esta sprint **compõe** com o callable existente (não sobrescreve).

---

## Problema

`_bottom_toolbar` atual em `cli.py`:

1. Mostra apenas `ctx X%` — não responde "X% de quanto?". Usuário não sabe se `11%` são `5k/45k` ou `500/4500`.
2. Bypass ON sem realce visual forte (ex.: só texto, sem fundo). Fácil de perder.
3. Sem schema de secções: cada extensão futura insere sua parte de forma ad-hoc, colidindo com bypass e causando desalinhamento.

Sprint seguinte **UX-BUG-02B** vai adicionar uma secção warm/cold (estado do modelo), então esta sprint precisa deixar o schema preparado.

---

## Solução proposta

- Reescrever `_bottom_toolbar()` consumindo `NYX_ACCENT`, `NYX_MUTED`, `NYX_PURPLE`, `BULLETS` de `design_tokens`.
- `ctx_label`: `ctx X% (Ntok/Mtok)` se `max_tokens>0`; `ctx X%` caso contrário.
- Secções separadas por ` · ` (bullet muted).
- Bypass ON: fragmento com `bg:{NYX_PURPLE} fg:#ffffff bold`.
- Schema documentado em docstring: `[ctx] · [modelo · iter · lidos · modif] [bypass] [<extensões futuras>]`.
- Alimentar `app_state["total_tokens"]` e `["max_tokens"]` a partir de `agent.get_context_info()` no loop do REPL.
- Se TUI-FIX-07A já registrou `bottom_toolbar`, compor: esta sprint passa a ser o único callable, absorvendo o conteúdo de TUI-FIX-07A.

---

## Arquivos alvo (paths absolutos)

### `/home/andrefarias/Desenvolvimento/Nyx-Code/nyx/cli.py`

**Antes (conceitual):**
```python
def _bottom_toolbar():
    ctx = app_state.get("ctx_pct", 0)
    return HTML(f"<b>ctx {ctx}%</b>")
```

**Depois:**
```python
def _bottom_toolbar():
    """Toolbar inferior do PromptSession.

    Schema de secções (separadas por ' · '):
      [ctx]                     -- ctx X% (Ntok/Mtok) ou ctx X%
      [modelo · iter · lidos · modif]
      [bypass]                  -- ON: fundo roxo; OFF: dica muted
      [<extensões futuras>]     -- UX-BUG-02B adicionará warm/cold aqui

    Contrato: cada secção é um FormattedText fragment (ou grupo). Novas
    extensões anexam seus fragments ao final de `parts`, sem sobrescrever.
    """
    from prompt_toolkit.formatted_text import FormattedText
    from nyx.themes.design_tokens import (
        NYX_ACCENT, NYX_MUTED, NYX_PURPLE, BULLETS,
    )

    ctx_pct = app_state.get("ctx_pct", 0)
    total_tok = app_state.get("total_tokens", 0)
    max_tok = app_state.get("max_tokens", 0)
    iter_n = app_state.get("iter_n", 0)
    reads = app_state.get("reads", 0)
    mods = app_state.get("mods", 0)
    model = app_state.get("model", "?")

    parts: list[tuple[str, str]] = []

    ctx_label = f"ctx {ctx_pct}%"
    if max_tok:
        ctx_label += f" ({total_tok}/{max_tok}tok)"
    parts.append((f"fg:{NYX_ACCENT}", ctx_label))

    meta = f" · {model} · iter {iter_n} · lidos {reads} · modif {mods}"
    parts.append((f"fg:{NYX_MUTED}", meta))

    if app_state.get("bypass"):
        parts.append(("", "  "))
        parts.append(
            (f"bg:{NYX_PURPLE} fg:#ffffff bold", f" {BULLETS['bypass_on']} bypass ON "),
        )
    else:
        parts.append((f"fg:{NYX_MUTED}", f"   {BULLETS['bypass_off']} shift+tab: bypass"))

    return FormattedText(parts)
```

E no loop do REPL (antes de `session.prompt`):

```python
ctx_info = agent.get_context_info()
app_state["ctx_pct"] = int(ctx_info.get("pct", 0) * 100)
app_state["total_tokens"] = ctx_info.get("total_tokens", 0)
app_state["max_tokens"] = ctx_info.get("max_tokens", 0)
```

**Mudanças:**
- Reescrita completa de `_bottom_toolbar` consumindo design_tokens.
- Docstring documenta schema de secções (para extensão futura).
- `app_state` recebe `total_tokens` e `max_tokens` do agent.

Se TUI-FIX-07A já registrou um `bottom_toolbar` com o footer de `ctx/iter/lidos/modif`, **esta sprint absorve** — o callable passa a ser o único registrado no `PromptSession`. Não deve haver dois `bottom_toolbar` concorrentes.

---

## Diff esperado (resumo)

```
+ 0 arquivos criados
~ 1 arquivo modificado
- 0 arquivos removidos
+ ~40 linhas líquidas
```

---

## Comandos de verificação (literais, copy-paste)

```bash
cd /home/andrefarias/Desenvolvimento/Nyx-Code

# 1. Validação estática
python -m ruff check nyx/cli.py

# 2. Zero hex hardcoded (exceto #ffffff do fragmento de bypass, que é padrão do prompt_toolkit; ou melhor, derivar também)
grep -nE '#[0-9A-Fa-f]{6}' nyx/cli.py
# Esperado: apenas o #ffffff do fragmento de bypass (documentar no relatório)
# Se design_tokens expõe NYX_ON_PURPLE, usar; caso contrário, #ffffff é aceitável por ser branco puro padrão

# 3. Toolbar gera FormattedText sem exceção
python -c "
import nyx.cli as cli
cli.app_state.update({'ctx_pct': 42, 'total_tokens': 5000, 'max_tokens': 45000, 'iter_n': 3, 'reads': 7, 'mods': 2, 'model': 'qwen3:4b', 'bypass': False})
fr = cli._bottom_toolbar()
texto = ''.join(p[1] for p in fr)
assert 'ctx 42%' in texto and '5000/45000tok' in texto, texto
assert 'shift+tab' in texto, texto
print('toolbar OFF OK:', texto)

cli.app_state['bypass'] = True
fr = cli._bottom_toolbar()
texto = ''.join(p[1] for p in fr)
assert 'bypass ON' in texto, texto
print('toolbar ON OK:', texto)
"

# 4. Gauntlet
./run.sh --gauntlet --only tui

# 5. Smoke
./run.sh --smoke

# 6. Validação visual
./run.sh
# Esperado no toolbar: 'ctx X% (Ntok/Mtok) · qwen3:4b · iter N · lidos R · modif M    · shift+tab: bypass'
# Shift+Tab ativa bypass — fragmento vira fundo roxo com texto branco.
```

---

## Critério binário de aceite (IA executora)

- [ ] Toolbar mostra `ctx X% (Ntok/Mtok)` quando `max_tokens > 0`
- [ ] Toolbar mostra `ctx X%` sem tokens quando `max_tokens == 0`
- [ ] Bypass ON: fragmento com fundo roxo visível
- [ ] Bypass OFF: dica `shift+tab: bypass` em muted
- [ ] Secções separadas por ` · ` documentadas em docstring
- [ ] `app_state['total_tokens']` e `['max_tokens']` alimentados no loop
- [ ] Zero hex hardcoded além do aceitável documentado
- [ ] Não existe mais de um `bottom_toolbar` no `PromptSession`
- [ ] Gauntlet `--only tui` passa 100%
- [ ] `./run.sh --smoke` continua PASS
- [ ] `ruff` não reclama
- [ ] Nenhuma violação de `forbidden[]`
- [ ] `SPRINT_ORDER_MASTER.md` atualizado com hash
- [ ] Sprint movida para `concluidos/`
- [ ] Commit atômico criado

---

## Guardrails anti-engodo (obrigatórios)

A IA executora **NÃO pode marcar sprint como concluída** se:

- `total_tokens`/`max_tokens` ficaram em 0 fixo (esqueceu de propagar do agent).
- Bypass ON exibido com mesma cor do OFF (meta-regra #4: feature flag falsa — visual precisa ser observável).
- Mexeu em `_build_banner` (fora de escopo — UX-LAYOUT-01A).
- Adicionou a secção warm/cold (é trabalho de UX-BUG-02B; apenas o schema é preparado aqui).
- Registrou segundo `bottom_toolbar` em paralelo ao de TUI-FIX-07A — precisa absorver o conteúdo, não duplicar.

Reportar se falhar:
```
[SPRINT UX-LAYOUT-01B] BLOQUEADA: <motivo em 1 linha>
```

---

## Gambiarras específicas desta sprint

1. **`total_tokens`/`max_tokens` hardcoded.** Retornar `(5000, 45000)` fixo. Proibido — precisa vir de `agent.get_context_info()`.
2. **Bypass sem diferença visual.** Mesma cor ON e OFF. Gambiarra #2 (stub como implementação).
3. **Duplicar `bottom_toolbar`.** Registrar um novo callable em paralelo ao de TUI-FIX-07A. Proibido — absorver, deixar um único.
4. **Hex redefinido em cli.py.** Proibido — design_tokens é a fonte.
5. **Incluir secção warm/cold.** Fora de escopo — UX-BUG-02B é responsável; apenas deixar schema documentado.
6. **Criar constantes `NYX_PURPLE`/`NYX_MUTED` em cli.py.** Proibido — meta-regra #1 (sincronização N-para-N).

---

## Proof-of-work obrigatório (4 passos)

```bash
# PASSO 1 — ANTES
bash scripts/sprint_invariants.sh > /tmp/inv_before.txt 2>&1
FAIL_BEFORE=$(grep -c "^\[FAIL\]" /tmp/inv_before.txt)

# PASSO 2 — implementação

# PASSO 3 — DEPOIS
bash scripts/sprint_invariants.sh > /tmp/inv_after.txt 2>&1
FAIL_AFTER=$(grep -c "^\[FAIL\]" /tmp/inv_after.txt)

# PASSO 4 — FAIL_AFTER <= FAIL_BEFORE; diff colado
```

Colar no relatório: `tail -10` de cada snapshot, `diff`, output literal do test harness (com bypass OFF e ON), gauntlet tui, `git show --stat HEAD`. Incluir descrição textual das cores observadas no REPL real (ON = fundo roxo; OFF = texto muted).

---

## Validação humana (checklist do usuário)

```bash
cd /home/andrefarias/Desenvolvimento/Nyx-Code
git log --oneline -1
git show --stat HEAD

./run.sh
# 1. Toolbar mostra 'ctx X% (Ntok/Mtok) · qwen3:4b · iter N · lidos R · modif M'.
# 2. Shift+Tab: bypass vira roxo brilhante.
# 3. Shift+Tab: volta para texto muted.
# 4. Ctrl+D.

ls dev-journey/06-sprints/concluidos/SPRINT_UX_LAYOUT_01B.md
ls dev-journey/06-sprints/producao/SPRINT_UX_LAYOUT_01B.md  # NÃO deve existir
```

---

## Riscos

| Risco | Mitigação |
|-------|-----------|
| `agent.get_context_info()` não existe ou retorna schema diferente | Grep e ler código do agent antes; adaptar leitura conforme o retorno real — nunca assumir chaves sem conferir |
| TUI-FIX-07A já registrou `bottom_toolbar` | Substituir por este callable (absorver o conteúdo), nunca registrar dois |
| Toolbar largo demais em 60 cols — `tok` e `iter` podem overflow | Se `cols<80`, omitir o `(Ntok/Mtok)` e mostrar apenas `ctx X%`; documentar na docstring |
| `BULLETS['bypass_on']`/`bypass_off` ausentes em design_tokens | Conferir; se ausentes, criar sprint de patch no design_tokens — não duplicar literal aqui |
| Roxo ilegível em tema claro | Nyx é dark-first (ADR-023 implícita); documentar no relatório |

---

*"A precisão começa na moldura." -- Johann Wolfgang von Goethe*
