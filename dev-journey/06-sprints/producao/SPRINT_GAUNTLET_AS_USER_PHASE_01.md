## 0. SPEC (machine-readable)

```yaml
sprint:
  id: GAUNTLET-AS-USER-PHASE-01
  numero: 433
  title: "Fase 'contrato' no gauntlet: exercer o caminho real modelo->tool->apresentacao via headless {\"type\":\"request\"} (cobertura ZERO hoje)"
  onda: 48
  prioridade: ALTA
  tipo: Cobertura de teste
  dependencias: []
  desbloqueia: []
  absorve: []

  touches:
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/scripts/gauntlet/nyx_gauntlet.py
      reason: "registrar a fase 'contrato' (PHASE_GROUPS + entrada no grupo 'completo' + PHASE_TIMEOUTS + NEEDS_OLLAMA) e implementar o metodo async _phase_contrato que roda o subprocess headless com {\"type\":\"request\"} e NYX_AUTO_APPROVE=1, cobrindo o caminho modelo->tool->apresentacao (contrato ONDA-48, sprints 397-401) hoje com cobertura ZERO"
      linhas_alvo: "51-184 (PHASE_GROUPS incl. lista 'completo'), 186-249 (PHASE_TIMEOUTS), 251 (NEEDS_OLLAMA), novo metodo async _phase_contrato apos _phase_e2e_real (~2969)"
  creates: []
  removes: []

  forbidden:
    - "Adicionar emoji"
    - "Usar 'print()' fora de cli.py/output.py"
    - "Mencao a IA proprietaria"
    - "Tocar os guards do contrato em nyx/agent/loop/ (397/398/399/400/401) -- esta sprint SO os EXERCE, nunca os altera"
    - "Tocar nyx/cli_headless.py (o caminho 'request' ja existe e esta pronto, linha 260)"
    - "Alterar as fases existentes (e2e_real, p3_headless, headless_protocol) -- a fase 'contrato' e ADITIVA"
    - "Trocar de modelo ou de placa (ADR-032/033: robustez pertence a infra, nunca ao modelo)"
    - "Rodar ./run.sh, ollama, gauntlet ou pkill durante a implementacao da spec (proof T1-T5 e DEFERIDO para GPU exclusiva)"

  tests:
    - cmd: "/home/andrefarias/.local/bin/ruff check scripts/gauntlet/nyx_gauntlet.py"
      deve_passar: true
    - cmd: "python3 -c \"import ast; ast.parse(open('scripts/gauntlet/nyx_gauntlet.py').read()); print('ast ok')\""
      deve_passar: true
    - cmd: "bash scripts/sprint_invariants.sh"
      deve_passar: true
    - cmd: "./run.sh --gauntlet --only contrato"
      timeout: 900
      deve_passar: true
      nota: "DEFERIDO para GPU exclusiva -- exige Ollama vivo; rodar so com pgrep de contencao vazio, como as specs 403/407"

  acceptance_criteria:
    - "PHASE_GROUPS ganha a entrada 'contrato': ['contrato'] e a fase 'contrato' e adicionada a lista do grupo 'completo' (senao o caminho as-user nunca roda no gauntlet completo -- o buraco atual)"
    - "PHASE_TIMEOUTS['contrato'] >= 600 (fase); cada subprocess.run(timeout=...) por turno >= 120 (o 3b no RTX 3050 4GB e lento)"
    - "'contrato' e adicionado a NEEDS_OLLAMA (a fase exige o modelo vivo; sem Ollama o runner registra HEALTH FAIL, comportamento identico as demais fases NEEDS_OLLAMA)"
    - "Novo metodo async _phase_contrato: subprocess [sys.executable, '-m', 'nyx.cli', '--headless'] com env NYX_AUTO_APPROVE=1, enviando os probes T1-T5 como {\"type\":\"request\",\"content\":...}, parseando cada linha do stdout como JSON (linhas 'tool_use' do callback on_tool + linha final 'response')"
    - "T1 (fastfetch + specs): assert existe linha {\"type\":\"tool_use\",\"tool\":\"run_command\"} E a 'response'.summary contem 'Resultado:' com dado real (não vazio), SEM sequencia ANSI (\\x1b) e SEM literal '{\"name\":' vazando na apresentacao"
    - "T2 (criar arquivo em _gauntlet_tmp_dir): assert o arquivo existe no disco APOS o turno E a 'response'.files_modified >= 1"
    - "T3 (listar diretório real): assert 'response'.summary tras nomes reais no bloco 'Resultado:' (ex.: um arquivo conhecido do dir listado)"
    - "T4 (buscar conteudo): assert a tool chamada e search/grep (linha tool_use.tool in {'search','grep'}), não glob usado como regex"
    - "T5 (edicao sequencial): assert a tool chamada e edit_file E o conteudo fora do trecho editado e preservado (sha/substring do restante intacto)"
    - "ruff limpo, ast.parse ok, acentuacao rc=0, invariantes FAIL_AFTER <= FAIL_BEFORE"
    - "Proof T1-T5 via './run.sh --gauntlet --only contrato' e DEFERIDO para GPU exclusiva; o wiring (fase registrada, no 'completo', no NEEDS_OLLAMA, metodo coroutine, modulo importavel) e provado SEM GPU"
```

---

# Sprint GAUNTLET-AS-USER-PHASE-01 -- Fase 'contrato': exercer o caminho real modelo->tool->apresentacao no gauntlet

**Status:** PENDENTE
**Data criação:** 2026-07-13
**Modelo obrigatório:** claude-opus-4-7 (executor-sprint autorizado pelo dono nesta onda)

---

## Contexto do projeto (snapshot — não referência)

> **Missão (ADR-032/033/034):** o Nyx-Code faz o pior LLM local (`qwen2.5-coder:3b`) na pior máquina possível (RTX 3050 4GB, usuário leigo, offline) parecer um agente de código profissional. **Robustez pertence à INFRA, não ao modelo.** O contrato de execução da ONDA-48 (sprints 397-401: tool-match, edição sequencial, apresentação forte, anti-recursão, sanitize de path) é justamente a camada de infra que sustenta essa promessa.
>
> **ADR-007 (gauntlet como único gate):** o gauntlet é o único portão de qualidade. Se um mecanismo de infra não tem teste vermelho quando quebra, ele pode regredir silenciosamente com o gauntlet verde.
>
> **Estado (2026-07-13):** `qwen2.5-coder:3b`. ONDA-48 fase raiz: núcleo do contrato (399/397/400/398/401) CONCLUIDO e commitado. Esta sprint materializa o item `GAUNTLET-TOOLCHAIN-01` do roadmap (cobertura de teste ampliada). Ports: Ollama `11435`, proxy `11436`. Auditoria de origem: prontidão 2026-07-12.

---

## Problema

**Achado (auditoria de prontidão 2026-07-12, verificado adversarialmente) [ALTA]:** o gauntlet **nunca envia `{"type":"request"}`** pelo headless. Todas as invocações do runner headless usam apenas mensagens de **controle**:

- `input='{"type": "ping"}\n'` (`scripts/gauntlet/nyx_gauntlet.py:2912`)
- `input='{"type": "reset"}\n'` (`:2948`)
- `_headless('{"type": "status"}\n')` (`:3221`)
- `_headless('{"type": "tools"}\n')` (`:3238`)
- `_headless('{"type": "xyz_invalido"}\n')` (`:3255`)
- pipeline `ping/status/tools/reset` (`:3267`)

`grep` por `'"request"'` no arquivo = **0 ocorrências.** O caminho real existe e está pronto: `nyx/cli_headless.py:260` (`if msg_type == "request" and content:`) roda o `AgentLoop.run()` de verdade e emite o trace via callback `on_tool` (`cli_headless.py:64-67`, linhas `{"type":"tool_use",...}`) + a linha final `{"type":"response","summary":...,"files_modified":...}`. Nenhum dos guards da fase raiz é exercido pelo gauntlet: `grep` por `_compose_presentation_summary|_seq_edit_reject|_tool_match_reject|_should_reject_done|wants_read_only` em `nyx_gauntlet.py` = **0 hits**.

**Impacto:** é exatamente o buraco que deixou o produto colapsar no uso real com o gauntlet verde (lição ONDA-48 literal: "o Gauntlet testa a tool via `ToolRegistry` direto e PULA o modelo" — ver `_phase_e2e_real:2969`, que executa `reg.execute(...)` sem modelo). Os mecanismos 397-401 podem regredir amanhã sem nenhum teste vermelho — fere ADR-007 (gauntlet como único gate) e ADR-032/033.

---

## Causa-raiz (verificada no código, 2026-07-13)

Reconferência das âncoras do briefing contra o código atual (as linhas **não** deslizaram):

- `scripts/gauntlet/nyx_gauntlet.py:2912` — `input='{"type": "ping"}\n'` **confirmado literal**.
- `:2948` reset, `:3221` status, `:3238` tools, `:3255` xyz_invalido, `:3267` pipeline — **todos confirmados literais**.
- `nyx/cli_headless.py:260` — `if msg_type == "request" and content:` **confirmado literal**; roda `await agent.run(content)` e serializa `state/summary/iterations/files_read/files_modified`.
- Callback `on_tool` em `cli_headless.py:64-67` emite uma linha `{"type":"tool_use","tool":name,"args":args}` por chamada de tool — **o trace de tool ESTÁ disponível no stdout headless** (isso torna as asserções "linha tool_use run_command" do briefing plenamente realizáveis; confirmação, não divergência).
- `NYX_AUTO_APPROVE=1` funciona em headless: `cli_headless.py:58` promove `CONFIRM_ONCE -> AUTO` (permite T2/T5 escreverem sem TTY).
- Marcador de apresentação `Resultado:` **confirmado literal** em `nyx/agent/loop/_core.py:605-606` (`_compose_presentation_summary`, def na linha 569): `f"{base}\n\nResultado:\n{resultado}"`. A `response`.summary carrega esse bloco — é o alvo da asserção de T1/T3.
- Estrutura de registro de fases confirmada: `PHASE_GROUPS` (`:51`, com a lista `'completo'` em `:127-183`), `PHASE_TIMEOUTS` (`:186`), `NEEDS_OLLAMA` (`:251`), gate de saúde por fase (`:427` — fase em `NEEDS_OLLAMA` com Ollama fora vira `HEALTH` FAIL, **não** skip). Método de referência `_phase_e2e_real` em `:2969`; helper de scratch autorizado `_gauntlet_tmp_dir()` em `:259`; `_add(fid,name,phase,passed,elapsed,...)` em `:5237`.

**Divergência do briefing:** o briefing diz que a sprint materializa `GAUNTLET-TOOLCHAIN-01` do **roadmap ONDA-50**; o `SPRINT_ORDER_MASTER.md:1109` lista `GAUNTLET-TOOLCHAIN-01` sob **ONDA-48 (Cobertura de Teste Ampliada)**. Divergência apenas de rótulo de onda — adotado `onda: 48` no header (autoridade do master). O mérito técnico do achado é idêntico.

---

## Solução proposta

Uma fase de gauntlet nova e **puramente aditiva**, `contrato`, que dispara o **caminho as-user completo** (modelo -> tool -> apresentação) via o subprocess headless — o mesmo que o usuário leigo exercita. Nada dos guards 397-401 é tocado; a fase apenas os **exerce** e falha em vermelho se algum regredir.

1. **Registrar a fase** em quatro pontos de `nyx_gauntlet.py`:
   - `PHASE_GROUPS`: adicionar `"contrato": ["contrato"]`.
   - Lista do grupo `"completo"` (`:127-183`): adicionar `"contrato"` (sem isso, o caminho as-user **nunca** roda no gauntlet completo — o buraco atual).
   - `PHASE_TIMEOUTS`: adicionar `"contrato": 900` (>= 600; folga para 5 turnos do 3b lento).
   - `NEEDS_OLLAMA`: adicionar `"contrato"` (a fase exige o modelo vivo; sem Ollama vira `HEALTH` FAIL, coerente com as demais).
2. **Implementar `async def _phase_contrato(self)`** logo após `_phase_e2e_real` (~`:2969`): para cada probe T1-T5, roda um `subprocess.run([sys.executable, "-m", "nyx.cli", "--headless"], input=<json request>, env={**os.environ, "NYX_AUTO_APPROVE": "1"}, timeout>=120, cwd=str(PROJECT_ROOT))`, parseia cada linha do `stdout` como JSON, coleta as linhas `tool_use` e a linha final `response`, e registra o resultado via `self._add(...)`.

### Probes (T1-T5)

Escrita/edição usam `_gauntlet_tmp_dir()` (root autorizado por `validate_path`, evita bloqueio de sandbox).

| Probe | Request `content` | Asserção (infra, não o texto do modelo) |
|-------|-------------------|------------------------------------------|
| **T1** | "da um fastfetch e me fala as specs em produção" | existe linha `tool_use.tool == "run_command"` **E** `response.summary` contém `Resultado:` com dado real (não vazio), **sem** `\x1b` (ANSI) e **sem** literal `'{"name":'` vazando |
| **T2** | "crie o arquivo `<tmp>/nyx_contrato_t2.txt` com o texto NYX_AS_USER_OK" | `Path(<tmp>/nyx_contrato_t2.txt).exists()` **E** `response.files_modified >= 1` |
| **T3** | "liste os arquivos de `<tmp>`" | `response.summary` traz nome(s) real(is) no bloco `Resultado:` (ex.: `nyx_contrato_t2.txt` criado em T2, se a fase encadear; senão um arquivo semeado pela fixture) |
| **T4** | "busque a palavra NYX_AS_USER_OK em `<tmp>`" | linha `tool_use.tool in {"search","grep"}` (NÃO `glob` usado como regex) |
| **T5** | "no arquivo `<tmp>/nyx_contrato_t5.py` troque `valor = 1` por `valor = 42`" (arquivo semeado pela fixture com um bloco maior) | linha `tool_use.tool == "edit_file"` **E** o conteúdo fora do trecho editado é preservado (substring/sha do restante intacto) |

> **Nota de robustez:** as asserções miram a **infra** (qual tool foi chamada, o efeito no disco, o formato da apresentação), nunca a prosa exata do 3b — coerente com a missão (o modelo é fraco; a infra é o contrato). A calibração fina de cada marcador (ex.: o nome exato semeado nas fixtures T3/T5) é confirmada pelo executor contra uma execução real quando a GPU estiver livre (proof DEFERIDO).

---

## Arquivos alvo (paths absolutos)

### `/home/andrefarias/Desenvolvimento/Nyx-Code/scripts/gauntlet/nyx_gauntlet.py`

#### Edit 1 — registrar a fase em `PHASE_GROUPS` (`:51`)
Adicionar, junto às demais entradas simples:
```python
    "contrato": ["contrato"],
```

#### Edit 2 — incluir na lista do grupo `"completo"` (`:127-183`)
Adicionar `"contrato"` à lista (ex.: logo após `"e2e_real"`, ou ao final antes de `"contexto"` — posição não é semântica, mas a **inclusão** é o núcleo do fix).

#### Edit 3 — `PHASE_TIMEOUTS` (`:186`)
```python
    "contrato": 900,
```

#### Edit 4 — `NEEDS_OLLAMA` (`:251`)
```python
NEEDS_OLLAMA = {"infra", "proxy", "guardrails", "tools", "qualidade", "performance", "resiliencia", "contexto", "contrato"}
```

#### Edit 5 — método `async def _phase_contrato(self)` (após `_phase_e2e_real`, ~`:2969`)
Esqueleto (o executor detalha as 5 asserções; `import json as _json`, `import subprocess`, `import os` locais como nas outras fases):
```python
    async def _phase_contrato(self) -> None:
        """Caminho as-user real: modelo -> tool -> apresentacao via headless.

        GAUNTLET-AS-USER-PHASE-01: o gauntlet so mandava mensagens de
        controle (ping/status/tools/reset). Esta fase envia
        {"type":"request"} de verdade, exercendo os guards 397-401 que
        antes tinham cobertura ZERO. não altera guard nenhum -- so os EXERCE.
        """
        import json as _json
        import os
        import subprocess

        tmp = _gauntlet_tmp_dir()
        env = {**os.environ, "NYX_AUTO_APPROVE": "1"}

        def _run(fid: str, content: str, timeout: int = 180) -> tuple[list[dict], dict | None]:
            proc = subprocess.run(
                [sys.executable, "-m", "nyx.cli", "--headless"],
                input=_json.dumps({"type": "request", "content": content}) + "\n",
                capture_output=True, text=True, timeout=timeout,
                cwd=str(PROJECT_ROOT), env=env,
            )
            tool_uses, response = [], None
            for ln in proc.stdout.splitlines():
                try:
                    obj = _json.loads(ln)
                except _json.JSONDecodeError:
                    continue
                if obj.get("type") == "tool_use":
                    tool_uses.append(obj)
                elif obj.get("type") == "response":
                    response = obj
            return tool_uses, response

        # T1..T5: cada probe chama _run(...) e registra via self._add(...)
        # com as assercoes da tabela da spec (tool chamada, efeito no disco,
        # 'Resultado:' na apresentacao, sem ANSI, sem '{"name":' vazando).
```

---

## Diff esperado (resumo)

```
~ 1 arquivo modificado (scripts/gauntlet/nyx_gauntlet.py)
+ 4 edits pequenos de registro (PHASE_GROUPS, 'completo', PHASE_TIMEOUTS, NEEDS_OLLAMA)
+ 1 metodo novo _phase_contrato (~70-110 linhas com as 5 asserções)
```

Sem meta numérica de tamanho de arquivo — é adição de cobertura, não extração. O único número relevante é o net-add do método + 4 linhas de registro.

---

## Comandos de verificação (literais, copy-paste)

```bash
cd /home/andrefarias/Desenvolvimento/Nyx-Code

# 1. Estatica + AST + acentuacao (ruff via binario direto -- ver BRIEF)
/home/andrefarias/.local/bin/ruff check scripts/gauntlet/nyx_gauntlet.py
python3 -c "import ast; ast.parse(open('scripts/gauntlet/nyx_gauntlet.py').read()); print('ast ok')"
python3 ~/.config/zsh/scripts/validar-acentuacao.py --paths scripts/gauntlet/nyx_gauntlet.py

# 2. Reconferir as ancoras (as linhas podem deslizar apos edits):
rg -n '"type": "ping"|"type": "request"|NEEDS_OLLAMA|def _phase_contrato' scripts/gauntlet/nyx_gauntlet.py

# 3. PROOF DE WIRING (SEM GPU) -- a fase esta registrada e importavel:
python3 - <<'PY'
import asyncio, inspect
import importlib.util, sys
spec = importlib.util.spec_from_file_location("ng", "scripts/gauntlet/nyx_gauntlet.py")
ng = importlib.util.module_from_spec(spec); sys.modules["ng"] = ng
spec.loader.exec_module(ng)
assert ng.PHASE_GROUPS.get("contrato") == ["contrato"], "PHASE_GROUPS sem 'contrato'"
assert "contrato" in ng.PHASE_GROUPS["completo"], "'contrato' fora do grupo completo"
assert ng.PHASE_TIMEOUTS.get("contrato", 0) >= 600, "timeout da fase < 600"
assert "contrato" in ng.NEEDS_OLLAMA, "'contrato' fora de NEEDS_OLLAMA"
runner_cls = [c for _,c in inspect.getmembers(ng, inspect.isclass) if hasattr(c, "_phase_contrato")]
assert runner_cls, "metodo _phase_contrato ausente"
assert asyncio.iscoroutinefunction(runner_cls[0]._phase_contrato), "_phase_contrato não e coroutine"
print("OK wiring: fase 'contrato' registrada, no 'completo', em NEEDS_OLLAMA, timeout>=600, metodo coroutine")
PY

# 4. Invariantes
bash scripts/sprint_invariants.sh

# 5. PROOF COMPORTAMENTAL T1-T5 -- DEFERIDO para GPU exclusiva:
#    ./run.sh --gauntlet --only contrato   # 100%, timeout 900
#    (exige Ollama vivo; rodar so quando pgrep -af "Luna.*driver|valida_sprint" estiver vazio)
```

> Nota GPU: os passos 1-4 rodam SEM Ollama/GPU (checagem estática + wiring). O passo 5 (`--only contrato`) exige GPU exclusiva e fica **DEFERIDO** — executar só quando a GPU estiver livre (protocolo anti-contenção do BRIEF), como as specs 403/407 fazem. O wiring provado no passo 3 é a evidência de que a fase existe e está no gate; o comportamento T1-T5 é validado na janela de GPU exclusiva.

---

## Critério binário de aceite (IA executora)

- [ ] `PHASE_GROUPS["contrato"] == ["contrato"]` e `"contrato" in PHASE_GROUPS["completo"]`
- [ ] `PHASE_TIMEOUTS["contrato"] >= 600`; cada `subprocess.run(timeout=...)` por turno `>= 120`
- [ ] `"contrato" in NEEDS_OLLAMA`
- [ ] `_phase_contrato` implementado, coroutine, envia `{"type":"request"}` com `NYX_AUTO_APPROVE=1`, parseia `tool_use` + `response` do stdout
- [ ] T1: `tool_use.tool == "run_command"` + `Resultado:` com dado real, sem ANSI, sem `'{"name":'`
- [ ] T2: arquivo no disco + `files_modified >= 1`
- [ ] T3: nomes reais no bloco `Resultado:`
- [ ] T4: `tool_use.tool in {"search","grep"}` (não glob-como-regex)
- [ ] T5: `tool_use.tool == "edit_file"` + conteúdo fora do trecho preservado
- [ ] Proof de wiring (passo 3) colado; `ruff` limpo, `ast.parse` ok, acentuação rc=0, `FAIL_AFTER <= FAIL_BEFORE`
- [ ] Proof T1-T5 (`--only contrato`) DEFERIDO para GPU exclusiva, registrado como pendente
- [ ] NÃO tocou `nyx/cli_headless.py` nem os guards 397-401; NÃO commitou; NÃO tocou `Checkpoint.md`
- [ ] `SPRINT_ORDER_MASTER.md` marca 433 CONCLUIDA; spec movida para `concluidos/` (ação do orquestrador)

---

## Guardrails anti-engodo (obrigatórios)

NÃO marcar concluída se:
- A fase foi registrada em `PHASE_GROUPS` mas **não** entrou na lista `"completo"` (aí o caminho as-user segue sem rodar no gate — o buraco continua aberto).
- O `_phase_contrato` envia `{"type":"ping"}`/`{"type":"status"}` em vez de `{"type":"request"}` (repetiria o defeito atual: só controle, nunca o modelo).
- Alguma asserção mira a prosa exata do 3b em vez da infra (tool chamada / efeito no disco / formato da apresentação) — o modelo é fraco, o contrato é a infra.
- Algum guard 397-401 (`nyx/agent/loop/`) foi tocado, ou `nyx/cli_headless.py` foi alterado.
- O proof de wiring (passo 3) não foi colado, ou o proof T1-T5 foi declarado "passou" sem GPU (é DEFERIDO, não fabricado).
- `NYX_AUTO_APPROVE=1` foi omitido (T2/T5 deadlocam no `CONFIRM_ONCE` sem TTY).

Se algo falhar: `[SPRINT 433] BLOQUEADA: <motivo 1 linha>`.

---

## Proof-of-work obrigatório

```bash
bash scripts/sprint_invariants.sh > /tmp/inv_before.txt 2>&1
FAIL_BEFORE=$(grep -c "^\[FAIL\]" /tmp/inv_before.txt)
# implementar
bash scripts/sprint_invariants.sh > /tmp/inv_after.txt 2>&1
FAIL_AFTER=$(grep -c "^\[FAIL\]" /tmp/inv_after.txt)
diff /tmp/inv_before.txt /tmp/inv_after.txt
```

Baseline esperado: `FAIL_BEFORE = 0`, `FAIL_AFTER <= 0`. Colar: `inv_before`/`inv_after` (tail), diff, o output do proof de wiring (passo 3), o `rg` do passo 2, `git --no-pager diff --stat`. O `./run.sh --gauntlet --only contrato` (proof T1-T5) fica **DEFERIDO** para a janela de GPU exclusiva — registrar como pendente, não bloqueia o mérito do wiring.

---

## Fora de escopo (anti-débito — `feedback_nenhum_debito`)

Achados de infra do gauntlet **não-verificados** citados nas notas do orquestrador. São mecanismos DIFERENTES do buraco as-user; cada um merece sprint própria, NÃO absorver aqui:

| Achado | Evidência (a verificar) | Recomendação de sprint |
|--------|-------------------------|-------------------------|
| `_chat_with_tools` é single-shot sem histórico | `nyx_gauntlet.py:5014` | `GAUNTLET-MULTITURN-HISTORY-01` — só afeta o caminho `_chat_*` (fases legadas), não a fase `contrato` (que roda o `AgentLoop` real com histórico próprio) |
| Runner mono-modelo | `nyx_gauntlet.py:786` | `GAUNTLET-MODEL-SWAP-E2E-01` (já no roadmap ONDA-48) |
| `_detect_regressions` cosmético | `nyx_gauntlet.py:467` | `GAUNTLET-REGRESSION-GUARD-01` (já no roadmap) |
| 7 fases fora do grupo `completo` | `nyx_gauntlet.py:127` (lista `completo` vs. `PHASE_GROUPS`) | `GAUNTLET-COMPLETO-COVERAGE-AUDIT-01` — auditar quais fases faltam no `completo` e por quê |

Esta sprint fecha **apenas** o achado principal (fase as-user com cobertura ZERO). Se durante a execução qualquer um dos itens acima virar bloqueante, registrar sprint nova com ID próprio — nunca absorver implicitamente.

---

## Riscos e não-objetivos

| Risco / não-objetivo | Decisão |
|-------|-----------|
| Flake de VRAM no RTX 3050 4GB (OOM em execuções consecutivas) | Conhecido (`INFRA-OOM-PATTERNS-KV-CACHE-01`, BRIEF). Por isso o proof T1-T5 é DEFERIDO para GPU exclusiva e roda 1 vez após cooldown; timeout de fase 900s e por-turno >= 120s dão folga ao 3b lento. |
| Asserção presa à prosa do 3b (frágil) | Mitigado: asserções miram infra (tool chamada, disco, formato da apresentação `Resultado:`), não o texto do modelo. |
| Adicionar `contrato` a `NEEDS_OLLAMA` faz o gauntlet completo falhar sem Ollama | Comportamento **correto e idêntico** às demais fases NEEDS_OLLAMA (`:427` registra `HEALTH` FAIL). O gauntlet completo já exige o stack vivo. |
| `NYX_AUTO_APPROVE=1` em automação | Já é o padrão do headless em CI/cockpit (`cli_headless.py:58`); log de aviso em stderr. Usado só dentro do subprocess da fase. |
| Tocar os guards 397-401 para "facilitar" o teste | NÃO-OBJETIVO. A fase EXERCE, nunca altera. Qualquer mudança em `nyx/agent/loop/` é violação de escopo. |

---

## Referências

- BRIEF: `/home/andrefarias/Desenvolvimento/Nyx-Code/VALIDATOR_BRIEF.md`
- Origem: auditoria de prontidão 2026-07-12, relatório durável `dev-journey/07-reports/AUDIT_2026_07_12.md` §3 (briefing efêmero da sessão de auditoria) (auditoria de prontidão 2026-07-12)
- Caminho headless real: `nyx/cli_headless.py:260` (`request`), `:64-67` (callback `on_tool`)
- Apresentação forte: `nyx/agent/loop/_core.py:569` (`_compose_presentation_summary`), `:605-606` (marcador `Resultado:`)
- Fase de referência (tool direto, sem modelo): `scripts/gauntlet/nyx_gauntlet.py:2969` (`_phase_e2e_real`)
- Roadmap: `dev-journey/06-sprints/SPRINT_ORDER_MASTER.md:1109` (`GAUNTLET-TOOLCHAIN-01`, Cobertura de Teste Ampliada)
- ADRs: ADR-007 (gauntlet único gate), ADR-032/033/034 (robustez na infra)

---

*"O gauntlet verde que nunca fala com o modelo é um espelho que só reflete a si mesmo. A fase 'contrato' obriga o espelho a olhar o usuário." -- princípio de cobertura (ADR-007)*
