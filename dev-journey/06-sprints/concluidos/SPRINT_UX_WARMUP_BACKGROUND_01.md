# SPRINT 236 — UX-WARMUP-BACKGROUND-01

## 0. SPEC (machine-readable)

```yaml
sprint:
  id: UX-WARMUP-BACKGROUND-01
  title: "warmup_model em background paraleliza com prompt 'Retomar última sessão?'"
  onda: 31
  prioridade: MÉDIA
  tipo: Refactor
  dependencias: [INFRA-PRELOAD-VIA-PROXY-01]
  desbloqueia: []

  touches:
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/run.sh
      reason: "warmup_model bloqueante 8s antes do CLI; usuário esperava warmup terminar para ver prompt"
      linhas_alvo: "623-628"
  creates: []
  removes: []

  forbidden:
    - "Quebrar logs/boot.log (warmup já usava log_boot)"
    - "Tocar em --gauntlet ou --smoke (skip preservado)"
    - "Quebrar shutdown ordenado (warmup é fire-and-forget)"

  tests:
    - cmd: "./run.sh --smoke"
      timeout: 10
      deve_passar: true
    - cmd: "bash scripts/sprint_invariants.sh"
      timeout: 30
      deve_passar: true

  acceptance_criteria:
    - "warmup_model rodado em background com & + disown"
    - "Próximo `./run.sh` interativo: prompt 'Retomar última sessão?' aparece imediatamente"
    - "Modelo aquece em paralelo enquanto usuário responde s/N"
    - "Primeira mensagem real serializada pelo Ollama se warmup não terminou (sem erro)"
    - "Smoke + invariantes preservados"
```

---

# Sprint 236 — UX-WARMUP-BACKGROUND-01

**Status:** CONCLUIDA
**Data criação:** 2026-05-25
**Data conclusão:** 2026-05-25
**Modelo obrigatório:** claude-opus-4-7 (sem subagentes)

---

## Contexto

Após sprint 235 remover a pré-carga direta, o boot ficou limpo (sem warning visível), mas o usuário observou um problema UX residual:

> "essa mensagem deveria ser enviado antes pra ele, não? pra ficar rápido de verdade."

Fluxo bloqueante atual:
```
boot ─→ warmup (8s, BLOQUEANTE) ─→ CLI ─→ prompt "Retomar?" ─→ usuário responde
```

Usuário só vê o prompt depois de 8 segundos esperando warmup. Mas a interação humana de ler/digitar s/N leva 1-3 segundos — tempo perdido onde o modelo poderia estar aquecendo em paralelo.

## Solução

Rodar `warmup_model` em **background** (`&` + `disown`). Boot prossegue imediatamente para o CLI. Prompt aparece sem espera. Enquanto usuário lê e responde, o modelo aquece via proxy.

```
boot ─→ warmup (background, 8s) ──┐
       │                            │
       └─→ CLI ─→ prompt aparece ──→ usuário responde s/N ─→ envia 1ª msg
                                                            ↑
                                                  warmup já terminou (na maioria dos casos)
```

Se a primeira mensagem chegar antes do warmup terminar, Ollama serializa a request (não dá erro). Pior caso: marginalmente mais lento. Melhor caso (típico): instantâneo.

## Fix aplicado

```bash
# Antes:
if [ "$GAUNTLET" -eq 0 ]; then
    warmup_model
fi

# Depois:
if [ "$GAUNTLET" -eq 0 ]; then
    warmup_model > /dev/null 2>&1 &
    WARMUP_PID=$!
    disown "$WARMUP_PID" 2>/dev/null || true
fi
```

`disown` remove o PID da jobs table (paridade com `start_ollama` linha 311 e `start_proxy` linha 597). Sem isso, bash poderia emitir "Done" ou "Killed" no shell pai. Output do `warmup_model` já vai para `logs/boot.log` via `log_boot`, então `> /dev/null 2>&1` só silencia warnings raros.

## Proof-of-work

```
./run.sh --smoke    → boot ok exit 0
bash scripts/sprint_invariants.sh → PASS=14/14 FAIL=0
```

Validação interativa final (TTY real):
- Próximo `./run.sh` deve mostrar prompt `Retomar última sessão?` **imediatamente** após `Iniciando Nyx CLI...`
- Em paralelo, `tail -f logs/boot.log` mostrará `Aquecendo modelo... Modelo aquecido (warmup duplo, Ns)` (não no stdout)
- Primeira mensagem real: latência típica baixa (modelo já pronto)

## Riscos

| Risco | Mitigação |
|---|---|
| Warmup não terminar antes da 1ª mensagem do usuário | Ollama serializa requests; sem erro, só latência marginal extra |
| Warmup falhar silenciosamente | INFRA-OOM-RETRY-STEP-01 do proxy absorve OOM; CPU fallback funciona |
| Shutdown rápido (Ctrl+Q antes do warmup terminar) | warmup é fire-and-forget; trap cleanup do run.sh mata Ollama + proxy juntos; warmup termina ou é interrompido junto |

---

*"Tempo do humano é precioso. Tempo da máquina é elástico. Paralelize." — princípio UX*
