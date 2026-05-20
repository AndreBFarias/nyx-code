# SPRINT K08-VRAM-RUNNER-ISOLATION-01 — Pre-flight de VRAM externa antes da fase K (performance)

## 0. SPEC (machine-readable)

```yaml
sprint:
  id: K08-VRAM-RUNNER-ISOLATION-01
  title: "Gauntlet detecta VRAM ocupada por processo externo antes da fase K (performance); SKIP por padrão, --strict-vram preserva FAIL, --isolate-vram mata com confirmação"
  onda: 25
  bloco: 25.1 Resiliência do gauntlet
  prioridade: ALTA
  tipo: Bugfix de runner / Anti-flaky
  dependencias: [VALIDATE-FINAL-01-PARTE-2]
  desbloqueia: [v1.0 release-gate verde sem qualificação manual]

  touches:
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/scripts/gauntlet/nyx_gauntlet.py
      reason: "Pre-flight check antes de _phase_performance + propagar SKIP no relatório; novos flags --strict-vram e --isolate-vram no argparse; remarcar K-08 (linha 801) como SKIP quando pre-flight detecta contaminação"
      linhas_alvo: "22-33 (imports), 759-817 (_phase_performance), 4032-4041 (_get_vram), 4354-4360 (argparse)"

  creates:
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/scripts/gauntlet/vram_check.py
      reason: "Módulo isolado importável; CLI standalone que retorna JSON com free_mib e lista de processos; reusa parsing do lifecycle.vram_check() mas adiciona enumeração via nvidia-smi --query-compute-apps"

  removes: []

  n_to_n_pairs:
    - descricao: "Threshold de VRAM mínima (1500 MiB default) aparece em vram_check.py e nyx_gauntlet.py — única fonte em vram_check.py exportada como VRAM_MIN_FREE_MIB"
      paths:
        - /home/andrefarias/Desenvolvimento/Nyx-Code/scripts/gauntlet/vram_check.py

  forbidden:
    - "Matar processo sem flag --isolate-vram explícita"
    - "Matar processo do próprio Nyx (proxy.py, ollama serve) -- detector deve filtrar por nome/PID conhecidos"
    - "Mudar comportamento default (atual: K-08 só lê memory.used e falha se >3500); novo default precisa ser SKIP com motivo, não FAIL silencioso"
    - "Pular pre-flight quando nvidia-smi indisponível (degradar para SKIP-graceful, não para FAIL)"
    - "Adicionar emoji"
    - "Menção a Claude/GPT/Anthropic em código Python"
    - "Acentuação errada em PT-BR"
    - "pkill -f sem confirmação stdin em --isolate-vram"
    - "Reordenar imports existentes em nyx_gauntlet.py (mudança cirúrgica)"

  tests:
    - cmd: "./venv/bin/python scripts/gauntlet/vram_check.py"
      timeout: 10
      deve_passar: true
      nota: "Saída JSON válido com keys free_mib (int), processes (list de objetos {pid, name, mib}), nvidia_smi_ok (bool)"
    - cmd: "NYX_FAKE_VRAM_FREE=500 ./venv/bin/python scripts/gauntlet/vram_check.py"
      timeout: 10
      deve_passar: "free_mib==500"
      nota: "Modo de teste sem GPU real para CI"
    - cmd: "./run.sh --smoke"
      timeout: 60
      deve_passar: "boot ok"
    - cmd: "bash scripts/sprint_invariants.sh"
      timeout: 60
      deve_passar: "FAIL_AFTER <= FAIL_BEFORE (14/14 PASS)"
    - cmd: "NYX_FAKE_VRAM_FREE=500 ./run.sh --gauntlet --only K-08"
      timeout: 300
      deve_passar: "SKIP com motivo declarado contendo 'VRAM externa'"
      nota: "K-08 sai como SKIP, não FAIL; relatório gauntlet contém razão"
    - cmd: "NYX_FAKE_VRAM_FREE=500 ./run.sh --gauntlet --only K-08 --strict-vram"
      timeout: 300
      deve_passar: "FAIL como antes"
      nota: "Preserva contrato anterior quando explicitamente solicitado"
    - cmd: "./run.sh --gauntlet --only K-08 --isolate-vram < /dev/null"
      timeout: 60
      deve_passar: "exit != 0 com mensagem 'isolate-vram requer TTY' OU sem efeito se VRAM livre suficiente"
      nota: "Em headless, --isolate-vram falha graciosamente sem matar nada"

  acceptance_criteria:
    - "scripts/gauntlet/vram_check.py existe, importável como módulo (from scripts.gauntlet.vram_check import probe, VRAM_MIN_FREE_MIB)"
    - "vram_check.py CLI standalone imprime JSON parseável com free_mib + processes + nvidia_smi_ok"
    - "vram_check.py honra NYX_FAKE_VRAM_FREE para CI sem GPU"
    - "vram_check.py enumera processos via 'nvidia-smi --query-compute-apps=pid,process_name,used_memory --format=csv,noheader,nounits'"
    - "nyx_gauntlet.py: novo pre-flight em _phase_performance antes da chamada self._get_vram() em linha 802"
    - "Pre-flight chama vram_check.probe(); se free < VRAM_MIN_FREE_MIB e há processo externo identificado, comportamento depende do flag"
    - "Flag default (sem --strict-vram e sem --isolate-vram): K-08 marcado como SKIP via novo método self._add_skip(); detalhe contém 'VRAM externa: X MiB livres, processo PID NAME ocupando Y MiB'"
    - "Flag --strict-vram: comportamento idêntico ao atual (FAIL se vram_mib > 3500)"
    - "Flag --isolate-vram: lista processos externos em stdout e pede confirmação 'kill PID NAME? [y/N]' via input(); se TTY ausente (não-interativo) erra com exit 2 e mensagem clara; nunca mata sem confirmação"
    - "Lista de PIDs/nomes do próprio Nyx (proxy.py, ollama serve, nyx/cli.py) filtrada antes de oferecer kill"
    - "Argparse ganha --strict-vram (store_true) e --isolate-vram (store_true); mutuamente exclusivos via add_mutually_exclusive_group"
    - "self._add_skip(id, title, phase, details) adiciona resultado com status SKIP que não conta como FAIL no gate"
    - "Cenário simulado NYX_FAKE_VRAM_FREE=500 sem flags resulta em SKIP no log final; com --strict-vram resulta em FAIL"
    - "Acentuação PT-BR correta em toda mensagem nova"
    - "Smoke + 14 invariantes 100% verdes após mudanças"
    - "Zero regressão: gauntlet --only performance em ambiente limpo (VRAM livre suficiente) executa como antes"
```

---

**Status:** CONCLUIDA (2026-05-19)
**Data criação:** 2026-05-19 (anti-débito de VALIDATE-FINAL-01-PARTE-2)
**Origem:** Frente 6 do gauntlet completo (commit 8101062) — K-08 falhou com 3750 MiB usada porque processo externo `chatterbox` (TTS daemon Neurosonancy, PID 956798) ocupava 3678 MiB da RTX 3050. Não é regressão Nyx; é contaminação de ambiente compartilhado.
**Modelo obrigatório:** claude-opus-4-7 (sem subagentes; planejamento explícito antes de codar; integração obrigatória)

---

## Contexto

### Achado original

Durante `./run.sh --gauntlet` completo em 2026-05-19, a fase `performance` reportou:

```
| K-08 | VRAM em uso | performance | FAIL | 0.0s | 0 | 3750MiB (baseline <2500, crítico >3500) |
```

Investigação manual (registrada em `dev-journey/07-reports/RELATORIO_VALIDATE_FINAL_01.md:234`) confirmou:

- Processo PID 956798 `python3 ... chatterbox-tts ...` (projeto vizinho Neurosonancy) ocupava 3678 MiB.
- Após `kill -9 956798`, VRAM caiu para ~80 MiB livres antes de subir o modelo Nyx novamente.
- K-08 voltaria a 64 MiB se rodado depois do cleanup, mas o gate já havia sido REPROVADO formalmente.

VALIDATE-FINAL-01-PARTE-2 anotou: *"K08-VRAM-RUNNER-ISOLATION-01: gauntlet checa VRAM disponível antes de rodar tests sensíveis."*

### Por que K-08, não BOOT-VRAM-GUARD?

BOOT-VRAM-GUARD-01 (concluída 2026-05-17, commit 436d1e7) cuida do **boot do Nyx**: ajusta `num_gpu` antes da pré-carga e suprime "Morto" do bash. O escopo dela é o ciclo de vida do próprio Ollama do Nyx.

Esta sprint cuida do **runner do gauntlet**: antes de avaliar KPI de performance (K-08), precisa saber se a VRAM baseline já está envenenada por terceiros. Independente de o Nyx ter subido com sucesso, a métrica K-08 reflete o estado global da GPU, não só o consumo do Nyx.

### Arquitetura atual relevante (snapshot, não referência)

- `scripts/gauntlet/nyx_gauntlet.py` (4370L) — runner principal; método `_phase_performance` em linha 759; `_get_vram()` em linha 4032 lê `memory.used` via `nvidia-smi`.
- `nyx/agent/services/lifecycle.py:113` — `vram_check()` já implementa leitura de `memory.free` com fallback gracioso (retorna `(True, -1)` se `nvidia-smi` indisponível). **Reusar a lógica de parsing, mas não importar diretamente** (lifecycle é runtime do agente, scripts/gauntlet é tooling — manter desacoplado).
- `run.sh:637` invoca o gauntlet passando `--only "$GAUNTLET_ONLY"`. Novos flags precisam ser forwarded via run.sh.
- `--only` (linha 246+ do gauntlet) já aceita feature_id direto (ex.: `K-08`).

### ADRs aplicáveis

- ADR-003 VRAM Management (RTX 3050 4 GB; limite empírico de 12 layers).
- ADR-004 Zero Emojis.
- ADR-005 Anonimato.
- ADR-006 PT-BR acentuação.
- ADR-007 Gauntlet (mecanismo único de teste; sem mocks; resultados binários).

---

## Problema

1. **K-08 falha sem culpa do Nyx.** O critério `vram_used < 3500 MiB` é absoluto e não distingue consumo Nyx de consumo externo. Quando há contaminação de ambiente, o gauntlet acusa regressão inexistente.
2. **O gate ficou REPROVADO por motivo qualificado.** Frente 6 da VALIDATE-FINAL-01-PARTE-2 documentou 13 falhas todas qualificadas (sandbox /tmp + VRAM externa). O release v1.0 NÃO foi cortado, parcialmente, por essa ambiguidade.
3. **Sem mecanismo para isolar ou aceitar contaminação.** Operador humano precisa parar, identificar o processo, decidir matar ou suspender, e re-rodar manualmente. Anti-flow.
4. **`_get_vram()` mede `memory.used` global** (linha 4035), não filtra. Mesmo se o Nyx usa só 200 MiB, a métrica reporta o total do sistema.

---

## Solução

### Parte 1 — Novo módulo `scripts/gauntlet/vram_check.py`

Módulo isolado e importável. Não depende de imports do `nyx/` (manter scripts/ autônomos).

```python
#!/usr/bin/env python3
"""Detector de VRAM livre + enumeração de processos GPU.

Uso programático:
    from scripts.gauntlet.vram_check import probe, VRAM_MIN_FREE_MIB
    snap = probe()
    # snap = {"free_mib": 423, "processes": [{"pid": 956798, "name": "...", "mib": 3678}], "nvidia_smi_ok": True}

Uso CLI:
    python3 scripts/gauntlet/vram_check.py        # imprime JSON
    NYX_FAKE_VRAM_FREE=500 python3 scripts/gauntlet/vram_check.py  # modo CI

Limite VRAM_MIN_FREE_MIB = 1500 (RTX 3050 4 GB; abaixo disso, modelo Nyx
não cabe na pré-carga + overhead Ollama).
"""

from __future__ import annotations
import json
import os
import subprocess
import sys
from typing import Any

VRAM_MIN_FREE_MIB: int = 1500

# Filtrar processos do próprio Nyx: nunca propor matar esses.
NYX_PROCESS_HINTS: tuple[str, ...] = (
    "nyx/proxy.py",
    "nyx/cli.py",
    "ollama serve",
    "ollama runner",
)


def _query_free_mib() -> int:
    """Retorna VRAM livre em MiB. -1 se nvidia-smi indisponível."""
    fake = os.environ.get("NYX_FAKE_VRAM_FREE")
    if fake is not None:
        try:
            return int(fake)
        except ValueError:
            return -1
    try:
        out = subprocess.check_output(
            ["nvidia-smi", "--query-gpu=memory.free",
             "--format=csv,noheader,nounits"],
            text=True, timeout=3,
        ).strip()
        return int(out.splitlines()[0])
    except (FileNotFoundError, subprocess.TimeoutExpired,
            subprocess.CalledProcessError, ValueError, OSError):
        return -1


def _query_processes() -> list[dict[str, Any]]:
    """Lista (pid, name, mib) ocupando VRAM. Vazia se nvidia-smi indisponível."""
    if os.environ.get("NYX_FAKE_VRAM_FREE") is not None:
        # Modo CI: simula 1 processo externo de 3000 MiB se fake free < threshold
        free = int(os.environ.get("NYX_FAKE_VRAM_FREE", "9999"))
        if free < VRAM_MIN_FREE_MIB:
            return [{"pid": 999999, "name": "fake-ext-process", "mib": 3000}]
        return []
    try:
        out = subprocess.check_output(
            ["nvidia-smi", "--query-compute-apps=pid,process_name,used_memory",
             "--format=csv,noheader,nounits"],
            text=True, timeout=3,
        ).strip()
    except (FileNotFoundError, subprocess.TimeoutExpired,
            subprocess.CalledProcessError, OSError):
        return []
    procs: list[dict[str, Any]] = []
    for line in out.splitlines():
        parts = [p.strip() for p in line.split(",")]
        if len(parts) < 3:
            continue
        try:
            pid = int(parts[0])
            mib = int(parts[2])
        except ValueError:
            continue
        procs.append({"pid": pid, "name": parts[1], "mib": mib})
    return procs


def is_nyx_owned(proc: dict[str, Any]) -> bool:
    """True se o processo pertence ao próprio Nyx (não candidato a kill)."""
    name = proc.get("name", "") or ""
    return any(hint in name for hint in NYX_PROCESS_HINTS)


def probe() -> dict[str, Any]:
    """Snapshot completo: VRAM livre + processos."""
    free = _query_free_mib()
    procs = _query_processes()
    return {
        "free_mib": free,
        "processes": procs,
        "nvidia_smi_ok": free >= 0,
    }


def main() -> int:
    snap = probe()
    print(json.dumps(snap, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

### Parte 2 — Pre-flight em `nyx_gauntlet.py::_phase_performance`

Antes da chamada `vram_mib = self._get_vram()` na linha 802, inserir bloco:

```python
# K08-VRAM-RUNNER-ISOLATION-01: pre-flight de contaminação externa.
from scripts.gauntlet.vram_check import probe as _vram_probe, VRAM_MIN_FREE_MIB, is_nyx_owned
snap = _vram_probe()
external_procs = [p for p in snap["processes"] if not is_nyx_owned(p)]
external_mib = sum(p["mib"] for p in external_procs)
contaminated = (
    snap["nvidia_smi_ok"]
    and snap["free_mib"] >= 0
    and snap["free_mib"] < VRAM_MIN_FREE_MIB
    and external_procs
)

if contaminated and not self._strict_vram and not self._isolate_vram:
    # Default: SKIP com razão declarada.
    proc_desc = ", ".join(
        f"PID {p['pid']} {p['name']} ocupando {p['mib']} MiB"
        for p in external_procs[:3]
    )
    self._add_skip(
        "K-08", "VRAM em uso", "performance",
        details=(
            f"SKIP -- VRAM externa: {snap['free_mib']} MiB livres, "
            f"processo {proc_desc}"
        ),
    )
    return  # pula resto da fase performance? NÃO: outras KPIs (K-01/03/04/10) seguem.
```

Em vez de `return`, o correto é **só pular o bloco K-08** e seguir K-10. Refatorar como:

```python
if contaminated and not self._strict_vram and not self._isolate_vram:
    # ... self._add_skip(...)
    skip_k08 = True
else:
    skip_k08 = False

if skip_k08:
    pass  # K-08 já marcado SKIP acima
else:
    vram_mib = self._get_vram()
    self._kpis["vram_mib"] = vram_mib
    if vram_mib > 0:
        self._add("K-08", "VRAM em uso", "performance",
                  vram_mib < 3500, 0,
                  details=f"{vram_mib}MiB (baseline <2500, crítico >3500)")
    else:
        self._add("K-08", "VRAM em uso", "performance", True, 0,
                  details="nvidia-smi indisponível (OK sem GPU)")
```

### Parte 3 — Flag `--isolate-vram` (modo interativo)

```python
if contaminated and self._isolate_vram:
    if not sys.stdin.isatty():
        logger.error("--isolate-vram requer TTY interativo (stdin)")
        sys.exit(2)
    print("Processos externos ocupando VRAM:")
    for p in external_procs:
        print(f"  PID {p['pid']:>7}  {p['name']:<40}  {p['mib']:>5} MiB")
    for p in external_procs:
        ans = input(f"kill PID {p['pid']} {p['name']}? [y/N] ").strip().lower()
        if ans == "y":
            try:
                os.kill(p["pid"], signal.SIGTERM)
                time.sleep(1.5)
                if _proc_alive(p["pid"]):
                    os.kill(p["pid"], signal.SIGKILL)
            except (ProcessLookupError, PermissionError) as exc:
                logger.warning("kill PID %d falhou: %s", p["pid"], exc)
    # Re-probe após kills
    snap = _vram_probe()
    # Se ainda contaminado, segue para SKIP-default
```

### Parte 4 — Flag `--strict-vram` (preserva contrato antigo)

Mantém o comportamento atual: `_get_vram()` global, FAIL se > 3500. Sem pre-flight.

### Parte 5 — Argparse + run.sh forward

`nyx_gauntlet.py::main()` (linha 4354):

```python
parser = argparse.ArgumentParser(description="Nyx-Code Gauntlet")
parser.add_argument("--proxy-url", default="http://127.0.0.1:11436")
parser.add_argument("--ollama-url", default="http://127.0.0.1:11435")
parser.add_argument("--only", default="completo")
parser.add_argument("--model", default="qwen3:4b")
mutex_vram = parser.add_mutually_exclusive_group()
mutex_vram.add_argument("--strict-vram", action="store_true",
                        help="K-08 FAIL real se VRAM excedida (default: SKIP em contaminação)")
mutex_vram.add_argument("--isolate-vram", action="store_true",
                        help="Lista processos externos e pede confirmação para kill (TTY obrigatório)")
args = parser.parse_args()

g = NyxGauntlet(
    proxy_url=args.proxy_url, ollama_url=args.ollama_url,
    only=args.only, model=args.model,
    strict_vram=args.strict_vram, isolate_vram=args.isolate_vram,
)
```

`run.sh` (linha 637+): adicionar parse de novos flags e forward para o python do gauntlet. Manter compat 100% (sem flag, sem mudança).

### Parte 6 — Novo método `_add_skip`

```python
def _add_skip(self, id_: str, title: str, phase: str, details: str = "") -> None:
    """Marca resultado como SKIP. Não conta como FAIL no gate."""
    r = GauntletResult(
        id=id_, title=title, phase=phase, status="SKIP",
        elapsed=0.0, tokens=0, details=details,
    )
    self._results.append(r)
    logger.info("[SKIP] %s: %s", id_, details)
```

Cuidado: o dataclass `GauntletResult` atualmente provavelmente assume `status in {"OK","FAIL"}`. Conferir definição e ajustar gate de PASS/FAIL/SKIP no relatório (status SKIP não soma nem em sucesso nem em falha; aparece em coluna separada).

---

## Plano de implementação (passos numerados)

1. **Read-only**: confirmar dataclass `GauntletResult` e gate logic (`_compute_summary` ou equivalente em `nyx_gauntlet.py`).
2. **Criar** `scripts/gauntlet/vram_check.py` com `probe()`, `is_nyx_owned()`, CLI standalone, suporte `NYX_FAKE_VRAM_FREE`.
3. **Testar isoladamente**: `python3 scripts/gauntlet/vram_check.py` retorna JSON; `NYX_FAKE_VRAM_FREE=500` retorna 500.
4. **Modificar** `_phase_performance` em `nyx_gauntlet.py` (linha 759): adicionar pre-flight conforme Parte 2.
5. **Adicionar** método `_add_skip` na classe `NyxGauntlet`.
6. **Adicionar** flags `--strict-vram` e `--isolate-vram` em `main()` (linha 4354).
7. **Adicionar** atributos `self._strict_vram` e `self._isolate_vram` no `__init__` da classe.
8. **Ajustar** gate (status SKIP não conta como FAIL).
9. **Modificar** `run.sh` linha 110+ (parsing de args do `--gauntlet`) para forward dos novos flags.
10. **Validação completa** (ver seção Verificação).

---

## Aritmética

Esta sprint **não tem meta de redução de linhas**. Estima-se delta:

- `nyx_gauntlet.py`: 4370L atuais → ~4430L pós (+60L: pre-flight K-08 + `_add_skip` + argparse).
- `vram_check.py`: 0L → ~120L (novo arquivo).
- `run.sh`: 664L atuais → ~672L pós (+8L: parsing dos 2 flags).

Total: +188L de código real (módulo + pre-flight + flags). Aceitável: é feature anti-flaky de runner, não refactor.

---

## Verificação end-to-end

```bash
# 1. FAIL_BEFORE
bash scripts/sprint_invariants.sh > /tmp/inv_before.txt 2>&1
echo "FAIL_BEFORE=$(grep -c '^\[FAIL\]' /tmp/inv_before.txt)"
# Esperado: 0 (14/14 PASS)

# 2. Reproduzir o cenário (sem fix): rodar gauntlet --only K-08
./run.sh --gauntlet --only K-08
# Esperado pré-fix: FAIL "VRAM em uso" se ambiente contaminado

# 3. Implementar (parte 1 -> parte 2 -> parte 3 -> parte 4 -> parte 5 -> parte 6)

# 4. Teste do módulo isolado
./venv/bin/python scripts/gauntlet/vram_check.py | jq .
# Esperado: JSON {"free_mib": N, "processes": [...], "nvidia_smi_ok": true}

NYX_FAKE_VRAM_FREE=500 ./venv/bin/python scripts/gauntlet/vram_check.py
# Esperado: {"free_mib": 500, "processes": [{"pid":999999,...}], ...}

# 5. Cenário SKIP default (simulado)
NYX_FAKE_VRAM_FREE=500 ./run.sh --gauntlet --only K-08
# Esperado: K-08 SKIP com "VRAM externa: 500 MiB livres, PID 999999 fake-ext-process..."

# 6. Cenário --strict-vram preserva contrato antigo
NYX_FAKE_VRAM_FREE=500 ./run.sh --gauntlet --only K-08 --strict-vram
# Esperado: FAIL (porque _get_vram global ainda mede memory.used)

# 7. Cenário --isolate-vram headless erra graciosamente
./run.sh --gauntlet --only K-08 --isolate-vram < /dev/null
# Esperado: exit 2, mensagem "isolate-vram requer TTY"

# 8. Cenário limpo (sem contaminação)
./run.sh --gauntlet --only performance
# Esperado: K-08 OK normal (zero regressão)

# 9. FAIL_AFTER
bash scripts/sprint_invariants.sh > /tmp/inv_after.txt 2>&1
echo "FAIL_AFTER=$(grep -c '^\[FAIL\]' /tmp/inv_after.txt)"
diff /tmp/inv_before.txt /tmp/inv_after.txt
# Esperado: FAIL_AFTER == FAIL_BEFORE (0/14)

# 10. Smoke
./run.sh --smoke
# Esperado: boot ok
```

---

## Tabela: comportamento por flag

| Flag                | Pre-flight detecta contaminação | Ação                                                     | K-08 final | Gate                     |
| ------------------- | ------------------------------- | -------------------------------------------------------- | ---------- | ------------------------ |
| (default)           | sim                             | Marca SKIP com motivo + lista processos externos no log  | SKIP       | Não conta como FAIL      |
| (default)           | não                             | Mede `memory.used`; FAIL se > 3500                       | OK ou FAIL | Conta normalmente        |
| `--strict-vram`     | (ignorado)                      | Comportamento idêntico ao atual: mede e avalia 3500      | OK ou FAIL | Conta normalmente        |
| `--isolate-vram`    | sim + TTY                       | Lista processos; pede `[y/N]` por PID; mata confirmados; re-mede | OK/FAIL/SKIP | Conta após cleanup     |
| `--isolate-vram`    | sim + headless                  | Exit 2 + mensagem clara                                  | (não chega) | Aborta gauntlet com erro |
| `--isolate-vram`    | não                             | No-op; segue fluxo normal                                | OK ou FAIL | Conta normalmente        |

---

## Invariantes a preservar

- **BRIEF [CORE] check #1**: smoke obrigatório antes de marcar CONCLUIDA.
- **BRIEF [CORE] check #2**: zero emojis em código, commits, docs.
- **BRIEF [CORE] check #3**: sem menção a IA externa em `.py`.
- **BRIEF [CORE] check #4**: acentuação correta PT-BR (validar via `~/.config/zsh/scripts/validar-acentuacao.py`).
- **BRIEF [CORE] check #5**: cleanup após teste com modelo. Esta sprint não roda modelo (K-08 é só métrica), mas deixar VRAM livre como antes.
- **GUIDE §3 mudanças cirúrgicas**: não refatorar `_get_vram`, não reordenar imports, não "limpar" código adjacente.
- **GUIDE §2 simplicidade**: sem abstração de fábrica de detectores; um módulo, uma função `probe()`.
- **ADR-007 Gauntlet**: SKIP é status novo; documentar no relatório como coluna separada (não confundir com FAIL nem com PASS).
- **Memória `nenhum_debito_fica_para_tras`**: se durante implementação aparecer outro problema (ex.: `_get_vram` deveria usar `memory.free`), registrar como sprint nova, não absorver.
- **Memória `integracao_obrigatoria`**: nada solto; vram_check.py é importado pelo nyx_gauntlet.py e exportado via CLI; sem código dormente.

---

## Proof-of-work esperado

- Diff final (3 arquivos: novo `vram_check.py`, modificações em `nyx_gauntlet.py` e `run.sh`).
- Runtime real:
  - `./run.sh --smoke` → `boot ok`
  - `bash scripts/sprint_invariants.sh` → 14/14 PASS
  - `./venv/bin/python scripts/gauntlet/vram_check.py` → JSON válido
  - `NYX_FAKE_VRAM_FREE=500 ./venv/bin/python scripts/gauntlet/vram_check.py` → `free_mib==500`
  - `NYX_FAKE_VRAM_FREE=500 ./run.sh --gauntlet --only K-08` → SKIP no log final
  - `NYX_FAKE_VRAM_FREE=500 ./run.sh --gauntlet --only K-08 --strict-vram` → FAIL
  - `./run.sh --gauntlet --only K-08 --isolate-vram < /dev/null` → exit 2
- Hipótese verificada via `rg`:
  - `rg "K-08" scripts/gauntlet/nyx_gauntlet.py` mostra os 3 sites originais (linha 806, 814) + os novos do pre-flight
  - `rg "from scripts.gauntlet.vram_check" scripts/gauntlet/nyx_gauntlet.py` mostra o import
  - `rg "_add_skip" scripts/gauntlet/nyx_gauntlet.py` mostra definição + invocação
- Acentuação periférica: validador roda nos 3 arquivos tocados sem violações.
- Checkpoint.md atualizado antes e depois (write-through).
- SPRINT_ORDER_MASTER.md atualizado de PENDENTE → CONCLUIDA com data e commit.

---

## Riscos e não-objetivos

### Não-objetivos (fora do escopo)

- Não modificar `_get_vram()` para usar `memory.free` (mudança semântica do KPI K-08; registrar sprint nova `K08-METRIC-REWORK-01` se justificar).
- Não criar novas categorias de KPI (K-08 continua sendo "VRAM em uso", não vira "VRAM disponível ao Nyx").
- Não tocar BOOT-VRAM-GUARD-01 (cobre runtime do Nyx, não runner).
- Não adicionar UI no Cockpit para gerenciar VRAM externa (ficar no runner; UI vira sprint separada `COCKPIT-VRAM-OBSERVABILITY-01` se houver demanda).
- Não auto-kill mesmo com `--isolate-vram` (sempre requer confirmação explícita por PID).

### Riscos

1. **`GauntletResult.status` pode ser string livre ou enum.** Se for enum restrito a OK/FAIL, ajustar para aceitar SKIP. Verificar antes de codar.
2. **Gate de exit code** (`asyncio.run(g.run())` retorna 0/1) pode depender de `len(fails) == 0`. Garantir que SKIP não vire FAIL implicitamente.
3. **Relatório markdown** gerado em `dev-journey/07-reports/gauntlet/` pode quebrar parser de tabela se nova coluna SKIP for adicionada. Manter coluna existente, só preencher status como `SKIP` em vez de `OK`/`FAIL`.
4. **`os.kill` em PID alheio**: pode falhar com `PermissionError` se processo pertence a outro UID. Tratar e reportar; não abortar.
5. **`signal` import**: pode não estar importado no topo de `nyx_gauntlet.py`. Adicionar `import signal` junto com `import os` existente.

### Decisões em aberto (resolver durante implementação)

- Threshold `VRAM_MIN_FREE_MIB = 1500` é o mesmo do `BOOT-VRAM-GUARD-01` (low-VRAM mode). Decisão: manter 1500 como default, exportar como constante editável. Documentar em ADR se virar configurável.
- Em `--isolate-vram` com múltiplos processos externos: ordenar por MiB decrescente para pedir kill do maior primeiro.

---

## Referências

- BRIEF: `/home/andrefarias/Desenvolvimento/Nyx-Code/VALIDATOR_BRIEF.md`
- Sprint origem: `dev-journey/06-sprints/concluidos/SPRINT_VALIDATE_FINAL_01_PARTE_2.md` (frente 6, linhas 70 e 77)
- Relatório do achado: `dev-journey/07-reports/RELATORIO_VALIDATE_FINAL_01.md` (linha 234 e 262)
- Log do gauntlet com a falha: `dev-journey/07-reports/gauntlet/GAUNTLET_2026-05-19_0352.md` (linhas 126 e 370)
- Sprint correlata: `dev-journey/06-sprints/concluidos/SPRINT_BOOT_VRAM_GUARD_01.md` (runtime do Nyx, não runner)
- ADR-003: `dev-journey/03-decisions/ADR_003_VRAM_MANAGEMENT.md`
- ADR-007: `dev-journey/03-decisions/ADR_007_GAUNTLET.md`
- Código atual K-08: `scripts/gauntlet/nyx_gauntlet.py` linhas 759-817 (`_phase_performance`) e 4032-4041 (`_get_vram`)
- Reusar lógica de parsing: `nyx/agent/services/lifecycle.py` linhas 113-141 (`vram_check`)
- Commit raiz: `8101062` (feat VALIDATE-FINAL-01-PARTE-2: release gate v1.0 pronto)
- MASTER entry: `dev-journey/06-sprints/SPRINT_ORDER_MASTER.md` linha 316 (sprint 58b — registro anti-débito)

---

*"Um KPI que pune o time pelo ruído da vizinhança não é métrica — é teatro. Detectar a contaminação é tão importante quanto medir o sinal."*
