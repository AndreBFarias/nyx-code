# SPRINT 260 — UX-TUI-MOUSE-SCROLL-01

## 0. SPEC (machine-readable)

```yaml
sprint:
  id: UX-TUI-MOUSE-SCROLL-01
  title: "Roda do mouse rola a conversa na TUI nativa"
  onda: 31
  prioridade: MÉDIA
  tipo: Bugfix
  dependencias: []
  desbloqueia: []
  coordenar_com: [UX-COCKPIT-FLASH-PRETO-01]   # 249 toca o mesmo núcleo repl_app.py

  touches:
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/agent/repl_app.py
      reason: "Application criada com mouse_support=False; output_window precisa receber scroll-wheel"
      linhas_alvo: "535-542 (output_window) + 575-581 (Application)"
  creates: []
  removes: []

  forbidden:
    - "Quebrar os keybindings de scroll por teclado (PgUp/PgDn/End da sprint 228)"
    - "Fazer a roda do mouse rolar o input_window em vez da conversa"
    - "Adicionar emoji"
    - "print() fora de cli*.py/output.py"
    - "Menção a IA externa"
    - "Regredir a seleção de texto a ponto de inviabilizar copiar a resposta"

  tests:
    - cmd: "./run.sh --gauntlet --only rapido"
      timeout: 120
      deve_passar: true
    - cmd: "python -m nyx.agent.repl_app --self-test"
      timeout: 30
      deve_passar: true

  acceptance_criteria:
    - "Roda para cima rola a conversa (output_window) para trás no histórico"
    - "Roda para baixo retorna em direção ao fim; ao chegar no bottom, retoma auto-scroll"
    - "Roda NÃO rola o input_window nem move o cursor do input"
    - "PgUp/PgDn/End continuam funcionando (sprint 228 preservada)"
    - "Smoke boot ok + invariantes 14/14 + ruff limpo + acentuacao rc=0"
```

---

**Status:** CONCLUIDA (estrutural — validação visual real pendente no orquestrador via TTY/`./run.sh --web`)
**Data criação:** 2026-05-26
**Data conclusão:** 2026-05-26
**Modelo obrigatório:** claude-opus-4-7 (sem subagentes)

---

## Contexto do projeto (snapshot — não referência)

> - ADR-001 Local First, ADR-004 Zero Emojis, ADR-006 PT-BR, ADR-024 Render Layer, ADR-025 Loop de Experiência (feedback contínuo, "sense of agency").
> - TUI default = `prompt_toolkit` Application `full_screen` em `nyx/agent/repl_app.py`. O caminho Textual (`nyx/agent/tui/`) é opt-in via `NYX_TUI_TEXTUAL=1`.
> - Scroll por teclado (PgUp/PgDn/End) + `ScrollbarMargin` visível foram entregues na sprint 228 (`TUI-CONVERSATION-SCROLLBAR-01`), com auto-scroll-pause via `app_state["_user_scrolled_up"]` + `_output_scroll_offset`. Scroll por mouse nunca foi habilitado.

---

## Problema

Reportado em 2026-05-26 rodando `./run.sh` (TUI nativa). A roda do mouse não rola a conversa — nem para cima nem para baixo. Quando o diálogo ultrapassa a altura da janela (evidência: 3 turnos já empurram o banner para fora do topo), o usuário não consegue voltar com o mouse; só com PgUp/PgDn — atalho que a maioria não descobre.

Sintoma observável: girar a roda do mouse sobre a área de conversa não tem efeito algum.

---

## Causa-raiz

`nyx/agent/repl_app.py:580` constrói a `Application` com `mouse_support=False`. Sem captura de mouse, o `prompt_toolkit` não recebe eventos de scroll-wheel; e como a app roda em `full_screen=True` (alternate screen), não existe scrollback nativo do terminal para o wheel rolar. Resultado: roda inerte. O único scroll disponível é o keyboard binding da sprint 228 (`@kb.add("pageup")`/`pagedown`/`end` em `repl_app.py:466-488`).

---

## Solução proposta

**Fase 1 — investigação (obrigatória antes do fix):**

- Ligar `mouse_support=True` num branch de teste e confirmar via `--self-test` + captura tmux: (a) o wheel passa a gerar eventos; (b) por padrão o `prompt_toolkit` rola o Window sob o cursor ou o focado — determinar qual, pois o foco vive no `input_window`.
- Medir o impacto na seleção de texto do terminal (arrastar para selecionar): documentar se passa a exigir Shift.

**Fase 2 — fix:**

- `mouse_support=True` na Application.
- Garantir que a roda role o **output_window** (a conversa), não o input. Reaproveitar as actions já existentes da sprint 228 (`_scroll_up_output` / `_scroll_down_output`) — via mouse handler no `output_window` (ou `BufferControl`/`Window` mouse-handler do `prompt_toolkit`) que dispara o mesmo caminho de `_output_scroll_offset` + `_user_scrolled_up`, OU confirmar que o roteamento nativo (scroll sobre a janela apontada) já basta.
- Manter `_user_scrolled_up` / `_output_scroll_offset` coerentes (mesma flag de auto-scroll-pause da 228): roda-para-cima seta `_user_scrolled_up=True`; voltar ao bottom zera o offset e retoma o auto-scroll.

---

## Arquivos alvo (paths absolutos)

### `/home/andrefarias/Desenvolvimento/Nyx-Code/nyx/agent/repl_app.py`

**Antes (linha ~575):**
```python
    app: Application = Application(
        layout=layout,
        key_bindings=kb,
        full_screen=True,
        style=_build_style(),
        mouse_support=False,
    )
```

**Depois (alvo mínimo; mouse handler do output_window pode somar conforme Fase 1):**
```python
    app: Application = Application(
        layout=layout,
        key_bindings=kb,
        full_screen=True,
        style=_build_style(),
        mouse_support=True,  # UX-TUI-MOUSE-SCROLL-01: roda rola a conversa
    )
```

**Mudanças:** habilitar `mouse_support` + (se a Fase 1 indicar que o wheel rola o input ou nada) anexar mouse handler de scroll ao `output_window` roteando para `_scroll_up_output`/`_scroll_down_output`.

---

## Trade-off / risco

| Risco | Mitigação |
|-------|-----------|
| `mouse_support=True` captura seleção de texto do terminal (arrastar pode exigir Shift) | `/copy` (xclip) já copia a última resposta; documentar Shift+seleção; é o trade-off padrão de TUI full-screen |
| Roda rolar o `input_window` (focado) em vez da conversa | Mouse handler explícito no `output_window` + critério de aceite dedicado |
| Conflito com o refactor in-app da 249 (mesmo arquivo, núcleo do REPL) | Coordenar ordem; a mudança aqui é localizada na construção da Application. Se a 249 entrar primeiro, revalidar este scroll depois |

---

## Comandos de verificação (literais, copy-paste)

```bash
# 1. Estática
/home/andrefarias/.local/bin/ruff check nyx/agent/repl_app.py

# 2. Self-test do módulo (sem TTY)
./venv/bin/python -m nyx.agent.repl_app --self-test

# 3. Gauntlet rápido
./run.sh --gauntlet --only rapido

# 4. Manual (TTY real) — evidência visual obrigatória (toca render layer)
./run.sh
#   - mande 3-4 mensagens ate a conversa passar da tela
#   - role a roda do mouse para CIMA  -> conversa volta no historico
#   - role para BAIXO                 -> volta ao fim, auto-scroll retoma
#   - confirme que o input embaixo NAO rola com a roda
#   - PgUp/PgDn/End continuam funcionando

# 5. Acentuação PT-BR (flag --paths obrigatoria)
python3 ~/.config/zsh/scripts/validar-acentuacao.py --paths nyx/agent/repl_app.py
```

---

## Critério binário de aceite

- [ ] Roda para cima rola a conversa para trás no histórico
- [ ] Roda para baixo retorna ao bottom + retoma auto-scroll no fim
- [ ] Roda não move/rola o input
- [ ] PgUp/PgDn/End preservados (sprint 228)
- [ ] `./run.sh --gauntlet --only rapido` 100%
- [ ] smoke `boot ok` + invariantes 14/14
- [ ] ruff limpo, acentuação rc=0
- [ ] captura tmux/scrot anexada mostrando a conversa rolando com a roda
- [ ] spec movida `producao/` -> `concluidos/`

---

## Proof-of-work obrigatório

Snapshot de invariantes antes/depois (`scripts/sprint_invariants.sh`, `FAIL_AFTER <= FAIL_BEFORE`) + output bruto do `--self-test` + output do gauntlet `--only rapido` + **captura visual** (tmux/scrot) provando o scroll com a roda. Sem a evidência visual, sprint é considerada não verificada (toca render layer — ADR-024).

---

*"Rolar o passado é permitir que ele ainda fale." -- anônimo*
