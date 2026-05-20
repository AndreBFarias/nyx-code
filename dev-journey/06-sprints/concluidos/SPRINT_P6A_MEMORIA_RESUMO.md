## 0. SPEC (machine-readable)

```yaml
sprint:
  id: P6-A
  title: "SessionMemory + AgentSummary"
  touches:
    - path: nyx/agent/services/memory.py
      reason: "Novo service: memória persistente de sessão"
    - path: nyx/agent/services/summary.py
      reason: "Novo service: resumo automático de ações"
    - path: scripts/gauntlet/nyx_gauntlet.py
      reason: "4 testes novos"
  origin:
    primary: "openclaud/src/services/SessionMemory/"
    secondary: "openclaud/src/services/AgentSummary/"
  tests:
    - cmd: "./run.sh --gauntlet --only p6_memoria"
      timeout: 30
  acceptance_criteria:
    - "SessionMemory persiste decisões-chave entre sessões"
    - "SessionMemory busca memórias por query"
    - "AgentSummary gera resumo de ações executadas"
    - "AgentSummary agrupa ações por tipo"
```

---

# Sprint P6-A -- Memória e Resumo

**Status:** CONCLUIDA (header corrigido em MASTER-CLEANUP-02 2026-05-20; presença em concluidos/ implica CONCLUIDA conforme convenção do projeto)
**Data:** 2026-04-05
**Prioridade:** MÉDIA
**Tipo:** Port (TS -> Python)
**Dependências:** P5-D
**Desbloqueia:** --

---

## Implementação

### SessionMemory (`nyx/agent/services/memory.py`)
- Persiste em `~/.nyx/memory/`
- Cada memória: `{key, content, tags, timestamp, session_id}`
- `save(key, content, tags)` -- salva memória
- `search(query, limit)` -- busca por conteúdo/tags
- `get_recent(n)` -- últimas N memórias
- `get_for_session(session_id)` -- memórias da sessão
- Formato JSON, um arquivo por sessão

### AgentSummary (`nyx/agent/services/summary.py`)
- Recebe histórico da sessão
- Agrupa por tipo de ação (read, write, edit, command, search)
- Gera resumo em PT-BR
- `summarize(session) -> str`
- `summarize_by_type(session) -> dict[str, list]`
- `get_key_actions(session) -> list[str]`

### Testes Gauntlet

| ID | Nome | Validação |
|----|------|-----------|
| P6M-01 | Memory save+search | Salva memória, busca por query, encontra |
| P6M-02 | Memory persistência | Salva, recarrega, verifica conteúdo |
| P6M-03 | Summary gera resumo | Resumo contém tipos de ação |
| P6M-04 | Summary agrupa por tipo | Dict tem chaves corretas |

## Verificação

- [ ] SessionMemory persiste em disco
- [ ] Busca retorna resultados relevantes
- [ ] AgentSummary funciona com sessão real
- [ ] 4 testes Gauntlet passando

---

*"A memória é o diário que todos carregam consigo." -- Oscar Wilde*
