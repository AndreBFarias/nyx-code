## 0. SPEC

```yaml
sprint:
  id: TUI-REDESIGN-25-09-PARTE-3
  title: "Captura real do thinking via proxy emitir reasoning_content para o cli"
  onda: 25
  bloco: "25.meta Anti-débito de UX"
  prioridade: MÉDIA
  tipo: Feature
  dependencias: [TUI-REDESIGN-25-09-PARTE-2]
  desbloqueia: []

  touches:
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/proxy.py
      reason: "Em vez de descartar conteúdo do <think>...</think> via _strip_think, emitir como campo `reasoning_content` na resposta OpenAI (campo custom não-bloqueante para clients que não consomem)"
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/agent/loop/_iteration.py
      reason: "Capturar `reasoning_content` quando presente na resposta e propagar via callback on_thinking (similar a on_token)"
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/scripts/gauntlet/nyx_gauntlet.py
      reason: "Adicionar P-09 (proxy emite reasoning_content quando think=true)"

  creates: []
  removes: []

  forbidden:
    - "Quebrar formato OpenAI atual (campo deve ser ADITIVO, não substituir choices/usage/message)"
    - "Tocar nyx/cli.py ou output.py (consumo do thinking fica para sub-sprint UX dedicada)"
    - "Quebrar P-01..P-07 do gauntlet (resposta core preservada)"
    - "Emoji ou menção a IA externa"

  tests:
    - cmd: "./run.sh --smoke"
      timeout: 10
    - cmd: "bash scripts/sprint_invariants.sh"
      timeout: 30
      assert: "PASS=14"
    - cmd: "./run.sh --gauntlet --only proxy"
      timeout: 60
      assert: "100% (P-01..P-07 preservados + P-09 novo)"

  acceptance_criteria:
    - "proxy.py extrai conteúdo entre <think>...</think> ANTES de strippar; preserva como string"
    - "Resposta JSON OpenAI ganha campo `nyx_reasoning` (top-level OU em choices[0].message) quando há thinking"
    - "Campo ausente quando sem thinking (não-zero default)"
    - "Clientes que ignoram campo desconhecido funcionam (compatibilidade)"
    - "Gauntlet --only proxy 100% incluindo P-09 novo"
    - "Smoke + invariantes 14/14 + acentuação rc=0"
    - "MASTER linha M3 (PARTE-3) DEFERIDA → CONCLUIDA"
```

---

**Status:** CONCLUIDA (2026-05-21, commit __post_hash__)
**Data criação:** 2026-05-21
**Data conclusão:** 2026-05-21
**Modelo obrigatório:** claude-opus-4-7

---

## Solução

1. Em `_strip_think()`, antes de retornar, capturar o conteúdo entre as tags em um helper paralelo `_extract_think(text) -> str`.
2. Em `ollama_to_openai()` (ou onde a resposta é montada), incluir `nyx_reasoning` no JSON quando houver thinking.
3. Em `_iteration.py`, ler `nyx_reasoning` da resposta e propagar via callback (se executor preferir, criar `on_thinking` ou usar `on_token` com flag).

## Proof-of-work

```bash
bash scripts/sprint_invariants.sh > /tmp/inv_before_c2.txt 2>&1
# IMPLEMENTAR
./run.sh --smoke
bash scripts/sprint_invariants.sh > /tmp/inv_after_c2.txt 2>&1
./run.sh --gauntlet --only proxy 2>&1 | tail -10
python3 ~/.config/zsh/scripts/validar-acentuacao.py --paths nyx/proxy.py nyx/agent/loop/_iteration.py scripts/gauntlet/nyx_gauntlet.py
```

## Critério binário

- [ ] `_extract_think()` helper em proxy.py
- [ ] `nyx_reasoning` no JSON OpenAI quando há thinking
- [ ] Campo ausente sem thinking
- [ ] Gauntlet --only proxy 100% (incl P-09)
- [ ] Smoke + invariantes 14/14
- [ ] MASTER M3 DEFERIDA → CONCLUIDA

---

*"Pensamento capturado é pensamento útil."*
