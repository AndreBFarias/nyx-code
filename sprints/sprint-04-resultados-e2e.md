# Sprint 4: Resultados E2E

Todos os testes executados via `expect` (pseudo-terminal interativo real).
Nenhum comando foi escondido ou desabilitado.

## Tools (execução real com modelo qwen3:4b)

| Tool | Resultado | Verificação |
|------|-----------|-------------|
| Bash | OK | Executou `ls README.md`, retornou resultado |
| Read | OK | Leu CLAUDE.md, detectou conteúdo "Nyx/agente/PT-BR" |
| Glob | OK | Listou arquivos .md do projeto |
| Grep | OK | Buscou "Nyx" nos arquivos, encontrou matches |
| Write | OK (modelo chamou) | Pattern match OK no expect |
| Edit | OK (modelo chamou) | Pattern match OK no expect |

## Slash Commands (interativo)

| Comando | Exit Code | Resultado |
|---------|-----------|-----------|
| /help | 0 | Painel com atalhos e docs |
| /status | 0 | Provider: OpenAI-compatible, Model: qwen3:4b, MCP: 2 |
| /config | 0 | 13+ settings editáveis |
| /model | 0 | Seletor de modelo |
| /diff | 0 | Lista uncommitted files |
| /doctor | 0 | Diagnóstico: path, config, instalações |
| /compact | 0 | Executou sem erro |
| /cost | 0 | Executou sem erro |
| /memory | 0 | Executou sem erro |
| /vim | 0 | Executou sem erro |
| /theme | 0 | Executou sem erro |
| /clear | 0 | Executou sem erro |
| /commit | 0 | Painel de commit |
| /review | 0 | Painel de review |
| /session | 0 | Executou sem erro |
| /files | 0 | Painel de arquivos |
| /permissions | 0 | Painel de permissões |
| /stats | 0 | Estatísticas da sessão |
| /usage | 0 | Info de uso |
| /mcp | 0 | Lista MCP servers |
| /terminal-setup | 0 | Info sobre setup (gnome-terminal limitado) |
| /fast | 0 | Toggle modo rápido |
| /init | 0 | Inicialização de projeto |
| /add-dir | 0 | Executou sem erro |
| /hooks | 0 | Executou sem erro |
| /skills | 0 | Lista skills disponíveis |
| /exit | 0 | Saiu corretamente |

## Performance

| Operação | Tempo médio |
|----------|-------------|
| Chat simples | 10-30s |
| Tool calling (1 turno) | 30-60s |
| Tool calling (multi-turno) | 1-3min |
| Slash command (TUI) | < 1s |

Hardware: RTX 3050 Laptop (4GB VRAM), qwen3:4b com num_gpu=20 (~1.6GB VRAM)

## Notas

- Nenhum "Unknown skill" em modo interativo
- Nenhum crash ou exit code != 0
- /terminal-setup: limitação real do gnome-terminal (não suporta Shift+Enter nativo)
- Performance de tools depende do modelo 4b local (não é bug)
- Write e Edit: modelo chama a tool corretamente, execução depende
  da velocidade do segundo turno (tool result -> resposta)
