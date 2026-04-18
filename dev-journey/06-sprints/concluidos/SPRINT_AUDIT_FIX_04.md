## 0. SPEC

```yaml
sprint:
  id: AUDIT-FIX-04
  title: "Logar exceção em cli.py:509 (anti-burla)"
  onda: 22
  bloco: 1
  prioridade: ALTA
  tipo: Bugfix
  dependencias: []

  touches:
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/cli.py
      linhas_alvo: "509-512"
      reason: "except RuntimeError: pass — adicionar logger.warning"

  forbidden:
    - "Remover o try/except (a falha é esperada quando loop já fechou)"

  tests:
    - cmd: "./run.sh --gauntlet --only rapido"
      deve_passar: true

  acceptance_criteria:
    - "cli.py:509 tem logger.warning explicando a falha"
    - "Comportamento funcional inalterado"
    - "grep -n 'except RuntimeError:' nyx/cli.py | wc -l == 1 (única ocorrência)"
```

---

# Sprint AUDIT-FIX-04 — Logar exceção silenciosa

## Contexto

CLAUDE.md inviolável: "Nunca except vazio — todo except deve ter `logger.error()` ou `raise`. `except: pass` é proibido."

## Problema

`nyx/cli.py:509-512`:
```python
try:
    asyncio.create_task(agent.maybe_summarize())
except RuntimeError:
    pass
```

Falha silenciosa: se `create_task` falha (loop fechado), sumarização é perdida sem qualquer aviso.

## Solução

```python
try:
    asyncio.create_task(agent.maybe_summarize())
except RuntimeError as exc:
    logger.warning("sumarização adiada (loop indisponível): %s", exc)
```

## Verificação

```bash
grep -A2 "except RuntimeError" nyx/cli.py | grep "logger"
# saída deve conter a linha do logger.warning
./run.sh --gauntlet --only rapido
```

## Critério

- [ ] Linha `logger.warning(...)` presente
- [ ] Commit: `fix: loga excecao silenciosa em cli.py (anti-burla)`

*"Quem mata o sinal, mata o paciente." -- anônimo SRE*
