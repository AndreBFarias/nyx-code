# SPRINT NYX-GSD-CHECKPOINTS-01 — Sistema GSD + checkpoints + documentação dinâmica

## 0. SPEC

```yaml
sprint:
  id: NYX-GSD-CHECKPOINTS-01
  title: "AgentLoop grava progress.md write-through a cada tool call (GSD entre tasks)"
  onda: 24
  bloco: 24.9 Memória contínua
  prioridade: ALTA
  tipo: Feature
  dependencias: [SESSION-RESUME-01, CTX-01]
  desbloqueia: [NYX-PROMPT-REINJECT-01, projetos longos sem perda de contexto]
  origem: "Pedido do usuario 2026-05-18: 'temos que ter um sistema de gsd, checkpoints e documentacao dinamica entre cada task que ele tiver que fazer'. Inspirado no Checkpoint.md do projeto Nyx-Code mas aplicado ao runtime da Nyx em qualquer projeto."

  touches:
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/agent/loop/_core.py
      reason: "Hook on_tool_result grava entry em progress.md write-through"
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/agent/loop/_iteration.py
      reason: "Iteracao registra plano antes de tool call"
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/agent/persistence.py
      reason: "save_session expande para incluir progress.md path"
  creates:
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/agent/services/gsd_writer.py
      reason: "Helper que mantém ~/.nyx/sessions/<id>/progress.md sincronizado"

  forbidden:
    - "Bloquear tool call ao falhar write em progress.md (best-effort)"
    - "Persistir secrets/senhas em progress.md"
    - "Truncar progress.md sem manter ultimas 200 linhas"
    - "Sobrescrever progress.md de outra sessao"

  tests:
    - cmd: "ls ~/.nyx/sessions/<id>/progress.md"
      timeout: 5
      deve_passar: "arquivo existe apos 1 turno"
    - cmd: "bash scripts/sprint_invariants.sh"
      timeout: 60
      deve_passar: "14/14"

  acceptance_criteria:
    - "Cada AgentLoop session tem ~/.nyx/sessions/<id>/progress.md"
    - "Cada tool call dispara entry: [timestamp] tool(args) -> result_summary"
    - "Cada user_input vira heading: ## [timestamp] Pedido: <texto>"
    - "Estado runtime registrado: iter_n, lidos, modif, files_read[], files_modified[]"
    - "Write-through obrigatorio: fflush + fsync apos cada entry"
    - "Rotacao: max 200 linhas; oldest removed quando excede"
    - "/resume carrega progress.md como contexto inicial extra"
    - "/progress mostra ultimas 30 linhas no terminal"
    - "Smoke + invariantes 14/14"
```

---

# Sprint NYX-GSD-CHECKPOINTS-01

**Status:** CONCLUIDA
**Data criação:** 2026-05-18 (achado de uso real)
**Data conclusão:** 2026-05-19
**Modelo obrigatório:** claude-opus-4-7

---

## Contexto

Padrão Nyx-Code já provou valor: `Checkpoint.md` mantém estado entre sessões Claude. Mesmo padrão aplicado ao runtime da Nyx em qualquer projeto:

- Modelo qwen2.5-coder:3b tem 12k tokens de contexto; conversas longas saturam.
- Compactação (CTX-01) condensa mas perde nuance.
- Sessão pode cair (OOM, kill, exit acidental).
- Re-attach via `/resume` hoje carrega só messages, não plano.

GSD checkpoints transforma a Nyx em **agente com memória de trabalho persistente**: cada tarefa deixa rastro write-through, e /resume retoma do ponto exato.

## Solução proposta

### `nyx/agent/services/gsd_writer.py` (novo)

```python
from pathlib import Path
from datetime import datetime

class GsdWriter:
    """Write-through de progress.md por sessao.

    Cada entry: timestamp + categoria + texto curto.
    Rotacao em 200 linhas, mantendo header + ultimas 199.
    """

    def __init__(self, session_id: str, project_name: str):
        self.path = Path.home() / ".nyx" / "sessions" / session_id / "progress.md"
        self.path.parent.mkdir(parents=True, exist_ok=True)
        if not self.path.is_file():
            self._init_file(session_id, project_name)

    def _init_file(self, sid, project):
        header = (
            f"# Progress -- sessao {sid}\n"
            f"\n"
            f"Projeto: {project}\n"
            f"Iniciada: {datetime.utcnow().isoformat()}Z\n"
            f"\n"
            f"## Append-only\n\n"
        )
        self.path.write_text(header, encoding="utf-8")

    def write(self, category: str, msg: str) -> None:
        """Append entry com timestamp; write-through (flush+fsync)."""
        ts = datetime.utcnow().strftime("%H:%M:%S")
        line = f"- [{ts}] **{category}** {msg}\n"
        with self.path.open("a", encoding="utf-8") as f:
            f.write(line)
            f.flush()
            import os
            os.fsync(f.fileno())
        self._rotate()

    def user_input(self, text: str) -> None:
        snippet = text.replace("\n", " ")[:120]
        self.write("user", f"`{snippet}`")

    def tool(self, name: str, args: dict, result: str) -> None:
        argp = ", ".join(f"{k}={str(v)[:30]}" for k, v in args.items())
        rsum = result[:80].replace("\n", " ") if result else "(sem output)"
        self.write("tool", f"{name}({argp}) -> {rsum}")

    def error(self, msg: str) -> None:
        self.write("err", msg[:200])

    def plan(self, msg: str) -> None:
        self.write("plan", msg[:200])

    def _rotate(self):
        lines = self.path.read_text(encoding="utf-8").splitlines()
        if len(lines) > 250:
            header = lines[:6]
            tail = lines[-194:]
            self.path.write_text("\n".join(header + tail) + "\n", encoding="utf-8")
```

### `nyx/agent/loop/_core.py`

```python
# No __init__:
from nyx.agent.services.gsd_writer import GsdWriter
self._gsd = GsdWriter(session.session_id, project_root_name)

# Em run(user_input):
self._gsd.user_input(user_input)

# Quando session salvar:
self._gsd.write("session", f"iter={iterations} lidos={files_read} modif={files_modified}")
```

### `nyx/agent/loop/_iteration.py`

```python
# Antes de cada tool call:
self._gsd.tool(name, args, "...")  # placeholder, atualiza apos execucao

# Apos resultado:
self._gsd.tool(name, args, result_summary)
```

### Slash `/progress`

`nyx/agent/commands/progress.py`:
```python
@nyx_command(name="progress", aliases=["gsd"], category="sessao",
             examples=["/progress", "/progress 50"])
def cmd_progress(args, root):
    n = int(args.strip() or 30)
    return f"__progress_tail__{n}"
```

Handler em cli.py imprime últimas N linhas do `progress.md`.

### `/resume` integra

`nyx/agent/persistence.py::load_session`:
```python
# Apos carregar messages:
gsd_path = sessions_dir / session_id / "progress.md"
if gsd_path.is_file():
    # Anexa últimas 50 linhas do progress como system message extra
    extra_context = "\n".join(gsd_path.read_text().splitlines()[-50:])
    session.add_system(f"Progresso anterior:\n{extra_context}")
```

## Critério binário

- [ ] `progress.md` criado por sessao
- [ ] Write-through (flush + fsync)
- [ ] Rotacao 200 linhas
- [ ] /progress mostra tail
- [ ] /resume carrega ultimas 50 linhas como contexto
- [ ] Sem leak de senhas/secrets
- [ ] Smoke + invariantes 14/14
- [ ] Commit `feat(NYX-GSD-CHECKPOINTS-01): progress.md write-through por sessao`

---

*"O cerebro esquece; o disco lembra." -- NYX-GSD-CHECKPOINTS-01*
