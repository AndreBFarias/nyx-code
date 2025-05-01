## 0. SPEC (machine-readable)

```yaml
sprint:
  id: INFRA-02
  title: "Gauntlet coverage -- fase automática de completude"
  touches:
    - path: scripts/gauntlet/nyx_gauntlet.py
      reason: "Nova fase 'coverage' que verifica completude"
  tests:
    - cmd: "./run.sh --gauntlet --only coverage"
      timeout: 30
  acceptance_criteria:
    - "Verifica toda tool no registry tem teste"
    - "Verifica todo command tem teste"
    - "Verifica todo service importa"
    - "Verifica nenhum test_*.py solto"
    - "Verifica todo .py em tools/ está no registry"
    - "FALHA se qualquer gap detectado"
```

---

# Sprint INFRA-02 -- Gauntlet coverage

**Status:** PENDENTE
**Data:** 2026-04-05
**Prioridade:** CRITICA
**Tipo:** Infra
**Dependências:** INFRA-01
**Desbloqueia:** P9, P10, P11

---

## Implementação

### Fase `coverage` no Gauntlet

```python
async def _phase_coverage(self) -> None:
    # COV-01: Toda tool no registry tem teste
    # Escaneia self._results, verifica que cada tool name aparece em algum teste

    # COV-02: Todo command registrado tem teste
    # Compara list_commands() com testes que exercitam handle_command()

    # COV-03: Todo service importa sem erro
    # Import dinâmico de cada .py em nyx/agent/services/

    # COV-04: Nenhum test_*.py solto
    # find no projeto, falha se encontrar

    # COV-05: Todo .py em tools/ está no registry
    # Lista arquivos, verifica import no registry.py

    # COV-06: Registry tool_count == esperado
    # Compara com meta do PORT_STATUS.md
```

### Configuração

- Fase `coverage` sempre na última posição
- Incluída em `completo` e no default (sem --only)
- Timeout: 30s (só verifica, não executa tools)

## Verificação

- [ ] `./run.sh --gauntlet --only coverage` roda e reporta gaps
- [ ] Se todas as tools têm teste, coverage passa
- [ ] Se falta teste para uma tool, coverage falha
- [ ] Fase aparece no report final

---

*"Confiança vem da verificação." -- Ronald Reagan*
