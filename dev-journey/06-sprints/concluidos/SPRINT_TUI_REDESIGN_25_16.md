# SPRINT TUI-REDESIGN-25-16 — Composição runtime (schema × aesthetic × entity) + /schema

## 0. SPEC

```yaml
sprint:
  id: TUI-REDESIGN-25-16
  title: "compose(schema, aesthetic, entity) retorna config completa + slash /schema list/set/get"
  onda: 25
  bloco: 25.1 Fundamentos visuais
  prioridade: ALTA
  tipo: Feature
  dependencias: [TUI-REDESIGN-25-15]
  desbloqueia: [TUI-REDESIGN-25-06..14]
  origem: "Resposta do usuário em planejamento: composição runtime das 3 camadas (4 × 6 × 7 = 168 combinações)"

  touches:
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/themes/design_tokens_extended.py
      reason: "Refatorar compose() para receber schema, aesthetic, entity; merge das 3 camadas"
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/themes/theme_manager.py
      reason: "resolve_active() lê NYX_SCHEMA, NYX_AESTHETIC, NYX_ENTITY do ambiente e cacheia"
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/agent/commands/aesthetic.py
      reason: "/aesthetic ganha contraparte /schema (list, set, get); ou consolidar em /aesthetic --schema X"
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/scripts/menu_wizard.py
      reason: "Wizard ganha 6º passo: schema (opcional, default hybrid)"

  forbidden:
    - "Quebrar compose(aesthetic, entity) atual (manter backward-compat 2-arg)"
    - "Persistir senha em config.toml (escopo não muda)"

  tests:
    - cmd: "./venv/bin/python -c 'from nyx.themes.design_tokens_extended import compose; c = compose(\"hybrid\", \"default\", \"nyx\"); assert \"prefixes\" in c'"
      timeout: 5
      deve_passar: true
    - cmd: "bash scripts/sprint_invariants.sh"
      timeout: 60
      deve_passar: "14/14"

  acceptance_criteria:
    - "compose(schema, aesthetic, entity) retorna dict com keys: prefixes, bubble_styles, tool_style, thinking_style, divider, banner, palette, accent"
    - "compose() sem args usa env NYX_SCHEMA + NYX_AESTHETIC + NYX_ENTITY (defaults hybrid/default/nyx)"
    - "/schema list mostra os 4 schemas com tagline"
    - "/schema set X muda runtime"
    - "/schema get mostra atual"
    - "Wizard ganha passo schema (opcional, default hybrid)"
    - "Smoke ok + invariantes 14/14"
```

---

# Sprint TUI-REDESIGN-25-16

**Status:** CONCLUIDA
**Data criação:** 2026-05-18
**Data conclusão:** 2026-05-18
**Modelo obrigatório:** claude-opus-4-7

## Contexto

25-15 cria os 4 schemas. Esta sprint compõe runtime: junta schema + aesthetic + entity em uma config consumível pelo render.

168 combinações possíveis (4 × 6 × 7). Default = hybrid + default + nyx (Dracula refinada com paleta D).

## Solução proposta

1. `design_tokens_extended.py::compose(schema, aesthetic, entity)`:

```python
def compose(schema="hybrid", aesthetic="default", entity="nyx"):
    s = INTERFACE_SCHEMAS[schema]
    a = AESTHETICS[aesthetic]
    e = ENTITIES[entity]
    return {
        "schema_id": schema,
        "aesthetic_id": aesthetic,
        "entity_id": entity,
        "prefixes": {"user": s["user_prefix"], "nyx": s["nyx_prefix"]},
        "bubble_styles": {"user": s["user_bubble"], "nyx": s["nyx_bubble"]},
        "tool_style": s["tool_style"],
        "thinking_style": s["thinking_style"],
        "divider": s["divider_style"],
        "banner": s["banner_style"],
        "heading_case": s["heading_case"],
        "palette": a["palette"],
        "accent": e["accent"],  # override
        "glow": e["glow"],
    }
```

2. `theme_manager.resolve_active()` lê env + cacheia.
3. Slash `/schema` (ou `/aesthetic --schema`).
4. `menu_wizard.py` ganha passo 6 opcional (apenas se `--full`).

## Critério binário

- [ ] compose() aceita 3 args
- [ ] Default (sem args) usa env
- [ ] /schema list/set/get funcional
- [ ] Wizard atualizado
- [ ] Backward-compat preservado
- [ ] Smoke + invariantes 14/14
- [ ] Commit `feat(TUI-REDESIGN-25-16): compose(schema, aesthetic, entity) + slash /schema`

## Invariantes

#6, #14.

## Anti-débito

- Aplicação real do schema em cada bloco fica para sprints específicas (já mapeadas).
- Modal de preview live no cockpit (escolher schema visualmente) fica para sprint nova.

## Verificação

```bash
./venv/bin/python -c "from nyx.themes.design_tokens_extended import compose; print(compose('hybrid', 'default', 'nyx'))"
NYX_SCHEMA=brutalist ./run.sh --smoke
bash scripts/sprint_invariants.sh
```

## Rollback

`git reset --hard HEAD~1`

---

*"Composição é a operação que faz 4 + 6 + 7 virar 168." -- TUI-REDESIGN-25-16*
