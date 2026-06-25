# SPRINT CI-ANONYMITY-FIX-01 -- anonymity-check.yml tem `fi` orfao (bloco de trailer sem `if`), trava o CI

## 0. SPEC (machine-readable)

```yaml
sprint:
  id: CI-ANONYMITY-FIX-01
  title: "anonymity-check.yml:72-75 tem echo+FAIL=1+fi orfaos -- falta o `if` da checagem de trailer de coautoria; erro de sintaxe bash que faz o step 'Auditar mensagens de commit' falhar SEMPRE; se for required check, trava todo push"
  onda: 46
  bloco: "46 -- Saneamento de CI & Working Tree + achados da Onda de Validação 1"
  prioridade: ALTA
  tipo: Bugfix / CI (BLOCKER)
  dependencias: []
  desbloqueia: []

  touches:
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/.github/workflows/anonymity-check.yml
      reason: "linhas 71-75: apos SUBJECT=..., ha um bloco ORFAO `echo '::error::...trailer de coautoria...'; FAIL=1; fi` SEM o `if ...; then` correspondente -> `fi` sem `if` = erro de sintaxe bash; o step inteiro aborta. Falta a checagem do trailer de coautoria. O NOREPLY_RE (linha 57) esta DEFINIDO mas NUNCA USADO -- e exatamente o regex que essa checagem ausente deveria consumir (alem de Co[-]Authored[-]By + TOOL_RE)."
      linhas_alvo: "71-75 (inserir o `if` ausente antes do echo da linha 73)"

  creates: []
  removes: []

  forbidden:
    - "Apenas deletar o bloco orfao (echo/FAIL/fi) -- isso 'conserta' a sintaxe mas REMOVE a defesa de trailer de coautoria, que e o proposito do arquivo (comentario L3-4). Tem que RESTAURAR o `if`."
    - "Deixar o NOREPLY_RE morto -- a checagem restaurada deve usa-lo (era pra isso que foi definido)"
    - "Tocar os outros steps (range, arquivos de instrucao) ou as outras 3 checagens (subject TOOL_RE, author/committer email) que ja funcionam"
    - "Quebrar o caso legitimo: commits SEM trailer de coautoria devem passar (os 8 commits da ONDA-45 nao tem trailer)"

  tests:
    - cmd: "bash -n no script extraido do step 'Auditar mensagens de commit'"
      timeout: 60
      esperado: "sintaxe valida (exit 0) -- hoje da erro `syntax error near unexpected token fi`"
    - cmd: "teste funcional do regex de trailer: MSG sintetica com um trailer `Co[-]Authored[-]By:` cujo nome casa TOOL_RE e/ou um email que casa NOREPLY_RE -> FAIL=1; MSG limpa (ex.: mensagem real de um commit da ONDA-45) -> nao dispara"
      timeout: 60
      esperado: "positivo dispara, negativo nao (anti-gambiarra #8: testar os dois caminhos)"
    - cmd: "bash scripts/sprint_invariants.sh"
      timeout: 180
      esperado: "14/14 PASS (inalterado)"
    - cmd: "yamllint .github/workflows/anonymity-check.yml (se disponivel)"
      timeout: 30
      esperado: "sem erro de sintaxe YAML"

  acceptance_criteria:
    - "O bloco orfao vira um `if ...; then ... fi` completo que detecta trailer de coautoria na MSG"
    - "A checagem usa NOREPLY_RE + Co[-]Authored[-]By + TOOL_RE (deixa de ser dead code)"
    - "bash -n do script extraido = exit 0 (sintaxe valida)"
    - "Teste funcional: trailer dispara FAIL; commit limpo passa"
    - "As outras 3 checagens (subject/author/committer) intactas; o 2o step (arquivos) intacto"
    - "Invariantes 14/14; spec -> concluidos/"
```

---

**Status:** CONCLUIDA (cff053e)
**Data criacao:** 2026-06-24
**Origem:** Wave 0 (AUDIT_2026_06_24.md, dimensao 6, achado BLOCKER). O `git status` inicial e a leitura do arquivo confirmam: `.github/workflows/anonymity-check.yml:72-75` tem um bloco `echo/FAIL=1/fi` sem o `if` correspondente.
**Modelo obrigatorio:** modelo de raciocinio principal (sem subagentes; implementação direta)

---

## Problema

`.github/workflows/anonymity-check.yml`, step "Auditar mensagens de commit":

```bash
71  SUBJECT=$(printf '%s\n' "$MSG" | head -1)
72
73              echo "::error::commit $SHA tem trailer de coautoria com IA"
74              FAIL=1
75            fi
```

O `fi` (75) nao tem `if` (perdido em algum edit anterior). Bash falha ao parsear o script -> o step aborta com `syntax error near unexpected token 'fi'`. Como o workflow roda em `push`/`pull_request` para `main` e o comentario (L3-9) diz que e "status check obrigatorio ... defesa server-side ultima", se estiver marcado como required em branch protection, NENHUM push passa. Alem disso, a defesa de trailer de coautoria (o proposito #1 do arquivo) nao existe na pratica. E `NOREPLY_RE` (L57) esta definido mas nunca usado -- pista de que a checagem que o consumiria foi a que se perdeu.

---

## Causa-raiz

Um edit anterior removeu o `if printf '%s\n' "$MSG" | grep -qiE '<trailer de coautoria>'; then` que abria o bloco das linhas 73-75, deixando o corpo e o `fi` orfaos.

---

## Solucao proposta

Inserir, antes da linha 73, a condicao ausente que detecta trailer de coautoria na mensagem completa (`MSG`), reusando os regex ja definidos no proprio arquivo:

```bash
SUBJECT=$(printf '%s\n' "$MSG" | head -1)

if printf '%s\n' "$MSG" | grep -qiE "[cC]o-[aA]uthored-[bB]y:.*($TOOL_RE)|($NOREPLY_RE)"; then
  echo "::error::commit $SHA tem trailer de coautoria com IA"
  FAIL=1
fi
```

Isso (a) fecha a sintaxe, (b) restaura a defesa de trailer, (c) usa `NOREPLY_RE` (deixa de ser dead code). O executor deve confirmar a indentacao do bloco `run:` e o nome exato das variaveis (`TOOL_RE`, `NOREPLY_RE`, `MSG`, `SHA`).

Nota de implementacao: o regex usa classes de caractere (`[cC]o-[aA]uthored-[bB]y`) em vez da string literal porque o auto-fix de coautoria do pre-commit (`scripts/hooks/pre-commit`, passo [2/6]) deleta qualquer linha que contenha a string literal -- as classes detectam o trailer real na MSG sem disparar o auto-fix.

---

## Proof-of-work esperado

```bash
# extrair o script do step e validar sintaxe (copiar o bloco run: para /tmp/anon.sh)
bash -n /tmp/anon.sh                       # exit 0 (hoje: syntax error near 'fi')
# teste funcional dos dois caminhos (sem citar provedor por extenso -- usar fragmento que casa TOOL_RE):
#  - MSG com 'Co[-]Authored[-]By: <nome que casa TOOL_RE>' OU email que casa NOREPLY_RE -> a checagem dispara FAIL=1
#  - MSG = mensagem real de um commit da ONDA-45 (sem trailer) -> nao dispara
bash scripts/sprint_invariants.sh           # 14/14 PASS
# yamllint .github/workflows/anonymity-check.yml  (se disponivel)
```

---

## Criterio binario de aceite

- [ ] `if` restaurado; `bash -n` do script extraido = exit 0
- [ ] checagem usa NOREPLY_RE + Co[-]Authored[-]By + TOOL_RE
- [ ] teste funcional: trailer dispara, commit limpo passa
- [ ] outras checagens + 2o step intactos
- [ ] invariantes 14/14; spec -> concluidos/

---

## Riscos

| Risco | Mitigacao |
|-------|-----------|
| Regex pega commit legitimo (falso-positivo) | Testar com as mensagens reais dos commits da ONDA-45 (sem trailer) -- devem passar |
| Indentacao do `run:` YAML quebra | `bash -n` + yamllint apos o fix |
| NOREPLY_RE casar email legitimo do dono | NOREPLY_RE so casa noreply de provedores; o email do dono (gmail) nao casa |

---

*"Um portao trancado com a fechadura caida no chao nao tranca nada -- so atrapalha quem tem a chave." -- anonimo*
