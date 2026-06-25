# SPRINT CI-MODEL-ASSERT-FIX-01 -- smoke do ci.yml assere modelo errado e acopla o CI a um model especifico

## 0. SPEC (machine-readable)

```yaml
sprint:
  id: CI-MODEL-ASSERT-FIX-01
  title: "ci.yml:109 `assert DEFAULT_MODEL == 'qwen3:4b'` mas o DEFAULT_MODEL real e 'qwen2.5-coder:3b' (defaults.py:55) -> o job smoke-tests FALHA; alem disso travar o CI num model literal contraria a meta de troca facil de model (ONDA-47)"
  onda: 46
  bloco: "46 -- Saneamento de CI & Working Tree + achados da Onda de Validação 1"
  prioridade: MEDIA
  tipo: Bugfix / CI
  dependencias: []
  desbloqueia: []

  touches:
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/.github/workflows/ci.yml
      reason: "step 'Testar config' (linha ~105-112): `assert DEFAULT_MODEL == 'qwen3:4b'` esta errado (real e 'qwen2.5-coder:3b', defaults.py:55) -> smoke-tests FALHA sempre. Trocar por uma checagem de SANIDADE robusta (DEFAULT_MODEL e string nao-vazia no formato ollama `nome:tag`), decouplando o CI do model especifico -- coerente com ADR-031/ONDA-39 (fonte unica) e com a meta de troca facil de model (ONDA-47)."
      linhas_alvo: "~108-112 (bloco python do step 'Testar config')"

  creates: []
  removes: []

  forbidden:
    - "Trocar o literal errado por OUTRO literal especifico (ex.: 'qwen2.5-coder:3b') -- volta a acoplar o CI ao model e quebra de novo no proximo swap; usar checagem de formato"
    - "Remover a checagem de OLLAMA_PORT == 11435 (essa esta correta, manter)"
    - "Tocar os outros steps/jobs (lint, temas, utils de cor, ci-summary)"
    - "Adicionar nome de provedor IA por extenso (hook anti-IA + o proprio check de anonimato do ci.yml linha 51 bloqueiam)"

  tests:
    - cmd: "extrair o snippet python do step 'Testar config' e rodar com o DEFAULT_MODEL real"
      timeout: 60
      esperado: "passa (hoje: AssertionError em qwen3:4b)"
    - cmd: "trocar mentalmente DEFAULT_MODEL para outro model valido (ex.: 'llama3.2:3b') -> a checagem de formato ainda passa (prova o decoupling)"
      timeout: 30
      esperado: "robusto a swap"
    - cmd: "bash scripts/sprint_invariants.sh"
      timeout: 180
      esperado: "14/14 PASS"
    - cmd: "yamllint .github/workflows/ci.yml (se disponivel) + python yaml.safe_load"
      timeout: 30
      esperado: "YAML valido"

  acceptance_criteria:
    - "A assercao de modelo no smoke vira checagem de sanidade/formato (string nao-vazia, formato `nome:tag`), nao um literal especifico"
    - "O step 'Testar config' passa com o DEFAULT_MODEL atual (qwen2.5-coder:3b)"
    - "Robusto a troca de model (nao quebra se o default mudar para outro model valido)"
    - "OLLAMA_PORT == 11435 mantido; demais steps intactos"
    - "Invariantes 14/14; spec -> concluidos/"
```

---

**Status:** CONCLUIDA (cc695de)
**Data criação:** 2026-06-24
**Origem:** Wave 0 (AUDIT_2026_06_24.md, dimensao 6) -- divergencia suspeita CI x DEFAULT_MODEL, confirmada lendo ci.yml:109 (`'qwen3:4b'`) vs defaults.py:55 (`'qwen2.5-coder:3b'`).
**Modelo obrigatorio:** modelo principal local, sem subagentes; implementação direta

---

## Problema

`.github/workflows/ci.yml`, job `smoke-tests`, step "Testar config":

```python
from nyx.config.defaults import DEFAULT_MODEL, OLLAMA_PORT
assert DEFAULT_MODEL == 'qwen3:4b'        # <-- ERRADO: real e 'qwen2.5-coder:3b'
assert OLLAMA_PORT == 11435               # ok
```

`nyx/config/defaults.py:55` define `DEFAULT_MODEL = "qwen2.5-coder:3b"` (ADR-031). Logo o `assert` levanta `AssertionError` e o job `smoke-tests` (required na intencao do CI) FALHA em todo push/PR. Pior: mesmo se corrigido para o literal certo, volta a quebrar no primeiro swap de model -- exatamente o que a ONDA-47 (troca facil de model) quer viabilizar.

---

## Causa-raiz

O smoke foi escrito quando o default era `qwen3:4b` (ou por engano) e cravou o literal, acoplando o CI ao model. ONDA-39 ja ensinou a licao do hardcode de model (INFRA-MODEL-DEFAULT-SINGLE-SOURCE-01); o CI ficou de fora.

---

## Solucao proposta

Trocar a assercao de igualdade literal por checagem de sanidade/formato:

```python
from nyx.config.defaults import DEFAULT_MODEL, OLLAMA_PORT
assert isinstance(DEFAULT_MODEL, str) and DEFAULT_MODEL, 'DEFAULT_MODEL vazio'
assert ':' in DEFAULT_MODEL, 'DEFAULT_MODEL deve ter formato nome:tag'
assert OLLAMA_PORT == 11435
print('Config defaults: OK (modelo=%s)' % DEFAULT_MODEL)
```

Isso valida que o default existe e tem formato de model ollama, sem acoplar a um nome -- robusto a swap.

---

## Proof-of-work esperado

```bash
# rodar o snippet do step com o DEFAULT_MODEL atual
python -c "from nyx.config.defaults import DEFAULT_MODEL, OLLAMA_PORT; assert isinstance(DEFAULT_MODEL,str) and DEFAULT_MODEL; assert ':' in DEFAULT_MODEL; assert OLLAMA_PORT==11435; print('OK', DEFAULT_MODEL)"
bash scripts/sprint_invariants.sh          # 14/14 PASS
python3 -c "import yaml; yaml.safe_load(open('.github/workflows/ci.yml'))"  # YAML valido
```

---

## Criterio binario de aceite

- [ ] assercao de modelo vira checagem de formato (sem literal especifico)
- [ ] step passa com o DEFAULT_MODEL atual e seria robusto a swap
- [ ] OLLAMA_PORT mantido; demais steps intactos
- [ ] invariantes 14/14; spec -> concluidos/

---

## Riscos

| Risco | Mitigacao |
|-------|-----------|
| Checagem fraca demais (passa lixo) | exigir formato `nome:tag` (`:` presente) + string nao-vazia cobre erro real de config |
| YAML do bloco python quebrar a indentacao | `yaml.safe_load` apos o fix |

---

*"Travar o teste num modelo e prender a porta que voce acabou de querer abrir." -- anonimo*
