# SPRINT TUI-FIX-07B — Paste longo colapsado com Ctrl+O e /help categorizado

## 0. SPEC (machine-readable)

```yaml
sprint:
  id: TUI-FIX-07B
  title: "render_user_input colapsa paste longo com Ctrl+O para expandir; /help categorizado com /help all"
  onda: 22
  bloco: 5b
  prioridade: MÉDIA
  tipo: Feature
  dependencias: [TUI-FIX-07A]
  desbloqueia: [TUI-FIX-07C]

  touches:
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/agent/output.py
      reason: "render_user_input detecta paste > 8 linhas e renderiza colapsado (eco)"
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/agent/commands/core.py
      reason: "cmd_help retorna lista curta por padrão (10 comandos) e lista completa (47) quando args=='all'"
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/cli.py
      reason: "Registrar keybind Ctrl+O que re-renderiza o último input de forma expandida"

  creates: []
  removes: []

  n_to_n_pairs:
    - descricao: "Colapso em render_user_input preserva o texto completo na sessão (histórico enviado ao modelo não é truncado)"
      paths:
        - /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/agent/output.py
        - /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/cli.py
    - descricao: "Lista curta do /help e lista completa /help all leem do mesmo registry de commands — nunca duplicar a lista literal"
      paths:
        - /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/agent/commands/core.py

  forbidden:
    - "Adicionar emoji"
    - "Usar 'print()' em modules novos (permitido apenas em cli.py e agent/output.py — ADR-024)"
    - "Menção a Claude/GPT/Anthropic"
    - "Colapsar paste por padrão em textos curtos (limiar obrigatório: > 8 linhas)"
    - "Tocar no banner (_build_banner) ou na toolbar — escopo de UX-LAYOUT-01A/01B"
    - "Quebrar o completer existente de slash commands ao mexer em cmd_help"
    - "Alterar histórico da sessão: o texto completo do paste deve ir ao modelo; só o eco visual colapsa"

  tests:
    - cmd: "./run.sh --gauntlet --only interface"
      timeout: 300
      deve_passar: true
    - cmd: "./run.sh --smoke"
      timeout: 60
      deve_passar: true

  acceptance_criteria:
    - "Paste > 8 linhas em render_user_input exibe eco como: primeira linha + '... [N linhas ocultas -- Ctrl+O para expandir]'"
    - "Paste <= 8 linhas renderiza integralmente, sem colapso"
    - "Ctrl+O dentro do REPL re-renderiza o último input do usuário em forma expandida"
    - "/help sem argumento mostra exatamente 10 comandos (os mais usados) + linha 'Digite /help all para ver todos'"
    - "/help all mostra os 47 comandos derivados do registry (não lista literal hardcoded)"
    - "Texto completo do paste continua no histórico enviado ao modelo (colapso é apenas visual)"
    - "Completer de slash commands continua funcional (não quebrado por cmd_help)"
    - "Gauntlet fase interface passa 100%"
    - "./run.sh --smoke continua PASS"
    - "Acentuação PT-BR correta em tudo novo"
```

---

# Sprint TUI-FIX-07B — Paste colapsado + /help categorizado

**Status:** CONCLUIDA (header corrigido em MASTER-CLEANUP-02 2026-05-20; presença em concluidos/ implica CONCLUIDA conforme convenção do projeto)
**Data criação:** 2026-04-19
**Origem:** split de TUI-FIX-07 (usabilidade geral inchada) em 3 sprints filhas. Herda Fases 2 e 3 do pai.
**Modelo obrigatório:** claude-opus-4-7 (sem subagentes)

---

## Contexto

> ADRs: 001, 004, 005, 006, 010, 013, 014, 020, 024 (`print` só em cli.py/agent/output.py). 34 tools, 47 commands, 10 services. TUI-FIX-07A CONCLUIDA. TUI-FIX-07C próxima (/memory, /paste, /tools, /recall).

**Escopo:** não tocar banner (UX-LAYOUT-01A) nem toolbar (UX-LAYOUT-01B). Foco: `render_user_input` (paste), `cmd_help` (categorizado), keybind Ctrl+O.

---

## Problema

1. **Paste longo estufa eco.** Colar 10+ linhas enche a tela em cada turno.
2. **`/help` despeja 47 comandos.** Ruim para uso diário; falta lista curta.
3. **Sem atalho de expand.** Se colapsou, como conferir? Falta Ctrl+O.

---

## Solução

- `render_user_input(text, console_width=80, expanded=False)`: se `len(splitlines()) > 8` e não `expanded`, mostrar primeira linha + `... [N linhas ocultas -- Ctrl+O para expandir]`.
- `cmd_help`: `args == "all"` devolve lista completa do `registry.list_all()`; caso contrário, 10 curadas + hint `Digite /help all`.
- `cli.py`: keybind Ctrl+O re-renderiza último input capturado em `_last_user_input`.

---

## Arquivos alvo (paths absolutos)

### `/home/andrefarias/Desenvolvimento/Nyx-Code/nyx/agent/output.py`

```python
USER_INPUT_COLLAPSE_LINES = 8

def render_user_input(text: str, console_width: int = 80, expanded: bool = False) -> None:
    lines = text.splitlines() or [text]
    if not expanded and len(lines) > USER_INPUT_COLLAPSE_LINES:
        hidden = len(lines) - 1
        display = f"{lines[0]}\n... [{hidden} linhas ocultas -- Ctrl+O para expandir]"
    else:
        display = text
    # ... renderização ╭─ você ─╮ consome `display`
```

Constante `USER_INPUT_COLLAPSE_LINES = 8`; parâmetro `expanded` default `False`; colapso substitui `display`, mantém renderização existente.

### `/home/andrefarias/Desenvolvimento/Nyx-Code/nyx/agent/commands/core.py`

```python
_HELP_TOP = [
    ("/help", "esta ajuda (/help all para lista completa)"),
    ("/status", "estado da sessão"),
    ("/tools", "tools disponíveis"),
    ("/plan", "iniciar plano"),
    ("/commit", "commit no git"),
    ("/memory", "memórias persistentes"),
    ("/paste", "imagens/pastes da sessão"),
    ("/config", "configuração efetiva"),
    ("/clear", "limpar sessão"),
    ("/quit", "sair (ou Ctrl+D)"),
]


def cmd_help(args, root):
    from nyx.agent.commands import registry
    if args.strip() == "all":
        todos = registry.list_all()
        linhas = [f"  /{c.name:<18}{c.description}" for c in todos]
        return "Comandos disponíveis:\n" + "\n".join(linhas)
    linhas = [f"  {nome:<10}{desc}" for nome, desc in _HELP_TOP]
    total = len(registry.list_all())
    return "Comandos principais:\n" + "\n".join(linhas) + f"\n\nDigite /help all para ver todos ({total})."
```

Lista curta com 10 entradas; lista completa sempre derivada do registry (nunca hardcoded); contador dinâmico.

### `/home/andrefarias/Desenvolvimento/Nyx-Code/nyx/cli.py`

```python
_last_user_input: str = ""

@kb.add("c-o")
def _expand_last_input(event):
    from nyx.agent.output import render_user_input
    if _last_user_input:
        render_user_input(_last_user_input, expanded=True)

# no loop de turnos, após ler user_input do prompt:
_last_user_input = user_input
render_user_input(user_input)  # colapsa se > 8 linhas
# texto completo (user_input) segue para o agente normalmente
```

Estado `_last_user_input` na sessão; keybind Ctrl+O re-renderiza com `expanded=True`; texto completo preservado no histórico enviado ao modelo.

---

## Diff esperado (resumo)

```
+ 0 arquivos criados
~ 3 arquivos modificados
- 0 arquivos removidos
+ ~55 linhas líquidas
```

---

## Comandos de verificação

```bash
cd /home/andrefarias/Desenvolvimento/Nyx-Code

python -m ruff check nyx/cli.py nyx/agent/output.py nyx/agent/commands/core.py

# Colapso ativa em > 8 linhas
python -c "
from nyx.agent.output import render_user_input
import io, sys
orig = sys.stdout; sys.stdout = io.StringIO()
render_user_input('\n'.join(f'linha {i}' for i in range(20)), console_width=100)
out = sys.stdout.getvalue(); sys.stdout = orig
assert 'linhas ocultas' in out and 'Ctrl+O' in out
print('colapso OK')
"

# Paste <= 8 linhas não colapsa
python -c "
from nyx.agent.output import render_user_input
import io, sys
orig = sys.stdout; sys.stdout = io.StringIO()
render_user_input('\n'.join(f'linha {i}' for i in range(5)), console_width=100)
out = sys.stdout.getvalue(); sys.stdout = orig
assert 'linhas ocultas' not in out
print('paste curto OK')
"

# /help categorizado
python -c "
from nyx.agent.commands.core import cmd_help
curto = cmd_help('', None); longo = cmd_help('all', None)
assert 'principais' in curto and len(longo.splitlines()) > len(curto.splitlines())
print('help OK')
"

./run.sh --gauntlet --only interface
./run.sh --smoke

# Manual: ./run.sh; colar 20 linhas (colapsa); Ctrl+O (expande); /help e /help all.
```

---

## Critério binário de aceite (IA executora)

- [ ] `render_user_input` colapsa paste > 8 linhas com hint `Ctrl+O para expandir`
- [ ] Paste <= 8 linhas renderiza sem colapso
- [ ] Ctrl+O registrado e funcional no `PromptSession`
- [ ] `/help` mostra 10 comandos; `/help all` mostra os 47 via registry
- [ ] Texto completo do paste continua no histórico (verificar em log/debug)
- [ ] Completer de slash commands continua funcional
- [ ] Gauntlet `--only interface` passa 100%
- [ ] `./run.sh --smoke` continua PASS
- [ ] `ruff` não reclama
- [ ] Nenhuma violação de `forbidden[]`
- [ ] `SPRINT_ORDER_MASTER.md` atualizado com hash
- [ ] Sprint movida para `concluidos/`
- [ ] Commit atômico criado

---

## Guardrails anti-engodo

Não marcar CONCLUIDA se `/help all` for lista hardcoded; se o colapso truncar o texto enviado ao modelo; se Ctrl+O for stub; se o limiar for diferente de 8 sem justificativa; se mexer em banner/toolbar. Reportar `[SPRINT TUI-FIX-07B] BLOQUEADA: <motivo>` em falha.

---

## Gambiarras específicas

1. **Lista completa hardcoded.** `/help all` devolver string fixa com 47 comandos copiados à mão. Proibido — usar `registry.list_all()`.
2. **Colapso destrutivo.** Truncar `user_input` antes de enviar ao modelo. Proibido — o colapso é apenas visual.
3. **Ctrl+O stub.** Keybind registrado sem handler real. Proibido — meta-regra #4 (feature flag falsa).
4. **Limiar dinâmico oculto.** Ex.: `if len(lines) > int(os.environ.get("NYX_COLLAPSE", 8))`. Só adicionar env var se ADR permitir.
5. **Tocar em banner/toolbar.** Fora de escopo — se precisar, criar sprint nova.
6. **Completer quebrado.** Ao mexer em `cmd_help`, verificar que o completer de `/` no REPL continua listando os 47 comandos.

---

## Proof-of-work obrigatório (4 passos)

```bash
# PASSO 1 — ANTES
bash scripts/sprint_invariants.sh > /tmp/inv_before.txt 2>&1
FAIL_BEFORE=$(grep -c "^\[FAIL\]" /tmp/inv_before.txt)

# PASSO 2 — implementação

# PASSO 3 — DEPOIS
bash scripts/sprint_invariants.sh > /tmp/inv_after.txt 2>&1
FAIL_AFTER=$(grep -c "^\[FAIL\]" /tmp/inv_after.txt)

# PASSO 4 — regras binárias: FAIL_AFTER <= FAIL_BEFORE; diff colado
```

Colar `tail -10` de cada snapshot, `diff`, output literal dos 4 sanity checks (colapso, paste curto, help, Ctrl+O manual), gauntlet interface e `git show --stat HEAD`.

---

## Validação humana (checklist do usuário)

```bash
cd /home/andrefarias/Desenvolvimento/Nyx-Code
git log --oneline -1
git show --stat HEAD

./run.sh
# 1. Cole 20 linhas -- eco colapsado aparece.
# 2. Ctrl+O -- eco expandido.
# 3. /help -- lista curta (10).
# 4. /help all -- lista completa (47).
# 5. Ctrl+D para sair.

ls dev-journey/06-sprints/concluidos/SPRINT_TUI_FIX_07B.md
ls dev-journey/06-sprints/producao/SPRINT_TUI_FIX_07B.md  # NÃO deve existir
```

---

## Riscos

| Risco | Mitigação |
|-------|-----------|
| `registry.list_all()` pode não existir em versão atual | Verificar; se ausente, usar iteração equivalente sobre o registry; nunca hardcoded |
| Ctrl+O já usado por outra função (ex.: expand de tool output) | Grep em `cli.py` antes; se conflito, usar Ctrl+G ou abrir issue — não sobrescrever silenciosamente |
| Paste com 8 linhas exatas: casos de borda | Limiar é `> 8` (estritamente maior); 8 linhas renderiza inteiro |

---

*"O que é simples deve parecer simples, o que é complexo deve ser revelado." -- Blaise Pascal*
