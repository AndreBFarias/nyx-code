## 0. SPEC (machine-readable)

```yaml
sprint:
  id: IDENTITY-GUARD-COPULA-01
  title: "Identidade: _SELF_AI_PATTERN pega auto-ID com copula intercalada (Sou e um assistente)"
  onda: 48
  prioridade: MEDIA
  tipo: Bugfix
  dependencias: [IDENTITY-GUARD-GENERIC-01]
  desbloqueia: []

  touches:
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/agent/lang_check.py
      reason: "_SELF_AI_PATTERN (V12, sprint 394) não casa auto-ID branda com copula intercalada"
      linhas_alvo: "131-139"
  creates: []
  removes: []

  forbidden:
    - "Adicionar emoji"
    - "Usar 'print()' fora de cli.py/output.py"
    - "Inflar falso-positivo: casar 'assistente digital' em discussao ABSTRATA (sem 'sou/como' de auto-referência)"
    - "Tocar _PROVIDER_PATTERN (nomes) ou is_pt_br (idioma) -- so o _SELF_AI_PATTERN"

  tests:
    - cmd: "./run.sh --gauntlet --only rapido"
      timeout: 300
      deve_passar: true

  acceptance_criteria:
    - "'Sou e um assistente digital programado' -> mentions_provider != None (casa)"
    - "'Sou seu assistente virtual' -> casa"
    - "'Sou a Nyx, codificadora' -> não casa (identidade legitima)"
    - "'explique o que e um assistente digital' -> não casa (abstrato, sem auto-referência)"
    - "Gauntlet rapido 100%"
```

---

# Sprint IDENTITY-GUARD-COPULA-01 — Identidade: copula intercalada

**Status:** PENDENTE
**Data criação:** 2026-06-26
**Modelo obrigatório:** claude-opus-4-7 (executor-sprint autorizado pelo dono nesta onda)

---

## Contexto do projeto (snapshot — não referência)

> **ADRs relevantes (inline):**
> - **ADR-005 Anonimato + ADR-027 Identidade Nyx (INVIOLAVEIS):** a Nyx NUNCA se descreve como IA/assistente/modelo. É a Nyx, codificadora silenciosa.
> - ADR-006 PT-BR, ADR-024 Render layer, ADR-014 Testes via Gauntlet.
>
> **Estado (2026-06-26):** `qwen2.5-coder:3b`. A sprint 394 (IDENTITY-GUARD-GENERIC-01, V12) adicionou `_SELF_AI_PATTERN` em `nyx/agent/lang_check.py`. Esta é follow-up (V12 residual). Achado: `dev-journey/07-reports/AUDIT_VALIDACAO_2026_06_26.md` (V12). Guard usado pelo proxy (`proxy.py:746` via `mentions_provider`) para disparar retry anti-vazamento.

---

## Problema

**Achado V12 residual (follow-up da 394):** o `_SELF_AI_PATTERN` (lang_check.py:131-139) tem a alternativa `(sou|como)\s+(um|uma)\s+(assistente|intelig[eê]ncia|modelo)`. Ela exige `sou` IMEDIATAMENTE seguido de `um/uma`. Mas o 3b produziu (runtime) **"Sou é um assistente digital programado"** -- a cópula `é` intercalada entre `Sou` e `um` quebra o match (`Sou` + `é` + `um`, não `Sou` + `um`). A frase passou pelo guard e a auto-identificação como assistente vazou.

---

## Solução proposta

Estender SÓ a alternativa de auto-referência do `_SELF_AI_PATTERN` para:
1. tolerar uma **cópula opcional** (`é`/`e`) entre o verbo e o artigo: `(sou|como)\s+(?:[ée]\s+)?...`;
2. aceitar mais artigos de posse/definidos (`seu`/`sua`/`o`/`a`) além de `um`/`uma`, mantendo a âncora `sou/como` (auto-referência) para NÃO inflar falso-positivo em discussão abstrata.

O resto do pattern (inteligência artificial, IA, modelo de linguagem, treinamentos) fica intacto.

---

## Arquivos alvo (paths absolutos)

### `/home/andrefarias/Desenvolvimento/Nyx-Code/nyx/agent/lang_check.py`

# Localização aproximada: `_SELF_AI_PATTERN` (linha 131-139)
**Antes:**
```python
_SELF_AI_PATTERN = re.compile(
    r"(intelig[eê]ncia\s+artificial|"
    r"(?<![a-zA-Z])IAs?(?![a-zA-Z])|"
    r"modelo\s+de\s+linguagem|"
    r"(sou|como)\s+(um|uma)\s+(assistente|intelig[eê]ncia|modelo)|"
    r"(meus|nos\s+meus)\s+treinamentos|fui\s+treinad[oa]|"
    r"treinad[oa]\s+(para|por|com|em))",
    re.IGNORECASE,
)
```
**Depois:**
```python
# IDENTITY-GUARD-COPULA-01 (V12 residual): a auto-referência tolera uma copula
# intercalada (`Sou e um assistente`, `Sou e um assistente digital programado`) e
# mais artigos (seu/sua/o/a), mantendo a ancora `sou/como` para não casar discussao
# abstrata ("explique o que e um assistente digital" não tem `sou/como` antes).
_SELF_AI_PATTERN = re.compile(
    r"(intelig[eê]ncia\s+artificial|"
    r"(?<![a-zA-Z])IAs?(?![a-zA-Z])|"
    r"modelo\s+de\s+linguagem|"
    r"(sou|como)\s+(?:[ée]\s+)?(um|uma|seu|sua|o|a)\s+(assistente|intelig[eê]ncia|modelo)|"
    r"(meus|nos\s+meus)\s+treinamentos|fui\s+treinad[oa]|"
    r"treinad[oa]\s+(para|por|com|em))",
    re.IGNORECASE,
)
```

**Mudanças:** insere `(?:[ée]\s+)?` (cópula opcional) e amplia o grupo de artigos de `(um|uma)` para `(um|uma|seu|sua|o|a)`. Uma linha alterada.

---

## Diff esperado (resumo)

```
~ 1 arquivo modificado (lang_check.py)
+ ~5 linhas líquidas (comentário + 1 linha de regex alterada)
```

---

## Comandos de verificação (literais, copy-paste)

```bash
# 1. Estatica + acentuacao
python -m ruff check nyx/
python3 ~/.config/zsh/scripts/validar-acentuacao.py --paths nyx/agent/lang_check.py

# 2. Unit sanity (função pura -- PRIMARIA, GPU-free; cole o output)
venv/bin/python -c "
from nyx.agent.lang_check import mentions_provider as m
print('copula:', m('Sou e um assistente digital programado'))       # != None
print('copula2:', m('Sou é um assistente digital programado'))   # != None
print('posse:', m('Sou seu assistente virtual'))                     # != None
print('nyx OK:', m('Sou a Nyx, codificadora silenciosa'))            # None
print('abstrato OK:', m('explique o que e um assistente digital'))   # None
print('provider intacto:', m('eu uso o modelo qwen'))                # != None (nome)
"
# ESPERADO: copula/copula2/posse != None; nyx/abstrato = None; provider intacto != None

# 3. Gauntlet
./run.sh --gauntlet --only rapido

# 4. PROOF RUNTIME (DEFERIDO p/ GPU exclusiva): induzir a Nyx a se auto-descrever
#    e confirmar que o proxy dispara retry e a resposta final não contem "assistente".
#    (rodar quando a GPU estiver livre; a unit sanity acima e a evidencia primaria do guard)
```

---

## Critério binário de aceite (IA executora)

- [ ] Cópula opcional `(?:[ée]\s+)?` + artigos ampliados na alternativa de auto-referência
- [ ] Unit sanity colado: cópula/posse casam; Nyx/abstrato NÃO casam; provider intacto
- [ ] `ruff` limpo, acentuação rc=0, `FAIL_AFTER <= FAIL_BEFORE`
- [ ] Gauntlet `rapido` 100%
- [ ] `SPRINT_ORDER_MASTER.md` marca 407 CONCLUIDA; spec movida para `concluidos/`
- [ ] NÃO commitar; NÃO tocar Checkpoint.md; NÃO tocar `_PROVIDER_PATTERN`/`is_pt_br`

---

## Guardrails anti-engodo (obrigatórios)

NÃO marcar concluída se:
- O teste "abstrato" (`explique o que e um assistente digital`) passou a casar (falso-positivo).
- Tocou `_PROVIDER_PATTERN` ou `is_pt_br` (fora de escopo).
- Unit sanity não colado.

Se algo falhar: `[SPRINT 407] BLOQUEADA: <motivo 1 linha>`.

---

## Proof-of-work obrigatório (4 passos)

```bash
bash scripts/sprint_invariants.sh > /tmp/inv_before.txt 2>&1
FAIL_BEFORE=$(grep -c "^\[FAIL\]" /tmp/inv_before.txt)
# implementar
bash scripts/sprint_invariants.sh > /tmp/inv_after.txt 2>&1
FAIL_AFTER=$(grep -c "^\[FAIL\]" /tmp/inv_after.txt)
diff /tmp/inv_before.txt /tmp/inv_after.txt
```
Colar: inv_before/inv_after (tail), diff, unit sanity, `git --no-pager diff --stat`.

---

## Gambiarras específicas desta sprint

- **Inflar falso-positivo:** a âncora `sou/como` é o que mantém a precisão. NÃO remover. O teste abstrato guarda isso.
- **Cópula gulosa:** `(?:[ée]\s+)?` é opcional e não-guloso por ser exato (`é` ou `e` + espaço). Não casa `e` de conjunção solta.

---

## Validação humana (checklist do usuário)

```bash
cd /home/andrefarias/Desenvolvimento/Nyx-Code
git --no-pager show --stat HEAD
venv/bin/python -c "from nyx.agent.lang_check import mentions_provider as m; print(m('Sou e um assistente digital'))"  # != None
ls dev-journey/06-sprints/concluidos/SPRINT_IDENTITY_GUARD_COPULA_01.md  # existe
```

---

## Riscos

| Risco | Mitigação |
|-------|-----------|
| "como o agente faria" casa (`como` + `o` + ... mas não assistente/IA/modelo) | O grupo final exige `assistente/inteligência/modelo`; "agente" não casa. |
| Cópula `e` solta de conjunção dispara | Exige `(sou|como)` antes + artigo + substantivo-alvo depois; conjunção solta não tem essa estrutura. |
| Discussão legítima sobre IA | A âncora `sou/como` de auto-referência limita; abstrato não casa. |

---

*"Identidade é a segunda porta; vazar o que se é por uma cópula torta quebra contrato." -- princípio de identidade (ADR-027)*
