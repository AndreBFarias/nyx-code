# Relatório -- Bloco 2 da Onda 22 (parcial)

**Data:** 2026-04-18
**Escopo:** Execução em sequência das sprints AUDIT-FIX-05, AUDIT-FIX-06, AUDIT-FIX-07, DEBT-01, DEBT-03.
**Status final:** 5 sprints concluídas; 13 pendentes no Bloco 2.
**Próxima:** UX-DESIGN-01.

---

## 1. Sumário executivo

| Sprint | Tipo | Commit | Arquivos | FAIL ∆ | Invariante fechado |
|--------|------|--------|----------|--------|--------------------|
| AUDIT-FIX-05 | Refactor | `7ab9414` | 11 | 6 → 5 | #7 (arquivo > 800 linhas) |
| AUDIT-FIX-06 | Docs | `5528e63` | 3 | 5 → 5 | — (ADR docs) |
| AUDIT-FIX-07 | Bugfix | `614c28c` | 4 | 5 → 4 | #3 (print fora de cli/output) |
| DEBT-01 | Refactor | `43cf4d2` | 7 | 4 → 4 | — (loop.py já < 800) |
| DEBT-03 | Refactor | `0ac665e` | 62 | 4 → 4 | — (logging unificação) |

**FAIL invariantes remanescentes (4):**
- #1 emoji em .py (ADR-004)
- #2 menção a IA em .py (ADR-005)
- #4 except silencioso sem log
- #10 ruff reclama (3 erros pré-existentes em `web_search.py`, `todo_write.py`, `analyze_tool.py`)

Sprints pendentes que podem fechar esses: UX-DESIGN-01 fecha #1 e #2 (conforme matriz `GAMBIARRAS_POR_SPRINT.md`).

---

## 2. Detalhamento por sprint

### 2.1 AUDIT-FIX-05 -- Split `commands.py`

**Commit:** `7ab9414 refactor: split commands.py 919 linhas em pacote por categoria`

Transformou `nyx/agent/commands.py` (919 linhas, 43 comandos) em pacote `nyx/agent/commands/` com 9 arquivos por domínio:

| Arquivo | Linhas | Conteúdo |
|---------|--------|----------|
| `_registry.py` | 101 | `CommandDef`, `_COMMANDS`, `nyx_command`, `get_command`, `list_commands`, `format_help`, `ESSENTIAL_COMMANDS` |
| `_dispatcher.py` | 24 | `handle_command` (parser + roteamento) |
| `core.py` | 132 | help, quit, clear, status, tools, memory, recall, paste |
| `code.py` | 81 | explain, plan, test, compact, brief-cmd |
| `git_cmds.py` | 172 | commit, diff, review, branch, issue, pr, pr-comments, commit-push-pr |
| `session.py` | 111 | session, resume, rewind, export, copy, summary, stats, usage, context, btw, files, trace |
| `system.py` | 239 | config, env, doctor, version, model, theme, permissions, hooks, init, add-dir, break-cache |
| `debug_cmds.py` | 89 | insights, advisor, security-review, ctx-viz, tasks, skills |
| `__init__.py` | 41 | re-exports + side-effect imports |

**API pública preservada:**
```python
from nyx.agent.commands import (
    CommandDef, nyx_command, get_command, list_commands,
    format_help, handle_command,
)
```

50 comandos registrados (≥ 47 exigidos). Todos submódulos ≤ 300 linhas. Ruff limpo.

**Decisão não-trivial:** quando o `category=` do decorador conflitava com a listagem textual do `creates:` da spec (ex.: `compact` tem `category="sessão"` mas spec mandava em `code.py`), priorizei o spec. Confirmado com o usuário.

### 2.2 AUDIT-FIX-06 -- ADR-024 render layer

**Commit:** `5528e63 docs: ADR-024 normaliza output.py como render layer`

- Criado `dev-journey/03-decisions/ADR_024_RENDER_LAYER.md` (Status: ACEITO, 2026-04-18).
- `GUIDE.md`: regra do `print()` expandida para permitir em `nyx/cli.py` **e** `nyx/agent/output.py` (ADR-024). Tabela de ADRs passou de (20) para (24), adicionada linha `| 024 | Render Layer (print em output.py) |`.
- Zero código Python tocado.

**Observação:** a tabela ADRs vigentes agora pula de 020 para 024. A inconsistência é pre-existente (linha de header da GUIDE.md já mencionava ADR-022/023 sem corpo criado). Mantido literalmente conforme spec -- não é escopo desta sprint criar 021/022/023.

### 2.3 AUDIT-FIX-07 -- ask_user retorna payload

**Commit:** `614c28c refactor: ask_user retorna payload, UI renderizada por output.py (ADR-013)`

Três arquivos:

1. **`nyx/agent/tools/ask_user.py`**: `print()` e `input()` removidos. Tool vira pura -- retorna `ActionResult(success=True, output=json.dumps({"kind":"question","question":...,"options":[...]}, ensure_ascii=False))`.
2. **`nyx/agent/output.py`**: nova função `render_ask_user(question, options)` usando a render layer oficial da ADR-024.
3. **`nyx/cli.py`**: callback `on_tool_result` (linha 271) intercepta `name == "ask_user"`, parseia JSON, chama `render_ask_user`, coleta `input("  Resposta: ")`, injeta `f"[resposta] {answer}"` via `agent.session.add_user(...)` para próxima iteração.

**Detalhe técnico que vale registrar:** `session.add_tool_call` faz `result[:TOOL_RESULT_LIMIT]` (slice de string). Se a tool retornasse `output=dict`, quebrava. Por isso a tool serializa para JSON string na borda (`json.dumps(..., ensure_ascii=False)` preserva PT-BR).

### 2.4 DEBT-01 -- Split `loop.py`

**Commit:** `43cf4d2 refactor: split loop.py 753 linhas em pacote por responsabilidade`

Transformou `nyx/agent/loop.py` (753 linhas) em pacote `nyx/agent/loop/`:

| Arquivo | Linhas | Conteúdo |
|---------|--------|----------|
| `_types.py` | 14 | `PermissionCallback` + re-export `SessionState/SessionStatus` |
| `_constants.py` | 88 | `LLM_TIMEOUT`, `ACTION_TO_TOOL`, `PARAM_REMAP`, `_remap_params`, `CORE_TOOLS`, `TOOL_KEYWORDS` |
| `_iteration.py` | 359 | Mixin `_IterationMixin` com `_execute_tool_calls`, `_execute_parsed_action`, `_check_repetition`, `_call_llm`, `_try_recovery`, `_select_tools_for_context` |
| `_core.py` | 328 | Classe `AgentLoop(_IterationMixin)` com `__init__`, `run`, reset/close/properties, `_rebuild_system_prompt`, `_build_force_done_summary`, `get_context_info`, `maybe_summarize` |
| `__init__.py` | 20 | Re-exports |

Todos ≤ 400 linhas. API preservada. `AgentLoop` instanciável, `tools_count=35`.

**Decisão não-trivial:** os métodos de iteração acessam muito estado do `self` (`_session`, `_permissions`, `_tools`, etc.). Em vez de transformar em funções livres (que exigiriam passar `agent` como primeiro arg e reescrever ~20 chamadas), usei **Mixin**. `AgentLoop(_IterationMixin)` -- a classe continua una; o split é só organizacional.

**Bug descoberto ao validar:** `scripts/gauntlet/nyx_gauntlet.py:1198` importa `from nyx.agent.loop import ACTION_TO_TOOL`. Após a migração, `ACTION_TO_TOOL` estava só em `_constants.py`. Corrigido no `__init__.py` re-exportando `ACTION_TO_TOOL`, `PARAM_REMAP`, `LLM_TIMEOUT` para preservar o caller.

### 2.5 DEBT-03 -- Logging unificado

**Commit:** `0ac665e refactor: logging unificado via logging_service.get_logger (ADR-015)`

62 arquivos alterados. Mudança em dois vetores:

1. **`nyx/agent/services/logging_service.py`**: adicionado `get_logger(name)` com guard `_INITIALIZED` que chama `InternalLogging()` idempotentemente na primeira invocação.
2. **60 módulos** (via script Python automatizado): `logger = logging.getLogger("nyx.xxx")` → `logger = get_logger("nyx.xxx")`, com `from nyx.agent.services.logging_service import get_logger` adicionado logo após `import logging`.

**Exceções mantidas:**
- `nyx/agent/services/logging_service.py` (infra, self-reference).
- `nyx/proxy.py` (roda standalone via `python nyx/proxy.py`, `basicConfig` próprio -- spec autoriza manter).

**Verificação:** `grep -rln 'logging.getLogger' nyx/ --include='*.py' | grep -v logging_service.py | grep -v proxy.py` retorna vazio.

**Ajuste colateral:** `nyx/themes/__init__.py` ficou com `import logging` órfão após a substituição (o único uso era o `getLogger`). Removido.

**Script de migração:** salvo em `/tmp/migrate_logging.py` durante a execução. Não commitado (é one-shot).

---

## 3. Problemas e observações

### 3.1 Gauntlet bloqueado por OOM de VRAM

**Sintoma:** todas as execuções de `./run.sh --gauntlet --only rapido` hoje falharam nos testes que dependem de inferência (I-05, P-01, P-04, P-05, P-07), com `"Ollama 500: do load request: Post http://127.0.0.1:XXXX/load EOF"` do proxy.

**Causa raiz:** `logs/ollama.log` mostra `total="4.0 GiB" available="1.5 GiB"` na GPU (RTX 3050 Laptop 4GB). O modelo `qwen3:4b` precisa de 2.6 GiB; Ollama tenta carregar, é morto (SIGKILL pelo kernel) por OOM. Gauntlet registra "TIMEOUT Fase infra" ou "13/18 (72%)".

**Evidência:**
```
time=2026-04-18T22:18:57.770-03:00 level=INFO source=types.go:42 msg="inference compute"
  name=CUDA0 description="NVIDIA GeForce RTX 3050 Laptop GPU" total="4.0 GiB" available="1.5 GiB"
time=2026-04-18T22:18:57.770-03:00 level=INFO source=routes.go:1648 msg="entering low vram mode"
...
run.sh, linha 350: 279222 Morto  "$OLLAMA_BIN" serve
```

**Decisão:** as 5 sprints foram validadas por critérios de código (imports, execução de tool via Python, ruff, invariantes). Usuário autorizou marcar como CONCLUIDA sem gauntlet 100%, com débito de infra documentado.

**Não relacionado ao código:** logs anteriores de hoje (17:58) mostram gauntlet 100%. Algo mudou no ambiente -- provavelmente VRAM consumida por outros processos.

### 3.2 Ruff: 3 erros pré-existentes não tocados

```
F841 nyx/agent/tools/analyze_tool.py:46 -- Local variable `old_todos` never used
F841 nyx/agent/tools/todo_write.py:58   -- idem
F401 nyx/agent/tools/web_search.py:67   -- `duckduckgo_search.DDGS` imported but unused
```

Todos em arquivos que não foram escopo das 5 sprints executadas. Regra `scope atômico` aplicada -- não corrigi inline. Fica como débito para sprint futura.

### 3.3 Warnings não-bloqueantes durante migração

Ao rodar o script `/tmp/migrate_logging.py`, o pre-commit hook emitiu:
```
[aviso] print() detectado: nyx/agent/output.py (usar logging)
[aviso] print() detectado: nyx/cli.py (usar logging)
```

Ambos são **permitidos pela ADR-024** (render layer) e `cli.py` (REPL). O hook é genérico e não conhece a ADR. Não bloqueou os commits; apenas avisos.

### 3.4 Ordem de imports após migração de logging

O script colocou `from nyx.agent.services.logging_service import get_logger` logo após `import logging`, o que violava I001 do ruff. Executei `ruff check --fix nyx/` que reorganizou automaticamente em 120 dos 124 pontos; os 4 residuais foram os 3 pré-existentes acima + um `import logging` sem uso em `themes/__init__.py` que corrigi manualmente.

### 3.5 Aviso de acentuação no pre-commit

Commits relacionados a `SPRINT_ORDER_MASTER.md` e `EXECUTAR_SPRINT.md` disparam:
```
[aviso] Possivel falta de acentuacao: EXECUTAR_SPRINT.md
[aviso] Possivel falta de acentuacao: dev-journey/06-sprints/SPRINT_ORDER_MASTER.md
```

Falso positivo do linter. Esses arquivos são gerados por `scripts/update_next_sprint.py` e têm conteúdo com palavras PT-BR corretas (contei manualmente). Não bloqueia.

### 3.6 Baseline do gauntlet "regrediu"

`GAUNTLET_REPORT.md` hoje mostra `"REGRESSAO: Pass rate caiu: 100% -> 67%"`. Isso é artefato do baseline salvo quando gauntlet passou antes (17:58). Comparado com o estado atual (OOM), parece regressão. **Não é regressão de código**; é degradação de ambiente. O baseline será atualizado quando o gauntlet voltar a passar 100% em próxima janela com VRAM livre.

### 3.7 Hash de ADR-024 no GUIDE.md

Ao atualizar `GUIDE.md` na AUDIT-FIX-06, notei que a tabela de contagem de ADRs no componentes diz "24" mas a tabela de ADRs vigentes só ia até 020. Pula direto para 024 agora. ADR-021/022/023 não têm arquivo correspondente em `dev-journey/03-decisions/` -- são referências que serão materializadas em sprints futuras (VISION-01, UX-DESIGN-01 etc).

---

## 4. Estado atual do repositório

### 4.1 Estrutura nova

Dois pacotes criados:
- `nyx/agent/commands/` (9 arquivos, split de `commands.py`)
- `nyx/agent/loop/` (5 arquivos, split de `loop.py`)

ADR novo:
- `dev-journey/03-decisions/ADR_024_RENDER_LAYER.md`

### 4.2 Arquivos removidos

- `nyx/agent/commands.py` (919 linhas, virou pacote)
- `nyx/agent/loop.py` (753 linhas, virou pacote)

### 4.3 Contadores pós-sessão

```
Tools:     35
Commands:  50 (registrados via @nyx_command)
Services:  9
Sprints:   83 concluídas | 32 pendentes | 5 backlog
```

(Nota: o contador de "concluídas" já inclui as 5 desta sessão conforme `update_next_sprint.py` atualizou o SPRINT_ORDER_MASTER.)

### 4.4 Invariantes

```
[FAIL] 1. emoji em .py (ADR-004)
[FAIL] 2. menção a IA em .py (ADR-005)
[FAIL] 4. except silencioso sem log
[FAIL] 10. ruff reclama
PASS: 8 / FAIL: 4
```

Reduziu de 6 FAILs (início da sessão) para 4 FAILs (fim). Fechou #3 e #7.

---

## 5. Commits (ordem cronológica)

```
7ab9414 refactor: split commands.py 919 linhas em pacote por categoria
f4a0484 docs: registra hash AUDIT-FIX-05 no SPRINT_ORDER_MASTER
5528e63 docs: ADR-024 normaliza output.py como render layer
921ab10 docs: registra hash AUDIT-FIX-06 no SPRINT_ORDER_MASTER
614c28c refactor: ask_user retorna payload, UI renderizada por output.py (ADR-013)
80be106 docs: registra hash AUDIT-FIX-07 no SPRINT_ORDER_MASTER
43cf4d2 refactor: split loop.py 753 linhas em pacote por responsabilidade
223b77c docs: registra hash DEBT-01 no SPRINT_ORDER_MASTER
0ac665e refactor: logging unificado via logging_service.get_logger (ADR-015)
98fe31b docs: registra hash DEBT-03 no SPRINT_ORDER_MASTER
```

10 commits totais (5 de código + 5 de hash no master).

---

## 6. Recomendações para próxima sessão

### 6.1 Antes de começar UX-DESIGN-01

1. **Liberar VRAM.** Fechar Claude Desktop/Chrome durante execução para ter ~3 GiB livres e rodar o gauntlet com validação completa.
2. **Re-rodar gauntlet completo** em estado limpo para gerar novo baseline 100% e apagar o "REGRESSAO" do report atual.

### 6.2 UX-DESIGN-01 (próxima)

Pelo catálogo `GAMBIARRAS_POR_SPRINT.md`, esta sprint fecha invariantes #1 (emoji), #2 ("Claude Code" docstring em `output.py:302`), #6 (hex hardcoded). Pontos de atenção:

- `nyx/agent/output.py:302` tem docstring mencionando "Claude Code" -- isso é o que pega o FAIL #2. Precisa ser reescrito sem menção.
- Os emojis FAIL #1 podem estar em strings de UI -- precisa ver quais e migrar para tokens de design (`BULLETS`, `ICONS`, etc.).
- Criar `nyx/themes/design_tokens.py` (se ainda não existe) com `NYX_ACCENT` e derivações ANSI via função (`hex_to_ansi_fg`).

### 6.3 Débito técnico deixado

- 3 erros ruff pré-existentes (`web_search.py`, `todo_write.py`, `analyze_tool.py`) -- considerar criar issue ou sprint de higienização.
- FAIL #4 (except silencioso) remanescente em `nyx/agent/memory.py:130`, `nyx/agent/output.py:268`, `nyx/context/project.py:80`. AUDIT-FIX-07 fechou um (ask_user.py:78) mas não os outros. Criar sprint futura ou incluir em DEBT-04.
- Tabela ADRs em `GUIDE.md` pula de 020 para 024. Quando VISION e UX-DESIGN criarem 021/022/023, a tabela deve ser reordenada.

---

## 7. Arquivos que a próxima sessão deve consultar

- `EXECUTAR_SPRINT.md` (raiz) -- prompt já preenchido com `UX-DESIGN-01`.
- `dev-journey/06-sprints/SPRINT_ORDER_MASTER.md` linha 260-274 -- estado do Bloco 2.
- `dev-journey/06-sprints/producao/SPRINT_UX_DESIGN_01.md` -- spec da próxima.
- `dev-journey/08-templates/GAMBIARRAS_POR_SPRINT.md` seção "UX-DESIGN-01" -- bypass-paths conhecidos.

---

*"Documentar é dar nome ao que aprendemos à força." -- anônimo*
