# ADR-015: Documentação para continuidade

**Data:** 2026-04-05
**Status:** Aceita
**Contexto:** Permitir que nova sessão de IA continue o trabalho sem contexto prévio

---

## Decisão

O projeto deve ser documentado de forma que uma nova conversa com IA (ou novo desenvolvedor) possa entender e continuar o trabalho lendo apenas os arquivos do projeto.

## Documentos obrigatórios

| Documento | Local | Propósito |
|-----------|-------|-----------|
| `CLAUDE.md` | raiz | Instruções para IA: identidade, convenções, arquitetura |
| `README.md` | raiz | Visão geral: o que é, como rodar, estrutura |
| `SPRINT_ORDER_MASTER.md` | `dev-journey/06-sprints/` | Ordem de execução, estado de cada sprint |
| `PORT_STATUS.md` | `dev-journey/` | Mapeamento 1:1 OpenClaude -> Nyx (o que existe, o que falta) |
| `ARCHITECTURE.md` | `dev-journey/02-architecture/` | Diagrama de componentes, fluxo de dados |
| ADRs | `dev-journey/03-decisions/` | Decisões arquiteturais numeradas |

## Regras

1. **CLAUDE.md** é a fonte primária -- qualquer IA lê isso primeiro
2. **PORT_STATUS.md** mapeia CADA item do OpenClaude com status
3. **SPRINT_ORDER_MASTER** mostra exatamente o que fazer em seguida
4. Sprint MDs individuais têm spec YAML machine-readable
5. Atualizar docs junto com código (mesma sprint, mesmo commit)

## O que deve estar no CLAUDE.md

- Identidade do Nyx
- Arquitetura (Ollama -> Proxy -> Agent)
- Convenções de código (PT-BR, type hints, logging, citações)
- Lista de ADRs vigentes
- Referência ao PORT_STATUS.md para saber o que falta
- Referência ao SPRINT_ORDER_MASTER para saber a ordem

---

*"A documentação é uma carta de amor para o futuro." -- Damian Conway*
