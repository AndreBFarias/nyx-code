# SPRINT AUTOTUNE-FIX-02 — cap RTX 3050 4GB para num_gpu=12 (valor canônico ADR-003)

## 0. SPEC (machine-readable)

```yaml
sprint:
  id: AUTOTUNE-FIX-02
  title: "Baixar cap VRAM 4GB de 15 para 12 (ADR-003 canônico)"
  onda: 22
  bloco: 2.6
  prioridade: CRÍTICA
  tipo: Bugfix (iteração sobre AUTOTUNE-FIX-01)
  dependencias: [AUTOTUNE-FIX-01]
  desbloqueia: [VALIDATE-ONDA-20, CTX-02]

  touches:
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/scripts/detect_gpu.py
      reason: "VRAM_CAP_MB_TO_LAYERS[(4096, 15)] ainda OOM em inferência real com system prompt inflado (RepoMap + 35 tools schemas). ADR-003 prescreve 12 como 'muito estável'."
      linhas_alvo: "VRAM_CAP_MB_TO_LAYERS"

  creates: []
  removes: []

  forbidden:
    - "Remover cap -- mantém regressão"
    - "Baixar cap de GPUs maiores (6GB/8GB) sem evidência"
    - "Adicionar emoji"

  tests:
    - cmd: "python scripts/detect_gpu.py --for-model qwen3:4b"
      esperado: "<= 12 em RTX 3050 4GB"
    - cmd: "VALIDATE-ONDA-20 rodada 2: 'lembra que eu uso pyenv 3.12' -> tool_call sem 'model runner unexpectedly stopped'"
      timeout: 120
    - cmd: "./run.sh --gauntlet --only contexto"
      timeout: 300
      esperado: "11/11 APROVADO"

  acceptance_criteria:
    - "calc_num_gpu('qwen3:4b', 3800, 4096) <= 12"
    - "TUI real responde a pedido natural sem 'model runner has unexpectedly stopped'"
    - "Gauntlet contexto 11/11"
    - "FAIL invariantes <= baseline"
```

---

**Status:** CONCLUIDA (commit d491600)
**Data criação:** 2026-04-20
**Origem:** VALIDATE-ONDA-20 rodada 2 reproduziu OOM do Ollama runner quando o prompt real (system = 2KB RepoMap + tools_schemas=35 * ~200B + history + user) chegou ao LLM com num_gpu=15. Mensagem: "model runner has unexpectedly stopped, this may be due to resource limitations". ADR-003 tabela explicitamente diz `num_gpu=20 -> instável`; o cap 15 estava no limite. Canônico: 12 ("muito estável").
**Modelo obrigatório:** claude-opus-4-7 (sem subagentes)

---

## Fix

```python
# antes
VRAM_CAP_MB_TO_LAYERS = [(4096, 15), (6144, 28), (8192, 36)]
# depois
VRAM_CAP_MB_TO_LAYERS = [(4096, 12), (6144, 28), (8192, 36)]
```

1 linha de diff. ADR-003 exato.

---

## Proof-of-work

- `python scripts/detect_gpu.py --for-model qwen3:4b` → ≤ 12
- Screenshot rodada 2: pedido natural → tool_call sem erro
- Gauntlet contexto 11/11

*"O limite aceito evita o limite imposto." — ADR-003*
