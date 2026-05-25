# SPRINT 222 — INFRA-PRELOAD-VRAM-CONSERVATIVE-01

## 0. SPEC (machine-readable)

```yaml
sprint:
  id: INFRA-PRELOAD-VRAM-CONSERVATIVE-01
  title: "Cap empírico de num_gpu reduzido em RTX 3050 4GB + BRIEF atualizado"
  onda: 31
  prioridade: ALTA
  tipo: Refactor
  dependencias: []
  desbloqueia: [TUI-SLASH-DISPATCH-INVESTIGATE-01, TUI-NYX-SOFT-BOX-01]

  touches:
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/scripts/detect_gpu.py
      reason: "VRAM_CAP_MB_TO_LAYERS desatualizado; 4096->12 causa OOM crônico"
      linhas_alvo: "44-72"
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/dev-journey/03-decisions/ADR_003_VRAM_MANAGEMENT.md
      reason: "Tabela empírica precisa registrar realidade 2026-05-25"
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/VALIDATOR_BRIEF.md
      reason: "Bundle do achado colateral C2: nova seção CORE com lição"
  creates: []
  removes: []

  n_to_n_pairs:
    - descricao: "Cap empírico citado em detect_gpu.py:62 + ADR-003 + BRIEF; manter coerência"  # noqa-acento
      paths:
        - scripts/detect_gpu.py
        - dev-journey/03-decisions/ADR_003_VRAM_MANAGEMENT.md
        - VALIDATOR_BRIEF.md

  forbidden:
    - "Mexer em proxy.py (retry step funciona; só estamos reduzindo entrada do auto-tune)"
    - "Quebrar override NYX_NUM_GPU em .env (preservar opt-in agressivo)"
    - "Adicionar emoji"
    - "Mencao a IA proprietaria em codigo/commit"   # noqa-anonimato
    - "Path absoluto hardcoded"

  tests:
    - cmd: "./run.sh --smoke"
      timeout: 10
      deve_passar: true
    - cmd: "./venv/bin/python scripts/detect_gpu.py --for-model qwen2.5-coder:3b"
      timeout: 10
      deve_passar: true
    - cmd: "bash scripts/sprint_invariants.sh"
      timeout: 30
      deve_passar: true

  acceptance_criteria:
    - "VRAM_CAP_MB_TO_LAYERS para 4096 baixou de 12 para 6"
    - "3 boots consecutivos com Chrome aberto NÃO incrementam oom_recovery_count"
    - "Warning 'Pré-carga falhou' não aparece em logs/boot.log após sprint"
    - "ADR-003 ganha tabela empírica nova com data 2026-05-25"
    - "VALIDATOR_BRIEF.md ganha seção CORE 'Cap empírico de VRAM em RTX 3050 4GB'"
    - "Smoke boot ok exit 0"
    - "Invariantes 14/14 PASS"
    - "Acentuação rc=0 em todos arquivos modificados"
```

---

# Sprint 222 — INFRA-PRELOAD-VRAM-CONSERVATIVE-01

**Status:** PENDENTE
**Data criação:** 2026-05-25
**Modelo obrigatório:** claude-opus-4-7 (sem subagentes)

---

## Contexto do projeto (snapshot)

> **ADRs relevantes:**
> - ADR-001 Local First. ADR-003 VRAM Management. ADR-031 modelo qwen2.5-coder:3b.
> - ADR-004 Zero Emojis. ADR-005 Anonimato. ADR-006 PT-BR.
> - ADR-013 Integração Obrigatória. ADR-014 Testes via Gauntlet.
>
> **Estado do sistema:**
> - Python 3.10+, RTX 3050 4GB (VRAM total 4096 MiB). Ollama 11435 + proxy 11436.
> - Auto-tune: `scripts/detect_gpu.py --for-model X` retorna num_gpu sugerido para o modelo.
> - INFRA-OOM-RETRY-STEP-01 (sprint 125aa) tenta `current // 2` antes de cair para CPU.
> - INFRA-OOM-HISTORY-01 (125cc) persiste `oom_recovery_count` em `~/.nyx/proxy_stats.json`.
> - Sprint anterior: ONDA-30 fechada (TEXTUAL-CUTOVER-01).

---

## Problema

`scripts/detect_gpu.py` linha 62 declara `VRAM_CAP_MB_TO_LAYERS = [(4096, 12), (6144, 28), (8192, 36)]`. Cap empírico de **12 layers para 4GB** está desatualizado. Em uso real (Chrome aberto + terminal + Spellbook + dpkg ocupando ~600 MiB residual), `num_gpu=12` resulta em `cudaMalloc failed: out of memory` durante a pré-carga do qwen2.5-coder:3b. Proxy então degrada 12 → 6 → 0 (CPU) e a sessão inteira roda em CPU lenta.

### Sintoma observável

`logs/boot.log` (2026-05-25 16:08:09):
```
[nyx] Pré-carregando modelo (num_gpu=12)...
[nyx] Pré-carga falhou (modelo será carregado na primeira requisição)
```

`logs/proxy.log` (mesma janela):
```
16:08:11 [proxy] ERROR: Ollama 500: cudaMalloc failed: out of memory
16:08:11 [proxy] WARNING: OOM degradation step: 12 -> 6
16:08:13 [proxy] WARNING: OOM detectado. Degradando num_gpu=0 (CPU)
```

`~/.nyx/proxy_stats.json` em 2026-05-25:
```json
{"version": "1", "oom_recovery_count": 23, "first_session": "2026-05-21T17:08:53Z", "last_recovery": "2026-05-25T19:08:18Z"}
```

**23 OOMs consecutivos em 4 dias.** Padrão sempre o mesmo: `12 → 6 → 0`. Cap 12 nunca cabe nesta máquina específica.

Implicação para o usuário: latência P50 em CPU > 4-10s (vs <2s em GPU). Resposta "indentação em python" levou 17.9s. "Pensando..." visível tempo demais — percepção de travamento.

---

## Solução proposta

Reduzir cap de 4GB para **6 layers** (estabilidade empírica). Documentar em ADR-003 + VALIDATOR_BRIEF.md. Preservar opt-in agressivo via `.env` `NYX_NUM_GPU=12` (override existente).

---

## Arquivos alvo

### `/home/andrefarias/Desenvolvimento/Nyx-Code/scripts/detect_gpu.py`

**Localização aproximada:** linhas 56-72 (drift tolerado).

**Antes:**
```python
# Cap por VRAM total (ADR-003 + ADR-009). A heurística por VRAM livre é otimista
# em hardware pequeno porque ignora overhead dinâmico do KV cache, buffers do
# Ollama e compartilhamento com desktop. Tabela empírica:
#   4GB  -> num_gpu=12 muito estável, 15 estável, 20 instável, 37 OOM
#   6GB  -> num_gpu=28 confortável
#   8GB  -> num_gpu=36 confortável (~full GPU)
VRAM_CAP_MB_TO_LAYERS: list[tuple[int, int]] = [
    (4096, 12),
    (6144, 28),
    (8192, 36),
]
```

**Depois:**
```python
# Cap por VRAM total (ADR-003 + ADR-009). A heurística por VRAM livre é otimista
# em hardware pequeno porque ignora overhead dinâmico do KV cache, buffers do
# Ollama e compartilhamento com desktop. Tabela empírica revisada 2026-05-25
# após audit de 23 OOMs consecutivos com cap=12 em RTX 3050 4GB com Chrome:
#   4GB  -> num_gpu=6 estável, 12 OOM crônico (vide ~/.nyx/proxy_stats.json)
#   6GB  -> num_gpu=28 confortável
#   8GB  -> num_gpu=36 confortável (~full GPU)
# Override agressivo via .env NYX_NUM_GPU=12 (auto-tune respeita o ENV).
VRAM_CAP_MB_TO_LAYERS: list[tuple[int, int]] = [
    (4096, 6),
    (6144, 28),
    (8192, 36),
]
```

**Mudanças:**
- Cap 4GB de 12 → 6.
- Comentário registra audit empírico de 2026-05-25 com link ao `proxy_stats.json`.

---

### `/home/andrefarias/Desenvolvimento/Nyx-Code/dev-journey/03-decisions/ADR_003_VRAM_MANAGEMENT.md`

Adicionar seção nova ao final (antes do epígrafe), titulada:

```markdown
## Revisão empírica 2026-05-25 (RTX 3050 4GB)

Auditoria pós-ONDA-30 detectou padrão de 23 OOMs consecutivos em 4 dias com
`num_gpu=12` cap original. Cap reduzido para 6 layers em RTX 3050 4GB.

| VRAM | Cap antigo | Cap novo | Justificativa |
|---|---|---|---|
| 4096 MiB | 12 | **6** | OOM crônico com Chrome + terminal + Spellbook (~600 MiB residual). 6 layers cabem com folga. |
| 6144 MiB | 28 | 28 | sem regressão reportada |
| 8192 MiB | 36 | 36 | sem regressão reportada |

Auditoria longitudinal: `cat ~/.nyx/proxy_stats.json` retorna `oom_recovery_count`.
Padrão para detectar regressão: `grep "OOM degradation step:" logs/proxy.log`.

Opt-in agressivo preserva paridade com hardware sem disputa: `.env`
`NYX_NUM_GPU=12` ou env shell. Auto-tune respeita override do usuário.
```

---

### `/home/andrefarias/Desenvolvimento/Nyx-Code/VALIDATOR_BRIEF.md`

Adicionar seção nova após "Defesa anti-sanitizer":

```markdown
## [CORE] Cap empírico de VRAM em RTX 3050 4GB

Auto-tune em `scripts/detect_gpu.py` aplica cap `4096 MiB → 6 layers` (não 12
como originalmente). Lição empírica de 2026-05-25: 23 OOMs consecutivos
durante 4 dias com `num_gpu=12` quando Chrome + terminal + Spellbook ocupam
~600 MiB residuais. Padrão sempre `12 → 6 → 0` via INFRA-OOM-RETRY-STEP-01.

Auditoria longitudinal:
```bash
cat ~/.nyx/proxy_stats.json   # oom_recovery_count cresce em recidiva
grep -c "OOM degradation step:" logs/proxy.log   # contagem de degradações
```

Validador deve aceitar override do usuário via `.env NYX_NUM_GPU=N` como opt-in
agressivo (paridade com hardware sem disputa).
```

---

## Diff esperado (resumo)

```
~ 3 arquivos modificados
- 0 arquivos removidos
+ ~25 linhas líquidas
```

---

## Comandos de verificação

```bash
# 1. Cap aplicado
./venv/bin/python -c "from scripts.detect_gpu import VRAM_CAP_MB_TO_LAYERS; print(VRAM_CAP_MB_TO_LAYERS)"
# Esperado: [(4096, 6), (6144, 28), (8192, 36)]

# 2. Auto-tune para qwen2.5-coder:3b
./venv/bin/python scripts/detect_gpu.py --for-model qwen2.5-coder:3b
# Esperado: <= 6 (com VRAM ~ 3.5 GiB livre)

# 3. Smoke
./run.sh --smoke
# Esperado: boot ok

# 4. Invariantes
bash scripts/sprint_invariants.sh
# Esperado: PASS 14/14, FAIL 0

# 5. Acentuação (BRIEF [CORE] check 4)
python3 ~/.config/zsh/scripts/validar-acentuacao.py --paths scripts/detect_gpu.py dev-journey/03-decisions/ADR_003_VRAM_MANAGEMENT.md VALIDATOR_BRIEF.md
# Esperado: rc=0

# 6. Snapshot de OOM ANTES da sprint
cat ~/.nyx/proxy_stats.json > /tmp/oom_pre.json

# 7. Após 3 boots (PASSO 2 da sprint), comparar:
for i in 1 2 3; do timeout 10 ./run.sh --smoke || true; done
cat ~/.nyx/proxy_stats.json > /tmp/oom_post.json
diff /tmp/oom_pre.json /tmp/oom_post.json
# Esperado: oom_recovery_count idêntico (nenhum incremento)
```

---

## Critério binário de aceite

- [ ] `VRAM_CAP_MB_TO_LAYERS` linha 62 alterado (4096 → 6).
- [ ] ADR-003 ganha seção "Revisão empírica 2026-05-25" com tabela.
- [ ] BRIEF ganha seção CORE "Cap empírico de VRAM em RTX 3050 4GB".
- [ ] `./run.sh --smoke` retorna `boot ok` exit 0.
- [ ] Invariantes 14/14 PASS.
- [ ] Acentuação rc=0 nos 3 arquivos.
- [ ] 3 boots seguidos não incrementam `oom_recovery_count` (validação empírica).
- [ ] Spec movida producao/ → concluidos/.
- [ ] MASTER atualizado entry 222 PENDENTE → CONCLUIDA.

---

## Proof-of-work (4 passos)

```bash
# PASSO 1 — snapshot ANTES
bash scripts/sprint_invariants.sh > /tmp/inv_before.txt 2>&1
FAIL_BEFORE=$(grep -c "^\[FAIL\]" /tmp/inv_before.txt)
cat ~/.nyx/proxy_stats.json > /tmp/oom_pre.json
echo "FAIL inicial: $FAIL_BEFORE"
echo "OOM pré: $(jq .oom_recovery_count /tmp/oom_pre.json)"

# PASSO 2 — implementação (Edit nos 3 arquivos)

# PASSO 3 — snapshot DEPOIS
bash scripts/sprint_invariants.sh > /tmp/inv_after.txt 2>&1
FAIL_AFTER=$(grep -c "^\[FAIL\]" /tmp/inv_after.txt)
for i in 1 2 3; do timeout 10 ./run.sh --smoke || true; done
cat ~/.nyx/proxy_stats.json > /tmp/oom_post.json
echo "FAIL final: $FAIL_AFTER"
echo "OOM pós: $(jq .oom_recovery_count /tmp/oom_post.json)"

# PASSO 4 — regras binárias
#   (a) FAIL_AFTER <= FAIL_BEFORE
#   (b) oom_recovery_count pós == oom_recovery_count pré
diff /tmp/inv_before.txt /tmp/inv_after.txt
diff /tmp/oom_pre.json /tmp/oom_post.json
```

---

## Riscos

| Risco | Mitigação |
|---|---|
| Cap 6 reduz throughput em máquinas sem disputa | Override via `.env NYX_NUM_GPU=12` preservado |
| Detect_gpu pode retornar < 6 em VRAM apertada | Cap é teto, não piso (já existia min via `apply_vram_cap`) |
| BRIEF crescer demais (atualmente 130L) | Seção é compacta (10-15 linhas) |
| ADR-003 historicamente sensível | Adição em seção dedicada não altera decisões anteriores |

---

*"Vale mais um cap conservador que cabe, do que um agressivo que cai." — princípio empírico*
