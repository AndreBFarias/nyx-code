# SPRINT RELEASE-V1.0-CUT-01 — Corte da tag v1.0 (delegado ao humano)

## 0. SPEC

```yaml
sprint:
  id: RELEASE-V1.0-CUT-01
  title: "Corte da tag v1.0 (delegado ao humano)"
  onda: 28
  bloco: "28.0 Release"
  prioridade: BLOQUEADA_AGUARDA_HUMANO
  tipo: Release
  dependencias: [DOC-CHANGELOG-V1RC-01, PROJECT-SNAPSHOT-CLOSE-V1-01, AUDIT-FINAL-V1-01]
  desbloqueia: []

  touches:
    - path: git
      reason: "Criar tag v1.0 anotada apontando para HEAD validado"

  creates: []
  removes: []

  forbidden:
    - "Eu (Claude) NUNCA corto a tag autonomamente"
    - "Não usar git tag --no-edit ou flags que escondam a mensagem"
    - "Não pular hooks de assinatura GPG se houver"

  comando_literal_pronto: |
    git tag -a v1.0 -m "Release v1.0: Claude Code offline opensource"
    git push origin v1.0

  acceptance_criteria:
    - "Humano executa os 2 comandos acima quando se sentir confortável"
    - "Tag v1.0 aparece em github.com/[REDACTED]/nyx-code/releases"
    - "CHANGELOG entry [1.3.0-rc1] é promovida para [1.3.0] no mesmo dia (sprint follow-up)"
```

---

**Status:** PENDENTE (aguarda decisão humana — não há executor-sprint para esta)
**Data criação:** 2026-05-21
**Modelo obrigatório:** N/A (humano executa)

---

## Pré-requisitos (gate v1.0 — 16 critérios) — TODOS SATISFEITOS em 2026-05-21:

- [x] 0 RASCUNHO em `dev-journey/06-sprints/producao/` (exceto esta)
- [x] 0 PENDENTE bloqueante no MASTER (5 anti-débitos BAIXA não bloqueiam release)
- [x] 0 CONCLUIDA_PARCIAL com pendência ativa (3 fechadas em 2026-05-21)
- [x] 0 DEFERIDA bloqueante
- [x] Smoke `boot ok` exit 0
- [x] Invariantes 14/14 PASS
- [x] Gauntlet completo 225/225 (100%) em 252s
- [x] `audit_help_coverage.py` 67/67 OK
- [x] `microcopy_audit.py --check` exit 0
- [x] `validar-acentuacao.py --paths` exit 0 em todos arquivos modificados
- [x] `ruff check nyx/ scripts/` exit 0 (All checks passed)
- [x] `sbom_sync.py --check` exit 0 (36/62 features verde via gauntlet, 26 meta-features)
- [x] `CHANGELOG.md` cobre Ondas 22-28 (entry [1.3.0-rc1])
- [x] `PROJECT_SNAPSHOT.md` atualizado para 2026-05-21
- [x] `README.md` contagens corretas (35 tools, 67 commands, 15 services)
- [x] `git status` clean (exceto Checkpoint.md untracked por design)

---

## Comando literal pronto (humano):

```bash
git tag -a v1.0 -m "Release v1.0: Claude Code offline opensource"
git push origin v1.0
```

---

## Após a tag

1. Promover entry `[1.3.0-rc1]` → `[1.3.0]` no CHANGELOG (sprint follow-up: `DOC-CHANGELOG-V1-PROMOTE-01`)
2. Atualizar `PROJECT_SNAPSHOT.md`: status muda de "v1.3.0-rc1 ready" → "v1.0 released"
3. Anunciar release no README com badge ou seção dedicada

---

*"Tudo pronto. Você corta a tag quando quiser."*
