## 0. SPEC (machine-readable)

```yaml
sprint:
  id: MODEL-SWAP-REAL-OR-HONEST-01
  title: "Satelite: trocar/listar modelos responde HONESTO (não alucina tool/lista fake)"
  onda: 48
  prioridade: MEDIA
  tipo: Feature
  dependencias: []
  desbloqueia: [ONDA-49 gerenciador de models]

  touches:
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/agent/intent.py
      reason: "wants_model_op -- detecta pedido de trocar/listar modelo (alta precisão)"
      linhas_alvo: "fim do arquivo"
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/agent/loop/_core.py
      reason: "run() short-circuita pedido de model-op com resposta honesta (não chama o LLM -> não alucina)"
      linhas_alvo: "run() -- apos os inits, antes de _run_iterations"
  creates: []
  removes: []

  forbidden:
    - "Adicionar emoji"
    - "Usar 'print()' fora de cli.py/output.py"
    - "Nomear o modelo proprietário na resposta (qwen e provider -- ADR-005; _PROVIDER_PATTERN pegaria)"
    - "Falso-positivo: short-circuitar 'qual o modelo de dados' / 'explique o modelo MVC' (exigir verbo trocar/listar + modelo adjacente)"
    - "Implementar troca REAL de modelo (isso e a ONDA-49; aqui so a resposta honesta)"

  tests:
    - cmd: "./run.sh --gauntlet --only rapido"
      timeout: 300
      deve_passar: true

  acceptance_criteria:
    - "'liste os modelos e troque' -> resposta honesta (não suportado/roadmap), SEM tool get_model_list nem lista fake"
    - "'troque de modelo' / 'mude o modelo' / 'liste os modelos' -> short-circuit honesto"
    - "'qual o modelo de dados?' / 'explique o modelo MVC' -> não short-circuita (segue fluxo normal)"
    - "A resposta não nomeia o modelo proprietário (sem 'qwen')"
    - "Gauntlet rapido 100%"
```

---

# Sprint MODEL-SWAP-REAL-OR-HONEST-01 — Satelite: model-op honesto

**Status:** PENDENTE
**Data criação:** 2026-06-26
**Modelo obrigatório:** claude-opus-4-7 (executor-sprint autorizado pelo dono nesta onda)

---

## Contexto do projeto (snapshot — não referência)

> **ADRs relevantes (inline):**
> - **ADR-032 A INFRA CARREGA O MODELO:** se a feature não existe, a infra responde HONESTO -- não deixa o 3b alucinar uma tool e uma lista falsa.
> - **ADR-033 honestidade na falha.** **ADR-005 Anonimato:** não nomear provider (`qwen`).
> - ADR-006 PT-BR, ADR-014 Testes via Gauntlet.
>
> **Estado (2026-06-26):** `qwen2.5-coder:3b`. A troca real de modelo é a ONDA-49 (gerenciador de models, roadmap). Esta sprint entrega só a **resposta honesta** até lá. Achado: `dev-journey/07-reports/AUDIT_VALIDACAO_2026_06_26.md` (V13).

---

## Problema

**Achado V13 MODEL-SWAP-HALLUCINATED [MEDIA]:** "liste os modelos e troque" -> o 3b chama uma tool **inexistente** `get_model_list` e **alucina** "Modelo 1, Modelo 2, Modelo 3". A feature de troca de modelo nunca foi construída (é a ONDA-49). O modelo, sem a ferramenta e sem um caminho honesto, fabrica.

**Causa-raiz:** o loop entrega o pedido ao LLM sem reconhecer que "trocar/listar modelo" é uma capacidade **inexistente**. O 3b então inventa uma tool e uma lista. A infra deveria responder honesto (ADR-032/033) -- a feature não existe ainda.

---

## Solução proposta

Short-circuit determinístico (não chama o LLM -> não há o que alucinar):
1. `nyx/agent/intent.py`: `wants_model_op(user_input)` -> True quando o pedido é claramente trocar/listar **modelo(s)** (verbo trocar/mudar/listar/alternar adjacente a "modelo(s)"). Alta precisão (não casa "modelo de dados"/"modelo MVC").
2. `nyx/agent/loop/_core.py` `run()`: se `wants_model_op(user_input)`, devolver uma `SessionStatus(DONE)` com mensagem HONESTA (não suportado ainda / roadmap), SEM nomear o modelo proprietário, antes de chamar `_run_iterations`.

---

## Arquivos alvo (paths absolutos)

### `/home/andrefarias/Desenvolvimento/Nyx-Code/nyx/agent/intent.py`

# Localização: fim do arquivo (após `wants_read_only`/`wants_mutation` da 398)
**Depois (adicionar):**
```python
# MODEL-SWAP-REAL-OR-HONEST-01 (V13): pedido de trocar/listar modelo (capacidade
# da ONDA-49, ainda inexistente). Alta precisão: verbo trocar/mudar/listar/alternar
# ADJACENTE a "modelo(s)" -- não casa "modelo de dados", "modelo MVC", "qual o
# modelo de negocio" (sem verbo de troca/lista direto em modelo).
_MODEL_OP_PATTERN = re.compile(
    r"\b("
    r"troc(?:ar|a|e|ue)\s+(?:de\s+|o\s+|para\s+(?:outro\s+)?)?modelos?|"
    r"mud(?:ar|e|a)\s+(?:de\s+|o\s+)?modelos?|"
    r"alterm(?:ar|e)\s+(?:de\s+|o\s+)?modelos?|"
    r"altern(?:ar|e)\s+(?:de\s+|o\s+|entre\s+)?modelos?|"
    r"list(?:ar|e|a)\s+(?:os\s+|todos\s+os\s+)?modelos?|"
    r"(?:qual|quais|que)\s+modelos?\s+(?:disponíveis|posso\s+usar|tem\s+disponivel)|"
    r"model\s+swap|switch\s+model"
    r")",
    re.IGNORECASE,
)


def wants_model_op(user_input: str) -> bool:
    """True quando o pedido e trocar/listar MODELO de inferencia (feature da
    ONDA-49, ainda inexistente). Alta precisão: não casa 'modelo de dados'."""
    if not user_input:
        return False
    return bool(_MODEL_OP_PATTERN.search(user_input))
```

> **Nota ao executor:** revise meu regex -- `alterm` foi typo meu (era para cobrir "alterar");
> use `alter(?:ar|e)` se quiser cobrir "alterar o modelo", OU remova essa alternativa. O
> essencial: trocar/mudar/listar/alternar + "modelo(s)" adjacente. Mantenha alta precisão e
> rode o unit sanity (inclui os casos de falso-positivo) antes de marcar.

---

### `/home/andrefarias/Desenvolvimento/Nyx-Code/nyx/agent/loop/_core.py`

#### Edit 1 — import + constante da resposta honesta

# Localização: imports do topo + uma constante de módulo
**Depois (adicionar no import de intent, se houver, senão novo import):**
```python
from nyx.agent.intent import wants_model_op as _wants_model_op
```
**Constante de módulo (junto dos outros regex/constantes do topo de _core.py):**
```python
# MODEL-SWAP-REAL-OR-HONEST-01 (V13): resposta honesta ate a ONDA-49 (gerenciador
# de modelos). não nomeia o modelo proprietário (ADR-005, _PROVIDER_PATTERN).
_MODEL_OP_HONEST = (
    "Trocar de modelo ou listar modelos ainda não é suportado por aqui -- isso "
    "está no roadmap (gerenciador de modelos). Por enquanto sigo com o modelo "
    "local que já está rodando."
)
```

#### Edit 2 — short-circuit em `run()`

# Localização aproximada: dentro de run(), no bloco `try:`, ANTES de `status = await self._run_iterations(user_input)`
**Antes:**
```python
        status: SessionStatus | None = None
        try:
            status = await self._run_iterations(user_input)
```
**Depois:**
```python
        status: SessionStatus | None = None
        try:
            # MODEL-SWAP-REAL-OR-HONEST-01 (V13): trocar/listar modelo e capacidade
            # da ONDA-49 (inexistente). Short-circuit HONESTO -- não chama o LLM,
            # entao não ha tool fantasma (get_model_list) nem lista fabricada. O
            # finally abaixo ainda dispara o Stop hook com este status.
            if _wants_model_op(user_input):
                self._session.add_assistant(_MODEL_OP_HONEST)
                self._gsd_record_turn_state("done")
                status = SessionStatus(
                    state=SessionState.DONE,
                    iterations=1,
                    summary=_MODEL_OP_HONEST,
                )
                return status
            status = await self._run_iterations(user_input)
```

> **Nota ao executor:** confirme via grep que `SessionStatus`/`SessionState.DONE`/`_gsd_record_turn_state`
> existem no escopo de `_core.py` (estão -- já usados). O `return status` dentro do `try` faz o
> `finally` (Stop hook) rodar com o status setado, igual ao caminho normal. NÃO duplicar o
> compose/strip de saída (a resposta honesta já é limpa, sem tool output).

---

## Diff esperado (resumo)

```
~ 2 arquivos modificados (intent.py, loop/_core.py)
+ ~30 linhas líquidas
```

---

## Comandos de verificação (literais, copy-paste)

```bash
# 1. Estatica + acentuacao
python -m ruff check nyx/
python3 ~/.config/zsh/scripts/validar-acentuacao.py --paths nyx/agent/intent.py nyx/agent/loop/_core.py

# 2. Unit sanity (função pura -- inclui falso-positivo; cole o output)
venv/bin/python -c "
from nyx.agent.intent import wants_model_op as w
print('troca:', w('liste os modelos e troque'))            # True
print('troca2:', w('troque de modelo'))                    # True
print('lista:', w('liste os modelos disponíveis'))         # True
print('dados FP:', w('qual o modelo de dados do banco?'))  # False
print('mvc FP:', w('explique o modelo MVC'))               # False
print('negocio FP:', w('descreva o modelo de negocio'))    # False
"
# ESPERADO: troca/troca2/lista True; dados/mvc/negocio False

# 3. Gauntlet
./run.sh --gauntlet --only rapido

# 4. PROOF RUNTIME (DEFERIDO p/ GPU exclusiva):
printf '%s\n' '{"type":"request","content":"liste os modelos disponíveis e troque para o melhor"}' \
  | NYX_AUTO_APPROVE=1 ./run.sh --headless 2>/dev/null
# ESPERADO: summary = resposta honesta (roadmap), iterations=1, ZERO tool_use, SEM "Modelo 1,2,3" fake.
```

---

## Critério binário de aceite (IA executora)

- [ ] `wants_model_op` alta precisão (troca/lista de modelo True; modelo-de-dados/MVC/negócio False)
- [ ] `run()` short-circuita com resposta honesta, sem chamar o LLM, sem nomear provider
- [ ] Unit sanity colado (3 True + 3 False)
- [ ] `ruff` limpo, acentuação rc=0, `FAIL_AFTER <= FAIL_BEFORE`
- [ ] Gauntlet `rapido` 100%
- [ ] `SPRINT_ORDER_MASTER.md` marca 403 CONCLUIDA; spec movida para `concluidos/`
- [ ] NÃO commitar; NÃO tocar Checkpoint.md; NÃO implementar troca real (ONDA-49)

---

## Guardrails anti-engodo (obrigatórios)

NÃO marcar concluída se:
- Falso-positivo: "modelo de dados/MVC/negócio" short-circuitou (o unit sanity guarda).
- Nomeou o modelo proprietário (`qwen`) na resposta.
- Implementou troca real (escopo da ONDA-49).
- Unit sanity não colado.

Se algo falhar: `[SPRINT 403] BLOQUEADA: <motivo 1 linha>`.

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

- **Falso-positivo "modelo":** "modelo" é palavra overloaded (ML/dados/MVC/negócio). A precisão vem de exigir verbo trocar/listar ADJACENTE a "modelo(s)". O unit sanity é load-bearing.
- **Nomear provider:** a resposta honesta NÃO cita `qwen` (ADR-005). Genérica.
- **Short-circuit que pula o Stop hook:** o `return` é DENTRO do `try`, então o `finally` (Stop) roda. Não mover para fora.

---

## Validação humana (checklist do usuário)

```bash
cd /home/andrefarias/Desenvolvimento/Nyx-Code
git --no-pager show --stat HEAD
venv/bin/python -c "from nyx.agent.intent import wants_model_op as w; print(w('troque de modelo'), w('qual o modelo de dados'))"  # True False
ls dev-journey/06-sprints/concluidos/SPRINT_MODEL_SWAP_REAL_OR_HONEST_01.md  # existe
```

---

## Riscos

| Risco | Mitigação |
|-------|-----------|
| Falso-positivo em "modelo" não-IA | Regex exige verbo troca/lista adjacente; unit sanity cobre dados/MVC/negócio. |
| Pedido misto ("troque de modelo e liste arquivos") short-circuita o todo | Aceitável: a parte de troca é honesta; o usuário re-pede a listagem. Raro. |
| Resposta honesta soa seca | Texto cita o roadmap (gerenciador de modelos), dá contexto. Ajustável. |

---

*"Não saber fazer é honesto; fingir que faz é o erro." -- princípio de execução (dev-journey/02-architecture/DESENHO_CONTRATO_EXECUCAO.md)*
