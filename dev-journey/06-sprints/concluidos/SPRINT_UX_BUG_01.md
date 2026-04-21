## 0. SPEC

```yaml
sprint:
  id: UX-BUG-01
  title: "Autocomplete reativo: ghost text + pre-select + popup agrupado + /help fuzzy"
  onda: 22
  bloco: 5
  prioridade: ALTA
  tipo: Feature + Bugfix
  dependencias: [UX-LAYOUT-03]
  desbloqueia: [UX-BUG-02]

  touches:
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/cli.py
      reason: "PromptSession ganha auto_suggest + select_first; keybinding Tab aceita ghost text"
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/agent/completer.py
      reason: "NyxCompleter agrupa por categoria quando exibe; display_meta com alias"
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/agent/commands/core.py (ou onde estiver /help pós AUDIT-FIX-05)
      reason: "/help suporta busca fuzzy: /help git, /help mem, /help co*"

  absorve:
    - "O-02 (/help fuzzy)"
    - "O-05 (popup agrupa por categoria visualmente)"

  forbidden:
    - "Remover complete_while_typing=True"
    - "Deixar de respeitar ADR-004 (zero emoji em display_meta)"

  tests:
    - cmd: "python -c 'from nyx.agent.completer import NyxCompleter; c=NyxCompleter(\"/tmp\")'"
      deve_passar: true
    - cmd: "./run.sh --gauntlet --only tui"
      deve_passar: true

  acceptance_criteria:
    - "PromptSession tem auto_suggest=AutoSuggestFromHistory()"
    - "@kb.add('/') dispara start_completion(select_first=True)"
    - "Novo @kb.add('tab') aceita ghost text se houver sugestão inline"
    - "display_meta inclui alias entre parênteses quando existir (ex.: 'sai do REPL (q, exit)')"
    - "Comandos aparecem agrupados por categoria visualmente no popup (separadores ---- [git])"
    - "/help git lista apenas comandos de category='git'"
    - "/help co* faz match fuzzy por prefixo (commit, compact, copy, config, context)"
    - "Gauntlet tui passa"
    - "Teste manual: digitar /q + Enter submete /quit imediatamente (pre-select)"
```

---

# Sprint UX-BUG-01 — Autocomplete reativo

## Contexto

- Finding: autocomplete aparece mas não pré-seleciona; usuário precisa seta ↓ antes do Enter. E `/help` lista tudo sem agrupar.
- Oportunidades absorvidas:
  - O-02: `/help fuzzy` (buscar por categoria ou prefixo).
  - O-05: popup agrupa por categoria visualmente.

## Problema

1. Digitar `/q` não pré-seleciona `/quit`. Enter fecha o popup sem submeter.
2. Sem ghost text inline — Claude CLI tem, sentimos falta.
3. `/help` joga lista densa sem hierarquia.

## Solução

### `nyx/cli.py` — auto_suggest + select_first

```python
from prompt_toolkit.auto_suggest import AutoSuggestFromHistory
...
prompt_session = PromptSession(
    history=FileHistory(str(history_path)),
    completer=completer,
    multiline=True,
    key_bindings=kb,
    complete_while_typing=True,
    complete_style=_style,
    bottom_toolbar=_bottom_toolbar,
    auto_suggest=AutoSuggestFromHistory(),
)
```

Trocar o keybinding de `/`:
```python
@kb.add("/")
def _slash(event: object) -> None:
    buf = event.current_buffer
    buf.insert_text("/")
    if buf.document.text_before_cursor.lstrip() == "/":
        buf.start_completion(select_first=True)  # <-- True
```

Novo keybinding Tab:
```python
@kb.add("tab")
def _accept_suggestion(event: object) -> None:
    buf = event.current_buffer
    sug = buf.suggestion
    if sug and sug.text:
        buf.insert_text(sug.text)
    else:
        # fallback: próxima completion no popup, se aberto
        if buf.complete_state:
            buf.complete_next()
        else:
            buf.insert_text("    ")  # 4 espaços
```

### `nyx/agent/completer.py` — agrupamento + alias

```python
def _complete_commands(self, word: str) -> Any:
    prefix = word.lstrip("/").lower()
    # Organizar por categoria
    by_cat: dict[str, list[dict]] = {}
    for cmd in self._commands:
        name = cmd.get("name", "")
        if name.startswith(prefix):
            cat = cmd.get("category", "geral")
            by_cat.setdefault(cat, []).append(cmd)

    for cat in sorted(by_cat.keys()):
        # Inserir separador (display-only): Completion com display_meta=f"[{cat}]"
        # prompt_toolkit permite Completion "falsa" com start_position=0, display vazio
        # mas pode gerar ruído — alternativa: usar display prefix "[cat] /cmd"
        for cmd in sorted(by_cat[cat], key=lambda c: c["name"]):
            name = cmd["name"]
            desc = cmd.get("description", "")
            aliases = cmd.get("aliases", []) or []
            alias_str = f" ({', '.join('/' + a for a in aliases)})" if aliases else ""
            display_meta_text = f"[{cat}] {desc}{alias_str}"[:60]
            yield Completion(
                f"/{name}",
                start_position=-len(word),
                display_meta=display_meta_text,
            )
```

**Nota sobre agrupamento:** prompt_toolkit exibe completions em ordem — usar `display_meta` com prefixo `[categoria]` dá o efeito visual sem quebrar o modelo. A IA não deve tentar inserir "falsas completions" — pode quebrar submissão.

### `/help` fuzzy

Em `format_help(show_all=False, filter_query=None)`:

```python
def format_help(show_all: bool = False, filter_query: str | None = None) -> str:
    commands = list_commands()
    if not commands:
        return "Nenhum comando registrado."

    if filter_query:
        fq = filter_query.strip().rstrip("*").lower()
        # Match: nome começa com fq OU categoria == fq
        matched = [c for c in commands if c.name.startswith(fq) or c.category.lower() == fq]
        if not matched:
            return f"Nenhum comando bate com '{filter_query}'."
        lines = ["", f"  Comandos para '{filter_query}':", ""]
        for cmd in matched:
            aliases = f" ({', '.join('/' + a for a in cmd.aliases)})" if cmd.aliases else ""
            lines.append(f"    /{cmd.name:<12s}{aliases:16s} -- {cmd.description}")
        lines.append("")
        return "\n".join(lines)

    # resto da lógica atual (show_all ou essentials)
    ...
```

E `cmd_help`:
```python
@nyx_command(name="help", description="Mostra ajuda (/help git, /help all)", aliases=["h"])
def cmd_help(args: str, _root: str) -> str:
    arg = args.strip().lower()
    if arg in ("all", "todos", "*"):
        return format_help(show_all=True)
    if arg:
        return format_help(show_all=False, filter_query=arg)
    return format_help(show_all=False)
```

## Comando de verificação

```bash
cd /home/andrefarias/Desenvolvimento/Nyx-Code

# 1. auto_suggest importado
grep -c "AutoSuggestFromHistory" nyx/cli.py

# 2. select_first=True
grep "select_first=True" nyx/cli.py

# 3. /help fuzzy
python -c "
from nyx.agent.commands import format_help
out = format_help(show_all=False, filter_query='git')
assert 'commit' in out.lower(), 'sem match git'
out2 = format_help(show_all=False, filter_query='co')
assert 'commit' in out2.lower()
print('fuzzy OK')
"

./run.sh --gauntlet --only tui
```

## Critério binário

- [ ] `AutoSuggestFromHistory` passado ao `PromptSession`
- [ ] `select_first=True` no keybinding `/`
- [ ] Keybinding Tab aceita ghost text
- [ ] `display_meta` dos completions começa com `[categoria]`
- [ ] `/help git` filtra; `/help co` filtra; `/help all` mantém
- [ ] Gauntlet tui passa
- [ ] Teste manual: `/q<Enter>` submete `/quit` na hora
- [ ] Teste manual: Tab aceita ghost text quando histórico casa
- [ ] Commit: `feat: autocomplete reativo (ghost+pre-select) + /help fuzzy + popup por categoria`

## Guardrails anti-engodo

**NÃO marque como concluída se:**
- IA adicionou auto_suggest mas esqueceu do keybinding Tab.
- `/help git` ainda lista todos os comandos.
- `display_meta` mudou mas não tem prefixo `[cat]`.

## Validação humana

```bash
./run.sh
# /  → popup aparece, primeiro item pré-selecionado (visualmente destacado)
# /q<Enter> → submete /quit (você sai do REPL)
# Reabrir: /help git → só lista comandos git
# /help co  → lista commit, compact, copy, config, context
```

---

*"Autocompletar é um diálogo onde a máquina termina a sua frase antes de você decidir." -- anônimo*
