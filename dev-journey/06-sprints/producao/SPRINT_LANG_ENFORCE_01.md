# SPRINT LANG-ENFORCE-01 — Forçar resposta em PT-BR (qwen3 ignora idioma do system_prompt)

## 0. SPEC (machine-readable)

```yaml
sprint:
  id: LANG-ENFORCE-01
  title: "Garantir resposta em PT-BR em saudações e turnos curtos — qwen3:4b responde em inglês mesmo com system PT-BR"
  onda: 23
  bloco: 23.0 Performance
  prioridade: ALTA
  tipo: Bugfix+Prompt
  dependencias: [PERF-INFERENCE-01]
  desbloqueia: []
  origem: "Achado A1 do executor PERF-INFERENCE-01: 'mesmo com system_prompt em PT-BR, qwen3:4b responde \"Hello! How can I help you today?\" para \"oi\"'. Bug central da meta 'CLI offline em PT-BR honesto'."

  touches:
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/agent/prompt.py
      reason: "system_prompt compacto reforça PT-BR como REGRA OBRIGATÓRIA (não sugestão); adiciona linha imperativa no fim do prompt"
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/proxy.py
      reason: "Opcional: post-processing detector se output é inglês quando intent=saudacao/chat; retry 1x com hint mais forte"
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/scripts/gauntlet/fixtures/perf_inference.py
      reason: "Adiciona verificação de idioma (langdetect simples) no benchmark"

  creates:
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/agent/lang_check.py
      reason: "Detector rule-based de inglês vs PT-BR (palavras-cheia + heurística). Zero ML, regex+lista."

  removes: []

  n_to_n_pairs:
    - descricao: "Regra de PT-BR aparece em prompt.py + lang_check.py + fixtures"
      paths:
        - /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/agent/prompt.py
        - /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/agent/lang_check.py
        - /home/andrefarias/Desenvolvimento/Nyx-Code/scripts/gauntlet/fixtures/perf_inference.py

  forbidden:
    - "Substituir resposta inglesa por tradução automatizada (perde fidelidade)"
    - "Retry infinito se modelo insiste em inglês (cap em 1 retry)"
    - "Detector que classifica errado nomes próprios em inglês ('Python', 'GitHub') como response-in-english"
    - "Mudar modelo padrão por causa disso (qwen3:4b é escolha do usuário)"
    - "Emoji"

  tests:
    - cmd: "./venv/bin/python -c 'from nyx.agent.lang_check import is_pt_br; print(is_pt_br(\"olá tudo bem\"), is_pt_br(\"Hello there\"))'"
      timeout: 10
      deve_passar: true
      nota: "Deve imprimir True False"
    - cmd: "./run.sh --gauntlet --only proxy"
      timeout: 300
      deve_passar: true
    - cmd: "./venv/bin/python scripts/gauntlet/fixtures/perf_inference.py --check-lang"
      timeout: 600
      deve_passar: true
      nota: "Verifica que 100% das respostas a saudações são em PT-BR"
    - cmd: "bash scripts/sprint_invariants.sh"
      timeout: 60
      deve_passar: "FAIL_AFTER <= FAIL_BEFORE"

  acceptance_criteria:
    - "Resposta a 'oi', 'olá', 'hello' (sim, em inglês de input!), 'bom dia' SEMPRE em PT-BR"
    - "lang_check.is_pt_br('olá tudo bem') == True; is_pt_br('Hello there') == False"
    - "fixture perf_inference.py grava 'lang_pt_br_rate' >= 95% nas 7 perguntas-tipo"
    - "system_prompt compacto agora tem linha tipo: 'RESPONDA EM PORTUGUÊS BRASILEIRO. Nunca em inglês.'"
    - "Se modelo responde em inglês em intent=saudacao/chat: proxy tenta retry 1x com hint reforçado"
    - "Após retry, se ainda em inglês: passa adiante (não trava o agent)"
    - "Não regride PERF-INFERENCE-01: 'oi' continua respondendo em P50 <= 6s (com retry pode subir até 8s)"
    - "Gauntlet proxy + rapido 100%"
    - "PT-BR; zero emoji; zero menção a IA"
```

---

**Status:** PENDENTE
**Data criação:** 2026-05-16
**Modelo obrigatório:** claude-opus-4-7 (sem subagentes)
**Origem:** achado colateral de PERF-INFERENCE-01

---

# Sprint LANG-ENFORCE-01

## Problema

PERF-INFERENCE-01 ficou em 4.67s mas o modelo responde:
```
nyx> oi
Hello! How can I help you today?
```

Mesmo com system_prompt em PT-BR ("Sou Nyx, agente de código local. PT-BR direto..."). Causas plausíveis:
1. qwen3:4b foi treinado predominantemente em inglês e ignora idioma do system para saudações curtas.
2. Tokens de saudação curta em inglês têm probabilidade default mais alta.
3. system_prompt compacto (~79 tokens) talvez seja insuficiente pra fixar idioma.

## Solução em 3 camadas

### Camada 1 — Prompt reforçado

```python
def build_system_prompt(..., compact=False):
    if compact:
        return (
            "Sou Nyx, agente de código local. "
            "RESPONDA SEMPRE EM PORTUGUÊS BRASILEIRO. Nunca em inglês. "
            "Frases curtas. Zero emoji. "
            f"Diretório: {project_root}."
        )
```

### Camada 2 — Detector de idioma (`nyx/agent/lang_check.py`)

```python
"""Detector rule-based pt-BR vs en."""
import re

PT_BR_MARKERS = re.compile(
    r'\b(é|você|não|sim|olá|tudo bem|obrigad|por favor|aqui|aí|'
    r'estou|estamos|posso|deve|preciso|fizer|qualquer|também)\b',
    re.I
)
EN_MARKERS = re.compile(
    r'\b(the|is|are|hello|hi|today|help|how|what|can|you|with|please|here|there)\b',
    re.I
)

def is_pt_br(text: str) -> bool:
    """True se texto tem mais marcadores PT-BR que EN, ou se tem acentos."""
    if not text or len(text.strip()) < 3:
        return True  # vazio/curto demais: assume ok
    if re.search(r'[áéíóúâêîôûãõàèç]', text, re.I):
        return True  # tem acento PT-BR
    pt = len(PT_BR_MARKERS.findall(text))
    en = len(EN_MARKERS.findall(text))
    return pt >= en
```

### Camada 3 — Retry no proxy

```python
# proxy.py handle_chat após receber resposta
result = ollama_to_openai(data, model)
content = result["choices"][0]["message"].get("content", "")
if intent in ('saudacao', 'chat') and content and not is_pt_br(content):
    logger.info("Resposta em ingles detectada; retry com hint reforcado")
    ollama_body["messages"].append({
        "role": "user",
        "content": "Responda em portugues brasileiro, nao em ingles."
    })
    # 1 retry com timeout shorter
    async with session.post(f"{OLLAMA_URL}/api/chat", json=ollama_body) as retry_resp:
        if retry_resp.status == 200:
            data = await retry_resp.json()
            result = ollama_to_openai(data, model)
```

## Verificação

```bash
./run.sh
# nyx> oi
# Deve responder em PT-BR (algo como "Olá! Em que posso ajudar?")
```

---

*"Idioma é a primeira porta de acolhimento; resposta errada quebra confiança." -- princípio gamedesigner aplicado a CLI multilíngue*
