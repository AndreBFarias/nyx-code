## 0. SPEC (machine-readable)

```yaml
sprint:
  id: AUDIT-04
  title: "Except handling e qualidade de codigo"
  touches:
    - path: nyx/providers/ollama.py
      reason: "Adicionar logger.debug nos except Exception:"
    - path: nyx/agent/completer.py
      reason: "Adicionar logger.debug no except Exception:"
    - path: nyx/agent/output.py
      reason: "Adicionar logger.debug nos except Exception:"
    - path: nyx/agent/model_tier.py
      reason: "Adicionar logger.debug no except Exception:"
    - path: nyx/agent/tools/config_tool.py
      reason: "Adicionar logger.debug no except Exception:"
    - path: nyx/agent/tools/skill_tool.py
      reason: "Adicionar logger.debug no except Exception:"
    - path: nyx/agent/tools/worktree.py
      reason: "Adicionar logger.warning nos except Exception:"
    - path: nyx/agent/services/memory.py
      reason: "Adicionar logger.warning no except Exception:"
    - path: nyx/agent/tools/multi_edit.py
      reason: "Adicionar logger.warning nos except Exception:"
    - path: nyx/agent/tools/task_manager.py
      reason: "Adicionar logger.debug no except Exception:"
    - path: nyx/agent/tools/web_search.py
      reason: "Adicionar logger.debug no except Exception:"
    - path: nyx/agent/tools/search.py
      reason: "Adicionar logger.debug no except Exception:"
    - path: nyx/agent/tools/brief_tool.py
      reason: "Adicionar logger.debug no except Exception:"
    - path: nyx/agent/tools/todo_write.py
      reason: "Adicionar logger.debug no except Exception:"
    - path: nyx/cli.py
      reason: "Corrigir Path hardcoded /tmp"
    - path: nyx/proxy.py
      reason: "Corrigir f-strings no logger"
  n_to_n_pairs: []
  forbidden:
    - "Nunca except Exception: sem as e"
    - "Nunca except Exception: pass sem logger"
    - "Nunca Path('/tmp/...')"
    - "Nunca f-string em logger.info/error/warning"
  tests:
    - cmd: "./run.sh --gauntlet --only audit_qualidade"
      timeout: 300
  acceptance_criteria:
    - "Zero 'except Exception:' sem 'as e' no projeto"
    - "Todo except tem logger.debug/warning/error"
    - "Zero Path('/tmp/...')"
    - "Zero f-string em chamadas de logger"
    - "Acentuacao PT-BR correta"
```

---

# Sprint AUDIT-04 -- Except Handling e Qualidade

**Status:** PENDENTE
**Data:** 2026-04-15
**Prioridade:** MEDIA
**Tipo:** Bugfix/Qualidade
**Dependencias:** AUDIT-01
**Desbloqueia:** AUDIT-05

---

## Problema / Contexto

A regra anti-burla do GUIDE.md diz: "Nunca except vazio -- todo except deve ter logger.error() ou raise. except: pass e proibido."

A auditoria encontrou 20+ locais com `except Exception:` (sem `as e`) seguidos de `pass`, `return False`, `return []` ou `continue`. Nenhum loga o erro. Isso viola a regra e dificulta debugging.

Alem disso:
- `cli.py:317` usa `Path("/tmp/nyx_clipboard.txt")` -- path absoluto hardcoded
- `proxy.py` usa f-strings em chamadas de logger (ineficiente: formata mesmo se o log nao sera emitido)

## Implementacao

### Fase 1: Corrigir except Exception:

Padrao de correcao:

**Antes:**
```python
except Exception:
    return False
```

**Depois:**
```python
except Exception as e:
    logger.debug("Contexto da operacao: %s", e)
    return False
```

Usar `logger.debug` para falhas esperadas (ex: GPU nao detectada, modulo nao instalado).
Usar `logger.warning` para falhas inesperadas (ex: memoria corrompida, worktree falhou).

### Fase 2: Corrigir Path hardcoded

`cli.py:317`:
```python
# Antes
tmp = Path("/tmp/nyx_clipboard.txt")
# Depois
tmp = Path.home() / ".nyx" / "clipboard.txt"
```

### Fase 3: Corrigir f-strings no proxy

`proxy.py`: trocar todos os `logger.info(f"...")` por `logger.info("...", var)`.

Exemplo:
```python
# Antes
logger.info(f"-> model={model} tools={n_tools}")
# Depois
logger.info("-> model=%s tools=%d", model, n_tools)
```

## Verificacao

- [ ] `grep -rn "except Exception:$" nyx/` retorna 0 resultados
- [ ] `grep -rn "Path(\"/tmp" nyx/` retorna 0 resultados
- [ ] `grep -rn 'logger\.\(info\|error\|warning\|debug\)(f"' nyx/` retorna 0 resultados
- [ ] Gauntlet fase audit_qualidade passa
- [ ] Acentuacao PT-BR correta

---

*"A qualidade nao e um ato, e um habito." -- Aristoteles*
