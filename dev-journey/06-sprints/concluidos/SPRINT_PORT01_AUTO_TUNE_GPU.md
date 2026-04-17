## 0. SPEC (machine-readable)

```yaml
sprint:
  id: PORT-01
  title: "Auto-tune de GPU layers"
  touches:
    - path: scripts/detect_gpu.py
      reason: "Novo script que detecta VRAM e calcula num_gpu ideal por modelo"
    - path: install.sh
      reason: "Chamar detect_gpu.py após baixar modelos e escrever NYX_NUM_GPU no .env"
    - path: run.sh
      reason: "Respeitar NYX_AUTO_TUNE; recalcular no boot quando ativo"
    - path: .env.example
      reason: "Documentar NYX_AUTO_TUNE e remover hardcode de NYX_NUM_GPU"
    - path: scripts/gauntlet/fases/gpu_tune.py
      reason: "Nova fase com 3 testes"
    - path: scripts/gauntlet/nyx_gauntlet.py
      reason: "Registrar fase gpu_tune"
  n_to_n_pairs:
    - ["scripts/detect_gpu.py", "install.sh"]
    - ["scripts/detect_gpu.py", "run.sh"]
  forbidden:
    - "Sobrescrever .env quando NYX_AUTO_TUNE=0"
    - "Crashar se nvidia-smi não existe (deve fallback CPU)"
    - "Hardcode de num_gpu fora do detect_gpu.py"
  tests:
    - cmd: "./run.sh --gauntlet --only gpu_tune"
      timeout: 60
  acceptance_criteria:
    - "detect_gpu.py retorna JSON válido em máquina com e sem GPU"
    - "Em 8GB de VRAM livre, num_gpu calculado para qwen3:4b >= 20"
    - "Fallback CPU (num_gpu=0) quando nvidia-smi ausente"
    - "NYX_AUTO_TUNE=0 preserva valor do .env (não sobrescreve)"
    - "Logs em logs/gpu_tune.log com GPU, VRAM, layers"
    - "Acentuação PT-BR correta"
```

> Executar antes de começar: rodar `./run.sh --gauntlet --only coverage` para confirmar baseline 6/6.

---

# Sprint PORT-01 -- Auto-tune de GPU layers

**Status:** CONCLUIDA
**Data:** 2026-04-16
**Prioridade:** ALTA
**Tipo:** Infra
**Dependências:** --
**Desbloqueia:** PORT-02, PORT-03

---

## Problema / Contexto

`NYX_NUM_GPU=12` e `NYX_NUM_CTX=4096` estão calibrados no `.env.example` para RTX 3050 4GB. Em outra máquina:

- **GPU com 8GB (ex.: 4060):** o projeto roda mas desperdiça metade da VRAM; inferência mais lenta que o necessário
- **GPU com 3GB:** dá OOM no boot (ADR-001 diz que deve degradar, não crashar)
- **Sem GPU:** `run.sh` força num_gpu=12 e Ollama não sobe em modo CPU corretamente

Precisa de uma camada que mede a máquina alvo e calcula `num_gpu` ideal por modelo antes do primeiro boot, e permite ao usuário fixar um valor manual quando necessário.

## Implementação

### Fase 1: Script de detecção (`scripts/detect_gpu.py`)

Expor três operações:

```
python scripts/detect_gpu.py --dry-run         # imprime JSON sem escrever em lugar algum
python scripts/detect_gpu.py --write-env       # escreve NYX_NUM_GPU no .env (se NYX_AUTO_TUNE=1)
python scripts/detect_gpu.py --for-model qwen3:4b   # retorna apenas num_gpu para o modelo
```

Tabela de consumo estimado (MB por camada, baseada em medições do próprio projeto):

| Modelo | MB por camada GPU | Total de camadas |
|--------|-------------------|------------------|
| qwen2.5-coder:3b | ~90 | 36 |
| qwen3:4b | ~110 | 40 |
| qwen2.5-coder:7b | ~180 | 28 (parcial) |

Reservar ~800MB de VRAM para contexto (num_ctx=4096) + buffers Ollama. `num_gpu` = floor((VRAM_livre_MB - 800) / MB_por_camada).

Detecção de VRAM:
- `nvidia-smi --query-gpu=memory.free --format=csv,noheader,nounits` (MiB disponível)
- Se exit != 0 ou binário ausente: `num_gpu=0` (CPU-only)

Log em `logs/gpu_tune.log`:
```
2026-04-16 22:10:31 [gpu_tune] GPU: NVIDIA GeForce RTX 4060 Laptop GPU
2026-04-16 22:10:31 [gpu_tune] VRAM livre: 7612 MiB
2026-04-16 22:10:31 [gpu_tune] qwen3:4b -> num_gpu=40 (full GPU)
2026-04-16 22:10:31 [gpu_tune] qwen2.5-coder:7b -> num_gpu=28 (parcial)
```

### Fase 2: Integração com install.sh

Após o passo 6 (baixar modelos), inserir:

```bash
log_step "Auto-tune de GPU"
"$SCRIPT_DIR/venv/bin/python" "$SCRIPT_DIR/scripts/detect_gpu.py" --write-env
log_ok "NYX_NUM_GPU calculado e escrito em .env"
```

### Fase 3: Integração com run.sh

Adicionar bloco antes de `configure_vram`:

```bash
if [ "${NYX_AUTO_TUNE:-1}" = "1" ] && [ -x "$SCRIPT_DIR/venv/bin/python" ]; then
    NYX_NUM_GPU=$("$SCRIPT_DIR/venv/bin/python" "$SCRIPT_DIR/scripts/detect_gpu.py" --for-model "$MODEL")
    export NYX_NUM_GPU
    log_nyx "Auto-tune: num_gpu=$NYX_NUM_GPU para $MODEL"
fi
```

### Fase 4: Atualizar `.env.example`

```
# Auto-tune de GPU (1=detecta automaticamente, 0=usa valor manual abaixo)
NYX_AUTO_TUNE=1

# Valor manual (ignorado se NYX_AUTO_TUNE=1)
# RTX 3050 4GB: 12. 4060 8GB: 40. CPU-only: 0
# NYX_NUM_GPU=12
```

### Fase 5: Testes Gauntlet (fase `gpu_tune`)

| ID | Nome | Validação |
|----|------|-----------|
| GPU-01 | `detect_gpu.py --dry-run` JSON válido | Parseia saída, tem chaves `vram_mb`, `gpu_name`, `num_gpu_per_model` |
| GPU-02 | Fallback CPU sem nvidia-smi | `PATH=/usr/bin:/bin` sem nvidia-smi instalado retorna `num_gpu=0` |
| GPU-03 | `NYX_AUTO_TUNE=0` preserva `.env` | Setar NYX_AUTO_TUNE=0 + NYX_NUM_GPU=5 no .env, rodar `run.sh` curto, validar que `env \| grep NYX_NUM_GPU` ainda é 5 |

## Verificação

- [ ] `detect_gpu.py --dry-run` funciona em máquina com GPU
- [ ] `detect_gpu.py --dry-run` funciona em máquina sem GPU (retorna num_gpu=0)
- [ ] `install.sh` escreve valor correto no `.env` após primeira execução
- [ ] `run.sh` respeita `NYX_AUTO_TUNE=0`
- [ ] Log em `logs/gpu_tune.log` criado
- [ ] Gauntlet fase `gpu_tune` passa 3/3

---

*"Medir é o primeiro passo para controlar." -- Peter Drucker*
