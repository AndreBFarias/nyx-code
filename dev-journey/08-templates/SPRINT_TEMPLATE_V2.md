# SPRINT TEMPLATE V2 — Blindado contra IA descontextualizada

**Versão:** v2.0 (2026-04-18)
**Uso:** cada sprint em `dev-journey/06-sprints/producao/` **deve** seguir este formato.
Uma IA lendo apenas o arquivo da sprint sabe exatamente o que fazer.

---

## 0. SPEC (machine-readable)

```yaml
sprint:
  id: <PREFIXO-NN>
  title: "Título descritivo"
  onda: 22
  prioridade: CRÍTICA | ALTA | MÉDIA | BAIXA
  tipo: Feature | Bugfix | Refactor | Infra | Docs | Audit
  dependencias: [<ID-ANTERIOR>]
  desbloqueia: [<ID-POSTERIOR>]

  touches:
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/caminho/arquivo.py
      reason: "Por que este arquivo é modificado"
      linhas_alvo: "120-165"   # opcional
  creates:
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/caminho/novo.py
      reason: "Propósito do novo arquivo"
  removes: []

  n_to_n_pairs:
    - descricao: "Constante X existe em A e B — atualizar ambos"
      paths: [A, B]

  forbidden:
    - "Adicionar emoji"
    - "Usar 'print()' fora de cli.py"
    - "Menção a Claude/GPT/Anthropic"
    - "Path absoluto hardcoded fora de design_tokens/settings"

  tests:
    - cmd: "./run.sh --gauntlet --only <fase>"
      timeout: 300
      deve_passar: true

  acceptance_criteria:
    - "Critério binário 1 (sim/não, sem ambiguidade)"
    - "Critério binário 2"
    - "Acentuação PT-BR correta em tudo novo"
    - "Zero hex hardcoded fora de design_tokens.py"
    - "Gauntlet passa 100% na fase relevante"
```

---

# Sprint <ID> — Título

**Status:** PENDENTE
**Data criação:** YYYY-MM-DD
**Modelo obrigatório:** claude-opus-4-7 (sem subagentes)

---

## Contexto do projeto (snapshot — não referência)

> **ADRs relevantes (colar o essencial inline, não apontar arquivo):**
>
> - ADR-001 Local First: tudo offline.
> - ADR-004 Zero Emojis: em tudo.
> - ADR-005 Anonimato: sem menção a IA em código/commits.
> - ADR-006 PT-BR: acentuação obrigatória.
> - ADR-010 Zero Mocks: testes contra infra real.
> - ADR-013 Integração Obrigatória: nada solto, tudo no registry.
> - ADR-014 Testes via Gauntlet: sem pytest/unittest, tudo no gauntlet.
> - ADR-020 Testes via run.sh: `./run.sh --gauntlet --only <fase>`.
>
> **Estado do sistema (na data da sprint):**
> - Python 3.10+, modelo `qwen3:4b` no Ollama porta 11435, proxy 11436.
> - 34 tools, 47 commands, 10 services. `cli.py` 722 linhas.
> - Sprint anterior: `<ID-ANTERIOR>` CONCLUIDA.

---

## Problema

Descrição objetiva do que está quebrado ou faltando. Incluir **sintoma observável** (screenshot, mensagem de erro literal, trace).

---

## Solução proposta

Frase curta: o que fazer.

---

## Arquivos alvo (paths absolutos)

### `/home/andrefarias/.../arquivo.py`

**Antes:**
```python
# trecho atual literal
```

**Depois:**
```python
# trecho alvo literal
```

**Mudanças:** bullet list do que mudou.

---

## Diff esperado (resumo)

```
+ 2 arquivos criados
~ 3 arquivos modificados
- 0 arquivos removidos
+ ~120 linhas líquidas
```

---

## Comandos de verificação (literais, copy-paste)

```bash
# 1. Validação estática
python -m ruff check nyx/

# 2. Teste da sprint
./run.sh --gauntlet --only <fase>

# 3. Validação manual (checkpoint visual se aplicável)
./run.sh
# (instruções passo-a-passo)
```

---

## Critério binário de aceite (IA executora)

- [ ] Critério 1 (claro, não ambíguo)
- [ ] Critério 2
- [ ] Gauntlet `--only <fase>` passa 100%
- [ ] `ruff` não reclama
- [ ] Nenhuma violação de `forbidden[]`
- [ ] `CLAUDE.md` + `SPRINT_ORDER_MASTER.md` atualizados marcando CONCLUIDA
- [ ] Sprint movida de `producao/` para `concluidos/`
- [ ] Commit atômico criado com mensagem no padrão `tipo: descrição`

---

## Guardrails anti-engodo (obrigatórios)

A IA executora **NÃO pode marcar sprint como concluída** se:

- Algum critério acima estiver incompleto.
- Tentou burlar teste modificando o teste em vez da implementação.
- "Gauntlet passou" sem output real mostrado ao validador.
- Falhou silenciosamente e assumiu sucesso.
- Ignorou item de `forbidden[]` "porque seria mais fácil".

Se qualquer item falhar, a IA **deve** reportar para o usuário:
```
[SPRINT <ID>] BLOQUEADA: <motivo objetivo em 1 linha>
```

---

## Catálogo de gambiarras proibidas (20 padrões)

Toda sprint é vulnerável a pelo menos um destes. A IA executora que fizer qualquer deles está em **violação grave** e será auditada.

### Burlas estruturais

1. **Rename em vez de delete.** Renomear `compact.py` para `_compact.py`, `compact_old.py`, `_compact_DEPRECATED.py`. **Regra:** quando a sprint pede remoção, o arquivo **deixa de existir** no filesystem.
2. **Stub como implementação.** Criar função que retorna `""`, `None`, `True`, `[]` fixo. **Regra:** função deve produzir output **diferente** para inputs diferentes.
3. **Copy-paste sem adaptação.** Colar código da Luna/openclaud sem ajustar paths/imports. **Regra:** grep por strings típicas da Luna (ex.: `src.core.`) deve retornar 0 no código Nyx.
4. **Documentação como implementação.** Escrever docstring dizendo o que a função "deveria fazer" sem implementar. **Regra:** chamada real deve produzir efeito observável (print, write, HTTP, mutação de estado).
5. **Arquivo único gigante no lugar do split.** Pedir "dividir em 8 módulos", IA cria `commands/everything.py` com 900 linhas. **Regra:** `find ... -exec wc -l ... '$1 > 300' | head` = vazio.

### Burlas de testes

6. **Modificar teste em vez de corrigir código.** Assertion falha → IA troca `assert x == 5` por `assert x >= 0`. **Regra:** comparar diff do teste **antes/depois**; alteração de assert é suspeita e precisa justificativa explícita.
7. **Test só passa com fixture fake.** Pré-popular cache, mock de HTTP, input hardcoded do que deveria ser dinâmico. **Regra:** teste precisa rodar contra **infra real** (ADR-010 Zero Mocks).
8. **Grep que não detecta o bug.** `grep "success" output.log` passa mesmo com falha real. **Regra:** verificação precisa **fail** quando o código não funciona, **pass** quando funciona. Escrever ambos os casos: o caminho positivo e o negativo.
9. **Condicional de skip.** `if os.environ.get("CI"): return True`. **Regra:** proibido adicionar `SKIP_*` env vars novos sem ADR explícita.
10. **Benchmark sem cronômetro.** Medir performance com `print("rápido")` sem `time.monotonic()`. **Regra:** número em ms/s real no output da verificação.

### Burlas de linter / type check

11. **`# noqa` indiscriminado.** Adicionar `# noqa` ou `# type: ignore` em vez de corrigir. **Regra:** cada `noqa` precisa especificar regra (`# noqa: E402`) e motivo em comentário adjacente.
12. **Remover arquivo que a regra checa.** Deletar `commands.py` para passar `grep "print(" commands.py`. **Regra:** verificação global (grep no repo inteiro), não no arquivo tocado.
13. **Desabilitar regra no pyproject.** Editar `select = [...]` removendo a letra que reclama. **Regra:** mudança em `pyproject.toml` só com ADR.

### Burlas de git / commit

14. **Commit message mentindo.** "feat: implementa X" mas só adicionou TODO. **Regra:** `git show --stat` precisa ter linhas líquidas compatíveis com o escopo (mínimo ~20 linhas novas para feature, ~5 para fix trivial).
15. **Amend para esconder retrabalho.** Sprint "concluída" em 3 commits viram 1 via amend. **Regra:** commits atômicos preservados; se amend acontecer, justificar.
16. **Squash que apaga reverts.** Esconder que algo foi revertido e reaplicado. **Regra:** nunca `git rebase -i` em histórico público.

### Burlas semânticas

17. **Silent except.** `except Exception: pass`. Já coberto por regra anti-burla global; repetido aqui por frequência. **Regra:** todo `except` precisa de `logger.warning/error` OU `raise`.
18. **Sleep como fix.** `time.sleep(1)` para "resolver" race condition. **Regra:** sprints que envolvem concorrência precisam mostrar que removeram sleeps prévios e não adicionaram novos.
19. **Feature flag falsa.** Esconder código incompleto atrás de `if FEATURE_X: ...` que nunca é True. **Regra:** novos flags precisam de teste que ativa True E False; se só testa False, não está implementado.
20. **Checkpoint marcado sem verificar.** `- [x] critério X` sem rodar o comando de verificação. **Regra:** IA executora **deve colar o output** do comando de verificação junto do checkbox marcado.

---

## Proof-of-work obrigatório (4 passos)

Toda sprint concluída **deve rodar e colar o output** dos 4 passos abaixo. Sem isso, a sprint é considerada **não verificada**, independentemente do que a IA afirma.

```bash
# PASSO 1 — snapshot ANTES de começar
bash scripts/sprint_invariants.sh > /tmp/inv_before.txt 2>&1
FAIL_BEFORE=$(grep -c "^\[FAIL\]" /tmp/inv_before.txt)
echo "FAIL inicial: $FAIL_BEFORE"

# PASSO 2 — implementação (seguindo literalmente este arquivo)
#            + consultar dev-journey/08-templates/GAMBIARRAS_POR_SPRINT.md seção <ID>

# PASSO 3 — snapshot DEPOIS
bash scripts/sprint_invariants.sh > /tmp/inv_after.txt 2>&1
FAIL_AFTER=$(grep -c "^\[FAIL\]" /tmp/inv_after.txt)
echo "FAIL final: $FAIL_AFTER"

# PASSO 4 — regras binárias
#   (a) $FAIL_AFTER <= $FAIL_BEFORE        (nunca pode aumentar)
#   (b) invariantes listados na "matriz sprint × invariantes" do GAMBIARRAS_POR_SPRINT.md
#       precisam cair pelo menos para 0 se esta sprint é responsável por eles
#   (c) diff /tmp/inv_before.txt /tmp/inv_after.txt — colar no relatório
```

**Formato obrigatório do relatório de conclusão:**

```
### Proof-of-work

$ cat /tmp/inv_before.txt | tail -10
(saída bruta)

$ cat /tmp/inv_after.txt | tail -10
(saída bruta)

$ diff /tmp/inv_before.txt /tmp/inv_after.txt
(diff)

FAIL inicial: N
FAIL final:   M  (M <= N)
Invariantes fechados por esta sprint: [#X, #Y]   (se houver)

### Comando específico da sprint
$ <comando da seção "Comando de verificação">
<output real, não editado>

### Git
$ git show --stat HEAD
<resultado>
```

**Se o output acima não for colado integralmente: sprint é rejeitada.**

Se `FAIL_AFTER > FAIL_BEFORE`: a IA **introduziu regressão**. Sprint deve ser revertida (`git reset --hard HEAD~1`) e reiniciada após correção.

---

## Gambiarras específicas desta sprint

Ver `dev-journey/08-templates/GAMBIARRAS_POR_SPRINT.md` seção `<ID>` para:
- Bypass-paths típicos do escopo desta sprint.
- Comandos de detecção específicos.
- Invariantes que esta sprint fecha (matriz).

**Antes de começar a implementar**, a IA executora deve ler essa seção e explicitar, em um comentário no relatório final, quais gambiarras considerou e como se protegeu delas.

---

## Validação humana (checklist do usuário)

Passos para o usuário confirmar que a sprint foi realmente feita — **sem abrir código**:

```bash
cd /home/andrefarias/Desenvolvimento/Nyx-Code

# 1. Ver diff do commit dessa sprint
git log --oneline -1
git show --stat HEAD

# 2. Rodar comando de verificação
<comando específico da sprint>
# saída esperada: <o que deve aparecer>

# 3. Validar arquivos movidos
ls dev-journey/06-sprints/concluidos/SPRINT_<ID>.md   # deve existir
ls dev-journey/06-sprints/producao/SPRINT_<ID>.md     # NÃO deve existir
```

Se qualquer passo divergir do esperado, a sprint **não está concluída**, mesmo que a IA afirme.

---

## Riscos

| Risco | Mitigação |
|-------|-----------|
| ... | ... |

---

*"Citação de filósofo em PT-BR." -- Autor*
