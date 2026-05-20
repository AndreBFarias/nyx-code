## 0. SPEC (machine-readable)

```yaml
sprint:
  id: P1-A
  title: "Core: Parser 7 níveis + Models atualizados"
  touches:
    - path: nyx/agent/parser.py
      reason: "Parser com 7 níveis de fallback (port da Luna)"
    - path: nyx/agent/models.py
      reason: "Adicionar ParseLevel, ParseResult, campos extras em AgentAction"
    - path: nyx/agent/session.py
      reason: "Adicionar métodos compress/compact que o context manager precisa"
  origin:
    primary: "Luna/src/skills/code_agent/parser.py (609 linhas)"
    reference: "openclaud/src/ (parse de respostas distribuído em vários arquivos)"
  forbidden:
    - "Remover funcionalidade existente do loop.py"
    - "Mocks de Ollama ou proxy"
  tests:
    - cmd: "python -c 'from nyx.agent.parser import ActionParser; p = ActionParser(); print(p.stats)'"
      timeout: 10
  acceptance_criteria:
    - "ActionParser com 7 níveis implementados"
    - "ParseLevel enum com EXACT, FUNCTION_CALL, RELAXED, BARE_TOOL, CODE_BLOCK, PATH_INTENT, IMPLICIT_DONE"
    - "ParseResult dataclass com action, level, success, error, raw_text"
    - "AgentAction com campo path e raw_block"
    - "Aliases PT-BR: ler, criar, editar, executar, buscar, pronto, concluído"
    - "Session com get_compressed_history(), get_full_history(), get_key_decisions()"
    - "Importa sem erro: from nyx.agent.parser import ActionParser"
    - "Acentuação PT-BR correta"
```

---

# Sprint P1-A -- Core: Parser + Models

**Status:** CONCLUIDA (header corrigido em MASTER-CLEANUP-02 2026-05-20; presença em concluidos/ implica CONCLUIDA conforme convenção do projeto)
**Data:** 2026-04-04
**Prioridade:** CRITICA
**Tipo:** Port (Luna -> Nyx)
**Dependências:** P-01 (agent loop básico)
**Desbloqueia:** P1-B, P1-C, P1-F

---

## O que portar

### 1. `nyx/agent/parser.py` (Luna: parser.py, 609 linhas)

Parser que extrai ações estruturadas da resposta do LLM. 7 níveis de fallback:

1. **EXACT:** blocos `ACTION: read_file` com separador `---`
2. **FUNCTION_CALL:** `read_file("path")` ou `read_file(path="value")`
3. **RELAXED:** regex relaxado (minúsculas, sem `---`)
4. **BARE_TOOL:** `read_file path/to/file` (sem parênteses)
5. **CODE_BLOCK:** extrai code blocks markdown como write_file
6. **PATH_INTENT:** "Vou ler o arquivo X" -> read_file
7. **IMPLICIT_DONE:** "pronto", "concluído" -> done

**Ajustes ao trazer da Luna:**
- Trocar `from src.core.logging_config import get_logger` -> `import logging; logger = logging.getLogger("nyx.parser")`
- Trocar `from .models import ActionType, AgentAction, ParseLevel, ParseResult` -> imports locais
- Luna tem `CREATE_FILE` e `WRITE_FILE` separados; Nyx tem só `WRITE_FILE` -- mapear ambos

### 2. `nyx/agent/models.py` (atualizar)

Adicionar ao existente:
- `ParseLevel` enum (7 níveis)
- `ParseResult` dataclass
- Campo `path` e `raw_block` em `AgentAction`
- `CREATE_FILE` como alias de `WRITE_FILE` no ActionType

### 3. `nyx/agent/session.py` (atualizar)

Adicionar métodos que o context_manager (P1-B) precisa:
- `get_compressed_history() -> str`
- `get_full_history() -> list[HistoryEntry]`
- `get_key_decisions() -> list[str]`
- `get_files_context() -> str`
- `compress()` e `ultra_compact()` em HistoryEntry

## Testes Gauntlet (novos, adicionados ao nyx_gauntlet.py)

Fase: `parser` (nova, 7 testes)

| ID | Nome | Validação |
|----|------|-----------|
| PR-01 | Parse EXACT | Envia "ACTION: read_file\nPATH: README.md\n---", verifica ActionType.READ_FILE |
| PR-02 | Parse FUNCTION_CALL | Envia "read_file('README.md')", verifica ActionType.READ_FILE |
| PR-03 | Parse RELAXED | Envia "action: read_file\npath: README.md", verifica extração |
| PR-04 | Parse BARE_TOOL | Envia "read_file README.md", verifica extração |
| PR-05 | Parse CODE_BLOCK | Envia "criar arquivo test.py:\n```python\nprint('ok')\n```", verifica WRITE_FILE |
| PR-06 | Parse PATH_INTENT | Envia "Vou ler o arquivo README.md", verifica READ_FILE |
| PR-07 | Parse IMPLICIT_DONE | Envia "Pronto, tarefa concluída", verifica DONE |

Implementação: cada teste chama `ActionParser().parse(texto)` e verifica `.success` e `.action.action_type`.

## Verificação

- [ ] `from nyx.agent.parser import ActionParser` importa sem erro
- [ ] `from nyx.agent.models import ParseLevel, ParseResult` importa
- [ ] 7 testes de parser passam no Gauntlet
- [ ] Parser retorna stats com contagem por nível
- [ ] Session tem get_compressed_history()
- [ ] `./run.sh --gauntlet --only parser` passa 100%
- [ ] Gauntlet completo continua passando 100%

---

*"Ouvir é mais difícil do que falar." -- Epicteto*
