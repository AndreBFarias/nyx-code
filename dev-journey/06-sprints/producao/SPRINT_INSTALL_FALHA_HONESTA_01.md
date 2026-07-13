## 0. SPEC (machine-readable)

```yaml
sprint:
  id: INSTALL-FALHA-HONESTA-01
  numero: 439
  title: "Instalador falha honesto: pull/venv/disco abortam com PT-BR e retomada, não com erro cru em ingles"
  onda: 48
  prioridade: ALTA
  tipo: Bugfix
  dependencias: []
  desbloqueia: []
  absorve: []

  touches:
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/install.sh
      reason: "FASE 0 ganha preflight de disco (df) e de python3-venv/ensurepip; FASES 5-6 envolvem os `ollama pull` em guard explicito com mensagem PT-BR e orientacao de retomada -- nada mais pode morrer seco via set -e no primeiro contato do usuario-alvo"
      linhas_alvo: "0 (FASE 0, 150-170: adicionar 2 guards), 270 (FASE 5 pull default), 288 (FASE 6 pull vision)"
  creates: []
  removes: []

  forbidden:
    - "Adicionar emoji"
    - "Mencao a IA proprietaria em qualquer arquivo"
    - "Remover `set -euo pipefail` (a blindagem e local, via guard `if !`; o set -e continua protegendo o resto)"
    - "Tocar run.sh, nyx/*, proxy, loop -- o achado e 100% no install.sh"
    - "Alterar o happy-path das FASES 5-6: com Ollama de pe e disco/rede ok, o pull segue identico e imprime o mesmo print_ok"
    - "Baixar modelo, subir ollama, subir GPU nesta sprint"
    - "Reintroduzir prompt interativo bloqueante nas fases 0/5/6 (respeitar --no-prompt e --dry-run)"

  tests:
    - cmd: "bash -n install.sh"
      deve_passar: true
    - cmd: "bash scripts/sprint_invariants.sh"
      deve_passar: true
    - cmd: "./run.sh --smoke"
      deve_passar: true

  acceptance_criteria:
    - "AC1 (pull honesto, FASES 5-6): o `ollama pull` do modelo padrão e do moondream roda dentro de um guard `if !`; em falha (rede caiu, disco cheio, daemon 11434 fora) o script imprime print_err em PT-BR com causas provaveis + a frase literal de retomada 'rode ./install.sh novamente -- a instalação e idempotente e o pull continua de onde parou', e sai com exit != 0 SEM despejar apenas o erro cru em ingles do ollama"
    - "AC2 (preflight de disco, FASE 0): antes de venv+pulls, o instalador checa o espaco livre em `$SCRIPT_DIR` via `df -Pm` contra um minimo (MIN_DISK_MB, default 6000); se faltar, aborta com print_err dizendo quanto ha e quanto falta em MB; respeita --dry-run (avisa, não aborta) e degrada gracioso se `df` ausente (print_warn + segue)"
    - "AC3 (preflight python3-venv/ensurepip, FASE 0): antes da FASE 1, testa `python3 -c 'import ensurepip'`; se falhar em distro apt-get, tenta instalar python3-venv via sudo_run (mesmo padrão da FASE 3 do zstd) e revalida; se ainda faltar (ou pkg-manager não-apt), aborta com print_err instruindo o pacote exato (ex.: 'sudo apt install python3-venv') -- nunca deixa a FASE 1 morrer com o traceback cru de ensurepip"
    - "Happy-path intacto: `bash -n install.sh` limpa; com disco/venv/rede ok os prints OK das FASES 0/5/6 sao byte-identicos aos atuais"
    - "Proof runtime-real SEM GPU: `MIN_DISK_MB=99999999 ./install.sh --dry-run` dispara o abort de disco com a mensagem PT-BR do deficit; o proof end-to-end do pull-fail (precisa do daemon ollama de pe para falhar de verdade) fica DEFERIDO para ambiente com Ollama"
    - "invariantes FAIL_AFTER <= FAIL_BEFORE, acentuacao rc=0, smoke boot ok"
```

---

# Sprint INSTALL-FALHA-HONESTA-01 — Instalador que falha honesto (pull, disco, venv)

**Status:** PENDENTE
**Data criação:** 2026-07-12
**Modelo obrigatório:** claude-opus-4-7 (executor-sprint autorizado pelo dono nesta onda)

---

## Contexto do projeto (snapshot — não referência)

> **ADRs relevantes (inline):**
> - **ADR-033 A CADEIA NUNCA QUEBRA NA MÃO DO USUÁRIO:** quando a infra não consegue garantir, a mensagem é clara em PT-BR ("não consegui X porque Y, faça Z"), nunca um erro cru mascarado. A robustez pertence à INFRA, não ao modelo.
> - **ADR-032/034:** o Nyx-Code faz o pior LLM local (qwen 3b) na pior máquina possível parecer um agente profissional offline. O usuário-alvo é leigo, com hardware fraco, internet instável e disco pequeno. O primeiro contato dele é o `install.sh`.
>
> **Estado (2026-07-12):** `qwen2.5-coder:3b`. Origem do achado: auditoria de prontidão 2026-07-12 (achados verificados adversarialmente, evidência `file:line`). O `install.sh` tem 12 fases idempotentes; `set -euo pipefail` no topo (linha 7). As FASES 3 (zstd) e 4 (Ollama install) já tratam falha com guard+mensagem; venv (FASE 1) e os pulls (FASES 5-6) ficaram de fora e morrem secos.

---

## Problema

**Achado (auditoria 2026-07-12):** o caso NOMINAL do público-alvo — internet instável, disco pequeno, distro mínima — termina o primeiro contato com o produto numa tela de erro críptica em inglês no meio da instalação. Três flancos do mesmo mecanismo (`set -euo pipefail` abortando uma fase sem tradução nem orientação):

**1. Pull morre seco (FASES 5-6, `install.sh:270` e `install.sh:288`).**
Verificado no código:
```bash
# FASE 5 (linha 270)
run_or_skip "ollama pull $DEFAULT_MODEL" ollama pull "$DEFAULT_MODEL"
print_ok "$DEFAULT_MODEL baixado"
# FASE 6 (linha 288)
run_or_skip "ollama pull $VISION_MODEL" ollama pull "$VISION_MODEL"
```
Nenhum `|| ...`. Sob `set -e`, qualquer falha do pull (rede caiu, disco encheu no meio dos ~3.4 GiB, daemon `11434` não subiu — ex.: WSL sem systemd) aborta o script na hora com só o erro cru do ollama em inglês. **Contraste:** o `run.sh` trata o mesmo caso com orientação (verificado em `run.sh:468-475`: "Causas possíveis: ... Sem conexão com registry Ollama"). O instalador não tem esse cuidado — e é justamente ele o primeiro contato do usuário.

**2. Nenhum preflight de disco (FASE 0, `install.sh:150-170`).**
Verificado: `grep 'df '` em `install.sh` e `run.sh` retorna zero hits (a única ocorrência de 'espaco' é o comentário de spinner em `run.sh:66`). A FASE 0 checa apenas `python3` (presença + versão >= 3.10) e o pkg-manager; não checa disco. Pontos que consomem disco sem guard: `install.sh:190-192` (pip), `install.sh:270` (~1.9 GiB), `install.sh:288` (~1.7 GiB). Necessidade real mínima ~4-6 GiB. Numa máquina com HD quase cheio o pull morre no meio (ou enche a partição raiz, degradando o sistema), com erro genérico — e o usuário sem contexto não sabe que faltou disco nem quanto precisa.

**3. `python3-venv`/`ensurepip` não validado (FASE 1, `install.sh:180`).**
Verificado: `run_or_skip "criar venv" python3 -m venv "$SCRIPT_DIR/venv"` sob `set -e`. A FASE 0 checa a presença do `python3`, não a do módulo `venv`. Em Ubuntu/Debian mínimos sem o pacote `python3-venv`, `python3 -m venv` falha com `ensurepip is not available` e o `set -e` aborta sem mensagem amigável nem sugestão de pacote — justamente nas distros mais comuns em máquinas fracas/antigas. A FASE 3 (zstd) prova que o instalador sabe fazer guard+instalação de dependência; venv ficou de fora.

**Todos os três ferem ADR-033** ("a cadeia nunca quebra na mão do usuário") no primeiro contato.

---

## Causa-raiz (verificada no código real)

Confirmação linha a linha (as linhas do briefing bateram, com deslize mínimo de faixa):

- `install.sh:7` — `set -euo pipefail`: presente. É o gatilho comum: qualquer comando não-guardado que retorna != 0 aborta o script.
- `install.sh:110-118` — `run_or_skip()`: apenas ecoa/executa `"$@"`; **não** captura falha. Em `--dry-run` retorna 0; fora dele, propaga o exit do comando, que sob `set -e` mata o script.
- `install.sh:150-170` — FASE 0: só `have_cmd python3` + comparação de versão + `detect_pkg_manager`. **Nenhum** `df`, **nenhum** teste de `ensurepip`.
- `install.sh:180` — FASE 1 venv: pull direto sem preflight do módulo.
- `install.sh:270` / `install.sh:288` — FASES 5-6: `ollama pull` via `run_or_skip`, sem `|| print_err`.
- `install.sh:95-99` — helpers `print_err`/`print_warn`/`print_ok`/`print_skip` já existem (reusar, não criar novos).
- `install.sh:124-130` — `sudo_run()` já existe (reusar na instalação do `python3-venv`, mesmo padrão do zstd em `install.sh:222`).
- `run.sh:467-475` — o guard honesto de pull do `run.sh` (referência de tom/idioma para AC1).

**Divergência com o briefing:** nenhuma material. O briefing citava a FASE 0 como "150-169"/"150-164" e o guard do `run.sh` como "468-474"; no código real a FASE 0 vai até 170 e o guard do `run.sh` até 475 (deslize de 1 linha, sem efeito no fix). O briefing também apontava a duplicação do store de modelos como agravante de disco — isso é escopo de outra sprint (`INSTALL-MODELS-STORE-UNIFY-01`, já em `producao/`), aqui só entra como constante de folga no MIN_DISK_MB.

**Coesão:** os três achados são o MESMO mecanismo (`set -e` abortando uma fase do instalador sem falha honesta) no MESMO arquivo. Ficam na mesma sprint, cada um como AC separado.

---

## Solução proposta

Três correções aditivas e cirúrgicas, todas em `install.sh`, reusando os helpers existentes. Sem tocar `set -euo pipefail` (a blindagem é local, via guard `if !`, que não dispara o `set -e`).

### AC2 — preflight de disco (FASE 0, após o bloco do pkg-manager, ~linha 170)

```bash
# INSTALL-FALHA-HONESTA-01: preflight de disco antes de venv (~0.5-1 GiB) +
# modelos (~3.6 GiB). Maquina-alvo tem HD pequeno; disco cheio no meio do pull
# vira erro cru do ollama. Falha honesta ANTES de baixar nada (ADR-033).
MIN_DISK_MB="${MIN_DISK_MB:-6000}"
if have_cmd df; then
    FREE_MB="$(df -Pm "$SCRIPT_DIR" | awk 'NR==2 {print $4}')"
    if [ -n "$FREE_MB" ] && [ "$FREE_MB" -lt "$MIN_DISK_MB" ]; then
        if [ $DRY_RUN -eq 1 ]; then
            print_warn "disco: ${FREE_MB} MB livres, minimo ${MIN_DISK_MB} MB (dry-run: não aborta)"
        else
            print_err "Espaco em disco insuficiente: ${FREE_MB} MB livres, precisa de ${MIN_DISK_MB} MB (venv ~1 GB + modelos ~3.6 GB)."
            print_err "Libere ~$(( MIN_DISK_MB - FREE_MB )) MB e rode ./install.sh novamente."
            exit 1
        fi
    else
        print_ok "Disco: ${FREE_MB} MB livres (minimo ${MIN_DISK_MB} MB)"
    fi
else
    print_warn "df ausente -- pulando checagem de disco"
fi
```

### AC3 — preflight python3-venv/ensurepip (FASE 0, logo após AC2, antes da FASE 1)

```bash
# INSTALL-FALHA-HONESTA-01: em Debian/Ubuntu minimos falta o pacote
# python3-venv e `python3 -m venv` morre com 'ensurepip is not available'.
# Mesmo padrão guard+install da FASE 3 (zstd). Falha honesta com o pacote exato.
if python3 -c 'import ensurepip' 2>/dev/null; then
    print_ok "python3-venv/ensurepip disponivel"
elif [ $DRY_RUN -eq 1 ]; then
    print_skip "ensurepip ausente (dry-run: não instala)"
elif [ "$PKG_MANAGER" = "apt-get" ]; then
    print_warn "python3-venv ausente -- instalando via apt-get"
    run_or_skip "apt install python3-venv" sudo_run apt-get install -y python3-venv || true
    if python3 -c 'import ensurepip' 2>/dev/null; then
        print_ok "python3-venv instalado"
    else
        print_err "python3-venv indisponivel. Instale manualmente: sudo apt install python3-venv"
        exit 1
    fi
else
    print_err "python3 sem o modulo venv (ensurepip ausente). Instale o pacote python3-venv da sua distro e rode ./install.sh novamente."
    exit 1
fi
```

### AC1 — pull honesto (FASES 5-6, envolvendo `install.sh:270` e `install.sh:288`)

Trocar o par `run_or_skip ...pull...; print_ok ...` pelo guard `if !`:

**FASE 5 (linha 270):**
```bash
    if run_or_skip "ollama pull $DEFAULT_MODEL" ollama pull "$DEFAULT_MODEL"; then
        print_ok "$DEFAULT_MODEL baixado"
    else
        print_err "Falha ao baixar $DEFAULT_MODEL. Causas provaveis:"
        print_err "  1. Sem conexão com o registry do Ollama (internet caiu?)"
        print_err "  2. Disco cheio no meio do download (~1.9 GB)"
        print_err "  3. Daemon do ollama fora do ar (ollama serve não subiu)"
        print_err "rode ./install.sh novamente -- a instalação e idempotente e o pull continua de onde parou."
        exit 1
    fi
```

**FASE 6 (linha 288)** — mesmo padrão para `$VISION_MODEL` (~1.7 GB), mantendo a nota `(ADR-022: CPU puro)` no `print_ok`.

Como o guard `if !` roda o comando dentro do contexto de condição, o `set -e` não dispara antes do `else` — o script chega no `print_err` e sai com a mensagem honesta, em vez de morrer seco.

---

## Arquivos alvo (paths absolutos)

### `/home/andrefarias/Desenvolvimento/Nyx-Code/install.sh`

- **Edit 1 (AC2):** inserir o bloco de preflight de disco na FASE 0, após o bloco do pkg-manager (~linha 170).
- **Edit 2 (AC3):** inserir o bloco de preflight `ensurepip` logo após o Edit 1, ainda na FASE 0, antes do cabeçalho da FASE 1.
- **Edit 3 (AC1):** trocar o par pull+print_ok da FASE 5 (linha 270-271) pelo guard `if !`.
- **Edit 4 (AC1):** trocar o par pull+print_ok da FASE 6 (linha 288-289) pelo guard `if !`.

---

## Diff esperado (resumo)

```
~ 1 arquivo modificado (install.sh)
+ ~45 linhas líquidas (fix aditivo; sem meta numérica de tamanho)
```

Sem aritmética de extração: esta sprint não tem meta `arquivo < NNNL`. O único número relevante é o net-add (~45L) num único arquivo shell.

---

## Comandos de verificação (literais, copy-paste)

```bash
cd /home/andrefarias/Desenvolvimento/Nyx-Code

# 1. Sintaxe do shell (a estatica que vale para bash; ruff não se aplica a .sh)
bash -n install.sh

# 2. Reconferir as ancoras (linhas podem ter deslizado -- reconferir):
rg -n "set -euo pipefail|ollama pull|df -Pm|import ensurepip|MIN_DISK_MB" install.sh

# 3. PROOF RUNTIME-REAL sem GPU/Ollama -- forcar o abort de disco (AC2):
#    MIN_DISK_MB absurdo forca o deficit; --dry-run mantem seguro (nada destrutivo).
MIN_DISK_MB=99999999 ./install.sh --dry-run 2>&1 | rg -n "insuficiente|dry-run: não aborta|MB livres"

# 4. PROOF RUNTIME-REAL sem GPU -- caminho feliz do preflight (disco normal):
./install.sh --dry-run 2>&1 | rg -n "Disco:|ensurepip|dry-run"

# 5. Confirmar que os pulls estao guardados (AC1) -- nenhum pull solto restou:
rg -n "if run_or_skip \"ollama pull|continua de onde parou" install.sh

# 6. DEFERIDO (precisa do daemon ollama de pe): forcar o pull a falhar de verdade
#    (ex.: parar o ollama e rodar so a FASE 5) e conferir a mensagem PT-BR + exit 1.
#    Executar so em ambiente com Ollama; não subir GPU nesta sprint.
```

> Nota: os passos 3-4 rodam com `--dry-run` (nenhum comando destrutivo, o código pula pip/pull/venv). Não sobem Ollama nem GPU. O passo 6 é o único que exige o daemon do Ollama para provocar a falha real do pull — fica DEFERIDO para o ambiente com Ollama, como as specs 403/407 fazem com proof que depende de GPU.

---

## Critério binário de aceite (IA executora)

- [ ] AC2: preflight de disco na FASE 0 com `df -Pm`, MIN_DISK_MB (default 6000), print_err do déficit em MB, respeita `--dry-run` e degrada se `df` ausente
- [ ] AC3: preflight `ensurepip` na FASE 0; em apt-get tenta `python3-venv` via `sudo_run` e revalida; senão aborta com o pacote exato
- [ ] AC1: FASES 5-6 com guard `if !`, print_err PT-BR com causas prováveis + a frase literal de retomada, `exit 1` na falha
- [ ] Proof passo 3 colado: `MIN_DISK_MB=99999999 ./install.sh --dry-run` imprime a mensagem PT-BR do déficit de disco
- [ ] Proof passo 4 colado: caminho feliz dos preflights imprime OK sem abortar
- [ ] Happy-path intacto: `bash -n install.sh` limpo; prints OK das FASES 0/5/6 preservados
- [ ] `set -euo pipefail` mantido; run.sh e nyx/* intocados
- [ ] acentuação rc=0, `FAIL_AFTER <= FAIL_BEFORE`, `./run.sh --smoke` imprime `boot ok`
- [ ] `SPRINT_ORDER_MASTER.md` marca 439 CONCLUIDA; spec movida para `concluidos/` (integração do orquestrador)
- [ ] NÃO commitar; NÃO tocar Checkpoint.md; NÃO baixar modelo/subir GPU

---

## Guardrails anti-engodo (obrigatórios)

NÃO marcar concluída se:
- Removeu `set -euo pipefail` para "simplificar" (a blindagem tem de ser local via `if !`; o `set -e` continua protegendo o resto do script).
- O guard de pull ficou sem a frase de retomada (`rode ./install.sh novamente ...`) — ela é o núcleo da falha honesta (o usuário precisa saber que basta rodar de novo).
- O preflight de disco aborta em `--dry-run` (deve só avisar) ou não trata `df` ausente.
- O preflight de `ensurepip` aborta em distro não-apt sem antes imprimir o pacote a instalar.
- O happy-path mudou: com disco/venv/rede ok, os prints OK e os `ollama pull` devem seguir equivalentes ao atual.
- Tocou `run.sh` ou qualquer `.py` (o achado é 100% no `install.sh`).
- Proof do passo 3 (abort de disco forçado) não colado.

Se algo falhar: `[SPRINT 439] BLOQUEADA: <motivo 1 linha>`.

---

## Proof-of-work obrigatório

```bash
bash scripts/sprint_invariants.sh > /tmp/inv_before.txt 2>&1
FAIL_BEFORE=$(grep -c "^\[FAIL\]" /tmp/inv_before.txt)
# implementar
bash scripts/sprint_invariants.sh > /tmp/inv_after.txt 2>&1
FAIL_AFTER=$(grep -c "^\[FAIL\]" /tmp/inv_after.txt)
diff /tmp/inv_before.txt /tmp/inv_after.txt
```
Baseline esperado: `FAIL_BEFORE = 0`, `FAIL_AFTER <= 0`. Colar: `bash -n install.sh` (silêncio = ok), o output dos passos 3-4-5 acima, `rg` do passo 2, `git --no-pager diff --stat install.sh`, `python3 ~/.config/zsh/scripts/validar-acentuacao.py --paths install.sh` (rc=0) e `./run.sh --smoke` (deve imprimir `boot ok`).

---

## Gambiarras específicas desta sprint

- **`df -Pm` (POSIX + MB):** `-P` força uma linha por filesystem (evita quebra de linha em dispositivos de nome longo) e `-m` dá o valor já em MB — sem aritmética de blocos. O `awk 'NR==2 {print $4}'` pega a coluna "Available" da segunda linha. Guardar com `[ -n "$FREE_MB" ]` porque em filesystem exótico o `df` pode não trazer a coluna.
- **`if !`/`if run_or_skip` não dispara `set -e`:** comando em contexto de condição tem o `set -e` suspenso pelo bash — por isso o guard captura a falha em vez de matar o script. É o mesmo idioma da FASE 3 (zstd), que já usa `&& ZSTD_OK=1 || ZSTD_OK=0`.
- **`ensurepip` como teste barato:** `python3 -c 'import ensurepip'` é o sinal exato que `python3 -m venv` usa; testar o import é mais rápido e não cria diretório temporário.
- **MIN_DISK_MB via env:** deixar override por env permite o proof forçado (`MIN_DISK_MB=99999999`) e afrouxar em CI/Docker (`NYX_INSTALL_SKIP_PULL=1` baixa a necessidade real, mas manter o default 6000 é conservador e seguro para o usuário-alvo).
- **`--dry-run` só avisa:** os três guards respeitam `--dry-run` (o instalador é idempotente e o dry-run não pode abortar) — abortar em dry-run quebraria o uso de inspeção.

---

## Validação humana (checklist do usuário)

```bash
cd /home/andrefarias/Desenvolvimento/Nyx-Code
git --no-pager show --stat HEAD

# Disco: forcar o deficit e ver a mensagem PT-BR (seguro, dry-run):
MIN_DISK_MB=99999999 ./install.sh --dry-run

# venv: em uma VM Debian minima sem python3-venv, ./install.sh deve avisar e
# tentar instalar (apt) ou instruir o pacote -- nunca cuspir o traceback cru.

# pull: com o ollama parado, rodar so a FASE 5 deve terminar com a mensagem
# PT-BR de retomada, não com o erro cru em ingles.

ls dev-journey/06-sprints/concluidos/SPRINT_INSTALL_FALHA_HONESTA_01.md  # apos integração
```

---

## Fora de escopo (anti-débito)

| Item | Decisão |
|------|---------|
| Unificar o store duplicado de modelos (`models/` do dev ocupa 11 GB; dobra a necessidade de disco) | JÁ é sprint própria: `INSTALL-MODELS-STORE-UNIFY-01` (em `producao/`). Aqui só entra como folga na constante MIN_DISK_MB. NÃO reabrir. |
| Retomada automática do pull com retry/backoff no próprio instalador | NÃO-OBJETIVO. A retomada é o próprio ollama (idempotente); a sprint só orienta o usuário a rodar de novo. Se o dono quiser retry automático, registrar `INSTALL-PULL-RETRY-01` (anti-débito: `feedback_nenhum_debito`). |
| Preflight de RAM/VRAM no instalador | Fora de escopo — a checagem de VRAM já vive no `run.sh`/proxy (guards OOM). Não duplicar no install. |
| Tornar o `run.sh:467` (re-pull de fallback) também guardado por `df` | O `run.sh` já dá orientação PT-BR no pull (verificado, `run.sh:468-475`); o déficit de disco no `run.sh` é achado separado. Registrar `RUN-PULL-DISK-GUARD-01` se o dono priorizar. |

---

## Referências

- BRIEF: `/home/andrefarias/Desenvolvimento/Nyx-Code/VALIDATOR_BRIEF.md`
- Origem: auditoria de prontidão 2026-07-12, relatório durável `dev-journey/07-reports/AUDIT_2026_07_12.md` §3 (briefing efêmero da sessão de auditoria)
- Padrão de guard+install de dependência: `install.sh:212-234` (FASE 3, zstd) — modelo para AC3
- Tom/idioma de pull honesto: `run.sh:463-481` (`check_model`) — modelo para AC1
- Precedentes de instalador: `SPRINT_INFRA_INSTALL_ZSTD_FALLBACK_01.md`, `SPRINT_INSTALL_SUDO_01.md` (concluídos), `SPRINT_INSTALL_MODELS_STORE_UNIFY_01.md` (producao)

---

*"O primeiro contato do usuário-alvo com o produto não pode ser um traceback em inglês. Um instalador que aborta seco é a cadeia quebrando na mão de quem menos tem contexto para consertar." — ADR-033*
