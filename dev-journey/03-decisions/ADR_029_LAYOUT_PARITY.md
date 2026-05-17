# ADR-029 — Layout Parity com Claude Code CLI mantendo identidade Nyx

**Status:** ACEITO
**Data:** 2026-05-17
**Contexto da Onda:** 23, Bloco 23.4 Gamedesigner, UX-CLAUDE-PARITY-01

## Contexto

Durante validação visual de UX-BUG-02B, o usuário comparou Nyx-Code com
Claude Code CLI lado-a-lado em screenshots reais. Diagnóstico:

| Aspecto | Claude Code CLI | Nyx (antes) | Decisão |
|---|---|---|---|
| Banner | Logo + 3 linhas (Logo · v · model · path) | Caixa ASCII 9 linhas | **Compactar** |
| Toolbar separator | `Luna \| dev \| Opus \| ctx 8%` (pipes) | `ctx 8% · qwen · iter 0` (·) | **Migrar para `\|`** |
| Bypass off | `▸▸ shift+tab to cycle bypass` | `[ ] shift+tab: bypass` | **Adotar `▸▸` prefix** |

## Decisão

Adotar **paridade estrutural** com Claude Code CLI (organização visual)
mantendo **identidade própria** (cores, glifos, microcopy PT-BR).

Aplicado em três frentes:

1. **Banner** (`nyx/agent/banner.py::_build_wide`): reduzido de 9 linhas
   (caixa com 4 colunas de info) para 3 linhas (`Nyx vX  |  100% offline`,
   linha de contexto inline, linha de atalhos). Identidade preservada por
   ANSI_ACCENT_FG (turquesa Nyx) no logo.

2. **Toolbar** (`nyx/cli.py::_bottom_toolbar`): separators ` · ` (middle
   dot) substituídos por `  |  ` (pipe com espaço duplo). Mantém glifos
   `○ cold | ◐ warming | ● warm` (UX-BUG-02B + UX-LOOP-VISIBILITY-01)
   intactos como signature visual.

3. **Bypass off** (`nyx/cli.py::_bottom_toolbar`): `[ ] shift+tab: bypass`
   substituído por `▸▸ shift+tab: bypass`. Inspiração direta do prompt
   de bypass do Claude Code. Bypass ON ganha sufixo "(shift+tab)" no
   highlight roxo para reforçar a ação reversa.

## Identidade Nyx que NÃO mudou

- Paleta D: turquesa `#00D4AA` (NYX_PRIMARY) + roxo `#9D4EDD` (NYX_PURPLE).
- Glifos `○ ◐ ●` (Geometric Shapes Unicode, ADR-004 exceção).
- Microcopy 100% PT-BR (`iter`, `lidos`, `modif`, `aquecendo modelo...`).
- Nome `Nyx` (zero menção a IA, ADR-005).

## Consequências

- **Positiva:** redução de carga cognitiva ao alternar entre Nyx e
  Claude Code; aproveitamento de affordances já aprendidas pelo usuário.
- **Positiva:** banner ocupa 5 linhas em vez de 11 — mais real-estate
  para conversa.
- **Positiva:** toolbar com pipes é mais legível em terminais largos
  (160+ cols) — `|` separa visualmente melhor que `·`.
- **Neutra:** mudança apenas de layout, não afeta tools ou comandos
  (ADR-001 Local First inalterado).
- **Negativa:** usuários acostumados ao banner grande precisam reaprender
  a leitura — mitigada por manter informação essencial em todas as 3
  linhas novas.

## Referências

- UX-BUG-02B (glifos cold/warming/warm na toolbar).
- UX-LOOP-VISIBILITY-01 (spinner com label dinâmico).
- ADR-023 Design System (paleta D).
- ADR-024 Render Layer.

*"Familiar não é igual; identidade não é cópia." — princípio de paridade estrutural*
