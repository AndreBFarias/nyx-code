# SPRINT VISUAL-LAYOUT-01 — design_tokens_extended.py (5 aesthetics + 7 entities)

## 0. SPEC (machine-readable)

```yaml
sprint:
  id: VISUAL-LAYOUT-01
  title: "Portar AESTHETICS (5) + ENTITIES (7) do novo_layout/src/themes.js para design_tokens_extended.py"
  onda: 24
  bloco: 24.2 Visual Layout
  prioridade: ALTA
  tipo: Feature
  dependencias: []
  desbloqueia: [VISUAL-LAYOUT-02, VISUAL-LAYOUT-05, VISUAL-LAYOUT-08]

  touches: []
  creates:
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/themes/design_tokens_extended.py
      reason: "5 aesthetics (default, arcano, cyberpunk, brutalist, mecha, editorial) + 7 entities (nyx, eris, juno, lars, luna, mars, somn). Compatível com paleta D atual via AESTHETICS['default'] + ENTITIES['nyx']."
  removes: []

  n_to_n_pairs:
    - descricao: "Paleta D do design_tokens.py atual = default aesthetic + nyx entity"
      paths:
        - /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/themes/design_tokens.py
        - /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/themes/design_tokens_extended.py

  forbidden:
    - "Hex fora de design_tokens*"
    - "Emoji em comentários ou docstrings"
    - "Menção a IA externa"
    - "Quebrar invariante #6 (hex só em design_tokens*) ou #14 (glifos canônicos)"

  tests:
    - cmd: "bash scripts/sprint_invariants.sh"
      timeout: 60
      deve_passar: "PASS 14, FAIL 0"
    - cmd: "./venv/bin/python -c 'from nyx.themes.design_tokens_extended import AESTHETICS, ENTITIES; assert len(AESTHETICS) == 5 and len(ENTITIES) == 7'"
      timeout: 10
      deve_passar: "import ok + tamanhos corretos"

  acceptance_criteria:
    - "Arquivo nyx/themes/design_tokens_extended.py criado"
    - "5 keys em AESTHETICS: default, arcano, cyberpunk, brutalist, mecha, editorial (note: default sobrescreve nenhuma anteriormente; total 5)"
    - "7 keys em ENTITIES: nyx, eris, juno, lars, luna, mars, somn"
    - "Cada aesthetic tem: palette, type (font weights/tracking), glyphs (box, junctions, spinners)"
    - "Cada entity tem accent override + glow"
    - "Smoke boot ok"
    - "Invariantes 14/14 (incluindo #6 hex e #14 glifos)"
```

---

# Sprint VISUAL-LAYOUT-01 — design_tokens_extended.py (5 aesthetics + 7 entities)

**Status:** PENDENTE
**Data criação:** 2026-05-18
**Modelo obrigatório:** claude-opus-4-7 (sem subagentes)

---

## Contexto do projeto (snapshot — não referência)

> **ADRs relevantes:**
> - ADR-001 Local First: tudo offline.
> - ADR-004 Zero Emojis.
> - ADR-005 Anonimato.
> - ADR-006 PT-BR acentuação.
> - ADR-023 Design System (paleta D: turquesa #00D4AA + roxo #9D4EDD).
> - ADR-029 Layout Parity (banner 3 linhas, toolbar pipes).
>
> **Estado:** design_tokens.py atual tem apenas paleta D fixa. novo_layout/src/themes.js (usuário entregou) propõe 5 estéticos visuais + 7 entidades. Sprint porta a estrutura para Python preservando paleta D como `AESTHETICS["default"] + ENTITIES["nyx"]`.

---

## Problema

O ADR-023 estabelece paleta D (turquesa + roxo) como única identidade visual. O usuário sinalizou intenção de oferecer variantes estéticas (Arcano, Cyberpunk, Brutalist, Mecha, Editorial) e entidades (Nyx, Eris, Juno, Lars, Luna, Mars, Somn). Hoje não existe estrutura Python para representar essa combinação. Tudo é hardcoded em `nyx/themes/design_tokens.py`.

### Sintoma observável

`grep -c "0x00D4AA\|#00D4AA" nyx/themes/design_tokens.py` retorna ocorrências locais; tentativa de trocar aesthetic exige reescrita do arquivo.

---

## Solução proposta

Criar `nyx/themes/design_tokens_extended.py` com:
- `AESTHETICS: dict[str, dict]` — 5 estéticos (default, arcano, cyberpunk, brutalist, mecha, editorial) cada um com palette, type, glyphs.
- `ENTITIES: dict[str, dict]` — 7 entidades cada uma com accent + accent_lo + glow.
- `compose(aesthetic_name, entity_name) -> dict` — merge das duas em paleta única.
- Função `get_active() -> dict` — lê env `NYX_AESTHETIC` (default "default") e `NYX_ENTITY` (default "nyx").

`design_tokens.py` (atual) **não é modificado**. Os arquivos coexistem: tokens.py é a paleta D imutável, extended.py oferece a opção quando módulos consumidores quiserem alternar.

---

## Arquivos alvo (paths absolutos)

### `/home/andrefarias/Desenvolvimento/Nyx-Code/nyx/themes/design_tokens_extended.py`

Estrutura literal:

```python
"""design_tokens_extended.py — paletas combinatórias (5 aesthetics x 7 entities).

Backwards compatible: AESTHETICS["default"] + ENTITIES["nyx"] = paleta D (ADR-023).

Uso:
    from nyx.themes.design_tokens_extended import compose, get_active
    tokens = compose("arcano", "nyx")   # roxo Nyx em estética Arcano
    tokens = get_active()               # respeita NYX_AESTHETIC + NYX_ENTITY do .env
"""

from __future__ import annotations

import os
from typing import Any

AESTHETICS: dict[str, dict[str, Any]] = {
    "default": {
        # Paleta D atual (ADR-023): minimalista, sem efeitos
        "name": "Default (paleta D)",
        "palette": {
            "bg": "#0E0F1A", "bg_soft": "#1A1D29", "bg_inset": "#0A0B14",
            "ink": "#E8E8E8", "ink_dim": "#A0A8B5", "ink_muted": "#6C7A89",
            "accent": "#00D4AA", "accent_lo": "#00A88A",
            "ember": "#9D4EDD", "success": "#00D4AA", "warning": "#FFB454",
            "error": "#FF6B6B", "info": "#86C5FF",
            "glow": "rgba(0, 212, 170, 0.0)", "glow_soft": "rgba(0, 212, 170, 0.0)",
        },
        "type": {"mono": "ui-monospace, monospace", "mono_weight": 400, "mono_track": "0", "mono_leading": 1.5},
        "glyphs": {"tl": "╭", "tr": "╮", "bl": "╰", "br": "╯", "h": "─", "v": "│"},
    },
    "arcano": {
        "name": "Arcano",
        "palette": {
            "bg": "#0E0820", "bg_soft": "#16102B", "bg_inset": "#08051A",
            "ink": "#E8E0D0", "ink_dim": "#9C8FB0", "ink_muted": "#5A4F70",
            "accent": "#9D4EDD", "accent_lo": "#5A189A",
            "ember": "#FFB454", "success": "#7DD3A0", "warning": "#FFB454",
            "error": "#E5484D", "info": "#86C5FF",
            "glow": "rgba(157, 78, 221, 0.35)", "glow_soft": "rgba(157, 78, 221, 0.15)",
        },
        "type": {"mono": "'JetBrains Mono', monospace", "mono_weight": 400, "mono_track": "0.01em", "mono_leading": 1.55},
        "glyphs": {"tl": "╭", "tr": "╮", "bl": "╰", "br": "╯", "h": "─", "v": "│"},
    },
    "cyberpunk": {
        "name": "Cyberpunk",
        "palette": {
            "bg": "#000000", "bg_soft": "#0D0D0D", "bg_inset": "#1A0A1A",
            "ink": "#F5F5F5", "ink_dim": "#888888", "ink_muted": "#444444",
            "accent": "#00F5FF", "accent_lo": "#00B8C0",
            "ember": "#FF00AA", "success": "#00FF88", "warning": "#FFD700",
            "error": "#FF0066", "info": "#00F5FF",
            "glow": "rgba(0, 245, 255, 0.4)", "glow_soft": "rgba(255, 0, 170, 0.2)",
        },
        "type": {"mono": "'JetBrains Mono', monospace", "mono_weight": 500, "mono_track": "0", "mono_leading": 1.4},
        "glyphs": {"tl": "┏", "tr": "┓", "bl": "┗", "br": "┛", "h": "━", "v": "┃"},
    },
    "brutalist": {
        "name": "Brutalist",
        "palette": {
            "bg": "#FAFAF7", "bg_soft": "#F0F0EC", "bg_inset": "#E8E8E0",
            "ink": "#0A0A0A", "ink_dim": "#3A3A3A", "ink_muted": "#7A7A7A",
            "accent": "#0A0A0A", "accent_lo": "#3A3A3A",
            "ember": "#C8102E", "success": "#1B5E20", "warning": "#E65100",
            "error": "#C8102E", "info": "#0D47A1",
            "glow": "rgba(0, 0, 0, 0)", "glow_soft": "rgba(0, 0, 0, 0)",
        },
        "type": {"mono": "'Courier New', monospace", "mono_weight": 700, "mono_track": "0", "mono_leading": 1.5},
        "glyphs": {"tl": "+", "tr": "+", "bl": "+", "br": "+", "h": "-", "v": "|"},
    },
    "mecha": {
        "name": "Mecha",
        "palette": {
            "bg": "#0C1117", "bg_soft": "#161C22", "bg_inset": "#0A0F14",
            "ink": "#E0E6ED", "ink_dim": "#8A95A5", "ink_muted": "#4A5460",
            "accent": "#FFAB00", "accent_lo": "#CC8800",
            "ember": "#FF3D3D", "success": "#52D072", "warning": "#FFAB00",
            "error": "#FF3D3D", "info": "#3DAEFF",
            "glow": "rgba(255, 171, 0, 0.3)", "glow_soft": "rgba(255, 61, 61, 0.2)",
        },
        "type": {"mono": "'Roboto Mono', monospace", "mono_weight": 500, "mono_track": "0.02em", "mono_leading": 1.4},
        "glyphs": {"tl": "┌", "tr": "┐", "bl": "└", "br": "┘", "h": "─", "v": "│"},
    },
    "editorial": {
        "name": "Editorial",
        "palette": {
            "bg": "#FFFBF0", "bg_soft": "#F5F0E0", "bg_inset": "#FAFAF7",
            "ink": "#1A1A1A", "ink_dim": "#5A5A5A", "ink_muted": "#9A9A9A",
            "accent": "#7A4A1A", "accent_lo": "#5A3A0A",
            "ember": "#C8102E", "success": "#1B5E20", "warning": "#E65100",
            "error": "#C8102E", "info": "#0D47A1",
            "glow": "rgba(0, 0, 0, 0)", "glow_soft": "rgba(0, 0, 0, 0)",
        },
        "type": {"mono": "'Crimson Pro', serif", "mono_weight": 400, "mono_track": "0", "mono_leading": 1.6},
        "glyphs": {"tl": "(", "tr": ")", "bl": "(", "br": ")", "h": "-", "v": "|"},
    },
}

ENTITIES: dict[str, dict[str, Any]] = {
    "nyx":  {"name": "Nyx",  "accent": "#00D4AA", "accent_lo": "#00A88A", "glow": "rgba(0, 212, 170, 0.30)"},
    "eris": {"name": "Eris", "accent": "#FF79C6", "accent_lo": "#C8568D", "glow": "rgba(255, 121, 198, 0.30)"},
    "juno": {"name": "Juno", "accent": "#A4CB58", "accent_lo": "#7AA040", "glow": "rgba(164, 203, 88, 0.30)"},
    "lars": {"name": "Lars", "accent": "#50FA7B", "accent_lo": "#3EC85F", "glow": "rgba(80, 250, 123, 0.30)"},
    "luna": {"name": "Luna", "accent": "#BD93F9", "accent_lo": "#9070C8", "glow": "rgba(189, 147, 249, 0.30)"},
    "mars": {"name": "Mars", "accent": "#FF5555", "accent_lo": "#C84040", "glow": "rgba(255, 85, 85, 0.30)"},
    "somn": {"name": "Somn", "accent": "#8BE9FD", "accent_lo": "#6BB8C8", "glow": "rgba(139, 233, 253, 0.30)"},
}


def compose(aesthetic: str = "default", entity: str = "nyx") -> dict[str, Any]:
    """Combina aesthetic + entity em paleta unificada.

    Aesthetic define bg/ink/glyphs/type. Entity sobrescreve accent + glow.
    Fallback silencioso para 'default' + 'nyx' se nome desconhecido.
    """
    base = AESTHETICS.get(aesthetic, AESTHETICS["default"])
    ent = ENTITIES.get(entity, ENTITIES["nyx"])
    palette = dict(base["palette"])
    palette["accent"] = ent["accent"]
    palette["accent_lo"] = ent["accent_lo"]
    palette["glow"] = ent["glow"]
    return {
        "aesthetic": base["name"],
        "entity": ent["name"],
        "palette": palette,
        "type": dict(base["type"]),
        "glyphs": dict(base["glyphs"]),
    }


def get_active() -> dict[str, Any]:
    """Retorna paleta ativa lendo NYX_AESTHETIC e NYX_ENTITY do ambiente."""
    return compose(
        os.environ.get("NYX_AESTHETIC", "default"),
        os.environ.get("NYX_ENTITY", "nyx"),
    )
```

**Mudanças:**
- Cria arquivo novo de ~140 linhas.
- Estruturas puras (dict). Zero efeito colateral em outros módulos.
- Hex apenas dentro deste arquivo (preserva invariante #6).
- Glifos das aesthetics são variantes ASCII/Unicode legais (não toca os canônicos `○ ◐ ●` de invariante #14, que vivem em `nyx/themes/design_tokens.py`, `nyx/cli.py`, `nyx/agent/output.py`).

---

## Diff esperado

```
+ 1 arquivo criado (nyx/themes/design_tokens_extended.py, ~140 linhas)
~ 0 arquivos modificados
- 0 arquivos removidos
+ ~140 linhas líquidas
```

---

## Comandos de verificação

```bash
# 1. Smoke + invariantes
./run.sh --smoke
bash scripts/sprint_invariants.sh | tail -5

# 2. Import + tamanhos
./venv/bin/python -c '
from nyx.themes.design_tokens_extended import AESTHETICS, ENTITIES, compose, get_active
assert len(AESTHETICS) == 6, f"esperado 6 aesthetics (default + 5 nomeados), got {len(AESTHETICS)}"
assert len(ENTITIES) == 7
t = compose("arcano", "nyx")
assert t["palette"]["accent"] == "#00D4AA"  # nyx override
print("OK", t["aesthetic"], t["entity"])
'

# 3. Audit hex
grep -rn "#[0-9A-Fa-f]\{6\}" nyx/themes/ | grep -v design_tokens
```

---

## Critério binário de aceite

- [ ] Arquivo `nyx/themes/design_tokens_extended.py` existe
- [ ] `AESTHETICS` tem 6 keys (default + 5 nomeados: arcano, cyberpunk, brutalist, mecha, editorial)
- [ ] `ENTITIES` tem 7 keys (nyx, eris, juno, lars, luna, mars, somn)
- [ ] `compose("arcano", "nyx")` retorna dict com accent `#00D4AA`
- [ ] `get_active()` respeita `NYX_AESTHETIC` e `NYX_ENTITY`
- [ ] Smoke boot ok
- [ ] Invariantes 14/14 (especialmente #6 hex e #14 glifos)
- [ ] `ruff` não reclama
- [ ] Sprint movida para `concluidos/`
- [ ] Commit atômico

---

## Riscos

| Risco | Mitigação |
|---|---|
| Hex no design_tokens_extended.py quebra invariante #6 | invariante já permite hex em `nyx/themes/design_tokens*` (testado: regex `design_tokens` casa também `design_tokens_extended`) |
| Glifos novos das aesthetics quebrarem invariante #14 | invariante conta codepoints de `○ ◐ ●` específicos — glifos das aesthetics são outros codepoints, não afetam |

---

*"Cinco aesthetics, sete entidades, uma identidade Nyx." — VISUAL-LAYOUT-01*
