# ADR-013: Integração obrigatória

**Data:** 2026-04-05
**Status:** Aceita
**Contexto:** Organização do código Nyx

---

## Decisão

Nenhum script, módulo ou arquivo de código deve existir "solto" no projeto. Todo código funcional deve estar integrado em um dos sistemas do Nyx.

## Regras

1. **Tools** -- registradas no `ToolRegistry` (`nyx/agent/tools/registry.py`)
2. **Commands** -- registrados com `@nyx_command` em `nyx/agent/commands.py`
3. **Services** -- importáveis de `nyx/agent/services/`
4. **Testes** -- exclusivamente dentro do Gauntlet (`scripts/gauntlet/nyx_gauntlet.py`)
5. **Scripts** -- apenas em `scripts/` e referenciados por `run.sh` ou `Makefile`

## Proibições

- Nenhum `test_*.py` ou `*_test.py` fora do Gauntlet
- Nenhum script Python solto na raiz
- Nenhum módulo que não é importado por ninguém
- Nenhum arquivo `.py` em `/tmp` como parte do projeto

## Verificação

- `find . -name "test_*.py" -not -path "*/venv/*"` deve retornar vazio
- Todo arquivo em `nyx/agent/tools/` deve estar importado em `registry.py`
- Todo `@nyx_command` deve aparecer no output de `/help`
- `python scripts/sync.py` valida consistência

---

*"Um lugar para cada coisa, e cada coisa em seu lugar." -- Benjamin Franklin*
