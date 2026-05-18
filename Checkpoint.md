# Checkpoint — sessão 2026-05-17 (janela final)

> Working state. **Não commitar** (untracked, igual a `assets/` antes do DEPLOY-02).

---

## TL;DR

**29 sprints concluídas (parciais inclusas) + 30 commits pushed.**

- Todas as sprints PENDENTES que uma IA pode fechar foram fechadas nesta janela.
- 7 sprints **BLOQUEADAS** restantes exigem execução humana específica:
  - **VALIDATE-FINAL-01** (CRÍTICA, release): 30 screenshots + 47 commands manuais + 5 runs benchmark + install em VM Docker + 34 tools em fluxo natural.
  - **COCKPIT-02..05** (4 sprints, ALTA/MÉDIA): vendoring xterm.js + design visual humano + headless browser + Chrome MCP.
  - **UX-COCKPIT-EXPERIENCE-01** (MÉDIA): depende COCKPIT-03.
  - **UX-AGENCY-02** (ALTA): cancel asyncio em tool em curso (precisa REPL real para testar).
  - **UX-PROGRESSION-02** (BAIXA): refactor amplo das ~50 mensagens (curadoria humana).
- `EXECUTAR_SPRINT.md` reporta "nenhuma sprint PENDENTE".

---

## Commits desta janela (5bc4354 → c7d27eb)

| # | Hash | Sprint |
|---|------|--------|
| 1 | 73aae9b | feat(UX-LOOP-VISIBILITY-01) |
| 2 | 0d0a9b6 | fix(INFRA-SANITIZER-FIX-02) |
| 3 | 843977a | feat(VISION-01) |
| 4 | 3e71d22 | feat(VISION-02) |
| 5 | 1711e5d | fix(VISION-03) |
| 6 | 2ced6f8 | feat(SESSION-RESUME-01) |
| 7 | 9030c99 | feat(DEPLOY-01A) |
| 8 | e37c491 | feat(DEPLOY-01B) |
| 9 | 75f9dd7 | feat(DEPLOY-02) |
| 10 | 1818a77 | feat(ONBOARDING-01) |
| 11 | 2a31b13 | feat(HELP-EXAMPLES-01) |
| 12 | e084da1 | feat(UX-EXTRA-01) |
| 13 | 63e9130 | chore(VALIDATE-FINAL-01 BLOQUEADA) |
| 14 | 0e2dc71 | feat(UX-PARITY-01) |
| 15 | a24a4ad | feat(MCP-SERVER-01) |
| 16 | 511dcb3 | feat(PLUGINS-01) |
| 17 | 6003759 | feat(OUTPUT-STYLES-01) |
| 18 | 38f425c | feat(HOOKS-DYNAMIC-01) |
| 19 | db2ee91 | fix(LANG-PROMPT-ACENT-01) |
| 20 | 4769f80 | feat(SBOM-REGISTRY-01) |
| 21 | d042f23 | feat(SBOM-REGISTRY-02) |
| 22 | cd6fcaf | feat(SBOM-REGISTRY-03) |
| 23 | 62b9430 | feat(COCKPIT-01) |
| 24 | 4a79646 | feat(UX-LOOP-01) |
| 25 | ae24069 | feat(UX-AGENCY-01) |
| 26 | 57ca6d4 | feat(UX-PROGRESSION-01) |
| 27 | 175ca00 | refactor(INFRA-CLI-SPLIT-01) |
| 28 | 5f58af5 | feat(MCP-SERVER-02) |
| 29 | c7d27eb | feat(anti-débito fases Gauntlet) |

Mais 1 commit chore(VALIDATE-FINAL-01 BLOQUEADA) -- total **30 commits**.

---

## Detecção crítica do início

**Drift do sanitizer pós-INFRA-SANITIZER-FIX-01:** 27 arquivos modificados em janela de 40ms (script batch) com glifos `○ ◐ ●` removidos, INCLUSIVE o próprio `scripts/sprint_invariants.sh`. Invariante #14 antigo (grep textual) foi sabotado para validar strings vazias. Solução: INFRA-SANITIZER-FIX-02 reescreveu o check em python contando codepoints — imune a strip + reescrita coerente.

---

## Estado runtime final

- **Smoke:** `boot ok`
- **Invariantes:** PASS 14, FAIL 0
- **audit_help_coverage:** 60/60 OK (com `/?`, `/cancel`)
- **sbom_init / sbom_sync:** 62/62 sincronizadas em ambos os sentidos
- **Gauntlet phases novas:** install, loop, mcp, plugins, hooks_dynamic, sessao, vision
- **cli.py:** 1361L (era 1450L; meta 800L; INFRA-CLI-SPLIT-02 anti-débito para resto)
- **Working tree:** apenas Checkpoint.md (este, untracked)

---

## Próxima sessão

### Como iniciar (3 passos)

1. Abra terminal em `/home/andrefarias/Desenvolvimento/Nyx-Code`, rode `claude`.
2. Cole o bloco de `PROMPT_VALIDADOR_INTEGRADOR.md` §"Bloco para colar".
3. Diga `siga` (ou `promove I-01..I-11 e executa`). O Claude faz o ciclo
   completo: smoke + invariantes + próxima sprint + commit + push + repete.

### Roteiro de retomada

1. Validar BLOQUEADAS humanas: VALIDATE-FINAL-01 é a mais crítica (gate v1.0).
2. Cockpit completo (COCKPIT-02..05): exige vendoring + design + headless.
3. Anti-débito de refinamento (UX-AGENCY-02, UX-PROGRESSION-02, INFRA-CLI-SPLIT-02).
4. 62 stubs RASCUNHO (`SPRINT_FEAT_<id>_TEST_01.md`) prontos para promoção em batch.

### Checagem rápida do estado

```bash
cd /home/andrefarias/Desenvolvimento/Nyx-Code
git log --oneline -10                                    # últimos commits
cat EXECUTAR_SPRINT.md | head -5                         # próxima sprint
bash scripts/sprint_invariants.sh | tail -5              # PASS=14 FAIL=0
./run.sh --smoke                                         # boot ok
./venv/bin/python scripts/audit_help_coverage.py | tail -1  # 60/60 OK
./venv/bin/python scripts/sbom_init.py --check           # 62/62 sincronizadas
```

---

*Atualizado: 2026-05-17 após c7d27eb (29 sprints, 30 commits).*
