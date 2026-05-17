# SPRINT BOOT-VRAM-GUARD-01 — Re-tune VRAM antes da pré-carga + supressão de "Morto"

## 0. SPEC (machine-readable)

```yaml
sprint:
  id: BOOT-VRAM-GUARD-01
  title: "Re-tune live de VRAM antes da pré-carga + supressão de 'Morto' do bash"
  onda: 23
  bloco: 23.1 Estabilização
  prioridade: ALTA
  tipo: Bugfix
  dependencias: []
  desbloqueia: [PROXY-NUMGPU-RUNTIME-01, COCKPIT-01]

  touches:
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/run.sh
      reason: "Re-roda detect_gpu antes da pré-carga; suprime 'Morto' do bash com disown"
      linhas_alvo: "184, 311, 338-367, 371-377"
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/scripts/detect_gpu.py
      reason: "Adiciona modo --strict-low-vram que retorna num_gpu seguro para pré-carga"
      linhas_alvo: "85-153"

  creates: []
  removes: []

  n_to_n_pairs:
    - descricao: "Threshold de low VRAM mode (1.5 GiB) aparece em run.sh e detect_gpu.py — única fonte em detect_gpu.py"
      paths:
        - /home/andrefarias/Desenvolvimento/Nyx-Code/scripts/detect_gpu.py

  forbidden:
    - "Adicionar emoji"
    - "Menção a Claude/GPT/Anthropic"
    - "Hardcoded de VRAM threshold em run.sh (deve vir de detect_gpu.py)"
    - "Pular detect_gpu se nvidia-smi falhar (deve cair pra num_gpu=0 sem crash)"
    - "Suprimir 'Morto' via 'set +b' global (afeta set -uo pipefail)"
    - "Aumentar tempo de boot acima de +2s vs baseline"

  tests:
    - cmd: "./run.sh --smoke"
      timeout: 60
      deve_passar: true
      nota: "Boot ok; stdout não contém literal 'Morto'"
    - cmd: "./run.sh --gauntlet --only infra"
      timeout: 300
      deve_passar: true
      nota: "Todas as 5 features I-01..I-11 verdes"
    - cmd: "bash scripts/sprint_invariants.sh"
      timeout: 60
      deve_passar: "FAIL_AFTER <= FAIL_BEFORE"
    - cmd: "python scripts/detect_gpu.py --for-model qwen3:4b"
      timeout: 30
      deve_passar: true
      nota: "Retorna inteiro >= 0 mesmo com VRAM baixa"

  acceptance_criteria:
    - "run.sh chama nvidia-smi live ANTES da pré-carga (linhas ~352-360); recalcula num_gpu se delta > 20% vs T0"
    - "Em low-VRAM (<1.5 GiB livre), pré-carga é pulada graciosamente OU usa num_gpu seguro retornado pelo detect_gpu.py --strict-low-vram"
    - "Mensagem 'Morto' do bash não aparece em stdout em fluxo normal (`./run.sh --smoke && ./run.sh --smoke` consecutivos)"
    - "disown aplicado nos background & (linhas 184 start_ollama, 311 cleanup_proxy, 372 start_proxy)"
    - "detect_gpu.py ganha --strict-low-vram flag; retorna 0..N onde N respeita reserva 1.5x para pré-carga"
    - "Acentuação PT-BR correta em todo texto novo"
    - "Zero hex hardcoded; zero path absoluto fora de design_tokens"
    - "Gauntlet infra passa 100%"
    - "Tempo de boot delta < +2s vs baseline (medir 3x antes, 3x depois)"
```

---

**Status:** PENDENTE
**Data criação:** 2026-05-15
**Modelo obrigatório:** claude-opus-4-7 (sem subagentes)

---

# Sprint BOOT-VRAM-GUARD-01 — Re-tune VRAM antes da pré-carga + supressão de "Morto"

## Contexto do projeto (snapshot — não referência)

> **ADRs relevantes:**
> - ADR-001 Local First.
> - ADR-003 VRAM Management (cap empírico por GPU: 4GB→12 layers).
> - ADR-004 Zero Emojis.
> - ADR-005 Anonimato.
> - ADR-006 PT-BR acentuação.
> - ADR-025 (PROPOSTO) Loop de Experiência — boot é um momento crítico de feedback.
>
> **Estado do sistema na data da sprint:**
> - Python 3.10+, modelo qwen3:4b, Ollama 11435, proxy 11436.
> - 35 tools, 52 commands, 9 services, 24 ADRs vigentes + ADR-025 proposto.
> - Onda 22 em execução; Onda 23 paralela iniciada nesta sprint.
> - `./run.sh --smoke` imprime `boot ok` (check #13 do invariants).
> - Auto-tune existe via `scripts/detect_gpu.py` mas roda **só uma vez no boot** (run.sh:338).
> - VRAM baseline da máquina: RTX 3050 4 GB; em uso normal com browser/DE: 1.5 GiB livre.

## Problema

Em sessão de 2026-05-15, ao rodar `./run.sh`, observou-se:

1. **Ollama morre durante pré-carga** (linha 354 do run.sh): o `curl /api/chat` com `num_gpu=12` faz Ollama tentar alocar 3.9 GiB mas só há ~1.5 GiB livre → OOM-killer mata o processo background. Auto-restart em run.sh:364 recupera.
2. **Mensagem "Morto" do bash vaza** (`run.sh, linha 361: 440626 Morto "$OLLAMA_BIN" serve...`): o bash, ao detectar filho `&` morto por SIGKILL externo, reporta no stderr/stdout do shell pai. Esteticamente feia e dá impressão de erro.
3. **Auto-tune T0 está desatualizado em runtime**: `scripts/detect_gpu.py` chamado em run.sh:338 calcula `num_gpu=12` baseado na VRAM livre no momento T0; quando o usuário tem browser/DE consumindo VRAM, esse valor já não cabe na pré-carga em T0+segundos.

Diagnóstico verificado via grep nesta sessão (plan file `~/.claude/plans/...`).

## Solução

### Parte 1 — `scripts/detect_gpu.py`: modo `--strict-low-vram`

Adicionar flag `--strict-low-vram` em `main()`. Quando ativo:

```python
# Threshold: VRAM livre < LOW_VRAM_THRESHOLD_MB define low-VRAM mode.
LOW_VRAM_THRESHOLD_MB = 1536  # 1.5 GiB

def calc_num_gpu_strict(model: str, vram_free_mb: int, vram_total_mb: int = 0) -> int:
    """Variante para pré-carga: reserva 1.5x para o overhead inicial.

    Em low-VRAM (<1536 MiB livre), retorna 0 explicitamente — pré-carga
    será pulada graciosamente. Acima do threshold, usa cálculo padrão
    com reserva ampliada.
    """
    if vram_free_mb < LOW_VRAM_THRESHOLD_MB:
        return 0  # Sinaliza: pré-carga skip; carrega na 1ª requisição.
    reserved = max(RESERVED_MB, int(vram_free_mb * 0.33))
    usable = vram_free_mb - reserved
    if usable <= 0:
        return 0
    entry = MODEL_TABLE.get(model, MODEL_TABLE[DEFAULT_MODEL])
    layers = usable // entry["mb_per_layer"]
    num_gpu = max(0, min(entry["total_layers"], int(layers)))
    return apply_vram_cap(num_gpu, vram_total_mb)
```

### Parte 2 — `run.sh`: re-tune live + skip gracioso

Antes da pré-carga (linha ~352), inserir:

```bash
# Re-tune live: VRAM livre pode ter mudado entre o boot e este momento.
log_boot "Re-checagem de VRAM antes da pré-carga..."
PRELOAD_NUM_GPU=$("$SCRIPT_DIR/venv/bin/python" \
    "$SCRIPT_DIR/scripts/detect_gpu.py" \
    --for-model "$MODEL" --strict-low-vram 2>/dev/null || echo "0")

if [ "$PRELOAD_NUM_GPU" = "0" ]; then
    log_warn "VRAM insuficiente para pré-carga. Modelo carrega na 1ª requisição."
    SKIP_PRELOAD=1
else
    SKIP_PRELOAD=0
    if [ "$PRELOAD_NUM_GPU" != "$NYX_NUM_GPU" ]; then
        log_boot "Ajuste runtime: num_gpu $NYX_NUM_GPU -> $PRELOAD_NUM_GPU (VRAM live mudou)"
        NYX_NUM_GPU="$PRELOAD_NUM_GPU"
        export NYX_NUM_GPU
    fi
fi

if [ "$SKIP_PRELOAD" -eq 0 ]; then
    # bloco curl original aqui, usando $NYX_NUM_GPU atualizado
    ...
fi
```

### Parte 3 — `run.sh`: `disown` nos background

Aplicar `disown` após cada `&`:

```bash
# Linha 184 (start_ollama):
"$OLLAMA_BIN" serve >> "$SCRIPT_DIR/logs/ollama.log" 2>&1 &
OLLAMA_PID=$!
disown $OLLAMA_PID 2>/dev/null || true

# Linha 372 (start_proxy):
"$SCRIPT_DIR/venv/bin/python" "$SCRIPT_DIR/nyx/proxy.py" ... &
PROXY_PID=$!
disown $PROXY_PID 2>/dev/null || true
```

`disown` remove o processo da jobs table do bash; quando ele morre, o
bash não reporta no terminal.

Cuidado: `wait` e `kill 0` deixam de funcionar para PIDs disowned, mas
`kill $PID` continua funcional. O cleanup do run.sh já usa `kill $PID`
explicitamente.

## Verificação end-to-end

```bash
# 1. FAIL_BEFORE
bash scripts/sprint_invariants.sh > /tmp/inv_before.txt 2>&1
echo "FAIL_BEFORE=$(grep -c '^\[FAIL\]' /tmp/inv_before.txt)"

# 2. Reproduzir o bug (opcional, antes do fix):
#    abrir alguns programas até VRAM livre cair abaixo de 1.5 GiB
#    rodar ./run.sh e capturar "Morto" no stdout

# 3. Implementar (parte 1 -> parte 2 -> parte 3)

# 4. FAIL_AFTER
bash scripts/sprint_invariants.sh > /tmp/inv_after.txt 2>&1
echo "FAIL_AFTER=$(grep -c '^\[FAIL\]' /tmp/inv_after.txt)"
diff /tmp/inv_before.txt /tmp/inv_after.txt

# 5. Smoke + gauntlet
./run.sh --smoke
./run.sh --gauntlet --only infra

# 6. Validação manual: rodar em low-VRAM e verificar:
#    - "VRAM insuficiente para pré-carga" mostrado
#    - Sem "Morto" no terminal
#    - REPL abre normalmente
#    - 1ª pergunta carrega modelo (lento, mas funciona)
```

## Gambiarras proibidas

- Hardcoded de threshold em run.sh em vez de detect_gpu.py.
- `set +bm` global (afeta `set -uo pipefail`).
- `2>&-` (fecha stderr globalmente — perde diagnóstico).
- Loop de retry no curl da pré-carga sem cap (mascara o bug).
- Adicionar nova ADR para esta sprint (não justifica — é bugfix, ADR-003 cobre).

## Pontos de feedback (ADR-025 PROPOSTO)

Esta sprint aplica:
- **Indício <100ms** na fase "Re-checagem de VRAM antes da pré-carga..." (log_boot imediato).
- **Resposta clara**: warning específico se low-VRAM ("modelo carrega na 1ª requisição") em vez de silêncio.
- **Sem caixa-preta**: usuário vê o que está acontecendo no boot.

---

*"Um boot que mente é uma promessa quebrada antes da primeira conversa." -- anônimo*
