## 0. SPEC

```yaml
sprint:
  id: VALIDATE-ONDA-21
  title: "Validação visual das 7 sprints da Onda 21 (TUI-FIX-01..07)"
  onda: 22
  bloco: 2.7
  prioridade: ALTA
  tipo: Audit
  dependencias: [VALIDATE-ONDA-20]
  desbloqueia: [UX-DESIGN-01]

  touches:
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/dev-journey/06-sprints/SPRINT_ORDER_MASTER.md
      reason: "Marcar TUI-FIX-01..07 como CONCLUIDA ou BLOQUEADA"

  creates:
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/dev-journey/07-reports/RELATORIO_VALIDACAO_ONDA_21.md

  removes: []

  forbidden:
    - "Validar só automatizado — fixes são visuais por natureza"
    - "Pular fixes com motivo 'provavelmente funciona'"
    - "Marcar CONCLUIDA sem screenshot ou transcrição de sessão"

  tests:
    - cmd: "./run.sh (interativo)"
      deve_passar: "checklist validado pelo usuário"
    - cmd: "ls dev-journey/06-sprints/concluidos/ | grep 'TUI_FIX' | wc -l"
      esperado: "7"

  acceptance_criteria:
    - "7 sprints TUI-FIX decididas (CONCLUIDA ou BLOQUEADA)"
    - "Arquivos CONCLUIDA em concluidos/"
    - "Cada BLOQUEADA vira sprint nova com ID sequencial no master (nenhum débito solto)"
    - "RELATORIO_VALIDACAO_ONDA_21.md completo"
```

---

# Sprint VALIDATE-ONDA-21 — Validação TUI-FIX-01..07

**Status:** CONCLUIDA (header corrigido em MASTER-CLEANUP-02 2026-05-20; presença em concluidos/ implica CONCLUIDA conforme convenção do projeto)
**Data criação:** 2026-04-19
**Modelo obrigatório:** claude-opus-4-7 (sem subagentes)

---

## Contexto do projeto (snapshot)

> - SPRINT_ORDER_MASTER linhas 196-204: 7 sprints TUI-FIX-01..07 "EM VALIDAÇÃO".
> - Escopo fechado via screenshots do usuário em 2026-04-17.
> - Validação pendente — fixes são visuais (banner, streaming, popup, bypass toggle, image paste, sandbox error, usabilidade geral).

---

## Problema

7 fixes UX implementados mas não validados pelo olho humano. Onda 22 (UX-DESIGN-01) reformula esses mesmos pontos; se algum fix ficou quebrado, há risco de regressão mascarada.

---

## Solução proposta

Sessão interativa guiada, uma sprint por vez. Para cada uma, comparar comportamento atual com screenshot original da 2026-04-17. Registrar sim/não + observação.

---

## Checklist por sprint

### TUI-FIX-01 — Banner único e limpo
- [ ] Ao iniciar `./run.sh`, banner renderiza **uma única vez**.
- [ ] Nenhum caractere ASCII corrompido (sem `\x1b[` bruto, sem �).
- [ ] Banner ocupa largura esperada (não quebra em terminal 80 cols).

### TUI-FIX-02 — Streaming sem resposta duplicada
- [ ] Ao receber resposta do LLM, texto aparece via streaming (token-by-token).
- [ ] Ao final, **não aparece** bloco duplicado no render final.

### TUI-FIX-03 — Popup slash automático
- [ ] Digitar `/` abre popup imediatamente (sem espaço).
- [ ] Digitar `/sta` filtra para `/status`.
- [ ] Esc fecha popup e preserva input atual.

### TUI-FIX-04 — Shift+Tab toggle bypass
- [ ] Shift+Tab toggla modo bypass (auto-approve tools).
- [ ] Bottom toolbar mostra `[bypass ON/OFF]` em accent color.

### TUI-FIX-05 — Ctrl+V + xclip paste imagem
- [ ] Com imagem no clipboard, Ctrl+V injeta `[Image #N]` no input.
- [ ] Imagem é salva em `~/.nyx/pastes/` (ou equivalente).
- [ ] Referência `[Image #N]` resolve no próximo request (vide VISION-01).

### TUI-FIX-06 — Sandbox erro colorido em PT-BR
- [ ] Tool rejeitada por sandbox exibe mensagem em vermelho, PT-BR.
- [ ] Motivo objetivo: "permissão negada", "fora do workspace", etc.

### TUI-FIX-07 — Usabilidade geral
- [ ] Footer em toolbar (não em linha fixa).
- [ ] Paste > X linhas colapsa (coerente com USER_INPUT_COLLAPSE_LINES).
- [ ] `/help` categorizado (git, ui, debug, mem, sistema).
- [ ] Indicador de memória ativo na toolbar.
- [ ] Comandos `/memory`, `/paste`, `/tools`, `/recall` respondem.

---

## Procedimento

```bash
# para cada TUI-FIX-NN:
./run.sh
# executar checklist
# anotar no relatório

# ao final, commit + git mv
```

---

## Comandos de verificação

```bash
ls dev-journey/06-sprints/producao/ | grep TUI_FIX
# esperado: vazio (todas migraram) OU só BLOQUEADAS (com motivo)

ls dev-journey/06-sprints/concluidos/ | grep TUI_FIX | wc -l
# esperado: contagem compatível
```

---

## Critério binário de aceite

- [ ] 7 TUI-FIX decididas (status final gravado)
- [ ] CONCLUIDA → arquivo em concluidos/
- [ ] BLOQUEADA → sprint nova criada (ex: UX-DESIGN-02 ou TUI-FIX-08) com ID na ordem
- [ ] SPRINT_ORDER_MASTER atualizado
- [ ] RELATORIO_VALIDACAO_ONDA_21.md completo
- [ ] Commit `docs: valida Onda 21 (TUI-FIX) — 7 sprints fechadas`

---

## Gambiarras específicas

- **Checklist rápido demais** — cada item precisa observação literal ou screenshot.
- **BLOQUEADA vira "débito" sem sprint** — proibido (regra "nenhum débito para trás").
- **Aglutinar os 7 no relatório** — cada um tem sua seção.

---

## Riscos

| Risco | Mitigação |
|-------|-----------|
| TUI-FIX-05 (clipboard) pode exigir xclip instalado | Pré-check `command -v xclip`; se faltar, BLOQUEADA com motivo específico |
| TUI-FIX-04 (Shift+Tab) pode não funcionar em todos terminais | Testar em GNOME Terminal (padrão da máquina) e documentar |

---

*"Quem não revê o próprio trabalho, constrói sobre areia." -- anônimo*
