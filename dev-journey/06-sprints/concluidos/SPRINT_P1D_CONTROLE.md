## 0. SPEC (machine-readable)

```yaml
sprint:
  id: P1-D
  title: "Controle: Permissions + Path Resolver"
  touches:
    - path: nyx/agent/permissions.py
      reason: "4 níveis de permissão: auto, confirm_once, always_confirm, deny (port Luna)"
    - path: nyx/agent/path_resolver.py
      reason: "Resolução de caminhos relativos + índice de arquivos (port Luna)"
  origin:
    primary:
      - "Luna/src/skills/code_agent/permissions.py (155 linhas)"
      - "Luna/src/skills/code_agent/path_resolver.py (243 linhas)"
    reference: "openclaud/src/hooks/toolPermission/ + openclaud/src/utils/file.ts"
  acceptance_criteria:
    - "PermissionChecker com 4 níveis: auto_approve, confirm_once, always_confirm, deny"
    - "Config em ~/.nyx/permissions.json (cria default se não existir)"
    - "PathResolver resolve caminhos relativos ao projeto"
    - "PathResolver sugere correção para paths errados (fuzzy match)"
```

---

# Sprint P1-D -- Controle

**Status:** CONCLUIDA (header corrigido em MASTER-CLEANUP-02 2026-05-20; presença em concluidos/ implica CONCLUIDA conforme convenção do projeto)
**Prioridade:** MEDIA
**Tipo:** Port (Luna -> Nyx)
**Dependências:** P1-A
**Desbloqueia:** P1-F

---

## O que portar

### 1. `nyx/agent/permissions.py` (Luna: permissions.py, 155 linhas)

4 níveis de permissão:
- **auto_approve:** read_file, search, list_files, glob, analyze, done
- **confirm_once:** edit_file, write_file, patch
- **always_confirm:** run_command
- **deny:** rm -rf, sudo

Config em `~/.nyx/permissions.json`.

**Ajustes:** trocar `~/.luna` -> `~/.nyx`, trocar `CREATE_FILE` para `WRITE_FILE`.

### 2. `nyx/agent/path_resolver.py` (Luna: path_resolver.py, 243 linhas)

Resolve caminhos relativos e sugere correções:
- Constrói índice de arquivos do projeto
- Fuzzy match para paths incorretos
- Resolve `./`, `../`, paths absolutos

**Ajustes:** trocar imports.

## Testes Gauntlet (novos, adicionados ao nyx_gauntlet.py)

Fase: `controle` (nova, 4 testes)

| ID | Nome | Validação |
|----|------|-----------|
| CT-01 | Permissão auto_approve | PermissionChecker aprova read_file sem confirmação |
| CT-02 | Permissão always_confirm | PermissionChecker requer confirmação para run_command |
| CT-03 | Path resolve relativo | PathResolver("README.md") retorna path absoluto existente |
| CT-04 | Path resolve fuzzy | PathResolver sugere correção para path com case errado |

## Verificação

- [ ] 4 testes de controle passam no Gauntlet
- [ ] `./run.sh --gauntlet --only controle` passa 100%
- [ ] Gauntlet completo continua passando 100%

---

*"O controle sem liberdade é tirania. Liberdade sem controle é caos." -- Voltaire*
