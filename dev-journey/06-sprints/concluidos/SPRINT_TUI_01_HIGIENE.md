## 0. SPEC (machine-readable)

```yaml
sprint:
  id: TUI-01
  title: "Higiene: silenciar logs, corrigir banner, formatar tool calls"
  touches:
    - path: nyx/cli.py
      reason: "Corrigir banner (\\033[0m literal), 100%%, remover basicConfig stdout"
    - path: nyx/agent/output.py
      reason: "Novo método render_tool_call (path compacto, sem dict cru)"
    - path: nyx/services/logging_service.py
      reason: "RotatingFileHandler para loggers nyx.*, nunca stdout"
    - path: run.sh
      reason: "Corrigir '100%%' (double-percent do printf do shell)"
    - path: nyx/agent/loop.py
      reason: "Substituir logger.info do loop por callbacks on_tool / on_iteration"
  n_to_n_pairs: []
  forbidden:
    - "Quebrar modo --headless (mantém stdout JSON puro)"
    - "Remover logs do projeto (só redirecionar pra arquivo)"
  tests:
    - cmd: "./run.sh --gauntlet --only rapido"
      timeout: 120
    - cmd: "manual: rodar ./run.sh, enviar 'Olá', verificar zero INFO no stdout"
      timeout: 60
  acceptance_criteria:
    - "Banner sem \\033[0m literal visível"
    - "Banner sem '%%' (mostra '100%' ou '100 por cento')"
    - "Zero INFO/DEBUG/WARNING no stdout durante REPL"
    - "Logs gravados em ~/.nyx/logs/nyx.log com rotação"
    - "Tool calls formatadas como 'read_file(path)' sem dict cru"
    - "Spinner 'pensando...' entre envio do prompt e primeiro token"
    - "Modo --headless continua emitindo JSON puro"
    - "Acentuação PT-BR correta em todas as strings"
```

---

# Sprint TUI-01 -- Higiene da interface

**Status:** CONCLUIDA (header corrigido em MASTER-CLEANUP-02 2026-05-20; presença em concluidos/ implica CONCLUIDA conforme convenção do projeto)
**Data:** 2026-04-17
**Prioridade:** ALTA
**Tipo:** Bugfix + Refactor
**Dependências:** nenhuma
**Desbloqueia:** TUI-02

---

## Problema / Contexto

Rodando `./run.sh` em 2026-04-17 o REPL mostra vários defeitos visuais:

1. Banner ASCII tem `\033[0m` LITERAL visível (não foi interpretado como reset ANSI)
2. Linha "100%% offline" (double-escape do `printf` do shell)
3. Logs `INFO` de `nyx.agent` e `nyx.tools` vazam no stdout durante iterações, intercalados com output real
4. Tool calls renderizadas como `read_file({'file_path': '/home/.../de)` -- dict Python cru, truncado no meio
5. Sem feedback visual enquanto o modelo pensa (primeira token demora, usuário não sabe se travou)

Referência visual está no plano master (mock 1). Esta sprint é o primeiro passo do redesign TUI estilo Claude Code CLI.

## Implementação

### Fase 1 -- Corrigir banner

- `nyx/cli.py:50-60`: refatorar `_build_banner` usando `rich.Panel` (já disponível via RichOutput) ou corrigir escapes ANSI. A ASCII art atual contém uma sequência `\033[0m` escrita como texto -- remover ou escapar.
- `run.sh`: localizar `printf` ou `echo` que gera "100%%". Se é string literal Python sendo passada pro shell via `printf`, escapar como `100%` (simples) no Python e ajustar o flow. Se é um `printf` puro no shell, usar `%%` é correto mas só pra `printf` -- se sai via `echo`, usar `%`.

### Fase 2 -- Roteamento de logging

- `nyx/services/logging_service.py`: definir `RotatingFileHandler` em `~/.nyx/logs/nyx.log` (5 arquivos, 1MB cada). Anexar ao logger `nyx` (que é parent de `nyx.agent`, `nyx.tools`, etc).
- `nyx/cli.py:32-37`: remover `logging.basicConfig(level=WARNING, ...)` que hoje envia tudo pra stderr/stdout. Substituir por import do `InternalLogging` service (já tem `logger.info("Logging rotacionado ativo")` de trás pra frente).
- Garantir que `nyx.cli` logger continua recebendo warnings em stderr (só pra erros de boot).

### Fase 3 -- Render de tool call

- `nyx/agent/output.py`: novo `render_tool_call(name: str, args: dict, project_root: str) -> None` que:
  - Extrai `file_path`/`path`/`command`/`pattern` (ordem de prioridade) como arg principal
  - Encurta path absoluto pra relativo se está dentro de `project_root`
  - Se relativo > 60 chars, substitui meio por `…` (ex: `dev-journey/…/SPRINT_ORDER.md`)
  - Formato: `   read_file(dev-journey/06-sprints/SPRINT_ORDER_MASTER.md)` com `` em accent color
- `nyx/cli.py:125-129`: substituir `on_tool` callback pelo novo render
- `nyx/agent/loop.py:262-339`: remover `logger.info("[tool] ...")` -- vira só arquivo, não stdout

### Fase 4 -- Spinner durante pensar

- `nyx/cli.py:344-345`: envolver `await agent.run(user_input)` com `with nyx_spinner("pensando..."):`. Spinner é context manager que já existe em `output.py:183`.
- Adicionar flag `_spinner_active` no callback `on_token`: na primeira chamada, se spinner ativo, para spinner antes de imprimir token. Evita sobrescrever primeiro caractere com `\r`.

## Verificação

```bash
./run.sh
# Esperado:
#  - Banner limpo, sem \033[0m literal
#  - "100% offline" (simples)
#  - Digitar "Olá"
#  - Ver "⋯ pensando..." enquanto modelo carrega
#  - Ver tool calls como " read_file(path)" sem dict cru
#  - Ver resposta final
#  - Nada de INFO/DEBUG na tela
# Ctrl+D
tail -30 ~/.nyx/logs/nyx.log
# Esperado: logs das iterações aqui
./run.sh --gauntlet --only rapido
# Esperado: 100%
./run.sh --headless <<< '{"type":"ping"}'
# Esperado: {"type":"pong","tools":34} em stdout puro
```

- [ ] Banner sem lixo ANSI
- [ ] Banner sem `%%`
- [ ] Zero logs INFO/DEBUG no stdout
- [ ] Tool calls com formato compacto
- [ ] Spinner aparece e desaparece corretamente
- [ ] Headless JSON intacto
- [ ] Gauntlet rapido passa

---

*"O simples é o último refúgio dos sofisticados." -- Steve Jobs*
