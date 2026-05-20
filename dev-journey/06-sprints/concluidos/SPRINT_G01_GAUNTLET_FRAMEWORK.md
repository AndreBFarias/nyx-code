## 0. SPEC (machine-readable)

```yaml
sprint:
  id: G-01
  title: "Framework do Gauntlet -- validação automatizada de 62 features"
  touches:
    - path: scripts/gauntlet/nyx_gauntlet.py
      reason: "Script único de validação (equivalente ao tui_audit.py da Luna)"
    - path: scripts/gauntlet/__init__.py
      reason: "Pacote do gauntlet"
    - path: run.sh
      reason: "Flag --gauntlet para execução integrada"
    - path: dev-journey/07-reports/gauntlet/
      reason: "Diretório de reports históricos"
  n_to_n_pairs: []
  forbidden:
    - "Mocks de Ollama ou proxy"
    - "Testes que rodem sem Ollama real"
  tests:
    - cmd: "./run.sh --gauntlet --only infra"
      timeout: 180
  acceptance_criteria:
    - "nyx_gauntlet.py executa com Ollama + proxy reais"
    - "Report gerado em GAUNTLET_REPORT.md"
    - "Flag --gauntlet no run.sh funciona"
    - "Flag --only FASE filtra execução"
    - "Acentuação PT-BR correta"
```

---

# Sprint G-01 -- Framework do Gauntlet

**Status:** CONCLUIDA (header corrigido em MASTER-CLEANUP-02 2026-05-20; presença em concluidos/ implica CONCLUIDA conforme convenção do projeto)
**Data:** 2026-04-04
**Prioridade:** ALTA (desbloqueia G-02 a G-08)
**Tipo:** Infra
**Dependências:** --
**Desbloqueia:** G-02, G-03, G-04, G-05, G-06, G-07, G-08
**ADR:** ADR-007 (Gauntlet)

---

## Contexto

O Nyx-Code tem 62 features mapeadas em `dev-journey/04-features/FEATURE_MAP.md`.
Precisamos de um framework de validação automatizado que:
1. Rode o sistema real (Ollama + Proxy) -- zero mocks
2. Teste cada feature com validação real (arquivo criou? grep achou? tool chamou?)
3. Meça KPIs (tempo, tokens, VRAM)
4. Gere report em markdown
5. Suporte execução seletiva por fase

## Implementação

### Fase 1: Estrutura base (`scripts/gauntlet/nyx_gauntlet.py`)

```python
@dataclass
class TestResult:
    feature_id: str       # Ex: "T-01"
    name: str             # Ex: "Read arquivo existente"
    phase: str            # Ex: "tools"
    passed: bool
    elapsed_s: float
    tokens: int
    details: str          # Resposta resumida
    error: str            # Se falhou

class NyxGauntlet:
    def __init__(self, proxy_url, phases, only):
        ...

    async def run(self):
        for phase in self.phases:
            await self._run_phase(phase)
        self._write_report()

    async def _run_phase(self, phase):
        with timeout(PHASE_TIMEOUTS[phase]):
            ...

    async def _send_request(self, messages, tools, max_timeout):
        """Envia request ao proxy e retorna resposta parseada."""
        ...

    def _write_report(self):
        """Gera GAUNTLET_REPORT.md com resultados e KPIs."""
        ...
```

### Fase 2: Fases e timeouts

```python
PHASE_GROUPS = {
    "infra": ["I-01", "I-02", ..., "I-11"],
    "proxy": ["P-01", ..., "P-08"],
    "tools": ["T-01", ..., "T-10"],
    "qualidade": ["Q-01", ..., "Q-07"],
    "performance": ["K-01", ..., "K-10"],
    "visual": ["V-01", ..., "V-07"],
    "config": ["C-01", ..., "C-04"],
    "resiliencia": ["R-01", ..., "R-05"],
    "rapido": infra + proxy + visual + config,
    "completo": todas as fases,
}

PHASE_TIMEOUTS = {
    "infra": 120,
    "proxy": 180,
    "tools": 480,
    "qualidade": 300,
    "performance": 180,
    "visual": 60,
    "config": 60,
    "resiliencia": 180,
}
```

### Fase 3: Integração com run.sh

```bash
# Nova flag no run.sh
--gauntlet)
    GAUNTLET=1
    shift ;;
--only)
    GAUNTLET_ONLY="$2"
    shift 2 ;;

# Após proxy pronto, em vez de iniciar TUI:
if [ "$GAUNTLET" -eq 1 ]; then
    "$SCRIPT_DIR/venv/bin/python" scripts/gauntlet/nyx_gauntlet.py \
        --proxy-url "http://127.0.0.1:${NYX_PROXY_PORT}" \
        --ollama-url "http://${NYX_OLLAMA_HOST}" \
        --only "${GAUNTLET_ONLY:-completo}"
    EXIT_CODE=$?
    exit $EXIT_CODE
fi
```

### Fase 4: Report (`GAUNTLET_REPORT.md`)

```markdown
# Gauntlet Report -- Nyx-Code

**Data:** 2026-04-04 20:30:00
**Modelo:** qwen3:4b
**GPU:** RTX 3050 (num_gpu=12, num_ctx=8192)
**Duração total:** 18min 45s

## Resumo

| Fase | Total | OK | Falhas | Tempo |
|------|-------|-----|--------|-------|
| infra | 11 | 11 | 0 | 1m 30s |
| proxy | 8 | 8 | 0 | 2m 10s |
| tools | 10 | 9 | 1 | 7m 20s |
...

## KPIs de Performance

| Métrica | Valor | Baseline | Status |
|---------|-------|----------|--------|
| Boot time | 12s | <30s | OK |
| TTFR chat | 8s | <15s | OK |
...

## Falhas

| ID | Feature | Erro | Detalhes |
|----|---------|------|----------|
| T-05 | Edit trecho | Sem tool_call | Modelo respondeu texto |

## Histórico

| Data | OK/Total | Duração | Modelo |
|------|----------|---------|--------|
| 2026-04-04 | 58/62 | 18m | qwen3:4b |
```

---

## Verificação

- [ ] `scripts/gauntlet/nyx_gauntlet.py` existe e roda
- [ ] `./run.sh --gauntlet --only infra` executa fase infra
- [ ] Report gerado em `GAUNTLET_REPORT.md`
- [ ] Timeouts por fase funcionam (não trava)
- [ ] Health check Ollama entre fases

---

*"Medir é o primeiro passo para controlar e eventualmente melhorar." -- H. James Harrington*
