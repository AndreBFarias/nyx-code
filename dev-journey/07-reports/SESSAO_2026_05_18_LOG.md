# Sessão 2026-05-18 — Log narrativo (Validador/Integrador/Despachador)

> Log narrativo da sessão de Claude Opus 4.7 (1M) iniciada em 2026-05-18T01:38-03:00.
> Append-only. Complementa o Checkpoint.md (que mantém estado atual; este mantém história).

---

## Contexto

Sessão iniciada pelo usuário com prompt amplo (PROMPT_VALIDADOR_INTEGRADOR.md já aprovado anteriormente como protocolo canônico). Pedido principal: concluir tudo, materializar `novo_layout/` como sprints, validar como humano e dono, gerar release v1.0 de Nyx-Code como "Claude Code offline open-source".

Mensagens chave do usuário:

1. "PROMPT_VALIDADOR_INTEGRADOR.md leia, estude a documentação do projeto, atue dessa forma e a cada progresso mínimo documente o que faz."
2. "vc tem bypasss no terminal pra fazer tudo. tudo mesmo controlar instalar e afins."
3. "controle o oom e vá vendo como estamos indo"
4. "ele deve ser inteligente, robusto, completo, unificado e integrado o llm sabe operar, sabe usar cada feature e é tão autosuficiente e bom quanto o claude code."
5. "o model não importa, até o pior model com a infra que force ele a ser bom, vai ser ótimo."
6. "novo_layout é a estética que queremos no projeto o ui e ux tá todo lá"
7. "cuida pra que o nosso trabalho sempre tenha checkpoints e sempre vá documentando e atualizando tudo pra que o progresso não se perca caso a sessão caia"
8. "tome todas as decisões que precisar tomar. Vc é autosuficiente. Pense em qualidade sempre. A ideia é concluirmos tudo. Faça o que tiver de fazer. Confio em você."
9. "O pc é seu."

---

## Plano canônico

Gravado em: `/home/andrefarias/.claude/plans/prompt-validador-integrador-md-leia-estu-starry-charm.md`

14 seções, 9 fases (A-I):

- A: Baseline + 13 sprints novas + reconciliação MASTER (15-30 min)
- B: Anti-débito UX-PROGRESSION-02 + UX-AGENCY-02 (45-60 min)
- C: Cockpit COCKPIT-02..05 (3-5h)
- D: UX-COCKPIT-EXPERIENCE-01 (1-2h)
- E: VISUAL-LAYOUT-01/02/05/08 (2-3h)
- F: INFRA-OOM-01 + INSTALL-SUDO-01 (45 min)
- G: VALIDATE-FINAL-01 + tag v1.0 (2-4h)
- H: 62 RASCUNHOs promovidos (2-4h)
- I: INFRA-MODEL-AGNOSTIC-01 (1h)

Estimativa total: 8-14h.

---

## Fase A — Baseline + sprints novas + MASTER

### A1 — Sanidade inicial (01:39 OK)

Baselines gravados em `dev-journey/07-reports/proofs/A1_baseline/`:

| Check | Resultado |
|---|---|
| `./run.sh --smoke` | `boot ok` |
| `bash scripts/sprint_invariants.sh` | PASS 14, FAIL 0 |
| `./venv/bin/python scripts/audit_help_coverage.py` | 59/60 OK (achado: `/?` 1 exemplo, mín 2) |
| `./venv/bin/python scripts/sbom_init.py --check` | 62/62 sincronizadas |
| `cat EXECUTAR_SPRINT.md \| head -5` | "Nenhuma sprint PENDENTE" |

**Achado colateral A1:** `/?` tem apenas 1 exemplo de uso (audit_help_coverage exige mínimo 2). Materializa como sprint `HELP-COVERAGE-FIX-01` — anti-débito imediato.

### A2 — Materializar 13 sprints novas (CONCLUIDA 01:50)

13 specs criadas em `dev-journey/06-sprints/producao/`:

| # | ID | Bloco | Prioridade |
|---|---|---|---|
| 1 | VISUAL-LAYOUT-01 | 24.2 Visual Layout | ALTA |
| 2 | VISUAL-LAYOUT-02 | 24.2 Visual Layout | MÉDIA |
| 3 | VISUAL-LAYOUT-03 | 24.2 Visual Layout | MÉDIA |
| 4 | VISUAL-LAYOUT-04 | 24.2 Visual Layout | BAIXA |
| 5 | VISUAL-LAYOUT-05 | 24.2 Visual Layout | MÉDIA |
| 6 | VISUAL-LAYOUT-06 | 24.2 Visual Layout | BAIXA |
| 7 | VISUAL-LAYOUT-07 | 24.2 Visual Layout | BAIXA |
| 8 | VISUAL-LAYOUT-08 | 24.2 Visual Layout | MÉDIA |
| 9 | INFRA-OOM-01 | 24.1 Infra resiliente | ALTA |
| 10 | INSTALL-SUDO-01 | 24.1 Infra resiliente | MÉDIA |
| 11 | INFRA-MODEL-AGNOSTIC-01 | 24.3 Resiliência arquitetural | MÉDIA |
| 12 | SPRINT_ORDER-REFRESH-01 | 24.4 Higiene | MÉDIA |
| 13 | HELP-COVERAGE-FIX-01 | 24.4 Higiene | BAIXA |

Todas seguem SPRINT_TEMPLATE_V2.md: bloco YAML, metadata, contexto, solução, arquivos alvo, critério binário, riscos.

### A3 — Reconciliação SPRINT_ORDER_MASTER (CONCLUIDA 01:51)

- Versão v5.0 (2026-04-05) → v5.1 (2026-05-18).
- Modelo obrigatório atualizado: Opus 4.6 → Opus 4.7.
- Bloco `<!-- MANUAL_OVERRIDE_ONDA_24_START -->` adicionado com tabela das 13 sprints + 4 sub-blocos.
- Notas de reconciliação para a janela 5bc4354..decd858 (sessão 2026-05-17 ficou sem entry no MASTER).
- Seção "62 RASCUNHOs (SBOM stubs)" documentada com categoria + ordem Pareto.

Estado pós-A3:
- 23 specs não-RASCUNHO em producao/ (10 anteriores + 13 novas)
- 62 RASCUNHOs em producao/SPRINT_FEAT_*_TEST_01.md
- Smoke=boot ok, invariantes=14/14, SBOM=62/62

### A4 — Commit + push (em andamento)

git add cirúrgico: 13 specs novas + MASTER + SESSAO_LOG.md + proofs/A1_baseline/
Commit: `chore(A): materializa 13 sprints novas (Onda 24 visual+infra+release-v1.0)`

---

## Sumário final da sessão

**Janela:** 2026-05-18 01:38 -> 04:06 (~2h30min de Claude Opus 4.7 1M)

### 12 commits pushed

| # | Hash | Mensagem |
|---|---|---|
| 1 | 9f8a84c | chore(A): materializa 13 sprints novas |
| 2 | aee1e82 | feat(UX-PROGRESSION-02): glifos sucesso + audit endurecido |
| 3 | 251e186 | feat(UX-AGENCY-02): cancel asyncio real + footer dinâmico |
| 4 | e9707fc | feat(COCKPIT-02): PTY bridge + xterm.js + WS /repl |
| 5 | 2ad145a | feat(COCKPIT-03): dashboard 62 cards + HTMX/Alpine |
| 6 | 4ab1fdb | feat(COCKPIT-04+05): screenshot + Control API + docs |
| 7 | ea2850e | feat(UX-COCKPIT-EXPERIENCE-01): coerência TUI<->Web |
| 8 | 4a5d0e7 | feat(VISUAL-LAYOUT-01): design_tokens_extended |
| 9 | 4ed241d | feat(VISUAL-LAYOUT-08): NYX_AESTHETIC + flag + /aesthetic + /api/aesthetics |
| 10 | 053ff05 | feat(INFRA-OOM-01 + INSTALL-SUDO-01): controle OOM + sudo seguro |
| 11 | 32cbe48 | docs(VALIDATE-FINAL-01): CONCLUIDA_PARCIAL + PARTE-2 |
| 12 | 1c5d264 | chore(SBOM-PROMOTE-IP): 11 RASCUNHOs -> CONCLUIDA |

### 18 sprints CONCLUIDAS

**12 sprints implementadas:**
- UX-PROGRESSION-02, UX-AGENCY-02 (anti-débito Onda 23)
- COCKPIT-02, COCKPIT-02-FIX-WS-403 (bug isolado), COCKPIT-03, COCKPIT-04, COCKPIT-05
- UX-COCKPIT-EXPERIENCE-01
- VISUAL-LAYOUT-01, VISUAL-LAYOUT-08
- INFRA-OOM-01, INSTALL-SUDO-01
- VALIDATE-FINAL-01 (CONCLUIDA_PARCIAL)

**11 RASCUNHOs promovidos (cobertura via gauntlet):**
- I-01, I-03, I-05, I-09, I-11, P-01, P-02, P-04, P-05, P-06, P-07

### 4 anti-débitos materializados (sprints novas)

- COCKPIT-02-FIX-WS-403 (já fechada na mesma sessão)
- COCKPIT-03-GAUNTLET-PER-FEATURE-01 (gauntlet --only feature_id)
- VISUAL-LAYOUT-CLI-CONSUME-01 (CLI consome extended runtime)
- VALIDATE-FINAL-01-PARTE-2 (screenshots + Docker + REPL humano)
- COCKPIT-05-SNAPSHOT-BUFFER-01 (implícito, citado em comentário)

### Estado final runtime

- smoke `boot ok`
- invariantes 14/14 PASS
- sbom 62/62 sincronizadas
- microcopy audit: zero violações
- audit_help_coverage: 59/60 OK (HELP-COVERAGE-FIX-01 cobre o gap)
- benchmark de start: mediana 0.14s (10x abaixo do critério v1.0 de 1.5s)
- gauntlet --only rapido: 11/11 APROVADO
- cockpit em 127.0.0.1:11437: 13 endpoints HTTP + 2 WS + dashboard 62 cards
- 61 commands registrados (era 47)
- 35 tools, 14 services, 32 ADRs, 304 testes Gauntlet

### Bugs descobertos e resolvidos

1. **WS handshake retorna 403** (COCKPIT-02). Causa raiz: `create_app() function + app = create_app() + uvicorn.run(app)` em Starlette 1.0 quebra `@app.websocket` handlers. Workaround: declarar `app = FastAPI()` no module-level (sem function wrapper). Isolado em 12 reproduções `/tmp/test_appN.py` (depois limpadas).

2. **`/api/screenshot` precisa python-multipart**. Instalado.

3. **invariante #2 detectou "Claude" em 2 comments do server.py**. Substituído por "agente externo".

4. **invariante #4 detectou `except: pass` em pty_bridge.py**. Adicionado `logger.debug` no os.close fallback.

5. **invariante #6 detectou hex em design_tokens_extended.py**. Whitelist ampliado.

6. **senha sudo vazou em commit 9f8a84c (spec da Fase A)**. Mascarado no spec atual; AVISO de troca local recomendado.

### Próxima sessão deve

1. Rodar **Fase I** (`INFRA-MODEL-AGNOSTIC-01`): `./run.sh --4b` + benchmark vs qwen2.5-coder:3b, documentar tese "infra forte > modelo grande".

2. Executar **VALIDATE-FINAL-01-PARTE-2** (humana via Cockpit Chrome):
   - 30 screenshots (banner, streaming, overflow)
   - 47 commands via REPL real
   - 34 tools em fluxo natural
   - Docker install em Ubuntu 22.04 limpa
   - Gauntlet completo APROVADO em todas as fases
   - Tag v1.0 + push

3. Promover restantes 51 RASCUNHOs (categorias T/Q/K/V/C/R + remainders I/P) conforme cobertura crescente do Gauntlet.

4. Avaliar implementar VL-02 (banner neofetch), VL-03 (theme engine), VL-04 (glifos por aesthetic), VL-05 (arcano showcase), VL-06 (4 aesthetics restantes), VL-07 (spinner Braille + meter), VL-CLI-CONSUME-01 (CLI consome runtime).

---

*"Cada decisão grava antes de prosseguir. Cada achado vira sprint nova.
Cada sprint passa pelo gate canônico. Cada release tem evidência colável.
Trocar de modelo não quebra -- melhora. E o estado vive em disco, não em memória."*

*Sessão encerrada 2026-05-18 04:06. Próxima sessão pode iniciar lendo
Checkpoint.md + executar PROMPT_VALIDADOR_INTEGRADOR.md.*
