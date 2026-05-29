# SPEC

```yaml
sprint:
  id: TUI-CSS-LUNA-ADOPT-01
  title: "Expande nyx.tcss adotando padrão Luna templo_de_nyx.css"
  onda: 32
  prioridade: ALTA
  tipo: Feature
  dependencias: []
  desbloqueia: [TUI-CHATMESSAGE-WIDGET-01, TUI-BANNER-DOCK-TOP-01]

  touches:
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/agent/tui/styles/nyx.tcss
      reason: "Expandir de 50L para ~200L com tokens, scrollbar, dock, ChatMessage classes"

  creates: []
  removes: []

  forbidden:
    - "Hex hardcoded fora dos tokens declarados no topo do arquivo (paridade design_tokens.py)"
    - "Adicionar emoji"
    - "Mencionar IA externa" <!-- noqa-anonimato -->

  tests:
    - cmd: "./run.sh --smoke"
      timeout: 60
      deve_passar: true
    - cmd: "NYX_TUI_TEXTUAL=1 ./venv/bin/python -c 'from nyx.agent.tui.app import NyxTUI; from pathlib import Path; t=NyxTUI.CSS_PATH; assert Path(t).exists(); print(\"tcss=\", Path(t).read_text().count(chr(10)), \"L\")'"
      timeout: 30
      deve_passar: true

  acceptance_criteria:
    - "nyx.tcss tem >=150 linhas (era 50)"
    - "Possui blocos para BannerWidget (dock: top), #chat (VerticalScroll height 1fr), InputWidget (dock: bottom h:5), Toolbar (dock: bottom h:1)"
    - "Possui blocos para ChatMessage.user, ChatMessage.assistant, ChatMessage.tool, ChatMessage.system"
    - "Possui scrollbar-background, scrollbar-color, scrollbar-color-hover, scrollbar-color-active em #chat"
    - "NYX_TUI_TEXTUAL=1 ./run.sh --smoke ainda imprime boot ok"
    - "Invariantes 14/14 PASS"
```

---

# Sprint TUI-CSS-LUNA-ADOPT-01 — Expande nyx.tcss adotando padrão Luna

**Status:** PENDENTE
**Data criação:** 2026-05-28
**Modelo obrigatório:** Modelo Opus 4.7 (1M) (sem subagentes)

---

## Contexto do projeto (snapshot)

> ADRs relevantes: ADR-001 Local First, ADR-004 Zero Emojis, ADR-005 Anonimato,
> ADR-006 PT-BR, ADR-013 Integração Obrigatória, ADR-014 Testes via Gauntlet,
> ADR-023 paleta canônica (turquesa #00D4AA + roxo #9D4EDD + verde #4ADE80).
>
> Sprint anterior: 207 TEXTUAL-CUTOVER-01 CONCLUIDA (opt-in via NYX_TUI_TEXTUAL=1).
> Esta sprint abre ONDA-32 (cutover real).
>
> Estado: `nyx/agent/tui/styles/nyx.tcss` tem 50L (placeholder).
> Referência: `/home/andrefarias/Desenvolvimento/Luna/novo_css/templo_de_nyx.css` (200L, Textual puro).

---

## Problema

`nyx.tcss` atual é placeholder mínimo (50L) -- não suporta os widgets que as
sprints filhas vão adicionar (ChatMessage user/assistant/tool, VerticalScroll com
scrollbar customizada, banner dock top fixo). Precisa expandir para template Luna
mantendo paleta Nyx (turquesa+roxo).

---

## Solução proposta

Reescrever `nyx.tcss` consumindo padrão de `templo_de_nyx.css` (Luna):
- Declarar tokens hex no topo ($accent, $primary, $muted, $surface, $foreground)
- Bloco `App`/`Screen` com background
- Bloco `BannerWidget { dock: top; height: auto; ... }`
- Bloco `#chat` (VerticalScroll) com `scrollbar-*` styles
- Blocos `ChatMessage.user`, `.assistant`, `.tool`, `.system`
- Bloco `InputWidget { dock: bottom; height: 5; border: round $accent }`
- Bloco `Toolbar { dock: bottom; height: 1 }`

---

## Arquivos alvo

### `/home/andrefarias/Desenvolvimento/Nyx-Code/nyx/agent/tui/styles/nyx.tcss`

**Antes (50L):**
```css
/* Nyx-Code TUI styles — ONDA-30 SCAFFOLD placeholder. ... */
App { background: $surface; }
$accent: #00D4AA;
$primary: #9D4EDD;
$success: #4ADE80;
OutputWidget { height: 1fr; background: $surface; padding: 0 1; }
InputWidget { dock: bottom; height: 3; background: $surface; border: round $accent; }
BannerWidget { height: auto; background: $surface; }
Toolbar { dock: bottom; height: 1; background: $surface; }
```

**Depois (~180-200L):**
```css
/* Nyx-Code TUI styles — ONDA-32 LUNA-ADOPT.
 *
 * Paleta canônica (ADR-023): turquesa #00D4AA + roxo #9D4EDD + verde #4ADE80.
 * Template estrutural derivado de Luna templo_de_nyx.css (2 colunas adaptado para 1 coluna).
 */

$accent: #00D4AA;        /* turquesa NYX_ACCENT */
$primary: #9D4EDD;       /* roxo NYX_PURPLE */
$success: #4ADE80;       /* verde NYX_SUCCESS */
$error: #EF4444;         /* vermelho NYX_ERROR */
$muted: #6B7280;         /* cinza NYX_MUTED */
$surface: #0A0E14;       /* fundo escuro */
$foreground: #E6E4D9;    /* texto claro */

Screen { background: $surface; color: $foreground; }
App { background: $surface; }

BannerWidget {
    dock: top;
    height: auto;
    background: $surface;
    padding: 0 1;
    color: $accent;
}

#chat {
    height: 1fr;
    background: $surface;
    padding: 1 1;
    scrollbar-background: $surface;
    scrollbar-color: $primary 30%;
    scrollbar-color-hover: $primary;
    scrollbar-color-active: $accent;
    scrollbar-corner-color: $surface;
}

ChatMessage {
    height: auto;
    background: $surface;
    padding: 0 1;
    margin: 0;
}

ChatMessage.user {
    color: $accent;
    border-left: heavy $accent;
    padding: 0 1 0 2;
    margin: 1 0 0 0;
}

ChatMessage.assistant {
    color: $primary;
    border-left: heavy $primary;
    padding: 0 1 0 2;
    margin: 1 0 0 0;
}

ChatMessage.tool {
    color: $muted;
    padding: 0 1 0 4;
    margin: 0;
}

ChatMessage.system {
    color: $muted;
    text-style: italic;
    padding: 0 1;
    margin: 0;
}

InputWidget {
    dock: bottom;
    height: 5;
    background: $surface;
    border: round $accent;
    padding: 0 1;
}

InputWidget > TextArea, InputWidget > Input {
    background: $surface;
    color: $foreground;
    border: none;
}

Toolbar {
    dock: bottom;
    height: 1;
    background: $surface;
    color: $muted;
    padding: 0 1;
}

/* Placeholder OutputWidget até remoção na sprint 3 (deprecação). */
OutputWidget { height: 1fr; background: $surface; padding: 0 1; }
```

**Mudanças:**
- Tokens hex declarados no topo (canonical naming `$accent/$primary/$muted/...`)
- BannerWidget recebe `dock: top` (preparando para sprint 4)
- `#chat` adicionado com scrollbar canônica (preparando sprint 3)
- ChatMessage classes user/assistant/tool/system (preparando sprint 2)
- InputWidget altura passa de 3 para 5 linhas (paridade prompt_toolkit)
- Toolbar mantido como estava

---

## Diff esperado

```
+ 0 arquivos criados
~ 1 arquivo modificado (nyx.tcss)
- 0 arquivos removidos
+ ~140 linhas líquidas
```

---

## Comandos de verificação

```bash
cd /home/andrefarias/Desenvolvimento/Nyx-Code

# 1. Smoke boot
./run.sh --smoke
# esperado: "boot ok" exit 0

# 2. NyxTUI carrega sem erro de parse CSS
NYX_TUI_TEXTUAL=1 ./venv/bin/python -c "
from nyx.agent.tui.app import NyxTUI
from pathlib import Path
t = NyxTUI.CSS_PATH
assert Path(t).exists()
content = Path(t).read_text()
linhas = content.count(chr(10))
print(f'tcss={linhas}L')
assert linhas >= 150, f'esperado >=150L, got {linhas}'
for sel in ['BannerWidget', '#chat', 'ChatMessage.user', 'ChatMessage.assistant', 'ChatMessage.tool', 'InputWidget', 'Toolbar', 'scrollbar-color']:
    assert sel in content, f'falta seletor: {sel}'
print('OK todos seletores presentes')
"

# 3. Invariantes
bash scripts/sprint_invariants.sh
# esperado: PASS 14/14 FAIL 0

# 4. Acentuação (no arquivo CSS, sem acentos é normal mas validar mesmo assim)
python3 ~/.config/zsh/scripts/validar-acentuacao.py --paths nyx/agent/tui/styles/nyx.tcss
# esperado: rc=0
```

---

## Critério binário de aceite

- [ ] nyx.tcss tem >=150 linhas
- [ ] Possui todos os blocos: BannerWidget, #chat (com scrollbar-*), ChatMessage.{user,assistant,tool,system}, InputWidget, Toolbar
- [ ] Possui tokens declarados ($accent, $primary, $muted, $surface, $foreground)
- [ ] `./run.sh --smoke` imprime `boot ok`
- [ ] `bash scripts/sprint_invariants.sh` PASS 14/14
- [ ] `ruff check` sem novos erros
- [ ] `validar-acentuacao.py` rc=0
- [ ] Sem hex hardcoded fora do bloco de tokens

---

## Proof-of-work obrigatório

Conforme template V2. Colar output de:
1. `bash scripts/sprint_invariants.sh > /tmp/inv_before.txt` ANTES
2. Implementação
3. `bash scripts/sprint_invariants.sh > /tmp/inv_after.txt` DEPOIS
4. `diff /tmp/inv_before.txt /tmp/inv_after.txt`
5. Output do comando de verificação #2

---

## Riscos

| Risco | Mitigação |
|-------|-----------|
| Textual CSS rejeita variantes não suportadas | Validar via dispatch NyxTUI no comando #2 antes de marcar CONCLUIDA |
| Mudança de InputWidget height 3→5 quebra layout opt-in atual | Aceitável -- usuário já roda em prompt_toolkit; mudança vira efetiva quando ONDA-32 completa |

---

*"A perfeição é estática, e eu estou em movimento perpétuo." -- Clarice Lispector*
