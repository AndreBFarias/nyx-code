# ADR-016: Integração Luna no backlog

**Data:** 2026-04-05
**Status:** Aceita
**Contexto:** Priorização do port OpenClaude vs integração Luna

---

## Decisão

As sprints de integração com a Luna (I-02: Comando /nyx, I-03: Mensagens inline) são movidas para o backlog. A prioridade é completar o port 100% do OpenClaude.

## Motivo

1. O port do OpenClaude é pré-requisito para integração
2. Integração Luna requer modificar o repositório da Luna (escopo diferente)
3. O protocolo headless (I-01) já está feito e funcional
4. 100% de cobertura OpenClaude traz mais valor que integração parcial

## Estado

- **I-01** (Protocolo headless): CONCLUIDA -- `--headless` funciona com ping, status, tools, session, request, reset
- **I-02** (Comando /nyx na Luna): BACKLOG
- **I-03** (Mensagens inline): BACKLOG

## Pré-requisitos para retomar

1. Port 100% concluído (todos os blocos P9-P11)
2. Gauntlet com 250+ testes passando
3. Disponibilidade para modificar repositório Luna

---

*"Priorizar é dizer não." -- Steve Jobs*
