## 0. SPEC (machine-readable)

```yaml
sprint:
  id: P7-A
  title: "prompt-toolkit base -- histórico, input multilinha, keybindings"
  touches:
    - path: nyx/cli.py
      reason: "Trocar input() por prompt-toolkit"
    - path: requirements.txt
      reason: "Adicionar prompt-toolkit"
    - path: scripts/gauntlet/nyx_gauntlet.py
      reason: "2 testes novos"
  origin:
    primary: "openclaud/src/cli/"
    secondary: "Luna/src/skills/code_agent/cli_completer.py"
  tests:
    - cmd: "./run.sh --gauntlet --only p7_tui"
      timeout: 30
  acceptance_criteria:
    - "Input com prompt-toolkit em vez de input()"
    - "Histórico de comandos com setas (up/down)"
    - "Input multilinha com Shift+Enter ou barra invertida"
    - "Keybindings vi/emacs selecionáveis"
    - "Fallback para input() se prompt-toolkit indisponível"
```

---

# Sprint P7-A -- prompt-toolkit base

**Status:** CONCLUIDA (header corrigido em MASTER-CLEANUP-02 2026-05-20; presença em concluidos/ implica CONCLUIDA conforme convenção do projeto)
**Data:** 2026-04-05
**Prioridade:** BAIXA
**Tipo:** Feature
**Dependências:** P5-D
**Desbloqueia:** P7-B

---

## Implementação

### Trocar input() por prompt-toolkit
- `from prompt_toolkit import PromptSession`
- `session = PromptSession(history=FileHistory('~/.nyx/history'))`
- Manter fallback para `input()` se importação falhar
- Histórico persistido em `~/.nyx/history`

### Input multilinha
- `Shift+Enter` ou `\` no final da linha continua
- `Enter` sozinho submete

### Keybindings
- Default: emacs
- Configurável via `/config keybindings vi`

### Testes Gauntlet

| ID | Nome | Validação |
|----|------|-----------|
| P7T-01 | prompt-toolkit importa | Import funciona ou fallback ok |
| P7T-02 | History path existe | `~/.nyx/history` acessível |

## Integração

- prompt-toolkit integrado diretamente no cli.py (substitui input())
- Nenhum arquivo solto -- tudo dentro do REPL existente
- Gauntlet valida via `./run.sh --gauntlet --only p7_tui`

## Verificação

- [ ] prompt-toolkit instalado no venv
- [ ] Setas up/down navegam histórico
- [ ] Fallback para input() funciona
- [ ] `./run.sh --gauntlet --only p7_tui` passa 100%

---

*"A interface é o produto." -- Jef Raskin*
