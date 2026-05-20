## 0. SPEC (machine-readable)

```yaml
sprint:
  id: TUI-FIX-03
  title: "Popup de slash commands abrindo automaticamente"
  touches:
    - path: nyx/cli.py
      reason: "Revisar keybindings que podem suprimir complete_while_typing"
    - path: nyx/agent/completer.py
      reason: "Garantir que yield de Completion inclui display, display_meta e start_position correto"
  n_to_n_pairs:
    - "Se completer detecta text.startswith('/') no buffer, PromptSession deve abrir popup sem precisar de Tab"
  forbidden:
    - "Exigir que usuário pressione Tab pra ver sugestões (dever ser automático)"
    - "Mostrar sugestões de path fora de contexto de slash"
    - "Quebrar Ctrl+J/Enter que já funcionam"
  tests:
    - cmd: "./run.sh --gauntlet --only p7"
      timeout: 60
    - cmd: "manual: ./run.sh, digitar '/', contar 5s sem teclar mais nada; popup deve aparecer"
      timeout: 30
  acceptance_criteria:
    - "Ao digitar '/' o popup aparece automaticamente em <1s"
    - "Popup mostra comandos em colunas (MULTI_COLUMN) com descrição"
    - "Digitar '/h' filtra pra /help, /hooks"
    - "Enter no popup aceita sugestão e envia comando"
    - "Esc fecha o popup sem enviar"
    - "Popup não aparece fora de contexto de slash (ex: texto normal)"
    - "Tab ainda funciona pra auto-complete manualmente"
```

---

# Sprint TUI-FIX-03 -- Popup slash funcionando (commander suggester)

**Status:** CONCLUIDA (header corrigido em MASTER-CLEANUP-02 2026-05-20; presença em concluidos/ implica CONCLUIDA conforme convenção do projeto)
**Data:** 2026-04-17
**Prioridade:** ALTA
**Tipo:** Fix
**Dependências:** --
**Desbloqueia:** --

---

## Problema / Contexto

Usuário: "commander sugester não rola". Ao digitar `/`, nenhum popup aparece. O `PromptSession` está configurado com:

```python
PromptSession(
    completer=create_completer(project_root),
    multiline=True,
    complete_while_typing=True,
    complete_style=CompleteStyle.MULTI_COLUMN,
    key_bindings=kb,
)
```

`completer.py` filtra com `text.lstrip().startswith("/")`. Então em teoria deveria funcionar. Três hipóteses:

1. **Custom keybindings capturando**: nossos keybindings para Enter/Ctrl+J podem estar interferindo com o event loop que dispara `complete_while_typing`
2. **start_position errado**: `Completion(...)` sem `start_position` adequado faz o popup renderizar mas invisível ou fora da tela
3. **MULTI_COLUMN exige muito espaço**: se o terminal for estreito, pode abortar silenciosamente

## Implementação

### Fase 1 -- Reproduzir

Script mínimo pra testar popup isolado (sem rodar o REPL inteiro):

```python
# scripts/debug_slash.py
import asyncio
from prompt_toolkit import PromptSession
from prompt_toolkit.shortcuts import CompleteStyle
from nyx.agent.completer import create_completer

async def main():
    session = PromptSession(
        completer=create_completer("/tmp"),
        complete_while_typing=True,
        complete_style=CompleteStyle.MULTI_COLUMN,
    )
    result = await session.prompt_async("teste> ")
    print(result)

asyncio.run(main())
```

Se popup funciona isolado → o problema está no REPL (keybinding ou multiline). Se não funciona isolado → problema no completer.

### Fase 2 -- Revisar completer.py

Em `nyx/agent/completer.py`, confirmar que cada `Completion` tem:
- `text`: o valor (ex: `/help`)
- `start_position`: negativo, ex: `-len(word)` pra substituir o que já foi digitado
- `display`: texto com formatação (FormattedText)
- `display_meta`: descrição

Suspeita: `start_position` pode estar faltando ou errado.

### Fase 3 -- Keybinding de compatibilidade

Se `multiline=True` está abafando o trigger, adicionar keybinding explícito no `/`:

```python
@kb.add('/')
def _slash(event):
    event.current_buffer.insert_text('/')
    event.current_buffer.start_completion(select_first=False)
```

### Fase 4 -- Validar MULTI_COLUMN

Se terminal <70 cols, trocar pra `COLUMN` (vertical simples) via fallback:

```python
cols = shutil.get_terminal_size().columns
style = CompleteStyle.MULTI_COLUMN if cols >= 100 else CompleteStyle.COLUMN
```

### Fase 5 -- display_meta PT-BR

Garantir que todos os commands têm descrição curta em português no completer (já implementado em `completer.py:43-50`, validar na execução).

## Verificação

```bash
# Teste isolado
./venv/bin/python scripts/debug_slash.py
# digitar /h -- ver popup

./run.sh
# digitar '/' -- popup automático com 40+ commands
# digitar 'h' -- filtra para /help, /hooks
# setas pra navegar, Enter pra aceitar
# Esc pra fechar

./run.sh --gauntlet --only p7
```

- [ ] Popup aparece ao digitar `/`
- [ ] Filtragem por prefixo funciona
- [ ] Descrição (`display_meta`) visível
- [ ] Seta/Enter/Esc funcionam
- [ ] Tab manual também funciona
- [ ] Em terminal estreito: fallback pra COLUMN
- [ ] Gauntlet p7 passa

---

*"A boa ferramenta antecipa o que o usuário quer." -- Don Norman*
