## 0. SPEC (machine-readable)

```yaml
sprint:
  id: AUDIT-01
  title: "Seguranca: path traversal, preflight, validator"
  touches:
    - path: nyx/agent/tools/base.py
      reason: "Adicionar validate_path() para protecao contra path traversal"
    - path: nyx/agent/tools/read_file.py
      reason: "Aplicar validate_path e limite de tamanho"
    - path: nyx/agent/tools/write_file.py
      reason: "Aplicar validate_path"
    - path: nyx/agent/tools/edit_file.py
      reason: "Aplicar validate_path"
    - path: nyx/agent/tools/glob_tool.py
      reason: "Aplicar validate_path"
    - path: nyx/agent/tools/list_files.py
      reason: "Aplicar validate_path"
    - path: nyx/agent/tools/multi_edit.py
      reason: "Aplicar validate_path"
    - path: nyx/agent/tools/patch_tool.py
      reason: "Aplicar validate_path"
    - path: nyx/agent/tools/notebook_edit.py
      reason: "Aplicar validate_path"
    - path: nyx/agent/tools/run_command.py
      reason: "Adicionar blocklist expandida de comandos destrutivos"
    - path: nyx/agent/loop.py
      reason: "Integrar preflight antes e validator depois de cada tool call"
    - path: nyx/agent/preflight.py
      reason: "Expandir validacoes pre-execucao"
    - path: nyx/agent/validator.py
      reason: "Expandir validacoes pos-execucao"
  n_to_n_pairs:
    - "validate_path em base.py deve ser usado por TODAS as tools de arquivo"
  forbidden:
    - "Nunca permitir path absoluto fora de project_root ou ~/.nyx/"
    - "Nunca permitir symlinks que escapam do projeto"
  tests:
    - cmd: "./run.sh --gauntlet --only audit_seguranca"
      timeout: 300
  acceptance_criteria:
    - "validate_path rejeita ../../etc/passwd"
    - "validate_path rejeita /etc/passwd"
    - "validate_path rejeita symlinks que saem do projeto"
    - "validate_path aceita paths dentro do projeto"
    - "validate_path aceita paths em ~/.nyx/"
    - "read_file rejeita arquivos maiores que 1MB"
    - "preflight e chamado antes de cada tool call no loop"
    - "validator e chamado depois de cada tool call no loop"
    - "run_command bloqueia rm -rf /, sudo, mkfs, dd if=/dev/"
    - "Acentuacao PT-BR correta"
```

---

# Sprint AUDIT-01 -- Seguranca: Path Traversal, Preflight, Validator

**Status:** PENDENTE
**Data:** 2026-04-15
**Prioridade:** CRITICA
**Tipo:** Bugfix/Seguranca
**Dependencias:** Nenhuma
**Desbloqueia:** AUDIT-02, AUDIT-03

---

## Problema / Contexto

A auditoria completa revelou que TODAS as tools de arquivo (read_file, write_file, edit_file, glob, list_files, multi_edit, patch, notebook_edit) aceitam paths absolutos sem nenhuma validacao. O LLM pode instruir o agente a ler `/etc/passwd` ou escrever em `/etc/crontab`. Combinado com `run_command` usando `shell=True`, e um vetor de ataque real.

Alem disso, `preflight.py` (validacao pre-execucao) e `validator.py` (validacao pos-execucao) existem e estao implementados, mas o `loop.py` nunca os chama.

## Implementacao

### Fase 1: validate_path em base.py

Criar funcao `validate_path(file_path: str, project_root: str) -> Path` que:
- Resolve o path absoluto via `.resolve()`
- Verifica que o path resolvido comeca com `project_root` ou `Path.home() / ".nyx"`
- Rejeita symlinks cujo target esta fora do projeto
- Lanca `ValueError` se violado
- Retorna o `Path` validado

### Fase 2: Aplicar em todas as tools de arquivo

Trocar o padrao atual:
```python
path = Path(project_root) / file_path if not Path(file_path).is_absolute() else Path(file_path)
```
Por:
```python
path = validate_path(file_path, project_root)
```

Aplicar em: read_file, write_file, edit_file, glob_tool, list_files, multi_edit, patch_tool, notebook_edit.

### Fase 3: Limite de tamanho no read_file

Adicionar constante `MAX_FILE_SIZE = 1_048_576` (1MB). Verificar `path.stat().st_size` antes de ler. Retornar erro se exceder.

### Fase 4: Integrar preflight e validator no loop

No `loop.py`, antes de `self._tools.execute()`:
```python
from nyx.agent.preflight import check as preflight_check
pf = preflight_check(name, args, self._project_root)
if not pf.ok:
    # logar e pular
```

Depois de `self._tools.execute()`:
```python
from nyx.agent.validator import validate as post_validate
vr = post_validate(name, args, result)
if vr.warnings:
    # logar warnings
```

### Fase 5: Expandir blocklist do run_command

Na `preflight.py`, adicionar: `chmod 777`, `chown`, `curl | sh`, `wget -O- | sh`, `pip install` (sem --user), `> /dev/sda`.

## Verificacao

- [ ] validate_path rejeita `../../etc/passwd`
- [ ] validate_path rejeita `/etc/passwd`
- [ ] validate_path aceita `nyx/cli.py`
- [ ] validate_path aceita `~/.nyx/memory/test.json`
- [ ] read_file rejeita arquivo > 1MB
- [ ] preflight bloqueia `rm -rf /`
- [ ] validator loga warning quando run_command output contem "error"
- [ ] Gauntlet fase audit_seguranca passa
- [ ] Acentuacao PT-BR correta em todo codigo novo

---

*"A seguranca nao e um produto, e um processo." -- Bruce Schneier*
