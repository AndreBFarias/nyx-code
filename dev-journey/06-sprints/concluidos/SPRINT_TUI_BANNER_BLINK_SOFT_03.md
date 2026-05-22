## 0. SPEC (machine-readable)

```yaml
sprint:
  id: TUI-BANNER-BLINK-SOFT-03
  title: "Cursor do banner $ nyx.code pisca suave alternando ▌▏ (sempre visível)"
  onda: 29
  prioridade: MÉDIA
  tipo: Bugfix
  dependencias: [TUI-BANNER-DEDUP-02]
  desbloqueia: []

  touches:
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/agent/banner.py
      reason: "Produzir 2 versões do banner (frame_a com ▌, frame_b com ▏) para alternância"
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/agent/repl_app.py
      reason: "Registrar timer (period 0.5s) que alterna a primeira linha do output_buffer entre frame_a e frame_b"
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/agent/banner_blink.py
      reason: "Alterar frame OFF para escrever ▏ em roxo dim em vez de espaço (caminho legacy)"
      linhas_alvo: "86-92"

  forbidden:
    - "Cursor desaparecer completamente em qualquer frame (banido espaço/vazio)"
    - "Mudar paleta de cor do cursor (segue roxo da paleta atual)"
    - "Adicionar emoji"
    - "Quebrar invariante #14 (Geometric Shapes) — ambos ▌ U+258C e ▏ U+258F são protegidos via chr() se necessário"
    - "Menção a IA externa em código"

  tests:
    - cmd: "./run.sh --smoke"
      timeout: 60
      deve_passar: true

  acceptance_criteria:
    - "GIF de 3s capturado em runtime mostra cursor visível em 100% dos frames (alterna ▌▏)"
    - "Cursor pulsa intensidade com período ~1Hz (0.5s por glifo)"
    - "Skip silencioso em NYX_NO_ANIMATION=1 e em não-TTY (CI/Gauntlet)"
    - "Caminho legacy banner_blink.py: frame OFF escreve ▏ (não espaço)"
    - "Smoke + invariantes 14/14 PASS"
```

---

# Sprint TUI-BANNER-BLINK-SOFT-03 — Blink suave alternando ▌▏

**Status:** PENDENTE
**Data criação:** 2026-05-21
**Modelo obrigatório:** claude-opus-4-7 (sem subagentes)

---

## Contexto do projeto (snapshot)

> - Banner final renderizado via `nyx/agent/banner.py:build_banner()` (caixa ASCII 2-col com `$ nyx.code▌`).
> - No caminho Application (default), banner vive no `output_buffer` da `prompt_toolkit.Application` — atualizado via `append_to_buffer` (sprint TUI-REDESIGN-28-08c-PARTE-3).
> - No caminho legacy PromptSession (`NYX_LEGACY_REPL=1`), banner é impresso via `print()` + animado por `blink_cursor_at()` async em `banner_blink.py`.
> - Sprint anterior: TUI-BANNER-DEDUP-02 — banner cru + blink crus agora só rodam no legacy.

---

## Problema

No banner permanente `$ nyx.code▌`, o cursor `▌` deveria piscar suave (sempre visível, pulsando intensidade). Comportamento atual: **alterna entre `▌` e nada** — cursor desaparece momentaneamente, parece bug visual.

Causa identificada em `nyx/agent/banner_blink.py:86-92`:

```python
# OFF: mesma posição, escreve espaço (apaga visualmente).
sys.stdout.write(f"\033[{rows_up}A\033[{cols_right}G")
sys.stdout.write(" ")   # <-- ESPAÇO, cursor some por 180ms
```

Com período de 0.18s e 4 frames, cursor fica invisível ~40% do tempo, parecendo "falha" em vez de "pulsar".

Decisão de design (já fechada com usuário 2026-05-21): alternar entre 2 glifos `▌` (U+258C, full block)  `▏` (U+258F, thin block). Cursor nunca some, oscila intensidade visual.

---

## Solução proposta

### Caminho Application (default — pós-DEDUP-02)

`build_banner()` em `nyx/agent/banner.py` passa a expor 2 helpers:
- `build_banner_frame_a(...)` — versão com `▌`.
- `build_banner_frame_b(...)` — versão com `▏`.

Em `nyx/agent/repl_app.py`, registrar timer `app.create_background_task(_blink_loop)` que a cada 0.5s alterna a primeira linha do `output_buffer` entre as 2 versões.

### Caminho legacy (banner_blink.py)

Substituir o frame OFF de escrever ` ` por escrever `▏` em roxo (preferencialmente dim, mas roxo puro também aceita). Mantém compat com TTY tradicional.

---

## Arquivos alvo

### `/home/andrefarias/Desenvolvimento/Nyx-Code/nyx/agent/banner.py`

**Adicionar (após `build_banner`):**

```python
def build_banner_frame_a(model: str, tools_count: int, project_name: str, *, settings: Any = None) -> str:
    """Banner com cursor em U+258C (full block)."""
    return build_banner(model, tools_count, project_name, settings=settings, cursor=chr(0x258C))

def build_banner_frame_b(model: str, tools_count: int, project_name: str, *, settings: Any = None) -> str:
    """Banner com cursor em U+258F (left one-eighth block)."""
    return build_banner(model, tools_count, project_name, settings=settings, cursor=chr(0x258F))
```

(Se `build_banner` não aceita parâmetro `cursor`, adicionar com default `chr(0x258C)`.)

### `/home/andrefarias/Desenvolvimento/Nyx-Code/nyx/agent/repl_app.py`

**Adicionar (dentro de `build_app`, após output_buffer pronto):**

```python
async def _banner_blink_loop() -> None:
    """Alterna primeira linha do output_buffer entre frame_a e frame_b a cada 0.5s.
    Skip se NYX_NO_ANIMATION=1.
    """
    if os.environ.get("NYX_NO_ANIMATION") == "1":
        return
    frames = [True, False]
    idx = 0
    while True:
        await asyncio.sleep(0.5)
        try:
            replace_first_line(output_buffer, frame_a if frames[idx] else frame_b)
        except Exception as exc:
            logger.debug("banner blink loop falhou: %s", exc)
            return
        idx = (idx + 1) % 2

# Registrar como background task quando a Application iniciar:
app.create_background_task(_banner_blink_loop())
```

**Helper `replace_first_line(buffer, new_text)`:** trocar apenas a primeira linha do `output_buffer.text` mantendo o resto intacto.

### `/home/andrefarias/Desenvolvimento/Nyx-Code/nyx/agent/banner_blink.py` (linhas 86-92)

**Antes:**
```python
# OFF: mesma posição, escreve espaço (apaga visualmente).
sys.stdout.write(f"\033[{rows_up}A\033[{cols_right}G")
sys.stdout.write(" ")
sys.stdout.flush()
```

**Depois:**
```python
# OFF: mesma posição, escreve thin block em roxo (cursor sempre visível).
sys.stdout.write(f"\033[{rows_up}A\033[{cols_right}G")
sys.stdout.write(f"{ANSI_PURPLE_FG}{chr(0x258F)}{ANSI_RESET}")
sys.stdout.flush()
```

**Mudanças:** zero "frame escuro". Cursor pulsa entre full block (`▌`) e thin block (`▏`).

---

## Diff esperado

```
~ 3 arquivos modificados
+ ~25 linhas (frame_a/frame_b + blink loop + replace_first_line)
- ~3 linhas (espaço do frame OFF)
```

---

## Comandos de verificação

```bash
# 1. Smoke
./run.sh --smoke

# 2. Validação visual (GIF 3s do blink)
./run.sh &
sleep 3
for i in 1 2 3 4 5 6; do
  scrot /tmp/blink_$i.png
  sleep 0.5
done
# inspecionar /tmp/blink_*.png — alternam entre ▌ e ▏, cursor visível em todos

# 3. Skip em headless
NYX_NO_ANIMATION=1 ./run.sh --smoke   # boot ok sem animação

# 4. Caminho legacy: ▏ presente no banner_blink.py
grep -n "0x258F" nyx/agent/banner_blink.py

# 5. Invariantes + acentuação
bash scripts/sprint_invariants.sh
python3 ~/.config/zsh/scripts/validar-acentuacao.py --paths nyx/agent/banner.py nyx/agent/repl_app.py nyx/agent/banner_blink.py
```

---

## Critério binário de aceite

- [ ] Captura visual: cursor visível em 100% dos frames (alterna ▌▏)
- [ ] Período ~1Hz (0.5s por glifo)
- [ ] `grep "0x258F" nyx/agent/banner_blink.py` retorna ≥1 match
- [ ] `NYX_NO_ANIMATION=1 ./run.sh --smoke` boot ok sem animação
- [ ] `./run.sh --smoke` boot ok exit 0
- [ ] `bash scripts/sprint_invariants.sh` PASS 14/14
- [ ] Acentuação PT-BR rc=0

---

## Riscos

| Risco | Mitigação |
|-------|-----------|
| `output_buffer.text` mutável conflita com prompt_toolkit | Usar API correta: substring replace + `buffer.text = new_text` ou `buffer.document = Document(new_text)` |
| Background task vaza após shutdown | Cancelar task no shutdown_repl (já há padrão em `cli_boot.py:233-246`) |
| ▏ U+258F renderizar como caixinha em terminal antigo | Aceito — fonte ASCII fallback é problema do terminal, não do código |
| Race entre append_to_buffer normal e blink loop | Lock implícito do prompt_toolkit cuida; testar via `--smoke` |

---

*"Pequenos sinais de vida tornam a interface viva." -- princípio TUI.*
