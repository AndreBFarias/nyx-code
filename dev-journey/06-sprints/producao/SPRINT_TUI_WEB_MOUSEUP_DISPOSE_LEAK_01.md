# SPRINT — TUI-WEB-MOUSEUP-DISPOSE-LEAK-01

## 0. SPEC (machine-readable)

```yaml
sprint:
  id: TUI-WEB-MOUSEUP-DISPOSE-LEAK-01
  title: "Erro do xterm.js no mouseup apos recreateTerminal (listener orfao pos-dispose)"
  onda: backlog-pos-35
  prioridade: BAIXA
  tipo: Bugfix
  origem: "Achado da validação da SPRINT 247 no Chrome real do usuário (2026-05-31)"
  dependencias: []
  desbloqueia: []

  touches:
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/cockpit/static/terminal.html
      reason: "recreateTerminal() faz term.dispose() mas o listener de mouseup no document fica orfao"
  creates: []
  removes: []

  forbidden:
    - "Suprimir o erro com try/catch vazio (gambiarra) -- corrigir a causa"
    - "Reintroduzir o tiling do resize (TUI-FIX-WEB-RESIZE-TILING-01)"
    - "Adicionar emoji / mencao a IA"

  tests:
    - cmd: "./run.sh --smoke"
      deve_passar: true
    - cmd: "bash scripts/sprint_invariants.sh"
      deve_passar: true

  acceptance_criteria:
    - "Após resize do --web + clique no terminal, o console NÃO mostra Uncaught TypeError (dimensions)"
    - "O resize continua sem tiling (1 input box)"
    - "Smoke + invariantes 14/14"
```

---

**Status:** PENDENTE
**Data criação:** 2026-05-31
**Modelo obrigatório:** claude-opus-4-7 (sem subagentes)

---

## Problema

No `--web`, após o `recreateTerminal()` (disparado no resize), soltar o mouse (mouseup) gera no console:

```
Uncaught TypeError: Cannot read properties of undefined (reading 'dimensions')
  at get dimensions (xterm.js)
  at MouseService.getMouseReportCoords (xterm.js)
  at i (xterm.js)
  at HTMLDocument.mouseup (xterm.js)
```

Capturado no Chrome real do usuário durante a validação da SPRINT 247 (2026-05-31). Não quebra o render (o terminal continua funcionando), mas polui o console e pode afetar cliques após um resize. Provável amplificação naquela sessão: o experimento revertido da 247 (ResizeObserver) fez ~25 recreates → ~25 listeners órfãos.

## Causa-raiz (a confirmar na FASE 0)

`recreateTerminal()` chama `term.dispose()` e cria um `new Terminal`. O xterm.js registra um listener de `mouseup` no `document` (para mouse report / seleção quando o mouse é solto fora do terminal). A hipótese: o `dispose()` do xterm.js 5.3.0 vendored **não remove** esse listener do `document`; o listener órfão dispara num mouseup posterior e acessa o render service já descartado (`dimensions` undefined).

## FASE 0 — repro obrigatória (antes do fix)

Via playwright: subir `--web`, navegar, **resize 1x** (1 recreate), **clicar no #terminal** (gera mouseup), ler o console (`browser_console_messages`). Confirmar:
- Reproduz com **1** recreate (bug latente) ou só com **muitos** (resíduo do experimento da 247)?
- Quantos listeners de `mouseup` há no `document` após N recreates (`getEventListeners(document)` no DevTools, ou instrumentar `addEventListener`)?

## Solução (direcionada pela FASE 0)

Candidatas, da menos à mais invasiva:
1. Confirmar se `term.dispose()` é chamado e se o xterm.js remove os listeners; se o dispose for incompleto, **desligar o mouse tracking / detach explícito** antes do dispose.
2. Guardar a referência do Terminal e garantir `dispose()` síncrono antes de criar o novo (já é o caso) + aguardar microtask se necessário.
3. Se for limitação do xterm.js 5.3.0 vendored: avaliar patch mínimo no vendored OU upgrade pontual (cuidado: a ONDA-34 testou 5.5.0 e manteve 5.3.0 por causa do resize-tiling — não regredir).

## Proof-of-work

```bash
# repro/validação via playwright: resize + clique, ler console (deve ficar limpo)
./run.sh --smoke
bash scripts/sprint_invariants.sh   # 14/14
./run.sh --gauntlet --only rapido   # APROVADO (não toca o agente, mas mantém o gate)
```

## Critério de aceite

- [ ] FASE 0: repro documentada (1 recreate vs muitos).
- [ ] Console limpo (sem o TypeError) após resize + clique no `--web` real.
- [ ] Resize sem tiling preservado.
- [ ] Smoke + invariantes 14/14.

---

*"Quem cria um terminal e o descarta deve recolher também os ouvidos que deixou no document." -- anônimo*
