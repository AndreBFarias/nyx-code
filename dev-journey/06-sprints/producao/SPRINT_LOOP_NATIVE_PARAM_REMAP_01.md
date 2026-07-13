## 0. SPEC (machine-readable)

```yaml
sprint:
  id: LOOP-NATIVE-PARAM-REMAP-01
  numero: 422
  title: "Caminho nativo de tool_calls aplica PARAM_REMAP e alias create_file->write_file (paridade com o parser fallback)"
  onda: 48
  prioridade: ALTA
  tipo: Bugfix
  dependencias: []
  desbloqueia: []
  absorve: []

  touches:
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/agent/loop/_iteration.py
      reason: "no caminho nativo _execute_tool_calls, aplicar o alias de nome (create_file->write_file) e _remap_params(name, args) logo apos sanitize_tool_args -- a mesma compensacao que o parser fallback ja faz nas linhas 550/564"
      linhas_alvo: "329-334 (leitura do name + sanitize no topo do loop nativo)"
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/agent/loop/_constants.py
      reason: "fonte unica do alias de nome nativo (NATIVE_TOOL_ALIAS = {'create_file': 'write_file'}), ao lado de ACTION_TO_TOOL/PARAM_REMAP -- sem ciclo de import"
      linhas_alvo: "26-36 (bloco ACTION_TO_TOOL / PARAM_REMAP)"
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/agent/tools/base.py
      reason: "mensagem honesta: trocar 'Path vazio' cru por texto que nomeia a convencao de parametro esperada (file_path vs path), para o 3b se corrigir no caso residual (tools sem entrada em PARAM_REMAP / MCP)"
      linhas_alvo: "175-176 (raise ValueError('Path vazio') em validate_path)"
  creates: []
  removes: []

  forbidden:
    - "Adicionar emoji"
    - "Usar 'print()' fora de cli.py/output.py"
    - "Mencao a ferramenta de IA proprietaria"
    - "Tocar o caminho do parser fallback (_execute_parsed_action, linhas 528-600) -- ele ja aplica remap/alias e fica byte-identico"
    - "Tocar os guards do contrato de execução (397/398/399/400/401): tool-match, seq-edit, echo-reject, done, preflight"
    - "Tocar PARAM_REMAP em si (a tabela ja existe e esta correta -- so passa a ser aplicada no caminho nativo)"
    - "Registrar create_file como tool real no registry -- a decisao e ALIAS para write_file, identica a ACTION_TO_TOOL[CREATE_FILE]"
    - "Remover create_file do system prompt (prompt.py:147) -- o alias torna o nome anunciado de fato funcional; mexer no prompt e não-objetivo"
    - "Alterar a semantica de sanitize_tool_args / _remap_params (funções puras, reuso sem copia nova)"

  tests:
    - cmd: "/home/andrefarias/.local/bin/ruff check nyx/agent/loop/_iteration.py nyx/agent/loop/_constants.py nyx/agent/tools/base.py"
      deve_passar: true
    - cmd: "python3 ~/.config/zsh/scripts/validar-acentuacao.py --paths nyx/agent/loop/_iteration.py nyx/agent/loop/_constants.py nyx/agent/tools/base.py"
      deve_passar: true
    - cmd: "bash scripts/sprint_invariants.sh"
      deve_passar: true
    - cmd: "./run.sh --gauntlet --only rapido"
      timeout: 300
      deve_passar: true
      nota: "DEFERIDO para GPU exclusiva -- exige inferencia real; rodar so com pgrep de contencao vazio"

  acceptance_criteria:
    - "AC1 (PARAM_REMAP no caminho nativo): tool_call nativo read_file{'path':'x'} chega a tool com {'file_path':'x'} -- _remap_params(name, args) roda em _execute_tool_calls logo apos sanitize_tool_args, exatamente como no parser fallback (linha 564). O erro 'Path vazio' por nome de parametro trocado deixa de ocorrer no caminho principal (proxy/nativo)."
    - "AC2 (alias create_file->write_file no caminho nativo): tool_call nativo create_file{...} e roteado para write_file ANTES de preflight/permissao/execute, via NATIVE_TOOL_ALIAS. O erro 'Tool desconhecida: create_file' (registry.py:223) deixa de ocorrer no caminho nativo; o nome que o próprio system prompt ensina (prompt.py:147) passa a funcionar."
    - "AC3 (mensagem honesta residual): validate_path (base.py) troca o 'Path vazio' cru por mensagem que nomeia a convencao de parametro esperada (file_path para read/edit/write/patch/analyze; path para search/glob/list_files), de modo que o caso residual (tool sem entrada em PARAM_REMAP, MCP) ensine o 3b o nome certo em vez de mentir que o path veio vazio."
    - "AC4 (paridade, não regressao): o parser fallback (_execute_parsed_action) segue byte-identico -- a mudanca so acrescenta ao caminho nativo o que o parser ja fazia. Guards do contrato (tool-match/seq-edit/echo/done/preflight/permissao) rodam sobre o name ja aliassado e os args ja remapeados, sem quebra."
    - "Proof runtime-real SEM GPU (transporte/inferencia faked): _execute_tool_calls real recebe read_file{'path':...} e o _tools.execute capturado ve name='read_file' + args com 'file_path' (sem 'path'); recebe create_file{...} e o _tools.execute capturado ve name='write_file', ZERO 'Tool desconhecida'."
    - "ruff limpo, acentuacao rc=0, invariantes FAIL_AFTER <= FAIL_BEFORE, smoke boot ok. Gauntlet DEFERIDO para GPU exclusiva."
```

---

# Sprint LOOP-NATIVE-PARAM-REMAP-01 — Caminho nativo de tool_calls ganha PARAM_REMAP e alias create_file->write_file

**Status:** PENDENTE
**Data criação:** 2026-07-12
**Modelo obrigatório:** claude-opus-4-7 (executor-sprint autorizado pelo dono nesta onda)

---

## Contexto do projeto (snapshot — não referência)

> **ADRs relevantes (inline):**
> - **ADR-032/033/034 — A INFRA CARREGA O MODELO / ENFORCEMENT, NÃO CONFIANÇA:** o Nyx-Code faz o pior LLM local (qwen 3b) na pior máquina parecer o Claude Code offline. Robustez pertence à INFRA, não ao modelo. Quando o 3b comete um erro de formato previsível, a infra corrige a estrutura de forma determinística — não confia que o modelo acerte, nem devolve um erro cru que ele não sabe consertar. <!-- noqa-anonimato -->
> - ADR-026 (nada silencioso), ADR-009, ADR-001.
>
> **Estado (2026-07-12):** `qwen2.5-coder:3b`. ONDA-48 fase raiz: núcleo do contrato (399/397/400/398/401) CONCLUIDO. Achado da auditoria de prontidão 2026-07-12 (verificado adversarialmente, evidência file:line). O caminho principal de tool_calls (nativo, via proxy) NÃO aplica a compensação de formato que o parser fallback já aplica. Ports: Ollama `11435`, proxy `11436` (`nyx/config/defaults.py`).

---

## Problema

O usuário-alvo é leigo, sem hardware bom, rodando o pior modelo local. O 3b comete um erro de formato clássico e previsível: usa `path` onde a tool espera `file_path`, ou chama `create_file` — nome que o **próprio** system prompt ensina (`nyx/agent/prompt.py:147`: `write_file, edit_file, create_file, multi_edit ou patch`).

A infra tem exatamente a compensação para isso:
- `PARAM_REMAP` (`nyx/agent/loop/_constants.py:28-36`) renomeia `path` para `file_path` por tool;
- `ACTION_TO_TOOL[ActionType.CREATE_FILE] = "write_file"` (`_constants.py:11`) mapeia o alias no caminho do parser.

**Mas essa compensação só roda no caminho do parser fallback**, não no caminho nativo (o principal, alimentado pelos `tool_calls` estruturados do proxy).

**Caminho do parser (compensa — verificado):** `nyx/agent/loop/_iteration.py`, `_execute_parsed_action`:
- linha 550: `tool_name = ACTION_TO_TOOL.get(action.action_type)` — resolve `CREATE_FILE` para `write_file`;
- linha 564: `remapped = _remap_params(tool_name, action.params)` — renomeia `path` para `file_path`.

**Caminho nativo (NÃO compensa — verificado):** `nyx/agent/loop/_iteration.py`, `_execute_tool_calls`:
- linha 329: `name = tc["name"]` — o nome cru do modelo (`create_file` chega como `create_file`);
- linha 334: `args = sanitize_tool_args(name, tc["arguments"])` — `sanitize` limpa crases/aspas/escapes do **valor** dos paths (`sanitize.py:35-52`, itera sobre `_PATH_KEYS = ("file_path","path")`), mas **NÃO renomeia chaves**;
- não há `_remap_params` nem alias de nome antes do `execute` (linha 462: `result = await asyncio.to_thread(self._tools.execute, name, args)`).

**Consequência 1 — "Path vazio" mentiroso:** `read_file{"path":"x.py"}` nativo → `nyx/agent/tools/read_file.py:32` `params.get("file_path", "")` devolve string vazia (a chave era `path`) → `nyx/agent/tools/base.py:176` `raise ValueError("Path vazio")`. O erro é mentiroso: o path veio preenchido; o **nome do parâmetro** é que era outro. O 3b não tem como se corrigir.

**Consequência 2 — "Tool desconhecida":** `create_file{...}` nativo → `nyx/agent/tools/registry.py:223` `error=f"Tool desconhecida: {tool_name}"`. O modelo usou o nome que o próprio prompt anunciou, e a infra o rejeita sem dizer qual é o nome correto.

Agrava: os nomes de parâmetro são inconsistentes entre tools (read/edit/write/patch/analyze usam `file_path`; search/glob/list_files usam `path`; notebook_edit usa `notebook_path`), e a docstring do parser (`nyx/agent/parser.py:246`) mostra `{"name":"read_file","arguments":{"path":"..."}}` como formato aceito — reforçando o `path` que a tool nativa rejeita.

Isso fere **ADR-032/033**: a infra que existe para compensar o 3b (PARAM_REMAP/alias) não roda no caminho principal, e as mensagens de erro não ensinam o nome certo.

---

## Solução proposta

Levar ao caminho nativo a **mesma** compensação que o parser fallback já faz — aditiva e cirúrgica, sem tocar o parser nem os guards do contrato:

1. **Alias de nome no caminho nativo** — logo após ler `name = tc["name"]`, resolver `create_file` para `write_file` via `NATIVE_TOOL_ALIAS` (fonte única em `_constants.py`, ao lado de `ACTION_TO_TOOL`). Aplicar o alias **antes** de tudo (sanitize, remap, preflight, permissão, execute) garante que todos os passos e os guards vejam o nome canônico — idêntico ao que `ACTION_TO_TOOL[CREATE_FILE]` faz no parser.
2. **`_remap_params` no caminho nativo** — logo após `sanitize_tool_args`, aplicar `args = _remap_params(name, args)` (função já importada, `_iteration.py:30`) para renomear `path` para `file_path` conforme a tool. Isso espelha `_execute_parsed_action:564`.
3. **Mensagem honesta residual em `validate_path`** — trocar o `"Path vazio"` cru por texto que nomeia a convenção de parâmetro esperada, para o caso residual (tool sem entrada em `PARAM_REMAP` ou MCP) ensinar o 3b em vez de mentir.

O alias deve ser aplicado a `name` **antes** de `_remap_params(name, args)`, para que `create_file` (aliassado para `write_file`) receba o remap de `write_file`.

---

## Arquivos alvo (paths absolutos)

### `/home/andrefarias/Desenvolvimento/Nyx-Code/nyx/agent/loop/_constants.py`

#### Edit A — fonte única do alias de nome nativo

# Localização: logo após o dicionário `PARAM_REMAP` (linha 36), antes de `_remap_params`
**Adicionar:**
```python
# LOOP-NATIVE-PARAM-REMAP-01: alias de NOME de tool para o caminho nativo de
# tool_calls (paridade com ACTION_TO_TOOL[CREATE_FILE] no parser fallback). O
# system prompt ensina 'create_file' (prompt.py:147), mas o registry so tem
# 'write_file' -- a infra resolve o alias antes do execute, não confia que o 3b
# use o nome canônico (ADR-032). Fonte unica aqui (sem ciclo de import).
NATIVE_TOOL_ALIAS: dict[str, str] = {"create_file": "write_file"}
```

### `/home/andrefarias/Desenvolvimento/Nyx-Code/nyx/agent/loop/_iteration.py`

#### Edit B — importar o alias

# Localização: bloco de import de `_constants` (linhas 24-31)
**Antes:**
```python
from nyx.agent.loop._constants import (
    ACTION_TO_TOOL,
    CORE_TOOLS,
    LLM_TIMEOUT,
    PRESENTABLE_TOOLS,
    TOOL_KEYWORDS,
    _remap_params,
)
```
**Depois:**
```python
from nyx.agent.loop._constants import (
    ACTION_TO_TOOL,
    CORE_TOOLS,
    LLM_TIMEOUT,
    NATIVE_TOOL_ALIAS,
    PRESENTABLE_TOOLS,
    TOOL_KEYWORDS,
    _remap_params,
)
```

#### Edit C — alias + remap no topo do loop nativo

# Localização: início do `for tc in tool_calls:` em `_execute_tool_calls` (linhas 328-334)
**Antes:**
```python
        for tc in tool_calls:
            name = tc["name"]
            # EXEC-CONTRACT-TOOLCALL-SANITIZE-01 (G1, V02/C1): limpa lixo de markdown
            # (crase/aspas/escape `\/`) dos args path-like ANTES de tudo (on_tool,
            # permission, preflight, execute veem o arg ja limpo). Estrutura, não
            # semantica -- a infra corrige o 3b sem adivinhar intencao (ADR-032).
            args = sanitize_tool_args(name, tc["arguments"])
```
**Depois:**
```python
        for tc in tool_calls:
            name = tc["name"]
            # LOOP-NATIVE-PARAM-REMAP-01: alias de NOME antes de tudo -- o 3b usa
            # 'create_file' (nome que o próprio prompt ensina, prompt.py:147), mas
            # o registry so tem 'write_file'. Resolver aqui faz sanitize/remap/
            # preflight/permissao/execute e os guards verem o nome canônico, igual
            # ao que ACTION_TO_TOOL[CREATE_FILE] faz no parser fallback (ADR-032).
            name = NATIVE_TOOL_ALIAS.get(name, name)
            # EXEC-CONTRACT-TOOLCALL-SANITIZE-01 (G1, V02/C1): limpa lixo de markdown
            # (crase/aspas/escape `\/`) dos args path-like ANTES de tudo (on_tool,
            # permission, preflight, execute veem o arg ja limpo). Estrutura, não
            # semantica -- a infra corrige o 3b sem adivinhar intencao (ADR-032).
            args = sanitize_tool_args(name, tc["arguments"])
            # LOOP-NATIVE-PARAM-REMAP-01: renomeia as CHAVES de parametro
            # ('path' -> 'file_path' etc.) conforme a tool -- paridade com o
            # parser fallback (_execute_parsed_action:564). Sem isto, o caminho
            # nativo (o principal, via proxy) entregava read_file{'path':...} a
            # tool que le 'file_path' -> 'Path vazio' mentiroso (base.py:176).
            args = _remap_params(name, args)
```

### `/home/andrefarias/Desenvolvimento/Nyx-Code/nyx/agent/tools/base.py`

#### Edit D — mensagem honesta no caso residual

# Localização: `validate_path`, o `raise ValueError("Path vazio")` (linhas 175-176)
**Antes:**
```python
    if not file_path or not file_path.strip():
        raise ValueError("Path vazio")
```
**Depois:**
```python
    if not file_path or not file_path.strip():
        # LOOP-NATIVE-PARAM-REMAP-01: o caso comum (chave 'path' onde a tool le
        # 'file_path') ja e corrigido pelo remap no loop; esta mensagem cobre o
        # residual (tool sem entrada em PARAM_REMAP / MCP) e ENSINA o nome certo
        # em vez de mentir que o caminho veio vazio (ADR-032, honestidade).
        raise ValueError(
            "Caminho sem valor: confira o nome do parametro esperado pela tool "
            "(file_path para read/edit/write/patch/analyze; path para "
            "search/glob/list_files)."
        )
```

---

## Diff esperado (resumo)

```
~ 3 arquivos modificados:
  nyx/agent/loop/_constants.py   (+ ~7L: NATIVE_TOOL_ALIAS + comentario)
  nyx/agent/loop/_iteration.py   (+ ~13L: import + alias + remap no loop nativo)
  nyx/agent/tools/base.py        (~ 1 raise trocado por mensagem que ensina, +5L)
+ ~25 linhas líquidas, fix aditivo. Nenhum arquivo cruza limite de tamanho.
```

Sem aritmética de extração: esta sprint não tem meta `arquivo < NNNL`. O único número relevante é o net-add (~25L) em 3 arquivos; nenhuma remoção de comportamento.

---

## Comandos de verificação (literais, copy-paste)

```bash
cd /home/andrefarias/Desenvolvimento/Nyx-Code

# 1. Estatica + acentuacao (ruff via binario direto -- não ha modulo ruff no venv, ver BRIEF)
/home/andrefarias/.local/bin/ruff check nyx/agent/loop/_iteration.py nyx/agent/loop/_constants.py nyx/agent/tools/base.py
python3 ~/.config/zsh/scripts/validar-acentuacao.py --paths nyx/agent/loop/_iteration.py nyx/agent/loop/_constants.py nyx/agent/tools/base.py

# 2. Reconferir as ancoras (linhas podem ter deslizado -- verificar hipotese, licao 4):
rg -n "name = tc\[.name.\]|sanitize_tool_args\(name|_remap_params\(name|NATIVE_TOOL_ALIAS" nyx/agent/loop/_iteration.py
rg -n "NATIVE_TOOL_ALIAS|PARAM_REMAP|ACTION_TO_TOOL\[|CREATE_FILE" nyx/agent/loop/_constants.py
rg -n "Path vazio|Caminho sem valor|file_path para read" nyx/agent/tools/base.py

# 3. PROOF RUNTIME-REAL sem GPU (transporte/inferencia faked). AgentLoop real,
#    _execute_tool_calls real -- so o _tools.execute e capturado. _vram_checked
#    pula o guard de VRAM (sem GPU nesta prova). Permissao forcada a ALLOW.
./venv/bin/python - <<'PY'
import asyncio
from nyx.agent.loop._core import AgentLoop
from nyx.agent.models import ActionResult
from nyx.agent.permissions import PermissionLevel

captured = []

def fake_execute(name, args):
    captured.append((name, dict(args)))
    return ActionResult(success=True, output="OK", error="")

loop = AgentLoop(project_root=".")
loop._vram_checked = True
loop._tools.execute = fake_execute            # captura o que chega ao registry
loop._permissions.check = lambda *a, **k: PermissionLevel.ALLOW
loop._on_permission = None

# AC1: read_file{'path': ...} nativo -> tool recebe file_path (remap aplicado)
captured.clear()
asyncio.run(loop._execute_tool_calls(
    [{"name": "read_file", "arguments": {"path": "README.md"}}], 1))
name, args = captured[-1]
assert name == "read_file", name
assert "file_path" in args and args["file_path"] == "README.md", args
assert "path" not in args, args
print("AC1 OK: read_file{'path'} -> tool ve file_path (sem 'path'):", args)

# AC2: create_file{...} nativo -> aliassado para write_file (sem 'Tool desconhecida')
captured.clear()
asyncio.run(loop._execute_tool_calls(
    [{"name": "create_file", "arguments": {"path": "/tmp/nyx_remap_probe.txt",
                                           "content": "oi"}}], 1))
name, args = captured[-1]
assert name == "write_file", name
assert "file_path" in args, args
print("AC2 OK: create_file -> write_file, args:", args)
print("OK: caminho nativo aplica PARAM_REMAP + alias (paridade com o parser)")
PY

# 4. Confirmar que o parser fallback segue intacto (AC4 -- não regressao):
rg -n "_remap_params\(tool_name, action.params\)|ACTION_TO_TOOL.get\(action.action_type\)" nyx/agent/loop/_iteration.py

# 5. Invariantes (14 checks) + smoke boot
bash scripts/sprint_invariants.sh
./run.sh --smoke   # deve imprimir 'boot ok' e exit 0

# 6. Gauntlet -- DEFERIDO para GPU exclusiva (exige inferencia real):
#    ./run.sh --gauntlet --only rapido   # rodar so com contencao vazia:
#    pgrep -af "Luna.*driver|valida_sprint" deve estar vazio (protocolo anti-contencao do BRIEF)
```

> Nota GPU: o passo 3 roda SEM Ollama/GPU (transporte/inferência faked; só `_execute_tool_calls` e o registry reais). O passo 6 (gauntlet) exige GPU exclusiva e fica **DEFERIDO** — executar só quando `pgrep -af "Luna.*driver|valida_sprint"` estiver vazio (como as specs 403/407 fazem).

---

## Critério binário de aceite (IA executora)

- [ ] `NATIVE_TOOL_ALIAS = {"create_file": "write_file"}` criado em `_constants.py`, ao lado de `ACTION_TO_TOOL`/`PARAM_REMAP` (fonte única)
- [ ] `_execute_tool_calls` aplica `name = NATIVE_TOOL_ALIAS.get(name, name)` ANTES de sanitize/remap/preflight/permissão/execute
- [ ] `_execute_tool_calls` aplica `args = _remap_params(name, args)` logo após `sanitize_tool_args` (paridade com `_execute_parsed_action:564`)
- [ ] `validate_path` (base.py) troca `"Path vazio"` por mensagem que nomeia a convenção de parâmetro (file_path vs path)
- [ ] Parser fallback (`_execute_parsed_action`) segue byte-idêntico (AC4)
- [ ] Proof runtime-real colado (passo 3): read_file{'path'} → tool vê `file_path`; create_file → `write_file`, ZERO `Tool desconhecida`
- [ ] `ruff` limpo, acentuação rc=0, `FAIL_AFTER <= FAIL_BEFORE`, smoke boot `boot ok`
- [ ] Gauntlet `--only rapido` **DEFERIDO** para GPU exclusiva (registrar quando rodar)
- [ ] `SPRINT_ORDER_MASTER.md` marca 422 CONCLUIDA; spec movida para `concluidos/` (integração é do orquestrador)
- [ ] NÃO commitar; NÃO tocar `Checkpoint.md`; NÃO tocar o parser fallback nem os guards do contrato

---

## Guardrails anti-engodo (obrigatórios)

NÃO marcar concluída se:
- O alias/remap ficou DEPOIS de preflight/permissão/execute (a ordem é o núcleo: alias e remap ANTES de todos os passos do caminho nativo).
- O alias foi aplicado ao `name` mas DEPOIS do `_remap_params` (aí `create_file` não recebe o remap de `write_file`; alias primeiro, remap depois).
- O parser fallback (`_execute_parsed_action`) foi alterado (deve seguir byte-idêntico — a mudança é só ADITIVA ao caminho nativo).
- `PARAM_REMAP` foi editado (a tabela já existe e está correta; só passa a ser aplicada no caminho nativo).
- `create_file` foi registrado como tool real no registry (a decisão é ALIAS, idêntica ao parser).
- Algum guard do contrato (tool-match/seq-edit/echo/done/preflight/permissão) foi movido, removido ou passou a ver o nome/args crus em vez do aliassado/remapeado.
- Proof runtime-real não colado, ou o `_tools.execute` capturado ainda recebe `path` (sem remap) ou `create_file` (sem alias).

Se algo falhar: `[SPRINT 422] BLOQUEADA: <motivo 1 linha>`.

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
Baseline esperado: `FAIL_BEFORE = 0`, `FAIL_AFTER <= 0` (regra binária `FAIL_AFTER <= FAIL_BEFORE`). Colar: inv_before/inv_after (tail), diff, o output do proof runtime-real (passo 3), o `rg` das âncoras (passos 2 e 4), `git --no-pager diff --stat` e `./run.sh --smoke` (deve imprimir `boot ok`). O gauntlet fica **DEFERIDO** para GPU exclusiva — registrar o resultado quando a GPU estiver livre.

---

## Gambiarras específicas desta sprint

- **Alias antes do remap (ordem obrigatória):** `_remap_params(name, args)` usa `name` para escolher a tabela em `PARAM_REMAP`. Como `create_file` não está em `PARAM_REMAP`, o alias para `write_file` precisa vir antes para o remap de `write_file` (`{"path":"file_path"}`) ser aplicado.
- **`sanitize_tool_args` é agnóstico de nome:** limpa os valores de `_PATH_KEYS = ("file_path","path")` independentemente do nome da tool (`sanitize.py:15,45-51`), então rodar sanitize entre o alias e o remap é seguro em qualquer ordem — a escolha (sanitize, depois remap) espelha a intenção e mantém o valor limpo antes de a chave ser renomeada.
- **Alias no topo, não no registry:** aplicar em `_execute_tool_calls` (não em `ToolRegistry.execute`) mantém o registry puro e faz o `name` canônico fluir pelos guards do contrato (tool-match, seq-edit, `is_key`, add_tool_call) — todos já tratam `create_file`/`write_file` de forma equivalente, então aliassar cedo não muda nenhuma decisão além de tornar o nome executável.
- **Mensagem de `validate_path` sem acesso aos args:** `validate_path(file_path, project_root)` só recebe a string do caminho, não o dict de args, então a mensagem não pode afirmar QUAL chave o modelo usou — ela lista as duas convenções honestamente (file_path vs path). O caso comum já foi resolvido pelo remap; esta mensagem é defesa do resíduo.

---

## Validação humana (checklist do usuário)

```bash
cd /home/andrefarias/Desenvolvimento/Nyx-Code
git --no-pager show --stat HEAD

# Com o stack real (GPU exclusiva), mandar um prompt que faca o 3b ler/criar
# arquivo. Antes: 'Path vazio' ou 'Tool desconhecida: create_file' apareciam
# quando o modelo usava 'path' ou 'create_file'. Depois: a leitura/criação
# acontece de fato (a infra corrige o nome do parametro e o alias da tool).

ls dev-journey/06-sprints/concluidos/SPRINT_LOOP_NATIVE_PARAM_REMAP_01.md  # existe apos integração
```

---

## Causa-raiz (verificada no código real — divergências do briefing)

Todas as evidências do briefing foram confirmadas no código; houve apenas **desvios de path e de numeração de linha** (as linhas deslizaram e o briefing usou paths encurtados):

- **Paths reais das tools:** o briefing cita `nyx/tools/read_file.py`, `base.py`, `registry.py`; os arquivos reais estão em **`nyx/agent/tools/`** (`read_file.py:32`, `base.py:176`, `registry.py:223`). Confirmados.
- **`sanitize.py` e `parser.py`:** ficam em **`nyx/agent/sanitize.py`** e **`nyx/agent/parser.py`** (não em `nyx/agent/loop/`). O loop `_PATH_KEYS` está em `sanitize.py:15,45-51`; a docstring `{"name":"read_file","arguments":{"path":"..."}}` em `parser.py:246`. Confirmados.
- **Ponto de aplicação do sanitize no caminho nativo:** o briefing sugere aplicar o remap "logo após sanitize_tool_args (_iteration.py:~434)". O `sanitize_tool_args` real está na **linha 334** (topo do `for tc in tool_calls:`); a linha 434 é o `preflight_check`, e a linha 462 é o `execute`. Portanto o ponto correto de inserção é **após a linha 334**, não 434. Ajustado na spec.
- **`_remap_params` já importado:** `_iteration.py:30` já importa `_remap_params` de `_constants`; a spec só adiciona `NATIVE_TOOL_ALIAS` ao mesmo import.
- **Alias no parser é via `ACTION_TO_TOOL`, não um dicionário de nomes:** o alias `create_file->write_file` no parser vem de `ACTION_TO_TOOL[ActionType.CREATE_FILE] = "write_file"` (`_constants.py:11`), aplicado em `_execute_parsed_action:550`. O caminho nativo trabalha com o nome-string cru (`tc["name"]`), não com `ActionType`, então precisa de um alias de **string** próprio (`NATIVE_TOOL_ALIAS`) — o `ACTION_TO_TOOL` não o cobre. Essa é a razão de a spec criar um dicionário novo em vez de reusar `ACTION_TO_TOOL`.

Nenhuma divergência de mecanismo: os dois sintomas (Consequência 1 "Path vazio" e Consequência 2 "Tool desconhecida") têm a **mesma** causa-raiz — o caminho nativo não replica a compensação do parser — e são fechados no **mesmo** ponto de inserção. Por isso ficam como ACs separados de uma única sprint (AC1 remap, AC2 alias), com AC3 (mensagem honesta) como complemento barato do resíduo.

---

## Fora de escopo (anti-débito)

| Item | Decisão |
|------|---------|
| Unificar a convenção de nomes de parâmetro entre tools (file_path vs path vs notebook_path) num único nome | **NÃO-OBJETIVO.** Refatoração ampla que toca todas as tools + schemas + prompt + parser. Se o dono quiser, registrar sprint própria `INFRA-TOOL-PARAM-NAME-UNIFY-01` (anti-débito: `feedback_nenhum_debito`). Esta sprint apenas faz o remap existente rodar no caminho nativo. |
| Remover `create_file` do system prompt (`prompt.py:147`) | **NÃO-OBJETIVO.** Com o alias em vigor, o nome anunciado passa a funcionar de fato (o caminho honesto por ADR-032: a infra torna verdadeiro o que o prompt promete). Mexer no prompt arriscaria os testes de prompt/parser sem ganho. |
| Alinhar a docstring do parser (`parser.py:246`, mostra `path`) com `file_path` | **NÃO-OBJETIVO.** É só docstring; o remap já cobre o `path` real emitido. Se incomodar, catalogar como minúcia BAIXA em sprint de documentação. |
| Registrar `create_file` como tool real (segunda classe) no registry | **REJEITADO.** A decisão é alias para `write_file`, idêntica ao parser — evita duas tools que fazem a mesma coisa. |
| Middleware/hardening no lado do proxy | Fora de escopo — a correção é client-side no loop. |

---

## Referências

- BRIEF: `/home/andrefarias/Desenvolvimento/Nyx-Code/VALIDATOR_BRIEF.md`
- Origem: auditoria de prontidão 2026-07-12, relatório durável `dev-journey/07-reports/AUDIT_2026_07_12.md` §3 (briefing efêmero da sessão de auditoria) (achado verificado file:line, 2026-07-12)
- Precedente de estrutura: `dev-journey/06-sprints/producao/SPRINT_EXEC_CONTRACT_PROXY_STATUS_BEFORE_JSON_01.md` (sprint 413)
- Compensação já existente no parser: `nyx/agent/loop/_iteration.py:550,564` (`_execute_parsed_action`)
- Tabela de remap e alias de ação: `nyx/agent/loop/_constants.py:9-46`
- ADR-032/033/034: robustez pertence à infra, não ao modelo

---

*"A infra que existe para compensar o 3b não pode rodar só no caminho de fallback — o caminho principal é onde o usuário leigo vive." -- princípio de execução (ADR-032/033/034)*
