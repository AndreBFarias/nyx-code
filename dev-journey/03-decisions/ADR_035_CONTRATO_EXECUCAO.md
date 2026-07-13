# ADR-035 — CONTRATO DE EXECUÇÃO

**Status:** ACEITO
**Data:** 2026-07-12
**Onda:** 48 (Validação a-fundo)

## Contexto

A onda de validação as-user de 2026-06-26 (`AUDIT_VALIDACAO_2026_06_26.md`) provou
que 7 bugs distintos (V02-V07, V14) eram na verdade UM mecanismo ausente: nada
garantia que o que o modelo diz ter feito corresponde ao que a infra executou e ao
que o usuário vê. O desenho arquitetural
`dev-journey/02-architecture/DESENHO_CONTRATO_EXECUCAO.md` (2026-06-26) propôs o
contrato; este ADR o formaliza — a condição declarada no desenho ("formalizar
quando a primeira sprint da fase raiz fechar") foi atingida com o núcleo 397-401
concluído e a validação holística executada (2026-07-12).

## Decisão

**Todo turno com intenção de ação obedece a três garantias, aplicadas em pontos
determinísticos do loop — nunca delegadas ao modelo ([[ADR-032]]):**

- **G1 — Tool bem-formada e pertinente.** Antes de executar: args sanitizados
  (397, `nyx/agent/sanitize.py`), tool compatível com o intent do pedido (398),
  edição sequencial usa edição e não overwrite cego nem shell-como-content (401).
- **G2 — Afirmado = produzido.** Turno que pede ação não conclui `done` com zero
  tools executadas (399); parser-fail não mascara tool_call cru como resposta —
  falha honesta em PT-BR (399).
- **G3 — Apresentado.** O dado real produzido pela tool aparece para o usuário
  sob `Resultado:`, abaixo da fala do modelo (399, apresentação forte); o output
  de uma tool nunca é realimentado como input da próxima (400, anti-recursão).

Princípios de mecanismo (DESENHO §6): rejeição de guard é SINAL de re-emissão
(1x por turno), nunca bloqueio definitivo; âncoras são ESTRUTURAIS (mutante vs
não-mutante, arquivo existe + não-lido), nunca semânticas; honestidade na falha
é preferível a sucesso fabricado.

## Estado da validação (2026-07-12)

Sessão holística contínua de 7 turnos, GPU exclusiva, contexto acumulado
(`AUDIT_2026_07_12.md` §2): **4 das 5 garantias SUSTENTADAS** (fastfetch, criação,
listagem, busca). A quinta (edição sequencial) não regrediu nos vetores que a 401
guarda, mas revelou mecanismo fora do contrato: drift de path em contexto
acumulado com falso sucesso (sprint 437). O contrato é válido e ativo; 437, 402
(recall) e 403 (model swap honesto) completam a família.

## Divergência registrada (ponto D)

O desenho previa, no parser-fail, "tentar executar o candidato OU falhar
honesto". A implementação cobre apenas o ramo "falhar honesto"
(`_core.py:499-504`). Decisão: o ramo "tentar executar" fica NÃO implementado por
ora — executar um tool_call que o parser não validou contraria a G1. Se evidência
futura mostrar perda relevante de turnos recuperáveis, abrir sprint própria.

## Consequências

### Positivas
- O pior modelo pode errar formato, escolher tool errada ou alucinar sucesso — a
  infra corrige, rejeita com hint ou falha honesta ([[ADR-033]], [[ADR-034]]).
- A confiança do usuário se ancora no `Resultado:` (dado real), não na fala.

### Negativas / custo aceito
- Guards determinísticos adicionam código ao loop (~5 mecanismos, 2 caminhos).
- Rejeição-com-hint consome 1 iteração extra em turnos que o modelo erra.

## Enforcement

- Gauntlet: fase as-user pelo headless cobrindo as garantias (sprint 433).
- Invariantes: line-refs do desenho corrigidas ao tocar o contrato; paridade dos
  DOIS caminhos de execução é critério de aceitação (sprint 416 fecha os gaps de
  paridade conhecidos: permissão, plan mode, hooks).
- Specs que toquem `_iteration.py`/`_core.py` citam qual garantia preservam.

## Referências
- `dev-journey/02-architecture/DESENHO_CONTRATO_EXECUCAO.md` (desenho completo,
  mapa sprint→garantia→ponto; line-refs de 2026-06-26 com drift conhecido).
- `dev-journey/07-reports/AUDIT_VALIDACAO_2026_06_26.md` (os 15 achados de origem).
- `dev-journey/07-reports/AUDIT_2026_07_12.md` (validação holística + achados 416-440).
- [[ADR-032]], [[ADR-033]], [[ADR-034]] — a infra carrega o modelo.

---

*"O modelo fala; a infra prova. O usuário acredita no Resultado:, não na fala."*
