## 0. SPEC (machine-readable)

```yaml
sprint:
  id: LOOP-RECOVERY-TRIGGER-PTBR-01
  numero: 420
  title: "Auto-recovery do loop e codigo morto: gatilho procura keywords em ingles, mensagens sao PT-BR"
  onda: 48
  prioridade: ALTA
  tipo: Bugfix
  dependencias: []
  desbloqueia: []
  absorve: []

  touches:
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/agent/loop/_iteration.py
      reason: "_call_llm anexa error_kind estruturado a cada retorno de erro (timeout/connect/provider/decode/unknown); _try_recovery eleva o teto do warmup para WARMUP_RECOVERY_TIMEOUT"
      linhas_alvo: "971-993 (os 4 handlers de erro de _call_llm), 1008-1016 (warmup POST de _try_recovery)"
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/agent/loop/_core.py
      reason: "_run_iterations decide recovery por error_kind estruturado (RECOVERABLE_ERROR_KINDS), não por substring da mensagem de usuário PT-BR"
      linhas_alvo: "22 (import de _constants), 414-419 (bloco de decisao do recovery)"
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/agent/loop/_constants.py
      reason: "fonte unica: RECOVERABLE_ERROR_KINDS (consumido por _core) e WARMUP_RECOVERY_TIMEOUT (consumido por _iteration); _constants não importa _core nem _iteration, e importado pelos dois"
      linhas_alvo: "7 (próximo de LLM_TIMEOUT)"
  creates: []
  removes: []

  forbidden:
    - "Adicionar emoji"
    - "Usar 'print()' fora de cli.py/output.py"
    - "Mencao a IA proprietaria"
    - "Alterar o texto PT-BR do campo 'error' de qualquer handler (o campo novo error_kind e ADITIVO; a mensagem ao usuário segue byte-identica)"
    - "Remover ou reordenar os handlers existentes (TimeoutException/ConnectError/ProviderError/Exception)"
    - "Alterar o happy-path do _call_llm (HTTP 200 + JSON valido segue byte-identico)"
    - "Tocar _try_recovery alem do teto do warmup POST (o loop de 3 tentativas, o sleep de 5s e a probe GET /v1/models com timeout=30 ficam intactos)"
    - "Voltar a rotear recovery por substring de mensagem de usuário"
    - "Tocar a cascata OOM do proxy, gating, write_memory, ou os guards do contrato (397/398/399/400/401)"

  tests:
    - cmd: "/home/andrefarias/.local/bin/ruff check nyx/agent/loop/_iteration.py nyx/agent/loop/_core.py nyx/agent/loop/_constants.py"
      deve_passar: true
    - cmd: "bash scripts/sprint_invariants.sh"
      deve_passar: true
    - cmd: "./run.sh --smoke"
      deve_passar: true
    - cmd: "./run.sh --gauntlet --only proxy"
      timeout: 300
      deve_passar: true
      nota: "DEFERIDO para GPU exclusiva (protocolo anti-contencao do BRIEF)"

  acceptance_criteria:
    - "_call_llm anexa error_kind a TODOS os 4 retornos de erro: TimeoutException->'timeout', ConnectError->'connect', ProviderError->'provider', Exception generico->'decode' se json.JSONDecodeError senao 'unknown'"
    - "_run_iterations roteia recovery por error_kind in RECOVERABLE_ERROR_KINDS (frozenset em _constants), NÃO por 'connection'/'disconnect'/'Extra data'/'500' na mensagem PT-BR"
    - "RECOVERABLE_ERROR_KINDS = {'connect','timeout','decode','http_error'}; no cenario-nucleo (Ollama morto por OOM) ConnectError e Timeout AGORA disparam _try_recovery em vez de encerrar em SessionState.ERROR"
    - "Prova runtime-real SEM GPU: AgentLoop com proxy_url apontando porta morta -> _call_llm devolve error_kind='connect' e o texto PT-BR 'conexão recusada' intacto"
    - "warmup POST de _try_recovery usa timeout=WARMUP_RECOVERY_TIMEOUT (300) via constante unica em _constants; a probe GET /v1/models segue timeout=30"
    - "mensagens PT-BR do campo 'error' byte-identicas; happy-path intacto; handlers não reordenados; ruff limpo, acentuacao rc=0, invariantes FAIL_AFTER <= FAIL_BEFORE, smoke boot ok"
```

---

# Sprint LOOP-RECOVERY-TRIGGER-PTBR-01 — Auto-recovery do loop deixa de ser codigo morto

**Status:** PENDENTE
**Data criação:** 2026-07-12
**Modelo obrigatorio:** claude-opus-4-7 (executor-sprint autorizado pelo dono nesta onda)

---

## Contexto do projeto (snapshot — não referencia)

> **ADRs relevantes (inline):**
> - **ADR-032/033/034 A INFRA CARREGA O MODELO / ROBUSTEZ E DA INFRA, NÃO DO MODELO:** o Nyx-Code faz o pior LLM local (qwen 3b) na pior maquina (RTX 3050 4GB, HDD, desktop disputando VRAM) parecer o Claude Code offline. Quando o Ollama cai por OOM-kill do kernel, a infra tem que se recuperar sozinha — "crash de OOM = cadeia falhou" e a alma do projeto. O usuario-alvo e leigo e sem hardware bom. <!-- noqa-anonimato -->
> - ADR-009, ADR-001, ADR-006.
>
> **Estado (2026-07-12):** `qwen2.5-coder:3b`. ONDA-48 fase raiz: nucleo do contrato (399/397/400/398/401) CONCLUIDO. Esta sprint e satelite de robustez do transporte, irma da 413 (falha honesta do proxy) e da 414 (teto de boot do Ollama). Ports: Ollama `11435`, proxy `11436` (`nyx/config/defaults.py`). Constantes do loop: `nyx/agent/loop/_constants.py`.

---

## Problema

**Achado ALTA (auditoria de prontidao 2026-07-12, verificado adversarialmente).** A infraestrutura de auto-recovery do loop — que existe justamente para compensar um crash do Ollama na maquina fraca — e **codigo morto**: o gatilho que decide se dispara o recovery procura substrings em ingles na mensagem de erro, mas **todas** as mensagens que `_call_llm` produz sao PT-BR e nenhuma contem os gatilhos.

`nyx/agent/loop/_core.py:414-419`, dentro de `_run_iterations` (linha 377):

```python
if (
    "connection" in error_msg.lower()
    or "disconnect" in error_msg.lower()
    or "Extra data" in error_msg
    or "500" in error_msg
):
    ...  # recovery
```

`error_msg` e o campo `"error"` retornado por `_call_llm` (`nyx/agent/loop/_iteration.py`, metodo na linha 814). Os retornos de erro (verificados no codigo real):

- `_iteration.py:971-976` (`httpx.TimeoutException`): `"error": f"Proxy de inferencia não respondeu em {LLM_TIMEOUT}s. ..."` — sem `timeout` nos gatilhos, e a palavra "timeout" nem sequer esta na lista de keywords;
- `_iteration.py:977-982` (`httpx.ConnectError`): `"error": "conexão recusada pelo proxy de inferencia. ..."` — `'conexão' != 'connection'`;
- `_iteration.py:983-987` (`ProviderError`): `"error": f"{e.user_message}..."` — PT-BR do provider;
- `_iteration.py:988-993` (`Exception` generico, pega `JSONDecodeError` quando o proxy 500a): `"error": f"Falha inesperada ao contatar o proxy: {type(e).__name__}. ..."` — sem `connection`/`disconnect`/`Extra data`/`500`.

**Impacto.** No cenario-nucleo (Ollama morto por OOM-kill do kernel), o `else` de `_core.py:451-457` encerra a sessão em `SessionState.ERROR` **imediatamente** — `_try_recovery` (`_iteration.py:995`, com warmup do modelo) **nunca dispara**. A infra que existia para segurar o crash e inalcancavel. O fix da 413 (mensagem com `HTTP <code>`) resgataria por acidente so o caso 500 (a keyword `"500"` casaria); `ConnectError` e `Timeout` continuariam sem recovery.

**Achado BAIXA (mesmo mecanismo, callsite do recovery).** `_iteration.py:1008-1016`: o warmup POST pos-crash tem teto fixo `timeout=120`. Depois de um crash do Ollama na pior maquina, o reload do modelo do disco (HDD lento) + primeira inferencia em CPU pode passar de 120s, e o recovery falharia mesmo com o Ollama ja saudavel. Hoje isso esta mascarado pelo achado ALTA (recovery nunca dispara); vira relevante no instante em que o gatilho for corrigido. Por isso os dois achados vao juntos: consertar o gatilho sem folgar o warmup seria meio-fix.

---

## Causa-raiz (verificada no codigo, com divergencias do briefing registradas)

O roteamento do recovery e feito por **inspecao de substring da mensagem voltada ao usuário**, que e PT-BR por design (honestidade na falha, DESENHO §6). A mensagem PT-BR e um artefato de apresentacao; usa-la como sinal de controle acopla a decisao de recovery ao idioma do texto. A correcao correta e **rotear por um campo estruturado** (`error_kind`) que `_call_llm` ja sabe no ponto do `except`, e nunca mais por substring.

**Divergencias do briefing (linhas deslizaram / sugestao imprecisa):**

1. **Deslize de linhas.** O briefing cita ConnectError em `978-980` e timeout em `972-974`; no codigo real sao `977-982` (ConnectError) e `971-976` (timeout); o handler generico esta em `988-993`. Substancia confirmada; ancoras reconferidas.
2. **"Alternativa minima: incluir error_detail na checagem" e insuficiente.** O `error_detail` traz o nome da exceção em ingles (`ConnectError:`, `TimeoutException:`), mas o conjunto atual de keywords **não tem `timeout`**, entao `TimeoutException` continuaria sem recovery mesmo checando `error_detail`; e o casamento por substring de `ConnectError` depende de a str da exceção carregar `Connection refused` (dependente de locale/errno). Por isso adotamos o fix preferido do briefing (campo estruturado), não a alternativa minima.
3. **"Reutilizar a constante que o fix do 414 criar" não se aplica.** A sprint 414 (`SPRINT_INFRA_OLLAMA_BOOT_TIMEOUT_DEFAULT_01`, producao/) toca **apenas `run.sh`** — muda o default bash `NYX_OLLAMA_START_TIMEOUT` para 60 e não cria nenhuma constante Python compartilhavel. não existe fonte unica possivel entre um env de bash e o warmup Python. Logo, o warmup ganha sua **própria** constante `WARMUP_RECOVERY_TIMEOUT` em `_constants.py` (fonte unica do lado Python).

---

## solução proposta

Tres arquivos, correcao aditiva e ciruragica. O contrato entre `_call_llm` (produtor) e `_run_iterations` (consumidor) passa a ser o campo `error_kind`; a mensagem PT-BR `error` fica so para o usuário.

### `nyx/agent/loop/_constants.py` — fonte unica (próximo de `LLM_TIMEOUT`, linha 7)

```python
LLM_TIMEOUT = 600

# LOOP-RECOVERY-TRIGGER-PTBR-01: teto do warmup POST pos-crash em _try_recovery.
# Na pior maquina (HDD lento, CPU), o reload do modelo do disco + a 1a inferencia
# podem passar de 120s; 300s da folga sem travar o happy-path (o POST retorna assim
# que o modelo aquece). Fonte unica do lado Python -- a 414 so mexe no run.sh (bash),
# não ha constante compartilhavel entre os dois.
WARMUP_RECOVERY_TIMEOUT = 300

# LOOP-RECOVERY-TRIGGER-PTBR-01: kinds de erro que autorizam _try_recovery.
# Roteamos recovery por este campo estruturado (error_kind), NUNCA por substring
# da mensagem de usuário (que e PT-BR e por isso nunca casava os gatilhos ingleses
# do codigo antigo). 'http_error' fica reservado para a 413 (status != 200) marcar
# seus retornos e ja entrar coberto. Kinds canônicos que _call_llm emite:
# 'timeout' | 'connect' | 'provider' | 'decode' | 'unknown' | 'http_error'.
RECOVERABLE_ERROR_KINDS = frozenset({"connect", "timeout", "decode", "http_error"})
```

### `nyx/agent/loop/_iteration.py`

**Edit 1 — anexar `error_kind` aos 4 handlers de erro de `_call_llm` (971-993).** A mensagem `error` não muda; so entra o campo novo.

```python
        except httpx.TimeoutException as e:
            return {
                "error": f"Proxy de inferencia não respondeu em {LLM_TIMEOUT}s. "
                "Verifique se o Ollama e o proxy estao vivos: systemctl status ollama && ss -ltnp | grep 1143",
                "error_detail": f"{type(e).__name__}: {e}",
                "error_kind": "timeout",
            }
        except httpx.ConnectError as e:
            return {
                "error": "conexão recusada pelo proxy de inferencia. "
                "Reinicie o stack com ./run.sh ou confira ~/.nyx/logs/proxy.log.",
                "error_detail": f"{type(e).__name__}: {e}",
                "error_kind": "connect",
            }
        except ProviderError as e:
            return {
                "error": f"{e.user_message}" + (f" {e.hint}" if e.hint else ""),
                "error_detail": f"{type(e.cause).__name__ if e.cause else type(e).__name__}: {e.cause or e}",
                "error_kind": "provider",
            }
        except Exception as e:
            return {
                "error": f"Falha inesperada ao contatar o proxy: {type(e).__name__}. "
                "Abra ~/.nyx/logs/nyx.log para o traceback completo.",
                "error_detail": f"{type(e).__name__}: {e}",
                "error_kind": "decode" if isinstance(e, json.JSONDecodeError) else "unknown",
            }
```

**Edit 2 — teto do warmup por constante unica (1008-1016).** Importar `WARMUP_RECOVERY_TIMEOUT` no bloco de import de `_constants` (linhas 24-31) e trocar o literal:

```python
                        warmup = await client.post(
                            f"{ollama_base}/v1/chat/completions",
                            json={
                                "model": self._model,
                                "messages": [{"role": "user", "content": "hi"}],
                                "max_tokens": 5,
                            },
                            timeout=WARMUP_RECOVERY_TIMEOUT,
                        )
```

A probe `httpx.AsyncClient(timeout=30)` (linha 1004) e o `GET /v1/models` (1005) ficam intactos — 30s basta para liveness; so a inferencia de warmup precisa da folga.

### `nyx/agent/loop/_core.py`

**Edit 3 — importar o frozenset (linha 22).**

```python
from nyx.agent.loop._constants import PRESENTABLE_TOOLS, RECOVERABLE_ERROR_KINDS
```

**Edit 4 — rotear recovery por `error_kind` (414-419).** Substituir o bloco de substrings:

```python
                error_kind = response.get("error_kind", "")
                if error_kind in RECOVERABLE_ERROR_KINDS:
                    logger.warning("[loop] LLM caiu (%s), tentando recovery...", error_kind)
                    recovered = await self._try_recovery()
                    ...  # resto do bloco 420-450 INALTERADO
```

O corpo do `if` (linhas 420-450: `_try_recovery`, re-chamada, `_has_results`, retornos DONE/ERROR) e o `else` (451-457) permanecem byte-identicos. So a **condicao** muda: de substring PT-BR frouxa para pertinencia no conjunto estruturado.

---

## Diff esperado (resumo)

```
~ 3 arquivos modificados:
  nyx/agent/loop/_constants.py   (+ ~10L: 2 constantes + comentarios)
  nyx/agent/loop/_iteration.py   (+ 4L error_kind, + 1 import, ~ 1L timeout)
  nyx/agent/loop/_core.py        (+ 1 import term, ~ 6L bloco de condicao)
+ ~20 linhas liquidas. Sem meta numerica de tamanho -- fix aditivo, nenhum arquivo cruza limite.
```

Sem aritmetica de extracao: esta sprint não tem meta `arquivo < NNNL`. O único numero relevante e o net-add (~20L) espalhado em 3 arquivos.

---

## Comandos de verificação (literais, copy-paste)

```bash
cd /home/andrefarias/Desenvolvimento/Nyx-Code

# 1. Estatica + acentuacao (ruff via binario direto -- não ha modulo ruff no venv, ver BRIEF)
/home/andrefarias/.local/bin/ruff check nyx/agent/loop/_iteration.py nyx/agent/loop/_core.py nyx/agent/loop/_constants.py
python3 ~/.config/zsh/scripts/validar-acentuacao.py --paths nyx/agent/loop/_iteration.py nyx/agent/loop/_core.py nyx/agent/loop/_constants.py

# 2. Confirmar as ancoras (linhas podem ter deslizado -- reconferir; licao 4):
rg -n "error_kind|RECOVERABLE_ERROR_KINDS|WARMUP_RECOVERY_TIMEOUT" nyx/agent/loop/_iteration.py nyx/agent/loop/_core.py nyx/agent/loop/_constants.py
rg -n '"connection" in error_msg' nyx/agent/loop/_core.py   # deve casar ZERO linhas (substring removida)

# 3. PROOF RUNTIME-REAL sem GPU: ConnectError de verdade (porta morta).
#    Sem Ollama, sem proxy -- so o transporte httpx contra uma porta fechada.
#    _call_llm real devolve error_kind='connect' e o texto PT-BR intacto.
./venv/bin/python - <<'PY'
import asyncio, socket
from nyx.agent.loop._core import AgentLoop

# porta livre garantida (bind+close -> ninguem escutando nela)
s = socket.socket(); s.bind(("127.0.0.1", 0)); port = s.getsockname()[1]; s.close()

loop = AgentLoop(project_root=".", proxy_url=f"http://127.0.0.1:{port}")
loop._vram_checked = True  # pula VRAM guard (sem GPU nesta prova)
res = asyncio.run(loop._call_llm())

print("error     :", res.get("error"))
print("error_kind:", res.get("error_kind"))
assert res.get("error_kind") == "connect", res
assert "conexão recusada" in res.get("error", ""), res           # texto PT-BR intacto
from nyx.agent.loop._constants import RECOVERABLE_ERROR_KINDS
assert res["error_kind"] in RECOVERABLE_ERROR_KINDS, res          # AGORA dispara recovery
print("OK: ConnectError -> error_kind='connect' recuperavel; mensagem PT-BR intacta")
PY

# 4. PROOF de roteamento: mensagem PT-BR com error_kind recuperavel dispara _try_recovery.
#    Sem GPU: _call_llm e _try_recovery sao substituidos por stubs; provamos SO a decisao.
./venv/bin/python - <<'PY'
import asyncio
from nyx.agent.loop._core import AgentLoop

loop = AgentLoop(project_root=".", proxy_url="http://127.0.0.1:1")
loop._vram_checked = True

chamou = {"recovery": False}
async def fake_call_llm():
    # mensagem 100% PT-BR, SEM nenhum gatilho ingles do codigo antigo
    return {"error": "conexão recusada pelo proxy de inferencia.", "error_kind": "connect"}
async def fake_recovery():
    chamou["recovery"] = True
    return False  # recovery falha -> sessão encerra, mas a TENTATIVA prova o gatilho
loop._call_llm = fake_call_llm
loop._try_recovery = fake_recovery

status = asyncio.run(loop._run_iterations("oi"))
assert chamou["recovery"] is True, "recovery NÃO foi tentado -- gatilho ainda morto"
print("OK: error_kind='connect' com mensagem PT-BR disparou _try_recovery")
PY

# 5. Warmup por constante unica (achado BAIXA):
rg -n "timeout=WARMUP_RECOVERY_TIMEOUT" nyx/agent/loop/_iteration.py    # 1 match
python3 -c "from nyx.agent.loop._constants import WARMUP_RECOVERY_TIMEOUT as w; assert w == 300, w; print('OK warmup', w)"

# 6. Invariantes + smoke
bash scripts/sprint_invariants.sh          # esperado PASS 14/14 FAIL 0
./run.sh --smoke                           # esperado 'boot ok' exit 0

# 7. Gauntlet do proxy -- DEFERIDO para GPU exclusiva (protocolo anti-contencao do BRIEF)
./run.sh --gauntlet --only proxy
```

> Nota GPU: os passos 3-5 rodam SEM Ollama/GPU (transporte real contra porta morta / stubs). O passo 7 e o teste de recovery ponta-a-ponta (matar o Ollama de proposito e ver a sessão se recuperar) exigem GPU exclusiva -- executar so quando `pgrep -af "Luna.*driver|valida_sprint"` estiver vazio.

---

## Criterio binario de aceite (IA executora)

- [ ] `RECOVERABLE_ERROR_KINDS` e `WARMUP_RECOVERY_TIMEOUT` em `_constants.py` (fonte unica)
- [ ] Os 4 handlers de `_call_llm` anexam `error_kind` (timeout/connect/provider/decode|unknown); mensagem `error` byte-identica
- [ ] `_run_iterations` roteia por `error_kind in RECOVERABLE_ERROR_KINDS`; ZERO substring `"connection"`/`"disconnect"`/`"Extra data"`/`"500"` restante em `_core.py`
- [ ] warmup POST de `_try_recovery` usa `timeout=WARMUP_RECOVERY_TIMEOUT`; probe GET segue `timeout=30`
- [ ] Proof runtime-real colado (passo 3): ConnectError -> `error_kind='connect'`, texto PT-BR intacto
- [ ] Proof de roteamento colado (passo 4): mensagem PT-BR com `error_kind` recuperavel dispara `_try_recovery`
- [ ] `ruff` limpo, acentuacao rc=0, `FAIL_AFTER <= FAIL_BEFORE`, smoke boot ok
- [ ] Gauntlet `--only proxy` 100% (ou marcado DEFERIDO para GPU exclusiva no relato)
- [ ] `SPRINT_ORDER_MASTER.md` marca 420 CONCLUIDA; spec movida para `concluidos/`
- [ ] NÃO commitar; NÃO tocar Checkpoint.md; NÃO tocar `run.sh` (a 414 cuida do teto do boot)

---

## Guardrails anti-engodo (obrigatorios)

NÃO marcar concluida se:
- Manteve qualquer substring (`"connection"`/`"disconnect"`/`"Extra data"`/`"500"`) como sinal de recovery em `_core.py` (o nucleo do fix e PARAR de rotear por texto de usuário).
- Alterou o texto PT-BR de algum campo `"error"` (o campo novo e `error_kind`, ADITIVO; a mensagem ao usuário não muda).
- Removeu ou reordenou os handlers `TimeoutException`/`ConnectError`/`ProviderError`/`Exception`.
- Mudou o corpo do `if`/`else` do recovery em `_core.py` (420-457) alem da condicao.
- Deixou `error_kind` faltando em algum dos 4 handlers (um handler sem o campo vira erro não-recuperavel silencioso).
- não colou os proofs runtime-real (passos 3-4), ou algum assert falhou.
- Tocou `run.sh` (o teto de boot do Ollama e da 414 -- ver Fora de escopo).

Se algo falhar: `[SPRINT 420] BLOQUEADA: <motivo 1 linha>`.

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
Baseline esperado: `FAIL_BEFORE = 0`, `FAIL_AFTER <= 0`. Colar: inv_before/inv_after (tail), diff, os proofs runtime-real (passos 3-4), o `rg` das ancoras (passos 2 e 5), `git --no-pager diff --stat` e `./run.sh --smoke` (deve imprimir `boot ok`). O gauntlet `--only proxy` e o recovery ponta-a-ponta (matar o Ollama e ver a sessão se recuperar) ficam **DEFERIDOS para GPU exclusiva** — marcar no relato como as specs 403/407 fazem.

---

## Gambiarras especificas desta sprint

- **error_kind ausente = não-recuperavel:** `response.get("error_kind", "")` devolve `""`, que não esta no frozenset -> cai no `else` (encerra). Isso e o comportamento seguro por default: so kinds explicitamente marcados disparam recovery. Por isso todo handler de erro PRECISA anexar o campo.
- **JSONDecodeError e subclasse de ValueError:** `isinstance(e, json.JSONDecodeError)` classifica o caso proxy-500 (corpo text/plain) como `'decode'` (recuperavel: Ollama caiu atras do proxy, warmup ajuda). `json` ja esta importado (`_iteration.py:13`).
- **'http_error' reservado, não emitido aqui:** o frozenset ja inclui `'http_error'` para a 413 (checagem `status != 200`) marcar seus retornos e entrar coberta sem nova sprint. Esta sprint não cria esse retorno; so reserva o kind (forward-compat, sem acoplamento).
- **Probe vs warmup:** so o POST de warmup ganha o teto maior; o `AsyncClient(timeout=30)` e o `GET /v1/models` sao liveness e ficam em 30s (não inferem modelo).

---

## Validação humana (checklist do usuário)

```bash
cd /home/andrefarias/Desenvolvimento/Nyx-Code
git --no-pager show --stat HEAD

# Com GPU exclusiva: subir o stack real, mandar um prompt, matar o Ollama no meio
# (pkill ollama), e observar ~/.nyx/logs/nyx.log: deve aparecer
#   [loop] LLM caiu (connect), tentando recovery...
#   [recovery] Aguardando Ollama reiniciar...
# e a sessão deve retomar apos o warmup, em vez de encerrar em ERROR na hora.

ls dev-journey/06-sprints/concluidos/SPRINT_LOOP_RECOVERY_TRIGGER_PTBR_01.md  # existe
```

---

## Fora de escopo (anti-debito)

| Item | Decisao |
|------|---------|
| Teto de boot do Ollama em `run.sh` (`OLLAMA_START_TIMEOUT`) | **Da sprint 414** (`SPRINT_INFRA_OLLAMA_BOOT_TIMEOUT_DEFAULT_01`, producao/). Esta sprint NÃO toca `run.sh`. |
| `ProviderError` disparar recovery (`error_kind='provider'` fora do frozenset) | **Decisao consciente:** `ProviderError` cobre tanto 5xx transiente (recuperavel) quanto 4xx de request malformado (retry não resolve). Marcamos o kind mas o deixamos FORA do conjunto para não adivinhar semantica de provider nem regredir. Se o dono quiser recovery seletivo por status do provider, registrar `INFRA-PROVIDER-RECOVERY-SELECTIVE-01` (feedback_nenhum_debito), não absorver aqui. |
| Fix da 413 marcar seus retornos `status != 200` com `error_kind='http_error'` | Reservado no frozenset; a implementação do campo nesses retornos e da 413 quando ela executar. Sem acoplamento nesta sprint. |
| Warmup adaptativo (escalar teto por hardware) | Complexidade especulativa (GUIDE §2). 300s fixo + degradacao graciosa basta; alinhado a decisao da 414. |

---

## Referencias

- BRIEF: `/home/andrefarias/Desenvolvimento/Nyx-Code/VALIDATOR_BRIEF.md`
- Origem: auditoria de prontidão 2026-07-12, relatório durável `dev-journey/07-reports/AUDIT_2026_07_12.md` §3 (briefing efêmero da sessão de auditoria)
- Irma (transporte): `dev-journey/06-sprints/producao/SPRINT_EXEC_CONTRACT_PROXY_STATUS_BEFORE_JSON_01.md` (413), `SPRINT_INFRA_OLLAMA_BOOT_TIMEOUT_DEFAULT_01.md` (414)
- Desenho do contrato: `dev-journey/02-architecture/DESENHO_CONTRATO_EXECUCAO.md` (§6, "Honestidade na falha")
- Alma: ADR-032/033/034 (robustez pertence a infra, não ao modelo)

---

*"Recovery que so dispara em ingles não recupera nada numa maquina que fala portugues. Roteie por contrato, nunca por texto de usuário." -- principio de execução*
