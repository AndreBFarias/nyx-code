# SPRINT INFRA-EMOJI-CHECK-DOC-NOQA-01 — emoji-check do pre-commit deixa de barrar docs que citam glifos

## 0. SPEC (machine-readable)

```yaml
sprint:
  id: INFRA-EMOJI-CHECK-DOC-NOQA-01
  title: "O emoji-check do pre-commit ganha uma exceção consciente para docs de dev-journey que citam glifos, resolvendo a tensão que impede recommitar os docs grandfathered"
  onda: 41
  bloco: "41 -- sanitizer na fonte"
  prioridade: BAIXA
  tipo: Infra / Hooks
  dependencias: [SANITIZER-GUARDIAN-DOC-PRESERVE-01]
  desbloqueia: []

  touches:
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/scripts/hooks/pre-commit
      reason: "O bloco '# 6. Emojis' (L240-256) escaneia STAGED_ALL com `git show :file` no range \\x{2600}-\\x{26FF} (inclui U+26A1) SEM exceção de path. Bloquearia recommitar SPRINT_UX_DESIGN_01.md (16 U+26A1 grandfathered). E o emoji é 'REGRA ABSOLUTA (sem noqa)' por decisão (L27) -- então a exceção precisa ser deliberada."
      linhas_alvo: "240-256 (bloco emoji)"

  forbidden:
    - "Abrir noqa-emoji genérico no código de produção (mataria a defesa anti-emoji em nyx/)"
    - "Adicionar emoji literal, menção a IA"

  decisao_de_design_em_aberto:
    - "Opção A (se a 346 escolher preservar glifo): adicionar exceção de PATH no emoji-check só para dev-journey/**/*.md (análogo às exclusões reference/, 09-legacy/ já presentes nos outros checks). Emoji segue absoluto em código/output."
    - "Opção B (se a 346 escolher de-emojificar docs): NÃO mexer no emoji-check -- com docs sem glifo literal, o check passa sozinho. Esta sprint vira no-op / cancelada."
    - "A 346 decide A/B; esta sprint só existe de fato no cenário A."

  tests:
    - cmd: "git add SPRINT_UX_DESIGN_01.md && rodar o pre-commit (dry)"
      timeout: 30
      esperado: "cenário A: passa (exceção de path); código com emoji em nyx/ continua bloqueado"

  acceptance_criteria:
    - "Cenário A: um doc de dev-journey com U+26A1 citado pode ser commitado; nyx/**/*.py com emoji continua bloqueado"
    - "A exceção é explícita e comentada (decisão consciente sobre a regra absoluta), não um noqa silencioso"
```

---

**Status:** CONCLUIDA (2026-06-02; cenário **A** da 346. Exceção de path `case "$file" in dev-journey/*) continue` no bloco emoji do pre-commit (L242-248). Proof: `bash -n` OK; replica fiel da lógica -- dev-journey SKIP, `nyx/code.py` com emoji BLOQUEIA, limpo passa; teste REAL -- doc de dev-journey com U+26A1 literal staged passa o pre-commit (`Zero emojis [OK]`), emoji em código segue absoluto; acento rc=0)
**Data criação:** 2026-06-02
**Origem:** ao documentar a corrupção do sanitizer no Checkpoint, o próprio emoji-check do pre-commit bloqueou a escrita do glifo literal. Os docs em HEAD têm U+26A1 grandfathered, mas o emoji-check (absoluto, sem path-exception) impediria recommitá-los após qualquer edição -- forçando `--no-verify`, que também pularia o guard anti-sanitizer.
**Modelo obrigatório:** claude-opus (sem subagentes)

## Notas

- **Acoplada à 346:** a decisão preserva-glifo (A) vs de-emojifica (B) da 346 determina se esta sprint é necessária. Por isso ambas nascem juntas na ONDA-41 e a 346 é dependência.
- **Precedente:** já existe `_has_noqa_marker` no pre-commit (acento/anonimato/cli-externo), mas emoji foi deixado de fora de propósito (L27). A exceção aqui é por PATH, não por marcador inline, justamente para não reabrir noqa-emoji no código.
