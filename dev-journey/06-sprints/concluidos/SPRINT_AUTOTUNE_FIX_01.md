# SPRINT AUTOTUNE-FIX-01 — calc_num_gpu respeita tabela ADR-003 por VRAM total

## 0. SPEC (machine-readable)

```yaml
sprint:
  id: AUTOTUNE-FIX-01
  title: "Auto-tune GPU aplica cap conservador por VRAM total (ADR-003)"
  onda: 22
  bloco: 2.6
  prioridade: CRÍTICA
  tipo: Bugfix
  dependencias: []
  desbloqueia: [VALIDATE-ONDA-20, TUI-02, CTX-02]

  touches:
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/scripts/detect_gpu.py
      reason: "calc_num_gpu retorna 23-24 layers em RTX 3050 4GB, violando ADR-003 que prescreve num_gpu=12 para 4GB"
      linhas_alvo: "115-130 (calc_num_gpu) + callers"
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/agent/summarizer.py
      reason: "REQUEST_TIMEOUT=60s foi calibrado com num_gpu=23 (otimista). Com cap ADR-003 (num_gpu<=15), summarizer fica 1.5x mais lento. ADR-009 '§Tempo não é limitante' autoriza 180s."
      linhas_alvo: "22 (REQUEST_TIMEOUT)"

  creates: []
  removes: []

  n_to_n_pairs: []

  forbidden:
    - "Hard-code num_gpu=12 -- viola NYX_AUTO_TUNE"
    - "Remover heurística -- prejudica GPUs >= 6GB que precisam do cálculo"
    - "Tocar nyx/proxy.py -- proxy apenas propaga NYX_NUM_GPU, não calcula"
    - "Mudar RESERVED_MB sem documentar -- caminho tentador mas oculta bug"
    - "Adicionar emoji, menção a IA"

  tests:
    - cmd: "python scripts/detect_gpu.py --dry-run --for-model qwen3:4b"
      timeout: 15
      esperado: "num_gpu <= 15 em RTX 3050 (4096 MiB)"
    - cmd: "./run.sh --smoke (3x consecutivos, kill Ollama entre eles)"
      timeout: 180
      esperado: "boot ok em todas 3 execuções, sem 'Ollama morreu durante pré-carga'"
    - cmd: "./run.sh --gauntlet --only rapido"
      timeout: 120
      esperado: "11/11 APROVADO"
    - cmd: "./run.sh --gauntlet --only contexto"
      timeout: 240
      esperado: "10/10 APROVADO"

  acceptance_criteria:
    - "calc_num_gpu em RTX 3050 4GB retorna valor <= 15 (ADR-003 prescreve 12, margem 15)"
    - "banner de boot mostra 'Auto-tune: num_gpu=N' com N <= 15"
    - "3 execuções consecutivas de ./run.sh sem 'Ollama morreu durante pré-carga'"
    - "GPUs >= 6GB (6144 MiB) continuam recebendo num_gpu > 15 quando cabe"
    - "Gauntlet rapido 100% + contexto 100%"
    - "FAIL invariantes <= baseline"
```

---

**Status:** CONCLUIDA (commit 6f5273b)
**Data criação:** 2026-04-20
**Origem:** achado durante execução de VALIDATE-ONDA-20 (Rodada 1). Banner mostrou `Auto-tune: num_gpu=23 para qwen3:4b` em RTX 3050 4GB. 2ª execução consecutiva de `./run.sh` reproduziu OOM: "Ollama morreu durante pré-carga. Reiniciando..." em loop. Viola frontalmente ADR-003 §Decisão ("num_gpu=12 como padrão") e ADR-009 §Configuração de VRAM (tabela que prescreve 12 para 4GB).
**Modelo obrigatório:** claude-opus-4-7 (sem subagentes)

---

## Contexto

### Heurística atual (`scripts/detect_gpu.py:115-130`)

```python
RESERVED_MB = 1024
MODEL_TABLE = {"qwen3:4b": {"total_layers": 40, "mb_per_layer": 115}, ...}

def calc_num_gpu(model, vram_free_mb):
    usable = vram_free_mb - 1024
    layers = usable // 115
    return min(40, layers)
```

Para RTX 3050 4GB com `vram_free_mb ≈ 3800`:
- `usable = 3800 - 1024 = 2776`
- `layers = 2776 // 115 = 24`
- retorna 24

### Empirismo ADR-003 (já vivido)

| num_gpu | VRAM | Estabilidade |
|---------|------|-------------|
| 37 (all) | 3.3GB | OOM frequente |
| 20 | 1.6GB | Instável |
| 15 | 1.4GB | Estável |
| 12 | 1.2GB | Muito estável |

ADR-009 tabela adaptativa também cita `num_gpu=12 num_ctx=8192` como estável em RTX 3050.

### Por que a heurística erra

`RESERVED_MB=1024` é otimista demais para hardware limitado:
- KV cache com `num_ctx=8192` consome ~300-500 MiB conforme inflada
- Sistema de tempo de execução do Ollama: ~200 MiB
- Desktop Pop!_OS compartilhando VRAM: variável, até 500 MiB
- System prompt inflado (RepoMap 2KB + Memory + Summary) durante sessão longa

Em hardware pequeno (≤4GB), a margem real para layers é muito menor que `(free - 1024)`. O cálculo puro ignora que o overhead **cresce durante a sessão** — OOM só aparece na 2ª execução.

---

## Solução proposta

Cap explícito por VRAM total, alinhado à tabela ADR-003. O cálculo heurístico é preservado — apenas limitado quando detecta hardware pequeno.

```python
# Tabela ADR-003: layers estáveis por classe de hardware.
# Ajustada com margem para sistema + desktop + KV cache dinâmico.
VRAM_CAP_MB_TO_LAYERS: list[tuple[int, int]] = [
    (4096, 15),   # RTX 3050 4GB: ADR-003 empírico (12 muito estável, 15 estável)
    (6144, 28),   # RTX 3060 6GB: margem para contexto grande
    (8192, 36),   # RTX 4060 8GB: quase full GPU
    # acima de 8GB: sem cap (heurística pura)
]


def apply_vram_cap(num_gpu: int, vram_total_mb: int) -> int:
    """Limita num_gpu em hardware pequeno conforme ADR-003."""
    if vram_total_mb <= 0:
        return num_gpu
    for cap_mb, max_layers in VRAM_CAP_MB_TO_LAYERS:
        if vram_total_mb <= cap_mb:
            return min(num_gpu, max_layers)
    return num_gpu


def calc_num_gpu(model: str, vram_free_mb: int, vram_total_mb: int = 0) -> int:
    entry = MODEL_TABLE.get(model, MODEL_TABLE[DEFAULT_MODEL])
    usable = vram_free_mb - RESERVED_MB
    if usable <= 0:
        return 0
    layers = usable // entry["mb_per_layer"]
    num_gpu = max(0, min(entry["total_layers"], int(layers)))
    return apply_vram_cap(num_gpu, vram_total_mb)
```

Todos os callers (`cmd_dry_run`, `cmd_write_env`, `cmd_for_model`, `build_report`) recebem `vram_total_mb` adicional (já disponível em `detect_gpu()`).

### Alternativas consideradas (descartadas)

1. **Aumentar `RESERVED_MB` para 2048** — fix oculto, ignora tabela ADR-003, quebra GPUs ≥ 6GB.
2. **Hard-code num_gpu=12** — viola `NYX_AUTO_TUNE` (opção do .env).
3. **Validar pré-carga real e reduzir se OOM** — correto mas caro (boot +30s em cada tentativa); cap por tabela é suficiente para 99% dos casos e o fallback ADR-009 item 4 (`Se OOM: reduzir num_gpu para 8`) cobre o 1% restante em sprint futura.

---

## Diff esperado

```
~ 1 arquivo modificado (scripts/detect_gpu.py)
+ ~25 linhas (VRAM_CAP_MB_TO_LAYERS, apply_vram_cap)
+ adaptação de 4 callers para passar vram_total_mb
```

---

## Comandos de verificação

```bash
bash scripts/sprint_invariants.sh > /tmp/inv_before.txt 2>&1
FAIL_BEFORE=$(grep -c "^\[FAIL\]" /tmp/inv_before.txt)

# Fix

# Validação isolada (sem Ollama)
python scripts/detect_gpu.py --dry-run
# Esperado: num_gpu_per_model[qwen3:4b] <= 15

python scripts/detect_gpu.py --for-model qwen3:4b
# Esperado: <= 15 impresso

# Smoke 3x
for i in 1 2 3; do
  ./run.sh --smoke
  pkill -f "ollama serve" 2>/dev/null
  sleep 2
done
# Esperado: 'boot ok' em todas 3

# Gauntlets críticos
./run.sh --gauntlet --only rapido
./run.sh --gauntlet --only contexto

bash scripts/sprint_invariants.sh > /tmp/inv_after.txt 2>&1
FAIL_AFTER=$(grep -c "^\[FAIL\]" /tmp/inv_after.txt)
```

---

## Critério binário de aceite

- [ ] `calc_num_gpu("qwen3:4b", 3800, 4096)` <= 15
- [ ] `calc_num_gpu("qwen3:4b", 5500, 6144)` <= 28
- [ ] `calc_num_gpu("qwen3:4b", 7500, 8192)` <= 36
- [ ] Banner mostra `num_gpu=N` com N <= 15 em RTX 3050
- [ ] 3× `./run.sh --smoke` sem OOM
- [ ] Gauntlet rapido 100% + contexto 100%
- [ ] FAIL_AFTER <= FAIL_BEFORE

---

## Gambiarras específicas

1. **Ignorar vram_total=0 silenciosamente** — já tratado no guard do `apply_vram_cap`, mas evitar que teste passe por falta de GPU (máquina sem nvidia-smi); `num_gpu=0` continua válido.
2. **Cap por `vram_free` em vez de `vram_total`** — errado. VRAM livre varia; tabela ADR-003 é por hardware (propriedade fixa).
3. **Cap só quando erro prévio** — gambiarra adaptativa sem sinal estável. Cap fixo é determinístico.
4. **Usar cap linear (`num_gpu = vram_total_mb // 341`)** — coincide em alguns pontos mas perde o empirismo da tabela ADR-003.

---

## Proof-of-work obrigatório

- Output de `python scripts/detect_gpu.py --dry-run` antes e depois do fix, mostrando queda de num_gpu em qwen3:4b.
- 3 transcripts de `./run.sh --smoke` consecutivos com `boot ok`.
- Gauntlet rapido e contexto APROVADO.
- `git diff scripts/detect_gpu.py` mostrando apenas as alterações listadas.

---

## Riscos

| Risco | Mitigação |
|-------|-----------|
| Cap muito conservador para RTX 3050 com desktop leve | ADR-009 permite num_ctx adaptativo; se sobrar VRAM, usuário pode setar NYX_AUTO_TUNE=0 e NYX_NUM_GPU manualmente |
| Nova GPU futura com VRAM entre faixas da tabela | Ordenação do laço pega o menor cap aplicável; usuário pode adicionar entrada |
| Quebra de testes gauntlet que assumem `num_gpu` específico | Gauntlet lê NYX_NUM_GPU dinâmico; não há assert de valor fixo |

---

*"A robustez vem do limite aceito, não do limite ignorado." — prática da ADR-003*
