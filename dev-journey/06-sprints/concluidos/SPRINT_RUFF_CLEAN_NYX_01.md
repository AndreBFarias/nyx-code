# SPRINT RUFF-CLEAN-NYX-01 -- 58 violações em nyx/ pós-upgrade ruff 0.15.10 -> 0.15.13

## 0. SPEC

```yaml
sprint:
  id: RUFF-CLEAN-NYX-01
  title: "Restaurar invariante #10 (ruff limpo) após upgrade 0.15.10 -> 0.15.13"
  onda: 25
  bloco: 25.1 Resiliência do gauntlet (anti-débito derivado de GAUNTLET-ACENTUACAO-FIX-01)
  prioridade: ALTA
  tipo: Limpeza de débito técnico
  dependencias: []
  desbloqueia: [GAUNTLET-ACENTUACAO-FIX-01, gauntlet completo gate v1.0]

  touches:
    - nyx/agent/repl_app.py
    - nyx/agent/banner.py
    - nyx/cli.py
    - nyx/agent/commands/_registry.py
    - nyx/agent/output.py
    - nyx/agent/persistence.py
    - nyx/agent/validator.py
    - nyx/agent/services/hook_runtime.py
    - nyx/proxy.py
    - nyx/cockpit/server.py
    - nyx/cli_helpers.py

  creates: []
  removes: []

  forbidden:
    - "Mexer em lógica de negócio — só limpeza de imports/lints"
    - "Remover imports usados sob try/except (preservar try-import disponibilidade)"
    - "Quebrar multi-imports legítimos em N imports separados (ex: design_tokens block em repl_app.py)"
```

---

**Status:** CONCLUIDA
**Data spec:** 2026-05-19 (segunda sessão)
**Data conclusão:** 2026-05-19 (segunda sessão, ~22h36)
**Modelo execução:** claude-opus-4-7

---

## Contexto

Durante execução de `GAUNTLET-ACENTUACAO-FIX-01`, o invariante #10 (`python3 -m ruff check nyx/`) passou de PASS para FAIL. Stash dos edits da sprint atual confirmou: erro pré-existente em a6c87be. Causa: cache `.ruff_cache/0.15.13` criado às 22:26 durante a sessão (provavelmente upgrade automático de pacote). Ruff 0.15.13 introduziu detecção mais estrita, expondo 58 violações latentes em `nyx/`.

## Inventário das 58 violações

| Regra | Count | Significado | Estratégia |
|-------|------:|-------------|-----------|
| I001  | 16 | Import block unsorted | `ruff --fix` |
| E402  | 16 | Import after statement | `ruff --fix` + reorg logger/imports |
| F541  | 4 | f-string sem placeholder | `ruff --fix` |
| F401  | 17 | Import unused | `ruff --fix` + Edit cirúrgico em ANSI |
| F841  | 3 | Variable assigned but unused | Edit cirúrgico (delete/underscore-prefix) |
| E501  | 2 | Line too long (>120) | Edit cirúrgico (multi-line ou `# noqa: E501`) |

## Plano executado

### Passo 1: autofix seguro
```bash
python3 -m ruff check --fix nyx/
# 34 fixes aplicados, 24 restantes
```

### Passo 2: reverter explosão de multi-import em repl_app.py
Ruff explodiu `from nyx.themes.design_tokens import (A as _A, B as _B, C as _C, ...)` em 6 imports separados — comportamento absurdo de I001 quando há aliases. Revertido manualmente com `# noqa: I001` no head do bloco para preservar legibilidade.

### Passo 3: E402 em repl_app.py
12 imports estavam após `logger = logging.getLogger(__name__)` em L30. Movido `logger = ...` para depois dos imports do prompt_toolkit (idiomático).

### Passo 4: E402 em banner.py
`from nyx.themes.theme_manager import current_ansi` estava na L35 depois de assignments de `_TJOIN/_BJOIN/...`. Movido para o bloco de imports superior.

### Passo 5: F841 em banner.py + cli.py
- `ports_box` (banner.py L204): código morto, removido.
- `warmup_task` (cli.py L376): fire-and-forget background task, renomeado `_warmup_task` com `# noqa: F841 -- ref viva contra GC`.

### Passo 6: F401 ANSI em cli.py
`from prompt_toolkit.formatted_text import ANSI` em L213 era unused (existem dois locais com `from ... import ANSI as _ANSI`). Removido — try/except de prompt_toolkit já testa disponibilidade via outros imports.

### Passo 7: E501 (5 lugares)
- `_registry.py:94` (tupla literal): `# noqa: E501`
- `output.py:791/793` (f-string com 8 vars): `# noqa: E501`
- `persistence.py:94` (list comprehension): quebrado em multi-line
- `validator.py:109` (chain de OR): quebrado em multi-line com parênteses

### Passo 8: 1 violação de acentuação periférica achada
`nyx/agent/output.py:601` tinha `"nao encontrado"` intencional (cobrir variante sem acento do modelo). Adicionado `# noqa-acento` seguindo padrão de `nyx/agent/lang_check.py`.

## Proof-of-work runtime

- `python3 -m ruff check nyx/` -> **All checks passed!** (era: Found 58 errors)
- `bash scripts/sprint_invariants.sh` -> 14/14 PASS (era: 13/14 com #10 FAIL)
- `./run.sh --smoke` -> `boot ok` antes e depois
- `./run.sh --gauntlet --only rapido` -> 17/18 (P-07 pré-existente, zero regressão por RUFF-CLEAN)
- `validar-acentuacao.py --paths` nos 11 arquivos -> exit 0 (era 1 violação em output.py:601, suprimida com noqa-acento)
- AST parse OK em todos os 11 arquivos

## Anti-débito catalogado

**RUFF-EXTERNAL-NOQA-CONFIG-01** (BAIXA, futuro): configurar `[tool.ruff.lint] external = ["noqa-acento"]` em `pyproject.toml` para suprimir warnings `Invalid noqa directive` que aparecem em arquivos que usam o marker customizado `# noqa-acento` (validar-acentuacao.py). Atualmente são apenas warnings (exit=0), não bloqueiam, mas poluem output.

## Referências

- `VALIDATOR_BRIEF.md` (raiz do repo) — invariantes obrigatórios
- `scripts/sprint_invariants.sh:169-179` — definição do check #10
- `nyx/agent/lang_check.py:29-40` — padrão de uso de `# noqa-acento`
- `pyproject.toml` (raiz) — configuração ruff atual
- `feedback_nenhum_debito.md` — protocolo anti-débito

---

*"Upgrade de linter é mudança silenciosa de contrato. Catalogar e limpar é nyx-protocolo." -- RUFF-CLEAN-NYX-01*
