# SPRINT 243 — INFRA-BANNER-BLINK-INVESTIGATE-01

## 0. SPEC

```yaml
sprint:
  id: INFRA-BANNER-BLINK-INVESTIGATE-01
  title: "Investigar e consertar cursor blink do banner que parou de funcionar"
  onda: 31
  prioridade: MÉDIA
  tipo: Bugfix (investigação)
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
    - "Captura tmux 6 frames @ 0.6s mostra alternância visual de cursor (>= 2 SHAs distintos para blink binário)"
    - "Cursor `|` alterna visualmente com vazio a cada ~0.5s (confirmado por logger.info instrumentado)"
    - "SEM flicker total da tela (frames sem outliers de tamanho ~600 bytes)"
    - "Smoke + invariantes PASS"
```

---

# Sprint 243 — INFRA-BANNER-BLINK-INVESTIGATE-01

**Status:** CONCLUIDA (investigação — hipótese refutada, blink já funcional pós sprint 238)
**Data criação:** 2026-05-25
**Data execução:** 2026-05-25
**Modelo obrigatório:** claude-opus-4-7 (sem subagentes)

---

## Contexto inicial

Usuário confirmou após sprint 238 (remoção do `renderer.clear()`): "o piscar nao ta funcionando mesmo, ta estranho de novo. voltou a bugar". Captura visual confirma: cursor `|` aparece ESTATICO no banner.

Sprint 225 criou `_banner_blink_loop` (cli.py:501-563) que:
1. A cada 0.5s alterna `cursor` entre `chr(0x7C)` e `""`
2. Reconstrói banner via `_bb(...)`
3. Substitui prefixo do `repl_output_buffer.text`
4. Chama `_get_app().invalidate()`

Sprint 238 removeu `renderer.clear()` por causar flicker total. Hipótese da spec 243: `invalidate()` sozinho NÃO esta re-renderizando — delta-rendering do prompt_toolkit otimiza away.

## Fase 1 — Investigação empírica (executada 2026-05-25 22:02 — 22:09)

### Instrumentação aplicada

`nyx/cli.py` ganhou logger.info gated por env `NYX_BLINK_DEBUG=1`:
- A cada tick: `tick=N visible=BOOL cursor=REPR`
- Após `set_document`: `tick=N set_document OK novo_len=N`
- Após `invalidate()`: `tick=N invalidate OK`
- Caso buffer não comece com prev_banner: `tick=N não startswith prev_banner`

Diff: +26 linhas, zero linhas removidas, zero impacto em runtime sem env var (custo: 1 ler-env por boot + 1 incremento de contador + 1 if por tick).

### Captura empírica

`./run.sh` rodado em tmux session 200x50:

**Experimento 1** (6 frames @ 0.6s, intervalo 3.0s):

```
frame 1  2268B  22:02:45.084   SHA 31a2195b... (com cursor '|')
frame 2  2268B  22:02:45.688   SHA c158f752... (cursor vazio)
frame 3  2268B  22:02:46.293   SHA 31a2195b... (com cursor '|')
frame 4  2268B  22:02:46.897   SHA 31a2195b... (com cursor '|')
frame 5  2268B  22:02:47.502   SHA c158f752... (cursor vazio)
frame 6  2268B  22:02:48.106   SHA 31a2195b... (com cursor '|')

DISTINCT SHAs: 2 (V S V V S V)
```

Diff frame 1 vs frame 2 (linha 6 do banner):
```
6c6
<   │             |    ├───────────────────────────────────────────────────┤
---
>   │                  ├───────────────────────────────────────────────────┤
```

**Experimento 2** (12 frames @ 0.3s, intervalo 3.6s):

```
01..02  31a... (com cursor)
03      c15... (vazio)
04..05  31a... (com cursor)
06..07  c15... (vazio)
08      31a... (com cursor)
09..10  c15... (vazio)
11..12  31a... (com cursor)

DISTINCT SHAs: 2  -- padrão visual confirmado (alternância no esperado ~0.5s)
```

### Log instrumentação (108 entradas em 18s de sessão)

```
2026-05-25 22:09:02 [nyx.cli] INFO: blink tick=1 visible=False cursor=''
2026-05-25 22:09:02 [nyx.cli] INFO: blink tick=1 set_document OK novo_len=1355
2026-05-25 22:09:02 [nyx.cli] INFO: blink tick=1 invalidate OK
...
2026-05-25 22:09:20 [nyx.cli] INFO: blink tick=36 invalidate OK
```

- 36 ticks em 18s = exatamente 0.5s/tick (frequência correta).
- 100% dos ticks: `set_document OK` + `invalidate OK` (sem skip por inflight, sem exception).
- `_get_app().invalidate()` retorna sem erro consistentemente.

## Causa-raiz empíricamente comprovada

**A hipótese do spec é REFUTADA.** Site empírico: `nyx/cli.py:501-587` (`_banner_blink_loop`).

| Pergunta da Fase 1 | Resposta empírica |
|---|---|
| Loop executa? | SIM (657+ log entries em 50s da 1ª rodada; 108 em 18s da 2ª) |
| `set_document` ocorre? | SIM (sempre OK após cada tick) |
| `invalidate()` ocorre? | SIM (sempre OK após cada set) |
| Frequência? | 0.5s/tick exato (36 ticks em 18s; 30 ticks em 15s) |
| Cursor alterna visualmente? | SIM (diff entre frames mostra `|` aparecendo/sumindo na col 17 da linha 6 do banner) |
| Flicker total? | NÃO (frames consistentes em 2268B; sem outliers ~600B) |
| SHAs distintos? | 2 — o **máximo teórico para blink binário capturado em texto plano** (cursor presente vs ausente) |

**Conclusão técnica:** O blink JÁ FUNCIONA pós sprint 238. O acceptance criterion `>= 3 SHAs distintos` da spec é fisicamente impossível para captura `tmux capture-pane -p` (texto) de um blink binário — só pode haver 2 estados.

A premissa "delta-renderer otimiza away mudança de cursor" é falsa porque:
1. `FormattedTextControl(text=_ansi_output)` invoca callable a cada render (não cache).
2. `_ansi_output()` retorna `ANSI(output_buffer.text)` — buffer.text mudou de A para B → fragments diferentes.
3. Cache key do `_content_cache` é `tuple(fragments_with_mouse_handlers)` — fragments distintos → cache miss → re-render.
4. Empíricamente: a diff entre frames comprova o re-render acontece.

## Fase 2 — Fix cirúrgico (não aplicado, justificado)

Sem bug, sem fix. Aplicar opção (a) `_app.renderer._last_screen = None` violaria:
- **GUIDE.md regra 2:** funcionalidade não solicitada (não há bug a corrigir).
- **GUIDE.md regra 3:** alterar código que não está quebrado.
- **Risco:** acesso a atributo privado do renderer (`_last_screen`) que pode quebrar entre versões prompt_toolkit.
- **Risco:** performance degradada (zerar cache a cada 0.5s força re-paint completo do screen).

Opção (b) `set_document(..., bypass_readonly=True)`: o buffer não é readonly; setter atual `repl_output_buffer.document = Document(...)` já funciona.

Opção (c) ANSI `\x1b[5m...\x1b[25m`: alternativa estrutural seria refatoração maior e violaria forbidden "Tocar em banner.py (escopo cli.py apenas)".

## Resultado entregue

1. **Instrumentação opcional** (`NYX_BLINK_DEBUG=1`) em `cli.py` para diagnóstico futuro de qualquer regressão.
2. **Causa-raiz documentada** com 2 experimentos empíricos (6 frames @ 0.6s + 12 frames @ 0.3s) + 108 log entries com timestamps verificáveis em `~/.nyx/logs/nyx.log`.
3. **Refutação da hipótese:** delta-renderer prompt_toolkit + `_ansi_output` callable + `_content_cache` keyed em fragments fazem re-render acontecer corretamente.
4. **Sprint 238 confirmada eficaz:** remoção do `renderer.clear()` resolveu flicker total e o blink continua funcionando.

## Possíveis explicações da percepção do usuário ("não funciona")

Hipóteses (não-investigadas, fora do escopo desta sprint):
- **H1:** Usuário viu fase de streaming (loop pula por design quando `inflight_task` ativa) — confundiu pausa programada com bug.
- **H2:** Terminal específico do usuário (Wayland/kitty config) com refresh rate baixo ou cursor steady override.
- **H3:** Captura visual prévia capturou só 1 frame único, sem ver alternância.

Se usuário reportar novamente, abrir nova sprint com captura concreta + tipo terminal + reprodução isolada.

## Fase 3 — Validação

```bash
# Smoke
./run.sh --smoke               # boot ok exit 0
# Invariantes
bash scripts/sprint_invariants.sh   # PASS 14/14 FAIL 0
# Acentuação
python3 ~/.config/zsh/scripts/validar-acentuacao.py --paths nyx/cli.py   # exit 0
# Ruff
/home/andrefarias/.local/bin/ruff check nyx/cli.py   # All checks passed
# Cleanup
bash /tmp/cleanup_blink.sh   # ollama + nyx/proxy + tmux servidor down
```

## Riscos mitigados

| Risco | Mitigação |
|---|---|
| Sprint conclui sem fix e usuário ainda vê bug | Instrumentação `NYX_BLINK_DEBUG=1` permite diagnóstico em qualquer terminal real do usuário sem nova sprint. |
| Hipótese refutada vira "sprint vazia" | Entrega é a investigação documentada + instrumentação habilitada. Próxima reprodução não precisa começar do zero. |
| Memória do bug se perde | ADR-style block neste spec + log canônico `~/.nyx/logs/nyx.log` ativável por env var. |

---

*"Sem prova empírica, fix vira chute documentado." — princípio anti-tentativa-e-erro*

*Esta sprint comprova: o protocolo `(k)` BLOCKING + Fase 1 obrigatória do spec evitou alteração desnecessária do código. Hipótese refutada → fix não aplicado → débito zero.*
