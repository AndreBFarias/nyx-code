# SPRINT TUI-REDESIGN-25-09 — Bloco de thinking recolhível com prévia

## 0. SPEC

```yaml
sprint:
  id: TUI-REDESIGN-25-09
  title: "Chain-of-thought em bloco recolhível: '▶ pensando · 4.2s · prévia' com Tab para expandir"
  onda: 25
  bloco: 25.4 Chain-of-thought, ferramentas e estrutura
  prioridade: ALTA
  tipo: Feature
  dependencias: [TUI-REDESIGN-25-08]
  desbloqueia: []
  origem: "Auditoria audit.jsx -- problema P06 (Sem chain-of-thought visível)"

  touches:
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/agent/output.py
      reason: "Novo helper render_thinking_block(text, duration) + integração com spinner atual"
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/agent/loop/_iteration.py
      reason: "Captura conteúdo de thinking (qwen3 tem campo think; qwen2.5-coder não — usar interlúdio entre tool calls)"
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/cli.py
      reason: "Keybinding Tab dentro do REPL: expande último thinking block se houver"

  forbidden:
    - "Forçar thinking em modelo non-thinking (qwen2.5-coder não emite think)"
    - "Persistir thinking em log permanente (apenas sessão)"

  tests:
    - cmd: "bash scripts/sprint_invariants.sh"
      timeout: 60
      deve_passar: "14/14"

  acceptance_criteria:
    - "Spinner atual é substituído por '▶ pensando · Ns · prévia' enquanto pensando"
    - "Após resposta, linha colapsada permanece: '▶ pensando · 4.2s · primeira frase'"
    - "Tab no REPL expande o último thinking block"
    - "qwen2.5-coder (sem think nativo): bloco mostra preview de interlúdio entre tool calls"
    - "qwen3:4b (com think): bloco mostra conteúdo real do field think"
    - "Smoke ok + invariantes 14/14"
```

---

# Sprint TUI-REDESIGN-25-09

**Status:** PENDENTE
**Data criação:** 2026-05-18
**Modelo obrigatório:** claude-opus-4-7

## Contexto

P06: usuário vê só "pensando..." e depois a resposta. Para iterar com modelos locais (que erram mais), ter prévia opcional do raciocínio melhora confiança.

Modelos qwen3:* expõem campo `think` no response; qwen2.5-coder:3b não (decisão ADR-031). Para qwen2.5-coder, usar interlúdio entre tool calls como "thinking surrogate".

## Solução proposta

1. `render_thinking_block(text, duration)` renderiza:
   - Inline: `▶ pensando · {duration}s · {text[:60]}...`
   - Expandido (após Tab): mostra `text` completo entre divisores.
2. `loop/_iteration.py`: captura `response.message.thinking` se modelo suportar; senão, usa última msg do assistant antes do tool call como surrogate.
3. `cli.py` keybinding Tab: se cursor está em prompt vazio e existe thinking_block recente, alternar expanded/collapsed.

## Critério binário

- [ ] render_thinking_block implementado
- [ ] Funciona com qwen3 (think nativo) e qwen2.5-coder (surrogate)
- [ ] Tab expande/colapsa
- [ ] Smoke + invariantes 14/14
- [ ] Commit `feat(TUI-REDESIGN-25-09): thinking block recolhivel com previa`

## Invariantes

#14.

## Anti-débito

- Persistência de thinking ao longo de turnos fica para sprint futura.
- Export de thinking em /replay já existe parcialmente.

## Verificação

```bash
./run.sh --4b
# pedir algo que invoque thinking (ex: "explique recursão em 3 passos")
# avaliar: bloco recolhível inicial + Tab expande
bash scripts/sprint_invariants.sh
```

## Rollback

`git reset --hard HEAD~1`

---

*"Pensar pode ser íntimo; revelar pode ser opcional." -- TUI-REDESIGN-25-09*
