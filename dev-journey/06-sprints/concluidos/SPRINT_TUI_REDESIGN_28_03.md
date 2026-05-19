# SPRINT TUI-REDESIGN-28-03 — Capitalização microcopy ("Última Sessão" + rótulos do grid)

## 0. SPEC

```yaml
sprint:
  id: TUI-REDESIGN-28-03
  title: "Box 'última sessão' do /quit vira 'Última Sessão' Title Case; rótulos: Iterações/Lidos/Modificados/Tempo/Tokens/Sessão"
  onda: 28
  bloco: 28.1 TUI paridade Claude Code
  prioridade: MÉDIA
  tipo: UX
  dependencias: []
  desbloqueia: []
  origem: "Feedback do usuário 2026-05-18: 'Faltou capitalização Última Sessão e todos os elementos do bloco. Mesma coisa no Sessão e demais abaixo'."

  touches:
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/agent/output.py
      reason: "linhas 633, 723: 'última sessão' -> 'Última Sessão'; linhas 636-643 + 712-719: rótulos Title Case (iterações->Iterações, arquivos lidos->Lidos, arquivos modif->Modificados, tempo->Tempo, tokens->Tokens, sessão->Sessão)"
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/agent/output.py
      reason: "linha 693: revisar CELL_W (22) — rótulos mais curtos (Lidos=5 chars) permitem reduzir para ~16-18 e grid mais apertado"
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/dev-journey/05-guides/MICROCOPY.md
      reason: "atualizar entries da tabela se 'última sessão'/'iterações'/etc estiverem catalogados"

  forbidden:
    - "Quebrar microcopy_audit.py --check (zero violações)"
    - "Mudar lógica de render_session_stats_card (só strings)"
    - "Alterar versão inline (cols<80) inconsistentemente com versão grid"

  tests:
    - cmd: "./run.sh --smoke"
      timeout: 60
      deve_passar: "boot ok"
    - cmd: "./venv/bin/python scripts/microcopy_audit.py --check"
      timeout: 30
      deve_passar: "zero violações"
    - cmd: "grep -n 'Última Sessão\\|Iterações\\|Lidos\\|Modificados\\|Tempo\\|Tokens\\|Sessão' nyx/agent/output.py | wc -l"
      timeout: 5
      deve_passar: ">= 12 matches (versão inline + grid)"

  acceptance_criteria:
    - "/quit em sessão real renderiza box com cabeçalho 'Última Sessão' (Title Case)"
    - "Rótulos do grid: Iterações, Lidos, Modificados (linha 1) + Tempo, Tokens, Sessão (linha 2)"
    - "Versão inline (cols<80) também capitalizada coerentemente"
    - "microcopy_audit.py --check sem violações"
    - "Smoke + invariantes ok"

  proof_of_work:
    - "Rodar Nyx, fazer 1 iteração simples, /quit, capturar saída final via tee /tmp/nyx_quit_box.txt"
    - "cat /tmp/nyx_quit_box.txt | grep -E 'Última Sessão|Iterações|Lidos|Modificados|Tempo|Tokens|Sessão' = 7 linhas mínimo"
```

---

# Sprint TUI-REDESIGN-28-03

**Status:** CONCLUIDA
**Data criação:** 2026-05-18
**Data conclusão:** 2026-05-18
**Modelo obrigatório:** claude-opus-4-7

## Resultado

Capitalização Title Case aplicada em ambas as versões (grid e inline) do `render_session_stats_card`:

- Cabeçalho: `última sessão` → `Última Sessão`
- Rótulos: `iterações`→`Iterações`, `arquivos lidos`→`Lidos`, `arquivos modif`→`Modificados`, `tempo`→`Tempo`, `tokens`→`Tokens`, `sessão`→`Sessão`
- CELL_W: 22 → 17 (justificativa aritmética: pior caso "Sessão"(6) + short_id 8 chars + gap 1 + padding 2 = 17)

Smoke + invariantes 14/14 + microcopy_audit zero violações.

## Rollback

`git reset --hard HEAD~1`
