# Changelog

Todas as mudanças notáveis neste projeto serão documentadas neste arquivo.

O formato é baseado em [Keep a Changelog](https://keepachangelog.com/pt-BR/1.0.0/),
e este projeto adere ao [Versionamento Semântico](https://semver.org/lang/pt-BR/).

## [1.3.1] - 2026-05-31

ONDA-35: correções de UX da TUI descobertas ao USAR a interface de verdade (digitando), que a validação por injeção (`/control/repl/send`) havia mascarado. Todas validadas digitando de verdade (Textual Pilot + `--web` via playwright `page.keyboard`). Invariantes 14/14, gauntlet `--only rapido` APROVADO por sprint.

### Corrigido

- **Autofoco do input** (`TUI-INPUT-AUTOFOCUS-01`) — ao abrir, o input já fica focado: `term.focus()` no xterm.js (abertura, conexão e resize) resolve o caso `--web` (as teclas do browser só chegavam ao PTY após clicar); `call_after_refresh` reforça o foco no nível Textual. Digitar passa a funcionar imediatamente, sem clique.
- **Input de 5 linhas fixas sem corte** (`TUI-INPUT-HEIGHT-5-SCROLL-01`) — altura fixa (5 linhas de conteúdo + borda) com scrollbar interna no Ctrl+J; input e toolbar agrupados num container `#bottombar` (um único `dock:bottom`), eliminando o corte da borda inferior pela toolbar.
- **Scroll da conversa + fim do travamento** (`TUI-CONVERSATION-SCROLL-TEXTUAL-01`) — re-porta o scroll perdido na migração ONDA-32: PgUp/PgDn rolam a conversa mesmo com o input focado e a roda do mouse funciona; o auto-scroll não puxa de volta ao fim enquanto se lê o histórico. O travamento era o streaming re-parseando o Markdown inteiro a cada token (O(n^2): ~1.6k caracteres levavam ~75s e 3253 parses) — agora o texto renderiza plano durante o stream e vira Markdown uma única vez ao assentar (2 parses).
- **Modos Shift+Tab com comportamento real** (`TUI-MODE-BEHAVIOR-01`) — antes só mudavam o rótulo. Agora: **plan** = somente leitura (bloqueia escrita, só explora e planeja), **sudo** = elevação real (SUDO-MODE-01), **bypass** = auto-aprovar permissões (CONFIRM_ONCE; DENY e ALWAYS_CONFIRM seguem pedindo). Modos exclusivos; boot reseta para normal.
- **Resposta final limpa** (`TUI-DONE-SUMMARY-CLEAN-01`) — quando o modelo emite `done(summary="...")` como texto, o balão exibe o summary limpo, não a sintaxe crua.
- **Capitalização** — footer da TUI (`TUI-FOOTER-CAPITALIZE-TERMS-01`: Cold/Warming/Warm, Shift+Tab e nomes dos modos) e chrome do cockpit (`COCKPIT-CHROME-CAPITALIZE-01`: Cockpit / Terminal, Dashboard, Conectado, hint do rodapé).

## [1.3.0] - 2026-05-30

Migração da TUI de prompt_toolkit para Textual (ONDA-32) + redesign completo da interface interativa a partir de uma auditoria de UX (ONDA-34, sprints 283-301). Toda a matriz de auditoria resolvida (features, higiene e decisões). Invariantes 14/14 PASS, gauntlet `--only rapido` APROVADO re-validado por sprint; as features de UI foram validadas via Textual Pilot (headless, sem OOM).

### Adicionado

- **Markdown + syntax highlight no chat** (`TUI-CHAT-MARKDOWN-SYNTAX-01`) — o conteúdo do NyxCode renderiza como Markdown; blocos ` ``` ` ganham syntax highlight (Rich/pygments, tema Monokai), listas e ênfase formatadas.
- **Bloco de raciocínio recolhível** (`TUI-THINKING-EXPAND-01`) — o reasoning do modelo (`think=true`), antes dropado na TUI Textual, volta como `Collapsible` recolhido ("◐ pensando"); expand/collapse nativo (clique no título ou foco+Enter), sem reusar o Tab.
- **Copiar bloco de código** (`TUI-CODE-COPY-BUTTON-01`) — `Ctrl+Y` copia o último bloco ` ``` ` da última resposta para a área de transferência via OSC52 (funciona no terminal e no `--web`/xterm.js).
- **Banner rolável** (`TUI-BANNER-SCROLLABLE-01`) — o banner deixa de ser fixo (`dock:top`) e vira o 1º filho do `#chat`, rolando junto com a conversa.
- **Labels nominais + cores no chat** (`TUI-CHAT-LABELS-COLORS-01`) — mensagens do usuário ganham label com o nome (via `resolve_user_display_name`); o NOME leva a cor de destaque da role e o CONTEÚDO fica em `$foreground` (neutro).
- **Histórico de inputs navegável** (`TUI-INPUT-HISTORY-NAV-01`) — `Ctrl+Up`/`Ctrl+Down` percorrem submissões anteriores (preservando rascunho), sem colidir com o cursor multiline.
- **Input multiline** (`TUI-INPUT-TEXTAREA-MULTILINE-01`) — base migrada de `Input` para `TextArea`: `Enter` envia, `Ctrl+J` insere nova linha, `Tab` aceita a sugestão ghost.
- **Slash completer ghost-inline** (`TUI-SLASH-COMPLETER-POPULATE-01`) — digitar `/` mostra sugestão dim do comando (67 comandos), `Tab` aceita.
- **VRAM ao vivo no rodapé** (`TUI-FOOTER-VRAM-REALTIME-01`) — a toolbar mostra a VRAM em tempo real (nvidia-smi, polling 2s, degradação graciosa).
- **Contador de imagem colada** (`TUI-IMAGE-PASTE-COUNTER-01`) — paste de imagem vira `[Image #N]` incremental.

### Mudado

- **TUI migrada de prompt_toolkit para Textual** (ONDA-32, `TUI-DEFAULT-FLIP-LEGACY-RM-01`) — a stack prompt_toolkit (incluindo `nyx/agent/repl_app.py`) foi removida; a interface passa a ser uma única TUI Textual, espelhada no `--web` via PTY + xterm.js.
- **Ghost "◆ NyxCode" eliminado por lazy-mount** (`TUI-NYXCODE-GHOST-LAZY-MOUNT-01`) — o balão do assistant só monta no 1º token, sem fantasma vazio entre o envio e a resposta.
- **Footer capitalizado** (`TUI-FOOTER-CAPITALIZATION-01`) — Ctx/Iter/Lidos/Modif.
- **CSS do input saneado** (`TUI-INPUT-CSS-SANITIZE-01`) — remove seletores mortos e unifica a altura.

### Corrigido

- **`--web` destravado** — boot-race do pid-file (`TUI-FIX-WEB-PIDFILE-BOOT-RACE-01`), prompt de resume bloqueante (`-RESUME-PROMPT-BLOCKS-01`), reap de sessão anterior (`-SESSION-REAP-01`) e empilhamento do input no resize (`-RESIZE-TILING-01`: recriar o Terminal do xterm.js já no tamanho-alvo).
- **Ponte agent↔Textual** — loop-affinity do httpx (`TUI-FIX-HTTPX-LOOP-AFFINITY-01`), relayout do streaming (`-CHATMESSAGE-RELAYOUT-01`), foco no input ao montar (`-INPUT-FOCUS-ON-MOUNT-01`).

### Higiene (anti-débito)

- Auditoria de `nyx/agent/output.py`: 4 funções `render_*` mortas (pré-Textual) marcadas `[MORTO]` sem deletar (GUIDE #3); 2 falso-positivos vivos no gauntlet preservados.
- Acentuação de docstrings/comentários legados de `app.py`; `VALIDATOR_BRIEF.md` sincronizado com a realidade pós-Textual (referência stale a `repl_app.py` removida do protocolo anti-sanitizer).
- Decisões registradas: status-line (redundante com toolbar + lazy-mount) e ADR-022 (já resolvido na dedup da sprint 261).

## [1.3.0-rc2] - 2026-05-21

Drena os 5 anti-débitos catalogados na rc1 + materializa 4 achados colaterais novos da pipeline. Backlog técnico zerado antes da decisão humana de cortar `v1.0`. Working tree limpo, invariantes 14/14 PASS, gauntlet `--only proxy` 7/7 + `--only qualidade` 5/5 re-validados em cada sprint.

### Adicionado

- **scripts/dispatch_pre_check.sh** (`INFRA-VALIDATOR-PRE-DISPATCH-RECHECK-01`, commit `d44bdf7`) — wrapper bash que parseia `acceptance_criteria` de specs e emite `PRE-SATISFEITA` quando todos critérios parseáveis já estão em verde antes do dispatch. Evita ciclo executor+validador para sprints redundantes (caso empírico: `MASTER-IDS-DEDUP-02` pre-satisfeita por commit `df1a8d9`). Mawk-compatible (não exige gawk).
- **scripts/gauntlet/nyx_gauntlet.py P-09b gated** (`INFRA-GAUNTLET-E2E-THINKING-01`, commit `6566d5f`) — teste E2E real do path `proxy  ollama  nyx_reasoning` ativado por flag `--with-qwen3` + VRAM check (skip se < 4GB). Default sem flag mantém gauntlet `--only proxy` 7/7 (100%) sem regressão.
- **dev-journey/08-templates/SPRINT_TEMPLATE_V2.md seção "Antes/Depois com trecho"** (`INFRA-PLANEJADOR-CODE-EXCERPT-IN-SPECS-01`, commit `801a0dd`) — exige fenced code block (≥3 linhas) em specs `type: Refactor` cirúrgico com `touches.length == 1`. Lição empírica: BUNDLE-01 teve 2/3 fixes com número de linha errado; texto-alvo inequívoco salvou.

### Mudado

- **nyx/agent/output.py `_strip_ansi` → `_visible_len`** (`OUTPUT-VISIBLE-LEN-RENAME-01`, commit `522fed0`) — rename semântico (função retorna `int` de largura visível, não `str`). Alias `_strip_ansi = _visible_len` preservado para retro-compat dos 4 callsites internos.
- **scripts/gauntlet/nyx_gauntlet.py** (`INFRA-GAUNTLET-CLEANUP-BUNDLE-01`, commit `ae004ac`) — bundle anti-débito que consolida 3 fixes: `PROJECT_ROOT` via `parents[2]`, 2 `print()` → `logger.info()`, literais hardcoded `"qwen"`/`"alibaba"` → `mentions_provider()` de `nyx.agent.lang_check`. FIX-4 (`HARDCODED-PATHS`) DESCARTADO por alvo inexistente.
- **dev-journey/06-sprints/SPRINT_ORDER_MASTER.md IDs renumerados** (`MASTER-IDS-DEDUP-01`, commit `b2f0054`) — 22 IDs numéricos duplicados pós-150 renumerados para série 200+ preservando chaves textuais e IDs históricos pré-150. Mapeamento: 110-115→200-205, 128b→206, 146-159→207-220, 162→221.
- **dev-journey/06-sprints/SPRINT_ORDER_MASTER.md entry MCP-SERVER-03 desduplicada** (`MASTER-ENTRY-DEDUP-MCP-SERVER-03-01`, commit `7144786`) — 2 entries da mesma sprint consolidadas em 1 (linha 128b canônica com hash `5e1927e` preservada; linha 206 redundante removida).

### Corrigido

- **dev-journey/06-sprints/producao/SPRINT_INFRA_GAUNTLET_CLEANUP_BUNDLE_01.md** (`BUNDLE-01 spec`, commit `8d4dd0c`) — comando `python3 -m ruff check` substituído por `/home/andrefarias/.local/bin/ruff check` conforme `VALIDATOR_BRIEF` linha 37 (ruff não está como módulo Python no venv).

### Status do backlog (ZERADO)

- 10 sprints CONCLUIDA: 125qq/rr/ss/ww/oo/tt/vv/xx/yy + housekeeping consolidado
- 1 SUPERSEDED: 125uu (pyproject.toml já tinha `external = ["noqa-acento"]` desde commit `3727cb6`)
- 1 DESCARTADA: 125pp (alvo inexistente)
- 3 CONSOLIDADAS: 125ll/mm/nn (absorvidas pelo BUNDLE)
- 1 DEFERIDA: 125zz `INFRA-COMMIT-HOOK-FILTER-01` (escopo externo, hook do usuário fora do projeto Nyx)

### Adicionado (extensão rc2)

- **scripts/dispatch_pre_check.sh fenced-block check** (`INFRA-PLANEJADOR-FENCED-CHECK-01`, commit `a8eecb3`) — bloco +32L que rejeita spec `type: Refactor` com `touches.length == 1` sem fenced code block (threshold ` ``` ` >=4: 2 do YAML + 2 do bloco extra). Exit code 3 distintivo. Mawk-compatible. Complementa 125xx (template) com check executável.

### Notas

- Tag `v1.0` permanece **NÃO cortada** — decisão delegada ao humano. Sprint `RELEASE-V1.0-CUT-01` em `producao/`.
- Próximo passo natural: `git tag -a v1.0 -m "Release v1.0: Claude Code offline opensource"` + `git push origin v1.0`. <!-- noqa-anonimato -->

---

## [1.3.0-rc1] - 2026-05-21

Release candidate cobrindo as Ondas 22 a 28: stack OOM consolidada, MCP/Plugin/Hook integrados ao ToolRegistry, redesign completo da TUI, cockpit web, aesthetics extensíveis, e ~70 sprints concluídas desde 1.2.0. Gauntlet 220/220 (100%) APROVADO em 252s. Tag `v1.0` permanece **NÃO cortada** — decisão delegada ao humano.

### Adicionado

- **Stack OOM resiliente (Ondas 22-25)** — sistema de degradação progressiva com 5 níveis quando GPU satura
  - INFRA-OOM-01/02: detecção via `_OOM_PATTERNS` (9 strings incluindo "kv cache" e "GGML_ASSERT", consolidação 2026-05-21), retry CPU automático com `num_gpu` decrescente
  - INFRA-OOM-HISTORY-01: persistência cross-session em `~/.nyx/proxy_stats.json` (schema v1, escrita atômica via tmp + os.replace, hidratação no boot, contrato `/admin/stats` em 4 chaves)
  - INFRA-OOM-RETRY-STEP-01 + INFRA-OOM-STATS-CLI-01: novo slash `/stats` cliente do endpoint `/admin/stats`; RB-01..RB-06 cobertos pelo gauntlet
  - INFRA-OOM-PATTERNS-KV-CACHE-01: cobertura adicional para erros llama.cpp recentes

- **MCP / Plugin / Hook stack (Onda 23)** — feature parity com Claude Code <!-- noqa-anonimato -->
  - MCP-SERVER-01/02/03: HTTP loopback transport (httpx async em 127.0.0.1 estrito), `ToolRegistry._load_mcp_tools()` com prefix `mcp_<server>_<tool>`, `McpToolAdapter` herda `RegisteredTool`, novo `ActionType.MCP_TOOL` em models
  - PLUGINS-01/02/03: descoberta automática + integração `_load_plugin_tools()` no boot, fallback tolerante quando sem plugins
  - HOOKS-DYNAMIC-01/02/03: `HookRuntime` amarrado ao `AgentLoop` em 4 eventos (pre-tool, post-tool, pre-prompt, post-prompt), plugins podem registrar hooks via @nyx_hook

- **Redesign TUI completo (Ondas 24-26)** — fidelidade visual com aesthetics extensíveis
  - TUI-REDESIGN-25-01..25-12: capitalização + acentuação PT-BR + thinking block recolhível + parser + side-rule streaming
  - TUI-REDESIGN-25-09-PARTE-3 (2026-05-21): captura real do thinking via `nyx_reasoning` em `choices[0].message`; callback `_on_thinking` propaga
  - TUI-REDESIGN-25-12-PARTE-2 (2026-05-21): amarra `_on_thinking` ao `render_thinking_block` (default colapsado, Tab expande)
  - TUI-REDESIGN-26-01..26-04: glyph-per-tool, tool chips com layout 2-col
  - TUI-REDESIGN-26-03-PARTE-2-DEFAULT-PAD (2026-05-21): pad dinâmico via `shutil.get_terminal_size`; duration+status alinhados à direita também sem `error_actions`
  - Banner duas camadas (VISUAL-LAYOUT-09): aesthetic provê estrutura (glyphs+cantos), entity provê accent textual (ADR-029)

- **Cockpit web (Onda 26)** — supervisor visual em browser
  - COCKPIT-WEB-01..05: FastAPI + WebSocket + xterm.js embed
  - PTY-PERMISSION-FLOW-01: overlay modal para aprovar permissões `CONFIRM_ONCE` do PTY (yes/yes_always/no), regex anti-injeção em `/permissions add <tool>`
  - PTY-EMBEDDED-REPL-01..03: REPL embarcado via PTY com clipboard sync

- **Aesthetics showcase (Onda 24)** — 5 aesthetics consumíveis
  - VISUAL-LAYOUT-06: cyberpunk, brutalist, mecha, editorial + arcano (showcase) + default; cada uma com paleta + glyphs próprios
  - Banner ganha consumo de `current_glyphs()` em build-time preservando `current_ansi()` em import-time

- **Identity + Language enforce (Onda 27)** — defesa em profundidade contra vazamento de modelo
  - IDENTITY-ENFORCE-01: espelho de LANG-ENFORCE; novo `mentions_provider(text)` em `lang_check.py` cobrindo 13 providers; word boundary customizado aceita "Qwen2.5"; retry 1x com hint anti-vazamento
  - MEMORY-INTENT-ENFORCE-01: 3 camadas (`wants_save_memory` 9 padrões PT-BR + guardrail re-issue + parser shell-like fallback)
  - LANG-ENFORCE-01..03: detecção PT-BR vs EN; retry com hint quando modelo responde no idioma errado

- **Sudo session + GSD (Ondas 22-24)** — privilege management
  - SUDO-SESSION-01..03: cache de sudo session com prompt único por sessão
  - SECRET-MIGRATE-01: migração de secrets legados para `~/.config/nyx/secrets/`
  - GSD-A/B/C: GitOps Self-Documenting (ActivePlan + render_active_plan_block + /plan command com 5 subcomandos)

- **CTX continuous memory (Onda 24)**
  - CTX-01..04: memory persistente cross-session, `/plan` checklist via `nyx/agent/active_plan.py` (singleton + write-through ~/.nyx/active_plan.md)

- **CLI refactor monolítico → modular (Onda 25)**
  - INFRA-CLI-SPLIT-01/02/03: `nyx/cli.py` 2223L → 792L extraindo `cli_headless.py` (298L), `cli_boot.py` (263L), `cli_callbacks.py` (150L), `cli_keybindings.py` (328L), `cli_handlers.py` (950L); meta GUIDE.md §6 `<800L` atingida

- **Onboarding wizard (Onda 26)**
  - REPL onboarding flow com nome + sandbox + aesthetic + GPU autotune
  - INSTALL-SUDO-01 + INSTALL-ZSTD-FALLBACK-01: install.sh robusto com fallback de unpacker

- **Gauntlet endurecido (Ondas 22-28)** — 220 testes em 53 fases
  - Cobertura: proxy (P-01..P-09), interface (I-01..I-13), tools (T-01..T-10), CTX (CTX-01..14), portabilidade, robustez_boot (RB-01..06), MCP (M-01..05), plugins, hooks_dynamic, vision, sessão, install, mcp, p11_infra, p10_root
  - INFRA-GAUNTLET-AUTO-SCAFFOLD: descoberta automática de novos comandos
  - GAUNTLET-FIXTURES-SANDBOX-01: fixtures em `~/.nyx/gauntlet_tmp/`
  - K08-VRAM-RUNNER-ISOLATION-01: runner com `scripts/vram_check.py` + 3 flags
  - Tempo total: ~252s no RTX 3050 4GB

- **Branding nyx  luna** — separação clara
  - branding: glifo nyx/luna conforme modo de operação

### Mudado

- **ADR-031**: modelo padrão muda de `qwen3:4b` (thinking, vaza CoT em inglês) para `qwen2.5-coder:3b` (non-thinking, melhor tool calling); pilha de infra do Nyx eleva non-thinking compatíveis a score 96.8 (vs qwen3 score 34.6 com mesma infra)
- **ADR-029**: `entity` sobrescreve `accent` em import-time (intencional para coerência visual)
- **ADR-024**: `print()` permitido apenas em `cli*.py` / `output.py`; glob ampliado em `INFRA-CLI-SPLIT-02`
- **ADR-013**: integração obrigatória — tools em ToolRegistry, commands `@nyx_command`, testes só via Gauntlet
- **Invariantes 13 → 14**: novo check #14 (defesa anti-sanitizer) endurecido em INFRA-SANITIZER-FIX-01..05 usando `chr(0x25CB)` / `chr(0x25D0)` / `chr(0x25CF)` / `chr(0x25C6)` para impossibilitar auto-neutralização por sanitizer
- **Sanitizer universal** (`~/.config/zsh/scripts/universal-sanitizer.py`): preserva glifos via `ALLOWED_GLYPHS` (○ ◐ ● ◆ ◇ ▶ ▼ ▸ ◼ ◻ ↗); pre-commit hook hardened
- **VALIDATOR_BRIEF.md**: 14 lições empíricas catalogadas; auto-invocação de skill validação-visual quando diff toca UI; protocolo anti-débito rigoroso
- **Defaults**: warmup on boot, proxy think adaptativo, log levels suprimidos no smoke

### Corrigido

- **NYX-OUTPUT-LIMITS-01**: log warning passivo se resposta parece truncada
- **HOTFIX-GLYPHS-01**: glifos `▶` / `▼` no thinking block (eram fallback ASCII)
- **BANNER-TOOLS-COUNT-01**: contagem de tools no banner via `len(list_tools())` dinâmico
- **TUI-FIX-08/09/10**: artefatos de scroll, capacidade de paste collapse, render race
- **TUI-INPUT-HEIGHT**: altura mínima respeitada
- **TUI-POPUP-META-01**: metadados do popup
- **UX-BUG-02C / 03**: pequenos polish de UX
- **UX-LAYOUT-03**: alinhamento corrigido
- **UX-COCKPIT-EXPERIENCE-01**: melhorias no cockpit
- **DEPLOY-02**: pipeline corrigido
- **PROXY-NUMGPU-RUNTIME-01**: num_gpu honrado em runtime
- **TUI-SHUTDOWN-SILENT-01**: shutdown sem ruído
- **HELP-COVERAGE-FIX-01**: cobertura do `/help` (66 → 67 commands)
- **CHECKPOINT-ACENTUACAO-FIX-01**: 21 violações de acentuação em Checkpoint.md
- **GAUNTLET-LOOP-PY-REF-FIX-01**: `loop.py` virou pacote, gauntlet atualizado
- **GAUNTLET-ACENTUACAO-FIX-01**: 13 violações em nyx_gauntlet.py
- **GAUNTLET-TOOLS-DESC-MATCH-01**: cross-validation contra alucinação `"Read Lê arquivo"` do modelo
- **GAUNTLET-RB05-CAP-FIX-01**: cap-counter robusto via indentação
- **GAUNTLET-SYNC-02-RECOVER-01**: aceita 4 formas de mensagem
- **INFRA-RUFF-NOQA-FORMAT-01**: 7 warnings `Invalid noqa directive` silenciados
- **INFRA-VALIDATE-ACENTUACAO-CLI-FIX-01**: padroniza `--paths` em templates
- **INFRA-PLANEJADOR-ACENTUACAO-AUTO-01**: defesa 2-camadas PT-BR no planejador-sprint (template global + sanitizer local)
- **MASTER-CLEANUP-01/02**: 168 specs em concluidos/ com header dessincronizado fixados em batch

### Removido

- Stubs e código morto detectados em PROD cleanup
- Funções `render_tool_card_compact` / `render_tool_card_done` (renomeadas para `render_tool_chip` em TUI-REDESIGN-25-10)

### Segurança

- **PTY-PERMISSION-FLOW-01**: sanitização anti-injeção em `/permissions add <tool>` (regex `[A-Za-z_][A-Za-z0-9_]*`)
- **MCP HTTP transport**: rejeita explicitamente `0.0.0.0` / IP-público / DNS; aceita apenas `127.0.0.1` / `localhost` / `::1` (loopback estrito)
- **Sudo session**: cache em memória apenas, nunca persistido em disco
- **Defesa anti-sanitizer**: invariante #14 endurecido contra auto-neutralização do defensor

### Notas técnicas

- **368 sprints CONCLUIDAS** acumuladas no MASTER (`dev-journey/06-sprints/SPRINT_ORDER_MASTER.md`)
- **5 anti-débitos PENDENTES** catalogados (125oo..125ss) para follow-up controlado
- **6 docs canônicos write-through**: PROJECT_SNAPSHOT (STATE), SPRINT_ORDER_MASTER (ROADMAP), CHANGELOG (este), REGISTRY.yaml + FEATURE_MAP.md (FEATURES), VALIDATOR_BRIEF (lições), Checkpoint.md (working state untracked)
- **Hardware testado**: RTX 3050 Laptop 4GB VRAM, num_gpu=12, num_ctx=8192
- **Modelo padrão**: qwen2.5-coder:3b (Ollama)

## [1.2.0] - 2026-04-16

### Adicionado
- **Onda 18 -- Portabilidade** (3 sprints concluídas)
  - PORT-01: auto-tune de GPU em `scripts/detect_gpu.py` (detecta VRAM e calcula num_gpu ideal por modelo); flag `NYX_AUTO_TUNE` em `.env.example`; integrado em `install.sh` e `run.sh`
  - PORT-02: harness Docker `docker/Dockerfile.clean-boot` + `docker/test-clean-boot.sh` para validar boot em máquina limpa; `install.sh --no-prompt` para execução não-interativa; seção "Portabilidade" no README
  - PORT-03: robustez de boot -- mensagens claras em `run.sh` para modelo inexistente (R-02) e porta ocupada (R-03); graceful degradation de OOM no `nyx/proxy.py` (R-04) com retry CPU automático
- 8 testes novos no Gauntlet (fases `gpu_tune`, `portabilidade`, `robustez_boot`)
- R-02/R-03/R-04 removidos de `UNMAPPED_FEATURES`

### Corrigido
- `nyx/proxy.py` auto-suficiente como script direto (issue #5): `sys.path.insert` permite `python nyx/proxy.py` e `python -m nyx.proxy`

### Integração
- **Onda 19 (Luna)** delegada ao repo externo. Sprints I-02 e I-03 marcadas DELEGADA; 4 sprints novas criadas em `Luna/dev-journey/06-sprints/producao/infra/` (INFRA-50 a 53) com código pronto pra copiar: bootstrap, NyxAdapter (IPC subprocess headless), refactor do code_agent, bloco inline na TUI

## [1.1.1] - 2025-10-01

### Adicionado
- Licença GPLv3
- Código de Conduta (Contributor Covenant v2.1)
- Política de Segurança (SECURITY.md)
- Guia de contribuição (CONTRIBUTING.md)
- Templates de issue e PR para GitHub
- Changelog completo
- .mailmap para unificação de identidade git

### Corrigido
- README atualizado com contagens corretas (47 commands, 10 services)
- pyproject.toml modernizado com build-system, classifiers e URLs
- CI com trigger de push para main

## [1.1.0] - 2025-08-15

### Adicionado
- Anti-OOM com auto-recovery para GPU limitada
- Parser robusto para GPU limitada
- Blindagem da infraestrutura (5 fixes para compensar modelo fraco)

### Corrigido
- Proxy think adaptativo (habilitar think quando há tools)
- Limpeza PROD: stubs removidos, boot corrigido, commands reais implementados
- Timeout LLM aumentado para 600s (hardware lento)

## [1.0.0] - 2025-05-01

### Adicionado
- Port completo ondas 10-16 do Claude Code TS (127K linhas → Python) <!-- noqa-anonimato -->
- Identidade visual Dracula Gothic + 20 ADRs
- Documentação completa e reorganização (dev-journey/)
- Proxy para tool calling funcional com modelo local

### Corrigido
- Proxy normaliza content array para string Ollama
- Auditoria completa de acentuação, cores e integração

## [0.5.0] - 2025-01-15

### Adicionado
- Agente funcional com REPL interativo (prompt-toolkit + Rich)
- 34 tools via ToolRegistry
- 47 slash commands
- Proxy think=false para tool calling nativo
- E2E completo (6 tools + 26 slash commands testados)
- Simulação de usuário real com resultados honestos

## [0.1.0] - 2024-08-01

### Adicionado
- Estrutura inicial do projeto Nyx-Code
- Integração com Ollama (porta 11435)
- Seleção de modelo (qwen3:4b como padrão, tool calling nativo)
- Scripts install.sh, run.sh e uninstall.sh
- Interface funcional restaurada
- Suporte GPU via Ollama do sistema
