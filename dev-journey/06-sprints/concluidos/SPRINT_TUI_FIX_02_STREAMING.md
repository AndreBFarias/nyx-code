## 0. SPEC (machine-readable)

```yaml
sprint:
  id: TUI-FIX-02
  title: "Fim da resposta duplicada (streaming + render final)"
  touches:
    - path: nyx/cli.py
      reason: "Remover print(status.summary) quando streaming ativo emitiu a mesma resposta"
    - path: nyx/agent/loop.py
      reason: "Clarificar contrato: se streaming=True e on_token consumiu tokens, SessionStatus.summary só serve pra logs, não pra re-render"
  n_to_n_pairs:
    - "Se cli ativou streaming, NÃO usa output('nyx', status.summary); SE não ativou streaming, AÍ usa summary"
  forbidden:
    - "Deixar status.summary ser impresso duas vezes"
    - "Quebrar o modo não-streaming (onde summary é a única fonte)"
    - "Silenciar summary em situações de erro (ERROR, MAX_ITERATIONS) -- aí precisa mostrar"
  tests:
    - cmd: "./run.sh --gauntlet --only interface"
      timeout: 60
    - cmd: "manual: ./run.sh -- digitar 'Olá' e contar quantas vezes a resposta aparece (esperado: 1)"
      timeout: 30
  acceptance_criteria:
    - "Resposta da Nyx aparece UMA vez no terminal"
    - "Spinner 'pensando...' some no primeiro token recebido"
    - "Em MAX_ITERATIONS ou ERROR, o summary ainda aparece (pois não houve streaming)"
    - "Header 'Nyx\\n───' aparece antes do streaming, não depois"
    - "Após resposta, linha em branco + novo footer + novo prompt"
```

---

# Sprint TUI-FIX-02 -- Resposta única (sem duplicação)

**Status:** CONCLUIDA (header corrigido em MASTER-CLEANUP-02 2026-05-20; presença em concluidos/ implica CONCLUIDA conforme convenção do projeto)
**Data:** 2026-04-17
**Prioridade:** CRÍTICA
**Tipo:** Fix
**Dependências:** --
**Desbloqueia:** TUI-FIX-07

---

## Problema / Contexto

Screenshot 9 do usuário mostra:
```
  Nyx
  ───
Oi. Tudo bem. O que você precisa hoje?
  Nyx: Oi. Tudo bem. O que você precisa hoje?
```

A resposta aparece **duas vezes** no mesmo turno. Causa raiz (auditada em `nyx/cli.py:393-410`):

```python
# on_token callback (streaming)
def on_token(token: str) -> None:
    sys.stdout.write(token)  # primeira impressão

# ...

# Após run() completar
status = await agent.run(user_input)

if status.summary:
    if use_rich and output:
        output("nyx", status.summary)  # SEGUNDA impressão da mesma coisa
    else:
        print(f"\n{PRIMARY}{status.summary}{NC}\n")
```

O loop em `nyx/agent/loop.py:206-226` preenche `status.summary = content` com a resposta final quando termina sem tool calls -- mesma coisa que já foi streamada.

## Implementação

### Fase 1 -- Flag de streaming ativo

Em `cli.py`, adicionar flag `streaming_printed` que o `on_token` seta ao receber o primeiro token:

```python
_streaming_state = {"printed": False}

def on_token(token: str) -> None:
    _stop_spinner()
    _streaming_state["printed"] = True
    sys.stdout.write(token)
    sys.stdout.flush()
```

### Fase 2 -- Guarda na render final

Trocar o bloco `if status.summary:` por:

```python
if status.summary:
    if _streaming_state["printed"] and status.state == SessionState.DONE:
        # Streaming já imprimiu; só quebra linha
        print()
    else:
        # Sem streaming (ex: ERROR, MAX_ITERATIONS, ou streaming=False)
        if use_rich and output:
            output("nyx", status.summary)
        else:
            print(f"\n{PRIMARY}{status.summary}{NC}\n")
```

### Fase 3 -- Resetar flag por turno

Antes de cada `agent.run(user_input)`:

```python
_streaming_state["printed"] = False
```

### Fase 4 -- Verificar header

`render_assistant_start()` chama antes do streaming; `render_assistant_end()` depois. Garantir que não está imprimindo o texto completo também.

## Verificação

```bash
./run.sh
# digitar: "Olá, tudo bem?"
# contar: "Olá" aparece 1 vez na resposta
# digitar: "lista arquivos .py em nyx/agent/"
# contar: descrição da resposta aparece 1 vez

# testar --no-stream
./run.sh --no-stream
# digitar algo, ver que ainda aparece resposta (via summary, não via streaming)

./run.sh --gauntlet --only interface
```

- [ ] Resposta DONE aparece 1 vez em streaming
- [ ] Resposta ERROR aparece 1 vez (via summary)
- [ ] Resposta MAX_ITERATIONS aparece 1 vez (via summary)
- [ ] --no-stream: resposta aparece 1 vez (via summary)
- [ ] Header `Nyx\n───` aparece só 1 vez por turno
- [ ] Gauntlet interface passa

---

*"O que se diz uma vez já foi dito." -- Wittgenstein*
