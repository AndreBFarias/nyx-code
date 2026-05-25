# SPRINT 225 — TUI-BANNER-BLINK-DEFAULT-01

## 0. SPEC (machine-readable)

```yaml
sprint:
  id: TUI-BANNER-BLINK-DEFAULT-01
  title: "Cursor do banner pisca continuamente no caminho default Application"
  onda: 31
  prioridade: MÉDIA
  tipo: Feature
  dependencias: []
  desbloqueia: []

  touches:
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/agent/banner.py
      reason: "build_banner aceita cursor='' (vazio) preservando alinhamento do grid"
      linhas_alvo: "51-235"
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/cli.py
      reason: "Application path inicia timer asyncio que alterna cursor"
      linhas_alvo: "440-490"
  creates: []
  removes: []

  forbidden:
    - "app.invalidate() global (causa raiz do flicker da sprint 187, revertida pela 193)"
    - "Manipulação direta do output_buffer durante stream de tokens"
    - "Adicionar emoji"
    - "Mencao a IA proprietaria em codigo/commit"   # noqa-anonimato

  tests:
    - cmd: "./run.sh --smoke"
      timeout: 10
      deve_passar: true
    - cmd: "./run.sh --gauntlet --only rapido"
      timeout: 120
      deve_passar: true

  acceptance_criteria:
    - "Cursor pisca em loop sem flicker observável durante stream"
    - "Cursor pisca durante input (sem race com keystroke)"
    - "Cursor para quando REPL sai (clean shutdown)"
    - "Cadência: chr(0x7C) ('|')  '' (vazio) a cada 0.5s"
    - "5 screenshots @ 200ms via scrot loop mostram 2+ SHAs distintos"
    - "Smoke boot ok"
    - "Invariantes 14/14 PASS"
    - "Acentuação rc=0"
```

---

# Sprint 225 — TUI-BANNER-BLINK-DEFAULT-01

**Status:** PENDENTE
**Data criação:** 2026-05-25
**Modelo obrigatório:** claude-opus-4-7 (sem subagentes)

---

## Contexto do projeto (snapshot)

> **ADRs relevantes:**
> - ADR-024 Render Layer. ADR-027 Identidade Nyx (presença visual).
>
> **Estado do sistema:**
> - `nyx/agent/banner.py:51 build_banner(..., cursor=chr(0x258C))` aceita cursor parametrizado.
> - Caminho default Application: `cli.py:473` chama `build_banner` UMA vez e fica estático.
> - Caminho legacy PromptSession: `cli.py:343-348` chama `blink_cursor_at()` async ONE-SHOT (~1.4s, depois para).
> - Sprint 187 BLINK_SOFT_03 tentou blink contínuo via `app.invalidate()` → causou flicker → revertida pela 193.
> - Sprint 205 TEXTUAL-BANNER-WIDGET-01 fez blink com `set_interval + self.refresh()` LOCAL — sem race global (só no NyxTUI Textual opt-in).

---

## Problema

Cursor `▌` do banner não pisca no caminho default. Aparece estático no boot + qualquer scroll/redraw o congela.

Feedback do usuário (2026-05-25): **"o piscar seria em um momento tem `|` no outro nada. Aí dá a ilusão."**

### Sintoma observável

Imagem 2 do feedback mostra cursor `|` estático após `$ nyx.code` no banner. Sem animação.

---

## Solução proposta

Adicionar timer asyncio no Application path (cli.py:440-490) que alterna cursor entre `chr(0x7C)` (`|`) e `""` (vazio) a cada 0.5s. Repaint controlado: atualizar **apenas** a região do banner via output_buffer dedicado (sem `app.invalidate()` global).

**Lição da 187 (revertida pela 193):** `app.invalidate()` global cria race com streaming. Solução: extrair banner para `output_buffer_banner` (Buffer/FormattedTextControl próprio) cuja atualização é local.

**Cadência:** `|` (0.5s) → vazio (0.5s) → `|` (0.5s) → ... Sensação de blink real (cursor de terminal).

---

## Arquivos alvo

### `/home/andrefarias/Desenvolvimento/Nyx-Code/nyx/agent/banner.py`

**Antes (linhas 51-67 aprox):**
```python
def build_banner(
    model: str,
    tools_count: int,
    project_name: str,
    settings: Any = None,
    cursor: str = chr(0x258C),
) -> str:
    ...
```

**Depois:**
```python
def build_banner(
    model: str,
    tools_count: int,
    project_name: str,
    settings: Any = None,
    cursor: str = chr(0x258C),
) -> str:
    """...
    cursor='' renderiza espaço alinhado (preserva grid 2-col).
    """
    if cursor == "":
        cursor = " "   # mantém largura visível para evitar quebra de layout
    ...
```

E ajuste em `_build_wide` (linha 234) e `_build_compact` (linha 163): o `cursor` recebido **deve ter sempre 1 caractere visível** — quando passamos `""`, substituímos por espaço.

### `/home/andrefarias/Desenvolvimento/Nyx-Code/nyx/cli.py`

**Localização aproximada:** após `build_banner` no Application path (linha 473).

Adicionar:
```python
# TUI-BANNER-BLINK-DEFAULT-01: timer assíncrono que repinta apenas a região
# do banner. NÃO usa app.invalidate() global (lição da sprint 187 revertida
# pela 193). Atualiza um Buffer dedicado.

_banner_cursor_visible = True

async def _banner_blink_loop(banner_buffer):
    global _banner_cursor_visible
    while True:
        await asyncio.sleep(0.5)
        _banner_cursor_visible = not _banner_cursor_visible
        cursor = chr(0x7C) if _banner_cursor_visible else ""
        new_banner = _build_banner(
            model, agent.tools_count, PROJECT_ROOT.name,
            settings=settings, cursor=cursor,
        )
        banner_buffer.text = new_banner   # atualização LOCAL

# Dispatch (fire-and-forget):
_banner_blink_task = asyncio.create_task(_banner_blink_loop(banner_buffer))
app_state["_banner_blink_task"] = _banner_blink_task
```

Cancel no shutdown via `cli_boot.py:shutdown_repl` (paridade com sprint 187 cleanup).

---

## Diff esperado (resumo)

```
~ 2 arquivos modificados
+ ~30 linhas líquidas
```

---

## Comandos de verificação

```bash
# Smoke
./run.sh --smoke

# 5 screenshots em loop 200ms (alternância)
./run.sh &
sleep 3
for i in 1 2 3 4 5; do
    sleep 0.2
    import -window $(xdotool search --name './run.sh' | head -1) /tmp/blink_$i.png
done
sha256sum /tmp/blink_*.png | sort -u | wc -l
# Esperado: >= 2 (cursor visível vs invisível)

# Invariantes + gauntlet
bash scripts/sprint_invariants.sh
./run.sh --gauntlet --only rapido

# Acentuação
python3 ~/.config/zsh/scripts/validar-acentuacao.py --paths nyx/agent/banner.py nyx/cli.py
```

---

## Critério binário de aceite

- [ ] Cursor pisca durante operação normal (não só boot).
- [ ] Sem flicker em streaming de tokens (race com output).
- [ ] Shutdown limpo cancela timer (sem zumbi).
- [ ] 5 screenshots: 2+ SHAs distintos.
- [ ] Sprint 187 BLINK_SOFT NÃO foi re-introduzida (sem `app.invalidate` global).
- [ ] Sprint 193 BLINK_SOFT_REVERT lições preservadas (banner_buffer dedicado).
- [ ] Smoke + invariantes + gauntlet rapido OK.
- [ ] Spec movida producao/ → concluidos/.

---

## Proof-of-work

```bash
bash scripts/sprint_invariants.sh > /tmp/inv_before.txt 2>&1
# Edit
bash scripts/sprint_invariants.sh > /tmp/inv_after.txt 2>&1
diff /tmp/inv_before.txt /tmp/inv_after.txt
# Screenshots de blink (script acima)
sha256sum /tmp/blink_*.png
```

---

## Riscos

| Risco | Mitigação |
|---|---|
| Race com streaming output (sprint 187) | Banner em Buffer próprio, sem `app.invalidate` global |
| Cursor `|vazio` parece "tremido" | Trade-off aceito; se feedback negativo, sprint follow-up com `▌▏` |
| Timer não cancela em shutdown rápido | Cancel no shutdown_repl com timeout 0.1s |
| Layout do grid 2-col quebra com cursor vazio | cursor="" substituído por " " preservando largura |

---

*"Blink é vida no terminal. Estático é estagnação." — princípio gamedesigner*
