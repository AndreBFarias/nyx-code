# SPRINT 283 — TUI-NYXCODE-GHOST-LAZY-MOUNT-01

- Onda: 34 (continuação — fixes do caminho `--web` + UX/redesign da auditoria)
- Data do spec: 2026-05-29
- Predecessor de execução: ONDA-34 fixes 278-282 (CONCLUIDAS, commit `cbc27c6` na origin/main)
- Plano de auditoria: `~/.claude/plans/redesign-auditoria-da-tender-beacon.md` (decisão #4, parte "balão assistant vazio")
- Status: PRONTO PARA EXECUÇÃO

## Contexto

A NyxTUI Textual monta um `ChatMessage("assistant", "")` vazio no container
`#chat` no início de cada turno, dentro de `_on_input_submit`
(`nyx/agent/tui/app.py:190-193`). Resultado: um balão fantasma renderizado
apenas como o cabeçalho "◆ NyxCode" (sem corpo) fica visível antes do primeiro
token chegar. Em turnos que não produzem texto de assistant (somente tool, ou
erro), o balão vazio persiste indefinidamente.

O `render()` de `ChatMessage` (`chat_message.py:82-85`) confirma a causa-raiz
visual: quando `self._content` é falsy, retorna `Text(f"{_DIAMOND} NyxCode")` —
exatamente o cabeçalho órfão observado.

Esta sprint aplica a parte "lazy-mount" da decisão #4 da auditoria: não montar o
assistant vazio; montá-lo somente quando o 1º token chega, em `_on_agent_token`.

Nota de escopo: a auditoria (linha 53 do plano) também previa um widget de status
line "NyxCode: processando" acima do input. Essa parte NÃO está nesta sprint —
nenhum widget de status line existe no código hoje (grep vazio em `app.py` e
`widgets/`), e o bloco `MANUAL_OVERRIDE_ONDA_34` do master (linha 809) já a lista
como item UX pendente separado. Aqui o objetivo é estritamente eliminar o balão
fantasma via lazy-mount, sem introduzir status line.

## Escopo (touches autorizados)

- Arquivos a modificar:
  - `nyx/agent/tui/app.py` — métodos `_on_input_submit` (linhas ~184-204),
    `_on_agent_token` (linhas ~289-296), `_process_turn` (linhas ~283-287) e o
    comentário do atributo `self._current_assistant` (linhas ~91-93).
- Arquivos a criar: nenhum.
- Arquivos NÃO a tocar:
  - `nyx/agent/tui/widgets/chat_message.py` — `ChatMessage` já expõe
    `__init__(role, content="")`, `append_text(token)`, `set_content(content)` e
    `render()` com o caminho assistant-vazio. O fix monta o widget via API
    existente; nenhuma alteração no widget é necessária. NÃO remover o ramo
    `else: return Text(f"{_DIAMOND} NyxCode")` do `render()` — ele permanece como
    estado transitório legítimo entre o mount e o 1º `append_text`.
  - `nyx/agent/loop/_core.py`, `nyx/agent/loop/_iteration.py` — o bridge de
    callbacks (`agent._on_token`, `agent._collector._on_token`) é patcheado no
    `__init__` da NyxTUI; assinatura do AgentLoop permanece intocada (FORBIDDEN
    explícito herdado de TUI-AGENT-BRIDGE-01, comentário em `app.py:94-104`).
  - `nyx/agent/tui/styles/nyx.tcss` — sem mudança de CSS.
  - 7 arquivos protegidos pelo check #14 (defesa anti-sanitizer): `chat_message.py`
    usa `_DIAMOND = chr(0x25C6)` e está na lista; como NÃO o tocamos, o invariante
    permanece intacto.

## Acceptance criteria

1. `_on_input_submit` NÃO monta nem guarda um `ChatMessage("assistant", "")` no
   início do turno: após `chat.mount(ChatMessage("user", text))`, segue direto
   para `toolbar.inflight = True` e `run_worker`, com `self._current_assistant`
   explicitamente em `None`.
2. `_on_agent_token` cria e monta o `ChatMessage("assistant", ...)` no `#chat`
   no PRIMEIRO token (quando `self._current_assistant is None`), e só então faz
   o `append_text`. Tokens subsequentes do mesmo turno reusam o mesmo widget.
3. Tokens vazios/falsy (`not token`) NÃO disparam o lazy-mount — não criam balão.
   (Hoje `append_text` já curto-circuita em `not token`; o mount também precisa
   ser condicionado a `token` truthy para não materializar balão vazio.)
4. Turno que não emite nenhum token de assistant (só tool call/result, ou erro)
   NÃO deixa balão "◆ NyxCode" vazio no chat ao terminar.
5. `_process_turn` reseta `self._current_assistant = None` no `finally`, de modo
   que o turno N+1 nunca faz append no widget assistant do turno N antes do
   próprio lazy-mount disparar.
6. O comentário de `self._current_assistant` (linhas ~91-93) é atualizado para
   refletir o lazy-mount (deixa de descrever "mountado no início de cada turno").
7. Quando há resposta de texto, o balão "◆ NyxCode\n<conteúdo>" renderiza
   corretamente — o streaming continua crescendo em altura via
   `refresh(layout=True)` (preservação de TUI-FIX-CHATMESSAGE-RELAYOUT-01).

## Invariantes a preservar

- `_current_assistant` tem escopo isolado a `app.py` (grep confirma: 4 referências,
  zero consumidores externos) — o fix não vaza para nenhum outro módulo.
- Loop affinity (TUI-FIX-HTTPX-LOOP-AFFINITY-01, ONDA-33): callbacks rodam no
  event loop principal do Textual; o mount em `_on_agent_token` toca o widget
  DIRETO (sem `call_from_thread`). Manter esse padrão — `call_from_thread` aqui
  lançaria RuntimeError.
- `scroll_end(animate=False)` sempre por keyword (TUI-FIX-SCROLL-END-KWARG-01):
  ao montar o assistant lazy, chamar `chat.scroll_end(animate=False)`, nunca
  posicional.
- Relayout streaming (TUI-FIX-CHATMESSAGE-RELAYOUT-01): não alterar `append_text`
  nem `set_content`; o widget cresce em altura por conta própria.
- Defesa anti-sanitizer (BRIEF, seção "Defesa anti-sanitizer"): `chat_message.py`
  permanece intocado, preservando `_DIAMOND = chr(0x25C6)` e a cobertura do
  check #14.
- GUIDE.md §3 (mudanças cirúrgicas): mexer somente nos 4 pontos de `app.py`; não
  refatorar callbacks vizinhos (`_on_agent_tool`, `_on_agent_tool_result`,
  `_dispatch_slash`) que já montam seus próprios `ChatMessage` corretamente.
- PT-BR com acentos completos em todo comentário/docstring tocado; zero emojis;
  zero menção a IA externa.

## Plano de implementação

1. Em `_on_input_submit` (`app.py`), remover as três linhas que montam e guardam
   o assistant vazio (atualmente `assistant = ChatMessage("assistant", "")`,
   `chat.mount(assistant)`, `self._current_assistant = assistant`). Manter o
   `chat.scroll_end(animate=False)` do balão do usuário. Setar explicitamente
   `self._current_assistant = None` antes de `toolbar.inflight = True`, deixando
   claro que o lazy-mount ocorre no callback de token.
2. Em `_on_agent_token` (`app.py`), trocar o guard. Hoje:
   `if self._current_assistant is not None and token: ... append_text`.
   Novo comportamento:
   - Se `not token`: retorna (não cria balão por token vazio).
   - Se `self._current_assistant is None`: cria `ChatMessage("assistant", "")`,
     `chat = self.query_one("#chat", VerticalScroll)`, `chat.mount(assistant)`,
     guarda em `self._current_assistant`, `chat.scroll_end(animate=False)`.
   - Em seguida (com `_current_assistant` garantido), `append_text(token)`.
   Manter o toque direto no widget (sem `call_from_thread`).
3. Em `_process_turn` (`app.py`), adicionar `self._current_assistant = None` no
   bloco `finally`, após (ou junto a) o reset de `toolbar.inflight = False` e o
   `scroll_end`. Garante que o próximo turno parta de estado limpo.
4. Atualizar o comentário do atributo `self._current_assistant` (linhas ~91-93)
   e a docstring de `_on_input_submit` (linhas ~160-174) para descrever o
   lazy-mount em vez de "monta assistant vazio". Docstring de `_on_agent_token`
   passa a documentar o lazy-mount no 1º token.

## Aritmética

Esta sprint NÃO tem meta numérica de linhas (não é refactor de tamanho).
Delta esperado em `app.py`: aproximadamente `-3` linhas no `_on_input_submit`
(remoção do mount do assistant vazio, +1 linha do `= None` explícito → net ~-2),
`+4..6` linhas no `_on_agent_token` (bloco de lazy-mount), `+1` linha no
`finally` de `_process_turn`, mais ajuste de comentários (sem impacto funcional).
Saldo líquido pequeno e positivo; nenhuma meta `< N linhas` a fechar.
`app.py` atual: 370 linhas (`wc -l`). Sem teto declarado para esta sprint.

## Testes

- Não há suíte unitária dedicada à NyxTUI Textual no repo (os widgets ainda não
  têm testes unitários; integração roda via Gauntlet e via PTY/xterm.js real).
  Baseline: FAIL_BEFORE = 0 nos invariantes; esperado FAIL_AFTER = 0.
- A verificação funcional desta sprint é o proof-of-work runtime-real abaixo
  (caminho `--web`), não um teste unitário novo. Se o executor julgar barato
  adicionar um teste de comportamento usando o Textual Pilot/headless para
  `_on_agent_token` (1º token monta, token vazio não monta, finally reseta),
  é bem-vindo, mas NÃO é obrigatório e NÃO deve crescer escopo nem tocar arquivos
  fora do listado — caso vire necessário criar fixture/arquivo de teste novo,
  registrar como sprint derivada (protocolo anti-débito).

## Proof-of-work esperado

- Diff final dos pontos tocados em `nyx/agent/tui/app.py`.
- Runtime real (contratos do BRIEF seção `[CORE] Contratos de runtime` + caminho
  `--web` da ONDA-34):
  - Web: `./run.sh --web` (cockpit FastAPI em `127.0.0.1:11437`, PTY + xterm.js).
    Enviar um turno via:
    ```
    curl -X POST http://127.0.0.1:11437/control/repl/send \
      -H "Content-Type: application/json" -d '{"text":"oi\r"}'
    ```
    (endpoint confirmado em `nyx/cockpit/server.py:413`, exige `text` string).
    Confirmar via dump do buffer xterm.js (`browser_evaluate` lendo
    `term.buffer`) OU screenshot Playwright que:
    (a) NENHUM balão "◆ NyxCode" vazio aparece entre o envio e o 1º token;
    (b) quando o 1º token chega, o balão "◆ NyxCode" renderiza com o conteúdo
        crescendo corretamente;
    (c) ao fim de um turno só-tool (sem texto de assistant), nenhum balão
        "◆ NyxCode" vazio fica no chat.
  - Smoke: `./run.sh --smoke` — `boot ok`, exit 0.
  - Invariantes: `bash scripts/sprint_invariants.sh` — PASS 14/14, FAIL 0.
  - Gauntlet: `./run.sh --gauntlet --only rapido` e `./run.sh --gauntlet --only loop`
    — APROVADO. Aceitar o flake reprodutível de VRAM do `--only rapido` em RTX
    3050 4GB documentado no BRIEF; cruzar com `--only loop`.
- Acentuação periférica:
  `python3 ~/.config/zsh/scripts/validar-acentuacao.py --paths nyx/agent/tui/app.py`
  — rc 0 (varrer todos os arquivos modificados; aqui só `app.py`).
- Hipótese verificada (lição 4): `rg "_current_assistant" nyx/` confirma as
  4 referências em `app.py`; `rg "def _on_agent_token|def _on_input_submit|def _process_turn" nyx/agent/tui/app.py`
  confirma as três funções alvo.
- Disciplina OOM: GPU de 4GB; sem agentes paralelos; gauntlet só rápido/por-fase,
  nunca completo. Cleanup pós-teste: `pkill -f "nyx/proxy.py"`,
  `pkill -f "nyx.cockpit.server"`, `pkill -f "ollama serve"`, `nvidia-smi`
  confirmando VRAM livre.

## Riscos e não-objetivos

- NÃO-OBJETIVO: introduzir o widget status line "NyxCode: processando" (parte (a)
  da decisão #4). Fica para sprint UX separada da continuação ONDA-34 — está
  catalogada na nota do bloco `MANUAL_OVERRIDE_ONDA_34` (master linha 809).
- NÃO-OBJETIVO: alterar `ChatMessage.render()` ou remover o ramo assistant-vazio
  do widget. O lazy-mount torna esse ramo um estado transitório breve (entre mount
  e 1º append), legítimo de manter.
- RISCO: race entre o `finally` de `_process_turn` (reset para `None`) e um token
  atrasado do mesmo turno. Como ambos rodam no mesmo event loop principal
  (loop affinity ONDA-33) e `agent.run()` é awaited dentro do `try`, todos os
  tokens chegam ANTES do `finally`. Não há thread concorrente; o reset é seguro.
- RISCO: turno cujo assistant produz token só DEPOIS de tool calls. O lazy-mount
  em `_on_agent_token` monta o balão na posição correta do scroll (após os
  `ChatMessage("tool")` já montados), preservando a ordem cronológica.
- Achado colateral durante execução → registrar como sprint nova com ID 284+ no
  bloco `MANUAL_OVERRIDE_ONDA_34` (protocolo anti-débito, memória
  `feedback_nenhum_debito.md`); nunca absorver implicitamente.

## Referências

- BRIEF: `/home/andrefarias/Desenvolvimento/Nyx-Code/VALIDATOR_BRIEF.md`
  (Contratos de runtime; flake VRAM `--only rapido`; defesa anti-sanitizer;
   sintaxe `--paths` do validador de acentuação).
- Plano de auditoria: `~/.claude/plans/redesign-auditoria-da-tender-beacon.md`
  (decisão #4, BUG `app.py:190-191`).
- Master: `dev-journey/06-sprints/SPRINT_ORDER_MASTER.md` bloco
  `MANUAL_OVERRIDE_ONDA_34` (nota linha 809: balão assistant vazio pendente,
   IDs 283+).
- Precedentes técnicos: TUI-AGENT-BRIDGE-01 (bridge de callbacks),
  TUI-FIX-HTTPX-LOOP-AFFINITY-01 (loop affinity, ONDA-33),
  TUI-FIX-CHATMESSAGE-RELAYOUT-01 (entry 277, relayout streaming),
  TUI-FIX-SCROLL-END-KWARG-01 (kwarg de scroll_end).
- Código confirmado por grep: `nyx/agent/tui/app.py` (370L),
  `nyx/agent/tui/widgets/chat_message.py` (91L),
  `nyx/cockpit/server.py:413` (endpoint `/control/repl/send`).
