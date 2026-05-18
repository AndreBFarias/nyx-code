# SPRINT UX-LOOP-01 — Implementa ADR-025: feedback loop + juicing no ciclo Nyx

## 0. SPEC (machine-readable)

```yaml
sprint:
  id: UX-LOOP-01
  title: "Aplica ADR-025 nos 5 pontos de feedback do ciclo Nyx (input/tool start/tool result/streaming/next prompt)"
  onda: 23
  bloco: 23.4 Gamedesigner
  prioridade: ALTA
  tipo: Feature+UX
  dependencias: [ADR-023]
  desbloqueia: [UX-AGENCY-01, UX-PROGRESSION-01, UX-COCKPIT-EXPERIENCE-01]

  touches:
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/dev-journey/03-decisions/ADR_025_LOOP_EXPERIENCIA.md
      reason: "Mudar Status PROPOSTO → ACEITO ao concluir sprint"
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/agent/output.py
      reason: "Aplicar contratos de feedback nos 5 pontos: input ack, tool start glyph, tool result duration, streaming cursor, next prompt footer"
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/cli.py
      reason: "Adiciona pontos de feedback no REPL loop"
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/scripts/gauntlet/nyx_gauntlet.py
      reason: "Adiciona fase 'loop' que mede tempos de feedback"

  creates:
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/scripts/gauntlet/fixtures/loop_benchmark.py
      reason: "Mede tempos: ack <100ms, tool start <300ms"

  removes: []

  n_to_n_pairs:
    - descricao: "Tempos limites (100ms, 300ms, 500ms) aparecem em ADR-025 e em fixtures — fonte única em ADR; fixtures importam constantes"
      paths:
        - /home/andrefarias/Desenvolvimento/Nyx-Code/dev-journey/03-decisions/ADR_025_LOOP_EXPERIENCIA.md
        - /home/andrefarias/Desenvolvimento/Nyx-Code/scripts/gauntlet/fixtures/loop_benchmark.py

  forbidden:
    - "Adicionar emoji"
    - "Hardcoded de hex (usar design_tokens)"
    - "Permitir tela 'muda' >1s sem indício de progresso"
    - "Spinner que não avança"

  tests:
    - cmd: "./run.sh --gauntlet --only loop"
      timeout: 300
      deve_passar: true
    - cmd: "bash scripts/sprint_invariants.sh"
      timeout: 60
      deve_passar: "FAIL_AFTER <= FAIL_BEFORE"

  acceptance_criteria:
    - "Ack de input <100ms (echo visível antes do processo seguir)"
    - "Tool start: glyph + label + cronômetro em <300ms"
    - "Tool result: glyph terminal + duração em ms+linha de status"
    - "Streaming: cursor vivo, sem flicker, frame budget honrado"
    - "Next prompt: footer atualizado com atalhos relevantes àquele momento"
    - "Sprint atualiza ADR-025 de PROPOSTO para ACEITO"
    - "Gauntlet fase 'loop' nova passa 100%"
    - "Acentuação PT-BR"
```

---

**Status:** PENDENTE
**Data criação:** 2026-05-15
**Modelo obrigatório:** claude-opus-4-7 (sem subagentes)

---

# Sprint UX-LOOP-01

Implementa o contrato de feedback definido em ADR-025 nos 5 pontos canônicos do ciclo Nyx. Após esta sprint, **toda sprint futura tem critério "ADR-025 aplicado"** em sua AC.

## Pontos de implementação

1. **Input ack <100ms** — `output.render_user_input` deve imprimir antes do `await` do `AgentLoop`.
2. **Tool start <300ms** — `on_tool_start` callback exibe glyph + label.
3. **Tool result <500ms** — `on_tool_end` exibe duração ao lado do glyph.
4. **Streaming frame budget** — `on_token` re-render a cada N tokens (não a cada token; evita flicker).
5. **Next prompt footer** — `cli.py` atualiza footer com base no estado (modo bypass, modo memory, modo tool ativo).

## Verificação

```bash
./run.sh --gauntlet --only loop
# Benchmark deve mostrar:
# - ack_ms: < 100
# - tool_start_ms: < 300
# - tool_result_ms: < 500
```

---

*"Cada estágio do loop é uma promessa de presença." -- anônimo*
