## 0. SPEC (machine-readable)

```yaml
sprint:
  id: G-02
  title: "Gauntlet resiliente -- checkpoints, baselines, flags, portabilidade"
  touches:
    - path: scripts/gauntlet/nyx_gauntlet.py
      reason: "Checkpoints, report incremental, baselines JSON, detecção de regressão, auto-config hardware"
    - path: dev-journey/07-reports/gauntlet/baselines/
      reason: "Diretório de baselines JSON para comparação histórica"
    - path: dev-journey/07-reports/gauntlet/flags/
      reason: "Diretório de flags de features não mapeadas"
    - path: nyx/config/defaults.py
      reason: "NUM_CTX default atualizado para 8192"
  n_to_n_pairs:
    - a: "scripts/gauntlet/nyx_gauntlet.py -> baselines/*.json"
      reason: "Gauntlet salva baseline, lê anterior para comparar"
  forbidden:
    - "Mocks de Ollama ou proxy"
    - "Limites artificiais de max_tokens"
  tests:
    - cmd: "./run.sh --gauntlet --only rapido"
      timeout: 300
  acceptance_criteria:
    - "GAUNTLET_REPORT.md atualizado a cada teste (não só no final)"
    - "Checkpoint JSON salvo a cada teste para recuperação de crash"
    - "Baseline JSON salvo em dev-journey/07-reports/gauntlet/baselines/"
    - "Detecção de regressão comparando com baseline anterior"
    - "Sistema de flags para features não mapeadas"
    - "Auto-detecção de hardware (GPU, VRAM, ajuste de num_gpu/num_ctx)"
    - "O pior LLM sabe se guiar pelo projeto (docs claros, estrutura previsível)"
    - "Trocar de PC = funciona automaticamente, só muda velocidade"
    - "100% obrigatório para push na main"
    - "Acentuação PT-BR correta"
```

> Executar antes de começar: `python scripts/sync.py`

---

# Sprint G-02 -- Gauntlet Resiliente

**Status:** CONCLUIDA
**Data:** 2026-04-04
**Prioridade:** ALTA
**Tipo:** Infra + Feature
**Dependências:** G-01 (framework base)
**Desbloqueia:** G-03 a G-08, D-01

---

## Problema

O Gauntlet atual tem limitações que impedem uso em produção real:

1. **Report só no final** -- se crashar no meio, perde tudo
2. **Sem checkpoints** -- não dá pra retomar de onde parou
3. **Sem baseline histórico** -- impossível detectar regressão entre execuções
4. **Sem flags** -- feature nova na TUI sem teste no Gauntlet passa despercebida
5. **Hardcoded para RTX 3050** -- trocar de PC exige ajuste manual
6. **LLM fraco não se guia** -- docs/estrutura precisam ser claros o suficiente para qualquer modelo

---

## Implementação

### 1. Checkpoint a cada teste

```python
CHECKPOINT_PATH = PROJECT_ROOT / "dev-journey" / "07-reports" / "gauntlet" / "checkpoint.json"

def _save_checkpoint(self) -> None:
    """Salva estado atual -- recuperável se crashar."""
    data = {
        "timestamp": datetime.now().isoformat(),
        "model": self._model,
        "phases_done": list(self._phases_done),
        "results": [
            {
                "id": r.feature_id,
                "name": r.name,
                "phase": r.phase,
                "passed": r.passed,
                "elapsed_s": r.elapsed_s,
                "tokens": r.tokens,
                "details": r.details,
                "error": r.error,
            }
            for r in self._results
        ],
        "kpis": self._kpis,
    }
    CHECKPOINT_PATH.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
```

Chamado dentro de `_add()` -- cada resultado salva checkpoint automaticamente.

### 2. Report incremental (GAUNTLET_REPORT.md em tempo real)

`_write_report()` chamado após cada fase (não só no finally).
O report mostra testes já executados + "em andamento" para fases restantes.

```python
def _add(self, ...):
    # ... registra resultado ...
    self._save_checkpoint()
    self._write_report()  # Atualiza report em tempo real
```

### 3. Baseline JSON

```
dev-journey/07-reports/gauntlet/baselines/
├── baseline_2026-04-04.json
├── baseline_2026-04-05.json
└── ...
```

Formato:
```json
{
    "date": "2026-04-04",
    "commit": "abc1234",
    "model": "qwen3:4b",
    "hardware": {
        "gpu": "NVIDIA GeForce RTX 3050 Laptop GPU",
        "vram_total_mib": 4096,
        "num_gpu": 12,
        "num_ctx": 8192
    },
    "kpis": {
        "warmup_s": 138.2,
        "ttfr_chat_s": 14.3,
        "ttfr_tool_s": 12.7,
        "vram_mib": 2100,
        "pass_rate": 100.0,
        "total_time_s": 468
    },
    "results": {
        "total": 36,
        "passed": 36,
        "failed": 0
    }
}
```

### 4. Detecção de regressão

Ao gerar report, carregar baseline anterior e comparar:

```python
def _detect_regressions(self, current: dict, previous: dict | None) -> list[str]:
    if not previous:
        return []
    regressions = []
    # TTFR chat: >50% mais lento
    if current["ttfr_chat_s"] > previous["ttfr_chat_s"] * 1.5:
        regressions.append(f"TTFR chat regrediu: {previous['ttfr_chat_s']}s -> {current['ttfr_chat_s']}s")
    # Pass rate caiu
    if current["pass_rate"] < previous["pass_rate"]:
        regressions.append(f"Pass rate caiu: {previous['pass_rate']}% -> {current['pass_rate']}%")
    # VRAM subiu >20%
    if current["vram_mib"] > previous["vram_mib"] * 1.2:
        regressions.append(f"VRAM subiu: {previous['vram_mib']}MiB -> {current['vram_mib']}MiB")
    return regressions
```

Regressões aparecem no report com destaque.

### 5. Sistema de flags

```
dev-journey/07-reports/gauntlet/flags/
├── FLAG_nova_feature_xxx.md
└── ...
```

Formato de flag:
```markdown
# FLAG: Nome da Feature

**Data:** 2026-04-05
**Status:** NAO_MAPEADA
**Descrição:** Feature X adicionada à TUI mas sem teste no Gauntlet
**Ação:** Adicionar teste na fase Y do Gauntlet
**Prioridade:** ALTA/MÉDIA/BAIXA
```

O Gauntlet verifica se existem flags pendentes e lista no report:
```
## Flags Pendentes (features sem teste)
- FLAG_nova_feature_xxx.md: Feature X não testada
```

Se houver flags com prioridade ALTA, o Gauntlet emite WARNING no report.

### 6. Auto-detecção de hardware

```python
def _detect_hardware(self) -> dict:
    """Detecta GPU e ajusta parâmetros automaticamente."""
    hw = {"gpu": "CPU-only", "vram_total_mib": 0, "num_gpu": 0, "num_ctx": 4096}

    try:
        out = subprocess.check_output(
            ["nvidia-smi", "--query-gpu=name,memory.total", "--format=csv,noheader,nounits"],
            text=True, timeout=5,
        ).strip()
        parts = out.split(",")
        hw["gpu"] = parts[0].strip()
        hw["vram_total_mib"] = int(parts[1].strip())

        vram = hw["vram_total_mib"]
        if vram >= 8000:      # 8GB+ (RTX 4060, etc)
            hw["num_gpu"] = -1   # Todas as layers
            hw["num_ctx"] = 32768
        elif vram >= 6000:    # 6GB (RTX 3060)
            hw["num_gpu"] = 20
            hw["num_ctx"] = 16384
        elif vram >= 4000:    # 4GB (RTX 3050)
            hw["num_gpu"] = 12
            hw["num_ctx"] = 8192
        else:                 # <4GB
            hw["num_gpu"] = 8
            hw["num_ctx"] = 4096
    except Exception:
        pass

    return hw
```

Hardware detectado e registrado no baseline. Ao trocar de PC, os KPIs se ajustam automaticamente e o baseline mostra a diferença.

### 7. Documentação para LLMs fracos

Criar `dev-journey/05-guides/LLM_GUIDE.md`:
- Explicar a estrutura do projeto em linguagem simples
- Mapear cada diretório com propósito claro
- Listar comandos disponíveis (run.sh flags)
- Explicar o fluxo do Gauntlet passo a passo
- Convenções de código (PT-BR, sem emojis, type hints, logging)

Objetivo: um modelo 3B consegue entender o projeto e contribuir.

---

## Verificação

- [x] Checkpoint JSON salvo a cada teste
- [x] GAUNTLET_REPORT.md atualiza em tempo real
- [x] Baseline JSON salvo em baselines/
- [x] Regressões detectadas comparando com baseline anterior
- [x] Flags pendentes listadas no report
- [x] Hardware detectado automaticamente
- [x] Report mostra "APROVADO" ou "REPROVADO"
- [x] `python scripts/sync.py` verifica gauntlet freshness
- [x] Trocar de PC e rodar funciona sem ajuste manual

---

*"A resiliência não é sobre evitar falhas, é sobre sobreviver a elas." -- Nassim Taleb*
