# SPRINT UX-BUG-02C — Fix do race de input conforme diagnóstico de 02A

## 0. SPEC (machine-readable)

```yaml
sprint:
  id: UX-BUG-02C
  title: "Fix do race de input-readiness (reorder init + drenar stdin)"
  onda: 22
  bloco: 5
  prioridade: ALTA
  tipo: Bugfix
  dependencias: [UX-BUG-02A]
  desbloqueia: []

  touches:
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/cli.py
      reason: "Reordenar init (banner primeiro, warm-up em asyncio.create_task), drenar stdin via termios.tcflush antes do primeiro prompt_async"
      linhas_alvo: "run_repl()"

  creates: []
  removes: []

  n_to_n_pairs: []

  forbidden:
    - "sleep() como fix (gambiarra explícita no catálogo #18)"
    - "Fazer fix sem confirmar com output do repro_race_input.sh"
    - "Remover streaming ou async loop"
    - "Tocar em nyx/agent/loop/* (escopo de 02B)"
    - "Mudar contrato de AgentLoop.__init__ (02B que define)"
    - "Ignorar o diagnóstico de 02A e aplicar outro fix 'por intuição'"
    - "Silenciar termios.error sem logger.warning (exceto path CI/headless documentado)"
    - "Menção a IA em comentários/commits"

  tests:
    - cmd: "bash scripts/repro_race_input.sh"
      deve_passar: true
      nota: "Agora DEVE retornar [ok] input chegou (ou, se fix é drenar, deve retornar [ok] prompt limpo com input descartado de forma consistente conforme escolha em 02A)"
    - cmd: "./run.sh --gauntlet --only tui"
      timeout: 300
      deve_passar: true
    - cmd: "./run.sh --gauntlet --only rapido"
      timeout: 300
      deve_passar: true

  acceptance_criteria:
    - "Fix alinhado ao diagnóstico de DIAG_RACE_INPUT.md (UX-BUG-02A)"
    - "scripts/repro_race_input.sh passa com comportamento determinístico (sempre [ok] ou sempre [bug-descartado-esperado], conforme decisão do relatório)"
    - "Banner imprime ANTES do warm-up; warm-up em asyncio.create_task"
    - "stdin drenado via termios.tcflush antes do primeiro prompt_async (se diagnóstico for 'drenar')"
    - "termios.error/OSError tratado com logger.warning + fallback silencioso em não-tty (CI/headless)"
    - "Zero sleep() novos em caminho síncrono do REPL"
    - "Gauntlet tui e rapido passam 100%"
    - "Acentuação PT-BR correta"
```

---

**Status:** CONCLUIDA
**Data criação:** 2026-04-19
**Data conclusão:** 2026-05-17
**Hash:** (a preencher pós-commit)
**Origem:** divisão de UX-BUG-02. Esta sprint aplica o fix identificado em 02A.
**Modelo obrigatório:** claude-opus-4-7 (sem subagentes)
**Resultado:** H2 (warmup sem indicador) e H1 (race de stdin) resolvidos. Cleanup + memory.index migrados para asyncio.create_task(_warmup()) pós-banner. termios.tcflush(stdin, TCIFLUSH) antes do primeiro prompt_async (guard sys.stdin.isatty()). repro_race_input.sh determinístico em 4 runs consecutivas. Gauntlet rapido 18/18 + p7 6/6 + interface 5/5. +32L em nyx/cli.py.

---

## Contexto do projeto (snapshot — não referência)

> **ADRs relevantes:**
> - ADR-001 Local First.
> - ADR-004 Zero Emojis.
> - ADR-005 Anonimato.
> - ADR-006 PT-BR.
> - ADR-010 Zero Mocks.
> - ADR-013 Integração Obrigatória.
> - ADR-014 Testes via Gauntlet.
> - ADR-020 Testes via run.sh.
>
> **Estado do sistema:**
> - Onda 22, Bloco 5.
> - UX-BUG-02A produziu `dev-journey/07-reports/DIAG_RACE_INPUT.md` com causa confirmada.
> - UX-BUG-02B adicionou estado cold/warming/warm (pode já estar concluída ou não — não depende, mas não sobrescrever).

---

## Problema

Após diagnóstico (UX-BUG-02A), aplicar o fix exato que fecha o race sem gambiarra.

---

## Solução proposta

Abrir `dev-journey/07-reports/DIAG_RACE_INPUT.md`, ler a seção "Causa confirmada" e "Recomendação", e aplicar literalmente. Três variantes esperadas:

### Variante 1 — Causa: warm-up síncrono atrasa prompt

Mover `cleanup_old_sessions()`, `Analytics()`, `agent._memory.index()` para `asyncio.create_task` **após** o banner imprimir:

```python
print(_build_banner(...))

async def _warmup():
    cleanup_old_sessions()
    await agent._memory.index()
    Analytics().boot()

asyncio.create_task(_warmup())
```

### Variante 2 — Causa: buffer de tty do prompt_toolkit

Drenar stdin antes do primeiro `prompt_async`:

```python
import termios
if sys.stdin.isatty():
    try:
        termios.tcflush(sys.stdin.fileno(), termios.TCIFLUSH)
    except (termios.error, OSError) as exc:
        logger.warning("termios.tcflush falhou: %s", exc)
```

### Variante 3 — Causa: render_user_input antes do prompt pronto

Reordenar para o prompt_async ser awaitado antes de qualquer render_user_input. Detalhes dependem do diagnóstico.

---

## Arquivos alvo (paths absolutos)

### `/home/andrefarias/Desenvolvimento/Nyx-Code/nyx/cli.py`

**Antes (conceitual):**
```python
async def run_repl():
    cleanup_old_sessions()
    analytics = Analytics()
    agent = AgentLoop(...)
    await agent._memory.index()
    print(_build_banner(...))
    while True:
        user_input = await prompt_async(...)
        ...
```

**Depois (conceitual, variante combinada 1+2):**
```python
async def run_repl():
    print(_build_banner(...))

    async def _warmup():
        cleanup_old_sessions()
        await agent._memory.index()
        Analytics().boot()

    agent = AgentLoop(...)
    asyncio.create_task(_warmup())

    if sys.stdin.isatty():
        try:
            termios.tcflush(sys.stdin.fileno(), termios.TCIFLUSH)
        except (termios.error, OSError) as exc:
            logger.warning("termios.tcflush falhou: %s", exc)

    while True:
        user_input = await prompt_async(...)
        ...
```

**Mudanças:**

- Banner imprime primeiro.
- `AgentLoop(...)` criado sincronicamente (barato), mas trabalho pesado de warm-up em task async.
- `termios.tcflush` antes do primeiro prompt em tty.
- `try/except` com `logger.warning` (nunca silent pass).
- Zero `sleep()` novo.

---

## Diff esperado (resumo)

```
+ 0 arquivos criados
~ 1 arquivo modificado
- 0 arquivos removidos
+ ~30 linhas líquidas
```

---

## Comandos de verificação (literais, copy-paste)

```bash
cd /home/andrefarias/Desenvolvimento/Nyx-Code

# 1. Zero sleep novo
git diff nyx/cli.py | grep -E "^\+.*time\.sleep|^\+.*asyncio\.sleep"
# esperado: vazio (ou justificado em comentário adjacente)

# 2. Repro passa
bash scripts/repro_race_input.sh

# 3. Lint
python -m ruff check nyx/cli.py

# 4. Gauntlet
./run.sh --gauntlet --only tui
./run.sh --gauntlet --only rapido

# 5. Validação manual
./run.sh
# tentar digitar durante o banner — comportamento deve ser consistente com decisão em DIAG_RACE_INPUT.md
```

---

## Critério binário de aceite

- [ ] Fix mapeia 1:1 para "Causa confirmada" em `DIAG_RACE_INPUT.md`
- [ ] Banner imprime antes de qualquer warm-up pesado
- [ ] Warm-up em `asyncio.create_task` (se variante 1 aplicável)
- [ ] `termios.tcflush` presente antes do primeiro prompt_async (se variante 2 aplicável)
- [ ] `try/except` com `logger.warning` em chamadas de termios (nunca `pass` silencioso)
- [ ] Zero `time.sleep` ou `asyncio.sleep` novo em `run_repl`
- [ ] `bash scripts/repro_race_input.sh` passa determinísticamente
- [ ] Gauntlet `--only tui` e `--only rapido` 100%
- [ ] `ruff` sem reclamações
- [ ] Sem emoji, sem menção a IA, acentuação PT-BR
- [ ] Commit: `fix: race de input no REPL (reorder + drenar stdin)`

---

## Guardrails anti-engodo

**NÃO marque como concluída se:**

- IA aplicou fix sem ler `DIAG_RACE_INPUT.md`.
- "Resolveu" com `await asyncio.sleep(0.5)` antes do prompt.
- `try/except: pass` em volta de termios (deve ter `logger.warning`).
- Repro ainda falha de forma não-determinística.
- Mexeu em `nyx/agent/loop/_core.py` (escopo de 02B, não desta).

---

## Catálogo de gambiarras proibidas

Aplicáveis especialmente:

- #17 **Silent except**: `except termios.error: pass` proibido — usar `logger.warning`.
- #18 **Sleep como fix**: `sleep` para contornar race. Proibido.
- #6 **Modificar teste em vez de código**: alterar `scripts/repro_race_input.sh` para ele "passar". Proibido — teste é o oráculo.
- #20 **Checkpoint marcado sem verificar**: marcar `- [x] repro passa` sem colar output.

---

## Proof-of-work obrigatório

Incluir no relatório:

- `cat /tmp/inv_before.txt | tail -10` e `cat /tmp/inv_after.txt | tail -10` + diff.
- Citação literal da seção "Causa confirmada" de `DIAG_RACE_INPUT.md`.
- Output de `bash scripts/repro_race_input.sh` ANTES (precisa ser `[bug]`) e DEPOIS (precisa ser `[ok]` ou determinístico).
- `./run.sh --gauntlet --only tui` output.
- `./run.sh --gauntlet --only rapido` output.
- `git show --stat HEAD`.

---

## Gambiarras específicas desta sprint

1. **Sleep disfarçado**: `asyncio.wait_for(..., timeout=0.3)` usado como barreira artificial. Proibido.
2. **Ignorar o diagnóstico**: aplicar fix "que geralmente funciona" sem ler 02A. Proibido — a sprint existe porque 02A existe.
3. **Mudar o repro para passar**: editar `scripts/repro_race_input.sh` para relaxar grep. Proibido.
4. **Silent except em termios**: `except: pass`. Proibido — usar `logger.warning` e continuar.
5. **Tocar em `nyx/agent/loop/*`**: fora do escopo. Se causa exigir mudanças ali, abrir sprint nova (nenhum débito fica para trás).

---

## Validação humana (checklist do usuário)

```bash
cd /home/andrefarias/Desenvolvimento/Nyx-Code

git log --oneline -1
git show --stat HEAD

cat dev-journey/07-reports/DIAG_RACE_INPUT.md | sed -n '/## Causa confirmada/,/^## /p'

bash scripts/repro_race_input.sh
./run.sh --gauntlet --only tui
./run.sh --gauntlet --only rapido

./run.sh
# tentar digitar antes do prompt aparecer; confirmar comportamento consistente com relatório
# Ctrl+D

ls dev-journey/06-sprints/concluidos/SPRINT_UX_BUG_02C.md
! ls dev-journey/06-sprints/producao/SPRINT_UX_BUG_02C.md 2>/dev/null
```

---

## Riscos

| Risco | Mitigação |
|-------|-----------|
| Diagnóstico de 02A conclui "inconclusivo" | Reabrir UX-BUG-02A antes; não iniciar 02C sem causa confirmada |
| termios.tcflush falha em CI/headless | Guard `sys.stdin.isatty()` + `try/except` com `logger.warning` |
| Warm-up em task async gera race com primeiro `run()` | `AgentLoop` precisa ser construível e `run()`-capaz antes do warm-up terminar; memória parcial aceita |
| Fix corrige sintoma mas não causa | Protocolo anti-débito: se 02C descobre segunda causa, registrar como sprint nova |

---

*"Quem fixa o sintoma herda o bug." -- adaptado do folclore de engenharia*
