## 0. SPEC (machine-readable)

```yaml
sprint:
  id: TUI-CANCEL-BINDING-REAL-01
  numero: 428
  title: "TUI: Ctrl+C cancela de verdade -- honra a promessa anunciada no momento mais lento"
  onda: 48
  prioridade: ALTA
  tipo: Bugfix
  dependencias: []
  desbloqueia: []
  absorve: []

  touches:
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/agent/tui/app.py
      reason: "adicionar Binding ctrl+c -> cancel_turn (priority=True) sobrepondo o help_quit default do Textual; extrair a logica do sentinel __cancel_inflight__ (613-624) para um helper reusavel; adicionar action_cancel_turn que chama o helper"
      linhas_alvo: "134-163 (bloco BINDINGS), 613-624 (branch __cancel_inflight__), ~960 (bloco de actions, apos action_quit_if_empty)"
  creates: []
  removes: []

  forbidden:
    - "Adicionar emoji"
    - "Usar 'print()' fora de cli.py/output.py"
    - "Mencao a IA proprietaria"
    - "Tocar a logica de execução do turno (run_worker / _on_input_submit / AgentLoop)"
    - "Remover ou reordenar os Bindings existentes -- o ctrl+c e ADITIVO"
    - "Alterar o texto dos handlers de sentinel que não sejam o __cancel_inflight__"
    - "Trocar o mecanismo de cancelamento (segue workers.cancel_all, identico ao /cancel)"

  tests:
    - cmd: "/home/andrefarias/.local/bin/ruff check nyx/agent/tui/app.py"
      deve_passar: true
    - cmd: "bash scripts/sprint_invariants.sh"
      deve_passar: true
    - cmd: "python3 ~/.config/zsh/scripts/validar-acentuacao.py --paths nyx/agent/tui/app.py"
      deve_passar: true

  acceptance_criteria:
    - "BINDINGS do NyxTUI passa a conter Binding('ctrl+c', 'cancel_turn', priority=True), que sobrepoe o default do Textual 8.2.7 (help_quit, toast em ingles)"
    - "action_cancel_turn cancela os workers ativos (workers.cancel_all quando ha turno) e monta ChatMessage de confirmacao em PT-BR; sem turno em curso monta a mesma mensagem amigavel do /cancel"
    - "A logica de cancelamento vive num único helper reusado pelo branch __cancel_inflight__ (613-624) e por action_cancel_turn -- zero duplicacao/drift entre /cancel e Ctrl+C"
    - "O toast em ingles 'Press ctrl+q to quit the app / Do you want to quit?' NUNCA aparece ao apertar Ctrl+C (o help_quit deixa de ser acionado) -- ADR-006 PT-BR honrado"
    - "A promessa da toolbar 'executando (Ctrl+C cancela)' (toolbar.py:199) e da mensagem do /cancel (app.py:619-622) passa a ser verdadeira -- sem alterar o texto delas"
    - "Proof runtime-real GPU-free (Textual Pilot headless): apertar ctrl+c dispara cancel_turn e monta o ChatMessage; ZERO notificacao de help_quit"
    - "ruff limpo, acentuacao rc=0, invariantes FAIL_AFTER <= FAIL_BEFORE, smoke boot ok"
```

---

# Sprint TUI-CANCEL-BINDING-REAL-01 — Ctrl+C cancela de verdade na TUI

**Status:** PENDENTE
**Data criação:** 2026-07-13
**Modelo obrigatório:** claude-opus-4-7 (executor-sprint autorizado pelo dono nesta onda)

---

## Contexto do projeto (snapshot — não referência)

> **ADRs relevantes (inline):**
> - **ADR-032/033/034 — A INFRA CARREGA O MODELO / ENFORCEMENT, NÃO CONFIANÇA:** o Nyx-Code faz o pior LLM local (qwen 3b) na pior máquina parecer um agente profissional offline. A robustez pertence à infra e à UX, não ao modelo. Um mecanismo de escape anunciado que não funciona é uma falha de infra.
> - **ADR-006 — PT-BR:** toda mensagem user-facing em português; um toast em inglês do framework fere o contrato.
> - ADR-009, ADR-001.
>
> **Estado (2026-07-13):** `qwen2.5-coder:3b`. ONDA-48. TUI migrada para Textual 8.2.7 (`nyx/agent/tui/app.py`, classe `NyxTUI(App)` na linha 72). O usuário-alvo é leigo e sem hardware bom: um turno em CPU pode levar 60s+, e é exatamente aí que o escape precisa funcionar.

---

## Problema

**Achado (auditoria de prontidão 2026-07-12, verificado adversarialmente com evidência file:line):** a TUI anuncia "Ctrl+C cancela" no exato ponto de maior fricção, mas o atalho não faz nada útil — apenas dispara um toast em inglês do framework sobre sair do app, enquanto o turno continua queimando CPU.

Três evidências do MESMO mecanismo (ausência do binding de cancelamento), todas confirmadas no código real:

1. **Promessa na toolbar** — `nyx/agent/tui/widgets/toolbar.py:197-199` (confirmado):
   ```python
   if self.inflight:
       msg.append("  |  ", style=NYX_MUTED)
       msg.append("executando (Ctrl+C cancela)", style=NYX_ACCENT)
   ```
2. **Promessa na mensagem do /cancel** — `nyx/agent/tui/app.py:619-622` (confirmado):
   ```python
   texto = ("/cancel: nenhum turno em curso. "
            "Use Ctrl+C durante a execução para interromper.")
   ```
3. **O binding não existe** — o bloco `BINDINGS` em `nyx/agent/tui/app.py:134-162` (confirmado, linha exata 134-162) lista `ctrl+q`, `ctrl+d`, `shift+tab`, `ctrl+v`, `ctrl+o`, `ctrl+up`, `ctrl+down`, `ctrl+y`, `pageup`, `pagedown` — e **nenhum `ctrl+c`**. Sem binding próprio, vale o default do Textual.

**Impacto:** o único mecanismo de escape anunciado durante os momentos mais lentos (turno de 60s+ em CPU) não funciona. O usuário leigo aperta Ctrl+C por reflexo, recebe um toast em INGLÊS sobre sair do app (viola ADR-006) e o turno segue queimando CPU. O caminho real (`/cancel`) só é revelado na mensagem exibida quando NÃO há turno em curso — exatamente quando não serve. Instrução falsa no ponto de maior fricção da pior máquina.

---

## Causa-raiz (verificada no código real)

Investigação confirmou o briefing com precisão; nenhuma linha deslizou de forma relevante:

- **Default do Textual 8.2.7** (verificado na instalação, `/home/andrefarias/.pyenv/versions/3.12.1/lib/python3.12/site-packages/textual/app.py:463`):
  ```python
  Binding("ctrl+c", "help_quit", show=False, system=True),
  ```
  e `action_help_quit` (mesmo arquivo, linha ~3990) apenas notifica `"Press [b]{key}[/b] to quit the app", title="Do you want to quit?"` — texto em inglês, hardcoded no framework.
- **Agravante confirmado** — `nyx/agent/tui/widgets/input.py:36`: `class InputWidget(TextArea)`. No Textual 8.2.7 o `ctrl+c` é remapeado para "copy" quando um `Input`/`TextArea` está focado (comentário do próprio framework em `action_help_quit`). Como o foco vive no `#input` (sprint 307), sem um binding do App com `priority=True` o `ctrl+c` seria capturado pelo widget focado. Por isso todos os atalhos globais do NyxTUI usam `priority=True` (comentário em `app.py:129-133`) — o `ctrl+c` precisa do mesmo tratamento para o App capturar antes do TextArea.
- **A lógica de cancelamento já existe e é correta** — `nyx/agent/tui/app.py:613-624`, branch do sentinel `__cancel_inflight__` (confirmado):
  ```python
  if result == "__cancel_inflight__":
      ativos = [w for w in self.workers if w.is_running]
      if ativos:
          self.workers.cancel_all()
          texto = "cancel sinalizado (turno em curso interrompido)"
      else:
          texto = ("/cancel: nenhum turno em curso. "
                   "Use Ctrl+C durante a execução para interromper.")
      chat.mount(ChatMessage("system", texto))
      chat.scroll_end(animate=False)
      return
  ```
  O bug é puramente a **ausência do ponto de entrada por teclado**: o `/cancel` (slash) chega até aqui, mas o `Ctrl+C` (tecla) não tem binding e cai no `help_quit`.

**Divergência do briefing:** o briefing sugere "atualizar toolbar.py:199 e a mensagem do /cancel para o atalho real". Investigação mostra que isso é **desnecessário e contraproducente**: uma vez que o `Ctrl+C` passa a cancelar de fato, os dois textos existentes ("executando (Ctrl+C cancela)" e "Use Ctrl+C durante a execução para interromper") tornam-se **verdadeiros como estão**. Alterá-los reintroduziria fricção (o usuário já foi ensinado a apertar Ctrl+C). Portanto a sprint **não toca toolbar.py** e **não altera os textos** — apenas faz o atalho cumprir a promessa. Mudança mais cirúrgica que a do briefing (GUIDE §3).

---

## Solução proposta

Três edits aditivos e cirúrgicos, todos em `nyx/agent/tui/app.py`, sem tocar a lógica de execução do turno nem os textos de UI:

1. **Extrair a lógica de cancelamento** do branch `__cancel_inflight__` (613-624) para um helper `_cancel_inflight_turn(self, chat)` — mesma semântica exata (workers.cancel_all quando há turno; mensagem amigável quando não há). O branch passa a chamar o helper. Zero mudança de comportamento no `/cancel`.
2. **Adicionar o binding** `Binding("ctrl+c", "cancel_turn", priority=True)` ao bloco `BINDINGS` (134-162). O `priority=True` garante que o App captura antes do `InputWidget(TextArea)` focado — mesmo padrão dos demais atalhos globais.
3. **Adicionar `action_cancel_turn`** no bloco de actions (após `action_quit_if_empty`, ~975), que resolve o `#chat` e chama o helper. Como o binding tem binding próprio, o `help_quit` default do Textual deixa de ser acionado — o toast em inglês some.

Com (2), o `Ctrl+C` passa a executar o mesmo cancelamento que o `/cancel` já fazia; com (1), as duas vias compartilham uma única fonte de verdade (sem drift). (3) é o glue.

---

## Arquivos alvo (paths absolutos)

### `/home/andrefarias/Desenvolvimento/Nyx-Code/nyx/agent/tui/app.py`

#### Edit 1 — extrair helper reusável e apontar o branch `__cancel_inflight__` para ele

# Localização: branch do sentinel, linha 613-624
**Antes:**
```python
        if result == "__cancel_inflight__":
            ativos = [w for w in self.workers if w.is_running]
            if ativos:
                self.workers.cancel_all()
                texto = "cancel sinalizado (turno em curso interrompido)"
            else:
                texto = (
                    "/cancel: nenhum turno em curso. "
                    "Use Ctrl+C durante a execução para interromper."
                )
            chat.mount(ChatMessage("system", texto))
            chat.scroll_end(animate=False)
            return
```
**Depois:**
```python
        if result == "__cancel_inflight__":
            self._cancel_inflight_turn(chat)
            return
```

E adicionar o helper (ex.: logo abaixo do método que contém este branch, ou junto ao bloco de helpers de chat):
```python
    def _cancel_inflight_turn(self, chat: VerticalScroll) -> None:
        """Cancela o turno em curso (workers.cancel_all) e confirma na conversa.

        TUI-CANCEL-BINDING-REAL-01: fonte única de verdade do cancelamento,
        reusada pelo sentinel /cancel (__cancel_inflight__) e pelo atalho
        Ctrl+C (action_cancel_turn). Sem turno em curso, exibe a mesma
        mensagem amigável do /cancel. O mecanismo segue idêntico ao anterior:
        na TUI o turno roda como worker (run_worker exclusive=True), então
        cancelamos o(s) worker(s) ativo(s).
        """
        ativos = [w for w in self.workers if w.is_running]
        if ativos:
            self.workers.cancel_all()
            texto = "cancel sinalizado (turno em curso interrompido)"
        else:
            texto = (
                "/cancel: nenhum turno em curso. "
                "Use Ctrl+C durante a execução para interromper."
            )
        chat.mount(ChatMessage("system", texto))
        chat.scroll_end(animate=False)
```

#### Edit 2 — adicionar o binding do Ctrl+C

# Localização: dentro de BINDINGS (134-162), junto aos demais atalhos globais
**Adicionar** (posição sugerida: logo após o `Binding("ctrl+d", ...)`, agrupando os atalhos de controle de sessão):
```python
        # TUI-CANCEL-BINDING-REAL-01: Ctrl+C cancela o turno em curso -- honra a
        # promessa anunciada na toolbar ("executando (Ctrl+C cancela)") e no
        # /cancel. priority=True e OBRIGATORIO: o InputWidget(TextArea) focado
        # remapeia ctrl+c para "copy" no Textual 8.2.7, e o default do framework
        # (help_quit) mostra um toast em INGLES sobre sair do app -- sobrepomos
        # ambos. Ctrl+Y segue como o atalho de copiar bloco de codigo.
        Binding("ctrl+c", "cancel_turn", "Cancelar turno", priority=True),
```

#### Edit 3 — adicionar `action_cancel_turn`

# Localização: bloco de actions, após `action_quit_if_empty` (~975)
```python
    async def action_cancel_turn(self) -> None:
        """Ctrl+C: cancela o turno em curso (paridade com /cancel).

        TUI-CANCEL-BINDING-REAL-01. Sobrepoe o help_quit default do Textual
        (toast em ingles). Reusa _cancel_inflight_turn -- fonte unica com o
        sentinel __cancel_inflight__.
        """
        chat = self.query_one("#chat", VerticalScroll)
        self._cancel_inflight_turn(chat)
```

---

## Diff esperado (resumo)

```
~ 1 arquivo modificado (nyx/agent/tui/app.py)
+ ~30 linhas líquidas (helper + binding + action; branch encolhe ~10L)
```

Sem aritmética de extração: esta sprint não tem meta `arquivo < NNNL`. É um fix aditivo num único arquivo (o `app.py` da TUI segue bem abaixo de qualquer teto ativo); o número relevante é o net-add (~30L).

---

## Comandos de verificação (literais, copy-paste)

```bash
cd /home/andrefarias/Desenvolvimento/Nyx-Code

# 1. Estática + acentuação
/home/andrefarias/.local/bin/ruff check nyx/agent/tui/app.py
python3 ~/.config/zsh/scripts/validar-acentuacao.py --paths nyx/agent/tui/app.py

# 2. Confirmar as âncoras (linhas podem ter deslizado -- reconferir):
rg -n "ctrl\+c|cancel_turn|__cancel_inflight__|_cancel_inflight_turn|workers.cancel_all" nyx/agent/tui/app.py

# 3. PROOF RUNTIME-REAL GPU-FREE (Textual Pilot headless). NÃO sobe Ollama/GPU:
#    o NyxTUI roda headless via run_test(); sem agent nem workers, ctrl+c
#    dispara cancel_turn e monta o ChatMessage "nenhum turno em curso".
#    O ponto provado: a tecla e capturada por cancel_turn (não pelo help_quit).
./venv/bin/python - <<'PY'
import asyncio
from nyx.agent.tui.app import NyxTUI
from nyx.agent.tui.widgets.chat_message import ChatMessage

# 3a. binding presente e mapeado para cancel_turn
acts = {b.key: b.action for b in NyxTUI.BINDINGS}
assert acts.get("ctrl+c") == "cancel_turn", acts
print("OK: BINDINGS['ctrl+c'] ->", acts["ctrl+c"])

# 3b. Pilot headless: apertar ctrl+c aciona cancel_turn (não help_quit)
async def main():
    app = NyxTUI()
    notes = []
    async with app.run_test() as pilot:
        orig = app.notify
        app.notify = lambda *a, **k: notes.append((a, k))  # captura help_quit
        await pilot.press("ctrl+c")
        await pilot.pause()
        msgs = [w for w in app.query(ChatMessage)]
        textos = " ".join(str(getattr(m, "content", "")) + str(m.renderable) if hasattr(m, "renderable") else "" for m in msgs)
    # Nenhum toast de help_quit (ingles) disparado
    assert not any("quit" in str(n).lower() for n in notes), notes
    print("OK: nenhum toast help_quit; cancel_turn acionado; ChatMessages:", len(msgs))

asyncio.run(main())
PY

# 4. Confirmar que o help_quit default do Textual foi de fato sobreposto
#    (o binding do App tem priority e chave própria):
rg -n "Binding\(\"ctrl\+c\", \"cancel_turn\"" nyx/agent/tui/app.py

# 5. Invariantes + smoke boot (gate obrigatório)
bash scripts/sprint_invariants.sh
./run.sh --smoke   # deve imprimir "boot ok" e exit 0 (ver nota GPU)
```

> **Nota GPU:** o passo 3 (Pilot headless) roda SEM Ollama/GPU — a TUI sobe headless e o cancelamento não depende de inferência. O passo 5 `./run.sh --smoke` é o gate universal (check #13); se houver contenção de GPU no momento (Luna/valida_sprint ativos), **marcar o smoke como DEFERIDO para GPU exclusiva** e executá-lo assim que `pgrep -af "Luna.*driver|valida_sprint"` estiver vazio (mesmo protocolo das specs 403/407). O gauntlet **não se aplica** a esta sprint (mudança é de binding de TUI, não coberta pelas suítes de proxy/rápido).

---

## Critério binário de aceite (IA executora)

- [ ] `Binding("ctrl+c", "cancel_turn", priority=True)` presente em `BINDINGS`, sem remover/reordenar os demais
- [ ] `_cancel_inflight_turn` extraído como fonte única; o branch `__cancel_inflight__` (613-624) passa a chamá-lo (comportamento do /cancel byte-idêntico)
- [ ] `action_cancel_turn` adicionado, resolve `#chat` e chama o helper
- [ ] Proof GPU-free colado (passo 3): `BINDINGS['ctrl+c'] == 'cancel_turn'` e nenhum toast `help_quit` ao apertar ctrl+c
- [ ] Textos da toolbar (`toolbar.py:197-199`) e do /cancel (`app.py:619-622`) intactos — a promessa agora é verdadeira sem editá-los
- [ ] `ruff` limpo, acentuação rc=0, `FAIL_AFTER <= FAIL_BEFORE`
- [ ] `./run.sh --smoke` imprime `boot ok` (ou DEFERIDO para GPU exclusiva, registrado)
- [ ] `SPRINT_ORDER_MASTER.md` marca 428 CONCLUIDA; spec movida para `concluidos/`
- [ ] NÃO commitar; NÃO tocar `Checkpoint.md`; NÃO tocar `toolbar.py`; NÃO alterar textos de UI

---

## Guardrails anti-engodo (obrigatórios)

NÃO marcar concluída se:
- O `ctrl+c` ficou sem `priority=True` (o `InputWidget(TextArea)` focado captura antes e o fix não vale nada).
- A lógica foi duplicada (copiada) em vez de extraída para o helper — /cancel e Ctrl+C precisam da mesma fonte de verdade (senão um dia divergem).
- O mecanismo de cancelamento mudou (deve seguir `workers.cancel_all` sobre `self.workers`, idêntico ao branch original).
- Os textos da toolbar ou do /cancel foram alterados (a promessa passa a ser verdadeira sem tocá-los — mexer reintroduz fricção).
- O toast em inglês do `help_quit` ainda aparece ao apertar Ctrl+C (o binding próprio não foi registrado ou não tem prioridade).
- Proof GPU-free não colado, ou `BINDINGS['ctrl+c']` não aponta para `cancel_turn`.

Se algo falhar: `[SPRINT 428] BLOQUEADA: <motivo 1 linha>`.

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
Baseline esperado: `FAIL_BEFORE = 0`, `FAIL_AFTER <= 0`. Colar: inv_before/inv_after (tail), diff, o output do proof GPU-free (passo 3), o `rg` dos passos 2 e 4, `git --no-pager diff --stat` e `./run.sh --smoke` (deve imprimir `boot ok`, ou marcar DEFERIDO com o motivo de contenção de GPU).

---

## Validação humana (checklist do usuário)

```bash
cd /home/andrefarias/Desenvolvimento/Nyx-Code
git --no-pager show --stat HEAD

# Com o stack real: mandar um prompt que gere um turno longo e apertar Ctrl+C
# no meio. A Nyx deve interromper o turno e responder em PT-BR
# ("cancel sinalizado (turno em curso interrompido)") -- SEM toast em inglês
# ("Do you want to quit?"). Sem turno em curso, Ctrl+C mostra a mensagem
# amigável de "nenhum turno em curso". (Executar só com GPU exclusiva.)

ls dev-journey/06-sprints/concluidos/SPRINT_TUI_CANCEL_BINDING_REAL_01.md  # existe
```

---

## Fora de escopo (anti-débito)

| Risco / não-objetivo | Decisão |
|-------|-----------|
| Interromper mid-flight o passo de inferência HTTP em andamento (o `workers.cancel_all` cancela a coroutine, mas o POST ao proxy pode seguir até o timeout no lado do servidor) | **NÃO-OBJETIVO.** O comportamento de cancelamento é o mesmo que o `/cancel` já entrega hoje; melhorar o corte do transporte é uma sprint própria `INFRA-TUI-CANCEL-HTTP-ABORT-01` se o dono quiser (`feedback_nenhum_debito`). |
| Perda do `ctrl+c` como "copiar seleção" dentro do `InputWidget` | Tradeoff aceito e desejado: `ctrl+c` reflexivo = "parar" para usuário de terminal; o copiar de código já vive em `ctrl+y` (TUI-CODE-COPY-BUTTON-01). Registrado como gambiarra abaixo. |
| Traduzir/remover o `help_quit` do Textual globalmente | Desnecessário: com binding próprio para `ctrl+c`, o `help_quit` deixa de ser alcançável por essa tecla. Não há outro caminho anunciado para ele. |
| Atualizar textos da toolbar/`/cancel` | Explicitamente evitado (ver Causa-raiz / divergência do briefing): a promessa passa a ser verdadeira como está. |

---

## Gambiarras específicas desta sprint

- **`priority=True` no `ctrl+c`:** obrigatório porque o `InputWidget(TextArea)` focado (`input.py:36`) remapeia `ctrl+c` para copy no Textual 8.2.7. Sem prioridade, o App nunca veria a tecla. Mesmo padrão dos outros nove atalhos globais (`app.py:129-133`).
- **`ctrl+c` supera o copy do input:** consequência do item acima — copiar seleção via `ctrl+c` dentro do input deixa de existir. Aceito de propósito (o copy de bloco de código é `ctrl+y`); anotado em "Fora de escopo".
- **Helper recebe `chat` por parâmetro:** o branch `__cancel_inflight__` já tem o `chat` resolvido em escopo; passar por parâmetro evita um segundo `query_one` e mantém o helper reusável tanto pelo sentinel quanto pelo `action_cancel_turn` (que resolve o seu próprio `#chat`).

---

## Referências

- BRIEF: `/home/andrefarias/Desenvolvimento/Nyx-Code/VALIDATOR_BRIEF.md`
- Origem: auditoria de prontidão 2026-07-12, relatório durável `dev-journey/07-reports/AUDIT_2026_07_12.md` §3 (briefing efêmero da sessão de auditoria)
- Estrutura de referência: `dev-journey/06-sprints/producao/SPRINT_EXEC_CONTRACT_PROXY_STATUS_BEFORE_JSON_01.md`
- Evidência primária: `nyx/agent/tui/app.py:134-162` (BINDINGS), `app.py:613-624` (__cancel_inflight__), `app.py:619-622` (/cancel), `nyx/agent/tui/widgets/toolbar.py:197-199` (promessa), `nyx/agent/tui/widgets/input.py:36` (InputWidget), Textual 8.2.7 `app.py:463` (default ctrl+c -> help_quit)

---

*"Um botão de pânico que não funciona é pior que nenhum botão: ensina o usuário a confiar no que vai traí-lo no pior momento." -- princípio de UX (ADR-032/033)*
