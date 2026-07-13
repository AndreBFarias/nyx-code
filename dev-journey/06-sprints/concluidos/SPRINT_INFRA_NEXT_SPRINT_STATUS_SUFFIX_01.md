# SPRINT INFRA-NEXT-SPRINT-STATUS-SUFFIX-01 -- ROW_PATTERN cego a status/nome com sufixo parentetizado deixa a fila da ONDA-48 invisível

## 0. SPEC (machine-readable)

```yaml
sprint:
  id: INFRA-NEXT-SPRINT-STATUS-SUFFIX-01
  numero: 415
  title: "O ROW_PATTERN de scripts/update_next_sprint.py exige status literal 'PENDENTE' e nome em negrito colado ao pipe; as linhas da tabela do bloco ONDA-48 usam 'PENDENTE (raiz)' etc. e '**NOME** (Vxx: descrição)', entao NENHUMA linha casa e o pipeline escreve 'Nenhuma sprint PENDENTE' com 10 sprints reais na fila"
  onda: 48
  bloco: "48 -- Validação as-user a-fundo (achado de auditoria 2026-07-12)"
  prioridade: ALTA
  tipo: Bugfix / Infra do pipeline de execução de sprints
  dependencias: []
  desbloqueia:
    - "toda a fila ONDA-48 (402/403/406/407 e demais) volta a ser selecionavel pelo pipeline"

  touches:
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/scripts/update_next_sprint.py
      reason: "ROW_PATTERN (linha ~36) exige '\\|\\s*PENDENTE\\s*\\|' na celula de status E '\\*\\*(NOME)\\*\\*\\s*\\|' na celula de nome. As linhas da ONDA-48 usam sufixo parentetizado nas duas celulas, entao a regex retorna zero match no bloco. Relaxar as duas celulas para tolerar sufixo/descrição apos o token, mantendo a captura do ID limpo no grupo 1."
      linhas_alvo: "ROW_PATTERN em ~L36-39 (o único ponto a mudar). _VALID_STATUS em ~L71 NÃO muda."

  creates: []
  removes: []

  forbidden:
    - "Alterar _VALID_STATUS = {'PENDENTE'} -- o sufixo so aparece na CELULA da tabela do MASTER; o Status do arquivo fisico da spec em producao/ e sempre literal 'PENDENTE'. A whitelist do arquivo fisico continua sendo a autoridade final (defesa em profundidade)."
    - "Editar SPRINT_ORDER_MASTER.md, EXECUTAR_SPRINT.md, GAMBIARRAS_POR_SPRINT.md ou reescrever as celulas de status da tabela para virar literal (a convencao documental fica como recomendacao suave, não como fix desta sprint)."
    - "Mudar a ordem de prioridade dos blocos MANUAL_OVERRIDE_ONDA_NN (DESC por numero) nem a logica de find_next_pending/_scan_block_for_pending alem da regex."
    - "Fazer a regex casar linhas de status CONCLUIDA/DESCARTADA/ABSORVIDA (so PENDENTE elegivel)."

  tests:
    - cmd: "python scripts/update_next_sprint.py --show"
      timeout: 30
      esperado: "imprime o prompt da proxima sprint da ONDA-48 (MEMORY-RECALL-REFRESH-01 = 402), NÃO 'Nenhuma sprint PENDENTE'"
    - cmd: "python scripts/update_next_sprint.py"
      timeout: 30
      esperado: "stdout 'proxima sprint: MEMORY-RECALL-REFRESH-01 (24 pendentes)'; EXECUTAR_SPRINT.md passa a apontar 402"
    - cmd: "bash scripts/sprint_invariants.sh"
      timeout: 180
      esperado: "14/14 PASS, FAIL 0"

  acceptance_criteria:
    - "ROW_PATTERN passa a casar as 10 linhas PENDENTE do bloco ONDA-48 (era 0). Comprovado por dry-run que lista os 10 IDs."
    - "python scripts/update_next_sprint.py aponta a proxima sprint da ONDA-48 (MEMORY-RECALL-REFRESH-01) em vez de escrever 'Nenhuma sprint PENDENTE' no EXECUTAR_SPRINT.md."
    - "As 4 specs fisicas ja enfileiradas em producao/ (402 MEMORY-RECALL-REFRESH-01, 403 MODEL-SWAP-REAL-OR-HONEST-01, 406 TUI-INTERNALS-LEAK-01, 407 IDENTITY-GUARD-COPULA-01) tem a linha literal '**Status:** PENDENTE' em linha própria e _read_status devolve 'PENDENTE' para cada uma; corrigir qualquer uma que não devolva."
    - "Nenhuma linha de status CONCLUIDA/DESCARTADA/ABSORVIDA passa a casar por engano (sem falso positivo)."
    - "_VALID_STATUS inalterado; find_next_pending/_scan_block_for_pending inalterados exceto pela regex."
    - "Invariantes 14/14; ruff limpo no script; acentuacao exit 0; spec -> concluidos/."
```

---

**Status:** PENDENTE
**Data criação:** 2026-07-12
**Origem:** Auditoria de sessão 2026-07-12. Achado confirmado no código: `scripts/update_next_sprint.py` gera `# Nenhuma sprint PENDENTE` no `EXECUTAR_SPRINT.md` enquanto o bloco `MANUAL_OVERRIDE_ONDA_48` tem 10 sprints PENDENTE reais. O pipeline de execução fica cego.
**Modelo obrigatório:** modelo de fronteira local, sem subagentes; implementação direta

---

## Problema

O seletor de próxima sprint (`scripts/update_next_sprint.py`) prioriza o bloco `MANUAL_OVERRIDE_ONDA_NN` de maior número (ONDA-48) e aplica `ROW_PATTERN` sobre as linhas da tabela. As linhas da ONDA-48 têm a forma:

```
| 402 | **MEMORY-RECALL-REFRESH-01** (V11: write_memory grava mas recall não atualiza; ...) | ALTA | -- | PENDENTE (raiz) |
```

A regex atual exige duas coisas que essas linhas não têm:

1. Célula de nome colada ao pipe: `\*\*([A-Z][A-Z0-9_\-]+)\*\*\s*\|` — falha porque depois de `**MEMORY-RECALL-REFRESH-01**` vem ` (V11: ...)` antes do `|`.
2. Célula de status literal: `\|\s*PENDENTE\s*\|` — falha porque a célula é `PENDENTE (raiz)`, não `PENDENTE`.

Resultado empírico (verificado nesta auditoria, sem GPU):

- `ROW_PATTERN` atual casa **0** linhas no bloco ONDA-48.
- `find_next_pending()` retorna `None` -> `main()` escreve `# Nenhuma sprint PENDENTE` no `EXECUTAR_SPRINT.md`.
- O `EXECUTAR_SPRINT.md` no working tree hoje começa literalmente com `# Nenhuma sprint PENDENTE`, apesar de haver 10 sprints PENDENTE no bloco ONDA-48 (o próprio cabeçalho do bloco diz `EM ANDAMENTO (10/15)`).

Efeito colateral hoje: o parser só casa 3 linhas legadas (382/383/384 do bloco ONDA-46, com nome limpo e status literal `PENDENTE`), mas os arquivos físicos dessas três não existem em `producao/`, então são puladas por `arquivo ausente` e o resultado final ainda é `None`.

## Causa-raiz

`ROW_PATTERN` foi escrito para o formato antigo de linha (nome em negrito seguido direto do pipe e status literal). O bloco ONDA-48 adotou um estilo mais rico: descrição inline na célula de nome (`**NOME** (Vxx: ...)`) e contexto parentetizado na célula de status (`PENDENTE (raiz)`, `PENDENTE (render TUI)`, `PENDENTE (follow-up)`, etc.). As duas convenções coexistem no MASTER e a regex só entende a antiga.

Ponto importante para o executor: **corrigir só o sufixo de status NÃO resolve.** Foi testado — relaxar apenas a célula de status mantém a linha 402 sem casar, porque a célula de nome também carrega o parêntese. As duas células precisam tolerar sufixo.

## Solução proposta

Relaxar `ROW_PATTERN` nas duas células, preservando a captura do ID limpo no grupo 1 (é ele que vira `SPRINT_<ID>.md` via `sprint_file_name`).

De:

```python
ROW_PATTERN = re.compile(
    r"^\|\s*[A-Z]?\d+\s*\|\s*\*\*([A-Z][A-Z0-9_\-]+)\*\*\s*\|.*\|\s*PENDENTE\s*\|",
    re.MULTILINE,
)
```

Para (candidato recomendado):

```python
ROW_PATTERN = re.compile(
    r"^\|\s*[A-Z]?\d+\s*\|\s*\*\*([A-Z][A-Z0-9_\-]+)\*\*[^|]*\|.*\|\s*PENDENTE\b[^|]*\|",
    re.MULTILINE,
)
```

Duas mudanças mínimas:

- Célula de nome: `\*\*(...)\*\*\s*\|` -> `\*\*(...)\*\*[^|]*\|` — tolera descrição/parêntese após o negrito, até o próximo pipe. O grupo 1 continua limitado a `[A-Z][A-Z0-9_\-]+` (para em espaço ou `(`), então captura o ID limpo.
- Célula de status: `\|\s*PENDENTE\s*\|` -> `\|\s*PENDENTE\b[^|]*\|` — tolera sufixo parentetizado após `PENDENTE` até o pipe. O `\b` impede casar `PENDENTEX`; o `[^|]*` fica dentro da célula.

Convenção documental (recomendação suave, item (b) do achado, fora do escopo de código): ao adicionar novas linhas ao MASTER, manter o status como `PENDENTE` no início da célula e o contexto entre parênteses depois. O parser passa a ser tolerante de qualquer forma — o espírito do projeto é infra resiliente a entrada imperfeita (ADR-031/032). Não reescrever as células existentes nesta sprint.

Não mexer em `_VALID_STATUS = {"PENDENTE"}`: o sufixo só existe na célula da tabela do MASTER; o campo `**Status:**` do arquivo físico da spec é sempre literal `PENDENTE`. A leitura do arquivo físico (`_read_status` + whitelist) permanece como autoridade final e filtra qualquer eventual falso match da regex do MASTER — defesa em profundidade preservada.

## Verificação numérica (medida nesta auditoria, reproduzível sem GPU)

- `grep -c "PENDENTE (" ` no bloco ONDA-48: **10** linhas (402, 403, 406, 407, 408, 409, 410, 411, 413, 414).
- `ROW_PATTERN` atual sobre o bloco ONDA-48: **0** matches. Regex candidata: **10** matches, IDs limpos corretos.
- Primeira sprint elegível após o fix (primeira do bloco com arquivo físico presente e `_read_status == PENDENTE`): **MEMORY-RECALL-REFRESH-01** (402). Confirmado que `producao/SPRINT_MEMORY_RECALL_REFRESH_01.md` existe e `_read_status` devolve `PENDENTE`.
- `count_pending()` (global, sobre o MASTER inteiro): passa de **3** para **24**. É esperado e honesto — reflete o total real de linhas PENDENTE no MASTER. O número aparece só como `Restam N sprints PENDENTE(S)` no cabeçalho do prompt; não altera a seleção. Se o executor julgar o salto confuso, registrar follow-up (não corrigir aqui) para escopar `count_pending` ao bloco ativo — anti-débito, fora do escopo desta sprint.

## Proof-of-work esperado

```bash
# 1. Dry-run do parser: deve listar os 10 IDs da ONDA-48 (antes: [])
python3 - <<'PY'
import re
from pathlib import Path
c = Path("dev-journey/06-sprints/SPRINT_ORDER_MASTER.md").read_text(encoding="utf-8")
blk = re.search(r"MANUAL_OVERRIDE_ONDA_48_START(.*?)MANUAL_OVERRIDE_ONDA_48_END", c, re.DOTALL).group(1)
import importlib.util
s = importlib.util.spec_from_file_location("uns", "scripts/update_next_sprint.py")
m = importlib.util.module_from_spec(s); s.loader.exec_module(m)
print("matches ONDA-48:", m.ROW_PATTERN.findall(blk))   # esperado: 10 IDs
PY

# 2. Seletor real (puro Python, sem ollama/GPU): aponta a proxima da ONDA-48
python scripts/update_next_sprint.py
# esperado stdout: "proxima sprint: MEMORY-RECALL-REFRESH-01 (24 pendentes) [atualizado]"

# 3. EXECUTAR_SPRINT.md deixou de dizer "Nenhuma sprint PENDENTE"
head -1 EXECUTAR_SPRINT.md
# esperado: "# Executar proxima sprint -- MEMORY-RECALL-REFRESH-01"

# 4. As 4 specs fisicas enfileiradas resolvem PENDENTE via _read_status real
python3 - <<'PY'
import importlib.util
from pathlib import Path
s = importlib.util.spec_from_file_location("uns", "scripts/update_next_sprint.py")
m = importlib.util.module_from_spec(s); s.loader.exec_module(m)
prod = Path("dev-journey/06-sprints/producao")
for f in ["SPRINT_MEMORY_RECALL_REFRESH_01.md","SPRINT_MODEL_SWAP_REAL_OR_HONEST_01.md",
          "SPRINT_TUI_INTERNALS_LEAK_01.md","SPRINT_IDENTITY_GUARD_COPULA_01.md"]:
    assert m._read_status(prod/f) == "PENDENTE", f
    print("PENDENTE OK:", f)
PY

# 5. Guardas de qualidade
bash scripts/sprint_invariants.sh                                   # 14/14 PASS, FAIL 0
/home/andrefarias/.local/bin/ruff check scripts/update_next_sprint.py
python3 ~/.config/zsh/scripts/validar-acentuacao.py --paths scripts/update_next_sprint.py dev-journey/06-sprints/producao/SPRINT_INFRA_NEXT_SPRINT_STATUS_SUFFIX_01.md

# 6. Smoke boot (protocolo feedback_smoke_boot.md, quando a GPU liberar --
#    esta mudanca não toca runtime nyx/, so o pipeline de docs)
./run.sh --smoke                                                    # boot ok, exit 0
```

## Critério binário de aceite

- [ ] Dry-run lista os 10 IDs da ONDA-48 (era 0)
- [ ] `python scripts/update_next_sprint.py` aponta MEMORY-RECALL-REFRESH-01, não "Nenhuma sprint PENDENTE"
- [ ] As 4 specs físicas (402/403/406/407) resolvem `PENDENTE` via `_read_status`
- [ ] Sem falso positivo em linhas CONCLUIDA/DESCARTADA/ABSORVIDA
- [ ] `_VALID_STATUS` e a lógica de seleção inalterados fora da regex
- [ ] Invariantes 14/14, ruff limpo, acentuação exit 0; smoke boot ok; spec -> concluidos/

## Riscos

| Risco | Mitigação |
|-------|-----------|
| `[^|]*` na célula de nome capturar ID errado | O grupo 1 é `[A-Z][A-Z0-9_\-]+`, para no primeiro caractere fora da classe (espaço/parêntese); `[^|]*` só consome o resto da célula. Comprovado: findall devolve IDs limpos. |
| Regex passar a casar linha de status não-PENDENTE | `\|\s*PENDENTE\b` exige `PENDENTE` no início da célula; e o arquivo físico (`_read_status` + whitelist `{PENDENTE}`) é a autoridade final. Defesa em profundidade. |
| `count_pending` saltar de 3 para 24 confundir o operador | Valor é só cosmético no cabeçalho; não afeta seleção. Follow-up opcional (escopar ao bloco ativo) fica como anti-débito, fora daqui. |
| Corrigir só o sufixo de status e a ONDA-48 seguir cega | Documentado explicitamente: as duas células precisam do relaxamento (testado). |

## Referências

- BRIEF: `/home/andrefarias/Desenvolvimento/Nyx-Code/VALIDATOR_BRIEF.md` (contratos de runtime, checks universais, arquivos periféricos)
- Arquivo alvo: `scripts/update_next_sprint.py` (`ROW_PATTERN` ~L36, `_VALID_STATUS` ~L71, `find_next_pending`, `_scan_block_for_pending`, `count_pending`, `main`)
- Fila afetada: `dev-journey/06-sprints/SPRINT_ORDER_MASTER.md`, bloco `MANUAL_OVERRIDE_ONDA_48` (linhas ~1204-1242)
- Memória: `feedback_smoke_boot.md` (smoke antes de CONCLUIDA), `feedback_nenhum_debito.md` (achado colateral vira sprint com ID)

---

*"Um parser que só entende o formato de ontem deixa a fila de hoje invisível." -- anônimo*
