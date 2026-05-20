# SPRINT GAUNTLET-TOOLS-DESC-MATCH-01 -- proxy normaliza name corrompido por modelo qwen2.5-coder:3b

## 0. SPEC

```yaml
sprint:
  id: GAUNTLET-TOOLS-DESC-MATCH-01
  title: "Cross-validation de tool name no fallback JSON inline do proxy"
  onda: 25
  bloco: 25.0 Release (anti-débito materializado a partir do MASTER L825)
  prioridade: ALTA
  tipo: Fix de resiliência (infra > modelo, ADR-031)
  dependencias: [RUFF-CLEAN-NYX-01, GAUNTLET-ACENTUACAO-FIX-01]
  desbloqueia: [gauntlet completo gate v1.0]

  touches:
    - path: nyx/proxy.py
      reason: "Cross-validar tool name extraído de JSON inline contra allowed_tool_names do request"
      blocos:
        - "L214-263: _extract_tool_call_from_content ganha parâmetro allowed_names + lógica de normalização"
        - "L266-271: ollama_to_openai ganha parâmetro allowed_tool_names"
        - "L284-288: ollama_to_openai propaga allowed_names ao fallback"
        - "L392-403: callsite extrai allowed_tool_names de body['tools']"

  creates: []
  removes: []

  forbidden:
    - "Modificar payload do Ollama nativo (tool_calls vem correto, só fallback inline corrompe)"
    - "Alterar fixture do gauntlet (a falha era da produção, não do teste)"
    - "Mascarar bug do modelo silenciosamente — logger.warning é obrigatório"
```

---

**Status:** CONCLUIDA
**Data spec:** 2026-05-19 (segunda sessão)
**Data conclusão:** 2026-05-19 (segunda sessão, ~22h48)
**Modelo execução:** claude-opus-4-7

---

## Investigação (caminho até o diagnóstico)

Usuário pediu "investigar antes de fixar". Sequência:

1. **Mapeamento de testes falhos**: T-01/T-03/T-06/T-08/T-09 da fase TOOLS do gauntlet. Padrão: "Esperava `Read`, recebeu `['Read Lê arquivo']`".
2. **Análise do código do gauntlet**: fixture envia tool_spec correto `{"name": "Read", "description": "Lê arquivo", ...}`. Match `expected_tool in tool_names` exato.
3. **Análise do proxy**: `_extract_tool_call_from_content` parseia JSON do content quando Ollama não emite `tool_calls` nativo. Preserva `name` literal do JSON.
4. **Análise dos logs `logs/proxy.log`**: descoberto literal `"name": "Read Le arquivo"` direto do `content` do modelo. **Modelo alucina o name**.
5. **Estatística**: 13 corrompidos vs 128 corretos no log atual (~9% taxa de falha). Padrão: Ollama nativo sempre vem correto; só corrompe quando modelo emite JSON livre no content (fallback path).

## Hipóteses descartadas

- **Fixture do gauntlet mal-formada**: descartada — gauntlet envia `function.name` e `function.description` separados, formato OpenAI canônico.
- **Proxy concatenando**: descartada — logs mostram corrupção já no `content` cru do modelo, antes de qualquer processamento do proxy.
- **OOM transitório**: descartada — bug aparece em 3 timestamps diferentes (22:05, 22:18, 22:36), e há horários com OOM SEM o bug e horários sem OOM COM o bug.
- **Custom prompt resolveria**: descartada — modelo é estocástico (T-05 veio correto em uma execução e o usuário pediu cinturão definitivo).

## Implementação

Cross-validation em 3 mudanças mínimas:

### 1. `_extract_tool_call_from_content` ganha `allowed_names`

```python
def _extract_tool_call_from_content(text: str, allowed_names: list[str] | None = None) -> dict | None:
    ...
    if allowed_names and name not in allowed_names:
        first_token = name.split()[0] if name.split() else ""
        if first_token and first_token in allowed_names:
            logger.warning(
                "tool name corrompido pelo modelo normalizado: %r -> %r",
                name,
                first_token,
            )
            name = first_token
    ...
```

Comportamento:
- name está em `allowed_names`: passa direto
- name corrompido + primeiro token bate: normaliza + log WARN
- name desconhecido (nem com cross-val resolve): preserva literal (graceful debug)
- `allowed_names=None`: comportamento legacy (preserva tudo)

### 2. `ollama_to_openai` propaga

```python
def ollama_to_openai(
    data: dict,
    model: str,
    has_tools_request: bool = False,
    allowed_tool_names: list[str] | None = None,
) -> dict:
    ...
    extracted = _extract_tool_call_from_content(content, allowed_names=allowed_tool_names)
```

### 3. Callsite extrai do request

```python
has_tools_request = bool(body.get("tools"))
allowed_tool_names = [
    t.get("function", {}).get("name", "")
    for t in body.get("tools", [])
    if isinstance(t, dict)
]
allowed_tool_names = [n for n in allowed_tool_names if n]
result = ollama_to_openai(
    data,
    model,
    has_tools_request=has_tools_request,
    allowed_tool_names=allowed_tool_names or None,
)
```

## Proof-of-work runtime

**Unit test inline (7 cenários, todos PASS):**
1. name puro sem cross-val: preserva
2. name corrompido + cross-val: `"Read Lê arquivo"` -> `"Read"` + WARN
3. name corrompido sem cross-val: preserva literal (legacy)
4. name puro + cross-val: passa direto (sem WARN)
5. name desconhecido: preserva literal (debug visibility)
6. code-fence + corrompido: `"Bash Executa comando"` -> `"Bash"` (parser de code-fence intocado)
7. Glob corrompido: `"Glob Busca arquivos"` -> `"Glob"`

**Runtime gauntlet:**
- `./run.sh --gauntlet --only tools` -> **6/6 (100%) APROVADO** (era 1/6 com 5 FAIL)
- Logs do proxy confirmam cross-val ativa:
  ```
  WARNING: tool name corrompido pelo modelo normalizado: 'Read Lê arquivo' -> 'Read'
  WARNING: tool name corrompido pelo modelo normalizado: 'Write Cria arquivo' -> 'Write'
  WARNING: tool name corrompido pelo modelo normalizado: 'Bash Executa comando' -> 'Bash'
  WARNING: tool name corrompido pelo modelo normalizado: 'Glob Busca arquivos' -> 'Glob'
  WARNING: tool name corrompido pelo modelo normalizado: 'Grep Busca texto' -> 'Grep'
  ```

**Restante:**
- `./run.sh --smoke` -> `boot ok`
- `bash scripts/sprint_invariants.sh` -> 14/14 PASS
- `python3 -m ruff check nyx/` -> All checks passed!
- `validar-acentuacao.py --paths nyx/proxy.py` -> exit 0

## Filosofia (link com ADR-031)

Esta sprint é validação empírica adicional da tese **"infra resiliente > modelo perfeito"** (ADR-031 amendado pela INFRA-MODEL-AGNOSTIC-01). O modelo qwen2.5-coder:3b alucina o `name` 9% das vezes; a infra do Nyx absorve sem repassar ao cliente. Sem essa camada, qualquer cliente OpenAI-compatível downstream do proxy receberia tool_calls com `name="Read Lê arquivo"` e quebraria sua lógica de despacho.

## Anti-débito catalogado

Nenhum. Implementação fechou o escopo completo.

## Referências

- `MASTER.md L825` — antecipação do anti-débito
- `nyx/proxy.py:282-300` — caminho do tool_calls nativo (preservado)
- `nyx/proxy.py:214-269` — caminho do fallback JSON inline (corrigido)
- `dev-journey/03-decisions/ADR_031_*.md` — filosofia infra > modelo
- `project_proxy_think.md` — memória sobre proxy think adaptativo

---

*"Quando o modelo alucina, infra resiliente não repassa erro — corrige." -- GAUNTLET-TOOLS-DESC-MATCH-01*
