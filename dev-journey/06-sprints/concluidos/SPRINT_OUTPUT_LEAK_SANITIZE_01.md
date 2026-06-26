## 0. SPEC (machine-readable)

```yaml
sprint:
  id: OUTPUT-LEAK-SANITIZE-01
  title: "Guard de saida completo: reminder truncado e hints de controle nao vazam no summary"
  onda: 48
  prioridade: ALTA
  tipo: Bugfix
  dependencias: []
  desbloqueia: []

  touches:
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/agent/loop/_iteration.py
      reason: "_SYSTEM_REMINDER_BLOCK exige fechamento; reminder truncado escapa (V08)"
      linhas_alvo: "76-96"
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/agent/loop/_core.py
      reason: "Guard de saida (L317) sai com 2 strips; nao aplica _DONE_HINT_RE nem limpa hints-colchete ao summary (V10)"
      linhas_alvo: "300-322"
  creates: []
  removes: []

  forbidden:
    - "Adicionar emoji"
    - "Remover os hints dos OUTPUTS das tools (read_file/search/list_files/run_command) -- eles induzem o modelo; so o SUMMARY user-facing e sanitizado"
    - "Tocar a reinjecao de reminder no contexto (_maybe_inject_reminder)"
    - "Mexer no proxy.py ou na TUI (V09 e a sprint 406; V07 e a 399)"

  tests:
    - cmd: "./run.sh --gauntlet --only rapido"
      timeout: 300
      deve_passar: true

  acceptance_criteria:
    - "strip_system_reminder remove bloco <system-reminder> mesmo SEM </system-reminder> (truncado ate o fim)"
    - "O summary final nao contem 'Se a tarefa esta completa, chame done()' nem '[Analise e execute a proxima acao.]' nem '[N linhas lidas...]'"
    - "Os OUTPUTS das tools (contexto do modelo) seguem com os hints (nao regredir inducao de done)"
    - "Resposta normal sem artefato passa identica; gauntlet rapido 100%; ruff limpo"
```

---

# Sprint OUTPUT-LEAK-SANITIZE-01 — Guard de saída completo (V08 + V10)

**Status:** CONCLUIDA
**Data criação:** 2026-06-26
**Modelo obrigatório:** claude-opus-4-7 (executor-sprint autorizado pelo dono nesta onda)

---

## Contexto do projeto (snapshot)

> **ADRs:** ADR-027 (microcopy Nyx, zero formato interno na tela), ADR-024 Render Layer, ADR-033 (cadeia limpa), ADR-006 PT-BR, ADR-014 Gauntlet.
> **Estado (2026-06-26):** ONDA-48 (achados V08, V10). O guard de saída único vive em `nyx/agent/loop/_core.py:300-320` e hoje aplica `strip_done_summary_artifact(strip_system_reminder(summary))`. Defesas existentes parciais: `_SYSTEM_REMINDER_BLOCK` (`_iteration.py:76`), `_DONE_HINT_RE` (`_core.py:62`, mas só usado nos tool_results, não no summary final).

---

## Problema

**Achados V08 e V10, provados runtime (2026-06-26).** No Bloco longo (turno 3), o summary final saiu como:
```
OK: Arquivo criado: ~/Desktop/identacao_python.md (0 bytes). Se a tarefa está completa, chame done().

<system-reminder>
Pedido original: agora crie um arquivo identacao_python.md ...
Estado: iter=2, lidos=0, modif=1
Invariantes vigentes (lembr      <- TRUNCADO, sem </system-reminder>
```

Duas falhas no guard de saída:
- **V08:** `_SYSTEM_REMINDER_BLOCK = r"<system-reminder>.*?</system-reminder>"` **exige** o fechamento. Reminder truncado (sem `</system-reminder>`) **não casa** -> não é removido.
- **V10:** o hint de controle "Se a tarefa está completa, chame done()." (anexado pelo `run_command.py:78` ao output) chegou ao summary user-facing. O `_DONE_HINT_RE` existe (`_core.py:62`) mas só é aplicado aos tool_results no contexto, **não ao `status.summary`**. Idem os hints "[Analise e execute a próxima ação.]" (`search.py:99,156`, `read_file.py:66`, `list_files.py:72`).

---

## Solução proposta

Completar o guard de saída, **sem tocar os outputs das tools** (que induzem o modelo): (1) estender `_SYSTEM_REMINDER_BLOCK` para casar reminder truncado; (2) no guard de `_core.py`, aplicar `_DONE_HINT_RE` + um strip dos hints-colchete ao `status.summary`.

---

## Arquivos alvo (paths absolutos)

### `/home/andrefarias/Desenvolvimento/Nyx-Code/nyx/agent/loop/_iteration.py`

# Localização aproximada: linha 76-79 (drift tolerado se trecho casa)
**Antes:**
```python
_SYSTEM_REMINDER_BLOCK = re.compile(
    r"<system-reminder>.*?</system-reminder>",
    re.DOTALL,
)
```

**Depois:**
```python
# OUTPUT-LEAK-SANITIZE-01 (V08): casa o bloco fechado OU um <system-reminder>
# truncado (sem fechamento) ate o fim -- o 3b as vezes regurgita o reminder
# cortado e o `.*?</system-reminder>` antigo nao casava (faltava o fecho).
_SYSTEM_REMINDER_BLOCK = re.compile(
    r"<system-reminder>.*?(?:</system-reminder>|\Z)",
    re.DOTALL,
)
```

**Mudanças:** `(?:</system-reminder>|\Z)` -- fecha no tag OU no fim do texto.

---

### `/home/andrefarias/Desenvolvimento/Nyx-Code/nyx/agent/loop/_core.py`

# Localização aproximada: linha 317 (o guard de saída). Reusa _DONE_HINT_RE (L62) e
# adiciona um regex de hints-colchete. Definir o regex novo perto de _DONE_HINT_RE.

**Antes (o guard, ~L317):**
```python
            status.summary = strip_done_summary_artifact(
                strip_system_reminder(status.summary)
            )
            return status
```

**Depois:**
```python
            # OUTPUT-LEAK-SANITIZE-01 (V10): alem do reminder e do artefato de done,
            # remover do summary user-facing os HINTS DE CONTROLE anexados aos outputs
            # das tools ("...chame done()", "[Analise e execute a proxima acao.]",
            # "[N linhas lidas...]"). Os outputs das tools (contexto do modelo) NAO
            # mudam -- so o texto que chega ao usuario. _DONE_HINT_RE ja existe (L62).
            _clean = strip_done_summary_artifact(strip_system_reminder(status.summary))
            _clean = _DONE_HINT_RE.sub("", _clean)
            _clean = _TOOL_HINT_BRACKET_RE.sub("", _clean)
            status.summary = _clean.strip()
            return status
```

**E adicionar perto de `_DONE_HINT_RE` (~L62):**
```python
# OUTPUT-LEAK-SANITIZE-01 (V10): hints entre colchetes anexados aos outputs de
# read_file/search/list_files ("[N linhas lidas. Analise e execute a proxima acao.]",
# "[Analise e execute a proxima acao.]"). So removidos do summary user-facing.
_TOOL_HINT_BRACKET_RE = re.compile(
    r"\s*\[[^\]]*(?:Analise e execute|linhas lidas)[^\]]*\]",
    re.IGNORECASE | re.DOTALL,
)
```

**Mudanças:** guard aplica `_DONE_HINT_RE` + `_TOOL_HINT_BRACKET_RE` ao summary; novo regex de hints-colchete.

---

## Diff esperado (resumo)

```
~ 2 arquivos modificados (nyx/agent/loop/_iteration.py, nyx/agent/loop/_core.py)
+ ~12 linhas líquidas
```

---

## Comandos de verificação (literais, copy-paste)

```bash
# 1. Static + acentuação
python -m ruff check nyx/
python3 ~/.config/zsh/scripts/validar-acentuacao.py --paths nyx/agent/loop/_iteration.py nyx/agent/loop/_core.py

# 2. Unidade dos strips (lógica pura, rodar inline; NÃO criar test_*.py):
python -c "
from nyx.agent.loop._iteration import strip_system_reminder as ssr
# reminder truncado (sem fechamento) -> removido:
assert '<system-reminder>' not in ssr('texto util\n<system-reminder>\nPedido: x\nInvariantes (lembr')
# reminder fechado -> removido:
assert ssr('ok <system-reminder>a</system-reminder> fim').strip() == 'ok  fim'.strip() or 'system-reminder' not in ssr('ok <system-reminder>a</system-reminder> fim')
# sem reminder -> idêntico:
assert ssr('resposta normal') == 'resposta normal'
print('OK strip reminder')
"

# 3. PROOF RUNTIME: criar arquivo em sessão e conferir summary limpo:
printf '%s\n' '{\"type\":\"request\",\"content\":\"crie /tmp/nyx_v395.txt com oi\"}' \
  | NYX_AUTO_APPROVE=1 ./run.sh --headless 2>/dev/null | grep -o 'response.*' | head -1
# ESPERADO no summary: SEM "<system-reminder", SEM "chame done()", SEM "[Analise e execute". COLE.
rm -f /tmp/nyx_v395.txt

# 4. Gauntlet
./run.sh --gauntlet --only rapido
```

---

## Critério binário de aceite

- [ ] `_SYSTEM_REMINDER_BLOCK` casa reminder truncado (assert do passo 2 passa)
- [ ] Guard de saída aplica `_DONE_HINT_RE` + `_TOOL_HINT_BRACKET_RE` ao summary
- [ ] Proof runtime: summary sem reminder/done-hint/colchete-hint (colar)
- [ ] Outputs das tools INTACTOS (grep confirma que run_command.py:78 / read_file.py:66 / search.py / list_files.py seguem com os hints)
- [ ] ruff limpo, acentuação rc=0, invariantes FAIL_AFTER <= FAIL_BEFORE, gauntlet rapido 100%
- [ ] 395 CONCLUIDA no MASTER; spec movida para concluidos/
- [ ] Commit: `fix(loop): 395 OUTPUT-LEAK-SANITIZE-01 -- reminder truncado e hints de controle fora do summary (V08,V10)`

---

## Guardrails anti-engodo

NÃO concluir se: removeu os hints dos OUTPUTS das tools (regride indução de done); o proof runtime não foi colado; tocou TUI/proxy; gauntlet "passou" sem output. Falha -> `[SPRINT 395] BLOQUEADA: <motivo>`.

---

## Proof-of-work (4 passos)

inv_before -> implementar -> inv_after (<=) -> diff. Colar tail de ambos + diff + asserts do passo 2 + o summary do proof runtime + grep confirmando hints intactos nos outputs das tools + `git show --stat HEAD`.

---

## Riscos

| Risco | Mitigação |
|-------|-----------|
| `\Z` no reminder regex apaga texto útil após um `<system-reminder>` legítimo truncado | Reminder só é injetado pela infra; texto após `<system-reminder>` sem fecho é sempre lixo de regurgitação. `.*?` é lazy: para no 1º fecho se existir. |
| Remover done-hint do summary faz o modelo parar de chamar done | NÃO removemos do output (contexto do modelo) -- só do summary user-facing. O modelo segue vendo o hint. |
| `_TOOL_HINT_BRACKET_RE` casa um colchete legítimo da resposta | Ancorado em "Analise e execute"/"linhas lidas" (frases internas fixas), não qualquer `[...]`. |

---

*"O bastidor não pertence ao palco." -- princípio de render*
