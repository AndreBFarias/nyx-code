## 0. SPEC (machine-readable)

```yaml
sprint:
  id: INFRA-OLLAMA-BOOT-TIMEOUT-DEFAULT-01
  numero_master: 414
  title: "run.sh: default de OLLAMA_START_TIMEOUT (30s) curto demais para cold-start sob contencao de VRAM"
  onda: 48
  prioridade: BAIXA
  tipo: Infra/Boot
  dependencias: []
  desbloqueia: []

  touches:
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/run.sh
      reason: "Linha 122 fixa default 30s; linhas 431-432 emitem o erro sem apontar a env de override"
      linhas_alvo: "122, 430-434"
  creates: []
  removes: []

  forbidden:
    - "Adicionar emoji"
    - "Renomear a env de override (o nome canônico é NYX_OLLAMA_START_TIMEOUT)"
    - "Introduzir detecção de hardware / timeout adaptativo (complexidade especulativa; ver não-objetivos)"
    - "Alterar a semantica do loop de poll (curl /api/version a cada 1s ate responder)"
    - "Mexer em WARMUP_TIMEOUT, CURL_TIMEOUT ou qualquer outro timeout do bloco"

  tests:
    - cmd: "bash -n run.sh"
      timeout: 30
      deve_passar: true
    - cmd: "./run.sh --smoke"
      timeout: 120
      deve_passar: true

  acceptance_criteria:
    - "run.sh:122 usa default 60 (NYX_OLLAMA_START_TIMEOUT:-60), mantendo o nome exato da env de override"
    - "Happy-path inalterado: o loop sai assim que /api/version responde; 60s e apenas o teto de falha"
    - "Mensagem de erro passa a apontar a env NYX_OLLAMA_START_TIMEOUT para maquina lenta se auto-servir"
    - "bash -n run.sh sem erro; ./run.sh --smoke imprime boot ok e exit 0"
    - "Acentuacao PT-BR correta; zero emoji; zero mencao a ferramenta de IA"
```

---

# Sprint INFRA-OLLAMA-BOOT-TIMEOUT-DEFAULT-01 — teto de boot do Ollama de 30s para 60s

**Status:** PENDENTE
**Data criação:** 2026-07-12
**Origem:** achado da validação holística ONDA-48 (session1, 2026-06-26), registrado na linha 1232 do `SPRINT_ORDER_MASTER.md` (bloco `MANUAL_OVERRIDE_ONDA_48`).

---

## Contexto do projeto (snapshot)

> **ADRs:** ADR-034 (Feito para quem não tem A100 — sucesso se mede no pior hardware razoável com o desktop cheio), ADR-032 (a infra carrega o modelo), ADR-006 (docs PT-BR).
> **Estado (2026-07-12):** ONDA-48, núcleo do contrato concluído (399/397/400/398/401). Achados colaterais registrados; 414 é o único de infra/boot ainda sem spec em `producao/`.

O `run.sh` sobe um Ollama dedicado na porta 11435 antes do proxy e da TUI. A `função` `start_ollama()` (`run.sh:415`) dispara `ollama serve` em background e faz busy-loop de `curl -sf /api/version` a cada 1s, saindo assim que o daemon responde. O teto desse loop é `OLLAMA_START_TIMEOUT`.

---

## Problema

**Achado (validação holística session1, 2026-06-26).** O default de `OLLAMA_START_TIMEOUT` é 30s (`run.sh:122`). No cenário de referência do ADR-034 — RTX 3050 4GB com o desktop cheio disputando VRAM — o cold-start do `ollama serve` (device discovery / init CUDA sob contenção) cruza os 30s antes de `/api/version` responder, e o boot aborta com:

```
Ollama não iniciou em 30s
```

Causa-raiz (`run.sh:122`):

```bash
OLLAMA_START_TIMEOUT="${NYX_OLLAMA_START_TIMEOUT:-30}"
```

O loop que consome o valor (`run.sh:426-435`):

```bash
    local elapsed=0
    while ! curl -sf "http://${NYX_OLLAMA_HOST}:${NYX_OLLAMA_PORT}/api/version" > /dev/null 2>&1; do
        sleep 1
        elapsed=$((elapsed + 1))
        if [ "$elapsed" -ge "$OLLAMA_START_TIMEOUT" ]; then
            log_err "Ollama não iniciou em ${OLLAMA_START_TIMEOUT}s"
            log_err "Verifique logs/ollama.log"
            exit 1
        fi
    done
```

O `while` sai no instante em que `/api/version` responde — logo o teto **só é atingido em falha**. Elevá-lo não custa nada no happy-path (boot saudável sai em ~1-3s e nunca chega perto do teto).

---

## Decisão de valor: 60s fixo, não adaptativo

A tabela do MASTER sugere 60. A tarefa pede avaliar, à luz do ADR-034 (máquina fraca, possivelmente CPU-only), se 60 basta ou se o valor deveria ser maior/adaptativo. Análise:

1. **O gate do loop é `/api/version`, não a carga do modelo.** `/api/version` responde quando o servidor HTTP do daemon está de pé. O que atrasa esse instante no cenário do achado é o device discovery / init CUDA do `ollama serve` sob VRAM disputada — não o load do qwen2.5-coder. A pré-carga do modelo acontece depois, sob `WARMUP_TIMEOUT=90` (`run.sh:123`), fora do escopo deste teto.
2. **Máquina CPU-only não é o pior caso deste teto.** Sem NVIDIA, o discovery de GPU do `ollama serve` termina cedo (nada a sondar em profundidade) e `/api/version` sobe rápido. O pior caso é justamente a GPU contida (RTX 3050 sob carga), já coberto por 60s. Uma máquina lenta por disco/RAM velhos ainda cabe folgadamente em 60s para subir o binário do daemon.
3. **Adaptativo seria complexidade especulativa (GUIDE §2).** Detectar hardware para escalar o teto adiciona código e caminhos de falha sem retorno: o loop já sai cedo no happy-path (custo zero) e a env de override `NYX_OLLAMA_START_TIMEOUT` já existe para o caso extremo. Honrar o ADR-034 aqui é **degradação graciosa via override documentado**, não detecção automática.

**Recomendação:** default 60s fixo. Preservar a env de override `NYX_OLLAMA_START_TIMEOUT` (nome exato confirmado no `run.sh` real, linha 122) e citá-la na mensagem de erro, para a máquina no limite se auto-servir sem tocar código.

---

## Arquivos alvo (paths absolutos)

### `/home/andrefarias/Desenvolvimento/Nyx-Code/run.sh`

**Mudança 1 — linha 122 (elevar o default):**

Antes:
```bash
OLLAMA_START_TIMEOUT="${NYX_OLLAMA_START_TIMEOUT:-30}"
```

Depois:
```bash
# INFRA-OLLAMA-BOOT-TIMEOUT-DEFAULT-01: cold-start do daemon sob contenção de
# VRAM (RTX 3050 4GB com desktop cheio, cenário do ADR-034) cruza os 30s antes
# de /api/version responder. Teto elevado p/ 60s (custo zero no happy-path: o
# loop sai assim que o daemon responde). Override via NYX_OLLAMA_START_TIMEOUT.
OLLAMA_START_TIMEOUT="${NYX_OLLAMA_START_TIMEOUT:-60}"
```

**Mudança 2 — linhas 430-434 (mensagem de erro aponta a env de override):**

Antes:
```bash
        if [ "$elapsed" -ge "$OLLAMA_START_TIMEOUT" ]; then
            log_err "Ollama não iniciou em ${OLLAMA_START_TIMEOUT}s"
            log_err "Verifique logs/ollama.log"
            exit 1
        fi
```

Depois:
```bash
        if [ "$elapsed" -ge "$OLLAMA_START_TIMEOUT" ]; then
            log_err "Ollama não iniciou em ${OLLAMA_START_TIMEOUT}s"
            log_err "Verifique logs/ollama.log"
            log_err "Máquina lenta? Aumente o teto: NYX_OLLAMA_START_TIMEOUT=120 ./run.sh"
            exit 1
        fi
```

**Escopo líquido:** 1 arquivo, ~5 linhas (comentário + valor + 1 linha de log). Nada além disso.

---

## Diff esperado (resumo)

```
~ 1 arquivo modificado (run.sh)
  L122: default 30 -> 60 (+ comentário de rationale)
  L430-434: +1 log_err apontando NYX_OLLAMA_START_TIMEOUT
```

---

## Invariantes a preservar

- **Nome da env de override:** `NYX_OLLAMA_START_TIMEOUT` (linha 122 do `run.sh` real) — não renomear.
- **Semântica do loop:** poll de `/api/version` a cada 1s, sai ao primeiro OK; o teto só dispara em falha.
- **Outros timeouts intactos:** `CURL_TIMEOUT` (121), `WARMUP_TIMEOUT=90` (123) não são tocados.
- **Sem emoji, sem menção a IA externa em código** (checks universais 2 e 3 do BRIEF).
- **Docs/comentário em PT-BR acentuado** (check 4; gate pre-commit bloqueia ASCII).
- **Nenhum débito implícito** (check 6): se durante a execução surgir um cenário onde 60s ainda estoura sistematicamente, registrar sprint nova no `SPRINT_ORDER_MASTER` — não subir o valor "no chute" fora desta spec.

---

## Plano de implementação

1. Confirmar hipótese: `rg -n "OLLAMA_START_TIMEOUT" run.sh` deve casar linhas 122, 430, 431 (lição 4 — só editar o que o grep confirma).
2. Editar `run.sh:122`: default `30` -> `60` com o comentário de rationale.
3. Editar o bloco de erro (`run.sh:430-434`): acrescentar o `log_err` com a dica de override.
4. `bash -n run.sh` — parse sem erro.
5. `./run.sh --smoke` — imprime `boot ok`, exit 0 (gate obrigatório antes de CONCLUIDA; note que `--smoke` valida imports e NÃO sobe o Ollama, ver `run.sh:149`).
6. `validar-acentuacao.py --paths run.sh` (e no próprio spec) rc=0.
7. Boot real sob contenção (deferido para quando a GPU liberar): `./run.sh` com o desktop cheio na RTX 3050 — confirmar `Ollama pronto (PID: ..., Ns)` com N possivelmente > 30 e < 60, e ausência de `Ollama não iniciou`.

---

## Aritmética

Sem meta numérica de linhas (não é refactor). O único número relevante é o valor do teto:

- Valor atual: `30` (`run.sh:122`).
- Valor alvo: `60`.
- Custo no happy-path: **0s** — o `while` sai ao primeiro `/api/version` OK (~1-3s em boot saudável); o teto de 60s só é alcançado em falha real.
- Teto de warmup adjacente (não tocado): `WARMUP_TIMEOUT=90` (`run.sh:123`) — referência de que 60s para o daemon é coerente com a folga já dada à fase seguinte.

---

## Testes

- `bash -n run.sh` — baseline PASS (verificado nesta análise), esperado PASS.
- `./run.sh --smoke` — imprime `boot ok`, exit 0.
- Não há suíte unitária dedicada ao `run.sh`; o gate é smoke + parse + boot real sob contenção.
- Baseline de invariantes: `bash scripts/sprint_invariants.sh` — FAIL_BEFORE = 0 (14/14 PASS), esperado FAIL_AFTER = 0 (mudança não toca os arquivos do check #14).

---

## Proof-of-work esperado

Comandos runtime-reais (do BRIEF seção `[CORE] Contratos de runtime`), copy-paste:

```bash
# 1. Hipótese (lição 4): confirmar os alvos antes de editar
rg -n "OLLAMA_START_TIMEOUT" run.sh          # casa 122, 430, 431

# 2. Parse do shell (shellcheck não está instalado neste ambiente)
bash -n run.sh                                # sem saída = OK

# 3. Confirmar o novo default no source
rg -n "NYX_OLLAMA_START_TIMEOUT:-60" run.sh   # 1 match na linha 122

# 4. Smoke boot obrigatório (gate check #13; valida imports, não sobe Ollama)
./run.sh --smoke                              # imprime "boot ok", exit 0

# 5. Invariantes
bash scripts/sprint_invariants.sh             # PASS 14/14, FAIL 0

# 6. Acentuação (BRIEF: usar --paths)
python3 ~/.config/zsh/scripts/validar-acentuacao.py --paths run.sh dev-journey/06-sprints/producao/SPRINT_INFRA_OLLAMA_BOOT_TIMEOUT_DEFAULT_01.md

# 7. Diff final
git diff run.sh
```

**Boot real sob contenção (DEFERIDO — GPU ocupada por outra validação nesta janela):**

```bash
# Com Chrome + Spotify + Discord abertos (cenário ADR-034) na RTX 3050 4GB:
./run.sh
# Esperado: "Ollama pronto (PID: <pid>, <N>s)" com N podendo passar de 30s,
# porém < 60s; SEM "Ollama não iniciou". Colar a linha do log de boot.
```

- Cleanup pós-teste (check #5 do BRIEF): `pkill -f "nyx/proxy.py"; pkill -f "ollama serve"; nvidia-smi` confirmando VRAM livre.
- Acentuação periférica: varredura em todos os arquivos modificados (`run.sh` + este spec).
- Hipótese verificada: `rg` dos identificadores citados (`OLLAMA_START_TIMEOUT`, `NYX_OLLAMA_START_TIMEOUT`).

---

## Riscos e não-objetivos

| Risco | Mitigação |
|-------|-----------|
| 60s ainda estoura em hardware extremo | A env `NYX_OLLAMA_START_TIMEOUT` (agora citada no erro) permite subir sem tocar código — degradação graciosa (ADR-034). Se estourar de forma sistemática mesmo com override, abrir sprint nova (check #6, sem débito implícito). |
| Boot "mais lento" percebido pelo usuário | Falso: o teto só conta em falha; boot saudável sai em segundos. |

**Não-objetivos (fora desta sprint):**
- Timeout adaptativo por detecção de hardware — complexidade especulativa (GUIDE §2); se um dia for requisito real, vira sprint própria com evidência.
- Mexer em `WARMUP_TIMEOUT`, `CURL_TIMEOUT` ou na lógica de poll.
- Retry/backoff do `ollama serve` — outro escopo.

---

## Referências

- BRIEF: `/home/andrefarias/Desenvolvimento/Nyx-Code/VALIDATOR_BRIEF.md`
- ADR: `dev-journey/03-decisions/ADR_034_FEITO_PARA_QUEM_NAO_TEM_A100.md`
- Registro do achado: `dev-journey/06-sprints/SPRINT_ORDER_MASTER.md` linha 1232 (bloco `MANUAL_OVERRIDE_ONDA_48`)
- Código: `run.sh:122` (default), `run.sh:415-438` (`start_ollama`), `run.sh:426-435` (loop de poll)

---

*"O teto que só dispara quando a máquina fraca ainda está acordando não pode ser mais curto que o bocejo dela." — princípio do ADR-034*
