# SPRINT INFRA-PRECOMMIT-NO-OWNER-WIP-01 -- o pre-commit força-stageia dois docs majoritariamente-manuais e arrasta o WIP do dono para o commit do executor

## 0. SPEC (machine-readable)

```yaml
sprint:
  id: INFRA-PRECOMMIT-NO-OWNER-WIP-01
  numero: 408
  title: "O hook pre-commit (seção 7) roda update_docs.py e depois git add em 7 docs, incluindo GAMBIARRAS_POR_SPRINT.md e SPRINT_TEMPLATE_V2.md, que carregam prosa MANUAL do dono alem de contagens; como o git add pega o arquivo INTEIRO, qualquer WIP não-commitado do dono nesses dois docs e força-staged e vaza para o commit do executor"
  onda: 48
  bloco: "48 -- Validação as-user a-fundo"
  prioridade: MEDIA
  tipo: Infra / Higiene (git / pre-commit)
  dependencias: []
  desbloqueia: []

  touches:
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/scripts/hooks/pre-commit
      reason: "Correcao load-bearing (Opção B). Remover as duas linhas de continuacao dev-journey/08-templates/SPRINT_TEMPLATE_V2.md e dev-journey/08-templates/GAMBIARRAS_POR_SPRINT.md da lista do laco `for doc in ...` (hoje linhas 279-280) para que o hook pare de força-stageá-los."
      linhas_alvo: "279-280 (lista do laco força-stage na seção 7); ajustar o `; do` para a linha do PROJECT_SNAPSHOT.md"
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/scripts/update_docs.py
      reason: "Reforco (Opção A). Remover as duas chamadas de update_sprint_template e update_gambiarras em main() (hoje linhas 746-747 e 753-754) e as duas funções orfas (update_gambiarras 600-627, update_sprint_template 630-655) para que update_docs.py pare de ESCREVER nesses dois docs majoritariamente-manuais; assim eles não ficam sujos-unstaged no working tree numa mudanca de contagem."
      linhas_alvo: "call-sites 746-747 e 753-754 em main(); defs orfas 600-627 e 630-655"

  creates: []
  removes: []

  forbidden:
    - "Remover GUIDE.md, README.md, PORT_STATUS.md, ARCHITECTURE.md ou PROJECT_SNAPSHOT.md do laco força-stage do hook (esses seguem auto-derivaveis e devem continuar sincronizados e staged)"
    - "Remover a linha `cli_lines = _count_cli_lines()` ou a função `_count_cli_lines` do update_docs.py: `cli_lines` segue usada pelo print de diagnostico em main() (`print(f\"  cli.py:    {cli_lines} linhas\")`); apaga-la quebra o print e/ou gera F841 no ruff"
    - "Desabilitar a seção 7 inteira do hook ou o `--check` do update_docs: o objetivo e cirurgico (parar de tocar SO os dois docs manuais), não remover o auto-sync"
    - "Editar o conteudo de GAMBIARRAS_POR_SPRINT.md ou SPRINT_TEMPLATE_V2.md (a prosa deles e do dono; a sprint so muda quem os toca automaticamente, não o texto)"

  tests:
    - cmd: "bash -n scripts/hooks/pre-commit"
      timeout: 30
      esperado: "exit 0 (sintaxe do hook valida apos remover as 2 linhas do laco)"
    - cmd: "grep -n 'GAMBIARRAS_POR_SPRINT\\|SPRINT_TEMPLATE_V2' scripts/hooks/pre-commit"
      timeout: 30
      esperado: "VAZIO (exit 1) -- os dois docs não aparecem mais na lista de força-stage do hook"
    - cmd: "grep -n 'update_gambiarras\\|update_sprint_template' scripts/update_docs.py"
      timeout: 30
      esperado: "VAZIO (exit 1) -- call-sites e defs orfas removidos"
    - cmd: "python3 scripts/update_docs.py && git status --short dev-journey/08-templates/GAMBIARRAS_POR_SPRINT.md dev-journey/08-templates/SPRINT_TEMPLATE_V2.md"
      timeout: 60
      esperado: "os dois docs NÃO aparecem como modificados apos rodar update_docs (deixou de toca-los)"
    - cmd: "/home/andrefarias/.local/bin/ruff check scripts/update_docs.py"
      timeout: 60
      esperado: "All checks passed (sem F841 de cli_lines, sem dead-code residual)"
    - cmd: "bash scripts/sprint_invariants.sh"
      timeout: 180
      esperado: "PASS 14/14 FAIL 0 (rodar quando a GPU estiver livre -- check #13 smoke exige proxy/ollama)"

  acceptance_criteria:
    - "O hook pre-commit não força-stageia SPRINT_TEMPLATE_V2.md nem GAMBIARRAS_POR_SPRINT.md"
    - "WIP manual simulado nesses dois docs NÃO entra no indice quando a seção 7 do hook roda"
    - "update_docs.py deixou de escrever nesses dois docs (Opção A -- reforço)"
    - "Os outros 5 docs auto-derivaveis (GUIDE, README, PORT_STATUS, ARCHITECTURE, PROJECT_SNAPSHOT) seguem sincronizados e force-staged"
    - "ruff limpo, acentuacao exit 0, invariantes 14/14, smoke boot ok; spec -> concluidos/"
```

---

**Status:** PENDENTE
**Data criação:** 2026-07-12
**Origem:** Achado recorrente dos executores das sprints 393-396 (registrado na tabela do bloco ONDA-48 do SPRINT_ORDER_MASTER, linha 408, entre MANUAL_OVERRIDE_ONDA_48_START/END). O `git add` da seção 7 do hook pega o arquivo inteiro, entao qualquer edicao manual não-commitada do dono nesses dois docs vaza para o commit do executor.
**Modelo obrigatorio:** modelo principal local (sem subagentes; implementação direta)

---

## Problema

O hook `scripts/hooks/pre-commit`, na seção "7. Auto-atualizar docs" (linhas 265-286), roda `update_docs.py` (sem `--check`, portanto ESCREVE) e em seguida percorre um laco `for doc in ...` que faz `git add "$PROJECT_ROOT/$doc"` em sete documentos:

```
GUIDE.md  README.md  dev-journey/PORT_STATUS.md
dev-journey/02-architecture/ARCHITECTURE.md
dev-journey/08-templates/PROJECT_SNAPSHOT.md
dev-journey/08-templates/SPRINT_TEMPLATE_V2.md
dev-journey/08-templates/GAMBIARRAS_POR_SPRINT.md
```

Dois deles -- `SPRINT_TEMPLATE_V2.md` e `GAMBIARRAS_POR_SPRINT.md` -- sao **majoritariamente-manuais**: carregam prosa do dono (guia de template, catalogo de gambiarras) alem de um único numero-exemplo que `update_docs.py` mantem sincronizado. Como `git add <arquivo>` estagia o arquivo INTEIRO (não so o pedaco que a ferramenta mudou), se o dono tiver WIP não-commitado nesses dois docs no momento em que um executor commita a própria sprint, o hook força-stageia essa prosa manual e ela vaza para o commit do executor. O executor entao "arrasta" trabalho do dono sem intencao.

---

## Causa-raiz

Duas condicoes somadas:

1. O laco `git add` da seção 7 e **incondicional por doc**: ele estagia os sete arquivos sempre que `update_docs.py --check` retorna não-zero (isto e, sempre que QUALQUER um dos docs ou o meta-check de cobertura precisa de atualizacao) -- inclusive os docs que aquele run especifico não alterou. Basta o README precisar de um numero novo para o laco disparar e força-stagear tambem o GAMBIARRAS com o WIP do dono dentro.
2. `git add` de um path estagia o conteudo inteiro do arquivo, não um hunk. Não existe granularidade que separe "a contagem que a ferramenta mexeu" da "prosa manual do dono".

Confirmacao empirica de que o vetor e EXCLUSIVO do hook: `grep -n 'git add' run.sh` retorna vazio -- o `run.sh --gauntlet` (linha 839) e o modo interativo (linha 854) chamam `update_docs.py` mas nunca fazem `git add`. Logo, so a seção 7 do pre-commit estagia esses docs.

---

## Solução proposta (abordagem recomendada)

A correcao **load-bearing** e a **Opção B** (o hook para de força-stageá-los). A Opção A sozinha (update_docs.py parar de toca-los) **NÃO resolve** o problema, porque o `git add` do hook e incondicional por doc: mesmo sem a ferramenta escrever no GAMBIARRAS, o laco ainda executaria `git add GAMBIARRAS_POR_SPRINT.md` e arrastaria o WIP do dono. Por isso a Opção B e obrigatoria.

A **Opção A** entra como **reforço** na mesma sprint: sem ela, `update_docs.py` continuaria ESCREVENDO o numero-exemplo nesses dois docs (numa eventual mudanca de contagem) e, como o hook não os estagia mais, eles ficariam sujos-unstaged no working tree -- exatamente o tipo de ruido permanente que o projeto ja combateu em WORKTREE-BASELINES-01. Remover a escrita torna os dois docs plenamente do dono: nem auto-escritos, nem auto-staged.

### Passo 1 -- Opcao B (obrigatoria): hook para de força-stageá-los

No `scripts/hooks/pre-commit`, remover as duas linhas de continuacao (hoje 279-280) da lista do laco `for doc in ...` e ajustar o `; do` para fechar na linha do `PROJECT_SNAPSHOT.md` (hoje 278). A lista final força-stageia apenas os cinco docs plenamente auto-derivaveis:

```
GUIDE.md  README.md  dev-journey/PORT_STATUS.md
dev-journey/02-architecture/ARCHITECTURE.md
dev-journey/08-templates/PROJECT_SNAPSHOT.md
```

### Passo 2 -- Opcao A (reforço): update_docs.py para de escrever nesses dois docs

No `scripts/update_docs.py`, remover em `main()` as duas chamadas condicionais:

- `if update_sprint_template(tools, commands, services, cli_lines, args.check): changes.append("SPRINT_TEMPLATE_V2.md")` (hoje 746-747)
- `if update_gambiarras(tools, commands, args.check): changes.append("GAMBIARRAS_POR_SPRINT.md")` (hoje 753-754)

E remover as duas funções que ficam orfas: `update_gambiarras` (600-627) e `update_sprint_template` (630-655). Grep confirmou zero referencias externas a essas duas funções.

MANTER intactos `cli_lines = _count_cli_lines()` e a função `_count_cli_lines`: `cli_lines` segue usada pelo print de diagnostico de `main()` (`print(f"  cli.py:    {cli_lines} linhas")`), entao NÃO ha cascata de F841 no ruff e nada mais precisa ser removido.

### Escopo deliberadamente NÃO tocado

- `PROJECT_SNAPSHOT.md` permanece no laco força-stage. O achado nomeia apenas os dois docs; `update_project_snapshot` diz tocar so celulas de tabela (partes narrativas preservadas). Se no futuro o dono comprovar drag de WIP tambem nele, abrir follow-up (ver Anti-debito).
- O texto/prosa dos dois docs não e editado por esta sprint.

---

## Aritmetica / superficie do diff

Sprint de higiene (sem meta de linhas de refactor). Superficie esperada:

- `scripts/hooks/pre-commit`: -2 linhas (as duas continuacoes da lista) + reposicionamento do `; do`. Sem mudanca logica no restante da seção 7.
- `scripts/update_docs.py`: -4 linhas em `main()` (dois `if`/`append`) e -~55 linhas das duas funções orfas. `_count_cli_lines` e `cli_lines` permanecem.

Verificação pré-execução (lição 7): confirmar que os numeros de linha ainda batem com `grep -n 'for doc in\|SPRINT_TEMPLATE_V2\|GAMBIARRAS_POR_SPRINT\|git add' scripts/hooks/pre-commit` e `grep -n 'update_gambiarras\|update_sprint_template\|cli_lines' scripts/update_docs.py` antes de editar.

---

## Proof-of-work esperado

Comandos GPU-livres (podem rodar agora):

```bash
# 1. Sintaxe do hook valida apos a edicao
bash -n scripts/hooks/pre-commit

# 2. Os dois docs sumiram da lista de força-stage
grep -n 'GAMBIARRAS_POR_SPRINT\|SPRINT_TEMPLATE_V2' scripts/hooks/pre-commit   # esperado VAZIO (exit 1)

# 3. Call-sites e funções orfas removidos do update_docs
grep -n 'update_gambiarras\|update_sprint_template' scripts/update_docs.py     # esperado VAZIO (exit 1)

# 4. cli_lines / _count_cli_lines PRESERVADOS (não foram vitima de cascata)
grep -n 'cli_lines\|_count_cli_lines' scripts/update_docs.py                   # esperado 2+ hits

# 5. update_docs deixou de tocar nos dois docs
python3 scripts/update_docs.py
git status --short dev-journey/08-templates/GAMBIARRAS_POR_SPRINT.md \
                   dev-journey/08-templates/SPRINT_TEMPLATE_V2.md              # esperado VAZIO

# 6. Reproducao do fix: WIP manual do dono NÃO e força-staged
printf '\n<!-- WIP manual simulado do dono -->\n' >> dev-journey/08-templates/GAMBIARRAS_POR_SPRINT.md
# rodar o laco pos-fix (copiar da seção 7 do hook ja editado) e checar o indice:
git diff --cached --name-only | grep -c GAMBIARRAS                            # esperado 0
git checkout -- dev-journey/08-templates/GAMBIARRAS_POR_SPRINT.md            # limpa a simulacao

# 7. Lint e acentuacao
/home/andrefarias/.local/bin/ruff check scripts/update_docs.py               # All checks passed
python3 ~/.config/zsh/scripts/validar-acentuacao.py --paths \
    scripts/hooks/pre-commit scripts/update_docs.py \
    dev-journey/06-sprints/producao/SPRINT_INFRA_PRECOMMIT_NO_OWNER_WIP_01.md  # exit 0
```

Comandos que exigem GPU (rodar quando a placa estiver livre -- a validação concorrente ocupa a GPU agora):

```bash
bash scripts/sprint_invariants.sh   # PASS 14/14 FAIL 0 (check #13 smoke usa proxy/ollama)
./run.sh --smoke                    # boot ok, exit 0
```

Runtime real do próprio hook (auto-teste do commit desta sprint): ao commitar as duas edicoes, o pre-commit da seção 7 deve rodar, mostrar `[OK] Docs auto-atualizados e re-staged`, e `git show --stat` do commit resultante NÃO deve listar `GAMBIARRAS_POR_SPRINT.md` nem `SPRINT_TEMPLATE_V2.md` -- prova viva de que o vetor foi cortado.

---

## Criterio binario de aceite

- [ ] hook não força-stageia SPRINT_TEMPLATE_V2.md nem GAMBIARRAS_POR_SPRINT.md
- [ ] WIP manual simulado nos dois docs não entra no indice quando a seção 7 roda
- [ ] update_docs.py não escreve mais nesses dois docs; funções orfas removidas
- [ ] cli_lines e _count_cli_lines preservados (print de diagnostico intacto)
- [ ] os 5 docs auto-derivaveis seguem sincronizados e force-staged
- [ ] bash -n do hook OK; ruff limpo; acentuacao exit 0
- [ ] invariantes 14/14 e smoke boot ok (quando GPU livre)
- [ ] spec -> concluidos/

---

## Invariantes a preservar

- Secao 7 do hook continua sincronizando e force-stageando os 5 docs plenamente auto-derivaveis (GUIDE, README, PORT_STATUS, ARCHITECTURE, PROJECT_SNAPSHOT) -- não regredir o auto-sync legitimo.
- `update_docs.py --check` continua funcional como gate do hook para os docs restantes.
- Nenhum debito implicito (memoria `feedback_nenhum_debito.md`): achado colateral vira sprint nova com ID no SPRINT_ORDER_MASTER.
- Working tree limpo (memoria WORKTREE-BASELINES-01): o reforço da Opção A existe justamente para não trocar "WIP arrastado" por "doc sujo-unstaged permanente".
- Acentuacao PT-BR correta em todo arquivo tocado (check #4; validador `~/.config/zsh/scripts/validar-acentuacao.py --paths`).

---

## Riscos

| Risco | Mitigacao |
|-------|-----------|
| O numero-exemplo em GAMBIARRAS/TEMPLATE passa a ser mantido a mao e pode envelhecer | Sao exemplos pedagogicos/referencia, não contratos de runtime; ironicamente o exemplo do GAMBIARRAS e literalmente sobre "não copiar numero sem verificar", entao uma leve defasagem ali e inofensiva (ate coerente) |
| Remover doc errado do laco força-stage do hook | Alterar SO as duas linhas de continuacao nomeadas (SPRINT_TEMPLATE_V2 e GAMBIARRAS); os outros 5 docs permanecem; validar com `bash -n` e com o grep do proof-of-work |
| Cascata de F841 ao mexer no update_docs | NÃO tocar `cli_lines`/`_count_cli_lines` (seguem usados pelo print de diagnostico); remover so os 2 call-sites e as 2 funções orfas nomeadas |

---

## Anti-debito (candidato a follow-up, NÃO desta sprint)

`PROJECT_SNAPSHOT.md` tambem e force-staged pela seção 7 e a docstring de `update_project_snapshot` afirma preservar partes narrativas tocando so celulas de tabela -- ou seja, tem componente manual. O achado 408 nomeia apenas os dois docs, entao PROJECT_SNAPSHOT fica fora de escopo. Se o dono comprovar que WIP manual em PROJECT_SNAPSHOT tambem vaza para commits de executor, abrir `INFRA-PRECOMMIT-SNAPSHOT-NO-DRAG-01` (ONDA-48/higiene) para dar-lhe o mesmo tratamento.

---

## Referencias

- BRIEF: `/home/andrefarias/Desenvolvimento/Nyx-Code/VALIDATOR_BRIEF.md`
- Entrada na tabela: `dev-journey/06-sprints/SPRINT_ORDER_MASTER.md` linha 408 (bloco MANUAL_OVERRIDE_ONDA_48)
- Precedente de higiene de working tree: `SPRINT_WORKTREE_BASELINES_01.md` (concluidos/)
- Alvos: `scripts/hooks/pre-commit` (seção 7, linhas 265-286) e `scripts/update_docs.py` (main + funções update_gambiarras/update_sprint_template)

---

*"Force-stage de arquivo majoritariamente-manual e assinar em nome do dono. O commit do executor so deve carregar o que o executor de fato mudou."*
