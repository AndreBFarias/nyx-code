# SPRINT DOC-CONSOLIDATE-01 — Reduzir carga cognitiva de leitura por sprint de ~1000 para ~400 linhas

## 0. SPEC (machine-readable)

```yaml
sprint:
  id: DOC-CONSOLIDATE-01
  title: "Consolidar documentação de protocolo: fundir catálogos duplicados, linkar em vez de duplicar, auto-injetar snapshot no EXECUTAR_SPRINT"
  onda: 22
  bloco: 2.9
  prioridade: MÉDIA
  tipo: Docs
  dependencias: []
  desbloqueia: [todas as sprints seguintes — reduz tempo de leitura obrigatória]

  touches:
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/dev-journey/08-templates/SPRINT_TEMPLATE_V2.md
      reason: "Remover seção duplicada 'Catálogo de 20 gambiarras' e substituir por link para GAMBIARRAS_POR_SPRINT.md"
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/dev-journey/08-templates/GAMBIARRAS_POR_SPRINT.md
      reason: "Receber seção nova 'Catálogo Universal de Gambiarras (20 padrões)' migrada do TEMPLATE_V2"
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/GUIDE.md
      reason: "Substituir seção Anti-burla por link para GAMBIARRAS_POR_SPRINT.md; substituir 'próxima sprint' por link para GSD.md"
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/scripts/update_next_sprint.py
      reason: "Injetar trecho da seção GAMBIARRAS do sprint atual dentro do EXECUTAR_SPRINT.md (recorte inline por ID)"
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/scripts/sprint_invariants.sh
      reason: "Corrigir header: linha 4 diz '12 checks' mas são 13"
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/GSD.md
      reason: "Padronizar seção 'Fluxo completo de uma sprint' com 10 passos canônicos; GUIDE.md passa a linkar pra cá"

  creates:
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/dev-journey/08-templates/PROJECT_SNAPSHOT.md
      reason: "Snapshot auto-gerável do projeto (portas, versão, contagens de tools/commands/services, ADRs, sprints concluídas) — referenciado por TEMPLATE_V2 em vez de cópia inline"

  removes: []

  n_to_n_pairs:
    - descricao: "Catálogo de 20 gambiarras aparece hoje em TEMPLATE_V2.md e é referenciado em GUIDE.md/GAMBIARRAS; migrar para fonte única em GAMBIARRAS_POR_SPRINT.md e linkar nos outros"
      paths:
        - /home/andrefarias/Desenvolvimento/Nyx-Code/dev-journey/08-templates/SPRINT_TEMPLATE_V2.md
        - /home/andrefarias/Desenvolvimento/Nyx-Code/dev-journey/08-templates/GAMBIARRAS_POR_SPRINT.md
        - /home/andrefarias/Desenvolvimento/Nyx-Code/GUIDE.md
    - descricao: "Fluxo de 10 passos (próxima sprint) aparece em GUIDE.md e GSD.md; canonizar em GSD e linkar no GUIDE.md"
      paths:
        - /home/andrefarias/Desenvolvimento/Nyx-Code/GUIDE.md
        - /home/andrefarias/Desenvolvimento/Nyx-Code/GSD.md

  forbidden:
    - "Apagar conteúdo antes de migrar — migração precede remoção, em commits separados se necessário"
    - "Remover seção sem deixar link apontando para o novo local"
    - "PROJECT_SNAPSHOT.md gerado à mão com valores chutados — dados precisam refletir estado real (contagens verificadas)"
    - "update_next_sprint.py ler EXECUTAR_SPRINT.md em vez de regenerar — scripts/update_next_sprint.py é o dono, não consumidor"
    - "Adicionar emoji ou menção a IA"
    - "Path absoluto hardcoded no update_next_sprint.py — usar Path(__file__).parent"

  tests:
    - cmd: "python scripts/update_next_sprint.py"
      timeout: 30
      deve_passar: "EXECUTAR_SPRINT.md regenera sem erro e contém recorte de gambiarras da próxima sprint PENDENTE"
    - cmd: "bash scripts/sprint_invariants.sh"
      timeout: 60
      deve_passar: "header diz '13 checks' (corrigido)"
    - cmd: "wc -l GUIDE.md GSD.md dev-journey/08-templates/SPRINT_TEMPLATE_V2.md"
      timeout: 5
      deve_passar: "soma líquida reduzida (evidência de desduplicação)"

  acceptance_criteria:
    - "GAMBIARRAS_POR_SPRINT.md tem nova seção 'Catálogo Universal de Gambiarras (20 padrões)' com o conteúdo migrado literal"
    - "SPRINT_TEMPLATE_V2.md não tem mais o catálogo inline — só link"
    - "GUIDE.md seção Anti-burla reduzida a link + 2 linhas de contexto"
    - "GUIDE.md seção 'próxima sprint' reduzida a link para GSD.md"
    - "scripts/update_next_sprint.py injeta recorte de gambiarras específicas no EXECUTAR_SPRINT.md"
    - "scripts/sprint_invariants.sh header corrigido de '12 checks' para '13 checks'"
    - "PROJECT_SNAPSHOT.md criado e referenciado por TEMPLATE_V2"
    - "Soma total de linhas dos docs tocados ficou menor do que antes (evidência no relatório)"
    - "IA executora precisa ler <= 400 linhas para pegar contexto de uma sprint típica"
    - "Acentuação PT-BR correta em tudo novo"
```

---

**Status:** CONCLUIDA (header corrigido em MASTER-CLEANUP-02 2026-05-20; presença em concluidos/ implica CONCLUIDA conforme convenção do projeto)
**Data criação:** 2026-04-19
**Modelo obrigatório:** claude-opus-4-7 (sem subagentes)

---

## Contexto do projeto (snapshot — não referência)

> **ADRs relevantes:**
> - ADR-015 Documentação para continuidade.
> - ADR-006 PT-BR.
> - ADR-004 Zero Emojis.
> - ADR-005 Anonimato.
>
> **Estado do sistema na data da sprint:**
> - Python 3.10+, Onda 22 em execução, 24 ADRs vigentes.
> - Documentação espalhada: catálogo de gambiarras está em SPRINT_TEMPLATE_V2.md **e** GAMBIARRAS_POR_SPRINT.md; fluxo de 10 passos está em GUIDE.md **e** GSD.md (ligeiramente diferentes).
> - `scripts/update_next_sprint.py` atualiza `EXECUTAR_SPRINT.md` com o ID da próxima PENDENTE, mas não injeta contexto específico de gambiarras.
> - `scripts/sprint_invariants.sh` tem 13 checks (check #13 `./run.sh --smoke` adicionado em BOOT-FIX-01), mas o header ainda diz "12 checks".
> - IA executora típica hoje precisa ler ~1000 linhas antes de codar: GUIDE.md (250) + SPRINT_TEMPLATE_V2.md (300) + GAMBIARRAS_POR_SPRINT.md (150) + arquivo da sprint (300).

---

## Problema

Duplicação de protocolo aumenta erro humano e tempo de contexto para IA executora:

- Quando o catálogo de 20 gambiarras é atualizado em um dos dois arquivos e não no outro, regras divergem.
- Fluxo de 10 passos está escrito com pequenas variações em GUIDE.md e GSD.md — IA lê o primeiro que encontra.
- Header desatualizado de `sprint_invariants.sh` induz IA a pensar que check #13 é "extra" quando é canônico.
- EXECUTAR_SPRINT.md hoje é um prompt genérico — não traz o recorte de gambiarras específicas daquela sprint, forçando IA a abrir GAMBIARRAS_POR_SPRINT.md e ir caçar a seção do ID.

### Sintoma observável

```bash
$ wc -l GUIDE.md dev-journey/08-templates/SPRINT_TEMPLATE_V2.md dev-journey/08-templates/GAMBIARRAS_POR_SPRINT.md GSD.md
# soma atual > 1000 linhas com redundância significativa

$ grep -n "12 checks" scripts/sprint_invariants.sh
4:# Checks: 12 invariantes...
# mas o script roda 13
```

---

## Solução proposta

Canonização da fonte única por tema, com links em vez de cópias, e enriquecimento automático do EXECUTAR_SPRINT.md.

---

## Arquivos alvo (paths absolutos)

### `/home/andrefarias/Desenvolvimento/Nyx-Code/dev-journey/08-templates/GAMBIARRAS_POR_SPRINT.md`

Adicionar no topo (antes das seções por ID) nova seção:

```markdown
## Catálogo Universal de Gambiarras (20 padrões)

Este catálogo aplica-se a toda sprint. Sprints específicas adicionam gambiarras extras na seção do seu ID abaixo.

### Burlas estruturais

1. Rename em vez de delete. [texto migrado literal de TEMPLATE_V2]
2. Stub como implementação. [...]
3. Copy-paste sem adaptação. [...]
4. Documentação como implementação. [...]
5. Arquivo único gigante no lugar do split. [...]

### Burlas de testes

6. Modificar teste em vez de corrigir código. [...]
7. Test só passa com fixture fake. [...]
8. Grep que não detecta o bug. [...]
9. Condicional de skip. [...]
10. Benchmark sem cronômetro. [...]

### Burlas de linter / type check

11. # noqa indiscriminado. [...]
12. Remover arquivo que a regra checa. [...]
13. Desabilitar regra no pyproject. [...]

### Burlas de git / commit

14. Commit message mentindo. [...]
15. Amend para esconder retrabalho. [...]
16. Squash que apaga reverts. [...]

### Burlas semânticas

17. Silent except. [...]
18. Sleep como fix. [...]
19. Feature flag falsa. [...]
20. Checkpoint marcado sem verificar. [...]
```

Texto migrado deve ser **literal** ao do TEMPLATE_V2 atual (linhas 170-207).

### `/home/andrefarias/Desenvolvimento/Nyx-Code/dev-journey/08-templates/SPRINT_TEMPLATE_V2.md`

Substituir seção "Catálogo de gambiarras proibidas (20 padrões)" por:

```markdown
## Catálogo de gambiarras proibidas

Fonte canônica: `dev-journey/08-templates/GAMBIARRAS_POR_SPRINT.md` seção "Catálogo Universal de Gambiarras (20 padrões)".

Toda sprint é vulnerável a pelo menos um desses 20 padrões. A IA executora deve ler o catálogo universal **e** a seção específica do ID da sprint antes de codar.
```

Substituir seção "Contexto do projeto (snapshot — não referência)" por:

```markdown
## Contexto do projeto (snapshot)

Fonte canônica: `dev-journey/08-templates/PROJECT_SNAPSHOT.md`.

Para cada sprint, colar aqui apenas os ADRs relevantes para o escopo. Não duplicar contagens, portas e versões — elas mudam e ficam obsoletas.
```

### `/home/andrefarias/Desenvolvimento/Nyx-Code/GUIDE.md`

Seção "Anti-burla" (hoje ~20 linhas inline) vira:

```markdown
## Anti-burla

Fonte canônica: `dev-journey/08-templates/GAMBIARRAS_POR_SPRINT.md` seção "Catálogo Universal de Gambiarras".

Resumo das 3 regras mais quebradas:
- Zero `TODO`/`FIXME` inline — criar issue.
- Zero `except` silencioso — sempre `logger.error` ou `raise`.
- Zero código comentado (3+ linhas) — deletar, git guarda.

Detalhes e os 17 padrões restantes no link acima.
```

Seção "próxima sprint" (hoje ~16 linhas inline) vira:

```markdown
### "próxima sprint"

Fonte canônica: `GSD.md` seção "Fluxo completo de uma sprint".

Resumo: ler SPRINT_ORDER_MASTER, identificar próxima PENDENTE, ler arquivo da sprint até o fim, apresentar plano, implementar, proof-of-work em 4 passos, mover para concluidos/, commit atômico.
```

### `/home/andrefarias/Desenvolvimento/Nyx-Code/GSD.md`

Canonizar seção "Fluxo completo de uma sprint" com os **10 passos** canônicos (unificando o que está em GUIDE.md e GSD.md hoje):

```markdown
## Fluxo completo de uma sprint

1. Ler `dev-journey/06-sprints/SPRINT_ORDER_MASTER.md`, identificar 1ª PENDENTE.
2. Ler arquivo da sprint em `dev-journey/06-sprints/producao/SPRINT_*.md` até o fim.
3. Ler `dev-journey/08-templates/GAMBIARRAS_POR_SPRINT.md` seção do ID.
4. PASSO 1 proof-of-work: `bash scripts/sprint_invariants.sh > /tmp/inv_before.txt 2>&1` — anotar FAIL_BEFORE.
5. Apresentar plano, perguntar dúvidas.
6. Implementar seguindo spec (integração obrigatória, ADR-013; testes via Gauntlet, ADR-014).
7. Validar: `./run.sh --gauntlet --only <fase>` + `./run.sh --smoke`.
8. PASSO 3 proof-of-work: `bash scripts/sprint_invariants.sh > /tmp/inv_after.txt 2>&1`.
9. PASSO 4: FAIL_AFTER <= FAIL_BEFORE; invariantes listados na matriz fechados.
10. Atualizar SPRINT_ORDER_MASTER (PENDENTE→CONCLUIDA com hash), `git mv` sprint para concluidos/, rodar `python scripts/update_next_sprint.py`, commit atômico.
```

### `/home/andrefarias/Desenvolvimento/Nyx-Code/scripts/update_next_sprint.py`

Adicionar função que extrai seção do ID atual de `GAMBIARRAS_POR_SPRINT.md` e injeta em `EXECUTAR_SPRINT.md`.

```python
def _extract_gambiarras_section(sprint_id: str, gambiarras_path: Path) -> str:
    content = gambiarras_path.read_text(encoding="utf-8")
    marker_start = f"## {sprint_id}"
    idx = content.find(marker_start)
    if idx == -1:
        return "(seção de gambiarras não encontrada para este ID)"
    rest = content[idx:]
    next_section = rest.find("\n## ", len(marker_start))
    if next_section == -1:
        return rest
    return rest[:next_section]
```

Injetar o retorno dessa função em `EXECUTAR_SPRINT.md` sob um marcador tipo `<!-- GAMBIARRAS_INJECT -->`.

### `/home/andrefarias/Desenvolvimento/Nyx-Code/scripts/sprint_invariants.sh`

Linha 4 (e qualquer outro comentário que diga "12"):

**Antes:**
```bash
# Checks: 12 invariantes binários
```

**Depois:**
```bash
# Checks: 13 invariantes binários (check #13 adicionado em BOOT-FIX-01: ./run.sh --smoke)
```

### `/home/andrefarias/Desenvolvimento/Nyx-Code/dev-journey/08-templates/PROJECT_SNAPSHOT.md`

Novo arquivo:

```markdown
# PROJECT SNAPSHOT

Atualizado em: 2026-04-19
(auto-gerável; rodar `python scripts/update_next_sprint.py` para renovar — enquanto o gerador não existir, editar manualmente por sprint de manutenção)

## Runtime

- Python 3.10+
- Modelo: qwen3:4b
- Ollama: porta 11435
- Proxy: porta 11436

## Contagens

- Tools: 34
- Comandos: 47
- Services: 10
- ADRs vigentes: 24 (001..024, 023 pendente de criação via UX-DESIGN-01)

## Smoke

- `./run.sh --smoke` imprime `boot ok` (check #13 do sprint_invariants)

## Estrutura de diretórios

(tabela com os paths principais)

## Sprints

- Concluídas: ver `dev-journey/06-sprints/concluidos/`
- Pendentes: ver `dev-journey/06-sprints/producao/`
- Ordem canônica: `dev-journey/06-sprints/SPRINT_ORDER_MASTER.md`
```

---

## Diff esperado

```
+ 1 arquivo criado (PROJECT_SNAPSHOT.md)
~ 6 arquivos modificados
- 0 arquivos removidos
Soma de linhas dos docs tocados: REDUZ (medir antes e depois)
```

---

## Comandos de verificação

```bash
# PASSO 1 — snapshot ANTES
bash scripts/sprint_invariants.sh > /tmp/inv_before.txt 2>&1
wc -l GUIDE.md GSD.md dev-journey/08-templates/SPRINT_TEMPLATE_V2.md dev-journey/08-templates/GAMBIARRAS_POR_SPRINT.md > /tmp/lines_before.txt

# PASSO 2 — implementar migrações

# PASSO 3 — verificar gerador
python scripts/update_next_sprint.py
grep -A 5 "GAMBIARRAS_INJECT" EXECUTAR_SPRINT.md    # confirma injeção

# PASSO 4 — verificar header corrigido
head -5 scripts/sprint_invariants.sh | grep "13 checks"

# PASSO 5 — snapshot DEPOIS
bash scripts/sprint_invariants.sh > /tmp/inv_after.txt 2>&1
wc -l GUIDE.md GSD.md dev-journey/08-templates/SPRINT_TEMPLATE_V2.md dev-journey/08-templates/GAMBIARRAS_POR_SPRINT.md dev-journey/08-templates/PROJECT_SNAPSHOT.md > /tmp/lines_after.txt
diff /tmp/lines_before.txt /tmp/lines_after.txt

# PASSO 6 — smoke
./run.sh --smoke
```

---

## Critério binário de aceite

- [ ] GAMBIARRAS_POR_SPRINT.md tem seção "Catálogo Universal de Gambiarras (20 padrões)"
- [ ] SPRINT_TEMPLATE_V2.md não tem catálogo inline — só link
- [ ] GUIDE.md seção Anti-burla tem no máximo 10 linhas (link + 3 regras resumo)
- [ ] GUIDE.md seção "próxima sprint" tem no máximo 5 linhas (link + 1 resumo)
- [ ] GSD.md tem seção "Fluxo completo de uma sprint" com os 10 passos canônicos
- [ ] scripts/update_next_sprint.py injeta recorte em EXECUTAR_SPRINT.md sob marcador
- [ ] scripts/sprint_invariants.sh header diz "13 checks"
- [ ] PROJECT_SNAPSHOT.md criado com runtime, contagens, smoke
- [ ] Soma de linhas dos 4 docs principais menor do que antes
- [ ] FAIL_AFTER <= FAIL_BEFORE no invariants
- [ ] `./run.sh --smoke` continua PASS
- [ ] Commit `docs: consolida catálogos e reduz carga de leitura por sprint`
- [ ] Sprint movida para concluidos/

---

## Guardrails anti-engodo

- Remover seção em um arquivo sem criar link apontando para a nova fonte: violação.
- Migrar texto adaptando (reescrevendo): violação — tem que ser literal para não perder nuance.
- PROJECT_SNAPSHOT.md com contagens chutadas: violação — rodar `ls` nos diretórios e contar.
- update_next_sprint.py com path absoluto hardcoded: violação — `Path(__file__).parent.parent`.
- Esquecer de atualizar a matriz "sprint × invariantes" em GAMBIARRAS_POR_SPRINT.md para refletir check #13: violação.

---

## Gambiarras específicas desta sprint

1. **Apagar antes de migrar.** Deletar seção em TEMPLATE_V2 e só depois pensar em colocar em GAMBIARRAS. Proibido — migrar primeiro, verificar, depois remover.
2. **Link quebrado.** Substituir seção por link `GAMBIARRAS_POR_SPRINT.md` sem o anchor da seção. Resultado: usuário pousa no topo e precisa caçar. Proibido — usar anchor: `GAMBIARRAS_POR_SPRINT.md#catálogo-universal-de-gambiarras-20-padrões`.
3. **PROJECT_SNAPSHOT.md "preenchido depois".** Arquivo criado vazio com "TODO preencher". Proibido — dados reais na criação.
4. **Contagens preguiçosas.** Copiar "34 tools, 47 comandos" do GUIDE.md sem verificar. Proibido — rodar `ls nyx/tools/*.py | wc -l` e similares, colar no proof-of-work.
5. **Regenerar EXECUTAR_SPRINT.md sem ler antes.** Script que sobrescreve perdendo customização manual. Proibido — ler, regenerar, diff, aplicar.
6. **Header do sprint_invariants.sh "quase certo".** Manter "12" e adicionar comentário "+1 recente". Proibido — atualizar para "13" definitivo.
7. **Fluxo de 10 passos renumerado sem sincronizar referências.** Se GSD tem 10 passos e outro doc fala "passo 5", quebrar referência. Proibido — grep por "passo N" no repo depois de reordenar.

Ver também `dev-journey/08-templates/GAMBIARRAS_POR_SPRINT.md` seção DOC-CONSOLIDATE-01.

---

## Proof-of-work obrigatório

Formato padrão (ver SPRINT_TEMPLATE_V2.md seção "Proof-of-work"). Incluir obrigatoriamente:

- `cat /tmp/inv_before.txt | tail -10`, `cat /tmp/inv_after.txt | tail -10`, diff.
- `diff /tmp/lines_before.txt /tmp/lines_after.txt` mostrando redução de linhas.
- `head -5 scripts/sprint_invariants.sh` provando header corrigido.
- Recorte de `EXECUTAR_SPRINT.md` mostrando bloco injetado.
- Conteúdo de `PROJECT_SNAPSHOT.md` na íntegra.
- `git show --stat HEAD`.

---

## Validação humana (checklist do usuário)

```bash
cd /home/andrefarias/Desenvolvimento/Nyx-Code

# 1. Conferir catálogo migrado
grep "Catálogo Universal de Gambiarras" dev-journey/08-templates/GAMBIARRAS_POR_SPRINT.md

# 2. Conferir link no template
grep "Fonte canônica" dev-journey/08-templates/SPRINT_TEMPLATE_V2.md

# 3. Conferir GUIDE.md enxugado
wc -l GUIDE.md    # menor que antes

# 4. Conferir header
head -5 scripts/sprint_invariants.sh    # "13 checks"

# 5. Conferir injeção
python scripts/update_next_sprint.py
cat EXECUTAR_SPRINT.md | grep -A 3 "GAMBIARRAS"

# 6. Conferir snapshot
cat dev-journey/08-templates/PROJECT_SNAPSHOT.md

# 7. Sprint movida
ls dev-journey/06-sprints/concluidos/SPRINT_DOC_CONSOLIDATE_01.md    # existe
ls dev-journey/06-sprints/producao/SPRINT_DOC_CONSOLIDATE_01.md      # NÃO existe
```

---

## Riscos

| Risco | Mitigação |
|-------|-----------|
| Link quebrado após reorganização de seções em GAMBIARRAS_POR_SPRINT | Usar anchor estável com slug explícito; testar abrindo no preview markdown antes de commitar |
| Injeção no EXECUTAR_SPRINT duplica conteúdo a cada run | Marcador `<!-- GAMBIARRAS_INJECT -->` e `<!-- /GAMBIARRAS_INJECT -->` delimitam região substituível |
| Dados em PROJECT_SNAPSHOT.md envelhecem rápido | Adicionar nota "regerado a cada sprint de manutenção"; gerador automático é trabalho futuro |
| Sprint anterior referencia "12 checks" em relatório antigo | Não editar relatórios passados — só docs vivos |
| Fluxo de 10 passos em GSD divergir do que GUIDE.md referencia | Depois da migração, grep "próxima sprint" em todo o repo para pegar menções órfãs |
| Injeção de bloco grande polui EXECUTAR_SPRINT.md | Limitar recorte a ~50 linhas; se seção maior, cortar e colocar nota "ver GAMBIARRAS_POR_SPRINT.md seção <ID>" |

---

*"A perfeição se alcança, não quando não há mais nada a acrescentar, mas quando não há mais nada a retirar." -- Antoine de Saint-Exupéry
