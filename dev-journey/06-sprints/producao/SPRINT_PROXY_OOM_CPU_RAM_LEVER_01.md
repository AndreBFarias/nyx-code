## 0. SPEC (machine-readable)

```yaml
sprint:
  id: PROXY-OOM-CPU-RAM-LEVER-01
  numero: 432
  title: "Cascata OOM ganha alavanca de RAM (num_ctx) em CPU puro + erro final honesto em PT-BR"
  onda: 48
  prioridade: ALTA
  tipo: Bugfix
  dependencias: []
  desbloqueia: []
  absorve: []

  touches:
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/proxy.py
      reason: "adicionar _next_num_ctx_step (ladder RAM) e usa-lo em _post_chat_with_oom_recovery quando num_gpu==0 evita re-post identico; traduzir o erro OOM terminal para mensagem honesta PT-BR"
      linhas_alvo: "124-133 (helper _next_num_gpu_step, adicionar _next_num_ctx_step ao lado), 656-701 (bloco de fallback CPU do _post_chat_with_oom_recovery)"
  creates: []
  removes: []

  forbidden:
    - "Adicionar emoji"
    - "Usar 'print()' fora de cli.py/output.py"
    - "Mencao a ferramenta de IA proprietaria"
    - "Tocar o caminho GPU da cascata (passo intermediario num_gpu//2 e fallback CPU quando num_gpu>0) de forma que mude o comportamento observavel existente"
    - "Tocar _is_oom_error, _OOM_PATTERNS, _persist_stats, oom_recovery_count, a reanimacao GPU (_maybe_reanimate_gpu) ou o gating/guardrails de saida"
    - "Alterar o happy-path: HTTP 200 do Ollama segue byte-identico"
    - "Subir o num_ctx acima do NUM_CTX de boot (a alavanca so DEGRADA; ADR-032 num_ctx adaptativo para BAIXO)"
    - "Medir RAM no boot / mexer em detect_gpu.py, run.sh, install.sh (preventivo e sprint própria -- ver Fora de escopo)"

  tests:
    - cmd: "/home/andrefarias/.local/bin/ruff check nyx/proxy.py"
      deve_passar: true
    - cmd: "bash scripts/sprint_invariants.sh"
      deve_passar: true
    - cmd: "./run.sh --gauntlet --only proxy"
      timeout: 300
      deve_passar: true
      nota: "DEFERIDO para GPU exclusiva -- exige Ollama vivo"

  acceptance_criteria:
    - "Existe _next_num_ctx_step(current) que degrada o contexto (4096->2048->1024) e retorna 0 quando o próximo passo cairia abaixo do piso 1024 (fim da cadeia), espelhando o contrato de _next_num_gpu_step"
    - "Em _post_chat_with_oom_recovery, quando num_gpu==0 na entrada (maquina CPU pura) e o erro e OOM, o proxy não re-posta o request identico (num_gpu=0, num_ctx inalterado): entra direto na cadeia de degradacao de num_ctx via ollama_body['options']['num_ctx']"
    - "A cadeia num_ctx reposta com contexto reduzido; em HTTP 200 devolve a resposta (sucesso via RAM-lever) e incrementa oom_recovery_count via _persist_stats, como o fallback GPU ja faz; em erro não-OOM devolve o erro daquele passo; persistindo OOM ate esgotar o piso, aborta"
    - "Ao esgotar a cadeia com OOM, o proxy devolve mensagem HONESTA em PT-BR ('memoria RAM insuficiente para carregar o modelo; feche programas ou reduza o contexto'), não o texto cru em ingles do Ollama (ex.: 'model requires more system memory ...')"
    - "O caminho com num_gpu>0 (passo intermediario + fallback CPU) preserva o comportamento observavel atual; a cadeia num_ctx so entra depois que o fallback CPU tambem esgota OU quando a sessão ja entra em num_gpu==0"
    - "Proof runtime-real SEM GPU: fake ClientSession devolvendo OOM -> a cadeia degrada num_ctx e a mensagem final e PT-BR honesta, ZERO texto cru em ingles vazado; gauntlet proxy DEFERIDO"
    - "ruff limpo, acentuacao rc=0, invariantes FAIL_AFTER <= FAIL_BEFORE, smoke boot ok"
```

---

# Sprint PROXY-OOM-CPU-RAM-LEVER-01 — Cascata OOM ganha a alavanca de RAM em CPU puro

**Status:** PENDENTE
**Data criação:** 2026-07-12
**Modelo obrigatório:** claude-opus-4-7 (executor-sprint autorizado pelo dono nesta onda)

---

## Contexto do projeto (snapshot — não referência)

> **ADRs relevantes (inline):**
> - **ADR-032 (A INFRA CARREGA O MODELO NAS COSTAS):** quando o custo é de memória, as únicas alavancas legítimas são de infra — `num_ctx` / `num_gpu` adaptativos à memória livre real (ADR-032, linha 33-37). Toda sprint de memória declara qual alavanca usou (linha 60). Aqui a alavanca é `num_ctx` para BAIXO.
> - **ADR-033 (A CADEIA NUNCA QUEBRA NA MÃO DO USUÁRIO):** toda falha é absorvida e explicada; nunca um erro cru vaza para quem o produto promete proteger.
> - **ADR-034 (FEITO PARA QUEM NÃO TEM A100):** o usuário-alvo é leigo, com pouca RAM e sem GPU boa; a robustez pertence à infra, não ao modelo.
>
> **Estado (2026-07-12):** `qwen2.5-coder:3b`. ONDA-48. Ports: Ollama `11435`, proxy `11436`. `NUM_CTX` default = `4096` (`nyx/config/defaults.py:82`). A cascata OOM vive em `nyx/proxy.py::_post_chat_with_oom_recovery` (INFRA-OOM-RETRY-STEP-01 / INFRA-OOM-HISTORY-01). Origem do achado: auditoria de prontidão 2026-07-12 (`dev-journey/07-reports/AUDIT_2026_07_12.md`), verificada adversarialmente com evidência file:line.

---

## Problema

A cascata OOM do proxy só tem **alavanca de GPU**. Numa máquina **sem GPU** (`num_gpu=0`, o cenário-alvo do ADR-034) o OOM mais provável é de **RAM** — os 4 GB não seguram o 3b com o navegador e o ambiente gráfico abertos — e a infra hoje não faz nada útil a respeito.

**Evidência (verificada no código, linhas confirmadas em `nyx/proxy.py`):**

- **`_post_chat_with_oom_recovery` (627-701):** recebe `num_gpu` e monta a recuperação em cima dele.
- **Linha 656 `intermediate = _next_num_gpu_step(num_gpu)`:** com `num_gpu=0`, `_next_num_gpu_step` (124-133) retorna `0` (`current <= 1` → `0`). Logo `intermediate > 0` (658) é falso e o passo intermediário de GPU parcial é pulado — correto, não há GPU.
- **Linhas 686-688 (fallback CPU):** `state["num_gpu"] = 0` / `ollama_body["options"]["num_gpu"] = 0`. Numa máquina que já entrou em `num_gpu=0`, isto **re-posta o request idêntico** (mesmo `num_gpu=0`, mesmo `num_ctx=4096`). Em CPU lenta, isso apenas **dobra o tempo até a falha**.
- **Linhas 690-696:** persistindo a falha, `retry_text = await retry_resp.text()` e `return None, web.json_response({"error": {"message": retry_text, ...}})` — devolve o **texto cru do Ollama em inglês** (ex.: `model requires more system memory (X GiB) than is available`, que inclusive casa o pattern `'requires more memory'` de `_OOM_PATTERNS` na linha 108). O usuário leigo recebe um erro técnico em inglês.

**Confirmação da ausência de medição de RAM:** grep por `MemAvailable`, `free -m`, `virtual_memory`, `psutil`, `SwapTotal` em `run.sh`, `nyx/proxy.py`, `nyx/hw/detect_gpu.py`, `install.sh`, `scripts/nyx-runtime-limits.sh` → **zero hits**. Só VRAM é medida. A alavanca `num_ctx` (listada em ADR-032:37 como legítima) **existe no código mas nunca é usada como recuperação** — `NUM_CTX` é fixado no boot (`nyx/proxy.py:311, 1138`) e nunca degradado em runtime.

Isso fere **ADR-032** (a alavanca de infra disponível não é usada) e **ADR-033** (o erro cru vaza para a mão do usuário).

---

## Causa-raiz (verificada; divergências do briefing)

O briefing agrupa **três** correções. Após verificar no código, elas se dividem em **dois mecanismos distintos**:

1. **Reativo, na cascata OOM (mesmo mecanismo, mesma função `_post_chat_with_oom_recovery`, `nyx/proxy.py`):**
   - (a) degradar `num_ctx` como passo de recuperação quando `num_gpu==0` em vez de re-postar idêntico;
   - (b) traduzir o erro OOM terminal para PT-BR honesto.
   Estes dois são o núcleo desta sprint (ACs 1-4) — coesos, no mesmo arquivo e função.

2. **Preventivo, no boot (mecanismo diferente, arquivo diferente):**
   - (c) medir `MemAvailable` no boot e avisar/ajustar `num_ctx` preventivamente.
   Isto vive em `detect_gpu.py`/`run.sh`, tem ciclo de vida de boot (não de recuperação de request) e exige decidir schema de saída do `detect_gpu.py` + consumo no `run.sh`. **É sprint própria** (ver "Fora de escopo (anti-débito)"), para manter esta cirúrgica.

**Divergência de detalhe vs briefing:** o briefing descreve a re-postagem idêntica genericamente. No código, o passo intermediário de GPU (656-661) **já é corretamente pulado** quando `num_gpu=0`; a re-postagem idêntica ocorre especificamente no **fallback CPU (686-689)**, porque ele força `num_gpu=0` sobre uma sessão que já estava em `num_gpu=0`. O fix precisa mirar o fallback CPU, não o passo intermediário. Nenhuma outra divergência: linhas 656, 686-696 e a ausência de medição de RAM batem com o briefing.

---

## Solução proposta

Correções aditivas e cirúrgicas, todas em `nyx/proxy.py`, sem tocar o caminho GPU observável nem o happy-path.

1. **Novo helper `_next_num_ctx_step(current: int) -> int`** (ao lado de `_next_num_gpu_step`, ~124-133), espelhando o contrato: degrada o contexto pela metade com **piso `1024`**; retorna `0` (fim da cadeia) quando `current // 2 < 1024`. Ladder: `4096 → 2048 → 1024 → 0`.

2. **Alavanca de RAM no fallback do `_post_chat_with_oom_recovery`:** quando o erro é OOM e a sessão está em `num_gpu==0` (CPU pura — seja por entrar assim, seja após o fallback CPU do caminho GPU esgotar), em vez de re-postar idêntico, iterar a cadeia `num_ctx`: para cada `ctx = _next_num_ctx_step(atual)` enquanto `> 0`, setar `ollama_body["options"]["num_ctx"] = ctx` e re-postar. Em `200` → devolver a resposta, `state["oom_recovery_count"] += 1`, `_persist_stats(state)` (idêntico ao fallback GPU, linhas 697-701). Em erro **não-OOM** → devolver aquele erro. Persistindo OOM até esgotar → passo 3.

3. **Erro OOM terminal honesto (ADR-033):** ao esgotar a cadeia com OOM, `return None, web.json_response(...)` com mensagem PT-BR honesta — algo como *"Memória insuficiente para carregar o modelo nesta máquina. Feche outros programas (navegador, editor) e tente de novo; se persistir, reduza o contexto."* — em vez do `retry_text` cru. Só o caso **OOM esgotado** é traduzido; erros não-OOM seguem repassando o texto do Ollama (são outra classe de falha, fora do escopo).

**Preservação do caminho GPU:** quando `num_gpu>0`, o passo intermediário (656-668) e o fallback CPU inicial (682-701) seguem como hoje; a cadeia `num_ctx` entra apenas quando `num_gpu` já é/chegou a `0` e o OOM persiste. O comportamento observável do caminho GPU não muda.

---

## Arquivos alvo (paths absolutos)

### `/home/andrefarias/Desenvolvimento/Nyx-Code/nyx/proxy.py`

#### Edit 1 — helper `_next_num_ctx_step` (ao lado de `_next_num_gpu_step`, ~124-133)

Novo helper com o mesmo contrato defensivo do `_next_num_gpu_step`:

```python
_MIN_NUM_CTX = 1024  # piso da alavanca RAM (num_ctx); abaixo disso o modelo perde utilidade

def _next_num_ctx_step(current: int) -> int:
    """Próximo passo de degradação de num_ctx (alavanca RAM, ADR-032).

    Ladder esperada: 4096 -> 2048 -> 1024 -> 0. Retorna 0 (fim da cadeia)
    quando o próximo passo cairia abaixo do piso _MIN_NUM_CTX.
    """
    nxt = current // 2
    if nxt < _MIN_NUM_CTX:
        return 0
    return nxt
```

#### Edit 2 — alavanca RAM + erro honesto no fallback do `_post_chat_with_oom_recovery`

# Localização: bloco "2o retry: fallback CPU" (682-701). Após o re-post CPU
# (num_gpu=0), quando ele ainda retorna OOM — e, no caso `num_gpu==0` de entrada,
# ANTES de gastar o re-post idêntico — entrar na cadeia `num_ctx`. Ao esgotar a
# cadeia com OOM, devolver a mensagem honesta PT-BR em vez do `retry_text` cru.
# O executor deve implementar a iteração degradando `ollama_body["options"]["num_ctx"]`
# via `_next_num_ctx_step`, repostando em `session.post(f"{OLLAMA_URL}/api/chat", ...)`,
# devolvendo em 200 (com `oom_recovery_count += 1` e `_persist_stats(state)`),
# devolvendo o erro em falha não-OOM, e caindo na mensagem honesta ao esgotar.

Mensagem honesta terminal (substitui o `retry_text` cru quando a cadeia OOM esgota):

```python
return None, web.json_response(
    {
        "error": {
            "message": (
                "Memória insuficiente para carregar o modelo nesta máquina. "
                "Feche outros programas (navegador, editor) e tente de novo; "
                "se persistir, reduza o contexto."
            ),
            "type": "insufficient_memory",
        }
    },
    status=507,  # Insufficient Storage: honesto e distinto do 500 cru do upstream
)
```

> O executor decide o entrelaçamento exato do laço (helper interno vs inline) desde que: (i) o caminho `num_gpu>0` preserve o comportamento observável atual, (ii) o caso `num_gpu==0` não gaste o re-post idêntico antes da cadeia `num_ctx`, (iii) o sucesso via RAM-lever incremente `oom_recovery_count` e chame `_persist_stats` como o fallback GPU, (iv) só o OOM-esgotado seja traduzido.

---

## Diff esperado (resumo)

```
~ 1 arquivo modificado (nyx/proxy.py)
+ ~35 linhas líquidas (helper + laço num_ctx + mensagem honesta)
```

Sem aritmética de extração: esta sprint não tem meta `arquivo < NNNL` — é fix aditivo num único arquivo. `nyx/proxy.py` segue no mesmo patamar de tamanho (~1150L), sem extração planejada.

---

## Comandos de verificação (literais, copy-paste)

```bash
cd /home/andrefarias/Desenvolvimento/Nyx-Code

# 1. Estatica + acentuacao (ruff via binario direto -- sem modulo ruff no venv, ver BRIEF)
/home/andrefarias/.local/bin/ruff check nyx/proxy.py
python3 ~/.config/zsh/scripts/validar-acentuacao.py --paths nyx/proxy.py

# 2. Confirmar as ancoras (linhas podem ter deslizado -- reconferir):
rg -n "_next_num_gpu_step|_next_num_ctx_step|_MIN_NUM_CTX|num_ctx|insufficient_memory|Memoria insuficiente" nyx/proxy.py

# 3. PROOF RUNTIME-REAL sem GPU/Ollama: fake ClientSession devolvendo OOM em
#    todo POST. _post_chat_with_oom_recovery real -- so o transporte e faked.
#    Verifica: (a) num_ctx degradou (4096->2048->1024), (b) a resposta final e
#    a mensagem honesta PT-BR, (c) ZERO texto cru em ingles vazado.
./venv/bin/python - <<'PY'
import asyncio, json
import nyx.proxy as proxy

OOM = "model requires more system memory (5.2 GiB) than is available (3.8 GiB)"
ctx_seen = []

class FakeResp:
    status = 500
    async def json(self): return {}
    async def text(self): return OOM
    async def __aenter__(self): return self
    async def __aexit__(self, *a): return False

class FakeSession:
    def post(self, url, json=None):
        ctx_seen.append(json["options"]["num_ctx"])
        return FakeResp()

state = {"oom_degraded": False, "num_gpu": 0, "oom_recovery_count": 0}
body = {"options": {"num_gpu": 0, "num_ctx": 4096}, "messages": []}
# num_gpu=0 na entrada (maquina CPU pura)
data, err = asyncio.run(proxy._post_chat_with_oom_recovery(FakeSession(), body, state, 0))

resp_text = err.text if hasattr(err, "text") else ""
payload = json.loads(err.body.decode()) if getattr(err, "body", None) else {}
msg = payload.get("error", {}).get("message", "")
print("num_ctx tentados :", ctx_seen)
print("mensagem final   :", msg)
assert 2048 in ctx_seen or 1024 in ctx_seen, ctx_seen  # a alavanca RAM foi usada
assert "insuficiente" in msg.lower(), msg               # PT-BR honesto
assert "requires more system memory" not in msg, msg    # texto cru não vaza
print("OK: alavanca num_ctx acionada + erro honesto PT-BR, sem vazar ingles")
PY

# 4. Sucesso via RAM-lever: fake que devolve OOM em num_ctx=4096 e 200 em <=2048
#    -> a função deve retornar (data, None) e incrementar oom_recovery_count.
#    (mesma tecnica; trocar FakeResp.status por 200 quando json['options']['num_ctx'] <= 2048.)

# 5. Invariantes + smoke
bash scripts/sprint_invariants.sh
./run.sh --smoke   # deve imprimir 'boot ok'

# 6. Gauntlet do proxy -- DEFERIDO para GPU exclusiva (exige Ollama vivo):
# ./run.sh --gauntlet --only proxy
```

> **Nota GPU:** passos 3-4 rodam SEM Ollama/GPU (transporte faked) e são o proof runtime-real desta sprint. O passo 6 (gauntlet `--only proxy`) exige Ollama vivo e GPU exclusiva — **DEFERIDO**, executar só quando `pgrep -af "Luna.*driver|valida_sprint"` estiver vazio (protocolo anti-contenção do BRIEF), assim como as specs 403/407.

---

## Critério binário de aceite (IA executora)

- [ ] `_next_num_ctx_step(current)` existe, degrada 4096→2048→1024 e retorna 0 abaixo do piso 1024
- [ ] Em `num_gpu==0` + OOM, NÃO há re-post idêntico: a cadeia `num_ctx` é acionada via `ollama_body["options"]["num_ctx"]`
- [ ] Sucesso via RAM-lever devolve `(data, None)`, incrementa `oom_recovery_count` e chama `_persist_stats(state)`
- [ ] OOM esgotado devolve mensagem honesta PT-BR (`insufficient_memory`), ZERO texto cru em inglês
- [ ] Caminho `num_gpu>0` (intermediário + fallback CPU) preserva o comportamento observável atual
- [ ] Proof runtime-real colado (passos 3-4): `num_ctx` tentados + mensagem honesta, sem vazar inglês
- [ ] `ruff` limpo, acentuação rc=0, `FAIL_AFTER <= FAIL_BEFORE`, smoke boot ok
- [ ] Gauntlet `--only proxy`: DEFERIDO (marcar na conclusão quando a GPU liberar)
- [ ] NÃO commitar; NÃO tocar Checkpoint.md; NÃO tocar `detect_gpu.py`/`run.sh`/`install.sh`

---

## Guardrails anti-engodo (obrigatórios)

NÃO marcar concluída se:
- A cadeia `num_ctx` sobe o contexto acima do `NUM_CTX` de boot (a alavanca só DEGRADA; ADR-032).
- O caminho `num_gpu>0` mudou de comportamento observável (o passo intermediário e o fallback CPU inicial ficam intactos).
- O sucesso via RAM-lever não incrementa `oom_recovery_count` / não chama `_persist_stats` (quebra a paridade com o fallback GPU e o INFRA-OOM-HISTORY-01).
- A mensagem terminal ainda vaza o texto cru do Ollama em inglês, ou traduz erros NÃO-OOM (só o OOM esgotado é traduzido).
- Tocou `_is_oom_error`, `_OOM_PATTERNS`, a reanimação GPU, o gating ou os guardrails de saída.
- Mediu RAM no boot / tocou `detect_gpu.py`, `run.sh`, `install.sh` (é a sprint separada — ver Fora de escopo).
- Proof runtime-real (passos 3-4) não colado.

Se algo falhar: `[SPRINT 432] BLOQUEADA: <motivo 1 linha>`.

---

## Proof-of-work esperado (runtime-real, comandos do VALIDATOR_BRIEF)

```bash
bash scripts/sprint_invariants.sh > /tmp/inv_before.txt 2>&1
FAIL_BEFORE=$(grep -c "^\[FAIL\]" /tmp/inv_before.txt)
# implementar
bash scripts/sprint_invariants.sh > /tmp/inv_after.txt 2>&1
FAIL_AFTER=$(grep -c "^\[FAIL\]" /tmp/inv_after.txt)
diff /tmp/inv_before.txt /tmp/inv_after.txt
```

Baseline esperado: `FAIL_BEFORE = 0`, `FAIL_AFTER <= 0` (14/14 PASS, ver BRIEF [CORE]). Colar: inv_before/inv_after (tail), diff, output dos proofs runtime-real (passos 3-4), o `rg` do passo 2, `git --no-pager diff --stat`, `./run.sh --smoke` (deve imprimir `boot ok`). Gauntlet `--only proxy`: **DEFERIDO para GPU exclusiva** (registrar como pendência de validação, precedente specs 403/407).

---

## Gambiarras específicas desta sprint

- **Piso `num_ctx=1024`:** abaixo disso o 3b perde utilidade prática; `1024` é o floor. Note que `num_predict` de intents `tool`/`tool-needed` é `2048` (`nyx/config/defaults.py:111-112`) — com `num_ctx=1024` o output fica apertado, mas é o último recurso antes de abortar honestamente; preferível a um erro cru.
- **`state["num_gpu"]` no caso CPU puro:** a sessão já está degradada em CPU; a cadeia `num_ctx` NÃO mexe em `num_gpu` (só em `num_ctx`) — as duas alavancas são ortogonais e não devem interferir na reanimação GPU (`_maybe_reanimate_gpu`).
- **HTTP 507 vs 500:** a mensagem honesta usa `status=507` (Insufficient Storage) para distinguir do `500` cru do upstream; o cliente (`_iteration.py`) já trata `status_code != 200` como erro (satélite 413), então o 507 é absorvido honestamente rio abaixo.
- **`_persist_stats` no sucesso RAM-lever:** reusar exatamente o par `oom_recovery_count += 1` + `_persist_stats(state)` do fallback GPU (697-701) mantém a contabilidade do INFRA-OOM-HISTORY-01 coerente — recuperação via RAM conta como recuperação.

---

## Fora de escopo (anti-débito)

| Item | Decisão |
|------|---------|
| **Medir `MemAvailable` no boot e ajustar/avisar `num_ctx` preventivamente** (fix (c) do briefing) | **SPRINT PRÓPRIA.** Mecanismo diferente (preventivo, boot-time), arquivo diferente (`detect_gpu.py`/`run.sh`), exige decidir schema de saída do `detect_gpu.py` e consumo no `run.sh`. Registrar `INFRA-RAM-PREFLIGHT-01` (anti-débito: `feedback_nenhum_debito`). Complementar a esta: preventivo no boot vs reativo na cascata. |
| Middleware de erro no `aiohttp` do proxy (JSON estruturado em vez do 500 cru default) | Fora de escopo — coberto do lado cliente pelo satélite 413; se o dono quiser o proxy estruturado, `INFRA-PROXY-STRUCTURED-503-01`. |
| Traduzir os erros NÃO-OOM (API errors do Ollama) para PT-BR | Fora de escopo — só o OOM esgotado é traduzido aqui; erros de outra classe são outra sprint. |

---

## Referências

- BRIEF: `/home/andrefarias/Desenvolvimento/Nyx-Code/VALIDATOR_BRIEF.md`
- Auditoria origem: `dev-journey/07-reports/AUDIT_2026_07_12.md`
- ADR-032: `dev-journey/03-decisions/ADR_032_INFRA_CARREGA_MODELO.md` (num_ctx como alavanca legítima)
- ADR-033: `dev-journey/03-decisions/ADR_033_CADEIA_NUNCA_QUEBRA.md`
- ADR-034: `dev-journey/03-decisions/ADR_034_FEITO_PARA_QUEM_NAO_TEM_A100.md`
- Precedente de estrutura + DEFER de GPU: `dev-journey/06-sprints/producao/SPRINT_EXEC_CONTRACT_PROXY_STATUS_BEFORE_JSON_01.md` (413)
- Cascata OOM atual: `nyx/proxy.py::_post_chat_with_oom_recovery` (627-701), `_next_num_gpu_step` (124-133)

---

*"Numa máquina sem GPU, a única alavanca que sobrou era repetir o mesmo erro em inglês. A infra tinha o num_ctx na mão o tempo todo -- ADR-032." -- achado da auditoria 2026-07-12*
