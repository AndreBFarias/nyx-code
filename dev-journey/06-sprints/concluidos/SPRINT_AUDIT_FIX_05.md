## 0. SPEC

```yaml
sprint:
  id: AUDIT-FIX-05
  title: "Split nyx/agent/commands.py (919 linhas) em pacote por categoria"
  onda: 22
  bloco: 2
  prioridade: ALTA
  tipo: Refactor
  dependencias: []
  desbloqueia: []

  touches:
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/agent/commands.py
      reason: "Transforma em pacote commands/ (pasta com __init__.py) mantendo API pública"

  creates:
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/agent/commands/__init__.py
      reason: "Re-exporta list_commands, handle_command, nyx_command, format_help, get_command"
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/agent/commands/_registry.py
      reason: "Decorador nyx_command, _COMMANDS dict, list_commands, get_command, format_help"
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/agent/commands/_dispatcher.py
      reason: "handle_command(line, project_root) -- parsing e roteamento"
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/agent/commands/core.py
      reason: "help, quit, clear, status, memory, recall, tools, paste"
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/agent/commands/code.py
      reason: "explain, plan, test, compact, brief, explain-tool"
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/agent/commands/git_cmds.py
      reason: "commit, branch, diff, pr, pr-comments, commit-push-pr"
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/agent/commands/session.py
      reason: "session, resume, rewind, export, copy, stats, usage, files, trace, btw"
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/agent/commands/system.py
      reason: "config, env, doctor, version, model, theme, fast, effort, break-cache"
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/agent/commands/debug_cmds.py
      reason: "insights, advisor, security-review, review, test, issue, hooks, ctx-viz"

  forbidden:
    - "Mudar a API pública (list_commands, handle_command, nyx_command, CommandDef)"
    - "Remover qualquer comando existente (47+ atualmente)"
    - "Criar arquivo com mais de 300 linhas (objetivo é fragmentação)"
    - "Quebrar o autocomplete (completer.py importa list_commands)"

  tests:
    - cmd: "python -c 'from nyx.agent.commands import list_commands, handle_command, nyx_command; print(len(list_commands()))'"
      deve_passar: true
      esperado: "Imprime número >= 47"
    - cmd: "find nyx/agent/commands -name '*.py' -exec wc -l {} + | sort -rn | head -1"
      esperado: "Nenhum arquivo > 300 linhas"
    - cmd: "./run.sh --gauntlet --only rapido"
      deve_passar: true

  acceptance_criteria:
    - "Arquivo nyx/agent/commands.py NÃO existe mais como arquivo único (vira pacote commands/)"
    - "Existe nyx/agent/commands/ com pelo menos 8 submódulos"
    - "Todo submódulo tem <= 300 linhas"
    - "API pública preservada: `from nyx.agent.commands import list_commands, handle_command, nyx_command, format_help, get_command, CommandDef`"
    - "Quantidade de comandos idêntica ou maior: antes >= depois"
    - "Gauntlet rapido passa 100%"
    - "Autocomplete continua funcionando (completer.py não precisa mudar)"
```

---

# Sprint AUDIT-FIX-05 — Split commands.py em pacote

**Status:** CONCLUIDA (header corrigido em MASTER-CLEANUP-02 2026-05-20; presença em concluidos/ implica CONCLUIDA conforme convenção do projeto)
**Data criação:** 2026-04-18

## Contexto

- ADR limite 800 linhas por arquivo (GUIDE.md). `commands.py` está com **919 linhas** (finding A-01).
- 47+ commands registrados via decorador `@nyx_command`.
- Consumidores: `nyx/cli.py` (chama `handle_command`), `nyx/agent/completer.py` (chama `list_commands`).

## Problema

Arquivo monolítico, difícil de revisar, cresce desordenadamente a cada sprint de commands.

## Solução

Transformar em **pacote** `nyx/agent/commands/` com módulos por domínio:

```
nyx/agent/commands/
├── __init__.py          # re-exports públicos + import side-effect dos submódulos (registra decoradores)
├── _registry.py         # infra: CommandDef, _COMMANDS, nyx_command, get_command, list_commands, format_help
├── _dispatcher.py       # handle_command(line, project_root) + parser
├── core.py              # help, quit, clear, status, tools, paste, memory, recall
├── code.py              # explain, plan, test, compact, brief
├── git_cmds.py          # commit, branch, diff, pr, pr-comments, commit-push-pr
├── session.py           # session, resume, rewind, export, copy, stats, usage, files, trace, btw
├── system.py            # config, env, doctor, version, model, theme, fast, effort
└── debug_cmds.py        # insights, advisor, security-review, review, issue, ctx-viz, hooks
```

### Regra de distribuição

Ler cada `@nyx_command(name="X", category="Y", ...)` em `commands.py` atual e alocar pelo **category** ou, na falta, por afinidade semântica:

- `category="git"` → `git_cmds.py`
- `category="sessão"` → `session.py`
- `category="código"` → `code.py`
- `category="sistema"` → `system.py`
- `category="debug"` / `category="análise"` → `debug_cmds.py`
- `category="geral"` ou ausente → `core.py` (se for frequente) ou `system.py`

### Import side-effect

O registro dos decoradores exige que cada módulo seja importado para popular `_COMMANDS`. `__init__.py` deve fazer:

```python
from nyx.agent.commands._registry import (
    CommandDef,
    nyx_command,
    get_command,
    list_commands,
    format_help,
)
from nyx.agent.commands._dispatcher import handle_command

# Side-effect: importa cada submódulo para que os @nyx_command rodem
from nyx.agent.commands import core, code, git_cmds, session, system, debug_cmds  # noqa: F401

__all__ = [
    "CommandDef",
    "nyx_command",
    "get_command",
    "list_commands",
    "format_help",
    "handle_command",
]
```

## Procedimento (ordem recomendada)

1. Ler `nyx/agent/commands.py` atual inteiro. Catalogar cada `@nyx_command(name="X", category="Y")`.
2. Criar diretório `nyx/agent/commands/` e arquivos vazios.
3. Mover conteúdo:
   - Infra (imports, `CommandDef`, `_COMMANDS`, `nyx_command`, `get_command`, `list_commands`, `format_help`, `ESSENTIAL_COMMANDS`) → `_registry.py`.
   - Parser/dispatcher `handle_command` → `_dispatcher.py`.
   - Cada função `cmd_*` → submódulo correspondente pela categoria.
4. Cada submódulo importa o decorador: `from nyx.agent.commands._registry import nyx_command`.
5. Criar `__init__.py` com re-exports e side-effect imports.
6. Deletar `nyx/agent/commands.py` original.
7. Rodar `python -c "from nyx.agent.commands import list_commands; print(len(list_commands()))"` — número deve ser **igual ou maior** ao original.
8. Rodar `ruff check nyx/agent/commands/` — zero erros.
9. Rodar Gauntlet.

## Diff esperado

```
- 1 arquivo removido (commands.py 919 linhas)
+ 9 arquivos criados (commands/*)
~ 0 arquivos modificados (API pública preservada)
Δ linhas ~= 0 (puro rearranjo; eventualmente -50 se imports duplicados forem mergeados)
```

## Comando de verificação

```bash
cd /home/andrefarias/Desenvolvimento/Nyx-Code

# 1. Estrutura
test -f nyx/agent/commands/__init__.py && echo "pacote OK"
test ! -f nyx/agent/commands.py && echo "arquivo antigo removido OK"

# 2. API preservada
python -c "
from nyx.agent.commands import list_commands, handle_command, nyx_command, format_help, get_command, CommandDef
cmds = list_commands()
assert len(cmds) >= 47, f'perdeu comandos: {len(cmds)}'
print(f'{len(cmds)} comandos OK')
"

# 3. Nenhum arquivo > 300 linhas
find nyx/agent/commands -name '*.py' -exec wc -l {} + | awk '$1 > 300 { print; exit 1 }' && echo "tamanhos OK"

# 4. Gauntlet
./run.sh --gauntlet --only rapido
```

## Critério binário

- [ ] Pacote `nyx/agent/commands/` existe com `__init__.py`
- [ ] Arquivo `nyx/agent/commands.py` (sem barra) NÃO existe
- [ ] `list_commands()` retorna >= 47 comandos
- [ ] Todos arquivos do pacote <= 300 linhas
- [ ] Ruff limpo em `nyx/agent/commands/`
- [ ] Gauntlet rapido passa
- [ ] `./run.sh` abre e `/help` mostra os comandos
- [ ] Commit: `refactor: split commands.py 919 linhas em pacote por categoria`

## Guardrails anti-engodo

**NÃO marque como concluída se:**
- A IA renomeou `commands.py` para `commands_old.py` mantendo vivo.
- `list_commands()` retornar **menos** comandos que antes.
- Autocomplete parou de funcionar.
- Criou um único arquivo `commands/everything.py` com as 900 linhas (burla do objetivo).
- Algum submódulo tem > 300 linhas.

## Validação humana

```bash
cd /home/andrefarias/Desenvolvimento/Nyx-Code
git show --stat HEAD | head -20
# deve mostrar: 1 delete (commands.py), 9 creates (commands/*.py)

find nyx/agent/commands -name '*.py' | wc -l
# esperado: 9 arquivos

find nyx/agent/commands -name '*.py' -exec wc -l {} + | sort -rn | head -3
# nenhum > 300
```

## Riscos

| Risco | Mitigação |
|-------|-----------|
| Decorador não registrou por faltar import | `__init__.py` importa todos submódulos para side-effect |
| Caller externo (completer.py) quebra | API preservada: `from nyx.agent.commands import list_commands` continua válido |
| Comando perdido na migração | Verificação compara `len(list_commands())` antes e depois |

---

*"Dividir bem é a metade do governo." -- Aristóteles*
