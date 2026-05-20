## 0. SPEC (machine-readable)

```yaml
sprint:
  id: F-02
  title: "Gauntlet E2E real -- validação interativa de tools"
  touches:
    - path: scripts/gauntlet/nyx_gauntlet.py
      reason: "Nova fase e2e_real com 8 testes de execução real"
  forbidden:
    - "Mocks de qualquer tipo (ADR-010)"
    - "Testes que verificam só success sem validar conteúdo (ADR-011)"
  tests:
    - cmd: "./run.sh --gauntlet --only e2e_real"
      timeout: 60
  acceptance_criteria:
    - "8 testes de execução real de tools em cadeia"
    - "Todos verificam CONTEÚDO, não só success"
    - "Sem Ollama necessário (execução direta via ToolRegistry)"
    - "Acentuação PT-BR correta"
```

---

# Sprint F-02 -- Gauntlet E2E real

**Status:** CONCLUIDA (header corrigido em MASTER-CLEANUP-02 2026-05-20; presença em concluidos/ implica CONCLUIDA conforme convenção do projeto)
**Data:** 2026-04-05
**Prioridade:** ALTA
**Tipo:** Fix
**Dependências:** P-01 (agent loop)
**Desbloqueia:** --

---

## Problema / Contexto

Os testes E2E atuais (fase `e2e`) verificam imports, atributos e configs.
Nenhum executa tools reais com dados reais em cadeia.
Precisamos validar que o pipeline de tools funciona de ponta a ponta.

## Implementação

Nova fase `e2e_real` no Gauntlet que executa tools via `ToolRegistry.execute()` diretamente.

### Testes

| ID | Nome | Validação |
|----|------|-----------|
| F2-01 | Write+Read roundtrip | Escreve /tmp/nyx_f2.py, lê de volta, compara conteúdo exato |
| F2-02 | Edit com substituição | Edita arquivo criado (old_string->new_string), lê e verifica |
| F2-03 | Glob encontra arquivo real | Glob `*.py` no projeto, verifica que retorna paths existentes |
| F2-04 | Search encontra conteúdo | Search "think" nos arquivos, verifica proxy.py na saída |
| F2-05 | RunCommand real | `echo NYX_E2E_OK`, verifica que output contém a string |
| F2-06 | ListFiles diretório real | Lista `nyx/agent/`, verifica loop.py na saída |
| F2-07 | Tool error handling | Read arquivo inexistente, verifica erro descritivo |
| F2-08 | Pipeline completo | write->read->edit->read->glob->done em cadeia |

## Verificação

- [ ] 8 testes passando em `e2e_real`
- [ ] Todos validam conteúdo real
- [ ] Sem Ollama necessário
- [ ] `./run.sh --gauntlet --only e2e_real` passa 100%
- [ ] Gauntlet completo continua passando

---

*"Medir é o primeiro passo para controlar." -- H. James Harrington*
