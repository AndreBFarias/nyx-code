# SPRINT SESSION-RESUME-01 — Retomada de sessão via `/resume` com índice persistente

## 0. SPEC (machine-readable)

```yaml
sprint:
  id: SESSION-RESUME-01
  title: "Implementar /resume (sem arg = última sessão, com arg = id), índice ~/.nyx/sessions/index.json, e prompt 'Retomar?' no boot quando aplicável"
  onda: 22
  bloco: 6b
  prioridade: MÉDIA
  tipo: Feature
  dependencias: [CTX-02]
  desbloqueia: [ONBOARDING-01]

  touches:
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/agent/persistence.py
      reason: "Adicionar read/write atômico de ~/.nyx/sessions/index.json com schema versionado"
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/agent/commands/session.py
      reason: "Implementar cmd_resume com e sem argumento (AUDIT-FIX-05 moveu cmds de sessão para este arquivo)"
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/cli.py
      reason: "Adicionar prompt 'Retomar última sessão? [s/N]' no boot + respeitar --no-resume-prompt"
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/agent/loop/_core.py
      reason: "Método load_session_into_loop() que injeta messages sem reexecutar tools"
  creates:
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/scripts/migrate_sessions.py
      reason: "Migra sessões antigas para o novo schema com campo de índice (idempotente)"
  removes: []

  n_to_n_pairs:
    - descricao: "Schema version do índice aparece em persistence.py, migrate_sessions.py e cmd_resume"
      paths:
        - /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/agent/persistence.py
        - /home/andrefarias/Desenvolvimento/Nyx-Code/scripts/migrate_sessions.py
        - /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/agent/commands/session.py
    - descricao: "TTL de 48h para prompt de retomada; threshold de 3 turnos; ambos em settings.py + cli.py"
      paths:
        - /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/config/settings.py
        - /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/cli.py

  forbidden:
    - "Restaurar session sem validar schema (quebra silenciosa em formato antigo)"
    - "Perguntar 'Retomar?' sempre, ignorando TTL de 48h ou threshold de 3 turnos"
    - "Reexecutar tools na retomada (deve ser read-only replay)"
    - "Sobrescrever session file sem backup atômico (.tmp + os.replace)"
    - "Ler index.json a cada turno (só no boot e em /resume)"
    - "Adicionar emoji, print() fora de output.py/cli.py, menção a IA"
    - "Path absoluto hardcoded para ~/.nyx (usar Path.home() / '.nyx')"

  tests:
    - cmd: "./run.sh --gauntlet --only sessao"
      timeout: 300
      deve_passar: true
    - cmd: "./run.sh --gauntlet --only interface"
      timeout: 300
      deve_passar: "prompt de retomada não aparece quando --no-resume-prompt passado"

  acceptance_criteria:
    - "`/resume` sem argumento retoma a última sessão salva"
    - "`/resume <id>` retoma sessão específica"
    - "Turnos anteriores são mostrados colapsados: 'N turnos anteriores -- ver com /replay <id>'"
    - "Tools não são reexecutadas na retomada"
    - "Boot sem flag mostra prompt se última sessão <48h e >=3 turnos"
    - "Boot com --no-resume-prompt NUNCA mostra prompt"
    - "~/.nyx/sessions/index.json atualizado a cada save_session"
    - "Schema validado com jsonschema antes de restaurar"
    - "Acentuação PT-BR correta em mensagens novas"
    - "Zero mocks: teste usa sessões reais gravadas em tmpdir"
    - "Gauntlet `--only sessao` e `--only interface` passam 100%"
```

---

**Status:** PENDENTE
**Data criação:** 2026-04-19
**Modelo obrigatório:** claude-opus-4-7 (sem subagentes)

---

## Contexto do projeto (snapshot — não referência)

> **ADRs relevantes:**
> - ADR-001 Local First: sessões em `~/.nyx/sessions/`, nunca remoto.
> - ADR-010 Zero Mocks: testes contra sessões reais persistidas em tmpdir.
> - ADR-013 Integração Obrigatória: `cmd_resume` entra em `_registry.py` via `@nyx_command`.
> - ADR-014 Testes via Gauntlet.
> - ADR-015 Documentação para continuidade: schema do índice documentado em docstring.
>
> **Estado do sistema:**
> - Python 3.10+, 34 tools, 47 commands, 10 services.
> - `~/.nyx/` já contém: `memory/`, `sessions/`, `pastes/`, `image_index.json`.
> - Commands pós-split AUDIT-FIX-05: `core.py`, `system.py`, `session.py`, `code.py`, `git_cmds.py`, `debug_cmds.py`.
> - CTX-02 (memória persistente) é pré-requisito — garante que `session.messages` tem formato estável.
> - Desbloqueia ONBOARDING-01 que reutiliza a mesma infra de sessões indexadas.

---

## Problema

### Sintoma observável

Hoje, ao fechar o REPL com Ctrl+D e reabrir:
1. A sessão anterior é salva em `~/.nyx/sessions/<uuid>.json` mas fica órfã.
2. Não há forma de retomá-la sem saber o UUID exato.
3. Nenhuma sugestão no boot — usuário sempre começa do zero.
4. `/resume` não existe no catálogo de comandos.

Resultado: memória conversacional vira write-only. Quem quer continuar uma conversa interrompida precisa copiar/colar manualmente.

### Requisitos de UX

- Cenário A (happy path): "Terminei o dia, fechei. Amanhã reabro e quero voltar de onde parei." → boot pergunta e retomo com Enter.
- Cenário B (sessão antiga): "Faz uma semana que fechei aquela conversa sobre X." → não quero ser incomodado com prompt; se quiser, rodo `/resume list` + `/resume <id>`.
- Cenário C (conversa curta): "Abri há 2 minutos, disse uma coisa só, fechei." → não faz sentido perguntar pra retomar um turno único.

### Análise de causa

`nyx/agent/persistence.py` tem `save_session(session)` e `load_session(id)` mas nenhum índice. Cada sessão é um arquivo isolado sem metadados resumíveis. `cli.py` boot só inicializa loop vazio. Nenhum comando `/resume` registrado.

---

## Solução proposta

1. **Índice `~/.nyx/sessions/index.json`** — list de entradas `{id, timestamp_inicio, timestamp_fim, primeiro_prompt_truncado, n_turnos, projeto}`, atualizado a cada `save_session`.
2. **`/resume` comando** — dois modos: sem arg (última) e com arg (id ou prefixo).
3. **Prompt de boot** — consulta índice; se última sessão satisfaz TTL + threshold, pergunta `[s/N]`.
4. **Replay read-only** — ao restaurar, injeta `messages` no loop sem reexecutar tool calls; renderiza colapsado.
5. **Migration script** — varre sessões existentes, gera índice se ausente.
6. **Flags de CLI** — `--no-resume-prompt` suprime prompt, `--resume <id>` retoma direto.

---

## Arquivos alvo (paths absolutos)

### `/home/andrefarias/Desenvolvimento/Nyx-Code/nyx/agent/persistence.py`

**Antes (trecho):**
```python
def save_session(session: Session) -> Path:
    path = SESSIONS_DIR / f"{session.id}.json"
    path.write_text(json.dumps(session.to_dict()))
    return path
```

**Depois:**
```python
INDEX_SCHEMA_VERSION = 1
INDEX_PATH = SESSIONS_DIR / "index.json"

def save_session(session: Session) -> Path:
    path = SESSIONS_DIR / f"{session.id}.json"
    _atomic_write(path, json.dumps(session.to_dict(), ensure_ascii=False))
    _update_index(session)
    return path

def _update_index(session: Session) -> None:
    index = _load_index()
    entry = {
        "id": session.id,
        "timestamp_inicio": session.created_at,
        "timestamp_fim": session.updated_at,
        "primeiro_prompt_truncado": _truncate(session.first_user_prompt(), 80),
        "n_turnos": session.turn_count(),
        "projeto": session.project_path,
    }
    index = [e for e in index if e["id"] != session.id] + [entry]
    _atomic_write(INDEX_PATH, json.dumps({"version": INDEX_SCHEMA_VERSION, "entries": index}, ensure_ascii=False))
```

### `/home/andrefarias/Desenvolvimento/Nyx-Code/nyx/agent/commands/session.py`

**Antes:**
```python
# cmd_resume não existe
```

**Depois:**
```python
@nyx_command(
    name="resume",
    description="Retomar sessão anterior. Sem argumento = última. Com argumento = id ou prefixo.",
    examples=["/resume", "/resume a3f2", "/resume list"],
)
def cmd_resume(args: list[str], ctx: CommandContext) -> CommandResult:
    from nyx.agent.persistence import load_index, load_session
    index = load_index()
    if not args:
        if not index:
            print_error("Nenhuma sessão anterior encontrada.", hint="Comece uma conversa normal e use /save.")
            return CommandResult.ok()
        target = index[-1]
    elif args[0] == "list":
        _print_index(index)
        return CommandResult.ok()
    else:
        target = _match_prefix(index, args[0])
        if not target:
            print_error(f"Nenhuma sessão casa com '{args[0]}'.", hint="Use /resume list para ver todas.")
            return CommandResult.ok()
    session = load_session(target["id"])
    ctx.loop.load_session_into_loop(session, replay_mode="collapsed")
    return CommandResult.ok()
```

### `/home/andrefarias/Desenvolvimento/Nyx-Code/nyx/cli.py`

**Antes:**
```python
def boot() -> None:
    loop = AgentLoop(...)
    repl(loop)
```

**Depois:**
```python
def boot(args: argparse.Namespace) -> None:
    loop = AgentLoop(...)
    if not args.no_resume_prompt and not args.resume:
        maybe_offer_resume(loop)
    elif args.resume:
        session = load_session(args.resume)
        loop.load_session_into_loop(session, replay_mode="collapsed")
    repl(loop)

def maybe_offer_resume(loop: AgentLoop) -> None:
    index = load_index()
    if not index:
        return
    last = index[-1]
    age_hours = (now() - last["timestamp_fim"]) / 3600
    if age_hours > 48 or last["n_turnos"] < 3:
        return
    prompt = f"Retomar última sessão ({last['primeiro_prompt_truncado']})? [s/N] "
    resposta = input(prompt).strip().lower()
    if resposta == "s":
        session = load_session(last["id"])
        loop.load_session_into_loop(session, replay_mode="collapsed")
```

### `/home/andrefarias/Desenvolvimento/Nyx-Code/nyx/agent/loop/_core.py`

**Antes:**
```python
class AgentLoop:
    def __init__(self, ...): ...
```

**Depois:** adicionar método
```python
def load_session_into_loop(self, session: Session, replay_mode: str = "collapsed") -> None:
    """Injeta messages de sessão prévia. NÃO reexecuta tool calls (read-only replay)."""
    if replay_mode == "collapsed":
        self.output.print_dim(f"{session.turn_count()} turnos anteriores -- ver com /replay {session.id[:6]}")
    self.messages.extend(session.messages)
    self.session_id = session.id
```

### `/home/andrefarias/Desenvolvimento/Nyx-Code/scripts/migrate_sessions.py`

Novo. Lê todos os `*.json` em `~/.nyx/sessions/`, reconstrói `index.json` a partir dos metadados. Idempotente: rodar 2x não duplica.

---

## Diff esperado (resumo)

```
+ 1 arquivo criado (migrate_sessions.py)
~ 4 arquivos modificados (persistence, session.py, cli, _core)
- 0 arquivos removidos
+ ~300 linhas líquidas
```

---

## Comandos de verificação (literais, copy-paste)

```bash
# 1. Validação estática
python -m ruff check nyx/

# 2. Migration idempotente
python scripts/migrate_sessions.py
python scripts/migrate_sessions.py  # segunda execução: zero diff
test -f ~/.nyx/sessions/index.json && echo "OK"

# 3. Gauntlet
./run.sh --gauntlet --only sessao
./run.sh --gauntlet --only interface

# 4. Manual: ciclo completo
./run.sh
# > pergunta 1
# > pergunta 2
# > pergunta 3
# Ctrl+D
./run.sh
# Esperado: "Retomar última sessão (...)? [s/N]"
# Digitar s
# Esperado: "3 turnos anteriores -- ver com /replay <id>"

# 5. Flag de supressão
./run.sh --no-resume-prompt
# Esperado: boot direto, sem prompt

# 6. /resume list
./run.sh
# No REPL: /resume list
# Esperado: tabela com id, timestamp, primeiro prompt, n_turnos
```

---

## Critério binário de aceite (IA executora)

- [ ] `/resume` sem arg carrega última sessão
- [ ] `/resume <prefixo>` carrega sessão por prefixo de id
- [ ] `/resume list` imprime tabela
- [ ] Boot com TTL <48h e >=3 turnos exibe prompt
- [ ] Boot com --no-resume-prompt NÃO exibe prompt
- [ ] Tools não são reexecutadas na retomada (logar replay_mode=collapsed)
- [ ] `~/.nyx/sessions/index.json` criado/atualizado a cada save
- [ ] Schema validado antes de restaurar (jsonschema)
- [ ] migrate_sessions.py idempotente
- [ ] Gauntlet `--only sessao` e `--only interface` passam 100%
- [ ] Acentuação PT-BR em todas as mensagens novas
- [ ] Sprint movida para `concluidos/` com commit `feat: /resume com índice persistente e prompt de retomada no boot`
- [ ] Nenhuma violação de `forbidden[]`

---

## Guardrails anti-engodo (obrigatórios)

- Não marcar concluída sem o ciclo manual completo (3 turnos → fechar → abrir → retomar).
- Não "facilitar" pulando validação de schema — sessão antiga corrompida vai travar boot.
- Não ignorar `replay_mode`: se IA escrever `load_session_into_loop(session)` sem o param, rejeitar.
- Se o prompt aparecer em cenário sem satisfazer condições: bug, não feature.

---

## Catálogo de gambiarras proibidas (20 padrões)

Ver `dev-journey/08-templates/SPRINT_TEMPLATE_V2.md` seção "Catálogo de gambiarras proibidas".

---

## Proof-of-work obrigatório (4 passos)

```bash
# PASSO 1 — snapshot ANTES
bash scripts/sprint_invariants.sh > /tmp/inv_before.txt 2>&1
FAIL_BEFORE=$(grep -c "^\[FAIL\]" /tmp/inv_before.txt)
echo "FAIL inicial: $FAIL_BEFORE"

# PASSO 2 — implementação
#   consultar GAMBIARRAS_POR_SPRINT.md seção SESSION-RESUME-01

# PASSO 3 — snapshot DEPOIS
bash scripts/sprint_invariants.sh > /tmp/inv_after.txt 2>&1
FAIL_AFTER=$(grep -c "^\[FAIL\]" /tmp/inv_after.txt)
echo "FAIL final: $FAIL_AFTER"

# PASSO 4 — regras binárias
diff /tmp/inv_before.txt /tmp/inv_after.txt
```

**Formato obrigatório do relatório de conclusão:** ver SPRINT_TEMPLATE_V2.md.

---

## Gambiarras específicas desta sprint

1. **Restaurar sem validar schema.** `session = Session(**json.load(...))` sem checar versão. Proibido — sessão antiga com campo faltando vai crashar loop.
2. **Reexecutar tools na retomada.** Iterar `for msg in session.messages: if msg.tool_call: execute(...)`. Proibido — efeitos colaterais duplicados (arquivos criados 2x, commits repetidos).
3. **Perguntar "Retomar?" sempre.** Ignorar TTL e threshold porque "o usuário decide". Proibido — spec diz TTL 48h, threshold 3 turnos. Respeitar.
4. **Path absoluto hardcoded.** `Path("/home/andrefarias/.nyx/sessions")`. Proibido — usar `Path.home() / ".nyx" / "sessions"`.
5. **Index escrito não-atomicamente.** `INDEX_PATH.write_text(...)` sem `.tmp + os.replace`. Proibido — crash no meio corrompe índice, usuário perde histórico.
6. **Migration não-idempotente.** Duplicar entradas a cada execução. Proibido — spec exige segunda execução = zero diff.
7. **Prefix match frágil.** `if target_id.startswith(arg)` sem checar colisão. Proibido — se 2 sessões começam com mesmo prefixo, pedir desambiguação.

---

## Validação humana (checklist do usuário)

```bash
cd /home/andrefarias/Desenvolvimento/Nyx-Code

# 1. Diff do commit
git log --oneline -1
git show --stat HEAD

# 2. Índice existe e está válido
python -c "import json; print(json.load(open(f'{__import__(\"pathlib\").Path.home()}/.nyx/sessions/index.json'))['version'])"
# esperado: 1

# 3. Ciclo completo manual
./run.sh
# digitar: "olá"
# digitar: "me fale sobre python"
# digitar: "e sobre rust?"
# Ctrl+D
./run.sh
# esperado: prompt "Retomar última sessão (olá)? [s/N]"
# digitar: s
# esperado: "3 turnos anteriores -- ver com /replay ..."

# 4. Flag de supressão
./run.sh --no-resume-prompt
# esperado: boot direto, sem prompt

# 5. Arquivo movido
ls dev-journey/06-sprints/concluidos/SPRINT_SESSION_RESUME_01.md
```

---

## Riscos

| Risco | Mitigação |
|-------|-----------|
| Sessões antigas sem campo `project_path` quebram migration | migrate_sessions.py preenche com "" e emite warning não-fatal |
| TTL de 48h pode ser curto para usuários esporádicos | Tornar configurável via settings (`session_resume_ttl_hours`, default 48) |
| Prompt bloqueia boot se stdin não for tty (ex: pipe) | Detectar `sys.stdin.isatty()` e suprimir prompt automaticamente |
| Race condition em save_session concorrente (múltiplas sessões) | `_atomic_write` com `.tmp + os.replace` + file lock opcional |
| Índice cresce sem limite | Implementar rotação: manter últimas 200 entradas, arquivar resto em `index.archive.json` |
| `/resume list` mostra sessões de projetos diferentes sem filtro | Default filtra por `cwd`; flag `--all` mostra tudo |

---

*"Quem ignora o passado carrega-o em dobro no presente." -- Sêneca (adaptado)*
