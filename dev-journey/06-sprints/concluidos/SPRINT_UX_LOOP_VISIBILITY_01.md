# SPRINT UX-LOOP-VISIBILITY-01 — Estado warming visível durante request

## 0. SPEC (machine-readable)

```yaml
sprint:
  id: UX-LOOP-VISIBILITY-01
  title: "Tornar o estado ◐ warming visível ao usuário enquanto o agente processa request"
  onda: 23
  bloco: 23.4 Gamedesigner
  prioridade: MÉDIA
  tipo: Feature+UX
  dependencias: [UX-BUG-02B]
  desbloqueia: []
  origem: "Validação visual de UX-BUG-02B (2026-05-16) mostrou que ◐ warming existe em app_state mas nunca aparece na toolbar — prompt-toolkit não renderiza bottom_toolbar enquanto prompt_async() está fora do laço. Sprint nova para fechar o gap (regra: nenhum débito fica para trás)."

  touches:
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/cli.py
      reason: "Spinner 'pensando...' enriquecido com label de estado, OU prompt_session.app.invalidate() forçando refresh durante warming"
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/agent/output.py
      reason: "Helper para construir label de estado contextual (combine glyph + duração)"

  creates: []
  removes: []

  n_to_n_pairs:
    - descricao: "Estado warming agora aparece tanto em app_state[model_state] (UX-BUG-02B) quanto no spinner contextual"
      paths:
        - /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/cli.py
        - /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/agent/output.py

  forbidden:
    - "Quebrar UX-BUG-02B (toolbar cold/warm continua funcional)"
    - "Spinner com FPS abusivo (>15fps gasta CPU sem ganho perceptual)"
    - "Estado preso em warming após exceção (já tratado por UX-BUG-02B, mas validar)"
    - "Emoji"

  tests:
    - cmd: "./run.sh --gauntlet --only tui"
      timeout: 300
      deve_passar: true
    - cmd: "./run.sh --gauntlet --only rapido"
      timeout: 300
      deve_passar: true
    - cmd: "manual: rodar Nyx; mandar 'oi'; observar texto de status durante 5-20s da espera"
      deve_passar: "usuário vê 'pensando...' OU 'aquecendo modelo...' OU '◐ warming Ns' visível, não tela vazia"

  acceptance_criteria:
    - "Durante request (entre Enter e primeira resposta), usuário vê label que indica estado warming"
    - "Label inclui glifo ◐ OU duração crescente OU texto explicativo em PT-BR"
    - "Transição cold→warming→warm continua coerente com ADR-025"
    - "Após resposta, toolbar volta para ● warm (UX-BUG-02B inalterado)"
    - "Em caso de exceção/timeout, estado volta para ○ cold (regressão zero)"
    - "PT-BR acentuado, zero emoji, zero menção a IA"
    - "Smoke + invariants passam"
```

---

**Status:** PENDENTE
**Data criação:** 2026-05-16
**Modelo obrigatório:** claude-opus-4-7 (sem subagentes)
**Origem:** achado colateral de UX-BUG-02B (validação visual). Anti-débito.

---

# Sprint UX-LOOP-VISIBILITY-01

## Contexto

UX-BUG-02B implementou cold/warming/warm corretamente no AgentLoop e gravou em `app_state["model_state"]`. Mas o `bottom_toolbar` do prompt-toolkit só é renderizado quando `prompt_async()` está ativo. Entre o Enter do usuário e o retorno do agent, prompt-toolkit está fora do estado de input — toolbar desaparece da tela. O usuário NÃO vê `◐ warming` na prática.

Esse gap quebra ADR-025 §"Tempos de feedback" para o estágio 2 (tool start) e 4 (streaming). O spinner `pensando...` cobre parcialmente, mas não nomeia o estado.

## Duas estratégias possíveis (escolher uma na implementação)

### Estratégia A — Spinner enriquecido

Spinner muda de label durante o ciclo:
- 0-3s: `aquecendo modelo...` (◐ warming explícito)
- 3-10s: `pensando...` (cold→warm, mid-flight)
- 10s+: `pensando... (15s)` (com cronômetro)

Toolbar continua `○ cold` ou `● warm` baseada em `_model_state` — mas o usuário tem feedback durante o request via spinner.

### Estratégia B — Toolbar live via app.invalidate()

Forçar refresh da toolbar via `prompt_session.app.invalidate()` em loop de fundo enquanto o agent executa. Tecnicamente: criar uma task asyncio que faz `app.invalidate()` a cada 500ms enquanto `_model_state == "warming"`. Toolbar mostra `◐ warming` em tempo real.

**Trade-off:** Estratégia A é mais simples e não mexe em internals do prompt-toolkit. Estratégia B é mais coerente com ADR-025 §"Estágio 5: footer atualizado" mas tem risco de race.

Recomendação: Estratégia A primeiro; se ADR-025 exigir paridade visual completa, evoluir para B.

## Verificação manual

```bash
./run.sh
# Mandar "diga um numero"
# Observar tela DURANTE os 10-20s antes da resposta:
#   - Existe label de estado? Sim/Não
#   - Label inclui ◐ ou "aquecendo" ou cronômetro?
#   - Toolbar reapareceu com ● warm após resposta?
```

## Riscos

| Risco | Mitigação |
|---|---|
| Estratégia B causa flicker no terminal | Limitar invalidate() a 2fps; testar em xterm + gnome-terminal |
| Estratégia A diverge de toolbar (label spinner ≠ glifo toolbar) | Documentar contrato: spinner mostra warming, toolbar mostra cold/warm |
| Cronômetro perdido se sleep do agent é longo | Tempo decorrido vem de `time.monotonic()` no início do request |

---

*"O que o usuário não vê, não aconteceu." -- princípio de gamedesign aplicado a CLI*
