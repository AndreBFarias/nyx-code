# ADR-025 — Loop de Experiência: feedback contínuo como contrato de UX

**Status:** PROPOSTO
**Data:** 2026-05-15
**Contexto da Onda:** 23, Bloco 23.4, UX-LOOP-01

## Contexto

A Onda 22 fechou o que era estética: tokens canônicos (ADR-023), banner,
toolbar, cards de tool e streaming suave (UX-LAYOUT-01A/01B/02/03). Sobra
o que não é estética: **como cada interação se conecta numa experiência
coerente que tem identidade própria**. Pedido explícito do usuário
(2026-05-15): "gamedesign não pela estética, pela filosofia de pensar a
experiência única".

A Nyx hoje tem todas as peças (35 tools, 52 commands, 9 services, paleta
turquesa+roxo), mas o ciclo de uso ainda é "input → caixa preta → output"
em vários momentos. Faltam pontos canônicos de feedback no loop e uma
definição operável do que "feedback satisfatório" significa neste
projeto.

## Decisão

Adotar **Feedback Loop + Juicing** como pilar canônico do bloco 23.4.

O ciclo de uso Nyx tem 5 estágios; **cada um exige um ponto de feedback
obrigatório**:

```
[1] input recebido   ─→ ack visível < 100ms
[2] tool start       ─→ glyph + label + cronômetro arrancando
[3] tool result      ─→ glyph terminal + duração + linha-de-status
[4] resposta agente  ─→ streaming com cursor vivo; sem flicker
[5] próximo prompt   ─→ footer atualizado mostra atalhos relevantes agora
```

### Tempos de feedback (orçamento perceptual)

| Estágio | Indício máximo | Resposta completa máxima |
|---|---|---|
| 1 input | 50 ms | 100 ms |
| 2 tool start | 100 ms | 300 ms |
| 3 tool result | 200 ms (após tool retornar) | 500 ms |
| 4 streaming | 200 ms até 1º token | streaming contínuo, frame budget 16 ms |
| 5 next prompt | 100 ms | 300 ms |

Acima desses limites a experiência **degrada** e o usuário perde flow. A
sprint UX-LOOP-01 verifica esses tempos com benchmark real.

### Juicing — feedback satisfatório

**Cada ação dá retorno sensorial dentro dos limites da TUI/Web:**
- Tool call ativo: glyph com microanimação (já temos spinner braille;
  estender para tool-call ativo).
- Tool sucesso: confirmação tonal (cor accent suave).
- Tool erro: cor de erro + sugestão actionable na mesma linha (já em parte).
- Comando aceito: fade-in no input echo.
- Comando rejeitado: shake sutil (em terminais que suportam) ou cor
  vermelha pulsada.

### Anti-patterns proibidos

1. Tela "muda" por mais de 1s sem indício de progresso.
2. Output em batch sem ordem cronológica visível (caixa-preta).
3. Erro sem actionable ("falhou" sozinho).
4. Sucesso silencioso em operação que demorou >500ms.
5. Spinner que não avança (impostor — pior que silêncio).

## Consequências

**Positivas:**
- Sense of agency: usuário sempre sabe o que está acontecendo.
- Bench objetivo: tempos viram invariante mensurável no Gauntlet.
- Aplica tanto à TUI quanto ao Cockpit web (ADR é fonte única).
- Após aprovação desta ADR, **toda sprint Onda 22 e 23 ganha critério
  de aceite "ADR-025 aplicado"** (princípios honrados nos pontos de
  feedback que a sprint toca).

**Neutras:**
- Não muda paleta nem glifo (ADR-023 fica intacto). Muda *quando* e
  *como* eles aparecem.

**Negativas:**
- Algumas sprints já concluídas (UX-LAYOUT-02 cards, UX-LAYOUT-03
  streaming) podem precisar de pequenos ajustes para entrar no
  contrato; serão tratados como achados colaterais conforme aparecerem
  (protocolo anti-débito).

## Alternativas consideradas

**Alt A (silêncio é design):** confiar que o usuário lê o output e não
precisa de feedback explícito. Rejeitada — viola "agency" e cria
caixa-preta perceptual.

**Alt B (apenas tempos, sem juicing):** documentar só os limites de
tempo, sem prescrever microinterações. Rejeitada — limita-se ao mínimo
e perde a parte de "experiência única" pedida pelo usuário.

**Alt C (motion tokens primeiro, filosofia depois):** começar por
ADR-025 "Motion Tokens" e adiar a filosofia. Rejeitada — o usuário
corrigiu explicitamente: filosofia é o pilar, motion serve a ela.

## Impacto em ADRs adjacentes

- **ADR-023 (Design System paleta D):** continua sendo a fonte única
  de cores e glifos; ADR-025 só governa *quando* eles entram em cena.
- **ADR-004 (Zero Emojis):** mantido. Juicing acontece via cor, fade,
  tempo e microcopy — não via emoji.
- **ADR-006 (PT-BR):** mantido. Microcopy auditado por ADR-027
  (Progressão & Identidade) que vem em seguida.

## Verificação

A sprint UX-LOOP-01 implementa e mede:
1. `./run.sh --gauntlet --only loop` (fase nova) verifica todos os 5
   pontos de feedback do ciclo.
2. Benchmark: comando trivial (`/help`) tem ack <100ms; tool call
   simples (Read README.md) tem indício <300ms.
3. Inspeção manual: tela "muda" >1s nunca acontece em uso normal.

## Referências

- Plano consolidado: `~/.claude/plans/venv-andrefarias-nitro-5-desenvolviment-declarative-spark.md`.
- ADR-023 (Design System paleta D).
- Memória: `feedback_gamedesign_filosofia.md`.

---

*"O que o jogador vê acontecer entre dois cliques é onde o jogo mora." -- anônimo*
