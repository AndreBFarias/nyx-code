# SPRINT 300 — TUI-THINKING-EXPAND-01

## 0. SPEC

```yaml
sprint:
  id: TUI-THINKING-EXPAND-01
  title: "Re-portar o thinking block (raciocínio do modelo) para a TUI Textual como bloco RECOLHÍVEL: a bridge passa a consumir agent._on_thinking e monta um Collapsible no #chat (expand/collapse nativo do Textual, sem reusar o Tab do ghost da 286)"
  onda: 34
  prioridade: MEDIA
  tipo: Feature
  dependencias: [TUI-CHAT-MARKDOWN-SYNTAX-01]
  desbloqueia: []

  origem: "Matriz de auditoria ONDA-34 (plano redesign, linhas 32/90): 'Expand thinking block (Tab -> render_thinking_block) PERDIDO' na migração Textual (fonte era repl_app.py:337-347, deletado). Na TUI Textual o reasoning era DROPADO -- a bridge nunca consumia _on_thinking."

  touches:
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/agent/tui/app.py
      reason: "Imports Markdown + Collapsible/Static + glifo _THINKING_GLYPH=chr(0x25D0); bridge patcheia agent._on_thinking=self._on_agent_thinking; método _on_agent_thinking(reasoning) monta Collapsible(Static(Markdown(reasoning)), collapsed=True, classes='thinking') no #chat."
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/agent/tui/styles/nyx.tcss
      reason: "Regra Collapsible.thinking (cor $muted, margin) -- raciocínio como info auxiliar/secundária."
  creates: []
  removes: []

  forbidden:
    - "Reusar Tab para expand (Tab é accept-ghost no input desde a 286) -- usar o expand nativo do Collapsible (clique/foco+Enter)"
    - "Mudar a assinatura do AgentLoop ou de _on_thinking (consumir o callback existente, não criar novo)"
    - "Renderizar o reasoning EXPANDIDO por padrão (polui a conversa) -- collapsed=True"
    - "Quebrar lazy-mount (283) / labels (297) / markdown (299) -- o thinking é um widget à parte no #chat"

  tests:
    - cmd: "./run.sh --smoke"
      timeout: 15
      deve_passar: true
    - cmd: "bash scripts/sprint_invariants.sh"
      timeout: 60
      deve_passar: true

  acceptance_criteria:
    - "agent._on_thinking patcheado pela bridge -> reasoning chega à TUI (antes dropado)"
    - "reasoning vira Collapsible RECOLHIDO no #chat com título '◐ pensando'"
    - "expand/collapse funciona nativamente (collapsed True->False mostra o raciocínio)"
    - "reasoning renderizado como Markdown; cor muted via Collapsible.thinking"
    - "invariantes 14/14; ruff limpo; sem conflito de Tab"
```

## 1. PROOF-OF-WORK (CONCLUIDA — 2026-05-30)

**Achado-chave:** o AgentLoop JÁ emite o reasoning via `_on_thinking(reasoning)` (1 arg string,
chamado em `loop/_iteration.py:517`, loop principal) — mesmo shape de `_on_tool`. A bridge da
TUI (app.py) patchava `_on_token`/`_on_tool`/`_on_tool_result` mas NÃO `_on_thinking`, então o
reasoning era silenciosamente dropado. O fix consome o callback existente (zero mudança no loop).

**Implementação (2 arquivos):**
- `app.py`: imports `Markdown` (rich), `Collapsible`/`Static` (textual), constante
  `_THINKING_GLYPH=chr(0x25D0)` (anti-sanitizer); bridge `agent._on_thinking=self._on_agent_thinking`;
  método `_on_agent_thinking(reasoning)` monta `Collapsible(Static(Markdown(reasoning)),
  title="◐ pensando", collapsed=True, classes="thinking")` no #chat + scroll_end.
- `nyx.tcss`: `Collapsible.thinking { color: $muted; margin: 1 0 0 0; }`.

**Por que Collapsible (e não o Tab original):** o Textual `Collapsible` traz expand/collapse
nativo (clique no título ou foco+Enter), eliminando o conflito de Tab (que virou accept-ghost
do input na 286). O reasoning fica RECOLHIDO por padrão (não polui), expansível sob demanda.

**Validação:**
- Pilot (chamando `_on_agent_thinking` direto): Collapsible montado `collapsed=True`,
  classes `{thinking, -collapsed}`; setar `collapsed=False` expande e mostra o raciocínio.
- **Visual (Pilot SVG→PNG):** `/tmp/think_collapsed.png` ("▶ ◐ pensando" compacto);
  `/tmp/think_expanded.png` ("▼ ◐ pensando" + raciocínio em Markdown muted, acima da resposta
  do NyxCode com seu code block colorido) — compõe com 297/298/299.
- `py_compile` OK; `validar-acentuacao` (app.py) rc 0; `ruff` "All checks passed!".
- `./run.sh --smoke` (invariantes #13): boot OK.
- `bash scripts/sprint_invariants.sh`: 14/14 (FAIL=0).
- `./run.sh --gauntlet --only rapido`: APROVADO.

**Nota de ordenação (refinamento futuro):** com streaming, o reasoning é extraído da mensagem
COMPLETA, então o Collapsible aparece após o texto streamado da resposta. Aceitável para v1
(recolhido por padrão); ordenar o thinking ANTES da resposta exigiria buffering — fora de escopo.
