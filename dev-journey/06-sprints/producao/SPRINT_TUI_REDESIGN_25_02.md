# SPRINT TUI-REDESIGN-25-02 — Glifos e divisores canônicos (boot vs sessão)

## 0. SPEC

```yaml
sprint:
  id: TUI-REDESIGN-25-02
  title: "Separar visualmente fase de boot ([nyx] log) da fase de sessão (Nyx + glifos)"
  onda: 25
  bloco: 25.1 Fundamentos visuais
  prioridade: ALTA
  tipo: UX
  dependencias: [TUI-REDESIGN-25-01]
  desbloqueia: [TUI-REDESIGN-25-06, TUI-REDESIGN-25-08]
  origem: "Auditoria audit.jsx -- problemas P10 (Output Nyx sem ancoragem visual) e P14 (Banner [nyx] vs Nyx misturados)"

  touches:
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/run.sh
      reason: "Marca explícita de fim do log de boot (linha 'fim do log de boot' + divisor canônico)"
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/agent/output.py
      reason: "Catálogo de glifos canônicos por tipo de bloco (divisor fino, divisor robusto, faixa lateral, prefix usuário, prefix Nyx)"
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/themes/design_tokens.py
      reason: "BOX_CHARS expande para incluir GLYPHS_BOOT, GLYPHS_SESSAO, SIDE_RULE, PREFIX_USER, PREFIX_NYX"

  forbidden:
    - "Quebrar invariante #14 (glifos ○ ◐ ●)"
    - "Hardcode de hex fora de design_tokens*"
    - "Misturar [nyx] (log boot) com Nyx (sessão) na mesma linha"

  tests:
    - cmd: "./run.sh --smoke 2>&1 | grep -c '^\\[nyx\\]'"
      timeout: 10
      deve_passar: "log boot continua com prefixo [nyx]"
    - cmd: "bash scripts/sprint_invariants.sh"
      timeout: 60
      deve_passar: "14/14"

  acceptance_criteria:
    - "run.sh emite linha separadora explícita ao concluir boot ('--- sessão iniciada ---' ou similar)"
    - "design_tokens.py expõe GLYPHS_BOOT, GLYPHS_SESSAO, SIDE_RULE_USER, SIDE_RULE_NYX, PREFIX_USER, PREFIX_NYX"
    - "Output da Nyx em sessão NUNCA usa prefixo [nyx] (reservado para boot)"
    - "Boot log mantém [nyx] como hoje (paridade com versão atual)"
    - "Documentado em MICROCOPY.md seção 'Vocabulário visual'"
    - "Smoke ok + invariantes 14/14"
```

---

# Sprint TUI-REDESIGN-25-02

**Status:** PENDENTE
**Data criação:** 2026-05-18
**Modelo obrigatório:** claude-opus-4-7

## Contexto

P10 + P14 da auditoria: a Nyx em sessão herda visualmente o estilo de log do boot (`[nyx] Iniciando...`), o que cria ambiguidade entre "estou inicializando" e "estou conversando". O redesenho separa as duas fases com glifos e divisores canônicos.

## Solução proposta

1. `design_tokens.py` ganha catálogo de glifos por tipo de bloco (sem mudar paleta, só inventário).
2. `run.sh` imprime divisor explícito ao concluir boot (antes do REPL iniciar).
3. `nyx/agent/output.py` documenta convenção: `[nyx]` só em fase boot/log; sessão usa `Nyx` standalone com side-rule.
4. MICROCOPY.md ganha tabela "Vocabulário visual" (prefix, divisor, faixa, ornamento por bloco).

## Critério binário

- [ ] Glifos canônicos catalogados em design_tokens.py
- [ ] Divisor explícito no fim do boot
- [ ] Convenção `[nyx]` vs `Nyx` documentada
- [ ] Smoke + invariantes 14/14
- [ ] Sprint movida → concluidos
- [ ] Commit `feat(TUI-REDESIGN-25-02): glifos e divisores canonicos (boot vs sessao)`

## Invariantes a preservar

#14 (○ ◐ ●), #6 (hex em design_tokens), #2 (anonimato).

## Anti-débito

- Aplicação dos novos glifos em cada bloco específico fica para sprints 25-06..25-14.
- Implementação real do header da Nyx (uso de PREFIX_NYX + SIDE_RULE_NYX) fica para 25-08.

## Verificação

```bash
grep -E "GLYPHS_BOOT|GLYPHS_SESSAO|SIDE_RULE_NYX" nyx/themes/design_tokens.py
./run.sh --smoke
bash scripts/sprint_invariants.sh
```

## Rollback

`git reset --hard HEAD~1`

---

*"Boot fala em log; sessão fala em diálogo." -- TUI-REDESIGN-25-02*
