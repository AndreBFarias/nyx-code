## 0. SPEC (machine-readable)

```yaml
sprint:
  id: TUI-INTERNALS-LEAK-01
  title: "Render-layer: a TUI não exibe args/internals crus dos eventos tool_use (V09)"
  onda: 48
  prioridade: ALTA
  tipo: Bugfix
  dependencias: [OUTPUT-LEAK-SANITIZE-01]
  desbloqueia: []

  touches:
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/agent/tui/app.py
      reason: "_on_agent_tool renderiza name(args_dict cru); _on_agent_tool_result renderiza result cru com hints de controle"
      linhas_alvo: "880-890 (_on_agent_tool), 949-958 (_on_agent_tool_result)"
  creates: []
  removes: []

  forbidden:
    - "Adicionar emoji"
    - "Usar 'print()' fora de cli.py/output.py (ADR-024)"
    - "Mencao a IA proprietaria"
    - "Tocar o loop de execução (399/397/400/398/401) -- esta sprint e SO a render-layer da TUI"
    - "Esconder o NOME da tool ou o ato de executar -- o usuario deve ver QUE tool rodou, so não o lixo cru"

  tests:
    - cmd: "./run.sh --gauntlet --only rapido"
      timeout: 300
      deve_passar: true

  acceptance_criteria:
    - "_on_agent_tool renderiza forma COMPACTA (nome + arg-chave truncado: path/command/pattern), não o dict cru com content inteiro"
    - "_on_agent_tool_result remove os hints de controle ('...chame done()', '[N linhas lidas...]', system-reminder) e trunca antes de exibir"
    - "O NOME da tool e o fato de ter rodado continuam visiveis (não esconder a ação)"
    - "Proof Textual Pilot (GPU-free): mock de tool_use/tool_result -> ChatMessage limpo, sem dict cru nem 'chame done()'"
    - "Gauntlet rapido 100%"
```

---

# Sprint TUI-INTERNALS-LEAK-01 — Render-layer: TUI não vomita internals

**Status:** PENDENTE
**Data criação:** 2026-06-26
**Modelo obrigatório:** claude-opus-4-7 (executor-sprint autorizado pelo dono nesta onda)

---

## Contexto do projeto (snapshot — não referência)

> **ADRs relevantes (inline):**
> - **ADR-024 Render layer:** a apresentação é responsabilidade da borda (cli.py/output.py/TUI), não do loop. A TUI deve exibir os eventos tool_use de forma limpa.
> - **ADR-026:** nada silencioso -- mas "não silencioso" é mostrar QUE rodou, não despejar o dict cru.
> - ADR-005 Anonimato, ADR-006 PT-BR, ADR-014 Testes via Gauntlet.
>
> **Estado (2026-06-26):** TUI Textual (`nyx/agent/tui/app.py`, `ChatMessage` widget). A 395 (OUTPUT-LEAK-SANITIZE) limpou o SUMMARY user-facing; esta sprint limpa o RENDER AO VIVO dos eventos tool_use na TUI. Achado: `dev-journey/07-reports/AUDIT_VALIDACAO_2026_06_26.md` (V09, visto ao vivo no Chrome). Os helpers de strip existem em `nyx/agent/loop/_core.py` (`_DONE_HINT_RE`, `_TOOL_HINT_BRACKET_RE`) e `_iteration.py` (`strip_system_reminder`).

---

## Problema

**Achado V09 INTERNALS-LEAK-TUI [ALTA]:** na TUI a tela **vomita** tool_calls crus, resultados de tool e hints de controle. Verificado no código:
- `nyx/agent/tui/app.py:889` -- `_on_agent_tool` monta `ChatMessage("tool", f"{name}({args_str})")` onde `args_str = str(args)` é o **dict cru inteiro**, incluindo `content` de um write_file (o arquivo todo) e paths com aspas/escape.
- `nyx/agent/tui/app.py:957` -- `_on_agent_tool_result` monta `ChatMessage("tool", f"-> {name}: {result}")` onde `result` é a saída crua, **com** os hints de controle anexados pelas tools (" Se a tarefa está completa, chame done().", "[N linhas lidas...]") e eventuais blocos `<system-reminder>` ecoados.

Resultado: a borda visual mostra ao usuário o formato interno (dict de args, instruções de done, reminders) em vez de uma representação limpa do que a Nyx está fazendo.

---

## Solução proposta

Limpar a render-layer dos DOIS callbacks (ADR-024, sem tocar o loop):
1. `_on_agent_tool`: exibir forma **compacta** -- `nome` + o **arg-chave** (file_path/path/command/cmd/pattern/url) truncado, NÃO o dict cru com `content`. Reusar a lógica de `_format_perm_detail` (já extrai esses args).
2. `_on_agent_tool_result`: **sanear** o texto antes de exibir -- aplicar `strip_system_reminder` + remover os hints de controle (`_DONE_HINT_RE`, `_TOOL_HINT_BRACKET_RE` de `_core.py`) + truncar (ex.: 600 chars) -- e manter o nome da tool visível.

O NOME da tool e o fato de ter rodado seguem visíveis (ADR-026: ação não some); só o lixo cru sai.

---

## Arquivos alvo (paths absolutos)

### `/home/andrefarias/Desenvolvimento/Nyx-Code/nyx/agent/tui/app.py`

#### Edit 1 — import dos helpers de strip (junto dos imports do topo)

# Localização: bloco de imports (ex.: junto de `from nyx.agent.tui.widgets.chat_message import ChatMessage`)
**Depois (adicionar):**
```python
from nyx.agent.loop._core import _DONE_HINT_RE, _TOOL_HINT_BRACKET_RE
from nyx.agent.loop._iteration import strip_system_reminder
```

#### Edit 2 — `_on_agent_tool` compacto

# Localização aproximada: linha 880-890
**Antes:**
```python
    def _on_agent_tool(self, name: str, args: Any) -> None:
        """Callback patcheado em agent._on_tool.

        Signature real do AgentLoop: `_on_tool(name, args)` -- 2 args
        posicionais (ver loop/_iteration.py:85). Monta ChatMessage("tool")
        com representacao compacta dos args.
        """
        args_str = "" if args is None else str(args)
        chat = self.query_one("#chat", VerticalScroll)
        chat.mount(ChatMessage("tool", f"{name}({args_str})"))
        self._follow_end(chat)
```
**Depois:**
```python
    def _on_agent_tool(self, name: str, args: Any) -> None:
        """Callback patcheado em agent._on_tool.

        TUI-INTERNALS-LEAK-01 (V09): exibe forma COMPACTA (nome + arg-chave
        truncado), não o dict cru com content inteiro. O usuario ve QUE tool
        rodou e sobre o que, sem o lixo de formato interno (ADR-024/026).
        """
        detail = self._format_perm_detail(name, args) if isinstance(args, dict) else ""
        label = f"{name}: {detail}" if detail else name
        chat = self.query_one("#chat", VerticalScroll)
        chat.mount(ChatMessage("tool", label))
        self._follow_end(chat)
```

#### Edit 3 — `_on_agent_tool_result` saneado

# Localização aproximada: linha 949-958
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
**Depois:**
```python
    def _on_agent_tool_result(self, name: str, result: Any = "") -> None:
        """Callback patcheado em agent._on_tool_result.

        TUI-INTERNALS-LEAK-01 (V09): saneia o resultado antes de exibir --
        remove os hints de controle (' ...chame done()', '[N linhas lidas...]')
        e blocos <system-reminder> que as tools/loop anexam, e trunca. O nome da
        tool segue visivel (ADR-024/026). Os mesmos regex do guard de saida do
        loop (_core.py) sao reusados -- fonte unica.
        """
        text = "" if result is None else str(result)
        text = strip_system_reminder(text)
        text = _DONE_HINT_RE.sub("", text)
        text = _TOOL_HINT_BRACKET_RE.sub("", text)
        text = text.strip()
        if len(text) > 600:
            text = text[:600] + " [...]"
        chat = self.query_one("#chat", VerticalScroll)
        chat.mount(ChatMessage("tool", f"-> {name}: {text}" if text else f"-> {name}"))
        self._follow_end(chat)
```

> **Nota ao executor:** confirme via grep que `_format_perm_detail` (app.py:927) existe e
> tem a assinatura `(self, name, args)` retornando string (extrai file_path/path/command/
> cmd/pattern/url). Confirme que `_DONE_HINT_RE`/`_TOOL_HINT_BRACKET_RE` são module-level em
> `_core.py` e que `strip_system_reminder` é importável de `_iteration.py` (ambos já usados
> pelo guard de saída). Se algum import causar ciclo (app.py -> _core -> _iteration), prefira
> definir os 2 regex localmente em app.py espelhando os de `_core.py` com comentário de fonte.

---

## Diff esperado (resumo)

```
~ 1 arquivo modificado (tui/app.py)
+ ~20 linhas líquidas
```

---

## Comandos de verificação (literais, copy-paste)

```bash
# 1. Estatica + acentuacao
python -m ruff check nyx/
python3 ~/.config/zsh/scripts/validar-acentuacao.py --paths nyx/agent/tui/app.py

# 2. PROOF VISUAL via Textual Pilot (PRIMARIA, GPU-free -- não precisa do modelo):
#    Montar a app, chamar os 2 callbacks com dados sujos, ler o texto dos ChatMessage("tool").
venv/bin/python - <<'PY'
import asyncio
from nyx.agent.tui.app import NyxApp  # ajuste o nome real da App se diferir (grep "class .*App")
async def main():
    app = NyxApp()  # se exigir args, use os defaults/mocks do harness Pilot ja usado na 389/390
    async with app.run_test() as pilot:
        app._on_agent_tool("write_file", {"file_path": "~/x.py", "content": "A"*5000})
        app._on_agent_tool_result("read_file", "linha 1\nlinha 2 [3 linhas lidas. Analise e execute a proxima ação.] Se a tarefa esta completa, chame done().")
        await pilot.pause()
        from nyx.agent.tui.widgets.chat_message import ChatMessage
        tools = [w for w in app.query(ChatMessage) if getattr(w, "_role", getattr(w, "role", "")) == "tool"]
        for w in tools:
            print(repr(getattr(w, "_content", getattr(w, "content", ""))))
asyncio.run(main())
PY
# ESPERADO: 1o ChatMessage = "write_file: file_path: ~/x.py" (SEM os 5000 chars de content);
#           2o = "-> read_file: linha 1\nlinha 2" (SEM '[... lidas]' nem 'chame done()').

# 3. Gauntlet
./run.sh --gauntlet --only rapido
```

---

## Critério binário de aceite (IA executora)

- [ ] `_on_agent_tool` exibe nome + arg-chave (sem dict cru / sem content inteiro)
- [ ] `_on_agent_tool_result` remove hints de controle + system-reminder + trunca; nome da tool visível
- [ ] Proof Textual Pilot colado: 1o ChatMessage sem os 5000 chars; 2o sem '[...lidas]'/'chame done()'
- [ ] `ruff` limpo, acentuação rc=0, `FAIL_AFTER <= FAIL_BEFORE`
- [ ] Gauntlet `rapido` 100%
- [ ] `SPRINT_ORDER_MASTER.md` marca 406 CONCLUIDA; spec movida para `concluidos/`
- [ ] NÃO commitar; NÃO tocar Checkpoint.md; NÃO tocar o loop

---

## Guardrails anti-engodo (obrigatórios)

NÃO marcar concluída se:
- Escondeu o NOME da tool ou o ato de executar (ADR-026 -- ação não pode sumir).
- Duplicou os regex de strip sem comentário de fonte (DRY: reusar `_core.py` se não houver ciclo).
- Proof Pilot não colado ou ainda mostra o content cru.

Se algo falhar: `[SPRINT 406] BLOQUEADA: <motivo 1 linha>`.

---

## Proof-of-work obrigatório (4 passos)

```bash
bash scripts/sprint_invariants.sh > /tmp/inv_before.txt 2>&1
FAIL_BEFORE=$(grep -c "^\[FAIL\]" /tmp/inv_before.txt)
# implementar
bash scripts/sprint_invariants.sh > /tmp/inv_after.txt 2>&1
FAIL_AFTER=$(grep -c "^\[FAIL\]" /tmp/inv_after.txt)
diff /tmp/inv_before.txt /tmp/inv_after.txt
```
Colar: inv_before/inv_after (tail), diff, proof Pilot, `git --no-pager diff --stat`.

---

## Gambiarras específicas desta sprint

- **Esconder a ação:** o nome da tool DEVE aparecer (ADR-026). Saneie o lixo, não a evidência.
- **Duplicar regex:** preferir importar de `_core.py` (fonte única). Só duplicar se houver ciclo de import, com comentário.
- **Truncar cedo demais:** 600 chars dá pra ver o resultado real; ajustar se a UX pedir, mas não esconder tudo.

---

## Validação humana (checklist do usuário)

```bash
cd /home/andrefarias/Desenvolvimento/Nyx-Code
git --no-pager show --stat HEAD
NYX_TUI_TEXTUAL=1 ./run.sh   # peca "leia ~/.zshrc" e observe a linha de tool
# ESPERADO: "read_file: file_path: ~/.zshrc" + "-> read_file: <conteudo limpo>" (sem 'chame done()').
ls dev-journey/06-sprints/concluidos/SPRINT_TUI_INTERNALS_LEAK_01.md  # existe
```

---

## Riscos

| Risco | Mitigação |
|-------|-----------|
| Ciclo de import (app.py -> _core -> _iteration -> ...) | Nota no Edit: se houver ciclo, definir os 2 regex localmente em app.py com comentário de fonte. |
| `_format_perm_detail` não cobre um arg-chave de alguma tool | Cai no fallback `name` (só o nome) -- ainda limpo, sem dict cru. |
| Frases do system prompt ecoadas no CONTENT do assistente (parte de V09) | Fora do escopo desta sprint (é conteúdo do modelo, não evento tool_use); a render-layer aqui trata os eventos tool. Registrar se reaparecer. |

---

*"Mostrar que age é honestidade; despejar o formato interno é ruído." -- princípio de render (ADR-024)*
