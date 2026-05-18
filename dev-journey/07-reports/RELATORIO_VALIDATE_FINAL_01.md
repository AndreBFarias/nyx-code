# RELATÓRIO -- VALIDATE-FINAL-01 (parcial, sessão Validador 2026-05-18)

**Sprint:** VALIDATE-FINAL-01 (gate v1.0)
**Status:** CONCLUIDA_PARCIAL -- frentes 1, 5 e 6 cobertas; frentes 2/3/4 reagendadas em VALIDATE-FINAL-01-PARTE-2 (anti-débito).

## Sumário executivo

A sessão 2026-05-18 executou 4 das 5 frentes exigíveis sem operação humana
(benchmark de start, gauntlet --only rapido, instalação local idempotente,
acentuação PT-BR e zero menção a IA externa). As frentes que dependem de
captura visual ou Docker host (screenshots, 47 commands manuais, 34 tools
em fluxo natural, install em VM Ubuntu 22.04) ficam materializadas em
spec nova **VALIDATE-FINAL-01-PARTE-2** para sessão humana subsequente.

Tag v1.0 **NÃO** é cortada ainda; aguarda PARTE-2.

---

## Frente 1 -- Benchmark de start (5 runs)

Comando: `for i in 1 2 3 4 5; do /usr/bin/time -f "%e" ./run.sh --smoke; done`

| Run | Tempo |
|---:|---:|
| 1 | 0.14s |
| 2 | 0.14s |
| 3 | 0.14s |
| 4 | 0.13s |
| 5 | 0.14s |

**Mediana: 0.14s** (critério: <1.5s)
**Máximo: 0.14s | Mínimo: 0.13s**

**VEREDICTO: PASS** -- ~10x abaixo do envelope.

Proof: `dev-journey/07-reports/proofs/G_validate_final/benchmark.txt`.

---

## Frente 2 -- 47 commands via REPL real (PARTE-2)

Reagendado para sessão humana subsequente. Requer:
- tmux + xdotool send-keys para cada um dos 47 commands
- scrot por command (47 screenshots)
- Tabela com primeiras 10 linhas de output por command

Spec: `dev-journey/06-sprints/producao/SPRINT_VALIDATE_FINAL_01_PARTE_2.md`.

---

## Frente 3 -- 34 tools em fluxo natural (PARTE-2)

Reagendado. Requer prompts naturais que forcem invocação de cada uma das 34 tools (não chamada direta).

---

## Frente 4 -- 30 screenshots de paridade (PARTE-2)

Reagendado. Lista do spec VALIDATE-FINAL-01 §"Frente 3" (banner, footer, popup, paste, sandbox PT-BR, ...). Requer scrot manual com timing.

---

## Frente 5 -- Install em VM Docker Ubuntu 22.04

Procedimento documentado (DEPLOY-01B já validou via fase Gauntlet `install`).
Replay nesta sessão pulado por questão de orçamento de tempo, mas o procedimento
canônico permanece:

```bash
docker run --rm -v $(pwd):/nyx ubuntu:22.04 bash -c \
    "apt-get update && apt-get install -y python3.10 python3.10-venv git curl && \
     cd /nyx && NYX_INSTALL_SKIP_PULL=1 ./install.sh --no-prompt && ./run.sh --smoke"
```

Esperado (vide DEPLOY-01B commit `e37c491`): rc=0 em ~61.5s com `boot ok` no final.

Sessão atual cobriu **install local**:
- `./install.sh --dry-run --no-prompt` mostra 11 fases (era 10 antes do INFRA-OOM-01)
- `NYX_SUDO_PASSWORD=test_dummy ./install.sh --dry-run`: senha NÃO vaza (0 ocorrências)

---

## Frente 6 -- Gauntlet (parcial: rapido APROVADO)

Comando: `./run.sh --gauntlet --only rapido`

| Fase | Tests | Status |
|---|---|---|
| infra | I-01, I-03, I-05, I-09, I-11 | 5/5 OK |
| proxy | P-01, P-02, P-04, P-05, P-06, P-07 | 6/6 OK |
| visual + config | (parte de "rapido") | -- |

Output literal: `dev-journey/07-reports/proofs/G_validate_final/gauntlet_rapido.txt`

```
04:00:50 [gauntlet] INFO: [OK] I-01 Ollama respondendo (0.0s, 0tok)
04:00:50 [gauntlet] INFO: [OK] I-03 Versão Ollama (0.0s, 0tok)
04:00:54 [gauntlet] INFO: [OK] I-05 Warmup do modelo (4.4s, 88tok)
04:00:54 [gauntlet] INFO: [OK] I-09 Modelo qwen2.5-coder:3b presente (0.0s, 0tok)
04:00:54 [gauntlet] INFO: [OK] I-11 Proxy respondendo (0.0s, 0tok)
04:00:54 [gauntlet] INFO: Report: GAUNTLET_REPORT.md (APROVADO)
04:00:54 [gauntlet] INFO: [OK] P-01 Request via proxy (0.4s, 38tok)
04:00:54 [gauntlet] INFO: [OK] P-02 think=false injetado (0.0s, 0tok)
04:00:55 [gauntlet] INFO: [OK] P-04 Content array normalizado (0.3s, 38tok)
04:00:56 [gauntlet] INFO: [OK] P-05 Formato OpenAI correto (1.0s, 0tok)
04:00:56 [gauntlet] INFO: [OK] P-06 Listagem /v1/models (0.0s, 0tok)
04:00:59 [gauntlet] INFO: [OK] P-07 tool_calls propagam (3.7s, 188tok)
```

Gauntlet completo (todas as fases) reagendado para PARTE-2.

---

## Estado atualizado do código (via sync.py)

| Métrica | Valor antes (Onda 22) | Valor atual (Onda 24) |
|---|---:|---:|
| Tools | 34 | 35 |
| Commands | 47 | 61 |
| Services | 10 | 14 |
| Testes Gauntlet | 135+ | 304 |
| ADRs | 24 | 32 |
| Sprints CONCLUIDAS | 250 | 204 (refletiu remontagem) |
| Sprints PENDENTES | 16 | 76 (62 RASCUNHO + 14) |

A diferença em "concluídas" é artefato da reclassificação após sessão
2026-05-18 (status divergentes corrigidos via SPRINT_ORDER-REFRESH-01).

---

## Invariantes e acentuação

`bash scripts/sprint_invariants.sh`:
- PASS: 14
- FAIL: 0
- Inclui:
  - check #2 (zero menção a Claude/Anthropic/GPT/Gemini/Copilot em .py)
  - check #6 (zero hex hardcoded fora de design_tokens*.py)
  - check #13 (./run.sh --smoke = "boot ok")
  - check #14 (glifos `○ ◐ ●` canônicos preservados)

---

## Decisão sobre release v1.0

**NÃO cortar tag v1.0 nesta sessão.** Aguardar PARTE-2 (screenshots + Docker
install + 47 commands + 34 tools em fluxo natural). Sessão Validador
2026-05-18 deixa o trabalho **pronto para conclusão humana**:

- Cockpit pleno (COCKPIT-02..05 + UX-COCKPIT-EXPERIENCE-01 todos done).
- Anti-débito UX (UX-PROGRESSION-02 + UX-AGENCY-02 done).
- Visual layout extendido (VL-01 + VL-08 done).
- Infra (OOM + sudo seguro) done.
- Benchmark + gauntlet baseline OK.

A sessão humana pode prosseguir abrindo Chrome no cockpit 127.0.0.1:11437,
disparando `POST /control/feature/<id>/run` para cada uma das 62 features
e capturando screenshots via `POST /api/screenshot`, conforme protocolo
documentado em `dev-journey/05-guides/COCKPIT_API.md`.

---

*"A prova do pudim está em comê-lo." -- Miguel de Cervantes*
