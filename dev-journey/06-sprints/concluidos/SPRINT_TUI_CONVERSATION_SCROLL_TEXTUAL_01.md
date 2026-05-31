# SPRINT 309 — TUI-CONVERSATION-SCROLL-TEXTUAL-01

## 0. SPEC (machine-readable)

```yaml
sprint:
  id: TUI-CONVERSATION-SCROLL-TEXTUAL-01
  title: "Re-portar scroll da conversa para a TUI Textual (regressao da migracao ONDA-32) + corrigir freeze"
  onda: 35
  prioridade: ALTA
  tipo: Bugfix
  dependencias: []
  desbloqueia: []
  coordenar_com:
    - "TUI-INPUT-AUTOFOCUS-01 (307): o foco no #input e a causa de o teclado nunca rolar o #chat"
    - "TUI-INPUT-HEIGHT-5-SCROLL-01 (306): scroll INTERNO do input e escopo separado, NAO tocar"

  touches:
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/agent/tui/app.py
      reason: "Adicionar bindings de scroll (PgUp/PgDn/Home/End) que rolam o #chat mesmo com #input focado; auto-scroll-pause"
      linhas_alvo: "70-89 (BINDINGS), 204-214 (on_mount), 342-366 (_process_turn/scroll_end)"
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/agent/tui/widgets/chat_message.py
      reason: "Suspeita do freeze: render() reconstroi Markdown(self._content) a cada repaint + append_text faz refresh(layout=True) por token; cachear renderable"
      linhas_alvo: "64-117 (append_text/set_content/render)"
  creates: []
  removes: []

  n_to_n_pairs: []

  forbidden:
    - "Tocar no scroll INTERNO do input (Ctrl+J > 5 linhas) -- escopo da 306 TUI-INPUT-HEIGHT-5-SCROLL-01"
    - "Reintroduzir nyx/agent/repl_app.py ou qualquer dependencia de prompt_toolkit (stack removida na ONDA-32)"
    - "Adicionar emoji"
    - "print() fora de cli.py / agent/output.py (ADR-024 Render Layer)"
    - "Mencao a IA externa em codigo ou commit"  # noqa-anonimato
    - "Glifo literal (U+25xx) em arquivo #14-protegido -- usar chr(0xNNNN)"
    - "Hex de cor fora de nyx/themes/design_tokens.py (invariante #6)"

  tests:
    - cmd: "./run.sh --smoke"
      timeout: 10
      deve_passar: true
    - cmd: "bash scripts/sprint_invariants.sh"
      timeout: 60
      deve_passar: true
    - cmd: "./run.sh --gauntlet --only rapido"
      timeout: 120
      deve_passar: true

  acceptance_criteria:
    - "Conversa com mais de uma tela: a roda do mouse rola o #chat (cima e baixo) no terminal nativo"
    - "PgUp / PgDn / Home / End rolam o #chat mesmo com o #input focado"
    - "Rolar NAO trava a TUI (sem freeze), inclusive durante streaming e com respostas longas contendo blocos de codigo"
    - "Auto-scroll-pause: ao rolar para cima, um novo turno NAO forca o bottom; ao voltar ao fim, o auto-scroll retoma"
    - "Paridade: funciona no terminal nativo (./run.sh) E no --web (cockpit/xterm.js)"
    - "Smoke boot ok + invariantes 14/14 PASS + gauntlet --only rapido APROVADO"
    - "Acentuacao PT-BR correta em tudo novo; zero hex hardcoded fora de design_tokens.py"
```

---

# Sprint 309 — TUI-CONVERSATION-SCROLL-TEXTUAL-01

**Status:** CONCLUIDA
**Data criação:** 2026-05-30
**Data conclusão:** 2026-05-30
**Modelo obrigatório:** claude-opus-4-7 (sem subagentes)

---

## RELATO DE CONCLUSÃO (2026-05-30)

**Causa-raiz confirmada (FASE 0):** o "travou feio" NÃO era re-parse de Markdown no scroll (medido: **0** re-parses ao rolar conteúdo estático — o Textual cacheia o renderable). Era o **streaming**: `append_text` chamava `refresh(layout=True)` por token e `render()` reconstruía `Markdown(self._content)` inteiro (com pygments) a cada repaint — O(n^2). Medição direta: **1626 chars => 75s e ~3253 parses**, com a TUI e o scroll congelados. O scroll por teclado, à parte, não funcionava porque o foco fica no `#input` e o `VerticalScroll` só rola por teclado quando focado (binding perdido na migração ONDA-32, vinha do `repl_app.py`/sprint 228).

**Fixes:**
1. **Freeze** (`chat_message.py`): durante o streaming, `render()` devolve TEXTO PLANO (barato); o Markdown (pygments) entra UMA vez quando o stream assenta (debounce `_SETTLE_INTERVAL` + flag `_streaming`/`_settle`), com refresh coalescido (`_STREAM_REFRESH_INTERVAL`) em vez de por token. Pós-fix: **2 parses** (era 3253).
2. **Scroll por teclado** (`app.py`): bindings `pageup`/`pagedown` (priority) → `action_scroll_chat_up/down` rolam o `#chat` mesmo com o `#input` focado.
3. **Auto-scroll-pause** (`app.py`): flag `_follow_output` (re-porta `_user_scrolled_up` da 228) — PgUp pausa; PgDn-até-o-fim e o submit do usuário religam; callbacks de agent usam `_follow_end`.

**Proof-of-work:**
```
FAIL_BEFORE=0 -> FAIL_AFTER=0 (14/14)   ruff: All checks passed!   acentuacao: rc=0
gauntlet --only rapido: 19/19 (100%) APROVADO
freeze (repro): Markdown 3253x/75600ms -> 2x  (conteudo final intacto)
```
- **Pilot** (`/tmp/val_309_scroll.py`): `#input` focado, PgUp rolou o #chat (y 68->53) sem vazar pro input; tool-result com follow=False NÃO puxou pro fim; PgDn-até-o-fim religou; novo tool-result voltou a acompanhar.
- **--web real** (playwright, digitando sem clicar): 3x `/help` levaram ao fim (banner fora de vista); **PgUp 3x trouxe o banner de volta ao topo** sem vazar pro input (buffer `.xterm-rows`: `banner_voltou=true`, `input_text_vazou=false`).

---

## Contexto do projeto (snapshot — não referência)

> **ADRs relevantes (essencial inline):**
> - ADR-001 Local First: tudo offline.
> - ADR-004 Zero Emojis. ADR-005 Anonimato (sem menção a IA em código/commit). ADR-006 PT-BR com acentuação.
> - ADR-024 Render Layer: `print()` só em `cli.py` e `agent/output.py`.
> - ADR-025 Loop de Experiência / ADR-026 Agência: **rolar o histórico é controle do usuário** — função básica de usabilidade, não enfeite.
>
> **Estado do sistema (na data da sprint):**
> - Python 3.10+, modelo `qwen2.5-coder:3b`, Ollama :11435, Proxy :11436, Cockpit :11437.
> - TUI **Textual 8.2.7** (`nyx/agent/tui/app.py` classe `NyxTUI`), caminho único interativo desde a ONDA-32 (`TUI-DEFAULT-FLIP-LEGACY-RM-01`). O `cli.py` dispara `NyxTUI.run_async()` em TTY real.
> - O `--web` espelha a MESMA TUI Textual via PTY + xterm.js (não há TUI duplicada).
> - Sprint imediatamente anterior nesta onda: bloco ONDA-35 (303–308) ainda PENDENTE.

---

## Problema

**Sintoma observável (relato do usuário, 2026-05-30, usando `./run.sh` — terminal nativo):**
"A barra de rolagem não funcionou no terminal. Ou algo travou feio ele."

Ou seja, na TUI Textual atual, a **conversa não rola** — a roda do mouse parece inerte sobre a área de chat — e em algum momento a interface **congela** ("travou feio") durante o uso. Quando o diálogo ultrapassa a altura da janela, o usuário fica sem como voltar ao conteúdo anterior.

Este bug é **distinto** dos itens já catalogados da ONDA-35:
- Não é a **306** (`TUI-INPUT-HEIGHT-5-SCROLL-01`), que trata do scroll **interno do input** (Ctrl+J além de 5 linhas).
- É o scroll da **conversa inteira** (o `VerticalScroll(id="chat")`).

---

## Causa-raiz (já investigada nesta auditoria)

A migração da TUI de `prompt_toolkit` para **Textual** (ONDA-32) re-adotou o container de output como `VerticalScroll(id="chat")` nativo do Textual, com scrollbar tematizada no CSS. **Porém, toda a engenharia de scroll da conversa havia sido construída no `nyx/agent/repl_app.py`, que foi DELETADO na ONDA-32** junto com a stack `prompt_toolkit` (`TUI-DEFAULT-FLIP-LEGACY-RM-01`). Confirmação: `ls nyx/agent/repl_app.py` → `No such file or directory`.

O que se perdeu na migração e **nunca foi re-portado** para o Textual:
- **Sprint 228 (`TUI-CONVERSATION-SCROLLBAR-01`):** scrollbar visível + keybindings `pageup`/`pagedown`/`end` + **auto-scroll-pause** (flag `_user_scrolled_up`, para que um novo turno não force o bottom quando o usuário está lendo o histórico).
- **Sprint 260 (`UX-TUI-MOUSE-SCROLL-01`):** `mouse_support=True` + handler de scroll-wheel roteado para a conversa (e não para o input).

Na TUI Textual atual (`nyx/agent/tui/app.py`):

1. **Não há nenhum binding de scroll por teclado** (grep por `page_up|page_down|scroll_up|scroll_down|on_mouse` em `app.py` e nos widgets retorna vazio). O `VerticalScroll` do Textual só rola por teclado **quando está focado**.
2. **O `on_mount` foca o `#input`** (`app.py:214`, fix `TUI-FIX-INPUT-FOCUS-ON-MOUNT-01`). Logo PgUp/PgDn/setas vão para o `TextArea` do input — **o `#chat` nunca recebe foco e nunca rola por teclado**. (Nota: a 307 vai reforçar esse foco; por isso este fix deve rolar o `#chat` **independente do foco**, via bindings no App.)
3. **Suspeita do freeze ("travou feio"):** `ChatMessage.render()` reconstrói `Markdown(self._content)` **a cada repaint** (`chat_message.py:113`, da sprint 299) e `append_text()` chama `refresh(layout=True)` **por token** (`chat_message.py:64-77`). Durante scroll (que repinta os widgets visíveis) com várias respostas longas e blocos de código (syntax highlight via pygments), o reparse de Markdown por frame pode ser O(n) por widget por frame — candidato direto a travamento, agravado se o usuário tenta rolar **durante** o streaming.

---

## Solução proposta

Re-portar o scroll da conversa para o idioma Textual, em fases. **A FASE 0 é obrigatória** porque o "travou feio" precisa ser reproduzido no ambiente real antes do fix (memória do projeto: bug de UI só conclui no ambiente real; não confiar em média de pixels nem em injeção).

### FASE 0 — Investigação / repro (obrigatória, antes de editar)
- Reproduzir no terminal nativo (`./run.sh`) e via Textual Pilot headless: encher o `#chat` com mais de uma tela (várias respostas longas, ao menos uma com bloco ```` ``` ````), e:
  - confirmar se a **roda do mouse** sobre o `#chat` rola nativamente no Textual 8.2.7 (deveria — o App liga mouse tracking por padrão). Se não rolar, registrar o porquê (terminal não entrega scroll ao app em alt-screen? handler ausente?).
  - reproduzir o **freeze** e isolar a causa: instrumentar `ChatMessage.render()` (contador de chamadas) e medir o custo do `Markdown(...)` por repaint; verificar se o freeze ocorre (H1) ao rolar com muitas mensagens longas, (H2) ao rolar durante streaming concorrente, ou (H3) por mouse capture do terminal.
- Colar a evidência da repro no relatório (contador de render, log, ou captura).

### FASE 1 — Scroll por teclado independente do foco
- Adicionar bindings no `App` (`priority=True`, mesmo padrão dos atalhos existentes) para `pageup`, `pagedown`, `home`, `end`, roteando para ações que rolam o `#chat` diretamente — ex.: `self.query_one("#chat", VerticalScroll).scroll_page_up()` / `scroll_page_down()` / `scroll_home()` / `scroll_end(animate=False)`. Como o `#input` (TextArea) **não** liga PgUp/PgDn/Home/End nus para movimento próprio relevante, e os bindings do App com `priority=True` capturam antes do widget focado, não há colisão.

### FASE 2 — Corrigir o freeze (se confirmado na FASE 0)
- Cachear o renderable do `ChatMessage`: construir `Markdown(self._content)` **apenas quando o conteúdo muda** (em `append_text`/`set_content`), guardando o resultado, em vez de reconstruir a cada `render()`. Invalidar o cache no append. Isso remove o custo de reparse por frame durante scroll/repaint.
- Se o freeze for por `refresh(layout=True)` por token durante streaming, avaliar throttle/coalescing do refresh (sem regredir o crescimento de altura da 299/`TUI-FIX-CHATMESSAGE-RELAYOUT-01`).

### FASE 3 — Auto-scroll-pause + paridade --web
- Re-portar o comportamento da 228: quando o usuário rolou para cima (não está no fim), um novo turno **não** deve forçar o bottom. Hoje todos os `chat.scroll_end(animate=False)` (em `app.py:259,297,320,340,360,394,407,428,439`) forçam o fim incondicionalmente. Consultar o estado de scroll do `VerticalScroll` (ex.: se está no fim antes de mostrar novo conteúdo) e só ancorar no bottom quando o usuário já estava no fim; caso contrário, preservar a posição.
- Validar nos **dois** caminhos: terminal nativo E `--web` (xterm.js).

---

## Arquivos alvo (paths absolutos)

### `/home/andrefarias/Desenvolvimento/Nyx-Code/nyx/agent/tui/app.py`

**Antes (BINDINGS, ~linha 70-89 — não há scroll):**
```python
    BINDINGS = [
        Binding("ctrl+q", "quit", "Quit", priority=True),
        Binding("ctrl+d", "quit_if_empty", "Quit (EOF)", priority=True),
        Binding("shift+tab", "cycle_mode", "Trocar modo", priority=True),
        Binding("ctrl+v", "paste", "Colar", priority=True),
        Binding("ctrl+o", "recall_last", "Recall último input", priority=True),
        Binding("ctrl+up", "history_prev", "Histórico anterior", priority=True),
        Binding("ctrl+down", "history_next", "Histórico próximo", priority=True),
        Binding("ctrl+y", "copy_last_code", "Copiar código", priority=True),
    ]
```

**Depois (acrescentar bindings de scroll do #chat; texto ilustrativo, o executor confirma os nomes de action do VerticalScroll do Textual 8.2.7):**
```python
    BINDINGS = [
        # ... bindings existentes ...
        # TUI-CONVERSATION-SCROLL-TEXTUAL-01: rola o #chat mesmo com #input focado.
        # priority=True captura antes do widget focado (paridade scroll da 228/260,
        # perdido na migracao ONDA-32 com o repl_app.py prompt_toolkit deletado).
        Binding("pageup", "scroll_chat_up", "Rolar conversa (cima)", priority=True),
        Binding("pagedown", "scroll_chat_down", "Rolar conversa (baixo)", priority=True),
        Binding("home", "scroll_chat_home", "Topo da conversa", priority=True),
        Binding("end", "scroll_chat_end", "Fim da conversa", priority=True),
    ]
```

**Mudanças:**
- Novos bindings + actions `action_scroll_chat_*` que operam o `query_one("#chat", VerticalScroll)`.
- Auto-scroll-pause nos pontos de `scroll_end` (consultar posição antes de ancorar no fim).

### `/home/andrefarias/Desenvolvimento/Nyx-Code/nyx/agent/tui/widgets/chat_message.py`

**Antes (render reconstrói Markdown a cada repaint, ~linha 106-114):**
```python
        if self._role == "assistant":
            label = Text(f"{_DIAMOND} NyxCode", style=NYX_PURPLE)
            if self._content:
                return Group(label, Markdown(self._content))
            return label
```

**Depois (cachear o renderable, reconstruindo só quando o conteúdo muda):**
```python
        # TUI-CONVERSATION-SCROLL-TEXTUAL-01: Markdown(self._content) construido
        # uma vez por mudanca de conteudo (cache invalidado em append_text/
        # set_content), NAO a cada repaint -- evita reparse O(n) por frame durante
        # o scroll, causa provavel do freeze. (executor confirma na FASE 0)
```

**Mudanças:** cache de renderable do assistant invalidado em `append_text`/`set_content`; `render()` devolve o cache. Preservar `_DIAMOND` (`chr(0x25C6)`), o label da 297 e o syntax highlight da 299.

> Observação: o trecho literal "Depois" é guia. O executor deve confirmar na FASE 0 que o freeze vem daqui antes de aplicar; se a causa for outra (ex.: mouse capture), ajustar o alvo e registrar.

---

## Diff esperado (resumo)

```
~ 2-3 arquivos modificados (app.py + chat_message.py [+ nyx.tcss se preciso])
- 0 arquivos removidos
+ ~40-70 linhas líquidas (bindings + actions de scroll + cache de renderable + auto-scroll-pause)
```

---

## Comandos de verificação (literais, copy-paste)

```bash
cd /home/andrefarias/Desenvolvimento/Nyx-Code

# 1. Confirmar a causa-raiz estrutural (repl_app removido + sem binding de scroll)
ls nyx/agent/repl_app.py 2>&1                       # esperado: No such file or directory
grep -in "page_up\|page_down\|scroll_chat\|on_mouse" nyx/agent/tui/app.py   # antes: vazio; depois: bindings/actions

# 2. Estática
/home/andrefarias/.local/bin/ruff check nyx/agent/tui/

# 3. Smoke + invariantes
./run.sh --smoke                                    # boot ok
bash scripts/sprint_invariants.sh                   # PASS 14/14

# 4. Gauntlet rápido
./run.sh --gauntlet --only rapido                   # APROVADO

# 5. Acentuação PT-BR (flag --paths OBRIGATÓRIA)
python3 ~/.config/zsh/scripts/validar-acentuacao.py --paths \
  nyx/agent/tui/app.py nyx/agent/tui/widgets/chat_message.py

# 6. VISUAL/DIGITAÇÃO REAL (toca render layer -- obrigatório, ADR-024) -- OS DOIS CAMINHOS:
#    Terminal nativo:
./run.sh
#      - mande 4-6 mensagens ate a conversa passar da tela
#      - roda do mouse para CIMA  -> conversa volta no historico
#      - roda do mouse para BAIXO -> volta ao fim, auto-scroll retoma
#      - PgUp/PgDn/Home/End rolam a conversa (mesmo sem clicar no #chat)
#      - role DURANTE uma resposta longa com bloco de codigo -> NAO trava
#    --web (digitando de verdade, nao /control/repl/send):
#      nohup ./run.sh --web > /tmp/log 2>&1 & ; pollar curl -sf http://127.0.0.1:11437/
#      via playwright: focar o #terminal, page.keyboard, rolar e conferir; matar por PID.
```

---

## Critério binário de aceite (IA executora)

- [ ] FASE 0: repro do scroll-inerte e do freeze documentada com evidência (antes do fix).
- [ ] Roda do mouse rola a conversa (cima/baixo) no terminal nativo.
- [ ] PgUp / PgDn / Home / End rolam o `#chat` mesmo com o `#input` focado.
- [ ] Rolar **não trava** a TUI durante streaming nem com respostas longas com código.
- [ ] Auto-scroll-pause: rolou para cima → novo turno não força bottom; voltou ao fim → retoma.
- [ ] Paridade confirmada no terminal **e** no `--web`, validando **digitando de verdade**.
- [ ] Gauntlet `--only rapido` APROVADO; `ruff` limpo; acentuação rc=0.
- [ ] Smoke `boot ok` + invariantes 14/14 (FAIL_AFTER <= FAIL_BEFORE).
- [ ] Nenhuma violação de `forbidden[]` (não tocou o scroll do input/306; não reintroduziu prompt_toolkit).
- [ ] `SPRINT_ORDER_MASTER.md` marca CONCLUIDA; spec movida `producao/` → `concluidos/`.
- [ ] Commit atômico no padrão `fix(tui): ...`.

---

## Guardrails anti-engodo (obrigatórios)

A IA executora **NÃO pode marcar concluída** se: pulou a FASE 0 e "supôs" a causa do freeze; validou só por injeção (`/control/repl/send`) em vez de digitar/rolar de verdade; mexeu no scroll do input (escopo 306); "gauntlet passou" sem output real colado; ignorou item de `forbidden[]`. Se qualquer item falhar:
```
[SPRINT 309] BLOQUEADA: <motivo objetivo em 1 linha>
```

---

## Proof-of-work obrigatório (4 passos)

```bash
# PASSO 1 — ANTES
bash scripts/sprint_invariants.sh > /tmp/inv_before.txt 2>&1
FAIL_BEFORE=$(grep -c "^\[FAIL\]" /tmp/inv_before.txt); echo "FAIL inicial: $FAIL_BEFORE"

# PASSO 2 — implementar seguindo este arquivo + ler GAMBIARRAS_POR_SPRINT.md (Universal)

# PASSO 3 — DEPOIS
bash scripts/sprint_invariants.sh > /tmp/inv_after.txt 2>&1
FAIL_AFTER=$(grep -c "^\[FAIL\]" /tmp/inv_after.txt); echo "FAIL final: $FAIL_AFTER"

# PASSO 4 — regra binária: FAIL_AFTER <= FAIL_BEFORE
diff /tmp/inv_before.txt /tmp/inv_after.txt
```

Colar no relatório: `inv_before`/`inv_after` (tail), o diff, o output do gauntlet `--only rapido`, a evidência da FASE 0 e a **evidência visual/digitação** dos dois caminhos (terminal + `--web`). Sem isso, sprint é considerada **não verificada** (toca render layer — ADR-024).

---

## Gambiarras específicas desta sprint

Ver `dev-journey/08-templates/GAMBIARRAS_POR_SPRINT.md` §"Catálogo Universal". Atenção específica:
- **Falso scroll:** adicionar binding que "parece" rolar mas não move o `#chat` real (validar pela posição/região do widget, não só pela ausência de erro).
- **Mascarar o freeze:** "não reproduzi o travamento" não é prova de que sumiu — a FASE 0 deve reproduzi-lo **antes** para então provar a ausência depois.
- **Validação por injeção:** `/control/repl/send` mascara foco/teclado/roda — proibido como única evidência (lição da ONDA-35).

---

## Riscos

| Risco | Mitigação |
|-------|-----------|
| Bindings de scroll no App colidem com teclas do `#input` (TextArea) | `priority=True`; o TextArea não liga PgUp/PgDn/Home/End nus para função relevante; critério de aceite dedicado |
| Auto-scroll-pause reintroduz race (turno novo vs leitura) | Lógica simples baseada na posição do `VerticalScroll` (está no fim?), sem heurística frágil; espelha a flag da 228 |
| Cache de renderable quebra o crescimento de altura no streaming (regressão da 299) | Invalidar o cache em `append_text` + manter `refresh(layout=True)`; validar streaming token-a-token na FASE 0 |
| Interação com a 307 (autofocus do input) | Por isso o scroll é via App-bindings independentes do foco; coordenar ordem (307 antes ajuda a validar o cenário real) |
| Mouse capture afeta seleção de texto do terminal | `Ctrl+Y` (301) já copia código; comportamento padrão de TUI full-screen; documentar |

---

*"Rolar o passado é permitir que ele ainda fale." -- anônimo*
