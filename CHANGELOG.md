# Changelog

Todas as mudanças notáveis neste projeto serão documentadas neste arquivo.

O formato é baseado em [Keep a Changelog](https://keepachangelog.com/pt-BR/1.0.0/),
e este projeto adere ao [Versionamento Semântico](https://semver.org/lang/pt-BR/).

## [1.1.1] - 2025-10-01

### Adicionado
- Licença GPLv3
- Código de Conduta (Contributor Covenant v2.1)
- Política de Segurança (SECURITY.md)
- Guia de contribuição (CONTRIBUTING.md)
- Templates de issue e PR para GitHub
- Changelog completo
- .mailmap para unificação de identidade git

### Corrigido
- README atualizado com contagens corretas (47 commands, 10 services)
- pyproject.toml modernizado com build-system, classifiers e URLs
- CI com trigger de push para main

## [1.1.0] - 2025-08-15

### Adicionado
- Anti-OOM com auto-recovery para GPU limitada
- Parser robusto para GPU limitada
- Blindagem da infraestrutura (5 fixes para compensar modelo fraco)

### Corrigido
- Proxy think adaptativo (habilitar think quando há tools)
- Limpeza PROD: stubs removidos, boot corrigido, commands reais implementados
- Timeout LLM aumentado para 600s (hardware lento)

## [1.0.0] - 2025-05-01

### Adicionado
- Port completo ondas 10-16 do Claude Code TS (127K linhas → Python)
- Identidade visual Dracula Gothic + 20 ADRs
- Documentação completa e reorganização (dev-journey/)
- Proxy para tool calling funcional com modelo local

### Corrigido
- Proxy normaliza content array para string Ollama
- Auditoria completa de acentuação, cores e integração

## [0.5.0] - 2025-01-15

### Adicionado
- Agente funcional com REPL interativo (prompt-toolkit + Rich)
- 34 tools via ToolRegistry
- 47 slash commands
- Proxy think=false para tool calling nativo
- E2E completo (6 tools + 26 slash commands testados)
- Simulação de usuário real com resultados honestos

## [0.1.0] - 2024-08-01

### Adicionado
- Estrutura inicial do projeto Nyx-Code
- Integração com Ollama (porta 11435)
- Seleção de modelo (qwen3:4b como padrão, tool calling nativo)
- Scripts install.sh, run.sh e uninstall.sh
- Interface funcional restaurada
- Suporte GPU via Ollama do sistema
