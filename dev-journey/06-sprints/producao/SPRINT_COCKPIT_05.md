# SPRINT COCKPIT-05 — Control API: Claude/MCP orquestra Cockpit headlessly

## 0. SPEC (machine-readable)

```yaml
sprint:
  id: COCKPIT-05
  title: "Control API: endpoints POST que permitem Claude/Chrome MCP disparar gauntlet, ler estado, capturar evidência via HTTP"
  onda: 23
  bloco: 23.3 Cockpit
  prioridade: MÉDIA
  tipo: Feature+API
  dependencias: [COCKPIT-04]
  desbloqueia: [UX-COCKPIT-EXPERIENCE-01, VALIDATE-FINAL-01]

  touches:
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/cockpit/server.py
      reason: "Adiciona endpoints /control/* expostos para automação"

  creates:
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/dev-journey/07-reports/COCKPIT_API.md
      reason: "Documentação da API control: como Claude/Chrome MCP usa cada endpoint"

  removes: []

  n_to_n_pairs: []

  forbidden:
    - "Endpoint /control sem autenticação loopback (já vem do COCKPIT-01)"
    - "Spawn de gauntlet completo sem timeout (cap 600s)"
    - "Bloqueio de operações concorrentes silenciosas (deve retornar 429 'busy')"
    - "Hardcoded de IDs de feature; deve consultar REGISTRY.yaml"

  tests:
    - cmd: "curl -X POST http://127.0.0.1:11437/control/gauntlet/run | jq .job_id"
      timeout: 10
      deve_passar: true
    - cmd: "curl http://127.0.0.1:11437/control/gauntlet/status/<job_id> | jq .state"
      timeout: 10
      deve_passar: true
    - cmd: "curl -X POST http://127.0.0.1:11437/control/repl/send -d '{\"text\":\"hi\\n\"}' -H 'Content-Type: application/json'"
      timeout: 10
      deve_passar: true
    - cmd: "bash scripts/sprint_invariants.sh"
      timeout: 60
      deve_passar: "FAIL_AFTER <= FAIL_BEFORE"

  acceptance_criteria:
    - "POST /control/gauntlet/run — dispara gauntlet completo; retorna job_id"
    - "POST /control/feature/{id}/run — dispara gauntlet single (alias de /api/features/{id}/run)"
    - "GET /control/gauntlet/status/{job_id} — retorna state, progress, log_tail"
    - "POST /control/repl/send — envia texto para REPL ativo (PTY write)"
    - "GET /control/repl/snapshot — retorna últimas N linhas do REPL em texto"
    - "COCKPIT_API.md documenta cada endpoint com curl exemplo"
    - "Chrome MCP consegue: rodar gauntlet, monitorar progresso, ler estado, capturar PNG, sem mouse/click manual"
    - "Acentuação PT-BR"
```

---

**Status:** PENDENTE
**Data criação:** 2026-05-15
**Modelo obrigatório:** claude-opus-4-7 (sem subagentes)

---

# Sprint COCKPIT-05

## Endpoints

| Verbo | Path | Propósito |
|-------|------|-----------|
| POST | /control/gauntlet/run | Roda gauntlet completo |
| POST | /control/feature/{id}/run | Roda 1 feature |
| GET | /control/gauntlet/status/{job_id} | Estado de job |
| POST | /control/repl/send | Texto → PTY |
| GET | /control/repl/snapshot | Últimas N linhas do REPL |
| GET | /control/registry | REGISTRY.yaml completo |

## Documentação `COCKPIT_API.md` (exemplo)

```markdown
# Cockpit Control API — uso por Claude via Chrome MCP

## Disparar gauntlet completo

curl -X POST http://127.0.0.1:11437/control/gauntlet/run
# → {"job_id": "abc-123", "state": "iniciado"}

## Monitorar progresso

curl http://127.0.0.1:11437/control/gauntlet/status/abc-123
# → {"state": "rodando", "progress": "8/18", "log_tail": "..."}

## Enviar comando ao REPL

curl -X POST http://127.0.0.1:11437/control/repl/send \
  -H 'Content-Type: application/json' \
  -d '{"text": "/help\n"}'

## Capturar evidência

curl -X POST http://127.0.0.1:11437/api/screenshot \
  -F feature_id=I-01 -F img=@<canvas.png>
```

## Verificação

```bash
./run.sh --cockpit
# Claude (via Chrome MCP):
# 1. navigate http://127.0.0.1:11437
# 2. POST /control/gauntlet/run
# 3. poll /control/gauntlet/status até state=completo
# 4. read /control/registry para ver REGISTRY atualizado
# 5. capture evidência via /api/screenshot
```

---

*"API é a linguagem em que dois agentes se reconhecem." -- anônimo*
