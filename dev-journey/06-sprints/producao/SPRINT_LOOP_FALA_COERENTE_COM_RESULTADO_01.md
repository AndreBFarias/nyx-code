## 0. SPEC (machine-readable)

```yaml
sprint:
  id: LOOP-FALA-COERENTE-COM-RESULTADO-01
  numero: 438
  title: "Qualidade da fala: quando uma tool apresentavel roda no turno, a frase do 3b acima do 'Resultado:' não pode narrar o turno errado nem soltar saudacao vazia"
  onda: 48
  prioridade: MEDIA
  tipo: Qualidade
  dependencias: []
  desbloqueia: []
  absorve: []

  touches:
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/agent/loop/_core.py
      reason: "detectar fala incoerente (saudacao generica ou fala que não referencia a ação do turno) em _compose_presentation_summary e substitui-la por um rotulo deterministico derivado da tool+args, preservando o marcador 'Resultado:'; consumir a nova forma da tupla de presentables (name, args, output)"
      linhas_alvo: "63 (regiao dos _RE de modulo -- adicionar _GENERIC_FALA_RE), 569-606 (_compose_presentation_summary: loop 587 e composicao 603-606)"
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/agent/loop/_iteration.py
      reason: "estender a tupla anexada a _turn_presentables de (name, output) para (name, args, output) nos dois sitios de append (caminho nativo e parser fallback) -- args ja estao em escopo em ambos"
      linhas_alvo: "519-520 (caminho nativo, args em escopo desde 500), 662-663 (parser fallback, remapped em escopo desde 564)"
  creates: []
  removes: []

  forbidden:
    - "Adicionar emoji"
    - "Mencao a ferramenta de IA proprietaria"
    - "Remover ou alterar o marcador literal 'Resultado:' (asserido por GAUNTLET-AS-USER-PHASE-01 T1/T3 e OUTPUT-STRIP-ANSI-01)"
    - "Mover ou duplicar o guard de saida único (_core.py L364-367) -- a composicao continua ANTES do guard"
    - "Tocar result.output / history / o contexto do modelo -- so o texto user-facing muda"
    - "Adicionar write_memory/write_file/edit_file a PRESENTABLE_TOOLS (fora de escopo; ver Riscos)"
    - "Suprimir a fala quando ela E coerente (referencia a ação do turno) -- o happy-path fica byte-identico"
    - "Alterar o cap de 8000 chars por bloco nem o dedup de substring exata"

  tests:
    - cmd: "/home/andrefarias/.local/bin/ruff check nyx/agent/loop/_core.py nyx/agent/loop/_iteration.py"
      deve_passar: true
    - cmd: "bash scripts/sprint_invariants.sh"
      deve_passar: true
    - cmd: "./run.sh --smoke"
      deve_passar: true
    - cmd: "./run.sh --gauntlet --only rapido"
      timeout: 300
      deve_passar: true
      nota: "DEFERIDO para GPU exclusiva (contencao Luna) -- ver Proof-of-work"

  acceptance_criteria:
    - "_turn_presentables passa a guardar (name, args, output) nos dois sitios de append (_iteration.py:520 nativo e :663 parser fallback); o loop consumidor em _core.py:587 desempacota os tres campos"
    - "Em _compose_presentation_summary, quando ha presentables e a fala base do 3b e uma SAUDACAO/FILLER generico (regex _GENERIC_FALA_RE), a fala e substituida por um rotulo deterministico derivado da tool+args; o marcador 'Resultado:' e o output cru seguem intactos (cobre T4)"
    - "Quando ha presentables, a fala base e prosa não-trivial E não referencia nenhum ancora da ação do turno (basename do path / pattern / query / 1o token do cmd), a fala e substituida pelo mesmo rotulo deterministico -- cobre T3 (a fala narrava o write_file do turno anterior)"
    - "Quando a fala base referencia a ação do turno (contem um ancora) OU não ha ancora derivavel dos args, a fala e PRESERVADA byte-identica (happy-path intacto -- sem falso-positivo de supressao)"
    - "O rotulo deterministico por tool: list_files/read_file -> 'Conteudo de <path>:'; search -> 'Resultados da busca por <pattern|query>:'; glob -> 'Arquivos que casam <pattern>:'; run_command -> 'Saida do comando <cmd>:' (cmd capado); fallback sem args uteis -> fala vazia (cai no ramo 'Resultado:' puro ja existente)"
    - "Proof runtime-real SEM GPU: AgentLoop real, _compose_presentation_summary real com presentables fabricados -> fala incoerente (T3 e T4) some do summary; fala coerente e preservada"
    - "ruff limpo, acentuacao rc=0, invariantes 14/14 (FAIL_AFTER <= FAIL_BEFORE), smoke boot ok"
```

---

# Sprint LOOP-FALA-COERENTE-COM-RESULTADO-01 — a frase do 3b acima do `Resultado:` deixa de narrar o turno errado

**Status:** PENDENTE
**Data criação:** 2026-07-13
**Modelo obrigatorio:** claude-opus-4-7 (executor-sprint autorizado pelo dono nesta onda)

---

## Contexto do projeto (snapshot — não referencia)

> **ADRs relevantes (inline):**
> - **ADR-032/033 A INFRA CARREGA O MODELO / ENFORCEMENT, não CONFIANCA:** robustez pertence a infra, não ao 3b. A apresentacao forte (G3) ja não confia que o 3b vai apresentar os dados: anexa o output cru da tool sob `Resultado:`. Esta sprint estende o mesmo principio ao TEXTO acima do `Resultado:` -- se a infra ja não confia no 3b para mostrar os dados, tambem não deve deixa-lo narrar o turno errado por cima deles.
> - **ADR-034 (lever = troca de model):** a raiz da fala incoerente e a capacidade do 3b (qwen2.5-coder:3b, a pior maquina possivel). Esta sprint não tenta consertar o modelo -- blinda a apresentacao deterministicamente na infra, como manda a missao (o pior LLM local parecer profissional offline).
> - ADR-035 (`ADR_035_CONTRATO_EXECUCAO.md`): registra as garantias do contrato e o estado 4/5 da validação holistica 2026-07-12.
>
> **Estado (2026-07-12/13):** `qwen2.5-coder:3b`. ONDA-48 fase raiz do contrato CONCLUIDA (399/397/400/398/401). Este e um satelite de QUALIDADE DA FALA (achado transversal MEDIA da validação holistica 2026-07-12, GPU exclusiva). A apresentacao forte G3 salva os DADOS (T1..T4 PASS), mas a fala do 3b por cima mina a confianca. Ports: Ollama `11435`, proxy `11436`.

---

## Problema

**Achado (validação holistica 2026-07-12, sessão unica continua `./run.sh --headless`, 7 turnos, contexto acumulado; log `/tmp/claude-1000/holistica_log.jsonl` turnos 3/4; relatorio `dev-journey/07-reports/AUDIT_2026_07_12.md` §2):**

Quando uma tool apresentavel roda no turno, a resposta final e composta por `_compose_presentation_summary` como `f"{base}\n\nResultado:\n{resultado}"`, onde `base` e a fala do 3b (`status.summary`) e `resultado` e o output cru da tool. O `resultado` esta sempre correto (G3 garante). O problema e o `base`:

- **T3 (listar `~/Desktop`):** a fala = `"Codigo adicionado para a função soma em nyx_hol_2026_07_12.py"` -- narra o turno ANTERIOR (T2, um `write_file`), não a listagem que de fato rodou. A listagem correta aparece sob `Resultado:`, mas a frase por cima descreve outra ação.
- **T4 (buscar TODO):** a fala = `"Ola! Como posso ajudar voce hoje?"` -- saudacao vazia sobre resultados de busca corretos.

**Impacto:** não corrompe dados (G3 anexa o resultado cru correto), mas degrada confianca -- o usuário leigo le uma narracao que não corresponde a ação executada: meia-verdade sistematica em sessão continua. Fere o espirito de "honestidade" do contrato (`DESENHO_CONTRATO_EXECUCAO.md` / ADR-035): a apresentacao deve refletir o que a infra realmente fez.

---

## Causa-raiz (verificada no codigo real — DIVERGENCIAS do briefing registradas)

**DIVERGENCIA 1 (arquivo):** o briefing aponta `_compose_presentation_summary` em `nyx/agent/loop/_iteration.py`. **A função vive em `nyx/agent/loop/_core.py`, def na linha 569** (confirmado por `rg`). O `_iteration.py` so contem os dois SITIOS DE APPEND em `_turn_presentables` (L520 caminho nativo, L663 parser fallback) e o import de `PRESENTABLE_TOOLS` (L28). A linha `:?` do briefing corresponde a `_core.py:569`.

Trecho literal do alvo (`nyx/agent/loop/_core.py`):

```python
569:    def _compose_presentation_summary(self, status: SessionStatus) -> str:
...
579:        presentables = getattr(self, "_turn_presentables", None)
580:        if not presentables:
581:            return status.summary
582:        if status.state not in (SessionState.DONE, SessionState.MAX_ITERATIONS):
583:            return status.summary
584:
585:        base = (status.summary or "").strip()
586:        blocks: list[str] = []
587:        for name, output in presentables:
...
603:        resultado = "\n\n".join(blocks)
604:        if base:
605:            return f"{base}\n\nResultado:\n{resultado}"
606:        return f"Resultado:\n{resultado}"
```

O `base` (fala do 3b) e colado sem qualquer verificação de coerencia com a ação do turno. O sitio de append guarda hoje so `(name, output)` -- os `args` (que dao o `<path>`/`<pattern>` do rotulo deterministico) não chegam ao ponto de composicao. Ambos os sitios de append tem `args` em escopo (`_iteration.py:500-502` passa `name, args, ...`; `:564` monta `remapped`), entao a tupla pode ser estendida sem plumbing novo.

**DIVERGENCIA 2 (T6 e outro mecanismo — não coberto aqui):** o briefing agrupa T3/T4/**T6** ("lembrar cor", `write_memory`) como o mesmo mecanismo. Verificacao no codigo: **`write_memory` não esta em `PRESENTABLE_TOOLS`** (`nyx/agent/loop/_constants.py:67-69` -> `{run_command, list_files, read_file, search, glob}`). Logo `write_memory` NUNCA passa por `_compose_presentation_summary`: não ha bloco `Resultado:` no turno T6, e o "OK: memoria em <path>" e status (como `write_file`, coberto pelo done-guard G2), que so chega ao usuário se o 3b narrar. O `SPRINT_ORDER_MASTER.md` (bloco ONDA-48) confirma: "T6 write_memory PASS (gravou de verdade em `~/.nyx/memory/`)" -- a memoria FOI escrita; o defeito de T6 e so a falta de confirmacao na fala. Isso e um mecanismo DIFERENTE (confirmacao de escrita não-apresentavel), com risco de colidir com `EXEC-CONTRACT-NO-SPURIOUS-MEMORY-01`. **Fica fora de escopo** e vai registrado abaixo como sprint própria (anti-debito). Esta sprint foca o mecanismo principal e cohesivo: a fala incoerente ACIMA de um `Resultado:` de tool apresentavel (T3/T4).

---

## solução proposta

Duas mudancas, cirurgicas e aditivas, sem tocar o happy-path nem o marcador `Resultado:`:

1. **Estender a tupla de presentables** de `(name, output)` para `(name, args, output)` nos dois sitios de append em `_iteration.py` (args ja em escopo) e desempacotar os tres campos no loop consumidor de `_core.py:587`.

2. **Guardar a coerencia da fala em `_compose_presentation_summary`:** antes de colar `base`, decidir se a fala e incoerente:
   - **Saudacao/filler generico** (regex `_GENERIC_FALA_RE`) -> incoerente (cobre T4).
   - **Prosa não-trivial que não referencia a ação do turno** (nenhum ancora dos args -- basename do path, pattern, query, 1o token do cmd -- aparece no `base`) -> incoerente (cobre T3, que narrava o `write_file` do turno anterior).
   - Caso contrario -> **coerente**: preserva `base` byte-identico (happy-path).
   Quando incoerente, substitui `base` por um **rotulo deterministico** derivado da tool+args do primeiro presentable (`Conteudo de <path>:`, `Resultados da busca por <pattern>:`, etc.). Se não houver ancora util, `base` vira vazio e cai no ramo `f"Resultado:\n{resultado}"` ja existente -- o `Resultado:` cru sozinho, sem narracao enganosa.

O marcador `Resultado:` e o `resultado` cru seguem intactos em todos os ramos. O guard de saida único (`_core.py:364-367`) continua rodando DEPOIS da composicao, inalterado.

---

## Arquivos alvo (paths absolutos)

### `/home/andrefarias/Desenvolvimento/Nyx-Code/nyx/agent/loop/_iteration.py`

#### Edit A1 — sitio de append nativo (L519-520): guardar args na tupla

**Antes:**
```python
                if name in PRESENTABLE_TOOLS:
                    self._turn_presentables.append((name, result.output or ""))
```
**Depois:**
```python
                # LOOP-FALA-COERENTE-COM-RESULTADO-01: guarda os args junto do
                # output para o ponto de saida (_compose_presentation_summary)
                # derivar um rotulo deterministico ('Conteudo de <path>:' etc.)
                # quando a fala do 3b for incoerente com a ação do turno.
                if name in PRESENTABLE_TOOLS:
                    self._turn_presentables.append((name, args, result.output or ""))
```

#### Edit A2 — sitio de append do parser fallback (L662-663): idem, com `remapped`

**Antes:**
```python
            if tool_name in PRESENTABLE_TOOLS:
                self._turn_presentables.append((tool_name, result.output or ""))
```
**Depois:**
```python
            # LOOP-FALA-COERENTE-COM-RESULTADO-01: idem caminho nativo -- os args
            # ja saneados (remapped) acompanham o output para o rotulo deterministico.
            if tool_name in PRESENTABLE_TOOLS:
                self._turn_presentables.append((tool_name, remapped, result.output or ""))
```

### `/home/andrefarias/Desenvolvimento/Nyx-Code/nyx/agent/loop/_core.py`

#### Edit B1 — regex de modulo (junto dos `_RE` existentes, ~L63)

Adicionar (o executor confirma a regiao com `rg -n "_DONE_HINT_RE = re.compile"`):

```python
# LOOP-FALA-COERENTE-COM-RESULTADO-01: saudacao/filler generico que o 3b solta
# como "resposta" mesmo tendo rodado uma tool apresentavel no turno. Casa a
# ABERTURA da fala (não uma substring qualquer no meio de uma prosa legitima).
# Curado da evidencia da validação holistica 2026-07-12 (T4/T6). ADR-032: a
# infra não confia que o 3b vai narrar o turno certo.
_GENERIC_FALA_RE = re.compile(
    r"^\s*(ola|oi|entendi|estou aqui|posso ajudar|como posso"
    r"|vou (te )?ajudar|posso gostaria)\b",
    re.IGNORECASE,
)
```

#### Edit B2 — coerencia da fala em `_compose_presentation_summary` (L585-606)

Substituir o desempacote do loop e a composicao final. **Antes (L585-606):**
```python
        base = (status.summary or "").strip()
        blocks: list[str] = []
        for name, output in presentables:
            ...
            blocks.append(out[:8000])
        if not blocks:
            return base

        resultado = "\n\n".join(blocks)
        if base:
            return f"{base}\n\nResultado:\n{resultado}"
        return f"Resultado:\n{resultado}"
```
**Depois (esboco -- o executor mantem o corpo do loop intacto, so muda o desempacote para `name, args, output` e a decisao do `base`):**
```python
        base = (status.summary or "").strip()
        blocks: list[str] = []
        for name, args, output in presentables:
            # ... corpo do loop inalterado (filtro PRESENTABLE_TOOLS, dedup, cap 8000) ...
            blocks.append(out[:8000])
        if not blocks:
            return base

        # LOOP-FALA-COERENTE-COM-RESULTADO-01: a fala do 3b acima do Resultado:
        # não pode narrar o turno errado (T3: eco do write_file anterior) nem
        # soltar saudacao vazia (T4). Se incoerente com a ação do turno, troca por
        # um rotulo deterministico derivado da tool+args (mesmo espirito do G3).
        if base and not self._fala_referencia_turno(base, presentables):
            base = self._rotulo_deterministico(presentables)

        resultado = "\n\n".join(blocks)
        if base:
            return f"{base}\n\nResultado:\n{resultado}"
        return f"Resultado:\n{resultado}"
```

#### Edit B3 — dois helpers puros novos (metodos de `AgentLoop`, junto de `_compose_presentation_summary`)

```python
    @staticmethod
    def _ancoras_do_turno(presentables) -> list[str]:
        """Tokens (>= 3 chars, lowercase) que uma fala coerente citaria: basename
        do path, pattern, query, 1o token do cmd. Fonte: os args de cada presentable."""
        ancoras: list[str] = []
        for _name, args, _out in presentables:
            if not isinstance(args, dict):
                continue
            for key in ("path", "file_path", "pattern", "query"):
                val = str(args.get(key) or "").strip()
                if val:
                    ancoras.append(Path(val).name.lower() if key in ("path", "file_path") else val.lower())
            cmd = str(args.get("command") or args.get("cmd") or "").strip()
            if cmd:
                ancoras.append(cmd.split()[0].lower())
        return [a for a in ancoras if len(a) >= 3]

    def _fala_referencia_turno(self, base: str, presentables) -> bool:
        """True se a fala e coerente com a ação do turno. Incoerente = saudacao
        generica OU prosa que não cita nenhum ancora do turno. Conservador: sem
        ancora derivavel, devolve True (não suprime -- evita falso-positivo)."""
        if _GENERIC_FALA_RE.match(base):
            return False
        ancoras = self._ancoras_do_turno(presentables)
        if not ancoras:
            return True
        low = base.lower()
        return any(a in low for a in ancoras)

    @staticmethod
    def _rotulo_deterministico(presentables) -> str:
        """Rotulo derivado da PRIMEIRA tool apresentavel do turno. Sem ancora util,
        devolve '' (cai no ramo 'Resultado:' puro)."""
        name, args, _out = presentables[0]
        args = args if isinstance(args, dict) else {}
        path = str(args.get("path") or args.get("file_path") or "").strip()
        patt = str(args.get("pattern") or args.get("query") or "").strip()
        cmd = str(args.get("command") or args.get("cmd") or "").strip()
        if name in ("list_files", "read_file") and path:
            return f"Conteudo de {path}:"
        if name == "search" and patt:
            return f"Resultados da busca por {patt}:"
        if name == "glob" and patt:
            return f"Arquivos que casam {patt}:"
        if name == "run_command" and cmd:
            return f"Saida do comando {cmd[:80]}:"
        return ""
```

> `Path` ja esta importado em `_core.py` (L16). O executor confirma antes de usar.

---

## Diff esperado (resumo)

```
~ 2 arquivos modificados (nyx/agent/loop/_core.py, nyx/agent/loop/_iteration.py)
+ ~50 linhas liquidas (regex + 3 helpers + 2 sitios de append de 1 token cada)
```

Sem aritmetica de extracao: esta sprint não tem meta `arquivo < NNNL`. Fix aditivo; `_core.py` segue < 1200L, `_iteration.py` segue ~1106L.

---

## Comandos de verificação (literais, copy-paste)

```bash
cd /home/andrefarias/Desenvolvimento/Nyx-Code

# 1. Estatica + acentuacao (ruff via binario direto -- ver BRIEF)
/home/andrefarias/.local/bin/ruff check nyx/agent/loop/_core.py nyx/agent/loop/_iteration.py
python3 ~/.config/zsh/scripts/validar-acentuacao.py --paths nyx/agent/loop/_core.py nyx/agent/loop/_iteration.py

# 2. Confirmar as ancoras (linhas podem ter deslizado -- reconferir):
rg -n "_turn_presentables.append|_compose_presentation_summary|def _fala_referencia_turno|_GENERIC_FALA_RE|Resultado:" nyx/agent/loop/_core.py nyx/agent/loop/_iteration.py

# 3. PROOF RUNTIME-REAL SEM GPU: AgentLoop real, _compose_presentation_summary real.
#    Fabrica presentables com args e uma fala incoerente (T3 e T4); não sobe Ollama.
./venv/bin/python - <<'PY'
from nyx.agent.loop._core import AgentLoop
from nyx.agent.models import SessionStatus, SessionState

loop = AgentLoop(project_root=".")

# --- T4: saudacao vazia sobre uma busca correta ---
loop._turn_presentables = [("search", {"pattern": "TODO"}, "arquivo.py:12: # TODO revisar")]
st = SessionStatus(state=SessionState.DONE, iterations=1,
                   summary="Ola! Como posso ajudar voce hoje?")
out = loop._compose_presentation_summary(st)
print("T4:\n", out)
assert "Como posso ajudar" not in out, out
assert "Resultado:" in out and "TODO revisar" in out, out
assert "busca por TODO" in out, out

# --- T3: fala narra o write_file do turno anterior sobre uma listagem correta ---
loop._turn_presentables = [("list_files", {"path": "/home/x/Desktop"},
                            "a.txt\nb.txt\nnyx_hol_2026_07_12.py")]
st = SessionStatus(state=SessionState.DONE, iterations=1,
                   summary="Codigo adicionado para a função soma em nyx_hol_2026_07_12.py")
out = loop._compose_presentation_summary(st)
print("T3:\n", out)
# a narracao do write_file some; sobra rotulo deterministico + Resultado cru
assert "Codigo adicionado" not in out, out
assert "Conteudo de /home/x/Desktop:" in out, out
assert "Resultado:" in out and "b.txt" in out, out

# --- HAPPY-PATH: fala coerente (cita o path) e preservada byte-identica ---
loop._turn_presentables = [("list_files", {"path": "/home/x/Desktop"}, "a.txt\nb.txt")]
st = SessionStatus(state=SessionState.DONE, iterations=1,
                   summary="Aqui esta o conteudo do seu Desktop:")
out = loop._compose_presentation_summary(st)
print("HAPPY:\n", out)
assert out.startswith("Aqui esta o conteudo do seu Desktop:"), out

print("OK: fala incoerente (T3/T4) trocada por rotulo deterministico; fala coerente preservada")
PY

# 4. Invariantes + smoke
bash scripts/sprint_invariants.sh
./run.sh --smoke   # deve imprimir 'boot ok'

# 5. Gauntlet as-user (marcador Resultado: preservado) -- DEFERIDO p/ GPU exclusiva:
./run.sh --gauntlet --only rapido
```

> Nota GPU: o passo 3 roda SEM Ollama/GPU (so `_compose_presentation_summary`, função pura sobre estado fabricado). O passo 5 (gauntlet) exige GPU exclusiva -- executar so quando `pgrep -af "Luna.*driver|valida_sprint"` estiver vazio (protocolo anti-contencao do BRIEF).

---

## Aritmetica

Esta sprint não tem meta numerica de tamanho de arquivo. O único numero relevante e o net-add (~50L em 2 arquivos). Nenhuma extracao planejada.

---

## Criterio binario de aceite (IA executora)

- [ ] `_turn_presentables` guarda `(name, args, output)` nos dois sitios (`_iteration.py:520` e `:663`); loop de `_core.py:587` desempacota `name, args, output`
- [ ] `_GENERIC_FALA_RE` adicionado na regiao dos `_RE` de modulo; casa a ABERTURA da fala (ancorado em `^`), não substring do meio
- [ ] `_fala_referencia_turno` + `_ancoras_do_turno` + `_rotulo_deterministico` adicionados como metodos puros; conservador (sem ancora -> preserva a fala)
- [ ] Fala incoerente (saudacao OU zero-ancora) trocada por rotulo deterministico; fala coerente preservada byte-identica
- [ ] Marcador `Resultado:` e output cru intactos em todos os ramos; guard de saida (L364-367) inalterado e ainda apos a composicao
- [ ] Proof runtime-real (passo 3) colado: T3 e T4 sem a narracao errada, happy-path preservado
- [ ] `write_memory`/`write_file`/`edit_file` não adicionados a `PRESENTABLE_TOOLS` (T6 fora de escopo)
- [ ] `ruff` limpo, acentuacao rc=0, `FAIL_AFTER <= FAIL_BEFORE`, smoke boot ok
- [ ] Gauntlet `--only rapido` 100% (DEFERIDO p/ GPU exclusiva)
- [ ] `SPRINT_ORDER_MASTER.md` marca 438 CONCLUIDA; spec movida para `concluidos/`
- [ ] não commitar; não tocar Checkpoint.md

---

## Guardrails anti-engodo (obrigatorios)

não marcar concluida se:
- A fala coerente (que cita o path/pattern do turno) foi suprimida -- isso e regressao do happy-path, não o fix.
- O marcador `Resultado:` sumiu, mudou de texto, ou a composicao passou a rodar DEPOIS do guard de saida.
- A regex `_GENERIC_FALA_RE` casa substring no MEIO de uma prosa legitima (tem de ser ancorada em `^` -- so a abertura da fala).
- Os helpers ficaram não-conservadores: sem ancora derivavel dos args, a fala DEVE ser preservada (nunca suprimir no escuro).
- `result.output` / history / contexto do modelo mudou (grep confirma zero mudanca fora do texto user-facing).
- `write_memory`/`write_file` entraram em `PRESENTABLE_TOOLS` (isso e a sprint de T6, fora de escopo -- ver Riscos).
- Proof runtime-real não colado, ou T3/T4 ainda mostram a narracao errada.

Se algo falhar: `[SPRINT 438] BLOQUEADA: <motivo 1 linha>`.

---

## Proof-of-work esperado (runtime-real do VALIDATOR_BRIEF)

```bash
bash scripts/sprint_invariants.sh > /tmp/inv_before.txt 2>&1
FAIL_BEFORE=$(grep -c "^\[FAIL\]" /tmp/inv_before.txt)
# implementar
bash scripts/sprint_invariants.sh > /tmp/inv_after.txt 2>&1
FAIL_AFTER=$(grep -c "^\[FAIL\]" /tmp/inv_after.txt)
diff /tmp/inv_before.txt /tmp/inv_after.txt
```

Baseline esperado: `FAIL_BEFORE = 0`, `FAIL_AFTER <= 0`. Colar:
- `inv_before`/`inv_after` (tail) + diff
- output do proof runtime-real (passo 3 -- SEM GPU)
- `rg` do passo 2 (ancoras confirmadas)
- `git --no-pager diff --stat`
- `./run.sh --smoke` (deve imprimir `boot ok`)

**DEFERIDO para GPU exclusiva** (contencao Luna, como as specs 403/407): `./run.sh --gauntlet --only rapido` 100% (confirma que o marcador `Resultado:` segue asserido por GAUNTLET-AS-USER-PHASE-01) e a re-execução da validação holistica as-user (T3/T4 devem mostrar rotulo deterministico, não a narracao do turno errado). Executar so quando a GPU estiver livre (`pgrep -af "Luna.*driver|valida_sprint"` vazio).

---

## Gambiarras especificas desta sprint

- **Tupla de 3 vs assinatura publica:** `_turn_presentables` e estado interno (`self._`), nunca serializado nem parte de API -- estender a tupla e seguro; o único consumidor e `_compose_presentation_summary` (grep confirma).
- **Ancora conservadora:** exigir `len >= 3` e `basename` do path evita casar tokens ruidosos (`/`, `.`, `~`). Sem ancora derivavel (args sem path/pattern/cmd), a fala e PRESERVADA -- prefere-se um falso-negativo (fala incoerente rara escapa) a um falso-positivo (suprimir uma fala legitima).
- **Regex ancorada em `^`:** casar a ABERTURA da fala, não substring. "Ola! ..." casa; "Encontrei um TODO, ola mundo no arquivo" não casa (a fala referencia a ação e ja seria coerente pela ancora).
- **Primeiro presentable para o rotulo:** quando ha varias tools apresentaveis no turno, o rotulo usa a primeira -- suficiente como cabecalho honesto; o `Resultado:` abaixo carrega TODOS os blocos crus (comportamento inalterado).

---

## validação humana (checklist do usuário)

```bash
cd /home/andrefarias/Desenvolvimento/Nyx-Code
git --no-pager show --stat HEAD

# Com o stack real (GPU exclusiva), sessão continua: primeiro peca uma ação
# (ex.: criar arquivo), depois peca "liste ~/Desktop". A resposta a listagem
# não pode narrar a criação anterior -- deve mostrar 'Conteudo de ~/Desktop:'
# (ou so 'Resultado:') com a listagem crua, nunca a frase do turno errado.

ls dev-journey/06-sprints/concluidos/SPRINT_LOOP_FALA_COERENTE_COM_RESULTADO_01.md  # apos concluir
```

---

## Riscos e não-objetivos

| Risco / não-objetivo | Decisao |
|-------|-----------|
| **T6: confirmar a escrita de `write_memory` na fala** (achado do briefing) | **FORA DE ESCOPO -- mecanismo diferente.** `write_memory` não esta em `PRESENTABLE_TOOLS` e nunca passa por `_compose_presentation_summary`; sua confirmacao seria uma feature nova (status de escrita não-apresentavel), com risco de colidir com `EXEC-CONTRACT-NO-SPURIOUS-MEMORY-01`. Registrar sprint própria `LOOP-MEMORY-WRITE-CONFIRM-01` (anti-debito: `feedback_nenhum_debito`). Ver "Fora de escopo" abaixo. |
| Falso-positivo: suprimir uma fala legitima | Mitigado: heuristica conservadora (sem ancora -> preserva; regex so na abertura). Happy-path testado no proof. |
| Rotulo deterministico soar redundante com `Resultado:` | Aceitavel -- e um cabecalho honesto ("Conteudo de X:") acima dos dados crus; melhor que uma narracao falsa. Sem ancora, cai no `Resultado:` puro. |
| Fala coerente mas em outro idioma (drift) | Fora de escopo -- drift de idioma e coberto por `NYX-PROMPT-REINJECT-01` / `LOOP-RECOVERY-TRIGGER-PTBR-01`, não por esta sprint. |

### Fora de escopo (anti-debito)

- **`LOOP-MEMORY-WRITE-CONFIRM-01` (recomendada):** T6 -- quando `write_memory` grava de fato (`~/.nyx/memory/`), a resposta deve CONFIRMAR a gravacao ("Memoria gravada em <path>") em vez de deixar so a fala do 3b (que na holistica soltou saudacao/filler). Mecanismo distinto: `write_memory` e não-apresentavel; a confirmacao teria de vir do resultado da tool (status), com cuidado para não reintroduzir escrita espuria (interação com `EXEC-CONTRACT-NO-SPURIOUS-MEMORY-01`). Prioridade MEDIA, mesma origem (holistica 2026-07-12 T6).

---

## Referencias

- BRIEF: `/home/andrefarias/Desenvolvimento/Nyx-Code/VALIDATOR_BRIEF.md`
- Achado + relatorio: `dev-journey/07-reports/AUDIT_2026_07_12.md` §2 (validação holistica 2026-07-12, GPU exclusiva)
- Contrato / apresentacao forte G3: `dev-journey/02-architecture/ADR_035_CONTRATO_EXECUCAO.md`, `DESENHO_CONTRATO_EXECUCAO.md`
- Codigo alvo: `nyx/agent/loop/_core.py:569` (`_compose_presentation_summary`), `nyx/agent/loop/_iteration.py:520` e `:663` (append de presentables), `nyx/agent/loop/_constants.py:67-69` (`PRESENTABLE_TOOLS`)
- Precedente de estrutura: `dev-journey/06-sprints/producao/SPRINT_EXEC_CONTRACT_PROXY_STATUS_BEFORE_JSON_01.md` (413)
- Marcador `Resultado:` asserido por: `SPRINT_GAUNTLET_AS_USER_PHASE_01.md` (T1/T3), `SPRINT_OUTPUT_STRIP_ANSI_01.md`

---

*"A infra ja não confia que o 3b vai mostrar os dados (G3). Tambem não deve deixa-lo narrar o turno errado por cima deles." -- principio de apresentacao forte (ADR-032/035)*
