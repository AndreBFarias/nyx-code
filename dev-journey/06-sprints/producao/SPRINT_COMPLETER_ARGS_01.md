# SPRINT COMPLETER-ARGS-01 — Autocomplete para argumentos de slash commands

## 0. SPEC (machine-readable)

```yaml
sprint:
  id: COMPLETER-ARGS-01
  title: "Completer de argumentos para slash commands: modelos, temas, sessões, tags de memória"
  onda: 22
  bloco: 5
  prioridade: MÉDIA
  tipo: Feature
  dependencias: [UX-BUG-01]
  desbloqueia: []

  touches:
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/agent/completer.py
      reason: "Implementar _complete_command_args com dispatch por nome do command; adicionar provedores para /model, /theme, /session load, /recall"

  creates: []
  removes: []

  n_to_n_pairs:
    - descricao: "Lista de temas aceitos aparece em completer.py e no ThemeService; fonte única deve ser ThemeService"
      paths:
        - /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/agent/completer.py
        - /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/agent/services/theme_service.py
    - descricao: "Lista de modelos aparece no completer.py e no comando /model; fonte única é `ollama list` (subprocess) ou o service correspondente"
      paths:
        - /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/agent/completer.py
        - /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/agent/commands/model.py

  forbidden:
    - "Shell-out síncrono que bloqueia o prompt (subprocess.run com timeout alto)"
    - "Listar diretórios via subprocess `ls` — usar Pathlib"
    - "Cache permanente de sessões/modelos em variável global sem TTL — invalida stale"
    - "Hardcoded list de modelos ou temas — puxar da fonte canônica"
    - "Adicionar emoji ou menção a IA"
    - "Quebrar autocomplete existente de nome de comando (o que UX-BUG-01 consertou)"

  tests:
    - cmd: "./run.sh --gauntlet --only tui/completer"
      timeout: 180
      deve_passar: "100%"
    - cmd: "manual: ./run.sh, digitar '/model ' e Tab; verificar lista de modelos reais"
      timeout: 30
    - cmd: "manual: ./run.sh, digitar '/theme eri' e Tab; verificar sugestão /theme eris (ou tema com prefixo eri)"
      timeout: 30
    - cmd: "manual: ./run.sh, digitar '/session load 2026' e Tab; verificar lista de sessões com prefixo 2026"
      timeout: 30
    - cmd: "manual: ./run.sh, digitar '/recall ' e Tab; verificar lista de tags em memória"
      timeout: 30

  acceptance_criteria:
    - "Digitar `/model ` + Tab sugere modelos reais listados por `ollama list` (ou service equivalente)"
    - "Digitar `/theme <prefixo>` + Tab sugere temas que batem com o prefixo"
    - "Digitar `/session load <prefixo>` + Tab lista sessões de logs/sessions/ cujo nome começa com o prefixo"
    - "Digitar `/recall <prefixo>` + Tab lista tags de memória que começam com o prefixo"
    - "Autocomplete de nome de comando (ex: `/mod` → `/model`) continua funcionando"
    - "Nenhuma chamada síncrona que bloqueia o prompt por > 200ms"
    - "Gauntlet fase tui/completer 100%"
    - "Acentuação PT-BR correta"
```

---

**Status:** PENDENTE
**Data criação:** 2026-04-19
**Modelo obrigatório:** claude-opus-4-7 (sem subagentes)

---

## Contexto do projeto (snapshot — não referência)

> **ADRs relevantes:**
> - ADR-001 Local First: `ollama list` é chamada local.
> - ADR-013 Integração Obrigatória.
> - ADR-014 Testes via Gauntlet.
> - ADR-020 Testes via run.sh.
>
> **Estado do sistema na data da sprint:**
> - Python 3.10+, 34 tools, 47 comandos, 10 services.
> - `nyx/agent/completer.py` hoje filtra nomes de comandos por prefixo após `/`.
> - UX-BUG-01 corrigiu o trigger do popup após `/` ser digitado.
> - `/model `, `/theme `, `/session load `, `/recall ` **não sugerem** nada ao pressionar Tab.
> - Sessões ficam em `logs/sessions/*.json`. Tags de memória: serviço de memory (`nyx/agent/services/memory_service.py`).

---

## Problema

O autocomplete do prompt hoje é útil apenas para descobrir nomes de slash commands. Depois do espaço, o usuário fica sem suporte — precisa lembrar de cabeça o nome exato do modelo, do tema, do id da sessão ou da tag de memória. Isso quebra paridade com a CLI de referência e aumenta fricção em uso real.

### Sintoma observável

```
> /model <TAB>
(nada acontece)

> /theme eri<TAB>
(nada acontece)

> /session load 2026<TAB>
(nada acontece)

> /recall <TAB>
(nada acontece)
```

Em todos os casos, a UX espera uma lista filtrada por prefixo — e não recebe nada.

---

## Solução proposta

Adicionar função `_complete_command_args(command_name, arg_prefix)` em `completer.py` que faz dispatch por nome do comando. Cada dispatcher retorna `list[str]` de sugestões. Integrar ao fluxo existente do completer (que já detecta quando o cursor está depois do primeiro espaço após `/<cmd>`).

---

## Arquivos alvo (paths absolutos)

### `/home/andrefarias/Desenvolvimento/Nyx-Code/nyx/agent/completer.py`

**Antes (trecho alto nível):**
```python
class NyxCompleter:
    def get_completions(self, document, complete_event):
        text = document.text_before_cursor
        if text.startswith("/"):
            # filtra nomes de comandos por prefixo
            for cmd in self._commands:
                if cmd.startswith(text[1:]):
                    yield Completion(cmd, start_position=-(len(text)-1))
            return
        # ...
```

**Depois:**
```python
class NyxCompleter:
    def __init__(self, ...):
        ...
        self._arg_providers: dict[str, Callable[[str], list[str]]] = {
            "model": self._list_models,
            "theme": self._list_themes,
            "session": self._list_sessions_for_subcmd,
            "recall": self._list_memory_tags,
        }

    def get_completions(self, document, complete_event):
        text = document.text_before_cursor
        if not text.startswith("/"):
            return
        body = text[1:]
        if " " not in body:
            for cmd in self._commands:
                if cmd.startswith(body):
                    yield Completion(cmd, start_position=-len(body))
            return

        cmd_name, _, arg_part = body.partition(" ")
        provider = self._arg_providers.get(cmd_name)
        if provider is None:
            return
        suggestions = provider(arg_part)
        for sug in suggestions:
            yield Completion(sug, start_position=-len(arg_part))

    # provedores:
    def _list_models(self, prefix: str) -> list[str]:
        models = self._cached_models()
        return [m for m in models if m.startswith(prefix)]

    def _list_themes(self, prefix: str) -> list[str]:
        themes = self._theme_service.available_themes()
        return [t for t in themes if t.startswith(prefix)]

    def _list_sessions_for_subcmd(self, arg_part: str) -> list[str]:
        # '/session load <prefix>' — dispatch por subcomando
        sub, _, sub_prefix = arg_part.partition(" ")
        if sub == "load":
            sessions_dir = Path("logs/sessions")
            if not sessions_dir.exists():
                return []
            return [
                p.stem for p in sessions_dir.glob("*.json")
                if p.stem.startswith(sub_prefix)
            ]
        return []

    def _list_memory_tags(self, prefix: str) -> list[str]:
        tags = self._memory_service.list_tags()
        return [t for t in tags if t.startswith(prefix)]

    def _cached_models(self) -> list[str]:
        now = time.monotonic()
        if now - self._models_cached_at < 30.0 and self._models_cache:
            return self._models_cache
        try:
            result = subprocess.run(
                ["ollama", "list"],
                capture_output=True, text=True, timeout=2.0,
            )
        except (subprocess.TimeoutExpired, FileNotFoundError) as exc:
            logger.warning("ollama list falhou: %s", exc)
            return self._models_cache or []
        models = []
        for line in result.stdout.splitlines()[1:]:
            parts = line.split()
            if parts:
                models.append(parts[0])
        self._models_cache = models
        self._models_cached_at = now
        return models
```

**Mudanças:**
- Adicionado dispatch `_arg_providers`.
- Provedores: modelos, temas, sessões (com subcomando load), tags de memória.
- Cache de modelos com TTL 30s para evitar spawn de subprocess em cada Tab.
- Timeout de 2s no subprocess — fallback gracioso para cache antigo ou lista vazia.
- Uso de `Pathlib` para varrer sessões (sem shell-out).

---

## Diff esperado

```
~ 1 arquivo modificado
+ 0 arquivos criados
- 0 arquivos removidos
+ ~90 linhas líquidas
```

---

## Comandos de verificação

```bash
# PASSO 1 — snapshot ANTES
bash scripts/sprint_invariants.sh > /tmp/inv_before.txt 2>&1

# PASSO 2 — implementar

# PASSO 3 — smoke
./run.sh --smoke         # esperado: boot ok

# PASSO 4 — testes manuais (capturar no proof-of-work)
./run.sh
# /model <TAB>        -> lista de modelos reais (qwen3:4b, etc.)
# /theme eri<TAB>     -> sugere tema com prefixo eri
# /session load 2026<TAB>  -> sessões com prefixo 2026
# /recall <TAB>       -> tags de memória
# Ctrl+D

# PASSO 5 — gauntlet
./run.sh --gauntlet --only tui/completer

# PASSO 6 — snapshot DEPOIS
bash scripts/sprint_invariants.sh > /tmp/inv_after.txt 2>&1
diff /tmp/inv_before.txt /tmp/inv_after.txt
```

---

## Critério binário de aceite

- [ ] `/model ` + Tab: lista de modelos reais aparece
- [ ] `/theme <prefixo>` + Tab: sugere temas com prefixo
- [ ] `/session load <prefixo>` + Tab: sugere sessões com prefixo
- [ ] `/recall <prefixo>` + Tab: sugere tags com prefixo
- [ ] Autocomplete de nome de comando segue funcionando (`/mod` → `/model`)
- [ ] Tab responde em < 200ms (cache warm) e < 2s (cache frio)
- [ ] Gauntlet `--only tui/completer` 100%
- [ ] FAIL_AFTER <= FAIL_BEFORE no invariants
- [ ] `./run.sh --smoke` continua PASS
- [ ] Nenhuma violação de `forbidden[]`
- [ ] Commit `feat: autocomplete de argumentos para /model, /theme, /session, /recall`
- [ ] Sprint movida para concluidos/

---

## Guardrails anti-engodo

- Retornar lista hardcoded de modelos ("qwen3:4b", "llama3") em vez de puxar do `ollama list`: violação.
- Usar `subprocess.run` com `timeout=None`: violação — bloqueia o prompt indefinidamente.
- Varrer `logs/sessions/` com `os.listdir` e regex manual quando Path.glob já faz: violação de estilo.
- Cache sem TTL — modelo novo instalado via `ollama pull` nunca aparece: violação.
- `except Exception: pass` em volta do subprocess: violação — logger.warning + fallback.
- Quebrar o autocomplete de nome do comando existente (o que UX-BUG-01 consertou): violação gravíssima — regressão direta.

---

## Gambiarras específicas desta sprint

1. **Lista fixa de modelos.** `return ["qwen3:4b", "llama3:8b"]` sem puxar do `ollama list`. Proibido — fonte canônica é o runtime do Ollama.
2. **Subprocess síncrono sem timeout.** `subprocess.run(["ollama", "list"])` sem `timeout=N`. Proibido — bloqueia prompt.
3. **Shell-out via `ls`.** `subprocess.run(["ls", "logs/sessions"])` em vez de `Path.glob("*.json")`. Proibido — GUIDE.md §Código.
4. **Cache infinito.** `self._models_cache = models` sem timestamp. Proibido — modelos novos nunca aparecem.
5. **Silent except.** `try: subprocess.run(...) except: return []`. Proibido — precisa `logger.warning` descrevendo o fallback.
6. **Sobrescrever autocomplete de nome.** Mudança no loop principal de `get_completions` que regride o fix de UX-BUG-01. Proibido — testar o caso `/mod` + Tab depois da mudança.
7. **Provedor que retorna tudo ignorando prefixo.** `_list_themes` retorna todos os temas mesmo quando prefix é `eri`. Proibido — filtro por prefixo sempre aplicado.
8. **Listagem bloqueante de sessões enormes.** Se há 10000 arquivos em `logs/sessions/`, varredura completa pode demorar. Proibido deixar sem limite — cortar em 50 resultados.
9. **Dependência direta do ThemeService/MemoryService sem injeção.** Import global no topo em vez de receber via construtor. Proibido — quebra testabilidade e viola o padrão já usado no arquivo.
10. **Path absoluto `/home/andrefarias/...` em test manual.** Proibido — Pathlib relativo ao cwd ou via service.

Ver também `dev-journey/08-templates/GAMBIARRAS_POR_SPRINT.md` seção COMPLETER-ARGS-01.

---

## Proof-of-work obrigatório

Formato padrão (ver SPRINT_TEMPLATE_V2.md seção "Proof-of-work"). Incluir obrigatoriamente:

- `cat /tmp/inv_before.txt | tail -10`, `cat /tmp/inv_after.txt | tail -10`, diff.
- Captura literal do REPL para os 4 cenários (model, theme, session, recall).
- Medição de latência do Tab (usar `time` no wrapper manual ou logs de `logger.debug`).
- `./run.sh --gauntlet --only tui/completer` com 100%.
- `git show --stat HEAD`.

---

## Validação humana (checklist do usuário)

```bash
cd /home/andrefarias/Desenvolvimento/Nyx-Code
./run.sh

# Teste 1: modelos
# > /model <TAB>
# esperado: lista qwen3:4b e outros modelos instalados

# Teste 2: temas
# > /theme er<TAB>
# esperado: sugere 'eris' ou tema com prefixo 'er'

# Teste 3: sessões
# > /session load 2026<TAB>
# esperado: lista ids de sessão começando com 2026

# Teste 4: tags memória
# > /recall <TAB>
# esperado: lista tags registradas

# Teste 5 (regressão UX-BUG-01): autocomplete de comando
# > /mod<TAB>
# esperado: completa para /model

# Ctrl+D
```

---

## Riscos

| Risco | Mitigação |
|-------|-----------|
| Ollama offline ou não instalado → `ollama list` falha | Timeout de 2s, fallback para cache antigo ou lista vazia com logger.warning |
| `logs/sessions/` inexistente em fresh install | `Path.exists()` check antes do glob; retorna lista vazia |
| Cache obsoleto após `ollama pull` | TTL de 30s expira cache; usuário com modelo novo espera no máximo 30s |
| ThemeService ou MemoryService não expõe método `list_*` | Verificar antes de implementar; se faltar, adicionar método na mesma sprint (não soltar sprint extra para 1 função) |
| Subprocess spawn repetido em cada Tab trava TUI | Cache com TTL mitiga; benchmark de latência no proof-of-work prova |
| Regressão no autocomplete de nomes de comando | Teste manual `/mod<TAB>` obrigatório no checklist |
| 10000 sessões em `logs/sessions/` lentifica glob | Limitar resultados em 50 e ordenar por mtime desc (sessões recentes primeiro) |

---

*"A facilidade com que uma ferramenta se usa determina a frequência com que ela é útil." -- Edsger Dijkstra (adaptado)
