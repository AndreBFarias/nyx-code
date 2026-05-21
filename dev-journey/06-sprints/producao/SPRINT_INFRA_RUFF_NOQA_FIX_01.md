# SPRINT INFRA-RUFF-NOQA-FIX-01 — Suprimir warning ruff de `# noqa-acento`

## 0. SPEC

```yaml
sprint:
  id: INFRA-RUFF-NOQA-FIX-01
  title: "Configurar pyproject.toml para reconhecer `# noqa-acento` como diretiva externa"
  onda: 25
  bloco: "25.meta Anti-débito de pipeline"
  prioridade: BAIXA
  tipo: Chore/Lint
  dependencias: [OUTPUT-VISIBLE-LEN-RENAME-01]
  desbloqueia: []

  touches:
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/pyproject.toml
      reason: "Adicionar config ruff para suprimir warning 'Invalid noqa directive' em `# noqa-acento` (marcador customizado consumido pelo validar-acentuacao.py externo)"

  forbidden:
    - "Tocar `nyx/agent/output.py`, `nyx/agent/lang_check.py` ou qualquer .py com `# noqa-acento`"
    - "Tocar `~/.config/zsh/scripts/validar-acentuacao.py` (script externo)"
    - "Tocar `nyx/proxy.py` (que também tem `# noqa-acento` em linhas 664/685 — mesmo padrão, mesma solução)"
    - "Emoji ou menção a IA externa"

  tests:
    - cmd: "./run.sh --smoke"
      timeout: 10
    - cmd: "bash scripts/sprint_invariants.sh"
      timeout: 30
      assert: "PASS=14"
    - cmd: "/home/andrefarias/.local/bin/ruff check nyx/agent/output.py nyx/agent/lang_check.py nyx/proxy.py 2>&1"
      assert: "All checks passed sem warning Invalid noqa"
    - cmd: "python3 ~/.config/zsh/scripts/validar-acentuacao.py --paths nyx/agent/output.py nyx/agent/lang_check.py nyx/proxy.py"
      assert: "rc=0 (marcador continua reconhecido)"

  acceptance_criteria:
    - "ruff check sobre os 3 arquivos não emite warning 'Invalid `# noqa` directive'"
    - "validar-acentuacao.py continua reconhecendo `# noqa-acento` (rc=0)"
    - "Smoke + invariantes 14/14"
    - "Acentuação rc=0"
```

---

**Status:** PENDENTE
**Data criação:** 2026-05-21
**Modelo obrigatório:** claude-opus-4-7

---

## Solução

Adicionar em `pyproject.toml` na seção `[tool.ruff.lint]` (ou criar a seção se não existir):

```toml
[tool.ruff.lint]
# ... config existente ...
# Marcador customizado consumido pelo validar-acentuacao.py externo.
# Suprime warning "Invalid `# noqa` directive" do ruff.
external = ["noqa-acento"]
```

**Verificar primeiro** se `[tool.ruff.lint]` já existe em pyproject.toml. Se sim, adicionar apenas a linha `external = ["noqa-acento"]` preservando demais configs.

**Documentação ruff**: a opção `external` declara códigos/diretivas que vêm de ferramentas externas e devem ser ignorados pelo verificador de noqa.

## Critério binário

- [ ] `ruff check nyx/agent/output.py nyx/agent/lang_check.py nyx/proxy.py` sem warning Invalid noqa
- [ ] `validar-acentuacao.py --paths <mesmos arquivos>` continua rc=0
- [ ] Smoke + invariantes 14/14
- [ ] Acentuação rc=0 em pyproject.toml
