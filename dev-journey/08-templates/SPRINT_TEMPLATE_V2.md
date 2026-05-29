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
    - descricao: "Constante X existe em A e B — atualizar ambos"  # noqa-acento
      paths: [A, B]

  forbidden:
    - "Adicionar emoji"
    - "Usar 'print()' fora de cli.py"
    - "Menção a Claude/GPT/Anthropic" <!-- noqa-anonimato -->
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

## Bloco de metadata (OBRIGATÓRIO)

O `scripts/update_next_sprint.py` extrai o `Status` da sprint a partir
deste bloco. Sem ele, o script retorna `SEM_METADATA`, emite warning
com hint e a sprint não entra na fila de execução.

Regras:
- `**Status:**` em linha própria, não dentro de bloco de código nem
  dentro de seção de ADR embedded (`# ADR-xxx ...`). O script mascara
  essas duas regiões antes da busca; metadata em linha solta sobrevive.
- Posicionar **imediatamente** após o `---` que fecha o `## 0. SPEC`.
  Pode vir antes ou depois do heading `# Sprint <ID>`; ambos os
  padrões são aceitos (preferir antes nas sprints novas).
- Valores aceitos de `Status`:
  - `PENDENTE` — único que entra na fila.
  - `CONCLUIDA` — terminal de sucesso.
  - `ABSORVIDA_POR_<OUTRA-ID>` — escopo foi absorvido por outra sprint.
  - `DEFERIDA` — reagendada fora da janela atual.
  - `OPCIONAL` — feature opt-in sem deadline.

Forma canônica literal (copiar-colar):

```
---

# Sprint <ID> — Título

**Status:** PENDENTE
**Data criação:** YYYY-MM-DD
**Modelo obrigatório:** claude-opus-4-7 (sem subagentes)

---
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
> - Python 3.10+, modelo `qwen2.5-coder:3b` no Ollama porta 11435, proxy 11436 (ADR-031).
> - 35 tools, 67 commands, 15 services. `cli.py` ~670 linhas.
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

### Antes/Depois com trecho (obrigatório para Refactor cirúrgico)

Para sprints `tipo: Refactor` com `touches.length == 1` e alvo do tipo literal/padrão/substring,
a spec **deve** incluir fenced code block (>= 3 linhas) com o trecho EXATO além do número de linha.

**Justificativa empírica:** INFRA-GAUNTLET-CLEANUP-BUNDLE-01 (2026-05-21) teve 2 de 3 fixes com
número de linha errado na spec (citava 859/861 e 700-701; reais eram 968/970 e 809-811).
Resolveu via texto-alvo inequívoco, mas só porque o planejador teve presença de mente de citar
padrão `"qwen" in content` e frase `"Processos externos ocupando VRAM"`. Sem trecho literal,
o executor teria editado linhas vizinhas erradas e a sprint teria virado regressão silenciosa.

**Formato sugerido:**

````markdown
# Localização aproximada: linha NNN (drift tolerado se trecho casa)
# Antes:
```python
<TRECHO LITERAL DO CÓDIGO ATUAL, >= 3 linhas, com pelo menos 1 token de ancoragem único>
```

# Depois:
```python
<TRECHO ESPERADO POS-FIX, >= 3 linhas>
```
````

Esse formato deixa o executor seguro mesmo quando linhas sofrem drift por edits intermediários
entre o momento da redação da spec e o momento da execução. O número de linha vira pista; o
trecho literal vira contrato.

**Exceções:** sprints `tipo: Feature` em arquivo novo, `tipo: Docs` puro, ou refactor onde
`touches.length >= 2` (drift mútuo torna trecho literal frágil — preferir descrição semântica).

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

# 3. Acentuação PT-BR (BRIEF §[CORE] Sintaxe correta de utilitários externos)
#    Flag --paths é OBRIGATÓRIA — argumentos posicionais são rejeitados.
python3 ~/.config/zsh/scripts/validar-acentuacao.py --paths <arquivo1> <arquivo2>

# 4. Validação manual (checkpoint visual se aplicável)
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
- [ ] `GUIDE.md` + `SPRINT_ORDER_MASTER.md` atualizados marcando CONCLUIDA
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

## Catálogo de gambiarras proibidas

O catálogo universal de 20 padrões (estruturais, testes, linter, git, semânticas) foi consolidado em `dev-journey/08-templates/GAMBIARRAS_POR_SPRINT.md` §"Catálogo Universal". **Ler antes de implementar.**

Gambiarras específicas desta sprint ficam em §"Gambiarras específicas desta sprint" abaixo.

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
