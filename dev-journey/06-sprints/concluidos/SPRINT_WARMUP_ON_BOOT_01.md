# SPRINT WARMUP-ON-BOOT-01 — Warmup agressivo no boot para evitar P95 outlier

## 0. SPEC (machine-readable)

```yaml
sprint:
  id: WARMUP-ON-BOOT-01
  title: "Warmup no boot do stack carrega pesos completos do modelo; primeira chamada de sessão respeita SLA <8s"
  onda: 23
  bloco: 23.0 Performance
  prioridade: MÉDIA
  tipo: Perf+Infra
  dependencias: [PERF-INFERENCE-01]
  desbloqueia: []
  origem: "Achado A3 do executor PERF-INFERENCE-01: 'outliers de P95 em runs sem warmup intenso: call1 isolado bate 22s. Indica cold start persistente apesar de warmup_model em run.sh:226'."

  touches:
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/run.sh
      reason: "Função warmup_model: enviar 2-3 chamadas de aquecimento (saudação + tool-like) em vez de só 'hi'"
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/scripts/gauntlet/fixtures/perf_inference.py
      reason: "Medir cold-call vs warm-call explicitamente; gravar separadamente"

  creates: []

  removes: []

  n_to_n_pairs: []

  forbidden:
    - "Warmup >60s no boot (usuário espera demais antes do prompt)"
    - "Warmup carrega modelo grande sem checar VRAM (OOM)"
    - "Warmup silencioso (deve mostrar 'aquecendo modelo...' com timeout)"
    - "Sleep artificial entre chamadas de warmup"
    - "Emoji"

  tests:
    - cmd: "./run.sh --smoke"
      timeout: 60
      deve_passar: true
    - cmd: "./venv/bin/python scripts/gauntlet/fixtures/perf_inference.py --measure-cold"
      timeout: 600
      deve_passar: true
      nota: "Mede primeira chamada de sessão limpa; deve ser <= 8s (P95)"
    - cmd: "bash scripts/sprint_invariants.sh"
      timeout: 60
      deve_passar: "FAIL_AFTER <= FAIL_BEFORE"

  acceptance_criteria:
    - "warmup_model em run.sh: envia 2 chamadas (saudação curta + 1 com tool dummy)"
    - "Após warmup, modelo está com pesos completos em VRAM (verificar via nvidia-smi delta)"
    - "Tempo total de warmup adicional: <= 15s (acima do baseline)"
    - "Primeira chamada de sessão fresca em fixture perf_inference --measure-cold: P95 <= 8s"
    - "Log claro 'aquecendo modelo...' visível ao usuário"
    - "Não regride boot smoke (continua passando em <60s)"
    - "Em low-VRAM (<1.5 GiB livre): warmup curto, log de warning, segue"
    - "Gauntlet rapido + proxy 100%"
    - "PT-BR; zero emoji; zero menção a IA"
```

---

**Status:** CONCLUIDA
**Data criação:** 2026-05-16
**Data conclusão:** 2026-05-17
**Commit:** e0f7836 (`feat(WARMUP-ON-BOOT-01): warmup duplo no boot reduz cold start`)
**Modelo obrigatório:** claude-opus-4-7 (sem subagentes)
**Origem:** achado colateral de PERF-INFERENCE-01

## Métricas

- Warmup duplo no boot: ~3s (margem 80% vs. 15s limite)
- Cold call após warmup: 0.634s (margem 92% vs. 8s SLA)
- Gauntlet rápido: 18/18 (100%) em 5.7s (sem regressão)
- VRAM: 64 MiB livre baseline → 1176 MiB modelo carregado (qwen2.5-coder:3b)
- Low-VRAM guard: ativa quando memory.free < 1500 MiB; pula warmup 2 com log_warn

## Notas de execução

- `warmup_model()` em `run.sh` reescrita: 2 chamadas via proxy (saudação + tool-like).
- Chamada explícita após proxy iniciar; pulada em modo `--gauntlet`.
- Flag `--measure-cold` adicionada em `scripts/gauntlet/fixtures/perf_inference.py`; grava `logs/perf_cold.json`.
- 1 sprint anti-débito derivada: **LANG-PROMPT-ACENT-01** (acentuação no `NYX_SYSTEM_PROMPT`).

---

# Sprint WARMUP-ON-BOOT-01

## Contexto

O `warmup_model` em `run.sh:226` envia 1 chamada `{"content": "hi"}` com `max_tokens: 3`. Isso carrega o modelo na VRAM mas não exercita o caminho com tools/think. Quando o usuário envia a primeira mensagem real, o modelo ainda paga um cold start de ~20s.

## Solução

### `run.sh` — warmup duplo

```bash
warmup_model() {
    log_boot "Aquecendo modelo $MODEL..."

    # Warmup 1: saudação curta (carrega pesos)
    curl -sf --max-time 30 \
        "http://${NYX_OLLAMA_HOST}:${NYX_OLLAMA_PORT}/v1/chat/completions" \
        -H "Content-Type: application/json" \
        -d "{\"model\":\"$MODEL\",\"messages\":[{\"role\":\"user\",\"content\":\"oi\"}],\"max_tokens\":5}" \
        > /dev/null 2>&1

    # Warmup 2: tool-like (exercita think + tool path)
    curl -sf --max-time 30 \
        "http://${NYX_OLLAMA_HOST}:${NYX_OLLAMA_PORT}/v1/chat/completions" \
        -H "Content-Type: application/json" \
        -d "{
            \"model\":\"$MODEL\",
            \"messages\":[{\"role\":\"user\",\"content\":\"leia README\"}],
            \"max_tokens\":20,
            \"tools\":[{\"type\":\"function\",\"function\":{\"name\":\"Read\",\"parameters\":{\"type\":\"object\",\"properties\":{\"path\":{\"type\":\"string\"}}}}}]
        }" \
        > /dev/null 2>&1

    log_boot "Modelo aquecido"
}
```

### `perf_inference.py` --measure-cold

```python
# Mede primeira chamada após ./run.sh fresh, sem aquecimento manual
# Roda apenas 1 vez, grava em logs/perf_cold.json
```

## Verificação

```bash
./run.sh &
sleep 25  # esperar warmup completo
./venv/bin/python scripts/gauntlet/fixtures/perf_inference.py --measure-cold
# Esperado: primeira chamada P95 <= 8s
```

## Trade-off

- **+10-15s no boot total** (warmup extra)
- **-15-20s na primeira mensagem do usuário** (modelo já está hot)

Saldo positivo: usuário sente boot mais lento por 10s, mas primeira interação é instantânea.

---

*"O tempo gasto preparando vale o triplo gasto reagindo." -- princípio de hospitalidade aplicado a inferência*
