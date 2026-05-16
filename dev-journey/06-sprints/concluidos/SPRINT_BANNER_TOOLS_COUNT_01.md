# SPRINT BANNER-TOOLS-COUNT-01 — Reconciliação da contagem de tools entre ToolRegistry runtime e documentação

## 0. SPEC (machine-readable)

```yaml
sprint:
  id: BANNER-TOOLS-COUNT-01
  title: "Investigar divergência ToolRegistry.tool_count=35 vs filesystem=28 e alinhar fonte única runtime"
  onda: 22
  bloco: 2.10 Higiene
  prioridade: MÉDIA
  tipo: Bugfix + Docs
  dependencias: [INVENTORY-SYNC-01]
  desbloqueia: []

  touches:
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/agent/tools/registry.py
      reason: "Entender como ToolRegistry monta os 35 tool_defs — pode ter subclasses automáticas, entidades dinâmicas, ou registro via entities/."
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/scripts/sync.py
      reason: "print_inventory() usa count filesystem (28); trocar para runtime (35 via ToolRegistry.tool_count). sync.py hoje contradiz o banner — precisa ser a fonte única."
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/dev-journey/08-templates/PROJECT_SNAPSHOT.md
      reason: "Tabela Contagens diz 28 tools com comando filesystem; trocar por comando runtime (python -c 'from nyx...') que retorna o mesmo número que o banner do REPL exibe."
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/GUIDE.md
      reason: "Resumo de contagens diz '28 tools'; sincronizar com runtime após reconciliação."
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/dev-journey/06-sprints/SPRINT_ORDER_MASTER.md
      reason: "Nota histórica do Inventário cita '28 tools'; atualizar para o valor runtime correto."
  creates: []
  removes: []

  n_to_n_pairs:
    - descricao: "Contagem de tools aparece em: ToolRegistry runtime, banner do REPL, _build_banner, toolbar, protocolo headless (pong/ping), scripts/sync.py print_inventory, PROJECT_SNAPSHOT, GUIDE.md, SPRINT_ORDER_MASTER. Todos precisam reportar o mesmo número."
      paths:
        - /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/agent/tools/registry.py
        - /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/cli.py
        - /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/agent/banner.py
        - /home/andrefarias/Desenvolvimento/Nyx-Code/scripts/sync.py
        - /home/andrefarias/Desenvolvimento/Nyx-Code/dev-journey/08-templates/PROJECT_SNAPSHOT.md
        - /home/andrefarias/Desenvolvimento/Nyx-Code/GUIDE.md
        - /home/andrefarias/Desenvolvimento/Nyx-Code/dev-journey/06-sprints/SPRINT_ORDER_MASTER.md

  forbidden:
    - "Forçar `len(tool_defs) == 28` modificando o registry para esconder tools dinâmicas (anti-scoping)"
    - "Inverter a correção adotando filesystem como fonte só porque 'o spec antigo dizia assim'"
    - "Adicionar emoji, menção a IA, print() fora de output.py/cli.py"
    - "Tocar em lógica de tool real sem justificativa — escopo é apenas reconciliação de contagem"
    - "Deixar contagem nova divergente em qualquer um dos 4 documentos"

  tests:
    - cmd: "python -c 'from nyx.agent.tools.registry import ToolRegistry; r=ToolRegistry(\"/tmp\"); print(r.tool_count, len(r.tool_defs))'"
      timeout: 10
      deve_passar: "dois números iguais, ambos correspondentes ao mostrado no banner do REPL"
    - cmd: "python scripts/sync.py"
      timeout: 30
      deve_passar: "linha 'inventario: tools=<N>, commands_unicos=52, services=9' onde N bate com ToolRegistry.tool_count"
    - cmd: "./run.sh --smoke"
      timeout: 60
      deve_passar: "boot ok"
    - cmd: "bash scripts/sprint_invariants.sh"
      timeout: 60
      deve_passar: "13/13 PASS"
    - cmd: "grep -E 'tools *= *[0-9]|^\\| Tools' GUIDE.md dev-journey/08-templates/PROJECT_SNAPSHOT.md dev-journey/06-sprints/SPRINT_ORDER_MASTER.md"
      timeout: 5
      deve_passar: "todos os 3 arquivos mostram o MESMO N"

  acceptance_criteria:
    - "Relatório curto no corpo do AUDIT (ou inline no commit) explica a origem das N-28 tools extras: subclasses automáticas de Tool, tools injetadas por ToolRegistry.__init__, ou arquivos em subpasta (entities/)"
    - "Fonte única canônica de contagem é runtime: python -c 'from nyx.agent.tools.registry import ToolRegistry; print(ToolRegistry(\".\").tool_count)'"
    - "PROJECT_SNAPSHOT.md §Contagens atualizado com comando runtime (não filesystem) ao lado de 'Tools'"
    - "scripts/sync.py print_inventory() usa ToolRegistry().tool_count (não find filesystem)"
    - "GUIDE.md §Estado atual resumo atualizado com N runtime"
    - "SPRINT_ORDER_MASTER.md nota histórica preserva a evolução: '34 → 30 → 28 (filesystem, INVENTORY-SYNC-01 incompleta) → N (runtime, BANNER-TOOLS-COUNT-01 definitivo)'"
    - "Banner do REPL (cli.py:360, agent.tools_count) continua mostrando o mesmo número que o sync report"
    - "Protocolo headless (cli.py:765,774) também reporta o mesmo N — n-para-n fechado"
    - "Gauntlet --only rapido passa"
    - "sprint_invariants.sh 13/13"
    - "Commit atômico 'fix(BANNER-TOOLS-COUNT-01): reconcilia contagem de tools via runtime ToolRegistry'"
```

---

**Status:** PENDENTE
**Data criação:** 2026-04-21
**Modelo obrigatório:** claude-opus-4-7 (sem subagentes)

---

## Contexto do projeto (snapshot — não referência)

> **ADRs relevantes:**
>
> - ADR-013 Integração Obrigatória: fonte de verdade para componentes registrados é o registry runtime, não o filesystem.
> - Meta-regra #1 (GUIDE.md global §9): Sincronização N-para-N — se um valor existe em N lugares, atualizar TODOS ou nenhum. INVENTORY-SYNC-01 concluiu parcialmente; esta sprint fecha a divergência.
> - Meta-regra #6: Evidência empírica > hipótese. Quando `ToolRegistry.tool_count` runtime diz 35 e `find` no filesystem diz 28, a verdade não é média — é escolher a autoridade semântica correta. Registry (runtime) governa o que o REPL mostra e o que as chamadas tools resolvem.
>
> **Estado do sistema (verificado 2026-04-21 pós TUI-CLEANUP-01):**
> - Commit atual: `3fd91e3` (refactor TUI-CLEANUP-01) / `4238526` (docs master).
> - Python 3.10+, qwen3:4b, Ollama 11435, proxy 11436.
> - **Divergência observada nesta sessão de orquestração:**
>   ```
>   $ python -c 'from nyx.agent.tools.registry import ToolRegistry; r=ToolRegistry("/tmp"); print(r.tool_count, len(r.tool_defs))'
>   35 35
>   $ find nyx/agent/tools -maxdepth 1 -name '*.py' ! -name '__init__.py' ! -name 'base.py' ! -name 'registry.py' | wc -l
>   28
>   $ ./run.sh (banner exibe): tools 35
>   $ python scripts/sync.py (imprime): inventario: tools=28, commands_unicos=52, services=9
>   ```
> - `INVENTORY-SYNC-01` (commits `3689081` + `7a5ea6a`) adotou 28 como fonte única, alinhando 3 docs + sync. Mas o **banner** e o **headless protocol** mostram 35, porque consomem o registry runtime. Resultado: sync.py CONTRADIZ a TUI que ele mesmo deveria validar.

---

## Problema

### Sintoma observável

Execução do REPL (screenshot da COMPLETER-SEPS-01):
```
  Nyx · v1.2.0                                                    100% offline
      modelo    qwen3:4b          tools    35
      projeto   Nyx-Code          visão    moondream (cold)
      rede      :11435 ollama  ·  :11436 proxy
```

Execução do sync:
```
$ python scripts/sync.py
inventario: tools=28, commands_unicos=52, services=9
  ...
  [OK]   Todas 28 tools registradas no registry
```

A linha `"Todas 28 tools registradas no registry"` é **literalmente falsa** (o registry tem 35). O validador empírico (meta-regra #6) invalida a alegação.

### Origem da divergência

Hipótese plausível (a investigar):
1. `ToolRegistry.__init__` registra algumas tools a mais do que existe como arquivo top-level — por exemplo via `entities/` (há diretório `nyx/themes/entities/`, talvez similar em tools) ou herança.
2. Alguns arquivos em `nyx/agent/tools/*.py` exportam MÚLTIPLAS classes Tool (1 arquivo → N registros).
3. `agent_tool.py` ou `task_manager.py` podem registrar sub-tools dinâmicas.

Verdade: **ToolRegistry runtime é a autoridade** — é o que o LLM recebe em `tool_defs` e o que o usuário vê no banner. Qualquer doc que contradiga isso está errado.

---

## Solução proposta

1. **Investigar e documentar** (no corpo do commit e/ou em `AUDIT_ERROR_MESSAGES_01.md` § novo) a origem exata das 7 tools extras. Listar os nomes via:
   ```bash
   python -c "from nyx.agent.tools.registry import ToolRegistry; r=ToolRegistry('/tmp'); [print(d['function']['name']) for d in r.tool_defs]"
   ```
   Comparar com `ls nyx/agent/tools/`. Identificar a fonte.
2. **Atualizar `scripts/sync.py::print_inventory()`** para usar runtime:
   ```python
   from nyx.agent.tools.registry import ToolRegistry
   tools_n = ToolRegistry(str(PROJECT_ROOT)).tool_count
   ```
   Preservar `commands_unicos` e `services` como estão (ambos já runtime-based ou equivalentes).
3. **Atualizar `PROJECT_SNAPSHOT.md`** trocando o comando `find nyx/agent/tools ...` pelo comando Python runtime. Atualizar o valor.
4. **Atualizar `GUIDE.md`** resumo com novo N.
5. **Atualizar `SPRINT_ORDER_MASTER.md`** nota histórica preservando evolução completa.
6. **Validar** que banner (cli.py:360) e headless (cli.py:765,774) reportam o mesmo N.

---

## Arquivos alvo (paths absolutos)

### `/home/andrefarias/Desenvolvimento/Nyx-Code/scripts/sync.py`

**Antes (trecho conceitual — ler o arquivo):**
```python
def _count_tools() -> int:
    # Conta arquivos em nyx/agent/tools/ excluindo __init__, base, registry
    tools_dir = PROJECT_ROOT / "nyx" / "agent" / "tools"
    return sum(
        1 for p in tools_dir.glob("*.py")
        if p.name not in ("__init__.py", "base.py", "registry.py")
    )
```

**Depois:**
```python
def _count_tools() -> int:
    # Fonte canônica runtime: ToolRegistry é o que o REPL consome.
    # Contagem filesystem (1 arquivo = 1 tool) subestima quando há
    # registro dinâmico, subclasses ou múltiplas tools por arquivo.
    from nyx.agent.tools.registry import ToolRegistry

    return ToolRegistry(str(PROJECT_ROOT)).tool_count
```

**Mudanças:** troca filesystem por runtime. Aceita que sync.py depende do pacote Nyx estar importável (já depende — roda outros `from nyx.themes import`, etc).

### `/home/andrefarias/Desenvolvimento/Nyx-Code/dev-journey/08-templates/PROJECT_SNAPSHOT.md`

**Antes (tabela §Contagens, linha aprox. 30):**
```markdown
| Tools no registry | 28 | `find nyx/agent/tools -maxdepth 1 -name '*.py' ! -name '__init__.py' ! -name 'base.py' ! -name 'registry.py' \| wc -l` |
```

**Depois:**
```markdown
| Tools no registry (runtime) | <N> | `python -c "from nyx.agent.tools.registry import ToolRegistry; print(ToolRegistry('.').tool_count)"` |
```

Onde `<N>` é o valor real obtido após a investigação (provavelmente 35; confirmar).

### `/home/andrefarias/Desenvolvimento/Nyx-Code/GUIDE.md`

**Antes:** linha de resumo cita "28 tools".
**Depois:** trocar por `<N> tools (runtime)` + data nova.

### `/home/andrefarias/Desenvolvimento/Nyx-Code/dev-journey/06-sprints/SPRINT_ORDER_MASTER.md`

**Antes:** nota histórica cita "realidade runtime 28/52/9".
**Depois:** preservar histórico completo:
```markdown
- **2026-04-21 (INVENTORY-SYNC-01):** contagens antes divergiam em 3 documentos (34/47/10 vs 30/54/9 vs filesystem 28/52/9). Normalizado apontando para PROJECT_SNAPSHOT.md como fonte única. Número de tools adotado (28) refletia filesystem, não registry runtime.
- **2026-04-21 (BANNER-TOOLS-COUNT-01):** reconciliado com autoridade runtime. `ToolRegistry.tool_count` retorna <N>; divergência de <N-28> explicada por <motivo descoberto>. Contagem canônica passa a ser runtime (comando Python) em vez de filesystem (find).
```

---

## Diff esperado (resumo)

```
+ 0 arquivos criados
~ 4 arquivos modificados (sync.py, PROJECT_SNAPSHOT.md, GUIDE.md, SPRINT_ORDER_MASTER.md)
- 0 arquivos removidos
+ ~20 linhas líquidas (maior parte docs)
```

---

## Comandos de verificação (literais, copy-paste)

```bash
cd /home/andrefarias/Desenvolvimento/Nyx-Code

# 1. Investigação inicial
python -c "from nyx.agent.tools.registry import ToolRegistry; r=ToolRegistry('.'); \
  print('tool_count:', r.tool_count); \
  print('names:'); [print('  -', d['function']['name']) for d in r.tool_defs]"

# 2. Comparar com filesystem para documentar origem das extras
ls nyx/agent/tools/*.py | grep -v -E '__init__|base\.py|registry\.py' | xargs -n1 basename | sort

# 3. Sync runtime (após edits)
python scripts/sync.py | head -5

# 4. Cross-check: banner e headless reportam o mesmo N
# banner: capturar linha 'tools' do banner via --smoke-extended (se existir) ou scrot
# headless:
echo '{"type":"ping"}' | ./run.sh --headless 2>&1 | grep -o '"tools":[0-9]*'

# 5. Regressão de invariantes
bash scripts/sprint_invariants.sh | tail -5

# 6. Gauntlet curto
./run.sh --gauntlet --only rapido
```

---

## Critério binário de aceite (IA executora)

- [ ] Investigação documentada: origem das <N-28> tools extras explicada no commit
- [ ] `scripts/sync.py::_count_tools()` usa ToolRegistry runtime, não filesystem
- [ ] `python scripts/sync.py` retorna `inventario: tools=<N>, commands_unicos=52, services=9` onde <N> = ToolRegistry.tool_count
- [ ] `PROJECT_SNAPSHOT.md` comando literal `python -c "from nyx.agent.tools.registry import ..."` ao lado do número
- [ ] Os 3 docs (CLAUDE, PROJECT_SNAPSHOT, ORDER_MASTER) concordam em <N>
- [ ] Banner do REPL (`agent.tools_count`) e headless pong/ping reportam o mesmo <N> do sync
- [ ] `sprint_invariants.sh` 13/13
- [ ] Gauntlet `--only rapido` passa
- [ ] Commit atômico `fix(BANNER-TOOLS-COUNT-01): reconcilia contagem de tools via runtime ToolRegistry`

---

## Guardrails anti-engodo (obrigatórios)

- Não "simplifique" removendo tools do registry para bater com 28 (anti-scoping destruidor).
- A investigação da origem das extras é **obrigatória** — não basta trocar o número. O commit precisa explicar o porquê.
- Se descobrir que tool dinâmica foi registrada por engano ou se há bug real no registry: **não fix inline** — registrar como sprint nova (ex: TOOL-REGISTRY-AUDIT-01) e manter o número runtime correto para esta sprint.
- Não altere lógica de registro. Só troca a fonte de count em sync/docs.
- `GUIDE.md` linhas 104, 110 (arquitetura ASCII) ainda citam "34 tools" e "47 commands" — atualizar também para o mesmo N (achado colateral herdado do validador da INVENTORY-SYNC-01).

---

## Catálogo de gambiarras proibidas

Ver `dev-journey/08-templates/GAMBIARRAS_POR_SPRINT.md` §"Catálogo Universal".

### Gambiarras específicas

1. **"Aproximar" o número** (ex: 35 ≈ "∼30"). Proibido — já caiu na armadilha em INVENTORY-SYNC-01.
2. **Deletar as tools extras** para fazer filesystem bater. Fonte de verdade é runtime.
3. **Manter duas fontes** ("filesystem=28 + runtime=35, use o que quiser"). Uma fonte, uma verdade.
4. **Pular a investigação da origem.** O commit deve explicar de onde vêm as extras. Caso contrário, a próxima auditoria repete o achado.
5. **Alterar GUIDE.md linhas 104/110 sem N-para-N em banner.py**. Banner é fonte runtime via `agent.tools_count` → não há N-para-N aqui, é só doc ASCII fora do escopo da sprint. Resolver **inline** como Edit-pronto no mesmo commit se o número é trivial, ou anotar.

---

## Proof-of-work obrigatório (4 passos)

```bash
bash scripts/sprint_invariants.sh > /tmp/inv_before.txt 2>&1
FAIL_BEFORE=$(grep -c '^\[FAIL\]' /tmp/inv_before.txt)

# --- investigação + edit sync.py + edits docs ---

bash scripts/sprint_invariants.sh > /tmp/inv_after.txt 2>&1
FAIL_AFTER=$(grep -c '^\[FAIL\]' /tmp/inv_after.txt)
diff /tmp/inv_before.txt /tmp/inv_after.txt
[ "$FAIL_AFTER" -le "$FAIL_BEFORE" ] || { echo REGRESSÃO; exit 1; }
```

Colar output literal de:
- Lista dos 35 nomes de tool (ou <N> se outro número).
- Lista dos arquivos filesystem.
- Explicação escrita da diferença (1-3 frases).
- `python scripts/sync.py | head -5`.
- Grep cross-doc confirmando concordância.

---

## Validação humana (checklist do usuário)

```bash
cd /home/andrefarias/Desenvolvimento/Nyx-Code

git log --oneline -1
git show --stat HEAD

python -c "from nyx.agent.tools.registry import ToolRegistry; print(ToolRegistry('.').tool_count)"
# esperado: <N> (número mostrado no banner e no sync.py)

python scripts/sync.py | head -3
# esperado: primeira linha "inventario: tools=<N>, ..."

./run.sh
# conferir banner: "tools  <N>"  (mesmo número)
```

---

## Riscos

| Risco | Mitigação |
|-------|-----------|
| Investigação revela bug real no ToolRegistry (tool duplicada, registro errado) | Não fix inline — abrir sprint nova TOOL-REGISTRY-AUDIT-01 e manter contagem runtime atual |
| `ToolRegistry("/tmp")` tem efeitos colaterais (cria diretório, abre conexão) | Passar `str(PROJECT_ROOT)` ou diretório seguro; verificar se init é lazy |
| `scripts/sync.py` perde robustez se `nyx.agent.tools.registry` falhar ao importar | Manter fallback filesystem com warning se import falhar, mas usar runtime como default |
| PROJECT_SNAPSHOT com dois comandos diferentes confunde leitores | Substituir inteiramente por runtime; filesystem fica só como nota histórica |
| Número final difere de 35 (registry mudou durante a sprint) | Executar no fim e usar o número final como autoridade |

---

*"Medir é o primeiro dever de quem quer conhecer." -- Galileu (adaptado)*
