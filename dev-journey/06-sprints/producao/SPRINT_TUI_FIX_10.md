# SPRINT TUI-FIX-10 — `/theme <id inexistente>` reporta "carregado" (fallback silencioso do ThemeManager)

## 0. SPEC (machine-readable)

```yaml
sprint:
  id: TUI-FIX-10
  title: "cmd_theme distingue tema inexistente de fallback silencioso do ThemeManager"
  onda: 22
  bloco: 2.8
  prioridade: MÉDIA
  tipo: Bugfix
  dependencias: [TUI-FIX-09]
  desbloqueia: [VALIDATE-ONDA-20]

  touches:
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/agent/commands/system.py
      reason: "cmd_theme deve verificar se o entity_id existe antes de chamar load_theme (que sempre retorna dict truthy via fallback Dracula)"
      linhas_alvo: "154-157"

  creates: []
  removes: []

  n_to_n_pairs: []

  forbidden:
    - "Mudar o contrato de ThemeManager.load_theme() para retornar None — outros callers dependem do fallback (get_ansi_colors, banner)"
    - "Remover o fallback Dracula do ThemeManager — é feature deliberada para boot robusto"
    - "Fixar via try/except ValueError — load_theme não lança, só loga warning"
    - "Tocar em arquivos fora do touches"
    - "Adicionar emoji, menção a IA"

  tests:
    - cmd: "./run.sh --gauntlet --only rapido"
      timeout: 120
    - cmd: "manual: /theme xyz-inexistente no REPL; saída deve conter 'não encontrado'"
      timeout: 30
    - cmd: "manual: /theme nyx no REPL; saída deve confirmar carregamento"
      timeout: 30

  acceptance_criteria:
    - "/theme <id inexistente> retorna mensagem 'Tema \"X\" não encontrado.' (comportamento atual prometido pelo próprio cmd_theme:157)"
    - "/theme <id válido> continua carregando normalmente"
    - "ThemeManager.load_theme() NÃO é alterado (mantém fallback Dracula para outros callers)"
    - "Gauntlet rapido 100%"
    - "Acentuação PT-BR correta"
```

---

**Status:** PENDENTE
**Data criação:** 2026-04-20
**Origem:** achado colateral durante execução de **TUI-FIX-09** (formatação do `/theme`). Teste programático de `cmd_theme('xyz-inexistente')` retornou `"Tema 'xyz-inexistente' carregado. Primary: #BD93F9"` em vez da mensagem de erro esperada. Causa: `ThemeManager.load_theme()` em `nyx/themes/__init__.py:44-61` faz fallback silencioso para `DRACULA_FALLBACK.copy()` quando o JSON da entidade não existe, sempre retornando dict truthy.
**Modelo obrigatório:** claude-opus-4-7 (sem subagentes)

---

## Contexto

`ThemeManager.load_theme` é usado em dois regimes:

1. **Boot / rendering (dominante):** `banner`, `get_ansi_colors`, etc. Precisam de fallback robusto — se JSON ausente, usar Dracula. Contrato correto.
2. **`cmd_theme` (REPL):** usuário quer feedback "tema existe ou não". Nesse caso o fallback **mente**: diz que carregou um tema que o usuário nunca viu.

A correção é no **consumidor** (cmd_theme), não no provider. O `ThemeManager` já expõe `list_themes()` e `get_theme_metadata()` — dá pra checar existência antes.

---

## Problema

### Sintoma observável

```
nyx> /theme xyz-inexistente
  Tema 'xyz-inexistente' carregado. Primary: #BD93F9
```

Esperado:

```
nyx> /theme xyz-inexistente
  Tema 'xyz-inexistente' não encontrado.
```

### Causa

`nyx/themes/__init__.py:52-54`:
```python
if not theme_path.exists():
    logger.warning("Tema '%s' não encontrado, usando fallback Dracula", entity_id)
    return DRACULA_FALLBACK.copy()
```

`nyx/agent/commands/system.py:154-157`:
```python
theme = tm.load_theme(args)
if theme:
    return f"  Tema '{args}' carregado. Primary: {theme.get('primary', '?')}"
return f"  Tema '{args}' não encontrado."
```

`load_theme` sempre retorna dict truthy. `if theme:` sempre True. Branch de erro é código morto.

---

## Solução proposta

Verificar existência via `list_themes()` (ou `ENTITIES_DIR / f"{id}.json".exists()`) antes de chamar `load_theme`:

```python
from nyx.themes import ThemeManager
tm = ThemeManager()
args = args.strip()
if not args or args == "list":
    # ... (bloco existente, intocado)
    ...
ids_validos = {t["id"] for t in tm.list_themes()}
if args not in ids_validos:
    return f"  Tema '{args}' não encontrado."
theme = tm.load_theme(args)
return f"  Tema '{args}' carregado. Primary: {theme.get('primary', '?')}"
```

**Alternativa considerada (descartada):** mudar `load_theme` para retornar `None` se não existir. Proibido pela gambiarra #1 — outros callers (`get_ansi_colors`, banner) dependem do fallback.

---

## Diff esperado

```
~ 1 arquivo modificado (cmd_theme em system.py)
+ ~5 linhas líquidas
```

---

## Comandos de verificação

```bash
bash scripts/sprint_invariants.sh > /tmp/inv_before.txt 2>&1

# Fix

./run.sh --smoke   # 'boot ok'

./run.sh
# /theme xyz        → "Tema 'xyz' não encontrado."
# /theme nyx        → "Tema 'nyx' carregado. Primary: #XXXXXX"
# /theme list       → lista formatada (comportamento TUI-FIX-09)
# Ctrl+D

./run.sh --gauntlet --only rapido
bash scripts/sprint_invariants.sh > /tmp/inv_after.txt 2>&1
diff /tmp/inv_before.txt /tmp/inv_after.txt
```

---

## Critério binário de aceite

- [ ] `/theme xyz` retorna "não encontrado"
- [ ] `/theme nyx` (ou outro id válido) carrega normalmente
- [ ] `load_theme` não foi alterado — outros callers intocados
- [ ] Gauntlet rapido 100%
- [ ] FAIL invariantes não regride; check #13 continua PASS

---

## Gambiarras específicas

1. **Mudar contrato de `load_theme` para `None`.** Quebra callers de boot/render. Proibido.
2. **Hard-code da lista de temas válidos em `cmd_theme`.** Viola single source of truth (`ENTITIES_DIR`).
3. **Usar `theme == DRACULA_FALLBACK`.** Impossível distinguir "fallback por erro" de "o usuário pediu luna que é Dracula-like".
4. **Silenciar o warning do ThemeManager.** Log é útil para boot diagnostics; problema é só no consumo do REPL.

---

## Proof-of-work obrigatório

- Transcript antes/depois do REPL com `/theme xyz-inexistente` e `/theme nyx`.
- Confirmação grep que `load_theme` não foi alterado: `git diff nyx/themes/__init__.py` deve ser vazio.
- Gauntlet rapido output.

---

## Riscos

| Risco | Mitigação |
|-------|-----------|
| `list_themes()` abre 7 arquivos JSON a cada `/theme <id>` | Aceitável — comando interativo, chamada rara; cache opcional em sprint futura se virar gargalo |
| Aliases de tema (se existirem) quebram a verificação de ID | Grep em `entities/*.json` por campo `aliases` antes do fix; se zero, seguir |

---

*"Uma abstração que mente é pior que nenhuma." -- paráfrase de Joel Spolsky*
