# SPRINT 284 — TUI-SLASH-COMPLETER-POPULATE-01

- Onda: 34 (continuação — fixes do caminho `--web` + UX/redesign da auditoria)
- Data do spec: 2026-05-29
- Predecessor de execução: ONDA-34 sprint 283 TUI-NYXCODE-GHOST-LAZY-MOUNT-01 (CONCLUIDA, última na origin/main = commit `e8314b1`)
- Plano de auditoria: bloco `MANUAL_OVERRIDE_ONDA_34` do master (linha 810: "slash completer populado" listado como item UX pendente IDs 284+)
- Status: PRONTO PARA EXECUÇÃO

## Contexto

O slash completer da NyxTUI Textual está inerte: ao digitar `/` no input, nenhuma
sugestão de comando aparece. A causa-raiz é dado de entrada vazio, NÃO defeito de
widget. Em `nyx/cli.py:542`, a NyxTUI é instanciada com `slash_completer=[]`
(lista literal vazia). O InputWidget já implementa o suporte completo: quando
`slash_completer` é não-vazio, constrói `SuggestFromList([f"/{c}" for c in
slash_completer], case_sensitive=False)` e o Textual exibe a sugestão ghost-inline
nativa (Tab aceita). Com lista vazia, `input.py:70` cai no ramo `else: suggester =
None` e o input nasce sem suggester.

O fix é estritamente popular `slash_completer` com a lista real de nomes de
comandos (sem o `/`), originada da fonte canônica e passada por
`cli.py -> NyxTUI.__init__ -> compose() -> InputWidget`. O pipeline já está pronto
ponta a ponta; só falta o dado.

Decisão de escopo (Q1 da auditoria): ghost-inline nativo basta. Popup-dropdown
está FORA de escopo — nenhum widget de dropdown existe no código hoje e nenhum
será introduzido aqui.

## Fonte canônica da lista de comandos (verificada via grep)

`nyx/agent/commands/_registry.py` mantém o dict global `_COMMANDS` populado por
side-effect dos decoradores `@nyx_command` (importados em
`nyx/agent/commands/__init__.py:13-30`). A API pública canônica para obter os
comandos é `list_commands()` (definida em `_registry.py:65-72`, re-exportada em
`__init__.py:36` e listada em `__all__`):

- Retorna `list[CommandDef]` deduplicada por `name` (aliases NÃO repetem o comando
  canônico) e ordenada por `name`.
- Cada `CommandDef.name` é o nome SEM `/` (ex.: `help`, `status`, `commit`).
- Confirmação em runtime: `[c.name for c in list_commands()]` retorna 67 nomes
  (`./venv/bin/python -c "from nyx.agent.commands import list_commands; print(len([c.name for c in list_commands()]))"` imprime `67`). Bate com a contagem
  esperada (~67).

Isto é exatamente o shape que `slash_completer` espera: nomes sem `/`. O
`input.py:71` adiciona o prefixo `/` (`f"/{c}"`). NÃO usar `_COMMANDS` (privado)
nem `_dispatcher._COMMANDS`; usar a função pública `list_commands`.

## Escopo (touches autorizados)

- Arquivos a modificar:
  - `nyx/cli.py` — dois pontos, ambos dentro da função `run_repl`:
    1. Import: adicionar `list_commands` ao import já existente
       `from nyx.agent.commands import handle_command` (linha 105).
    2. Instanciação: trocar `slash_completer=[]` (linha 542) por
       `slash_completer=[c.name for c in list_commands()]`.
- Arquivos a criar: nenhum.
- Arquivos NÃO a tocar:
  - `nyx/agent/tui/widgets/input.py` — `InputWidget` já constrói o
    `SuggestFromList` corretamente (linhas 70-72) e cai em `suggester=None`
    apenas quando a lista é vazia. Com lista não-vazia funciona sem alteração.
    NÃO reescrever o widget; NÃO introduzir dropdown.
  - `nyx/agent/tui/app.py` — `NyxTUI.__init__` já guarda
    `self._slash_completer = slash_completer or []` (linha 86) e o `compose()`
    já repassa `slash_completer=self._slash_completer` ao InputWidget (linha
    146). Nenhuma alteração necessária; apenas verificar (read-only) que o
    encadeamento continua intacto.
  - `nyx/agent/commands/_registry.py`, `nyx/agent/commands/__init__.py` — a API
    `list_commands` é consumida como está; nenhum comando novo é registrado.
  - 7 arquivos protegidos pelo check #14 (defesa anti-sanitizer): `cli.py` NÃO
    está entre os arquivos do check #14 que dependem de `chr(0xNNNN)` para
    ícones; o touch é uma única expressão de lista, sem remover literais Unicode.

## Acceptance criteria

1. `nyx/cli.py:105` importa `list_commands` junto de `handle_command` da
   `nyx.agent.commands` (mesma instrução de import, dentro de `run_repl`).
2. `nyx/cli.py:542` passa `slash_completer=[c.name for c in list_commands()]` à
   NyxTUI (não mais `[]`). A lista resultante tem 67 entradas, todas sem `/`.
3. O encadeamento `cli.py -> NyxTUI.__init__ -> compose -> InputWidget` permanece
   intacto: `app.py:86` e `app.py:146` inalterados; `input.py` inalterado.
4. Smoke boot continua verde: `./run.sh --smoke` imprime `boot ok` e exit 0.
5. Invariantes: `bash scripts/sprint_invariants.sh` reporta PASS 14/14, FAIL 0.
6. Gauntlet rápido e loop: `./run.sh --gauntlet --only rapido` e `--only loop`
   APROVADO (aceitar 1 execução de cada; cruzar com flake conhecido do BRIEF
   seção "Flake reprodutível do gauntlet --only rapido no RTX 3050 4GB").
7. Proof-of-work runtime-real `--web`: ao digitar `/` no input da TUI no xterm.js,
   aparece uma sugestão ghost de comando (antes não aparecia nada). Confirmado via
   dump do buffer xterm.js ou screenshot (ver seção Proof-of-work).
8. Acentuação: `python3 ~/.config/zsh/scripts/validar-acentuacao.py --paths
   nyx/cli.py` retorna rc 0 nas linhas tocadas (o touch não introduz texto
   acentuado novo; é expressão de código).

## Invariantes a preservar

- Encadeamento de `slash_completer` (descoberto na exploração): `cli.py:542 ->
  app.py:78/86 -> app.py:146 -> input.py:61/70/71`. O dado flui sem transformação
  além do prefixo `/` adicionado em `input.py:71`. Passar nomes JÁ com `/` causaria
  `//help` (regressão); manter nomes sem `/`.
- API pública: consumir `list_commands` (não `_COMMANDS`). Aderência ao contrato
  de `nyx/agent/commands/__init__.py` (`__all__`), que existe justamente para
  isolar o registry privado.
- Defesa anti-sanitizer (BRIEF seção "Defesa anti-sanitizer" + check #14): o touch
  em `cli.py` não remove nem altera literais `chr(0xNNNN)`; o invariante #14
  permanece intacto porque os arquivos cobertos (banner.py, output.py,
  design_tokens*, chat_message.py, sprint_invariants.sh) não são tocados.
- Side-effect do `--gauntlet` em README + PORT_STATUS (BRIEF): rodar gauntlet pode
  modificar `README.md` e `dev-journey/PORT_STATUS.md` via `scripts/update_docs.py`;
  esses touches são derivados automáticos e NÃO contam como violação de escopo.
- GUIDE.md §3 (mudanças cirúrgicas): tocar apenas o import e a expressão da lista;
  não reformatar o bloco de instanciação adjacente nem o caminho não-TTY (linhas
  551-576).
- Memória `feedback_smoke_boot.md`: `./run.sh --smoke` (check #13/#1) obrigatório
  antes de marcar CONCLUIDA.

## Plano de implementação

1. Confirmar pré-condição (read-only): `grep -n "slash_completer=\[\]" nyx/cli.py`
   retorna a linha 542; `grep -n "from nyx.agent.commands import handle_command"
   nyx/cli.py` retorna a linha 105.
2. Em `nyx/cli.py:105`, alterar
   `from nyx.agent.commands import handle_command` para
   `from nyx.agent.commands import handle_command, list_commands`.
3. Em `nyx/cli.py:542`, trocar `slash_completer=[],` por
   `slash_completer=[c.name for c in list_commands()],`.
4. Verificar (read-only) que `app.py:86/146` e `input.py:61/70/71` seguem
   intactos (nenhuma edição esperada nesses arquivos).
5. Rodar a bateria estrutural (seção Testes) e o proof-of-work runtime-real
   `--web` (seção Proof-of-work).

## Aritmética

Sprint sem meta de redução de linhas. Delta esperado em `nyx/cli.py`: +0 linhas
líquidas (linha 105 reescrita no lugar; linha 542 reescrita no lugar). Nenhuma
extração nem arquivo novo. A "aritmética" relevante é de cardinalidade da lista:

- Lista atual passada à NyxTUI: 0 entradas (`[]`).
- Lista projetada: `len([c.name for c in list_commands()])` = 67 entradas.
- Conferência: deve fechar em 67 (`./venv/bin/python -c "from nyx.agent.commands
  import list_commands; print(len([c.name for c in list_commands()]))"` == `67`).
  Se o número divergir de 67 no momento da execução, é porque comandos foram
  adicionados/removidos desde o spec — não é regressão; apenas registrar o número
  observado no proof-of-work.

## Testes

- Não há suíte de unit isolada para o slash completer (grep `slash_completer` em
  testes retorna apenas os arquivos de produção). A cobertura é via gauntlet +
  proof-of-work runtime-real.
- Baseline: FAIL_BEFORE do `bash scripts/sprint_invariants.sh` = 0 (14/14 PASS).
  Esperado FAIL_AFTER = 0 (14/14 PASS) — o touch não altera nenhum invariante.
- Smoke: `./run.sh --smoke` deve continuar `boot ok` exit 0.

## Proof-of-work esperado

- Diff final de `nyx/cli.py` (2 linhas: import 105 + instanciação 542).
- Runtime real (comandos do BRIEF seção `[CORE] Contratos de runtime`):
  - Smoke: `./run.sh --smoke` (espera `boot ok`, exit 0).
  - Invariantes: `bash scripts/sprint_invariants.sh` (espera PASS 14/14, FAIL 0).
  - Gauntlet: `./run.sh --gauntlet --only rapido` + `./run.sh --gauntlet --only
    loop` (APROVADO; 1 execução de cada, cruzar com flake conhecido do BRIEF).
- Validação visual `--web` (cockpit :11437), com shim no-open
  `PATH="/tmp/nyx_noopen:$PATH"`:
  1. Subir `--web` em background+disown (NOTA: `--web` bloqueia; fechar o browser
     dispara SIGTERM no run.sh): `PATH="/tmp/nyx_noopen:$PATH" ./run.sh --web`
     (run_in_background, capturar PID).
  2. Enviar `/` ao REPL via control endpoint:
     `curl -X POST http://127.0.0.1:11437/control/repl/send -H "Content-Type:
     application/json" -d '{"text":"/"}'`.
  3. Carregar `mcp__plugin_playwright_playwright__*` por ToolSearch; navegar para
     `http://127.0.0.1:11437/static/terminal.html`.
  4. Confirmar a sugestão ghost via `browser_evaluate` lendo `term.buffer.active`
     (dump do buffer xterm.js) OU screenshot: deve aparecer uma sugestão de
     comando (ghost-inline) após o `/` — antes do fix, nada aparecia.
  5. Cleanup por PID (NÃO `pkill -f "run.sh --web"`): matar o PID capturado em (1)
     e processos-filho diretos; depois `pkill -f "nyx/proxy.py"`,
     `pkill -f "ollama serve"`; `nvidia-smi` confirmando VRAM livre (BRIEF check
     universal #5 + disciplina OOM GPU 4GB).
- Acentuação periférica: `python3 ~/.config/zsh/scripts/validar-acentuacao.py
  --paths nyx/cli.py` (rc 0 nas linhas tocadas).
- Hipótese verificada (lição 4): `grep -n "def list_commands" nyx/agent/commands/_registry.py` e `grep -n "list_commands" nyx/agent/commands/__init__.py`
  confirmam que `list_commands` existe e é re-exportada (já verificado neste spec).

## Disciplina OOM (BRIEF + memórias)

- GPU 4GB; sem agentes paralelos; gauntlet só `--only rapido`/`--only loop`.
- `--web` bloqueia: rodar em background+disown; fechar o browser dispara SIGTERM
  no run.sh.
- Cleanup pós-teste SEMPRE por PID capturado; NUNCA `pkill -f "run.sh --web"`
  (mata sessões legítimas alheias).
- Flake conhecido do gauntlet rápido no RTX 3050 4GB é esperado (BRIEF): aceitar 1
  execução fresca; não tratar I-05/P-01/P-04/P-05/P-07 como regressão desta sprint.

## Riscos e não-objetivos

- NÃO-objetivo: popup-dropdown de comandos (decisão Q1 = ghost-inline nativo
  basta). Se ressurgir como requisito, abrir sprint nova (anti-débito: memória
  `feedback_nenhum_debito.md`).
- NÃO-objetivo: incluir aliases no completer. `list_commands()` já deduplica para
  nomes canônicos; expor aliases (ex.: `/d` para `diff`) seria escopo separado.
- NÃO-objetivo: descrições inline / preview no completer. `SuggestFromList` só
  oferece a string do comando; enriquecer a sugestão exigiria suggester custom
  (sprint nova se desejado).
- Risco baixo: se algum `@nyx_command` futuro registrar `name` com `/` embutido,
  geraria `//`; hoje nenhum o faz (todos os 67 nomes são sem `/`, verificado em
  runtime). Não introduzir guarda especulativa (GUIDE.md §2).
- Achado colateral durante execução vira sprint nova com ID no
  `SPRINT_ORDER_MASTER` (BRIEF check universal #6 + memória `feedback_nenhum_debito.md`); nunca absorver implicitamente.

## Registro no master (pós-execução)

Adicionar linha ID 284 ao bloco `MANUAL_OVERRIDE_ONDA_34` do
`dev-journey/06-sprints/SPRINT_ORDER_MASTER.md` (linhas 801-808), dependência
`TUI-NYXCODE-GHOST-LAZY-MOUNT-01`, e remover "slash completer populado" da lista
de pendentes na linha 810.

## Referências

- BRIEF: `/home/andrefarias/Desenvolvimento/Nyx-Code/VALIDATOR_BRIEF.md`
  (seções `[CORE] Contratos de runtime`, `Defesa anti-sanitizer`, `Flake
  reprodutível do gauntlet`, `Side-effect do --gauntlet`).
- Precedente histórico: SPRINT 283 TUI-NYXCODE-GHOST-LAZY-MOUNT-01
  (`dev-journey/06-sprints/producao/SPRINT_TUI_NYXCODE_GHOST_LAZY_MOUNT_01.md`
  estilo/formato; mesma sessão ONDA-34, mesmo arquivo de UI tocado em parte).
- Master: bloco `MANUAL_OVERRIDE_ONDA_34` (linha 810 lista este item como
  pendente IDs 284+).
- Fonte da lista: `nyx/agent/commands/_registry.py:65-72` (`list_commands`),
  re-export em `nyx/agent/commands/__init__.py:36`.
