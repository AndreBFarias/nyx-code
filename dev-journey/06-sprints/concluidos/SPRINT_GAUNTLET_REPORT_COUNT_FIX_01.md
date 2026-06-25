# SPRINT GAUNTLET-REPORT-COUNT-FIX-01 -- header do GAUNTLET_REPORT soma SKIP como pass

## 0. SPEC (machine-readable)

```yaml
sprint:
  id: GAUNTLET-REPORT-COUNT-FIX-01
  title: "O header do GAUNTLET_REPORT.md (e/ou o tally exibido) conta o(s) SKIP como pass: mostra 232/235 (99%) enquanto o checkpoint real e 231 pass / 3 fail / 1 skip -- numero inflado ao operador, mascara o sinal de saude"
  onda: 46
  bloco: "46 -- Saneamento de CI & Working Tree + achados da Onda de Validação 1"
  prioridade: BAIXA
  tipo: Bugfix / Relatorio (observabilidade)
  dependencias: []
  desbloqueia: []

  touches:
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/scripts/gauntlet/nyx_gauntlet.py
      reason: "a geracao do header/sumario do GAUNTLET_REPORT.md (e o tally impresso) computa passados de forma que inclui SKIP no numerador (232/235) em vez de reportar pass/fail/skip separados (231/3/1). Localizar a contagem do sumario e separar SKIP de PASS."
      linhas_alvo: "função que monta o header/tally do report (grep por 'passed'/'/235'/'%' e por '_add_skip'/SKIP)"

  creates: []
  removes: []

  forbidden:
    - "Mudar a logica de PASS/FAIL/SKIP por teste (so a AGREGACAO do sumario esta errada)"
    - "Esconder os SKIP -- eles devem aparecer no sumario como categoria própria, não somados a pass"
    - "Quebrar o gate (APROVADO exige 100% dos não-skip; SKIP não conta como fail nem como pass)"

  tests:
    - cmd: "./run.sh --gauntlet (ou subset que gere SKIP, ex.: K-08 em ambiente com VRAM externa)"
      timeout: 1200
      esperado: "o header/tally mostra pass/fail/skip separados; o numerador de pass não inclui skip"
    - cmd: "comparar o header do GAUNTLET_REPORT.md com o checkpoint.json (contagens batem)"
      timeout: 60
      esperado: "header coerente com checkpoint (sem +1 de skip)"
    - cmd: "bash scripts/sprint_invariants.sh"
      timeout: 180
      esperado: "14/14 PASS"

  acceptance_criteria:
    - "Sumario/header do report mostra PASS, FAIL e SKIP separados; pass não inclui skip"
    - "Numeros do header batem com o checkpoint.json"
    - "Gate inalterado (SKIP não vira pass nem fail)"
    - "Invariantes 14/14; spec -> concluidos/"
```

---

**Status:** CONCLUIDA
**Data criação:** 2026-06-25
**Origem:** Onda de Validação 1 (achado #5, INFO). O full gauntlet exibiu 232/235 (99%) no header enquanto o checkpoint registrou 231 pass / 3 fail / 1 skip -- o SKIP foi somado ao pass.
**Modelo obrigatorio:** modelo de fronteira local (sem subagentes; implementação direta)

---

## Problema

No full gauntlet da Onda de Validação 1, o header do `GAUNTLET_REPORT.md` mostrou `232/235 (99%)` mas o `checkpoint.json` tinha 231 pass, 3 fail, 1 skip. O SKIP (ex.: K-08 VRAM quando ha processo externo) foi contado como pass no numerador do sumario, inflando o numero em +1 e mascarando o sinal real de saude.

---

## Causa-raiz

A agregacao do sumario soma `total - fail` como "pass" (ou similar), incluindo SKIP no pass, em vez de contar as 3 categorias separadamente.

---

## Solucao proposta

Na função que monta o header/tally do report, computar e exibir `pass`, `fail`, `skip` como categorias distintas (ex.: "231 pass / 3 fail / 1 skip de 235"). O gate de APROVADO continua exigindo 100% dos não-skip (skip não conta como fail nem como pass). Confirmar onde o tally e impresso e onde o report e escrito; alinhar ambos ao checkpoint.json.

---

## Proof-of-work esperado

```bash
# rodar um gauntlet que gere ao menos 1 SKIP e comparar header vs checkpoint
./run.sh --gauntlet --only performance     # K-08 costuma SKIP fora de ambiente isolado
# ler dev-journey/07-reports/gauntlet/GAUNTLET_REPORT.md (header) e checkpoint.json -> contagens coerentes
bash scripts/sprint_invariants.sh           # 14/14 PASS
/home/andrefarias/.local/bin/ruff check scripts/gauntlet/nyx_gauntlet.py
python3 ~/.config/zsh/scripts/validar-acentuacao.py --paths scripts/gauntlet/nyx_gauntlet.py
```

---

## Criterio binario de aceite

- [ ] header mostra pass/fail/skip separados; pass não inclui skip
- [ ] header coerente com checkpoint.json
- [ ] gate inalterado
- [ ] invariantes 14/14, ruff/acento OK; spec -> concluidos/

---

## Riscos

| Risco | Mitigacao |
|-------|-----------|
| Ambiente não gerar SKIP para testar | forcar um SKIP (ex.: K-08 com VRAM externa) ou um teste sintetico que exercite o caminho de agregacao |
| Mudar o gate sem querer | so a EXIBICAO muda; o criterio APROVADO (100% dos não-skip) fica intacto -- confirmar com um run APROVADO |

---

*"Contar o que voce pulou como acerto e mentir pro próprio painel." -- anonimo*
