# SPRINT SLASH-BYPASS-AUDIT-01 — Confirmar que /comandos não passam pelo LLM

## 0. SPEC (machine-readable)

```yaml
sprint:
  id: SLASH-BYPASS-AUDIT-01
  title: "Auditoria + teste no Gauntlet: /help, /memory, /quit etc. são interceptados pelo CLI ANTES do proxy/LLM"
  onda: 23
  bloco: 23.0 Performance
  prioridade: MÉDIA
  tipo: Audit+Test
  dependencias: [PERF-INFERENCE-01]
  desbloqueia: []
  origem: "Achado A2 do executor PERF-INFERENCE-01: '/help demorou 4.5s no benchmark via POST direto no proxy. CLI real deve interceptar antes do LLM mas precisa validar'. Sem isso, claim de '/help em <=2s' é meta-mentira."

  touches:
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/scripts/gauntlet/nyx_gauntlet.py
      reason: "Adicionar fase 'slash_bypass' que valida que /help, /memory, /tools, /quit retornam em <500ms"
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/cli.py
      reason: "Se grep revelar que algum /command vai parar no LLM, fix; senão só audit"

  creates: []

  removes: []

  n_to_n_pairs: []

  forbidden:
    - "Modificar caminho de /command em produção sem evidência de regressão"
    - "Adicionar latência artificial pra 'simular' bypass"
    - "Documentar bypass como existente sem evidência via teste real"
    - "Emoji"

  tests:
    - cmd: "grep -n 'startswith(\"/\")' nyx/cli.py | head -5"
      timeout: 10
      deve_passar: true
      nota: "Localizar o ponto onde /commands são interceptados"
    - cmd: "./run.sh --gauntlet --only slash_bypass"
      timeout: 120
      deve_passar: true
      nota: "Fase nova que mede latência de cada /command"
    - cmd: "./run.sh --gauntlet --only rapido"
      timeout: 300
      deve_passar: true
    - cmd: "bash scripts/sprint_invariants.sh"
      timeout: 60
      deve_passar: "FAIL_AFTER <= FAIL_BEFORE"

  acceptance_criteria:
    - "Audit: grep documentado mostrando onde /commands são interceptados em cli.py (handle_command? branch dedicado?)"
    - "Fase nova 'slash_bypass' no Gauntlet testa /help, /memory, /tools, /quit, /theme"
    - "Cada /command testado retorna em <500ms (sem LLM call)"
    - "Se descobrir que algum /command está sendo enviado ao LLM erroneamente: fix imediato"
    - "Relatório curto em comentário do commit: 'audit: N commands testados, M com bypass OK, K corrigidos'"
    - "Gauntlet rapido 100% (sem regressão)"
    - "PT-BR; zero emoji; zero menção a IA"
```

---

**Status:** CONCLUIDA
**Hash:** PENDING
**Data criação:** 2026-05-16
**Data conclusão:** 2026-05-16
**Modelo obrigatório:** claude-opus-4-7 (sem subagentes)
**Origem:** achado colateral de PERF-INFERENCE-01

## Resultado do audit

Bypass confirmado em `nyx/cli.py:417` -- branch `if user_input.startswith("/"):` chama `handle_command()` (em `nyx/agent/commands/_dispatcher.py:36`) que retorna string ou sentinela (`__quit__`, `__clear__`, etc.) sem qualquer chamada ao proxy/Ollama. Bug colateral: nenhum -- todos os 5 `/commands` testados respeitam o bypass.

Fase nova `slash_bypass` em `scripts/gauntlet/nyx_gauntlet.py` mede latência direta de:

| Feature | Comando | Latência | len(result) |
|---------|---------|----------|-------------|
| SB-01 | /help | 0 ms | 711 |
| SB-02 | /memory | 2 ms | 99 |
| SB-03 | /tools | 17 ms | 3154 |
| SB-04 | /quit | 0 ms | 8 |
| SB-05 | /theme | 2 ms | 487 |

Todos < 500 ms (critério do spec). Gauntlet `slash_bypass` 5/5 OK.

---

# Sprint SLASH-BYPASS-AUDIT-01

## Contexto

O benchmark de PERF-INFERENCE-01 mediu `/help` em 4.5s pelo POST direto no proxy. Mas o fluxo REAL no CLI é diferente: o usuário digita `/help` e o `handle_command` em `nyx/agent/commands/*` deveria interceptar ANTES de qualquer chamada ao LLM.

Sem evidência via teste, é palpite. Sprint resolve isso: audit + teste no Gauntlet.

## Verificação inicial via grep

```bash
grep -n 'startswith("/")' nyx/cli.py
grep -rn 'handle_command' nyx/
```

Expectativa: o REPL tem branch tipo:
```python
if user_input.startswith("/"):
    result = handle_command(user_input, project_root)
    # ... nunca chama LLM
    continue
```

Se confirmar via grep e teste: bypass está correto, só adiciona teste no Gauntlet para garantir contra regressão.

Se descobrir que algum /command está caindo no LLM (bug): fix e teste.

## Fase Gauntlet nova

```python
# scripts/gauntlet/nyx_gauntlet.py, adicionar fase
def _phase_slash_bypass(self):
    """Mede latência de /commands; deve ser <500ms (zero LLM)."""
    cases = ["/help", "/memory", "/tools", "/quit", "/theme"]
    for cmd in cases:
        # invocar via stdin do REPL ou via direct handle_command
        t = time.monotonic()
        result = handle_command(cmd, project_root=str(PROJECT_ROOT))
        dt = time.monotonic() - t
        ok = dt < 0.5 and result is not None
        self._add(f"S-{cmd}", f"slash bypass {cmd}", "slash_bypass", ok, dt)
```

---

*"O que não está testado, está só prometido." -- princípio de evidência aplicado a CLI*
