## 0. SPEC (machine-readable)

```yaml
sprint:
  id: INFRA-03
  title: "sync.py enhanced -- verificação de integração completa"
  touches:
    - path: scripts/sync.py
      reason: "Novas verificações de integração"
  tests:
    - cmd: "./run.sh --gauntlet --only infra"
      timeout: 30
  acceptance_criteria:
    - "Verifica todo .py em tools/ importado no registry"
    - "Verifica todo @nyx_command aparece no /help"
    - "Verifica todo service importa"
    - "Verifica PORT_STATUS.md atualizado"
    - "Verifica nenhum test_*.py solto"
```

---

# Sprint INFRA-03 -- sync.py enhanced

**Status:** PENDENTE
**Data:** 2026-04-05
**Prioridade:** ALTA
**Tipo:** Infra
**Dependências:** INFRA-02
**Desbloqueia:** --

---

## Implementação

Adicionar ao SyncChecker existente:

### _check_tool_registration()
- Lista todos os .py em `nyx/agent/tools/` (exceto __init__, base, registry)
- Verifica que cada um está importado no registry.py
- ERRO se algum arquivo não importado

### _check_command_coverage()
- Conta @nyx_command em commands.py
- Verifica que o total bate com o esperado

### _check_service_imports()
- Import dinâmico de cada .py em services/
- ERRO se import falha

### _check_no_loose_tests()
- `find . -name "test_*.py"` excluindo venv
- ERRO se encontrar

### _check_port_status()
- Verifica que PORT_STATUS.md existe e contém números atuais

## Integração

- sync.py registrado como verificação no Gauntlet (fase `infra`)
- Resultados aparecem no GAUNTLET_REPORT.md
- CI usa `./run.sh --gauntlet` que inclui sync

## Verificação

- [ ] `./run.sh --gauntlet --only infra` inclui sync verificações
- [ ] Todas as verificações passam no estado atual
- [ ] Se adicionar tool sem registrar, sync detecta
- [ ] Gauntlet fase `coverage` complementa sync

---

*"A ordem é o primeiro passo para a liberdade." -- Aristóteles*
