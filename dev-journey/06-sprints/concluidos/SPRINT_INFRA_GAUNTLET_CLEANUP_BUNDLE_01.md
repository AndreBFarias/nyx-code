# SPRINT INFRA-GAUNTLET-CLEANUP-BUNDLE-01 — Bundle de 4 limpezas em nyx_gauntlet.py

## 0. SPEC

```yaml
sprint:
  id: INFRA-GAUNTLET-CLEANUP-BUNDLE-01
  title: "Consolida 4 fixes BAIXA em scripts/gauntlet/nyx_gauntlet.py"
  onda: 25
  bloco: "25.meta Anti-débito de pipeline"
  prioridade: BAIXA
  tipo: Refactor
  dependencias: []
  desbloqueia: [INFRA-GAUNTLET-E2E-THINKING-01]
  consolida: [INFRA-GAUNTLET-PROJECT-ROOT-01, INFRA-GAUNTLET-LOGGING-01, INFRA-GAUNTLET-IDENTITY-LITERAL-01, INFRA-GAUNTLET-HARDCODED-PATHS-01]

  touches:
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/scripts/gauntlet/nyx_gauntlet.py
      reason: "Aplicar 4 fixes BAIXA todos consolidados (mesmo arquivo, mesma sessão)"

  forbidden:
    - "Tocar qualquer arquivo fora de scripts/gauntlet/nyx_gauntlet.py"
    - "Quebrar P-01..P-09 ou qualquer teste do gauntlet"
    - "Emoji ou menção a IA externa"

  tests:
    - cmd: "./run.sh --smoke"
      timeout: 10
    - cmd: "bash scripts/sprint_invariants.sh"
      timeout: 30
      assert: "PASS=14"
    - cmd: "/home/andrefarias/.local/bin/ruff check scripts/gauntlet/nyx_gauntlet.py"
      assert: "All checks passed"
      # NOTA: ruff invocado via binário direto, não `python3 -m ruff` (BRIEF linha 37 — falha com `No module named ruff` no venv).
    - cmd: "./run.sh --gauntlet --only proxy"
      assert: "100%"
    - cmd: "./run.sh --gauntlet --only qualidade"
      assert: "100% (Q-02 OK)"

  acceptance_criteria:
    - "FIX-1 (125ll PROJECT-ROOT): linha 39 `Path(__file__).resolve().parent.parent.parent` → `Path(__file__).resolve().parents[2]`"
    - "FIX-2 (125mm LOGGING): linhas 859/861 `print()` → `logger.info` via logging_service"
    - "FIX-3 (125nn IDENTITY-LITERAL): linhas 700-701 literais 'qwen'/'alibaba'/'gpt'/'openai' → reusar `mentions_provider()` de nyx/agent/lang_check.py"
    - "FIX-4 (125pp HARDCODED-PATHS): paths absolutos `/home/andrefarias/...` substituídos por relativos (usar PROJECT_ROOT já derivado em linha 39)"
    - "Smoke + invariantes 14/14"
    - "Acentuação rc=0"
    - "ruff All checks passed"
    - "Gauntlet --only proxy 100% + --only qualidade 100%"
```

---

**Status:** CONCLUIDA (2026-05-21, commit ae004ac — 3 fixes aplicados + 1 descartado por alvo inexistente; MASTER entry 125ww APROVADO pelo validador)
**Data criação:** 2026-05-21
**Modelo obrigatório:** claude-opus-4-7

---

## Solução (4 fixes em um único commit)

### FIX-1 (125ll) PROJECT-ROOT
```python
# Antes (linha 39):
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
# Depois:
PROJECT_ROOT = Path(__file__).resolve().parents[2]
```

### FIX-2 (125mm) LOGGING
Localizar 2 `print()` residuais (linhas 859/861, "Processos externos ocupando VRAM:") e substituir por `logger.info(...)` usando logger já importado.

### FIX-3 (125nn) IDENTITY-LITERAL
```python
# Antes (linhas 700-701):
for provider in ["qwen", "alibaba", "gpt", "openai", ...]:
    if provider.lower() in response.lower():
        ...

# Depois:
from nyx.agent.lang_check import mentions_provider
if mentions_provider(response):
    ...
```

### FIX-4 (125pp) HARDCODED-PATHS
Grep `/home/andrefarias` em nyx_gauntlet.py e trocar por construções relativas via PROJECT_ROOT.

## Critério binário

- [ ] 4 fixes aplicados
- [ ] Smoke + invariantes 14/14
- [ ] Ruff All checks passed
- [ ] Gauntlet --only proxy 100% + --only qualidade 100%
- [ ] Acentuação rc=0
