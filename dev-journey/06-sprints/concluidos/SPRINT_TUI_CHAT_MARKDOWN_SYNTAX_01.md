# SPRINT 299 — TUI-CHAT-MARKDOWN-SYNTAX-01

## 0. SPEC

```yaml
sprint:
  id: TUI-CHAT-MARKDOWN-SYNTAX-01
  title: "Renderizar o conteúdo das mensagens do assistant (NyxCode) como Markdown: blocos ``` ganham syntax highlight (Rich/pygments), listas/ênfase/headers formatados -- entrega a metade 'syntax highlight em blocos' do item de auditoria TUI-CODE-COPY-BUTTON-01"
  onda: 34
  prioridade: MEDIA
  tipo: Feature
  dependencias: [TUI-CHAT-LABELS-COLORS-01]
  desbloqueia: [TUI-CODE-COPY-BUTTON-01]

  origem: "Matriz de auditoria ONDA-34 (plano redesign, linha 43/83): blocos de código sem syntax highlight; plano pede 'syntax highlight em blocos ``` (render Syntax/Markdown)'. A outra metade (botão copiar) fica registrada à parte."

  touches:
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/agent/tui/widgets/chat_message.py
      reason: "Importar Group (rich.console) e Markdown (rich.markdown); no role assistant, render() retorna Group(label_roxo, Markdown(content)) em vez de Text plano. user/tool/system inalterados (Text)."
  creates: []
  removes: []

  forbidden:
    - "Retornar str de render() (re-introduziria o crash get_height do Textual 8.x) -- só renderables Rich"
    - "Renderizar user/tool/system como Markdown (entrada do usuário e output estruturado ficam plain Text)"
    - "Remover/corromper _DIAMOND=chr(0x25C6) ou regredir o label colorido da 297"
    - "Adicionar dependência nova (Rich + pygments já presentes)"

  tests:
    - cmd: "./run.sh --smoke"
      timeout: 15
      deve_passar: true
    - cmd: "bash scripts/sprint_invariants.sh"
      timeout: 60
      deve_passar: true

  acceptance_criteria:
    - "assistant com bloco ``` renderiza código com syntax highlight (cores pygments/Monokai)"
    - "assistant render retorna Group contendo Markdown; label '◆ NyxCode' roxo preservado"
    - "user/tool/system continuam Text plano"
    - "streaming não crasha mesmo com ``` ainda aberto mid-stream"
    - "invariantes 14/14; ruff limpo"
```

## 1. PROOF-OF-WORK (CONCLUIDA — 2026-05-30)

**Implementação (1 arquivo — chat_message.py):**
- Imports: `from rich.console import Group`, `from rich.markdown import Markdown`.
- render() assistant: `label = Text("◆ NyxCode", style=NYX_PURPLE)`; com conteúdo retorna
  `Group(label, Markdown(self._content))`. Sem conteúdo, só o label (lazy-mount da 283 intacto).
- user/tool/system: inalterados (Text plano; 297 preservado).

**De-risk (Pilot, antes de implementar):**
- Markdown em Static NÃO dispara o crash `get_height` (o motivo histórico de render() retornar
  Text) -- testado, render limpo com código colorido.
- Streaming token-a-token de um bloco ``` (incluindo estado com ``` ainda ABERTO mid-stream):
  zero crash -- Markdown tolera markdown parcial.

**Validação:**
- Render direto: assistant → `Group` contendo `Markdown` (True); user → `Text`.
- `py_compile` OK; `validar-acentuacao` rc 0; `ruff check` "All checks passed!".
- `./run.sh --smoke` (invariantes #13): boot OK.
- `bash scripts/sprint_invariants.sh`: 14/14 (FAIL=0).
- **Visual (Pilot SVG→PNG `/tmp/md_real.png`):** no NyxTUI real, bloco ```python``` com syntax
  highlight Monokai (def/return ciano, função verde, string amarela, fundo escuro) + lista
  formatada; compõe corretamente com 297 (labels coloridos) e 298 (banner rolável).
- `./run.sh --gauntlet --only rapido`: APROVADO.

**Escopo separado:** a outra metade do item de auditoria — o BOTÃO COPIAR — fica registrada
como TUI-CODE-COPY-BUTTON-01 PENDENTE (Textual Button + clipboard envolve mouse/OSC52; baixo
valor sobre a seleção nativa do terminal/xterm.js; decisão dedicada a seguir).
