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

## Critério binário de aceite

- [ ] Critério 1 (claro, não ambíguo)
- [ ] Critério 2
- [ ] Gauntlet `--only <fase>` passa 100%
- [ ] `ruff` não reclama
- [ ] Nenhuma violação de `forbidden[]`
- [ ] `CLAUDE.md` + `SPRINT_ORDER_MASTER.md` atualizados marcando CONCLUIDA
- [ ] Sprint movida de `producao/` para `concluidos/`
- [ ] Commit atômico criado com mensagem no padrão `tipo: descrição`

---

## Riscos

| Risco | Mitigação |
|-------|-----------|
| ... | ... |

---

*"Citação de filósofo em PT-BR." -- Autor*
