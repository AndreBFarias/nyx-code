## 0. SPEC (machine-readable)

```yaml
sprint:
  id: MODEL-NATIVE-TOOLCALL-PIPELINE-01
  numero_master: 446
  title: "Usar tool-calling NATIVO do Ollama quando o modelo suporta, em vez de suprimi-lo via few-shot no prompt"
  onda: 49
  prioridade: ALTA
  tipo: Infra/Arquitetura
  dependencias: []
  desbloqueia: [MODEL-BAKEOFF-CANDIDATES-01 (re-run com nativo), MODEL-MANAGER-CORE-01, ADR-036]

  touches:
    - path: nyx/agent/prompt.py
      reason: "few-shot do formato JSON-no-content (linhas ~105-135) empurra modelos capazes de nativo para o formato texto; condicionar ao modelo NÃO suportar nativo"
    - path: nyx/proxy.py
      reason: "linha ~517 so extrai do content quando tool_calls nativo vem vazio; garantir que o nativo, quando presente, e usado direto (ja e) e não competir com o prompt"
  creates: []
  removes: []

  forbidden:
    - "Quebrar o caminho do qwen2.5-coder:3b (baseline sem nativo) -- ele DEPENDE do few-shot + resgate; o comportamento atual e o fallback quando model_supports_native_toolcall e False"
    - "Efetivar troca de modelo (não mexer em DEFAULT_MODEL)"
    - "Remover o resgate _extract_tool_call_from_content (e o fallback essencial para modelos sem nativo)"
    - "Adicionar emoji; mencionar ferramenta de IA"

  acceptance_criteria:
    - "Existe um predicado (ex.: model_supports_native_toolcall(model) em defaults.py) que classifica o modelo; qwen3* -> True, qwen2.5-coder/llama -> False"
    - "Quando True: o system prompt NÃO injeta o few-shot de formato JSON-no-content (deixa o campo tools nativo trabalhar); o proxy le message.tool_calls direto"
    - "Quando False: comportamento atual intacto (few-shot + resgate) -- baseline qwen2.5-coder:3b sem regressao"
    - "Proof runtime: NYX_MODEL=qwen3:1.7b, probe que exige tool -> log mostra tool_call NATIVO (não 'extraido do content'); NYX_MODEL=qwen2.5-coder:3b -> resgate segue funcionando"
    - "Invariantes 14/14; gauntlet rapido; acentuacao rc=0; zero emoji/IA"
```

---

# Sprint MODEL-NATIVE-TOOLCALL-PIPELINE-01 — usar o tool-calling nativo quando o modelo suporta

**Status:** PENDENTE
**Data criação:** 2026-07-13
**Origem:** achado central do bake-off 2026-07-13 (`dev-journey/07-reports/PESQUISA_MODELO_2026_07.md` §Bake-off). O `qwen3:1.7b` emite `tool_calls` nativo perfeitamente no Ollama desta máquina (teste direto provado), mas dentro do Nyx deu 0 de 81 inferências nativas — o pipeline suprime o nativo.

---

## Contexto do projeto (snapshot)

> **ADRs:** ADR-031 (modelo atual qwen2.5-coder:3b — que NÃO faz nativo, justificando o pipeline atual), ADR-032/033/034 (a infra é a alavanca), ADR-013 (integração/fonte única).
> **Achado:** o pipeline de tool-calling do Nyx (few-shot de formato JSON-no-content em `prompt.py` + resgate `_extract_tool_call_from_content` em `proxy.py:517`) foi construído para o `qwen2.5-coder:3b`, que não expõe `tool_calls` nativo do Ollama. Quando roda um modelo que SUPORTA nativo (qwen3), o few-shot do prompt o empurra para o formato texto, desperdiçando o mecanismo nativo — mais confiável.

---

## Problema

**Evidência (bake-off 2026-07-13):** 5 modelos, 81 inferências, **0 tool_call nativo** dentro do Nyx — todos via resgate texto->JSON. **Teste direto isolado** (chamada crua ao Ollama, fora do Nyx): `qwen3:1.7b` com `think=true` + `tools` nativas retorna `message.tool_calls` estruturado e correto. Logo, o modelo e o Ollama fazem nativo; o Nyx o suprime via `prompt.py` (few-shot de formato). O resgate existe porque o baseline precisa dele — mas para modelos capazes de nativo, o nativo é mais confiável (o Ollama valida o JSON schema, elimina o `function.name` alucinado e o eco de comando como texto).

## Solução (aditiva, com fallback preservado)

1. **Predicado de capacidade** em `nyx/config/defaults.py` (irmão de `model_supports_thinking`): `model_supports_native_toolcall(model) -> bool` (qwen3* True; qwen2.5-coder, llama, granite conforme confirmado empiricamente por probe — granite alega nativo mas o bake-off mostrou resgate, então validar antes de marcar True).
2. **Prompt condicional** (`prompt.py`): quando o predicado é True, o `build_system_prompt` NÃO injeta o bloco de few-shot do formato JSON-no-content — descreve as tools de forma mínima (o campo `tools` nativo carrega o schema) e deixa o modelo emitir nativo. Quando False, o comportamento atual (few-shot completo) permanece.
3. **Proxy** (`proxy.py`): já lê `message.tool_calls` nativo primeiro (linha 515) e só cai no resgate se vazio — não precisa mudar a ordem; garantir apenas que o `has_tools` (tools nativas no body) siga passando para os modelos nativos e que o `think` correto (já resolvido para qwen3).

## Proof-of-work esperado

```bash
# nativo (deve mostrar tool_call NATIVO, não "extraido do content"):
NYX_MODEL=qwen3:1.7b NYX_OLLAMA_START_TIMEOUT=120 ./run.sh --headless <<< '{"type":"request","content":"liste os arquivos em ~/Desktop"}'
grep "tool_call extraido do content\|tool_calls: \[" ~/.nyx/logs/proxy.log | tail
# baseline (resgate deve seguir funcionando, sem regressao):
NYX_MODEL=qwen2.5-coder:3b ... (mesmo probe) -> ainda executa via resgate
bash scripts/sprint_invariants.sh   # 14/14
./run.sh --gauntlet --only rapido   # APROVADO
```

Colar: log do proxy provando `tool_calls` nativo com qwen3:1.7b + resgate intacto com o baseline; diff; invariantes antes/depois; acentuação rc=0.

## Não-objetivos (anti-débito)

- **Não** trocar o `DEFAULT_MODEL` (é decisão do dono após o bake-off v2).
- **Não** remover o resgate nem o few-shot (são o caminho do baseline sem nativo).
- **Não** implementar o gerenciador de models (443) — esta sprint é só o pipeline de tool-calling.

---

*"O Ollama sabia chamar a ferramenta; era o nosso prompt que mandava o modelo escrever a chamada em vez de fazê-la."*
