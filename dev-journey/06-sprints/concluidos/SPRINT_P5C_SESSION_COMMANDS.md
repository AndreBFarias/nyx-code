## 0. SPEC (machine-readable)

```yaml
sprint:
  id: P5-C
  title: "Sessão & Métricas -- /resume, /export, /copy, /summary, /stats, /usage"
  touches:
    - path: nyx/agent/commands.py
      reason: "6 novos commands de sessão e métricas"
    - path: scripts/gauntlet/nyx_gauntlet.py
      reason: "6 testes novos"
  origin:
    primary: "openclaud/src/commands/resume/"
    secondary: "openclaud/src/commands/stats/"
  tests:
    - cmd: "./run.sh --gauntlet --only p5_session"
      timeout: 30
  acceptance_criteria:
    - "/resume restaura sessão anterior"
    - "/export salva conversa em arquivo"
    - "/copy copia último output para clipboard"
    - "/summary gera resumo da sessão"
    - "/stats mostra estatísticas detalhadas"
    - "/usage mostra uso de tokens/contexto"
```

---

# Sprint P5-C -- Sessão & Métricas

**Status:** PENDENTE
**Data:** 2026-04-05
**Prioridade:** MÉDIA
**Tipo:** Port (TS -> Python)
**Dependências:** P5-A
**Desbloqueia:** --

---

## Implementação

### /resume
- `/resume` -- restaura última sessão salva (atalho para `/session load`)
- Mostra resumo do que foi restaurado

### /export
- `/export` -- exporta sessão atual para `~/.nyx/exports/session_TIMESTAMP.md`
- `/export json` -- exporta como JSON
- Inclui: histórico, arquivos, métricas

### /copy
- `/copy` -- copia último output do agent para clipboard
- Usa `xclip` ou `xsel` no Linux
- Fallback: salva em `/tmp/nyx_clipboard.txt`

### /summary
- `/summary` -- gera resumo da sessão em PT-BR
- Lista: ações tomadas, arquivos modificados, decisões-chave
- Formato bullet-point

### /stats
- `/stats` -- estatísticas detalhadas
- Iterações total, por tipo de tool, taxa de sucesso
- Parser: taxa por nível de fallback
- Tempo: total, médio por iteração

### /usage
- `/usage` -- uso de tokens e contexto
- Tokens estimados: system, user, assistant
- Budget: % usado, nível de compactação
- Histórico: N entradas, N compactadas

### Testes Gauntlet

| ID | Nome | Validação |
|----|------|-----------|
| P5S-01 | /resume registrado | Command existe e retorna magic string |
| P5S-02 | /export gera arquivo | Exporta e verifica arquivo criado |
| P5S-03 | /copy registrado | Command existe |
| P5S-04 | /summary gera resumo | Contém "ações" ou "arquivos" |
| P5S-05 | /stats mostra métricas | Contém "iterações" ou "parser" |
| P5S-06 | /usage mostra tokens | Contém "tokens" ou "contexto" |

## Verificação

- [ ] 6 commands registrados
- [ ] /export cria arquivo real
- [ ] /stats calcula métricas reais
- [ ] /usage usa ContextBudget real
- [ ] 6 testes Gauntlet passando

---

*"O que não se mede não se gerencia." -- Peter Drucker*
