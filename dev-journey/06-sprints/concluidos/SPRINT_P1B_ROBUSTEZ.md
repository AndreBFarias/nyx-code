## 0. SPEC (machine-readable)

```yaml
sprint:
  id: P1-B
  title: "Robustez: Context Manager + Repetition Detector + Model Tier"
  touches:
    - path: nyx/agent/context.py
      reason: "Budget de tokens com 4 níveis de compactação (port da Luna)"
    - path: nyx/agent/repetition.py
      reason: "Detecção de loops: exact, semantic, cycle (port da Luna)"
    - path: nyx/agent/model_tier.py
      reason: "Auto-detecção de hardware e perfis de modelo (port da Luna)"
  origin:
    primary:
      - "Luna/src/skills/code_agent/context_manager.py (181 linhas)"
      - "Luna/src/skills/code_agent/repetition.py (147 linhas)"
      - "Luna/src/skills/code_agent/model_tier.py (143 linhas)"
    reference: "openclaud/src/services/compact/ + openclaud/src/services/tokenEstimation.ts"
  acceptance_criteria:
    - "ContextBudget com 4 níveis: full (<40%), partial (40-60%), compact (60-85%), emergency (>85%)"
    - "Repetition detector: exact, semantic, cycle + SkipStrategy"
    - "ModelTier: 3 perfis (COMPACT, STANDARD, POWER) com auto-detecção nvidia-smi"
    - "Importa sem erro: from nyx.agent.context import ContextBudget"
    - "Importa sem erro: from nyx.agent.repetition import detect_repetition"
    - "Importa sem erro: from nyx.agent.model_tier import get_model_tier"
```

---

# Sprint P1-B -- Robustez

**Status:** CONCLUIDA (header corrigido em MASTER-CLEANUP-02 2026-05-20; presença em concluidos/ implica CONCLUIDA conforme convenção do projeto)
**Data:** 2026-04-04
**Prioridade:** ALTA
**Tipo:** Port (Luna -> Nyx)
**Dependências:** P1-A (models atualizados)
**Desbloqueia:** P1-F (integração no loop)

---

## O que portar

### 1. `nyx/agent/context.py` (Luna: context_manager.py, 181 linhas)

Budget de tokens com compactação progressiva:
- Nível 0 (<40%): histórico completo
- Nível 1 (40-60%): últimas 3 entradas full + resto ultra-compact
- Nível 2 (60-85%): apenas key_decisions + files_context
- Nível 3 (>85%): truncar agressivamente + warning

Inclui `render_context_bar()` para exibir barra visual de uso.

**Ajustes:** trocar `from .prompt import estimate_tokens` por heurística local (chars/4).

### 2. `nyx/agent/repetition.py` (Luna: repetition.py, 147 linhas)

Três níveis de detecção:
- **Exact:** mesma ação com mesmos params
- **Semantic:** mesma ação no mesmo path (params diferentes)
- **Cycle:** padrão A->B->A->B em janela de histórico

Estratégias: CONTINUE, SKIP, FORCE_DONE.

**Ajustes:** trocar imports de `src.core` e `.models`.

### 3. `nyx/agent/model_tier.py` (Luna: model_tier.py, 143 linhas)

Auto-detecção de hardware via nvidia-smi:
- **COMPACT (<4GB):** qwen3:4b, num_gpu=8, num_ctx=4096
- **STANDARD (4-8GB):** qwen3:4b, num_gpu=12, num_ctx=8192
- **POWER (8GB+):** qwen3:4b, num_gpu=-1, num_ctx=32768

**Ajustes:** trocar modelos de qwen2.5-coder para qwen3:4b, trocar imports de `src.core.model_registry`.

## Testes Gauntlet (novos, adicionados ao nyx_gauntlet.py)

Fase: `robustez` (nova, 6 testes)

| ID | Nome | Validação |
|----|------|-----------|
| RB-01 | Context budget nível 0 | ContextBudget com texto curto -> level 0 (full) |
| RB-02 | Context budget nível 3 | ContextBudget com texto enorme -> level 3 (emergency) |
| RB-03 | Repetition exact | detect_repetition com mesma ação 2x -> True |
| RB-04 | Repetition cycle | is_cycle com A->B->A->B -> True |
| RB-05 | Model tier auto | get_model_tier() retorna tier válido com num_gpu > 0 |
| RB-06 | Model tier hardware | tier.hardware_profile corresponde à GPU detectada |

## Verificação

- [ ] 6 testes de robustez passam no Gauntlet
- [ ] `./run.sh --gauntlet --only robustez` passa 100%
- [ ] Gauntlet completo continua passando 100%

---

*"A resiliência não é sobre evitar falhas, é sobre sobreviver a elas." -- Nassim Taleb*
