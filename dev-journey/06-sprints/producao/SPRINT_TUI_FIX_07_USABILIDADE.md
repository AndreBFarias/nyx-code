## 0. SPEC (machine-readable)

```yaml
sprint:
  id: TUI-FIX-07
  title: "Consertos gerais de usabilidade (footer, paste longo, help, indicadores)"
  touches:
    - path: nyx/cli.py
      reason: "Deixar de re-printar footer a cada turno (só no boot + quando muda)"
    - path: nyx/agent/output.py
      reason: "render_user_input colapsa pastes grandes (>8 linhas) com toggle"
    - path: nyx/agent/commands.py
      reason: "/help paginado/categorizado; adicionar /memory pra listar memórias"
    - path: nyx/cli.py
      reason: "Mostrar indicador de memória carregada no boot (se ~/.nyx/memory/ tem arquivos)"
  n_to_n_pairs:
    - "Se render_user_input colapsa, o histórico salvo deve preservar o conteúdo completo"
    - "Se boot mostra '[memória: N entradas]', clicar /memory deve listá-las"
  forbidden:
    - "Sair silenciando spinner sem garantia de que um token veio"
    - "Colapsar paste por padrão (ruim pra casos curtos)"
    - "Mexer em /help de forma que quebre completer"
  tests:
    - cmd: "./run.sh --gauntlet --only interface"
      timeout: 60
    - cmd: "manual: 3 turnos, ver se footer não poluiu scroll"
      timeout: 60
  acceptance_criteria:
    - "Footer aparece 1x no boot e é atualizado no mesmo lugar (ou aparece só antes do próximo prompt, sem duplicar no scroll)"
    - "Paste >8 linhas: eco colapsa para 'você: [N linhas coladas -- Ctrl+O pra expandir]'"
    - "Tool result de erro em cor diferente de sucesso (vindo de TUI-FIX-06)"
    - "/help mostra 10 comandos mais usados + 'Digite /help all pra ver tudo'"
    - "Boot mostra '[memória: 3 entradas de pyenv.md, convencoes.md, setup.md]' se houver"
    - "/memory lista memórias e permite /memory show <arquivo>"
    - "Novo command /paste lista [Image #N] e paths quando houver imagens"
    - "Spinner stoppado antes do primeiro token garantido (sem overlap visual)"
```

---

# Sprint TUI-FIX-07 -- Usabilidade geral

**Status:** PENDENTE
**Data:** 2026-04-17
**Prioridade:** MÉDIA
**Tipo:** UX + Refinamento
**Dependências:** TUI-FIX-02 (streaming), TUI-FIX-06 (erro colorido)
**Desbloqueia:** --

---

## Problema / Contexto

Além dos 6 bugs específicos, as screenshots do usuário revelam pontos de usabilidade que se acumulam:

1. **Footer polui scroll**: aparece antes de CADA prompt, então depois de 10 turnos você tem 10 footers no histórico. Claude Code tem 1 footer que atualiza no lugar.

2. **Paste longo estufa o eco**: usuário colou saída de `ls` com 10+ linhas. O eco `╭─ você ─╮` renderizou tudo, comendo metade da tela.

3. **47 commands no /help**: o completer já lida, mas `/help` deve listar os úteis primeiro (`/help`, `/status`, `/tools`, `/plan`, `/commit`, ...) e esconder os raros atrás de `/help all`.

4. **Memória é invisível**: o usuário não sabe que tem memória carregada. No boot, seria útil indicar "[memória: 3 entradas]" se houver, com `/memory` pra listar.

5. **Spinner com texto estranho**: screenshot 9 mostra `:. pensando...` com o char Unicode do spinner rendering ruim. Precisa verificar se o spinner frame set funciona no terminal do usuário.

6. **Sem `/paste`**: depois de TUI-FIX-05 (colar imagem), vai ter que ter um jeito de listar as imagens coladas na sessão atual.

## Implementação

### Fase 1 -- Footer em lugar fixo (não no scroll)

Opção A (mais simples): só renderizar footer no BOOT, nunca mais. Usuário vê uma vez; as info (ctx%, iter) são acessíveis via `/status`.

Opção B (mais elegante): usar `bottom_toolbar` do PromptSession pra render dinâmico abaixo do prompt (convive com bypass toolbar da TUI-FIX-04). Trocar `render_footer(...) + prompt` por `prompt(..., bottom_toolbar=footer_fn)`.

Decisão: **Opção B**. Footer é útil como feedback constante.

### Fase 2 -- Paste longo colapsado

Em `output.py::render_user_input`:

```python
def render_user_input(text: str, console_width: int = 80) -> None:
    lines = text.split("\n")
    if len(lines) > 8:
        preview = "\n".join(lines[:3])
        collapsed = f"{preview}\n... [{len(lines)-3} linhas ocultas -- Ctrl+O pra expandir]"
        text_to_render = collapsed
    else:
        text_to_render = text
    # ... render ╭─ você ─╮ com text_to_render
```

Ctrl+O (já bindado pra tool expand?) ou novo bindings pra expand do último input.

### Fase 3 -- /help categorizado

Em `commands.py::cmd_help`:

```python
def cmd_help(args, root):
    if args.strip() == "all":
        return "\n".join(full_list)
    return """Comandos principais:
  /help, /help all    Ajuda
  /status             Estado da sessão
  /tools              Tools disponíveis
  /plan <objetivo>    Iniciar plano
  /commit             Commit no git
  /memory             Listar memórias
  /clear              Limpar sessão
  /quit (Ctrl+D)      Sair
Para ver todos (47), digite /help all.
"""
```

### Fase 4 -- Indicador de memória no boot

Em `cli.py`, logo após criar AgentLoop:

```python
mem = agent._memory
entries = mem.index()
if entries:
    names = [e["file"] for e in entries[:3]]
    suffix = f" (+{len(entries)-3})" if len(entries) > 3 else ""
    print(f"  {DIM}[memória: {len(entries)} entradas] {', '.join(names)}{suffix}{NC}")
```

### Fase 5 -- Comando /memory

```python
@nyx_command(name="memory", description="Lista memórias persistentes do projeto")
def cmd_memory(args, root):
    from nyx.agent.memory import NyxMemory
    m = NyxMemory(root)
    entries = m.index()
    if not entries:
        return "Sem memórias gravadas. Use write_memory pra criar."
    lines = [f"- {e['file']}: {e['reason']}" for e in entries]
    return "\n".join(lines)
```

### Fase 6 -- Comando /paste

```python
@nyx_command(name="paste", description="Lista imagens coladas nesta sessão")
def cmd_paste(args, root):
    # Reaproveita session.image_map se existir
    ...
```

### Fase 7 -- Spinner mais compatível

Em `output.py::nyx_spinner`, garantir que o spinner usa frames ASCII simples (`|/-\`) em vez de Unicode esotérico, quando detectar `LANG` sem UTF-8.

## Verificação

```bash
./run.sh
# No boot: ver "[memória: 3 entradas] ..." se houver memória
# No prompt: bottom_toolbar mostra footer (não spams no scroll)
# digitar /help -- ver lista curta
# digitar /help all -- ver lista longa
# digitar /memory -- ver lista
# colar 20 linhas de texto -- eco colapsa
# Ctrl+O -- expande

./run.sh --gauntlet --only interface
```

- [ ] Footer em bottom_toolbar
- [ ] Paste longo colapsa
- [ ] /help curto por padrão
- [ ] /memory lista
- [ ] /paste lista (pós TUI-FIX-05)
- [ ] Indicador de memória no boot
- [ ] Spinner sem chars quebrados
- [ ] Gauntlet interface passa

---

*"Simplicidade é a sofisticação suprema." -- Leonardo da Vinci*
