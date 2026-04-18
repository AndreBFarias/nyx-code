## 0. SPEC

```yaml
sprint:
  id: VISION-03
  title: "Garantir moondream em CPU puro sem descarregar qwen3 (num_gpu=0 forçado + teste)"
  onda: 22
  bloco: 6
  prioridade: ALTA
  tipo: Bugfix + Verify
  dependencias: [VISION-02]
  desbloqueia: [DEPLOY-01]

  touches:
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/providers/vision_client.py
      reason: "Reforçar options: num_gpu=0, num_ctx=2048 em todas requests (VISION-01 já colocou; esta sprint confirma)"
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/agent/services/vision_service.py
      reason: "Log 'moondream rodando em CPU' na primeira invocação"

  creates:
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/scripts/verify_vram.sh
      reason: "Script que roda nvidia-smi antes/depois da inferência vision e confere que qwen3 não foi descarregado"

  forbidden:
    - "Mudar num_gpu para > 0 (quebra ADR-022)"
    - "Assumir que usuário tem GPU — funcionar sem nvidia-smi"

  tests:
    - cmd: "bash scripts/verify_vram.sh"
      esperado: "VRAM qwen3 estável antes/depois (delta <= 200MB)"
    - cmd: "./run.sh --gauntlet --only vision"
      deve_passar: true

  acceptance_criteria:
    - "vision_client emite options: {num_gpu: 0, num_ctx: 2048}"
    - "Log 'moondream em CPU (num_gpu=0)' registrado na primeira chamada"
    - "Script verify_vram.sh existe, pula gracefully se sem nvidia-smi"
    - "Em máquina com GPU: teste passa (qwen3 VRAM estável)"
    - "Fallback timeout: se moondream > 30s, cancela e retorna '[Imagem: timeout]'"
    - "Gauntlet vision passa"
```

---

# Sprint VISION-03 — VRAM estável

## Contexto

- VISION-01 já colocou `num_gpu: 0` no payload.
- Esta sprint **verifica** que a decisão tem efeito real: qwen3 permanece quente durante chamada de visão.

## Problema

Ollama pode ignorar `num_gpu` em certos builds ou quando VRAM sobra. Precisamos garantir empiricamente.

## Solução

### `scripts/verify_vram.sh` (NOVO)

```bash
#!/usr/bin/env bash
# Confere que chamada de vision_service.describe NÃO descarrega qwen3.
# Pula gracefully se nvidia-smi ausente.

set -u

if ! command -v nvidia-smi &>/dev/null; then
    echo "[skip] nvidia-smi não encontrado — teste pulado"
    exit 0
fi

mem_qwen() {
    # Retorna MB alocados por processo de qwen3 no Ollama (aprox via memory.used)
    nvidia-smi --query-gpu=memory.used --format=csv,noheader,nounits | head -1
}

BEFORE=$(mem_qwen)
echo "[verify_vram] VRAM antes: ${BEFORE} MB"

python - <<'PY'
from pathlib import Path
from nyx.agent.services.vision_service import VisionService
v = VisionService()
if not v.is_available():
    print("[skip] moondream não instalado")
    exit(0)
p = Path("assets/nyx-icon.png")
if not p.exists():
    print("[skip] assets/nyx-icon.png ausente")
    exit(0)
desc = v.describe(p)
print(f"[vision] descricao OK ({len(desc)} chars)")
PY

AFTER=$(mem_qwen)
echo "[verify_vram] VRAM depois: ${AFTER} MB"

DELTA=$((AFTER - BEFORE))
ABS_DELTA=${DELTA#-}
if [ $ABS_DELTA -gt 200 ]; then
    echo "[FAIL] VRAM variou ${DELTA} MB (esperado <= 200 MB)"
    exit 1
fi
echo "[OK] VRAM estável (delta ${DELTA} MB)"
```

Dar executável: `chmod +x scripts/verify_vram.sh`.

### `vision_service.py` — log primeira chamada

```python
class VisionService:
    def __init__(self, client: VisionClient | None = None) -> None:
        self._client = client or VisionClient()
        self._logged_cpu = False
        CACHE_DIR.mkdir(parents=True, exist_ok=True)

    def describe(self, image_path: Path, prompt: str = "...") -> str:
        if not self._logged_cpu:
            logger.info("moondream em CPU puro (num_gpu=0) — ver ADR-022")
            self._logged_cpu = True
        # ... resto ...
```

### `vision_client.py` — timeout robusto

Confirmar que REQUEST_TIMEOUT = 60s cobre margem. Em caso de timeout, retornar sentinela:

```python
def describe_image(self, image_path: Path, prompt: str) -> str:
    ...
    try:
        with httpx.Client(timeout=self._timeout) as client:
            r = client.post(...)
            ...
    except httpx.TimeoutException:
        logger.warning("vision: timeout após %ds — provavelmente CPU sobrecarregada", self._timeout)
        raise TimeoutError("moondream não respondeu a tempo")
```

E em `VisionService.describe`, tratar `TimeoutError`:

```python
except TimeoutError:
    return "[Imagem: timeout — descrição demorou demais]"
```

## Comando de verificação

```bash
cd /home/andrefarias/Desenvolvimento/Nyx-Code

# 1. Script executável
test -x scripts/verify_vram.sh && echo "script OK"

# 2. num_gpu=0 presente
grep -A3 "options" nyx/providers/vision_client.py | grep "num_gpu"

# 3. Log na primeira chamada
grep -c "CPU puro\|num_gpu=0" nyx/agent/services/vision_service.py
# esperado: >= 1

# 4. Timeout handler
grep "TimeoutError\|timeout" nyx/providers/vision_client.py nyx/agent/services/vision_service.py

# 5. Execução real (se GPU disponível)
bash scripts/verify_vram.sh

./run.sh --gauntlet --only vision
```

## Critério binário

- [ ] Script `verify_vram.sh` criado, executável e funcional
- [ ] `num_gpu=0` no payload
- [ ] Log "moondream em CPU" emitido na primeira chamada
- [ ] Timeout retorna sentinela "[Imagem: timeout]"
- [ ] Em máquina sem GPU: script pula com exit 0
- [ ] Em máquina com GPU: delta VRAM <= 200 MB
- [ ] Gauntlet vision passa
- [ ] Commit: `fix: verifica moondream em CPU puro (num_gpu=0) + timeout amigavel`

## Guardrails anti-engodo

**NÃO marque como concluída se:**
- IA adicionou options mas pôs `num_gpu: 1` por engano.
- Timeout handler nunca aciona (test: `self._timeout = 1` temporário no repro).
- Script sempre retorna "OK" sem medir de verdade.

## Validação humana

```bash
# Com GPU
nvidia-smi --query-gpu=memory.used --format=csv,noheader,nounits
# rodar bash scripts/verify_vram.sh
# rodar Nyx, colar imagem, pedir descrição
# VRAM depois: praticamente igual (qwen3 continua na GPU)

# Sem GPU (VM)
bash scripts/verify_vram.sh
# imprime "[skip] nvidia-smi não encontrado"
```

## Riscos

| Risco | Mitigação |
|-------|-----------|
| Ollama ignora num_gpu em certos builds | Script de verify pega isso empiricamente |
| CPU fraca deixa moondream > 30s | Timeout com sentinela; usuário vê explicação |

---

*"Confiar sem medir é um luxo que a engenharia não tem." -- anônimo SRE*
