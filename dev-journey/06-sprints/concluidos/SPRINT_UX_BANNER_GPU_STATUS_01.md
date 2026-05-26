# SPRINT 244 — UX-BANNER-GPU-STATUS-01

## 0. SPEC

```yaml
sprint:
  id: UX-BANNER-GPU-STATUS-01
  title: "Adicionar campo `GPU: Ativo|CPU` no banner do CLI"
  onda: 31
  prioridade: MÉDIA
  tipo: Feature
  dependencias: []
  desbloqueia: []

  touches:
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/agent/banner.py
      reason: "Adicionar linha/campo `GPU: Ativo|CPU` ao lado de `100% offline`"
  creates: []
  removes: []
```

---

# Sprint 244 — UX-BANNER-GPU-STATUS-01

**Status:** PENDENTE
**Data criação:** 2026-05-25

## Contexto

Usuário pediu: "tem que ter uma seção no banner ja temos o versão: n | 100% offline | E o GPU: Ativo e afins". Banner atual tem `v1.3.0 ● 100% offline | MODELO qwen2.5-coder:3b | PROJETO Nyx-Code`. Falta indicador GPU.

Atualmente o usuário só descobre se está em GPU ou CPU olhando o toolbar `o cold` (após primeira mensagem) ou `oom_recovery_count` em logs. Banner deveria informar IMEDIATAMENTE.

## Solução

Em `nyx/agent/banner.py`, função `_build_wide`, adicionar campo logo após `100% offline`:

```
v1.3.0  ● 100% offline  │  GPU: 4/36 (4GB)
```

OU mais simples (linha separada):

```
v1.3.0      ● 100% offline
GPU: 4 layers · qwen2.5-coder:3b · Nyx-Code
TOOLS 35 | COMANDOS 67 | MEMÓRIA ativa
```

Fonte do `num_gpu`: env var `NYX_NUM_GPU` (setada pelo run.sh após auto-tune). Fallback 0 (CPU).

Cor:
- `GPU: 4 layers` em accent (turquesa) se `NYX_NUM_GPU > 0`
- `CPU` em ORANGE (warning) se `NYX_NUM_GPU == 0`

## Acceptance

- [ ] Banner exibe `GPU: N layers` (ou `CPU`) entre `100% offline` e info MODELO
- [ ] Cor turquesa em GPU mode, laranja em CPU mode
- [ ] Layout não quebra largura do banner (testar terminal 80, 100, 120, 160 cols)
- [ ] Smoke + invariantes preservados

## Proof-of-work

```bash
./run.sh --smoke
NYX_NUM_GPU=4 ./venv/bin/python -c "from nyx.agent.banner import build_banner; print(build_banner('qwen2.5-coder:3b', 35, 'Nyx-Code'))"
NYX_NUM_GPU=0 ./venv/bin/python -c "from nyx.agent.banner import build_banner; print(build_banner('qwen2.5-coder:3b', 35, 'Nyx-Code'))"
# Capturar via tmux+import + comparar visualmente
bash scripts/sprint_invariants.sh
```
