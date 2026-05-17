# SPRINT INFRA-SANITIZER-FIX-01 — Restaurar glifos canônicos + invariante anti-sanitizer

## 0. SPEC (machine-readable)

```yaml
sprint:
  id: INFRA-SANITIZER-FIX-01
  title: "Restaurar glifos canônicos removidos por sanitizer global + adicionar invariante #14 defensivo"
  onda: 23
  prioridade: MÉDIA
  tipo: Infra
  dependencias: []
  desbloqueia: [UX-LOOP-VISIBILITY-01]

  touches:
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/scripts/sprint_invariants.sh
      reason: "Adicionar check #14 (glifos canônicos preservados) como defesa em profundidade contra re-execução do sanitizer global"
      linhas_alvo: "199-200 (inserir antes de section 'Resumo')"
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/cli.py
      reason: "Comentário de 1 linha avisando que glifos abaixo são geometric shapes Unicode permitidos pelo ADR-004"
      linhas_alvo: "68-70 (próximo a _STATE_GLYPHS)"
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/themes/design_tokens.py
      reason: "Comentário de 1 linha avisando que ● e ○ em BULLETS são geometric shapes Unicode permitidos pelo ADR-004"
      linhas_alvo: "71-72 (antes do dicionário BULLETS)"
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/dev-journey/06-sprints/SPRINT_ORDER_MASTER.md
      reason: "Registrar linha nova da sprint INFRA-SANITIZER-FIX-01 no Bloco ONDA-23 / 23.0 Performance"

  creates: []
  removes: []

  restoration:
    # Restauração explícita de 23 arquivos versionados via `git checkout HEAD -- <path>`.
    # Não constam como `touches` porque voltam ao estado do commit 5bc4354 (HEAD na criação da sprint).
    # Lista obtida via `git diff --name-only` no working tree antes da execução.
    head_commit_at_planning: "5bc43545665570d05391102efa97445061dfacb1"
    files_to_restore:
      - dev-journey/06-sprints/SPRINT_ORDER_MASTER.md
      - dev-journey/06-sprints/concluidos/SPRINT_AUDIT_FIX_08.md
      - dev-journey/06-sprints/concluidos/SPRINT_TOOL_INVOKE_MEMORY_01.md
      - dev-journey/06-sprints/concluidos/SPRINT_TUI_01_HIGIENE.md
      - dev-journey/06-sprints/concluidos/SPRINT_TUI_02_BOXES.md
      - dev-journey/06-sprints/concluidos/SPRINT_TUI_FIX_04_BYPASS_TOGGLE.md
      - dev-journey/06-sprints/concluidos/SPRINT_TUI_FIX_06_SANDBOX_ERROR.md
      - dev-journey/06-sprints/concluidos/SPRINT_UX_BUG_02.md
      - dev-journey/06-sprints/concluidos/SPRINT_UX_BUG_02B.md
      - dev-journey/06-sprints/concluidos/SPRINT_UX_DESIGN_01.md
      - dev-journey/06-sprints/concluidos/SPRINT_UX_LAYOUT_01.md
      - dev-journey/06-sprints/concluidos/SPRINT_VALIDATE_ONDA_20.md
      - dev-journey/06-sprints/producao/SPRINT_DEPLOY_01A.md
      - dev-journey/06-sprints/producao/SPRINT_DEPLOY_02.md
      - dev-journey/06-sprints/producao/SPRINT_UX_CLAUDE_PARITY_01.md
      - dev-journey/06-sprints/producao/SPRINT_UX_LOOP_VISIBILITY_01.md
      - dev-journey/07-reports/AUDIT_EXT_2026_04_18.md
      - dev-journey/07-reports/RELATORIO_ONDA_20.md
      - dev-journey/07-reports/RELATORIO_ONDA_21.md
      - dev-journey/08-templates/GAMBIARRAS_POR_SPRINT.md
      - nyx/cli.py
      - nyx/themes/design_tokens.py
      - scripts/sprint_invariants.sh
    files_excluded_from_restore:
      - Checkpoint.md     # untracked / working state — atualizado pelo orquestrador APÓS conclusão
      - assets/           # untracked

  n_to_n_pairs:
    - descricao: "Glifos canônicos UX-BUG-02B existem em nyx/cli.py (_STATE_GLYPHS) e nyx/themes/design_tokens.py (BULLETS) — invariante #14 valida ambos"
      paths:
        - /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/cli.py
        - /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/themes/design_tokens.py

  forbidden:
    - "Modificar ~/.config/zsh/scripts/universal-sanitizer.py (escopo externo ao repo)"
    - "Modificar qualquer arquivo fora do repo Nyx-Code"
    - "Adicionar dependência nova (pre-commit, lint, codespell, etc.)"
    - "Adicionar ferramenta de sanitização própria no projeto (duplica responsabilidade do sanitizer global)"
    - "Mexer em código de runtime além dos 2 comentários de 1 linha (escopo cirúrgico)"
    - "Tocar Checkpoint.md (untracked — working state do orquestrador)"
    - "Skip de check (--no-verify, SKIP_*, git -c core.hookspath=)"
    - "Menção a Claude/Anthropic/GPT/Gemini/Copilot em commit, código ou strings (ADR-005)"
    - "Adicionar emoji em qualquer arquivo modificado (ADR-004)"
    - "Path absoluto hardcoded fora de design_tokens.py/settings.py"

  tests:
    - cmd: "bash scripts/sprint_invariants.sh"
      timeout: 30
      deve_passar: true
      esperado: "PASS=14, FAIL=0"
    - cmd: "./run.sh --smoke"
      timeout: 10
      deve_passar: true
      esperado: "stdout contém 'boot ok', exit 0"

  acceptance_criteria:
    - "git diff --shortstat retorna working tree limpo (zero modificações) após restauração + commits, exceto Checkpoint.md e assets/ (untracked)"
    - "nyx/cli.py contém literal '_STATE_GLYPHS = {\"cold\": \"○\", \"warming\": \"◐\", \"warm\": \"●\"}' (verificável via grep -F literal exato)"
    - "nyx/themes/design_tokens.py contém literais '\"tool\": \"●\"', '\"tool_ok\": \"●\"', '\"tool_err\": \"●\"', '\"ready\": \"●\"', '\"working\": \"○\"' no dicionário BULLETS (5 ocorrências verificáveis)"
    - "scripts/sprint_invariants.sh tem 14 checks ativos: PASS=14, FAIL=0"
    - "./run.sh --smoke imprime 'boot ok' e exit 0"
    - "wc -l scripts/sprint_invariants.sh aumenta no máximo 30 linhas (213 -> <=243)"
    - "Zero menção a Claude/Anthropic/GPT/Gemini/Copilot em commit message e código novo (ADR-005)"
    - "Acentuação PT-BR correta em todos comentários novos (ADR-006)"
    - "Zero emoji em arquivos modificados (ADR-004) — Box Drawing, Braille e Geometric Shapes permitidos"
    - "Spec da sprint movido de producao/ para concluidos/ após CONCLUIDA"
    - "SPRINT_ORDER_MASTER.md tem linha INFRA-SANITIZER-FIX-01 no bloco ONDA-23 / 23.0 Performance com status CONCLUIDA"
```

---

# Sprint INFRA-SANITIZER-FIX-01 — Restaurar glifos canônicos + invariante anti-sanitizer

**Status:** CONCLUIDA
**Data criação:** 2026-05-17
**Data conclusão:** 2026-05-17
**Hash:** e16e61b
**Modelo obrigatório:** claude-opus-4-7 (sem subagentes)
**Resultado:** 23 arquivos versionados restaurados bit-exact via `git checkout HEAD --` antes de qualquer edição. Touches autorizados: scripts/sprint_invariants.sh (+19L líquidas, check #14 "glifos canônicos preservados"), nyx/cli.py (+1L comentário ADR-004), nyx/themes/design_tokens.py (+1L comentário ADR-004), SPRINT_ORDER_MASTER.md (linha 124 da sprint), GAMBIARRAS_POR_SPRINT.md (entrada anti-débito). Invariantes: PASS=13→14, FAIL=0→0. `./run.sh --smoke` retorna `boot ok` exit 0 em 0.14s. Aritmética: 213→232 linhas (meta < 243, margem 11). Sanitizer global em `~/.config/zsh/scripts/universal-sanitizer.py` intacto (escopo externo). Validador: APROVADO_COM_RESSALVAS — ressalva única (entrada em GAMBIARRAS_POR_SPRINT.md) absorvida no mesmo commit técnico.

---

## Contexto do projeto (snapshot — não referência)

> **ADRs relevantes (essencial inline):**
>
> - ADR-001 Local First: tudo offline.
> - ADR-004 Zero Emojis: em tudo. **Exceção explícita**: Geometric Shapes Unicode (U+25A0-U+25FF) e Box Drawing (U+2500-U+257F) e Braille (U+2800-U+28FF) NÃO são emoji — são símbolos técnicos permitidos. Citação literal do spec UX-BUG-02B (`dev-journey/06-sprints/concluidos/SPRINT_UX_BUG_02B.md:36`): "Emoji como glifo (usar só caracteres Unicode genéricos: cifrao-circulo branco, cifrao-circulo meio, cifrao-circulo cheio)" — texto original cita os glifos diretamente; aqui evitado para não disparar verificadores que ainda não distinguem geometric shapes de emoji.
> - ADR-005 Anonimato: sem menção a IA externa em código/commits.
> - ADR-006 PT-BR: acentuação obrigatória em comentários/textos.
> - ADR-013 Integração obrigatória: nada solto, tudo no registry.
> - ADR-020 Testes via run.sh: `./run.sh --gauntlet --only <fase>`.
>
> **Estado do sistema na data da sprint:**
> - Python 3.10+, modelo `qwen2.5-coder:3b` no Ollama porta 11435, proxy 11436.
> - 35 tools (runtime), 52 commands únicos, 9 services.
> - HEAD: `5bc43545665570d05391102efa97445061dfacb1` (sincronizado com `origin/main`: `0 0` no `git rev-list --left-right --count HEAD...origin/main`).
> - Working tree: 23 arquivos modificados POS-PUSH, `112 insertions(+), 112 deletions(-)` — todos por ação inadvertida do sanitizer global.
> - Sprint anterior CONCLUIDA: `UX-BUG-03` (commit `14e96aa`, start <1.5s).
> - Próxima sprint estratégica (desbloqueada por esta): `UX-LOOP-VISIBILITY-01` — depende do indicador cold/warming/warm restaurado em `_STATE_GLYPHS`.

---

## Problema

### Sintoma observável

`git diff --shortstat` retorna `23 files changed, 112 insertions(+), 112 deletions(-)` em `main` POS-PUSH (estado anômalo: HEAD sincronizado com `origin/main` mas working tree sujo).

### Causa-raiz identificada (já validada pelo planejador)

O sanitizer global do usuário em `~/.config/zsh/scripts/universal-sanitizer.py` define `EMOJI_RE` com ranges Unicode que capturam **caracteres legítimos não-emoji**:

- Range `\U000025AA-\U000025FE` cobre Geometric Shapes incluindo `U+25CB` (white circle), `U+25CF` (black circle) e `U+25D0` (circle with left half black).
- Range `\U000023F8-\U000023FA` cobre `U+23FA` (Black Circle for Record).

Esses glifos são **permitidos pelo ADR-004** e são **carga útil de runtime** das features UX-BUG-02B e UX-LAYOUT-01.

### Impacto runtime (medido)

1. **`nyx/cli.py:70`** — `_STATE_GLYPHS = {"cold": "", "warming": "", "warm": ""}`. Todos os 3 glifos do indicador de estado do modelo (UX-BUG-02B) sumiram. **Feature visualmente quebrada em runtime** — bottom_toolbar não consegue desenhar transição cold->warming->warm.

2. **`nyx/themes/design_tokens.py:72-84`** — `BULLETS = {"tool": "", "tool_ok": "", "tool_err": "", "ready": "", "working": "", ...}`. Bullets visuais do design system removidos. **Design tokens sem carga útil**, fallback ASCII silencioso.

3. **`scripts/sprint_invariants.sh:53`** — comentário do EMOJI_RE perdeu a citação literal do caractere `U+26A1` que vinha entre parênteses. **Zero impacto runtime** (só comentário; o range Unicode na regex segue intacto).

4. **19 arquivos de doc** (`dev-journey/06-sprints/`, `07-reports/`, `08-templates/`) — referências históricas a vários símbolos (raios, círculos cheios/vazios/parciais, gravação) foram suprimidas. **Rastreabilidade textual degradada**, **zero impacto runtime**.

### Evidência colhida

```
$ git rev-parse HEAD
5bc43545665570d05391102efa97445061dfacb1

$ git diff --shortstat
 23 files changed, 112 insertions(+), 112 deletions(-)

$ git rev-list --left-right --count HEAD...origin/main
0	0
```

```
$ git show HEAD:nyx/cli.py | sed -n '70p'
_STATE_GLYPHS = {"cold": "○", "warming": "◐", "warm": "●"}

$ cat nyx/cli.py | sed -n '70p'
_STATE_GLYPHS = {"cold": "", "warming": "", "warm": ""}
```

Diferença line-for-line entre HEAD (committed) e working tree (sanitizado): os 3 caracteres dos valores removidos in-place.

---

## Solução proposta

Restaurar 23 arquivos via `git checkout HEAD -- <path>` (volta ao commit `5bc4354`), adicionar invariante #14 em `scripts/sprint_invariants.sh` como defesa em profundidade, e marcar 2 pontos de código com comentário curto avisando que os glifos abaixo são geometric shapes permitidos pelo ADR-004.

**Não tocar no sanitizer global** — escopo fora do repo. Mensagem de commit menciona como nota informativa para o usuário ajustar.

---

## Notas de planejamento (correções factuais ao briefing)

O briefing original do orquestrador continha 2 critérios numericamente incorretos que foram corrigidos neste spec após verificação direta do HEAD:

1. **`grep -c "○\|◐\|●" nyx/cli.py >= 3`** — factualmente impossível. `grep -c` conta **linhas**, não caracteres. Em HEAD, os 3 glifos coexistem na **mesma linha 70**, então `grep -c` retorna `1`, não `3`. Substituído por critério literal: presença do dicionário `_STATE_GLYPHS = {"cold": "○", "warming": "◐", "warm": "●"}` via `grep -F` exato.
2. **`grep -c "●" nyx/themes/design_tokens.py >= 5`** — factualmente impossível. Em HEAD, o círculo cheio aparece em **4 linhas**: `tool`, `tool_ok`, `tool_err`, `ready`. O quinto valor seria `working`, mas usa círculo branco (não círculo cheio). Substituído por: contagem de 4 ocorrências do círculo cheio + 1 do círculo branco em chaves específicas, verificáveis individualmente.

Ambas as correções **mantêm a intenção** (validar que os 5 glifos canônicos do BULLETS foram restaurados), apenas com critérios precisos. Documentado aqui para transparência ao executor.

---

## Arquivos alvo (paths absolutos)

### `/home/andrefarias/Desenvolvimento/Nyx-Code/scripts/sprint_invariants.sh`

**Antes** (HEAD, linhas 191-211, check #13 + Resumo):

```bash
# 13. ./run.sh --smoke retorna 0 e imprime exatamente 'boot ok' (boot integrity, BOOT-FIX-01)
SMOKE_OUT=$(timeout 5 ./run.sh --smoke 2>&1)
SMOKE_RC=$?
if [ $SMOKE_RC -eq 0 ] && echo "$SMOKE_OUT" | grep -qx "boot ok"; then
    ok "13. ./run.sh --smoke (boot integrity)"
else
    SMOKE_HEAD=$(echo "$SMOKE_OUT" | head -3 | tr '\n' '|')
    fail "13. ./run.sh --smoke (boot integrity)" "exit=${SMOKE_RC}, stdout=${SMOKE_HEAD}"
fi

section "Resumo"
```

**Depois** (inserir check #14 entre #13 e a section "Resumo"):

```bash
# 13. ./run.sh --smoke retorna 0 e imprime exatamente 'boot ok' (boot integrity, BOOT-FIX-01)
SMOKE_OUT=$(timeout 5 ./run.sh --smoke 2>&1)
SMOKE_RC=$?
if [ $SMOKE_RC -eq 0 ] && echo "$SMOKE_OUT" | grep -qx "boot ok"; then
    ok "13. ./run.sh --smoke (boot integrity)"
else
    SMOKE_HEAD=$(echo "$SMOKE_OUT" | head -3 | tr '\n' '|')
    fail "13. ./run.sh --smoke (boot integrity)" "exit=${SMOKE_RC}, stdout=${SMOKE_HEAD}"
fi

# 14. Glifos canônicos preservados (defesa anti-sanitizer global, INFRA-SANITIZER-FIX-01)
#     Geometric Shapes U+25CB, U+25D0, U+25CF são Unicode genéricos
#     permitidos pelo ADR-004 (NÃO são emoji). Carga útil de UX-BUG-02B + UX-LAYOUT-01.
GLYPH_FAIL=""
if ! grep -qF '_STATE_GLYPHS = {"cold": "○", "warming": "◐", "warm": "●"}' nyx/cli.py 2>/dev/null; then
    GLYPH_FAIL="nyx/cli.py: _STATE_GLYPHS sem glifos canônicos"
fi
if ! grep -qF '"tool": "●"' nyx/themes/design_tokens.py 2>/dev/null \
   || ! grep -qF '"ready": "●"' nyx/themes/design_tokens.py 2>/dev/null \
   || ! grep -qF '"working": "○"' nyx/themes/design_tokens.py 2>/dev/null; then
    GLYPH_FAIL="${GLYPH_FAIL:+$GLYPH_FAIL; }nyx/themes/design_tokens.py: BULLETS sem glifos canônicos"
fi
if [ -n "$GLYPH_FAIL" ]; then
    fail "14. glifos canônicos preservados (anti-sanitizer)" "${GLYPH_FAIL}"
else
    ok "14. glifos canônicos preservados (UX-BUG-02B + UX-LAYOUT-01)"
fi

section "Resumo"
```

**Mudanças:**
- Inserir 18 linhas (check #14 completo) entre check #13 e `section "Resumo"`.
- Atualizar comentário do cabeçalho (linha 4): `13 checks` -> `14 checks`.
- Linhas líquidas adicionadas: ~18-20 (dentro do limite de 30).

---

### `/home/andrefarias/Desenvolvimento/Nyx-Code/nyx/cli.py`

**Antes** (HEAD, linhas 68-70):

```python
# Glifos do estado do modelo (UX-BUG-02B).
# Círculos da faixa Geometric Shapes (U+25CB/D0/CF) — não são emoji.
_STATE_GLYPHS = {"cold": "○", "warming": "◐", "warm": "●"}
```

**Depois** (após restauração via `git checkout HEAD --`, adicionar 1 linha):

```python
# Glifos do estado do modelo (UX-BUG-02B).
# Círculos da faixa Geometric Shapes (U+25CB/D0/CF) — não são emoji.
# NÃO remover via sanitizer global: invariante #14 (sprint_invariants.sh) protege estes 3 caracteres.
_STATE_GLYPHS = {"cold": "○", "warming": "◐", "warm": "●"}
```

**Mudanças:**
- 1 linha de comentário adicional acima de `_STATE_GLYPHS`.

---

### `/home/andrefarias/Desenvolvimento/Nyx-Code/nyx/themes/design_tokens.py`

**Antes** (HEAD, linhas 71-72):

```python

BULLETS = {
```

**Depois** (após restauração, adicionar 1 linha de comentário):

```python

# NÃO remover círculos abaixo via sanitizer global: ADR-004 exceção (Geometric Shapes Unicode); invariante #14 protege.
BULLETS = {
```

**Mudanças:**
- 1 linha de comentário antes do dicionário `BULLETS`.

---

### `/home/andrefarias/Desenvolvimento/Nyx-Code/dev-journey/06-sprints/SPRINT_ORDER_MASTER.md`

**Antes** (linhas 333-336, fim do bloco 23.0 Performance):

```
| 121 | **MODEL-SWAP-01** | 23.0 Performance | ALTA | CONCLUIDA (...) | -- |
| 122 | **GAUNTLET-RAPIDO-FIXES-01** | 23.0 Performance | ALTA | CONCLUIDA (...) | -- |
| 123 | **LANG-PROMPT-ACENT-01** | 23.0 Performance | BAIXA | PENDENTE | LANG-ENFORCE-01 |
```

**Depois** (inserir linha entre 122 e 123):

```
| 121 | **MODEL-SWAP-01** | 23.0 Performance | ALTA | CONCLUIDA (...) | -- |
| 122 | **GAUNTLET-RAPIDO-FIXES-01** | 23.0 Performance | ALTA | CONCLUIDA (...) | -- |
| 124 | **INFRA-SANITIZER-FIX-01** | 23.0 Performance | MÉDIA | PENDENTE (anti-débito: restaurar glifos sanitizados; invariante #14) | -- |
| 123 | **LANG-PROMPT-ACENT-01** | 23.0 Performance | BAIXA | PENDENTE | LANG-ENFORCE-01 |
```

**Mudanças:**
- Inserir 1 linha nova com ID `124` (próximo ID livre após 123).
- Bloco: `23.0 Performance`.
- Prioridade: `MÉDIA`.
- Status na criação: `PENDENTE`.
- Após CONCLUIDA, executor atualiza status com hash do commit.

---

## Plano de implementação (passos numerados)

1. **Pré-execução — snapshot**:
   ```bash
   cd /home/andrefarias/Desenvolvimento/Nyx-Code
   git rev-parse HEAD                                    # esperar 5bc43545665570d05391102efa97445061dfacb1
   git diff --shortstat                                  # esperar "23 files changed, 112 insertions(+), 112 deletions(-)"
   git rev-list --left-right --count HEAD...origin/main  # esperar "0 0"
   bash scripts/sprint_invariants.sh > /tmp/inv_before.txt 2>&1 || true
   FAIL_BEFORE=$(grep -c "^\[FAIL\]" /tmp/inv_before.txt)
   echo "FAIL inicial: $FAIL_BEFORE"
   ```

2. **Restauração dos 23 arquivos versionados** (lista exata vem de `git diff --name-only`, exclui `Checkpoint.md` e `assets/` que são untracked):
   ```bash
   git checkout HEAD -- $(git diff --name-only)
   git diff --shortstat   # esperar saída vazia (0 modificações)
   ```

3. **Verificação imediata da restauração**:
   ```bash
   grep -F '_STATE_GLYPHS = {"cold": "○", "warming": "◐", "warm": "●"}' nyx/cli.py
   # esperar 1 linha match

   grep -cF '●' nyx/themes/design_tokens.py
   # esperar 4 (tool, tool_ok, tool_err, ready)

   grep -cF '○' nyx/themes/design_tokens.py
   # esperar 1 (working)
   ```

4. **Adicionar comentário em `nyx/cli.py`** (1 linha acima de `_STATE_GLYPHS`):
   - Texto literal: `# NÃO remover via sanitizer global: invariante #14 (sprint_invariants.sh) protege estes 3 caracteres.`
   - Posição: após a linha `# Círculos da faixa Geometric Shapes (U+25CB/D0/CF) — não são emoji.` e antes de `_STATE_GLYPHS = ...`.

5. **Adicionar comentário em `nyx/themes/design_tokens.py`** (1 linha acima de `BULLETS`):
   - Texto literal: `# NÃO remover círculos abaixo via sanitizer global: ADR-004 exceção (Geometric Shapes Unicode); invariante #14 protege.`
   - Posição: linha vazia logo antes de `BULLETS = {`.

6. **Adicionar invariante #14 em `scripts/sprint_invariants.sh`**:
   - Bloco completo conforme spec acima (subseção `Arquivos alvo` -> `sprint_invariants.sh` -> `Depois`).
   - Inserir entre o fim do check #13 e a linha `section "Resumo"`.
   - Atualizar o cabeçalho (linha 4): substituir `13 checks` por `14 checks`.

7. **Registrar linha nova em `SPRINT_ORDER_MASTER.md`**:
   - Inserir conforme subseção acima, ID 124, status `PENDENTE`.

8. **Validar invariantes**:
   ```bash
   bash scripts/sprint_invariants.sh > /tmp/inv_after.txt 2>&1
   FAIL_AFTER=$(grep -c "^\[FAIL\]" /tmp/inv_after.txt)
   PASS_AFTER=$(grep -c "^\[OK\]" /tmp/inv_after.txt)
   echo "PASS final: $PASS_AFTER, FAIL final: $FAIL_AFTER"
   # esperar PASS=14, FAIL=0
   ```

9. **Smoke obrigatório**:
   ```bash
   ./run.sh --smoke
   # esperar "boot ok" e exit 0
   ```

10. **Aritmética declarada**:
    ```bash
    wc -l scripts/sprint_invariants.sh
    # baseline: 213
    # esperado: <= 243 (aumento líquido < 30 linhas)
    ```

11. **Commit atômico** (mensagem em PT-BR, sem menção a IA):
    - Padrão: `fix(INFRA-SANITIZER-FIX-01): restaura glifos canônicos sanitizados + invariante #14`
    - Body deve mencionar: causa-raiz no sanitizer global externo, lista resumida dos 23 arquivos restaurados, link à decisão ADR-004 (geometric shapes permitidos), nota informativa de que `~/.config/zsh/scripts/universal-sanitizer.py` precisa ajuste por parte do usuário.
    - Body NÃO deve mencionar: Claude, Anthropic, GPT, Gemini, Copilot, IA, assistente, modelo de linguagem.

12. **Atualizar status no `SPRINT_ORDER_MASTER.md`** (após commit):
    - `PENDENTE` -> `CONCLUIDA (hash <commit-hash>)`.

13. **Mover spec**:
    ```bash
    git mv dev-journey/06-sprints/producao/SPRINT_INFRA_SANITIZER_FIX_01.md \
           dev-journey/06-sprints/concluidos/SPRINT_INFRA_SANITIZER_FIX_01.md
    ```

14. **Commit final do move + status** (separado do commit técnico ou amend conforme política do projeto — preferência é commit separado, ADR não força amend).

15. **Atualizar `Checkpoint.md`** com snapshot working-state pós conclusão (responsabilidade do orquestrador, não da sprint).

---

## Aritmética (meta numérica)

- Arquivo alvo único com aumento de linhas: `scripts/sprint_invariants.sh`.
- Linhas atuais (HEAD): **213**.
- Linhas adicionadas planejadas: **18-20** (check #14 + comentários internos).
- Linhas modificadas: **1** (cabeçalho `13 checks` -> `14 checks`).
- Projetado após: **231-233**.
- Meta: **< 243** (aumento líquido < 30 linhas).
- Margem: 10-12 linhas.

Demais arquivos: aumento mínimo (1 linha de comentário cada em `cli.py` e `design_tokens.py`; 1 linha nova em `SPRINT_ORDER_MASTER.md`). Sem impacto material em wc -l global.

---

## Diff esperado (resumo)

```
~ 4 arquivos modificados (touches reais):
  - scripts/sprint_invariants.sh         (+18-20 linhas)
  - nyx/cli.py                           (+1 linha)
  - nyx/themes/design_tokens.py          (+1 linha)
  - dev-journey/06-sprints/SPRINT_ORDER_MASTER.md  (+1 linha)

~ 23 arquivos restaurados ao HEAD (volta a 5bc4354 — diff líquido zero):
  - 22 listados em yaml.restoration.files_to_restore
  - +1 (scripts/sprint_invariants.sh) que é também touch

+ ~21 linhas líquidas (touches reais), 0 linhas líquidas (restaurados)
```

---

## Comandos de verificação (literais, copy-paste)

```bash
cd /home/andrefarias/Desenvolvimento/Nyx-Code

# 1. Working tree limpo
git diff --shortstat
# esperado: vazio (zero modificações pendentes além dos commits da sprint)

# 2. Conteúdo restaurado em runtime
grep -F '_STATE_GLYPHS = {"cold": "○", "warming": "◐", "warm": "●"}' nyx/cli.py
# esperado: 1 linha match exato

grep -nE '"(tool|tool_ok|tool_err|ready)": "●"' nyx/themes/design_tokens.py
# esperado: 4 linhas

grep -nE '"working": "○"' nyx/themes/design_tokens.py
# esperado: 1 linha

# 3. Invariantes + smoke
bash scripts/sprint_invariants.sh
# esperado: PASS=14, FAIL=0

./run.sh --smoke
# esperado: "boot ok" + exit 0

# 4. Aritmética
wc -l scripts/sprint_invariants.sh
# esperado: <= 243

# 5. Confirmar que sanitizer global NÃO foi modificado (escopo externo)
ls -la ~/.config/zsh/scripts/universal-sanitizer.py 2>/dev/null
# arquivo existe (não é tocado pela sprint, apenas validar que está fora do repo)
```

---

## Critério binário de aceite (IA executora)

- [ ] `git diff --shortstat` retorna working tree limpo após commits (exceto `Checkpoint.md` e `assets/` untracked).
- [ ] `grep -F '_STATE_GLYPHS = {"cold": "○", "warming": "◐", "warm": "●"}' nyx/cli.py` retorna 1 match exato.
- [ ] `grep -cF '●' nyx/themes/design_tokens.py` retorna 4.
- [ ] `grep -cF '○' nyx/themes/design_tokens.py` retorna 1.
- [ ] `bash scripts/sprint_invariants.sh` retorna `PASS=14, FAIL=0`.
- [ ] `./run.sh --smoke` imprime `boot ok` e exit 0.
- [ ] `wc -l scripts/sprint_invariants.sh` retorna valor <= 243.
- [ ] `nyx/cli.py` tem comentário novo de 1 linha citando "invariante #14" próximo a `_STATE_GLYPHS`.
- [ ] `nyx/themes/design_tokens.py` tem comentário novo de 1 linha citando "ADR-004 exceção" próximo a `BULLETS`.
- [ ] Sprint registrada em `SPRINT_ORDER_MASTER.md` com ID 124, status atualizado para `CONCLUIDA` ao final.
- [ ] Spec movido de `producao/` para `concluidos/`.
- [ ] Commit message em PT-BR acentuado, zero menção a IA externa, padrão `fix(INFRA-SANITIZER-FIX-01): ...`.
- [ ] Body do commit menciona como nota informativa que `~/.config/zsh/scripts/universal-sanitizer.py` precisa ajuste pelo usuário (apenas informa — não age).
- [ ] Nenhuma violação de `forbidden[]` (sanitizer global intacto, sem deps novas, sem skip flags).
- [ ] `Checkpoint.md` atualizado pelo orquestrador (não pela sprint).

---

## Guardrails anti-engodo (obrigatórios)

A IA executora **NÃO pode marcar sprint como CONCLUIDA** se:

- Algum critério acima estiver incompleto.
- Tentou "consertar" arquivos via `sed`/`awk` em vez de `git checkout HEAD --` (gambiarra: restauração precisa ser bit-exact ao commit `5bc4354`).
- Modificou `~/.config/zsh/scripts/universal-sanitizer.py` ou qualquer arquivo fora do repo (escopo externo).
- Adicionou dependência nova (codespell, pre-commit, etc.) para "resolver" o problema — `forbidden`.
- Criou ferramenta de sanitização própria — `forbidden`.
- "Invariantes passou" sem colar o output real de `bash scripts/sprint_invariants.sh`.
- Smoke passou em modo silencioso sem output mostrado ao validador.
- Editou o spec da sprint para "fazer caber" em vez de seguir o critério literal.

Se qualquer item falhar, a IA **deve** reportar:
```
[SPRINT INFRA-SANITIZER-FIX-01] BLOQUEADA: <motivo objetivo em 1 linha>
```

---

## Catálogo de gambiarras proibidas

Catálogo universal em `dev-journey/08-templates/GAMBIARRAS_POR_SPRINT.md` §"Catálogo Universal". **Ler antes de implementar.**

---

## Proof-of-work obrigatório (4 passos)

```bash
# PASSO 1 — snapshot ANTES
cd /home/andrefarias/Desenvolvimento/Nyx-Code
bash scripts/sprint_invariants.sh > /tmp/inv_before.txt 2>&1 || true
FAIL_BEFORE=$(grep -c "^\[FAIL\]" /tmp/inv_before.txt)
echo "FAIL inicial: $FAIL_BEFORE"

# PASSO 2 — implementação (seguir literalmente a seção "Plano de implementação")
#            + consultar dev-journey/08-templates/GAMBIARRAS_POR_SPRINT.md seção INFRA-SANITIZER-FIX-01

# PASSO 3 — snapshot DEPOIS
bash scripts/sprint_invariants.sh > /tmp/inv_after.txt 2>&1
FAIL_AFTER=$(grep -c "^\[FAIL\]" /tmp/inv_after.txt)
PASS_AFTER=$(grep -c "^\[OK\]" /tmp/inv_after.txt)
echo "PASS final: $PASS_AFTER, FAIL final: $FAIL_AFTER"

# PASSO 4 — regras binárias
#   (a) $FAIL_AFTER <= $FAIL_BEFORE   (nunca pode aumentar)
#   (b) $PASS_AFTER == 14             (invariante #14 ativo)
#   (c) ./run.sh --smoke retorna 0 e imprime 'boot ok'
#   (d) diff /tmp/inv_before.txt /tmp/inv_after.txt — colar no relatório
```

**Formato obrigatório do relatório de conclusão:**

```
### Proof-of-work

$ cat /tmp/inv_before.txt | tail -10
(saída bruta — esperado FAIL provavelmente em #1 emoji por causa do estado sanitizado, OU
 PASS pleno se invariantes #1 não cobrem glifos legítimos. Documentar literalmente.)

$ cat /tmp/inv_after.txt | tail -10
(saída bruta — esperado PASS=14, FAIL=0)

$ diff /tmp/inv_before.txt /tmp/inv_after.txt
(diff completo)

FAIL inicial: N
FAIL final:   0   (0 <= N)
PASS final:   14
Invariantes fechados por esta sprint: [#14 (novo, glifos canônicos)]

### Comando específico da sprint
$ grep -F '_STATE_GLYPHS = {"cold": "○", "warming": "◐", "warm": "●"}' nyx/cli.py
nyx/cli.py:_STATE_GLYPHS = {"cold": "○", "warming": "◐", "warm": "●"}

$ grep -cF '●' nyx/themes/design_tokens.py
4

$ grep -cF '○' nyx/themes/design_tokens.py
1

$ ./run.sh --smoke
boot ok

$ wc -l scripts/sprint_invariants.sh
<N> scripts/sprint_invariants.sh    # esperado <= 243

### Git
$ git show --stat HEAD
(resultado completo do commit técnico)

$ git log --oneline -3
(últimos 3 commits — incluir commit técnico + commit de status update se separados)
```

**Se o output acima não for colado integralmente: sprint é rejeitada.**

Se `FAIL_AFTER > FAIL_BEFORE`: regressão. Sprint deve ser revertida (`git reset --hard <hash-anterior>`) e reiniciada após correção.

---

## Gambiarras específicas desta sprint

Adicionar entrada nova em `dev-journey/08-templates/GAMBIARRAS_POR_SPRINT.md` na seção "Gambiarras específicas por sprint":

```markdown
### INFRA-SANITIZER-FIX-01 (restaurar glifos canônicos)

**Bypass típicos:**
- Tentar "consertar" via `sed`/`awk` em vez de `git checkout HEAD --` (restauração precisa ser bit-exact).
- Modificar `~/.config/zsh/scripts/universal-sanitizer.py` (escopo externo, proibido).
- Adicionar dependência (codespell, pre-commit) para "resolver" o problema.
- Criar ferramenta de sanitização própria no projeto (duplica responsabilidade).
- Modificar critérios de aceite do spec para "fazer caber" se grep retornar valor diferente.

**Comandos de detecção:**
- `git diff --name-only ~/.config/zsh/scripts/universal-sanitizer.py 2>/dev/null` deve retornar vazio.
- `grep -rE 'pre-commit|codespell|black|isort' nyx/ requirements*.txt pyproject.toml 2>/dev/null` antes/depois — diff zero.

**Invariantes fechados:** #14 (novo).
```

**Nota ao executor**: a IA executora deve adicionar essa entrada como parte do commit técnico desta sprint (mesmo commit; não precisa de commit separado).

---

## Validação humana (checklist do usuário)

Passos para o usuário confirmar que a sprint foi realmente feita — **sem abrir código**:

```bash
cd /home/andrefarias/Desenvolvimento/Nyx-Code

# 1. Ver diff do commit
git log --oneline -3
git show --stat HEAD

# 2. Working tree limpo
git diff --shortstat   # vazio

# 3. Glifos canônicos presentes em runtime
grep -F '_STATE_GLYPHS = {"cold": "○", "warming": "◐", "warm": "●"}' nyx/cli.py
# esperado: 1 linha match

# 4. Invariantes + smoke
bash scripts/sprint_invariants.sh   # PASS=14, FAIL=0
./run.sh --smoke                    # "boot ok", exit 0

# 5. Spec movido
ls dev-journey/06-sprints/concluidos/SPRINT_INFRA_SANITIZER_FIX_01.md   # existe
ls dev-journey/06-sprints/producao/SPRINT_INFRA_SANITIZER_FIX_01.md     # NÃO existe

# 6. Sanitizer global intacto (escopo externo)
git -C ~/.config/zsh log --oneline -3 -- scripts/universal-sanitizer.py 2>/dev/null || echo "fora de repo gerenciado"
# Nenhum commit recente atribuível a esta sprint
```

Se qualquer passo divergir, a sprint **não está concluída**.

---

## Riscos

| Risco | Mitigação |
|-------|-----------|
| Sanitizer global re-executar antes do commit (em hook pre-commit do shell zsh do usuário) e re-suprimir glifos | Após `git checkout HEAD --`, fazer `git add` + `git commit` **imediatamente** numa única sessão sem trocar diretório ou abrir outro shell. Se sanitizer disparar mesmo assim, commit captura o estado pré-sanitizer; verificar com `git show HEAD:nyx/cli.py | grep _STATE_GLYPHS`. |
| Sanitizer global re-executar **após** commit, sujando working tree de novo | Spec aceita working tree sujo se HEAD está limpo. Critério é `git diff HEAD` contra commit final, não working tree fluído. Documentar no `Checkpoint.md` que sanitizer global precisa ajuste. |
| Invariante #14 quebrar smoke por dependência circular (smoke chama check #13 que chama smoke) | Não há circularidade: check #14 só faz `grep`, não chama `./run.sh`. Check #13 mantém comportamento. |
| Comentários em PT-BR com acentos quebrarem em algum encoder | Arquivos Python já têm acentos em outros lugares; comentário usa UTF-8 padrão. Validador `validar-acentuacao.py` confirma. |
| `git mv` falhar por status conflicting | Executar `git mv` somente após `git diff` limpo. Se conflict, fazer `mv` + `git add` separados. |
| ID 124 no `SPRINT_ORDER_MASTER.md` colidir com outra sprint criada paralelamente | Antes de commitar, `grep '| 124 ' dev-journey/06-sprints/SPRINT_ORDER_MASTER.md` — se já existir, usar próximo livre (125+). |

---

## Não-objetivos (escopo fora da sprint — protocolo anti-débito)

- **NÃO** consertar o sanitizer global `~/.config/zsh/scripts/universal-sanitizer.py`. Escopo externo ao repo. Mensagem de commit informa o usuário; ação fica como **tarefa do usuário** (não vira sprint nova porque não é débito do projeto).
- **NÃO** auditar outros caracteres potencialmente afetados pelo sanitizer (ex.: caracteres Box Drawing `─ │ └─`). Esta sprint trata só dos 23 arquivos modificados POS-PUSH **observáveis no momento da criação** (HEAD 5bc4354). Se sanitizer voltar a disparar em outra faixa, criar sprint nova `INFRA-SANITIZER-FIX-02`.
- **NÃO** adicionar lint/hook ao projeto para detectar emoji (já existe invariante #1 no `sprint_invariants.sh`).
- **NÃO** tocar `Checkpoint.md` nem `assets/` (untracked, working state do orquestrador).

---

## Referências

- **VALIDATOR_BRIEF.md** (`/home/andrefarias/Desenvolvimento/Nyx-Code/VALIDATOR_BRIEF.md`) — contratos canônicos de runtime: `./run.sh --smoke`, `bash scripts/sprint_invariants.sh`, checks #1-13 ativos.
- **ADR-004 (Zero Emojis)** — exceção dos geometric shapes Unicode (citação literal em `SPRINT_UX_BUG_02B.md:36`).
- **ADR-005 (Anonimato)** — sem menção a IA externa em commits/código.
- **ADR-006 (PT-BR)** — acentuação obrigatória.
- **Precedente histórico**: `dev-journey/06-sprints/concluidos/SPRINT_UX_BUG_02B.md` (introduziu `_STATE_GLYPHS` com 3 glifos canônicos) e `SPRINT_UX_LAYOUT_01.md` (introduziu `BULLETS` com círculos cheios e brancos).
- **Memória usuário**: `feedback_nenhum_debito.md` — esta sprint materializa o achado colateral conforme protocolo "Nenhum débito fica para trás".

---

*"A higiene é cega quando o critério é apenas a faixa de caracteres; é precisa quando o critério é o propósito do caractere." — Anônimo*
