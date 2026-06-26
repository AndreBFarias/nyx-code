## 0. SPEC (machine-readable)

```yaml
sprint:
  id: EXEC-CONTRACT-TOOL-MATCH-01
  title: "Contrato G1: rejeitar tool que contradiz o pedido (pedido de leitura -> tool de escrita)"
  onda: 48
  prioridade: ALTA
  tipo: Feature
  dependencias: [EXEC-CONTRACT-NO-HALLUCINATED-RESULT-01, LOOP-RESULT-NOT-AS-INPUT-01]
  desbloqueia: [SEQ-EDIT-ENFORCE-EDITFILE-01]

  touches:
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/agent/intent.py
      reason: "adicionar wants_read_only(user_input) -- sinal de re-emissao (pedido de ler/listar/buscar SEM verbo de mutação)"
      linhas_alvo: "fim do arquivo (apos wants_save_memory)"
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/agent/loop/_iteration.py
      reason: "guard de tool-match antes de executar tool mutante, nos 2 caminhos; rejeita 1x + re-emite"
      linhas_alvo: "_execute_tool_calls (apos echo-reject da 400); _execute_parsed_action (idem); reset do flag"
  creates: []
  removes: []

  forbidden:
    - "Adicionar emoji"
    - "Usar 'print()' fora de cli.py/output.py"
    - "Mencao a IA proprietaria"
    - "Usar a intenção como GATE unico (DESENHO §6: intenção e so SINAL de re-emissao 1x, nunca bloqueio definitivo)"
    - "Rejeitar quando o pedido tem QUALQUER verbo de mutação (crie/escreva/edite) -- so quando e claramente leitura pura"
    - "Tocar a apresentacao da 399, o sanitize da 397, a anti-recursao da 400, gating, write_memory, cascata OOM"

  tests:
    - cmd: "./run.sh --gauntlet --only rapido"
      timeout: 300
      deve_passar: true
    - cmd: "./run.sh --gauntlet --only fs_arbitrary"
      timeout: 300
      deve_passar: true

  acceptance_criteria:
    - "Pedido de leitura pura (liste/leia/mostre/busque SEM crie/escreva/edite) + tool mutante (write_file/create_file/edit_file/multi_edit/patch) -> rejeita 1x + re-emite hint"
    - "Pedido com verbo de mutação (ou ambíguo) não e rejeitado (alta precisão, baixo falso-positivo)"
    - "Rejeicao no maximo 1x/turno (flag); MAX_ITERATIONS e a rede"
    - "wants_read_only e usado SO como sinal de re-emissao, nunca gate definitivo"
    - "Proof runtime: 'liste os arquivos em ~/Desktop' não cria mais novo_arquivo.txt -- usa list_files e mostra a lista real (V03 morto)"
    - "Gauntlet rapido E fs_arbitrary 100%"
```

---

# Sprint EXEC-CONTRACT-TOOL-MATCH-01 — Contrato G1: tool casa o pedido

**Status:** PENDENTE
**Data criação:** 2026-06-26
**Modelo obrigatório:** claude-opus-4-7 (executor-sprint autorizado pelo dono nesta onda)

---

## Contexto do projeto (snapshot — não referência)

> **ADRs relevantes (inline):**
> - **ADR-032 A INFRA CARREGA O MODELO:** quando o 3b escolhe a ferramenta errada (pediram LISTAR, ele vai ESCREVER), a infra detecta a contradição e re-emite -- não deixa criar lixo nem alucinar.
> - **ADR-033 A CADEIA NUNCA QUEBRA.** ADR-009, ADR-001, ADR-006, ADR-005, ADR-024, ADR-014, ADR-010.
>
> **Estado (2026-06-26):** `qwen2.5-coder:3b`, Ollama :11435, proxy :11436. ONDA-48 fase raiz: 399 `f0883a1`, 397 `6c61f1d`, 400 `b1a17fe` CONCLUIDAS. Desenho: `dev-journey/02-architecture/DESENHO_CONTRATO_EXECUCAO.md` (G1, ponto A, "tool-match"). Achado: `dev-journey/07-reports/AUDIT_VALIDACAO_2026_06_26.md` (V03).

---

## Problema

**Achado V03 WRONG-TOOL-SELECTED [ALTA]:**
- pedir **LISTAR** `~/Desktop` -> o 3b chama `write_file` criando `novo_arquivo.txt` vazio e **alucina** a lista ("novo_arquivo.txt, outro_arquivo.txt" inexistentes).
- (caso secundário, fora de escopo desta sprint: buscar "TODO" -> chama `glob *.py`. Ambas read-tools, contradição mais sutil; pertence à família da 409 search.)

**Causa-raiz:** o loop executa **a tool que o modelo escolheu sem checar** se ela casa o pedido. Pediram leitura (não-mutante), o modelo chama escrita (mutante) -- e a infra cria um arquivo lixo + deixa o modelo alucinar a lista. A contradição **leitura-pedida vs escrita-executada** é estrutural e de alto risco (destrutiva: cria/sobrescreve arquivo que ninguém pediu).

---

## Solução proposta

**G1 (ponto A), alta precisão, intenção como SINAL de re-emissão (1x):**
1. `nyx/agent/intent.py`: `wants_read_only(user_input)` -> True quando o pedido tem verbo de leitura/listagem/busca **E não tem** verbo de mutação (crie/escreva/edite/gere/delete). Reusa `INTENT_CODE_KEYWORDS` (mutação) já existente.
2. `nyx/agent/loop/_iteration.py`: antes de executar uma tool **mutante** (`write_file`/`create_file`/`edit_file`/`multi_edit`/`patch`), se `wants_read_only(self._original_input)` -> rejeitar **1x** + re-emitir hint ("o pedido é de leitura; use read_file/list_files/search, não escreva").

Princípio (DESENHO §6): a intenção é só **sinal** de re-emissão (1x), nunca gate definitivo. A âncora dura é **mutante vs não-mutante** (estrutural). Alta precisão: só dispara quando o pedido é leitura PURA (sem nenhum verbo de mutação).

---

## Arquivos alvo (paths absolutos)

### `/home/andrefarias/Desenvolvimento/Nyx-Code/nyx/agent/intent.py`

#### Edit 1 — `wants_read_only` (no fim do arquivo, após `wants_save_memory`)

**Depois (adicionar):**
```python
# EXEC-CONTRACT-TOOL-MATCH-01: verbos de leitura/listagem/busca (não-mutantes).
_READ_LIST_PATTERN = re.compile(
    r"\b("
    r"leia|leu|ler|le\b|"
    r"liste|listar|lista|"
    r"mostre|mostrar|mostra|exiba|exibir|exibe|"
    r"veja|ver|vejo|olhe|olhar|"
    r"quais|quantos|"
    r"abra|abrir|abre|cat|ls|"
    r"busque|buscar|busca|procure|procurar|procura|grep|encontre|encontrar"
    r")\b",
    re.IGNORECASE,
)

# Verbos de remoção (complementam INTENT_CODE_KEYWORDS para "mutação").
_DELETE_PATTERN = re.compile(
    r"\b(delete|deletar|delet[ae]|remova|remover|remove|apague|apagar|apaga)\b",
    re.IGNORECASE,
)


def wants_mutation(user_input: str) -> bool:
    """True se o pedido tem verbo de escrita/geracao/edicao/remoção."""
    if not user_input:
        return False
    return bool(INTENT_CODE_KEYWORDS.search(user_input)) or bool(
        _DELETE_PATTERN.search(user_input)
    )


def wants_read_only(user_input: str) -> bool:
    """True quando o pedido e claramente de LEITURA/listagem/busca e não pede
    mutação -- sinal de re-emissao quando o modelo chama uma tool mutante
    (EXEC-CONTRACT-TOOL-MATCH-01). Alta precisão: leitura presente E mutação
    ausente. Ambiguo (ambos, ou nenhum) -> False (não re-emite a toa)."""
    if not user_input:
        return False
    return bool(_READ_LIST_PATTERN.search(user_input)) and not wants_mutation(user_input)
```

---

### `/home/andrefarias/Desenvolvimento/Nyx-Code/nyx/agent/loop/_iteration.py`

#### Edit 2 — import + constantes

# Localização: o import de intent ja existe (`from nyx.agent.intent import classify as _classify_intent`)
**Antes:**
```python
from nyx.agent.intent import classify as _classify_intent
```
**Depois:**
```python
from nyx.agent.intent import classify as _classify_intent
from nyx.agent.intent import wants_read_only as _wants_read_only
```

# Constantes -- junto de `_ECHO_REJECT_HINT` (classe `_IterationMixin`)
**Depois (adicionar):**
```python
    # EXEC-CONTRACT-TOOL-MATCH-01 (V03): tools que MUTAM o FS. Se o pedido e
    # leitura pura e o modelo chama uma destas, e contradicao destrutiva.
    _MUTATING_TOOLS = frozenset(
        {"write_file", "create_file", "edit_file", "multi_edit", "patch"}
    )
    _TOOL_MATCH_HINT = (
        "O pedido é de LEITURA/listagem, não de escrita. Não crie nem sobrescreva "
        "arquivo. Use a ferramenta certa: list_files para listar, read_file para "
        "ler, search para buscar. Refaça com a ferramenta de leitura."
    )
```

#### Edit 3 — helper de guard (método de `_IterationMixin`, junto de `_should_reject_done`)

**Depois (adicionar):**
```python
    def _tool_match_reject(self, name: str) -> str | None:
        """EXEC-CONTRACT-TOOL-MATCH-01: hint a re-emitir quando o modelo chama uma
        tool MUTANTE mas o pedido era leitura pura. None se não deve rejeitar.
        Rejeita no maximo 1x/turno (flag _tool_match_rejected)."""
        if getattr(self, "_tool_match_rejected", False):
            return None
        if name not in self._MUTATING_TOOLS:
            return None
        if _wants_read_only(getattr(self, "_original_input", "") or ""):
            return self._TOOL_MATCH_HINT
        return None
```

#### Edit 4 — reset do flag em `_init_done_guard`

# Localização: `_init_done_guard`, junto de `self._done_rejected = False`
**Antes:**
```python
        self._done_rejected = False
```
**Depois:**
```python
        self._done_rejected = False
        # EXEC-CONTRACT-TOOL-MATCH-01: arma o guard de tool-match (rejeição 1x/turno).
        self._tool_match_rejected = False
```

#### Edit 5 — aplicar o guard em `_execute_tool_calls` (apos o echo-reject da 400)

# Localização aproximada: logo apos o bloco `if _echo_reject:` (da 400), antes de `if self._on_tool:`
**Antes:**
```python
            if _echo_reject:
                logger.warning("[loop] arg é puro eco de resultado anterior: %s", name)
                self._session.add_tool_call(name, args, self._ECHO_REJECT_HINT)
                continue

            if self._on_tool:
                self._on_tool(name, args)
```
**Depois:**
```python
            if _echo_reject:
                logger.warning("[loop] arg é puro eco de resultado anterior: %s", name)
                self._session.add_tool_call(name, args, self._ECHO_REJECT_HINT)
                continue

            # EXEC-CONTRACT-TOOL-MATCH-01 (V03): pediram leitura, o modelo chama
            # escrita -> rejeita 1x + re-emite (não cria lixo nem deixa alucinar).
            tm_hint = self._tool_match_reject(name)
            if tm_hint:
                self._tool_match_rejected = True
                logger.warning("[loop] tool-match: pedido de leitura, tool mutante %s", name)
                self._session.add_tool_call(name, args, tm_hint)
                continue

            if self._on_tool:
                self._on_tool(name, args)
```

#### Edit 6 — aplicar o guard em `_execute_parsed_action` (apos o echo-reject da 400)

# Localização aproximada: apos o bloco `if _echo_reject:` (da 400) no parser fallback
**Antes:**
```python
        if _echo_reject:
            logger.warning("[loop] arg é puro eco (parser): %s", tool_name)
            self._session.add_tool_call(tool_name, remapped, self._ECHO_REJECT_HINT)
            return None

        if self._on_tool:
            self._on_tool(tool_name, remapped)
```
**Depois:**
```python
        if _echo_reject:
            logger.warning("[loop] arg é puro eco (parser): %s", tool_name)
            self._session.add_tool_call(tool_name, remapped, self._ECHO_REJECT_HINT)
            return None

        # EXEC-CONTRACT-TOOL-MATCH-01 (V03): idem caminho nativo, no parser fallback.
        tm_hint = self._tool_match_reject(tool_name)
        if tm_hint:
            self._tool_match_rejected = True
            logger.warning("[loop] tool-match (parser): pedido leitura, tool mutante %s", tool_name)
            self._session.add_tool_call(tool_name, remapped, tm_hint)
            return None

        if self._on_tool:
            self._on_tool(tool_name, remapped)
```

---

## Diff esperado (resumo)

```
~ 2 arquivos modificados (intent.py, loop/_iteration.py)
+ ~70 linhas líquidas
```

---

## Comandos de verificação (literais, copy-paste)

```bash
# 1. Estatica + acentuacao
python -m ruff check nyx/
python3 ~/.config/zsh/scripts/validar-acentuacao.py --paths nyx/agent/intent.py nyx/agent/loop/_iteration.py

# 2. Unit sanity (função pura -- inline)
venv/bin/python -c "
from nyx.agent.intent import wants_read_only as r, wants_mutation as m
print('leitura pura:', r('liste os arquivos em ~/Desktop'), m('liste os arquivos em ~/Desktop'))      # True False
print('mutação:', r('crie um arquivo x.py'), m('crie um arquivo x.py'))                                  # False True
print('ambíguo (ambos):', r('liste os arquivos e crie um resumo'))                                       # False (tem mutação)
print('chat:', r('explique recursividade'))                                                              # False (sem verbo leitura)
"
# ESPERADO: leitura pura True False; mutação False True; ambíguo False; chat False

# 3. Gauntlet
./run.sh --gauntlet --only rapido
./run.sh --gauntlet --only fs_arbitrary

# 4. PROOF RUNTIME-REAL as-user (V03):
printf '%s\n' '{"type":"request","content":"liste os arquivos em ~/Desktop"}' \
  | NYX_AUTO_APPROVE=1 ./run.sh --headless 2>/dev/null
# ESPERADO: list_files chamado, lista REAL dos arquivos sob Resultado:; files_modified=0
#           (não criou novo_arquivo.txt). Confirmar que nenhum arquivo foi criado em ~/Desktop.
```

---

## Critério binário de aceite (IA executora)

- [ ] `wants_read_only`/`wants_mutation` em `intent.py`; alta precisão (leitura presente E mutação ausente)
- [ ] Guard aplicado nos DOIS caminhos, após o echo-reject da 400; rejeição 1x/turno (flag resetado em `_init_done_guard`)
- [ ] Unit sanity colado (leitura pura True, mutação/ambíguo/chat False)
- [ ] Proof runtime as-user colado: listar não cria mais arquivo lixo (V03 morto); `ls ~/Desktop` antes/depois inalterado
- [ ] `ruff` limpo, acentuação rc=0, `FAIL_AFTER <= FAIL_BEFORE`
- [ ] Gauntlet `rapido` E `fs_arbitrary` 100%
- [ ] `SPRINT_ORDER_MASTER.md` marca 398 CONCLUIDA; spec movida para `concluidos/`
- [ ] NÃO commitar; NÃO tocar Checkpoint.md

---

## Guardrails anti-engodo (obrigatórios)

NÃO marcar concluída se:
- `wants_read_only` dispara em pedido com verbo de mutação (falso-positivo -> bloqueia escrita legítima).
- Virou gate definitivo (rejeição >1x/turno, loop).
- Proof runtime não colado, ou um arquivo lixo foi criado mesmo assim.

Se algo falhar: `[SPRINT 398] BLOQUEADA: <motivo 1 linha>`.

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

- **Falso-positivo de leitura:** `wants_read_only` DEVE exigir mutação ausente. O teste "ambíguo" (liste E crie) deve dar False.
- **Gate em vez de sinal:** a rejeição é 1x/turno (flag). Se o 3b insistir, FORCE_DONE/MAX_ITER encerram (não loop infinito).
- **Pegar a tool errada certa:** só MUTATING_TOOLS disparam. read/list/search/glob entre si (read-tool vs read-tool) NÃO é escopo (é a família 409).

---

## Validação humana (checklist do usuário)

```bash
cd /home/andrefarias/Desenvolvimento/Nyx-Code
git --no-pager show --stat HEAD
ls ~/Desktop > /tmp/desktop_antes.txt
./run.sh   # peca: "liste os arquivos em ~/Desktop"
ls ~/Desktop > /tmp/desktop_depois.txt
diff /tmp/desktop_antes.txt /tmp/desktop_depois.txt   # ESPERADO: vazio (nenhum arquivo criado)
ls dev-journey/06-sprints/concluidos/SPRINT_EXEC_CONTRACT_TOOL_MATCH_01.md  # existe
```

---

## Riscos

| Risco | Mitigação |
|-------|-----------|
| Pedido de leitura que legitimamente leva a escrever (raro: "liste e salve a lista num arquivo") | Tem verbo de mutação (salve) -> `wants_mutation` True -> não rejeita. Alta precisão. |
| Verbo de leitura ausente mas pedido é leitura ("o que tem na pasta X?") | Não dispara (False) -> não rejeita. Falso-negativo é preferível a falso-positivo (não bloqueia nada legítimo). |
| 3b insiste na tool mutante após re-emissão | Rejeição 1x; FORCE_DONE/MAX_ITER encerram. |

---

*"A ferramenta errada não erra sozinha -- a infra que a deixa agir erra junto." -- princípio de execução (dev-journey/02-architecture/DESENHO_CONTRATO_EXECUCAO.md)*
