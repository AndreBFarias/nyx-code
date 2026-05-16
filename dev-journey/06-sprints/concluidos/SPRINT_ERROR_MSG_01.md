# SPRINT ERROR-MSG-01 — Auditoria e reescrita completa das mensagens de erro do REPL

## 0. SPEC (machine-readable)

```yaml
sprint:
  id: ERROR-MSG-01
  title: "Auditar e reescrever todas as mensagens de erro do REPL em PT-BR, cor vermelha (ANSI_ERROR_FG) e tom acionável"
  onda: 22
  bloco: 5
  prioridade: ALTA
  tipo: UX + Audit
  dependencias: [UX-DESIGN-01]
  desbloqueia: []

  touches:
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/agent/loop/_iteration.py
      reason: "Handlers de erro de tool call (timeout, permissão, falha de execução) usam strings cruas em inglês ou sem cor"
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/agent/commands/_dispatcher.py
      reason: "Mensagem 'Comando desconhecido' é genérica e não sugere alternativa — adicionar difflib.get_close_matches"
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/cli.py
      reason: "Handlers de boot (falha ao conectar Ollama, proxy offline, settings inválido) exibem traceback cru"
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/providers/ollama.py
      reason: "Timeouts e conexão recusada retornam exceção httpx sem tradução para usuário"
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/providers/base.py
      reason: "Superclasse de provider padroniza wrapper de erro de rede para todos os providers"
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/agent/output.py
      reason: "Adicionar helper print_error(msg, hint=None) que centraliza formatação vermelha + prefixo [erro]"
  creates:
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/dev-journey/07-reports/AUDIT_ERROR_MESSAGES_01.md
      reason: "Inventário de todas as ~40 mensagens antes/depois, tabela 3 colunas (local, antes, depois)"
  removes: []

  n_to_n_pairs:
    - descricao: "Token ANSI_ERROR_FG vive apenas em design_tokens.py; todos os módulos importam de lá"
      paths:
        - /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/themes/design_tokens.py
        - /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/agent/output.py
        - /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/cli.py
    - descricao: "Formato de mensagem: '[erro] <mensagem em PT-BR>. <verbo imperativo de ação>.' em TODOS os pontos"
      paths:
        - /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/agent/loop/_iteration.py
        - /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/agent/commands/_dispatcher.py
        - /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/cli.py
        - /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/providers/ollama.py

  forbidden:
    - "Engolir traceback em except genérico — em modo DEBUG mostrar tipo + linha relevante"
    - "Genericar mensagens ('algo deu errado', 'erro interno', 'falha inesperada')"
    - "Deixar qualquer mensagem em inglês — inclusive as que vêm de bibliotecas (envelopar na tradução)"
    - "Pular auditoria de providers/*.py alegando 'é externo'"
    - "Afrouxar teste trocando assertion por regex mais permissivo"
    - "Usar hex hardcoded (#FF3333 etc) fora de design_tokens.py"
    - "Adicionar emoji, menção a IA, print() fora de output.py/cli.py"

  tests:
    - cmd: "./run.sh --gauntlet --only interface"
      timeout: 300
      deve_passar: true
    - cmd: "python scripts/audit_error_messages.py"
      timeout: 30
      deve_passar: "inventário completo, zero inglês, zero mensagem sem cor"

  acceptance_criteria:
    - "Inventário AUDIT_ERROR_MESSAGES_01.md tem pelo menos 40 linhas de mensagens (antes/depois)"
    - "Toda mensagem nova: PT-BR com acentuação + ANSI_ERROR_FG + verbo imperativo de ação"
    - "Comando inválido `/xyz` sugere match próximo via difflib se score >= 0.6"
    - "Timeout de Ollama produz: 'Ollama não respondeu em 30s. Verifique se está rodando: systemctl status ollama'"
    - "Boot com proxy offline produz mensagem acionável com comando de diagnóstico"
    - "Gauntlet `--only interface` passa 100%"
    - "grep -rn 'error' nyx/ | grep -v '#' | grep -E '(failed|error|invalid|denied)' retorna zero matches em strings de usuário"
```

---

**Status:** PENDENTE
**Data criação:** 2026-04-19
**Modelo obrigatório:** claude-opus-4-7 (sem subagentes)

---

## Contexto do projeto (snapshot — não referência)

> **ADRs relevantes:**
> - ADR-001 Local First: tudo offline. Mensagens de erro precisam refletir isso (citar `systemctl`, caminhos locais, jamais URLs de suporte cloud).
> - ADR-004 Zero Emojis: em toda mensagem de erro.
> - ADR-005 Anonimato: sem menção a IA no texto exibido ao usuário.
> - ADR-006 PT-BR: acentuação obrigatória em todas as mensagens.
> - ADR-013 Integração Obrigatória: qualquer helper novo (`print_error`) entra via `output.py` e é consumido de todo ponto que hoje usa `print` cru.
> - ADR-014 Testes via Gauntlet: validação exclusivamente via `./run.sh --gauntlet`.
> - ADR-020 Testes via run.sh: scripts diretos proibidos.
> - ADR-023 Design System (UX-DESIGN-01): todos os tokens de cor vivem em `nyx/themes/design_tokens.py`. Esta sprint **depende** de `ANSI_ERROR_FG` já estar lá.
> - ADR-024 Render Layer: `print()` só em `cli.py` e `output.py`. Tools, services, providers, loop: proibido.
>
> **Estado do sistema:**
> - Python 3.10+, `qwen3:4b`, Ollama 11435, proxy 11436.
> - 34 tools, 47 commands, 10 services.
> - `TUI-FIX-06` já cobriu mensagens do sandbox; este escopo é maior: cobre tool errors, command errors, boot errors, network errors, parse errors.
> - Sprint anterior relevante: UX-DESIGN-01 (design system) — precisa estar CONCLUIDA antes desta.

---

## Problema

### Sintoma observável

Hoje o REPL exibe mensagens inconsistentes, em inglês, sem cor e sem ação sugerida. Exemplos colhidos em sessão real (2026-04-18):

```
Nyx: ReadTimeout
Nyx: Connection refused
Nyx: Command not found: /helpp
Nyx: failed to execute tool 'read_file': [Errno 2] No such file or directory
Nyx: Invalid argument
```

Todos os problemas acima:
1. Em inglês (viola ADR-006).
2. Sem cor (usuário não distingue erro de output normal).
3. Não informam o que fazer (não-acionável).
4. Expõem detalhe de biblioteca (`ReadTimeout`, `[Errno 2]`) sem tradução.

### Inventário inicial estimado

Grep exploratório revela ~40 pontos que exibem mensagens de erro diretamente ao usuário, distribuídos em:

- `nyx/agent/loop/_iteration.py`: ~12 mensagens (tool call failures, timeouts, permissão negada)
- `nyx/agent/commands/_dispatcher.py`: 3 mensagens (comando inválido, argumento faltando, comando sem permissão)
- `nyx/agent/commands/*.py`: ~15 mensagens (uma por comando que valida args)
- `nyx/cli.py`: ~6 mensagens (boot failures, signal handlers)
- `nyx/providers/ollama.py` + `base.py`: ~4 mensagens (timeout, conexão, parse)

Nenhum módulo usa um helper unificado — todos fazem `print(f"erro: {e}")` ou variantes.

---

## Solução proposta

1. Introduzir helper canônico `nyx/agent/output.py::print_error(msg: str, hint: str | None = None, debug_detail: str | None = None)`.
2. Reescrever toda mensagem em PT-BR, seguindo o formato:
   `[erro] <O QUE falhou>. <VERBO IMPERATIVO: o que fazer>.`
3. Aplicar cor `ANSI_ERROR_FG` (importado de `nyx/themes/design_tokens.py`).
4. Em modo DEBUG (`NYX_DEBUG=1`): acrescentar tipo da exceção + linha relevante.
5. Em `_dispatcher.py`: `difflib.get_close_matches` com cutoff 0.6 para sugerir comando próximo.
6. Criar inventário `AUDIT_ERROR_MESSAGES_01.md` com tabela `| local | antes | depois |`, mínimo 40 linhas.
7. Criar script `scripts/audit_error_messages.py` que falha CI se alguma string de erro estiver em inglês ou sem wrapper.

---

## Arquivos alvo (paths absolutos)

### `/home/andrefarias/Desenvolvimento/Nyx-Code/nyx/agent/output.py`

**Antes (trecho ilustrativo):**
```python
def print_stream(text: str) -> None:
    sys.stdout.write(text)
    sys.stdout.flush()
```

**Depois:**
```python
from nyx.ui.design_tokens import ANSI_ERROR_FG, ANSI_RESET, ANSI_DIM

def print_error(msg: str, hint: str | None = None, debug_detail: str | None = None) -> None:
    prefix = f"{ANSI_ERROR_FG}[erro]{ANSI_RESET}"
    body = f"{prefix} {msg}"
    if hint:
        body += f" {ANSI_DIM}{hint}{ANSI_RESET}"
    sys.stdout.write(body + "\n")
    if debug_detail and os.environ.get("NYX_DEBUG") == "1":
        sys.stdout.write(f"{ANSI_DIM}  detalhe: {debug_detail}{ANSI_RESET}\n")
    sys.stdout.flush()
```

### `/home/andrefarias/Desenvolvimento/Nyx-Code/nyx/agent/loop/_iteration.py`

**Antes:**
```python
except ToolExecutionError as e:
    print(f"tool error: {e}")
```

**Depois:**
```python
except ToolExecutionError as e:
    from nyx.agent.output import print_error
    print_error(
        f"Falha ao executar a ferramenta '{e.tool_name}'.",
        hint="Verifique permissões do arquivo ou rode com bypass se confiar na operação.",
        debug_detail=f"{type(e).__name__}: {e}",
    )
```

### `/home/andrefarias/Desenvolvimento/Nyx-Code/nyx/agent/commands/_dispatcher.py`

**Antes:**
```python
if cmd_name not in registry:
    print(f"Command not found: /{cmd_name}")
    return
```

**Depois:**
```python
if cmd_name not in registry:
    from difflib import get_close_matches
    from nyx.agent.output import print_error
    suggestion = get_close_matches(cmd_name, registry.keys(), n=1, cutoff=0.6)
    hint = f"Você quis dizer /{suggestion[0]}?" if suggestion else "Use /help para listar comandos disponíveis."
    print_error(f"Comando desconhecido: /{cmd_name}.", hint=hint)
    return
```

### `/home/andrefarias/Desenvolvimento/Nyx-Code/nyx/providers/ollama.py`

**Antes:**
```python
except httpx.ReadTimeout:
    raise RuntimeError("ReadTimeout")
```

**Depois:**
```python
except httpx.ReadTimeout as e:
    raise ProviderError(
        user_message="Ollama não respondeu em 30s.",
        hint="Verifique se está rodando: systemctl status ollama",
        cause=e,
    )
```

### `/home/andrefarias/Desenvolvimento/Nyx-Code/nyx/cli.py`

**Antes:**
```python
except ConnectionRefusedError:
    print("Proxy offline")
    sys.exit(1)
```

**Depois:**
```python
except ConnectionRefusedError as e:
    from nyx.agent.output import print_error
    print_error(
        "Proxy de inferência offline na porta 11436.",
        hint="Reinicie com ./run.sh ou verifique logs em ~/.nyx/logs/proxy.log",
        debug_detail=str(e),
    )
    sys.exit(1)
```

### `/home/andrefarias/Desenvolvimento/Nyx-Code/dev-journey/07-reports/AUDIT_ERROR_MESSAGES_01.md`

Inventário em tabela markdown com três colunas. Mínimo 40 linhas de dados (sem contar cabeçalho).

### `/home/andrefarias/Desenvolvimento/Nyx-Code/scripts/audit_error_messages.py`

Script que percorre `nyx/` procurando por strings com padrões suspeitos (`error`, `failed`, `invalid`, `denied`, `not found` em inglês) e falha se encontrar em qualquer arquivo que não seja teste ou comentário.

**Mudanças:** bullets resumidos
- Helper `print_error` centralizado com hint + debug_detail
- `ProviderError` novo em `providers/base.py` com tradução automática para mensagem PT-BR
- Todas as ~40 mensagens reescritas
- Script de auditoria incorporado ao Gauntlet (fase `interface`)

---

## Diff esperado (resumo)

```
+ 2 arquivos criados (inventário + script de auditoria)
~ 6 arquivos modificados (output, iteration, dispatcher, cli, ollama, base)
- 0 arquivos removidos
+ ~250 linhas líquidas (inventário pesa)
```

---

## Comandos de verificação (literais, copy-paste)

```bash
# 1. Validação estática
python -m ruff check nyx/

# 2. Auditoria de mensagens
python scripts/audit_error_messages.py
# Esperado: "OK: 0 mensagens em inglês, 0 sem wrapper, 40+ traduzidas"

# 3. Gauntlet
./run.sh --gauntlet --only interface

# 4. Manual: disparar cada tipo de erro
./run.sh
# No REPL:
#   /xyz                        -> deve sugerir comando próximo
#   (simular Ollama desligado)  -> deve imprimir mensagem acionável vermelha
#   /read_file /nao-existe      -> deve imprimir erro de tool em PT-BR
```

---

## Critério binário de aceite (IA executora)

- [ ] `AUDIT_ERROR_MESSAGES_01.md` tem >= 40 linhas de inventário
- [ ] Toda mensagem nova em PT-BR com acentuação correta
- [ ] Toda mensagem com `ANSI_ERROR_FG` via helper `print_error`
- [ ] `/xyz` sugere match próximo quando score >= 0.6
- [ ] `scripts/audit_error_messages.py` retorna exit 0
- [ ] Gauntlet `--only interface` passa 100%
- [ ] `ruff` não reclama
- [ ] Nenhuma violação de `forbidden[]`
- [ ] Sprint movida para `concluidos/` com commit `feat: auditoria e reescrita das mensagens de erro do REPL`
- [ ] SPRINT_ORDER_MASTER marca CONCLUIDA com hash

---

## Guardrails anti-engodo (obrigatórios)

- Não marcar concluída sem rodar cada cenário manual listado (traceback real de Ollama desligado, comando inválido com match, tool com path inexistente).
- Não "afrouxar" o script de auditoria para evitar falhas — se falhou, é porque a tradução está incompleta.
- Não envolver TUDO em `try/except Exception` para não ter que traduzir — causa silenciamento (GUIDE.md §3).
- Se descobrir que uma mensagem vem de lib externa impossível de interceptar: registrar em `riscos` + nova sprint, não deixar passar.

---

## Catálogo de gambiarras proibidas (20 padrões)

Ver `dev-journey/08-templates/SPRINT_TEMPLATE_V2.md` seção "Catálogo de gambiarras proibidas".

---

## Proof-of-work obrigatório (4 passos)

```bash
# PASSO 1 — snapshot ANTES
bash scripts/sprint_invariants.sh > /tmp/inv_before.txt 2>&1
FAIL_BEFORE=$(grep -c "^\[FAIL\]" /tmp/inv_before.txt)
echo "FAIL inicial: $FAIL_BEFORE"

# PASSO 2 — implementação
#   consultar GAMBIARRAS_POR_SPRINT.md seção ERROR-MSG-01

# PASSO 3 — snapshot DEPOIS
bash scripts/sprint_invariants.sh > /tmp/inv_after.txt 2>&1
FAIL_AFTER=$(grep -c "^\[FAIL\]" /tmp/inv_after.txt)
echo "FAIL final: $FAIL_AFTER"

# PASSO 4 — regras binárias
diff /tmp/inv_before.txt /tmp/inv_after.txt
```

**Se o output acima não for colado integralmente: sprint é rejeitada.**

---

## Gambiarras específicas desta sprint

1. **Afrouxar o teste trocando assertion.** Mudar `assert "[erro]" in stdout` para `assert "erro" in stdout.lower()` para aceitar mensagem crua. Proibido — quebra o contrato de cor + prefixo.
2. **Deixar inglês "porque é da lib".** Mensagens de `httpx`/`urllib3` são envelopadas em `ProviderError`. Nenhuma string em inglês chega ao usuário.
3. **Pular auditoria de `providers/*.py`.** Providers são a principal fonte de ReadTimeout/ConnectionRefused. Ignorar = 30% do escopo não entregue.
4. **Fazer wrapper genérico que engole detalhe.** `print_error` com `hint=None` em tudo. Cada erro precisa de hint específico e acionável.
5. **Usar hex hardcoded em vez de token.** `\033[31m` em vez de `ANSI_ERROR_FG`. Quebra o design system.
6. **Mensagem genérica "algo deu errado".** Proibido — cada erro tem causa identificável, diga qual.

---

## Validação humana (checklist do usuário)

```bash
cd /home/andrefarias/Desenvolvimento/Nyx-Code

# 1. Diff do commit
git log --oneline -1
git show --stat HEAD

# 2. Rodar auditoria
python scripts/audit_error_messages.py
# saída esperada: OK com contagem >= 40

# 3. Cenário manual — comando inválido
./run.sh
# digitar: /helpp
# esperado: linha vermelha "[erro] Comando desconhecido: /helpp. Você quis dizer /help?"

# 4. Cenário manual — Ollama desligado
sudo systemctl stop ollama
./run.sh
# esperado: "[erro] Ollama não respondeu em 30s. Verifique se está rodando: systemctl status ollama"
sudo systemctl start ollama

# 5. Validar arquivos movidos
ls dev-journey/06-sprints/concluidos/SPRINT_ERROR_MSG_01.md
ls dev-journey/06-sprints/producao/SPRINT_ERROR_MSG_01.md 2>&1 | grep -q "No such" && echo OK
```

---

## Riscos

| Risco | Mitigação |
|-------|-----------|
| Bibliotecas externas (httpx, anyio) emitem warnings no stderr sem passar pelos handlers | Configurar `logging.captureWarnings(True)` e filtro no root logger redirecionando para `print_error` |
| Inventário de 40 linhas pode crescer para 60+ durante execução | Aceitar expansão; floor é 40, não teto |
| Modo DEBUG vazando em produção | Variável `NYX_DEBUG` opt-in, default off; documentar em `AUDIT_ERROR_MESSAGES_01.md` |
| `difflib.get_close_matches` sugere comando com permissão elevada para usuário sem permissão | Filtrar sugestões pelo nível de permissão do usuário antes de exibir |
| Token `ANSI_ERROR_FG` ainda não existe se UX-DESIGN-01 atrasar | Bloquear sprint; não inventar constante paralela |

---

*"A clareza no aviso é o primeiro ato de respeito ao outro." -- Epicteto (adaptado)*
