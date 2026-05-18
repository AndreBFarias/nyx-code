# Nyx Code — PR-ready bundle

Arquivos prontos pra cair como PR no `nyx-code`. Implementam o redesign visual
descrito no doc principal (`Nyx Code Terminal.html`):

- **5 estéticos × 7 entidades** (Arcano, Cyber, Brutalist, Mecha, Editorial × Nyx, Eris, Juno, Lars, Luna, Mars, Somn)
- **Hot-reload de temas** via observer pattern
- **Box drawing + Braille** com fallback ASCII automático
- **Banner neofetch-style** (logo ASCII + system info) quando cols >= 100
- **Compatibilidade total** com a API atual

## Estrutura

```
nyx/
├── themes/
│   ├── design_tokens.py   ← REWRITE — 5 aesthetics × 7 entities
│   ├── glyphs.py           ← NOVO — box drawing por peso + fallback ASCII
│   └── ascii_art.py        ← NOVO — logo Nyx em Block Elements
└── agent/
    └── banner.py           ← REWRITE — neofetch (>=100), classic (60-99), compact (<60)
```

## ADRs envolvidos

- **ADR-004 — Zero Emojis**  preservado. Glifos novos (Block Elements U+2580-259F, Braille U+2800-28FF) ficam fora das faixas proibidas.
- **ADR-005 — Sem menção a IA**  preservado. Banner não usa as palavras "modelo de IA", "assistant", "treinada".
- **ADR-006 — PT-BR**  preservado.
- **ADR-023 — Design tokens**  ampliado, não substituído. Funções e constantes do v1 (NYX_ACCENT, BOX_CHARS, BULLETS, SPINNER_FRAMES) seguem exportadas e funcionando.
- **ADR-NEW-025 — Multi-aesthetic** (proposta): documenta o sistema 5×7 introduzido aqui.

## Como aplicar

```bash
# 1. Backup do antigo
cp nyx/themes/design_tokens.py nyx/themes/design_tokens.py.bak
cp nyx/agent/banner.py nyx/agent/banner.py.bak

# 2. Substituir pelos novos
cp pr-ready/nyx/themes/design_tokens.py nyx/themes/
cp pr-ready/nyx/themes/glyphs.py nyx/themes/
cp pr-ready/nyx/themes/ascii_art.py nyx/themes/
cp pr-ready/nyx/agent/banner.py nyx/agent/

# 3. Rodar o gauntlet
./run.sh --gauntlet --only visual
./run.sh --gauntlet --only rapido

# 4. Smoke test interativo
./run.sh
# (observe boot neofetch se seu terminal estiver com >=100 cols)
```

## Migração de chamadas existentes

A API antiga continua funcionando — esses imports não quebram:

```python
from nyx.themes.design_tokens import (
    ANSI_ACCENT_FG, ANSI_DIM, ANSI_RESET, BOX_CHARS, BULLETS, SPINNER_FRAMES,
    NYX_ACCENT,
)
```

**Mas** a partir desse PR, o caminho recomendado para code novo é:

```python
from nyx.themes.design_tokens import get_active_theme, apply_theme

theme = get_active_theme()
accent_fg = theme.ansi_accent_fg
ember_fg = theme.ansi_ember_fg
palette = theme.palette  # dataclass com .bg, .accent, .ember, ...

# Trocar tema em runtime (hot-reload)
apply_theme(aesthetic_id="cyber", entity_id="luna")
```

E para glifos:

```python
from nyx.themes.glyphs import glyphs_for

g = glyphs_for(theme.aesthetic.id)  # respeita locale ASCII fallback
border_top = f"{g.box.tl}{g.box.h * 20}{g.box.tr}"
spinner = g.spinner  # tupla de frames
```

## Próximos PRs sugeridos (não inclusos aqui)

1. **`/theme` command** que consome `apply_theme()` e persiste em `~/.nyx/config.toml`
2. **`render_tool_card_*`** refatorado pra usar `theme.ansi_*` em vez de hardcode
3. **`/doctor`** com checagem nova: `terminal supports utf-8?` + `cols >= ?`
4. **Onboarding** (`nyx/welcome.py`) que pergunta o estético na primeira execução
5. **Observer no banner** — `subscribe()` pra re-renderizar quando o tema troca

Cada um desses é incremental e mantém a compat. O PR atual é apenas a **fundação tipográfica** (sprint 01 do roadmap).

## Notas de compatibilidade

- `themes/__init__.py` (ThemeManager classe) **não foi tocado**. Continua carregando os JSONs em `themes/entities/`. O novo sistema de Entity vive em paralelo até alguém migrar.
- O `compose(aesthetic, entity)` herda accent + glow da entidade; o resto (bg, ember, tipografia) vem do estético. Decisão intencional: a entidade é a "voz", o estético é a "língua".

— gerado por design doc, revisado por humano antes do merge

```text
"Perfeição não é quando não há mais nada para adicionar,
 mas quando não há mais nada para remover."
                                    — Antoine de Saint-Exupéry
```
