## 0. SPEC (machine-readable)

```yaml
sprint:
  id: PATCH-HUNK-OFFSET-HONEST-01
  numero: 424
  title: "patch honra o offset do hunk (@@) ou falha honesto -- fim da corrupção silenciosa com success=True"
  onda: 48
  prioridade: ALTA
  tipo: Bugfix
  dependencias: []
  desbloqueia: []
  absorve: []

  touches:
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/agent/tools/patch_tool.py
      reason: "parsear o cabeçalho @@ -a,b +c,d @@ e localizar o hunk pela pre-imagem (contexto + remoções); aplicar na posição correta; FALHAR com erro claro quando o hunk não casa, em vez de inserir deslocado e retornar success=True"
      linhas_alvo: "59-90 (bloco try do execute: loop de aplicação e o return de sucesso)"
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/scripts/gauntlet/nyx_gauntlet.py
      reason: "endurecer P8E-02 (hoje só assere presença da linha adicionada, mascara a corrupção) e adicionar P8E-02b: hunk com offset @@ aplica no lugar certo, e hunk que não casa retorna success=False honesto"
      linhas_alvo: "3685-3699 (bloco P8E-02)"
  creates: []
  removes: []

  forbidden:
    - "Adicionar emoji"
    - "Usar 'print()' fora de cli.py/output.py"
    - "Mencao a IA proprietaria"
    - "Delegar para patch(1) do sistema ou exigir unified-diff bem-formado: o 3b emite diffs informais (sem ---/+++/@@) e o gauntlet P8E-02 usa '-linha2\\n+linha2_editada' sem cabeçalho -- a tool tem de continuar aplicando esse caso, agora corretamente"
    - "Alterar a assinatura da tool (ToolDef name/parameters/required) nem o ActionType.EDIT_FILE"
    - "Tocar edit_file.py, multi_edit.py, write_file.py, parser.py, validator.py ou registry.py"
    - "Mudar o happy-path a ponto de um patch que HOJE aplica certo passar a falhar sem motivo (ver Riscos: fallback de busca quando não ha @@)"

  tests:
    - cmd: "/home/andrefarias/.local/bin/ruff check nyx/agent/tools/patch_tool.py"
      deve_passar: true
    - cmd: "python3 ~/.config/zsh/scripts/validar-acentuacao.py --paths nyx/agent/tools/patch_tool.py"
      deve_passar: true
    - cmd: "bash scripts/sprint_invariants.sh"
      deve_passar: true
    - cmd: "./run.sh --gauntlet --only rapido"
      timeout: 300
      deve_passar: true
      nota: "DEFERIDO para GPU exclusiva; a prova unitaria da tool (passo 3) roda AGORA sem GPU"

  acceptance_criteria:
    - "AC1: quando o patch traz cabeçalho @@ -a,b +c,d @@, o cursor parte de a-1 (0-based) e NÃO de 0; um diff valido visando a linha 50 e aplicado na linha 50, não no topo do arquivo"
    - "AC2: cada linha de contexto (' ') e de remoção ('-') e validada contra o arquivo; a pre-imagem do hunk (contexto + remoções, na ordem) tem de casar consecutivamente antes de aplicar"
    - "AC3: quando a pre-imagem do hunk NÃO casa em lugar nenhum (ou casa de forma ambigua), a tool retorna success=False com mensagem honesta citando a linha-alvo e instruindo o modelo a reler com read_file e regerar o diff, ou usar edit_file -- NUNCA aplica deslocado com success=True"
    - "AC4: patch sem cabeçalho @@ (caso do gauntlet: '-linha2\\n+linha2_editada') continua funcionando, agora corretamente -- localiza a pre-imagem pela busca e remove de fato linha2 (não deixa linha2 orfã ao lado de linha2_editada)"
    - "AC5: gauntlet P8E-02 endurecido: assere que a linha removida SUMIU do conteudo (não só que a adicionada apareceu); P8E-02b novo cobre offset correto e falha honesta em mismatch"
    - "AC6: ruff limpo, acentuação rc=0, invariantes FAIL_AFTER <= FAIL_BEFORE, prova unitaria da tool colada (passo 3), smoke boot ok"
```

---

# Sprint PATCH-HUNK-OFFSET-HONEST-01 — patch honra o offset do hunk ou falha honesto

**Status:** PENDENTE
**Data criação:** 2026-07-12
**Modelo obrigatório:** claude-opus-4-7 (executor-sprint autorizado pelo dono nesta onda)

---

## Contexto do projeto (snapshot — não referência)

> **Missão (calibra a severidade):** o Nyx-Code faz o pior LLM local (qwen 3b) na pior máquina possível parecer o Claude Code offline. Robustez pertence a INFRA, não ao modelo (ADR-032/033/034). O usuário-alvo e leigo e sem hardware bom. Uma tool que corrompe o arquivo do usuário e ainda diz "sucesso" e a pior classe de falha possível neste projeto: engana o modelo (que sela com done()) e engana o humano. <!-- noqa-anonimato -->
>
> **ADRs relevantes (inline):**
> - **ADR-032/033 A INFRA CARREGA O MODELO / ENFORCEMENT, NÃO CONFIANÇA:** quando a infra não consegue garantir o resultado, a mensagem ao usuário e clara ("não consegui X porque Y"), nunca um sucesso fabricado. Rejeitar honesto e melhor que aplicar deslocado.
> - **DESENHO_CONTRATO_EXECUCAO.md §6, "Honestidade na falha":** "Se a infra não consegue garantir, a mensagem ao usuário e clara -- nunca um sucesso fabricado nem um formato interno cru." <!-- noqa-acento -->
>
> **Estado (2026-07-12):** `qwen2.5-coder:3b`. Achado da auditoria de prontidão 2026-07-12 (verificado adversarialmente, evidência file:line). Tool afetada: `nyx/agent/tools/patch_tool.py` (registrada em `registry.py:25`, mapeada em `parser.py:70-72` para `ActionType.PATCH`, considerada tool de escrita em `validator.py:30`).

---

## Problema

**Achado (auditoria de prontidão 2026-07-12, severidade ALTA):** a tool `patch` ignora os offsets dos hunks (`@@`) e aplica inserções na posição errada reportando sucesso.

**Causa-raiz (verificada no código real — evidência confere linha a linha):** `nyx/agent/tools/patch_tool.py`, método `execute`:

- **linha 60:** `line_idx = 0` — o cursor sempre parte do topo do arquivo.
- **linha 62-63:** `if pline.startswith("---") or pline.startswith("+++") or pline.startswith("@@"): continue` — o cabeçalho do hunk, que carrega a linha-alvo (ex.: `@@ -50,3 +50,4 @@`), e simplesmente descartado. A informação de posição vai para o lixo.
- **linha 64-70:** uma linha de remoção (`-`) só remove se casar com `result_lines[line_idx]`; se NÃO casa, o codigo apenas faz `line_idx += 1` (linha 70) e segue — sem erro, sem aviso.
- **linha 71-75:** uma linha de adição (`+`) faz `result_lines.insert(line_idx, content)` na posição corrente — que, por causa do topo forçado, quase nunca e a posição pretendida.
- **linha 76-77:** linhas de contexto (' ') só fazem `line_idx += 1`, sem verificar se de fato casam com o arquivo.
- **linha 83-86:** independentemente de o hunk ter casado ou não, a tool retorna `success=True` com `output=f"Patch aplicado: {file_path} (+{additions} -{removals} linhas)"`.

**Efeito prático:** um diff valido visando a linha 50 e aplicado no topo do arquivo; a tool retorna sucesso. O arquivo do usuário fica corrompido, o 3b acredita que editou certo, o `done()` sela a alucinação. Pior que rejeitar: engana modelo e humano ao mesmo tempo.

**Prova adversarial do próprio gauntlet (evidência de que a fachada de sucesso já engana o teste):** `scripts/gauntlet/nyx_gauntlet.py:3690-3695` roda `patch = "-linha2\n+linha2_editada"` sobre `linha1\nlinha2\nlinha3\n`. Sem cabeçalho `@@`, `line_idx=0`; `-linha2` não casa com `result_lines[0]="linha1"`, então `line_idx` vira 1; `+linha2_editada` insere no indice 1. Resultado real: `linha1\nlinha2_editada\nlinha2\nlinha3\n` — a `linha2` NUNCA foi removida. O teste assere apenas `"linha2_editada" in content` (linha 3695), então PASSA apesar da corrupção. O teste atual e cego para o bug.

---

## Divergência do briefing (registrada por exigência do protocolo)

O briefing sugere como alternativa mínima "delegar para `patch(1)`/difflib com verificação estrita". A investigação no código real mostra que essa alternativa QUEBRA dois consumidores legitimos:

1. O gauntlet P8E-02 usa um "diff" informal (`-linha2\n+linha2_editada`, sem `---`/`+++`/`@@`). O `patch(1)` do sistema rejeita entrada mal-formada — o caso deixaria de aplicar.
2. O 3b (modelo-alvo) frequentemente emite diffs informais sem cabeçalho completo. Exigir unified-diff bem-formado transferiria a robustez de volta para o modelo, o oposto do ADR-032/033.

Por isso esta sprint adota a correção **pura-Python com localização estrita da pre-imagem**: honra o `@@` quando existe, e quando não existe faz busca da pre-imagem no arquivo — aplicando certo ou falhando honesto, sem depender de `patch(1)`. O `difflib` do stdlib não aplica patches (só gera/compara), então também não serve como aplicador. Nenhuma outra divergência de evidência: as linhas 60-77 e 85 do briefing conferem exatamente com o código atual.

---

## Solução proposta

Reescrever apenas o miolo de aplicação dentro do `try:` de `execute` (linhas 59-87), mantendo intactos: assinatura da tool, validação de path, leitura do arquivo (44-53) e a estrutura de `ActionResult`. O algoritmo passa a ser orientado a hunks, com localização estrita:

1. **Segmentar o patch em hunks.** Um hunk começa num cabeçalho `@@ -a,b +c,d @@` (quando presente) ou, na ausência de qualquer `@@`, o patch inteiro e tratado como um único hunk sem posição declarada. Linhas `---`/`+++` continuam ignoradas.
2. **Montar a pre-imagem do hunk** = concatenação, na ordem, das linhas de contexto (' ') e de remoção ('-'), com o prefixo removido. Essa e a sequência que TEM de existir no arquivo para o hunk casar.
3. **Localizar a pre-imagem** em `result_lines` (comparação por `rstrip()`, como o codigo atual já faz na linha 66):
   - Se ha cabeçalho `@@ -a,...`, tentar primeiro na posição `a-1` (0-based).
   - Se não casa ali, ou não ha cabeçalho, buscar uma ocorrência da pre-imagem no arquivo inteiro.
   - Se ha exatamente uma ocorrência: aplicar ali. Se ha zero: **falhar honesto**. Se ha mais de uma (ambiguo) e sem `@@` para desempatar: **falhar honesto** pedindo mais contexto.
4. **Aplicar o hunk** na posição encontrada: reconstruir o bloco a partir do corpo do hunk (' ' mantem, '-' descarta, '+' insere) e substituir `result_lines[pos : pos+len(pre_imagem)]` pelo bloco reconstruido. Atualizar `additions`/`removals`.
5. **Falha honesta** (quando qualquer hunk não casa): `return ActionResult(success=False, error=...)` com mensagem que cita a linha-alvo declarada e instrui o modelo:
   `"hunk não casa no arquivo (alvo ~linha {n}). Releia o arquivo com read_file e gere o diff de novo, ou use edit_file com o trecho exato."`
6. Só retorna `success=True` (linha 83-86 atual) se TODOS os hunks casaram e foram aplicados.

Empates entre hunks múltiplos aplicados em sequência: aplicar da posição maior para a menor, ou reindexar após cada hunk, para que a inserção de um hunk anterior não desloque a busca do seguinte. O executor escolhe a implementação; a invariante e: cada hunk casa contra o estado corrente de `result_lines`.

---

## Arquivos alvo (paths absolutos)

### `/home/andrefarias/Desenvolvimento/Nyx-Code/nyx/agent/tools/patch_tool.py`

Reescrever o bloco `try:` de aplicação (linhas 59-90). Referência de implementação (o executor pode ajustar, desde que os ACs fechem):

```python
        import re

        result_lines = list(original_lines)
        additions = 0
        removals = 0

        # PATCH-HUNK-OFFSET-HONEST-01: segmenta o patch em hunks. O cabeçalho
        # @@ -a,b +c,d @@ carrega a linha-alvo; ignora-lo (comportamento antigo)
        # aplicava tudo no topo e retornava success=True -> corrupção silenciosa.
        hunk_header = re.compile(r"^@@ -(\d+)(?:,\d+)? \+(\d+)(?:,\d+)? @@")
        hunks: list[dict[str, Any]] = []
        current: dict[str, Any] | None = None
        for pline in patch_lines:
            if pline.startswith("---") or pline.startswith("+++"):
                continue
            m = hunk_header.match(pline)
            if m:
                current = {"start": int(m.group(1)) - 1, "body": []}
                hunks.append(current)
                continue
            if current is None:
                current = {"start": None, "body": []}
                hunks.append(current)
            if pline.startswith(("-", "+", " ")) or not pline.strip():
                current["body"].append(pline)

        def _locate(lines: list[str], pre: list[str], hint: int | None) -> int | None:
            if not pre:
                return hint if hint is not None else 0
            n = len(pre)
            def _match(i: int) -> bool:
                return i >= 0 and i + n <= len(lines) and all(
                    lines[i + k].rstrip() == pre[k].rstrip() for k in range(n)
                )
            if hint is not None and _match(hint):
                return hint
            found = [i for i in range(len(lines) - n + 1) if _match(i)]
            if len(found) == 1:
                return found[0]
            return None  # zero ou ambiguo -> falha honesta

        for hunk in hunks:
            body = hunk["body"]
            pre = [ln[1:] for ln in body if ln.startswith((" ", "-")) or not ln.strip()]
            pos = _locate(result_lines, pre, hunk["start"])
            if pos is None:
                alvo = (hunk["start"] + 1) if hunk["start"] is not None else "?"
                return ActionResult(
                    success=False,
                    error=(
                        f"hunk não casa no arquivo (alvo ~linha {alvo}). "
                        "Releia o arquivo com read_file e gere o diff de novo, "
                        "ou use edit_file com o trecho exato."
                    ),
                )
            rebuilt: list[str] = []
            for ln in body:
                if ln.startswith("+"):
                    rebuilt.append(ln[1:])
                    additions += 1
                elif ln.startswith("-"):
                    removals += 1
                else:
                    rebuilt.append(ln[1:] if ln.startswith(" ") else ln)
            result_lines[pos : pos + len(pre)] = rebuilt

        new_content = "\n".join(result_lines)
        path.write_text(new_content, encoding="utf-8")
        logger.info("Patch aplicado: %s (+%d -%d)", file_path, additions, removals)
        return ActionResult(
            success=True,
            output=f"Patch aplicado: {file_path} (+{additions} -{removals} linhas)",
            files_modified=[str(path)],
        )
```

> Nota de implementação: `import re` pode subir para o topo do modulo. O `except Exception` externo (linha 89-90) e mantido como rede de seguranca. A comparação por `rstrip()` preserva o comportamento tolerante a espaço-em-branco final que o codigo atual já tinha (linha 66).

### `/home/andrefarias/Desenvolvimento/Nyx-Code/scripts/gauntlet/nyx_gauntlet.py`

Endurecer o P8E-02 (linhas 3685-3699) e adicionar P8E-02b. O teste atual e cego para o bug (assere só a presença da linha adicionada). Novo contrato:

- P8E-02: patch sem cabeçalho aplica e a linha removida SOME. Assere `"linha2_editada" in content and "\nlinha2\n" not in content` (linha2 orfã não pode sobrar).
- P8E-02b: patch com cabeçalho `@@` visando uma linha no meio de um arquivo maior aplica NO LUGAR CERTO; e um hunk cuja pre-imagem não existe retorna `success=False` (falha honesta), sem escrever nada.

---

## Diff esperado (resumo)

```
~ 2 arquivos modificados (nyx/agent/tools/patch_tool.py, scripts/gauntlet/nyx_gauntlet.py)
patch_tool.py: reescrita do miolo de aplicação (~30 linhas antigas -> ~55 linhas)
nyx_gauntlet.py: P8E-02 endurecido + P8E-02b novo (~20 linhas)
```

Sem aritmética de extração: esta sprint não tem meta `arquivo < NNNL`. `patch_tool.py` segue muito abaixo de qualquer teto (arquivo pequeno, < 150L após a mudança).

---

## Comandos de verificação (literais, copy-paste)

```bash
cd /home/andrefarias/Desenvolvimento/Nyx-Code

# 1. Estatica + acentuacao (ruff via binario direto -- não ha modulo ruff no venv, ver BRIEF)
/home/andrefarias/.local/bin/ruff check nyx/agent/tools/patch_tool.py scripts/gauntlet/nyx_gauntlet.py
python3 ~/.config/zsh/scripts/validar-acentuacao.py --paths nyx/agent/tools/patch_tool.py

# 2. Confirmar as ancoras (linhas podem ter deslizado -- reconferir):
rg -n "line_idx = 0|startswith\(\"@@\"\)|Patch aplicado|success=True" nyx/agent/tools/patch_tool.py

# 3. PROVA UNITARIA RUNTIME-REAL (SEM GPU, SEM Ollama -- a tool e pura-Python):
./venv/bin/python - <<'PY'
import tempfile, os
from nyx.agent.tools.patch_tool import PatchTool

pt = PatchTool()
root = tempfile.mkdtemp()

# (a) offset honrado: diff visando o meio do arquivo aplica no lugar certo
f = os.path.join(root, "a.txt")
open(f, "w").write("\n".join(f"linha{i}" for i in range(1, 11)) + "\n")
patch = "@@ -5,1 +5,2 @@\n linha5\n+INSERIDA\n"
r = pt.execute({"file_path": f, "patch": patch}, root)
out = open(f).read().split("\n")
assert r.success, r.error
assert out[4] == "linha5" and out[5] == "INSERIDA", out  # inserida DEPOIS da linha5, não no topo
assert out[0] == "linha1", out                            # topo intacto
print("(a) OK: offset @@ honrado, inserção na linha certa")

# (b) falha honesta: hunk que não casa NÃO aplica e retorna success=False
f2 = os.path.join(root, "b.txt")
open(f2, "w").write("alpha\nbeta\ngamma\n")
before = open(f2).read()
r2 = pt.execute({"file_path": f2, "patch": "@@ -1,1 +1,1 @@\n-INEXISTENTE\n+X\n"}, root)
assert not r2.success, "deveria falhar honesto"
assert "read_file" in r2.error or "edit_file" in r2.error, r2.error
assert open(f2).read() == before, "arquivo NÃO pode ter sido tocado no mismatch"
print("(b) OK: mismatch -> success=False honesto, arquivo intacto")

# (c) compat: patch informal sem @@ (caso do gauntlet) aplica e REMOVE de fato
f3 = os.path.join(root, "c.txt")
open(f3, "w").write("linha1\nlinha2\nlinha3\n")
r3 = pt.execute({"file_path": f3, "patch": "-linha2\n+linha2_editada"}, root)
c = open(f3).read()
assert r3.success, r3.error
assert "linha2_editada" in c and "\nlinha2\n" not in c, c  # linha2 removida, não orfã
print("(c) OK: patch informal aplica e remove de verdade")

print("PROVA COMPLETA: offset honrado, falha honesta, compat preservada")
PY

# 4. Invariantes (14 checks)
bash scripts/sprint_invariants.sh

# 5. Smoke boot
./run.sh --smoke   # deve imprimir "boot ok"

# 6. Gauntlet rapido (inclui P8E-02/P8E-02b) -- DEFERIDO para GPU exclusiva
./run.sh --gauntlet --only rapido
```

> Nota GPU: o passo 3 (prova unitaria da tool) roda AGORA, sem Ollama/GPU — a `PatchTool` e pura-Python e não toca o proxy nem o modelo. O passo 6 (gauntlet completo) exige GPU exclusiva; executar só quando `pgrep -af "Luna.*driver|valida_sprint"` estiver vazio (protocolo anti-contenção do BRIEF). Marcado **DEFERIDO para GPU exclusiva**, como as specs 403/407.

---

## Critério binário de aceite (IA executora)

- [ ] AC1: cabeçalho `@@ -a,...` posiciona o cursor em `a-1`; prova (a) passa (inserção na linha 5, topo intacto)
- [ ] AC2: pre-imagem (contexto + remoções) validada antes de aplicar
- [ ] AC3: mismatch retorna `success=False` com mensagem citando a linha-alvo e `read_file`/`edit_file`; arquivo NÃO tocado; prova (b) passa
- [ ] AC4: patch informal sem `@@` aplica e remove de verdade; prova (c) passa (linha2 não fica orfã)
- [ ] AC5: gauntlet P8E-02 endurecido (assere remoção) + P8E-02b novo (offset + falha honesta)
- [ ] AC6: `ruff` limpo, acentuação rc=0, `FAIL_AFTER <= FAIL_BEFORE`, prova unitaria (passo 3) colada, smoke boot ok
- [ ] `SPRINT_ORDER_MASTER.md` marca 424 CONCLUIDA; spec movida para `concluidos/` (pelo orquestrador)
- [ ] NÃO commitar; NÃO tocar Checkpoint.md; NÃO tocar edit_file/multi_edit/parser/validator/registry

---

## Guardrails anti-engodo (obrigatórios)

NÃO marcar concluída se:
- Um hunk que não casa ainda resulta em `success=True` (o núcleo do fix e falhar honesto no mismatch).
- O cursor ainda parte de 0 ignorando o `@@` (prova (a) tem de mostrar inserção na linha 5, não no topo).
- O arquivo foi escrito mesmo com hunk que não casa (prova (b): conteudo byte-identico ao original no mismatch).
- O patch informal sem `@@` parou de aplicar (regressão que quebraria o 3b e o gauntlet — prova (c)).
- A prova unitaria do passo 3 não foi colada, ou alguma das asserções (a)/(b)/(c) falha.
- Tocou edit_file/multi_edit/parser/validator/registry (fora de escopo).

Se algo falhar: `[SPRINT 424] BLOQUEADA: <motivo 1 linha>`.

---

## Proof-of-work esperado (colar no relato)

```bash
bash scripts/sprint_invariants.sh > /tmp/inv_before.txt 2>&1
FAIL_BEFORE=$(grep -c "^\[FAIL\]" /tmp/inv_before.txt)
# implementar
bash scripts/sprint_invariants.sh > /tmp/inv_after.txt 2>&1
FAIL_AFTER=$(grep -c "^\[FAIL\]" /tmp/inv_after.txt)
diff /tmp/inv_before.txt /tmp/inv_after.txt
```
Baseline esperado: `FAIL_BEFORE = 0`, `FAIL_AFTER <= 0`. Colar: inv_before/inv_after (tail), diff, o output da prova unitaria (passo 3, as três asserções (a)/(b)/(c) verdes), o `rg` do passo 2, `git --no-pager diff --stat`, `./run.sh --smoke` (`boot ok`). Gauntlet `--only rapido` 100% quando a GPU liberar (DEFERIDO).

---

## Gambiarras específicas desta sprint

- **Comparação por `rstrip()`:** preserva a tolerância a espaço-em-branco final que o codigo atual já tinha (linha 66); evita falso-mismatch por `\r`/espaços à direita que o 3b costuma emitir.
- **Regex do cabeçalho aceita `@@ -a @@` e `@@ -a,b @@`:** os contadores `,b`/`,d` são opcionais no padrão; o 3b as vezes omite. Só o número da linha-alvo (`a`) importa para posicionar.
- **Ambiguidade sem `@@`:** quando a pre-imagem casa em mais de um ponto e não ha cabeçalho para desempatar, falhar honesto pedindo mais contexto e mais seguro que adivinhar — mesma filosofia do `edit_file` (`edit_file.py:46-47`, "Trecho encontrado N vezes. Forneça mais contexto.").
- **Ordem de aplicação de hunks múltiplos:** cada hunk casa contra o estado corrente de `result_lines`; aplicar em ordem e reindexar (ou aplicar do fim para o começo) evita que a inserção de um hunk desloque a busca do próximo.

---

## Riscos e não-objetivos

| Risco / não-objetivo | Decisão |
|-------|-----------|
| Suporte a fuzz/offset-slack estilo `patch(1)` (aplicar com deslocamento de N linhas quando o contexto casa aproximado) | **NÃO-OBJETIVO.** Localização exata da pre-imagem basta e e mais segura para o usuário-alvo. Se surgir demanda, sprint própria `INFRA-PATCH-FUZZ-01` (anti-débito: `feedback_nenhum_debito`). |
| Reescrever `patch` para delegar a `patch(1)` do sistema | Rejeitado na seção Divergência: quebraria diffs informais do 3b e o gauntlet. |
| Unificar `patch`/`edit_file`/`multi_edit` num aplicador comum | Fora de escopo — refatoração arquitetural, não fix do achado. |
| Patch informal ambiguo (pre-imagem em vários pontos, sem `@@`) hoje aplicava no topo | Agora falha honesto pedindo contexto — mudança de comportamento intencional e desejada (era corrupção silenciosa). |

---

## Fora de escopo (anti-débito)

Nenhum achado secundário de mecanismo distinto neste briefing — ele traz um único achado (offset ignorado + sucesso mentiroso), coberto integralmente pelos ACs acima. Se durante a execução aparecer corrupção análoga em `multi_edit.py` (que também aplica edições em lote), registrar sprint própria, não absorver aqui.

---

## Referências

- BRIEF: `/home/andrefarias/Desenvolvimento/Nyx-Code/VALIDATOR_BRIEF.md`
- Origem: auditoria de prontidão 2026-07-12, relatório durável `dev-journey/07-reports/AUDIT_2026_07_12.md` §3 (briefing efêmero da sessão de auditoria)
- Desenho do contrato: `dev-journey/02-architecture/DESENHO_CONTRATO_EXECUCAO.md` (§6, "Honestidade na falha")
- Evidência primaria: `nyx/agent/tools/patch_tool.py:60-77,85`
- Prova adversarial (teste cego): `scripts/gauntlet/nyx_gauntlet.py:3690-3695`
- Precedente de falha honesta em tool de edição: `nyx/agent/tools/edit_file.py:42-47`
- Precedente de estrutura: `SPRINT_EXEC_CONTRACT_PROXY_STATUS_BEFORE_JSON_01.md` (satelite de honestidade na falha)

---

*"Rejeitar honesto vale mais que aplicar deslocado: um patch no lugar errado com carimbo de sucesso engana o modelo e o humano de uma vez." -- princípio de execução (DESENHO_CONTRATO_EXECUCAO.md §6)* <!-- noqa-acento -->
