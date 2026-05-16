# ADR-026 — Agência: o usuário sempre sente que controla

**Status:** PROPOSTO
**Data:** 2026-05-15
**Contexto da Onda:** 23, Bloco 23.4, UX-AGENCY-01

## Contexto

ADR-025 (Loop de Experiência) define **quando** o feedback acontece. Esta
ADR define **como** o usuário se mantém no controle: princípios de agência
e tutorial-sem-tutorial aplicados ao Nyx.

Princípio de gamedesign: o jogador (aqui, dev humano OU Claude via MCP)
nunca deve se sentir empurrado pela máquina, nunca deve precisar adivinhar
o que fazer a seguir, e nunca deve perder estado por uma ação sem retorno.

## Decisão

Toda interação Nyx (TUI + Cockpit) honra estes 4 contratos:

### 1. Affordances visíveis

Cada momento da experiência mostra o que **pode** ser feito agora:
- Footer da TUI: atalhos do contexto atual (Ctrl+R, Ctrl+D, /, etc.)
- Cursor: pulse 1Hz idle, sólido durante streaming, ausente durante input
  bloqueado.
- Prompt prefix sinaliza estado (`nyx |` neutro, `nyx ?` aguardando
  resposta a uma pergunta, `nyx !` modo bypass).

### 2. `/?` em qualquer ponto

Comando `/?` (alias de `/help` contextual) **sempre** mostra opções
relevantes àquele momento:
- Antes do primeiro input: tutorial-sem-tutorial (3 ações principais).
- Durante tool call: cancelar (Ctrl+C), reagendar (`/pause`), inspecionar.
- Após resposta longa: scroll, copy, retry, edit.
- Em erro: actionable específico (não "tente novamente").

### 3. Comandos sempre cancela­veis

Toda operação tem **kill-switch claro**:
- Ctrl+C interrompe sem corromper estado.
- `/cancel` cancela tool call em curso.
- ESC fecha popups, modos especiais, autocomplete.
- Operações destrutivas (delete, force-push, etc.) sempre confirmam
  antes (via `ask_user` tool ou Cockpit modal).

### 4. Nada de "mágica" indecifrável

Toda decisão automática do Nyx é **visível** no output:
- Tool selection: "Vou usar Read porque..."
- Auto-tune: "VRAM live mudou; ajustando num_gpu para X"
- Compaction: "Contexto >70%; sumarizando..." (não em silêncio)
- Memory recall: "Lembrando: <fact> [de <data>]"

Se algo aconteceu, foi nomeado. Se não foi nomeado, não aconteceu.

## Tutorial-sem-tutorial

Onboarding implícito: o usuário aprende as power-features pelo uso.
Mecanismos:
- Primeira run: banner adiciona linha "tente: /help, /memory, Ctrl+R"
- Após N tool calls bem-sucedidas, hint sutil mostra um atalho relacionado.
- `/?` é o tutorial contextual permanente.

Anti-padrões:
- Modal de tutorial obrigatório no primeiro start (interrompe flow).
- Tooltips invasivos.
- Onda de explicações sem ação (read-only é cansativo).

## Consequências

**Positivas:**
- Curva de aprendizagem natural; usuário descobre power-features quando
  está pronto.
- Claude (via MCP) tem mesma "agência" — `/?` retorna estado consultável.
- Footer + prompt prefix são fonte rápida de status do sistema.

**Neutras:**
- Adiciona complexidade ao footer e prompt prefix (estado dinâmico).

**Negativas:**
- Auditoria de microcopy precisa: todo erro e sucesso precisa ter
  actionable ou confirmação claros. ADR-027 trata isso explicitamente.

## Alternativas consideradas

**Alt A (modal tutorial first-run):** rejeitada — interrompe flow,
viola princípio "tutorial sem tutorial".

**Alt B (sem footer; só /help):** rejeitada — quebra "affordances visíveis"
(usuário precisaria invocar help para saber o que existe).

## Verificação

Sprint UX-AGENCY-01 implementa e mede:
1. `/?` em estados diferentes retorna conteúdo diferente (e relevante).
2. Footer atualiza ao mudar de modo (bypass on/off).
3. Ctrl+C cancela tool call em andamento sem corromper REPL.
4. Cada erro de tool tem actionable nomeado (audit grep).

## Referências

- ADR-023 (paleta D).
- ADR-024 (render layer).
- ADR-025 (Loop de Experiência).
- Memória: `feedback_gamedesign_filosofia.md`.

---

*"A sensação de controle é o oposto da magia." -- anônimo*
