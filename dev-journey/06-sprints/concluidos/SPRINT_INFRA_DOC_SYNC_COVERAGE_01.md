# SPRINT TEMPLATE V2 — INFRA-DOC-SYNC-COVERAGE-01

## 0. SPEC (machine-readable)

```yaml
sprint:
  id: INFRA-DOC-SYNC-COVERAGE-01
  title: "Cobertura de numeros narrativos no update_docs.py (iteracoes, fases, ADRs) + meta-check anti-debito"
  onda: 38
  prioridade: ALTA
  tipo: Feature
  dependencias: [DOC-COUNT-INTERNAL-SYNC-01]
  desbloqueia: []

  touches:
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/scripts/update_docs.py
      reason: "Adiciona 3 leitores (_read_max_iterations, _count_gauntlet_phases, ja existe _count_adrs), 3+ regex no update_readme e 1 meta-check de cobertura."
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/README.md
      reason: "Numeros narrativos sincronizados pelo próprio script rodando (NUNCA edicao manual de numeros). README:88 30->50 iteracoes; README:308 ## ADRs (34) ganha regex; README:351 225 testes em 53 fases sincroniza."
      linhas_alvo: "88, 308, 351"

  creates: []
  removes: []

  n_to_n_pairs:
    - descricao: "MAX_ITERATIONS vive em defaults.py (fonte) e e narrado em README.md (consumidor) -- regex liga os dois"  # noqa-acento
      paths:
        - /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/config/defaults.py
        - /home/andrefarias/Desenvolvimento/Nyx-Code/README.md
    - descricao: "contagem de fases vive em PHASE_TIMEOUTS/PHASE_GROUPS no gauntlet (fonte) e e narrada em README.md (consumidor)"  # noqa-acento
      paths:
        - /home/andrefarias/Desenvolvimento/Nyx-Code/scripts/gauntlet/nyx_gauntlet.py
        - /home/andrefarias/Desenvolvimento/Nyx-Code/README.md

  forbidden:
    - "Adicionar emoji"
    - "Mencao a Claude/GPT/Anthropic/Gemini/Copilot em .py"  # noqa-anonimato
    - "Editar manualmente os numeros do README.md (so o próprio update_docs.py rodando pode reescrever; o executor edita o SCRIPT, não o README)"
    - "Tocar arquivos com dano de glifo U+23FA: dev-journey/07-reports/* e novo_layout/*.jsx (fora do escopo; usuário trata separado)"
    - "Mudar a fonte de verdade dos campos ja corretos: tools (runtime ToolRegistry), commands (runtime list_commands) -- decisao BANNER-TOOLS-COUNT-01"
    - "Tocar qualquer arquivo do check #14 (cli.py, design_tokens.py, output.py, banner.py, design_tokens_extended.py, sprint_invariants.sh)"
    - "Inventar um numero de fases que não seja derivavel de PHASE_TIMEOUTS ou PHASE_GROUPS['completo'] do gauntlet"

  tests:
    - cmd: "./venv/bin/python scripts/update_docs.py --check"
      timeout: 120
      deve_passar: true   # exit 0 apos sync aplicado
    - cmd: "bash scripts/sprint_invariants.sh"
      timeout: 120
      deve_passar: true   # PASS 14/14 FAIL 0

  acceptance_criteria:
    - "update_docs.py tem função _read_max_iterations() que le MAX_ITERATIONS de nyx/config/defaults.py via regex (espelho de _default_model)"
    - "update_docs.py tem função _count_gauntlet_phases() que conta fases derivaveis do gauntlet de forma estavel (PHASE_TIMEOUTS ou PHASE_GROUPS['completo'])"
    - "update_readme() ganha regex que reescreve 'ate N iteracoes' com o valor real (50)"
    - "update_readme() ganha regex que reescreve '## ADRs (N)' com o valor real (34)"
    - "update_readme() ganha regex que reescreve o numero de testes/fases da linha narrativa 351 ('N testes em M fases')"
    - "README.md:88 passa de 'ate 30 iteracoes' para 'ate 50 iteracoes' apos rodar o script"
    - "Existe META-CHECK que lista numeros auto-deriveis conhecidos e ALERTA/FALHA se algum não tiver regex correspondente nos docs"
    - "Apos o sync: ./venv/bin/python scripts/update_docs.py --check retorna exit 0"
    - "Regressao: injetar 'ate 99 iteracoes' no README -> --check exit 1 -> sync corrige -> --check exit 0"
    - "Acentuacao PT-BR correta em tudo novo (validar-acentuacao.py exit 0)"
    - "ruff check scripts/update_docs.py sem erros"
    - "smoke boot ./run.sh --smoke imprime 'boot ok' exit 0"
    - "Invariantes 14/14, FAIL 0; FAIL_AFTER <= FAIL_BEFORE"
```

---

**Status:** PENDENTE
**Data criação:** 2026-06-01
**Modelo obrigatório:** claude-opus-4-7 (sem subagentes)

---

# Sprint INFRA-DOC-SYNC-COVERAGE-01 — Cobertura de numeros narrativos no update_docs.py

**Status:** PENDENTE
**Data criação:** 2026-06-01
**Modelo obrigatório:** claude-opus-4-7 (sem subagentes)

---

## Contexto do projeto (snapshot — não referência)

> **ADRs relevantes (colar o essencial inline, não apontar arquivo):**
>
> - ADR-001 Local First: tudo offline.
> - ADR-004 Zero Emojis: em tudo.
> - ADR-005 Anonimato: sem menção a IA em código/commits.
> - ADR-006 PT-BR: acentuação obrigatória.
> - ADR-013 Integração Obrigatória: nada solto, tudo no registry/pipeline.
>
> **Estado do sistema (na data da sprint):**
> - Python 3.10+, modelo `qwen2.5-coder:3b` no Ollama porta 11435, proxy 11436.
> - 35 tools, 67 commands, 15 services. Versão `1.3.0` (`nyx/__version__.py`).
> - `scripts/update_docs.py` tem 630 linhas, sincroniza 7 documentos por regex.
> - Sprint anterior da família: `DOC-COUNT-INTERNAL-SYNC-01` CONCLUIDA (ONDA-31) — adicionou 2 regex ao `update_readme` para headers internos.
> - Precedente de meta-check: `INVARIANT-14-COVERAGE` (254, ONDA-31).

---

## Problema

`scripts/update_docs.py` sincroniza docs <-> código por regex de padrões pré-cadastrados (7 documentos, modo `--check`, enforced no pre-commit ativo `scripts/hooks/pre-commit:265` e em `run.sh:828/843`). Mas só cobre números que têm regex. Três números narrativos do `README.md` divergem ou vão divergir por falta de cobertura. **Sintomas observáveis confirmados via grep no código real:**

1. **DIVERGÊNCIA REAL hoje.** `README.md:88`:
   ```
   - AgentLoop: plan-execute-observe (até 30 iterações)
   ```
   versus `nyx/config/defaults.py:72`:
   ```python
   MAX_ITERATIONS: int = 50
   ```
   O README narra 30, o código usa 50. Documentação mente.

2. **DIVERGÊNCIA REAL hoje.** `README.md:351`:
   ```
   - **Gauntlet**: 225 testes em 53 fases; `--only rapido` 18/18 ...
   ```
   versus estado real do gauntlet: **320 testes** catalogados (`grep -c "self\._add(" scripts/gauntlet/nyx_gauntlet.py` = 320). Repare que `README.md:426` JÁ diz `320 testes catalogados` — porque o regex existente em `update_readme` (`# \d+ testes(?: em \d+ fases)?; --only fase\|feature_id`) só casa a linha 426 (tem `--only fase|feature_id`), NÃO casa a linha 351 (que termina em `; --only rapido`). A linha 351 ficou órfã de cobertura.

3. **Correto hoje, mas sem regex (bomba-relógio).** `README.md:308`:
   ```
   ## ADRs (34)
   ```
   `_count_adrs()` JÁ existe e conta `ADR_*.md` em `dev-journey/03-decisions` = 34 (correto). Mas nenhum regex liga essa contagem ao README. No 35º ADR, diverge silenciosamente.

**Lacuna estrutural (causa-raiz):** não existe um mecanismo que perceba quando um número auto-derivável passa a existir num doc sem regex correspondente. Cada número solto novo é uma divergência futura garantida.

---

## Solução proposta

Adicionar ao `update_docs.py`: (a) `_read_max_iterations()` espelhando `_default_model()`; (b) `_count_gauntlet_phases()` derivando fases de forma ESTÁVEL do gauntlet; (c) 3 regex novos em `update_readme()` (iterações, ADRs, testes/fases da linha 351); (d) um META-CHECK anti-débito que falha se um número auto-derivável conhecido não tiver regex no doc. Rodar o script reescreve o README; o executor edita o SCRIPT, nunca os números do README à mão.

---

## INVESTIGAÇÃO PRÉVIA — fases do gauntlet (decisão de design obrigatória)

O CONTEXTO pediu para investigar como o gauntlet agrupa fases ANTES de fixar a contagem. Investigação feita; resultados empíricos (não suposição):

- **`PHASE_TIMEOUTS`** (`nyx_gauntlet.py:183`) = **60 chaves**. Cada chave é uma fase real executável com timeout próprio.
- **Métodos `_phase_*`** = **60** (`grep -c "async def _phase_"`). Cruzamento perfeito com `PHASE_TIMEOUTS`: `set(metodos) - set(PHASE_TIMEOUTS) == set()` E `set(PHASE_TIMEOUTS) - set(metodos) == set()`. Zero falta, zero sobra. **Esta é a métrica estável das fases reais.**
- **`PHASE_GROUPS`** (`nyx_gauntlet.py:51`) = **75 chaves**, mas mistura fases singleton (`"infra": ["infra"]`) com agregadores/aliases (`"p2": [...]`, `"rapido": [...]`, `"completo": [...]`, `"port": [...]`). Contar `PHASE_GROUPS` daria 75 (inflado e frágil). Singletons (`k -> [k]`) dentro de `PHASE_GROUPS` = 60 (coincide com `PHASE_TIMEOUTS`).
- **`len(PHASE_GROUPS["completo"])` = 53.** Esta é a origem exata do "53 fases" do README: a lista canônica de fases que o run `completo` executa (subset que exclui fases marginais como `vision`, `sessao`, `install`, `loop`, `mcp`, `plugins`, `hooks_dynamic`, `contexto`... presentes em `PHASE_TIMEOUTS` mas fora do `completo`).

**Conclusão: "fases" É derivável de forma estável.** Há duas definições legítimas e o executor deve escolher uma e documentar no docstring:

- **OPÇÃO A (recomendada): `len(PHASE_TIMEOUTS)` = 60.** Robustez máxima: 1:1 com métodos `_phase_*`, definição única de "fase executável". Muda o README de `53 fases` para `60 fases`. Semântica honesta: o universo de 320 testes cobre as 60 fases.
- **OPÇÃO B: `len(PHASE_GROUPS["completo"])` = 53.** Preserva o número narrativo histórico (53). Risco: alguém pode adicionar uma fase em `PHASE_TIMEOUTS` e esquecer de incluí-la em `completo`, mantendo 53 enquanto o gauntlet real cresce — a mesma classe de divergência que esta sprint combate.

**Recomendação do planejador: OPÇÃO A** (`PHASE_TIMEOUTS`), por coerência com o objetivo anti-débito da própria sprint. A linha 351 do README passa a `320 testes em 60 fases`. Se o executor preferir preservar 53 por razão narrativa, OPÇÃO B é aceitável desde que o docstring de `_count_gauntlet_phases()` registre explicitamente a escolha e o motivo. **Qualquer outro número é violação de `forbidden`.**

---

## Arquivos alvo (paths absolutos)

> **Nota de acentuação (load-bearing).** O `update_docs.py` real usa acentos PT-BR em docstrings, comentários e `logger.info` (ex.: `atualização`, `versão`, `únicos`). Ao materializar as funções novas, manter acentuação PT-BR no texto dos docstrings/comentários (identificadores Python ficam sem acento por PEP-8). Os snippets abaixo aparecem com acentos no texto; copiar preservando-os para não reprovar no `validar-acentuacao.py --paths scripts/update_docs.py` do proof-of-work.

### `/home/andrefarias/Desenvolvimento/Nyx-Code/scripts/update_docs.py`

#### Adição 1 — `_read_max_iterations()` (espelho literal de `_default_model`, linhas 116-123)

**Padrão de referência existente (NÃO modificar, só espelhar o idioma):**
```python
def _default_model() -> str:
    """Lê DEFAULT_MODEL de nyx/config/defaults.py."""
    defaults = PROJECT_ROOT / "nyx" / "config" / "defaults.py"
    if not defaults.exists():
        return "qwen2.5-coder:3b"
    src = defaults.read_text(encoding="utf-8")
    m = re.search(r'^DEFAULT_MODEL[^=]*=\s*"([^"]+)"', src, re.MULTILINE)
    return m.group(1) if m else "qwen2.5-coder:3b"
```

**Adicionar (sugestão — ancorar logo após `_default_model`):**
```python
def _read_max_iterations() -> int:
    """Lê MAX_ITERATIONS de nyx/config/defaults.py."""
    defaults = PROJECT_ROOT / "nyx" / "config" / "defaults.py"
    if not defaults.exists():
        return 50
    src = defaults.read_text(encoding="utf-8")
    m = re.search(r"^MAX_ITERATIONS[^=]*=\s*(\d+)", src, re.MULTILINE)
    return int(m.group(1)) if m else 50
```
Observação: a linha real é `MAX_ITERATIONS: int = 50` — o regex `^MAX_ITERATIONS[^=]*=\s*(\d+)` casa o anotador de tipo `: int ` antes do `=`. Confirmar com `grep -n "MAX_ITERATIONS" nyx/config/defaults.py`.

#### Adição 2 — `_count_gauntlet_phases()` (espelho de `_count_gauntlet_tests`, linhas 67-73)

**Padrão de referência existente:**
```python
def _count_gauntlet_tests() -> int:
    """Conta testes no Gauntlet (self._add calls)."""
    gauntlet = PROJECT_ROOT / "scripts" / "gauntlet" / "nyx_gauntlet.py"
    if not gauntlet.exists():
        return 0
    content = gauntlet.read_text(encoding="utf-8")
    return len(re.findall(r"self\._add\(", content))
```

**Adicionar (sugestão — OPÇÃO A; usar `ast` para robustez ou regex de chaves do bloco `PHASE_TIMEOUTS`):**
```python
def _count_gauntlet_phases() -> int:
    """Conta fases reais executaveis do Gauntlet.

    Fonte: dict PHASE_TIMEOUTS em scripts/gauntlet/nyx_gauntlet.py.
    Cada chave e uma fase com timeout próprio, 1:1 com os metodos
    _phase_* (cruzamento verificado: zero falta, zero sobra).
    Definicao escolhida em INFRA-DOC-SYNC-COVERAGE-01 (Opção A) por
    coerencia com o objetivo anti-debito desta sprint.
    """
    gauntlet = PROJECT_ROOT / "scripts" / "gauntlet" / "nyx_gauntlet.py"
    if not gauntlet.exists():
        return 0
    import ast as _ast

    src = gauntlet.read_text(encoding="utf-8")
    try:
        for node in _ast.walk(_ast.parse(src)):
            if (
                isinstance(node, _ast.AnnAssign)
                and isinstance(node.target, _ast.Name)
                and node.target.id == "PHASE_TIMEOUTS"
            ):
                return len(_ast.literal_eval(node.value))
    except (SyntaxError, ValueError):
        pass
    return 0
```
Observação: `ast.literal_eval` é seguro (não executa código). Alternativa de regex pura (`grep` das linhas `"\w+": \d+,` dentro do bloco) é mais frágil — preferir `ast`. Se OPÇÃO B, ler `PHASE_GROUPS["completo"]` e retornar `len(...)`.

#### Adição 3 — regex em `update_readme()` (lista `replacements`, linhas 252-294)

`update_readme` precisa receber os novos valores. O executor deve:
- Estender a assinatura de `update_readme(...)` para receber `max_iterations: int`, `adrs: int`, `phases: int` (e passar de `main()`, linha 599).
- Adicionar à lista `replacements`:

```python
# README:88 -- iteracoes do AgentLoop (DIVERGENCIA: 30 narrado vs 50 real).
(
    r"plan-execute-observe \(até \d+ iterações\)",
    f"plan-execute-observe (até {max_iterations} iterações)",
),
# README:308 -- header de ADRs (correto hoje=34, sem regex ate agora).
(
    r"## ADRs \(\d+\)",
    f"## ADRs ({adrs})",
),
# README:351 -- linha narrativa do Gauntlet que o regex de 426 NÃO casa
# (termina em '; --only rapido', não em '--only fase|feature_id').
(
    r"\*\*Gauntlet\*\*: \d+ testes em \d+ fases;",
    f"**Gauntlet**: {tests} testes em {phases} fases;",
),
```
Observação de ancoragem: a linha 351 literal é `- **Gauntlet**: 225 testes em 53 fases; \`--only rapido\` ...`. O regex acima ancora em `**Gauntlet**:` e no sufixo `fases;` — não colide com a linha 426 (que tem `# 320 testes catalogados; --only fase|feature_id`). Validar via `grep -n "testes em" README.md` antes e depois.

#### Adição 4 — META-CHECK anti-débito de cobertura

Função nova que materializa o objetivo: impedir que números auto-deriváveis futuros passem batido. Sugestão de forma (o executor pode ajustar a estrutura desde que cumpra o acceptance):

```python
def _coverage_meta_check(values: dict[str, int | str]) -> list[str]:
    """META-CHECK anti-debito: para cada numero auto-derivavel conhecido,
    verifica se existe pelo menos uma ocorrencia do valor ESPERADO nos docs
    sincronizados. Retorna lista de alertas (vazia = cobertura ok).

    Objetivo (INFRA-DOC-SYNC-COVERAGE-01): se um numero derivavel deixa de
    aparecer sincronizado em algum doc, este check alerta -- impede numero
    solto novo de divergir silenciosamente como aconteceu com README:88/351.
    """
    readme = PROJECT_ROOT / "README.md"
    if not readme.exists():
        return []
    txt = readme.read_text(encoding="utf-8")
    alerts: list[str] = []
    checks = {
        "max_iterations": f"até {values['max_iterations']} iterações",
        "adrs": f"## ADRs ({values['adrs']})",
        "gauntlet_phases": f"em {values['gauntlet_phases']} fases",
    }
    for nome, esperado in checks.items():
        if esperado not in txt:
            alerts.append(
                f"COBERTURA: '{nome}' esperado '{esperado}' ausente no README "
                f"(numero auto-derivavel sem regex sincronizando -- adicionar)"
            )
    return alerts
```
Integração em `main()`: após aplicar os updates, chamar `_coverage_meta_check(...)`; se houver alertas, imprimir e — em modo `--check` — contribuir para o exit 1 (igual ao comportamento atual de `changes`). Em modo escrita, os regex já corrigiram, então o meta-check deve passar limpo no segundo passe (idempotência). O executor decide se o meta-check soma a `sys.exit(1)` ou emite warning não-fatal; o acceptance exige no mínimo ALERTA visível. Preferir falha dura em `--check` para fechar o débito de verdade.

#### Adição 5 — fiação em `main()` (linhas 556-624)

- Computar `max_iterations = _read_max_iterations()`, `gauntlet_phases = _count_gauntlet_phases()` (reusar `adrs` já existente, linha 565).
- Adicionar ao bloco de print de estado (linhas 579-593) as novas métricas.
- Passar os novos valores para `update_readme(...)` na chamada da linha 599.
- Chamar `_coverage_meta_check(...)` e integrar ao exit conforme acima.

### `/home/andrefarias/Desenvolvimento/Nyx-Code/README.md`

**NÃO editar à mão.** Os números mudam exclusivamente por rodar `./venv/bin/python scripts/update_docs.py` (modo escrita). Mudanças esperadas após rodar:
- Linha 88: `(até 30 iterações)` -> `(até 50 iterações)`.
- Linha 308: `## ADRs (34)` -> `## ADRs (34)` (sem mudança hoje; regex passa a proteger).
- Linha 351: `225 testes em 53 fases` -> `320 testes em 60 fases` (OPÇÃO A) ou `320 testes em 53 fases` (OPÇÃO B).

---

## Diff esperado (resumo)

```
+ 0 arquivos criados
~ 2 arquivos modificados (scripts/update_docs.py, README.md)
- 0 arquivos removidos
+ ~50-70 linhas líquidas (no update_docs.py)
```

---

## Aritmética (meta numérica de linhas)

O BRIEF §[CORE] Heurísticas de aritmética exige `wc -l` antes/depois quando há meta de linhas. Aqui a "meta" é o delta declarado do `update_docs.py`:

- **Arquivo alvo:** `scripts/update_docs.py`
- **Linhas atuais:** 630 (confirmado `wc -l`).
- **Adições planejadas:**
  - `_read_max_iterations()`: ~8L
  - `_count_gauntlet_phases()` (com `ast`): ~22L
  - 3 regex novos em `update_readme` + 3 params na assinatura: ~12L
  - `_coverage_meta_check()`: ~25L
  - fiação em `main()` (computar valores, prints, passar args, chamar meta-check): ~8L
  - Total bruto estimado: **~75L**
- **Projetado após adição:** 630 + ~75 = **~700-705L** (o `_count_adrs` já existe, então não soma).
- **Faixa esperada declarada pelo CONTEXTO:** +40-70L. A estimativa do planejador (~75L) fica ligeiramente acima por causa do `ast` no `_count_gauntlet_phases` (mais robusto que regex puro, ~+10L). **Tolerância:** se o executor usar regex de chaves em vez de `ast`, cai para ~+60L (dentro da faixa). Aceitar 670-710L final.
- **README.md:** delta de conteúdo ~0 linhas (só valores numéricos in-place mudam; nenhuma linha adicionada/removida).

O executor DEVE rodar `wc -l scripts/update_docs.py` antes e depois e colar ambos no proof-of-work.

---

## Comandos de verificação (literais, copy-paste)

```bash
cd /home/andrefarias/Desenvolvimento/Nyx-Code

# 0. ANTES: divergencia presente
grep -n "até 30 iterações" README.md          # deve EXISTIR antes
grep -n "MAX_ITERATIONS" nyx/config/defaults.py # confirma fonte = 50
wc -l scripts/update_docs.py                    # baseline (630)

# 1. Validação estática
/home/andrefarias/.local/bin/ruff check scripts/update_docs.py

# 2. Rodar o sync (modo escrita reescreve README via o próprio script)
./venv/bin/python scripts/update_docs.py

# 3. DEPOIS: divergencia resolvida
grep -n "até 50 iterações" README.md            # deve EXISTIR depois
grep -n "até 30 iterações" README.md            # NÃO deve existir
grep -n "testes em" README.md                   # linha 351 sincronizada
wc -l scripts/update_docs.py                    # ~700-705

# 4. --check limpo (idempotencia)
./venv/bin/python scripts/update_docs.py --check ; echo "exit=$?"   # exit 0

# 5. REGRESSAO controlada (injeta divergencia, prova que o check pega)
sed -i 's/até 50 iterações/até 99 iterações/' README.md
./venv/bin/python scripts/update_docs.py --check ; echo "exit=$?"   # exit 1
./venv/bin/python scripts/update_docs.py                            # corrige
./venv/bin/python scripts/update_docs.py --check ; echo "exit=$?"   # exit 0
grep -n "até 50 iterações" README.md                               # restaurado

# 6. Acentuacao PT-BR (BRIEF: flag --paths OBRIGATORIA)
python3 ~/.config/zsh/scripts/validar-acentuacao.py --paths \
  scripts/update_docs.py \
  dev-journey/06-sprints/producao/SPRINT_INFRA_DOC_SYNC_COVERAGE_01.md

# 7. Smoke boot
./run.sh --smoke    # imprime "boot ok", exit 0

# 8. Invariantes
bash scripts/sprint_invariants.sh   # PASS 14/14 FAIL 0
```

---

## Critério binário de aceite (IA executora)

- [ ] `_read_max_iterations()` existe e lê `MAX_ITERATIONS=50` de defaults.py.
- [ ] `_count_gauntlet_phases()` existe e retorna número derivável estável (60 via PHASE_TIMEOUTS, ou 53 via PHASE_GROUPS['completo'] com docstring justificando).
- [ ] `update_readme()` reescreve `até N iterações`, `## ADRs (N)`, `N testes em M fases` (linha 351).
- [ ] Após rodar: README:88 = `até 50 iterações`; `até 30 iterações` ausente.
- [ ] META-CHECK existe, lista números auto-deriváveis e alerta/falha se algum sem regex.
- [ ] `./venv/bin/python scripts/update_docs.py --check` exit 0 após sync.
- [ ] Regressão `99 iterações`: `--check` exit 1 -> sync -> `--check` exit 0 (output colado).
- [ ] `ruff check scripts/update_docs.py` sem erros.
- [ ] `validar-acentuacao.py --paths` exit 0.
- [ ] Smoke `./run.sh --smoke` = `boot ok` exit 0.
- [ ] Invariantes 14/14, FAIL 0, FAIL_AFTER <= FAIL_BEFORE.
- [ ] `wc -l scripts/update_docs.py` antes/depois colado (delta dentro de 670-710L final).
- [ ] Nenhum touch em `dev-journey/07-reports/*`, `novo_layout/*.jsx` nem nos 6 arquivos do check #14.
- [ ] `GUIDE.md`/`SPRINT_ORDER_MASTER.md` atualizados marcando CONCLUIDA; sprint movida para `concluidos/`.
- [ ] Commit atômico no padrão `feat(docs): ...` ou `feat(infra): ...`.

---

## Guardrails anti-engodo (obrigatórios)

A IA executora **NÃO pode marcar concluída** se:

- README foi editado à mão (números) em vez de reescrito pelo próprio script. Verificar: o diff do README deve ser consequência de rodar `update_docs.py`, não de Edit manual de dígitos.
- O número de fases foi chutado (qualquer valor != 60 e != 53). Verificar contra `PHASE_TIMEOUTS`/`PHASE_GROUPS['completo']`.
- A regressão `99 iterações` não foi exercitada com output real do exit 1 -> 0.
- `--check` final não retorna exit 0 (significa que algum doc ficou dessincronizado).
- O meta-check é cosmético (sempre retorna vazio independente do estado) — gambiarra. Ele deve realmente detectar ausência: se o executor remover temporariamente um dos regex de README, o meta-check deve acusar.
- Tocou arquivo do check #14 ou arquivo periférico com dano de glifo (fora do escopo).

Se qualquer item falhar:
```
[SPRINT INFRA-DOC-SYNC-COVERAGE-01] BLOQUEADA: <motivo objetivo em 1 linha>
```

---

## Gambiarras específicas desta sprint

Ver `dev-journey/08-templates/GAMBIARRAS_POR_SPRINT.md` §"Catálogo Universal". Específicas deste escopo:

- **Hardcodar o valor no README** ("trocar 30 por 50 na mão") em vez de adicionar o regex. Resolve o sintoma de hoje e perpetua o débito — o objetivo é o regex sincronizador, não o número certo num instante. Detecção: `git diff README.md` deve mostrar mudança gerada pelo script; `git diff scripts/update_docs.py` deve conter os regex novos.
- **Meta-check fantasma** que retorna `[]` sempre. Detecção: teste de inversão — remover um regex e confirmar que o meta-check acusa.
- **Contar fases pelo número frágil.** Usar `len(PHASE_GROUPS)` cru (75, inclui aliases) ou `grep -c "_phase_"` em string solta (pega comentários). Usar `PHASE_TIMEOUTS` (via `ast`) ou `PHASE_GROUPS["completo"]`.
- **Regex que casa a linha errada.** O regex de testes/fases NÃO pode reativar na linha 426 (já coberta) nem vice-versa. Ancorar em `**Gauntlet**:` para a 351. Verificar `grep -n "testes" README.md` mostra ambas as linhas coerentes após sync.

---

## Proof-of-work obrigatório (4 passos)

```bash
# PASSO 1 — snapshot ANTES
bash scripts/sprint_invariants.sh > /tmp/inv_before.txt 2>&1
FAIL_BEFORE=$(grep -c "^\[FAIL\]" /tmp/inv_before.txt)
echo "FAIL inicial: $FAIL_BEFORE"
wc -l scripts/update_docs.py        # baseline 630
grep -n "até 30 iterações" README.md

# PASSO 2 — implementação (seguindo literalmente este arquivo)
#            + consultar dev-journey/08-templates/GAMBIARRAS_POR_SPRINT.md

# PASSO 3 — snapshot DEPOIS
bash scripts/sprint_invariants.sh > /tmp/inv_after.txt 2>&1
FAIL_AFTER=$(grep -c "^\[FAIL\]" /tmp/inv_after.txt)
echo "FAIL final: $FAIL_AFTER"
wc -l scripts/update_docs.py        # ~700-705

# PASSO 4 — regras binárias
#   (a) FAIL_AFTER <= FAIL_BEFORE
#   (b) diff /tmp/inv_before.txt /tmp/inv_after.txt no relatório
#   (c) output da regressão 99 iterações colado
```

**Formato obrigatório do relatório de conclusão:**

```
### Proof-of-work
$ cat /tmp/inv_before.txt | tail -10
(saída bruta)
$ cat /tmp/inv_after.txt | tail -10
(saída bruta)
$ diff /tmp/inv_before.txt /tmp/inv_after.txt
(diff)
FAIL inicial: N
FAIL final:   M  (M <= N)

### Aritmética
$ wc -l scripts/update_docs.py   # antes / depois
630 -> ~70x

### Comando específico (regressão)
$ ./venv/bin/python scripts/update_docs.py --check ; echo $?   # apos sync -> 0
$ sed -i 's/até 50 iterações/até 99 iterações/' README.md
$ ./venv/bin/python scripts/update_docs.py --check ; echo $?   # -> 1
$ ./venv/bin/python scripts/update_docs.py
$ ./venv/bin/python scripts/update_docs.py --check ; echo $?   # -> 0
(output real, não editado)

### Smoke
$ ./run.sh --smoke   # boot ok, exit 0

### Git
$ git show --stat HEAD
```

**Se o output acima não for colado integralmente: sprint é rejeitada.**

---

## Validação humana (checklist do usuário)

```bash
cd /home/andrefarias/Desenvolvimento/Nyx-Code

# 1. Ver diff do commit
git log --oneline -1
git show --stat HEAD

# 2. Provar a sincronizacao
grep -n "até 50 iterações" README.md     # deve aparecer (antes era 30)
./venv/bin/python scripts/update_docs.py --check ; echo "exit=$?"   # exit 0

# 3. Arquivos movidos
ls dev-journey/06-sprints/concluidos/SPRINT_INFRA_DOC_SYNC_COVERAGE_01.md   # existe
ls dev-journey/06-sprints/producao/SPRINT_INFRA_DOC_SYNC_COVERAGE_01.md     # NÃO existe
```

Se qualquer passo divergir do esperado, a sprint **não está concluída**, mesmo que a IA afirme.

---

## Riscos

| Risco | Mitigação |
|-------|-----------|
| Mudar 53->60 quebra expectativa narrativa do usuário | Documentado como decisão de design (OPÇÃO A vs B); ambas válidas; executor escolhe e justifica no docstring. Número permanece derivável e verdadeiro. |
| Regex da linha 351 vazar para a linha 426 (dupla substituição) | Ancorar em `**Gauntlet**:` (exclusivo da 351). Verificar `grep -n "testes" README.md` pós-sync. |
| `_count_gauntlet_phases` via `ast` falha se gauntlet tiver sintaxe nova | `try/except (SyntaxError, ValueError)` com fallback 0; o `--check` acusaria divergência (fail-loud), não silêncio. |
| Meta-check muito rígido bloqueia commits legítimos | Em modo escrita os regex corrigem antes; meta-check só falha em `--check` quando há número auto-derivável sem regex — exatamente o débito que combate. |
| `run.sh:828/843` roda update_docs em modo escrita (não --check) | Esperado: o gauntlet/boot pode reescrever README — side-effect já documentado no BRIEF §[CORE]. Não é violação de escopo. |
| Pre-commit ativo (`scripts/hooks/pre-commit:265`) roda `--check` e auto-corrige na 268 | Comportamento desejado: garante que o commit sai sincronizado. Confirmar que o hook não entra em loop (auto-fix re-stage é one-shot). |

---

## Referências

- BRIEF: `/home/andrefarias/Desenvolvimento/Nyx-Code/VALIDATOR_BRIEF.md` (§[CORE] Contratos de runtime, §[CORE] Side-effect do --gauntlet em README, §[CORE] Heurísticas de aritmética, §[CORE] Sintaxe correta de utilitários externos).
- Precedente direto: `DOC-COUNT-INTERNAL-SYNC-01` (255, ONDA-31) — `dev-journey/06-sprints/concluidos/SPRINT_DOC_COUNT_INTERNAL_SYNC_01.md`.
- Precedente de meta-check de cobertura: `INVARIANT-14-COVERAGE` (254, ONDA-31).
- Decisão de fonte de verdade tools/commands: `BANNER-TOOLS-COUNT-01` — `dev-journey/06-sprints/concluidos/SPRINT_BANNER_TOOLS_COUNT_01.md`.
- Código investigado: `scripts/update_docs.py` (630L), `nyx/config/defaults.py:72`, `scripts/gauntlet/nyx_gauntlet.py:51,183` (`PHASE_GROUPS`/`PHASE_TIMEOUTS`), `README.md:88,308,351,426`, `scripts/hooks/pre-commit:265,268`, `run.sh:828,843`.

---

*"Documentação que mente é pior que documentação ausente: a ausente você desconfia, a que mente você acredita." -- adágio de engenharia*
