## 0. SPEC (machine-readable)

```yaml
sprint:
  id: README-REQUISITOS-HONESTOS-01
  numero: 435
  title: "README honesto para leigo sem hardware: GPU opcional, RAM/download/internet explícitos, primeiro comando executável"
  onda: 48
  prioridade: ALTA
  tipo: Docs
  dependencias: []
  desbloqueia: []
  absorve: []

  touches:
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/README.md
      reason: "reescrever a seção Requisitos (GPU opcional + RAM + download por fase + internet-uma-vez), adicionar bloco 'Não tenho GPU', corrigir o badge de CI (linha 1) e o git clone placeholder (linha 13)"
      linhas_alvo: "1 (badge CI com [REDACTED]), 13 (git clone <este-repo>), 358-363 (seção Requisitos)"
  creates: []
  removes: []

  forbidden:
    - "Adicionar emoji"
    - "Mencao a IA proprietaria"
    - "Tocar QUALQUER arquivo alem de README.md"
    - "Tocar código-fonte (nyx/**, scripts/**, install.sh, run.sh) -- a infra JÁ suporta CPU-only; esta sprint só corrige a documentação para refletir a realidade"
    - "Alterar os contadores auto-gerados do README (slash count / gauntlet test count / commands count) -- são derivados por scripts/update_docs.py no gauntlet, não editar à mão"
    - "Prometer no README número de RAM/latência que o código NÃO garante -- ancorar apenas no que é verificável (ex.: o ulimit -v 8GB já aplicado em run.sh) e marcar estimativas como estimativa"
    - "Remover a frase '100% offline' -- ela é verdadeira em runtime; a correção é adicionar a ressalva 'instalação baixa uma vez', não negar o offline"

  tests:
    - cmd: "python3 /home/andrefarias/.config/zsh/scripts/validar-acentuacao.py --paths README.md"
      deve_passar: true
    - cmd: "bash scripts/sprint_invariants.sh"
      deve_passar: true
    - cmd: "./run.sh --smoke"
      deve_passar: true

  acceptance_criteria:
    - "AC1 (GPU opcional): a seção Requisitos (README.md:358-363) deixa de listar 'GPU NVIDIA (RTX 3050 4GB recomendado)' como requisito absoluto e passa a marcá-la OPCIONAL, deixando explícito que sem GPU o Nyx roda em CPU automaticamente (fallback já implementado em scripts/detect_gpu.py: 'se ausente -> num_gpu=0, fallback CPU'). Existe um bloco curto 'Não tenho GPU' com a expectativa de que respostas ficam mais lentas em CPU."
    - "AC2 (RAM/download/internet explícitos): os Requisitos passam a informar RAM mínima ancorada no ulimit -v 8GB já aplicado por run.sh (README.md:49), a composição do download (~5 GB: Ollama + qwen2.5-coder:3b 1.8 GB + moondream 1.6 GB opcional via --no-vision) e a frase 'a instalação baixa ~5 GB uma única vez pela internet; depois roda 100% offline'. A promessa '100% offline' (README.md:5) ganha essa ressalva sem ser removida."
    - "AC3 (primeiro comando executável): README.md:13 deixa de conter o placeholder 'git clone <este-repo> Nyx-Code' e passa a usar a URL real (pyproject.toml:42 -> https://github.com/[REDACTED]/nyx-code). O badge de CI (README.md:1) troca o '[REDACTED]' por '[REDACTED]'. Um leigo copia-e-cola o primeiro comando sem erro de sintaxe do git."
    - "AC4 (sem regressão de escopo): nenhum arquivo alem de README.md tocado; contadores auto-gerados (slash/tools/commands) intactos; acentuação rc=0; invariantes FAIL_AFTER <= FAIL_BEFORE; smoke boot ok."
```

---

# Sprint README-REQUISITOS-HONESTOS-01 — README honesto para quem não tem GPU

**Status:** PENDENTE
**Data criação:** 2026-07-13
**Modelo obrigatório:** claude-opus-4-7 (executor-sprint autorizado pelo dono nesta onda)

---

## Contexto do projeto (snapshot — não referência)

> **Missão (ADR-032/033/034):** o Nyx-Code faz o pior LLM local (qwen 3b) na pior máquina possível parecer um agente de código profissional offline. A robustez pertence à INFRA, não ao modelo. O público-alvo é o leigo sem hardware bom e sem dinheiro para uma A100. A infra já compensa a falta de GPU (fallback CPU automático); o problema desta sprint é que o README esconde isso e afasta exatamente esse público na primeira leitura.
>
> **Estado (2026-07-13):** `qwen2.5-coder:3b`. ONDA-48. Achado da auditoria de prontidão 2026-07-12 (verificado adversarialmente com evidência file:line). Fix 100% documental em `README.md`; zero código.

---

## Problema

A auditoria de prontidão 2026-07-12 encontrou três defeitos no `README.md` que, juntos, sabotam o primeiro contato do público-alvo. São o mesmo mecanismo — **o README descreve o projeto para quem já tem hardware bom, não para o leigo sem GPU** — e por isso vão numa única sprint, cada defeito virando um AC.

**Achado 1 (ALTA) — GPU listada como requisito, não como opcional.** `README.md:358-363` traz a seção Requisitos:

```
## Requisitos

- Linux (x86_64)
- Python 3.10+
- GPU NVIDIA (RTX 3050 4GB recomendado)
- ~8 GB de disco (modelos Ollama)
```

A única menção a CPU-only está enterrada na seção de portabilidade Docker (`README.md:217-218`: "Sem GPU no container, o auto-tune detecta e usa CPU (num_gpu=0)"). O código suporta CPU plenamente: `scripts/detect_gpu.py` (docstring, "Lê VRAM livre via nvidia-smi (se ausente -> num_gpu=0, fallback CPU)"). O leigo sem GPU NVIDIA lê "GPU NVIDIA" na lista de requisitos e desiste antes de clonar — o oposto da razão de existir do projeto (ADR-034, "feito para quem não tem A100"). Reforçam a moldura GPU-cêntrica `README.md:7` ("otimizado para RTX 3050 4GB", em `README.md:8`) e o abre-alas do arquivo.

**Achado 2 (ALTA) — README não comunica RAM mínima, download total (~5 GB) nem que a instalação exige internet.** `grep -niE "RAM|memória" README.md` só retorna `check_oom.sh` (linha 65), o rodapé de VRAM (132), a nota de senha em memória (187) e a linha da ADR-003 (314) — **zero requisito de RAM**. `grep -niE "internet|download|baixar" README.md` retorna **vazio**. O arquivo abre com "Agente de código local. 100% offline." (`README.md:5`) e a instalação só diz "`./install.sh # Ollama, venv, modelos (~8GB)`" (`README.md:97`). O `~8GB` é de **disco**, não de download nem de RAM. Download real medido na auditoria: clone (~134 MB) + Ollama (~1.5 GB) + qwen2.5-coder:3b (1.8 GB) + moondream (1.6 GB, opcional via `--no-vision`) ≈ **~5 GB pela internet**. O leigo com internet lenta ou franquia de dados inicia ~5 GB sem aviso; a máquina de 4 GB de RAM tenta rodar em CPU sem saber se cabe. O "100% offline" sem a ressalva "instalação requer internet uma vez" cria expectativa falsa justamente para quem mais depende dessa informação.

**Achado 3 (MEDIA) — o primeiro comando do percurso não é executável.** `README.md:13` manda `git clone <este-repo> Nyx-Code` (placeholder literal) e `README.md:1` traz `![CI](https://github.com/[REDACTED]/nyx-code/actions/workflows/ci.yml/badge.svg)`. A URL real existe em `pyproject.toml:42` (`Homepage = "https://github.com/[REDACTED]/nyx-code"`). O leigo copia-e-cola o comando e recebe erro de sintaxe do git no passo 1 da jornada (descobrir -> clonar); o badge quebrado passa impressão de projeto abandonado na página inicial do repositório.

**Princípio ferido:** honestidade com o usuário — a infra é robusta o suficiente para o leigo sem GPU, mas o README não conta, e o afasta antes que a infra possa provar seu valor.

---

## Causa-raiz

O README foi escrito a partir da máquina de desenvolvimento (RTX 3050 4GB) e nunca foi revisado pela ótica do público-alvo (leigo, sem GPU, internet possivelmente limitada). Não há bug de código: a infra faz o certo (fallback CPU em `scripts/detect_gpu.py`; `ulimit -v 8GB` em `run.sh`, evidenciado em `README.md:49`). O defeito é puramente de comunicação: o documento de entrada descreve requisitos ideais de desenvolvedor, não o mínimo real do usuário final.

**Verificação adversarial das evidências do briefing (linhas podem deslizar):**

| Evidência do briefing | Linha real conferida | Situação |
|---|---|---|
| Badge `[REDACTED]` em README.md:1 | README.md:1 | confirmado exato |
| "100% offline" em README.md:5 | README.md:5 | confirmado exato |
| `git clone <este-repo>` em README.md:13 | README.md:13 | confirmado exato |
| Seção Requisitos em README.md:358 | README.md:358 (`## Requisitos`) | confirmado exato |
| "GPU NVIDIA (RTX 3050 4GB...)" em README.md:362 | README.md:362 | confirmado exato |
| `install.sh # ...(~8GB)` em README.md:97 | README.md:97 | confirmado exato |
| Docker CPU em README.md:218 | README.md:217-218 | leve deslize (frase abre em 217, cai em 218); conteúdo idêntico |
| detect_gpu.py "fallback CPU" na linha :17 | scripts/detect_gpu.py:19 (docstring) | deslize de +2 linhas; texto idêntico |
| Homepage em pyproject.toml:42 | pyproject.toml:42 | confirmado exato |
| grep RAM/internet | grep executado: RAM só em contextos não-requisito; internet/download/baixar vazio | confirmado |

Divergências: apenas dois deslizes de referência (Docker CPU 218->217-218; detect_gpu.py 17->19), ambos irrelevantes para o fix, que é no README. `--no-vision` confirmada como flag real (`install.sh:35,45`) e já parcialmente documentada em `README.md:16` — o AC2 apenas a conecta à economia de download.

---

## Solução proposta

Edição documental de `README.md`, três blocos, todos no mesmo arquivo:

### Edit 1 — Requisitos honestos (GPU opcional + RAM + download + internet) — README.md:358-363

Substituir a lista atual por uma que separe requisito real de recomendação, ancorando os números no que é verificável (disco medido, `ulimit -v 8GB` de `run.sh`) e marcando latência/RAM-mínima como estimativa. Modelo de conteúdo (o executor ajusta a redação, preservando o estilo do arquivo):

```markdown
## Requisitos

- Linux (x86_64)
- Python 3.10+
- ~8 GB de disco (modelos Ollama)
- RAM: 8 GB recomendado (o `run.sh` já aplica `ulimit -v 8GB` ao processo). Em
  4 GB é possível com swap, só mais lento — estimativa, não garantia.
- Conexão à internet **apenas na instalação**: o `./install.sh` baixa ~5 GB uma
  única vez (Ollama ~1.5 GB, modelo `qwen2.5-coder:3b` 1.8 GB, visão `moondream`
  1.6 GB — pulável com `./install.sh --no-vision`). Depois disso, roda 100%
  offline.

**GPU NVIDIA é OPCIONAL** (RTX 3050 4GB acelera as respostas). Sem GPU, o Nyx
detecta a ausência e roda em CPU automaticamente — ver "Não tenho GPU" abaixo.

### Não tenho GPU

Funciona. O `scripts/detect_gpu.py` detecta a falta de GPU e configura
`num_gpu=0` (CPU puro) sozinho — nenhum passo manual. A diferença é só a
latência: as respostas ficam mais lentas do que com GPU, mas o agente é o
mesmo. É exatamente o cenário para o qual o Nyx foi feito.
```

Ajustar/atenuar a moldura GPU-cêntrica do topo se o executor julgar necessário (`README.md:8` "otimizado para RTX 3050 4GB" pode virar "otimizado para rodar bem até em RTX 3050 4GB — e em CPU sem GPU"), mas isso é secundário; o núcleo do AC1/AC2 está na seção Requisitos.

### Edit 2 — primeiro comando executável — README.md:13

`git clone <este-repo> Nyx-Code` -> `git clone https://github.com/[REDACTED]/nyx-code Nyx-Code` (URL de `pyproject.toml:42`).

### Edit 3 — badge de CI — README.md:1

`https://github.com/[REDACTED]/nyx-code/...` -> `https://github.com/[REDACTED]/nyx-code/...`.

---

## Arquivos alvo (paths absolutos)

- `/home/andrefarias/Desenvolvimento/Nyx-Code/README.md` — único arquivo tocado.

Nenhum código. Nenhum outro arquivo. A integração em `SPRINT_ORDER_MASTER.md` / `GAMBIARRAS_POR_SPRINT.md` / `EXECUTAR_SPRINT.md` é do orquestrador, não desta sprint.

---

## Diff esperado (resumo)

```
~ 1 arquivo modificado (README.md)
+ ~20 linhas líquidas (nova subseção "Não tenho GPU" + Requisitos expandidos)
~ 3 linhas alteradas (badge linha 1, git clone linha 13, item GPU dos Requisitos)
```

Sem aritmética de extração: não há meta `arquivo < NNNL`. Fix documental aditivo.

---

## Comandos de verificação (literais, copy-paste)

```bash
cd /home/andrefarias/Desenvolvimento/Nyx-Code

# 1. Reconferir as âncoras ANTES de editar (linhas podem ter deslizado):
sed -n '1p;5p;13p' README.md
sed -n '358,363p' README.md
grep -n "Homepage" pyproject.toml

# 2. Acentuação (obrigatória, gate pre-commit):
python3 ~/.config/zsh/scripts/validar-acentuacao.py --paths README.md

# 3. Confirmar que os defeitos sumiram:
! grep -q "<este-repo>" README.md && echo "OK: placeholder git clone removido"
! grep -q "\[REDACTED\]" README.md && echo "OK: badge corrigido"
grep -q "[REDACTED]/nyx-code" README.md && echo "OK: URL real presente"
grep -qi "opcional" README.md && grep -qi "sem GPU" README.md && echo "OK: GPU marcada opcional"
grep -qi "Não tenho GPU" README.md && echo "OK: bloco CPU-only presente"
grep -qiE "internet|download|~5 GB|5 GB" README.md && echo "OK: download/internet documentado"

# 4. Contadores auto-gerados intactos (não devem ter mudado nesta edição manual):
grep -n "tools," README.md | head -1   # linha 7: "35 tools, 67 commands, 16 services"

# 5. Invariantes (baseline):
bash scripts/sprint_invariants.sh > /tmp/inv_before.txt 2>&1
FAIL_BEFORE=$(grep -c "^\[FAIL\]" /tmp/inv_before.txt)
# ... editar ...
bash scripts/sprint_invariants.sh > /tmp/inv_after.txt 2>&1
FAIL_AFTER=$(grep -c "^\[FAIL\]" /tmp/inv_after.txt)
diff /tmp/inv_before.txt /tmp/inv_after.txt

# 6. Smoke boot (check #13 obrigatório antes de CONCLUIDA; edição de docs não
#    deve quebrar o boot -- prova que nada mais foi tocado):
./run.sh --smoke   # deve imprimir "boot ok" e exit 0
```

---

## Proof-of-work esperado

Colar no relato de conclusão:

1. `git --no-pager diff --stat` — deve mostrar **apenas** `README.md`.
2. `git --no-pager diff README.md` — os três Edits (badge, git clone, Requisitos + "Não tenho GPU").
3. Output do passo 3 dos comandos de verificação (todos os `OK:`).
4. `python3 ~/.config/zsh/scripts/validar-acentuacao.py --paths README.md` — rc=0.
5. `inv_before`/`inv_after` (tail) + `diff` — `FAIL_AFTER <= FAIL_BEFORE`.
6. `./run.sh --smoke` — `boot ok`, exit 0 (check #13, contrato de runtime do VALIDATOR_BRIEF).

**DEFERIDO para GPU exclusiva** (não bloqueia esta sprint documental, seguindo o padrão das specs 403/407): `./run.sh --gauntlet --only rapido` e `--only proxy` exigem GPU exclusiva. Como esta sprint **não toca código**, o gauntlet não pode regredir por ela; rodar apenas quando `pgrep -af "Luna.*driver|valida_sprint"` estiver vazio, como sanidade final antes do corte de release, não como gate desta sprint.

---

## Critério binário de aceite (IA executora)

- [ ] AC1: seção Requisitos marca GPU como OPCIONAL e existe bloco "Não tenho GPU" citando o fallback CPU automático.
- [ ] AC2: Requisitos informam RAM (ancorada no `ulimit -v 8GB`), download ~5 GB por fase (com `--no-vision`) e a ressalva "internet só na instalação; depois offline".
- [ ] AC3: `README.md:13` usa `https://github.com/[REDACTED]/nyx-code`; badge (`README.md:1`) sem `[REDACTED]`.
- [ ] AC4: só `README.md` tocado; contadores auto-gerados intactos; acentuação rc=0; `FAIL_AFTER <= FAIL_BEFORE`; `./run.sh --smoke` = `boot ok`.
- [ ] Proof-of-work (6 itens) colado.
- [ ] NÃO commitar; NÃO tocar `Checkpoint.md`; NÃO tocar `SPRINT_ORDER_MASTER.md` (integração é do orquestrador).

---

## Guardrails anti-engodo (obrigatórios)

NÃO marcar concluída se:

- A frase "100% offline" foi **removida** em vez de ganhar a ressalva "instalação baixa uma vez" (o offline em runtime é verdadeiro; negá-lo é outro engodo).
- Algum número de RAM/latência foi apresentado como garantia sem estar ancorado no código (só o `ulimit -v 8GB` é fato; RAM mínima e latência CPU são estimativa e devem ser rotuladas como tal).
- Qualquer arquivo alem de `README.md` foi tocado.
- Os contadores auto-gerados (`35 tools, 67 commands, 16 services`, contagem de testes do gauntlet) foram editados à mão — são derivados por `scripts/update_docs.py`.
- O `git clone` continua com `<este-repo>` ou o badge continua com `[REDACTED]`.

Se algo falhar: `[SPRINT 435] BLOQUEADA: <motivo 1 linha>`.

---

## Fora de escopo (anti-débito)

| Item | Decisão |
|---|---|
| Hardening do `scripts/detect_gpu.py` (a infra CPU-only já funciona; nada a corrigir no código) | **NÃO-OBJETIVO.** Esta sprint é 100% documental. |
| Medir e publicar latência real do 3b em CPU (benchmark) | **Fora de escopo.** Exige rodada controlada em máquina sem GPU. Se o dono quiser número medido no README, registrar sprint `DOCS-CPU-LATENCY-BENCH-01` (anti-débito, `feedback_nenhum_debito`), não fabricar aqui. |
| Revisão editorial geral do README (tom, estrutura, seções além de Requisitos/topo/badge) | **Fora de escopo.** Mudança cirúrgica: só os três achados. Reescrita ampla seria sprint própria. |
| Corrigir o mesmo placeholder/badge em outros docs (CONTRIBUTING, docs/) se existirem | **Fora de escopo** desta sprint (touches restritos a `README.md`); se a auditoria achar recorrência, sprint `DOCS-URL-PLACEHOLDERS-SWEEP-01`. |

---

## Referências

- BRIEF: `/home/andrefarias/Desenvolvimento/Nyx-Code/VALIDATOR_BRIEF.md`
- Origem: auditoria de prontidão 2026-07-12, relatório durável `dev-journey/07-reports/AUDIT_2026_07_12.md` §3 (briefing efêmero da sessão de auditoria)
- Evidência primária: `README.md:1,5,13,358-363,97,217-218`; `scripts/detect_gpu.py:19`; `pyproject.toml:42`; `install.sh:35,45`
- Missão: ADR-034 ("feito para quem não tem A100"), ADR-032/033 (a infra carrega o modelo)

---

*"O README é o primeiro contato do leigo sem hardware. Se ele lê 'GPU NVIDIA obrigatória', desiste antes de a infra provar que não precisa. Honestidade aqui não é enfeite: é a diferença entre o público-alvo ficar ou ir embora."*
