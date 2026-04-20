# SPRINT BUG-PORT-PARSE-01 — URL inválida `http://host:PORT1:PORT2` em todo tool call

## 0. SPEC (machine-readable)

```yaml
sprint:
  id: BUG-PORT-PARSE-01
  title: "Corrigir montagem de URL que gera `Invalid port: 'PORT1:PORT2'` em toda chamada HTTP do agente"
  onda: 22
  bloco: 2.6
  prioridade: CRÍTICA
  tipo: Bugfix
  dependencias: []
  desbloqueia: [VALIDATE-ONDA-20, CTX-01, CTX-02, CTX-03, CTX-04, TUI-FIX-08, TUI-FIX-09]

  touches:
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/run.sh
      reason: "NYX_OLLAMA_HOST é redefinido para `HOST:PORT` (linha 45); quebra o contrato implícito de que OLLAMA_HOST é apenas host"
      linhas_alvo: "44-46, 94"
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/config/settings.py
      reason: "ollama_host lê NYX_OLLAMA_HOST que pode vir com porta embutida; properties concatenam `:porta` gerando URL com porta dupla"
      linhas_alvo: "20, 34, 38, 42, 74"
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/config/defaults.py
      reason: "Revisar contrato: OLLAMA_HOST é só host (sem porta) — documentar inline e espelhar no código que lê NYX_OLLAMA_HOST"
      linhas_alvo: "7-9"
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/agent/commands/system.py
      reason: "cmd_config usa `os.environ.get('OLLAMA_HOST', _OLLAMA_URL)` — fallback mistura host com URL (inconsistência que pode propagar)"
      linhas_alvo: "34"

  creates: []
  removes: []

  n_to_n_pairs:
    - descricao: "Contrato de OLLAMA_HOST (só host, sem porta) aparece em: run.sh, settings.py, defaults.py, commands/system.py"
      paths:
        - /home/andrefarias/Desenvolvimento/Nyx-Code/run.sh
        - /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/config/settings.py
        - /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/config/defaults.py
        - /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/agent/commands/system.py

  forbidden:
    - "Fixar com regex/strip para remover porta embutida de OLLAMA_HOST — trata sintoma, não causa"
    - "Duplicar variável: criar NYX_OLLAMA_HOST_ONLY além de NYX_OLLAMA_HOST — proliferação de estado"
    - "Silenciar o erro com try/except em volta de httpx — é sinal legítimo de URL inválida"
    - "Corrigir apenas settings.py sem corrigir run.sh — N-para-N exige alinhar ambos"
    - "Alterar proxy.py — já usa `args.ollama_port` explícito (linha 293), não é a origem do bug"
    - "Adicionar emoji ou menção a IA em commits"
    - "Tocar em qualquer arquivo fora dos 4 touches — se descobrir bug colateral, materializar sprint nova (protocolo anti-débito)"

  tests:
    - cmd: "./run.sh --gauntlet --only rapido"
      timeout: 300
      deve_passar: "todos os testes passam (proxy/ollama URL consistente)"
    - cmd: "manual: ./run.sh, pedir `liste os arquivos em nyx/agent/` e confirmar que não aparece 'Invalid port' em nenhuma linha do stdout"
      timeout: 60
    - cmd: "manual: ./run.sh, executar `/config` e conferir que `ollama:` mostra URL bem formada `http://127.0.0.1:11435` (zero `:` extras)"
      timeout: 30

  acceptance_criteria:
    - "Nenhuma linha do REPL contém 'Invalid port' após prompt livre com tool call"
    - "`/config` mostra `ollama: http://127.0.0.1:11435` (não `http://127.0.0.1:11435:11435`)"
    - "Tool `list_files` (ou qualquer outra que use http) executa sem ValueError de porta"
    - "Gauntlet rapido passa 100%"
    - "Grep `grep -rn 'NYX_OLLAMA_HOST' nyx/ run.sh` produz definições consistentes (host puro, porta separada em NYX_OLLAMA_PORT)"
    - "Acentuação PT-BR correta em tudo novo"
```

---

**Status:** PENDENTE
**Data criação:** 2026-04-19
**Origem:** achado colateral durante **VALIDATE-ONDA-20** (Rodada 1). Usuário reportou `Nyx: Invalid port: '11435:11436'` em toda resposta do modelo.
**Modelo obrigatório:** claude-opus-4-7 (sem subagentes)

---

## Contexto do projeto (snapshot — não referência)

> **ADRs relevantes:**
> - ADR-001 Local First.
> - ADR-013 Integração Obrigatória.
> - ADR-014 Testes via Gauntlet.
> - ADR-020 Testes via run.sh.
>
> **Estado do sistema:**
> - 2026-04-19, Onda 22, Bloco 2.6 Integração. Última sprint concluída: BOOT-FIX-01 (commit bb3d61b).
> - VALIDATE-ONDA-20 travada por este bug — cascata bloqueia CTX-01/02/03/04 e TUI-FIX-08/09.
> - proxy.py usa padrão correto (`OLLAMA_URL = f"http://127.0.0.1:{args.ollama_port}"` em :293) — **não é a origem**.

---

## Problema

### Sintoma observável (screenshots do usuário, 2026-04-19)

Ao rodar `./run.sh` e enviar prompt com tool call, cada resposta do modelo vem seguida de:

```
Nyx: Invalid port: '11435:11436'
[error]
```

Mensagem aparece em **toda** iteração, bloqueando 100% das chamadas HTTP do agente.

### Evidência — grep no código

```bash
$ grep -rn "Invalid port" nyx/
# (zero resultados)
```

A string **não é nossa**. Formato `Invalid port: '<valor>'` é padrão de `httpx`/`urllib3`/`http.client` quando `int(port_str)` falha.

### Análise de causa (hipótese forte)

1. **`run.sh:44-45`** define:
   ```bash
   NYX_OLLAMA_PORT="${NYX_OLLAMA_PORT:-11435}"
   NYX_OLLAMA_HOST="${NYX_OLLAMA_HOST:-127.0.0.1}:${NYX_OLLAMA_PORT}"
   ```
   Resultado: `NYX_OLLAMA_HOST=127.0.0.1:11435` (**host + porta**, contrato implícito quebrado).

2. **`run.sh:94`** exporta:
   ```bash
   export OLLAMA_HOST="$NYX_OLLAMA_HOST"
   ```
   Agora `OLLAMA_HOST` também contém porta embutida.

3. **`nyx/config/settings.py:74`** lê:
   ```python
   ollama_host=os.getenv("NYX_OLLAMA_HOST", defaults.OLLAMA_HOST),
   ```
   `defaults.OLLAMA_HOST = "127.0.0.1"` (só host, linha 7). Mas a env var tem porta → `self.ollama_host = "127.0.0.1:11435"`.

4. **`settings.py:38`** monta:
   ```python
   @property
   def proxy_url(self) -> str:
       return f"http://{self.ollama_host}:{self.proxy_port}"
   ```
   Resultado: `"http://127.0.0.1:11435:11436"`. httpx extrai `'11435:11436'` como string de porta, `int()` falha → `ValueError: Invalid port: '11435:11436'`.

5. **`nyx/agent/commands/system.py:34`** tem defeito correlato (inconsistência de tipos):
   ```python
   ollama = os.environ.get("OLLAMA_HOST", _OLLAMA_URL)
   ```
   Fallback é URL inteira (`http://host:port`), mas a env var é só `host:port`. `/config` exibe valores incomparáveis.

### Por que só apareceu agora

VALIDATE-ONDA-20 foi a primeira execução real com `./run.sh` desde o fix de boot (BOOT-FIX-01 bb3d61b). Antes, crash no boot mascarava este bug. Gauntlet `--only rapido` passa porque exercita proxy diretamente (linha 293 do `proxy.py` usa `args.ollama_port` puro, sem passar por `settings.NyxSettings`).

---

## Solução proposta

Contrato canônico: **`NYX_OLLAMA_HOST` é host puro, `NYX_OLLAMA_PORT` é porta**. Nunca concatenar.

1. `run.sh:44-46` — separar a definição:
   ```bash
   NYX_OLLAMA_PORT="${NYX_OLLAMA_PORT:-11435}"
   NYX_OLLAMA_HOST="${NYX_OLLAMA_HOST:-127.0.0.1}"   # host puro, sem porta
   ```
   Onde o shell hoje usa `NYX_OLLAMA_HOST` como `host:port` (ex: `curl "http://${NYX_OLLAMA_HOST}/..."`), trocar por `"http://${NYX_OLLAMA_HOST}:${NYX_OLLAMA_PORT}"`.

2. `run.sh:94` — manter export, mas agora com host puro:
   ```bash
   export OLLAMA_HOST="$NYX_OLLAMA_HOST"   # só host
   ```

3. `nyx/config/defaults.py:7-9` — adicionar comentário inline reforçando o contrato:
   ```python
   # OLLAMA_HOST é host puro (sem porta). Para URL use OLLAMA_URL abaixo.
   OLLAMA_HOST: str = "127.0.0.1"
   ```

4. `nyx/config/settings.py:74` — adicionar guard defensivo (validação no boundary, não mascaramento):
   ```python
   raw_host = os.getenv("NYX_OLLAMA_HOST", defaults.OLLAMA_HOST)
   if ":" in raw_host:
       raise ValueError(
           f"NYX_OLLAMA_HOST deve ser host puro (sem porta), recebido '{raw_host}'. "
           "Use NYX_OLLAMA_PORT para a porta."
       )
   ollama_host = raw_host
   ```
   Justificativa: CLAUDE.md §3 "Error handling explicito (nunca silent failures)" + §9 "Filtros sem falso-positivo — todo regex/filtro DEVE ser testado contra inputs que NÃO devem casar".

5. `nyx/agent/commands/system.py:34` — alinhar tipo do fallback:
   ```python
   ollama_host = os.environ.get("OLLAMA_HOST", defaults.OLLAMA_HOST)
   ollama_port = os.environ.get("NYX_OLLAMA_PORT", str(_OLLAMA_PORT))
   ollama = f"http://{ollama_host}:{ollama_port}"
   ```
   (import de `defaults` já existe no arquivo via `nyx.config.defaults`).

### Primeiro passo de execução (obrigatório)

Antes de editar qualquer arquivo:

```bash
./run.sh &
sleep 8
# Capturar iteração real e localizar origem do ValueError
echo "/config" | /dev/tcp/... || # usar stdin do REPL
grep -rn "httpx" nyx/agent/ | head -10
```

Alternativa menos interativa: instrumentar temporariamente `nyx/agent/loop/_core.py` (onde `httpx.AsyncClient` é instanciado) com `logger.debug("URL: %s", url)` e re-executar. **Remover instrumentação antes do commit.**

---

## Diff esperado

```
~ 4 arquivos modificados
+ 0 arquivos criados
- 0 arquivos removidos
+ ~20 linhas líquidas
```

---

## Comandos de verificação

```bash
# PASSO 1 — snapshot ANTES
bash scripts/sprint_invariants.sh > /tmp/inv_before.txt 2>&1
FAIL_BEFORE=$(grep -c "^\[FAIL\]" /tmp/inv_before.txt)

# PASSO 2 — smoke do boot fix (BOOT-FIX-01 já garantiu boot ok)
./run.sh --smoke   # deve imprimir 'boot ok'

# PASSO 3 — implementar as 4 edições

# PASSO 4 — reproduzir o cenário que falhava
./run.sh &
sleep 10
# REPL: digitar 'liste os arquivos em nyx/agent/' e enviar
# Esperado: resposta do modelo SEM 'Invalid port' e SEM [error]

# PASSO 5 — gauntlet
./run.sh --gauntlet --only rapido
# Esperado: 100% OK

# PASSO 6 — invariantes
bash scripts/sprint_invariants.sh > /tmp/inv_after.txt 2>&1
diff /tmp/inv_before.txt /tmp/inv_after.txt
```

---

## Critério binário de aceite

- [ ] Prompt `liste os arquivos em nyx/agent/` completa sem `Invalid port` no stdout
- [ ] `/config` exibe `ollama: http://127.0.0.1:11435`
- [ ] Gauntlet `--only rapido` 100%
- [ ] `FAIL_AFTER <= FAIL_BEFORE` em `sprint_invariants.sh`
- [ ] Check #13 (`./run.sh --smoke`) continua PASS
- [ ] Sprint movida para `concluidos/` com commit `fix: URL inválida com porta dupla (Invalid port cascade)`
- [ ] SPRINT_ORDER_MASTER marca CONCLUIDA com hash; narrativa do Bloco 2.6 atualizada
- [ ] Nenhuma violação de `forbidden[]`

---

## Guardrails anti-engodo

- Não marcar CONCLUIDA sem reproduzir o cenário do usuário (prompt com tool call no REPL real).
- Não trocar `httpx` por outra lib "pra evitar o erro" — é fuga.
- Se o fix exigir tocar em 5+ arquivos além dos 4 listados: **parar** e reclassificar como sprint maior (BUG-PORT-PARSE-01-v2) com spec nova.

---

## Gambiarras específicas

1. **Strip da porta embutida.** `ollama_host.split(":")[0]` em settings.py. Proibido — mascara o bug no run.sh.
2. **Fallback silencioso.** `try: int(port) except: port = 11435`. Proibido — CLAUDE.md §3.
3. **Duplicação de truth source.** Criar `NYX_OLLAMA_HOST_ONLY`. Proibido — N-para-N vai multiplicar o problema.
4. **Fixar só o sintoma em 1 arquivo.** Se só `settings.py` for editado e `run.sh:45` continuar concatenando host+porta, o bug reaparece na próxima vez que alguém ler `os.getenv("NYX_OLLAMA_HOST")` em outro ponto. Contrato canônico em **todos** os 4 arquivos ou nada.
5. **Ignorar `commands/system.py:34`.** É inconsistência de tipo correlata (fallback URL vs env host) que vai virar bug futuro. Alinhar agora.

---

## Proof-of-work obrigatório

Formato padrão (ver SPRINT_TEMPLATE_V2.md seção "Proof-of-work"). Incluir obrigatoriamente:

- `cat /tmp/inv_before.txt | tail -10`, `cat /tmp/inv_after.txt | tail -10`, diff.
- Output literal do REPL antes (com `Invalid port`) e depois (sem).
- `./run.sh --gauntlet --only rapido` final.
- Achados colaterais materializados: seguir protocolo de BOOT-FIX-01 (criar SPRINT_<ID>.md em `producao/` + linha PENDENTE no master + commit separado **antes** do commit docs de conclusão).

---

## Validação humana (checklist do usuário)

```bash
cd /home/andrefarias/Desenvolvimento/Nyx-Code
./run.sh
# REPL: enviar 'liste os arquivos em nyx/agent/'
# saída esperada: tool call executa, resposta aparece, ZERO 'Invalid port' e ZERO [error]
# /config
# saída esperada: ollama: http://127.0.0.1:11435 (uma porta só)
# Ctrl+D
```

---

## Riscos

| Risco | Mitigação |
|-------|-----------|
| Mudar `run.sh:45` quebra scripts externos que assumem `NYX_OLLAMA_HOST=host:port` | Grep exaustivo em `scripts/` e `Luna/` (se acessível) — se houver dependentes, atualizar em batch. Documentar no commit |
| `cmd_config` usado por `VALIDATE-ONDA-20` diretamente | Verificar checklist da VALIDATE-ONDA-20; se houver passo `/config`, atualizar critério |
| Instrumentação `logger.debug` esquecida no commit | Checklist inclui `grep -rn "URL: %s" nyx/` antes do commit (esperado: zero) |
| Erro pode ter segunda origem (não só settings.NyxSettings) | Primeiro passo obrigatório: instrumentar e capturar URL real que gera `ValueError`, não assumir apenas hipótese |

---

*"Um erro que se repete em todos os lugares é apenas um erro com má documentação." -- Marcus Aurelius (adaptado)*
