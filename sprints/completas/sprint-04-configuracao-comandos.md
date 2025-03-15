# Sprint 4: Fazer Tudo Funcionar

**Objetivo:** Cada feature, comando e configuração do openclaude deve funcionar
com o modelo local. Nada é escondido ou desabilitado — tudo é adaptado.

---

## Inventário completo de slash commands

Extraído do código fonte (`cli.mjs` linhas 460451-460538). Todos os commands
públicos que o openclaude registra:

### Grupo 1: Essenciais (devem funcionar perfeitamente)

| Comando | Descrição | Status | Ação |
|---------|-----------|--------|------|
| `/help` | Lista de comandos | Testar | Garantir que lista tudo |
| `/config` | Configurações | Testar | Persistir model, language, thinking |
| `/model` | Trocar modelo | Adaptar | Listar modelos do Ollama local |
| `/clear` | Limpar sessão | Testar | Deve funcionar nativo |
| `/compact` | Compactar contexto | Testar | Essencial para modelo com contexto limitado |
| `/diff` | Git diff | Testar | Usa Bash internamente |
| `/status` | Status do provider | Adaptar | Mostrar Ollama, modelo, VRAM |
| `/exit` | Sair | Testar | Deve funcionar nativo |

### Grupo 2: Código e Git (core da ferramenta)

| Comando | Descrição | Status | Ação |
|---------|-----------|--------|------|
| `/commit` | Git commit | Testar | Usa Bash(git) internamente |
| `/commit-push-pr` | Commit + push + PR | Testar | Depende de gh CLI |
| `/review` | Review de código | Testar | Usa Read + análise |
| `/plan` | Planejar implementação | Testar | Prompt-based |
| `/security-review` | Auditoria de segurança | Testar | Prompt-based |
| `/release-notes` | Gerar release notes | Testar | Prompt-based |
| `/rename` | Renomear símbolo | Testar | Usa Edit internamente |

### Grupo 3: Navegação e Contexto

| Comando | Descrição | Status | Ação |
|---------|-----------|--------|------|
| `/add-dir` | Adicionar diretório ao contexto | Testar | |
| `/context` | Ver contexto atual | Testar | |
| `/files` | Listar arquivos no contexto | Testar | |
| `/resume` | Retomar sessão anterior | Testar | |
| `/session` | Info da sessão atual | Testar | |
| `/memory` | Memória persistente | Testar | |
| `/tasks` | Gerenciar tasks | Testar | |
| `/copy` | Copiar resposta | Testar | |

### Grupo 4: Configuração e Sistema

| Comando | Descrição | Status | Ação |
|---------|-----------|--------|------|
| `/theme` | Trocar tema | Testar | |
| `/color` | Configurar cores | Testar | |
| `/output-style` | Estilo de output | Testar | |
| `/effort` | Nível de esforço | Testar | |
| `/fast` | Modo rápido | Adaptar | Precisa de modelo fast no Ollama |
| `/vim` | Modo vim | Testar | |
| `/keybindings` | Atalhos de teclado | Testar | |
| `/terminal-setup` | Setup de terminal | Adaptar | Suportar gnome-terminal |
| `/permissions` | Gerenciar permissões | Testar | |
| `/privacy-settings` | Privacidade | Testar | |
| `/hooks` | Gerenciar hooks | Testar | |
| `/stats` | Estatísticas | Testar | |
| `/statusline` | Barra de status | Testar | |

### Grupo 5: Provider e Autenticação

| Comando | Descrição | Status | Ação |
|---------|-----------|--------|------|
| `/provider` | Configurar provider | Adaptar | Fixar como Ollama local |
| `/login` | Autenticar | Adaptar | Desnecessário para local, mas não travar |
| `/logout` | Desautenticar | Adaptar | Idem |
| `/cost` | Custo de uso | Adaptar | Mostrar custo zero (local) |
| `/usage` | Uso da API | Adaptar | Mostrar uso local |

### Grupo 6: Extensões e Plugins

| Comando | Descrição | Status | Ação |
|---------|-----------|--------|------|
| `/mcp` | Gerenciar MCP servers | Testar | |
| `/plugin` | Gerenciar plugins | Testar | |
| `/reload-plugins` | Recarregar plugins | Testar | |
| `/skills` | Listar skills | Testar | |
| `/chrome` | Integração Chrome | Testar | Se MCP Chrome estiver ativo |
| `/ide` | Integração IDE | Testar | |

### Grupo 7: Avançado

| Comando | Descrição | Status | Ação |
|---------|-----------|--------|------|
| `/doctor` | Diagnóstico do sistema | Adaptar | Verificar Ollama, GPU, modelos |
| `/init` | Inicializar projeto | Testar | |
| `/export` | Exportar sessão | Testar | |
| `/branch` | Gerenciar branches | Testar | |
| `/rewind` | Desfazer mudanças | Testar | |
| `/advisor` | Conselheiro de código | Testar | |
| `/feedback` | Enviar feedback | Adaptar | Redirecionar para GitHub do Nyx |
| `/pr-comments` | Comentários de PR | Testar | |
| `/tag` | Tagging | Testar | |
| `/upgrade` | Atualizar versão | Adaptar | Apontar para Nyx releases |
| `/stickers` | Adesivos | Testar | |
| `/thinkback` | Replay de raciocínio | Testar | |
| `/sandbox-toggle` | Toggle sandbox | Testar | |

---

## Processo de execução

### Fase 1: Testar tudo no estado atual

Executar cada comando listado acima na interface interativa.
Para cada um, registrar:
- Funciona? (sim/não/parcial)
- Mensagem de erro (se houver)
- Adaptação necessária

### Fase 2: Configuração base

1. Criar `CLAUDE.md` na raiz com identidade Nyx + regras PT-BR
2. Criar `.claude/settings.json` com defaults otimizados
3. Atualizar `run.sh` para não usar `--bare` (para carregar CLAUDE.md e commands)
   mas resolver o problema de autenticação de outra forma
4. Atualizar `install.sh` para criar configs automaticamente

### Fase 3: Adaptar commands que precisam de ajuste

Para cada command que não funciona:
1. Identificar a causa raiz (auth? provider? modelo?)
2. Se é configuração: ajustar settings
3. Se é código: documentar para port Python (Sprint 6)
4. Se é limitação do modelo: criar workaround via system prompt

### Fase 4: PT-BR completo

- `CLAUDE.md` em PT-BR
- System prompt em PT-BR (já feito)
- `/config` > Language: PT-BR
- Tips e mensagens: verificar se respeitam o idioma

---

## Verificação

- [ ] Cada comando do inventário testado e documentado
- [ ] Commands essenciais (Grupo 1) funcionando 100%
- [ ] Commands de código (Grupo 2) funcionando 100%
- [ ] Commands de navegação (Grupo 3) funcionando 100%
- [ ] Commands de config (Grupo 4) funcionando ou adaptados
- [ ] Commands de auth (Grupo 5) adaptados para local
- [ ] `/config` persiste configurações entre sessões
- [ ] `/model` troca entre modelos locais
- [ ] `/doctor` diagnostica Ollama + GPU + modelos
- [ ] PT-BR em todas as interfaces configuráveis
- [ ] `install.sh` cria todas as configurações automaticamente

---

## Arquivos a criar/modificar

- `CLAUDE.md` -- identidade Nyx + regras PT-BR
- `.claude/settings.json` -- settings pré-configurados
- `run.sh` -- resolver autenticação sem --bare
- `install.sh` -- criar CLAUDE.md e settings
- `.env` / `.env.example` -- defaults atualizados
