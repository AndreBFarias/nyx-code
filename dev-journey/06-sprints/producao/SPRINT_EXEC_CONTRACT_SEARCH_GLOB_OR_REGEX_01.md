## 0. SPEC (machine-readable)

```yaml
sprint:
  id: EXEC-CONTRACT-SEARCH-GLOB-OR-REGEX-01
  title: "Contrato: a tool search aceita glob (*.md, **/*.py) sem crashar -- infra robusta, não o modelo"
  onda: 48
  prioridade: ALTA
  tipo: Fix
  dependencias: [EXEC-CONTRACT-NO-HALLUCINATED-RESULT-01, LOOP-RESULT-NOT-AS-INPUT-01]
  desbloqueia: []

  touches:
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/agent/tools/search.py
      reason: "compilar o pattern; se falhar como regex, tratar como glob e traduzir para regex de substring -- nunca mais retornar 'Regex inválido' para globs comuns"
      linhas_alvo: "bloco try/except re.compile (linhas 55-64) + helper novo antes/dentro da classe SearchTool"
  creates: []
  removes: []

  forbidden:
    - "Adicionar emoji"
    - "Usar 'print()' fora de cli.py/output.py"
    - "Mencao a IA proprietaria"
    - "Traduzir glob quando o pattern JA compila como regex (regex legítima foo.*bar DEVE ser preservada intacta)"
    - "Retornar erro (mesmo helpful) ao modelo: a 400 realimenta erro como pattern seguinte -- a tool DEVE ter sucesso, não instruir"
    - "Tocar glob_tool.py, o intent.py, a apresentação da 399, o sanitize da 397, a anti-recursao da 400, gating, write_memory, cascata OOM"
    - "Adicionar dependência nova de import além de re (já importado)"

  tests:
    - cmd: "./run.sh --gauntlet --only rapido"
      timeout: 300
      deve_passar: true

  acceptance_criteria:
    - "search com pattern '*.md' retorna success=True (não mais 'Regex inválido: nothing to repeat')"
    - "search com pattern '**/*.py' retorna success=True"
    - "search com regex legítima ('ActionResult', 'foo.*bar', 'think') mantém comportamento idêntico ao atual (regex preservada, mesmo caminho rg/grep)"
    - "O pattern efetivo (traduzido) é o que vai ao caminho rápido rg/grep E ao walk -- consistência entre os dois caminhos"
    - "A tool NUNCA retorna 'Regex inválido' para pattern não-vazio (glob sempre traduzível; último recurso literal via re.escape)"
    - "Gauntlet rapido 100% (F2-04 search e F2-03 glob intactos)"
```

---

# Sprint EXEC-CONTRACT-SEARCH-GLOB-OR-REGEX-01 — a tool search aceita glob

**Status:** PENDENTE
**Data criação:** 2026-07-12
**Modelo obrigatório:** claude-opus-4-7 (executor-sprint autorizado pelo dono nesta onda)

---

## Contexto do projeto (snapshot — não referência)

> **ADRs relevantes (inline):**
> - **ADR-034 FEITO PARA QUEM NÃO TEM A100:** a robustez mora na INFRA, não no modelo. O `qwen2.5-coder:3b` é fraco e emite o que é natural para ele; a tool deve aceitar o que o modelo naturalmente produz, em vez de exigir que o modelo aprenda o formato exato. Corolário direto desta sprint: a tool `search` deve engolir glob sem crashar.
> - **ADR-032 A INFRA CARREGA O MODELO** e **ADR-033 A CADEIA NUNCA QUEBRA:** um erro de tool não pode virar realimentação que polui a resposta (é exatamente o que a sprint 400 provou: o erro vira o pattern da busca seguinte -> recursão que suja o `Resultado:`).
>
> **Estado (2026-07-12):** `qwen2.5-coder:3b`, Ollama :11435, proxy :11436. ONDA-48 núcleo do contrato CONCLUIDO: 399 `f0883a1`, 397 `6c61f1d`, 400 `b1a17fe`, 398 `2e15c81`, 401 `2a89e19`. Esta é a família 409 (achado colateral da validação as-user da 399), registrada no bloco `MANUAL_OVERRIDE_ONDA_48` de `dev-journey/06-sprints/SPRINT_ORDER_MASTER.md` como PENDENTE, sem arquivo em `producao/` até agora.

---

## Problema

**Achado 409 SEARCH-GLOB-VS-REGEX [ALTA]** (validação as-user da 399, sessão contínua, 2026-06-26 ~19:12, `~/.nyx/logs/nyx.log`):

- A tool `search` (`nyx/agent/tools/search.py`) trata o `pattern` como **regex** e compila com `re.compile(pattern, re.IGNORECASE)` (linha 56). Um glob comum quebra a compilação:
  - `*.md` -> `re.error: nothing to repeat at position 0`
  - `**/*.py` -> `re.error: nothing to repeat at position 0`
  - `src/**/*.ts` -> `re.error: multiple repeat at position 5`
- A tool então retorna `ActionResult(success=False, error="Regex inválido: ...")` (linha 58).
- Em **sessão contínua**, o 3b usa glob **naturalmente** ao buscar/listar (ex.: ao trabalhar em `~/Desktop`). O erro retornado é realimentado (efeito da sprint 400) como pattern da busca seguinte -> **3 erros encadeados + recursão que poluiu o `Resultado:`** da resposta da 399.

**Evidência reproduzida (runtime real, python puro, sem stack):**
```
'*.md'         -> ERRO: Regex inválido: nothing to repeat at position 0
'**/*.py'      -> ERRO: Regex inválido: nothing to repeat at position 0
'ActionResult' -> OK: (busca de conteúdo funciona)
```

**Causa-raiz:** o contrato da tool exige do modelo fraco um formato (regex) que ele não domina, quando o que ele emite naturalmente é glob. Violação direta de ADR-034: a rigidez está na infra, empurrando a robustez para o modelo.

---

## Abordagem recomendada (UMA)

Das três opções catalogadas na tabela — (a) detectar glob e converter para regex/fnmatch, (b) aceitar ambos via flag, (c) reforçar schema/descrição —, a recomendação é **(a) conversão automática glob->regex, restrita ao caminho de erro**.

Por que (a) e não (b)/(c):

- **(b) flag** exige que o 3b saiba setar um parâmetro extra correto. Modelo fraco não seta flags de forma confiável -> empurra robustez para o modelo (anti-ADR-034).
- **(c) reforçar descrição/schema** depende do 3b LER e OBEDECER a descrição da tool. A descrição atual já diz "Regex para buscar" e o modelo emite glob mesmo assim. Além disso, qualquer variante que RETORNE erro/instrução ao modelo é exatamente o vetor que a sprint 400 mostrou poluir o `Resultado:` (o erro vira o pattern seguinte). A tool tem que **ter sucesso**, não instruir.
- **(a) conversão** é robustez pura na infra: o modelo emite glob, a tool entende e devolve resultado. É a leitura literal de ADR-034.

**Restrição crítica de precisão (evita regressão):** traduzir **somente quando a compilação regex falha**. Regex legítima (`foo.*bar`, `ActionResult`, `think`) compila e é preservada intacta — mesmo caminho `rg`/`grep` de hoje, zero mudança de comportamento. Só o caminho de exceção (`re.error`) é reescrito. Mudança cirúrgica, um arquivo.

**Semântica da tradução:** `search` é grep de **conteúdo** (usa `regex.search(line)`). O glob é traduzido para regex de **substring** (sem âncora de fim), então `*.md` -> `.*\.md` casa qualquer linha que **referencie** um `.md`. Verificado empíricamente:
```
'*.md'    -> eff='.*\.md'         (casa "veja o README.md agora")
'**/*.py' -> eff='.*.*/.*\.py'    (casa "import nyx/agent/parser.py")
'foo.*bar'-> preservada (compila como regex, não traduz)
```

Optou-se por tradutor glob->regex **artesanal** (loop char-a-char com `re.escape`) em vez de `fnmatch.translate`: o `fnmatch.translate` ancora com `\Z` (fim de string), o que perde matches de substring numa busca de linha, e seu formato de saída varia entre versões de Python. O tradutor artesanal é estável, sem import novo (só `re`, já importado), e casa exatamente a semântica de `regex.search`.

---

## Arquivos alvo (paths absolutos)

### `/home/andrefarias/Desenvolvimento/Nyx-Code/nyx/agent/tools/search.py`

#### Edit 1 — helper de módulo `_glob_to_regex` (logo após a linha 24 `_SEARCH_TIMEOUT = 30`, antes de `class SearchTool`)

**Depois (adicionar):**
```python
def _glob_to_regex(pattern: str) -> str:
    """EXEC-CONTRACT-SEARCH-GLOB-OR-REGEX-01: o 3b emite glob naturalmente
    (*.md, **/*.py) onde a tool espera regex (ADR-034: robustez na infra,
    não no modelo). Traduz glob -> regex de SUBSTRING (sem âncora de fim,
    porque search usa regex.search(line)). Só chamado quando a compilação
    regex já falhou -- regex legítima nunca passa por aqui."""
    out: list[str] = []
    for ch in pattern:
        if ch == "*":
            out.append(".*")
        elif ch == "?":
            out.append(".")
        else:
            out.append(re.escape(ch))
    return "".join(out)
```

#### Edit 2 — método `_compile_pattern` (dentro de `SearchTool`, antes de `execute`)

**Depois (adicionar):**
```python
    def _compile_pattern(self, pattern: str) -> tuple[re.Pattern, str]:
        """Compila o pattern como regex. Se falhar, trata como glob e traduz
        (nunca mais 'Regex inválido' para *.md / **/*.py). Devolve
        (regex_compilada, pattern_efetivo); o efetivo vai também ao caminho
        rápido rg/grep para manter os dois caminhos coerentes."""
        try:
            return re.compile(pattern, re.IGNORECASE), pattern
        except re.error:
            effective = _glob_to_regex(pattern)
            try:
                return re.compile(effective, re.IGNORECASE), effective
            except re.error:
                # Último recurso: busca literal (nunca crasha).
                literal = re.escape(pattern)
                return re.compile(literal, re.IGNORECASE), literal
```

#### Edit 3 — substituir o try/except que retorna "Regex inválido" (linhas 55-64)

**Antes:**
```python
        try:
            regex = re.compile(pattern, re.IGNORECASE)
        except re.error as e:
            return ActionResult(success=False, error=f"Regex inválido: {e}")

        fast = self._search_fast(pattern, target, root)
        if fast is not None:
            return fast

        return self._search_walk(regex, target)
```
**Depois:**
```python
        # EXEC-CONTRACT-SEARCH-GLOB-OR-REGEX-01: aceita glob (*.md, **/*.py)
        # sem crashar; regex legítima passa intacta. O pattern efetivo (glob
        # traduzido, ou o próprio regex) alimenta o caminho rápido E o walk.
        regex, effective = self._compile_pattern(pattern)

        fast = self._search_fast(effective, target, root)
        if fast is not None:
            return fast

        return self._search_walk(regex, target)
```

Observação de escopo: NÃO alterar `_search_fast` nem `_search_walk` além de receber o `effective` já passado no Edit 3. O `_search_fast` continua repassando o pattern recebido a `rg`/`grep` (que entendem `.*\.md` como regex); o `_search_walk` recebe a `re.Pattern` já compilada.

---

## Aritmética (meta numérica)

Sem meta numérica de linhas nesta sprint (não há teto `search.py <N` no escopo). Registro do delta esperado apenas:

- `search.py` atual: **159L**.
- Adição: helper `_glob_to_regex` (~13L) + método `_compile_pattern` (~14L) + reescrita do bloco 55-64 (líquido ~-1L). Total projetado: **~185L**.
- Não há limite a fechar; a aritmética serve só de baliza de diff (`+~26L` líquidas, 1 arquivo).

---

## Diff esperado (resumo)

```
~ 1 arquivo modificado (nyx/agent/tools/search.py)
+ ~26 linhas líquidas
```

---

## Comandos de verificação (literais, copy-paste — python direto, sem stack/GPU)

```bash
cd /home/andrefarias/Desenvolvimento/Nyx-Code

# 1. Estatica + acentuacao
python -m ruff check nyx/agent/tools/search.py
python3 ~/.config/zsh/scripts/validar-acentuacao.py --paths nyx/agent/tools/search.py

# 2. PROOF runtime-real via ToolRegistry (sem subir proxy/ollama):
#    ANTES do fix os globs davam 'Regex inválido'; DEPOIS retornam success=True.
./venv/bin/python -c "
from nyx.agent.tools.registry import ToolRegistry
reg = ToolRegistry('.')
for p in ['*.md', '**/*.py', 'src/**/*.ts']:
    r = reg.execute('search', {'pattern': p, 'path': 'nyx/agent/tools'})
    print(f'{p!r:14} -> success={r.success} ' + ('OK' if r.success else 'ERRO: '+str(r.error)))
"
# ESPERADO: os 3 globs -> success=True (NENHUM 'Regex inválido')

# 3. NÃO-REGRESSÃO: regex legítima segue idêntica (busca de conteúdo real)
./venv/bin/python -c "
from nyx.agent.tools.registry import ToolRegistry
reg = ToolRegistry('.')
r = reg.execute('search', {'pattern': 'ActionResult', 'path': 'nyx/agent/tools/search.py'})
print('regex legit:', r.success, 'ActionResult' in (r.output or ''))
r2 = reg.execute('search', {'pattern': 'foo.*bar', 'path': 'nyx/agent/tools'})
print('regex com .* compila e roda:', r2.success)
"
# ESPERADO: regex legit True True; regex com .* True (preservada, não traduzida)

# 4. Smoke boot + invariantes + gauntlet rapido
./run.sh --smoke                      # boot ok, exit 0
bash scripts/sprint_invariants.sh     # PASS 14/14 FAIL 0
./run.sh --gauntlet --only rapido     # 100% (F2-03 glob e F2-04 search intactos)
```

> NOTA GPU: os passos 1-3 são python puro (não sobem proxy/ollama) e podem rodar com a GPU ocupada. Os passos 4 (smoke/invariantes/gauntlet) exigem a GPU livre — rodar quando a validação concorrente liberar (respeitar `feedback_bash_limites_orquestrador.md`: gauntlet via subagente + ler checkpoint).

---

## Critério binário de aceite (IA executora)

- [ ] `_glob_to_regex` + `_compile_pattern` em `search.py`; tradução SÓ no caminho de `re.error`
- [ ] Bloco `Regex inválido` (linhas 55-64) substituído; a tool não retorna mais esse erro para glob
- [ ] `effective` (pattern traduzido) passado ao `_search_fast`; `_search_walk` recebe a regex compilada
- [ ] Proof runtime colado: `*.md`, `**/*.py`, `src/**/*.ts` -> `success=True`
- [ ] Não-regressão colada: `ActionResult`/`foo.*bar` preservados (regex intacta, mesmo caminho)
- [ ] `ruff` limpo, acentuação rc=0, `FAIL_AFTER <= FAIL_BEFORE`
- [ ] Smoke `boot ok` + gauntlet `rapido` 100% (F2-03/F2-04)
- [ ] `SPRINT_ORDER_MASTER.md` marca 409 CONCLUIDA; spec movida para `concluidos/`
- [ ] NÃO commitar; NÃO tocar Checkpoint.md

---

## Guardrails anti-engodo (obrigatórios)

NÃO marcar concluída se:
- Regex legítima passou a ser traduzida (falso-positivo: `foo.*bar` virou `foo\.\*bar` ou similar). A tradução SÓ ocorre quando `re.compile(pattern)` levanta `re.error`.
- A tool ainda retorna `Regex inválido` para qualquer pattern não-vazio.
- O `_search_fast` recebeu o `pattern` cru (glob) em vez do `effective` -> `rg`/`grep` crashariam com o glob e o resultado mentiria.
- Proof runtime não colado (os 3 globs + as 2 regexes de não-regressão).

Se algo falhar: `[SPRINT 409] BLOQUEADA: <motivo 1 linha>`.

---

## Proof-of-work obrigatório (4 passos)

```bash
cd /home/andrefarias/Desenvolvimento/Nyx-Code
bash scripts/sprint_invariants.sh > /tmp/inv_before_409.txt 2>&1
FAIL_BEFORE=$(grep -c "^\[FAIL\]" /tmp/inv_before_409.txt)
# implementar
bash scripts/sprint_invariants.sh > /tmp/inv_after_409.txt 2>&1
FAIL_AFTER=$(grep -c "^\[FAIL\]" /tmp/inv_after_409.txt)
diff /tmp/inv_before_409.txt /tmp/inv_after_409.txt
```
Colar: inv_before/inv_after (tail), diff, proof runtime (3 globs + 2 regexes de não-regressão), `git --no-pager diff --stat`, saída de `ruff` e de `validar-acentuacao.py`.

---

## Gambiarras específicas desta sprint

- **Traduzir regex legítima:** o `_compile_pattern` DEVE tentar `re.compile(pattern)` primeiro e só cair na tradução no `except re.error`. `foo.*bar` compila -> nunca é traduzido.
- **Fast path com glob cru:** `rg`/`grep` também tratam o argumento como regex e crashariam com `*.md`. Por isso o `effective` (traduzido) vai ao `_search_fast`, não o `pattern` original.
- **Ancoragem do glob:** NÃO usar `fnmatch.translate` cru — ele ancora `\Z` (fim), perdendo matches de substring numa busca de linha, e varia por versão de Python. O tradutor artesanal casa `regex.search`.
- **Erro realimentado (400):** a correção elimina o erro na fonte; a tool passa a ter SUCESSO. Não introduzir nenhum novo retorno de erro/instrução que o loop possa realimentar como pattern seguinte.

---

## Validação humana (checklist do usuário)

```bash
cd /home/andrefarias/Desenvolvimento/Nyx-Code
git --no-pager show --stat HEAD
./venv/bin/python -c "
from nyx.agent.tools.registry import ToolRegistry
reg = ToolRegistry('.')
r = reg.execute('search', {'pattern': '*.md', 'path': 'dev-journey'})
print('glob *.md ->', 'OK' if r.success else 'FALHOU: '+str(r.error))
"
./run.sh   # em sessão contínua, peça algo que leve o 3b a buscar por glob; confirme
           # que o Resultado NÃO tem 'Regex inválido' encadeado
ls dev-journey/06-sprints/concluidos/SPRINT_EXEC_CONTRACT_SEARCH_GLOB_OR_REGEX_01.md  # existe pós-conclusão
```

---

## Riscos

| Risco | Mitigação |
|-------|-----------|
| Regex legítima com `*` (ex.: `foo.*bar`) ser traduzida por engano | Tradução SÓ no `except re.error`. `foo.*bar` compila -> preservada. Teste de não-regressão obrigatório. |
| Glob traduzido não casa a intenção real do 3b (search é grep de conteúdo, não busca de arquivo por nome) | Fora de escopo desta sprint. O objetivo é ELIMINAR o crash + a recursão que poluía o `Resultado:` (ADR-034). Redirecionamento cross-tool search->glob por intenção pertence à família tool-match (398), não à 409. |
| `rg`/`grep` interpretarem o `effective` de forma diferente do walk Python | O `effective` é regex POSIX-compatível simples (`.*`, `.`, chars escapados); `rg`/`grep` e `re` concordam. Se `rg` divergir, o `returncode not in (0,1)` cai no walk (fallback já existente). |
| Pattern degenerado (só metachars) gerar regex custosa | `_glob_to_regex` produz no máximo `.*` repetidos; o `_SEARCH_TIMEOUT=30` e o cap de 100 matches já limitam custo. |

---

*"A ferramenta que exige do modelo fraco o formato que ele não domina errou antes do modelo. A robustez mora na infra." -- ADR-034 (dev-journey/03-decisions/ADR_034_FEITO_PARA_QUEM_NAO_TEM_A100.md)*
