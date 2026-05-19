# Checkpoint — sessão 2026-05-18 (Validador/Integrador/Despachador)

> Working state. Write-through. Atualizado a cada step. **NÃO commitar** (untracked).

---

## Retomada de emergência

Em caso de sessão Claude cair, próxima sessão Claude deve:

1. `cd /home/andrefarias/Desenvolvimento/Nyx-Code`
2. `cat Checkpoint.md` (este arquivo) — ler seção "Linha de retomada"
3. `tmux ls` — ver sessões persistidas (`ollama`, `cockpit`, etc.)
4. `git log --oneline -10` — últimos commits desta sessão
5. `cat EXECUTAR_SPRINT.md | head -5` — próxima sprint PENDENTE
6. Ler `~/.claude/plans/prompt-validador-integrador-md-leia-estu-starry-charm.md` — plano canônico
7. Continuar de onde parou.

---

## Linha de retomada (sempre atualizada)

- **Fase atual:** **Onda 28 FECHADA (2026-05-19).** 28-09 CONCLUIDA — retoque visual pós-validação Onda 28. Banner `_build_wide()` reescrito como grid 2-col (inner_w=70, left_w=18, right_w=51); junções `┬├┤┴` em accent, pipes internos `│` em muted, rótulos CAPS (MODELO, PROJETO, TOOLS, COMANDOS, MEMÓRIA), "MEMÓRIA ativa" fixo. `_build_compact()` preservado. `nyx/cli.py` migrou completion-menu para `bg:default` (preserva `.current` com `bg:{accent}`). `run.sh` removeu echo do endmark `─── Sessão Iniciada ───` (token preservado em `design_tokens.py`). Screenshot kitty arquivado em `dev-journey/07-reports/proofs/TUI_28_RETOQUE/tui_banner_28_09_VALIDADO.png` (sha256 `69c17b39...`). **Anterior 28-08 CONCLUIDA** em 4 commits atômicos com 28_08c_PARTE_2 DEFERIDA.
- **Último commit:** `fc80d06 feat(TUI-REDESIGN-28-09)`. Anteriores: `2187b3f chore(MASTER)`, `339fea5 chore(TUI-REDESIGN-28-09)`, `22d5719 test(TUI-REDESIGN-28-08d)`.
- **Próxima ação:** Onda 28 conclui. Próximas frentes possíveis: 28-08c-PARTE-2 (switch runtime Application/PromptSession) ou ondas seguintes (12 sprints anti-débito em `producao/`).
- **Estado runtime final:** smoke=`boot ok` | invariantes=14/14 | sbom=62/62 | gauntlet rapido=11/11 APROVADO | benchmark P50=0.14s | cockpit 13 endpoints HTTP + 2 WS + dashboard 62 cards | --menu/--web/--auto-approve flags ativas
- **tmux sessões persistidas:** `cockpit` (porta 11437; pode reaproveitar via `tmux attach -t cockpit`)
- **12 sprints anti-débito pendentes em `producao/`** (a próxima sessão pode dispatch executor-sprint em paralelo):
  - NYX-AUTO-APPROVE-01 (ALTA) — destrava automação via PTY
  - PTY-PERMISSION-FLOW-01 (MÉDIA) — UI cockpit aprovar
  - COCKPIT-LIFECYCLE-FIX-01 (ALTA) — evita cascata de kill
  - NYX-NO-HALLUCINATE-TOOL-01 (ALTA) — validator anti-alucinação
  - HELP-COVERAGE-FIX-02 (BAIXA) — /aesthetic com 3 exemplos
  - PROJECT-ROOTS-MULTI-01 (ALTA) — múltiplos project roots + /sandbox + /cd
  - SHIFT-TAB-CYCLE-01 (ALTA) — shift+tab cicla normal/plan/sudo/bypass
  - SUDO-MODE-01 (ALTA) — sudo cacheado na sessão (não disco)
  - NYX-GSD-CHECKPOINTS-01 (ALTA) — progress.md write-through por sessão
  - NYX-PROMPT-REINJECT-01 (ALTA) — system-reminder periódico anti-drift
  - NYX-OUTPUT-LIMITS-01 (ALTA) — num_predict adaptativo por intent
  - VALIDATE-FINAL-01-PARTE-2 (CRÍTICA, humana) — screenshots/Docker/47cmds
- **TaskList:** Todas as 14 tasks completed. Task #9 (Fase I) ainda PENDING formal.

---

## ANEXO — Prompt para continuação em Claude Code

Cole o bloco abaixo como primeira mensagem em uma sessão nova de Claude Opus 4.7
(modelo `claude-opus-4-7`) com pwd em `/home/andrefarias/Desenvolvimento/Nyx-Code`:

```text
Voce assume os papeis Validador / Integrador / Despachador no projeto Nyx-Code.
Modelo obrigatorio: claude-opus-4-7. SEM emoji em codigo/commits/docs/respostas.
PT-BR acentuado em tudo user-facing. ADR-005: sem mencao a IA externa.

Estado herdado (sessao 2026-05-18, 17+ commits, 24+ sprints CONCLUIDAS):
- smoke ok, invariantes 14/14, sbom 62/62
- cockpit operacional em 127.0.0.1:11437 (HTTP + WS + dashboard 62 cards)
- 6 sprints anti-debito em `dev-journey/06-sprints/producao/` aguardando execucao
- novas flags em run.sh: --menu (wizard), --web (cockpit + browser), --auto-approve
- 51 RASCUNHOs em producao/ (categorias T/Q/K/V/C/R + remainders)
- 14 sprints PENDENTES nao-RASCUNHO (varias da Onda 22/23)

Leia em ordem:
1. cat Checkpoint.md (este arquivo)
2. cat PROMPT_VALIDADOR_INTEGRADOR.md
3. cat EXECUTAR_SPRINT.md
4. ls dev-journey/06-sprints/producao/ | grep -v FEAT
5. bash scripts/sprint_invariants.sh | tail -5
6. ./run.sh --smoke

Em seguida, escolha um dos caminhos:

CAMINHO A -- "completar a sessao anterior":
  Dispatch 3 executor-sprint em paralelo (run_in_background=true):
    - NYX-AUTO-APPROVE-01    (ALTA, destrava automacao)
    - COCKPIT-LIFECYCLE-FIX-01 (ALTA, evita cascata kill)
    - NYX-NO-HALLUCINATE-TOOL-01 (ALTA, confianca)
  Quando os 3 completarem, dispatch PTY-PERMISSION-FLOW-01 +
  HELP-COVERAGE-FIX-02 em paralelo.

CAMINHO A2 -- "escopo expandido (multi-projeto + sudo)":
  Dispatch 3 executor-sprint em ordem (algumas com dependencia):
    1. PROJECT-ROOTS-MULTI-01 (independente, comeca primeiro)
    2. SUDO-MODE-01 (sem UX -- pode ir paralelo com 1)
    3. SHIFT-TAB-CYCLE-01 (depois das 2 acima -- integra UX dos 4 modos)
  Tras a Nyx para projetos reais: cross-repo + sudo cacheado.

CAMINHO A3 -- "robustez de contexto (GSD + reinject + outputs longos)":
  Dispatch 3 executor-sprint em ordem:
    1. NYX-GSD-CHECKPOINTS-01 (progress.md write-through; base de tudo)
    2. NYX-OUTPUT-LIMITS-01 (num_predict adaptativo; pode paralelo com 1)
    3. NYX-PROMPT-REINJECT-01 (depende de GSD-CHECKPOINTS pra ler historico)
  Faz a Nyx aguentar tarefas longas sem perder a meta nem truncar resposta.

CAMINHO B -- "Fase I do plano original":
  Rodar INFRA-MODEL-AGNOSTIC-01 (compara qwen3:4b vs qwen2.5-coder:3b
  com mesma infra Nyx). Gera relatorio em
  dev-journey/07-reports/RELATORIO_INFRA_RESILIENTE_MODELO_01.md.

CAMINHO C -- "Validate final para tag v1.0":
  Executar VALIDATE-FINAL-01-PARTE-2 via cockpit Control API:
    1. ./run.sh --web --auto-approve (sobe cockpit + auto-approve)
    2. Para cada feature in REGISTRY.yaml: POST /control/feature/{id}/run + poll
    3. POST /api/screenshot a cada teste relevante (30 screenshots)
    4. docker run ubuntu:22.04 + ./install.sh em VM limpa
    5. Atualizar RELATORIO_VALIDATE_FINAL_01.md + CHECKLIST_PARIDADE_CLAUDE_CODE.md
    6. git tag -a v1.0 + git push origin v1.0

CAMINHO D -- "promocao acelerada dos 51 RASCUNHOs":
  Rodar `./run.sh --gauntlet` (completo, ~10 min) + script Python que itera
  producao/SPRINT_FEAT_*.md e move pra concluidos/ os que aparecem como [OK]
  no gauntlet output. Espelha o que fez SBOM-PROMOTE-IP (commit 1c5d264) mas
  com cobertura completa, nao so 'rapido'.

Recomendacao: CAMINHO A (anti-debitos primeiro -- desbloqueia C).

Cadencia obrigatoria por sprint (memoria feedback_smoke_boot.md +
feedback_write_through_apagao.md):
  pre  -> ./run.sh --smoke + bash scripts/sprint_invariants.sh > /tmp/inv_before.txt
  impl -> Edit/Write cirurgico
  pos  -> smoke + invariantes; FAIL_AFTER <= FAIL_BEFORE
  log  -> atualizar Checkpoint.md (entry [hh:mm] sprint <ID> CONCLUIDA hash)
  move -> producao/ -> concluidos/
  next -> ./venv/bin/python scripts/update_next_sprint.py
  commit -> 1-2 atomicos: 'feat(<ID>): descricao' SEM emoji
  push  -> origin main; sem --force, sem --no-verify

Anti-debito rigoroso: achado colateral durante exec vira sprint NOVA
com ID enumerado em producao/. Nunca absorver implicitamente.

Aja.
```

Fim do anexo.

## Mensagens do usuário recebidas durante a sessão

- [01:38] "tome todas as decisões que precisar tomar. Vc é autosuficiente. Pense em qualidade sempre. A ideia é concluirmos tudo. Faça o que tiver de fazer. Confio em você."
- [01:38] "O pc é seu."

→ Autonomia total confirmada. Decisões D1-D9 do plano canônico ficam vinculantes.

---

## Histórico desta sessão (append-only, ordem cronológica)

- [2026-05-18 01:38] Sessão Claude Opus 4.7 iniciada na raiz `/home/andrefarias/Desenvolvimento/Nyx-Code`.
- [2026-05-18 01:38] Plano canônico gravado em `~/.claude/plans/prompt-validador-integrador-md-leia-estu-starry-charm.md` (14 seções, 9 fases A-I).
- [2026-05-18 01:38] Plano aprovado via ExitPlanMode com 11 categorias de permissão Bash (smoke, git, tmux, run.sh, scrot, vendor npm, Docker, curl, edição docs, pkill, sudo via env).
- [2026-05-18 01:38] Checkpoint.md anterior renomeado para `Checkpoint_2026_05_17.md.bkp` (backup local; untracked).
- [2026-05-18 01:38] Diretório `dev-journey/07-reports/proofs/` criado.
- [2026-05-18 01:38] Checkpoint.md (este) inicializado. Próximo: baseline runtime via sanity checks paralelos.
- [2026-05-18 01:39] A1 baseline gravado em `dev-journey/07-reports/proofs/A1_baseline/`: smoke=boot ok, invariantes=14/14, sbom=62/62, executar_sprint=vazio, help_coverage=59/60 (1 falta).
- [2026-05-18 01:39] Achado colateral A1: `/?` tem 1 exemplo (mínimo 2). Materializa como sprint `HELP-COVERAGE-FIX-01` na Fase A (anti-débito).
- [2026-05-18 01:39] TaskList criada: 9 tasks (Fases A-I). Task #1 IN_PROGRESS.
- [2026-05-18 01:42-01:50] A2: 13 specs materializadas em producao/ (8 VISUAL-LAYOUT + INFRA-OOM + INSTALL-SUDO + INFRA-MODEL-AGNOSTIC + SPRINT_ORDER-REFRESH + HELP-COVERAGE-FIX).
- [2026-05-18 01:51] A3: SPRINT_ORDER_MASTER.md bump v5.0 → v5.1, bloco Onda 24 adicionado (13 entries, 4 sub-blocos, notas de reconciliação 5bc4354..decd858, seção 62 RASCUNHOs).
- [2026-05-18 01:51] Smoke + invariantes + sbom pós-A3 OK (14/14, 62/62).
- [2026-05-18 01:55] A4: commit 9f8a84c pushed (20 arquivos, +1799/-3). 13 specs em producao/ + MASTER v5.1 + SESSAO_LOG + proofs/A1_baseline/.
- [2026-05-18 01:55] **Fase A CONCLUIDA.** Transição: Task #1 completed, Task #2 (Fase B) in_progress. Iniciando UX-PROGRESSION-02.
- [2026-05-18 02:00-02:10] B1: UX-PROGRESSION-02 implementada. 3 mensagens de sessão migradas para glifo . microcopy_audit.py endurecido com 3 padrões novos (Goodbye/Bye, Adeus/Tchau, Sucesso!/Pronto!/Ok!/Concluido! isolados) + heurística anti-falso-positivo. MICROCOPY.md ganhou 3 entradas + seção de glifos. ADR-027 PROPOSTO -> ACEITO.
- [2026-05-18 02:11] B1 commit `aee1e82` pushed. UX-PROGRESSION-02 movida producao -> concluidos. EXECUTAR_SPRINT.md agora aponta VISUAL-LAYOUT-01 (24 pendentes). Iniciando B2: UX-AGENCY-02.
- [2026-05-18 02:15-02:25] B2: UX-AGENCY-02 implementada. agent.run wrappado em asyncio.create_task com tracking em app_state["inflight_task"]. Handler /cancel agora chama .cancel() de verdade. KeyboardInterrupt também cancela explicitamente. Footer dinâmico mostra " executando (Ctrl+C cancela)" quando inflight. ADR-026 PROPOSTO -> ACEITO.
- [2026-05-18 02:26] B2 commit `251e186` pushed. UX-AGENCY-02 movida producao -> concluidos. **Fase B CONCLUIDA.** Iniciando Fase C: Cockpit (COCKPIT-02..05).
- [2026-05-18 02:30-03:30] C1: COCKPIT-02 implementação. xterm.js + xterm.css vendored em static/vendor/ (curl unpkg, 288KB total). pty_bridge.py criado (~140L: PtyBridge async com pty.openpty, read/write/resize/close idempotente). server.py extendido com @app.websocket("/repl").
- [2026-05-18 02:35-03:30] **BUG isolado em 12 reproduções `/tmp/test_appN.py`:** combinação `create_app() function + uvicorn.run(app obj)` em Starlette 1.0 quebra WS handshake (retorna 403 sem chamar handler). Documentado em sprint nova `COCKPIT-02-FIX-WS-403`.
- [2026-05-18 03:30] **Bug resolvido:** reescrita do `nyx/cockpit/server.py` declarando `app = FastAPI()` no module-level (sem function wrapper). WS handshake passa a retornar 101. PTY bridge end-to-end OK (Python websockets test recebe banner do Nyx).
- [2026-05-18 03:35] C1 commit `e9707fc` pushed. COCKPIT-02 + COCKPIT-02-FIX-WS-403 ambas em `concluidos/`. requirements.txt atualizado com fastapi/uvicorn[standard]/wsproto/websockets/pyyaml. Iniciando C2: COCKPIT-03 (dashboard 62 cards).
- [2026-05-18 03:38] C2: COCKPIT-03 dashboard 62 cards implementado. HTMX 1.9.12 + Alpine.js 3.13.5 vendored. /api/tokens (paleta D), POST /api/features/{id}/run, GET status. _job_register + rotate 50 jobs LRU. Mapeamento categoria->fase (achado: gauntlet --only espera fase, materializado anti-debito COCKPIT-03-GAUNTLET-PER-FEATURE-01). Commit `2ad145a` pushed.
- [2026-05-18 03:42] C3+4: COCKPIT-04 (screenshot/evidencia.py com rotate 5 + 1MB cap) + COCKPIT-05 (6 control endpoints: /control/gauntlet/run, status, feature/run, repl/send, repl/snapshot, registry) + COCKPIT_API.md (180+ linhas, curl exemplos). python-multipart instalado. Substituida menção 'Claude' por 'agente externo' em comments para honrar ADR-005. Commit `4ab1fdb` pushed.
- [2026-05-18 03:46] **Fase C CONCLUIDA.** Iniciando D: UX-COCKPIT-EXPERIENCE-01.
- [2026-05-18 03:47] D: GET /api/microcopy serve MICROCOPY.md + 25 strings canonicas em PT-BR. Frontend hidrata via fetch + this.copy.*. Botao cancelar (purple) aparece quando rodando. Tooltips :title nos filtros. Voz Nyx uniforme TUI<->Web. Commit `ea2850e` pushed.
- [2026-05-18 03:48] **Fase D CONCLUIDA.** Iniciando E: VISUAL-LAYOUT-01 (design_tokens_extended).
- [2026-05-18 03:50] E1: VL-01 design_tokens_extended.py (6 AESTHETICS + 7 ENTITIES, ~280L). Invariante #6 atualizado para incluir design_tokens_extended.py no whitelist. Commit `4a5d0e7`.
- [2026-05-18 03:55] E4: VL-08 NYX_AESTHETIC env + --aesthetic flag + /aesthetic command + /api/aesthetics. Total commands sobe pra 61. Materializa VL-CLI-CONSUME-01 anti-débito (CLI ainda lê design_tokens.py direto; consumer extended fica para sub-sprint). Commit `4ed241d`.
- [2026-05-18 04:00] **Fase E CONCLUIDA** (4 sprints visuais + 1 anti-débito materializada). VL-02 (banner neofetch), VL-05 (arcano showcase), VL-03/04/06/07 ficam para próxima sessão.
- [2026-05-18 04:00] F: INFRA-OOM-01 (bin/nyx-runtime-limits.sh + scripts/check_oom.sh + FASE 11 no install + source em run.sh) + INSTALL-SUDO-01 (NYX_SUDO_PASSWORD via env var, sem hardcode, AVISO de troca local pois senha vazou em commit 9f8a84c). README seção "Replicação". .gitignore endurecido. Commit `053ff05`.
- [2026-05-18 04:00] **Fase F CONCLUIDA.**
- [2026-05-18 04:02] G: VALIDATE-FINAL-01 CONCLUIDA_PARCIAL. Frente 1 (5 runs benchmark mediana 0.14s vs <1.5s critério): PASS. Frente 6 (gauntlet --only rapido: infra 5/5 + proxy 6/6): APROVADO. RELATORIO + CHECKLIST + proofs/G_validate_final/. PARTE-2 anti-débito materializada para screenshots/Docker/47cmds/34tools. Tag v1.0 NÃO cortada. Commit `32cbe48`.
- [2026-05-18 04:05] **Fase G CONCLUIDA_PARCIAL**. PARTE-2 pendente humana.
- [2026-05-18 04:05] H light: 11 RASCUNHOs já cobertos pelo gauntlet rapido (I-01/03/05/09/11 + P-01/02/04/05/06/07) promovidos RASCUNHO -> CONCLUIDA. 51 RASCUNHOs restantes em producao/. Commit `1c5d264`.
- [2026-05-18 04:05] **Fase H light CONCLUIDA.** Fase I (INFRA-MODEL-AGNOSTIC-01) pendente para próxima sessão.
- [2026-05-18 04:06] **Fase H light CONCLUIDA.** Marcador anterior. Sessão segue.
- [2026-05-18 04:30-05:00] Validacao via Playwright/Chrome MCP: cockpit dashboard 62 cards OK, terminal.html PTY conectado, Nyx responde "oi" em PT-BR. 3 agentes executor-sprint disparados em paralelo (HELP-COVERAGE-FIX-01, COCKPIT-03-GAUNTLET-PER-FEATURE-01, VISUAL-LAYOUT-CLI-CONSUME-01).
- [2026-05-18 05:00] 5 achados de uso real materializados como sprints anti-débito: HELP-COVERAGE-FIX-02 (/aesthetic > max 3), NYX-AUTO-APPROVE-01 (CONFIRM_ONCE em PTY), PTY-PERMISSION-FLOW-01 (UI aprovar), COCKPIT-LIFECYCLE-FIX-01 (lock colide com cockpit), NYX-NO-HALLUCINATE-TOOL-01 (modelo afirmou sucesso sem tool real).
- [2026-05-18 05:00] 3 agentes completaram: commits 2c87ae2, f12be5d, 3b7eb79. Pushed.
- [2026-05-18 05:10] NYX-MENU-WIZARD-01 implementada: scripts/menu_wizard.py + run.sh `--menu` / `--web` / `--auto-approve`. README seção "Wizard" e "Cockpit Web". Sprint CONCLUIDA direto.
- [2026-05-18 05:15] **SESSÃO CONCLUÍDA.** Total: ~17 commits pushed em ~3h30min. ~24 sprints CONCLUIDAS (15 implementação + 11 RASCUNHOs cobertos + 5 anti-débitos materializados + 1 wizard). Estado: smoke=ok, inv=14/14, sbom=62/62, cockpit operacional, dashboard renderizado em Chrome.
- [22:52] sprint TUI-REDESIGN-28-01 CONCLUIDA hash 916adc5 — boot silencioso (6 mensagens [nyx] viraram log_boot) + endmark capitalizado "Sessão Iniciada" em run.sh:654 e design_tokens.py:103.
- [2026-05-18] sprint TUI-REDESIGN-28-03 CONCLUIDA — capitalização Title Case do box `Última Sessão` em ambas versões (grid >=80 cols + inline <80 cols) de `render_session_stats_card` em `nyx/agent/output.py`. 7 strings + docstring + CELL_W (22→17 com justificativa aritmética: pior caso "Sessão"(6) + short_id 8 chars + gap 1 + padding 2 = 17). Smoke=ok | invariantes=14/14 | microcopy_audit=zero violações. Render via stub salvo em `/tmp/stats_28_03.txt`.

---

## Contexto da sessão (resumido — detalhe no plano)

**Meta declarada do usuário:** "Claude Code offline e opensource: inteligente, robusto, completo, unificado e integrado. O LLM sabe operar, sabe usar cada feature e é tão autosuficiente e bom quanto o Claude Code. O modelo não importa — até o pior modelo com a infra força ele a ser bom. Trocar de modelo não quebra; melhora qualidade ou velocidade de fabricação do código. Estética importa."

**Pedido reforçado (segunda mensagem):** "cuida pra que o nosso trabalho sempre tenha checkpoints e sempre vá documentando e atualizando tudo pra que o progresso não se perca caso a sessão caia"

**9 fases planejadas:**

| Fase | Tema | Tempo | Estado |
|---|---|---|---|
| A | Baseline + 12 sprints novas + reconciliação MASTER | 15-30 min | INICIANDO |
| B | Anti-débito (UX-PROGRESSION-02 + UX-AGENCY-02) | 45-60 min | pendente |
| C | Cockpit (COCKPIT-02..05: PTY+xterm + dashboard + screenshot + control API) | 3-5h | pendente |
| D | Coerência TUIWeb (UX-COCKPIT-EXPERIENCE-01) | 1-2h | pendente |
| E | Estética (VISUAL-LAYOUT-01/02/05/08 portados do novo_layout) | 2-3h | pendente |
| F | Infra (INFRA-OOM-01 + INSTALL-SUDO-01) | 45 min | pendente |
| G | VALIDATE-FINAL-01 (gate v1.0, tag v1.0) | 2-4h | pendente |
| H | Promoção 62 RASCUNHOs (categoria a categoria) | 2-4h | pendente |
| I | INFRA-MODEL-AGNOSTIC-01 (tese "modelo menor + infra forte") | 1h | pendente |

**13 sprints novas a materializar na Fase A (12 planejadas + 1 achado A1):**

1. VISUAL-LAYOUT-01 — design_tokens_extended.py (5 aesthetics + 7 entities)
2. VISUAL-LAYOUT-02 — Banner 3 modos (compact/wide/neofetch)
3. VISUAL-LAYOUT-03 — Theme engine no terminal
4. VISUAL-LAYOUT-04 — Glifos por aesthetic
5. VISUAL-LAYOUT-05 — Estético arcano (showcase MVP)
6. VISUAL-LAYOUT-06 — Estéticos restantes (cyber/brutalist/mecha/editorial)
7. VISUAL-LAYOUT-07 — Spinner Braille + meter inline
8. VISUAL-LAYOUT-08 — Config aesthetic + flag + command
9. INFRA-OOM-01 — Controle OOM no install/run
10. INSTALL-SUDO-01 — NYX_SUDO_PASSWORD via env var
11. INFRA-MODEL-AGNOSTIC-01 — Tese "infra forte"
12. SPRINT_ORDER-REFRESH-01 — Auditoria + update do MASTER defasado
13. **HELP-COVERAGE-FIX-01** (achado A1) — `/?` precisa de pelo menos +1 exemplo

---

*Atualizado: 2026-05-18 01:38, Fase A iniciada.*

---

## Append-only log (sprints executadas)

- [22:59] sprint TUI-REDESIGN-28-02 CONCLUIDA hash d9df1ff
- [M6] sprint INFRA-ACENTO-FIX-01 CONCLUIDA — 3 violações de acentuação corrigidas em `scripts/menu_wizard.py` (linhas 8/64/119: `nao`→`não` x2, `descricao`→`descrição`). validar-acentuacao 3→0, smoke ok, invariantes 14/14, import sanity ok
- [M5] sprint DOCS-MICROCOPY-SESSAO-INICIADA-01 CONCLUIDA — capitaliza `sessão iniciada`→`Sessão Iniciada` em `dev-journey/05-guides/MICROCOPY.md:109` (paridade com `nyx/themes/design_tokens.py` e `run.sh`). microcopy_audit zero violações, smoke ok, invariantes 14/14, grep `Sessão Iniciada` retorna 1
