# SPRINT TUI-REDESIGN-25-10 — Tool calls compactos com status colorido (1 linha)

## 0. SPEC

```yaml
sprint:
  id: TUI-REDESIGN-25-10
  title: "Tool call vira chip de 1 linha: ● read_file ~/.../path 12ms ok (substitui 2 caixas)"
  onda: 25
  bloco: 25.4 Chain-of-thought, ferramentas e estrutura
  prioridade: ALTA
  tipo: UX+Refactor
  dependencias: [TUI-REDESIGN-25-08]
  desbloqueia: [TUI-REDESIGN-25-11]
  origem: "Auditoria audit.jsx -- problema P08 (Tool calls poluídos e cortados)"

  touches:
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/agent/output.py
      reason: "render_tool_card_start/end (linhas 480-542) substituídos por render_tool_chip(name, args, status, duration_ms)"
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/agent/loop/_iteration.py
      reason: "Callback on_tool_result emite chip em vez de start+end"

  forbidden:
    - "Truncar path absoluto sem ellipsis (sempre mostrar ~/.../basename)"
    - "Esconder erro: erro mantém o output (preview do stderr)"

  tests:
    - cmd: "bash scripts/sprint_invariants.sh"
      timeout: 60
      deve_passar: "14/14"

  acceptance_criteria:
    - "Tool call sucesso: '● {name} {arg1} {Nms} ok' em verde"
    - "Tool call erro: '● {name} {arg1} {Nms} erro' em vermelho + 1 linha preview"
    - "Path abrevia com ~/.../basename se cabe; senão truncate com … no meio"
    - "Toda info em 1 linha (até 2 com erro)"
    - "Smoke ok + invariantes 14/14"
```

---

# Sprint TUI-REDESIGN-25-10

**Status:** PENDENTE
**Data criação:** 2026-05-18
**Modelo obrigatório:** claude-opus-4-7

## Contexto

P08: render atual usa 2 caixas grandes (start `╭─...─╮` + end `╰─...─╯`) que ocupam 4-6 linhas para informação que cabe em 1.

## Solução proposta

Novo helper:

```python
def render_tool_chip(name: str, args: dict, status: str, duration_ms: int, error: str | None = None):
    glyph_color = NYX_SUCCESS if status == "ok" else NYX_ERROR
    arg_preview = shorten_path(args.get("file_path") or args.get("path") or args.get("cmd") or "")
    line = f"  {glyph_color}●{ANSI_RESET} {name} {arg_preview}  {duration_ms}ms  {status}"
    print(line)
    if error:
        print(f"      {DIM}{error[:120]}{RESET}")
```

## Critério binário

- [ ] render_tool_chip presente
- [ ] tool_card_start/end deletados (ou mantidos como aliases deprecated)
- [ ] Path abreviado corretamente
- [ ] Erro mostra preview de 1 linha
- [ ] Smoke + invariantes 14/14
- [ ] Commit `feat(TUI-REDESIGN-25-10): tool calls compactos com status colorido`

## Invariantes

#6, #14.

## Anti-débito

- Animação de execução (spinner durante tool) já existe via `_make_progress_bar` para tools longas; pode ser preservada.
- Detalhamento do erro (ações) fica para 25-11.

## Verificação

```bash
./run.sh
# pedir Nyx ler arquivo dentro do project
# avaliar: chip em 1 linha
bash scripts/sprint_invariants.sh
```

## Rollback

`git reset --hard HEAD~1`

---

*"Densidade dignifica o olho; verbosidade canceira." -- TUI-REDESIGN-25-10*
