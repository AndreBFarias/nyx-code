# SPRINT 288: TUI-FOOTER-VRAM-REALTIME-01 (ONDA-34, decisão #6)

## Contexto

O footer/toolbar da NyxTUI (`nyx/agent/tui/widgets/toolbar.py`) não mostra
VRAM em tempo real. A deteccao de GPU so ocorre no boot (via
`scripts/detect_gpu.py` -> `NYX_NUM_GPU`, lido pelo banner em
`nyx/agent/banner.py:241`). A decisão #6 da auditoria
(`~/.claude/plans/redesign-auditoria-da-tender-beacon.md`) pede um campo VRAM
ao vivo no footer, atualizado por polling leve de `nvidia-smi` a cada ~2s, com
degradacao graciosa quando não ha GPU (campo oculto, sem quebrar o render).

Restricao crítica do ambiente: a maquina alvo tem GPU de 4GB. O polling NÃO
pode bloquear o event loop do Textual nem competir por VRAM. Os helpers de GPU
ja existentes no codebase (`nyx/agent/services/lifecycle.py::vram_check`,
`nyx/agent/commands/system.py`, `scripts/gauntlet/fixtures/model_compare.py::vram_used_mib`)
sao todos SINCRONOS (`subprocess.run`) e portanto inadequados dentro do loop
do Textual. A sprint reutiliza o PADRAO async ja consagrado em
`nyx/proxy.py:859 (_detect_num_gpu_async)` -- `asyncio.create_subprocess_exec`
+ `asyncio.wait_for` + `proc.kill()` em timeout -- e NÃO o codigo sincrono.

## Escopo (touches autorizados)

- Arquivos a modificar:
  - `nyx/agent/tui/widgets/toolbar.py` -- novo reactive `vram`, watch handler,
    insercao do campo no `render()`, timer `set_interval` no `on_mount`, e o
    coroutine `_poll_vram` (subprocess async + parsing + set do reactive).
- Arquivos a criar:
  - Nenhum. O helper async vive em `toolbar.py` (escopo único, ~25L). NAO criar
    modulo novo nem helper "reutilizavel" especulativo (GUIDE.md seção 2).
- Arquivos NÃO a tocar:
  - `nyx/themes/design_tokens.py` -- as cores `NYX_ACCENT` e `NYX_MUTED` ja
    estao importadas no `toolbar.py`. Zero token novo, zero hex (invariante #6).
  - `nyx/agent/tui/app.py` -- o timer fica NO Toolbar (precedente
    `banner.py:106`), não na App. So tocar app.py se a exploracao do executor
    revelar bloqueio real; nesse caso, registrar como achado, não expandir
    escopo silenciosamente.
  - `nyx/agent/services/lifecycle.py`, `nyx/agent/commands/system.py`,
    `scripts/detect_gpu.py`, `scripts/gauntlet/*` -- helpers sincronos de GPU
    permanecem intactos; não sao chamados por esta sprint.

## Acceptance criteria

1. Com GPU presente, o footer exibe um campo VRAM com numero real coerente com
   `nvidia-smi --query-gpu=memory.used,memory.total` (ex.: `VRAM 1234/4096 MiB`
   ou `VRAM 30%`), atualizado a cada ~2s sem intervencao do usuario.
2. Sem GPU (ou `nvidia-smi` ausente do PATH), o campo VRAM e OMITIDO do render
   -- o footer permanece identico ao atual (Ctx/Iter/Lidos/Modif/glyph/modo) e
   não ha exceção no log.
3. O polling e NÃO-BLOQUEANTE: usa `asyncio.create_subprocess_exec` com
   `asyncio.wait_for` (timeout curto, ~3s) e `proc.kill()` no timeout. Nao
   existe `subprocess.run` nem chamada sincrona no caminho do timer.
4. O reactive dispara `self.refresh()` LOCAL ao widget (precedente
   BannerWidget / sprint 193) -- nada de `app.invalidate()` global.
5. Zero hex hardcoded: a cor do campo VRAM usa `NYX_ACCENT` (valor) e
   `NYX_MUTED` (rotulo/separador), ja importados.
6. Invariantes `bash scripts/sprint_invariants.sh` = 14/14 PASS, FAIL 0
   (atenção especial #3 zero-print e #6 zero-hex).
7. Smoke `./run.sh --smoke` imprime `boot ok` e exit 0.

## Invariantes a preservar

- Invariante #6 (BRIEF): zero hex de cor fora de `design_tokens*.py` /
  `constants.py`. O campo VRAM deve consumir tokens importados; não introduzir
  literal `#RRGGBB`.
- Invariante #3 (BRIEF / ADR-024): zero `print()` fora de `nyx/cli*.py` e
  `nyx/agent/output.py`. Diagnostico de falha do polling, se houver, via
  `logger.debug` (importar `logging` se necessario, padrao do codebase).
- Loop-affinity ONDA-33 (`app.py:209-217`, `TUI-FIX-HTTPX-LOOP-AFFINITY-01`):
  o subprocess do `nvidia-smi` deve correr NO event loop do Textual via
  `asyncio.create_subprocess_exec` (que ja agenda no loop corrente). NAO criar
  loop novo nem thread descartavel; não usar `asyncio.run`.
- Refresh por-widget (sprint 187 BLINK_SOFT revertida pela 193, citada em
  `banner.py:108-114` e no docstring do Toolbar): `self.refresh()`, nunca
  invalidação global -- evita race com streaming de output.
- Degradacao graciosa identica aos helpers existentes
  (`lifecycle.py:118` retorna `(True, -1)` quando `nvidia-smi` ausente): a
  ausencia de GPU e estado normal, não erro. O reactive fica `""` e o render
  omite o campo.
- GUIDE.md seção 2 (Simplicidade) e seção 3 (Cirurgico): nenhum helper
  generico/reutilizavel especulativo; toque so o `toolbar.py`.
- STATE_GLYPHS canonicos (`design_tokens.py:100`) intactos -- o novo campo não
  reusa nem altera os glifos de estado do modelo.

## Plano de implementacao

1. Em `toolbar.py`, importar `asyncio` e `logging` (topo do arquivo; manter
   `from __future__ import annotations`). Criar `logger = logging.getLogger(__name__)`.
2. Declarar o novo reactive logo apos `inflight`:
   `vram: reactive[str] = reactive("")` (string ja formatada para render;
   vazia = sem GPU/sem dado).
3. Adicionar `watch_vram(self, old: str, new: str) -> None: self.refresh()`
   junto aos demais watch handlers.
4. Implementar `on_mount(self) -> None`: registrar
   `self.set_interval(2.0, self._poll_vram)` (precedente exato
   `banner.py:106`). Disparar tambem uma chamada inicial para não esperar 2s no
   primeiro frame (opcional: `self.call_after_refresh(self._poll_vram)` ou
   deixar so o interval -- decisão do executor, ambas validas).
   IMPORTANTE: o Toolbar não tem `on_mount` hoje; criar do zero, sem `super()`
   call obrigatorio (Static não exige).
5. Implementar `async def _poll_vram(self) -> None`:
   - `proc = await asyncio.create_subprocess_exec("nvidia-smi",
     "--query-gpu=memory.used,memory.total", "--format=csv,noheader,nounits",
     stdout=PIPE, stderr=PIPE)` (argv-list, sem shell -- imune a injection,
     mesmo padrao proxy.py:870).
   - `stdout, _ = await asyncio.wait_for(proc.communicate(), timeout=3.0)`;
     em `FileNotFoundError` (nvidia-smi ausente) ou `asyncio.TimeoutError`
     (com `proc.kill()` + `await proc.wait()`), setar `self.vram = ""` e
     retornar (degradacao graciosa, sem raise; logger.debug opcional).
   - Parsear a primeira linha: `used, total = raw.split(",")`, converter para
     int. Em `ValueError`/linha vazia, `self.vram = ""` e retornar.
   - Formatar (escolher 1 formato e fixar; recomendado `VRAM {used}/{total} MiB`
     por paridade com `system.py:129`, que ja usa `({used}/{total} MiB)`).
     Setar `self.vram = "VRAM ..."`.
6. No `render()`, inserir o campo APOS o bloco de `Modif`/glyph e ANTES do
   `inflight`/modo (manter a extrema direita do modo intacta, mesma logica do
   `inflight`): se `self.vram`, append separador `"  |  "` em `NYX_MUTED` +
   `self.vram` em `NYX_ACCENT`. Se `self.vram == ""`, não append nada (campo
   omitido).
7. Atualizar o docstring da classe e o do `render()` para listar o novo
   reactive `vram` e o comportamento de omissao.

## Aritmetica

Esta sprint NÃO tem meta de reducao de linhas; e adicao de funcionalidade.
Saldo esperado por componente em `toolbar.py` (atual 140L):

- Imports `asyncio`, `logging` + `logger`: ~3L.
- Reactive `vram`: ~1L.
- `watch_vram`: ~2L.
- `on_mount` + `set_interval`: ~3L.
- `_poll_vram` (subprocess async + parsing + degradacao): ~22-28L.
- Insercao no `render()` (bloco condicional): ~3L.
- Atualizacao de docstrings: ~4L.

Projetado: 140L -> ~175-185L. Sem meta-cap declarado para `toolbar.py`; se o
BRIEF/executor identificar um teto, reavaliar. Saldo positivo justificado:
feature nova, sem extracao planejada.

## Testes

- Nao ha teste unitario direto de widget Textual no padrao do projeto (a
  validação e via Gauntlet + smoke + runtime-real --web). NAO inventar suite
  pytest nova (ADR-014 removeu config pytest do pyproject; sprint 259).
- Cobertura efetiva:
  - Smoke (`./run.sh --smoke`) garante que o boot da TUI não quebra com o novo
    `on_mount`/timer.
  - Gauntlet `--only rapido` + loop confirma ausencia de regressao estrutural.
  - Runtime-real `--web` confirma o campo VRAM com numero real (criterio de
    aceite 1) e a omissao sem GPU se testavel.
- Baseline de invariantes: FAIL_BEFORE = 0, esperado FAIL_AFTER = 0 (14/14).
- Se houver baseline de gauntlet rapido (ex.: 19/19 nas sprints 283-287),
  manter FAIL_AFTER <= FAIL_BEFORE.

## Proof-of-work esperado

- Diff final (so `nyx/agent/tui/widgets/toolbar.py`).
- Runtime real (contratos do BRIEF seção [CORE]):
  - Smoke: `./run.sh --smoke` -- imprime `boot ok`, exit 0.
  - Invariantes: `bash scripts/sprint_invariants.sh` -- 14/14 PASS, FAIL 0.
    Atenção reforcada: check #3 (zero-print) e check #6 (zero-hex) -- o campo
    novo NÃO pode introduzir `print(` nem `#RRGGBB`.
  - Gauntlet: `./run.sh --gauntlet --only rapido` -- 100% (APROVADO) + loop.
    Disciplina OOM (GPU 4GB): SO o subset rapido/por-fase, sem paralelismo,
    cleanup por PID. NAO rodar a suite completa concorrente.
- Validação visual (UI -- toca render layer `toolbar.py`):
  - `./run.sh --web` sobe o cockpit em `127.0.0.1:11437` (ADR-001 loopback).
  - Via playwright (`mcp__plugin_playwright_playwright__*`) ou Chrome real via
    CDP/X11 (`DISPLAY=:1`, fallback). Confirmar por dump do buffer
    (`browser_evaluate` em `term.buffer.active`) OU screenshot que o footer
    mostra `VRAM <numero> MiB` (ou `%`) coerente com a saida real de
    `nvidia-smi --query-gpu=memory.used,memory.total --format=csv,noheader,nounits`.
  - Se testavel sem GPU (ou simulando PATH sem nvidia-smi): confirmar que o
    campo SOME e o footer fica identico ao atual.
  - PNG do frame + sha256 do artefato.
- Acentuacao periferica: varredura `validar-acentuacao.py` em todos os arquivos
  modificados (so `toolbar.py`) -- rc 0.
- Hipotese verificada (licao 4): `rg` confirma que os identificadores citados
  existem antes de iniciar -- `set_interval` (`banner.py:106`),
  `asyncio.create_subprocess_exec` (`proxy.py:870`), reactives existentes do
  Toolbar (`ctx_pct`/`iter_n`/`reads`/`mods`/`model_state`/`mode`/`inflight`),
  tokens `NYX_ACCENT`/`NYX_MUTED` (importados em `toolbar.py`).
- Anti-sanitizer (BRIEF, protocolo do check #14): a sprint NÃO toca
  `design_tokens*.py` nem glifos `chr(0x25xx)`; mesmo assim, rodar o check #14
  integral confirma que nenhum glifo foi corrompido no working tree.

## Riscos e não-objetivos

- Risco: contencao por subprocess. Mitigado por `asyncio.create_subprocess_exec`
  (não bloqueia o loop) + timeout 3s + intervalo 2s (sem sobreposição porque o
  Textual não reentra o callback antes de concluir o anterior em uso normal).
  `nvidia-smi` e leve; não retem VRAM.
- Risco: formato do campo (`MiB` vs `%`). Decisão: fixar `VRAM {used}/{total} MiB`
  por paridade com `system.py:129`. Se o usuario preferir `%`, e ajuste trivial
  de uma linha de format -- NAO virar sub-sprint.
- Nao-objetivo: re-tune de `num_gpu` em runtime (isso e PROXY-NUMGPU-RUNTIME-01,
  ja existente em `proxy.py`). Esta sprint e SO display.
- Nao-objetivo: footer legado `output.py::render_footer` (sem chamador vivo,
  fora de escopo desde a sprint 287) e `banner.py`. NAO tocar.
- Nao-objetivo: status line "NyxCode: processando", thinking-expand, histórico,
  image-counter, banner-rolavel, botao-copiar -- sao IDs 289+ da mesma fila
  ONDA-34 (MASTER linha 814). Se algum aparecer durante execução, registrar como
  sprint nova com ID proprio (protocolo anti-debito, `feedback_nenhum_debito.md`).
- Se o executor descobrir que o timer PRECISA viver na App (e não no Toolbar)
  por algum motivo de lifecycle real, isso e um achado: registrar e confirmar
  com o planejador antes de expandir o escopo para `app.py`.

## Referencias

- BRIEF: `/home/andrefarias/Desenvolvimento/Nyx-Code/VALIDATOR_BRIEF.md`
- Plano canonico: `~/.claude/plans/redesign-auditoria-da-tender-beacon.md`
  (decisão #6).
- MASTER: `dev-journey/06-sprints/SPRINT_ORDER_MASTER.md` bloco
  `MANUAL_OVERRIDE_ONDA_34` (linha 814 lista "VRAM-footer" como PENDENTE
  ID 288+).
- Precedente de timer local: `nyx/agent/tui/widgets/banner.py:98-117`
  (`on_mount` + `set_interval` + `self.refresh()`).
- Precedente de subprocess async de nvidia-smi:
  `nyx/proxy.py:859-891` (`_detect_num_gpu_async`).
- Precedente de degradacao graciosa sem GPU:
  `nyx/agent/services/lifecycle.py:113-141` (`vram_check`, retorna `(True, -1)`).
- Formato de display `({used}/{total} MiB)`: `nyx/agent/commands/system.py:129`.
- Base estavel: commit `302379f` (HEAD origin/main, ONDA-34 287 CONCLUIDA).
