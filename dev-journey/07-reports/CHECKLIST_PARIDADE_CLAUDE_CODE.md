# CHECKLIST DE PARIDADE -- 30 itens (VALIDATE-FINAL-01)

Status preenchido na sessão Validador 2026-05-18. Itens marcados PENDENTE
exigem captura visual em sessão humana (anti-débito VALIDATE-FINAL-01-PARTE-2).

| # | Item | Resultado | Screenshot/Evidência |
|---|---|---|---|
| 1 | Banner ASCII aparece no boot | PENDENTE | aguarda scrot em sessão humana |
| 2 | Caixas de mensagem com borda consistente | OK | UX-LAYOUT-02 + glifo `╭╮╰╯` invariante #14 |
| 3 | Footer com contador de tokens | OK | `_bottom_toolbar` em cli.py:265 (`ctx X%`) |
| 4 | Popup de slash commands ao digitar `/` | OK | UX-BUG-01 + TUI-FIX-08 |
| 5 | Colapso de paste grande (>N linhas) | OK | TUI-FIX-07B |
| 6 | Streaming suave (sem stutter) | PENDENTE | aguarda observação visual |
| 7 | Bypass toggle funcional | OK | UX-CLAUDE-PARITY-01 (`▸▸ shift+tab: bypass`) |
| 8 | Paste de imagem reconhecido | OK | VISION-01..03 + TUI-FIX-05 (`[Image #N]`) |
| 9 | Sandbox PT-BR (mensagens em português) | OK | LANG-PROMPT-ACENT-01 + invariante #2 |
| 10 | Autocomplete reativo a cada tecla | OK | UX-BUG-01 |
| 11 | Ghost text (sugestão inline) | OK | prompt-toolkit AutoSuggestFromHistory (cli.py:301) |
| 12 | Tool cards com duração em ms/s | OK | UX-LAYOUT-02 + `_format_duration` em output.py:452 |
| 13 | Evento visual de compactação | OK | OBSERVABILITY-01 + `on_compaction` callback |
| 14 | Memória cross-session persiste | OK | CTX-02 + memory.py |
| 15 | /resume recupera última sessão | OK | SESSION-RESUME-01 |
| 16 | Cursor piscante consistente | OK | prompt-toolkit default + ADR-026 |
| 17 | Quebra de linha em resposta longa | OK | output.py:625+ via wrap |
| 18 | Cor de erro distinta da cor de info | OK | TAG_STYLES em output.py:79+ |
| 19 | Feedback imediato ao ENTER | OK | UX-LOOP-01 ADR-025 (ack <100ms) |
| 20 | Histórico com seta pra cima | OK | prompt-toolkit FileHistory (cli.py:294) |
| 21 | Ctrl+C cancela sem sair | OK | UX-AGENCY-02 (cancel asyncio real) |
| 22 | Ctrl+D sai limpo | OK | prompt-toolkit default + UX-LIFECYCLE-01 |
| 23 | /help lista os commands | OK | core.py + 61 commands registrados; /? falta exemplo (HELP-COVERAGE-FIX-01) |
| 24 | Banner respeita largura do terminal | OK | UX-LAYOUT-01A `_build_compact` fallback |
| 25 | Overflow horizontal trunca sem quebrar layout | PENDENTE | aguarda teste manual em terminal estreito |
| 26 | Título do terminal muda pra nome do projeto | OK | TUI-FIX-07A footer + project name detection |
| 27 | Model state transitions (cold/warming/warm) visível | OK | UX-BUG-02B + UX-LOOP-VISIBILITY-01 (`○ ◐ ●`) |
| 28 | Replay de sessão read-only funciona | OK | OBSERVABILITY-01 + `/replay <id>` |
| 29 | /debug session retorna métricas reais | OK | OBSERVABILITY-01 |
| 30 | Output com paleta D aplicada (design system) | OK | UX-DESIGN-01 + ADR-023 + invariante #6 |

**Resumo:** 27 OK + 3 PENDENTE (itens 1, 6, 25).

PENDENTEs reagendadas em VALIDATE-FINAL-01-PARTE-2 (captura visual humana).

---

*"Cada linha desta tabela é um pixel a menos de incerteza." -- VALIDATE-FINAL-01*
