# ADR-018: Stubs progressivos

**Data:** 2026-04-05
**Status:** Aceita
**Contexto:** Atingir 100% de cobertura de interfaces rapidamente

---

## Decisão

Features podem ser implementadas em 3 fases:

1. **Stub** -- Interface correta, retorna "Funcionalidade em desenvolvimento" ou equivalente mínimo
2. **Básico** -- Funcionalidade core implementada, teste Gauntlet valida conteúdo
3. **Completo** -- Funcionalidade completa, edge cases tratados

## Motivo

Implementar 98 componentes "completos" de uma vez é inviável. Stubs permitem:
- 100% de interfaces registradas (tools no registry, commands no /help, services importáveis)
- Gauntlet valida que tudo importa e registra sem erro
- Implementação gradual sem quebrar nada

## Regras

1. **Stub deve funcionar** -- não deve lançar exceção. Retorna output informativo.
2. **Stub tem teste** -- teste Gauntlet verifica que a tool/command existe e retorna algo
3. **Stub é temporário** -- sprint não é CONCLUIDA com stub. Precisa de implementação básica.
4. **Stub é documentado** -- PORT_STATUS.md marca como STUB até implementação básica

## Exemplo

```python
class MCPTool(RegisteredTool):
    action_type = ActionType.READ_FILE
    tool_def = ToolDef(name="mcp", description="...", parameters={...}, required=[...])

    def execute(self, params, project_root):
        # Fase 1: Stub
        return ActionResult(success=True, output="MCP: funcionalidade em desenvolvimento. Servidor local não configurado.")
```

---

*"Imperfeito e funcionando supera perfeito e inexistente." -- Reid Hoffman*
