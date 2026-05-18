# SPRINT VISUAL-LAYOUT-CLI-CONSUME-01 — CLI consome design_tokens_extended runtime

## 0. SPEC (machine-readable)

```yaml
sprint:
  id: VISUAL-LAYOUT-CLI-CONSUME-01
  title: "Banner e output.py consomem nyx.themes.design_tokens_extended.get_active() em runtime"
  onda: 24
  bloco: 24.2 Visual Layout
  prioridade: MÉDIA
  tipo: Refactor
  dependencias: [VISUAL-LAYOUT-01, VISUAL-LAYOUT-08]
  desbloqueia: [VISUAL-LAYOUT-02, VISUAL-LAYOUT-05]

  touches:
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/themes/theme_manager.py
      reason: "Adicionar resolve_palette() que delega para design_tokens_extended.get_active"
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/agent/output.py
      reason: "Carregar accent/glyphs via theme_manager em vez de ler design_tokens diretamente"
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/agent/banner.py
      reason: "Banner respeita aesthetic ativo (palette + tagline)"
  creates: []
  removes: []

  forbidden:
    - "Hex hardcoded fora de design_tokens*"
    - "Quebrar default behavior (paleta D preservada quando NYX_AESTHETIC=default)"
    - "Tocar invariante #14 (glifos canonicos preservados)"

  tests:
    - cmd: "NYX_AESTHETIC=arcano ./run.sh --smoke"
      timeout: 30
      deve_passar: "boot ok"
    - cmd: "NYX_AESTHETIC=cyberpunk NYX_ENTITY=mars ./run.sh --smoke"
      timeout: 30
      deve_passar: "boot ok"

  acceptance_criteria:
    - "NYX_AESTHETIC=arcano altera cor do banner/output observavel (scrot)"
    - "Default behavior identico a antes (paleta D)"
    - "Smoke ok em todas 6 aesthetics + 7 entities (varredura combinatoria reduzida)"
    - "Invariantes 14/14 (especialmente #6 hex e #14 glifos)"
```

---

# Sprint VISUAL-LAYOUT-CLI-CONSUME-01

**Status:** PENDENTE
**Data criação:** 2026-05-18 (anti-débito de VISUAL-LAYOUT-08)
**Modelo obrigatório:** claude-opus-4-7

---

## Contexto

VL-01 cria estrutura. VL-08 entrega controle (env/flag/command/API). Mas o CLI (cli.py + output.py + banner.py) ainda lê `design_tokens.py` direto — paleta D fixa. Trocar `NYX_AESTHETIC=arcano` muda env var mas nao a apresentacao real.

Esta sprint cabea o consumo: theme_manager torna-se fachada que delega.

## Solução proposta

1. `nyx/themes/theme_manager.py` ganha `resolve_palette()` cached que chama `design_tokens_extended.get_active()`.
2. `nyx/agent/output.py` consulta `theme_manager.resolve_palette()["palette"]["accent"]` em vez de `from nyx.themes.design_tokens import NYX_ACCENT`.
3. `nyx/agent/banner.py` idem.

Mudanças cirurgicas, sem refactor amplo. Cache via lru_cache para performance.

## Critério binário

- [ ] resolve_palette implementado
- [ ] output.py consome via theme_manager
- [ ] banner.py consome via theme_manager
- [ ] NYX_AESTHETIC=arcano muda cor no terminal (validação visual via scrot)
- [ ] Default preservado
- [ ] Invariantes 14/14
- [ ] Commit `refactor(VISUAL-LAYOUT-CLI-CONSUME-01): CLI consome design_tokens_extended.get_active() em runtime`

---

*"Controle sem propagação é só vidro pintado." — VISUAL-LAYOUT-CLI-CONSUME-01*
