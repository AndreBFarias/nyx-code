## 0. SPEC (machine-readable)

```yaml
sprint:
  id: CTX-03
  title: "RepoMap via AST -- índice de símbolos Python no prompt"
  touches:
    - path: nyx/agent/repomap.py
      reason: "Novo módulo: RepoMap que usa ast (stdlib) + hook opcional tree-sitter"
    - path: nyx/agent/loop.py
      reason: "Gerar repomap no boot, invalidar em write_file/edit_file"
    - path: nyx/agent/prompt.py
      reason: "Placeholder {repo_map} no system prompt (cap 2KB)"
    - path: pyproject.toml
      reason: "Declarar tree-sitter como optional dep"
    - path: dev-journey/03-decisions/ADR_021_DEPS_OPCIONAIS.md
      reason: "Novo ADR sobre deps opcionais (tree-sitter)"
  n_to_n_pairs:
    - "Se tool write_file/edit_file toca .py, invalidar cache do repomap"
  forbidden:
    - "tree-sitter como dep obrigatória (viola local-first leve)"
    - "Indexar node_modules, venv, __pycache__, .git"
    - "Repo-map > 2KB no prompt"
  tests:
    - cmd: "./run.sh --gauntlet --only contexto"
      timeout: 240
    - cmd: "manual: perguntar 'onde está a classe X', resposta precisa sem grep"
      timeout: 120
  acceptance_criteria:
    - "Boot: repomap indexa nyx/ em <2s"
    - "Formato compacto por arquivo: 'path: class X; def foo(); def bar()'"
    - "Cap 2KB com truncagem explícita (... N omitidos)"
    - "Cache em ~/.nyx/cache/repomap.json (TTL 1h, invalidação por edit)"
    - "Funciona 100% sem tree-sitter instalado (ast puro)"
    - "Com tree-sitter: ganha suporte JS/TS/MD"
    - "ADR-021 documentado"
```

---

# Sprint CTX-03 -- Repo-map via AST (tree-sitter opcional)

**Status:** PENDENTE
**Data:** 2026-04-17
**Prioridade:** MÉDIA
**Tipo:** Feature
**Dependências:** CTX-02
**Desbloqueia:** CTX-04 (opcional)

---

## Problema / Contexto

Hoje, quando o dev pergunta "onde está a classe AgentLoop?", a Nyx faz `list_files` + `grep_files` + `read_file` -- 3 tool calls e ~30s. Aider resolve isso com um repo-map sempre injetado no system prompt: ela já sabe, só responde.

Dois caminhos: AST da stdlib Python (sem dep nova, mas só indexa `.py`) ou tree-sitter (multi-linguagem, mas dep pesada ~5MB). Solução híbrida: AST como default, tree-sitter como dep opcional opt-in.

## Implementação

### Fase 1 -- Indexador AST

- `nyx/agent/repomap.py`:
  ```python
  class RepoMap:
      def __init__(self, root: Path): ...
      def build(self) -> dict[str, list[str]]: ...
      def render(self, budget_bytes: int = 2048) -> str: ...
      def invalidate(self, path: Path) -> None: ...
  ```
- `build()` glob `**/*.py`, exclui: `.git`, `venv`, `__pycache__`, `node_modules`, `openclaud`, `logs`
- Pra cada arquivo: `ast.parse(source)`, walk AST, extrai `ClassDef`/`FunctionDef`/`AsyncFunctionDef` top-level e métodos
- Formato por arquivo: `nyx/agent/loop.py: class AgentLoop(BaseAgent); def run(user_input); def close()`

### Fase 2 -- Cache invalidável

- `~/.nyx/cache/repomap.json`: `{path: {mtime: int, symbols: [str]}}`
- No boot: compara mtime com cache. Se igual, reusa. Se diferente ou novo, reindexar arquivo.
- `invalidate(path)`: seta mtime inválido no cache pra forçar reindex no próximo boot (ou agora se já carregado).

### Fase 3 -- Cap 2KB com priorização

- `render(budget_bytes=2048)`:
  - Prioridade 1: arquivos em `session.files_touched` (sessão atual)
  - Prioridade 2: arquivos em `nyx/agent/`
  - Prioridade 3: `nyx/services/`, `nyx/tools/`
  - Prioridade 4: resto
- Itera por prioridade, acumula até estourar 2KB, corta e adiciona `... {N} arquivos omitidos`.

### Fase 4 -- Hook em tools de escrita

- `nyx/agent/tools/write_file.py` e `edit_file.py`: após escrita bem-sucedida, se `.py`, chamar `agent.repomap.invalidate(path)`.
- Loop carrega `repomap` no `__init__`, disponibiliza como `self._repomap`.

### Fase 5 -- Tree-sitter opcional

- `pyproject.toml`:
  ```toml
  [project.optional-dependencies]
  tree-sitter = [
      "tree-sitter>=0.21",
      "tree-sitter-python>=0.21",
      "tree-sitter-javascript>=0.21",
      "tree-sitter-typescript>=0.21",
  ]
  ```
- `repomap.py`: tenta `import tree_sitter`; se ok, usa pra `.js`/`.ts`/`.md` adicional. Se fail, loga debug e segue só com `.py`.

### Fase 6 -- ADR-021

- Criar `dev-journey/03-decisions/ADR_021_DEPS_OPCIONAIS.md`:
  - Contexto: features como repo-map multi-linguagem são úteis mas deps pesadas contrariam local-first leve
  - Decisão: usar `[project.optional-dependencies]` pra opt-in explícito
  - Consequências: core fica leve, features avançadas disponíveis sob demanda

### Fase 7 -- Prompt

- `nyx/agent/prompt.py`: placeholder `{repo_map}` injeta como `### Mapa do repositório\n{repo_map}\n---\n`.

## Verificação

```bash
./run.sh
# No log: "repomap: 87 arquivos indexados, 1.8KB no prompt"
# Perguntar: "em qual arquivo está definida a classe AgentLoop?"
# Esperado: "nyx/agent/loop.py" -- resposta em <3s, 0 tool calls
# Editar um .py via Nyx
cat ~/.nyx/cache/repomap.json | jq '.[0]'
# Esperado: mtime atualizado no arquivo editado
./run.sh --gauntlet --only contexto
# Instalar tree-sitter opcional
pip install -e ".[tree-sitter]"
./run.sh
# Esperado: log mostra "repomap: tree-sitter ativo, 95 arquivos (inclui .ts, .js)"
```

- [ ] Boot indexa nyx/ em <2s
- [ ] Cache em ~/.nyx/cache/repomap.json
- [ ] Cap 2KB respeitado
- [ ] Invalidação após edit funciona
- [ ] AST funciona sem tree-sitter
- [ ] Tree-sitter opcional amplia suporte
- [ ] ADR-021 documentado
- [ ] Gauntlet contexto passa

---

*"Um mapa não é o território." -- Alfred Korzybski*
