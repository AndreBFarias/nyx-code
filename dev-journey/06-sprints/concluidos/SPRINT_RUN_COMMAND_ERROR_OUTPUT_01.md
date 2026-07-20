## 0. SPEC (machine-readable)

```yaml
sprint:
  id: RUN-COMMAND-ERROR-OUTPUT-01
  numero: 423
  title: "run_command com exit != 0 preserva stdout/stderr no error -- o 3b passa a ver o diagnostico e se autocorrige"
  onda: 48
  prioridade: ALTA
  tipo: Bugfix
  dependencias: []
  desbloqueia: []
  absorve: []
  relacionada: [382]

  touches:
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/agent/tools/run_command.py
      reason: "quando returncode != 0, anexar o output capturado (stdout + [stderr]) ao campo error, para que o consumidor do loop (que em falha grava so o error) leve o diagnostico ao histórico do LLM"
      linhas_alvo: "77-83 (bloco de return do caminho feliz/falha)"
  creates: []
  removes: []

  forbidden:
    - "Adicionar emoji"
    - "Usar 'print()' fora de cli.py/output.py"
    - "Mencao a ferramenta de IA"
    - "Tocar nyx/agent/loop/_iteration.py (o contrato do loop não muda -- ver Riscos)"
    - "Tocar o caminho feliz: success=True segue byte-identico (output[:8000] + hint, error vazio)"
    - "Tocar SUDO-MODE-01 (encapsulamento sudo, blacklist destrutiva, DANGER_PATTERNS)"
    - "Tocar os handlers de TimeoutExpired e Exception generico (84-87)"
    - "Alterar o cap de 120s do subprocess ou capture_output/text"

  tests:
    - cmd: "/home/andrefarias/.local/bin/ruff check nyx/agent/tools/run_command.py"
      deve_passar: true
    - cmd: "bash scripts/sprint_invariants.sh"
      deve_passar: true
    - cmd: "./run.sh --smoke"
      deve_passar: true
    - cmd: "./run.sh --gauntlet --only rapido"
      timeout: 300
      deve_passar: true
      nota: "DEFERIDO para GPU exclusiva (contencao) -- executar so com pgrep de Luna/valida_sprint vazio"

  acceptance_criteria:
    - "AC1: quando returncode != 0, ActionResult.error contem 'Exit code: N' E o output capturado (stdout + bloco [stderr]); o 3b passa a receber o stderr no histórico via _iteration.py:494 (result.error no ramo de falha)"
    - "AC2: caminho feliz intacto -- success=True devolve error vazio e output = output[:8000] + hint byte-identico ao atual; o hint 'chame done()' segue so no sucesso"
    - "AC3: falha sem saida nenhuma (stdout e stderr vazios) devolve error = 'Exit code: N\\n(sem saida)' -- nunca error vazio nem crash"
    - "AC4: proof runtime-real SEM GPU -- RunCommandTool().execute de um comando que falha (import de modulo inexistente) devolve success=False e error contendo 'ModuleNotFoundError'/'No module named'; ZERO diagnostico descartado"
    - "AC5: SUDO-MODE-01, TimeoutExpired e Exception generico intactos; ruff limpo, acentuacao rc=0, FAIL_AFTER <= FAIL_BEFORE, smoke boot ok"
```

---

# Sprint RUN-COMMAND-ERROR-OUTPUT-01 — run_command devolve o diagnostico da falha ao modelo

**Status:** PENDENTE
**Data criação:** 2026-07-12
**Modelo obrigatório:** claude-opus-4-7 (executor-sprint autorizado pelo dono nesta onda)

---

## Contexto do projeto (snapshot — não referência)

> **ADRs relevantes (inline):**
> - **ADR-032/033/034 A INFRA CARREGA O MODELO / ENFORCEMENT, NÃO CONFIANÇA:** robustez pertence à infraestrutura, não ao 3b. O Nyx-Code faz o pior LLM local (`qwen2.5-coder:3b`) na pior máquina parecer o Claude Code offline. Se a informação de diagnóstico existe e a infra a descarta, é falha de infra, não teto de modelo. <!-- noqa-anonimato -->
> - ADR-009, ADR-001, ADR-006.
>
> **Estado (2026-07-12):** `qwen2.5-coder:3b`. ONDA-48 fase raiz: núcleo do contrato (399/397/400/398/401) CONCLUIDO. Este é achado da auditoria de prontidão 2026-07-12 (verificado adversarialmente, evidência file:line). Usuário-alvo: leigo, sem hardware bom, precisa que a Nyx se autocorrija sozinha quando um comando quebra.

---

## Problema

**Achado (auditoria 2026-07-12, severidade ALTA):** quando um comando de shell falha (`exit != 0` — teste quebrado, import ausente, typo), o `run_command` captura `stdout` e `stderr`, mas devolve ao modelo **apenas** a string `"Exit code: N"`. Todo o diagnóstico (a mensagem de erro que diria ao 3b **o que** consertar) é jogado fora pela própria infra.

O 3b, o pior modelo, fica sem nenhuma pista para se autocorrigir. Isso fere a promessa central "a infraestrutura compensa o modelo" (ADR-032/033): a informação existia, o `subprocess` a capturou, e o código a descartou.

## Causa-raiz (verificada no código real)

Ancoras reconferidas em 2026-07-12 — as linhas do briefing bateram com o código atual.

`nyx/agent/tools/run_command.py`, método `execute`:

- **linhas 73-75:** o `stderr` é concatenado em `output`:
  ```python
  output = result.stdout
  if result.stderr:
      output += f"\n[stderr]\n{result.stderr}"
  ```
- **linhas 77-83:** no return, o `output` (com stdout + stderr) só é usado no campo `output`; o campo `error` recebe apenas `"Exit code: N"`:
  ```python
  ok = result.returncode == 0
  hint = " Se a tarefa está completa, chame done()." if ok else ""
  return ActionResult(
      success=ok,
      output=(output[:8000] if output else "(sem saída)") + hint,
      error=f"Exit code: {result.returncode}" if not ok else "",
  )
  ```

**O consumidor descarta o `output` quando a tool falha.** `nyx/agent/loop/_iteration.py:491-496` grava no histórico do LLM:
```python
self._session.add_tool_call(
    name,
    args,
    result.output if result.success else result.error,   # <- linha 494
    is_key=name in ("write_file", "edit_file", "create_file", "run_command"),
)
```
O mesmo padrão `result.output if result.success else result.error` aparece em **6 sítios** do loop (474 hook PostToolUse, 489 on_tool_result/TUI, 494 add_tool_call, 502 _gsd.tool, 640 e 648 em outro ramo de execução). Em **todos**, o ramo de falha usa **só** o `error`. Como o `error` do `run_command` é `"Exit code: 2"`, o que volta ao 3b (e à TUI, e ao progress.md) é literalmente `Exit code: 2` — zero stderr.

**Divergência do briefing (registrada):** o briefing sugeriu, como alternativa "melhor", mudar o contrato do loop para anexar `output+error` no `add_tool_call`. **Rejeitado por escopo:** o padrão vive em 6 sítios do `_iteration.py`; mudá-lo é largo e arriscado (afeta toda tool que falha), e não há evidência de uma segunda tool com o mesmo sintoma. O fix cirúrgico é local ao `run_command`: fazer o `error` carregar o diagnóstico, respeitando o contrato do loop intacto. A generalização fica registrada em "Fora de escopo (anti-débito)".

**Relação com a sprint 382 LOOP-TOOL-RESULT-FIDELITY-01 (DEFERIDA):** a 382 foi deferida como "capacidade do modelo" (ADR-034: o 3b alucina o resultado da tool). Este achado mostra que **parte era INFRA** — o stderr era descartado antes mesmo de o modelo poder lê-lo. Esta sprint absorve **só a parte de infra** (devolver o diagnóstico). A 382 segue DEFERIDA para a parte de capacidade (o 3b ainda pode alucinar sobre o resultado mesmo com o stderr presente).

---

## Solução proposta

Uma única correção cirúrgica em `run_command.py`, no bloco de return (77-83): quando `not ok`, embutir o `output` capturado (stdout + `[stderr]`) no campo `error`, para que o ramo de falha do loop leve o diagnóstico ao histórico do 3b.

O caminho feliz (`ok == True`) fica byte-idêntico: `error` vazio, `output` com `[:8000] + hint`.

**Head vs tail (divergência deliberada do briefing):** o briefing sugeriu `output[:2000]` (início). Esta spec usa a **cauda** `output[-4000:]`: em falhas reais o erro operativo fica quase sempre **no fim** — a última linha de um traceback Python é a exceção, o sumário do pytest fica ao final, o `ModuleNotFoundError` é a última linha. A cauda entrega ao 3b a linha que importa. O cap de 4000 caracteres protege a janela de contexto minúscula do 3b sem cortar o essencial.

---

## Arquivos alvo (paths absolutos)

### `/home/andrefarias/Desenvolvimento/Nyx-Code/nyx/agent/tools/run_command.py`

#### Edit único — anexar o diagnóstico ao `error` no ramo de falha

# Localização: bloco de return dentro do `try:` de `execute` (linhas 77-83)
**Antes:**
```python
            ok = result.returncode == 0
            hint = " Se a tarefa está completa, chame done()." if ok else ""
            return ActionResult(
                success=ok,
                output=(output[:8000] if output else "(sem saída)") + hint,
                error=f"Exit code: {result.returncode}" if not ok else "",
            )
```
**Depois:**
```python
            ok = result.returncode == 0
            hint = " Se a tarefa está completa, chame done()." if ok else ""
            # RUN-COMMAND-ERROR-OUTPUT-01: em falha o consumidor do loop grava
            # so o `error` (result.output if success else result.error, em 6
            # sitios de _iteration.py). Antes o error era so "Exit code: N" e o
            # stdout/stderr capturado era descartado -- o 3b não via o
            # diagnostico e não tinha como se autocorrigir (fere ADR-032/033: a
            # infra tinha a informação e a jogou fora). Anexamos a CAUDA do
            # output (onde vive o erro operativo: última linha do traceback,
            # sumario do pytest), capada em 4000 para não estourar a janela do 3b.
            diag = output if output else "(sem saída)"
            return ActionResult(
                success=ok,
                output=(output[:8000] if output else "(sem saída)") + hint,
                error=(
                    f"Exit code: {result.returncode}\n{diag[-4000:]}"
                    if not ok
                    else ""
                ),
            )
```

---

## Diff esperado (resumo)

```
~ 1 arquivo modificado (nyx/agent/tools/run_command.py)
+ ~10 linhas líquidas (comentário + expressão do error; sem meta numérica de tamanho)
```

Sem aritmética de extração: esta sprint não tem meta `arquivo < NNNL`. O único número relevante é o net-add (~10L) num único arquivo, que segue muito abaixo de qualquer limite.

---

## Comandos de verificação (literais, copy-paste)

```bash
cd /home/andrefarias/Desenvolvimento/Nyx-Code

# 1. Estatica + acentuacao (ruff via binario direto -- não ha modulo ruff no venv, ver BRIEF)
/home/andrefarias/.local/bin/ruff check nyx/agent/tools/run_command.py
python3 ~/.config/zsh/scripts/validar-acentuacao.py --paths nyx/agent/tools/run_command.py

# 2. Confirmar as ancoras (linhas podem ter deslizado -- reconferir):
rg -n "Exit code|result.returncode|\[stderr\]|success=ok" nyx/agent/tools/run_command.py

# 3. PROOF RUNTIME-REAL sem GPU (a tool roda subprocess real, não toca Ollama).
#    Comando que falha por import ausente -> o error deve carregar o stderr.
./venv/bin/python - <<'PY'
from nyx.agent.tools.run_command import RunCommandTool

t = RunCommandTool()

# 3a. Falha: import de modulo inexistente -> stderr no error
res = t.execute({"command": "python3 -c 'import __modulo_que_nao_existe__'"}, ".")
print("success :", res.success)
print("error   :", repr(res.error[:300]))
assert res.success is False, res
assert "Exit code:" in res.error, res
assert ("ModuleNotFoundError" in res.error) or ("No module named" in res.error), res
print("OK 3a: stderr preservado no error (o 3b ve o diagnostico)")

# 3b. Caminho feliz intacto: success=True, error vazio, sem stderr no error
ok = t.execute({"command": "echo ola"}, ".")
assert ok.success is True, ok
assert ok.error == "", ok
assert "ola" in ok.output, ok
print("OK 3b: caminho feliz byte-identico (error vazio)")

# 3c. Falha sem saida nenhuma -> '(sem saida)' no error, nunca vazio/crash
q = t.execute({"command": "exit 3"}, ".")
assert q.success is False, q
assert "Exit code: 3" in q.error, q
print("OK 3c: falha silenciosa -> error com Exit code + (sem saida)")
print("error 3c:", repr(q.error))
PY

# 4. Confirmar que o consumidor do loop leva o error ao histórico (leitura, não exec):
rg -n "result.output if result.success else result.error" nyx/agent/loop/_iteration.py

# 5. Smoke boot (obrigatorio antes de CONCLUIDA -- feedback_smoke_boot):
./run.sh --smoke   # deve imprimir 'boot ok'

# 6. Gauntlet rapido (DEFERIDO p/ GPU exclusiva -- so com pgrep Luna/valida_sprint vazio):
./run.sh --gauntlet --only rapido
```

> Nota GPU: os passos 3 e 4 rodam SEM Ollama/GPU (a tool executa um subprocess local; o passo 4 é só `rg`). O passo 6 (gauntlet) exige GPU exclusiva e fica **DEFERIDO** — executar só quando `pgrep -af "Luna.*driver|valida_sprint"` estiver vazio (protocolo anti-contenção do BRIEF), tal como as specs 403/407.

---

## Critério binário de aceite (IA executora)

- [ ] AC1: em `returncode != 0`, `ActionResult.error` contém `Exit code: N` E o output capturado (stdout + `[stderr]`)
- [ ] AC2: caminho feliz byte-idêntico — `success=True` -> `error == ""`, `output == output[:8000] + hint`
- [ ] AC3: falha sem saída -> `error` = `"Exit code: N\n(sem saída)"`, nunca vazio nem crash
- [ ] AC4: proof runtime-real colado (passo 3): 3a/3b/3c passam, stderr presente no error, ZERO descarte
- [ ] AC5: SUDO-MODE-01, `TimeoutExpired` (85) e `Exception` genérico (86-87) intactos
- [ ] `ruff` limpo, acentuação rc=0, `FAIL_AFTER <= FAIL_BEFORE`, smoke boot `boot ok`
- [ ] `_iteration.py` NÃO tocado (o contrato do loop fica intacto — ver Riscos)
- [ ] `SPRINT_ORDER_MASTER.md` marca 423 CONCLUIDA; spec movida para `concluidos/` (integração é do orquestrador, não desta execução)
- [ ] NÃO commitar; NÃO tocar Checkpoint.md

---

## Guardrails anti-engodo (obrigatórios)

NÃO marcar concluída se:
- O `error` no ramo de falha continuar sendo só `"Exit code: N"` (o núcleo do fix é o diagnóstico voltar ao modelo).
- O caminho feliz mudou (`success=True` deve seguir com `error == ""` e o `hint` presente só no sucesso).
- Tocou `nyx/agent/loop/_iteration.py` (a generalização do contrato do loop é não-objetivo — ver Riscos).
- Tocou SUDO-MODE-01, a blacklist destrutiva, o `TimeoutExpired` ou o `Exception` genérico.
- Proof runtime-real não colado, ou algum dos asserts (3a/3b/3c) falhou.
- Removeu o cap de segurança do `error` (o `[-4000:]` protege a janela do 3b; sem cap, um comando verboso pode saturar o contexto).

Se algo falhar: `[SPRINT 423] BLOQUEADA: <motivo 1 linha>`.

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
Baseline esperado: `FAIL_BEFORE = 0`, `FAIL_AFTER <= 0`. Colar: inv_before/inv_after (tail), diff, o output do proof runtime-real (passo 3, 3a/3b/3c OK), o `rg` do passo 4, `git --no-pager diff --stat` e `./run.sh --smoke` (deve imprimir `boot ok`). O gauntlet (passo 6) fica DEFERIDO para GPU exclusiva.

---

## Gambiarras específicas desta sprint

- **Cauda `[-4000:]` em vez de head:** o erro operativo vive no fim do output (última linha do traceback, sumário do pytest). Head cortaria justamente a linha que o 3b precisa. Cap 4000 protege o contexto minúsculo do 3b.
- **`output` e `error` ambos com o diagnóstico:** o campo `output` segue populado (para consumidores que leem output mesmo em falha, ex.: `post_validate`), e o `error` agora também o carrega. Não há duplicação no histórico do LLM porque o loop usa **um OU outro** (`result.output if success else result.error`), nunca ambos na mesma entrada.
- **`session.compress()` corta em `[:200]`:** entradas antigas do histórico são comprimidas para `tool_result[:200]` (`nyx/agent/session.py:26`). Isso é esperado e NÃO bloqueia: a entrada mais recente (a que dispara a autocorreção na próxima iteração) mantém o `error` completo; a compressão só atinge entradas já antigas. Fora de escopo mexer nisso.
- **`(sem saída)` com acento:** manter o literal exatamente `"(sem saída)"` (com `í`) — é o mesmo literal já usado no campo `output`, não introduzir variante ASCII.

---

## Validação humana (checklist do usuário)

```bash
cd /home/andrefarias/Desenvolvimento/Nyx-Code
git --no-pager show --stat HEAD

# Com o stack real (GPU exclusiva), pedir à Nyx: "rode os testes" num repo com
# um teste quebrado de proposito. A Nyx deve VER o traceback do pytest e tentar
# consertar -- não apenas dizer "o comando falhou com Exit code 1" e parar.

ls dev-journey/06-sprints/concluidos/SPRINT_RUN_COMMAND_ERROR_OUTPUT_01.md  # apos integração
```

---

## Fora de escopo (anti-débito)

| Item | Decisão |
|-------|-----------|
| Generalizar o contrato do loop (anexar `output+error` no `add_tool_call` quando ambos existem, nos 6 sítios de `_iteration.py`) | **NÃO-OBJETIVO.** Largo e arriscado (afeta toda tool que falha), sem evidência de uma segunda tool com o sintoma. Se outra tool vier a descartar diagnóstico em falha, abrir sprint própria `LOOP-TOOL-RESULT-DIAG-CONTRACT-01` (`feedback_nenhum_debito`), não absorver aqui. |
| Parte de capacidade da 382 (o 3b alucina o resultado da tool mesmo com o stderr presente) | Segue DEFERIDA como ADR-034 (teto de modelo). Esta sprint cobre só a metade de INFRA (devolver o diagnóstico). |
| Hardening do proxy / streaming de output grande | Fora de escopo — o fix é local à tool. |

---

## Riscos e não-objetivos

| Risco / não-objetivo | Decisão |
|-------|-----------|
| Mudar o contrato do loop (`_iteration.py`) | **NÃO-OBJETIVO.** O fix é local ao `run_command`; o loop fica intacto. |
| `error` muito grande satura o contexto do 3b | Capado em `[-4000:]`; a cauda entrega o erro operativo sem despejar o output inteiro. |
| Duplicação output/error no histórico | Impossível: o loop usa um OU outro por entrada, nunca ambos. |
| Regressão no caminho feliz | AC2 + proof 3b garantem byte-identidade (`error == ""`, hint só no sucesso). |

---

## Referências

- BRIEF: `/home/andrefarias/Desenvolvimento/Nyx-Code/VALIDATOR_BRIEF.md`
- Achado: auditoria de prontidão 2026-07-12 (briefing `423_RUN-COMMAND-ERROR-OUTPUT-01`)
- Evidência: `nyx/agent/tools/run_command.py:73-83`; consumidor `nyx/agent/loop/_iteration.py:474/489/494/502/640/648`
- Sprint relacionada: 382 LOOP-TOOL-RESULT-FIDELITY-01 (DEFERIDA — esta absorve só a parte de INFRA)
- Estrutura-modelo: `dev-journey/06-sprints/producao/SPRINT_EXEC_CONTRACT_PROXY_STATUS_BEFORE_JSON_01.md`

---

*"A infra tinha a mensagem de erro nas mãos e a jogou fora antes de o modelo ler. Robustez pertence à infra, não ao 3b." -- ADR-032/033.*
