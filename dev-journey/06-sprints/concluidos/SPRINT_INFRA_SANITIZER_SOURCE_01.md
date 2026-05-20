# SPRINT INFRA-SANITIZER-SOURCE-01 -- Diagnóstico do vetor que destruiu 57 arquivos do working tree

## 0. SPEC

```yaml
sprint:
  id: INFRA-SANITIZER-SOURCE-01
  title: "Diagnóstico: vetor de regressão sanitizer que destruiu 57 arquivos do working tree"
  onda: 24
  bloco: 24.5 Release (anti-débito)
  prioridade: CRITICA
  tipo: Investigação
  dependencias: []
  desbloqueia: [INFRA-SANITIZER-FIX-04]

  touches:
    - path: dev-journey/06-sprints/concluidos/SPRINT_INFRA_SANITIZER_SOURCE_01.md
      reason: "Documentação literal do vetor identificado"

  creates: []
  removes: []

  forbidden:
    - "Modificar ~/.config/zsh/scripts/universal-sanitizer.py (versão atual já está correta)"
    - "Renomear/bloquear o sanitizer (não é mais ameaça ativa)"

  tests:
    - cmd: "echo 'glyph_test: ● ○ ◐ ◼ ◻ ▶ ▼ ▸ ◆ ◇' > /tmp/test_glyph.txt && python3 ~/.config/zsh/scripts/universal-sanitizer.py /tmp/test_glyph.txt && cat /tmp/test_glyph.txt"
      timeout: 5
      deve_passar: "string idêntica preservada (bytes e2 97 8f, e2 97 8b, e2 97 90 mantidos)"

  acceptance_criteria:
    - "Vetor identificado com path absoluto"
    - "Versão antiga (destrutiva) vs versão nova (segura) comparadas literalmente"
    - "Confirmado empiricamente que a versão atual NÃO destrói os glifos"
    - "Plano de defesa em camadas registrado para INFRA-SANITIZER-FIX-04"
```

---

**Status:** CONCLUIDA (2026-05-19)
**Data:** 2026-05-19
**Modelo:** claude-opus-4-7 (sessão validador/integrador/despachador)

## Achado

Na auditoria inicial da sessão 2026-05-19, encontrei o working tree com **57 arquivos modificados não-commitados**, todos com perda sistemática de Unicode Geometric Shapes:

- `nyx/cli.py:75` → `_STATE_GLYPHS = {"cold": "", "warming": "", "warm": ""}` (era `{"cold": "○", "warming": "◐", "warm": "●"}`)
- `nyx/agent/banner.py` → glifos `●` removidos em 4 sítios
- `nyx/themes/design_tokens.py` → BULLETS dict perdeu `●/○/◐`; TOOL_GLYPHS perdeu `▸/◇/◆`
- `nyx/agent/output.py` → `◼/◻/▶` removidos em `render_todo_block`/`render_thinking_block`
- `nyx/agent/repl_app.py`, `nyx/themes/design_tokens_extended.py`: similar
- `scripts/sprint_invariants.sh:220` → a PRÓPRIA defesa neutralizada: `if cli.count("○") < 1` virou `if cli.count("") < 1` (comparação contra string vazia, sempre PASS falso)
- `nyx/cockpit/static/vendor/xterm.js` → 553KB diff
- 45 docs (.md) com perda de acentuação PT-BR e glifos
- 4 JSX em `novo_layout/v2_referencias/`

`bash scripts/sprint_invariants.sh` retornava 14/14 PASS — **mas falso**, pois o check #14 estava neutralizado pelo próprio ataque.

## Investigação forense

1. **`~/.claude/settings.json` hooks:** nenhum hook ativo invoca `universal-sanitizer.py` (apenas `guardian.py`, `aurora-checkpoint.py`, `post-plan-clear.py`, `session-start-briefing.py`).

2. **`~/.config/git/hooks/pre-commit:289-299`:** invoca `universal-sanitizer.py` como camada adicional pós auto-fix de emoji/coautor/IA. Re-stage arquivos modificados (linha 295-297).

3. **`~/.config/zsh/scripts/universal-sanitizer.py`** (mtime 2026-05-18 21:25:35):
   - Versão atual tem `ALLOWED_GLYPHS = {○ ◐ ● ◆ ◇ ▶ ▼ ▸ ◼ ◻ ↗}` (linha 76-88)
   - Função `_strip_emojis_preserving_allowed` (linha 91-103): preserva glifos do allowed set mesmo dentro da faixa `U+25AA-U+25FE` capturada pelo `EMOJI_RE`.

4. **`git log -- scripts/universal-sanitizer.py` em ~/.config/zsh:**
   - `7ac4fd2` (2026-05-19 17:57) — sync nitro-5 (sincronização entre máquinas)
   - `b0b2de3` (2026-04-15 18:38) — sync anterior
   - `ecf2b3c` (anterior) — `fix: restaurar variaveis e identidade removidas pelo auto-sanitize` (indicação de incidente prévio)
   - `9448650` (inicial) — feat configuração zsh modular

5. **Versão ANTIGA (commit `b0b2de3`, 2026-04-15):**
   ```python
   content, n = EMOJI_RE.subn("", content)  # remove TUDO sem allowed
   report["emojis"] = n
   ```
   **Esta é a versão culpada.** Removia todos os matches da faixa `U+25AA-U+25FE` (incluindo `●/○/◐/◼/◻/▶/▼/▸/◆/◇`) sem preservar nada.

6. **Verificação empírica da versão ATUAL:**
   ```bash
   echo 'glyph_test: ● ○ ◐ ◼ ◻ ▶ ▼ ▸ ◆ ◇' > /tmp/test_glyph.txt
   python3 ~/.config/zsh/scripts/universal-sanitizer.py /tmp/test_glyph.txt
   cat /tmp/test_glyph.txt
   # → "glyph_test: ● ○ ◐ ◼ ◻ ▶ ▼ ▸ ◆ ◇" (bytes idênticos, preservado)
   ```

## Diagnóstico literal

As 57 modificações são **resíduo histórico** de uma execução da **versão antiga** do `universal-sanitizer.py` (anterior ao commit `7ac4fd2`/`b0b2de3` que introduziu `ALLOWED_GLYPHS`). Os arquivos foram destruídos em algum momento entre as datas dos commits do sanitizer, mas as modificações nunca foram commitadas — ficaram como working tree pending até hoje.

A **versão atual** do sanitizer (mtime 2026-05-18 21:25) está **correta** e **NÃO** representa ameaça ativa contínua.

## Defesa em camadas (delegada para INFRA-SANITIZER-FIX-04)

1. Reverter os 57 arquivos via `git checkout HEAD -- <files>` (sprint INFRA-SANITIZER-FIX-04)
2. Endurecer invariante #14 em `scripts/sprint_invariants.sh`:
   - Cobertura ampliada para `nyx/agent/banner.py`, `nyx/agent/repl_app.py`, `nyx/themes/design_tokens_extended.py`
   - Auto-proteção: count dos próprios glifos na definição do check
3. Pre-commit hook local em `.git/hooks/pre-commit` (no projeto, não global) que recusa diff staged com remoção de Unicode Geometric Shapes (U+25A0-U+25FF)
4. Não bloquear `universal-sanitizer.py` (versão atual está correta)

## Anti-débito derivado

Caso o sanitizer atual venha a regredir em sync futuro (sincronização nitro-5 ou outra máquina): defesas das fases 2-4 acima recusariam a mudança nos commits do Nyx-Code.

## Proof-of-work

```
[pre]
git status --short | wc -l → 57 (modificados não-commitados)
bash scripts/sprint_invariants.sh → 14/14 PASS (falso positivo, check 14 neutralizado)

[evidencia]
git diff scripts/sprint_invariants.sh:220 → 'if cli.count("○") < 1' virou 'if cli.count("") < 1'
git diff nyx/cli.py:75 → '_STATE_GLYPHS = {"cold": "○", "warming": "◐", "warm": "●"}' virou '{"cold": "", "warming": "", "warm": ""}'

[teste empirico]
echo 'glyph_test: ● ○ ◐ ◼ ◻ ▶ ▼ ▸ ◆ ◇' > /tmp/test_glyph.txt
python3 ~/.config/zsh/scripts/universal-sanitizer.py /tmp/test_glyph.txt
hexdump -C /tmp/test_glyph.txt | head -1
→ '67 6c 79 70 68 5f 74 65 73 74 3a 20 e2 97 8f 20' (preservado)
```

## Touches

- `dev-journey/06-sprints/concluidos/SPRINT_INFRA_SANITIZER_SOURCE_01.md` (este arquivo)

## Creates

(nenhum código novo — apenas documentação)

---

*"Conheça seu inimigo. Ele já se foi, mas deixou pegadas." -- INFRA-SANITIZER-SOURCE-01*
