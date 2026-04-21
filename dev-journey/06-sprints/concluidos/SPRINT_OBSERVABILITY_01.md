# SPRINT OBSERVABILITY-01 — Callbacks de observação no AgentLoop, /debug session, /replay e log rotacionado

## 0. SPEC (machine-readable)

```yaml
sprint:
  id: OBSERVABILITY-01
  title: "Wirear callbacks on_compaction e on_model_state no AgentLoop, adicionar /debug session, /replay e log rotacionado"
  onda: 22
  bloco: 2.9
  prioridade: ALTA
  tipo: Feature
  dependencias: [VALIDATE-ONDA-21]
  desbloqueia: [UX-LAYOUT-02]

  touches:
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/agent/loop/_core.py
      reason: "Declarar slots on_compaction e on_model_state no construtor e disparar nos pontos certos do ciclo"
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/cli.py
      reason: "Registrar callbacks stub (toolbar não renderiza ainda — fica para UX-LAYOUT-02)"
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/agent/commands/debug_cmds.py
      reason: "Adicionar cmd_debug_session com métricas estruturadas da sessão corrente"
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/agent/commands/session.py
      reason: "Adicionar cmd_replay que lê logs/sessions/<id>.json e re-renderiza em modo read-only"
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/agent/services/logging_service.py
      reason: "Adicionar RotatingFileHandler para ~/.nyx/logs/nyx.log com limite de 10MB"
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/agent/commands/__init__.py
      reason: "Registrar /debug session e /replay se ainda não estiverem na lista de commands"

  creates: []
  removes: []

  n_to_n_pairs:
    - descricao: "Assinatura dos callbacks on_compaction e on_model_state aparece no _core.py e em quem consome (cli.py); atualizar ambos"
      paths:
        - /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/agent/loop/_core.py
        - /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/cli.py

  forbidden:
    - "Renderizar visualmente a compactação aqui — fica para UX-LAYOUT-02; esta sprint só wirea o callback"
    - "Usar print() em loop/_core.py, services/logging_service.py, commands/ — usar logger"
    - "Silenciar exceção ao abrir logs/sessions/<id>.json — error handling explícito"
    - "Path absoluto hardcoded — usar Path.home() / Path(__file__).parent"
    - "Adicionar emoji ou menção a IA"
    - "Criar test_*.py solto — tudo no Gauntlet (ADR-014)"

  tests:
    - cmd: "./run.sh --gauntlet --only rapido"
      timeout: 300
      deve_passar: "100%"
    - cmd: "manual: ./run.sh, conversar por 3 turnos, rodar '/debug session' e verificar saída com iterações/tokens/duração por tool/compactações"
      timeout: 60
    - cmd: "manual: ./run.sh, Ctrl+D, depois './run.sh' novamente e rodar '/replay <id>' apontando para um arquivo em logs/sessions/"
      timeout: 60
    - cmd: "ls -lh ~/.nyx/logs/nyx.log"
      timeout: 10
      deve_passar: "arquivo existe e tem tamanho > 0 após sessão"

  acceptance_criteria:
    - "on_compaction é chamado com (level, tokens_removed, pct_before, pct_after) em toda compactação"
    - "on_model_state é chamado com 'cold', 'warming' e 'warm' nas transições correspondentes"
    - "/debug session retorna string não-vazia com métricas reais (iterações, tokens/iter, duração por tool, contagem de compactações)"
    - "/replay <session_id> lê logs/sessions/<id>.json e re-renderiza turnos em modo read-only (sem chamar modelo)"
    - "~/.nyx/logs/nyx.log existe, rotaciona a 10MB, mantém N backups"
    - "Gauntlet --only rapido 100%"
    - "Acentuação PT-BR correta"
    - "Zero print() novo fora de cli.py/output.py"
```

---

**Status:** CONCLUIDA (commit 691f0c5)
**Data criação:** 2026-04-19
**Modelo obrigatório:** claude-opus-4-7 (sem subagentes)

---

## Contexto do projeto (snapshot — não referência)

> **ADRs relevantes:**
> - ADR-001 Local First.
> - ADR-013 Integração Obrigatória — nada solto, tudo no registry.
> - ADR-014 Testes via Gauntlet — sem test_*.py fora do Gauntlet.
> - ADR-015 Documentação para continuidade — logging_service já unificado.
> - ADR-020 Testes via run.sh.
> - ADR-024 Render Layer — print() permitido apenas em cli.py e output.py.
>
> **Estado do sistema na data da sprint:**
> - Python 3.10+, Ollama 11435, proxy 11436, 34 tools, 47 comandos.
> - `on_compaction` e `on_model_state` **não existem** em `nyx/agent/loop/_core.py`.
> - Sessões são logadas em `logs/sessions/*.json` (estrutura presumida a confirmar no primeiro passo).
> - `logging_service` já existe e é canônico (sprint DEBT-03, commit 0ac665e).
> - UX-LAYOUT-02 está bloqueada porque assume que `on_compaction` existe.

---

## Problema

O AgentLoop roda sem expor sinais de eventos observáveis: não dá pra saber quando houve compactação de contexto, quando o modelo saiu de cold para warm, nem revisar uma sessão anterior sem re-executar tudo. Sem esses sinais:

- A TUI não consegue mostrar feedback visual de compactação (UX-LAYOUT-02 precisa).
- Debug de bug reportado pelo usuário exige reproduzir o cenário, gastando ciclos do modelo.
- Logs ficam em stdout sem persistência rotacionada; sessão longa some quando o terminal fecha.

### Sintoma observável

```bash
$ grep -rn "on_compaction\|on_model_state" nyx/agent/loop/
# (zero resultados)
```

Ninguém pode se plugar nesses eventos porque eles não existem.

```bash
$ ls ~/.nyx/logs/
# (diretório inexistente ou vazio, sem nyx.log)
```

---

## Solução proposta

1. Declarar os dois callbacks como slots opcionais no construtor do AgentLoop e disparar dentro dos pontos apropriados do ciclo.
2. Novo comando `/debug session` que imprime métricas estruturadas do estado da sessão corrente.
3. Novo comando `/replay <session_id>` que lê o JSON da sessão e re-renderiza em modo read-only (sem chamar o modelo).
4. RotatingFileHandler no logging_service para `~/.nyx/logs/nyx.log`, limite 10MB, 5 backups.

---

## Arquivos alvo (paths absolutos)

### `/home/andrefarias/Desenvolvimento/Nyx-Code/nyx/agent/loop/_core.py`

**Antes (trecho do construtor):**
```python
class AgentLoop:
    def __init__(
        self,
        registry,
        parser,
        budget,
        permissions,
        ...
    ):
        ...
```

**Depois:**
```python
class AgentLoop:
    def __init__(
        self,
        registry,
        parser,
        budget,
        permissions,
        ...
        on_compaction: Optional[Callable[[int, int, float, float], None]] = None,
        on_model_state: Optional[Callable[[str], None]] = None,
    ):
        ...
        self._on_compaction = on_compaction
        self._on_model_state = on_model_state
```

**Pontos de disparo:**
- `on_compaction(level, tokens_removed, pct_before, pct_after)` chamado imediatamente após ContextBudget aplicar compactação (procurar ponto onde hoje só se ajusta o estado interno).
- `on_model_state(state)` chamado em três lugares: antes da primeira requisição do ciclo (`"warming"`), após resposta bem-sucedida (`"warm"`), no boot antes de qualquer request (`"cold"`).

Todos os disparos protegidos por `if self._on_compaction is not None: self._on_compaction(...)` — callbacks são opcionais.

### `/home/andrefarias/Desenvolvimento/Nyx-Code/nyx/cli.py`

Registrar callbacks stub no instanciamento do AgentLoop. Stub aqui significa: função que apenas chama `logger.debug(...)`. Renderização visual fica para UX-LAYOUT-02.

**Depois:**
```python
def _on_compaction_stub(level, removed, pct_before, pct_after):
    logger.debug(
        "compaction level=%d removed=%d before=%.2f after=%.2f",
        level, removed, pct_before, pct_after,
    )

def _on_model_state_stub(state: str):
    logger.debug("model state -> %s", state)

loop = AgentLoop(
    registry=...,
    ...,
    on_compaction=_on_compaction_stub,
    on_model_state=_on_model_state_stub,
)
```

### `/home/andrefarias/Desenvolvimento/Nyx-Code/nyx/agent/commands/debug_cmds.py`

Adicionar função nova:

```python
def cmd_debug_session(args: list[str], loop: "AgentLoop") -> str:
    state = loop.session_state()
    lines = [
        "sessão atual:",
        f"  iterações: {state['iter']}",
        f"  tokens acumulados: {state['tokens_total']}",
        f"  compactações: {state['compactions']}",
        "tools (duração média em ms):",
    ]
    for tool_name, durations in state["tool_durations"].items():
        avg = sum(durations) / len(durations) if durations else 0.0
        lines.append(f"  {tool_name}: {avg:.1f}ms (chamadas: {len(durations)})")
    return "\n".join(lines)
```

`loop.session_state()` precisa ser método novo em `_core.py` que retorna dict com as métricas acima. Dados já existem em contadores internos; só precisam ser expostos.

### `/home/andrefarias/Desenvolvimento/Nyx-Code/nyx/agent/commands/session.py`

Adicionar função nova:

```python
def cmd_replay(args: list[str], loop: "AgentLoop") -> str:
    if not args:
        return "uso: /replay <session_id>"
    session_id = args[0]
    session_path = Path.home() / ".nyx" / "sessions" / f"{session_id}.json"
    if not session_path.exists():
        session_path = Path("logs/sessions") / f"{session_id}.json"
    if not session_path.exists():
        return f"sessão não encontrada: {session_id}"
    try:
        data = json.loads(session_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        logger.error("replay falhou ao parsear %s: %s", session_path, exc)
        return f"sessão corrompida: {exc}"
    lines = [f"[replay read-only de {session_id}]"]
    for turn in data.get("turns", []):
        lines.append(f"> {turn.get('user', '')}")
        lines.append(f"{turn.get('assistant', '')}")
    return "\n".join(lines)
```

### `/home/andrefarias/Desenvolvimento/Nyx-Code/nyx/agent/services/logging_service.py`

Adicionar handler rotacionado. O get_logger já centraliza — adicionar no setup inicial:

```python
from logging.handlers import RotatingFileHandler

def _ensure_file_handler(logger_root):
    log_dir = Path.home() / ".nyx" / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / "nyx.log"
    handler = RotatingFileHandler(
        log_file,
        maxBytes=10 * 1024 * 1024,
        backupCount=5,
        encoding="utf-8",
    )
    handler.setFormatter(logging.Formatter(
        "%(asctime)s %(levelname)s [%(name)s] %(message)s"
    ))
    logger_root.addHandler(handler)
```

Chamar `_ensure_file_handler` apenas uma vez no bootstrap do logging_service (guardar flag de idempotência).

### `/home/andrefarias/Desenvolvimento/Nyx-Code/nyx/agent/commands/__init__.py`

Registrar os dois comandos novos na estrutura `COMMANDS = {...}` ou `register_command(...)` conforme o padrão existente.

---

## Diff esperado

```
~ 6 arquivos modificados
+ 0 arquivos criados
- 0 arquivos removidos
+ ~160 linhas líquidas
```

---

## Comandos de verificação

```bash
# PASSO 1 — snapshot ANTES
bash scripts/sprint_invariants.sh > /tmp/inv_before.txt 2>&1

# PASSO 2 — implementar

# PASSO 3 — smoke
./run.sh --smoke       # esperado: boot ok

# PASSO 4 — sessão real
./run.sh
# REPL:
# > liste os arquivos em nyx/agent/
# > explique o que a tool list_files faz
# > /debug session
# saída esperada: bloco estruturado com iterações, tokens, compactações, tools
# Ctrl+D

# PASSO 5 — log rotacionado
ls -lh ~/.nyx/logs/nyx.log   # esperado: arquivo existe, tamanho > 0

# PASSO 6 — replay
ls logs/sessions/ | head -1
./run.sh
# > /replay <id-da-sessão-anterior>
# saída esperada: bloco "[replay read-only de ...]" + turnos
# Ctrl+D

# PASSO 7 — gauntlet
./run.sh --gauntlet --only rapido

# PASSO 8 — snapshot DEPOIS
bash scripts/sprint_invariants.sh > /tmp/inv_after.txt 2>&1
diff /tmp/inv_before.txt /tmp/inv_after.txt
```

---

## Critério binário de aceite

- [ ] `grep -n "on_compaction\|on_model_state" nyx/agent/loop/_core.py` mostra declaração + pontos de disparo
- [ ] `/debug session` retorna string não-vazia com ao menos 3 linhas de métricas
- [ ] `/replay <id>` lê arquivo e renderiza turnos; erro gracioso se id não existe
- [ ] `~/.nyx/logs/nyx.log` existe após 1 sessão, rotaciona em 10MB
- [ ] Gauntlet `--only rapido` 100%
- [ ] FAIL_AFTER <= FAIL_BEFORE
- [ ] Nenhum print() novo fora de cli.py/output.py
- [ ] Commit `feat: callbacks observacionais no AgentLoop e comandos /debug session, /replay`
- [ ] Sprint movida para concluidos/

---

## Guardrails anti-engodo

- Declarar callback wireado sem ele ser chamado de fato: violação. Precisa de evidência nos logs (`logger.debug` registra a chamada).
- Fazer `/debug session` retornar string hardcoded "iterações: 0, tokens: 0" sem puxar do estado real: violação.
- Renderizar compactação visualmente aqui "já que eu tava mexendo": violação do escopo — vai para UX-LAYOUT-02.
- `/replay` que chama o modelo em vez de ler o JSON: violação — é read-only.
- Log file em path absoluto hardcoded (`/home/andrefarias/...`) em vez de `Path.home()`: violação.

---

## Gambiarras específicas desta sprint

1. **Callback declarado mas nunca chamado.** Slot existe no construtor mas nenhum ponto do ciclo dispara. Proibido — a IA deve colar o stdout do `logger.debug` provando chamada.
2. **`session_state()` devolve dict vazio.** Método existe mas retorna `{}`. Proibido — `/debug session` precisa mostrar números reais.
3. **`/replay` delega para o modelo.** Re-executar em vez de só renderizar. Proibido — é read-only, premissa é economizar ciclos.
4. **RotatingFileHandler adicionado múltiplas vezes.** Sem flag de idempotência, cada import duplica o handler. Proibido — usar guarda (`hasattr(logger_root, "_nyx_file_handler_setup")`).
5. **Path do log em constante hardcoded.** Proibido — usar `Path.home() / ".nyx" / "logs"`.
6. **print() usado para "debug rápido" em loop/_core.py.** Proibido — ADR-024 restringe print a cli.py e output.py.
7. **`except Exception: pass` em volta de `json.loads`.** Proibido — logger.error + retorno de mensagem clara.
8. **Backup count 0 no RotatingFileHandler.** Efetivamente desabilita rotação. Proibido — mínimo 5.

Ver também `dev-journey/08-templates/GAMBIARRAS_POR_SPRINT.md` seção OBSERVABILITY-01.

---

## Proof-of-work obrigatório

Formato padrão (ver SPRINT_TEMPLATE_V2.md seção "Proof-of-work"). Incluir obrigatoriamente:

- `cat /tmp/inv_before.txt | tail -10`, `cat /tmp/inv_after.txt | tail -10`, diff.
- Trecho do `~/.nyx/logs/nyx.log` mostrando as linhas `compaction level=...` e `model state -> warming|warm`.
- Saída literal de `/debug session` após uma sessão com pelo menos 3 turnos.
- Saída literal de `/replay <id>` com turnos renderizados.
- `./run.sh --gauntlet --only rapido` final com 100%.
- `git show --stat HEAD`.

---

## Validação humana (checklist do usuário)

```bash
cd /home/andrefarias/Desenvolvimento/Nyx-Code
./run.sh
# REPL: conversar 3 turnos
# > /debug session
# saída: bloco com iterações, tokens, compactações, tools
# Ctrl+D

# conferir log
ls -lh ~/.nyx/logs/nyx.log
tail -20 ~/.nyx/logs/nyx.log | grep -E "compaction|model state"

# replay de sessão
./run.sh
# > /replay <id-da-sessão-anterior listado em logs/sessions/>
# saída: turnos antigos renderizados, sem chamada de modelo
# Ctrl+D
```

---

## Riscos

| Risco | Mitigação |
|-------|-----------|
| Estrutura de `logs/sessions/<id>.json` diferente do presumido | Primeiro passo: inspecionar um arquivo real e ajustar parser em cmd_replay antes de codar |
| RotatingFileHandler duplicado em cada import | Guarda de idempotência via flag no logger root |
| Callbacks disparados em excesso degradam performance | Disparos apenas em transições de estado; perfil no gauntlet para validar |
| `/replay` quebra em sessão corrompida | `json.JSONDecodeError` capturado explicitamente com logger.error + mensagem amigável |
| UX-LAYOUT-02 depende da assinatura exata dos callbacks | Assinatura definida aqui é contrato; qualquer mudança futura exige sprint nova |
| Diretório `~/.nyx/logs/` inexistente em primeira execução | `mkdir(parents=True, exist_ok=True)` no handler setup |

---

*"Quem não mede, não conhece; quem não conhece, não controla." -- Peter Drucker
