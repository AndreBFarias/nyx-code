# SPRINT OUTPUT-STYLES-01 — Estilos de output (default, concise, learning)

## 0. SPEC (machine-readable)

```yaml
sprint:
  id: OUTPUT-STYLES-01
  title: "Estilos de saída (default, concise, learning) afetando system_prompt + tom de render"
  onda: 23
  bloco: 23.5 Feature parity Claude Code
  prioridade: MÉDIA
  tipo: Feature
  dependencias: [PERF-INFERENCE-01]
  desbloqueia: []
  origem: "Auditoria estratégica 2026-05-16 — gap real vs Claude Code: zero 'output_style' em nyx/. Claude Code tem learning mode, concise, default; Nyx tem só um tom hardcoded."

  touches:
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/agent/prompt.py
      reason: "build_system_prompt aceita output_style; injeta hint de tom (default/concise/learning)"
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/config/settings.py
      reason: "NyxSettings.output_style (default='default')"
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/cli.py
      reason: "Banner mostra estilo ativo; comando /output-style integrado"

  creates:
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/agent/output_style.py
      reason: "Registry de estilos: cada estilo é um dict com hint_prompt + max_words + tom"
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/agent/commands/output_style.py
      reason: "Slash commands: /output-style list, /output-style set <name>, /output-style get"

  removes: []

  n_to_n_pairs:
    - descricao: "Lista de estilos disponíveis em output_style.py — fonte única, settings e commands importam"
      paths:
        - /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/agent/output_style.py
        - /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/config/settings.py
        - /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/agent/commands/output_style.py

  forbidden:
    - "Estilo modifica funcionalidade de tools (só afeta tom da resposta)"
    - "Estilo desabilita ADRs (zero emoji, PT-BR, etc. são invariantes em TODOS estilos)"
    - "Hardcoded de nomes de estilos espalhados (única fonte em output_style.py)"
    - "Estilo 'learning' implica explicar TUDO sempre (cabe ao prompt do usuário pedir)"
    - "Emoji"

  tests:
    - cmd: "./venv/bin/python -c 'from nyx.agent.output_style import STYLES; print(list(STYLES.keys()))'"
      timeout: 10
      deve_passar: true
      nota: "Deve imprimir ['default', 'concise', 'learning']"
    - cmd: "./run.sh --gauntlet --only rapido"
      timeout: 300
      deve_passar: true
    - cmd: "bash scripts/sprint_invariants.sh"
      timeout: 60
      deve_passar: "FAIL_AFTER <= FAIL_BEFORE"

  acceptance_criteria:
    - "nyx/agent/output_style.py define pelo menos 3 estilos: default, concise, learning"
    - "Cada estilo tem: name, hint_prompt (texto inserido no system_prompt), max_words (soft hint), description"
    - "NyxSettings.output_style persiste em config.toml"
    - "/output-style list mostra estilos disponíveis"
    - "/output-style set <name> aplica imediatamente (próxima request usa)"
    - "/output-style get retorna estilo atual"
    - "Banner do Nyx mostra estilo atual quando não é 'default'"
    - "Build_system_prompt inclui hint_prompt do estilo ativo"
    - "Invariantes mantidos em todos estilos: PT-BR, zero emoji, zero menção a IA, ADR-024"
    - "PT-BR; zero emoji; zero menção a IA"
```

---

**Status:** PENDENTE
**Data criação:** 2026-05-16
**Modelo obrigatório:** claude-opus-4-7 (sem subagentes)

---

# Sprint OUTPUT-STYLES-01

## Estilos canônicos

| Nome | hint_prompt (snippet) | Quando usar |
|---|---|---|
| `default` | (vazio — usa apenas o system_prompt base Nyx) | Trabalho normal |
| `concise` | "Responda de forma mínima. Frases curtas. Zero floreio. Apenas o essencial." | Dev experiente, sessões longas |
| `learning` | "Explique o porquê das decisões. Ofereça contexto. Quando possível, peça para o usuário escrever pequenos trechos." | Onboarding, ensino |

## Estrutura

```python
# nyx/agent/output_style.py
STYLES = {
    "default": {
        "hint_prompt": "",
        "max_words": None,
        "description": "Tom padrão do Nyx",
    },
    "concise": {
        "hint_prompt": "Responda de forma mínima. Frases curtas. Zero floreio.",
        "max_words": 80,
        "description": "Respostas curtas e diretas",
    },
    "learning": {
        "hint_prompt": "Explique o porquê. Ofereça contexto. Convide o usuário a contribuir.",
        "max_words": None,
        "description": "Tom didático para aprendizado",
    },
}
```

---

*"Tom é a metade do conteúdo." -- princípio de comunicação aplicado a CLI*
