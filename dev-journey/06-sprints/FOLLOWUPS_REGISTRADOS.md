# Follow-ups registrados

> Catálogo anti-débito ([[feedback_nenhum_debito]]). Cada spec da onda declara, na seção
> "Fora de escopo (anti-débito)", sprints-satélite para achados que ficaram fora do seu escopo
> principal. Este arquivo materializa esses follow-ups com ID + origem, para que nenhum fique
> só dentro de uma spec.
>
> **Status REGISTRADO** = existe, tem ID e origem, mas NÃO está na fila do gerador
> (`update_next_sprint.py`). Vira uma spec `PENDENTE` em `producao/` só quando promovido com
> evidência/decisão do dono -- mesma disciplina do catálogo de candidatos C-01..C-58 do
> `dev-journey/07-reports/AUDIT_2026_07_12.md`. Ao promover, escrever a spec, mover a linha
> daqui para o bloco da onda no `SPRINT_ORDER_MASTER.md`, e apagar a linha aqui.

## Origem

Auditoria de prontidão 2026-07-12/13 (specs 408-440, 442, 446) + bake-off de modelo.
27 follow-ups genuínos extraídos das seções "Fora de escopo" das specs, cada um verificado
como inexistente no `SPRINT_ORDER_MASTER.md`, em `concluidos/` e em `backlog/`.

## ALTA

| ID | Descrição | Spec de origem |
|----|-----------|----------------|
| GAUNTLET-PROD-PARITY-TUNE-01 | Endurecer a infra (descrições de tool, few-shots, remap) se a fase `--only tools/qualidade` cair de 100% sob o schema+prompt REAIS de produção -- decorre do achado central do bake-off (o gauntlet testava schema sintético) | SPRINT_GAUNTLET_PROD_PARITY_01.md |
| INFRA-SECRET-PATHS-EXPAND-01 | Ampliar `_is_secret_path` (`base.py`) para `.kube`, `.docker/config.json`, `.netrc` e tokens de nuvem -- lacuna de exposição de credenciais além de `.ssh`/`.gnupg`/`.aws` | SPRINT_ANALYZE_VALIDATE_PATH_01.md |

## MEDIA

| ID | Descrição | Spec de origem |
|----|-----------|----------------|
| INFRA-PROXY-STRUCTURED-503-01 | Middleware no proxy aiohttp que devolve JSON 503 estruturado quando o Ollama cai (hoje 500 cru) -- recomendado em 3 specs (413/guardrail-retry/oom); o lado-cliente já mitiga o sintoma, por isso MEDIA | SPRINT_EXEC_CONTRACT_PROXY_STATUS_BEFORE_JSON_01.md |
| INFRA-RAM-PREFLIGHT-01 | Medir `MemAvailable` no boot e ajustar/avisar `num_ctx` preventivamente (`detect_gpu.py`/`run.sh`) -- prevenção proativa de OOM, complementar ao lever reativo da 432 | SPRINT_PROXY_OOM_CPU_RAM_LEVER_01.md |
| INFRA-OLLAMA-REAP-WAIT-01 | Trocar `pkill`+sleep fixo por `pgrep` até vazio com timeout no teardown do `run.sh`, confirmando morte e liberação de VRAM do órfão | SPRINT_INFRA_PROXY_READINESS_RETRY_01.md |
| LOOP-TOOL-RESULT-DIAG-CONTRACT-01 | Generalizar o contrato do loop para anexar output+error no `add_tool_call` (6 sítios de `_iteration.py`) quando qualquer tool descartar diagnóstico em falha | SPRINT_RUN_COMMAND_ERROR_OUTPUT_01.md |
| LOOP-MEMORY-WRITE-CONFIRM-01 | `write_memory` (não-apresentável) deve confirmar a gravação na fala ("Memória gravada em <path>") sem reintroduzir escrita espúria -- achado T6 da holística | SPRINT_LOOP_FALA_COERENTE_COM_RESULTADO_01.md |
| INFRA-LLM-TOOLCALL-DEDUP-01 | Dedup estrutural de `tool_calls` duplicados em `_call_llm` (colapsar `[done, done]` antes do loop) como 2a linha de defesa da 417 | SPRINT_LOOP_GUARD_FLAGS_INTRA_BATCH_01.md |
| INFRA-TOOL-PARAM-NAME-UNIFY-01 | Unificar a convenção de nome de parâmetro entre tools (`file_path` vs `path` vs `notebook_path`) num único nome nas tools+schemas+prompt+parser | SPRINT_LOOP_NATIVE_PARAM_REMAP_01.md |
| INFRA-SYNTHETIC-MSG-TAG-01 | Marcar mensagens sintéticas com campo estrutural (`synthetic:True`) em `HistoryEntry`/`to_messages`, eliminando o reconhecimento por prefixo de texto duplicado em 4 arquivos | SPRINT_PROXY_INTENT_ON_USER_REQUEST_01.md |
| TUI-SELECT-SCREEN-ID-SANITIZE-01 | `SelectScreen` monta `id=f"opt-{value}"` sem sanitizar (`select_screen.py:63`) -> `BadIdentifier` do Textual quando o label do `ask_user` tem espaço/acento/começa com dígito ("Refatorar agora"). CRASH REAL na feature que a 429 acabou de habilitar (não cosmético) -- opção multi-palavra é o caso comum. Sanitizar o id (slug/hash) mantendo o label visível. Candidato a PROMOÇÃO IMEDIATA (avaliar no validador da Leva D). Achado do executor 429, 2026-07-20 | SPRINT_TUI_ASK_USER_PLUMBING_01.md |
| SEARCH-GREP-ERE-FALLBACK-01 | Fallback do `search` sem ripgrep usa `grep` SEM `-E` (BRE): `TODO\|FIXME` e `def \w+` retornam "Nenhum resultado" silenciosamente mesmo com matches (falso-negativo mudo, provado byte-idêntico antes/depois da 409). Na máquina-alvo da missão (sem rg) o fallback É o caminho de produção -- trocar para `grep -E` ou traduzir classes GNU antes de degradar ao fallback Python (achado do executor 409, 2026-07-20) | SPRINT_EXEC_CONTRACT_SEARCH_GLOB_OR_REGEX_01.md |
| EXEC-CONTRACT-TURN-TARGET-ANCHOR-01 | Ancorar formalmente o arquivo-alvo do turno na sessão (além de `files_modified`+basename) se surgir drift que o basename não pega (mesmo nome em pastas distintas). AMPLIADO 2026-07-20 (validador Leva B, varredura adversarial): cobrir também a face falso-POSITIVA do guard 437 -- colisão de basename: pedido cita `~/X` existente E o turno cria legitimamente arquivo NOVO in-repo com o MESMO basename -> hint falso dispara 1x (transitório pelo cap 1x/turno, a re-emissão passa; custo = 1 iteração + hint que pode desorientar o 3b) | SPRINT_EXEC_CONTRACT_PATH_DRIFT_01.md |
| TUI-CANCEL-THREAD-COOPERATIVE-01 | Cancelamento cooperativo da tool órfã de um turno já cancelado por `/cancel` (`asyncio.to_thread` não recebe `CancelledError` e roda até o fim) | SPRINT_TUI_INPUT_NO_SILENT_CANCEL_01.md |

## BAIXA

| ID | Descrição | Spec de origem |
|----|-----------|----------------|
| GAUNTLET-COMPLETO-COVERAGE-AUDIT-01 | Auditar quais das 7 fases fora do grupo `completo` faltam e por quê (`nyx_gauntlet.py:127`) | SPRINT_GAUNTLET_AS_USER_PHASE_01.md |
| GAUNTLET-MULTITURN-HISTORY-01 | Dar histórico ao `_chat_with_tools` (hoje single-shot) -- afeta só o caminho legado, não a fase de contrato real | SPRINT_GAUNTLET_AS_USER_PHASE_01.md |
| TUI-INPUT-TURN-QUEUE-01 | Fila real FIFO de turnos (guardar `pending` e despachar no `finally` de `_process_turn`) em vez de bloquear com feedback | SPRINT_TUI_INPUT_NO_SILENT_CANCEL_01.md |
| TUI-STATE-LABEL-NONTERMINAL-01 | Exibir marcador de estado para `max_iterations`/`cancelled` na TUI, paridade com `cli.py:472-479` (só ausência de rótulo, não silêncio de crash) | SPRINT_TUI_STATUS_SUMMARY_RENDER_01.md |
| INFRA-TUI-CANCEL-HTTP-ABORT-01 | Cortar mid-flight o POST de inferência ao proxy no `/cancel` (hoje o transporte segue até o timeout do servidor) | SPRINT_TUI_CANCEL_BINDING_REAL_01.md |
| TUI-ASK-USER-TIMEOUT-01 | Timeout/expiração do modal ask-user se o usuário nunca responde (hoje bloqueia indefinidamente, igual ao `input()` do REPL) | SPRINT_TUI_ASK_USER_PLUMBING_01.md |
| VALIDATOR-FORGE-PATTERNS-WIDEN-01 | Ampliar `FORGE_PATTERNS` para casar "o conteúdo é..." e outros relatos fabricados (o forge só anexa aviso; o done-guard 399 é o mecanismo correto) | SPRINT_LOOP_PROSE_DONE_GUARD_01.md |
| INFRA-PATCH-FUZZ-01 | Suporte a fuzz/offset-slack estilo `patch(1)` no apply de hunks quando o contexto casa aproximado (só se surgir demanda) | SPRINT_PATCH_HUNK_OFFSET_HONEST_01.md |
| INFRA-PRECOMMIT-SNAPSHOT-NO-DRAG-01 | Dar a `PROJECT_SNAPSHOT.md` o mesmo tratamento anti-drag de WIP do dono, se comprovado que vaza para commits de executor | SPRINT_INFRA_PRECOMMIT_NO_OWNER_WIP_01.md |
| INFRA-PROVIDER-RECOVERY-SELECTIVE-01 | Recovery seletivo de `ProviderError` por status (5xx transiente recuperável vs 4xx malformado) -- hoje fora do frozenset por decisão consciente da 420 | SPRINT_LOOP_RECOVERY_TRIGGER_PTBR_01.md |
| INFRA-UNINSTALL-SYSTEM-STORE-CLEANUP-01 | Limpar blobs órfãos do store do sistema (`~/.ollama`, `/usr/share/ollama`) no `uninstall.sh` para instalações antigas "sujas" | SPRINT_INSTALL_MODELS_STORE_UNIFY_01.md |
| INSTALL-PULL-RETRY-01 | Retomada automática do pull com retry/backoff no instalador (hoje só orienta a rodar de novo; o ollama já é idempotente) | SPRINT_INSTALL_FALHA_HONESTA_01.md |
| RUN-PULL-DISK-GUARD-01 | Guardar o re-pull de fallback do `run.sh:467` por checagem de `df` (déficit de disco), paridade com o install | SPRINT_INSTALL_FALHA_HONESTA_01.md |
| DOCS-CPU-LATENCY-BENCH-01 | Medir e publicar a latência real do 3b em CPU no README (exige rodada controlada em máquina sem GPU; não fabricar) | SPRINT_README_REQUISITOS_HONESTOS_01.md |
| DOCS-URL-PLACEHOLDERS-SWEEP-01 | Corrigir o mesmo placeholder/badge em outros docs (CONTRIBUTING, docs/) se a auditoria achar recorrência | SPRINT_README_REQUISITOS_HONESTOS_01.md |
| LOOP-RECENT-OUTPUTS-INIT-01 | Inicializar `_recent_tool_outputs` no `__init__` do AgentLoop (hoje só em `run()`, `_core.py:328`) -- `AttributeError` em qualquer caminho que execute tool sem passar por `run()`; produção sempre passa, impacto restrito a harnesses/testes (achado do executor 416, 2026-07-20) | SPRINT_LOOP_FALLBACK_GATES_PARITY_01.md |
| DOCS-MASTER-ACENTO-SWEEP-01 | Varrer as 121 violações de acentuação PRÉ-EXISTENTES do `SPRINT_ORDER_MASTER.md` (linhas ~512-1197, prosa histórica: "canonico"/"usuario"/"secao" etc.) numa sprint de higiene dedicada -- flagadas por 3 executores seguidos (406/425/424, 2026-07-20) e conhecidas desde 2026-07-13; grandes demais para absorção cirúrgica em sprint de código; usar `sanitize_spec_acentuacao.py` com cuidado com paths (`producao/` já foi sobre-corrigido uma vez) | (débito histórico do MASTER, sem spec de origem) |

---

*31 follow-ups (2 ALTA, 12 MEDIA, 17 BAIXA). Promover com evidência; nunca absorver em silêncio.*
