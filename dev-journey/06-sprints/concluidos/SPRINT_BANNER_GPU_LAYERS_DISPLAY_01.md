## 0. SPEC (machine-readable)

```yaml
sprint:
  id: BANNER-GPU-LAYERS-DISPLAY-01
  title: "Banner exibe 'GPU: full' em vez de 'GPU: 999 layers' (numero interno cru)"
  onda: 48
  prioridade: BAIXA
  tipo: Bugfix
  dependencias: []
  desbloqueia: []

  touches:
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/agent/banner.py
      reason: "Linha 284 mostra o sentinel FULL_GPU_LAYERS=999 cru ('GPU: 999 layers')"
      linhas_alvo: "283-288"
  creates: []
  removes: []

  forbidden:
    - "Adicionar emoji"
    - "Importar de scripts/ no banner (use threshold local ou constante de defaults)"
    - "Mudar o caminho CPU (num_gpu == 0 -> 'CPU' fica intacto)"

  tests:
    - cmd: "./run.sh --gauntlet --only rapido"
      timeout: 300
      deve_passar: true

  acceptance_criteria:
    - "num_gpu sentinel de offload total (>= 100, valor real 999) exibe 'GPU: full' (plain e colorido)"
    - "num_gpu parcial (ex.: 12, 28) continua exibindo 'GPU: N layers'"
    - "num_gpu == 0 continua exibindo 'CPU'"
    - "Acentuacao PT-BR correta; gauntlet --only rapido 100%; ruff limpo"
```

---

# Sprint BANNER-GPU-LAYERS-DISPLAY-01 — "GPU: full" em vez de "999 layers"

**Status:** PENDENTE
**Data criação:** 2026-06-26
**Modelo obrigatório:** claude-opus-4-7 (executor-sprint autorizado pelo dono nesta onda)

---

## Contexto do projeto (snapshot)

> **ADRs:** ADR-027 Identidade/microcopy Nyx (zero placeholder cru), ADR-024 Render Layer, ADR-006 PT-BR, ADR-014 Gauntlet.
> **Estado (2026-06-26):** ONDA-48 (achado V15). Desde GPU-FULL-OR-CPU-01, `detect_gpu.py:61` usa `FULL_GPU_LAYERS = 999` como sentinel de "offload total" (todas as camadas na GPU). O banner recebe esse `num_gpu` e o exibe literal.

---

## Problema

**Achado V15, visto na TUI real (2026-06-26).** O banner exibe **"GPU: 999 layers"** (o dono estranhou: "999 layers?"). O modelo padrão (qwen2.5-coder:3b) tem ~28 camadas; "999" é o sentinel interno `FULL_GPU_LAYERS`, não um número real de camadas. Vaza estado interno na UI (microcopy crua, contra ADR-027).

Causa-raiz (`nyx/agent/banner.py:283-285`):
```python
if num_gpu > 0:
    gpu_plain = f"GPU: {num_gpu} layers"
    gpu_colored = f"{accent}GPU:{nc} {primary}{num_gpu} layers{nc}"
```

---

## Solução proposta

Quando `num_gpu` é o sentinel de offload total (>= 100; o valor real é 999), exibir **"GPU: full"** em vez do número cru. Offload parcial (12, 28...) e CPU (0) ficam intactos.

---

## Arquivos alvo (paths absolutos)

### `/home/andrefarias/Desenvolvimento/Nyx-Code/nyx/agent/banner.py`

# Localização aproximada: linha 283-288 (drift tolerado se trecho casa)
**Antes:**
```python
    if num_gpu > 0:
        gpu_plain = f"GPU: {num_gpu} layers"
        gpu_colored = f"{accent}GPU:{nc} {primary}{num_gpu} layers{nc}"
    else:
        gpu_plain = "CPU"
        gpu_colored = f"{warning}CPU{nc}"
```

**Depois:**
```python
    if num_gpu > 0:
        # BANNER-GPU-LAYERS-DISPLAY-01 (V15): num_gpu >= 100 e o sentinel de
        # offload total (FULL_GPU_LAYERS=999 em detect_gpu.py); exibir "full"
        # em vez do numero interno cru ("999 layers" confundia o usuario).
        gpu_label = "full" if num_gpu >= 100 else f"{num_gpu} layers"
        gpu_plain = f"GPU: {gpu_label}"
        gpu_colored = f"{accent}GPU:{nc} {primary}{gpu_label}{nc}"
    else:
        gpu_plain = "CPU"
        gpu_colored = f"{warning}CPU{nc}"
```

**Mudanças:** introduz `gpu_label`; `>= 100` vira "full"; parcial mantém "N layers"; CPU intacto.

---

## Diff esperado (resumo)

```
~ 1 arquivo modificado (nyx/agent/banner.py)
+ ~5 linhas líquidas
```

---

## Comandos de verificação (literais, copy-paste)

```bash
# 1. Static + acentuação
python -m ruff check nyx/
python3 ~/.config/zsh/scripts/validar-acentuacao.py --paths nyx/agent/banner.py

# 2. Render do banner nos 3 casos (lógica pura, rodar inline):
python -c "
import nyx.agent.banner as b
# inspecionar a função que monta o banner com num_gpu=999, 12, 0:
# (ajuste para a assinatura real de _build_wide/build; checar a string 'GPU: full' / 'GPU: 12 layers' / 'CPU')
"
# Alternativa visível: subir a TUI e conferir o banner mostra 'GPU: full'
# (validação-visual: a skill captura o banner; canvas pinta no Chrome real).

# 3. Gauntlet
./run.sh --gauntlet --only rapido
```

---

## Critério binário de aceite

- [ ] `num_gpu >= 100` (sentinel) exibe "GPU: full" (plain e colorido)
- [ ] `num_gpu` parcial (12/28) exibe "GPU: N layers"; `num_gpu == 0` exibe "CPU"
- [ ] Evidência visual do banner com "GPU: full" (skill validação-visual, toca UI)
- [ ] ruff limpo, acentuação rc=0, invariantes FAIL_AFTER <= FAIL_BEFORE, gauntlet rapido 100%
- [ ] 396 marcada CONCLUIDA no MASTER; spec movida para concluidos/
- [ ] Commit: `fix(banner): 396 BANNER-GPU-LAYERS-DISPLAY-01 -- 'GPU: full' em vez de '999 layers' (V15)`

---

## Guardrails anti-engodo

NÃO concluir se: o caso parcial (12 layers) ou CPU regrediu; mexeu no caminho CPU; usou import de scripts/; gauntlet "passou" sem output; sem evidência visual do banner. Falha -> `[SPRINT 396] BLOQUEADA: <motivo>`.

---

## Proof-of-work (4 passos)

inv_before -> implementar -> inv_after (<=) -> diff. Colar tail de ambos + diff + o render dos 3 casos (full/parcial/CPU) + evidência visual do banner + `git show --stat HEAD`.

---

## Riscos

| Risco | Mitigação |
|-------|-----------|
| Threshold 100 corta um caso legítimo de 100+ layers reais | Nenhum modelo local nesse path oferece 100+ camadas via num_gpu; o sentinel é 999. Caso surja modelo gigante, o threshold é ajustável. |
| Skill de validação-visual indisponível | Pipeline 3-tentativas (scrot/import -> claude-in-chrome -> playwright); só declara impossível após as 3. |

---

*"O número que só a máquina entende não pertence à tela do humano." -- princípio de microcopy*
