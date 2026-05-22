## 0. SPEC (machine-readable)

```yaml
sprint:
  id: TUI-SIGINT-RECLAIM-07
  title: "Liberar SIGINT após bootstrap (Ctrl+C funciona durante cold-start e warmup)"
  onda: 29
  prioridade: MÉDIA
  tipo: Bugfix
  dependencias: []
  desbloqueia: []

  touches:
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/cli.py
      reason: "Restaurar handler default de SIGINT após bootstrap (atualmente fica mascarado a sessão inteira)"
      linhas_alvo: "720-740"

  forbidden:
    - "Remover completamente o masking de SIGINT (pode ter motivo de imports pesados)"
    - "Permitir Ctrl+C interromper imports do Ollama/torch (causa half-init)"
    - "Adicionar emoji"
    - "Menção a IA externa em código"

  tests:
    - cmd: "./run.sh --smoke"
      timeout: 60
      deve_passar: true

  acceptance_criteria:
    - "Ctrl+C durante warmup pós-banner (cleanup_old_sessions, memory.index) interrompe corretamente"
    - "Ctrl+C durante imports pesados (primeiros ~200ms) continua noop (proteção preservada)"
    - "Após Application montar, Ctrl+C chega ao prompt_toolkit que cancela tool inflight ou propaga"
    - "Smoke + invariantes 14/14 PASS"
```

---

# Sprint TUI-SIGINT-RECLAIM-07 — Liberar SIGINT pós-bootstrap

**Status:** PENDENTE
**Data criação:** 2026-05-21
**Modelo obrigatório:** claude-opus-4-7 (sem subagentes)

---

## Contexto do projeto (snapshot)

> - 35 tools, 67 commands. `nyx/cli.py` ~790 linhas.
> - `main()` instala `signal.signal(SIGINT, lambda *_: None)` em `cli.py:725` — neutraliza Ctrl+C global.
> - Provável motivo: evitar que Ctrl+C durante imports pesados (ollama, torch via PyVISA, prompt_toolkit init) deixe estado parcial. Mas a flag fica ativa a sessão inteira, mesmo depois do prompt_toolkit assumir o terminal.

---

## Problema

Linha 725 de `cli.py`:

```python
signal.signal(signal.SIGINT, lambda *_: None)
```

Esse handler descarta SIGINT silenciosamente — Ctrl+C não interrompe nada antes do `Application.run_async()` assumir o terminal e instalar seu próprio handler. Durante a janela "boot → banner → warmup pós-banner" (até a Application/PromptSession assumir), Ctrl+C **não funciona**.

Sintoma observado pelo Explore agent (2026-05-21): "Ctrl+C durante cold-start (warmup task, blink async) não funciona, travando o boot — usuário precisa Ctrl+\\ ou kill externo."

---

## Solução proposta

Estreitar a janela de masking: ativar o `signal.signal(SIGINT, lambda *_: None)` **apenas** durante a fase de imports pesados (se ainda necessária), e restaurar o handler default antes de devolver controle ao usuário (warmup ou prompt assume).

---

## Arquivos alvo

### `/home/andrefarias/Desenvolvimento/Nyx-Code/nyx/cli.py` (linhas ~720-740)

**Antes:**
```python
def main() -> None:
    # ... outros setups ...
    signal.signal(signal.SIGINT, lambda *_: None)
    # ... imports pesados, asyncio.run(run_repl(...))
```

**Depois:**
```python
def main() -> None:
    # ... outros setups ...

    # Mascarar SIGINT apenas durante imports pesados que não toleram interrupção.
    # Restaurado para handler default antes de asyncio.run() para permitir
    # Ctrl+C no warmup/cold-start.
    _prev_sigint = signal.signal(signal.SIGINT, lambda *_: None)
    try:
        # imports pesados aqui (se realmente necessário)
        import nyx.agent.loop  # noqa: F401
        # outros imports...
    finally:
        # Restaura handler antes do loop principal.
        # default_int_handler levanta KeyboardInterrupt — comportamento
        # padrão do Python que asyncio + prompt_toolkit já tratam.
        signal.signal(signal.SIGINT, signal.default_int_handler)

    asyncio.run(run_repl(...))
```

**Mudanças:**
- Bloco `try/finally` envolve apenas os imports pesados.
- `signal.default_int_handler` restaurado antes do `asyncio.run`.
- Comentário inline explica o motivo.

**Alternativa mínima (se imports pesados não exigem masking):** remover totalmente `signal.signal(SIGINT, lambda *_: None)`. Validar via `./run.sh --smoke` se há regressão.

---

## Diff esperado

```
~ 1 arquivo modificado
+ ~10 linhas (try/finally + comentário)
- 1 linha (signal.signal antigo)
```

---

## Comandos de verificação

```bash
# 1. Smoke
./run.sh --smoke

# 2. Ctrl+C durante warmup interrompe limpo
./run.sh &
TUI_PID=$!
sleep 0.2   # janela de warmup (cleanup_old_sessions, memory.index)
kill -INT $TUI_PID
sleep 2
kill -0 $TUI_PID 2>/dev/null && echo "FAIL: SIGINT ignorado" || echo "OK: SIGINT propagado"

# 3. Ctrl+C durante imports (primeiros 50ms) ainda mascarado (proteção)
./run.sh &
TUI_PID=$!
sleep 0.05
kill -INT $TUI_PID
sleep 1
# Se ainda rodando após 1s: imports protegidos OK.
# Se morreu: aceitar (proteção opcional — alternativa mínima).

# 4. Ctrl+C dentro do prompt_toolkit cancela tool inflight (já testado em UX-AGENCY-02)
./run.sh &
sleep 5
xdotool type "/help"   # ou outro slash que dispare task
xdotool key Return
sleep 1
xdotool key ctrl+c
# esperado: tool cancela, prompt volta livre

# 5. Invariantes + acentuação
bash scripts/sprint_invariants.sh
python3 ~/.config/zsh/scripts/validar-acentuacao.py --paths nyx/cli.py
```

---

## Critério binário de aceite

- [ ] Ctrl+C durante warmup (após bootstrap) propaga KeyboardInterrupt ou termina processo
- [ ] Ctrl+C dentro da TUI (Application ou legacy) cancela tool inflight (comportamento existente preservado)
- [ ] `./run.sh --smoke` boot ok exit 0 (boot completo sem Ctrl+C funciona)
- [ ] `bash scripts/sprint_invariants.sh` PASS 14/14
- [ ] Acentuação PT-BR rc=0
- [ ] Nenhuma violação de forbidden[]

---

## Riscos

| Risco | Mitigação |
|-------|-----------|
| Remover masking quebra import pesado (deixa half-init) | Manter masking durante imports; restaurar só depois |
| asyncio loop perder handler customizado | `default_int_handler` é o handler padrão do Python — asyncio o trata via `loop.add_signal_handler` |
| Ctrl+C no exato momento do `signal.signal()` perde sinal | Race aceitável (janela ~1µs); pior caso usuário pressiona Ctrl+C de novo |

---

*"Ctrl+C é direito do usuário, não privilégio do programa." -- princípio Unix.*
