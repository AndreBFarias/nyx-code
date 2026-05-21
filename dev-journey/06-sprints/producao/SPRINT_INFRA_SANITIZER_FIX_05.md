## 0. SPEC (machine-readable)

```yaml
sprint:
  id: INFRA-SANITIZER-FIX-05
  title: "Endurecer check #14 com chr() para imunidade contra auto-neutralização do sanitizer"
  onda: 25
  bloco: "25.meta Anti-débito de pipeline"
  prioridade: ALTA
  tipo: Infra
  dependencias: [INFRA-SANITIZER-FIX-04]
  desbloqueia: [todas as sprints da Fase 1 em diante]

  touches:
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/scripts/sprint_invariants.sh
      reason: "Reescrever check #14 substituindo literais Unicode (●○◐) por chr(0x25CF), chr(0x25CB), chr(0x25D0); literais são vulneráveis a sanitizadores que removem em massa, chr() resiste"
      linhas_alvo: "207-275"
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/VALIDATOR_BRIEF.md
      reason: "Adicionar seção [CORE] Defesa anti-sanitizer com protocolo empírico de regressão"
      linhas_alvo: "EOF (adicionar antes do bloco final)"

  creates: []
  removes: []

  n_to_n_pairs:
    - descricao: "Os 3 codepoints canônicos (U+25CB, U+25D0, U+25CF) devem aparecer em ambos os arquivos preservados; check #14 verifica nyx/cli.py + nyx/themes/design_tokens.py + nyx/agent/output.py + nyx/agent/banner.py + nyx/agent/repl_app.py + nyx/themes/design_tokens_extended.py + scripts/sprint_invariants.sh (auto-proteção)"
      paths: [scripts/sprint_invariants.sh]

  forbidden:
    - "Reduzir cobertura de qualquer arquivo no check #14"
    - "Remover qualquer dos 3 codepoints (U+25CB, U+25D0, U+25CF) da defesa"
    - "Trocar chr() por literal Unicode em código Python ativo do check"
    - "Adicionar emoji em qualquer arquivo do projeto"
    - "Menção a Claude/Anthropic/GPT/Gemini/Copilot em comentário, log ou commit"

  tests:
    - cmd: "bash scripts/sprint_invariants.sh"
      timeout: 30
      deve_passar: true
      assert: "PASS=14, FAIL=0"
    - cmd: "./run.sh --smoke"
      timeout: 10
      deve_passar: true
      assert: "imprime exatamente 'boot ok', exit 0"
    - cmd: "python3 -c 'from pathlib import Path; src = Path(\"scripts/sprint_invariants.sh\").read_text(); assert \"chr(0x25CF)\" in src and \"chr(0x25CB)\" in src and \"chr(0x25D0)\" in src'"
      timeout: 5
      deve_passar: true
      assert: "exit 0"

  acceptance_criteria:
    - "scripts/sprint_invariants.sh check #14 usa chr(0xNNNN) em vez de literais Unicode para os 3 glifos canônicos"
    - "Comportamento funcional preservado: invariantes 14/14 PASS antes e depois"
    - "VALIDATOR_BRIEF.md ganha seção [CORE] Defesa anti-sanitizer com pelo menos 3 itens (regra, protocolo de teste, justificativa)"
    - "Smoke './run.sh --smoke' retorna 'boot ok' exit 0"
    - "Acentuação PT-BR correta no spec, código e BRIEF (validar-acentuacao.py --paths exit 0)"
    - "git status --short após commit contém apenas os 2 arquivos do escopo (sprint_invariants.sh + VALIDATOR_BRIEF.md); spec movida para concluidos/"
```

---

# Sprint INFRA-SANITIZER-FIX-05 — Endurecer check #14 com chr() para imunidade anti-sanitizer

**Status:** PENDENTE
**Data criação:** 2026-05-21
**Modelo obrigatório:** claude-opus-4-7 (executor-sprint via Agent tool)

---

## Contexto do projeto (snapshot inline)

> **ADRs relevantes:**
> - ADR-001 Local First: tudo offline.
> - ADR-004 Zero Emojis: exceção para Geometric Shapes (U+25xx) usados como UI ícones — protegidos pelo check #14.
> - ADR-005 Anonimato: zero menção a IA externa.
> - ADR-006 PT-BR acentuado.
> - ADR-013 Integração Obrigatória.
> - ADR-014 Testes via Gauntlet.
>
> **Lições absorvidas:**
> - `feedback_smoke_boot.md`: check #13 obrigatório
> - `feedback_nenhum_debito.md`: cada achado vira sprint com ID
> - `feedback_write_through_apagao.md`: cada decisão grava no doc antes de prosseguir
>
> **Estado runtime na data:** Python 3.10+, modelo qwen2.5-coder:3b padrão (ADR-031), Ollama :11435, proxy :11436. 35 tools, 66 commands, 14 services. cli.py 789L pós INFRA-CLI-SPLIT-03. Após restauração de 56 arquivos corrompidos por sanitizer histórico desconhecido em 2026-05-20 23:36, working tree clean, smoke `boot ok`, invariantes 14/14 PASS REAL.

---

## Problema

Em 2026-05-20 23:36 (data exata via mtime), 57 arquivos do working tree foram corrompidos por algum vetor não-identificável que removeu os Geometric Shapes Unicode (`●`, `○`, `◐`, `▸`, `◇`, `◆`). O check #14 do `scripts/sprint_invariants.sh` foi também corrompido — mas pior: o sanitizer NEUTRALIZOU a defesa porque ela compara literais.

Quando o sanitizer remove `chars` literais, código como:

```python
if dt.count("●") < 4 or dt.count("○") < 1:
```

vira:

```python
if dt.count("") < 4 or dt.count("") < 1:
```

E `dt.count("")` retorna `len(dt) + 1` (sempre milhares), o que faz a condição ser sempre falsa — **o check passa falsamente**. O Python `str.count("")` é semanticamente bem-definido mas armadilha aqui: contar string vazia conta separadores entre cada par de caracteres + extremidades.

A vulnerabilidade é estrutural: **qualquer ferramenta hostil que remova caracteres em massa neutraliza simultaneamente o defensor**.

## Sintoma observável

`git diff HEAD scripts/sprint_invariants.sh` em 2026-05-21 mostrou:

```diff
-if cli.count("○") < 1 or cli.count("◐") < 1 or cli.count("●") < 1:
+if cli.count("") < 1 or cli.count("") < 1 or cli.count("") < 1:
```

Esse padrão se repetiu em todas as 7 verificações do check #14 (cli.py, design_tokens.py, output.py, banner.py, repl_app.py, design_tokens_extended.py, sprint_invariants.sh auto-proteção).

Empirismo realizado em 2026-05-21:
- HEAD do design_tokens.py tem 7 glifos (●○◐)
- Aplicar sanitizer atual (mtime 2026-05-20 19:27) sobre cópia produz SHA idêntico
- Logo: sanitizer atual NÃO é o culpado, mas o check #14 vulnerável
- Vetor histórico (entre 19:27 e 23:36) usou regex bruto sem ALLOWED_GLYPHS

## Solução proposta

Reescrever as condições do check #14 usando `chr(0xNNNN)` em vez de literais Unicode. Esse padrão sobrevive a sanitizadores porque é construído em runtime a partir do codepoint numérico.

Bônus: emitir mensagens com `chr()` também, ou usar `.format()` com hex literais — qualquer ferramenta hostil teria que parsear AST Python para neutralizar, custo proibitivo.

## Arquivos alvo (paths absolutos)

### `/home/andrefarias/Desenvolvimento/Nyx-Code/scripts/sprint_invariants.sh`

Bloco Python heredoc no check #14 (linhas ~217-269 do source atual).

**Antes (vulnerável):**
```python
cli = Path("nyx/cli.py").read_text(encoding="utf-8")
if cli.count("○") < 1 or cli.count("◐") < 1 or cli.count("●") < 1:
    fails.append(
        f"nyx/cli.py: codepoints insuficientes "
        f"(cb={cli.count('○')}, d0={cli.count('◐')}, cf={cli.count('●')})"
    )
```

**Depois (resistente):**
```python
# Codepoints canônicos via chr() — resiste a sanitizers que removem literais
CB = chr(0x25CB)  # U+25CB White Circle (cold)
D0 = chr(0x25D0)  # U+25D0 Circle Half Black (warming)
CF = chr(0x25CF)  # U+25CF Black Circle (warm)

cli = Path("nyx/cli.py").read_text(encoding="utf-8")
if cli.count(CB) < 1 or cli.count(D0) < 1 or cli.count(CF) < 1:
    fails.append(
        f"nyx/cli.py: codepoints insuficientes "
        f"(cb={cli.count(CB)}, d0={cli.count(D0)}, cf={cli.count(CF)})"
    )
```

Replicar para os outros 6 arquivos verificados (design_tokens.py, output.py, banner.py, repl_app.py, design_tokens_extended.py, sprint_invariants.sh auto-proteção).

### `/home/andrefarias/Desenvolvimento/Nyx-Code/VALIDATOR_BRIEF.md`

Adicionar antes do bloco final `---` (linha 61):

```markdown
## [CORE] Defesa anti-sanitizer

Regra: qualquer defesa que verifica presença de caracteres Unicode (especialmente Geometric Shapes U+25xx) deve usar `chr(0xNNNN)` em vez de literais. Sanitizers hostis removem literais em massa e neutralizam simultaneamente o defensor.

Protocolo de regressão (rodar antes de marcar qualquer sprint que toca check #14 ou design_tokens):

# 1. Verificar que chr() está no source
python3 -c 'from pathlib import Path; src = Path("scripts/sprint_invariants.sh").read_text(); assert "chr(0x25CF)" in src and "chr(0x25CB)" in src and "chr(0x25D0)" in src'

# 2. Verificar que glifos canônicos estão presentes nos 7 arquivos protegidos
for f in nyx/cli.py nyx/themes/design_tokens.py nyx/agent/output.py nyx/agent/banner.py nyx/agent/repl_app.py nyx/themes/design_tokens_extended.py scripts/sprint_invariants.sh; do
    python3 -c "from pathlib import Path; t = Path('$f').read_text(); cb, d0, cf = chr(0x25CB), chr(0x25D0), chr(0x25CF); assert (cb in t) or (d0 in t) or (cf in t), '$f: nenhum glifo'"
done

Justificativa empírica: incidente de 2026-05-20 23:36 corrompeu 57 arquivos do Nyx-Code com vetor histórico não-identificável; check #14 passou falsamente porque count com string vazia retorna comprimento+1 do texto. INFRA-SANITIZER-FIX-05 endureceu para imunidade futura.
```

---

## Diff esperado

```
~ 2 arquivos modificados (scripts/sprint_invariants.sh, VALIDATOR_BRIEF.md)
+ ~50 linhas líquidas no scripts (3 const + 7 substituições + 1 comentário explicativo no bloco)
+ ~20 linhas no VALIDATOR_BRIEF
```

---

## Comandos de verificação (literais, copy-paste)

```bash
# 1. Smoke + invariantes pré-edit
bash scripts/sprint_invariants.sh > /tmp/inv_before_sanitizer05.txt 2>&1
grep -c "^\[FAIL\]" /tmp/inv_before_sanitizer05.txt  # 0 esperado

# 2. Implementar (Edit/Write)

# 3. Smoke + invariantes pós-edit
./run.sh --smoke
bash scripts/sprint_invariants.sh > /tmp/inv_after_sanitizer05.txt 2>&1
grep -c "^\[FAIL\]" /tmp/inv_after_sanitizer05.txt  # 0 esperado

# 4. Verificar chr() no source
python3 -c 'from pathlib import Path; src = Path("scripts/sprint_invariants.sh").read_text(); assert "chr(0x25CF)" in src and "chr(0x25CB)" in src and "chr(0x25D0)" in src, "chr() nao presente"; print("OK chr presente")'

# 5. Acentuação
python3 ~/.config/zsh/scripts/validar-acentuacao.py --paths scripts/sprint_invariants.sh VALIDATOR_BRIEF.md

# 6. Diff
diff /tmp/inv_before_sanitizer05.txt /tmp/inv_after_sanitizer05.txt
```

---

## Critério binário de aceite

- [ ] `chr(0x25CF)`, `chr(0x25CB)`, `chr(0x25D0)` presentes no Python heredoc do check #14
- [ ] Os 3 codepoints originais (literais) podem permanecer em strings de erro/comentários, mas as comparações operacionais usam `chr()`
- [ ] Invariantes 14/14 PASS antes e depois
- [ ] Smoke `boot ok` exit 0
- [ ] VALIDATOR_BRIEF.md tem seção [CORE] Defesa anti-sanitizer (mínimo 3 itens)
- [ ] `validar-acentuacao.py --paths scripts/sprint_invariants.sh VALIDATOR_BRIEF.md` exit 0
- [ ] git diff --stat HEAD: apenas 2 arquivos modificados
- [ ] SPRINT_ORDER_MASTER.md ganha linha 125kk para esta sprint
- [ ] Sprint movida de `producao/` para `concluidos/` após validação

---

## Guardrails anti-engodo

Executor-sprint NÃO pode marcar concluída se:
- `chr()` aparece só em comentários, não nas comparações operacionais
- VALIDATOR_BRIEF tem só placeholder sem conteúdo
- `validar-acentuacao.py` reclama
- Algum invariante regrediu (FAIL_AFTER > FAIL_BEFORE)
- Tocou arquivo fora do escopo (`forbidden[]`)

Se algum desses, reportar BLOQUEADA com motivo objetivo.

---

## Proof-of-work obrigatório

```bash
# Snapshot BEFORE
bash scripts/sprint_invariants.sh > /tmp/inv_before.txt 2>&1
FAIL_BEFORE=$(grep -c "^\[FAIL\]" /tmp/inv_before.txt)
echo "FAIL inicial: $FAIL_BEFORE"

# IMPLEMENTAR (Edit dos 2 arquivos)

# Snapshot AFTER
bash scripts/sprint_invariants.sh > /tmp/inv_after.txt 2>&1
FAIL_AFTER=$(grep -c "^\[FAIL\]" /tmp/inv_after.txt)
echo "FAIL final: $FAIL_AFTER"

# Regra binária
[ "$FAIL_AFTER" -le "$FAIL_BEFORE" ] || { echo "REGRESSAO"; exit 1; }

# Asserto da spec
python3 -c 'from pathlib import Path; src = Path("scripts/sprint_invariants.sh").read_text(); assert "chr(0x25CF)" in src and "chr(0x25CB)" in src and "chr(0x25D0)" in src, "chr nao presente"; print("OK chr presente")'

# Acentuação
python3 ~/.config/zsh/scripts/validar-acentuacao.py --paths scripts/sprint_invariants.sh VALIDATOR_BRIEF.md
```

Formato de relatório esperado pelo validador-sprint:
```
### Proof-of-work
FAIL inicial: 0
FAIL final:   0

### chr() asserto
OK chr presente

### Acentuação
exit 0

### Git
$ git show --stat HEAD
 scripts/sprint_invariants.sh | XX +-
 VALIDATOR_BRIEF.md          | XX +-
```

---

## Gambiarras específicas desta sprint

- **Anti-padrão #11 (noqa indiscriminado):** se ruff reclamar de `chr(0xNNNN)`, NÃO adicionar `# noqa` sem especificar regra. O padrão é PEP-friendly.
- **Anti-padrão #6 (modificar teste em vez de código):** se a contagem de algum arquivo for menor que o esperado, é porque o arquivo foi mutilado — NÃO baixar o threshold, restaurar o arquivo.
- **Anti-padrão #20 (checkpoint marcado sem verificar):** executor DEVE colar saída literal de `bash scripts/sprint_invariants.sh` antes e depois, não dizer "passou".

---

## Validação humana (checklist)

```bash
cd /home/andrefarias/Desenvolvimento/Nyx-Code

# 1. Ver diff
git log --oneline -1
git show --stat HEAD

# 2. Confirmar resistência
python3 -c 'from pathlib import Path; src = Path("scripts/sprint_invariants.sh").read_text(); assert "chr(0x25CF)" in src and "chr(0x25CB)" in src and "chr(0x25D0)" in src; print("OK")'

# 3. Spec migrou
ls dev-journey/06-sprints/concluidos/SPRINT_INFRA_SANITIZER_FIX_05.md   # deve existir
ls dev-journey/06-sprints/producao/SPRINT_INFRA_SANITIZER_FIX_05.md     # NAO deve existir
```

---

## Riscos

| Risco | Mitigação |
|---|---|
| `chr(0x25CF)` ser parseado de forma diferente em Python 3.10 vs 3.12 | Testado: `chr()` é estável desde Python 3.0; sem ambiguidade |
| Reescrita quebrar acentuação PT-BR em comentários | `validar-acentuacao.py --paths` no acceptance |
| Heredoc com `chr()` ser difícil de ler vs literal | Adicionar comentário inline explicando: White/Half/Black circles |

---

*"O defensor que precisa do agressor para existir já perdeu." — princípio de resiliência*
