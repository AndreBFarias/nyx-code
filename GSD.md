# GSD — Getting Shit Done (Nyx-Code)

**Arquivo para execução rápida. Zero floreio.** Tudo que uma session nova precisa para executar uma sprint sem o usuário ter que reexplicar o projeto.

---

## Quick-ref

| Ação | Comando |
|------|---------|
| Próxima sprint a executar | `cat EXECUTAR_SPRINT.md` |
| Atualizar esse arquivo | `python scripts/update_next_sprint.py` |
| Checar invariantes agora | `bash scripts/sprint_invariants.sh` |
| Subir Nyx (Ollama+Proxy+CLI) | `./run.sh` |
| Rodar Gauntlet | `./run.sh --gauntlet` |
| Rodar fase específica | `./run.sh --gauntlet --only <fase>` |
| Modo headless (JSON) | `./run.sh --headless` |

---

## Arquitetura do dia (resumo)

```
usuário → run.sh → Ollama (:11435) → GPU
                 → Proxy  (:11436) → think adaptativo → Ollama
                 → Nyx CLI (TUI)   → Proxy
                     ├── AgentLoop (nyx/agent/loop.py)
                     ├── 34 tools no registry
                     ├── 50 commands slash (/help, /commit, ...)
                     └── 10 services
```

Portas, URLs, modelo: `nyx/config/defaults.py` (fonte única, ADR-AUDIT-FIX-03).

---

## Regras invioláveis

- **Local First** (ADR-001): zero cloud.
- **Zero emoji** (ADR-004), **zero menção a IA** (ADR-005), **PT-BR com acento** (ADR-006).
- **Integração obrigatória** (ADR-013): tools no registry, commands registrados, services importados.
- **Testes via Gauntlet** (ADR-014, ADR-020): sem pytest solto, sempre via `./run.sh --gauntlet`.
- **Zero mocks** (ADR-010): testes contra infra real.
- **Render layer** (ADR-024): `print()` só em `nyx/cli.py` e `nyx/agent/output.py`.

---

## Protocolo anti-gambiarra (obrigatório em TODA sprint)

```bash
# ANTES
bash scripts/sprint_invariants.sh > /tmp/inv_before.txt 2>&1
FAIL_BEFORE=$(grep -c "^\[FAIL\]" /tmp/inv_before.txt)

# IMPLEMENTAR (seguindo o arquivo da sprint em producao/)

# DEPOIS
bash scripts/sprint_invariants.sh > /tmp/inv_after.txt 2>&1
FAIL_AFTER=$(grep -c "^\[FAIL\]" /tmp/inv_after.txt)

# REGRA BINÁRIA
[ "$FAIL_AFTER" -le "$FAIL_BEFORE" ] || { echo "REGRESSÃO — reverter"; git reset --hard HEAD~1; exit 1; }

# PROOF-OF-WORK (colar no relatório)
diff /tmp/inv_before.txt /tmp/inv_after.txt
```

Ler também:
- `dev-journey/08-templates/GAMBIARRAS_POR_SPRINT.md` §"Catálogo Universal" → 20 padrões de gambiarra.
- `dev-journey/08-templates/GAMBIARRAS_POR_SPRINT.md` §"<ID>" → bypass-paths específicos por sprint.
- `dev-journey/08-templates/GAMBIARRAS_POR_SPRINT.md` §"Matriz" → quais invariantes cada sprint fecha.
- `dev-journey/08-templates/REVIEWER_PROTOCOL.md` → como o reviewer valida após conclusão.
- `dev-journey/08-templates/PROJECT_SNAPSHOT.md` → estado atual (contagens, portas, ADRs).

---

## Fluxo completo de uma sprint (10 passos — fonte única)

1. `cat EXECUTAR_SPRINT.md` → pega o ID e o prompt já preenchido.
2. Abre **session nova** de Claude Opus 4.7 (sem subagentes, salvo autorização explícita).
3. Cola o prompt. A IA executora lê: o arquivo da sprint + GAMBIARRAS_POR_SPRINT.md (Universal + §ID).
4. IA roda `bash scripts/sprint_invariants.sh > /tmp/inv_before.txt 2>&1` e mostra `FAIL_BEFORE`.
5. IA apresenta plano e pergunta dúvidas **antes** de editar código.
6. IA implementa seguindo literalmente o arquivo da sprint.
7. IA roda `bash scripts/sprint_invariants.sh > /tmp/inv_after.txt 2>&1` e cola o diff.
8. IA cola output bruto dos comandos de verificação da sprint.
9. IA commit atômico + `git mv producao→concluidos` + `python scripts/update_next_sprint.py`.
10. Reviewer valida conforme `dev-journey/08-templates/REVIEWER_PROTOCOL.md`.

**Regra binária:** `FAIL_AFTER <= FAIL_BEFORE`. Caso contrário, regressão → `git reset --hard HEAD~1` e refazer.

**Se qualquer passo falhar:** sprint fica **BLOQUEADA** com motivo de 1 linha; pode virar sprint nova (regra "nenhum débito para trás").

*Este fluxo é citado por `CLAUDE.md §próxima sprint` e `EXECUTAR_SPRINT.md §Prompt`. Atualizar aqui, não duplicar.*

---

## Estado agora

- **Onda 22 em execução** (redesign UX + visão + deploy).
- Progresso: ver `dev-journey/06-sprints/SPRINT_ORDER_MASTER.md` tabela da Onda 22.
- Próxima sprint: ver `EXECUTAR_SPRINT.md` (auto-atualizado).

---

## Arquivos-bússola

| O que você quer saber | Onde |
|-----------------------|------|
| Próxima sprint + prompt | `EXECUTAR_SPRINT.md` |
| Ordem exata de execução | `dev-journey/06-sprints/SPRINT_ORDER_MASTER.md` |
| Detalhe da sprint | `dev-journey/06-sprints/producao/SPRINT_<ID>.md` |
| Como NÃO ser enganado | `dev-journey/08-templates/GAMBIARRAS_POR_SPRINT.md` |
| Regras universais | `CLAUDE.md` |
| Decisões arquiteturais | `dev-journey/03-decisions/ADR_*.md` |
| Auditoria mais recente | `dev-journey/07-reports/AUDIT_EXT_2026_04_18.md` |

---

*"O trabalho feito é melhor que o trabalho perfeito que nunca sai." -- anônimo*
