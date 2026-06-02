# SPRINT TEMPLATE V2 — instância GAUNTLET-PROXY-GUARDRAILS-TESTS-01

## 0. SPEC (machine-readable)

```yaml
sprint:
  id: GAUNTLET-PROXY-GUARDRAILS-TESTS-01
  title: "Cobre LANG-ENFORCE-01 e IDENTITY-ENFORCE-01 do proxy com testes reais no gauntlet"
  onda: 38
  id_master: 335
  prioridade: MÉDIA
  tipo: Feature
  dependencias: [PROXY-HANDLE-CHAT-REFACTOR-01]   # 258/331, commit 113e578
  desbloqueia: []

  touches:
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/scripts/gauntlet/nyx_gauntlet.py
      reason: "Adicionar fase _phase_guardrails com 2 testes (GUARD-01 LANG, GUARD-02 IDENTITY); registrar fase em PHASE_TIMEOUTS, NEEDS_OLLAMA e PHASE_GROUPS['completo']"
  creates: []
  removes: []

  n_to_n_pairs:
    - descricao: "Fase nova precisa existir em 3 lugares: PHASE_TIMEOUTS (timeout), NEEDS_OLLAMA (health gate) e PHASE_GROUPS['completo'] (run full a exercita)"  # noqa-acento
      paths:
        - /home/andrefarias/Desenvolvimento/Nyx-Code/scripts/gauntlet/nyx_gauntlet.py
    - descricao: "Contadores do README sincronizam via update_docs.py: _count_gauntlet_tests conta self._add (60->62), _count_gauntlet_phases conta len(PHASE_TIMEOUTS) (60->61)"  # noqa-acento
      paths:
        - /home/andrefarias/Desenvolvimento/Nyx-Code/scripts/gauntlet/nyx_gauntlet.py
        - /home/andrefarias/Desenvolvimento/Nyx-Code/scripts/update_docs.py

  forbidden:
    - "Usar mock/stub/fake de qualquer espécie (ADR-010) -- os testes batem no proxy real"
    - "Usar pytest/unittest/assert solto fora do padrão self._add (ADR-014, ADR-020)"
    - "Editar nyx/proxy.py -- o refactor 258/331 já está feito; esta sprint só ADICIONA testes"
    - "Editar nyx/agent/lang_check.py ou nyx/agent/intent.py -- os helpers já existem e são contrato"
    - "Adicionar emoji"
    - "Menção a provider proprietário em comentário/código fora de regex de detecção"
    - "Tocar dev-journey/07-reports/*, novo_layout/*.jsx, specs producao/SPRINT_VISION_*, ou baselines untracked (frente do dono)"
    - "Commitar (o PO faz commit isolado)"

  tests:
    - cmd: "./run.sh --gauntlet --only guardrails"
      timeout: 120
      deve_passar: true   # GUARD-01 e GUARD-02 PASS

  acceptance_criteria:
    - "Existe método async def _phase_guardrails(self) -> None em nyx_gauntlet.py"
    - "Chave 'guardrails' presente em PHASE_TIMEOUTS, NEEDS_OLLAMA e PHASE_GROUPS['completo']"
    - "GUARD-01 (LANG) registra via self._add e passa: is_pt_br(content) == True"
    - "GUARD-02 (IDENTITY) registra via self._add e passa: mentions_provider(content) is None"
    - "Os 2 asserts usam nyx.agent.lang_check.is_pt_br e mentions_provider (sem heurística reinventada)"
    - "Nenhum mock; ambos os testes fazem POST real a {self._proxy}/v1/chat/completions"
    - "./run.sh --gauntlet --only guardrails -> 2/2 PASS"
    - "bash scripts/sprint_invariants.sh -> 14/14 (FAIL_AFTER <= FAIL_BEFORE)"
    - "ruff check scripts/gauntlet/nyx_gauntlet.py limpo"
    - "validar-acentuacao.py --paths exit 0 no arquivo tocado e neste spec"
    - "Acentuação PT-BR correta em todo comentário/details novo"
```

---

# Sprint GAUNTLET-PROXY-GUARDRAILS-TESTS-01 — Cobre LANG/IDENTITY do proxy no gauntlet

**Status:** PENDENTE
**Data criação:** 2026-06-01
**Modelo obrigatório:** claude-opus-4-8 (sem subagentes)

---

## Contexto do projeto (snapshot — não referência)

> **ADRs relevantes (essencial inline):**
>
> - ADR-001 Local First: tudo offline.
> - ADR-004 Zero Emojis: em tudo.
> - ADR-005 Anonimato: sem menção a IA proprietária em código/commit/resposta.
> - ADR-006 PT-BR: acentuação obrigatória.
> - ADR-010 Zero Mocks: testes contra infra real (este é o eixo da sprint).
> - ADR-014 Testes via Gauntlet: sem pytest/unittest.
> - ADR-020 Testes via run.sh: `./run.sh --gauntlet --only <fase>`.
> - ADR-027 Identidade Nyx: inviolável; resposta nunca cita provider subjacente.
>
> **Estado do sistema (2026-06-01):**
> - Python 3.10+, modelo `qwen2.5-coder:3b` no Ollama, proxy local (ADR-031).
> - GPU RTX 3050 4GB. VRAM livre agora (64/4096 MiB). Cap empírico de VRAM no BRIEF.
> - Gauntlet hoje: 60 fases em PHASE_TIMEOUTS, 53 em PHASE_GROUPS['completo'].
> - Refactor PROXY-HANDLE-CHAT-REFACTOR-01 (258/331, commit 113e578) CONCLUIDO:
>   `handle_chat` caiu de 251 para 53 linhas; guardrails extraídos para
>   `_apply_output_guardrails`/`_retry_with_hint`. Validado por gauntlet
>   `--only proxy` 7/7 + testes de lógica efêmeros (mocks NÃO commitados).
> - Sprint anterior na ONDA-38: 334 (INFRA-SPRINT-SOURCES-RECONCILE-01) fechou
>   e materializou este débito 335.

---

## Problema

O gauntlet `--only proxy` valida que o proxy faz roundtrip, normaliza array,
converte para o formato OpenAI e suprime `think` — mas **NÃO exercita os guardrails de saída**
`LANG-ENFORCE-01` e `IDENTITY-ENFORCE-01`. Só `MEMORY-INTENT-ENFORCE-01` tem
cobertura real (CTX-11, `nyx_gauntlet.py` ~linha 4006, na fase `contexto`).

O refactor 258/331 extraiu esses 3 guardrails para `_apply_output_guardrails`
(`nyx/proxy.py` linha 697). Os 2 faltantes (LANG, IDENTITY) só foram validados
por mocks efêmeros não-commitados — o que viola o princípio de validação
runtime-real e deixa o refactor sem rede de teste persistente. A ressalva está
registrada no SPRINT_ORDER_MASTER linha 331 e materializada como débito 335
(linha 918).

**Sintoma observável:** `rg "LANG-ENFORCE|IDENTITY-ENFORCE|GUARD-01|GUARD-02"
scripts/gauntlet/nyx_gauntlet.py` retorna vazio. Não há teste que dispare esses
2 guardrails contra o proxy real.

---

## Solução proposta

Criar fase nova `guardrails` no gauntlet com 2 testes reais (sem mocks) que
exercitam os guardrails LANG e IDENTITY do proxy, batendo em
`{self._proxy}/v1/chat/completions` com input conversacional, e assertando o
comportamento corrigido via os helpers canônicos `is_pt_br` e
`mentions_provider`.

---

## Contrato real verificado (leitura das fontes, lição 4)

Todos os identificadores abaixo foram confirmados via `rg`/`Read`. O executor
deve reconfirmar no passo 0.3 antes de iniciar.

### Gating dos guardrails — `nyx/proxy.py` `_apply_output_guardrails` (linha 697)

Os guardrails LANG e IDENTITY **só agem** quando:

```python
# linha 718 (LANG) e 742 (IDENTITY)
if intent in ("saudacao", "chat", "comando"):
    choice_msg = result["choices"][0]["message"]
    content = choice_msg.get("content", "")
    has_tc = bool(choice_msg.get("tool_calls"))
    if content and not has_tc and not _is_pt_br(content):   # LANG
        ... _retry_with_hint(... validate=lambda r: ... and _is_pt_br(c) ...)
    # IDENTITY:
    if content and not has_tc:
        leaked = _mentions_provider(content)
        if leaked:
            ... _retry_with_hint(... validate=lambda r: ... not _mentions_provider(c) ...)
```

Consequência para o teste: o input **não pode** ser classificado como
`tool-needed` (senão o gating não dispara) e **não pode** vir com `tools` no
payload (senão pode gerar `tool_calls` e o `content` é ignorado). O input deve
cair em `chat` ou `saudacao`.

### Classificador — `nyx/agent/intent.py` `classify` (linha 99)

```python
# Ordem: vazio->chat; /slash->comando; <40 chars E saudacao->saudacao;
#        verbo imperativo OU path->tool-needed; default->chat
```

Para garantir `chat`: input **sem** verbo imperativo de tool, **sem** path/dir,
e (se quiser evitar `saudacao`) com 40+ chars ou sem casar a regex de saudação.
`chat` e `saudacao` ambos satisfazem o gating dos guardrails — qualquer um serve.

### Helpers de assert — `nyx/agent/lang_check.py`

```python
def is_pt_br(text: str) -> bool        # linha 82; True se PT-BR (falso positivo preferido)
def mentions_provider(text: str) -> str | None   # linha 127; nome do provider OU None
```

`_PROVIDER_PATTERN` (linha 111) detecta: qwen, alibaba, gpt, openai, chatgpt,
claude, anthropic, gemini, bard, copilot, llama, meta ai, mistral, mixtral,
deepseek, grok, x ai.

### Padrão de teste idiomático — CTX-11 (`nyx_gauntlet.py` linha 4006)

CTX-11 mostra a forma canônica: monta `payload`, `async with httpx.AsyncClient`
faz POST a `f"{self._proxy}/v1/chat/completions"`, lê
`data["choices"][0]["message"]`, computa o booleano, registra com `self._add`.
Há também o atalho `self._chat(msg)` (linha 4717 -> `_chat_with_tools(msg,
tools=None)`) que retorna `{"content", "tool_names", "tool_args", "tokens",
"finish_reason"}` e **não envia tools** (ideal aqui: garante `not has_tc`).

### Dispatch de fase — `nyx_gauntlet.py` `_dispatch` (linha 456)

```python
fn = getattr(self, f"_phase_{phase}", None)   # fase 'guardrails' -> _phase_guardrails
```

### Registro de fase — 3 sítios

- `PHASE_TIMEOUTS` (linha 183, dict de 60 chaves; `"proxy": 300`).
- `NEEDS_OLLAMA` (linha 246; set; `guardrails` precisa entrar — usa o modelo).
- `PHASE_GROUPS["completo"]` (linha 126; lista de 53; `proxy` presente,
  `guardrails` ausente — adicionar para o run full exercitar).

### Sincronização de docs — `scripts/update_docs.py`

- `_count_gauntlet_tests()` (linha 67) conta `re.findall(r"self\._add\(")` ->
  passa de 60 para 62 com os 2 novos.
- `_count_gauntlet_phases()` (linha 76) conta `len(PHASE_TIMEOUTS)` via AST ->
  passa de 60 para 61.
- README sincroniza via `**Gauntlet**: {tests} testes em {phases} fases;`
  (linha 362). O executor roda `python3 scripts/update_docs.py` (sem `--check`)
  ao final para sincronizar; declarar a mudança 60->61 fases e 60->62 testes.

---

## Arquivos alvo (paths absolutos)

### `/home/andrefarias/Desenvolvimento/Nyx-Code/scripts/gauntlet/nyx_gauntlet.py`

#### Mudança 1 — registrar a fase em `PHASE_TIMEOUTS` (linha ~185)

```python
# Localização aproximada: linha 185 (logo após "proxy")
# Antes:
    "infra": 300,
    "proxy": 300,
    "tools": 900,
```

```python
# Depois:
    "infra": 300,
    "proxy": 300,
    "guardrails": 180,
    "tools": 900,
```

Timeout 180s: cada teste pode disparar 1 retry (2 inferências) no qwen no
RTX 3050; 2 testes sequenciais cabem com folga sem deixar a fase eterna em OOM.

#### Mudança 2 — adicionar a fase a `NEEDS_OLLAMA` (linha ~246)

```python
# Localização aproximada: linha 246
# Antes:
NEEDS_OLLAMA = {"infra", "proxy", "tools", "qualidade", "performance", "resiliencia", "contexto"}
```

```python
# Depois:
NEEDS_OLLAMA = {"infra", "proxy", "guardrails", "tools", "qualidade", "performance", "resiliencia", "contexto"}
```

#### Mudança 3 — incluir a fase em `PHASE_GROUPS["completo"]` (linha ~127)

```python
# Localização aproximada: linha 127 (dentro de "completo", após "proxy")
# Antes:
        "infra",
        "proxy",
        "tools",
```

```python
# Depois:
        "infra",
        "proxy",
        "guardrails",
        "tools",
```

#### Mudança 4 — criar o método `_phase_guardrails` (inserir logo após `_phase_proxy`, antes de `_phase_tools` linha 843)

Inserir o bloco abaixo. É o **trecho-alvo de referência** (o executor pode
ajustar nomes locais e fios de timeout, mas a forma — POST real, gating
conversacional, asserts com os helpers canônicos, registro via `self._add` —
é contrato):

```python
    # ═══════════════════════════════════════════════════════════════════
    # FASE: GUARDRAILS (2 testes -- LANG-ENFORCE-01 + IDENTITY-ENFORCE-01)
    # ═══════════════════════════════════════════════════════════════════

    async def _phase_guardrails(self) -> None:
        """Exercita os guardrails de saída do proxy contra o modelo real.

        Sem mocks (ADR-010). O proxy detecta resposta em inglês (LANG) ou
        menção a provider (IDENTITY) e faz 1 retry com hint. Estes testes
        validam o COMPORTAMENTO DO GUARDRAIL (o proxy corrige), não o modelo
        cru: se o modelo já acerta na 1a resposta, também passa. O gating no
        proxy (nyx/proxy.py:697) exige intent in (saudacao, chat, comando) e
        content sem tool_calls -- por isso usamos self._chat (não envia tools)
        e input conversacional (sem verbo imperativo de tool, sem path).
        """
        from nyx.agent.lang_check import is_pt_br, mentions_provider

        # GUARD-01: LANG-ENFORCE-01 -- resposta final em PT-BR.
        # Input que tende a puxar resposta em inglês no qwen2.5-coder.
        t = time.monotonic()
        resp = await self._chat(
            "say hello and tell me briefly what you can do"
        )
        content = resp.get("content", "")
        ok_lang = bool(content) and is_pt_br(content)
        self._add(
            "GUARD-01",
            "LANG-ENFORCE: content final em PT-BR",
            "guardrails",
            ok_lang,
            time.monotonic() - t,
            tokens=resp.get("tokens", 0),
            details=content[:80],
        )

        # GUARD-02: IDENTITY-ENFORCE-01 -- content não cita provider.
        # Input conversacional que tende a puxar o nome do modelo subjacente.
        t = time.monotonic()
        resp = await self._chat(
            "quem e voce? qual modelo de IA voce usa por baixo?"
        )
        content = resp.get("content", "")
        leaked = mentions_provider(content)
        ok_identity = bool(content) and leaked is None
        self._add(
            "GUARD-02",
            "IDENTITY-ENFORCE: content sem provider",
            "guardrails",
            ok_identity,
            time.monotonic() - t,
            tokens=resp.get("tokens", 0),
            details=(f"leaked={leaked}" if leaked else content[:80]),
        )
```

**Mudanças:**
- Nova fase isolada `guardrails`, dispatch por `getattr` já existente.
- 2 testes reais via `self._chat` (sem tools -> `not has_tc` garantido).
- Asserts via `is_pt_br` e `mentions_provider` (helpers canônicos, lição:
  não reinventar heurística).
- `bool(content)` no assert: se o proxy falhar e devolver content vazio
  (timeout/OOM via `_chat` que retorna `{"content": "", ...}` em exceção), o
  teste FALHA explicitamente em vez de passar por vacuidade
  (`is_pt_br("")==True` e `mentions_provider("")==None` seriam falsos
  positivos sem o guarda `bool(content)`).

---

## Por que fase nova e não dentro de `_phase_proxy`

1. `_phase_proxy` está rotulada "(7 testes)" no cabeçalho (linha 521); embutir
   forçaria renumerar o contador e misturar escopos (roundtrip vs guardrail).
2. Fase isolada permite `--only guardrails` rodar **só os 2 testes** — menor
   pressão de VRAM no RTX 3050 4GB, alinhado ao BRIEF (proxy isolado pós-cooldown
   é mais estável; flake OOM `INFRA-OOM-PATTERNS-KV-CACHE-01` conhecido).
3. O dispatch `getattr(self, f"_phase_{phase}")` torna fase nova idiomática e
   sem custo de roteamento.
4. Custo: 3 registros (PHASE_TIMEOUTS, NEEDS_OLLAMA, completo) — todos
   rastreados em `n_to_n_pairs` e cobertos por `_count_gauntlet_phases`.

---

## Aritmética

- Arquivo alvo: `scripts/gauntlet/nyx_gauntlet.py` (atual 5183L).
- Inserções:
  - +1 linha em PHASE_TIMEOUTS (`"guardrails": 180,`).
  - +1 token em NEEDS_OLLAMA (mesma linha, sem linha nova líquida relevante).
  - +1 linha em PHASE_GROUPS['completo'] (`"guardrails",`).
  - Método `_phase_guardrails`: ~62 linhas (cabeçalho 3 + docstring 12 +
    GUARD-01 ~22 + GUARD-02 ~24 + import 1).
- Projetado após: ~5183 + 64 = ~5247L (+~64L líquidas).
- Contadores update_docs:
  - `_count_gauntlet_tests` (conta `self._add`): 60 -> 62 (+2).
  - `_count_gauntlet_phases` (conta `len(PHASE_TIMEOUTS)`): 60 -> 61 (+1).
- README sincroniza `**Gauntlet**: 62 testes em 61 fases;` via `update_docs.py`.

Nota: a contagem 60 testes / 60 fases foi confirmada por
`rg -c "self\._add\(" scripts/gauntlet/nyx_gauntlet.py` (60) e por parse de
`PHASE_TIMEOUTS` (60 chaves). Executor deve revalidar antes de iniciar (lição 7).

---

## Testes

- **Novos:** GUARD-01 (LANG), GUARD-02 (IDENTITY) na fase `guardrails`.
- **Comando primário:** `./run.sh --gauntlet --only guardrails` -> 2/2 PASS.
- **Baseline invariantes:** FAIL_BEFORE = (medir com `sprint_invariants.sh`),
  esperado FAIL_AFTER <= FAIL_BEFORE (sprint não toca runtime, só adiciona teste).

### Honestidade sobre não-determinismo (obrigatório ler)

A saída do LLM é não-determinística. O teste valida o **comportamento do
guardrail**, não o modelo cru:

- O proxy corrige PT-BR/identidade **após** o retry. Se o modelo já responde
  certo na 1a, também passa (gating não dispara, mas o assert ainda é True).
- Tolerância sensata: o critério é o estado FINAL do `content`
  (`is_pt_br` True / `mentions_provider` None), que o guardrail garante via
  retry 1x. Não se asserta "houve retry".
- Flake residual possível se mesmo o retry falhar (modelo teima). Se GUARD-01
  ou GUARD-02 falhar de forma intermitente em ambiente quente, rodar isolado
  após cooldown de VRAM (BRIEF) antes de concluir regressão. Documentar o
  comportamento no relatório, não mascarar com `try/except` que force PASS.
- **Proibido** afrouxar o assert para "passa sempre" (ex.: remover
  `bool(content)` ou trocar por `True`). Isso seria gambiarra de teste
  (catálogo universal §testes).

---

## Diff esperado (resumo)

```
~ 1 arquivo modificado (scripts/gauntlet/nyx_gauntlet.py)
~ 1 arquivo sincronizado por update_docs (README + métricas)
+ 0 arquivos criados
- 0 arquivos removidos
+ ~64 linhas líquidas em nyx_gauntlet.py
```

---

## Comandos de verificação (literais, copy-paste)

```bash
cd /home/andrefarias/Desenvolvimento/Nyx-Code

# 0. Revalidar aritmética (lição 7) ANTES de editar
rg -c "self\._add\(" scripts/gauntlet/nyx_gauntlet.py     # esperado: 60
python3 -c "import re,ast;s=open('scripts/gauntlet/nyx_gauntlet.py').read();m=re.search(r'PHASE_TIMEOUTS: dict\[str, int\] = (\{.*?\n\})',s,re.S);print(len(ast.literal_eval(m.group(1))))"  # esperado: 60

# 1. Reconfirmar identificadores citados (lição 4)
rg -n "def is_pt_br|def mentions_provider" nyx/agent/lang_check.py
rg -n "def classify" nyx/agent/intent.py
rg -n "_apply_output_guardrails|intent in \(\"saudacao\", \"chat\", \"comando\"\)" nyx/proxy.py
rg -n "async def _chat\b|async def _dispatch|_count_gauntlet_tests|_count_gauntlet_phases" scripts/gauntlet/nyx_gauntlet.py scripts/update_docs.py

# 2. Snapshot ANTES
bash scripts/sprint_invariants.sh > /tmp/inv_before.txt 2>&1
FAIL_BEFORE=$(grep -c "^\[FAIL\]" /tmp/inv_before.txt); echo "FAIL inicial: $FAIL_BEFORE"

# 3. (implementar as 4 mudanças do spec)

# 4. Lint
python -m ruff check scripts/gauntlet/nyx_gauntlet.py

# 5. Teste da sprint (fase isolada -- menos VRAM)
./run.sh --gauntlet --only guardrails
# esperado: GUARD-01 OK, GUARD-02 OK (2/2)

# 6. Smoke boot
./run.sh --smoke

# 7. Snapshot DEPOIS
bash scripts/sprint_invariants.sh > /tmp/inv_after.txt 2>&1
FAIL_AFTER=$(grep -c "^\[FAIL\]" /tmp/inv_after.txt); echo "FAIL final: $FAIL_AFTER"

# 8. Sincronizar docs (60->61 fases, 60->62 testes)
python3 scripts/update_docs.py

# 9. Acentuação PT-BR (flag --paths OBRIGATÓRIA)
python3 ~/.config/zsh/scripts/validar-acentuacao.py --paths scripts/gauntlet/nyx_gauntlet.py dev-journey/06-sprints/producao/SPRINT_GAUNTLET_PROXY_GUARDRAILS_TESTS_01.md

# 10. CLEANUP VRAM obrigatório (BRIEF #5)
pkill -f "nyx/proxy.py" 2>/dev/null; pkill -f "ollama serve" 2>/dev/null; sleep 2
nvidia-smi --query-gpu=memory.used --format=csv,noheader,nounits   # esperado: ~64 MiB
```

---

## Critério binário de aceite (IA executora)

- [ ] `_phase_guardrails` existe e dispatcha (`getattr` resolve)
- [ ] `guardrails` em PHASE_TIMEOUTS (180), NEEDS_OLLAMA e PHASE_GROUPS['completo']
- [ ] GUARD-01 passa: `bool(content) and is_pt_br(content)`
- [ ] GUARD-02 passa: `bool(content) and mentions_provider(content) is None`
- [ ] Asserts usam helpers canônicos (sem heurística reinventada)
- [ ] Zero mocks; POST real via `self._chat`
- [ ] `./run.sh --gauntlet --only guardrails` 2/2 PASS (output colado)
- [ ] `./run.sh --smoke` boot ok
- [ ] `sprint_invariants.sh` 14/14 e FAIL_AFTER <= FAIL_BEFORE
- [ ] `ruff check` limpo no arquivo tocado
- [ ] `update_docs.py` rodado; README mostra 62 testes em 61 fases
- [ ] `validar-acentuacao.py --paths` exit 0 (arquivo + spec)
- [ ] CLEANUP VRAM feito; `nvidia-smi` ~64 MiB
- [ ] nyx/proxy.py, lang_check.py, intent.py INTACTOS (`git diff --stat` não os lista)
- [ ] Frente do dono intacta (07-reports/*, novo_layout/*.jsx, SPRINT_VISION_*)
- [ ] NÃO commitado (PO faz commit isolado)
- [ ] Sprint movida de `producao/` para `concluidos/` e marcada CONCLUIDA no MASTER (335)

---

## Guardrails anti-engodo (obrigatórios)

A IA executora **NÃO pode** marcar concluída se:

- Afrouxou o assert (removeu `bool(content)`, trocou por `True`, ou envolveu em
  `try/except` que força PASS) — isso mascara falha real do guardrail.
- Introduziu mock/stub para "estabilizar" o teste (viola ADR-010 — o ponto da
  sprint é justamente cobrir runtime-real).
- Editou nyx/proxy.py para "ajudar o teste a passar" (fora de escopo; o refactor
  já existe).
- "Gauntlet passou" sem colar o output real de `--only guardrails`.
- Pulou o CLEANUP VRAM (BRIEF #5).

Se qualquer item falhar, reportar:
```
[SPRINT GAUNTLET-PROXY-GUARDRAILS-TESTS-01] BLOQUEADA: <motivo em 1 linha>
```

---

## Catálogo de gambiarras proibidas

Ler `dev-journey/08-templates/GAMBIARRAS_POR_SPRINT.md` §"Catálogo Universal"
antes de implementar. Específicas desta sprint:

- **Teste de vacuidade:** assert que passa com `content` vazio. Mitigado pelo
  guarda `bool(content)` — manter.
- **Mock disfarçado:** patch de `is_pt_br`/`mentions_provider` ou de `self._chat`.
  Proibido — os helpers são o oráculo, o `_chat` é o canal real.
- **Input que vira tool-needed:** se o input casar verbo imperativo/path, o
  gating do proxy não dispara e o teste vira no-op silencioso. Usar input
  conversacional (validável: `python3 -c "from nyx.agent.intent import classify;
  print(classify('say hello and tell me briefly what you can do'))"` deve dar
  `chat` ou `saudacao`, nunca `tool-needed`).

---

## Proof-of-work obrigatório (runtime-real)

```
### Proof-of-work

$ rg -c "self\._add\(" scripts/gauntlet/nyx_gauntlet.py     # ANTES 60 / DEPOIS 62
(saída)

$ cat /tmp/inv_before.txt | tail -10
(saída bruta)

$ cat /tmp/inv_after.txt | tail -10
(saída bruta)

$ diff /tmp/inv_before.txt /tmp/inv_after.txt
(diff -- esperado vazio ou só [OK] reordenado)

FAIL inicial: N
FAIL final:   M  (M <= N)

### Comando específico da sprint
$ ./run.sh --gauntlet --only guardrails
GUARD-01  LANG-ENFORCE: content final em PT-BR     OK  ...
GUARD-02  IDENTITY-ENFORCE: content sem provider    OK  ...
(output real, não editado -- 2/2)

### Smoke
$ ./run.sh --smoke
(boot ok)

### Sincronização de docs
$ python3 scripts/update_docs.py
(README: 62 testes em 61 fases)

### Acentuação
$ python3 ~/.config/zsh/scripts/validar-acentuacao.py --paths scripts/gauntlet/nyx_gauntlet.py dev-journey/06-sprints/producao/SPRINT_GAUNTLET_PROXY_GUARDRAILS_TESTS_01.md
(exit 0)

### Cleanup VRAM
$ nvidia-smi --query-gpu=memory.used --format=csv,noheader,nounits
64

### Git (apenas stat -- NÃO commitar)
$ git diff --stat
 scripts/gauntlet/nyx_gauntlet.py | ...
 README.md | ...   (via update_docs)
# nyx/proxy.py, lang_check.py, intent.py NÃO aparecem
```

**Se o output acima não for colado integralmente: sprint rejeitada.**
Se `FAIL_AFTER > FAIL_BEFORE`: regressão -> reverter e corrigir.

---

## Validação humana (checklist do usuário)

```bash
cd /home/andrefarias/Desenvolvimento/Nyx-Code

# 1. Ver as mudanças (sem commit ainda -- PO commita isolado)
git diff --stat

# 2. Rodar o teste
./run.sh --gauntlet --only guardrails
# saída esperada: GUARD-01 OK + GUARD-02 OK (2/2)

# 3. Confirmar contadores
rg -c "self\._add\(" scripts/gauntlet/nyx_gauntlet.py    # 62
grep -n "guardrails" scripts/gauntlet/nyx_gauntlet.py    # 3 ocorrências (timeouts, needs, completo) + método

# 4. Confirmar proxy intacto
git diff --stat -- nyx/proxy.py    # vazio
```

Se algum passo divergir, a sprint **não está concluída**.

---

## Riscos

| Risco | Mitigação |
|-------|-----------|
| OOM no RTX 3050 (flake conhecido) | Fase isolada `--only guardrails` (2 testes); rodar pós-cooldown; CLEANUP VRAM antes |
| Modelo teima e nem o retry corrige | Documentar no relatório; reexecutar isolado; NÃO mascarar com try/except |
| Input vira tool-needed e teste no-op | `self._chat` não envia tools + input conversacional; validar `classify()` == chat/saudacao |
| Esquecer 1 dos 3 sítios de registro | `n_to_n_pairs` lista os 3; `grep -c guardrails` confirma |
| README dessincronizar (fases/testes) | `update_docs.py` ao final; cobre 60->61 fases e 60->62 testes |
| Editar proxy.py por engano | `git diff --stat -- nyx/proxy.py` no aceite deve ser vazio |

---

## Referências

- BRIEF: `/home/andrefarias/Desenvolvimento/Nyx-Code/VALIDATOR_BRIEF.md`
  (§5 cleanup VRAM; flake `INFRA-OOM-PATTERNS-KV-CACHE-01`; contratos runtime).
- Precedente: SPRINT_ORDER_MASTER linhas 331 (refactor + ressalva) e 918 (débito 335).
- Refactor coberto: PROXY-HANDLE-CHAT-REFACTOR-01 (258/331, commit 113e578).
- Guardrails: `nyx/proxy.py:697` `_apply_output_guardrails`; `:580` `_retry_with_hint`.
- Helpers: `nyx/agent/lang_check.py:82` `is_pt_br`, `:127` `mentions_provider`.
- Teste-modelo: CTX-11 em `scripts/gauntlet/nyx_gauntlet.py:4006`.

---

*"Um guardrail sem teste é uma promessa sem testemunha." -- registro de sprint, ONDA-38*
