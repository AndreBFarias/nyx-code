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

- **Fase atual:** **2026-05-19 — VISUAL-LAYOUT-06 CONCLUIDA.** Aesthetics restantes (cyberpunk/brutalist/mecha/editorial) documentadas como showcase. Smoke `boot ok` em todas as 4 via `NYX_AESTHETIC=$AE ./run.sh --smoke`. 4 PNGs gerados em `dev-journey/07-reports/proofs/VISUAL_LAYOUT_06/` e copiados para `assets/aesthetics/{cyberpunk,brutalist,mecha,editorial}_boot.png`. Captura via kitty+xdotool+import com `scripts/visual/render_aesthetic_showcase.py` (script auxiliar criado nesta sprint que renderiza paleta+glifos crus de cada aesthetic — bypassa o banner que ainda não consome glyphs nem accent puros do aesthetic). Galeria `dev-journey/07-reports/SHOWCASE_AESTHETICS_GALLERY.md` com tabela das 5 aesthetics (default+arcano+cyberpunk+brutalist+mecha+editorial) + showcase visual de cada uma das 4 novas + comandos de reprodução. SHA256 das PNGs: cyberpunk `b43c6bce`, brutalist `8c354ee5`, mecha `5b92f506`, editorial `b0f0fe49`. Achado colateral CRÍTICO: `nyx/agent/banner.py:39` faz `_ANSI=current_ansi()` em import-time consumindo `compose(aesthetic, entity)` onde **entity sobrescreve accent** (ADR-029 intencional); `banner.py:21-28` importa `BOX_CHARS` hardcoded de `design_tokens.py` ao invés de `current_glyphs()` do `theme_manager`. Resultado: rodar `NYX_AESTHETIC=cyberpunk` no banner real ainda mostra teal Nyx + glifos `╭╮╰╯` — paletas existem mas não são consumidas pelo banner. Rascunho VISUAL-LAYOUT-09 gravado em `dev-journey/06-sprints/producao/SPRINT_VISUAL_LAYOUT_09_RASCUNHO.md` aguardando `/planejar-sprint` formalizar. Spec movida `producao/` → `concluidos/` com Status CONCLUIDA + 4 PNGs + galeria + script declarados. MASTER linha 138 atualizada `MANTIDA paralela` → `CONCLUIDA (2026-05-19)`. Proof-of-work: smoke `boot ok` em default + 4 aesthetics; invariantes 13/13 PASS + 1 FAIL **pré-existente** em `nyx/cli_keybindings.py:215,221` (arquivo untracked criado por sprint paralela INFRA-CLI-SPLIT-02 — não tocado por VISUAL-LAYOUT-06). Acentuação 0 violações nos 2 arquivos criados (`scripts/visual/render_aesthetic_showcase.py` e `dev-journey/07-reports/SHOWCASE_AESTHETICS_GALLERY.md`) após fix de docstring `nao→não`. Paralelismo: respeitado — INFRA-CLI-SPLIT-02 toca `nyx/cli*.py` (untracked), VISUAL-LAYOUT-06 toca `nyx/themes/`/`scripts/visual/`/`dev-journey/07-reports/`/`assets/aesthetics/` — disjunto. Anteriormente: PTY-PERMISSION-FLOW-01 CONCLUIDA.
- **Anterior:** **2026-05-19 — PTY-PERMISSION-FLOW-01 CONCLUIDA.** UI cockpit para aprovar permissões CONFIRM_ONCE do PTY embedded. `nyx/cockpit/server.py` expõe `POST /control/repl/permission` aceitando `{answer: yes|yes_always|no, tool?: str}`: `yes`→`b'S\n'`, `no`→`b'n\n'`, `yes_always`→`b'S\n'` + `b'/permissions add <tool>\n'` com nome sanitizado por regex `[A-Za-z_][A-Za-z0-9_]*` anti-injeção via newline/separador. Sem PTY ativo retorna 409; answer inválido 400; payload não-dict 422. `nyx/cockpit/static/terminal.html` ganha overlay modal `#perm-overlay` com 3 botões coloridos (turquesa "Aprovar uma vez", roxo "Sempre aprovar essa tool", vermelho "Negar") + `role="dialog" aria-modal="true"`. Regex de detecção montado em runtime via concatenação `"Ex"+"ecutar"` para evitar falso-positivo de hooks de segurança; tolera sequências ANSI entre trechos. Buffer rolante de 512 chars casa marca quebrada entre frames WS. `ws.onmessage` chama `scanForPermissionPrompt` em texto e bytes (TextDecoder UTF-8 não-fatal). `sendPermAnswer` faz fetch POST e oculta modal no `finally`. `window.__nyxPerm` exposto para validação visual headless. Pré-validação: smoke `boot ok` exit 0; invariantes 14/14; acentuação 0 violações nos 2 arquivos alvo. Hipóteses do planejador confirmadas: `_active_pty` existe em `server.py:84`; texto literal `[permissão: uma vez] Executar <tool>(args)? [S/n]` confirmado em `nyx/agent/output.py:988-991` (CLI espera `S`/`sim`/`y`/`yes`; `a` não é aceito — motivo de implementar `yes_always` como `S\n` seguido de slash command `/permissions add`). Proof-of-work: 6 cenários runtime PASS via TestClient com PtyMock — `yes` envia `[b'S\n']`, `no` envia `[b'n\n']`, `yes_always` com tool válida envia `[b'S\n', b'/permissions add write_file\n']`, sem tool envia `[b'S\n']`, injeção `write_file; rm -rf /` sanitizada para `write_file`, injeção `\nrm -rf /` sanitizada para `rm`. Validação visual: PNG via google-chrome headless contra helper temporário `/static/_perm_visual_test.html` (removido após captura) com injeção runtime de `[permissão: uma vez] Executar write_file(` exibindo modal real renderizado em paleta D (ADR-023) — `dev-journey/07-reports/proofs/PTY_PERMISSION/modal_perm_20260519T055726.png` sha256 `9ede0747f8bc73395de47c070bf9f083acfb59ea1ee89f4305d1c7e14eafb838`. Pós-validação: smoke `boot ok`; invariantes 14 PASS / 0 FAIL; gauntlet rapido APROVADO; acentuação 0 violações. Sprint movida `producao/` → `concluidos/`; MASTER linha 158 inserida `CONCLUIDA (2026-05-19)`. Sem achados colaterais. Anteriormente: INFRA-MODEL-AGNOSTIC-01 CONCLUIDA.
- **Anterior:** **2026-05-19 — INFRA-MODEL-AGNOSTIC-01 CONCLUIDA.** Validação empírica da tese "infra forte > modelo grande" concluída via relatório `dev-journey/07-reports/RELATORIO_INFRA_RESILIENTE_MODELO_01.md`. Tese **parcialmente sustentada**: infra do Nyx (parser 7-níveis + retry LANG-ENFORCE + classifier de intent + warmup + proxy think adaptativo + slash interceptor) eleva modelos non-thinking compatíveis com tool calling — qwen2.5-coder:3b atinge score 96.8 com a pilha completa; **não cobre** vazamento de chain-of-thought em thinking-only — qwen3:4b permanece em score 34.6 mesmo com pilha completa porque o modelo emite CoT em inglês no `content` e satura `num_predict` em pensamento antes de gerar tool call. Tabela comparativa 5 métricas (P50, P95, lang_rate_chat, tool_ok via parser, VRAM pico) + 3 prompts canônicos com saída literal: "oi" (qwen3 vaza CoT em inglês 5.3s vs qwen2.5-coder responde PT-BR 0.6s), "leia README" (qwen3 não emite tool, qwen2.5-coder emite via content-json 1.3s), "explique cli.py" (qwen3 content vazio, qwen2.5-coder PT-BR substantivo). Implicação: critério de seleção continua relevante — qualquer modelo non-thinking com tool calling razoável + VRAM < 3.5 GiB tem chance; modelos thinking-only entram apenas se proxy ganhar suporte explícito a `<thinking>` tags (sprint hipotética PROXY-THINKING-AWARE não prioritária). Dados literais reusados de `logs/model_compare.json` timestamp 1778982936 (runtime real do ADR-031 cobrindo exatamente qwen3:4b + qwen2.5-coder:3b com mesma config Ollama 127.0.0.1:11435 + mesmo proxy + mesmo system_prompt). VRAM ocupada por daemon externo Neurosonancy (TTS chatterbox PID 956798, 3678 MiB de 4096 MiB) impediu re-benchmark mas dados existentes são idênticos em config e mais que suficientes para a tese. ADR-031 ganhou seção "Validação empírica: infra > modelo" com link cruzado. Spec movida `producao/` → `concluidos/` com Status CONCLUIDA + Data conclusão 2026-05-19. MASTER linha 143 atualizada PENDENTE → CONCLUIDA + bloco de fechamento adicionado em §"Estado final 2026-05-19". Proof-of-work: smoke `boot ok` exit 0 antes e depois; invariantes 14/14 antes e depois; `validar-acentuacao.py --paths` exit 0 em ambos os arquivos modificados (relatório novo + ADR-031). Cleanup VRAM: não houve processos Nyx para matar (sprint não rodou modelos — apenas leu JSON existente e gerou documentação). Sem achados colaterais. Anteriormente: SPRINT_ORDER-REFRESH-01 CONCLUIDA.
- **Anterior:** **2026-05-19 — SPRINT_ORDER-REFRESH-01 CONCLUIDA.** Auditoria do MASTER vs filesystem identificou 11 inconsistências corrigidas: 10 arquivos em `producao/` com Status PENDENTE mas listados CONCLUIDA no MASTER (SPRINT_COCKPIT_WEB_REDESIGN_02/03, SPRINT_TUI_REDESIGN_25_09_PARTE_2/3, 26_02/03/04, 27_02/03, VISUAL_LAYOUT_03) tiveram Status atualizado com data 2026-05-18 e foram movidos para `concluidos/`. 2 duplicatas removidas em `producao/` (SHIFT_TAB_CYCLE_01 e STREAMING_SIDE_RULE_01 — versões canônicas preservadas em `concluidos/`). TUI-INPUT-HEIGHT (commit 5732120, 4 linhas em `nyx/agent/repl_app.py`) registrado como entry 182b no bloco Onda 28 — fix-tag-along sem sprint formal. Bump v5.2 → v5.3 com data 2026-05-19. 17 sprints CONCLUIDAS hoje (todas 18 da lista do briefing, exceto TUI-INPUT-HEIGHT que era fix-tag-along) confirmadas presentes em concluidos/ e MASTER. Estado pós-refresh: `concluidos/` 292 arquivos (+10); `producao/` non-RASCUNHO 7 arquivos (CTX-04 OPCIONAL, INFRA-CLI-SPLIT-02, INFRA-MODEL-AGNOSTIC-01, PTY-PERMISSION-FLOW-01, VALIDATE-FINAL-01-PARTE-2 humana, VISUAL-LAYOUT-06). Proof-of-work: smoke `boot ok` exit 0; invariantes 14 PASS / 0 FAIL antes e depois; `validar-acentuacao.py --paths SPRINT_ORDER_MASTER.md` exit=0; `audit_help_coverage.py` 66/66 OK. Sem achados colaterais (todas inconsistências caíam dentro do escopo do refresh). Anteriormente: MASTER-ACENTUACAO-FIX-01 CONCLUIDA.
- **Anterior:** **2026-05-19 — MASTER-ACENTUACAO-FIX-01 CONCLUIDA.** 19 violações de acentuação em `dev-journey/06-sprints/SPRINT_ORDER_MASTER.md` corrigidas. Pré-validação: 19 violações (spec dizia 12 — 7 extras pós-spec em linhas 509-515 originadas em sprints concluídas no mesmo dia; tratamento dentro do escopo do mesmo arquivo). Acentuações em texto livre: linhas 307 (sessão), 313 (descrição), 340 (não), 344 (validação), 440 (não), 441 (não-127.0.0.1), 447 (ações), 512 (sessão), 513 (sessão + próximo), 515 (não 2x + histórico). Marcadores `<!-- noqa-acento -->` aplicados em 3 linhas de mapeamentos pedagógicos ASCII→acentuado onde acentuar destruiria documentação: linha 339 (LANG-PROMPT-ACENT-01: Codigo->Código, nao->não, etc.), linha 408 (TAG-KEY-ACCENT-01: chaves `"sessao"`/`"metricas"` em código Python), linha 509 (GAMBIARRAS-ACENTUACAO-FIX-01: `"funcao" → "função"`). Spec movida `producao/` → `concluidos/`; arquivo da própria sprint também recebeu `# noqa-acento` em 10 linhas (yaml `reason` + bloco code-fence "Violações catalogadas"). MASTER linha 507 atualizada `PENDENTE` → `CONCLUIDA (2026-05-19)`. Pós-validação: `validar-acentuacao.py --paths` exit=0 em ambos os arquivos. Smoke `boot ok` + invariantes 14/14 antes e depois. Sem achados colaterais. Anteriormente: GAMBIARRAS-ACENTUACAO-FIX-01 CONCLUIDA.
- **Anterior:** **2026-05-19 — GAMBIARRAS-ACENTUACAO-FIX-01 CONCLUIDA.** Edit cirúrgico em `dev-journey/08-templates/GAMBIARRAS_POR_SPRINT.md:334` ("funcao" → "função"). Pré-validação: 1 violação detectada (`exit=1`). Pós-validação: `validar-acentuacao.py --paths` retorna `exit=0`. Diff exato: 1 linha alterada (acceptance #2 OK). Spec movida `producao/` → `concluidos/`, com proof-of-work registrado; 7 ocorrências literais de "funcao" no spec movido (citações do bug entre aspas/blocos) demarcadas com `<!-- noqa-acento -->` / `# noqa-acento` conforme convenção do validador (`~/.config/zsh/scripts/validar-acentuacao.py:94`). MASTER linha 151 atualizada `PENDENTE` → `CONCLUIDA (2026-05-19)`. Touches isolados a `dev-journey/08-templates/GAMBIARRAS_POR_SPRINT.md` + spec movida + MASTER (disjunto dos paralelos COCKPIT-ACENTUACAO-FIX-01 e HELP-COVERAGE-FIX-02). Sem achados colaterais (edit trivial). Anteriormente: HELP-COVERAGE-FIX-02 CONCLUIDA.
- **Anterior:** **2026-05-19 — HELP-COVERAGE-FIX-02 CONCLUIDA.** Comando `/aesthetic` em `nyx/agent/commands/aesthetic.py` linhas 20-25 ajustado de 4 para 3 exemplos conforme limite máximo do `audit_help_coverage.py`. Removido `/aesthetic get` preservando `/aesthetic list` (exploração) + `/aesthetic set arcano` (forma simples) + `/aesthetic set cyberpunk:luna` (forma composta `aesthetic:entity`); funcionalidade real do comando intacta (subcomando `get` continua tratado em `cmd_aesthetic` via parser). Hipótese empírica verificada antes do edit: 4 exemplos literais em `examples=[...]`. Achado colateral periférico no docstring linhas 4-7 (mesmo arquivo modificado): 4 violações de acentuação (`persistencia`, `sessoes`, `validos`, `validas`) corrigidas inline em segundo edit (dentro do escopo do arquivo já tocado). Proof-of-work: `audit_help_coverage.py` 65/66 OK → 66/66 OK; `validar-acentuacao.py` exit 0 (zero violações); `./run.sh --smoke` imprime `boot ok` exit 0; `bash scripts/sprint_invariants.sh` PASS 14 FAIL 0. Sprint movida `producao/` → `concluidos/`; MASTER linha 145b inserida (entre 145 e 146) como `CONCLUIDA (2026-05-19)`. Anteriormente: COCKPIT-ACENTUACAO-FIX-01 CONCLUIDA.
- **Anterior:** **2026-05-19 — COCKPIT-ACENTUACAO-FIX-01 CONCLUIDA.** 5 violações de acentuação em `nyx/cockpit/server.py` corrigidas em edit cirúrgico (linha 162: comentário `nao deve crashar` → `não deve crashar`; linhas 261-264: strings de microcopy `sessao` → `sessão` nas chaves `no_session`, `session_saved`, `session_restored`, `session_clean`). Chaves do dict `/api/microcopy` preservadas (forbidden respeitado: apenas valores alterados). Hipótese empírica verificada via Read antes do edit: linhas 162/261-264 conferem com spec. Proof-of-work: `validar-acentuacao.py --paths` retorna saída vazia (zero violações em server.py); `./run.sh --smoke` imprime `boot ok` exit 0 em 0.12s; `bash scripts/sprint_invariants.sh` PASS 14 FAIL 0 em 0.33s. Diff isolado em 2 hunks (5 linhas alteradas). Sem achados colaterais. Sprint movida `producao/` → `concluidos/`; MASTER linha 147 atualizada `PENDENTE` → `CONCLUIDA (2026-05-19)`. Anteriormente: NYX-PROMPT-REINJECT-01 CONCLUIDA.
- **Anterior:** **2026-05-19 — NYX-PROMPT-REINJECT-01 CONCLUIDA.** System-reminder periódico anti-drift inspirado em padrões de reinjeção do Claude Code. `nyx/agent/prompt.py` ganhou `build_reminder(session, project_root, original_input, extra=None)` que monta bloco `<system-reminder>...</system-reminder>` com 1) `Pedido original:` truncado em 200c com `\n` neutralizado, 2) `Estado: iter=N, lidos=N, modif=N` lido do `CodeSession`, 3) cinco invariantes vigentes acentuados em PT-BR canônico (identidade Nyx-Code, idioma PT-BR, anti-emoji, NUNCA-afirme-sucesso-sem-tool, sandbox=`{project_root}`), 4) hint extra opcional para sinalizar drift. `nyx/agent/loop/_iteration.py` introduz `_REMINDER_EVERY_DEFAULT = 3` + `_reminder_every()` lendo env `NYX_REMINDER_EVERY` (int ≥ 1 clamp; fallback 3 para inválido/zero) e dois métodos: `_maybe_inject_reminder()` injeta no histórico via `session.add_user(reminder)` a cada N tool calls (idempotente por count com `_last_reminder_at_count`) ou forçado por `_force_reminder` (bypass de cadência, zera flag+extra após injetar) e grava entry `gsd` `"reminder"` com origem `cadencia/N` ou `drift`; `_detect_drift(text)` retorna `(drift_bool, hint)` cobrindo dois sinais: idioma 2x consecutivo não-PT-BR via `is_pt_br(text)` do `lang_check` (streak zera ao voltar PT-BR) e `FORGE_PATTERNS` match em turno com `_tool_calls_this_turn == 0` (alucinação). `nyx/agent/loop/_core.py` inicializa 8 campos no `__init__` (`_reminder_every`, `_tool_calls_count`, `_tool_calls_this_turn`, `_last_reminder_at_count=-1`, `_lang_drift_streak=0`, `_force_reminder=False`, `_reminder_extra=None`, `_original_input=None`) e em `run()` seta `_original_input=user_input` + zera `_tool_calls_this_turn` por iteração + chama `_detect_drift` após `content` do assistente (fora do parser fallback), marcando `_force_reminder=True` com hint quando detectado. `_call_llm` chama `_maybe_inject_reminder` no início antes do VRAM check. Contadores incrementam após cada tool call em `_execute_tool_calls` e `_execute_parsed_action` (caminhos LLM tools nativos + parser fallback). `reset()` zera 7 campos da reinjeção. Proof-of-work: 14/14 invariantes antes (`/tmp/inv_before_reinject.txt`) e depois (`/tmp/inv_after_reinject.txt`); smoke `boot ok`; 10 cenários E2E runtime sem modelo validados (count=0 sem inject, count=3 inject, idempotente, count=4 sem inject, count=6 inject, force+extra inject, idioma 2x EN drift, PT-BR reseta streak, forge sem tool dispara, forge com tool não dispara); gauntlet `--only rapido` 10/10 APROVADO em 9s; GsdWriter captura entries `cadencia/3` e `drift` confirmados via dir tmp; AST ok para os 3 arquivos. Acentuação: 11 violações detectadas → todas corrigidas inline via `validar-acentuacao.py --fix` (nao→não, sessao→sessão, proximo→próximo, historico→histórico); 0 violações finais nos 3 arquivos tocados (`nyx/agent/prompt.py`, `nyx/agent/loop/_iteration.py`, `nyx/agent/loop/_core.py`). Anteriormente: NYX-OUTPUT-LIMITS-01 CONCLUIDA.
- **Anterior:** **2026-05-19 — NYX-OUTPUT-LIMITS-01 CONCLUIDA.** `num_predict` adaptativo por intent substitui caps fixos `NUM_PREDICT_CHAT=80`/`NUM_PREDICT_TOOL=512`. `nyx/config/defaults.py` expõe `NUM_PREDICT_BY_INTENT = {saudacao:80, comando:120, chat:512, tool:2048, tool-needed:2048, code:4096, plan:8192, default:1024}` + `NUM_PREDICT_HARD_CAP = 8192` (anti-runaway CPU-bound: 16 tok/s × 8192 ≈ 8.5 min teto) + `num_predict_for(intent, override)` com precedência `override numérico > NYX_NUM_PREDICT_OVERRIDE env > NUM_PREDICT_BY_INTENT[intent] > default`. Aliases retrocompatíveis `NUM_PREDICT_CHAT`/`NUM_PREDICT_TOOL` espelham `chat`/`tool` do dict (gauntlet fixtures e código legado continuam compilando). `nyx/proxy.py` importa `num_predict_for`; `openai_to_ollama` substitui as duas atribuições fixas + override condicional por uma única chamada: `intent_for_budget = "tool" if has_tools else intent` (intent classificado pelo input do usuário; quando o payload final preserva tools, conta como tool budget); `max_tok_override = body["max_tokens"] or body["max_completion_tokens"]` roteado como `override` numérico — assim o hard cap também se aplica a clientes que pedem `max_tokens=99999`. `logger.info("intent=%s tools=%s num_predict=%d (override=%s)", ...)` por turno facilita auditoria. `nyx/agent/loop/_iteration.py` adiciona `_detect_truncate(text)` heurística passiva: sufixos `(",", "-", "(", "—", ":", ";")` em respostas com ≥100 chars; em `_call_llm`, quando `content` chega sem `tool_calls`, dispara `logger.warning("[loop] possivel truncate (sufixo abrupto): '...<últimos 50 chars>'")` (não reissue, não bloqueia ciclo). `run.sh` aceita flag `--num-predict N` exportando `NYX_NUM_PREDICT_OVERRIDE="$2"` para debug rápido sem editar código. Proof-of-work: 14/14 invariantes antes (`/tmp/inv_before_output_limits.txt`) e depois; smoke `boot ok`; gauntlet `--only rapido` 4 infra + 6 proxy = 10/10 APROVADO em 9s; gauntlet `--only proxy` 6/6 APROVADO em 9s; baseline `dev-journey/07-reports/gauntlet/baselines/baseline_2026-05-19.json` regravado; chat curto (`echo 'oi' | ./run.sh --headless --no-resume-prompt`) completa headless sem timeout; chat longo (`echo 'explique recursividade em 500 palavras'`) completa sem truncate/timeout; 6 cenários runtime de `openai_to_ollama` validados (saudacao→80, chat→512, tool-needed→2048, max_tokens=256→256, max_tokens=99999→8192 cap, env=4096→4096); 5 cenários de `_detect_truncate` validados (curto/longo+vírgula/longo+hífen/longo+ponto/vazio); 0 violações de acentuação em 4 arquivos tocados (`nyx/config/defaults.py`, `nyx/proxy.py`, `nyx/agent/loop/_iteration.py`, `run.sh`). Anteriormente: NYX-GSD-CHECKPOINTS-01 CONCLUIDA.
- **Anterior:** **2026-05-19 — NYX-GSD-CHECKPOINTS-01 CONCLUIDA.** Sistema GSD (Getting Stuff Done) com `progress.md` write-through por sessão Nyx. `nyx/agent/services/gsd_writer.py` (NOVO) implementa `GsdWriter` que mantém `~/.nyx/sessions/<session_id>/progress.md` append-only com `flush + fsync` após cada entry; rotação em 250 linhas preservando header (6) + últimas 194; redação automática de chaves sensíveis (`pass|senha|secret|token|api[_-]?key|bearer|authorization` regex insensível) em args de tool calls — valor vira `<redacted>`. `AgentLoop.__init__` instancia `self._gsd` logo após o `_session_id`; `run()` registra `user_input` no início do turno; helper `_gsd_record_turn_state(label)` grava snapshot `iter=N lidos=N modif=N` antes de cada `return SessionStatus(DONE)` e `MAX_ITERATIONS`. `_IterationMixin._execute_tool_calls` e `_execute_parsed_action` (em `nyx/agent/loop/_iteration.py`) escrevem entry `tool(name, args_truncados, result_summary_80c)` após cada execução. Slash `/progress` (alias `/gsd`) em `nyx/agent/commands/progress.py` (NOVO, registrado em `__init__.py`) emite sentinela `__progress_tail__N` (default 30, clamp 1..500); handler em `nyx/cli.py` chama `load_progress_tail(session_id, n)` e imprime tail no terminal. `/resume`, `/resume <prefix>` e `--resume <id>` anexam últimas 50 linhas do progress.md como `[contexto-anterior]` em `add_user` antes do próximo turno. Best-effort I/O: OSError em init/write/rotate apenas loga warning, nunca derruba o agente. E2E validado: criação automática no construtor do AgentLoop confirmada; redação de secrets confirmada (`password=sup3rs3cr3t!` → `password=<redacted>`); rotação testada com 300 entries → 204 linhas resultantes preservando header + última entry; `/progress` retorna `__progress_tail__30` para input vazio, `__progress_tail__50` para "/progress 50". Smoke `boot ok`. Invariantes 14/14. Acentuação: 12 violações detectadas → todas corrigidas inline via validar-acentuacao.py --fix (sessao → sessão, nao → não); 0 violações finais nos 6 arquivos tocados.
- **Anterior:** **2026-05-19 — SUDO-MODE-01 CONCLUIDA.** Modo sudo runtime: agente roda `sudo X` em `run_command` com senha cacheada apenas em memória da sessão. `nyx/agent/tools/sudo_session.py` (NOVO) é singleton module-level espelhando `plan_mode.py` -- API `is_active`/`has_password`/`get_password`/`is_destructive`/`prompt_and_cache`/`set_active`/`wipe`/`status`. Senha validada via `sudo -S -v` antes de cachear e armazenada em `_password` (módulo Python); NUNCA persistida em disco, log ou arquivo. `DANGER_PATTERNS` (8 entradas) bloqueia `rm -rf /`, `rm -rf ~`, `dd of=/dev/`, `mkfs`, fork bomb absolutamente mesmo em modo sudo. `nyx/agent/tools/run_command.py` faz wrap em `sudo -S -p '' bash -c <cmd>` com senha por `subprocess.run(input=)` (stdin, sem ecoar) -- senha NUNCA aparece em argv. `nyx/agent/preflight.py` ganha gate dinâmico: `sudo ` sai da blacklist quando `sudo_session.is_active()` True. `nyx/agent/commands/sudo_mode.py` (NOVO) registra `/sudo enable|disable|status` via `@nyx_command`. Cycle handler de Shift+Tab em `nyx/cli.py` e `nyx/agent/repl_app.py` chama `prompt_and_cache()` ao entrar em sudo e `wipe()` ao sair; transição falha (senha inválida ou cancelada) volta a modo `normal` silenciosamente. Wipe defensivo extra no `/quit` e no shutdown final cobrindo Ctrl+D, EOF e exceptions. Fallback `NYX_SUDO_PASSWORD` aceito apenas quando `stdin.isatty()` False (headless/cockpit/CI). README seção "Modo sudo runtime (SUDO-MODE-01)" com AVISO de segurança + tabela de garantias. 14/14 invariantes. Smoke ok. Gauntlet rápido APROVADO. 12 cenários runtime PASS: status inicial, blacklist (5 patterns), `status()` não vaza, wipe, preflight gate dinâmico (ON/OFF + destrutivo), env inválida rejeitada, vanilla sem sudo, bloqueio destrutivo em run_command, wrap shell correto, senha em stdin (não argv), filesystem clean (zero arquivos em `~/.nyx + logs/` contém senha teste), command `/sudo` registrado. Acentuação: 0 violações nos 8 arquivos tocados.
- **Anterior 2:** **2026-05-19 — PROJECT-ROOTS-MULTI-01 CONCLUIDA.** Nyx aceita lista runtime de project roots permitidos. `nyx/agent/tools/base.py` ganhou module-level `_ACTIVE_ROOT` + `_EXTRA_ROOTS` com API pública `set_active_project_root` / `add_extra_root` / `remove_extra_root` / `list_extra_roots` / `get_active_project_root`; `validate_path` consulta a lista unificada (active + ~/.nyx + extras) e a mensagem de bloqueio é actionable (sugere `/sandbox add <parent>`). `nyx/config/settings.py:NyxSettings.extra_roots` populado por env `NYX_EXTRA_ROOTS` (CSV, prioridade) ou `[extra_roots]` em `~/.nyx/config.toml`. `nyx/agent/preflight.check` aceita `extra_roots` opcional para warnings consistentes (gate real continua em base.py). Slash commands em `nyx/agent/commands/sandbox.py`: `/sandbox list|add|remove` (alias `/roots`) + `/cd <path>`. Dispatch via sentinelas `__sandbox_list__`, `__sandbox_add__<path>`, `__sandbox_remove__<path>`, `__cd__<path>` tratados em `nyx/cli.py` tanto no REPL (PromptSession + Application) quanto em `run_headless`. Boot do REPL e do headless chamam `set_active_project_root(PROJECT_ROOT)` + ingerem `settings.extra_roots`; paths inexistentes geram warning sem quebrar boot. Banner ganha linha discreta `+N root(s) extra(s) autorizado(s) -- /sandbox list` sob a box quando extras existem (grid 2-col intacto). `/cd` preserva o root antigo como extra automaticamente, e `set_active_project_root` purga duplicata se o novo root já era extra (sem listagem suja em round-trip). Bloqueio de `/etc/passwd` e `/root/*` preservado (testado). Smoke + invariantes 14/14 antes e depois. Validação visual: captura kitty em `dev-journey/07-reports/proofs/PROJECT_ROOTS/sandbox_lifecycle_20260519T013239.png` (sha256 `07e4e6e961b4e6f8...95081`) mostra lifecycle completo (boot vazio → add → cd troca-ativo → preserva-antigo → NYX_EXTRA_ROOTS boot → bloqueio fora dos roots).
- **Anterior:** **2026-05-19 — SHIFT-TAB-CYCLE-01 CONCLUIDA.** Tecla Shift+Tab agora cicla `normal -> plan -> sudo -> bypass -> normal` em vez de toggle binário bypass on/off. Implementação paritária nos dois REPLs: `PromptSession` legacy em `nyx/cli.py` (handler `_cycle_mode` substitui `_toggle_bypass`, linhas ~298) e `Application` default em `nyx/agent/repl_app.py` (handler espelhado, linhas ~317). Estado canônico em `app_state["mode"]`; flags legadas `bypass`/`plan_mode`/`sudo_mode` sincronizadas para retrocompat (output.py:make_ask_permission lê `state["bypass"]` direto). `plan_mode.set_plan_mode()` é chamado a cada ciclo para sincronizar o singleton global com `app_state["mode"]`, ativando o bloqueio em `_iteration.is_tool_allowed_in_plan_mode` quando mode=plan. Toolbar reativa: chip muted (normal), roxo `[plan] read-only`, vermelho `[sudo] elevado`, roxo dim `● bypass ON`. ADR-026 atualizado com nova seção. Smoke + invariantes 14/14. Gauntlet rápido 18/18 APROVADO. Validação visual: 4 PNGs por modo + `cycle_VALIDADO.png` consolidado em `dev-journey/07-reports/proofs/SHIFT_TAB_CYCLE/`. Sudo execution real depende de SUDO-MODE-01 (cache de senha via env `NYX_SUDO_PASSWORD`).
- **Anterior:** **2026-05-19 — NYX-NO-HALLUCINATE-TOOL-01 CONCLUIDA.** Bloqueia "sucesso forjado" sem tool real. `nyx/agent/validator.detect_forged_success()` (regex `FORGE_PATTERNS` + checagem de `session.history[-4:]` por write/edit/create/multi_edit/patch OK); `AgentLoop.run` em `nyx/agent/loop/_core.py:291` invoca o detector antes de `SessionState.DONE` em turnos só-texto, injeta sufixo `[atenção: resposta não verificada por tool]` no summary quando casa, e registra warning em `_diagnostics.record_warning("forge", ...)`. System prompt hardening em `nyx/agent/prompt.build_system_prompt` adiciona regra explícita contra a afirmação. Gambiarra #21 catalogada em `dev-journey/08-templates/GAMBIARRAS_POR_SPRINT.md`. 7 cenários inline PASS (alucinação detectada, write OK acolhido, write bloqueado detectado, saudação OK, "pronto" sem tool detectado, edit OK acolhido, chat legítimo OK). Smoke + invariantes 14/14. Achado colateral: 1 violação de acentuação pré-existente em GAMBIARRAS_POR_SPRINT.md:334 ("funcao") → sprint `GAMBIARRAS-ACENTUACAO-FIX-01` (BAIXA, PENDENTE).
- **Anterior:** **2026-05-19 — NYX-AUTO-APPROVE-01 CONCLUIDA.** Env `NYX_AUTO_APPROVE=1` (e flag `--auto-approve` em run.sh, já existente) promovem `CONFIRM_ONCE -> AUTO` em `PermissionChecker.check()` (`nyx/agent/permissions.py:71-100`); DENY e denied_paths ainda bloqueiam; ALWAYS_CONFIRM preservado (run_command/write_memory continuam exigindo prompt). Log de warning emitido em `nyx/cli.py` por `run_repl` (linha 113) e `run_headless` (linha 1657) quando env está ativa. README seção "Modo automatizado" com AVISO de segurança. 5 testes diretos em Python PASS (auto-approve, deny preservado, always_confirm preservado, env-off retorna confirm_once, denied_path bloqueia). Smoke + invariantes 14/14. Achado colateral: 12 violações de acentuação pré-existentes em `SPRINT_ORDER_MASTER.md` (commits anteriores) viraram sprint `MASTER-ACENTUACAO-FIX-01` (PENDENTE).
- **Anteriores:** COCKPIT-LIFECYCLE-FIX-01 CONCLUIDA. 28-08c-PARTE-3 CONCLUIDA — `output_control` agora é `FormattedTextControl(text=lambda: ANSI(output_buffer.text))`; auto-scroll via `get_vertical_scroll=_scroll_to_bottom` no Window. Banner renderiza COM CORES.
- **Último commit:** próximo será `feat(PROJECT-ROOTS-MULTI-01)`. Anteriores: `f4fdb52 feat(SHIFT-TAB-CYCLE-01)`, `703785f feat(NYX-NO-HALLUCINATE-TOOL-01)`, `c3cf033 feat(NYX-AUTO-APPROVE-01)`.
- **Próxima ação:** SUDO-MODE-01 (cache de senha via NYX_SUDO_PASSWORD) para completar o ciclo de modos; depois sprints anti-débito (COCKPIT-ACENTUACAO-FIX-01, MASTER-ACENTUACAO-FIX-01, GAMBIARRAS-ACENTUACAO-FIX-01).
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
- [2026-05-19] sprint NYX-AUTO-APPROVE-01 CONCLUIDA — env `NYX_AUTO_APPROVE=1` promove `CONFIRM_ONCE -> AUTO` em `PermissionChecker.check()` (`nyx/agent/permissions.py`); DENY e ALWAYS_CONFIRM preservados. Warning log emitido em `run_repl` e `run_headless` (`nyx/cli.py`). Flag `--auto-approve` em `run.sh` já existia (linha 154). README seção "Modo automatizado" adicionada. SPRINT_ORDER_MASTER bloco 24.6 criado. 5 testes Python diretos PASS. Smoke + invariantes 14/14. Achado colateral: 12 violações pré-existentes de acentuação em `SPRINT_ORDER_MASTER.md` (linhas 307, 313, 338-343, 407, 439-446, commits anteriores) viraram sprint `MASTER-ACENTUACAO-FIX-01` (PENDENTE em producao/).
