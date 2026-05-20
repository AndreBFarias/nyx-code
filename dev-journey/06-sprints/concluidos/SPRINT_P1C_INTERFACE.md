## 0. SPEC (machine-readable)

```yaml
sprint:
  id: P1-C
  title: "Interface: Streaming + Rich Output + Commands"
  touches:
    - path: nyx/agent/streaming.py
      reason: "Streaming de tokens do Ollama em tempo real (port da Luna)"
    - path: nyx/agent/output.py
      reason: "Formatação Rich com cores Nyx (port da Luna rich_output.py)"
    - path: nyx/agent/commands.py
      reason: "Slash commands: /explain, /plan, /test, /compact (port da Luna)"
  origin:
    primary:
      - "Luna/src/skills/code_agent/streaming.py (146 linhas)"
      - "Luna/src/skills/code_agent/rich_output.py"
      - "Luna/src/skills/code_agent/commands.py + command_registry.py"
    reference: "openclaud/src/commands/ (101 commands)"
  acceptance_criteria:
    - "Streaming mostra tokens um a um no terminal"
    - "Output com cores Nyx (#00D4AA accent, #E8E8E8 texto)"
    - "Code blocks com syntax highlighting via Rich"
    - "Commands: /help, /quit, /clear, /status, /explain, /plan, /test, /compact"
    - "Formatação de tool results (caminho, conteúdo, erro)"
```

---

# Sprint P1-C -- Interface

**Status:** CONCLUIDA (header corrigido em MASTER-CLEANUP-02 2026-05-20; presença em concluidos/ implica CONCLUIDA conforme convenção do projeto)
**Prioridade:** ALTA
**Tipo:** Port (Luna -> Nyx)
**Dependências:** P1-A
**Desbloqueia:** P1-F

---

## O que portar

### 1. `nyx/agent/streaming.py` (Luna: streaming.py, 146 linhas)

StreamingCollector que acumula tokens durante inferência.
Callback para exibir tokens em tempo real no terminal.

**Ajustes:** adaptar para httpx async streaming (proxy Nyx usa /v1/ API).

### 2. `nyx/agent/output.py` (Luna: rich_output.py)

Formatação visual com Rich:
- Cores Nyx (#00D4AA accent, #E8E8E8 primary, #2A2C39 bg)
- Syntax highlighting em code blocks
- Painel de tool results
- Barra de contexto (budget de tokens)
- Mensagens de erro formatadas

**Ajustes:** trocar cores da Luna (Dracula #BD93F9) para Nyx (#00D4AA).

### 3. `nyx/agent/commands.py` (Luna: commands.py + command_registry.py)

Comandos que moldam o prompt antes de enviar ao AgentLoop:
- `/explain <arquivo>` -- analisa e explica arquivo
- `/plan <descrição>` -- cria plano de implementação
- `/test <arquivo>` -- gera testes
- `/compact` -- resume sessão
- `/help` -- lista comandos
- `/quit` -- sai
- `/clear` -- limpa sessão
- `/status` -- mostra estado

**Ajustes:** mesclar command_registry.py em commands.py, remover dependências Luna.

## Testes Gauntlet (novos, adicionados ao nyx_gauntlet.py)

Fase: `interface` (nova, 5 testes)

| ID | Nome | Validação |
|----|------|-----------|
| IF-01 | Streaming importa | `from nyx.agent.streaming import StreamingCollector` sem erro |
| IF-02 | Output importa | `from nyx.agent.output import RichOutput` sem erro |
| IF-03 | Commands /help | `handle_command("/help")` retorna texto com lista de comandos |
| IF-04 | Commands /explain | `build_explain_prompt("README.md")` retorna prompt com "read_file" |
| IF-05 | Commands /plan | `build_plan_prompt("feature X")` retorna prompt com "list_files" |

## Verificação

- [ ] 5 testes de interface passam no Gauntlet
- [ ] `./run.sh --gauntlet --only interface` passa 100%
- [ ] Gauntlet completo continua passando 100%

---

*"A forma segue a função." -- Louis Sullivan*
