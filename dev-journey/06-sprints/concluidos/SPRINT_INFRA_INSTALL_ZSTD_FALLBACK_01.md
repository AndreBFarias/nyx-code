# SPRINT INFRA-INSTALL-ZSTD-FALLBACK-01 -- install.sh detecta e instala zstd antes do Ollama bootstrap

## 0. SPEC (machine-readable)

```yaml
sprint:
  id: INFRA-INSTALL-ZSTD-FALLBACK-01
  title: "install.sh detecta ausência do binário zstd e instala via pkg-manager apropriado antes da fase Ollama, evitando falha do tar em imagens Linux mínimas (ex.: ubuntu:22.04 base)"
  onda: 24
  bloco: 24.1 Infra resiliente
  prioridade: MÉDIA
  tipo: Infra
  dependencias: []
  desbloqueia: []
  origem: "Achado colateral de VALIDATE-FINAL-01-PARTE-2 (frente 4, commit 8101062). Sessão Docker ubuntu:22.04 fez ./install.sh quebrar na fase Ollama: o script oficial upstream (curl https://ollama.com/install.sh | sh) extrai archive .tar.zst e tar -- xJf / tar --zstd dispara erro 'tar: this does not look like a tar archive' quando zstd não está no PATH. Imagem ubuntu:22.04 base não traz zstd."

  touches:
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/install.sh
      reason: "Adicionar fase nova de detecção + install de zstd ANTES da fase Ollama. Renumerar fases subsequentes (TOTAL=11 -> TOTAL=12)."
  creates: []
  removes: []

  forbidden:
    - "Modificar o script oficial upstream do Ollama (https://ollama.com/install.sh) -- não é nosso código"
    - "Tornar a fase obrigatória/hard-fail: deve ser graceful (skip se zstd já existe; warn-and-continue se pkg-manager ausente ou install falhou)"
    - "Quebrar --no-prompt: modo CI/container precisa funcionar sem TTY, sem perguntas"
    - "Pedir confirmação interativa em qualquer caminho da fase (must respeitar NO_PROMPT)"
    - "Logar NYX_SUDO_PASSWORD ou qualquer credencial em stdout/stderr"
    - "Reintroduzir emojis em mensagens (regra universal do projeto)"

  tests:
    - cmd: "bash -n install.sh"
      timeout: 5
      deve_passar: "exit 0 (sintaxe bash OK)"
    - cmd: "./install.sh --dry-run --no-prompt 2>&1 | grep -E 'FASE [0-9]+.*zstd|zstd.*pre-Ollama'"
      timeout: 30
      deve_passar: "mostra a fase nova no plano de dry-run"
    - cmd: "command -v zstd"
      timeout: 5
      deve_passar: "retorna caminho válido (ex.: /usr/bin/zstd) após install rodar em ambiente sem zstd"
    - cmd: "./run.sh --smoke"
      timeout: 60
      deve_passar: "imprime 'boot ok' e exit 0"
    - cmd: "bash scripts/sprint_invariants.sh"
      timeout: 60
      deve_passar: "PASS 14/14, FAIL 0"

  acceptance_criteria:
    - "install.sh tem fase explícita (recomendada FASE 3) que detecta ausência de zstd e instala via pkg-manager (apt-get/dnf/pacman/zypper)"
    - "Em ambiente que JÁ tem zstd: fase imprime SKIP visível com `print_skip` (idempotência preservada)"
    - "Em ambiente SEM zstd e COM pkg-manager conhecido: fase tenta instalar via sudo_run e imprime OK quando sucesso"
    - "Em ambiente SEM zstd e SEM pkg-manager conhecido: fase imprime AVISO claro (print_warn) mas continua execução (graceful, não exit 1)"
    - "Em ambiente SEM zstd, COM pkg-manager, MAS install falhou: fase imprime AVISO mais claro e continua (graceful) -- Ollama tentará e poderá falhar com mensagem própria"
    - "Fase respeita --no-prompt (sem perguntas interativas em CI/Docker)"
    - "Fase respeita --dry-run (sem comando destrutivo; apenas anúncio do que faria)"
    - "Renumeração de fases coerente: TOTAL=12; Ollama vira FASE 4; modelo padrão FASE 5; ... ícones XDG FASE 12. Todas mensagens print_step e referências internas (`FASE 3`, `FASES 4 e 5`) atualizadas"
    - "Header --help atualizado: '12 fases:' e nova linha '  3  Garantia de zstd (pré-Ollama; instala se ausente, graceful em falha)'"
    - "bash -n install.sh exit 0"
    - "./install.sh --dry-run --no-prompt roda end-to-end sem erro de sintaxe e a nova fase aparece"
    - "Em ambiente sem zstd: command -v zstd retorna OK após a fase"
    - "./run.sh --smoke continua imprimindo 'boot ok' (zero regressão na boot path)"
    - "bash scripts/sprint_invariants.sh: PASS 14/14, FAIL 0"
    - "Sprint movida producao/ -> concluidos/"
    - "Commit: feat(INFRA-INSTALL-ZSTD-FALLBACK-01): garante zstd antes do Ollama install (graceful em distros minimas)"
```

---

# Sprint INFRA-INSTALL-ZSTD-FALLBACK-01 -- Garantia de zstd antes do bootstrap Ollama

**Status:** CONCLUIDA (2026-05-19)
**Data criação:** 2026-05-19
**Sprint mãe:** VALIDATE-FINAL-01-PARTE-2 (commit `8101062`)
**Tipo:** Anti-débito (achado colateral)

---

## 1. Contexto

Em VALIDATE-FINAL-01-PARTE-2 (frente 4: smoke Docker), a sessão rodou `./install.sh --no-prompt` dentro de container `ubuntu:22.04` limpo para validar replicação cross-host. A fase Ollama quebrou:

- `./install.sh` chega na FASE 3 atual e executa `curl -fsSL https://ollama.com/install.sh | sh`.
- O script oficial upstream do Ollama baixa um archive `.tar.zst` (zstandard) e descompacta com `tar --zstd` (ou `zstd -d | tar -x`).
- O binário `zstd` NÃO está no PATH da imagem `ubuntu:22.04` base mínima.
- Resultado: `tar` falha, install do Ollama aborta, fase 3 do nosso script exit 1.

A sprint mãe contornou registrando este achado como sprint nova (princípio "nenhum débito fica para trás" -- memória `feedback_nenhum_debito.md`) e seguiu sem bloquear v1.0. O smoke real do Docker passou na segunda tentativa após `apt-get install -y zstd` manual.

Confirmado em `dev-journey/07-reports/RELATORIO_VALIDATE_FINAL_01.md:163` e em `dev-journey/06-sprints/concluidos/SPRINT_VALIDATE_FINAL_01_PARTE_2.md:78`.

### Sintoma observável

```
$ docker run --rm -it ubuntu:22.04 bash
# apt-get update && apt-get install -y curl git python3 python3-venv sudo
# git clone ... && cd Nyx-Code && ./install.sh --no-prompt
...
[3/11] Instalação do Ollama
    AVISO ollama ausente -- instalando via script oficial
... (curl baixa archive .tar.zst)
tar: this does not look like a tar archive
tar: Exiting with failure status due to previous errors
    ERRO Falha ao instalar Ollama. Veja https://ollama.com/download
```

### Causa raiz

Distribuições Linux base mínimas (ubuntu:22.04, debian:slim, alpine sem `build-base`) não incluem `zstd`. Upstream Ollama assume presença. Nosso install.sh não checa. Replicação cross-host quebra.

---

## 2. Solução proposta

Inserir nova fase explícita no `install.sh` ANTES da fase Ollama. Ela:

1. Verifica `have_cmd zstd`. Se existe: `print_skip` e continua.
2. Se ausente: detecta `PKG_MANAGER` via `detect_pkg_manager()` (já existe no script).
3. Se pkg-manager conhecido: roda `sudo_run <pkg> install -y zstd` via `run_or_skip` (respeita --dry-run).
4. Se install OK: `print_ok` e continua.
5. Se install falhou (exit code não-zero do `sudo_run`): `print_warn "zstd install falhou; Ollama install pode quebrar -- veja https://github.com/facebook/zstd"` e CONTINUA (não exit 1).
6. Se pkg-manager ausente: `print_warn "Sem pkg-manager suportado; instale zstd manualmente se Ollama install falhar"` e CONTINUA.

Não bloqueia. Não interage. Sem TTY OK.

### Por quê graceful?

- Em ambientes que já têm Ollama instalado (FASE Ollama dá SKIP), a ausência de zstd é irrelevante.
- Em distros exóticas sem nosso pkg-manager (NixOS, void, etc.), o usuário avança e recebe erro upstream do Ollama com contexto mais claro.
- Falha hard nesta fase quebraria fluxos que hoje funcionam (usuários com zstd via outro caminho, snap, brew-on-linux, etc.).

---

## 3. Plano de implementação por fases

### Fase A -- Renumeração

`install.sh` hoje tem `TOTAL=11` (linha 77) e fases 0..11 (linhas 147..353).

Inserir a nova fase como **FASE 3** (entre pip install e Ollama). Renumeração:

| Antes | Depois | Conteúdo |
|---|---|---|
| FASE 0 | FASE 0 | Requisitos mínimos |
| FASE 1 | FASE 1 | venv |
| FASE 2 | FASE 2 | pip install |
| -- | **FASE 3** | **Garantia de zstd (nova)** |
| FASE 3 | FASE 4 | Ollama install |
| FASE 4 | FASE 5 | Modelo padrão |
| FASE 5 | FASE 6 | moondream |
| FASE 6 | FASE 7 | xclip |
| FASE 7 | FASE 8 | kitty |
| FASE 8 | FASE 9 | permissões |
| FASE 9 | FASE 10 | smoke test |
| FASE 10 | FASE 11 | Controle OOM |
| FASE 11 | FASE 12 | Ícones XDG |

Atualizações sintáticas necessárias:

- Linha 77: `TOTAL=11` -> `TOTAL=12`
- Linhas 52-64 (bloco --help): adicionar linha `  3  Garantia de zstd (pré-Ollama; instala se ausente, graceful em falha)` e renumerar `3..11` para `4..12`.
- Linha 230 (comentário): `# DEPLOY-01B: NYX_INSTALL_SKIP_PULL=1 pula FASES 4 e 5 quando o ambiente` -> `pula FASES 5 e 6`.
- Linha 237: `print_warn "ollama ausente -- pull pulado (rodar novamente após FASE 3)"` -> `após FASE 4`.

### Fase B -- Inserção da nova fase

Trecho a inserir logo após a FASE 2 (atual linha 203, antes do `# ===========================================================` que abre FASE 3):

```bash
# ===========================================================
# FASE 3 -- Garantia de zstd (pré-Ollama)
# ===========================================================
# Script oficial do Ollama baixa archive .tar.zst que requer binario zstd.
# Distros minimas (ubuntu:22.04 base, debian:slim) nao trazem zstd no PATH.
# Achado em VALIDATE-FINAL-01-PARTE-2; ver INFRA-INSTALL-ZSTD-FALLBACK-01.
print_step 3 "Garantia de zstd (pré-Ollama install)"

if have_cmd zstd; then
    print_skip "zstd já instalado ($(zstd --version 2>&1 | head -1))"
elif [ -z "$PKG_MANAGER" ]; then
    print_warn "zstd ausente e sem pkg-manager suportado -- Ollama install pode quebrar; instale zstd manualmente"
else
    print_warn "zstd ausente -- tentando instalar via $PKG_MANAGER"
    ZSTD_OK=0
    case "$PKG_MANAGER" in
        apt-get) run_or_skip "apt install zstd" sudo_run apt-get install -y zstd && ZSTD_OK=1 || ZSTD_OK=0 ;;
        dnf)     run_or_skip "dnf install zstd" sudo_run dnf install -y zstd && ZSTD_OK=1 || ZSTD_OK=0 ;;
        pacman)  run_or_skip "pacman -S zstd"   sudo_run pacman -S --noconfirm zstd && ZSTD_OK=1 || ZSTD_OK=0 ;;
        zypper)  run_or_skip "zypper install zstd" sudo_run zypper install -y zstd && ZSTD_OK=1 || ZSTD_OK=0 ;;
    esac
    if [ $DRY_RUN -eq 1 ]; then
        print_skip "zstd install (dry-run)"
    elif [ $ZSTD_OK -eq 1 ] && have_cmd zstd; then
        print_ok "zstd instalado ($(zstd --version 2>&1 | head -1))"
    else
        print_warn "zstd install falhou ou pacote indisponível; Ollama install pode quebrar (graceful, continuando)"
    fi
fi
```

**Notas de implementação:**

- O padrão `cmd && ZSTD_OK=1 || ZSTD_OK=0` é compatível com `set -euo pipefail` porque o `||` neutraliza o exit non-zero antes do shell abortar.
- O fallback `[ $DRY_RUN -eq 1 ] && print_skip` cobre o caso dry-run sem duplicar `run_or_skip` (que já imprime SKIP internamente).
- A mensagem "graceful, continuando" é explícita para o usuário entender que a próxima fase poderá falhar.

### Fase C -- Aritmética de linhas

- `install.sh` atual: 409 linhas.
- Inserção estimada: ~30 linhas (cabeçalho + 4 ramos + 4 cases + ramo dry-run/ok/warn).
- Renumeração: ~10 substituições de string (sem mudança de count).
- `install.sh` projetado: ~440 linhas. Sem meta de tamanho para esse arquivo no BRIEF; mudança aceitável.

### Fase D -- Verificação

```bash
# 1. Sintaxe
bash -n install.sh
# esperado: exit 0

# 2. Dry-run mostra a fase nova
./install.sh --dry-run --no-prompt 2>&1 | grep -E "\[3/12\].*zstd|FASE 3.*zstd"
# esperado: pelo menos uma linha de match

# 3. Smoke boot continua
./run.sh --smoke
# esperado: "boot ok", exit 0

# 4. Invariantes
bash scripts/sprint_invariants.sh
# esperado: PASS 14/14, FAIL 0

# 5. Container ubuntu:22.04 (validação real, opcional mas recomendada)
docker run --rm ubuntu:22.04 bash -c "
    apt-get update -q &&
    apt-get install -y -q curl git python3 python3-venv sudo &&
    git clone https://github.com/<repo>/Nyx-Code &&
    cd Nyx-Code &&
    ./install.sh --no-prompt --no-vision
"
# esperado: chega na FASE 12 (icones) sem exit 1 em FASE 3 ou FASE 4

# 6. Ambiente com zstd já presente (skip path)
command -v zstd  # supondo /usr/bin/zstd
./install.sh --dry-run --no-prompt 2>&1 | grep -E "\[3/12\]" -A 1
# esperado: "SKIP zstd já instalado (zstd command line interface ...)"

# 7. Acentuação periférica
python3 ~/.config/zsh/scripts/validar-acentuacao.py install.sh
# esperado: zero issues
```

---

## 4. Invariantes a preservar

- **Idempotência** (DEPLOY-01A doctrine): rodar `./install.sh` N vezes não muda o sistema após a primeira. A fase zstd respeita `have_cmd zstd` para SKIP.
- **Modo --no-prompt funcional em CI/Docker** (sem TTY): nenhuma fase pergunta. Confirmado via `ask_or_default` apenas em FASE kitty (fora do escopo).
- **Modo --dry-run não-destrutivo**: nenhum `sudo_run` real quando `DRY_RUN=1` -- garantido pelo `run_or_skip`.
- **Acentuação correta em PT-BR** (BRIEF check #4): mensagens "Garantia de zstd", "instalando", "pode quebrar" usam acentos corretos.
- **Sem emojis** (BRIEF check #2 e regra universal): nenhuma emoji nas novas strings.
- **Sem menção a IA externa** (BRIEF check #3): N/A em shell script, mas evitar mesmo assim.
- **Renumeração coerente**: cada `print_step N` corresponde ao índice real; `[N/12]` aparece para todas as 13 fases (0..12).
- **`set -euo pipefail` (linha 7) preservado**: nova fase usa `&& ||` para neutralizar exit non-zero sem disparar abort.

---

## 5. Riscos e mitigações

| Risco | Mitigação |
|---|---|
| Renumeração quebra grep de outras sprints/docs por "FASE 3 = Ollama" | grep `FASE [0-9]+` em `dev-journey/` antes de commit; documentar mapeamento no commit message |
| `sudo_run apt-get install -y zstd` em ambiente onde apt repos estão stale | `apt-get update` não é pré-requisito desta fase (assumir que usuário rodou antes); se falhar, cai no ramo warn-and-continue |
| Algum pkg-manager nomeia pacote diferente | Em apt/dnf/pacman/zypper, o pacote canônico é `zstd`. Verificado em packages.ubuntu.com, koji.fedoraproject.org, archlinux.org, software.opensuse.org |
| `set -euo pipefail` aborta antes do `\|\|` neutralizar | Padrão `cmd && VAR=1 \|\| VAR=0` é safe em bash 4+; testado em outros pontos do script (`chmod ... 2>/dev/null \|\| true` na FASE 8) |
| Quebra fluxos com Ollama já instalado | FASE 3 vem antes da FASE 4 (Ollama). Se ollama já instalado, FASE 4 dá SKIP. Independência preservada |
| dry-run não mostra a nova fase | Teste explícito no critério: grep `\[3/12\].*zstd` |

---

## 6. Não-objetivos (escopo fora desta sprint)

- Modificar o script oficial upstream do Ollama (proibido por contrato).
- Adicionar verificação de `tar --version` >= versão com suporte nativo a `.zst` (sai do escopo; instalar zstd resolve a maioria dos casos).
- Cachear archive Ollama localmente para evitar re-download (sprint potencial nova: `INFRA-INSTALL-OLLAMA-CACHE-01`, registrar se aparecer).
- Suportar Alpine/BusyBox (apk não está em `detect_pkg_manager`; sprint nova se aparecer: `INFRA-INSTALL-APK-SUPPORT-01`).

---

## 7. Proof-of-work esperado

Runtime real conforme `VALIDATOR_BRIEF.md` seção `[CORE] Contratos de runtime`:

```bash
# Smoke obrigatório (BRIEF check #1)
./run.sh --smoke
# esperado: "boot ok", exit 0

# Invariantes (14/14 atualmente, conforme prompt da sprint)
bash scripts/sprint_invariants.sh
# esperado: PASS 14/14, FAIL 0

# Sintaxe do script tocado
bash -n install.sh
# esperado: exit 0

# Comando que motivou a sprint
command -v zstd
# esperado: caminho válido (ex.: /usr/bin/zstd) em qualquer ambiente após install

# Acentuação periférica (BRIEF check #4) em arquivo modificado
python3 ~/.config/zsh/scripts/validar-acentuacao.py install.sh
# esperado: zero issues

# Hipótese verificada (rg dos identificadores citados, lição 4)
rg -n "detect_pkg_manager|sudo_run|run_or_skip|have_cmd|print_step|print_skip|print_ok|print_warn" install.sh
# esperado: todas presentes; nenhum identificador inventado
```

Validação cross-host opcional mas recomendada (replicação real da causa raiz):

```bash
docker run --rm ubuntu:22.04 bash -c "
    set -e &&
    apt-get update -q &&
    apt-get install -y -q curl git python3 python3-venv sudo ca-certificates &&
    git clone <repo-url> /tmp/nyx &&
    cd /tmp/nyx &&
    ./install.sh --no-prompt --no-vision --no-kitty 2>&1 | tail -30
"
# esperado: chega ao final ('Instalação concluída'), passa FASE 3 (zstd instalado) e FASE 4 (Ollama instalado)
```

---

## 8. Referências

- `VALIDATOR_BRIEF.md` -- contratos de runtime + checks universais.
- `dev-journey/06-sprints/concluidos/SPRINT_VALIDATE_FINAL_01_PARTE_2.md:78` -- registro do achado.
- `dev-journey/07-reports/RELATORIO_VALIDATE_FINAL_01.md:163` -- relato textual da causa raiz.
- `dev-journey/06-sprints/concluidos/SPRINT_INSTALL_SUDO_01.md` -- precedente de modificação de `install.sh` com formato yaml SPEC.
- `dev-journey/06-sprints/concluidos/SPRINT_INFRA_SANITIZER_FIX_04.md:14` -- entrada `desbloqueia` listando esta sprint como dependente futura.
- `install.sh` linhas 102-107 (`detect_pkg_manager`) -- helper já existente reaproveitado.
- `install.sh` linhas 123-129 (`sudo_run`) -- helper já existente reaproveitado.
- `install.sh` linhas 109-117 (`run_or_skip`) -- helper já existente reaproveitado.
- `README.md` seção "Replicação em outro PC (sem TTY / CI)" linha 32 -- contrato de modo CI preservado.
- Memória global `feedback_nenhum_debito.md` -- princípio que motivou registrar este achado como sprint nova.
- Memória global `feedback_smoke_boot.md` -- smoke obrigatório antes de marcar CONCLUIDA.

---

*"O script oficial assume zstd. A imagem mínima não tem. Nosso install protege o usuário antes do upstream estourar." -- INFRA-INSTALL-ZSTD-FALLBACK-01*
