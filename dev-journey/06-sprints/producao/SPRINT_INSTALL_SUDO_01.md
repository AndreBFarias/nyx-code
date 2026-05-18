# SPRINT INSTALL-SUDO-01 — NYX_SUDO_PASSWORD via env var (replicação)

## 0. SPEC (machine-readable)

```yaml
sprint:
  id: INSTALL-SUDO-01
  title: "install.sh aceita NYX_SUDO_PASSWORD via env var para replicação em outros PCs (nunca commitada)"
  onda: 24
  bloco: 24.1 Infra resiliente
  prioridade: MÉDIA
  tipo: Infra
  dependencias: []
  desbloqueia: []

  touches:
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/install.sh
      reason: "Adicionar suporte a echo $NYX_SUDO_PASSWORD | sudo -S quando env var setada"
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/README.md
      reason: "Seção 'Replicação em outro PC' explicando como usar NYX_SUDO_PASSWORD"
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/.gitignore
      reason: "Confirmar que .env.local e qualquer arquivo com NYX_SUDO_PASSWORD está ignorado"
  creates: []
  removes: []

  forbidden:
    - "HARDCODE da senha em install.sh, .env, README ou QUALQUER arquivo commitado"
    - "Logar a senha em stdout/stderr"
    - "Salvar a senha em arquivo dentro de logs/ ou sessions/"

  tests:
    - cmd: "grep -c '10203040' install.sh README.md .env.example 2>/dev/null | grep -v ':0' && echo 'VAZAMENTO' || echo 'OK'"
      timeout: 5
      deve_passar: "imprime OK (sem vazamento)"
    - cmd: "NYX_SUDO_PASSWORD=test_dummy ./install.sh --dry-run --no-prompt 2>&1 | grep -v 'test_dummy' && echo OK"
      timeout: 30
      deve_passar: "OK (senha não vaza em dry-run)"

  acceptance_criteria:
    - "install.sh detecta NYX_SUDO_PASSWORD e usa sudo -S para apt/dnf/pacman/zypper"
    - "Sem NYX_SUDO_PASSWORD: comportamento atual (prompt interativo)"
    - "README seção 'Replicação' explica passo a passo"
    - "Senha NUNCA aparece em log, output, ou arquivo commitado"
    - "git grep -c '10203040' retorna 0"
    - "Smoke ok"
    - "Invariantes 14/14"
```

---

# Sprint INSTALL-SUDO-01 — Sudo seguro via env var

**Status:** PENDENTE
**Data criação:** 2026-05-18
**Modelo obrigatório:** claude-opus-4-7

---

## Contexto

Usuário precisa replicar Nyx-Code em outros PCs sem precisar digitar sudo manualmente em cada um (mensagem do prompt: "senha sudo 10203040, eu preciso replicar tudo em outros pcs"). Mas hardcoded em `.sh` é vetor crítico — mesmo em repo privado, git log expõe.

### Sintoma observável

`./install.sh` em PC novo pede senha sudo interativamente em apt/dnf install. Sem TTY (CI/script remoto) trava.

---

## Solução proposta

`install.sh` aceita `NYX_SUDO_PASSWORD` env var. Se setada, usa `echo "$NYX_SUDO_PASSWORD" | sudo -S <cmd>`. Senão, mantém comportamento atual.

README documenta:
```bash
# Em PC novo
export NYX_SUDO_PASSWORD='sua-senha-aqui'
./install.sh --no-prompt
unset NYX_SUDO_PASSWORD
```

`.gitignore` confirma `.env.local` ignorado.

---

## Arquivos alvo

### `install.sh`

Adicionar helper:
```bash
sudo_run() {
    if [ -n "${NYX_SUDO_PASSWORD:-}" ]; then
        echo "$NYX_SUDO_PASSWORD" | sudo -S "$@"
    else
        sudo "$@"
    fi
}
```

Substituir `sudo apt-get install ...` por `sudo_run apt-get install ...`. Mesmo para `dnf/pacman/zypper`.

### `README.md`

Seção nova ## Replicação em outro PC:
```markdown
## Replicação em outro PC

Para instalar em outro Linux sem interação manual:

```bash
export NYX_SUDO_PASSWORD='sua-senha-aqui'
./install.sh --no-prompt
unset NYX_SUDO_PASSWORD
```

**Segurança:** a senha nunca é gravada em log nem em arquivo do repositório.
Após instalar, faça `history -d <N>` se sua shell salvou o `export` no histórico.
```

### `.gitignore`

Verificar que tem (adicionar se não):
```
.env.local
.secrets
*.password
```

---

## Comandos de verificação

```bash
# 1. Sem vazamento de senha
grep -rn "10203040" install.sh README.md .env.example 2>/dev/null
# esperado: zero hits

git log -p --all | grep -c "10203040"
# esperado: 0

# 2. Comportamento sem env
unset NYX_SUDO_PASSWORD
./install.sh --dry-run --no-prompt
# esperado: roda dry-run normal, pede sudo via prompt se necessário

# 3. Comportamento com env (dummy)
NYX_SUDO_PASSWORD=test_dummy_value ./install.sh --dry-run --no-prompt
# esperado: dry-run roda, sem vazar test_dummy_value

# 4. Smoke + invariantes
./run.sh --smoke
bash scripts/sprint_invariants.sh | tail -5
```

---

## Critério binário de aceite

- [ ] `install.sh` tem função `sudo_run` que usa env var quando setada
- [ ] Sem env: comportamento atual preservado
- [ ] README seção "Replicação em outro PC" documenta uso
- [ ] `.gitignore` cobre `.env.local`, `.secrets`, `*.password`
- [ ] `git grep '10203040'` retorna zero hits
- [ ] `git log -p --all | grep '10203040'` retorna zero hits
- [ ] Smoke ok
- [ ] Invariantes 14/14
- [ ] Sprint movida `producao/` → `concluidos/`
- [ ] Commit `feat(INSTALL-SUDO-01): NYX_SUDO_PASSWORD via env var (replicacao segura em outros PCs)`

---

## Riscos

| Risco | Mitigação |
|---|---|
| Senha vazar em commit | Verificar via `git grep` antes de push |
| Senha vazar em log | `2>/dev/null` em sudo -S; nunca usar `set -x` durante sudo |
| Histórico de shell capturar senha | README orienta `history -d` ou `HISTCONTROL=ignoreboth` |

---

*"A senha vive na cabeça. Nunca no repositório." — INSTALL-SUDO-01*
