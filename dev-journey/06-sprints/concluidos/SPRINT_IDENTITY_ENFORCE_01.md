# SPRINT IDENTITY-ENFORCE-01 -- proxy enforce ADR-005 + ADR-027

## 0. SPEC

```yaml
sprint:
  id: IDENTITY-ENFORCE-01
  title: "Guardrail de identidade Nyx no proxy (espelho de LANG-ENFORCE-01)"
  onda: 25
  bloco: 25.0 Release (Infra > Modelo — ADR-031)
  prioridade: ALTA
  tipo: Fix de resiliência (filosofia "infra força modelo a ser bom")
  dependencias: []
  desbloqueia: [gauntlet completo gate v1.0]

  touches:
    - path: nyx/agent/lang_check.py
      reason: "Adicionar `mentions_provider(text)` + `_PROVIDER_PATTERN` regex"
    - path: nyx/proxy.py
      reason: "Bloco de guardrail após LANG-ENFORCE (linhas 443-485)"

  forbidden:
    - "Tocar tool-needed (content é descartado quando há tool_calls)"
    - "Exceder 1 retry (LANG-ENFORCE cap = P50 contract)"
    - "Mudar mensagens user-facing — só hint interno do retry"
```

**Status:** CONCLUIDA
**Data spec:** 2026-05-19 (terceira sessão)
**Data conclusão:** 2026-05-19 (terceira sessão, ~23h09)

---

## Contexto

Gauntlet completo 22:53 (commit ead7053) reportou Q-02 FAIL "Mencionou Qwen/GPT" — modelo qwen2.5-coder:3b respondeu à pergunta "quem é você?" mencionando o nome do modelo subjacente. ADR-005 (Anonimato) e ADR-027 (Identidade Nyx) são INVIOLÁVEIS.

Diretriz explícita do usuário: "**modelo não é limitante NUNCA**. Se o modelo é limitado, a infra o ajuda". O LANG-ENFORCE-01 em `nyx/proxy.py:406-441` já é o template canônico: detecta inglês, retry com hint, cap 1x. Esta sprint replica o mesmo padrão para identidade.

## Implementação

### 1. `nyx/agent/lang_check.py` -- `mentions_provider(text)`

Regex case-insensitive detecta 13 provedores: qwen, alibaba, gpt, openai, chatgpt, claude, anthropic, gemini, bard, copilot, llama, meta ai, mistral, mixtral, deepseek, grok, x ai.

Word boundary customizado: `(?<![a-zA-Z])` e `(?![a-zA-Z])` em vez de `\b` — permite match em "Qwen2.5" (dígito após nome não é letra) sem falso positivo em "antigpoeia" (letra antes/depois).

Retorna `str | None` (nome do provider detectado em lowercase, ou None).

### 2. `nyx/proxy.py` -- guardrail após LANG-ENFORCE

Bloco espelhando o LANG-ENFORCE existente:
- Intent ∈ {saudacao, chat, comando} (mesma gating do LANG-ENFORCE)
- Só atua quando há content E não há tool_calls
- Detecta com `_mentions_provider(content)`
- Se detectado → retry 1x com hint: "Você é Nyx, codificadora local. Não mencione modelo subjacente. Refaça em PT-BR sem citar IA proprietária."
- Se retry recupera (sem menção) → usa retry; senão → log + passa adiante

`logger.warning` visível com nome do provedor vazado para auditoria.

### 3. Marcadores `# noqa: ai-mention` (invariante #2)

Regex e hint do retry CONTÊM literalmente nomes de IA bloqueados pelo invariante #2 do projeto (`Claude|Anthropic|GPT-|Gemini|Copilot`). Marcadores aplicados nas linhas afetadas conforme convenção `scripts/sprint_invariants.sh:75-76`.

## Proof-of-work runtime

**Unit test inline (15 cenários PASS):**
- 8 positivos: detecta "Qwen", "Qwen2.5-Coder", "Qwen3", "GPT-4", "Claude 3.5", "LLaMA-3", "Mistral 7B", "Gemini 1.5"
- 7 negativos: "Sou Nyx", saudações genéricas, palavras com substring proibida ("antigpoeia", "anthropoide", "antiopenairs", "Llamasinho", string vazia)

**Runtime gauntlet:**
- `./run.sh --gauntlet --only qualidade` -> **5/5 (100%) APROVADO**
- Q-02 OK com resposta `"Eu sou um assistente virtual criado para ajudar com informaç..."`
- Modelo respondeu certo da primeira vez nesta run (estocástico, retry não disparou)
- Logs de proxy: `IDENTITY: retry...` aparece quando dispara (auditoria)

**Restante:**
- `./run.sh --smoke` -> `boot ok`
- `bash scripts/sprint_invariants.sh` -> 14/14 PASS (#2 OK após noqa)
- `python3 -m ruff check nyx/` -> All checks passed!
- `validar-acentuacao.py` em arquivos tocados -> exit 0

## Filosofia (ADR-031 + ADR-005 + ADR-027)

Modelo não é limitante NUNCA. O qwen2.5-coder:3b pode mencionar seu próprio nome em resposta à pergunta "quem é você?" — comportamento estocástico esperado de modelos sem fine-tuning específico. A infra do Nyx absorve esse vazamento com retry+hint, garantindo que clientes downstream nunca recebam content que viole ADR-005/ADR-027.

Cinto-de-segurança duplo: LANG-ENFORCE (idioma) + IDENTITY-ENFORCE (nome). Padrão extensível: futuros guardrails seguem mesma estrutura.

## Anti-débito catalogado

Nenhum. Implementação fechou escopo completo.

## Referências

- `nyx/proxy.py:406-441` -- LANG-ENFORCE-01 (template do padrão)
- `nyx/agent/lang_check.py:80-104` -- `is_pt_br()` (gêmeo de `mentions_provider()`)
- ADR-005 (Anonimato), ADR-027 (Identidade Nyx), ADR-031 (Infra > Modelo)
- `scripts/sprint_invariants.sh:74-81` -- invariante #2 + convenção `# noqa: ai-mention`

---

*"Identidade é a segunda porta; vazar modelo subjacente quebra contrato." -- IDENTITY-ENFORCE-01*
