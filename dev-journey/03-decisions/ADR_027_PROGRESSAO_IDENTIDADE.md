# ADR-027 — Progressão & Identidade Nyx

**Status:** PROPOSTO
**Data:** 2026-05-15
**Contexto da Onda:** 23, Bloco 23.4, UX-PROGRESSION-01

## Contexto

ADR-025 (Loop de Experiência) e ADR-026 (Agência) cobrem o ciclo
imediato. Falta o tempo longo: como o uso acumula contexto e como a
Nyx tem voz própria — não é "mais um agente", é Nyx.

## Decisão

### 1. Sense of progression — histórico visível

O usuário **sente** o passar do tempo na sessão:
- Banner mostra `memória: N entradas` (já existe; manter).
- `/recall` lista snippets navegáveis de inputs/outputs anteriores
  (já existe via memory module; melhorar microcopy).
- Ctrl+R abre busca incremental de comandos anteriores (já há base).
- `/sessions` lista sessões anteriores com timestamp + título inferido
  (a partir do primeiro user input).

### 2. Identidade Nyx — voz coerente

Nyx tem **personalidade**:
- PT-BR direto, frases curtas.
- Zero floreio, zero emoji (ADR-004).
- Zero menção a IA (ADR-005).
- Tom técnico mas não frio: erros têm actionable; sucessos têm
  confirmação concreta; não "ótimo!" genérico.
- Mensagens de sistema em primeira pessoa quando faz sentido:
  "Não encontrei X em Y." > "Erro: X não encontrado."

### 3. Microcopy auditado

Esta ADR autoriza a sprint UX-PROGRESSION-01 a fazer **audit
sistemático** das mensagens (erro, sucesso, prompts) do Nyx:
- Toda string user-facing entra numa tabela `dev-journey/05-guides/MICROCOPY.md`.
- Cada string tem: contexto, atual, proposta, motivação.
- Zero placeholder genérico ("operação concluída", "ok", "erro").

### 4. Continuidade entre sessões

- `/resume` (SESSION-RESUME-01) retoma última sessão (já planejado).
- Memória cross-session (CTX-02, já feito) preserva fatos importantes.
- Banner mostra "N entradas em memória" sutil.

## Vocabulário Nyx (não-vinculante, indicativo)

| Contexto | Em vez de | Use |
|---|---|---|
| Tool sucesso | "Sucesso." | "Pronto." / "Salvo em X." |
| Tool falha | "Erro: falha ao..." | "Não consegui X porque Y. Tenta Z." |
| Aguardando | "Carregando..." | "Carregando modelo..." (contexto explícito) |
| Compaction | "Resumindo..." | "Contexto cheio; condensando histórico..." |
| Quit | "Adeus" | "Até." (curto, identidade) |

## Anti-padrões

- Emojis para "amigar" a interface.
- Mensagens floridas ("Que ótimo, tudo funcionou perfeitamente!").
- Genéricos vazios ("Algo deu errado.").
- Inglês em microcopy ("Loading...", "Done!").
- Identidade alterada por sprint (manter voz Nyx em todas).

## Consequências

**Positivas:**
- Cada interação reforça quem é a Nyx.
- Microcopy auditado vira invariante; gauntlet pode validar.
- Reduz "alucinação UX" — fonte única em MICROCOPY.md.

**Neutras:**
- Trabalho contínuo de manutenção: novas mensagens passam por audit.

**Negativas:**
- Pode soar "frio" em algumas situações. Trade-off aceito: identidade >
  warmth genérica.

## Alternativas consideradas

**Alt A (warm, friendly):** rejeitada — vira "mais um chatbot".

**Alt B (apenas técnico, sem voz):** rejeitada — perde identidade.

**Alt C (mista, configurável):** rejeitada — fragmenta identidade.

## Verificação

Sprint UX-PROGRESSION-01 implementa:
1. MICROCOPY.md criado com audit das mensagens atuais.
2. Refactor das mensagens conforme tabela.
3. Test no Gauntlet: `--only microcopy` valida ausência de placeholders
   genéricos (lista negra: "ok", "loading", "error", "done", "success"
   isolados).

## Referências

- ADR-004 (Zero Emojis), ADR-005 (Anonimato), ADR-006 (PT-BR).
- ADR-025 (Loop), ADR-026 (Agência).

---

*"Voz é o que sobra quando você tira tudo que poderia ser de outro." -- anônimo*
