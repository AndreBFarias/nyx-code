# SPRINT TUI-FIX-07A — Footer fixo, indicador de memória no boot, spinner ASCII compatível

## 0. SPEC (machine-readable)

```yaml
sprint:
  id: TUI-FIX-07A
  title: "Footer fixo via bottom_toolbar, indicador de memória no boot, spinner ASCII compatível"
  onda: 22
  bloco: 5b
  prioridade: MÉDIA
  tipo: Feature
  dependencias: [VALIDATE-ONDA-21]
  desbloqueia: [TUI-FIX-07B]

  touches:
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/cli.py
      reason: "Migrar render_footer por turno para bottom_toolbar fixo do PromptSession; adicionar indicador de memória no boot"
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/agent/output.py
      reason: "nyx_spinner detecta LANG não UTF-8 e cai para frames ASCII (|/-\\)"

  creates: []
  removes: []

  n_to_n_pairs:
    - descricao: "Remoção de chamadas a render_footer no loop do REPL precisa casar com o registro do bottom_toolbar no PromptSession — nunca parcial"
      paths:
        - /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/cli.py
    - descricao: "Indicador de memória no boot e comando /memory devem ler a mesma fonte (NyxMemory.index); TUI-FIX-07C implementa o /memory formal"
      paths:
        - /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/cli.py
        - /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/agent/memory.py

  forbidden:
    - "Adicionar emoji"
    - "Usar 'print()' em modules novos (permitido apenas em cli.py para REPL e output.py como render layer — ADR-024)"
    - "Menção a Claude/GPT/Anthropic"
    - "Path absoluto hardcoded fora de design_tokens/settings"
    - "Manter chamadas a render_footer dentro do loop de turnos (objetivo é eliminar poluição de scroll)"
    - "Tocar em paste/help/banner/toolbar (escopo de TUI-FIX-07B, UX-LAYOUT-01A, UX-LAYOUT-01B)"

  tests:
    - cmd: "./run.sh --gauntlet --only interface"
      timeout: 300
      deve_passar: true
    - cmd: "./run.sh --smoke"
      timeout: 60
      deve_passar: true

  acceptance_criteria:
    - "Footer renderiza uma única vez por sessão (como bottom_toolbar do PromptSession) e atualiza no mesmo lugar; após 10 turnos, scroll não contém 10 cópias do footer"
    - "Boot imprime '[memória: N entradas] <arquivo1>, <arquivo2>, <arquivo3> (+K)' quando houver memórias; nada quando N==0"
    - "Spinner detecta LANG sem UTF-8 (LC_ALL, LANG) e usa frames ASCII |/-\\ nesse caso; mantém frames Unicode em UTF-8"
    - "Gauntlet fase interface passa 100%"
    - "./run.sh --smoke continua PASS (check #13)"
    - "Acentuação PT-BR correta em tudo novo"
    - "Zero hex hardcoded introduzido fora de design_tokens.py"
```

---

# Sprint TUI-FIX-07A — Footer fixo, indicador de memória, spinner ASCII

**Status:** CONCLUIDA (header corrigido em MASTER-CLEANUP-02 2026-05-20; presença em concluidos/ implica CONCLUIDA conforme convenção do projeto)
**Data criação:** 2026-04-19
**Origem:** split de TUI-FIX-07 (usabilidade geral inchada) em 3 sprints filhas. Este arquivo herda literalmente as Fases 1, 4 e 7 do pai.
**Modelo obrigatório:** claude-opus-4-7 (sem subagentes)

---

## Contexto

> ADRs: 001 Local First; 004 Zero Emojis; 005 Anonimato; 006 PT-BR; 010 Zero Mocks; 013 Integração Obrigatória; 014/020 Testes via Gauntlet/run.sh; 024 Render Layer (`print` só em `cli.py` e `agent/output.py`).
>
> Estado: Python 3.10+, qwen3:4b em 11435, proxy 11436; 34 tools, 47 commands, 10 services. VALIDATE-ONDA-21 CONCLUIDA. TUI-FIX-07 original absorvido por 07A/07B/07C.

---

## Problema

Três pontos independentes:

1. **Footer polui scroll.** Aparece antes de cada prompt; após 10 turnos há 10 cópias. Correto: linha fixa abaixo do input, padrão `bottom_toolbar` do `PromptSession`.
2. **Memória é invisível.** Com arquivos em `~/.nyx/memory/`, o usuário não sabe que há memória carregada. Precisa indicador no boot.
3. **Spinner quebrado.** Glifo Unicode renderiza mal em locale não-UTF-8. `nyx_spinner` precisa cair para ASCII (`|/-\`) quando `LC_ALL`/`LANG` não indicam UTF-8.

---

## Solução

- `bottom_toolbar` callable no `PromptSession` exibindo `ctx X% · iter N · lidos R · modif M`. Eliminar chamadas a `render_footer` dentro do loop de turnos.
- Após instanciar `AgentLoop`, ler `agent._memory.index()` e imprimir `[memória: N entradas] <f1>, <f2>, <f3> (+K)` quando `N>0`.
- `nyx_spinner`: inspecionar `os.environ.get("LC_ALL", "") + os.environ.get("LANG", "")` (uppercase); se não contiver `UTF-8`/`UTF8`, usar frames ASCII.

---

## Arquivos alvo (paths absolutos)

### `/home/andrefarias/Desenvolvimento/Nyx-Code/nyx/cli.py`

**Antes (conceitual — localizar bloco atual do REPL que chama render_footer a cada turno):**
```python
while True:
    render_footer(app_state)
    user_input = session.prompt(HTML("<b>você</b> › "))
    ...
```

**Depois:**
```python
def _footer_fn():
    from prompt_toolkit.formatted_text import FormattedText
    ctx = app_state.get("ctx_pct", 0)
    it = app_state.get("iter_n", 0)
    rd = app_state.get("reads", 0)
    md = app_state.get("mods", 0)
    return FormattedText([("", f"ctx {ctx}% · iter {it} · lidos {rd} · modif {md}")])

session = PromptSession(bottom_toolbar=_footer_fn, ...)

while True:
    user_input = session.prompt(HTML("<b>você</b> › "))
    ...
```

E no bloco de boot, logo após `agent = AgentLoop(...)`:

```python
try:
    entries = agent._memory.index()
except Exception as exc:
    logger.warning("falha ao indexar memória no boot: %s", exc)
    entries = []

if entries:
    nomes = [e["file"] for e in entries[:3]]
    extra = f" (+{len(entries) - 3})" if len(entries) > 3 else ""
    print(f"  [memória: {len(entries)} entradas] {', '.join(nomes)}{extra}")
```

**Mudanças:**
- Registrar `bottom_toolbar` no `PromptSession`.
- Remover todas as chamadas a `render_footer` dentro do loop de turnos.
- Adicionar bloco de indicador de memória após instanciar `AgentLoop`.

### `/home/andrefarias/Desenvolvimento/Nyx-Code/nyx/agent/output.py`

**Antes (conceitual):**
```python
_SPINNER_FRAMES = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]

def nyx_spinner(...):
    ...
```

**Depois:**
```python
_SPINNER_UTF8 = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]
_SPINNER_ASCII = ["|", "/", "-", "\\"]


def _spinner_frames() -> list[str]:
    import os
    raw = (os.environ.get("LC_ALL", "") + os.environ.get("LANG", "")).upper()
    if "UTF-8" in raw or "UTF8" in raw:
        return _SPINNER_UTF8
    return _SPINNER_ASCII


def nyx_spinner(...):
    frames = _spinner_frames()
    ...
```

**Mudanças:**
- Separar frame set UTF-8 e ASCII.
- `_spinner_frames()` escolhe conforme locale.
- `nyx_spinner` consome a função.

---

## Diff esperado (resumo)

```
+ 0 arquivos criados
~ 2 arquivos modificados
- 0 arquivos removidos
+ ~35 linhas líquidas
```

---

## Comandos de verificação (literais, copy-paste)

```bash
cd /home/andrefarias/Desenvolvimento/Nyx-Code

# 1. Validação estática
python -m ruff check nyx/cli.py nyx/agent/output.py

# 2. Sanity: frames ASCII em LANG=C
LANG=C LC_ALL=C python -c "
from nyx.agent.output import _spinner_frames
fr = _spinner_frames()
assert fr == ['|', '/', '-', '\\\\'], fr
print('frames ASCII OK')
"

# 3. Sanity: frames Unicode em UTF-8
LANG=pt_BR.UTF-8 LC_ALL=pt_BR.UTF-8 python -c "
from nyx.agent.output import _spinner_frames
fr = _spinner_frames()
assert fr[0] == '⠋', fr
print('frames UTF-8 OK')
"

# 4. Gauntlet
./run.sh --gauntlet --only interface

# 5. Smoke
./run.sh --smoke

# 6. Validação manual
./run.sh
# Esperado no boot: linha '[memória: N entradas] ...' se houver memória.
# Esperado no scroll: após 5 turnos, o footer aparece UMA VEZ no rodapé, não duplicado no histórico.
# Ctrl+D para sair.
```

---

## Critério binário de aceite (IA executora)

- [ ] `bottom_toolbar` registrado no `PromptSession`; todas as chamadas antigas a `render_footer` dentro do loop de turnos removidas
- [ ] Boot imprime `[memória: N entradas] ...` quando `N > 0`; silencioso quando `N == 0`
- [ ] `_spinner_frames()` retorna ASCII em `LANG=C` e UTF-8 em `LANG=*.UTF-8`
- [ ] `./run.sh --gauntlet --only interface` passa 100%
- [ ] `./run.sh --smoke` continua PASS
- [ ] `ruff` não reclama
- [ ] Nenhuma violação de `forbidden[]`
- [ ] `SPRINT_ORDER_MASTER.md` atualizado marcando CONCLUIDA com hash
- [ ] Sprint movida de `producao/` para `concluidos/`
- [ ] Commit atômico criado

---

## Guardrails anti-engodo

Não marcar CONCLUIDA se algum critério estiver incompleto; se `render_footer` continua no loop de turnos; se indicador de memória é stub; se detector só olha `LANG` ou só `LC_ALL`; se gauntlet rodou sem output colado. Reportar `[SPRINT TUI-FIX-07A] BLOQUEADA: <motivo>` em falha.

---

## Gambiarras específicas

1. **Stub de bottom_toolbar.** Registrar callable que retorna string vazia só para passar a verificação. Proibido — precisa conter `ctx X% · iter N · lidos R · modif M` literalmente.
2. **Deixar render_footer convivendo "por segurança".** Objetivo da sprint é eliminar poluição de scroll; manter ambos é contradição.
3. **Detecção de UTF-8 via `sys.getdefaultencoding()`.** Não reflete locale do terminal. Usar `LC_ALL`/`LANG`.
4. **Indicador de memória via `print()` em módulo fora de `cli.py`.** ADR-024 proíbe; `print` só em `cli.py` REPL e `agent/output.py` render layer.
5. **Tocar em paste/help/banner/toolbar.** Fora de escopo — pertence a TUI-FIX-07B, UX-LAYOUT-01A, UX-LAYOUT-01B. Se esbarrar, criar sprint nova (protocolo anti-débito).

Ver `dev-journey/08-templates/GAMBIARRAS_POR_SPRINT.md` seção `TUI-FIX-07A` se existir.

---

## Proof-of-work obrigatório (4 passos)

```bash
# PASSO 1 — snapshot ANTES
bash scripts/sprint_invariants.sh > /tmp/inv_before.txt 2>&1
FAIL_BEFORE=$(grep -c "^\[FAIL\]" /tmp/inv_before.txt)
echo "FAIL inicial: $FAIL_BEFORE"

# PASSO 2 — implementação (seguindo este arquivo)

# PASSO 3 — snapshot DEPOIS
bash scripts/sprint_invariants.sh > /tmp/inv_after.txt 2>&1
FAIL_AFTER=$(grep -c "^\[FAIL\]" /tmp/inv_after.txt)
echo "FAIL final: $FAIL_AFTER"

# PASSO 4 — regras binárias
#   (a) $FAIL_AFTER <= $FAIL_BEFORE
#   (b) diff /tmp/inv_before.txt /tmp/inv_after.txt colado no relatório
```

Colar no relatório final: `tail -10` de cada snapshot, `diff`, output do gauntlet interface e do `--smoke`, e `git show --stat HEAD`.

Se `FAIL_AFTER > FAIL_BEFORE`: reverter (`git reset --hard HEAD~1`) e reiniciar.

---

## Validação humana (checklist do usuário)

```bash
cd /home/andrefarias/Desenvolvimento/Nyx-Code
git log --oneline -1
git show --stat HEAD

./run.sh
# 1. Ver '[memória: N entradas] ...' no boot, se houver memória.
# 2. Após 5 turnos: scroll NÃO contém 5 cópias do footer.
# 3. Em outro terminal com LANG=C: spinner usa |/-\.
# 4. Ctrl+D para sair.

ls dev-journey/06-sprints/concluidos/SPRINT_TUI_FIX_07A.md   # deve existir
ls dev-journey/06-sprints/producao/SPRINT_TUI_FIX_07A.md     # NÃO deve existir
```

---

## Riscos

| Risco | Mitigação |
|-------|-----------|
| `bottom_toolbar` conflita com bypass toolbar existente | Verificar se já há `bottom_toolbar` registrado por UX-LAYOUT-01B; se sim, compor callables em vez de sobrescrever |
| `agent._memory.index()` pode não existir em versões antigas do NyxMemory | Guard com `getattr(agent, "_memory", None)` e `try/except` com `logger.warning` explícito |
| Locale com UTF-8 em lowercase (`utf-8`) não detectado | Fazer comparação case-insensitive (`.upper()` e testar `UTF-8`/`UTF8`) |

---

*"A clareza é a virtude suprema da forma." -- Aristóteles*
