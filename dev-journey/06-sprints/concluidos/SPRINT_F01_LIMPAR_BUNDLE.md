## 0. SPEC (machine-readable)

```yaml
sprint:
  id: F-01
  title: "Limpar bundle OpenClaude + remover dependência Node.js"
  touches:
    - path: dist/cli.mjs
      reason: "Remover -- substituído pelo agent Python"
    - path: bin/nyx
      reason: "Remover -- era wrapper Node.js"
    - path: package.json
      reason: "Manter como metadata, remover scripts de build"
    - path: run.sh
      reason: "Alterar bloco TUI para chamar Python em vez de Node.js"
    - path: nyx/cli.py
      reason: "Novo ponto de entrada Python"
  forbidden:
    - "Manter dist/cli.mjs (544K linhas de JS compilado sem source)"
    - "Depender de Node.js para funcionar"
  acceptance_criteria:
    - "Zero arquivos .mjs no projeto"
    - "run.sh lança nyx/cli.py em vez de bin/nyx"
    - "node não é pré-requisito para rodar"
    - "Gauntlet passa 100%"
```

---

# Sprint F-01 -- Limpar bundle OpenClaude

**Status:** CONCLUIDA (header corrigido em MASTER-CLEANUP-02 2026-05-20; presença em concluidos/ implica CONCLUIDA conforme convenção do projeto)
**Data:** 2026-04-04
**Prioridade:** CRITICA
**Tipo:** Fix
**Dependências:** --
**Desbloqueia:** P-01

---

## Problema

O `dist/cli.mjs` é um bundle compilado de 544K linhas do fork Gitlawb/OpenClaude.
Não temos o source code. O bundle contém:
- 31 referências a "openclaude/OpenClaude"
- Textos de ajuda mostrando "OpenClaude supports..."
- User-Agent "claude-cli/99.0.0"
- Referências a caminhos do desenvolvedor original (/Users/kevin/Projects/)

Não dá para rebuildar. A solução é remover o bundle e substituir por um agent Python próprio.

## Implementação

### 1. Remover artefatos Node.js

```bash
rm dist/cli.mjs
rm bin/nyx
```

Manter `package.json` como metadata do projeto (nome, versão, repositório).

### 2. Criar stub `nyx/cli.py`

Ponto de entrada mínimo que será expandido na P-01:
- Banner Nyx
- Verificação de Ollama
- Mensagem indicando que o agent loop está sendo construído

### 3. Atualizar `run.sh`

Trocar o bloco da TUI de:
```bash
node "$SCRIPT_DIR/bin/nyx" --bare --thinking disabled ...
```
Para:
```bash
"$SCRIPT_DIR/venv/bin/python" "$SCRIPT_DIR/nyx/cli.py" ...
```

### 4. Atualizar `.gitignore`

Adicionar `dist/` e `bin/nyx` ao .gitignore.

### 5. Atualizar sync.py

Remover `bin/nyx` da lista de estrutura obrigatória.
Adicionar `nyx/cli.py` no lugar.

## Verificação

- [ ] `dist/cli.mjs` não existe
- [ ] `bin/nyx` não existe
- [ ] `run.sh` lança Python em vez de Node.js
- [ ] `python nyx/cli.py` executa sem erro
- [ ] `python scripts/sync.py` passa sem erros
- [ ] Gauntlet passa 100% (fases que não dependem da TUI)

---

*"Simplificar é o mais difícil dos trabalhos." -- Auguste Perret*
