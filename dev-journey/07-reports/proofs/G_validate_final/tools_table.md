# Total tools registradas: 35

## read_file -- OK
**Descrição:** Lê o conteúdo de um arquivo
**Args:** `{"file_path": "VALIDATOR_BRIEF.md"}`
```text
"ActionResult(success=True, output='   1\\t# VALIDATOR_BRIEF — Nyx-Code\\n   2\\t\\n   3\\tContratos de runtime para validação de sprints. Bootstrap mínimo gerado em 2026-05-16.\\n   4\\t\\n   5\\t## [CORE] Contratos de runtime\\n   6\\t\\n   7\\tComandos canônicos de proof-of-work:\\n   8\\t\\n   9\\t- Smoke boot: `./run.sh --smoke` — deve imprimir `boot ok` e exit 0.\\n  10\\t- Invariantes: `bash scripts/sprint_invariants.sh` — PASS 13/13, FAIL 0.\\n  11\\t- Gauntlet rápido: `./run.sh --gauntlet --only rapido` — 100%.\\n  12\\t- Gauntlet proxy: `./run.sh --gauntlet --only proxy` — 100%.\\n  13\\t- Perf baseline: `./venv/bin/python scripts/gauntlet/fixtures/perf_inference.py --baseline`.\\n  14\\t\\n  15\\t## [CORE] Checks universais ativados\\n  16\\t\\n  17\\t1. Smoke boot obrigatório antes de marcar CONCLUIDA (memória `feedback_smoke_boot.md`).\\n  18\\t2. Sem emojis em código, commits, docs.\\n  19\\t3. Sem menção a IA externa (Claude/Anthropic/GPT/Gemini/Copilot) em `.py`.\\n  20\\t4. Acentuação correta em PT-BR (validador `~/.config/zsh/scripts/validar-acentuacao.py`).\\n  21\\t5. Cleanup explícito após teste com modelo: `pkill -f \"nyx/proxy.py\"`, `pkill -f \"ollama serve\"`, `nvidia-smi` confirmando VRAM livre.\\n  22\\t6. Nenhum débito implícito; achado colateral vira sprint nova com ID no `SPRINT_ORDER_MASTER`.\\n  23\\t\\n  24\\t## [CORE] Arquivos periféricos\\n  25\\t\\n  26\\t- `dev-journey/06-sprints/producao/SPRINT_*.md` — specs em vigor.\\n  27\\t- `dev-jour
```

## write_file -- OK
**Descrição:** Cria ou sobrescreve um arquivo com o conteúdo fornecido
**Args:** `{"file_path": "/tmp/nyx_validate_final_write_test.txt", "content": "ping"}`
```text
"ActionResult(success=False, output='', error=\"Fora dos projetos permitidos: '/tmp/nyx_validate_final_write_test.txt'. Para autorizar: /sandbox add /tmp\", files_read=[], files_modified=[])"
```

## edit_file -- OK
**Descrição:** Substitui um trecho de texto em um arquivo existente
**Args:** `{"file_path": "/tmp/nyx_validate_final_write_test.txt", "old_string": "ping", "new_string": "pong"}`
```text
"ActionResult(success=False, output='', error=\"Fora dos projetos permitidos: '/tmp/nyx_validate_final_write_test.txt'. Para autorizar: /sandbox add /tmp\", files_read=[], files_modified=[])"
```

## run_command -- OK
**Descrição:** Executa um comando no terminal (bash)
**Args:** `{"command": "echo nyx-validate"}`
```text
"ActionResult(success=True, output='nyx-validate\\n Se a tarefa está completa, chame done().', error='', files_read=[], files_modified=[])"
```

## glob -- OK
**Descrição:** Busca arquivos por padrão glob (ex: **/*.py, src/**/*.ts)
**Args:** `{"pattern": "*.md"}`
```text
"ActionResult(success=True, output='CHANGELOG.md\\nCODE_OF_CONDUCT.md\\nCONTRIBUTING.md\\nCheckpoint.md\\nEXECUTAR_SPRINT.md\\nGAUNTLET_REPORT.md\\nGSD.md\\nPROMPT_VALIDADOR_INTEGRADOR.md\\nREADME.md\\nSECURITY.md\\nVALIDATOR_BRIEF.md\\n[Analise e execute a próxima ação.]', error='', files_read=[], files_modified=[])"
```

## search -- OK
**Descrição:** Busca texto (regex) em arquivos do projeto (grep)
**Args:** `{"pattern": "validate", "path": "VALIDATOR_BRIEF.md"}`
```text
"ActionResult(success=True, output='Nenhum resultado para: validate', error='', files_read=[], files_modified=[])"
```

## list_files -- OK
**Descrição:** Lista arquivos e diretórios de um caminho
**Args:** `{"path": "dev-journey/07-reports"}`
```text
"ActionResult(success=True, output='d dev-journey/07-reports/checkpoints_historicos\\nd dev-journey/07-reports/evidencia\\nd dev-journey/07-reports/gauntlet\\nd dev-journey/07-reports/proofs\\nf dev-journey/07-reports/AUDIT_ERROR_MESSAGES_01.md\\nf dev-journey/07-reports/AUDIT_EXT_2026_04_18.md\\nf dev-journey/07-reports/CHECKLIST_PARIDADE_CLAUDE_CODE.md\\nf dev-journey/07-reports/DIAG_RACE_INPUT.md\\nf dev-journey/07-reports/RELATORIO_BLOCO_2_2026_04_18.md\\nf dev-journey/07-reports/RELATORIO_INFRA_RESILIENTE_MODELO_01.md\\nf dev-journey/07-reports/RELATORIO_ONDA_20.md\\nf dev-journey/07-reports/RELATORIO_ONDA_21.md\\nf dev-journey/07-reports/RELATORIO_VALIDACAO_ONDA_20.md\\nf dev-journey/07-reports/RELATORIO_VALIDACAO_ONDA_21.md\\nf dev-journey/07-reports/RELATORIO_VALIDATE_FINAL_01.md\\nf dev-journey/07-reports/SESSAO_2026_05_17.md\\nf dev-journey/07-reports/SESSAO_2026_05_18_LOG.md\\nf dev-journey/07-reports/SHOWCASE_AESTHETICS_GALLERY.md\\n[Analise e execute a próxima ação.]', error='', files_read=[], files_modified=[])"
```

## notebook_edit -- OK
**Descrição:** Edita células de um Jupyter notebook (.ipynb). Modos: replace (substitui célula), insert (insere após célula), delete (remove célula). Identifica células pelo índice (0-based).
**Args:** `{"notebook_path": "/tmp/inexistente.ipynb", "cell_index": 0, "new_source": "y"}`
```text
"ActionResult(success=False, output='', error=\"Fora dos projetos permitidos: '/tmp/inexistente.ipynb'. Para autorizar: /sandbox add /tmp\", files_read=[], files_modified=[])"
```

## todo_write -- OK
**Descrição:** Gerencia a lista de tarefas da sessão. Cada item tem: content (descrição), status (pending/in_progress/completed). Envie a lista completa atualizada a cada chamada.
**Args:** `{"todos": [{"content": "x", "status": "pending", "activeForm": "x"}]}`
```text
"ActionResult(success=True, output='Tarefas atualizadas: 1 total (1 pendentes, 0 em progresso, 0 concluídas)', error='', files_read=[], files_modified=[])"
```

## web_fetch -- OK
**Descrição:** Busca conteúdo de uma URL e retorna como texto/markdown. Funciona com páginas HTML, APIs JSON e texto puro. Não funciona com URLs autenticadas ou conteúdo binário pesado.
**Args:** `{"url": "http://127.0.0.1:1/invalido", "prompt": "extract"}`
```text
"ActionResult(success=False, output='', error='Conexão recusada: http://127.0.0.1:1/invalido', files_read=[], files_modified=[])"
```

## web_search -- OK
**Descrição:** Busca na web usando DuckDuckGo e Wikipedia. Retorna títulos, URLs e trechos dos resultados. Use para buscar informações atuais, documentação, ou qualquer dado que não esteja no projeto local.
**Args:** `{"query": "nyx-validate-test"}`
```text
"ActionResult(success=True, output='[Busca web - 19/05/2026 03:37]\\n\\n1. Simplified: How to setup Nyx Validator | by Lee King | Medium\\n   October 11, 2023 -In the file $HOME/nyxd/config/app.toml, set the following values: # Mainnet minimum-gas-prices = \"0.025unym,0.025unyx\" enable = true in the `[api]` section to get the API server running · # Sandbox Testnet minimum-gas-prices = \"0.025unymt,0.025unyxt\" enable = true` in the `[api]` s\\n   https://medium.com/@kingwillie418/simplified-how-to-setup-nyx-validator-fc4ce9aa0d18\\n\\n2. Nyx Validator REST API - Cosmos SDK Endpoints | Nym Docs\\n   Reference for theNyxValidatorREST API, providing Cosmos SDK endpoints for account balances, staking, governance, and CosmWasm smart contract queries.\\n   https://nym.com/docs/apis/cosmos-sdk-nyx\\n\\n3. ComfyUI-KNXEcosystem/tests-unit/execution_test/validate_node ...\\n   The most powerful and modular diffusion model GUI, api and backend with a graph/nodes interface. Forked to use within the KtiseosNyxTrainer/AI Ecosystem - ComfyUI-KNXEcosystem/tests-unit/execution_test/validate_node_input_test.py at master · Ktiseos-Nyx/ComfyUI-KNXEcosystem\\n   https://github.com/Ktiseos-Nyx/ComfyUI-KNXEcosystem/blob/master/tests-unit/execution_test/validate_node_input_test.py\\n\\n4. Validation - Nyx Space\\n   This comprehensive workflow involves running parallel queries in both ANISE and SPICE (in single-threadedtestmode using the rust-spice crate by Grégoire Henry) for precise comparison.\\
```

## task_create -- OK
**Descrição:** Cria uma nova tarefa no sistema de tarefas. Retorna o ID da tarefa criada.
**Args:** `{"subject": "ping", "description": "validate"}`
```text
"ActionResult(success=True, output='Task #d7565852 criada: ping', error='', files_read=[], files_modified=[])"
```

## task_update -- OK
**Descrição:** Atualiza status de uma tarefa existente. Status: pending, in_progress, completed.
**Args:** `{"task_id": "inexistente", "status": "in_progress"}`
```text
"ActionResult(success=False, output='', error='Task #inexistente não encontrada', files_read=[], files_modified=[])"
```

## task_list -- OK
**Descrição:** Lista todas as tarefas com seus status.
**Args:** `{}`
```text
"ActionResult(success=True, output='[x] #91df37bc gauntlet test\\n[ ] #2c88dfbd gauntlet test\\n[ ] #617a7925 gauntlet test\\n[ ] #6deeaeae gauntlet test\\n[ ] #4846e7cf p4 gauntlet task\\n[ ] #87cc51e8 gauntlet test\\n[ ] #ae9ba8ce p4 gauntlet task\\n[ ] #10ff08ae p4 gauntlet task\\n[ ] #67d4b51e p4 gauntlet task\\n[ ] #d077ad0d gauntlet test\\n[ ] #c8736cbe p4 gauntlet task\\n[ ] #be7bd69d gauntlet test\\n[ ] #2eab5f58 p4 gauntlet task\\n[ ] #a33426d7 gauntlet test\\n[ ] #3d29de93 p4 gauntlet task\\n[ ] #f92fc940 gauntlet test\\n[ ] #404f273d p4 gauntlet task\\n[ ] #07b7cebb gauntlet test\\n[ ] #96cad83b p4 gauntlet task\\n[ ] #c87daf7e gauntlet test\\n[ ] #5b36b82c p4 gauntlet task\\n[ ] #703bf209 gauntlet test\\n[ ] #15706864 p4 gauntlet task\\n[ ] #d95c7f08 gauntlet test\\n[ ] #575e991b p4 gauntlet task\\n[ ] #61421479 gauntlet test\\n[ ] #002cf0f3 p4 gauntlet task\\n[ ] #d7565852 ping\\n\\nTotal: 28 (16 pendentes, 0 em progresso, 1 concluídas)', error='', files_read=[], files_modified=[])"
```

## task_get -- OK
**Descrição:** Retorna detalhes de uma tarefa específica por ID.
**Args:** `{"task_id": "inexistente"}`
```text
"ActionResult(success=False, output='', error='Task #inexistente não encontrada', files_read=[], files_modified=[])"
```

## task_output -- OK
**Descrição:** Retorna o output/log de uma tarefa específica.
**Args:** `{"task_id": "inexistente"}`
```text
"ActionResult(success=False, output='', error='Task #inexistente não encontrada', files_read=[], files_modified=[])"
```

## task_stop -- OK
**Descrição:** Cancela uma tarefa em execução. Muda status para 'cancelled'.
**Args:** `{"task_id": "inexistente"}`
```text
"ActionResult(success=False, output='', error='Task #inexistente não encontrada', files_read=[], files_modified=[])"
```

## enter_plan_mode -- OK
**Descrição:** Entra no modo planejamento. Neste modo, apenas tools de leitura e busca são permitidas. Use para explorar o código antes de implementar. Chame exit_plan_mode quando estiver pronto para executar.
**Args:** `{}`
```text
"ActionResult(success=True, output='Modo planejamento ativo. Regras:\\n1. Explore o código com read_file, search, glob, list_files\\n2. Identifique padrões e dependências\\n3. Planeje a implementação\\n4. Use exit_plan_mode quando estiver pronto para executar\\n\\nTools bloqueadas: write_file, edit_file, run_command', error='', files_read=[], files_modified=[])"
```

## exit_plan_mode -- OK
**Descrição:** Sai do modo planejamento e volta ao modo normal. Todas as tools ficam disponíveis novamente.
**Args:** `{"plan_summary": "validate-final-01"}`
```text
"ActionResult(success=True, output='Modo planejamento desativado. Todas as tools disponíveis.\\n\\nPlano:\\nvalidate-final-01', error='', files_read=[], files_modified=[])"
```

## ask_user -- OK
**Descrição:** Faz uma pergunta ao usuário e aguarda resposta. Use quando precisar de decisão do usuário sobre abordagem, trade-offs ou confirmação. Pode incluir opções formatadas.
**Args:** `{"question": "ping?"}`
```text
"ActionResult(success=True, output='{\"kind\": \"question\", \"question\": \"ping?\", \"options\": []}', error='', files_read=[], files_modified=[])"
```

## agent -- OK
**Descrição:** Executa uma sub-tarefa em um loop isolado com sessão separada. Use para tarefas que exigem múltiplas iterações de leitura/análise sem poluir o contexto da conversa principal. O sub-agente tem acesso às mesmas tools mas sessão independente.
**Args:** `{"prompt": "echo"}`
```text
"ActionResult(success=True, output='[sub-agente] error em 1 iterações\\nLidos: 0 | Modificados: 0\\nResultado: VRAM insuficiente (19 MiB livres). Feche outros processos GPU ou rode em CPU com NYX_NUM_GPU=0.', error='', files_read=[], files_modified=[])"
```

## sleep -- OK
**Descrição:** Espera um número de segundos antes de continuar. Máximo 30s.
**Args:** `{"seconds": 0.01}`
```text
"ActionResult(success=True, output='Esperou 1s (real: 1.0s)', error='', files_read=[], files_modified=[])"
```

## config -- OK
**Descrição:** Lê ou escreve configuração do Nyx. Ações: get (lê chave), set (define chave=valor), list (mostra tudo).
**Args:** `{"action": "get", "key": "model"}`
```text
"ActionResult(success=True, output=\"Chave 'model' não definida.\", error='', files_read=[], files_modified=[])"
```

## brief -- OK
**Descrição:** Gera um resumo do contexto atual: modelo, tools, arquivos no contexto, iterações e budget.
**Args:** `{}`
```text
"ActionResult(success=True, output='Resumo do contexto Nyx:\\n  Projeto: /home/andrefarias/Desenvolvimento/Nyx-Code\\n  Tools: 35 registradas\\n  Lista: agent, analyze, ask_user, brief, config, done, edit_file, enter_plan_mode, enter_worktree, exit_plan_mode, exit_worktree, glob, list_files, multi_edit, notebook_edit...', error='', files_read=[], files_modified=[])"
```

## enter_worktree -- OK
**Descrição:** Cria um git worktree isolado para trabalhar em mudanças sem afetar a árvore principal.
**Args:** `{"branch_name": "validate-final-test"}`
```text
"ActionResult(success=True, output='Worktree criado: /tmp/nyx-wt-1779172669\\nBranch: validate-final-test', error='', files_read=[], files_modified=[])"
```

## exit_worktree -- OK
**Descrição:** Remove o git worktree ativo e limpa a branch temporária. Se houver mudanças, retorna o diff.
**Args:** `{}`
```text
"ActionResult(success=True, output='Worktree removido: /tmp/nyx-wt-1779172669\\nBranch validate-final-test removida (sem mudanças)', error='', files_read=[], files_modified=[])"
```

## repl -- OK
**Descrição:** Executa código Python e retorna o output. Útil para cálculos, testes rápidos e exploração.
**Args:** `{"code": "print(1+1)"}`
```text
"ActionResult(success=True, output='2\\n', error='', files_read=[], files_modified=[])"
```

## tool_search -- OK
**Descrição:** Busca tools disponíveis por nome ou descrição. Retorna lista de matches com nome e descrição.
**Args:** `{"query": "edit"}`
```text
"ActionResult(success=True, output=\"Resultados para 'edit' (3 encontradas):\\n  - edit_file: Substitui um trecho de texto em um arquivo existente\\n  - notebook_edit: Edita células de um Jupyter notebook (.ipynb). Modos: replace (substitui célula), insert (insere apó\\n  - multi_edit: Aplica múltiplas edições atomicamente. Se uma falhar, reverte todas as anteriores.\", error='', files_read=[], files_modified=[])"
```

## skill -- OK
**Descrição:** Invoca um skill local definido em ~/.nyx/skills/. Cada skill é um módulo Python com função execute(args, project_root).
**Args:** `{"skill_name": "validacao-visual"}`
```text
"ActionResult(success=False, output='', error=\"Skill 'validacao-visual' não encontrado. Disponíveis: nenhum\", files_read=[], files_modified=[])"
```

## send_message -- OK
**Descrição:** Envia mensagem para um sub-agent Nyx via protocolo headless. O sub-agent processa e retorna a resposta.
**Args:** `{"content": "ping"}`
```text
"ActionResult(success=True, output='[sub-agent] VRAM insuficiente (19 MiB livres). Feche outros processos GPU ou rode em CPU com NYX_NUM_GPU=0. (1 iterações)', error='', files_read=[], files_modified=[])"
```

## analyze -- OK
**Descrição:** Analisa estrutura de um arquivo: imports, classes, funções, linhas, complexidade. Suporta Python via AST.
**Args:** `{"file_path": "VALIDATOR_BRIEF.md"}`
```text
"ActionResult(success=True, output='Análise de VALIDATOR_BRIEF.md (.md):\\n  Linhas: 45 (17 vazias)\\n  Funções encontradas: 0\\n  Classes/structs: 0', error='', files_read=['/home/andrefarias/Desenvolvimento/Nyx-Code/VALIDATOR_BRIEF.md'], files_modified=[])"
```

## patch -- OK
**Descrição:** Aplica um patch em formato unified diff a um arquivo. O patch deve ter linhas começando com +, -, ou espaço.
**Args:** `{"file_path": "/tmp/x.txt", "patch": "diff --git a/x b/x"}`
```text
"ActionResult(success=False, output='', error=\"Fora dos projetos permitidos: '/tmp/x.txt'. Para autorizar: /sandbox add /tmp\", files_read=[], files_modified=[])"
```

## multi_edit -- OK
**Descrição:** Aplica múltiplas edições atomicamente. Se uma falhar, reverte todas as anteriores.
**Args:** `{"edits": [{"file_path": "/tmp/x.txt", "old_string": "a", "new_string": "b"}]}`
```text
"ActionResult(success=False, output='', error=\"Revertido: Fora dos projetos permitidos: '/tmp/x.txt'. Para autorizar: /sandbox add /tmp\", files_read=[], files_modified=[])"
```

## write_memory -- OK
**Descrição:** Grava memória persistente sobre o projeto ou o desenvolvedor. USE SEMPRE que o usuário disser em tom imperativo: 'lembra que ...', 'anota que ...', 'guarda essa decisão ...', 'memoriza ...', 'fixa ...'. Armazena em ~/.nyx/memory/<projeto>/. Só para fatos que continuam válidos entre sessões (convenções, preferências, decisões estáveis).
**Args:** `{"file": "/tmp/nyx_validate_final_mem.md", "content": "ping", "reason": "validate-final-01-parte-2"}`
```text
"ActionResult(success=True, output='OK: Memória gravada em /home/andrefarias/.nyx/memory/Nyx-Code-387b2a37/nyx_validate_final_mem.md (4 bytes).', error='', files_read=[], files_modified=['/home/andrefarias/.nyx/memory/Nyx-Code-387b2a37/nyx_validate_final_mem.md'])"
```

## done -- OK
**Descrição:** Sinaliza que a tarefa foi concluída. Use SUMMARY para resumir o que foi feito.
**Args:** `{"summary": "validate-final-01-parte-2 dry"}`
```text
"ActionResult(success=True, output='validate-final-01-parte-2 dry', error='', files_read=[], files_modified=[])"
```
