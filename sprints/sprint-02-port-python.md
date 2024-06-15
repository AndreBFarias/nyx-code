# Sprint 2: Port para Python

**Objetivo:** Traduzir toda a logica para Python, usando o code_agent da Luna como base
real (28 modulos, 6500 LOC) e o openclaude como referencia de comportamento.

---

## Estrategia de port

O pacote npm contem apenas o bundle compilado (`dist/cli.mjs` - 19MB).
Fontes TypeScript originais nao estao incluidos.

**Base real:** code_agent da Luna (`src/skills/code_agent/`)
**Referencia:** openclaude README (arquitetura, 6 arquivos core, shim OpenAI)
**Abordagem:** Desacoplar modulos da Luna, limpar dependencias, renomear

---

## 2.1 Core do agente

| # | Origem Luna | Destino Nyx-Code | Acao |
|---|-------------|------------------|------|
| 1 | `loop.py` (34KB) + `loop_actions.py` (12.8KB) | `nyx/agent/loop.py` | Port + desacoplar TUI Luna |
| 2 | `parser.py` (20KB) | `nyx/agent/parser.py` | Port (4 niveis fallback) |
| 3 | `models.py` (3.7KB) | `nyx/agent/models.py` | Port direto |
| 4 | `session.py` (10.3KB) | `nyx/agent/session.py` | Port |
| 5 | `persistence.py` (12KB) | `nyx/agent/persistence.py` | Port |
| 6 | `prompt.py` (13.6KB) | `nyx/agent/prompt.py` | Port + customizar Nyx |
| 7 | `planner.py` (6.8KB) | `nyx/agent/planner.py` | Port |
| 8 | `repetition.py` (3.9KB) | `nyx/agent/repetition.py` | Port direto |

---

## 2.2 Sistema de tools

| # | Origem Luna | Destino Nyx-Code |
|---|-------------|------------------|
| 1 | `tools/base.py` | `nyx/tools/base.py` |
| 2 | `tools/registry.py` | `nyx/tools/registry.py` |
| 3 | `tools/read_file.py` | `nyx/tools/file_read.py` |
| 4 | `tools/edit_file.py` + `search_replace.py` | `nyx/tools/file_edit.py` |
| 5 | `tools/create_file.py` | `nyx/tools/file_create.py` |
| 6 | `tools/write_file.py` | `nyx/tools/file_write.py` |
| 7 | `tools/search.py` | `nyx/tools/search.py` |
| 8 | `tools/glob_tool.py` | `nyx/tools/glob.py` |
| 9 | `tools/list_files.py` | `nyx/tools/list_files.py` |
| 10 | `tools/run_command.py` | `nyx/tools/bash.py` |
| 11 | `tools/analyze.py` | `nyx/tools/analyze.py` |
| 12 | `tools/patch.py` | `nyx/tools/patch.py` |
| 13 | `multi_edit.py` | `nyx/tools/multi_edit.py` |
| 14 | `git_ops.py` | `nyx/tools/git.py` |

---

## 2.3 Providers e contexto

| # | Origem | Destino Nyx-Code |
|---|--------|------------------|
| 1 | Luna `core/ollama_client/` | `nyx/providers/ollama.py` |
| 2 | openclaude shim (conceito) | `nyx/providers/openai_compat.py` |
| 3 | `model_tier.py` | `nyx/providers/model_tier.py` |
| 4 | `context_manager.py` | `nyx/context/manager.py` |
| 5 | `path_resolver.py` | `nyx/context/path_resolver.py` |
| 6 | Novo | `nyx/context/project.py` |
| 7 | Luna `conversation_compactor.py` | `nyx/context/compactor.py` |

---

## 2.4 Infraestrutura

| # | Origem Luna | Destino Nyx-Code |
|---|-------------|------------------|
| 1 | `hooks.py` | `nyx/agent/hooks.py` |
| 2 | `permissions.py` | `nyx/agent/permissions.py` |
| 3 | `preflight.py` | `nyx/agent/preflight.py` |
| 4 | `post_validator.py` | `nyx/agent/validator.py` |
| 5 | `confirmation.py` | `nyx/interface/confirmation.py` |

---

## 2.5 Configuracao

| # | Descricao | Destino |
|---|-----------|---------|
| 1 | Settings centralizadas | `nyx/config/settings.py` |
| 2 | Defaults | `nyx/config/defaults.py` |

---

## 2.6 Nomenclatura Luna-compativel

- Nomes de modulos, classes e funcoes seguindo convencoes Luna
- Logging rotacionado (nunca print/console.log)
- Type hints em tudo
- Sem emojis, sem mencoes a IA
- Paths relativos via Path (nunca hardcoded)
- Error handling explicito (nunca silent failures)

---

## DROP (nao portar)

| Modulo Luna | Motivo |
|-------------|--------|
| `vram_switch.py` (5.8KB) | Luna gerencia VRAM centralmente |
| `vram_helper.py` (3.8KB) | Idem |
| `import_fixer.py` (6.3KB) | Especifico da Luna |
| `vision.py` (6.8KB) | Sprint futuro |
| `tools/legacy.py` (0.4KB) | Retrocompatibilidade |
| `tools_legacy.py` (28KB) | Monolito legado ja migrado |

---

## Verificacao

- [ ] Todos os modulos portados e funcionais
- [ ] `nyx/agent/loop.py` executa ciclo completo: prompt -> LLM -> parse -> tool -> repeat
- [ ] Parser funciona com 4 niveis de fallback (exact, relaxed, code_block, implicit_done)
- [ ] Deteccao de repeticao impede loops infinitos
- [ ] Tools funcionais: read, edit, create, write, search, glob, list, bash, analyze, git
- [ ] Sessoes persistidas e recuperaveis
- [ ] Testes basicos para cada modulo
- [ ] Zero dependencias residuais da Luna (imports limpos)
