# SPRINT GAUNTLET-RB03-OOM-FLAG-FIX-01 -- RB-03 testa flag de OOM que migrou de lugar (falso-negativo no gate)

## 0. SPEC (machine-readable)

```yaml
sprint:
  id: GAUNTLET-RB03-OOM-FLAG-FIX-01
  title: "RB-03 (nyx_gauntlet.py:~4790) testa `hasattr(mod, '_OOM_DEGRADED')` mas o refactor PROXY-HANDLE-CHAT (commit 113e578) migrou o flag para `app['state']['oom_degraded']` -> hasattr sempre False -> RB-03 e um falso-negativo permanente no gate. RB-05 (~4892) tem o mesmo idiom frágil com a string antiga."
  onda: 46
  bloco: "46 -- Saneamento de CI & Working Tree + achados da Onda de Validação 1"
  prioridade: MEDIA
  tipo: Bugfix / Teste (gate de produção)
  dependencias: []
  desbloqueia: []

  touches:
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/scripts/gauntlet/nyx_gauntlet.py
      reason: "RB-03 (~linha 4790) usa `hasattr(mod, '_OOM_DEGRADED')` para 'provar' a feature de degradação OOM; o flag de módulo `_OOM_DEGRADED` foi removido no refactor (commit 113e578) e migrado para o estado da app `app['state']['oom_degraded']` (documentado em proxy.py:86). hasattr -> sempre False -> a subcondição falha de mentira. RB-05 (~4892) referencia a mesma string antiga numa heurística cap-counter (passou por acaso). Atualizar a detecção para a arquitetura pos-refactor."
      linhas_alvo: "~4780-4900 (RB-03 e RB-05; confirmar via grep _OOM_DEGRADED)"

  creates: []
  removes: []

  forbidden:
    - "Mascarar a subcondição (ex.: trocar o assert por `True`) -- tem que detectar a feature REAL de degradação OOM no lugar novo"
    - "Mudar a feature de degradação OOM em si (e do proxy, esta correta; so o TESTE esta obsoleto)"
    - "Quebrar as outras subcondições de RB-03 (detecta/sem_fp/retry/patterns_kv) que ja passam"
    - "Zero mocks (ADR-010): a detecção deve refletir o código real do proxy"

  tests:
    - cmd: "grep -n '_OOM_DEGRADED' scripts/gauntlet/nyx_gauntlet.py nyx/proxy.py"
      timeout: 30
      esperado: "após o fix, o gauntlet não depende mais do símbolo de módulo inexistente; proxy usa app['state']['oom_degraded']"
    - cmd: "./run.sh --gauntlet --only robustez_boot"
      timeout: 300
      esperado: "RB-01..07 PASS, incluindo RB-03 agora por motivo REAL (detecta a feature no lugar certo) e RB-05 intacto"
    - cmd: "bash scripts/sprint_invariants.sh"
      timeout: 180
      esperado: "14/14 PASS"

  acceptance_criteria:
    - "RB-03 detecta a feature de degradação OOM via o mecanismo atual (app state / a função de oom_recovery do proxy), não via `hasattr(mod, '_OOM_DEGRADED')`"
    - "RB-03 PASSA por motivo verdadeiro (e FALHARIA se a feature fosse removida -- testar o caminho negativo conceitualmente)"
    - "RB-05 não depende mais da string `_OOM_DEGRADED` morta"
    - "robustez_boot 7/7; invariantes 14/14; spec -> concluidos/"
```

---

**Status:** CONCLUIDA (6c47526)
**Data criação:** 2026-06-24
**Origem:** Onda de Validação 1 (achado #4, GAP). O full gauntlet acusou RB-03 FAIL; investigação mostrou que a subcondição `hasattr(mod, "_OOM_DEGRADED")` e um falso-negativo desde o refactor 113e578 (flag virou estado da app).
**Modelo obrigatorio:** modelo principal local, sem subagentes; implementação direta

---

## Problema

`scripts/gauntlet/nyx_gauntlet.py`, RB-03 (~4790): para "provar" que o proxy degrada de GPU para CPU em OOM, faz `hasattr(mod, "_OOM_DEGRADED")`. Mas o refactor PROXY-HANDLE-CHAT-REFACTOR-01 (commit `113e578`) removeu o flag de módulo `_OOM_DEGRADED` e passou a guardar o estado em `app["state"]["oom_degraded"]` (ver proxy.py:86 e os sets em ~571/578/682). Logo `hasattr` retorna sempre False e a subcondição falha por motivo errado -- um falso-negativo permanente no gate de produção (mascara o sinal real). RB-05 (~4892) também cita a string antiga numa heurística (passou por acaso).

---

## Causa-raiz

O teste foi escrito contra a API antiga (flag de módulo) e não foi atualizado quando o refactor moveu o estado para a app. Acoplamento do teste a um detalhe de implementação que mudou.

---

## Solução proposta

Atualizar a detecção de RB-03 (e o idiom de RB-05) para a arquitetura atual. O executor deve ler RB-03/RB-05 + como o proxy expõe a degradação hoje e escolher um sinal estável e REAL, por exemplo:
- verificar que `proxy.py` define/inicializa `app["state"]["oom_degraded"]` e que existe a função de oom_recovery que o seta; OU
- exercitar o caminho (sem mock) e ler o estado resultante.
O objetivo: RB-03 passa porque a feature EXISTE, e falharia se ela sumisse.

---

## Proof-of-work esperado

```bash
grep -n "_OOM_DEGRADED\|oom_degraded" scripts/gauntlet/nyx_gauntlet.py nyx/proxy.py
./run.sh --gauntlet --only robustez_boot      # RB-01..07 PASS (RB-03 por motivo real)
bash scripts/sprint_invariants.sh              # 14/14 PASS
python3 ~/.config/zsh/scripts/validar-acentuacao.py --paths scripts/gauntlet/nyx_gauntlet.py
/home/andrefarias/.local/bin/ruff check scripts/gauntlet/nyx_gauntlet.py
```

---

## Critério binário de aceite

- [x] RB-03 detecta a feature no lugar atual (app state / oom_recovery), não `hasattr(mod,'_OOM_DEGRADED')`
- [x] RB-03 passa por motivo verdadeiro; RB-05 sem a string morta
- [x] robustez_boot 6/6 (a fase robustez_boot tem RB-01..06, sem RB-07); invariantes 14/14, ruff/acento OK; spec -> concluidos/

---

## Riscos

| Risco | Mitigação |
|-------|-----------|
| Nova detecção também frágil a refactor | Preferir exercitar o comportamento/estado a inspecionar símbolo interno; se inspecionar, mirar `app['state']` que e o contrato atual |
| RB-05 quebrar ao remover a string | Confirmar o que RB-05 realmente conta; ajustar o idiom sem alterar o que ele mede |

---

*"Um alarme que toca sempre (ou nunca) e pior que nenhum alarme." -- anonimo*
