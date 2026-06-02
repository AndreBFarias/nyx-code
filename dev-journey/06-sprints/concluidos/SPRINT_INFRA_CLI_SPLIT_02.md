# SPRINT INFRA-CLI-SPLIT-02 — Reduzir nyx/cli.py para <800L (anti-débito)

## 0. SPEC

```yaml
sprint:
  id: INFRA-CLI-SPLIT-02
  title: "Extrair handlers de sentinela e keybindings de run_repl para cli_handlers.py + cli_keybindings.py"
  onda: 23
  bloco: 23.1 Estabilização
  prioridade: BAIXA
  tipo: Refactor
  dependencias: [INFRA-CLI-SPLIT-01]
  origem: "INFRA-CLI-SPLIT-01 extraiu helpers (cli_helpers.py) e reduziu cli.py de 1450 -> 1361 linhas. Limite GUIDE.md §6 é 800L; ainda 561L acima. Refactor maior requer cuidado com closures e estado compartilhado de run_repl."

  touches:
    - /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/cli.py
  creates:
    - /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/cli_handlers.py
    - /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/cli_keybindings.py

  acceptance_criteria:
    - "wc -l nyx/cli.py < 800"
    - "Smoke + gauntlet rapido + p7_tui + interface 100%"
    - "Zero mudança de comportamento externo do REPL"
    - "Zero import circular entre cli_*.py"
```

---

**Status:** CONCLUIDA (reconciliada em AUDIT-SPRINT-STATUS-RECONCILE-01 2026-06-02; meta 800L fechada pela cadeia CLI-SPLIT-03, cli.py=713L)
**Data:** 2026-05-17 (criada) / 2026-05-19 (executada)
**Origem:** anti-débito de INFRA-CLI-SPLIT-01 (corte parcial; chegamos a 1361L; meta 800L)
**Modelo obrigatório:** claude-opus-4-7 (sem subagentes)

---

## Execução (2026-05-19)

### Resultado

**wc -l nyx/cli.py:**
- ANTES: 2223L (cli.py cresceu após INFRA-CLI-SPLIT-01 com novos sentinels da Onda 28)
- DEPOIS: 1328L
- Delta: -895L (-40%)
- Meta `<800L`: **NÃO ATINGIDA** (528L acima)

### Módulos criados

- **nyx/cli_keybindings.py (328L):** `build_keybindings()`, `build_bottom_toolbar()`,
  `build_prompt_style()`. KeyBindings carregam closures sobre app_state, last_input_state,
  image_map, image_counter. Bottom toolbar respeita SHIFT-TAB-CYCLE-01 + UX-AGENCY-02 +
  invariante 14 (_STATE_GLYPHS continuam em cli.py).
- **nyx/cli_handlers.py (950L):** dataclass `HandlerCtx` + 40 handlers de sentinela
  (`_handle_clear`, `_handle_status`, ..., `_handle_mcp_test`). Dispatcher `dispatch_sync`
  itera lista de handlers síncronos; `dispatch_async` cobre MCP. `__quit__` permanece
  em cli.py (shutdown encadeia com proxy admin endpoint + save_session + asyncio.gather).
- **scripts/sprint_invariants.sh:** invariante #3 estendido para aceitar
  `nyx/cli*.py` glob (cli.py + cli_helpers.py + cli_keybindings.py + cli_handlers.py).
  ADR-024 amendado em sincronia.
- **dev-journey/03-decisions/ADR_024_RENDER_LAYER.md:** adicionada cláusula explicando
  que cli_*.py compartilha o papel de orquestração de REPL — mesmo print() permitido,
  pela mesma razão (rejected Alt A revisited).

### Proof-of-work

```
./run.sh --smoke                              -> boot ok
bash scripts/sprint_invariants.sh             -> PASS=14, FAIL=0
./run.sh --gauntlet --only rapido             -> 18/18 (100%) APROVADO
./run.sh --gauntlet --only interface          -> 5/5 (100%) APROVADO
./run.sh --gauntlet --only proxy              -> 6/6 (100%) APROVADO
./venv/bin/python -c "from nyx.cli import *"  -> ok
validar-acentuacao.py --paths nyx/cli*.py     -> zero violações
```

### Decisão anti-débito

Meta `<800L` não foi atingida com a primeira passada de extração porque cli.py
cresceu 600L entre SPLIT-01 e SPLIT-02 (Onda 28 adicionou múltiplos sentinels
de tema/aesthetic/schema/select e novos handlers de boot via Application).
Promovida **SPRINT_INFRA_CLI_SPLIT_03** com plano explícito para extrair
`run_headless` (278L) + boot pieces. Esperado fechar em ~720-780L na próxima
iteração.

### Achados colaterais

- Nenhum bug pré-existente detectado durante a extração.
- ADR-024 já previa "qualquer arquivo futuro que queira escrever UI direto
  precisa de nova ADR. Isolamento por convenção, não por linter" — a
  extensão para cli_*.py honra esse contrato.

### Touches/creates finais (incluindo periféricos necessários)

- nyx/cli.py (modificado, -895L)
- nyx/cli_keybindings.py (novo, 328L)
- nyx/cli_handlers.py (novo, 950L)
- scripts/sprint_invariants.sh (amendado: invariante #3 glob)
- dev-journey/03-decisions/ADR_024_RENDER_LAYER.md (amendado: cláusula cli_*.py)
- dev-journey/06-sprints/SPRINT_ORDER_MASTER.md (linha 127b adicionada)
- dev-journey/06-sprints/producao/SPRINT_INFRA_CLI_SPLIT_03.md (novo, anti-débito)
