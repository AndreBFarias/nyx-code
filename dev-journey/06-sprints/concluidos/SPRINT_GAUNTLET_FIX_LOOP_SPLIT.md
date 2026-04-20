# SPRINT GAUNTLET-FIX-LOOP-SPLIT — CTX-08 usa caminho antigo `nyx/agent/loop.py` (foi split)

## 0. SPEC (machine-readable)

```yaml
sprint:
  id: GAUNTLET-FIX-LOOP-SPLIT
  title: "CTX-08 do gauntlet usa target hardcoded que não existe mais após split de loop.py"
  onda: 22
  bloco: 2.6
  prioridade: CRÍTICA
  tipo: Bugfix
  dependencias: []
  desbloqueia: [VALIDATE-ONDA-20]

  touches:
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/scripts/gauntlet/nyx_gauntlet.py
      reason: "CTX-08 assert target 'nyx/agent/loop.py' in r._cache -- arquivo foi split em nyx/agent/loop/ (pacote)"
      linhas_alvo: "2807"

  creates: []
  removes: []

  n_to_n_pairs: []

  forbidden:
    - "Tocar nyx/agent/repomap.py -- feature RepoMap.invalidate() funciona; bug é no teste"
    - "Ignorar a regressão -- pass rate 100% -> 90% é bloqueante (gate de produção)"
    - "Escolher qualquer string que 'provavelmente está no cache' -- tem que ser arquivo real e estável"
    - "Tocar arquivos fora do touches"
    - "Adicionar emoji, menção a IA"

  tests:
    - cmd: "./run.sh --gauntlet --only contexto"
      timeout: 240
      esperado: "10/10 APROVADO"
    - cmd: "./run.sh --gauntlet --only rapido"
      timeout: 120
      esperado: "11/11"

  acceptance_criteria:
    - "CTX-08 OK (pass rate contexto 10/10)"
    - "Report: Gate de Produção APROVADO"
    - "Nenhuma regressão em fase rapido"
    - "RepoMap.invalidate() continua intocado (git diff nyx/agent/repomap.py vazio)"
    - "FAIL invariantes não regride; check #13 continua PASS"
```

---

**Status:** CONCLUIDA (commit dd29b98)
**Data criação:** 2026-04-20
**Origem:** achado colateral durante execução de **VALIDATE-ONDA-20** (Rodada 1). Gauntlet `contexto` rodou 9/10 com REGRESSÃO (100%→90%). CTX-08 `RepoMap invalidate` FAIL. Investigação: `scripts/gauntlet/nyx_gauntlet.py:2807` hardcoded `target = "nyx/agent/loop.py"`, arquivo inexistente — foi split em `nyx/agent/loop/_core.py` + `_iteration.py` + `_types.py` + `_constants.py` por refactor posterior (AUDIT-FIX-05 ou DEBT-01, ver blame).
**Modelo obrigatório:** claude-opus-4-7 (sem subagentes)

---

## Contexto

`CTX-08` valida a feature `RepoMap.invalidate(path)`: põe arquivo no cache via `build()`, chama `invalidate()`, e verifica que a chave sumiu. Para isso, escolhe um arquivo-alvo estável do projeto. O alvo original era `nyx/agent/loop.py`.

Após o split de `loop.py` em pacote `nyx/agent/loop/`, a chave `"nyx/agent/loop.py"` simplesmente não existe no cache → `assert target in r._cache` falha → `except Exception` captura AssertionError, marca FAIL, erro vazio (assert sem msg).

Feature `RepoMap.invalidate()` em `nyx/agent/repomap.py` está íntegra — validado programaticamente:

```
>>> r.build(); target = 'main.py'
>>> target in r._cache  # True
>>> r.invalidate(str(PROJECT_ROOT / target))
>>> target in r._cache  # False
```

---

## Solução proposta

Trocar o alvo para um arquivo que existe na nova estrutura e é estável: `nyx/agent/loop/_core.py`.

```python
target = "nyx/agent/loop/_core.py"
```

Uma linha, troca cirúrgica.

### Alternativas consideradas (descartadas)

1. **`main.py`** — arquivo raiz, estável, porém curto demais; futura refatoração pode levá-lo a `nyx/__main__.py`. Risco de repetir o bug.
2. **`nyx/agent/repomap.py`** (o próprio testado) — auto-referência ruim, se alguém renomear o módulo o teste some junto.
3. **Lista dinâmica** (`target = next(iter(r._cache))`) — perde determinismo do teste. `invalidate` deveria testar um caminho conhecido, não "qualquer um".
4. **Corrigir `RepoMap.invalidate` para aceitar path antigo** — impossível, arquivo não existe.

`_core.py` foi escolhido porque:
- Existe pós-split (confirmado: `ls nyx/agent/loop/_core.py`)
- É o "núcleo" do pacote (contém classe `AgentLoop` principal), pouco provável de ser renomeado
- Convenção `_core.py` é estável em pacotes Python

---

## Diff esperado

```
~ 1 arquivo modificado (scripts/gauntlet/nyx_gauntlet.py)
+ 1 / - 1 linha
```

---

## Comandos de verificação

```bash
bash scripts/sprint_invariants.sh > /tmp/inv_before.txt 2>&1
FAIL_BEFORE=$(grep -c "^\[FAIL\]" /tmp/inv_before.txt)

# Fix: sed -i 's|"nyx/agent/loop.py"|"nyx/agent/loop/_core.py"|' scripts/gauntlet/nyx_gauntlet.py

./run.sh --smoke                            # boot ok (check #13)
./run.sh --gauntlet --only contexto          # esperado 10/10
./run.sh --gauntlet --only rapido            # esperado 11/11

bash scripts/sprint_invariants.sh > /tmp/inv_after.txt 2>&1
FAIL_AFTER=$(grep -c "^\[FAIL\]" /tmp/inv_after.txt)
diff /tmp/inv_before.txt /tmp/inv_after.txt

# Evidências de não-regressão de feature
git diff nyx/agent/repomap.py   # vazio
```

---

## Critério binário de aceite

- [ ] CTX-08 PASS (10/10 em contexto)
- [ ] `git diff nyx/agent/repomap.py` vazio
- [ ] `FAIL_AFTER <= FAIL_BEFORE`
- [ ] `./run.sh --smoke` → `boot ok`
- [ ] Gate de Produção APROVADO no report

---

## Gambiarras específicas

1. **Trocar target para `nyx/cli.py` "só porque tá lá"** — cli.py é alvo de ADR-024 e pode ser reorganizado; escolher um alvo de teste ruim repete o bug em 6 meses.
2. **Envolver em try/AssertionError silencioso** — mascara o problema sem corrigir.
3. **Remover o assert** — perde a garantia de que o arquivo estava de fato no cache antes do invalidate; teste vira ritual.

---

## Proof-of-work obrigatório

- Report do gauntlet `contexto` com CTX-08 OK e pass rate 10/10.
- `git diff scripts/gauntlet/nyx_gauntlet.py` mostrando 1 linha alterada.
- `git diff nyx/agent/repomap.py` vazio.

---

## Riscos

| Risco | Mitigação |
|-------|-----------|
| `_core.py` também ser renomeado no futuro | Convenção Python estável; se ocorrer, mesmo processo: sprint-nova cirúrgica |
| Outros testes do gauntlet fazem hardcode de path ausente | Grep pós-fix: `grep -rn "nyx/agent/loop.py" scripts/gauntlet/` → deve retornar 0 |

---

*"Teste que referencia código morto testa fantasma." -- máxima do panteão Luna*
