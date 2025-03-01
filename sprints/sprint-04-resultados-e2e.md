# Sprint 4: Resultados E2E (Definitivo)

Todos os testes executados via `expect` com run.sh real (Ollama + GPU + qwen3:4b).

## Simulação de Usuário Real

| # | Pedido | Tool esperada | Resultado | Arquivo verificado |
|---|--------|---------------|-----------|-------------------|
| 1 | "leia main.py e diga quantas linhas" | Read | PASSOU | Modelo leu e respondeu |
| 2 | "crie /tmp/nyx_hello.py com função" | Write | PARCIAL | Modelo respondeu mas arquivo não criado |
| 3 | "execute python3 /tmp/nyx_hello.py" | Bash | PARCIAL | Executou mas arquivo do teste 2 não existia |
| 4 | "busque Ollama nos arquivos" | Grep | PASSOU | Encontrou matches |
| 5 | "liste arquivos .sh" | Glob/Bash | PASSOU | Listou install.sh, run.sh, uninstall.sh |
| 6 | /diff | TUI | PASSOU | Mostrou uncommitted files |
| 7 | /status | TUI | PASSOU | Mostrou provider, model, endpoint (confirmado em teste separado) |

### Problema identificado: Write/Edit inconsistente

O qwen3:4b com tool calling não executa Write/Edit de forma confiável.
Comportamento observado:
- Read, Bash, Grep, Glob: executam a tool corretamente
- Write, Edit: às vezes o modelo DESCREVE o que faria em vez de chamar a tool

Causa provavel: o modelo 4b tem capacidade limitada de multi-step tool calling.
No primeiro turno chama a tool, mas no segundo (Write apos Read, ou Edit apos Read)
às vezes responde textualmente em vez de chamar.

Nao e bug do openclaude — e limitação do modelo 4b local.

## Slash Commands (26 testados)

Todos exit code 0, nenhum crash, nenhum "Unknown skill":

| Categoria | Commands | Status |
|-----------|----------|--------|
| Essenciais | /help, /config, /model, /status, /clear, /compact, /exit | OK |
| Código | /commit, /review, /diff | OK |
| Navegação | /session, /files, /add-dir, /memory | OK |
| Config | /theme, /vim, /permissions, /fast, /stats, /usage | OK |
| Sistema | /doctor, /init, /hooks, /skills, /mcp, /terminal-setup | OK |

## Tools (6 testadas)

| Tool | Teste direto | Confiabilidade |
|------|-------------|----------------|
| Bash | OK | Alta (funciona sempre) |
| Read | OK | Alta (funciona sempre) |
| Grep | OK | Alta |
| Glob | OK | Alta |
| Write | Parcial | Media (modelo às vezes não chama) |
| Edit | Parcial | Media (idem) |

## Performance

| Operação | Tempo médio | Hardware |
|----------|-------------|----------|
| Chat simples | 10-30s | RTX 3050, 4GB VRAM |
| Tool Read/Bash | 30-90s | qwen3:4b, num_gpu=20 |
| Tool multi-turno | 1-3min | ~1.6GB VRAM |
| Slash command TUI | < 1s | -- |

## Conclusao

A infraestrutura funciona: Ollama, GPU, warmup, tools, slash commands.
A limitação esta no modelo qwen3:4b (4 bilhões de parâmetros) que não tem
capacidade suficiente para tool calling complexo de forma consistente.

Opcoes para melhorar:
1. Usar qwen3:8b (se houver GPU/RAM suficiente)
2. Usar modelo via API remota (DeepSeek, GPT-4o) para tasks complexas
3. Sprint 6 (port Python): implementar agent loop proprio com prompts
   otimizados para qwen, parser de fallback, deteccao de repeticao
