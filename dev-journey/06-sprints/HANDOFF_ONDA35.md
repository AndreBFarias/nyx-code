# HAND-OFF — ONDA-35 (bugs de UX achados em USO REAL)

> Escrito 2026-05-30 por sessão anterior, ao fim da ONDA-34. Contexto de origem: o
> usuário usou a TUI de verdade (digitando no `--web`) e achou bugs que a validação
> "por injeção" (`/control/repl/send`) tinha mascarado. Esta onda corrige isso.

## Estado de partida (NÃO refazer)
- **ONDA-34 CONCLUIDA: sprints 283-302, pushed.** HEAD ao escrever: `69d7060`. `origin/main` 0/0.
- Invariantes 14/14 (com check #10 ruff estável "via ruff"), smoke OK, gauntlet rápido APROVADO.
- Docs públicos atualizados (CHANGELOG 1.3.0 + README seção TUI), commit `a97bd82`.
- Só drift do gauntlet (checkpoint.json, PROJECT_SNAPSHOT.md, baselines/) fica untracked — de propósito.

## LIÇÃO CRÍTICA DE VALIDAÇÃO (a causa de tudo isto)
A sessão anterior validou a TUI **injetando texto via `POST /control/repl/send`** + lendo o
buffer do xterm.js. Isso PROVA render, mas MASCARA: foco do input, corte de borda, echo de
digitação, comportamento de teclado. **VALIDE DIGITANDO DE VERDADE:**
- `--web`: via playwright, focar o terminal e usar `page.keyboard.type(...)` / `browser_press_key`
  (não só o control endpoint). Ex.: clicar no `#terminal`, digitar, ver o eco aparecer.
- terminal: `./run.sh` e (se possível) tmux send-keys, ou pedir ao usuário para confirmar.
- Sempre conferir os 2 caminhos (terminal E `--web`) — vários bugs só aparecem num deles.

## Mecânica `--web` + OOM (herdada, vale)
- `nohup ./run.sh --web > /tmp/log 2>&1 &` ; pollar `curl -sf http://127.0.0.1:11437/`.
- Encerrar: **matar por PID** (`pgrep -f "nyx.cockpit.server|nyx/cli.py --no-resume|nyx/proxy.py"` →
  kill nos PIDs; o cockpit respawna o cli, então mate o listener da :11437 com `ss -ltnp | grep 11437`).
  NUNCA `pkill -f "run.sh --web"` (mata o próprio shell — exit 144).
- GPU 4GB: uma inferência por vez. Modelo roda parcial em GPU (num_gpu=4), VRAM fica ~64 MiB.
- Validação visual headless sem OOM: Textual Pilot (`app.run_test`) → `save_screenshot` SVG →
  `rsvg-convert` PNG. Mas Pilot NÃO pega bugs de foco/teclado do path real — use digitação real.

## Protocolo de commit (herdado, OBRIGATÓRIO)
- Uma sprint por vez: diagnostica → corrige → valida (real, visual + digitação) → `./run.sh --smoke`
  + `bash scripts/sprint_invariants.sh` (14/14 FAIL=0) + `./run.sh --gauntlet --only rapido` (APROVADO)
  → entrada CONCLUIDA no `SPRINT_ORDER_MASTER.md` (bloco MANUAL_OVERRIDE) + spec em `concluidos/` →
  commit → push.
- Pré-check ANTES de commitar (.md/.sh): rodar o grep da wordlist do hook de acentuação (~16 termos PT-BR em -ção que o hook detecta quando vêm SEM acento) e corrigir acentuando. O pattern exato (lista entre parênteses) está nos comandos de commit das sprints da ONDA-34 — reusar de lá para não embutir os termos-gatilho aqui.
- Acentuação PT-BR completa (CLAUDE.md: nunca ASCII para palavra acentuada). `# noqa-anonimato` /
  `<!-- noqa-anonimato -->` para menção legítima a IA (ex.: "Claude Code" como port-origem).
- `nyx/agent/banner.py` (CLI legado) é #14-protegido; o widget `nyx/agent/tui/widgets/banner.py` NÃO é.
  Glifos sempre via `chr(0xNNNN)`. Após tocar qualquer coisa, confira #14 (CB/D0/CF >= 3 no invariants).

---

## SPRINTS ONDA-35 (próximo ID livre: 303)

### 303 — TUI-DONE-SUMMARY-CLEAN-01 (ALTA)
**Bug:** a resposta final do NyxCode aparece como o texto cru `done(summary="A versão... é 1.3.0.")`
em vez da frase limpa. Visto no chat real (`◆ NyxCode` seguido de `done(summary="...")`).
**Diagnóstico:** o `done` é uma ActionType (`_constants.py:21 ActionType.DONE`). O loop monta o
summary (`_iteration.py:95 is_done(name)`, `:225 add_tool_call("done", params, summary)`,
`_core.py:388 summary=final_content`). O conteúdo cru da ação chega ao chat provavelmente via o
streaming de tokens (`_on_token`) ou via render da tool call. **Investigar:** o `done(summary=...)`
que aparece é (a) conteúdo streamado do modelo (`_iteration.py:506 content`, `:529 collector`), ou
(b) render de tool call no TUI? Rastrear de onde o assistant recebe esse texto. **Fix esperado:** o
assistant deve exibir o `summary` limpo (o loop JÁ o tem). Não exibir a sintaxe `done(...)`.
**Aceite:** mandar "diga oi" → o chat mostra a resposta natural, sem `done(summary=...)` visível.

### 304 — COCKPIT-CHROME-CAPITALIZE-01 (BAIXA)
**Bug:** termos do chrome do cockpit em minúscula. **Locais exatos:**
- `nyx/cockpit/static/terminal.html:131` `cockpit / terminal` → `Cockpit / Terminal`
- `:132` `dashboard` → `Dashboard`
- `:147` `Ctrl+C cancela | Ctrl+D sai | redimensione livremente` → `Ctrl+C Cancela | Ctrl+D Sai | Redimensione livremente` (ou capitalizar a gosto, cada termo)
- `:232` `setStatus("connected", "conectado")` → `"Conectado"`
- `:339` `setStatus("error", "desconectado")` → `"Desconectado"`
- `nyx/cockpit/static/index.html:15` `cockpit / dashboard` → `Cockpit / Dashboard`; `:77` `'cancelar'` → `'Cancelar'`
**Aceite:** header/hint/status capitalizados no `--web`. Cuidado com `<!-- noqa-acento -->` onde houver.

### 305 — TUI-FOOTER-CAPITALIZE-TERMS-01 (BAIXA)
**Bug:** o footer/toolbar tem termos ainda minúsculos. A SPRINT 287 capitalizou Ctx/Iter/Lidos/Modif,
mas faltam: `○ cold` → `○ Cold` (e os outros estados de modelo: warming/warm/etc.) e
`shift+tab: normal/plan/sudo/bypass` → `Shift+Tab: Normal/Plan/Sudo/Bypass`. **Local:**
`nyx/agent/tui/widgets/toolbar.py` (render do footer). Grep por "cold"/"shift+tab"/"normal"/"plan".
**Aceite:** cada termo do footer capitalizado, validado no `--web` (ler buffer xterm.js linha do footer).

### 306 — TUI-INPUT-HEIGHT-5-SCROLL-01 (ALTA)
**Bug:** a área de input (a) aparece CORTADA (a borda inferior some — no `--web` o box fica ~2 linhas,
a borda de baixo é comida pela toolbar) e (b) o usuário pediu **5 linhas fixas** com **barra de
rolagem vertical interna** quando Ctrl+J passa de 5 linhas. **Estado atual:** `nyx/agent/tui/styles/nyx.tcss`
bloco `InputWidget { dock: bottom; height: auto; min-height: 3; max-height: 10; border: round $accent; }`.
**Fix esperado:** altura fixa de 5 linhas de conteúdo (atenção: `border: round` consome 2 linhas, então
o box ocupa ~7; garantir que a toolbar dock:bottom NÃO corte a borda inferior — pode precisar reservar
a altura ou ajustar a ordem/dock); overflow vertical com scrollbar interna no TextArea quando o conteúdo
passa de 5 linhas (Ctrl+J). **Investigar** se a borda some por conflito de dock com a Toolbar (h:1) — a
soma das alturas dock:bottom deve caber. **Aceite:** no terminal E no `--web`, o input mostra 5 linhas
com borda completa (topo+baixo); Ctrl+J além de 5 linhas → scrollbar interna, sem empurrar/cortar a toolbar.

### 307 — TUI-INPUT-AUTOFOCUS-01 (ALTA)
**Bug:** ao abrir, o input NÃO está focado — o usuário tem que clicar nele pra digitar; e enquanto
não focado, a digitação "não aparece no chat" (keystrokes vão pro vazio). Deveria iniciar pré-focado.
**Estado:** existe `TUI-FIX-INPUT-FOCUS-ON-MOUNT-01` (ONDA-33) que foca `#input` no `on_mount` (app.py),
mas NÃO surte efeito no `--web` (e talvez nem sempre no terminal). **Investigar:** `on_mount` pode rodar
ANTES do PTY/web conectar; tentar focar em `on_ready`/após o primeiro refresh, ou re-focar quando o
terminal recebe foco. No `--web` o xterm.js pode precisar encaminhar foco ao PTY. **Aceite:** abrir
`./run.sh` e `--web`, digitar IMEDIATAMENTE (sem clicar) → o texto aparece no input e submete no Enter.
**Validar DIGITANDO de verdade** (não injeção) — este bug é invisível à injeção.

### 308 — TUI-MODE-BEHAVIOR-01 (ALTA)
**Bug:** `Shift+Tab` cicla o LABEL do modo no footer (normal → plan → sudo → bypass) mas o
COMPORTAMENTO do agente é sempre "normal" — ele executa igual em qualquer modo. Intenção do usuário:
- **plan** = modo planejar (paridade com o plan mode de agentes de referência): o agente PLANEJA e
  NÃO executa — apresenta o plano antes de agir, sem efeitos colaterais / sem rodar tools que modificam estado.
- **sudo** = **bypass de permissão**: auto-aprova os prompts de permissão (equivale ao bypass).
- **bypass** = idem sudo (ou consolidar: sudo e bypass são o mesmo conceito de pular permissão —
  confirmar com o usuário se quer 3 modos {normal, plan, bypass} ou 4).
**Diagnóstico:** `app.py action_cycle_mode` (~L450) atualiza só o visual (classes `Toolbar.-plan/-sudo/-bypass`).
O modo NÃO é propagado ao `AgentLoop` nem ao `PermissionChecker` (`_core.py: self._permissions =
PermissionChecker()`). Provavelmente o NyxTUI nem passa o modo ao agente. **Fix esperado:** ligar o
estado de modo do footer ao comportamento do agente: plan → loop não executa (só planeja); bypass/sudo →
`PermissionChecker` auto-aprova (equivalente ao `NYX_AUTO_APPROVE`/`--auto-approve` já existente, ver
README seção "Modo automatizado" e `_permissions`). **Investigar** se há um modo plan no loop legado
(prompt_toolkit tinha SHIFT-TAB-CYCLE-01) que não foi religado na migração Textual. **Aceite:** em plan,
mandar uma tarefa de escrita → o agente apresenta plano sem escrever; em bypass, tools CONFIRM_ONCE
passam sem prompt; em normal, comportamento atual. Validar DIGITANDO + Shift+Tab de verdade.

### NÃO é bug (esclarecer ao usuário se voltar)
- "footer não aparece": era o estado **desconectado** (sessão morta). Conectado, o footer aparece
  (verificado: linha 58 do buffer no `--web`). Não há sprint para isto.

---

## Sugestão de ordem (por impacto no uso)
307 (autofoco — destrava digitar) → 306 (input 5 linhas, sem corte) → 308 (modes plan/bypass reais) →
303 (done limpo) → 305 (footer capitalizado) → 304 (chrome do cockpit). Cada uma: 1 por vez, validação
REAL (digitando no terminal E no `--web`), commit+push. Ao fim, atualizar CHANGELOG/README se algo
público mudar, e marcar ONDA-35 CONCLUIDA no MASTER.

## Resumo dos 8 achados → 6 sprints
- 303 done(summary=) cru · 304 capitalizar chrome cockpit · 305 capitalizar termos do footer ·
  306 input 5 linhas + scrollbar + corte da borda · 307 autofoco do input (hoje exige clique;
  "texto não aparece ao digitar" é consequência disto) · 308 modes Shift+Tab plan/sudo/bypass só
  cosméticos. "Footer não aparece" = era sessão desconectada, NÃO é bug.
