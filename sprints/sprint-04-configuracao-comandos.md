# Sprint 4: Configuração, Comandos e Integração de Features

**Objetivo:** Configurar o openclaude para funcionar corretamente com o modelo
local, integrar slash commands, pré-configurar tudo em PT-BR, e garantir que
todas as features acessíveis pela interface funcionem de verdade.

---

## Problemas atuais

### /config (settings que não funcionam ou precisam de ajuste)
- `Language`: Default (English) -- precisa ser PT-BR
- `Thinking mode`: false -- já desabilitado via flag mas precisa persistir
- `Model`: qwen3:4b -- correto mas precisa persistir
- `Default permission mode`: Accept edits -- correto
- `Output style`: default -- avaliar se precisa ajustar
- `Auto-compact`: true -- verificar se funciona com modelo local
- `Show tips`: true -- verificar se tips fazem sentido localmente
- `Terminal progress bar`: true -- verificar funcionamento
- `Verbose output`: false -- manter

### Slash commands que não funcionam
- `/terminal-setup` -- não suporta gnome-terminal (limitação)
- `/help` -- funciona mas mostra commands do Claude Code original
- `/config` -- abre mas settings podem não persistir
- `/compact` -- verificar se funciona com modelo local
- `/model` -- verificar se troca modelo funcional
- `/status` -- verificar se mostra info correta

### Command suggesters (autocomplete de /)
- Sugere commands que não existem (ex: `/bash` mostrado na sessão anterior)
- Precisa filtrar para apenas commands funcionais

---

## Plano de execução

### 4.1 Criar settings.json do projeto

Criar `~/Desenvolvimento/Nyx-Code/.claude/settings.json` (ou equivalente)
com configurações pré-definidas para o Nyx-Code:

```json
{
  "model": "qwen3:4b",
  "language": "pt-BR",
  "theme": "dark",
  "thinkingMode": false,
  "autoCompact": true,
  "showTips": false,
  "verboseOutput": false,
  "terminalProgressBar": true,
  "showTurnDuration": true,
  "defaultPermissionMode": "bypass",
  "outputStyle": "default"
}
```

### 4.2 Criar CLAUDE.md do projeto Nyx-Code

Arquivo `.claude/CLAUDE.md` ou `CLAUDE.md` na raiz que define o comportamento:

```markdown
# Nyx-Code

## Identidade
Você é Nyx, agente de código local.

## Regras
- Responda SEMPRE em PT-BR
- Use as tools (Read, Write, Edit, Bash, Glob, Grep) quando pedirem
- Seja direto e conciso
- Nunca diga que não pode acessar o sistema de arquivos
```

O openclaude carrega CLAUDE.md automaticamente como contexto (exceto com --bare).

### 4.3 Configurar via flags no run.sh

Passar configurações via flags ao invés de depender de ~/.claude/:
- `--system-prompt` com identidade e regras (já feito)
- `--thinking disabled` (já feito)
- `--dangerously-skip-permissions` (já feito)
- Avaliar: `--disable-slash-commands` para remover commands inúteis

### 4.4 Mapear e filtrar slash commands

Listar todos os commands do openclaude e classificar:

| Comando | Funciona | Ação |
|---------|----------|------|
| `/help` | Parcial | Ajustar para mostrar só commands funcionais |
| `/config` | Parcial | Settings que fazem sentido localmente |
| `/model` | Verificar | Trocar entre qwen3:4b, qwen2.5-coder:3b, 7b |
| `/compact` | Verificar | Compactar contexto da sessão |
| `/status` | Verificar | Status do provider/modelo |
| `/clear` | Verificar | Limpar sessão |
| `/diff` | Verificar | Mostrar git diff |
| `/commit` | Verificar | Fazer git commit |
| `/review` | Verificar | Review de código |
| `/doctor` | Verificar | Diagnóstico do sistema |
| `/terminal-setup` | Não | Não suporta gnome-terminal |
| `/login` | Não | Irrelevante (modelo local) |
| `/logout` | Não | Irrelevante |

### 4.5 Testar cada command

Para cada command funcional, testar no modo interativo:
1. Digitar o comando
2. Verificar se executa ou dá erro
3. Documentar resultado
4. Se não funciona: desabilitar ou adaptar

### 4.6 Integrar estética da Luna

Referência: `src/skills/code_agent/rich_output.py` e `run_luna.sh`.

O que copiar/adaptar da Luna para o Nyx-Code:
- **Paleta de cores**: Roxo/violeta como primária (já no banner)
- **Banner**: Manter o banner Nyx atual mas alinhar estilo Luna
- **Barra de status**: ctx%, iter, files, edits, tempo
- **Formatação de diffs**: Bordas estilizadas
- **Mensagens de erro**: Claras com sugestões
- **PT-BR**: Tudo em português

A estética visual do openclaude já é boa (TUI com bordas, cores).
O ajuste principal é:
- Trocar textos internos para PT-BR onde possível
- Cores Nyx no banner/prompt do run.sh
- CLAUDE.md em PT-BR para contexto

### 4.7 Pré-configurar .env com defaults otimizados

Atualizar `.env.example` e `.env` com valores otimizados para uso local:

```env
NYX_MODEL=qwen3:4b
NYX_OLLAMA_PORT=11435
NYX_VRAM_MAX=2.5
NYX_NUM_GPU=20
NYX_NUM_CTX=4096
NYX_TEMPERATURE=0.3
NYX_DEBUG=0
NYX_LANGUAGE=pt-BR
```

---

## Adicionar ao install.sh

O `install.sh` deve criar automaticamente:
- `.claude/settings.json` com configurações padrão
- `CLAUDE.md` com identidade Nyx
- `.env` com defaults otimizados (já faz isso)

---

## Verificação

- [ ] `/config` mostra settings corretos (model, language, theme)
- [ ] `/help` mostra apenas commands funcionais
- [ ] `/model` lista modelos disponíveis (qwen3:4b, qwen2.5-coder:3b, 7b)
- [ ] `/compact` compacta contexto sem erro
- [ ] `/status` mostra provider local + modelo correto
- [ ] `/clear` limpa sessão
- [ ] `/diff` mostra git diff
- [ ] Autocomplete de `/` sugere apenas commands válidos
- [ ] Textos do banner e prompt em PT-BR
- [ ] CLAUDE.md carregado como contexto
- [ ] `install.sh` cria configurações automaticamente

---

## Arquivos a criar/modificar

- `CLAUDE.md` -- identidade Nyx + regras PT-BR
- `.claude/settings.json` -- settings pré-configurados
- `run.sh` -- ajustar flags conforme necessário
- `install.sh` -- criar CLAUDE.md e settings automaticamente
- `.env.example` -- novos defaults
