# SPRINT INFRA-OOM-01 — Controle de OOM (oom_score_adj + ulimit + monitor)

## 0. SPEC (machine-readable)

```yaml
sprint:
  id: INFRA-OOM-01
  title: "Controle de OOM via oom_score_adj + ulimit + script de monitor"
  onda: 24
  bloco: 24.1 Infra resiliente
  prioridade: ALTA
  tipo: Infra
  dependencias: []
  desbloqueia: [VALIDATE-FINAL-01]

  touches:
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/install.sh
      reason: "Adicionar fase 11 - configurar oom_score_adj e ulimit no install"
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/run.sh
      reason: "Source bin/nyx-runtime-limits.sh no início se existir"
  creates:
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/bin/nyx-runtime-limits.sh
      reason: "Aplica ulimit -v 8GB + oom_score_adj -100 ao shell que invoca Nyx"
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/scripts/check_oom.sh
      reason: "Monitor de OOM (lê /proc/meminfo + dmesg | grep OOM)"
  removes: []

  n_to_n_pairs:
    - descricao: "Total de fases do install.sh subiu de 10 para 11"
      paths:
        - install.sh
        - README.md

  forbidden:
    - "Setar oom_score_adj positivo (kill mais agressivo) - usar valores negativos"
    - "Quebrar idempotência do install.sh"
    - "Hardcode de senha sudo (Vide INSTALL-SUDO-01)"

  tests:
    - cmd: "./run.sh --smoke && cat /proc/self/oom_score 2>/dev/null || true"
      timeout: 30
      deve_passar: "boot ok"
    - cmd: "bash scripts/check_oom.sh"
      timeout: 10
      deve_passar: "exit 0 (sem OOM atual)"

  acceptance_criteria:
    - "bin/nyx-runtime-limits.sh aplica ulimit -v 8000000 (8GB virt mem)"
    - "bin/nyx-runtime-limits.sh tenta echo -100 > /proc/self/oom_score_adj (best effort; sem sudo)"
    - "run.sh source nyx-runtime-limits.sh no início (se existir)"
    - "install.sh fase 11 cria/atualiza bin/nyx-runtime-limits.sh idempotente"
    - "scripts/check_oom.sh: cat /proc/meminfo + dmesg --since='1 hour ago' | grep -iE 'oom|killed' || true"
    - "Smoke ok"
    - "Invariantes 14/14"
```

---

# Sprint INFRA-OOM-01 — Controle de OOM

**Status:** CONCLUIDA (header corrigido em MASTER-CLEANUP-02 2026-05-20; presença em concluidos/ implica CONCLUIDA conforme convenção do projeto)
**Data criação:** 2026-05-18
**Modelo obrigatório:** claude-opus-4-7

---

## Contexto

Máquina-alvo do usuário (neofetch da sessão 2026-05-18): RAM 14.81 GiB com **swap 80%** já consumido antes do boot do Nyx. RTX 3050 4GB (VRAM 195/4096 MiB, 4%). Boot do Nyx + Ollama qwen2.5-coder:3b consome ~2.5GB VRAM + ~2GB RAM. Em sessões longas com cockpit + Chrome MCP, OOM-killer pode matar o Ollama silenciosamente. Hoje o `install.sh` não tem nenhum controle.

### Sintoma observável

`dmesg | grep -i oom` em sessões longas mostra "Out of memory: Killed process N (ollama)". Ollama reinicia, modelo descarrega, próximo prompt sofre cold start 20s+.

---

## Solução proposta

3 camadas:

1. **bin/nyx-runtime-limits.sh** — sourced pelo run.sh:
```bash
#!/usr/bin/env bash
# Limites de runtime aplicados ao shell que invoca Nyx
ulimit -v 8000000 2>/dev/null || true   # 8GB virt mem por processo
ulimit -m 8000000 2>/dev/null || true   # 8GB phys mem
# oom_score_adj negativo = menos likely kill (sem sudo, best effort)
echo -100 > /proc/self/oom_score_adj 2>/dev/null || true
```

2. **run.sh** — source no início:
```bash
[ -f "${SCRIPT_DIR}/bin/nyx-runtime-limits.sh" ] && source "${SCRIPT_DIR}/bin/nyx-runtime-limits.sh"
```

3. **scripts/check_oom.sh** — diagnóstico:
```bash
#!/usr/bin/env bash
echo "Memória:"
free -h
echo ""
echo "Swap:"
swapon --show
echo ""
echo "OOM no kernel (última hora):"
journalctl --since='1 hour ago' -k 2>/dev/null | grep -iE 'oom|killed' || echo "(nenhum)"
echo ""
echo "Processos top RAM:"
ps aux --sort=-%mem | head -10
```

---

## Comandos de verificação

```bash
# 1. Sanity inicial
free -h
swapon --show

# 2. Aplicar limites e bootar
./run.sh --smoke

# 3. Verificar oom_score do processo nyx
NYX_PID=$(pgrep -f "python.*nyx" | head -1)
[ -n "$NYX_PID" ] && cat /proc/$NYX_PID/oom_score

# 4. Monitor
bash scripts/check_oom.sh

# 5. Invariantes
bash scripts/sprint_invariants.sh | tail -5
```

---

## Critério binário de aceite

- [ ] `bin/nyx-runtime-limits.sh` existe, é executável, aplica ulimit + oom_score_adj
- [ ] `run.sh` source o limits.sh no início
- [ ] `scripts/check_oom.sh` reporta memória, swap, OOM kernel, top procs
- [ ] `install.sh` fase 11 cria/atualiza limits.sh idempotente
- [ ] README seção "Replicação" cita o controle de OOM
- [ ] `./run.sh --smoke` ok com limits aplicados
- [ ] Invariantes 14/14
- [ ] Commit `feat(INFRA-OOM-01): controle OOM via oom_score_adj + ulimit + monitor`

---

## Riscos

| Risco | Mitigação |
|---|---|
| ulimit pode bloquear processos legítimos | 8GB é confortável para qwen2.5-coder:3b (~2GB) + buffers + chrome |
| oom_score_adj sem sudo é best-effort | Documentar; usuário pode rodar `sudo ./install.sh` para aplicar via systemd-run |
| Quebrar idempotência | Test: rodar 2x install.sh, diff deve ser vazio |

---

*"OOM-killer prefere quem deve menos. Que Nyx deva pouco." — INFRA-OOM-01*
