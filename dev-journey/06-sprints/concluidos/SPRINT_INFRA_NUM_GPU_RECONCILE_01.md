# SPRINT 263 — INFRA-NUM-GPU-RECONCILE-01

## 0. SPEC (machine-readable)

```yaml
sprint:
  id: INFRA-NUM-GPU-RECONCILE-01
  title: "Reconciliar valores fantasma de num_gpu"
  onda: 31
  prioridade: BAIXA
  tipo: Refactor
  dependencias: []
  desbloqueia: []
  conflito_arquivo: [DOC-CONTEXT-LAYERS-CLARIFY-01]   # ambos tocam defaults.py/proxy.py -> sequenciar

  touches:
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/config/settings.py
      reason: "Remover property num_gpu (dead code, nao consumida)"
      linhas_alvo: "48-52"
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/config/defaults.py
      reason: "NUM_GPU_3B=-1 é inerte na prática; documentar/alinhar"
      linhas_alvo: "79-80"
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/proxy.py
      reason: "Comentário da cadeia run.sh->proxy (argparse default mascara o import)"

  forbidden:
    - "Alterar o comportamento real de boot (run.sh sempre passa --num-gpu)"
    - "Tocar scripts/detect_gpu.py ou run.sh (auto-tune é a fonte real)"
    - "Adicionar emoji / menção a IA externa"

  tests:
    - cmd: "./run.sh --gauntlet --only proxy"
      timeout: 300
      deve_passar: true
    - cmd: "./run.sh --gauntlet --only robustez"
      timeout: 60
      deve_passar: true

  acceptance_criteria:
    - "grep 'def num_gpu' nyx/config/settings.py retorna vazio (property removida) OU documentada como usada"
    - "NUM_GPU_3B tem comentário explicando que é inerte (mascarado por argparse default + run.sh)"
    - "RB-05 (model tier) do gauntlet robustez continua passando"
    - "gauntlet --only proxy 7/7"
    - "smoke boot ok + invariantes 14/14"
```

---

**Status:** PENDENTE
**Data criação:** 2026-05-26
**Modelo obrigatório:** claude-opus-4-7 (sem subagentes)

---

## Contexto

> ADR-003 (VRAM Management) + ADR-031. O num_gpu real vem de `scripts/detect_gpu.py` (auto-tune) via `run.sh`, que SEMPRE passa `--num-gpu` explícito ao proxy.

## Problema

Três valores de `num_gpu` divergem e confundem:

1. `nyx/config/settings.py:49` define a property `num_gpu` que retorna `NUM_GPU_7B (18)` ou `NUM_GPU_3B (-1)`. **Dead code:** nenhum callsite consome `settings.num_gpu` (o `model_tier.py:126` usa `tier.num_gpu`, que é outro objeto; o gauntlet usa `tier.num_gpu`).
2. `nyx/config/defaults.py:80` `NUM_GPU_3B = -1`. O `proxy.py` o importa como `_INITIAL_NUM_GPU`, mas `proxy.main()` tem `argparse --num-gpu default=15` que popula `app["state"]["num_gpu"]` ANTES do `_on_startup`, então o `setdefault(_INITIAL_NUM_GPU)` nunca usa o `-1`.
3. O `run.sh` real usa `NYX_NUM_GPU=12` + auto-tune (`detect_gpu.py`), passando `--num-gpu` explícito. Logo o `-1` e o `15` são ambos inertes no caminho real.

## Solução

- **Remover** a property morta `num_gpu` de `settings.py` (linhas 48-52). Confirmar via grep que ninguém a consome antes.
- **Documentar** `NUM_GPU_3B` em `defaults.py`: comentário curto deixando claro que o valor é inerte no boot real (run.sh sempre passa `--num-gpu`; proxy argparse default vence o import).
- **Comentar** em `proxy.py` (perto do import de `_DEFAULT_NUM_GPU`/`_INITIAL_NUM_GPU`) a cadeia real: run.sh -> --num-gpu -> app["state"], e que o import só serve de fallback teórico.
- Sem mudança de comportamento. A rede é o gauntlet `--only proxy` (7/7) + `--only robustez` (RB-05 model tier).

## Comandos de verificação

```bash
grep -rn "settings\.num_gpu" nyx/ scripts/        # vazio antes e depois (confirma dead code)
grep -rn "def num_gpu" nyx/config/settings.py     # vazio apos remocao
/home/andrefarias/.local/bin/ruff check nyx/config/settings.py nyx/config/defaults.py nyx/proxy.py
./run.sh --gauntlet --only proxy                  # 7/7
./run.sh --gauntlet --only robustez               # RB-05 ok
./run.sh --smoke                                  # boot ok
python3 ~/.config/zsh/scripts/validar-acentuacao.py --paths nyx/config/settings.py nyx/config/defaults.py nyx/proxy.py
```

## Critério binário de aceite

- [ ] property `num_gpu` removida de `settings.py` (ou justificada como consumida)
- [ ] `NUM_GPU_3B` com comentário de "inerte"
- [ ] gauntlet `--only proxy` 7/7 + RB-05 ok
- [ ] smoke + invariantes 14/14 + ruff + acentuação rc=0
- [ ] spec movida `producao/` -> `concluidos/`

## Proof-of-work

grep confirmando dead code + output dos gauntlets proxy/robustez + invariantes antes/depois.

---

*"Número que não é lido por ninguém é ruído com aparência de regra." -- anônimo*
