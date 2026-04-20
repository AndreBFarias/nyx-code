# SPRINT TUI-FIX-07C — Comandos /memory, /paste, /tools, /recall

## 0. SPEC (machine-readable)

```yaml
sprint:
  id: TUI-FIX-07C
  title: "Comandos /memory (listar e mostrar), /paste (imagens da sessão), /tools (34 registradas), /recall (busca textual em memória)"
  onda: 22
  bloco: 5b
  prioridade: BAIXA
  tipo: Feature
  dependencias: [TUI-FIX-07B, TUI-FIX-05]
  desbloqueia: []

  touches:
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/agent/commands/system.py
      reason: "Adicionar cmd_memory (lista + show <arquivo>) e cmd_paste (lista imagens coladas na sessão)"
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/agent/commands/code.py
      reason: "Adicionar cmd_tools (lista das 34 tools registradas) e cmd_recall (busca textual em memória). Se já existir cmd_tools, apenas ampliar"

  creates: []
  removes: []

  n_to_n_pairs:
    - descricao: "cmd_memory consome NyxMemory.index/read — mesma fonte do indicador de boot introduzido em TUI-FIX-07A"
      paths:
        - /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/agent/commands/system.py
        - /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/agent/memory.py
        - /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/cli.py
    - descricao: "cmd_paste consome session.image_map (ou estrutura equivalente) criada por TUI-FIX-05"
      paths:
        - /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/agent/commands/system.py
    - descricao: "cmd_tools lista nomes e descrições a partir do ToolRegistry — mesma fonte do /help all em TUI-FIX-07B"
      paths:
        - /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/agent/commands/code.py

  forbidden:
    - "Adicionar emoji"
    - "Usar 'print()' em modules novos (permitido apenas em cli.py e agent/output.py — ADR-024)"
    - "Menção a Claude/GPT/Anthropic"
    - "Duplicar lista de tools (meta-regra #1: fonte única no ToolRegistry)"
    - "Criar cmd_tools se já existir — apenas ampliar; descobrir com grep"
    - "Ler paths absolutos hardcoded; usar Path.home() ou settings"
    - "Retornar string vazia / None em /memory quando houver entradas (stub como implementação)"

  tests:
    - cmd: "./run.sh --gauntlet --only interface"
      timeout: 300
      deve_passar: true
    - cmd: "./run.sh --smoke"
      timeout: 60
      deve_passar: true

  acceptance_criteria:
    - "/memory lista entradas com formato '- <arquivo>: <reason>' (ou linha 'Sem memórias gravadas.' se vazio)"
    - "/memory show <arquivo> imprime conteúdo do arquivo; erro objetivo se não existir"
    - "/paste lista imagens coladas na sessão com '#N path'; mensagem clara se vazio"
    - "/tools lista as 34 tools com nome + descrição curta, derivado do ToolRegistry"
    - "/recall <termo> busca textualmente em todas as memórias (case-insensitive) e retorna arquivo + linha matching"
    - "/recall sem argumento retorna erro claro 'uso: /recall <termo>'"
    - "Todos os 4 comandos registrados via @nyx_command (ADR-013 Integração Obrigatória)"
    - "Gauntlet fase interface passa 100%"
    - "./run.sh --smoke continua PASS"
    - "Acentuação PT-BR correta em tudo novo"
```

---

# Sprint TUI-FIX-07C — /memory, /paste, /tools, /recall

**Status:** PENDENTE
**Data criação:** 2026-04-19
**Origem:** split de TUI-FIX-07 em 3 sprints. Herda Fases 5 e 6 do pai + expansão para `/tools` e `/recall`.
**Modelo obrigatório:** claude-opus-4-7 (sem subagentes)

---

## Contexto

> ADRs: 001, 004, 005, 006, 010, 013 (tudo via `@nyx_command`), 014, 020, 024. 34 tools, 47 commands, 10 services. TUI-FIX-07B CONCLUIDA. TUI-FIX-05 CONCLUIDA — confirmar nome exato da estrutura de imagens (`session.image_map` assumido) antes de implementar.

---

## Problema

1. Memória invisível após boot (TUI-FIX-07A mostrou indicador, faltam comandos).
2. Sem lista de imagens coladas (pós TUI-FIX-05).
3. Tools só aparecem via chamada do modelo — falta descoberta.
4. Memórias longas precisam busca textual.

---

## Solução

Quatro comandos via `@nyx_command`:

- `/memory` lista entradas; `/memory show <arquivo>` imprime conteúdo.
- `/paste` lista imagens da sessão.
- `/tools` lista tools do `ToolRegistry` (ampliar se já existir).
- `/recall <termo>` busca textual case-insensitive em memórias.

**Passo 0:** `grep -rn 'name="tools"\|name="recall"' nyx/agent/commands/` — se existirem, ampliar; se não, criar.

---

## Arquivos alvo (paths absolutos)

### `/home/andrefarias/Desenvolvimento/Nyx-Code/nyx/agent/commands/system.py`

```python
from nyx.agent.commands import nyx_command
from nyx.agent.memory import NyxMemory


@nyx_command(name="memory", description="Lista memórias (/memory show <arquivo>)")
def cmd_memory(args: str, root) -> str:
    m = NyxMemory(root)
    parts = args.strip().split(maxsplit=1)
    if parts and parts[0] == "show" and len(parts) == 2:
        try:
            return m.read(parts[1])
        except FileNotFoundError:
            return f"memória '{parts[1]}' não encontrada."
        except Exception as exc:
            return f"erro ao ler memória: {exc}"
    entries = m.index()
    if not entries:
        return "Sem memórias gravadas. Use write_memory para criar."
    return "\n".join(f"- {e['file']}: {e.get('reason', '')}" for e in entries)


@nyx_command(name="paste", description="Lista imagens coladas nesta sessão")
def cmd_paste(args: str, root) -> str:
    from nyx.agent.session import get_session
    sess = get_session()
    imgs = getattr(sess, "image_map", None) or {}
    if not imgs:
        return "Nenhuma imagem colada nesta sessão."
    return "\n".join(f"#{i+1} {path}" for i, (_k, path) in enumerate(imgs.items()))
```

Dois comandos novos com error handling explícito e `getattr` defensivo em `session.image_map`.

### `/home/andrefarias/Desenvolvimento/Nyx-Code/nyx/agent/commands/code.py`

Se `cmd_tools`/`cmd_recall` já existirem no repo, apenas ampliar. Se ausentes:

```python
from nyx.agent.commands import nyx_command


@nyx_command(name="tools", description="Lista tools registradas")
def cmd_tools(args: str, root) -> str:
    from nyx.agent.tools import registry as tool_registry
    tools = tool_registry.list_all()
    linhas = [f"  {t.name:<22}{t.description}" for t in tools]
    return f"Tools disponíveis ({len(tools)}):\n" + "\n".join(linhas)


@nyx_command(name="recall", description="Busca textual nas memórias (/recall <termo>)")
def cmd_recall(args: str, root) -> str:
    termo = args.strip()
    if not termo:
        return "uso: /recall <termo>"
    from nyx.agent.memory import NyxMemory
    m = NyxMemory(root)
    termo_lower = termo.lower()
    resultados: list[str] = []
    for entry in m.index():
        fname = entry["file"]
        try:
            conteudo = m.read(fname)
        except Exception as exc:
            resultados.append(f"  [erro ao ler {fname}: {exc}]")
            continue
        for n, linha in enumerate(conteudo.splitlines(), start=1):
            if termo_lower in linha.lower():
                resultados.append(f"  {fname}:{n}: {linha.strip()}")
    if not resultados:
        return f"nenhuma ocorrência de '{termo}' nas memórias."
    return "\n".join(resultados)
```

Lista de tools sempre derivada do `ToolRegistry`; `/recall` itera via `NyxMemory.read`, nunca abre path arbitrário.

---

## Diff esperado (resumo)

```
+ 0 arquivos criados
~ 2 arquivos modificados
- 0 arquivos removidos
+ ~85 linhas líquidas
```

---

## Comandos de verificação (literais, copy-paste)

```bash
cd /home/andrefarias/Desenvolvimento/Nyx-Code

# 0. Verificar se cmd_tools e cmd_recall já existem (impacta decisão)
grep -rn "name=\"tools\"\|name=\"recall\"" nyx/agent/commands/

# 1. Validação estática
python -m ruff check nyx/agent/commands/

# 2. Sanity: comandos registrados
python -c "
from nyx.agent.commands import registry
nomes = {c.name for c in registry.list_all()}
for n in ('memory', 'paste', 'tools', 'recall'):
    assert n in nomes, f'{n} não registrado'
print('todos registrados')
"

# 3. Sanity: /memory vazio retorna mensagem clara
python -c "
from nyx.agent.commands.system import cmd_memory
out = cmd_memory('', '/tmp/nyx-empty-root')
assert 'memória' in out.lower() or 'Sem' in out
print('memory vazio OK:', out)
"

# 4. Sanity: /recall sem arg retorna uso
python -c "
from nyx.agent.commands.code import cmd_recall
out = cmd_recall('', '.')
assert 'uso' in out.lower()
print('recall vazio OK:', out)
"

# 5. Gauntlet
./run.sh --gauntlet --only interface

# 6. Smoke
./run.sh --smoke

# 7. Validação manual
./run.sh
# /memory -- listar
# /memory show <algum-arquivo> -- imprimir
# /paste -- listar (ou mensagem de vazio)
# /tools -- lista 34 tools
# /recall python -- buscar
```

---

## Critério binário de aceite (IA executora)

- [ ] `/memory` sem args lista entradas; `/memory show <arquivo>` imprime conteúdo
- [ ] `/paste` lista imagens ou mensagem de vazio
- [ ] `/tools` lista 34 tools derivadas do `ToolRegistry`
- [ ] `/recall <termo>` encontra matches; `/recall` sem arg retorna "uso: /recall <termo>"
- [ ] Todos registrados via `@nyx_command` (aparecem em `registry.list_all()`)
- [ ] `/help all` (vindo de TUI-FIX-07B) agora inclui os 4 novos automaticamente
- [ ] Gauntlet `--only interface` passa 100%
- [ ] `./run.sh --smoke` continua PASS
- [ ] `ruff` não reclama
- [ ] Nenhuma violação de `forbidden[]`
- [ ] `SPRINT_ORDER_MASTER.md` atualizado com hash
- [ ] Sprint movida para `concluidos/`
- [ ] Commit atômico criado

---

## Guardrails anti-engodo

Não marcar CONCLUIDA se `/tools` for duplicado; se a lista de tools for hardcoded; se `/memory show` retornar `None` em arquivo ausente; se houver `except Exception: pass`; se `/recall` abrir path fora de memória. Reportar `[SPRINT TUI-FIX-07C] BLOQUEADA: <motivo>` em falha.

---

## Gambiarras específicas

1. **Stub de retorno fixo.** `/paste` sempre retorna `"Nenhuma imagem"` mesmo quando há. Proibido — gambiarra #2 do catálogo global.
2. **Lista hardcoded de tools.** Em vez de ler do registry. Gambiarra #1 de "burlas estruturais".
3. **`/recall` abrindo paths absolutos.** Usar só `NyxMemory.read(fname)` com nomes derivados de `index()`; nunca `open("/etc/passwd")` etc.
4. **`/tools` duplicado.** Se já existe no código, apenas ampliar — nunca criar segundo decorator com mesmo nome.
5. **Silent except.** `/recall` fazendo `except: continue` sem log. Proibido — usar `logger.warning` explícito ou acrescentar ao output de erros.
6. **Ignorar dependência TUI-FIX-05.** `/paste` só faz sentido depois de TUI-FIX-05; confirmar que `session.image_map` ou estrutura equivalente existe antes. Se ausente, bloquear sprint e reportar.

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

# PASSO 4 — FAIL_AFTER <= FAIL_BEFORE; diff colado
```

Colar no relatório: `tail -10` de cada snapshot, `diff`, output literal dos 4 sanity checks, gauntlet interface, `git show --stat HEAD`.

---

## Validação humana (checklist do usuário)

```bash
cd /home/andrefarias/Desenvolvimento/Nyx-Code
git log --oneline -1
git show --stat HEAD

./run.sh
# /memory             -- lista ou "Sem memórias gravadas."
# /memory show <arq>  -- imprime conteúdo
# /paste              -- lista ou "Nenhuma imagem colada nesta sessão."
# /tools              -- lista as 34 tools
# /recall python      -- matches
# /recall             -- "uso: /recall <termo>"
# Ctrl+D

ls dev-journey/06-sprints/concluidos/SPRINT_TUI_FIX_07C.md
ls dev-journey/06-sprints/producao/SPRINT_TUI_FIX_07C.md  # NÃO deve existir
```

---

## Riscos

| Risco | Mitigação |
|-------|-----------|
| `session.image_map` com nome diferente (TUI-FIX-05 pode ter usado outra estrutura) | Grep antes; se diferente, adaptar import; nunca assumir |
| `/tools` já existente em outro módulo | Passo 0 do comando de verificação detecta; se sim, ampliar |
| `/recall` com padrão regex injetado pelo usuário | Usar comparação textual (`in`), não regex — evita ReDoS |
| Memórias muito grandes (> 1 MB) | `/recall` itera linha a linha; aceitável; sem paginação por ora |

---

*"Memória é a sentinela do espírito." -- William Shakespeare*
