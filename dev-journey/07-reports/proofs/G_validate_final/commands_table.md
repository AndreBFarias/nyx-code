# Total únicos: 66
# Total entradas (com aliases): 89

## /? -- OK
**Descrição:** Ajuda contextual (UX-AGENCY-01): mostra 3 ações relevantes ao estado atual
```text
  Ações disponíveis agora:
    /help                 -- catálogo completo de comandos
    /memory               -- memória persistente do projeto
    /resume               -- retomar sessão anterior
  (Em tool call ativa: Ctrl+C cancela; /cancel pausa fluxo)
```

## /add-dir -- ERR
**Descrição:** Adiciona diretório ao contexto do agent
```text
__error__Argumento obrigatório ausente em /add-dir.||Uso correto: /add-dir <caminho relativo ao projeto>.
```

## /advisor -- OK
**Descrição:** Conselheiro de código
```text
Analise '.' e sugira melhorias. Passos:
1. Use list_files(path='.') para ver estrutura
2. Use read_file nos arquivos principais
3. Avalie: complexidade, duplicação, nomes, organização, testes
4. Use done(summary='sugestões: <lista priorizada>')
```

## /aesthetic -- OK
**Descrição:** Lista, mostra ou troca o estético visual em runtime
**Aliases:** /estetica, /skin
```text
__aesthetic_list__
```

## /branch -- OK
**Descrição:** Operações de branch
**Aliases:** /br
```text
Branches:
* main
```

## /break-cache -- OK
**Descrição:** Limpa caches internos e sessões salvas em ~/.nyx/sessions
```text
  Cache limpo. 10 sessão(ões) removida(s).
```

## /brief-cmd -- OK
**Descrição:** Resumo rápido da sessão
```text
Gere um resumo em no máximo 3 linhas do trabalho realizado.
Foque em: o que foi feito, resultado, e próximo passo.
Use done(summary='resumo breve')
```

## /btw -- ERR
**Descrição:** Nota lateral para o agent
```text
__error__Argumento obrigatório ausente em /btw.||Uso: /btw <nota> -- injeta contexto sem gerar resposta.
```

## /cancel -- OK
**Descrição:** Cancela tool em curso (UX-AGENCY-01)
```text
__cancel_inflight__
```

## /cd -- ERR
**Descrição:** Troca o project_root corrente; o root antigo vira extra autorizado
```text
__error__/cd exige um caminho de destino.||Exemplo: /cd ~/Desenvolvimento/Outro-Projeto
```

## /clear -- OK
**Descrição:** Limpa a sessão (histórico, tela)
```text
__clear__
```

## /commit -- OK
**Descrição:** Cria um commit git
```text
Crie um commit git com as mudanças atuais. Passos:
1. Use run_command('git status --short') para ver mudanças
2. Use run_command('git diff HEAD') para ver detalhes
3. Use run_command('git log --oneline -5') para ver estilo de commits
4. Analise as mudanças e crie mensagem de commit em PT-BR
5. Use run_command('git add <arquivos relevantes>')
6. Use run_command('git commit -m "tipo: descrição"')
7. Use done(summary='commit criado: <hash> <mensagem>')

Regras:
... (3 linhas omitidas)
```

## /commit-push-pr -- OK
**Descrição:** Commit, push e PR
```text
Execute o fluxo completo: commit, push e PR. Passos:
1. Use run_command('git status --short') para ver mudanças
2. Use run_command('git diff HEAD') para ver detalhes
3. Use run_command('git log --oneline -5') para estilo de commits
4. Analise e crie mensagem de commit PT-BR, sem emojis, sem IA
5. Use run_command('git add <arquivos>')
6. Use run_command('git commit -m "tipo: descrição"')
7. Use run_command('git push -u origin <branch>')
8. Use run_command('gh pr create --title "..." --body "..."')
9. Use done(summary='PR criada: <url>')
```

## /compact -- OK
**Descrição:** Resume o que foi feito na sessão
```text
Resuma o trabalho realizado até agora.
Histórico atual:


Use done(summary='resumo') contendo:
1. O que foi feito (arquivos lidos/editados)
2. Decisões tomadas
3. Próximos passos sugeridos
```

## /config -- OK
**Descrição:** Mostra ou edita configuração (use /config setup para wizard)
```text
  Configuração atual:
    modelo: qwen2.5-coder:3b
    proxy: http://127.0.0.1:11436/v1
    ollama: http://127.0.0.1:11435
    projeto: .
    Use /config setup para gerar ~/.nyx/config.toml interativamente.
```

## /context -- OK
**Descrição:** Mostra uso do contexto
**Aliases:** /ctx
```text
__context__
```

## /copy -- OK
**Descrição:** Copia último output para clipboard
```text
__copy__
```

## /ctx-viz -- OK
**Descrição:** Visualização do contexto
```text
__context__
```

## /debug -- ERR
**Descrição:** Debug da sessão (subcomando: session)
```text
__error__Subcomando inválido para /debug.||Uso: /debug session -- métricas estruturadas da sessão corrente.
```

## /diff -- OK
**Descrição:** Mostra mudanças não commitadas
**Aliases:** /d
```text
Status:
M EXECUTAR_SPRINT.md
 M README.md
 M dev-journey/07-reports/gauntlet/baselines/baseline_2026-05-19.json
 M dev-journey/07-reports/gauntlet/checkpoint.json
 M dev-journey/PORT_STATUS.md
?? dev-journey/07-reports/proofs/G_validate_final/commands_table.md

Diff:
diff --git a/EXECUTAR_SPRINT.md b/EXECUTAR_SPRINT.md
... (215 linhas omitidas)
```

## /doctor -- OK
**Descrição:** Diagnóstico do sistema (Ollama, proxy, GPU, venv)
**Aliases:** /dr
```text
Diagnóstico Nyx:
  [ERRO] Ollama: não responde na porta 11435
  [ERRO] Proxy: não responde na porta 11436
  [OK] GPU: NVIDIA GeForce RTX 3050 Laptop GPU (3750/4096 MiB)
  [OK] Projeto:
  [OK] Venv: venv
  [OK] .env: presente
```

## /edit -- OK
**Descrição:** Edita o último input antes de reenviar (UX-EXTRA-01)
**Aliases:** /e
```text
__edit_last__
```

## /env -- OK
**Descrição:** Mostra variáveis de ambiente relevantes
```text
  Variáveis de ambiente:
    (nenhuma variável NYX/OPENAI/OLLAMA definida)
```

## /explain -- OK
**Descrição:** Analisa e explica um arquivo
**Aliases:** /exp
```text
Analise e explique o arquivo ''. Passos:
1. Use read_file para ler ''
2. Identifique: propósito, classes/funções principais, dependências, padrões de design usados
3. Use done(summary='explicação completa em português')
```

## /export -- OK
**Descrição:** Exporta sessão para arquivo
```text
__export__md
```

## /files -- OK
**Descrição:** Mostra arquivos no contexto
```text
__files__
```

## /help -- OK
**Descrição:** Mostra esta ajuda (/help <cmd> mostra exemplos; /help all lista tudo)
**Aliases:** /h
```text

  Sessão                    Contexto                  Modelo
  /resume — Retoma sessão (…/memory — Lista memórias… /model — Mostra ou troca…
  /compact — Resume o que f…/add-dir — Adiciona diret…/aesthetic — Lista, mostr…
  /context — Mostra uso do… /init — Inicializa estrut…/schema — Lista, mostra o…
  /clear — Limpa a sessão (…/sandbox — Lista, adicion…/output-style — Lista, mo…
  /quit — Sai do REPL salva…/cd — Troca o project_roo…/permissions — Mostra per…
  /stats — Estatísticas det…/skills — Lista skills di…/hooks — Lista hooks regi…
  /cancel — Cancela tool em…/files — Mostra arquivos… /theme — Lista ou troca t…
  /status — Mostra estado d…/paste — Lista imagens co…/config — Mostra ou edita…
... (6 linhas omitidas)
```

## /hooks -- OK
**Descrição:** Lista hooks registrados (pre/post tool)
```text
  Hooks são registrados via ToolRegistry.
  Tipos: pre (antes da tool), post (depois da tool)
  Exemplo: path_guard bloqueia acesso a .env
  Use /doctor para verificar estado do sistema.
```

## /init -- OK
**Descrição:** Inicializa estrutura ~/.nyx/ (memory, sessions, logs)
```text
  Nyx já inicializado. Diretórios existem.
```

## /insights -- OK
**Descrição:** Insights do projeto
```text
Gere insights sobre o projeto. Passos:
1. Use run_command('git log --oneline -20') para atividade recente
2. Use run_command('git shortlog -sn --since="1 month ago"') para contribuidores
3. Use list_files para ver estrutura geral
4. Use search para encontrar padrões (TODOs, FIXMEs, imports)
5. Use done(summary='insights: <análise>')
```

## /issue -- OK
**Descrição:** Cria/lista issues via gh CLI
```text
Nenhuma issue aberta.
```

## /mcp -- OK
**Descrição:** Lista, recarrega ou testa servers MCP (/mcp list|reload|test <name>)
```text
  Uso: /mcp <subcomando>
    list             -- lista servers configurados
    reload           -- re-conecta todos servers
    test <name>      -- ping em um server
```

## /memory -- OK
**Descrição:** Lista memórias persistentes do projeto
```text
Sem memórias gravadas. A Nyx grava via tool write_memory quando você pede pra lembrar algo estável.
```

## /model -- OK
**Descrição:** Mostra ou troca o modelo em runtime
**Aliases:** /m
```text
  Modelo atual: qwen2.5-coder:3b
  Use /model <nome> para trocar.
```

## /output-style -- OK
**Descrição:** Lista, mostra ou troca o estilo de saída (default/concise/learning)
**Aliases:** /style
```text
__output_style_list__
```

## /paste -- ERR
**Descrição:** Lista imagens coladas na sessão (Ctrl+V)
```text
__error__Nenhuma imagem colada ainda nesta sessão.||Use Ctrl+V com uma imagem no clipboard para colar.
```

## /permissions -- OK
**Descrição:** Mostra permissões por tool
**Aliases:** /perms
```text
  Permissões por nível:
    [always_confirm]
      - run_command
      - agent
      - todo_write
      - web_fetch
      - web_search
      - notebook_edit
    [auto_approve]
      - read_file
... (7 linhas omitidas)
```

## /plan -- OK
**Descrição:** Cria plano de implementação
```text
Crie um plano de implementação para:
Passos:
1. Use list_files para entender a estrutura do projeto
2. Use read_file nos arquivos relevantes
3. Use search para encontrar código relacionado
4. Use done(summary='plano detalhado') contendo:
   - Arquivos a criar/modificar
   - Ordem de implementação
   - Riscos e dependências
NÃO execute ações de escrita. Apenas planeje.
```

## /plugin -- OK
**Descrição:** Gerencia plugins instalados em ~/.nyx/plugins (/plugin list|reload|install|uninstall)
```text
  Uso: /plugin <subcomando>
    list                   -- lista plugins instalados
    reload                 -- re-descobre e re-carrega
    install <path>         -- copia <path> para ~/.nyx/plugins/
    uninstall <name>       -- remove plugin pelo nome
```

## /pr -- OK
**Descrição:** Lista/mostra PRs via gh CLI
```text
Nenhuma PR aberta.
```

## /pr-comments -- ERR
**Descrição:** Mostra comentários de PR
```text
__error__Argumento inválido para /pr-comments.||Uso correto: /pr-comments <número> -- ex: /pr-comments 123
```

## /progress -- OK
**Descrição:** Mostra ultimas N linhas do progress.md da sessão
**Aliases:** /gsd
```text
__progress_tail__30
```

## /quit -- OK
**Descrição:** Sai do REPL salvando a sessão atual
**Aliases:** /q, /exit
```text
__quit__
```

## /recall -- ERR
**Descrição:** Busca textual nas memórias do projeto (/recall <termo>)
**Aliases:** /rec
```text
__error__Argumento obrigatório ausente em /recall.||Use: /recall <termo> -- busca textual nas memórias do projeto.
```

## /replay -- ERR
**Descrição:** Re-renderiza sessão salva (read-only, sem chamar modelo)
```text
__error__Argumento obrigatório ausente em /replay.||Uso: /replay <session_id> -- ex: session_Nyx-Code_1776736000
```

## /resume -- OK
**Descrição:** Retoma sessão (sem arg = última, /resume list, /resume <prefixo>)
```text
__session_load__
```

## /review -- OK
**Descrição:** Review de pull request
**Aliases:** /rv
```text
Use run_command('gh pr list') para ver PRs abertos.
Depois use /review <número> para revisar uma PR específica.
```

## /rewind -- OK
**Descrição:** Desfaz últimas N ações do agent
```text
__rewind__1
```

## /sandbox -- OK
**Descrição:** Lista, adiciona ou remove roots permitidos no sandbox
**Aliases:** /roots
```text
__sandbox_list__
```

## /schema -- OK
**Descrição:** Lista, mostra ou troca o schema de interface (estrutura)
**Aliases:** /esquema, /layout
```text
__schema_list__
```

## /security-review -- OK
**Descrição:** Review de segurança
```text
Faça uma revisão de segurança em '.'. Passos:
1. Use list_files(path='.') para ver estrutura
2. Use search(pattern='password|secret|token|api_key') para buscar segredos
3. Use search(pattern='eval|exec|subprocess|os\.system') para injeção
4. Verifique: .env no .gitignore, permissões de arquivo, inputs não sanitizados
5. Use done(summary='revisão: N problemas encontrados')
```

## /session -- OK
**Descrição:** Gerencia sessões salvas
**Aliases:** /sess
```text
  Uso: /session <ação>
    list    -- lista sessões salvas
    save    -- salva sessão atual
    load    -- restaura última sessão
```

## /skills -- ERR
**Descrição:** Lista skills disponíveis
```text
__error__Nenhum skill registrado em ~/.nyx/skills/.||Crie arquivos .py com função execute() para disponibilizar skills.
```

## /stats -- OK
**Descrição:** Estatísticas detalhadas da sessão
```text
__stats__
```

## /status -- OK
**Descrição:** Mostra estado da sessão (iterações, tokens, contexto)
```text
__status__
```

## /sudo -- OK
**Descrição:** Controla modo sudo (cache de senha apenas em memória)
```text
  sudo mode: inativo
  senha cacheada: não
  Use /sudo enable para ativar; /sudo disable para limpar.
```

## /summary -- OK
**Descrição:** Gera resumo da sessão
```text
Gere um resumo do trabalho realizado nesta sessão.
Inclua:
1. Ações tomadas (leituras, edições, comandos)
2. Arquivos modificados
3. Decisões-chave
4. Próximos passos sugeridos
Use done(summary='resumo completo em PT-BR')
```

## /tasks -- OK
**Descrição:** Gerencia tarefas
```text
[x] #91df37bc gauntlet test
[ ] #2c88dfbd gauntlet test
[ ] #617a7925 gauntlet test
[ ] #6deeaeae gauntlet test
[ ] #4846e7cf p4 gauntlet task
[ ] #87cc51e8 gauntlet test
[ ] #ae9ba8ce p4 gauntlet task
[ ] #10ff08ae p4 gauntlet task
[ ] #67d4b51e p4 gauntlet task
[ ] #d077ad0d gauntlet test
... (19 linhas omitidas)
```

## /test -- OK
**Descrição:** Gera testes para um arquivo
**Aliases:** /tst
```text
Gere testes para ''. Passos:
1. Use read_file para ler ''
2. Identifique funções/métodos testáveis
3. Use write_file para criar arquivo de teste com:
   - Imports necessários
   - Testes para casos normais e edge cases
4. Use done(summary='lista dos testes criados')
```

## /theme -- OK
**Descrição:** Lista ou troca tema de cores
```text
  Temas disponíveis:
    - eris: Eris — Caos púrpura. Vermelho + rosa sobre fundo profundo.
    - juno: Juno — Verde orgânico + laranja quente. Natureza digital.
    - lars: Lars — Verde matrix + cyan. Terminal clássico.
    - luna: Luna — Dracula Gothic. Roxo profundo + rosa neon.
    - mars: Mars — Vermelho agressivo sobre negro absoluto.
    - nyx: Nyx — Codificadora silenciosa. Cinza cirúrgico + cyan técnico.
    - somn: Somn — Azul profundo noturno. Cyan + roxo sobre escuridão.
```

## /tools -- OK
**Descrição:** Lista ferramentas (tools) disponíveis no agent
```text
  Tools registradas (35):

    agent              -- Executa uma sub-tarefa em um loop isolado com sessão separada. Use par
    analyze            -- Analisa estrutura de um arquivo: imports, classes, funções, linhas, co
    ask_user           -- Faz uma pergunta ao usuário e aguarda resposta. Use quando precisar de
    brief              -- Gera um resumo do contexto atual: modelo, tools, arquivos no contexto,
    config             -- Lê ou escreve configuração do Nyx. Ações: get (lê chave), set (define
    done               -- Sinaliza que a tarefa foi concluída. Use SUMMARY para resumir o que fo
    edit_file          -- Substitui um trecho de texto em um arquivo existente
    enter_plan_mode    -- Entra no modo planejamento. Neste modo, apenas tools de leitura e busc
... (27 linhas omitidas)
```

## /trace -- OK
**Descrição:** Trace de execução do agent loop
```text
__trace__
```

## /tune -- ERR
**Descrição:** Re-calcula num_gpu via VRAM atual (PROXY-NUMGPU-RUNTIME-01)
```text
__error__Proxy não respondeu em /admin/tune: ConnectError.||Verifique se o proxy está rodando com /doctor.
```

## /usage -- OK
**Descrição:** Uso de tokens e contexto
```text
__usage__
```

## /version -- OK
**Descrição:** Mostra versão do Nyx
**Aliases:** /v
```text
  Nyx v1.2.0
  Modelo: qwen2.5-coder:3b
  Proxy: http://127.0.0.1:11436/v1
  Python: 3.12.1
  Local First. Zero Emojis.
```

## /vision -- OK
**Descrição:** Mostra descrição da imagem N (ex.: /vision 1)
```text
Uso: /vision <numero>. Ex.: /vision 1
```
