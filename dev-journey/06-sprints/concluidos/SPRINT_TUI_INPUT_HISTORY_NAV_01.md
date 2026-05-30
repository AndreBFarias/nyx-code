# SPRINT 289 — TUI-INPUT-HISTORY-NAV-01

## 0. SPEC

```yaml
sprint:
  id: TUI-INPUT-HISTORY-NAV-01
  title: "Histórico navegável de inputs na NyxTUI: Ctrl+Up/Ctrl+Down percorrem submissões anteriores sem colidir com o cursor multiline (Up/Down) nem regredir o ghost-completer"
  onda: 34
  prioridade: MEDIA
  tipo: Feature
  dependencias: [TUI-INPUT-TEXTAREA-MULTILINE-01, TUI-SLASH-COMPLETER-POPULATE-01]
  desbloqueia: []

  touches:
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/agent/tui/app.py
      reason: "Adicionar store de histórico (lista + índice + rascunho) na NyxTUI; alimentar a lista em _on_input_submit (mesmo ponto onde _last_input já é setado, linha 196); adicionar bindings Ctrl+Up/Ctrl+Down em BINDINGS (priority=True, ao lado de Ctrl+O) e as actions action_history_prev/action_history_next que substituem input_widget.text pelo item e reposicionam o cursor no fim"
  creates: []
  removes: []

  forbidden:
    - "Tocar nyx/agent/tui/widgets/input.py: o override _on_key (enter/ctrl+j/tab) e o update_suggestion (ghost do 284/286) NÃO devem mudar; a navegação vive 100% na App via bindings priority"
    - "Usar as teclas Up/Down nuas para histórico: elas movem o cursor DENTRO do TextArea multiline (sprint 286) e DEVEM continuar movendo só o cursor"
    - "Remover ou absorver Ctrl+O / action_recall_last: é affordance distinta (recall do último), mantida intacta — absorvê-la seria scope creep silencioso"
    - "Regredir o ghost-completer do slash (sprint 284/286): digitar '/' continua mostrando sugestão dim aceitável por Tab; popular o histórico no buffer NÃO deve disparar/quebrar update_suggestion"
    - "Tocar chat_message.py (regra de escopo desta sprint), banner.py, toolbar.py, _core.py, _iteration.py, proxy.py, nyx/cli.py, nyx.tcss"
    - "Adicionar dependência externa (só textual 8.2.7 já instalado)"
    - "Mudar a assinatura pública de InputWidget.__init__ (slash_completer, on_submit, placeholder, id) — app.py:145-149 depende dela"
    - "Introduzir hex de cor hardcoded; adicionar emoji ou menção a IA externa"

  tests:
    - cmd: "./run.sh --smoke"
      timeout: 15
      deve_passar: true
    - cmd: "bash scripts/sprint_invariants.sh"
      timeout: 60
      deve_passar: true

  acceptance_criteria:
    - "Submeter 2-3 inputs e depois Ctrl+Up substitui o buffer pelo input ANTERIOR; Ctrl+Up de novo recua para o de antes (mais antigo)"
    - "Ctrl+Down avança de volta na direção dos mais recentes; ao passar do mais recente, restaura o rascunho que estava sendo digitado (string vazia se não havia rascunho)"
    - "Up/Down nuas continuam movendo o cursor no TextArea multiline (anti-regressão sprint 286), NÃO navegam histórico"
    - "Ctrl+O (action_recall_last) continua recarregando o último input (anti-regressão UX-EXTRA-01); não foi removido nem alterado"
    - "Ghost-completer do slash preservado: digitar '/' mostra sugestão dim, Tab aceita (anti-regressão 284/286)"
    - "Slash commands (text começa com '/') NÃO entram no histórico (mesma semântica de _last_input, que só é setado no ramo não-slash em app.py:196)"
    - "input.py intocado: rg confirma diff zero no widget"
    - "smoke boot ok; invariantes 14/14 FAIL=0; gauntlet --only rapido + loop APROVADO; acentuação rc=0"
```

---

## Contexto

A migração ONDA-32 (prompt_toolkit -> Textual) perdeu o **histórico navegável de inputs**. No legado, `repl_app.py:245` montava `FileHistory`/setas e Ctrl+Up recuperavam inputs anteriores; hoje a NyxTUI só tem `Ctrl+O` (`action_recall_last`, `app.py:402-406`), que recarrega APENAS o último input. A auditoria ONDA-34 (`~/.claude/plans/redesign-auditoria-da-tender-beacon.md`, linha 34, severidade MÉDIA) cataloga "Histórico navegável (Ctrl+Up / History) PERDIDO (só Ctrl+O recall last)". O `SPRINT_ORDER_MASTER.md` (linha 815) lista "histórico navegável" entre os itens PENDENTES para IDs 289+.

### Interação crítica com a sprint 286 (verificada via leitura do código real)

A sprint 286 (commit 3e31739, CONCLUIDA) trocou a base do `InputWidget` de `Input` para `TextArea`. Confirmado em `nyx/agent/tui/widgets/input.py:36` (`class InputWidget(TextArea)`). Consequência verificada na API instalada do Textual 8.2.7:

- `venv/lib/python3.12/site-packages/textual/widgets/_text_area.py:224-237` — o `TextArea.BINDINGS` liga **`up` -> `cursor_up`** e **`down` -> `cursor_down`** (movimento de cursor multiline). Portanto Up/Down NUAS já são do cursor e NÃO podem virar navegação de histórico sem regredir a 286.
- Mesmo arquivo, linhas 250-261 — só `ctrl+left`/`ctrl+right` estão ligados (word-left/right). **`ctrl+up` e `ctrl+down` NÃO aparecem em nenhum Binding do TextArea** (grep `ctrl\+up|ctrl\+down` no arquivo retorna apenas os comentários de cursor, não bindings). Logo Ctrl+Up/Ctrl+Down estão LIVRES.
- `TextArea._on_key` (`_text_area.py:1818-1849`) só consome `is_printable` ou `enter`/`tab`; teclas não-imprimíveis como `ctrl+up` NÃO são paradas ali e seguem para o sistema de bindings.

**Conclusão de design:** a navegação usa **Ctrl+Up / Ctrl+Down** registradas em `NyxTUI.BINDINGS` com `priority=True` (mesmo padrão de `Ctrl+O`/`Ctrl+V`/`Shift+Tab` em `app.py:59-65`, que documenta: "priority=True garante que o App captura o key event antes do widget focado"). Como bindings `priority` do App vencem o widget e Ctrl+Up/Down não existem no TextArea, não há colisão com o cursor multiline. **Nada é tocado em `input.py`** — o override `_on_key` (enter/ctrl+j/tab) e `update_suggestion` (ghost) ficam intactos, eliminando risco de regressão na 284/286.

### Onde a store vive e como é alimentada (verificado via grep)

- `NyxTUI.__init__` já mantém `self._last_input: str = ""` (`app.py:90`).
- `_on_input_submit` (`app.py:167-217`) já seta `self._last_input = text` em `app.py:196`, **só no ramo não-slash** (o ramo slash retorna antes, em `app.py:193-195`). Esse é o ponto natural para também fazer `append` no histórico, garantindo a paridade de semântica (slash commands fora do histórico).
- `action_recall_last` (`app.py:402-406`) faz `input_widget.text = self._last_input` — a substituição direta de `.text` é o idioma já em uso para reescrever o buffer; reaproveitamos.

### API do TextArea para reposicionar o cursor (confirmada via grep)

| Necessidade | API TextArea | Local |
|---|---|---|
| Reescrever o buffer | `input_widget.text = <str>` (setter reactive, já usado em `action_recall_last`) | `app.py:406` |
| Fim do documento | `input_widget.document.end` (property `Location`; usada internamente em `clear()`) | `_text_area.py:2543` |
| Mover o cursor | `input_widget.move_cursor(location)` | `_text_area.py:2052` |

Após `input_widget.text = item`, chamar `input_widget.move_cursor(input_widget.document.end)` deixa o cursor no fim (UX esperada ao recuperar um comando para editar/reenviar).

## Escopo (touches autorizados)

- Arquivos a modificar:
  - `/home/andrefarias/Desenvolvimento/Nyx-Code/nyx/agent/tui/app.py`:
    1. `__init__`: adicionar `self._input_history: list[str] = []` e `self._history_idx: int = 0` (ou `None` para "fora do histórico", ver Plano) e `self._history_draft: str = ""` (rascunho preservado).
    2. `_on_input_submit` (no ramo não-slash, junto da linha 196 `self._last_input = text`): `append` do `text` no histórico (com de-dup do consecutivo, ver Plano) e reset do índice de navegação para "fora do histórico".
    3. `BINDINGS` (`app.py:59-65`): adicionar `Binding("ctrl+up", "history_prev", "Histórico anterior", priority=True)` e `Binding("ctrl+down", "history_next", "Histórico próximo", priority=True)`.
    4. Adicionar `action_history_prev` e `action_history_next` (perto de `action_recall_last`, `app.py:402`).
- Arquivos a criar: nenhum.
- Arquivos NÃO a tocar: `nyx/agent/tui/widgets/input.py` (override `_on_key` e `update_suggestion` intactos), `chat_message.py`, `banner.py`, `toolbar.py`, `nyx/cli.py`, `nyx.tcss`, `loop/_core.py`, `loop/_iteration.py`, `proxy.py`.

## Acceptance criteria

1. `rg -n "ctrl\+up|ctrl\+down|action_history" nyx/agent/tui/app.py` mostra os 2 bindings + as 2 actions.
2. Submeter `a`, `b`, `c` (Enter cada). Com o buffer vazio: Ctrl+Up -> buffer mostra `c`; Ctrl+Up -> `b`; Ctrl+Up -> `a`; Ctrl+Up no topo permanece em `a` (não estoura índice).
3. A partir de `a`: Ctrl+Down -> `b`; Ctrl+Down -> `c`; Ctrl+Down (passou do mais recente) -> restaura o rascunho (vazio se nada digitado antes do 1º Ctrl+Up).
4. Up/Down nuas movem o cursor no TextArea multiline (digitar 2 linhas via Ctrl+J, Up sobe uma linha o cursor) — NÃO navegam histórico (anti-regressão 286).
5. Ctrl+O recarrega o último input via `action_recall_last` intacto (anti-regressão UX-EXTRA-01).
6. Digitar `/` mostra ghost dim; Tab aceita (anti-regressão 284/286). Popular o buffer pelo histórico não corrompe o ghost no próximo `/`.
7. `/help` (Enter) NÃO entra no histórico: após submetê-lo, Ctrl+Up pula direto para o último input não-slash.
8. `git diff --stat nyx/agent/tui/widgets/input.py` vazio (widget intocado).
9. smoke boot ok; invariantes 14/14 FAIL=0; gauntlet `--only rapido` + loop APROVADO; acentuação rc=0.

## Invariantes a preservar

- **Cursor multiline (sprint 286)**: Up/Down nuas = `cursor_up`/`cursor_down` do TextArea (`_text_area.py:224-237`). Não interceptar Up/Down; usar só Ctrl+Up/Ctrl+Down. Acceptance #4 é bloqueante.
- **Ghost-completer (sprint 284/286)**: `update_suggestion` em `input.py:89-107` roda a cada edição. Setar `.text` para um item do histórico dispara o recálculo do ghost normalmente — aceitável (item raramente começa com `/`). Não tocar `update_suggestion`. Acceptance #6 é bloqueante.
- **Ctrl+O / action_recall_last (UX-EXTRA-01)**: mantido sem alteração; histórico é adição, não substituição. Acceptance #5.
- **Assinatura pública de `InputWidget.__init__`** (`app.py:145-149`): não muda (esta sprint não toca o widget).
- **Paridade de semântica slash**: `_last_input` só é setado no ramo não-slash (`app.py:193-196`); o histórico segue a mesma regra. Acceptance #7.
- **Bindings priority (app.py:54-58)**: o comentário existente justifica `priority=True` para atalhos globais não ficarem reféns do foco; os 2 novos seguem o padrão.
- **Check #6 (zero hex)**: nenhuma cor nova; sprint é pura lógica de buffer.
- **Check #14 (anti-sanitizer)**: `app.py` NÃO está na lista de 7 arquivos protegidos do `sprint_invariants.sh` (são `cli.py`, `themes/design_tokens.py`, `agent/output.py`, `agent/banner.py`, `themes/design_tokens_extended.py`, `scripts/sprint_invariants.sh` + 3 sentinelas de docs/xterm.js). Sem glifo canônico em risco; `FAIL_BEFORE == FAIL_AFTER`.
- **GUIDE.md §2 (simplicidade) e §3 (cirúrgico)**: store mínima (lista + índice + rascunho), 2 bindings, 2 actions; sem persistência em disco, sem dedup fuzzy, sem auto-suggest. Touch único em `app.py`.
- **MEMORY "Nenhum débito fica para trás"**: auto-suggest do histórico (`AutoSuggestFromHistory`, plano linha 33) e persistência em arquivo (FileHistory legado) NÃO entram aqui — ficam como sprints futuras (ver Riscos), nunca absorvidas implicitamente.

## Plano de implementação

1. `app.py __init__` (perto de `self._last_input` em `app.py:90`): adicionar
   - `self._input_history: list[str] = []` — submissões não-slash, ordem cronológica (mais antigo primeiro, mais recente no fim).
   - `self._history_idx: int = len(self._input_history)` — cursor de navegação; convenção: `idx == len(history)` significa "fora do histórico" (mostrando o rascunho do usuário). Após cada submit, resetar para `len(history)`.
   - `self._history_draft: str = ""` — guarda o buffer que o usuário estava digitando quando iniciou a navegação, para restaurar ao sair pelo lado recente.
2. `_on_input_submit`, no ramo não-slash, logo após `self._last_input = text` (`app.py:196`):
   - Dedup do consecutivo: `if not self._input_history or self._input_history[-1] != text: self._input_history.append(text)` (evita poluir com Enter repetido do mesmo comando; sem dedup global, para preservar ordem de uso).
   - `self._history_idx = len(self._input_history)` (volta a "fora do histórico").
   - `self._history_draft = ""`.
3. `BINDINGS` (`app.py:59-65`): adicionar duas linhas, ao lado de `ctrl+o`:
   - `Binding("ctrl+up", "history_prev", "Histórico anterior", priority=True)`
   - `Binding("ctrl+down", "history_next", "Histórico próximo", priority=True)`
4. `action_history_prev` (recua para inputs mais antigos):
   - `if not self._input_history: return`
   - Se `self._history_idx == len(self._input_history)` (estava fora do histórico): salvar o rascunho atual — `input_widget = self.query_one("#input", InputWidget); self._history_draft = input_widget.text`.
   - `if self._history_idx > 0: self._history_idx -= 1` (no topo, permanece — não estoura).
   - `input_widget.text = self._input_history[self._history_idx]` e `input_widget.move_cursor(input_widget.document.end)`.
5. `action_history_next` (avança para inputs mais recentes / volta ao rascunho):
   - `if not self._input_history: return`
   - `input_widget = self.query_one("#input", InputWidget)`
   - `if self._history_idx >= len(self._input_history): return` (já fora do histórico; nada a fazer).
   - `self._history_idx += 1`
   - `if self._history_idx == len(self._input_history): input_widget.text = self._history_draft` (saiu do histórico pelo lado recente: restaura rascunho)
   - `else: input_widget.text = self._input_history[self._history_idx]`
   - `input_widget.move_cursor(input_widget.document.end)`.
6. Rodar smoke + invariantes + acentuação; validação runtime `--web` cobrindo as acceptance de navegação e anti-regressão (286/284, Ctrl+O).

Observação de design (registrar no relato): a store vive na App (não no widget) porque `_on_input_submit` e `action_recall_last` já vivem ali e já mantêm `_last_input` — manter o widget "burro" é mais cirúrgico e evita acoplar histórico ao ciclo de edição do TextArea.

## Aritmética

Sem meta de redução de linhas. Estimativa de saldo (informativa):
- `app.py`: +3 linhas no `__init__` (3 atributos) + ~3 linhas no `_on_input_submit` (append+dedup+reset) + 2 linhas em `BINDINGS` + ~10 linhas `action_history_prev` + ~10 linhas `action_history_next` (com docstrings curtas) ≈ **+28 linhas**.
- `input.py`: **0** (intocado — acceptance #8).
- Net esperado: ~ +28 linhas, arquivo único. Sem alvo `<NL` a fechar.

## Testes

- Não há suíte pytest cobrindo `NyxTUI`/`InputWidget` (`rg -l "NyxTUI|InputWidget" tests/` = vazio, confirmado). Verificação primária é runtime (`--web`) + invariantes.
- Opcional (não bloqueante): o executor pode blindar com um teste headless via `App.run_test()`/`Pilot`: submeter 2-3 textos, `pilot.press("ctrl+up")` e checar `query_one("#input").text`, `pilot.press("ctrl+down")` e checar restauração do rascunho, `pilot.press("up")` mantém histórico parado (move só o cursor). Se adicionar, deve passar; o gauntlet `update_docs` pode recontar testes (touch derivado esperado pelo BRIEF, seção `[CORE] Side-effect do --gauntlet`).
- Baseline: `FAIL_BEFORE` = estado atual de `sprint_invariants.sh` (registrar número real ao iniciar). Esperado `FAIL_AFTER == FAIL_BEFORE` — `app.py` não é arquivo protegido pelo check #14.

## Proof-of-work esperado

- Diff final de `app.py` (único arquivo de código tocado) + `git diff --stat nyx/agent/tui/widgets/input.py` vazio.
- Runtime real (BRIEF seção `[CORE] Contratos de runtime`):
  - Smoke: `./run.sh --smoke` -> `boot ok`, exit 0.
  - Invariantes: `bash scripts/sprint_invariants.sh` -> 14/14, FAIL=0.
  - Gauntlet: `./run.sh --gauntlet --only rapido` + loop -> APROVADO. Disciplina OOM (GPU 4GB): 1 execução, sem paralelismo, só `rapido`; se o flake do BRIEF (seção `[CORE] Flake reprodutível do gauntlet --only rapido no RTX 3050 4GB`) aparecer, cruzar com `--only proxy`. Cleanup por PID ao fim: `pkill -f "nyx/proxy.py"`, `pkill -f "ollama serve"`, confirmar VRAM livre via `nvidia-smi` (BRIEF check #5).
- Validação runtime obrigatória (caminho da auditoria): `./run.sh --web` (cockpit `127.0.0.1:11437`), via playwright (ToolSearch `mcp__plugin_playwright_playwright__*`) ou Chrome real (CDP / X11 `DISPLAY=:1`, fallback). Submeter 2-3 inputs e comprovar via dump do buffer (`term.buffer.active`):
  - (a) Ctrl+Up recupera o input anterior; Ctrl+Up de novo o de antes; Ctrl+Down volta na direção recente e restaura o rascunho ao passar do mais recente.
  - (b) Up/Down nuas movem o cursor no input multiline (não regride a 286): digitar 2 linhas (Ctrl+J), Up sobe o cursor uma linha, o buffer não muda.
  - (c) Ctrl+O ainda recarrega o último input (não regride UX-EXTRA-01).
  - (d) Ghost após `/` ainda funciona (não regride 284/286).
  - Gerar PNG + sha256 de pelo menos um frame por comportamento se houver evidência visual (cor/posição do cursor); para (a)/(c) o dump textual do buffer basta.
- Acentuação periférica: `python3 /home/andrefarias/.config/zsh/scripts/validar-acentuacao.py --paths nyx/agent/tui/app.py` -> rc=0. Varredura também no spec e no relato.
- Hipótese verificada (lição 4): `rg -n "ctrl\+up|ctrl\+down" venv/lib/python3.12/site-packages/textual/widgets/_text_area.py` confirma que NÃO há binding de Ctrl+Up/Down no TextArea (livres); `rg -n "\"up\"|\"down\"|cursor_up|cursor_down" venv/lib/python3.12/site-packages/textual/widgets/_text_area.py` confirma Up/Down = cursor; `rg -n "def move_cursor|def end" venv/lib/python3.12/site-packages/textual/widgets/_text_area.py venv/lib/python3.12/site-packages/textual/document/_document.py` confirma `move_cursor`/`document.end`.

## Riscos e não-objetivos

- **Risco BAIXO — colisão de Ctrl+Up/Down com terminal/xterm.js no `--web`**: alguns emuladores mapeiam Ctrl+Seta para escape sequences próprias. Se no `--web` (xterm.js) o Ctrl+Up/Down não chegar ao Textual, o executor deve PARAR e dispatchar `planejador-sprint` para uma derivada (ex.: usar `Alt+Up`/`Alt+Down` como alternativa) — NÃO improvisar Up/Down nuas (regrediria a 286). Validar a chegada da tecla cedo no `--web` antes de prosseguir.
- **Risco BAIXO — ghost ao popular do histórico**: setar `.text` dispara `update_suggestion`. Se o item recuperado começar com `/` e houver match, o ghost aparece — comportamento aceitável e não bloqueante. Só vira problema se corromper o estado; acceptance #6 cobre.
- **Não-objetivo (sprints futuras, anti-débito)**:
  - Auto-suggest do histórico (`AutoSuggestFromHistory` inline, plano linha 33, severidade MÉDIA) — sprint própria `TUI-INPUT-HISTORY-AUTOSUGGEST-02`.
  - Persistência do histórico em disco (paridade `FileHistory` do `repl_app.py:245` legado, sobreviver entre sessões) — sprint própria.
  - Busca reversa tipo Ctrl+R, dedup fuzzy, limite de tamanho do histórico — fora de escopo.
  - Não absorver/remover Ctrl+O.
- **Pré-requisito**: a sprint 286 (TextArea multiline) já está CONCLUIDA (commit 3e31739) — base estável para o Up/Down = cursor que esta sprint precisa preservar.

## Referências

- BRIEF: `/home/andrefarias/Desenvolvimento/Nyx-Code/VALIDATOR_BRIEF.md` (Contratos de runtime; flake OOM do gauntlet rápido; lista dos 7 arquivos protegidos do check #14; side-effect do `--gauntlet` em README/PORT_STATUS).
- Plano da onda: `~/.claude/plans/redesign-auditoria-da-tender-beacon.md` (linha 34: "Histórico navegável PERDIDO"; linha 33: auto-suggest, deixado para sprint futura).
- API confirmada: `venv/lib/python3.12/site-packages/textual/widgets/_text_area.py` (Textual 8.2.7) — BINDINGS `up`/`down`=cursor (224-237), `ctrl+up`/`ctrl+down` ausentes; `_on_key` (1818); `move_cursor` (2052); `document.end` em `_document.py:181`.
- Código real desta sprint: `nyx/agent/tui/app.py` — `__init__` (`_last_input` linha 90), `BINDINGS` (59-65), `_on_input_submit` (167-217, `_last_input=text` na 196, ramo slash 193-195), `action_recall_last` (402-406). `nyx/agent/tui/widgets/input.py` — `class InputWidget(TextArea)` linha 36, `_on_key` 109-138, `update_suggestion` 89-107 (intocados).
- Precedentes a NÃO regredir: sprint 286 (commit 3e31739, cursor multiline), sprint 284/286 (ghost-completer), UX-EXTRA-01 (Ctrl+O recall last).
- MASTER: `dev-journey/06-sprints/SPRINT_ORDER_MASTER.md` (bloco ONDA-34, linhas 795-817; "histórico navegável" listado entre PENDENTES IDs 289+ na linha 815).
- Base estável: commit 814be13 (SPRINT 288 VRAM ao vivo no footer).
```
