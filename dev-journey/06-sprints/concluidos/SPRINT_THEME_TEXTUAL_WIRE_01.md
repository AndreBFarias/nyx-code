# SPRINT ONDA-38-D — THEME-TEXTUAL-WIRE-01

## 0. SPEC (machine-readable)

```yaml
sprint:
  id: THEME-TEXTUAL-WIRE-01
  title: "Wirear troca de tema/aesthetic/schema em runtime no modo Textual (sair do STUB)"
  onda: 38
  prioridade: MEDIA
  tipo: Feature
  touches:
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/agent/tui/app.py
      reason: "_open_select_modal (L422-440) deixa de ser STUB: popula opções reais e aplica a seleção em runtime"
  acceptance_criteria:
    - "o SelectScreen de tema/aesthetic/schema mostra as opções reais (de list_aesthetics/list_schemas), não opt1/opt2"
    - "escolher uma opção aplica a paleta em runtime sob o caminho Textual default"
    - "ESC/cancelar não altera o tema vigente"
    - "smoke boot ok + invariantes 14/14"
```

---

**Status:** CONCLUIDA_COM_RESSALVA (2026-06-01 — _open_select_modal saiu do STUB: helper estático testável _select_options_for popula opções REAIS (aesthetic: default/arcano/cyberpunk/brutalist/mecha/editorial; schema: editorial/arcano/brutalist/hybrid; env vars NYX_AESTHETIC/NYX_SCHEMA corretas), seleção seta env+clear_cache, ESC não toca env. Proof: harness comprova fim do opt1/opt2; smoke boot ok; invariantes 14/14; acentuação exit 0. RESSALVA/ACHADO: repaint visual em runtime NÃO ocorre — design_tokens.py usa constantes estáticas e nenhum widget Textual lê resolve_palette(); registrado como sprint dedicada THEME-TEXTUAL-RUNTIME-REPAINT-01 (apply+persist). Captura visual de paleta-mudando não aplicável até esse follow-up.)
**Data criação:** 2026-06-01
**Modelo obrigatório:** sem subagentes (Read/Grep/Glob direto)

---

## Contexto

No modo Textual (caminho ÚNICO interativo pós-ONDA-32, `cli.py:517`/`cli.py:536-539`), o handler `_open_select_modal` (`nyx/agent/tui/app.py:422-440`) é um STUB declarado: a docstring (L425) diz "opções vêm de settings/theme_manager; sprint dedicada popula" e as opções são literais `options = [("opt1", "Opção 1"), ("opt2", "Opção 2")]` (L431). Ao escolher, ele só monta um `ChatMessage` com o valor — NÃO aplica a paleta. Esta é a sprint dedicada que liga a seleção ao runtime.

## Escopo (touches autorizados)

- Arquivos a modificar:
  - `/home/andrefarias/Desenvolvimento/Nyx-Code/nyx/agent/tui/app.py` (apenas `_open_select_modal`, L422-440)
- Arquivos a criar: nenhum
- Arquivos NÃO a tocar:
  - `nyx/themes/theme_manager.py` e `nyx/themes/design_tokens_extended.py` — só CONSUMIR suas funções públicas (`list_aesthetics`, `list_schemas`, `clear_cache`), não editar.
  - `nyx/agent/tui/screens/select_screen.py` — já funcional (`SelectScreen(title, options)`), não editar.
  - Os 6 arquivos protegidos do check #14 (app.py não está no conjunto).

## Observação sobre a hipótese original (ajuste do planejador)

Verificado via leitura:

- O STUB está em `app.py:422-440` (a tarefa citou L425-435 — confere, é o corpo do método).
- Os sentinels `__theme_select__`/`__aesthetic_select__`/`__schema_select__` são tratados em `app.py:409-417` (a tarefa citou L410-435 — confere).
- A fonte de opções correta JÁ existe e é pública: `nyx/themes/design_tokens_extended.py` expõe `list_aesthetics() -> [{id,name,tagline}]` (L340), `list_schemas() -> [{id,heading_case,...}]` (L327), `list_entities() -> [{id,name,accent}]` (L348). O STUB usava `opt1/opt2` por preguiça; a infra já está pronta.
- `theme_manager.clear_cache()` (`theme_manager.py:122-125`) limpa o lru de `resolve_palette`/`resolve_active` — necessário após mudar env para a nova paleta valer.
- A seleção é aplicada via env vars: `NYX_AESTHETIC`, `NYX_SCHEMA`, `NYX_ENTITY` (lidas por `theme_manager._env_keys`/`_env_keys_full`, `theme_manager.py:28-42`).

A tarefa cita `NYX_TUI_TEXTUAL=1` como gate, mas pós-ONDA-32 o Textual é o caminho default (sem necessidade do env). O proof deve rodar o app normalmente; se o env ainda for honrado como alias, manter para retrocompat.

## Acceptance criteria

1. Para `__aesthetic_select__`, o `SelectScreen` é populado de `list_aesthetics()` mapeado para `(id, name)`.
2. Para `__schema_select__`, populado de `list_schemas()` mapeado para `(id, id)` (ou `(id, heading_case)` como descrição legível).
3. Para `__theme_select__`, mapear ao conjunto apropriado (aesthetic ou schema conforme a semântica de "tema" no produto — confirmar via `rg` qual sentinel o comando `/theme` ou `/aesthetic` emite; usar aesthetic se "tema" == paleta).
4. Ao escolher uma opção (resultado não-None): setar a env var correspondente, chamar `theme_manager.clear_cache()`, e refrescar a UI (re-render do banner/widgets que consomem cor) — usar `self.refresh(recompose=...)` ou re-mount do banner conforme o que a árvore Textual suportar.
5. ESC/cancelar (resultado None): não mexer em env nem cache; manter o tema vigente.
6. `./run.sh --smoke` imprime `boot ok`, exit 0.
7. `bash scripts/sprint_invariants.sh` PASS 14/14, FAIL 0.

## Invariantes a preservar

- `push_screen_wait` + `run_worker(exclusive=False)` já funcionam (o STUB provou isso); não quebrar o ciclo async.
- Caminho default Textual (`cli.py:517`) intacto — não reintroduzir prompt_toolkit (removido na ONDA-32).
- Glifos de UI dos widgets (que vêm de `design_tokens`) permanecem; troca de paleta só muda COR, não glifo.
- GUIDE.md §2: reusar `list_aesthetics`/`list_schemas`/`clear_cache`; não criar novo registry de temas.

## Plano de implementação

1. Em `_open_select_modal`, antes do `push_screen_wait`, construir `options` por `kind`:
   - `__aesthetic_select__` -> `[(a["id"], a["name"]) for a in list_aesthetics()]`
   - `__schema_select__` -> `[(s["id"], s["id"]) for s in list_schemas()]`
   - `__theme_select__` -> conforme decisão do AC #3.
2. Importar `list_aesthetics`/`list_schemas` de `nyx.themes.design_tokens_extended` e `clear_cache` de `nyx.themes.theme_manager` (imports locais, como o padrão do arquivo).
3. Após `selected = await self.push_screen_wait(...)`: se `selected` não-None, `os.environ[env_key_de(kind)] = selected`, `clear_cache()`, e disparar refresh da UI. Substituir o `ChatMessage("tool", f"{kind}: {selected}")` por uma confirmação legível (ex.: "Tema aplicado: {name}").
4. Se `selected` é None, montar um `ChatMessage` neutro ("seleção cancelada") sem tocar env.
5. Rodar smoke + invariantes + validação visual.

## Testes

- Adicionar teste em `tests/` (localizar testes da TUI via `rg -l "SelectScreen\|_open_select_modal\|NyxTUI" tests/`): cobrir que `_open_select_modal` popula options de `list_aesthetics()` e que escolher seta a env var + chama `clear_cache`. Usar mock de `push_screen_wait` retornando um id válido e None.
- Baseline: FAIL_BEFORE = 0, esperado FAIL_AFTER = 0.

## Proof-of-work esperado

- Diff final de `app.py` (só `_open_select_modal`).
- Runtime real:
  - Subir o app (Textual default; se honrar o alias, `NYX_TUI_TEXTUAL=1 ./run.sh`), disparar o select de tema em runtime, escolher uma aesthetic não-default e comprovar a aplicação visual.
  - Smoke: `./run.sh --smoke` (`boot ok`, exit 0)
  - Invariantes: `bash scripts/sprint_invariants.sh` (14/14)
- Validação visual: skill `validacao-visual` <!-- noqa-acento --> — capturar dois frames (antes e depois da troca de tema) provando que a paleta mudou no app rodando. PNG + sha256 de cada.
- Cleanup pós-teste: `pkill -f "nyx/proxy.py"`, `pkill -f "ollama serve"`, `nvidia-smi` VRAM livre (BRIEF check #5).
- Acentuação periférica: `python3 /home/andrefarias/.config/zsh/scripts/validar-acentuacao.py --paths nyx/agent/tui/app.py` exit 0.
- Hipótese verificada: `rg -n "_open_select_modal|list_aesthetics|list_schemas|clear_cache|__theme_select__" nyx/agent/tui/app.py nyx/themes/design_tokens_extended.py nyx/themes/theme_manager.py`.

## Riscos e não-objetivos

- Não-objetivo: persistir a escolha em `~/.nyx/config.toml` (troca é só de runtime nesta sprint; persistência fica para sprint futura se pedida — anti-débito).
- Risco: refresh da paleta no Textual pode exigir re-mount de widgets (o banner é renderizado uma vez). Se o refresh não propagar a cor, registrar achado e propor a estratégia mínima (re-mount do `BannerWidget`) — não escalar para refactor amplo.
- Risco: confundir a semântica de "tema" vs "aesthetic" vs "schema". Mitigação: AC #3 manda confirmar via `rg` qual sentinel cada comando emite antes de mapear.

## Referências

- BRIEF: `/home/andrefarias/Desenvolvimento/Nyx-Code/VALIDATOR_BRIEF.md` (seção "Capacidades visuais aplicáveis")
- Precedente: VISUAL-LAYOUT-CLI-CONSUME-01 (theme_manager origem); TUI-REDESIGN-25-16 (schemas)

---

*"O STUB provou o ciclo; agora o ciclo carrega cor de verdade."*
