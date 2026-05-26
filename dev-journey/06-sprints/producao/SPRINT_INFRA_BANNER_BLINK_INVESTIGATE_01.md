# SPRINT 243 — INFRA-BANNER-BLINK-INVESTIGATE-01

## 0. SPEC

```yaml
sprint:
  id: INFRA-BANNER-BLINK-INVESTIGATE-01
  title: "Investigar e consertar cursor blink do banner que parou de funcionar"
  onda: 31
  prioridade: MÉDIA
  tipo: Bugfix
  dependencias: [TUI-BANNER-BLINK-DEFAULT-01, INFRA-BANNER-BLINK-NO-CLEAR-01]
  desbloqueia: []

  touches:
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/cli.py
      reason: "_banner_blink_loop linhas 501-563; invalidate sozinho nao re-renderiza"
  creates: []
  removes: []

  forbidden:
    - "Reintroduzir renderer.clear() (sprint 238 provou que causa flicker total)"
    - "Reintroduzir app.invalidate() global em loop curto (sprint 187 ja revertida)"
    - "Tocar em banner.py (escopo cli.py apenas)"
    - "Mexer em sprints commitadas (185+ todas preservar)"

  tests:
    - cmd: "./run.sh --smoke"
      timeout: 10
      deve_passar: true
    - cmd: "bash scripts/sprint_invariants.sh"
      timeout: 30
      deve_passar: true

  acceptance_criteria:
    - "Captura tmux 6 frames @ 0.6s mostra >= 3 SHAs distintos no banner area"
    - "Cursor `|` alterna visualmente com vazio a cada ~0.5s"
    - "SEM flicker total da tela (frames sem outliers de tamanho ~600 bytes)"
    - "Smoke + invariantes PASS"
```

---

# Sprint 243 — INFRA-BANNER-BLINK-INVESTIGATE-01

**Status:** PENDENTE
**Data criação:** 2026-05-25
**Modelo obrigatório:** claude-opus-4-7 (sem subagentes)

---

## Contexto

Usuário confirmou após sprint 238 (remoção do `renderer.clear()`): "o piscar nao ta funcionando mesmo, ta estranho de novo. voltou a bugar". Captura visual confirma: cursor `|` aparece ESTATICO no banner.

Sprint 225 criou `_banner_blink_loop` (cli.py:501-563) que:
1. A cada 0.5s alterna `cursor` entre `chr(0x7C)` e `""`
2. Reconstrói banner via `_bb(...)`
3. Substitui prefixo do `repl_output_buffer.text`
4. Chama `_get_app().invalidate()`

Sprint 238 removeu `renderer.clear()` por causar flicker total. Mas `invalidate()` sozinho NAO esta re-renderizando o banner — delta-rendering do prompt_toolkit otimiza away a mudanca.

## Fase 1 — Investigação obrigatória

1. Adicionar `logger.info` em pontos críticos do loop:
   - Antes do sleep: visible state
   - Após buffer.document = ...: confirmar que set ocorreu
   - Após invalidate(): confirmar chamada

2. Rodar `./run.sh` via tmux, capturar 6 frames @ 0.6s, computar SHAs:
   - Se SHA constante: invalidate não tem efeito → fix tem que ir além
   - Se SHA varia mas visualmente igual: delta-rendering perde mudança

3. Isolar comportamento de FormattedTextControl com lambda callable. Possíveis fixes:
   - Usar `text_callable=` em vez de `text=` no FormattedTextControl
   - Forçar `_app.renderer.reset()` (diferente de clear)
   - Trocar mecanismo de blink para ANSI nativo `\x1b[5m...\x1b[25m`

## Fase 2 — Fix cirúrgico

Aplicar O QUE FUNCIONAR empíricamente. Não chutar sem ver SHA mudar.

## Fase 3 — Validação

```bash
# Pre-cleanup
pkill -9 -f "run.sh|ollama serve|nyx/proxy|kitty.*ntest"
rm -f /tmp/nyx.pid

# Rodar via kitty + capturar 6 frames
setsid kitty --title="ntest" --hold sh -c './run.sh' </dev/null >/dev/null 2>&1 &
sleep 15  # aguardar CLI abrir
WID=$(xdotool search --name "^ntest$" | head -1)
for i in 1 2 3 4 5 6; do
    import -window "$WID" /tmp/blink_validate_$i.png
    sleep 0.6
done
sha256sum /tmp/blink_validate_*.png | awk '{print $1}' | sort -u | wc -l
# Esperado: >= 3 (banner area animando)

# Smoke + invariantes
./run.sh --smoke
bash scripts/sprint_invariants.sh

# Cleanup
pkill -9 -f "run.sh|ollama serve|nyx/proxy|kitty.*ntest"
```

## Riscos

| Risco | Mitigação |
|---|---|
| `invalidate()` insuficiente, precisar `renderer.reset()` ou outro | Testar empíricamente antes de assumir |
| ANSI blink `\x1b[5m` desabilitado por padrão em alguns terminais | Verificar suporte no kitty/gnome-terminal antes de adotar |
| Mudança quebra sprint 188 Ctrl+Q ou 193 NO_CLEAR | Validar Ctrl+Q + ausência de flicker total |

---

*"Sem prova empirica, fix vira chute documentado." -- principio anti-tentativa-e-erro*
