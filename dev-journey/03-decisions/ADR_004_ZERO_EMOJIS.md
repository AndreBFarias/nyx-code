# ADR 004: Zero Emojis

## Status
ACEITA (2026-04-04)

## Contexto

Alinhamento com projeto Luna. Emojis são genéricos, infantis e quebram
a estética cyberpunk de terminal. Luna é única, não é chatbot genérico.

## Decisão

**Zero emojis em código, commits, docs, respostas do agente e interface.**

### Abrangência

- Código Python e Shell: zero emojis em strings, logs, comentários
- Commits: mensagens em PT-BR, sem emojis
- Documentação: markdown sem emojis
- System prompt: instruir o modelo a nunca usar emojis
- Interface: sem emojis decorativos

### System prompt

```
Zero emojis. Zero verbosidade. Zero linguagem corporativa.
```

## Consequências

### Positivas
- Estética coerente com Luna
- Interface mais profissional e limpa
- Modelo local gera menos tokens desnecessários

### Negativas
- Nenhuma

## Enforcement

Revisão manual em code review. Futuro: hook de pre-commit.
