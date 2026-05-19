# SPRINT INFRA-CLI-SPLIT-03 — Reduzir nyx/cli.py para <800L (continuação anti-débito)

## 0. SPEC

```yaml
sprint:
  id: INFRA-CLI-SPLIT-03
  title: "Extrair run_headless + boot pieces de nyx/cli.py para cli_headless.py + cli_boot.py"
  onda: 23
  bloco: 23.1 Estabilização
  prioridade: BAIXA
  tipo: Refactor
  dependencias: [INFRA-CLI-SPLIT-02]
  origem: |
    INFRA-CLI-SPLIT-02 concluiu CONCLUIDA_PARCIAL: cli.py 2223L -> 1328L
    (40% reduction). Meta GUIDE.md §6 é 800L; ainda 528L acima. Extrações
    pendentes mais óbvias: `run_headless()` (278L) e blocos de boot
    (sandbox init, warmup, blink_cursor, prompt str builder).

  touches:
    - /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/cli.py
  creates:
    - /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/cli_headless.py
    - /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/cli_boot.py

  acceptance_criteria:
    - "wc -l nyx/cli.py < 800"
    - "Smoke + invariantes 14/14 + gauntlet rapido + interface + proxy 100%"
    - "Zero mudança de comportamento externo do REPL nem do headless"
    - "Zero import circular entre cli_*.py"
    - "Pipeline `--headless` continua aceitando JSON e /slash commands"
```

---

## 1. Plano de implementação

### 1.1 nyx/cli_headless.py (~280L)

Extrair `async def run_headless() -> int` integral. Atualmente está em
`nyx/cli.py:985-1262`. Dependências externas:
- `AgentLoop` (já importado no caller)
- `save_session`, `load_settings`
- Tools.base (set_active_project_root, add_extra_root, etc.)
- `PROJECT_ROOT` — passar como parâmetro
- `logger` — pode reaproveitar via `get_logger("nyx.cli")` local

API:
```python
async def run_headless(project_root: Path, logger_: Logger) -> int:
    """Mesmo comportamento; argumentos antes implícitos viram explícitos."""
```

`cli.py` chama: `asyncio.run(run_headless(PROJECT_ROOT, logger))`.

### 1.2 nyx/cli_boot.py (~120L)

Boot pieces antes do laço do REPL:
1. `init_sandbox_roots(settings, project_root, logger)` -- bloco set_active +
   add_extra_root + warning de paths inválidos (cli.py:135-150).
2. `compute_prompt_str(app_state, model, schema, accent, bold, nc)` -- builder
   do `prompt_str` da linha 588-617 (após o app_state ser populado a cada turno).
3. `build_handler_ctx_factory(...)` opcional -- factory de HandlerCtx, eliminando
   a duplicação dos 13 args na assinatura do dataclass; só extrair se reduzir
   mais de 30 linhas.

### 1.3 cli.py final

Vai conter:
- Imports + cores ANSI + `_STATE_GLYPHS` + `_MODES` (invariante 14).
- `maybe_offer_resume` wrapper (5L).
- `run_repl` enxuto (~650L, esperado).
- `main()` (60L).

Total esperado: ~720-780L.

---

## 2. Cuidados

- `run_headless` muta `agent._project_root` em `/cd`. Após extrair, esse
  comportamento permanece igual (a função recebe `agent` local; não há
  state externo). Sandbox helpers continuam globais (módulo singleton).
- Importações `prompt_toolkit` em `cli.py` ficam apenas na parte do REPL
  (já são lazy via try/except ImportError).
- Cuidado com circular: `cli_headless.py` NÃO importa `cli.py`. Importa
  apenas `nyx.agent.*`, `nyx.config.*`, e o handler dispatcher de
  cli_handlers.py se quiser reutilizar.

---

## 3. Validação

```
./run.sh --smoke                              # boot ok
bash scripts/sprint_invariants.sh             # 14/14
./run.sh --gauntlet --only rapido             # 100%
./run.sh --gauntlet --only interface          # 5/5
./run.sh --gauntlet --only proxy              # 100%
echo '{"type":"ping"}' | ./venv/bin/python nyx/cli.py --headless   # pong
echo '/sandbox list' | ./venv/bin/python nyx/cli.py --headless     # roots listados
wc -l nyx/cli.py                              # <800
```

---

**Status:** PENDENTE
**Data:** 2026-05-19
**Origem:** anti-débito de INFRA-CLI-SPLIT-02 (corte parcial; chegamos a 1328L; meta 800L)
**Modelo obrigatório:** claude-opus-4-7 (sem subagentes)
