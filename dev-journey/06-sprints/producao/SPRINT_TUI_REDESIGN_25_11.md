# SPRINT TUI-REDESIGN-25-11 — Erros de tool com ações sugeridas (a/b/c)

## 0. SPEC

```yaml
sprint:
  id: TUI-REDESIGN-25-11
  title: "Erro de tool emite 3 ações sugeridas com comandos chip: (a) /sandbox add (b) /cd (c) colar"
  onda: 25
  bloco: 25.4 Chain-of-thought, ferramentas e estrutura
  prioridade: ALTA
  tipo: UX
  dependencias: [TUI-REDESIGN-25-10]
  desbloqueia: []
  origem: "Auditoria audit.jsx -- problema P12 (Tratamento de erro sem solução)"

  touches:
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/agent/output.py
      reason: "render_error_with_actions(error_msg, actions=[(key, label, cmd), ...])"
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/agent/preflight.py
      reason: "Cada erro de preflight gera lista de ações curatáveis"
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/agent/tools/registry.py
      reason: "Helper que classifica erros conhecidos (sandbox, permission, syntax) e injeta ações padrão"

  forbidden:
    - "Executar ação sem confirmação do usuário (chip é sugestão, não auto-run)"
    - "Esconder erro original"

  tests:
    - cmd: "bash scripts/sprint_invariants.sh"
      timeout: 60
      deve_passar: "14/14"

  acceptance_criteria:
    - "Erro 'Fora do projeto Nyx-Code' lista: (a) /sandbox add X  (b) /cd X  (c) colar conteúdo"
    - "Erro de permissão lista: (a) /permissions add  (b) executar mesmo assim  (c) pular"
    - "Erro syntax lista: (a) /edit  (b) reler arquivo  (c) ignorar"
    - "Comandos aparecem em chip clicável (representação textual ok no terminal)"
    - "Smoke ok + invariantes 14/14"
```

---

# Sprint TUI-REDESIGN-25-11

**Status:** PENDENTE
**Data criação:** 2026-05-18
**Modelo obrigatório:** claude-opus-4-7

## Contexto

P12: hoje erro de tool emite só `[erro] Fora do projeto Nyx-Code: '/X/Y'`. Sem ação. Usuário precisa decorar o que fazer.

Visão redesenhada (audit.jsx):
```
●  read_file  ~/.../Checkpoint.md  1ms  erro

   Fora do projeto Nyx-Code.

   (a) /sandbox add ~/Desenvolvimento/Protocolo-Mob-Ouroboros
   (b) /cd ~/Desenvolvimento/Protocolo-Mob-Ouroboros
   (c) colar conteúdo aqui
```

## Solução proposta

1. `output.py` ganha `render_error_with_actions(msg, actions=[(key, label, cmd), ...])`.
2. `preflight.py` classifica erros e injeta ações padrão:
   - sandbox-violation → /sandbox add X, /cd X, colar
   - permission-denied → /permissions add, executar, pular
   - syntax-error → /edit, reler, ignorar
   - file-not-found → criar, /cd até dir certo, descartar
3. `registry.py` propaga error_type junto com mensagem (pode ser método novo `tool_result_with_actions`).

## Critério binário

- [ ] render_error_with_actions implementado
- [ ] preflight injeta ações para erro de sandbox
- [ ] Chip de comando visível e legível
- [ ] Smoke + invariantes 14/14
- [ ] Commit `feat(TUI-REDESIGN-25-11): erros de tool com acoes sugeridas`

## Invariantes

#2, #14.

## Anti-débito

- Auto-execução da ação selecionada via tecla (a/b/c) fica para sprint nova (precisa keybinding contextual).

## Verificação

```bash
./run.sh
# pedir Nyx ler arquivo fora do project: erro com 3 ações
bash scripts/sprint_invariants.sh
```

## Rollback

`git reset --hard HEAD~1`

---

*"Toda mensagem de erro é uma oportunidade de próximo passo." -- TUI-REDESIGN-25-11*
