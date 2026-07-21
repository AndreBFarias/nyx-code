## 0. SPEC (machine-readable)

```yaml
sprint:
  id: TUI-ASK-USER-PLUMBING-01
  numero: 429
  title: "TUI: coletar a resposta do ask_user via modal e injetar [resposta] na sessão -- a decisao do usuário deixa de morrer no caminho interativo único"
  onda: 48
  prioridade: ALTA
  tipo: Bugfix
  dependencias: []
  desbloqueia: []
  absorve: []

  touches:
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/agent/tui/app.py
      reason: "interceptar name == ask_user + payload kind==question em _on_agent_tool_result; abrir modal (SelectScreen se ha options, PromptScreen se texto livre) e injetar self._agent.session.add_user('[resposta] ...') -- espelha cli_callbacks.py:88-112"
      linhas_alvo: "949-958 (_on_agent_tool_result)"
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/agent/loop/_iteration.py
      reason: "habilitar callback ASYNC no _on_tool_result via inspect.isawaitable + await -- espelha o padrão ja existente do _on_permission (linhas 397-404). Sem isso o modal (push_screen_wait, async) nunca abre porque o callback não e aguardado"
      linhas_alvo: "488-489 (chamada do _on_tool_result)"
  creates:
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/agent/tui/screens/prompt_screen.py
      reason: "modal de texto livre (ModalScreen[str] com Input) para ask_user SEM options -- espelha select_screen.py; a TUI não tem modal de input"
  removes: []

  forbidden:
    - "Adicionar emoji"
    - "Usar 'print()' fora de cli.py/output.py"
    - "Mencao a ferramenta de IA proprietaria ou trailer de co-autoria"
    - "Mudar o caminho não-ask_user de _on_agent_tool_result (segue mostrando '-> name: result' como hoje)"
    - "Tocar cli_callbacks.py (o REPL legado ja tem o handler; a TUI ESPELHA, não altera)"
    - "Tocar a semantica do _on_permission (397-404) -- a mudanca no loop e ADITIVA e do _on_tool_result (488-489)"
    - "Quebrar o caminho SYNC do _on_tool_result: callback que retorna None (REPL/headless) segue byte-identico (isawaitable(None) == False)"
    - "Renderizar o JSON cru como fallback quando o modal abre (o vazamento do JSON e coberto pela 406; aqui a resposta e coletada e o JSON não chega ao chat)"

  tests:
    - cmd: "/home/andrefarias/.local/bin/ruff check nyx/agent/tui/app.py nyx/agent/loop/_iteration.py nyx/agent/tui/screens/prompt_screen.py"
      deve_passar: true
    - cmd: "python3 ~/.config/zsh/scripts/validar-acentuacao.py --paths nyx/agent/tui/app.py nyx/agent/loop/_iteration.py nyx/agent/tui/screens/prompt_screen.py"
      deve_passar: true
    - cmd: "bash scripts/sprint_invariants.sh"
      deve_passar: true
    - cmd: "./run.sh --gauntlet --only rapido"
      timeout: 300
      deve_passar: true
      deferido_gpu: true

  acceptance_criteria:
    - "AC1: _on_agent_tool_result vira async e, quando name == 'ask_user' e o payload (json.loads do result) tem kind == 'question', não monta o ChatMessage cru -- abre um modal e coleta a resposta"
    - "AC2: com options presentes, abre SelectScreen(question, [(label, label) ...]); a seleção (str) vira a resposta; ESC/cancelar (None) não injeta nada"
    - "AC3: sem options (texto livre), abre a nova PromptScreen(question); o texto digitado vira a resposta; ESC/cancelar (None) não injeta nada"
    - "AC4: havendo resposta, injeta self._agent.session.add_user('[resposta] <answer>') -- mesmo formato de cli_callbacks.py:110 -- e monta um ChatMessage confirmando a resposta escolhida (feedback visual, espelha _open_select_modal)"
    - "AC5: _iteration.py aguarda o callback quando ele e awaitable (inspect.isawaitable + await), espelhando o _on_permission (397-404); callback sync (retorna None) segue byte-identico"
    - "AC6: PromptScreen criada em nyx/agent/tui/screens/prompt_screen.py, ModalScreen[str], espelhando select_screen.py (Binding escape -> dismiss(None), submit -> dismiss(texto))"
    - "AC7: proof Textual Pilot GPU-free colado: ask_user com options -> click na opção -> session recebe '[resposta] <label>' e ZERO ChatMessage('tool') com JSON cru; ruff limpo; acentuacao rc=0; FAIL_AFTER <= FAIL_BEFORE; smoke boot ok"
```

---

# Sprint TUI-ASK-USER-PLUMBING-01 -- a resposta do ask_user na TUI

**Status:** PENDENTE
**Data criação:** 2026-07-13
**Modelo obrigatorio:** claude-opus-4-7 (executor-sprint autorizado pelo dono nesta onda)

---

## Contexto do projeto (snapshot -- não referencia)

> **Missao (calibra o fix):** o Nyx-Code faz o pior LLM local (`qwen2.5-coder:3b`) na pior maquina possivel parecer um agente de codigo profissional offline. Robustez pertence a INFRA, não ao modelo (ADR-032/033/034). O usuario-alvo e leigo e sem hardware bom.
>
> **ADRs relevantes (inline):**
> - **ADR-026 (a ação não pode sumir / agencia do usuário):** quando a Nyx pergunta "vai por A ou B?", a decisao e do humano -- a UI tem que coletar a escolha, não decidir sozinha nem travar.
> - **ADR-013 / ADR-024:** a tool `ask_user` não renderiza UI nem bloqueia com `input()`; devolve payload estruturado em `ActionResult.output` e a camada de apresentacao (REPL: `output.py` + `cli_callbacks.py`; TUI: `app.py`) e quem renderiza e coleta a resposta.
> - **ADR-032/033 (a infra carrega o modelo / enforcement):** quando a infra não garante, a mensagem ao usuário e clara; aqui a infra (a TUI) tem que fechar o ciclo de decisao que hoje esta morto.
>
> **Estado (2026-07-13):** `qwen2.5-coder:3b`. TUI baseada em Textual (migrada de prompt_toolkit na ONDA-32; widgets em `nyx/agent/tui/`). ONDA-48 fase raiz: nucleo do contrato CONCLUIDO. Este e um achado da auditoria de prontidao 2026-07-12 (verificado adversarialmente). O REPL legado (`cli_callbacks.py`) tem o handler completo do `ask_user`; a TUI, que e o caminho interativo único da v1.4, não tem NADA -- `rg ask_user nyx/agent/tui/` retorna zero.

---

## Problema

**Achado (auditoria 2026-07-12, ALTA):** na TUI o `ask_user` esta quebrado ponta a ponta. A tool executa e devolve JSON estruturado; o callback da TUI so monta o JSON cru no chat e **não existe plumbing para o usuário responder dentro do turno**. O loop segue para a proxima iteracao sem resposta, e o modelo decide sozinho ou trava. Para o usuário leigo, a agencia (ADR-026) esta morta no único caminho interativo.

**Evidencia literal (verificada no codigo real 2026-07-13):**

- `nyx/agent/tools/ask_user.py:65-71` -- a tool devolve `payload = {"kind": "question", "question": question, "options": sanitized}` serializado (`ActionResult(success=True, output=json.dumps(payload, ensure_ascii=False))`). `options` e opcional (`required=["question"]`), entao existe o caminho de texto livre.
- `nyx/agent/tui/app.py:949-958` -- `_on_agent_tool_result(self, name, result="")` e **sync** e faz apenas `chat.mount(ChatMessage("tool", f"-> {name}: {result}"))`. Nenhum caso especial para `ask_user`. O JSON cru vai para a tela e a resposta nunca e coletada.
- `nyx/cli_callbacks.py:88-112` -- o REPL legado tem o handler completo: `if payload.get("kind") == "question": render_ask_user(...)` + `input("  Resposta: ")` + mapeamento de opção numerica para label + `agent_ref[0].session.add_user(f"[resposta] {answer}")`. A TUI precisa espelhar essa semantica com um modal (a TUI e async, não pode usar `input()` bloqueante).

---

## Causa-raiz (verificada no codigo -- DIVERGENCIA do briefing registrada aqui)

O briefing sugere "interceptar em `_on_agent_tool_result` e abrir um modal". Correto, mas **incompleto**: a investigacao revelou um pre-requisito no loop que o briefing não menciona.

- `nyx/agent/loop/_iteration.py:488-489`:
  ```python
              if self._on_tool_result:
                  self._on_tool_result(name, result.output if result.success else result.error)
  ```
  O `_on_tool_result` e chamado **sync, sem `await` e sem `inspect.isawaitable`**. Isso e DIFERENTE do `_on_permission` (mesmo arquivo, linhas 397-404), que ja suporta callback async:
  ```python
                  approved = self._on_permission(perm, name, args)
                  if inspect.isawaitable(approved):
                      approved = await approved
  ```
- Consequencia: se o executor apenas transformar `_on_agent_tool_result` em `async def` (necessario para `push_screen_wait`, que e async), a corrotina retornada **nunca sera aguardada** -- o modal jamais abre e ainda ha `RuntimeWarning: coroutine was never awaited`. Por isso o fix EXIGE um toque aditivo em `_iteration.py:488-489` espelhando o padrão ja consagrado do `_on_permission`.
- `inspect` ja esta importado (`nyx/agent/loop/_iteration.py:12`), entao a mudanca no loop e minima e ADITIVA.

**Outro ponto verificado:** `ask_user` tem `action_type = ActionType.ANALYZE` (`nyx/agent/tools/ask_user.py:21`) -- e uma ação de leitura, **não passa por permissao**. Logo o `_on_permission` não ajuda aqui; o único ponto de interceptacao valido e o `_on_tool_result`.

**Acesso a sessão verificado:** `AgentLoop` expoe a property publica `session` (`nyx/agent/loop/_core.py:637`, `def session(self) -> CodeSession`) e `CodeSession.add_user` existe (`nyx/agent/session.py:46`). A TUI guarda o `AgentLoop` em `self._agent` (`nyx/agent/tui/app.py:194`), o mesmo objeto do REPL. Portanto `self._agent.session.add_user(...)` e valido -- identico ao `agent_ref[0].session.add_user(...)` do REPL.

**Por que awaitar o callback e seguro (loop affinity ONDA-33):** o turno roda como worker async NO event loop do Textual (`_process_turn`, `nyx/agent/tui/app.py:742`). Suspender a corrotina do turno em `push_screen_wait` deixa o event loop continuar bombeando eventos de UI -- o modal aparece, o usuário responde, a corrotina resume. E exatamente o que o `_on_agent_permission` (`app.py:913`) ja faz com `ConfirmScreen`.

---

## solução proposta

Tres mudancas, todas cirurgicas, espelhando padrões que ja existem no repo:

1. **`_iteration.py:488-489`** -- aguardar o `_on_tool_result` quando ele for awaitable (`inspect.isawaitable` + `await`), copia fiel do bloco `_on_permission` (397-404). Callback sync segue byte-identico.
2. **`app.py:949-958`** -- `_on_agent_tool_result` vira `async def`; intercepta `name == "ask_user"` com payload `kind == "question"`; abre `SelectScreen` (se ha `options`) ou a nova `PromptScreen` (texto livre); injeta `self._agent.session.add_user(f"[resposta] {answer}")` e monta um `ChatMessage` confirmando. Todo o resto (qualquer outra tool) segue montando `-> name: result` como hoje.
3. **CRIAR `nyx/agent/tui/screens/prompt_screen.py`** -- `ModalScreen[str]` com um `Input`, espelhando `select_screen.py`: `escape` -> `dismiss(None)`, submit (Enter/botão) -> `dismiss(texto)`. A TUI não tem modal de input; `SelectScreen` so cobre o caso com opções.

Mapeamento de paridade com o REPL (`cli_callbacks.py:88-112`):

| REPL (`cli_callbacks.py`) | TUI (`app.py`, esta sprint) |
|---|---|
| `render_ask_user(question, options)` | modal (`SelectScreen`/`PromptScreen`) mostra a pergunta |
| `input("  Resposta: ")` (bloqueia o loop sync) | `await self.push_screen_wait(...)` (suspende o turno async) |
| resposta numerica -> `options[idx].label` | `SelectScreen` ja devolve o `value` (o próprio label) |
| `agent_ref[0].session.add_user(f"[resposta] {answer}")` | `self._agent.session.add_user(f"[resposta] {answer}")` |
| cancelou (answer vazio) -> não injeta | `None` (ESC) -> não injeta |

**Ordem na sessão (paridade):** no REPL o `add_user([resposta])` roda DENTRO do `_on_tool_result` (portanto ANTES do `_iteration.py:491 add_tool_call`). A TUI mantem a mesma ordem: injeta no callback, o loop registra o tool_call logo depois. não inverter.

---

## Arquivos alvo (paths absolutos)

### `/home/andrefarias/Desenvolvimento/Nyx-Code/nyx/agent/loop/_iteration.py`

#### Edit 1 -- aguardar o `_on_tool_result` awaitable (espelha `_on_permission` 397-404)

# Localizacao: linhas 488-489
**Antes:**
```python
            if self._on_tool_result:
                self._on_tool_result(name, result.output if result.success else result.error)
```
**Depois:**
```python
            if self._on_tool_result:
                # TUI-ASK-USER-PLUMBING-01: suporta callback ASYNC (espelha
                # _on_permission, 397-404). A TUI abre um modal e ESPERA a
                # resposta (push_screen_wait, async) no caso ask_user. Callback
                # sync (REPL/headless) retorna None -- isawaitable(None) == False,
                # entao o caminho sync segue byte-identico.
                maybe = self._on_tool_result(
                    name, result.output if result.success else result.error
                )
                if inspect.isawaitable(maybe):
                    await maybe
```

### `/home/andrefarias/Desenvolvimento/Nyx-Code/nyx/agent/tui/app.py`

#### Edit 2 -- `_on_agent_tool_result` async + interceptacao do ask_user

# Localizacao: linhas 949-958 (metodo inteiro)
**Antes:**
```python
    def _on_agent_tool_result(self, name: str, result: Any = "") -> None:
        """Callback patcheado em agent._on_tool_result.

        Signature real do AgentLoop: `_on_tool_result(name, result.output
        if result.success else result.error)` -- 2 args, segundo eh string
        (output ou error). Ver loop/_iteration.py:183.
        """
        chat = self.query_one("#chat", VerticalScroll)
        chat.mount(ChatMessage("tool", f"-> {name}: {result}"))
        self._follow_end(chat)
```
**Depois (esboco -- o executor ajusta imports/detalhes):**
```python
    async def _on_agent_tool_result(self, name: str, result: Any = "") -> None:
        """Callback patcheado em agent._on_tool_result (agora ASYNC).

        Signature real do AgentLoop: `_on_tool_result(name, result.output
        if result.success else result.error)` -- 2 args, segundo eh string
        (output ou error). Ver loop/_iteration.py:488.

        TUI-ASK-USER-PLUMBING-01: intercepta ask_user (payload kind==question)
        e abre um modal (SelectScreen se ha options, PromptScreen se texto
        livre), injetando a resposta na sessão. Espelha cli_callbacks.py:88-112.
        O loop aguarda este callback (isawaitable, _iteration.py:488-489).
        """
        if name == "ask_user":
            payload = self._parse_ask_user_payload(result)
            if payload is not None:
                await self._handle_ask_user(payload)
                return
        chat = self.query_one("#chat", VerticalScroll)
        chat.mount(ChatMessage("tool", f"-> {name}: {result}"))
        self._follow_end(chat)

    @staticmethod
    def _parse_ask_user_payload(result: Any) -> dict | None:
        """Desserializa o JSON do ask_user; None se não for question."""
        import json

        if not isinstance(result, str) or not result.startswith("{"):
            return None
        try:
            payload = json.loads(result)
        except json.JSONDecodeError:
            return None
        return payload if payload.get("kind") == "question" else None

    async def _handle_ask_user(self, payload: dict) -> None:
        """Abre o modal do ask_user e injeta '[resposta] ...' na sessão.

        options presentes -> SelectScreen; texto livre -> PromptScreen.
        ESC/cancelar (None) não injeta nada (paridade cli_callbacks:88-112).
        """
        question = str(payload.get("question", "")).strip()
        options = payload.get("options", []) or []
        chat = self.query_one("#chat", VerticalScroll)

        if options:
            from nyx.agent.tui.screens.select_screen import SelectScreen

            choices = [(o.get("label", ""), o.get("label", "")) for o in options if o.get("label")]
            answer = await self.push_screen_wait(SelectScreen(question, choices))
        else:
            from nyx.agent.tui.screens.prompt_screen import PromptScreen

            answer = await self.push_screen_wait(PromptScreen(question))

        if answer and self._agent is not None:
            self._agent.session.add_user(f"[resposta] {answer}")
            chat.mount(ChatMessage("tool", f"resposta: {answer}"))
        else:
            chat.mount(ChatMessage("tool", "pergunta cancelada"))
        self._follow_end(chat)
```

### CRIAR `/home/andrefarias/Desenvolvimento/Nyx-Code/nyx/agent/tui/screens/prompt_screen.py`

# Espelha select_screen.py. ModalScreen[str]: submit -> dismiss(texto), ESC -> dismiss(None).
```python
"""PromptScreen -- ModalScreen Textual para uma resposta de texto livre.

Usada pelo ask_user (nyx/agent/tools/ask_user.py) quando a pergunta não tem
options. Espelha select_screen.py; substitui o input() bloqueante do REPL
(cli_callbacks.py:101) por um modal async compativel com o event loop do Textual.
"""

from __future__ import annotations

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Container, Vertical
from textual.screen import ModalScreen
from textual.widgets import Input, Static


class PromptScreen(ModalScreen[str]):
    """Modal de resposta em texto livre.

    Uso:
        answer = await self.push_screen_wait(PromptScreen("Qual o nome do modulo?"))
        # answer vem como str (texto) ou None (ESC cancelou)
    """

    DEFAULT_CSS = """
    PromptScreen { align: center middle; }
    PromptScreen > Container {
        width: 60%;
        max-width: 80;
        height: auto;
        background: $surface;
        border: heavy $accent;
        padding: 1 2;
    }
    PromptScreen Vertical { height: auto; }
    PromptScreen #modal-title {
        color: $accent;
        text-style: bold;
        margin: 0 0 1 0;
    }
    PromptScreen Input { width: 100%; }
    """

    BINDINGS = [
        Binding("escape", "cancel", "Cancelar", priority=True),
    ]

    def __init__(self, title: str) -> None:
        super().__init__()
        self._title = title

    def compose(self) -> ComposeResult:
        with Container():
            with Vertical():
                yield Static(self._title, id="modal-title")
                yield Input(placeholder="Resposta...", id="prompt-input")

    def on_mount(self) -> None:
        self.query_one("#prompt-input", Input).focus()

    def on_input_submitted(self, event: Input.Submitted) -> None:
        self.dismiss(event.value.strip())

    def action_cancel(self) -> None:
        self.dismiss(None)


__all__ = ["PromptScreen"]
```

---

## Diff esperado (resumo)

```
~ 2 arquivos modificados (nyx/agent/loop/_iteration.py, nyx/agent/tui/app.py)
+ 1 arquivo criado   (nyx/agent/tui/screens/prompt_screen.py, ~70L)
+ ~55 linhas liquidas -- fix aditivo; nenhum arquivo passa de 1200L
```

Sem aritmetica de extracao: esta sprint não tem meta `arquivo < NNNL`. O único numero relevante e o net-add (~55L), sem reducao de tamanho alvo.

---

## Comandos de verificação (literais, copy-paste)

```bash
cd /home/andrefarias/Desenvolvimento/Nyx-Code

# 1. Estatica + acentuacao (ruff via binario direto -- não ha modulo ruff no venv, ver BRIEF)
/home/andrefarias/.local/bin/ruff check nyx/agent/tui/app.py nyx/agent/loop/_iteration.py nyx/agent/tui/screens/prompt_screen.py
python3 ~/.config/zsh/scripts/validar-acentuacao.py --paths nyx/agent/tui/app.py nyx/agent/loop/_iteration.py nyx/agent/tui/screens/prompt_screen.py

# 2. Confirmar as ancoras (linhas podem ter deslizado -- reconferir):
rg -n "_on_tool_result|isawaitable|_on_agent_tool_result|push_screen_wait|add_user" nyx/agent/loop/_iteration.py nyx/agent/tui/app.py

# 3. PROOF Textual Pilot (PRIMARIA, GPU-free -- não precisa do modelo nem do Ollama):
#    ask_user COM options -> click na opção -> a sessão recebe [resposta] <label>
#    e NENHUM ChatMessage('tool') carrega JSON cru.
./venv/bin/python - <<'PY'
import asyncio, json
from nyx.agent.tui.app import NyxTUI
from nyx.agent.loop._core import AgentLoop
from nyx.agent.tui.widgets.chat_message import ChatMessage

async def main():
    agent = AgentLoop(project_root=".")
    app = NyxTUI(agent=agent)
    async with app.run_test() as pilot:
        payload = json.dumps({
            "kind": "question",
            "question": "vai por A ou B?",
            "options": [{"label": "A", "description": ""}, {"label": "B", "description": ""}],
        }, ensure_ascii=False)
        task = asyncio.create_task(app._on_agent_tool_result("ask_user", payload))
        await pilot.pause()
        await pilot.click("#opt-A")   # botão da opção A no SelectScreen
        await task
        # a sessão deve conter um turno de usuário "[resposta] A"
        msgs = [getattr(m, "content", "") for m in agent.session.messages]
        assert any("[resposta] A" in str(c) for c in msgs), msgs
        # nenhum ChatMessage('tool') deve conter o JSON cru
        tools = [w for w in app.query(ChatMessage)
                 if getattr(w, "_role", getattr(w, "role", "")) == "tool"]
        raw = [getattr(w, "_content", getattr(w, "content", "")) for w in tools]
        assert not any('"kind"' in str(t) for t in raw), raw
        print("OK: [resposta] A injetada; ZERO JSON cru no chat")

asyncio.run(main())
PY
# NOTA: o acessor exato (agent.session.messages / _role) pode diferir -- o executor
# ajusta ao shape real de CodeSession/ChatMessage (grep no arquivo). O que importa
# e a ASSERCAO: a resposta entrou na sessão e o JSON não vazou.

# 4. Variante texto livre: payload sem 'options' -> PromptScreen; digitar via
#    pilot (app.query_one('#prompt-input', Input).value = 'foo'; pilot.press('enter'))
#    -> session recebe '[resposta] foo'.

# 5. Gauntlet rapido (regressao geral) -- DEFERIDO para GPU exclusiva.
./run.sh --gauntlet --only rapido
```

> Nota GPU: os passos 3-4 rodam SEM Ollama/GPU (o Pilot monta a TUI headless; `AgentLoop` instancia sem tocar a GPU -- ela so e exigida em `run()`/`_call_llm`). O passo 5 (gauntlet) exige GPU exclusiva -- executar so quando `pgrep -af "Luna.*driver|valida_sprint"` estiver vazio (protocolo anti-contencao do BRIEF). Marcar o gauntlet como DEFERIDO ate a janela de GPU exclusiva (paridade com as specs 403/407).

---

## Criterio binario de aceite (IA executora)

- [ ] `_on_agent_tool_result` async; `name == "ask_user"` + `kind == "question"` abre modal, não monta JSON cru
- [ ] options presentes -> `SelectScreen`; texto livre -> `PromptScreen` (criada)
- [ ] resposta -> `self._agent.session.add_user(f"[resposta] {answer}")` (formato identico a cli_callbacks:110); ESC/None não injeta
- [ ] `_iteration.py:488-489` aguarda o callback via `inspect.isawaitable` + `await` (espelha `_on_permission`); caminho sync byte-identico
- [ ] `PromptScreen` em `nyx/agent/tui/screens/prompt_screen.py`, `ModalScreen[str]`, espelha `select_screen.py`
- [ ] Proof Textual Pilot colado (passo 3): `[resposta] <label>` na sessão, ZERO JSON cru em `ChatMessage('tool')`
- [ ] Caminho não-ask_user intacto (segue `-> name: result`)
- [ ] `ruff` limpo, acentuacao rc=0, `FAIL_AFTER <= FAIL_BEFORE`, smoke boot ok
- [ ] Gauntlet `--only rapido` 100% (DEFERIDO ate GPU exclusiva)
- [ ] `SPRINT_ORDER_MASTER.md` marca 429 CONCLUIDA; spec movida para `concluidos/` (integração do orquestrador)
- [ ] não commitar; não tocar Checkpoint.md; não tocar `cli_callbacks.py`

---

## Guardrails anti-engodo (obrigatorios)

não marcar concluida se:
- O JSON cru do `ask_user` ainda aparece no chat (o modal tem que abrir NO LUGAR do `-> name: result`).
- A resposta não entra na sessão com o prefixo `[resposta] ` (o modelo não ve a escolha e decide sozinho -- o bug original persiste).
- Tornou `_on_agent_tool_result` async mas não tocou `_iteration.py:488-489` (a corrotina nunca e aguardada -- modal não abre, `RuntimeWarning`).
- Quebrou o caminho sync do `_on_tool_result` (callback do REPL retorna None -- tem que seguir byte-identico; `isawaitable(None)` e False).
- Alterou `_on_permission` (397-404) ou removeu/reordenou handlers do loop -- a mudanca e ADITIVA e restrita ao `_on_tool_result`.
- Proof Pilot não colado, ou a assercao de `[resposta]`/ausencia de JSON cru não passa.
- Tocou `cli_callbacks.py` (o REPL ja funciona; a TUI ESPELHA, não altera o REPL).

Se algo falhar: `[SPRINT 429] BLOQUEADA: <motivo 1 linha>`.

---

## Proof-of-work esperado (4 passos)

```bash
bash scripts/sprint_invariants.sh > /tmp/inv_before.txt 2>&1
FAIL_BEFORE=$(grep -c "^\[FAIL\]" /tmp/inv_before.txt)
# implementar
bash scripts/sprint_invariants.sh > /tmp/inv_after.txt 2>&1
FAIL_AFTER=$(grep -c "^\[FAIL\]" /tmp/inv_after.txt)
diff /tmp/inv_before.txt /tmp/inv_after.txt
```
Baseline esperado: `FAIL_BEFORE = 0`, `FAIL_AFTER <= 0`. Colar: inv_before/inv_after (tail), diff, o output do proof Pilot (passos 3-4), o `rg` do passo 2, `git --no-pager diff --stat` e `./run.sh --smoke` (deve imprimir `boot ok`).

Runtime real (contratos do VALIDATOR_BRIEF, seção [CORE]):
- Smoke: `./run.sh --smoke` -> `boot ok`, exit 0.
- Invariantes: `bash scripts/sprint_invariants.sh` -> PASS 14/14, FAIL 0.
- Pilot GPU-free: passos 3-4 acima (não exige modelo).
- Gauntlet `--only rapido`: **DEFERIDO** para janela de GPU exclusiva (paridade specs 403/407).

---

## Gambiarras especificas desta sprint

- **`_on_tool_result` awaitable:** a alternativa a mexer no loop seria a TUI disparar `run_worker(self._handle_ask_user(...))` e não bloquear o turno -- mas ai o loop segue para a proxima iteracao ANTES da resposta, que e exatamente o bug. Bloquear o turno (awaitar) e obrigatorio para a paridade com o `input()` sincrono do REPL. Por isso o toque no `_iteration.py` e o nucleo, não um extra.
- **`SelectScreen` devolve o label:** as opções viram `(label, label)`; o REPL mapeia resposta numerica para label, o `SelectScreen` ja entrega o label direto -- a resposta injetada e o label, identico ao REPL.
- **`json` import local:** `_parse_ask_user_payload` importa `json` no corpo (espelha `cli_callbacks.py:90` que faz `import json as _json` local) para não inflar o topo de `app.py`; alternativamente usar o import ja presente se houver.
- **`PromptScreen` foco no Input:** `on_mount` foca o `Input` para o usuário digitar direto sem clicar -- UX de teclado (o usuario-alvo e leigo).

---

## Fora de escopo (anti-debito)

| Item | Decisao |
|---|---|
| Vazamento do JSON cru do `ask_user` como sintoma visual generico de tool_result | Coberto pela **406 (TUI-INTERNALS-LEAK-01)**. Esta sprint resolve a COLETA da resposta; a higienizacao generica do render de tool_result e da 406. Sem sobreposicao: aqui o `ask_user` NUNCA chega ao render generico (e interceptado antes). |
| Timeout/expiracao do modal (se o usuário nunca responde) | não-objetivo. O `input()` do REPL tambem bloqueia indefinidamente; paridade preservada. Se o dono quiser timeout, registrar `TUI-ASK-USER-TIMEOUT-01` (feedback_nenhum_debito). |
| Renderizar `description` das options no modal (hoje o `SelectScreen` so mostra o label) | não-objetivo desta sprint -- o `SelectScreen` atual so exibe label. Melhoria de UX registravel como sprint própria se o dono pedir. |
| Persistir a pergunta+resposta no histórico de chat de forma rica (card) | Fora de escopo; a sprint monta um `ChatMessage("tool", "resposta: ...")` simples (paridade minima com `_open_select_modal`). |

---

## Referencias

- BRIEF: `/home/andrefarias/Desenvolvimento/Nyx-Code/VALIDATOR_BRIEF.md`
- Origem: auditoria de prontidão 2026-07-12, relatório durável `dev-journey/07-reports/AUDIT_2026_07_12.md` §3 (briefing efêmero da sessão de auditoria)
- Handler de paridade (REPL): `nyx/cli_callbacks.py:88-112`
- Padrao async ja existente no loop: `nyx/agent/loop/_iteration.py:397-404` (`_on_permission`)
- Modal precedente: `nyx/agent/tui/screens/select_screen.py`; callback async precedente: `nyx/agent/tui/app.py:913` (`_on_agent_permission`)
- Estrutura de referencia: `dev-journey/06-sprints/producao/SPRINT_EXEC_CONTRACT_PROXY_STATUS_BEFORE_JSON_01.md`

---

*"Quando a Nyx pergunta 'vai por A ou B?', quem decide e o humano -- uma pergunta sem resposta possivel e pior que nenhuma pergunta." -- ADR-026 (a ação, e a decisao, não podem sumir).*
