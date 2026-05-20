# SPRINT HELP-EXAMPLES-01 — `/help <cmd>` com 2-3 exemplos reais por comando

## 0. SPEC (machine-readable)

```yaml
sprint:
  id: HELP-EXAMPLES-01
  title: "Enriquecer /help <cmd> com 2-3 exemplos reais de uso por comando; cobertura 100% dos 47 commands"
  onda: 22
  bloco: 8
  prioridade: BAIXA
  tipo: Docs + Feature
  dependencias: [UX-BUG-01]
  desbloqueia: []

  touches:
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/agent/commands/_registry.py
      reason: "Adicionar campo `examples: list[str]` na dataclass NyxCommand"
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/agent/commands/core.py
      reason: "cmd_help consome examples quando chamado com argumento"
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/agent/commands/system.py
      reason: "Adicionar examples em cada @nyx_command do arquivo (split AUDIT-FIX-05)"
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/agent/commands/session.py
      reason: "Adicionar examples em cada @nyx_command"
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/agent/commands/code.py
      reason: "Adicionar examples em cada @nyx_command"
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/agent/commands/git_cmds.py
      reason: "Adicionar examples em cada @nyx_command"
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/agent/commands/debug_cmds.py
      reason: "Adicionar examples em cada @nyx_command"
  creates:
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/scripts/audit_help_coverage.py
      reason: "Verifica que 100% dos 47 commands têm pelo menos 2 examples não-vazios"
  removes: []

  n_to_n_pairs:
    - descricao: "Contrato 'mínimo 2 exemplos' vive no decorator @nyx_command e no script de auditoria"
      paths:
        - /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/agent/commands/_registry.py
        - /home/andrefarias/Desenvolvimento/Nyx-Code/scripts/audit_help_coverage.py

  forbidden:
    - "Copiar exemplos genéricos sem sentido (ex: /commit 'teste', /read arquivo)"
    - "Menos de 2 exemplos por command — floor é 2, ceil é 3"
    - "Exemplo em inglês (ex: /read file.txt em vez de /read arquivo.txt)"
    - "Exemplo com path absoluto real do usuário (/home/andrefarias/... vaza info)"
    - "Pular commands 'óbvios' tipo /exit ou /clear — cobertura é 100%, não 95%"
    - "Duplicar exemplos entre commands (copiar /commit examples para /amend)"
    - "Adicionar emoji ou menção a IA"

  tests:
    - cmd: "python scripts/audit_help_coverage.py"
      timeout: 30
      deve_passar: "saída literal '47/47 OK'"
    - cmd: "./run.sh --gauntlet --only interface"
      timeout: 300
      deve_passar: true

  acceptance_criteria:
    - "Todos os 47 commands têm >=2 e <=3 exemplos"
    - "Exemplos em PT-BR com acentuação correta quando aplicável"
    - "Exemplos realistas (refletem uso real, não sintéticos)"
    - "Zero paths absolutos reais de usuário"
    - "`/help <cmd>` exibe descrição + bloco 'Exemplos:'"
    - "`/help` sem argumento continua funcionando (lista comandos)"
    - "Script de auditoria incorporado ao Gauntlet fase `interface`"
    - "Gauntlet `--only interface` passa 100%"
```

---

**Status:** CONCLUIDA (header corrigido em MASTER-CLEANUP-02 2026-05-20; presença em concluidos/ implica CONCLUIDA conforme convenção do projeto)
**Data criação:** 2026-04-19
**Modelo obrigatório:** claude-opus-4-7 (sem subagentes)

---

## Contexto do projeto (snapshot — não referência)

> **ADRs relevantes:**
> - ADR-004 Zero Emojis: em exemplos também.
> - ADR-005 Anonimato: sem "peça ajuda a Claude" etc.
> - ADR-006 PT-BR: exemplos com acentuação.
> - ADR-013 Integração Obrigatória: campo `examples` entra na dataclass, não em arquivo paralelo.
> - ADR-014 Testes via Gauntlet.
>
> **Estado do sistema:**
> - 47 commands distribuídos em: `core.py`, `system.py`, `session.py`, `code.py`, `git_cmds.py`, `debug_cmds.py` (pós-split AUDIT-FIX-05).
> - `UX-BUG-01` (pré-requisito) já entregou `/help` com fuzzy match.
> - `@nyx_command` é o decorator único de registro — manter simetria: se mexe um, mexe todos.

---

## Problema

### Sintoma observável

Hoje `/help commit` retorna apenas:
```
/commit -- Cria commit git com mensagem.
```

Usuário que não conhece o comando não sabe:
- Se aceita mensagem inline ou abre editor.
- Se tem flags (--amend, -m, --no-verify).
- Como chamar interativamente.

Resultado: usuários voltam ao modelo ("/ajuda me fala como commitar") em vez de usar `/help`.

### Requisito funcional

`/help commit` deve retornar:
```
/commit -- Cria commit git com mensagem.

Exemplos:
  /commit -m "fix: corrige regex do parser"
  /commit --amend
  /commit
```

### Escopo

TODOS os 47 commands. Não negociável: "óbvios" como `/exit`, `/clear`, `/help` também entram. Usuário novo não sabe o que é óbvio.

---

## Solução proposta

1. Adicionar campo `examples: list[str] = field(default_factory=list)` na dataclass `NyxCommand` em `_registry.py`.
2. Atualizar decorator `@nyx_command` para aceitar `examples=[...]`.
3. Atualizar `cmd_help` em `core.py` para, quando chamado com argumento, incluir bloco `Exemplos:` formatado.
4. Adicionar `examples=[...]` em cada `@nyx_command` dos 6 arquivos de commands.
5. Criar `scripts/audit_help_coverage.py` que percorre `registry` e exige `len(cmd.examples) >= 2`.
6. Incorporar script à fase `interface` do Gauntlet.

---

## Arquivos alvo (paths absolutos)

### `/home/andrefarias/Desenvolvimento/Nyx-Code/nyx/agent/commands/_registry.py`

**Antes:**
```python
@dataclass
class NyxCommand:
    name: str
    description: str
    handler: Callable
    permission_level: int = 0
```

**Depois:**
```python
@dataclass
class NyxCommand:
    name: str
    description: str
    handler: Callable
    permission_level: int = 0
    examples: list[str] = field(default_factory=list)
```

Atualizar `nyx_command(...)` para repassar `examples`.

### `/home/andrefarias/Desenvolvimento/Nyx-Code/nyx/agent/commands/core.py`

**Antes (trecho de cmd_help):**
```python
def cmd_help(args, ctx):
    if args:
        cmd = registry.get(args[0])
        if cmd:
            print(f"/{cmd.name} -- {cmd.description}")
```

**Depois:**
```python
def cmd_help(args, ctx):
    if args:
        cmd = registry.get(args[0])
        if not cmd:
            # mantém comportamento do fuzzy de UX-BUG-01
            return _help_fuzzy_suggest(args[0], ctx)
        ctx.output.print(f"/{cmd.name} -- {cmd.description}\n")
        if cmd.examples:
            ctx.output.print("Exemplos:")
            for ex in cmd.examples:
                ctx.output.print(f"  {ex}")
        return CommandResult.ok()
```

### `/home/andrefarias/Desenvolvimento/Nyx-Code/nyx/agent/commands/system.py`

**Antes:**
```python
@nyx_command(name="config", description="Mostra configuração atual.")
def cmd_config(args, ctx): ...
```

**Depois:**
```python
@nyx_command(
    name="config",
    description="Mostra configuração atual.",
    examples=[
        "/config",
        "/config setup",
        "/config get tema",
    ],
)
def cmd_config(args, ctx): ...
```

Fazer o equivalente para todos os comandos do arquivo: `/theme`, `/model`, `/bypass`, etc.

### `/home/andrefarias/Desenvolvimento/Nyx-Code/nyx/agent/commands/session.py`

Adicionar `examples` para `/save`, `/load`, `/resume`, `/replay`, `/sessions`, etc. Exemplo:
```python
@nyx_command(
    name="save",
    description="Salva sessão atual.",
    examples=[
        "/save",
        "/save nome-da-sessao",
    ],
)
def cmd_save(args, ctx): ...
```

### `/home/andrefarias/Desenvolvimento/Nyx-Code/nyx/agent/commands/code.py`

Exemplos para `/edit`, `/read`, `/search`, `/write`, `/diff`:
```python
@nyx_command(
    name="edit",
    description="Edita arquivo com diff interativo.",
    examples=[
        "/edit nyx/cli.py",
        "/edit README.md",
    ],
)
```

### `/home/andrefarias/Desenvolvimento/Nyx-Code/nyx/agent/commands/git_cmds.py`

Exemplos para `/commit`, `/status`, `/log`, `/diff`, `/branch`, `/push`, `/stash`:
```python
@nyx_command(
    name="commit",
    description="Cria commit git com mensagem.",
    examples=[
        "/commit -m \"fix: corrige regex do parser\"",
        "/commit --amend",
        "/commit",
    ],
)
```

### `/home/andrefarias/Desenvolvimento/Nyx-Code/nyx/agent/commands/debug_cmds.py`

Exemplos para `/debug`, `/trace`, `/profile`, `/log`, `/verbose`:
```python
@nyx_command(
    name="debug",
    description="Ativa modo debug.",
    examples=[
        "/debug on",
        "/debug off",
        "/debug status",
    ],
)
```

### `/home/andrefarias/Desenvolvimento/Nyx-Code/scripts/audit_help_coverage.py`

Novo arquivo. Lógica:
```python
from nyx.agent.commands._registry import registry
faltantes = []
for name, cmd in registry.items():
    if len(cmd.examples) < 2:
        faltantes.append((name, len(cmd.examples)))
    if len(cmd.examples) > 3:
        faltantes.append((name, len(cmd.examples)))  # teto
total = len(registry)
ok = total - len(faltantes)
print(f"{ok}/{total} OK")
if faltantes:
    for name, n in faltantes:
        print(f"  FAIL /{name}: {n} exemplos (esperado 2-3)")
    sys.exit(1)
```

---

## Diff esperado (resumo)

```
+ 1 arquivo criado (audit_help_coverage.py)
~ 8 arquivos modificados (_registry + core + 5 de commands)
- 0 arquivos removidos
+ ~180 linhas líquidas (3 exemplos x 47 commands + ajustes estruturais)
```

---

## Comandos de verificação (literais, copy-paste)

```bash
# 1. Validação estática
python -m ruff check nyx/ scripts/

# 2. Auditoria de cobertura
python scripts/audit_help_coverage.py
# Saída esperada: "47/47 OK"

# 3. Gauntlet
./run.sh --gauntlet --only interface

# 4. Manual
./run.sh
# No REPL:
#   /help commit   -> deve mostrar 2-3 exemplos
#   /help xyz      -> fuzzy suggest (preservado de UX-BUG-01)
#   /help          -> lista tudo sem exemplos individuais
```

---

## Critério binário de aceite (IA executora)

- [ ] `python scripts/audit_help_coverage.py` imprime `47/47 OK`
- [ ] Todos os 47 commands têm 2 ou 3 exemplos
- [ ] Exemplos em PT-BR com acentuação correta onde aplicável
- [ ] Nenhum exemplo com path absoluto real de usuário (grep `/home/andrefarias` nos examples)
- [ ] `/help commit` exibe bloco `Exemplos:` formatado
- [ ] `/help` sem argumento continua listando comandos
- [ ] Fuzzy match de UX-BUG-01 preservado
- [ ] Script incorporado à fase `interface` do Gauntlet
- [ ] Gauntlet `--only interface` passa 100%
- [ ] `ruff` não reclama
- [ ] Sprint movida para `concluidos/` com commit `feat: /help com 2-3 exemplos reais por comando`
- [ ] Nenhuma violação de `forbidden[]`

---

## Guardrails anti-engodo (obrigatórios)

- Não reduzir `floor` de 2 para 1 em commands "difíceis de exemplificar".
- Não repetir o mesmo exemplo em 2 comandos diferentes (verificar via `set`).
- Não pular commands que a IA "não entende" — ler `description` e inferir.
- Não marcar concluída sem saída literal `47/47 OK` do script.

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
#   consultar GAMBIARRAS_POR_SPRINT.md seção HELP-EXAMPLES-01

# PASSO 3 — snapshot DEPOIS
bash scripts/sprint_invariants.sh > /tmp/inv_after.txt 2>&1
FAIL_AFTER=$(grep -c "^\[FAIL\]" /tmp/inv_after.txt)

# PASSO 4 — regras binárias
diff /tmp/inv_before.txt /tmp/inv_after.txt

# Extra obrigatório: colar saída literal de audit_help_coverage.py
python scripts/audit_help_coverage.py
```

**Formato obrigatório:** ver SPRINT_TEMPLATE_V2.md.

---

## Gambiarras específicas desta sprint

1. **Copiar exemplos genéricos.** `/commit teste`, `/read arquivo.txt`. Proibido — exemplos precisam fazer sentido contextual (`/commit -m "fix: corrige regex"`, `/read nyx/cli.py`).
2. **Menos de 2 exemplos.** `examples=["/exit"]` para o comando `/exit`. Proibido — floor é 2 (ex: `/exit` e `/exit --no-save`).
3. **Exemplo em inglês.** `/read file.txt` em vez de `/read arquivo.txt`. Proibido — ADR-006.
4. **Path absoluto real.** `/edit /home/andrefarias/foo.py`. Proibido — vaza info pessoal.
5. **Duplicar exemplos entre commands.** Copiar `examples` de `/commit` para `/amend`. Proibido — cada comando tem uso próprio.
6. **Afrouxar script de auditoria.** Mudar `>= 2` para `>= 1`. Proibido — quebra contrato.
7. **Pular comandos "óbvios".** `/exit` sem examples "porque é óbvio". Proibido — 47/47, não 45/47.
8. **Mais de 3 exemplos.** `examples=["a", "b", "c", "d", "e"]`. Proibido — ceil é 3, senão vira manual.

---

## Validação humana (checklist do usuário)

```bash
cd /home/andrefarias/Desenvolvimento/Nyx-Code

# 1. Diff do commit
git log --oneline -1
git show --stat HEAD

# 2. Auditoria
python scripts/audit_help_coverage.py
# saída esperada: "47/47 OK"

# 3. Teste manual
./run.sh
# digitar: /help commit
# esperado:
#   /commit -- Cria commit git com mensagem.
#
#   Exemplos:
#     /commit -m "fix: corrige regex do parser"
#     /commit --amend
#     /commit

# 4. Fuzzy ainda funciona
# digitar: /help commmit
# esperado: "Você quis dizer /commit?"

# 5. Arquivo movido
ls dev-journey/06-sprints/concluidos/SPRINT_HELP_EXAMPLES_01.md
```

---

## Riscos

| Risco | Mitigação |
|-------|-----------|
| 47 commands são muitos; fadiga leva a exemplos ruins | Revisar lote por arquivo (6 arquivos), fazer pausa entre lotes, usar checklist |
| Comandos novos criados depois desta sprint esquecem `examples` | Script de auditoria no Gauntlet força falha — CI impede merge sem |
| Usuário digita `/help /commit` (com barra) em vez de `/help commit` | cmd_help normaliza strip de `/` inicial |
| Exemplos ficam desatualizados quando comando muda interface | Docstring do decorator lembra: "atualizar examples ao mudar args" |
| Exemplo com aspas quebra formatação ANSI | Escapar via repr seguro no output |

---

*"Quem explica bem ensina uma vez, quem explica mal repete para sempre." -- Sêneca (adaptado)*
