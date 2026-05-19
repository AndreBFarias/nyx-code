# SPRINT TUI-REDESIGN-28-07 — Cursor blink async no banner

## 0. SPEC

```yaml
sprint:
  id: TUI-REDESIGN-28-07
  title: "Cursor '▌' do banner '$nyx.code' pisca 4× em loop async (~1.5s) antes de ceder ao prompt"
  onda: 28
  bloco: 28.1 TUI paridade Claude Code
  prioridade: MÉDIA
  tipo: Visual
  dependencias: [TUI-REDESIGN-28-06]
  desbloqueia: []
  origem: "Mockup HTML mostra cursor piscante após '$ nyx.code'. Feedback do usuário 2026-05-18: 'Banner Piscando com o $nyx.code com o ponto final e a barrinha piscando com as cores roxas'."

  touches:
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/agent/banner_blink.py
      reason: "Novo módulo: função async blink_cursor_at(row, col, frames=4, period_s=0.375) com cursor positioning ANSI"
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/cli.py
      reason: "Após print(banner_str), antes do primeiro prompt_async, fazer await blink_cursor_at(...); pular se !sys.stdout.isatty() OR NYX_NO_ANIMATION=1"

  forbidden:
    - "Bloquear input do usuário se ele apertar tecla durante a animação"
    - "Animar em ambientes não-TTY (gauntlet, CI, pipe) — skip obrigatório"
    - "Total > 2 segundos (evitar latência percebida)"
    - "Esquecer de respeitar NYX_NO_ANIMATION=1"

  tests:
    - cmd: "./run.sh --smoke"
      timeout: 60
      deve_passar: "boot ok (smoke é headless, blink pula)"
    - cmd: "./venv/bin/python -c 'from nyx.agent.banner_blink import blink_cursor_at; import inspect; print(inspect.iscoroutinefunction(blink_cursor_at))'"
      timeout: 5
      deve_passar: "True"
    - cmd: "NYX_NO_ANIMATION=1 timeout 5 ./run.sh --smoke"
      timeout: 10
      deve_passar: "boot ok"

  acceptance_criteria:
    - "Sessão real (TTY): banner aparece, cursor '▌' pisca 4× (~1.5s total) em roxo, depois libera prompt"
    - "./run.sh --smoke (headless) NÃO faz blink (skip por isatty)"
    - "NYX_NO_ANIMATION=1 ./run.sh pula blink"
    - "Ctrl+C durante blink interrompe limpo (não corrompe terminal)"
    - "Smoke + invariantes ok"

  proof_of_work:
    - "Capturar boot via 'ffmpeg -f x11grab' ou 'asciinema rec' por 3s e conferir frames com/sem cursor"
    - "./venv/bin/python -c 'import asyncio; from nyx.agent.banner_blink import blink_cursor_at; asyncio.run(blink_cursor_at(1, 12))' executa em <2s sem erro"
```

---

# Sprint TUI-REDESIGN-28-07

**Status:** CONCLUIDA
**Data criação:** 2026-05-18
**Data conclusão:** 2026-05-18
**Modelo obrigatório:** claude-opus-4-7

## Proof-of-work (2026-05-18)

- Arquivos:
  - Novo: `nyx/agent/banner_blink.py` (~120L) — função async
    `blink_cursor_at(rows_up=7, cols_right=13, frames=4, period_s=0.18)`,
    skip silencioso em não-TTY ou `NYX_NO_ANIMATION=1`, restauração de
    cursor em `CancelledError` (Ctrl+C-safe).
  - Modificado: `nyx/cli.py` — chamada `await blink_cursor_at()` após
    `print(_build_banner(...))` na linha 522, com fallback best-effort
    `logger.debug` em caso de exceção.
- Sanity coroutine: `iscoroutinefunction(blink_cursor_at)` → `True`.
- Sanity skip headless: `asyncio.run(blink_cursor_at())` em pipe → 63 ms,
  exit 0, zero output (skip por `sys.stdout.isatty() is False`).
- Smoke real: `./run.sh --smoke` → `boot ok` em ~140 ms.
- Smoke com opt-out: `NYX_NO_ANIMATION=1 timeout 10 ./run.sh --smoke`
  → `boot ok` em ~165 ms.
- TTY simulado via `script`: 4 ciclos on/off (`CSI 7A CSI 13G ▌` /
  espaço) com sequência ANSI literal correta, duração medida
  **1.526 s** (target ~1.5 s, dentro de < 2 s).
- Invariantes: 14/14 PASS, 0 FAIL.
- Acentuação periférica: ambos os arquivos OK
  (`validar-acentuacao.py --paths` exit 0).

## Rollback

`git reset --hard HEAD~1`
