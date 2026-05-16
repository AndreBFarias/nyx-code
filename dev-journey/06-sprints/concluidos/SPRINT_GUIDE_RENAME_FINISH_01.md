# SPRINT GUIDE-RENAME-FINISH-01 — Fechar rename CLAUDE.md → GUIDE.md (débito do commit d77d8c7)

## 0. SPEC (machine-readable)

```yaml
sprint:
  id: GUIDE-RENAME-FINISH-01
  title: "Finalizar rename CLAUDE.md → GUIDE.md (243 ocorrências internas pós d77d8c7)"
  onda: 23
  bloco: 23.0 Recuperação de débito
  prioridade: ALTA
  tipo: Refactor+Docs
  dependencias: []
  desbloqueia: []
  origem: "Sessão IA anterior perdeu trabalho por freezy. Commit d77d8c7 alinhou gitignore+workflow; restou rename interno em ~45 arquivos."

  touches:
    - path: "45 arquivos já modificados no working tree (rename de string em docs, sprints, scripts)"
      reason: "Aproveitar trabalho da sessão IA anterior; commit + N-para-N completo"
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/agent/prompt.py
      reason: "Renomear função build_claude_md_context() → build_guide_md_context() (consistência)"
      linhas_alvo: "75-85"
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/scripts/update_docs.py
      reason: "Renomear função update_claude_md() → update_guide_md() (consistência)"
      linhas_alvo: "129-180, 277+"

  creates: []
  removes: []

  n_to_n_pairs:
    - descricao: "Função build_claude_md_context exposta em prompt.py é chamada em loop.py ou cli.py — atualizar call-sites"
      paths:
        - /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/agent/prompt.py
        - "todos call-sites encontrados via grep"
    - descricao: "Função update_claude_md em update_docs.py é chamada em main() — atualizar call-site interno"
      paths:
        - /home/andrefarias/Desenvolvimento/Nyx-Code/scripts/update_docs.py

  forbidden:
    - "Adicionar novas mudanças além do rename"
    - "Mexer em sprints CONCLUIDAS sem necessidade do rename"
    - "Deixar referências a CLAUDE.md em arquivo NÃO-symlink (CLAUDE.md continua existindo só como symlink local)"
    - "Adicionar emoji"
    - "Quebrar update_docs.py: ele precisa continuar atualizando GUIDE.md no auto-update"

  tests:
    - cmd: "grep -rln 'CLAUDE\\.md' nyx/ scripts/ dev-journey/ 2>/dev/null | wc -l"
      timeout: 10
      deve_passar: true
      nota: "Deve retornar 0 após o fix (excluindo .claude/ e o próprio symlink)"
    - cmd: "grep -rln 'claude_md\\|build_claude_md\\|update_claude_md' nyx/ scripts/ 2>/dev/null"
      timeout: 5
      deve_passar: true
      nota: "Deve retornar vazio (todas as funções renomeadas)"
    - cmd: "./run.sh --smoke"
      timeout: 60
      deve_passar: true
    - cmd: "bash scripts/sprint_invariants.sh"
      timeout: 60
      deve_passar: "FAIL_AFTER <= FAIL_BEFORE"
    - cmd: "python scripts/update_docs.py --check"
      timeout: 30
      deve_passar: true

  acceptance_criteria:
    - "Zero ocorrência de 'CLAUDE.md' em nyx/, scripts/, dev-journey/ (excluindo .claude/)"
    - "Zero função/variável com nome 'claude_md' em nyx/, scripts/"
    - "build_claude_md_context renomeada para build_guide_md_context com call-sites atualizados"
    - "update_claude_md renomeada para update_guide_md com call-sites atualizados"
    - "Smoke + gauntlet rapido passam"
    - "Commit dedicado descrevendo origem (recuperação do freezy d77d8c7)"
    - "Acentuação PT-BR; zero menção a IA"
```

---

**Status:** CONCLUIDA
**Data criação:** 2026-05-15
**Data conclusão:** 2026-05-16
**Modelo obrigatório:** claude-opus-4-7 (sem subagentes)
**Resultado:** FAIL_AFTER=0=FAIL_BEFORE; smoke ok; zero refs legadas restantes.

---

# Sprint GUIDE-RENAME-FINISH-01

## Origem

Em 2026-04-21, o commit `d77d8c7 chore: alinhar com padrão anti-IA (gitignore + workflow)` mudou `CLAUDE.md` para `GUIDE.md` no `.gitignore` e no workflow `anonymity-check.yml`. A sessão IA seguinte iniciou o rename N-para-N nos ~45 arquivos restantes (docs, sprints, scripts internos), mas **freezou antes de commit**.

Em 2026-05-15, na sessão de auditoria, o estado foi descoberto: working tree com 45 arquivos modificados, todos rename literal string `"CLAUDE.md"` → `"GUIDE.md"`. Função `build_claude_md_context` em `prompt.py` e `update_claude_md` em `update_docs.py` continuam com nomes legados.

## Solução

### Parte 1 — Commit do trabalho existente (95% pronto)

Apenas adicionar os 45 arquivos já modificados ao stage e commitar. Não tocar no conteúdo deles.

```bash
git add .gitignore .github/workflows/anonymity-check.yml
git add EXECUTAR_SPRINT.md GSD.md
git add dev-journey/01-getting-started/FOLDER_STRUCTURE.md
git add dev-journey/03-decisions/ADR_005_ANONIMATO.md \
        dev-journey/03-decisions/ADR_015_DOCUMENTACAO_CONTINUIDADE.md \
        dev-journey/03-decisions/ADR_024_RENDER_LAYER.md
git add dev-journey/04-features/FEATURE_MAP.md
git add dev-journey/05-guides/LLM_GUIDE.md
# (não incluir SPRINT_ORDER_MASTER nesse commit — já tem mudança da Onda 23)
git add dev-journey/06-sprints/concluidos/SPRINT_*.md
git add dev-journey/06-sprints/producao/SPRINT_COMPLETER_ARGS_01.md \
        dev-journey/06-sprints/producao/SPRINT_DEPLOY_01A.md \
        dev-journey/06-sprints/producao/SPRINT_ONBOARDING_01.md \
        dev-journey/06-sprints/producao/SPRINT_VALIDATE_FINAL_01.md
git add dev-journey/07-reports/*.md dev-journey/07-reports/gauntlet/checkpoint.json
git add dev-journey/08-templates/*.md
git add dev-journey/09-legacy/tests-expect/test_all_features.exp
git add nyx/agent/commands/_observability.py nyx/agent/output.py
git add scripts/gauntlet/nyx_gauntlet.py scripts/hooks/pre-commit \
        scripts/sprint_invariants.sh scripts/sync.py scripts/update_next_sprint.py
```

### Parte 2 — Renomear funções legadas (consistência)

Em `nyx/agent/prompt.py:78`:

```diff
-def build_claude_md_context(project_root: str) -> str:
-    """Carrega GUIDE.md se existir (compacto para manter contexto leve)."""
-    claude_md = Path(project_root) / "GUIDE.md"
-    if claude_md.exists():
-        content = claude_md.read_text(encoding="utf-8", errors="replace")
+def build_guide_md_context(project_root: str) -> str:
+    """Carrega GUIDE.md se existir (compacto para manter contexto leve)."""
+    guide_md = Path(project_root) / "GUIDE.md"
+    if guide_md.exists():
+        content = guide_md.read_text(encoding="utf-8", errors="replace")
         return f"\n[GUIDE.md]\n{content[:800]}\n"
     return ""
```

Atualizar call-sites com:

```bash
grep -rn "build_claude_md_context" nyx/ scripts/
# substituir cada por build_guide_md_context
```

Em `scripts/update_docs.py:131`:

```diff
-def update_claude_md(
+def update_guide_md(
     tools: int, commands: int, services: int, tests: int, adrs: int, sprints: dict[str, int], check: bool
 ) -> bool:
```

E o call-site em `main()`:

```diff
-    if update_claude_md(tools, commands, services, tests, adrs, sprints, args.check):
+    if update_guide_md(tools, commands, services, tests, adrs, sprints, args.check):
```

### Parte 3 — Verificação

```bash
grep -rln 'CLAUDE\.md' nyx/ scripts/ dev-journey/ 2>/dev/null | grep -v '\.claude/' | wc -l  # 0
grep -rln 'claude_md\|build_claude_md\|update_claude_md' nyx/ scripts/ 2>/dev/null  # vazio
./run.sh --smoke
bash scripts/sprint_invariants.sh
python scripts/update_docs.py --check
```

## Gambiarras proibidas

- Commitar tudo de uma vez sem revisar (são 45 arquivos — diff deve bater com o rename simples).
- Tocar em arquivos `concluidos/` além do rename de string.
- Deixar funções `claude_md` no código.
- Mexer em `SPRINT_ORDER_MASTER.md` nesta sprint (já tem mudança da Onda 23 dele).

## Pontos de feedback (ADR-025 PROPOSTO)

Esta sprint é mecânica; pontos de feedback se aplicam mais ao processo:
- Commit incremental por categoria (docs / scripts / sprints), não bigbang.
- Logs claros mostrando: "X arquivos renomeados; Y funções renomeadas; Z call-sites atualizados".

---

*"Trabalho não-commitado é dívida com juros." -- anônimo*
