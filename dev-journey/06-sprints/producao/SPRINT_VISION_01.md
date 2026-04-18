## 0. SPEC

```yaml
sprint:
  id: VISION-01
  title: "Provider moondream + VisionService + ADR-022 + barra de progresso para operações longas"
  onda: 22
  bloco: 6
  prioridade: ALTA
  tipo: Feature
  dependencias: [UX-BUG-03]
  desbloqueia: [VISION-02]

  creates:
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/dev-journey/03-decisions/ADR_022_MOONDREAM.md
      reason: "Decisão de visão: moondream CPU, cache local, fallback claro"
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/providers/vision_client.py
      reason: "Cliente HTTP para POST Ollama /api/generate com images + num_gpu=0"
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/agent/services/vision_service.py
      reason: "Fachada VisionService.describe() com cache por sha256 e fallback"

  touches:
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/agent/output.py
      reason: "Adiciona render_progress_bar(label, current, total) para operações longas"

  absorve:
    - "O-01 (barra de progresso para operações longas)"

  forbidden:
    - "Subir moondream na GPU (precisa num_gpu=0 explícito)"
    - "Fazer vision_service bloquear o event loop principal"
    - "Crashar se moondream não estiver instalado — deve dar erro claro"

  tests:
    - cmd: "python -c 'from nyx.agent.services.vision_service import VisionService; v=VisionService(); print(v.is_available())'"
      deve_passar: true
    - cmd: "./run.sh --gauntlet --only vision"
      deve_passar: true
      nota: "Cria nova fase no Gauntlet; teste básico com assets/nyx-icon.png"

  acceptance_criteria:
    - "ADR-022 criado (Status ACEITO)"
    - "vision_client.py existe e aceita image_path: Path"
    - "VisionService.describe(path) retorna str não vazia quando moondream instalado"
    - "VisionService.is_available() retorna False e não crasha quando moondream ausente"
    - "Cache em ~/.nyx/vision_cache/<sha256>.txt funciona (2ª chamada é cache-hit)"
    - "render_progress_bar(label, current, total) existe em output.py"
    - "Gauntlet vision passa quando moondream instalado; pula quando ausente (skip, não fail)"
```

---

# Sprint VISION-01 — Provider moondream + Service + ADR-022

## Contexto

- Decisão D1 (usuário): visão via moondream CPU (qwen3:4b é texto-only).
- Absorve O-01: operações longas (download de modelo, inferência lenta) precisam de feedback visual.
- ADR-001 Local First: nada de API cloud. Ollama porta 11435.

## Solução

### ADR-022 (NOVO)

**Path:** `dev-journey/03-decisions/ADR_022_MOONDREAM.md`

```markdown
# ADR-022 — Visão via moondream em CPU puro

**Status:** ACEITO
**Data:** 2026-04-18
**Contexto da Onda:** 22, Bloco 6, VISION-01

## Contexto

qwen3:4b é modelo text-only. A Onda 22 adiciona capacidade de visão.
A referência da Luna usa moondream (1.8B) com swap de VRAM.

Na máquina alvo (RTX 3050 4GB), qwen3:4b consome ~3.2GB de VRAM.
moondream consome ~1.7GB. Rodar ambos simultâneos na GPU: estoura.

Alternativas:
- (a) moondream em CPU puro (num_gpu=0): latência 2-8s por imagem,
  qwen3 não é descarregado. Overhead é aceitável para descrição de
  imagens (não é caminho quente de chat).
- (b) swap VRAM (Luna-style): descarrega qwen3, sobe moondream,
  processa, volta. Complexidade alta, quebra streaming.
- (c) qwen2.5-vl:3b no lugar de qwen3:4b: perde qualidade de texto.

## Decisão

Moondream em CPU puro. Invocação via Ollama `/api/generate` com
`options: {"num_gpu": 0, "num_ctx": 2048}`.

## Consequências

- Positiva: qwen3 permanece quente; latência de chat não é afetada.
- Positiva: simples — sem orquestração de VRAM.
- Negativa: descrição de imagem leva 2-8s (CPU). Aceitável.
- Futuro: quando hardware permitir, criar `vram_swap_service.py`
  para pipeline (b).

## Referências

- AUDIT-EXT-01 finding O-01 (progress bar).
- ADR-001 Local First, ADR-003 VRAM Management.

*"Lento no lugar certo é mais rápido que rápido no lugar errado." -- anônimo*
```

### `nyx/providers/vision_client.py` (NOVO)

```python
"""VisionClient -- wrapper HTTP para Ollama /api/generate com imagem.

Usa moondream em CPU (num_gpu=0). Não compete com qwen3 por VRAM.
"""

from __future__ import annotations

import base64
import logging
from pathlib import Path

import httpx

from nyx.agent.services.logging_service import get_logger
from nyx.config.defaults import OLLAMA_URL

logger = get_logger("nyx.providers.vision")

VISION_MODEL = "moondream"
REQUEST_TIMEOUT = 60
NUM_CTX_VISION = 2048


class VisionClient:
    def __init__(self, ollama_url: str = OLLAMA_URL, timeout: int = REQUEST_TIMEOUT) -> None:
        self._url = ollama_url.rstrip("/")
        self._timeout = timeout

    def describe_image(self, image_path: Path, prompt: str = "Describe this image in detail.") -> str:
        """Chama moondream com imagem base64. CPU only (num_gpu=0)."""
        if not image_path.is_file():
            raise FileNotFoundError(f"Imagem não encontrada: {image_path}")

        b64 = base64.b64encode(image_path.read_bytes()).decode("ascii")
        payload = {
            "model": VISION_MODEL,
            "prompt": prompt,
            "images": [b64],
            "stream": False,
            "options": {
                "num_gpu": 0,
                "num_ctx": NUM_CTX_VISION,
            },
        }
        try:
            with httpx.Client(timeout=self._timeout) as client:
                r = client.post(f"{self._url}/api/generate", json=payload)
                r.raise_for_status()
                data = r.json()
                return (data.get("response") or "").strip()
        except httpx.HTTPError as e:
            logger.warning("vision: falha HTTP (%s)", e)
            raise
        except (KeyError, ValueError) as e:
            logger.warning("vision: resposta inesperada (%s)", e)
            raise

    def is_model_available(self) -> bool:
        """Consulta /api/tags e verifica se moondream está puxado."""
        try:
            with httpx.Client(timeout=5) as client:
                r = client.get(f"{self._url}/api/tags")
                if r.status_code != 200:
                    return False
                tags = r.json().get("models", [])
                return any(VISION_MODEL in (m.get("name") or "") for m in tags)
        except httpx.HTTPError:
            return False


# "Ver é um ato de escolha." -- John Berger
```

### `nyx/agent/services/vision_service.py` (NOVO)

```python
"""VisionService -- fachada de descrição de imagens com cache.

Cache: ~/.nyx/vision_cache/<sha256>.txt
Fallback claro se moondream ausente.
"""

from __future__ import annotations

import hashlib
from pathlib import Path

from nyx.agent.services.logging_service import get_logger
from nyx.providers.vision_client import VisionClient

logger = get_logger("nyx.services.vision")

CACHE_DIR = Path.home() / ".nyx" / "vision_cache"


class VisionService:
    def __init__(self, client: VisionClient | None = None) -> None:
        self._client = client or VisionClient()
        CACHE_DIR.mkdir(parents=True, exist_ok=True)

    def is_available(self) -> bool:
        return self._client.is_model_available()

    def describe(self, image_path: Path, prompt: str = "Describe this image in detail.") -> str:
        """Retorna descrição. Usa cache por sha256 do arquivo + prompt.

        Se moondream não disponível, retorna string-sentinela
        '[Imagem: visão indisponível — rode `./install.sh --vision`]'.
        """
        if not image_path.is_file():
            return f"[Imagem: arquivo não encontrado ({image_path})]"

        digest = self._digest(image_path, prompt)
        cache_file = CACHE_DIR / f"{digest}.txt"
        if cache_file.exists():
            logger.debug("vision cache hit: %s", digest[:8])
            return cache_file.read_text(encoding="utf-8")

        if not self.is_available():
            return "[Imagem: visão indisponível — rode `./install.sh --vision`]"

        try:
            desc = self._client.describe_image(image_path, prompt).strip()
            if desc:
                cache_file.write_text(desc, encoding="utf-8")
            return desc or "[Imagem: descrição vazia]"
        except Exception as e:
            logger.warning("vision: descrição falhou (%s)", e)
            return f"[Imagem: erro ao descrever ({type(e).__name__})]"

    @staticmethod
    def _digest(path: Path, prompt: str) -> str:
        h = hashlib.sha256()
        h.update(path.read_bytes())
        h.update(b"||")
        h.update(prompt.encode("utf-8"))
        return h.hexdigest()


# "A paciência vê o que a pressa não alcança." -- anônimo fotógrafo
```

### `nyx/agent/output.py` — progress bar

```python
def render_progress_bar(label: str, current: int, total: int, width: int = 30) -> None:
    """Imprime barra de progresso discreta: '[===>    ] 42% label'.

    Idempotente no mesmo line (\\r no início); chamar render_progress_end()
    quando terminar para pular linha.
    """
    from nyx.themes.design_tokens import ANSI_ACCENT_FG, ANSI_MUTED_FG, ANSI_RESET
    if total <= 0:
        pct = 0.0
    else:
        pct = min(current / total, 1.0)
    filled = int(pct * width)
    bar = "█" * filled + "░" * (width - filled)
    sys.stdout.write(f"\r  {ANSI_ACCENT_FG}{bar}{ANSI_RESET} {int(pct*100):3d}% {ANSI_MUTED_FG}{label}{ANSI_RESET}")
    sys.stdout.flush()

def render_progress_end() -> None:
    sys.stdout.write("\n")
    sys.stdout.flush()
```

### Gauntlet: nova fase `vision`

Adicionar (arquivo do Gauntlet, geralmente `scripts/gauntlet/run.py` ou similar): uma fase `vision` com 1 teste inicial — descrever `assets/nyx-icon.png` e verificar que string não vazia + keyword esperada.

**A IA executora deve inspecionar a estrutura do Gauntlet** (`scripts/gauntlet/`) e seguir padrão existente. Fase DEVE pular gracefully quando moondream ausente (marca como "skip" não como "fail").

## Comando de verificação

```bash
cd /home/andrefarias/Desenvolvimento/Nyx-Code

# 1. Arquivos existem
test -s dev-journey/03-decisions/ADR_022_MOONDREAM.md
test -s nyx/providers/vision_client.py
test -s nyx/agent/services/vision_service.py

# 2. Import smoke
python -c "
from nyx.providers.vision_client import VisionClient
from nyx.agent.services.vision_service import VisionService
from nyx.agent.output import render_progress_bar, render_progress_end
v = VisionService()
print('is_available:', v.is_available())
"

# 3. Se moondream instalado: describe funciona
python -c "
from pathlib import Path
from nyx.agent.services.vision_service import VisionService
v = VisionService()
if v.is_available():
    desc = v.describe(Path('assets/nyx-icon.png'))
    assert len(desc) > 20, f'descricao muito curta: {desc}'
    print('describe OK:', desc[:80])
else:
    print('moondream ausente — skip')
"

# 4. Cache funciona: 2ª chamada é instantânea
python -c "
from pathlib import Path
from nyx.agent.services.vision_service import VisionService
import time
v = VisionService()
if v.is_available():
    t1 = time.monotonic(); _ = v.describe(Path('assets/nyx-icon.png')); dt1 = time.monotonic() - t1
    t2 = time.monotonic(); _ = v.describe(Path('assets/nyx-icon.png')); dt2 = time.monotonic() - t2
    assert dt2 < dt1 * 0.3, f'cache não efetivo: {dt1}s -> {dt2}s'
    print(f'cache OK: {dt1:.2f}s -> {dt2:.2f}s')
"

./run.sh --gauntlet --only vision
```

## Critério binário

- [ ] ADR-022 criado (ACEITO)
- [ ] `vision_client.py` e `vision_service.py` criados
- [ ] `is_available()` não crasha quando moondream ausente
- [ ] `describe()` retorna string não vazia quando disponível
- [ ] Cache funciona (sha256 + prompt)
- [ ] `render_progress_bar` existe
- [ ] Fase `vision` no Gauntlet criada
- [ ] Commit: `feat: visao moondream CPU + VisionService + progress bar (ADR-022)`

## Guardrails anti-engodo

**NÃO marque como concluída se:**
- IA esqueceu `options: {"num_gpu": 0}` — quebra ADR-022.
- Cache nunca grava no disco.
- `is_available()` retorna True mesmo sem moondream.
- Gauntlet `vision` fail-hard em máquina sem moondream (deve skip).

## Validação humana

```bash
# Pré-requisito: moondream instalado
ollama pull moondream

python -c "
from pathlib import Path
from nyx.agent.services.vision_service import VisionService
v = VisionService()
print(v.describe(Path('assets/nyx-icon.png')))
"

ls ~/.nyx/vision_cache/   # deve ter um arquivo .txt
```

## Riscos

| Risco | Mitigação |
|-------|-----------|
| moondream lento > 30s em CPU fraca | Timeout em 60s; cache evita refazer |
| Cache cresce indefinido | Adicionar rotação em sprint futura (dívida) |

---

*"Ver é descrever em silêncio, até que as palavras cheguem." -- anônimo*
