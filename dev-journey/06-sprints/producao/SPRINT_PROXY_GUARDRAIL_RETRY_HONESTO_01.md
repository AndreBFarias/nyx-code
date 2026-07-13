## 0. SPEC (machine-readable)

```yaml
sprint:
  id: PROXY-GUARDRAIL-RETRY-HONESTO-01
  numero: 440
  title: "Retry de guardrail honesto: retry de IDENTITY que falha não entrega o vazamento; exceção no retry não destrói resposta válida já computada"
  onda: 48
  prioridade: MEDIA
  tipo: Bugfix
  dependencias: []
  desbloqueia: []
  absorve: []

  touches:
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/agent/lang_check.py
      reason: "adicionar redact_provider_mentions(text) -- redação determinística reaproveitando _PROVIDER_PATTERN + _SELF_AI_PATTERN; fallback usado pelo proxy quando o retry de IDENTITY falha"
      linhas_alvo: "após 161 (fim de mentions_provider), antes do rodapé de docstring 164-165"
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/proxy.py
      reason: "AC1: no bloco IDENTITY, quando o retry retorna None, redigir o content original em vez de passar o vazamento adiante + reformular o hint sem listar nomes proibidos; AC2: envolver o session.post de _retry_with_hint em try/except (ClientError, TimeoutError) -> None"
      linhas_alvo: "614-618 (_retry_with_hint post), 764-775 (bloco IDENTITY: hint + fallback), import 29 (aiohttp), import 41 (lang_check)"
  creates: []
  removes: []

  forbidden:
    - "Adicionar emoji"
    - "Mencao a IA proprietaria em .py fora de regex/hint ja marcados noqa"
    - "Tocar a cascata OOM (_post_chat_with_oom_recovery), gating de intent, MEMORY-INTENT"
    - "Alterar o happy-path dos 3 guardrails: retry que RECUPERA (recovered is not None) segue byte-identico"
    - "Alterar o guardrail LANG (a mudanca de fallback e SO no bloco IDENTITY; LANG e MEMORY seguem passando o original adiante quando o retry falha, semantica original preservada)"
    - "Mudar a semantica de resp.status != 200 do _retry_with_hint (ja retorna None; a mudanca e ADITIVA: cobrir tambem exception de transporte)"
    - "Enfraquecer _PROVIDER_PATTERN ou _SELF_AI_PATTERN (a 407 trata detecção; esta trata o fallback pós-detecção)"

  tests:
    - cmd: "/home/andrefarias/.local/bin/ruff check nyx/proxy.py nyx/agent/lang_check.py"
      deve_passar: true
    - cmd: "python3 ~/.config/zsh/scripts/validar-acentuacao.py --paths nyx/proxy.py nyx/agent/lang_check.py"
      deve_passar: true
    - cmd: "bash scripts/sprint_invariants.sh"
      deve_passar: true
    - cmd: "./run.sh --gauntlet --only proxy"
      timeout: 300
      deve_passar: true
      nota: "DEFERIDO para GPU exclusiva (contencao de VRAM) -- ver Proof-of-work"

  acceptance_criteria:
    - "AC1a (achado proxy.py:623/774): quando o retry de IDENTITY retorna None, o content ORIGINAL vazado NÃO e passado adiante -- e redigido por redact_provider_mentions e, se ainda assim mentions_provider detectar, cai para a linha canônica de identidade. Zero vazamento chega ao usuário."
    - "AC1b (achado proxy.py:764-765): o hint do retry de IDENTITY deixa de listar nomes proibidos (Qwen/GPT/Claude/Llama) -- passa a instruir 'não cite o nome de nenhum modelo nem empresa de IA'. Reduz o eco em modelo 3b (o hint não injeta mais os nomes proibidos como turno de user no contexto do retry)."
    - "AC2 (achado proxy.py:614): o session.post de _retry_with_hint fica em try/except (aiohttp.ClientError, asyncio.TimeoutError) retornando None -- se o Ollama cai ENTRE a inferência original e o retry, o guardrail devolve None e o caller preserva o result válido já computado, em vez de propagar a exceção e 500ar o turno."
    - "redact_provider_mentions(text) e pura e determinística: substitui as menções de _PROVIDER_PATTERN e _SELF_AI_PATTERN por 'Nyx'; para todo caso conhecido, mentions_provider(redact_provider_mentions(x)) is None."
    - "Happy-path intacto: retry que recupera (recovered is not None) troca o result como antes, byte-identico; LANG e MEMORY-INTENT seguem com a semântica original (fallback = passar original adiante)."
    - "Proof runtime-real SEM GPU: (a) prova pura de redact + (b) prova de _retry_with_hint devolvendo None quando o session.post levanta aiohttp.ClientError. Gauntlet --only proxy DEFERIDO para GPU exclusiva."
    - "ruff limpo, acentuação rc=0, FAIL_AFTER <= FAIL_BEFORE, smoke boot ok."
```

---

# Sprint PROXY-GUARDRAIL-RETRY-HONESTO-01 — Retry de guardrail honesto

**Status:** PENDENTE
**Data criação:** 2026-07-12
**Modelo obrigatório:** claude-opus-4-7 (executor-sprint autorizado pelo dono nesta onda)

---

## Contexto do projeto (snapshot — não referência)

> **ADRs relevantes (inline):**
> - **ADR-005 (Anonimato) + ADR-027 (Identidade Nyx):** a identidade Nyx e INVIOLÁVEL; nenhuma resposta pode mencionar provider proprietário nem se autodescrever como IA/modelo. O guardrail IDENTITY existe para blindar isso.
> - **ADR-032/033/034 (a infra carrega o modelo; robustez pertence à INFRA, não ao modelo):** o pior LLM local (qwen2.5-coder:3b) na pior máquina deve parecer um agente profissional offline. Quando o modelo eco-repete o nome proibido, a INFRA corrige de forma determinística — não se confia no modelo para acertar no segundo turno.
> - Princípio "Honestidade na falha" (`dev-journey/02-architecture/DESENHO_CONTRATO_EXECUCAO.md` §6): quando a infra não garante, a mensagem e clara — nunca um vazamento cru entregue como se fosse a Nyx, nem um turno perdido por uma exceção evitável.
>
> **Estado (2026-07-12):** `qwen2.5-coder:3b`. ONDA-48 fase raiz: núcleo do contrato concluido. Esta e satélite dos guardrails de saída do proxy (achados da auditoria adversarial 2026-07-12). Ports: Ollama `11435`, proxy `11436` (`nyx/config/defaults.py`). Guardrails de saída: `nyx/proxy.py`, função `_apply_output_guardrails` (LANG -> IDENTITY -> MEMORY-INTENT), helper comum `_retry_with_hint`.

---

## Problema

A auditoria adversarial de prontidão (2026-07-12) achou dois defeitos no mesmo mecanismo — o retry de guardrail de saída do proxy. Ambos transformam um dispositivo que existe para MELHORAR a resposta em causa de dano.

### Achado 1 — o retry de IDENTITY que insiste entrega o vazamento intacto, e o próprio hint injeta os nomes proibidos

`nyx/proxy.py`, bloco IDENTITY de `_apply_output_guardrails` (linhas 749-775):

- quando o content vaza um provider, dispara-se `_retry_with_hint` (linha 761) com um hint que valida `not _mentions_provider(c)` (linhas 767-770);
- se o retry falha a validação, `_retry_with_hint` devolve `None` (proxy.py:623) e o caller mantém o `result` ORIGINAL — `if recovered is not None: result = recovered` (proxy.py:774-775), ou seja, o `else` implícito preserva o content VAZADO;
- esse content segue por `handle_chat` (proxy.py:880 `return web.json_response(result)`) e chega ao usuário — o pior caso do guardrail e entregar `"sou o Qwen..."` / `"baseando-se em meus treinamentos"` intacto, ferindo ADR-005/027 (INVIOLÁVEL);
- agravante: o hint (proxy.py:764-765) lista literalmente `"(Qwen, GPT, Claude, Llama, etc.)"` e e anexado como turno de `user` no contexto do retry (`_retry_with_hint`, proxy.py:612). Modelos 3b são eco-prone: colocar os nomes proibidos no contexto AUMENTA a chance de o retry re-vazar e cair no pass-through. <!-- noqa-anonimato -->

**Prova runtime nova (sessão holística 2026-07-12 T7):** um summary entregue ao usuário continha `"baseando-se em meus treinamentos"` — `_SELF_AI_PATTERN` (`nyx/agent/lang_check.py:136`, alternativa `(meus|nos\s+meus)\s+treinamentos`) CASA esse trecho, logo o guard DETECTOU, o retry insistiu e o proxy ENTREGOU o vazamento.

Distinto da 407 (SPRINT_IDENTITY_GUARD_COPULA_01, gap de regex da cópula), que trata de DETECÇÃO. Esta trata do FALLBACK pós-detecção — o que fazer quando a detecção acerta mas o retry não corrige.

### Achado 2 — exceção dentro do retry destrói uma resposta válida já computada

`nyx/proxy.py`, `_retry_with_hint` (linha 614):

- `async with session.post(f"{OLLAMA_URL}/api/chat", json=retry_body) as resp:` NÃO tem try/except; só trata `resp.status != 200` (proxy.py:615);
- `_retry_with_hint` e chamado por `_apply_output_guardrails` (proxy.py:731 LANG, 761 IDENTITY, 799 MEMORY) DEPOIS de `result` já estar pronto em `handle_chat` (proxy.py:857-862);
- se o Ollama cai ENTRE a inferência original (bem-sucedida) e o retry do guardrail — plausível na pior máquina, onde a própria inferência anterior pressiona a memória e pode derrubar o Ollama — a exceção de transporte (`aiohttp.ClientError` / `asyncio.TimeoutError`) propaga, `handle_chat` 500a e o usuário perde uma resposta boa que JÁ EXISTIA;
- a semântica pretendida já e "retry falhou, passa adiante" (o `resp.status != 200` já devolve `None`); falta apenas cobrir a exceção de transporte com a mesma semântica.

**Nota:** os achados 1 e 2 são o MESMO mecanismo (o retry de guardrail de saída), com ACs separados. Achado 2 protege os 3 guardrails (LANG/IDENTITY/MEMORY); achado 1 e específico do fallback de IDENTITY.

---

## Causa-raiz (verificada no código, 2026-07-12)

Reconferência das âncoras do briefing no arquivo real — sem deslize material:

- `proxy.py:614` — `async with session.post(f"{OLLAMA_URL}/api/chat", json=retry_body) as resp:` — confere.
- `proxy.py:615` — `if resp.status != 200:` (único guard); `proxy.py:620-624` — `if validate(candidate): ... return candidate` / `return None` — confere.
- `proxy.py:731 / 761 / 799` — as 3 chamadas de `_retry_with_hint` (LANG/IDENTITY/MEMORY) — confere.
- `proxy.py:764-765` — hint com a lista `"(Qwen, GPT, Claude, Llama, etc.)"` — confere (marcado `noqa-anonimato` / `noqa: ai-mention`). <!-- noqa-anonimato -->
- `proxy.py:774-775` — `if recovered is not None: result = recovered` (o `else` implícito preserva o original) — confere.
- `handle_chat:857-862` — `result = ollama_to_openai(...)` antes dos guardrails; `proxy.py:880` — `return web.json_response(result)` — confere.
- `lang_check.py:131-139` — `_SELF_AI_PATTERN`; a alternativa de `treinamentos` está na linha 136 (o briefing citou "lang_check.py:136", que aponta a alternativa específica, não o início do compile em 131) — sem divergência material.
- `mentions_provider` retorna o trecho casado em minúsculas (`lang_check.py:157-161`); `_PROVIDER_PATTERN` (111-124) pega NOMES, `_SELF_AI_PATTERN` (131-139) pega auto-identificação genérica.

**Divergência do briefing:** nenhuma material. Único ajuste de precisão: o `_SELF_AI_PATTERN` inicia o `re.compile` na linha 131 (o briefing citou :136, que e a linha da alternativa `treinamentos` dentro do padrão) — não altera o fix.

---

## Solução proposta

Três correções aditivas e cirúrgicas. Nenhuma toca a cascata OOM, o gating de intent, o happy-path (retry que recupera) nem os guardrails LANG/MEMORY (que mantêm a semântica original de passar o original adiante quando o retry falha).

### 1. `redact_provider_mentions` em `nyx/agent/lang_check.py` (nova função pura)

Reaproveita os dois padrões já existentes para redigir de forma determinística — a INFRA corrige, não o modelo:

```python
def redact_provider_mentions(text: str) -> str:
    """Redige menções a IA proprietária / auto-identificação como IA.

    Fallback determinístico do proxy quando o retry de IDENTITY falha: em vez
    de entregar o vazamento ('sou o Qwen', 'baseando-se em meus treinamentos'),
    substitui os trechos casados por 'Nyx'. Reaproveita _PROVIDER_PATTERN
    (nomes) e _SELF_AI_PATTERN (auto-referência genérica como IA). Preserva o
    restante do content útil (ADR-005/027 -- identidade inviolável).

    Garantia: para todo caso conhecido, mentions_provider(redact_provider_mentions(x))
    is None. Se, por borda, ainda casar, o caller cai na linha canônica.
    """
    if not text:
        return text
    out = _PROVIDER_PATTERN.sub("Nyx", text)
    out = _SELF_AI_PATTERN.sub("Nyx", out)
    return out
```

### 2. Bloco IDENTITY em `nyx/proxy.py` — redigir em vez de vazar + hint sem nomes

**Import (proxy.py:41):** juntar a nova função ao import existente do `lang_check`:
```python
from nyx.agent.lang_check import redact_provider_mentions as _redact_provider_mentions  # noqa: E402
```

**Hint (proxy.py:764-765) — reformular sem listar nomes (AC1b):**
```python
"Você é Nyx, codificadora local. Não cite o nome de nenhum modelo nem de "
"nenhuma empresa de IA, e não se descreva como IA ou modelo de linguagem. "
"Refaça em PT-BR mantendo a identidade Nyx.",  # noqa-anonimato  # noqa: ai-mention
```

**Fallback (proxy.py:774-775) — redigir quando o retry falha (AC1a):**
```python
if recovered is not None:
    result = recovered
else:
    # PROXY-GUARDRAIL-RETRY-HONESTO-01: o retry insistiu no vazamento. NÃO
    # entregar o original vazado (ADR-005/027). Redige determinísticamente;
    # se, por borda, ainda casar, cai na linha canônica de identidade.
    safe = _redact_provider_mentions(content)
    if _mentions_provider(safe):
        safe = "Sou a Nyx, sua codificadora local. Como posso ajudar?"
    logger.warning("IDENTITY: retry insistiu; content redigido determinísticamente")
    result["choices"][0]["message"]["content"] = safe
```

### 3. `_retry_with_hint` em `nyx/proxy.py` — blindar o transporte (AC2)

**Import (proxy.py:29):** somar `ClientError` ao import do aiohttp:
```python
from aiohttp import ClientError, ClientSession, ClientTimeout, web  # noqa: E402
```

**Envolver o post (proxy.py:614-618):**
```python
try:
    async with session.post(f"{OLLAMA_URL}/api/chat", json=retry_body) as resp:
        if resp.status != 200:
            logger.warning("%s: retry HTTP %d; passa adiante", tag, resp.status)
            return None
        data = await resp.json()
except (ClientError, asyncio.TimeoutError) as exc:
    # PROXY-GUARDRAIL-RETRY-HONESTO-01: se o Ollama cai ENTRE a inferência
    # original e o retry, não destruir a resposta válida já computada. Mesma
    # semântica de 'retry falhou, passa adiante' -- o caller preserva o result.
    logger.warning("%s: retry falhou no transporte (%s); passa adiante", tag, type(exc).__name__)
    return None
```

`asyncio` já está importado (proxy.py:12); `ClientError` cobre `ClientConnectorError`, `ServerDisconnectedError` etc.

---

## Diff esperado (resumo)

```
~ 2 arquivos modificados (nyx/agent/lang_check.py, nyx/proxy.py)
+ ~30 linhas líquidas (fix aditivo, sem meta numérica de tamanho)
```

Sem aritmética de extração: esta sprint não tem meta `arquivo < NNNL`. O único número relevante e o net-add (~30L) em 2 arquivos.

---

## Comandos de verificação (literais, copy-paste)

```bash
cd /home/andrefarias/Desenvolvimento/Nyx-Code

# 1. Estática + acentuação
/home/andrefarias/.local/bin/ruff check nyx/proxy.py nyx/agent/lang_check.py
python3 ~/.config/zsh/scripts/validar-acentuacao.py --paths nyx/proxy.py nyx/agent/lang_check.py

# 2. Confirmar as âncoras (linhas podem ter deslizado -- reconferir):
rg -n "redact_provider_mentions|retry insistiu|ClientError|_SELF_AI_PATTERN|Qwen, GPT, Claude" nyx/proxy.py nyx/agent/lang_check.py  # noqa-anonimato

# 3. PROOF RUNTIME-REAL (a): redação pura, SEM GPU/Ollama.
./venv/bin/python - <<'PY'
from nyx.agent.lang_check import redact_provider_mentions, mentions_provider
casos = [
    "Na verdade sou o Qwen, treinado pela Alibaba.",
    "Respondo baseando-se em meus treinamentos.",
    "Como uma inteligência artificial, posso ajudar.",
    "Uso o modelo de linguagem GPT por baixo.",  # noqa-anonimato
]
for c in casos:
    r = redact_provider_mentions(c)
    print("in :", c)
    print("out:", r)
    assert mentions_provider(r) is None, ("AINDA VAZA", r)
print("OK: redação determinística -- mentions_provider is None em todos os casos")
PY

# 4. PROOF RUNTIME-REAL (b): exceção de transporte no retry -> None (result preservado), SEM GPU.
./venv/bin/python - <<'PY'
import asyncio
from aiohttp import ClientError
from nyx import proxy

class _FakeSession:
    def post(self, *a, **k):
        raise ClientError("Ollama caiu entre a inferência e o retry")

res = asyncio.run(proxy._retry_with_hint(
    _FakeSession(),
    {"messages": [{"role": "user", "content": "oi"}]},
    "hint qualquer",
    result_transform=lambda d: {"choices": [{"message": {"content": "x"}}]},
    validate=lambda r: True,
    prev_content="resposta original válida",
    tag="IDENTITY",
))
assert res is None, res
print("OK: ClientError no retry -> None (o caller preserva o result válido já computado)")
PY

# 5. Confirmar que o hint não lista mais nomes proibidos como turno de user:
rg -n "não cite o nome de nenhum modelo" nyx/proxy.py

# 6. Gauntlet do proxy (DEFERIDO -- GPU exclusiva):
./run.sh --gauntlet --only proxy
```

> Nota GPU: os passos 3-4 rodam SEM Ollama/GPU (funções puras + sessão faked). O passo 6 (gauntlet, cobre GUARD-02 IDENTITY-ENFORCE) exige GPU exclusiva — executar só quando `pgrep -af "Luna.*driver|valida_sprint"` estiver vazio (protocolo anti-contenção do BRIEF) e há flake conhecido de VRAM em execuções consecutivas. **DEFERIDO para GPU exclusiva**, como as specs 403/407.

---

## Critério binário de aceite (IA executora)

- [ ] `redact_provider_mentions` criada em `lang_check.py`, pura, reaproveitando os dois padrões; `mentions_provider(redact_provider_mentions(x)) is None` nos casos do passo 3
- [ ] Bloco IDENTITY: quando `recovered is None`, o content e REDIGIDO (com fallback canônico) — o original vazado NÃO chega ao usuário
- [ ] Hint de IDENTITY reformulado SEM listar nomes proibidos (não injeta mais Qwen/GPT/Claude/Llama no contexto do retry)
- [ ] `_retry_with_hint`: `session.post` em `try/except (ClientError, asyncio.TimeoutError)` -> `None` (mesma semântica de passar o original adiante)
- [ ] Proof runtime-real (a) e (b) colados; ambos sem GPU
- [ ] Happy-path intacto: `recovered is not None` troca o result como antes; LANG e MEMORY-INTENT com semântica original
- [ ] `ruff` limpo, acentuação rc=0, `FAIL_AFTER <= FAIL_BEFORE`, smoke boot ok
- [ ] Gauntlet `--only proxy` 100% (DEFERIDO — colar quando rodar com GPU exclusiva)
- [ ] `SPRINT_ORDER_MASTER.md` marca 440 CONCLUIDA; spec movida para `concluidos/`
- [ ] NÃO commitar; NÃO tocar Checkpoint.md

---

## Guardrails anti-engodo (obrigatórios)

NÃO marcar concluída se:
- O content vazado ainda pode chegar ao usuário (o `else` do bloco IDENTITY não redige, ou redige mas não cobre o caso de `mentions_provider` residual com a linha canônica).
- O hint de IDENTITY ainda lista nomes proibidos (`Qwen`/`GPT`/`Claude`/`Llama`) no texto anexado como turno de user. <!-- noqa-anonimato -->
- O `session.post` de `_retry_with_hint` segue sem `try/except` de transporte, ou o except engole erro DIFERENTE de `ClientError`/`TimeoutError` (não capturar `Exception` genérico — mascararia bugs reais do result_transform/validate).
- O happy-path mudou: retry que recupera (`recovered is not None`) deve seguir byte-identico; LANG e MEMORY não podem ganhar redação (a redação e SO de IDENTITY).
- `_PROVIDER_PATTERN` ou `_SELF_AI_PATTERN` foram enfraquecidos (detecção e da 407; aqui só se ADICIONA a função de redação).
- Proof runtime-real (a) e (b) não colados.

Se algo falhar: `[SPRINT 440] BLOQUEADA: <motivo 1 linha>`.

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

Baseline esperado: `FAIL_BEFORE = 0`, `FAIL_AFTER <= 0`. Colar: inv_before/inv_after (tail), diff, o output das provas runtime-real (passos 3-4), o `rg` dos passos 2 e 5, `git --no-pager diff --stat` e `./run.sh --smoke` (deve imprimir `boot ok`).

Proof que exige GPU (gauntlet `--only proxy`, cobre GUARD-02 IDENTITY-ENFORCE de ponta a ponta): **DEFERIDO para GPU exclusiva** — colar output separado quando `pgrep` de contenção estiver vazio.

---

## Gambiarras específicas desta sprint

- **Redação com "Nyx" pode ficar gramaticalmente estranha:** `"sou uma inteligência artificial"` -> `"Nyx artificial"`. Custo cosmético aceito — a prioridade e ZERO vazamento (ADR-005/027 INVIOLÁVEL) preservando o restante do content útil. A linha canônica de fallback cobre a borda em que a redação não basta.
- **Por que redigir e não sempre responder a linha canônica:** o guardrail IDENTITY só dispara em intent conversacional (`saudacao/chat/comando`); ainda assim, a prova T7 mostrou o vazamento DENTRO de um summary útil. Redigir preserva o summary; a canônica e só o piso de segurança. (Decisão registrada; a alternativa "sempre canônica" descartaria conteúdo bom.)
- **`ClientError` cobre a família:** `aiohttp.ClientError` e a base de `ClientConnectorError`/`ServerDisconnectedError` etc.; `asyncio.TimeoutError` cobre o timeout do `ClientTimeout`. NÃO capturar `Exception` genérico — mascararia bug no `result_transform`/`validate`.
- **`mentions_provider` retorna minúsculo:** e usado só como predicado (`if _mentions_provider(safe)`), não para reconstruir texto — o casamento em minúsculas não afeta a redação (o `.sub` opera sobre o texto original com `re.IGNORECASE`).

---

## Validação humana (checklist do usuário)

```bash
cd /home/andrefarias/Desenvolvimento/Nyx-Code
git --no-pager show --stat HEAD

# Com o stack real e GPU exclusiva: forçar o modelo a vazar (prompt provocador
# de identidade). A Nyx nunca deve entregar "sou o Qwen" / "meus treinamentos";
# no pior caso, texto redigido ou "Sou a Nyx, sua codificadora local."
# Derrubar o Ollama entre a inferência e o retry (janela estreita) NÃO deve 500ar:
# a resposta original válida deve ser entregue.

ls dev-journey/06-sprints/concluidos/SPRINT_PROXY_GUARDRAIL_RETRY_HONESTO_01.md  # existe
```

---

## Fora de escopo (anti-débito)

| Item | Decisão |
|-------|-----------|
| Detecção da cópula / gaps de regex (`_PROVIDER_PATTERN`/`_SELF_AI_PATTERN`) | **NÃO-OBJETIVO.** E a sprint 407 (SPRINT_IDENTITY_GUARD_COPULA_01). Esta trata do FALLBACK pós-detecção, não da detecção. |
| Aplicar redação também a LANG e MEMORY-INTENT | Fora de escopo — o vazamento de identidade e específico de IDENTITY; LANG (idioma) e MEMORY (tool-call) têm outra semântica de fallback. Se surgir necessidade, sprint própria. |
| Middleware de erro no `web.Application()` do proxy (503 estruturado quando o Ollama cai) | **NÃO-OBJETIVO.** Já registrado como recomendação da 413 (`INFRA-PROXY-STRUCTURED-503-01`). Não absorver aqui. |
| Redação com paráfrase natural (LLM-assisted) em vez de substituição literal | Fora de escopo — a INFRA deve ser determinística e offline; paráfrase por modelo reintroduz o risco que o guardrail existe para eliminar. |

---

## Referências

- BRIEF: `/home/andrefarias/Desenvolvimento/Nyx-Code/VALIDATOR_BRIEF.md`
- Desenho do contrato: `dev-journey/02-architecture/DESENHO_CONTRATO_EXECUCAO.md` (§6, "Honestidade na falha")
- Detecção (sprint irmã): `dev-journey/06-sprints/concluidos/SPRINT_IDENTITY_GUARD_COPULA_01.md` (407)
- Achados + tabela: `dev-journey/05-history/SPRINT_ORDER_MASTER.md` (bloco ONDA-48)
- Origem: auditoria adversarial de prontidão 2026-07-12 + prova runtime da sessão holística 2026-07-12 T7 (summary com "baseando-se em meus treinamentos" entregue ao usuário)

---

*"O guardrail existe para melhorar a resposta; quando ele entrega o vazamento ou destrói a resposta boa, virou o oposto de si mesmo. A INFRA corrige de forma determinística — não confia no modelo para acertar no segundo turno." — ADR-032/033/034*
