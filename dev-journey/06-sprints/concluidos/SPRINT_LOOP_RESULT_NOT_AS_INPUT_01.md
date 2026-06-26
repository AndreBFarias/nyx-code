## 0. SPEC (machine-readable)

```yaml
sprint:
  id: LOOP-RESULT-NOT-AS-INPUT-01
  title: "Contrato G3: nunca usar o resultado de uma tool como entrada da proxima (quebra a recursao)"
  onda: 48
  prioridade: ALTA
  tipo: Feature
  dependencias: [EXEC-CONTRACT-NO-HALLUCINATED-RESULT-01, EXEC-CONTRACT-TOOLCALL-SANITIZE-01]
  desbloqueia: [EXEC-CONTRACT-TOOL-MATCH-01]

  touches:
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/agent/sanitize.py
      reason: "adicionar strip_result_echo puro -- remove de um arg o eco de um resultado recente de tool"
      linhas_alvo: "fim do arquivo (apos sanitize_tool_args)"
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/agent/loop/_iteration.py
      reason: "rastrear _recent_tool_outputs por turno + aplicar strip_result_echo antes de executar nos 2 caminhos"
      linhas_alvo: "_execute_tool_calls (apos sanitize_tool_args + apos execução); _execute_parsed_action (idem)"
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/agent/loop/_core.py
      reason: "resetar _recent_tool_outputs por turno em run()"
      linhas_alvo: "junto do reset de _turn_presentables"
  creates: []
  removes: []

  n_to_n_pairs:
    - descrição: "strip_result_echo + append de _recent_tool_outputs existem nos DOIS caminhos de execução -- atualizar ambos"  # noqa-acento
      paths: [_execute_tool_calls, _execute_parsed_action]

  forbidden:
    - "Adicionar emoji"
    - "Usar 'print()' fora de cli.py/output.py"
    - "Mencao a IA proprietaria"
    - "Detectar eco SEM amarrar ao output recente real (marker-only puro gera falso-positivo em conteudo que cite 'Exit code:' etc.)"
    - "Stripar content/command/pattern legitimo (copia de A para B não e eco -- so e eco se a linha veio de um resultado RECENTE da sessão)"
    - "Tocar a apresentacao da 399, o sanitize_tool_args da 397, gating, write_memory, cascata OOM"

  tests:
    - cmd: "./run.sh --gauntlet --only rapido"
      timeout: 300
      deve_passar: true
    - cmd: "./run.sh --gauntlet --only contexto"
      timeout: 300
      deve_passar: true

  acceptance_criteria:
    - "Um arg content/new_string que ecoa linhas de um resultado recente de tool tem essas linhas removidas antes de executar (V06)"
    - "Um arg pattern/command que vira o eco de um erro recente (ex.: 'regex invalido...') e rejeitado + re-emite hint (C2)"
    - "Conteudo legitimo (copia de A->B, ou texto que cite 'Exit code:' sem ter vindo de um resultado recente) não e alterado"
    - "Rastreio _recent_tool_outputs resetado por turno; alimentado nos 2 caminhos"
    - "Proof runtime: listar ~/Desktop não polui mais o Resultado: com 'Nenhum resultado para: regex invalido...' (C2 morto)"
    - "Gauntlet rapido E contexto 100%"
```

---

# Sprint LOOP-RESULT-NOT-AS-INPUT-01 — Contrato G3: anti-recursao

**Status:** PENDENTE
**Data criação:** 2026-06-26
**Modelo obrigatório:** claude-opus-4-7 (executor-sprint autorizado pelo dono nesta onda)

---

## Contexto do projeto (snapshot — não referência)

> **ADRs relevantes (inline):**
> - **ADR-032 A INFRA CARREGA O MODELO:** as strings de controle que a infra injeta nos resultados (`OK: ...`, `chame done()`, `regex inválido`, `[stderr]`) nunca deveriam voltar como ENTRADA do modelo. Quando voltam, a infra corta o ciclo.
> - **ADR-033 A CADEIA NUNCA QUEBRA.** ADR-009, ADR-001, ADR-006, ADR-005, ADR-024, ADR-014, ADR-010.
>
> **Estado (2026-06-26):** `qwen2.5-coder:3b`, Ollama :11435, proxy :11436. ONDA-48 fase raiz: 399 (esqueleto) `f0883a1`, 397 (sanitize args) `6c61f1d` CONCLUIDAS. Desenho: `dev-journey/02-architecture/DESENHO_CONTRATO_EXECUCAO.md` (G3, ponto B). Achados: `dev-journey/07-reports/AUDIT_VALIDACAO_2026_06_26.md` (V06) + C2 (validação as-user da 399).

---

## Problema

**Achado V06 LOOP-RESULT-AS-CONTENT [ALTA]** + **C2** (reproduzido na validação as-user da 399):
- V06: o loop realimenta o **resultado** de uma tool como **conteúdo** da próxima: `write_file(content="...validado pela onda\n[resultado de write_file]\nOK: Arquivo criado... chame done().")` -- o modelo copiou a saída do write anterior (com os markers de controle da infra) para dentro do content do próximo write.
- C2 (validação 399, turno listar `~/Desktop`): a mensagem de erro de uma busca virou o **pattern** da busca seguinte -- `search('regex inválido: nothing to repeat at position 0')` -- e a linha `Nenhum resultado para: regex inválido...` LEAKOU para o `Resultado:` apresentado, poluindo justamente o ganho da 399.

**Causa-raiz:** o resultado de uma tool entra no contexto (`_iteration.py` ~349-360); o 3b, no turno seguinte, reusa esse texto como arg da próxima tool. A infra não detecta nem corta o eco. As strings de controle que a PRÓPRIA infra injeta (`OK:`, `chame done()`, `regex inválido`, `[stderr]`, `Exit code:`, `[resultado de ...]`) aparecendo num arg de ENTRADA são a assinatura estrutural do eco.

---

## Solução proposta

**G3 (ponto B), determinístico e amarrado ao output real (zero falso-positivo):**
1. Rastrear `self._recent_tool_outputs` -- as últimas N (3) saídas de tool bem-sucedidas do turno.
2. Antes de executar, `strip_result_echo(name, args, recent_outputs)`: para args que carregam texto (`content`, `new_string`, `command`, `pattern`), remover as **linhas** do arg que (a) aparecem num output recente E (b) carregam um marker de controle da infra OU são uma linha substancial (>=30 chars) idêntica a uma do output recente. Retorna `(args_limpos, should_reject)`.
3. Se após a limpeza um arg **essencial** (`pattern` de search, `command` de run_command) ficou vazio/inutilizável -> `should_reject=True` -> rejeitar + re-emitir hint anti-recursão (a busca/comando virou puro eco). Para `content`/`new_string`, apenas limpar (o resto do content segue válido).

Princípio (DESENHO §6): estrutura, não semântica. A detecção é **amarrada ao output recente real** -- copiar A para B (content = conteúdo de A lido) só seria eco se A fosse um resultado recente COM markers; conteúdo novo que por acaso cite "Exit code:" não casa (não veio de um output recente).

---

## Arquivos alvo (paths absolutos)

### `/home/andrefarias/Desenvolvimento/Nyx-Code/nyx/agent/sanitize.py`

#### Edit 1 — adicionar `strip_result_echo` (no fim do arquivo, após `sanitize_tool_args`)

**Depois (adicionar):**
```python
# LOOP-RESULT-NOT-AS-INPUT-01 (G3): markers que a própria infra injeta nos
# resultados de tool. Aparecendo num arg de ENTRADA, sao assinatura de eco
# recursivo (o 3b copiou o resultado anterior). Lista conservadora: so strings
# que a infra gera, nunca conteudo de usuário tipico.
_RESULT_MARKERS = (
    "chame done()",
    "OK: Arquivo criado",
    "OK: Editado",
    "Exit code:",
    "[stderr]",
    "[resultado de",
    "regex invalido",
    "regex inválido",
    "Nenhum resultado para",
    "Bloqueado por",
    "Permissão negada",
    "Permissao negada",
    "Analise e execute",
    "linhas lidas",
)

# Args textuais onde o eco pode aparecer. file_path/path não entram (sao curtos e
# ja tratados por sanitize_tool_args).
_ECHOABLE_KEYS = ("content", "new_string", "command", "pattern")
# Args essenciais: se viram puro eco (vazios apos limpar), a tool e inutilizavel.
_ESSENTIAL_KEYS = ("command", "pattern")


def _line_is_echo(line: str, recent_lines: set[str]) -> bool:
    """True se a linha e eco de um resultado recente: casa um marker de controle,
    ou e uma linha substancial (>=30 chars) identica a uma recente."""
    stripped = line.strip()
    if not stripped:
        return False
    if any(m in line for m in _RESULT_MARKERS):
        return True
    return len(stripped) >= 30 and stripped in recent_lines


def strip_result_echo(
    name: str, args: Any, recent_outputs: list[str]
) -> tuple[dict[str, Any], bool]:
    """Remove de args textuais as linhas que ecoam um resultado recente de tool.

    Retorna (args_limpos, should_reject). should_reject=True quando um arg
    ESSENCIAL (command/pattern) ficou vazio apos remover o eco -- a tool virou
    puro eco e deve ser rejeitada + re-emitida. Puro/deterministico; so toca
    _ECHOABLE_KEYS; não muta o input (devolve copia).
    """
    if not isinstance(args, dict) or not recent_outputs:
        return (args if isinstance(args, dict) else {}, False) if not isinstance(args, dict) else (args, False)
    recent_lines = {
        ln.strip()
        for out in recent_outputs
        for ln in (out or "").splitlines()
        if ln.strip()
    }
    cleaned = dict(args)
    should_reject = False
    for key in _ECHOABLE_KEYS:
        v = cleaned.get(key)
        if not isinstance(v, str) or not v.strip():
            continue
        kept = [ln for ln in v.splitlines() if not _line_is_echo(ln, recent_lines)]
        new_v = "\n".join(kept).strip()
        if new_v != v.strip():
            cleaned[key] = new_v
            if not new_v and key in _ESSENTIAL_KEYS:
                should_reject = True
    return cleaned, should_reject
```

> **Nota:** o `if not isinstance(args, dict)` acima ficou redundante na minha redação --
> o executor deve simplificar para o idioma do arquivo: se `args` não é dict OU `recent_outputs`
> vazio, devolver `(args if dict else {}, False)`. Mantenha puro e claro.

---

### `/home/andrefarias/Desenvolvimento/Nyx-Code/nyx/agent/loop/_core.py`

#### Edit 2 — resetar `_recent_tool_outputs` por turno (junto de `_turn_presentables`)

# Localização aproximada: em run(), onde a 399 reseta `self._turn_presentables = []`
**Antes:**
```python
        self._turn_presentables = []
```
**Depois:**
```python
        self._turn_presentables = []
        # LOOP-RESULT-NOT-AS-INPUT-01 (G3): saidas recentes de tool do turno, p/
        # detectar eco recursivo (resultado virando entrada da proxima). Rolling 3.
        self._recent_tool_outputs = []
```

---

### `/home/andrefarias/Desenvolvimento/Nyx-Code/nyx/agent/loop/_iteration.py`

#### Edit 3 — import

**Antes:**
```python
from nyx.agent.sanitize import sanitize_tool_args
```
**Depois:**
```python
from nyx.agent.sanitize import sanitize_tool_args, strip_result_echo
```

#### Edit 4 — aplicar anti-recursao em `_execute_tool_calls` (apos o sanitize da 397)

# Localização aproximada: logo apos `args = sanitize_tool_args(name, tc["arguments"])`
**Antes:**
```python
            args = sanitize_tool_args(name, tc["arguments"])

            if self._on_tool:
                self._on_tool(name, args)
```
**Depois:**
```python
            args = sanitize_tool_args(name, tc["arguments"])
            # LOOP-RESULT-NOT-AS-INPUT-01 (G3): corta o eco -- se o arg reusa o
            # resultado recente de uma tool (V06 write recursivo; C2 pattern=erro),
            # limpa as linhas ecoadas; se a busca/comando virou puro eco, rejeita.
            args, _echo_reject = strip_result_echo(
                name, args, getattr(self, "_recent_tool_outputs", [])
            )
            if _echo_reject:
                logger.warning("[loop] arg e puro eco de resultado anterior: %s", name)
                self._session.add_tool_call(name, args, self._ECHO_REJECT_HINT)
                continue

            if self._on_tool:
                self._on_tool(name, args)
```

#### Edit 5 — alimentar `_recent_tool_outputs` apos execução (em `_execute_tool_calls`)

# Localização aproximada: no bloco `if result.success:` (onde a 399 faz `_turn_presentables.append`)
**Antes:**
```python
            if result.success:
                self._has_results = True
                # G3: registra a saída apresentável para o ponto de saída compor.
                if name in PRESENTABLE_TOOLS:
                    self._turn_presentables.append((name, result.output or ""))

        return None
```
**Depois:**
```python
            if result.success:
                self._has_results = True
                # G3: registra a saída apresentável para o ponto de saída compor.
                if name in PRESENTABLE_TOOLS:
                    self._turn_presentables.append((name, result.output or ""))
                # LOOP-RESULT-NOT-AS-INPUT-01: alimenta o rolling de outputs recentes
                # (cap 3) p/ a detecção de eco no próximo tool_call.
                self._recent_tool_outputs.append(result.output or "")
                self._recent_tool_outputs[:] = self._recent_tool_outputs[-3:]

        return None
```

#### Edit 6 — idem no caminho do parser fallback (`_execute_parsed_action`)

# Localização aproximada: apos `remapped = sanitize_tool_args(tool_name, remapped)` (397)
**Antes:**
```python
        remapped = sanitize_tool_args(tool_name, remapped)

        if self._on_tool:
            self._on_tool(tool_name, remapped)
```
**Depois:**
```python
        remapped = sanitize_tool_args(tool_name, remapped)
        remapped, _echo_reject = strip_result_echo(
            tool_name, remapped, getattr(self, "_recent_tool_outputs", [])
        )
        if _echo_reject:
            logger.warning("[loop] arg e puro eco (parser): %s", tool_name)
            self._session.add_tool_call(tool_name, remapped, self._ECHO_REJECT_HINT)
            return None

        if self._on_tool:
            self._on_tool(tool_name, remapped)
```

#### Edit 7 — alimentar `_recent_tool_outputs` no parser fallback + a constante do hint

# Localização aproximada: no `if result.success:` do `_execute_parsed_action` (onde a 399 faz `_turn_presentables.append`)
**Antes:**
```python
        if result.success:
            self._has_results = True
            if tool_name in PRESENTABLE_TOOLS:
                self._turn_presentables.append((tool_name, result.output or ""))

        return None
```
**Depois:**
```python
        if result.success:
            self._has_results = True
            if tool_name in PRESENTABLE_TOOLS:
                self._turn_presentables.append((tool_name, result.output or ""))
            self._recent_tool_outputs.append(result.output or "")
            self._recent_tool_outputs[:] = self._recent_tool_outputs[-3:]

        return None
```

# Constante do hint -- adicionar junto de `_ACTION_REJECT_HINT` (classe `_IterationMixin`)
**Depois (adicionar):**
```python
    # LOOP-RESULT-NOT-AS-INPUT-01 (V06/C2): o arg reusou o resultado de uma tool
    # anterior como entrada (eco recursivo). Forca um arg novo, real.
    _ECHO_REJECT_HINT = (
        "O parâmetro reusa o resultado de uma ferramenta anterior como entrada "
        "(eco). Não cole a saída de uma ferramenta na próxima. Forneça um termo "
        "de busca / comando / conteúdo NOVO e real."
    )
```

---

## Diff esperado (resumo)

```
~ 3 arquivos modificados (sanitize.py, loop/_core.py, loop/_iteration.py)
+ ~75 linhas líquidas
```

---

## Comandos de verificação (literais, copy-paste)

```bash
# 1. Estatica + acentuacao
python -m ruff check nyx/
python3 ~/.config/zsh/scripts/validar-acentuacao.py --paths nyx/agent/sanitize.py nyx/agent/loop/_core.py nyx/agent/loop/_iteration.py

# 2. Unit sanity (função pura -- inline no relatorio)
venv/bin/python -c "
from nyx.agent.sanitize import strip_result_echo as e
# V06: content ecoa o resultado de um write recente -> linha removida
a,r = e('write_file', {'file_path':'x.md','content':'titulo real\nOK: Arquivo criado: x.md (5 bytes). Se a tarefa esta completa, chame done().'}, ['OK: Arquivo criado: x.md (5 bytes). Se a tarefa esta completa, chame done().'])
print('V06:', repr(a['content']), 'reject=', r)
# C2: pattern = erro recente -> vazio -> reject
a,r = e('search', {'pattern':'regex invalido: nothing to repeat at position 0'}, ['Nenhum resultado para: regex invalido: nothing to repeat at position 0'])
print('C2:', repr(a.get('pattern')), 'reject=', r)
# legitimo: content novo que cita Exit code mas não veio de output recente -> intacto
a,r = e('write_file', {'file_path':'d.md','content':'doc: o campo Exit code: 0 indica sucesso'}, ['algum output recente diferente'])
print('LEGIT:', repr(a['content']), 'reject=', r)
"
# ESPERADO: V06 content='titulo real' reject=False; C2 pattern='' reject=True; LEGIT intacto reject=False

# 3. Gauntlet
./run.sh --gauntlet --only rapido
./run.sh --gauntlet --only contexto

# 4. PROOF RUNTIME-REAL as-user (a recursao da C2 não deve mais poluir o Resultado:):
printf '%s\n%s\n' \
  '{"type":"request","content":"liste os arquivos em ~/Desktop"}' \
  '{"type":"request","content":"procure a palavra TODO nesses arquivos"}' \
  | NYX_AUTO_APPROVE=1 ./run.sh --headless 2>/dev/null
# ESPERADO: o summary do listar não contem 'Nenhum resultado para: regex invalido...' ecoado;
#           a busca usa um pattern real (ou rejeita+re-emite), não o eco de um erro.
```

---

## Critério binário de aceite (IA executora)

- [ ] `strip_result_echo` puro em `sanitize.py` (cópia, não muta; só `_ECHOABLE_KEYS`)
- [ ] `_recent_tool_outputs` resetado em `run()` (`_core.py`) e alimentado (cap 3) nos DOIS caminhos
- [ ] anti-recursão aplicada nos DOIS caminhos, após o sanitize da 397
- [ ] `_ECHO_REJECT_HINT` re-emitido quando command/pattern vira puro eco
- [ ] Unit sanity colado (V06 limpa, C2 rejeita, legítimo intacto)
- [ ] Proof runtime as-user colado: listar+buscar sem eco de erro no `Resultado:`
- [ ] `ruff` limpo, acentuação rc=0, `FAIL_AFTER <= FAIL_BEFORE`
- [ ] Gauntlet `rapido` E `contexto` 100%
- [ ] `SPRINT_ORDER_MASTER.md` marca 400 CONCLUIDA; spec movida para `concluidos/`
- [ ] NÃO commitar; NÃO tocar Checkpoint.md

---

## Guardrails anti-engodo (obrigatórios)

NÃO marcar concluída se:
- Detecção de eco NÃO amarrada ao output recente (marker-only puro -> falso-positivo).
- Strippou conteúdo legítimo (o teste LEGIT do unit sanity prova o contrário).
- Re-emitiu mais de 1x em loop (o eco-reject deve convergir; se o 3b insistir, o FORCE_DONE/MAX_ITER é a rede).
- Proof runtime não colado.

Se algo falhar: `[SPRINT 400] BLOQUEADA: <motivo 1 linha>`.

---

## Proof-of-work obrigatório (4 passos)

```bash
bash scripts/sprint_invariants.sh > /tmp/inv_before.txt 2>&1
FAIL_BEFORE=$(grep -c "^\[FAIL\]" /tmp/inv_before.txt)
# implementar
bash scripts/sprint_invariants.sh > /tmp/inv_after.txt 2>&1
FAIL_AFTER=$(grep -c "^\[FAIL\]" /tmp/inv_after.txt)
diff /tmp/inv_before.txt /tmp/inv_after.txt
```
Colar: inv_before/inv_after (tail), diff, unit sanity, proof runtime as-user, `git --no-pager diff --stat`.

---

## Gambiarras específicas desta sprint

- **Falso-positivo por marker-only:** a detecção DEVE amarrar ao `recent_outputs` (a linha tem de ter vindo de um resultado recente). O teste LEGIT do unit sanity guarda isso.
- **Mutar o input:** `strip_result_echo` devolve cópia.
- **Rolling sem cap:** `_recent_tool_outputs` cap 3 (`[-3:]`) -- senão infla memória em sessão longa.
- **Loop de re-emit:** eco-reject re-emite 1x por tool call; a convergência vem do FORCE_DONE (344)/MAX_ITER.

---

## Validação humana (checklist do usuário)

```bash
cd /home/andrefarias/Desenvolvimento/Nyx-Code
git --no-pager show --stat HEAD
./run.sh
# Numa sessão: "liste os arquivos em ~/Desktop" e depois "procure TODO neles".
# ESPERADO: a resposta não mostra 'Nenhum resultado para: regex invalido...' ecoado.
ls dev-journey/06-sprints/concluidos/SPRINT_LOOP_RESULT_NOT_AS_INPUT_01.md  # existe
```

---

## Riscos

| Risco | Mitigação |
|-------|-----------|
| Conteúdo legítimo copiado de A para B é stripado | Amarrado ao `recent_outputs` + markers de controle; copiar dados puros (sem markers) não casa. Teste LEGIT cobre. |
| Linha substancial (>=30) legítima coincide com output recente | Raro; e se ocorrer, é de fato eco (o usuário não digita 30+ chars idênticos a um resultado recente). |
| Re-emit em loop se o 3b insiste no eco | Rejeição re-emite 1x/tool; FORCE_DONE/MAX_ITER encerram. |

---

*"O resultado de uma ação não é o material da próxima -- senão o ciclo nunca fecha." -- princípio de execução (dev-journey/02-architecture/DESENHO_CONTRATO_EXECUCAO.md)*
