# SPRINT HOOKS-DYNAMIC-01 — Hooks dinâmicos via settings.json

## 0. SPEC (machine-readable)

```yaml
sprint:
  id: HOOKS-DYNAMIC-01
  title: "Hooks de execução (PreToolUse, PostToolUse, UserPromptSubmit, Stop) declarados em ~/.nyx/settings.json"
  onda: 23
  bloco: 23.5 Feature parity Claude Code
  prioridade: MÉDIA
  tipo: Feature
  dependencias: [PERF-INFERENCE-01]
  desbloqueia: []
  origem: "Auditoria estratégica 2026-05-16 — gap real vs Claude Code: Nyx tem só git hooks em scripts/hooks/, não tem hooks de execução dinâmicos. Claude Code tem hooks por evento com 'block on failure', 'matcher', etc."

  touches:
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/agent/tools/registry.py
      reason: "Tool execution invoca hooks pre/post via hook_runtime"
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/agent/loop/_core.py
      reason: "Hook 'UserPromptSubmit' invocado após add_user, antes do _call_llm; 'Stop' invocado no fim de turn"
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/config/settings.py
      reason: "Carrega hooks de ~/.nyx/settings.json"

  creates:
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/agent/services/hook_runtime.py
      reason: "Executa hooks shell ou skill, com timeout, matcher (regex de tool name), block_on_failure"
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/dev-journey/05-guides/HOOKS.md
      reason: "Documentação dos eventos + exemplos de hook json"

  removes: []

  n_to_n_pairs:
    - descricao: "Schema de hook em settings.json definido em hook_runtime.py + documentado em HOOKS.md"
      paths:
        - /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/agent/services/hook_runtime.py
        - /home/andrefarias/Desenvolvimento/Nyx-Code/dev-journey/05-guides/HOOKS.md

  forbidden:
    - "Hook executa sem timeout (default 30s, max 300s)"
    - "Hook silencia falha sem logger.warning se block_on_failure=True"
    - "Variáveis sensíveis (API keys) passadas para hooks shell sem opt-in explícito"
    - "Hook que adiciona >5MB ao contexto sem aviso (gauntletria de bloat)"
    - "Emoji"

  tests:
    - cmd: "./venv/bin/python -c 'from nyx.agent.services.hook_runtime import HookRuntime; print(HookRuntime)'"
      timeout: 10
      deve_passar: true
    - cmd: "./run.sh --gauntlet --only rapido"
      timeout: 300
      deve_passar: true
    - cmd: "bash scripts/sprint_invariants.sh"
      timeout: 60
      deve_passar: "FAIL_AFTER <= FAIL_BEFORE"

  acceptance_criteria:
    - "~/.nyx/settings.json suporta seção 'hooks' com eventos: PreToolUse, PostToolUse, UserPromptSubmit, Stop"
    - "Cada hook tem: command (shell ou skill:<name>), matcher (regex opcional), timeout, block_on_failure"
    - "PreToolUse pode VETAR execução de tool (exit != 0 + block_on_failure)"
    - "PostToolUse recebe resultado da tool e pode injetar mensagem no contexto"
    - "UserPromptSubmit recebe input e pode rejeitar/modificar"
    - "Stop recebe último turno e pode disparar finalização externa"
    - "Hook shell roda em subprocess com env limpo (whitelist de vars)"
    - "Hook skill chama Skill tool internamente"
    - "Timeout default 30s, max 300s"
    - "HOOKS.md documenta cada evento com exemplo (shell + skill)"
    - "Boot tolera settings.json malformado (warning, hooks desabilitados, segue)"
    - "PT-BR; zero emoji; zero menção a IA"
```

---

**Status:** PENDENTE
**Data criação:** 2026-05-16
**Modelo obrigatório:** claude-opus-4-7 (sem subagentes)

---

# Sprint HOOKS-DYNAMIC-01

## Schema em ~/.nyx/settings.json

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash",
        "command": "shell:scripts/audit_bash.sh",
        "timeout": 5,
        "block_on_failure": true
      }
    ],
    "PostToolUse": [
      {
        "matcher": "(Write|Edit|MultiEdit)",
        "command": "skill:validacao-visual",
        "timeout": 30,
        "block_on_failure": false
      }
    ],
    "UserPromptSubmit": [
      {
        "command": "shell:scripts/inject_context.sh",
        "timeout": 5,
        "block_on_failure": false
      }
    ],
    "Stop": [
      {
        "command": "shell:scripts/end_turn_summary.sh",
        "timeout": 10,
        "block_on_failure": false
      }
    ]
  }
}
```

## Comportamento

- **PreToolUse**: roda antes de tool execution. Se `block_on_failure=true` e exit !=0, tool é abortada e usuário vê motivo.
- **PostToolUse**: roda após tool. Stdout do hook pode ser injetado no contexto via convenção `INJECT: <texto>`.
- **UserPromptSubmit**: roda quando usuário envia input. Hook recebe o input via stdin. Stdout substitui o input se exit==0 e block_on_failure=false.
- **Stop**: roda quando turno acaba (DONE state). Útil para notify externos.

## Verificação

```bash
mkdir -p ~/.nyx
cat > ~/.nyx/settings.json <<EOF
{
  "hooks": {
    "PostToolUse": [
      {"matcher": "Write", "command": "shell:echo 'Wrote file'", "timeout": 5}
    ]
  }
}
EOF
./run.sh
# nyx> escreva um arquivo /tmp/x.txt com conteudo hello
# Esperado: após tool Write, log mostra "Wrote file"
```

---

*"Hooks são o tendão do agente: invisíveis quando funcionam, óbvios quando faltam." -- princípio de extensibilidade*
