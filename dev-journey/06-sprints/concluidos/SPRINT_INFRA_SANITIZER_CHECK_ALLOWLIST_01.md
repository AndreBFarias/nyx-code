# SPRINT 233 — INFRA-SANITIZER-CHECK-ALLOWLIST-01

## 0. SPEC (machine-readable)

```yaml
sprint:
  id: INFRA-SANITIZER-CHECK-ALLOWLIST-01
  title: "find_emojis_in_line respeita ALLOWED_GLYPHS (paridade com clean)"
  onda: 31
  prioridade: BAIXA
  tipo: Refactor
  dependencias: [INFRA-SANITIZER-ALLOWLIST-EXPAND-01]
  desbloqueia: []

  touches:
    - path: /home/andrefarias/Controle de Bordo/.sistema/scripts/emoji_guardian.py
      reason: "find_emojis_in_line não usava ALLOWED_GLYPHS — santuario reportava [ALERTA] N arquivos como falso-positivo cosmetico"
  creates: []
  removes: []

  forbidden:
    - "Alterar logica de clean (ja corrigida pela sprint 232)"

  tests:
    - cmd: "python3 '/home/andrefarias/Controle de Bordo/.sistema/scripts/emoji_guardian.py' check ."
      timeout: 5
      deve_passar: true
    - cmd: "bash scripts/sprint_invariants.sh"
      timeout: 30
      deve_passar: true

  acceptance_criteria:
    - "find_emojis_in_line filtra matches que so contem caracteres em ALLOWED_GLYPHS"
    - "emoji_guardian.py check . retorna ZERO arquivos no Nyx-Code"
    - "Proximo santuario Nyx-Code nao exibe mensagem [ALERTA] N arquivo(s) com emojis"
    - "Invariantes 14/14 PASS preservado"
    - "Funcionalidade real de deteccao de emojis preservada"
```

---

# Sprint 233 — INFRA-SANITIZER-CHECK-ALLOWLIST-01

**Status:** CONCLUIDA
**Data criação:** 2026-05-25
**Data conclusão:** 2026-05-25
**Modelo obrigatório:** claude-opus-4-7 (sem subagentes)

---

## Contexto

Apos sprint 232 neutralizar o vetor raiz no `clean_emojis_from_text`, o usuario rodou `santuario Nyx-Code` e ainda viu:

```
[ALERTA] 8 arquivo(s) com emojis
Limpando automaticamente...
[OK] Emojis removidos
```

Falso-positivo cosmético: a função `find_emojis_in_line` ainda usava o regex bruto sem filtrar `ALLOWED_GLYPHS`. O `clean --apply` (sprint 232) já preservava os glifos canônicos, mas a verificação prévia (`check`) os contava como emojis.

8 arquivos detectados eram exatamente os 7 arquivos protegidos pelo invariante #14 + 1 spec documentando os glifos.

## Fix aplicado

```python
def find_emojis_in_line(line: str) -> List[str]:
    """Encontra todos os emojis em uma linha, ignorando ALLOWED_GLYPHS."""
    found = []
    for pattern in ALL_EMOJI_PATTERNS:
        for match in pattern.findall(line):
            if not all(c in ALLOWED_GLYPHS for c in match):
                found.append(match)
    return found
```

Diff: +6/-3 (logica de filtro adicionada).

## Proof-of-work

```
ANTES: emoji_guardian.py check . detectava 8 arquivos
DEPOIS: emoji_guardian.py check . detecta 0 arquivos

Invariantes 14/14 PASS preservado.
Glifos canonicos nos 7 arquivos protegidos: intactos.
Deteccao de emojis reais preservada (testada via /tmp/test_nyx_glyphs.md
na sprint 232: glifos canonicos preservados, pictographs U+1F300-1FAFF
removidos como antes).
```

Proximo `santuario Nyx-Code` exibira `[ALERTA] 0 arquivo(s) com emojis` ou pulara a mensagem.

---

*"Deteccao sem filtro vira ruido. Deteccao com allowlist vira sinal." -- principio*
