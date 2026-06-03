# SPRINT LOOP-CONTEXT-WINDOW-AUDIT-01 — janela de 4 mensagens é a causa-raiz da alucinação de contexto longo

## 0. SPEC (machine-readable)

```yaml
sprint:
  id: LOOP-CONTEXT-WINDOW-AUDIT-01
  title: "Auditar a janela fixa de 4 mensagens em _call_llm: causa-raiz da alucinação que 354/355 tratam por prompt; compactação inalcançável"
  onda: 44
  bloco: "44 -- auditoria das ondas 36-43 (2026-06-03)"
  prioridade: MÉDIA
  tipo: Audit / Core loop
  dependencias: []
  desbloqueia: [CONV-CONTEXT-LOCATION-HALLUCINATION-01, EDIT-SEQUENTIAL-OVERWRITE-LOSS-01]

  touches:
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/agent/loop/_iteration.py
      reason: "_call_llm (linha 505-531): quando len(history_msgs) > 4, envia SEMPRE só as últimas 4 mensagens (linha 521-522). O branch `elif should_compact` (524-529) fica inalcançável quando há >4 msgs (redundante com a compactação do _run_iterations). A docstring (476-480) promete 'compactação se budget > 40%' que na prática não roda por aqui."
      linhas_alvo: "505-531 (seleção de contexto); 476-480 (docstring)"

  creates: []
  removes: []
  n_to_n_pairs: []

  forbidden:
    - "Aumentar a janela cegamente sem medir VRAM/latência no cenário-alvo (RTX 3050 4GB com desktop cheio, ADR-034)"
    - "Desabilitar a compactação real do _run_iterations (linha 293-303)"
    - "Adicionar emoji ou menção a IA externa"

  tests:
    - cmd: "bash scripts/sprint_invariants.sh"
      timeout: 180
      esperado: "14/14 PASS"
    - cmd: "./run.sh --gauntlet --only rapido"
      timeout: 300
      esperado: "APROVADO; sem regressão de VRAM/latência"

  acceptance_criteria:
    - "Documentar (relatório em dev-journey/07-reports/) se a janela de 4 é deliberada ou acidental e qual o impacto medido em conversa longa"
    - "Decidir e implementar UMA de: (a) janela adaptativa por VRAM livre; (b) sempre incluir o resumo compactado além das 4 recentes; (c) manter 4 e remover o branch morto + corrigir a docstring (assumir explicitamente o trade-off)"
    - "Se mexer na janela: proof runtime de que não estoura VRAM no cenário-alvo (ADR-034)"
    - "Invariantes 14/14, gauntlet rápido APROVADO"
```

---

**Status:** PENDENTE
**Data criação:** 2026-06-03
**Origem:** auditoria das ondas 36-43 (achado A4, severidade MÉDIA). Conecta com 354/355 (CONV-CONTEXT-LOCATION-HALLUCINATION / EDIT-SEQUENTIAL-OVERWRITE): os fixes de prompt tratam o sintoma; a janela curta pode ser a causa.
**Modelo obrigatório:** claude-opus (sem subagentes)

---

## Contexto do projeto (snapshot — não referência)

> - ADR-032 A infra carrega o modelo / ADR-034 Feito para quem não tem A100: a janela curta é uma escolha de sobrevivência em GPU 4GB; o ponto é entender se está sub-dimensionada e compensada por prompt.
> - ADR-009 Acesso Universal: "uma resposta de 60s correta vale mais que 5s truncada" — contexto é parte da qualidade.
> - 354/355 (ONDA-43) adicionaram diretivas no `build_reminder` contra alucinação de localização e overwrite em conversa longa; runtime ficou **inconclusivo** (3b em CPU degradado).

---

## Problema

`_call_llm` (`_iteration.py:505-531`) seleciona o contexto enviado ao modelo:

```python
history_msgs = self._session.to_messages()
...
if len(history_msgs) > 4:
    messages.extend(history_msgs[-4:])          # <-- SEMPRE só as 4 últimas
    logger.info("[loop] contexto reduzido: %d/%d msgs", 4, len(history_msgs))
elif self._budget.should_compact(self._session):
    compacted = self._budget.compact_history(self._session)   # <-- inalcançável se len>4
    ...
```

Em conversa longa (cenário da ONDA-43: 15 turnos), o modelo recebe **só as últimas 4 mensagens** + o system prompt + o reminder. Ao perguntar "em qual arquivo está a função X" (citada 8 turnos atrás), o modelo **não vê** onde X foi mencionado e inventa o caminho — o sintoma exato do #354. Os fixes 354/355 são diretivas de prompt sobre essa janela apertada.

Colateral: o branch `elif should_compact` dentro de `_call_llm` é **logicamente inalcançável** quando há >4 msgs (a compactação real já roda no `_run_iterations:293-303`). A docstring (linha 476-480, "Compactação se budget > 40%") descreve um comportamento que não acontece neste ponto.

---

## Causa-raiz (hipótese a confirmar)

A janela fixa de 4 mensagens, somada ao repo_map (que pode não conter X) e à reinjeção do pedido original, é a estratégia de contexto para GPU 4GB. Ela é eficaz em latência/VRAM, mas pode ser a **fonte** das alucinações de contexto longo que 354/355 mitigam por prompt. É preciso medir, não presumir.

---

## Solução proposta (decidir após medir)

Investigar e escolher UMA:
- **(a)** janela adaptativa: `N` mensagens em função da VRAM livre / `num_ctx` real (mais contexto quando há folga).
- **(b)** sempre anexar o **resumo compactado** (do `SessionSummarizer`/`compact_history`) além das 4 recentes, dando ao modelo memória de longo prazo barata em tokens.
- **(c)** manter 4 deliberadamente, remover o branch morto (`elif should_compact` em `_call_llm`) e corrigir a docstring — assumindo o trade-off por escrito e deixando 354/355 como a mitigação aceita.

Qualquer mudança na janela exige **proof runtime no cenário-alvo** (RTX 3050 4GB, desktop cheio): VRAM e latência antes/depois.

---

## Proof-of-work esperado (runtime real)

```bash
bash scripts/sprint_invariants.sh                       # 14/14 PASS
./run.sh --gauntlet --only rapido                       # APROVADO
# Conversa longa reproduzível (>= 8 turnos) que cita um arquivo cedo e pergunta a localização tarde;
# medir se a resposta acerta o arquivo (opção a/b) ou documentar o trade-off (opção c).
# nvidia-smi / proxy_stats.json antes/depois se a janela mudar.
```

---

## Critério binário de aceite

- [ ] Relatório com a decisão (a/b/c) e a medição que a justifica
- [ ] Branch morto removido e docstring corrigida (em qualquer opção)
- [ ] Se a janela mudou: proof de VRAM/latência no cenário-alvo
- [ ] Invariantes 14/14, gauntlet rápido APROVADO
- [ ] Spec movida `producao/` → `concluidos/`; MASTER marca CONCLUIDA

---

## Riscos

| Risco | Mitigação |
|-------|-----------|
| Aumentar a janela estoura VRAM no cenário-alvo | Medir; preferir resumo compactado (opção b) que custa poucos tokens |
| Investigação vira refactor grande do ContextBudget | Manter escopo de auditoria + 1 decisão; refactor maior vira sprint própria |

---

*"Tapar o sintoma com prompt é remédio; achar a janela curta é diagnóstico." -- anônimo*
