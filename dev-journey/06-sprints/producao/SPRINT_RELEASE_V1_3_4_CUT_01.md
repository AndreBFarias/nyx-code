# SPRINT RELEASE-V1.3.4-CUT-01 — Corte da tag v1.3.4 (delegado ao humano)

## 0. SPEC

```yaml
sprint:
  id: RELEASE-V1.3.4-CUT-01
  title: "Corte da tag v1.3.4 (delegado ao humano)"
  onda: 39
  bloco: "39 Release"
  prioridade: BLOQUEADA_AGUARDA_HUMANO
  tipo: Release
  supersedes: RELEASE-V1.0-CUT-01
  dependencias: [DOC-RECONCILE-ONDA38-STATE-01]
  desbloqueia: []

  touches:
    - path: git
      reason: "Criar tag v1.3.4 anotada apontando para o HEAD validado"

  forbidden:
    - "A IA NUNCA corta a tag autonomamente"
    - "Não usar flags que escondam a mensagem do tag"

  comando_literal_pronto: |
    git tag -a v1.3.4 -m "Release v1.3.4: agente de codigo local, 100% offline"
    git push origin v1.3.4

  acceptance_criteria:
    - "Humano executa os 2 comandos quando se sentir confortavel"
    - "Tag v1.3.4 aparece nos releases do repositorio"
```

---

**Status:** PENDENTE (aguarda decisão humana — não há executor para esta)
**Data criação:** 2026-06-02
**Supersedes:** RELEASE-V1.0-CUT-01

---

## Por que v1.3.4 e não v1.0

A sprint original `RELEASE-V1.0-CUT-01` (2026-05-21) preparava a tag v1.0 com base
no estado daquela data. Desde então o projeto avançou seis ondas (32-38): migração
para Textual, redesign de UX, stack OOM, a alma documentada em ADRs (032-034) e a
reconciliação documental da ONDA-39. O `nyx/__version__.py` e o CHANGELOG já
registram **1.3.4**. Cortar uma tag "v1.0" agora seria incoerente com a versão
real; a decisão do dono (2026-06-02) foi cortar a tag alinhada: **v1.3.4**.

As tags `v1.0.0` / `v1.1.x` existentes no repositório são do port histórico (2025)
e permanecem como registro. A v1.3.4 é a primeira tag da fase madura pós-Textual.

---

## Gate (estado em 2026-06-02)

- [x] Smoke `boot ok` exit 0
- [x] Invariantes 14/14 PASS
- [x] `./venv/bin/python scripts/update_docs.py --check` exit 0 (docs sincronizados ao runtime)
- [x] `nyx/__version__.py` = 1.3.4 (alinhado ao CHANGELOG)
- [x] Working tree dos arquivos do projeto limpo (artefatos do gauntlet untracked por design)

---

## Comando literal pronto (humano)

```bash
git tag -a v1.3.4 -m "Release v1.3.4: agente de codigo local, 100% offline"
git push origin v1.3.4
```

---

*"Tudo pronto. Você corta a tag quando quiser."*
