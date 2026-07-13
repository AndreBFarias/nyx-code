## 0. SPEC (machine-readable)

```yaml
sprint:
  id: INFRA-PROXY-READINESS-RETRY-01
  numero_master: 431
  title: "run.sh + gauntlet: readiness do proxy e single-shot (sleep 2s + curl único); maquina lenta aborta o boot por raca de infra"
  onda: 48
  prioridade: ALTA
  tipo: Infra/Boot
  dependencias: []
  desbloqueia: []

  touches:
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/run.sh
      reason: "readiness do proxy (724-731) e do cockpit (744-746) sao sleep fixo + curl único -- trocar por loop de poll espelhando start_ollama (426-435); adicionar teto PROXY_START_TIMEOUT com override NYX_PROXY_START_TIMEOUT no bloco de timeouts (120-123)"
      linhas_alvo: "120-123 (bloco TIMEOUTS), 724-731 (readiness proxy), 744-746 (readiness cockpit)"
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/scripts/gauntlet/nyx_gauntlet.py
      reason: "gate de fase (427-429) reprova em 1 tentativa de _health (5000-5006) -- dar retry com backoff antes de registrar HEALTH FAIL, para gauntlets consecutivos não reprovarem por raca de VRAM/orfao"
      linhas_alvo: "427-429 (gate de fase), 5000-5006 (_health)"
  creates: []
  removes: []

  forbidden:
    - "Adicionar emoji"
    - "Mencao a ferramenta de IA"
    - "Usar 'print()' fora de cli.py/output.py"
    - "Alterar a semantica do happy-path: boot saudavel sai assim que /v1/models responde (poll de 1s), o teto so dispara em falha real"
    - "Tocar a semantica de reaping/pkill de kill_existing_ollama (407-408) ou stop_ollama (456-459) -- reaping de orfao e escopo separado (ver Fora de escopo)"
    - "Tocar a cascata OOM do proxy, gating, warmup_model ou WARMUP_TIMEOUT"
    - "Renomear NYX_OLLAMA_START_TIMEOUT nem alterar OLLAMA_START_TIMEOUT (linha 122)"
    - "Mudar o endpoint checado (proxy: /v1/models; cockpit: /health) nem as portas (11436/11437)"

  tests:
    - cmd: "bash -n run.sh"
      timeout: 30
      deve_passar: true
    - cmd: "/home/andrefarias/.local/bin/ruff check scripts/gauntlet/nyx_gauntlet.py"
      deve_passar: true
    - cmd: "./run.sh --smoke"
      timeout: 120
      deve_passar: true
    - cmd: "bash scripts/sprint_invariants.sh"
      deve_passar: true

  acceptance_criteria:
    - "run.sh: readiness do proxy (724-731) vira loop de poll de curl -sf .../v1/models a cada 1s, saindo ao primeiro OK; teto PROXY_START_TIMEOUT (default 30s, override NYX_PROXY_START_TIMEOUT) so aborta em falha real; mensagem de erro aponta a env de override"
    - "run.sh: readiness do cockpit (744-746) recebe o mesmo loop de poll de /health (mesmo mecanismo, mesmo teto), no lugar do sleep 2 + curl único"
    - "run.sh: novo PROXY_START_TIMEOUT definido no bloco TIMEOUTS (120-123), espelhando OLLAMA_START_TIMEOUT; nome da env de override e NYX_PROXY_START_TIMEOUT"
    - "nyx_gauntlet.py: o gate de fase (427-429) da retry ao _health (ate 3 tentativas com backoff exponencial) antes de registrar HEALTH FAIL; happy-path (Ollama up na 1a) inalterado; FAIL so apos as tentativas esgotarem"
    - "Happy-path preservado: boot saudavel do proxy/cockpit sai em 1-3s; gauntlet com Ollama up passa na 1a tentativa sem atraso perceptivel"
    - "bash -n run.sh sem erro; ruff limpo no gauntlet; ./run.sh --smoke imprime boot ok exit 0; invariantes 14/14; acentuacao rc=0; zero emoji; zero mencao a IA"
```

---

# Sprint INFRA-PROXY-READINESS-RETRY-01 — readiness do proxy/cockpit e do gate do gauntlet com poll de retry

**Status:** PENDENTE
**Data criação:** 2026-07-12
**Origem:** auditoria de prontidão ONDA-48 (2026-07-12), achados verificados adversarialmente com evidência file:line. Evidência de campo: células 398 e 401 do `SPRINT_ORDER_MASTER.md` ("1 flaky de boot -- proxy health-check race após 2 gauntlets seguidos + ollama órfão"; "ollama respondeu /api/version às :07 e o health do gauntlet falhou às :10").

---

## Contexto do projeto (snapshot — não referência)

> **ADRs relevantes (inline):**
> - **ADR-034 (Feito para quem não tem A100):** o sucesso se mede no pior hardware razoável com o desktop cheio. HD lento, RAM curta e VRAM disputada são o cenário-alvo, não a exceção.
> - **ADR-032/033 (a infra carrega o modelo / enforcement, não confiança):** robustez de boot pertence à INFRA, não ao modelo. Uma máquina fraca que ainda está acordando não pode ser reprovada por um teto mais curto que o bocejo dela.
> - **ADR-007 (gate 100%-obrigatório):** o gauntlet é gate duro; se ele reprova por raça de infraestrutura em vez de regressão, corrói a confiança no vermelho — exatamente a confiança que salvaria o usuário-alvo leigo.
>
> **Estado (2026-07-12):** `qwen2.5-coder:3b`. ONDA-48, núcleo do contrato (399/397/400/398/401) concluído. Achados de infra/boot desta onda: 414 (`INFRA-OLLAMA-BOOT-TIMEOUT-DEFAULT-01`, eleva teto do Ollama para 60s) e esta 431. Ports: Ollama `11435`, proxy `11436`, cockpit `11437`.

---

## Problema

O `run.sh` sobe o Ollama, depois o proxy, depois (opcional) o cockpit. Para o **Ollama** o readiness é um loop de poll robusto (`run.sh:426-435`): `curl -sf /api/version` a cada 1s até responder, com teto `OLLAMA_START_TIMEOUT`. Para o **proxy** e o **cockpit**, porém, o readiness é um `sleep` fixo de 2s seguido de **um único** `curl` — sem loop, sem retry.

**Achado A — readiness do proxy é single-shot (`run.sh:724-731`, severidade ALTA):**

```bash
disown "$PROXY_PID" 2>/dev/null || true
sleep 2

if curl -sf "http://127.0.0.1:${NYX_PROXY_PORT}/v1/models" > /dev/null 2>&1; then
    log_boot "Proxy pronto (PID: $PROXY_PID)"
else
    log_err "Proxy não iniciou. Verifique logs/proxy.log"
    exit 1
fi
```

Na pior máquina (cenário ADR-034), o Python do venv importando `aiohttp` a frio de um HD lento facilmente passa de 2s para abrir o bind da porta 11436. Resultado: o boot inteiro aborta com mensagem genérica, sendo que o proxy subiria 1-3s depois. É exatamente a máquina-alvo do produto que sofre o falso negativo.

**Achado B — readiness do cockpit é o mesmo padrão frágil (`run.sh:744-746`):**

```bash
disown "$COCKPIT_PID" 2>/dev/null || true
sleep 2
if curl -sf http://127.0.0.1:11437/health > /dev/null 2>&1; then
    log_boot "Cockpit pronto (PID: $COCKPIT_PID)"
```

Mesmo `sleep 2` fixo + `curl` único. Mesmo mecanismo, mesma fragilidade.

**Achado C — gate de fase do gauntlet reprova em 1 tentativa (`scripts/gauntlet/nyx_gauntlet.py:427-429` + `_health` em `:5000-5006`, severidade ALTA):**

```python
for phase in self._phases:
    if phase in NEEDS_OLLAMA and not await self._health():
        self._add("HEALTH", f"Ollama antes de {phase}", phase, False, 0, error="Ollama não responde")
        continue
```

```python
async def _health(self) -> bool:
    try:
        async with httpx.AsyncClient(timeout=5) as c:
            r = await c.get(f"{self._ollama}/api/version")
            return r.status_code == 200
    except Exception:
        return False
```

`_health` faz **1** GET e, no primeiro `except`, devolve `False`; o gate registra `HEALTH FAIL` e o `run()` retorna `exit 1` (`:467`, `return 0 if fail == 0 else 1`). Em gauntlets consecutivos (fluxo normal de sprint: rodar a fase + `rapido`), há uma janela real em que o Ollama respondeu `/api/version` segundos antes mas ainda não estabilizou (device discovery / órfão da run anterior liberando VRAM) — e o gate reprova por raça, não por regressão. A evidência de campo está registrada nas próprias células 398 e 401 do `SPRINT_ORDER_MASTER.md`.

**Impacto agregado:** o gate 100%-obrigatório (ADR-007) reprova por raça de infraestrutura. O dono precisa re-rodar e aprende a desconfiar do vermelho — corroendo exatamente a confiança que o produto vende ao usuário leigo.

---

## Causa-raiz (verificada no código real 2026-07-12)

Todas as âncoras do briefing foram reconferidas por leitura direta; **nenhuma linha deslizou** em relação ao briefing:

- `run.sh:724` — `sleep 2` (confirmado); `run.sh:726-731` — `if curl -sf .../v1/models ... else log_err "Proxy não iniciou..."; exit 1` (confirmado, literal).
- `run.sh:744-746` — `sleep 2` + `if curl -sf http://127.0.0.1:11437/health` do cockpit (confirmado).
- `run.sh:426-435` — loop de poll do `start_ollama` a espelhar (confirmado), teto `OLLAMA_START_TIMEOUT`.
- `run.sh:120-123` — bloco `TIMEOUTS` onde `OLLAMA_START_TIMEOUT` é definido (`:122`); `NYX_PROXY_PORT` em `:128`. **`PROXY_START_TIMEOUT` não existe** hoje (grep vazio) — é env nova.
- `scripts/gauntlet/nyx_gauntlet.py:427-429` — gate de fase sem retry (confirmado); `:5000-5006` — `_health` single-shot (confirmado); `:467` — `return 0 if fail == 0 else 1` (confirmado); `NEEDS_OLLAMA` em `:251`; `self._ollama` em `:395`.

**Divergência do briefing (registrada):** o briefing citou a evidência de campo como `MASTER:1218` e `MASTER:1221`. Na árvore atual essas frases **não estão em linhas fixas soltas** — migraram para dentro das células da tabela das sprints 398 e 401 do `SPRINT_ORDER_MASTER.md` (o texto é idêntico ao citado: "proxy health-check race após 2 gauntlets seguidos + ollama órfão" e "ollama respondeu /api/version às :07 e o health do gauntlet falhou às :10"). O conteúdo do achado está preservado; apenas a referência numérica de linha do briefing ficou obsoleta.

**Divergência de escopo (registrada):** o briefing agrupava um terceiro fix — trocar o `pkill` + `sleep 1` fixo de `kill_existing_ollama` (`run.sh:407-411`) e `stop_ollama` (`run.sh:456-459`) por um poll de `pgrep -f 'ollama (serve|runner)'` até morte real. Esse é um **mecanismo diferente** (reaping de processo / liberação de VRAM no teardown), toca código guardado por `INFRA-OLLAMA-RUNNER-ORPHAN-CLEANUP-01` (ADR-034), e não é readiness/retry. Fica **fora do escopo** desta sprint, registrado como sprint própria recomendada (ver "Fora de escopo (anti-débito)"). O retry de readiness (achados A/B/C) já mitiga substancialmente o flake de campo: dar tempo com backoff ao health-check absorve a janela em que o órfão da run anterior ainda está liberando VRAM, sem tocar a delicada semântica de reaping.

---

## Solução proposta

Uma mudança coesa em torno de **um** mecanismo — *health-check com retry no lugar de single-shot* — em dois arquivos:

1. **`run.sh` (Achados A e B):** substituir o `sleep 2` + `curl` único do proxy e do cockpit por um loop de poll idêntico ao do `start_ollama`: `curl -sf` a cada 1s, sai ao primeiro OK, aborta só ao cruzar `PROXY_START_TIMEOUT` (default 30s, override `NYX_PROXY_START_TIMEOUT`). A mensagem de erro aponta a env de override.
2. **`nyx_gauntlet.py` (Achado C):** dar retry ao gate de fase — até 3 tentativas de `_health` com backoff exponencial (`2**tentativa`) antes de registrar `HEALTH FAIL`. Happy-path intacto (Ollama up na 1a tentativa sai imediato).

Custo no happy-path: **zero** — os loops saem no primeiro OK; os tetos só contam em falha real.

---

## Arquivos alvo (paths absolutos)

### `/home/andrefarias/Desenvolvimento/Nyx-Code/run.sh`

#### Edit 1 — definir `PROXY_START_TIMEOUT` no bloco TIMEOUTS (linha 122-123)

**Antes:**
```bash
OLLAMA_START_TIMEOUT="${NYX_OLLAMA_START_TIMEOUT:-30}"
WARMUP_TIMEOUT=90
```
**Depois:**
```bash
OLLAMA_START_TIMEOUT="${NYX_OLLAMA_START_TIMEOUT:-30}"
# INFRA-PROXY-READINESS-RETRY-01: readiness do proxy/cockpit poll a cada 1s ate
# responder, com este teto. Na pior maquina (ADR-034, HD lento) o venv importando
# aiohttp a frio passa de 2s p/ abrir o bind -- um curl único abortava o boot por
# falso negativo. Override via NYX_PROXY_START_TIMEOUT. So conta em falha real.
PROXY_START_TIMEOUT="${NYX_PROXY_START_TIMEOUT:-30}"
WARMUP_TIMEOUT=90
```

#### Edit 2 — readiness do proxy vira loop de poll (linhas 724-731)

**Antes:**
```bash
disown "$PROXY_PID" 2>/dev/null || true
sleep 2

if curl -sf "http://127.0.0.1:${NYX_PROXY_PORT}/v1/models" > /dev/null 2>&1; then
    log_boot "Proxy pronto (PID: $PROXY_PID)"
else
    log_err "Proxy não iniciou. Verifique logs/proxy.log"
    exit 1
fi
```
**Depois:**
```bash
disown "$PROXY_PID" 2>/dev/null || true

# INFRA-PROXY-READINESS-RETRY-01: poll espelhando start_ollama (426-435) no lugar
# do sleep 2 + curl único. Sai ao primeiro /v1/models OK; o teto so dispara em
# falha real, entao maquina lenta não aborta o boot por falso negativo (ADR-034).
proxy_elapsed=0
until curl -sf "http://127.0.0.1:${NYX_PROXY_PORT}/v1/models" > /dev/null 2>&1; do
    sleep 1
    proxy_elapsed=$((proxy_elapsed + 1))
    if [ "$proxy_elapsed" -ge "$PROXY_START_TIMEOUT" ]; then
        log_err "Proxy não iniciou em ${PROXY_START_TIMEOUT}s. Verifique logs/proxy.log"
        log_err "Máquina lenta? Aumente o teto: NYX_PROXY_START_TIMEOUT=90 ./run.sh"
        exit 1
    fi
done
log_boot "Proxy pronto (PID: $PROXY_PID, ${proxy_elapsed}s)"
```

#### Edit 3 — readiness do cockpit vira loop de poll (linhas 744-746)

**Antes:**
```bash
disown "$COCKPIT_PID" 2>/dev/null || true
sleep 2
if curl -sf http://127.0.0.1:11437/health > /dev/null 2>&1; then
    log_boot "Cockpit pronto (PID: $COCKPIT_PID)"
```
**Depois:**
```bash
disown "$COCKPIT_PID" 2>/dev/null || true
# INFRA-PROXY-READINESS-RETRY-01: mesmo poll do proxy p/ o cockpit (mesmo teto).
cockpit_elapsed=0
until curl -sf http://127.0.0.1:11437/health > /dev/null 2>&1; do
    sleep 1
    cockpit_elapsed=$((cockpit_elapsed + 1))
    if [ "$cockpit_elapsed" -ge "$PROXY_START_TIMEOUT" ]; then
        log_err "Cockpit não iniciou em ${PROXY_START_TIMEOUT}s. Verifique logs/cockpit.log"
        break
    fi
done
if curl -sf http://127.0.0.1:11437/health > /dev/null 2>&1; then
    log_boot "Cockpit pronto (PID: $COCKPIT_PID, ${cockpit_elapsed}s)"
```

> **Nota de fidelidade estrutural (Edit 3):** o bloco original do cockpit (`if ... then log_boot ...`) continua com um `else` e mais linhas de UX (rm do lockfile, xdg-open) DEPOIS da linha 746. O executor deve preservar esse corpo `if/else` intacto: o loop `until` é **inserido antes** do `if` existente e o `if` original é mantido byte-a-byte (a única mudança na linha do `log_boot` é acrescentar `, ${cockpit_elapsed}s`). O cockpit, ao contrário do proxy, **não** aborta o boot em falha (é opcional) — por isso `break` em vez de `exit 1`, e o `if` original decide se loga "pronto" ou cai no `else` de erro já existente.

### `/home/andrefarias/Desenvolvimento/Nyx-Code/scripts/gauntlet/nyx_gauntlet.py`

#### Edit 4 — retry com backoff no gate de fase (linhas 427-429)

**Antes:**
```python
            for phase in self._phases:
                if phase in NEEDS_OLLAMA and not await self._health():
                    self._add("HEALTH", f"Ollama antes de {phase}", phase, False, 0, error="Ollama não responde")
                    continue
```
**Depois:**
```python
            for phase in self._phases:
                if phase in NEEDS_OLLAMA and not await self._health_with_retry():
                    self._add("HEALTH", f"Ollama antes de {phase}", phase, False, 0, error="Ollama não responde")
                    continue
```

#### Edit 5 — novo helper `_health_with_retry` (ao lado de `_health`, linhas 5000-5006)

**Adicionar logo após `_health` (`:5000-5006`):**
```python
    async def _health_with_retry(self, tentativas: int = 3) -> bool:
        # INFRA-PROXY-READINESS-RETRY-01: gate de fase reprovava em 1 tentativa
        # (_health single-shot). Em gauntlets consecutivos ha uma janela real em
        # que o Ollama respondeu /api/version segundos antes mas ainda não
        # estabilizou (device discovery / orfao da run anterior liberando VRAM):
        # o gate reprovava por raca, não por regressao (ADR-007). Retry com
        # backoff exponencial absorve a janela; happy-path (up na 1a) sai imediato.
        for tentativa in range(tentativas):
            if await self._health():
                return True
            if tentativa < tentativas - 1:
                await asyncio.sleep(2 ** tentativa)
        return False
```

> Confirmar que `asyncio` já está importado no `nyx_gauntlet.py` (o arquivo usa `asyncio.wait_for` na linha 431 e `asyncio.sleep` já aparece na base — `rg -n "^import asyncio|asyncio.sleep" scripts/gauntlet/nyx_gauntlet.py`). Se por acaso não estiver, o import já existe pelo uso em `:431`; nenhum import novo é necessário.

---

## Diff esperado (resumo)

```
~ 2 arquivos modificados
  run.sh                          : +~22 linhas (Edit 1: +5; Edit 2: proxy ~+9 liq.; Edit 3: cockpit ~+8 liq.)
  scripts/gauntlet/nyx_gauntlet.py: +~13 linhas (Edit 4: 1 troca; Edit 5: +12 helper)
```

Sem meta numérica de tamanho — fix aditivo. O único número relevante é o net-add (~35L em 2 arquivos) e o valor do teto (`PROXY_START_TIMEOUT=30`).

---

## Aritmética

Sem meta `arquivo < NNNL` (não é refactor). Números relevantes:

- **Teto do proxy/cockpit:** novo `PROXY_START_TIMEOUT` default `30` (env `NYX_PROXY_START_TIMEOUT`). Espelha `OLLAMA_START_TIMEOUT` (30 hoje; 60 se a 414 já tiver rodado — independente desta sprint). 30s é folgado para o venv abrir o bind do aiohttp mesmo em HD lento; a env cobre o extremo.
- **Custo no happy-path:** `0s` — os `until` saem no primeiro `curl` OK (~1-3s em boot saudável); o teto só é alcançado em falha.
- **Retry do gauntlet:** até 3 tentativas, backoff `1s + 2s` (`2**0 + 2**1`) = no máximo **3s** de espera adicional **somente** quando o Ollama ainda não estabilizou; na 1a tentativa OK (caso normal) o custo é 0.

---

## Testes

- `bash -n run.sh` — baseline PASS (verificado nesta análise), esperado PASS.
- `/home/andrefarias/.local/bin/ruff check scripts/gauntlet/nyx_gauntlet.py` — esperado `All checks passed`.
- `./run.sh --smoke` — imprime `boot ok`, exit 0 (gate check #13; `--smoke` valida imports e não sobe o stack).
- `bash scripts/sprint_invariants.sh` — FAIL_BEFORE = 0 (14/14 PASS), esperado FAIL_AFTER = 0 (mudança não toca os 6 arquivos do check #14).
- Não há suíte unitária dedicada ao `run.sh`; o gate é parse + smoke + boot real (deferido para GPU).

---

## Proof-of-work esperado

Comandos runtime-reais (do BRIEF seção `[CORE] Contratos de runtime`), copy-paste:

```bash
cd /home/andrefarias/Desenvolvimento/Nyx-Code

# 1. Hipótese (lição 4): confirmar as âncoras antes de editar
rg -n "sleep 2" run.sh                                    # casa readiness proxy (724) e cockpit (744)
rg -n "Proxy não iniciou|/v1/models|PROXY_START_TIMEOUT" run.sh
rg -n "_health|NEEDS_OLLAMA|await self._health" scripts/gauntlet/nyx_gauntlet.py

# 2. Parse do shell (shellcheck não instalado neste ambiente)
bash -n run.sh                                            # sem saída = OK

# 3. Confirmar o novo teto e o loop no source
rg -n "NYX_PROXY_START_TIMEOUT:-30" run.sh                # 1 match (bloco TIMEOUTS)
rg -n "until curl -sf" run.sh                             # 2 matches (proxy + cockpit)
rg -n "_health_with_retry" scripts/gauntlet/nyx_gauntlet.py  # gate (427) + helper (novo)

# 4. Estática do gauntlet (ruff via binário direto -- ver BRIEF)
/home/andrefarias/.local/bin/ruff check scripts/gauntlet/nyx_gauntlet.py

# 5. Smoke boot obrigatório (gate check #13; valida imports, não sobe o stack)
./run.sh --smoke                                          # imprime "boot ok", exit 0

# 6. Invariantes
bash scripts/sprint_invariants.sh                         # PASS 14/14, FAIL 0

# 7. Acentuação (BRIEF: usar --paths)
python3 ~/.config/zsh/scripts/validar-acentuacao.py --paths \
  run.sh scripts/gauntlet/nyx_gauntlet.py \
  dev-journey/06-sprints/producao/SPRINT_INFRA_PROXY_READINESS_RETRY_01.md

# 8. Diff final
git --no-pager diff --stat run.sh scripts/gauntlet/nyx_gauntlet.py
```

**Boot real sob contenção (DEFERIDO — exige GPU exclusiva; executar só com `pgrep -af "Luna.*driver|valida_sprint"` vazio):**

```bash
# Proxy readiness sob máquina lenta (cenário ADR-034), stack real:
./run.sh
# Esperado: "Proxy pronto (PID: <pid>, <N>s)" com N podendo passar de 2s,
# porém < 30s; SEM "Proxy não iniciou". Colar a linha do log de boot.

# Prova do retry do gate (Achado C), gauntlets consecutivos:
./run.sh --gauntlet --only proxy   # 1a: 100%
./run.sh --gauntlet --only rapido  # 2a consecutiva: o gate NÃO deve reprovar por
                                   # HEALTH FAIL (retry absorve a janela do órfão);
                                   # eventual queda de I-05/P-0x por OOM de VRAM é o
                                   # flake conhecido (BRIEF), ORTOGONAL a este fix.
```

- Cleanup pós-teste (check #5 do BRIEF): `pkill -f "nyx/proxy.py"; pkill -f "ollama serve"; nvidia-smi` confirmando VRAM livre.
- Acentuação periférica: varredura em todos os arquivos modificados (`run.sh`, `nyx_gauntlet.py` e este spec).
- Hipótese verificada: `rg` dos identificadores citados (`PROXY_START_TIMEOUT`, `NYX_PROXY_START_TIMEOUT`, `_health_with_retry`, `_health`, `NEEDS_OLLAMA`).

> **Nota GPU:** os passos 1-8 rodam SEM subir o stack (parse/smoke/estática/invariantes). O boot real e o gauntlet consecutivo exigem GPU exclusiva — DEFERIDOS, como as specs 403/407/414 desta onda fazem (protocolo anti-contenção do BRIEF).

---

## Critério binário de aceite (IA executora)

- [ ] `PROXY_START_TIMEOUT="${NYX_PROXY_START_TIMEOUT:-30}"` no bloco TIMEOUTS (122-123)
- [ ] Readiness do proxy (724-731) é loop `until curl -sf .../v1/models`, sai ao 1o OK, aborta só ao cruzar `PROXY_START_TIMEOUT`, com `log_err` citando `NYX_PROXY_START_TIMEOUT`
- [ ] Readiness do cockpit (744+) é o mesmo loop de `/health` (com `break`, não `exit 1`); o corpo `if/else` original do cockpit fica intacto
- [ ] Gate de fase do gauntlet chama `_health_with_retry` (Edit 4); helper novo com até 3 tentativas + backoff `2**tentativa` (Edit 5)
- [ ] Happy-path intacto: proxy/cockpit saem em segundos; gauntlet up na 1a tentativa sem atraso
- [ ] Semântica de reaping (`pkill` de kill_existing_ollama/stop_ollama) NÃO tocada
- [ ] `bash -n run.sh` OK; `ruff` limpo no gauntlet; `--smoke` boot ok exit 0; invariantes 14/14; acentuação rc=0
- [ ] Proof colado: passos 1-8; boot real e gauntlet consecutivo marcados DEFERIDO (GPU)
- [ ] `SPRINT_ORDER_MASTER.md` marca 431 CONCLUIDA; spec movida para `concluidos/`
- [ ] NÃO commitar; NÃO tocar Checkpoint.md; NÃO tocar a semântica de reaping

---

## Guardrails anti-engodo (obrigatórios)

NÃO marcar concluída se:
- O `sleep 2` do proxy/cockpit continuar no lugar do loop de poll (a troca é o núcleo do fix).
- O teto `PROXY_START_TIMEOUT` for aplicado ao happy-path (o `until` DEVE sair ao primeiro OK; o teto só conta em falha).
- O gauntlet reprovar `HEALTH FAIL` sem esgotar as 3 tentativas (o retry é o núcleo do Achado C).
- A semântica de reaping (`pkill`/`sleep 1` de kill_existing_ollama/stop_ollama) foi alterada — é escopo de OUTRA sprint (ver Fora de escopo).
- O corpo `if/else` do cockpit (rm do lockfile, xdg-open, `else` de erro) foi removido ou reordenado.
- `bash -n` falhou, `ruff` acusou, `--smoke` não imprimiu `boot ok`, ou acentuação != rc 0.

Se algo falhar: `[SPRINT 431] BLOQUEADA: <motivo 1 linha>`.

---

## Invariantes a preservar

- **Nome da env de override:** `NYX_PROXY_START_TIMEOUT` (nova, espelha `NYX_OLLAMA_START_TIMEOUT`) — não renomear depois de definida.
- **Endpoints e portas:** proxy `11436` / `/v1/models`; cockpit `11437` / `/health`; Ollama `11435` / `/api/version` — nenhum muda.
- **Semântica do poll:** `curl -sf` a cada 1s, sai ao primeiro OK; teto só dispara em falha (idêntico ao `start_ollama`).
- **Reaping intocado:** `kill_existing_ollama` (407-408) e `stop_ollama` (456-459) seguem byte-idênticos (guardados por `INFRA-OLLAMA-RUNNER-ORPHAN-CLEANUP-01`, ADR-034).
- **Sem emoji, sem menção a IA externa em código** (checks universais 2 e 3 do BRIEF).
- **Docs/comentário em PT-BR acentuado** (check 4; gate pre-commit bloqueia ASCII).
- **Nenhum débito implícito** (check 6): o reaping poll levantado no briefing vira sprint própria abaixo, não é absorvido aqui.

---

## Fora de escopo (anti-débito)

| Item | Decisão |
|------|---------|
| **Reaping de órfão com poll de morte real** — trocar `pkill` + `sleep 1` fixo de `kill_existing_ollama` (`run.sh:407-411`) e `stop_ollama` (`run.sh:456-459`) por `pgrep -f 'ollama (serve\|runner)'` até vazio com timeout (~10s), em vez de confiar num sleep fixo que não confirma morte/liberação de VRAM. | **Sprint própria recomendada: `INFRA-OLLAMA-REAP-WAIT-01`.** Mecanismo DIFERENTE (teardown/reaping, não readiness/retry), toca código guardado pela `INFRA-OLLAMA-RUNNER-ORPHAN-CLEANUP-01` (ADR-034). O retry de readiness desta sprint já mitiga o flake de campo (dá tempo ao órfão liberar VRAM); o reaping determinístico é hardening adicional. Registrar no `SPRINT_ORDER_MASTER` (check #6, `feedback_nenhum_debito`). |
| **`curl` usado sem guard de existência** (`run.sh:427` e demais) — se o binário `curl` faltar, o poll falha silenciosamente até o teto. | Candidato menor (nota do orquestrador). Não-objetivo desta sprint. Registrar como follow-up se o dono quiser um preflight de dependências. |
| **Porta do proxy (11436) ocupada sem detecção honesta** (`run.sh:729`) — se algo já escuta 11436, o `curl` passa e o boot segue com um proxy alheio. | Candidato relacionado (nota do orquestrador). Detecção honesta de porta ocupada é outro mecanismo (preflight de bind, não readiness). Não-objetivo; follow-up se priorizado. |
| **Timeout adaptativo por detecção de hardware** para o proxy/cockpit. | Complexidade especulativa (GUIDE §2). A env de override cobre o extremo. Só vira sprint se houver evidência de que 30s + override não bastam. |

---

## Referências

- BRIEF: `/home/andrefarias/Desenvolvimento/Nyx-Code/VALIDATOR_BRIEF.md` (seção `[CORE] Contratos de runtime`; `[CORE] Flake reprodutível do gauntlet`)
- ADRs: `dev-journey/03-decisions/ADR_034_FEITO_PARA_QUEM_NAO_TEM_A100.md`; ADR-007 (gate 100%); ADR-032/033 (a infra carrega o modelo)
- Precedente direto: `dev-journey/06-sprints/producao/SPRINT_INFRA_OLLAMA_BOOT_TIMEOUT_DEFAULT_01.md` (414 — mesmo padrão de teto de boot no `run.sh`)
- Evidência de campo: células 398 e 401 do `SPRINT_ORDER_MASTER.md` (flaky de boot / proxy health-check race)
- Código: `run.sh:120-123` (TIMEOUTS), `run.sh:426-435` (loop a espelhar), `run.sh:724-731` (proxy), `run.sh:744-746` (cockpit); `scripts/gauntlet/nyx_gauntlet.py:427-429` (gate), `:5000-5006` (`_health`), `:467` (exit)

---

*"O health-check que reprova a máquina fraca no instante em que ela ainda está acordando não mede regressão — mede a impaciência do teto. A infra espera; o modelo não precisa saber." — princípio do ADR-034/ADR-007*
