# SPRINT STATUS-FILTER-HARDEN-01 — Hardenização do filtro de Status em update_next_sprint.py

## 0. SPEC (machine-readable)

```yaml
sprint:
  id: STATUS-FILTER-HARDEN-01
  title: "Robustecer regex de Status no update_next_sprint.py para ignorar Status embeddado em ADR/código e alertar quando sprint não tem metadata própria"
  onda: 22
  bloco: 2.10 Higiene
  prioridade: MÉDIA
  tipo: Bugfix + Infra
  dependencias: [PRODUCAO-CLEANUP-01]
  desbloqueia: []

  touches:
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/scripts/update_next_sprint.py
      reason: "_read_status() usa regex que pega o PRIMEIRO match de '**Status:**' em qualquer parte do arquivo — inclusive dentro de blocos YAML/código/ADR embedded. Resultado: SPRINT_VISION_01.md inadvertidamente reportava status='ACEITO' que era o ADR-022 embedded no corpo da sprint. Restringir busca ao bloco de metadata canônico (entre '```' pós-YAML e '# Sprint <ID>')."
      linhas_alvo: "40-70 (função _read_status e constantes _STATUS_RE, _VALID_STATUS)"
  creates: []
  removes: []

  n_to_n_pairs:
    - descricao: "Contrato de formato de sprint vive no SPRINT_TEMPLATE_V2.md. Se o script assume que '**Status:** PENDENTE' está na região entre YAML-close e '# Sprint', o template também precisa documentar isso explicitamente (e rejeitar sprints sem metadata)."
      paths:
        - /home/andrefarias/Desenvolvimento/Nyx-Code/scripts/update_next_sprint.py
        - /home/andrefarias/Desenvolvimento/Nyx-Code/dev-journey/08-templates/SPRINT_TEMPLATE_V2.md

  forbidden:
    - "Deletar/suprimir sprints com metadata ausente — o script deve LOGAR warning claro e pular, jamais silenciar com 'DESCONHECIDO' genérico"
    - "Expandir whitelist para aceitar 'ACEITO', 'APROVADO' etc — só PENDENTE passa; outros são estados terminais"
    - "Hard-code paths absolutos — continuar usando PROJECT_ROOT / Path(__file__)"
    - "Adicionar emoji, menção a IA"
    - "Tocar em código de nyx/ — sprint é 100% script utilitário + 1 doc template"
    - "Relaxar o proof-of-work do template (Proof-of-work obrigatório) para não obrigar metadata"

  tests:
    - cmd: "python scripts/update_next_sprint.py"
      timeout: 10
      deve_passar: "aponta próxima sprint PENDENTE válida; pula apenas sprints com status != PENDENTE explícito OU sem metadata, com mensagem clara indicando motivo"
    - cmd: "python -c 'import re; from scripts.update_next_sprint import _read_status; from pathlib import Path; assert _read_status(Path(\"dev-journey/06-sprints/producao/SPRINT_VISION_01.md\")) == \"PENDENTE\"'"
      timeout: 5
      deve_passar: true
    - cmd: "python -c 'from scripts.update_next_sprint import _read_status; from pathlib import Path; import tempfile; f=Path(tempfile.mkstemp(suffix=\".md\")[1]); f.write_text(\"## 0. SPEC\\n\\n```yaml\\n...\\n```\\n\\n---\\n\\n# Sprint TESTE — título\\n\"); assert _read_status(f) == \"SEM_METADATA\"'"
      timeout: 5
      deve_passar: true
    - cmd: "bash scripts/sprint_invariants.sh"
      timeout: 60
      deve_passar: "13/13 PASS"

  acceptance_criteria:
    - "_read_status() lê apenas a região entre fim do bloco YAML (primeiro '```' fechando) e linha '# Sprint' — ignora Status embedded em ADR/código citado"
    - "Arquivos sem metadata retornam status = 'SEM_METADATA' (não 'DESCONHECIDO'), com mensagem de log distinguindo os dois casos"
    - "Log inclui hint acionável: 'sprint X sem metadata — adicione **Status:** PENDENTE após o bloco YAML de 0. SPEC'"
    - "whitelist continua = {'PENDENTE'}; nenhuma expansão"
    - "SPRINT_TEMPLATE_V2.md ganha seção curta '## Bloco de metadata (obrigatório após 0. SPEC)' documentando os 3 campos canônicos"
    - "SPRINT_VISION_01.md (que foi fixado inline pela sprint anterior) continua passando"
    - "Qualquer sprint nova que não siga o template é detectada pelo script no próximo run"
    - "Commit atômico 'fix(STATUS-FILTER-HARDEN-01): regex do update_next_sprint lê só o bloco metadata e alerta quando ausente'"
```

---

**Status:** PENDENTE
**Data criação:** 2026-04-21
**Modelo obrigatório:** claude-opus-4-7 (sem subagentes)

---

## Contexto do projeto (snapshot — não referência)

> **ADRs relevantes:**
>
> - ADR-015 Documentação para continuidade: metadata da sprint é parte do contrato — sem ela, o ciclo automático não funciona.
> - Meta-regra #6: evidência empírica > hipótese. Script atual pegava `ACEITO` de ADR embedded em VISION-01 — regex ingênuo leu a primeira ocorrência ignorando contexto semântico.
>
> **Estado do sistema (auditado 2026-04-21 durante orquestração pós-TUI-CLEANUP-01):**
> - Commit atual: após `4238526` + correções inline de 6 arquivos com metadata ausente (DEPLOY-02, UX-BUG-03, UX-EXTRA-01, VISION-01, VISION-02, VISION-03).
> - `update_next_sprint.py` implementado em PRODUCAO-CLEANUP-01 (commit `767e871`). Regex atual: `r"^(?:>\s*)?\*{0,2}Status:?\*{0,2}:?\s*([A-Z][A-Z0-9_\-]*)"` com `re.MULTILINE`, tolerância a blockquote e asteriscos variados.
> - Bug observado: `re.search` retorna o PRIMEIRO match em TODO o buffer (até 8000 chars). SPRINT_VISION_01.md cita ADR-022 embedded com `**Status:** ACEITO` na linha 70 (dentro de bloco markdown citado) — regex pegou e devolveu `ACEITO`.

---

## Problema

### Sintoma observável

```bash
$ python scripts/update_next_sprint.py 2>&1 | grep pulando
[update_next_sprint] pulando SPRINT_CTX_04_ACTIVE_PLAN.md (status=OPCIONAL)
[update_next_sprint] pulando SPRINT_DEPLOY_02.md (status=DESCONHECIDO)
[update_next_sprint] pulando SPRINT_UX_BUG_03.md (status=DESCONHECIDO)
[update_next_sprint] pulando SPRINT_UX_EXTRA_01.md (status=DESCONHECIDO)
[update_next_sprint] pulando SPRINT_VISION_01.md (status=ACEITO)
```

### Análise por caso

**Caso 1 (DEPLOY-02, UX-BUG-03, UX-EXTRA-01, VISION-02, VISION-03):** arquivo não tem bloco de metadata próprio — o regex fracassa e retorna `DESCONHECIDO`. Comportamento defensivo correto, mas a mensagem não orienta o autor do arquivo.

**Caso 2 (VISION-01):** arquivo contém `**Status:** ACEITO` dentro do corpo de um ADR-022 citado inline como exemplo. Regex pegou o primeiro match e devolveu o status do ADR — que é informação alienígena à sprint. Silencia completamente uma sprint PENDENTE legítima.

### Causa técnica

`_STATUS_RE.search(head)` busca em todo o buffer (até 8000 chars). Isso:
- Não distingue "metadata da sprint" (região canônica) de "Status embedded em texto/código citado".
- Não alerta quando o arquivo não segue o template.

### Correção inline aplicada (sprint anterior)

Os 6 arquivos foram corrigidos inline adicionando bloco metadata. Mas a **causa raiz** (regex ingênuo) continua viva. Próxima sprint nova que por engano citar um ADR com `**Status:**` vai sofrer o mesmo bug.

---

## Solução proposta

1. **Restringir a janela de busca** em `_read_status()`:
   - Ler o arquivo
   - Localizar o PRIMEIRO `# Sprint <ID> —` (heading de nível 1 que abre o corpo da sprint)
   - Buscar `**Status:**` APENAS na região **antes** desse heading
   - Se o heading não existe ou não está nas primeiras 8000 chars, a busca global é fallback com warning
2. **Distinguir dois status inválidos** com mensagens diferentes:
   - `SEM_METADATA`: regex não encontrou nenhum `**Status:**` na região canônica → log hint "adicione bloco metadata após 0. SPEC"
   - `<STATUS_NAO_PENDENTE>`: status explícito mas diferente de PENDENTE (ex: CONCLUIDA, ABSORVIDA, DEFERIDA, OPCIONAL) → log literal do valor
3. **Documentar o contrato** no `SPRINT_TEMPLATE_V2.md`: seção curta "Bloco de metadata (obrigatório)" fixando a estrutura que o script exige.

---

## Arquivos alvo (paths absolutos)

### `/home/andrefarias/Desenvolvimento/Nyx-Code/scripts/update_next_sprint.py`

**Antes (trecho conceitual — ler o arquivo real):**
```python
_STATUS_RE = re.compile(
    r"^(?:>\s*)?\*{0,2}Status:?\*{0,2}:?\s*([A-Z][A-Z0-9_\-]*)",
    re.MULTILINE,
)
_VALID_STATUS = {"PENDENTE"}

def _read_status(path: Path) -> str:
    try:
        head = path.read_text(encoding="utf-8", errors="replace")[:8000]
    except OSError as exc:
        logger.warning("não foi possível ler %s: %s", path, exc)
        return "DESCONHECIDO"
    match = _STATUS_RE.search(head)
    return match.group(1) if match else "DESCONHECIDO"
```

**Depois:**
```python
_STATUS_RE = re.compile(
    r"^(?:>\s*)?\*{0,2}Status:?\*{0,2}:?\s*([A-Z][A-Z0-9_\-]*)",
    re.MULTILINE,
)
# Heading de nível 1 que abre o corpo da sprint — marca fim da região de metadata.
# Aceita "# Sprint <ID> — ..." e "# Sprint <ID>: ..." para tolerância.
_SPRINT_HEADING_RE = re.compile(
    r"^#\s+Sprint\s+[A-Z][A-Z0-9_\-]+",
    re.MULTILINE,
)
_VALID_STATUS = {"PENDENTE"}

def _read_status(path: Path) -> str:
    """Extrai o Status da região canônica de metadata da sprint.

    Região canônica = início do arquivo até o primeiro heading '# Sprint <ID>'.
    Isso evita que Status embedded em ADR/código citado no corpo da sprint
    seja confundido com o Status da sprint em si (bug detectado em
    SPRINT_VISION_01.md, 2026-04-21).
    """
    try:
        text = path.read_text(encoding="utf-8", errors="replace")[:8000]
    except OSError as exc:
        logger.warning("não foi possível ler %s: %s", path, exc)
        return "DESCONHECIDO"

    heading = _SPRINT_HEADING_RE.search(text)
    region = text[: heading.start()] if heading else text

    match = _STATUS_RE.search(region)
    if match:
        return match.group(1)

    # Distingue ausência de metadata (template violado) de erro de IO.
    logger.warning(
        "sprint %s sem campo Status na região de metadata — "
        "adicione '**Status:** PENDENTE' entre o bloco YAML (0. SPEC) e o heading "
        "'# Sprint <ID>', conforme SPRINT_TEMPLATE_V2.md",
        path.name,
    )
    return "SEM_METADATA"
```

**Mudanças:**
- Nova constante `_SPRINT_HEADING_RE` marca o fim da região de metadata.
- `_read_status` restringe a busca ao prefixo antes do heading.
- Separa estados `SEM_METADATA` (template violado) de `DESCONHECIDO` (erro IO).
- Log de warning com hint acionável direto no log.

### `/home/andrefarias/Desenvolvimento/Nyx-Code/dev-journey/08-templates/SPRINT_TEMPLATE_V2.md`

**Antes:** template tem YAML de 0. SPEC seguido direto por `---` e `# Sprint <ID> — Título` + bloco metadata opcionalmente.

**Depois:** adicionar seção curta explícita:

```markdown
## Bloco de metadata (OBRIGATÓRIO — após 0. SPEC, antes de "# Sprint")

O `scripts/update_next_sprint.py` lê o Status APENAS desta região. Colocar Status dentro de bloco YAML, dentro de ADR citado, ou depois do heading `# Sprint <ID>` é ignorado (o script não encontra e devolve `SEM_METADATA`).

Forma canônica, literalmente:
```
---

**Status:** PENDENTE
**Data criação:** YYYY-MM-DD
**Modelo obrigatório:** claude-opus-4-7 (sem subagentes)

---

# Sprint <ID> — Título
```

Valores aceitos de Status: `PENDENTE` (único que vai para a fila), `CONCLUIDA`, `ABSORVIDA_POR_<outro>`, `DEFERIDA`, `OPCIONAL`.
```

**Mudanças:**
- Documenta explicitamente o contrato que o script exige.
- Lista valores aceitos com semântica de cada um.

---

## Diff esperado (resumo)

```
+ 0 arquivos criados
~ 2 arquivos modificados (update_next_sprint.py, SPRINT_TEMPLATE_V2.md)
- 0 arquivos removidos
+ ~35 linhas líquidas
```

---

## Comandos de verificação (literais, copy-paste)

```bash
cd /home/andrefarias/Desenvolvimento/Nyx-Code

# 1. Antes
bash scripts/sprint_invariants.sh > /tmp/inv_before.txt 2>&1

# 2. Implementar

# 3. Rodar script e conferir ausência de DESCONHECIDO e ACEITO
python scripts/update_next_sprint.py 2>&1
# esperado: pula CTX_04 (OPCIONAL), zero DESCONHECIDOs, aponta próxima PENDENTE

# 4. Teste de regressão com arquivo sem metadata
TMPDIR=$(mktemp -d)
cat > "$TMPDIR/SPRINT_FAKE.md" <<'EOF'
## 0. SPEC

```yaml
sprint: id: FAKE
```

---

# Sprint FAKE — teste
EOF
python -c "import sys; sys.path.insert(0,'scripts'); from update_next_sprint import _read_status; from pathlib import Path; print(_read_status(Path('$TMPDIR/SPRINT_FAKE.md')))"
# esperado: SEM_METADATA
rm -rf "$TMPDIR"

# 5. Teste de regressão com Status embedded em ADR
TMPDIR=$(mktemp -d)
cat > "$TMPDIR/SPRINT_EMBEDDED.md" <<'EOF'
## 0. SPEC

```yaml
sprint: id: EMBED
```

---

**Status:** PENDENTE

---

# Sprint EMBED — com ADR embedded

Exemplo de ADR citado:
```markdown
# ADR-FAKE
**Status:** ACEITO
```
EOF
python -c "import sys; sys.path.insert(0,'scripts'); from update_next_sprint import _read_status; from pathlib import Path; print(_read_status(Path('$TMPDIR/SPRINT_EMBEDDED.md')))"
# esperado: PENDENTE (ignorou o ACEITO embedded)
rm -rf "$TMPDIR"

# 6. Depois
bash scripts/sprint_invariants.sh > /tmp/inv_after.txt 2>&1
diff /tmp/inv_before.txt /tmp/inv_after.txt
```

---

## Critério binário de aceite (IA executora)

- [ ] `_read_status` só lê a região antes do heading `# Sprint <ID>`
- [ ] Arquivo sem metadata retorna `SEM_METADATA` + log com hint acionável
- [ ] Arquivo com Status embedded em ADR retorna o Status CORRETO da sprint (não o embedded)
- [ ] Output do script diferencia "status=SEM_METADATA" de "status=<outro>"
- [ ] Whitelist continua = `{"PENDENTE"}` — não expandiu
- [ ] `SPRINT_TEMPLATE_V2.md` ganha seção "Bloco de metadata (OBRIGATÓRIO)" com forma literal e valores aceitos
- [ ] `python scripts/update_next_sprint.py` continua apontando `COMPLETER-ARGS-01` (ou o próximo PENDENTE) corretamente
- [ ] `sprint_invariants.sh` 13/13
- [ ] Dois testes de regressão (arquivo-temporário sem metadata / com ADR embedded) passam
- [ ] Commit atômico `fix(STATUS-FILTER-HARDEN-01): regex do update_next_sprint lê só o bloco metadata e alerta quando ausente`

---

## Guardrails anti-engodo (obrigatórios)

- Não relaxe a whitelist — `ACEITO`, `APROVADO`, `EM_PROGRESSO` são estados terminais ou intermediários, nenhum vai para a fila de execução.
- Não aceite "DESCONHECIDO" como saída — ou é erro de IO (mensagem explícita), ou é SEM_METADATA (mensagem de hint), ou é status válido. Três caminhos, três logs distintos.
- Não delete o fallback de busca global — apenas degrade para warning quando a região canônica não existe.
- Não introduza dependência externa (`yaml`, `marko`, etc) — `re` basta.
- Template atualizado precisa ser LINHA A LINHA o que o script espera, para servir como referência de copy-paste.

---

## Catálogo de gambiarras proibidas

Ver `dev-journey/08-templates/GAMBIARRAS_POR_SPRINT.md` §"Catálogo Universal".

### Gambiarras específicas

1. **Expandir whitelist** para aceitar `ACEITO`. Disfarça o bug.
2. **Regex mais guloso** (ex: `^\*\*Status:\*\*\s+PENDENTE$`) — quebra arquivos com formato válido mas ligeiramente diferente (ex: `**Status**: PENDENTE`).
3. **Silenciar warnings** de `SEM_METADATA` (achando que é barulho). Warning é feature: sprint nova sem metadata deve ser detectada cedo.
4. **Usar `yaml.safe_load` para parsear o bloco `## 0. SPEC`** — viola ADR (dependência extra para algo que `re` resolve).
5. **Hardcode de paths de arquivo** no teste de regressão — usar `tempfile`.

---

## Proof-of-work obrigatório (4 passos)

```bash
bash scripts/sprint_invariants.sh > /tmp/inv_before.txt 2>&1
FAIL_BEFORE=$(grep -c '^\[FAIL\]' /tmp/inv_before.txt)

# --- edit script + edit template ---

bash scripts/sprint_invariants.sh > /tmp/inv_after.txt 2>&1
FAIL_AFTER=$(grep -c '^\[FAIL\]' /tmp/inv_after.txt)
diff /tmp/inv_before.txt /tmp/inv_after.txt
[ "$FAIL_AFTER" -le "$FAIL_BEFORE" ] || { echo REGRESSÃO; exit 1; }
```

Colar:
- output de `python scripts/update_next_sprint.py` ANTES e DEPOIS (mostrando que `DESCONHECIDO`/`ACEITO` falsos somem após fix em sprints repetindo o padrão).
- output dos 2 testes de regressão (arquivo temp sem metadata → SEM_METADATA; arquivo temp com ADR embedded → PENDENTE).
- diff dos invariantes.

---

## Validação humana (checklist do usuário)

```bash
cd /home/andrefarias/Desenvolvimento/Nyx-Code

git log --oneline -1
git show --stat HEAD

# Script não deve mais mostrar DESCONHECIDO
python scripts/update_next_sprint.py 2>&1 | grep DESCONHECIDO && echo "BUG" || echo "ok"

# Template tem seção obrigatória
grep -A3 'Bloco de metadata' dev-journey/08-templates/SPRINT_TEMPLATE_V2.md | head -5

# Fila aponta próxima sprint real
head -6 EXECUTAR_SPRINT.md
```

---

## Riscos

| Risco | Mitigação |
|-------|-----------|
| Sprint legítima tem heading `# Sprint <ID>` seguido de bloco metadata dentro do corpo (padrão atípico) | A regra atual (metadata entre YAML e heading) é convenção histórica do projeto — 130+ sprints seguem. Se aparecer exceção, registrar como achado colateral e padronizar |
| Novo regex `_SPRINT_HEADING_RE` falha para sprints com título que usa `—` (em-dash) vs `-` (hífen) | Regex `^#\s+Sprint\s+[A-Z]...` casa ambos (não depende do separador título) |
| `SEM_METADATA` warning polui output em CI | Log em `INFO` ou `WARNING`, não `ERROR`; CI não falha por warning. Redirecionável se necessário |
| Teste de regressão com tempfile vaza entre test runs | `shutil.rmtree` no teardown (o comando de verificação faz rm -rf) |
| Alguém adiciona sprint com Status na linha 1 (antes de `## 0. SPEC`) | Região antes do heading ainda captura — preserva compatibilidade; template recomenda posição canônica mas flexibilidade preserva |

---

*"Ferramenta que engana silenciosamente é pior que ferramenta que quebra alto." -- Dijkstra (adaptado)*
