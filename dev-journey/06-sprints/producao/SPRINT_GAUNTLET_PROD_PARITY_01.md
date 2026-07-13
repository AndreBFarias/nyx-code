## 0. SPEC (machine-readable)

```yaml
sprint:
  id: GAUNTLET-PROD-PARITY-01
  numero: 434
  title: "Gauntlet mede o contrato real: fases tools/qualidade usam schema de tools e system prompt do produto, não sinteticos"
  onda: 48
  prioridade: ALTA
  tipo: Bugfix
  dependencias: []
  desbloqueia: []
  absorve: []

  touches:
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/scripts/gauntlet/nyx_gauntlet.py
      reason: "trocar os 6 schemas hand-rolled de _phase_tools por registry.tool_defs e injetar build_system_prompt real; atualizar os expected_tool para os nomes reais (read_file/write_file/edit_file/run_command/glob/search); Q-02 e Q-04 de _phase_qualidade passam a usar o system prompt real e o schema real"
      linhas_alvo: "907-960 (_phase_tools: all_tools + tuplas tests + laco de asserts), 966-1002 (_phase_qualidade: Q-02 nyx_prompt sintetico e Q-04 tool fake)"
  creates: []
  removes: []

  forbidden:
    - "Adicionar emoji"
    - "Usar 'print()' fora de cli.py/output.py"
    - "Mencao a ferramenta de IA proprietaria"
    - "Tocar o proxy (nyx/proxy.py), o loop (nyx/agent/loop/) ou o registry/prompt do produto -- a mudanca e SO no gauntlet"
    - "Remover o helper self._tool (usado por outras fases); ele fica, apenas deixa de ser a fonte das fases tools/qualidade"
    - "Alterar CTX-11 (4274-4320): ja usa o padrão correto e serve de referencia"
    - "Mudar o mecanismo de assert (found = expected_tool in tool_names) -- so muda o VALOR esperado para o nome real"

  tests:
    - cmd: "/home/andrefarias/.local/bin/ruff check scripts/gauntlet/nyx_gauntlet.py"
      deve_passar: true
    - cmd: "bash scripts/sprint_invariants.sh"
      deve_passar: true
    - cmd: "./venv/bin/python -c \"import ast,sys; ast.parse(open('scripts/gauntlet/nyx_gauntlet.py').read()); print('parse ok')\""
      deve_passar: true
    - cmd: "./run.sh --gauntlet --only tools"
      timeout: 300
      deve_passar: false
      nota: "DEFERIDO para GPU exclusiva (exige Ollama vivo; rodar so com pgrep de contencao vazio). não e criterio de merito -- o objetivo e MEDIR o contrato real, não garantir 100%"

  acceptance_criteria:
    - "_phase_tools deixa de montar os 6 tools fake (Read/Write/Edit/Bash/Glob/Grep) e passa a usar ToolRegistry(str(PROJECT_ROOT)).tool_defs -- o mesmo schema das 35 tools reais que o produto registra (padrão de CTX-11 :4282-4285)"
    - "_phase_tools injeta o system prompt real via build_system_prompt(str(PROJECT_ROOT), tool_names) na chamada _chat_with_tools (hoje passa system=None -- ZERO prompt); tool_names = [name for name in registry._tools], identico a CTX-11"
    - "os expected_tool das 6 tuplas de _phase_tools passam a apontar os nomes reais: Read->read_file, Write->write_file, Edit->edit_file, Bash->run_command, Glob->glob, Grep->search"
    - "Q-02 (:969-985) troca o nyx_prompt sintetico de 1 linha ('Sou Nyx. Codificadora...') pelo build_system_prompt real -- a identidade e testada sob o prompt FULL do produto, não um resumo"
    - "Q-04 (:987-1002) troca o único tool fake Read pelo registry.tool_defs real + system prompt real -- o uso proativo e medido com as 35 tools, não com 1"
    - "regressao do proxy preservada: um (1) teste sonda com schema minimo hand-rolled (via self._tool) permanece para detectar quebra do proxy isolada do prompt FULL -- documentado no codigo com comentario da sprint"
    - "ruff limpo, ast.parse ok, acentuacao rc=0, invariantes FAIL_AFTER <= FAIL_BEFORE, smoke boot ok; gauntlet --only tools/qualidade DEFERIDO para GPU exclusiva (o pass-rate real pode CAIR -- isso e o achado honesto, não regressao desta sprint)"
```

---

# Sprint GAUNTLET-PROD-PARITY-01 — O gauntlet mede o contrato real, não um sintético

**Status:** PENDENTE
**Data criação:** 2026-07-12
**Modelo obrigatório:** claude-opus-4-7 (executor-sprint autorizado pelo dono nesta onda)

---

## Contexto do projeto (snapshot — não referência)

> **Missão (calibra o mérito desta sprint):** o Nyx-Code faz o pior LLM local (qwen 3b) na pior máquina possível parecer um agente de código profissional offline. Robustez pertence à INFRA, não ao modelo (ADR-032/033/034). O usuário-alvo é leigo e sem hardware bom. Um gate que valida um contrato inexistente em produção dá falsa confiança: o modelo pode passar no gauntlet e falhar 100% com o usuário real — foi o modo de falha da ONDA-48.
>
> **Estado (2026-07-12):** `qwen2.5-coder:3b`. Registry expõe **35 tools nativas** (verificado: `read_file, write_file, edit_file, run_command, glob, search, list_files, multi_edit, patch, ...`). Ports: Ollama `11435`, proxy `11436`. O gauntlet vive em `scripts/gauntlet/nyx_gauntlet.py`.

---

## Problema

**Achado (auditoria de prontidão 2026-07-12, verificado adversarialmente com file:line):** as fases do gauntlet que invocam o modelo para provar comportamento de tools medem um contrato **sintético**, diferente do que roda em produção. O gate passa validando algo que o produto não registra.

**Causa-raiz (reconferida no código real — linhas confirmadas, sem deslize relevante):**

1. **`_phase_tools` monta 6 tools fake** (`scripts/gauntlet/nyx_gauntlet.py:908-925`):
   `self._tool("Read", "Lê arquivo", ...)`, `self._tool("Bash", "Executa comando", ...)`, `Write`, `Edit`, `Glob`, `Grep`. **Mas o produto registra `read_file`/`write_file`/`edit_file`/`run_command`/`glob`/`search`** — o próprio runner do gauntlet usa os nomes reais em outra fase (`:2978 reg.execute("write_file", ...)`, `:3021 reg.execute("run_command", ...)`). O assert `:949 found = expected_tool in resp.get("tool_names", [])` só confere se o nome fake apareceu; **a tool nunca e executada**.
2. **`_phase_tools` não passa system prompt algum:** `:948 resp = await self._chat_with_tools(prompt, all_tools)` — o parâmetro `system` fica no default `None` (assinatura `:5014`). Em produção o modelo sempre recebe o `build_system_prompt` FULL (com ADRs, few-shots, repo_map). Testar sem prompt e com 6 nomes curtos não reproduz a condição real.
3. **`_phase_qualidade` Q-02 usa um prompt de 1 linha** (`:971 nyx_prompt = "Sou Nyx. Codificadora. Vivo no terminal. PT-BR. Frases curtas. Sem emojis."`) em vez do `build_system_prompt` real; **Q-04 (`:989`) usa um único tool fake `Read`** em vez do schema completo.
4. **Só CTX-11 (`:4274-4320`) faz certo:** monta `registry = ToolRegistry(str(PROJECT_ROOT))`, `tool_names = [name for name in registry._tools]`, `system = build_system_prompt(str(PROJECT_ROOT), tool_names)`, `tool_schemas = registry.tool_defs`. Esse e o padrão a replicar.

**Por que isso importa (impacto):** o qwen3 3b e hipersensível a nome/descrição de tool e ao tamanho do prompt — a GAUNTLET-TOOLS-DESC-MATCH-01 mediu **~9% de alucinação do `function.name`** com o schema real. Passar com 6 tools fake de nome curto e sem prompt **não prova nada** sobre o comportamento com as 35 tools reais + prompt FULL (few-shots das sprints 393/404). O modelo pode acertar no gauntlet e errar com o usuário — o gate estaria mentindo.

Isso fere **"a infra prova o que o usuário vive"**: o gate de qualidade tem que exercitar o MESMO contrato (schema + prompt) que a sessão real monta.

---

## Solução proposta

Trocar, **apenas dentro do gauntlet**, os schemas hand-rolled e o prompt sintético pelo par real `registry.tool_defs` + `build_system_prompt`, replicando o padrão que CTX-11 já usa. Três edições cirúrgicas, todas em `scripts/gauntlet/nyx_gauntlet.py`, sem tocar produto:

1. **`_phase_tools`:** construir `registry = ToolRegistry(str(PROJECT_ROOT))`, `tool_names = [name for name in registry._tools]`, `system = build_system_prompt(str(PROJECT_ROOT), tool_names)`, `real_tools = registry.tool_defs`. As 6 tuplas de teste passam a esperar os nomes reais; o laço chama `self._chat_with_tools(prompt, real_tools, system=system)`.
2. **`_phase_qualidade` Q-02:** substituir `nyx_prompt` de 1 linha pelo `build_system_prompt` real (identidade sob o prompt FULL). Mantém `tools=None` (Q-02 e sobre identidade, não sobre chamar tool).
3. **`_phase_qualidade` Q-04:** substituir o único tool fake `Read` por `registry.tool_defs` real + o system prompt real; o assert `used_tool = len(tool_names) > 0` fica, mas agora sob a condição de produção.
4. **Sonda de regressão do proxy:** manter **um** teste com schema mínimo hand-rolled (via `self._tool`) — isola quebra do proxy de quebra do prompt FULL. Documentar no código com comentário citando esta sprint. O helper `self._tool` NÃO e removido (outras fases o usam).

O import de `build_system_prompt` e `ToolRegistry` e local (dentro do método), idêntico a CTX-11 (`:4279-4280`) — não mexe no header.

---

## Arquivos alvo (paths absolutos)

### `/home/andrefarias/Desenvolvimento/Nyx-Code/scripts/gauntlet/nyx_gauntlet.py`

#### Edit 1 — `_phase_tools`: schema real + system real + expected_tool reais (linhas 907-960)

Substituir o bloco `all_tools = [ ...6 fakes... ]` por:

```python
    async def _phase_tools(self) -> None:
        # GAUNTLET-PROD-PARITY-01: o gauntlet media um contrato sintetico (6 tools
        # fake de nome curto, sem system prompt) diferente do que o produto registra.
        # Passa a usar o MESMO schema + prompt da sessão real (padrão de CTX-11).
        from nyx.agent.prompt import build_system_prompt
        from nyx.agent.tools.registry import ToolRegistry

        registry = ToolRegistry(str(PROJECT_ROOT))
        tool_names = [name for name in registry._tools]
        system = build_system_prompt(str(PROJECT_ROOT), tool_names)
        real_tools = registry.tool_defs

        tests = [
            ("T-01", "read_file arquivo", "leia o arquivo README.md", "read_file"),
            ("T-03", "write_file criar arquivo", "crie /tmp/nyx_gauntlet_test.py com def hello(): return 'ok'", "write_file"),
            ("T-05", "edit_file editar arquivo", "edite o arquivo /tmp/nyx_gauntlet_test.py trocando 'ok' por 'nyx'", "edit_file"),
            ("T-06", "run_command executar", "execute o comando: echo NYX_GAUNTLET_OK", "run_command"),
            ("T-08", "glob buscar .sh", "encontre todos os arquivos .sh do projeto", "glob"),
            ("T-09", "search buscar think", "use search para buscar o texto 'think' dentro dos arquivos do projeto", "search"),
        ]

        for fid, name, prompt, expected_tool in tests:
            t = time.monotonic()
            resp = await self._chat_with_tools(prompt, real_tools, system=system)
            found = expected_tool in resp.get("tool_names", [])
            elapsed = time.monotonic() - t
            self._add(
                fid, name, "tools", found, elapsed,
                tokens=resp.get("tokens", 0),
                details=str(resp.get("tool_args", ""))[:100],
                error="" if found else f"Esperava {expected_tool}, recebeu {resp.get('tool_names', [])}",
            )
```

> Observação para o executor: preserve a assinatura e a ordem dos argumentos de `self._add(...)` exatamente como no original (`fid, name, "tools", found, elapsed, tokens=..., details=..., error=...`). O bloco acima e ilustrativo do alvo; ajuste ao layout exato das linhas 946-960.

#### Edit 2 — Q-02: system prompt real (linhas 969-985)

Trocar:
```python
        nyx_prompt = "Sou Nyx. Codificadora. Vivo no terminal. PT-BR. Frases curtas. Sem emojis."
        resp = await self._chat_with_tools("quem é voce? responda em uma frase curta", tools=None, system=nyx_prompt)
```
por (import local + prompt real):
```python
        # GAUNTLET-PROD-PARITY-01: identidade sob o prompt FULL do produto, não um resumo.
        from nyx.agent.prompt import build_system_prompt
        from nyx.agent.tools.registry import ToolRegistry

        _reg = ToolRegistry(str(PROJECT_ROOT))
        nyx_prompt = build_system_prompt(str(PROJECT_ROOT), [n for n in _reg._tools])
        resp = await self._chat_with_tools("quem é voce? responda em uma frase curta", tools=None, system=nyx_prompt)
```

#### Edit 3 — Q-04: schema real + system real (linhas 987-1002)

Trocar:
```python
        tools = [self._tool("Read", "Lê arquivo", {"file_path": {"type": "string"}}, ["file_path"])]
        resp = await self._chat_with_tools("leia o arquivo README.md", tools)
```
por (reaproveita `_reg`/`nyx_prompt` do Q-02 se no mesmo método, senão reconstrói):
```python
        # GAUNTLET-PROD-PARITY-01: uso proativo medido com as 35 tools reais + prompt FULL.
        resp = await self._chat_with_tools("leia o arquivo README.md", _reg.tool_defs, system=nyx_prompt)
```

#### Edit 4 — sonda de regressão do proxy (aditiva, opcional-mas-recomendada)

Adicionar em `_phase_tools`, após o laço, UM teste com schema mínimo hand-rolled, para isolar quebra do proxy da quebra do prompt FULL:
```python
        # GAUNTLET-PROD-PARITY-01: sonda de regressao do proxy -- schema minimo
        # hand-rolled, sem prompt FULL, isola quebra do transporte da quebra do
        # contrato real. não substitui os testes de paridade acima.
        t = time.monotonic()
        sonda = [self._tool("read_file", "Le arquivo", {"file_path": {"type": "string"}}, ["file_path"])]
        resp = await self._chat_with_tools("leia o arquivo README.md", sonda)
        self._add("T-SONDA", "sonda proxy (schema minimo)", "tools",
                  "read_file" in resp.get("tool_names", []), time.monotonic() - t,
                  tokens=resp.get("tokens", 0))
```

---

## Diff esperado (resumo)

```
~ 1 arquivo modificado (scripts/gauntlet/nyx_gauntlet.py)
  net ~ +15/-12 linhas (troca de schema+prompt; helper self._tool preservado)
```

Sem aritmética de extração: esta sprint não tem meta `arquivo < NNNL`. O número relevante e o net-add num único arquivo; nenhum arquivo de produto e tocado.

---

## Comandos de verificação (literais, copy-paste)

```bash
cd /home/andrefarias/Desenvolvimento/Nyx-Code

# 1. Estatica + acentuacao (ruff via binario direto -- não ha modulo ruff no venv, ver BRIEF)
/home/andrefarias/.local/bin/ruff check scripts/gauntlet/nyx_gauntlet.py
python3 ~/.config/zsh/scripts/validar-acentuacao.py --paths scripts/gauntlet/nyx_gauntlet.py

# 2. Parse e conferencia das ancoras (linhas podem ter deslizado -- reconferir):
./venv/bin/python -c "import ast; ast.parse(open('scripts/gauntlet/nyx_gauntlet.py').read()); print('parse ok')"
rg -n "build_system_prompt|registry.tool_defs|_reg.tool_defs|real_tools|expected_tool|self._tool\(" scripts/gauntlet/nyx_gauntlet.py

# 3. PROOF RUNTIME-REAL SEM GPU: os nomes esperados batem com os do registry?
#    (não invoca o modelo; so confere que a paridade schema<->assert e coerente)
./venv/bin/python - <<'PY'
from nyx.agent.tools.registry import ToolRegistry
reg = ToolRegistry(".")
nomes = set(reg._tools)
esperados = {"read_file", "write_file", "edit_file", "run_command", "glob", "search"}
faltando = esperados - nomes
assert not faltando, f"nomes esperados ausentes no registry: {faltando}"
print("OK: os 6 expected_tool das tuplas existem no registry real:", sorted(esperados))
print("total de tools reais:", len(nomes))
PY

# 4. build_system_prompt real produz prompt não-trivial (prova que o Q-02/tools usa o FULL)
./venv/bin/python - <<'PY'
from nyx.agent.prompt import build_system_prompt
from nyx.agent.tools.registry import ToolRegistry
reg = ToolRegistry(".")
p = build_system_prompt(".", [n for n in reg._tools])
assert len(p) > 500, len(p)
print("OK: build_system_prompt real ->", len(p), "chars (não e o resumo de 1 linha)")
PY

# 5. Invariantes + smoke boot
bash scripts/sprint_invariants.sh
./run.sh --smoke   # deve imprimir 'boot ok'

# 6. Gauntlet das fases afetadas -- DEFERIDO para GPU exclusiva (protocolo anti-contencao do BRIEF)
./run.sh --gauntlet --only tools
./run.sh --gauntlet --only qualidade
```

> Nota GPU: os passos 1-5 rodam SEM Ollama/GPU. O passo 6 (gauntlet) exige GPU exclusiva e fica **DEFERIDO** — executar só quando `pgrep -af "Luna.*driver|valida_sprint"` estiver vazio, como as specs 403/407 fazem. **Atenção de mérito:** o pass-rate de `--only tools`/`--only qualidade` PODE CAIR após esta mudança — isso e o achado honesto que a sprint expõe (o gate antes media fácil demais), NÃO uma regressão desta sprint. Qualquer queda vira achado novo (ver Fora de escopo).

---

## Critério binário de aceite (IA executora)

- [ ] `_phase_tools` usa `ToolRegistry(str(PROJECT_ROOT)).tool_defs` (não os 6 fakes) + `build_system_prompt(...)` como `system`
- [ ] As 6 tuplas esperam `read_file/write_file/edit_file/run_command/glob/search` (não `Read/Write/Edit/Bash/Glob/Grep`)
- [ ] Q-02 usa `build_system_prompt` real (não o `nyx_prompt` de 1 linha)
- [ ] Q-04 usa `registry.tool_defs` real + system real (não o tool fake único)
- [ ] Sonda de regressão do proxy (schema mínimo) presente e comentada com a tag da sprint
- [ ] Helper `self._tool` preservado (outras fases o usam); CTX-11 intacto
- [ ] Passos 3 e 4 do proof colados: os 6 nomes existem no registry; `build_system_prompt` > 500 chars
- [ ] `ruff` limpo, `ast.parse` ok, acentuação rc=0, `FAIL_AFTER <= FAIL_BEFORE`, smoke boot ok
- [ ] Gauntlet `--only tools`/`--only qualidade` marcado **DEFERIDO para GPU exclusiva** no relato (pass-rate real anexado quando a GPU liberar; queda documentada como achado, não como falha da sprint)
- [ ] NÃO commitar; NÃO tocar Checkpoint.md; NÃO tocar produto (`nyx/`)

---

## Guardrails anti-engodo (obrigatórios)

NÃO marcar concluída se:
- Ficou algum `self._tool("Read"...)`/`"Bash"`/`"Write"`/`"Edit"`/`"Glob"`/`"Grep"` como fonte das fases tools/qualidade (a sonda usa `read_file` minúsculo — nome real, schema mínimo; isso e permitido e distinto).
- `_phase_tools` seguiu chamando `_chat_with_tools(prompt, all_tools)` sem `system=` (o prompt FULL e metade do fix).
- Q-02 seguiu com o `nyx_prompt` de 1 linha.
- Os `expected_tool` ficaram com os nomes fake antigos (o assert passaria a nunca casar e mascararia como falha do modelo).
- Tocou `nyx/proxy.py`, `nyx/agent/loop/`, `nyx/agent/prompt.py` ou `nyx/agent/tools/registry.py` (produto e não-objetivo — só o gauntlet muda).
- Removeu o helper `self._tool` ou alterou CTX-11.
- Alterou o pass-rate reportado para "100%" sem GPU real (o gauntlet e DEFERIDO; forjar número e engodo).

Se algo falhar: `[SPRINT 434] BLOQUEADA: <motivo 1 linha>`.

---

## Proof-of-work esperado (obrigatório)

```bash
bash scripts/sprint_invariants.sh > /tmp/inv_before.txt 2>&1
FAIL_BEFORE=$(grep -c "^\[FAIL\]" /tmp/inv_before.txt)
# implementar
bash scripts/sprint_invariants.sh > /tmp/inv_after.txt 2>&1
FAIL_AFTER=$(grep -c "^\[FAIL\]" /tmp/inv_after.txt)
diff /tmp/inv_before.txt /tmp/inv_after.txt
```
Baseline esperado: `FAIL_BEFORE = 0`, `FAIL_AFTER <= 0`. Colar: inv_before/inv_after (tail), diff, os proofs sem-GPU (passos 3-4), o `rg` das âncoras (passo 2), `git --no-pager diff --stat` e `./run.sh --smoke` (deve imprimir `boot ok`). O gauntlet `--only tools`/`--only qualidade` fica **DEFERIDO para GPU exclusiva** — anexar o pass-rate real quando a GPU liberar; a queda esperada e o valor da sprint (medir o contrato real), não bloqueia o mérito.

---

## Gambiarras específicas desta sprint

- **Import local, não no header:** `build_system_prompt`/`ToolRegistry` entram dentro dos métodos (idêntico a CTX-11 `:4279-4280`) — o header do gauntlet fica intocado e o custo de import só ocorre nas fases que usam.
- **`registry._tools` e atributo "privado":** CTX-11 já lê `registry._tools` para montar `tool_names`; seguir o mesmo acesso mantém a paridade e evita inventar API nova. Não trocar por `registry.tool_defs` para extrair nomes (formatos diferentes).
- **`self._add` posicional:** a ordem `(fid, name, categoria, ok, elapsed, tokens=, details=, error=)` e sensível — copiar do bloco original, não reescrever de memória.
- **Sonda com nome real minúsculo:** a sonda usa `read_file` (nome real) com descrição/params mínimos de propósito — ela mede o transporte/proxy, não o contrato completo; por isso NÃO conta como violação do "sem fakes".

---

## Validação humana (checklist do usuário)

```bash
cd /home/andrefarias/Desenvolvimento/Nyx-Code
git --no-pager show --stat HEAD

# Com GPU exclusiva: rodar o gauntlet das fases afetadas e comparar com o baseline
# anterior. Uma eventual QUEDA no pass-rate e o sinal honesto de que o gate agora
# mede o que o usuário vive -- registrar o numero real, não maquiar.
./run.sh --gauntlet --only tools
./run.sh --gauntlet --only qualidade

ls dev-journey/06-sprints/concluidos/SPRINT_GAUNTLET_PROD_PARITY_01.md  # apos mover
```

---

## Fora de escopo (anti-débito)

| Item | Decisão |
|------|---------|
| Se `--only tools`/`--only qualidade` cair abaixo de 100% com o schema+prompt reais | **Achado NOVO, sprint própria.** E o comportamento real do qwen3 3b sob o contrato de produção; endurecer a infra (descrições de tool, few-shots, remap) e trabalho de outra sprint — registrar `GAUNTLET-PROD-PARITY-TUNE-01` (memória `feedback_nenhum_debito`). Esta sprint SÓ corrige a medição. |
| Outras fases do gauntlet que ainda usem `self._tool` fake fora de tools/qualidade | Não auditadas neste briefing; se houver, registrar sprint de varredura própria — não expandir escopo aqui. |
| Hardening do proxy para nomes alucinados (já coberto por GAUNTLET-TOOLS-DESC-MATCH-01) | Fora — a sonda apenas detecta regressão; o fix do proxy já existe. |

---

## Referências

- BRIEF: `/home/andrefarias/Desenvolvimento/Nyx-Code/VALIDATOR_BRIEF.md`
- Padrão a replicar: CTX-11 em `scripts/gauntlet/nyx_gauntlet.py:4274-4320`
- Precedente (hipersensibilidade a nome de tool): `dev-journey/06-sprints/concluidos/SPRINT_GAUNTLET_TOOLS_DESC_MATCH_01.md` (~9% de alucinação do `function.name`)
- Nomes reais das tools (35): `read_file, write_file, edit_file, run_command, glob, search, list_files, ...` — via `ToolRegistry(".")._tools`
- Achado + tabela: `dev-journey/06-sprints/SPRINT_ORDER_MASTER.md` (bloco ONDA-48, sprint 434)
- Origem: auditoria de prontidão 2026-07-12 (achados verificados adversarialmente, file:line)

---

*"Um gate que valida um contrato que o produto não tem dá falsa confiança: o modelo passa no teste e falha com o usuário. A infra prova o que o usuário vive — schema e prompt reais, ou o número mente."*
