# ADR 005: Anonimato

## Status
ACEITA (2026-04-04)

## Contexto

Alinhamento com GUIDE.md global. Nenhum arquivo ou commit deve
mencionar nomes de IAs (Claude, GPT, Gemini, Copilot, Anthropic, OpenAI).

## Decisão

**Proibido em qualquer arquivo ou commit:**
- Nomes: Claude, GPT, Gemini, Copilot, Anthropic, OpenAI
- Commits totalmente limpos e anônimos

**Exceções permitidas:**
- Strings técnicas: api_key, provider, model, config, client
- Documentação de API de terceiros
- Variáveis de ambiente: ANTHROPIC_API_KEY, OPENAI_API_KEY
- Diretório reference/ (fonte original da TUI)

## Consequências

- Commits passam no hook check_anonimato da Luna
- Projeto não tem dependência nominal de nenhum provider

## Enforcement

Hook de pre-commit bloqueia commits com nomes de IA no subject.
