## 0. SPEC (machine-readable)

```yaml
sprint:
  id: INSTALL-MODELS-STORE-UNIFY-01
  numero: 430
  title: "install.sh baixa os modelos no store do projeto (models/), não no store do sistema -- fim do re-download no 1o boot e do moondream morto"
  onda: 48
  prioridade: ALTA
  tipo: Bugfix
  dependencias: []
  desbloqueia: []
  absorve: []

  touches:
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/install.sh
      reason: "antes das FASES 5 e 6, alinhar o store dos pulls ao do run.sh: exportar OLLAMA_MODELS=$SCRIPT_DIR/models + OLLAMA_HOST=127.0.0.1:11435, subir um daemon `ollama serve` temporario próprio na porta do projeto (mesmo padrão do run.sh start_ollama) e derruba-lo ao fim; assim os blobs de qwen2.5-coder:3b e moondream caem em models/ e as checagens de skip (ollama list) consultam o store certo"
      linhas_alvo: "256-290 (FASES 5 e 6); helper novo + cleanup/trap adicionados acima da FASE 5"
  creates: []
  removes: []

  forbidden:
    - "Adicionar emoji"
    - "Usar 'print()' fora de cli.py/output.py (N/A: shell)"
    - "Mencao a IA proprietaria"
    - "Tocar run.sh (check_model, start_ollama, exports OLLAMA_*) -- o run.sh ja esta correto; o defeito e so no install.sh"
    - "Tocar nyx/config/defaults.py, nyx/providers/vision_client.py"
    - "Trocar modelo, porta ou placa (ADR: infra sobre hardware)"
    - "Quebrar o guard NYX_INSTALL_SKIP_PULL=1 (DEPLOY-01B): com ele setado, NENHUM daemon temporario sobe e NENHUM pull roda"
    - "Alterar o fluxo das FASES 0-4, 7+ (so 5-6 e o helper acima delas)"

  tests:
    - cmd: "bash -n install.sh"
      deve_passar: true
    - cmd: "bash scripts/sprint_invariants.sh"
      deve_passar: true
    - cmd: "DEFERIDO_GPU: ./install.sh --no-prompt (rede) + desligar rede + ./run.sh --smoke (sem re-download)"
      deve_passar: true

  acceptance_criteria:
    - "Antes da FASE 5, install.sh exporta OLLAMA_MODELS=$SCRIPT_DIR/models e OLLAMA_HOST=127.0.0.1:<porta-projeto> (default 11435), de modo que TANTO as checagens de skip (ollama list, install.sh:265/283) QUANTO os pulls (install.sh:270/288) atinjam o store do projeto -- não o store default do daemon do sistema (~/.ollama ou /usr/share/ollama)"
    - "install.sh sobe um daemon `ollama serve` temporario próprio na porta do projeto (mesmo padrão de run.sh:415-431: serve backgrounded + poll em /api/version) apenas quando ha pull a fazer, e o derruba via cleanup/trap ao fim (nada de daemon orfao)"
    - "Ao fim de um install com rede, $SCRIPT_DIR/models contem os manifests de qwen2.5-coder:3b (~1.80 GiB) E moondream (~1.62 GiB); nenhum blob novo do Nyx-Code fica no store do sistema"
    - "Primeiro ./run.sh offline: check_model (run.sh:464) encontra o qwen ja em models/ e não cai no re-pull (run.sh:467) nem no exit 1 de 'Sem conexão com registry' (run.sh:468-475) -- zero acesso a registry"
    - "moondream fica visivel ao VisionClient (nyx/providers/vision_client.py:25 -> OLLAMA_URL 11435): a feature de visao deixa de ser 1.62 GiB morto no store errado (ADR-034: nenhuma feature assume disco abundante)"
    - "Idempotencia: re-rodar install.sh com os modelos ja em models/ imprime print_skip ('ja baixado') sem re-baixar; o guard NYX_INSTALL_SKIP_PULL=1 (DEPLOY-01B) segue pulando FASES 5-6 sem subir daemon algum"
    - "bash -n install.sh limpo, acentuacao rc=0, invariantes FAIL_AFTER <= FAIL_BEFORE"
```

---

# Sprint INSTALL-MODELS-STORE-UNIFY-01 -- install.sh baixa no store do projeto, não no do sistema

**Status:** PENDENTE
**Data criação:** 2026-07-12
**Modelo obrigatorio:** claude-opus-4-7 (executor-sprint autorizado pelo dono nesta onda)

---

## Contexto do projeto (snapshot -- não referencia)

> **Missao:** o Nyx-Code faz o pior LLM local (qwen 3b) na pior maquina possivel parecer um agente de codigo profissional offline. Robustez pertence a INFRA, não ao modelo (ADR-032/033/034). O usuario-alvo e leigo, sem hardware bom e frequentemente sem internet estavel.
>
> **ADRs relevantes (inline):**
> - **ADR-034 (nenhuma feature assume VRAM/CPU/disco abundantes):** baixar 3.4 GiB de modelos e joga-los no store errado (mortos, re-baixados) viola diretamente o principio; disco fraco não pode carregar duplicatas.
> - **ADR-032/033 (a infra carrega o modelo / enforcement, não confianca):** a premissa "sem internet apos instalar" e um contrato da infra; se o install baixa o modelo mas o run.sh não o enxerga, a infra quebrou a própria promessa.
>
> **Estado (2026-07-12):** `qwen2.5-coder:3b`. Ports do projeto: Ollama `11435`, proxy `11436` (`nyx/config/defaults.py:45-53`). O run.sh sobe um daemon Ollama PRÓPRIO em 11435 com store `$SCRIPT_DIR/models` (run.sh:246-247); o install.sh não -- ele fala com o daemon default do sistema em 11434. Origem do achado: auditoria de prontidao 2026-07-12 (achados verificados adversarialmente com evidencia file:line).

---

## Problema

Dois achados da auditoria, **mesmo mecanismo**: o `install.sh` baixa os modelos num store diferente do que o `run.sh` consome. Consequencia dupla no usuario-alvo (leigo, internet emprestada, disco fraco):

1. **Re-download no 1o boot offline.** O usuário instala com internet emprestada (lan house, wifi publico), chega em casa offline, roda `./run.sh` e o boot morre pedindo registry -- porque o modelo baixado no install esta invisivel para o run.sh.
2. **moondream morto + duplicata em disco.** A visao baixa 1.62 GiB que nunca sao vistos; qwen (1.80 GiB) fica duplicado entre o store do sistema e `models/`.

### Evidencia verificada no codigo real (linhas reconferidas 2026-07-12)

- **install.sh não seta store algum** (grep confirma zero `OLLAMA_MODELS`/`OLLAMA_HOST` no arquivo):
  - `install.sh:270` -> `run_or_skip "ollama pull $DEFAULT_MODEL" ollama pull "$DEFAULT_MODEL"`
  - `install.sh:288` -> `run_or_skip "ollama pull $VISION_MODEL" ollama pull "$VISION_MODEL"`
  - As checagens de skip tambem consultam o store do sistema: `install.sh:265` (`ollama list ... grep -q "^${DEFAULT_MODEL}$"`) e `install.sh:283` (idem para `$VISION_MODEL`).
  - Sem `OLLAMA_HOST`/`OLLAMA_MODELS`, o pull vai ao daemon default do sistema (porta 11434, store `~/.ollama` ou `/usr/share/ollama`), instalado pelo script oficial na FASE 4 (`install.sh:238-256`).
- **run.sh usa OUTRO store** (verificado):
  - `run.sh:246-247` -> `export OLLAMA_HOST="${NYX_OLLAMA_HOST}:${NYX_OLLAMA_PORT}"` + `export OLLAMA_MODELS="$SCRIPT_DIR/models"`.
  - `run.sh:126-127` -> `NYX_OLLAMA_PORT="${NYX_OLLAMA_PORT:-11435}"`, `NYX_OLLAMA_HOST="${NYX_OLLAMA_HOST:-127.0.0.1}"`.
  - `run.sh:415-431` sobe daemon próprio (`"$OLLAMA_BIN" serve` backgrounded + poll em `/api/version`).
  - `run.sh:463-476` -> `check_model()`: `if ! "$OLLAMA_BIN" list ... grep -q "$MODEL"` (linha 464), cai em `"$OLLAMA_BIN" pull "$MODEL"` (467) e, sem rede, em `log_err "Sem conexão com registry Ollama"` + `exit 1` (linha 468-475).
- **check_model so puxa o `$MODEL` (qwen), nunca o moondream** (verificado: nenhuma referencia a `moondream`/`VISION` dentro de `check_model`) -- ou seja, mesmo que o run.sh re-baixasse o qwen, o moondream continuaria dependendo exclusivamente do store certo no install.
- **VisionClient consome 11435** (verificado): `nyx/providers/vision_client.py:25` -> `def __init__(self, ollama_url: str = OLLAMA_URL, ...)`, com `nyx/config/defaults.py:45` -> `OLLAMA_PORT: int = 11435` -> `OLLAMA_URL = http://127.0.0.1:11435`. O moondream precisa estar no store de 11435 (o daemon do projeto) para a visao funcionar.

Tamanhos reais (manifests locais, do briefing): qwen2.5-coder:3b = **1.80 GiB**, moondream = **1.62 GiB**. Custo do defeito para o usuário de internet lenta: ~3.4 GiB no install **+** ~1.8 GiB re-baixados no 1o `./run.sh`, com ~3.4 GiB de duplicata/morto no store do sistema que o `uninstall.sh` não remove.

---

## Causa-raiz (verificada no codigo)

**Divergencia de store entre os dois entrypoints.** O `run.sh` isola tudo num daemon Ollama próprio (porta 11435, store `$SCRIPT_DIR/models`) -- decisao de projeto para local-first, offline e reprodutivel. O `install.sh` foi escrito antes desse contrato (ou não acompanhou) e delega os pulls ao daemon default do sistema (11434, `~/.ollama`), que a FASE 4 acabou de instalar via script oficial. Nada no `install.sh` exporta `OLLAMA_MODELS`/`OLLAMA_HOST`, entao os blobs caem no lugar que o `run.sh` nunca le.

**não ha divergencia entre briefing e codigo** nas linhas centrais (270, 288, 265, 283, 246-247, 464). Unica derrapagem menor: o briefing cita o bloco de erro do `check_model` como `run.sh:468-471`; no codigo atual ele vai de **468 a 475** (`log_err` + `exit 1` + `list` de fallback). não muda o diagnostico.

---

## solução proposta

Alinhar o store do `install.sh` ao do `run.sh`, cirurgicamente, **so nas FASES 5-6**, reusando o mesmo padrão de daemon temporario do `run.sh:415-431`:

1. **Exportar o store do projeto antes da FASE 5.** Definir (com os mesmos defaults do run.sh) `NYX_OLLAMA_PORT=${NYX_OLLAMA_PORT:-11435}`, `NYX_OLLAMA_HOST=${NYX_OLLAMA_HOST:-127.0.0.1}`, `export OLLAMA_HOST="${NYX_OLLAMA_HOST}:${NYX_OLLAMA_PORT}"`, `export OLLAMA_MODELS="$SCRIPT_DIR/models"`. Com isso, as checagens de skip (`ollama list`, linhas 265/283) e os pulls (270/288) passam a operar sobre o store do projeto.
2. **Subir um daemon temporario próprio na porta do projeto**, apenas quando ha pull a fazer (respeitando `NYX_INSTALL_SKIP_PULL=1`, `have_cmd ollama` e os skips de "ja baixado"). Reproduzir o padrão do `run.sh start_ollama`: `mkdir -p "$SCRIPT_DIR/models" "$SCRIPT_DIR/logs"`, `"$(command -v ollama)" serve >> logs/ollama-install.log 2>&1 &`, guardar o PID, `disown`, e poll em `curl -sf http://127.0.0.1:$PORT/api/version` com timeout curto.
3. **Derrubar o daemon temporario ao fim** via função de cleanup registrada em `trap` (e chamada explicita apos a FASE 6), matando pelo PID guardado. Nada de daemon orfao; o `run.sh` sobe o seu próprio depois.

Preferir um helper único (ex.: `ensure_project_ollama()` + `stop_project_ollama()`) chamado **uma vez antes da FASE 5** e **uma vez apos a FASE 6**, para não duplicar logica entre as duas fases e para que ambos os pulls compartilhem o mesmo daemon temporario.

**Guardas preservados:** o ramo `NYX_INSTALL_SKIP_PULL=1` (DEPLOY-01B, install.sh:263-264/279-280) deve continuar pulando as fases **sem** subir daemon algum; o ramo `! have_cmd ollama` (267-268/285-286) segue com `print_warn` e sem daemon.

### Por que install.sh e não "delegar ao run.sh"?

O briefing lista como alternativa estender o `check_model` do run.sh para puxar tambem o moondream. Rejeitada por dois motivos: (a) mantem o defeito primario (re-download no 1o boot) porque o install ainda baixaria no store errado, so mudaria QUEM re-baixa; (b) transfere trabalho de rede para o primeiro boot -- exatamente o momento em que o usuario-alvo esta offline. Corrigir na origem (install.sh) honra a premissa "sem internet apos instalar".

---

## Arquivos alvo (paths absolutos)

### `/home/andrefarias/Desenvolvimento/Nyx-Code/install.sh`

Regiao: acima da FASE 5 (novo helper + trap) e dentro/entre as FASES 5-6 (linhas 256-290). Sem tocar FASES 0-4 nem 7+.

Esboco de implementacao (o executor ajusta nomes/estilo ao arquivo; a forma abaixo e guia, não literal obrigatorio):

```sh
# --- INSTALL-MODELS-STORE-UNIFY-01: store do projeto (paridade com run.sh) ---
# O run.sh sobe um daemon Ollama próprio em 11435 com store $SCRIPT_DIR/models.
# O install DEVE baixar no MESMO store, senao o 1o ./run.sh offline re-baixa
# tudo (registry) e o moondream fica morto no store do sistema (ADR-034).
NYX_OLLAMA_PORT="${NYX_OLLAMA_PORT:-11435}"
NYX_OLLAMA_HOST="${NYX_OLLAMA_HOST:-127.0.0.1}"
export OLLAMA_HOST="${NYX_OLLAMA_HOST}:${NYX_OLLAMA_PORT}"
export OLLAMA_MODELS="$SCRIPT_DIR/models"

INSTALL_OLLAMA_PID=""
stop_project_ollama() {
    [ -n "$INSTALL_OLLAMA_PID" ] && kill "$INSTALL_OLLAMA_PID" 2>/dev/null || true
    INSTALL_OLLAMA_PID=""
}
trap stop_project_ollama EXIT

ensure_project_ollama() {
    # ja de pe? (curl na porta do projeto)
    curl -sf "http://${NYX_OLLAMA_HOST}:${NYX_OLLAMA_PORT}/api/version" >/dev/null 2>&1 && return 0
    mkdir -p "$SCRIPT_DIR/models" "$SCRIPT_DIR/logs"
    "$(command -v ollama)" serve >> "$SCRIPT_DIR/logs/ollama-install.log" 2>&1 &
    INSTALL_OLLAMA_PID=$!
    disown "$INSTALL_OLLAMA_PID" 2>/dev/null || true
    local elapsed=0
    while ! curl -sf "http://${NYX_OLLAMA_HOST}:${NYX_OLLAMA_PORT}/api/version" >/dev/null 2>&1; do
        sleep 1; elapsed=$((elapsed + 1))
        [ "$elapsed" -ge 30 ] && { print_warn "daemon Ollama do projeto não subiu em 30s (ver logs/ollama-install.log)"; return 1; }
    done
    return 0
}
```

Nas FASES 5 e 6, no ramo `else` que hoje chama `run_or_skip "ollama pull ..."` (install.sh:269-271 e 287-289), chamar `ensure_project_ollama` antes do pull. Como as checagens de skip (265/283) agora consultam o store do projeto via `OLLAMA_HOST`, elas so acertam se um daemon do projeto estiver de pe; para manter o skip correto em re-install, subir o daemon uma vez antes da FASE 5 (`ensure_project_ollama || true`) e chamar `stop_project_ollama` apos a FASE 6.

---

## Diff esperado (resumo)

```
~ 1 arquivo modificado (install.sh)
+ ~30-40 linhas liquidas (helper ensure_project_ollama/stop_project_ollama + trap + exports + 2 chamadas)
```

Sem aritmetica de extracao: esta sprint **não** tem meta `arquivo < NNNL`. O único numero relevante e o net-add (~30-40L) num único arquivo shell. Numeros de disco/rede (1.80 GiB qwen, 1.62 GiB moondream, ~1.8 GiB de re-download evitado) sao a metrica de impacto, não de tamanho de arquivo.

---

## Comandos de verificação (literais, copy-paste)

```bash
cd /home/andrefarias/Desenvolvimento/Nyx-Code

# 1. Sintaxe do shell (obrigatorio, roda sem GPU/rede):
bash -n install.sh

# 2. Confirmar a hipotese das ancoras (linhas podem ter deslizado -- reconferir):
rg -n "OLLAMA_MODELS|OLLAMA_HOST|ollama pull|ollama serve|ensure_project_ollama|NYX_INSTALL_SKIP_PULL" install.sh

# 3. Confirmar que os guards não regrediram (DEPLOY-01B intacto):
rg -n "NYX_INSTALL_SKIP_PULL" install.sh   # ainda pula FASES 5-6 sem subir daemon

# 4. Invariantes do projeto (não deve regredir; install.sh não afeta o core):
bash scripts/sprint_invariants.sh   # esperado PASS 14/14 FAIL 0

# 5. Acentuacao da spec e do arquivo tocado:
python3 ~/.config/zsh/scripts/validar-acentuacao.py --paths dev-journey/06-sprints/producao/SPRINT_INSTALL_MODELS_STORE_UNIFY_01.md

# 6. [DEFERIDO -- exige rede + Ollama + disco/GPU exclusiva] Prova end-to-end:
#    a) com rede:   ./install.sh --no-prompt
#    b) verificar:  OLLAMA_MODELS="$PWD/models" ollama list  # qwen2.5-coder:3b E moondream presentes
#    c) verificar:  ls models/manifests -R | rg 'qwen2.5-coder|moondream'
#    d) SEM rede (desligar wifi): ./run.sh --smoke
#       -> deve imprimir 'boot ok' SEM tocar o registry (check_model acha o qwen em models/)
#    e) visao:      mandar imagem para o VisionClient (11435) e obter descrição (moondream vivo)
```

> Nota GPU/rede: os passos 1-5 rodam SEM Ollama/GPU/rede (estatica + invariantes). O passo 6 (prova end-to-end) exige rede para o download e depois disco/GPU para o smoke -- **DEFERIDO para GPU exclusiva**, executar so quando `pgrep -af "Luna.*driver|valida_sprint"` estiver vazio (protocolo anti-contencao do BRIEF), a exemplo das specs 403/407.

---

## Criterio binario de aceite (IA executora)

- [ ] `install.sh` exporta `OLLAMA_MODELS="$SCRIPT_DIR/models"` e `OLLAMA_HOST=127.0.0.1:<porta>` antes da FASE 5
- [ ] Helper que sobe daemon temporario próprio (padrão run.sh:415-431) e o derruba via `trap`/cleanup (sem orfao)
- [ ] Skips (`ollama list`, 265/283) e pulls (270/288) operam sobre o store do projeto, não o do sistema
- [ ] Guard `NYX_INSTALL_SKIP_PULL=1` intacto: pula FASES 5-6 SEM subir daemon; ramo `! have_cmd ollama` intacto
- [ ] `bash -n install.sh` limpo; `rg` do passo 2/3 confirma exports + guard
- [ ] Invariantes `FAIL_AFTER <= FAIL_BEFORE`; acentuacao rc=0
- [ ] Prova end-to-end (passo 6) colada OU marcada DEFERIDO_GPU com justificativa (contencao)
- [ ] `SPRINT_ORDER_MASTER.md` marca 430 conforme fluxo do orquestrador; spec movida para `concluidos/` ao concluir
- [ ] não commitar; não tocar Checkpoint.md; não tocar run.sh, defaults.py, vision_client.py

---

## Guardrails anti-engodo (obrigatorios)

não marcar concluida se:
- O daemon temporario não e derrubado (deixa `ollama serve` orfao segurando VRAM/porta para o `run.sh` seguinte).
- Os exports ficaram DEPOIS dos pulls (a ordem e o nucleo do fix: store ANTES do skip-check e do pull).
- O guard `NYX_INSTALL_SKIP_PULL=1` passou a subir daemon (quebra DEPLOY-01B/Docker/Gauntlet).
- Tocou `run.sh` para "compensar" (o run.sh ja esta correto; o defeito e no install.sh).
- A prova end-to-end não foi colada nem marcada DEFERIDO_GPU com justificativa de contencao.

Se algo falhar: `[SPRINT 430] BLOQUEADA: <motivo 1 linha>`.

---

## Proof-of-work esperado

- Diff final (`git --no-pager diff --stat` + `git --no-pager diff install.sh`).
- `bash -n install.sh` limpo.
- `rg` dos passos 2-3 (exports presentes, guard intacto, ancoras confirmadas).
- `bash scripts/sprint_invariants.sh` -> PASS 14/14 FAIL 0 (before/after + diff).
- Acentuacao rc=0 na spec.
- **DEFERIDO para GPU/rede exclusiva** (como 403/407): prova end-to-end do passo 6 (install com rede -> `models/` com qwen+moondream -> `./run.sh --smoke` offline sem tocar registry -> visao viva). Rodar so com `pgrep -af "Luna.*driver|valida_sprint"` vazio.

Baseline: `FAIL_BEFORE = 0`, esperado `FAIL_AFTER <= 0`.

---

## Fora de escopo (anti-debito)

| Item | Decisao |
|------|---------|
| Limpeza do store do SISTEMA no `uninstall.sh` (remover blobs antigos de `~/.ollama` / `/usr/share/ollama`) | **Fora de escopo.** Apos este fix, instalações novas nunca populam o store do sistema, logo não ha o que limpar no caminho feliz. Instalacoes ja "sujas" (feitas antes do fix) tem blobs orfaos la; registrar sprint própria `INFRA-UNINSTALL-SYSTEM-STORE-CLEANUP-01` se o dono quiser cobrir migracao de instalações antigas (`feedback_nenhum_debito`). Nota: `uninstall.sh:100-102` ja remove `$SCRIPT_DIR/models`. |
| Estender `check_model` do run.sh para puxar moondream | **Fora de escopo e desaconselhado.** Manteria o re-download no 1o boot (offline). Coberto pela correcao na origem (install.sh). |
| Hardening do daemon temporario contra porta 11435 ja ocupada por outro projeto durante o install | **Fora de escopo.** O `ensure_project_ollama` faz curl antes de subir; se a porta ja responde, reusa. Caso patologico (porta ocupada por processo não-Ollama) e raro no momento do install e ja tratado pelo run.sh no boot (run.sh:379-395). |

---

## Riscos e não-objetivos

| Risco / não-objetivo | Decisao |
|-------|-----------|
| Daemon do sistema (11434) e daemon temporario (11435) coexistindo durante o install | Esperado e seguro: portas distintas, stores distintos. O temporario e derrubado ao fim. |
| Timeout do daemon temporario não subir em 30s (maquina fraca) | `print_warn` + segue; os ramos existentes de erro do pull continuam validos. Alinhar o timeout ao `OLLAMA_START_TIMEOUT` do run.sh se ja exportado no ambiente. |
| Tocar a cascata de portas/boot do run.sh | não-OBJETIVO. O run.sh esta correto; o fix e inteiramente no install.sh. |
| Mudar modelo/porta/placa | Proibido (ADR: infra sobre hardware). |

---

## Referencias

- BRIEF: `/home/andrefarias/Desenvolvimento/Nyx-Code/VALIDATOR_BRIEF.md`
- Origem: auditoria de prontidão 2026-07-12, relatório durável `dev-journey/07-reports/AUDIT_2026_07_12.md` §3 (briefing efêmero da sessão de auditoria)
- Evidencia de codigo: `install.sh:256-290` (FASES 5-6), `run.sh:126-127,246-247,415-431,463-476`, `nyx/config/defaults.py:45`, `nyx/providers/vision_client.py:25`, `uninstall.sh:100-102`
- Memoria do projeto: `project_moondream_models_projeto.md` (moondream em `models/` do projeto), `feedback_nenhum_debito.md`
- Precedente de estrutura: `dev-journey/06-sprints/producao/SPRINT_EXEC_CONTRACT_PROXY_STATUS_BEFORE_JSON_01.md`

---

*"Baixar 3.4 GiB e joga-los no store errado não e economia de rede -- e cobrar a conta duas vezes do usuário que menos pode pagar." -- ADR-034, nenhuma feature assume recurso abundante.*
