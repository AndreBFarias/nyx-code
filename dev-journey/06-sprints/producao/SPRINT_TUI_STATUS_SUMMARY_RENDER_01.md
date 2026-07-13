## 0. SPEC (machine-readable)

```yaml
sprint:
  id: TUI-STATUS-SUMMARY-RENDER-01
  numero: 426
  title: "TUI descarta status.summary/state: erro de proxy vira silencio total e turno tool-only nunca mostra a resposta final (quebra G3)"
  onda: 48
  prioridade: ALTA
  tipo: Bugfix
  dependencias: []
  desbloqueia: []
  absorve: []

  touches:
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/agent/tui/app.py
      reason: "no pos-await de _process_turn, deixar de descartar o SessionStatus: (a) state==error monta ChatMessage('system', summary) com a mensagem PT-BR honesta do loop; (b) DONE com summary não-subset do texto ja streamado monta/atualiza o balao do assistant, cobrindo turnos tool-only e o bloco de dados crus do G3"
      linhas_alvo: "764-774 (bloco pos-await do done() summary swap, dentro do try de _process_turn)"
  creates: []
  removes: []

  forbidden:
    - "Adicionar emoji"
    - "Usar 'print()' na TUI (a TUI monta widgets, não imprime em stdout)"
    - "Mencao a IA proprietaria"
    - "Tocar o loop (nyx/agent/loop/*), _core.py, models.py -- a origem do status ja esta correta"
    - "Tocar cli.py (o REPL legado ja renderiza certo; e a referencia, não o alvo)"
    - "Tocar o except TUI-WORKER-CRASH-GUARD-01 (775-789) -- ele cobre exceção, não state==error de retorno normal; sao caminhos distintos"
    - "Alterar o happy-path de texto puro streamado: turno normal (summary subset do streamado) segue sem balao extra, byte-identico"
    - "Remover o swap done() existente (TUI-DONE-SUMMARY-CLEAN-01): a logica nova e ADITIVA e preserva esse caso"

  tests:
    - cmd: "/home/andrefarias/.local/bin/ruff check nyx/agent/tui/app.py"
      deve_passar: true
    - cmd: "python3 ~/.config/zsh/scripts/validar-acentuacao.py --paths nyx/agent/tui/app.py"
      deve_passar: true
    - cmd: "bash scripts/sprint_invariants.sh"
      deve_passar: true
    - cmd: "./run.sh --smoke"
      deve_passar: true

  acceptance_criteria:
    - "AC1 (erro de proxy não vira silencio): quando run() retorna SessionStatus com state==error (proxy caido/timeout/OOM, nenhum token streamado), _process_turn monta ChatMessage('system', status.summary) no #chat -- a mensagem PT-BR honesta e acionavel do loop (ex.: 'Conexão recusada pelo proxy... reinicie o stack com ./run.sh') aparece para o usuário leigo, em vez do silencio absoluto apos o 'pensando...' sumir"
    - "AC2 (turno tool-only mostra a resposta): quando run() retorna DONE com summary não-vazio E não houve balao de assistant (turno so tool_calls + done(summary=...), _current_assistant is None), monta ChatMessage('assistant', summary) -- o summary final e o bloco de dados crus do G3 deixam de sumir"
    - "AC3 (subset guard, sem eco): usa a mesma logica _is_subset de cli.py:456-462 contra o texto ja streamado (_current_assistant.content quando existe); se o summary ja e subset do streamado, não monta/atualiza balao extra -- turno de texto puro normal fica byte-identico"
    - "AC4 (done() cru preservado): o caso TUI-DONE-SUMMARY-CLEAN-01 (balao existe E contem 'done(' cru) continua trocando o content pelo summary limpo -- comportamento preservado"
    - "AC5 (crash guard intacto): o except TUI-WORKER-CRASH-GUARD-01 (775-789) fica byte-identico -- ele cobre exceção levantada, não o retorno normal com state==error; os dois caminhos coexistem"
    - "Proof runtime-real SEM GPU: SessionStatus fabricado (state=ERROR, summary='...') e (state=DONE, summary='...') alimentam a logica de _process_turn extraida/exercida -- assercao de que ERROR gera role 'system' e DONE-tool-only gera role 'assistant'; DEFERIDO para GPU o teste as-user com stack real (Ollama parado de proposito)"
    - "ruff limpo, acentuacao rc=0, invariantes FAIL_AFTER <= FAIL_BEFORE, smoke boot ok"
```

---

# Sprint TUI-STATUS-SUMMARY-RENDER-01 — a TUI para de descartar o SessionStatus: erro honesto e resposta final tool-only voltam a aparecer

**Status:** PENDENTE
**Data criação:** 2026-07-13
**Modelo obrigatorio:** claude-opus-4-7 (executor-sprint autorizado pelo dono nesta onda)

---

## Contexto do projeto (snapshot — não referencia)

> **Missao:** o Nyx-Code faz o pior LLM local (qwen 3b) na pior maquina possivel parecer um agente de codigo profissional offline. Robustez pertence a INFRA, não ao modelo (ADR-032/033/034). O usuario-alvo e leigo, sem hardware bom: para ele, o silencio absoluto apos um crash e indistinguivel de um travamento -- ele não sabe que a cadeia caiu nem como reerguer.
>
> **ADRs relevantes (inline):**
> - **ADR-033 (a cadeia nunca quebra na mao do usuário sem rastro):** todo caminho de falha termina numa mensagem honesta e acionavel no chat, nunca num silencio.
> - **G3 da fase raiz ONDA-48 (apresentacao forte):** os dados crus da tool aparecem abaixo da fala do 3b; o `_core.py` compoe SEMPRE `status.summary = self._compose_presentation_summary(status)` (verificado em `_core.py:346`) -- se a camada de UI joga o summary fora, o contrato G3 morre na última milha.
>
> **Estado (2026-07-13):** `qwen2.5-coder:3b`. ONDA-48 fase raiz: nucleo do contrato CONCLUIDO. Caminho ÚNICO interativo em TTY = `NyxTUI` (`cli.py:538`, `sys.stdin.isatty()`); o REPL legado de `cli.py` so roda em não-TTY (pipe/headless). Ports: Ollama `11435`, proxy `11436`.

---

## Problema

**Achado (auditoria de prontidao 2026-07-12, verificado adversarialmente):** a `NyxTUI` -- caminho único interativo em terminal real -- **descarta** o `SessionStatus` devolvido por `agent.run()`, exceto num único caso estreito. Em `nyx/agent/tui/app.py`, `_process_turn` (linha 742) faz:

```python
status = await self._agent.run(text)                                # 764
...
if status is not None and self._current_assistant is not None:      # 771
    summary = (getattr(status, "summary", "") or "").strip()        # 772
    if summary and "done(" in self._current_assistant.content:      # 773
        self._current_assistant.set_content(summary)                # 774
```

O `summary` so e usado quando **ja existe um balao de assistant** (`_current_assistant is not None`) **E** esse balao contem o artefato cru `done(`. Fora dessa janela, `status.state` e `status.summary` sao ignorados. Dois cenarios reais no caminho único interativo caem no vazio:

1. **Erro de proxy vira silencio total.** Quando o proxy cai/timeout/OOM, o loop devolve uma mensagem PT-BR honesta e ja pronta -- ex. `nyx/agent/loop/_iteration.py:977-982` (`"Conexão recusada pelo proxy de inferencia. Reinicie o stack com ./run.sh ou confira ~/.nyx/logs/proxy.log."`), que vira `SessionStatus(state=ERROR, summary=error_msg)` em `_core.py:446-450`. Como nenhum token foi streamado, `_current_assistant is None`, o `if` da linha 771 e falso e **nada e montado no chat**. O indicador 'pensando...' e removido no `finally` (linha 793) e o usuário leigo fica olhando o silencio absoluto -- sem saber que a cadeia caiu nem como reergue-la. Isso fere **ADR-033**.

2. **Turno tool-only nunca mostra a resposta final.** Quando o qwen3 responde so via `tool_calls` + `done(summary=...)` (fluxo canônico do 3b), nenhum token de texto e streamado, entao `_current_assistant is None` e o `if` da 771 nunca dispara. O `summary` final (que carrega tambem o bloco de dados crus do G3 composto em `_core.py:346`) **nunca aparece** -- o usuário ve as linhas de tool e nenhuma resposta. Isso fere o **G3 da fase raiz ONDA-48**.

O REPL legado de `cli.py` ja resolve os dois casos (`cli.py:463-467` renderiza o summary quando não e subset do streamado; `cli.py:471-477` imprime erro honesto para `state==error`), mas ele so roda em não-TTY. **Nada equivalente existe na TUI**, que e o único caminho que o usuário leigo enxerga.

---

## Causa-raiz (verificada no codigo real)

Investigacao byte-a-byte em 2026-07-13; as linhas do briefing não deslizaram, todas conferem:

- `nyx/agent/tui/app.py:764-774` -- bloco pos-await confirmado exatamente como no briefing; o `if` da 771 e a raiz do descarte.
- `nyx/agent/tui/app.py:775-789` -- `except TUI-WORKER-CRASH-GUARD-01` monta `ChatMessage("system", ...)` **so quando uma exceção e levantada** dentro do `try`. O retorno `SessionStatus(state=ERROR, ...)` do loop **não levanta exceção** -- e um retorno normal -- entao esse handler não cobre o cenario 1. Confirmado: sao caminhos distintos.
- `nyx/agent/tui/app.py:790-806` -- `finally` remove o indicador (793), zera inflight (794) e reseta `_current_assistant = None` (806). O reset e no `finally`, entao a leitura de `_current_assistant` para o fix deve ocorrer ANTES, dentro do `try` (mesmo lugar do bloco 771-774).
- `nyx/agent/loop/_iteration.py:977-982` -- handler `httpx.ConnectError` com a mensagem PT-BR honesta. Confirmado.
- `nyx/agent/loop/_core.py:446-450` e `453-457` -- retornam `SessionStatus(state=SessionState.ERROR, summary=error_msg)`. Confirmado.
- `nyx/agent/loop/_core.py:340-346` -- `status.summary = self._compose_presentation_summary(status)` composto SEMPRE (G3). Confirmado.
- `nyx/cli.py:456-462` -- helper `_is_subset(a, b)` (normaliza whitespace, testa contencao mutua). Referencia da logica anti-eco.
- `nyx/cli.py:463-467` e `471-477` -- render do summary (não-subset) e do erro (`state_label == "error"`) no REPL legado. Referencia do comportamento correto.
- `nyx/agent/models.py:41-47` -- `class SessionState(Enum)` com `DONE = "done"`, `ERROR = "error"`. Confirmado.
- `nyx/agent/tui/widgets/chat_message.py:28` -- `_VALID_ROLES = ("user", "assistant", "tool", "system")`; property `content` em `:107`; `set_content` em `:155`. Confirmado: os roles e metodos que o fix usa existem.

**Divergencia material do briefing: nenhuma.** O achado e integralmente reproduzivel; linhas e mecanismos batem.

**Detalhe de implementacao descoberto (não e divergencia do achado):** `SessionState` não esta importado em `nyx/agent/tui/app.py` (verificado: zero import do enum no arquivo). Para não ampliar o escopo com um import novo, o fix deve comparar o estado pela string do valor -- `(getattr(status.state, "value", "") == "error")` -- espelhando exatamente o que `cli.py:471-473` ja faz (`state_label = status.state.value; if state_label == "error"`). Isso mantem o touch restrito a um único bloco e evita acoplar a TUI ao simbolo do enum.

---

## Solução proposta

Reescrever o bloco pos-await (764-774), dentro do `try` de `_process_turn`, para deixar de descartar o `SessionStatus`. A logica nova e ADITIVA e cobre tres casos, nesta ordem:

1. **`state == "error"` -> monta erro honesto.** `ChatMessage("system", status.summary)` no `#chat` (mesmo padrão do crash-guard 782-789). A mensagem PT-BR do loop ja e honesta e acionavel; o usuário deixa de ver silencio.
2. **`state == "done"` com summary não-subset do streamado.** Reusa a logica `_is_subset` (portada inline de `cli.py:456-462`) contra `_current_assistant.content` (o texto ja streamado). Se o balao existe e ja contem o summary, no-op (happy-path de texto puro fica byte-identico). Se o balao existe e contem `done(` cru, troca pelo summary (preserva TUI-DONE-SUMMARY-CLEAN-01). Se o balao não existe (turno tool-only, `_current_assistant is None`) e o summary e não-vazio, monta `ChatMessage("assistant", summary)`.

Todo o resto de `_process_turn` (o `except` crash-guard, o `finally`) fica intocado.

---

## Arquivos alvo (paths absolutos)

### `/home/andrefarias/Desenvolvimento/Nyx-Code/nyx/agent/tui/app.py`

#### Edit único — substituir o bloco pos-await (764-774) que descarta o status

# Localizacao: dentro do `try:` de `_process_turn`, logo apos `status = await self._agent.run(text)` (linhas 764-774)

**Antes:**
```python
            status = await self._agent.run(text)
            # TUI-DONE-SUMMARY-CLEAN-01 (SPRINT 303): o modelo as vezes emite
            # `done(summary="...")` como TEXTO (parser fallback), que o streaming
            # ja exibiu CRU no balao do NyxCode. O summary limpo esta no
            # SessionStatus de run(); quando o balao contem a sintaxe crua
            # `done(`, troca pelo summary. Resposta normal (texto puro) não casa
            # a condicao -- balao fica intacto.
            if status is not None and self._current_assistant is not None:
                summary = (getattr(status, "summary", "") or "").strip()
                if summary and "done(" in self._current_assistant.content:
                    self._current_assistant.set_content(summary)
```

**Depois:**
```python
            status = await self._agent.run(text)
            # TUI-STATUS-SUMMARY-RENDER-01: antes a TUI DESCARTAVA status.state
            # e status.summary fora do caso done()-cru abaixo -- dois buracos no
            # caminho único interativo (cli.py:538): (1) state==error (proxy
            # caido/timeout/OOM) sem token streamado => silencio absoluto apos o
            # 'pensando...' sumir (fere ADR-033); (2) turno so tool_calls +
            # done(summary=...) => summary final e dados crus do G3 nunca
            # aparecem (fere G3 ONDA-48). O REPL legado ja resolvia (cli.py:463-
            # 477), mas so roda em não-TTY. SessionState não e importado aqui:
            # compara-se pelo .value, como cli.py:471-473.
            if status is not None:
                summary = (getattr(status, "summary", "") or "").strip()
                state_value = getattr(getattr(status, "state", None), "value", "")
                if state_value == "error":
                    # ADR-033: erro de proxy nunca vira silencio -- a mensagem
                    # PT-BR honesta e acionavel do loop (ex. 'Conexão recusada
                    # pelo proxy... reinicie o stack com ./run.sh') aparece no
                    # chat como mensagem de sistema.
                    if summary:
                        chat = self.query_one("#chat", VerticalScroll)
                        chat.mount(ChatMessage("system", summary))
                elif summary:
                    streamed = (
                        self._current_assistant.content
                        if self._current_assistant is not None
                        else ""
                    ).strip()

                    def _is_subset(a: str, b: str) -> bool:
                        # cli.py:456-462: True se a e essencialmente contido em b
                        # (ignora whitespace). Evita eco do summary ja streamado.
                        ca = " ".join(a.split())
                        cb = " ".join(b.split())
                        return bool(ca) and bool(cb) and (ca in cb or cb in ca)

                    if self._current_assistant is not None:
                        # TUI-DONE-SUMMARY-CLEAN-01 (SPRINT 303) preservado: o 3b
                        # as vezes emite done(summary="...") como TEXTO cru, ja
                        # exibido no balao; troca pelo summary limpo.
                        if "done(" in self._current_assistant.content:
                            self._current_assistant.set_content(summary)
                        # G3: se o balao existe mas o summary tem conteudo alem
                        # do streamado (dados crus da tool), atualiza; se ja e
                        # subset, no-op (texto puro normal fica byte-identico).
                        elif not _is_subset(summary, streamed):
                            self._current_assistant.set_content(summary)
                    else:
                        # G3 / turno tool-only: nenhum token de texto foi
                        # streamado (_current_assistant is None), entao o summary
                        # final e o único lugar onde a resposta e os dados crus
                        # da tool aparecem. Monta o balao do assistant agora.
                        chat = self.query_one("#chat", VerticalScroll)
                        chat.mount(ChatMessage("assistant", summary))
```

> Nota ao executor: `ChatMessage` e `VerticalScroll` ja estao importados e em uso em `_process_turn` (ver o `except` crash-guard, linhas 782-789, que faz exatamente `chat = self.query_one("#chat", VerticalScroll)` + `chat.mount(ChatMessage("system", ...))`). O fix reusa esse padrão; nenhum import novo. Se o linter reclamar de função aninhada redefinida por turno, o executor pode promover `_is_subset` a metodo estatico do modulo -- decisao dele, desde que a semantica de cli.py:456-462 seja preservada byte-a-byte.

---

## Diff esperado (resumo)

```
~ 1 arquivo modificado (nyx/agent/tui/app.py)
+ ~35 linhas liquidas (fix aditivo num único bloco de _process_turn; sem meta numerica de tamanho)
```

Sem aritmetica de extracao: esta sprint não tem meta `arquivo < NNNL`. O único numero relevante e o net-add (~35L) num único metodo.

---

## Comandos de verificação (literais, copy-paste)

```bash
cd /home/andrefarias/Desenvolvimento/Nyx-Code

# 1. Estatica + acentuacao (ruff via binario direto -- não ha modulo ruff no venv, ver BRIEF)
/home/andrefarias/.local/bin/ruff check nyx/agent/tui/app.py
python3 ~/.config/zsh/scripts/validar-acentuacao.py --paths nyx/agent/tui/app.py

# 2. Confirmar as ancoras (linhas podem ter deslizado -- reconferir):
rg -n "await self._agent.run|status.state|status.summary|_is_subset|ChatMessage\(\"system\"|ChatMessage\(\"assistant\"" nyx/agent/tui/app.py

# 3. PROOF RUNTIME-REAL sem GPU (regra: não subir Ollama/GPU nem run.sh/gauntlet).
#    Fabrica SessionStatus (state=ERROR e state=DONE) e exercita a MESMA logica
#    de decisao de _process_turn (role resultante), sem instanciar a App Textual.
#    Isola a decisao pura: state==error -> role 'system'; DONE tool-only -> role
#    'assistant'; DONE subset -> nenhum balao novo.
./venv/bin/python - <<'PY'
from nyx.agent.models import SessionState, SessionStatus

def _is_subset(a, b):
    ca = " ".join(a.split()); cb = " ".join(b.split())
    return bool(ca) and bool(cb) and (ca in cb or cb in ca)

def decide(status, streamed):
    """Espelha a decisao do bloco pos-await de _process_turn."""
    summary = (getattr(status, "summary", "") or "").strip()
    state_value = getattr(getattr(status, "state", None), "value", "")
    if state_value == "error":
        return ("system", summary) if summary else None
    if summary:
        s = (streamed or "").strip()
        if streamed is not None and streamed != "":
            if "done(" in streamed:
                return ("assistant-set", summary)
            if not _is_subset(summary, s):
                return ("assistant-set", summary)
            return None  # subset: no-op
        return ("assistant-mount", summary)  # tool-only, sem balao
    return None

# Cenario 1: erro de proxy, nenhum token streamado
st_err = SessionStatus(state=SessionState.ERROR,
                       summary="Conexão recusada pelo proxy de inferencia. "
                               "Reinicie o stack com ./run.sh.")
r1 = decide(st_err, streamed=None)
assert r1 == ("system", st_err.summary), r1
print("AC1 OK: state==error -> role 'system' com a msg honesta")

# Cenario 2: turno tool-only, DONE com summary, sem balao
st_done = SessionStatus(state=SessionState.DONE, summary="Criei o arquivo X.\n[dados crus]")
r2 = decide(st_done, streamed=None)
assert r2 == ("assistant-mount", st_done.summary), r2
print("AC2 OK: DONE tool-only -> monta balao 'assistant'")

# Cenario 3: texto puro normal, summary e subset do streamado -> no-op
st_pure = SessionStatus(state=SessionState.DONE, summary="Ola, tudo certo.")
r3 = decide(st_pure, streamed="Ola, tudo certo.")
assert r3 is None, r3
print("AC3 OK: summary subset do streamado -> nenhum balao extra")

print("PROOF OK: a decisao pura fecha AC1/AC2/AC3 sem GPU")
PY

# 4. Invariantes + smoke boot
bash scripts/sprint_invariants.sh
./run.sh --smoke   # deve imprimir 'boot ok'
```

> Nota GPU (DEFERIDO): o teste as-user com stack real -- parar o Ollama de proposito e mandar um prompt na TUI para ver a mensagem honesta, e rodar um turno tool-only real para ver o summary -- exige GPU exclusiva. Executar so quando `pgrep -af "Luna.*driver|valida_sprint"` estiver vazio (protocolo anti-contencao do BRIEF), como as specs 403/407 fazem. O passo 3 prova a logica de decisao SEM GPU.

---

## Criterio binario de aceite (IA executora)

- [ ] `state == "error"` monta `ChatMessage("system", status.summary)` no `#chat` (AC1) -- comparado via `.value`, sem importar `SessionState`
- [ ] DONE tool-only (`_current_assistant is None`, summary não-vazio) monta `ChatMessage("assistant", summary)` (AC2)
- [ ] Guard `_is_subset` (semantica de cli.py:456-462) evita eco quando o summary ja esta streamado (AC3)
- [ ] Caso `done(` cru preservado (TUI-DONE-SUMMARY-CLEAN-01) (AC4)
- [ ] `except TUI-WORKER-CRASH-GUARD-01` (775-789) e o `finally` (790-806) byte-identicos (AC5)
- [ ] Proof runtime-real colado (passo 3): AC1/AC2/AC3 verdes, SEM GPU
- [ ] `ruff` limpo, acentuacao rc=0, `FAIL_AFTER <= FAIL_BEFORE`, smoke boot ok
- [ ] Teste as-user com stack real: DEFERIDO para GPU exclusiva (registrar no proof como pendente)
- [ ] `SPRINT_ORDER_MASTER.md` marca 426 CONCLUIDA; spec movida para `concluidos/`
- [ ] NÃO commitar; NÃO tocar Checkpoint.md; NÃO tocar loop/_core.py/cli.py

---

## Guardrails anti-engodo (obrigatorios)

NÃO marcar concluida se:
- O `except` crash-guard (775-789) foi tocado (ele cobre exceção, não `state==error` de retorno normal -- confundir os dois e o erro classico aqui).
- O happy-path de texto puro mudou (summary subset do streamado deve seguir SEM balao extra -- AC3).
- O caso `done(` cru deixou de trocar o content pelo summary limpo (regressao de TUI-DONE-SUMMARY-CLEAN-01).
- Importou `SessionState` em `app.py` sem necessidade (a comparacao por `.value` e o caminho de menor escopo; se o executor preferir o import, deve justificar -- mas não e o pedido).
- Tocou o loop/`_core.py`/`models.py`/`cli.py` (a origem do status ja esta correta; o bug e so a camada de UI descartando-o).
- Proof runtime-real (passo 3) não colado, ou alguma das assercoes AC1/AC2/AC3 falhou.

Se algo falhar: `[SPRINT 426] BLOQUEADA: <motivo 1 linha>`.

---

## Proof-of-work esperado (runtime-real do VALIDATOR_BRIEF.md)

```bash
bash scripts/sprint_invariants.sh > /tmp/inv_before.txt 2>&1
FAIL_BEFORE=$(grep -c "^\[FAIL\]" /tmp/inv_before.txt)
# implementar
bash scripts/sprint_invariants.sh > /tmp/inv_after.txt 2>&1
FAIL_AFTER=$(grep -c "^\[FAIL\]" /tmp/inv_after.txt)
diff /tmp/inv_before.txt /tmp/inv_after.txt
```

Baseline esperado: `FAIL_BEFORE = 0`, `FAIL_AFTER <= 0`. Colar: `inv_before`/`inv_after` (tail), diff, o output do proof runtime-real (passo 3), o `rg` das ancoras (passo 2), `git --no-pager diff --stat` e `./run.sh --smoke` (deve imprimir `boot ok`).

**Proof que exige GPU -- DEFERIDO para GPU exclusiva** (como 403/407): teste as-user com stack real na TUI (Ollama parado -> mensagem honesta de sistema; turno tool-only -> summary no balao do assistant). Executar so com `pgrep -af "Luna.*driver|valida_sprint"` vazio.

---

## Gambiarras especificas desta sprint

- **Comparacao por `.value`, não por `SessionState.ERROR`:** `SessionState` não esta importado em `app.py`; comparar `getattr(status.state, "value", "") == "error"` (como cli.py:471-473) mantem o touch num único bloco e evita acoplar a TUI ao simbolo do enum. Trade-off consciente: string em vez de enum, em nome do escopo cirurgico.
- **`_is_subset` inline vs metodo:** a semantica precisa ser identica a cli.py:456-462; definir a função dentro do bloco e o caminho de menor toque, mas redefine por turno. Se o `ruff` reclamar, promover a metodo estatico e aceitavel (decisao do executor), desde que a logica não mude.
- **Ler `_current_assistant` ANTES do `finally`:** o `finally` (806) reseta `_current_assistant = None`; a leitura para decidir mount vs set precisa ficar no `try`, no bloco pos-await -- nunca no `finally`.
- **`state==error` monta 'system', não 'assistant':** a mensagem e da infra (proxy fora), não do modelo -- role 'system' e o correto (mesmo role que o crash-guard usa), coerente com o REPL que chama `_print_error`.

---

## Riscos e não-objetivos

| Risco / não-objetivo | Decisao |
|-------|-----------|
| Hardening do lado do proxy (middleware que devolva JSON estruturado) | NÃO-OBJETIVO. O fix e client-side na UI; o loop ja produz a mensagem honesta. Ver sprint 413 (proxy status-before-json). |
| Unificar a logica de render entre TUI e REPL num helper compartilhado | Fora de escopo -- refactor maior. O fix porta a semantica de cli.py:456-477 inline; se o dono quiser DRY, registrar sprint própria (anti-debito). |
| Mudar o texto das mensagens de erro do loop | Fora de escopo -- as mensagens PT-BR do loop ja sao honestas; a TUI so precisa exibi-las. |
| Estado `max_iterations`/`cancelled` na TUI | Fora de escopo desta sprint (ver Fora de escopo abaixo). |

---

## Fora de escopo (anti-debito)

O REPL legado trata `state != DONE` de forma generica (`cli.py:472-479`): alem de `error`, os estados `max_iterations` e `cancelled` imprimem um marcador `[state_label]`. A TUI, apos este fix, cobre `error` e `done`, mas não exibe um aviso equivalente para `max_iterations`/`cancelled` (esses terminam sem balao e sem marcador). E um mecanismo aparentado, porem distinto (aviso de estado não-terminal vs. render de summary/erro) e de severidade menor -- o usuário ao menos não ve silencio de crash, so ausencia de um rotulo de estado. **Recomendacao:** registrar sprint própria `TUI-STATE-LABEL-NONTERMINAL-01` (feedback_nenhum_debito) para paridade com cli.py:472-479 nos estados `max_iterations`/`cancelled`. NÃO absorver aqui -- manter esta sprint cirurgica nos dois buracos verificados (silencio de erro + resposta tool-only sumida).

---

## Referencias

- BRIEF: `/home/andrefarias/Desenvolvimento/Nyx-Code/VALIDATOR_BRIEF.md`
- Origem: auditoria de prontidao 2026-07-12 (achado verificado adversarialmente, evidencia file:line)
- Codigo: `nyx/agent/tui/app.py:764-774` (bug), `775-789` (crash-guard distinto), `nyx/cli.py:456-477` (referencia correta, so não-TTY), `nyx/agent/loop/_iteration.py:977-982` (msg honesta), `nyx/agent/loop/_core.py:340-346, 446-450` (origem do status + G3)
- Estrutura de spec: `dev-journey/06-sprints/producao/SPRINT_EXEC_CONTRACT_PROXY_STATUS_BEFORE_JSON_01.md`

---

*"A cadeia nunca quebra na mao do usuário sem rastro (ADR-033); um summary composto que a UI joga fora e um contrato G3 que morre na última milha."*
