# SPRINT DOC-RECONCILE-ONDA43-STATE-01 — reconciliar docs de estado defasados (STATE/contagens/GAUNTLET)

## 0. SPEC (machine-readable)

```yaml
sprint:
  id: DOC-RECONCILE-ONDA43-STATE-01
  title: "STATE.md 4 ondas atrás, contagem de commands divergente em 3 docs, GAUNTLET_REPORT só da fase rápida"
  onda: 44
  bloco: "44 -- auditoria das ondas 36-43 (2026-06-03)"
  prioridade: BAIXA
  tipo: Docs / Reconcile
  dependencias: []
  desbloqueia: []

  touches:
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/STATE.md
      reason: "Linha de retomada no topo diz 'ONDA-39 CONCLUIDA' (estado real: ONDA-43). Inventário diz 'Commands: 67 únicos' (real: ~70 @nyx_command; Checkpoint ONDA-42 diz 71). 'Sprints concluídas: 497' a revisar."
      linhas_alvo: "11-16 (linha de retomada); 63-66 (Runtime/inventário)"
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/GAUNTLET_REPORT.md
      reason: "Mostra 19/19 (apenas fase rápida) com 'Gate de Produção: APROVADO'. Pode iludir: o completo (220) não roda desde cdcee20. Deixar explícito que é a fase rápida."
      linhas_alvo: "1-11 (cabeçalho + Gate)"

  creates: []
  removes: []

  n_to_n_pairs:
    - descricao: "Contagem de commands aparece em STATE.md (67), Checkpoint.md (71) e PROJECT_SNAPSHOT.md/MASTER (67). Fonte viva é `python scripts/sync.py`."  # noqa-acento
      paths:
        - /home/andrefarias/Desenvolvimento/Nyx-Code/STATE.md
        - /home/andrefarias/Desenvolvimento/Nyx-Code/dev-journey/08-templates/PROJECT_SNAPSHOT.md

  forbidden:
    - "Inventar contagens à mão -- usar `python scripts/sync.py` como fonte autoritativa"
    - "Marcar o gauntlet completo como APROVADO sem rodá-lo (rodar é caro/GPU; apenas rotular o report como fase rápida)"
    - "Adicionar emoji ou menção a IA externa"

  tests:
    - cmd: "python scripts/sync.py"
      timeout: 60
      esperado: "imprime inventario: tools=N, commands_unicos=M, services=S (fonte autoritativa)"
    - cmd: "bash scripts/sprint_invariants.sh"
      timeout: 180
      esperado: "14/14 PASS"

  acceptance_criteria:
    - "STATE.md linha de retomada reflete ONDA-43 (ou a onda corrente na execução)"
    - "Contagem de commands em STATE/SNAPSHOT bate com `scripts/sync.py`"
    - "GAUNTLET_REPORT.md deixa explícito que o 19/19 é a fase rápida (não o completo 220)"
    - "Invariantes 14/14"
```

---

**Status:** PENDENTE
**Data criação:** 2026-06-03
**Origem:** auditoria das ondas 36-43 (observação documental, severidade BAIXA). ADR-015 (documentação para continuidade) e ADR-028 (SBOM fonte única) prometem precisão.
**Modelo obrigatório:** claude-opus (sem subagentes)

---

## Contexto do projeto (snapshot — não referência)

> - ADR-015 Documentação para continuidade: uma nova sessão deve entender o estado lendo os docs.
> - ADR-028 SBOM: REGISTRY.yaml é fonte única; contagens divergentes entre docs violam o espírito.
> - O próprio STATE.md reconhece que "pulou direto de 35 para 39"; aqui o gap chegou a 43.

---

## Problema

1. **STATE.md desatualizado:** a linha de retomada no topo abre com "ONDA-39 CONCLUIDA (2026-06-02)", mas o estado real (Checkpoint.md + commits) é **ONDA-43** — 4 ondas de defasagem (40 sanitizer, 41 backlog, 42 E2E, 43 estresse/GPU).
2. **Contagem de commands divergente:** STATE.md "67 únicos" · `grep @nyx_command` ~70 · Checkpoint ONDA-42 "71". Três números para a mesma coisa.
3. **GAUNTLET_REPORT.md ilusório:** mostra 19/19 com "Gate de Produção: APROVADO", mas são só as fases rápidas (infra+proxy+visual+config). O completo (220) não roda desde `cdcee20`. Quem lê o report pode achar que o sistema inteiro passou.

---

## Causa-raiz

Write-through dos docs de estado ficou para trás durante as ondas 40-43 (foco em runtime/GPU). A contagem de commands não é regenerada de fonte única em todos os docs. O `update_docs.py` (rodado pelo `--gauntlet`) regenera o report a partir da última execução, que tem sido a fase rápida.

---

## Solução proposta

1. Atualizar a linha de retomada do STATE.md para a onda corrente (sintetizar 40-43 em 1 parágrafo, como o STATE já faz).
2. Rodar `python scripts/sync.py` e alinhar a contagem de commands em STATE.md e PROJECT_SNAPSHOT.md ao número autoritativo.
3. No GAUNTLET_REPORT.md, rotular explicitamente "(fase rápida — completo não executado nesta sessão)" no cabeçalho/Gate, para não iludir.

---

## Proof-of-work esperado (runtime real)

```bash
python scripts/sync.py                                  # número autoritativo de commands
bash scripts/sprint_invariants.sh                       # 14/14 PASS
python3 ~/.config/zsh/scripts/validar-acentuacao.py --paths STATE.md GAUNTLET_REPORT.md
grep -c 'ONDA-43' STATE.md                              # >= 1 após o fix
```

---

## Critério binário de aceite

- [ ] STATE.md linha de retomada reflete a onda corrente
- [ ] Contagem de commands consistente com `scripts/sync.py`
- [ ] GAUNTLET_REPORT.md rotulado como fase rápida
- [ ] Invariantes 14/14; spec movida para `concluidos/`

---

## Riscos

| Risco | Mitigação |
|-------|-----------|
| Reconciliar à mão volta a defasar | Preferir números de `scripts/sync.py`; não chumbar valores |
| Mexer no STATE.md durante outra sprint gera conflito | Sprint pequena e isolada; rodar por último na onda |

---

*"O mapa que mente sobre onde estamos atrasa mais que a falta de mapa." -- anônimo*
