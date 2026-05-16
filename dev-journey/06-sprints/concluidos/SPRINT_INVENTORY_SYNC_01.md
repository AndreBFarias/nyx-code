# SPRINT INVENTORY-SYNC-01 — Sincronização N-para-N das contagens de tools/commands/services

## 0. SPEC (machine-readable)

```yaml
sprint:
  id: INVENTORY-SYNC-01
  title: "Normalizar contagens reais de tools/commands/services em GUIDE.md, PROJECT_SNAPSHOT.md e SPRINT_ORDER_MASTER.md"
  onda: 22
  bloco: 2.10 Higiene
  prioridade: MÉDIA
  tipo: Docs + Bugfix
  dependencias: [PRODUCAO-CLEANUP-01]
  desbloqueia: []

  touches:
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/GUIDE.md
      reason: "Tabela 'Estado atual' afirma 34 tools, 47 commands, 10 services. Contagem real é diferente — viola meta-regra #1 (sincronização N-para-N)."
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/dev-journey/08-templates/PROJECT_SNAPSHOT.md
      reason: "Seção 'Contagens (verificadas em 2026-04-21, pós UX-BUG-01)' afirma 30 tools, 54 commands, 9 services — parcialmente correto (services ok; tools inflada; commands infla aliases)."
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/dev-journey/06-sprints/SPRINT_ORDER_MASTER.md
      reason: "Seção 'Inventário: Nyx Python (pós-limpeza PROD 2026-04-09)' congelou contagens 34/47/10."
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/scripts/sync.py
      reason: "Se o script atual não imprime contagens canônicas (tools/commands/services), adicionar essa saída para virar fonte única de verdade executável."
  creates: []
  removes: []

  n_to_n_pairs:
    - descricao: "Contagens de inventário vivem em 3+ documentos mais o script sync.py. O comando canônico e o número devem concordar em todos."
      paths:
        - /home/andrefarias/Desenvolvimento/Nyx-Code/GUIDE.md
        - /home/andrefarias/Desenvolvimento/Nyx-Code/dev-journey/08-templates/PROJECT_SNAPSHOT.md
        - /home/andrefarias/Desenvolvimento/Nyx-Code/dev-journey/06-sprints/SPRINT_ORDER_MASTER.md
        - /home/andrefarias/Desenvolvimento/Nyx-Code/scripts/sync.py

  forbidden:
    - "Chutar número — TODO valor na doc tem que vir de um comando bash literal que produza aquele número hoje"
    - "Contar aliases como comandos distintos sem declarar o critério (ex: '47 comandos únicos, 54 ocorrências com aliases')"
    - "Adicionar emoji, menção a IA"
    - "Tocar código em nyx/ (sprint é exclusivamente docs + script utilitário)"
    - "Deixar divergência 'aceitável por desatualização' — o ponto da sprint é justamente zerar divergência"

  tests:
    - cmd: "python scripts/sync.py"
      timeout: 30
      deve_passar: "retorna exit 0 e imprime linha 'inventario: tools=<N>, commands_unicos=<M> (<K> com aliases), services=<S>' sem divergência"
    - cmd: "bash scripts/sprint_invariants.sh"
      timeout: 60
      deve_passar: "13/13 PASS"
    - cmd: "grep -E 'Tools.*Commands.*Services|tools.*commands.*services' GUIDE.md dev-journey/08-templates/PROJECT_SNAPSHOT.md dev-journey/06-sprints/SPRINT_ORDER_MASTER.md"
      timeout: 5
      deve_passar: "os 3 arquivos exibem o MESMO trio (N,M,S)"

  acceptance_criteria:
    - "Comando canônico documentado e executável para cada contagem"
    - "Tools = número de arquivos .py em nyx/agent/tools/ excluindo __init__.py, base.py e registry.py"
    - "Commands = (a) contagem de decorators @nyx_command únicos (dedup por name); (b) contagem total incluindo aliases — ambos reportados explicitamente"
    - "Services = arquivos .py em nyx/agent/services/ excluindo __init__.py"
    - "GUIDE.md Estado atual refletindo os números reais + data"
    - "PROJECT_SNAPSHOT.md seção Contagens com comando literal ao lado de cada número"
    - "SPRINT_ORDER_MASTER.md Inventário atualizado (ou marca a seção como DEPRECATED, apontando PROJECT_SNAPSHOT como fonte única)"
    - "scripts/sync.py imprime as contagens em formato parseável"
    - "Se algum dos 3 docs divergir do script: exit code != 0"
```

---

**Status:** CONCLUIDA (2026-04-21)
**Data criação:** 2026-04-21
**Modelo obrigatório:** claude-opus-4-7 (sem subagentes)

---

## Contexto do projeto (snapshot — não referência)

> **ADRs relevantes:**
>
> - ADR-013 Integração Obrigatória: contagens devem refletir o estado do registry (qualquer divergência = bug).
> - ADR-015 Documentação para continuidade: uma IA nova lendo GUIDE.md não pode encontrar número conflitante em PROJECT_SNAPSHOT.
> - Meta-regra #1 (GUIDE.md global §9): "Sincronização N-para-N — se um valor existe em N lugares, atualizar TODOS ou nenhum."
>
> **Estado real verificado em 2026-04-21 (auditoria desta sessão):**
>
> ```
> $ find nyx/agent/tools -maxdepth 1 -name '*.py' \
>     ! -name '__init__.py' ! -name 'base.py' ! -name 'registry.py' | wc -l
> 28
>
> $ grep -rn '@nyx_command' nyx/agent/commands/ --include='*.py' | wc -l
> 47    # decorators únicos (nomes de comando sem aliases)
>
> $ find nyx/agent/services -maxdepth 1 -name '*.py' ! -name '__init__.py' | wc -l
> 9
> ```
>
> **Divergência atual:**
>
> | Fonte | Tools | Commands | Services |
> |---|---|---|---|
> | Realidade | 28 | 47 únicos | 9 |
> | `PROJECT_SNAPSHOT.md:30-32` | 30 | 54 | 9 |
> | `GUIDE.md` projeto + `SPRINT_ORDER_MASTER.md:32-34` | 34 | 47 | 10 |

---

## Problema

Três documentos de onboarding afirmam três contagens diferentes de tools/commands/services. Uma IA executora lendo `EXECUTAR_SPRINT.md` + `GUIDE.md` chega a uma conclusão; lendo `PROJECT_SNAPSHOT.md` chega a outra; rodando o script real, a uma terceira. Esta divergência:

1. **Viola a meta-regra #1** do protocolo universal (GUIDE.md global).
2. **Engana o validador** — se o validador precisa confirmar "todos os 34 tools estão no registry", ele pode reprovar uma sprint legítima ou aprovar um estado quebrado.
3. **Invalida critérios de aceite históricos** — sprints passadas diziam "testes vão de 135 para 202" mas se a base está errada, a projeção está errada.
4. **Documento `PROJECT_SNAPSHOT.md` (auto-gerado pela DOC-CONSOLIDATE-01)** deveria ser fonte única — mas hoje conta aliases como commands distintos.

---

## Solução proposta

1. **Definir comandos canônicos** (copy-paste-ready) para cada contagem.
2. **Executar** e registrar números exatos na data da sprint.
3. **Atualizar** 3 documentos com tabela unificada + linha "comando de verificação" ao lado.
4. **Hardenizar** `scripts/sync.py` para imprimir o trio em formato parseável e falhar se qualquer dos 3 docs divergir.
5. **Declarar** explicitamente: `PROJECT_SNAPSHOT.md` é a fonte-mãe; GUIDE.md e SPRINT_ORDER_MASTER apontam para ele ("ver PROJECT_SNAPSHOT para contagens atuais") ao invés de duplicar.

---

## Arquivos alvo (paths absolutos)

### `/home/andrefarias/Desenvolvimento/Nyx-Code/scripts/sync.py`

**Antes (conceitual — ler o arquivo real):** verifica consistência N-para-N mas pode não emitir o trio canônico.

**Depois:** adicionar/garantir a função `print_inventory()` que emite:
```
inventario: tools=28, commands_unicos=47, services=9
```
e compara com os números congelados em cada doc (via regex), falhando se divergir.

### `/home/andrefarias/Desenvolvimento/Nyx-Code/dev-journey/08-templates/PROJECT_SNAPSHOT.md`

**Antes (linhas 28-36 aprox.):**
```markdown
| Categoria | Quantidade | Como verificar |
|----------|------------|----------------|
| Tools no registry | 30 | `find nyx/agent/tools -maxdepth 1 -name "*.py" ! -name "__init__.py" \| wc -l` |
| Commands (slash) | 54 | `grep -rn "@nyx_command" nyx/agent/commands/ \| wc -l` |
| Services | 9 | `find nyx/agent/services -maxdepth 1 -name "*.py" ! -name "__init__.py" \| wc -l` |
```

**Depois:**
```markdown
| Categoria | Quantidade | Como verificar |
|----------|------------|----------------|
| Tools no registry | 28 | `find nyx/agent/tools -maxdepth 1 -name '*.py' ! -name '__init__.py' ! -name 'base.py' ! -name 'registry.py' \| wc -l` |
| Commands (únicos, sem aliases) | 47 | `grep -rhE "@nyx_command\(name=" nyx/agent/commands/ \| wc -l` |
| Services | 9 | `find nyx/agent/services -maxdepth 1 -name '*.py' ! -name '__init__.py' \| wc -l` |
| ADRs vigentes | 24 | `ls dev-journey/03-decisions/ADR_*.md \| wc -l` |
| Sprints concluídas | 137 | `ls dev-journey/06-sprints/concluidos/*.md \| wc -l` (inclui 4 absorvidas movidas por PRODUCAO-CLEANUP-01) |
| Sprints pendentes | 18 | `ls dev-journey/06-sprints/producao/*.md \| wc -l` (17 PENDENTE + CTX-04 DEFERIDA) |
```

**Mudanças:**
- Comandos `find` excluem corretamente `base.py` e `registry.py` dos tools (são infra, não tool).
- Commands usa `grep -rhE "@nyx_command\(name="` para contar decorators por linha de definição — sem contar aliases, que moram em parâmetro do decorator.
- Contagens atualizadas para refletir pós-PRODUCAO-CLEANUP-01 (137 concluídas / 18 pendentes).

### `/home/andrefarias/Desenvolvimento/Nyx-Code/GUIDE.md` (projeto)

**Antes (seção "Estado atual"):**
```markdown
| Componente | Atual | Nota |
|-----------|-------|------|
| Tools | 34 | Todas funcionais |
| Commands | 47 | Todos funcionais (27 stubs cloud removidos) |
| Services | 10 | Todos funcionais (11 stubs cloud removidos) |
| ADRs | 24 | ADR-022 (moondream), ADR-023 (design system), ADR-024 (render layer) adicionados na Onda 22 |
```

**Depois:**
```markdown
> **Contagens:** ver `dev-journey/08-templates/PROJECT_SNAPSHOT.md` §Contagens (auto-gerado pelo DOC-CONSOLIDATE-01). Este GUIDE.md não duplica números para evitar divergência. Estado em 2026-04-21: 28 tools · 47 commands · 9 services · 24 ADRs.
```

**Mudanças:**
- Elimina duplicação — aponta para fonte única.
- Mantém resumo de uma linha para conveniência, mas com data explícita.

### `/home/andrefarias/Desenvolvimento/Nyx-Code/dev-journey/06-sprints/SPRINT_ORDER_MASTER.md`

**Antes (linhas 28-38):**
```markdown
## Inventário: Nyx Python (pós-limpeza PROD 2026-04-09)

| Componente | Nyx (atual) | Nota |
|-----------|------------|------|
| Tools | 34 | Todas funcionais |
| Commands | 47 | Todos funcionais (27 stubs cloud removidos) |
| Services | 10 | Todos funcionais (11 stubs cloud removidos) |
| Testes | 135 | Gauntlet atualizado para testar funcionalidade real |
```

**Depois:**
```markdown
## Inventário

> **Fonte única:** `dev-journey/08-templates/PROJECT_SNAPSHOT.md` §Contagens. Atualizado automaticamente. Em 2026-04-21: 28 tools · 47 commands únicos · 9 services · 135+ testes no Gauntlet.
> Mantemos aqui só a nota histórica: em 2026-04-09 a limpeza PROD removeu 27 command-stubs cloud e 11 service-stubs cloud; port 1:1 do OpenClaude abandonado, foco local-first.
```

**Mudanças:**
- Deixa de congelar contagens.
- Preserva nota histórica da decisão.

---

## Diff esperado (resumo)

```
+ 0 arquivos criados
~ 4 arquivos modificados (GUIDE.md, PROJECT_SNAPSHOT.md, SPRINT_ORDER_MASTER.md, scripts/sync.py)
- 0 arquivos removidos
+ ~40 linhas líquidas (docs) / ~30 linhas em sync.py
```

---

## Comandos de verificação (literais, copy-paste)

```bash
cd /home/andrefarias/Desenvolvimento/Nyx-Code

# 1. Contagem canônica (cole na atualização)
TOOLS=$(find nyx/agent/tools -maxdepth 1 -name '*.py' ! -name '__init__.py' ! -name 'base.py' ! -name 'registry.py' | wc -l)
CMDS=$(grep -rhE '@nyx_command\(name=' nyx/agent/commands/ | wc -l)
SRVS=$(find nyx/agent/services -maxdepth 1 -name '*.py' ! -name '__init__.py' | wc -l)
ADRS=$(ls dev-journey/03-decisions/ADR_*.md 2>/dev/null | wc -l)
CONCLUIDAS=$(ls dev-journey/06-sprints/concluidos/*.md 2>/dev/null | wc -l)
PENDENTES=$(ls dev-journey/06-sprints/producao/*.md 2>/dev/null | wc -l)
echo "tools=$TOOLS commands=$CMDS services=$SRVS adrs=$ADRS concluidas=$CONCLUIDAS pendentes=$PENDENTES"

# 2. Conferir que os 3 docs concordam (após edits)
grep -E '28 tools|47 commands|9 services' \
    GUIDE.md \
    dev-journey/08-templates/PROJECT_SNAPSHOT.md \
    dev-journey/06-sprints/SPRINT_ORDER_MASTER.md

# 3. Rodar sync
python scripts/sync.py

# 4. Regressão de invariantes
bash scripts/sprint_invariants.sh | tail -5
```

---

## Critério binário de aceite (IA executora)

- [ ] Comandos do passo 1 executados AO VIVO — colar output no relatório
- [ ] Os 3 documentos mostram exatamente o mesmo trio (28/47/9)
- [ ] `PROJECT_SNAPSHOT.md` mostra comando literal ao lado de cada contagem
- [ ] `GUIDE.md` e `SPRINT_ORDER_MASTER.md` apontam para `PROJECT_SNAPSHOT.md` ao invés de duplicar números
- [ ] `scripts/sync.py` imprime `inventario: tools=N, commands_unicos=M, services=S` em uma única linha
- [ ] Se algum doc divergir do script: exit code != 0 (teste artificial aceito)
- [ ] `sprint_invariants.sh` 13/13 (FAIL_AFTER <= FAIL_BEFORE)
- [ ] Nenhuma mudança em `nyx/` (sprint é docs + script utilitário)
- [ ] Commit atômico `docs(INVENTORY-SYNC-01): normaliza contagens tools/commands/services`

---

## Guardrails anti-engodo (obrigatórios)

- Nenhuma contagem pode vir de memória — todo número tem comando bash que o produz.
- Se `grep '@nyx_command'` retornar 47 mas o usuário lembra de 54: reportar a divergência, **não ajustar a lembrança**.
- Se `scripts/sync.py` já existir com estrutura diferente do proposto: preservar API pública, apenas adicionar `print_inventory()`.
- Não apagar a tabela inteira de GUIDE.md e SPRINT_ORDER_MASTER — reduzir a resumo de uma linha com data.

---

## Catálogo de gambiarras proibidas

Ver `dev-journey/08-templates/GAMBIARRAS_POR_SPRINT.md` §"Catálogo Universal".

### Gambiarras específicas

1. **"Aproximar" o número sem comando.** `~28` ou `aproximadamente 47` proibido. É exatamente o que gerou a divergência atual.
2. **Copiar valor do PROJECT_SNAPSHOT sem reexecutar o `find`.** PROJECT_SNAPSHOT está errado hoje — precisa ser corrigido ANTES de virar fonte única.
3. **Reinterpretar "commands = 54" como correto porque inclui aliases.** Se a intenção era contar aliases, o rótulo deve ser "commands registrados incluindo aliases". Esclarecer semanticamente; não sobrecarregar o mesmo número.
4. **Omitir data.** Toda linha de contagem tem data explícita — inventário de hoje não é verdade eterna.
5. **Mexer em commands/__init__.py para "regularizar" o count.** Escopo proibido — essa sprint só toca docs/script.

---

## Proof-of-work obrigatório (4 passos)

```bash
bash scripts/sprint_invariants.sh > /tmp/inv_before.txt 2>&1
FAIL_BEFORE=$(grep -c '^\[FAIL\]' /tmp/inv_before.txt)

# --- implementação: edits + python scripts/sync.py para conferir ---

bash scripts/sprint_invariants.sh > /tmp/inv_after.txt 2>&1
FAIL_AFTER=$(grep -c '^\[FAIL\]' /tmp/inv_after.txt)
diff /tmp/inv_before.txt /tmp/inv_after.txt
[ "$FAIL_AFTER" -le "$FAIL_BEFORE" ] || { echo REGRESSÃO; exit 1; }
```

Colar output de `python scripts/sync.py` + output do `grep` cross-doc.

---

## Validação humana (checklist do usuário)

```bash
cd /home/andrefarias/Desenvolvimento/Nyx-Code

git log --oneline -1
git show --stat HEAD

python scripts/sync.py
# esperado: linha única "inventario: tools=28, commands_unicos=47, services=9"

grep -HE 'tools=28|28 tools|28 · 47|47 commands|9 services' \
    GUIDE.md \
    dev-journey/08-templates/PROJECT_SNAPSHOT.md \
    dev-journey/06-sprints/SPRINT_ORDER_MASTER.md
# esperado: pelo menos 1 match em cada arquivo
```

---

## Riscos

| Risco | Mitigação |
|-------|-----------|
| PRODUCAO-CLEANUP-01 não foi executada antes — contagem de sprints pode estar errada | Sprint declara dependência; executor deve confirmar que SPRINT_UX_BUG_02.md etc. já estão em concluidos/ |
| `scripts/sync.py` hoje faz validações diferentes e acoplamento quebra | Abrir o arquivo antes; preservar funções existentes; adicionar `print_inventory()` como aditivo |
| Algum comando `@nyx_command` usa sintaxe multilinha (aparece em 2 linhas) e grep conta a metade | Teste cruzado: contar via `python -c "from nyx.agent.commands._registry import list_commands; print(len(list_commands()))"` e confrontar com o grep |
| Surge descoberta de tool/service extra durante a contagem | Registrar no relatório; se o número ficar > 28/9, ajustar os 3 docs consistentemente (nunca divergente) |

---

*"Contar é o primeiro ato da honestidade intelectual." -- Simone Weil (adaptado)*
