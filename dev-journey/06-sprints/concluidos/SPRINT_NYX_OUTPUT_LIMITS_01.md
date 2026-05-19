# SPRINT NYX-OUTPUT-LIMITS-01 — Tirar limite de caracteres em outputs

## 0. SPEC

```yaml
sprint:
  id: NYX-OUTPUT-LIMITS-01
  title: "num_predict adaptativo (sem cap fixo) para chat e tool calls"
  onda: 24
  bloco: 24.9 Memória contínua
  prioridade: ALTA
  tipo: Feature
  dependencias: [PERF-INFERENCE-01]
  desbloqueia: [tarefas que precisam de resposta longa (código, planos, refactor)]
  origem: "Pedido do usuario 2026-05-18: 'temos que tirar a limitacao de caracteres do projeto. Digo em outputs.'"

  touches:
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/config/defaults.py
      reason: "Substituir NUM_PREDICT_CHAT/TOOL fixos por funcao adaptativa"
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/proxy.py
      reason: "Aplicar adaptive num_predict conforme intent + tipo de tool"

  forbidden:
    - "Permitir num_predict=infinito (proteger contra runaway)"
    - "Quebrar PERF-INFERENCE-01 (cold start <8s precisa cap inicial)"
    - "Ignorar max_tokens explicito do request"

  tests:
    - cmd: "echo 'oi' | ./run.sh --headless --no-resume-prompt"
      timeout: 60
      deve_passar: "resposta curta retorna ok (P50 <2s)"
    - cmd: "echo 'explique recursividade em 500 palavras' | ./run.sh --headless --no-resume-prompt"
      timeout: 120
      deve_passar: "resposta longa retorna sem truncate"
    - cmd: "bash scripts/sprint_invariants.sh"
      timeout: 60
      deve_passar: "14/14"

  acceptance_criteria:
    - "Defaults.py expoe NUM_PREDICT_BY_INTENT dict:"
    - "  saudacao=80, comando=120, chat=512, tool=2048, code=4096, plan=8192"
    - "proxy.py classifica intent (ja faz via classify_intent) e mapeia"
    - "Override via env NYX_NUM_PREDICT_OVERRIDE=N (debug)"
    - "Override via max_tokens explicito do request (preserva comportamento atual)"
    - "Resposta longa nao trunca em 80 tokens para chat se modelo precisa"
    - "Detector de truncate: se ultimo char e ',' ou nao termina sentenca, log warning"
    - "Smoke + invariantes 14/14"
```

---

# Sprint NYX-OUTPUT-LIMITS-01

**Status:** CONCLUIDA
**Data criação:** 2026-05-18
**Data conclusão:** 2026-05-19
**Modelo obrigatório:** claude-opus-4-7

---

## Contexto

Hoje `nyx/config/defaults.py:77`:
```python
NUM_PREDICT_CHAT: int = 80
NUM_PREDICT_TOOL: int = 512
```

Cap agressivo (PERF-INFERENCE-01) para CPU-bound em RTX 3050 4GB.
Trade-off: chat curto rapido, mas:
- Explicacoes longas truncam meio caminho
- Planos detalhados nao cabem
- Codigo gerado eh cortado
- Documentacao tecnica fica pela metade

Usuario validou via uso real (sessao 2026-05-18): respostas curtas
demais para tarefas complexas.

## Solucao proposta

### `nyx/config/defaults.py`

```python
# Substitui os 2 fixos
NUM_PREDICT_BY_INTENT: dict[str, int] = {
    "saudacao":  80,    # oi/ola -> respondem em <50 tok
    "comando":   120,   # slash sem LLM, mas alguns hibridos
    "chat":      512,   # explicacao curta
    "tool":      2048,  # tool call + breve resumo
    "code":      4096,  # gerar codigo (write_file, edit_file)
    "plan":      8192,  # /plan, refactor amplo
    "default":   1024,
}

def num_predict_for(intent: str, override: int | None = None) -> int:
    """Resolve num_predict por intent; respeita override (env ou request)."""
    if override is not None:
        return min(override, 8192)  # hard cap pra evitar runaway
    import os
    env_override = os.environ.get("NYX_NUM_PREDICT_OVERRIDE")
    if env_override and env_override.isdigit():
        return min(int(env_override), 8192)
    return NUM_PREDICT_BY_INTENT.get(intent.lower(), NUM_PREDICT_BY_INTENT["default"])
```

### `nyx/proxy.py`

```python
# Substituir:
result["options"]["num_predict"] = _NUM_PREDICT_TOOL  # ou _CHAT

# Por:
from nyx.config.defaults import num_predict_for
intent = classify_intent(prompt)
override = body.get("max_tokens") or body.get("max_completion_tokens")
result["options"]["num_predict"] = num_predict_for(intent, override)
```

### Detector de truncate

`nyx/agent/loop/_iteration.py` apos receber resposta:

```python
def _detect_truncate(self, text: str) -> bool:
    if not text:
        return False
    stripped = text.rstrip()
    # Heuristica: termina com virgula, sem ponto final, ou termina abruptamente
    if stripped.endswith((",", "-", "(")) and len(stripped) > 100:
        logger.warning("possivel truncate detectado: '%s...'", stripped[-50:])
        return True
    return False
```

Se truncate, log warning + sugerir num_predict maior na proxima.

### CLI flag

`run.sh`:
```bash
--num-predict)
    export NYX_NUM_PREDICT_OVERRIDE="$2"
    shift 2 ;;
```

Permite debug rapido: `./run.sh --num-predict 4096`.

## Critério binário

- [ ] num_predict_for() implementada
- [ ] proxy.py usa por intent
- [ ] NYX_NUM_PREDICT_OVERRIDE funciona
- [ ] max_tokens do request preservado
- [ ] Detector de truncate ativo
- [ ] Hard cap 8192 (anti-runaway)
- [ ] PERF-INFERENCE-01 nao regride (oi <2s P50)
- [ ] Smoke + invariantes 14/14
- [ ] Commit `feat(NYX-OUTPUT-LIMITS-01): num_predict adaptativo por intent`

---

## Riscos

| Risco | Mitigacao |
|---|---|
| Latencia explode em CPU-bound | Cap 8192 hard; gauntlet perf valida P95 |
| Modelo gera muita "thinking" antes da resposta | qwen2.5-coder:3b nao tem thinking; qwen3:4b ja sofre (ADR-031) |
| Cache de contexto cresce mais rapido | CTX-01 compactacao trata |

---

*"Capa que aperta sufoca; capa que solta veste." -- NYX-OUTPUT-LIMITS-01*
