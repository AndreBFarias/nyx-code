# SPRINT INFRA-MODEL-AGNOSTIC-01 — Tese "infra forte > modelo grande"

## 0. SPEC (machine-readable)

```yaml
sprint:
  id: INFRA-MODEL-AGNOSTIC-01
  title: "Validar empiricamente que infra do Nyx eleva qualquer modelo (mesmo o pior)"
  onda: 24
  bloco: 24.3 Resiliência arquitetural
  prioridade: MÉDIA
  tipo: Audit
  dependencias: [MODEL-SWAP-01]
  desbloqueia: []

  touches:
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/dev-journey/03-decisions/ADR_031_MODEL_CHOICE.md
      reason: "Adicionar seção 'Validacao empirica: infra > modelo' com resultado da sprint"
  creates:
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/dev-journey/07-reports/RELATORIO_INFRA_RESILIENTE_MODELO_01.md
      reason: "Relatório comparativo qwen2.5-coder:3b (atual) vs qwen3:4b (legacy --4b) com mesmo prompt"
  removes: []

  forbidden:
    - "Marcar tese sustentada sem números empíricos"
    - "Modificar model_compare.py se ele já faz o trabalho"

  tests:
    - cmd: "./venv/bin/python scripts/gauntlet/fixtures/model_compare.py --n 3 --models qwen2.5-coder:3b qwen3:4b"
      timeout: 300
      deve_passar: "JSON com lang_rate, tool_ok, P50, P95 para ambos"
    - cmd: "bash scripts/sprint_invariants.sh"
      timeout: 60
      deve_passar: "14/14"

  acceptance_criteria:
    - "RELATORIO_INFRA_RESILIENTE_MODELO_01.md com tabelas comparativas"
    - "Métricas: lang_pt_br_rate, tool_ok via parser fallback, P50, P95, VRAM"
    - "Conclusão binária: tese sustentada (sim/não) + diferença numérica"
    - "ADR-031 ganha seção com link para o relatório"
    - "Smoke ok"
```

---

# Sprint INFRA-MODEL-AGNOSTIC-01 — Validar tese arquitetural

**Status:** PENDENTE
**Data criação:** 2026-05-18
**Modelo obrigatório:** claude-opus-4-7

---

## Contexto

Meta declarada do usuário (mensagem 2026-05-18): **"o model não importa, até o pior model com a infra que force ele a ser bom, vai ser ótimo. Ao trocar de model o projeto não quebra, melhora a qualidade do código ou nota-se velocidade na fabricação do código. Não no programa como um todo. A infra é o que sustenta tudo."**

ADR-031 já mostrou empiricamente que qwen2.5-coder:3b vence qwen3:4b em score 96.8 vs 34.6. Mas a tese mais forte é: **mesmo qwen3:4b com a infra do Nyx (parser de fallback, retry, classifier, warmup) produz experiência aceitável**.

INFRA-MODEL-AGNOSTIC-01 valida empiricamente essa tese.

---

## Solução proposta

Rodar `scripts/gauntlet/fixtures/model_compare.py --n 3` em ambos modelos, com **mesmo system_prompt e mesma infra Nyx**. Comparar:

- `lang_pt_br_rate` em chat
- `tool_ok` (via parser de fallback do `nyx/agent/parser.py`)
- Latência P50/P95
- VRAM
- Saída literal para 1 prompt complexo

Se infra eleva qwen3:4b para próximo do qwen2.5-coder:3b em pelo menos 2 dimensões (lang_rate, tool_ok), tese sustentada. Sprint não fala em "ganhador" — fala em "ambos viáveis".

---

## Critério binário de aceite

- [ ] `RELATORIO_INFRA_RESILIENTE_MODELO_01.md` criado
- [ ] Tabela compara qwen2.5-coder:3b vs qwen3:4b em 5 métricas
- [ ] Saída literal anexada para ≥3 prompts
- [ ] Conclusão: tese sustentada (numérico)
- [ ] ADR-031 atualizado com link
- [ ] Smoke ok
- [ ] Invariantes 14/14
- [ ] Commit `docs(INFRA-MODEL-AGNOSTIC-01): tese 'infra forte > modelo grande' validada empiricamente`

---

*"O modelo é cavalo; a infra é arreio. Cavalo qualquer arreio bom doma." — INFRA-MODEL-AGNOSTIC-01*
