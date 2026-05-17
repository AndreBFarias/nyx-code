# SPRINT UX-CLAUDE-PARITY-01 — Paridade de estabilidade e layout com Claude Code CLI

## 0. SPEC (machine-readable)

```yaml
sprint:
  id: UX-CLAUDE-PARITY-01
  title: "Layout do Nyx imita estabilidade e organização visual do Claude Code CLI (mantém identidade Nyx)"
  onda: 23
  bloco: 23.4 Gamedesigner
  prioridade: ALTA
  tipo: Feature+UX
  dependencias: [UX-BUG-02B, UX-LOOP-VISIBILITY-01]
  desbloqueia: []
  origem: "Usuário em 2026-05-16: 'pode deixar o layout funcionando e imitando a estabilidade e layout do Claude Code no terminal?' — comparação feita com screenshots reais lado a lado durante validação UX-BUG-02B."

  touches:
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/agent/banner.py
      reason: "Banner compacto estilo Claude Code: logo + 3 linhas de info, em vez de caixa ASCII de 9 linhas"
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/cli.py
      reason: "Prompt com box thin-border ao redor do input (paridade Claude Code), toolbar com formato pipe-separator"
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/agent/output.py
      reason: "Render_user_input já tem box; padronizar para mesmo glyph set do Claude Code (─│╭╮╰╯)"
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/themes/design_tokens.py
      reason: "Adicionar tokens de spacing e box style estilo Claude Code"

  creates:
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/dev-journey/03-decisions/ADR_029_LAYOUT_PARITY.md
      reason: "Documentar decisão: paridade ESTRUTURAL com Claude Code, identidade Nyx mantida (turquesa+roxo, glifos)"

  removes: []

  n_to_n_pairs:
    - descricao: "Box chars (╭╮╰╯─│) já em design_tokens; cli.py + output.py + banner.py importam de lá"
      paths:
        - /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/themes/design_tokens.py
        - /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/agent/banner.py
        - /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/agent/output.py
        - /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/cli.py

  forbidden:
    - "Trocar paleta D (turquesa #00D4AA + roxo #9D4EDD) — ADR-023 mantida"
    - "Remover '○ cold/◐ warming/● warm' (UX-BUG-02B + UX-LOOP-VISIBILITY-01)"
    - "Adicionar emoji"
    - "Quebrar bottom_toolbar quando terminal redimensiona"
    - "Renomear comandos (/help, /memory, etc.)"
    - "Esconder a identidade Nyx (logo, nome, glifos)"

  tests:
    - cmd: "./run.sh --gauntlet --only tui"
      timeout: 300
      deve_passar: true
    - cmd: "./run.sh --gauntlet --only rapido"
      timeout: 300
      deve_passar: true
    - cmd: "manual: rodar Nyx, capturar PNG, comparar com Claude Code screenshot lado a lado"
      deve_passar: "paridade estrutural visível (banner top, prompt central com box, toolbar bottom com pipe-separator)"

  acceptance_criteria:
    - "Banner compacto: máximo 5 linhas, com logo turquesa + nome + versão + info mínima (modelo, projeto, contexto)"
    - "Prompt: input com box border (╭─╮│╰╯) ao redor, estilo Claude Code"
    - "Bottom toolbar: formato 'Nyx-Code | dev | qwen3:4b | ctx 8% | ○ cold' com pipes (|) em vez de · separator (paridade visual com Claude Code)"
    - "Bypass: mantém 'shift+tab: bypass' embaixo da toolbar, estilo Claude Code"
    - "Estabilidade: layout não quebra em redimensionamento do terminal (testar com 80, 100, 120, 160 cols)"
    - "Estabilidade: tee no boot não corrompe layout (prompt-toolkit detecta fallback corretamente)"
    - "Identidade Nyx preservada: paleta turquesa+roxo, glifos próprios (○◐●), microcopy PT-BR"
    - "ADR-029 criado documentando decisão de paridade estrutural mantendo identidade visual"
    - "PT-BR acentuado, zero emoji, zero menção a IA"
    - "Smoke + invariants passam"
```

---

**Status:** PENDENTE
**Data criação:** 2026-05-16
**Modelo obrigatório:** claude-opus-4-7 (sem subagentes)
**Origem:** comparação direta Nyx vs Claude Code via screenshots reais em 2026-05-16, durante validação visual de UX-BUG-02B.

---

# Sprint UX-CLAUDE-PARITY-01

## Contexto

Durante validação visual de UX-BUG-02B, o usuário compartilhou screenshots reais comparando Nyx-Code com Claude Code CLI rodando em terminal. Diagnóstico:

**Equivalências estruturais já presentes:**
- Banner top
- Prompt central com echo do input
- Bottom toolbar com info dinâmica
- Bypass toggle visual

**Diferenças de polimento:**

| Aspecto | Claude Code | Nyx atual | Gap |
|---|---|---|---|
| Banner | Logo + 3 linhas (Logo · v2.1.143 · Opus · path) | Caixa ASCII de 9 linhas | Nyx é maior, ocupa mais tela |
| Prompt | Box border thin-line ao redor do input | Linha sem border (`nyx> `) | Sem visual cue de "área de input" |
| Toolbar separator | `Luna \| dev \| Opus \| $0.00 \| brief:187L` (pipes) | `ctx 8% · qwen3:4b · iter 0 · ○ cold` (middle dots) | Estética diferente |
| Bypass | `▸▸ bypass permissions on (shift+tab to cycle)` em laranja | `[ ] shift+tab: bypass` | Menos destaque |

**Identidade Nyx que NÃO pode mudar:**
- Paleta D (turquesa #00D4AA + roxo #9D4EDD)
- Glifos ○◐● para estado do modelo
- Microcopy PT-BR
- Nome "Nyx" (zero menção a IA)

## Solução conceitual

Aplicar **paridade estrutural** (organização visual idêntica) mantendo **identidade própria** (cores, glifos, PT-BR):

```
┌──────────────────────────────────────────────────────────────┐
│  Nyx  v1.2.0                                       qwen3:4b  │  <-- banner compacto (3 linhas)
│  Nyx-Code · ~/Desenvolvimento/Nyx-Code                       │
│                                                              │
│  ╭─────────────────────────────────────────────────────────╮ │  <-- prompt com box (paridade Claude Code)
│  │ > diga ola_                                             │ │
│  ╰─────────────────────────────────────────────────────────╯ │
│                                                              │
│  ⠋ pensando... (3s · ◐ warming)                             │  <-- spinner enriquecido (UX-LOOP-VISIBILITY-01)
│                                                              │
│  ────────────────────────────────────────────────────────── │
│  Nyx-Code | dev | qwen3:4b | ctx 8% | ● warm                │  <-- toolbar com pipes
│  ▸▸ shift+tab: bypass                                       │
└──────────────────────────────────────────────────────────────┘
```

## ADR-029 (a criar)

**Título:** Layout Parity com Claude Code CLI mantendo identidade Nyx.

**Decisão:** Adotar organização visual (banner compacto + prompt-box + toolbar-pipes) como paridade estrutural. Identidade visual (cores, glifos, microcopy) permanece. Não é "skin de Claude Code" — é princípio de **familiaridade cognitiva** com a ferramenta de referência do mercado.

**Por quê:** redução de carga cognitiva ao alternar entre Nyx e Claude Code; aproveitamento de affordances já aprendidas pelo usuário; ADR-001 (Local First) não viola — é só layout.

## Verificação manual obrigatória

```bash
./run.sh
# Avaliação visual:
#   1. Banner ocupa menos de 6 linhas? Sim/Não
#   2. Prompt tem box border ao redor? Sim/Não
#   3. Toolbar usa pipes em vez de · ? Sim/Não
#   4. Cores turquesa/roxo preservadas? Sim/Não
#   5. Glifos ○◐● na toolbar/spinner? Sim/Não
#   6. PT-BR acentuado em todas as strings? Sim/Não
#
# Comparação lado a lado com screenshot do Claude Code:
#   organização ≈ Claude Code, identidade = Nyx
```

## Riscos

| Risco | Mitigação |
|---|---|
| Box border quebra em terminais sem suporte a Unicode | Fallback para ASCII (`+- `) em locale não-UTF-8 (já existe em TUI-FIX-07A) |
| Paleta perde identidade ao copiar Claude Code | ADR-029 explicitamente proíbe trocar paleta D |
| Banner compacto perde info importante (visão, memória) | Mover info detalhada para `/info` command; banner só tem essencial |
| Usuário acha estranho (ele se acostumou com banner grande) | Validação visual obrigatória + opção de voltar via `/layout legacy` |

---

*"Familiar não é igual; identidade não é cópia." -- princípio de paridade estrutural*
