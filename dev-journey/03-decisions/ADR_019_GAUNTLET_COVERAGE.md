# ADR-019: Gauntlet coverage automática

**Data:** 2026-04-05
**Status:** Aceita
**Contexto:** Garantir que nenhum componente fica sem teste

---

## Decisão

O Gauntlet inclui uma fase `coverage` que roda automaticamente e verifica:

1. **Tools:** toda tool no ToolRegistry tem pelo menos 1 teste
2. **Commands:** todo command registrado tem pelo menos 1 teste
3. **Services:** todo .py em services/ importa sem erro
4. **Nada solto:** nenhum test_*.py fora do Gauntlet
5. **Nada órfão:** todo .py em tools/ está importado no registry

## Motivo

Sem verificação automática, é fácil esquecer de testar um componente novo. A fase coverage é o "compilador" que garante completude.

## Implementação

Fase `coverage` no Gauntlet (última fase, sempre roda):

```python
async def _phase_coverage(self) -> None:
    # 1. Toda tool registrada tem teste no gauntlet
    # 2. Todo command registrado tem teste no gauntlet
    # 3. Todo service importa
    # 4. Nenhum test_*.py solto
    # 5. Todo .py em tools/ importado no registry
```

## Quando roda

- Sempre que `--only completo` ou sem `--only` (default)
- FALHA bloqueia merge na main (via CI)

---

*"O que pode ser verificado automaticamente deve ser." -- Edsger Dijkstra*
