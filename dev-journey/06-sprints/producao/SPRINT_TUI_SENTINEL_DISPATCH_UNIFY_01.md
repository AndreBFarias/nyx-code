# SPRINT TUI-SENTINEL-DISPATCH-UNIFY-01 — sentinels de slash-command param de vazar crus na TUI

## 0. SPEC (machine-readable)

```yaml
sprint:
  id: TUI-SENTINEL-DISPATCH-UNIFY-01
  title: "TUI Textual trata TODOS os sentinels de slash-command (hoje ~10+ vazam crus na tela)"
  onda: 44
  bloco: "44 -- auditoria das ondas 36-43 (2026-06-03)"
  prioridade: ALTA
  tipo: Bugfix / TUI
  dependencias: []
  desbloqueia: []

  touches:
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/agent/tui/app.py
      reason: "_dispatch_slash (linha 425-561) trata explicitamente so 9 sentinels (__quit__, __error__, __sandbox_*__, __cd__, __aesthetic_select__, __theme_select__, __schema_select__). Os demais (~35) caem no fallback `chat.mount(ChatMessage('tool', str(result)))` da linha 559-561 e aparecem crus na tela."
      linhas_alvo: "425-561 (estrutura de dispatch); 559-561 (fallback que vaza)"

  creates:
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/agent/tui/sentinel_dispatch.py
      reason: "Despachador de sentinel COMPARTILHADO entre os 3 hosts (cli.py REPL, app.py TUI, cli_headless). Fonte unica do mapeamento sentinel -> render, eliminando a divergencia N-para-N que a migracao Textual (ONDA-32) introduziu (cada host portou um subconjunto). OPCIONAL: se o refactor compartilhado for grande demais, fallback minimo e estender o app.py para cobrir todos os sentinels conhecidos com um registry local (ver Solucao alternativa)."
  removes: []

  n_to_n_pairs:
    - descricao: "O conjunto de sentinels tratados existe em 3 hosts (cli_headless.py, app.py, cli.py REPL legado) e diverge entre eles. A fonte dos sentinels emitidos e o _dispatcher dos commands."  # noqa-acento
      paths:
        - /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/cli_headless.py
        - /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/agent/tui/app.py
        - /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/cli_handlers.py

  forbidden:
    - "Adicionar emoji ou menção a IA externa"
    - "print() fora de cli*.py/output.py (app.py NÃO e render layer; usar ChatMessage)"
    - "Resolver caso-a-caso so os sentinels que o dono esbarrou (foi o que 343/348/349 fizeram; o problema e sistêmico)"
    - "Quebrar os 9 sentinels que JÁ funcionam (error/sandbox/cd/quit/selects)"

  tests:
    - cmd: "bash scripts/sprint_invariants.sh"
      timeout: 180
      esperado: "14/14 PASS"
    - cmd: "probe determinístico: para cada comando que emite sentinel, app._dispatch_slash NÃO deve montar ChatMessage cujo texto comece com '__'"
      timeout: 60
      esperado: "zero sentinels crus montados; cada um vira render legível"
    - cmd: "./run.sh --gauntlet --only rapido"
      timeout: 300
      esperado: "APROVADO (19/19)"

  acceptance_criteria:
    - "Nenhum comando slash registrado faz a TUI montar um ChatMessage cujo conteúdo comeca com '__<nome>__' cru"
    - "/usage, /status, /trace, /context, /files, /export, /rewind, /schema, /aesthetic, /output-style renderizam conteúdo legível na TUI (não o marcador)"
    - "Os 9 sentinels ja tratados continuam funcionando (regressão zero)"
    - "Invariantes 14/14, gauntlet rápido APROVADO, acento rc=0"
```

---

**Status:** PENDENTE
**Data criação:** 2026-06-03
**Origem:** auditoria das ondas 36-43 (achado A1, severidade ALTA). Prova em runtime sem subir a TUI.
**Modelo obrigatório:** claude-opus (sem subagentes)

---

## Contexto do projeto (snapshot — não referência)

> - ADR-026 Agência: "se algo aconteceu, foi nomeado; se não foi nomeado, não aconteceu". Nada de mágica indecifrável. Sentinel cru na tela é o oposto de affordance visível.
> - ADR-024 Render Layer: `app.py` NÃO é render layer; renderiza via `ChatMessage`, não `print()`.
> - ADR-004 Zero Emojis / ADR-005 Anonimato / ADR-006 PT-BR.
> - Estado: TUI Textual é o modo padrão desde a ONDA-32. O protocolo de slash-command é por **sentinel**: `handle_command()` devolve uma string `__nome__[payload]` e o HOST (cli.py REPL, app.py TUI, cli_headless) a interpreta e renderiza.

---

## Problema

A TUI Textual (`app.py:_dispatch_slash`, modo padrão) trata explicitamente apenas 9 sentinels. Os demais caem no fallback `chat.mount(ChatMessage("tool", str(result)))` (`app.py:559-561`) e **o marcador aparece cru na tela**.

Prova em runtime (via `handle_command(cmd, ".")`, sem subir a TUI):

```
/usage         -> '__usage__'              [VAZA]
/status        -> '__status__'             [VAZA]
/trace         -> '__trace__'              [VAZA]
/context       -> '__context__'            [VAZA]
/files         -> '__files__'              [VAZA]
/export        -> '__export__md'           [VAZA]
/rewind        -> '__rewind__1'            [VAZA]
/schema        -> '__schema_list__'        [VAZA]
/aesthetic     -> '__aesthetic_list__'     [VAZA]
/output-style  -> '__output_style_list__'  [VAZA]
```

Provável também: `/stats`, `/plugin`, `/mcp list`, `/debug`, `/replay <arg>`, `/copy`, `/edit`, `/btw`, `/session*`. As sprints 343 (`__error__`), 348 (`__cd__`) e 349 (`__sandbox_*__`) corrigiram apenas os 3 casos que o dono esbarrou no E2E — não o padrão sistêmico.

---

## Causa-raiz

O protocolo de sentinel exige que **cada host** trate **cada sentinel**. A migração para Textual (ONDA-32) portou só um subconjunto para `app.py`. O fallback genérico (`ChatMessage("tool", str(result))`) foi pensado para retornos de **texto comum** (ex.: `/help`, `/model`), mas captura também os sentinels não tratados e os exibe crus. Não há fonte única do mapeamento sentinel → render; os 3 hosts divergem (`cli_headless.py` trata um conjunto, `app.py` outro, `cli.py` REPL legado outro).

---

## Solução proposta

**Preferida:** extrair um **despachador de sentinel compartilhado** (`nyx/agent/sentinel_dispatch.py`) que mapeia cada sentinel conhecido para uma ação de render abstrata (retorna texto/título/efeito), consumido pelos 3 hosts. Elimina a divergência N-para-N de uma vez e impede regressão futura (sentinel novo entra num só lugar).

**Alternativa mínima (se o refactor compartilhado for grande):** estender `app.py:_dispatch_slash` com um registry local cobrindo TODOS os sentinels emitidos, e trocar o fallback final por: se `str(result).startswith("__")` e o sentinel não foi tratado → montar `ChatMessage("system", "[comando não suportado nesta interface: <nome>]")` em vez do marcador cru (fail-safe que nunca vaza). Os comandos que retornam texto comum continuam no caminho de `ChatMessage("tool", ...)`.

Inventário dos sentinels a cobrir (de `cli_headless.py`/`cli_handlers.py`): `__usage__ __status__ __stats__ __trace__ __context__ __files__ __export__ __rewind__ __replay__ __model__ __clear__ __copy__ __edit_last__ __debug_session__ __btw__ __cancel_inflight__ __progress_tail__ __config_setup__ __mcp_list/reload/test__ __plugin_install/list/reload/uninstall__ __output_style_get/list/set__ __schema_get/list/set__ __aesthetic_get/list/set__ __session_index/load/load_id/save__`.

---

## Proof-of-work esperado (runtime real — BRIEF §[CORE] Contratos de runtime)

```bash
bash scripts/sprint_invariants.sh                       # 14/14 PASS
./run.sh --gauntlet --only rapido                       # APROVADO (19/19)
python3 ~/.config/zsh/scripts/validar-acentuacao.py --paths nyx/agent/tui/app.py nyx/agent/sentinel_dispatch.py
# probe: nenhum ChatMessage montado com texto iniciando em '__'
```

Validação visual (skill validação-visual, pois toca a TUI): capturar a TUI rodando `/usage`, `/status`, `/trace` e confirmar conteúdo legível (não o marcador) — `import`/scrot ou `--web` via playwright.

---

## Critério binário de aceite

- [ ] `/usage /status /trace /context /files /export /rewind /schema /aesthetic /output-style` não exibem marcador cru na TUI
- [ ] Os 9 sentinels já tratados seguem funcionando
- [ ] Invariantes 14/14, gauntlet rápido APROVADO, ruff limpo, acento rc=0
- [ ] Evidência visual anexada
- [ ] Spec movida `producao/` → `concluidos/`; MASTER marca CONCLUIDA

---

## Riscos

| Risco | Mitigação |
|-------|-----------|
| Refactor compartilhado regride os 9 que já funcionam | Cobrir os 9 com o probe determinístico antes/depois; preservar a lógica existente (cd/sandbox têm efeito de estado, não só render) |
| Sentinel com efeito colateral (cd troca root, cancel mata task) tratado como render puro | Mapear no despachador a categoria (render puro vs efeito de estado); efeitos continuam no app.py |

---

*"O que não foi nomeado, não aconteceu — e o que vaza cru foi nomeado errado." -- paráfrase do ADR-026*
