# SPRINT SANITIZER-GUARDIAN-DOC-PRESERVE-01 — guardian para de corromper docs de dev-journey

## 0. SPEC (machine-readable)

```yaml
sprint:
  id: SANITIZER-GUARDIAN-DOC-PRESERVE-01
  title: "O emoji_guardian.py (externo) deixa de stripar glifos citados em dev-journey/*.md, fechando a FONTE da corrupção que a 345 só defendia no commit"
  onda: 41
  bloco: "41 -- sanitizer na fonte"
  prioridade: MEDIA
  tipo: Infra / Defesa anti-sanitizer (FONTE)
  dependencias: [INFRA-SANITIZER-DOC-GUARD-EXTEND-01]
  desbloqueia: []

  touches:
    - path: /home/andrefarias/.config/zsh/scripts/emoji_guardian.py
      reason: "EXTERNO AO REPO. Escaneia .md (extensão permitida, L147) e tira emoji incluindo U+26A1 -- foi ele que stripou 24 ocorrências em 7 docs de dev-journey em 2026-06-02. IGNORE_DIRS (L133) já tem vendor/third_party (257) mas não cobre docs por path."
      linhas_alvo: "IGNORE_DIRS / should_check_file / _preserve_allowed_in_match / scan_directory"

  forbidden:
    - "Executar sem autorização explícita do dono (touch EXTERNO ao repo -- regra do projeto)"
    - "Desligar o guardian inteiro (perde a defesa anti-emoji no código/output)"
    - "Adicionar emoji literal, menção a IA"

  decisao_de_design_em_aberto:
    - "Opção A (preserva glifo literal nos docs -- alinha com a reversão feita hoje): excluir dev-journey/ do scan do guardian (path-based, análogo a vendor). Docs viram registro histórico intocável."
    - "Opção B (alinha com 'emoji = REGRA ABSOLUTA'): guardian REPLACE em vez de DELETE nos docs (glifo -> texto `U+26A1`), preservando o sentido. Aí não sobra emoji literal e o emoji-check do pre-commit fica feliz."
    - "A escolha A/B define também a 347 (emoji-check). Decisão do dono na execução."

  tests:
    - cmd: "rodar o guardian sobre uma cópia de SPRINT_UX_DESIGN_01.md"
      timeout: 30
      esperado: "U+26A1 preservado (opção A) ou convertido para texto sem corromper a frase (opção B); nunca apagado para vazio"
    - cmd: "git status após o guardian rodar no repo"
      timeout: 15
      esperado: "zero modificação em dev-journey/*.md"

  acceptance_criteria:
    - "O guardian rodando sobre o repo não modifica nenhum dev-journey/*.md"
    - "A defesa anti-emoji no código de produção (nyx/) permanece intacta"
    - "Complementa a 345: a 345 pega no commit (rede), esta fecha a fonte (guardian)"
```

---

**Status:** CONCLUIDA (2026-06-02; decisão **A** -- preserva o glifo nos docs. `emoji_guardian.py` externo editado com OK do dono: `IGNORE_DIRS += 'dev-journey'` (análogo a vendor) + guarda `if 'dev-journey' in Path(filepath).parts` no `clean_file` (defesa em profundidade). Proof: probe RED->GREEN -- doc de dev-journey preservado (U+26A1 fica), `code.py` fora de dev-journey segue stripado; `clean_file` direto num doc real retorna (0,0); AST OK, acento rc=0. Arquivo externo ao repo, não commitável aqui)
**Data criação:** 2026-06-02
**Origem:** durante a ONDA-40 o `emoji_guardian.py` corrompeu 7 docs (24 U+26A1 stripados). A 345 (`INFRA-SANITIZER-DOC-GUARD-EXTEND-01`) foi a rede defensiva no commit; a fonte (o guardian escaneando .md de dev-journey) continua aberta. A 257 (`SANITIZER-VENDOR-EXCLUDE-HARDEN-01`) já adicionou vendor/third_party ao IGNORE_DIRS, mas isso protege código vendored, não docs.
**Modelo obrigatório:** claude-opus (sem subagentes)

## Notas

- **Touch externo:** o arquivo vive em `~/.config/zsh/scripts/`, fora do repo Nyx-Code. Por regra do projeto, editar exige OK explícito do dono no dispatch de execução.
- **Par com a 347:** a decisão A/B aqui amarra a 347 (se A, o emoji-check precisa de exceção de path para docs; se B, os docs já não têm emoji literal e o emoji-check passa naturalmente).
