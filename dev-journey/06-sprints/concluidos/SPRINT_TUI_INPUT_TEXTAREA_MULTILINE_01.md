# SPRINT 286 — TUI-INPUT-TEXTAREA-MULTILINE-01

## 0. SPEC

```yaml
sprint:
  id: TUI-INPUT-TEXTAREA-MULTILINE-01
  title: "InputWidget base Input -> TextArea: multiline, Ctrl+J newline, Enter submit, preserva ghost-completer"
  onda: 34
  prioridade: ALTA
  tipo: Feature
  dependencias: [TUI-INPUT-CSS-SANITIZE-01, TUI-SLASH-COMPLETER-POPULATE-01]
  desbloqueia: []

  touches:
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/agent/tui/widgets/input.py
      reason: "Trocar classe-base Input -> TextArea; reimplementar Enter=submit / Ctrl+J=newline via _on_key; reimplementar ghost-completer manual (TextArea não tem suggester); migrar API .value->.text, insert_text_at_cursor->insert"
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/agent/tui/app.py
      reason: "action_quit_if_empty/recall_last usam input_widget.value (Input-only); migrar para .text (TextArea); adicionar binding Ctrl+J se necessario fora do widget"
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/agent/tui/styles/nyx.tcss
      reason: "Ajustar CSS de altura crescente do TextArea (height: auto/min/max) + cor do ghost-completer (texto dim); placeholder do TextArea usa classe interna distinta do Input"
  creates: []
  removes: []

  forbidden:
    - "Regredir o ghost-completer do slash (sprint 284): digitar '/' DEVE continuar mostrando sugestao dim aceitavel por Tab"
    - "Adicionar dependencia externa (so textual 8.2.7 ja instalado)"
    - "Mudar a assinatura publica de InputWidget.__init__ (slash_completer, on_submit, placeholder, id) -- app.py:144-148 depende dela"
    - "Tocar chat_message.py, banner.py, toolbar.py, _core.py, _iteration.py, proxy.py"
    - "Introduzir hex de cor hardcoded (usar $accent/$surface/$foreground/$text-muted)"
    - "Adicionar emoji ou mencao a IA externa"

  tests:
    - cmd: "./run.sh --smoke"
      timeout: 15
      deve_passar: true
    - cmd: "bash scripts/sprint_invariants.sh"
      timeout: 60
      deve_passar: true

  acceptance_criteria:
    - "InputWidget herda de textual.widgets.TextArea (não mais Input)"
    - "Enter SUBMETE o conteudo (chama on_submit) e limpa o buffer"
    - "Ctrl+J insere newline (não submete); input cresce em altura ate um maximo"
    - "Colar (Ctrl+V) e [Image #?] continuam funcionando via paste_text -> insert"
    - "Ghost-completer do slash preservado: digitar '/' mostra sugestao dim, Tab aceita"
    - "app.py não referencia mais .value (so .text); action_quit_if_empty/recall_last funcionam"
    - "smoke boot ok; invariantes 14/14 FAIL=0; gauntlet rapido + loop APROVADO; acentuacao rc=0"
```

---

## Contexto

A migração ONDA-32 (prompt_toolkit -> Textual) perdeu o **input multiline** que existia via `multiline=True` no `repl_app.py` deletado. O `InputWidget` atual (`nyx/agent/tui/widgets/input.py`) herda de `textual.widgets.Input`, que é single-line por construção. A auditoria ONDA-34 (`~/.claude/plans/redesign-auditoria-da-tender-beacon.md`, linhas 28-29, severidade ALTA) cataloga "Input multiline PERDIDO" e "Ctrl+J newline PERDIDO" como decisão #1 (linha 50): trocar a base para `TextArea`, Enter = submit, Ctrl+J = newline.

### Interação crítica com a sprint 284 (verificada via leitura do código real)

A sprint 284 (commit 4fe225f, CONCLUIDA) populou o slash completer ghost-inline. Em `input.py:69-80`, o `InputWidget` cria `SuggestFromList([f"/{c}" for c in slash_completer])` e passa ao `super().__init__(suggester=...)`. **Esse mecanismo é exclusivo do `Input`.** Confirmado por leitura da API instalada do Textual 8.2.7:

- `venv/lib/python3.12/site-packages/textual/widgets/_text_area.py` — o `TextArea.__init__` (linha 584) **NÃO aceita `suggester`**; aceita `text`, `language`, `theme`, `soft_wrap`, `tab_behavior`, `read_only`, `placeholder`, `id`, `classes`. `grep -n "suggester\|Suggest"` no arquivo retorna **vazio**.
- `TextArea` expõe só `class Changed(Message)` e `class SelectionChanged(Message)` — **não há `Submitted`** (o `Input.Submitted` não existe no TextArea).
- O ghost do `Input` funciona via `suggester._get_suggestion` -> `SuggestionReady` -> reactive `_suggestion` renderizado dim (`_input.py:265-267,540-542`). Esse caminho inteiro é `Input`-only.

**Conclusão:** trocar Input->TextArea ingenuamente QUEBRA o ghost-completer da sprint 284. Por isso esta sprint inclui a **reimplementação manual do ghost** sobre o TextArea (decisão (b) do briefing), e foi SEPARADA da sanitização de CSS (sprint 285), que é independente e de-risca o swap.

### Diferenças de API a migrar (Input -> TextArea), todas confirmadas via grep

| Uso atual (Input) | Equivalente TextArea | Local |
|---|---|---|
| `.value` (getter/setter) | `.text` (getter/setter, `_text_area.py:1632,1637`) | `app.py:372,405`; `input.py:89` |
| `.clear()` | `.clear()` (existe, `_text_area.py:2537`) | `input.py:92` |
| `.insert_text_at_cursor(s)` | `.insert(s)` (`_text_area.py:2465`) | `input.py:103,105` |
| `action_submit()` (binding enter) | `_on_key` intercepta `enter`->`\n` (`_text_area.py:1818-1849`); precisa override | `input.py:83` |
| `action_delete_right()` | existe no TextArea (`_text_area.py:2599`) | `app.py:375` |
| `suggester=` no `__init__` | ausente -> ghost manual | `input.py:76-78` |

## Escopo (touches autorizados)

- Arquivos a modificar:
  - `/home/andrefarias/Desenvolvimento/Nyx-Code/nyx/agent/tui/widgets/input.py` — trocar base `Input` -> `TextArea`; manter assinatura pública `__init__(slash_completer, on_submit, placeholder, id)`; reimplementar Enter=submit/Ctrl+J=newline via override de `_on_key`; reimplementar ghost-completer manual; migrar `.value`->`.text` e `insert_text_at_cursor`->`insert`.
  - `/home/andrefarias/Desenvolvimento/Nyx-Code/nyx/agent/tui/app.py` — `action_quit_if_empty` (linha 372) e `action_recall_last` (linha 405) usam `input_widget.value`; migrar para `.text`. Avaliar se Ctrl+J precisa de binding no App (priority) ou se o override de `_on_key` no widget basta (preferir o widget para não poluir BINDINGS globais).
  - `/home/andrefarias/Desenvolvimento/Nyx-Code/nyx/agent/tui/styles/nyx.tcss` — ajustar `InputWidget` para altura crescente (`height: auto; min-height: 3; max-height: 10` ou equivalente) já que TextArea cresce com o conteúdo; ajustar seletor de placeholder (TextArea usa classe interna distinta do `.input--placeholder` do Input) e a cor dim do ghost manual.
- Arquivos a criar: nenhum.
- Arquivos NÃO a tocar: `chat_message.py`, `banner.py`, `toolbar.py`, `nyx/cli.py` (o `slash_completer=[c.name for c in list_commands()]` da sprint 284 fica intacto), `loop/_core.py`, `loop/_iteration.py`, `proxy.py`.

## Acceptance criteria

1. `rg -n "class InputWidget" nyx/agent/tui/widgets/input.py` mostra base `TextArea`.
2. Enter chama `on_submit(text)` e limpa o buffer; o turno dispara (paridade com `action_submit` atual).
3. Ctrl+J insere `\n`; o input cresce em altura até o `max-height`; depois scrolla internamente.
4. `paste_text` continua tratando `[clipboard-image]:` -> `[Image #?]` e texto comum via `insert`.
5. Digitar `/` mostra ghost dim de comando; Tab aceita a sugestão (anti-regressão sprint 284).
6. `rg -n "\.value" nyx/agent/tui/app.py` retorna vazio (tudo migrado para `.text`).
7. smoke boot ok; invariantes 14/14 FAIL=0; gauntlet `--only rapido` + loop APROVADO; acentuação rc=0.

## Invariantes a preservar

- **Ghost-completer (sprint 284)**: a entrega mais recente da onda. Reimplementar manualmente sobre TextArea ou registrar débito explícito se a reimplementação não fechar nesta sprint (ver Riscos). A acceptance #5 é bloqueante.
- **Assinatura pública de `InputWidget.__init__`**: `app.py:144-148` instancia com `id=`, `slash_completer=`, `on_submit=`. Não mudar nomes nem ordem dos kwargs.
- **Foco no mount** (`app.py:154-164`, TUI-FIX-INPUT-FOCUS-ON-MOUNT-01): TextArea é focável; garantir que `query_one("#input").focus()` continua funcionando (TextArea aceita foco).
- **Dock order** (`app.py:119-132`): Input antes de Toolbar no `dock: bottom`. Com altura crescente, garantir que o crescimento empurra o chat para cima sem cobrir a Toolbar (h:1).
- **Check #6 (zero hex)**: só `.py`; usar variáveis Textual no `nyx.tcss`; a cor dim do ghost deve sair de `$text-muted`/`$accent NN%`, não hex.
- **Check #14 (anti-sanitizer)**: `input.py`/`app.py`/`nyx.tcss` não são arquivos protegidos; sem glifo canônico em risco.
- **GUIDE.md §2 (simplicidade)**: o ghost manual deve ser o mínimo viável — filtrar `slash_completer` por prefixo do texto atual e renderizar a sugestão; não construir um framework de completions.
- **MEMORY "Nenhum débito fica para trás"**: qualquer função não portada (ex.: popup dropdown, histórico) vira sprint nova com ID, nunca absorvida.

## Plano de implementação

1. Em `input.py`: trocar `from textual.widgets import Input` por `from textual.widgets import TextArea`; `class InputWidget(TextArea)`. Remover o import de `SuggestFromList` (não há suggester no TextArea).
2. `__init__`: manter kwargs públicos. Guardar `self._slash_full = [f"/{c}" for c in (slash_completer or [])]` para o ghost manual. Chamar `super().__init__(placeholder=placeholder, id=id, soft_wrap=True, tab_behavior="focus")` (manter Tab para foco/aceite do ghost, não para indentar). Guardar `self._on_submit`.
3. Override de `_on_key(self, event)`:
   - `enter` (sem Ctrl): consumir (`event.stop()`, `event.prevent_default()`), chamar `self._on_submit(self.text)` e `self.clear()` — semântica submit.
   - `ctrl+j`: consumir e inserir `"\n"` via `self.insert("\n")` — semântica newline.
   - `tab` com ghost ativo: aceitar a sugestão (substituir o texto pelo match); senão, comportamento default.
   - demais teclas: delegar ao `super()._on_key(event)` para preservar edição normal (multiline natural).
4. Ghost-completer manual: em `on_text_area_changed` (ou na própria `_on_key` após inserir), se `self.text` começa com `/`, computar o 1º match em `self._slash_full` por prefixo case-insensitive e renderizar a porção restante como texto dim. Implementação mínima: usar `placeholder`/render auxiliar ou um overlay simples; se TextArea não der render trivial de ghost inline, aceitar o débito (ver Riscos) — mas a meta é paridade visual com a sprint 284.
5. `paste_text`: trocar `self.insert_text_at_cursor(...)` por `self.insert(...)` (2 sites, linhas 103/105).
6. `app.py`: `action_quit_if_empty` -> `if not input_widget.text:`; `action_recall_last` -> `input_widget.text = self._last_input`. Confirmar que `action_delete_right()` existe no TextArea (confirmado, `_text_area.py:2599`).
7. `nyx.tcss`: `InputWidget { height: auto; min-height: 3; max-height: 10; ... }` (altura crescente); ajustar seletor de placeholder do TextArea; definir cor dim do ghost com variável.
8. Rodar smoke + invariantes + acentuação; validação visual `--web` cobrindo as 4 acceptance de runtime.

## Aritmética

Sem meta de redução de linhas. Estimativa de saldo:
- `input.py`: remoção do bloco suggester (~6 linhas) + remoção do `action_submit` (~10) + adição de `_on_key` override (~25) + ghost manual (~20) = saldo líquido ~ +30 linhas.
- `app.py`: 2 trocas `.value`->`.text` (saldo 0).
- `nyx.tcss`: ajuste de height + ghost (~+4 linhas).
- Net esperado: ~ +34 linhas. Sem alvo `<NL` a fechar; aritmética informativa.

## Testes

- Não há suíte pytest cobrindo `InputWidget` (grep em `tests/` = zero, confirmado). Verificação primária é runtime (`--web`) + invariantes.
- Se o executor quiser blindar a migração de API, pode adicionar um teste mínimo com `App.run_test()`/`Pilot` exercitando: digitar texto, Ctrl+J (newline presente em `.text`), Enter (on_submit chamado + `.text` vazio), `/` (ghost presente). Opcional, não bloqueante.
- Baseline: FAIL_BEFORE = estado atual de `sprint_invariants.sh`. Esperado FAIL_AFTER == FAIL_BEFORE (registrar números reais).

## Proof-of-work esperado

- Diff final dos 3 arquivos.
- Runtime real (BRIEF seção `[CORE] Contratos de runtime`):
  - Smoke: `./run.sh --smoke` -> `boot ok`, exit 0.
  - Invariantes: `bash scripts/sprint_invariants.sh` -> 14/14, FAIL=0.
  - Gauntlet: `./run.sh --gauntlet --only rapido` + loop -> APROVADO (disciplina OOM: 1 execução, sem paralelismo; cruzar com `--only proxy` se flake do BRIEF aparecer).
- Validação visual (UI obrigatória): `./run.sh --web` (cockpit 127.0.0.1:11437), via playwright (ToolSearch `mcp__plugin_playwright_playwright__*`) ou Chrome real CDP + skill `validação-visual`. Capturar e gerar sha256 de PNGs comprovando:
  - (a) Ctrl+J insere newline e o input cresce em altura;
  - (b) Enter submete (mensagem entra no chat, input limpa);
  - (c) borda não cortada;
  - (d) ghost após `/` ainda funciona (não regrediu a sprint 284).
- Acentuação periférica: `python3 /home/andrefarias/.config/zsh/scripts/validar-acentuacao.py --paths nyx/agent/tui/widgets/input.py nyx/agent/tui/app.py nyx/agent/tui/styles/nyx.tcss` -> rc=0.
- Hipótese verificada (lição 4): `rg -n "suggester|Suggest" venv/lib/python3.12/site-packages/textual/widgets/_text_area.py` retorna vazio (justifica o ghost manual); `rg -n "def text|def clear|def insert|action_delete_right" venv/lib/python3.12/site-packages/textual/widgets/_text_area.py` confirma os métodos migrados.

## Riscos e não-objetivos

- **Risco ALTO — ghost manual sobre TextArea**: o `Input` renderiza o ghost via reactive interno `_suggestion`; reproduzir inline no TextArea pode exigir um overlay/Text customizado. **Mitigação**: se a reimplementação visual fiel não fechar dentro do escopo cirúrgico, o executor deve PARAR e dispatchar `planejador-sprint` para uma sprint derivada `TUI-TEXTAREA-GHOST-COMPLETER-02` (mecanismo de ghost) e, nesta 286, manter o swap funcional com o completer registrado como débito explícito — NUNCA marcar CONCLUIDA degradando a sprint 284 silenciosamente (MEMORY "Nenhum débito fica para trás"). A acceptance #5 permanece a meta; o split é o plano B catalogado, não a saída fácil.
- **Risco MÉDIO — altura crescente vs dock bottom**: TextArea com `height: auto` dentro de `dock: bottom` pode empurrar a Toolbar ou colidir com o `#chat`. Validar no `--web` em viewport 120x36 (caso citado em `app.py:131`).
- **Não-objetivo**: popup dropdown de completions, histórico navegável, auto-suggest do histórico, thinking-expand, image-counter real — são sprints separadas da onda (287+). Não implementar aqui.
- **Pré-requisito**: a sprint 285 (CSS-sanitize) deve estar CONCLUIDA antes — remove os seletores mortos e o conflito de height, evitando que o swap herde CSS ambíguo.

## Referências

- BRIEF: `/home/andrefarias/Desenvolvimento/Nyx-Code/VALIDATOR_BRIEF.md` (Contratos de runtime; flake OOM do gauntlet rápido).
- Plano da onda: `~/.claude/plans/redesign-auditoria-da-tender-beacon.md` (decisão #1, linha 50; Q1 ghost-inline, linha 61).
- API confirmada: `venv/lib/python3.12/site-packages/textual/widgets/_text_area.py` (Textual 8.2.7) — sem suggester/Submitted; `_on_key` linha 1818; `__init__` linha 584.
- Precedente CRÍTICO a não regredir: sprint 284 (commit 4fe225f) — slash-completer ghost-inline.
- Pré-requisito: sprint 285 TUI-INPUT-CSS-SANITIZE-01.
- MASTER: `dev-journey/06-sprints/SPRINT_ORDER_MASTER.md` (linha 811, bloco ONDA-34 em curso).
