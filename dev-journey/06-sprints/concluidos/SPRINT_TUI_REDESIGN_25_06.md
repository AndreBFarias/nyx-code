# SPRINT TUI-REDESIGN-25-06 — Header de sessão em bloco de 3 linhas com agrupamento

## 0. SPEC

```yaml
sprint:
  id: TUI-REDESIGN-25-06
  title: "Header de sessão em 3 linhas com rótulos agrupados (Modelo | Projeto | Rede | Sessão)"
  onda: 25
  bloco: 25.2 Onboarding & Banner
  prioridade: ALTA
  tipo: UX
  dependencias: [TUI-REDESIGN-25-02, TUI-REDESIGN-25-05]
  desbloqueia: [TUI-REDESIGN-25-08]
  origem: "Auditoria audit.jsx -- problema P05 (Header de sessão entupido)"

  touches:
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/agent/banner.py
      reason: "_build_wide reorganiza output em 3 linhas com rótulos agrupados"

  forbidden:
    - "Hardcode de hex fora de design_tokens*"
    - "Aumentar banner para >4 linhas (ADR-029)"
    - "Quebrar modo compact (banner ainda funciona em <80 cols)"

  tests:
    - cmd: "./run.sh --smoke 2>&1 | grep -c 'Nyx v'"
      timeout: 10
      deve_passar: ">= 1"
    - cmd: "bash scripts/sprint_invariants.sh"
      timeout: 60
      deve_passar: "14/14"

  acceptance_criteria:
    - "Banner ocupa exatamente 3 linhas (mais 1 divisor opcional)"
    - "Linha 1: Nyx vX | 100% offline"
    - "Linha 2: Modelo (qwen2.5-coder:3b) | Projeto (Nyx-Code) | Rede (:11435 ollama · :11436 proxy)"
    - "Linha 3: Tools (35) | Comandos (61) | Memória ativa | Tipo (REPL)"
    - "Cor accent no nome do app, ink_dim nos valores, ink_muted nos rótulos"
    - "Smoke ok + invariantes 14/14"
```

---

# Sprint TUI-REDESIGN-25-06

**Status:** CONCLUIDA
**Data criação:** 2026-05-18
**Data conclusão:** 2026-05-18
**Modelo obrigatório:** claude-opus-4-7

## Contexto

P05: banner atual mistura tudo em poucas linhas sem hierarquia (Nyx v1.2.0 + qwen2.5-coder + Nyx-Code + portas + tools count + memória ativa, tudo em pipe-separated). Falta agrupamento.

## Solução proposta

Reescrever `_build_wide`:

```
Nyx v1.2.0                                                       100% offline
Modelo qwen2.5-coder:3b   Projeto Nyx-Code   Rede :11435 / :11436
Tools 35   Comandos 61   Memória ativa   Tipo REPL
```

Rótulos em `ink_muted`, valores em `ink_dim` ou `ink`, accent só no nome "Nyx vX".

## Critério binário

- [ ] 3 linhas (4 com divisor)
- [ ] Rótulos agrupados claramente
- [ ] Cores corretas (rótulos muted, valores ink)
- [ ] Modo compact preservado para terminais estreitos
- [ ] Smoke + invariantes 14/14
- [ ] Commit `feat(TUI-REDESIGN-25-06): header sessao em 3 linhas com agrupamento`

## Invariantes

#6, #14.

## Anti-débito

- Banner neofetch (info-rich) fica como modo extra opcional para sprint futura (VL-02 ABSORVIDA, mas conceito sobrevive).

## Verificação

```bash
./run.sh
# avaliar visualmente as 3 linhas
bash scripts/sprint_invariants.sh
```

## Rollback

`git reset --hard HEAD~1`

---

*"Hierarquia se faz com agrupamento, não com pipes." -- TUI-REDESIGN-25-06*
