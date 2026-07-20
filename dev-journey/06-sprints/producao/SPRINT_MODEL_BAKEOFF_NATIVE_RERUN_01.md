## 0. SPEC (machine-readable)

```yaml
sprint:
  id: MODEL-BAKEOFF-NATIVE-RERUN-01
  numero_master: 447
  title: "Re-run do bake-off de modelos com o pipeline de tool-calling nativo ligado (pos-446)"
  onda: 49
  prioridade: ALTA
  tipo: Pesquisa/Avaliacao
  dependencias: [MODEL-NATIVE-TOOLCALL-PIPELINE-01, MODEL-BAKEOFF-CANDIDATES-01]
  desbloqueia: [MODEL-MANAGER-CORE-01, MODEL-FALLBACK-CHAIN-01, ADR-036]

  touches: []
  creates:
    - path: dev-journey/07-reports/PESQUISA_MODELO_2026_07.md
      reason: "anexar a seção Bake-off v2 (nativo ligado) ao relatório existente, lado a lado com a v1"
  removes: []

  forbidden:
    - "Efetivar troca de modelo: NÃO editar DEFAULT_MODEL em nyx/config/defaults.py"
    - "Editar código de produto (a 446 já terminou; esta sprint só mede)"
    - "Rodar dois modelos ao mesmo tempo na GPU (um por vez)"
    - "Deixar processo orfao ou VRAM presa entre candidatos"
    - "Adicionar emoji; mencionar ferramenta de IA"

  acceptance_criteria:
    - "Mesmos probes P1-P6 e mesmo protocolo da 442 (arquivo de referencia), com o pipeline da 446 ativo"
    - "Metrica central: taxa de tool_call NATIVO por modelo (era 0/81 na v1; qwen3 deve subir de zero, baseline pode continuar via resgate)"
    - "Tabela v1 vs v2 anexada ao relatorio; recomendacao empirica de piso para a decisao do dono"
    - "Default qwen2.5-coder:3b intacto ao fim; zero processo orfao; VRAM liberada"
```

---

# Sprint MODEL-BAKEOFF-NATIVE-RERUN-01 — bake-off v2 com o nativo ligado

**Status:** ENFILEIRADA

**Enfileiramento:** mesma decisão do dono de 2026-07-13 que enfileirou a 446 — fechar a ONDA-48 inteira antes da frente de modelo. Ao abrir a ONDA-49, reverter este status (e a linha no `SPRINT_ORDER_MASTER.md`) para `PENDENTE`, DEPOIS de a 446 concluir.

**Data criação:** 2026-07-20
**Origem:** achado central do bake-off v1 (2026-07-13, commit `9280978`): 0/81 tool_call nativo DENTRO do Nyx apesar de o `qwen3:1.7b` emitir `message.tool_calls` perfeito em teste direto ao Ollama — o pipeline suprime o nativo. A ordem revisada do bloco ONDA-49 ("446 -> re-run do bake-off -> dono decide o piso") citava este re-run só em prosa, sem ID nem spec; esta sprint dá corpo à etapa para ela não se perder na esteira (regra "nenhum débito fica para trás").

---

## Contexto do projeto (snapshot)

> **ADRs:** ADR-031 (modelo atual), ADR-032/033/034 (a infra carrega o modelo), ADR-035 (contrato de execução).
> **A alma:** o bake-off v1 provou que trocar modelo sem consertar o pipeline é cosmético. A 446 conserta o pipeline; esta sprint mede o ganho REAL da troca com o pipeline certo — é a evidência que faltava para o ADR-036.

---

## Problema

O bake-off v1 mediu os candidatos com o pipeline suprimindo o tool-calling nativo (few-shot de JSON-no-content empurrava todos para o formato texto). As conclusões sobre QUALIDADE dos candidatos são, portanto, provisórias: um modelo com nativo funcional pode inverter os resultados de P3/P4/P5 (os probes que mais falharam). Decidir o piso com os dados da v1 seria decidir com dados enviesados pelo bug que a 446 removeu.

## Solução proposta

Repetir literalmente o protocolo da 442 (`producao/SPRINT_MODEL_BAKEOFF_CANDIDATES_01.md` — candidatos, probes P1-P6, métricas, protocolo de execução e limpeza) com o pipeline da 446 ativo. Sem probe novo, sem candidato novo: a única variável que muda entre v1 e v2 é o pipeline, para a comparação ser limpa.

Adicional único da v2:

- **Métrica de regressão do baseline:** o `qwen2.5-coder:3b` (que NÃO tem nativo) deve continuar funcionando via resgate texto->JSON exatamente como antes — qualquer queda do baseline na v2 é regressão da 446, não achado de modelo, e deve ser reportada como bug da 446.

## Proof-of-work esperado

- `out_<id>.jsonl` de cada candidato + tabela comparativa **v1 vs v2** (probes x modelos x nativo/sucesso/PT-BR/VRAM/tempo) anexada em §Bake-off v2 do relatório `dev-journey/07-reports/PESQUISA_MODELO_2026_07.md`.
- Contagem explícita de tool_call nativo por modelo (v1 era 0/81; esperado qwen3 > 0 na v2).
- `grep DEFAULT_MODEL nyx/config/defaults.py` ainda `qwen2.5-coder:3b` ao fim.
- `nvidia-smi` com VRAM liberada e `pgrep ollama` vazio ao fim.
- Recomendação empírica de 1 parágrafo endereçada à decisão do dono (piso + cadeia), insumo direto do ADR-036.

## Critério binário de aceite (IA executora)

1. Os 6 probes rodaram para baseline + qwen3:1.7b + qwen3:4b (mínimo) com o pipeline nativo ativo.
2. A tabela v1 vs v2 está no relatório com a coluna de tool_call nativo preenchida por evidência de log (não estimativa).
3. Baseline sem regressão (ou regressão reportada como bug da 446, bloqueando a recomendação).
4. DEFAULT_MODEL intocado; VRAM liberada; zero órfão.

## Não-objetivos (anti-débito)

- **Não** decidir o piso (decisão do dono, com esta evidência na mão).
- **Não** escrever o ADR-036 aqui (vem depois, com a decisão).
- **Não** implementar gerenciador/fallback (443/445).

---

*"A v1 mediu os modelos com a infra errada; a v2 mede a pergunta certa."*
