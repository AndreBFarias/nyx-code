## 0. SPEC (machine-readable)

```yaml
sprint:
  id: TUI-STATE-GLYPHS-SYNC-06
  title: "Consolidar _STATE_GLYPHS em fonte única e remover divergência cli.py vs repl_app.py"
  onda: 29
  prioridade: ALTA
  tipo: Refactor
  dependencias: []
  desbloqueia: [TUI-INPUT-DEADLOCK-01]

  touches:
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/cli.py
      reason: "Substituir definição local de _STATE_GLYPHS por import do módulo canônico"
      linhas_alvo: "70-80"
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/agent/repl_app.py
      reason: "Substituir definição local de _STATE_GLYPHS (atualmente com espaços vazios) por import"
      linhas_alvo: "92-100"
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/themes/design_tokens.py
      reason: "Hospedar STATE_GLYPHS canônico"

  n_to_n_pairs:
    - descricao: "_STATE_GLYPHS existe em 2 lugares (cli.py:75 e repl_app.py:95) com valores diferentes — uma cópia tem espaços vazios"  # noqa-acento (chave YAML canônica do template V2)
      paths: [nyx/cli.py, nyx/agent/repl_app.py]

  forbidden:
    - "Adicionar emoji"
    - "Mudar visualmente os glifos de cli.py (são canônicos via Geometric Shapes U+25CB/25D0/25CF)"
    - "Deixar repl_app.py com espaços vazios"
    - "Quebrar invariante #14 (Geometric Shapes presença) do sprint_invariants.sh"

  tests:
    - cmd: "./run.sh --smoke"
      timeout: 60
      deve_passar: true
    - cmd: "bash scripts/sprint_invariants.sh"
      timeout: 30
      deve_passar: true

  acceptance_criteria:
    - "grep -rn 'STATE_GLYPHS' nyx/ retorna 1 definição (design_tokens.py) + N imports — zero duplicação"
    - "repl_app.py:_STATE_GLYPHS não existe mais como definição local"
    - "Toolbar do REPL exibe glifo Geometric Shape (não espaço) em todos os 3 estados (cold/warming/warm)"
    - "Smoke boot OK, invariantes 14/14 PASS, sem regressão visual"
```

---

# Sprint TUI-STATE-GLYPHS-SYNC-06 — Consolidar _STATE_GLYPHS

**Status:** PENDENTE
**Data criação:** 2026-05-21
**Modelo obrigatório:** claude-opus-4-7 (sem subagentes)

---

## Contexto do projeto (snapshot)

> - ADR-001 Local First; ADR-004 Zero Emojis; ADR-006 PT-BR; ADR-013 Integração Obrigatória.
> - Python 3.10+, modelo qwen2.5-coder:3b porta 11435, proxy 11436.
> - 35 tools, 67 commands. cli.py ~790 linhas.
> - Sprint anterior pública: TUI-REDESIGN-28-08c-PARTE-3 CONCLUIDA.

---

## Problema

`_STATE_GLYPHS` está definido em dois arquivos com **valores divergentes**:

- `nyx/cli.py:75` usa glifos Geometric Shapes (Circle Outline / Half / Filled): `chr(0x25CB)`, `chr(0x25D0)`, `chr(0x25CF)`. Esses glifos são protegidos pelo invariante #14 do `scripts/sprint_invariants.sh` (anti-sanitizer).
- `nyx/agent/repl_app.py:95` tem `_STATE_GLYPHS = {"cold": " ", "warming": " ", "warm": " "}` — **espaços vazios em vez de glifos**. Não há defesa anti-sanitizer aqui.

A divergência tem dois efeitos:

1. **Visual:** o toolbar exibe um ponto bullet quando o REPL usa o PromptSession legacy (cli.py) e fica em branco quando usa a Application (repl_app.py).
2. **Suspeito (a confirmar runtime):** os espaços vazios podem estar corrompendo o render do toolbar dentro da Application e potencialmente bloqueando o input loop — hipótese principal do bug do input travado (`TUI-INPUT-DEADLOCK-01`).

Esta sprint vai primeiro, antes do diagnóstico de input, porque pode resolver o bug raiz sozinha.

---

## Solução proposta

Mover `_STATE_GLYPHS` para `nyx/themes/design_tokens.py` (já é o módulo canônico de glifos/cores e tem proteção anti-sanitizer via `chr(0xNNNN)`). Importar em ambos os arquivos.

---

## Arquivos alvo

### `/home/andrefarias/Desenvolvimento/Nyx-Code/nyx/themes/design_tokens.py`

**Adicionar (próximo dos demais glifos):**

```python
STATE_GLYPHS = {
    "cold":    chr(0x25CB),
    "warming": chr(0x25D0),
    "warm":    chr(0x25CF),
}
```

**Justificativa:** este módulo já protege Geometric Shapes via `chr()` (BRIEF §Defesa anti-sanitizer). Centralizar aqui mantém o invariante #14 com fonte única.

### `/home/andrefarias/Desenvolvimento/Nyx-Code/nyx/cli.py` (linhas ~70-80)

**Antes:**
```python
_STATE_GLYPHS = {
    "cold":    chr(0x25CB),
    "warming": chr(0x25D0),
    "warm":    chr(0x25CF),
}
```

**Depois:**
```python
from nyx.themes.design_tokens import STATE_GLYPHS as _STATE_GLYPHS
```

### `/home/andrefarias/Desenvolvimento/Nyx-Code/nyx/agent/repl_app.py` (linhas ~92-100)

**Antes:**
```python
_STATE_GLYPHS = {"cold": " ", "warming": " ", "warm": " "}
```

**Depois:**
```python
from nyx.themes.design_tokens import STATE_GLYPHS as _STATE_GLYPHS
```

**Mudanças:** remoção da divergência. Ambos os caminhos passam a usar a mesma fonte. O caminho Application volta a exibir glifo visível.

---

## Diff esperado

```
~ 3 arquivos modificados
+ 5 linhas (def em design_tokens) + 2 imports
- 7 linhas (defs locais duplicadas)
```

---

## Comandos de verificação

```bash
# 1. Garantir 1 definição + 2 imports
grep -rn "STATE_GLYPHS" nyx/

# 2. Confirmar que repl_app.py não tem mais espaços vazios em _STATE_GLYPHS
grep -n "_STATE_GLYPHS" nyx/agent/repl_app.py

# 3. Invariantes (especialmente #14 Geometric Shapes anti-sanitizer)
bash scripts/sprint_invariants.sh

# 4. Smoke boot
./run.sh --smoke

# 5. Validação visual: rodar TUI e confirmar glifo no toolbar do REPL
./run.sh
# (esperado: toolbar mostra "○ cold" ou "◐ warming" ou "● warm")
```

---

## Critério binário de aceite

- [ ] `grep -rn "STATE_GLYPHS" nyx/` mostra 1 definição (`design_tokens.py`) + 2 imports (cli.py + repl_app.py)
- [ ] `grep "_STATE_GLYPHS" nyx/agent/repl_app.py` retorna apenas linha de import
- [ ] `bash scripts/sprint_invariants.sh` → PASS 14/14
- [ ] `./run.sh --smoke` → `boot ok` exit 0
- [ ] Toolbar do REPL exibe glifo Geometric Shape em runtime (validação visual `validacao-visual`)  <!-- noqa-acento (nome canônico do plugin, BRIEF §CORE) -->
- [ ] `ruff` zero novos warnings
- [ ] Acentuação PT-BR (`validar-acentuacao.py --paths`) rc=0

---

## Riscos

| Risco | Mitigação |
|-------|-----------|
| Importação circular se design_tokens importar de nyx.cli | design_tokens não importa nyx.cli — relação é unidirecional |
| Hook commit-msg consumir linha com path acentuado | Mensagem de commit em ASCII puro (BRIEF §Hook commit-msg) |
| Invariante #14 falhar se chr() não for preservado | Já uso chr(0x25CB)/chr(0x25D0)/chr(0x25CF), pattern empírico do BRIEF |

---

*"Uma fonte, uma verdade." -- princípio Nyx-Code.*
