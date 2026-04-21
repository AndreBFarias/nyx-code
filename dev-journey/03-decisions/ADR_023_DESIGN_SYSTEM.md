# ADR-023 — Design System Nyx: paleta D e tokens canônicos

**Status:** ACEITO
**Data:** 2026-04-18
**Contexto da Onda:** 22, Bloco 3, UX-DESIGN-01

## Contexto

Até esta data, cores e glifos estavam espalhados em `cli.py` e `output.py`
(8+ pontos com hex `#00D4AA` e escapes ANSI 24-bit hardcoded). Auditoria
externa (AUDIT-EXT-01) apontou como violação N-para-N (regras de meta
anti-regressão).

Havia ainda um caractere de emoji `U+26A1` (raio) usado como indicador de
bypass — violação direta de ADR-004 (Zero Emojis).

## Decisão

Adotar **paleta D** (decisão do usuário, 2026-04-18):

- **Estrutura visual:** CLI minimalista (box chars `╭╮╯╰─│`, hierarquia
  por indentação, sem caixas decorativas).
- **Cor principal:** turquesa histórica `#00D4AA`.
- **Cor de estados especiais** (bypass ON, memória, skills): roxo
  `#9D4EDD`.
- **Glifo de bypass:** `[!]` em vez do caractere U+26A1.

Criar `nyx/themes/design_tokens.py` como **única fonte** dessas
constantes. Qualquer módulo que renderize UI importa dela.

## Consequências

**Positivas**
- Mudança de paleta/glifo: 1 arquivo editado.
- Zero ambiguidade de cor entre módulos.
- Gauntlet pode validar invariante de "zero hex fora de `design_tokens.py`".

**Neutra**
- `nyx/themes/entities/*.json` continua existindo para temas
  alternativos (Luna, Eris, etc.). O tema default `nyx` passa a derivar
  dos tokens via `ThemeManager.get_ansi_colors("nyx")` (fonte única).

## Alternativas consideradas

| Paleta | Veredicto | Motivo |
|--------|-----------|--------|
| A (só CLI minimalista) | rejeitada | perde identidade Nyx |
| B (Gemini/Codex) | rejeitada | colorida demais, contraria noite |
| C (identidade full roxa) | rejeitada | quebra affordance do turquesa existente |
| **D (mista)** | **aceita** | estrutura CLI + turquesa histórico + roxo em estados especiais |

## Referências

- AUDIT-EXT-01 findings A-04 (cores N-para-N), A-06 (emoji U+26A1).
- Plano Onda 22, bloco 3.
- `nyx/themes/design_tokens.py` (implementação).

---

*"Consistência é a forma visível da atenção." -- anônimo*
