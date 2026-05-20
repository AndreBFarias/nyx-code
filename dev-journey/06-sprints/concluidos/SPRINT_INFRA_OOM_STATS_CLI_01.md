# SPRINT INFRA-OOM-STATS-CLI-01 — Slash `/stats` CLI consumindo `/admin/stats` do proxy

## 0. SPEC (machine-readable)

```yaml
sprint:
  id: INFRA-OOM-STATS-CLI-01
  title: "Slash `/stats` CLI consumindo GET /admin/stats do proxy (renderiza OOM recovery, num_gpu, degraded)"
  onda: 24
  bloco: 24.1 Infra resiliente
  prioridade: BAIXA
  tipo: Feature+Resolve-conflito-nomes
  dependencias: [INFRA-OOM-02, SCAFFOLD-CMD-FIX-01]
  desbloqueia: []

  touches:
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/agent/commands/stats.py
      reason: "NOVO. Módulo com @nyx_command(name='stats', category='debug') que faz GET http://127.0.0.1:<PROXY_PORT>/admin/stats via httpx e renderiza saída CLI compacta em PT-BR. Erros de rede/HTTP/JSON viram strings amigáveis (sem crash do REPL)."
      linhas_alvo: "novo arquivo (~50L)"
      criar: true
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/agent/commands/__init__.py
      reason: "Adicionar `stats` no bloco `from nyx.agent.commands import (...)` mantendo ordem alfabética (entre `session` e `sudo_mode`)."
      linhas_alvo: "13-29 (bloco de imports)"
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/agent/commands/session.py
      reason: "Renomear `@nyx_command(name='stats', ...)` para `name='session-stats'` (linha 148) — resolve colisão de nome com novo /stats. Atualizar docstring do módulo (linha 1) trocando 'stats' por 'session-stats'. Sentinela retornada continua `'__stats__'` (cli_handlers._handle_stats consome por valor, não por nome do comando)."
      linhas_alvo: "1, 148-152"
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/agent/commands/_registry.py
      reason: "HELP_COLUMN_GROUPS['Sessão'] (linha 92): trocar `'stats'` por `'session-stats'`. ESSENTIAL_COMMANDS (linhas 75-86) não contém 'stats', então nenhuma mudança ali."
      linhas_alvo: "92"
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/scripts/gauntlet/nyx_gauntlet.py
      reason: "P5S-05 (linhas 2832-2835): trocar `handle_command('/stats', ...)` por `handle_command('/session-stats', ...)` (sentinela ainda é '__stats__'). Adicionar novo check P5S-07 que invoca `/stats` (proxy DOWN, esperado) e verifica que retorno é string contendo 'proxy offline' (sem crash). Mantém P5S-05 funcionando após renomeio."
      linhas_alvo: "2832-2835 (renomear), inserção após 2840 (novo P5S-07)"

  creates:
    - /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/agent/commands/stats.py
  removes: []

  n_to_n_pairs:
    - descricao: "Cada referência ao comando antigo /stats migra para /session-stats; novo /stats vira ponto único de consumo do endpoint."
      paths:
        - /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/agent/commands/session.py
        - /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/agent/commands/_registry.py
        - /home/andrefarias/Desenvolvimento/Nyx-Code/scripts/gauntlet/nyx_gauntlet.py

  forbidden:
    - "Tocar `cli_handlers.py:_handle_stats` (linha 708): sentinela `__stats__` permanece. Renomear só o nome registrado, não o sentinela."
    - "Adicionar alias para /stats ou /session-stats (enunciado: 'sem aliases extras')."
    - "Trocar httpx por requests/urllib se httpx já é dependência ubíqua (system.py, summarizer.py, completer.py, web_search.py, web_fetch.py, loop/_iteration.py, loop/_core.py usam httpx). Decisão: usar httpx síncrono via `httpx.get(url, timeout=...)` — segue o idioma do projeto."
    - "Hardcode da porta 11436 — usar `PROXY_PORT` ou `PROXY_URL` de `nyx.config.defaults` (mesmo idioma de system.py linhas 12-28)."
    - "Spawn de subprocess no path do comando."
    - "Emojis em código/output/commit (ADR-005)."
    - "Menção a IA externa em .py (ADR-027)."
    - "Mencionar nome de modelo/provider no output do comando (ADR-004)."
    - "Crash do REPL em qualquer cenário de erro (timeout, refused, 4xx, 5xx, JSON inválido, chaves faltantes)."

  tests:
    - cmd: "./run.sh --smoke"
      timeout: 30
      deve_passar: "boot ok"
    - cmd: "bash scripts/sprint_invariants.sh"
      timeout: 60
      deve_passar: "FAIL_AFTER <= FAIL_BEFORE (baseline 0)"
    - cmd: "python3 -c \"from nyx.agent.commands import handle_command; print(handle_command('/stats', '/tmp'))\""
      timeout: 15
      deve_passar: "string contendo '[stats]' e (com proxy DOWN) 'proxy offline'; sem traceback"
    - cmd: "python3 -c \"from nyx.agent.commands import handle_command; print(handle_command('/session-stats', '/tmp'))\""
      timeout: 5
      deve_passar: "retorna '__stats__' (sentinela inalterada após renomeio)"
    - cmd: "./run.sh --gauntlet --only p5_session"
      timeout: 120
      deve_passar: "P5S-05 PASS com /session-stats e novo P5S-07 PASS com /stats (proxy offline path)"
    - cmd: "./run.sh --gauntlet --only interface"
      timeout: 120
      deve_passar: "IF-03 /help inclui /stats no listing; sem regressão em IF-04, IF-05"
    - cmd: "./run.sh --gauntlet --only rapido"
      timeout: 300
      deve_passar: "100% (regression-free)"
    - cmd: "python3 -m ruff check nyx/agent/commands/stats.py nyx/agent/commands/__init__.py nyx/agent/commands/session.py nyx/agent/commands/_registry.py"
      timeout: 10
      deve_passar: "All checks passed!"
    - cmd: "~/.config/zsh/scripts/validar-acentuacao.py nyx/agent/commands/stats.py nyx/agent/commands/__init__.py nyx/agent/commands/session.py nyx/agent/commands/_registry.py scripts/gauntlet/nyx_gauntlet.py"
      timeout: 10
      deve_passar: "exit 0"

  acceptance_criteria:
    - "Existe `nyx/agent/commands/stats.py` com função decorada `@nyx_command(name='stats', description='<...>', category='debug', examples=['/stats'])` (sem aliases)."
    - "Handler do novo /stats faz `httpx.get(f'{PROXY_URL}/admin/stats', timeout=2.0)` (ou equivalente usando PROXY_PORT) e retorna string PT-BR multilinha começando com '[stats]'."
    - "Output proxy UP exatamente no formato (ordem e prefixo): linha 1 '[stats]'; linha 2 'OOM recovery count: <N>'; linha 3 'num_gpu atual: <C> (inicial: <I>)'; linha 4 'degraded: sim' OU 'degraded: não'."
    - "Output proxy DOWN: string única '[stats] proxy offline (porta <PROXY_PORT> não responde)'."
    - "Output HTTP 4xx/5xx: '[stats] proxy retornou erro <code>'."
    - "Output JSON inválido / chaves ausentes: '[stats] proxy resposta inválida'."
    - "Nenhum cenário causa `raise` para fora do handler (REPL fica vivo). Todas as exceções de httpx (`ConnectError`, `TimeoutException`, `HTTPStatusError`, `RequestError`) e `json`/`KeyError`/`ValueError` são capturadas."
    - "Renomeação cirúrgica: `session.py` linha 148 troca `name='stats'` por `name='session-stats'`. Função, sentinela retornada (`'__stats__'`) e categoria (`'sessão'`) permanecem inalteradas. Examples do decorator atualizam para `['/session-stats']`."
    - "_registry.py linha 92: tuple do grupo 'Sessão' troca `'stats'` por `'session-stats'`. Tamanho do tuple permanece o mesmo."
    - "__init__.py: `stats` aparece no bloco `from nyx.agent.commands import (...)` em ordem alfabética entre `session` e `sudo_mode`."
    - "Gauntlet P5S-05 atualizado para invocar `/session-stats` (sentinela `__stats__` continua o asserto). Novo P5S-07 invoca `/stats` com proxy DOWN e verifica que retorno contém 'proxy offline' e não levanta exceção."
    - "IF-03 (gauntlet interface): /help mostra /stats com descrição PT-BR (validado pelo gauntlet via len > 0; descrição não é asserto literal)."
    - "Smoke ok + invariantes 14/14 + ruff All checks passed em todos arquivos tocados + acentuação exit 0."
    - "Sem emojis, sem menção a IA externa, sem menção a modelo/provider no output do /stats."
```

---

**Status:** RASCUNHO
**Data criação:** 2026-05-20
**Modelo obrigatório:** claude-opus-4-7 (sem subagentes; Read/Grep/Glob direto)

---

## Contexto

INFRA-OOM-02 (concluída 2026-05-20) instrumentou graceful degradation OOM do proxy: criou contador `state["oom_recovery_count"]`, snapshot imutável `num_gpu_initial` e endpoint loopback-only `GET /admin/stats` (proxy.py linhas 804-825). O endpoint está live e validado em runtime — retorna JSON `{oom_recovery_count, num_gpu_current, num_gpu_initial, oom_degraded}`.

Anti-débito declarado pelo INFRA-OOM-02 (item 2 do out-of-scope): expor o endpoint via slash command CLI para auditoria sem `curl` manual. Registrado no MASTER linha 125bb como RASCUNHO. Esta sprint executa esse anti-débito.

### Conflito identificado durante o planejamento

Verificação pré-execução via grep encontrou colisão direta com o enunciado original da sprint:

- `nyx/agent/commands/session.py:148` já tem `@nyx_command(name="stats", description="Estatísticas detalhadas da sessão", category="sessão", examples=['/stats', '/stats verbose'])` mapeado para `cmd_stats` que retorna sentinela `"__stats__"`.
- `nyx/cli_handlers.py:708` `_handle_stats` consome o sentinela `"__stats__"` e imprime métricas de sessão (iterações, arquivos lidos, parser success rate, tools registradas).
- `nyx/agent/commands/_registry.py:92` `HELP_COLUMN_GROUPS["Sessão"]` lista `"stats"` no grupo Sessão.
- `scripts/gauntlet/nyx_gauntlet.py:2833` P5S-05 valida `handle_command("/stats", ...) == "__stats__"`.

Criar `commands/stats.py` decorado com `@nyx_command(name="stats", ...)` causaria sobrescrita no registry (`_registry.py:53` faz `_COMMANDS[name] = cmd` sem checar duplicata). O comando antigo viraria zumbi: import de `session.cmd_stats` continuaria executar o decorator, mas `stats.cmd_stats` (importado depois — `s` vem antes de `session` no init alfabético... não, espera: ordem dos imports no `__init__.py` é alfabética crescente, então `session` vem ANTES de `stats` se `stats` for adicionado após `session`. Mas alfabeticamente `s-e-s-s-i-o-n` vem antes de `s-t-a-t-s`, portanto `stats` é importado depois e venceria a colisão — o /stats antigo sumiria silenciosamente, P5S-05 quebra).

### Resolução do conflito (escolha justificada)

Opção adotada: **renomear o comando antigo de `/stats` para `/session-stats`**. Justificativa:

- O enunciado original da sprint pede explicitamente `nyx/agent/commands/stats.py` NOVO + categoria `debug` + output que começa com `[stats]`. Manter essa especificação intacta preserva a intenção declarada do usuário.
- O `/stats` antigo é métrica de sessão (iterações, arquivos, parser) — semanticamente `/session-stats` é mais descritivo. Não há aliases/atalhos a preservar (verificado: `aliases=[]` no decorator atual).
- O sentinela `"__stats__"` continua válido — `cli_handlers._handle_stats` consome por valor de retorno, não pelo nome do comando registrado. Zero mudança em `cli_handlers.py`.
- Custo: 1 linha em `session.py` (nome), 1 linha em `_registry.py` (tuple), 1 linha em `nyx_gauntlet.py:2833` (string passada ao gauntlet). Mais 1 P5S novo para cobrir o novo /stats.

Opções rejeitadas:

- **Rebatizar o novo para `/proxy-stats`**: viola enunciado literal ("Slash `/stats` em PT-BR"). Quem escreveu o anti-débito quis `/stats`.
- **Subcomando `/stats proxy`**: complica handler (precisa dispatchar interno), aumenta superfície de teste, dilui semântica.
- **Unificar saída**: viola "Sem emojis. PT-BR estilo Nyx: frase curta, sem floreio" — empilhar 2 seções num só comando contraria a estética.

Decisão registrada para auditoria: a renomeação é trivial e reversível. Se rejeitada pelo usuário em revisão, alternativa fallback é Opção B (subcomando) — mas a Opção A adotada é mais cirúrgica e respeita melhor o enunciado.

### Sintoma observável (antes desta sprint)

```bash
$ curl -s http://127.0.0.1:11436/admin/stats | python -m json.tool
{
    "oom_recovery_count": 0,
    "num_gpu_current": 15,
    "num_gpu_initial": 15,
    "oom_degraded": false
}
```

Operador hoje precisa de `curl` na CLI. Esta sprint substitui por `/stats` direto no REPL.

---

## Escopo (touches autorizados)

### Arquivos a modificar

- `/home/andrefarias/Desenvolvimento/Nyx-Code/nyx/agent/commands/__init__.py` (49L)
  - Bloco `from nyx.agent.commands import (...)` (linhas 13-29): adicionar `stats` em ordem alfabética entre `session` e `sudo_mode`.

- `/home/andrefarias/Desenvolvimento/Nyx-Code/nyx/agent/commands/session.py` (189L)
  - Linha 1 (docstring): trocar `"...stats, usage..."` por `"...session-stats, usage..."`.
  - Linha 148 (decorator): `name="stats"` → `name="session-stats"`; `examples=['/stats', '/stats verbose']` → `examples=['/session-stats', '/session-stats verbose']`.
  - Função `cmd_stats` permanece (não renomear; só o decorator muda).
  - Retorno `"__stats__"` permanece (sentinela inalterada).

- `/home/andrefarias/Desenvolvimento/Nyx-Code/nyx/agent/commands/_registry.py` (~198L)
  - Linha 92: `"Sessão": ("resume", "compact", "context", "clear", "quit", "stats", "cancel", "status"),` → `"Sessão": ("resume", "compact", "context", "clear", "quit", "session-stats", "cancel", "status"),`

- `/home/andrefarias/Desenvolvimento/Nyx-Code/scripts/gauntlet/nyx_gauntlet.py`
  - Linhas 2832-2835 (P5S-05): trocar `handle_command("/stats", ...)` por `handle_command("/session-stats", ...)`. Texto do `_add` em P5S-05 também atualiza ("/session-stats retorna magic").
  - Inserir após linha 2840 (após P5S-06): novo P5S-07 invocando `/stats` (proxy DOWN durante gauntlet — esperado quando o test runner não sobe proxy real). Esperado: retorno é string não-vazia contendo `"proxy offline"` ou `"[stats]"` e nenhuma exceção propaga.

### Arquivos a criar

- `/home/andrefarias/Desenvolvimento/Nyx-Code/nyx/agent/commands/stats.py` (~50L)
  - Imports: `httpx` (lazy dentro do handler para evitar custo de import em registry); `nyx.agent.commands._registry.nyx_command`; `nyx.config.defaults.PROXY_PORT` (ou `PROXY_URL`).
  - Decorator: `@nyx_command(name="stats", description="Estado do proxy local: OOM recovery, num_gpu, degradação", category="debug", examples=["/stats"])`.
  - Função `cmd_stats(_args: str, _root: str) -> str` (note: nome `cmd_stats` colide com `session.cmd_stats` se houver `from .session import cmd_stats` em algum lugar — confirmar via grep antes de implementar; provavelmente safe porque ninguém importa o cmd_stats por nome, só o decorator o registra). Para zero ambiguidade, usar nome interno distinto: `cmd_stats_proxy` (a função em si não tem ligação semântica com o nome do comando — o registry usa `name="stats"` do decorator).
  - Lógica:
    1. `from nyx.config.defaults import PROXY_PORT, PROXY_URL`
    2. `try: import httpx; r = httpx.get(f"{PROXY_URL}/admin/stats", timeout=2.0)`
    3. Se `httpx.ConnectError` ou `httpx.TimeoutException`: retorna `f"[stats] proxy offline (porta {PROXY_PORT} não responde)"`.
    4. Se `r.status_code >= 400`: retorna `f"[stats] proxy retornou erro {r.status_code}"`.
    5. `try: data = r.json()` — se `json.JSONDecodeError` / `ValueError`: retorna `"[stats] proxy resposta inválida"`.
    6. Lê chaves esperadas com `.get(...)` defensivo; se faltar qualquer chave essencial (`oom_recovery_count`, `num_gpu_current`, `num_gpu_initial`, `oom_degraded`): retorna `"[stats] proxy resposta inválida"`.
    7. Renderiza:
       ```
       [stats]
       OOM recovery count: <N>
       num_gpu atual: <C> (inicial: <I>)
       degraded: <"sim" if oom_degraded else "não">
       ```
    8. Catch genérico `Exception` no final → `f"[stats] erro inesperado: {type(exc).__name__}"`. Evita crash do REPL.

### Arquivos NÃO a tocar

- `nyx/cli_handlers.py` — `_handle_stats` (linha 708) consome sentinela `"__stats__"` por valor; sem mudança necessária.
- `nyx/cli.py` — não há referência hardcoded ao nome `"stats"` que precise de atualização (verificar via grep para confirmar).
- `nyx/proxy.py` — endpoint `/admin/stats` já existe e está validado. Sem mudança.
- `nyx/config/defaults.py` — `PROXY_PORT=11436` e `PROXY_URL=f"http://{OLLAMA_HOST}:{PROXY_PORT}"` já existem.
- Qualquer outro `commands/*.py`.

---

## Invariantes a preservar

Do `VALIDATOR_BRIEF.md` (CORE - Checks universais):

1. Smoke boot obrigatório antes de marcar CONCLUIDA.
2. Sem emojis em código/commit/doc.
3. Sem menção a IA externa em `.py`.
4. Acentuação PT-BR correta nos arquivos tocados (validador `~/.config/zsh/scripts/validar-acentuacao.py`).
5. Cleanup explícito após teste com modelo (não aplicável a esta sprint — não carrega modelo).
6. Nenhum débito implícito — qualquer achado vira sprint nova com ID.

ADRs aplicáveis (do enunciado):

7. ADR-004 — sem menção a provider/modelo subjacente no output user-facing.
8. ADR-005 — sem emojis.
9. ADR-027 — sem menção a IA externa em código.
10. ADR-001 (Local First) — `httpx.get` usa loopback (`127.0.0.1` via PROXY_URL); endpoint do proxy já tem guard loopback-only.

Acoplamentos descobertos na exploração:

11. `_COMMANDS[name] = cmd` em `_registry.py:53` sobrescreve duplicatas silenciosamente — renomear o /stats antigo ANTES de criar o novo previne zumbi.
12. Sentinela `"__stats__"` em `cli_handlers._handle_stats:709` é consumida por igualdade exata — não muda com o renomeio do comando.
13. Ordem alfabética em `__init__.py:13-29` é convenção (validada pelo scaffold em SCAFFOLD-CMD-FIX-01) — inserir `stats` entre `session` e `sudo_mode`.
14. `httpx` é dependência ubíqua (cli_boot, summarizer, completer, web_search, web_fetch, loop/_iteration, loop/_core, system.cmd_doctor) — não há motivo pra preferir `urllib`. Mantém o idioma.
15. `cmd_doctor` em `system.py:99-117` já mostra padrão de chamada httpx ao proxy — replicar idioma (timeout=5s lá, aqui 2s porque /admin/stats é leitura pura sem subprocess).

---

## Acceptance criteria

1. `nyx/agent/commands/stats.py` existe e tem `@nyx_command(name="stats", description="<...>", category="debug", examples=["/stats"])`.
2. `handle_command("/stats", "/tmp")` com proxy DOWN retorna string PT-BR contendo `"proxy offline"` e prefixo `"[stats]"`, **sem traceback**.
3. `handle_command("/stats", "/tmp")` com proxy UP e endpoint live retorna string com 4 linhas no formato:
   - linha 1: `[stats]`
   - linha 2: `OOM recovery count: <int>`
   - linha 3: `num_gpu atual: <int> (inicial: <int>)`
   - linha 4: `degraded: sim` ou `degraded: não`
4. HTTP 4xx/5xx do proxy → `[stats] proxy retornou erro <code>` (sem traceback).
5. JSON inválido ou chaves faltantes → `[stats] proxy resposta inválida` (sem traceback).
6. `handle_command("/session-stats", "/tmp")` retorna sentinela `"__stats__"` (renomeado, função/sentinela inalteradas).
7. `commands/__init__.py` importa `stats` em ordem alfabética entre `session` e `sudo_mode`. Total de imports passa de 15 para 16 módulos.
8. `_registry.py:HELP_COLUMN_GROUPS["Sessão"]` substitui `"stats"` por `"session-stats"`. Tamanho do tuple = 8 (igual ao antes).
9. Gauntlet P5S-05 atualizado e PASS. Novo P5S-07 PASS validando que `/stats` com proxy DOWN retorna string esperada sem crash.
10. Gauntlet IF-03 (`/help`) continua PASS — `/stats` aparece no listing (novo, categoria `debug`).
11. Gauntlet `--only rapido` 100% (regression-free).
12. Smoke + invariantes 14/14.
13. `python3 -m ruff check` nos 4 arquivos tocados + novo = All checks passed.
14. Validador de acentuação exit 0 nos 5 arquivos tocados.
15. Sem emojis no novo arquivo, no diff dos modificados, no commit message.

---

## Plano de implementação

### Passo 0 — Conferir baseline

```bash
cd /home/andrefarias/Desenvolvimento/Nyx-Code
wc -l nyx/agent/commands/__init__.py nyx/agent/commands/session.py nyx/agent/commands/_registry.py
bash scripts/sprint_invariants.sh > /tmp/inv_before.txt 2>&1
tail -5 /tmp/inv_before.txt   # FAIL_BEFORE esperado 0
./run.sh --gauntlet --only p5_session 2>&1 | tail -20 > /tmp/p5s_before.txt
./run.sh --gauntlet --only interface 2>&1 | tail -20 > /tmp/if_before.txt
```

Esperado: 49 / 189 / ~198, FAIL=0, P5S-05 PASS (referência), IF-03 PASS.

### Passo 1 — Verificar hipóteses (PRÉ-0.3 protocolo, lição 4)

```bash
# Confirmar que /stats colide
grep -n 'name="stats"\|name='\''stats'\''' nyx/agent/commands/*.py
# Esperado: session.py:148 (único hit)

# Confirmar sentinela
grep -n '__stats__' nyx/ -r
# Esperado: 2 hits (session.py:152 retorna, cli_handlers.py:709 consome)

# Confirmar HELP_COLUMN_GROUPS
grep -n '"stats"' nyx/agent/commands/_registry.py
# Esperado: 1 hit (linha 92)

# Confirmar P5S-05
grep -n "'/stats'" scripts/gauntlet/nyx_gauntlet.py
# Esperado: 1 hit em ~2833

# Confirmar imports do __init__
grep -n "from nyx.agent.commands import" nyx/agent/commands/__init__.py
# Esperado: linha 13 abrindo o bloco

# Confirmar PROXY_PORT e PROXY_URL
grep -n "^PROXY_PORT\|^PROXY_URL" nyx/config/defaults.py
# Esperado: PROXY_PORT=11436, PROXY_URL=f"http://{OLLAMA_HOST}:{PROXY_PORT}"

# Confirmar endpoint vivo no proxy
grep -n 'handle_stats\|add_get."/admin/stats"' nyx/proxy.py
# Esperado: 2-3 hits (def, registro de rota, docstring)

# Confirmar que httpx é dependência ubíqua
grep -rn "import httpx" nyx/agent/commands/ | head -5
# Esperado: pelo menos 3 hits em system.py
```

Se algum hit divergir do esperado, **PARAR** e reportar — não codificar com hipótese quebrada.

### Passo 2 — Renomear /stats antigo para /session-stats

Edição em `nyx/agent/commands/session.py`:

```python
# Linha 1 (docstring do módulo):
"""Comandos de sessão -- session, resume, rewind, export, copy, summary, session-stats, usage, context, btw, files, trace."""

# Linha 148-152 (decorator + função):
@nyx_command(name="session-stats", description="Estatísticas detalhadas da sessão", category="sessão",
    examples=['/session-stats', '/session-stats verbose'],
)
def cmd_stats(_args: str, _root: str) -> str:
    return "__stats__"
```

Note: nome interno `cmd_stats` permanece (refatorar o nome interno é fora de escopo). Sentinela `"__stats__"` inalterada.

### Passo 3 — Atualizar HELP_COLUMN_GROUPS

Edição em `nyx/agent/commands/_registry.py` linha 92:

```python
"Sessão": ("resume", "compact", "context", "clear", "quit", "session-stats", "cancel", "status"),
```

Tamanho do tuple permanece 8.

### Passo 4 — Atualizar P5S-05 do gauntlet

Edição em `scripts/gauntlet/nyx_gauntlet.py` linhas 2832-2835:

```python
        # P5S-05: /session-stats retorna magic (renomeado em INFRA-OOM-STATS-CLI-01)
        r = handle_command("/session-stats", str(PROJECT_ROOT))
        ok = r == "__stats__"
        self._add("P5S-05", "/session-stats retorna magic", "p5_session", ok, 0)
```

### Passo 5 — Criar novo nyx/agent/commands/stats.py

Conteúdo completo (~50L):

```python
"""Slash command /stats -- consome GET /admin/stats do proxy local (INFRA-OOM-STATS-CLI-01)."""

from __future__ import annotations

from nyx.agent.commands._registry import nyx_command
from nyx.config.defaults import PROXY_PORT, PROXY_URL

_CHAVES_OBRIGATORIAS = (
    "oom_recovery_count",
    "num_gpu_current",
    "num_gpu_initial",
    "oom_degraded",
)


@nyx_command(
    name="stats",
    description="Estado do proxy local: OOM recovery, num_gpu, degradação",
    category="debug",
    examples=["/stats"],
)
def cmd_stats_proxy(_args: str, _root: str) -> str:
    """Retorna snapshot do estado do proxy via GET /admin/stats.

    Erros (rede, HTTP, JSON, chave faltante) viram strings amigáveis;
    o REPL nunca crasha. Loopback-only no servidor (proxy.py).
    """
    try:
        import httpx
    except ImportError:
        return "[stats] dependência httpx ausente"

    url = f"{PROXY_URL}/admin/stats"
    try:
        r = httpx.get(url, timeout=2.0)
    except (httpx.ConnectError, httpx.TimeoutException):
        return f"[stats] proxy offline (porta {PROXY_PORT} não responde)"
    except httpx.RequestError as exc:
        return f"[stats] proxy inacessível: {type(exc).__name__}"
    except Exception as exc:  # pragma: no cover -- defensivo
        return f"[stats] erro inesperado: {type(exc).__name__}"

    if r.status_code >= 400:
        return f"[stats] proxy retornou erro {r.status_code}"

    try:
        data = r.json()
    except (ValueError, Exception):
        return "[stats] proxy resposta inválida"

    if not isinstance(data, dict) or not all(k in data for k in _CHAVES_OBRIGATORIAS):
        return "[stats] proxy resposta inválida"

    degraded_str = "sim" if data["oom_degraded"] else "não"
    return (
        "[stats]\n"
        f"OOM recovery count: {data['oom_recovery_count']}\n"
        f"num_gpu atual: {data['num_gpu_current']} (inicial: {data['num_gpu_initial']})\n"
        f"degraded: {degraded_str}"
    )


# "Observar o estado é metade de manter o sistema vivo." -- INFRA-OOM-STATS-CLI-01
```

Notas:

- `except (ValueError, Exception)`: ruff vai reclamar de `Exception` redundante após `ValueError`. Trocar para `except Exception:` puro (capturar tudo na decodificação JSON é defensivo, mesmo que feio). Ajustar conforme ruff.
- `pragma: no cover` aceitável aqui; gauntlet não exercita o catch genérico.
- Nome interno `cmd_stats_proxy` (não `cmd_stats`) para evitar colisão de símbolo com `session.cmd_stats`.

### Passo 6 — Atualizar __init__.py

Edição em `nyx/agent/commands/__init__.py` linhas 13-29: inserir `stats,` entre `session,` e `sudo_mode,`:

```python
from nyx.agent.commands import (  # noqa: F401  -- side-effect: registra @nyx_command
    aesthetic,
    code,
    core,
    debug_cmds,
    git_cmds,
    mcp,
    output_style,
    plan,
    plugin,
    progress,
    sandbox,
    schema,
    session,
    stats,
    sudo_mode,
    system,
)
```

Total de módulos: 15 → 16.

### Passo 7 — Inserir novo P5S-07 no gauntlet

Em `scripts/gauntlet/nyx_gauntlet.py` após linha 2840 (após P5S-06), inserir:

```python
        # P5S-07: /stats (proxy DOWN) retorna mensagem amigável sem crash (INFRA-OOM-STATS-CLI-01)
        try:
            r = handle_command("/stats", str(PROJECT_ROOT))
            crashed = False
        except Exception:
            r = None
            crashed = True
        ok = (not crashed) and isinstance(r, str) and "[stats]" in r and (
            "proxy offline" in r or "OOM recovery count" in r
        )
        self._add(
            "P5S-07",
            "/stats CLI consome /admin/stats (proxy DOWN ok)",
            "p5_session",
            ok,
            0,
            details=(r or "")[:80],
        )
```

Note: o teste aceita tanto `"proxy offline"` (proxy DOWN durante gauntlet) quanto `"OOM recovery count"` (proxy UP em ambiente raro). Cobre os 2 cenários.

### Passo 8 — Validar pipeline completo

```bash
cd /home/andrefarias/Desenvolvimento/Nyx-Code

# Smoke
./run.sh --smoke

# Invariantes
bash scripts/sprint_invariants.sh > /tmp/inv_after.txt 2>&1
diff /tmp/inv_before.txt /tmp/inv_after.txt
tail -5 /tmp/inv_after.txt   # PASS 14/14, FAIL 0

# Ruff
python3 -m ruff check nyx/agent/commands/stats.py nyx/agent/commands/__init__.py nyx/agent/commands/session.py nyx/agent/commands/_registry.py scripts/gauntlet/nyx_gauntlet.py

# Acentuação
~/.config/zsh/scripts/validar-acentuacao.py \
  nyx/agent/commands/stats.py \
  nyx/agent/commands/__init__.py \
  nyx/agent/commands/session.py \
  nyx/agent/commands/_registry.py \
  scripts/gauntlet/nyx_gauntlet.py

# Runtime real: /stats com proxy DOWN
python3 -c "from nyx.agent.commands import handle_command; print(handle_command('/stats', '/tmp'))"
# Esperado: '[stats] proxy offline (porta 11436 não responde)'

# Runtime real: /session-stats
python3 -c "from nyx.agent.commands import handle_command; print(repr(handle_command('/session-stats', '/tmp')))"
# Esperado: '__stats__'

# Runtime real: /stats com proxy UP (opcional, requer proxy live)
./run.sh --headless &
PID=$!
sleep 5
python3 -c "from nyx.agent.commands import handle_command; print(handle_command('/stats', '/tmp'))"
# Esperado:
# [stats]
# OOM recovery count: 0
# num_gpu atual: 15 (inicial: 15)
# degraded: não
kill $PID
pkill -f "nyx/proxy.py" 2>/dev/null
pkill -f "ollama serve" 2>/dev/null

# Gauntlet
./run.sh --gauntlet --only p5_session
./run.sh --gauntlet --only interface
./run.sh --gauntlet --only rapido
```

Esperado: tudo PASS, P5S-05 e P5S-07 PASS, sem regressão.

### Passo 9 — Commit

```
feat(INFRA-OOM-STATS-CLI-01): /stats CLI consumindo /admin/stats; antigo vira /session-stats
```

---

## Aritmética

Sprint é feature + renomeio cirúrgico. Sem meta numérica de redução de linhas.

- `nyx/agent/commands/__init__.py`: 49L → 50L (delta +1L: nova linha `stats,`).
- `nyx/agent/commands/session.py`: 189L → 189L (delta 0L: edições in-place na docstring e decorator).
- `nyx/agent/commands/_registry.py`: ~198L → ~198L (delta 0L: substituição de string in-place).
- `nyx/agent/commands/stats.py`: 0L → ~55L (novo arquivo).
- `scripts/gauntlet/nyx_gauntlet.py`: atual → +~18L (P5S-07 novo; P5S-05 in-place).

Delta total estimado: ~74L adicionadas, 0L removidas. Nenhum arquivo cruza teto crítico.

---

## Testes

### Baseline a coletar antes de iniciar

```bash
wc -l nyx/agent/commands/__init__.py nyx/agent/commands/session.py nyx/agent/commands/_registry.py
bash scripts/sprint_invariants.sh | tail -5    # FAIL_BEFORE = 0
./run.sh --gauntlet --only p5_session 2>&1 | tail -20  # P5S-05 PASS
./run.sh --gauntlet --only interface 2>&1 | tail -20   # IF-03 PASS
./run.sh --gauntlet --only rapido 2>&1 | tail -10      # contagem PASS global
```

### Esperado após implementação

- `FAIL_AFTER` == `FAIL_BEFORE` (0). Smoke ok.
- Gauntlet p5_session: passes ≥ baseline + 1 (P5S-07 novo PASS). P5S-05 mantém PASS após renomeio.
- Gauntlet interface: passes ≥ baseline (IF-03 incluindo /stats no listing; /session-stats também presente).
- Gauntlet rapido: 100% (sem regressão).

---

## Proof-of-work esperado

- **Diff final**: git diff cobrindo `nyx/agent/commands/{__init__.py, session.py, stats.py, _registry.py}` + `scripts/gauntlet/nyx_gauntlet.py`.
- **Runtime real** (do `VALIDATOR_BRIEF.md` CORE):
  - `./run.sh --smoke` → boot ok.
  - `bash scripts/sprint_invariants.sh` → 14/14 PASS, FAIL 0.
  - `./run.sh --gauntlet --only p5_session` → 100% (P5S-05 + P5S-07 PASS).
  - `./run.sh --gauntlet --only interface` → 100%.
  - `./run.sh --gauntlet --only rapido` → 100%.
- **Probes diretos**:
  - `python3 -c "from nyx.agent.commands import handle_command; print(handle_command('/stats', '/tmp'))"` com proxy DOWN → string começa com `[stats]` e contém `proxy offline`. Sem traceback.
  - `python3 -c "from nyx.agent.commands import handle_command; print(repr(handle_command('/session-stats', '/tmp')))"` → `'__stats__'`.
  - Opcional com proxy UP: output 4 linhas conforme formato canônico.
- **Ruff**: `python3 -m ruff check` nos 5 arquivos → All checks passed.
- **Acentuação periférica**: validador em todos arquivos tocados → exit 0.
- **Hipótese verificada via rg** (pré-implementação): confirmar `name="stats"` único em `session.py:148`; `"__stats__"` em 2 hits; `HELP_COLUMN_GROUPS` linha 92; P5S-05 em `nyx_gauntlet.py:2833`; `PROXY_PORT`/`PROXY_URL` em `defaults.py:38,45`; endpoint live em `proxy.py:804,878`.
- **Cleanup pós-teste** (se proxy foi subido para teste UP): `pkill -f "nyx/proxy.py"`, `pkill -f "ollama serve"`, `nvidia-smi`.

---

## Riscos e mitigações

| Risco | Mitigação |
|---|---|
| Renomeio de /stats quebra ação muscle-memory do usuário ("eu sempre digitei /stats") | Mensagem do commit deixa claro: "/stats é agora proxy stats; sessão moveu para /session-stats". /help mostra ambos. |
| `_COMMANDS[name] = cmd` no registry sobrescreve silenciosamente se renomeio falhar | Passo 1 grep confirma único hit antes; Passo 2 renomeia ANTES de Passo 5 criar o novo. Ordem importa. |
| Import lazy de httpx em handler aumenta latência da 1ª chamada | Aceitável; outros commands fazem o mesmo (`system.cmd_doctor:100,110`). REPL latency budget tolerante. |
| Timeout 2s curto demais em proxy lento | Endpoint é leitura pura de dict in-memory; resposta sub-10ms em healthy state. 2s é generoso. Se virar problema, sprint anti-débito INFRA-OOM-STATS-CLI-TIMEOUT-01. |
| `cli_handlers.py:_handle_stats` continua consumindo `"__stats__"` — alguém pode pensar que precisa renomear lá também | Acceptance criteria #6 explícito: sentinela inalterada. Forbidden lista cli_handlers como NÃO tocar. |
| Texto exato do output muda no futuro (ex.: i18n) | Out-of-scope; sprint vincula formato literal aqui. Se mudar, vira nova sprint. |
| ruff reclama de `except (ValueError, Exception)` | Trocar para `except Exception:` puro durante implementação. Listado no Passo 5 como ajuste. |
| ruff reclama de import de httpx dentro da função | Outros handlers usam mesmo padrão (system.py:100,110,334); precedente estabelecido. Se ruff reclamar, adicionar `# noqa: PLC0415` no import (consistente com codebase). |
| /stats no `/help` aparece em duas categorias (sessão moveu para 'sessão', proxy é 'debug') | Esperado e desejado: separa semanticamente. HELP_COLUMN_GROUPS["Sessão"] tem "session-stats"; /stats novo cai em "Outros" do help layout 3 colunas. |

---

## Out-of-scope (anti-débito)

Se durante execução surgir qualquer um destes, registrar como sprint nova:

1. **Histórico longitudinal de OOM** → `INFRA-OOM-HISTORY-01` (já catalogado MASTER linha 125cc). Persistir `oom_recovery_count` cross-session em `~/.nyx/proxy_stats.json` e mostrar evolução via `/stats history`.
2. **Cockpit web view de /admin/stats** → `COCKPIT-STATS-VIEW-01` (BAIXA, hipotética). Painel HTML no cockpit existente exibindo as 4 métricas em tempo real (polling).
3. **Métricas adicionais no endpoint** (latency p50/p99, request count, error count) → `INFRA-OBSERVABILITY-METRICS-01` (BAIXA, hipotética). Expandir contrato do `/admin/stats`.
4. **Subcomandos de /stats** (`/stats verbose`, `/stats reset`) → `INFRA-OOM-STATS-CLI-SUBCOMMANDS-01` (BAIXA). Verbose mostraria timestamps; reset não é trivial (precisa endpoint mutador).
5. **Alias `/oom` ou `/ps` para /stats** → o enunciado proíbe ("Sem aliases extras"). Se útil no futuro, vira nova sprint.
6. **Configuração de porta via flag CLI** (`--proxy-port`) → out-of-scope; usar `PROXY_PORT` de `nyx.config.defaults` é decisão fechada. Se virar requisito, sprint nova `CONFIG-PROXY-PORT-FLAG-01`.
7. **Retry intermediário num_gpu // 2** → `INFRA-OOM-RETRY-STEP-01` (MASTER linha 125aa). Não relacionado ao CLI; independente.
8. **Cobrir cenário proxy UP em gauntlet** → o gauntlet rodando localmente pode ou não ter proxy live; P5S-07 cobre o caso DOWN (mais comum em CI). Sprint nova `INFRA-OOM-STATS-CLI-LIVE-TEST-01` (BAIXA) se quiser fixture que sobe proxy em background.

---

## Referências

- VALIDATOR_BRIEF: `/home/andrefarias/Desenvolvimento/Nyx-Code/VALIDATOR_BRIEF.md`
- Sprint precedente: `dev-journey/06-sprints/concluidos/SPRINT_INFRA_OOM_02.md` — criou `/admin/stats` que esta sprint consome.
- Sprint precedente: `dev-journey/06-sprints/concluidos/SPRINT_SCAFFOLD_CMD_FIX_01.md` — estabeleceu convenção de pacote `commands/` (1 arquivo por command + ordem alfabética em `__init__.py`).
- MASTER linha 125bb: `RASCUNHO (anti-débito declarado pelo INFRA-OOM-02 — novo slash command /stats em nyx/agent/commands/ consumindo GET /admin/stats e renderizando em CLI...)`.
- ADRs: ADR-001 (Local First), ADR-004 (sem provider/modelo), ADR-005 (sem emojis), ADR-027 (sem IA externa em .py).
- Idioma de chamada httpx ao proxy: `nyx/agent/commands/system.py:99-117` (`cmd_doctor`).
- Registry de comandos: `nyx/agent/commands/_registry.py:31-58` (`nyx_command`).
- Sentinela consumer: `nyx/cli_handlers.py:708-722` (`_handle_stats`).

---

*"O endpoint sem comando é dado mudo. O comando sem endpoint é folclore. /stats fecha o ciclo." — INFRA-OOM-STATS-CLI-01*
