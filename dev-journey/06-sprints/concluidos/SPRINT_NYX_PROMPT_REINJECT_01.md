# SPRINT NYX-PROMPT-REINJECT-01 — Reinjetar contexto canônico periodicamente

## 0. SPEC

```yaml
sprint:
  id: NYX-PROMPT-REINJECT-01
  title: "AgentLoop reinjeta sistema canônico + meta do turno a cada N iterações"
  onda: 24
  bloco: 24.9 Memória contínua
  prioridade: ALTA
  tipo: Feature
  dependencias: [NYX-GSD-CHECKPOINTS-01]
  desbloqueia: [tarefas multi-turno robustas]
  origem: "Pedido do usuario 2026-05-18: 'Prompt injection pra evitar perder o contexto e ficar maluca'. Inspirado em Claude Code system-reminders que reaparecem entre tool results para manter o agente alinhado."

  touches:
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/agent/loop/_iteration.py
      reason: "Antes de cada _call_llm, decidir se injeta reminder"
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/agent/prompt.py
      reason: "build_reminder(session) gera bloco system-reminder canonico"

  forbidden:
    - "Reinjetar em todas iteracoes (overhead)"
    - "Reinjetar conteudo identico que ja esta no contexto (waste)"
    - "Misturar reminder com user message (precisa ser role=system)"

  tests:
    - cmd: "echo 'manual: rode tarefa com 4+ iteracoes; ver no progress.md entry [reminder]'"
      timeout: 5
    - cmd: "bash scripts/sprint_invariants.sh"
      timeout: 60
      deve_passar: "14/14"

  acceptance_criteria:
    - "A cada 3 tool calls (configurável), injeta reminder antes do proximo _call_llm"
    - "Reminder inclui: meta do turno (user_input original), estado (iter, lidos, modif), invariantes (PT-BR, sem emoji, sandbox)"
    - "Reminder tem prefixo <system-reminder>...</system-reminder> (estilo Claude Code)"
    - "Detecta drift: se modelo emitir output em ingles 2x consecutivo, dispara reminder extra de idioma"
    - "Detecta drift: se modelo afirma sucesso sem tool, reminder NYX-NO-HALLUCINATE"
    - "GsdWriter registra entry 'reminder' quando injetado"
    - "Smoke + invariantes 14/14"
```

---

# Sprint NYX-PROMPT-REINJECT-01

**Status:** CONCLUIDA
**Data criação:** 2026-05-18
**Data conclusão:** 2026-05-19
**Modelo obrigatório:** claude-opus-4-7

---

## Contexto

Modelos pequenos (qwen2.5-coder:3b) perdem foco em tarefas multi-turno.
Sintomas observados (sessao 2026-05-18):
- Iter 4 sem completar pedido simples
- Alucina sucesso sem chamar tool (NYX-NO-HALLUCINATE-TOOL-01)
- Esquece restricao de sandbox e tenta path absoluto

Claude Code resolve isso via "system-reminder" reaparecente entre
tool results (visivel em transcripts: blocos `<system-reminder>...
</system-reminder>` que reafirmam invariantes, perfil do usuario,
estado do projeto). Nyx replica esse padrao em escala menor.

## Solucao proposta

### `nyx/agent/prompt.py` ampliado

```python
def build_reminder(session, project_root: str, original_input: str | None = None) -> str:
    """Bloco <system-reminder> com estado canonico do turno."""
    meta = original_input or "(pedido nao registrado)"
    lines = [
        "<system-reminder>",
        f"Pedido original: {meta[:200]}",
        f"Estado: iter={session.iter_n}, "
        f"lidos={session.files_read_count}, modif={session.files_modified_count}",
        f"Invariantes vigentes (lembrar SEMPRE):",
        "- Voce e Nyx-Code. Sem mencao a IA externa.",
        "- Responda em PT-BR acentuado.",
        "- Sem emoji em codigo/output user-facing.",
        "- Use tools (write_file/edit_file/run_command) -- NUNCA afirme sucesso sem tool call real.",
        f"- Sandbox: pode tocar apenas {project_root} (e roots extra opt-in).",
        "</system-reminder>",
    ]
    return "\n".join(lines)
```

### `nyx/agent/loop/_iteration.py` integra

```python
class _IterationMixin:
    REMINDER_EVERY = 3  # configuravel via NYX_REMINDER_EVERY

    def _maybe_inject_reminder(self):
        if self._tool_calls_count % self.REMINDER_EVERY != 0:
            return
        from nyx.agent.prompt import build_reminder
        reminder = build_reminder(
            self._session,
            self._project_root,
            original_input=self._session.original_input,
        )
        # Push como system role
        self._session.messages.append({"role": "system", "content": reminder})
        if self._gsd:
            self._gsd.write("reminder", "injetado (drift prevention)")
```

### Detecção de drift

```python
def _detect_drift(self, last_assistant_text: str) -> bool:
    # Lang drift: 2 turnos consecutivos em ingles
    if not is_pt_br(last_assistant_text):
        self._lang_drift_streak += 1
        if self._lang_drift_streak >= 2:
            return True
    else:
        self._lang_drift_streak = 0
    # Hallucination drift: afirma sucesso sem tool no turno
    if has_success_phrase(last_assistant_text) and self._tool_calls_this_turn == 0:
        return True
    return False
```

Quando drift detectado, força reminder no próximo _call_llm.

## Critério binário

- [ ] build_reminder gera bloco canonico
- [ ] Injeção a cada 3 tool calls
- [ ] Drift de idioma força reminder
- [ ] Drift de alucinação força reminder
- [ ] GsdWriter registra
- [ ] Sem overhead notavel (latencia <10% extra)
- [ ] Smoke + invariantes 14/14
- [ ] Commit `feat(NYX-PROMPT-REINJECT-01): system-reminder periodico anti-drift`

---

*"Memoria que se reforca, contexto que sobrevive." -- NYX-PROMPT-REINJECT-01*
