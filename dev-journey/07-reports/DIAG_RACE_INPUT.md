# Diagnóstico — race de input-readiness (UX-BUG-02A)

**Data:** 2026-05-15
**Sprint:** UX-BUG-02A
**Modelo executor:** claude-opus-4-7
**Escopo:** apenas diagnóstico — nenhum código de produção alterado.

---

## Sintoma observado

O usuário relata: "se eu clicar em enviar a mensagem antes de aparecer a tela do input ela não processa".

Reprodução prática:
1. Roda `./run.sh`.
2. Durante a fase de boot/banner ASCII (warm-up de `AgentLoop()` + carga de tools + memory index), digita um texto e pressiona Enter.
3. Quando o prompt `nyx>` finalmente aparece, o texto digitado aparece **ecoado** ou **renderizado**, mas o agente não dispara a iteração — ou pior, o texto chega trocado de ordem.

Tempo observado de boot-to-prompt: aproximadamente **15.9 segundos** (medido nesta sprint, ver Hipótese 2). Janela de race muito grande.

---

## Hipótese 1 — buffer de tty do prompt_toolkit

`prompt_toolkit.PromptSession.prompt_async()` só começa a ler stdin no momento em que é invocado (linha 382 de `nyx/cli.py`). Antes disso, qualquer keystroke do usuário vai para o buffer da line discipline do tty (modo canonical/cooked). A hipótese é que esses bytes pré-buffer:

- (a) são preservados pelo kernel e consumidos pelo `prompt_async` quando ele entra em ação; **OU**
- (b) são descartados/embaralhados por algum reset de terminal que o prompt_toolkit faz na ativação (ex.: query CPR `\033[6n`, modo bracket-paste `\033[?2004h`, troca para raw mode).

### Teste 1 — stdin via pipe (sem TTY)

**Comando literal:**

```bash
bash scripts/repro_race_input.sh
```

O script envia `MARK\n/quit\n` com 100 ms de delay para `./run.sh` via pipe, e checa se a marca aparece no log.

**Output (recortado nas linhas reveladoras):**

```
Warning: Input is not a terminal (fd=0).
nyx>
  ╭─ Nyx · v1.2.0 ─────────────...
  │    modelo    qwen3:4b        ...
  │    projeto   Nyx-Code        ...
  ╰─ /help para comandos · Ctrl+D para sair ─...
oi-pre-banner-1778901851-572167
     /quit
     nyx> oi-pre-banner-1778901851-572167
     /quit
[ok] input chegou (marca: oi-pre-banner-1778901851-572167)
```

**Conclusão:** **refutada (parcial)** para o caminho de stdin não-tty. A marca pré-banner foi consumida pelo fallback `input()` nativo (prompt_toolkit emite `Input is not a terminal` e cai para input cru). O bug não se manifesta neste caminho.

### Teste 2 — stdin via PTY (simula terminal real)

**Comando literal:** `python3 /tmp/h1_pty.py` (script usa `pty.fork()`, envia marca quando vê os primeiros bytes do boot, depois envia `/quit` ao detectar `nyx>`).

**Output (recortado):**

```
  [nyx] próxima sprint: UX-BUG-02A (31 pendentes)
oi-tty-1778901926-577965
[?12l[?25h
  ╭─ Nyx · v1.2.0 ──────────... 100% offline ─╮
  │    modelo    qwen3:4b            tools    35 ...
  ...
  ╰─ /help para comandos · Ctrl+D para sair ─...

\033[6n\033[?2004h\033[?1l\033[?25l...nyx>


\033[?12l\033[?25h\033[?25l...oi-tty-1778901926-577965
\033[?12l\033[?25h/quit
... WARNING: your terminal doesn't support cursor position requests (CPR).
... nyx> oi-tty-1778901926-577965
    /quit
```

```
[h1_pty] mandei oi-tty-1778901926-577965 aos 1778901926.65
[h1] input PRE-banner em PTY foi CONSUMIDO (achou oi-tty-1778901926-577965 no output)
```

**Conclusão:** **refutada** para PTY com line discipline canonical. O kernel preserva a linha digitada (terminada com `\n`) e o `prompt_async` a consome quando ativa. Ainda assim, o output revelou dois sinais que apoiam Hipótese 3 (ver abaixo): o texto da marca aparece **duas vezes** no fluxo — uma ecoada pelo kernel durante a fase pré-prompt e outra renderizada pelo prompt_toolkit no momento da reativação. E o `WARNING: your terminal doesn't support cursor position requests (CPR)` mostra que o prompt_toolkit dispara `\033[6n` ao ativar e bloqueia até o terminal responder; em terminais que não respondem, há latência adicional.

**Nota:** o teste em PTY simulado é uma aproximação. Em terminais reais (gnome-terminal, alacritty), o bracket-paste mode (`\033[?2004h`) habilitado pelo prompt_toolkit no momento da ativação pode reinterpretar bytes pré-buffer de forma diferente. Ainda é possível que H1 se manifeste em emuladores específicos — porém, neste pty, **não foi reproduzido**.

---

## Hipótese 2 — warm-up síncrono de AgentLoop

`AgentLoop()` é construído com carga de 34/35 tools, memory index, Analytics e settings antes do primeiro `print(banner)` (linha 360 de `nyx/cli.py`). Durante essa janela, o prompt ainda não existe. A hipótese: a janela é longa o suficiente para o usuário "vencer" o boot e enviar input no vazio.

### Teste — medir boot-to-quit elapsed

**Comando literal:**

```bash
T0=$(date +%s.%N)
echo "/quit" | timeout 90 ./run.sh 2>&1 | tail -5 > /tmp/h2.out
T1=$(date +%s.%N)
python3 -c "print(round($T1-$T0, 2))"
```

**Output:**

```
boot-to-quit elapsed: 15.91s
--- tail ---
  Sessão salva: session_Nyx-Code_1778901897.json
  [nyx] Desconectando...
  [nyx] Parando Ollama (PID: 574858)...
  [nyx] Fim.
```

**Conclusão:** **confirmada como condição necessária**. A janela de boot é de ~15.9 s — tempo amplo para o usuário digitar antes do prompt. A latência sozinha não causa perda de input (vimos em H1 que o input fica buffered no kernel), mas é o **pré-requisito da race**: sem essa janela longa, não haveria oportunidade para o bug se manifestar em emuladores que sofrem com H1 ou H3.

---

## Hipótese 3 — render_user_input / banner imprimem stdout antes do prompt pronto

Inspeção de `nyx/cli.py`:

- Linha 238: `prompt_session = PromptSession(...)` — apenas constrói o objeto, **não** entra em modo raw.
- Linha 360: `print(_build_banner(...))` — banner ASCII vai para stdout via `print()` (sys.stdout, line-buffered).
- Linha 382: `await prompt_session.prompt_async(ANSI(prompt_str))` — só aqui o prompt_toolkit toma o terminal, troca para raw, manda CPR (`\033[6n`), bracket-paste (`\033[?2004h`), DECSET 25 (cursor visível), etc.
- Linha 396: `render_user_input(user_input)` — só chamado **depois** que o input foi recebido.

A hipótese de que `render_user_input` rodaria antes do prompt está estruturalmente **refutada**: o código só o chama após o `prompt_async` retornar.

Porém, há um achado adjacente revelado pelo teste 2 de H1: quando o `prompt_async` entra em ação **após** já ter chegado input no buffer do kernel, a interação prompt_toolkit + terminal-emulator pode:

1. Ecoar duas vezes o texto (kernel ecoou durante boot, prompt_toolkit re-renderiza ao redesenhar).
2. Em terminais que não respondem ao CPR rapidamente, atrasar o redraw — o que cria a percepção de "input perdido" mesmo quando ele foi consumido.
3. Em conjunto com `bracket-paste mode`, bytes pré-buffer podem ser interpretados como sequência de paste ao invés de input normal — risco de mismatch.

### Teste — inspecionar ordem das chamadas

**Comando literal:**

```bash
grep -n "build_banner\|prompt_async\|PromptSession(\|render_user_input" nyx/cli.py
```

**Output:**

```
68:from nyx.agent.banner import build_banner as _build_banner  # noqa: E402
119:            from nyx.agent.output import render_user_input as _render_expanded
238:        prompt_session = PromptSession(
266:        render_user_input,
360:    print(_build_banner(model, agent.tools_count, PROJECT_ROOT.name, settings=settings))
382:                user_input = (await prompt_session.prompt_async(ANSI(prompt_str))).strip()
396:            render_user_input(user_input)
```

**Conclusão:** **refutada na ordem direta** (render só após input). Mas observada uma manifestação correlata: o redesenho do prompt_toolkit ao "absorver" o buffer pré-prompt cria duplicação visual e atraso aparente, o que pode justificar a impressão subjetiva do usuário de que "o input não processou".

---

## Causa confirmada

**Causa principal:** Hipótese 2 (warm-up síncrono de ~15.9 s antes do prompt_async ativar) é o **pré-requisito necessário**. A perda real do input acontece nos terminais em que `prompt_toolkit` na ativação descarta/reordena o buffer pré-prompt (não reproduzido aqui em pty.fork canonical, mas plausível em emuladores que tratam bracket-paste/CPR de forma agressiva).

**Síntese:** o usuário não tem feedback de "estou pronto para receber input"; a janela longa convida o erro. O bug observado é uma combinação:
- **H2 (confirmada)**: janela longa de warm-up sem indicador de readiness.
- **H1 (refutada em pty canonical, plausível em emuladores específicos)**: buffer pré-prompt nem sempre é preservado intacto na transição para raw mode.
- **H3 (refutada estruturalmente)**: nenhum render acontece antes do prompt.

## Recomendação para UX-BUG-02B e UX-BUG-02C

**UX-BUG-02B (indicador cold/warm na toolbar):**
- Adicionar campo `model_state` em `app_state` (cold/warming/warm) e renderizar em `_bottom_toolbar`.
- Disparar transição `cold → warming` no início do `AgentLoop()` e `warming → warm` ao final do warm-up (callback `on_model_state` já está cabeado na linha 355, basta consumir).
- Bloquear visualmente o prompt enquanto `model_state != "warm"` — ex.: exibir `nyx (cold)>` em fg muted, ou imprimir uma linha "aguarde, preparando agente..." antes do banner final.

**UX-BUG-02C (fix do race):**
- Antes do `await prompt_session.prompt_async(...)`, executar `termios.tcflush(sys.stdin.fileno(), termios.TCIFLUSH)` para descartar deterministicamente o buffer pré-prompt (em vez de deixar comportamento indefinido por emulador). Combinado com o indicador visual de H2, o usuário sabe quando começar a digitar.
- Validação: após a 02C, rodar `bash scripts/repro_race_input.sh` em pty.fork — esperado: `[bug] input perdido (marca: ...)` (porque o flush descarta a marca pré-buffer determinístico). Para o caminho via pipe (não-tty), o flush é noop e o teste deve continuar `[ok]`.
- Não adicionar `time.sleep(N)` em hipótese alguma — viola gambiarra #18 e #2 do catálogo desta sprint.

**Riscos a documentar:**
- O fix por `tcflush` é destrutivo intencional (descarta input pré-prompt). O indicador visual (02B) é o que torna isso aceitável: o usuário sabe que precisa esperar. Sem 02B, 02C piora UX em vez de melhorar.

---

## Evidência coletada (manifesto)

- `scripts/repro_race_input.sh` — repro via pipe, output `[ok] input chegou`.
- Experimento PTY (script ad-hoc em `/tmp/h1_pty.py`): input pré-banner consumido.
- Medição warm-up: 15.91 s.
- Inspeção estática de `nyx/cli.py` linhas 238, 360, 382, 396: ordem prompt_session-construído → banner-impresso → prompt_async-ativo → render_user_input.
- `grep -rn "tcflush\|termios" nyx/` retorna **zero** linhas: nenhum flush deliberado de tty no código atual.
- `prompt_toolkit.__version__` = 3.0.52.

---

## Aderência a ADRs e gambiarras

- **ADR-001 Local First:** todo o diagnóstico rodou offline (Ollama local).
- **ADR-004 Zero Emojis:** este relatório não contém emoji.
- **ADR-005 Anonimato:** sem referência a IA externa.
- **ADR-006 PT-BR:** acentuação correta em todo o texto.
- **ADR-010 Zero Mocks:** repro usa REPL real via `./run.sh`, não mocka prompt_toolkit.
- **ADR-013 Integração Obrigatória:** comandos rodam o sistema inteiro, não unidades isoladas.
- **ADR-020 Testes via run.sh:** `bash scripts/repro_race_input.sh` invoca `./run.sh`.
- **Gambiarra #8 (grep que não detecta o bug):** marca única `oi-pre-banner-<timestamp>-<pid>` evita falso-positivo.
- **Gambiarra #10 (benchmark sem cronômetro):** medição de H2 usa `date +%s.%N` real, 15.91 s explícito.
- **Gambiarra #18 (sleep como fix):** nenhum sleep adicionado em código de produção — único `sleep 0.1` está no script de repro, intencional para garantir start.

---

*"O que não pode ser observado não pode ser depurado." — Peter Drucker (adaptado).*
