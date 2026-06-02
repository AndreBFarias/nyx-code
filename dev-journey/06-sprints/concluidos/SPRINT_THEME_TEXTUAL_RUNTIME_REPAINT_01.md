# SPRINT ONDA-38 (anti-débito) — THEME-TEXTUAL-RUNTIME-REPAINT-01

## 0. SPEC (machine-readable)

```yaml
sprint:
  id: THEME-TEXTUAL-RUNTIME-REPAINT-01
  title: "Repintar a TUI Textual em runtime ao trocar aesthetic/schema (apply + persist)"
  onda: 38
  prioridade: MEDIA
  tipo: Feature
  origem: "achado de THEME-TEXTUAL-WIRE-01 (bloco D) -- anti-débito"
  acceptance_criteria:
    - "trocar aesthetic via /aesthetic select repinta os widgets Textual em runtime (sem restart)"
    - "a escolha persiste em ~/.nyx/config.toml (sobrevive a restart)"
    - "smoke boot ok + invariantes 14/14"
```

---

**Status:** PENDENTE
**Data criação:** 2026-06-01
**Modelo obrigatório:** sem subagentes (Read/Grep/Glob direto)

---

## Contexto (por que esta sprint existe)

THEME-TEXTUAL-WIRE-01 (bloco D) tirou o `_open_select_modal` do STUB: o modal de
seleção agora mostra as aesthetics/schemas REAIS e, ao escolher, seta a env var
(`NYX_AESTHETIC`/`NYX_SCHEMA`) + `theme_manager.clear_cache()`. Porém a troca **não
repinta a TUI em runtime**, por uma razão arquitetural confirmada na execução de D:

- `nyx/themes/design_tokens.py` define as cores como CONSTANTES estáticas
  hard-coded (`NYX_ACCENT = "#00D4AA"`, etc.), congeladas no import.
- Os widgets Textual (`nyx/agent/tui/widgets/*`, `banner.py`) importam essas
  constantes diretamente; NENHUM consome `theme_manager.resolve_palette()` /
  `resolve_active()` (a paleta dinâmica). Verificado: `rg resolve_palette
  nyx/agent/tui/ nyx/agent/banner.py` retorna vazio.
- Logo, setar `NYX_AESTHETIC` + `clear_cache()` não tem efeito visual no Textual;
  e a escolha nem persiste (env do processo morre no exit).

## Escopo proposto (a definir na execução)

Duas frentes, a serem dimensionadas:

1. **Apply em runtime**: fazer os widgets/banner lerem a paleta dinâmica
   (`resolve_palette()`/`resolve_active()`) em vez das constantes estáticas, OU
   um mecanismo de re-mount que recompute as cores após `clear_cache()`. Avaliar
   o custo de migrar os consumidores de `design_tokens` (constantes) para o
   theme_manager (dinâmico) sem quebrar o check #14 anti-sanitizer (que protege
   glifos U+25xx nesses arquivos) nem a estabilidade do event loop Textual.
2. **Persistência**: gravar a escolha em `~/.nyx/config.toml` (reusar o padrão
   merge não-destrutivo de `onboarding._persist_user_name`) para sobreviver a
   restart. Era não-objetivo explícito de D.

## Riscos

- `design_tokens.py` está no conjunto protegido do check #14 — migrar para paleta
  dinâmica exige cuidado para não tocar os glifos canônicos U+25xx.
- Re-mount de widgets no Textual pode ter custo/efeitos colaterais; medir antes
  de escalar.

## Referências

- Origem: `dev-journey/06-sprints/producao/SPRINT_THEME_TEXTUAL_WIRE_01.md` (bloco D)
- `nyx/themes/theme_manager.py` (resolve_palette/resolve_active/clear_cache)
- `nyx/themes/design_tokens.py` (constantes estáticas — alvo da migração)
- BRIEF: seção "Defesa anti-sanitizer" (check #14)

---

*"O modal já carrega a escolha; falta a tela mudar de cor com ela."*
