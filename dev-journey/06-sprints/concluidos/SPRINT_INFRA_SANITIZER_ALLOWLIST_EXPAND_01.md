# SPRINT 232 — INFRA-SANITIZER-ALLOWLIST-EXPAND-01

## 0. SPEC (machine-readable)

```yaml
sprint:
  id: INFRA-SANITIZER-ALLOWLIST-EXPAND-01
  title: "Adicionar ALLOWED_GLYPHS ao emoji_guardian.py (vetor raiz das 8 recidivas)"
  onda: 31
  prioridade: CRÍTICA
  tipo: Bugfix
  dependencias: [INFRA-SANITIZER-RECIDIVA-08, INFRA-SANITIZER-VENDOR-RESTORE-01]
  desbloqueia: []

  touches:
    - path: /home/andrefarias/Controle de Bordo/.sistema/scripts/emoji_guardian.py
      reason: "Vetor raiz das recidivas: santuario hook chama clean . --apply sem distinguir glifos canônicos da Nyx (U+25xx range). Touch autorizado pelo usuário explicitamente."
  creates: []
  removes: []

  forbidden:
    - "Alterar lógica de detecção de emojis reais (apenas adicionar exceções)"
    - "Quebrar funcionamento em outros projetos (Luna, etc.)"

  tests:
    - cmd: "python3 '/home/andrefarias/Controle de Bordo/.sistema/scripts/emoji_guardian.py' clean ."
      timeout: 30
      deve_passar: true
    - cmd: "bash scripts/sprint_invariants.sh"
      timeout: 30
      deve_passar: true

  acceptance_criteria:
    - "ALLOWED_GLYPHS adicionado ao emoji_guardian.py espelhando universal-sanitizer.py linhas 104-116"
    - "clean_emojis_from_text preserva ALLOWED_GLYPHS via _repl helper igual ao universal-sanitizer.py"
    - "Rodar emoji_guardian.py clean . --apply no Nyx-Code: ZERO arquivos modificados (glifos preservados)"
    - "Invariantes 14/14 PASS após o teste"
    - "santuario Nyx-Code próximo boot: [ALERTA] 0 arquivos com emojis"
```

---

# Sprint 232 — INFRA-SANITIZER-ALLOWLIST-EXPAND-01

**Status:** CONCLUIDA
**Data criação:** 2026-05-25
**Data conclusão:** 2026-05-25
**Modelo obrigatório:** claude-opus-4-7 (sem subagentes)

---

## Contexto

Validação 2026-05-25 do usuário confirmou empíricamente o vetor raiz:

```
SANTUARIO: Nyx-Code
...
Verificando emojis...
[ALERTA] 14 arquivo(s) com emojis
Limpando automaticamente...
[OK] Emojis removidos
```

Localização do vetor: `~/.config/zsh/functions/projeto.zsh:249-260` invoca:
```
python3 "$BORDO_DIR/.sistema/scripts/emoji_guardian.py" clean . --apply
```

`emoji_guardian.py:51-61 EMOJI_MISC` casa `-` que inclui TODOS os glifos canônicos da Nyx (U+25CB ○, U+25CF ●, U+25D0 ◐, U+25C6 ◆). Script NÃO tem `ALLOWED_GLYPHS` — destrói tudo.

VECTOR-AUDIT-01 (2026-05-21) absolveu o `universal-sanitizer.py` (que TEM ALLOWED_GLYPHS), mas não examinou o `emoji_guardian.py`. Esse foi o blind spot.

Recidivas afetadas: 06 (2026-05-21), 07 (2026-05-22), 08 (2026-05-25), VENDOR-01 (xterm.js, 2026-05-25). Todas seriam evitadas se o emoji_guardian preservasse os glifos canônicos.

## Fix aplicado

Adicionar `ALLOWED_GLYPHS` ao `emoji_guardian.py` espelhando `universal-sanitizer.py:104-116`. Modificar `clean_emojis_from_text` para usar `_repl` helper que preserva caracteres em ALLOWED_GLYPHS.

Touch autorizado pelo usuário (arquivo fora do repo Nyx-Code mas com autorização explícita: "adiciona os... sanitizer global pra evitar que ele quebre os nossos emojis da nyx").

## Diff esperado

```
~ 1 arquivo modificado (fora do repo Nyx-Code)
+ ~20 linhas líquidas
```

## Proof-of-work

```bash
# Snapshot ANTES (vetor ativo)
python3 "$HOME/Controle de Bordo/.sistema/scripts/emoji_guardian.py" clean . --apply 2>&1 | head -3
# Sintoma: dezenas de arquivos modificados

# Aplicar fix
# Edit em emoji_guardian.py adicionando ALLOWED_GLYPHS + _repl helper

# Re-rodar (vetor neutralizado)
python3 "$HOME/Controle de Bordo/.sistema/scripts/emoji_guardian.py" clean . --apply 2>&1 | head -3
# Esperado: 0 arquivos modificados em Nyx-Code

# Confirmar invariantes
bash scripts/sprint_invariants.sh
# Esperado: PASS=14/14 FAIL=0
```

---

*"Defesa global é defesa real. Lista de exceções local não fecha o vetor." — princípio anti-débito raiz*
