> **Status:** ABSORVIDA_POR_UX-BUG-02A, UX-BUG-02B, UX-BUG-02C (2026-04-19)
>
> **Nota de absorção:** sprint original tinha 5 responsabilidades (repro, diagnóstico de 3 hipóteses, reorder init, drenar stdin, estado warm/cold). Dividida por protocolo `systematic-debugging`:
> - Parte A (diagnóstico sistemático + repro_race_input.sh + DIAG_RACE_INPUT.md) → `SPRINT_UX_BUG_02A.md`.
> - Parte B.3/B.4 (estado cold/warming/warm + toolbar) → `SPRINT_UX_BUG_02B.md` (deps: 02A + OBSERVABILITY-01).
> - Parte B.1/B.2 (reorder init + termios.tcflush) → `SPRINT_UX_BUG_02C.md` (deps: 02A).
>
> Arquivo preservado em `producao/` como referência histórica.

---

## 0. SPEC

```yaml
sprint:
  id: UX-BUG-02
  title: "[ABSORVIDA] Race de input-readiness + indicador visual qwen3 cold/warm"
  onda: 22
  bloco: 5
  prioridade: ALTA
  tipo: Bugfix + Feature
  dependencias: [UX-BUG-01]
  desbloqueia: [UX-BUG-03]

  touches:
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/cli.py
      reason: "Reordenar banner/prompt; adicionar estado warm/cold do modelo; drenar stdin pré-prompt"
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/agent/loop.py
      reason: "AgentLoop expõe is_model_warm() e executa warm-up async em background após init"

  creates:
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/scripts/repro_race_input.sh
      reason: "Script de reprodução do bug (envia stdin antes do banner terminar)"

  absorve:
    - "O-03 (indicador cold/warm do modelo)"

  forbidden:
    - "Pular verificação de hipótese sistemática (skill superpowers:systematic-debugging)"
    - "Remover streaming ou async loop"
    - "Adicionar sleep() em caminho síncrono do REPL"

  tests:
    - cmd: "bash scripts/repro_race_input.sh"
      deve_passar: true
    - cmd: "./run.sh --gauntlet --only tui"
      deve_passar: true

  acceptance_criteria:
    - "scripts/repro_race_input.sh documentado e executável"
    - "Diagnóstico escrito: hipótese 1 (prompt_toolkit tardio) testada; hipótese 2 (warm-up) testada"
    - "Mitigação escolhida e implementada"
    - "Toolbar mostra estado do modelo: cold (primeiro uso), warming (request ativo), warm (resposta chegou)"
    - "stdin drenado antes do primeiro prompt_async (ou equivalente)"
    - "Teste pexpect simula envio rápido — texto chega intacto"
    - "Gauntlet tui passa"
```

---

# Sprint UX-BUG-02 — Race de input + indicador cold/warm

## Contexto

- O usuário reportou: "se eu clicar em enviar a mensagem antes de aparecer a tela do input ela não processa".
- Oportunidade absorvida O-03: primeira request em qwen3 cold demora 5-15s; usuário acha que travou.
- ADR implícito: antes de modificar código, usar skill `superpowers:systematic-debugging` — formular hipóteses, refutar ordem.

## Problema

1. Primeiro keystroke após banner pode ser perdido (bug reportado).
2. Warm-up do modelo na primeira request é invisível ao usuário.

## Solução (dividida em 2 partes)

### Parte A — Diagnóstico sistemático

**Antes de qualquer edit**, rodar `scripts/repro_race_input.sh` (criado nesta sprint):

```bash
#!/usr/bin/env bash
# Reproduz race de input-readiness
# Envia 'oi\n/quit\n' via heredoc imediatamente após start
(
  sleep 0.1  # minimal
  printf 'oi pre-banner\n/quit\n'
) | ./run.sh 2>&1 | tee /tmp/nyx_repro_$(date +%s).log
grep -q 'oi pre-banner' /tmp/nyx_repro_*.log && echo "[ok] input chegou" || echo "[bug] input perdido"
```

**Hipóteses (ordem):**

1. `prompt_toolkit` só lê stdin quando entra no `await prompt_async()`. Keystrokes anteriores ficam no buffer tty e **são lidas no primeiro prompt**. Se `/quit` aparece mas a pergunta `oi pre-banner` é descartada: é outra coisa.
2. O warm-up async de `AgentLoop()` (load de 35 tools + memory) consome tempo antes do primeiro prompt.
3. `render_user_input` renderiza antes do prompt estar pronto, confundindo o terminal.

### Parte B — Mitigações

#### B.1 Reordenar inicialização

Mover inicializações pesadas (`cleanup_old_sessions()`, `Analytics()`, `agent._memory.index()`) para `asyncio.create_task` **após** o banner ser impresso:

```python
print(_build_banner(...))  # banner primeiro

async def _warmup():
    cleanup_old_sessions()
    # ... memory index, analytics
    app_state["model_state"] = "warm"
asyncio.create_task(_warmup())
```

#### B.2 Drenar stdin pré-prompt

Antes do primeiro `prompt_async`:

```python
import termios, tty, os
if sys.stdin.isatty():
    try:
        termios.tcflush(sys.stdin.fileno(), termios.TCIFLUSH)
    except (termios.error, OSError):
        pass  # não-crítico em CI/headless
```

**Decisão do usuário (preserva ou descarta input pré-banner):**
- Drenar = descarta keystrokes prematuros (usuário reenvia).
- Não drenar = keystrokes vão para o primeiro prompt (comportamento default).

Escolher **drenar** pois o usuário reportou "a mensagem não processa" — é mais claro descartar e deixar o prompt limpo do que enviar texto incompleto.

#### B.3 Estado do modelo

`AgentLoop` mantém `self._model_state: str = "cold"` e muda para `"warming"` quando primeiro request inicia, e `"warm"` quando primeira resposta chega:

```python
async def run(self, user_input: str) -> AgentStatus:
    self._model_state = "warming"
    if self._on_model_state:
        self._on_model_state(self._model_state)
    try:
        # ...existing run logic...
        result = await ...
        self._model_state = "warm"
        if self._on_model_state:
            self._on_model_state(self._model_state)
        return result
    except Exception:
        self._model_state = "cold"
        raise
```

Callback `on_model_state: Callable[[str], None] | None = None` no construtor.

#### B.4 Toolbar reflete estado

No `_bottom_toolbar`:
```python
state = app_state.get("model_state", "cold")
state_glyph = {"cold": "○", "warming": "◐", "warm": "●"}[state]
parts.append((f"fg:{NYX_MUTED}", f" {state_glyph} {state}"))
```

Em `cli.py`:
```python
def on_model_state(state: str) -> None:
    app_state["model_state"] = state

agent = AgentLoop(..., on_model_state=on_model_state)
```

## Comando de verificação

```bash
cd /home/andrefarias/Desenvolvimento/Nyx-Code

# 1. Script de repro existe e é executável
test -x scripts/repro_race_input.sh && echo "repro OK"

# 2. Teste pexpect (cria inline)
python -c "
import pexpect, sys
child = pexpect.spawn('./run.sh', timeout=30)
child.expect('nyx>', timeout=15)
child.sendline('oi')
child.expect('você', timeout=5)   # caixa de user_input aparece
child.sendline('/quit')
child.expect(pexpect.EOF, timeout=5)
print('pexpect OK')
" || echo "pexpect FAIL"

# 3. on_model_state wired
grep -c "on_model_state\|model_state" nyx/cli.py nyx/agent/loop.py
# esperado: >= 4

./run.sh --gauntlet --only tui
```

## Critério binário

- [ ] `scripts/repro_race_input.sh` criado e executável
- [ ] `AgentLoop._model_state` existe com transições cold→warming→warm
- [ ] Callback `on_model_state` wired em `cli.py`
- [ ] Toolbar mostra glifo e texto do estado
- [ ] `termios.tcflush` drena stdin antes do primeiro prompt
- [ ] `cleanup_old_sessions()` e `Analytics()` movidos para task async pós-banner
- [ ] Teste pexpect passa
- [ ] Gauntlet tui passa
- [ ] Commit: `fix: race de input + indicador cold/warm no toolbar`

## Guardrails anti-engodo

**NÃO marque como concluída se:**
- IA "resolveu" colocando sleep(1) no início (gambiarra).
- `on_model_state` é declarado mas nunca chamado.
- Toolbar mostra "warm" fixo sem depender do estado real.
- Script de repro só dá echo "ok" sem testar de fato.

## Validação humana

```bash
./run.sh
# Toolbar mostra "○ cold"
# enviar uma mensagem; durante streaming: "◐ warming"; depois: "● warm"

./run.sh &
echo 'oi pre-banner' | head
# sem drenar: essa linha vai para o prompt. Com drenar: descartada.
```

## Riscos

| Risco | Mitigação |
|-------|-----------|
| termios.tcflush falha em CI/headless | try/except silencioso é aceitável (não é path de produção) |
| Estado "warm" fica incorreto após erro de rede | Volta para "cold" no except |

---

*"Toda fila silenciosa é uma fonte futura de bugs." -- Gil Tene*
