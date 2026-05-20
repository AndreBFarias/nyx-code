# SPRINT TUI-CLEANUP-01 — Remoção de dead code e correção de docstrings mentirosas

## 0. SPEC (machine-readable)

```yaml
sprint:
  id: TUI-CLEANUP-01
  title: "Remover render_tool_call/render_tool_result órfãos e corrigir docstrings de _observability.py que mentem sobre substituição"
  onda: 22
  bloco: 2.10 Higiene
  prioridade: BAIXA
  tipo: Refactor + Docs
  dependencias: [UX-LAYOUT-02, OBSERVABILITY-01]
  desbloqueia: []

  touches:
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/agent/output.py
      reason: "render_tool_call (linha 349) e render_tool_result (linha 364) não têm caller em nyx/ — UX-LAYOUT-02 prometeu remoção ou @deprecated mas nenhum dos dois foi feito"
      linhas_alvo: "349-380"
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/agent/commands/_observability.py
      reason: "on_compaction_log (linha 23) ficou órfão — cli.py:331-332 chama render_compaction_event direto; on_model_state_log docstring (linha 35) atribui substituição a UX-LAYOUT-02 quando na verdade é UX-BUG-02B que vai implementar"
      linhas_alvo: "22-38"
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/cli.py
      reason: "Se remover on_compaction_log, conferir que cli.py não o importa residualmente"
  creates: []
  removes: []

  n_to_n_pairs:
    - descricao: "Callbacks de observabilidade aparecem no loop/_core.py, no cli.py e nos stubs de _observability.py — todos precisam refletir que compaction tem visual (UX-LAYOUT-02 CONCLUIDA) e model_state ainda está pendente (UX-BUG-02B)"
      paths:
        - /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/agent/loop/_core.py
        - /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/cli.py
        - /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/agent/commands/_observability.py

  forbidden:
    - "Remover função que ainda tem caller — rodar grep antes de deletar"
    - "Marcar @deprecated sem plano de remoção (data de remoção = fim da Onda 22)"
    - "Adicionar emoji, menção a IA"
    - "Mudar comportamento observável do REPL — sprint é 100% no-op em runtime"
    - "Confundir on_compaction_log (órfão) com on_model_state_log (ainda usado em cli.py:345)"

  tests:
    - cmd: "grep -rn 'render_tool_call\\|render_tool_result' nyx/ --include='*.py' | grep -v 'output.py:'"
      timeout: 5
      deve_passar: "zero matches (nenhum caller fora da definição)"
    - cmd: "grep -rn 'on_compaction_log' nyx/ --include='*.py'"
      timeout: 5
      deve_passar: "zero matches (remoção completa)"
    - cmd: "./run.sh --smoke"
      timeout: 60
      deve_passar: "boot ok"
    - cmd: "./run.sh --gauntlet --only rapido"
      timeout: 300
      deve_passar: true
    - cmd: "bash scripts/sprint_invariants.sh"
      timeout: 60
      deve_passar: "13/13 PASS"

  acceptance_criteria:
    - "render_tool_call e render_tool_result removidos de output.py (export __all__ atualizado se existir)"
    - "on_compaction_log removido de _observability.py"
    - "on_model_state_log permanece (ainda consumido em cli.py:345), mas docstring corrigido: menciona 'UX-BUG-02B (toolbar warm/cold)', não UX-LAYOUT-02"
    - "cli.py não tem import residual de on_compaction_log"
    - "Smoke boot OK"
    - "Gauntlet --only rapido passa"
    - "Sprint invariants 13/13 PASS"
    - "Nenhuma mudança de comportamento visível no REPL"
    - "Commit atômico 'refactor(TUI-CLEANUP-01): remove orfaos de output.py e _observability.py + corrige docstrings'"
```

---

**Status:** CONCLUIDA (header corrigido em MASTER-CLEANUP-02 2026-05-20; presença em concluidos/ implica CONCLUIDA conforme convenção do projeto)
**Data criação:** 2026-04-21
**Modelo obrigatório:** claude-opus-4-7 (sem subagentes)

---

## Contexto do projeto (snapshot — não referência)

> **ADRs relevantes:**
>
> - ADR-013 Integração Obrigatória: função sem caller é dead code, viola invariante de registro.
> - ADR-015 Documentação para continuidade: docstring mentirosa engana a próxima IA (meta-regra #6 — hipótese empírica).
> - ADR-024 Render Layer: `print()` só em cli.py e output.py. Remover render_tool_call não afeta o render layer ativo (UX-LAYOUT-02 substituiu pelo render_tool_card_start/end que permanece).
>
> **Estado do sistema (auditado 2026-04-21):**
> - UX-LAYOUT-02 CONCLUIDA (commit 80a6ccc): `render_tool_card_start/end/error` + `render_compaction_event` ativos. cli.py chama diretamente.
> - OBSERVABILITY-01 CONCLUIDA (commit 691f0c5): callbacks `on_compaction` e `on_model_state` declarados e disparados pelo AgentLoop.
> - Auditoria desta sessão detectou:
>   - `render_tool_call` e `render_tool_result` em output.py:349 e 364 sem caller (grep em `nyx/` retorna só as definições e docs/sprints).
>   - `on_compaction_log` em _observability.py:23 — stub órfão; cli.py:331-332 chama `render_compaction_event` direto, passando por cima do stub.
>   - `on_model_state_log` em _observability.py:35 — ainda usado (cli.py:345), mas docstring atribui substituição a UX-LAYOUT-02 quando o espaço visual é responsabilidade de UX-BUG-02B (toolbar warm/cold, PENDENTE).

---

## Problema

### Sintoma observável

```bash
$ grep -rn 'render_tool_call\|render_tool_result' nyx/ --include='*.py'
nyx/agent/output.py:349:def render_tool_call(
nyx/agent/output.py:364:def render_tool_result(result: str, max_chars: int = 110) -> None:

$ grep -rn 'on_compaction_log' nyx/ --include='*.py'
nyx/agent/commands/_observability.py:23:def on_compaction_log(level: int, removed: int, pct_before: float, pct_after: float) -> None:

$ grep -A1 'UX-LAYOUT-02 substitui' nyx/agent/commands/_observability.py
    """Stub do callback on_compaction. UX-LAYOUT-02 substitui por render visual."""
    """Stub do callback on_model_state. UX-LAYOUT-02 substitui por indicador visual."""
```

Três cheiros no mesmo arquivo: duas funções órfãs na render layer e dois docstrings enganando sobre quem substitui o quê.

### Spec UX-LAYOUT-02 (linha 42 do spec):

> "Funções antigas render_tool_call e render_tool_result foram removidas ou marcadas @deprecated"

Nenhuma das duas ações foi tomada.

### Spec OBSERVABILITY-01:

> "Registrar callbacks stub (toolbar não renderiza ainda — fica para UX-LAYOUT-02)"

A parte de `on_compaction` foi de fato substituída por UX-LAYOUT-02 e o stub virou órfão. A parte de `on_model_state` ficou em aberto — quem vai substituir é UX-BUG-02B (toolbar warm/cold), como indicado no comentário de cli.py:190: "UX-BUG-02B adicionará warm/cold aqui". Docstring desatualizada.

---

## Solução proposta

1. **Deletar `render_tool_call` e `render_tool_result`** de output.py. Grep confirma zero caller em `nyx/`.
2. **Deletar `on_compaction_log`** de _observability.py. Grep confirma zero caller (cli.py usa render_compaction_event diretamente).
3. **Corrigir docstring de `on_model_state_log`**: trocar "UX-LAYOUT-02 substitui" por "UX-BUG-02B (toolbar warm/cold) implementará o render visual; este stub ativa o contrato enquanto isso".
4. **Atualizar `__all__` em output.py** (se existir) para remover render_tool_call/result.
5. **Confirmar com smoke** que nada quebra.

---

## Arquivos alvo (paths absolutos)

### `/home/andrefarias/Desenvolvimento/Nyx-Code/nyx/agent/output.py`

**Antes (linhas 349-380):**
```python
def render_tool_call(
    name: str,
    args: dict,
    project_root: str | None = None,
) -> None:
    """Renderiza linha de tool call com bullet em accent color.

    Forma compacta (sem card). Preservada para call-sites que não têm
    duração. Call-sites novos (cli.py on_tool/on_tool_result) usam
    render_tool_card_start/end com duração.
    """
    formatted = format_tool_call(name, args, project_root=project_root)
    print(f"  {ANSI_ACCENT_FG}{BULLETS['tool']}{ANSI_RESET} {formatted}")


def render_tool_result(result: str, max_chars: int = 110) -> None:
    """Resumo colapsado do resultado de uma tool: '    └─ 1ª linha'.

    Erros (prefixos conhecidos) saem em vermelho; sucesso em dim.
    """
    if not result:
        return
    first_line = next(
        (line.strip() for line in result.splitlines() if line.strip()),
        "",
    )
    if not first_line:
        return
    if len(first_line) > max_chars:
        first_line = first_line[: max_chars - 1] + "…"
    color = ANSI_ERROR_FG if is_tool_error(first_line) else ANSI_DIM
    print(f"    {color}{BULLETS['result']} {first_line}{ANSI_RESET}")
```

**Depois:** as duas funções **deletadas**. Se existir `__all__`, remover entradas.

### `/home/andrefarias/Desenvolvimento/Nyx-Code/nyx/agent/commands/_observability.py`

**Antes (linhas 22-38):**
```python
def on_compaction_log(level: int, removed: int, pct_before: float, pct_after: float) -> None:
    """Stub do callback on_compaction. UX-LAYOUT-02 substitui por render visual."""
    logger.debug(
        "compaction level=%d removed=%d before=%.2f after=%.2f",
        level,
        removed,
        pct_before,
        pct_after,
    )


def on_model_state_log(state: str) -> None:
    """Stub do callback on_model_state. UX-LAYOUT-02 substitui por indicador visual."""
    logger.debug("model state -> %s", state)
```

**Depois:**
```python
def on_model_state_log(state: str) -> None:
    """Callback que registra transições cold → warming → warm no log.

    Este stub ativa o contrato de on_model_state no AgentLoop enquanto
    o render visual não chega. UX-BUG-02B (toolbar warm/cold) substituirá
    por indicador visual no bottom_toolbar. Enquanto isso, segue como log
    estruturado para debug de boot lento.
    """
    logger.debug("model state -> %s", state)
```

**Mudanças:**
- `on_compaction_log` **deletado** (órfão).
- `on_model_state_log` **mantido**; docstring reescrito sem mencionar UX-LAYOUT-02 e apontando UX-BUG-02B como sucessor correto.

### `/home/andrefarias/Desenvolvimento/Nyx-Code/nyx/cli.py`

**Antes (linha 334 aprox.):**
```python
from nyx.agent.commands._observability import on_model_state_log
```

**Depois:** inalterado (o import continua válido; só confere que não há import residual `on_compaction_log`).

**Verificar:**
```bash
grep -n 'on_compaction_log' nyx/cli.py
# esperado: zero linhas
```

---

## Diff esperado (resumo)

```
+ 0 arquivos criados
~ 2 arquivos modificados (output.py, _observability.py)
- 0 arquivos removidos
- ~35 linhas no output.py (render_tool_call + render_tool_result)
- ~10 linhas em _observability.py (on_compaction_log + docstring)
+ ~6 linhas em _observability.py (docstring novo em on_model_state_log)
```

---

## Comandos de verificação (literais, copy-paste)

```bash
cd /home/andrefarias/Desenvolvimento/Nyx-Code

# 1. Confirmar orfandade ANTES
grep -rn 'render_tool_call\|render_tool_result' nyx/ --include='*.py'
grep -rn 'on_compaction_log' nyx/ --include='*.py'

# 2. Aplicar edits

# 3. Confirmar limpeza
grep -rn 'render_tool_call\|render_tool_result' nyx/ --include='*.py' | grep -v 'output.py:' || echo "limpo"
grep -rn 'on_compaction_log' nyx/ --include='*.py' || echo "limpo"

# 4. Smoke
./run.sh --smoke

# 5. Gauntlet fase rápida
./run.sh --gauntlet --only rapido

# 6. Invariantes
bash scripts/sprint_invariants.sh | tail -5
```

---

## Critério binário de aceite (IA executora)

- [ ] `grep -rn 'render_tool_call' nyx/` retorna zero matches
- [ ] `grep -rn 'render_tool_result' nyx/` retorna zero matches
- [ ] `grep -rn 'on_compaction_log' nyx/` retorna zero matches
- [ ] Docstring de `on_model_state_log` menciona UX-BUG-02B, não UX-LAYOUT-02
- [ ] `./run.sh --smoke` retorna "boot ok"
- [ ] `./run.sh --gauntlet --only rapido` passa 100%
- [ ] `sprint_invariants.sh` 13/13 PASS
- [ ] Commit `refactor(TUI-CLEANUP-01): remove orfaos de output.py e _observability.py + corrige docstrings`
- [ ] Sprint movida para concluidos/ e SPRINT_ORDER_MASTER atualizado

---

## Guardrails anti-engodo (obrigatórios)

- Antes de deletar cada função, rodar `grep` em `nyx/` + em `scripts/gauntlet/` + em docs Markdown relevantes. Se aparecer em gauntlet, a função ainda é viva (sprint anterior mentiu sobre orfandade) — reportar divergência, não deletar cegamente.
- `on_model_state_log` **não deve ser deletado** — cli.py:345 ainda depende. Confundir com `on_compaction_log` destrói o callback de estado do modelo.
- Mudança é no-op em runtime — qualquer alteração visual (banner, toolbar, tool card) indica que você tocou o lugar errado.

---

## Catálogo de gambiarras proibidas

Ver `dev-journey/08-templates/GAMBIARRAS_POR_SPRINT.md` §"Catálogo Universal".

### Gambiarras específicas

1. **"Marcar @deprecated em vez de deletar".** Sem caller, @deprecated é teatro. Delete.
2. **Deletar `on_model_state_log` junto com `on_compaction_log` "porque ambos são stubs".** Um é órfão, o outro está vivo. Regra: grep ANTES de deletar.
3. **Sumir com `render_tool_call` mas preservar "para compatibilidade futura".** Compatibilidade com quem? Gauntlet não usa. Local-first — API não é contrato externo.
4. **Atualizar docstring apenas em comentário dentro de cli.py.** Comentário efêmero; docstring da função é a fonte que a próxima IA vai ler.
5. **Pular gauntlet rapido "porque mudança é pequena".** Smoke + gauntlet rapido é o mínimo absoluto para confirmar no-op.

---

## Proof-of-work obrigatório (4 passos)

```bash
bash scripts/sprint_invariants.sh > /tmp/inv_before.txt 2>&1
FAIL_BEFORE=$(grep -c '^\[FAIL\]' /tmp/inv_before.txt)

# --- delete render_tool_call + render_tool_result + on_compaction_log; reescrever docstring ---

bash scripts/sprint_invariants.sh > /tmp/inv_after.txt 2>&1
FAIL_AFTER=$(grep -c '^\[FAIL\]' /tmp/inv_after.txt)
diff /tmp/inv_before.txt /tmp/inv_after.txt
[ "$FAIL_AFTER" -le "$FAIL_BEFORE" ] || { echo REGRESSÃO; exit 1; }
```

Colar grep before/after (comprovando orfandade real antes, limpeza depois) + smoke output + gauntlet rapido.

---

## Validação humana (checklist do usuário)

```bash
cd /home/andrefarias/Desenvolvimento/Nyx-Code

git log --oneline -1
git show --stat HEAD
# esperado: refactor(TUI-CLEANUP-01): ...
#           2 arquivos modificados, ~35 linhas a menos em output.py, ~5 a menos em _observability.py

grep -rn 'render_tool_call\|render_tool_result\|on_compaction_log' nyx/ --include='*.py'
# esperado: zero matches

grep -A2 'def on_model_state_log' nyx/agent/commands/_observability.py
# esperado: docstring cita UX-BUG-02B

./run.sh --smoke
# esperado: boot ok
```

---

## Riscos

| Risco | Mitigação |
|-------|-----------|
| Algum teste do gauntlet importa `render_tool_call` diretamente | Grep prévio em `scripts/gauntlet/` — se aparecer, converter o teste para usar `render_tool_card_start/end` |
| Plugin externo (ex: Luna via headless) parseia saída de render_tool_call | Local-first; nenhum plugin externo integrado hoje consome essa API. Se houver, reportar e adicionar shim temporário |
| Docstring de on_model_state_log precisa atualização extra quando UX-BUG-02B concluir | Acompanhado pela spec de UX-BUG-02B (já existe em producao/) — atualizar naquele momento |
| `output.py` tem `__all__` que congela os nomes | Conferir e remover entradas se existir |

---

*"Tirar é criar — o vazio evidencia a forma." -- Lao Tsé (adaptado)*
