# ADR 006: PT-BR Obrigatório

## Status
ACEITA (2026-04-04)

## Contexto

Alinhamento com Luna. Todo texto voltado ao usuário e à documentação
deve ser em PT-BR com acentuação correta.

## Decisão

**PT-BR em:**
- Commits (tipo: descrição imperativa)
- Documentação (README, sprints, ADRs)
- Mensagens do run.sh e install.sh
- System prompt do agente
- Respostas do modelo (instruído via prompt)
- Comentários em código (quando necessário)

**Acentuação correta obrigatória:**
á, é, í, ó, ú, â, ê, ô, ã, õ, à, ç

**Exceções:**
- Nomes de variáveis e funções em inglês (padrão Python)
- Mensagens de log internas (podem ser inglês)
- Código de terceiros

## Enforcement

Revisão manual. Futuro: hook check_acentuação adaptado da Luna.
