## 0. SPEC (machine-readable)

```yaml
sprint:
  id: TUI-TEXTUAL-MIGRATION-PLAN-01
  title: "Planejamento ONDA-30: migrar TUI Nyx-Code de prompt_toolkit para Textual (estilo Luna)"
  onda: 30
  prioridade: ALTA
  tipo: Brainstorm
  dependencias: [TUI-BLINK-SOFT-REVERT-01]
  desbloqueia: [TEXTUAL-SCAFFOLD-01, TEXTUAL-OUTPUT-WIDGET-01, TEXTUAL-INPUT-WIDGET-01, TEXTUAL-BANNER-WIDGET-01, TEXTUAL-TOOLBAR-01, TEXTUAL-CUTOVER-01]

  touches:
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/dev-journey/06-sprints/producao/SPRINT_TUI_TEXTUAL_MIGRATION_PLAN_01.md
      reason: "Este próprio spec — documento de planejamento da ONDA-30"
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/dev-journey/06-sprints/SPRINT_ORDER_MASTER.md
      reason: "Registrar ONDA-30 com sub-sprints filhas em PENDENTE"

  creates: []
  removes: []

  forbidden:
    - "Implementar código nesta sprint — é DOC ONLY (planejamento)"
    - "Despachar executor para criar Textual app real — fica para sub-sprints filhas (196+)"

  tests:
    - cmd: "test -f dev-journey/06-sprints/producao/SPRINT_TUI_TEXTUAL_MIGRATION_PLAN_01.md"
      timeout: 5
      deve_passar: true

  acceptance_criteria:
    - "Este spec existe e contém: motivação, arquitetura proposta, fases (sub-sprints), riscos, critérios de paridade"
    - "MASTER atualizado com bloco MANUAL_OVERRIDE_ONDA_30 + sub-sprints 196-201 PENDENTE"
    - "Plano canônico salvo em ~/.claude/plans/ (opcional, fora do repo)"
```

---

# Sprint TUI-TEXTUAL-MIGRATION-PLAN-01 — Planejamento ONDA-30

**Status:** PENDENTE
**Data criação:** 2026-05-22
**Modelo obrigatório:** claude-opus-4-7 (sem subagentes)

---

## Motivação

A TUI atual do Nyx-Code usa `prompt_toolkit.Application` em alternate-screen com layout HSplit, output_buffer central e `app.invalidate()` global. Essa arquitetura sofre de **race conditions** entre tasks concorrentes (streaming + animações + input) que provocam flicker observável.

Histórico:
- Sprint 187 (BANNER_BLINK_SOFT_03) tentou adicionar blink suave do cursor — introduziu flicker pesado, foi revertida (sprint 193 BLINK_SOFT_REVERT_01).
- Diagnóstico da Explore agent confirmou: cada `app.invalidate()` refaz tela inteira; com múltiplas tasks editando o buffer central, repaints sobrepõem e o usuário vê "tela quebra, volta, quebra".
- Luna (`/home/andrefarias/Desenvolvimento/Luna/`) usa **Textual** com `BannerGlitchWidget(Static)` + `self.update(text)` local, sem race global. **Funciona suave.**

A escolha técnica é migrar a TUI para Textual mantendo paridade funcional total com a Claude Code CLI.

---

## Arquitetura proposta (Textual)

### Estrutura de arquivos

```
nyx/agent/
├── tui/
│   ├── __init__.py
│   ├── app.py            # App principal (substitui repl_app.py)
│   ├── widgets/
│   │   ├── __init__.py
│   │   ├── banner.py     # BannerWidget (estilo Luna BannerGlitchWidget)
│   │   ├── output.py     # OutputWidget (rolling log de mensagens)
│   │   ├── input.py      # InputWidget (prompt > ancorado no rodapé)
│   │   └── toolbar.py    # ToolbarWidget (bottom bar com modos + ctx)
│   ├── styles/
│   │   └── nyx.tcss      # Textual CSS (paleta turquesa+roxo+verde)
│   └── lifecycle.py      # on_mount async, shutdown ordenado
└── repl_app.py           # MANTIDO durante transição como fallback NYX_LEGACY_REPL
```

### Layout Textual (CSS-driven)

```python
def compose(self) -> ComposeResult:
    yield Header()
    yield BannerWidget(id="banner")
    yield OutputWidget(id="output")
    yield InputWidget(id="input")
    yield Toolbar(id="toolbar")
    yield Footer()
```

### Widget design (resumido)

- **BannerWidget(Static)**: render `$ nyx.code▌` + box info (v1.3.0 | offline | MODELO | PROJETO | TOOLS | COMANDOS | MEMÓRIA). Timer `set_interval(0.5)` alterna `▌``▏` via `self.update(text)` local — **sem invalidate global**.
- **OutputWidget(RichLog)**: rolling log de mensagens user/assistant/tool. Usa `RichLog.write()` para append sem race.
- **InputWidget(Input)**: prompt `>` ancorado no rodapé via dock=bottom. Captura teclas via `on_input_submitted`.
- **Toolbar(Static)**: render `ctx X% | iter N | lidos M | modif K | ○ cold | shift+tab: ...`. Refresh local quando state muda.

### Lifecycle

```python
class NyxTUI(App):
    CSS_PATH = "tui/styles/nyx.tcss"
    BINDINGS = [
        Binding("ctrl+q", "quit_and_stop", "Sair + parar Ollama"),
        Binding("ctrl+d", "quit_if_empty", "EOF"),
        Binding("shift+tab", "cycle_mode", "Trocar modo"),
        Binding("ctrl+v", "paste", "Colar"),
        # ...
    ]

    async def on_mount(self) -> None:
        await self.run_warmup()       # carrega Agent, settings, memória
        await self.show_banner()
        self.query_one(InputWidget).focus()
```

---

## Fases (sub-sprints filhas — não criadas ainda)

| ID | Sprint | Escopo | Esforço estimado |
|----|--------|--------|------------------|
| 196 | **TEXTUAL-SCAFFOLD-01** | Adicionar dependência `textual>=0.76` em `pyproject.toml`; criar estrutura `nyx/agent/tui/` vazia; smoke pass | 1-2h |
| 197 | **TEXTUAL-OUTPUT-WIDGET-01** | `OutputWidget(RichLog)` recebendo append de mensagens user/assistant/tool com paleta correta | 2-4h |
| 198 | **TEXTUAL-INPUT-WIDGET-01** | `InputWidget(Input)` ancorado no rodapé com completer de slash commands + paste handler + history | 3-5h |
| 199 | **TEXTUAL-BANNER-WIDGET-01** | `BannerWidget(Static)` com layout grid 2-col + timer blink `▌``▏` local | 2-3h |
| 200 | **TEXTUAL-TOOLBAR-01** | `Toolbar(Static)` com ctx/iter/lidos/modif/glyph_state/modo via reactive properties | 2-3h |
| 201 | **TEXTUAL-CUTOVER-01** | Trocar default de prompt_toolkit para Textual; manter `NYX_LEGACY_REPL=1` para fallback; gauntlet completo PASS | 4-8h |

**Total estimado:** 14-25h de trabalho focado. Recomendação: 1 sub-sprint por sessão de execução, com validação visual entre cada.

---

## Paridade obrigatória com a TUI atual

Cada sub-sprint deve preservar 1:1 a funcionalidade abaixo:

- Banner block com paleta turquesa+roxo+verde (ADR-023)
- 4 modos via shift+tab: normal/plan/sudo/bypass (SHIFT-TAB-CYCLE-01)
- Bottom toolbar com `ctx X%`, `iter`, `lidos`, `modif`, `cold/warming/warm` (UX-BUG-02B)
- Slash commands via `/` (popup navegável) — 67 commands totais
- Completion de paths/files
- Ctrl+V clipboard (texto + imagem `[Image #N]`)
- Ctrl+Q fecha + ollama stop all (sprint 188)
- Ctrl+D em buffer vazio = EOF (sprint 189)
- Ctrl+C cancela tool inflight
- Ctrl+O expand último input (UX-EXTRA-01)
- Ctrl+Up recall último input
- Ctrl+J newline literal
- Tab accept suggestion / completion / expand-thinking (TUI-REDESIGN-25-09-PARTE-2)
- Streaming token-by-token de respostas do modelo
- Tool calls renderizados em chips com duration + status
- Diff boxes para tool results de file edits
- Spinner durante warmup / model load
- Quit card no shutdown
- First-run wizard (7 passos)
- `--web` cockpit ainda funcionando (independente da TUI)
- `--smoke` boot ok
- `--gauntlet` PASS

---

## Riscos

| Risco | Mitigação |
|-------|-----------|
| Textual não suporta alguma feature do prompt_toolkit (raw stdin drain, completion popup customizado) | Investigar em SCAFFOLD-01; se confirmado, hibridizar (Textual para output/banner, prompt_toolkit para input) |
| Migração quebra Gauntlet (sprint não-CONCLUIDA até fim) | Manter `NYX_LEGACY_REPL=1` durante toda a ONDA-30 — fallback estável. Cutover só na 201 |
| Animações Rich-text dentro do RichLog não renderizam ANSI escapes nativos | Confirmar em OUTPUT-WIDGET-01 que `RichLog.write(Text.from_ansi(...))` funciona |
| Paleta CSS Textual não casa byte-a-byte com ANSI atual | Aceitar drift visual mínimo — ADR-023 define cores como tokens, não bytes |
| Reactive properties + watchers do Textual têm pegadas de performance pior que prompt_toolkit | Profile na 200 (toolbar com 5 reactive props) — usar `recompose=False` se necessário |
| Esforço total (14-25h) exceder o orçado | Spec da 201 inclui critério "se hibridização for inevitável, cancelar cutover e fechar ONDA-30 com hybrid" |

---

## Critérios para abrir ONDA-30 oficialmente

- [ ] Este spec (194) revisado e aprovado pelo usuário
- [ ] MASTER bumped v5.4.0 → v5.5.0 com bloco MANUAL_OVERRIDE_ONDA_30
- [ ] 6 sub-sprints filhas (196-201) materializadas em `producao/` com spec V2 cada
- [ ] Brainstorming opcional via `/planejar-sprint TEXTUAL-SCAFFOLD-01` para refinar primeira sub-sprint
- [ ] Backup do branch atual (`git tag pre-textual-migration` antes de iniciar 196)

---

## Recomendação imediata

A sessão atual já fechou ONDA-29 (9 sprints CONCLUIDAS) + sprint de revert (193) + sprint 195 (terceira recidiva). Recomendo:

1. **Fechar a sessão por aqui** — commitar este spec (194) + atualizar MASTER + push.
2. **ONDA-30 em sessão separada e dedicada** — começar com brainstorming via `/planejar-sprint TEXTUAL-SCAFFOLD-01` para refinar a primeira sub-sprint.
3. **Não despachar executor automaticamente desta sprint** — é planejamento, não execução.

---

## Achados colaterais

- Sprint INFRA-SANITIZER-WORKING-TREE-GUARD-01 (recomendada pelas sprints 192 + 195) continua pendente. **Considerar priorizar antes da ONDA-30** porque a TUI corrupção continua: se sanitizer atacar durante migração Textual, vai introduzir flicker novo causado por glifos faltando.

---

*"Migrar é menos sobre código novo e mais sobre coragem de revisitar premissas antigas." -- princípio refactor Nyx-Code.*
