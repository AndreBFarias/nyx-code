# SPRINT 285 — TUI-INPUT-CSS-SANITIZE-01

## 0. SPEC

```yaml
sprint:
  id: TUI-INPUT-CSS-SANITIZE-01
  title: "Saneia CSS do InputWidget: remove seletores mortos e unifica height (3 vs 5)"
  onda: 34
  prioridade: ALTA
  tipo: Bugfix
  dependencias: [TUI-SLASH-COMPLETER-POPULATE-01]
  desbloqueia: [TUI-INPUT-TEXTAREA-MULTILINE-01]

  touches:
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/agent/tui/widgets/input.py
      reason: "DEFAULT_CSS declara height:3 que conflita com nyx.tcss height:5 (borda cortada/altura ambígua); remover bloco DEFAULT_CSS ou alinhar a 5"
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/agent/tui/styles/nyx.tcss
      reason: "Seletores mortos 'InputWidget > TextArea, InputWidget > Input' (linhas ~114-123) -- InputWidget E-UM Input (subclasse), não tem filho desse tipo; regras nunca casam"
  creates: []
  removes: []

  forbidden:
    - "Trocar a classe-base do InputWidget (Input -> TextArea) -- escopo da sprint 286"
    - "Mexer em qualquer logica Python alem do bloco DEFAULT_CSS de input.py"
    - "Tocar app.py, chat_message.py, banner.py, toolbar.py"
    - "Introduzir hex de cor hardcoded (usar variaveis Textual $accent/$surface/$foreground)"
    - "Adicionar emoji ou mencao a IA externa"

  tests:
    - cmd: "./run.sh --smoke"
      timeout: 15
      deve_passar: true
    - cmd: "bash scripts/sprint_invariants.sh"
      timeout: 60
      deve_passar: true

  acceptance_criteria:
    - "nyx.tcss não contem mais os seletores 'InputWidget > TextArea' nem 'InputWidget > Input' (mortos)"
    - "Existe uma unica fonte de verdade para height do InputWidget (sem conflito 3 vs 5)"
    - "No --web a borda turquesa do input NÃO aparece cortada (4 lados visiveis); altura estavel em 5 linhas"
    - "Ghost-completer do slash (sprint 284) continua funcionando -- nada de Python tocado"
    - "smoke boot ok; invariantes 14/14 FAIL=0; acentuacao rc=0"
```

---

## Contexto

A migração TUI prompt_toolkit -> Textual (ONDA-32) deixou o CSS do input com dois defeitos correlatos, catalogados na auditoria ONDA-34 (`~/.claude/plans/redesign-auditoria-da-tender-beacon.md`, linha 40, severidade ALTA, "Input cortado"):

1. **Seletores mortos** em `nyx/agent/tui/styles/nyx.tcss` (linhas ~114-123): `InputWidget > TextArea, InputWidget > Input` e suas variantes `:focus`. `InputWidget` herda de `textual.widgets.Input` (é-UM Input, confirmado em `input.py:28` `class InputWidget(Input)`), não tem um filho do tipo `Input`/`TextArea`. O combinador de descendência `>` nunca casa — regras inertes.
2. **Conflito de height**: `input.py:46-56` declara `DEFAULT_CSS` com `height: 3`; `nyx.tcss:106-113` declara `InputWidget { height: 5 }`. Em Textual, CSS de arquivo (`CSS_PATH`) tem precedência sobre `DEFAULT_CSS` da classe, então o valor efetivo é 5 — mas a coexistência dos dois valores é débito e fonte de confusão (a auditoria suspeita que contribui para a borda cortada percebida).

Esta sprint é o **passo de saneamento que de-risca o swap Input->TextArea** (sprint 286). É puramente CSS, sem tocar lógica Python além do bloco `DEFAULT_CSS`, e portanto **não regride** o ghost-completer recém-entregue pela sprint 284 (commit 4fe225f).

## Escopo (touches autorizados)

- Arquivos a modificar:
  - `/home/andrefarias/Desenvolvimento/Nyx-Code/nyx/agent/tui/widgets/input.py` — remover (ou alinhar a 5) o bloco `DEFAULT_CSS` para eliminar o conflito de height. Recomendado: **remover o `DEFAULT_CSS` inteiro** e deixar `nyx.tcss` como fonte única (já cobre `dock: bottom`, `height: 5`, `background`, `border`, `padding`). A única regra exclusiva do `DEFAULT_CSS` é `InputWidget > .input--placeholder { color: $accent 50% }`; portá-la para `nyx.tcss` como `InputWidget > .input--placeholder` (esse seletor SIM casa — `.input--placeholder` é a classe interna do componente de placeholder do `Input`, não um widget filho).
  - `/home/andrefarias/Desenvolvimento/Nyx-Code/nyx/agent/tui/styles/nyx.tcss` — remover os blocos mortos `InputWidget > TextArea, InputWidget > Input { ... }` (linhas ~114-118) e `InputWidget > TextArea:focus, InputWidget > Input:focus { ... }` (linhas ~120-123); acolher o seletor de placeholder vindo do `DEFAULT_CSS`.
- Arquivos a criar: nenhum.
- Arquivos NÃO a tocar:
  - `nyx/agent/tui/app.py` — composição e bindings ficam intactos (sprint 286 cuida do Ctrl+J).
  - `nyx/agent/onboarding.py`, `nyx/cli.py` — fora de escopo.
  - Os 7 arquivos protegidos pelo check #14 (anti-sanitizer): `input.py` e `nyx.tcss` NÃO estão na lista, então sem risco de glifo-órfão; ainda assim a varredura de acentuação roda nos modificados.

## Acceptance criteria

1. `grep -nE "InputWidget > (TextArea|Input)" nyx/agent/tui/styles/nyx.tcss` retorna vazio.
2. Não há mais dois valores de `height` para `InputWidget` (apenas um, em `nyx.tcss`).
3. O placeholder do input mantém a cor `$accent 50%` (regra preservada, agora num seletor que casa).
4. No `--web`: borda turquesa íntegra nos 4 lados (não cortada), altura 5 linhas estável.
5. Ghost-completer do slash (digitar `/` mostra sugestão dim) continua funcionando — verificação anti-regressão da sprint 284.
6. smoke boot ok; `sprint_invariants.sh` 14/14 FAIL=0; `validar-acentuacao.py` rc=0.

## Invariantes a preservar

- **Check #6 (zero hex hardcoded)**: aplica-se só a `.py` (`scripts/sprint_invariants.sh:129-143` filtra Python); `nyx.tcss` usa variáveis Textual (`$accent`, `$surface`, `$foreground`) — não introduzir hex literal em lugar nenhum.
- **Check #14 (anti-sanitizer)**: `input.py`/`nyx.tcss` não são arquivos protegidos; nenhuma alteração de glifo canônico envolvida.
- **GUIDE.md §3 (mudanças cirúrgicas)**: tocar apenas os dois blocos descritos; não "melhorar" CSS adjacente (Toolbar, banner, chat).
- **Dock order** (`app.py:119-132`): a remoção de regras mortas não altera o `dock: bottom` do InputWidget nem a ordem Input->Toolbar; não mexer.

## Plano de implementação

1. Em `nyx/agent/tui/widgets/input.py`: remover o atributo `DEFAULT_CSS` (linhas ~46-56) por completo.
2. Em `nyx/agent/tui/styles/nyx.tcss`: dentro do bloco `/* ---------- InputWidget ---------- */`, **remover** os dois blocos de seletor morto (`InputWidget > TextArea, InputWidget > Input` e o `:focus`).
3. No mesmo bloco, **adicionar** a regra de placeholder migrada do DEFAULT_CSS:
   ```
   InputWidget > .input--placeholder {
       color: $accent 50%;
   }
   ```
4. Confirmar que `InputWidget { dock: bottom; height: 5; background: $surface; border: round $accent; padding: 0 1; }` permanece intacto (fonte única).
5. Rodar smoke + invariantes + acentuação.
6. Validação visual `--web` (cockpit :11437) inspecionando a borda do input.

## Aritmética

Sem meta numérica de redução de linhas. Saldo de linhas:
- `input.py`: remoção do `DEFAULT_CSS` ~ −11 linhas (bloco de 46 a 56).
- `nyx.tcss`: remoção de 2 blocos mortos (~10 linhas) + adição de 1 bloco de placeholder (~3 linhas) = saldo ~ −7 linhas.
- Net esperado: ~ −18 linhas. Sem alvo `<NL` a fechar.

## Testes

- Não há suíte pytest cobrindo `InputWidget` (grep em `tests/` retornou zero — confirmado). Sem teste novo obrigatório; a verificação é runtime (`--web`) + invariantes.
- Baseline: FAIL_BEFORE = estado atual de `sprint_invariants.sh`. Esperado FAIL_AFTER == FAIL_BEFORE (mudança é CSS puro). Registrar os números reais no proof-of-work.

## Proof-of-work esperado

- Diff final dos 2 arquivos.
- Runtime real (BRIEF seção `[CORE] Contratos de runtime`):
  - Smoke: `./run.sh --smoke` -> `boot ok`, exit 0.
  - Invariantes: `bash scripts/sprint_invariants.sh` -> 14/14, FAIL=0.
  - Gauntlet (disciplina OOM, só ao fechar bloco): `./run.sh --gauntlet --only rapido`. Ver flake reprodutível do BRIEF (1ª execução fresca 18/18 ou 17/18; aceitar 1 execução e cruzar com `--only proxy` se necessário).
- Validação visual (UI): `./run.sh --web` (cockpit 127.0.0.1:11437), inspeção via playwright (ToolSearch `mcp__plugin_playwright_playwright__*`) ou Chrome real CDP + skill `validação-visual` — capturar PNG da borda do input íntegra (4 lados) e do ghost-completer após `/`; gerar sha256 do PNG.
- Acentuação periférica: `python3 /home/andrefarias/.config/zsh/scripts/validar-acentuacao.py --paths nyx/agent/tui/widgets/input.py nyx/agent/tui/styles/nyx.tcss` -> rc=0.
- Hipótese verificada (lição 4): `rg -n "class InputWidget" nyx/agent/tui/widgets/input.py` confirma base `Input`; `rg -n "InputWidget > (TextArea|Input)" nyx/agent/tui/styles/nyx.tcss` pós-fix retorna vazio.

## Riscos e não-objetivos

- **Não-objetivo**: trocar a base para `TextArea`, adicionar Ctrl+J, suportar multiline — isso é a sprint 286.
- **Risco baixo**: se a borda continuar cortada após o saneamento, a causa-raiz é outra (provável `padding`/`border` vs `height: 5` na renderização do cockpit/xterm.js, correlato às sprints 281-282). Nesse caso registrar achado como sprint nova (protocolo anti-débito, MEMORY: "Nenhum débito fica para trás") — não absorver implicitamente.

## Referências

- BRIEF: `/home/andrefarias/Desenvolvimento/Nyx-Code/VALIDATOR_BRIEF.md` (Contratos de runtime; flake OOM do gauntlet rápido).
- Plano da onda: `~/.claude/plans/redesign-auditoria-da-tender-beacon.md` (decisão #2, linha 51; matriz linha 40).
- Precedente: sprint 284 (commit 4fe225f, slash-completer ghost-inline) — não regredir.
- MASTER: `dev-journey/06-sprints/SPRINT_ORDER_MASTER.md` (linha 811, bloco ONDA-34 em curso).
