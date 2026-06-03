# SPRINT LOOP-TOOL-ROUTING-CONSISTENCY-01 — unificar ActionType / aliases / ACTION_TO_TOOL

## 0. SPEC (machine-readable)

```yaml
sprint:
  id: LOOP-TOOL-ROUTING-CONSISTENCY-01
  title: "Parser fallback roteia write_memory/analyze/patch/repl; hoje caem em falha silenciosa por 3 tabelas divergentes"
  onda: 44
  bloco: "44 -- auditoria das ondas 36-43 (2026-06-03)"
  prioridade: MÉDIA
  tipo: Bugfix / Core loop
  dependencias: []
  desbloqueia: []

  touches:
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/agent/loop/_constants.py
      reason: "ACTION_TO_TOOL (linha 9-22) não tem WRITE_MEMORY, ANALYZE, PATCH, REPL (existem no enum ActionType). _execute_parsed_action faz ACTION_TO_TOOL.get() -> None -> aborta silencioso."
      linhas_alvo: "9-22 (ACTION_TO_TOOL)"
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/agent/parser.py
      reason: "_ACTION_ALIASES (linha 24+) não tem 'write_memory' (nem variações). O parser dá `return _fail` (linha 294) para o JSON do 3b com name='write_memory', então o caminho do parser fallback nunca grava memória."
      linhas_alvo: "24-72 (_ACTION_ALIASES)"
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/agent/loop/_iteration.py
      reason: "_execute_parsed_action (linha 282-285): quando ACTION_TO_TOOL.get() é None, retorna None com apenas logger.warning. Tornar o descarte VISÍVEL (add_tool_call informando que a ação não pôde ser roteada) em vez de sumir."
      linhas_alvo: "282-285"

  creates: []
  removes: []

  n_to_n_pairs:
    - descricao: "ActionType (enum, models.py), _ACTION_ALIASES (parser.py) e ACTION_TO_TOOL (_constants.py) descrevem o mesmo universo de tools roteáveis e divergem. Idealmente uma derivar da outra."  # noqa-acento
      paths:
        - /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/agent/models.py
        - /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/agent/parser.py
        - /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/agent/loop/_constants.py

  forbidden:
    - "Adicionar ao ACTION_TO_TOOL uma rota para um nome de tool que não existe no ToolRegistry (verificar registry)"
    - "Quebrar o roteamento já correto (read_file/write_file/edit_file/run_command/search/glob/list_files/done/web_*/todo_write)"
    - "Adicionar emoji ou menção a IA externa"

  tests:
    - cmd: "bash scripts/sprint_invariants.sh"
      timeout: 180
      esperado: "14/14 PASS"
    - cmd: "./run.sh --gauntlet --only rapido"
      timeout: 300
      esperado: "APROVADO (19/19)"
    - cmd: "probe determinístico: ActionParser.parse de um JSON write_memory(file,content,reason) -> ParseResult.success com action_type WRITE_MEMORY; _execute_parsed_action roteia para a tool real"
      timeout: 60
      esperado: "write_memory/analyze/patch roteiam; nenhum descarte silencioso"

  acceptance_criteria:
    - "Um tool_call write_memory emitido como JSON-no-content (formato do 3b) é roteado e executado pelo caminho do parser fallback"
    - "analyze e patch via parser fallback executam (ou, se intencional não suportá-los aí, o descarte é VISÍVEL no chat, não só log)"
    - "As 3 tabelas ficam coerentes (toda ActionType roteável tem alias E rota, ou está explicitamente fora)"
    - "Invariantes 14/14, gauntlet rápido APROVADO, ruff/acento OK"
```

---

**Status:** PENDENTE
**Data criação:** 2026-06-03
**Origem:** auditoria das ondas 36-43 (achado A3, severidade MÉDIA). O sintoma da ONDA-42 (#353: "write_memory não grava → memória cross-session quebrada") foi atribuído só ao modelo (ADR-034); parte é este roteamento.
**Modelo obrigatório:** claude-opus (sem subagentes)

---

## Contexto do projeto (snapshot — não referência)

> - ADR-032 A infra carrega o modelo: a infra deve rotear consistentemente o que o modelo emite; rede dedicada frágil no proxy (regex para write_memory) é sintoma de roteamento incompleto na raiz.
> - O qwen2.5-coder:3b emite tool calls como **JSON-no-content** (ADR-031). Os logs confirmam que o **caminho do parser fallback é o primário** do 3b (31 usos num dia: function_call, bare_tool, code_block, implicit_done).
> - `write_memory` hoje só funciona porque o proxy tem um remendo dedicado (MEMORY-INTENT-ENFORCE-01, `proxy.py:776`) que captura o formato do 3b — e só dispara quando o usuário usa verbo de memória explícito.

---

## Problema

Três tabelas que descrevem o mesmo universo de tools divergem:

| Tool | no enum `ActionType`? | tem alias no parser? | tem rota em `ACTION_TO_TOOL`? | resultado via parser fallback |
|------|:--:|:--:|:--:|---|
| `write_memory` | sim | **não** | **não** | parser dá `return _fail` (parser.py:294) → não grava |
| `analyze` | sim | sim | **não** | `_execute_parsed_action` aborta silencioso (_iteration.py:282-285) |
| `patch` | sim | sim | **não** | idem |
| `repl` | sim | não | **não** | não roteia |
| read/write/edit/run/search/glob/list/done/web_*/todo_write | sim | sim | sim | OK |

`_execute_parsed_action` (`_iteration.py:282-285`):

```python
tool_name = ACTION_TO_TOOL.get(action.action_type)
if not tool_name:
    logger.warning("[loop] sem tool para %s", action.action_type.value)
    return None      # <-- descarte SILENCIOSO (só log); o usuário não vê
```

O grep por `"sem tool para"` nos logs veio vazio: `analyze`/`patch` quase não são emitidos pelo 3b (bug latente). `write_memory` é mais sensível porque a memória cross-session é feature central; hoje depende inteiramente do remendo do proxy.

---

## Causa-raiz

O roteamento de tools via parser fallback é montado por **subconjunto manual** (`ACTION_TO_TOOL`) e a tabela de aliases por **outro subconjunto manual** (`_ACTION_ALIASES`), ambos menores que o enum `ActionType`. Tools adicionadas ao enum sem entrada nas duas outras tabelas viram caminho de falha silenciosa. `write_memory` nunca teve alias; foi remendado só no proxy.

---

## Solução proposta

1. Adicionar `write_memory` ao `_ACTION_ALIASES` (`"write_memory" / "memoria" / "lembrar"` → `ActionType.WRITE_MEMORY`).
2. Adicionar ao `ACTION_TO_TOOL` as rotas faltantes para tools que existem no `ToolRegistry`: `WRITE_MEMORY → "write_memory"`, `ANALYZE → "analyze"`, `PATCH → "patch"`, `REPL → "repl"` (confirmar cada nome no registry antes).
3. Tornar o descarte VISÍVEL: quando `ACTION_TO_TOOL.get()` for `None`, `add_tool_call(name, args, "ação não roteável: <nome>")` em vez de só `logger.warning` — assim qualquer lacuna futura aparece ao usuário/validador (princípio ADR-026), não some.
4. (Opcional, maior valor a longo prazo) derivar `ACTION_TO_TOOL` de uma fonte única para impedir nova divergência.

---

## Proof-of-work esperado (runtime real)

```bash
bash scripts/sprint_invariants.sh                       # 14/14 PASS
./run.sh --gauntlet --only rapido                       # APROVADO
python3 ~/.config/zsh/scripts/validar-acentuacao.py --paths nyx/agent/loop/_constants.py nyx/agent/parser.py nyx/agent/loop/_iteration.py
# probe: ActionParser().parse('{"name":"write_memory","arguments":{"file":"x","content":"y","reason":"z"}}')
#        -> success, action_type=WRITE_MEMORY ; ACTION_TO_TOOL[WRITE_MEMORY]=="write_memory"
```

Idealmente: runtime real (proxy + 3b) pedindo gravação de memória ESPONTÂNEA (sem verbo de memória explícito, para escapar do remendo do proxy) e confirmando que `~/.nyx/.../memory` recebeu o arquivo.

---

## Critério binário de aceite

- [ ] `write_memory` roteia pelo parser fallback (não só pelo remendo do proxy)
- [ ] `analyze`/`patch`/`repl` roteiam, OU o descarte é visível no chat
- [ ] As 3 tabelas ficam coerentes (documentado quem está dentro/fora e por quê)
- [ ] Roteamento já correto intacto (regressão zero no gauntlet rápido)
- [ ] Invariantes 14/14, ruff/acento OK; spec movida para `concluidos/`

---

## Riscos

| Risco | Mitigação |
|-------|-----------|
| Adicionar rota para tool com nome errado | Confirmar cada nome em `ToolRegistry`/`nyx/agent/tools/*.py` antes |
| Colisão com o remendo do proxy (write_memory roteado 2x) | O proxy normaliza para tool_call nativo (caminho `_execute_tool_calls`), o parser só age quando o nativo está vazio — caminhos mutuamente exclusivos por turno |

---

*"Três mapas do mesmo território que discordam são pior que nenhum mapa." -- anônimo*
