## 0. SPEC (machine-readable)

```yaml
sprint:
  id: TUI-BANNER-DEDUP-02
  title: "Eliminar banner fantasma pré-Application (print + blink crus antes da alternate-screen)"
  onda: 29
  prioridade: ALTA
  tipo: Bugfix
  dependencias: []
  desbloqueia: [TUI-BANNER-BLINK-SOFT-03]

  touches:
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/cli.py
      reason: "Condicionar print(_build_banner) e blink_cursor_at() ao caminho legacy PromptSession"
      linhas_alvo: "300-450"

  forbidden:
    - "Remover o banner do caminho legacy PromptSession (NYX_LEGACY_REPL=1 ainda usa print+blink)"
    - "Mudar texto, paleta ou layout do banner (apenas reposicionar a chamada)"
    - "Adicionar emoji"
    - "Menção a IA externa em código"

  tests:
    - cmd: "./run.sh --smoke"
      timeout: 60
      deve_passar: true

  acceptance_criteria:
    - "Boot da TUI Application (default) NÃO mostra banner antes do output_buffer subir (zero banner fantasma)"
    - "Boot com NYX_LEGACY_REPL=1 mantém banner cru + blink (comportamento preservado)"
    - "Boot Application: banner aparece UMA vez, dentro do output_buffer (via append_to_buffer)"
    - "Smoke + invariantes 14/14 PASS"
```

---

# Sprint TUI-BANNER-DEDUP-02 — Eliminar banner fantasma

**Status:** PENDENTE
**Data criação:** 2026-05-21
**Modelo obrigatório:** claude-opus-4-7 (sem subagentes)

---

## Contexto do projeto (snapshot)

> - Python 3.10+, modelo qwen2.5-coder:3b porta 11435, proxy 11436.
> - 35 tools, 67 commands. `nyx/cli.py` ~790 linhas; `nyx/agent/repl_app.py` ~510 linhas.
> - Onda 28: TUI passou a usar `prompt_toolkit.Application` full-screen quando TTY real + `NYX_LEGACY_REPL != "1"` (sprint TUI-REDESIGN-28-08c-PARTE-2/3).
> - Sprint anterior: TUI-REDESIGN-28-08c-PARTE-3 CONCLUIDA — banner re-renderiza via FormattedTextControl ANSI no output_buffer.

---

## Problema

Ao iniciar `./run.sh` no caminho default (Application), o banner aparece **duas vezes**:

1. **Banner fantasma:** `print(_build_banner(...))` em `nyx/cli.py:311` imprime banner cru no stdout. Em seguida `await blink_cursor_at()` (linha 329) anima um cursor `▌` por ~1.4s em **posição errada** (`rows_up=7` hardcoded, mas o banner tem 9 linhas) — cursor pisca em local aleatório.
2. **Banner correto:** quando `use_application=True` (linha 407), a Application entra em alternate-screen e o banner do stdout some; depois `append_to_buffer(repl_output_buffer, _banner_str + "\n")` (linhas 437-439) reinjeta o banner DENTRO da Application.

Sintoma para o usuário: "página sobe, fica com cursor aleatório piscando, depois some, e aparece o banner correto" (relato 2026-05-21).

O banner cru + o blink crus são úteis no fallback legacy (PromptSession sem alternate-screen), mas redundantes/poluentes quando Application está ativa.

---

## Solução proposta

Reposicionar `print(_build_banner)` e `await blink_cursor_at()` para **dentro do branch que NÃO usa Application** (legacy). No caminho Application, o banner aparece apenas via `append_to_buffer`.

---

## Arquivos alvo

### `/home/andrefarias/Desenvolvimento/Nyx-Code/nyx/cli.py` (linhas ~300-450)

**Antes (estrutura atual):**
```python
# linha 311
print(_build_banner(model, agent.tools_count, PROJECT_ROOT.name, settings=settings))
# linhas 313-322: roots extras
# linhas 324-331: blink_cursor_at()
try:
    from nyx.agent.banner_blink import blink_cursor_at
    await blink_cursor_at()
except Exception as _blink_exc:
    logger.debug("blink_cursor_at falhou: %s", _blink_exc)

# ... linhas 402-454: detecção use_application + build_app + append_to_buffer
```

**Depois (banner cru + blink só no caminho legacy):**
```python
# Detecta caminho ANTES do banner cru
_legacy_env = os.environ.get("NYX_LEGACY_REPL", "").strip() == "1"
use_application = (
    sys.stdin.isatty() and not _legacy_env and prompt_session is not None
)

if not use_application:
    # Caminho legacy PromptSession: banner cru + blink async
    print(_build_banner(model, agent.tools_count, PROJECT_ROOT.name, settings=settings))
    # linhas 313-322: roots extras (mantém)
    try:
        from nyx.agent.banner_blink import blink_cursor_at
        await blink_cursor_at()
    except Exception as _blink_exc:
        logger.debug("blink_cursor_at falhou: %s", _blink_exc)
# else: caminho Application — banner aparece via append_to_buffer abaixo (mesma linha 437-439)
```

**Mudanças:**
- Mover detecção `use_application` para antes do banner (atualmente está na linha 406, depois do banner).
- Envolver `print(_build_banner)` + `blink_cursor_at()` em `if not use_application:`.
- Atualizar comentários `TUI-REDESIGN-28-07/28-08c-PARTE-3` mencionando a decisão.

---

## Diff esperado

```
~ 1 arquivo modificado
+ ~5 linhas (if not use_application: wrap)
- 0 linhas removidas (apenas reordenação)
```

---

## Comandos de verificação

```bash
# 1. Smoke
./run.sh --smoke

# 2. Boot Application (default)
./run.sh
# (esperado: tela limpa, banner aparece UMA vez dentro do alternate-screen; sem cursor pisca-pisca em local errado antes)

# 3. Boot legacy (preservar comportamento antigo)
NYX_LEGACY_REPL=1 ./run.sh
# (esperado: banner cru + blink ~1.4s + prompt nyx>)

# 4. Captura visual antes/depois
scrot --delay 1 /tmp/banner_app.png   # default
NYX_LEGACY_REPL=1 scrot --delay 3 /tmp/banner_legacy.png

# 5. Invariantes + acentuação
bash scripts/sprint_invariants.sh
python3 ~/.config/zsh/scripts/validar-acentuacao.py --paths nyx/cli.py
```

---

## Critério binário de aceite

- [ ] Boot Application: zero banner antes do alternate-screen (captura visual antes/depois)
- [ ] Boot Application: banner aparece UMA vez (via append_to_buffer)
- [ ] Boot legacy (`NYX_LEGACY_REPL=1`): banner cru + blink ~1.4s + prompt — mesmo comportamento de antes
- [ ] `./run.sh --smoke` boot ok exit 0
- [ ] `bash scripts/sprint_invariants.sh` PASS 14/14
- [ ] Acentuação PT-BR rc=0

---

## Riscos

| Risco | Mitigação |
|-------|-----------|
| Mover detecção `use_application` antes do banner quebra ordem de avaliação | A detecção depende apenas de `sys.stdin.isatty()`, `os.environ`, e `prompt_session != None` — todos disponíveis antes do banner |
| Caminho legacy perder o banner | Wrap explícito `if not use_application:` envolve `print` + `blink_cursor_at` |
| `prompt_session` ser None aqui (não construído ainda) | Confirmar via Read antes — se for, ajustar ordem ou usar flag intermediária |

---

*"O usuário não deve ver os bastidores do palco." -- princípio TUI.*
