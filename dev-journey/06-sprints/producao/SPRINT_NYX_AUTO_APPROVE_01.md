# SPRINT NYX-AUTO-APPROVE-01 — Pular CONFIRM_ONCE em automação (env + flag)

## 0. SPEC

```yaml
sprint:
  id: NYX-AUTO-APPROVE-01
  title: "Modo automatizado pula prompts CONFIRM_ONCE para tools write/edit"
  onda: 24
  bloco: 24.6 Infra resiliente
  prioridade: ALTA
  tipo: Feature
  dependencias: []
  desbloqueia: [VALIDATE-FINAL-01-PARTE-2, automacao via cockpit]
  origem: "Achado real 2026-05-18: tentei via /control/repl/send pedir Nyx criar projeto. Tool write_file disparou prompt CONFIRM_ONCE [permissão: uma vez] no PTY -- sem canal de resposta automática, gerou deadlock."

  touches:
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/agent/permissions.py
      reason: "Aceitar env NYX_AUTO_APPROVE=1 que retorna PermissionLevel.AUTO para tools com CONFIRM_ONCE"
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/cli.py
      reason: "Honrar env var ao construir AgentLoop; documentar trade-off"
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/run.sh
      reason: "Aceitar flag --auto-approve que seta NYX_AUTO_APPROVE=1 antes do exec"

  forbidden:
    - "Quebrar permissões DENY (esses NUNCA passam, mesmo com auto-approve)"
    - "Ativar auto-approve por default (segurança: usuario opt-in via env/flag)"
    - "Persistir auto-approve em arquivo (somente runtime)"

  tests:
    - cmd: "NYX_AUTO_APPROVE=1 echo 'crie arquivo /tmp/test_auto.txt com conteudo oi' | ./run.sh --headless"
      timeout: 60
      deve_passar: true
      nota: "Cria arquivo sem prompt interativo"
    - cmd: "bash scripts/sprint_invariants.sh"
      timeout: 60
      deve_passar: "14/14"

  acceptance_criteria:
    - "Env NYX_AUTO_APPROVE=1 ativa modo automático"
    - "Flag --auto-approve em run.sh seta env antes do exec"
    - "CONFIRM_ONCE silenciosamente aprova quando flag ativa"
    - "DENY ainda bloqueia (segurança)"
    - "Documentado em README + AVISO de segurança"
    - "Smoke + invariantes 14/14"
```

---

# Sprint NYX-AUTO-APPROVE-01

**Status:** PENDENTE
**Data criação:** 2026-05-18 (achado de uso real via cockpit/REPL)
**Modelo obrigatório:** claude-opus-4-7

---

## Contexto

Cenário: tentei via cockpit Control API (`POST /control/repl/send`) pedir ao Nyx para criar projeto Python. O Nyx invocou `write_file` corretamente, mas o flow de permissão `CONFIRM_ONCE` disparou prompt interativo `[permissão: uma vez] Executar write_file(...)? [S/n] Terminado` no PTY. Sem canal automático de resposta (cockpit não tem UI de aprovar), a tool fica travada e o REPL eventualmente é morto.

Esta sprint resolve o caso de **automação confiável**:

1. Modo opt-in via env `NYX_AUTO_APPROVE=1` ou flag `--auto-approve`.
2. Quando ativo, `PermissionLevel.CONFIRM_ONCE` é tratado como aprovado silenciosamente.
3. `PermissionLevel.DENY` permanece bloqueando (segurança preservada).

### Sintoma observável

Screenshot `nyx_project_progress.png` (sessão 2026-05-18) mostra:
```
write_file ──────────── executando ┐
│  file_path=/tmp/nyx_validation_project/README.md · content=todo-cli é um CLI
[permissão: uma vez] Executar write_file(...)? [S/n] Terminado
[nyx] Desconectando...
```

`Terminado` é a mensagem do EOF que matou o REPL — agente externo enviou newlines mas não respondeu `S`.

---

## Solução proposta

### 1. nyx/agent/permissions.py

Adicionar check no início do `PermissionManager.check()`:
```python
if os.environ.get("NYX_AUTO_APPROVE") == "1":
    # AVISO: modo automatizado; CONFIRM_ONCE silenciosamente aprovado.
    # Ainda respeita DENY (segurança).
    current_level = self._get_level(tool_name, args)
    if current_level == PermissionLevel.CONFIRM_ONCE:
        return PermissionLevel.AUTO_APPROVED
    return current_level
```

Onde `PermissionLevel.AUTO_APPROVED` é um valor novo que `loop._iteration.py` interpreta como "aprovado sem perguntar".

### 2. nyx/cli.py

No início (após carregar settings), logar warning se `NYX_AUTO_APPROVE=1` for detectado:
```python
if os.environ.get("NYX_AUTO_APPROVE") == "1":
    logger.warning("NYX_AUTO_APPROVE ativo: CONFIRM_ONCE auto-aprovado. Use só em automação confiável.")
```

### 3. run.sh

```bash
--auto-approve)
    export NYX_AUTO_APPROVE=1
    shift ;;
```

### 4. README

Seção nova "Modo automatizado":
```
Para automação via Cockpit Control API ou scripts não-interativos, ative:

  ./run.sh --auto-approve     # CONFIRM_ONCE silenciosamente aprovado

ATENCAO: tools que tocam filesystem/network/git rodam sem prompt.
Use apenas em ambientes controlados (CI, dev, sandbox).
```

---

## Critério binário

- [ ] `NYX_AUTO_APPROVE=1` ativa modo automático
- [ ] `--auto-approve` em run.sh seta env
- [ ] CONFIRM_ONCE -> aprovado quando flag ativa
- [ ] DENY ainda bloqueia
- [ ] README seção "Modo automatizado" com AVISO
- [ ] Smoke + invariantes 14/14
- [ ] Sprint movida `producao/` → `concluidos/`
- [ ] Commit `feat(NYX-AUTO-APPROVE-01): --auto-approve / NYX_AUTO_APPROVE=1 pula CONFIRM_ONCE`

---

*"Automacao sem caminho de aprovacao automatica = deadlock disfarcado." -- NYX-AUTO-APPROVE-01*
