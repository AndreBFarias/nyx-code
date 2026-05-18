# SPRINT UX-COCKPIT-EXPERIENCE-01 — Coerência de experiência TUI ↔ Web (filosofia única)

## 0. SPEC (machine-readable)

```yaml
sprint:
  id: UX-COCKPIT-EXPERIENCE-01
  title: "Aplica ADRs 025/026/027 no Cockpit web; coerência pixel-perfect com TUI"
  onda: 23
  bloco: 23.4 Gamedesigner
  prioridade: MÉDIA
  tipo: Feature+UX
  dependencias: [COCKPIT-03, UX-LOOP-01, UX-AGENCY-01]
  desbloqueia: [VALIDATE-FINAL-01]

  touches:
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/cockpit/static/app.js
      reason: "Implementa feedback loop, agency, identidade Nyx no Cockpit"
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/cockpit/static/app.css
      reason: "Aplica paleta D + tokens motion; espelha TUI estilo"
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/cockpit/server.py
      reason: "GET /api/tokens expõe design_tokens.py para o frontend; GET /api/microcopy expõe MICROCOPY.md"

  creates: []
  removes: []

  n_to_n_pairs:
    - descricao: "Cores e microcopy só em design_tokens.py e MICROCOPY.md — cockpit consome via API"
      paths:
        - /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/themes/design_tokens.py
        - /home/andrefarias/Desenvolvimento/Nyx-Code/dev-journey/05-guides/MICROCOPY.md

  forbidden:
    - "CSS com hex hardcoded (usar vars CSS hidratadas via /api/tokens)"
    - "Microcopy inline (deve vir de /api/microcopy)"
    - "Tela 'muda' >1s sem indício (ADR-025)"
    - "Decisão automática sem nomear (ADR-026)"
    - "Voz divergente da TUI (ADR-027)"

  tests:
    - cmd: "./run.sh --cockpit --gauntlet --only cockpit"
      timeout: 600
      deve_passar: true
    - cmd: "curl -sf http://127.0.0.1:11437/api/tokens | jq .accent"
      timeout: 10
      deve_passar: true
      nota: "Retorna '#00D4AA'"
    - cmd: "bash scripts/sprint_invariants.sh"
      timeout: 60
      deve_passar: "FAIL_AFTER <= FAIL_BEFORE"

  acceptance_criteria:
    - "Cockpit aplica ADR-025: ack <100ms ao clicar 'Rodar'; status muda visível imediato"
    - "Cockpit aplica ADR-026: tooltip contextual em '?' nos cards; cancel disponível em jobs"
    - "Cockpit aplica ADR-027: microcopy auditado; voz Nyx no UI"
    - "Paleta D hidratada via /api/tokens (sem hex no CSS)"
    - "Mobile responsive; navegação por teclado funcional"
    - "Claude via Chrome MCP consegue: rodar gauntlet, ler estado, capturar evidência sem ambiguidade"
    - "Acentuação PT-BR no UI; zero emoji"
```

---

**Status:** BLOQUEADA
**Data criação:** 2026-05-15
**Modelo obrigatório:** claude-opus-4-7 (sem subagentes)

---

# Sprint UX-COCKPIT-EXPERIENCE-01

Última sprint do Bloco 23.4. Garante que a filosofia gamedesigner aplicada à TUI também governa o Cockpit web. Coerência total entre os dois "rostos" do Nyx.

## Solução resumida

1. Frontend lê `/api/tokens` no boot e injeta CSS variables.
2. Microcopy do UI lê `/api/microcopy` ao carregar; sem strings hardcoded.
3. Cada interação no dashboard segue contrato ADR-025 (feedback <100ms).
4. Help contextual: tooltip ao hover em '?' nos cards e ações.
5. Cancel/pause disponível para jobs em andamento.

## Verificação

- Manual: olhar TUI e Cockpit lado a lado; voz, cores, microcopy iguais.
- Automated: gauntlet `--only cockpit` valida endpoints + smoke da UI via headless browser (Chrome MCP).

---

*"Dois rostos da mesma Nyx: o terminal e a janela." -- anônimo*
