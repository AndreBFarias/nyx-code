## 0. SPEC (machine-readable)

```yaml
sprint:
  id: SEQ-EDIT-ENFORCE-EDITFILE-01
  title: "Contrato G1: edição sequencial usa edit_file (não write_file cego); content não e comando shell"
  onda: 48
  prioridade: ALTA
  tipo: Feature
  dependencias: [EXEC-CONTRACT-TOOL-MATCH-01]
  desbloqueia: []

  touches:
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/agent/loop/_iteration.py
      reason: "guard seq-edit antes de executar tool de escrita, nos 2 caminhos; rejeita 1x + re-emite"
      linhas_alvo: "_execute_tool_calls (apos tool-match da 398); _execute_parsed_action (idem); reset do flag"
  creates: []
  removes: []

  forbidden:
    - "Adicionar emoji"
    - "Usar 'print()' fora de cli.py/output.py"
    - "Mencao a IA proprietaria"
    - "Bloquear DEFINITIVO o write_file em arquivo existente (rewrite legitimo existe -- a rejeição e 1x SINAL, depois passa)"
    - "Tocar validate_path/base.py (sandbox/secrets intactos); apresentacao 399, sanitize 397, anti-recursao 400, tool-match 398"

  tests:
    - cmd: "./run.sh --gauntlet --only rapido"
      timeout: 300
      deve_passar: true
    - cmd: "./run.sh --gauntlet --only fs_arbitrary"
      timeout: 300
      deve_passar: true

  acceptance_criteria:
    - "write_file num arquivo que JA existe e não foi lido na sessão -> rejeita 1x + re-emite (leia antes / use edit_file)"
    - "content/new_string que e um comando shell de redirecionamento (echo ... >> arquivo) -> rejeita 1x + re-emite (use run_command ou conteudo real)"
    - "write_file em arquivo NOVO (não existe) ou JA lido na sessão -> passa normal (sem falso-positivo)"
    - "Rejeicao no maximo 1x/turno (flag); rewrite legitimo passa na 2a tentativa"
    - "Proof runtime: edição sequencial num .md existente não sobrescreve cegamente nem injeta shell-como-content (V05 mitigado)"
    - "Gauntlet rapido E fs_arbitrary 100%"
```

---

# Sprint SEQ-EDIT-ENFORCE-EDITFILE-01 — Contrato G1: edição sequencial segura

**Status:** PENDENTE
**Data criação:** 2026-06-26
**Modelo obrigatório:** claude-opus-4-7 (executor-sprint autorizado pelo dono nesta onda)

---

## Contexto do projeto (snapshot — não referência)

> **ADRs relevantes (inline):**
> - **ADR-032 A INFRA CARREGA O MODELO:** numa edição sequencial o 3b sobrescreve cego e mistura comando shell com conteúdo. A infra detecta e re-emite -- não deixa perder o arquivo nem gravar lixo.
> - **ADR-033 A CADEIA NUNCA QUEBRA.** ADR-009, ADR-001, ADR-006, ADR-005, ADR-024, ADR-014, ADR-010.
>
> **Estado (2026-06-26):** `qwen2.5-coder:3b`, Ollama :11435, proxy :11436. ONDA-48 fase raiz: 399 `f0883a1`, 397 `6c61f1d`, 400 `b1a17fe`, 398 `2e15c81` CONCLUIDAS. Desenho: `dev-journey/02-architecture/DESENHO_CONTRATO_EXECUCAO.md` (G1, ponto A). Achado: `dev-journey/07-reports/AUDIT_VALIDACAO_2026_06_26.md` (V05).

---

## Problema

**Achado V05 SEQ-EDIT-BROKEN [ALTA]:** 3 edições sequenciais no mesmo arquivo:
- `write_file` **sobrescreve** (perde o título existente) -- escrita cega sem ler o que já estava lá;
- põe **comando shell como conteúdo** (`content="echo '...' >> arquivo"`) -- confundiu `write_file` com `run_command`;
- tenta `create_file`, erros contraditórios ("já existe" / "não encontrado"). Resultado: nada aplicado corretamente.

**Causa-raiz (2 problemas estruturais):**
1. **Overwrite cego:** `write_file` num arquivo que JÁ existe e que o modelo NÃO leu na sessão -> perde o conteúdo anterior. A edição sequencial pede `edit_file` (substituição cirúrgica) ou read-before-write.
2. **Shell-como-content:** `content` é um comando de redirecionamento shell (`echo ... >>`), não o conteúdo do arquivo -- o modelo quis `run_command`.

---

## Solução proposta

**G1 (ponto A), 1x SINAL de re-emissão (não bloqueio definitivo):**
1. Guard `_seq_edit_reject(name, args)` antes de executar tool de escrita, nos 2 caminhos:
   - **Overwrite cego:** `name` em (`write_file`,`create_file`), arquivo resolvido **existe** E **não** está no set de lidos da sessão (`self._session._files_read`) -> hint "leia antes (read_file) e use edit_file, ou reescreva com o conteúdo completo".
   - **Shell-como-content:** `content`/`new_string` casa um redirecionamento shell (`echo|cat|printf|tee ... >>|>`) -> hint "isso é um comando shell, não conteúdo; use run_command para executar, ou forneça o conteúdo real".
2. Rejeita no máximo **1x/turno** (flag `_seq_edit_rejected`). Rewrite legítimo passa na 2a tentativa.

Princípio (DESENHO §6): âncora estrutural (arquivo existe + não lido; padrão shell), intenção como sinal 1x. `validate_path` (sandbox/secrets) intacto -- só usado para resolver o path canônico igual ao que read_file grava.

---

## Arquivos alvo (paths absolutos)

### `/home/andrefarias/Desenvolvimento/Nyx-Code/nyx/agent/loop/_iteration.py`

#### Edit 1 — import de `re` (se ausente) + Path; e o resolver canônico

# `re` já é importado no topo (`import re`). `Path` e `validate_path`: adicionar.
**Antes (bloco de imports):**
```python
from nyx.agent.preflight import check as preflight_check
```
**Depois:**
```python
from nyx.agent.preflight import check as preflight_check
from nyx.agent.tools.base import validate_path as _validate_path
```

#### Edit 2 — constantes + regex (classe `_IterationMixin`, junto de `_TOOL_MATCH_HINT`)

**Depois (adicionar):**
```python
    # SEQ-EDIT-ENFORCE-EDITFILE-01 (V05): content que e um comando shell de
    # redirecionamento (echo '...' >> arquivo) -- o 3b confundiu write_file com
    # run_command. Ancorado no inicio da linha; precisa do redirecionamento.
    _SHELL_AS_CONTENT_RE = re.compile(
        r"^\s*(?:echo|cat|printf|tee|sed|awk)\b.*?(?:>>|>)\s*\S",
        re.IGNORECASE | re.MULTILINE,
    )
    _SEQ_OVERWRITE_HINT = (
        "Esse arquivo JÁ existe e você não o leu nesta sessão. Não sobrescreva às "
        "cegas: leia primeiro com read_file e use edit_file para a alteração "
        "cirúrgica, ou reescreva com o conteúdo COMPLETO (não parcial)."
    )
    _SEQ_SHELL_HINT = (
        "O conteúdo é um comando de shell (redirecionamento), não o conteúdo do "
        "arquivo. Para executar um comando use run_command; para escrever, forneça "
        "o texto real que deve ficar no arquivo."
    )
```

#### Edit 3 — helper `_seq_edit_reject` (método de `_IterationMixin`, junto de `_tool_match_reject`)

**Depois (adicionar):**
```python
    def _seq_edit_reject(self, name: str, args: dict) -> str | None:
        """SEQ-EDIT-ENFORCE-EDITFILE-01: hint a re-emitir numa edição sequencial
        insegura. None se não deve rejeitar. Rejeita no maximo 1x/turno.

        Dois casos:
        - shell-como-content: content/new_string e um comando de redirecionamento;
        - overwrite cego: write_file/create_file num arquivo que JA existe e não
          foi lido nesta sessão.
        """
        if getattr(self, "_seq_edit_rejected", False):
            return None
        # Shell-como-content (qualquer tool de escrita).
        if name in ("write_file", "create_file", "edit_file"):
            text = args.get("content") or args.get("new_string") or ""
            if isinstance(text, str) and self._SHELL_AS_CONTENT_RE.search(text):
                return self._SEQ_SHELL_HINT
        # Overwrite cego (so write_file/create_file -- edit_file ja e cirúrgico).
        if name in ("write_file", "create_file"):
            file_path = args.get("file_path") or args.get("path") or ""
            if isinstance(file_path, str) and file_path.strip():
                try:
                    resolved = _validate_path(file_path, self._project_root)
                except Exception:  # noqa: BLE001 -- resolver falho não deve derrubar o guard
                    return None
                read_set = getattr(self._session, "_files_read", set())
                if resolved.exists() and str(resolved) not in read_set:
                    return self._SEQ_OVERWRITE_HINT
        return None
```

#### Edit 4 — reset do flag em `_init_done_guard`

# Localização: junto de `self._tool_match_rejected = False`
**Antes:**
```python
        self._tool_match_rejected = False
```
**Depois:**
```python
        self._tool_match_rejected = False
        # SEQ-EDIT-ENFORCE-EDITFILE-01: arma o guard de edição sequencial (1x/turno).
        self._seq_edit_rejected = False
```

#### Edit 5 — aplicar o guard em `_execute_tool_calls` (apos o tool-match da 398)

# Localização aproximada: logo apos o bloco `if tm_hint:` (da 398), antes de `if self._on_tool:`
**Antes:**
```python
            tm_hint = self._tool_match_reject(name)
            if tm_hint:
                self._tool_match_rejected = True
                logger.warning("[loop] tool-match: pedido de leitura, tool mutante %s", name)
                self._session.add_tool_call(name, args, tm_hint)
                continue

            if self._on_tool:
                self._on_tool(name, args)
```
**Depois:**
```python
            tm_hint = self._tool_match_reject(name)
            if tm_hint:
                self._tool_match_rejected = True
                logger.warning("[loop] tool-match: pedido de leitura, tool mutante %s", name)
                self._session.add_tool_call(name, args, tm_hint)
                continue

            # SEQ-EDIT-ENFORCE-EDITFILE-01 (V05): edição sequencial insegura
            # (overwrite cego ou shell-como-content) -> rejeita 1x + re-emite.
            se_hint = self._seq_edit_reject(name, args)
            if se_hint:
                self._seq_edit_rejected = True
                logger.warning("[loop] seq-edit inseguro em %s", name)
                self._session.add_tool_call(name, args, se_hint)
                continue

            if self._on_tool:
                self._on_tool(name, args)
```

#### Edit 6 — aplicar o guard em `_execute_parsed_action` (apos o tool-match da 398)

# Localização aproximada: apos o bloco `if tm_hint:` (da 398) no parser fallback
**Antes:**
```python
        tm_hint = self._tool_match_reject(tool_name)
        if tm_hint:
            self._tool_match_rejected = True
            logger.warning("[loop] tool-match (parser): pedido leitura, tool mutante %s", tool_name)
            self._session.add_tool_call(tool_name, remapped, tm_hint)
            return None

        if self._on_tool:
            self._on_tool(tool_name, remapped)
```
**Depois:**
```python
        tm_hint = self._tool_match_reject(tool_name)
        if tm_hint:
            self._tool_match_rejected = True
            logger.warning("[loop] tool-match (parser): pedido leitura, tool mutante %s", tool_name)
            self._session.add_tool_call(tool_name, remapped, tm_hint)
            return None

        # SEQ-EDIT-ENFORCE-EDITFILE-01 (V05): idem caminho nativo, no parser fallback.
        se_hint = self._seq_edit_reject(tool_name, remapped)
        if se_hint:
            self._seq_edit_rejected = True
            logger.warning("[loop] seq-edit inseguro (parser) em %s", tool_name)
            self._session.add_tool_call(tool_name, remapped, se_hint)
            return None

        if self._on_tool:
            self._on_tool(tool_name, remapped)
```

> **Nota ao executor:** confirme que `validate_path` NÃO levanta para paths fora da raiz no modo
> default (acesso livre ONDA-37) -- ele resolve e devolve o Path (só `~/.ssh` etc. levanta). O
> `try/except` cobre o raise de segredo (nesse caso, não rejeitamos por overwrite -- o secret-block
> da própria tool age depois). Confirme tambem o nome real do set de lidos da sessão (`_files_read`)
> via grep em `nyx/agent/session.py` ANTES (a spec assume `self._session._files_read`).

---

## Diff esperado (resumo)

```
~ 1 arquivo modificado (loop/_iteration.py)
+ ~75 linhas líquidas
```

---

## Comandos de verificação (literais, copy-paste)

```bash
# 1. Estatica + acentuacao
python -m ruff check nyx/
python3 ~/.config/zsh/scripts/validar-acentuacao.py --paths nyx/agent/loop/_iteration.py

# 2. Gauntlet
./run.sh --gauntlet --only rapido
./run.sh --gauntlet --only fs_arbitrary

# 3. PROOF RUNTIME-REAL as-user (V05 -- edição sequencial num arquivo existente):
F=~/Desktop/nyx_401_seq.md
printf '# Titulo Original\n\nlinha um\n' > "$F"
printf '%s\n%s\n%s\n' \
  '{"type":"request","content":"adicione a linha \"linha dois\" no arquivo ~/Desktop/nyx_401_seq.md"}' \
  '{"type":"request","content":"agora adicione \"linha tres\" no mesmo arquivo"}' \
  '{"type":"request","content":"mostre o conteudo final do arquivo"}' \
  | NYX_AUTO_APPROVE=1 ./run.sh --headless 2>/dev/null
cat "$F"   # ESPERADO: o titulo original PRESERVADO + linhas adicionadas; não um 'echo ... >>' literal
rm -f "$F"
# REPROVADO se: o titulo sumiu (overwrite cego), ou o arquivo contem 'echo ... >>' como texto.
```

---

## Critério binário de aceite (IA executora)

- [ ] `_seq_edit_reject` cobre overwrite-cego (existe + não lido) E shell-como-content
- [ ] Guard nos DOIS caminhos, após o tool-match da 398; rejeição 1x/turno (flag resetado em `_init_done_guard`)
- [ ] Nome do set de lidos confirmado via grep (`session.py`); `validate_path` resolve sem derrubar o guard
- [ ] Proof runtime as-user colado: título preservado na edição sequencial; sem shell-como-content no arquivo
- [ ] `ruff` limpo, acentuação rc=0, `FAIL_AFTER <= FAIL_BEFORE`
- [ ] Gauntlet `rapido` E `fs_arbitrary` 100% (sem regressão de escrita legítima)
- [ ] `SPRINT_ORDER_MASTER.md` marca 401 CONCLUIDA; spec movida para `concluidos/`
- [ ] NÃO commitar; NÃO tocar Checkpoint.md

---

## Guardrails anti-engodo (obrigatórios)

NÃO marcar concluída se:
- Bloqueou write_file em arquivo NOVO (falso-positivo -> quebra criação legítima; o gauntlet fs_arbitrary pega).
- Virou bloqueio definitivo (rejeição >1x -> rewrite legítimo nunca passa).
- Proof runtime não colado, ou o título sumiu mesmo assim.

Se algo falhar: `[SPRINT 401] BLOQUEADA: <motivo 1 linha>`.

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
Colar: inv_before/inv_after (tail), diff, proof runtime as-user (cat do arquivo), `git --no-pager diff --stat`.

---

## Gambiarras específicas desta sprint

- **Falso-positivo em arquivo novo:** o overwrite-cego SÓ dispara se `resolved.exists()`. Arquivo novo (não existe) passa.
- **Bloqueio definitivo:** 1x/turno (flag). Rewrite legítimo re-emite e passa.
- **Shell regex frágil:** ancorar no início da linha + exigir redirecionamento (`>>`/`>`). Um content que mencione "echo" sem redirecionar não casa.
- **Set de lidos errado:** confirmar `_files_read` via grep; se o nome diferir, ajustar (senão o guard nunca acha o arquivo lido e re-emite sempre).

---

## Validação humana (checklist do usuário)

```bash
cd /home/andrefarias/Desenvolvimento/Nyx-Code
git --no-pager show --stat HEAD
printf '# Titulo\nlinha um\n' > ~/Desktop/seq.md
./run.sh   # peca: "adicione 'linha dois' em ~/Desktop/seq.md"
cat ~/Desktop/seq.md   # ESPERADO: titulo + linha um PRESERVADOS + linha dois
rm ~/Desktop/seq.md
ls dev-journey/06-sprints/concluidos/SPRINT_SEQ_EDIT_ENFORCE_EDITFILE_01.md  # existe
```

---

## Riscos

| Risco | Mitigação |
|-------|-----------|
| Rewrite legítimo de arquivo existente é re-emitido | 1x SINAL; na 2a passa. E o hint sugere o caminho seguro (ler+editar). |
| `validate_path` levanta para `~/.ssh` e quebra o guard | `try/except` -> None (não rejeita por overwrite; o secret-block da tool age). |
| Set `_files_read` com nome diferente | Nota no Edit 3: confirmar via grep em session.py antes. |
| Shell-regex pega content legítimo com `echo ... >>` (ex.: um script .sh) | Raro; e se o usuário escreve um script com redirecionamento, o re-emit 1x sugere run_command -- na 2a tentativa o write passa. |

---

*"Editar não é reescrever do zero -- e quem não lê antes de escrever, apaga." -- princípio de execução (dev-journey/02-architecture/DESENHO_CONTRATO_EXECUCAO.md)*
