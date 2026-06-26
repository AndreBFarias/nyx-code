## 0. SPEC (machine-readable)

```yaml
sprint:
  id: TOOL-GATING-NO-SUPPRESS-01
  title: "Parar de suprimir tools no intent 'chat' (a infra amarra as maos do modelo)"
  onda: 48
  prioridade: ALTA
  tipo: Bugfix
  dependencias: []
  desbloqueia: [EXEC-CONTRACT-NO-HALLUCINATED-RESULT-01]

  touches:
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/agent/loop/_iteration.py
      reason: "_select_tools_for_context retorna [] para intent 'chat' -> o modelo nunca recebe a tool"
      linhas_alvo: "840-844"
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/proxy.py
      reason: "Gating redundante no proxy suprime tools para intent 'chat' (defesa em profundidade)"
      linhas_alvo: "273-277"
  creates: []
  removes: []

  n_to_n_pairs:
    - descrição: "A tupla de intents que zera tools existe em DOIS pontos (loop e proxy) -- atualizar AMBOS"
      paths: [nyx/agent/loop/_iteration.py, nyx/proxy.py]

  forbidden:
    - "Adicionar emoji"
    - "Usar 'print()' fora de cli.py/output.py"
    - "Mencao a IA proprietaria"
    - "Mexer no cap de 5 tools (escopo de outra sprint -- D3 cap-esconde-tool)"
    - "Tentar 'consertar o classifier' adicionando verbos no regex (a licao da onda e que regex nao cobre)"

  tests:
    - cmd: "./run.sh --gauntlet --only rapido"
      timeout: 300
      deve_passar: true

  acceptance_criteria:
    - "intent 'chat' NAO zera mais as tools no loop nem no proxy"
    - "'saudacao' e 'comando' continuam zerando tools (sem regressao de latencia em saudacao)"
    - "Proof runtime: 'da um fastfetch' dispara run_command e traz specs REAIS (Ryzen/RTX 3050/Pop!_OS), nao inventadas"
    - "Acentuacao PT-BR correta em tudo novo"
    - "Gauntlet --only rapido passa 100%"
```

---

# Sprint TOOL-GATING-NO-SUPPRESS-01 — Parar de suprimir tools no intent 'chat'

**Status:** PENDENTE
**Data criação:** 2026-06-26
**Modelo obrigatório:** claude-opus-4-7 (executor-sprint autorizado pelo dono nesta onda)

---

## Contexto do projeto (snapshot — não referência)

> **ADRs relevantes (inline):**
> - ADR-032 A INFRA CARREGA O MODELO: a solucao nunca e trocar de modelo; e a infra guiar o modelo fraco a agir certo. Suprimir as tools faz o OPOSTO.
> - ADR-033 A CADEIA NUNCA QUEBRA: alucinacao que chega ao usuario = cadeia com buraco.
> - ADR-009 Acesso Universal / ADR-001 Local First / ADR-006 PT-BR / ADR-005 Anonimato.
> - ADR-014 Testes via Gauntlet, ADR-010 Zero Mocks.
>
> **Estado (2026-06-26):** Python 3.10+, `qwen2.5-coder:3b` no Ollama :11435, proxy :11436. 35 tools, 16 services. Onda ONDA-48 (validacao as-user). Relatorio: `dev-journey/07-reports/AUDIT_VALIDACAO_2026_06_26.md` (achado V01).

---

## Problema

**Achado V01 da ONDA-48 (provado runtime, headless E TUI real).** O proxy E o loop suprimem as ferramentas quando o classifier rule-based (`nyx/agent/intent.py`) devolve `chat`. Como o regex de verbos nunca cobre todo o PT-BR, qualquer pedido de acao fora do dicionario cai em `chat` e o modelo **nunca recebe a ferramenta** -> so lhe resta alucinar.

**Sintoma literal (TUI real, 2026-06-26):** prompt "da um fastfetch e me fala as specs do pc atual" -> a Nyx respondeu *"Comando executado com sucesso: Processador Intel i7-10850K / RTX 3080 / 24GB"* (a maquina real e AMD Ryzen 5 7535HS / RTX 3050 / 14GB / Pop!_OS). **Zero `tool_use`, `files_modified=0`** -- `run_command` foi apagado do payload antes de chegar ao modelo.

Causa-raiz (verificada no codigo):
1. `nyx/agent/loop/_iteration.py:842` -- `_select_tools_for_context` retorna `[]` para `intent in ("saudacao","chat","comando")`; com tools=[] o `_call_llm` ainda usa o **system prompt compact** (sem schema de tools).
2. `nyx/proxy.py:275` -- suprime de novo (defesa em profundidade).

---

## Solução proposta

Remover `"chat"` da tupla de supressao nos **dois** pontos. `chat` passa a selecionar `CORE_TOOLS` (que inclui `run_command`, `read_file`, `write_file`, `edit_file`, ... no top-5 do registry, confirmado) + ativadas por keyword. `saudacao` e `comando` continuam zerando tools (saudacao genuina nao precisa; slash sai antes do LLM).

NAO mexer no cap de 5 (run_command e o 4o CORE na ordem do registry -> sobrevive). NAO adicionar verbos ao regex (paliativo que a onda provou nao escalar).

---

## Arquivos alvo (paths absolutos)

### `/home/andrefarias/Desenvolvimento/Nyx-Code/nyx/agent/loop/_iteration.py`

# Localização aproximada: linha 840-844 (drift tolerado se trecho casa)
**Antes:**
```python
        intent = _classify_intent(last_user)

        if intent in ("saudacao", "chat", "comando"):
            logger.info("[loop] intent=%s -> tools=[]", intent)
            return []
```

**Depois:**
```python
        intent = _classify_intent(last_user)

        # TOOL-GATING-NO-SUPPRESS-01 (V01): 'chat' NAO zera mais as tools. O regex
        # de intent nunca cobre todo o PT-BR ("da um fastfetch" caia em chat e o
        # modelo perdia run_command -> alucinava). Suprimir tools fere ADR-032 (a
        # infra deve guiar o modelo a agir, nao amarra-lo). Saudacao/comando seguem
        # sem tools (saudacao genuina nao precisa; slash sai antes do LLM).
        if intent in ("saudacao", "comando"):
            logger.info("[loop] intent=%s -> tools=[]", intent)
            return []
```

**Mudanças:** remove `"chat"` da tupla; comentario explica o porque (anti-regressao futura).

---

### `/home/andrefarias/Desenvolvimento/Nyx-Code/nyx/proxy.py`

# Localização aproximada: linha 273-277 (drift tolerado se trecho casa)
**Antes:**
```python
    has_tools = bool(body.get("tools"))
    # Suprime tools quando intent não precisa.
    if intent in ("saudacao", "chat", "comando") and has_tools:
        logger.info("intent=%s -> tools suprimidos (%d)", intent, len(body["tools"]))
        has_tools = False
```

**Depois:**
```python
    has_tools = bool(body.get("tools"))
    # TOOL-GATING-NO-SUPPRESS-01 (V01): 'chat' fora da supressao (par do loop em
    # _iteration.py). Suprimir tools no chat amarrava o modelo (ADR-032).
    if intent in ("saudacao", "comando") and has_tools:
        logger.info("intent=%s -> tools suprimidos (%d)", intent, len(body["tools"]))
        has_tools = False
```

**Mudanças:** remove `"chat"` da tupla (par N-para-N do loop).

---

## Diff esperado (resumo)

```
~ 2 arquivos modificados (nyx/agent/loop/_iteration.py, nyx/proxy.py)
+ ~8 linhas líquidas (comentários explicativos + remoção de "chat")
```

---

## Comandos de verificação (literais, copy-paste)

```bash
# 1. Validação estática
python -m ruff check nyx/

# 2. Invariantes
bash scripts/sprint_invariants.sh

# 3. Acentuação PT-BR
python3 ~/.config/zsh/scripts/validar-acentuacao.py --paths nyx/agent/loop/_iteration.py nyx/proxy.py

# 4. PROOF RUNTIME-REAL (o coração desta sprint): a Nyx agora AGE no fastfetch.
#    Roda a Nyx de verdade via headless e confirma run_command + specs reais.
printf '%s\n' '{"type":"request","content":"da um fastfetch e me fala as specs do pc atual"}' \
  | NYX_AUTO_APPROVE=1 ./run.sh --headless 2>/dev/null
# ESPERADO: uma linha {"type":"tool_use","tool":"run_command","args":{"command":"fastfetch..."}}
#           e o summary com specs REAIS (Ryzen 5 7535HS / RTX 3050 / Pop!_OS), files_modified/read coerente.
# REPROVADO se: nenhum tool_use, ou specs inventadas (Intel/RTX 3080/Windows).
```

---

## Critério binário de aceite (IA executora)

- [ ] `"chat"` removido da tupla em `_iteration.py` E `proxy.py` (os dois)
- [ ] `saudacao`/`comando` continuam zerando tools (grep confirma a tupla `("saudacao", "comando")`)
- [ ] Proof runtime: "da um fastfetch" emite `tool_use run_command` e specs reais (colar o JSON literal)
- [ ] `ruff` limpo, acentuacao rc=0, invariantes `FAIL_AFTER <= FAIL_BEFORE`
- [ ] Gauntlet `--only rapido` 100%
- [ ] `SPRINT_ORDER_MASTER.md` marca 393 CONCLUIDA; spec movida para `concluidos/`
- [ ] Commit atômico `fix(loop): 393 TOOL-GATING-NO-SUPPRESS-01 -- chat recebe tools (V01)`

---

## Guardrails anti-engodo (obrigatórios)

NÃO marcar concluída se:
- O proof runtime do fastfetch não foi colado (output real do headless).
- "Consertou" adicionando "fastfetch" ao regex de `intent.py` em vez de tirar `chat` do gating (burla o escopo).
- Removeu `saudacao`/`comando` junto (regressao de latencia em saudacao).
- Gauntlet "passou" sem output real.

Se algo falhar: `[SPRINT 393] BLOQUEADA: <motivo 1 linha>`.

---

## Proof-of-work obrigatório (4 passos)

```bash
bash scripts/sprint_invariants.sh > /tmp/inv_before.txt 2>&1
FAIL_BEFORE=$(grep -c "^\[FAIL\]" /tmp/inv_before.txt)
# implementar
bash scripts/sprint_invariants.sh > /tmp/inv_after.txt 2>&1
FAIL_AFTER=$(grep -c "^\[FAIL\]" /tmp/inv_after.txt)
# regra binária: FAIL_AFTER <= FAIL_BEFORE
diff /tmp/inv_before.txt /tmp/inv_after.txt
```
Colar: inv_before/inv_after (tail), diff, o JSON do proof runtime do fastfetch, e `git show --stat HEAD`.

---

## Riscos

| Risco | Mitigação |
|-------|-----------|
| Chat genuíno ("explique recursividade") agora recebe tools e o modelo chama tool desnecessária | Trade-off aceito (ADR-009: qualidade > latência); a sprint 399 (no-hallucinated-result) cobre o inverso. Latência de chat sobe pouco (schema de tools no input). |
| Cap de 5 corta `list_files`/`search`/`done` (7º/8º CORE) | Fora de escopo (achado D3 cap-esconde-tool, sprint própria). `run_command` é 4º -> seguro para o proof. |
| Saudação fica mais lenta se `chat` vazasse para ela | Não vaza: `saudacao` tem regex próprio e continua na tupla de supressão. |

---

*"A infra que esconde a ferramenta do operário não o protege -- o aleija." -- princípio de agência*
