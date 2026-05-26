# SPRINT 240 — INFRA-BOOT-HANG-DIAGNOSE-01

## 0. SPEC (machine-readable)

```yaml
sprint:
  id: INFRA-BOOT-HANG-DIAGNOSE-01
  title: "Diagnosticar e resolver run.sh travando entre acquire_lock e start_ollama"
  onda: 31
  prioridade: ALTA
  tipo: Bugfix
  dependencias: [UX-BOOT-SILENT-SPINNER-01]
  desbloqueia: []

  touches:
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/run.sh
      reason: "Boot trava em algum lugar entre update_next_sprint.py e Iniciando Ollama -- usuario reportou 'a nyx nao inicia'"
  creates: []
  removes: []

  forbidden:
    - "Adicionar emoji"
    - "Mencao a IA proprietaria em codigo/commit"   # noqa-anonimato
    - "Mexer em nyx/cli.py (sprint sobre run.sh apenas)"

  tests:
    - cmd: "./run.sh --smoke"
      timeout: 10
      deve_passar: true
    - cmd: "bash scripts/sprint_invariants.sh"
      timeout: 30
      deve_passar: true

  acceptance_criteria:
    - "Fase 1: causa-raiz documentada com prova literal (qual linha trava)"
    - "Fase 2: fix aplicado (timeout, SIGKILL agressivo, ou refactor)"
    - "Fase 3: 3 boots seguidos via `./run.sh --smoke` exit 0 dentro de 5s cada"
    - "Smoke + invariantes preservados"
```

---

# Sprint 240 — INFRA-BOOT-HANG-DIAGNOSE-01

**Status:** CONCLUIDA
**Data criação:** 2026-05-25
**Data conclusão:** 2026-05-25
**Modelo obrigatório:** claude-opus-4-7 (sem subagentes)

---

## Resultado empírico (Fase 1 executada)

**Causa-raiz isolada:** `lsof -ti:"$NYX_OLLAMA_PORT"` em `run.sh:327` (original) trava INDEFINIDAMENTE neste sistema.

**Prova empírica direta** (5 rodadas, 2 portas distintas, mesmo padrão):

```
$ for i in 1 2 3 4 5; do time timeout 2 lsof -ti:11435 2>&1 >/dev/null; echo "rc=$?"; done
2.54s rc=124    # rc=124 == timeout estourado
2.05s rc=124
2.82s rc=124
3.19s rc=124
3.66s rc=124

$ time timeout 3 lsof -ti:8000 2>&1 >/dev/null   # outra porta
rc=124 em 3.66s   # trava igual — não é específico de 11435
```

**Confirmação via traces empíricos no run.sh:**

```
###BOOT_TRACE_1###
21:13:00 [nyx] [trace] before update_next_sprint.py
21:13:00 [nyx] [trace] after update_next_sprint.py (info_len=23)
21:13:00 [nyx] nenhuma sprint PENDENTE
21:13:00 [nyx] [trace] before kill_existing_ollama
21:13:00 [nyx] [trace] kill_existing_ollama entry
21:13:00 [nyx] [trace] kill_existing_ollama after pkill proxy
^^^ ÚLTIMA LINHA — `[trace] after lsof` NÃO aparece (trava no lsof)
```

**Hipótese B do spec CONFIRMADA**, as outras (A, C, D, E) refutadas (não estão no caminho do hang).

## Fix aplicado (Fase 2)

Substituído `lsof -ti:` por helper `_port_owner_pid()` baseado em `ss -Hltnp` + awk. `ss` (iproute2) responde em <30ms; permanece fallback `timeout 2 lsof -nP` para sistemas sem ss.

**Touches finais em `run.sh`:**

- `+_port_owner_pid()` helper (linhas 322-340, 22 linhas)
- `existing_pid=$(_port_owner_pid "$NYX_OLLAMA_PORT")` (substitui `lsof -ti:...`)
- `< /dev/null` em `update_next_sprint.py` call (defensivo contra herança de stdin)
- 3 fixes de acentuação periférica em comentários (pré-existentes da SPRINT 237, varredura check #4)

## Validação (Fase 3 — 3 boots reais consecutivos)

```
Boot 2: 14.41s  →  Ollama 1s, Proxy 2s, Warmup 9s, "Iniciando Nyx CLI"
Boot 3: 14.51s  →  idem
Boot 4: 14.45s  →  idem
```

Antes do fix: travava indefinidamente entre "nenhuma sprint PENDENTE" e "Limpando cache" (lsof pendurado). Após fix: progride sequencialmente com VRAM final livre 3706 MiB / 64 used.

**Smoke (`--smoke` faz exec curto antes do bug):** 3 rodadas, 0.15s cada, "boot ok".
**Invariantes:** PASS=14/14, FAIL=0.

---

## Contexto

Usuário reportou em 2026-05-25 ~21:05: **"fora isso. a nyx nao inicia. Pode verificar se ela limpa o ollama, da um kill em outras instancias nao sei, mas ele nao inicia de fato."**

Evidência em `logs/boot.log`:
```
20:58:18 [nyx] Modelo aquecido (warmup duplo, 9s)
20:58:18 [nyx] Iniciando Nyx CLI...
21:02:15 [nyx] Lock stale (PID 668234 morto), sobrescrevendo
21:02:15 [nyx] nenhuma sprint PENDENTE
21:04:39 [nyx] Lock stale (PID 691035 morto), sobrescrevendo
21:04:39 [nyx] nenhuma sprint PENDENTE
```

Boots às 21:02:15 e 21:04:39 chegam em `update_next_sprint.py` (que emite "nenhuma sprint PENDENTE" via `log_boot`) e DEPOIS NADA — não há `Limpando cache...` nem `Iniciando Ollama...`.

A função `kill_existing_ollama` é chamada logo após (linha 589). Sua primeira ação visivel é `log_boot "Limpando cache..."` mas não aparece no log → função NÃO está sendo executada OU está travando ANTES da primeira linha.

## Possíveis causas-raiz (Fase 1 deve isolar)

### Hipótese A — pkill bloqueante em pipe quebrado
`kill_existing_ollama` linha 1: `pkill -f "nyx/proxy.py" 2>/dev/null || true`. Em sistemas com pipe stdout fechado (após nossa redireção de stdout no start_boot_spinner), `pkill` pode travar em SIGPIPE handling. Não é provável mas testável.

### Hipótese B — `lsof` travando
Linha 320: `existing_pid=$(lsof -ti:"$NYX_OLLAMA_PORT" 2>/dev/null || true)`. `lsof` pode demorar se houver FDs abertos em estados estranhos.

### Hipótese C — `start_boot_spinner` interfere
Spinner em background imprimindo `\b<char>` a cada 0.5s pode interferir em chamadas síncronas se houver competição por TTY. Mas o stdout do background ainda é o original, e o foreground tem fd 1 já redefinido.

### Hipótese D — Locks anteriores não morrem
`acquire_lock` linha 270: loop `for i in 1 2 3 4 5; do kill -0 ... ; sleep 1; done` espera até 5s. Se PID anterior tem child que não morre, fica em zombie state. Mas `acquire_lock` continua após 5s sempre.

### Hipótese E — `update_next_sprint.py` deixa stdin/stdout em estado estranho
O script Python que emite "nenhuma sprint PENDENTE" pode estar deixando FDs em estado que confunde shell subsequente.

## Solução proposta

**Fase 1 — Reprodução + isolamento:**

1. Adicionar `log_boot` BEFORE/AFTER cada chamada crítica entre `update_next_sprint.py` e `start_ollama`:
   ```bash
   log_boot "[trace] entering kill_existing_ollama"
   kill_existing_ollama
   log_boot "[trace] exiting kill_existing_ollama"
   log_boot "[trace] entering start_ollama"
   start_ollama
   log_boot "[trace] exiting start_ollama"
   ```

2. Rodar `./run.sh --smoke` 3 vezes. Inspecionar boot.log entre tentativas.

3. Identificar qual linha NÃO aparece no log → essa é onde trava.

**Fase 2 — Fix cirurgico baseado na causa:**

- Se `pkill` trava → adicionar timeout via `timeout 2 pkill ...`
- Se `lsof` trava → cache em arquivo + fallback alternativo
- Se acquire_lock loop fica travado → reduzir para `for i in 1 2`
- Se update_next_sprint.py vaza FDs → `< /dev/null` na chamada

**Fase 3 — Validação:**

```bash
# Cleanup completo
pkill -9 -f "ollama serve|nyx/proxy" 2>/dev/null
rm -f /tmp/nyx.pid

# 3 smoke boots seguidos, cada um exit 0 em <5s
for i in 1 2 3; do
    time ./run.sh --smoke || echo "FALHOU"
done
```

## Riscos

| Risco | Mitigação |
|---|---|
| Hipótese errada — fix não resolve | Fase 1 isola causa empíricamente, sem chutar |
| Adicionar log_boot vaza demais em logs/boot.log | Linhas [trace] são temporárias; remover após Fase 2 |
| Timeout agressivo mata processo legítimo | Usar 2s como ceiling — suficiente para casos normais |

## Aritmética esperada

~10 linhas líquidas (traces + timeout cirurgico em 1-2 sites).

## Proof-of-work

```bash
./run.sh --smoke           # boot ok exit 0
time ./run.sh --smoke      # esperado <5s
time ./run.sh --smoke      # idem
time ./run.sh --smoke      # idem
bash scripts/sprint_invariants.sh   # PASS=14/14
grep -E "\[trace\]" logs/boot.log | tail -10   # mostra cada fase
```

---

*"Bug que se isola sozinho não existe. Prova literal antes de fix." -- princípio anti-chute*
