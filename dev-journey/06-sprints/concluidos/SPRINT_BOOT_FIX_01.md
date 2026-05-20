# SPRINT BOOT-FIX-01 — Corrigir boot de `./run.sh` e adicionar smoke check ao protocolo

## 0. SPEC (machine-readable)

```yaml
sprint:
  id: BOOT-FIX-01
  title: "Corrigir boot de ./run.sh (sys.path antes de import nyx.*) e adicionar smoke check ao protocolo anti-regressão"
  onda: 22
  bloco: 2.6
  prioridade: CRÍTICA
  tipo: Bugfix
  dependencias: []
  desbloqueia: [VALIDATE-ONDA-20]

  touches:
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/cli.py
      reason: "Reordenar sys.path.insert para ANTES de qualquer import `from nyx.*` (mirror de proxy.py:22-24); adicionar flag argparse --smoke"
      linhas_alvo: "18-40"
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/run.sh
      reason: "Adicionar branch --smoke no topo: delega direto ao cli.py sem subir Ollama/proxy"
      linhas_alvo: "56-91"
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/scripts/sprint_invariants.sh
      reason: "Adicionar check #13 — `./run.sh --smoke` retorna 0 e imprime exatamente 'boot ok'"

  creates: []
  removes: []

  n_to_n_pairs: []

  forbidden:
    - "Alterar lógica de cli.py além da reordenação de imports e adição de --smoke (sem mexer em _build_banner, REPL, nada)"
    - "Alterar run.sh além de adicionar o branch --smoke no topo (sem reformatar, sem mexer em Ollama/proxy startup)"
    - "Adicionar outras verificações ao smoke além da presença do binário 'boot ok' — minimalismo"
    - "Criar test_boot.py ou similar (ADR-014 — testes só via Gauntlet)"
    - "Fixar outros bugs encontrados durante auditoria inline — materializar como arquivo de sprint em producao/ + linha no master (ver seção 'Protocolo de achados colaterais')"
    - "Fazer smoke rodar Ollama/proxy — derrota o propósito (rápido, determinístico)"
    - "Implementar --smoke via env var ou arquivo de lock — flag argparse, puro"
    - "Emitir 'boot ok' via logger.info — deve ser `print(\"boot ok\")` no cli.py (permitido por ADR-024 + GUIDE.md para cli.py)"
    - "Mudar o texto 'boot ok' para qualquer outra coisa — check do invariante é grep literal"
    - "Adicionar emoji em qualquer lugar"
    - "Menção a Claude/GPT/Anthropic em código/commits"

  tests:
    - cmd: "./venv/bin/python nyx/cli.py --smoke"
      deve_passar: "stdout exato 'boot ok' + exit 0"
    - cmd: "./run.sh --smoke"
      deve_passar: "stdout contém 'boot ok' + exit 0 + < 5s sem subir Ollama/proxy"
    - cmd: "timeout 20s ./run.sh"
      deve_passar: "alcança prompt nyx> sem ModuleNotFoundError"
    - cmd: "bash scripts/sprint_invariants.sh"
      deve_passar: "check #13 PASS; FAIL_AFTER == FAIL_BEFORE (1)"
    - cmd: "./run.sh --gauntlet --only rapido"
      deve_passar: "não regride"

  acceptance_criteria:
    - "`./run.sh` boota sem ModuleNotFoundError e alcança o prompt `nyx>`"
    - "`./run.sh --smoke` retorna 0, imprime exatamente 'boot ok', executa em < 5s sem subir Ollama"
    - "`./venv/bin/python nyx/cli.py --smoke` retorna 0, imprime 'boot ok'"
    - "`scripts/sprint_invariants.sh` tem check #13 funcional; FAIL mantém-se estável em 1 (emoji pré-existente)"
    - "Gauntlet `--only rapido` não regride"
    - "Acentuação PT-BR correta em tudo novo"
```

---

**Status:** CONCLUIDA (header corrigido em MASTER-CLEANUP-02 2026-05-20; presença em concluidos/ implica CONCLUIDA conforme convenção do projeto)
**Data criação:** 2026-04-19
**Modelo obrigatório:** claude-opus-4-7 (sem subagentes)

---

## Contexto do projeto (snapshot)

> **ADRs relevantes:**
> - ADR-001 Local First.
> - ADR-013 Integração Obrigatória.
> - ADR-014 Testes via Gauntlet (não criar `test_boot.py`).
> - ADR-020 Testes via `run.sh`.
> - ADR-024 Render Layer: `print()` permitido em `nyx/cli.py` e `nyx/agent/output.py`.
>
> **Estado do sistema:**
> - 2026-04-19, Onda 22, Bloco 2.6 (rebatizado de "Infra" para "Integração" após INFRA-GAUNTLET-01 DESCARTADA em 2026-04-19).
> - VALIDATE-ONDA-20 em execução; validação visual travou porque `./run.sh` crasha.
> - `nyx/cli.py` 722 linhas; `nyx/proxy.py` 367 linhas (referência do padrão correto).
> - `scripts/sprint_invariants.sh` tem 12 checks; o 13º fecha esse gap de protocolo.
> - Última sprint concluída: DEBT-07 (commit 8c91fe5).

---

## Problema

Durante a validação visual da Onda 20 (VALIDATE-ONDA-20), tentou-se rodar `./venv/bin/python nyx/cli.py --headless` e obteve-se:

```
Traceback (most recent call last):
  File "/home/andrefarias/Desenvolvimento/Nyx-Code/nyx/cli.py", line 29, in <module>
    from nyx.agent.services.logging_service import get_logger
ModuleNotFoundError: No module named 'nyx'
```

**Causa:** `nyx/cli.py:29` faz `from nyx.agent.services.logging_service import get_logger` **antes** de `sys.path.insert(0, str(PROJECT_ROOT))` na linha 35. Quando invocado como `python nyx/cli.py` (caminho do `run.sh:407`), o interpretador só coloca `nyx/` em `sys.path`, não o repo-root. `nyx.proxy` tem o fix correto em `proxy.py:22-24`; `cli.py` regrediu em refactor recente (provável DEBT-03 que moveu `logging_service` para `nyx/agent/services/`).

**Gap de protocolo exposto:** Sprints inteiras rodaram com o app quebrado em boot sem detecção. `run.sh --gauntlet --only <fase>` não pega porque invoca scripts de gauntlet com `PYTHONPATH=.` implícito via cwd. Pytest-like idem. Nenhum check do `sprint_invariants.sh` prova que o entrypoint oficial `./run.sh` sobe.

---

## Solução proposta

Duas correções atômicas na mesma sprint:

1. **Fix do boot** — reordenar `sys.path.insert` em `cli.py` (mirror de `proxy.py`).
2. **Check de protocolo** — flag `--smoke` minimalista em `cli.py` + branch `--smoke` em `run.sh` + check #13 no invariantes.

---

## Arquivos alvo

### 1. `nyx/cli.py`

**Antes (linhas 18-42):**
```python
from __future__ import annotations

import argparse
import asyncio
import os
import signal
import sys
import time
from pathlib import Path
from typing import TYPE_CHECKING

from nyx.agent.services.logging_service import get_logger

if TYPE_CHECKING:
    from nyx.config.settings import NyxSettings

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from nyx.agent.services.logging_service import InternalLogging  # noqa: E402

InternalLogging()
logger = get_logger("nyx.cli")

from nyx.__version__ import __version__ as NYX_VERSION  # noqa: E402
```

**Depois:**
```python
from __future__ import annotations

import argparse
import asyncio
import os
import signal
import sys
import time
from pathlib import Path
from typing import TYPE_CHECKING

# Permitir execução como script direto (python nyx/cli.py) além de -m nyx.cli.
# Sem isso, só o diretório nyx/ entra no sys.path e `import nyx.*` falha.
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from nyx.agent.services.logging_service import (  # noqa: E402
    InternalLogging,
    get_logger,
)

if TYPE_CHECKING:
    from nyx.config.settings import NyxSettings

InternalLogging()
logger = get_logger("nyx.cli")

from nyx.__version__ import __version__ as NYX_VERSION  # noqa: E402
```

**Mudanças:**
- `sys.path.insert` promovido a **antes** de qualquer `from nyx.*`.
- Guard `if str(PROJECT_ROOT) not in sys.path` (mirror de `proxy.py:23`, evita poluição em reimports).
- `get_logger` e `InternalLogging` unificados em um só import com `# noqa: E402` (só uma linha noqa em vez de duas).
- `TYPE_CHECKING` guard mantido abaixo do import (puramente sintático, sem efeito em runtime).

**Segunda edição (dentro do mesmo arquivo, no bloco de argparse):**

Localizar o `argparse.ArgumentParser` (buscar por `add_argument("--headless"` para ponto de referência) e adicionar:

```python
parser.add_argument("--smoke", action="store_true",
                    help="Prova que imports resolvem (imprime 'boot ok' e sai).")
```

E, logo após o `args = parser.parse_args()`, adicionar — **antes** de qualquer lógica de REPL/headless/conexão:

```python
if args.smoke:
    print("boot ok")
    sys.exit(0)
```

**Justificativa do print:** ADR-024 + GUIDE.md § "Nunca print()" autorizam `print()` em `nyx/cli.py` (e só lá + `output.py`). `boot ok` é literal; `logger.info` não serve porque stdout é o canal que o invariante vai grepar.

---

### 2. `run.sh`

**Adicionar no topo do loop de parse de flags** (linhas 56-91), como primeiro `case` antes dos demais:

```bash
    case "$1" in
        --smoke)
            # Smoke check: prova que imports resolvem sem subir Ollama/proxy.
            exec "$SCRIPT_DIR/venv/bin/python" "$SCRIPT_DIR/nyx/cli.py" --smoke
            ;;
        --3b)
            ...
```

`exec` substitui o processo: exit code do Python vira exit code do script, nada mais roda depois. Sem `set_trap`, sem `cleanup`, sem Ollama.

**Mudanças:**
- Branch `--smoke` como primeiro `case`.
- Usa `exec` para encerrar limpo.
- Não toca em nada mais do script.

---

### 3. `scripts/sprint_invariants.sh`

**Adicionar check #13** (após o último check existente, antes do resumo final):

```bash
# 13. ./run.sh --smoke (boot integrity)
check_start "13. ./run.sh --smoke (boot integrity)"
out=$(timeout 5 ./run.sh --smoke 2>&1)
rc=$?
if [ $rc -eq 0 ] && echo "$out" | grep -qx "boot ok"; then
    pass
else
    fail "exit=$rc, stdout=$(echo "$out" | head -3 | tr '\n' ' | ')"
fi
```

Adaptar à convenção de `check_start`/`pass`/`fail` do script atual (inspeção prévia obrigatória — não copiar cego se os helpers tiverem nomes diferentes).

---

## Diff esperado

```
~ 3 arquivos modificados
+ 0 arquivos criados
- 0 arquivos removidos
+ ~40 linhas líquidas
```

---

## Comandos de verificação (literais, copy-paste)

```bash
# PASSO 1 — snapshot ANTES
bash scripts/sprint_invariants.sh > /tmp/inv_before.txt 2>&1
FAIL_BEFORE=$(grep -c "^\[FAIL\]" /tmp/inv_before.txt)
echo "FAIL inicial: $FAIL_BEFORE"  # esperado: 1

# PASSO 2 — implementação (ordem obrigatória)
#   2a. Fix nyx/cli.py (imports + flag --smoke)
#   2b. Sanity: ./venv/bin/python nyx/cli.py --smoke → 'boot ok' + exit 0
#   2c. Patch run.sh (branch --smoke)
#   2d. Sanity: ./run.sh --smoke → 'boot ok' + exit 0, < 5s
#   2e. Sanity boot real: timeout 20s ./run.sh (deve alcançar nyx> sem crash)
#   2f. Patch scripts/sprint_invariants.sh (check #13)

# PASSO 3 — snapshot DEPOIS
bash scripts/sprint_invariants.sh > /tmp/inv_after.txt 2>&1
FAIL_AFTER=$(grep -c "^\[FAIL\]" /tmp/inv_after.txt)
echo "FAIL final: $FAIL_AFTER"  # esperado: 1 (mesmo pré-existente)
echo "PASS final: $(grep -c '^\[PASS\]' /tmp/inv_after.txt)"  # esperado: 12

# PASSO 4 — regressão global
./run.sh --gauntlet --only rapido
# esperado: sem regressão vs. baseline da Onda 20

# PASSO 5 — diff dos invariantes
diff /tmp/inv_before.txt /tmp/inv_after.txt
```

---

## Critério binário de aceite

- [ ] `./venv/bin/python nyx/cli.py --smoke` → stdout `boot ok`, exit 0
- [ ] `./run.sh --smoke` → stdout contém `boot ok`, exit 0, < 5s, sem Ollama/proxy no `ps aux`
- [ ] `timeout 20s ./run.sh` alcança prompt `nyx>` sem `ModuleNotFoundError`
- [ ] `sprint_invariants.sh` tem check #13, reporta PASS, FAIL total estável em 1
- [ ] `./run.sh --gauntlet --only rapido` sem regressão
- [ ] Nenhuma violação de `forbidden[]`
- [ ] SPRINT_ORDER_MASTER marca CONCLUIDA com hash, Bloco 2.6 rewording aplicado
- [ ] Sprint movida de `producao/` para `concluidos/`
- [ ] Dois commits atômicos: `fix: boot ./run.sh + smoke check no protocolo` e `docs: conclui BOOT-FIX-01`

---

## Guardrails anti-engodo

A IA executora **não pode** marcar sprint CONCLUIDA se:

- Smoke não reportar `boot ok` exato.
- `./run.sh` ainda crashar com ModuleNotFoundError.
- Introduzir novo FAIL no invariants (FAIL_AFTER > FAIL_BEFORE).
- Tocar em qualquer arquivo fora de `nyx/cli.py`, `run.sh`, `scripts/sprint_invariants.sh`, `SPRINT_ORDER_MASTER.md`, `EXECUTAR_SPRINT.md` e o próprio arquivo da sprint.
- Fixar bug adicional descoberto inline em vez de registrar como achado para sprint nova.

Se algum item falhar:
```
[SPRINT BOOT-FIX-01] BLOQUEADA: <motivo objetivo em 1 linha>
```

---

## Gambiarras específicas desta sprint

1. **Fallback por `try/except ImportError`** — proibido. Fix é reordenação, não mascarar ausência de path.
2. **Smoke que importa só `sys`** — proibido. Smoke deve exercitar o mesmo caminho de imports do REPL (`from nyx.agent...`). A presença do `print("boot ok")` pós-argparse já garante isso, desde que o import não seja movido para dentro de função.
3. **`PYTHONPATH=...` hardcoded no `run.sh --smoke`** — proibido. O fix é em `cli.py` e deve valer para qualquer invocação direta, inclusive `python nyx/cli.py` sem env var.
4. **`sys.path.insert` duplicado** — guard `if str(PROJECT_ROOT) not in sys.path` previne.
5. **Check #13 que não detecta o bug real** — o check precisa **falhar** se alguém voltar a mover `sys.path.insert` para depois do import, e **passar** quando o arquivo está ok. Teste manual obrigatório: reverter localmente a ordem dos imports, rodar o invariante, confirmar que #13 reporta FAIL. **Não colocar esse teste no relatório** (seria modificar o arquivo), apenas mencionar que foi feito.
6. **Conversar com usuário sobre "enquanto isso podemos…"** — não. Minimalismo: 3 arquivos, 2 commits, fim.

---

## Protocolo de achados colaterais (obrigatório — portão anti-débito)

Se durante a auditoria de `nyx/cli.py`, `run.sh` ou `scripts/sprint_invariants.sh` a IA executora descobrir **qualquer bug adicional fora do escopo declarado em `touches`**, aplica este protocolo **sem exceção**:

1. **NÃO fixa inline.** Escopo da BOOT-FIX-01 é exatamente o declarado em `touches`. Fixar inline = violação grave.
2. **Anota em lista interna** durante a sprint: rascunho em `/tmp/achados_boot_fix_01.md` (um achado por bloco, com: sintoma, arquivo, linha, proposta de fix em 1 frase).
3. **Antes do commit `docs: conclui BOOT-FIX-01`**, para **cada** achado da lista:
   - **Cria** `dev-journey/06-sprints/producao/SPRINT_<ID>.md` via `SPRINT_TEMPLATE_V2.md` com spec completa (touches, forbidden, tests, acceptance). Pode ser preliminar; usuário refina depois se quiser. ID novo sequencial no bloco apropriado.
   - **Adiciona linha** no `SPRINT_ORDER_MASTER.md` no bloco adequado (2.6 Integração se for bug de boot/integração; 2.5 se for cleanup; outro bloco se for outro tema) com status `PENDENTE`.
   - **Commit separado**: `docs: cria SPRINT_<ID>.md (achado durante BOOT-FIX-01)` — **um commit por achado**.
4. **Só depois** vem o commit final `docs: conclui BOOT-FIX-01`, que também atualiza a narrativa do Bloco 2.6 no master listando os novos sprints criados.
5. **Se nada foi achado**: segue direto pro commit de conclusão e declara no relatório final:
   > nenhum achado colateral durante a auditoria.

### Regra operacional

- Relatório menciona o achado **para histórico**, mas a **materialização acontece SEMPRE** como arquivo de sprint em `producao/` + entrada no master. Nunca só no relatório. Nunca "pra criar depois".
- Se a sessão terminar antes de materializar tudo: sprint **não é CONCLUIDA** — fica **BLOQUEADA** até materializar.

### Seção obrigatória no relatório final

Deve conter um dos dois textos abaixo, literalmente:

**Se houve achados:**
```
### Achados colaterais materializados

- SPRINT_<ID1>: `dev-journey/06-sprints/producao/SPRINT_<ID1>.md` (commit <hash>)
- SPRINT_<ID2>: `dev-journey/06-sprints/producao/SPRINT_<ID2>.md` (commit <hash>)
- ... (um por linha)
```

**Se não houve:**
```
### Achados colaterais materializados

Nenhum achado colateral durante a auditoria.
```

Sem esse registro explícito: sprint rejeitada mesmo que o boot esteja funcionando. Portão anti-débito.

---

## Proof-of-work obrigatório

Formato de relatório (não negociável):

```
### Proof-of-work

$ cat /tmp/inv_before.txt | tail -15
(saída bruta)

$ cat /tmp/inv_after.txt | tail -15
(saída bruta)

$ diff /tmp/inv_before.txt /tmp/inv_after.txt
(diff)

FAIL inicial: 1
FAIL final:   1  (estável; novo check #13 PASS)
Invariantes fechados por esta sprint: [#13 novo]

### Comando do smoke
$ ./venv/bin/python nyx/cli.py --smoke
boot ok
$ echo $?
0

$ time ./run.sh --smoke
boot ok
real    0m<5

### Boot real
$ timeout 20s ./run.sh 2>&1 | head -20
(primeiras 20 linhas do output; última deve conter 'nyx>' ou sinal de REPL vivo)

### Gauntlet rapido
$ ./run.sh --gauntlet --only rapido
(resumo: 18/18 ou baseline atual)

### Git
$ git log --oneline -2
<hash_fix>  fix: boot ./run.sh + smoke check no protocolo
<hash_docs> docs: conclui BOOT-FIX-01

$ git show --stat <hash_fix>
(stat)
```

Se o output acima não for colado integralmente: sprint rejeitada.

---

## Validação humana (checklist do usuário)

```bash
cd /home/andrefarias/Desenvolvimento/Nyx-Code

# 1. Ver diff
git log --oneline -2
git show --stat HEAD~1  # commit fix
git show --stat HEAD    # commit docs

# 2. Smoke manual
./run.sh --smoke
# saída esperada: 'boot ok' + exit 0

# 3. Boot real
./run.sh
# saída esperada: banner + prompt 'nyx>' (Ctrl+D para sair)

# 4. Invariante
bash scripts/sprint_invariants.sh | tail -20
# saída esperada: PASS total 12, FAIL 1 (emoji pré-existente)

# 5. Arquivos movidos
ls dev-journey/06-sprints/concluidos/SPRINT_BOOT_FIX_01.md  # existe
ls dev-journey/06-sprints/producao/SPRINT_BOOT_FIX_01.md    # NÃO existe
```

---

## Riscos

| Risco | Mitigação |
|-------|-----------|
| Reordenação quebra algum import já "protegido" por E402 e escondido | Diff mínimo (só linhas 18-40), guard não-destrutivo, sanity boot real obrigatório antes do commit |
| `exec` em `run.sh --smoke` interage mal com trap de cleanup | `exec` substitui processo inteiro, traps do shell antigo não disparam; confirmado em `man bash(1)` |
| Check #13 depende de porta/venv — pode dar falso FAIL em CI pobre | Timeout 5s + invocação direta do binário `venv/bin/python` (sem subir Ollama); não depende de rede |
| `sprint_invariants.sh` usa helpers que não batem com snippet proposto | Inspeção obrigatória do script real antes de editar — adaptar ao padrão exato dos 12 checks atuais |
| Descobrir outro bug durante a auditoria (ex.: outro arquivo com mesma ordem errada) | Registrar no relatório como achado → sprint nova. **Nunca** fixar inline (regra "nenhum débito para trás") |

---

*"A estrada certa raramente é a mais fácil." -- Sêneca (adaptado)*
