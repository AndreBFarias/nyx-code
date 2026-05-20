## 0. SPEC (machine-readable)

```yaml
sprint:
  id: AUDIT-02
  title: "Integracao de servicos mortos"
  touches:
    - path: nyx/agent/loop.py
      reason: "Integrar analytics, diagnostics, tool_use_summary, auto_compact, model_tier"
    - path: nyx/cli.py
      reason: "Integrar NyxSettings, InternalLogging, Analytics, cleanup_old_sessions"
    - path: nyx/config/settings.py
      reason: "Tornar single source of truth para configuracao"
    - path: nyx/providers/ollama.py
      reason: "Integrar como provider do loop em vez de httpx direto"
    - path: nyx/agent/services/analytics.py
      reason: "Conectar ao CLI e loop"
    - path: nyx/agent/services/logging_service.py
      reason: "Ativar no startup da CLI"
    - path: nyx/agent/services/diagnostics.py
      reason: "Conectar ao loop para tracking de erros"
    - path: nyx/agent/services/tool_use_summary.py
      reason: "Conectar ao loop para tracking de tools"
    - path: nyx/agent/services/compact.py
      reason: "Substituir compactacao inline do loop"
    - path: nyx/agent/model_tier.py
      reason: "Usar para configurar loop automaticamente"
    - path: nyx/agent/path_resolver.py
      reason: "Integrar para resolucao de paths do LLM"
    - path: nyx/agent/persistence.py
      reason: "Chamar cleanup_old_sessions no startup"
  n_to_n_pairs:
    - "NyxSettings deve ser a unica fonte de modelo, proxy_url, max_iterations"
    - "Todos os services devem ter status() chamavel via /doctor"
  forbidden:
    - "Nunca usar os.environ direto para configs que existem em NyxSettings"
  tests:
    - cmd: "./run.sh --gauntlet --only audit_integracao"
      timeout: 300
  acceptance_criteria:
    - "CLI usa NyxSettings em vez de os.environ"
    - "Loop usa OllamaProvider em vez de httpx direto"
    - "Analytics rastreia tool calls e sessoes"
    - "InternalLogging ativo com rotacao"
    - "ToolUseSummary alimentado a cada tool call"
    - "DiagnosticTracking alimentado a cada erro"
    - "ModelTier configura loop automaticamente"
    - "cleanup_old_sessions chamado no startup"
    - "Acentuacao PT-BR correta"
```

---

# Sprint AUDIT-02 -- Integracao de Servicos Mortos

**Status:** CONCLUIDA (header corrigido em MASTER-CLEANUP-02 2026-05-20; presença em concluidos/ implica CONCLUIDA conforme convenção do projeto)
**Data:** 2026-04-15
**Prioridade:** ALTA
**Tipo:** Refactor/Integracao
**Dependencias:** AUDIT-01 (seguranca resolve antes)
**Desbloqueia:** AUDIT-04

---

## Problema / Contexto

A auditoria identificou 10 modulos que existem, estao implementados e testados pelo Gauntlet, mas nunca sao instanciados pelo sistema:

1. `NyxSettings` -- config centralizada, ignorada pelo CLI
2. `OllamaProvider` -- provider com retry, ignorado pelo loop
3. `PathResolver` -- resolucao de paths, nunca instanciado
4. `AutoCompactService` -- compactacao gerenciada, loop faz inline
5. `Analytics` -- metricas de uso, nunca conectado
6. `InternalLogging` -- logging rotacionado, nunca ativado
7. `ToolUseSummary` -- resumo de tools, nunca alimentado
8. `DiagnosticTracking` -- tracking de erros, nunca alimentado
9. `ModelTier` -- auto-detect GPU, nunca usado
10. `cleanup_old_sessions` -- funcao de limpeza, nunca chamada

Sao orgaos funcionais fora do corpo. Esta sprint faz a cirurgia de transplante.

## Implementacao

### Fase 1: NyxSettings como fonte unica

Modificar `cli.py` para:
1. Chamar `load_settings()` no inicio
2. Passar settings para `AgentLoop` em vez de strings individuais
3. Remover os.environ direto para modelo, proxy, etc

### Fase 2: OllamaProvider no loop

Modificar `loop.py`:
1. Receber OllamaProvider no construtor (ou criar internamente)
2. Substituir `_call_llm` para usar `provider.chat()`
3. O provider ja tem retry com backoff

### Fase 3: Services no loop e CLI

No `AgentLoop.__init__`:
- Instanciar `ToolUseSummary`
- Instanciar `DiagnosticTracking`
- Usar `AutoCompactService` em vez de compactacao inline
- Usar `ModelTier` para definir max_iterations, num_ctx, etc

No `cli.py` startup:
- Instanciar `InternalLogging()`
- Instanciar `Analytics()`
- Chamar `cleanup_old_sessions()`

No loop, a cada tool call:
- `analytics.track_tool(name)`
- `tool_use_summary.track(name, args)`

No loop, a cada erro:
- `diagnostics.record_error(source, message)`

No CLI ao sair:
- `analytics.end_session()`

### Fase 4: /doctor integrado

Expandir `cmd_doctor` para chamar `.status()` de cada servico ativo.

## Verificacao

- [ ] `cli.py` nao tem mais `os.environ.get("OPENAI_MODEL"...)` direto
- [ ] Loop usa OllamaProvider com retry
- [ ] `~/.nyx/analytics/metrics.json` e criado apos primeira sessao
- [ ] `~/.nyx/logs/nyx.log` e criado com rotacao
- [ ] /doctor mostra status de todos os servicos
- [ ] Sessoes antigas (>7 dias) sao limpas no startup
- [ ] ModelTier detecta GPU e configura loop
- [ ] Gauntlet fase audit_integracao passa
- [ ] Acentuacao PT-BR correta

---

*"O todo e mais que a soma das partes." -- Aristoteles*
