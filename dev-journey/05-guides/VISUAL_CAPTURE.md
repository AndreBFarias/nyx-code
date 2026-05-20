# Visual Capture — midframe + final

Pipeline de captura visual de `scripts/visual/`. Documenta como o Nyx-Code
evidencia UX dinâmica (animações) em PNGs reproduzíveis.

## Problema que resolve

Captura única (apenas frame final) perde estados intermediários:

- Spinner durante warming do modelo (ciclo `⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏`).
- Transição cold → warming → warm (glifos `○ → ◐ → ●`).
- Side rule de streaming de tokens.

Sem o midframe, qualquer PNG vira "foto do destino": esconde o caminho
percorrido. Em revisão visual de UX dinâmico isso é cegueira metodológica.

## Solução

Cada execução salva 2 PNGs:

- `<prefix>_midframe.png` — captura no instante `anim_duration * midframe_pct / 100`.
- `<prefix>_final.png` — captura após `anim_duration` (estado terminal).

Retrocompat: `--midframe-pct 0` ou `--midframe-pct 100` salva apenas o final.
Invocação sem `--out` não dispara captura nenhuma (continua imprimindo o
quadro em stdout, fluxo VISUAL-LAYOUT-06 preservado).

## Comando canônico (terminal kitty)

```bash
NYX_AESTHETIC=arcano ./venv/bin/python scripts/visual/render_aesthetic_showcase.py \
    --midframe-pct 50 \
    --anim-duration-sec 1.0 \
    --out /tmp/showcase_arcano
```

Gera `/tmp/showcase_arcano_midframe.png` e `/tmp/showcase_arcano_final.png`.

Validar diferença literal de bytes:

```bash
sha256sum /tmp/showcase_arcano_midframe.png /tmp/showcase_arcano_final.png \
    | awk '{print $1}' | sort -u | wc -l
# Esperado: 2 (hashes distintos)
```

Se a saída for `1`, midframe e final coincidiram — investigar timing de
refresh do compositor ou aumentar `--anim-duration-sec`.

## Comando canônico (cockpit web)

```bash
./venv/bin/python scripts/visual/render_aesthetic_showcase.py \
    --mode web \
    --url http://127.0.0.1:11437/repl \
    --midframe-pct 50 \
    --anim-duration-sec 3.0 \
    --out /tmp/cockpit_repl
```

Requer `google-chrome` no PATH (validado em `which google-chrome`).
A flag `--virtual-time-budget` do Chrome traduz `delay_sec` em milissegundos
para captura determinística mesmo sem `DISPLAY`.

## Flags disponíveis

| Flag | Default | Faixa | Descrição |
|---|---|---|---|
| `aesthetic` (posicional) | `$NYX_AESTHETIC` ou `default` | string | ID da estética em `AESTHETICS` |
| `--midframe-pct` | `50` | `0..100` | `0` ou `100` desativa midframe |
| `--anim-duration-sec` | `1.0` | float | Tempo total de espera antes da captura final |
| `--out` | `None` | string | Prefix de saída; ausente = sem captura |
| `--mode` | `terminal` | `terminal\|web` | Estratégia de captura |
| `--url` | `None` | string | Obrigatório com `--mode web` |

## Integração com a skill `validacao-visual`  <!-- noqa-acento -->

A skill global `validacao-visual` (`~/.claude/skills/validacao-visual/SKILL.md`)  <!-- noqa-acento -->
define pipeline de 3 tentativas:

1. **Tentativa 1 — CLI X11**: `scrot`, `import`, `xdotool`. É o caminho que
   `capture_terminal()` usa internamente.
2. **Tentativa 2 — claude-in-chrome MCP**: usado pelo validador humano quando
   uma aba do Chrome já está aberta com a UI alvo.
3. **Tentativa 3 — playwright MCP**: para apps web dev local quando Chrome
   não está pareado. Equivalente programático ao que `capture_web()` faz com
   `google-chrome --headless`.

`capture_terminal` é equivalente programático da tentativa 1; `capture_web`
é equivalente programático da tentativa 3. Tentativa 2 fica para captura
humana ad-hoc, fora deste pipeline automatizado.

## Casos de uso

### Spinner durante warming

```bash
# Modelo aquecendo em background, captura aos 0.4s (40% de 1.0s)
NYX_AESTHETIC=arcano ./venv/bin/python scripts/visual/render_aesthetic_showcase.py \
    --midframe-pct 40 --anim-duration-sec 1.0 --out /tmp/spinner_warm
```

O `_midframe.png` deve mostrar um glifo do ciclo Braille; `_final.png`
mostra o estado pós-warm (sem spinner).

### Transição cold → warming → warm

```bash
# Captura 33% (durante warming) + final (warm). anim=3s, midframe=1s.
NYX_AESTHETIC=arcano ./venv/bin/python scripts/visual/render_aesthetic_showcase.py \
    --midframe-pct 33 --anim-duration-sec 3.0 --out /tmp/transition
```

`_midframe.png` deve conter `◐`; `_final.png` deve conter `●`.

### Side rule de streaming

```bash
# Tokens entrando em stream, captura no meio (50%) e no fim.
NYX_AESTHETIC=arcano ./venv/bin/python scripts/visual/render_aesthetic_showcase.py \
    --midframe-pct 50 --anim-duration-sec 2.0 --out /tmp/streaming
```

## Limites

- `--anim-duration-sec` máximo recomendado: 3.0s. Acima disso o gauntlet
  visual fica lento. Sleep total proibido: >2s em script single-shot.
- Sem dependência fora de stdlib + binários do sistema (xdotool, import,
  google-chrome). Não adicionar pyautogui, mss, pillow, selenium.
- PNGs vão para `/tmp/` por padrão — não comitar. Quando precisar de
  evidência permanente, copiar para `dev-journey/07-evidence/`.
- `xdotool search --name kitty` retorna primeira janela encontrada quando
  há várias instâncias de kitty abertas; documente isso ao comparar PNGs
  entre execuções.

## Referências

- Script: `scripts/visual/render_aesthetic_showcase.py`
- Helpers: `scripts/visual/_capture_helpers.py`
- Skill: `~/.claude/skills/validacao-visual/SKILL.md`  <!-- noqa-acento -->: nome canônico do plugin, manter sem acento.
- Sprint origem do midframe: `SPRINT_VALIDATE_VISUAL_MIDFRAME_01.md`
- Sprint precedente (uso atual do pipeline): `SPRINT_VISUAL_LAYOUT_06.md`
