## 0. SPEC (machine-readable)

```yaml
sprint:
  id: P5-A
  title: "Git & GitHub commands -- /branch, /issue, /pr, /rewind"
  touches:
    - path: nyx/agent/commands.py
      reason: "4 novos commands de git/GitHub"
    - path: nyx/agent/git_ops.py
      reason: "Funções git branch, git log, rewind"
    - path: scripts/gauntlet/nyx_gauntlet.py
      reason: "4 testes novos"
  origin:
    primary: "openclaud/src/commands/branch/"
    secondary: "openclaud/src/commands/issue/"
  tests:
    - cmd: "./run.sh --gauntlet --only p5_git"
      timeout: 30
  acceptance_criteria:
    - "/branch lista, cria, troca branches"
    - "/issue cria/lista issues via gh CLI"
    - "/pr expande /review com comentários"
    - "/rewind desfaz últimas N ações do agente"
```

---

# Sprint P5-A -- Git & GitHub commands

**Status:** CONCLUIDA (header corrigido em MASTER-CLEANUP-02 2026-05-20; presença em concluidos/ implica CONCLUIDA conforme convenção do projeto)
**Data:** 2026-04-05
**Prioridade:** MÉDIA
**Tipo:** Port (TS -> Python)
**Dependências:** P3-D
**Desbloqueia:** P5-C

---

## Implementação

### /branch
- `/branch` -- lista branches locais
- `/branch nome` -- cria e troca para branch
- `/branch -d nome` -- deleta branch
- Usa `git_ops.py` expandido

### /issue
- `/issue` -- lista issues abertas (via `gh issue list`)
- `/issue N` -- mostra issue N (via `gh issue view N`)
- `/issue create titulo` -- gera prompt para agent criar issue
- Requer `gh` CLI instalado

### /pr
- `/pr` -- lista PRs abertas (via `gh pr list`)
- `/pr N` -- mostra PR N com comentários
- Expandir /review existente com mais contexto
- Gera prompt para o agent analisar

### /rewind
- `/rewind` -- desfaz última ação do agent
- `/rewind N` -- desfaz últimas N ações
- Remove entradas do histórico da sessão
- Desfaz file writes/edits se possível (git checkout)

### Testes Gauntlet

| ID | Nome | Validação |
|----|------|-----------|
| P5G-01 | /branch lista | Retorna branches, contém "main" |
| P5G-02 | /issue interface | Retorna output ou mensagem sobre gh CLI |
| P5G-03 | /pr interface | Retorna output ou mensagem sobre gh CLI |
| P5G-04 | /rewind registrado | Command existe e retorna help |

## Verificação

- [ ] 4 commands registrados
- [ ] /branch funciona com git real
- [ ] /issue e /pr detectam se gh está disponível
- [ ] /rewind remove entradas do histórico
- [ ] 4 testes Gauntlet passando

---

*"Quem controla o passado controla o futuro." -- George Orwell*
