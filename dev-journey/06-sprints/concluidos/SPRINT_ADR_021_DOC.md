## 0. SPEC

```yaml
sprint:
  id: ADR-021-DOC
  title: "Materializar ADR-021: Dependências opcionais (tree-sitter)"
  onda: 22
  bloco: 2.5
  prioridade: MÉDIA
  tipo: Docs
  dependencias: []
  desbloqueia: [CTX-03, UX-DESIGN-01]

  creates:
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/dev-journey/03-decisions/ADR_021_OPTIONAL_DEPENDENCIES.md
      reason: "ADR referenciado por CTX-03 (RepoMap via AST) nunca foi criado como arquivo"

  touches:
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/GUIDE.md
      reason: "Tabela de ADRs vigentes pula de 020 para 024 — corrigir inserindo 021"

  removes: []

  forbidden:
    - "Criar ADR com Status: proposto ou sem Status"
    - "Duplicar conteúdo de outra ADR"
    - "Quebrar a numeração sequencial (021 deve vir entre 020 e 022)"

  tests:
    - cmd: "test -f dev-journey/03-decisions/ADR_021_OPTIONAL_DEPENDENCIES.md"
      deve_passar: true
    - cmd: "grep -E '^\\*\\*Status:\\*\\* ACEITO' dev-journey/03-decisions/ADR_021_OPTIONAL_DEPENDENCIES.md"
      deve_passar: true
    - cmd: "grep -c '^| 021 |' GUIDE.md"
      esperado: ">= 1"

  acceptance_criteria:
    - "Arquivo ADR_021_OPTIONAL_DEPENDENCIES.md existe com estrutura canônica (Status/Contexto/Decisão/Consequências/Alternativas)"
    - "Status: ACEITO"
    - "GUIDE.md menciona ADR-021 na tabela de ADRs vigentes"
    - "Citação de filósofo no final"
```

---

# Sprint ADR-021-DOC — Dependências opcionais

**Status:** CONCLUIDA (header corrigido em MASTER-CLEANUP-02 2026-05-20; presença em concluidos/ implica CONCLUIDA conforme convenção do projeto)
**Data criação:** 2026-04-19
**Modelo obrigatório:** claude-opus-4-7 (sem subagentes)

---

## Contexto do projeto (snapshot)

> - ADR-001 Local First; ADR-013 Integração Obrigatória; ADR-015 Documentação para continuidade.
> - Sprint CTX-03 (`producao/SPRINT_CTX_03_REPOMAP.md`) referencia ADR-021 para justificar tree-sitter como dependência opcional.
> - `GUIDE.md` afirma "ADRs vigentes (24)" e lista até 020 + salta para 024; 021/022/023 mencionadas no cabeçalho sem arquivo.
> - ADR-023 será criada em UX-DESIGN-01; ADR-022 será criada em ADR-022-DOC. Esta sprint fecha a 021.

---

## Problema

Referência órfã: sprints e documentos mencionam ADR-021 (tree-sitter opcional) mas não existe arquivo. Impossibilita CTX-03 ser executada sem violar ADR-015 (Documentação para continuidade).

---

## Solução proposta

Criar `ADR_021_OPTIONAL_DEPENDENCIES.md` cobrindo:
- Conceito: dependências **opcionais** (tree-sitter, kitty, outras) habilitam features avançadas mas o sistema funciona sem elas.
- Decisão: toda dep opcional faz `import` dentro de try/except, expõe `HAS_<FEATURE>` booleano, e fallback textual/graceful.
- Consequências positivas: Local First preservado; instalação mínima continua funcionando.
- Consequências negativas: código um pouco mais verboso; teste dos dois caminhos exigido.
- Alternativas: (a) deps obrigatórias com fallback em runtime (rejeitada — bloat de instalação), (b) deps em extras_require (aceitável, mas não precisa de ADR separada).

---

## Arquivos alvo

### `/home/andrefarias/Desenvolvimento/Nyx-Code/dev-journey/03-decisions/ADR_021_OPTIONAL_DEPENDENCIES.md` (criar)

Estrutura:
```markdown
# ADR-021 — Dependências opcionais

**Status:** ACEITO
**Data:** 2026-04-19
**Contexto da Onda:** 22, Bloco 2.5

## Contexto

O Nyx é Local First (ADR-001) e precisa rodar em hardware modesto (RTX 3050 4GB). Features avançadas como RepoMap via AST (tree-sitter), renderização em kitty, etc., são **desejáveis** mas não podem ser exigências de instalação.

## Decisão

Dependências que habilitam features avançadas são **opcionais**:
1. `import` dentro de `try/except ImportError`.
2. Flag booleana no módulo: `HAS_TREE_SITTER = True/False`.
3. Feature detecta flag e fornece fallback (p.ex.: RepoMap textual via grep).
4. README lista "dependências opcionais" com comando de instalação.
5. Teste no Gauntlet cobre ambos caminhos (com e sem dep).

## Consequências

Positivas:
- Instalação base permanece leve (Local First preservado).
- Sistema degrada gracefully em máquinas sem a dep.

Negativas:
- Código fica verboso (try/except em cada import opcional).
- Teste exige cobrir dois caminhos.

## Alternativas

- Deps em `extras_require` do `pyproject.toml`: aceitável, mas não substitui a detecção runtime.
- Dep obrigatória com fallback runtime: rejeitada (bloat).

## Referências

- ADR-001 Local First.
- ADR-013 Integração Obrigatória.
- Sprint CTX-03 (primeiro consumidor).

*"Citação de filósofo em PT-BR." -- autor*
```

### `/home/andrefarias/Desenvolvimento/Nyx-Code/GUIDE.md`

Adicionar linha na tabela de ADRs vigentes:
```
| 021 | Dependências opcionais (tree-sitter, kitty, etc.) |
```

---

## Comandos de verificação

```bash
# 1. arquivo criado
test -f dev-journey/03-decisions/ADR_021_OPTIONAL_DEPENDENCIES.md && echo OK

# 2. Status ACEITO
grep '^\*\*Status:\*\* ACEITO' dev-journey/03-decisions/ADR_021_OPTIONAL_DEPENDENCIES.md

# 3. Referência em GUIDE.md
grep -c '^| 021 |' GUIDE.md
```

---

## Critério binário de aceite

- [ ] `ADR_021_OPTIONAL_DEPENDENCIES.md` criado com seções canônicas
- [ ] Status: ACEITO
- [ ] GUIDE.md atualizado (linha 021 na tabela)
- [ ] Citação de filósofo no final do ADR
- [ ] Commit `docs: cria ADR-021 sobre dependências opcionais`

---

## Gambiarras específicas

- **Status proposto** — proibido.
- **ADR sem alternativas consideradas** — obrigatório incluir a seção Alternativas.
- **Copiar e colar ADR-001 com troca de título** — proibido.

---

## Riscos

| Risco | Mitigação |
|-------|-----------|
| ADR inchar a ponto de virar manual | Manter < 80 linhas; decisão objetiva |

---

*"Nem toda dependência merece ser universal." -- anônimo*
