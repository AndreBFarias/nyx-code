# Project Snapshot — Nyx-Code

**Atualizado em:** 2026-05-21 (retomada da sessão pós-rc1 — backlog zerado)
**Versão do projeto:** **v1.3.0 ready** (Ondas 22-28 concluídas + 5 anti-débitos drenados)
**Tag v1.0 status:** NÃO cortada (decisão delegada ao humano — sprint `RELEASE-V1.0-CUT-01` PENDENTE)

**Este arquivo é referenciável por qualquer sprint** em vez de copiar o estado inline. Atualizar com regularidade (após fim de bloco, ou quando contagens mudarem).

---

## Estado v1.3.0-rc2 (2026-05-21 — retomada pós-rc1)

| Critério gate v1.0 (16 itens) | Status |
|---|---|
| 0 RASCUNHO em `producao/` | OK (só `RELEASE-V1.0-CUT-01` que aguarda humano) |
| 0 PENDENTE no MASTER (exceto RELEASE-V1.0-CUT-01) | OK — backlog completamente drenado em 2026-05-21 (10 sprints CONCLUIDA: 125qq/rr/ss/ww/oo/tt/vv/xx/yy + housekeeping; 1 SUPERSEDED: 125uu; 1 DESCARTADA: 125pp; 3 CONSOLIDADAS: 125ll/mm/nn; 1 DEFERIDA: 125zz INFRA-COMMIT-HOOK-FILTER-01 escopo externo) |
| 0 CONCLUIDA_PARCIAL com pendência ativa | OK |
| 0 DEFERIDA bloqueante | OK |
| Smoke `boot ok` | OK |
| Invariantes 14/14 PASS | OK |
| Gauntlet completo 100% | OK 225/225 em 252s (2026-05-21 rc1); proxy 7/7 + qualidade 5/5 re-validados pelos validadores na rc2 |
| `audit_help_coverage.py` N/N | OK 67/67 |
| `microcopy_audit.py --check` exit 0 | OK |
| `validar-acentuacao.py --paths` exit 0 | OK em arquivos modificados |
| `ruff check nyx/ scripts/` exit 0 | OK All checks passed (warnings cosméticos noqa-acento neutralizados por external em pyproject.toml desde 3727cb6) |
| `sbom_sync.py --check` exit 0 | OK |
| `CHANGELOG.md` cobre Ondas 22-28 | OK [1.3.0-rc1] + [1.3.0-rc2] backlog drenado |
| `PROJECT_SNAPSHOT.md` atualizado | OK (este) |
| `README.md` contagens corretas | OK via update_docs.py (35 tools, 67 commands) |
| `git status` clean | OK (Checkpoint.md untracked por design) |

---

## Stack

| Componente | Valor |
|-----------|-------|
| Python | 3.10+ |
| LLM principal | `qwen2.5-coder:3b` via Ollama |
| LLM visão | `moondream` via Ollama CPU (num_gpu=0, pendente VISION-01) |
| Proxy | porta 11436 (think adaptativo, ADR-002) |
| Ollama | porta 11435 |
| TUI | prompt_toolkit ≥ 3 |
| Testes | Gauntlet (ADR-014, sem pytest solto) |
| Modelos em runtime | 1 único momento: qwen3 quente; moondream CPU é on-demand |

Fonte única de portas/URLs: `nyx/config/defaults.py` (ADR-AUDIT-FIX-03).

---

## Contagens (verificadas em 2026-05-21, pós gauntlet 225/225)

Fonte de verdade executável: `python scripts/sync.py` imprime
`inventario: tools=N, commands_unicos=M, services=S` na primeira linha.
Também via `./run.sh --gauntlet` final summary block.

Contagem de tools é **runtime** (ToolRegistry), não filesystem. Arquivos como
`task_manager.py` (6 tools), `plan_mode.py` (2) e `worktree.py` (2) exportam
múltiplas tools por arquivo; a autoridade é o registry, que é o que o REPL
consome e o que o LLM recebe em `tool_defs`.

| Categoria | Quantidade | Como verificar |
|----------|------------|----------------|
| Tools no registry (runtime) | 35 | `python -c "from nyx.agent.tools.registry import ToolRegistry; print(ToolRegistry('.').tool_count)"` |
| Commands únicos (sem aliases) | 67 | runtime via `list_commands()` |
| Services | 15 | `find nyx/agent/services -maxdepth 1 -name '*.py' ! -name '__init__.py' \| wc -l` |
| ADRs vigentes | 31 | `ls dev-journey/03-decisions/ADR_*.md \| wc -l` |
| Testes no Gauntlet | 320 (catalogados) | `./run.sh --gauntlet` |
| Sprints concluídas | 455 | `ls dev-journey/06-sprints/concluidos/*.md \| wc -l` |
| Sprints pendentes | APENAS RELEASE-V1.0-CUT-01 (humano corta tag) — backlog técnico ZERADO | `ls dev-journey/06-sprints/producao/*.md \| wc -l` |

---

## Diretórios de estado do usuário

| Caminho | Conteúdo |
|---------|----------|
| `~/.nyx/` | root de estado |
| `~/.nyx/memory/` | memória cross-session (CTX-02) |
| `~/.nyx/sessions/` | sessões salvas (JSON por sessão) |
| `~/.nyx/sessions/index.json` | índice de sessões (pós SESSION-RESUME-01) |
| `~/.nyx/pastes/` | imagens coladas via Ctrl+V |
| `~/.nyx/image_index.json` | mapa `[Image #N]` → path (pós VISION-02) |
| `~/.nyx/vision_cache/` | descrições de imagens por sha256 (pós VISION-01) |
| `~/.nyx/logs/nyx.log` | log central rotacionado (pós OBSERVABILITY-01) |
| `~/.nyx/config.toml` | preferências do usuário (pós ONBOARDING-01) |
| `~/.nyx/.first_run_done` | flag de primeiro boot (pós ONBOARDING-01) |
| `~/.nyx/todos.json` | lista de tarefas da sessão (TodoWrite tool) |

---

## Diretórios do código

| Caminho | Papel |
|---------|-------|
| `nyx/cli.py` | REPL, banner, toolbar, keybindings. `print()` permitido aqui. |
| `nyx/agent/output.py` | render layer. `print()` permitido aqui (ADR-024). |
| `nyx/agent/loop/` | AgentLoop, iteração, constantes, tipos. |
| `nyx/agent/commands/` | 67 commands únicos (sem aliases) split em arquivos por categoria. |
| `nyx/agent/tools/` | 31 arquivos, 35 tools no registry (runtime). |
| `nyx/agent/services/` | 15 services (memory, summary, logging, vision, etc). |
| `nyx/themes/` | ThemeManager + `design_tokens.py` (pós UX-DESIGN-01). |
| `nyx/providers/` | clientes HTTP (ollama, vision). |
| `nyx/config/` | defaults, settings (NyxSettings). |
| `nyx/context/` | RepoMap, project context. |
| `nyx/integration/` | headless, protocolo JSON. |
| `scripts/` | gauntlet, invariants, scaffold, update_next_sprint, etc. |

---

## Regras invioláveis (resumo)

1. **Local First** (ADR-001): tudo offline.
2. **Zero emoji** em código, commit, doc, resposta (ADR-004).
3. **Anonimato**: sem menção a Claude/Anthropic/GPT/Gemini/Copilot (ADR-005). <!-- noqa-anonimato -->
4. **PT-BR com acentuação** (ADR-006): nunca "funcao", sempre "função". <!-- noqa-acento -->
5. **Render layer** (ADR-024): `print()` só em `cli.py` e `output.py`.
6. **Portas** só em `nyx/config/defaults.py` (invariant #5).
7. **Hex de cor** só em `nyx/themes/design_tokens.py` (invariant #6, ativo desde UX-DESIGN-01).
8. **Integração obrigatória** (ADR-013): tool no registry, command em commands.py, service importável.
9. **Testes via Gauntlet** (ADR-014): sem pytest/unittest solto.
10. **Proof-of-work**: `bash scripts/sprint_invariants.sh` antes e depois, `FAIL_AFTER <= FAIL_BEFORE`.

---

## Callbacks da TUI (contrato AgentLoop → cli.py)

Estado dos callbacks observacionais (atualizado conforme sprints):

| Callback | Status | Sprint que implementa |
|----------|--------|----------------------|
| `on_token(token: str)` | IMPLEMENTADO | — (pré-Onda 22) |
| `on_tool(name: str, args: dict)` | IMPLEMENTADO | — |
| `on_tool_result(name: str, result: str)` | IMPLEMENTADO | — |
| `on_permission(tool, args)` | IMPLEMENTADO | — |
| `on_compaction(level, tokens_removed, pct_before, pct_after)` | IMPLEMENTADO | OBSERVABILITY-01 + UX-LAYOUT-02 |
| `on_model_state(state: str)` | IMPLEMENTADO | OBSERVABILITY-01 |

---

## Scripts utilitários

| Script | Função |
|--------|--------|
| `./run.sh` | sobe Ollama + Proxy + CLI |
| `./run.sh --smoke` | imports OK (imprime "boot ok", check #13) |
| `./run.sh --headless` | protocolo JSON stdin/stdout |
| `./run.sh --gauntlet` | gauntlet completo |
| `./run.sh --gauntlet --only <fase>` | fase específica |
| `bash scripts/sprint_invariants.sh` | 14 checks binários |
| `python scripts/update_next_sprint.py` | auto-atualiza EXECUTAR_SPRINT.md |
| `python scripts/scaffold.py` | cria tool/command/service novo |
| `python scripts/sync.py` | consistência N-para-N |
| `python scripts/detect_gpu.py` | num_gpu automático |

---

## Fluxo de sprint (resumo em 10 passos)

Ver detalhes em `GSD.md §Fluxo completo de uma sprint`.

```
1. cat EXECUTAR_SPRINT.md              → pega ID da próxima PENDENTE + prompt
2. Session nova de Claude Opus 4.7     → cola o prompt <!-- noqa-anonimato -->
3. Executora lê sprint + GAMBIARRAS    → plano apresentado ao usuário
4. bash scripts/sprint_invariants.sh   → FAIL_BEFORE registrado
5. Implementa seguindo o arquivo       → código + testes no Gauntlet
6. ./run.sh --gauntlet --only <fase>   → valida
7. bash scripts/sprint_invariants.sh   → FAIL_AFTER <= FAIL_BEFORE
8. git commit + git mv producao→concluidos
9. python scripts/update_next_sprint.py
10. Reviewer valida conforme REVIEWER_PROTOCOL.md
```

---

## Ondas em execução

- **Onda 22** (em execução): redesign UX + visão + deploy. ~38 sprints, 10 concluídas.
  - Bloco 0: AUDIT-EXT-01 (auditoria externa) — CONCLUIDO.
  - Bloco 1-2.6: Fundamentos + limpeza + integração — CONCLUIDO.
  - Bloco 2.7: validação ondas 20/21 — EM EXECUÇÃO.
  - Bloco 2.8: fixes colaterais — PENDENTE.
  - Bloco 2.9: observability + doc consolidate — PENDENTE (criado 2026-04-19).
  - Bloco 3: design system — PENDENTE (pode paralelizar com 2.7).
  - Blocos 4-8: layout, bugs, visão, deploy, extra — PENDENTE.
  - Bloco 9: VALIDATE-FINAL-01 — PENDENTE (release gate).

---

*"Um snapshot é um contrato temporal: 'este estado foi verdade nesta data'." -- anônimo*
