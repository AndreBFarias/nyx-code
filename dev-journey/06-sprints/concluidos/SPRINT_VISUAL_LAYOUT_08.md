# SPRINT VISUAL-LAYOUT-08 — Config NYX_AESTHETIC + flag + command

## 0. SPEC (machine-readable)

```yaml
sprint:
  id: VISUAL-LAYOUT-08
  title: "Configuração ergonômica: NYX_AESTHETIC env, --aesthetic flag, /aesthetic command"
  onda: 24
  bloco: 24.2 Visual Layout
  prioridade: MÉDIA
  tipo: Feature
  dependencias: [VISUAL-LAYOUT-01, VISUAL-LAYOUT-03]
  desbloqueia: []

  touches:
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/run.sh
      reason: "Aceitar --aesthetic <name> setando NYX_AESTHETIC antes do exec"
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/config/defaults.py
      reason: "NYX_AESTHETIC e NYX_ENTITY default lidos do ambiente"
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/.env.example
      reason: "Documentar NYX_AESTHETIC e NYX_ENTITY"
  creates:
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/agent/commands/aesthetic.py
      reason: "Novo command /aesthetic list/get/set"
  removes: []

  forbidden:
    - "Quebrar commands existentes"
    - "Comando que não respeita ADR-013 (Integração obrigatória)"

  tests:
    - cmd: "./run.sh --aesthetic arcano --smoke"
      timeout: 30
      deve_passar: "boot ok"
    - cmd: "echo '/aesthetic list' | ./run.sh --no-resume-prompt"
      timeout: 30
      deve_passar: "lista 5 aesthetics + 7 entities"

  acceptance_criteria:
    - "Flag --aesthetic <name> em run.sh seta NYX_AESTHETIC"
    - "/aesthetic command registrado em ToolRegistry/CommandRegistry"
    - "/aesthetic list → mostra 5 aesthetics + 7 entities"
    - "/aesthetic get → mostra atual"
    - "/aesthetic set <name> → muda runtime (não persistente)"
    - "audit_help_coverage 60+/60+ OK"
    - "Smoke ok"
```

---

# Sprint VISUAL-LAYOUT-08 — Config + flag + command

**Status:** PENDENTE
**Data criação:** 2026-05-18
**Modelo obrigatório:** claude-opus-4-7

---

## Contexto

VISUAL-LAYOUT-01/03/04/05 atendem o nível arquitetural. VISUAL-LAYOUT-08 oferece a ergonomia: como o usuário escolhe?

---

## Solução

1. `run.sh` aceita `--aesthetic <name>` e exporta `NYX_AESTHETIC` antes do exec.
2. `nyx/agent/commands/aesthetic.py` registra command `/aesthetic` com 3 subcommands: list, get, set.
3. `.env.example` documenta opções.

---

## Critério binário de aceite

- [ ] `run.sh --aesthetic arcano` muda banner/CLI
- [ ] `/aesthetic list` mostra 5 nomes
- [ ] `/aesthetic set arcano` muda em runtime
- [ ] `/aesthetic get` mostra atual
- [ ] audit_help_coverage não regride
- [ ] Smoke ok
- [ ] Commit `feat(VISUAL-LAYOUT-08): config NYX_AESTHETIC + flag + /aesthetic command`

---

*"Escolher é cuidar." — VISUAL-LAYOUT-08*
