# ADR 007: Validação via Gauntlet -- Um Teste por Feature

## Status
ACEITA (2026-04-04)

## Contexto

O Nyx-Code precisa de validação automatizada que cubra todas as 62 features
mapeadas em `dev-journey/04-features/FEATURE_MAP.md`. Testes unitários isolados
não capturam problemas reais de integração (Ollama morre, VRAM estoura, proxy
perde conexão, modelo não gera tool_calls).

Replicando a decisão ADR-017 da Luna: a validação real é feita via Gauntlet
que roda o sistema inteiro (Ollama + Proxy + requests reais).

## Decisão

**Toda validação é feita via Gauntlet (`scripts/gauntlet/nyx_gauntlet.py`)
executado pelo `./run.sh --gauntlet`. Um teste por feature. Zero mocks.**

### Regras

1. **PROIBIDO**: Testes que mockem o Ollama, o proxy, ou tool calls.
2. **PROIBIDO**: Testes que rodem sem Ollama real.
3. **OBRIGATÓRIO**: Cada feature mapeada tem exatamente 1 teste no Gauntlet.
4. **OBRIGATÓRIO**: Gauntlet gera report em `GAUNTLET_REPORT.md` com KPIs.
5. **OBRIGATÓRIO**: Sprint que modifica proxy, run.sh, ou tools -> rodar Gauntlet.
6. **EXCEÇÃO**: Lógica pura sem dependência de LLM (utils, config) pode ter pytest.

### Fases do Gauntlet

| Fase | Features | Tempo estimado |
|------|----------|----------------|
| infra | I-01 a I-11 | ~2min |
| proxy | P-01 a P-08 | ~3min |
| tools | T-01 a T-10 | ~8min |
| qualidade | Q-01 a Q-07 | ~5min |
| performance | K-01 a K-10 | ~3min |
| visual | V-01 a V-07 | ~1min |
| config | C-01 a C-04 | ~1min |
| resiliencia | R-01 a R-05 | ~3min |

### Como rodar

```bash
./run.sh --gauntlet              # Completo (~25min)
./run.sh --gauntlet --only tools # Só uma fase
./run.sh --gauntlet --only rapido # Fases rápidas (infra+proxy+visual+config)
```

### Report

Gerado em `GAUNTLET_REPORT.md` (raiz) e `dev-journey/07-reports/gauntlet/`.
Formato: markdown com tabelas de resultado, KPIs, e tempos.

## Consequências

### Positivas
- Validação real com Ollama, proxy e modelo reais
- KPIs medidos em cada execução (tempos, tokens, VRAM)
- Um único script cobre todas as features
- Report histórico permite detectar regressões

### Negativas
- Requer GPU e Ollama rodando (~25min)
- Não roda em CI sem GPU (skip automático)

## Enforcement

Sprint que modifica arquivos críticos -> Gauntlet obrigatório.

---

*"O teste que testa mocks em vez de código real não é um teste -- é teatro." -- Pragmático*
