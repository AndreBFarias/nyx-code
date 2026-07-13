## 0. SPEC (machine-readable)

```yaml
sprint:
  id: LOOP-GUARD-FLAGS-INTRA-BATCH-01
  numero: 417
  title: "Guard 1x rejeitado deve encerrar o batch/turno -- o hint precisa voltar ao modelo antes da 2a tentativa; eco teimoso precisa de teto de convergência"
  onda: 48
  prioridade: ALTA
  tipo: Bugfix
  dependencias: []
  desbloqueia: []
  absorve: []

  touches:
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/agent/loop/_iteration.py
      reason: "no batch loop de _execute_tool_calls, trocar o `continue` das rejeições de guard 1x (done/tool-match/seq-edit) e do echo-reject por `return None`, para que a proxima tentativa so ocorra apos o hint entrar no contexto; armar contador de eco por turno e forçar fim honesto ao estourar o teto (achado 2)"
      linhas_alvo: "328-381 (batch loop), 341-344 (echo-reject), 348-353 (tool-match), 357-362 (seq-edit), 367-372 (done-reject), 241-245 (reset de flags em arm_done_guard), 192-197 (constante _ECHO_REJECT_HINT / novo _ECHO_REJECT_MAX); 573-576 (echo-reject do parser fallback -- contador simetrico)"
  creates: []
  removes: []

  forbidden:
    - "Adicionar emoji"
    - "Usar 'print()' fora de cli.py/output.py"
    - "Menção a IA proprietaria"
    - "Alterar a semantica dos predicados de guard (_should_reject_done, _tool_match_reject, _seq_edit_reject, strip_result_echo) -- so muda o FLUXO apos a rejeição, não a decisão de rejeitar"
    - "Tocar o happy-path: tool_call valido único executa byte-identico"
    - "Mudar os `continue` das rejeições NÃO-1x (plan_mode 388, permissão 393, preflight 437) -- essas são por-tool e devem seguir processando o resto do batch"
    - "Tocar _call_llm, o proxy, o gating ou a cascata OOM"
    - "Alterar os textos dos hints (_DONE_REJECT_HINT, _ACTION_REJECT_HINT, _TOOL_MATCH_HINT, _SEQ_*_HINT, _ECHO_REJECT_HINT)"

  tests:
    - cmd: "/home/andrefarias/.local/bin/ruff check nyx/agent/loop/_iteration.py"
      deve_passar: true
    - cmd: "python3 ~/.config/zsh/scripts/validar-acentuacao.py --paths nyx/agent/loop/_iteration.py"
      deve_passar: true
    - cmd: "bash scripts/sprint_invariants.sh"
      deve_passar: true
    - cmd: "./run.sh --gauntlet --only loop"
      timeout: 120
      deve_passar: true
      nota: "DEFERIDO para GPU exclusiva se o suite loop puxar Ollama; o proof-of-work principal (runtime-real inline) NÃO precisa de GPU"

  acceptance_criteria:
    - "AC1 (achado 1 -- done duplicado): batch `[done(summary=X), done(summary=X)]` num turno que pediu ação e nada executou -> o 1o done e rejeitado (hint re-emitido) e `_execute_tool_calls` retorna None SEM processar o 2o done; o turno NÃO termina com summary alucinado nessa mesma iteração"
    - "AC2 (achado 1 -- tool-match): num pedido de leitura pura, batch `[write_file(a), write_file(b)]` -> o 1o write e rejeitado pelo tool-match e o batch encerra (return None); o 2o write NÃO executa a mutação na mesma iteração"
    - "AC3 (achado 1 -- seq-edit): batch com 2+ escritas inseguras -> a 1a rejeição de seq-edit encerra o batch; a 2a NÃO passa sem o hint ter voltado ao modelo"
    - "AC4 (simetria com o parser fallback): o comportamento do batch loop passa a espelhar `_execute_parsed_action`, que ja retorna None ao rejeitar (não `continue`) -- confirmando que a correção alinha os dois caminhos"
    - "AC5 (achado 2 -- eco teimoso): apos _ECHO_REJECT_MAX rejeições de eco no MESMO turno, em vez de re-emitir o hint indefinidamente, o loop força um fim honesto (SessionState.DONE com summary de _build_force_done_summary), sem queimar as 50 iterações"
    - "AC6 (flags/reset): `_echo_reject_count` e armado (reset para 0) em arm_done_guard junto das demais flags de turno; nenhum estado vaza entre turnos"
    - "AC7: happy-path intacto (tool_call valido único executa e o turno segue); rejeições NÃO-1x (plan_mode, permissão, preflight) seguem com `continue`; ruff limpo, acentuação rc=0, FAIL_AFTER <= FAIL_BEFORE, smoke boot ok"
```

---

# Sprint LOOP-GUARD-FLAGS-INTRA-BATCH-01 — Guard 1x rejeitado tem que encerrar o batch; eco teimoso precisa de teto

**Status:** PENDENTE
**Data criação:** 2026-07-12
**Modelo obrigatório:** claude-opus-4-7 (executor-sprint autorizado pelo dono nesta onda)

---

## Contexto do projeto (snapshot — não referência)

> **Missão (ADR-032/033/034):** o Nyx-Code faz o pior LLM local (qwen2.5-coder:3b) na pior máquina (RTX 3050, VRAM 2.5GB) parecer o Claude Code offline. Robustez pertence a INFRA, não ao modelo. O usuário-alvo e leigo e sem hardware bom: cada iteração desperdiçada e minutos de GPU girando na frente dele. <!-- noqa-anonimato -->
>
> **Estado (2026-07-12):** `qwen2.5-coder:3b`. ONDA-48 fase raiz: núcleo do contrato de execução (guards 397/398/399/400/401) CONCLUIDO e commitado. Estes guards implementam o padrão "rejeita 1x + re-emite hint": ao detectar um tool_call errado, a infra rejeita a chamada uma vez, injeta um hint no histórico e deixa o modelo tentar de novo. O pressuposto do padrão e que **o hint chega ao modelo antes da 2a tentativa** -- pressuposto que esta sprint descobre ser FALSO dentro de um mesmo batch de tool_calls.
>
> Desenho: `dev-journey/02-architecture/DESENHO_CONTRATO_EXECUCAO.md` (§6, "Honestidade na falha"). Origem: auditoria de prontidão 2026-07-12 (achados verificados adversarialmente com evidência file:line).

---

## Problema

Dois achados do MESMO subsistema (a convergência da rejeição-de-guard no batch loop de `_execute_tool_calls`), tratados como ACs separados.

### Achado 1 (ALTA) — flags 1x são consumidas intra-batch: o 2o tool_call do MESMO response derrota o guard sem o modelo ver o hint

O batch loop `for tc in tool_calls:` (`_iteration.py:328`) itera o response inteiro do modelo. Quando um guard 1x rejeita um tool_call, ele seta a flag, injeta o hint via `add_tool_call(...)` e dá **`continue` para o PRÓXIMO tc do MESMO batch**:

- done-reject: `_iteration.py:367-372` -- `_should_reject_done()` (L368) rejeita, `self._done_rejected = True` (L370), `continue` (L372). E `_should_reject_done` retorna None assim que `_done_rejected` e True (L270);
- tool-match: `_iteration.py:348-353` -- `self._tool_match_rejected = True` (L350), `continue` (L353);
- seq-edit: `_iteration.py:357-362` -- `self._seq_edit_rejected = True` (L359), `continue` (L362).

O hint só volta ao modelo na PRÓXIMA chamada `_call_llm` (o caller `_core.py:462-465` faz `continue` no loop externo só quando `_execute_tool_calls` retorna None). Mas o `continue` interno NÃO retorna -- ele processa o próximo tc do mesmo batch, com a flag ja consumida e o hint ainda invisivel ao modelo.

**Impacto (pior JSON do 3b -- tool_calls duplicados e padrão comum):**

- `[done(summary="fiz X"), done(summary="fiz X")]`: o 1o done e rejeitado, `_done_rejected` vira True; o 2o done chega ao `is_done` (L367), `_should_reject_done()` agora retorna None (gate ja consumido), e o turno **termina com o summary alucinado na MESMA iteração** -- o hint jamais voltou ao modelo;
- `[write_file(a), write_file(b)]` num pedido de leitura: o 1o write consome o tool-match; o 2o **executa a mutação** que o guard existia para impedir.

O mecanismo "rejeita 1x + re-emite" pressupõe que o hint chega ao modelo antes da 2a tentativa. Dentro do batch isso e falso.

### Achado 2 (MEDIA) — echo-reject não tem flag 1x nem passa pelo detector de repetição: o modelo teimoso queima as 50 iterações

O echo-reject (`_iteration.py:341-344`) rejeita um tool_call cujo arg e puro eco do resultado anterior, injeta `_ECHO_REJECT_HINT` e dá `continue` -- **sem nenhuma flag 1x/turno** (diferente de tool-match e seq-edit) e **antes de `_check_repetition` (L426)**, então SKIP/FORCE_DONE nunca acumulam pressão por esse caminho.

`MAX_ITERATIONS` = 50 (`nyx/config/defaults.py:72`). O 3b que insiste em `search(pattern=<eco do resultado anterior>)` -- parroting típico de modelo fraco -- e rejeitado infinitamente com o mesmo hint: **50 roundtrips de LLM na RTX 3050** (minutos de GPU) ate "Atingiu limite de 50 iterações". Todos os outros guards convergem (via flag 1x que encerra o turno, ou via detector de repetição -> FORCE_DONE); o echo-reject e o único sem nenhum dos dois mecanismos de convergência.

---

## Causa-raiz (verificada no código real -- 2026-07-12)

Confirmado em `nyx/agent/loop/_iteration.py` (linhas conferidas, pequeno deslize vs briefing anotado abaixo):

| Elemento | Linha real | Briefing | Confere |
|----------|-----------|----------|---------|
| `for tc in tool_calls:` | 328 | 328 | OK |
| echo-reject (`continue`, sem flag) | 341-344 | 341-344 | OK |
| tool-match (`_tool_match_rejected=True`, `continue`) | 348-353 (flag 350) | 349-353 | deslize de 1 linha |
| seq-edit (`_seq_edit_rejected=True`, `continue`) | 357-362 (flag 359) | 357-362 | OK |
| done-reject (`_done_rejected=True`, `continue`) | 367-372 (flag 370) | 369-372 | OK |
| gate `_should_reject_done` (`if _done_rejected: return None`) | 270 | 270 | OK |
| `_check_repetition` (chamada) | 426 | 426 | OK |
| montagem de tool_calls em `_call_llm` (sem dedup) | 953-967 | 953-967 | OK |
| `MAX_ITERATIONS = 50` | defaults.py:72 | defaults.py:72 | OK |

**Divergências / achados adicionais da investigação (registrados por honestidade):**

1. **O caminho do parser fallback ja esta correto.** `_execute_parsed_action` (L528-668) tem os MESMOS guards (echo L573-576, tool-match L579-584, seq-edit L587-592, done L534-539), mas processa UMA ação e **retorna None** ao rejeitar (não `continue`), o que encerra o processamento e força um novo roundtrip com o hint no contexto. Ou seja: o comportamento-alvo desta sprint ja existe no caminho do parser; o batch loop e o único assimetrico. A correção alinha o batch loop ao parser (AC4). O briefing não menciona essa simetria; ela confirma a direção do fix.

2. **A raiz do achado 1 e o `continue`, não a flag.** O briefing sugere duas alternativas ("descartar o resto do batch" OU "marcar a flag apenas na fronteira da iteração"). A 1a e cirúrgica e local (troca `continue` -> `return None`); a 2a exigiria reestruturar o ciclo de vida das flags e e mais invasiva. Esta spec adota a 1a (GUIDE §2/§3: mínimo que resolve).

3. **Completude do achado 2.** O echo-reject existe em DOIS lugares (batch L341 e parser L573). Para o teto de convergência ser real, o contador de eco por turno precisa ser incrementado em AMBOS -- senão um modelo que alterne entre tool_calls nativos e content parseavel evadiria o teto. O briefing cita só o batch (L342); a spec cobre os dois (AC5).

4. **`_build_force_done_summary` esta em `_core.py:533`**, no mesmo objeto (AgentLoop e composto por mixins `_iteration` + `_core`), acessivel via `self.` -- ja usado por `_check_repetition` (L702). Reusa-lo no teto de eco garante summary honesto (não afirma artefato inexistente).

---

## Solução proposta

Correções cirúrgicas, todas dentro de `_execute_tool_calls` (+ uma linha em `arm_done_guard`, uma constante nova, e o contador simetrico no parser fallback). Nada muda nos predicados de decisão dos guards -- só o FLUXO apos a rejeição.

### Achado 1 — encerrar o batch quando um guard 1x rejeita

Trocar o `continue` por `return None` nas três rejeições de guard 1x (done, tool-match, seq-edit) e no echo-reject. Ao retornar None, o caller (`_core.py:462-465`) faz `continue` no loop externo e dispara um novo `_call_llm` -- agora com o hint ja no histórico, visivel ao modelo. As rejeições NÃO-1x (plan_mode L388, permissão L393, preflight L437) seguem com `continue` (são por-tool, não dependem de re-emissão de hint).

### Achado 2 — teto de convergência para o eco teimoso

Armar `self._echo_reject_count = 0` em `arm_done_guard` (junto das outras flags de turno). Adicionar a constante `_ECHO_REJECT_MAX` (sugerido: 3). No echo-reject (batch e parser), incrementar o contador; ao atingir `_ECHO_REJECT_MAX`, em vez de re-emitir o hint, **forçar um fim honesto**: `SessionStatus(state=SessionState.DONE, summary=self._build_force_done_summary(create_unmet=self._turn_create_unmet()))`. Isso troca 50 roundtrips por no máximo ~3, com uma mensagem honesta ao usuário leigo (ADR-033: forçar o fim e aceitavel; mentir sobre o fim, não).

---

## Arquivos alvo (paths absolutos)

### `/home/andrefarias/Desenvolvimento/Nyx-Code/nyx/agent/loop/_iteration.py`

#### Edit 1 — constante do teto de eco (perto de `_ECHO_REJECT_HINT`, ~L192-197)

**Adicionar** (logo apos o bloco `_ECHO_REJECT_HINT`):
```python
    # LOOP-GUARD-FLAGS-INTRA-BATCH-01 (achado 2): teto de convergência do eco.
    # Sem flag 1x nem passagem pelo detector de repetição, o echo-reject podia
    # queimar as 50 iterações contra um 3b que parroteia o resultado anterior.
    # Ao atingir este teto no turno, força um fim honesto (não 50 roundtrips).
    _ECHO_REJECT_MAX = 3
```

#### Edit 2 — armar o contador de eco em `arm_done_guard` (~L241-245)

**Depois de** `self._seq_edit_rejected = False` (L245), adicionar:
```python
        # LOOP-GUARD-FLAGS-INTRA-BATCH-01 (achado 2): contador de rejeições de
        # eco no turno (reset por turno, como as demais flags). Ao estourar
        # _ECHO_REJECT_MAX, o loop força um fim honesto em vez de reciclar o hint.
        self._echo_reject_count = 0
```

#### Edit 3 — echo-reject do batch: contador + teto + encerrar o batch (~L341-344)

**Antes:**
```python
            if _echo_reject:
                logger.warning("[loop] arg é puro eco de resultado anterior: %s", name)
                self._session.add_tool_call(name, args, self._ECHO_REJECT_HINT)
                continue
```
**Depois:**
```python
            if _echo_reject:
                # LOOP-GUARD-FLAGS-INTRA-BATCH-01 (achado 2): conta o eco no turno;
                # ao estourar o teto, força fim honesto em vez de reciclar o hint
                # ate MAX_ITERATIONS (o 3b parroteia o resultado anterior).
                self._echo_reject_count = getattr(self, "_echo_reject_count", 0) + 1
                logger.warning(
                    "[loop] arg é puro eco de resultado anterior (%dx): %s",
                    self._echo_reject_count,
                    name,
                )
                if self._echo_reject_count >= self._ECHO_REJECT_MAX:
                    summary = self._build_force_done_summary(
                        create_unmet=self._turn_create_unmet()
                    )
                    logger.info("[loop] FORCE_DONE por eco repetido (%dx)", self._echo_reject_count)
                    return SessionStatus(
                        state=SessionState.DONE, iterations=iteration, summary=summary
                    )
                self._session.add_tool_call(name, args, self._ECHO_REJECT_HINT)
                # LOOP-GUARD-FLAGS-INTRA-BATCH-01 (achado 1): encerra o batch para o
                # hint entrar no contexto ANTES da proxima tentativa (não `continue`).
                return None
```

#### Edit 4 — tool-match do batch: encerrar o batch (~L348-353)

**Trocar** a linha `continue` (L353) por:
```python
                # LOOP-GUARD-FLAGS-INTRA-BATCH-01 (achado 1): não `continue` -- o 2o
                # tc do batch derrotava o guard 1x (flag ja consumida) sem o modelo
                # ver o hint. Encerra o batch; a re-tentativa vem no próximo roundtrip.
                return None
```

#### Edit 5 — seq-edit do batch: encerrar o batch (~L357-362)

**Trocar** a linha `continue` (L362) por `return None` com o mesmo comentario de referência (achado 1).

#### Edit 6 — done-reject do batch: encerrar o batch (~L367-372)

**Trocar** a linha `continue` (L372) por `return None` com o mesmo comentario (achado 1). Assim o 2o `done(...)` do batch não escapa pelo gate `_should_reject_done` ja consumido.

#### Edit 7 — echo-reject do parser fallback: contador simetrico (~L573-576)

**Antes:**
```python
        if _echo_reject:
            logger.warning("[loop] arg é puro eco (parser): %s", tool_name)
            self._session.add_tool_call(tool_name, remapped, self._ECHO_REJECT_HINT)
            return None
```
**Depois** (o parser ja retorna None; falta só o contador para o teto ser simetrico entre os caminhos):
```python
        if _echo_reject:
            # LOOP-GUARD-FLAGS-INTRA-BATCH-01 (achado 2): mesmo contador do caminho
            # nativo -- senão um modelo que alterne nativo/parser evadiria o teto.
            self._echo_reject_count = getattr(self, "_echo_reject_count", 0) + 1
            logger.warning("[loop] arg é puro eco (parser, %dx): %s", self._echo_reject_count, tool_name)
            if self._echo_reject_count >= self._ECHO_REJECT_MAX:
                summary = self._build_force_done_summary(create_unmet=self._turn_create_unmet())
                logger.info("[loop] FORCE_DONE por eco repetido (parser, %dx)", self._echo_reject_count)
                return SessionStatus(state=SessionState.DONE, iterations=iteration, summary=summary)
            self._session.add_tool_call(tool_name, remapped, self._ECHO_REJECT_HINT)
            return None
```

---

## Diff esperado (resumo)

```
~ 1 arquivo modificado (nyx/agent/loop/_iteration.py)
+ ~35 linhas líquidas (constante + contador + teto em dois caminhos; troca de 4 `continue` por `return None` no batch)
```

Sem aritmética de extração: esta sprint não tem meta `arquivo < NNNL`. Fix aditivo/cirúrgico; o arquivo segue no mesmo patamar de tamanho.

---

## Comandos de verificação (literais, copy-paste)

```bash
cd /home/andrefarias/Desenvolvimento/Nyx-Code

# 1. Estatica + acentuação (ruff via binario direto -- não ha modulo ruff no venv, ver BRIEF)
/home/andrefarias/.local/bin/ruff check nyx/agent/loop/_iteration.py
python3 ~/.config/zsh/scripts/validar-acentuacao.py --paths nyx/agent/loop/_iteration.py

# 2. Confirmar as ancoras (linhas podem ter deslizado -- reconferir antes de editar):
rg -n "for tc in tool_calls|_done_rejected = True|_tool_match_rejected = True|_seq_edit_rejected = True|_echo_reject|_ECHO_REJECT_MAX|_echo_reject_count" nyx/agent/loop/_iteration.py

# 3. PROOF RUNTIME-REAL sem GPU/Ollama (exercita _execute_tool_calls real; nenhum
#    _call_llm, nenhum modelo -- so os guards). Constroi um AgentLoop real e passa
#    batches crafted direto ao batch loop.
./venv/bin/python - <<'PY'
import asyncio
from nyx.agent.loop._core import AgentLoop
from nyx.agent.loop._iteration import SessionState

# --- AC1: [done, done] num turno que pediu ação e nada executou ---
loop = AgentLoop(project_root=".")
loop.arm_done_guard("liste os arquivos da pasta")   # intent tool-needed; _turn_tool_count=0
batch = [
    {"name": "done", "arguments": {"summary": "listei os arquivos"}},
    {"name": "done", "arguments": {"summary": "listei os arquivos"}},
]
status = asyncio.run(loop._execute_tool_calls(batch, 1))
# O 1o done e rejeitado; o batch encerra (return None). O turno NÃO termina
# com summary alucinado nesta iteração.
assert status is None, f"AC1 FALHOU: o 2o done escapou -> {status}"
assert getattr(loop, "_done_rejected", False) is True, "AC1: o 1o done deveria ter sido rejeitado"
print("OK AC1: [done,done] -> 1o rejeitado, batch encerrado, sem summary alucinado")

# --- AC5: eco teimoso estoura o teto e fecha honesto ---
loop2 = AgentLoop(project_root=".")
loop2.arm_done_guard("busque no projeto")
loop2._recent_tool_outputs = ["conteudo do resultado anterior xyz"]
eco = {"name": "search", "arguments": {"pattern": "conteudo do resultado anterior xyz"}}
last = None
for i in range(1, loop2._ECHO_REJECT_MAX + 1):
    last = asyncio.run(loop2._execute_tool_calls([eco], i))
    if last is not None:
        break
assert last is not None and last.state == SessionState.DONE, f"AC5 FALHOU: eco não convergiu -> {last}"
assert loop2._echo_reject_count <= loop2._ECHO_REJECT_MAX, "AC5: contador estourou o teto"
print(f"OK AC5: eco convergiu em {loop2._echo_reject_count} rejeições (teto {loop2._ECHO_REJECT_MAX}), fim honesto")
PY

# 4. AC7 -- happy-path: um tool_call valido único ainda executa e o turno segue.
#    (Reusar o padrão acima com um list_files real num diretório de teste e
#    assertar que status is None E que a tool executou -- _turn_tool_count > 0.)

# 5. Invariantes
bash scripts/sprint_invariants.sh

# 6. Smoke boot (obrigatorio antes de CONCLUIDA -- feedback_smoke_boot)
./run.sh --smoke   # deve imprimir 'boot ok', exit 0

# 7. Gauntlet do loop -- DEFERIDO para GPU exclusiva se puxar Ollama
#    (executar so quando `pgrep -af "Luna.*driver|valida_sprint"` estiver vazio):
./run.sh --gauntlet --only loop
```

> Nota GPU: os passos 3-4 (proof principal) rodam SEM Ollama/GPU -- exercitam `_execute_tool_calls` real, sem nenhum `_call_llm`. O passo 7 (gauntlet loop) e DEFERIDO para GPU exclusiva (protocolo anti-contenção do BRIEF), como as specs 403/407 fazem.

---

## Critério binário de aceite (IA executora)

- [ ] AC1: batch `[done, done]` em turno que pediu ação -> 1o rejeitado, `_execute_tool_calls` retorna None, 2o done NÃO conclui o turno
- [ ] AC2: batch `[write_file, write_file]` em pedido de leitura -> 1o rejeitado por tool-match, batch encerra, 2a mutação NÃO executa
- [ ] AC3: 2+ escritas inseguras -> 1a rejeição de seq-edit encerra o batch
- [ ] AC4: os quatro `continue` de rejeição-1x/eco viraram `return None`; simetria com `_execute_parsed_action` confirmada
- [ ] AC5: apos `_ECHO_REJECT_MAX` ecos no turno -> FORCE_DONE honesto (SessionState.DONE), sem 50 iterações
- [ ] AC6: `_echo_reject_count` armado em `arm_done_guard` (reset por turno); contador incrementado no batch E no parser fallback
- [ ] AC7: happy-path intacto; rejeições NÃO-1x (plan_mode/permissão/preflight) seguem com `continue`
- [ ] Proof runtime-real colado (passo 3): AC1 e AC5 verdes, SEM GPU
- [ ] `ruff` limpo, acentuação rc=0, `FAIL_AFTER <= FAIL_BEFORE`, smoke boot `boot ok`
- [ ] `SPRINT_ORDER_MASTER.md` marca 417 CONCLUIDA; spec movida para `concluidos/`
- [ ] NÃO commitar; NÃO tocar Checkpoint.md; NÃO tocar `_call_llm`, o proxy nem o gating

---

## Guardrails anti-engodo (obrigatórios)

NÃO marcar concluída se:
- Algum predicado de guard (`_should_reject_done`, `_tool_match_reject`, `_seq_edit_reject`, `strip_result_echo`) teve a DECISÃO alterada -- só o fluxo pos-rejeição muda.
- O happy-path mudou (tool_call valido único deve executar e o turno seguir).
- As rejeições NÃO-1x (plan_mode, permissão, preflight) viraram `return None` -- essas devem seguir com `continue` (processar o resto do batch e correto para elas).
- O teto de eco fecha com summary que afirma artefato inexistente (usar `_build_force_done_summary(create_unmet=self._turn_create_unmet())` para honestidade).
- `_echo_reject_count` não reseta por turno (vazamento entre turnos -> FORCE_DONE prematuro no turno seguinte).
- Proof runtime-real não colado, ou AC1/AC5 vermelhos.
- Tocou `_call_llm`, `nyx/proxy.py`, gating ou a cascata OOM.

Se algo falhar: `[SPRINT 417] BLOQUEADA: <motivo 1 linha>`.

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
Baseline esperado: `FAIL_BEFORE = 0`, `FAIL_AFTER <= 0`. Colar: inv_before/inv_after (tail), diff, o output do proof runtime-real (passos 3-4 acima), o `rg` das ancoras (passo 2), `git --no-pager diff --stat` e `./run.sh --smoke` (deve imprimir `boot ok`). Gauntlet `--only loop` DEFERIDO para GPU exclusiva.

---

## Fora de escopo (anti-débito)

| Item | Decisão |
|------|---------|
| Dedup de tool_calls duplicados em `_call_llm` (L953-967) | **NÃO-OBJETIVO.** Seria uma 2a linha de defesa (colapsar `[done, done]` antes do loop). O fix desta sprint ja neutraliza o sintoma no batch loop. Se o dono quiser a dedup estrutural, registrar `INFRA-LLM-TOOLCALL-DEDUP-01` (feedback_nenhum_debito), não absorver aqui. |
| Rodar `_check_repetition` antes do echo-reject (alternativa do briefing p/ achado 2) | Descartada: o eco muda de conteudo a cada turno (pattern=<resultado NOVO anterior>), então o detector de repetição -- que casa por identidade de ação -- não pega de forma confiavel. O contador dedicado (AC5) e a escolha robusta. Registrado aqui por transparencia. |
| Ajuste de `_ECHO_REJECT_MAX` (3 vs 2) | Valor sugerido 3; se a validação holística mostrar que 2 fecha mais rapido sem falso-positivo, ajustar em sprint de tuning, não aqui. |

---

## Referências

- BRIEF: `/home/andrefarias/Desenvolvimento/Nyx-Code/VALIDATOR_BRIEF.md`
- Briefing de origem: auditoria de prontidão 2026-07-12 (achados verificados com evidência file:line)
- Desenho do contrato: `dev-journey/02-architecture/DESENHO_CONTRATO_EXECUCAO.md` (§6, "Honestidade na falha")
- Guards do núcleo (padrão rejeita-1x + re-emite): sprints 397/398/399/400/401 (ONDA-48), em `concluidos/`
- Spec-referência de formato: `dev-journey/06-sprints/producao/SPRINT_EXEC_CONTRACT_PROXY_STATUS_BEFORE_JSON_01.md`

---

*"O guard que rejeita e depois processa o próximo item do mesmo batch não rejeitou nada -- só adiou a alucinação em uma linha. O hint tem que voltar ao modelo antes da segunda tentativa, ou o mecanismo inteiro e teatro." -- causa-raiz do achado 1*
