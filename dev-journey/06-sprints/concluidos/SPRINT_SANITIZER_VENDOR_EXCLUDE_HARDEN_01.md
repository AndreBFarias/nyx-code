# SPRINT 257 — SANITIZER-VENDOR-EXCLUDE-HARDEN-01

## 0. SPEC

```yaml
sprint:
  id: SANITIZER-VENDOR-EXCLUDE-HARDEN-01
  title: "emoji_guardian.py exclui /vendor/ (defense-in-depth; allowlist ja protege, vendored nao deve ser tocado)"
  onda: 31
  prioridade: BAIXA
  tipo: Infra
  dependencias: [SANITIZER-WORKING-TREE-RESTORE-09]
  desbloqueia: []

  touches:
    - path: "~/Controle de Bordo/.sistema/scripts/emoji_guardian.py (EXTERNO ao repo Nyx-Code)"
      reason: "IGNORE_DIRS (linhas 106-112) nao inclui 'vendor'; o universal-sanitizer.py JA exclui via EXCLUDED_PATH_SUBSTRINGS '/vendor/'. Foi o emoji_guardian que corrompeu nyx/cockpit/static/vendor/xterm.js (U+25C6). A allowlist atual ja protege U+25C6, mas vendored nao deveria ser varrido."
  creates: []
  removes: []

  forbidden:
    - "Remover ou enfraquecer a allowlist centralizada (glyphs_canonicos.py)"
    - "Quebrar a remocao de emoji real (U+26A1 etc) em arquivos legitimos"
    - "Tocar o repo Nyx-Code: este fix e no ambiente do usuario (Controle de Bordo); registrar aqui por anti-debito"

  tests:
    - cmd: "bash ~/.config/zsh/scripts/tests/test_sanitizer_invariance.sh"
      timeout: 60
      deve_passar: true

  acceptance_criteria:
    - "emoji_guardian.py: 'vendor', 'third_party' adicionados a IGNORE_DIRS (paridade com universal-sanitizer EXCLUDED_PATH_SUBSTRINGS)"
    - "Teste: rodar emoji_guardian clean num dir com sub vendor/ -> arquivo vendored NAO e modificado"
    - "test_sanitizer_invariance.sh continua passando"
    - "Avaliar limpar o .pyc arquivado _desativados/emoji_guardian.cpython-310.pyc (vetor historico)"
```

---

# Sprint 257 — SANITIZER-VENDOR-EXCLUDE-HARDEN-01

**Status:** CONCLUIDA
**Data criacao:** 2026-05-25
**Data conclusão:** 2026-05-31 (fix no ambiente do usuário, externo ao repo)

## Contexto

Auditoria de 2026-05-25: o `emoji_guardian.py` (em `~/Controle de Bordo/.sistema/
scripts/`, EXTERNO ao repo Nyx-Code) tem `IGNORE_DIRS` sem 'vendor'. Foi ele que
corrompeu `nyx/cockpit/static/vendor/xterm.js` (U+25C6 removido) na janela
pre-allowlist. O `universal-sanitizer.py` ja exclui `/vendor/` via
`EXCLUDED_PATH_SUBSTRINGS`. A allowlist centralizada (criada hoje) ja protege
U+25C6, entao a recidiva nao se repete pelos sanitizers atuais — mas codigo
vendored/minificado nunca deveria ser varrido (defense-in-depth).

Nota de escopo: o arquivo e do ambiente do usuario, nao do repo. Registrado
aqui por anti-debito (feedback_nenhum_debito). Executar com cuidado cross-repo.

## Solucao

1. Adicionar 'vendor', 'third_party' a `IGNORE_DIRS` do emoji_guardian.py.
2. Considerar tambem `EXCLUDED_NAME_SUFFIXES` (.min.js etc) para paridade total
   com o universal-sanitizer.
3. Avaliar remover o `.pyc` arquivado em `_desativados/` (versao 3.10 sem
   allowlist; vetor historico latente).

## Acceptance

- [x] 'vendor'/'third_party' em IGNORE_DIRS.
- [x] Teste empirico: vendored nao e tocado.
- [x] test_sanitizer_invariance.sh PASSA.

## CONCLUSÃO 2026-05-31

Fix aplicado em `~/Controle de Bordo/.sistema/scripts/emoji_guardian.py` (EXTERNO ao repo Nyx-Code — não entra no commit; registrado aqui por anti-débito): `'vendor', 'third_party'` adicionados a `IGNORE_DIRS`. **Validado:** `py_compile` OK; teste empírico — emoji (U+26A1) em `vendor/lib.js` **preservado** (dir ignorado; "Arquivos processados: 1" exclui o vendor) e o mesmo emoji em `src/normal.md` **removido** (função primária do guardian preservada); `test_sanitizer_invariance.sh` 6/6 OK (rodado do CWD do universal-sanitizer). Repo Nyx intocado (smoke ok, invariantes 14/14). Itens OPCIONAIS não feitos (mínimo que resolve): `EXCLUDED_NAME_SUFFIXES` (.min.js) e limpeza do `.pyc` arquivado em `_desativados/` — ficam como nota caso ressurjam.

## Proof-of-work

```
mkdir -p /tmp/vt/vendor && printf 'x = "U+25C6 literal"\n' > /tmp/vt/vendor/lib.js
python3 "$HOME/Controle de Bordo/.sistema/scripts/emoji_guardian.py" clean /tmp/vt --apply
diff <(cat /tmp/vt/vendor/lib.js) <(printf 'x = "U+25C6 literal"\n')   # esperado: sem diff
bash ~/.config/zsh/scripts/tests/test_sanitizer_invariance.sh
```
