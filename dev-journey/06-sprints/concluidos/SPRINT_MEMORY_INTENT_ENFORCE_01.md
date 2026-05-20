# SPRINT MEMORY-INTENT-ENFORCE-01 -- proxy força write_memory por intent

## 0. SPEC

```yaml
sprint:
  id: MEMORY-INTENT-ENFORCE-01
  title: "Guardrail de save_memory: classifier + retry forte + parser shell-like"
  onda: 25
  bloco: 25.0 Release (Infra > Modelo — ADR-031)
  prioridade: ALTA
  tipo: Fix de resiliência (filosofia "infra força modelo a ser bom")
  dependencias: []
  desbloqueia: [gauntlet completo gate v1.0]

  touches:
    - path: nyx/agent/intent.py
      reason: "Novo wants_save_memory(text) com regex PT-BR de gatilhos"
    - path: nyx/proxy.py
      reason: "Guardrail após IDENTITY-ENFORCE + parser shell-like fallback"

  forbidden:
    - "Forçar write_memory quando modelo não viu tool (tools=[]) — gating preserva semântica"
    - "Exceder 1 retry (padrão LANG-ENFORCE)"
```

**Status:** CONCLUIDA
**Data spec:** 2026-05-19 (terceira sessão)
**Data conclusão:** 2026-05-19 (terceira sessão, ~23h20)

---

## Contexto

Gauntlet completo 22:53 reportou CTX-11 FAIL "tool_calls=0 write_memory=False". Usuário enviou "lembra que eu uso pyenv 3.12 neste projeto" — modelo qwen2.5-coder:3b respondeu apenas com texto sem chamar write_memory. ADR-026 (Agência) exige que ações sejam VISÍVEIS no output; quando usuário pede para lembrar e modelo só fala texto, contrato quebra.

Diretriz do usuário: **"modelo não é limitante NUNCA — infra absorve"**. CTX-11 não é "comportamento do modelo intocável"; é falha de infra que pode ser corrigida com guardrail.

## Implementação (3 mecanismos sobrepostos)

### Mecanismo 1: Classifier de intent `wants_save_memory` (nyx/agent/intent.py)

Regex PT-BR cobrindo 9 padrões linguísticos:
- `lembr[ae]\s+(que|de|do|da)` — "lembra que...", "lembre disso"
- `lembre[\-\s]*se` — "lembre-se que..."
- `guarda\s+(essa|isso|esse|esta|este|isto|que)` — "guarda essa info"
- `anota\s+(ai|isso|que|aí)` — "anota aí"
- `memoriz[ae]\s+(que|isso|esse|esta)` — "memoriza que..."
- `registr[ae]\s+que` — "registra que..."
- `salv[ae]\s+(pra|para|essa|isso|isto)` — "salva pra depois"
- `n[aã]o\s+esquec[ae]\s+(que|de|do|da|disso)` — "não esquece que..."
- `fica\s+(sabendo|de\s+olho)\s+que` — "fica sabendo que..."

Verbos no PASSADO ("lembrei") ou substantivos ("guarda-chuva") **não** ativam — exige imperativo + pronome demonstrativo/conector.

### Mecanismo 2: Retry com hint forte (nyx/proxy.py)

Após response da Ollama, se intent é `tool-needed` E `wants_save_memory(last_user)` True E `write_memory` está em `body['tools']` E modelo NÃO chamou write_memory:

```python
retry_messages.append({
    "role": "user",
    "content": (
        "O usuário pediu para você LEMBRAR de algo importante. "
        "Use a tool write_memory AGORA. Responda APENAS com JSON "
        "no formato exato (sem texto antes/depois):\n"
        '```json\n'
        '{"name": "write_memory", "arguments": {'
        '"file": "<snake_case_curto>", '
        '"content": "<o fato a lembrar>", '
        '"reason": "<1 linha de motivo>"}}\n'
        '```'
    ),
})
```

Re-issue com 1 cap. Se retry chamou write_memory → usa retry. Senão → log + passa adiante.

### Mecanismo 3: Parser shell-like fallback (nyx/proxy.py)

qwen2.5-coder:3b ocasionalmente emite tool call no formato shell-like:
```
write_memory file="ambiente" content="Uso pyenv 3.12"
```

Em vez de JSON. `_extract_tool_call_from_content` agora chama `_extract_tool_call_shell_like` como segundo fallback quando JSON parse falha:

- Regex `_SHELL_ARG_PATTERN = re.compile(r'(\w+)\s*=\s*"((?:[^"\\]|\\.)*)"')` extrai pares `attr="val"`
- Requer `allowed_names` para validar que primeira palavra é tool real (evita falso positivo em texto livre)
- Loga `INFO: tool_call extraido do content (formato shell-like 'name' com N args)`

## Proof-of-work runtime

**Unit tests inline:**
- `wants_save_memory`: 10 positivos (variantes de "lembra/guarda/anota/memoriza/registra/salva/não esquece/fica sabendo") + 8 negativos (verbos passado, substantivos, frases sem intent) = **18/18 PASS**
- Parser shell-like: 7 cenários PASS (simples, 3 args, code fence, nome desconhecido bloqueado, JSON ainda funciona, sem allowed_names não dispara, texto livre)

**Runtime gauntlet:**
- `./run.sh --gauntlet --only contexto` -> **11/11 (100%) APROVADO** (era 10/11 com CTX-11 FAIL)
- CTX-11 OK com `tool_calls=1 write_memory=True`
- Tempo: 127.5s (modelo precisou de retry para o cenário, mas convergiu)
- Logs proxy mostram retry disparado: `MEMORY: usuário pediu para lembrar; modelo não chamou write_memory; retry 1x com hint`
- Logs proxy mostram parser ativo: `tool_call extraido do content (formato JSON inline)` quando o retry foi para JSON; ou `formato shell-like 'write_memory' com 3 args` quando foi para shell-like

**Restante:**
- `./run.sh --smoke` -> `boot ok`
- `bash scripts/sprint_invariants.sh` -> 14/14 PASS
- `python3 -m ruff check nyx/` -> All checks passed!
- Acentuação exit 0

## Defense in depth (3 camadas)

```
usuario: "lembra que uso pyenv 3.12"
         |
         v
  [1] wants_save_memory() detecta intent → True
         |
         v
  Modelo responde → 3 cenários possíveis:
    (a) tool_calls=[{name: write_memory, ...}] → OK direto
    (b) content = JSON inline → _extract_tool_call_from_content() pega
    (c) content = "write_memory file=X" → _extract_tool_call_shell_like() pega
         |
         v
  Se ainda assim modelo não chamou:
  [2] retry com hint forte + exemplo JSON literal
         |
         v
  [3] novo content passa pelos parsers de novo (JSON ou shell-like)
```

## Filosofia (ADR-031 + ADR-026)

Modelo qwen2.5-coder:3b pode:
- Responder só texto ("ok, vou lembrar") — capturado por (1) + (2)
- Emitir JSON tool_call — capturado por (b)
- Emitir sintaxe shell-like — capturado por (c)
- Combinar formatos errados — múltiplos parsers tentam

Infra **força** o modelo a se comportar via gating + retry + parser estendido. Modelo não é limitante.

## Anti-débito catalogado

Nenhum. Mecanismos sobrepostos cobrem os formatos observados em logs reais.

## Referências

- ADR-026 (Agência), ADR-031 (Infra > Modelo)
- `nyx/proxy.py:406-441` -- LANG-ENFORCE (padrão de retry)
- `nyx/proxy.py:443-485` -- IDENTITY-ENFORCE (padrão de retry)
- `nyx/agent/tools/write_memory.py` -- tool target
- `scripts/gauntlet/nyx_gauntlet.py:3538-3584` -- CTX-11 test

---

*"Modelo emite formato errado? Infra parsea. Modelo esquece tool? Infra força retry. Modelo não é limitante." -- MEMORY-INTENT-ENFORCE-01*
