## 0. SPEC (machine-readable)

```yaml
sprint:
  id: P-07
  title: "CLI REPL (banner, /commands, sessão, resumo)"
  touches:
    - path: nyx/cli.py
      reason: "REPL completo com banner, comandos, sessão"
  acceptance_criteria:
    - "Banner Nyx com modelo, projeto, tools, num_ctx"
    - "Comandos: /help, /quit, /clear, /status"
    - "Prompt 'nyx>' com cores"
    - "Resumo da sessão ao sair (iterações, arquivos lidos/modificados, tempo)"
    - "Ctrl+C cancela operação atual, Ctrl+D sai"
```

---

# Sprint P-07 -- CLI REPL

**Status:** CONCLUIDA (header corrigido em MASTER-CLEANUP-02 2026-05-20; presença em concluidos/ implica CONCLUIDA conforme convenção do projeto)
**Prioridade:** ALTA
**Tipo:** Feature
**Dependências:** P-06
**Desbloqueia:** P-08, V-01

## Referência Luna

`scripts/nyx_cli.py`:
- Banner: modelo, projeto, tools, context
- Prompt: `nyx>`
- Comandos: /help, /quit, /code, /explain
- Resumo: iterações, arquivos, tempo
- Ctrl+C: cancela, Ctrl+D: sai

## Adaptação Nyx

Mesmo fluxo, mas:
- Cores Nyx (#00D4AA) em vez de cyan genérico
- Comandos: /help, /quit, /clear, /status, /model
- Integração com Rich (prompt-toolkit opcional)

---

*"O terminal é o lar do programador." -- Ken Thompson*
