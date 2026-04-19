## 0. SPEC

```yaml
sprint:
  id: DEBT-06
  title: "Excluir arquivos auto-gerados do check de acentuação no hook global"
  onda: 22
  bloco: 2.5
  prioridade: BAIXA
  tipo: Infra
  dependencias: []
  desbloqueia: [DEBT-05]

  touches:
    - path: /home/andrefarias/.config/git/hooks/pre-commit
      reason: "Hook global (core.hookspath) é o emissor real de `[aviso] Possivel falta de acentuacao`. Blast radius: afeta TODOS os repositórios do usuário. Whitelist deve ser condicional ao repo Nyx-Code."
      linhas_alvo: "180-205 (bloco ACCENT_PATTERNS)"

  creates: []
  removes: []

  forbidden:
    - "Alterar scripts/hooks/pre-commit do repo Nyx-Code (não é executado; core.hookspath aponta para o global)"
    - "Alterar hooks de outros repositórios"
    - "Reescrever o check de acentuação além da whitelist condicional (manter regex e lista de palavras intactos)"
    - "Aplicar whitelist incondicional (sem checar nome do repo) — afetaria outros projetos"
    - "Adicionar .md genericamente à whitelist"

  tests:
    - descricao: "Positivo (blindagem): em Nyx-Code, commit staged com 'funcao' sem acento em EXECUTAR_SPRINT.md ou dev-journey/06-sprints/SPRINT_ORDER_MASTER.md NÃO dispara aviso"
      deve_passar: true
    - descricao: "Negativo (regressão dentro de Nyx-Code): arquivo .md qualquer outro com 'funcao' sem acento DISPARA aviso"
      deve_passar: true
    - descricao: "Isolamento (fora do repo): em qualquer outro repositório, arquivo .md com 'funcao' sem acento DISPARA aviso (comportamento global preservado)"
      deve_passar: true

  acceptance_criteria:
    - "Commit em Nyx-Code tocando EXECUTAR_SPRINT.md e/ou SPRINT_ORDER_MASTER.md com conteúdo sem acento (staged) não emite aviso"
    - "Commit em Nyx-Code em qualquer outro .md com falta real de acento continua emitindo aviso"
    - "Commit em outro repositório do usuário com falta de acento continua emitindo aviso (comportamento inalterado fora de Nyx-Code)"
    - "Bloco ACCENT_PATTERNS e lista de palavras preservados literalmente"
    - "scripts/hooks/pre-commit do repo Nyx-Code não é tocado"
    - "DEBT-05 reaberta e concluída em seguida, com proof-of-work nas 3 rotas de teste acima"
```

---

# Sprint DEBT-06 — Whitelist condicional no hook global de acentuação

**Status:** PENDENTE
**Data criação:** 2026-04-19
**Modelo obrigatório:** claude-opus-4-7 (sem subagentes)

---

## Contexto

Durante a execução de DEBT-05 (2026-04-19) descobriu-se que:

- `git config core.hookspath` está setado como `/home/andrefarias/.config/git/hooks` (config global do usuário).
- O git executa, portanto, **apenas** o hook em `~/.config/git/hooks/pre-commit` — nunca `.git/hooks/pre-commit` local nem `scripts/hooks/pre-commit` versionado no repo.
- A mensagem literal `[aviso] Possivel falta de acentuacao: <arquivo>` é emitida pelo hook global, linha ~192 do arquivo `~/.config/git/hooks/pre-commit`.
- Esse hook é compartilhado entre todos os projetos do usuário — modificá-lo sem isolamento afeta outros repositórios.

DEBT-05 ficou **BLOQUEADA** aguardando esta sprint (registrado como AC-03 no relatório de DEBT-05 no commit de planejamento).

---

## Problema

Commits em `EXECUTAR_SPRINT.md` e `dev-journey/06-sprints/SPRINT_ORDER_MASTER.md` (ambos regenerados por `scripts/update_next_sprint.py` após cada sprint) emitem falso-positivo:

```
[aviso] Possivel falta de acentuacao: EXECUTAR_SPRINT.md
[aviso] Possivel falta de acentuacao: dev-journey/06-sprints/SPRINT_ORDER_MASTER.md
```

O conteúdo desses arquivos é auditado por revisão humana; o aviso é ruído e tende a desensibilizar o validador para avisos reais.

Complicação: o hook é global. Qualquer alteração precisa ser **condicional** ao repositório Nyx-Code para não escapar o escopo para outros projetos do usuário.

---

## Solução proposta

No hook `~/.config/git/hooks/pre-commit`, dentro do bloco de checagem de acentuação (próximo à linha 180-205 onde `ACCENT_PATTERNS` é aplicado), antes de emitir o aviso para um arquivo, aplicar a whitelist apenas quando o repositório corrente for Nyx-Code:

```bash
# Pseudocódigo — IA executora deve ler o arquivo inteiro e adaptar à estrutura exata

REPO_TOPLEVEL="$(git rev-parse --show-toplevel 2>/dev/null || true)"
REPO_BASENAME="$(basename "$REPO_TOPLEVEL")"

# ... dentro do loop que detecta acentuação ...
if [ "$REPO_BASENAME" = "Nyx-Code" ]; then
    case "$file" in
        EXECUTAR_SPRINT.md|dev-journey/06-sprints/SPRINT_ORDER_MASTER.md)
            continue
            ;;
    esac
fi
# ... fluxo original segue ...
```

Isolamento por nome do toplevel é simples e suficiente. Se um dia existir outro repo chamado `Nyx-Code` em outra pasta, reavaliar — até lá, é mínimo viável e reversível.

---

## Procedimento

```bash
# 1. Ler o hook global inteiro
cat ~/.config/git/hooks/pre-commit

# 2. Localizar bloco de acentuação
grep -n 'ACCENT_PATTERNS\|Possivel falta' ~/.config/git/hooks/pre-commit

# 3. Fazer backup antes de editar (blast radius global)
cp ~/.config/git/hooks/pre-commit /tmp/pre-commit.bak.$(date +%s)

# 4. Editar aplicando whitelist condicional
# 5. Validar sintaxe: bash -n ~/.config/git/hooks/pre-commit
```

---

## Comandos de verificação (literais)

### Rota positiva (Nyx-Code, paths whitelisted)

```bash
cd /home/andrefarias/Desenvolvimento/Nyx-Code
cp EXECUTAR_SPRINT.md /tmp/EXECUTAR_SPRINT.md.bak
printf '\nlinha com funcao sem acento para teste.\n' >> EXECUTAR_SPRINT.md
git add EXECUTAR_SPRINT.md
bash ~/.config/git/hooks/pre-commit 2>&1 | grep -i 'Possivel falta'
# esperado: VAZIO
git reset HEAD EXECUTAR_SPRINT.md
cp /tmp/EXECUTAR_SPRINT.md.bak EXECUTAR_SPRINT.md
rm /tmp/EXECUTAR_SPRINT.md.bak
```

### Rota negativa (Nyx-Code, arquivo genérico)

```bash
cd /home/andrefarias/Desenvolvimento/Nyx-Code
printf 'linha com funcao sem acento.\n' > test_debt06_acento.md
git add test_debt06_acento.md
bash ~/.config/git/hooks/pre-commit 2>&1 | grep -i 'Possivel falta'
# esperado: dispara aviso citando test_debt06_acento.md
git reset HEAD test_debt06_acento.md
rm test_debt06_acento.md
```

### Rota isolamento (fora de Nyx-Code)

```bash
# Usar qualquer outro repo do usuário (ex: Luna, ou um temp)
TMPREPO=$(mktemp -d)
cd "$TMPREPO"
git init -q
printf 'funcao sem acento.\n' > foo.md
git add foo.md
bash ~/.config/git/hooks/pre-commit 2>&1 | grep -i 'Possivel falta'
# esperado: dispara aviso (hook global preservado para outros repos)
cd /tmp && rm -rf "$TMPREPO"
```

Colar output bruto dos 3 comandos no relatório de conclusão.

---

## Critério binário de aceite

- [ ] Rota positiva (EXECUTAR_SPRINT.md com falta de acento em Nyx-Code): sem aviso
- [ ] Rota positiva (SPRINT_ORDER_MASTER.md com falta de acento em Nyx-Code): sem aviso
- [ ] Rota negativa (arquivo .md genérico em Nyx-Code com falta de acento): dispara aviso
- [ ] Rota isolamento (repo qualquer fora de Nyx-Code): dispara aviso
- [ ] `bash -n ~/.config/git/hooks/pre-commit` retorna 0 (sintaxe válida)
- [ ] `scripts/hooks/pre-commit` do repo **não foi tocado** (diff vazio)
- [ ] Backup salvo em `/tmp/pre-commit.bak.*` antes da edição
- [ ] DEBT-05 marcada CONCLUIDA na sequência (acceptance agora alcançável)
- [ ] `sprint_invariants.sh` FAIL_AFTER ≤ FAIL_BEFORE
- [ ] Commit `chore: whitelist condicional para Nyx-Code no check de acentuação do hook global`

---

## Gambiarras específicas (bypass-paths desta sprint)

- **Whitelist incondicional** (sem checar `REPO_BASENAME`) — proibido. Afetaria outros projetos do usuário.
- **Checar `$PWD` em vez de `git rev-parse --show-toplevel`** — proibido. `$PWD` pode ser subdiretório; toplevel é canônico.
- **Remover o bloco inteiro de acentuação** — proibido. O check permanece intacto para todos os outros casos.
- **Adicionar mais paths à whitelist** além dos 2 explícitos — proibido.
- **Reescrever `ACCENT_PATTERNS`** "para ficar mais robusto" — proibido. Escopo é apenas whitelist.
- **Não fazer backup** — proibido. Hook global, blast radius alto: `/tmp/pre-commit.bak.<timestamp>` obrigatório antes do edit.
- **Testar só a rota positiva** — proibido. Obrigatório rodar as 3 rotas (positiva, negativa dentro do repo, isolamento fora do repo).

---

## Riscos

| Risco | Mitigação |
|-------|-----------|
| Edit quebra hook global e afeta commits em qualquer repo | Backup obrigatório `/tmp/pre-commit.bak.<timestamp>` + `bash -n` + teste nas 3 rotas antes de declarar concluído |
| Outro repo no futuro chamado "Nyx-Code" em pasta diferente herdaria a whitelist | Aceitável (basename é estável; reavaliar apenas se acontecer) |
| Hook global é re-instalado/sobrescrito por outro processo (dotfiles, setup script) e perde a whitelist | Fora de escopo — se ocorrer, reabrir sprint |
| A IA executora muda `scripts/hooks/pre-commit` do repo "por precaução" | Forbidden explícito + diff do repo deve ficar vazio |

---

## Observação de integração

Ao concluir DEBT-06, a IA executora deve **imediatamente reabrir DEBT-05** (marcar PENDENTE novamente ou abrir DEBT-05B) e verificar que, com o hook corrigido, o acceptance original de DEBT-05 passa. Só então ambas viram CONCLUIDA.

Alternativa aceita: DEBT-06 absorve o acceptance de DEBT-05 (as rotas positivas desta sprint cobrem exatamente o que DEBT-05 queria). Nesse caso, DEBT-05 é marcada `ABSORVIDA_POR_DEBT_06 (commit HASH)` no SPRINT_ORDER_MASTER e movida para concluidos/ sem rework de código.

Decisão final fica com o usuário ao executar DEBT-06.

---

*"O sinal só alerta quem o reconhece." — anônimo*
