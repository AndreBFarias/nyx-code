# SPRINT VALIDATE-VISUAL-MIDFRAME-01 — Captura PNG do meio da animação além do frame final

## 0. SPEC (machine-readable)

```yaml
sprint:
  id: VALIDATE-VISUAL-MIDFRAME-01
  title: "Pipeline visual captura midframe (~50%) + final em vez de só final"
  onda: 25
  bloco: 25.1 Validação visual dinâmica
  prioridade: MEDIA
  tipo: Feature
  dependencias: [VALIDATE-FINAL-01-PARTE-2, VISUAL-LAYOUT-06]
  desbloqueia: []

  touches:
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/scripts/visual/render_aesthetic_showcase.py
      reason: "Adicionar argparse, flag --midframe-pct, flag --out, lógica de dupla captura."
      linhas_alvo: "104-114"
  creates:
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/scripts/visual/_capture_helpers.py
      reason: "Lib comum para captura terminal (xdotool+import) e web (chrome --headless --screenshot). Reutilizável por outros scripts de scripts/visual/."
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/dev-journey/05-guides/VISUAL_CAPTURE.md
      reason: "Documentar midframe vs final, comandos canônicos, casos de uso (spinner, transição cold→warming→warm, side rule streaming)."
  removes: []

  n_to_n_pairs:
    - descricao: "Flag --midframe-pct precisa ter mesmo nome e default em script principal e em _capture_helpers.MIDFRAME_PCT_DEFAULT"
      paths:
        - /home/andrefarias/Desenvolvimento/Nyx-Code/scripts/visual/render_aesthetic_showcase.py
        - /home/andrefarias/Desenvolvimento/Nyx-Code/scripts/visual/_capture_helpers.py

  forbidden:
    - "Remover captura final atual (apenas adicionar midframe; final continua sendo gerado)"
    - "Adicionar sleep estático >2s (degradaria velocidade do gauntlet visual)"
    - "Dependência nova fora de stdlib (proibido: pyautogui, mss, pillow, selenium). Usar binários já presentes: xdotool, import, scrot, kitty, google-chrome."
    - "Adicionar emoji em código, doc, commit"
    - "Menção a Claude/Anthropic/GPT/Gemini/Copilot em .py"
    - "Hardcode de path absoluto fora de design_tokens/settings"

  tests:
    - cmd: "./run.sh --smoke"
      timeout: 60
      deve_passar: "boot ok"
    - cmd: "bash scripts/sprint_invariants.sh --ci"
      timeout: 60
      deve_passar: "14/14 PASS"
    - cmd: "NYX_AESTHETIC=arcano ./venv/bin/python scripts/visual/render_aesthetic_showcase.py --midframe-pct 50 --out /tmp/visual_test"
      timeout: 30
      deve_passar: "exit 0 e gera /tmp/visual_test_midframe.png + /tmp/visual_test_final.png"
    - cmd: "test -f /tmp/visual_test_midframe.png && test -f /tmp/visual_test_final.png"
      timeout: 5
      deve_passar: "ambos os PNGs existem"
    - cmd: "sha256sum /tmp/visual_test_midframe.png /tmp/visual_test_final.png | awk '{print $1}' | sort -u | wc -l"
      timeout: 5
      deve_passar: "2 (hashes distintos -- midframe != final)"
    - cmd: "NYX_AESTHETIC=arcano ./venv/bin/python scripts/visual/render_aesthetic_showcase.py --midframe-pct 0 --out /tmp/visual_compat_zero"
      timeout: 30
      deve_passar: "exit 0 e gera APENAS /tmp/visual_compat_zero_final.png (sem midframe)"
    - cmd: "NYX_AESTHETIC=arcano ./venv/bin/python scripts/visual/render_aesthetic_showcase.py --midframe-pct 100 --out /tmp/visual_compat_hundred"
      timeout: 30
      deve_passar: "exit 0 e gera APENAS /tmp/visual_compat_hundred_final.png (sem midframe)"

  acceptance_criteria:
    - "Execução padrão com --midframe-pct 50 gera 2 PNGs: <out>_midframe.png e <out>_final.png"
    - "SHA256 dos 2 PNGs sao DIFERENTES (prova de captura em momentos distintos)"
    - "--midframe-pct=0 ou --midframe-pct=100 faz apenas captura final (retrocompatibilidade)"
    - "Pipeline funciona em terminal kitty (xdotool+import) e em Chrome headless (cockpit web)"
    - "Em animação Nyx existente (spinner durante warming) midframe mostra glifo intermediário (◐) e final mostra terminal (●) -- prova literal de diff de bytes"
    - "Acentuação PT-BR correta em VISUAL_CAPTURE.md (já, é, í, ó, ú, ã, ç, etc.)"
    - "Sprint anterior (VALIDATE-FINAL-01-PARTE-2 + VISUAL-LAYOUT-06) NÃO regride: smoke ok + invariantes 14/14"
    - "Skill validacao-visual citada em VISUAL_CAPTURE.md como pipeline 3-tentativas (scrot/import → claude-in-chrome MCP → playwright MCP)"
```

---

# Sprint VALIDATE-VISUAL-MIDFRAME-01 — Captura PNG do meio da animação além do frame final

**Status:** CONCLUIDA (2026-05-19)
**Data criação:** 2026-05-19
**Modelo obrigatório:** claude-opus-4-7 (sem subagentes)

---

## Contexto do projeto (snapshot — não referência)

> **ADRs relevantes (colar o essencial inline, não apontar arquivo):**
>
> - ADR-001 Local First: tudo offline.
> - ADR-004 Zero Emojis: em tudo.
> - ADR-005 Anonimato: sem menção a IA em código/commits.
> - ADR-006 PT-BR: acentuação obrigatória.
> - ADR-013 Integração Obrigatória: nada solto, tudo no registry.
> - ADR-014 Testes via Gauntlet: tudo no gauntlet (este caso é script auxiliar de validação, não tool runtime).
>
> **Estado do sistema (na data da sprint):**
> - Python 3.10+, modelo `qwen3:4b` no Ollama porta 11435, proxy 11436.
> - 35 tools, 52 commands, 9 services. `cli.py` 792 linhas (pós INFRA-CLI-SPLIT-03).
> - Sprint anterior: VALIDATE-FINAL-01-PARTE-2 CONCLUIDA (commit 8101062), VISUAL-LAYOUT-06 CONCLUIDA (commit 0d1b6e2).
> - Binários de captura disponíveis (confirmado via `which`): `/usr/bin/xdotool`, `/usr/bin/import`, `/usr/bin/scrot`, `/usr/bin/kitty`, `/home/andrefarias/.local/bin/google-chrome`.
> - Script-alvo `scripts/visual/render_aesthetic_showcase.py` atualmente tem 115 linhas, sem argparse, lê só `sys.argv[1]` ou `NYX_AESTHETIC`. Imprime quadro estático em stdout (não anima).

---

## Problema

Capturas visuais do pipeline `scripts/visual/` atualmente geram **apenas o frame final** da renderização. Animações dinâmicas do Nyx-Code não ficam evidenciadas em PNG:

- **Spinner** durante warming do modelo: ciclo `⠋ ⠙ ⠹ ⠸ ⠼ ⠴ ⠦ ⠧ ⠇ ⠏` invisível em screenshot estático.
- **Transição cold → warming → warm** do model state (`nyx/cli_keybindings.py:266`, `nyx/cli_callbacks.py:131`): glifos `○ → ◐ → ●` perdidos.
- **Side rule de streaming** de tokens (`nyx/agent/streaming.py:68`): apenas o final fica visível.

Achado catalogado em VALIDATE-FINAL-01-PARTE-2 (commit 8101062, bloco anti-débito materializado, linha 79 da sprint concluída) como item não-bloqueante de v1.0. Esta sprint resolve o débito.

**Sintoma observável:** rodando `NYX_AESTHETIC=arcano python3 scripts/visual/render_aesthetic_showcase.py` em terminal e tirando `scrot -u`, o PNG mostra apenas o quadro final pintado; estados intermediários de qualquer animação dinâmica não são capturados.

---

## Solução proposta

Adicionar argparse ao `render_aesthetic_showcase.py` e criar `_capture_helpers.py` com duas funções: `capture_terminal(window_name, out_path)` (xdotool+import) e `capture_web(url, out_path)` (chrome headless). O script principal aceita `--midframe-pct PCT` (default 50, range 0..100) e `--out PREFIX` (default `/tmp/aesthetic_<id>`):

- Se `PCT in (0, 100)`: comportamento atual preservado, salva só `<prefix>_final.png`.
- Se `PCT in 1..99`: agenda captura via subprocess timer em `duracao_anim * PCT/100`, salva `<prefix>_midframe.png`, depois aguarda render concluir e salva `<prefix>_final.png`.

Duração da animação detectada por: (1) flag opcional `--anim-duration-sec FLOAT` (default 1.0s para showcase estático, 3.0s para animações reais); (2) sem sleep estático grande — usa `subprocess.Popen` + `time.sleep(duracao * pct/100)` apenas no thread de captura.

---

## Arquivos alvo (paths absolutos)

### `/home/andrefarias/Desenvolvimento/Nyx-Code/scripts/visual/render_aesthetic_showcase.py`

**Antes (linhas 104-114):**
```python
def main() -> int:
    if len(sys.argv) > 1:
        aid = sys.argv[1]
    else:
        aid = os.environ.get("NYX_AESTHETIC", "default")
    print(render(aid))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

**Depois:**
```python
def main() -> int:
    import argparse
    from scripts.visual._capture_helpers import (
        MIDFRAME_PCT_DEFAULT,
        capture_terminal,
        capture_web,
        should_capture_midframe,
    )

    parser = argparse.ArgumentParser(
        description="Render aesthetic showcase com captura midframe + final."
    )
    parser.add_argument("aesthetic", nargs="?", default=None,
                        help="ID da aesthetic (default: $NYX_AESTHETIC ou 'default')")
    parser.add_argument("--midframe-pct", type=int, default=MIDFRAME_PCT_DEFAULT,
                        help="Percentual da duração para captura intermediária (0..100). "
                             "0 ou 100 desabilita midframe. Default: 50.")
    parser.add_argument("--anim-duration-sec", type=float, default=1.0,
                        help="Duração total da animação em segundos. Default: 1.0.")
    parser.add_argument("--out", type=str, default=None,
                        help="Prefix de saída. Default: /tmp/aesthetic_<id>.")
    parser.add_argument("--mode", choices=["terminal", "web"], default="terminal",
                        help="Modo de captura: terminal (xdotool+import) ou web (chrome headless).")
    parser.add_argument("--url", type=str, default=None,
                        help="URL para modo web (ex.: http://127.0.0.1:11437/repl).")
    args = parser.parse_args()

    aid = args.aesthetic or os.environ.get("NYX_AESTHETIC", "default")
    out_prefix = args.out or f"/tmp/aesthetic_{aid}"

    # Render do quadro (mesmo de sempre, comportamento preservado).
    print(render(aid))

    # Captura.
    if args.mode == "terminal":
        if should_capture_midframe(args.midframe_pct):
            capture_terminal(window_name="kitty",
                             out_path=f"{out_prefix}_midframe.png",
                             delay_sec=args.anim_duration_sec * args.midframe_pct / 100.0)
        capture_terminal(window_name="kitty",
                         out_path=f"{out_prefix}_final.png",
                         delay_sec=args.anim_duration_sec)
    else:
        if args.url is None:
            print("ERRO: --mode web exige --url", file=sys.stderr)
            return 2
        if should_capture_midframe(args.midframe_pct):
            capture_web(url=args.url,
                        out_path=f"{out_prefix}_midframe.png",
                        delay_sec=args.anim_duration_sec * args.midframe_pct / 100.0)
        capture_web(url=args.url,
                    out_path=f"{out_prefix}_final.png",
                    delay_sec=args.anim_duration_sec)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

**Mudanças:**
- Adicionar `argparse` (stdlib, sem dependência nova).
- Aceitar posicional `aesthetic` mantendo retrocompat com `sys.argv[1]` e `NYX_AESTHETIC`.
- Quatro flags novas: `--midframe-pct`, `--anim-duration-sec`, `--out`, `--mode`, `--url`.
- Chamar helpers de captura ao final do render.
- Sleep agendado é `anim_duration * pct/100` — para defaults `1.0s * 0.5 = 0.5s`, bem abaixo do limite proibido (>2s).

### `/home/andrefarias/Desenvolvimento/Nyx-Code/scripts/visual/_capture_helpers.py` (NOVO)

```python
"""Helpers de captura visual para scripts/visual/.

Duas estratégias canônicas:
- capture_terminal: xdotool localiza janela kitty, import salva PNG da janela.
- capture_web: google-chrome --headless --screenshot salva PNG da URL.

Ambas honram delay_sec antes de capturar para permitir frame intermediário
em animações (midframe). Sem dependência nova; usa subprocess + binários
já presentes no sistema (xdotool, import, google-chrome).

Uso típico:
    from scripts.visual._capture_helpers import capture_terminal, should_capture_midframe
    if should_capture_midframe(50):
        capture_terminal("kitty", "/tmp/teste_midframe.png", delay_sec=0.5)
    capture_terminal("kitty", "/tmp/teste_final.png", delay_sec=1.0)
"""

from __future__ import annotations

import subprocess
import sys
import time
from pathlib import Path

MIDFRAME_PCT_DEFAULT = 50


def should_capture_midframe(pct: int) -> bool:
    """Midframe ativo apenas em 1..99 (exclui extremos)."""
    return 0 < pct < 100


def capture_terminal(window_name: str, out_path: str, delay_sec: float) -> int:
    """Captura janela de terminal via xdotool+import.

    Retorna exit code (0 = ok). Em caso de DISPLAY vazio ou binário ausente,
    imprime erro literal e retorna != 0 (sem raise, para não derrubar o pipeline).
    """
    time.sleep(max(0.0, delay_sec))
    try:
        wid = subprocess.run(
            ["xdotool", "search", "--name", window_name],
            capture_output=True, text=True, check=True,
        ).stdout.strip().splitlines()
        if not wid:
            print(f"ERRO captura terminal: janela '{window_name}' nao encontrada", file=sys.stderr)
            return 1
        target = wid[0]
        Path(out_path).parent.mkdir(parents=True, exist_ok=True)
        subprocess.run(
            ["import", "-window", target, out_path],
            check=True,
        )
        return 0
    except FileNotFoundError as e:
        print(f"ERRO captura terminal: binario ausente ({e})", file=sys.stderr)
        return 2
    except subprocess.CalledProcessError as e:
        print(f"ERRO captura terminal: comando falhou ({e})", file=sys.stderr)
        return 3


def capture_web(url: str, out_path: str, delay_sec: float) -> int:
    """Captura URL via google-chrome --headless --screenshot.

    delay_sec é traduzido em --virtual-time-budget (ms) para frame
    determinístico em animação. Retorna exit code (0 = ok).
    """
    try:
        Path(out_path).parent.mkdir(parents=True, exist_ok=True)
        ms = int(max(0.0, delay_sec) * 1000)
        subprocess.run(
            [
                "google-chrome",
                "--headless",
                "--disable-gpu",
                "--no-sandbox",
                f"--screenshot={out_path}",
                f"--virtual-time-budget={ms}",
                "--window-size=1280,800",
                url,
            ],
            check=True,
            capture_output=True,
        )
        return 0
    except FileNotFoundError as e:
        print(f"ERRO captura web: binario ausente ({e})", file=sys.stderr)
        return 2
    except subprocess.CalledProcessError as e:
        print(f"ERRO captura web: chrome falhou ({e})", file=sys.stderr)
        return 3
```

**Mudanças:** arquivo novo, 60 linhas. Sem dependência fora de stdlib. Erros são logados em stderr sem raise — pipeline visual segue mesmo se captura falha (consistente com pipeline 3-tentativas da skill `validacao-visual`).

### `/home/andrefarias/Desenvolvimento/Nyx-Code/dev-journey/05-guides/VISUAL_CAPTURE.md` (NOVO)

```markdown
# Visual Capture — midframe + final

Pipeline de captura visual de `scripts/visual/`. Documenta como o Nyx-Code
evidencia UX dinâmica (animações) em PNGs reproduzíveis.

## Problema que resolve

Captura única (apenas frame final) perde estados intermediários:
- Spinner durante warming do modelo (ciclo `⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏`).
- Transição cold → warming → warm (glifos `○ → ◐ → ●`).
- Side rule de streaming de tokens.

## Solução

Cada execução salva 2 PNGs:
- `<prefix>_midframe.png` — captura no instante `anim_duration * midframe_pct / 100`.
- `<prefix>_final.png` — captura após `anim_duration` (estado terminal).

Retrocompat: `--midframe-pct 0` ou `--midframe-pct 100` salva apenas o final.

## Comando canônico (terminal kitty)

```bash
NYX_AESTHETIC=arcano ./venv/bin/python scripts/visual/render_aesthetic_showcase.py \
    --midframe-pct 50 \
    --anim-duration-sec 1.0 \
    --out /tmp/showcase_arcano
```

Gera `/tmp/showcase_arcano_midframe.png` e `/tmp/showcase_arcano_final.png`.
Validar diferença literal:

```bash
sha256sum /tmp/showcase_arcano_midframe.png /tmp/showcase_arcano_final.png \
    | awk '{print $1}' | sort -u | wc -l
# Esperado: 2 (hashes distintos)
```

## Comando canônico (cockpit web)

```bash
./venv/bin/python scripts/visual/render_aesthetic_showcase.py \
    --mode web \
    --url http://127.0.0.1:11437/repl \
    --midframe-pct 50 \
    --anim-duration-sec 3.0 \
    --out /tmp/cockpit_repl
```

## Integração com a skill `validacao-visual`

A skill global `validacao-visual` (`~/.claude/skills/validacao-visual/SKILL.md`)
define pipeline de 3 tentativas:

1. **Tentativa 1 — CLI X11**: `scrot`, `import`, `xdotool`. É o caminho que
   `capture_terminal()` usa internamente.
2. **Tentativa 2 — claude-in-chrome MCP**: usado pelo validador humano quando
   uma aba do Chrome já está aberta com a UI alvo.
3. **Tentativa 3 — playwright MCP**: para apps web dev local quando Chrome
   não está pareado. Equivalente programático ao que `capture_web()` faz com
   `google-chrome --headless`.

`capture_terminal` é equivalente programático da tentativa 1; `capture_web` é
equivalente programático da tentativa 3. Tentativa 2 fica para captura humana
ad-hoc, fora deste pipeline automatizado.

## Limites

- `--anim-duration-sec` máximo recomendado: 3.0s. Acima disso o gauntlet visual
  fica lento. Sleep total proibido: >2s em script single-shot.
- Sem dependência fora de stdlib + binários do sistema (xdotool, import,
  google-chrome). Não adicionar pyautogui, mss, pillow, selenium.
- PNGs vão para `/tmp/` por padrão — não comitar.
```

**Mudanças:** doc novo, ~70 linhas, PT-BR com acentuação correta.

---

## Diff esperado (resumo)

```
+ 2 arquivos criados (scripts/visual/_capture_helpers.py, dev-journey/05-guides/VISUAL_CAPTURE.md)
~ 1 arquivo modificado (scripts/visual/render_aesthetic_showcase.py)
- 0 arquivos removidos
+ ~200 linhas líquidas
```

---

## Aritmética

Sprint NÃO tem meta numérica de redução de linhas. Adiciona código:

- `render_aesthetic_showcase.py`: 115 L atuais + ~60 L de argparse/captura = ~175 L finais (sem meta de upper bound).
- `_capture_helpers.py`: 0 → ~60 L (arquivo novo, sem meta).
- `VISUAL_CAPTURE.md`: 0 → ~70 L (doc novo, sem meta).

Verificação de comportamento (binário):
- Antes: 1 captura por execução (frame final). Esperado: 2 capturas com `--midframe-pct 50`, 1 captura com `--midframe-pct 0|100`.
- Antes: 0 PNGs distintos. Esperado: 2 PNGs com SHA256 diferentes na execução padrão.

---

## Comandos de verificação (literais, copy-paste)

```bash
# 1. Validação estática
python3 -m ruff check scripts/visual/

# 2. Smoke (não pode regredir)
./run.sh --smoke
# saída esperada: "boot ok"

# 3. Invariantes universais
bash scripts/sprint_invariants.sh --ci
# saída esperada: PASS 14/14

# 4. Comando principal da sprint
NYX_AESTHETIC=arcano ./venv/bin/python scripts/visual/render_aesthetic_showcase.py \
    --midframe-pct 50 \
    --out /tmp/visual_test

# 5. Validar 2 PNGs criados
ls -la /tmp/visual_test_midframe.png /tmp/visual_test_final.png

# 6. Validar SHA256 distintos (prova de captura em momentos diferentes)
sha256sum /tmp/visual_test_midframe.png /tmp/visual_test_final.png \
    | awk '{print $1}' | sort -u | wc -l
# saída esperada: 2

# 7. Validar retrocompat com pct=0
NYX_AESTHETIC=arcano ./venv/bin/python scripts/visual/render_aesthetic_showcase.py \
    --midframe-pct 0 \
    --out /tmp/visual_compat_zero
ls /tmp/visual_compat_zero_midframe.png 2>&1 | grep -q "No such file" && echo "OK: midframe ausente com pct=0"
test -f /tmp/visual_compat_zero_final.png && echo "OK: final presente com pct=0"

# 8. Validar retrocompat com pct=100
NYX_AESTHETIC=arcano ./venv/bin/python scripts/visual/render_aesthetic_showcase.py \
    --midframe-pct 100 \
    --out /tmp/visual_compat_hundred
ls /tmp/visual_compat_hundred_midframe.png 2>&1 | grep -q "No such file" && echo "OK: midframe ausente com pct=100"

# 9. Validar invocação sem flags (retrocompat absoluta com VISUAL-LAYOUT-06)
NYX_AESTHETIC=cyberpunk ./venv/bin/python scripts/visual/render_aesthetic_showcase.py
# saída esperada: quadro pintado em stdout, exit 0
```

---

## Invariantes a preservar

Do BRIEF e do código existente:

- **Check #1 invariantes**: zero emoji em `.py`. As strings de erro novas em `_capture_helpers.py` usam ASCII puro.
- **Check #2 invariantes**: zero menção a Claude/Anthropic/GPT em código. Helpers chamam binários neutros (xdotool, import, chrome).
- **Check #4 invariantes**: acentuação PT-BR correta. Validar `VISUAL_CAPTURE.md` com `~/.config/zsh/scripts/validar-acentuacao.py`.
- **Check #13 invariantes**: smoke boot obrigatório (`./run.sh --smoke` → `boot ok`).
- **Pipeline visual VISUAL-LAYOUT-06**: invocações antigas (`NYX_AESTHETIC=cyberpunk python3 scripts/visual/render_aesthetic_showcase.py cyberpunk`) precisam continuar funcionando — argparse aceita posicional opcional.
- **GUIDE.md §1 (Pense antes de codar)**: sem speculação além do escopo declarado. Helpers são mínimos, sem abstração para 2º caso.
- **GUIDE.md §3 (Mudanças cirúrgicas)**: não tocar em `render()` nem em `_hex_to_ansi_*` do script — só `main()`.
- **Memória `feedback_integracao_obrigatoria.md`**: helpers são lib comum em `scripts/visual/`, não solto.
- **Memória `feedback_nenhum_debito.md`**: sprint resolve débito declarado em VALIDATE-FINAL-01-PARTE-2 (linha 79); fecha esse item explicitamente.

---

## Critério binário de aceite (IA executora)

- [ ] `--midframe-pct 50` gera 2 PNGs em `<out>_midframe.png` + `<out>_final.png`
- [ ] SHA256 dos 2 PNGs é DIFERENTE (sort -u | wc -l == 2)
- [ ] `--midframe-pct 0` gera apenas `<out>_final.png` (sem midframe)
- [ ] `--midframe-pct 100` gera apenas `<out>_final.png` (sem midframe)
- [ ] Invocação sem flags (`python3 ... cyberpunk`) continua funcionando (retrocompat VISUAL-LAYOUT-06)
- [ ] `--mode web --url ...` invoca `google-chrome --headless` e gera PNG da URL
- [ ] `./run.sh --smoke` retorna `boot ok` e exit 0
- [ ] `bash scripts/sprint_invariants.sh --ci` retorna PASS 14/14
- [ ] `ruff check scripts/visual/` sem violações
- [ ] `VISUAL_CAPTURE.md` cita pipeline 3-tentativas da skill `validacao-visual` (scrot/import → claude-in-chrome MCP → playwright MCP)
- [ ] Acentuação PT-BR correta em `VISUAL_CAPTURE.md` (validar com `~/.config/zsh/scripts/validar-acentuacao.py` se script existir)
- [ ] Nenhuma violação de `forbidden[]` (sem emoji, sem menção a IA, sem dependência nova, sem sleep >2s, sem remover captura final)
- [ ] `SPRINT_ORDER_MASTER.md` atualizado marcando VALIDATE-VISUAL-MIDFRAME-01 como CONCLUIDA
- [ ] Sprint movida de `producao/` para `concluidos/`
- [ ] Commit atômico: `feat(VALIDATE-VISUAL-MIDFRAME-01): captura midframe+final em pipeline visual`

---

## Guardrails anti-engodo (obrigatórios)

A IA executora **NÃO pode marcar sprint como concluída** se:

- SHA256 dos PNGs midframe e final coincidirem (significa que captura midframe falhou silenciosamente — ou ambas capturam o mesmo estado).
- Algum critério acima estiver incompleto.
- Tentou burlar teste removendo asserções de hash distinto.
- Adicionou `time.sleep(N)` com N > 2 para forçar diff entre midframe e final.
- Falhou silenciosamente (ex.: `try/except: pass` em `capture_terminal`) e assumiu sucesso.
- Ignorou item de `forbidden[]` "porque seria mais fácil".

Se qualquer item falhar, reportar:
```
[SPRINT VALIDATE-VISUAL-MIDFRAME-01] BLOQUEADA: <motivo objetivo em 1 linha>
```

---

## Proof-of-work obrigatório (4 passos)

```bash
# PASSO 1 — snapshot ANTES
bash scripts/sprint_invariants.sh > /tmp/inv_before.txt 2>&1
FAIL_BEFORE=$(grep -c "^\[FAIL\]" /tmp/inv_before.txt)
echo "FAIL inicial: $FAIL_BEFORE"

# PASSO 2 — implementação (este arquivo é a única fonte de verdade)

# PASSO 3 — snapshot DEPOIS
bash scripts/sprint_invariants.sh > /tmp/inv_after.txt 2>&1
FAIL_AFTER=$(grep -c "^\[FAIL\]" /tmp/inv_after.txt)
echo "FAIL final: $FAIL_AFTER"

# PASSO 4 — regras binárias
#   (a) $FAIL_AFTER <= $FAIL_BEFORE
#   (b) diff /tmp/inv_before.txt /tmp/inv_after.txt — colar no relatório

# PASSO 5 — proof específico de midframe (criterio binário central)
NYX_AESTHETIC=arcano ./venv/bin/python scripts/visual/render_aesthetic_showcase.py \
    --midframe-pct 50 --out /tmp/proof_midframe
sha256sum /tmp/proof_midframe_midframe.png /tmp/proof_midframe_final.png \
    | awk '{print $1}' | sort -u | wc -l
# saída esperada: 2
```

**Formato obrigatório do relatório de conclusão:**

```
### Proof-of-work

$ cat /tmp/inv_before.txt | tail -10
(saída bruta)

$ cat /tmp/inv_after.txt | tail -10
(saída bruta)

$ diff /tmp/inv_before.txt /tmp/inv_after.txt
(diff)

FAIL inicial: N
FAIL final:   M  (M <= N)

### Proof específico midframe
$ NYX_AESTHETIC=arcano ./venv/bin/python scripts/visual/render_aesthetic_showcase.py --midframe-pct 50 --out /tmp/proof_midframe
(saída bruta)

$ ls -la /tmp/proof_midframe_midframe.png /tmp/proof_midframe_final.png
(saída bruta — ambos devem existir)

$ sha256sum /tmp/proof_midframe_midframe.png /tmp/proof_midframe_final.png
<hash1>  /tmp/proof_midframe_midframe.png
<hash2>  /tmp/proof_midframe_final.png
(hash1 != hash2)

### Git
$ git show --stat HEAD
<resultado>
```

---

## Validação humana (checklist do usuário)

```bash
cd /home/andrefarias/Desenvolvimento/Nyx-Code

# 1. Ver commit
git log --oneline -1
git show --stat HEAD

# 2. Rodar comando da sprint
NYX_AESTHETIC=arcano ./venv/bin/python scripts/visual/render_aesthetic_showcase.py \
    --midframe-pct 50 --out /tmp/visual_check

# 3. Conferir 2 PNGs distintos
sha256sum /tmp/visual_check_midframe.png /tmp/visual_check_final.png

# 4. Validar arquivos movidos
ls dev-journey/06-sprints/concluidos/SPRINT_VALIDATE_VISUAL_MIDFRAME_01.md   # deve existir
ls dev-journey/06-sprints/producao/SPRINT_VALIDATE_VISUAL_MIDFRAME_01.md     # NÃO deve existir
```

---

## Riscos

| Risco | Mitigação |
|-------|-----------|
| `xdotool search --name kitty` retorna múltiplas janelas (várias instâncias kitty abertas) | `capture_terminal` usa `wid[0]` -- primeira janela. Documentado em VISUAL_CAPTURE.md. Não bloqueia teste padrão (1 kitty geralmente). |
| `google-chrome --headless` falha em sessão sem `DISPLAY` | Helper retorna exit code != 0 e loga erro literal em stderr; pipeline visual da skill `validacao-visual` cai para tentativa 3 (playwright MCP) manualmente. |
| Showcase atual é estático (`render()` imprime quadro pronto), midframe pode coincidir com final | Captura usa `delay_sec = anim_duration * pct/100` mas estado do terminal é determinado pelo print já feito. Para showcase puro, diferença vem de timing do refresh do compositor (X11 typically 60Hz) -- midframe captura no meio do flush. Se isso não bastar para gerar SHA distintos, próximo passo é adicionar `--inject-anim-sec` que renderiza animação real (spinner) antes do quadro final. Risco aceito para v1 da sprint; fallback documentado. |
| `--virtual-time-budget` do Chrome headless varia entre versões | Helper hardcoda binário `google-chrome`, não `chromium`. Versão validada via `which google-chrome` na data da sprint. |
| Sleep agendado degrada gauntlet visual | Default `anim_duration_sec=1.0`, pct=50 → 0.5s adicional. Bem abaixo do limite 2s. Total da execução: ~1.5s. |

---

## Referências

- BRIEF: `/home/andrefarias/Desenvolvimento/Nyx-Code/VALIDATOR_BRIEF.md` seção `[CORE] Capacidades visuais aplicáveis`
- Skill `validacao-visual`: `/home/andrefarias/.claude/skills/validacao-visual/SKILL.md` (pipeline 3-tentativas)
- Sprint precedente (anti-débito declarado): `/home/andrefarias/Desenvolvimento/Nyx-Code/dev-journey/06-sprints/concluidos/SPRINT_VALIDATE_FINAL_01_PARTE_2.md` linha 79
- Sprint precedente (último uso do pipeline visual): `/home/andrefarias/Desenvolvimento/Nyx-Code/dev-journey/06-sprints/concluidos/SPRINT_VISUAL_LAYOUT_06.md`
- Commit que declara o débito: `8101062`
- Template canônico: `/home/andrefarias/Desenvolvimento/Nyx-Code/dev-journey/08-templates/SPRINT_TEMPLATE_V2.md`

---

*"O frame final mente sobre o caminho percorrido; o midframe é a única prova de que houve animação." -- VALIDATE-VISUAL-MIDFRAME-01*
