## 0. SPEC (machine-readable)

```yaml
sprint:
  id: EXEC-CONTRACT-TOOLCALL-SANITIZE-01
  title: "Contrato G1: sanitizar args do tool_call antes de executar (path sem crase/escape; content vazio bloqueado)"
  onda: 48
  prioridade: ALTA
  tipo: Feature
  dependencias: [EXEC-CONTRACT-NO-HALLUCINATED-RESULT-01]
  desbloqueia: [EXEC-CONTRACT-TOOL-MATCH-01, SEQ-EDIT-ENFORCE-EDITFILE-01]

  touches:
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/agent/loop/_iteration.py
      reason: "aplicar a sanitizacao nos DOIS caminhos de execução, antes de permission/preflight/execute"
      linhas_alvo: "243-246 (_execute_tool_calls), apos _remap_params (_execute_parsed_action)"
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/agent/preflight.py
      reason: "escalar content vazio de write_file/create_file de warning para erro (bloqueia o arquivo vazio que mascara o codigo perdido -- V02)"
      linhas_alvo: "59-67"
  creates:
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/agent/sanitize.py
      reason: "função pura sanitize_tool_args: limpa lixo de markdown/aspas/escape dos args path-like antes de executar"
  removes: []

  forbidden:
    - "Adicionar emoji"
    - "Usar 'print()' fora de cli.py/output.py"
    - "Mencao a IA proprietaria"
    - "Adivinhar intencao por dicionario de verbos (a sanitizacao valida ESTRUTURA do arg, não semantica)"
    - "Mexer no validate_path/base.py (o gate de sandbox e o bloqueio de segredos seguem intactos)"
    - "Tocar a apresentacao da 399, o gating, o write_memory, a cascata OOM"

  tests:
    - cmd: "./run.sh --gauntlet --only rapido"
      timeout: 300
      deve_passar: true
    - cmd: "./run.sh --gauntlet --only fs_arbitrary"
      timeout: 300
      deve_passar: true

  acceptance_criteria:
    - "Path com crase de markdown (`\\`arquivo.md`) e limpo para `arquivo.md` antes de executar"
    - "Path com escape `\\/home\\/user` e desescapado para `/home/user` antes de executar"
    - "write_file/create_file com content vazio/branco e BLOQUEADO no preflight (não cria arquivo vazio mascarando o codigo perdido)"
    - "A sanitizacao roda nos DOIS caminhos (tool_calls nativo E parser fallback)"
    - "Proof runtime: criar arquivo numa sessão acumulada salva no path CERTO com conteudo real (V02 morto); listar dir com path escapado funciona (C1 morto)"
    - "Gauntlet rapido E fs_arbitrary 100%; validate_path/secrets intactos"
```

---

# Sprint EXEC-CONTRACT-TOOLCALL-SANITIZE-01 — Contrato G1: sanitizar o tool_call

**Status:** PENDENTE
**Data criação:** 2026-06-26
**Modelo obrigatório:** claude-opus-4-7 (executor-sprint autorizado pelo dono nesta onda)

---

## Contexto do projeto (snapshot — não referência)

> **ADRs relevantes (inline):**
> - **ADR-032 A INFRA CARREGA O MODELO:** quando o 3b emite um tool_call com lixo de markdown no path, a infra **corrige** (sanitiza) -- não repassa o erro nem cria arquivo no lugar errado.
> - **ADR-033 A CADEIA NUNCA QUEBRA.** ADR-009 Acesso Universal, ADR-001 Local First, ADR-006 PT-BR, ADR-005 Anonimato, ADR-024 Render layer, ADR-014 Testes via Gauntlet, ADR-010 Zero Mocks.
>
> **Estado (2026-06-26):** `qwen2.5-coder:3b`, Ollama :11435, proxy :11436. 35 tools. ONDA-48 fase raiz: 399 (esqueleto do contrato) CONCLUIDA em `f0883a1`. Desenho: `dev-journey/02-architecture/DESENHO_CONTRATO_EXECUCAO.md` (G1, ponto A). Achado: `dev-journey/07-reports/AUDIT_VALIDACAO_2026_06_26.md` (V02).

---

## Problema

**Achado V02 CREATE-FILE-MALFORMED [ALTA]** + **C1** (reproduzido na validação as-user da 399):
- V02: criar arquivo em sessão acumulada -> `write_file` com `file_path="\`identacao_python.md"` (crase de markdown no nome), `content=""` (perdeu o código gerado), salvo no **project root** em vez do `~/Desktop` pedido; o summary mentia "criado: ~/Desktop/...".
- C1 (validação 399, turno listar `~/Desktop`): `list_files({'path': '\\/home\\/andrefarias\\/Desktop'})` -> o escape `\/` resolveu para o **pai errado** (`/home/andrefarias/Desenvolvimento/`), `Diretório não encontrado`.

**Causa-raiz:** o loop passa os args do tool_call **direto** para `self._tools.execute` sem limpar o lixo estrutural que o 3b cola (crase de markdown, aspas penduradas, escapes `\/`). E `write_file` com `content` vazio cria um arquivo vazio que **mascara** o código perdido (a `validate.py:48-51` só **avisa**, não bloqueia).

Pontos no código (lidos e confirmados nesta sessão, pós-399):
- `nyx/agent/loop/_iteration.py:243-245` -- `_execute_tool_calls`: `name=tc["name"]; args=tc["arguments"]` vão direto para permission/preflight/execute sem sanitização.
- `nyx/agent/loop/_iteration.py` -- `_execute_parsed_action`: `remapped = _remap_params(tool_name, action.params)` idem.
- `nyx/agent/preflight.py:59-67` -- `write_file` só checa diretório pai; `nyx/agent/validator.py:48-51` só **avisa** content vazio (pós-execução, tarde demais).

---

## Solução proposta

**G1 (ponto A):** sanitizar **estrutura** dos args antes de executar (não semântica -- nada de adivinhar verbo):
1. Novo módulo `nyx/agent/sanitize.py` com `sanitize_tool_args(name, args)` puro: limpa valores **path-like** (`file_path`, `path`) -- tira crase/aspas/espaço nas pontas, desescapa `\/ \. \- \_`.
2. Aplicar a sanitização nos **dois** caminhos de execução, logo após obter os args (antes de `on_tool`/permission/preflight/execute).
3. `nyx/agent/preflight.py`: escalar `content` vazio/branco de `write_file`/`create_file` de **warning** para **erro** (bloqueia o arquivo vazio; o modelo re-emite com o conteúdo real).

Princípio (DESENHO §6): valida **estrutura** do arg, não intenção. Determinístico, aditivo, sem regex de verbo.

---

## Arquivos alvo (paths absolutos)

### `/home/andrefarias/Desenvolvimento/Nyx-Code/nyx/agent/sanitize.py` (NOVO)

```python
"""Sanitização estrutural de args de tool_call (EXEC-CONTRACT-TOOLCALL-SANITIZE-01).

G1 do contrato de execução (ponto A): o 3b cola lixo de markdown no tool_call
(crase em volta do path, aspas penduradas, escapes `\\/`). A infra LIMPA a
estrutura antes de executar -- não confia que o 3b emita o arg limpo (ADR-032).
Puro/determinístico: valida estrutura, nunca semântica (sem dicionário de verbos).
"""

from __future__ import annotations

import re
from typing import Any

# Args que carregam um caminho de arquivo/diretório.
_PATH_KEYS = ("file_path", "path")

# Desescapa markdown-escapes comuns que o 3b cola num path: \/ \. \- \_
_UNESCAPE_RE = re.compile(r"\\([/._\-])")


def _clean_path_value(value: str) -> str:
    """Tira crase/aspas/espaço das pontas e desescapa o path. Idempotente."""
    s = value.strip()
    # Remove cercas de markdown / crases / aspas nas pontas (repete p/ aninhado).
    for _ in range(3):
        new = s.strip().strip("`").strip().strip("\"'").strip()
        if new == s:
            break
        s = new
    # Desescapa \/ -> / etc. (um path real não traz esses escapes).
    s = _UNESCAPE_RE.sub(r"\1", s)
    return s.strip()


def sanitize_tool_args(name: str, args: Any) -> dict[str, Any]:
    """Devolve uma CÓPIA dos args com os valores path-like limpos.

    Só toca `file_path`/`path` quando são strings não-vazias e a limpeza muda
    algo. Não remove chaves, não inventa valores, não valida sandbox (isso é do
    validate_path). Se `args` não é dict, devolve como veio.
    """
    if not isinstance(args, dict):
        return args
    cleaned = dict(args)
    for key in _PATH_KEYS:
        v = cleaned.get(key)
        if isinstance(v, str) and v.strip():
            nv = _clean_path_value(v)
            if nv and nv != v:
                cleaned[key] = nv
    return cleaned


# "Limpar a ferramenta antes de usá-la é metade do trabalho." -- princípio de execução
```

---

### `/home/andrefarias/Desenvolvimento/Nyx-Code/nyx/agent/loop/_iteration.py`

#### Edit 1 — import do sanitizador (junto dos outros imports do topo)

# Localização aproximada: bloco de imports `from nyx.agent...` (linha ~20-30)
**Depois (adicionar):**
```python
from nyx.agent.sanitize import sanitize_tool_args
```

#### Edit 2 — sanitizar em `_execute_tool_calls`

# Localização aproximada: linha 243-245 (inicio do for, antes de on_tool)
**Antes:**
```python
        for tc in tool_calls:
            name = tc["name"]
            args = tc["arguments"]

            if self._on_tool:
                self._on_tool(name, args)
```
**Depois:**
```python
        for tc in tool_calls:
            name = tc["name"]
            # EXEC-CONTRACT-TOOLCALL-SANITIZE-01 (G1, V02/C1): limpa lixo de markdown
            # (crase/aspas/escape `\/`) dos args path-like ANTES de tudo (on_tool,
            # permission, preflight, execute veem o arg ja limpo). Estrutura, não
            # semantica -- a infra corrige o 3b sem adivinhar intencao (ADR-032).
            args = sanitize_tool_args(name, tc["arguments"])

            if self._on_tool:
                self._on_tool(name, args)
```

#### Edit 3 — sanitizar em `_execute_parsed_action`

# Localização aproximada: a linha `remapped = _remap_params(tool_name, action.params)` (apos o roteamento ACTION_TO_TOOL, ~linha 400-435 pos-399)
**Antes:**
```python
        remapped = _remap_params(tool_name, action.params)

        if self._on_tool:
            self._on_tool(tool_name, remapped)
```
**Depois:**
```python
        remapped = _remap_params(tool_name, action.params)
        # EXEC-CONTRACT-TOOLCALL-SANITIZE-01 (G1): idem caminho nativo, agora no
        # parser fallback (onde o 3b mais cola lixo de markdown no path).
        remapped = sanitize_tool_args(tool_name, remapped)

        if self._on_tool:
            self._on_tool(tool_name, remapped)
```

---

### `/home/andrefarias/Desenvolvimento/Nyx-Code/nyx/agent/preflight.py`

#### Edit 4 — bloquear content vazio em write_file/create_file

# Localização aproximada: bloco `if tool_name == "write_file" and file_path:` (linha 59-67)
**Antes:**
```python
    if tool_name == "write_file" and file_path:
        path = (
            Path(file_path)
            if file_path.startswith("/")
            else _resolve_first_existing(file_path)
        )
        parent = path.parent
        if not parent.exists():
            result.warnings.append(f"Diretório pai não existe: {parent}")
```
**Depois:**
```python
    if tool_name in ("write_file", "create_file") and file_path:
        # EXEC-CONTRACT-TOOLCALL-SANITIZE-01 (G1, V02): content vazio/branco vira
        # ERRO (era so warning no validator pos-execução). O 3b as vezes perde o
        # codigo gerado e manda content="" -> um arquivo vazio mascara o codigo
        # perdido. Bloquear forca o re-emit com o conteudo real (ADR-032).
        if not (args.get("content") or "").strip():
            result.errors.append(
                "content vazio: reenvie write_file com o conteudo real do arquivo"
            )
        path = (
            Path(file_path)
            if file_path.startswith("/")
            else _resolve_first_existing(file_path)
        )
        parent = path.parent
        if not parent.exists():
            result.warnings.append(f"Diretório pai não existe: {parent}")
```

> **Nota ao executor:** confirme via grep que nenhuma fase do gauntlet cria arquivo vazio
> legítimo via `write_file` (ex.: fixture de `__init__.py` vazio). Se houver, o bloqueio
> regride essa fase -- nesse caso, reporte e NÃO marque concluída; reavaliamos o gate
> (ex.: só bloquear quando o nome sugere arquivo de código `.py/.js/.ts/.md`).

---

## Diff esperado (resumo)

```
+ 1 arquivo criado (nyx/agent/sanitize.py)
~ 2 arquivos modificados (_iteration.py, preflight.py)
+ ~70 linhas líquidas
```

---

## Comandos de verificação (literais, copy-paste)

```bash
# 1. Estatica + acentuacao
python -m ruff check nyx/
python3 ~/.config/zsh/scripts/validar-acentuacao.py --paths nyx/agent/sanitize.py nyx/agent/loop/_iteration.py nyx/agent/preflight.py

# 2. Unit sanity (sanitizador puro -- pode ser inline no relatorio, ADR-014 não exige gauntlet p/ função pura)
venv/bin/python -c "from nyx.agent.sanitize import sanitize_tool_args as s; \
print(s('write_file', {'file_path': '\`identacao.md', 'content': 'x'})); \
print(s('list_files', {'path': '\\\\/home\\\\/andre\\\\/Desktop'}))"
# ESPERADO: {'file_path': 'identacao.md', 'content': 'x'}  e  {'path': '/home/andre/Desktop'}

# 3. Gauntlet (sem regressao)
./run.sh --gauntlet --only rapido
./run.sh --gauntlet --only fs_arbitrary

# 4. PROOF RUNTIME-REAL as-user (sessão acumulada -- onde V02 nascia):
printf '%s\n%s\n%s\n' \
  '{"type":"request","content":"liste os arquivos em ~/Desktop"}' \
  '{"type":"request","content":"agora crie ~/Desktop/nyx_397.py com uma função soma(a,b) que retorna a+b"}' \
  '{"type":"request","content":"confirme o conteudo do arquivo que voce criou"}' \
  | NYX_AUTO_APPROVE=1 ./run.sh --headless 2>/dev/null
# ESPERADO: arquivo criado em ~/Desktop/nyx_397.py (path CERTO, não project root),
#           com a função real (content não vazio), confirmado na leitura. Limpar o arquivo apos.
```

---

## Critério binário de aceite (IA executora)

- [ ] `nyx/agent/sanitize.py` criado; `sanitize_tool_args` puro (cópia, não muta o input)
- [ ] Sanitização aplicada nos DOIS caminhos (`_execute_tool_calls` E `_execute_parsed_action`)
- [ ] preflight bloqueia `content` vazio em write_file/create_file (erro, não warning)
- [ ] Unit sanity colado (crase limpa, escape desescapado)
- [ ] Proof runtime as-user colado: criação no path certo + content real (V02/C1 mortos)
- [ ] `ruff` limpo, acentuação rc=0, `FAIL_AFTER <= FAIL_BEFORE`
- [ ] Gauntlet `rapido` E `fs_arbitrary` 100% (validate_path/secrets intactos)
- [ ] `SPRINT_ORDER_MASTER.md` marca 397 CONCLUIDA; spec movida para `concluidos/`
- [ ] NÃO commitar (orquestrador faz o commit seletivo); NÃO tocar Checkpoint.md

---

## Guardrails anti-engodo (obrigatórios)

NÃO marcar concluída se:
- Sanitização semântica (adivinhar verbo/intenção) em vez de estrutural.
- Mexeu em `validate_path`/secrets (escopo proibido).
- Bloqueio de content vazio regrediu uma fase do gauntlet sem reportar.
- Proof runtime não colado com dados reais.

Se algo falhar: `[SPRINT 397] BLOQUEADA: <motivo 1 linha>`.

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
Colar: inv_before/inv_after (tail), diff, unit sanity, proof runtime as-user, e `git --no-pager diff --stat`.

---

## Gambiarras específicas desta sprint

- **Sanitizar demais:** não tocar `content`/`command`/`pattern` (só `file_path`/`path`). Limpar content quebraria código legítimo com crase/aspas.
- **Idempotência:** `sanitize_tool_args` aplicado 2x não pode mudar o resultado (o loop pode re-emitir).
- **Não mutar o input:** retornar cópia (`dict(args)`), não o dict original (o histórico/telemetria referenciam o original).
- **Bloqueio cego de content vazio:** verificar gauntlet antes de marcar; reportar se regredir (ver nota no Edit 4).

---

## Validação humana (checklist do usuário)

```bash
cd /home/andrefarias/Desenvolvimento/Nyx-Code
git --no-pager show --stat HEAD
./run.sh
# Numa sessão, peca: "crie ~/Desktop/teste.py com uma função qualquer"
# ESPERADO: arquivo no ~/Desktop (path certo) com o codigo de verdade (não vazio).
ls dev-journey/06-sprints/concluidos/SPRINT_EXEC_CONTRACT_TOOLCALL_SANITIZE_01.md  # existe
```

---

## Riscos

| Risco | Mitigação |
|-------|-----------|
| Path legítimo com crase/aspas no nome (raro no Linux) é alterado | Trade-off aceito: o 3b emite markdown muitíssimo mais que paths com crase real. |
| Bloqueio de content vazio quebra fixture de arquivo vazio no gauntlet | Nota no Edit 4: executor verifica antes; se regredir, estreita o gate para arquivos de código. |
| Desescape `\/` corromper um path que de fato tinha `\` | Path real não traz `\/`; é artefato de markdown. Idempotente e ancorado em escapes específicos. |

---

*"Confiar é barato; garantir é o trabalho." -- princípio de execução (dev-journey/02-architecture/DESENHO_CONTRATO_EXECUCAO.md)*
