# SPRINT TUI-FIX-08 — Popup de slash commands sem filtro dinâmico por prefixo

## 0. SPEC (machine-readable)

```yaml
sprint:
  id: TUI-FIX-08
  title: "Popup de / deve filtrar por prefixo conforme o usuário digita (não só abrir com / isolado)"
  onda: 22
  bloco: 2.8
  prioridade: ALTA
  tipo: Bugfix
  dependencias: [BUG-PORT-PARSE-01]
  desbloqueia: [VALIDATE-ONDA-20]

  touches:
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/agent/completer.py
      reason: "_complete_commands precisa filtrar por prefixo digitado (text.startswith(typed)) e devolver Completions com start_position correto"
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/cli.py
      reason: "PromptSession precisa ter complete_while_typing=True e CompleteStyle.MULTI_COLUMN conforme especificação TUI-03"
      linhas_alvo: "local do PromptSession(...) na função run_repl"

  creates: []
  removes: []

  n_to_n_pairs: []

  forbidden:
    - "Substituir popup por `print()` manual — violação de ADR-024 (render layer)"
    - "Filtrar do lado do dispatcher em vez do completer — dispatcher só valida, completer descobre"
    - "Hard-code a lista de comandos no completer (deve vir de COMMAND_DESCRIPTIONS já exposto por commands)"
    - "Remover fallback de Tab — Tab continua como atalho oficial (TUI-03 acceptance criteria)"
    - "Mover código para fora de `nyx/agent/completer.py` criando arquivo novo — fix é in-place"
    - "Adicionar emoji, menção a IA, ou tocar em qualquer arquivo fora dos 2 touches"

  tests:
    - cmd: "./run.sh --gauntlet --only rapido"
      timeout: 120
      deve_passar: "sem regressão"
    - cmd: "manual: digitar `/t` no REPL e verificar popup com apenas comandos começando por `t` (ex.: /theme, /test, /tools)"
      timeout: 60
    - cmd: "manual: digitar `/them` e verificar que `/theme` é a única sugestão visível"
      timeout: 30
    - cmd: "manual: Enter seleciona; Esc fecha; ↑↓ navega; Tab completa; texto livre depois de espaço não dispara popup"
      timeout: 60

  acceptance_criteria:
    - "Digitar `/` abre popup com todos os comandos (comportamento atual — não regredir)"
    - "Digitar `/th` filtra popup para apenas comandos com prefixo `th`"
    - "Digitar `/them` mantém popup com `/theme` único"
    - "Enter em item do popup substitui o texto digitado pelo comando completo"
    - "Tab também completa como fallback"
    - "Texto sem `/` inicial não abre popup"
    - "Dispatcher continua retornando `Comando desconhecido: /X. Use /help.` quando usuário pressiona Enter direto sem usar popup (cenário fora de escopo, apenas confirmar não-regressão)"
    - "Gauntlet rapido 100%"
    - "Acentuação PT-BR correta"
```

---

**Status:** CONCLUIDA (2026-04-20) -- fix no handler Enter de `nyx/cli.py` aceita completion ativa de slash antes de submeter; validado visualmente pelo usuário.
**Data criação:** 2026-04-19
**Origem:** achado colateral durante **VALIDATE-ONDA-20** (Rodada 1). Usuário digitou `/them` (typo de `/theme`); esperava popup filtrado navegável, recebeu `Comando desconhecido: /them. Use /help.` do dispatcher (`nyx/agent/commands/_dispatcher.py:19`).
**Modelo obrigatório:** claude-opus-4-7 (sem subagentes)

---

## Contexto do projeto (snapshot)

> **Especificação original violada:** `SPRINT_TUI_03_FOOTER_POPUP.md` (ainda em `producao/`, EM VALIDAÇÃO).
>
> Critérios de aceite literais da TUI-03:
> - "Digitar '/' abre popup de commands com descrição visível"
> - "Popup navegável ↑↓, Enter insere, Esc cancela"
> - "Tab continua funcionando (fallback)"
>
> Gap descoberto: popup é decorativo (só abre com `/` isolado), não filtra dinamicamente. Especificação promete "navegável"; implementação entregou "estático".
>
> **Estado atual do codebase:**
> - `nyx/agent/completer.py` — módulo do completer (alvo principal do fix).
> - `nyx/agent/commands/__init__.py` exporta `COMMAND_DESCRIPTIONS: dict[str, str]` (contrato definido em TUI-03 Fase 3).
> - `nyx/cli.py` — inicialização do `PromptSession(...)`.
> - `nyx/agent/commands/_dispatcher.py:19` retorna literal `"  Comando desconhecido: /{name}. Use /help."` — intocado neste fix.
>
> **Bug dependente:** BUG-PORT-PARSE-01 precisa ser concluído primeiro — enquanto `Invalid port` polui o REPL, não dá pra testar popup com confiança.

---

## Problema

### Sintoma observável (screenshot do usuário, 2026-04-19)

```
nyx> /them
Nyx: Comando desconhecido: /them. Use /help.
```

Esperado (conforme TUI-03):

```
nyx> /them_
┌────────────────┐
│ /theme  Lista… │  ← highlight
└────────────────┘
```

### Causas prováveis

1. `PromptSession` em `nyx/cli.py` não tem `complete_while_typing=True` (TUI-03 Fase 2, linha 72 da spec). Sem isso, prompt_toolkit só mostra completions em Tab.
2. `_complete_commands` em `nyx/agent/completer.py` provavelmente retorna lista estática sem filtrar por `document.get_word_before_cursor()` ou pelo texto começado por `/`.
3. Possível ausência de `CompleteStyle.MULTI_COLUMN` no `PromptSession`.

---

## Solução proposta

Fase 1 — diagnóstico (obrigatório antes de editar):

```bash
grep -n "complete_while_typing\|CompleteStyle" nyx/cli.py
grep -n "def _complete_commands\|get_completions" nyx/agent/completer.py
```

Documentar resultado no snapshot do PR.

Fase 2 — aplicar mínimo necessário:

- `nyx/agent/completer.py`: em `get_completions`, checar se `document.text_before_cursor` começa com `/`; pegar o prefixo após `/`; iterar `COMMAND_DESCRIPTIONS.items()` filtrando por `name.startswith(prefix)`; yield `Completion(f"/{name}", start_position=-len(prefix)-1, display_meta=descricao)`.
- `nyx/cli.py`: garantir `complete_while_typing=True` e `complete_style=CompleteStyle.MULTI_COLUMN` no `PromptSession`.

Fase 3 — manter Tab como fallback:

Nada a adicionar — prompt_toolkit já trata Tab quando `complete_while_typing=True` coexiste.

---

## Arquivos alvo (paths absolutos)

### `/home/andrefarias/Desenvolvimento/Nyx-Code/nyx/agent/completer.py`

**Diagnóstico obrigatório antes de editar:** ler função atual de completions de commands e copiar o trecho no snapshot do commit.

**Mudanças mínimas:** filtrar por prefixo; preservar outros completers (paths, tools) intactos.

### `/home/andrefarias/Desenvolvimento/Nyx-Code/nyx/cli.py`

**Diagnóstico:** localizar instanciação do `PromptSession`.

**Mudança:** adicionar/garantir `complete_while_typing=True` e `complete_style=CompleteStyle.MULTI_COLUMN`.

---

## Diff esperado

```
~ 2 arquivos modificados
+ ~15 linhas líquidas
```

---

## Comandos de verificação

```bash
# 1. Invariantes baseline
bash scripts/sprint_invariants.sh > /tmp/inv_before.txt 2>&1

# 2. Diagnóstico pré-fix
grep -n "complete_while_typing\|CompleteStyle" nyx/cli.py
grep -n "get_completions" nyx/agent/completer.py

# 3. Aplicar fix

# 4. Boot smoke
./run.sh --smoke   # 'boot ok'

# 5. Manual (REPL)
./run.sh
# nyx> /            → popup com todos
# nyx> /th          → popup com começando em 'th'
# nyx> /them        → popup com '/theme' único
# Enter seleciona; ↑↓ navega; Esc fecha
# Ctrl+D sair

# 6. Gauntlet
./run.sh --gauntlet --only rapido

# 7. Invariantes depois
bash scripts/sprint_invariants.sh > /tmp/inv_after.txt 2>&1
diff /tmp/inv_before.txt /tmp/inv_after.txt
```

---

## Critério binário de aceite

- [ ] Diagnóstico pré-fix colado no relatório
- [ ] `/th` abre popup filtrado; `/them` mantém `/theme` como sugestão única
- [ ] Enter seleciona; Esc fecha; ↑↓ navega; Tab fallback
- [ ] Texto sem `/` não abre popup de commands
- [ ] Gauntlet rapido 100%
- [ ] FAIL invariantes não regride; check #13 continua PASS
- [ ] Sprint movida para `concluidos/` com commit `fix: popup de slash commands filtra por prefixo (TUI-FIX-08)`
- [ ] SPRINT_ORDER_MASTER atualizado

---

## Gambiarras específicas

1. **Filtrar do lado do dispatcher.** O dispatcher só valida e despacha; completer é responsável pelo filtro. Misturar reduz coesão.
2. **Listar todos sempre.** "popup mostra tudo, usuário filtra visualmente" — quebra UX em 50+ commands.
3. **Hard-coded de nomes.** Single source of truth é `COMMAND_DESCRIPTIONS` do registry.
4. **Capturar `/them` no dispatcher e sugerir `/theme`.** Fora de escopo — nice-to-have, mas não é este fix.

---

## Proof-of-work obrigatório

Formato padrão (SPRINT_TEMPLATE_V2.md). Incluir transcript do REPL com 3 prefixos (`/`, `/th`, `/them`) e prints do popup visível — se impossível (sem TTY no assistente), pedir screenshot ao usuário em checkpoint de validação.

---

## Validação humana (checklist do usuário)

```bash
./run.sh
# Digitar sequência: "/", esperar popup → funciona
# Apagar e digitar: "/t", popup reduzido → funciona
# Continuar: "/th", reduzido → funciona
# Continuar: "/them", apenas /theme → funciona
# Pressionar Enter → seleciona /theme, executa
# Ctrl+D sair
```

---

## Riscos

| Risco | Mitigação |
|-------|-----------|
| `complete_while_typing=True` atrasa latência do prompt | prompt_toolkit ≥3 processa completer em thread separada; validar com terminal real |
| Completer atual é compartilhado com outros contextos (paths, tools) | Ler `get_completions` inteira antes de editar; filtrar só quando `text_before_cursor.startswith("/")` |
| Popup conflita com footer de TUI-03 | Ambos são renderizados por prompt_toolkit; sem conflito esperado. Verificar com `resize -s 24 60` |

---

*"O que não é navegável não é interface." -- paráfrase de Jef Raskin*
