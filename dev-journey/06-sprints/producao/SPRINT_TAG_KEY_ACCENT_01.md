# SPRINT TAG-KEY-ACCENT-01 — Acentuação nas chaves internas de TAG_STYLES/TAG_LABELS

## 0. SPEC (machine-readable)

```yaml
sprint:
  id: TAG-KEY-ACCENT-01
  title: "Renomear chaves 'sessao'/'metricas' em TAG_STYLES/TAG_LABELS com acentuação PT-BR canônica e atualizar call-sites"
  onda: 22
  bloco: 2.10 Higiene
  prioridade: BAIXA
  tipo: Refactor + Docs
  dependencias: []
  desbloqueia: []

  touches:
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/agent/output.py
      reason: "TAG_STYLES (linhas 43-53) e TAG_LABELS (linhas 55-67) usam chaves ASCII 'sessao'/'metricas' para mapear tipos de mensagem. Condicional tag == 'sessao' em linha 137. Violação pré-existente de ADR-006 flagada por validar-acentuacao.py (pré-existente desde d945bcd8, 2025-05-01)."
      linhas_alvo: "43-67, 137"
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/cli.py
      reason: "Call-sites output('sessao', ...) em linhas 427 e 675. Precisam atualizar em N-para-N com a renomeação."
      linhas_alvo: "427, 675"
  creates: []
  removes: []

  n_to_n_pairs:
    - descricao: "Chaves 'sessao' e 'metricas' ligam TAG_STYLES, TAG_LABELS, condicional em output.py e call-sites output() em cli.py. Renomear em qualquer um exige renomear em todos."
      paths:
        - /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/agent/output.py
        - /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/cli.py

  forbidden:
    - "Remover as chaves sem substituto — call-sites quebram silenciosamente (tag não encontrada cai em default)"
    - "Deixar aliases duplicados (tanto 'sessao' quanto 'sessão' em TAG_STYLES) — proliferação N-para-N"
    - "Tocar em lógica de render de TAG_STYLES — escopo é renomear chave, não reimplementar"
    - "Adicionar emoji, menção a IA"
    - "Reinterpretar a sprint como 'desabilitar o linter' — ADR-006 é lei; chaves PT-BR internas também seguem"
    - "Alterar TAG_LABELS (valor visível); só a KEY precisa de acento. O VALOR já tem acento ('sessão', 'métricas')"

  tests:
    - cmd: "python -c 'from nyx.agent.output import TAG_STYLES, TAG_LABELS; assert \"sessão\" in TAG_STYLES; assert \"métricas\" in TAG_STYLES; assert \"sessao\" not in TAG_STYLES'"
      timeout: 10
      deve_passar: true
    - cmd: "grep -rn '\"sessao\"\\|\"metricas\"' nyx/ --include='*.py'"
      timeout: 5
      deve_passar: "zero matches (tudo renomeado)"
    - cmd: "./run.sh --smoke"
      timeout: 60
      deve_passar: "boot ok"
    - cmd: "./run.sh --gauntlet --only rapido"
      timeout: 300
      deve_passar: true
    - cmd: "bash scripts/sprint_invariants.sh"
      timeout: 60
      deve_passar: "13/13 PASS"
    - cmd: "python3 ~/.config/zsh/scripts/validar-acentuacao.py --paths nyx/agent/output.py nyx/cli.py"
      timeout: 10
      deve_passar: "zero violações em output.py e cli.py referentes a 'sessao'/'metricas'"

  acceptance_criteria:
    - "TAG_STYLES tem chaves 'sessão' e 'métricas' (valores preservados: bold NYX_ACCENT, dim NYX_ACCENT)"
    - "TAG_LABELS tem chaves 'sessão' e 'métricas' mapeando para 'sessão' e 'métricas' (idempotente — chave = valor)"
    - "Condicional em output.py (antes 'if tag == \"sessao\"') usa a chave nova 'sessão'"
    - "cli.py:427,675 chama output('sessão', ...) e output('métricas', ...) se aplicável"
    - "grep -rn '\"sessao\"\\|\"metricas\"' nyx/ --include='*.py' retorna zero matches"
    - "validar-acentuacao.py exit 0 para output.py e cli.py (ou pelo menos zero violações ligadas a esse débito)"
    - "Smoke boot OK"
    - "Gauntlet --only rapido 100% (mudança é no-op em runtime se renomeação estiver consistente)"
    - "Teste manual: rodar REPL, disparar comando que emite tag 'sessão' (ex: /session save, /context show) e conferir que label renderiza corretamente"
    - "Commit atômico 'refactor(TAG-KEY-ACCENT-01): chaves PT-BR com acentuação em TAG_STYLES/TAG_LABELS + call-sites'"
```

---

**Status:** PENDENTE
**Data criação:** 2026-04-21
**Modelo obrigatório:** claude-opus-4-7 (sem subagentes)

---

## Contexto do projeto (snapshot — não referência)

> **ADRs relevantes:**
>
> - ADR-006 PT-BR: "ACENTUAÇÃO CORRETA É OBRIGATÓRIA em TODAS as respostas, código, commits, docs, comentários e variáveis em português." Chaves de dicionário em PT-BR são variáveis — entram na regra.
> - ADR-013 Integração Obrigatória: chaves que atravessam módulos (output.py ↔ cli.py) são contrato e devem ser consistentes.
> - Meta-regra #1: valor que aparece em N lugares atualizar em todos ou nenhum.
>
> **Estado do sistema (verificado 2026-04-21 pós TUI-CLEANUP-01):**
> - Commit atual: `4238526`.
> - Débito detectado originalmente em ERROR-MSG-01 (achado colateral "TAG-KEY-ACCENT-01", 2026-04-21) e reconfirmado em COMPLETER-SEPS-01 (mesmo débito, ID duplicado "ACENT-API-KEYS-01"). Consolidado aqui sob ID único TAG-KEY-ACCENT-01.
> - Origem histórica: commit `d945bcd8` (2025-05-01) — versão inicial do `RichOutput` com chaves ASCII.
> - Localização exata:
>   ```
>   nyx/agent/output.py:50:    "sessao": f"bold {NYX_ACCENT}",
>   nyx/agent/output.py:51:    "metricas": f"dim {NYX_ACCENT}",
>   nyx/agent/output.py:62:    "sessao": "sessão",
>   nyx/agent/output.py:63:    "metricas": "métricas",
>   nyx/agent/output.py:137:        if tag == "sessao":
>   nyx/cli.py:427:                    output("sessao", status_msg)
>   nyx/cli.py:675:        output("sessão", session_summary)  # já tem acento neste call-site? validar ao abrir
>   ```
> - `validar-acentuacao.py` reporta essas 5 linhas como violações (não existe — as chaves são strings, não palavras faladas; mas contagem literal casa o padrão `\bsessao\b`).

---

## Problema

### Sintoma observável

```bash
$ python3 ~/.config/zsh/scripts/validar-acentuacao.py --paths nyx/agent/output.py nyx/cli.py
nyx/agent/output.py:50: 'sessao' sem acento — esperado 'sessão'
nyx/agent/output.py:51: 'metricas' sem acento — esperado 'métricas'
nyx/agent/output.py:62: 'sessao' sem acento — esperado 'sessão'
nyx/agent/output.py:63: 'metricas' sem acento — esperado 'métricas'
nyx/agent/output.py:137: 'sessao' sem acento — esperado 'sessão'
nyx/cli.py:427: 'sessao' sem acento — esperado 'sessão'
```

Chaves internas de `TAG_STYLES` e `TAG_LABELS` em ASCII violam ADR-006. Os **valores** estão corretos (`"sessão"`, `"métricas"`), apenas as **chaves** sofrem.

### Origem

O dict foi escrito em maio/2025 como API interna do `RichOutput`. Tradição de chaves ASCII em Python (antecede convenções PT-BR neste projeto). Consolidou-se quando ADR-006 foi formalizado em 2026.

---

## Solução proposta

1. **Renomear as chaves** nos dicts `TAG_STYLES` e `TAG_LABELS` em `output.py` de `"sessao"`/`"metricas"` para `"sessão"`/`"métricas"`.
2. **Atualizar a condicional** em `output.py:137` (`if tag == "sessao"` → `if tag == "sessão"`).
3. **Atualizar call-sites** em `cli.py:427,675` de `output("sessao", ...)` para `output("sessão", ...)`.
4. **Opcional/defensivo**: adicionar no dict um `.get("sessao", None)` fallback? **NÃO** — ADR-013 proíbe shim de compatibilidade local; se algum call-site externo (não encontrado) quebrar, abrir sprint com ID para esse caller.
5. **Grep final** confirma zero remanescente.
6. **Testes**: invariants 13/13 + gauntlet rapido + smoke.

---

## Arquivos alvo (paths absolutos)

### `/home/andrefarias/Desenvolvimento/Nyx-Code/nyx/agent/output.py`

**Antes (linhas 43-67, aprox.):**
```python
TAG_STYLES: dict[str, str] = {
    "ok": f"bold {NYX_SUCCESS}",
    "erro": f"bold {NYX_ERROR}",
    "aviso": f"bold {NYX_WARNING}",
    "info": NYX_ACCENT,
    "debug": f"dim {NYX_MUTED}",
    "ferramenta": NYX_ACCENT,
    "sessao": f"bold {NYX_ACCENT}",
    "metricas": f"dim {NYX_ACCENT}",
}


TAG_LABELS: dict[str, str] = {
    "ok": "ok",
    "erro": "erro",
    "aviso": "aviso",
    "info": "info",
    "debug": "debug",
    "ferramenta": "ferramenta",
    "sessao": "sessão",
    "metricas": "métricas",
}
```

**Depois:**
```python
TAG_STYLES: dict[str, str] = {
    "ok": f"bold {NYX_SUCCESS}",
    "erro": f"bold {NYX_ERROR}",
    "aviso": f"bold {NYX_WARNING}",
    "info": NYX_ACCENT,
    "debug": f"dim {NYX_MUTED}",
    "ferramenta": NYX_ACCENT,
    "sessão": f"bold {NYX_ACCENT}",
    "métricas": f"dim {NYX_ACCENT}",
}


TAG_LABELS: dict[str, str] = {
    "ok": "ok",
    "erro": "erro",
    "aviso": "aviso",
    "info": "info",
    "debug": "debug",
    "ferramenta": "ferramenta",
    "sessão": "sessão",
    "métricas": "métricas",
}
```

**E também linha 137:**
```python
# antes
if tag == "sessao":
# depois
if tag == "sessão":
```

### `/home/andrefarias/Desenvolvimento/Nyx-Code/nyx/cli.py`

**Antes (linhas 427 e 675, aprox.):**
```python
output("sessao", status_msg)
# e
output("sessao", session_summary)
```

**Depois:**
```python
output("sessão", status_msg)
# e
output("sessão", session_summary)
```

---

## Diff esperado (resumo)

```
+ 0 arquivos criados
~ 2 arquivos modificados (output.py, cli.py)
- 0 arquivos removidos
+ ~7 linhas líquidas (só renomeação literal)
```

---

## Comandos de verificação (literais, copy-paste)

```bash
cd /home/andrefarias/Desenvolvimento/Nyx-Code

# 1. Inventário ANTES
grep -rn '"sessao"\|"metricas"' nyx/ --include='*.py'

# 2. Aplicar edits

# 3. Confirmar limpeza
grep -rn '"sessao"\|"metricas"' nyx/ --include='*.py'
# esperado: zero matches

# 4. Confirmar presença com acento
grep -rn '"sessão"\|"métricas"' nyx/agent/output.py nyx/cli.py

# 5. Teste runtime de import
python -c "from nyx.agent.output import TAG_STYLES, TAG_LABELS; \
  assert 'sessão' in TAG_STYLES and 'métricas' in TAG_STYLES; \
  assert 'sessao' not in TAG_STYLES and 'metricas' not in TAG_STYLES; \
  print('keys ok')"

# 6. Validador de acentuação
python3 ~/.config/zsh/scripts/validar-acentuacao.py --paths nyx/agent/output.py nyx/cli.py

# 7. Smoke + gauntlet
./run.sh --smoke
./run.sh --gauntlet --only rapido

# 8. Invariantes
bash scripts/sprint_invariants.sh | tail -5
```

---

## Critério binário de aceite (IA executora)

- [ ] `grep '"sessao"' nyx/ -r` zero matches
- [ ] `grep '"metricas"' nyx/ -r` zero matches
- [ ] `TAG_STYLES["sessão"]` e `TAG_STYLES["métricas"]` existem em runtime
- [ ] Condicional `tag == "sessão"` em output.py (sem acento-sem)
- [ ] cli.py:427,675 usam `output("sessão", ...)` / `output("métricas", ...)` conforme cada call
- [ ] `validar-acentuacao.py` não reporta violação ligada a essas chaves
- [ ] Smoke boot OK
- [ ] Gauntlet `--only rapido` passa
- [ ] `sprint_invariants.sh` 13/13
- [ ] Commit atômico `refactor(TAG-KEY-ACCENT-01): chaves PT-BR com acentuação em TAG_STYLES/TAG_LABELS + call-sites`

---

## Guardrails anti-engodo (obrigatórios)

- Antes de editar, grep EXAUSTIVO: `grep -rn "'sessao'\|\"sessao\"\|'metricas'\|\"metricas\"" nyx/ scripts/` — se aparecer em gauntlet ou em outro módulo fora do escopo declarado, reportar e expandir touches (ou abrir sprint nova).
- Não adicione aliases duplicados (`TAG_STYLES["sessao"] = TAG_STYLES["sessão"]`). É exatamente o anti-pattern que motivou esta sprint.
- Mudança é pequena mas toca string de API interna — rodar gauntlet inteiro ou fase que usa RichOutput (`--only interface` ou `--only rapido` cobre).
- Se o comando `/session save` ou similar emite tag via RichOutput, testar manualmente no REPL e confirmar que label `[sessão]` continua aparecendo.

---

## Catálogo de gambiarras proibidas

Ver `dev-journey/08-templates/GAMBIARRAS_POR_SPRINT.md` §"Catálogo Universal".

### Gambiarras específicas

1. **Alias duplicado.** `TAG_STYLES["sessao"] = TAG_STYLES["sessão"]`. Anti-scoping — proliferação.
2. **Desabilitar o linter PT-BR só para esse arquivo.** ADR-006 é global.
3. **Deixar condicional `tag in ("sessao", "sessão")`**. Meia-medida. Fica proibido.
4. **Renomear apenas a key de STYLES mas não de LABELS** (ou vice-versa). N-para-N exige ambos.
5. **Pular cli.py:427,675**. Call-site é parte do N-para-N; esquecer quebra runtime.

---

## Proof-of-work obrigatório (4 passos)

```bash
bash scripts/sprint_invariants.sh > /tmp/inv_before.txt 2>&1
FAIL_BEFORE=$(grep -c '^\[FAIL\]' /tmp/inv_before.txt)

# --- rename keys + call-sites ---

bash scripts/sprint_invariants.sh > /tmp/inv_after.txt 2>&1
FAIL_AFTER=$(grep -c '^\[FAIL\]' /tmp/inv_after.txt)
diff /tmp/inv_before.txt /tmp/inv_after.txt
[ "$FAIL_AFTER" -le "$FAIL_BEFORE" ] || { echo REGRESSÃO; exit 1; }
```

Colar:
- grep before (confirmando 5-7 matches do débito).
- grep after (zero matches).
- `python -c` de assert das novas keys.
- output `validar-acentuacao.py` after (sem violação).
- smoke + gauntlet rapido.

---

## Validação humana (checklist do usuário)

```bash
cd /home/andrefarias/Desenvolvimento/Nyx-Code

git log --oneline -1
git show --stat HEAD
# esperado: refactor(TAG-KEY-ACCENT-01): ...
# 2 arquivos modificados, ~7 linhas líquidas

grep -rn '"sessao"\|"metricas"' nyx/ --include='*.py'
# esperado: zero matches

python -c "from nyx.agent.output import TAG_STYLES; print(sorted(TAG_STYLES.keys()))"
# esperado: lista com 'sessão' e 'métricas' presentes

./run.sh
# rodar algum /session, conferir que label [sessão] aparece corretamente
```

---

## Riscos

| Risco | Mitigação |
|-------|-----------|
| Call-site externo (gauntlet, plugin, headless) usa chave ASCII | Grep exaustivo antes da edição; se aparecer, expandir touches ou abrir sprint para o caller |
| Algum teste compara output raw `'[sessao]'` em vez de `'[sessão]'` | Rodar gauntlet; se reprovar, atualizar o teste (é cliente da API interna, não fonte de verdade) |
| Mudança reformata o arquivo (pre-commit) | Run: `git diff --stat` antes do commit; se pre-commit alterar, commitar ambos |
| `validar-acentuacao.py` reporta outros falsos-positivos não relacionados | Registrar como achado colateral (não fixar inline); foco exclusivo em 'sessao'/'metricas' |

---

*"O nome é o primeiro lugar onde o respeito se faz ver." -- Rosa Luxemburgo (adaptado)*
