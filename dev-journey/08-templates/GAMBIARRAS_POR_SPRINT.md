# Catálogo de Gambiarras por Sprint — Onda 22

**Uso:** antes de executar qualquer sprint, a IA executora **deve** ler a seção correspondente. Este documento lista as bypass-paths típicas que freelas/IAs usam para fingir conclusão.

Complementa o catálogo geral em `SPRINT_TEMPLATE_V2.md` (20 padrões universais).

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
| DEBT-01 | — (loop.py já < 800) |
| DEBT-02 | — (interface/ vazio, removido) |
| DEBT-03 | — (logging unificação) |
| UX-DESIGN-01 | **#1** emoji ⚡; **#2** "Claude Code" docstring; **#6** hex hardcoded |
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

## Lições do freelancer

- Toda "implementação em 5 min" que deveria levar 2h provavelmente é gambiarra. Pergunta-se: "que comando provaria que funciona?" Se a IA não sabe responder, não fez.
- Prefira verificação **por efeito observável** (rodar código, ver resultado) em vez de "li o diff e parece ok".
- Quando a IA diz "checkpoint OK", **cole o output do comando** que provou isso.
- `git log -p | grep "new file"` revela se um diff gigante é de fato código ou só caracteres em string/docstring.
- Sprints grandes (FIX-05, DEBT-01, UX-DESIGN-01): **sempre pedir screenshot / output de execução real** antes de aceitar CONCLUIDA.

---

*"Medir sem cronômetro é opinar sobre velocidade." -- anônimo*
