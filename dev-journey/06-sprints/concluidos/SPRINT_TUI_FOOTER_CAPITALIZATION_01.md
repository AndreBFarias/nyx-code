# SPRINT 287 — TUI-FOOTER-CAPITALIZATION-01

## 0. SPEC

```yaml
sprint:
  id: TUI-FOOTER-CAPITALIZATION-01
  title: "Capitalizar os 4 rotulos de metrica do footer da NyxTUI (Ctx/Iter/Lidos/Modif)"
  onda: 34
  prioridade: BAIXA
  tipo: UX
  dependencias: [TUI-INPUT-TEXTAREA-MULTILINE-01]
  desbloqueia: []

  touches:
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/agent/tui/widgets/toolbar.py
      reason: "render() (L85-113) emite os rotulos em minusculo via msg.append(f'ctx ...'), msg.append(f'iter ...'), msg.append(f'lidos ...'), msg.append(f'modif ...'); decisao #7 da auditoria pede inicial maiuscula. Somente os literais de rotulo mudam; reactives/watchers/glyph/modo intactos."
  creates: []
  removes: []

  forbidden:
    - "Tocar nyx/agent/tui/widgets/banner.py (arquivo protegido pelo check #14 anti-sanitizer -- fora de escopo)"
    - "Tocar nyx/agent/output.py::render_footer (footer legado do PromptSession, sem chamador vivo -- registrado como item separado abaixo)"
    - "Alterar qualquer reactive property, watch_* handler, glyph (STATE_GLYPHS) ou os labels de modo (shift+tab / [plan] / [sudo] / bypass)"
    - "Mudar a logica de degradacao por largura ou os separadores '  |  '"
    - "Adicionar emoji ou mencao a IA externa"

  tests:
    - cmd: "./run.sh --smoke"
      timeout: 10
      deve_passar: true
    - cmd: "bash scripts/sprint_invariants.sh"
      timeout: 60
      deve_passar: true

  acceptance_criteria:
    - "render() do Toolbar emite 'Ctx X%', 'Iter N', 'Lidos M', 'Modif K' (inicial maiuscula nos 4 rotulos de metrica)"
    - "Nome do modelo, glyph, model_state e labels de modo (shift+tab/[plan]/[sudo]/bypass) permanecem byte-identicos ao atual"
    - "Nenhum reactive property ou watch_* handler alterado (so os literais de string)"
    - "Smoke boot ok + invariantes 14/14 FAIL=0 + gauntlet rapido + loop APROVADO"
    - "Validação --web confirma footer com rotulos capitalizados (antes: minusculo)"
```

---

## Contexto

Decisao #7 da auditoria de redesign (`~/.claude/plans/redesign-auditoria-da-tender-beacon.md`, linha 56: "Capitalizacao: `Ctx / Iter / Lidos / Modif` no footer + revisar saidas do output") sinaliza que o footer/toolbar da NyxTUI exibe os rotulos de metrica em minusculo. O bloco ONDA-34 do `SPRINT_ORDER_MASTER.md` (linha 813) lista "capitalizacao do footer" como o primeiro item PENDENTE dos IDs 287+.

Texto exato confirmado via leitura de `nyx/agent/tui/widgets/toolbar.py::render()` (L85-113):

```python
msg.append(f"ctx {self.ctx_pct}%", style=NYX_ACCENT)   # L86
msg.append(f"iter {self.iter_n}", style=NYX_MUTED)      # L90
msg.append(f"lidos {self.reads}", style=NYX_MUTED)      # L92
msg.append(f"modif {self.mods}", style=NYX_MUTED)       # L94
```

O layout final renderizado e:

```
ctx X%  |  <modelo>  |  iter N  |  lidos M  |  modif K  |  <glyph> <state>    shift+tab: normal/plan/sudo/bypass
```

Os 4 rotulos-alvo (`ctx`, `iter`, `lidos`, `modif`) NÃO possuem acentuacao, entao a capitalizacao e puramente trocar a inicial. Nenhum rotulo do footer e "Memoria" ou similar acentuado.

## Escopo (touches autorizados)

- Arquivos a modificar: `nyx/agent/tui/widgets/toolbar.py` (apenas 4 literais de rotulo dentro de `render()`).
- Arquivos a criar: nenhum.
- Arquivos NÃO a tocar:
  - `nyx/agent/tui/widgets/banner.py` — protegido pelo check #14 (lista dos 7 arquivos anti-sanitizer no BRIEF, protocolo de regressao L73). Fora de escopo desta sprint.
  - `nyx/agent/output.py::render_footer` (L1288-1315) — footer legado do path PromptSession; o grep confirma que NÃO ha chamador vivo no codigo (`rg 'render_footer' nyx/ tests/` retorna so a definicao). A clausula "revisar saidas do output" da decisao #7 e vaga/ampla; conforme o protocolo anti-debito (memoria `feedback_nenhum_debito.md`), fica registrada como item separado (ver "Riscos e não-objetivos").
  - Qualquer reactive/watcher/CSS do widget.

## Acceptance criteria

1. `render()` emite `Ctx {pct}%` no lugar de `ctx {pct}%` (L86).
2. `render()` emite `Iter {n}` no lugar de `iter {n}` (L90).
3. `render()` emite `Lidos {reads}` no lugar de `lidos {reads}` (L92).
4. `render()` emite `Modif {mods}` no lugar de `modif {mods}` (L94).
5. Nome do modelo (`self._model`, L88), glyph + `model_state` (L96-97), hint de inflight (L103) e labels de modo (L106-112) permanecem byte-identicos.
6. Nenhum reactive property nem `watch_*` handler tocado (so os 4 literais).
7. Smoke `./run.sh --smoke` -> `boot ok` exit 0.
8. `bash scripts/sprint_invariants.sh` -> PASS 14/14 FAIL 0.
9. `./run.sh --gauntlet --only rapido` 100% + loop APROVADO.
10. `validar-acentuacao.py --paths` no arquivo tocado -> rc 0.

## Invariantes a preservar

- **Anti-sanitizer / check #14 (BRIEF L73, L134)**: `toolbar.py` NÃO esta na lista dos 7 arquivos protegidos (`nyx/cli.py`, `design_tokens.py`, `output.py`, `banner.py`, `repl_app.py`, `design_tokens_extended.py`, `sprint_invariants.sh`). Editar `toolbar.py` não reabre o vetor de glifos. NAO tocar `banner.py` mantem o invariante intacto.
- **Refresh por-widget (toolbar.py docstring L47-51, lição BannerWidget 185/193)**: não alterar a mecanica de `self.refresh()` nos watchers; a sprint so muda literais, sem efeito de re-render.
- **Mudancas cirurgicas (GUIDE.md §3)**: tocar apenas os 4 literais; não reformatar linhas adjacentes nem "melhorar" separadores/estilos.
- **Nada solto / integracao obrigatoria (memoria `feedback_integracao_obrigatoria.md`)**: a unica validação runtime de UI e via `--web` + invariantes + gauntlet; nenhum teste novo isolado.
- **Anti-debito (memoria `feedback_nenhum_debito.md`)**: a parte "revisar saidas do output" da decisao #7 vira item registrado, não absorvido.

## Plano de implementação

1. `0.3` Confirmar hipotese: `rg -n 'msg.append\(f"(ctx|iter|lidos|modif) ' nyx/agent/tui/widgets/toolbar.py` deve retornar as 4 linhas (86, 90, 92, 94). Se a grafia divergir, parar e reportar.
2. Editar L86: `f"ctx {self.ctx_pct}%"` -> `f"Ctx {self.ctx_pct}%"`.
3. Editar L90: `f"iter {self.iter_n}"` -> `f"Iter {self.iter_n}"`.
4. Editar L92: `f"lidos {self.reads}"` -> `f"Lidos {self.reads}"`.
5. Editar L94: `f"modif {self.mods}"` -> `f"Modif {self.mods}"`.
6. NAO mexer no docstring L79 (exemplo `ctx X% | model | iter N | lidos M | modif K`); e comentario ilustrativo, mas se quiser coerencia pode atualizar para `Ctx X% | model | Iter N | Lidos M | Modif K` (opcional, cirurgico, não quebra nada). Decisao: atualizar tambem para manter docstring fiel ao render.
7. Rodar a bateria de proof-of-work (secao Proof-of-work).

## Aritmética

Sem meta numerica de linhas. A mudanca e de 4 caracteres (um por rotulo: `c->C`, `i->I`, `l->L`, `m->M`), mais a atualizacao opcional do docstring de exemplo (L79). Saldo de linhas: 0 (edicao in-place, sem add/remove de linhas). Nao ha extracao nem refactor.

## Testes

- Nenhum teste novo a adicionar: não existe teste que faca assert dos rotulos do widget `Toolbar` (confirmado: `rg -l 'Toolbar' tests/` retorna vazio; os unicos asserts de `lidos|modif` em codigo estao em `nyx/agent/output.py` render_footer/output legado, fora de escopo).
- Baseline esperada: `FAIL_BEFORE` (invariantes) = 0, `FAIL_AFTER` = 0. Gauntlet rapido baseline ~19/19 (conforme sprints 283-286), `FAIL_AFTER` <= baseline.
- Regressao visual e o teste real (secao Proof-of-work --web).

## Proof-of-work esperado

- **Diff final**: 4 (ou 5 com docstring) literais alterados em `toolbar.py`, nada mais.
- **Runtime real** (comandos do BRIEF seção `[CORE] Contratos de runtime`):
  - Smoke: `./run.sh --smoke` -> `boot ok` exit 0.
  - Invariantes: `bash scripts/sprint_invariants.sh` -> PASS 14/14 FAIL 0.
  - Gauntlet: `./run.sh --gauntlet --only rapido` -> 100% + loop APROVADO. (Disciplina OOM: so rapido/por-fase; sem paralelismo; GPU 4GB.)
- **Validação visual (--web)**:
  - `./run.sh --web` (cockpit em `http://127.0.0.1:11437`).
  - Conectar via playwright (ToolSearch `mcp__plugin_playwright_playwright__*`) OU Chrome real via CDP/X11 (`DISPLAY=:1`, fallback alinhado a `feedback_validacao_visual_ambiente_real.md`).
  - Confirmar via dump do buffer xterm.js (`browser_evaluate` varrendo `term.buffer.active` linha a linha procurando a linha do footer) OU screenshot, que o footer mostra `Ctx ... Iter ... Lidos ... Modif` (capitalizado). Registrar o ANTES (minusculo) como referencia historica do commit `3e31739`.
- **Acentuacao periferica**: `python3 ~/.config/zsh/scripts/validar-acentuacao.py --paths nyx/agent/tui/widgets/toolbar.py` -> rc 0. (BRIEF L36: usar `--paths`, não posicional.)
- **Hipotese verificada** (lição 4): `rg -n 'msg.append\(f"(ctx|iter|lidos|modif) ' nyx/agent/tui/widgets/toolbar.py` antes do edit confirma as 4 linhas exatas.
- **Cleanup OOM (BRIEF L21)**: apos `--web`/gauntlet, `pkill -f "nyx/proxy.py"`, `pkill -f "ollama serve"`, `nvidia-smi` confirmando VRAM livre. Cleanup por PID, sem paralelismo.

## Riscos e não-objetivos

- **Risco**: nenhum funcional — sao literais cosmeticos sem leitura por parser/teste. Risco residual zero sobre reactives/glyph.
- **Não-objetivo (anti-debito, item separado)**: a clausula "+ revisar saidas do output" da decisao #7 e ampla e cobre `nyx/agent/output.py::render_footer` (footer legado, sem chamador vivo) e potencialmente outras saidas de `output.py`. NAO entra nesta sprint. Registrar como sprint nova **TUI-OUTPUT-CAPITALIZATION-AUDIT-01** (ONDA-34, BAIXA): auditar as saidas de `nyx/agent/output.py` (render_footer L1306/1310/1314, render_context_compaction L1019, e demais) e decidir capitalizacao/remoção de codigo morto. So abrir se o usuario confirmar que o footer legado ainda e alcancavel por algum path; caso contrario, vira candidato a remoção de codigo morto (mencionar, não deletar — GUIDE.md §3).
- **Não-objetivo**: capitalizar nome de modelo, state (cold/warming/warm) ou labels de modo. A ideia restringe aos 4 rotulos de metrica; manter o resto como esta.

## Referências

- BRIEF: `/home/andrefarias/Desenvolvimento/Nyx-Code/VALIDATOR_BRIEF.md` (contratos runtime L9-13; `--paths` L36; protocolo check #14 L65-90; arquivos protegidos L73).
- Plano de auditoria: `~/.claude/plans/redesign-auditoria-da-tender-beacon.md` (decisao #7, L56; tabela audit L42).
- Master: `dev-journey/06-sprints/SPRINT_ORDER_MASTER.md` (bloco MANUAL_OVERRIDE_ONDA_34, L795-815; item 287 listado na L813).
- Base estavel: commit `3e31739` (última na origin/main).
- Precedente de formato: `dev-journey/06-sprints/producao/SPRINT_UX_COCKPIT_RESPONSIVE_FIT_01.md` (sprint 247).
- Arquivo-alvo: `nyx/agent/tui/widgets/toolbar.py::render()` (L76-113).
```
