## 0. SPEC (machine-readable)

```yaml
sprint:
  id: CTX-04
  title: "Plano ativo opt-in via /plan (GSD-B)"
  touches:
    - path: nyx/agent/commands.py
      reason: "Commands /plan <objetivo>, /plan show, /plan done <n>, /plan clear"
    - path: nyx/agent/plan.py
      reason: "Novo módulo: ActivePlan (checklist persistida)"
    - path: nyx/agent/prompt.py
      reason: "Placeholder {active_plan}"
    - path: nyx/agent/persistence.py
      reason: "Salvar/carregar plan junto com session"
  n_to_n_pairs: []
  forbidden:
    - "Plan > 500 tokens no prompt"
    - "Auto-criar plan sem comando explícito do dev"
  tests:
    - cmd: "./run.sh --gauntlet --only commands"
      timeout: 120
  acceptance_criteria:
    - "/plan <objetivo> cria plan.md"
    - "/plan show exibe checklist"
    - "/plan done N marca item"
    - "Plan aparece no prompt quando ativo"
    - "/plan clear remove"
    - "Acentuação PT-BR"
```

---

# Sprint CTX-04 -- Plano ativo opt-in (GSD-B) [OPCIONAL]

**Status:** OPCIONAL
**Data:** 2026-04-17
**Prioridade:** BAIXA
**Tipo:** Feature
**Dependências:** CTX-03
**Desbloqueia:** nenhuma

---

## Problema / Contexto

Às vezes você começa uma sessão com objetivo bem definido ("portar feature X do TS pra Python"). Um plano vivo estilo TODO.md que a Nyx atualiza (risca itens concluídos) ajuda a manter foco.

Opcional porque nem toda sessão tem plano -- conversas exploratórias não precisam. É opt-in via `/plan <objetivo>`.

## Implementação

### Fase 1 -- ActivePlan module

- `nyx/agent/plan.py`:
  ```python
  @dataclass
  class PlanItem:
      text: str
      done: bool = False

  class ActivePlan:
      objective: str
      items: list[PlanItem]
      def add(self, text): ...
      def done(self, n: int): ...
      def render(self) -> str: ...
      def save(self, path: Path): ...
      @classmethod
      def load(cls, path: Path) -> ActivePlan | None: ...
  ```

### Fase 2 -- Commands

- `/plan <objetivo>`: cria ActivePlan com objective, salva em `~/.nyx/sessions/<id>/plan.md`
- `/plan add <texto>`: adiciona item
- `/plan done <n>`: marca item n como done
- `/plan show`: imprime checklist renderizada
- `/plan clear`: apaga plan

### Fase 3 -- Injeção no prompt

- `prompt.py`: placeholder `{active_plan}`. Se não-vazio, bloco `### Plano ativo\n{plan}\n---\n`.

### Fase 4 -- Persistência

- Junto da session (ADR padrão). Load no boot se plan.md existe.

## Verificação

```bash
./run.sh
# /plan Portar módulo de streaming
# /plan add Ler openclaud/src/streaming/
# /plan add Implementar nyx/services/streaming.py
# /plan add Adicionar caso no Gauntlet
# /plan show
# Esperado: lista com 3 itens, 0 done
# Conversar, pedir pra Nyx fazer 1 item
# /plan done 1
# /plan show
# Esperado: [x] item 1 riscado
# Ctrl+D, ./run.sh
# /plan show
# Esperado: plan restaurado
./run.sh --gauntlet --only commands
```

- [ ] /plan cria arquivo
- [ ] /plan add/done funciona
- [ ] Plan aparece no system prompt
- [ ] /plan clear remove
- [ ] Persiste entre sessões
- [ ] Acentuação PT-BR
- [ ] Gauntlet commands passa

---

*"Um objetivo sem plano é apenas um desejo." -- Antoine de Saint-Exupéry*
