## 0. SPEC

```yaml
sprint:
  id: DEBT-07
  title: "Completar exportações públicas pós-split loop.py (DEBT-01 residual)"
  onda: 22
  bloco: 2.5
  prioridade: ALTA
  tipo: Bugfix
  dependencias: []
  desbloqueia: [INFRA-GAUNTLET-01]

  touches:
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/agent/loop/__init__.py
      reason: "Reexportar símbolos privados/públicos consumidos por terceiros (gauntlet, scripts, testes) que deixaram de ser acessíveis após o split de DEBT-01"

  creates: []
  removes: []

  forbidden:
    - "Alterar nyx/agent/loop/_constants.py"
    - "Alterar nyx/agent/loop/_iteration.py"
    - "Alterar nyx/agent/loop/_core.py"
    - "Alterar nyx/agent/loop/_types.py"
    - "Alterar scripts/gauntlet/nyx_gauntlet.py (fix é no exporter, não no importador)"
    - "Expandir escopo para refatorar a API pública do loop — só reexportar o que já é importado por terceiros"
    - "Absorver silenciosamente outros buracos de DEBT-01 encontrados na auditoria; se houver outros, registrar sprint nova (AUDIT-FIX-10)"

  tests:
    - cmd: "./run.sh --gauntlet --only rapido"
      timeout: 300
      deve_passar: true
    - cmd: "python -c 'from nyx.agent.loop import _remap_params; assert callable(_remap_params)'"
      deve_passar: true

  acceptance_criteria:
    - "Todo símbolo importado por terceiros via 'from nyx.agent.loop import X' resolve sem ImportError"
    - "nyx/agent/loop/__init__.py contém todos os símbolos necessários no __all__ e nos imports"
    - "Gauntlet 'rapido' passa 100% sem ImportError em nenhuma fase"
    - "Auditoria dos imports externos colada no relatório (grep output literal)"
    - "Zero alteração em módulos de produção fora do __init__.py do pacote loop"
    - "FAIL_AFTER <= FAIL_BEFORE no sprint_invariants.sh"
```

---

# Sprint DEBT-07 — Completar exportações públicas pós-split loop.py

**Status:** CONCLUIDA (header corrigido em MASTER-CLEANUP-02 2026-05-20; presença em concluidos/ implica CONCLUIDA conforme convenção do projeto)
**Data criação:** 2026-04-19
**Modelo obrigatório:** claude-opus-4-7 (sem subagentes)

---

## Contexto do projeto (snapshot)

> **ADRs relevantes:**
> - ADR-013 Integração Obrigatória: nada solto, API pública clara.
> - ADR-014 Testes via Gauntlet: fix validado via `./run.sh --gauntlet --only rapido`.
> - ADR-020 Testes via run.sh: proibido chamar gauntlet direto.
>
> **Estado do sistema (2026-04-19):**
> - Bloco 2 Onda 22 splitou `nyx/agent/loop.py` em pacote `nyx/agent/loop/` com módulos `_constants.py`, `_core.py`, `_iteration.py`, `_types.py` (DEBT-01, commit 43cf4d2).
> - `__init__.py` atual reexporta apenas `AgentLoop`, `PermissionCallback`, `SessionState`, `SessionStatus`, `ACTION_TO_TOOL`, `PARAM_REMAP`, `LLM_TIMEOUT`.
> - `_remap_params` (função em `_constants.py:35`) **não foi reexportada**, causando `ImportError` quando `scripts/gauntlet/nyx_gauntlet.py:1224` faz `from nyx.agent.loop import _remap_params`.
> - Bug dormiu até INFRA-GAUNTLET-01 rodar o gauntlet completo — crash na fase 15 (`e2e_real` ou subsequente), abortando 37 das 51 fases.

---

## Problema

Gauntlet crasha com:
```
File "/home/andrefarias/Desenvolvimento/Nyx-Code/scripts/gauntlet/nyx_gauntlet.py", line 1224, in _phase_e2e
    from nyx.agent.loop import _remap_params
ImportError: cannot import name '_remap_params' from 'nyx.agent.loop'
```

DEBT-01 movou `_remap_params` de `loop.py` para `loop/_constants.py` mas não reexportou via `__init__.py`. O gauntlet completo nunca foi rodado pós-refactor (OOM de VRAM abortava antes da fase 15), então o bug passou desapercebido.

Possível haver outros símbolos na mesma situação — a sprint obriga auditoria sistemática, não só `_remap_params`.

---

## Solução proposta

1. Auditar todos os `from nyx.agent.loop import X` no repositório.
2. Para cada `X` ausente do `__all__` ou dos imports do `__init__.py`, adicionar.
3. Rodar `./run.sh --gauntlet --only rapido` para verificar que não há mais `ImportError` nas fases cobertas.

---

## Arquivos alvo

### `/home/andrefarias/Desenvolvimento/Nyx-Code/nyx/agent/loop/__init__.py`

**Antes:**
```python
"""Pacote nyx.agent.loop -- AgentLoop e tipos públicos."""

from nyx.agent.loop._constants import ACTION_TO_TOOL, LLM_TIMEOUT, PARAM_REMAP
from nyx.agent.loop._core import AgentLoop
from nyx.agent.loop._types import PermissionCallback, SessionState, SessionStatus

__all__ = [
    "AgentLoop",
    "PermissionCallback",
    "SessionState",
    "SessionStatus",
    "ACTION_TO_TOOL",
    "PARAM_REMAP",
    "LLM_TIMEOUT",
]
```

**Depois (exemplo — lista final depende da auditoria):**
```python
"""Pacote nyx.agent.loop -- AgentLoop e tipos públicos."""

from nyx.agent.loop._constants import (
    ACTION_TO_TOOL,
    CORE_TOOLS,
    LLM_TIMEOUT,
    PARAM_REMAP,
    TOOL_KEYWORDS,
    _remap_params,
)
from nyx.agent.loop._core import AgentLoop
from nyx.agent.loop._types import PermissionCallback, SessionState, SessionStatus

__all__ = [
    "AgentLoop",
    "PermissionCallback",
    "SessionState",
    "SessionStatus",
    "ACTION_TO_TOOL",
    "CORE_TOOLS",
    "PARAM_REMAP",
    "LLM_TIMEOUT",
    "TOOL_KEYWORDS",
    "_remap_params",
]
```

**Mudanças:**
- Adicionar ao import todos os símbolos identificados pela auditoria.
- Espelhar no `__all__`.
- Ordenar alfabeticamente para estabilidade do diff.

---

## Método de auditoria (obrigatório)

```bash
# 1. Listar todos os imports do pacote loop em código externo ao próprio pacote
grep -rn "from nyx.agent.loop import" \
    --include="*.py" \
    /home/andrefarias/Desenvolvimento/Nyx-Code \
    | grep -v "nyx/agent/loop/"

# 2. Para cada import encontrado, extrair os símbolos e cruzar com o __all__ atual
python -c "from nyx.agent.loop import __all__; print(__all__)"

# 3. Confirmar que cada símbolo ausente do __all__ está definido em algum submódulo
grep -n "^def \|^class \|^[A-Z_][A-Z0-9_]* = " nyx/agent/loop/_constants.py nyx/agent/loop/_core.py nyx/agent/loop/_iteration.py nyx/agent/loop/_types.py
```

**Colar no relatório final:**
- Output literal dos 3 comandos acima (antes e depois).
- Lista de símbolos adicionados ao `__all__`.
- Justificativa de 1 linha para cada: "símbolo X importado em arquivo Y:linha Z".

---

## Diff esperado (resumo)

```
~ 1 arquivo modificado (nyx/agent/loop/__init__.py)
+ ~10 linhas líquidas (imports + __all__)
```

---

## Comandos de verificação

```bash
# 1. Auditoria
grep -rn "from nyx.agent.loop import" --include="*.py" . | grep -v "nyx/agent/loop/"

# 2. Smoke test import direto
python -c "from nyx.agent.loop import _remap_params; assert callable(_remap_params); print('ok')"

# 3. Linter
python -m ruff check nyx/agent/loop/

# 4. Gauntlet rápido
./run.sh --gauntlet --only rapido
```

---

## Critério binário de aceite

- [ ] Auditoria executada e output colado no relatório
- [ ] Todo símbolo importado externamente está em `__all__` e nos imports do `__init__.py`
- [ ] `python -c "from nyx.agent.loop import _remap_params"` não levanta ImportError
- [ ] `./run.sh --gauntlet --only rapido` passa 100%
- [ ] `ruff` limpo
- [ ] FAIL_AFTER <= FAIL_BEFORE no `sprint_invariants.sh`
- [ ] Commit atômico: `fix: reexporta símbolos pós-split loop.py (resíduo de DEBT-01)`
- [ ] SPRINT_ORDER_MASTER.md linha 18 (DEBT-07) marcada CONCLUIDA com hash
- [ ] INFRA-GAUNTLET-01 volta a PENDENTE na linha 19 (mantém DEBT-07 nas deps, remove nota BLOQUEADA)
- [ ] Sprint movida de `producao/` para `concluidos/`

---

## Gambiarras específicas desta sprint

- **Fix local em vez de auditoria completa.** Adicionar só `_remap_params` sem varrer os outros símbolos. **Detectar:** output do grep no relatório deve cobrir todos os arquivos que importam de `nyx.agent.loop`, não só o gauntlet.
- **Mudar o importador.** Editar `scripts/gauntlet/nyx_gauntlet.py:1224` trocando `from nyx.agent.loop import _remap_params` por `from nyx.agent.loop._constants import _remap_params`. **Proibido:** fix é no exporter público, não em cada consumidor. Exporta quem expõe API.
- **Inflar o `__all__` com símbolos privados não consumidos.** Adicionar tudo que está em `_constants.py` mesmo sem uso externo. **Regra:** só reexportar o que de fato é importado por código externo (auditoria prova).
- **Absorver buracos vizinhos no escopo.** Se a auditoria revelar outros defeitos de DEBT-01 (ex.: símbolo em `_iteration.py` não reexportado, função renomeada sem ajuste em caller), **proibido** fixar inline. Registrar como AUDIT-FIX-10 em sprint nova. Esta sprint só fecha imports ausentes no `__init__.py` do pacote loop.
- **Declarar CONCLUIDA sem rodar gauntlet.** Proibido. Gauntlet `--only rapido` é obrigatório no proof-of-work.

---

## Proof-of-work obrigatório

```bash
# PASSO 1
bash scripts/sprint_invariants.sh > /tmp/inv_before.txt 2>&1
FAIL_BEFORE=$(grep -c "^\[FAIL\]" /tmp/inv_before.txt)

# PASSO 2 — implementação

# PASSO 3
bash scripts/sprint_invariants.sh > /tmp/inv_after.txt 2>&1
FAIL_AFTER=$(grep -c "^\[FAIL\]" /tmp/inv_after.txt)

# PASSO 4 — FAIL_AFTER <= FAIL_BEFORE; diff colado no relatório
diff /tmp/inv_before.txt /tmp/inv_after.txt
```

---

## Validação humana

```bash
cd /home/andrefarias/Desenvolvimento/Nyx-Code

# 1. Diff do commit
git log --oneline -1
git show --stat HEAD

# 2. Smoke test
python -c "from nyx.agent.loop import _remap_params; print('ok:', _remap_params)"
# esperado: "ok: <function _remap_params at ...>"

# 3. Gauntlet rápido
./run.sh --gauntlet --only rapido
# esperado: pass rate 100%, zero ImportError

# 4. Arquivos movidos
ls dev-journey/06-sprints/concluidos/SPRINT_DEBT_07.md   # deve existir
ls dev-journey/06-sprints/producao/SPRINT_DEBT_07.md     # NÃO deve existir
```

---

## Riscos

| Risco | Mitigação |
|-------|-----------|
| Auditoria revela mais símbolos faltando além de `_remap_params` | Reexportar todos; listar cada um no relatório. Escopo permite porque todos são parte do mesmo defeito de DEBT-01. |
| Auditoria revela defeito diferente (ex.: função mudou de assinatura) | Registrar como AUDIT-FIX-10 em sprint nova, NÃO fixar inline. |
| `__all__` cresce e vira leak de API privada | Só reexportar o que o grep provou ser consumido externamente. Símbolo com `_` no nome (convenção privada) que já é importado por terceiro vira parte da API pública de-facto — decisão é explícita no relatório. |
| Gauntlet `rapido` não cobre a fase que explodiu | A fase original era `e2e_real` ou pós-`e2e`. Validar via smoke test `python -c "from nyx.agent.loop import _remap_params"` é condição necessária; INFRA-GAUNTLET-01 (gauntlet completo) é quem vai validar de ponta a ponta. |

---

*"Todo símbolo que um outro módulo chama faz parte da sua API pública, goste você ou não." -- Hyrum Wright (paráfrase)*
