# SPRINT INFRA-CLI-SPLIT-01 — Refactor nyx/cli.py (984L) abaixo de 800L

## 0. SPEC (machine-readable)

```yaml
sprint:
  id: INFRA-CLI-SPLIT-01
  title: "Refactor nyx/cli.py em módulos coesos abaixo do limite 800L (GUIDE.md §6)"
  onda: 23
  bloco: 23.1 Estabilização
  prioridade: MÉDIA
  tipo: Refactor
  dependencias: []
  desbloqueia: []
  origem: "Achado colateral de UX-BUG-03 (14e96aa): nyx/cli.py em 984L excede limite GUIDE.md §6 (800L). Já estava em 943L antes de UX-BUG-03 (+41L da sprint). Pré-existente."

  touches:
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/cli.py
      reason: "Ponto de entrada. Manter run_repl/main como dispatcher fino; mover handlers e setup para módulos."

  creates:
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/cli_keybindings.py
      reason: "Extrair PromptSession keybindings (Ctrl+O paste, /slash, Tab, etc.)"
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/cli_callbacks.py
      reason: "Extrair on_token, on_tool, on_tool_result, on_compaction, on_model_state callbacks"
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/cli_sentinels.py
      reason: "Extrair handlers de result == '__quit__', '__clear__', '__status__', '__context__', '__error__<msg>'"

  removes: []

  n_to_n_pairs: []

  forbidden:
    - "Mudar comportamento externo do REPL (output, prompt, atalhos — tudo idêntico)"
    - "Quebrar gauntlet rapido/p7_tui/interface"
    - "Aumentar complexidade ciclomatica do run_repl"
    - "Imports circulares entre os novos módulos"
    - "Emoji"

  tests:
    - cmd: "wc -l nyx/cli.py | awk '{print $1}'"
      timeout: 5
      deve_passar: true
      nota: "Deve ser < 800"
    - cmd: "./run.sh --smoke"
      timeout: 60
      deve_passar: true
    - cmd: "./run.sh --gauntlet --only rapido"
      timeout: 300
      deve_passar: true
    - cmd: "./run.sh --gauntlet --only p7_tui"
      timeout: 60
      deve_passar: true
    - cmd: "./run.sh --gauntlet --only interface"
      timeout: 60
      deve_passar: true
    - cmd: "bash scripts/sprint_invariants.sh"
      timeout: 60
      deve_passar: "FAIL_AFTER <= FAIL_BEFORE"

  acceptance_criteria:
    - "nyx/cli.py < 800 linhas (limite GUIDE.md §6)"
    - "3 módulos novos coesos: cli_keybindings.py, cli_callbacks.py, cli_sentinels.py"
    - "Tempo time-to-prompt continua <= 1.5s (sem regressão de UX-BUG-03)"
    - "Mediana time-to-prompt: nova mediana <= 0.5s (mantém 4x folga de UX-BUG-03)"
    - "Gauntlet rapido + p7_tui + interface passam 100% sem regressão"
    - "Imports cíclicos: zero"
    - "Comportamento externo do REPL idêntico (prompt, atalhos, output)"
    - "PT-BR; zero emoji; zero menção a IA"
```

---

**Status:** PENDENTE
**Data criação:** 2026-05-17
**Modelo obrigatório:** claude-opus-4-7 (sem subagentes)
**Origem:** achado colateral de UX-BUG-03 (commit 14e96aa). Anti-débito.

---

# Sprint INFRA-CLI-SPLIT-01

## Contexto

`nyx/cli.py` cresceu para 984L ao longo das sprints da Onda 23. Excede limite GUIDE.md §6 (800L para arquivos não-registry). Refactor não-funcional para alinhar com regra. Comportamento externo preservado.

## Plano de extração

| Módulo novo | Conteúdo | LOC estimado |
|---|---|---|
| `nyx/cli_keybindings.py` | KeyBindings @kb.add (Ctrl+O paste expansion, /slash, Tab, etc.) | ~80L |
| `nyx/cli_callbacks.py` | on_token, on_tool, on_tool_result, on_compaction, on_model_state | ~100L |
| `nyx/cli_sentinels.py` | Handlers de result == '__quit__'/'__clear__'/etc | ~60L |
| `nyx/cli.py` (residual) | run_repl + main + dispatcher fino | ~750L |

## Verificação

```bash
wc -l nyx/cli.py        # < 800
./run.sh --smoke
./run.sh --gauntlet --only rapido
./run.sh --gauntlet --only p7_tui
./run.sh --gauntlet --only interface
```

---

*"Arquivos grandes mascaram responsabilidades misturadas." -- princípio de coesão*
