## 0. SPEC (machine-readable)

```yaml
sprint:
  id: OUTPUT-STRIP-ANSI-01
  title: "Higiene de saída: stripar sequências ANSI cruas do summary user-facing (Resultado: da apresentação forte)"
  onda: 48
  prioridade: MEDIA
  tipo: Bugfix
  dependencias: [EXEC-CONTRACT-NO-HALLUCINATED-RESULT-01]
  desbloqueia: []

  touches:
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/agent/loop/_iteration.py
      reason: "Adicionar helper puro strip_ansi_sequences + regex _ANSI_ESCAPE_RE, irmão de strip_system_reminder / strip_done_summary_artifact"
      linhas_alvo: "148 (após strip_done_summary_artifact, antes de _REMINDER_EVERY_DEFAULT)"
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/agent/loop/_core.py
      reason: "Importar o helper (bloco 23-28) e aplicá-lo no guard de saída único (366-367), após os strips já existentes"
      linhas_alvo: "23-28 (import), 364-367 (guard de saída)"
  creates: []
  removes: []

  forbidden:
    - "Adicionar emoji"
    - "Usar 'print()' fora de cli.py/output.py (ADR-024)"
    - "Menção a IA proprietária"
    - "Tocar o output das tools no CONTEXTO do modelo (self._session.history / result.output) -- só o summary user-facing muda"
    - "Adicionar branch específico da TUI para 'preservar cor' -- verificado: a TUI não renderiza ANSI como cor (ver Verificação da TUI)"
    - "Stripar no _compose_presentation_summary em vez do guard de saída -- o guard é o ponto único (LOOP-REMINDER-LEAK-SUMMARY-01)"

  tests:
    - cmd: "./run.sh --smoke"
      timeout: 120
      deve_passar: true
    - cmd: "bash scripts/sprint_invariants.sh"
      timeout: 120
      deve_passar: true
    - cmd: "./run.sh --gauntlet --only rapido"
      timeout: 300
      deve_passar: true

  acceptance_criteria:
    - "strip_ansi_sequences é função pura e determinística: input com ANSI -> sem ANSI; input sem ANSI -> string idêntica"
    - "O guard de saída único em _core.py (364-367) aplica strip_ansi_sequences DEPOIS dos strips de reminder/done/hints"
    - "Um summary que carrega a saída de fastfetch via run_command (Resultado: com [93m...[0m e truecolor \\x1b[38;2;R;G;Bm) chega ao usuário sem nenhuma sequência ANSI"
    - "O output das tools no contexto do modelo (history) NÃO muda -- só status.summary"
    - "Texto user-facing legítimo (sem ANSI) permanece byte-a-byte idêntico após o strip"
    - "Smoke boot ok, invariants 14/14, gauntlet rápido 100%"
```

---

# Sprint OUTPUT-STRIP-ANSI-01 — Higiene: stripar ANSI cru do Resultado: user-facing

**Status:** PENDENTE
**Data criação:** 2026-07-12
**Modelo obrigatório:** claude-opus-4-7 (executor-sprint autorizado pelo dono nesta onda)

---

## Contexto do projeto (snapshot — não referência)

> **ADRs relevantes (inline):**
> - **ADR-024 Render layer:** apresentação é da borda (cli.py/output.py/TUI). Aqui o alvo é o texto que o loop entrega à borda (status.summary), não a borda em si.
> - **ADR-032 / EXEC-CONTRACT (G3 apresentação forte):** para run_command/list_files/read_file/search/glob a resposta SEMPRE anexa a saída crua da tool sob `Resultado:` -- a infra não confia que o 3b apresenta.
> - ADR-005 Anonimato, ADR-006 PT-BR, ADR-014 Testes via Gauntlet.
>
> **Estado (2026-07-12):** o contrato da apresentação forte (sprint 399, `f0883a1`) compõe o `Resultado:` em `nyx/agent/loop/_core.py::_compose_presentation_summary` (L569-606), anexando `result.output` das tools de `PRESENTABLE_TOOLS` (`_constants.py` L67: `run_command, list_files, read_file, search, glob`). Todo summary passa por um GUARD DE SAÍDA ÚNICO em `_core.py` (L364-367) que já aplica `strip_system_reminder` + `strip_done_summary_artifact` + `_DONE_HINT_RE` + `_TOOL_HINT_BRACKET_RE`. Os dois primeiros são funções puras irmãs em `_iteration.py` (L95, L128).

---

## Problema

**Achado da validação as-user da 399 (turno fastfetch, prioridade MEDIA):** ao pedir algo que roda `fastfetch` via `run_command`, a saída real do comando é colorida (sequências ANSI cruas: `\x1b[93m...\x1b[0m`, truecolor `\x1b[38;2;R;G;Bm`). Essa saída é capturada crua por `run_command` e vaza no campo `summary` apresentado sob `Resultado:`.

Cadeia verificada no código:
- `nyx/agent/tools/run_command.py` L64-81: `subprocess.run(..., capture_output=True, text=True)` devolve `result.stdout` cru -- ANSI incluso -- em `ActionResult.output`.
- `nyx/agent/loop/_iteration.py` L519-520: se a tool está em `PRESENTABLE_TOOLS`, `self._turn_presentables.append((name, result.output))` -- guarda o output cru (com ANSI).
- `nyx/agent/loop/_core.py` L587-605 (`_compose_presentation_summary`): junta os blocos em `Resultado:\n{resultado}` sem sanear ANSI.
- `nyx/agent/loop/_core.py` L364-367 (guard de saída): saneia reminder/done/hints, mas NÃO ANSI.

Não é formato interno (como reminder/done) -- é output REAL de terminal colorido. Nas bordas de apresentação o ANSI vira ruído: Rich (`output("nyx", ...)` em `cli.py:465`) escapa os controles e mostra `[93m` literal; o headless (`cli_headless.py:267`) emite o ANSI cru dentro do JSON de `summary`.

---

## Solução proposta

Stripar ANSI no **guard de saída único** (`_core.py` L364-367), o ponto por onde TODO summary passa antes de chegar à borda (TUI e headless), logo depois dos strips já existentes. É o mesmo padrão de defesa-em-profundidade das sprints 381/388/V10.

1. **Novo helper puro** `strip_ansi_sequences(text)` em `_iteration.py`, irmão de `strip_system_reminder` / `strip_done_summary_artifact` (mesma pureza/determinismo, sem ciclo de import: `_iteration` já é importado por `_core`).
2. **Wire** no guard de saída: importar o helper no bloco 23-28 de `_core.py` e chamá-lo após `_TOOL_HINT_BRACKET_RE.sub` (L366), antes do `.strip()` final (L367).

Só `status.summary` (user-facing) muda. O `result.output` no contexto do modelo (`self._session.history`) permanece cru -- o modelo continua vendo o output real, exatamente como o invariante de OUTPUT-LEAK-SANITIZE-01 exige ("os outputs das tools no contexto do modelo NÃO mudam -- só o texto que chega ao usuário").

### Verificação da TUI (requisito do achado: não dessaturar a TUI)

Grep de auditoria confirma que **a TUI NÃO renderiza o summary como cor** -- logo, stripar no loop não remove nenhuma cor que a TUI mostraria:

- `rg "from_ansi" nyx/` retorna **um único hit**: `nyx/agent/tui/widgets/banner.py:97` (`Text.from_ansi` do banner ASCII-art de boot, NÃO do conteúdo do chat).
- O widget de conteúdo `nyx/agent/tui/widgets/chat_message.py` L200-215 renderiza o texto do assistant via `Markdown(self._content)` (settle) ou `Text(self._content)` (streaming), e tool/system via `Text(...)`. Nenhum usa `from_ansi` -- Rich `Text(str)`/`Markdown(str)` tratam sequências ANSI como caracteres literais (lixo), nunca como cor.

Conclusão: a TUI hoje mostraria o ANSI como ruído literal, igual ao headless. Um único strip no guard cobre TUI + headless + CLI plano sem branch específico e sem perda de cor. **Não** adicionar caminho condicional por borda.

---

## Arquivos alvo (paths absolutos)

### `/home/andrefarias/Desenvolvimento/Nyx-Code/nyx/agent/loop/_iteration.py`

#### Edit 1 — novo helper puro (inserir após `strip_done_summary_artifact`, ~L148, antes de `_REMINDER_EVERY_DEFAULT`)

```python
# OUTPUT-STRIP-ANSI-01: sequências ANSI cruas da saída de tools (run_command
# roda comandos coloridos como fastfetch: \x1b[93m...\x1b[0m, truecolor
# \x1b[38;2;R;G;Bm) vazavam no summary user-facing sob "Resultado:" (achado da
# validação as-user da 399). ANSI não é formato interno, é output REAL de
# terminal -- nas bordas de apresentação vira ruído (Rich escapa como '[93m'
# literal; headless emite cru no JSON). Cobre CSI/SGR, OSC (\x1b]...BEL/ST) e
# escapes de 2 chars. Verificado: a TUI não usa from_ansi no conteúdo do chat
# (só o banner), então strip aqui não remove cor que a TUI mostraria.
_ANSI_ESCAPE_RE = re.compile(
    r"\x1b(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~]|\][^\x07\x1b]*(?:\x07|\x1b\\))"
)


def strip_ansi_sequences(text: str) -> str:
    """Remove sequências de escape ANSI de um texto user-facing.

    Defesa em profundidade, irmã de strip_system_reminder /
    strip_done_summary_artifact. Pura e determinística:
    - input com ANSI    -> sequências removidas, texto visível preservado;
    - input sem ANSI    -> retorna a MESMA string (fast-path sem \\x1b);
    - string vazia/None  -> retorna como veio.
    NÃO toca o output das tools no contexto do modelo -- só o summary.
    """
    if not text or "\x1b" not in text:
        return text
    return _ANSI_ESCAPE_RE.sub("", text)
```

> **Nota ao executor:** o `re` já está importado no topo de `_iteration.py` (usado por `_SYSTEM_REMINDER_BLOCK` L89 e `_DONE_SUMMARY_ARTIFACT` L121). Confirme via grep antes de assumir. O fast-path `"\x1b" not in text` garante que texto sem ANSI retorne byte-a-byte idêntico (acceptance #5).

### `/home/andrefarias/Desenvolvimento/Nyx-Code/nyx/agent/loop/_core.py`

#### Edit 2 — adicionar import no bloco existente (L23-28)

**Antes:**
```python
from nyx.agent.loop._iteration import (
    _IterationMixin,
    _reminder_every,
    strip_done_summary_artifact,
    strip_system_reminder,
)
```
**Depois:**
```python
from nyx.agent.loop._iteration import (
    _IterationMixin,
    _reminder_every,
    strip_ansi_sequences,
    strip_done_summary_artifact,
    strip_system_reminder,
)
```

#### Edit 3 — aplicar no guard de saída único (L364-367)

**Antes:**
```python
            _clean = strip_done_summary_artifact(strip_system_reminder(status.summary))
            _clean = _DONE_HINT_RE.sub("", _clean)
            _clean = _TOOL_HINT_BRACKET_RE.sub("", _clean)
            status.summary = _clean.strip()
```
**Depois:**
```python
            _clean = strip_done_summary_artifact(strip_system_reminder(status.summary))
            _clean = _DONE_HINT_RE.sub("", _clean)
            _clean = _TOOL_HINT_BRACKET_RE.sub("", _clean)
            # OUTPUT-STRIP-ANSI-01: remove sequências ANSI cruas (ex.: fastfetch via
            # run_command) do summary user-facing. Só o texto de saída -- o output no
            # contexto do modelo (history) segue cru. É o ponto único por onde todo
            # summary passa antes da borda (TUI + headless).
            _clean = strip_ansi_sequences(_clean)
            status.summary = _clean.strip()
```

> **Nota ao executor:** este é o mesmo guard citado nos comentários L347-363 (LOOP-REMINDER-LEAK-SUMMARY-01 / OUTPUT-DONE-SUMMARY-RENDER-01 / OUTPUT-LEAK-SANITIZE-01). Manter a ordem: ANSI por último, depois do `.strip()`. NÃO mover o strip para `_compose_presentation_summary` -- o guard é o ponto único e cobre também um summary onde o 3b ecoou ANSI no `content` (não só o bloco de presentables).

---

## Diff esperado (resumo)

```
~ 2 arquivos modificados (_iteration.py, _core.py)
+ ~28 linhas líquidas (helper + regex + docstring + import + wire + comentário)
- 0 linhas removidas
```

Sem meta numérica de contagem de linhas (não é sprint de refatoração/split): a aritmética aqui é só o delta do diff acima.

---

## Proof-of-work esperado

Runtime-real. Comandos do VALIDATOR_BRIEF seção [CORE] Contratos de runtime. NÃO rodar nesta sessão (GPU ocupada) -- o executor roda na janela de GPU exclusiva.

```bash
cd /home/andrefarias/Desenvolvimento/Nyx-Code

# 1. Estática + acentuação nos arquivos tocados
python -m ruff check nyx/agent/loop/_iteration.py nyx/agent/loop/_core.py
python3 ~/.config/zsh/scripts/validar-acentuacao.py --paths nyx/agent/loop/_iteration.py nyx/agent/loop/_core.py

# 2. PROOF de pureza do helper (GPU-free, determinístico -- PRIMÁRIA):
venv/bin/python - <<'PY'
from nyx.agent.loop._iteration import strip_ansi_sequences as s
# saída típica de fastfetch: cor 8-bit + truecolor + reset
sujo = "\x1b[93mOS\x1b[0m: \x1b[38;2;137;180;250mPop!_OS 22.04\x1b[0m\nHost: laptop"
limpo = s(sujo)
assert "\x1b" not in limpo, "ainda tem ESC"
assert "[93m" not in limpo and "[0m" not in limpo and "[38;2;" not in limpo, "sobrou SGR"
assert limpo == "OS: Pop!_OS 22.04\nHost: laptop", repr(limpo)
# idempotência + identidade em texto sem ANSI (acceptance #5)
puro = "Resultado:\nOS: Pop!_OS 22.04"
assert s(puro) is puro or s(puro) == puro
assert s(limpo) == limpo
assert s("") == "" and s(None) is None
print("OK strip_ansi_sequences: sujo->limpo, idempotente, identidade preservada")
PY

# 3. PROOF end-to-end do guard (GPU-free): compor um summary com ANSI e confirmar
#    que o ponto de saída o remove. Usa o helper no mesmo ponto do guard.
venv/bin/python - <<'PY'
import re
from nyx.agent.loop import _core
src = open("nyx/agent/loop/_core.py").read()
assert "strip_ansi_sequences(_clean)" in src, "wire ausente no guard"
assert "strip_ansi_sequences" in src.split("from nyx.agent.loop._iteration import")[1][:200], "import ausente"
print("OK guard: import + wire presentes no ponto único de saída")
PY

# 4. Smoke boot (BRIEF: imprime 'boot ok', exit 0)
./run.sh --smoke

# 5. Invariantes (BRIEF: PASS 14/14, FAIL 0)
bash scripts/sprint_invariants.sh

# 6. Gauntlet rápido (BRIEF: 100%)
./run.sh --gauntlet --only rapido
```

Colar na conclusão: saída dos passos 2/3 (proofs puros), tail de `sprint_invariants.sh`, `boot ok` do smoke, tally do gauntlet, `git --no-pager diff --stat`.

### Baseline de testes
- `sprint_invariants.sh`: FAIL_BEFORE esperado = 0 (14/14). FAIL_AFTER deve permanecer 0.
- Sem suíte pytest no projeto (verificado: sem diretório `tests/`); a prova unitária é o snippet puro do passo 2 (GPU-free).

---

## Critério binário de aceite (IA executora)

- [ ] `strip_ansi_sequences` existe em `_iteration.py`, pura, com fast-path `"\x1b" not in text`
- [ ] Importada em `_core.py` e chamada no guard de saída (L364-367), por último, antes do `.strip()`
- [ ] Proof puro (passo 2) colado: fastfetch sujo -> limpo, idempotente, identidade em texto sem ANSI
- [ ] Proof do wire (passo 3) colado
- [ ] `result.output`/`history` (contexto do modelo) NÃO tocados -- grep confirma zero mudança em `run_command.py`/`_compose_presentation_summary`
- [ ] `ruff` limpo, acentuação rc=0
- [ ] Smoke `boot ok`, invariants 14/14, gauntlet rápido 100%
- [ ] `SPRINT_ORDER_MASTER.md` marca 410 CONCLUIDA; spec movida para `concluidos/`
- [ ] NÃO commitar; NÃO tocar Checkpoint.md

---

## Guardrails anti-engodo (obrigatórios)

NÃO marcar concluída se:
- Stripou ANSI no `result.output` das tools ou no `_compose_presentation_summary` em vez do guard único (muda o contexto do modelo / duplica ponto de saneamento).
- Adicionou branch condicional por borda ("se TUI preserva cor") -- verificado que a TUI não renderiza ANSI como cor; não há cor a preservar.
- Regex ANSI que também come colchetes/texto legítimo (`[foo]` sem ESC deve sobreviver -- o fast-path e a âncora em `\x1b` garantem isso; provar no passo 2 com um texto `[nota] sem esc`).
- Proof puro não colado ou ainda mostra `\x1b`/`[93m`.

Se algo falhar: `[SPRINT 410] BLOQUEADA: <motivo 1 linha>`.

---

## Invariantes a preservar

- **OUTPUT-LEAK-SANITIZE-01:** o contexto do modelo (history / result.output) NÃO muda -- só o texto user-facing. Este strip vive no guard de saída, que só toca `status.summary`.
- **EXEC-CONTRACT / G3 (399):** a apresentação forte continua anexando a saída crua das tools; o strip só higieniza o ANSI, o CONTEÚDO textual do `Resultado:` permanece.
- **Ponto único de saída (LOOP-REMINDER-LEAK-SUMMARY-01):** todo caminho que monta o summary converge no guard L364-367; não criar um segundo ponto de saneamento.
- **GUIDE.md §3 (cirúrgico):** tocar só os 2 arquivos; não reformatar código adjacente.

---

## Riscos e não-objetivos

| Risco | Mitigação |
|-------|-----------|
| Regex ANSI muito agressivo apaga `[texto]` legítimo | Âncora em `\x1b` + fast-path `"\x1b" not in text`: só remove sequências que começam com ESC. Provar com `[nota] sem esc` no passo 2. |
| CSI de 8 bits (`\x9b`) não coberto | fastfetch emite CSI de 7 bits (`\x1b[`); 8-bit é raro em `text=True`. Se surgir em validação futura, registrar sprint nova (protocolo anti-débito) -- não expandir escopo aqui. |
| Ciclo de import ao adicionar `strip_ansi_sequences` | Zero risco: `_iteration` já é importado por `_core` no mesmo bloco (L23-28); é a direção existente. |

**Não-objetivos:** stripar ANSI no output que o modelo vê (contexto); tocar a render-layer da TUI (a TUI já trata como texto); cor no banner (`banner.py`, fora de escopo).

---

## Validação humana (checklist do usuário)

```bash
cd /home/andrefarias/Desenvolvimento/Nyx-Code
git --no-pager show --stat HEAD
NYX_TUI_TEXTUAL=1 ./run.sh   # peça: "roda fastfetch" e observe o bloco Resultado:
# ESPERADO: as infos do sistema aparecem em texto limpo, SEM '[93m'/'[0m'/'[38;2;...' cru.
ls dev-journey/06-sprints/concluidos/SPRINT_OUTPUT_STRIP_ANSI_01.md  # existe após conclusão
```

---

## Referências

- BRIEF: `/home/andrefarias/Desenvolvimento/Nyx-Code/VALIDATOR_BRIEF.md` (seção [CORE] Contratos de runtime)
- Precedente de padrão (guard de saída único, funções puras irmãs): `dev-journey/06-sprints/concluidos/` -- OUTPUT-LEAK-SANITIZE-01, OUTPUT-DONE-SUMMARY-RENDER-01, LOOP-REMINDER-LEAK-SUMMARY-01
- Contrato da apresentação forte: sprint 399 EXEC-CONTRACT-NO-HALLUCINATED-RESULT-01 (`f0883a1`)
- Achado de origem: tabela ONDA-48 do `SPRINT_ORDER_MASTER.md`, linha 410 (validação as-user da 399, turno fastfetch)

---

*"ANSI cru no Resultado: é output real que virou ruído na borda; higienizar no ponto único é cirúrgico, não cosmético."*
