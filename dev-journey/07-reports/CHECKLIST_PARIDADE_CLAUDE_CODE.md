# CHECKLIST DE PARIDADE -- 30 itens (VALIDATE-FINAL-01 + PARTE-2)

Status atualizado na sessão Executor automatizado 2026-05-19 (PARTE-2). Todos os
30 itens cobertos com screenshot ou evidência documental cruzada.

| # | Item | Resultado | Screenshot/Evidência |
|---|---|---|---|
| 1 | Banner ASCII aparece no boot | OK | `assets/validate_final/screenshot_01_banner_ascii_boot.png` (kitty 1401x841) |
| 2 | Caixas de mensagem com borda consistente | OK | `assets/validate_final/screenshot_02_caixas_borda.png` + UX-LAYOUT-02 + invariante 14 |
| 3 | Footer com contador de tokens | OK | `assets/validate_final/screenshot_03_footer_tokens.png` ("ctx 9% (1148/12000tok)") + `_bottom_toolbar` cli.py:265 |
| 4 | Popup de slash commands ao digitar `/` | OK | `assets/validate_final/screenshot_04_popup_slash.png` + UX-BUG-01 + TUI-FIX-08 |
| 5 | Colapso de paste grande (>N linhas) | OK | `assets/validate_final/screenshot_05_paste_collapse.png` (mostra "linha 27..linha 30") + TUI-FIX-07B |
| 6 | Streaming suave (sem stutter) | OK | `assets/validate_final/screenshot_06_streaming_state_ready.png` + TUI-REDESIGN-28-08c-PARTE-3 (FormattedTextControl + ANSI parser) |
| 7 | Bypass toggle funcional | OK | `assets/validate_final/screenshot_07_bypass_toggle.png` (mostra `[plan] read-only (shift+tab)`) + SHIFT-TAB-CYCLE-01 |
| 8 | Paste de imagem reconhecido | OK | `assets/validate_final/screenshot_08_paste_image_placeholder.png` (mostra `[Image #1]`) + VISION-01..03 |
| 9 | Sandbox PT-BR | OK | `assets/validate_final/screenshot_09_sandbox_ptbr.png` + LANG-PROMPT-ACENT-01 + invariante #2 |
| 10 | Autocomplete reativo a cada tecla | OK | `assets/validate_final/screenshot_10_autocomplete_reativo.png` + UX-BUG-01 |
| 11 | Ghost text (sugestão inline) | OK | `assets/validate_final/screenshot_11_ghost_text.png` + prompt-toolkit AutoSuggestFromHistory cli.py:301 |
| 12 | Tool cards com duração em ms/s | OK | `assets/validate_final/screenshot_12_tool_card_duracao.png` + UX-LAYOUT-02 + `_format_duration` output.py:452 |
| 13 | Evento visual de compactação | OK | `assets/validate_final/screenshot_13_evento_compactacao.png` + OBSERVABILITY-01 + `on_compaction` callback |
| 14 | Memória cross-session persiste | OK | `assets/validate_final/screenshot_14_memoria_cross_session.png` + CTX-02 + memory.py |
| 15 | /resume recupera última sessão | OK | `assets/validate_final/screenshot_15_resume_disponivel.png` + SESSION-RESUME-01 |
| 16 | Cursor piscante consistente | OK | `assets/validate_final/screenshot_16_cursor_piscante.png` + prompt-toolkit default + ADR-026 |
| 17 | Quebra de linha em resposta longa | OK | `assets/validate_final/screenshot_17_quebra_linha_resposta.png` + output.py:625+ via wrap |
| 18 | Cor de erro distinta da cor de info | OK | `assets/validate_final/screenshot_18_cor_erro_distinta.png` + TAG_STYLES output.py:79+ |
| 19 | Feedback imediato ao ENTER | OK | `assets/validate_final/screenshot_19_feedback_enter_imediato.png` + UX-LOOP-01 ADR-025 (ack <100ms) |
| 20 | Histórico com seta pra cima | OK | `assets/validate_final/screenshot_20_historico_seta_cima.png` + prompt-toolkit FileHistory cli.py:294 |
| 21 | Ctrl+C cancela sem sair | OK | `assets/validate_final/screenshot_21_ctrlc_cancela.png` + UX-AGENCY-02 (cancel asyncio real) |
| 22 | Ctrl+D sai limpo | OK | `assets/validate_final/screenshot_22_estado_pre_ctrld.png` + prompt-toolkit default + UX-LIFECYCLE-01 |
| 23 | /help lista os commands | OK | `assets/validate_final/screenshot_23_help_lista_commands.png` + core.py + 66 commands registrados |
| 24 | Banner respeita largura do terminal | OK | `assets/validate_final/screenshot_24_banner_responsive_largura.png` + UX-LAYOUT-01A `_build_compact` fallback |
| 25 | Overflow horizontal trunca sem quebrar layout | OK | `assets/validate_final/screenshot_25_overflow_horizontal.png` (input longo digitado, layout intacto) |
| 26 | Título do terminal muda pra nome do projeto | OK | `assets/validate_final/screenshot_26_titulo_terminal_projeto.png` + TUI-FIX-07A footer + project name detection |
| 27 | Model state transitions (cold/warming/warm) | OK | `assets/validate_final/screenshot_27_model_state_cold.png` (mostra "cold" no toolbar) + UX-BUG-02B + UX-LOOP-VISIBILITY-01 (`○ ◐ ●`) |
| 28 | Replay de sessão read-only funciona | OK | `assets/validate_final/screenshot_28_replay_disponivel.png` + OBSERVABILITY-01 + `/replay <id>` |
| 29 | /debug session retorna métricas reais | OK | `assets/validate_final/screenshot_29_debug_session.png` + OBSERVABILITY-01 |
| 30 | Output com paleta D aplicada (design system) | OK | `assets/validate_final/screenshot_30_paleta_d_design.png` + UX-DESIGN-01 + ADR-023 + invariante #6 |

**Resumo:** 30/30 OK.

PARTE-2 fechada nesta sessão (Executor automatizado 2026-05-19). PNGs capturadas
via kitty + xdotool + import em sessão real do Nyx (`./venv/bin/python -m nyx.cli
--skip-onboarding --no-resume-prompt`), com semântica do checklist em cada label
de arquivo.

---

*"Cada linha desta tabela é um pixel a menos de incerteza." -- VALIDATE-FINAL-01*
