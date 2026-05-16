# SPRINT PRODUCAO-CLEANUP-01 — Higiene do diretório `producao/` e filtro de status no `update_next_sprint.py`

## 0. SPEC (machine-readable)

```yaml
sprint:
  id: PRODUCAO-CLEANUP-01
  title: "Mover arquivos ABSORVIDA/DEFERIDA de producao/ e ensinar update_next_sprint.py a ignorar status não-PENDENTE"
  onda: 22
  bloco: 2.10 Higiene
  prioridade: ALTA
  tipo: Infra + Bugfix
  dependencias: []
  desbloqueia: [ERROR-MSG-01, /sprint-ciclo saudável]

  touches:
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/scripts/update_next_sprint.py
      reason: "Script escolhe 'próxima sprint' varrendo producao/. Hoje não filtra Status — pode eleger fantasma ABSORVIDA/DEFERIDA. Precisa ler o campo Status e descartar tudo que não seja PENDENTE."
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/dev-journey/06-sprints/SPRINT_ORDER_MASTER.md
      reason: "Confirmar que os 4 fantasmas já estão marcados ABSORVIDA na tabela e não há discrepância entre master e sistema de arquivos após o mv"
  creates: []
  removes:
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/dev-journey/06-sprints/producao/SPRINT_UX_BUG_02.md
      reason: "Status: ABSORVIDA_POR_UX-BUG-02A/B/C — não deve aparecer em producao/"
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/dev-journey/06-sprints/producao/SPRINT_DEPLOY_01.md
      reason: "Status: ABSORVIDA_POR_DEPLOY-01A/01B"
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/dev-journey/06-sprints/producao/SPRINT_UX_LAYOUT_01.md
      reason: "Status: ABSORVIDA_POR_UX-LAYOUT-01A/01B"
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/dev-journey/06-sprints/producao/SPRINT_TUI_FIX_07_USABILIDADE.md
      reason: "Status: ABSORVIDA_POR_TUI-FIX-07A/B/C"

  n_to_n_pairs:
    - descricao: "Fila real de sprints existe em TRÊS lugares: (a) producao/*.md, (b) SPRINT_ORDER_MASTER.md tabela Onda 22, (c) EXECUTAR_SPRINT.md texto gerado. Após mv, TODOS devem concordar que só há 17 PENDENTES."
      paths:
        - /home/andrefarias/Desenvolvimento/Nyx-Code/dev-journey/06-sprints/producao/
        - /home/andrefarias/Desenvolvimento/Nyx-Code/dev-journey/06-sprints/SPRINT_ORDER_MASTER.md
        - /home/andrefarias/Desenvolvimento/Nyx-Code/EXECUTAR_SPRINT.md

  forbidden:
    - "Usar `rm` ao invés de `git mv` (perde histórico)"
    - "Deletar o arquivo original da sprint monolítica sem preservar em concluidos/ — o histórico de decisão fica"
    - "Filtrar apenas por string 'ABSORVIDA' no update_next_sprint.py (frágil). Ler o campo Status literal e tratar PENDENTE como whitelist."
    - "Adicionar emoji, menção a IA, print em módulos não-autorizados (se precisar mensagem, logger)"
    - "Tocar código em nyx/ — sprint puramente de higiene de docs + script utilitário"

  tests:
    - cmd: "ls dev-journey/06-sprints/producao/SPRINT_UX_BUG_02.md 2>&1 | grep -q 'No such' && echo OK"
      timeout: 5
      deve_passar: true
    - cmd: "python scripts/update_next_sprint.py && grep -q 'ERROR-MSG-01' EXECUTAR_SPRINT.md"
      timeout: 10
      deve_passar: true
    - cmd: "bash scripts/sprint_invariants.sh"
      timeout: 60
      deve_passar: "13/13 PASS — higiene não pode introduzir regressão em código"

  acceptance_criteria:
    - "Os 4 arquivos listados em removes[] não existem mais em producao/"
    - "Todos os 4 existem em concluidos/ (preservados via git mv, histórico intacto)"
    - "ls producao/*.md retorna exatamente 18 arquivos (17 PENDENTE + SPRINT_CTX_04_ACTIVE_PLAN.md DEFERIDA)"
    - "update_next_sprint.py filtra por Status: lê arquivo, descarta qualquer linha que case regex '^(\\*\\*)?Status(\\*\\*)?:\\s*(ABSORVIDA|DEFERIDA|CONCLUIDA)' e só considera PENDENTE"
    - "EXECUTAR_SPRINT.md gerado aponta para ERROR-MSG-01 e conta '17 sprints PENDENTE(S)'"
    - "sprint_invariants.sh segue 13/13"
    - "CTX-04 (DEFERIDA) é ignorado silenciosamente pelo script"
    - "Commit atômico: 'chore(PRODUCAO-CLEANUP-01): move absorvidas e filtra status no update_next_sprint'"
```

---

**Status:** PENDENTE
**Data criação:** 2026-04-21
**Modelo obrigatório:** claude-opus-4-7 (sem subagentes)

---

## Contexto do projeto (snapshot — não referência)

> **ADRs relevantes:**
>
> - ADR-004 Zero Emojis: script de manutenção sem emoji.
> - ADR-005 Anonimato: sem menção a IA em código/doc/commit.
> - ADR-006 PT-BR: acentuação correta em mensagens log do script.
> - ADR-013 Integração Obrigatória: script utilitário fica em `scripts/`, seguindo convenção.
> - ADR-015 Documentação para continuidade: `SPRINT_ORDER_MASTER.md` é fonte única da fila — discrepâncias com filesystem são bugs.
>
> **Estado do sistema (auditado 2026-04-21):**
> - Commit atual: `3e29a4f` (master: "limpa duplicatas em producao/" — limpeza foi parcial).
> - `producao/` contém 22 arquivos `.md`: 17 PENDENTE + 4 ABSORVIDA (resíduo) + 1 DEFERIDA (`CTX-04`).
> - `concluidos/` contém 133 arquivos.
> - `sprint_invariants.sh`: 13/13 PASS.
> - Sprint anterior (3e29a4f): docs consolidation passou mas deixou 4 fantasmas.

---

## Problema

### Sintoma observável

```bash
$ grep -l "ABSORVIDA" dev-journey/06-sprints/producao/*.md
dev-journey/06-sprints/producao/SPRINT_UX_BUG_02.md
dev-journey/06-sprints/producao/SPRINT_DEPLOY_01.md
dev-journey/06-sprints/producao/SPRINT_UX_LAYOUT_01.md
dev-journey/06-sprints/producao/SPRINT_TUI_FIX_07_USABILIDADE.md
```

Cada arquivo tem `Status: ABSORVIDA_POR_...` no topo. O `SPRINT_ORDER_MASTER.md` já registra as absorções. Mas:

1. O arquivo físico segue em `producao/`, contaminando qualquer ferramenta que liste `*.md` daquele diretório para decidir a "próxima PENDENTE".
2. `scripts/update_next_sprint.py` é usado pelo hook `cca` e pelo `/sprint-ciclo`. Se a heurística dele for "primeiro arquivo em ordem alfabética de `producao/`", pode devolver `SPRINT_DEPLOY_01.md` (um fantasma) como próxima — o ciclo automático agenda uma sprint já absorvida.
3. O `PROJECT_SNAPSHOT.md` diz "22 sprints pendentes"; o `EXECUTAR_SPRINT.md` diz "17". A divergência é sintoma desta sujeira.

### Origem

Commit `3e29a4f` prometia "limpa duplicatas em producao/" e de fato removeu alguns, mas deixou estes 4 por descuido. Protocolo anti-débito (GUIDE.md §9.7) exige resolver inline ou materializar — materializamos aqui.

---

## Solução proposta

1. **`git mv` dos 4 fantasmas** de `producao/` → `concluidos/`. O estado `ABSORVIDA` é informação histórica válida; `concluidos/` é o lugar certo (já contém outras sprints com status `ABSORVIDA_POR_...` aprendidos em 2026-04-19).
2. **Hardenizar `update_next_sprint.py`** para ler o campo `Status:` de cada `.md` em `producao/` e tratar `PENDENTE` como whitelist — qualquer outro valor (`ABSORVIDA*`, `DEFERIDA`, `OPCIONAL`, `CONCLUIDA`) é descartado silenciosamente com `logger.info`.
3. **Ao final**, rodar o próprio script e confirmar que `EXECUTAR_SPRINT.md` aponta para `ERROR-MSG-01` e conta 17 pendentes.

---

## Arquivos alvo (paths absolutos)

### `/home/andrefarias/Desenvolvimento/Nyx-Code/scripts/update_next_sprint.py`

**Antes (trecho conceitual — leia o arquivo real antes de editar):**
```python
def _find_next_pending(producao: Path) -> Path | None:
    for p in sorted(producao.glob("SPRINT_*.md")):
        # hoje retorna o primeiro arquivo, sem ler o Status
        return p
    return None
```

**Depois:**
```python
import re

_STATUS_RE = re.compile(r"^\*{0,2}Status\*{0,2}:\s*([A-Z_]+)", re.MULTILINE)
_VALID_STATUS = {"PENDENTE"}  # whitelist explícita

def _read_status(path: Path) -> str:
    """Extrai o primeiro campo Status do arquivo de sprint."""
    try:
        head = path.read_text(encoding="utf-8", errors="replace")[:4000]
    except OSError as exc:
        logger.warning("não foi possível ler %s: %s", path, exc)
        return "DESCONHECIDO"
    match = _STATUS_RE.search(head)
    return match.group(1) if match else "DESCONHECIDO"

def _find_next_pending(producao: Path) -> Path | None:
    for p in sorted(producao.glob("SPRINT_*.md")):
        status = _read_status(p)
        if status in _VALID_STATUS:
            return p
        logger.info("pulando %s (status=%s)", p.name, status)
    return None
```

**Mudanças:**
- Nova função `_read_status(path)` com regex única e tolerância a `**Status**:` ou `Status:`.
- `_find_next_pending` filtra por whitelist `{"PENDENTE"}`.
- Ausência de status explícito → `DESCONHECIDO` → descartado (seguro).
- Logs explicam pulo para facilitar debug futuro.

### `/home/andrefarias/Desenvolvimento/Nyx-Code/dev-journey/06-sprints/producao/SPRINT_{UX_BUG_02,DEPLOY_01,UX_LAYOUT_01,TUI_FIX_07_USABILIDADE}.md`

**Ação:** `git mv <arquivo> ../concluidos/`. Conteúdo intacto.

### `/home/andrefarias/Desenvolvimento/Nyx-Code/dev-journey/06-sprints/SPRINT_ORDER_MASTER.md`

**Ação:** nenhuma mudança de tabela (absorções já documentadas). Adicionar rodapé no bloco 2.10 Higiene quando esta sprint for concluída.

---

## Diff esperado (resumo)

```
+ 0 arquivos criados
~ 1 arquivo modificado  (scripts/update_next_sprint.py, ~20 linhas)
- 0 arquivos removidos  (mv não remove, reloca)
R 4 arquivos movidos    (producao/ -> concluidos/)
+ ~25 linhas líquidas
```

---

## Comandos de verificação (literais, copy-paste)

```bash
cd /home/andrefarias/Desenvolvimento/Nyx-Code

# 1. Antes: snapshot invariantes + inventário
bash scripts/sprint_invariants.sh > /tmp/inv_before.txt 2>&1
FAIL_BEFORE=$(grep -c "^\[FAIL\]" /tmp/inv_before.txt)
echo "FAIL inicial: $FAIL_BEFORE"
ls dev-journey/06-sprints/producao/*.md | wc -l   # esperado agora: 22

# 2. Mover fantasmas (PASSO 2 da implementação)
cd dev-journey/06-sprints
git mv producao/SPRINT_UX_BUG_02.md concluidos/
git mv producao/SPRINT_DEPLOY_01.md concluidos/
git mv producao/SPRINT_UX_LAYOUT_01.md concluidos/
git mv producao/SPRINT_TUI_FIX_07_USABILIDADE.md concluidos/
cd ../..

# 3. Editar scripts/update_next_sprint.py conforme seção "Arquivos alvo"

# 4. Rodar o script; conferir saída
python scripts/update_next_sprint.py
grep -E '^> \*\*|Restam' EXECUTAR_SPRINT.md
# Esperado literal:
#   > Restam **17** sprints PENDENTE(S) na fila.
# e a próxima sprint identificada deve ser ERROR-MSG-01

# 5. Depois: snapshot de regressão
bash scripts/sprint_invariants.sh > /tmp/inv_after.txt 2>&1
FAIL_AFTER=$(grep -c "^\[FAIL\]" /tmp/inv_after.txt)
diff /tmp/inv_before.txt /tmp/inv_after.txt

# 6. Inventário final
ls dev-journey/06-sprints/producao/*.md | wc -l   # esperado: 18
ls dev-journey/06-sprints/concluidos/SPRINT_UX_BUG_02.md   # deve existir
ls dev-journey/06-sprints/producao/SPRINT_UX_BUG_02.md 2>&1 | grep -q 'No such' && echo OK
```

---

## Critério binário de aceite (IA executora)

- [ ] 4 arquivos movidos via `git mv` (histórico preservado)
- [ ] `ls producao/*.md | wc -l` retorna 18
- [ ] `update_next_sprint.py` importa a função nova e filtra por whitelist
- [ ] `python scripts/update_next_sprint.py` executa sem erro
- [ ] `EXECUTAR_SPRINT.md` aponta para `ERROR-MSG-01` e menciona "17"
- [ ] `sprint_invariants.sh` continua 13/13 (FAIL_AFTER <= FAIL_BEFORE)
- [ ] Teste artificial: criar arquivo `producao/SPRINT_TESTE_FANTASMA.md` com `Status: ABSORVIDA` em uma linha — rodar o script — esperado: script pula e aponta ERROR-MSG-01; apagar o arquivo de teste antes do commit
- [ ] Commit atômico com mensagem `chore(PRODUCAO-CLEANUP-01): move absorvidas e filtra status no update_next_sprint`
- [ ] `SPRINT_ORDER_MASTER.md` registra CONCLUIDA com hash do commit

---

## Guardrails anti-engodo (obrigatórios)

- Não use `mv` puro — precisa ser `git mv` para o histórico acompanhar.
- Não edite o conteúdo dos 4 arquivos movidos (relocação literal).
- Não introduza dependência nova no script (`re` já é stdlib; manter).
- Se o script atual já filtrar Status de alguma forma: mostrar o `grep` literal do arquivo antes e depois; se a lógica existir mas estiver quebrada, consertar-na ao invés de reescrever monolítica.
- O teste artificial do fantasma é obrigatório — prova que o filtro funciona de verdade.

---

## Catálogo de gambiarras proibidas

Ver `dev-journey/08-templates/GAMBIARRAS_POR_SPRINT.md` §"Catálogo Universal". Leitura antes de implementar.

### Gambiarras específicas

1. **Filtrar por nome de arquivo ao invés de Status.** "Se o arquivo tem '02' no nome, é absorvido." Proibido — frágil, quebra quando novas absorções aparecerem.
2. **Regex só para `ABSORVIDA`.** `PENDENTE` como whitelist é invariante mais robusta — `DEFERIDA`, `OPCIONAL`, etc também precisam ser pulados.
3. **Deletar o arquivo ao invés de mover.** `rm` destrói histórico e contexto da decisão de absorção; `git mv` preserva.
4. **Ajustar contagem hardcoded em outro arquivo.** Não mexer em `PROJECT_SNAPSHOT.md` aqui — ele é atualizado na sprint seguinte (INVENTORY-SYNC-01).

---

## Proof-of-work obrigatório (4 passos)

```bash
# PASSO 1
bash scripts/sprint_invariants.sh > /tmp/inv_before.txt 2>&1
FAIL_BEFORE=$(grep -c "^\[FAIL\]" /tmp/inv_before.txt)

# PASSO 2 — git mv + edição do script (ver "Arquivos alvo")

# PASSO 3
bash scripts/sprint_invariants.sh > /tmp/inv_after.txt 2>&1
FAIL_AFTER=$(grep -c "^\[FAIL\]" /tmp/inv_after.txt)

# PASSO 4
diff /tmp/inv_before.txt /tmp/inv_after.txt
[ "$FAIL_AFTER" -le "$FAIL_BEFORE" ] || { echo "REGRESSÃO"; exit 1; }
```

Colar output bruto dos 4 passos + output do teste artificial de fantasma.

---

## Validação humana (checklist do usuário)

```bash
cd /home/andrefarias/Desenvolvimento/Nyx-Code

git log --oneline -1
git show --stat HEAD
# esperado: chore(PRODUCAO-CLEANUP-01): ...
# 4 arquivos renomeados producao/->concluidos/, 1 arquivo modificado scripts/update_next_sprint.py

ls dev-journey/06-sprints/producao/*.md | wc -l      # 18
ls dev-journey/06-sprints/concluidos/SPRINT_UX_BUG_02.md   # existe

python scripts/update_next_sprint.py
head -10 EXECUTAR_SPRINT.md   # deve citar ERROR-MSG-01 e "17"

ls dev-journey/06-sprints/concluidos/SPRINT_PRODUCAO_CLEANUP_01.md    # esta sprint foi movida
ls dev-journey/06-sprints/producao/SPRINT_PRODUCAO_CLEANUP_01.md 2>&1 | grep -q 'No such' && echo OK
```

---

## Riscos

| Risco | Mitigação |
|-------|-----------|
| `update_next_sprint.py` usa estrutura interna diferente do pseudocódigo apresentado | Ler o arquivo real antes de editar; preservar nomes de funções públicas existentes |
| Algum consumidor externo (hook `cca`, `/sprint-ciclo`) parseia nome de arquivo com `SPRINT_DEPLOY_01.md` literal | Buscar com `grep -rn SPRINT_DEPLOY_01 .claude/ ~/.config/zsh/` antes do commit; se houver referência, migrar para ID `DEPLOY-01A` |
| Sprint monolítica absorvida tem conteúdo único que não foi transposto para A/B/C | Auditar rapidamente comparando tabelas de "absorvidas" no SPRINT_ORDER_MASTER — se houver perda, abrir sprint de recuperação (zero follow-up) |
| `concluidos/` já tem arquivo homônimo (conflito de nome) | `ls concluidos/SPRINT_UX_BUG_02.md` antes do mv; se existir, renomear o recém-movido com sufixo `_ABSORVIDA` |

---

*"Quem não arruma a casa não recebe visita." -- provérbio popular*
