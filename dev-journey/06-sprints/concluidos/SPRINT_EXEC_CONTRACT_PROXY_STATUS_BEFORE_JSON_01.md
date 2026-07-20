## 0. SPEC (machine-readable)

```yaml
sprint:
  id: EXEC-CONTRACT-PROXY-STATUS-BEFORE-JSON-01
  numero: 413
  title: "Satelite: checar status_code do proxy ANTES de r.json() -- falha honesta quando o Ollama cai"
  onda: 48
  prioridade: MEDIA
  tipo: Bugfix
  dependencias: []
  desbloqueia: []
  absorve: [412]

  touches:
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/agent/loop/_iteration.py
      reason: "checar r.status_code != 200 antes de r.json() no _call_llm; blindar o r.json() contra corpo não-JSON; logger.exception no handler generico para a promessa de traceback deixar de ser vazia"
      linhas_alvo: "906-914 (bloco do POST + r.json()), 988-993 (handler except Exception generico)"
  creates: []
  removes: []

  forbidden:
    - "Adicionar emoji"
    - "Usar 'print()' fora de cli.py/output.py"
    - "Mencao a IA proprietaria"
    - "Tocar a cascata OOM do proxy (_post_chat_with_oom_recovery), gating, write_memory"
    - "Tocar os guards do contrato (397/398/399/400/401)"
    - "Alterar o happy-path: HTTP 200 com JSON valido segue byte-identico"
    - "Remover ou reordenar os handlers existentes (TimeoutException/ConnectError/ProviderError) -- a checagem nova e ADITIVA"

  tests:
    - cmd: "/home/andrefarias/.local/bin/ruff check nyx/agent/loop/_iteration.py"
      deve_passar: true
    - cmd: "bash scripts/sprint_invariants.sh"
      deve_passar: true
    - cmd: "./run.sh --gauntlet --only proxy"
      timeout: 300
      deve_passar: true

  acceptance_criteria:
    - "_call_llm checa r.status_code != 200 ANTES de r.json(); em HTTP != 200 devolve erro honesto citando o code + 'o Ollama pode estar fora (ss -ltnp | grep 11435)', SEM chamar r.json()"
    - "r.json() protegido por try/except json.JSONDecodeError: HTTP 200 com corpo não-JSON devolve erro honesto ('proxy respondeu 200 mas o corpo não e JSON, ver proxy.log'), não o 'Falha inesperada' generico"
    - "handler except Exception generico (988-993) chama logger.exception ANTES do return -- a promessa 'Abra ~/.nyx/logs/nyx.log para o traceback completo' deixa de ser vazia (honestidade na falha, DESENHO §6)"
    - "Proof runtime-real SEM stack completo: servidor HTTP local devolvendo HTTP 500 text/plain -> _call_llm devolve 'HTTP 500 ... 11435', ZERO 'JSONDecodeError' mascarado"
    - "Absorve 412: o sintoma COL-401-A (JSONDecodeError ao contatar o proxy) fica coberto -- a causa era proxy-500/connection-refused, não tool_call malformado"
    - "ruff limpo, acentuação rc=0, invariantes FAIL_AFTER <= FAIL_BEFORE, smoke boot ok"
```

---

# Sprint EXEC-CONTRACT-PROXY-STATUS-BEFORE-JSON-01 — Satelite: falha honesta quando o proxy devolve HTTP de erro

**Status:** PENDENTE
**Data criação:** 2026-07-12
**Modelo obrigatório:** claude-opus-4-7 (executor-sprint autorizado pelo dono nesta onda)

---

## Contexto do projeto (snapshot — não referência)

> **ADRs relevantes (inline):**
> - **ADR-032/033 A INFRA CARREGA O MODELO / ENFORCEMENT, NÃO CONFIANÇA:** quando a infra não consegue garantir, a mensagem ao usuário e clara ("não consegui X porque Y"), nunca um erro cru mascarado nem uma promessa vazia.
> - ADR-009, ADR-001, ADR-006.
>
> **Estado (2026-07-12):** `qwen2.5-coder:3b`. ONDA-48 fase raiz: núcleo do contrato (399/397/400/398/401) CONCLUIDO e commitado. Este e satélite de robustez do transporte (achado da validação holística), independente do núcleo. Desenho: `dev-journey/02-architecture/DESENHO_CONTRATO_EXECUCAO.md` (§6, "Honestidade na falha"). Origem do achado: validação holística 2026-06-26 (session2, Ollama morto por contenção de GPU). Ports: Ollama `11435`, proxy `11436` (`nyx/config/defaults.py:45-53`).

---

## Problema

**Achado (validação holística 2026-06-26, absorve COL-401-A / sprint 412):** quando o Ollama cai (por contenção de GPU, OOM ou boot que não subiu), o proxy propaga um `ClientConnectorError` do upstream. Como `nyx/proxy.py` monta `web.Application()` SEM middleware de erro (verificado: nenhum `middlewares=` no arquivo), o aiohttp devolve o default **HTTP 500 com corpo `text/plain`** (`500 Internal Server Error\n\nServer got itself in trouble`), não JSON.

**Causa-raiz (verificada no código):** `nyx/agent/loop/_iteration.py`, método `_call_llm` (linha 814):

- linha 910-913: `r = await self._http_client.post(...)` — o httpx 0.28.1 **não levanta** em 4xx/5xx sem `raise_for_status()`, então o POST retorna normalmente com o 500;
- **linha 914: `data = r.json()` roda ANTES de qualquer checagem de `r.status_code`** — parsear o corpo `text/plain` do 500 estoura `json.JSONDecodeError`;
- o `JSONDecodeError` não e `httpx.TimeoutException` (971), não e `httpx.ConnectError` (977 — não dispara porque a conexão ao PROXY teve sucesso; quem caiu foi o Ollama atras dele), não e `ProviderError` (983), então cai no `except Exception` generico (linha 988-993);
- esse handler devolve `"Falha inesperada ao contatar o proxy: JSONDecodeError. Abra ~/.nyx/logs/nyx.log para o traceback completo."` — mas **não ha nenhum `logger.exception` em `_call_llm`** (confirmado: o único `logger` do bloco de erro e o `logger.warning` do on_thinking, linha 938). **O traceback prometido nunca e escrito.** A causa real (Ollama fora) fica mascarada por um "erro inesperado" e uma promessa vazia.

Isso fere o princípio **"Honestidade na falha"** (`DESENHO_CONTRATO_EXECUCAO.md` §6, linha 131-132): "Se a infra não consegue garantir, a mensagem ao usuário e clara ('não consegui X porque Y') -- nunca um sucesso fabricado nem um formato interno cru." <!-- noqa-acento -->

---

## Solução proposta

Três correções aditivas e cirúrgicas, todas dentro de `_call_llm`, sem tocar os handlers existentes nem o happy-path:

1. **Checar `r.status_code != 200` ANTES de `r.json()`** — em HTTP de erro, devolver mensagem honesta citando o code e apontando o Ollama (`ss -ltnp | grep 11435`), sem tentar decodificar JSON de um corpo que quase sempre não e JSON.
2. **Blindar `r.json()`** com `try/except json.JSONDecodeError` — cobre o caso raro de HTTP 200 com corpo corrompido/não-JSON; devolve erro honesto apontando `proxy.log`, não o "inesperado".
3. **`logger.exception` no handler generico (988-993)** — torna a promessa "Abra ~/.nyx/logs/nyx.log" verdadeira: o traceback de fato aterrissa no log. A mensagem ao usuário e mantida (agora honesta).

Com (1) em vigor, o caso proxy-500/Ollama-fora e capturado pela checagem de status e nunca mais chega ao handler generico como JSONDecodeError. (2) e (3) endurecem os flancos restantes.

---

## Arquivos alvo (paths absolutos)

### `/home/andrefarias/Desenvolvimento/Nyx-Code/nyx/agent/loop/_iteration.py`

#### Edit 1 — checar status e blindar o decode ANTES de `r.json()`

# Localização: dentro do `try:` de `_call_llm`, logo após o POST (linha 910-914)
**Antes:**
```python
            r = await self._http_client.post(
                f"{self._proxy_url}/v1/chat/completions",
                json=payload,
            )
            data = r.json()
```
**Depois:**
```python
            r = await self._http_client.post(
                f"{self._proxy_url}/v1/chat/completions",
                json=payload,
            )
            # EXEC-CONTRACT-PROXY-STATUS-BEFORE-JSON-01 (absorve 412): checar o
            # status ANTES de r.json(). Quando o Ollama cai, o proxy propaga
            # ClientConnectorError e o aiohttp (sem middleware) devolve HTTP 500
            # com corpo text/plain -- r.json() estourava JSONDecodeError e
            # mascarava a causa real (Ollama fora) num "erro inesperado" que
            # ainda prometia um traceback nunca escrito. Falha honesta: cita o
            # code e aponta o Ollama (11435). DESENHO §6.
            if r.status_code != 200:
                logger.error("[loop] proxy HTTP %d: %s", r.status_code, r.text[:200])
                return {
                    "error": (
                        f"O proxy de inferência retornou HTTP {r.status_code}. "
                        "O Ollama pode estar fora -- confira com "
                        "'ss -ltnp | grep 11435' e reinicie o stack com ./run.sh."
                    ),
                    "error_detail": f"HTTP {r.status_code}: {r.text[:200]}",
                }

            try:
                data = r.json()
            except json.JSONDecodeError as exc:
                logger.error(
                    "[loop] corpo do proxy não e JSON (HTTP %d): %s",
                    r.status_code,
                    r.text[:200],
                )
                return {
                    "error": (
                        "O proxy respondeu HTTP 200 mas o corpo não e JSON. "
                        "Inspecione ~/.nyx/logs/proxy.log."
                    ),
                    "error_detail": f"{type(exc).__name__}: {r.text[:200]}",
                }
```

#### Edit 2 — `logger.exception` no handler generico (a promessa deixa de ser vazia)

# Localização: o `except Exception as e:` no fim de `_call_llm` (linha 988-993)
**Antes:**
```python
        except Exception as e:
            return {
                "error": f"Falha inesperada ao contatar o proxy: {type(e).__name__}. "
                "Abra ~/.nyx/logs/nyx.log para o traceback completo.",
                "error_detail": f"{type(e).__name__}: {e}",
            }
```
**Depois:**
```python
        except Exception as e:
            # EXEC-CONTRACT-PROXY-STATUS-BEFORE-JSON-01: a mensagem prometia o
            # traceback em nyx.log, mas NADA o logava -- promessa vazia (fere
            # "honestidade na falha", DESENHO §6). logger.exception torna a
            # promessa verdadeira: o traceback de fato aterrissa no log.
            logger.exception("[loop] falha inesperada ao contatar o proxy")
            return {
                "error": f"Falha inesperada ao contatar o proxy: {type(e).__name__}. "
                "Abra ~/.nyx/logs/nyx.log para o traceback completo.",
                "error_detail": f"{type(e).__name__}: {e}",
            }
```

---

## Diff esperado (resumo)

```
~ 1 arquivo modificado (nyx/agent/loop/_iteration.py)
+ ~25 linhas líquidas (sem meta numérica de tamanho -- fix aditivo, arquivo segue < 1200L)
```

Sem aritmética de extração: esta sprint não tem meta `arquivo < NNNL`. O único número relevante e o net-add (~25L) num único arquivo.

---

## Comandos de verificação (literais, copy-paste)

```bash
cd /home/andrefarias/Desenvolvimento/Nyx-Code

# 1. Estatica + acentuacao (ruff via binario direto -- não ha modulo ruff no venv, ver BRIEF)
/home/andrefarias/.local/bin/ruff check nyx/agent/loop/_iteration.py
python3 ~/.config/zsh/scripts/validar-acentuacao.py --paths nyx/agent/loop/_iteration.py

# 2. Confirmar a hipotese das ancoras (linhas podem ter deslizado -- reconferir):
rg -n "r.status_code|r.json\(\)|logger.exception|traceback completo" nyx/agent/loop/_iteration.py

# 3. PROOF RUNTIME-REAL sem stack completo (regra: NÃO subir Ollama/GPU).
#    Um http.server stdlib devolve HTTP 500 text/plain (identico ao que o
#    aiohttp sem middleware devolve quando o Ollama cai). AgentLoop real,
#    _call_llm real -- só o transporte e faked. _vram_checked=True pula o
#    guard de VRAM (sem GPU nesta prova).
./venv/bin/python - <<'PY'
import asyncio, threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from nyx.agent.loop._core import AgentLoop

class H(BaseHTTPRequestHandler):
    def do_POST(self):
        body = b"500 Internal Server Error\n\nServer got itself in trouble"
        self.send_response(500)
        self.send_header("Content-Type", "text/plain")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)
    def log_message(self, *a):  # silencio
        pass

srv = HTTPServer(("127.0.0.1", 0), H)
port = srv.server_address[1]
threading.Thread(target=srv.serve_forever, daemon=True).start()

loop = AgentLoop(project_root=".", proxy_url=f"http://127.0.0.1:{port}")
loop._vram_checked = True  # pula VRAM guard (sem GPU nesta prova)
res = asyncio.run(loop._call_llm())
srv.shutdown()

print("error   :", res.get("error"))
print("detail  :", res.get("error_detail"))
assert "HTTP 500" in res.get("error", ""), res
assert "11435" in res.get("error", ""), res
assert "JSONDecodeError" not in res.get("error", ""), res
print("OK: HTTP 500 honesto (cita 11435), SEM JSONDecodeError mascarado")
PY

# 4. Variante: HTTP 200 com corpo não-JSON -> mensagem honesta de proxy.log
#    (mesma tecnica, trocar send_response(500) por 200 e assertar
#    "não e JSON" no error, sem "Falha inesperada").

# 5. Confirmar que a promessa deixou de ser vazia (logger.exception presente):
rg -n "logger.exception\(\"\[loop\] falha inesperada" nyx/agent/loop/_iteration.py

# 6. Gauntlet do proxy (mais estavel isolado que o rapido, ver BRIEF flake nota)
./run.sh --gauntlet --only proxy
```

> Nota GPU: os passos 3-4 rodam SEM Ollama/GPU (transporte faked). O passo 6 (gauntlet) exige GPU exclusiva -- executar só quando `pgrep -af "Luna.*driver|valida_sprint"` estiver vazio (protocolo anti-contenção do BRIEF).

---

## Critério binário de aceite (IA executora)

- [ ] Checagem `r.status_code != 200` ANTES de `r.json()`, com mensagem honesta citando o code + `ss -ltnp | grep 11435`
- [ ] `r.json()` protegido por `try/except json.JSONDecodeError` com mensagem honesta apontando `proxy.log`
- [ ] `logger.exception` adicionado ao handler `except Exception` (988-993) -- a promessa de traceback deixa de ser vazia
- [ ] Proof runtime-real colado (passo 3): HTTP 500 -> "HTTP 500 ... 11435", ZERO `JSONDecodeError` no `error`
- [ ] Handlers existentes (Timeout/ConnectError/ProviderError) e happy-path intactos
- [ ] `ruff` limpo, acentuação rc=0, `FAIL_AFTER <= FAIL_BEFORE`, smoke boot ok
- [ ] Gauntlet `--only proxy` 100%
- [ ] `SPRINT_ORDER_MASTER.md` marca 413 CONCLUIDA (e 412 segue ABSORVIDA_POR 413); spec movida para `concluidos/`
- [ ] NÃO commitar; NÃO tocar Checkpoint.md; NÃO tocar `nyx/proxy.py`

---

## Guardrails anti-engodo (obrigatórios)

NÃO marcar concluída se:
- A checagem de status ficou DEPOIS do `r.json()` (a ordem e o núcleo do fix -- status ANTES).
- O happy-path mudou (HTTP 200 + JSON valido deve seguir byte-identico: `data = r.json()` -> `"choices"`).
- Algum handler existente (`TimeoutException`/`ConnectError`/`ProviderError`) foi removido, reordenado ou teve a mensagem alterada.
- Adicionou o `logger.exception` mas manteve o texto prometendo um traceback que ainda não e escrito (a alternativa valida seria REMOVER a promessa; a escolhida e LOGAR de fato).
- Proof runtime-real não colado, ou o `error` retornado ainda contem `JSONDecodeError`.
- Tocou `nyx/proxy.py` (o hardening do lado do proxy e não-objetivo desta sprint -- ver Riscos).

Se algo falhar: `[SPRINT 413] BLOQUEADA: <motivo 1 linha>`.

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
Baseline esperado: `FAIL_BEFORE = 0`, `FAIL_AFTER <= 0`. Colar: inv_before/inv_after (tail), diff, o output do proof runtime-real (passos 3-4), o `rg` do passo 5, `git --no-pager diff --stat` e `./run.sh --smoke` (deve imprimir `boot ok`).

---

## Gambiarras específicas desta sprint

- **`r.text` após 500:** o httpx bufferiza o corpo por default (não-streaming), então `r.text` esta disponivel logo após o POST -- capar em `[:200]` evita despejar um HTML/stacktrace inteiro no `error_detail`.
- **JSONDecodeError vs ValueError:** o `json` do stdlib levanta `json.JSONDecodeError` (subclasse de `ValueError`); o `r.json()` do httpx repassa esse tipo -- capturar `json.JSONDecodeError` (já importado, linha 13) e suficiente e preciso.
- **ConnectError não cobre este caso:** o `except httpx.ConnectError` (977) só dispara quando o PROXY (11436) esta fora; aqui o proxy responde (500) e quem caiu e o Ollama (11435) atras dele -- por isso a checagem de status e necessaria, não basta o handler de conexão.
- **logger.exception fora de except e erro:** o `logger.exception` só faz sentido dentro do `except` (usa o traceback ativo) -- manter exatamente no handler generico, não no fluxo normal.

---

## Validação humana (checklist do usuário)

```bash
cd /home/andrefarias/Desenvolvimento/Nyx-Code
git --no-pager show --stat HEAD

# Simular Ollama fora com o stack real e mandar um prompt: a Nyx deve dizer
# claramente "o proxy retornou HTTP 500, o Ollama pode estar fora
# (ss -ltnp | grep 11435)" -- não "Falha inesperada / JSONDecodeError".
# (executar só com GPU exclusiva; parar o ollama de proposito p/ o teste manual.)

ls dev-journey/06-sprints/concluidos/SPRINT_EXEC_CONTRACT_PROXY_STATUS_BEFORE_JSON_01.md  # existe
```

---

## Riscos e não-objetivos

| Risco / não-objetivo | Decisão |
|-------|-----------|
| Hardening do lado do proxy (aiohttp middleware que capture `ClientConnectorError` e devolva JSON 503 estruturado) | **NÃO-OBJETIVO desta sprint.** O fix e client-side em `_iteration.py`. Se o dono quiser o proxy devolvendo erro estruturado, registrar sprint nova `INFRA-PROXY-STRUCTURED-503-01` (anti-débito: `feedback_nenhum_debito`), não absorver aqui. |
| Mudar o texto/idioma das mensagens dos handlers existentes | Fora de escopo -- só o handler generico ganha `logger.exception`; os demais ficam intactos. |
| Corpo não-JSON com HTTP 200 (raro) | Coberto pelo `except json.JSONDecodeError` do Edit 1. |
| `r.text` grande (HTML de erro) polui o log | Capado em `[:200]` no `logger.error` e no `error_detail`. |

---

## Referências

- BRIEF: `/home/andrefarias/Desenvolvimento/Nyx-Code/VALIDATOR_BRIEF.md`
- Desenho do contrato: `dev-journey/02-architecture/DESENHO_CONTRATO_EXECUCAO.md` (§6, "Honestidade na falha")
- Achado + tabela: `dev-journey/06-sprints/SPRINT_ORDER_MASTER.md` (bloco ONDA-48, linha 413; 412 ABSORVIDA_POR 413)
- Origem: validação holística 2026-06-26 (session2, Ollama morto por contenção de GPU)

---

*"Um erro honesto vale mais que um sucesso fabricado; uma promessa de traceback sem o traceback e a pior das duas coisas." -- princípio de execução (dev-journey/02-architecture/DESENHO_CONTRATO_EXECUCAO.md §6)*
