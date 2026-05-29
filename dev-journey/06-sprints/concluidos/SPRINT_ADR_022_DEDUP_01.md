# SPRINT 261 — ADR-022-DEDUP-01

## 0. SPEC (machine-readable)

```yaml
sprint:
  id: ADR-022-DEDUP-01
  title: "Desduplicar ADR-022 (dois arquivos, mesmo número)"
  onda: 31
  prioridade: BAIXA
  tipo: Docs
  dependencias: []
  desbloqueia: []

  # CORRIGIDO 2026-05-26: a v1 desta spec INVERTEU os nomes. Confirmado por
  # leitura de conteúdo + git history (843977a feat(VISION-01) criou o MOONDREAM.md
  # com a impl Ollama real; 70063ca criou o VISION_MOONDREAM_CPU.md transformers).
  touches:
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/README.md
      reason: "Contagem de ADRs (32 -> 31) nas linhas 294 e 417"
  removes:
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/dev-journey/03-decisions/ADR_022_VISION_MOONDREAM_CPU.md
      reason: "ADR-022 OBSOLETO (2026-04-19, abordagem transformers/HuggingFace abandonada, cita qwen3:4b). Apesar do nome descritivo, é o conteúdo desatualizado."

  forbidden:
    - "Remover dev-journey/03-decisions/ADR_022_MOONDREAM.md (é o CANÔNICO: 2026-05-17, Ollama /api/generate, qwen2.5-coder:3b, aponta vision_client.py/vision_service.py)"
    - "Renomear o canônico (V1 = mínima; nome casa com o título do ADR e o README)"
    - "Adicionar emoji / menção a IA externa"

  tests:
    - cmd: "python scripts/sync.py"
      timeout: 60
      deve_passar: false   # exit 1 pré-existente; critério é não introduzir erro NOVO de ADR

  acceptance_criteria:
    - "Existe exatamente 1 arquivo ADR-022 (o ADR_022_MOONDREAM.md canônico)"
    - "README reflete 31 ADRs (era 32 contando a duplicata)"
    - "sync.py _check_adrs sem gap nem erro novo"
    - "smoke boot ok + invariantes 14/14"
```

---

**Status:** PENDENTE
**Data criação:** 2026-05-26
**Modelo obrigatório:** claude-opus-4-7 (sem subagentes)

---

## Contexto

> ADR-015 (Documentação para continuidade): docs são fonte única; duplicata gera ambiguidade.
> Achado da auditoria 2026-05-26.

## Problema

Existem **dois** arquivos para o ADR-022 (verificado por conteúdo + git history):

- `ADR_022_MOONDREAM.md` — **CANÔNICO.** Data interna **2026-05-17**. Decide moondream em CPU via Ollama `POST /api/generate` (`num_gpu=0`), aponta os arquivos reais (`vision_client.py` + `vision_service.py`) e cita o modelo atual `qwen2.5-coder:3b` (ADR-031). Reflete a implementação que existe no código. Origem: `843977a feat(VISION-01)`.
- `ADR_022_VISION_MOONDREAM_CPU.md` — **OBSOLETO.** Data interna **2026-04-19**. Decide moondream2 via `transformers`/HuggingFace; cita o modelo antigo `qwen3:4b`; tem "Alternativas A-D". **A abordagem descrita NÃO foi a implementada.** Origem: `70063ca`.

Paradoxo de nomenclatura: o nome mais descritivo (`_VISION_MOONDREAM_CPU`) pertence ao conteúdo obsoleto; o nome genérico (`_MOONDREAM`) pertence ao canônico. Mesmo número, dois conteúdos divergentes — confunde quem lê.

## Solução (V1 — mínima)

- **Canônico:** `ADR_022_MOONDREAM.md` (mantém, sem renomear).
- **Remover:** `ADR_022_VISION_MOONDREAM_CPU.md` (obsoleto). Antes de remover, fazer grep por referências ao **nome** desse arquivo no repo (código/docs) — ADRs costumam ser referenciados por número, não nome; se nada o referencia por nome, remover. As "Alternativas A-D" do obsoleto têm valor histórico (justificam rejeição de LLaVA/Qwen-VL/cloud) — se desejável, portá-las como seção no canônico antes de remover; caso contrário, o histórico git preserva.
- Atualizar `README.md` linhas 294 (`## ADRs (32)`) e 417 (`# 32 ADRs`) para `31`. Grep por outras citações de "32 ADRs".
- **Fase 1:** rodar `./venv/bin/python scripts/sync.py` e inspecionar `_check_adrs()` — confirmar contagem 32→31 sem gap.

## Comandos de verificação

```bash
ls dev-journey/03-decisions/ADR_022*.md           # deve listar 1 arquivo (ADR_022_MOONDREAM.md)
grep -rn "32 ADRs\|ADRs (32)" README.md            # vazio após fix
grep -rn "ADR_022_VISION_MOONDREAM_CPU" .          # confirmar que nada referencia o removido por nome
./venv/bin/python scripts/sync.py                  # _check_adrs sem gap
./run.sh --smoke                                   # boot ok
bash scripts/sprint_invariants.sh                  # 14/14
```

## Critério binário de aceite

- [ ] 1 único arquivo ADR-022 em `03-decisions/` (o `_MOONDREAM.md` canônico)
- [ ] README sem contagem "32" remanescente
- [ ] `_check_adrs` sem gap nem erro novo
- [ ] smoke + invariantes preservados
- [ ] entrada 261 do MASTER marcada CONCLUIDA com os nomes CORRETOS
- [ ] spec movida `producao/` -> `concluidos/`

## Proof-of-work

`ls` dos ADRs + trecho do `_check_adrs` + grep do nome removido + invariantes antes/depois.

---

*"Duas verdades sobre a mesma coisa é meia mentira." -- anônimo*
