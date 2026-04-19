## 0. SPEC

```yaml
sprint:
  id: AUDIT-FIX-09
  title: "Fechar 3 excepts silenciosos residuais (memory/output/project)"
  onda: 22
  bloco: 2.5
  prioridade: ALTA
  tipo: Bugfix
  dependencias: []
  desbloqueia: [UX-DESIGN-01]

  touches:
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/agent/memory.py
      reason: "except OSError: pass sem log na linha 130"
      linhas_alvo: "127-132"
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/agent/output.py
      reason: "except silencioso na linha 268 sem log"
      linhas_alvo: "265-270"
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/context/project.py
      reason: "except PermissionError: pass sem log na linha 80"
      linhas_alvo: "77-82"

  creates: []
  removes: []

  forbidden:
    - "Remover o except e deixar a exceção estourar silenciosamente via nível acima"
    - "Usar print() ao invés de logger"
    - "Fazer logger.error quando o caso é legítimo de best-effort (usar warning/debug)"

  tests:
    - cmd: "bash scripts/sprint_invariants.sh | grep -E '^\\[FAIL\\].*4\\.'"
      esperado: "vazio (invariante #4 fecha completamente)"
    - cmd: "python -c 'from nyx.agent.memory import MemoryStore; from nyx.agent.output import Output; from nyx.context.project import ProjectContext; print(ok)'"
      deve_passar: true
    - cmd: "./run.sh --gauntlet --only rapido"
      deve_passar: true

  acceptance_criteria:
    - "Invariante #4 sai de FAIL para PASS no sprint_invariants.sh"
    - "Cada except tem logger.warning ou logger.debug com contexto (motivo + path/id quando aplicável)"
    - "Nenhuma mudança de semântica — fluxo best-effort mantido"
    - "Gauntlet rapido passa"
```

---

# Sprint AUDIT-FIX-09 — Excepts silenciosos residuais

**Status:** PENDENTE
**Data criação:** 2026-04-19
**Modelo obrigatório:** claude-opus-4-7 (sem subagentes)

---

## Contexto do projeto (snapshot)

> - CLAUDE.md anti-burla: "Nunca except vazio — todo except deve ter logger.error() ou raise".
> - AUDIT-FIX-04 fechou `cli.py:509-512` (sumarização async).
> - AUDIT-FIX-07 fechou `ask_user.py:78`.
> - Residual: invariante `#4` do `sprint_invariants.sh` aponta 3 lugares ainda em FAIL.

---

## Problema

Três excepts silenciosos sobram no código:

### 1. `nyx/agent/memory.py:130`
```python
except OSError:
    pass
```
Sem log. Escopo do bloco `try`: provável leitura/escrita de arquivo de memória. Se falhar, memória silenciosamente perdida.

### 2. `nyx/agent/output.py:268`
Contexto: bloco dentro de rich spinner (linhas 215-244 usam `except Exception as e: logger.debug(...)` corretamente; a linha 268 está fora desse padrão).

### 3. `nyx/context/project.py:80`
```python
except PermissionError:
    pass
```
Dentro de `_scan_project_files` varrendo extensões. Path sem permissão é silenciosamente pulado.

---

## Solução proposta

Adicionar `logger.warning(...)` (ou `debug` quando for caso legítimo de best-effort) em cada bloco, incluindo contexto (path, id, motivo).

---

## Arquivos alvo

### `/home/andrefarias/Desenvolvimento/Nyx-Code/nyx/agent/memory.py`

**Antes (linhas ~127-132):**
```python
        try:
            <operação I/O>
        except OSError:
            pass
```

**Depois:**
```python
        try:
            <operação I/O>
        except OSError as e:
            logger.warning("falha I/O em memory.py: %s (path=%s)", e, <path se disponível>)
```

### `/home/andrefarias/Desenvolvimento/Nyx-Code/nyx/agent/output.py`

**Antes (linha 268):**
```python
        except <...>:
            pass
```

**Depois:**
```python
        except <...> as e:
            logger.debug("render degradado: %s", e)
```

(Usar `debug` em vez de `warning` porque output é best-effort visual — não deve ficar barulhento se terminal não suportar algum glifo.)

### `/home/andrefarias/Desenvolvimento/Nyx-Code/nyx/context/project.py`

**Antes (linhas 77-82):**
```python
        except PermissionError:
            pass
```

**Depois:**
```python
        except PermissionError as e:
            logger.debug("sem permissão para ler entrada: %s", e)
```

(Usar `debug`: `_scan_project_files` varre árvore; paths sem permissão são esperados em `.git/objects/`, `/proc`, etc.)

---

## Diff esperado

```
~ 3 arquivos modificados
+ 6 linhas líquidas (3 except ... as e + 3 logger calls)
```

---

## Comandos de verificação

```bash
# 1. invariante #4 fecha
bash scripts/sprint_invariants.sh | grep -E '^\[FAIL\].*4\.'
# esperado: vazio

# 2. grep por pass pós-except sem log
grep -n -A1 'except.*:$' nyx/agent/memory.py nyx/agent/output.py nyx/context/project.py | grep -B1 '^\s*pass\s*$'
# esperado: vazio

# 3. smoke
./run.sh --gauntlet --only rapido
```

---

## Critério binário de aceite

- [ ] Invariante #4 PASS
- [ ] Cada except tem logger.<level>(...) com contexto
- [ ] Nenhum `pass` isolado após `except:` nos 3 arquivos
- [ ] Gauntlet rapido passa
- [ ] Commit `fix: loga exceções silenciosas em memory/output/project`

---

## Gambiarras específicas

- **`logger.error` quando o caso é best-effort** → ruído. Regra: `warning` quando é falha que poderia ser bug; `debug` quando é caminho previsto (PermissionError em scan, glifo não suportado).
- **`except Exception` genérico** no lugar do tipo específico → não correlaciona com o original. Proibido trocar o tipo da exceção capturada.
- **Logar `str(e)` vazio** quando a exceção não tem mensagem → acrescentar path/id literal no log.

---

## Riscos

| Risco | Mitigação |
|-------|-----------|
| Log barulhento em scan de árvore | Usar `debug`, não `warning` |
| Conflito com logger não importado no arquivo | Verificar: memory.py/output.py/project.py já usam `get_logger` (via DEBT-03); reusar |

---

*"Silêncio é irmão do erro. Fala é irmã da correção." -- adaptação livre*
