# SPRINT COMPLETER-SEPS-01 — Separadores visuais por categoria no popup de autocomplete

## 0. SPEC (machine-readable)

```yaml
sprint:
  id: COMPLETER-SEPS-01
  title: "Implementar separadores visuais '---- [categoria]' no popup de completer (critério faltante de UX-BUG-01)"
  onda: 22
  bloco: 5 Bugs
  prioridade: MÉDIA
  tipo: Feature
  dependencias: [UX-BUG-01]
  desbloqueia: []

  touches:
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/agent/completer.py
      reason: "NyxCompleter._complete_commands agrupa por categoria via sort mas não renderiza separador visual entre grupos. Critério de aceite 5 de UX-BUG-01 não foi cumprido."
  creates: []
  removes: []

  n_to_n_pairs:
    - descricao: "Categorias declaradas nos @nyx_command(category='X') batem com as renderizadas pelo completer"
      paths:
        - /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/agent/completer.py
        - /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/agent/commands/core.py
        - /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/agent/commands/session.py
        - /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/agent/commands/system.py
        - /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/agent/commands/git_cmds.py
        - /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/agent/commands/debug_cmds.py
        - /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/agent/commands/code.py

  forbidden:
    - "Remover ou quebrar complete_while_typing=True em cli.py"
    - "Remover o sort por categoria (precisa preservar agrupamento)"
    - "Usar emoji, menção a IA"
    - "Hex de cor hardcoded no completer — qualquer cor vem de design_tokens.py"
    - "Fazer o separador selecionável (digitar Enter no separador deve ser no-op ou saltar para próximo item real)"
    - "Quebrar display_meta com alias implementado na UX-BUG-01"

  tests:
    - cmd: "python -c 'from nyx.agent.completer import NyxCompleter; c=NyxCompleter(\"/tmp\"); list(c.get_completions(type(\"D\",(),{\"text_before_cursor\":\"/\",\"get_word_before_cursor\":lambda **k:\"\"})(),None))'"
      timeout: 10
      deve_passar: "retorna lista com Completion(s), nenhum erro"
    - cmd: "./run.sh --gauntlet --only tui"
      timeout: 300
      deve_passar: true
    - cmd: "./run.sh (manual: digitar '/', conferir popup com cabeçalhos '---- [git] ----' etc)"
      timeout: 60
      deve_passar: "screenshot aprovado"

  acceptance_criteria:
    - "Ao digitar '/' no REPL, popup exibe uma linha de cabeçalho por categoria, formato literal '---- [categoria] ----'"
    - "Cabeçalhos aparecem entre grupos e são visualmente distintos (dim + não selecionáveis)"
    - "Enter sobre um cabeçalho não submete nada; seta ↓ pula para próximo comando real"
    - "Ordem preservada: categorias em ordem alfabética, comandos em ordem alfabética dentro de cada categoria"
    - "display_meta dos comandos reais mantém aliases (ex: '[git] commit (c)' — regressão proibida)"
    - "Categorias vazias (0 matches) não geram cabeçalho"
    - "Filtro por prefixo continua funcionando: digitar '/com' mostra cabeçalho '[git]' + 'commit' + cabeçalho '[root]' + 'commit-push-pr', sem cabeçalhos de categorias sem match"
    - "Gauntlet --only tui passa"
    - "Validação visual aprovada (screenshot de /tmp/nyx_completer_seps_*.png via skill validacao-visual)"
```

---

**Status:** CONCLUIDA (header corrigido em MASTER-CLEANUP-02 2026-05-20; presença em concluidos/ implica CONCLUIDA conforme convenção do projeto)
**Data criação:** 2026-04-21
**Modelo obrigatório:** claude-opus-4-7 (sem subagentes)

---

## Contexto do projeto (snapshot — não referência)

> **ADRs relevantes:**
>
> - ADR-004 Zero Emojis: separador usa caracteres box/dash, nunca emoji.
> - ADR-006 PT-BR: rótulos em português (categorias já estão: "git", "sistema", "código", "sessão", "contexto", "memória", "execução", "debug", "projeto", "avançado", "root", "geral").
> - ADR-013 Integração Obrigatória: completer é o único ponto que consome metadata dos commands — não duplicar lista em outro lugar.
> - ADR-023 Design System (UX-DESIGN-01): se precisar cor, usa `ANSI_DIM` de `nyx/themes/design_tokens.py`.
> - Sprint UX-BUG-01 (commit 73c0e21) implementou `complete_while_typing` + `auto_suggest` + `display_meta` com aliases + `/help fuzzy`. Esta sprint fecha o 5º critério daquela spec.
>
> **Estado do sistema (auditado 2026-04-21):**
> - Python 3.10+, `qwen3:4b`, Ollama 11435, proxy 11436.
> - 28 tools, 47 commands únicos, 9 services (pós INVENTORY-SYNC-01).
> - `prompt_toolkit` >= 3 (`Completion` + `Document` disponíveis).
> - `NyxCompleter._complete_commands` em `nyx/agent/completer.py:52-74` já ordena por `(category, name)` mas yield apenas `Completion` puros sem cabeçalho.

---

## Problema

### Sintoma observável

Ao digitar `/` no REPL:

```
> /
  ──────────────────────────────────────────
  /add-dir   [projeto] Adiciona diretório
  /advisor   [root]    Conselheiro de código
  /agents    ?         Lista agents
  /branch    [git]     Operações de branch (b, br)
  /commit    [git]     Cria um commit (c)
  /config    [sistema] Mostra ou edita configuração
  ...
```

Comandos estão ordenados por `(categoria, nome)` — mas o usuário não enxerga a fronteira entre categorias. Precisa ler `[cat]` em cada linha. Perde hierarquia.

### Spec UX-BUG-01 (commit 73c0e21), critério 5 literal

> "Comandos aparecem agrupados por categoria visualmente no popup (separadores `---- [git]` ----)"

**Realidade**: `nyx/agent/completer.py:59-74` apenas ordena e yields `Completion` planos. Sem separador. Critério binário falhou sem ressalva declarada.

---

## Solução proposta

1. **Inserir Completion-cabeçalho** entre grupos de categoria diferente.
2. O cabeçalho é um `Completion` com:
   - `text=""` (não insere nada se aceito)
   - `display="---- [categoria] ----"` (formatado via `to_formatted_text` para aplicar `ANSI_DIM`)
   - `display_meta=""` (sem descrição)
   - `start_position=0` (não remove caracteres)
3. **Problema conhecido do prompt_toolkit**: `Completion` sempre é selecionável. Mitigação: no keybinding `enter` (cli.py:124) já há `buf.apply_completion(state.current_completion or state.completions[0])`. Precisa detectar se o `current_completion.text == ""` (é cabeçalho) e pular para o próximo; se for o último, retomar o primeiro real.
4. **Navegação com seta**: `complete_next()` / `complete_previous()` do prompt_toolkit já itera linearmente. Adicionar helper que pula cabeçalhos (itera até próximo `text != ""`).

---

## Arquivos alvo (paths absolutos)

### `/home/andrefarias/Desenvolvimento/Nyx-Code/nyx/agent/completer.py`

**Antes (linhas 52-74):**
```python
def _complete_commands(self, word: str) -> Any:
    prefix = word.lstrip("/").lower()
    matched: list[dict] = []
    for cmd in self._commands:
        name = cmd.get("name", "")
        if name.startswith(prefix):
            matched.append(cmd)
    # Ordena por (categoria, nome) para que o popup agrupe visualmente.
    matched.sort(key=lambda c: (c.get("category", "geral"), c.get("name", "")))
    for cmd in matched:
        name = cmd.get("name", "")
        desc = cmd.get("description", "")
        cat = cmd.get("category", "geral")
        aliases = cmd.get("aliases", []) or []
        alias_str = (
            f" ({', '.join('/' + a for a in aliases)})" if aliases else ""
        )
        display_meta_text = f"[{cat}] {desc}{alias_str}"[:60]
        yield Completion(
            f"/{name}",
            start_position=-len(word),
            display_meta=display_meta_text,
        )
```

**Depois:**
```python
def _complete_commands(self, word: str) -> Any:
    from prompt_toolkit.formatted_text import FormattedText

    from nyx.themes.design_tokens import ANSI_DIM, ANSI_RESET  # apenas para referência semântica

    prefix = word.lstrip("/").lower()
    matched: list[dict] = []
    for cmd in self._commands:
        name = cmd.get("name", "")
        if name.startswith(prefix):
            matched.append(cmd)
    matched.sort(key=lambda c: (c.get("category", "geral"), c.get("name", "")))

    last_cat: str | None = None
    for cmd in matched:
        name = cmd.get("name", "")
        desc = cmd.get("description", "")
        cat = cmd.get("category", "geral")
        aliases = cmd.get("aliases", []) or []

        # Separador de categoria — só quando cat muda.
        if cat != last_cat:
            header = FormattedText([("class:completion.header", f"---- [{cat}] ----")])
            yield Completion(
                text="",                     # aceitar não insere nada
                start_position=0,            # não substitui o buffer
                display=header,              # renderizado como linha dim
                display_meta="",
            )
            last_cat = cat

        alias_str = (
            f" ({', '.join('/' + a for a in aliases)})" if aliases else ""
        )
        display_meta_text = f"[{cat}] {desc}{alias_str}"[:60]
        yield Completion(
            f"/{name}",
            start_position=-len(word),
            display_meta=display_meta_text,
        )
```

**Mudanças:**
- Novo `last_cat` rastreia mudança de categoria.
- Emite `Completion` header com `text=""` + `display` formatado `FormattedText`.
- Classe CSS `completion.header` deixa o styling para o prompt_toolkit; usuário define em stylesheet ou herda default dim (aceitável).

### `/home/andrefarias/Desenvolvimento/Nyx-Code/nyx/cli.py`

**Antes (keybinding Enter em cli.py:124-134):**
```python
@kb.add("enter")
def _submit(event: object) -> None:
    buf = event.current_buffer  # type: ignore[attr-defined]
    state = buf.complete_state
    if (
        state
        and state.completions
        and buf.document.text_before_cursor.lstrip().startswith("/")
    ):
        buf.apply_completion(state.current_completion or state.completions[0])
    buf.validate_and_handle()
```

**Depois:**
```python
@kb.add("enter")
def _submit(event: object) -> None:
    buf = event.current_buffer  # type: ignore[attr-defined]
    state = buf.complete_state
    if (
        state
        and state.completions
        and buf.document.text_before_cursor.lstrip().startswith("/")
    ):
        current = state.current_completion or state.completions[0]
        # Pula cabeçalhos (text=""): busca próximo real; se não houver, usa o primeiro real.
        if not current.text:
            current = next(
                (c for c in state.completions if c.text), state.completions[0]
            )
        buf.apply_completion(current)
    buf.validate_and_handle()
```

**Mudanças:** quando a "completion atual" é um cabeçalho (`text=""`), o Enter busca o próximo `Completion` real e aplica esse.

---

## Diff esperado (resumo)

```
+ 0 arquivos criados
~ 2 arquivos modificados (completer.py, cli.py)
- 0 arquivos removidos
+ ~20 linhas líquidas
```

---

## Comandos de verificação (literais, copy-paste)

```bash
cd /home/andrefarias/Desenvolvimento/Nyx-Code

# 1. Sintaxe OK
python -c "from nyx.agent.completer import NyxCompleter, create_completer; print('ok')"

# 2. Unit visual via smoke
./run.sh --smoke

# 3. Testes TUI do Gauntlet
./run.sh --gauntlet --only tui

# 4. Manual — abrir REPL e testar
./run.sh
# no REPL:
#   digitar '/'  -> popup com "---- [código] ----" acima de /explain etc
#   digitar '/g' -> popup com "---- [git] ----" acima dos commits
#   digitar '/help' + Enter -> executa /help (cabeçalho de categoria é pulado corretamente)

# 5. Validação visual (skill valicao-visual auto-invocada)
#   PNG em /tmp/nyx_completer_seps_<ts>.png  +  sha256sum  +  descrição

# 6. Regressão
bash scripts/sprint_invariants.sh | tail -5
```

---

## Critério binário de aceite (IA executora)

- [ ] Cabeçalho aparece entre grupos quando categoria muda
- [ ] Formato literal do cabeçalho: `---- [categoria] ----` com `FormattedText`
- [ ] Enter sobre cabeçalho não faz `/` vazio nem quebra o REPL
- [ ] Filtro por prefixo (`/com`) mostra apenas cabeçalhos de categorias com match
- [ ] Aliases no `display_meta` preservados (ex: `[git] Cria commit (/c)`)
- [ ] Categorias renderizadas em ordem alfabética (como o sort atual)
- [ ] Nenhum hex hardcoded no completer — só referência a design_tokens se for colorir
- [ ] Gauntlet `--only tui` passa 100%
- [ ] Screenshot aprovado em `/tmp/nyx_completer_seps_<ts>.png` + sha256 + descrição de 3-5 linhas
- [ ] `sprint_invariants.sh` 13/13 PASS
- [ ] Commit `feat(COMPLETER-SEPS-01): separadores de categoria no popup de completer`

---

## Guardrails anti-engodo (obrigatórios)

- Não testar só via `python -c` — é necessário TUI real (`./run.sh` + screenshot).
- Não emitir separador quando só há comandos de uma categoria no match — é visualmente redundante.
- Não aceitar o cabeçalho como completion válida "para passar o teste" — comportamento de Enter deve pular.
- `display` deve ser `FormattedText` (suporte a classes CSS); não usar string com ANSI escapes direto, que prompt_toolkit não renderiza corretamente em popup.
- Se a versão do prompt_toolkit disponível não suportar Completion com `display=FormattedText`, reportar BLOQUEADA e abrir sprint de upgrade, **não** cair em hack.

---

## Catálogo de gambiarras proibidas

Ver `dev-journey/08-templates/GAMBIARRAS_POR_SPRINT.md` §"Catálogo Universal".

### Gambiarras específicas

1. **Cabeçalho selecionável com `text="/"` ou `text=f"[{cat}]"`.** Insere lixo no buffer quando Enter. Proibido.
2. **ANSI escapes hardcoded no `display`** (`\033[2m`). Desvia do design system (invariante #6). Usar classe CSS ou constante de `design_tokens.py`.
3. **Duplicar lista de categorias no completer.** Categoria é atributo do `@nyx_command`; completer lê via `list_commands()` (UX-BUG-01). Não criar fonte paralela.
4. **"Correção" do Enter editando `_dispatcher.py`.** O dispatcher não vê `Completion` — só vê texto. Se ignorado o skip de cabeçalho em `cli.py:124`, o REPL recebe string vazia. Proteger no keybinding, não no dispatcher.
5. **Não incluir validação visual.** Diff toca TUI — skill `validacao-visual` é obrigatória (BRIEF §13).

---

## Proof-of-work obrigatório (4 passos)

```bash
bash scripts/sprint_invariants.sh > /tmp/inv_before.txt 2>&1
FAIL_BEFORE=$(grep -c '^\[FAIL\]' /tmp/inv_before.txt)

# --- implementação + screenshot TUI ---

bash scripts/sprint_invariants.sh > /tmp/inv_after.txt 2>&1
FAIL_AFTER=$(grep -c '^\[FAIL\]' /tmp/inv_after.txt)
diff /tmp/inv_before.txt /tmp/inv_after.txt
[ "$FAIL_AFTER" -le "$FAIL_BEFORE" ] || { echo REGRESSÃO; exit 1; }
```

Colar output bruto + caminho absoluto do PNG + sha256 + descrição multimodal.

---

## Validação humana (checklist do usuário)

```bash
cd /home/andrefarias/Desenvolvimento/Nyx-Code

git log --oneline -1
git show --stat HEAD

./run.sh
# digitar '/' — conferir visual:
#   ---- [código] ----
#     /explain ...
#     /plan ...
#   ---- [git] ----
#     /branch ...
#     /commit ...
#   ...

# Teste de Enter no cabeçalho:
#   digitar '/', seta ↑ para o cabeçalho, Enter — REPL deve tratar como "cabeçalho pulado" e executar primeiro comando real

ls /tmp/nyx_completer_seps_*.png    # screenshot existe
```

---

## Riscos

| Risco | Mitigação |
|-------|-----------|
| prompt_toolkit não suporta `Completion(display=FormattedText)` na versão instalada | Verificar `pip show prompt_toolkit`; precisa >= 3.0.0. Se não suportar, abrir sprint de upgrade como achado colateral (zero follow-up) |
| Cabeçalho dim demais e invisível em tema claro | Usar `ANSI_DIM` neutro + negrito — ou classe CSS `completion.header` que respeita tema |
| Navegação ↑/↓ trava no cabeçalho | prompt_toolkit itera todos Completions — usuário usa ↑/↓ normalmente. Guardrail do Enter evita problema semântico |
| Filtro com prefix que casa categoria mas não comando (`/cont`) gera cabeçalho órfão | Loop só emite cabeçalho quando há pelo menos um comando real subsequente no mesmo grupo — adicionar `if matched_by_cat: yield header` |

---

*"Agrupar é ensinar olhar." -- Rudolf Arnheim (adaptado)*
