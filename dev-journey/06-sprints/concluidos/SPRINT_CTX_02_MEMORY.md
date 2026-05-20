## 0. SPEC (machine-readable)

```yaml
sprint:
  id: CTX-02
  title: "Memória persistente cross-session em ~/.nyx/memory/<project>/*.md"
  touches:
    - path: nyx/agent/memory.py
      reason: "Novo módulo: NyxMemory (load/write em ~/.nyx/memory/<project>/)"
    - path: nyx/agent/loop.py
      reason: "Carregar memory no __init__, injetar no prompt"
    - path: nyx/agent/tools/memory_tool.py
      reason: "Nova tool: write_memory(file, content, reason)"
    - path: nyx/agent/tools/__init__.py
      reason: "Registrar tool no registry (ADR-013)"
    - path: nyx/agent/prompt.py
      reason: "Placeholder {memory_files}"
  n_to_n_pairs: []
  forbidden:
    - "Criar arquivos fora de ~/.nyx/memory/<project>/ (sandbox)"
    - "Arquivo > 4KB (limitar antes de escrever)"
    - "Tool sem permission check"
  tests:
    - cmd: "./run.sh --gauntlet --only tools"
      timeout: 180
    - cmd: "manual: 'lembra disso', verificar arquivo criado"
      timeout: 60
  acceptance_criteria:
    - "Boot carrega ~/.nyx/memory/<project>/*.md e injeta no prompt"
    - "Tool write_memory listada em /tools"
    - "Limite 4KB respeitado"
    - "Permission always_confirm aplicada"
    - "MEMORY.md index mantido (auto)"
    - "Sobrevive restart"
    - "Acentuação PT-BR"
```

---

# Sprint CTX-02 -- Memória cross-session (GSD-C)

**Status:** CONCLUIDA (header corrigido em MASTER-CLEANUP-02 2026-05-20; presença em concluidos/ implica CONCLUIDA conforme convenção do projeto)
**Data:** 2026-04-17
**Prioridade:** ALTA
**Tipo:** Feature
**Dependências:** CTX-01
**Desbloqueia:** CTX-03

---

## Problema / Contexto

Hoje a Nyx não se lembra de nada entre execuções do REPL além do histórico da sessão anterior. Convenções do dev ("uso pyenv 3.12", "sempre type hints", "commit message sem emoji") precisam ser re-explicadas toda vez.

Claude Code resolve isso com `GUIDE.md` (que já existe neste projeto, feito por dev). A ideia aqui é inverter: a Nyx escreve/atualiza memory files durante a conversa.

Referência: sistema de memória do Claude Code descrito no system prompt (`~/.claude/projects/.../memory/`).

## Implementação

### Fase 1 -- NyxMemory

- `nyx/agent/memory.py`:
  ```python
  class NyxMemory:
      def __init__(self, project_root: str): ...
      def load(self) -> str: ...
      def write(self, file: str, content: str, reason: str) -> None: ...
      def index(self) -> list[dict]: ...
  ```
- Resolve diretório: `~/.nyx/memory/<slug(project_path)>/`
- `load`: concatena todos `.md` do dir com separadores `--- {filename} ---\n{content}`; cap 8KB total
- `write`: valida 4KB max, sanitiza filename (slug), garante `.md`, atualiza `MEMORY.md` index

### Fase 2 -- Tool write_memory

- `nyx/agent/tools/memory_tool.py`:
  ```python
  def write_memory(file: str, content: str, reason: str) -> str:
      """Grava uma memória persistente sobre o projeto/dev.

      Args:
          file: nome do arquivo (sem extensão, será .md)
          content: conteúdo markdown, max 4KB
          reason: motivo curto, vira comentário no topo
      """
  ```
- Retorna path gravado em caso de sucesso, mensagem de erro em caso de violação de limite.

### Fase 3 -- Registry e permissions

- `nyx/agent/tools/__init__.py`: registrar `write_memory` no `TOOL_REGISTRY` com permission `always_confirm`.
- Descrição PT-BR clara no docstring (aparece em `/tools`).

### Fase 4 -- Injeção no prompt

- `nyx/agent/loop.py:__init__`: `self._memory = NyxMemory(project_root); self._memory_bundle = self._memory.load()`
- `nyx/agent/prompt.py`: placeholder `{memory_files}`. Bloco: `### Memória persistente\n{memory_files}\n---\n`.

### Fase 5 -- Gauntlet

- Adicionar caso na fase `tools`:
  - Setup: `rm -rf ~/.nyx/memory/test-project/`
  - Executar: `write_memory("teste", "use ruff", "validação gauntlet")`
  - Assert: arquivo existe, conteúdo bate, MEMORY.md atualizado

## Verificação

```bash
rm -rf ~/.nyx/memory/Nyx-Code
./run.sh
# Dizer: "lembra que eu sempre uso pyenv 3.12"
# Nyx chama write_memory -> confirmar [S/n] -> s
# Ctrl+D
ls ~/.nyx/memory/Nyx-Code/
cat ~/.nyx/memory/Nyx-Code/MEMORY.md
# Esperado: arquivo + index
./run.sh
# enviar: "o que você lembra de mim?"
# Nyx deve citar pyenv 3.12
./run.sh --gauntlet --only tools
```

- [ ] Tool registrada e funcional
- [ ] Sandbox respeitado (só grava em ~/.nyx/memory/<project>/)
- [ ] Limite 4KB aplicado
- [ ] Permission sempre pede confirmação
- [ ] MEMORY.md index auto
- [ ] Memória sobrevive restart e é injetada no prompt
- [ ] Acentuação PT-BR
- [ ] Gauntlet tools passa

---

*"A memória é a guardiã de todas as coisas." -- Cícero*
