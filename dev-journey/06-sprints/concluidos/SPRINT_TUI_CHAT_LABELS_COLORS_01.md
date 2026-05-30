# SPRINT 297 — TUI-CHAT-LABELS-COLORS-01

## 0. SPEC

```yaml
sprint:
  id: TUI-CHAT-LABELS-COLORS-01
  title: "Dar label nominal ao usuário no chat (user_display_name via resolve_user_display_name, plumbado cli.py -> NyxTUI -> ChatMessage) e distinguir cor do NOME (destaque) vs CONTEÚDO ($foreground neutro) tanto no user quanto no NyxCode"
  onda: 34
  prioridade: MEDIA
  tipo: Feature
  dependencias: [TUI-NYXCODE-GHOST-LAZY-MOUNT-01]
  desbloqueia: []

  origem: "Matriz de auditoria ONDA-34 (plano redesign, linhas 38/39/54/82): nome do user AUSENTE no chat (só '> texto'); cor do nome IGUAL à do conteúdo (tudo na cor da role)."

  touches:
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/agent/tui/widgets/chat_message.py
      reason: "Novo param display_name; render() colore o NOME via span Rich (user=NYX_ACCENT, assistant=NYX_PURPLE, importados de design_tokens) e deixa o CONTEÚDO sem span (neutro); glifo _DIAMOND=chr(0x25C6) preservado."
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/agent/tui/styles/nyx.tcss
      reason: "ChatMessage.user e .assistant: color $accent/$primary -> $foreground (conteúdo neutro); border-left mantém a cor da role."
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/agent/tui/app.py
      reason: "NyxTUI.__init__ ganha kwarg user_display_name; armazenado e repassado aos 2 ChatMessage('user', text) call-sites."
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/cli.py
      reason: "Passa user_display_name=app_state.get('user_display_name','') ao instanciar NyxTUI."
  creates: []
  removes: []

  forbidden:
    - "Remover/corromper o glifo _DIAMOND=chr(0x25C6) do assistant (chat_message.py é sensível ao sanitizer, #14)"
    - "Hardcodar hex de cor em chat_message.py (invariante #6) — usar NYX_ACCENT/NYX_PURPLE de design_tokens"
    - "Regredir o lazy-mount (283): o ChatMessage('assistant') segue lazy-mountado no 1º token"
    - "Mudar a assinatura pública de NyxTUI de forma incompatível (só adiciona kwarg opcional)"

  tests:
    - cmd: "./run.sh --smoke"
      timeout: 15
      deve_passar: true
    - cmd: "bash scripts/sprint_invariants.sh"
      timeout: 60
      deve_passar: true

  acceptance_criteria:
    - "user mostra '> {display_name}' com o nome em turquesa (NYX_ACCENT) e conteúdo neutro"
    - "assistant mostra '◆ NyxCode' em roxo (NYX_PURPLE) e conteúdo neutro; glifo preservado"
    - "display_name plumbado de resolve_user_display_name (cli.py app_state) até o ChatMessage"
    - "fallback 'Você' quando display_name vazio"
    - "py_compile OK; invariantes 14/14; render Rich com spans corretos"
```

## 1. PROOF-OF-WORK (CONCLUIDA — 2026-05-30)

**Implementação (4 arquivos, +39/-9):**
- `chat_message.py`: import `NYX_ACCENT, NYX_PURPLE` de design_tokens; `__init__` ganha
  `*, display_name=""`; `render()` monta `Text()` vazio + `append(label, style=NYX_*)` (nome
  colorido) + `append(content)` sem style (neutro, herda $foreground do CSS). `_DIAMOND` intacto.
- `nyx.tcss`: `.user`/`.assistant` `color` → `$foreground`; `border-left` mantém `$accent`/`$primary`.
- `app.py`: `NyxTUI.__init__` ganha `user_display_name=""`; 2 call-sites de `ChatMessage("user", text)`
  passam `display_name=self._user_display_name`.
- `cli.py`: `NyxTUI(..., user_display_name=app_state.get("user_display_name", ""))`.

**Validação:**
- Render direto (venv): `user`→`'> [REDACTED]\nminha pergunta'` span(0,14,#00D4AA) só no nome;
  `assistant`→`'◆ NyxCode\nresposta'` span(0,9,#9D4EDD) só no label; fallback `'> Você'`.
- `py_compile` OK; `validar-acentuacao` rc 0; `app_state` confirmado dict em escopo (cli.py:154).
- `./run.sh --smoke` (via invariantes #13): boot OK com o CSS novo.
- `bash scripts/sprint_invariants.sh`: 14/14 (FAIL=0).
- **Visual (Textual Pilot headless, SVG→PNG `/tmp/labels_cores.png`):** confirma nome do user
  turquesa `#00d4aa`, `◆ NyxCode` roxo `#9d4edd`, conteúdo neutro, glifo `◆` presente, border-left
  por role. Sem OOM (sem Ollama).
- `./run.sh --gauntlet --only rapido`: APROVADO (cli.py instancia NyxTUI com o novo kwarg sem regressão).
