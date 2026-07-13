## 0. SPEC (machine-readable)

```yaml
sprint:
  id: PROXY-INTENT-ON-USER-REQUEST-01
  numero: 421
  title: "Classificar intent pelo PEDIDO REAL do usuário, não pelo resultado da tool (budget/guardrails/memoria corretos em iteracoes 2+)"
  onda: 48
  prioridade: ALTA
  tipo: Bugfix
  dependencias: []
  desbloqueia: []
  absorve: []
  relacionada: [352, 411]

  touches:
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/proxy.py
      reason: "_last_user_text passa a pular mensagens sinteticas (resultado de tool + resumo reinjetado); openai_to_ollama honra body['nyx_intent'] autoritativo com fallback para a heuristica atual"
      linhas_alvo: "238-246 (_last_user_text), 269-296 (openai_to_ollama intent + budget), 782-784 (gating MEMORY-INTENT-ENFORCE)"
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/agent/loop/_iteration.py
      reason: "propagar o intent do turno REAL como payload['nyx_intent']; espelhar o skip de sinteticas no scan inline de _select_tools_for_context"
      linhas_alvo: "227-237 (_init_done_guard: guardar self._turn_intent), 900-904 (payload build: injetar nyx_intent), 1036-1042 (scan de last_user em _select_tools_for_context)"
  creates: []
  removes: []

  forbidden:
    - "Adicionar emoji"
    - "Usar 'print()' fora de cli.py/output.py"
    - "Mencao a IA proprietaria"
    - "Tocar a cascata OOM do proxy (_post_chat_with_oom_recovery), o retry de guardrails (_retry_with_hint) ou o gating LANG/IDENTITY em si"
    - "Tocar os guards do contrato de execução (397/398/399/400/401)"
    - "Mudar o formato do ollama_body enviado ao Ollama: 'nyx_intent' NUNCA pode vazar para o body nativo do Ollama"
    - "Alterar o happy-path: quando body não traz 'nyx_intent', o intent classificado deve ser byte-identico ao atual para o MESMO conjunto de mensagens reais"
    - "Mudar os valores de NUM_PREDICT_BY_INTENT em nyx/config/defaults.py"

  tests:
    - cmd: "/home/andrefarias/.local/bin/ruff check nyx/proxy.py nyx/agent/loop/_iteration.py"
      deve_passar: true
    - cmd: "python3 ~/.config/zsh/scripts/validar-acentuacao.py --paths nyx/proxy.py nyx/agent/loop/_iteration.py"
      deve_passar: true
    - cmd: "bash scripts/sprint_invariants.sh"
      deve_passar: true
    - cmd: "./run.sh --gauntlet --only proxy"
      timeout: 300
      deve_passar: true
      nota: "DEFERIDO para GPU exclusiva (exige Ollama vivo). Ver Proof-of-work."

  acceptance_criteria:
    - "AC1 (budget / regressao #352): em iteracao 2+ de um fluxo 'leia X e reescreva com docstrings', o intent de orcamento não cai por causa do texto do arquivo lido -- write_file de codigo mantem num_predict=4096 (code), nunca 512 (chat) nem 2048 (tool). Fechado pelo nyx_intent autoritativo do loop, com fallback no _last_user_text endurecido."
    - "AC2 (guardrails LANG/IDENTITY): o gating dos guardrails de saida passa a usar o intent do PEDIDO real, não o texto do tool_result. Um arquivo lido em ingles não dispara retry de idioma (LANG) sobre a resposta final de um turno 'tool-needed'."
    - "AC3 (memoria espontanea / raiz do 411): _wants_save_memory passa a checar o TEXTO do pedido real do usuário, não o conteudo do tool_result. Um arquivo lido que contenha 'lembre-se que' não forca retry exigindo write_memory num fluxo de leitura pura."
    - "AC4 (loop tool-selection): o scan inline de last_user em _select_tools_for_context pula mensagens sinteticas; a seleção de tools e o must-keep de write_memory usam o pedido real, não o tool_result."
    - "AC5 (aditivo e seguro): body sem 'nyx_intent' -> comportamento byte-identico ao atual para o mesmo conjunto de mensagens reais; 'nyx_intent' JAMAIS vaza para o ollama_body (o Ollama nunca recebe o campo)."
    - "AC6: ruff limpo, acentuacao rc=0, invariantes FAIL_AFTER <= FAIL_BEFORE; smoke boot e gauntlet --only proxy DEFERIDOS para GPU exclusiva."
```

---

# Sprint PROXY-INTENT-ON-USER-REQUEST-01 — Intent pelo pedido do usuário, não pelo resultado da tool

**Status:** PENDENTE
**Data criação:** 2026-07-12
**Modelo obrigatório:** claude-opus-4-7 (executor-sprint autorizado pelo dono nesta onda)

---

## Contexto do projeto (snapshot — não referência)

> **Missão (calibração):** o Nyx-Code faz o pior LLM local (qwen 3b) na pior máquina possível parecer o Claude Code offline. Robustez pertence à INFRA, não ao modelo (ADR-032/033/034). O usuário-alvo é leigo, sem hardware bom: qualquer degradação silenciosa de orçamento ou disparo espúrio de retry custa segundos de CPU e confiança que ele não tem para gastar. <!-- noqa-anonimato -->
>
> **ADRs relevantes (inline):**
> - **ADR-032/033 A INFRA CARREGA O MODELO / ENFORCEMENT, NÃO CONFIANÇA:** o gating de orçamento e de guardrails é decisão da infra; deve refletir a INTENÇÃO do turno, não um artefato do transporte (o histórico convertido).
> - ADR-034 (capacidade do modelo é limite, mitigável por infra), ADR-026 (Agência).
>
> **Estado (2026-07-12):** `qwen2.5-coder:3b`. ONDA-48 fase raiz: núcleo do contrato (399/397/400/398/401) CONCLUIDO e commitado. Esta e satélite de correção do classificador de intent no proxy e no loop (achado da auditoria de prontidão 2026-07-12). Ports: Ollama `11435`, proxy `11436` (`nyx/config/defaults.py`).

---

## Problema

**Achado (auditoria de prontidão 2026-07-12, ALTA, verificado adversarialmente):** a partir da segunda iteração de qualquer turno, o intent que governa **orçamento de saída, guardrails de idioma/identidade e enforcement de memória** e classificado sobre o **resultado da última tool**, não sobre o **pedido real do usuário**.

**Causa-raiz (verificada no código):**

1. `nyx/agent/session.py:79-81` — todo entry de histórico com `role == "tool"` vira uma mensagem `role="user"` sintética:
   ```python
   if entry.role == "tool":
       msgs.append({"role": "user", "content": f"[resultado de {entry.tool_name}]\n{entry.tool_result}"})
   ```
2. `nyx/proxy.py:238-246` — `_last_user_text` retorna o conteúdo do **último** `role=user`. Em iterações 2+, esse último user e a mensagem sintética `[resultado de <tool>]` (ou o resumo reinjetado `[resumo da conversa anterior]`, prefixo `SUMMARY_REINJECT_PREFIX` de `nyx/agent/context.py:58`, injetado em `_iteration.py:884-888`).
3. `nyx/proxy.py:270-271` — `intent = _classify_intent(_last_user_text(messages))`; `proxy.py:293-296` deriva o orçamento a partir desse intent; `proxy.py:717-782` gateia LANG/IDENTITY/MEMORY pelo mesmo intent; `proxy.py:782-784` re-deriva `last_user = _last_user_text(...)` e chama `_wants_save_memory(last_user)`.
4. O mesmo padrão vive no loop: `nyx/agent/loop/_iteration.py:1036-1042` — `_select_tools_for_context` escaneia o "último user" das mensagens e classifica intent sobre ele; `_iteration.py:1088-1090` usa esse mesmo `last_user` para o must-keep de `write_memory`.

**Três sintomas do mesmo mecanismo (verificados):**

- **(i) Orçamento — regressão exata do #352 (PROXY-INTENT-CODE-BUDGET-01).** No fluxo `"leia utils.py e reescreva com docstrings"`, a iteração do `write_file` tem como último user o conteúdo do arquivo lido, que raramente classifica como `code`. O orçamento cai de `code`=4096 para `tool`=2048 — e, se a janela de 4 já não contém o turno real (só tool_results + resumo), `_last_user_text` retorna `''` e classifica `chat`=512 (`nyx/config/defaults.py:107-115`). O JSON do `write_file` trunca — exatamente o que o #352 corrigiu, agora reaparecendo em qualquer fluxo com leitura prévia.
- **(ii) Guardrails.** LANG/IDENTITY (`proxy.py:725,749`) passam a ser gateados pelo texto do tool_result: um arquivo em inglês pode disparar retry de idioma sobre a resposta final (+segundos em CPU).
- **(iii) Memória espontânea — raiz provável do achado 411.** Se o arquivo lido contém `'lembre-se que'` (comum nos próprios docs deste projeto), `_wants_save_memory(tool_result)` retorna `True` e força retry exigindo `write_memory` num fluxo de **leitura pura**. A sprint 411 cobre o sintoma no contrato do loop; esta cobre a causa no gating do proxy.

---

## Causa-raiz — reconciliação com o briefing (linhas deslizaram)

O briefing citava `proxy.py:271` para a classificação e `238-246` para `_last_user_text`. Verificado no código real: `_last_user_text` está em `proxy.py:238-246` (idêntico); a classificação está em **`proxy.py:270-271`** (deslizou 1 linha); o gating de orçamento em **`293-296`**; o gating MEMORY em **`782-784`**. O scan do loop está em **`_iteration.py:1036-1042`** (confere). Nenhuma divergência de mecanismo — apenas deslize de numeração de 1 linha na classificação. Confirmado ainda, além do briefing: (a) o loop **já classifica o intent do turno real** em `_init_done_guard` (`_iteration.py:232`), o que torna a propagação de `nyx_intent` barata; (b) o orçamento `chat` e **512**, não 2048 — o pior caso de degradação e mais severo do que o briefing sugeria.

---

## Solução proposta

Um único mecanismo (intent-sobre-sintética), duas correções complementares e aditivas — cada uma carrega um subconjunto dos sintomas:

- **Fix A — `nyx_intent` autoritativo (fecha (i) de forma robusta, reforça (ii)).** O loop já conhece o intent do turno REAL (`_init_done_guard`). Ele o propaga como campo aditivo `payload["nyx_intent"]`. O proxy, quando recebe um `nyx_intent` válido, o usa como fonte de verdade do intent (orçamento + guardrails), **sobrevivendo à janela deslizante** — mesmo quando o turno real já saiu do `history_msgs[-4:]`. Sem o campo, cai na heurística atual (compatibilidade com o probe de GPU e clientes externos).
- **Fix B — `_last_user_text` endurecido + espelho no loop (fecha (iii), sustenta o fallback de (i)/(ii)).** `_last_user_text` passa a **pular mensagens sintéticas** (`[resultado de ` e `SUMMARY_REINJECT_PREFIX`), devolvendo o texto do último pedido REAL. Isso conserta a fonte de `_wants_save_memory(last_user)` no proxy (sintoma iii, que depende do TEXTO, não só do intent) e serve de fallback correto para a classificação. O mesmo skip e espelhado no scan inline de `_select_tools_for_context` no loop.

Ambos são necessários: `nyx_intent` sozinho não conserta (iii) — o enforcement de memória lê o TEXTO do pedido, não o intent; `_last_user_text` endurecido sozinho não conserta (i) na janela profunda — quando o turno real saiu da janela, o texto real não está mais presente e só o `nyx_intent` o carrega.

---

## Arquivos alvo (paths absolutos)

### `/home/andrefarias/Desenvolvimento/Nyx-Code/nyx/proxy.py`

#### Edit 1 — `_last_user_text` pula mensagens sintéticas

# Localização: função `_last_user_text` (linhas 238-246). Adicionar constantes de módulo logo acima.
**Antes:**
```python
def _last_user_text(messages: list) -> str:
    """Retorna o conteúdo do último turno role=user. '' se não houver."""
    for msg in reversed(messages):
        if msg.get("role") == "user":
            content = msg.get("content", "")
            if isinstance(content, str):
                return content
            return _normalize_content(content)
    return ""
```
**Depois:**
```python
# PROXY-INTENT-ON-USER-REQUEST-01: prefixos de mensagens role=user SINTETICAS
# (não sao pedido do usuário). Espelham as fontes canonicas:
#   - "[resultado de "  -> nyx/agent/session.py:80 (to_messages, entry.role=="tool")
#   - SUMMARY_REINJECT_PREFIX -> nyx/agent/context.py:58 (resumo reinjetado)
# Sao literais espelhados de proposito (evitam import de session/context no proxy);
# se as fontes mudarem, este skip deve acompanhar (ver invariante da spec).
_SYNTHETIC_USER_PREFIXES = ("[resultado de ", "[resumo da conversa anterior]")


def _is_synthetic_user(content: str) -> bool:
    return isinstance(content, str) and content.startswith(_SYNTHETIC_USER_PREFIXES)


def _last_user_text(messages: list) -> str:
    """Retorna o conteúdo do último turno role=user REAL. '' se não houver.

    PROXY-INTENT-ON-USER-REQUEST-01: ignora mensagens role=user sintéticas
    (resultado de tool, resumo reinjetado) -- em iterações 2+ elas mascaravam o
    pedido real e faziam o intent (orçamento/guardrails/memória) ser classificado
    sobre o resultado da ferramenta, não sobre o que o usuário pediu.
    """
    for msg in reversed(messages):
        if msg.get("role") == "user":
            content = msg.get("content", "")
            if not isinstance(content, str):
                content = _normalize_content(content)
            if _is_synthetic_user(content):
                continue
            return content
    return ""
```

#### Edit 2 — `openai_to_ollama` honra `nyx_intent` autoritativo (fallback = heurística)

# Localização: dentro de `openai_to_ollama`, no ponto da classificação (linhas 270-271).
**Antes:**
```python
    messages = _normalize_messages(body.get("messages", []))
    last_user = _last_user_text(messages)
    intent = _classify_intent(last_user)
```
**Depois:**
```python
    messages = _normalize_messages(body.get("messages", []))
    last_user = _last_user_text(messages)
    # PROXY-INTENT-ON-USER-REQUEST-01: o loop conhece o intent do turno REAL
    # (nyx/agent/loop/_iteration.py:_init_done_guard) e o propaga em
    # body['nyx_intent']. Quando presente e valido, e a fonte de verdade do
    # intent -- sobrevive a janela deslizante (o turno real pode ja ter saido
    # de history_msgs[-4:]). Sem o campo, cai na heuristica sobre o último user
    # REAL (compatibilidade: probe de GPU e clientes externos não enviam o campo).
    nyx_intent = body.get("nyx_intent")
    if nyx_intent in _VALID_INTENTS:
        intent = nyx_intent
    else:
        intent = _classify_intent(last_user)
```

# E, junto às demais constantes de módulo do topo, definir o conjunto de validação:
```python
# PROXY-INTENT-ON-USER-REQUEST-01: intents canônicos que classify() emite
# (nyx/agent/intent.py:classify). Qualquer nyx_intent fora deste conjunto e
# ignorado (fallback para a heurística).
_VALID_INTENTS = frozenset({"saudacao", "comando", "tool-needed", "code", "chat"})
```

> Nota de não-vazamento (verificado): `openai_to_ollama` monta o `ollama_body` **explicitamente** (`result = {"model":..., "messages":..., "options":...}` mais `result["tools"]` condicional). `nyx_intent` fica só no `body` OpenAI e **nunca** entra no `ollama_body` — o Ollama jamais recebe o campo. `handle_chat` (linha 838) usa `body` apenas para ler `tools`/`temperature`/`nyx_intent`, nunca o repassa cru. <!-- noqa-anonimato -->

### `/home/andrefarias/Desenvolvimento/Nyx-Code/nyx/agent/loop/_iteration.py`

#### Edit 3 — guardar o intent do turno REAL em `_init_done_guard`

# Localização: `_init_done_guard` (linha 227-237), onde o intent já e classificado (linha 232).
**Antes:**
```python
        self._turn_writes_baseline = self._session.files_modified_count
        intent = _classify_intent(user_input)
        self._turn_wants_create = intent == "code"
```
**Depois:**
```python
        self._turn_writes_baseline = self._session.files_modified_count
        intent = _classify_intent(user_input)
        # PROXY-INTENT-ON-USER-REQUEST-01: guarda o intent do turno REAL para
        # propaga-lo ao proxy (payload['nyx_intent']) em TODAS as iteracoes --
        # o proxy não ve mais o pedido original a partir da iteracao 2+ (o
        # histórico converte tool results em role=user sinteticos).
        self._turn_intent = intent
        self._turn_wants_create = intent == "code"
```

#### Edit 4 — injetar `nyx_intent` no payload do `_call_llm`

# Localização: build do `payload` no `_call_llm` (linhas 900-904).
**Antes:**
```python
        payload: dict[str, Any] = {
            "model": self._model,
            "messages": messages,
            "tools": selected_tools,
        }
```
**Depois:**
```python
        payload: dict[str, Any] = {
            "model": self._model,
            "messages": messages,
            "tools": selected_tools,
        }
        # PROXY-INTENT-ON-USER-REQUEST-01: propaga o intent do turno REAL. O proxy
        # (openai_to_ollama) o usa como fonte de verdade do orcamento/guardrails,
        # em vez de reclassificar sobre o último role=user (que em iteracoes 2+ e
        # o resultado sintetico da tool). getattr defensivo: se _init_done_guard
        # não rodou (não deveria), o proxy cai na heuristica.
        turn_intent = getattr(self, "_turn_intent", None)
        if turn_intent:
            payload["nyx_intent"] = turn_intent
```

#### Edit 5 — espelhar o skip de sintéticas no scan de `_select_tools_for_context`

# Localização: scan inline de `last_user` em `_select_tools_for_context` (linhas 1036-1042).
**Antes:**
```python
        last_user = ""
        for msg in reversed(messages):
            if msg.get("role") == "user":
                content = msg.get("content", "")
                if isinstance(content, str):
                    last_user = content
                break
        intent = _classify_intent(last_user)
```
**Depois:**
```python
        # PROXY-INTENT-ON-USER-REQUEST-01: pula mensagens role=user sintéticas
        # (resultado de tool / resumo reinjetado) -- em iterações 2+ elas
        # mascaravam o pedido real na seleção de tools e no must-keep de
        # write_memory abaixo. Prefere o intent do turno real quando disponível.
        last_user = ""
        for msg in reversed(messages):
            if msg.get("role") != "user":
                continue
            content = msg.get("content", "")
            if not isinstance(content, str):
                continue
            if content.startswith(("[resultado de ", "[resumo da conversa anterior]")):
                continue
            last_user = content
            break
        intent = getattr(self, "_turn_intent", None) or _classify_intent(last_user)
```

---

## Diff esperado (resumo)

```
~ 2 arquivos modificados (nyx/proxy.py, nyx/agent/loop/_iteration.py)
+ ~35 linhas líquidas (fix aditivo; nenhum arquivo cruza meta de tamanho)
```

Sem aritmética de extração: esta sprint não tem meta `arquivo < NNNL`. O único número relevante e o net-add (~35L) distribuído em 2 arquivos, todo aditivo (nenhuma remoção de lógica).

---

## Invariantes a preservar

- **Happy-path byte-idêntico sem `nyx_intent`:** para o MESMO conjunto de mensagens reais (sem sintéticas), a classificação de intent e o orçamento não mudam quando `body` não traz `nyx_intent`. O único comportamento novo aparece quando (a) há sintéticas mascarando o último user, ou (b) `nyx_intent` válido está presente.
- **`nyx_intent` não vaza para o Ollama:** verificado — `ollama_body` e montado explicitamente; o campo fica só no `body` OpenAI. <!-- noqa-anonimato -->
- **Espelho de literais rastreável:** `_SYNTHETIC_USER_PREFIXES` espelha `nyx/agent/session.py:80` e `nyx/agent/context.py:58`. Se essas fontes mudarem o prefixo, este skip deve acompanhar (registrado aqui como acoplamento consciente — evita import de `session`/`context` no `proxy`).
- **Fonte única do classificador:** `classify()` (`nyx/agent/intent.py`) segue sendo a única fonte de intent; `_VALID_INTENTS` apenas espelha o conjunto de saída dele.
- **Não tocar** a cascata OOM (`_post_chat_with_oom_recovery`), `_retry_with_hint`, os guards do contrato (397-401), nem `NUM_PREDICT_BY_INTENT` (`defaults.py`).

---

## Comandos de verificação (literais, copy-paste)

```bash
cd /home/andrefarias/Desenvolvimento/Nyx-Code

# 1. Estatica + acentuacao (ruff via binario direto -- não ha modulo ruff no venv, ver BRIEF)
/home/andrefarias/.local/bin/ruff check nyx/proxy.py nyx/agent/loop/_iteration.py
python3 ~/.config/zsh/scripts/validar-acentuacao.py --paths nyx/proxy.py nyx/agent/loop/_iteration.py

# 2. Confirmar as ancoras (linhas podem ter deslizado -- reconferir antes de editar):
rg -n "_last_user_text|nyx_intent|_turn_intent|resultado de |SUMMARY_REINJECT_PREFIX|_classify_intent" nyx/proxy.py nyx/agent/loop/_iteration.py

# 3. PROOF RUNTIME-REAL SEM GPU (funções puras do proxy; nenhum Ollama envolvido).
#    Prova os tres sintomas de uma vez com mensagens sinteticas reais.
./venv/bin/python - <<'PY'
from nyx.proxy import _last_user_text, openai_to_ollama, _wants_save_memory

# Cenario iteracao 2+: último role=user e o resultado sintetico da tool,
# cujo conteudo esta em ingles e contem "lembre-se que".
msgs = [
    {"role": "user", "content": "leia utils.py e reescreva com docstrings"},
    {"role": "assistant", "content": ""},
    {"role": "user", "content": "[resultado de read_file]\n# lembre-se que this file is in English\ndef foo(): pass"},
]

# (Fix B) _last_user_text volta ao pedido REAL, não ao tool_result:
lu = _last_user_text(msgs)
print("last_user REAL:", repr(lu))
assert lu == "leia utils.py e reescreva com docstrings", lu
assert "lembre-se que" not in lu, lu          # sintoma (iii): memoria não dispara
assert "English" not in lu, lu                # sintoma (ii): LANG não dispara

# (Fix A) nyx_intent autoritativo mantem o orcamento de code=4096 mesmo com
# tools e com o último user sintetico:
body = {
    "model": "qwen2.5-coder:3b",
    "messages": msgs,
    "tools": [{"function": {"name": "write_file"}}],
    "nyx_intent": "code",
}
ob, intent = openai_to_ollama(body, num_gpu=0)
print("intent:", intent, "num_predict:", ob["options"]["num_predict"])
assert intent == "code", intent
assert ob["options"]["num_predict"] == 4096, ob["options"]["num_predict"]
assert "nyx_intent" not in ob, "nyx_intent VAZOU para o ollama_body"   # AC5

# (Compat) sem nyx_intent, com último user REAL, comportamento inalterado:
body2 = {"model": "m", "messages": [{"role": "user", "content": "oi tudo bem"}]}
_, intent2 = openai_to_ollama(body2, num_gpu=0)
assert intent2 == "saudacao", intent2
print("OK: budget/guardrails/memoria pelo pedido REAL; nyx_intent não vaza")
PY

# 4. Confirmar que a heuristica sozinha (sem nyx_intent) tambem volta ao real:
./venv/bin/python - <<'PY'
from nyx.proxy import openai_to_ollama
# So sinteticas apos o turno real, SEM nyx_intent: cai na heuristica sobre o
# último user REAL (não sobre o tool_result).
body = {"model": "m", "messages": [
    {"role": "user", "content": "crie o arquivo core/utils.py com uma função"},
    {"role": "user", "content": "[resultado de list_files]\nREADME.md em ingles"},
], "tools": [{"function": {"name": "write_file"}}]}
ob, intent = openai_to_ollama(body, num_gpu=0)
print("fallback intent:", intent, "num_predict:", ob["options"]["num_predict"])
assert intent == "code" and ob["options"]["num_predict"] == 4096, (intent, ob["options"]["num_predict"])
print("OK: fallback (sem nyx_intent) tambem classifica pelo pedido REAL")
PY

# 5. Invariantes (não exige GPU):
bash scripts/sprint_invariants.sh
```

> Nota GPU: passos 3-4 rodam SEM Ollama/GPU (só funções puras do proxy). Smoke boot (`./run.sh --smoke`) e gauntlet (`./run.sh --gauntlet --only proxy`) exigem Ollama vivo e GPU exclusiva -> **DEFERIDOS** para janela de GPU exclusiva (mesmo padrão das specs 403/407), executar só quando `pgrep -af "Luna.*driver|valida_sprint"` estiver vazio (protocolo anti-contenção do BRIEF).

---

## Critério binário de aceite (IA executora)

- [ ] `_last_user_text` pula mensagens sintéticas (`[resultado de ` e `[resumo da conversa anterior]`) e devolve o último user REAL
- [ ] `openai_to_ollama` usa `body['nyx_intent']` quando presente e válido; fallback = heurística sobre o último user REAL
- [ ] `_VALID_INTENTS` espelha o conjunto de saída de `classify()`
- [ ] Loop guarda `self._turn_intent` em `_init_done_guard` e injeta `payload['nyx_intent']` no `_call_llm` (getattr defensivo)
- [ ] `_select_tools_for_context` pula sintéticas no scan de `last_user` e prefere `self._turn_intent`
- [ ] Proof runtime-real colado (passos 3-4): budget `code`=4096 preservado, `lembre-se`/`English` ausentes do `last_user`, `nyx_intent` NÃO no `ollama_body`
- [ ] `ruff` limpo, acentuação rc=0, `FAIL_AFTER <= FAIL_BEFORE`
- [ ] Smoke boot + gauntlet `--only proxy` DEFERIDOS (GPU exclusiva) e marcados como tal no relato
- [ ] NÃO commitar; NÃO tocar `Checkpoint.md`; NÃO tocar `nyx/config/defaults.py`, `nyx/agent/session.py` nem `nyx/agent/intent.py`

---

## Guardrails anti-engodo (obrigatórios)

NÃO marcar concluída se:
- `_last_user_text` passou a retornar `''` quando existe um user REAL na lista (o skip deve pular só as sintéticas, nunca o pedido genuíno).
- `nyx_intent` inválido (fora de `_VALID_INTENTS`) foi aceito sem cair no fallback.
- `nyx_intent` vazou para o `ollama_body` (o Ollama nunca pode receber o campo — AC5).
- O happy-path mudou: `body` sem `nyx_intent` e sem sintéticas deve classificar exatamente como antes.
- Alterou `NUM_PREDICT_BY_INTENT`, `session.py` (`to_messages`) ou o `classify()`.
- Proof runtime-real não colado, ou algum assert dos passos 3-4 falhou.

Se algo falhar: `[SPRINT 421] BLOQUEADA: <motivo 1 linha>`.

---

## Proof-of-work esperado (4 passos)

```bash
bash scripts/sprint_invariants.sh > /tmp/inv_before.txt 2>&1
FAIL_BEFORE=$(grep -c "^\[FAIL\]" /tmp/inv_before.txt)
# implementar
bash scripts/sprint_invariants.sh > /tmp/inv_after.txt 2>&1
FAIL_AFTER=$(grep -c "^\[FAIL\]" /tmp/inv_after.txt)
diff /tmp/inv_before.txt /tmp/inv_after.txt
```
Baseline esperado: `FAIL_BEFORE = 0`, `FAIL_AFTER <= 0`. Colar: inv_before/inv_after (tail), diff, o output do proof runtime-real (passos 3-4), o `rg` do passo 2, `git --no-pager diff --stat`.

**DEFERIDO para GPU exclusiva** (padrão 403/407, exige Ollama vivo):
- `./run.sh --smoke` -> deve imprimir `boot ok` (obrigatório antes de CONCLUIDA, `feedback_smoke_boot`).
- `./run.sh --gauntlet --only proxy` -> 100% (mais estável isolado após cooldown, ver flake do BRIEF).
- Validação as-user: fluxo `"leia <arquivo em ingles com 'lembre-se que'> e reescreva com docstrings"` -> o `write_file` completa sem truncar, sem retry de idioma, sem `write_memory` espontâneo.

---

## Gambiarras específicas desta sprint

- **Literais espelhados em vez de import:** `_SYNTHETIC_USER_PREFIXES` duplica os prefixos de `session.py:80` e `context.py:58` de propósito — importar `session`/`context` no `proxy` arrisca ciclo e acopla o transporte à camada de agente. Verificado: `context.py` não importa `proxy` (sem ciclo hoje), mas a duplicação de 2 literais e mais barata e mais estável que o import. Acoplamento registrado nos Invariantes.
- **`nyx_intent` como campo aditivo do body OpenAI:** e ignorado por qualquer cliente OpenAI padrão e nunca alcança o Ollama; carrega a intenção do turno de forma windowing-proof sem tocar o formato de mensagens. <!-- noqa-anonimato -->
- **`getattr(self, "_turn_intent", None)`:** defensivo — se `_init_done_guard` não rodou (não deveria, mas o probe de GPU e caminhos de teste existem), o payload simplesmente omite o campo e o proxy cai na heurística.
- **`chat`=512 e o pior caso:** quando o turno real sai da janela de 4 e não há `nyx_intent`, a heurística sobre `''` classifica `chat`=512 — pior que o `tool`=2048 do #352. Por isso o `nyx_intent` autoritativo (Fix A) e o que fecha (i) de forma robusta; o skip (Fix B) sozinho não basta na janela profunda.

---

## Validação humana (checklist do usuário)

```bash
cd /home/andrefarias/Desenvolvimento/Nyx-Code
git --no-pager show --stat HEAD

# Com o stack real (GPU exclusiva): mandar
#   "leia <um .md deste projeto que contenha 'lembre-se'> e reescreva com docstrings"
# Esperado: write_file completa (JSON não trunca), resposta em PT-BR, e a Nyx
# não grava memoria espontanea nem refaz por idioma.

ls dev-journey/06-sprints/concluidos/SPRINT_PROXY_INTENT_ON_USER_REQUEST_01.md  # apos conclusao
```

---

## Riscos e não-objetivos

| Risco / não-objetivo | Decisão |
|-------|-----------|
| Refatorar `session.py:to_messages` para marcar mensagens sintéticas com um campo estrutural (ex.: `"synthetic": True`) em vez de prefixo de texto | **NÃO-OBJETIVO desta sprint.** Seria a solução "certa" a longo prazo, mas cruza a camada de sessão e mexe no formato do histórico (risco em todo o loop). Se o dono quiser, registrar sprint nova `INFRA-SYNTHETIC-MSG-TAG-01` (anti-débito, `feedback_nenhum_debito`). |
| Fazer o proxy importar os prefixos de `session`/`context` (fonte única real) | Fora de escopo — risco de ciclo de import no transporte; mantidos literais espelhados com acoplamento registrado. |
| Sintoma do achado 411 no contrato do loop | Já coberto pela sprint 411 (sintoma). Esta fecha a causa no gating do proxy; as duas são complementares, não sobrepostas. |
| `nyx_intent` enviado por cliente externo malicioso para inflar orçamento | Capado por `_VALID_INTENTS` + `NUM_PREDICT_HARD_CAP` (já vigente em `defaults.py`); o proxy e local-only (11436). |

---

## Fora de escopo (anti-débito)

- **`INFRA-SYNTHETIC-MSG-TAG-01` (sugerida):** substituir o reconhecimento por prefixo de texto por um marcador estrutural em `HistoryEntry`/`to_messages`, eliminando a duplicação de literais entre `session.py`, `context.py`, `proxy.py` e `_iteration.py`. Mecanismo diferente (camada de sessão), maior superfície — sprint própria.

---

## Referências

- BRIEF: `/home/andrefarias/Desenvolvimento/Nyx-Code/VALIDATOR_BRIEF.md`
- Precedente direto: `#352 PROXY-INTENT-CODE-BUDGET-PARSER-01` (`dev-journey/06-sprints/SPRINT_ORDER_MASTER.md` linha 991) — esta sprint impede a regressão daquele fix em fluxos multi-step.
- Relacionada: sprint 411 (sintoma de `write_memory` espontâneo no contrato do loop).
- Fontes canônicas dos prefixos: `nyx/agent/session.py:79-81`, `nyx/agent/context.py:58`.
- Origem: auditoria de prontidão 2026-07-12 (achado ALTA, verificado adversarialmente).

---

*"O orçamento e o guardrail devem servir ao que o usuário pediu, não ao que a ferramenta devolveu -- caso contrário a infra passa a reagir ao próprio eco." -- princípio de gating (ADR-032/033)*
