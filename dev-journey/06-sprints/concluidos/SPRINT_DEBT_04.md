## 0. SPEC

```yaml
sprint:
  id: DEBT-04
  title: "Higienização ruff: F841 e F401 em analyze_tool/todo_write/web_search"
  onda: 22
  bloco: 2.5
  prioridade: MÉDIA
  tipo: Refactor
  dependencias: []
  desbloqueia: [UX-DESIGN-01]

  touches:
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/agent/tools/analyze_tool.py
      reason: "F841 — variável old_todos nunca usada (linha 46)"
      linhas_alvo: "40-50"
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/agent/tools/todo_write.py
      reason: "F841 — variável local atribuída e nunca lida (linha 58)"
      linhas_alvo: "52-62"
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/agent/tools/web_search.py
      reason: "F401 — duckduckgo_search.DDGS importado mas não usado (linha 67)"
      linhas_alvo: "60-72"

  creates: []
  removes: []

  forbidden:
    - "Usar # noqa para mascarar o erro em vez de corrigir"
    - "Remover código funcional como 'solução' — se for regressão de refactor, restaurar uso"
    - "Introduzir dependência nova para justificar uso do DDGS"

  tests:
    - cmd: "ruff check nyx/"
      esperado: "All checks passed!"
    - cmd: "bash scripts/sprint_invariants.sh | grep -E '^\\[FAIL\\].*10\\.'"
      esperado: "vazio (invariante #10 fecha)"
    - cmd: "./run.sh --gauntlet --only rapido"
      deve_passar: true

  acceptance_criteria:
    - "ruff check nyx/ retorna All checks passed"
    - "Invariante #10 sai de FAIL"
    - "Se variável F841 era usada em fluxo pretendido, restaurar uso; caso contrário, remover"
    - "DDGS: verificar se web_search.py ainda deve chamar DuckDuckGo; se sim, restaurar uso; se não, remover import"
    - "Gauntlet rapido passa"
```

---

# Sprint DEBT-04 — Higienização ruff

**Status:** PENDENTE
**Data criação:** 2026-04-19
**Modelo obrigatório:** claude-opus-4-7 (sem subagentes)

---

## Contexto do projeto (snapshot)

> - GUIDE.md: zero `# noqa` / `# type: ignore` indiscriminados.
> - Relatório do Bloco 2 da Onda 22 (linhas 146-154): 3 erros ruff pré-existentes, não tocados por `scope atômico`.
> - `sprint_invariants.sh` check #10 (`ruff reclama`) está FAIL por causa destes.

---

## Problema

```
F841 nyx/agent/tools/analyze_tool.py:46 -- Local variable `old_todos` never used
F841 nyx/agent/tools/todo_write.py:58   -- (variável local nunca lida)
F401 nyx/agent/tools/web_search.py:67   -- `duckduckgo_search.DDGS` imported but unused
```

Cada um exige investigação: são bugs semânticos (variável foi atribuída e uso foi perdido) ou resíduo de refactor (import morto).

---

## Solução proposta

Para cada erro: (1) ler contexto do arquivo; (2) decidir entre **restaurar uso** (se era parte do fluxo) ou **remover** (se é resíduo). Nunca mascarar com `# noqa`.

---

## Procedimento detalhado

### `analyze_tool.py:46` — `old_todos`

```bash
# passo 1: ler contexto
sed -n '30,60p' nyx/agent/tools/analyze_tool.py

# passo 2: grep por uso potencial
grep -n 'old_todos\|previous_todos\|existing_todos' nyx/agent/tools/analyze_tool.py
```

Se a análise pretendia comparar antes/depois e o uso foi perdido, **restaurar**. Se só restou atribuição, **remover**.

### `todo_write.py:58` — idem

Provavelmente segue mesmo padrão de comparação antes/depois (tool de todo). Verificar se há lógica de diff que deveria rodar.

### `web_search.py:67` — `DDGS`

`DDGS` é o cliente síncrono do `duckduckgo_search`. Se web_search.py usa apenas `AsyncDDGS` ou outra API, o import é resíduo. Se deveria fazer fallback síncrono, restaurar.

```bash
grep -n 'DDGS\|duckduckgo_search' nyx/agent/tools/web_search.py
```

---

## Comandos de verificação

```bash
# 1. ruff limpo
ruff check nyx/
# esperado: All checks passed!

# 2. invariante #10
bash scripts/sprint_invariants.sh | grep -E '^\[FAIL\].*10\.'
# esperado: vazio

# 3. tools ainda funcionais
python -c "from nyx.agent.tools.analyze_tool import AnalyzeTool; print(ok)"
python -c "from nyx.agent.tools.todo_write import TodoWriteTool; print(ok)"
python -c "from nyx.agent.tools.web_search import WebSearchTool; print(ok)"

# 4. smoke
./run.sh --gauntlet --only rapido
```

---

## Critério binário de aceite

- [ ] `ruff check nyx/` limpo
- [ ] Invariante #10 PASS
- [ ] Para cada F841: decisão justificada (restaurar uso OU remover) no commit message
- [ ] Para F401 (DDGS): decisão justificada
- [ ] Nenhum `# noqa` novo introduzido
- [ ] Gauntlet rapido passa
- [ ] Commit `refactor: resolve 3 avisos ruff em analyze_tool, todo_write, web_search`

---

## Gambiarras específicas

- **`# noqa: F841` inline** — proibido. Se variável é intencional de debug, prefixar com `_`.
- **Deletar o bloco inteiro** que contém a variável, para passar ruff. Proibido: bloco pode ter efeito colateral necessário.
- **`_ = DDGS  # touch**` — touch falso para silenciar linter. Proibido.

---

## Riscos

| Risco | Mitigação |
|-------|-----------|
| Remover variável que era parte de feature incompleta | Grep por nome da variável em todo nyx/ antes de remover; se for stub de feature, documentar decisão |
| `DDGS` é fallback quando AsyncDDGS falha | Ler web_search.py inteiro; se houver try/except com plan B, restaurar fallback |

---

*"Código morto apodrece e contamina o vivo." -- anônimo, do Tao dos programadores*
