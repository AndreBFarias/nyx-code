# Sprint Order Master -- Nyx-Code

**Versão:** v5.0
**Data:** 2026-04-05
**Modelo obrigatório:** Opus 4.6 (claude-opus-4-6) -- sem subagentes

---

## Visão Geral

Sprints concluídas em `dev-journey/06-sprints/concluidos/`.
Sprints de produção em `dev-journey/06-sprints/producao/`.
Template canônico: `dev-journey/08-templates/SPRINT_TEMPLATE.md`.
Port status: `dev-journey/PORT_STATUS.md`.

**Princípios (16 ADRs):**
1. **Local First:** Tudo funciona offline (ADR-001)
2. **Gauntlet obrigatório:** Sprint que afeta proxy/tools/TUI -> rodar `./run.sh --gauntlet` (ADR-007)
3. **Zero mocks:** todos os testes contra infraestrutura real (ADR-010)
4. **Conteúdo verificado:** testes validam conteúdo, não só success (ADR-011)
5. **Cobertura 100%:** todo componente do OpenClaude tem equivalente Python (ADR-012)
6. **Integração obrigatória:** nada solto, tudo no registry/commands/services (ADR-013)
7. **Testes via Gauntlet:** sem pytest/unittest, tudo no gauntlet (ADR-014)
8. **Documentação:** docs suficientes para nova sessão IA continuar (ADR-015)

---

## Inventário

> **Fonte única:** `dev-journey/08-templates/PROJECT_SNAPSHOT.md` §Contagens. Verificação executável: `python scripts/sync.py` imprime `inventario: tools=N, commands_unicos=M, services=S` na primeira linha. Em 2026-04-21 (pós BANNER-TOOLS-COUNT-01): **35 tools (runtime) · 52 commands únicos · 9 services · 24 ADRs · 135+ testes no Gauntlet**.

**Nota histórica:**
- **2026-04-09 (limpeza PROD):** removidos 27 command-stubs cloud e 11 service-stubs cloud. Port 1:1 do OpenClaude abandonado. Foco em funcionalidade local-first; features cloud/enterprise (voice, mobile, chrome, plugins, rate-limit, etc) não se aplicam.
- **2026-04-21 (INVENTORY-SYNC-01):** contagens antes divergiam em 3 documentos (34/47/10 vs 30/54/9 vs filesystem 28/52/9). Normalizado apontando para `PROJECT_SNAPSHOT.md` como fonte única. Número de tools adotado (28) refletia filesystem, não registry runtime — ainda contradizia o banner do REPL que exibia 35.
- **2026-04-21 (BANNER-TOOLS-COUNT-01):** reconciliado com autoridade runtime. `ToolRegistry.tool_count == 35`; diferença de 7 explicada por arquivos que exportam múltiplas tools: `task_manager.py` (6 tools: task_create/update/list/get/output/stop → +5), `plan_mode.py` (enter/exit_plan_mode → +1), `worktree.py` (enter/exit_worktree → +1). Contagem canônica passa a ser runtime (`ToolRegistry.tool_count`) em vez de filesystem (`find`). Evolução: 34 → 30 → 28 (filesystem) → 35 (runtime, definitivo).

---

## Blocos concluídos

### Bloco G: Gauntlet -- CONCLUIDO
G-01 a G-08. Framework de 36 testes, 8 fases, report automático.

### Bloco D: DevOps -- CONCLUIDO
D-01 (CI), D-02 (pre-commit), D-03 (sync.py).

### Bloco F: Fix -- CONCLUIDO
F-01 (limpar bundle), F-02 (Gauntlet E2E real, 8 testes).

### Bloco P: Port Core -- CONCLUIDO
P-01 (agent loop), P1-A a P1-F (parser, robustez, interface, controle, persistência, integração).

### Bloco P2: Features TS -- CONCLUIDO
P2-A (TodoWrite, WebFetch, WebSearch), P2-B (Tasks, PlanMode, Agent), P2-C (commands git), P2-D (services).

### Bloco P3: Avançado -- CONCLUIDO
P3-A (NotebookEdit, AskUser), P3-B (commands sessão), P3-C (hooks, PlanMode), P3-D (headless).

### Bloco I-01: Headless -- CONCLUIDO
Protocolo JSON expandido (ping, status, tools, session, request, reset, erro).

### Bloco P4: Tools Intermediários -- CONCLUIDO
P4-A (Sleep, Config, Brief), P4-B (Worktree), P4-C (Tasks expandido), P4-D (REPL, ToolSearch, Skill, SendMessage). **+12 tools, +12 testes.**

### Bloco P5: Commands Expandidos -- CONCLUIDO
P5-A (Git), P5-B (Config), P5-C (Sessão), P5-D (Execução). **+18 commands, +19 testes.**

### Bloco P6: Services -- CONCLUIDO
P6-A (Memory, Summary), P6-B (Suggestions, Preflight, Validator). **+5 services, +7 testes.**

### Bloco P8: Edição Avançada -- CONCLUIDO
P8-A (Analyze, Patch, MultiEdit), P8-B (Provider, ProjectContext). **+3 tools, +5 testes.**

**Subtotal concluído: 34 tools | 33 commands | 8 services | 135 testes**

---

## Blocos pendentes

### Bloco INFRA: Automação e QoL (pré-requisito para tudo)

| # | Nome | Testes | Status | Deps |
|---|------|--------|--------|------|
| **INFRA-01** | Scaffold automático (scripts/scaffold.py) | +3 testes | CONCLUIDA | -- |
| **INFRA-02** | Gauntlet coverage (fase automática de completude) | +6 testes | CONCLUIDA | INFRA-01 |
| **INFRA-03** | sync.py enhanced (verificação de integração) | +5 testes | CONCLUIDA | INFRA-02 |

**ADRs:** ADR-017 (Scaffold-first), ADR-018 (Stubs progressivos), ADR-019 (Gauntlet coverage)

**O que muda:** após INFRA, toda sprint futura usa scaffold.py para criar componentes. Gauntlet detecta automaticamente gaps. sync.py valida integração completa. Criar 98 componentes vira mecânico.

### Bloco P7: Interface TUI (prompt-toolkit)

| # | Nome | Testes | Status | Deps |
|---|------|--------|--------|------|
| **P7-A** | Base: histórico, input multilinha, keybindings | +2 testes | CONCLUIDA | P5-D |
| **P7-B** | Completion: paths, commands, tools | +2 testes | CONCLUIDA | P7-A |
| **P7-C** | Visual: diff boxes, spinners, progress bars | +2 testes | CONCLUIDA | P7-B |

### Bloco P9: Tools restantes (+12 tools)

| # | Nome | Testes | Status | Deps |
|---|------|--------|--------|------|
| **P9-A** | MCP + LSP (MCPTool, McpAuth, ListMcp, ReadMcp, LSP) | +5 testes | CONCLUIDA | P8-B |
| **P9-B** | Platform (Shell, Trigger, Schedule, Synthetic, Team x2, Bash expand) | +7 testes | CONCLUIDA | P9-A |

### Bloco P10: Commands restantes (+65 commands)

| # | Nome | Testes | Status | Deps |
|---|------|--------|--------|------|
| **P10-A** | Auth: login, logout, oauth-refresh, install-github, install-slack | +5 testes | CONCLUIDA | P9-B |
| **P10-B** | Projeto: add-dir, init, onboarding, version, rename | +5 testes | CONCLUIDA | P9-B |
| **P10-C** | UI: color, output-style, keybindings, stickers, fast, effort, vim | +7 testes | CONCLUIDA | P9-B |
| **P10-D** | Debug: trace, autofix-pr, bughunter, ctx-viz, debug-tool, heapdump, perf-issue, kudos, break-cache | +9 testes | CONCLUIDA | P10-A |
| **P10-E** | Plataforma: chrome, desktop, ide, mobile, bridge, teleport, remote-env, remote-setup, voice | +9 testes | CONCLUIDA | P10-A |
| **P10-F** | Lifecycle: upgrade, release-notes, feedback, privacy, sandbox, terminal-setup | +6 testes | CONCLUIDA | P10-B |
| **P10-G** | Limites: cost, extra-usage, mock-limits, passes, rate-limit, reset-limits | +6 testes | CONCLUIDA | P10-B |
| **P10-H** | Memória: memory, plugin, reload-plugins, agents, share, tag | +6 testes | CONCLUIDA | P10-C |
| **P10-I** | Avançado: btw, bridge-kick, backfill, thinkback, thinkback-play, pr-comments | +6 testes | CONCLUIDA | P10-C |
| **P10-J** | Root: advisor, brief-cmd, commit-push-pr, insights, security-review | +5 testes | CONCLUIDA | P10-D |

### Bloco P11: Services restantes (+27 services)

| # | Nome | Testes | Status | Deps |
|---|------|--------|--------|------|
| **P11-A** | Infra: analytics, diagnostics, logging, notifier, preventSleep | +5 testes | CONCLUIDA | P10-J |
| **P11-B** | Auth: oauth, limits, policy | +4 testes | CONCLUIDA | P10-A |
| **P11-C** | Plugins: plugins, MagicDocs, tips, toolUseSummary | +4 testes | CONCLUIDA | P11-A |
| **P11-D** | Sync: settingsSync, remoteSettings, teamSync | +3 testes | CONCLUIDA | P11-A |
| **P11-E** | Conteúdo: extractMemories, autoDream, awaySummary, summary expandido | +4 testes | CONCLUIDA | P11-B |
| **P11-F** | Protocolo: mcp, lsp, api, vcr | +4 testes | CONCLUIDA | P11-B |
| **P11-G** | Voz + Rate: voice, voiceSTT, voiceKeyterms, rateLimiting | +4 testes | CONCLUIDA | P11-C |

---

### Bloco AUDIT: Auditoria Completa (pós-port)

| # | Nome | Testes | Status | Deps |
|---|------|--------|--------|------|
| **AUDIT-01** | Segurança: path traversal, preflight, validator | +6 testes | CONCLUIDA | -- |
| **AUDIT-03** | Sincronização N-para-N: versão, constantes, dependências | +4 testes | CONCLUIDA | -- |
| **AUDIT-02** | Integração de serviços mortos | +6 testes | CONCLUIDA | AUDIT-01 |
| **AUDIT-04** | Except handling e qualidade de código | +3 testes | CONCLUIDA | AUDIT-01 |
| **AUDIT-05** | Performance: conexões, search, proxy | +3 testes | CONCLUIDA | AUDIT-04 |
| **AUDIT-06** | Robustez e UX: shutdown, health check, atomicidade | +4 testes | CONCLUIDA | AUDIT-05 |

**Origem:** Auditoria completa do código-fonte (2026-04-15). Todos os arquivos de `nyx/` lidos e analisados.

---

### Bloco PORT: Portabilidade (preparação para hardware novo)

| # | Nome | Testes | Status | Deps |
|---|------|--------|--------|------|
| **PORT-01** | Auto-tune de GPU layers | +3 testes | CONCLUIDA | -- |
| **PORT-02** | Teste de máquina limpa via Docker | +2 testes | CONCLUIDA | PORT-01 |
| **PORT-03** | Robustez de boot (R-02/R-03/R-04) | +3 testes | CONCLUIDA | PORT-01, PORT-02 |

**Origem:** projeto otimizado apenas para a máquina atual (RTX 3050 4GB, num_gpu=12 hardcoded). Portabilidade nunca foi validada em hardware diferente ou máquina limpa.

### Bloco LUNA: Integração com Luna (DELEGADA AO REPO LUNA)

| # | Nome | Status | Delegada para |
|---|------|--------|---------------|
| **I-02** | Substituir nyx antiga na Luna | DELEGADA | `Luna/.../producao/infra/SPRINT_INFRA50..52_*.md` |
| **I-03** | Mensagens inline [nyx] na TUI | DELEGADA | `Luna/.../producao/infra/SPRINT_INFRA53_NYX_INLINE_TUI.md` |

**Origem:** a Luna já tinha um code agent interno (nyx antiga). Objetivo: substituir pelo Nyx-Code standalone via subprocess headless (protocolo I-01 pronto).

**Desfecho (2026-04-16):** como as mudanças são no repo da Luna, foram criadas 4 sprints novas no próprio repo Luna (INFRA-50 a 53) com código pronto pra copiar. Este Nyx-Code oferece apenas o protocolo headless (ja concluido em I-01), sem mudanças adicionais necessárias.

---

### Bloco TUI+CTX: Redesign TUI estilo Claude Code CLI + Sistema de contexto

| # | Nome | Testes | Status | Deps |
|---|------|--------|--------|------|
| **TUI-01** | Higiene: silenciar logs, corrigir banner, formatar tool calls | +2 testes | CONCLUIDA (VALIDATE-ONDA-20 2026-04-20) | -- |
| **TUI-02** | Boxes ╭─╮ no user input, tool calls com ⏺ └─ colapsável | +2 testes | CONCLUIDA (VALIDATE-ONDA-20 2026-04-20) | TUI-01 |
| **TUI-03** | Footer 1 linha + popup navegável de slash command | +2 testes | CONCLUIDA (VALIDATE-ONDA-20 2026-04-20) | TUI-02 |
| **CTX-01** | SessionSummarizer: resumo vivo injetado em compactação | +3 testes | CONCLUIDA (VALIDATE-ONDA-20 2026-04-20) | TUI-03 |
| **CTX-02** | Memória persistente cross-session em ~/.nyx/memory/ | +3 testes | CONCLUIDA (VALIDATE-ONDA-20 2026-04-20) | CTX-01 |
| **CTX-03** | RepoMap via AST (tree-sitter opcional, ADR-021) | +4 testes | CONCLUIDA (VALIDATE-ONDA-20 2026-04-20) | CTX-02 |
| **CTX-04** | Plano ativo opt-in via /plan (opcional) | +2 testes | DEFERIDA (VALIDATE-ONDA-20 2026-04-20) | CTX-03 |

**CONCLUIDA = implementado + Gauntlet passou + validação visual/interativa em 2026-04-20 (vide RELATORIO_VALIDACAO_ONDA_20.md). Onda 20 fechada.**

---

### Bloco TUI-FIX: Onda 21 -- correções de UX após validação visual

| # | Nome | Testes | Status | Deps |
|---|------|--------|--------|------|
| **TUI-FIX-01** | Banner único e limpo (sem duplicação, sem ASCII corrompido) | +1 teste | CONCLUIDA (VALIDATE-ONDA-21 2026-04-20) | -- |
| **TUI-FIX-02** | Fim da resposta duplicada (streaming + render final) | +1 teste | CONCLUIDA (VALIDATE-ONDA-21 2026-04-20, ressalva ADR-002) | -- |
| **TUI-FIX-03** | Popup de slash commands abrindo automaticamente | +1 teste | CONCLUIDA (VALIDATE-ONDA-21 2026-04-20) | -- |
| **TUI-FIX-04** | Shift+Tab toggle bypass + bottom toolbar | +2 testes | CONCLUIDA (VALIDATE-ONDA-21 2026-04-20) | -- |
| **TUI-FIX-05** | Ctrl+V + xclip para colar imagens ([Image #N]) | +2 testes | CONCLUIDA (VALIDATE-ONDA-21 2026-04-20) | -- |
| **TUI-FIX-06** | Mensagens de sandbox claras em PT-BR (erro colorido) | +1 teste | CONCLUIDA (VALIDATE-ONDA-21 2026-04-20) | -- |
| **TUI-FIX-07** | Usabilidade geral: footer em toolbar, paste colapsado, /help categorizado, indicador de memória, /memory, /paste, /tools, /recall | +2 testes | ABSORVIDA_POR_TUI-FIX-07A/B/C | FIX-02, FIX-06 |

**Origem:** Validação visual da Onda 20 revelou 6 bugs (banner duplicado, ASCII corrompido, resposta duplicada, popup slash quebrado, ausência de bypass toggle, Ctrl+Shift+V inviável em xterm) + 1 sprint de usabilidade geral. Escopo fechado via screenshots do usuário em 2026-04-17.

**Origem:** UX/UI atual não alcança o Claude Code CLI (referência); sessões longas degradam por falta de sumarização; sem memória cross-session nem repo-map. Brainstorming com usuário em 2026-04-17 fechou escopo.

**Checkpoint entre TUI-03 e CTX-01:** usuário roda `./run.sh` e valida visual antes de atacar contexto.

**ADR novo:** ADR-021 (Dependências opcionais: tree-sitter).

---

## Backlog

CTX-04 permanece opcional. TUI-01..03 + CTX-01..03 implementadas em 2026-04-17, aguardando validação visual do usuário antes de marcar CONCLUIDA.

---

### Bloco ONDA-22: Redesign Total UX + Visão + Deploy

**Origem:** brainstorm do usuário em 2026-04-18 após validação visual da Onda 21. Escopo: auditoria externa + redesign visual + fix de bugs TUI + visão moondream + instalador + desktop entry.

**Decisões fechadas (2026-04-18):**
- D1 visão via moondream CPU (ADR-022)
- D2 paleta mista D (Claude CLI + turquesa + roxo) (ADR-023)
- D3 auditoria cataloga + corrige (gera AUDIT-FIX dinâmicas)
- D4 kitty opcional (padrão Luna)
- D5 SPRINT_TEMPLATE_V2 blindado contra IA descontextualizada

**Template V2:** `dev-journey/08-templates/SPRINT_TEMPLATE_V2.md`
**Catálogo de gambiarras por sprint:** `dev-journey/08-templates/GAMBIARRAS_POR_SPRINT.md`
**Script de invariantes globais:** `scripts/sprint_invariants.sh` (obrigatório ANTES e DEPOIS de cada sprint)
**Relatório da auditoria:** `dev-journey/07-reports/AUDIT_EXT_2026_04_18.md`
**Plano consolidado:** `~/.claude/plans/image-1-venv-andrefarias-nitro-5-purring-thacker.md`

**Protocolo anti-gambiarra obrigatório:**
```bash
# PASSO 1 - antes
bash scripts/sprint_invariants.sh > /tmp/inv_before.txt 2>&1
FAIL_BEFORE=$(grep -c "^\[FAIL\]" /tmp/inv_before.txt)
# PASSO 2 - implementar
# PASSO 3 - depois
bash scripts/sprint_invariants.sh > /tmp/inv_after.txt 2>&1
FAIL_AFTER=$(grep -c "^\[FAIL\]" /tmp/inv_after.txt)
# PASSO 4 - FAIL_AFTER <= FAIL_BEFORE; colar diff no relatório
diff /tmp/inv_before.txt /tmp/inv_after.txt
```
Se `FAIL_AFTER > FAIL_BEFORE`, sprint introduziu regressão. **Reverter e refazer.**

| # | Sprint | Bloco | Prioridade | Status | Depende de |
|---|--------|-------|------------|--------|------------|
| 0 | **AUDIT-EXT-01** | 0 Auditoria | CRÍTICA | CONCLUIDA (commit 46f9ab0) | -- |
| 1 | **AUDIT-FIX-01** | 1 Fundamentos | CRÍTICA | CONCLUIDA (commit 46f9ab0) | -- |
| 2 | **AUDIT-FIX-03** | 1 Fundamentos | CRÍTICA | CONCLUIDA (commit 46f9ab0) | -- |
| 3 | **AUDIT-FIX-04** | 1 Fundamentos | ALTA | CONCLUIDA (commit 46f9ab0) | -- |
| 4 | **DEBT-02** | 1 Fundamentos | BAIXA | CONCLUIDA (commit 46f9ab0) | -- |
| 5 | **AUDIT-FIX-02** | 2 Fundamentos | CRÍTICA | CONCLUIDA (commit ae0115d) | AUDIT-FIX-03 |
| 6 | **AUDIT-FIX-05** | 2 Fundamentos | ALTA | CONCLUIDA (commit 7ab9414) | -- |
| 7 | **AUDIT-FIX-06** | 2 Fundamentos | ALTA | CONCLUIDA (commit 5528e63) | -- |
| 8 | **AUDIT-FIX-07** | 2 Fundamentos | ALTA | CONCLUIDA (commit 614c28c) | -- |
| 9 | **DEBT-01** | 2 Fundamentos | MÉDIA | CONCLUIDA (commit 43cf4d2) | -- |
| 10 | **DEBT-03** | 2 Fundamentos | MÉDIA | CONCLUIDA (commit 0ac665e) | -- |
| 11 | **AUDIT-FIX-08** | 2.5 Limpeza | ALTA | CONCLUIDA (commit 4995500) | -- |
| 12 | **AUDIT-FIX-09** | 2.5 Limpeza | ALTA | CONCLUIDA (commit c2ba860) | -- |
| 13 | **DEBT-04** | 2.5 Limpeza | MÉDIA | CONCLUIDA (commit a326d98) | -- |
| 14 | **DEBT-05** | 2.5 Limpeza | BAIXA | ABSORVIDA_POR_DEBT_06 (commit 4f73432) | -- |
| 15 | **DEBT-06** | 2.5 Limpeza | BAIXA | CONCLUIDA (commit 4f73432) | -- |
| 16 | **ADR-021-DOC** | 2.5 Limpeza | MÉDIA | CONCLUIDA (commit c918e3b) | -- |
| 17 | **ADR-022-DOC** | 2.5 Limpeza | MÉDIA | CONCLUIDA (commit 8eefed3) | -- |
| 18 | **DEBT-07** | 2.5 Limpeza | ALTA | CONCLUIDA (commit 8c91fe5) | -- |
| 19 | **INFRA-GAUNTLET-01** | 2.6 Integração | CRÍTICA | DESCARTADA (decisão de escopo 2026-04-19) | -- |
| 20 | **BOOT-FIX-01** | 2.6 Integração | CRÍTICA | CONCLUIDA (commit bb3d61b) | -- |
| 21 | **BUG-PORT-PARSE-01** | 2.6 Integração | CRÍTICA | CONCLUIDA | -- |
| 22 | **TUI-FIX-08** | 2.8 Fixes Onda 20 | ALTA | CONCLUIDA | BUG-PORT-PARSE-01 |
| 23 | **TUI-FIX-09** | 2.8 Fixes Onda 20 | MÉDIA | CONCLUIDA | BUG-PORT-PARSE-01 |
| 24 | **TUI-FIX-10** | 2.8 Fixes Onda 20 | MÉDIA | CONCLUIDA (commit b17be7d) | TUI-FIX-09 |
| 24b | **GAUNTLET-FIX-LOOP-SPLIT** | 2.6 Integração | CRÍTICA | CONCLUIDA (commit dd29b98) | -- |
| 24c | **AUTOTUNE-FIX-01** | 2.6 Integração | CRÍTICA | CONCLUIDA (commit 6f5273b) | -- |
| 24c1 | **AUTOTUNE-FIX-02** | 2.6 Integração | CRÍTICA | CONCLUIDA (commit d491600) | AUTOTUNE-FIX-01 |
| 24d | **TOOL-INVOKE-MEMORY-01** | 2.6 Integração | ALTA | CONCLUIDA (commit 815f2fc) | AUTOTUNE-FIX-01 |
| 24e | **TUI-POPUP-META-01** | 2.8 Fixes Onda 20 | MÉDIA | CONCLUIDA (commit 94d7327) | -- |
| 24f | **TUI-BOOT-LOG-01** | 2.8 Fixes Onda 20 | BAIXA | CONCLUIDA (commit 91e27f4) | -- |
| 25 | **VALIDATE-ONDA-20** | 2.7 Validação | ALTA | CONCLUIDA (RELATORIO_VALIDACAO_ONDA_20.md) | BUG-PORT-PARSE-01, TUI-FIX-08, TUI-FIX-09, TUI-FIX-10, GAUNTLET-FIX-LOOP-SPLIT, AUTOTUNE-FIX-01, AUTOTUNE-FIX-02, TOOL-INVOKE-MEMORY-01, TUI-POPUP-META-01, TUI-BOOT-LOG-01 |
| 26 | **VALIDATE-ONDA-21** | 2.7 Validação | ALTA | CONCLUIDA (RELATORIO_VALIDACAO_ONDA_21.md) | VALIDATE-ONDA-20 |
| 27 | **OBSERVABILITY-01** | 2.9 Integração | ALTA | CONCLUIDA (commit 691f0c5) | VALIDATE-ONDA-21 |
| 28 | **DOC-CONSOLIDATE-01** | 2.9 Integração | MÉDIA | CONCLUIDA | -- |
| 29 | **UX-DESIGN-01** | 3 Design | CRÍTICA | CONCLUIDA (commit e189f15) | AUDIT-FIX-03 |
| 30 | **UX-LAYOUT-01** | 4 Layout | ALTA | ABSORVIDA_POR_UX-LAYOUT-01A, UX-LAYOUT-01B (decisão de escopo 2026-04-19) | UX-DESIGN-01 |
| 31 | **UX-LAYOUT-01A** | 4 Layout | ALTA | CONCLUIDA (commit af0a901) | UX-DESIGN-01 |
| 32 | **UX-LAYOUT-01B** | 4 Layout | ALTA | CONCLUIDA (commit 9557d5a) | UX-LAYOUT-01A, OBSERVABILITY-01 |
| 33 | **UX-LAYOUT-02** | 4 Layout | ALTA | CONCLUIDA (commit 80a6ccc) | UX-LAYOUT-01B, OBSERVABILITY-01 |
| 34 | **UX-LAYOUT-03** | 4 Layout | ALTA | CONCLUIDA | UX-LAYOUT-02 |
| 35 | **TUI-FIX-07** | 4b Herdado | MÉDIA | ABSORVIDA_POR_TUI-FIX-07A, TUI-FIX-07B, TUI-FIX-07C (decisão de escopo 2026-04-19) | VALIDATE-ONDA-21 |
| 36 | **TUI-FIX-07A** | 4b Herdado | MÉDIA | CONCLUIDA | VALIDATE-ONDA-21 |
| 37 | **TUI-FIX-07B** | 4b Herdado | MÉDIA | CONCLUIDA | TUI-FIX-07A |
| 38 | **TUI-FIX-07C** | 4b Herdado | BAIXA | CONCLUIDA | TUI-FIX-07B |
| 39 | **UX-BUG-01** | 5 Bugs | ALTA | CONCLUIDA | UX-LAYOUT-03 |
| 40 | **ERROR-MSG-01** | 5 Bugs | ALTA | CONCLUIDA (commit 70ed36a) | UX-DESIGN-01 |
| 41 | **COMPLETER-ARGS-01** | 5 Bugs | MÉDIA | CONCLUIDA | UX-BUG-01 |
| 42 | **UX-BUG-02** | 5 Bugs | ALTA | ABSORVIDA_POR_UX-BUG-02A, UX-BUG-02B, UX-BUG-02C (decisão de escopo 2026-04-19) | UX-BUG-01 |
| 43 | **UX-BUG-02A** | 5 Bugs | ALTA | CONCLUIDA | UX-BUG-01 |
| 44 | **UX-BUG-02B** | 5 Bugs | ALTA | CONCLUIDA | UX-BUG-02A, OBSERVABILITY-01 |
| 45 | **UX-BUG-02C** | 5 Bugs | ALTA | PENDENTE | UX-BUG-02A |
| 46 | **UX-BUG-03** | 5 Bugs | ALTA | PENDENTE | UX-LAYOUT-03 |
| 47 | **VISION-01** | 6 Visão | ALTA | CONCLUIDA (ADR-022 ACEITO; VisionClient + VisionService + cache sha256; describe end-to-end 17.4s; cache hit 0.001s; gauntlet vision 3/3; render_progress_bar absorveu O-01) | UX-BUG-03, ADR-022-DOC |
| 48 | **VISION-02** | 6 Visão | ALTA | CONCLUIDA (_expand_images substitui [Image #N] inline; _shorten_description trunca 200 chars; describe_many em VisionService; /vision N lê ~/.nyx/image_index.json; _persist_image_index alimenta o índice via Ctrl+V; smoke ok + invariantes 14/14) | VISION-01 |
| 49 | **VISION-03** | 6 Visão | ALTA | CONCLUIDA (verify_vram.sh delta 0 MB com qwen quente; log "moondream em CPU puro" na 1a chamada; TimeoutError -> "[Imagem: timeout — descrição demorou demais]"; fallback URL no script 11435->11434) | VISION-02 |
| 50 | **SESSION-RESUME-01** | 6b Sessões | MÉDIA | CONCLUIDA (index.json v1 com _atomic_write; load_session_by_id por prefixo; /resume com args (list/prefixo); --resume/--no-resume-prompt em main; maybe_offer_resume TTL 48h + threshold 3 turnos + isatty guard; migrate_sessions.py idempotente; gauntlet sessao 3/3) | CTX-02 |
| 51 | **DEPLOY-01** | 7 Deploy | ALTA | ABSORVIDA_POR_DEPLOY-01A, DEPLOY-01B (decisão de escopo 2026-04-19) | VISION-03 |
| 52 | **DEPLOY-01A** | 7 Deploy | ALTA | CONCLUIDA (install.sh 230L; 10 fases [N/10]; 5 flags --no-vision/no-kitty/dev/dry-run/no-prompt; detect_pkg_manager apt-get/dnf/pacman/zypper; idempotente 2 runs diff vazio; dry-run 0 escritas; smoke import nyx.agent.loop OK) | VISION-03 |
| 53 | **DEPLOY-01B** | 7 Deploy | ALTA | CONCLUIDA (fase Gauntlet install em Docker ubuntu:22.04 real ADR-010; D-02 rc=0 em 61.5s com NYX_INSTALL_SKIP_PULL=1; README ## Instalação rápida com 5 flags e 4 distros; install.sh ganhou guard minimo NYX_INSTALL_SKIP_PULL) | DEPLOY-01A |
| 54 | **DEPLOY-02** | 7 Deploy | ALTA | PENDENTE | DEPLOY-01B |
| 55 | **ONBOARDING-01** | 7b Onboarding | MÉDIA | CONCLUIDA (onboarding.py com 5 steps + timeout 60s SIGALRM + auto-skip em pipe; --skip-onboarding flag; /config setup wizard interativo grava ~/.nyx/config.toml com backup atomico; settings.py precedencia env > toml > defaults) | SESSION-RESUME-01, HELP-EXAMPLES-01 |
| 56 | **HELP-EXAMPLES-01** | 8 Extra | BAIXA | CONCLUIDA (54/54 commands com 2-3 examples; audit_help_coverage.py; /help <cmd> renderiza descricao+exemplos+aliases com fallback fuzzy) | UX-BUG-01 |
| 57 | **UX-EXTRA-01** | 8 Extra | BAIXA | CONCLUIDA (Ctrl+Up recall via keybinding; /edit /e em session.py; app_state["prefill"] alimenta prompt_async default=; absorve O-09) | UX-BUG-01 |
| 58 | **VALIDATE-FINAL-01** | 9 Release | CRÍTICA | BLOQUEADA (aguarda DOC-CONSOLIDATE-01 + execução humana: 30 screenshots paridade, 47 commands manuais, 5 runs benchmark, install em VM Docker Ubuntu 22.04, 34 tools em fluxo natural) | UX-EXTRA-01, DEPLOY-02, ONBOARDING-01, VISION-03, DOC-CONSOLIDATE-01 |
| 59 | **PRODUCAO-CLEANUP-01** | 2.10 Higiene | ALTA | CONCLUIDA (commit 767e871) | -- |
| 60 | **INVENTORY-SYNC-01** | 2.10 Higiene | MÉDIA | CONCLUIDA (commit 3689081) | PRODUCAO-CLEANUP-01 |
| 61 | **COMPLETER-SEPS-01** | 5 Bugs | MÉDIA | CONCLUIDA (commit 920b3e6) | UX-BUG-01 |
| 62 | **TUI-CLEANUP-01** | 2.10 Higiene | BAIXA | CONCLUIDA (commit 3fd91e3) | UX-LAYOUT-02, OBSERVABILITY-01 |
| 63 | **BANNER-TOOLS-COUNT-01** | 2.10 Higiene | MÉDIA | CONCLUIDA | INVENTORY-SYNC-01 |
| 64 | **TAG-KEY-ACCENT-01** | 2.10 Higiene | BAIXA | CONCLUIDA | -- |
| 65 | **STATUS-FILTER-HARDEN-01** | 2.10 Higiene | MÉDIA | CONCLUIDA | PRODUCAO-CLEANUP-01 |
| 110 | **UX-LOOP-VISIBILITY-01** | 23.4 Gamedesigner | MÉDIA | CONCLUIDA (Estratégia A: spinner com Callable[[], str]; build_warming_label janelas 0-3s/3-10s/10s+; glifo ◐ em "aquecendo modelo..."; smoke ok + invariantes 14/14 + gauntlet rapido 18/18) | UX-BUG-02B |
| 111 | **UX-CLAUDE-PARITY-01** | 23.4 Gamedesigner | ALTA | CONCLUIDA (ADR-029; banner 9->3 linhas mantendo paleta D + glifos; toolbar separator . substituido por pipes; bypass off com prefix triangulo duplo paridade estrutural; identidade Nyx preservada) | UX-BUG-02B, UX-LOOP-VISIBILITY-01 |
| 112 | **UX-LIFECYCLE-01** | 23.1 Estabilização | ALTA | CONCLUIDA (lock file + cleanup robusto SIGINT/TERM/HUP + /admin/shutdown loopback + VRAM check pré-inferência; gauntlet rápido 18/18 em 11s) | BOOT-VRAM-GUARD-01, TUI-SHUTDOWN-SILENT-01 |
| 113 | **PERF-INFERENCE-01** | 23.0 Performance (NOVA FASE 1) | CRÍTICA | CONCLUIDA | -- |
| 114 | **MCP-SERVER-01** | 23.5 Feature parity | ALTA | CONCLUIDA (ADR-030; McpClient stdio JSON-RPC com timeouts; /mcp list/reload/test; NYX_MCP_CONFIG em defaults; boot tolerante; MCP-SERVER-02 anti-debito para ToolRegistry+HTTP+Gauntlet) | PERF-INFERENCE-01 |
| 115 | **PLUGINS-01** | 23.5 Feature parity | MÉDIA | CONCLUIDA (PluginManager com discover/load/install/uninstall + AST check anti-codigo-arbitrario; /plugin list/reload/install/uninstall; NYX_PLUGINS_DIR; PLUGIN_API.md; PLUGINS-02 anti-debito para auto-registro+Gauntlet) | MCP-SERVER-01 |
| 116 | **OUTPUT-STYLES-01** | 23.5 Feature parity | MÉDIA | CONCLUIDA (3 estilos default/concise/learning em output_style.py; build_system_prompt aceita output_style param; /output-style list/get/set; app_state["output_style"] runtime; invariantes ADR preservados em todos estilos) | PERF-INFERENCE-01 |
| 117 | **HOOKS-DYNAMIC-01** | 23.5 Feature parity | MÉDIA | CONCLUIDA (HookRuntime MVP em services/hook_runtime.py; 4 eventos PreToolUse/PostToolUse/UserPromptSubmit/Stop; matcher regex + timeout 30s/300s + block_on_failure; env whitelist; HOOKS.md; HOOKS-DYNAMIC-02 anti-debito para integracao no loop+ToolRegistry+skill bridge) | PERF-INFERENCE-01 |
| 118 | **LANG-ENFORCE-01** | 23.0 Performance | ALTA | CONCLUIDA (lang_pt_br_rate=100% com qwen2.5-coder:3b) | PERF-INFERENCE-01, MODEL-SWAP-01 |
| 119 | **SLASH-BYPASS-AUDIT-01** | 23.0 Performance | MÉDIA | CONCLUIDA (5/5 /commands com latência <500ms; fase slash_bypass nova no Gauntlet) | PERF-INFERENCE-01 |
| 120 | **WARMUP-ON-BOOT-01** | 23.0 Performance | MÉDIA | CONCLUIDA (warmup duplo via proxy adiciona ~3s ao boot; cold call P95 <=8s validada com 0.634s) | PERF-INFERENCE-01 |
| 121 | **MODEL-SWAP-01** | 23.0 Performance | ALTA | CONCLUIDA (ADR-031: qwen2.5-coder:3b padrão; score 96.8) | -- |
| 122 | **GAUNTLET-RAPIDO-FIXES-01** | 23.0 Performance | ALTA | CONCLUIDA (18/18 100% rapido; fix P-07 think gating + parser content-JSON; fix C-03 settings.json criado; fix C-04 GUIDE.md -> GSD.md) | -- |
| 124 | **INFRA-SANITIZER-FIX-01** | 23.0 Performance | MÉDIA | CONCLUIDA (hash e16e61b; 23 arquivos restaurados bit-exact; invariante #14 ativo; PASS=14/FAIL=0) | -- |
| 125 | **INFRA-SANITIZER-FIX-02** | 23.0 Performance | ALTA | CONCLUIDA (invariante #14 endurecido: grep textual -> python codepoint count; cobertura expandida para output.py; imune a strip + reescrita coerente) | INFRA-SANITIZER-FIX-01 |
| 123 | **LANG-PROMPT-ACENT-01** | 23.0 Performance | BAIXA | PENDENTE | LANG-ENFORCE-01 |

---

## Roadmap por FASES (auditoria estratégica 2026-05-16)

Reorganização proposta priorizando meta v1.0 "Claude Code offline e opensource". A coluna **FASE** define ordem de execução; sprints dentro da mesma FASE podem rodar em paralelo se não dependem entre si.

| FASE | Tema | Sprints |
|---|---|---|
| **1** | Performance (resgate de UX — bloqueia tudo) | PERF-INFERENCE-01 (CRÍTICA), UX-LIFECYCLE-01 (ALTA) |
| **2** | Base estável | BOOT-VRAM-GUARD-01, PROXY-NUMGPU-RUNTIME-01, UX-BUG-02C, UX-BUG-03, TUI-SHUTDOWN-SILENT-01, SECRET-MIGRATE-01 |
| **3** | UX paridade Claude Code | UX-CLAUDE-PARITY-01, UX-LOOP-01, UX-AGENCY-01, UX-PROGRESSION-01, UX-LOOP-VISIBILITY-01 |
| **4** | Features parity Claude Code | MCP-SERVER-01, PLUGINS-01, OUTPUT-STYLES-01, HOOKS-DYNAMIC-01 |
| **5** | Sessões + Visão + Onboarding | SESSION-RESUME-01, VISION-01, VISION-02, VISION-03, ONBOARDING-01, HELP-EXAMPLES-01, UX-EXTRA-01 |
| **6** | SBOM (observabilidade) | SBOM-REGISTRY-01, SBOM-REGISTRY-02, SBOM-REGISTRY-03 |
| **7** | Cockpit (extensão além Claude Code — opcional v1.0) | COCKPIT-01..05, UX-COCKPIT-EXPERIENCE-01 |
| **8** | Release v1.0 | DEPLOY-01A, DEPLOY-01B, DEPLOY-02, VALIDATE-FINAL-01 |

**Notas:**
- FASE 1 é gate binário: sem `oi` respondendo em <5s, qualquer outra UX é teatro.
- FASE 4 cobre os 4 gaps reais vs Claude Code identificados na auditoria (MCP, plugins, output-styles, hooks dinâmicos). Sem essas 4, "Claude Code offline" é meta-mentira.
- FASE 7 (Cockpit) é diferencial além do Claude Code; pode ser adiado para pós-v1.0 sem perda de paridade.
- 38 sprints PENDENTES totais (WARMUP-ON-BOOT-01 CONCLUIDA; LANG-PROMPT-ACENT-01 nova como achado colateral).



**Bloco 0 (Auditoria):** 1 sprint — relatório externo independente com 12 findings.

**Bloco 1 (Fundamentos rápidos):** 4 sprints paralelas resolvidas (remoção de código morto, centralização de portas, log de exceção, remoção de dir vazio).

**Bloco 2 (Fundamentos dependentes):** 6 sprints — cabeamento de `NyxSettings`, split de `commands.py` e `loop.py`, ADR-024 render layer, refactor de `ask_user`, logging unificado.

**Bloco 2.5 (Limpeza de pendências, 2026-04-19):** 8 sprints — materializa sprints que haviam ficado como débito implícito: docstring órfã, excepts residuais, higienização ruff, pre-commit local, pre-commit global (DEBT-06 desdobrada de DEBT-05 quando se descobriu que o hook executado é o global `core.hookspath`), ADR-021, ADR-022, e DEBT-07 (exports pós-split `loop.py` — resíduo de DEBT-01 exposto por INFRA-GAUNTLET-01). Regra "nenhum débito para trás".

**Bloco 2.6 (Integração — baseline limpo):** 3 sprints — INFRA-GAUNTLET-01 DESCARTADA (decisão de escopo 2026-04-19; validações visuais não exigem baseline gauntlet 100% pré-release, smoke gauntlet por fase cobre regressão pontual quando necessário), BOOT-FIX-01 CONCLUIDA (2026-04-19, commit bb3d61b — fixou `nyx/cli.py` promovendo `sys.path.insert` para antes de `from nyx.*` e adicionou check #13 ao `scripts/sprint_invariants.sh`) e BUG-PORT-PARSE-01 CONCLUIDA (2026-04-19 — estabeleceu contrato dual para `OLLAMA_HOST`: interno Nyx/Python = host puro via `NYX_OLLAMA_HOST`; daemon Ollama externo = `host:port` composto no export de `run.sh`. Separou `NYX_OLLAMA_HOST` e `NYX_OLLAMA_PORT` em `run.sh:45`, ajustou 4 call-sites internos e removeu reformat do case `--port`. Adicionou guard `ValueError` em `settings.py` e alinhou fallback em `commands/system.py`. Gauntlet rapido 11/11 APROVADO, `httpx.URL` parseia corretamente `http://127.0.0.1:11436/v1/...`).

**Bloco 2.7 (Validação das ondas 20/21):** 2 sprints — VALIDATE-ONDA-20 e VALIDATE-ONDA-21, destravando as 14 sprints em limbo. **VALIDATE-ONDA-20 ganhou deps em 2026-04-19**: BUG-PORT-PARSE-01 (CRÍTICO), TUI-FIX-08 e TUI-FIX-09 precisam concluir primeiro (achados colaterais da Rodada 1 — ver Bloco 2.6 e 2.8).

**Bloco 2.8 (Fixes Onda 20, 2026-04-19):** 2 sprints materializadas como achados colaterais de VALIDATE-ONDA-20 (Rodada 1, protocolo anti-débito). **TUI-FIX-08** (ALTA) — popup de `/` não filtra dinamicamente por prefixo (violação da especificação TUI-03 "Popup navegável"); usuário digitou `/them` e recebeu `Comando desconhecido` em vez de popup filtrado para `/theme`. **TUI-FIX-09** (MÉDIA) — comando `/theme` imprime lista de dicts Python crua (`{'id': ..., 'name': ..., 'description': ...}`) em vez de linhas formatadas (viola ADR-024 render layer e higiene definida em TUI-01). Ambas dependem de BUG-PORT-PARSE-01 para validação real no REPL.

**Bloco 2.9 (Integração — observability + docs, 2026-04-19):** 2 sprints criadas após revisão ampla do projeto. **OBSERVABILITY-01** (ALTA) — wirea callbacks `on_compaction` e `on_model_state` no `AgentLoop` (hoje inexistentes); adiciona `/debug session` e `/replay <id>`; log centralizado rotacionado. Pré-requisito para UX-LAYOUT-02 (que hoje *assume* `on_compaction` existe) e UX-BUG-02B (estado cold/warming/warm). **DOC-CONSOLIDATE-01** (MÉDIA) — reduz carga cognitiva da IA executora de ~1000 para ~400 linhas: funde catálogo universal em GAMBIARRAS, atualiza `update_next_sprint.py` para injetar recorte GAMBIARRAS no EXECUTAR_SPRINT, cria `PROJECT_SNAPSHOT.md` auto-gerado.

**Bloco 3 (Design System):** 1 sprint — tokens canônicos + ADR-023. Destrava todo o Bloco 4. **Agora pode rodar em paralelo a VALIDATE-ONDA-20/21/2.8/2.9** (só depende de AUDIT-FIX-03 já CONCLUIDA).

**Bloco 4 (Layout):** banner (LAYOUT-01A), toolbar (LAYOUT-01B, depende de OBSERVABILITY-01), cards de tool (LAYOUT-02), streaming suave (LAYOUT-03). Checkpoint visual entre cada uma. UX-LAYOUT-01 original ABSORVIDA por 01A+01B em 2026-04-19 (split: responsabilidades separadas).

**Bloco 4b (Herdado):** TUI-FIX-07 original ABSORVIDA por TUI-FIX-07A (footer + spinner ASCII + indicador memória boot), TUI-FIX-07B (paste longo + /help categorizado), TUI-FIX-07C (/memory + /paste + /tools + /recall). Split em 2026-04-19: escopo inchado de 8 critérios heterogêneos.

**Bloco 5 (Bugs TUI + mensagens):** autocomplete reativo (UX-BUG-01), ERROR-MSG-01 (auditoria de mensagens de erro em PT-BR + cor + actionable — paralelo), COMPLETER-ARGS-01 (completer de argumentos de slash commands), UX-BUG-02A/B/C (split do race input + estado warm/cold), UX-BUG-03 (perf). UX-BUG-02 original ABSORVIDA. UX-BUG-01 e UX-BUG-03 **podem rodar em paralelo** (arquivos disjuntos).

**Bloco 6 (Visão):** moondream CPU, pipeline `[Image #N]`, verificação de VRAM.

**Bloco 6b (Sessões):** SESSION-RESUME-01 (`/resume` retoma última sessão; índice em `~/.nyx/sessions/index.json`) — paralelo a VISION.

**Bloco 7 (Deploy):** DEPLOY-01A (install.sh local idempotente), DEPLOY-01B (teste Docker Ubuntu + README), DEPLOY-02 (desktop entry + ícone). DEPLOY-01 original ABSORVIDA por 01A+01B (371 linhas → 2 arquivos por responsabilidade).

**Bloco 7b (Onboarding):** ONBOARDING-01 (tutorial 30s na primeira run + `/config setup` interativo) — paralelo a DEPLOY.

**Bloco 8 (Extra):** HELP-EXAMPLES-01 (`/help <cmd>` com 2-3 exemplos reais para cada um dos 47 commands), UX-EXTRA-01 (editar último input). UX-EXTRA-01 desvinculada de DEPLOY-02 em 2026-04-19 — depende apenas de UX-BUG-01 (keybindings).

**Bloco 9 (Release gate):** VALIDATE-FINAL-01 — demo end-to-end, checklist de paridade com Claude Code CLI, smoke install em VM Docker limpa, benchmark start<1.5s, gauntlet 100%. Bloqueia tag v1.0.

**Bloco 2.10 (Higiene, 2026-04-21):** 6 sprints materializadas como achados colaterais da auditoria profunda das sprints concluídas pós-bloco 2.5 e da orquestração sequencial do mesmo dia (protocolo anti-débito, meta-regra #9). **Lote 1 (auditoria inicial):** PRODUCAO-CLEANUP-01 (4 fantasmas ABSORVIDA em `producao/` + filtro de Status em `update_next_sprint.py`), INVENTORY-SYNC-01 (três fontes de contagens divergentes — adotou 28/52/9 filesystem), COMPLETER-SEPS-01 (5º critério silenciado de UX-BUG-01 — separadores `---- [categoria] ----`), TUI-CLEANUP-01 (órfãos `render_tool_call`/`render_tool_result`/`on_compaction_log` + docstring corrigida). **Lote 2 (achados da validação do Lote 1):** BANNER-TOOLS-COUNT-01 (MÉDIA, dep INVENTORY-SYNC-01) — divergência `ToolRegistry.tool_count == 35` (runtime, banner, headless) vs `sync.py == 28` (filesystem) invalida fonte única adotada pela INVENTORY-SYNC-01; trocar `_count_tools()` para usar registry runtime + reconciliar docs + explicar origem das 7 tools extras. TAG-KEY-ACCENT-01 (BAIXA) — chaves `"sessao"`/`"metricas"` em `TAG_STYLES`/`TAG_LABELS` (pré-existentes desde `d945bcd8`, 2025-05-01) violam ADR-006; renomear para chaves acentuadas com N-para-N em call-sites `output("sessao", ...)` de cli.py. STATUS-FILTER-HARDEN-01 (MÉDIA, dep PRODUCAO-CLEANUP-01) — regex de `_read_status` em `update_next_sprint.py` pegava o primeiro `**Status:**` do arquivo, confundindo Status embedded em ADR citado (caso SPRINT_VISION_01 retornando `ACEITO`) com Status da sprint; restringir busca à região antes do heading `# Sprint <ID>`, distinguir `SEM_METADATA` de `DESCONHECIDO`, documentar contrato no SPRINT_TEMPLATE_V2. **Fix inline paralelo:** 6 arquivos em `producao/` (DEPLOY-02, UX-BUG-03, UX-EXTRA-01, VISION-01, VISION-02, VISION-03) receberam bloco metadata canônico que estava faltando — esses arquivos eram escritos antes da convenção firmar e não tinham `**Status:** PENDENTE` próprio.

---

<!-- MANUAL_OVERRIDE_ONDA_23_START -->

### Bloco ONDA-23: Cockpit + SBOM + Gamedesigner (filosofia de experiência)

**Origem:** auditoria + brainstorm do usuário em 2026-05-15. Plano: `~/.claude/plans/venv-andrefarias-nitro-5-desenvolviment-declarative-spark.md`. Onda 23 paralela à Onda 22 (não bloqueia VALIDATE-FINAL-01). 15 sprints novas em 4 blocos.

**Decisões fechadas (2026-05-15):**
- D1 Ordem paralelo: track Onda 22 segue normal; track Onda 23 começa em paralelo.
- D2 Stack Cockpit = FastAPI + WebSocket + xterm.js, bind 127.0.0.1:11437.
- D3 MVP Cockpit completo (paineis + REPL embedded + gauntlet por feature + evidência + control API).
- D4 Pilar gamedesigner = **filosofia de experiência única** (juicing/flow/agency/feedback/tutorial-sem-tutorial/onboarding-onda/progression/microcopy/identidade), não estética. Paleta D do ADR-023 serve a essa filosofia.
- D5 Princípio operacional: write-through (sem UPS — cada decisão grava antes de prosseguir).

**Bugs novos detectados e formalizados nesta onda** (não cobertos pelas 16 sprints pendentes da Onda 22):
- BOOT-VRAM-GUARD-01 (ALTA): OOM-killer mata Ollama em pré-carga em low-VRAM.
- PROXY-NUMGPU-RUNTIME-01 (MÉDIA): `NUM_GPU` módulo-global; sem re-tune proativo.
- TUI-SHUTDOWN-SILENT-01 (BAIXA): "Morto" do bash vaza no terminal por SIGKILL em filho `&`.
- SECRET-MIGRATE-01 (BAIXA): `ANTHROPIC_API_KEY` em `.env` (mitigado por .gitignore; mover para `~/.config/nyx/secrets`).

| # | Sprint | Bloco | Prioridade | Status | Depende de |
|---|--------|-------|------------|--------|------------|
| 99 | **GUIDE-RENAME-FINISH-01** | 23.0 Recuperação | ALTA | CONCLUIDA | -- |
| 100 | **BOOT-VRAM-GUARD-01** | 23.1 Estabilização | ALTA | CONCLUIDA (re-tune VRAM live + disown nos background; smoke + gauntlet infra/rapido 100%) | -- |
| 101 | **PROXY-NUMGPU-RUNTIME-01** | 23.1 Estabilização | MÉDIA | PENDENTE | BOOT-VRAM-GUARD-01 |
| 102 | **TUI-SHUTDOWN-SILENT-01** | 23.1 Estabilização | BAIXA | PENDENTE | -- |
| 103 | **SECRET-MIGRATE-01** | 23.1 Estabilização | BAIXA | PENDENTE | -- |
| 104 | **SBOM-REGISTRY-01** | 23.2 SBOM | ALTA | PENDENTE | -- |
| 105 | **SBOM-REGISTRY-02** | 23.2 SBOM | ALTA | PENDENTE | SBOM-REGISTRY-01 |
| 106 | **SBOM-REGISTRY-03** | 23.2 SBOM | MÉDIA | PENDENTE | SBOM-REGISTRY-02 |
| 107 | **COCKPIT-01** | 23.3 Cockpit | ALTA | PENDENTE | BOOT-VRAM-GUARD-01, SBOM-REGISTRY-02 |
| 108 | **COCKPIT-02** | 23.3 Cockpit | ALTA | PENDENTE | COCKPIT-01 |
| 109 | **COCKPIT-03** | 23.3 Cockpit | ALTA | PENDENTE | COCKPIT-02 |
| 110 | **COCKPIT-04** | 23.3 Cockpit | MÉDIA | PENDENTE | COCKPIT-03 |
| 111 | **COCKPIT-05** | 23.3 Cockpit | MÉDIA | PENDENTE | COCKPIT-04 |
| 112 | **UX-LOOP-01** | 23.4 Gamedesigner | ALTA | PENDENTE | ADR-023 |
| 113 | **UX-AGENCY-01** | 23.4 Gamedesigner | ALTA | PENDENTE | UX-LOOP-01 |
| 114 | **UX-PROGRESSION-01** | 23.4 Gamedesigner | MÉDIA | PENDENTE | UX-LOOP-01 |
| 115 | **UX-COCKPIT-EXPERIENCE-01** | 23.4 Gamedesigner | MÉDIA | PENDENTE | COCKPIT-03, UX-LOOP-01, UX-AGENCY-01 |

**Bloco 23.0 (Recuperação de débito, 2026-05-15):** 1 sprint — GUIDE-RENAME-FINISH-01 fecha trabalho não-commitado deixado por sessão IA anterior (rename CLAUDE.md → GUIDE.md, ~45 arquivos com modificações prontas + 2 funções com nome legado em prompt.py e update_docs.py). Origem: freezy.

**Bloco 23.1 (Estabilização cirúrgica):** 4 sprints. Resolve achados de runtime observados em 2026-05-15 ao rodar `./run.sh`. Pré-requisito de COCKPIT (Cockpit precisa boot confiável).

**Bloco 23.2 (SBOM Registry vivo):** 3 sprints. Estende `FEATURE_MAP.md` para `REGISTRY.yaml` machine-readable; Gauntlet alimenta com status/evidência/timestamp; features sem teste viram sprint stub. Hoje 18/62 cobertas; meta <10 sem teste.

**Bloco 23.3 (Web Cockpit):** 5 sprints. Servidor local FastAPI em :11437 com REPL embedded via PTY, dashboard de features, captura de evidência e control API. Permite Claude pilotar via Chrome MCP.

**Bloco 23.4 (Pilar gamedesigner — filosofia):** 4 sprints. Materializa 4 princípios canônicos como ADRs (025 Loop, 026 Agência, 027 Progressão & Identidade) aplicados ao loop Nyx; sprint final garante coerência TUI↔Web. **Após UX-LOOP-01, toda sprint Onda 22 e Onda 23 passa a ter critério de aceite "princípios do ADR-025 aplicados".**

**Status: PENDENTE.** Specs serão criadas em `producao/` na sequência da Semana 1 do plano. Promoção para PENDENTE só após review.

<!-- MANUAL_OVERRIDE_ONDA_23_END -->

---

## Ordem de Execução

```
Ondas 1-9 (Concluídas):     G, D, F, P, P2, P3, I-01, P4, P5, P6, P8

Onda 10 (INFRA -- OBRIGATÓRIA ANTES DE TUDO):
  INFRA-01 (scaffold) -> INFRA-02 (gauntlet coverage) -> INFRA-03 (sync enhanced)

Onda 11 (Interface):         P7-A -> P7-B -> P7-C
Onda 12 (Tools):             P9-A -> P9-B
Onda 13 (Commands lote 1):   P10-A, P10-B, P10-C (paralelo) -> P10-D, P10-E (paralelo)
Onda 14 (Commands lote 2):   P10-F, P10-G (paralelo) -> P10-H, P10-I (paralelo) -> P10-J
Onda 15 (Services lote 1):   P11-A, P11-B (paralelo) -> P11-C, P11-D (paralelo)
Onda 16 (Services lote 2):   P11-E, P11-F (paralelo) -> P11-G

Onda 17 (AUDITORIA -- PÓS-PORT):
  AUDIT-01 (segurança), AUDIT-03 (sincronização) -> AUDIT-02 (integração), AUDIT-04 (qualidade)
  AUDIT-04 -> AUDIT-05 (performance) -> AUDIT-06 (robustez)

Onda 18 (PORTABILIDADE -- antes de rodar em máquina nova):
  PORT-01 (auto-tune GPU) -> PORT-02 (Docker clean boot) -> PORT-03 (robustez boot)

Onda 19 (INTEGRAÇÃO LUNA -- substituir code agent antigo):
  I-02 (substituir nyx antiga) -> I-03 (mensagens inline [nyx])

Onda 20 (TUI+CTX -- redesign UX/UI + sistema de contexto) -- EM VALIDAÇÃO:
  TUI-01 (higiene) -> TUI-02b (boxes+multiline) -> TUI-03 (footer+popup)
  PROMPT-01 (anti-agressivo) [fora do bloco mas no mesmo commit]
  [CHECKPOINT visual com usuário -- PENDENTE]
  CTX-01 (summarizer) -> CTX-02 (memory) -> CTX-03 (repomap)
  CTX-04 (plano ativo) -- deferido

Onda 21 (TUI-FIX -- correções pós-validação visual):
  TUI-FIX-01 (banner) -> TUI-FIX-02 (streaming) -> TUI-FIX-03 (slash popup)
  TUI-FIX-04 (bypass toggle) -> TUI-FIX-05 (image paste) -> TUI-FIX-06 (sandbox msg)
  TUI-FIX-07 (usabilidade geral -- depende de FIX-02 e FIX-06)

Onda 22 (Redesign Total UX + Visão + Deploy) -- EM EXECUÇÃO:
  Bloco 0: AUDIT-EXT-01 (auditoria externa) -- CONCLUIDA
  Bloco 1: AUDIT-FIX-01, -03, -04, DEBT-02 (paralelos, rápidos) -- CONCLUIDA
  Bloco 2: AUDIT-FIX-02 (dep 03), -05, -06, -07, DEBT-01, DEBT-03 -- CONCLUIDA (2026-04-18)
  Bloco 2.5 (2026-04-19): AUDIT-FIX-08, -09, DEBT-04, DEBT-05 (BLOQUEADA por DEBT-06), DEBT-06, ADR-021-DOC, ADR-022-DOC (paralelos)
  Bloco 2.6 (Integração): INFRA-GAUNTLET-01 DESCARTADA + BOOT-FIX-01 CONCLUIDA + BUG-PORT-PARSE-01 CONCLUIDA (contrato dual OLLAMA_HOST, 2026-04-19)
  Bloco 2.8 (Fixes Onda 20): TUI-FIX-08 (popup sem filtro por prefixo) + TUI-FIX-09 (/theme imprime dict cru)
  Bloco 2.7: VALIDATE-ONDA-20 -> VALIDATE-ONDA-21 (destrava 14 sprints em limbo)
  Bloco 3: UX-DESIGN-01 (tokens + ADR-023)
  Bloco 4: UX-LAYOUT-01 -> -02 -> -03 (checkpoint visual entre cada)
  Bloco 5: UX-BUG-01 -> -02 -> -03
  Bloco 6: VISION-01 -> -02 -> -03
  Bloco 7: DEPLOY-01 -> DEPLOY-02
  Bloco 8: UX-EXTRA-01 (opcional se sobrar tempo)
  [CHECKPOINT final: demo interativa com install.sh em VM limpa + ícone no launcher]

Onda 23 (Cockpit + SBOM + Gamedesigner) -- PARALELA A ONDA 22 (2026-05-15):
  Bloco 23.1 (Estabilização): BOOT-VRAM-GUARD-01 (ALTA), TUI-SHUTDOWN-SILENT-01 (BAIXA) [paralelos] -> PROXY-NUMGPU-RUNTIME-01 (MÉDIA), SECRET-MIGRATE-01 (BAIXA) [paralelos]
  Bloco 23.2 (SBOM): SBOM-REGISTRY-01 (ALTA) -> SBOM-REGISTRY-02 (ALTA) -> SBOM-REGISTRY-03 (MÉDIA)
  Bloco 23.3 (Cockpit): COCKPIT-01 (ALTA) -> COCKPIT-02 (ALTA) -> COCKPIT-03 (ALTA) -> COCKPIT-04 (MÉDIA) -> COCKPIT-05 (MÉDIA)
  Bloco 23.4 (Gamedesigner - filosofia): UX-LOOP-01 (ALTA, ADR-025) -> UX-AGENCY-01 (ALTA, ADR-026) [paralelo] -> UX-PROGRESSION-01 (MÉDIA, ADR-027) -> UX-COCKPIT-EXPERIENCE-01 (MÉDIA)
  [Após UX-LOOP-01: critério "ADR-025 aplicado" vira invariante em toda sprint Onda 22 e 23]
  [Integração: VALIDATE-FINAL-01 ganha critério extra "Cockpit demonstrado via Chrome MCP screenshot"]
```

**REGRA: Onda 10 (INFRA) é pré-requisito para TODAS as ondas seguintes.**
Após INFRA, toda sprint usa scaffold.py. Gauntlet valida completude automaticamente.

**Cada sprint inclui testes no Gauntlet. Sprint só é CONCLUÍDA quando Gauntlet valida.**

## Projeção de testes

| Onda | Conteúdo | Testes novos | Total |
|------|---------|-------------|-------|
| 1-9 (atual) | Core completo | -- | 135 |
| 10 (INFRA) | scaffold + coverage + sync | +14 | 149 |
| 11 (P7) | Interface TUI | +6 | 155 |
| 12 (P9) | Tools restantes | +12 | 167 |
| 13 (P10 lote 1) | Commands auth+projeto+UI+debug+plat | +35 | 202 |
| 14 (P10 lote 2) | Commands lifecycle+limites+mem+avanç+root | +29 | 231 |
| 15 (P11 lote 1) | Services infra+auth+plugins+sync | +16 | 247 |
| 16 (P11 lote 2) | Services conteúdo+protocolo+voz | +12 | 259 |
| 17 (AUDIT) | Segurança+sync+integração+qualidade+perf+robustez | +26 | 285 |
| 18 (PORT) | Auto-tune+Docker+robustez boot | +8 | 293 |
| 19 (LUNA) | Substituição nyx antiga + mensagens inline | +5 | 298 |
| 20 (TUI+CTX) | Redesign TUI + summarizer + memory + repomap (+ plano opcional) | +18 | 316 |
| 22 (ONDA-22) | Auditoria + fundamentos + redesign + visão + deploy | +24 | 340 |
| **FINAL** | **100% + portabilidade + Luna + TUI pro + contexto + visão + install** | | **340 testes** |

---

*"Um plano sem execução é uma alucinação." -- Thomas Edison*
