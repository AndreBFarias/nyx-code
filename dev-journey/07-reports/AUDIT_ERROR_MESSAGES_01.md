# AUDIT_ERROR_MESSAGES_01 -- Inventário de mensagens de erro do REPL

Sprint: ERROR-MSG-01
Data: 2026-04-21
Canal canônico: `nyx.agent.output.print_error(msg, hint, debug_detail)`
Sentinela de dispatcher: `__error__<msg>||<hint>` (consumido por `cli.py`)
Wrapper de provider: `nyx.providers.base.ProviderError(user_message, hint, cause)`

## Regras de formato aplicadas

1. Toda mensagem em PT-BR com acentuação correta (á, é, í, ó, ú, ã, ç, etc).
2. Formato: `[erro] <O QUE falhou>. <VERBO IMPERATIVO: o que fazer>.`
3. Cor vermelha via `ANSI_ERROR_FG` (token canônico de `design_tokens.py`). Hint em `ANSI_DIM`.
4. `NYX_DEBUG=1` habilita `debug_detail` (tipo da exceção + trecho da mensagem original) em dim.
5. Mensagens de biblioteca externa (httpx, urllib3) são envelopadas em `ProviderError` e nunca vazam cruas.
6. Zero emojis, zero menção a IA, zero hex hardcoded.

## Tabela de inventário (antes / depois)

| # | Local | Antes | Depois |
|---|-------|-------|--------|
| 1 | `nyx/providers/ollama.py:56` (TimeoutException) | `last_error = "Timeout"` + `return {"error": f"Falha após N tentativas: Timeout"}` | `raise ProviderError(user_message="Ollama não respondeu em {N}s.", hint="Verifique se está rodando: systemctl status ollama")` |
| 2 | `nyx/providers/ollama.py:58` (ConnectError) | `last_error = "Conexão recusada"` | `raise ProviderError(user_message="Conexão recusada com o proxy em {url}.", hint="Reinicie com ./run.sh ou confira a porta com ss -ltnp \| grep 1143")` |
| 3 | `nyx/providers/ollama.py:46` (resposta sem choices) | `return {"error": f"Resposta sem choices: {str(data)[:200]}"}` | `raise ProviderError(user_message="Resposta do proxy sem campo 'choices'.", hint="Reinicie o proxy com ./run.sh ou inspecione ~/.nyx/logs/proxy.log.")` |
| 4 | `nyx/providers/ollama.py:68` (exception genérica) | `return {"error": f"Falha após N tentativas: {last_error}"}` | `raise ProviderError(user_message="Falha após {N} tentativas de chat com o proxy.", hint="Consulte ~/.nyx/logs/nyx.log para o traceback completo.")` |
| 5 | `nyx/agent/loop/_iteration.py:299` (TimeoutException) | `return {"error": "Timeout ao chamar LLM (proxy não respondeu)"}` | `return {"error": "Proxy de inferência não respondeu em {N}s. Verifique se o Ollama e o proxy estão vivos: systemctl status ollama && ss -ltnp \| grep 1143", "error_detail": ...}` |
| 6 | `nyx/agent/loop/_iteration.py:301` (Exception genérica) | `return {"error": str(e)}` | `return {"error": "Falha inesperada ao contatar o proxy: {TipoDaExcecao}. Abra ~/.nyx/logs/nyx.log para o traceback completo.", "error_detail": f"{type(e).__name__}: {e}"}` |
| 7 | `nyx/agent/loop/_iteration.py` (ConnectError) | (não tratado isoladamente) | `return {"error": "Conexão recusada pelo proxy de inferência. Reinicie o stack com ./run.sh ou confira ~/.nyx/logs/proxy.log.", "error_detail": ...}` |
| 8 | `nyx/agent/loop/_iteration.py` (ProviderError) | (inexistente) | `return {"error": f"{e.user_message} {e.hint}", "error_detail": f"{type(e.cause).__name__}: {e.cause or e}"}` |
| 9 | `nyx/agent/loop/_iteration.py:270` (sem choices) | `return {"error": f"Resposta sem choices: {str(data)[:200]}"}` | `return {"error": "Resposta do proxy sem campo 'choices'. Reinicie o proxy com ./run.sh ou inspecione ~/.nyx/logs/proxy.log.", "error_detail": ...}` |
| 10 | `nyx/agent/commands/_dispatcher.py:19` (comando desconhecido) | `return f"  Comando desconhecido: /{name}. Use /help."` | `return f"__error__Comando desconhecido: /{name}.\|\|Você quis dizer /{sugestao}?"` (via `difflib.get_close_matches(cutoff=0.6, n=1)`) |
| 11 | `nyx/agent/commands/_dispatcher.py` (sem sugestão próxima) | (fallback genérico) | `"__error__Comando desconhecido: /{name}.\|\|Use /help para listar comandos disponíveis."` |
| 12 | `nyx/agent/commands/core.py:65` (`/memory show`) | `return f"Memória '{name}' não existe. Use /memory pra listar."` | `"__error__Memória '{name}' não foi encontrada em {mem.directory}.\|\|Liste as memórias disponíveis com /memory."` |
| 13 | `nyx/agent/commands/core.py:93` (`/recall` sem termo) | `return "uso: /recall <termo>"` | `"__error__Argumento obrigatório ausente em /recall.\|\|Use: /recall <termo> -- busca textual nas memórias do projeto."` |
| 14 | `nyx/agent/commands/core.py:98` (`/recall` sem memórias) | `return "Nenhuma memória gravada para buscar."` | `"__error__Nenhuma memória gravada neste projeto.\|\|Peça à Nyx para lembrar algo estável e rode /recall depois."` |
| 15 | `nyx/agent/commands/core.py:115` (`/recall` sem matches) | `return f"Nenhuma ocorrência de '{termo}' nas memórias."` | `"__error__Nenhuma ocorrência de '{termo}' nas memórias do projeto.\|\|Tente um termo mais curto ou liste as memórias com /memory."` |
| 16 | `nyx/agent/commands/core.py:123` (`/paste` sem pastes/) | `return "Nenhuma imagem colada ainda. Use Ctrl+V com imagem no clipboard."` | `"__error__Nenhuma imagem colada ainda nesta sessão.\|\|Use Ctrl+V com uma imagem no clipboard para colar."` |
| 17 | `nyx/agent/commands/core.py:126` (`/paste` vazio) | `return "Nenhuma imagem em ~/.nyx/pastes/."` | `"__error__Diretório ~/.nyx/pastes/ está vazio.\|\|Cole uma imagem com Ctrl+V antes de usar /paste."` |
| 18 | `nyx/agent/commands/git_cmds.py:36` (`/diff` sem git) | `return "Erro ao obter diff. Verifique se é um repositório git."` | `"__error__Falha ao obter o diff do repositório.\|\|Confirme que está dentro de um repositório git com: git rev-parse --show-toplevel"` |
| 19 | `nyx/agent/commands/git_cmds.py:79` (`/branch --list` falhou) | `return f"Erro: {out}"` | `"__error__Falha ao listar branches.\|\|Detalhe: {out[:120]}"` |
| 20 | `nyx/agent/commands/git_cmds.py:83` (`/branch -d` falhou) | `return f"Erro: {out}"` | `"__error__Falha ao remover a branch '{branch}'.\|\|Detalhe: {out[:120]}"` |
| 21 | `nyx/agent/commands/git_cmds.py:85` (`/branch <nova>` falhou) | `return f"Erro ao criar branch: {out}"` | `"__error__Falha ao criar a branch '{args}'.\|\|Detalhe: {out[:120]}"` |
| 22 | `nyx/agent/commands/git_cmds.py:101` (`/issue <n>` não encontrada) | `return r.stdout if r.stdout else f"Issue #{args} não encontrada."` | `"__error__Issue #{args} não encontrada neste repositório.\|\|Liste issues abertas com /issue (sem argumento)."` |
| 23 | `nyx/agent/commands/git_cmds.py:104` (`gh` ausente em /issue) | `return "gh CLI não instalado. Instale: https://cli.github.com"` | `"__error__gh CLI não está instalado no sistema.\|\|Instale com: sudo apt install gh -- ou veja https://cli.github.com"` |
| 24 | `nyx/agent/commands/git_cmds.py:120` (`/pr <n>` não encontrada) | `return r.stdout if r.stdout else f"PR #{args} não encontrada."` | `"__error__PR #{args} não encontrada neste repositório.\|\|Liste PRs abertas com /pr (sem argumento)."` |
| 25 | `nyx/agent/commands/git_cmds.py:121` (`/pr` argumento inválido) | `return "Uso: /pr [número]"` | `"__error__Argumento inválido para /pr.\|\|Uso correto: /pr [número] -- sem argumento lista as PRs abertas."` |
| 26 | `nyx/agent/commands/git_cmds.py:123` (`gh` ausente em /pr) | `return "gh CLI não instalado. Instale: https://cli.github.com"` | `"__error__gh CLI não está instalado no sistema.\|\|Instale com: sudo apt install gh -- ou veja https://cli.github.com"` |
| 27 | `nyx/agent/commands/git_cmds.py:130` (`/pr-comments` sem arg) | `return "  Uso: /pr-comments <número>"` | `"__error__Argumento inválido para /pr-comments.\|\|Uso correto: /pr-comments <número> -- ex: /pr-comments 123"` |
| 28 | `nyx/agent/commands/git_cmds.py:151` (PR sem comentários) | `return f"  PR #{pr_number}: nenhum comentário."` | `"__error__PR #{pr_number} não possui comentários.\|\|Abra a PR para comentar: gh pr view {pr_number} --web"` |
| 29 | `nyx/agent/commands/git_cmds.py:153` (`gh` ausente em /pr-comments) | `return "  gh CLI não instalado."` | `"__error__gh CLI não está instalado no sistema.\|\|Instale com: sudo apt install gh -- ou veja https://cli.github.com"` |
| 30 | `nyx/agent/commands/system.py:50` (chave env ausente) | `return f"  Chave '{parts[0]}' não definida."` | `"__error__Chave '{parts[0]}' não está definida no ambiente.\|\|Defina com: export {KEY}=<valor> ou use /env para ver as ativas."` |
| 31 | `nyx/agent/commands/system.py:162` (tema inválido) | `return f"  Tema '{args}' não encontrado."` | `"__error__Tema '{args}' não existe no ThemeManager.\|\|Liste os temas disponíveis com /theme list."` |
| 32 | `nyx/agent/commands/system.py:166` (temas indisponíveis) | `return "  Módulo de temas não disponível."` | `"__error__Módulo de temas indisponível: {TipoDoImportError}.\|\|Reinstale dependências com: ./run.sh --install"` |
| 33 | `nyx/agent/commands/system.py:229` (`/add-dir` sem arg) | `return "  Uso: /add-dir <caminho>"` | `"__error__Argumento obrigatório ausente em /add-dir.\|\|Uso correto: /add-dir <caminho relativo ao projeto>."` |
| 34 | `nyx/agent/commands/system.py:232` (`/add-dir` dir inexistente) | `return f"  Diretório '{target}' não encontrado."` | `"__error__Diretório '{target}' não existe em {project_root}.\|\|Confira o caminho com: ls -la ou tab-completion."` |
| 35 | `nyx/agent/commands/session.py:21` (`/session list` sem dir) | `return "  Nenhuma sessão salva."` | `"__error__Diretório de sessões ainda não existe.\|\|Rode /init para criar ~/.nyx/sessions/."` |
| 36 | `nyx/agent/commands/session.py:24` (`/session list` vazia) | `return "  Nenhuma sessão salva."` | `"__error__Nenhuma sessão salva encontrada.\|\|Saia do REPL com /quit para salvar a sessão atual."` |
| 37 | `nyx/agent/commands/session.py:34` (`/session load` vazia) | `return "  Nenhuma sessão para restaurar."` | `"__error__Nenhuma sessão salva para restaurar.\|\|Saia do REPL com /quit para salvar a sessão atual."` |
| 38 | `nyx/agent/commands/session.py:64` (`/replay` sem session_id) | `return "  Uso: /replay <session_id> -- ex: session_Nyx-Code_1776736000"` | `"__error__Argumento obrigatório ausente em /replay.\|\|Uso: /replay <session_id> -- ex: session_Nyx-Code_1776736000"` |
| 39 | `nyx/agent/commands/session.py:115` (`/btw` sem nota) | `return "  Uso: /btw <nota> -- injeta contexto sem gerar resposta"` | `"__error__Argumento obrigatório ausente em /btw.\|\|Uso: /btw <nota> -- injeta contexto sem gerar resposta."` |
| 40 | `nyx/agent/commands/code.py:14` (`/explain` arquivo inexistente) | `return f"Arquivo '{file_path}' não encontrado. Verifique o caminho."` | `"__error__Arquivo '{file_path}' não existe em {project_root}.\|\|Confira o caminho com: ls -la ou tab-completion."` |
| 41 | `nyx/agent/commands/code.py:46` (`/test` arquivo inexistente) | `return f"Arquivo '{file_path}' não encontrado."` | `"__error__Arquivo '{file_path}' não existe em {project_root}.\|\|Confira o caminho com: ls -la ou tab-completion."` |
| 42 | `nyx/agent/commands/_observability.py:66` (`/replay` sem id) | `return "  Uso: /replay <session_id>"` | `"__error__Argumento obrigatório ausente em /replay.\|\|Uso: /replay <session_id>"` |
| 43 | `nyx/agent/commands/_observability.py:75` (sessão não encontrada) | `return f"  Sessão não encontrada: {session_id}"` | `"__error__Sessão '{session_id}' não encontrada em ~/.nyx/sessions/ nem em {project_root}/logs/sessions/.\|\|Liste sessões disponíveis com /session list."` |
| 44 | `nyx/agent/commands/_observability.py:81` (sessão corrompida) | `return f"  Sessão corrompida: {exc}"` | `"__error__Sessão {session_path.name} está corrompida (JSON inválido).\|\|Inspecione o arquivo ou remova com: rm {session_path}"` |
| 45 | `nyx/agent/commands/debug_cmds.py:55` (`/debug` subcomando inválido) | `return "  Uso: /debug session -- métricas estruturadas da sessão corrente"` | `"__error__Subcomando inválido para /debug.\|\|Uso: /debug session -- métricas estruturadas da sessão corrente."` |
| 46 | `nyx/agent/commands/debug_cmds.py:81` (`/tasks` subcomando inválido) | `return "  Uso: /tasks [list\|create <título>\|done <id>]"` | `"__error__Subcomando inválido para /tasks.\|\|Uso: /tasks [list\|create <título>\|done <id>]"` |
| 47 | `nyx/agent/commands/debug_cmds.py:90` (`/skills` vazio) | `return "  Nenhum skill em ~/.nyx/skills/. Crie arquivos .py com função execute()."` | `"__error__Nenhum skill registrado em ~/.nyx/skills/.\|\|Crie arquivos .py com função execute() para disponibilizar skills."` |
| 48 | `nyx/cli.py:439` (sessão falhou salvar) | `print(f"  {DIM}Falha ao salvar sessão.{NC}")` | `_print_error("Falha ao salvar a sessão atual.", hint="Verifique permissões de escrita em ~/.nyx/sessions/.")` |
| 49 | `nyx/cli.py:450` (sessão restaurar vazia) | `print(f"  {DIM}Nenhuma sessão para restaurar.{NC}")` | `_print_error("Nenhuma sessão salva para restaurar.", hint="Use /quit para salvar esta sessão e rode novamente para carregá-la.")` |
| 50 | `nyx/cli.py:495` (contexto /files vazio) | `print(f"  {ctx}" if ctx else "  Nenhum arquivo no contexto.")` | `_print_error("Nenhum arquivo no contexto da sessão.", hint="Peça a Nyx para ler um arquivo ou use /read <caminho>.")` |
| 51 | `nyx/cli.py:510` (/trace vazia) | `print(f"  {DIM}Nenhuma tool call na sessão.{NC}")` | `_print_error("Nenhuma tool call registrada nesta sessão.", hint="Faça uma pergunta à Nyx para gerar atividade antes de inspecionar /trace.")` |
| 52 | `nyx/cli.py:555` (xclip ausente) | `print(f"  {DIM}xclip indisponível. Salvo em {tmp}{NC}")` | `_print_error("xclip indisponível no sistema.", hint=f"Conteúdo salvo em {tmp}. Instale com: sudo apt install xclip", debug_detail=str(exc))` |
| 53 | `nyx/cli.py:557` (sem output para copiar) | `print(f"  {DIM}Nenhum output para copiar.{NC}")` | `_print_error("Nenhum output disponível para copiar.", hint="Aguarde uma resposta da Nyx ou execute um comando antes de /copy.")` |
| 54 | `nyx/cli.py:607` (iteração estado ERROR) | `print(f"  {DIM}[{state_label}]{NC})` para qualquer estado !=DONE | `_print_error(f"Iteração encerrou em estado '{state_label}'.", hint="Consulte ~/.nyx/logs/nyx.log para o traceback completo.")` (apenas quando `state_label == "error"`) |
| 55 | `nyx/cli.py` (dispatcher sentinela `__error__`) | handler ausente | Novo: decompõe `__error__<msg>\|\|<hint>` e chama `_print_error(msg, hint=hint)` |
| 56 | `nyx/agent/output.py` (helper novo) | (ausente) | `print_error(msg, hint=None, debug_detail=None)` -- usa `ANSI_ERROR_FG`/`ANSI_DIM`/`ANSI_RESET` do `design_tokens.py`; `debug_detail` só renderiza com `NYX_DEBUG=1` |
| 57 | `nyx/providers/base.py` (exceção nova) | (arquivo ausente) | `ProviderError(user_message, hint, cause)` -- wrapper canônico para httpx/urllib3/etc |

## Comportamento de difflib

`nyx/agent/commands/_dispatcher.py::_format_unknown_command` usa
`difflib.get_close_matches(name, names, n=1, cutoff=0.6)`:

- `/helpp` → sugere `/help` (distância 1 char, score alto).
- `/memeory` → sugere `/memory`.
- `/xyz` → sem match próximo (score < 0.6); hint genérico aponta para `/help`.

## Modo DEBUG

Variável `NYX_DEBUG=1` (opt-in, default off). Quando ativa, `print_error`
imprime linha adicional com `  detalhe: <tipo>: <mensagem>`. Usada apenas em
troubleshooting -- não deve permanecer ligada em uso normal.

## Invariantes verificadas

- Zero emoji nas mensagens novas. Conferido por varredura manual.
- Zero menção a IA / nomes de modelos. Conferido.
- Acentuação PT-BR correta em `função`, `sessão`, `permissão`, `não`, `está`, `já`, `memória`, `inválido`, etc.
- Cor vermelha aplicada via `ANSI_ERROR_FG` (token canônico) -- nenhum `\033[31m` ou `#FF*` hardcoded introduzido.
- `print()` fora de `cli.py`/`output.py` permanece proibido (ADR-024). Sentinela `__error__` atravessa o dispatcher em string, cli.py é quem chama `print_error`.
- `scripts/audit_error_messages.py` exit 0 + 56 ocorrências canônicas (floor do spec: 40).

## Simulações de cenário manual

### Cenário 1 -- comando inválido com match próximo

```
nyx> /helpp
  [erro] Comando desconhecido: /helpp. Você quis dizer /help?
```

(linha em vermelho via ANSI_ERROR_FG, hint em ANSI_DIM)

### Cenário 2 -- comando inválido sem match

```
nyx> /xyz
  [erro] Comando desconhecido: /xyz. Use /help para listar comandos disponíveis.
```

### Cenário 3 -- Ollama desligado (proxy timeout)

Output quando o LLM não responde:

```
  [erro] Proxy de inferência não respondeu em 90s. Verifique se o Ollama e o proxy estão vivos: systemctl status ollama && ss -ltnp | grep 1143
```

### Cenário 4 -- NYX_DEBUG=1

```
NYX_DEBUG=1 nyx
nyx> (simular proxy down)
  [erro] Proxy de inferência não respondeu em 90s. Verifique se o Ollama e o proxy estão vivos...
  detalhe: TimeoutException: timed out
```

## Riscos assumidos

| Risco | Mitigação |
|-------|-----------|
| Lib externa (httpx/anyio) emite warning em stderr | Logging rotacionado captura; UX do usuário vê apenas `print_error` |
| Usuário confunde "__error__" como string visível | Sentinela sempre consumida pelo cli.py antes de qualquer render |
| `difflib.get_close_matches` sugere comando elevado a usuário sem permissão | Filtro por permissão pode ser adicionado em INFRA subsequente; por ora sugere qualquer comando registrado |

## Próximos passos (opt-in, não bloqueadores)

- INFRA-AUDIT-NEXT: adicionar `audit_error_messages.py` como check #14 em `sprint_invariants.sh`.
- UX-DEBUG-01: expor `NYX_DEBUG` via `/debug on/off` no REPL.

---

*"A palavra precisa corresponde ao fato preciso." -- Sêneca*
