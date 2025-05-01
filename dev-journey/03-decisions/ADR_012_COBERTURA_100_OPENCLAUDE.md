# ADR-012: Cobertura 100% do OpenClaude

**Data:** 2026-04-05
**Status:** Aceita
**Contexto:** Port do OpenClaude TypeScript para Python

---

## Decisão

Todo tool, command e service presente no source do OpenClaude (`openclaud/src/`) deve ter um equivalente funcional em Python no Nyx (`nyx/`).

## Motivo

O Nyx é um port 1:1 do OpenClaude. Cobertura parcial significa funcionalidade incompleta. Mesmo features cloud-specific devem ter equivalentes locais (adaptados para local-first).

## Métricas

| Componente | OpenClaude | Meta Nyx | Validação |
|-----------|-----------|---------|-----------|
| Tools | 40 | 40+ | `ToolRegistry.tool_count >= 40` |
| Commands | 98 | 98+ | `len(list_commands()) >= 98` |
| Services | 35 | 35+ | Imports sem erro |

## Regras

1. Cada tool do OpenClaude tem 1 arquivo Python em `nyx/agent/tools/`
2. Cada command do OpenClaude tem 1 handler em `nyx/agent/commands.py`
3. Cada service do OpenClaude tem 1 arquivo em `nyx/agent/services/`
4. Features cloud adaptadas para local-first (arquivo local, não API remota)
5. Gauntlet valida cada item com pelo menos 1 teste (ADR-011)

## Mapeamento

Documento completo: `dev-journey/PORT_STATUS.md`

---

*"Completude é a medida da seriedade." -- Ludwig Wittgenstein*
