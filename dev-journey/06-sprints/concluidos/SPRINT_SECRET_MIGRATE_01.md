# SPRINT SECRET-MIGRATE-01 — ANTHROPIC_API_KEY de .env para ~/.config/nyx/secrets

## 0. SPEC (machine-readable)

```yaml
sprint:
  id: SECRET-MIGRATE-01
  title: "Move ANTHROPIC_API_KEY de .env para ~/.config/nyx/secrets (chmod 600)"
  onda: 23
  bloco: 23.1 Estabilização
  prioridade: BAIXA
  tipo: Infra+Segurança
  dependencias: []
  desbloqueia: [DEPLOY-01A]

  touches:
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/run.sh
      reason: "Carregar ~/.config/nyx/secrets após .env (precedência secrets)"
      linhas_alvo: "39-43"
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/.env.example
      reason: "Remove ANTHROPIC_API_KEY do exemplo; adiciona comentário sobre secrets"

  creates:
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/install.sh
      reason: "Se DEPLOY-01A ainda não criou; cria seção que pergunta API key e grava em ~/.config/nyx/secrets"
      nota: "Coordenar com DEPLOY-01A — se conflito, esta sprint só preserva o trecho"

  removes: []

  n_to_n_pairs:
    - descricao: "Variável ANTHROPIC_API_KEY existe em .env e potencialmente em GitHub workflow/anonymity-check — verificar se aparece em algum logs"
      paths:
        - /home/andrefarias/Desenvolvimento/Nyx-Code/.env
        - /home/andrefarias/Desenvolvimento/Nyx-Code/.env.example
        - /home/andrefarias/Desenvolvimento/Nyx-Code/.github/workflows/anonymity-check.yml

  forbidden:
    - "Commitar valor real de ANTHROPIC_API_KEY em qualquer arquivo"
    - "Imprimir API key em logs (mesmo parcial)"
    - "Deixar secrets file world-readable (chmod !=600)"
    - "Quebrar o boot existente: sem secrets file, deve cair pra .env (compat backward)"

  tests:
    - cmd: "./run.sh --smoke"
      timeout: 60
      deve_passar: true
    - cmd: "test -f ~/.config/nyx/secrets && stat -c '%a' ~/.config/nyx/secrets"
      timeout: 5
      deve_passar: true
      nota: "Saída deve ser 600"
    - cmd: "bash scripts/sprint_invariants.sh"
      timeout: 60
      deve_passar: "FAIL_AFTER <= FAIL_BEFORE"

  acceptance_criteria:
    - "Arquivo ~/.config/nyx/secrets criado com chmod 600 ao primeiro boot ou install"
    - "run.sh carrega .env primeiro e ~/.config/nyx/secrets depois (precedência secrets)"
    - "ANTHROPIC_API_KEY removida de .env.example (instrução clara onde colocar)"
    - "Smoke passa; gauntlet rapido passa"
    - "Documentação clara em README ou install.sh sobre onde armazenar a key"
    - "Acentuação PT-BR; zero menção a IA"
```

---

**Status:** CONCLUIDA
**Data criação:** 2026-05-15
**Data conclusão:** 2026-05-17
**Hash:** (a preencher pós-commit)
**Modelo obrigatório:** claude-opus-4-7 (sem subagentes)
**Resultado:** run.sh carrega .env primeiro + ~/.config/nyx/secrets depois (precedência secrets). install.sh seção 7a cria diretório 700 + arquivo secrets 600 com template. .env.example documenta onde guardar key. Backward compat: smoke passa sem secrets file. Gauntlet rapido 18/18.

---

# Sprint SECRET-MIGRATE-01

## Contexto

`ANTHROPIC_API_KEY` em texto plano em `.env`. Mitigado por `.gitignore` (nunca commitado), mas risco residual: screenshots, logs, pastes acidentais. Padrão Unix é colocar secrets em `~/.config/<app>/secrets` 0600.

## Solução

### `run.sh`

```bash
# Após carregar .env (linha 39-43):
SECRETS_FILE="${XDG_CONFIG_HOME:-$HOME/.config}/nyx/secrets"
if [ -f "$SECRETS_FILE" ]; then
    set -a
    source "$SECRETS_FILE"
    set +a
fi
```

### `install.sh` (coordenado com DEPLOY-01A)

```bash
mkdir -p "${XDG_CONFIG_HOME:-$HOME/.config}/nyx"
chmod 700 "${XDG_CONFIG_HOME:-$HOME/.config}/nyx"
if [ ! -f "${XDG_CONFIG_HOME:-$HOME/.config}/nyx/secrets" ]; then
    touch "${XDG_CONFIG_HOME:-$HOME/.config}/nyx/secrets"
    chmod 600 "${XDG_CONFIG_HOME:-$HOME/.config}/nyx/secrets"
    cat <<EOF > "${XDG_CONFIG_HOME:-$HOME/.config}/nyx/secrets"
# Nyx-Code secrets (chmod 600)
# ANTHROPIC_API_KEY=sk-ant-...
EOF
fi
```

### `.env.example` (se existir)

```diff
- ANTHROPIC_API_KEY=sk-ant-...
+ # ANTHROPIC_API_KEY foi movido para ~/.config/nyx/secrets (chmod 600).
+ # Edite esse arquivo após o primeiro install.
```

## Verificação

```bash
bash scripts/sprint_invariants.sh > /tmp/inv_before.txt 2>&1
# implementar
ls -la ~/.config/nyx/secrets  # deve ser -rw-------
./run.sh --smoke
bash scripts/sprint_invariants.sh > /tmp/inv_after.txt 2>&1
diff /tmp/inv_before.txt /tmp/inv_after.txt
```

## Gambiarras proibidas

- chmod 644 (world-readable).
- Adicionar ANTHROPIC_API_KEY hardcoded em algum fallback.
- Imprimir valor da key em logs (mesmo trunc).
- Manter ANTHROPIC_API_KEY como obrigatória — Nyx é local-first; só algumas operações dependem dela.

---

*"O segredo do segredo é o permission bit certo." -- anônimo*
