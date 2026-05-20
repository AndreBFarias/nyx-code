## 0. SPEC

```yaml
sprint:
  id: DEBT-03
  title: "Logging padrão: todos módulos passam por InternalLogging via import"
  onda: 22
  bloco: 2
  prioridade: MÉDIA
  tipo: Refactor

  touches:
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/agent/services/logging_service.py
      reason: "Expor get_logger(name) que garante InternalLogging está inicializado"
    - path: "nyx/**/*.py (todos arquivos com logging.getLogger)"
      reason: "Substituir logging.getLogger() por nyx.agent.services.logging_service.get_logger()"

  forbidden:
    - "Remover InternalLogging (é infraestrutura central)"
    - "Duplicar configuração de logging em múltiplos arquivos"
    - "Quebrar o mecanismo de rotação de logs (arquivo rotacionado obrigatório)"

  tests:
    - cmd: "grep -rn 'logging.getLogger' nyx/ --include='*.py' | grep -v 'logging_service.py' | wc -l"
      esperado: "0 (todos migraram)"
    - cmd: "./run.sh --gauntlet --only rapido"
      deve_passar: true

  acceptance_criteria:
    - "logging_service.py exporta get_logger(name) que idempotentemente inicializa InternalLogging()"
    - "Todos módulos Python em nyx/ importam get_logger de logging_service"
    - "Zero uso direto de logging.getLogger em nyx/ fora de logging_service.py"
    - "Logs continuam rotacionados em ~/.nyx/logs/"
    - "Gauntlet rapido passa"
```

---

# Sprint DEBT-03 — Logging via logging_service padrão

**Status:** CONCLUIDA (header corrigido em MASTER-CLEANUP-02 2026-05-20; presença em concluidos/ implica CONCLUIDA conforme convenção do projeto)
**Data criação:** 2026-04-18

## Contexto

- GUIDE.md exige "Logging rotacionado obrigatório".
- `nyx/agent/services/logging_service.py` define `InternalLogging()` (chamado em `cli.py`).
- Outros módulos usam `logging.getLogger(...)` diretamente, confiando que `cli.py` já inicializou. Isso quebra quando o módulo é importado fora do REPL (ex.: script, teste, Gauntlet standalone).

## Problema

Inicialização de logging acoplada a quem importa primeiro. Scripts que não passam por `cli.py` podem ter logs sem rotação.

## Solução

1. **`logging_service.py`**: adicionar `get_logger(name: str) -> logging.Logger` que garante `InternalLogging()` foi chamado (idempotente).
2. **Substituir** `logger = logging.getLogger("nyx.xxx")` por `logger = get_logger("nyx.xxx")` em todos os ~30 arquivos.

## Arquivos alvo

### `nyx/agent/services/logging_service.py`

Adicionar no topo:

```python
_INITIALIZED = False


def get_logger(name: str) -> logging.Logger:
    """Retorna logger garantindo que InternalLogging foi inicializado."""
    global _INITIALIZED
    if not _INITIALIZED:
        InternalLogging()
        _INITIALIZED = True
    return logging.getLogger(name)
```

### Padrão de substituição em todos os módulos

**Antes:**
```python
import logging
logger = logging.getLogger("nyx.xxx")
```

**Depois:**
```python
from nyx.agent.services.logging_service import get_logger
logger = get_logger("nyx.xxx")
```

### Lista de arquivos com `logging.getLogger` (baseline em 2026-04-18)

Rodar primeiro para confirmar lista exata:

```bash
grep -rln "logging.getLogger" nyx/ --include='*.py' | sort
```

Esperado: ~30 arquivos incluindo `nyx/cli.py`, `nyx/proxy.py`, `nyx/themes/__init__.py`, `nyx/providers/ollama.py`, todos `nyx/agent/*.py`, `nyx/agent/tools/*.py`, `nyx/agent/services/*.py`.

### Exceções (não migrar)

- `nyx/agent/services/logging_service.py` — é a infra, não se importa
- `nyx/proxy.py` — roda como processo standalone via `nyx.proxy`; pode precisar manter `basicConfig` próprio (avaliar: se InternalLogging já gera rotação adequada para proxy também, migrar; senão, deixar com `# noqa: logging-migration` e documentar em comentário)

## Procedimento

1. Expandir `logging_service.py` com `get_logger`.
2. `grep -rln "logging.getLogger" nyx/ --include='*.py' | sort > /tmp/pending.txt`
3. Para cada arquivo na lista (exceto exceções): substituir as 2 linhas.
4. `grep -rn "logging.getLogger" nyx/` deve mostrar só `logging_service.py` + exceções documentadas.
5. Smoke test: `python -c 'from nyx.agent.services.logging_service import get_logger; import logging; l=get_logger("test"); l.info("oi")'`
6. `./run.sh` — abrir, enviar mensagem, verificar log em `~/.nyx/logs/`.
7. Ruff limpo.
8. Gauntlet.

## Diff esperado

```
~ nyx/agent/services/logging_service.py: +10 linhas
~ 30+ arquivos: 2 linhas cada (-1 import, +1 import; -1 getLogger, +1 get_logger)
Δ linhas líquidas ~= +10
```

## Comando de verificação

```bash
cd /home/andrefarias/Desenvolvimento/Nyx-Code

# 1. Nenhum getLogger direto fora do serviço e exceções
grep -rln "logging.getLogger" nyx/ --include='*.py' | grep -v 'logging_service.py' | grep -v 'proxy.py'
# esperado: vazio

# 2. get_logger é importado em ~30 arquivos
grep -rln "from nyx.agent.services.logging_service import get_logger" nyx/ --include='*.py' | wc -l
# esperado: >= 25

# 3. Smoke test de log
python -c "
from nyx.agent.services.logging_service import get_logger
l = get_logger('test')
l.info('hello from debt-03 sprint')
"
tail -5 ~/.nyx/logs/*.log 2>/dev/null

# 4. Gauntlet
./run.sh --gauntlet --only rapido
```

## Critério binário

- [ ] `get_logger` existe em `logging_service.py` e é idempotente
- [ ] `grep logging.getLogger nyx/` mostra só `logging_service.py` + exceções justificadas
- [ ] Log escreve em `~/.nyx/logs/` após o smoke test
- [ ] Gauntlet rapido passa
- [ ] Commit: `refactor: logging unificado via logging_service.get_logger (ADR-015)`

## Guardrails anti-engodo

**NÃO marque como concluída se:**
- Algum arquivo não-exceção ainda usa `logging.getLogger`.
- A IA só mudou 2-3 arquivos como "amostra".
- `~/.nyx/logs/` não tem saída após rodar o REPL.

## Validação humana

```bash
grep -rln "logging.getLogger" nyx/ --include='*.py'
# esperado: só logging_service.py (e proxy.py se ficou como exceção)

grep -rln "from nyx.agent.services.logging_service import get_logger" nyx/ | wc -l
# esperado: >= 25

ls -la ~/.nyx/logs/
# deve ter arquivos recentes
```

## Riscos

| Risco | Mitigação |
|-------|-----------|
| Import circular com logging_service | Service não importa de nada além de logging/stdlib |
| Proxy standalone perde rotação | Manter proxy.basicConfig; reavaliar em sprint futura |

---

*"Observar é metade de consertar." -- anônimo SRE*
