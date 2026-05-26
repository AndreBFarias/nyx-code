# SPRINT 258 — PROXY-HANDLE-CHAT-REFACTOR-01

## 0. SPEC

```yaml
sprint:
  id: PROXY-HANDLE-CHAT-REFACTOR-01
  title: "Extrair _retry_with_hint dos 3 guardrails duplicados em handle_chat; mover _OOM_DEGRADED para app[state]"
  onda: 31
  prioridade: BAIXA
  tipo: Refactor
  dependencias: []
  desbloqueia: []

  touches:
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/proxy.py
      reason: "handle_chat tem 245 linhas; os 3 guardrails LANG-ENFORCE/IDENTITY-ENFORCE/MEMORY-INTENT tem estrutura quase identica (~140 linhas: append assistant+user hint, re-post, checar resultado). _OOM_DEGRADED e global mutavel enquanto o resto do estado migrou para app['state'] (PROXY-NUMGPU-RUNTIME-01) -- incoerencia."
  creates: []
  removes: []

  forbidden:
    - "Mudar comportamento observavel: think adaptativo, num_predict por intent, OOM degradation em 4 camadas, os 3 guardrails devem produzir resultado identico"
    - "Quebrar o fail-safe anti-oscilacao (OOM degradado nao reanima GPU)"
    - "Introduzir race: se _OOM_DEGRADED virar app['state'], garantir leitura/escrita consistente no handler async"
    - "Adicionar emoji ou mencao a IA externa"

  tests:
    - cmd: "./run.sh --gauntlet --only proxy"
      timeout: 120
      deve_passar: true
    - cmd: "./run.sh --smoke"
      timeout: 10
      deve_passar: true

  acceptance_criteria:
    - "handle_chat fica < 120 linhas; helper _retry_with_hint(session, ollama_body, hint_user, validate_fn) extraido e reutilizado pelos 3 guardrails"
    - "_OOM_DEGRADED migrado para state['oom_degraded']; handle_tune e handle_stats leem de state"
    - "Gauntlet --only proxy 7/7 identico antes e depois (P-01..P-09)"
    - "ruff All checks passed; acentuacao rc=0"
```

---

# Sprint 258 — PROXY-HANDLE-CHAT-REFACTOR-01

**Status:** PENDENTE
**Data criacao:** 2026-05-25

## Contexto

Auditoria de 2026-05-25 da `nyx/proxy.py`: `handle_chat` (linhas 531-776, 245
linhas) concentra OOM retry + 3 guardrails de saida. Os guardrails LANG-ENFORCE-01,
IDENTITY-ENFORCE-01 e MEMORY-INTENT-ENFORCE-01 repetem o mesmo padrao:

1. condicao de gating por intent;
2. monta retry_body = dict(ollama_body) + append {assistant: content} + {user: hint};
3. re-post para /api/chat;
4. valida o resultado (is_pt_br / nao mentions_provider / chamou write_memory);
5. troca `result` se recuperou, senao passa adiante. Cap 1 retry.

~140 linhas de codigo altamente similar. Alem disso, `_OOM_DEGRADED` (linha 79)
e modulo-global mutavel, enquanto `num_gpu`/`oom_recovery_count` migraram para
`app['state']` em PROXY-NUMGPU-RUNTIME-01 — incoerencia de design.

## Solucao

1. `_retry_with_hint(session, base_body, hint_text, validate, transform_result=None)`:
   helper async que encapsula passos 2-5. Cada guardrail vira ~10 linhas.
2. Mover `_OOM_DEGRADED` para `state['oom_degraded']` (default False em
   `_on_startup` e `main()`). Atualizar `handle_chat`, `handle_tune`, `handle_stats`.
   Nota: aiohttp e single-threaded no event loop; mutacao de state e segura entre
   awaits desde que nao haja await entre leitura e escrita critica (documentar).

Refactor puro: zero mudanca de comportamento. Gauntlet --only proxy e a rede de
seguranca (P-02 think=false, P-07 tool_calls, P-09 nyx_reasoning).

## Acceptance

- [ ] handle_chat < 120 linhas.
- [ ] 3 guardrails usam _retry_with_hint.
- [ ] state['oom_degraded'] substitui o global.
- [ ] Gauntlet --only proxy 7/7 antes == depois.

## Proof-of-work

```
# ANTES
./run.sh --gauntlet --only proxy   # 7/7
wc -l nyx/proxy.py ; grep -n "def handle_chat" nyx/proxy.py
# DEPOIS
./run.sh --gauntlet --only proxy   # 7/7 identico
python3 -m ruff check nyx/proxy.py # All checks passed
```
