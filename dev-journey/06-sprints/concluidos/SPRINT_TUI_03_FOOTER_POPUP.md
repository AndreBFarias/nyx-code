## 0. SPEC (machine-readable)

```yaml
sprint:
  id: TUI-03
  title: "Footer 1 linha + popup navegável de slash command"
  touches:
    - path: nyx/cli.py
      reason: "Renderizar footer antes do prompt; setar complete_style=MULTI_COLUMN"
    - path: nyx/agent/completer.py
      reason: "Incluir display_meta (descrição) em Completion; ordenar por relevância"
    - path: nyx/agent/output.py
      reason: "render_footer(ctx, model, iter, reads, mods) com degradação por largura"
    - path: nyx/agent/commands.py
      reason: "Expor dict {nome: descrição} pra o completer usar no boot"
  n_to_n_pairs: []
  forbidden:
    - "Footer que pisca a cada token (atualiza só no boundary de turn)"
    - "Popup bloqueando texto livre"
  tests:
    - cmd: "./run.sh --gauntlet --only rapido"
      timeout: 120
    - cmd: "manual: digitar '/' no prompt, verificar popup multi-coluna aparece"
      timeout: 60
    - cmd: "manual: resize -s 24 50, verificar footer degradado sem quebrar"
      timeout: 60
  acceptance_criteria:
    - "Footer '── ctx 12% ── qwen3:4b ── iter 4 ── lidos 3 ── modif 0 ──' aparece 1 linha antes do prompt"
    - "Cor accent, largura = terminal"
    - "Digitar '/' abre popup de commands com descrição visível"
    - "Popup navegável ↑↓, Enter insere, Esc cancela"
    - "Tab continua funcionando (fallback)"
    - "Terminal <60 cols: footer vira 'ctx 12% | qwen3:4b' truncado"
```

---

# Sprint TUI-03 -- Footer fixo + popup slash command

**Status:** CONCLUIDA (header corrigido em MASTER-CLEANUP-02 2026-05-20; presença em concluidos/ implica CONCLUIDA conforme convenção do projeto)
**Data:** 2026-04-17
**Prioridade:** MÉDIA
**Tipo:** Feature
**Dependências:** TUI-02
**Desbloqueia:** CTX-01 (após checkpoint visual)

---

## Problema / Contexto

TUI-02 resolve a formatação das mensagens, mas falta:
- Feedback constante do estado (ctx %, modelo, iter) sem poluir scroll
- Descoberta de commands via popup navegável (hoje só tab completion simples)

Referência visual: plano master, mock 3.

## Implementação

### Fase 1 -- Footer 1 linha

- `nyx/agent/output.py`: `render_footer(ctx: dict, model: str, iter_: int, reads: int, mods: int)`:
  - Monta string `── ctx {pct}% ── {model} ── iter {n} ── lidos {r} ── modif {m} ──`
  - Se `console.width < 60`: degradar pra `ctx {pct}% | {model}`
  - Se `console.width < 40`: só `ctx {pct}%`
  - Cor accent, linha cheia (usar `console.rule`)
- `nyx/cli.py`: chamar `output.render_footer(...)` logo antes de `prompt_async`. Substitui o `ctx_info + prompt_str` atual inline.

### Fase 2 -- Popup de slash commands

- `nyx/agent/commands.py`: expor `COMMAND_DESCRIPTIONS: dict[str, str]` (nome -> descrição curta, max 40 chars PT-BR).
- `nyx/agent/completer.py`: no `_complete_commands`, retornar `Completion(text, start_position, display_meta=descricao)`.
- `nyx/cli.py`: no `PromptSession(...)`, adicionar `complete_style=CompleteStyle.MULTI_COLUMN`, `complete_while_typing=True`. prompt_toolkit renderiza popup automaticamente.

### Fase 3 -- Descrições dos commands

- Para cada comando existente em `handle_command`, escrever 1 linha em PT-BR acentuado (ex: `/explain`: `Explica um arquivo ou trecho`).
- Integrar a lista no boot do completer em `cli.py`: `create_completer(project_root, commands=COMMAND_DESCRIPTIONS)`.

## Verificação

```bash
./run.sh
# Esperado:
#   ─── ctx 0% ──── qwen3:4b ──── iter 0 ──── lidos 0 ──── modif 0 ───
#   nyx> _
# Digitar "/ex":
#   Popup mostra:
#     /explain    Explica um arquivo ou trecho
#     /export     Exporta a sessão
#     /exit       Sai do REPL
# Navegar ↓ ↓, Enter seleciona
resize -s 24 50
./run.sh
# Footer degradado: "ctx 0% | qwen3:4b"
```

- [ ] Footer 1 linha, accent, correta
- [ ] Footer degrada bem em terminal estreito
- [ ] Popup multi-coluna com descrições
- [ ] Navegação ↑↓ / Enter / Esc funciona
- [ ] Tab continua como fallback
- [ ] Gauntlet rapido passa

---

*"Bom design é tão pouco design quanto possível." -- Dieter Rams*
