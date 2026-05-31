# SPRINT 303 — TUI-DONE-SUMMARY-CLEAN-01

## 0. SPEC (machine-readable)

```yaml
sprint:
  id: TUI-DONE-SUMMARY-CLEAN-01
  title: "Resposta final do NyxCode limpa (sem done(summary=...) cru no balao)"
  onda: 35
  prioridade: ALTA
  tipo: Bugfix
  touches:
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/agent/tui/app.py
      reason: "_process_turn captura o SessionStatus e troca o balao cru pelo summary limpo"
  acceptance_criteria:
    - "mandar 'oi' -> chat mostra resposta natural, sem done(summary=...) visivel"
    - "resposta normal (texto puro) fica intacta"
    - "smoke + invariantes 14/14 + gauntlet rapido APROVADO"
```

---

**Status:** CONCLUIDA
**Data criação:** 2026-05-30
**Data conclusão:** 2026-05-30
**Modelo obrigatório:** claude-opus-4-7 (sem subagentes)

---

## Problema

A resposta final do NyxCode às vezes aparecia como o texto cru `done(summary="A versão... é 1.3.0.")` em vez da frase limpa (`◆ NyxCode` seguido de `done(summary="...")`).

## Causa-raiz

`done` é uma ActionType. Quando o modelo emite `done(summary="...")` como **TEXTO** (não como tool call estruturada), o `ActionParser` (fallback) o reconhece como ação done e extrai o summary — mas o **streaming de tokens (`_on_token`) já exibiu o texto CRU no balão do assistant ANTES** de o parser rodar. O `summary` limpo existe no `SessionStatus` retornado por `run()`, mas o `_process_turn` ignorava esse retorno.

## Fix

`app.py _process_turn`: captura `status = await self._agent.run(text)`. Se o turno tem `_current_assistant` e o conteúdo do balão contém a sintaxe crua `done(`, substitui pelo `status.summary` (limpo) via `set_content`. Cirúrgico: respostas normais (texto puro, sem `done(`) não casam a condição e ficam intactas; e mesmo um falso-positivo é seguro (no texto puro, `summary == content`).

## Proof-of-work

```
FAIL_BEFORE=0 -> FAIL_AFTER=0 (14/14)   ruff: All checks passed!   acentuacao: rc=0
gauntlet --only rapido: 19/19 (100%) APROVADO
```
**Pilot (`/tmp/val_303_done.py`):** stub streama `done(summary="A versao do projeto e 1.3.0.")` cru; após o turno o balão = `A versao do projeto e 1.3.0.` (sem `done(`).
**--web real (playwright, inferência):** digitei "oi" (sem clicar); NyxCode respondeu **"Olá! Como posso ajudar você hoje?"** — `tem_done_cru=false` no buffer `.xterm-rows`. (Mesma captura confirmou a integração com 307 autofoco, 306 input 5 linhas com borda, 309 Markdown sem travar.)

## Critério de aceite

- [x] "oi" -> resposta natural sem `done(...)` visível (validado no --web com inferência real).
- [x] Resposta normal intacta (condição cirúrgica).
- [x] Smoke + invariantes 14/14 + gauntlet 19/19; ruff/acentuação limpos.

---

*"A intenção entregue, não a sintaxe que a carregou." -- anônimo*
