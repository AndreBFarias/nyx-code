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

## Inventário: Nyx Python (pós-limpeza PROD 2026-04-09)

| Componente | Nyx (atual) | Nota |
|-----------|------------|------|
| Tools | 34 | Todas funcionais |
| Commands | 47 | Todos funcionais (27 stubs cloud removidos) |
| Services | 10 | Todos funcionais (11 stubs cloud removidos) |
| Testes | 135 | Gauntlet atualizado para testar funcionalidade real |

**Nota:** Port 1:1 do OpenClaude abandonado. Foco em funcionalidade local-first.
Features cloud/enterprise (voice, mobile, chrome, plugins, rate-limit, etc) não se aplicam.

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

## Backlog

Vazio. I-02 e I-03 movidas para produção (Onda 19).

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
| **FINAL** | **100% + portabilidade + Luna integrada** | | **298 testes** |

---

*"Um plano sem execução é uma alucinação." -- Thomas Edison*
