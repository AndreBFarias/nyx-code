# SPRINT PROMPT-TOOLNAME-SEARCH-FIX-01 — system prompt cita tool-fantasma grep_files (real é search)

## 0. SPEC (machine-readable)

```yaml
sprint:
  id: PROMPT-TOOLNAME-SEARCH-FIX-01
  title: "Trocar grep_files (tool inexistente) por search no system prompt; o prompt se contradiz com o reminder 354"
  onda: 44
  bloco: "44 -- auditoria das ondas 36-43 (2026-06-03)"
  prioridade: BAIXA
  tipo: Bugfix / Prompt
  dependencias: []
  desbloqueia: []

  touches:
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/agent/prompt.py
      reason: "build_system_prompt (linha 106) lista 'grep_files' como tool de busca, mas a tool real é 'search' (nyx/agent/tools/search.py, name='search'). Não há alias grep_files no parser. O reminder 354 (linha 194) já usa 'search' -- o próprio prompt se contradiz."
      linhas_alvo: "105-110 (descrição das tools no system prompt)"

  creates: []
  removes: []
  n_to_n_pairs: []

  forbidden:
    - "Renomear a tool real ou criar alias grep_files (a direção certa é o prompt usar o nome real 'search')"
    - "Adicionar emoji ou menção a IA externa"

  tests:
    - cmd: "bash scripts/sprint_invariants.sh"
      timeout: 180
      esperado: "14/14 PASS"
    - cmd: "grep -n 'grep_files' nyx/agent/prompt.py"
      timeout: 10
      esperado: "vazio (nenhuma ocorrência após o fix)"

  acceptance_criteria:
    - "nyx/agent/prompt.py não cita 'grep_files'; usa 'search'"
    - "O system prompt e o reminder (build_reminder) usam o MESMO nome de tool de busca (search)"
    - "Invariantes 14/14, ruff/acento OK"
```

---

**Status:** PENDENTE
**Data criação:** 2026-06-03
**Origem:** auditoria das ondas 36-43 (achado A5, severidade BAIXA, fix trivial). Inconsistência interna do system prompt que confunde o 3b — o oposto do que 354 tenta fazer.
**Modelo obrigatório:** claude-opus (sem subagentes)

---

## Contexto do projeto (snapshot — não referência)

> - ADR-031: modelo padrão qwen2.5-coder:3b; nomes de tool inconsistentes no prompt induzem alucinação de tool num modelo fraco.
> - A tool de busca real chama-se `search` (`nyx/agent/tools/search.py`, `name="search"`). O parser tem aliases `grep`/`search`→SEARCH, mas **não** `grep_files`.

---

## Problema

`prompt.py:106` (system prompt principal):

```python
"- Ler/listar/buscar arquivo real (read_file, list_files, grep_files)\n"
```

`grep_files` **não existe** como tool (nem como alias). O nome real é `search`. Pior: o `build_reminder` (`prompt.py:194`, fix 354) já instrui usar `search`. O modelo recebe **dois nomes diferentes** para a mesma capacidade de busca no mesmo contexto — exatamente a inconsistência que faz um 3b alucinar uma tool inexistente, anulando parte do esforço de 354.

Confirmação: `grep -rn grep_files nyx/` retorna só `prompt.py:106` e um comentário inofensivo em `repomap.py:3`. Nenhuma tool ou alias real.

---

## Solução proposta

Trocar `grep_files` por `search` na linha 106:

```python
# Antes
"- Ler/listar/buscar arquivo real (read_file, list_files, grep_files)\n"
# Depois
"- Ler/listar/buscar arquivo real (read_file, list_files, search)\n"
```

Verificar as linhas vizinhas (105-110) por outros nomes de prosa que não batam com tools reais (a lista canônica de tools vem de `tool_names` no `tools_str`, mas a prosa explicativa é hardcoded).

---

## Proof-of-work esperado (runtime real)

```bash
bash scripts/sprint_invariants.sh                       # 14/14 PASS
grep -n 'grep_files' nyx/agent/prompt.py                # vazio
python3 ~/.config/zsh/scripts/validar-acentuacao.py --paths nyx/agent/prompt.py
```

---

## Critério binário de aceite

- [ ] `prompt.py` não cita `grep_files`
- [ ] System prompt e reminder usam `search` para busca
- [ ] Invariantes 14/14, ruff/acento OK
- [ ] Spec movida `producao/` → `concluidos/`; MASTER marca CONCLUIDA

---

## Riscos

| Risco | Mitigação |
|-------|-----------|
| Outras prosas com nome-fantasma passam batido | Revisar 105-110 inteiras; cruzar com `ToolRegistry` os nomes citados |

---

*"O contrato que usa dois nomes para a mesma coisa não é contrato." -- anônimo*
