## 0. SPEC (machine-readable)

```yaml
sprint:
  id: PORT-03
  title: "Robustez de boot (R-02, R-03, R-04)"
  touches:
    - path: scripts/gauntlet/fases/robustez_boot.py
      reason: "Nova fase com 3 testes E2E de cenários de falha"
    - path: scripts/gauntlet/nyx_gauntlet.py
      reason: "Registrar fase robustez_boot"
    - path: run.sh
      reason: "Melhorar mensagens de erro em kill_existing_ollama, start_ollama, check_model"
    - path: nyx/proxy.py
      reason: "Detectar OOM e degradar num_gpu=0 (graceful degradation ADR-001)"
  n_to_n_pairs:
    - ["run.sh", "nyx/proxy.py"]
  forbidden:
    - "Crashar em cenário de OOM (deve degradar)"
    - "Mostrar stacktrace cru ao usuário (só mensagem formatada)"
    - "Remover tratamento existente, apenas melhorar"
  tests:
    - cmd: "./run.sh --gauntlet --only robustez_boot"
      timeout: 180
  acceptance_criteria:
    - "R-02: modelo inexistente gera exit != 0 com mensagem clara"
    - "R-03: porta 11435 ocupada gera mensagem com instrução de kill/port"
    - "R-04: NYX_NUM_GPU irreal (999) degrada para num_gpu=0 em vez de crashar"
    - "Nenhum stacktrace cru chega ao terminal do usuário"
    - "Acentuação PT-BR correta"
```

> Executar antes de começar: ler `run.sh` funções `kill_existing_ollama`, `start_ollama`, `check_model`, `configure_vram`. Ler `nyx/proxy.py` tratamento de erros.

---

# Sprint PORT-03 -- Robustez de boot

**Status:** CONCLUIDA
**Data:** 2026-04-16
**Prioridade:** ALTA
**Tipo:** Infra
**Dependências:** PORT-01, PORT-02
**Desbloqueia:** I-02 (pré-requisito de portabilidade completa)

---

## Problema / Contexto

`dev-journey/04-features/FEATURE_MAP.md` lista três cenários de falha de boot sem teste:

- **R-02:** modelo não existe (ex.: usuário muda `NYX_MODEL` para nome errado)
- **R-03:** porta 11435 ocupada (outro Ollama rodando, ou qualquer processo)
- **R-04:** VRAM insuficiente (GPU menor que o esperado, ou outros processos consumindo VRAM)

Em máquina nova qualquer um desses pode acontecer. Hoje `run.sh` trata parcialmente R-02 e R-03 (tenta pull, tenta matar processo), mas as mensagens são ruins e R-04 não é tratado — um `num_gpu` muito alto crasha Ollama em vez de degradar.

ADR-001 exige graceful degradation: o sistema deve cair para CPU em vez de falhar completamente.

## Implementação

### Fase 1: Melhorar mensagens em `run.sh`

Função `check_model`:

```bash
check_model() {
    if ! "$OLLAMA_BIN" list 2>/dev/null | grep -q "$MODEL"; then
        log_warn "Modelo $MODEL não encontrado localmente"
        log_nyx "Tentando baixar $MODEL..."
        if ! "$OLLAMA_BIN" pull "$MODEL"; then
            log_err "Falha ao baixar $MODEL."
            log_err "Possíveis causas:"
            log_err "  1. Nome de modelo incorreto (verifique NYX_MODEL no .env)"
            log_err "  2. Sem conexão com registry Ollama"
            log_err "  3. Modelo não existe no registry"
            log_err "Modelos disponíveis localmente:"
            "$OLLAMA_BIN" list 2>/dev/null | sed 's/^/    /' || true
            exit 1
        fi
    fi
}
```

Função `kill_existing_ollama` (R-03):

```bash
kill_existing_ollama() {
    pkill -f "nyx/proxy.py" 2>/dev/null || true
    local existing_pid
    existing_pid=$(lsof -ti:"$NYX_OLLAMA_PORT" 2>/dev/null || true)
    if [ -n "$existing_pid" ]; then
        local owner_cmd
        owner_cmd=$(ps -p "$existing_pid" -o comm= 2>/dev/null || echo "desconhecido")
        log_warn "Porta $NYX_OLLAMA_PORT ocupada por PID $existing_pid ($owner_cmd)"

        # Se for ollama, tentamos matar normal
        if echo "$owner_cmd" | grep -qi ollama; then
            log_nyx "Detectado Ollama antigo. Parando..."
            kill "$existing_pid" 2>/dev/null || true
            sleep 1
            kill -9 "$existing_pid" 2>/dev/null || true
        else
            log_err "Processo não-Ollama ocupando a porta. Opções:"
            log_err "  1. Matar manualmente: kill $existing_pid"
            log_err "  2. Usar outra porta: NYX_OLLAMA_PORT=11437 ./run.sh"
            log_err "  3. Configurar em .env: NYX_OLLAMA_PORT=XXXXX"
            exit 1
        fi
    fi
    pkill -f "$OLLAMA_BIN serve" 2>/dev/null || true
    sleep 1
}
```

### Fase 2: Graceful degradation em `nyx/proxy.py` (R-04)

No handler de `/v1/chat/completions`, após receber erro do Ollama, detectar padrões de OOM:

```python
OOM_PATTERNS = [
    "out of memory",
    "CUDA out of memory",
    "cudaMalloc",
    "requires more memory",
]

if any(p.lower() in str(error).lower() for p in OOM_PATTERNS):
    logger.warning("OOM detectado. Degradando num_gpu para 0 (CPU)")
    self.num_gpu = 0
    # retry uma única vez com num_gpu=0
    return await self._retry_with_cpu(request)
```

Flag `self.num_gpu_degraded` para não ficar tentando retry infinito. Log em `logs/proxy.log` registra a degradação.

### Fase 3: Testes Gauntlet (fase `robustez_boot`)

Todos os testes rodam `run.sh` como subprocess com timeout curto (30s cada), verificam exit code e conteúdo de stdout/stderr.

| ID | Nome | Setup | Validação |
|----|------|-------|-----------|
| RB-01 | Modelo inexistente | `NYX_MODEL=qwen-zzz:99b ./run.sh` com timeout 30s | exit != 0 E stderr contém "não encontrado" ou "Falha ao baixar" |
| RB-02 | Porta ocupada | `nc -l 11435 &` antes, depois `./run.sh` timeout 15s | stderr contém "ocupada" E "kill" E instrução de porta alternativa |
| RB-03 | OOM graceful | `NYX_NUM_GPU=999 ./run.sh` timeout 30s | proxy.log contém "Degradando num_gpu para 0" E exit 0 (não crasha) |

Helper em `scripts/gauntlet/fases/robustez_boot.py`:

```python
def run_with_env(env_overrides: dict, timeout: int = 30) -> tuple[int, str, str]:
    env = os.environ.copy()
    env.update(env_overrides)
    proc = subprocess.run(
        ["./run.sh"],
        env=env, timeout=timeout,
        capture_output=True, text=True,
    )
    return proc.returncode, proc.stdout, proc.stderr
```

Cada teste faz cleanup (kill processos criados) no `finally`.

## Verificação

- [ ] R-02: `NYX_MODEL=inexistente:99b ./run.sh` sai com mensagem clara
- [ ] R-03: `nc -l 11435 &` + `./run.sh` dá mensagem com instrução
- [ ] R-04: `NYX_NUM_GPU=999 ./run.sh` degrada para CPU sem crashar
- [ ] `logs/proxy.log` registra OOM e degradação
- [ ] Gauntlet fase `robustez_boot` passa 3/3

---

*"Um sistema robusto falha com elegância, não com pânico." -- James Bach*
