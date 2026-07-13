## 0. SPEC (machine-readable)

```yaml
sprint:
  id: LOOP-PROSE-DONE-GUARD-01
  numero: 419
  title: "Estender o done-guard da 399 ao 3o caminho de DONE: conclusão por prosa (parser-fail) com ação pedida e zero tools"
  onda: 48
  prioridade: ALTA
  tipo: Bugfix
  dependencias: []
  desbloqueia: []
  absorve: []

  touches:
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/agent/loop/_core.py
      reason: "no ramo parser-fail de _run_iterations (o 3o caminho para SessionState.DONE, o único que NÃO consulta o guard da 399) consultar self._should_reject_done() ANTES de aceitar o content como resposta final; rejeitar 1x re-injetando o _ACTION_REJECT_HINT quando o turno pediu ação e zero tools rodaram"
      linhas_alvo: "493-515 (bloco forge + add_assistant + return DONE do parser-fail)"
  creates: []
  removes: []

  forbidden:
    - "Adicionar emoji"
    - "Usar 'print()' fora de cli.py/output.py"
    - "Menção a IA proprietária"
    - "Alterar os dois caminhos de DONE que JÁ consultam o guard (_iteration.py:368 is_done, _iteration.py:535 _execute_parsed_action DONE)"
    - "Alterar a lógica de _should_reject_done / _turn_wants_action / _turn_tool_count / _done_rejected em _iteration.py (só CONSUMIR, não redefinir)"
    - "Tocar o detect_forged_success / FORGE_PATTERNS (validator.py) -- a estreiteza dos padrões é justamente por que o guard 399 é necessário aqui, não se amplia o forge"
    - "Alterar o happy-path do parser (parse_result.success and parse_result.action segue byte-idêntico)"
    - "Alterar o ramo _looks_like_raw_toolcall (tool_call cru continua virando mensagem honesta)"
    - "Rebaixar MAX_ITERATIONS como rede final (a rejeição é 1x/turno; MAX_ITERATIONS continua sendo o teto)"

  tests:
    - cmd: "/home/andrefarias/.local/bin/ruff check nyx/agent/loop/_core.py"
      deve_passar: true
    - cmd: "python3 ~/.config/zsh/scripts/validar-acentuacao.py --paths nyx/agent/loop/_core.py"
      deve_passar: true
    - cmd: "bash scripts/sprint_invariants.sh"
      deve_passar: true
    - cmd: "./run.sh --smoke"
      deve_passar: true
    - cmd: "./run.sh --gauntlet --only rapido"
      timeout: 300
      deve_passar: true
      nota: "DEFERIDO para GPU exclusiva (exige Ollama vivo; rodar só com pgrep de contenção vazio)"

  acceptance_criteria:
    - "No ramo parser-fail de _run_iterations (_core.py:493-515), ANTES de self._session.add_assistant(final_content), consultar self._should_reject_done(); quando retorna hint (turno pediu ação + zero tools + ainda não rejeitou), NÃO retornar DONE: marcar self._done_rejected=True, re-injetar o hint (via _force_reminder/_reminder_extra) e continuar o loop"
    - "A rejeição é 1x/turno: na 2a vez que o content-prosa chega, _done_rejected já é True, _should_reject_done() devolve None e o turno conclui DONE normalmente (sem laço infinito); MAX_ITERATIONS permanece como rede final"
    - "O caminho só dispara quando _turn_wants_action=True E _turn_tool_count==0 (a alucinação em prosa pura): se qualquer tool rodou no turno, _turn_tool_count>0 e o content-prosa é aceito como summary honesto -- comportamento atual preservado"
    - "A prosa fabricada NÃO entra no histórico como resposta na iteração rejeitada (o content não-verificado é descartado; só o hint de correção é injetado) -- não se persiste dado fabricado"
    - "Proof runtime-real SEM GPU (fake _call_llm com prosa fabricada em input read-only): a 1a resposta-prosa é rejeitada (call count sobe para 2), a 2a conclui DONE; asserta _done_rejected True ao final e que o _ACTION_REJECT_HINT foi injetado no histórico"
    - "ruff limpo, acentuação rc=0, invariantes FAIL_AFTER <= FAIL_BEFORE, smoke boot ok"
```

---

# Sprint LOOP-PROSE-DONE-GUARD-01 — Conclusão por prosa não pode bypassar o done-guard da 399

**Status:** PENDENTE
**Data criação:** 2026-07-12
**Modelo obrigatório:** claude-opus-4-7 (executor-sprint autorizado pelo dono nesta onda)

---

## Contexto do projeto (snapshot — não referência)

> **Missão (por que isto importa):** o Nyx-Code faz o pior LLM local (`qwen2.5-coder:3b`) na pior máquina parecer o Claude Code offline. A robustez pertence à INFRA, não ao modelo (ADR-032/033/034). O usuário-alvo é leigo e sem hardware bom: quando o 3b alucina "o conteúdo do ~/.bashrc é ..." com dados fabricados, é a infra que tem de barrar, não o usuário que tem de desconfiar. <!-- noqa-anonimato -->
>
> **ADRs relevantes (inline):**
> - **ADR-032/033 A INFRA CARREGA O MODELO / ENFORCEMENT, NÃO CONFIANÇA:** o enforcement de "não conclua sem agir" é da infra; o modelo não é confiável para respeitar sozinho. Forçar o fim é aceitável; mentir sobre o fim, não.
> - ADR-034, ADR-009, ADR-026.
>
> **Estado (2026-07-12):** `qwen2.5-coder:3b`. ONDA-48 fase raiz: núcleo do contrato de execução (399/397/398/400/401) CONCLUIDO e commitado. Esta sprint é um satélite de robustez do MESMO mecanismo da 399 (EXEC-CONTRACT-NO-HALLUCINATED-RESULT-01): estende o done-guard ao terceiro caminho de DONE que a 399 deixou descoberto. Desenho: `dev-journey/02-architecture/DESENHO_CONTRATO_EXECUCAO.md` (§6, "Honestidade na falha"). Origem: auditoria de prontidão 2026-07-12 (achado verificado adversarialmente).

---

## Problema

**Achado (auditoria 2026-07-12, severidade ALTA):** existem TRÊS caminhos por onde `_run_iterations` retorna `SessionState.DONE`, mas o done-guard da 399 (`_should_reject_done()`) só é consultado em DOIS deles:

1. **DONE explícito via tool** — `_iteration.py:368` (`is_done(name)`): consulta o guard. OK.
2. **DONE via parser fallback** — `_iteration.py:535` (`_execute_parsed_action`, `ActionType.DONE`): consulta o guard. OK.
3. **DONE por prosa (parser-fail)** — `_core.py:493-515`: quando o parser falha em TODOS os níveis (`parse_result.success` é False), o `content` vira a resposta final e o turno retorna `SessionState.DONE` **sem NUNCA consultar `_should_reject_done()`**. Este é o caminho descoberto.

Nesse terceiro caminho, o único filtro é `detect_forged_success` (`_core.py:493`), que apenas **anexa** um aviso (`_core.py:505-508`) e cujos padrões são estreitos: `FORGE_PATTERNS` (`validator.py:21-26`) casa só `"... criado/salvo/escrito com sucesso"`, `"pronto"` e `"feito"` no fim da mensagem. Um relato de conteúdo fabricado ("O conteúdo do ~/.bashrc é: export PATH=...") **não casa nenhum padrão** — não recebe nem o aviso.

**Impacto (o modo de falha mais comum do pior modelo):** o turno pediu uma ação (`_turn_wants_action=True`), ZERO tools executaram (`_turn_tool_count==0`) e o 3b responde em prosa com dados fabricados. O turno termina `DONE`:
- sem re-emissão (o guard 399 nunca é consultado neste caminho),
- sem aviso (o `forge` não casa relato de conteúdo),
- sem dados crus (G3 vazio, nenhuma tool rodou; o "apresentação forte" da fase raiz fica sem substrato).

O sinal que a 399 já computa (`_turn_wants_action`, `_turn_tool_count`, `_done_rejected`) fica **inutilizado exatamente no caminho onde a alucinação mais escapa**. Para um usuário leigo, isso é o pior resultado possível: uma resposta confiante, verossímil e falsa, sem nenhum indício de que nada foi lido.

---

## Causa-raiz (verificada no código, 2026-07-12)

Verificação linha a linha (as linhas do briefing bateram; registro a única nuance abaixo):

- `nyx/agent/loop/_core.py:493-515` (dentro de `_run_iterations`, após o parser falhar no `if content:` da L468):
  - L493 `forge = detect_forged_success(content, self._session.history)`;
  - L499-504 se `_looks_like_raw_toolcall(content)`: content vira mensagem honesta (mantém);
  - L505-508 `elif forge.warnings:` apenas ANEXA `"[atenção: resposta não verificada por tool]"`;
  - L509 `self._session.add_assistant(final_content)`;
  - L511-515 `return SessionStatus(state=SessionState.DONE, ...)`.
  - **`self._should_reject_done()` não aparece em lugar nenhum deste bloco.**
- O guard existe e está armado no momento certo: `run()` chama `_init_done_guard(user_input)` em `_core.py:313` ANTES de `_run_iterations` (`_core.py:339`); `_init_done_guard` (`_iteration.py:227-245`) arma `_turn_wants_action`, `_turn_tool_count=0`, `_done_rejected=False`.
- `_should_reject_done()` (`_iteration.py:261-276`) devolve `self._ACTION_REJECT_HINT` (`_iteration.py:183-188`) exatamente quando `_turn_wants_action and _turn_tool_count == 0 and not _done_rejected`.
- Os dois caminhos que consultam o guard: `_iteration.py:368` e `_iteration.py:535`.

**Divergência do briefing (registrada):** o briefing aponta `_core.py:509` e diz que `_should_reject_done()` "só é consultado em is_done/_execute_parsed_action DONE". Substantivamente correto, com uma nuance de localização: o método `_should_reject_done` e os dois pontos que o consultam vivem no **mixin `_iteration.py`**, não em `_core.py`. Como `AgentLoop(_IterationMixin)` (`_core.py:93`), o fix dentro de `_core.py:_run_iterations` chama o método herdado `self._should_reject_done()` normalmente — nenhum import novo, nenhum acoplamento novo. O canal de re-injeção (`self._force_reminder` / `self._reminder_extra`) também já existe e já é usado neste MESMO bloco pela detecção de drift (`_core.py:475-476`), consumido por `_maybe_inject_reminder` (`_iteration.py:735-764`).

---

## Solução proposta

Uma única correção aditiva e cirúrgica dentro de `_run_iterations`, no topo do bloco parser-fail (imediatamente antes de `forge = detect_forged_success(...)` em `_core.py:493`): consultar o guard herdado; se ele pedir rejeição, descartar a prosa não-verificada, marcar `_done_rejected=True`, re-injetar o hint pelo canal de reminder e `continue` — em vez de retornar DONE.

Contrato preservado, byte a byte, por reuso de `_should_reject_done()`:
- rejeita **no máximo 1x/turno** (o próprio guard checa `_done_rejected` primeiro);
- só dispara com `_turn_wants_action=True` e `_turn_tool_count==0` (ou `_turn_create_unmet`) — se qualquer tool rodou, o content-prosa segue sendo aceito como summary;
- `MAX_ITERATIONS` continua sendo a rede final.

A prosa fabricada é **descartada** na iteração rejeitada (não entra no histórico como resposta): só o hint de correção é injetado, para não persistir dado fabricado. Na 2a passagem, `_done_rejected` já é True e o turno conclui normalmente.

---

## Arquivos alvo (paths absolutos)

### `/home/andrefarias/Desenvolvimento/Nyx-Code/nyx/agent/loop/_core.py`

#### Edit único — consultar o guard 399 no ramo parser-fail, antes de aceitar o content

# Localização: dentro de `_run_iterations`, no `if content:` (L468), logo após o
# bloco do parser fallback que falhou (o `continue` da L491), imediatamente antes
# de `forge = detect_forged_success(...)` (L493).

**Antes:**
```python
                forge = detect_forged_success(content, self._session.history)
                final_content = content
```

**Depois:**
```python
                # LOOP-PROSE-DONE-GUARD-01: 3o caminho para DONE (além de is_done
                # e _execute_parsed_action DONE) e o ÚNICO que NÃO consultava o
                # done-guard da 399. É exatamente onde a alucinação em prosa mais
                # escapa: o turno pediu ação, ZERO tools rodaram e o 3b relata
                # conteúdo fabricado -- o forge (padrões estreitos) não casa e o
                # turno terminava DONE sem re-emissão. Consulta o guard herdado
                # (_IterationMixin) e rejeita 1x, re-injetando o hint pelo mesmo
                # canal de reminder que a detecção de drift já usa acima. A prosa
                # não-verificada é DESCARTADA (não vira resposta): só a correção é
                # injetada. MAX_ITERATIONS segue como rede. DESENHO §6.
                reject_hint = self._should_reject_done()
                if reject_hint:
                    self._done_rejected = True
                    self._force_reminder = True
                    self._reminder_extra = reject_hint
                    logger.info(
                        "[loop] prose-done rejeitado 1x: turno pediu ação, zero tools"
                    )
                    continue

                forge = detect_forged_success(content, self._session.history)
                final_content = content
```

Nota ao executor: reusar `self._should_reject_done()` (não redefinir o predicado); o hint retornado já é o `_ACTION_REJECT_HINT` no caso alvo. Alternativa aceitável (se preferir simetria com os caminhos 368/535): injetar via `self._session.add_tool_call("done", {}, reject_hint)` em vez de `_force_reminder`/`_reminder_extra`; ambas satisfazem os ACs, desde que a prosa fabricada NÃO entre como resposta e a rejeição seja 1x. A via `_force_reminder` é a recomendada por já estar em uso neste exato bloco (L475-476).

---

## Diff esperado (resumo)

```
~ 1 arquivo modificado (nyx/agent/loop/_core.py)
+ ~14 linhas líquidas (fix aditivo; sem meta numérica de tamanho -- arquivo segue < 900L)
```

Sem aritmética de extração: esta sprint não tem meta `arquivo < NNNL`. O único número relevante é o net-add (~14L) num único arquivo, num ramo já existente.

---

## Comandos de verificação (literais, copy-paste)

```bash
cd /home/andrefarias/Desenvolvimento/Nyx-Code

# 1. Estática + acentuação (ruff via binário direto -- não há módulo ruff no venv, ver BRIEF)
/home/andrefarias/.local/bin/ruff check nyx/agent/loop/_core.py
python3 ~/.config/zsh/scripts/validar-acentuacao.py --paths nyx/agent/loop/_core.py

# 2. Confirmar as âncoras (linhas podem ter deslizado -- reconferir antes de editar):
rg -n "detect_forged_success\(content|final_content = content|_should_reject_done|SessionState.DONE" nyx/agent/loop/_core.py
rg -n "def _should_reject_done|_ACTION_REJECT_HINT|_turn_wants_action|_turn_tool_count|_done_rejected" nyx/agent/loop/_iteration.py

# 3. PROOF RUNTIME-REAL sem GPU (regra: NÃO subir Ollama/GPU).
#    AgentLoop real, _run_iterations real; só o _call_llm é faked por um
#    script de respostas em prosa (parser-fail). Input read-only faz o
#    _init_done_guard armar _turn_wants_action=True; zero tools rodam.
./venv/bin/python - <<'PY'
import asyncio
from nyx.agent.loop._core import AgentLoop
from nyx.agent.models import SessionState

loop = AgentLoop(project_root=".")

# Fake do transporte: sempre prosa fabricada, sem tool_calls, sem action parseável.
calls = {"n": 0}
async def fake_call_llm():
    calls["n"] += 1
    return {"content": "O conteúdo do ~/.bashrc é: export PATH=/usr/bin (relato fabricado)."}
loop._call_llm = fake_call_llm

# Input read-only -> intent 'tool-needed' -> _turn_wants_action=True.
status = asyncio.run(loop.run("leia o arquivo ~/.bashrc e me diga o conteúdo"))

print("intent wants_action:", loop._turn_wants_action)
print("tool_count        :", loop._turn_tool_count)
print("done_rejected     :", loop._done_rejected)
print("llm_calls         :", calls["n"])
print("state             :", status.state)

# A 1a prosa foi rejeitada (guard 399 aplicado ao 3o caminho); a 2a concluiu.
assert loop._turn_wants_action is True, "input read-only deveria armar wants_action"
assert loop._done_rejected is True, "a prosa deveria ter sido rejeitada 1x"
assert calls["n"] >= 2, ("prosa foi aceita de primeira -- guard NÃO aplicado", calls["n"])
assert status.state in (SessionState.DONE, SessionState.MAX_ITERATIONS), status.state
# O hint de ação foi injetado no histórico (via reminder / add_user).
hist = " ".join(getattr(e, "content", "") or "" for e in loop._session.history)
assert "ainda NÃO executou nenhuma ferramenta" in hist or "chame a ferramenta" in hist.lower(), \
    "o _ACTION_REJECT_HINT não apareceu no histórico"
print("OK: prosa-done rejeitada 1x, hint injetado, sem persistir dado fabricado como resposta")
PY

# 4. Guard NÃO regride o caso legítimo: se uma tool rodou (_turn_tool_count>0),
#    a prosa segue sendo aceita como summary. Variante do proof acima injetando
#    loop._turn_tool_count = 1 antes do run e assertando calls["n"] == 1.

# 5. Invariantes
bash scripts/sprint_invariants.sh

# 6. Smoke boot
./run.sh --smoke   # deve imprimir 'boot ok'

# 7. Gauntlet rápido (DEFERIDO -- exige GPU exclusiva)
./run.sh --gauntlet --only rapido
```

> Nota GPU: os passos 3-4 rodam SEM Ollama/GPU (`_call_llm` faked). O passo 7 (gauntlet) exige GPU exclusiva e fica **DEFERIDO** — executar só quando `pgrep -af "Luna.*driver|valida_sprint"` estiver vazio (protocolo anti-contenção do BRIEF), como as specs 403/407 fazem.

---

## Proof-of-work esperado

```bash
bash scripts/sprint_invariants.sh > /tmp/inv_before.txt 2>&1
FAIL_BEFORE=$(grep -c "^\[FAIL\]" /tmp/inv_before.txt)
# implementar
bash scripts/sprint_invariants.sh > /tmp/inv_after.txt 2>&1
FAIL_AFTER=$(grep -c "^\[FAIL\]" /tmp/inv_after.txt)
diff /tmp/inv_before.txt /tmp/inv_after.txt
```

Baseline esperado: `FAIL_BEFORE = 0`, `FAIL_AFTER <= 0`. Colar no relato:
- `inv_before`/`inv_after` (tail) e `diff`;
- o output do proof runtime-real (passos 3-4, SEM GPU);
- o `rg` das âncoras (passo 2);
- `git --no-pager diff --stat` e `./run.sh --smoke` (deve imprimir `boot ok`);
- Gauntlet `--only rapido`: **DEFERIDO para GPU exclusiva** (registrar como pendente de execução com GPU livre, não bloqueia a implementação nem a prova sem GPU).

---

## Critério binário de aceite (IA executora)

- [ ] No ramo parser-fail (`_core.py:493-515`), `self._should_reject_done()` é consultado ANTES de `add_assistant(final_content)`; quando devolve hint, o turno NÃO retorna DONE (marca `_done_rejected=True`, re-injeta o hint, `continue`)
- [ ] Rejeição 1x/turno: 2a passagem conclui DONE (sem laço); `MAX_ITERATIONS` intacto como rede
- [ ] Só dispara com `_turn_wants_action=True` e `_turn_tool_count==0` (ou `_turn_create_unmet`); com tool rodada, a prosa segue aceita como summary (passo 4)
- [ ] A prosa fabricada NÃO entra no histórico como resposta na iteração rejeitada (só o hint)
- [ ] Os dois caminhos que já consultam o guard (`_iteration.py:368`, `_iteration.py:535`) e o happy-path do parser ficam byte-idênticos
- [ ] `detect_forged_success`/`FORGE_PATTERNS` NÃO alterados; `_looks_like_raw_toolcall` NÃO alterado
- [ ] Proof runtime-real colado (passo 3): `llm_calls >= 2`, `_done_rejected True`, hint no histórico, ZERO prosa fabricada persistida como resposta
- [ ] `ruff` limpo, acentuação rc=0, `FAIL_AFTER <= FAIL_BEFORE`, smoke boot ok
- [ ] Gauntlet `--only rapido` DEFERIDO (executar com GPU exclusiva)
- [ ] NÃO commitar; NÃO tocar Checkpoint.md; NÃO tocar `_iteration.py`/`validator.py`/`intent.py`

---

## Guardrails anti-engodo (obrigatórios)

NÃO marcar concluída se:
- A consulta ao guard ficou DEPOIS de `add_assistant` (a ordem é o núcleo: rejeitar ANTES de aceitar o content).
- A rejeição não é 1x (laço infinito por não marcar `_done_rejected=True`, ou por reconsultar sem checar a flag).
- O guard passou a disparar com `_turn_tool_count>0` (regressão: sumária honesta de tool virou rejeição espúria).
- A prosa fabricada foi persistida como resposta na iteração rejeitada.
- O predicado `_should_reject_done` foi redefinido/duplicado em `_core.py` em vez de reusado do mixin.
- `detect_forged_success`/`FORGE_PATTERNS` foram "ampliados" para tapar o caso (não-objetivo: o guard 399 é o mecanismo correto, não o forge).
- Proof runtime-real não colado, ou `llm_calls` ficou em 1 (prosa aceita de primeira).

Se algo falhar: `[SPRINT 419] BLOQUEADA: <motivo 1 linha>`.

---

## Gambiarras específicas desta sprint

- **Guard no mixin, fix no núcleo:** `_should_reject_done` vive em `_iteration.py`; `_run_iterations` vive em `_core.py`. Funciona por herança (`AgentLoop(_IterationMixin)`); não criar import cruzado nem mover o método.
- **Canal de re-injeção:** `_force_reminder`/`_reminder_extra` já são usados neste mesmo bloco pela detecção de drift (`_core.py:475-476`) e consumidos por `_maybe_inject_reminder` (`_iteration.py:735-764`), que injeta mesmo com `count==0` quando `force=True`. Reusar esse canal evita fabricar um tool_call "done" sintético.
- **Descartar a prosa:** na iteração rejeitada NÃO chamar `add_assistant(content)` — persistir a alucinação como turno do assistente contamina o histórico. Só o hint entra (via reminder).
- **`_turn_tool_count` persiste entre iterações** (diferente de `_tool_calls_this_turn`, que reseta por iteração) — é o contador certo para "zero tools no turno inteiro".

---

## Riscos e não-objetivos

| Risco / não-objetivo | Decisão |
|-------|-----------|
| Ampliar `FORGE_PATTERNS` para casar "o conteúdo é ..." e outros relatos fabricados | **NÃO-OBJETIVO.** O forge só ANEXA aviso; o mecanismo correto para barrar a conclusão é o done-guard 399. Se o dono quiser enriquecer o forge, registrar sprint própria `VALIDATOR-FORGE-PATTERNS-WIDEN-01` (anti-débito, `feedback_nenhum_debito`). |
| Rejeitar mais de 1x (forçar a tool de verdade a qualquer custo) | Fora de escopo e arriscado (laço). O contrato 399 é 1x + `MAX_ITERATIONS`; manter. |
| Cobrir o caso "tool rodou mas o modelo mente na prosa" | Fora de escopo: com `_turn_tool_count>0` há dado cru; é o território de "apresentação forte" (G3), não deste guard. |
| Mexer nos caminhos 368/535 que já consultam o guard | Fora de escopo -- só o 3o caminho (parser-fail) é tocado. |

---

## Fora de escopo (anti-débito)

Achado único no briefing; nada agrupado. Se durante a execução aparecer um QUARTO caminho para `SessionState.DONE` sem guard, ou um caso de conclusão-por-prosa COM tool rodada porém mentirosa, NÃO absorver: registrar sprint nova com ID próprio no `SPRINT_ORDER_MASTER.md` (memória `feedback_nenhum_debito`).

---

## Referências

- BRIEF: `/home/andrefarias/Desenvolvimento/Nyx-Code/VALIDATOR_BRIEF.md`
- Desenho do contrato: `dev-journey/02-architecture/DESENHO_CONTRATO_EXECUCAO.md` (§6, "Honestidade na falha")
- Mecanismo estendido: 399 EXEC-CONTRACT-NO-HALLUCINATED-RESULT-01 (guard em `nyx/agent/loop/_iteration.py:261-276`, consumido em 368 e 535)
- Spec-irmã de referência estrutural: `dev-journey/06-sprints/producao/SPRINT_EXEC_CONTRACT_PROXY_STATUS_BEFORE_JSON_01.md`
- Origem: auditoria de prontidão 2026-07-12 (achado verificado adversarialmente com evidência file:line)

---

*"Uma resposta confiante, verossímil e falsa, sem nenhum indício de que nada foi lido, é o pior resultado possível para quem não tem como desconfiar." -- princípio de execução (DESENHO_CONTRATO_EXECUCAO.md §6)* <!-- noqa-acento -->
