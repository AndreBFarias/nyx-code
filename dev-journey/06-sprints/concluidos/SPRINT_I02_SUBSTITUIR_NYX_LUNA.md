## 0. SPEC (machine-readable)

```yaml
sprint:
  id: I-02
  title: "Substituir nyx antiga na Luna pelo Nyx-Code standalone"
  touches:
    - path: dev-journey/04-features/LUNA_INTEGRATION_MAP.md
      reason: "Mapa da superfície atual do code agent na Luna (fase auditoria)"
    - path: Luna/src/skills/code_agent/nyx_adapter.py
      reason: "Novo adapter que proxya para Nyx-Code headless"
    - path: Luna/src/skills/code_agent/commands.py
      reason: "Refatorar comando /nyx para usar nyx_adapter"
    - path: Luna/src/skills/code_agent/loop.py
      reason: "Substituir loop antigo por chamadas ao adapter"
    - path: Luna/src/skills/code_agent/hooks.py
      reason: "Ajustar hooks de entidade para o novo backend"
    - path: scripts/gauntlet/fases/i_luna.py
      reason: "Nova fase com 3 testes de integração"
    - path: scripts/gauntlet/nyx_gauntlet.py
      reason: "Registrar fase i_luna"
  n_to_n_pairs:
    - ["Luna/src/skills/code_agent/nyx_adapter.py", "nyx/cli.py (--headless)"]
  forbidden:
    - "Quebrar comandos existentes da Luna (API pública deve ser preservada)"
    - "Remover a nyx antiga antes de comprovar que o adapter funciona"
    - "Mexer em código da Luna fora de src/skills/code_agent/ e src/app/event_handlers.py"
  tests:
    - cmd: "./run.sh --gauntlet --only i_luna"
      timeout: 120
  acceptance_criteria:
    - "LUNA_INTEGRATION_MAP.md documenta 100% da API atual da nyx antiga"
    - "nyx_adapter inicia subprocess headless e responde ping em <2s"
    - "Comando /nyx na Luna dispara Nyx-Code novo (não a antiga)"
    - "Graceful stop não deixa processo zombie"
    - "Zero regressão em testes existentes da Luna"
    - "Acentuação PT-BR correta"
```

> Executar antes de começar: PORT-01, PORT-02, PORT-03 devem estar CONCLUIDAS. Nyx-Code precisa ser portável antes de virar dependência de outro projeto.

---

# Sprint I-02 -- Substituir nyx antiga na Luna pelo Nyx-Code standalone

**Status:** DELEGADA (2026-04-16) -- transferida para o repo Luna
**Delegada para:** `Luna/dev-journey/06-sprints/producao/infra/SPRINT_INFRA50_NYX_BOOTSTRAP.md`, `SPRINT_INFRA51_NYX_ADAPTER.md`, `SPRINT_INFRA52_CODE_AGENT_REFACTOR.md`
**Motivo:** a implementação toca arquivos em `Luna/src/skills/code_agent/`. Sprints no repo correto com código pronto pra copiar. Este Nyx-Code oferece o protocolo headless (I-01 concluida) e nao precisa de mudanca.
**Data:** 2026-04-16
**Prioridade:** ALTA
**Tipo:** Integração
**Dependências:** I-01 (headless pronto), PORT-01, PORT-02, PORT-03
**Desbloqueia:** I-03

---

## Problema / Contexto

A Luna já tem uma "nyx" interna como code agent em `Luna/src/skills/code_agent/`. Essa implementação antiga foi um experimento antes do Nyx-Code standalone existir. Agora que o Nyx-Code está maduro (34 tools, 47 commands, 10 services, protocolo headless I-01 pronto), o objetivo é substituir a antiga pela nova sem quebrar a interface que a Luna expõe ao usuário.

A substituição tem duas fases: **auditoria** (mapear o que existe hoje) e **port** (trocar o backend por trás de uma API estável).

## Implementação

### Fase 1: Auditoria (sem mudar código)

Entrar no repo da Luna (caminho exato depende da configuração do dev) e ler:

- `Luna/src/skills/code_agent/commands.py` — quais comandos registra, qual a assinatura
- `Luna/src/skills/code_agent/loop.py` — como processa entrada, qual o ciclo
- `Luna/src/skills/code_agent/hooks.py` — quais eventos escuta e publica
- `Luna/src/app/event_handlers.py` — onde as mensagens da nyx antiga aparecem na TUI
- Outros arquivos em `code_agent/` que existirem (services, helpers, etc.)

Produzir `dev-journey/04-features/LUNA_INTEGRATION_MAP.md` no repo do Nyx-Code, contendo:

1. Lista de comandos públicos (`/nyx`, `/nyx off`, `/nyx status`, ...)
2. Assinatura de cada função exportada pelo módulo `code_agent`
3. Eventos publicados no event bus da Luna (ex.: `code_agent.response`, `code_agent.error`)
4. Formato de mensagens na TUI (prefixos, cores, estilos)
5. Estado compartilhado (arquivos de sessão, locks, etc.)
6. Classificação por módulo: **preservar** / **refatorar** / **remover**

**Checkpoint:** não avançar para Fase 2 sem apresentar o MAP e alinhar com o usuário quais módulos ficam.

### Fase 2: Implementar `nyx_adapter.py`

```python
# Luna/src/skills/code_agent/nyx_adapter.py
"""Adapter: expõe a superfície antiga da nyx, mas roda Nyx-Code via subprocess."""
from __future__ import annotations

import asyncio
import json
import logging
import shutil
import subprocess
from pathlib import Path
from typing import Any

logger = logging.getLogger("luna.nyx_adapter")

class NyxAdapter:
    def __init__(self, nyx_root: Path, timeout: float = 120.0):
        self.nyx_root = nyx_root
        self.timeout = timeout
        self.proc: subprocess.Popen | None = None

    async def start(self) -> None: ...
    async def stop(self) -> None: ...
    async def ping(self) -> bool: ...
    async def request(self, prompt: str, context: dict[str, Any]) -> dict: ...
    async def tools(self) -> list[str]: ...
```

Responsabilidades:

- **Lifecycle:** start/stop do subprocess `python -m nyx.cli --headless` (usa venv do Nyx-Code)
- **Protocolo:** JSON stdin/stdout (já implementado em I-01: ping, status, tools, session, request, reset, erro)
- **Timeout:** default 120s por request, configurável
- **Health check:** ping no start para validar subida (<2s)
- **Restart:** se subprocess morrer entre requests, reinicia automaticamente
- **Cleanup:** stop garante que não fica processo zombie (SIGTERM → aguarda 3s → SIGKILL)

### Fase 3: Refatorar commands.py e loop.py

Trocar chamadas internas à implementação antiga por chamadas ao adapter. A API pública (comandos `/nyx`, `/nyx status`, etc.) permanece idêntica — só o backend muda.

Exemplo:
```python
# antes
from .old_nyx_core import process_request
response = process_request(prompt, ctx)

# depois
from .nyx_adapter import NyxAdapter
adapter = get_or_create_adapter()
response = await adapter.request(prompt, ctx)
```

### Fase 4: Hooks de entidade

Quando `/nyx` ativo, a TUI da Luna precisa mostrar "Nyx" como entidade (paleta cyan/teal #00D4AA). Isso já existe na Luna para outras entidades (kernel, augur). Apenas garantir que o hook `on_entity_switch` reconhece "nyx" e usa a paleta correta.

### Fase 5: Limpeza

Após validar que o adapter funciona, remover módulos da nyx antiga que ficaram sem uso. Manter apenas o que o MAP marcou como **preservar**. Zero código comentado — deletar de vez (ADR anti-burla).

### Fase 6: Testes Gauntlet (fase `i_luna`)

| ID | Nome | Validação |
|----|------|-----------|
| I2-01 | Import e init | `from luna.skills.code_agent.nyx_adapter import NyxAdapter` + `NyxAdapter(nyx_root).start()` não levanta |
| I2-02 | Ping <2s | `adapter.start()` + `adapter.ping()` em menos de 2000ms |
| I2-03 | Graceful stop | `adapter.stop()` deixa `ps -ef \| grep nyx.cli` limpo (zero zombies) |

Testes executam contra um Nyx-Code local instalado. Se Luna não estiver disponível no ambiente do Gauntlet, esses testes ficam pulados com mensagem clara (não falha).

## Verificação

- [ ] `LUNA_INTEGRATION_MAP.md` criado e revisado com usuário
- [ ] `nyx_adapter.py` implementado
- [ ] `commands.py` e `loop.py` usando adapter
- [ ] `/nyx` na Luna dispara subprocess do Nyx-Code novo
- [ ] Testes existentes da Luna continuam passando
- [ ] Módulos mortos da nyx antiga removidos
- [ ] Gauntlet fase `i_luna` passa 3/3

## Riscos

1. **Tamanho real da API da Luna antiga:** só a Fase 1 vai revelar. Se for grande, dividir em sub-sprints.
2. **Sincronização de sessão:** Luna gerencia sessão própria; Nyx-Code também. Decidir na Fase 2 quem é a fonte da verdade (provavelmente Luna, e o adapter serializa/desserializa).
3. **Latência do subprocess:** 2s para ping pode ser otimista em primeira chamada (carregamento de modelo). Se necessário, ajustar timeout para 10s no primeiro ping apenas.

---

*"Não se rebenta o ovo pelo lado errado." -- Jonathan Swift*
