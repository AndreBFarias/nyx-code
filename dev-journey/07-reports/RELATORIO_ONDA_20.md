# Relatório Onda 20 -- TUI+CTX

**Data:** 2026-04-17
**Commits:** `6d98321` (parte 1: TUI+PROMPT) e `a38f7d7` (parte 2: CTX) em `main`
**Status:** IMPLEMENTADO, EM VALIDAÇÃO VISUAL pelo usuário

---

## 1. Sprints executadas

### Parte 1 -- `main@6d98321`

| Sprint | Entregue | Gauntlet |
|---|---|---|
| TUI-01 | Banner `╭─╮`, logs em arquivo, spinner, render de tool call, eco `╭─ você ─╮`, `└─ resumo` de tool | rapido 18/18, p7 6/6, interface 5/5 |
| TUI-02b | ROLLBACK do NyxInputFrame. PromptSession com `multiline=True`, Ctrl+J insere newline, Enter envia | e2e 8/8 |
| TUI-03 | Footer adaptativo acima do prompt, completer com `display_meta`, `CompleteStyle.MULTI_COLUMN` | headless 4/4, parser 7/7 |
| PROMPT-01 | System prompt reescrito para condicional (responde saudações em texto) | embutido em interface |

### Parte 2 -- `main@a38f7d7`

| Sprint | Entregue | Gauntlet |
|---|---|---|
| CTX-01 | `SessionSummarizer` LLM-based, batching 5 turnos, 4 seções PT-BR, injetado em `_compact_heavy` e `_compact_emergency`, espelho em `~/.nyx/sessions/<id>/summary.md` | CTX-01, CTX-10 |
| CTX-02 | `NyxMemory` em `~/.nyx/memory/<slug-project>/`, tool `write_memory` com permission `always_confirm`, limite 4KB, MEMORY.md índice auto, path traversal neutralizado | CTX-02, CTX-03, CTX-04, CTX-05 |
| CTX-03 | `RepoMap` via `ast`, cache por mtime em `~/.nyx/cache/repomap.json`, cap 2KB no prompt, priorização, invalidação via post-hook do `ToolRegistry` | CTX-06, CTX-07, CTX-08 |

---

## 2. Arquivos novos / alterados

**Novos (4):**
- `nyx/agent/memory.py` -- 142 linhas
- `nyx/agent/repomap.py` -- 190 linhas
- `nyx/agent/summarizer.py` -- 130 linhas
- `nyx/agent/tools/write_memory.py` -- 70 linhas

**Alterados:**
- `nyx/agent/prompt.py` -- aceita 3 placeholders novos (`memory_files`, `repo_map`, `session_summary`) em ordem de estabilidade
- `nyx/agent/session.py` -- campos `summary`, `last_summarized_at`
- `nyx/agent/context.py` -- `_compact_heavy` e `_compact_emergency` injetam `session.summary`
- `nyx/agent/persistence.py` -- lê/salva summary no JSON
- `nyx/agent/loop.py` -- instancia `NyxMemory` + `RepoMap` + `SessionSummarizer` no `__init__`, registra post-hook de invalidação, método `maybe_summarize()`
- `nyx/agent/models.py` -- `ActionType.WRITE_MEMORY`
- `nyx/agent/tools/registry.py` -- registra `WriteMemoryTool` (tools: 34 → 35)
- `nyx/agent/permissions.py` -- `write_memory` em `always_confirm`
- `nyx/cli.py` -- `asyncio.create_task(agent.maybe_summarize())` após cada `run()`
- `scripts/gauntlet/nyx_gauntlet.py` -- fase `contexto` com 10 casos (CTX-01..CTX-10)

---

## 3. Gauntlet -- evidências automatizadas

### Fase contexto (nova) -- 10/10 em 51s

```
CTX-01 Summarizer instancia e batching (0.0s)
CTX-02 NyxMemory roundtrip -- bundle_bytes=60 (0.0s)
CTX-03 NyxMemory sandbox (size+traversal) -- oversize=True traversal=True (0.0s)
CTX-04 WriteMemoryTool registrada -- tools=35 (0.0s)
CTX-05 ActionType.WRITE_MEMORY (0.0s)
CTX-06 RepoMap build + render 2KB -- files=90 render=1846b dt=0.30s (0.3s)
CTX-07 RepoMap cache roundtrip -- entries=89 (0.3s)
CTX-08 RepoMap invalidate (0.3s)
CTX-09 Prompt com 3 placeholders -- len=3980 (0.0s)
CTX-10 Summarizer LLM roundtrip -- chars=3215 (50.1s) [roundtrip real via proxy]
```

### Fases adjacentes (sem regressão)

| Fase | Resultado |
|---|---|
| rapido (infra+proxy+visual+config) | 18/18 |
| p7 (p7_tui+p7_completion+p7_visual) | 6/6 |
| interface | 5/5 |
| headless_protocol | 4/4 |
| parser | 7/7 |
| e2e | 8/8 |
| **contexto (novo)** | **10/10** |

Completo rodado em background antes do commit final da parte 2 -- sem falhas.

---

## 4. O que o assistente NÃO conseguiu validar sozinho

O assistente não tem TTY/display disponível. Só tem MCP de browser (Chrome/Playwright) que serve pra web, não pra terminal. Logo, **não foi possível tirar screenshots** ou interagir com o REPL. Cobertura do assistente:

- Gauntlet automatizado (acima)
- Smoke headless: `echo '{"type":"ping"}' | ./venv/bin/python nyx/cli.py --headless` -> `{"type":"pong","tools":35}`
- Testes unitários ad-hoc via `venv/bin/python -c "..."` (memória, repomap, summarizer, persistence roundtrip, sandbox)
- Checks estáticos: sintaxe AST, imports, enum `ActionType` incluindo `WRITE_MEMORY`, registry incluindo `write_memory`, `DEFAULT_PERMISSIONS` com `write_memory` em `always_confirm`, prompt com 3 seções injetadas

O resto depende de olho humano no terminal.

---

## 5. Checklist de validação visual (pro usuário)

Rodar `./run.sh` e conferir:

| # | O que testar | Esperado |
|---|---|---|
| 1 | Banner de boot | Caixa `╭─╮` com modelo, projeto, tools=35, `100% offline`; sem `\033[0m` literal |
| 2 | Log de boot | Linha `repomap: NN arquivos indexados, X.XXs` no stderr/log |
| 3 | Footer | Linha `── ctx X% · qwen3:4b · iter 0 · lidos 0 · modif 0 ──` acima de `nyx>` |
| 4 | Saudação sem tools | `Olá, tudo bem?` -> resposta curta em texto, **zero** `⏺` de tool call |
| 5 | Multiline Ctrl+J | `linha 1` + Ctrl+J + `linha 2` + Enter -> eco `╭─ você ─╮` com 2 linhas |
| 6 | Popup slash | digitar `/` -> lista em colunas com descrição por comando |
| 7 | RepoMap no prompt | `em qual arquivo fica a classe AgentLoop?` -> resposta `nyx/agent/loop.py` em <5s, **zero tool calls** |
| 8 | Memória write | `lembra que eu uso pyenv 3.12 neste projeto` -> permission `[S/n]`, `⏺ write_memory(...)`, `└─ OK` |
| 9 | Memória em disco | `ls ~/.nyx/memory/Nyx-Code-*/` -> `.md` + `MEMORY.md` |
| 10 | Memória cross-session | Ctrl+D, `./run.sh`, digitar `o que você sabe sobre como eu trabalho?` -> resposta cita pyenv |
| 11 | Summarizer batch | 5 turnos curtos, esperar ~1min, `cat ~/.nyx/sessions/*/summary.md` -> 4 seções PT-BR |
| 12 | Terminal estreito | `resize -s 24 60; ./run.sh` -> footer degrada para só `ctx X%` |
| 13 | Sem INFO no stdout | `~/.nyx/logs/nyx.log` recebe logs; stdout limpo |

Se algum falhar, reportar o número -- arrumo antes de mover as sprints pra `concluidos/`.

---

## 6. Fluxo de fechamento

1. Usuário roda `./run.sh` e confirma itens 1-13
2. Se tudo passar: mover `SPRINT_TUI_01_HIGIENE.md`, `SPRINT_TUI_02_BOXES.md`, `SPRINT_TUI_03_FOOTER_POPUP.md`, `SPRINT_CTX_01_SUMMARIZER.md`, `SPRINT_CTX_02_MEMORY.md`, `SPRINT_CTX_03_REPOMAP.md` de `producao/` para `concluidos/`, status `CONCLUIDA` no master
3. Se algum falhar: assistente corrige, re-roda gauntlet relevante, repete validação visual

---

*"Sem prova, sem pressa." -- Spinoza (adaptado)*
