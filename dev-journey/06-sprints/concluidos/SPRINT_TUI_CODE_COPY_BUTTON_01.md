# SPRINT 301 — TUI-CODE-COPY-BUTTON-01

## 0. SPEC

```yaml
sprint:
  id: TUI-CODE-COPY-BUTTON-01
  title: "Copiar bloco de código: Ctrl+Y copia o último bloco ``` da última mensagem do NyxCode para a área de transferência via OSC52 (copy_to_clipboard nativo do Textual). Fecha a outra metade do item de auditoria (a metade syntax-highlight saiu na 299)"
  onda: 34
  prioridade: MEDIA
  tipo: Feature
  dependencias: [TUI-CHAT-MARKDOWN-SYNTAX-01]
  desbloqueia: []

  origem: "Matriz de auditoria ONDA-34 (plano redesign, linhas 43/83): 'Botão copiar código AUSENTE'. A metade syntax-highlight foi entregue na SPRINT 299; resta o mecanismo de cópia."

  decisao_de_design: |
    O plano pedia um BOTÃO (mouse) por bloco. Decisão de engenharia: entregar a
    CÓPIA (o fim) via atalho de teclado (o meio), não um botão-mouse, porque:
    (a) um botão por bloco exigiria QUEBRAR o render Markdown único da 299 em
        segmentos texto/CodeWidget + plumbing de mouse/OSC52 por widget — alto
        custo, rearquitetura da 299;
    (b) atalho de teclado é idiomático em TUI/terminal e aparece no rodapé de
        bindings (descobrível);
    (c) Textual 8.2.7 expõe `App.copy_to_clipboard` (OSC52) que funciona no
        terminal E no --web/xterm.js sem mouse.
    Copiar código (vs seleção-mouse manual, que pega number-gutter/wrap) é o
    ganho real para um agente de código. Botão-mouse literal fica revisitável.

  touches:
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/agent/tui/app.py
      reason: "import re + _CODE_FENCE_RE; Binding ctrl+y -> action_copy_last_code; método varre o #chat de baixo p/ cima pela última ChatMessage assistant com fence ```, extrai o último bloco e chama copy_to_clipboard + notify."
  creates: []
  removes: []

  forbidden:
    - "Quebrar o render Markdown da 299 (o copy lê msg.content, não toca o render)"
    - "Usar uma tecla já ligada (ctrl+y é livre; input não o consome)"
    - "Mudar a assinatura pública de ChatMessage/NyxTUI"

  tests:
    - cmd: "./run.sh --smoke"
      timeout: 15
      deve_passar: true
    - cmd: "bash scripts/sprint_invariants.sh"
      timeout: 60
      deve_passar: true

  acceptance_criteria:
    - "Ctrl+Y copia o ÚLTIMO bloco ``` da última mensagem assistant (pula blocos anteriores)"
    - "copy_to_clipboard chamado com o código limpo (sem a fence ```lang nem trailing newline)"
    - "notify de sucesso; severity=warning quando não há bloco"
    - "funciona via OSC52 no terminal e no --web; invariantes 14/14; ruff limpo"
```

## 1. PROOF-OF-WORK (CONCLUIDA — 2026-05-30)

**Implementação (1 arquivo — app.py):**
- `import re` + `_CODE_FENCE_RE = re.compile(r"```[^\n]*\n(.*?)```", re.DOTALL)`.
- `Binding("ctrl+y", "copy_last_code", "Copiar código", priority=True)`.
- `action_copy_last_code()`: varre `list(#chat.query(ChatMessage))` de trás p/ frente; na
  1ª assistant com ```` ``` ````, `_CODE_FENCE_RE.findall` pega todos os blocos, usa o
  ÚLTIMO (`blocks[-1].rstrip("\n")`), chama `self.copy_to_clipboard(code)` (OSC52) e `notify`.
  Sem bloco → `notify(..., severity="warning")`.

**Validação:**
- Pilot (copy_to_clipboard + notify monkeypatchados p/ capturar): com 2 blocos na mensagem,
  copiou o ÚLTIMO — `'def hello(nome):\n    return f"Ola, {nome}!"'` (pulou o `x = 1`); notify
  "Código copiado para a área de transferência." disparado.
- `py_compile` OK; `validar-acentuacao` rc 0; `ruff` "All checks passed!".
- `./run.sh --smoke` (invariantes #13): boot OK.
- `bash scripts/sprint_invariants.sh`: 14/14 (FAIL=0).
- `./run.sh --gauntlet --only rapido`: APROVADO.

**Fecha a ONDA-34:** com a 301, todos os itens da matriz de auditoria (283-301) estão
CONCLUIDOS ou resolvidos por decisão. Botão-mouse literal por bloco fica como melhoria
opcional futura (revisitável).
