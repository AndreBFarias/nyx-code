# SPRINT ONDA-38-C — ONBOARDING-IMPROVE-02

## 0. SPEC (machine-readable)

```yaml
sprint:
  id: ONBOARDING-IMPROVE-02
  title: "Melhorar o onboarding padrão (revisar os 7 passos do wizard + os 5 steps do tutorial)"
  onda: 38
  prioridade: MEDIA
  tipo: UX
  depende_de_ordem: roda DEPOIS de ONBOARDING-REPLAY-FLAG-01 (ambas tocam onboarding.py; NUNCA em paralelo)
  touches:
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/agent/onboarding.py
      reason: "revisar microcopy/ordem dos 7 passos de run_first_run_wizard (L174-244) e os 5 steps de _build_steps (L101-124)"
  acceptance_criteria:
    - "os 7 passos do wizard ficam coerentes (numeração, prompts claros, defaults explícitos)"
    - "os 5 steps de _build_steps ficam coerentes com o estado atual do produto"
    - "varredura anti-débito do MASTER por sprints de onboarding ABERTAS feita e registrada"
    - "smoke boot ok + invariantes 14/14"
```

---

**Status:** CONCLUIDA (2026-06-01 — polimento mínimo objetivo: docstring de run_first_run_wizard sincronizada com ONBOARDING-REPLAY-FLAG-01 (default nome persistido->git->visitante; nota force/replay). Anti-débito re-confirmado: ZERO sprint de onboarding aberta no MASTER (IDs todos CONCLUIDA/SUPERSEDED). Coerência dos 5 steps verificada: /resume,/tools,/quit,/help (17 refs) e Shift+Tab/bypass (51 refs) válidos. Achado registrado (não removido, GUIDE §3): _build_steps/run_first_time_tutorial é tutorial legado (removível Onda 26 após consumers migrarem). Proof: smoke boot ok, invariantes 14/14, acentuação exit 0.)
**Data criação:** 2026-06-01
**Modelo obrigatório:** sem subagentes (Read/Grep/Glob direto)

---

## Contexto

O onboarding tem duas superfícies: o wizard interativo de 7 passos (`run_first_run_wizard`, `onboarding.py:174-244`) e o tutorial textual de 5 steps (`_build_steps`, `onboarding.py:101-124`). Esta sprint revisa o microcopy, a numeração e a coerência de ambos com o estado atual do produto (pós-migração Textual, pós-aesthetics, pós-vision). Tipo UX puro.

## Escopo (touches autorizados)

- Arquivos a modificar:
  - `/home/andrefarias/Desenvolvimento/Nyx-Code/nyx/agent/onboarding.py`
- Arquivos a criar: nenhum
- Arquivos NÃO a tocar: nenhum dos 6 protegidos do check #14 (onboarding.py não está no conjunto).

## Anti-débito (varredura do MASTER — resultado já apurado pelo planejador)

A instrução pedia varrer `SPRINT_ORDER_MASTER.md` por sprints de onboarding ABERTAS/PENDENTES para dobrá-las nesta. Varredura feita com `rg -ni onboarding dev-journey/06-sprints/SPRINT_ORDER_MASTER.md`:

- ONBOARDING-01 (L313): CONCLUIDA.
- P10-B (L112): CONCLUIDA.
- VALIDATE-FINAL-01 (L316): SUPERSEDED.
- TUI-REDESIGN-26-05 (L968), TUI-REDESIGN-25-04/05/06 (L1004-1006): todas CONCLUIDAS.
- DOC-CHANGELOG-V1RC-01 (L386): CONCLUIDA.

Conclusão: ZERO sprints de onboarding ABERTAS/PENDENTES no MASTER. Não há débito a dobrar. Esta sprint fica restrita à revisão dos 7 passos + 5 steps existentes. O executor deve RE-confirmar a varredura no momento da execução (o coordenador pode ter aberto sprints novas entre a redação e a execução) e, se aparecer alguma sprint de onboarding aberta, dobrá-la aqui ou registrar como achado anti-débito.

## Acceptance criteria

1. Os 7 passos do wizard (`run_first_run_wizard`) têm prompts claros, numeração consistente `NN/07` e defaults explícitos entre colchetes.
2. Os 5 steps de `_build_steps` refletem o produto atual (sem menção a recursos removidos; coerência com Textual default).
3. A docstring do wizard (L175-192) permanece sincronizada com a sequência efetiva de passos.
4. Varredura anti-débito do MASTER re-confirmada na execução e registrada no proof-of-work.
5. `./run.sh --smoke` imprime `boot ok`, exit 0.
6. `bash scripts/sprint_invariants.sh` PASS 14/14, FAIL 0.

## Invariantes a preservar

- Não-tty safe: o gate `if not sys.stdin.isatty(): mark_done(); return` (`onboarding.py:193-195`) e os timeouts de `_timed_input` (60s SIGALRM) devem permanecer — onboarding NUNCA pode travar em pipe/CI.
- Persistência: a revisão NÃO muda o formato de `~/.nyx/config.toml`; só microcopy/ordem.
- Compat com ONBOARDING-REPLAY-FLAG-01: se a sprint B já introduziu o parâmetro `force`, a revisão dos passos deve preservá-lo (por isso a ordem B antes de C).
- Check #4 acentuação PT-BR em todo texto user-facing do wizard.
- GUIDE.md §3: mudança cirúrgica de microcopy; não refatorar a mecânica do `menu_wizard`.

## Plano de implementação

1. Ler integralmente `onboarding.py:101-244` e mapear: os 5 tuples de `_build_steps` e os 7 passos do wizard (passo 01 nome local + passos 02-07 delegados a `scripts.menu_wizard.main`).
2. Revisar o texto de cada um dos 5 steps de `_build_steps` para coerência com o produto atual (ex.: confirmar que `/help`, `/tools`, `/quit`, `/resume`, Shift+Tab bypass continuam corretos via `rg` nos handlers de comando).
3. Revisar prompts/defaults do passo 01/07 (nome) no wizard; conferir que a docstring (L175-192) descreve exatamente o que o código faz.
4. Para os passos 02-07 (delegados a `menu_wizard`), revisar apenas o que `onboarding.py` controla (env vars `NYX_MENU_EMIT`/`NYX_MENU_FIRST_RUN`, mensagens de cancelamento L230). NÃO alterar `scripts/menu_wizard.py` (fora de escopo — abrir achado se precisar mudança lá).
5. Rodar smoke + invariantes + acentuação.

## Testes

- Reusar/estender o teste de onboarding existente (localizar via `rg -l onboarding tests/`). Validar que `_build_steps("X")` retorna 5 tuples e que cada texto está sem emoji/acentuação correta.
- Baseline: FAIL_BEFORE = 0, esperado FAIL_AFTER = 0.

## Proof-of-work esperado

- Diff final de `onboarding.py`.
- Runtime real:
  - Wizard: rodar o wizard completo (via `./run.sh --onboarding` se a sprint B já estiver concluída, senão removendo `~/.nyx/.first_run_done` temporariamente em ambiente de teste) e comprovar os 7 passos coerentes. Capturar a saída.
  - Smoke: `./run.sh --smoke` (`boot ok`, exit 0)
  - Invariantes: `bash scripts/sprint_invariants.sh` (14/14)
- Re-varredura anti-débito: colar a saída de `rg -ni onboarding dev-journey/06-sprints/SPRINT_ORDER_MASTER.md` no proof, confirmando que nada aberto ficou de fora.
- Acentuação periférica: `python3 /home/andrefarias/.config/zsh/scripts/validar-acentuacao.py --paths nyx/agent/onboarding.py` exit 0.
- Hipótese verificada: `rg -n "_build_steps|run_first_run_wizard|/07" nyx/agent/onboarding.py`.

## Riscos e não-objetivos

- Não-objetivo: alterar `scripts/menu_wizard.py`, a mecânica de persistência, ou o conjunto de aesthetics/schemas. Só microcopy/coerência.
- Risco de ordem: C DEPOIS de B (compartilham `onboarding.py`). NUNCA paralelo.
- Risco: introduzir regressão no gate não-tty. Mitigação: preservar L193-195 e os timeouts.

## Referências

- BRIEF: `/home/andrefarias/Desenvolvimento/Nyx-Code/VALIDATOR_BRIEF.md`
- MASTER: `/home/andrefarias/Desenvolvimento/Nyx-Code/dev-journey/06-sprints/SPRINT_ORDER_MASTER.md` (varredura anti-débito — não modificar)
- Depende de: ONBOARDING-REPLAY-FLAG-01 (bloco B)

---

*"Tutorial sem tutorial: a primeira experiência ensina sem pedir licença."*
