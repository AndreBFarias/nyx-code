# Relatório Onda 21 -- TUI-FIX

**Data:** 2026-04-18
**Commits em main:** `b0b6659` ... `738527e` (8 commits)
**Status:** IMPLEMENTADO + AUDITADO + gauntlet passou. EM VALIDAÇÃO VISUAL pelo usuário.

---

## 1. Contexto

A onda 20 passou no Gauntlet 85/85 mas a primeira validação visual do usuário (com 5 screenshots) expôs 6 bugs + vários pontos de usabilidade que nenhum teste automatizado pegava:

1. Dois banners no boot (shell ASCII art corrompido + caixa Python)
2. Resposta da Nyx aparecia duas vezes (streaming + render final)
3. Popup de slash commands não abria ao digitar `/`
4. Sem Shift+Tab para alternar bypass de permissões (pedido do usuário)
5. Ctrl+Shift+V para colar imagens não funciona em xterm/GNOME (terminal captura antes da app)
6. Mensagens de sandbox (`Acesso negado: ... resolve ...`) truncadas e pouco úteis
7. Footer repetia a cada turno, poluindo o scroll; `/help` com 47 comandos virava parede de texto; sem indicador de memória carregada

Esta onda trata esses pontos como 7 sprints independentes + auditoria honesta ao final.

---

## 2. Sprints executadas

| Sprint | Commit | Entregue |
|---|---|---|
| TUI-FIX-02 | `b0b6659` | `turn_state["streamed_text"]` acumula tokens; suprime summary só se já foi streamed |
| TUI-FIX-01 | `4906480` | `show_banner` removido do shell; `_build_banner` incorpora rede + degrada para 1 linha em terminais <60 cols |
| TUI-FIX-06 | `0b73659` | `validate_path` retorna "Fora do projeto X: path. Inicie o Nyx lá"; `render_tool_result` detecta prefixos de erro e pinta em âmbar |
| TUI-FIX-03 | `6b6c20d` | Keybinding `@kb.add("/")` força `start_completion` quando buffer tem apenas `/`; fallback `COLUMN` em terminais <100 cols |
| TUI-FIX-04 | `a607eb9` | `s-tab` alterna `app_state["bypass"]`; bottom_toolbar mostra faixa âmbar quando ON; `on_permission` auto-aprova respeitando deny rules |
| TUI-FIX-05 | `bbc4d10` | `nyx/agent/clipboard.py` usa xclip para detectar imagem/texto; Ctrl+V salva em `~/.nyx/pastes/` e insere `[Image #N]` |
| TUI-FIX-07 | `738709a` | Footer migra para bottom_toolbar (ctx/iter/lidos/modif atualizados no lugar); paste >8 linhas colapsa no eco; `/help` mostra 10 essenciais (+ `/help all`); indicador `[memória: N entradas]` no boot; comandos `/memory` e `/paste` |
| Auditoria pós-onda | `738527e` | `/memory` estava registrado 2x → antigo renomeado para `/recall`; `/tools` criado (faltava apesar de estar em ESSENTIAL_COMMANDS); lógica de `streamed` refeita com texto acumulado para cobrir edge case `"Vou ler..." + tool + done(summary="X")` |

---

## 3. Arquivos tocados

- **Código (7):** `nyx/cli.py`, `nyx/agent/output.py`, `nyx/agent/commands.py`, `nyx/agent/completer.py`, `nyx/agent/tools/base.py`, `nyx/agent/clipboard.py` (NOVO), `run.sh`
- **Doc:** `dev-journey/06-sprints/SPRINT_ORDER_MASTER.md`, 7 specs em `dev-journey/06-sprints/producao/SPRINT_TUI_FIX_*.md`, este relatório

---

## 4. Auditoria honesta feita pelo próprio assistente

Após os 7 commits, o assistente lançou Explore agent pedindo revisão crítica procurando regressões sutis. O agent apontou 2 problemas reais:

1. **`/memory` duplicado** -- `_COMMANDS` descartava silenciosamente o comando antigo em favor do novo; usuário não notaria mas o antigo sumiu sem registro. Corrigido: renomeado antigo para `/recall` (faz busca semântica em `SessionMemory` JSON, papel diferente do markdown cross-session).
2. **`/tools` inexistente** -- estava listado em `ESSENTIAL_COMMANDS` mas nunca foi registrado; `format_help(show_all=False)` pulava silencioso. Corrigido: criado `cmd_tools` que lê `ToolRegistry` e lista 35 tools com descrição.
3. **Edge case no `streamed`**: boolean ficava True no 1º token e podia suprimir summary legítimo. Refeito para acumular texto e só suprimir se o summary é suffix do streamed.

Checks OK (sem ação):
- Banner em <60 cols cabe (49 chars sem ANSI)
- `render_footer` não é mais importado em produção
- Keybinding `/` só dispara completion quando buffer tem apenas `/` (não quebra digitar path)
- Ctrl+V degrada pra texto quando não há imagem
- `session.add_user` recebe texto original (sem truncagem do eco)
- `image_map` local por sessão + `/paste` lê `~/.nyx/pastes/` global (desejado)
- `app_state["bypass"]` resetado a cada sessão

---

## 5. Gauntlet

| Fase | Antes | Depois |
|---|---|---|
| rapido | 18/18 | 18/18 |
| completo (`~/.nyx/sessions`, proxy, tools, qualidade, performance, visual, config, resiliencia, parser, robustez, interface, controle, persistencia, e2e) | 69/69 | **69/69** |
| contexto (CTX-01..10) | 10/10 | **10/10** |
| interface (IF-01..05) | 5/5 | **5/5** |
| tools (T-01..T-09) | 6/6 | **6/6** |
| controle (CT-01..CT-04) | 4/4 | **4/4** |

Zero regressão. Todos os casos existentes continuam passando.

---

## 6. Validação visual ainda pendente

O assistente não tem TTY/display para capturar screenshot de REPL. O usuário deve rodar `./run.sh` e confirmar cada um dos 7 pontos abaixo. Quando todos passarem, mover as 7 sprints de `producao/` para `concluidos/`.

| # | O que testar | Esperado |
|---|---|---|
| 1 | Boot | UM banner (caixa `╭─╮`), sem ASCII "Nyx Code" quebrado, sem `...sintonizando frequencia...` |
| 2 | Saudação "Olá" | Resposta aparece 1 vez (streaming) |
| 3 | Task real ("lista .py em nyx/agent") | Resposta com tool_calls; summary final não duplica |
| 4 | Digitar `/` | Popup com 10 comandos essenciais (MULTI_COLUMN em terminal largo, COLUMN em estreito) |
| 5 | Digitar `/help` | Mostra 10 essenciais + dica "/help all pra ver todos" |
| 6 | Shift+Tab | bottom_toolbar vira faixa âmbar "⚡ bypass permissions ON"; Shift+Tab de novo desliga |
| 7 | Ctrl+V com imagem no clipboard | Insere `[Image #1]` no input; `ls ~/.nyx/pastes/` mostra arquivo; próximo paste vira `[Image #2]` |
| 8 | Ctrl+V com texto | Paste normal (xclip fallback) |
| 9 | Pedir leitura de `/home/andre/Desenvolvimento/ArcaneTab/README.md` | `⏺ read_file(...)` + `└─ Fora do projeto Nyx-Code: ... Para acessar outro projeto, inicie o Nyx lá.` em cor âmbar |
| 10 | Footer | Aparece abaixo do prompt como bottom_toolbar dinâmica (não repete no scroll) |
| 11 | `/memory` | Lista memórias se houver, ou mensagem "Sem memórias gravadas" |
| 12 | `/tools` | Lista 35 tools com descrição curta |
| 13 | Paste de 20 linhas | Eco `╭─ você ─╮` colapsa para 3 primeiras linhas + `[17 linhas ocultas do paste]` |

---

## 7. O que fica de backlog

- Frame persistente estilo Claude Code (`Application` + `Frame`) — já falhou uma vez, requer sprint dedicada com POC isolado (TUI-04 do backlog original)
- Image map <-> modelo de visão — quando tivermos modelo multimodal, integrar `image_map` no prompt
- `/paste` command deveria opcionalmente filtrar apenas a sessão atual (hoje lista global)

---

*"A honestidade começa em reconhecer o que não funciona." -- adaptado de Sêneca*
