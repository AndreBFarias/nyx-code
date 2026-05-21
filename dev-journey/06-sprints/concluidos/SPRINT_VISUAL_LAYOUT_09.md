## 0. SPEC (machine-readable)

```yaml
sprint:
  id: VISUAL-LAYOUT-09
  title: "Banner duas camadas: aesthetic = estrutura (glyphs+cantos), entity = accent textual"
  onda: 24
  bloco: "24.2 Visual Layout"
  prioridade: BAIXA
  tipo: Feature
  dependencias: [VISUAL-LAYOUT-06, VL-CLI-CONSUME-01]
  desbloqueia: []

  touches:
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/agent/banner.py
      reason: "Banner consome current_glyphs() para cantos/linhas (vindos do aesthetic) e current_accent_hex() / current_ansi() para accent textual (continua vindo da entity via ADR-029); decoupling cirúrgico"
      linhas_alvo: "_build_compact + _build_wide + bloco de imports/_ANSI"

  creates: []
  removes: []

  n_to_n_pairs:
    - descricao: "current_glyphs() é fonte única em theme_manager; banner.py consome em vez de hardcoded BOX_CHARS"
      paths: [nyx/agent/banner.py, nyx/themes/theme_manager.py]

  forbidden:
    - "Alterar ADR-029 (entity = accent textual primary)"
    - "Hardcoded BOX_CHARS direto de design_tokens.py em banner.py (deve vir de current_glyphs())"
    - "Quebrar invariante #14 (glifos canônicos preservados)"
    - "Adicionar emoji ou menção a IA externa"
    - "Tocar nyx/cli.py, nyx/themes/, ou qualquer arquivo fora de nyx/agent/banner.py"

  tests:
    - cmd: "./run.sh --smoke"
      timeout: 10
      deve_passar: true
    - cmd: "bash scripts/sprint_invariants.sh"
      timeout: 30
      deve_passar: true
      assert: "PASS=14 FAIL=0"
    - cmd: "NYX_AESTHETIC=cyberpunk NYX_ENTITY=luna ./venv/bin/python -c 'from nyx.agent.banner import build_banner; print(build_banner(\"qwen2.5-coder:3b\", 35, \"Nyx-Code\"))'"
      timeout: 10
      deve_passar: true
      assert: "Output contém glifos cyberpunk (┏ ┓ ou similar) E cor accent luna (#BD93F9 ANSI)"
    - cmd: "NYX_AESTHETIC=brutalist NYX_ENTITY=nyx ./venv/bin/python -c 'from nyx.agent.banner import build_banner; print(build_banner(\"qwen2.5-coder:3b\", 35, \"Nyx-Code\"))'"
      timeout: 10
      deve_passar: true
      assert: "Output contém glifos brutalist (+ | ou similar) E cor accent nyx (#00D4AA ANSI)"

  acceptance_criteria:
    - "nyx/agent/banner.py consome current_glyphs() do theme_manager em vez de BOX_CHARS hardcoded de design_tokens"
    - "Accent textual continua vindo da entity (current_accent_hex() / current_ansi()) — ADR-029 preservado"
    - "Combinação cyberpunk+luna renderiza glifos cyberpunk + accent luna roxo"
    - "Combinação brutalist+nyx renderiza glifos brutalist + accent nyx teal"
    - "Default (aesthetic=default, entity=nyx) renderiza igual ao estado atual (regressão zero)"
    - "Smoke + invariantes 14/14"
    - "MASTER linha de VISUAL-LAYOUT-09 PENDENTE → CONCLUIDA"
```

---

# Sprint VISUAL-LAYOUT-09 — Banner consome aesthetic.glyphs + entity.accent (duas camadas)

**Status:** PENDENTE
**Data criação:** 2026-05-21
**Modelo obrigatório:** claude-opus-4-7 (executor-sprint via Agent tool)

---

## Contexto

ADR-029 (Layout Parity) estabelece que **entity** define o accent visual primary (cor da identidade — turquesa Nyx, roxo Luna, vermelho Mars, etc.). Aesthetic é camada de schema (estrutura visual, paleta secundária).

Atualmente o banner em `nyx/agent/banner.py`:
1. Linha 39: `_ANSI = current_ansi()` em import-time — consome `compose(aesthetic, entity)` mas com `entity` sobrescrevendo accent (intencional ADR-029)
2. Linhas 21-28: importa `BOX_CHARS` hardcoded de `design_tokens.py` — não consome `current_glyphs()` de `theme_manager`

Resultado:
- Glifos cyberpunk (`┏ ┓`), brutalist (`+ |`), editorial (`( )`) **nunca aparecem** no banner — sempre `╭ ╮ ╰ ╯` da paleta default
- Accent textual vem corretamente da entity (luna roxa, mars vermelho, etc.)

## Decisão de design (opção (c) confirmada pelo usuário 2026-05-21)

**Duas camadas:**
- `aesthetic` → estrutura visual: cantos, linhas, separadores (`current_glyphs()`)
- `entity` → accent textual: cor primary das labels, linha "100% offline", versão (`current_accent_hex()` / `current_ansi()`)

Preserva ADR-029 (entity = identidade visual primary, intocada) e libera o aesthetic para mostrar sua paleta estrutural real.

## Solução proposta

Em `nyx/agent/banner.py`:

1. **Remover** `from nyx.themes.design_tokens import BOX_CHARS` (linha 21-28 atual)
2. **Adicionar** `from nyx.themes.theme_manager import current_glyphs, current_ansi`
3. **Reescrever** o uso de BOX_CHARS para chamar `current_glyphs()` (chamada em build-time, não import-time, para permitir override via env var entre chamadas)
4. **Preservar** `_ANSI = current_ansi()` mantendo accent textual da entity

Funções a modificar: `_build_compact()` e `_build_wide()` ambas dentro de `nyx/agent/banner.py`.

## Arquivos alvo

`/home/andrefarias/Desenvolvimento/Nyx-Code/nyx/agent/banner.py`

Investigar primeiro via:
```bash
grep -n "BOX_CHARS\|current_glyphs\|current_ansi" nyx/agent/banner.py
grep -n "BOX_CHARS\|GLYPHS" nyx/themes/theme_manager.py
```

Verificar se `current_glyphs()` existe em `nyx/themes/theme_manager.py`. Se NÃO existir, criar como helper:
```python
def current_glyphs() -> dict[str, str]:
    """Retorna BOX_CHARS do aesthetic ativo (NYX_AESTHETIC env var)."""
    from nyx.themes.design_tokens_extended import get_active
    ae = get_active().get("aesthetic", "default")
    # Mapping aesthetic → glyphs (extender se necessário)
    return AESTHETIC_GLYPHS.get(ae, BOX_CHARS_DEFAULT)
```

## Diff esperado

```
~ 1 arquivo modificado (nyx/agent/banner.py)
+ ~15-25 linhas (imports + helper + refactor de uso)
- ~5-8 linhas (remoção de import e ocorrências hardcoded BOX_CHARS)
```

## Proof-of-work

```bash
# Antes
bash scripts/sprint_invariants.sh > /tmp/inv_before_vl09.txt 2>&1

# Implementar (Edit em nyx/agent/banner.py)

# Smoke + invariantes
./run.sh --smoke
bash scripts/sprint_invariants.sh > /tmp/inv_after_vl09.txt 2>&1

# Validação visual cyberpunk+luna (glifos cyberpunk + accent luna)
NYX_AESTHETIC=cyberpunk NYX_ENTITY=luna ./venv/bin/python -c '
from nyx.agent.banner import build_banner
out = build_banner("qwen2.5-coder:3b", 35, "Nyx-Code")
print(out)
assert "┏" in out or "┓" in out or "━" in out, "glifos cyberpunk ausentes"
print("OK cyberpunk glyphs")
'

# Validação visual brutalist+nyx
NYX_AESTHETIC=brutalist NYX_ENTITY=nyx ./venv/bin/python -c '
from nyx.agent.banner import build_banner
out = build_banner("qwen2.5-coder:3b", 35, "Nyx-Code")
print(out)
# brutalist usa + e | (ASCII) ou similar
print("OK")
'

# Regressão default
NYX_AESTHETIC=default NYX_ENTITY=nyx ./venv/bin/python -c '
from nyx.agent.banner import build_banner
out = build_banner("qwen2.5-coder:3b", 35, "Nyx-Code")
print(out)
assert "╭" in out, "default glyphs (╭╮╰╯) ausentes"
print("OK default")
'

# Acentuação
python3 ~/.config/zsh/scripts/validar-acentuacao.py --paths nyx/agent/banner.py
```

## Critério binário de aceite

- [ ] `nyx/agent/banner.py` consome `current_glyphs()` (ou helper similar) em vez de `BOX_CHARS` hardcoded
- [ ] Accent textual continua vindo da entity (current_ansi / current_accent_hex preservados)
- [ ] cyberpunk+luna renderiza glifos cyberpunk + cor luna
- [ ] brutalist+nyx renderiza glifos brutalist + cor nyx
- [ ] default+nyx idêntico ao estado atual (regressão zero)
- [ ] Smoke + invariantes 14/14 PASS
- [ ] Acentuação rc=0
- [ ] MASTER linha de VISUAL-LAYOUT-09 PENDENTE → CONCLUIDA
- [ ] Spec movida producao/ → concluidos/

## Gambiarras específicas

- **Anti-padrão #6 (modificar teste em vez de código):** se `current_glyphs()` não existir em theme_manager, NÃO baixar acceptance — criar o helper.
- **Anti-padrão #18 (sleep como fix):** glyphs não dependem de tempo; nada de sleeps.
- **Anti-padrão #21 (sucesso forjado):** executor DEVE renderizar banner real e capturar saída literal, não dizer "passou".

## Validação humana

```bash
# Visual
NYX_AESTHETIC=cyberpunk NYX_ENTITY=luna ./run.sh
# (Conferir banner mostra glifos cyberpunk + cor luna roxa)
```

## Riscos

| Risco | Mitigação |
|---|---|
| `current_glyphs()` não existe em theme_manager | Criar helper com mapping AESTHETIC_GLYPHS local; verificar via grep antes |
| Quebrar invariante #14 (glifos `○◐●` em banner.py) | Banner.py atualmente tem `●>=4` no check #14 — preservar |
| Aesthetic não tem glyphs próprios | Fallback para default (`╭╮╰╯`) é padrão; já é o comportamento atual |

---

*"O aesthetic é o ato; a entity é o ator." — princípio de duas camadas*
