# Port Status: OpenClaude TypeScript -> Nyx Python

**Atualizado:** 2026-05-21
**Source TS:** `openclaud/src/` (127.516 linhas, 1.884 arquivos)
**Destino Python:** `nyx/` (~6.000 linhas)
**Nota:** este documento rastreia paridade vs OpenClaude TS. Para snapshot canônico do projeto (contagens, gate v1.0, sprints), ver `dev-journey/08-templates/PROJECT_SNAPSHOT.md`.

---

## Resumo

| Componente | OpenClaude | Nyx | Falta | Cobertura |
|-----------|-----------|-----|-------|-----------|
| Tools | 40 | 35 | 5 | 87% |
| Commands | 98 | 67 | 31 | 68% |
| Services | 35 | 16 | 19 | 45% |
| **TOTAL** | **173** | **118** | **55** | **68%** |

Meta: 100% (ADR-012)

---

## 1. TOOLS (40 OpenClaude -> 35 Nyx)

### Portadas (35)

| OpenClaude | Nyx Python | Arquivo | Status |
|-----------|-----------|---------|--------|
| AgentTool | AgentTool | `tools/agent_tool.py` | OK |
| AskUserQuestionTool | AskUserTool | `tools/ask_user.py` | OK |
| BashTool | RunCommandTool | `tools/run_command.py` | PARCIAL (simplificado) |
| BriefTool | BriefTool | `tools/brief_tool.py` | OK |
| ConfigTool | ConfigTool | `tools/config_tool.py` | OK |
| EnterPlanModeTool | EnterPlanModeTool | `tools/plan_mode.py` | OK |
| EnterWorktreeTool | EnterWorktreeTool | `tools/worktree.py` | OK |
| ExitPlanModeTool | ExitPlanModeTool | `tools/plan_mode.py` | OK |
| ExitWorktreeTool | ExitWorktreeTool | `tools/worktree.py` | OK |
| FileEditTool | EditFileTool | `tools/edit_file.py` | OK |
| FileReadTool | ReadFileTool | `tools/read_file.py` | OK |
| FileWriteTool | WriteFileTool | `tools/write_file.py` | OK |
| GlobTool | GlobTool | `tools/glob_tool.py` | OK |
| GrepTool | SearchTool | `tools/search.py` | OK |
| NotebookEditTool | NotebookEditTool | `tools/notebook_edit.py` | OK |
| REPLTool | REPLTool | `tools/repl_tool.py` | OK |
| SendMessageTool | SendMessageTool | `tools/send_message.py` | OK |
| SkillTool | SkillTool | `tools/skill_tool.py` | OK |
| SleepTool | SleepTool | `tools/sleep_tool.py` | OK |
| TaskCreateTool | TaskCreateTool | `tools/task_manager.py` | OK |
| TaskGetTool | TaskGetTool | `tools/task_manager.py` | OK |
| TaskListTool | TaskListTool | `tools/task_manager.py` | OK |
| TaskOutputTool | TaskOutputTool | `tools/task_manager.py` | OK |
| TaskStopTool | TaskStopTool | `tools/task_manager.py` | OK |
| TaskUpdateTool | TaskUpdateTool | `tools/task_manager.py` | OK |
| TodoWriteTool | TodoWriteTool | `tools/todo_write.py` | OK |
| ToolSearchTool | ToolSearchTool | `tools/tool_search.py` | OK |
| WebFetchTool | WebFetchTool | `tools/web_fetch.py` | OK |
| WebSearchTool | WebSearchTool | `tools/web_search.py` | OK |

**Extras Nyx (sem equivalente no OpenClaude):**

| Tool | Arquivo | Descrição |
|------|---------|-----------|
| AnalyzeTool | `tools/analyze_tool.py` | Análise estrutural de código |
| PatchTool | `tools/patch_tool.py` | Aplica unified diff |
| MultiEditTool | `tools/multi_edit.py` | Edição multi-arquivo atômica |
| DoneTool | `tools/done.py` | Sinaliza fim de tarefa |
| ListFilesTool | `tools/list_files.py` | Lista diretórios |

### Faltam portar (6) -- Sprint P9

| OpenClaude | Sprint | Adaptação local-first |
|-----------|--------|----------------------|
| MCPTool | P9-A | Protocolo MCP local (sem cloud) |
| McpAuthTool | P9-A | Auth MCP local |
| ListMcpResourcesTool | P9-A | Listar recursos MCP locais |
| ReadMcpResourceTool | P9-A | Ler recursos MCP locais |
| LSPTool | P9-A | Cliente LSP para code intelligence |
| ScheduleCronTool | P9-B | Agendamento via crontab/schedule |

**Adaptados (não port 1:1, adaptação cross-platform):**

| OpenClaude | Sprint | Adaptação |
|-----------|--------|-----------|
| PowerShellTool | P9-B | ShellTool cross-platform (bash no Linux) |
| RemoteTriggerTool | P9-B | Trigger local via subprocess/webhook |
| SyntheticOutputTool | P9-B | Output estruturado local |
| TeamCreateTool | P9-B | Equipes locais (arquivo JSON) |
| TeamDeleteTool | P9-B | Remoção de equipes locais |

---

## 2. COMMANDS (98 OpenClaude -> 33 Nyx)

### Portados (33)

| Nyx Command | Categoria | Aliases | OpenClaude equivalente |
|-------------|----------|---------|----------------------|
| /help | geral | /h | help |
| /quit | geral | /q, /exit | exit |
| /clear | geral | | clear |
| /status | geral | | status |
| /explain | código | /exp | (prompt-based) |
| /plan | código | | plan |
| /test | código | /tst | (prompt-based) |
| /compact | sessão | | compact |
| /commit | git | | commit |
| /diff | git | /d | diff |
| /doctor | sistema | /dr | doctor |
| /review | git | /rv | review |
| /model | sistema | /m | model |
| /context | sessão | /ctx | context |
| /session | sessão | /sess | session |
| /branch | git | /br | branch |
| /issue | git | | issue |
| /pr | git | | pr_comments |
| /rewind | sessão | | rewind |
| /config | sistema | | config |
| /env | sistema | | env |
| /permissions | sistema | /perms | permissions |
| /hooks | sistema | | hooks |
| /theme | sistema | | theme |
| /resume | sessão | | resume |
| /export | sessão | | export |
| /copy | sessão | | copy |
| /summary | sessão | | summary |
| /stats | sessão | | stats |
| /usage | sessão | | usage |
| /tasks | execução | | tasks |
| /skills | execução | | skills |
| /files | execução | | files |

### Faltam portar (65) -- Sprints P10-A a P10-J

**P10-A: Auth (5)**
login, logout, oauth-refresh, install-github-app, install-slack-app

**P10-B: Projeto (5)**
add-dir, init, onboarding, version, rename

**P10-C: UI (7)**
color, output-style, keybindings, stickers, fast, effort, vim

**P10-D: Debug (9)**
ant-trace, autofix-pr, bughunter, ctx_viz, debug-tool-call, heapdump, perf-issue, good-claude, break-cache

**P10-E: Plataforma (9)**
chrome, desktop, ide, mobile, bridge, teleport, remote-env, remote-setup, voice

**P10-F: Ciclo de vida (6)**
upgrade, release-notes, feedback, privacy-settings, sandbox-toggle, terminalSetup

**P10-G: Limites (6)**
cost, extra-usage, mock-limits, passes, rate-limit-options, reset-limits

**P10-H: Memória (6)**
memory, plugin, reload-plugins, agents, share, tag

**P10-I: Avançado (6)**
btw, bridge-kick, backfill-sessions, thinkback, thinkback-play, pr_comments

**P10-J: Root commands (5)**
advisor, brief(cmd), commit-push-pr, insights, security-review

---

## 3. SERVICES (35 OpenClaude -> 8 Nyx)

### Portados (8)

| Nyx Service | Arquivo | OpenClaude equivalente |
|-------------|---------|----------------------|
| AutoCompactService | `services/compact.py` | compact/ |
| ToolHooks | `services/hooks.py` | tools/ (hook system) |
| token estimation | `services/tokens.py` | tokenEstimation.ts |
| SessionMemory | `services/memory.py` | SessionMemory/ |
| AgentSummary | `services/summary.py` | AgentSummary/ |
| PromptSuggestion | `services/suggestions.py` | PromptSuggestion/ |
| Preflight | `agent/preflight.py` | (distributed) |
| PostValidator | `agent/validator.py` | (distributed) |

### Faltam portar (27) -- Sprints P11-A a P11-G

**P11-A: Infra (5)**
analytics, diagnosticTracking, internalLogging, notifier, preventSleep

**P11-B: Auth (4)**
oauth, claudeAiLimits, claudeAiLimitsHook, policyLimits

**P11-C: Plugins (4)**
plugins, MagicDocs, tips, toolUseSummary

**P11-D: Sync (3)**
settingsSync, remoteManagedSettings, teamMemorySync

**P11-E: Conteúdo (4)**
extractMemories, autoDream, awaySummary, AgentSummary (expandir)

**P11-F: Protocolo (4)**
mcp, lsp, api, vcr

**P11-G: Voz + Rate (6)**
voice, voiceStreamSTT, voiceKeyterms, rateLimitMessages, rateLimitMocking, mockRateLimits

---

## 4. MÓDULOS CORE

| Módulo | Arquivo | Origem | Status |
|--------|---------|--------|--------|
| AgentLoop | `agent/loop.py` | main.tsx + assistant/ | OK |
| ActionParser | `agent/parser.py` | Luna parser.py | OK (7 níveis) |
| CodeSession | `agent/session.py` | Luna session.py | OK |
| ContextBudget | `agent/context.py` | Luna context_manager.py | OK |
| PermissionChecker | `agent/permissions.py` | Luna permissions.py | OK |
| RepetitionDetector | `agent/repetition.py` | Luna repetition.py | OK |
| StreamingCollector | `agent/streaming.py` | Luna streaming.py | OK |
| RichOutput | `agent/output.py` | Luna rich_output.py | OK |
| PathResolver | `agent/path_resolver.py` | Luna path_resolver.py | OK |
| ModelTier | `agent/model_tier.py` | Luna model_tier.py | OK |
| GitOps | `agent/git_ops.py` | Luna git_ops.py | OK |
| Persistence | `agent/persistence.py` | Luna persistence.py | OK |
| SystemPrompt | `agent/prompt.py` | Luna prompt.py | OK |
| Models | `agent/models.py` | Luna models.py | OK |
| Commands | `agent/commands.py` | Luna commands.py | OK (67 cmds) |
| ToolRegistry | `agent/tools/registry.py` | Luna tools/registry.py | OK (35 tools) |
| OllamaProvider | `providers/ollama.py` | Luna ollama_client/ | OK |
| ProjectContext | `context/project.py` | openclaud context/ | OK |

---

*"A completude é a medida da seriedade." -- Wittgenstein*
