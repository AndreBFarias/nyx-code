## 0. SPEC (machine-readable)

```yaml
sprint:
  id: INFRA-HOOK-LOCAL-WIRING-01
  title: "Hook global invoca pre-commit local em commits dentro de Nyx-Code (fecha defense-in-depth)"
  onda: 29
  prioridade: ALTA
  tipo: Infra
  dependencias: [INFRA-SANITIZER-WORKING-TREE-GUARD-01]
  desbloqueia: []

  touches:
    - path: ~/.config/git/hooks/pre-commit
      reason: "Adicionar bloco no topo que detecta repo Nyx-Code e invoca scripts/hooks/pre-commit local"
      autorizacao: "Usuário autorizou explicitamente em 2026-05-22 ao pedir esta sprint para fechar guard defense-in-depth"

  creates:
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/scripts/hooks/test_global_wiring.sh
      reason: "Teste end-to-end: simula commit dentro do repo, confirma que guard local foi invocado"

  forbidden:
    - "Modificar outros hooks globais (commit-msg, pre-push) — só pre-commit"
    - "Quebrar hooks globais para outros projetos do usuário"
    - "Tornar core.hooksPath específico do projeto (decisão de design: detecção runtime via topo do hook global, sem alterar config)"
    - "Adicionar emoji"
    - "Bypass do hook global para Nyx-Code (a chamada ao hook local é ADICIONAL, não substitutiva)"

  tests:
    - cmd: "bash scripts/hooks/test_global_wiring.sh"
      timeout: 30
      deve_passar: true
    - cmd: "bash scripts/sprint_invariants.sh"
      timeout: 30
      deve_passar: true
    - cmd: "./run.sh --smoke"
      timeout: 60
      deve_passar: true

  acceptance_criteria:
    - "Hook global tem bloco no topo que detecta repo Nyx-Code via `git rev-parse --show-toplevel` casando com path absoluto do projeto"
    - "Quando dentro do Nyx-Code: invoca `scripts/hooks/pre-commit` local; se este retornar exit≠0, hook global retorna o mesmo exit (bloqueia commit)"
    - "Quando FORA do Nyx-Code: hook global continua com comportamento existente (zero regressão para outros projetos)"
    - "Teste empírico: commit fake com diff que ataca glifos é bloqueado pelo hook global via cadeia hook-global → hook-local → check_sanitizer_attack.py"
    - "Smoke + invariantes 14/14 PASS"
```

---

# Sprint INFRA-HOOK-LOCAL-WIRING-01 — Fecha defense-in-depth

**Status:** PENDENTE
**Data criação:** 2026-05-22
**Modelo obrigatório:** claude-opus-4-7 (sem subagentes)

---

## Contexto

> Sprint 196 INFRA-SANITIZER-WORKING-TREE-GUARD-01 (commit a2e7aeb) criou `scripts/hooks/check_sanitizer_attack.py` + integrou no `scripts/hooks/pre-commit` local do projeto. Porém o achado colateral descobriu que o hook local **não é invocado** pelo hook global (`~/.config/git/hooks/pre-commit`) — guard está armado mas só dispara em validação manual (`bash scripts/hooks/pre-commit`).
> Esta sprint fecha a defesa: faz o hook global delegar para o local quando o commit está dentro do projeto Nyx-Code.

---

## Problema

`core.hooksPath` configurado globalmente para `~/.config/git/hooks/` faz com que TODOS os commits do usuário (em qualquer projeto) executem o hook global. Hooks locais em `<repo>/scripts/hooks/` ou `<repo>/.git/hooks/` são ignorados.

Sem invocação automática, o guard da 196 é inútil em fluxo de commit real. 4 recidivas do sanitizer no fim de semana já demonstraram que precisamos de defesa automatizada — operador esquecer de rodar o check manualmente derrota o propósito.

---

## Solução proposta

Adicionar no TOPO do `~/.config/git/hooks/pre-commit` um bloco que:

1. Detecta se o `git rev-parse --show-toplevel` casa com o path absoluto do projeto Nyx-Code (`/home/andrefarias/Desenvolvimento/Nyx-Code`).
2. Se SIM: invoca `<projeto>/scripts/hooks/pre-commit` local; se exit≠0, propaga e bloqueia commit.
3. Se NÃO: continua com hook global existente (zero impacto em outros projetos).

### Patch sugerido

```bash
#!/usr/bin/env bash
# ~/.config/git/hooks/pre-commit

# INFRA-HOOK-LOCAL-WIRING-01: invoca hook local de Nyx-Code se aplicável.
# Mantém defense-in-depth do invariante #14 (anti-sanitizer guard da
# sprint 196). Outros projetos do usuário não são afetados.
_repo_root=$(git rev-parse --show-toplevel 2>/dev/null || echo "")
_nyx_root="/home/andrefarias/Desenvolvimento/Nyx-Code"
if [ "$_repo_root" = "$_nyx_root" ]; then
    _local_hook="$_nyx_root/scripts/hooks/pre-commit"
    if [ -x "$_local_hook" ]; then
        "$_local_hook" || exit $?
    fi
fi

# ... resto do hook global existente ...
```

### Por que NÃO mudar core.hooksPath

Trocar `core.hooksPath` para `<repo>/scripts/hooks/` resolveria — mas o hook global cuida de outras coisas (commit-msg, pre-push, validações cross-project). Substituí-lo localmente perderia essas garantias. A solução acima ADICIONA, não substitui.

### Teste end-to-end

`scripts/hooks/test_global_wiring.sh`:

```bash
#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT="/home/andrefarias/Desenvolvimento/Nyx-Code"
cd "$PROJECT_ROOT"

# Cenário: criar diff que ataca glifos em arquivo protegido, tentar commit.
# Esperado: hook global delega para local, local invoca check, check bloqueia.
TARGET="nyx/themes/design_tokens.py"
BACKUP=$(mktemp)
cp "$TARGET" "$BACKUP"
trap "cp '$BACKUP' '$TARGET'; rm -f '$BACKUP'; git reset HEAD '$TARGET' 2>/dev/null || true" EXIT

# Simula sanitizer attack: substitui chr(0x25CF) por ""
python3 -c "
from pathlib import Path
p = Path('$TARGET')
t = p.read_text()
attacked = t.replace(chr(0x25CF), '').replace(chr(0x25CB), '').replace(chr(0x25D0), '')
p.write_text(attacked)
"
git add "$TARGET"

# Tenta commit — deve falhar bloqueado pelo guard via cadeia
if git commit --dry-run --no-verify=0 -m "ataque simulado" 2>&1 | grep -q "BLOQUEIO"; then
    echo "TEST PASS: wiring funcionando — hook global invocou local"
    exit 0
else
    # Tenta commit real (sem dry-run) capturando exit
    set +e
    git commit -m "ataque simulado teste" 2>&1 | tee /tmp/wiring_test_out.txt
    EXIT_CODE=$?
    set -e
    if [ $EXIT_CODE -ne 0 ] && grep -q "BLOQUEIO" /tmp/wiring_test_out.txt; then
        echo "TEST PASS: commit bloqueado pela cadeia"
        exit 0
    else
        echo "TEST FAIL: commit não foi bloqueado (exit=$EXIT_CODE)"
        cat /tmp/wiring_test_out.txt
        exit 1
    fi
fi
```

---

## Diff esperado

```
~ 1 arquivo modificado FORA do repo (~/.config/git/hooks/pre-commit) — autorizado pelo usuário
+ 1 arquivo criado dentro do repo (scripts/hooks/test_global_wiring.sh)
+ ~15 linhas no hook global + ~40 linhas no teste
```

---

## Comandos de verificação

```bash
# 1. Estado do hook global (antes/depois)
sha256sum ~/.config/git/hooks/pre-commit

# 2. Teste end-to-end
bash scripts/hooks/test_global_wiring.sh

# 3. Smoke + invariantes
./run.sh --smoke
bash scripts/sprint_invariants.sh

# 4. Verificar que commit normal (sem ataque) ainda funciona
echo "# comentário inócuo" >> README.md
git add README.md
git commit -m "test: comentario inocuo" --dry-run    # esperado: OK, sem bloqueio
git checkout README.md

# 5. Outros projetos não afetados (rodar fora do Nyx-Code)
# Se houver outro projeto git, fazer commit fake lá e confirmar zero diferença
```

---

## Critério binário de aceite

- [ ] Hook global tem bloco de wiring no topo (verificar via `head -20 ~/.config/git/hooks/pre-commit`)
- [ ] `bash scripts/hooks/test_global_wiring.sh` PASS
- [ ] Commit que ataca glifo em arquivo protegido é bloqueado por hook global
- [ ] Commit que NÃO ataca (mudança legítima) passa
- [ ] Smoke + invariantes 14/14 PASS
- [ ] Acentuação rc=0
- [ ] Nenhuma violação de forbidden[]

---

## Riscos

| Risco | Mitigação |
|-------|-----------|
| Modificar hook global quebra outros projetos do usuário | Bloco no TOPO + detecção via path absoluto = isolamento total para Nyx-Code |
| Path absoluto hardcoded perde portabilidade se projeto mudar de lugar | Aceito — Nyx-Code está fixo neste path em todas as sessões; futura sprint pode generalizar |
| Hook global pode ser substituído por sistema (apt upgrade, dotfiles sync) | Adicionar mensagem no spec sobre re-aplicar se necessário; documentar em VALIDATOR_BRIEF.md |
| `git rev-parse --show-toplevel` falha em git submodule | Aceito — fallback `echo ""` evita match e o bloco passa silencioso |

---

## Pós-condição

Após esta sprint, qualquer tentativa de commitar working tree corrompido pelo sanitizer (mesmo via mass-edit acidental) será bloqueada automaticamente. Defense-in-depth completa: ALLOWED_GLYPHS (sanitizer atual) + chr(0xNNNN) (defensor) + pre-commit local (heurística) + hook global wiring (automação). 4 camadas independentes.

---

*"Defesa só vale quando dispara sozinha." -- princípio defense-in-depth Nyx-Code.*
