# SPRINT ONDA-38-E — VISION-RUNTIME-REVALIDATE-01

## 0. SPEC (machine-readable)

```yaml
sprint:
  id: VISION-RUNTIME-REVALIDATE-01
  title: "Verificação de runtime do moondream/visão (describe end-to-end + delta VRAM 0) -- não reimplementa"
  onda: 38
  prioridade: MEDIA
  tipo: Verificação
  touches: []
  acceptance_criteria:
    - "phase vision do gauntlet passa (V-VS-01 e V-VS-02 verdes)"
    - "describe end-to-end real de 1 imagem retorna transcrição não-vazia"
    - "verify_vram.sh reporta delta 0 MB (chat model não é descarregado pela visão)"
    - "se o port pós-Textual quebrou algo, achado registrado e corrigido cirurgicamente"
    - "smoke boot ok"
```

---

**Status:** CONCLUIDA_COM_RESSALVA (2026-06-01 — PORT VERIFICADO OK: gauntlet --only vision 3/3 (V-VS-01 importa/instancia PASS; V-VS-02 is_available() PASS com available=False; V-VS-03 describe+cache PASS via skip "moondream não instalado"). Árvore intacta (VisionService/VisionClient/describe/is_available presentes). baseline_2026-06-01.json: total 3 passed 3 failed 0. Smoke boot ok. Cleanup: VRAM 64/4096 MiB livre, zero processos órfãos. RESSALVA: moondream NÃO está instalado nesta máquina (available=False), então describe-real (AC#2) e verify_vram delta-0 (AC#3) não puderam rodar — pendem de `ollama pull moondream` (~1.7GB, CPU puro ADR-022). NÃO é regressão de port; é ausência do modelo (possível --no-vision intencional). Próximo: decisão do usuário sobre puxar o modelo p/ fechar o describe-real.)
**Data criação:** 2026-06-01
**Modelo obrigatório:** sem subagentes (Read/Grep/Glob direto)

---

## Contexto

A stack de visão foi CONCLUÍDA nas sprints VISION-01/02/03: `VisionService` (`nyx/agent/services/vision_service.py`), `VisionClient` (`nyx/providers/vision_client.py`), os entrypoints `/vision` + Ctrl+V (`nyx/cli_helpers.py`), cache sha256 em `~/.nyx/vision_cache/`. moondream roda em CPU puro (ADR-022). Papel: "opus multimodal" — lê a imagem e transcreve para o model de chat. Esta sprint é VERIFICAÇÃO de runtime, não reimplementação: confirma describe end-to-end e delta VRAM 0. Se o port pós-Textual quebrou algo, corrige cirurgicamente; senão, é verde de verificação.

## Escopo (touches autorizados)

- Arquivos a modificar: NENHUM por padrão (sprint de verificação). Touches `[]`.
- EXCEÇÃO cirúrgica: SE a verificação revelar regressão real do port pós-Textual, autorizar correção mínima APENAS no arquivo culpado (provável candidato: `nyx/agent/services/vision_service.py`, `nyx/providers/vision_client.py` ou `nyx/cli_helpers.py`). Toda correção vira nota no proof + atualização deste spec; se a correção for ampla, ABRIR sprint nova (anti-débito) em vez de inflar esta.
- Arquivos NÃO a tocar: nenhum dos 6 protegidos (a stack de visão não os inclui).

## Observação sobre a hipótese original (ajuste do planejador — IMPORTANTE)

Verificado via leitura de `scripts/gauntlet/nyx_gauntlet.py`:

- `--only vision` é suportado (L115: `"vision": ["vision"]`) e a `_phase_vision` (L1739+) adiciona DOIS checks: `V-VS-01` ("VisionService importa e instancia") e `V-VS-02` ("is_available() sem crash"). NÃO há um terceiro check de visão na phase.
- Portanto o critério correto é a phase vision passar com 2/2 (V-VS-01 + V-VS-02), NÃO "3/3" como na hipótese do coordenador. O "3" da hipótese provavelmente confundiu a phase vision com os checks `V-05/V-06/V-07` (que existem no gauntlet mas pertencem a outra fase, não à phase `vision`). O describe end-to-end real é uma prova SEPARADA do gauntlet (feita à mão), assim como o `verify_vram.sh`.

O critério desta sprint usa os números reais: phase vision 2/2 + describe manual + verify_vram.sh delta 0.

## Acceptance criteria

1. `./run.sh --gauntlet --only vision` passa com V-VS-01 e V-VS-02 verdes (2/2 na phase vision).
2. Describe end-to-end real: rodar `VisionService.describe(<imagem>)` sobre 1 imagem de teste e obter transcrição NÃO-vazia.
3. `bash scripts/verify_vram.sh` reporta delta 0 MB entre antes e depois do describe (o model de chat não é descarregado da VRAM). Em ambiente sem GPU, o script pula gracefully (exit 0) — registrar o skip como verde condicional.
4. Se houver regressão de port: achado documentado, correção cirúrgica aplicada (ou sprint nova aberta), re-verificação verde.
5. `./run.sh --smoke` imprime `boot ok`, exit 0.

## Invariantes a preservar

- ADR-022: moondream em CPU puro; a visão NÃO deve competir por VRAM com o chat model (daí o delta 0 do verify_vram.sh).
- Cache sha256 em `~/.nyx/vision_cache/`: a 1ª chamada popula, a 2ª serve do cache; o delta VRAM 0 é medido na 1ª chamada (BRIEF/coordenador).
- Cleanup obrigatório pós-teste com modelo (BRIEF check #5): `pkill -f "nyx/proxy.py"`, `pkill -f "ollama serve"`, `nvidia-smi` confirmando VRAM livre.
- GUIDE.md §4: critério de sucesso é "verde de verificação"; só virar código se um teste FALHAR.

## Plano de implementação

1. Confirmar a árvore de visão intacta: `rg -n "class VisionService|class VisionClient|def describe|def is_available" nyx/agent/services/vision_service.py nyx/providers/vision_client.py`.
2. Rodar `./run.sh --gauntlet --only vision` e capturar V-VS-01/V-VS-02.
3. Escolher/criar 1 imagem de teste (procurar fixture existente via `rg -l --glob '*.png' --glob '*.jpg' .` em diretórios de teste/fixtures; se houver fixture de visão, usá-la). Rodar `describe` end-to-end e capturar a transcrição.
4. Rodar `bash scripts/verify_vram.sh` e capturar BEFORE/AFTER/delta.
5. Se tudo verde: fechar como verificação. Se algo falhar: diagnosticar o port, aplicar correção mínima OU abrir sprint nova, re-verificar.
6. Cleanup VRAM + smoke.

## Testes

- Sem teste unitário novo (verificação reusa o gauntlet existente). Se a correção cirúrgica for necessária, adicionar teste de regressão pontual no arquivo de testes de visão (`rg -l vision tests/`).
- Baseline gauntlet vision: PASS esperado = 2/2.

## Proof-of-work esperado

- Runtime real:
  - Gauntlet: `./run.sh --gauntlet --only vision` (V-VS-01 + V-VS-02 verdes; colar o sumário)
  - Describe real: comando que invoca `VisionService.describe(<imagem>)` + a transcrição não-vazia retornada
  - VRAM: `bash scripts/verify_vram.sh` (BEFORE/AFTER/delta = 0 MB, ou `[skip]` em ambiente sem GPU)
  - Smoke: `./run.sh --smoke` (`boot ok`, exit 0)
- Cleanup: `pkill -f "nyx/proxy.py"`, `pkill -f "ollama serve"`, `nvidia-smi` (VRAM livre).
- Diff: vazio se for verde puro; ou diff mínimo da correção cirúrgica + nota de achado.
- Hipótese verificada: `rg -n "\"vision\": \[\"vision\"\]|_phase_vision|V-VS-01|V-VS-02" scripts/gauntlet/nyx_gauntlet.py`.

## Riscos e não-objetivos

- Não-objetivo: reimplementar a stack de visão, mudar moondream para GPU, ou adicionar features de visão. Só verificar.
- Risco: ambiente sem GPU faz `verify_vram.sh` pular (exit 0 com `[skip]`). Isso é aceitável — registrar como skip, não como falha.
- Risco: flakiness de VRAM no RTX 3050 4GB (BRIEF). Rodar com VRAM previamente livre; aceitar 1 execução limpa.

## Referências

- BRIEF: `/home/andrefarias/Desenvolvimento/Nyx-Code/VALIDATOR_BRIEF.md` (check #5 cleanup; cap VRAM RTX 3050)
- Precedente: VISION-01/VISION-02/VISION-03 (CONCLUIDAS); ADR-022 (moondream CPU)
- Ferramenta: `/home/andrefarias/Desenvolvimento/Nyx-Code/scripts/verify_vram.sh`

---

*"Verificar é confiar com prova na mão."*
