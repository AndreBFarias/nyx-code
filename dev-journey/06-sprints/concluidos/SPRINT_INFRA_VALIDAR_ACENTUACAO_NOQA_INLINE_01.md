## 0. SPEC (machine-readable)

```yaml
sprint:
  id: INFRA-VALIDAR-ACENTUACAO-NOQA-INLINE-01
  title: "Validator externo de acentuacao respeita marker inline igual ao hook local (backward-compat)"
  onda: 29
  prioridade: MÉDIA
  tipo: Bugfix
  dependencias: [INFRA-MASTER-DEBT-MARKERS-01]
  desbloqueia: []

  touches:
    - path: ~/.config/zsh/scripts/validar-acentuacao.py
      reason: "Adicionar funcao has_noqa_marker + filtro inline em check_file()"  <!-- noqa-acento -->
      autorizacao: "Usuario autorizou explicitamente em 2026-05-22 ao pedir esta sprint para fechar follow-up implicita"

  creates: []

  forbidden:
    - "Remover backward-compat do substring check existente (linhas 94-96)"
    - "Modificar regex de detecção (CORRECOES / _PARES)"
    - "Adicionar dependencias externas"
    - "Adicionar emoji"
    - "Quebrar comportamento para outros projetos do usuario"

  tests:
    - cmd: "python3 ~/.config/zsh/scripts/validar-acentuacao.py --paths dev-journey/06-sprints/SPRINT_ORDER_MASTER.md"
      timeout: 10
      deve_passar: true
    - cmd: "bash scripts/sprint_invariants.sh"
      timeout: 30
      deve_passar: true
    - cmd: "./run.sh --smoke"
      timeout: 60
      deve_passar: true

  acceptance_criteria:
    - "Funcao has_noqa_marker(line) adicionada ao script externo"  <!-- noqa-acento -->
    - "Backward-compat: linha com substring 'noqa-acento' antiga continua passando"
    - "Novo: linha com regex preciso `<!-- noqa-acento -->` tambem passa"
    - "Validador roda em MASTER (com markers da sprint 203) e retorna rc=0"
    - "Validador continua bloqueando linha sem marker quando ha violacao real"
    - "Smoke + invariantes 14/14 PASS"
```

---

# Sprint INFRA-VALIDAR-ACENTUACAO-NOQA-INLINE-01

**Status:** PENDENTE
**Data criacao:** 2026-05-22
**Modelo obrigatorio:** claude-opus-4-7 (sem subagentes)

---

## Contexto

> Sprint 201 (commit e161e0f) introduziu marker `<!-- noqa-acento -->` inline no hook local `scripts/hooks/pre-commit` via regex precisa `(<!--|#|//)\s*noqa-acento(\s|-->|$)`.
> Sprint 203 (commit 1527a47) aplicou 46 markers em 44 linhas + removeu excecoes globais redundantes.
> Restou 1 follow-up implicita catalogada pela 203: o validador externo `~/.config/zsh/scripts/validar-acentuacao.py` (script global compartilhado, fora do repo) ainda usa heuristica substring antiga (`"noqa-acento" in line`), que casa em literais documentados (palavras em backticks, strings tmux) gerando 27 violacoes residuais que deveriam ser silenciadas.
> Esta sprint refina o validador para usar regex precisa igual ao hook local, mantendo backward-compat com o substring antigo.

---

## Problema

`~/.config/zsh/scripts/validar-acentuacao.py` linhas 94-96 (heuristica atual):

```python
if "# noqa-acento" in line or "noqa-acento" in line:
    fixed_lines.append(line)
    continue
```

Funciona mas e generico demais:
- Match em qualquer ocorrencia do substring, mesmo em texto narrativo entre backticks.
- Nao casa o padrao usado pelo hook local desde a 201 (`<!-- noqa-acento -->`).
- Resultado: validador externo reporta 27 violacoes em arquivos cobertos pelos markers do hook local.

Risco da remocao direta: script e global (compartilhado com possiveis outros projetos do usuario fora do Nyx-Code). Solucao backward-compat: aceitar ambos.

---

## Solucao proposta

### 1. Adicionar funcao helper  <!-- noqa-acento -->

Apos linha 80 (area de helpers):

```python
_NOQA_PRECISE_RE = re.compile(r"(<!--|#|//)\s*noqa-acento(\s|-->|$)")


def has_noqa_marker(line: str) -> bool:
    """Backward-compat: aceita marker preciso (regex) OU substring antiga.

    Marker preciso: <!-- noqa-acento -->, # noqa-acento, // noqa-acento.
    Substring antiga: qualquer ocorrencia de 'noqa-acento' ou '# noqa-acento'
    na linha (forma legada anterior a sprint 201 do Nyx-Code).
    """
    if _NOQA_PRECISE_RE.search(line):
        return True
    if "# noqa-acento" in line or "noqa-acento" in line:
        return True
    return False
```

### 2. Substituir linhas 94-96 (check substring antigo)

ANTES:
```python
if "# noqa-acento" in line or "noqa-acento" in line:
    fixed_lines.append(line)
    continue
```

DEPOIS:
```python
if has_noqa_marker(line):
    fixed_lines.append(line)
    continue
```

### 3. Adicionar filtro inline no loop de matches (linhas 99-112)

Mesmo se a linha nao tem `continue` cedo (caso a linha tenha multiplas violacoes), filtrar dentro do loop:

ANTES:
```python
for errada, correta in CORRECOES.items():
    pattern = re.compile(...)
    for m in pattern.finditer(line):
        prefix = line[: m.start()]
        # ... skip semantico ...
        results.append((i, m.group(), correta, line.strip()))
```

DEPOIS:
```python
for errada, correta in CORRECOES.items():
    pattern = re.compile(...)
    for m in pattern.finditer(line):
        if has_noqa_marker(line):
            continue  # marker presente — silencia esta linha
        prefix = line[: m.start()]
        # ... skip semantico ...
        results.append((i, m.group(), correta, line.strip()))
```

(O filtro duplicado e defesa em profundidade: linhas 94-96 ja capturam, mas garantir que mesmo se logica futura mudar, o filtro inline cobre.)

---

## Diff esperado

```
~ 1 arquivo modificado FORA do repo (autorizado pelo usuario)
+ ~12 linhas (funcao + 2 callsites)  <!-- noqa-acento -->
```

---

## Comandos de verificacao

```bash
# 1. Backup do script global antes de modificar
cp ~/.config/zsh/scripts/validar-acentuacao.py \
   ~/.config/zsh/scripts/validar-acentuacao.py.bak-SPRINT204

# 2. Estado pre: 27 violacoes esperadas
python3 ~/.config/zsh/scripts/validar-acentuacao.py --paths \
    dev-journey/06-sprints/SPRINT_ORDER_MASTER.md \
    Checkpoint.md \
    README.md 2>&1 | wc -l

# 3. Aplicar patch (3 etapas acima)

# 4. Estado pos: zero violacoes esperadas
python3 ~/.config/zsh/scripts/validar-acentuacao.py --paths \
    dev-journey/06-sprints/SPRINT_ORDER_MASTER.md \
    Checkpoint.md \
    README.md
# esperado: exit 0, sem output

# 5. Backward-compat: criar arquivo de teste com marker antigo
echo "validacao usada aqui # noqa-acento" > /tmp/legacy_marker.md
python3 ~/.config/zsh/scripts/validar-acentuacao.py --paths /tmp/legacy_marker.md
# esperado: exit 0 (substring antiga ainda funciona)
rm /tmp/legacy_marker.md

# 6. Forward-compat: arquivo de teste com marker novo
echo "validacao usada aqui <!-- noqa-acento -->" > /tmp/new_marker.md
python3 ~/.config/zsh/scripts/validar-acentuacao.py --paths /tmp/new_marker.md
# esperado: exit 0 (regex preciso pega o novo)
rm /tmp/new_marker.md

# 7. Sem marker: continua bloqueando
echo "validacao usada aqui sem marker" > /tmp/no_marker.md
python3 ~/.config/zsh/scripts/validar-acentuacao.py --paths /tmp/no_marker.md
# esperado: exit 1, reporta violacao
rm /tmp/no_marker.md

# 8. Smoke + invariantes
./run.sh --smoke
bash scripts/sprint_invariants.sh
```

---

## Criterio binario de aceite

- [ ] Backup do script criado em `~/.config/zsh/scripts/validar-acentuacao.py.bak-SPRINT204`
- [ ] Funcao `has_noqa_marker` adicionada  <!-- noqa-acento -->
- [ ] Linhas 94-96 substituidas por chamada a `has_noqa_marker`
- [ ] Filtro inline no loop de matches (linha ~104)
- [ ] Cenario 4 (estado pos no MASTER): exit 0, zero violacoes
- [ ] Cenario 5 (backward-compat antigo): exit 0
- [ ] Cenario 6 (forward-compat novo): exit 0
- [ ] Cenario 7 (sem marker): exit 1, bloqueia
- [ ] Smoke + invariantes 14/14 PASS
- [ ] Nenhuma violacao de forbidden[]

---

## Riscos

| Risco | Mitigacao |
|-------|-----------|
| Script global afetar outros projetos | Backward-compat preserva comportamento existente; substring antigo continua valido |
| Patch quebrar import circular ou erro de sintaxe | Backup criado antes (linha 1 do verify); `python3 -c "import validar-acentuacao"` se torna teste implicito via `cenarios 5-7` |
| Funcao colidir com nome existente no script | Validar via `grep "def has_noqa_marker" ~/.config/zsh/scripts/validar-acentuacao.py` antes |

---

## Pos-condicao

Validador externo de acentuacao fica granular puro igual ao hook local. Os 27 falsos-positivos catalogados pela sprint 203 (literais em backticks, strings tmux) desaparecem. Backward-compat garantida — outros projetos do usuario que possam usar marker antigo nao sao afetados.

---

*"Backward-compat e o respeito que se deve ao passado." -- principio refactor Nyx-Code.*
