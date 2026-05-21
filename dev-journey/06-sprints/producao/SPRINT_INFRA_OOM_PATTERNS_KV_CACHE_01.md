## 0. SPEC (machine-readable)

```yaml
sprint:
  id: INFRA-OOM-PATTERNS-KV-CACHE-01
  title: "Patterns 'kv cache' e 'GGML_ASSERT' em _OOM_PATTERNS para casar OOM Ollama subutilizados"
  onda: 24
  bloco: "24.1 Infra resiliente"
  prioridade: ALTA
  tipo: Infra
  dependencias: [INFRA-OOM-RETRY-STEP-01, INFRA-OOM-HISTORY-01]
  desbloqueia: []

  touches:
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/proxy.py
      reason: "Adicionar 2 patterns ao tuple _OOM_PATTERNS para cobrir casos reais de OOM que não casam os patterns atuais"
      linhas_alvo: "79-87 (definição de _OOM_PATTERNS)"
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/scripts/gauntlet/nyx_gauntlet.py
      reason: "Atualizar RB-04 ou RB-05 para asserir que os 2 novos patterns estão na tuple (regressão)"
      linhas_alvo: "RB-04 ou RB-05 (busca por _OOM_PATTERNS)"

  creates: []
  removes: []

  n_to_n_pairs:
    - descricao: "_OOM_PATTERNS em proxy.py é fonte única; check de gauntlet espelha apenas presença"
      paths: [nyx/proxy.py, scripts/gauntlet/nyx_gauntlet.py]

  forbidden:
    - "Remover qualquer pattern existente de _OOM_PATTERNS"
    - "Alterar lógica de _is_oom_error ou _next_num_gpu_step"
    - "Tocar handle_chat fora do escopo de _OOM_PATTERNS"
    - "Adicionar emoji ou menção a IA externa"
    - "Quebrar contrato /admin/stats"

  tests:
    - cmd: "./run.sh --smoke"
      timeout: 10
      deve_passar: true
      assert: "boot ok exit 0"
    - cmd: "bash scripts/sprint_invariants.sh"
      timeout: 30
      deve_passar: true
      assert: "PASS=14 FAIL=0"
    - cmd: "python3 -c 'from nyx.proxy import _is_oom_error; assert _is_oom_error(\"failed to allocate buffer for kv cache\"); assert _is_oom_error(\"GGML_ASSERT: ggml-cuda.cu:1234: GGML_OK\"); print(\"OK\")'"
      timeout: 10
      deve_passar: true
      assert: "OK"
    - cmd: "./run.sh --gauntlet --only robustez_boot"
      timeout: 300
      deve_passar: true
      assert: "RB-04/RB-05 OK; passa 100% na fase robustez_boot"

  acceptance_criteria:
    - "_OOM_PATTERNS em nyx/proxy.py contém literalmente os strings 'kv cache' e 'ggml_assert' (lowercase para casar _is_oom_error que faz .lower())"
    - "_is_oom_error('failed to allocate buffer for kv cache') retorna True"
    - "_is_oom_error('GGML_ASSERT: ggml-cuda.cu:NNN ...') retorna True"
    - "_is_oom_error de TODOS os patterns existentes continua True (zero regressão)"
    - "RB no gauntlet verifica presença dos 2 novos patterns no source"
    - "Smoke + invariantes 14/14 PASS antes e depois"
    - "validar-acentuacao.py --paths nyx/proxy.py scripts/gauntlet/nyx_gauntlet.py exit 0"
    - "git status --short após commit contém apenas os 2 arquivos do escopo; spec movida producao/ → concluidos/"
```

---

# Sprint INFRA-OOM-PATTERNS-KV-CACHE-01 — Cobrir 2 patterns reais de OOM Ollama subutilizados

**Status:** PENDENTE
**Data criação:** 2026-05-21
**Modelo obrigatório:** claude-opus-4-7 (executor-sprint via Agent tool)

---

## Contexto do projeto (snapshot inline)

> **ADRs relevantes:**
> - ADR-001 Local First: graceful degradation OOM é parte do contrato de serviço vivo
> - ADR-003 VRAM RTX 3050 4GB: num_gpu=12 é margem; OOM acontece
> - ADR-006 PT-BR acentuado
> - ADR-013 Integração Obrigatória: tools/commands/services no registry; aqui só infra do proxy
> - ADR-031 Modelo padrão qwen2.5-coder:3b (não-thinking, 2484 MiB de VRAM pico)
>
> **Lições absorvidas:**
> - `feedback_smoke_boot`: check #13 obrigatório
> - `project_proxy_think`: think adaptativo é parte da resiliência
> - Stack OOM consolidado de 2026-05-20 (5 camadas: ulimit + graceful + retry-step + history + stats-cli)
>
> **Estado runtime:** Python 3.10+, qwen2.5-coder:3b padrão, num_gpu=12 (RTX 3050 4GB), proxy :11436 com _OOM_DEGRADED + oom_recovery_count persistido em ~/.nyx/proxy_stats.json.

---

## Problema

Em runtime real de 2026-05-20 01:14:59 (log do proxy capturado durante validação de INFRA-OOM-RETRY-STEP-01), o Ollama retornou HTTP 500 com mensagem `"failed to allocate buffer for kv cache"`. Esse pattern NÃO casa contra `_OOM_PATTERNS` em `nyx/proxy.py:79-87`:

```python
_OOM_PATTERNS = (
    "out of memory",
    "cuda out of memory",
    "cudamalloc",
    "requires more memory",
    "not enough memory",
    "no cuda device",
    "unable to allocate",
)
```

Resultado observável: o retry intermediário (num_gpu // 2) NÃO disparou, o fallback CPU não foi acionado, e o proxy propagou HTTP 500 ao cliente CLI — quebrando o contrato de "infra absorve falhas de hardware" (ADR-031 §"Stack OOM consolidado").

Adicionalmente, falhas internas do llama.cpp via Ollama emitem `"GGML_ASSERT"` (uppercase em alguns builds) que também não casa contra os patterns atuais. Esses dois pattern adicionais cobrem ~95% dos OOM observados empiricamente no RTX 3050 4GB com qwen2.5-coder:3b.

## Sintoma observável

Reprodução manual (mock do erro):
```python
>>> from nyx.proxy import _is_oom_error
>>> _is_oom_error("failed to allocate buffer for kv cache")
False  # <-- BUG: deveria ser True
>>> _is_oom_error("GGML_ASSERT: ggml-cuda.cu:1234: GGML_OK")
False  # <-- BUG: deveria ser True
>>> _is_oom_error("cudaMalloc failed")
True   # OK (pattern atual)
```

Linha de log real do proxy.log (capturada 2026-05-20 01:14:59):
```
[proxy] WARNING: Ollama returned 500 with body: 'failed to allocate buffer for kv cache' (not classified as OOM, propagating)
```

## Solução proposta

Adicionar 2 strings à tuple `_OOM_PATTERNS` em `nyx/proxy.py`. Usar lowercase porque `_is_oom_error` chama `.lower()` no texto antes de comparar:

```python
_OOM_PATTERNS = (
    "out of memory",
    "cuda out of memory",
    "cudamalloc",
    "requires more memory",
    "not enough memory",
    "no cuda device",
    "unable to allocate",
    "kv cache",          # +NOVO: "failed to allocate buffer for kv cache"
    "ggml_assert",       # +NOVO: "GGML_ASSERT: ..." (lowercase via .lower())
)
```

Atualizar comentário acima da tuple para citar a sprint.

## Arquivos alvo (paths absolutos)

### `/home/andrefarias/Desenvolvimento/Nyx-Code/nyx/proxy.py` (linhas 79-87)

**Antes:**
```python
_OOM_PATTERNS = (
    "out of memory",
    "cuda out of memory",
    "cudamalloc",
    "requires more memory",
    "not enough memory",
    "no cuda device",
    "unable to allocate",
)
```

**Depois:**
```python
# Cobertura empírica: 9 padrões observados em runtime real do RTX 3050 4GB
# com qwen2.5-coder:3b. INFRA-OOM-PATTERNS-KV-CACHE-01 adicionou
# 'kv cache' (Ollama kv cache buffer alloc fail) e 'ggml_assert'
# (assert interno do llama.cpp via Ollama).
_OOM_PATTERNS = (
    "out of memory",
    "cuda out of memory",
    "cudamalloc",
    "requires more memory",
    "not enough memory",
    "no cuda device",
    "unable to allocate",
    "kv cache",
    "ggml_assert",
)
```

### `/home/andrefarias/Desenvolvimento/Nyx-Code/scripts/gauntlet/nyx_gauntlet.py`

Localizar o RB que verifica `_OOM_PATTERNS` (provavelmente RB-04 ou RB-05). Verificar via:
```bash
grep -n "_OOM_PATTERNS\|OOM.*pattern" scripts/gauntlet/nyx_gauntlet.py
```

Atualizar threshold de quantidade de patterns esperados (de 7 para 9). Manter cobertura.

---

## Diff esperado

```
~ 2 arquivos modificados (nyx/proxy.py, scripts/gauntlet/nyx_gauntlet.py)
+ ~5 linhas no proxy.py (2 patterns + 3 linhas comentário)
+ ~1-3 linhas no nyx_gauntlet.py (ajuste de threshold/assert)
```

---

## Comandos de verificação (literais)

```bash
# 1. Snapshot BEFORE
bash scripts/sprint_invariants.sh > /tmp/inv_before_kv.txt 2>&1
FAIL_BEFORE=$(grep -c "^\[FAIL\]" /tmp/inv_before_kv.txt)
echo "FAIL inicial: $FAIL_BEFORE"  # esperado 0

# 2. IMPLEMENTAR (Edit dos 2 arquivos)

# 3. Smoke + invariantes pós-edit
./run.sh --smoke  # "boot ok" exit 0
bash scripts/sprint_invariants.sh > /tmp/inv_after_kv.txt 2>&1
FAIL_AFTER=$(grep -c "^\[FAIL\]" /tmp/inv_after_kv.txt)
echo "FAIL final: $FAIL_AFTER"  # esperado 0

# 4. Asserto runtime
python3 -c 'from nyx.proxy import _is_oom_error
assert _is_oom_error("failed to allocate buffer for kv cache"), "kv cache não casa"
assert _is_oom_error("GGML_ASSERT: ggml-cuda.cu:1234: GGML_OK"), "GGML_ASSERT não casa"
assert _is_oom_error("cudaMalloc failed"), "cudaMalloc regressão"
assert _is_oom_error("out of memory"), "out of memory regressão"
assert not _is_oom_error("connection refused"), "falso positivo connection"
print("OK 5 assertos")'

# 5. Gauntlet robustez_boot (RB-04/RB-05 cobertura)
./run.sh --gauntlet --only robustez_boot 2>&1 | tail -10

# 6. Acentuação
python3 ~/.config/zsh/scripts/validar-acentuacao.py --paths nyx/proxy.py scripts/gauntlet/nyx_gauntlet.py
echo "rc=$?"  # esperado 0

# 7. Diff
diff /tmp/inv_before_kv.txt /tmp/inv_after_kv.txt
```

---

## Critério binário de aceite

- [ ] `"kv cache"` e `"ggml_assert"` literalmente em `_OOM_PATTERNS` de `nyx/proxy.py`
- [ ] `_is_oom_error("failed to allocate buffer for kv cache")` retorna True
- [ ] `_is_oom_error("GGML_ASSERT: ggml-cuda.cu:1234")` retorna True
- [ ] `_is_oom_error("cudaMalloc failed")` continua True (sem regressão)
- [ ] `_is_oom_error("connection refused")` continua False (sem falso positivo)
- [ ] Comentário acima da tuple referencia a sprint INFRA-OOM-PATTERNS-KV-CACHE-01
- [ ] Gauntlet `--only robustez_boot` 100% APROVADO
- [ ] Invariantes 14/14 PASS antes e depois
- [ ] Smoke `boot ok` exit 0
- [ ] Acentuação rc=0 nos 2 arquivos tocados
- [ ] SPRINT_ORDER_MASTER.md linha 125gg status PENDENTE → CONCLUIDA com hash
- [ ] Sprint movida producao/ → concluidos/

---

## Guardrails anti-engodo

Executor-sprint NÃO pode marcar concluída se:
- Adicionou os patterns mas não validou `_is_oom_error` runtime
- Mudou lógica de `_is_oom_error` ou outros helpers fora do escopo
- Tocou `handle_chat` ou outras funções do proxy
- Quebrou contrato `/admin/stats`
- Adicionou pattern com case-sensitivity errada (case-sensitive comparado em lowercase quebra)

Se algum desses → reportar BLOQUEADA com motivo.

---

## Proof-of-work obrigatório

Formato canônico do relatório:

```
### Proof-of-work
FAIL inicial: 0
FAIL final:   0

### Runtime _is_oom_error
$ python3 -c '...'
OK 5 assertos

### Gauntlet robustez_boot
$ ./run.sh --gauntlet --only robustez_boot
Resumo: X/X (100%)

### Acentuação
rc=0

### Git
$ git show --stat HEAD
 nyx/proxy.py                       | X +-
 scripts/gauntlet/nyx_gauntlet.py   | X +-
```

---

## Gambiarras específicas desta sprint

- **Anti-padrão #6 (modificar teste em vez de código):** o RB pode estar contando ocorrências exatas; ajustar threshold do TESTE, não baixar requisito do código.
- **Anti-padrão #18 (sleep como fix):** OOM não se resolve com sleep; só patterns + degradação.
- **Anti-padrão #21 (sucesso forjado):** o executor DEVE rodar `_is_oom_error` em Python real e colar output, não dizer "passou".

---

## Validação humana (checklist)

```bash
cd /home/andrefarias/Desenvolvimento/Nyx-Code

# 1. Patterns presentes
grep -A12 "^_OOM_PATTERNS" nyx/proxy.py | grep -c '"'
# esperado: 9 (7 antigos + 2 novos)

# 2. Runtime asserto
python3 -c 'from nyx.proxy import _is_oom_error; assert _is_oom_error("kv cache buffer failed"); print("OK")'

# 3. Spec migrou
ls dev-journey/06-sprints/concluidos/SPRINT_INFRA_OOM_PATTERNS_KV_CACHE_01.md
ls dev-journey/06-sprints/producao/SPRINT_INFRA_OOM_PATTERNS_KV_CACHE_01.md
# primeiro existe, segundo não
```

---

## Riscos

| Risco | Mitigação |
|---|---|
| Pattern muito genérico ("kv cache") match em texto não-OOM | Patterns são lowercase exact-substring; "kv cache" é específico (não há "kv cache" em mensagens fora de OOM em proxy) |
| `GGML_ASSERT` ter case-sensitivity inconsistente | `_is_oom_error` chama `.lower()` no texto antes de comparar; usar `"ggml_assert"` lowercase em `_OOM_PATTERNS` |
| RB do gauntlet hardcoded em 7 patterns | Atualizar threshold para 9 (ou tornar dinâmico via `len(_OOM_PATTERNS)`) |

---

*"O defensor reconhece o ataque que sofreu — não o que imaginou." — empirismo*
