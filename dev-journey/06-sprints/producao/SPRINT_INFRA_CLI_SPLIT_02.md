# SPRINT INFRA-CLI-SPLIT-02 — Reduzir nyx/cli.py para <800L (anti-débito)

## 0. SPEC

```yaml
sprint:
  id: INFRA-CLI-SPLIT-02
  title: "Extrair handlers de sentinela e keybindings de run_repl para cli_handlers.py + cli_keybindings.py"
  onda: 23
  bloco: 23.1 Estabilização
  prioridade: BAIXA
  tipo: Refactor
  dependencias: [INFRA-CLI-SPLIT-01]
  origem: "INFRA-CLI-SPLIT-01 extraiu helpers (cli_helpers.py) e reduziu cli.py de 1450 -> 1361 linhas. Limite GUIDE.md §6 é 800L; ainda 561L acima. Refactor maior requer cuidado com closures e estado compartilhado de run_repl."

  touches:
    - /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/cli.py
  creates:
    - /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/cli_handlers.py
    - /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/cli_keybindings.py

  acceptance_criteria:
    - "wc -l nyx/cli.py < 800"
    - "Smoke + gauntlet rapido + p7_tui + interface 100%"
    - "Zero mudança de comportamento externo do REPL"
    - "Zero import circular entre cli_*.py"
```

---

**Status:** PENDENTE
**Data:** 2026-05-17
**Origem:** anti-débito de INFRA-CLI-SPLIT-01 (corte parcial; chegamos a 1361L; meta 800L)
**Modelo obrigatório:** claude-opus-4-7 (sem subagentes)
