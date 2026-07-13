## 0. SPEC (machine-readable)

```yaml
sprint:
  id: TUI-INPUT-NO-SILENT-CANCEL-01
  numero: 427
  title: "Submeter durante um turno em curso não pode CANCELAR o turno em silencio -- bloquear com feedback (exclusive=True do Textual mata, não enfileira)"
  onda: 48
  prioridade: ALTA
  tipo: Bugfix
  dependencias: []
  desbloqueia: []
  absorve: []

  touches:
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/agent/tui/app.py
      reason: "guard no inicio do ramo de turno de _on_input_submit: se ja ha turno em curso (toolbar.inflight True), não despachar novo worker -- montar ChatMessage system com feedback, preservar o texto digitado e retornar ANTES de qualquer mutacao; corrigir o comentario enganoso 'fila implicita' (exclusive=True do Textual CANCELA o grupo, não enfileira)"
      linhas_alvo: "418 (topo do ramo de turno, apos o return do slash na ~417), 457-464 (comentario duplicado 'fila implicita' + run_worker exclusive=True)"
  creates: []
  removes: []

  forbidden:
    - "Adicionar emoji"
    - "Usar 'print()' fora de cli.py/output.py"
    - "Mencao a IA proprietaria"
    - "Tocar _process_turn (742+): o try/except/finally e o crash-guard (ADR-033) ficam intactos"
    - "Tocar o ramo de slash command (_dispatch_slash) nem a semantica do /cancel (__cancel_inflight__, 613-625)"
    - "Remover exclusive=True do run_worker -- ele permanece como defesa-em-profundidade; o guard e ADITIVO, roda ANTES"
    - "Tocar input.py alem do estritamente necessario para preservar o texto (se o executor optar por preservar via app.py, input.py fica ZERO diff)"
    - "Alterar o happy-path: submeter SEM turno em curso segue byte-identico (monta user, inflight=True, dispara worker)"

  tests:
    - cmd: "/home/andrefarias/.local/bin/ruff check nyx/agent/tui/app.py"
      deve_passar: true
    - cmd: "bash scripts/sprint_invariants.sh"
      deve_passar: true
    - cmd: "python3 ~/.config/zsh/scripts/validar-acentuacao.py --paths nyx/agent/tui/app.py"
      deve_passar: true

  acceptance_criteria:
    - "AC1 (no-silent-cancel): submeter uma mensagem de chat enquanto um turno esta em curso (toolbar.inflight True) não cancela o turno em andamento -- o worker de _process_turn segue rodando ate concluir; o segundo submit e BLOQUEADO antes de chamar run_worker"
    - "AC2 (feedback honesto): o submit bloqueado monta um ChatMessage('system') claro para o usuário leigo, ex.: 'Ha um turno em andamento. Aguarde a resposta ou use /cancel para interromper.' -- nunca um no-op silencioso"
    - "AC3 (texto preservado): o texto digitado no submit bloqueado não e perdido -- reaparece no InputWidget (o clear() de input.py:182 roda DEPOIS do callback; reinserir via call_after_refresh) para o leigo poder reenviar ao fim do turno"
    - "AC4 (indicador intacto): o guard retorna ANTES de setar toolbar.inflight/_current_assistant/_start_thinking_indicator, entao o indicador 'pensando... (Ns)' do turno em curso não e apagado nem duplicado (o bug bonus do finally que setava inflight=False some junto, pois nenhum worker novo/cancelamento ocorre)"
    - "AC5 (comentario honesto): os comentarios duplicados 'exclusive=True mantem 1 turno por vez (fila implicita)' (457 e 461) sao corrigidos -- o Textual 8.2.7 CANCELA o grupo em exclusive=True (não enfileira); o texto novo descreve a realidade e cita o guard novo + o /cancel como via sancionada de interrupcao"
    - "AC6 (nada mais muda): happy-path intacto (submit sem turno em curso identico); ramo slash e /cancel intactos; _process_turn intacto; ruff limpo, acentuacao rc=0, invariantes FAIL_AFTER <= FAIL_BEFORE, smoke boot ok (DEFERIDO GPU)"
```

---

# Sprint TUI-INPUT-NO-SILENT-CANCEL-01 — submeter durante um turno não pode matar o turno em silencio

**Status:** PENDENTE
**Data criação:** 2026-07-13
**Modelo obrigatório:** claude-opus-4-7 (executor-sprint autorizado pelo dono nesta onda)

---

## Contexto do projeto (snapshot — não referência)

> **ADRs relevantes (inline):**
> - **ADR-032/033 A INFRA CARREGA O MODELO / ENFORCEMENT, NÃO CONFIANÇA:** a robustez pertence à infra, não ao modelo. A pior máquina (CPU-only) roda um turno de 60s+; o usuário leigo e impaciente vai digitar um follow-up. A infra tem de tratar isso sem destruir trabalho em curso nem deixar o usuário no escuro.
> - ADR-034 (falha honesta / feedback claro), ADR-026 (nada cru vaza na tela), ADR-009, ADR-001.
>
> **Estado (2026-07-13):** `qwen2.5-coder:3b`. TUI Textual (migrada da prompt_toolkit na ONDA-32; widgets em `nyx/agent/tui/`). O turno de chat roda como worker async no loop principal (`TUI-FIX-HTTPX-LOOP-AFFINITY-01`, ONDA-33), disparado por `_on_input_submit`. A interrupção sancionada e `/cancel` (sentinel `__cancel_inflight__`, `app.py:613-625`) ou `Ctrl+C`. Origem do achado: auditoria de prontidão 2026-07-12 (achado ALTA, verificado adversarialmente com evidência file:line).

---

## Problema

**Achado (auditoria 2026-07-12, ALTA):** submeter uma mensagem de chat com um turno em curso CANCELA o turno em andamento em silencio, sem nenhuma mensagem ao usuário.

O dispatch do turno em `nyx/agent/tui/app.py:_on_input_submit` termina em (linhas 462-464):

```python
self.run_worker(
    self._process_turn(text), exclusive=True, exit_on_error=False
)
```

Os comentários logo acima (linhas 457 e 461, DUPLICADOS) afirmam:

```python
# exclusive=True mantem 1 turno por vez (fila implicita).
```

**A afirmação e falsa.** No Textual 8.2.7 (verificado na instalação, `worker_manager.py`), `exclusive=True` significa **"Cancel all workers in the same group"**: `add_worker` chama `cancel_group(node, group)` ANTES de iniciar o novo worker. **Não existe fila.** O turno em curso e cancelado no meio do `await` (levanta `CancelledError`).

**Impacto (na pior máquina, usuário leigo):** durante um turno de 60s+ o usuário impaciente digita um follow-up ("e aí?") e tecla Enter. O turno em andamento e morto silenciosamente. Três consequências:

1. **Sem feedback:** nenhuma mensagem explica que o turno anterior foi interrompido -- viola ADR-034 (falha honesta) e o princípio de feedback claro ao leigo.
2. **Tool órfã:** uma tool em execução via `asyncio.to_thread` dentro do AgentLoop não recebe o `CancelledError` (thread não e cancelável) e segue rodando órfã -- escrita parcial possível sem registro na sessão.
3. **Indicador inconsistente:** o `finally` do worker cancelado (`_process_turn`, `app.py:790-794`) roda DEPOIS do submit novo e seta `toolbar.inflight = False` enquanto o turno 2 ainda executa -- apaga o indicador "executando/pensando" no meio de um turno vivo.

---

## Causa-raiz (verificada no código real, com divergências do briefing anotadas)

`nyx/agent/tui/app.py`, método `_on_input_submit` (linha 371). O ramo de turno de chat (não-slash) vai da linha ~418 (`self._last_input = text`, logo após o `return` do ramo slash na ~417) até o `run_worker` na 462-464. Nesse trajeto o método:

- 426-433: alimenta o histórico navegável e o `_history_service`;
- 434-438: monta o `ChatMessage("user", text)` e ancora o scroll;
- 439-440: `if self._agent is None: return` (sem agent, nada de turno);
- 446-447: `toolbar.inflight = True`;
- 448-449: `self._start_thinking_indicator()`;
- 462-464: `self.run_worker(self._process_turn(text), exclusive=True, exit_on_error=False)`.

**Não ha nenhuma checagem de "ja existe turno em curso" antes do `run_worker`.** O estado de turno-em-curso ja e observável: `toolbar.inflight` (reactive em `widgets/toolbar.py:80`) e setado `True` na 447 e resetado `False` só no `finally` de `_process_turn` (794). Logo, o guard e barato: consultar `self.query_one("#toolbar", Toolbar).inflight`.

**Divergências do briefing (linhas deslizaram / detalhe a mais):**
- O briefing cita o `run_worker` na **linha 462**; no código real ele ocupa **462-464** (chamada multi-linha). Sem impacto no fix.
- O comentário enganoso "fila implicita" aparece **DUPLICADO** (linhas 457 E 461, texto identico), não só uma vez. Ambos devem ser corrigidos.
- Confirmado o bug bonus do `finally`: `_process_turn` reseta `toolbar.inflight = False` na linha 794 dentro do `finally`, exatamente como o briefing descreve.

**Decisão de projeto (BLOQUEAR, não cancelar-e-avisar).** O briefing oferece duas saídas: (A) bloquear o submit com feedback, ou (B) cancelar o turno mas montar um aviso. **Esta sprint adota (A) bloquear.** Racional: (A) e estritamente superior para o leigo na pior máquina -- alem de eliminar o cancelamento-silencioso (consequência 1), (A) tambem elimina a **tool órfã** (consequência 2, pois nenhum cancelamento ocorre) e o **indicador apagado** (consequência 3, pois nenhum worker novo dispara nem o `finally` do turno velho roda cedo). O usuário mantem seu texto e reenvia quando o turno terminar. A via de interrupção deliberada continua sendo `/cancel` / `Ctrl+C`, ja existentes e explicitas. Uma FILA real (guardar o pending e despachar no `finally`) fica FORA de escopo (ver seção própria) -- e mais superfície e o dono não pediu semântica de fila.

---

## Solução proposta

Duas correções cirúrgicas, ambas em `nyx/agent/tui/app.py`, dentro/junto de `_on_input_submit`, sem tocar `_process_turn`, o ramo slash ou o `/cancel`:

1. **Guard no topo do ramo de turno** (logo após o `return` do ramo slash, antes de `self._last_input = text` na ~418): se `toolbar.inflight` for `True`, montar um `ChatMessage("system")` com feedback honesto, **preservar o texto digitado** (reinserir no InputWidget via `call_after_refresh`, porque o `self.clear()` de `input.py:182` roda DEPOIS do callback) e `return` -- antes de tocar histórico, montar user, setar `inflight` ou disparar worker.
2. **Corrigir o comentário duplicado** (457 e 461): trocar "mantem 1 turno por vez (fila implicita)" pela realidade -- `exclusive=True` CANCELA o grupo no Textual (não enfileira); o guard novo garante 1 turno por vez ANTES de chegar aqui; a interrupção deliberada e via `/cancel`.

O `exclusive=True` PERMANECE no `run_worker` como defesa-em-profundidade (se por corrida algum worker escapar do guard, o Textual ainda evita 2 turnos concorrentes) -- mas na prática o guard impede que se chegue nele com um turno vivo.

---

## Arquivos alvo (paths absolutos)

### `/home/andrefarias/Desenvolvimento/Nyx-Code/nyx/agent/tui/app.py`

#### Edit 1 — guard "turno em curso" no topo do ramo de turno

# Localização: em `_on_input_submit`, logo APOS o bloco slash que retorna (a linha
# `self._last_input = text`, ~418). O guard precede QUALQUER mutacao do ramo de turno.
# ATENÇÃO: reconferir a linha via rg antes de editar (pode ter deslizado).
**Antes (trecho, ~416-418):**
```python
            self._dispatch_slash(text)
            return
        self._last_input = text
```
**Depois:**
```python
            self._dispatch_slash(text)
            return
        # TUI-INPUT-NO-SILENT-CANCEL-01: se ja ha um turno em curso, não despachar
        # um novo worker. O run_worker(exclusive=True) do Textual CANCELA o turno
        # em andamento (não enfileira -- ver worker_manager.py 8.2.7), matando-o em
        # silencio no meio do await, deixando tool órfã e apagando o indicador. Na
        # pior máquina (turno de 60s+) o leigo impaciente teclava Enter e perdia a
        # resposta sem aviso. Bloqueamos com feedback honesto (ADR-034) e
        # preservamos o texto digitado; /cancel segue sendo a via de interrupcao.
        toolbar = self.query_one("#toolbar", Toolbar)
        if toolbar.inflight:
            chat = self.query_one("#chat", VerticalScroll)
            chat.mount(
                ChatMessage(
                    "system",
                    "Ha um turno em andamento. Aguarde a resposta ou use "
                    "/cancel para interromper.",
                )
            )
            chat.scroll_end(animate=False)
            # O clear() do InputWidget (input.py:182) roda DEPOIS deste callback;
            # reinserir o texto apos o refresh para o leigo poder reenviar.
            self.call_after_refresh(self._restore_blocked_input, text)
            return
        self._last_input = text
```

# Helper para reinserir o texto bloqueado (metodo novo na classe NyxTUI). O executor
# deve conferir a API real do InputWidget (base TextArea 8.2.7): usar o setter/loader
# publico disponivel (`load_text` ou `.text = ...`) + focar o input.
```python
    def _restore_blocked_input(self, text: str) -> None:
        """TUI-INPUT-NO-SILENT-CANCEL-01: devolve ao InputWidget o texto de um
        submit bloqueado por turno em curso (o clear() do widget roda depois do
        callback de submit), para o usuário não perder o que digitou."""
        widget = self.query_one("#input", InputWidget)
        widget.load_text(text)
        widget.focus()
```

#### Edit 2 — corrigir o comentário duplicado enganoso (457 e 461)

# Localização: as duas linhas identicas de comentario logo antes do run_worker.
**Antes (457 e 461, duplicado):**
```python
        # exclusive=True mantem 1 turno por vez (fila implicita).
```
**Depois (uma unica linha honesta; remover a duplicata):**
```python
        # exclusive=True e defesa-em-profundidade: no Textual 8.2.7 ele CANCELA
        # os workers do grupo (não enfileira). Quem garante 1 turno por vez e o
        # guard de toolbar.inflight no topo deste metodo (TUI-INPUT-NO-SILENT-
        # CANCEL-01); a interrupcao deliberada de um turno e via /cancel.
```

> Imports: `Toolbar`, `ChatMessage`, `VerticalScroll` e `InputWidget` ja sao usados/importados em `app.py` (aparecem em `query_one`/`mount`/`compose`). Reconferir via `rg` que nenhum import novo e necessario; se `InputWidget` não estiver importado no escopo, adicionar o import ja existente na base do modulo.

---

## Diff esperado (resumo)

```
~ 1 arquivo modificado (nyx/agent/tui/app.py)
+ ~25 linhas líquidas (guard + helper + comentario). Sem meta numérica de tamanho -- fix aditivo.
```

Sem aritmética de extração: esta sprint não tem meta `arquivo < NNNL`. O único número relevante e o net-add (~25L) num único arquivo.

---

## Comandos de verificação (literais, copy-paste)

```bash
cd /home/andrefarias/Desenvolvimento/Nyx-Code

# 1. Estatica + acentuacao
/home/andrefarias/.local/bin/ruff check nyx/agent/tui/app.py
python3 ~/.config/zsh/scripts/validar-acentuacao.py --paths nyx/agent/tui/app.py

# 2. Confirmar as ancoras (linhas podem ter deslizado -- reconferir ANTES de editar):
rg -n "fila implicita|exclusive=True|toolbar.inflight = True|run_worker\(|self._last_input = text|_restore_blocked_input" nyx/agent/tui/app.py

# 3. PROOF RUNTIME-REAL headless SEM GPU (Textual Pilot; agent fake que trava o
#    turno num asyncio.Event que nunca resolve, simulando um turno de 60s+).
#    Submete o 1o texto (dispara o worker), depois submete um 2o texto e assere:
#      (a) o worker do turno 1 SEGUE rodando (não foi cancelado);
#      (b) apareceu um ChatMessage('system') com o feedback de bloqueio;
#      (c) toolbar.inflight continua True (indicador do turno 1 intacto).
./venv/bin/python - <<'PY'
import asyncio
from nyx.agent.tui.app import NyxTUI

class FakeAgent:
    def __init__(self):
        self.gate = asyncio.Event()  # nunca setado -> turno "trava" em curso
        self.runs = 0
    async def run(self, text):
        self.runs += 1
        await self.gate.wait()   # bloqueia como um turno de 60s+
        return None

async def main():
    agent = FakeAgent()
    app = NyxTUI(agent=agent)
    async with app.run_test() as pilot:
        app._on_input_submit("primeiro turno longo")
        await pilot.pause()
        assert agent.runs == 1, agent.runs
        # segundo submit com turno em curso:
        app._on_input_submit("e ai?")
        await pilot.pause()
        # (a) turno 1 não foi recomecado nem cancelado -> run() so foi chamado 1x
        assert agent.runs == 1, f"run() chamado {agent.runs}x (esperado 1 -- sem cancelar/reiniciar)"
        # (b) feedback de bloqueio presente
        from nyx.agent.tui.widgets.chat_message import ChatMessage
        systems = [w for w in app.query(ChatMessage) if getattr(w, "role", "") == "system"]
        assert any("turno em andamento" in (getattr(w, "content", "") or "").lower() for w in systems), \
            [getattr(w, "content", "") for w in systems]
        # (c) indicador do turno 1 intacto
        from nyx.agent.tui.widgets.toolbar import Toolbar
        assert app.query_one("#toolbar", Toolbar).inflight is True
        agent.gate.set()  # libera para o app fechar limpo
        await pilot.pause()
    print("OK: submit bloqueado -- turno 1 vivo, feedback montado, inflight intacto")

asyncio.run(main())
PY

# 4. Confirmar que o comentario enganoso sumiu (sem "fila implicita"):
rg -n "fila implicita" nyx/agent/tui/app.py && echo "FALHA: comentario enganoso ainda presente" || echo "OK: comentario 'fila implicita' removido"

# 5. Invariantes
bash scripts/sprint_invariants.sh
```

> Nota GPU: o passo 3 roda SEM Ollama/GPU (agent fake, Pilot headless). O executor deve
> ajustar os acessos de atributo do ChatMessage (`role`/`content`) e do InputWidget
> (`load_text` vs `.text`) à API real confirmada por `rg` -- os nomes acima são a
> hipótese verificada na exploração e podem exigir ajuste de 1 linha.

---

## Critério binário de aceite (IA executora)

- [ ] Guard `if toolbar.inflight:` no TOPO do ramo de turno, ANTES de histórico/mount-user/`inflight=True`/worker
- [ ] Submit bloqueado monta `ChatMessage("system")` com feedback honesto citando `/cancel`
- [ ] Texto digitado preservado (reinserido no InputWidget apos o clear via `call_after_refresh`)
- [ ] Turno em curso não e cancelado (proof passo 3: `run()` chamado 1x, `inflight` segue True)
- [ ] Comentário duplicado "fila implicita" (457 e 461) corrigido para descrever o cancelamento real do Textual + o guard + o `/cancel`
- [ ] `_process_turn`, ramo slash e `/cancel` (`__cancel_inflight__`) intactos; `exclusive=True` mantido como defesa
- [ ] Happy-path intacto (submit SEM turno em curso identico ao anterior)
- [ ] Proof runtime-real headless colado (passo 3), `ruff` limpo, acentuação rc=0, `FAIL_AFTER <= FAIL_BEFORE`
- [ ] Smoke boot ok e gauntlet `--only rapido` (DEFERIDO -- executar só com GPU exclusiva)
- [ ] `SPRINT_ORDER_MASTER.md` marca 427 CONCLUIDA; spec movida para `concluidos/` (pelo orquestrador)
- [ ] NÃO commitar; NÃO tocar Checkpoint.md

---

## Guardrails anti-engodo (obrigatórios)

NÃO marcar concluída se:
- O guard ficou DEPOIS de `toolbar.inflight = True` ou depois do `run_worker` (a ordem e o núcleo: o guard tem de retornar ANTES de qualquer mutacao do ramo de turno).
- O submit bloqueado ficou como no-op silencioso (sem `ChatMessage("system")` de feedback) -- viola AC2/ADR-034.
- O texto digitado se perde no submit bloqueado (AC3) -- reconferir que o `call_after_refresh` reinsere apos o `clear()` do widget.
- O turno em curso passou a ser CANCELADO (a alternativa B do briefing) em vez de o novo submit ser BLOQUEADO -- esta sprint adota BLOQUEAR (proof passo 3: `run()` 1x).
- Removeu `exclusive=True` do `run_worker` (ele fica como defesa-em-profundidade).
- Tocou `_process_turn`, o ramo slash ou o `/cancel`.
- Manteve qualquer ocorrencia de "fila implicita" no comentario.
- Proof runtime-real headless não colado.

Se algo falhar: `[SPRINT 427] BLOQUEADA: <motivo 1 linha>`.

---

## Proof-of-work esperado

```bash
cd /home/andrefarias/Desenvolvimento/Nyx-Code
bash scripts/sprint_invariants.sh > /tmp/inv_before.txt 2>&1
FAIL_BEFORE=$(grep -c "^\[FAIL\]" /tmp/inv_before.txt)
# implementar
bash scripts/sprint_invariants.sh > /tmp/inv_after.txt 2>&1
FAIL_AFTER=$(grep -c "^\[FAIL\]" /tmp/inv_after.txt)
diff /tmp/inv_before.txt /tmp/inv_after.txt
```

Baseline esperado: `FAIL_BEFORE = 0`, `FAIL_AFTER <= 0`. Colar como proof: `inv_before`/`inv_after` (tail), o `diff`, o output do proof runtime-real headless (passo 3), o `rg` dos passos 2 e 4, e `git --no-pager diff --stat`.

Runtime-real (contratos do VALIDATOR_BRIEF.md):
- **Estatica/acentuacao (roda agora, sem GPU):** `ruff check nyx/agent/tui/app.py`; `validar-acentuacao.py --paths nyx/agent/tui/app.py`.
- **Pilot headless (roda agora, sem GPU):** proof passo 3 (agent fake + `run_test()`).
- **Smoke boot (DEFERIDO -- GPU exclusiva):** `./run.sh --smoke` deve imprimir `boot ok`. Executar só quando `pgrep -af "Luna.*driver|valida_sprint"` estiver vazio (protocolo anti-contenção do BRIEF), como as specs 403/407.
- **Gauntlet (DEFERIDO -- GPU exclusiva):** `./run.sh --gauntlet --only rapido` deve dar 100%. Mesmo gate de GPU.

Validação visual (opcional, se o dono pedir): `NYX_TUI_TEXTUAL=1 ./run.sh` em TTY real -- digitar um prompt, e ANTES da resposta chegar, digitar outro e teclar Enter; confirmar que a resposta em curso NÃO some e que aparece a mensagem "Ha um turno em andamento...". Pipeline `validação-visual` só se tocar render layer alem do fluxo (não e o caso).

---

## Gambiarras específicas desta sprint

- **Ordem clear-vs-callback:** o `InputWidget._on_key` chama `self._on_submit(text)` e SÓ ENTÃO `self.clear()` (`input.py:180-182`). Logo, reinserir o texto direto no guard seria apagado pelo `clear()` seguinte. Usar `self.call_after_refresh(self._restore_blocked_input, text)` agenda a reinsercao para depois do ciclo -- o padrão `call_after_refresh` ja e usado no `app.py` (linha 347, `_focus_input`).
- **`toolbar.inflight` como fonte de verdade do estado de turno:** e um `reactive[bool]` (`widgets/toolbar.py:80`), setado `True` na 447 e resetado no `finally` de `_process_turn` (794). Consultar `self.query_one("#toolbar", Toolbar).inflight` e barato e não introduz estado novo na app.
- **API do InputWidget (base TextArea 8.2.7):** o setter publico de texto pode ser `load_text(text)` ou `.text = text`; o executor confirma via `rg` em `input.py`/base. Se `load_text` mover o cursor para o inicio, e aceitavel (o leigo so vai reenviar).
- **`exclusive=True` fica:** não remover -- e barato e cobre a corrida teorica de dois submits no mesmo tick antes de o `inflight` refletir.

---

## Riscos e não-objetivos / Fora de escopo (anti-débito)

| Risco / não-objetivo | Decisão |
|-------|-----------|
| FILA real de turnos (guardar o pending e despacha-lo no `finally` de `_process_turn`, processando follow-ups em ordem FIFO) | **FORA DE ESCOPO.** E mais superfície (estado de fila, cap, descarte, ordem) e o dono não pediu semântica de fila. Esta sprint BLOQUEIA com feedback (mais simples e seguro para o leigo). Se o dono quiser fila, registrar sprint própria `TUI-INPUT-TURN-QUEUE-01` (anti-débito: `feedback_nenhum_debito`), não absorver aqui. |
| Tool órfã de um turno JA cancelado por `/cancel` ou `Ctrl+C` (a `asyncio.to_thread` não recebe `CancelledError`) | **FORA DE ESCOPO desta sprint.** O guard elimina o cancelamento por submit acidental (o vetor deste achado). O cancelamento DELIBERADO via `/cancel` ainda deixa a thread rodar ate o fim -- isso e um flanco separado; se relevante, registrar `TUI-CANCEL-THREAD-COOPERATIVE-01`. |
| Alterar a mensagem/idioma do `/cancel` ou do crash-guard de `_process_turn` | Fora de escopo -- intocados. |
| Bloquear tambem submits de SLASH command durante turno em curso | **Não.** Slash commands (ex.: `/cancel`, `/status`) devem funcionar DURANTE um turno -- o guard fica só no ramo de turno de chat, apos o `return` do ramo slash. |

---

## Referências

- BRIEF: `/home/andrefarias/Desenvolvimento/Nyx-Code/VALIDATOR_BRIEF.md`
- Briefing da auditoria: achado ALTA 2026-07-12 (`nyx/agent/tui/app.py:457-464`, exclusive=True cancela)
- Evidência Textual: `worker_manager.py` 8.2.7 (`add_worker` -> `cancel_group`); `exclusive: Cancel all workers in the same group.`
- Código: `nyx/agent/tui/app.py` (`_on_input_submit` 371-464, `_process_turn` 742-801, `/cancel` 613-625), `nyx/agent/tui/widgets/input.py:176-183` (submit-then-clear), `nyx/agent/tui/widgets/toolbar.py:80` (`inflight` reactive)
- Precedente de estrutura: `dev-journey/06-sprints/producao/SPRINT_EXEC_CONTRACT_PROXY_STATUS_BEFORE_JSON_01.md` (413)

---

*"Um turno de 60s que morre em silencio porque o usuário teclou Enter e a pior traicao da infra: ela tinha o estado (`inflight`) e escolheu não olhar. Bloquear com uma frase honesta custa dez linhas e devolve o controle ao leigo." -- princípio de execução (ADR-034, honestidade na falha)*
