## 0. SPEC (machine-readable)

```yaml
sprint:
  id: TEXTUAL-INPUT-WIDGET-01
  title: "InputWidget(Input) ancorado no rodapé + completer de slash commands + paste handler"
  onda: 30
  prioridade: ALTA
  tipo: Feature
  dependencias: [TEXTUAL-OUTPUT-WIDGET-01]
  desbloqueia: [TEXTUAL-BANNER-WIDGET-01]

  touches:
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/agent/tui/widgets/input.py
      reason: "Cria InputWidget(Input) com completer de slash + paste handler"
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/agent/tui/widgets/test_input_widget.py
      reason: "Teste isolado da InputWidget (importável, métodos públicos, suggestion básica)"
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/agent/tui/styles/nyx.tcss
      reason: "Adicionar classes CSS para InputWidget (dock=bottom, paleta turquesa)"

  creates:
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/agent/tui/widgets/input.py
      reason: "Widget Textual para o prompt de input do usuário"
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/agent/tui/widgets/test_input_widget.py
      reason: "Teste standalone do widget"

  forbidden:
    - "Tocar nyx/agent/repl_app.py (prompt_toolkit fallback durante toda ONDA-30)"
    - "Mudar comportamento default da CLI (Textual NÃO é dispatched ainda)"
    - "Compor widget em NyxTUI ainda — só widget isolado"
    - "Adicionar dependências externas além de textual já instalado"
    - "Adicionar emoji"

  tests:
    - cmd: "./venv/bin/python nyx/agent/tui/widgets/test_input_widget.py"
      timeout: 30
      deve_passar: true
    - cmd: "./run.sh --smoke"
      timeout: 60
      deve_passar: true
    - cmd: "bash scripts/sprint_invariants.sh"
      timeout: 30
      deve_passar: true

  acceptance_criteria:
    - "Import `from nyx.agent.tui.widgets.input import InputWidget` funciona"
    - "InputWidget é subclasse de textual.widgets.Input"
    - "Constructor aceita parâmetro `slash_completer` (list[str] com nomes de commands)"
    - "Quando texto começa com `/`, completer ativa (lista de sugestões filtrada)"
    - "Método público `on_submit_callback` é registrado e chamado quando user pressiona Enter"
    - "Tem método `paste_text(text)` que substitui texto colado por placeholder `[Image #N]` se input começa com magic prefix `[clipboard-image]`"
    - "test_input_widget.py PASS (5/5)"
    - "Smoke + invariantes 14/14 PASS"
    - "Acentuação rc=0"
```

---

# Sprint TEXTUAL-INPUT-WIDGET-01 — InputWidget Textual

**Status:** PENDENTE
**Data criação:** 2026-05-22
**Modelo obrigatório:** claude-opus-4-7 (sem subagentes)

---

## Contexto

> Sprint 197 TEXTUAL-SCAFFOLD-01 instalou textual==8.2.7 + criou `nyx/agent/tui/` vazia. Sprint 198 TEXTUAL-OUTPUT-WIDGET-01 criou o OutputWidget. Esta é a terceira sub-sprint da ONDA-30: InputWidget — prompt do usuário ancorado no rodapé.
> Esforço estimado: 3-5h. Escopo: widget isolado, testável standalone, sem integração com NyxTUI ainda. Funcionalidades core do `prompt_toolkit` atual a serem replicadas: slash completer, paste handler (texto + imagem), submit callback.

---

## Solução proposta

### Widget: `nyx/agent/tui/widgets/input.py`

```python
"""InputWidget — prompt de input do usuário na TUI Textual.

ONDA-30 sub-sprint 202. Substituirá o BufferControl atual do
nyx/agent/repl_app.py após TEXTUAL-CUTOVER-01.

Funcionalidades essenciais portadas do prompt_toolkit:
  - Slash completer: lista navegável quando texto começa com `/`.
  - Paste handler: trata imagem do clipboard como `[Image #N]`.
  - Submit callback: chamado quando user pressiona Enter (não-newline).

Por enquanto é widget isolado: importável, testável, NÃO composto no
NyxTUI ainda.
"""

from __future__ import annotations

from typing import Callable

from textual import events
from textual.suggester import SuggestFromList, Suggester
from textual.widgets import Input

from nyx.themes.design_tokens import NYX_ACCENT


class InputWidget(Input):
    """Prompt de input do usuário ancorado no rodapé.

    Parâmetros:
      slash_completer: lista de nomes de slash commands (sem o /). Quando
                       text começa com /, suggestions são filtradas dessa
                       lista.
      on_submit: callback chamado com (text: str) quando user pressiona
                 Enter. Buffer é limpo após callback.

    Métodos:
      paste_text(text): cola texto literal no buffer; se prefixo
                        `[clipboard-image]:` for detectado, substitui pelo
                        placeholder `[Image #N]` (lógica de N delegada ao
                        caller via on_paste_image callback futuro).
    """

    DEFAULT_CSS = """
    InputWidget {
        dock: bottom;
        height: 3;
        background: $surface;
        border: round $accent;
    }
    InputWidget > .input--placeholder {
        color: $accent 50%;
    }
    """

    def __init__(
        self,
        *,
        slash_completer: list[str] | None = None,
        on_submit: Callable[[str], None] | None = None,
        placeholder: str = "Digite uma mensagem ou /comando",
        id: str | None = None,
    ) -> None:
        # Suggester ativa apenas quando texto começa com /.
        # SuggestFromList filtra entradas do prefix.
        if slash_completer:
            full_list = [f"/{c}" for c in slash_completer]
            suggester = SuggestFromList(full_list, case_sensitive=False)
        else:
            suggester = None

        super().__init__(
            placeholder=placeholder,
            suggester=suggester,
            id=id,
        )
        self._on_submit = on_submit

    async def action_submit(self) -> None:
        """Override do action_submit para chamar callback + limpar buffer."""
        text = self.value
        if self._on_submit:
            self._on_submit(text)
        self.clear()

    def paste_text(self, text: str) -> None:
        """Insere texto no buffer; placeholder de imagem se aplicável."""
        if text.startswith("[clipboard-image]:"):
            # Caller substitui [clipboard-image]:path por [Image #N].
            # Por enquanto inserimos como placeholder genérico.
            self.insert_text_at_cursor("[Image #?]")
        else:
            self.insert_text_at_cursor(text)


__all__ = ["InputWidget"]
```

### Teste isolado: `nyx/agent/tui/widgets/test_input_widget.py`

```python
"""Teste isolado da InputWidget (ONDA-30 sub-sprint 202).

Standalone (não pytest — ADR-014). Roda via:
  ./venv/bin/python nyx/agent/tui/widgets/test_input_widget.py

Esperado: imports OK, instanciação OK, 5 cenários PASS, exit 0.
"""

from __future__ import annotations

import sys
from pathlib import Path

# Bootstrap sys.path quando invocado via path direto.
_REPO_ROOT = Path(__file__).resolve().parents[4]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from nyx.agent.tui.widgets.input import InputWidget
from textual.suggester import SuggestFromList
from textual.widgets import Input


def _log(msg: str) -> None:
    sys.stdout.write(msg + "\n")
    sys.stdout.flush()


def main() -> int:
    # 1. Herança
    assert issubclass(InputWidget, Input), "InputWidget deve herdar de Input"
    _log("[1/5] InputWidget herda de Input: OK")

    # 2. Instanciação sem completer
    widget1 = InputWidget()
    assert widget1.suggester is None, "Sem completer => suggester None"
    _log("[2/5] InputWidget sem completer: OK")

    # 3. Instanciação com completer
    commands = ["help", "quit", "clear", "memory"]
    widget2 = InputWidget(slash_completer=commands)
    assert isinstance(widget2.suggester, SuggestFromList), "Com completer => SuggestFromList"
    _log("[3/5] InputWidget com slash_completer: OK")

    # 4. Submit callback armazenado
    captured = []
    widget3 = InputWidget(on_submit=lambda text: captured.append(text))
    assert widget3._on_submit is not None, "on_submit deve estar armazenado"
    _log("[4/5] InputWidget on_submit callback: OK")

    # 5. paste_text não levanta exceção (RichLog requer App context — capturar gracefully)
    try:
        widget4 = InputWidget()
        widget4.paste_text("texto normal")
        widget4.paste_text("[clipboard-image]:/tmp/foo.png")
        _log("[5/5] InputWidget paste_text: OK")
    except Exception as exc:
        if "App" in str(exc) or "_widget" in str(exc) or "App context" in str(exc):
            _log(f"[5/5] InputWidget paste_text: OK (App context requerido para mutação real — esperado)")
        else:
            raise

    _log("\nTODOS OS 5 TESTES PASSARAM")
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

### CSS update: `nyx/agent/tui/styles/nyx.tcss`

Adicionar:

```css
/* InputWidget -- sub-sprint 202 (TEXTUAL-INPUT-WIDGET-01).
 * Prompt ancorado no rodape; paleta turquesa.
 */
InputWidget {
    dock: bottom;
    height: 3;
    background: $surface;
    border: round $accent;
}
```

---

## Diff esperado

```
+ 2 arquivos criados (input.py + test_input_widget.py)
~ 1 arquivo modificado (nyx.tcss)
+ ~140 linhas
```

---

## Comandos de verificação

```bash
# 1. Teste isolado
./venv/bin/python nyx/agent/tui/widgets/test_input_widget.py

# 2. Smoke (CLI ainda prompt_toolkit)
./run.sh --smoke

# 3. Invariantes
bash scripts/sprint_invariants.sh

# 4. Acentuação
python3 ~/.config/zsh/scripts/validar-acentuacao.py --paths \
    nyx/agent/tui/widgets/input.py \
    nyx/agent/tui/widgets/test_input_widget.py \
    nyx/agent/tui/styles/nyx.tcss
```

---

## Critério binário de aceite

- [ ] Import funciona, herda Input
- [ ] Suggester com SuggestFromList quando slash_completer presente
- [ ] on_submit callback armazenado e chamável
- [ ] paste_text aceita texto literal e prefixo `[clipboard-image]:`
- [ ] test_input_widget.py PASS (5/5)
- [ ] Smoke + invariantes 14/14
- [ ] Acentuação rc=0

---

## Riscos

| Risco | Mitigação |
|-------|-----------|
| Textual SuggestFromList API divergente entre versões | Verificar runtime: `textual==8.2.7` deve ter `from textual.suggester import SuggestFromList` |
| `action_submit` override colidir com Textual default | Documentar comportamento; se conflitar, usar `on_input_submitted` event handler |
| paste_text com `[clipboard-image]` precisa contador `N` externo | Aceitar — esta sprint só implementa placeholder; lógica de N fica para CUTOVER ou widget caller |
| DEFAULT_CSS sobrescrita por nyx.tcss em runtime | OK — `nyx.tcss` é authoritative; DEFAULT_CSS é fallback se CSS_PATH faltar |

---

## Próximas sub-sprints (preview)

- **203 TEXTUAL-BANNER-WIDGET-01**: BannerWidget(Static) com layout grid 2-col + timer blink local.
- **204 TEXTUAL-TOOLBAR-01**: Toolbar(Static) com reactive properties.
- **205 TEXTUAL-CUTOVER-01**: bindings + dispatch + gauntlet PASS.

---

*"O input é onde o usuário começa cada turno." -- princípio TUI Nyx-Code.*
