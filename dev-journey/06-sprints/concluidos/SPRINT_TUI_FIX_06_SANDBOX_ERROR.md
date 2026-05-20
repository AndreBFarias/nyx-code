## 0. SPEC (machine-readable)

```yaml
sprint:
  id: TUI-FIX-06
  title: "Mensagens de sandbox claras (validate_path em PT-BR amigável)"
  touches:
    - path: nyx/agent/tools/base.py
      reason: "validate_path retorna ValueError com mensagem mais útil"
    - path: nyx/agent/output.py
      reason: "render_tool_result detecta 'Acesso negado' e formata diferente (cor vermelha/âmbar)"
  n_to_n_pairs:
    - "Se validate_path muda formato da mensagem, render_tool_result precisa ajustar parser"
  forbidden:
    - "Remover a validação em si (segurança)"
    - "Truncar mensagem a ponto de esconder o motivo"
    - "Expor paths absolutos sensíveis em mensagens (ok mostrar /home/user/X, não ok mostrar /etc/shadow)"
  tests:
    - cmd: "./run.sh --gauntlet --only tools"
      timeout: 60
    - cmd: "manual: pedir 'lê /home/andrefarias/Desenvolvimento/ArcaneTab/README.md'; ver mensagem clara"
      timeout: 30
  acceptance_criteria:
    - "Quando tool é bloqueada por validate_path, mensagem é 'Fora do projeto Nyx-Code: <path>. Para acessar outro projeto, inicie Nyx lá.'"
    - "render_tool_result colore mensagens de erro em âmbar/vermelho"
    - "Tool result com sucesso fica dim (como hoje)"
    - "Mensagem não é truncada a ponto de cortar o motivo"
    - "Logger registra erro completo (full path) para debug; usuário vê versão limpa"
```

---

# Sprint TUI-FIX-06 -- Erros de sandbox em PT-BR amigável

**Status:** CONCLUIDA (header corrigido em MASTER-CLEANUP-02 2026-05-20; presença em concluidos/ implica CONCLUIDA conforme convenção do projeto)
**Data:** 2026-04-17
**Prioridade:** BAIXA
**Tipo:** UX + Refinamento
**Dependências:** --
**Desbloqueia:** --

---

## Problema / Contexto

Screenshot 10 mostra o seguinte resultado de tool call:

```
 read_file(/home/andrefarias/Desenvolvimento/ArcaneTab/README.md)
  └─ Acesso negado: '/home/andrefarias/Desenvolvimento/ArcaneTab/README.md' resolve …
```

A mensagem está truncada com `…` em um ponto que esconde a explicação real. Usuário não entende se é:
- Arquivo não existe?
- Problema de permissão do sistema?
- Sandbox do Nyx?

Na verdade é **sandbox do Nyx** (validate_path em `nyx/agent/tools/base.py:33-69`). A mensagem atual:

```python
raise ValueError(
    f"Acesso negado: '{file_path}' resolve para '{resolved}', "
    f"fora das raízes permitidas ({', '.join(str(r) for r in allowed)})"
)
```

Muito longa, truncada na render, e não explica o que o usuário pode fazer.

## Implementação

### Fase 1 -- Mensagem reformulada

Em `base.py::validate_path`, trocar a mensagem:

```python
raise ValueError(
    f"Fora do projeto {Path(project_root).name}: '{file_path}'. "
    f"Para acessar outro projeto, inicie o Nyx lá."
)
```

Curto, claro, acionável. O path absoluto completo fica no log via `logger.warning` (já existe na linha 65).

### Fase 2 -- Colorir erro no render

Em `nyx/agent/output.py::render_tool_result`:

```python
ERROR_PREFIXES = ("Fora do projeto", "Erro:", "Falha", "Acesso negado", "Bloqueado")

def render_tool_result(result: str, max_chars: int = 100) -> None:
    line = result.split("\n")[0][:max_chars]
    if any(line.startswith(p) for p in ERROR_PREFIXES):
        # Erro: âmbar/amarelo
        print(f"    {AMBER}└─ {line}{NC}")
    else:
        # Sucesso: dim
        print(f"    {DIM}└─ {line}{NC}")
```

Definir `AMBER = "\033[38;2;255;176;0m"` em output.py.

### Fase 3 -- Aumentar max_chars

O truncamento em `…` atual corta em 80 chars. Com a nova mensagem mais concisa, 100 chars deve caber sempre.

### Fase 4 -- Adicionar render_tool_success vs render_tool_error

Refatorar internamente: `_render_tool_line(result, level)` onde level ∈ {"ok", "warn", "error"}. Mantém a API pública de `render_tool_result(result)` detectando automaticamente.

## Verificação

```bash
./run.sh
# digitar: "lê /home/andrefarias/Desenvolvimento/ArcaneTab/README.md"
# ver: └─ Fora do projeto Nyx-Code: '/home/...'. Para acessar outro projeto, inicie o Nyx lá.
# em cor âmbar

# digitar: "lista arquivos .py em nyx/agent"
# ver: └─ 50 arquivos em nyx/agent em dim (como antes)

./run.sh --gauntlet --only tools
```

- [ ] Mensagem curta e clara
- [ ] Path absoluto só no log
- [ ] Erro em âmbar, sucesso em dim
- [ ] max_chars não corta a mensagem útil
- [ ] Gauntlet tools passa

---

*"A clareza é a cortesia do filósofo." -- Ortega y Gasset*
