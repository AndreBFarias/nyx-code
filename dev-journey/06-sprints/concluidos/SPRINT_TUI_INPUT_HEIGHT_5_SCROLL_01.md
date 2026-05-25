# SPRINT 226 — TUI-INPUT-HEIGHT-5-SCROLL-01

## 0. SPEC (machine-readable)

```yaml
sprint:
  id: TUI-INPUT-HEIGHT-5-SCROLL-01
  title: "Input do REPL com altura fixa em 5 linhas visíveis + scrollbar interno"
  onda: 31
  prioridade: MÉDIA
  tipo: Refactor
  dependencias: []
  desbloqueia: []

  touches:
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/agent/repl_app.py
      reason: "input_window Dimension(min=1, max=5) -> Dimension(min=5, max=5) + ScrollbarMargin"
      linhas_alvo: "490-510"
  creates: []
  removes: []

  forbidden:
    - "Tocar em output_window (sprint S7 separada)"
    - "Modificar comportamento de Ctrl+J (newline interno)"
    - "Quebrar paridade com PromptSession legacy"
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
    - "Buffer vazio mostra 5 linhas visíveis (4 brancas + prompt > na linha 1)"
    - "Buffer com 3 linhas mostra 5 visíveis (3 conteúdo + 2 brancas)"
    - "Buffer com 7 linhas mostra 5 visíveis + ScrollbarMargin à direita"
    - "Ctrl+J cria newline interno preservado"
    - "Enter submete preservado"
    - "Sprint 185 INPUT_DEADLOCK não regrediu (input continua digitando)"
    - "Smoke boot ok"
    - "Invariantes 14/14 PASS"
    - "Acentuação rc=0"
```

---

# Sprint 226 — TUI-INPUT-HEIGHT-5-SCROLL-01

**Status:** PENDENTE
**Data criação:** 2026-05-25
**Modelo obrigatório:** claude-opus-4-7 (sem subagentes)

---

## Contexto do projeto (snapshot)

> **ADRs relevantes:**
> - ADR-024 Render Layer. ADR-026 Agência (usuário controla).
>
> **Estado do sistema:**
> - `nyx/agent/repl_app.py:494` define `input_window = Window(height=Dimension(min=1, max=5))`.
> - `nyx/agent/repl_app.py:228 output_buffer = Buffer(read_only=False, multiline=True)`.
> - `nyx/agent/repl_app.py:235 input_buffer = Buffer(multiline=True, ...)`.
> - `@kb.add("c-j")` cria newline interno (linha 299).
> - Sprint 185 TUI-INPUT-DEADLOCK-01 destravou digitação removendo `editing_mode=None`.

---

## Problema

Input atual cresce de 1 linha até 5 conforme texto. Usuário quer **altura fixa visível 5 linhas** desde o boot, com scrollbar interno quando texto > 5 linhas.

Feedback do usuário (2026-05-25): **"o input user sempre fica com 5 linhas mostrando tipo 5 control J ali em termos de espaço e se eu escrever mais do que cinco linhas ele adiciona uma barra de rolagem vertical apenas na área do user input. fora isso o > no início sempre aparece na linha 1 indepdnente de rolar pra cima ou pra baixo."**

### Sintoma observável

Input visivelmente colapsado para 1 linha quando vazio. Cresce expansivelmente com Ctrl+J. Sem indicador de scroll.

---

## Solução proposta

Alterar `Dimension(min=1, max=5)` → `Dimension(min=5, max=5)` e adicionar `right_margins=[ScrollbarMargin(display_arrows=False)]` ao `Window`.

Prompt `>` permanece na linha 1 do textarea (já é comportamento padrão do BufferControl multiline com cursor inicial em (0,0)).

---

## Arquivos alvo

### `/home/andrefarias/Desenvolvimento/Nyx-Code/nyx/agent/repl_app.py`

**Localização aproximada:** linha 494-498.

**Antes:**
```python
input_window = Window(
    content=BufferControl(buffer=input_buffer, ...),
    height=Dimension(min=1, max=5),
    ...
)
```

**Depois:**
```python
from prompt_toolkit.layout.margins import ScrollbarMargin   # noqa: E402

input_window = Window(
    content=BufferControl(buffer=input_buffer, ...),
    height=Dimension(min=5, max=5),
    right_margins=[ScrollbarMargin(display_arrows=False)],
    ...
)
```

**Mudanças:**
- min=1 → min=5 (altura sempre 5 visíveis).
- Adiciona `ScrollbarMargin` à direita.
- Import `ScrollbarMargin` adicionado no topo do arquivo (próximo aos demais imports prompt_toolkit).

---

## Diff esperado (resumo)

```
~ 1 arquivo modificado
+ ~3 linhas líquidas (import + 2 args)
```

---

## Comandos de verificação

```bash
# Smoke
./run.sh --smoke

# Visual interativo
./run.sh
# Cenário 1: input vazio → contar linhas (esperado: 5 visíveis com > na linha 1)
# Cenário 2: Ctrl+J 3x → 4 linhas (não cresce além de 5)
# Cenário 3: Ctrl+J 7x → 8 linhas total; visíveis ainda 5; scrollbar à direita
import -window $(xdotool search --name './run.sh' | head -1) /tmp/input_height.png

# Invariantes + gauntlet
bash scripts/sprint_invariants.sh
./run.sh --gauntlet --only rapido

# Acentuação
python3 ~/.config/zsh/scripts/validar-acentuacao.py --paths nyx/agent/repl_app.py
```

---

## Critério binário de aceite

- [ ] Buffer vazio: 5 linhas visíveis (4 brancas + prompt `>` linha 1).
- [ ] Buffer com 3 linhas: 5 visíveis.
- [ ] Buffer com 7 linhas: 5 visíveis com scrollbar.
- [ ] Sprint 185 INPUT_DEADLOCK preservada (input continua digitando).
- [ ] Ctrl+J e Enter preservados.
- [ ] Smoke + invariantes + gauntlet rapido OK.
- [ ] Spec movida producao/ → concluidos/.

---

## Proof-of-work (4 passos)

```bash
bash scripts/sprint_invariants.sh > /tmp/inv_before.txt 2>&1
# Edit (3 linhas)
bash scripts/sprint_invariants.sh > /tmp/inv_after.txt 2>&1
diff /tmp/inv_before.txt /tmp/inv_after.txt
# Visual cenários (acima)
sha256sum /tmp/input_height.png
```

---

## Riscos

| Risco | Mitigação |
|---|---|
| Altura fixa 5 reduz real-estate da conversa em 4 linhas | Confirmado por feedback do usuário |
| `ScrollbarMargin` pode não existir em prompt_toolkit instalado | Verificar versão via `python -c "from prompt_toolkit.layout.margins import ScrollbarMargin"` antes do commit |
| Regressão na sprint 185 (deadlock do input) | Re-rodar tmux send-keys "ola mundo" para confirmar input ainda aceita |
| Cursor inicial em (0,0) — prompt > pode aparecer linha 5 em vez de 1 | `cursor_position=0` no Buffer já garante topo |

---

*"5 linhas dão respiro. 1 linha aperta. Espaço é UX." — princípio*
