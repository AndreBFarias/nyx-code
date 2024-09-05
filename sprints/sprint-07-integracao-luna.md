# Sprint 4: Integracao Luna

**Objetivo:** Nyx-Code funcionando como backend do code agent da Luna,
com comando `/nyx`, mensagens inline e troca de modelo automatica.

---

## 4.1 Protocolo de comunicacao

| # | Arquivo | Descricao |
|---|---------|-----------|
| 1 | `nyx/integration/protocol.py` | Protocolo JSON via stdin/stdout |
| 2 | `nyx/integration/messages.py` | Formato de mensagens para TUI Luna |
| 3 | `nyx/integration/hooks.py` | Hooks de eventos (start, action, done) |

### Modo headless

`./run.sh --headless`

- Nyx-Code roda sem interface propria
- Input: JSON no stdin (request, config)
- Output: JSON no stdout (actions, responses, status)
- Luna consome como subprocess

### Formato de mensagem (stdin -> Nyx)

```json
{
  "type": "request",
  "content": "crie um arquivo hello.py",
  "config": {
    "model": "3b",
    "auto_confirm": false,
    "max_iterations": 50
  }
}
```

### Formato de resposta (Nyx -> stdout)

```json
{
  "type": "action",
  "action": "create_file",
  "params": {
    "path": "hello.py",
    "content": "print('Hello')"
  },
  "status": "pending_confirmation"
}
```

```json
{
  "type": "done",
  "summary": {
    "actions": 5,
    "files_edited": 2,
    "time_seconds": 12.3
  }
}
```

---

## 4.2 Correcoes no code agent da Luna

| # | Correcao | Local Luna |
|---|----------|------------|
| 1 | Registrar comando `/nyx` | `src/skills/code_agent/commands.py` |
| 2 | Troca de entidade para Nyx ao entrar em /code | `src/skills/code_agent/hooks.py` |
| 3 | Substituir code_agent legado por Nyx-Code | `src/skills/code_agent/loop.py` |
| 4 | Mensagens inline na TUI (estilo kernel) | `src/app/event_handlers.py` |
| 5 | VRAM switch para qwen-coder | `src/skills/code_agent/vram_switch.py` |

### Detalhes das correcoes

**Comando /nyx:**
Atualmente `/nyx` retorna "Comando desconhecido". Registrar no command_registry
para iniciar o Nyx-Code em modo headless.

**Troca de entidade:**
Ao ativar `/code` ou `/nyx`, a entidade deve mudar para Nyx automaticamente.
Mensagens na TUI devem usar o nome "Nyx" em vez de "Luna".

**Mensagens inline:**
As respostas do Nyx-Code devem aparecer no chat da TUI como mensagens
prefixadas com `[nyx]`, similar ao `[kernel]` ou `[augur]`.

---

## 4.3 Configuracao GOD MODE

Adicionar em `src/core/config/`:

```python
# Nyx-Code (agente de codigo externo)
NYX_CODE_PATH = ""           # Caminho para projeto Nyx-Code
NYX_CODE_MODEL = "3b"        # Modelo padrao (3b/7b)
NYX_CODE_PORT = 11435        # Porta do Ollama dedicado
NYX_CODE_HEADLESS = True     # Modo headless para integracao
NYX_CODE_VRAM_MAX = 2.5      # GB max de VRAM
```

Adicionar em `.env.example` da Luna:

```env
NYX_CODE_PATH=../Nyx-Code
NYX_CODE_MODEL=3b
NYX_CODE_PORT=11435
```

---

## 4.4 DI Container

Registrar NyxCodeService no container Luna:

```python
# src/core/di/providers.py
class NyxCodeService:
    """Gerencia lifecycle do Nyx-Code como subprocess."""

    def start(self, model: str = "3b") -> None: ...
    def stop(self) -> None: ...
    def send_request(self, content: str) -> dict: ...
    def is_running(self) -> bool: ...
```

- Factory que inicializa subprocess do Nyx-Code (`./run.sh --headless`)
- Gerenciamento de lifecycle (start/stop)
- Interface com protocolo JSON via stdin/stdout
- Timeout e error handling

---

## Verificacao

- [ ] `/nyx` funciona na Luna CLI
- [ ] `/code` usa Nyx-Code como backend
- [ ] Entidade troca para Nyx ao ativar code agent
- [ ] Mensagens aparecem inline na TUI (como `[kernel]`)
- [ ] Troca de modelo automatica (VRAM switch)
- [ ] `./run.sh --headless` funciona standalone
- [ ] Nyx-Code standalone continua independente
- [ ] VRAM dentro dos limites (2.5GB max)
- [ ] Protocolo JSON testado com requests de exemplo
- [ ] Cleanup correto ao fechar Luna (para Nyx-Code subprocess)
