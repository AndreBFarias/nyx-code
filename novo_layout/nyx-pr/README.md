# nyx-pr/ — pacote PR-ready pro Nyx Code

Arquivos prontos pra abrir PR direto no [AndreBFarias/nyx-code](https://github.com/AndreBFarias/nyx-code).
Tudo respeitando ADRs existentes (004 zero emoji, 005 anonimato, 006 PT-BR, 023 design tokens fonte única).

## O que tem aqui

```
nyx-pr/
├── README.md                          ← este arquivo
└── nyx/
    ├── themes/
    │   ├── __init__.py                ← builder + persistência + reexports retrocompat
    │   ├── design_tokens.py           ← REFATORADO (dataclasses + retrocompat)
    │   ├── aesthetics.py              ← NOVO — 5 estéticos
    │   ├── entities.py                ← NOVO — 7 entidades como dataclass
    │   ├── glyphs.py                  ← NOVO — Box/Braille por estético + ASCII fallback
    │   └── ascii_art.py               ← NOVO — banner NYX + sigilo de ritual
    └── agent/
        └── banner.py                  ← REFATORADO (3 modos: compact/wide/neofetch)
```

## Ordem sugerida de merge

### PR-1 · Fundação (não-breaking)
Adicione os **novos arquivos** sem mexer nos existentes:

- `nyx/themes/aesthetics.py`
- `nyx/themes/entities.py`  (coexiste com o JSON; usar o que preferir)
- `nyx/themes/glyphs.py`
- `nyx/themes/ascii_art.py`

Nenhum import existente quebra. O `nyx/themes/__init__.py` atual continua valendo.

### PR-2 · Substituir design_tokens.py
Substitua o `nyx/themes/design_tokens.py` pelo novo. **Retrocompatível**:
todas as constantes globais (`NYX_ACCENT`, `ANSI_ACCENT_FG`, `BOX_CHARS`,
`BULLETS`, `SPINNER_FRAMES`) continuam exportadas. Acrescenta dataclasses
e o composer `build_theme()`.

Testes esperados: tudo que importa de `design_tokens` continua passando.

### PR-3 · Substituir __init__.py do pacote themes
Substitua `nyx/themes/__init__.py`. Mantém o `ThemeManager` legado funcionando
(via reexport) E adiciona `build_theme`, `load_theme_from_config`,
`save_theme_to_config`. Persistência em `~/.nyx/config.toml`.

### PR-4 · Refatorar banner.py
Substitua `nyx/agent/banner.py`. Mantém assinatura de `build_banner()` mas
adiciona o modo `neofetch` (ativável com `NYX_BANNER=neofetch ./run.sh`).
Os modos compact e wide preservam o output atual byte-por-byte.

### PR-5+ · Refatorar consumers (incremental)
Migre `output.py`, comandos `_observability.py`, etc. para consumirem
`theme.ansi.accent` ao invés de `ANSI_ACCENT_FG`. **Cada arquivo
independente**. As constantes globais continuam exportadas, então é
opcional.

## Como usar (nova API)

```python
from nyx.themes import build_theme

theme = build_theme("arcano", "nyx")

# cores como escape codes ANSI
print(f"{theme.ansi.accent}Nyx{theme.ansi.reset}")
print(f"{theme.ansi.ember}aviso{theme.ansi.reset}")

# glifos do estético
g = theme.glyphs
print(f"  {g.tl}{g.h * 60}{g.tr}")
print(f"  {g.v}  conteúdo")
print(f"  {g.bl}{g.h * 60}{g.br}")

# spinner braille (já no estético)
import time
for frame in theme.glyphs.spinner_frames * 3:
    print(f"\r  {theme.ansi.accent}{frame}{theme.ansi.reset}", end="", flush=True)
    time.sleep(0.08)
```

## Como trocar tema em tempo de execução

```python
from nyx.themes import save_theme_to_config, build_theme

save_theme_to_config("cyber", "luna")
theme = build_theme("cyber", "luna")  # cyberpunk com accent roxo dracula
```

Override por env (precedência maior que config):

```bash
NYX_AESTHETIC=mecha NYX_ENTITY=mars ./run.sh
```

Forçar ASCII fallback:

```bash
NYX_FORCE_ASCII=1 ./run.sh   # sem UTF-8
NYX_FORCE_UTF8=1  ./run.sh   # força UTF-8 mesmo sem locale
```

## Como ativar banner neofetch

```bash
NYX_BANNER=neofetch ./run.sh
```

Mostra arte ASCII "NYX" + system info (SO, kernel, GPU, VRAM, RAM, etc).
Tudo coletado via `/proc/*` e `nvidia-smi --query-gpu=...` com timeout 0.5s.
Falha em qualquer item degrada para `—`, nunca crasha o boot.

## Notas de compatibilidade

- **Python 3.11+** (usa `tomllib` da stdlib)
- **Sem deps novas** — apenas stdlib
- **Locale detection**: respeita `LC_ALL`, `LANG`, e overrides explícitos
- **Frozen dataclasses**: temas e palettes são imutáveis após `build_theme`

## Próximos PRs sugeridos (não inclusos aqui)

- `nyx/agent/output.py` — refatorar `render_tool_card_start/end` pra consumir `theme.glyphs`
- `nyx/agent/commands/theme.py` — slash command `/theme` com TUI de seleção
- `nyx/onboarding.py` — fluxo 3-passos primeira vez
- `nyx/agent/services/heartbeat.py` — sparkline Braille de tps do modelo
- `nyx/agent/orchestrator/wave.py` — dispatch de agentes paralelos com worktree isolation

---

> "Cada PR é uma decisão de design feita em código." — anônimo
