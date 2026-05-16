# SPRINT UX-BUG-02B — Estado cold/warming/warm do modelo no toolbar

## 0. SPEC (machine-readable)

```yaml
sprint:
  id: UX-BUG-02B
  title: "Indicador visual cold/warming/warm do qwen3 no bottom toolbar"
  onda: 22
  bloco: 5
  prioridade: ALTA
  tipo: Feature
  dependencias: [UX-BUG-02A, OBSERVABILITY-01]
  desbloqueia: [UX-BUG-02C]

  touches:
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/agent/loop/_core.py
      reason: "AgentLoop mantém _model_state e emite transições cold→warming→warm via on_model_state callback"
      linhas_alvo: "construtor + método run()"
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/cli.py
      reason: "Wire on_model_state no app_state e consumir no _bottom_toolbar respeitando schema de secções de UX-LAYOUT-01B"
      linhas_alvo: "run_repl() + _bottom_toolbar()"

  creates: []
  removes: []

  n_to_n_pairs:
    - descricao: "Estados válidos cold/warming/warm aparecem em _core.py (emissor) e cli.py (consumidor + toolbar). Mudar um exige mudar o outro."
      paths:
        - /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/agent/loop/_core.py
        - /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/cli.py

  forbidden:
    - "Estado fixo 'warm' sem respeitar transição real"
    - "Duplicar lógica de observabilidade se OBSERVABILITY-01 já provê infra parcial — reusar, não reimplementar"
    - "Emoji como glifo (usar só caracteres Unicode genéricos: ○ ◐ ●)"
    - "Menção a IA em strings, comentários ou commits"
    - "print() em nyx/agent/loop/_core.py (ADR-024: print só em nyx/cli.py REPL e nyx/agent/output.py)"
    - "Callback ser declarado mas nunca chamado (stub)"
    - "Path absoluto hardcoded"

  tests:
    - cmd: "grep -c 'on_model_state\\|_model_state' nyx/cli.py nyx/agent/loop/_core.py"
      deve_passar: ">= 4 ocorrências somadas"
    - cmd: "./run.sh --gauntlet --only tui"
      timeout: 300
      deve_passar: true
    - cmd: "./run.sh --gauntlet --only rapido"
      timeout: 300
      deve_passar: true

  acceptance_criteria:
    - "AgentLoop._model_state inicia em 'cold', vai para 'warming' ao disparar request, 'warm' ao chegar resposta"
    - "Em caso de exceção no request, estado volta para 'cold' (não fica travado em 'warming')"
    - "Callback on_model_state: Callable[[str], None] | None no construtor de AgentLoop"
    - "cli.py define on_model_state que atualiza app_state['model_state']"
    - "_bottom_toolbar lê app_state['model_state'] e renderiza glifo + texto"
    - "Toolbar usa schema de secções definido em UX-LAYOUT-01B (sem reinventar layout)"
    - "Zero emoji (○ ◐ ● são permitidos — são círculos Unicode, não emoji)"
    - "Gauntlet tui e rapido passam 100%"
    - "Acentuação PT-BR correta"
```

---

**Status:** CONCLUIDA
**Data criação:** 2026-04-19
**Data conclusão:** 2026-05-16
**Hash:** (a preencher pós-commit)
**Origem:** divisão de UX-BUG-02. Esta sprint cobre apenas o indicador cold/warm (O-03 absorvido).
**Modelo obrigatório:** claude-opus-4-7 (sem subagentes)
**Validação:** smoke `boot ok`; FAIL_AFTER=0=FAIL_BEFORE; ruff `All checks passed`; 13 invariants OK; validação visual via skill `validacao-visual` capturou 3 PNGs reais (cold/warming/warm) com sha256 registrados — toolbar exibiu `○ cold → ● warm` como esperado; `iter 0→1`, `ctx 1030→1033 tokens`. Gap descoberto na validação: `◐ warming` não aparece na toolbar entre Enter e resposta (prompt-toolkit fora de `prompt_async`); spinner `pensando...` cobre o gap. Achado colateral virou sprint UX-LOOP-VISIBILITY-01.

---

## Contexto do projeto (snapshot — não referência)

> **ADRs relevantes:**
> - ADR-001 Local First.
> - ADR-004 Zero Emojis (○ ◐ ● são círculos, não emoji).
> - ADR-005 Anonimato.
> - ADR-006 PT-BR.
> - ADR-013 Integração Obrigatória.
> - ADR-014 Testes via Gauntlet.
> - ADR-020 Testes via run.sh.
> - ADR-024 Render Layer (print só em cli.py e agent/output.py).
>
> **Estado do sistema:**
> - Onda 22, Bloco 5. AgentLoop foi splittado (commit 43cf4d2) — lógica core vive em `nyx/agent/loop/_core.py`.
> - OBSERVABILITY-01 adiciona infra de callbacks de estado; esta sprint **reusa** esse ponto de integração.
> - UX-LAYOUT-01B define schema de secções do toolbar; consumir schema, não reinventar.

---

## Problema

Primeira request em qwen3 cold demora 5-15s. Usuário acha que o terminal travou. Não há feedback visual do ciclo de vida do modelo.

---

## Solução proposta

AgentLoop mantém campo `_model_state` (`"cold" | "warming" | "warm"`). Ao iniciar um request, emite `"warming"` via callback; ao receber resposta, emite `"warm"`; em exceção, volta para `"cold"`. O CLI assina o callback, guarda o estado em `app_state`, e o `_bottom_toolbar` renderiza glifo correspondente via schema de UX-LAYOUT-01B.

---

## Arquivos alvo (paths absolutos)

### `/home/andrefarias/Desenvolvimento/Nyx-Code/nyx/agent/loop/_core.py`

**Antes (conceitual):**
```python
class AgentLoop:
    def __init__(self, ..., on_model_state=None):
        ...

    async def run(self, user_input: str) -> AgentStatus:
        # ... dispatch direto ao modelo
        result = await ...
        return result
```

**Depois (conceitual):**
```python
class AgentLoop:
    def __init__(
        self,
        ...,
        on_model_state: Callable[[str], None] | None = None,
    ) -> None:
        ...
        self._model_state: str = "cold"
        self._on_model_state = on_model_state

    def _emit_state(self, state: str) -> None:
        self._model_state = state
        if self._on_model_state is not None:
            try:
                self._on_model_state(state)
            except Exception as exc:
                logger.warning("on_model_state raised: %s", exc)

    async def run(self, user_input: str) -> AgentStatus:
        self._emit_state("warming")
        try:
            result = await ...
            self._emit_state("warm")
            return result
        except Exception:
            self._emit_state("cold")
            raise
```

**Mudanças:**

- Novo parâmetro `on_model_state` no construtor.
- Novo campo `_model_state` iniciado em `"cold"`.
- Helper privado `_emit_state` com try/except de guarda no callback (observabilidade não pode derrubar loop).
- `run()` emite transições nos três pontos: início, sucesso, exceção.

### `/home/andrefarias/Desenvolvimento/Nyx-Code/nyx/cli.py`

**Antes (conceitual):**
```python
agent = AgentLoop(...)

def _bottom_toolbar():
    parts = [...]
    return parts
```

**Depois (conceitual):**
```python
def on_model_state(state: str) -> None:
    app_state["model_state"] = state

agent = AgentLoop(..., on_model_state=on_model_state)

_STATE_GLYPHS = {"cold": "○", "warming": "◐", "warm": "●"}

def _bottom_toolbar():
    state = app_state.get("model_state", "cold")
    glyph = _STATE_GLYPHS.get(state, "○")
    # Usar secção do schema de UX-LAYOUT-01B
    sections = toolbar_schema.compose(
        ...,
        model=(NYX_MUTED, f" {glyph} {state}"),
    )
    return sections
```

**Mudanças:**

- Função módulo-local `on_model_state` gravando em `app_state["model_state"]`.
- `app_state["model_state"]` inicializado como `"cold"` antes de `AgentLoop(...)`.
- `_bottom_toolbar` lê estado e compõe via schema de secções (UX-LAYOUT-01B) — não hardcodar índice em lista de tuplas.
- Mapa `_STATE_GLYPHS` como constante módulo-local (não inline).

---

## Diff esperado (resumo)

```
+ 0 arquivos criados
~ 2 arquivos modificados
- 0 arquivos removidos
+ ~50 linhas líquidas
```

---

## Comandos de verificação (literais, copy-paste)

```bash
cd /home/andrefarias/Desenvolvimento/Nyx-Code

# 1. Lint
python -m ruff check nyx/

# 2. Contrato N-para-N (emissor + consumidor)
grep -n "_model_state\|on_model_state" nyx/agent/loop/_core.py nyx/cli.py
# esperado: >= 4 ocorrências totais; ambos arquivos mencionam

# 3. Gauntlet TUI
./run.sh --gauntlet --only tui

# 4. Gauntlet rápido (não-regressão)
./run.sh --gauntlet --only rapido

# 5. Validação visual manual
./run.sh
# antes do primeiro envio: toolbar mostra "○ cold"
# durante streaming: "◐ warming"
# após resposta: "● warm"
# Ctrl+D para sair
```

---

## Critério binário de aceite

- [ ] `AgentLoop.__init__` aceita `on_model_state`
- [ ] `AgentLoop._model_state` inicia em `"cold"`
- [ ] Transições cold→warming→warm emitidas em `run()`
- [ ] Exceção no request volta estado para `"cold"` (não trava em `"warming"`)
- [ ] Callback com `try/except` de guarda + `logger.warning` se falhar
- [ ] `cli.py` assina callback e grava em `app_state["model_state"]`
- [ ] `_bottom_toolbar` usa schema de UX-LAYOUT-01B para renderizar secção do modelo
- [ ] Glifos via constante `_STATE_GLYPHS` módulo-local
- [ ] Gauntlet `--only tui` e `--only rapido` passam 100%
- [ ] `ruff` sem reclamações
- [ ] Sem emoji (○ ◐ ● são Unicode genérico), sem menção a IA, acentuação PT-BR
- [ ] Commit: `feat: indicador cold/warming/warm do modelo no toolbar`

---

## Guardrails anti-engodo

**NÃO marque como concluída se:**

- Callback é declarado mas nunca chamado em `run()`.
- Toolbar mostra `"warm"` fixo (constante) sem depender do estado real.
- Estado trava em `"warming"` após erro de rede.
- IA hardcoda índice em lista de tuplas em vez de usar schema do toolbar.
- Código de `render_user_input` foi tocado "de brinde" (escopo fora desta sprint).

---

## Catálogo de gambiarras proibidas

Aplicáveis especialmente:

- #2 **Stub como implementação**: callback que só faz `pass`.
- #4 **Documentação como implementação**: docstring "emite warming" sem emitir.
- #17 **Silent except**: try/except no callback deve ter `logger.warning`, nunca `pass`.
- #19 **Feature flag falsa**: `if ENABLE_MODEL_STATE: ...` nunca True.

Ver lista completa em `SPRINT_TEMPLATE_V2.md`.

---

## Proof-of-work obrigatório

Incluir no relatório final:

- `cat /tmp/inv_before.txt | tail -10` + `cat /tmp/inv_after.txt | tail -10` + diff.
- `FAIL_BEFORE` e `FAIL_AFTER` com `FAIL_AFTER <= FAIL_BEFORE`.
- Output de `./run.sh --gauntlet --only tui` (não-editado).
- Output de `./run.sh --gauntlet --only rapido`.
- Screenshot ou transcrição literal do REPL mostrando três estados no toolbar.
- `git show --stat HEAD`.

---

## Gambiarras específicas desta sprint

1. **Emoji disfarçado**: usar 🟢 em vez de ●. Proibido — qualquer codepoint com categoria Emoji é proibido.
2. **Estado global sem observabilidade**: mexer em `app_state` direto de `_core.py` em vez de via callback. Proibido — quebra camadas.
3. **Reimplementar infra já feita em OBSERVABILITY-01**: criar `_emit_state` do zero se OBSERVABILITY-01 já entregou pattern de callbacks. Consultar o código de OBSERVABILITY-01 antes.
4. **Schema inline**: hardcodar posição da secção no toolbar sem usar API de UX-LAYOUT-01B. Força conflito.
5. **Toolbar com estado via global mutável sem lock**: em REPL síncrono não há race, mas documentar que callback é chamado no thread do loop, não em outro.

---

## Validação humana (checklist do usuário)

```bash
cd /home/andrefarias/Desenvolvimento/Nyx-Code

git log --oneline -1
git show --stat HEAD

./run.sh --gauntlet --only tui
./run.sh --gauntlet --only rapido

./run.sh
# Ver o toolbar inicial com "○ cold"
# Enviar mensagem; durante resposta: "◐ warming"
# Após resposta completa: "● warm"
# /quit

ls dev-journey/06-sprints/concluidos/SPRINT_UX_BUG_02B.md
! ls dev-journey/06-sprints/producao/SPRINT_UX_BUG_02B.md 2>/dev/null
```

---

## Riscos

| Risco | Mitigação |
|-------|-----------|
| OBSERVABILITY-01 ainda não concluída quando UX-BUG-02B iniciar | Respeitar `dependencias: [OBSERVABILITY-01]`; não iniciar antes |
| Schema de UX-LAYOUT-01B não suporta secção de modelo | Estender schema, não hardcodar; abrir sub-sprint se for grande |
| Callback lança exceção e derruba loop | `try/except` com `logger.warning` no emissor |
| Estado fica travado em "warming" em timeout longo | Caminho de exceção deve voltar para "cold"; incluir teste de timeout |

---

*"Tornar o invisível visível é metade da depuração." -- adaptado de Fred Brooks*
