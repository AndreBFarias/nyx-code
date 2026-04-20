## 0. SPEC

```yaml
sprint:
  id: INFRA-GAUNTLET-01
  title: "Rodar gauntlet completo com watchdog de VRAM, refrescar baseline"
  onda: 22
  bloco: 2.6
  prioridade: CRÍTICA
  tipo: Infra
  dependencias: [AUDIT-FIX-08, AUDIT-FIX-09, DEBT-04, DEBT-05]
  desbloqueia: [VALIDATE-ONDA-20, VALIDATE-ONDA-21, UX-DESIGN-01]

  creates:
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/scripts/vram_watchdog.sh
      reason: "Monitor de VRAM que aborta gauntlet preventivamente se memória livre cair abaixo de threshold"
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/dev-journey/07-reports/gauntlet/baselines/baseline_2026-04-19.json
      reason: "Novo baseline limpo após sprints do Bloco 2.5"

  touches:
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/dev-journey/07-reports/GAUNTLET_REPORT.md
      reason: "Report fica sem REGRESSAO fantasma"
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/dev-journey/07-reports/gauntlet/checkpoint.json
      reason: "Checkpoint atualiza para pass rate 100%"

  removes: []

  forbidden:
    - "Abrir Chrome ou outras aplicações de GPU durante a execução"
    - "Declarar sucesso com pass rate < 100% (reportar BLOQUEADA se não alcançar)"
    - "Pular fases com flags de skip — todas as fases devem rodar"

  tests:
    - cmd: "./run.sh --gauntlet 2>&1 | tee /tmp/gauntlet_full.log"
      timeout: 1800
      deve_passar: true
    - cmd: "grep -E 'Pass rate:.*100%' dev-journey/07-reports/GAUNTLET_REPORT.md"
      deve_passar: true
    - cmd: "grep -c 'REGRESSAO' dev-journey/07-reports/GAUNTLET_REPORT.md"
      esperado: "0"

  acceptance_criteria:
    - "Gauntlet completo (todas as fases) passa 100%"
    - "Baseline salvo como dev-journey/07-reports/gauntlet/baselines/baseline_2026-04-19.json"
    - "GAUNTLET_REPORT.md sem palavra REGRESSAO"
    - "scripts/vram_watchdog.sh criado, executável, monitora memória livre a cada 5s"
    - "Log de VRAM salvo em /tmp/vram_watch.log com timestamps"
    - "Watchdog aborta gauntlet via pkill se memória livre < threshold (default 500 MiB)"
```

---

# Sprint INFRA-GAUNTLET-01 — Gauntlet com watchdog de VRAM

**Status:** PENDENTE
**Data criação:** 2026-04-19
**Modelo obrigatório:** claude-opus-4-7 (sem subagentes)

---

## Contexto do projeto (snapshot)

> - ADR-007 Gauntlet; ADR-011 Gauntlet Obrigatório; ADR-020 Testes via run.sh.
> - Relatório Bloco 2 Onda 22 §3.1: 5 sprints concluídas sem gauntlet 100% por OOM de VRAM.
> - `GAUNTLET_REPORT.md` atual reporta `REGRESSAO: Pass rate caiu: 100% -> 67%` (fantasma de ambiente, não de código).
> - Máquina: RTX 3050 Laptop 4GB, 14.8 GiB RAM, estado atual GPU 64/4096 MiB (1% uso). Condições ideais.
> - Bloco 2.5 (AUDIT-FIX-08, AUDIT-FIX-09, DEBT-04, DEBT-05) deve ser concluído antes para garantir invariantes estáveis.

---

## Problema

Baseline do gauntlet está poluído por falsos positivos. Sprints do Bloco 2.5 precisam ser validadas contra gauntlet completo; antes disso o baseline precisa estar limpo. Sem watchdog, OOM volta a bloquear a execução se VRAM for consumida por outros processos.

---

## Solução proposta

### Parte 1 — `scripts/vram_watchdog.sh`

Script que roda em background durante o gauntlet:
- A cada 5s, lê `nvidia-smi --query-gpu=memory.free --format=csv,noheader,nounits`.
- Loga timestamp + valor em `/tmp/vram_watch.log`.
- Se `memory.free < 500 MiB` **por 2 leituras consecutivas**, executa `pkill -f "gauntlet"` + `pkill -f "ollama"` e grita no stdout.
- PID salvo em `/tmp/vram_watchdog.pid` para kill limpo no fim do gauntlet.

### Parte 2 — Execução guiada do gauntlet

```bash
# pré-checks (CONFIRMAR com usuário):
# - Chrome fechado? Claude Desktop fechado?
nvidia-smi --query-gpu=memory.free --format=csv,noheader,nounits
# esperado: >= 3000 (MiB livres)

# iniciar watchdog
bash scripts/vram_watchdog.sh &
WATCH_PID=$!
echo $WATCH_PID > /tmp/vram_watchdog.pid

# rodar gauntlet completo
./run.sh --gauntlet 2>&1 | tee /tmp/gauntlet_full.log

# parar watchdog
kill $WATCH_PID 2>/dev/null
```

### Parte 3 — Salvar baseline

Após 100% pass:
```bash
cp dev-journey/07-reports/gauntlet/checkpoint.json \
   dev-journey/07-reports/gauntlet/baselines/baseline_2026-04-19.json
```

---

## Arquivos alvo

### `/home/andrefarias/Desenvolvimento/Nyx-Code/scripts/vram_watchdog.sh` (criar)

```bash
#!/usr/bin/env bash
# Monitor de VRAM durante execução do gauntlet.
# Uso: bash scripts/vram_watchdog.sh &
# Mata gauntlet + ollama se VRAM livre cair abaixo de THRESHOLD_MIB por 2 leituras seguidas.

set -u

LOG="/tmp/vram_watch.log"
PID_FILE="/tmp/vram_watchdog.pid"
THRESHOLD_MIB="${VRAM_THRESHOLD_MIB:-500}"
INTERVAL_S="${VRAM_INTERVAL_S:-5}"
BREACH_COUNT=0
BREACH_MAX=2

echo $$ > "$PID_FILE"
echo "[$(date -Iseconds)] watchdog iniciado (threshold=${THRESHOLD_MIB} MiB, interval=${INTERVAL_S}s)" | tee -a "$LOG"

while true; do
    FREE=$(nvidia-smi --query-gpu=memory.free --format=csv,noheader,nounits 2>/dev/null | head -1 | tr -d ' ')
    TS=$(date -Iseconds)
    if [ -z "$FREE" ]; then
        echo "[${TS}] WARN: nvidia-smi falhou" | tee -a "$LOG"
        sleep "$INTERVAL_S"
        continue
    fi
    echo "[${TS}] free=${FREE} MiB" >> "$LOG"
    if [ "$FREE" -lt "$THRESHOLD_MIB" ]; then
        BREACH_COUNT=$((BREACH_COUNT + 1))
        echo "[${TS}] BREACH ${BREACH_COUNT}/${BREACH_MAX} (free=${FREE} < ${THRESHOLD_MIB})" | tee -a "$LOG"
        if [ "$BREACH_COUNT" -ge "$BREACH_MAX" ]; then
            echo "[${TS}] EMERGÊNCIA: abortando gauntlet e ollama" | tee -a "$LOG"
            pkill -f "nyx_gauntlet.py"
            pkill -f "ollama"
            rm -f "$PID_FILE"
            exit 2
        fi
    else
        BREACH_COUNT=0
    fi
    sleep "$INTERVAL_S"
done
```

Tornar executável: `chmod +x scripts/vram_watchdog.sh`.

### Baseline

Copiar `checkpoint.json` → `baselines/baseline_2026-04-19.json` somente se pass rate = 100%.

---

## Comandos de verificação

```bash
# pré-check VRAM
nvidia-smi --query-gpu=memory.free --format=csv,noheader,nounits

# executar
bash scripts/vram_watchdog.sh &
./run.sh --gauntlet 2>&1 | tee /tmp/gauntlet_full.log
kill $(cat /tmp/vram_watchdog.pid) 2>/dev/null

# validar
grep 'Pass rate' dev-journey/07-reports/GAUNTLET_REPORT.md
grep -c REGRESSAO dev-journey/07-reports/GAUNTLET_REPORT.md
tail -20 /tmp/vram_watch.log
```

---

## Critério binário de aceite

- [ ] `scripts/vram_watchdog.sh` criado e executável
- [ ] `/tmp/vram_watch.log` preenchido com timestamps + valores reais
- [ ] Gauntlet completo roda do início ao fim (não aborta)
- [ ] Pass rate = 100% no GAUNTLET_REPORT.md
- [ ] `baseline_2026-04-19.json` criado em `gauntlet/baselines/`
- [ ] Zero ocorrência de `REGRESSAO` no report
- [ ] Commit `infra: adiciona watchdog de VRAM e refresca baseline do gauntlet`

---

## Gambiarras específicas

- **Watchdog sem `pkill` real** — só loga, não aborta. Proibido: watchdog precisa abortar na breach.
- **Threshold alto demais** (ex.: 2000 MiB) — aborta preventivamente quando gauntlet ainda rodaria. Manter padrão 500 MiB.
- **Baseline forjado** — copiar checkpoint antigo como se fosse novo. Detectar: timestamp do JSON deve ser de hoje.
- **Pular fase** via `--only rapido` e declarar gauntlet completo passou. Proibido: obrigatório `./run.sh --gauntlet` sem filtros.

---

## Riscos

| Risco | Mitigação |
|-------|-----------|
| Outros processos consumindo VRAM durante execução | Pré-check manual: fechar Chrome/Claude Desktop; confirmar `free >= 3000 MiB` antes |
| `nvidia-smi` não responder rápido | Watchdog tolera falha pontual de leitura (loga WARN, não aborta) |
| `pkill` derrubar outros processos pkill-f "gauntlet" pode ser ambíguo | Pattern específico `nyx_gauntlet.py` evita colisão |

---

## Validação humana

Após a sprint, o usuário pode verificar:
```bash
ls dev-journey/07-reports/gauntlet/baselines/
# esperado: baseline_2026-04-19.json existe

tail -5 /tmp/vram_watch.log
# esperado: timestamps recentes, free sempre >= 500 MiB

grep 'Pass rate' dev-journey/07-reports/GAUNTLET_REPORT.md
# esperado: "Pass rate: 100%"
```

---

*"Confiar em medições é o primeiro passo da engenharia." -- Lord Kelvin (paráfrase)*
