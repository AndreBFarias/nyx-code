## 0. SPEC

```yaml
sprint:
  id: AUDIT-FIX-07
  title: "Tool ask_user retorna via ActionResult (não imprime direto)"
  onda: 22
  bloco: 2
  prioridade: ALTA
  tipo: Bugfix
  dependencias: []

  touches:
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/agent/tools/ask_user.py
      reason: "Remover print() direto; tool devolve pergunta formatada; quem renderiza é a camada CLI"
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/agent/output.py
      reason: "Adiciona render_ask_user(question, options) para receber o ActionResult e renderizar via render layer"
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/cli.py
      reason: "Callback on_tool_result detecta tool=ask_user e chama render_ask_user antes de pedir input"

  forbidden:
    - "Continuar com print() dentro de ask_user.py"
    - "Mover o input() para dentro de ask_user.py (input bloqueia; tool não deve bloquear async loop por baixo)"
    - "Quebrar API da tool (parâmetros question/options mantidos)"

  tests:
    - cmd: "grep -n 'print(' nyx/agent/tools/ask_user.py | wc -l"
      esperado: "0"
    - cmd: "./run.sh --gauntlet --only rapido"
      deve_passar: true

  acceptance_criteria:
    - "Zero print() em nyx/agent/tools/ask_user.py"
    - "Tool ask_user.execute() retorna ActionResult com output estruturado (JSON-safe: dict com question + options)"
    - "nyx/agent/output.py tem função render_ask_user(question: str, options: list[dict]) -> None"
    - "cli.py detecta tool_use de ask_user e chama render_ask_user + input()"
    - "Gauntlet rapido passa; tool ask_user continua funcional no REPL"
```

---

# Sprint AUDIT-FIX-07 — ask_user retorna, não imprime

**Status:** PENDENTE
**Data criação:** 2026-04-18

## Contexto

- ADR-013 (Integração Obrigatória): tools retornam `ActionResult`; quem renderiza é `cli.py` via `output.py` (render layer, ADR-024).
- Finding A-03: `nyx/agent/tools/ask_user.py:68` usa `print(prompt_text)` diretamente. Isso quebra o contrato: a tool tem efeito colateral visual e bloqueia com `input()`.

## Problema

Tool que renderiza UI por conta própria:
1. Não é testável via `ActionResult`.
2. Fura isolamento (output.py deveria ser o único a desenhar no terminal).
3. `input()` síncrono dentro do agent loop async congela stream.

## Solução

1. **Remover `print()` e `input()` de `ask_user.py`**. A tool vira pura: recebe pergunta, retorna `ActionResult(success=True, output={"kind":"question", "question":..., "options":...})`.
2. **`output.py` ganha `render_ask_user(question, options)`**: responsável por desenhar o box com a pergunta e opções.
3. **`cli.py` intercepta tool_use de `ask_user`**: renderiza via `render_ask_user`, chama `input()` no contexto certo (fora do async flow tight), devolve a resposta como próxima entrada do usuário (via `agent.session.add_user` ou similar).

## Arquivos alvo

### `nyx/agent/tools/ask_user.py` — Depois

```python
"""AskUser -- Pergunta ao usuário e retorna payload estruturado.

A tool NÃO renderiza UI nem bloqueia com input(); retorna dict em
ActionResult.output. A camada CLI (output.py + cli.py) é quem renderiza
e coleta a resposta do humano.
"""

from __future__ import annotations

import logging
from typing import Any

from nyx.agent.models import ActionResult, ActionType
from nyx.agent.tools.base import RegisteredTool, ToolDef

logger = logging.getLogger("nyx.tools.ask_user")


class AskUserTool(RegisteredTool):
    action_type = ActionType.ANALYZE

    tool_def = ToolDef(
        name="ask_user",
        description=(
            "Faz uma pergunta ao usuário e aguarda resposta. "
            "Use quando precisar de decisão do usuário sobre abordagem, "
            "trade-offs ou confirmação. Pode incluir opções formatadas."
        ),
        parameters={
            "question": {"type": "string", "description": "Pergunta para o usuário"},
            "options": {
                "type": "array",
                "description": "Opções para o usuário escolher (opcional)",
                "items": {
                    "type": "object",
                    "properties": {
                        "label": {"type": "string"},
                        "description": {"type": "string"},
                    },
                    "required": ["label"],
                },
            },
        },
        required=["question"],
    )

    def execute(self, params: dict[str, Any], project_root: str) -> ActionResult:
        question = str(params.get("question", "")).strip()
        if not question:
            return ActionResult(success=False, error="Pergunta vazia")

        options = params.get("options", []) or []
        sanitized: list[dict[str, str]] = []
        if isinstance(options, list):
            for opt in options:
                if not isinstance(opt, dict):
                    continue
                label = str(opt.get("label", "")).strip()
                if not label:
                    continue
                desc = str(opt.get("description", "")).strip()
                sanitized.append({"label": label, "description": desc})

        payload = {
            "kind": "question",
            "question": question,
            "options": sanitized,
        }
        logger.info("ask_user: %s (%d opções)", question[:60], len(sanitized))
        return ActionResult(success=True, output=payload)


# "Perguntar é o início da sabedoria." -- Sócrates
```

### `nyx/agent/output.py` — Adicionar

```python
def render_ask_user(question: str, options: list[dict[str, str]] | None = None) -> None:
    """Renderiza pergunta do agent ao usuário, com opções numeradas se existirem."""
    ACCENT_FG = "\033[38;2;0;212;170m"
    DIM_FG = "\033[2m"
    NC_FG = "\033[0m"
    print()
    print(f"  {ACCENT_FG}[pergunta]{NC_FG} {question}")
    for i, opt in enumerate(options or [], 1):
        label = opt.get("label", "")
        desc = opt.get("description", "")
        if desc:
            print(f"    {ACCENT_FG}{i}.{NC_FG} {label} {DIM_FG}-- {desc}{NC_FG}")
        else:
            print(f"    {ACCENT_FG}{i}.{NC_FG} {label}")
    print()
```

### `nyx/cli.py` — on_tool_result interceptar ask_user

No callback `on_tool_result`, antes do `render_tool_result(result)`:

```python
def on_tool_result(name: str, result: str) -> None:
    if name == "ask_user":
        # result é JSON-string do payload — parsear e renderizar via render layer
        try:
            import json as _json
            payload = _json.loads(result) if result.startswith("{") else {}
        except _json.JSONDecodeError:
            payload = {}
        if payload.get("kind") == "question":
            from nyx.agent.output import render_ask_user
            render_ask_user(payload["question"], payload.get("options", []))
            # Coleta resposta do usuário e injeta como próxima mensagem
            try:
                answer = input("  Resposta: ").strip()
            except (EOFError, KeyboardInterrupt):
                answer = ""
            if answer:
                agent.session.add_user(f"[resposta] {answer}")
            return
    render_tool_result(result)
```

**Observação sobre o formato de `result`:** `ActionResult.output` é dict. Conferir como `loop.py` serializa (provavelmente `str(result.output)` ou `json.dumps(result.output)`). Ajustar parse conforme.

## Diff esperado

```
~ nyx/agent/tools/ask_user.py: 90→60 linhas (remove print/input)
~ nyx/agent/output.py: +15 linhas (render_ask_user)
~ nyx/cli.py: +15 linhas (on_tool_result branch)
```

## Comando de verificação

```bash
cd /home/andrefarias/Desenvolvimento/Nyx-Code

# 1. Zero print em ask_user.py
grep -n "print(" nyx/agent/tools/ask_user.py
# esperado: vazio

# 2. render_ask_user existe
grep -c "def render_ask_user" nyx/agent/output.py
# esperado: 1

# 3. cli.py intercepta
grep -c "render_ask_user" nyx/cli.py
# esperado: >= 1

# 4. Gauntlet
./run.sh --gauntlet --only rapido
```

## Critério binário

- [ ] `grep print nyx/agent/tools/ask_user.py` vazio
- [ ] `grep input nyx/agent/tools/ask_user.py` vazio (exceto em docstring)
- [ ] `render_ask_user` existe em output.py
- [ ] cli.py trata `ask_user` no `on_tool_result`
- [ ] Teste manual: rodar Nyx, pedir "faça me uma pergunta via ask_user" — funciona igual antes
- [ ] Gauntlet rapido passa
- [ ] Commit: `refactor: ask_user retorna payload, UI renderizada por output.py (ADR-013)`

## Guardrails anti-engodo

**NÃO marque como concluída se:**
- A IA só comentou o print (não remove de verdade).
- A IA moveu o print pra dentro de um if — continua violação.
- A IA deixou `input()` dentro da tool — continua bloqueio síncrono.
- Não há caminho visível (grep) em que `render_ask_user` é chamada a partir de cli.py.

## Validação humana

```bash
git show --stat HEAD
grep "print\|input" nyx/agent/tools/ask_user.py | grep -v '^#\|"""'
# esperado: vazio
./run.sh
# nyx> ask_user pergunta="qual sua cor favorita?" options=[...]
# deve aparecer o box de pergunta
```

## Riscos

| Risco | Mitigação |
|-------|-----------|
| `ActionResult.output` serialização quebra no loop | Testar com payload dict; se loop exigir str, fazer `json.dumps` na tool |
| Input bloqueia durante stream async | cli.py intercepta no `on_tool_result` que já é chamado fora do stream |

---

*"O silêncio do código puro vale mais que a sinfonia da gambiarra." -- anônimo*
