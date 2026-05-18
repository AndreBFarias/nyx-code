# SPRINT TUI-REDESIGN-25-13 — /help em 3 colunas (Sessão · Contexto · Modelo)

## 0. SPEC

```yaml
sprint:
  id: TUI-REDESIGN-25-13
  title: "/help reagrupa 61 commands em 3 colunas categorizadas + descrição inline"
  onda: 25
  bloco: 25.5 Comandos & encerramento
  prioridade: MÉDIA
  tipo: UX
  dependencias: [TUI-REDESIGN-25-01]
  desbloqueia: []
  origem: "Auditoria audit.jsx -- problema P15 (Sem hint de comandos)"

  touches:
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/agent/commands/core.py
      reason: "cmd_help (linha 38-63) reorganiza output em 3 colunas"
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/agent/commands/_registry.py
      reason: "format_help expõe agrupamento por categoria + descrição curta"

  forbidden:
    - "Quebrar /help <cmd> (mostra detalhes de um comando específico)"
    - "Esconder commands em modo plain-text"

  tests:
    - cmd: "echo '/help' | ./run.sh --headless --no-resume-prompt 2>&1 | grep -c 'Sessão\\|Contexto\\|Modelo'"
      timeout: 30
      deve_passar: ">= 3"
    - cmd: "bash scripts/sprint_invariants.sh"
      timeout: 60
      deve_passar: "14/14"

  acceptance_criteria:
    - "/help imprime 3 colunas com títulos: Sessão · Contexto · Modelo"
    - "Cada coluna lista commands relevantes + 1 linha de descrição"
    - "/help <cmd> mantém detalhes completos (não regride)"
    - "Layout responsivo: 1 coluna em terminais <80 cols"
    - "Smoke ok + invariantes 14/14"
```

---

# Sprint TUI-REDESIGN-25-13

**Status:** PENDENTE
**Data criação:** 2026-05-18
**Modelo obrigatório:** claude-opus-4-7

## Contexto

P15: hoje `/help` lista commands em fluxo único sem agrupamento visual. Com 61 commands, fica difícil descobrir o que existe.

## Solução proposta

Reagrupar em 3 colunas:

- **Sessão** (gestão de turno/contexto/saída): /resume, /compact, /context, /clear, /quit, /stats, /cancel
- **Contexto** (projeto, memória, sandbox): /memory, /add-dir, /init, /sandbox, /cd, /skills, /files, /paste
- **Modelo** (config & introspecção do agente): /model, /aesthetic, /output-style, /permissions, /hooks, /theme, /config, /env, /doctor

Restantes (Debug/Git/Etc) ficam em segundo bloco abaixo.

Layout:
```
Sessão           Contexto           Modelo
/resume <id>     /memory list       /model
  retomar...       memória cross...   trocar...
/compact          /add-dir <p>       /aesthetic
  compactar...      adicionar...        mudar tema...
...               ...                ...
```

## Critério binário

- [ ] /help mostra 3 colunas categorizadas
- [ ] Cada item tem descrição inline
- [ ] /help <cmd> preserva detalhes
- [ ] Responsivo (1 coluna se <80 cols)
- [ ] Smoke + invariantes 14/14
- [ ] Commit `feat(TUI-REDESIGN-25-13): /help em 3 colunas categorizadas`

## Invariantes

#14.

## Anti-débito

- Busca interativa (`/help busca` ou fuzzy) fica fora.

## Verificação

```bash
echo '/help' | ./run.sh --headless --no-resume-prompt
bash scripts/sprint_invariants.sh
```

## Rollback

`git reset --hard HEAD~1`

---

*"Comando que não se acha não existe." -- TUI-REDESIGN-25-13*
