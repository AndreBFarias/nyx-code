# SPRINT ONBOARDING-01 — Tutorial de primeiro `./run.sh` + `/config setup` interativo

## 0. SPEC (machine-readable)

```yaml
sprint:
  id: ONBOARDING-01
  title: "Tutorial inline de 30s no primeiro ./run.sh + comando /config setup interativo gravando ~/.nyx/config.toml"
  onda: 22
  bloco: 7b
  prioridade: MÉDIA
  tipo: Feature
  dependencias: [SESSION-RESUME-01, HELP-EXAMPLES-01]
  desbloqueia: []

  touches:
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/cli.py
      reason: "Detectar ausência de ~/.nyx/.first_run_done; invocar tutorial antes do REPL; respeitar --skip-onboarding"
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/agent/commands/system.py
      reason: "Adicionar cmd_config_setup (perguntas interativas gravando config.toml)"
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/config/settings.py
      reason: "Integrar leitura de ~/.nyx/config.toml quando existir (mantém precedência env > toml > defaults)"
  creates:
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/agent/onboarding.py
      reason: "Módulo dedicado com run_first_time_tutorial(); 5 steps + pausas com timeout"
  removes: []

  n_to_n_pairs:
    - descricao: "Caminho ~/.nyx/.first_run_done é lido em cli.py e escrito em onboarding.py — constante compartilhada"
      paths:
        - /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/cli.py
        - /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/agent/onboarding.py
    - descricao: "Precedência de config (env > toml > defaults) vive em settings.py; /config setup escreve o toml que settings.py lê"
      paths:
        - /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/config/settings.py
        - /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/agent/commands/system.py

  forbidden:
    - "Tutorial bloqueia indefinidamente sem stdin (usar input com timeout de 60s; após isso, auto-skip e tocar .first_run_done)"
    - "Escrever config.toml sem backup (~/.nyx/config.toml.bak) se já existe"
    - "Tutorial aparece duas vezes (idempotência via .first_run_done)"
    - "Tutorial bloqueia quando stdin não é tty (pipe, CI): auto-skip"
    - "Adicionar emoji, print() fora de cli.py/output.py, menção a IA"
    - "Path absoluto hardcoded (usar Path.home())"
    - "Escrita não-atômica em config.toml (usar .tmp + os.replace)"

  tests:
    - cmd: "./run.sh --gauntlet --only interface"
      timeout: 300
      deve_passar: true
    - cmd: "rm -rf /tmp/nyx_test_home && NYX_HOME=/tmp/nyx_test_home ./run.sh --skip-onboarding"
      timeout: 60
      deve_passar: "não executa tutorial"

  acceptance_criteria:
    - "Primeira `./run.sh` em ~/.nyx/ limpo exibe tutorial (5 steps, 1 pausa cada)"
    - "Segunda `./run.sh` NÃO exibe tutorial (idempotência via .first_run_done)"
    - "Flag `--skip-onboarding` pula tutorial e toca .first_run_done"
    - "Tutorial em stdin não-tty faz auto-skip sem travar"
    - "Pausa 'pressione Enter' tem timeout de 60s; após isso auto-continua"
    - "`/config setup` grava ~/.nyx/config.toml válido (parseável por tomllib)"
    - "Se config.toml existir, gerar backup .bak antes de sobrescrever"
    - "Escrita atômica (.tmp + os.replace) em config.toml"
    - "Precedência env > toml > defaults respeitada em settings.py"
    - "Acentuação PT-BR correta em todo texto do tutorial"
    - "Gauntlet `--only interface` passa 100%"
```

---

**Status:** PENDENTE
**Data criação:** 2026-04-19
**Modelo obrigatório:** claude-opus-4-7 (sem subagentes)

---

## Contexto do projeto (snapshot — não referência)

> **ADRs relevantes:**
> - ADR-001 Local First: config fica em `~/.nyx/`, não em remoto.
> - ADR-004 Zero Emojis: texto do tutorial limpo.
> - ADR-005 Anonimato: tutorial apresenta "Nyx", nunca menciona IA externa.
> - ADR-006 PT-BR: todo o tutorial em português.
> - ADR-013 Integração Obrigatória: `cmd_config_setup` entra no registry via `@nyx_command`.
> - ADR-014 Testes via Gauntlet.
> - ADR-024 Render Layer: prints do tutorial vão via `output.py` (exceto prompts interativos que usam `input()` direto em cli.py).
>
> **Estado do sistema:**
> - 34 tools, 47 commands, 10 services.
> - `~/.nyx/` hoje contém: `memory/`, `sessions/`, `pastes/`, `image_index.json`.
> - SESSION-RESUME-01 (pré-requisito) já estabelece infra de sessões indexadas; ONBOARDING-01 reutiliza mensageria (`print_dim`, prompt `[s/N]` etc).
> - HELP-EXAMPLES-01 (pré-requisito) garante que `/help config` mostrará os examples de `config setup` que esta sprint adiciona.

---

## Problema

### Sintoma observável

Primeiro uso do Nyx numa máquina nova:

```
$ ./run.sh
[proxy up] [ollama up]
Nyx>
```

Usuário fica encarando um prompt vazio. Não sabe:
- Que pode digitar linguagem natural.
- Que existem slash commands.
- Que pode usar bypass com atalho específico.
- Que a memória persiste entre sessões.
- Que há comandos como `/help` com exemplos.

Taxa de abandono em primeiro contato é alta. Também: `~/.nyx/config.toml` não existe; toda configuração exige editar env vars ou `settings.py` na mão.

### Requisitos funcionais

1. **Tutorial one-shot**: 5 steps curtos, cada um com uma pausa manual. Ao final, toca `.first_run_done`.
2. **Idempotência**: segunda execução não repete.
3. **Não-bloqueante**: stdin fechado ou timeout de 60s → auto-skip.
4. **Opt-out**: `--skip-onboarding` pula direto.
5. **`/config setup`**: fluxo interativo para gerar `~/.nyx/config.toml` inicial ou reescrever.

---

## Solução proposta

1. **`nyx/agent/onboarding.py`** — módulo novo com `run_first_time_tutorial()`:
   - Step 1: Banner de boas-vindas + identidade Nyx.
   - Step 2: Prompt livre (explicar que linguagem natural funciona).
   - Step 3: Slash commands (mostrar `/help`).
   - Step 4: Bypass (explicar atalho de permissão elevada).
   - Step 5: Memória persistente (explicar `/resume` e `~/.nyx/sessions`).
   - Entre steps: `input("pressione Enter para continuar...")` com timeout 60s.
   - Ao final: `touch ~/.nyx/.first_run_done`.

2. **`cli.py`** — detecção + orquestração:
   - Ler `args.skip_onboarding`.
   - Se não ativo e `.first_run_done` ausente e stdin é tty: rodar tutorial.
   - Se stdin não é tty ou flag ativa: marcar `.first_run_done` silenciosamente.

3. **`cmd_config_setup`** — perguntas sequenciais:
   - Modelo preferido (default `qwen3:4b`).
   - Tema (default `paleta_d`).
   - Bypass default (`cauteloso` | `moderado` | `ousado`).
   - Limite de contexto em turnos (default 40).
   - Gravar `~/.nyx/config.toml` (com backup `.bak` se existir).

4. **`settings.py`** — carregar `~/.nyx/config.toml` com precedência: env > toml > defaults.

---

## Arquivos alvo (paths absolutos)

### `/home/andrefarias/Desenvolvimento/Nyx-Code/nyx/agent/onboarding.py`

**Antes:** não existe.

**Depois:**
```python
"""Tutorial de primeiro uso. Invocado uma vez por instalação."""
from __future__ import annotations

import signal
import sys
from pathlib import Path

from nyx.agent.output import print_info, print_dim, print_header

NYX_HOME = Path.home() / ".nyx"
FIRST_RUN_MARKER = NYX_HOME / ".first_run_done"

STEPS = [
    ("Bem-vinda ao Nyx", "Sou Nyx. Codificadora local, 100% offline, sem telemetria."),
    ("Prompt livre", "Digite qualquer pergunta ou tarefa em português. Eu respondo e executo."),
    ("Slash commands", "Comandos começam com /. Exemplo: /help ou /status. Use /help <cmd> para exemplos."),
    ("Bypass de permissão", "Quando precisar acesso elevado, confirme no prompt. Sessão lembra escolhas."),
    ("Memória persistente", "Suas sessões ficam em ~/.nyx/sessions/. Use /resume para retomar a última."),
]

def _timed_input(prompt: str, timeout: int = 60) -> str | None:
    def _handler(signum, frame): raise TimeoutError
    old = signal.signal(signal.SIGALRM, _handler)
    signal.alarm(timeout)
    try:
        return input(prompt)
    except (TimeoutError, EOFError):
        return None
    finally:
        signal.alarm(0)
        signal.signal(signal.SIGALRM, old)

def run_first_time_tutorial() -> None:
    if not sys.stdin.isatty():
        _mark_done()
        return
    print_header("Tutorial rápido -- 30 segundos")
    for title, body in STEPS:
        print_info(f"-- {title} --")
        print_dim(body)
        resposta = _timed_input("pressione Enter para continuar (ou aguarde 60s)...")
        if resposta is None:
            print_dim("tempo esgotado, seguindo.")
    print_info("Pronto. Qualquer dúvida: /help. Vamos ao trabalho.")
    _mark_done()

def _mark_done() -> None:
    NYX_HOME.mkdir(parents=True, exist_ok=True)
    FIRST_RUN_MARKER.touch(exist_ok=True)

def should_run_tutorial(skip_flag: bool) -> bool:
    if skip_flag:
        return False
    if FIRST_RUN_MARKER.exists():
        return False
    return sys.stdin.isatty()
```

### `/home/andrefarias/Desenvolvimento/Nyx-Code/nyx/cli.py`

**Antes (trecho):**
```python
def main() -> None:
    args = parser.parse_args()
    boot(args)
```

**Depois:**
```python
def main() -> None:
    args = parser.parse_args()
    from nyx.agent.onboarding import should_run_tutorial, run_first_time_tutorial, _mark_done
    if should_run_tutorial(args.skip_onboarding):
        run_first_time_tutorial()
    elif args.skip_onboarding:
        _mark_done()
    boot(args)
```

E no parser adicionar:
```python
parser.add_argument("--skip-onboarding", action="store_true", help="Pula tutorial de primeiro uso")
```

### `/home/andrefarias/Desenvolvimento/Nyx-Code/nyx/agent/commands/system.py`

Adicionar:
```python
@nyx_command(
    name="config",
    description="Mostra ou configura Nyx.",
    examples=[
        "/config",
        "/config setup",
        "/config get tema",
    ],
)
def cmd_config(args, ctx):
    if args and args[0] == "setup":
        return cmd_config_setup(args[1:], ctx)
    # ... comportamento existente de exibir config

def cmd_config_setup(args, ctx):
    import tomllib
    from nyx.agent.output import print_info, print_error

    config_path = Path.home() / ".nyx" / "config.toml"
    if config_path.exists():
        backup = config_path.with_suffix(".toml.bak")
        backup.write_bytes(config_path.read_bytes())
        print_info(f"Backup salvo em {backup}")

    modelo = input("Modelo preferido [qwen3:4b]: ").strip() or "qwen3:4b"
    tema = input("Tema (paleta_a/b/c/d) [paleta_d]: ").strip() or "paleta_d"
    bypass = input("Bypass default (cauteloso/moderado/ousado) [cauteloso]: ").strip() or "cauteloso"
    try:
        ctx_limit = int(input("Limite de contexto em turnos [40]: ").strip() or "40")
    except ValueError:
        print_error("Valor inválido.", hint="Deve ser inteiro. Usando 40.")
        ctx_limit = 40

    content = (
        f'# Configuração Nyx gerada via /config setup\n'
        f'modelo = "{modelo}"\n'
        f'tema = "{tema}"\n'
        f'bypass = "{bypass}"\n'
        f'ctx_limit = {ctx_limit}\n'
    )
    tmp = config_path.with_suffix(".toml.tmp")
    tmp.write_text(content, encoding="utf-8")
    tmp.replace(config_path)
    print_info(f"Configuração salva em {config_path}")
    return CommandResult.ok()
```

### `/home/andrefarias/Desenvolvimento/Nyx-Code/nyx/config/settings.py`

**Antes (trecho):**
```python
def load_settings() -> NyxSettings:
    return NyxSettings(
        model=os.getenv("NYX_MODEL", defaults.MODEL),
        ...
    )
```

**Depois:**
```python
def load_settings() -> NyxSettings:
    toml_cfg = _load_toml_if_exists()
    return NyxSettings(
        model=os.getenv("NYX_MODEL") or toml_cfg.get("modelo") or defaults.MODEL,
        theme=os.getenv("NYX_THEME") or toml_cfg.get("tema") or defaults.THEME,
        bypass=os.getenv("NYX_BYPASS") or toml_cfg.get("bypass") or defaults.BYPASS,
        ctx_limit=int(os.getenv("NYX_CTX_LIMIT") or toml_cfg.get("ctx_limit") or defaults.CTX_LIMIT),
    )

def _load_toml_if_exists() -> dict:
    import tomllib
    path = Path.home() / ".nyx" / "config.toml"
    if not path.exists():
        return {}
    try:
        with path.open("rb") as f:
            return tomllib.load(f)
    except Exception as e:
        from nyx.agent.output import print_error
        print_error(
            f"~/.nyx/config.toml inválido.",
            hint="Rode /config setup para regenerar. Usando defaults por ora.",
            debug_detail=str(e),
        )
        return {}
```

---

## Diff esperado (resumo)

```
+ 1 arquivo criado (onboarding.py)
~ 3 arquivos modificados (cli, system.py, settings.py)
- 0 arquivos removidos
+ ~240 linhas líquidas
```

---

## Comandos de verificação (literais, copy-paste)

```bash
# 1. Validação estática
python -m ruff check nyx/

# 2. Cenário: primeira execução
rm -f ~/.nyx/.first_run_done
./run.sh
# esperado: tutorial aparece; seguir até o fim; REPL abre
# Ctrl+D

# 3. Cenário: segunda execução (idempotência)
./run.sh
# esperado: NÃO aparece tutorial; REPL abre direto
# Ctrl+D

# 4. Cenário: flag skip
rm -f ~/.nyx/.first_run_done
./run.sh --skip-onboarding
# esperado: sem tutorial; .first_run_done tocado
test -f ~/.nyx/.first_run_done && echo "OK"
# Ctrl+D

# 5. Cenário: stdin não-tty
rm -f ~/.nyx/.first_run_done
echo "" | ./run.sh
# esperado: auto-skip; .first_run_done tocado

# 6. Cenário: /config setup
./run.sh
# No REPL: /config setup
# responder: qwen3:4b / paleta_d / cauteloso / 40
test -f ~/.nyx/config.toml && echo "OK"
python -c "import tomllib; print(tomllib.load(open(f'{__import__(\"pathlib\").Path.home()}/.nyx/config.toml','rb')))"

# 7. Cenário: backup
./run.sh
# /config setup (de novo)
test -f ~/.nyx/config.toml.bak && echo "OK"

# 8. Gauntlet
./run.sh --gauntlet --only interface
```

---

## Critério binário de aceite (IA executora)

- [ ] Primeira execução com `~/.nyx/` limpo exibe tutorial de 5 steps
- [ ] Segunda execução NÃO exibe tutorial
- [ ] `--skip-onboarding` pula e toca `.first_run_done`
- [ ] stdin não-tty faz auto-skip
- [ ] Timeout de 60s na pausa funciona (teste: não pressionar Enter e esperar)
- [ ] `/config setup` grava toml válido parseável por `tomllib`
- [ ] Backup `.bak` gerado quando toml já existia
- [ ] Escrita atômica (`.tmp + replace`)
- [ ] Precedência env > toml > defaults respeitada
- [ ] Acentuação PT-BR em todo texto
- [ ] Gauntlet `--only interface` passa 100%
- [ ] `ruff` não reclama
- [ ] Sprint movida para `concluidos/` com commit `feat: tutorial de primeiro uso e /config setup interativo`
- [ ] Nenhuma violação de `forbidden[]`

---

## Guardrails anti-engodo (obrigatórios)

- Não marcar concluída sem testar o cenário stdin não-tty (`echo "" | ./run.sh`).
- Não marcar concluída sem testar o timeout de 60s (pressionar nada, esperar).
- Não "simplificar" removendo o backup `.bak`.
- Se `signal.SIGALRM` não funciona no ambiente de teste (Windows): aceitar fallback com `select.select` em stdin, mas manter contrato de timeout.

---

## Catálogo de gambiarras proibidas (20 padrões)

Ver `dev-journey/08-templates/SPRINT_TEMPLATE_V2.md` seção "Catálogo de gambiarras proibidas".

---

## Proof-of-work obrigatório (4 passos)

```bash
# PASSO 1 — snapshot ANTES
bash scripts/sprint_invariants.sh > /tmp/inv_before.txt 2>&1
FAIL_BEFORE=$(grep -c "^\[FAIL\]" /tmp/inv_before.txt)

# PASSO 2 — implementação
#   consultar GAMBIARRAS_POR_SPRINT.md seção ONBOARDING-01

# PASSO 3 — snapshot DEPOIS
bash scripts/sprint_invariants.sh > /tmp/inv_after.txt 2>&1
FAIL_AFTER=$(grep -c "^\[FAIL\]" /tmp/inv_after.txt)

# PASSO 4 — regras binárias
diff /tmp/inv_before.txt /tmp/inv_after.txt

# Extra obrigatório: colar output de todos os 8 cenários da seção "Comandos de verificação"
```

**Formato obrigatório:** ver SPRINT_TEMPLATE_V2.md.

---

## Gambiarras específicas desta sprint

1. **Tutorial trava sem timeout.** `input("...")` sem `signal.alarm`. Proibido — spec exige 60s de ceiling.
2. **Escrever config.toml sem backup.** `path.write_text(new)` quando já existe. Proibido — usuário perde config antiga em erro.
3. **Tutorial roda em CI / pipe.** Não verificar `sys.stdin.isatty()`. Proibido — trava pipeline.
4. **Idempotência fake.** Marcar `.first_run_done` em memória mas não em disco. Proibido — segundo boot repete tutorial.
5. **Escrita não-atômica.** `path.write_text(content)` direto. Proibido — crash no meio corrompe toml.
6. **Precedência errada.** toml sobrescrever env. Proibido — env é sempre mais forte.
7. **Path absoluto hardcoded.** `/home/andrefarias/.nyx`. Proibido — `Path.home() / ".nyx"`.
8. **Emoji no banner.** `print("Bem-vinda ao Nyx!")`. Proibido — ADR-004.
9. **"Press any key to continue" em inglês.** Proibido — ADR-006.
10. **Silent skip sem log.** Auto-skip por timeout sem mensagem. Proibido — usuário precisa saber que foi pulado.

---

## Validação humana (checklist do usuário)

```bash
cd /home/andrefarias/Desenvolvimento/Nyx-Code

# 1. Diff do commit
git log --oneline -1
git show --stat HEAD

# 2. Primeira execução (em home limpo)
mv ~/.nyx ~/.nyx.backup
./run.sh
# esperado: tutorial de 5 steps com pausas
# Ctrl+D

# 3. Idempotência
./run.sh
# esperado: sem tutorial
# Ctrl+D

# 4. /config setup
./run.sh
# /config setup
# responder as 4 perguntas
# esperado: "Configuração salva em ~/.nyx/config.toml"
cat ~/.nyx/config.toml

# 5. Restaurar home
rm -rf ~/.nyx
mv ~/.nyx.backup ~/.nyx

# 6. Arquivo movido
ls dev-journey/06-sprints/concluidos/SPRINT_ONBOARDING_01.md
```

---

## Riscos

| Risco | Mitigação |
|-------|-----------|
| `signal.SIGALRM` indisponível em Windows | Fallback com `select.select([sys.stdin], [], [], timeout)` |
| Usuário interrompe tutorial com Ctrl+C | Capturar KeyboardInterrupt, marcar `.first_run_done`, sair limpo |
| config.toml com sintaxe inválida causa crash em settings | `_load_toml_if_exists` captura `tomllib.TOMLDecodeError` e usa defaults com mensagem de erro |
| Backup .bak acumula sem limite | Rotação: manter apenas último .bak (sobrescrever) |
| tomllib indisponível em Python <3.11 | GUIDE.md especifica Python 3.10+; adicionar fallback com `tomli` se detectar <3.11 |
| Usuário pula tutorial e depois quer rever | Adicionar comando `/tutorial` que re-executa sem tocar `.first_run_done` (fora de escopo, anotar como débito) |

---

*"O primeiro passo bem dado poupa mil retrocessos." -- Epicteto (adaptado)*
