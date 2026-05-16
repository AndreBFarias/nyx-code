## 0. SPEC

```yaml
sprint:
  id: UX-DESIGN-01
  title: "Design System Nyx: tokens + glifos + ADR-023 + ThemeManager unificado"
  onda: 22
  bloco: 3
  prioridade: CRÍTICA
  tipo: Feature + Docs
  dependencias: [AUDIT-FIX-03]     # precisa da centralização de constantes
  desbloqueia: [UX-LAYOUT-01, UX-LAYOUT-02, UX-LAYOUT-03]

  creates:
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/themes/design_tokens.py
      reason: "Fonte única de cores, glifos, box chars, spinner frames"
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/dev-journey/03-decisions/ADR_023_DESIGN_SYSTEM.md
      reason: "Decisão de paleta D (Claude-CLI estrutura + turquesa + toques de roxo)"

  touches:
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/agent/output.py
      reason: "Importar tokens; remover hex hardcoded (8+ pontos). Docstring 'Claude Code' é escopo de AUDIT-FIX-08, NÃO desta sprint."
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/cli.py
      reason: "Importar tokens; substituir ACCENT/PRIMARY/DIM locais por design_tokens; trocar emoji ⚡ por glifo do sistema"
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/themes/__init__.py
      reason: "ThemeManager passa a derivar de design_tokens quando entidade=nyx (fonte única)"
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/GUIDE.md
      reason: "Lista de ADRs vai a 25; menciona design_tokens como fonte única"

  forbidden:
    - "Manter hex hardcoded fora de design_tokens.py"
    - "Usar emoji (incluindo ⚡ U+26A1) — substituir por glifo ASCII/Unicode seguro"
    - "Deixar menção a 'Claude Code' em código/docstring/comentário (ADR-005)"
    - "Criar segunda constante duplicada em outro módulo"

  tests:
    - cmd: "grep -rn '#[0-9A-Fa-f]\\{6\\}' nyx/ --include='*.py' | grep -v 'design_tokens.py\\|themes/constants.py'"
      esperado: "vazio (zero hex hardcoded fora da fonte)"
    - cmd: "python -c 'from nyx.themes.design_tokens import NYX_ACCENT, NYX_PURPLE, BULLETS, BOX_CHARS, SPINNER_FRAMES; print(NYX_ACCENT)'"
      deve_passar: true
    - cmd: "./run.sh --gauntlet --only rapido"
      deve_passar: true

  acceptance_criteria:
    - "Arquivo nyx/themes/design_tokens.py existe com constantes listadas abaixo"
    - "ADR-023 criado e marcado ACEITO"
    - "GUIDE.md atualizado (lista ADRs + contagem)"
    - "Zero hex (#RRGGBB) em código Python fora de design_tokens.py e themes/constants.py"
    - "Zero emoji (⚡) em código — substituído pelo glifo BULLETS['bypass']"
    - "ThemeManager.get_ansi_colors('nyx') retorna cores derivadas de design_tokens"
    - "cli.py e output.py importam de design_tokens"
    - "Gauntlet rapido passa"
```

---

# Sprint UX-DESIGN-01 — Design System Nyx

**Status:** CONCLUIDA (commit e189f15)
**Data criação:** 2026-04-18
**Prioridade:** CRÍTICA (desbloqueia todo Bloco 4 — Layout)

## Contexto do projeto (snapshot)

- ADR-004 Zero Emojis; ADR-005 Anonimato; ADR-006 PT-BR.
- Findings do AUDIT-EXT-01:
  - **A-04:** cores em 8+ pontos (`#00D4AA`, escapes ANSI `\033[38;2;0;212;170m`) — violação N-para-N.
  - **A-05:** docstring `output.py:302` menciona "Claude Code".
  - **A-06:** ⚡ (U+26A1) em `cli.py:88, 195` — emoji.
  - **D-02:** sistema `nyx/themes/entities/*.json` existe mas `output.py` ignora.
- Decisão D2 (usuário, 2026-04-18): paleta **mista D** — estrutura Claude CLI (box chars ╭╮╯╰─│) + turquesa `#00D4AA` + toques de roxo `#9D4EDD`.

## Problema

Sem fonte única de linguagem visual, cada sprint de layout reintroduz drift de cores, glifos e emojis. Design System precisa vir **antes** do trabalho visual.

## Solução

1. Criar `nyx/themes/design_tokens.py` — constantes imutáveis canônicas.
2. Criar `ADR-023` documentando a decisão da paleta D.
3. Refatorar `cli.py` e `output.py` importando dos tokens.
4. Trocar `⚡` por glifo canônico (ex.: `!`, `*`, `»`, ou `BYPASS`) — decidido em `design_tokens.py`.
5. Limpar docstring `output.py:302`.
6. Ligar `ThemeManager` aos tokens quando entidade = `nyx`.

## Arquivos alvo

### `nyx/themes/design_tokens.py` (NOVO)

```python
"""Design Tokens Nyx -- fonte única da linguagem visual.

Qualquer cor, glifo, box char ou frame de spinner usado na UI (cli.py,
output.py, toolbar, etc.) DEVE vir daqui. Ver ADR-023.

Paleta D (2026-04-18): estrutura Claude CLI + turquesa histórica + toques
de roxo para estados especiais (bypass ON, memória, skills).
"""

from __future__ import annotations

# ── Cores (hex) ─────────────────────────────────────────────────────

NYX_ACCENT      = "#00D4AA"   # turquesa — accent principal
NYX_ACCENT_DIM  = "#007A63"   # turquesa escuro — hover/selected

NYX_PURPLE      = "#9D4EDD"   # roxo — bypass ON, memória, skills, estado "atenção"
NYX_PURPLE_DIM  = "#5A189A"   # roxo escuro

NYX_PRIMARY     = "#E8E8E8"   # texto primário
NYX_MUTED       = "#606060"   # dim

NYX_BG          = "#1A1B23"   # fundo preferido
NYX_BG_SOFT     = "#2A2C39"   # fundo de painel

NYX_SUCCESS     = "#4ADE80"
NYX_WARNING     = "#FFC857"
NYX_ERROR       = "#FF6B6B"

# ── ANSI 24-bit (derivados dos hex acima) ───────────────────────────

def hex_to_ansi_fg(hex_str: str) -> str:
    """Converte #RRGGBB para escape ANSI 24-bit foreground."""
    h = hex_str.lstrip("#")
    r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    return f"\033[38;2;{r};{g};{b}m"

def hex_to_ansi_bg(hex_str: str) -> str:
    """Converte #RRGGBB para escape ANSI 24-bit background."""
    h = hex_str.lstrip("#")
    r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    return f"\033[48;2;{r};{g};{b}m"

ANSI_ACCENT_FG = hex_to_ansi_fg(NYX_ACCENT)
ANSI_PURPLE_FG = hex_to_ansi_fg(NYX_PURPLE)
ANSI_PRIMARY_FG = hex_to_ansi_fg(NYX_PRIMARY)
ANSI_MUTED_FG = hex_to_ansi_fg(NYX_MUTED)
ANSI_ERROR_FG = hex_to_ansi_fg(NYX_ERROR)
ANSI_SUCCESS_FG = hex_to_ansi_fg(NYX_SUCCESS)
ANSI_WARNING_FG = hex_to_ansi_fg(NYX_WARNING)

ANSI_DIM = "\033[2m"
ANSI_BOLD = "\033[1m"
ANSI_RESET = "\033[0m"

# ── Glifos canônicos (zero emoji, ADR-004) ──────────────────────────
# Se um símbolo está na faixa Unicode de emoji (U+1F300-U+1F9FF ou
# U+2600-U+27BF), NÃO adicionar aqui. Preferir box drawing e ASCII.

BOX_CHARS = {
    "tl": "╭", "tr": "╮", "bl": "╰", "br": "╯",
    "h": "─", "v": "│",
    "tjoin": "┬", "bjoin": "┴", "ljoin": "├", "rjoin": "┤", "cross": "┼",
}

BULLETS = {
    "tool":        "●",    # círculo cheio — tool em execução/concluída
    "tool_ok":     "●",
    "tool_err":    "●",
    "result":      "└─",
    "note":        "·",
    "arrow":       "→",
    "bypass_on":   "[!]",  # substitui ⚡ (U+26A1 é emoji)
    "bypass_off":  "[ ]",
    "ready":       "●",
    "working":     "○",
    "prompt":      ">",
}

SPINNER_FRAMES = ("⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏")
# Braille Patterns (U+2800-U+28FF) — NÃO é emoji, é símbolo técnico.

# ── Re-exports convenientes ─────────────────────────────────────────

__all__ = [
    "NYX_ACCENT", "NYX_ACCENT_DIM", "NYX_PURPLE", "NYX_PURPLE_DIM",
    "NYX_PRIMARY", "NYX_MUTED", "NYX_BG", "NYX_BG_SOFT",
    "NYX_SUCCESS", "NYX_WARNING", "NYX_ERROR",
    "ANSI_ACCENT_FG", "ANSI_PURPLE_FG", "ANSI_PRIMARY_FG", "ANSI_MUTED_FG",
    "ANSI_ERROR_FG", "ANSI_SUCCESS_FG", "ANSI_WARNING_FG",
    "ANSI_DIM", "ANSI_BOLD", "ANSI_RESET",
    "BOX_CHARS", "BULLETS", "SPINNER_FRAMES",
    "hex_to_ansi_fg", "hex_to_ansi_bg",
]


# "A linguagem do produto começa pela consistência de seus tokens." -- anônimo
```

### ADR-023 (NOVO)

**Path:** `dev-journey/03-decisions/ADR_023_DESIGN_SYSTEM.md`

```markdown
# ADR-023 — Design System Nyx: paleta D e tokens canônicos

**Status:** ACEITO
**Data:** 2026-04-18
**Contexto da Onda:** 22, Bloco 3, UX-DESIGN-01

## Contexto

Até esta data, cores e glifos estavam espalhados em `cli.py` e `output.py`
(8+ pontos com hex `#00D4AA` e escapes ANSI 24-bit hardcoded). Auditoria
externa (AUDIT-EXT-01) apontou como violação N-para-N.

Havia ainda um emoji `⚡` (U+26A1) usado como indicador de bypass — violação
de ADR-004 (Zero Emojis).

## Decisão

Adotar **paleta D** (decisão do usuário, 2026-04-18):

- Estrutura visual: Claude Code CLI (box chars `╭╮╯╰─│`, hierarquia minimalista).
- Cor principal: turquesa histórica `#00D4AA`.
- Cor de estados especiais (bypass ON, memória, skills): roxo `#9D4EDD`.
- Glifo de bypass: `[!]` em vez de `⚡`.

Criar `nyx/themes/design_tokens.py` como **única fonte** dessas constantes.
Qualquer arquivo que renderize UI consome dela.

## Consequências

- Positivas: mudança de paleta/glifo = 1 arquivo editado.
- Positivas: zero ambiguidade de cor entre módulos.
- Neutra: `nyx/themes/entities/*.json` continua existindo para temas
  alternativos (Luna, Eris); `nyx` vira o tema default e sua cor nasce
  em `design_tokens.py`. `ThemeManager.get_ansi_colors("nyx")` passa a
  derivar dos tokens (fonte única).

## Alternativas consideradas

- **Paleta A (só Claude CLI):** rejeitada — perde identidade Nyx.
- **Paleta B (Gemini/Codex):** rejeitada — colorida demais, contraria noite.
- **Paleta C (identidade própria full roxa):** rejeitada — quebra affordance
  existente (usuário habituado ao turquesa).
- **Paleta D (mista):** aceita.

## Referências

- AUDIT-EXT-01 findings A-04, A-05, A-06, D-02.
- Plano Onda 22.

*"Consistência é a forma visível da atenção." -- anônimo*
```

### `nyx/cli.py` — mudanças

No topo (substitui linhas 41-45):

```python
from nyx.themes.design_tokens import (
    ANSI_ACCENT_FG as ACCENT,
    ANSI_PRIMARY_FG as PRIMARY,
    ANSI_DIM as DIM,
    ANSI_BOLD as BOLD,
    ANSI_RESET as NC,
    ANSI_PURPLE_FG,
    BULLETS,
)
```

Linha 88 (substituir `⚡`):

**Antes:**
```python
print(f"  {DIM}⚡ bypass · {tool_name} auto-aprovado{NC}")
```

**Depois:**
```python
print(f"  {DIM}{BULLETS['bypass_on']} bypass · {tool_name} auto-aprovado{NC}")
```

Linha 195 (substituir no toolbar):

**Antes:**
```python
parts.append(("bg:#7a4d00 fg:#ffffff bold", " ⚡ bypass permissions ON "))
```

**Depois:**
```python
parts.append((f"bg:{NYX_PURPLE_DIM} fg:#ffffff bold", f" {BULLETS['bypass_on']} bypass permissions ON "))
```

*(Import `NYX_PURPLE_DIM` também.)*

### `nyx/agent/output.py` — mudanças

Substituir todos os `ACCENT_FG = "\033[38;2;0;212;170m"` locais (aparecem em múltiplas funções) por import único no topo:

```python
from nyx.themes.design_tokens import (
    ANSI_ACCENT_FG,
    ANSI_ERROR_FG,
    ANSI_MUTED_FG,
    ANSI_DIM,
    ANSI_BOLD,
    ANSI_RESET,
    NYX_ACCENT,
    NYX_PRIMARY,
    BULLETS,
)
```

Onde existia `ACCENT_FG = "\033[38;2;0;212;170m"; NC_FG = "\033[0m"`, usar os imports.

Onde existia `⏺` hardcoded, usar `BULLETS["tool"]`.
Onde existia `└─` hardcoded, usar `BULLETS["result"]`.

**Docstring linha 302**:

**Antes:**
```python
"""Imprime tool call estilo Claude Code: '⏺ nome(arg)' em accent color."""
```

**Depois:**
```python
"""Renderiza linha de tool call com bullet em accent color."""
```

### `nyx/themes/__init__.py` — ThemeManager plugado

Em `get_ansi_colors`, quando `entity_id == "nyx"`, retornar dict derivado dos tokens:

```python
def get_ansi_colors(self, entity_id: str | None = None) -> dict[str, str]:
    entity_id = entity_id or self._tema_ativo
    if entity_id == "nyx":
        from nyx.themes.design_tokens import (
            ANSI_ACCENT_FG, ANSI_PRIMARY_FG, ANSI_MUTED_FG,
            ANSI_ERROR_FG, ANSI_SUCCESS_FG, ANSI_PURPLE_FG, ANSI_RESET,
        )
        return {
            "accent": ANSI_ACCENT_FG,
            "primary": ANSI_PRIMARY_FG,
            "muted": ANSI_MUTED_FG,
            "error": ANSI_ERROR_FG,
            "success": ANSI_SUCCESS_FG,
            "special": ANSI_PURPLE_FG,
            "reset": ANSI_RESET,
        }
    # fallback: comportamento atual (lê JSON + hex_to_ansi_raw)
    cores = self.load_theme(entity_id)
    ...
```

### GUIDE.md — atualizar

- Tabela ADRs: adicionar `| 023 | Design System (paleta D) |`
- Contagem: `ADRs | 25 | --` (após ADR-024 de AUDIT-FIX-06)
- Seção "Código": adicionar linha "Cores/glifos/spinner vêm de `nyx.themes.design_tokens` (ADR-023)"

## Diff esperado

```
+ nyx/themes/design_tokens.py (criado, ~100 linhas)
+ dev-journey/03-decisions/ADR_023_DESIGN_SYSTEM.md (criado)
~ nyx/cli.py: -3 linhas, +~5 linhas (import + glifo novo)
~ nyx/agent/output.py: -20 linhas, +~10 linhas (consolidação)
~ nyx/themes/__init__.py: +15 linhas
~ GUIDE.md: +2 linhas
```

## Comando de verificação

```bash
cd /home/andrefarias/Desenvolvimento/Nyx-Code

# 1. Tokens importáveis
python -c "
from nyx.themes.design_tokens import (
    NYX_ACCENT, NYX_PURPLE, ANSI_ACCENT_FG, BULLETS, BOX_CHARS, SPINNER_FRAMES,
    hex_to_ansi_fg,
)
assert NYX_ACCENT == '#00D4AA'
assert NYX_PURPLE == '#9D4EDD'
assert BULLETS['bypass_on'] == '[!]'
assert len(SPINNER_FRAMES) == 10
print('tokens OK')
"

# 2. Zero hex fora da fonte
grep -rn '#[0-9A-Fa-f]\{6\}' nyx/ --include='*.py' | grep -v 'design_tokens.py\|themes/constants.py'
# esperado: vazio

# 3. Zero emoji ⚡
grep -rn $'\u26A1' nyx/ --include='*.py'
# esperado: vazio

# 4. ADR existe
test -s dev-journey/03-decisions/ADR_023_DESIGN_SYSTEM.md && echo "ADR OK"

# 5. ThemeManager retorna tokens
python -c "
from nyx.themes import ThemeManager
c = ThemeManager().get_ansi_colors('nyx')
assert 'accent' in c
print('ThemeManager OK')
"

# 6. Gauntlet
./run.sh --gauntlet --only rapido
```

## Critério binário

- [ ] `nyx/themes/design_tokens.py` existe e importável
- [ ] ADR-023 criado (Status: ACEITO)
- [ ] GUIDE.md tabela de ADRs até 25
- [ ] `grep #[0-9A-Fa-f]{6}` em `nyx/*.py` retorna vazio (exceto `design_tokens.py` e `themes/constants.py`)
- [ ] `grep ⚡ nyx/*.py` retorna vazio
- [ ] `cli.py` e `output.py` importam de `design_tokens`
- [ ] `ThemeManager.get_ansi_colors("nyx")` retorna dict dos tokens
- [ ] Gauntlet rapido passa
- [ ] Visual: `./run.sh` abre com cores idênticas ao antes (usuário valida screenshot)
- [ ] Commit: `feat: design system tokens + ADR-023 + limpeza hex N-para-N`

## Guardrails anti-engodo

**NÃO marque como concluída se:**
- IA importou `design_tokens` mas deixou hex hardcoded "por segurança".
- Emoji ⚡ foi substituído em 1 linha e deixado em outra.
- Docstring "Claude Code" foi só mascarado com "C**** C***".
- `ThemeManager` tem código copiado dos tokens em vez de **importar**.

## Validação humana

```bash
# Inspeção visual
./run.sh
# Banner deve ter cores idênticas ao antes; toolbar com bypass ON mostra roxo em vez de ⚡

# Verificação automatizada
grep -rn '#00D4AA\|#9D4EDD' nyx/ --include='*.py'
# esperado: apenas em design_tokens.py

grep -rn '\\\\033\\[38' nyx/ --include='*.py'
# esperado: apenas em design_tokens.py
```

## Riscos

| Risco | Mitigação |
|-------|-----------|
| Import circular themes/__init__ ↔ design_tokens | design_tokens não importa de themes |
| Cor muda visualmente por engano | Comparar screenshot antes/depois |
| ⚡ aparece em logs antigos | Aceitável — só impede emissão nova |

---

*"A identidade visual é a gramática silenciosa do produto." -- anônimo designer*
