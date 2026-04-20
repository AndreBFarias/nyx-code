# Catálogo de Gambiarras por Sprint — Onda 22

**Uso:** antes de executar qualquer sprint, a IA executora **deve** ler:
1. Seção §"Catálogo Universal (20 padrões)" abaixo.
2. Seção específica da sprint (mais abaixo, por ID).

Este é o documento canônico de gambiarras. `SPRINT_TEMPLATE_V2.md` referencia esta fonte única (não duplica).

---

## Catálogo Universal (20 padrões)

Toda sprint é vulnerável a pelo menos um destes. A IA executora que fizer qualquer deles está em **violação grave** e será auditada pelo reviewer (`REVIEWER_PROTOCOL.md`).

### Burlas estruturais

1. **Rename em vez de delete.** Renomear `compact.py` para `_compact.py`, `compact_old.py`, `_compact_DEPRECATED.py`. **Regra:** quando a sprint pede remoção, o arquivo **deixa de existir** no filesystem.
2. **Stub como implementação.** Criar função que retorna `""`, `None`, `True`, `[]` fixo. **Regra:** função deve produzir output **diferente** para inputs diferentes.
3. **Copy-paste sem adaptação.** Colar código de outros repos sem ajustar paths/imports. **Regra:** grep por strings típicas de fonte externa deve retornar 0 no código Nyx.
4. **Documentação como implementação.** Escrever docstring dizendo o que a função "deveria fazer" sem implementar. **Regra:** chamada real deve produzir efeito observável (print, write, HTTP, mutação de estado).
5. **Arquivo único gigante no lugar do split.** Pedir "dividir em 8 módulos", IA cria `commands/everything.py` com 900 linhas. **Regra:** `find ... -exec wc -l ... '$1 > 300' | head` = vazio.

### Burlas de testes

6. **Modificar teste em vez de corrigir código.** Assertion falha → IA troca `assert x == 5` por `assert x >= 0`. **Regra:** comparar diff do teste **antes/depois**; alteração de assert é suspeita e precisa justificativa explícita.
7. **Test só passa com fixture fake.** Pré-popular cache, mock de HTTP, input hardcoded do que deveria ser dinâmico. **Regra:** teste precisa rodar contra **infra real** (ADR-010 Zero Mocks).
8. **Grep que não detecta o bug.** `grep "success" output.log` passa mesmo com falha real. **Regra:** verificação precisa **fail** quando o código não funciona, **pass** quando funciona. Escrever ambos os casos: o caminho positivo e o negativo.
9. **Condicional de skip.** `if os.environ.get("CI"): return True`. **Regra:** proibido adicionar `SKIP_*` env vars novos sem ADR explícita.
10. **Benchmark sem cronômetro.** Medir performance com `print("rápido")` sem `time.monotonic()`. **Regra:** número em ms/s real no output da verificação.

### Burlas de linter / type check

11. **`# noqa` indiscriminado.** Adicionar `# noqa` ou `# type: ignore` em vez de corrigir. **Regra:** cada `noqa` precisa especificar regra (`# noqa: E402`) e motivo em comentário adjacente.
12. **Remover arquivo que a regra checa.** Deletar `commands.py` para passar `grep "print(" commands.py`. **Regra:** verificação global (grep no repo inteiro), não no arquivo tocado.
13. **Desabilitar regra no pyproject.** Editar `select = [...]` removendo a letra que reclama. **Regra:** mudança em `pyproject.toml` só com ADR.

### Burlas de git / commit

14. **Commit message mentindo.** "feat: implementa X" mas só adicionou TODO. **Regra:** `git show --stat` precisa ter linhas líquidas compatíveis com o escopo (mínimo ~20 linhas novas para feature, ~5 para fix trivial).
15. **Amend para esconder retrabalho.** Sprint "concluída" em 3 commits viram 1 via amend. **Regra:** commits atômicos preservados; se amend acontecer, justificar.
16. **Squash que apaga reverts.** Esconder que algo foi revertido e reaplicado. **Regra:** nunca `git rebase -i` em histórico público.

### Burlas semânticas

17. **Silent except.** `except Exception: pass`. **Regra:** todo `except` precisa de `logger.warning/error` OU `raise`.
18. **Sleep como fix.** `time.sleep(1)` para "resolver" race condition. **Regra:** sprints que envolvem concorrência precisam mostrar que removeram sleeps prévios e não adicionaram novos.
19. **Feature flag falsa.** Esconder código incompleto atrás de `if FEATURE_X: ...` que nunca é True. **Regra:** novos flags precisam de teste que ativa True E False; se só testa False, não está implementado.
20. **Checkpoint marcado sem verificar.** `- [x] critério X` sem rodar o comando de verificação. **Regra:** IA executora **deve colar o output** do comando de verificação junto do checkbox marcado.

---

---

## Protocolo obrigatório de cada sprint

```bash
# PASSO 1 - snapshot antes
bash scripts/sprint_invariants.sh > /tmp/inv_before.txt 2>&1
grep -c "^\[FAIL\]" /tmp/inv_before.txt   # N fails inicial

# PASSO 2 - implementação (seguindo o arquivo SPRINT_<ID>.md)

# PASSO 3 - snapshot depois
bash scripts/sprint_invariants.sh > /tmp/inv_after.txt 2>&1
grep -c "^\[FAIL\]" /tmp/inv_after.txt   # N fails final

# PASSO 4 - diff
diff /tmp/inv_before.txt /tmp/inv_after.txt
```

**Regras:**
1. **Nenhuma sprint pode INTRODUZIR novos FAILs** (N_final > N_inicial = bloqueio).
2. Sprint que promete **fechar** um invariante específico **deve** reduzir o FAIL correspondente (ver coluna "Fecha invariantes" abaixo).
3. O output do PASSO 4 deve ser colado no relatório de conclusão.

---

## Matriz sprint × invariantes fechados

| Sprint | Invariantes que ESTA sprint fecha |
|--------|-----------------------------------|
| AUDIT-EXT-01 | (só leitura, zero) |
| AUDIT-FIX-01 | — (remove código morto) |
| AUDIT-FIX-02 | — (conecta settings) |
| AUDIT-FIX-03 | **#5** portas em múltiplos arquivos |
| AUDIT-FIX-04 | **#4** except silencioso (parcial, cli.py) |
| AUDIT-FIX-05 | **#7** arquivo > 800 linhas (commands.py) |
| AUDIT-FIX-06 | — (ADR docs) |
| AUDIT-FIX-07 | **#3** print em tool; **#4** except silencioso (ask_user.py) |
| AUDIT-FIX-08 | **#2** "Claude Code" docstring em output.py |
| AUDIT-FIX-09 | **#4** except silencioso (memory.py, output.py, project.py) — fecha completamente |
| DEBT-01 | — (loop.py já < 800) |
| DEBT-02 | — (interface/ vazio, removido) |
| DEBT-03 | — (logging unificação) |
| DEBT-04 | **#10** ruff (F841 em analyze_tool/todo_write, F401 em web_search) |
| DEBT-05 | — (pre-commit hook, cosmético) |
| ADR-021-DOC | — (docs, zero código) |
| ADR-022-DOC | — (docs, zero código) |
| INFRA-GAUNTLET-01 | — (valida todos; refresca baseline) |
| VALIDATE-ONDA-20 | preservar; valida 7 sprints em limbo |
| VALIDATE-ONDA-21 | preservar; valida 7 sprints em limbo |
| UX-DESIGN-01 | **#1** emoji ⚡; **#6** hex hardcoded |
| UX-LAYOUT-01/02/03 | preservar todos; não reintroduzir |
| UX-BUG-01/02/03 | preservar; não adicionar sleep (#18 do catálogo geral) |
| VISION-01/02/03 | preservar |
| DEPLOY-01/02 | preservar |
| UX-EXTRA-01 | preservar |

**FAILs remanescentes após Onda 22 = 0.** Se alguma sprint não zera o que deveria, a Onda não está concluída.

---

## Gambiarras específicas por sprint

### AUDIT-FIX-01 (remover compact.py)

- **Rename em vez de delete:** criar `compact_old.py`, `_compact.py`, `compact.py.bak`.
  - **Detectar:** `find nyx -name "compact*" -not -path "*pycache*"` deve retornar vazio.
- **Mover funcionalidade sem deletar original:** duplica código.
  - **Detectar:** garantir que `AutoCompactService` não aparece em grep global.

### AUDIT-FIX-02 (NyxSettings wiring)

- **Import sem uso:** IA adiciona `from nyx.config.settings import load_settings` mas nunca chama.
  - **Detectar:** `grep -c "load_settings()" nyx/cli.py nyx/agent/loop.py` deve ser >= 2.
- **Duplicata viva:** cria `settings = load_settings()` mas mantém `os.environ.get("NYX_OLLAMA_PORT", ...)` ao lado.
  - **Detectar:** após mudança, nenhum `os.environ.get("NYX_OLLAMA_PORT"` deve existir em cli/loop/commands — só em `settings.py`.
- **Prop errada:** `settings.proxy_port` retorna `None` por esquecer do `load_settings()`.
  - **Detectar:** `python -c "from nyx.config.settings import load_settings; assert load_settings().proxy_port == 11436"`.

### AUDIT-FIX-03 (centralizar portas) — JÁ CONCLUÍDO no commit 46f9ab0

Invariante #5 do `sprint_invariants.sh` vigia regressão futura.

### AUDIT-FIX-04 (log exception) — JÁ CONCLUÍDO no commit 46f9ab0

### AUDIT-FIX-05 (split commands.py)

- **Arquivo mega único:** criar `nyx/agent/commands/all.py` com 900 linhas.
  - **Detectar:** `find nyx/agent/commands -name "*.py" -exec wc -l {} + | awk '$1 > 300'` deve ser vazio.
- **Rename `commands.py` mantendo vivo:** renomear para `commands_core.py` e `__init__.py` faz `from .commands_core import *`.
  - **Detectar:** arquivo `nyx/agent/commands.py` (sem barra) **não existe**; `from nyx.agent.commands import list_commands` continua funcionando.
- **Perder comandos na migração:** `list_commands()` retorna 30 em vez de 50.
  - **Detectar:** comparar count antes e depois da sprint.

### AUDIT-FIX-06 (ADR-024)

- **ADR em rascunho:** `Status: proposto` ou ausente.
  - **Detectar:** `grep "Status:.*ACEITO" dev-journey/03-decisions/ADR_024_RENDER_LAYER.md`.
- **CLAUDE.md intacto:** não menciona ADR-024.
  - **Detectar:** `grep "ADR-024\|render layer" CLAUDE.md` deve ter >= 2 matches.

### AUDIT-FIX-07 (ask_user)

- **Print escondido em helper:** mover `print(x)` para `_show_prompt(x)` em outro arquivo que faz print.
  - **Detectar:** `grep -rn "print(" nyx/agent/tools/` deve retornar 0.
- **`sys.stdout.write` no lugar de print:** bypass textual do grep.
  - **Detectar:** `grep -rn "sys.stdout.write\|print(" nyx/agent/tools/` deve retornar 0.
- **`input()` mantido com comentário "temporário":**
  - **Detectar:** `grep "input(" nyx/agent/tools/ask_user.py` deve retornar 0 (ignorando docstring).

### DEBT-01 (split loop.py)

- Mesmos vetores que FIX-05. Arquivo único `_core.py` com 700 linhas.
  - **Detectar:** `find nyx/agent/loop -name '*.py' -exec wc -l {} + | awk '$1 > 400'` vazio.
- **API pública quebrada:** callers não encontram `AgentLoop`.
  - **Detectar:** `python -c "from nyx.agent.loop import AgentLoop; AgentLoop('/tmp')"`.

### DEBT-02 (remover nyx/interface/) — JÁ CONCLUÍDO no commit 46f9ab0

### DEBT-03 (logging via logging_service)

- **Migração de amostra:** IA altera 3 arquivos e afirma ter coberto 30.
  - **Detectar:** `grep -rc "logging.getLogger" nyx/ --include='*.py' | grep -v ':0$' | grep -v 'logging_service.py'` deve ser vazio (exceto exceções documentadas).
- **`get_logger` aponta pro default:** implementa como `return logging.getLogger(name)` sem chamar `InternalLogging()`.
  - **Detectar:** `grep -A5 "def get_logger" nyx/agent/services/logging_service.py` deve conter `InternalLogging()`.

### UX-DESIGN-01 (design system)

- **Tokens criados mas hex vivos em outros arquivos:**
  - **Detectar:** invariante #6 do script.
- **⚡ removido só em 1 dos 2 lugares:**
  - **Detectar:** invariante #1 do script (detecta Unicode emoji por faixa).
- **BULLETS['bypass_on'] = '⚡':** IA declara token mas usa o próprio emoji.
  - **Detectar:** `grep "⚡\|\\\\u26A1" nyx/themes/design_tokens.py` vazio.
- **ANSI sem derivação:** IA define `NYX_ACCENT = "#00D4AA"` mas `ANSI_ACCENT_FG = "\033[38;2;1;1;1m"` (valor fake).
  - **Detectar:** `python -c "from nyx.themes.design_tokens import NYX_ACCENT, ANSI_ACCENT_FG, hex_to_ansi_fg; assert ANSI_ACCENT_FG == hex_to_ansi_fg(NYX_ACCENT)"`.

### UX-LAYOUT-01 (banner + toolbar + paste)

- **Colapso fake:** IA implementa com `lines[:3]` só, sem pegar tail.
  - **Detectar:** teste com 20 linhas — output precisa conter `linha 0` E `linha 19`.
- **Toolbar `N/M tok` com zeros:** nunca pega `get_context_info()`.
  - **Detectar:** após envio de mensagem, toolbar mostra números > 0.

### UX-LAYOUT-02 (tool cards + evento compactação)

- **Card sempre OK (verde):** não distingue erro.
  - **Detectar:** teste manual: chamar tool com erro (path inválido), card deve ter borda `NYX_ERROR` e rótulo ERRO.
- **Duração = 0ms sempre:** timer quebrado.
  - **Detectar:** visualmente ou via stdout capture.
- **`on_compaction` wired mas nunca disparado:**
  - **Detectar:** sessão longa de 50 iterações — evento deve aparecer pelo menos 1x.

### UX-LAYOUT-03 (streaming + spinner + Ctrl+C)

- **Buffer nunca esvazia:** resposta só aparece no fim — quebra streaming.
  - **Detectar:** enviar pergunta longa; ver tokens aparecendo **durante** a geração, não no final.
- **Spinner hardcoded em vez de SPINNER_FRAMES:**
  - **Detectar:** `grep "⠋\|spinner.*'⠋'" nyx/agent/output.py` deve apontar para uso via import de design_tokens, não char literal.
- **Ctrl+C imprime `[cancelado]` sem `\r\x1b[2K`:**
  - **Detectar:** no código: `grep -B1 -A3 "KeyboardInterrupt" nyx/cli.py | grep "2K"`.

### UX-BUG-01 (autocomplete)

- **`auto_suggest` declarado mas Tab não aceita:**
  - **Detectar:** teste pexpect: digitar `/co` + Tab, buffer deve ter `/commit` (ou primeiro match).
- **`select_first=True` mas popup vazio por filtro bugado:**
  - **Detectar:** `/q<Enter>` deve submeter `/quit`.
- **`/help git` retorna lista inteira:** filtro não funciona.
  - **Detectar:** `format_help(filter_query="git")` só deve conter comandos de categoria git.

### UX-BUG-02 (race input + cold/warm)

- **`time.sleep(1)` como "fix" de race:**
  - **Detectar:** `git diff` da sprint — nenhuma linha adicionada contendo `time.sleep` ou `asyncio.sleep`.
- **`on_model_state` wired sem disparo real:**
  - **Detectar:** `./run.sh`, enviar mensagem, observar toolbar mudar de cold → warming → warm.
- **`termios.tcflush` não roda:** só em `if False`.
  - **Detectar:** bash `scripts/repro_race_input.sh` — input pré-banner **deve** ser descartado.

### UX-BUG-03 (perf)

- **Mediu 1 run só:** primeiro run engana por cache cold.
  - **Detectar:** script de medição precisa rodar 5x e imprimir mediana.
- **`@lru_cache` em método com `self`:** nunca cacheia (unhashable).
  - **Detectar:** verificar que `memory.index()` cacheia por atributo, não por lru_cache em método.
- **Console singleton mas `Console(highlight=False)` ainda instanciado localmente:**
  - **Detectar:** `grep -c "Console(highlight" nyx/agent/output.py` deve ser <= 1.

### VISION-01 (provider moondream)

- **Cache pré-populado com descrição genérica:** IA cria `~/.nyx/vision_cache/*.txt` com "imagem".
  - **Detectar:** rm `~/.nyx/vision_cache/*` e rodar describe — deve popular cache novamente com descrição real variada.
- **`is_available()` sempre True:** ignora ollama list.
  - **Detectar:** parar Ollama (`pkill ollama`), chamar `is_available()` → deve retornar False.
- **Fallback com string ambígua:** retorna `"OK"` quando moondream ausente.
  - **Detectar:** `describe(path)` sem moondream → string contém "indisponível" ou "ausente".

### VISION-02 (pipeline [Image #N])

- **`_expand_images` retorna texto fixo:**
  - **Detectar:** 2 imagens diferentes → descrições inline diferentes no output.
- **Regex não captura `[Image #10]` (2 dígitos):**
  - **Detectar:** teste com map `{10: "path"}`.
- **image_map não persiste entre turnos:** usuário cola imagem, envia turno 1, turno 2 `/vision 1` não acha.
  - **Detectar:** `ls ~/.nyx/image_index.json` deve existir após colar imagem.

### VISION-03 (VRAM estável)

- **Script `verify_vram.sh` só ecoa `[OK]`:**
  - **Detectar:** ler o script e verificar que há `nvidia-smi` + comparação numérica real.
- **`num_gpu=0` no código mas IA esqueceu de colocar em `options`:**
  - **Detectar:** `grep -A5 "options" nyx/providers/vision_client.py | grep "num_gpu.*0"`.

### DEPLOY-01 (install.sh)

- **Script só imprime `[OK]` sem rodar comandos:**
  - **Detectar:** `grep -c "ollama pull\|pip install\|apt install\|curl" install.sh` deve ser >= 4.
- **Idempotência fingida:** segunda run ainda instala tudo.
  - **Detectar:** `./install.sh` duas vezes — segunda execução com stdout contendo `SKIP` em cada fase.
- **Sem `set -eu`:** erros silenciosos.
  - **Detectar:** `head -3 install.sh | grep "set -eu\|set -e"`.
- **`sudo` sem distro detect:** roda `apt install` em Fedora.
  - **Detectar:** ler script, confirmar detecção de PKG_MANAGER.

### DEPLOY-02 (.desktop + ícone)

- **`Exec=/home/andrefarias/...` hardcoded:** não funciona pra outro usuário.
  - **Detectar:** `grep "Exec=" ~/.local/share/applications/nyx.desktop` — se `$HOME` ou caminho derivado de `Path(__file__).parent`, OK; se path fixo, FAIL.
- **Icon=nyx mas arquivo `nyx.png` ausente:**
  - **Detectar:** `test -f ~/.local/share/icons/hicolor/256x256/apps/nyx.png`.
- **`--dry-run` ainda escreve:**
  - **Detectar:** rodar `--dry-run` e conferir que `~/.local/share/applications/nyx.desktop` **não** foi criado/modificado (comparar mtime).

### UX-EXTRA-01 (editar último input)

- **Ctrl+Up insere literal `\x1b[1;5A`:** keybinding não capturou.
  - **Detectar:** pexpect: envia Ctrl+Up, buffer deve ter conteúdo anterior, não escape sequence.
- **`/edit` retorna placeholder sem prefill:**
  - **Detectar:** teste: digitar `oi`, enviar; digitar `/edit`; prompt seguinte deve pré-popular `oi`.

---

### AUDIT-FIX-08 (docstring Claude Code em output.py)

- **Substituir por sinônimo sutil** ("estilo Anthropic-CLI", "como no CC"): proibido. Grep textual `Claude` deve ser 0.
  - **Detectar:** `grep -rn 'Claude\|claude' nyx/ --include='*.py' | grep -v '# noqa'` vazio.
- **Transformar docstring em comentário** achando que sai do check. Proibido: `sprint_invariants.sh` usa grep puro.
- **Deletar a função inteira** em vez de reescrever. Proibido: mantém assinatura e comportamento.

### AUDIT-FIX-09 (excepts silenciosos residuais)

- **Remover o except** para "resolver" o invariante — exceção vira não tratada. Proibido: tipo específico (OSError, PermissionError) foi mantido por design.
  - **Detectar:** `grep -nB1 -A2 'except.*:$' nyx/agent/memory.py nyx/agent/output.py nyx/context/project.py` deve mostrar 3 blocos com logger, nenhum com `pass` isolado.
- **Logger no nível errado** (`error` onde é best-effort esperado). Detectar: revisar severidade caso a caso.
- **`print()` em vez de logger.** Proibido: ADR-024 permite print só em output.py render layer, não em except block.

### DEBT-04 (ruff F841/F401)

- **`# noqa: F841`** inline em vez de corrigir. Proibido.
  - **Detectar:** `grep -n 'noqa' nyx/agent/tools/analyze_tool.py nyx/agent/tools/todo_write.py nyx/agent/tools/web_search.py` deve retornar vazio após a sprint.
- **Deletar a linha da variável** sem investigar se era parte de fluxo perdido. Exige analisar contexto e justificar decisão no commit.
- **`_ = DDGS`** no nível do módulo só para silenciar linter. Proibido.

### DEBT-05 (pre-commit hook acentuação)

- **`exclude: '.*\.md$'`** genérico. Proibido — só os 2 arquivos nomeados.
- **Desativar o hook inteiro** em vez de excluir. Proibido.
- **Não testar o caminho positivo** (arquivo .md real com "funcao" sem acento deve disparar warning). Obrigatório verificar ambos caminhos.

### ADR-021-DOC (tree-sitter opcional)

- **ADR Status: proposto** ou sem Status. Proibido: ACEITO exigido.
- **Copiar ADR-001 e trocar título.** Proibido: cada ADR tem contexto próprio.
- **Pular seção "Alternativas"** — obrigatória em todo ADR deste projeto.
- **Não atualizar CLAUDE.md.** Detectar: `grep -c '^| 021 |' CLAUDE.md` deve ser >= 1.

### ADR-022-DOC (moondream CPU)

- **Número genérico de RAM** ("poucos GB"). Proibido: valor concreto.
- **Alternativa fantasma** (mencionar sem comparar). Obrigatório: cada alternativa rejeitada tem argumento objetivo.
- **Deixar detalhes para VISION-01.** Proibido: ADR é onde a decisão vive, não só no código.
- **Licença não verificada.** Obrigatório: citar licença do moondream2 no ADR.

### INFRA-GAUNTLET-01 (gauntlet + watchdog VRAM)

- **Watchdog só loga, não aborta.** Proibido: precisa executar `pkill` real na breach.
- **Threshold alto demais** (ex.: 2000 MiB) — aborta preventivamente quando gauntlet ainda rodaria. Manter padrão 500 MiB configurable via env.
- **Baseline forjado** (copy de checkpoint antigo). Detectar: timestamp do JSON deve ser de hoje.
- **Pular fase via `--only`** e declarar gauntlet "completo". Proibido: exigido `./run.sh --gauntlet` sem filtros.
- **Pass rate 99% passar por 100%.** Proibido: critério é binário, 100% exigido.

### VALIDATE-ONDA-20 (TUI+CTX)

- **Marcar CONCLUIDA só lendo código** sem rodar `./run.sh`. Proibido: validação é visual+funcional.
- **OK no checklist sem output.** Obrigatório: observação literal ou screenshot por item.
- **BLOQUEADA virar "débito" sem sprint.** Proibido (feedback "nenhum débito para trás"): cada BLOQUEADA precisa de sprint nova com ID no master.
- **Aglutinar as 7 num só checkpoint.** Proibido: cada sprint decide independente.

### VALIDATE-ONDA-21 (TUI-FIX)

- **"Parece que funciona" sem executar.** Proibido.
- **Screenshot ausente para item visual.** Obrigatório para FIX-01 (banner), FIX-02 (streaming), FIX-03 (popup), FIX-07 (toolbar).
- **BLOQUEADA sem sprint nova.** Proibido.
- **xclip ausente virar "CONCLUIDA".** Detectar: `command -v xclip` é pré-check; se faltar, BLOQUEADA com motivo.

---

## Lições do freelancer

- Toda "implementação em 5 min" que deveria levar 2h provavelmente é gambiarra. Pergunta-se: "que comando provaria que funciona?" Se a IA não sabe responder, não fez.
- Prefira verificação **por efeito observável** (rodar código, ver resultado) em vez de "li o diff e parece ok".
- Quando a IA diz "checkpoint OK", **cole o output do comando** que provou isso.
- `git log -p | grep "new file"` revela se um diff gigante é de fato código ou só caracteres em string/docstring.
- Sprints grandes (FIX-05, DEBT-01, UX-DESIGN-01): **sempre pedir screenshot / output de execução real** antes de aceitar CONCLUIDA.

---

*"Medir sem cronômetro é opinar sobre velocidade." -- anônimo*
