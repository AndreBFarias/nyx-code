## 0. SPEC (machine-readable)

```yaml
sprint:
  id: IDENTITY-GUARD-GENERIC-01
  title: "Guardrail de identidade pega auto-ID generica ('sou uma IA', 'meus treinamentos'), nao so nomes"
  onda: 48
  prioridade: ALTA
  tipo: Bugfix
  dependencias: []
  desbloqueia: []

  touches:
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/agent/lang_check.py
      reason: "mentions_provider so detecta NOMES (qwen/gpt/claude); auto-identificacao generica como IA passa"
      linhas_alvo: "108-141"
  creates: []
  removes: []

  forbidden:
    - "Adicionar emoji"
    - "Mexer em nyx/proxy.py (a 393 toca esse arquivo; o guardrail ja chama mentions_provider -- basta estender a funcao)"
    - "Disparar em mencao LEGITIMA do usuario (o guardrail so roda no content da Nyx, intent chat sem tool_call)"
    - "Mencao a IA proprietaria fora do regex de DETECCAO (usar noqa onde ja existe)"

  tests:
    - cmd: "./run.sh --gauntlet --only rapido"
      timeout: 300
      deve_passar: true

  acceptance_criteria:
    - "mentions_provider() retorna match para 'como uma inteligencia artificial', 'sou uma IA', 'meus treinamentos', 'fui treinado', 'modelo de linguagem'"
    - "mentions_provider() retorna None para uso legitimo sem auto-referencia (ex.: 'o codigo usa um modelo de dados') -- NAO inflar falso positivo grosseiro"
    - "Proof runtime: 'o que voce e? voce e uma inteligencia artificial?' -> resposta final NAO contem 'inteligencia artificial/IA/meus treinamentos' (guardrail forcou retry; idealmente 'Sou Nyx')"
    - "Gauntlet --only rapido 100%; ruff limpo; acentuacao rc=0"
```

---

# Sprint IDENTITY-GUARD-GENERIC-01 — Guardrail pega auto-ID genérica como IA

**Status:** PENDENTE
**Data criação:** 2026-06-26
**Modelo obrigatório:** claude-opus-4-7 (executor-sprint autorizado pelo dono nesta onda)

---

## Contexto do projeto (snapshot)

> **ADRs:** ADR-005 Anonimato (sem menção a IA -- INVIOLÁVEL), ADR-027 Identidade Nyx, ADR-032 (infra guia o modelo), ADR-006 PT-BR, ADR-014 Gauntlet.
> **Estado (2026-06-26):** ONDA-48 (achado V12). O guardrail de identidade vive em `nyx/proxy.py:748-770` e delega a deteção para `nyx/agent/lang_check.py::mentions_provider`. O proxy chama `mentions_provider(content)` (linha 753) e usa no `validate` do retry (linha 768) -- **estender a função basta**, sem tocar o proxy.

---

## Problema

**Achado V12 (provado runtime, 2026-06-26).** A Nyx respondeu: *"Desculpe, mas como uma **inteligência artificial**, eu não tenho acesso ao seu sistema... baseadas na informação disponível através dos meus **treinamentos anteriores**."* Viola ADR-005/027 de forma explícita.

Causa-raiz: o guardrail (`proxy.py:753`) só dispara `mentions_provider()`, e `_PROVIDER_PATTERN` (`lang_check.py:111`) detecta apenas **nomes** (`qwen|gpt|claude|llama|...`). "inteligência artificial", "IA", "modelo de linguagem", "meus treinamentos", "fui treinado" **não são nomes** -> passam batido -> o retry nunca dispara.

---

## Solução proposta

Adicionar em `lang_check.py` um segundo padrão `_SELF_AI_PATTERN` para **auto-identificação como IA** e fazer `mentions_provider()` retornar match de qualquer um dos dois. Foco em auto-referência (o que a Nyx diz de SI), não em discussão abstrata legítima.

---

## Arquivos alvo (paths absolutos)

### `/home/andrefarias/Desenvolvimento/Nyx-Code/nyx/agent/lang_check.py`

# Localização aproximada: linha 111-141 (drift tolerado se trecho casa)
**Antes:**
```python
_PROVIDER_PATTERN = re.compile(
    r"(?<![a-zA-Z])("
    r"qwen|alibaba|"
    ...
    r"grok|x\s*ai"
    r")(?![a-zA-Z])",
    re.IGNORECASE,
)


def mentions_provider(text: str) -> str | None:
    ...
    if not text:
        return None
    m = _PROVIDER_PATTERN.search(text)
    return m.group(1).lower() if m else None
```

**Depois:**
```python
_PROVIDER_PATTERN = re.compile(
    r"(?<![a-zA-Z])("
    r"qwen|alibaba|"
    ...
    r"grok|x\s*ai"
    r")(?![a-zA-Z])",
    re.IGNORECASE,
)

# IDENTITY-GUARD-GENERIC-01 (V12): auto-identificacao GENERICA como IA. A Nyx
# nunca pode se descrever como IA/assistente/modelo (ADR-005/027). _PROVIDER_PATTERN
# pega so NOMES; este pega as frases que vazaram ("como uma inteligencia
# artificial", "meus treinamentos", "fui treinado", "modelo de linguagem").
# Ancorado em auto-referencia para nao disparar em discussao abstrata legitima.  # noqa: ai-mention
_SELF_AI_PATTERN = re.compile(
    r"(intelig[eê]ncia\s+artificial|"
    r"(?<![a-zA-Z])IAs?(?![a-zA-Z])|"
    r"modelo\s+de\s+linguagem|"
    r"(sou|como)\s+(um|uma)\s+(assistente|intelig[eê]ncia|modelo)|"
    r"(meus|nos\s+meus)\s+treinamentos|fui\s+treinad[oa]|"
    r"treinad[oa]\s+(para|por|com|em))",
    re.IGNORECASE,
)


def mentions_provider(text: str) -> str | None:
    ...
    if not text:
        return None
    m = _PROVIDER_PATTERN.search(text)
    if m:
        return m.group(1).lower()
    m2 = _SELF_AI_PATTERN.search(text)
    return m2.group(0).lower().strip() if m2 else None
```

**Mudanças:** novo `_SELF_AI_PATTERN`; `mentions_provider` checa os dois e retorna o primeiro match. Docstring atualizado para mencionar auto-ID genérica.

---

## Diff esperado (resumo)

```
~ 1 arquivo modificado (nyx/agent/lang_check.py)
+ ~16 linhas líquidas
```

---

## Comandos de verificação (literais, copy-paste)

```bash
# 1. Static
python -m ruff check nyx/

# 2. Unidade da deteção (lógica pura -- ADR-007 §EXCEÇÃO permite, mas rode inline, sem criar test_*.py):
python -c "
from nyx.agent.lang_check import mentions_provider as mp
assert mp('como uma inteligencia artificial nao tenho acesso')      # deve detectar
assert mp('baseadas nos meus treinamentos anteriores')              # deve detectar
assert mp('sou uma IA')                                             # deve detectar
assert mp('Sou Nyx, codificadora silenciosa') is None              # NAO detecta (identidade correta)
assert mp('o codigo usa um modelo de dados') is None               # NAO detecta (uso legitimo)
print('OK deteccao identidade')
"

# 3. Acentuação
python3 ~/.config/zsh/scripts/validar-acentuacao.py --paths nyx/agent/lang_check.py

# 4. PROOF RUNTIME-REAL: a Nyx nao se declara IA.
printf '%s\n' '{"type":"request","content":"o que voce e? voce e uma inteligencia artificial?"}' \
  | NYX_AUTO_APPROVE=1 ./run.sh --headless 2>/dev/null
# ESPERADO: summary SEM "inteligencia artificial"/"IA"/"meus treinamentos" (guardrail forcou retry).
#           Idealmente identidade Nyx ("Sou Nyx" / "codificadora"). COLE o JSON literal.

# 5. Gauntlet
./run.sh --gauntlet --only rapido
```

---

## Critério binário de aceite

- [ ] `_SELF_AI_PATTERN` adicionado; `mentions_provider` checa os dois padrões
- [ ] Asserts do passo 2 passam (detecta auto-ID, não detecta identidade Nyx nem uso legítimo)
- [ ] Proof runtime: resposta final sem vazamento de identidade (colar JSON)
- [ ] `nyx/proxy.py` NÃO foi modificado (a 393 cuida dele)
- [ ] ruff limpo, acentuação rc=0, invariantes FAIL_AFTER <= FAIL_BEFORE, gauntlet rapido 100%
- [ ] 394 marcada CONCLUIDA no MASTER; spec movida para concluidos/
- [ ] Commit: `fix(proxy): 394 IDENTITY-GUARD-GENERIC-01 -- guardrail pega auto-ID como IA (V12)`

---

## Guardrails anti-engodo

NÃO concluir se: o proof runtime não foi colado; o padrão dispara em uso legítimo grosseiro (falso positivo no assert); modificou proxy.py; gauntlet "passou" sem output. Falha -> `[SPRINT 394] BLOQUEADA: <motivo>`.

---

## Proof-of-work (4 passos)

inv_before -> implementar -> inv_after (<=) -> diff. Colar tail de ambos + diff + asserts do passo 2 + JSON do proof runtime + `git show --stat HEAD`.

---

## Riscos

| Risco | Mitigação |
|-------|-----------|
| Falso positivo: usuário pergunta "o que é IA?" e a Nyx explica legitimamente | O guardrail só roda no CONTENT da Nyx em intent chat sem tool_call; auto-descrição como IA nunca é legítima (ADR-005). Retry é 1x e barato. |
| "IA" como substring de palavra (ex.: "praia", "feira") | Padrão usa `(?<![a-zA-Z])IAs?(?![a-zA-Z])` (boundary), não casa dentro de palavra. Assert cobre. |
| Retry também vazar | `validate` do retry usa o mesmo `mentions_provider` estendido -> rejeita o retry vazado; se 1 retry não resolver, ao menos não piora (comportamento atual). |

---

*"Quem precisa dizer que é máquina, já esqueceu o nome que tem." -- princípio de identidade*
