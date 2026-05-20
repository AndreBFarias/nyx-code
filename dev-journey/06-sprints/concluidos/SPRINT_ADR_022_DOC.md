## 0. SPEC

```yaml
sprint:
  id: ADR-022-DOC
  title: "Materializar ADR-022: Visão via moondream CPU"
  onda: 22
  bloco: 2.5
  prioridade: MÉDIA
  tipo: Docs
  dependencias: []
  desbloqueia: [VISION-01]

  creates:
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/dev-journey/03-decisions/ADR_022_VISION_MOONDREAM_CPU.md
      reason: "ADR referenciado em SPRINT_ORDER_MASTER.md (Onda 22 D1) nunca foi criado como arquivo"

  touches:
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/GUIDE.md
      reason: "Tabela de ADRs vigentes adiciona 022 entre 021 e 023"

  removes: []

  forbidden:
    - "Status: proposto"
    - "Justificar escolha de moondream sem comparar com alternativas"
    - "Deixar VRAM/RAM sem número concreto"

  tests:
    - cmd: "test -f dev-journey/03-decisions/ADR_022_VISION_MOONDREAM_CPU.md"
      deve_passar: true
    - cmd: "grep -c '^| 022 |' GUIDE.md"
      esperado: ">= 1"

  acceptance_criteria:
    - "Arquivo ADR_022 existe com estrutura canônica"
    - "Status: ACEITO"
    - "GUIDE.md atualizado com linha 022"
    - "ADR inclui consumo de RAM/VRAM medido ou estimado para a máquina-alvo (RTX 3050 4GB)"
    - "Compara com ao menos 1 alternativa (llava / llama-cpp vision) e justifica"
```

---

# Sprint ADR-022-DOC — Visão moondream CPU

**Status:** CONCLUIDA (header corrigido em MASTER-CLEANUP-02 2026-05-20; presença em concluidos/ implica CONCLUIDA conforme convenção do projeto)
**Data criação:** 2026-04-19
**Modelo obrigatório:** claude-opus-4-7 (sem subagentes)

---

## Contexto do projeto (snapshot)

> - ADR-001 Local First; ADR-003 VRAM Management.
> - `SPRINT_ORDER_MASTER.md` linha 227: "D1 visão via moondream CPU (ADR-022)" — decisão tomada em 2026-04-18 mas arquivo nunca criado.
> - Sprint VISION-01/02/03 dependem deste ADR.
> - RTX 3050 Laptop 4GB já está carregando qwen3:4b (~2.6 GiB). Não há VRAM para um modelo de visão concorrente.

---

## Problema

Decisão tomada (moondream CPU para visão) mas sem documento formal. Sprint VISION-01 não pode ser executada sem violar ADR-015 (Documentação para continuidade).

---

## Solução proposta

Criar `ADR_022_VISION_MOONDREAM_CPU.md` explicando:

- Problema: precisamos entender imagens coladas no REPL (Ctrl+V → `[Image #N]`).
- Restrição: VRAM já ocupada por qwen3:4b; CPU tem 14.8 GiB RAM livres.
- Decisão: usar **moondream2** (≈ 1.8 GiB RAM em FP16) rodando **em CPU** via transformers/onnxruntime.
- Latência aceita: ~3-5s por imagem (uma vez por prompt).
- Consequências positivas: VRAM intacta, Local First preservado.
- Consequências negativas: CPU usage alto durante inferência; RAM residente +1.8 GiB.
- Alternativas:
  - llava-7b via Ollama: exige GPU, não cabe.
  - llama.cpp vision: cabe em CPU mas modelos maiores, mais lentos.
  - Qwen-VL: mesma restrição de VRAM.

---

## Arquivos alvo

### `/home/andrefarias/Desenvolvimento/Nyx-Code/dev-journey/03-decisions/ADR_022_VISION_MOONDREAM_CPU.md` (criar)

Seguir estrutura do ADR-024 como modelo. Seções: Contexto, Decisão, Consequências (+/-), Alternativas, Referências, citação final.

### `/home/andrefarias/Desenvolvimento/Nyx-Code/GUIDE.md`

Adicionar:
```
| 022 | Visão via moondream CPU |
```

---

## Comandos de verificação

```bash
test -f dev-journey/03-decisions/ADR_022_VISION_MOONDREAM_CPU.md && echo OK
grep '^\*\*Status:\*\* ACEITO' dev-journey/03-decisions/ADR_022_VISION_MOONDREAM_CPU.md
grep -c '^| 022 |' GUIDE.md
```

---

## Critério binário de aceite

- [ ] Arquivo criado com Status ACEITO
- [ ] Número concreto de RAM ou VRAM para a decisão
- [ ] Ao menos 1 alternativa comparada e rejeitada
- [ ] GUIDE.md atualizado
- [ ] Citação de filósofo
- [ ] Commit `docs: cria ADR-022 sobre visão via moondream CPU`

---

## Gambiarras específicas

- **Números genéricos tipo "poucos GB"** — proibido. Valor numérico real.
- **Alternativa fantasma** — ao citar alternativa, precisa de argumento concreto de rejeição, não "não achamos legal".
- **Deixar para VISION-01 detalhar** — não. ADR é onde a decisão é registrada; VISION-01 é onde é implementada.

---

## Riscos

| Risco | Mitigação |
|-------|-----------|
| moondream2 pode ter licença restritiva | Verificar licença antes de marcar ACEITO (Apache-2.0 esperado) |
| Números de VRAM/RAM estimados podem divergir da realidade | Marcar como "estimado"; sprint VISION-01 confirma com benchmark |

---

*"Aquele que vê precisa também pensar." -- Heráclito (paráfrase)*
