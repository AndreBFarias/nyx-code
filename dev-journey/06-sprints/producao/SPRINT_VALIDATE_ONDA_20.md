## 0. SPEC

```yaml
sprint:
  id: VALIDATE-ONDA-20
  title: "Validação visual e funcional das 7 sprints da Onda 20 (TUI-01/02/03 + CTX-01/02/03/04)"
  onda: 22
  bloco: 2.7
  prioridade: ALTA
  tipo: Audit
  dependencias: [INFRA-GAUNTLET-01]
  desbloqueia: [VALIDATE-ONDA-21, UX-DESIGN-01]

  touches:
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/dev-journey/06-sprints/SPRINT_ORDER_MASTER.md
      reason: "Marcar as 7 sprints validadas como CONCLUIDA"
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/dev-journey/07-reports/RELATORIO_VALIDACAO_ONDA_20.md
      reason: "Registro do resultado (criar)"

  creates:
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/dev-journey/07-reports/RELATORIO_VALIDACAO_ONDA_20.md

  removes: []

  forbidden:
    - "Marcar sprint como CONCLUIDA sem executar o checklist visual"
    - "Pular sprints com critério 'opcional' (CTX-04 pode ser deferida MAS precisa ser decidida explicitamente)"
    - "Validar só automatizado — checklist é visual por natureza"

  tests:
    - cmd: "./run.sh (interativo)"
      deve_passar: "checklist validado pelo usuário"
    - cmd: "ls dev-journey/06-sprints/concluidos/ | grep -E 'TUI_0[1-3]|CTX_0[1-4]' | wc -l"
      esperado: ">= 6 (CTX-04 opcional)"

  acceptance_criteria:
    - "Cada uma das 7 sprints tem decisão registrada: CONCLUIDA ou DEFERIDA com motivo"
    - "Arquivos movidos de producao/ para concluidos/ para as CONCLUIDA"
    - "SPRINT_ORDER_MASTER atualizado"
    - "RELATORIO_VALIDACAO_ONDA_20.md lista screenshots/observações por sprint"
```

---

# Sprint VALIDATE-ONDA-20 — Validação Onda 20

**Status:** PENDENTE
**Data criação:** 2026-04-19
**Modelo obrigatório:** claude-opus-4-7 (sem subagentes)

---

## Contexto do projeto (snapshot)

> - SPRINT_ORDER_MASTER linhas 180-189 listam 7 sprints da Onda 20 "EM VALIDAÇÃO" desde 2026-04-17.
> - Código foi implementado e gauntlet passou na época. Falta validação visual interativa do usuário.
> - Arquivos ainda em `producao/`: TUI-01, TUI-02, TUI-03, CTX-01, CTX-02, CTX-03, CTX-04.

---

## Problema

7 sprints em limbo há 2 dias. Nada garante que feature X ainda funciona após 5 sprints de refactor (AUDIT-FIX-05/07, DEBT-01/03). Precisamos rodar checklist visual antes de avançar para UX-DESIGN-01, que reformula o mesmo código.

---

## Solução proposta

Sessão interativa com o usuário. Para cada sprint, rodar `./run.sh` e conferir checklist abaixo. Usuário confirma sim/não. Cada sim → sprint CONCLUIDA (hash do último commit relevante); cada não → BLOQUEADA com motivo. CTX-04 pode ser DEFERIDA se usuário não quiser feature.

---

## Checklist de validação

### TUI-01 — Higiene
- [ ] Banner único (sem duplicação).
- [ ] Logs do boot (ollama/proxy) silenciados ou reduzidos.
- [ ] Tool calls formatados como `⏺ nome(arg)` em accent color.

### TUI-02 — Boxes + multiline
- [ ] User input renderizado em box `╭─...─╮` / `╰─...─╯`.
- [ ] Tool call com bullet `⏺` e linha de fechamento `└─`.
- [ ] Input > 8 linhas colapsa (veremos colapso adequado após UX-LAYOUT-01).

### TUI-03 — Footer + popup
- [ ] Footer 1 linha na parte inferior com info de contexto (ctx %, bypass, etc).
- [ ] Digitar `/` abre popup navegável de comandos.
- [ ] ↑↓ navega; Enter seleciona; Esc fecha.

### CTX-01 — Summarizer
- [ ] Após N iterações com contexto cheio, `maybe_summarize()` roda.
- [ ] Resumo é injetado como mensagem system.
- [ ] Grep log: `logger.info("sumarizando")` ou similar aparece.

### CTX-02 — Memory
- [ ] Pasta `~/.nyx/memory/` existe após primeira execução.
- [ ] Fato escrito em uma sessão é lido na próxima.
- [ ] Comando `/memory` lista facts armazenados.

### CTX-03 — RepoMap
- [ ] RepoMap gera mapa do repo (via AST se tree-sitter instalado, senão fallback textual).
- [ ] ADR-021 (dep opcional) respeitada.
- [ ] Grep em repositório grande não trava UI (roda em background).

### CTX-04 — Plano ativo (opcional)
- [ ] Comando `/plan` inicia plano; `/plan done` termina.
- [ ] Se usuário não quer feature, DEFERIR com motivo.

---

## Procedimento

```bash
# para cada sprint, em janela interativa:
./run.sh
# executar checklist acima
# anotar resultado em RELATORIO_VALIDACAO_ONDA_20.md

# ao final, para cada CONCLUIDA:
git mv dev-journey/06-sprints/producao/SPRINT_TUI_01_HIGIENE.md \
       dev-journey/06-sprints/concluidos/
# (repetir para cada sprint)

# atualizar SPRINT_ORDER_MASTER (marcar CONCLUIDA + hash do commit original)
# re-rodar:
python scripts/update_next_sprint.py
```

---

## Comandos de verificação

```bash
# 1. cada sprint validada migrou
ls dev-journey/06-sprints/producao/ | grep -E 'TUI_0[1-3]|CTX_0[1-4]'
# esperado: apenas as DEFERIDAS (ideal: vazio ou só CTX-04 se deferida)

# 2. concluidos tem entradas novas
ls dev-journey/06-sprints/concluidos/ | grep -E 'TUI_0[1-3]|CTX_0[1-4]' | wc -l
# esperado: >= 6

# 3. master atualizado
grep -E 'TUI-0[1-3]|CTX-0[1-4]' dev-journey/06-sprints/SPRINT_ORDER_MASTER.md | grep -c CONCLUIDA
# esperado: >= 6
```

---

## Critério binário de aceite

- [ ] Cada uma das 7 sprints tem status final gravado (CONCLUIDA / BLOQUEADA / DEFERIDA)
- [ ] Arquivos das CONCLUIDA migraram para `concluidos/`
- [ ] `SPRINT_ORDER_MASTER.md` reflete estado
- [ ] `RELATORIO_VALIDACAO_ONDA_20.md` descreve observação por sprint
- [ ] Se alguma BLOQUEADA: issue criada ou sprint de correção nova (nada pode ficar como débito)
- [ ] Commit `docs: valida Onda 20 (TUI+CTX) — 7 sprints fechadas`

---

## Gambiarras específicas

- **Marcar CONCLUIDA só por ler código** — proibido. Validação é visual+funcional, requer execução.
- **Dar OK em checklist sem rodar** — proibido. Output real no relatório.
- **Ignorar BLOQUEADA e seguir em frente** — proibido. Cada BLOQUEADA vira sprint nova (regra "nenhum débito para trás").
- **Aglutinar as 7 num só checkpoint** — proibido. Cada sprint tem decisão independente.

---

## Riscos

| Risco | Mitigação |
|-------|-----------|
| 5 sprints de refactor após implementação original podem ter quebrado feature | Esse é exatamente o ponto da sprint: descobrir |
| Usuário pode não ter disponibilidade para sessão interativa | Sprint roda em janelas de 15-30min por bloco de features; agendar com usuário |
| CTX-04 pode não ter sido implementada completamente | Já marcada "OPCIONAL"; DEFERIR é decisão válida |

---

*"O que não é validado não é real." -- Popper (paráfrase)*
