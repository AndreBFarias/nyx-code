## 0. SPEC

```yaml
sprint:
  id: DEBT-05
  title: "Ajustar pre-commit hook: excluir arquivos auto-gerados do check de acentuação"
  onda: 22
  bloco: 2.5
  prioridade: BAIXA
  tipo: Infra
  dependencias: []
  desbloqueia: []

  touches:
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/.pre-commit-config.yaml
      reason: "Adicionar exclude pattern no hook de acentuação"
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/scripts/check_acentuacao.py
      reason: "(se existir) whitelist EXECUTAR_SPRINT.md e SPRINT_ORDER_MASTER.md"

  creates: []
  removes: []

  forbidden:
    - "Desativar o check inteiro"
    - "Adicionar exclude para arquivos .md arbitrários (risco de mascarar bugs reais)"

  tests:
    - cmd: "pre-commit run --all-files 2>&1 | grep 'Possivel falta de acentuacao'"
      esperado: "vazio ou apenas falsos-positivos legítimos"
    - cmd: "git commit --allow-empty -m 'test: pre-commit acentuacao' --dry-run"
      deve_passar: true

  acceptance_criteria:
    - "Commits em EXECUTAR_SPRINT.md e SPRINT_ORDER_MASTER.md não disparam warning falso"
    - "Hook ainda flagra arquivos .md com falta real de acentuação (regressão coberta)"
    - "Nenhum arquivo adicional silenciado sem justificativa"
```

---

# Sprint DEBT-05 — Tunar pre-commit de acentuação

**Status:** PENDENTE
**Data criação:** 2026-04-19
**Modelo obrigatório:** claude-opus-4-7 (sem subagentes)

---

## Contexto do projeto (snapshot)

> - Relatório Bloco 2 Onda 22 §3.5: hook de acentuação dispara warning falso-positivo em `EXECUTAR_SPRINT.md` e `SPRINT_ORDER_MASTER.md`.
> - Esses arquivos são auto-gerados por `scripts/update_next_sprint.py` e passam por manual review; estão corretos em PT-BR.
> - Warnings não bloqueiam commit, mas poluem saída e podem mascarar warnings reais.

---

## Problema

Toda sprint concluída atualiza esses dois arquivos. Todo commit relacionado dispara:
```
[aviso] Possivel falta de acentuacao: EXECUTAR_SPRINT.md
[aviso] Possivel falta de acentuacao: dev-journey/06-sprints/SPRINT_ORDER_MASTER.md
```

Impacto: ruído cumulativo + desensibilização ao sinal.

---

## Solução proposta

### Opção A — Whitelist no script do hook
Se o hook é um script Python/shell em `scripts/`, adicionar lista `EXCLUDED_FILES` contendo os 2 paths.

### Opção B — Exclude pattern no `.pre-commit-config.yaml`
```yaml
- id: acentuacao
  exclude: '^(EXECUTAR_SPRINT\.md|dev-journey/06-sprints/SPRINT_ORDER_MASTER\.md)$'
```

Preferir Opção B por ser padrão do pre-commit.

---

## Procedimento

```bash
# 1. localizar hook
cat .pre-commit-config.yaml | grep -A5 -B1 'acentuacao\|accent'

# 2. identificar script do hook (se for custom)
grep -rn 'Possivel falta de acentuacao' scripts/ nyx/

# 3. adicionar exclude
```

---

## Arquivos alvo

### `.pre-commit-config.yaml`

Adicionar ao hook relevante:
```yaml
exclude: |
  (?x)^(
    EXECUTAR_SPRINT\.md|
    dev-journey/06-sprints/SPRINT_ORDER_MASTER\.md
  )$
```

Se o hook for script shell em `scripts/hooks/`, também adicionar whitelist.

---

## Comandos de verificação

```bash
# 1. pre-commit sem warning falso
touch EXECUTAR_SPRINT.md
pre-commit run --files EXECUTAR_SPRINT.md 2>&1 | grep -i 'acentuacao\|falta'
# esperado: vazio (ou mensagem explícita "skipping excluded")

# 2. hook ainda detecta arquivo com problema real
cat > /tmp/test_acento.md <<'EOF'
Palavra com falta de acentuacao.
EOF
pre-commit run --files /tmp/test_acento.md 2>&1 | grep -i 'acentuacao'
# esperado: warning disparado
rm /tmp/test_acento.md
```

---

## Critério binário de aceite

- [ ] Commit em EXECUTAR_SPRINT.md não dispara warning
- [ ] Commit em SPRINT_ORDER_MASTER.md não dispara warning
- [ ] Arquivo .md genérico com falta real de acento ainda dispara
- [ ] Nenhum arquivo extra silenciado
- [ ] Commit `chore: exclui arquivos auto-gerados do check de acentuação`

---

## Gambiarras específicas

- **`exclude: '.*'`** no hook — proibido. Apenas os 2 paths listados.
- **Deletar o hook** inteiro em vez de excluir paths. Proibido.
- **Adicionar `.md` genericamente** à lista de exclusão. Proibido.

---

## Riscos

| Risco | Mitigação |
|-------|-----------|
| `.pre-commit-config.yaml` pode não existir (hooks custom em scripts/) | Primeiro localizar via `grep`; aplicar Opção A se for o caso |
| Arquivo futuro com nome similar ganhar isenção indevida | Pattern usa `^...$` (match exato) |

---

*"Os sinais de alarme só servem se distinguirem ruído de perigo." -- anônimo*
