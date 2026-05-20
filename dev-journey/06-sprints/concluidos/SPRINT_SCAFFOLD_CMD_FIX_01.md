# SPRINT SCAFFOLD-CMD-FIX-01 -- scaffold acompanha refactor commands/

**Status:** CONCLUIDA
**Data:** 2026-05-19 (terceira sessão, ~23h27)

## Contexto

Gauntlet SCF-02 FAIL "[Errno 2] No such file or directory: '/home/.../nyx/agent/commands.py'". O `scripts/scaffold.py` referenciava `nyx/agent/commands.py` (arquivo monolítico) mas a refatoração anterior (provavelmente Onda 24) transformou `commands/` em **pacote** com arquivo próprio por command (aesthetic.py, code.py, plan.py, etc.). O `__init__.py` importa os submódulos para que os decorators `@nyx_command` executem.

## Fix

### 1. `scripts/scaffold.py` -- paths e funções

- `COMMANDS_PATH = ... / "commands.py"` -> `COMMANDS_DIR = ... / "commands"` + `COMMANDS_INIT = COMMANDS_DIR / "__init__.py"`
- `_command_block()` -> `_command_module_template()` que gera **módulo completo** (docstring + import `nyx_command` + função `cmd_<name>` + quote)
- `_register_command_in_commands()` reescrita:
  - Cria `commands/<safe_name>.py`
  - Lê `__init__.py`, encontra bloco `from nyx.agent.commands import (...)`, insere `safe_name` ordenado alfabeticamente
  - Cleanup do arquivo se inserção do import falha
- `_unregister_command_from_commands()` reescrita:
  - Deleta `commands/<safe_name>.py`
  - Remove linha de import do `__init__.py` via regex multiline

### 2. `scripts/gauntlet/nyx_gauntlet.py` -- teste SCF-02

Lógica de verificação atualizada para refletir nova estrutura:
- Antes: lê `commands.py` e procura `cmd___gauntlet_test_cmd`
- Depois: verifica `commands/__gauntlet_test_cmd.py` existe E `__gauntlet_test_cmd` aparece em `__init__.py`
- Cleanup: arquivo deletado E import removido

## Proof-of-work

**Teste manual inline:**
- `scaffold_command(args)` -> arquivo criado + import em __init__.py + decorator registrou no `_COMMANDS` (validado via `get_command()`)
- `remove_command(name)` -> arquivo deletado + import removido

**Runtime gauntlet:**
- `./run.sh --gauntlet --only infra_scaffold` -> **3/3 (100%) APROVADO** (era 2/3)
- SCF-02 OK: `rc=0 cmd=True cleanup=True`

**Restante:**
- `./run.sh --smoke` -> `boot ok`
- `bash scripts/sprint_invariants.sh` -> 14/14 PASS
- `python3 -m ruff check nyx/` -> All checks passed!
- `python3 -m ruff check scripts/scaffold.py` -> All checks passed!
- Acentuação exit 0

## Filosofia (ADR-013 + ADR-017)

ADR-017 (Scaffold-first) declara que **nenhum componente novo é criado manualmente**. Quando a estrutura interna do projeto muda (commands.py -> commands/), o scaffold tem que acompanhar, senão a regra perde sentido. Esta sprint fecha o gap.

## Anti-débito catalogado

Nenhum.

## Referências

- ADR-013 (Integração obrigatória)
- ADR-017 (Scaffold-first)
- `scripts/scaffold.py` -- refatorado
- `scripts/gauntlet/nyx_gauntlet.py:3064-3091` -- SCF-02 atualizado
- `nyx/agent/commands/__init__.py` -- estrutura nova de imports

---

*"Quando a estrutura muda, scaffold acompanha — senão a regra é mentira." -- SCAFFOLD-CMD-FIX-01*
