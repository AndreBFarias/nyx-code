## 0. SPEC (machine-readable)

```yaml
sprint:
  id: MEMORY-RECALL-REFRESH-01
  title: "Satelite: recarregar o bundle de memória apos write_memory e no reset (recall stale)"
  onda: 48
  prioridade: ALTA
  tipo: Bugfix
  dependencias: []
  desbloqueia: []

  touches:
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/agent/loop/_core.py
      reason: "_on_post_tool recarrega o bundle apos write_memory; reset() recarrega + reconstroi o prompt"
      linhas_alvo: "169-177 (_on_post_tool), 577-592 (reset)"
  creates: []
  removes: []

  forbidden:
    - "Adicionar emoji"
    - "Usar 'print()' fora de cli.py/output.py"
    - "Mencao a IA proprietaria"
    - "Tocar o loop de execução (399/397/400/398/401), gating, cascata OOM"
    - "Mudar a logica de write_memory/NyxMemory (so RECARREGAR o que ela ja grava)"

  tests:
    - cmd: "./run.sh --gauntlet --only rapido"
      timeout: 300
      deve_passar: true

  acceptance_criteria:
    - "Apos write_memory bem-sucedido, _memory_bundle e recarregado e o system prompt reconstruido (memória disponivel no MESMO turno seguinte)"
    - "reset() recarrega _memory_bundle e reconstroi o prompt (recall pos-reset no mesmo processo não fica stale)"
    - "Proof runtime: gravar memória e, no turno seguinte (mesmo processo), a Nyx CITA a memória gravada (V11 morto same-session)"
    - "Gauntlet rapido 100%"
```

---

# Sprint MEMORY-RECALL-REFRESH-01 — Satelite: recall de memória não-stale

**Status:** PENDENTE
**Data criação:** 2026-06-26
**Modelo obrigatório:** claude-opus-4-7 (executor-sprint autorizado pelo dono nesta onda)

---

## Contexto do projeto (snapshot — não referência)

> **ADRs relevantes (inline):**
> - **ADR-032 A INFRA CARREGA O MODELO:** a memória cross-session é capacidade da infra; gravar e não disponibilizar é a infra falhando, não o modelo.
> - ADR-009, ADR-001, ADR-006, ADR-005, ADR-024, ADR-014, ADR-010.
>
> **Estado (2026-06-26):** `qwen2.5-coder:3b`. ONDA-48 fase raiz: núcleo do contrato (399/397/400/398/401) CONCLUIDO. Este é satélite (V11), independente do contrato. Desenho: `dev-journey/02-architecture/DESENHO_CONTRATO_EXECUCAO.md` (§4, satélite 402). Achado: `dev-journey/07-reports/AUDIT_VALIDACAO_2026_06_26.md` (V11).

---

## Problema

**Achado V11 MEMORY-RECALL-STALE [ALTA]:** `write_memory` grava no disco corretamente (`~/.nyx/memory/<projeto>/`), mas no turno seguinte (mesmo processo) a Nyx diz que "não tem acesso ao seu sistema" / não cita a memória recém-gravada.

**Causa-raiz (verificada no código):** `nyx/agent/loop/_core.py:153-154` carrega `self._memory_bundle = self._memory.load()` UMA vez no `__init__`. O bundle alimenta o system prompt (`_rebuild_system_prompt` -> `build_system_prompt(memory_files=self._memory_bundle)`). Após um `write_memory`:
- o `_on_post_tool` (`_core.py:169-177`) só invalida o repomap para `.py` -- **não recarrega o bundle**;
- `reset()` (`_core.py:577-592`) zera sessão/contadores -- **não recarrega o bundle nem reconstrói o prompt**.

Resultado: o prompt segue com o bundle do boot (stale). A memória gravada nunca entra no contexto até o processo reiniciar.

---

## Solução proposta

Recarregar `_memory_bundle` + reconstruir o prompt nos dois gatilhos (só recarregar o que `NyxMemory` já grava -- zero mudança na lógica de gravação):
1. `_on_post_tool`: após `write_memory` bem-sucedido -> `self._memory_bundle = self._memory.load()` + `self._rebuild_system_prompt()`.
2. `reset()`: idem (recall pós-reset no mesmo processo não fica stale).

---

## Arquivos alvo (paths absolutos)

### `/home/andrefarias/Desenvolvimento/Nyx-Code/nyx/agent/loop/_core.py`

#### Edit 1 — `_on_post_tool` recarrega após write_memory

# Localização aproximada: a closure `_on_post_tool` dentro de `__init__` (linha 169-177)
**Antes:**
```python
        def _on_post_tool(tool_name: str, args: dict, result: Any) -> None:
            if tool_name not in ("write_file", "edit_file", "create_file", "multi_edit", "patch"):
                return
            path = args.get("file_path") or args.get("path") or ""
            if not path or not path.endswith(".py"):
                return
            self._repomap.invalidate(path)
```
**Depois:**
```python
        def _on_post_tool(tool_name: str, args: dict, result: Any) -> None:
            # MEMORY-RECALL-REFRESH-01 (V11): write_memory gravou no disco; recarrega
            # o bundle e reconstroi o prompt p/ a memória entrar no contexto JA no
            # próximo turno (mesmo processo). Sem isto o recall usa o bundle do boot.
            if tool_name == "write_memory":
                if getattr(result, "success", True):
                    self._memory_bundle = self._memory.load()
                    self._rebuild_system_prompt()
                return
            if tool_name not in ("write_file", "edit_file", "create_file", "multi_edit", "patch"):
                return
            path = args.get("file_path") or args.get("path") or ""
            if not path or not path.endswith(".py"):
                return
            self._repomap.invalidate(path)
```

#### Edit 2 — `reset()` recarrega o bundle + reconstrói o prompt

# Localização aproximada: fim de reset() (linha 577-592), após `self._original_input = None`
**Antes:**
```python
        # NYX-PROMPT-REINJECT-01: reset zera contadores da sessão.
        self._tool_calls_count = 0
        self._tool_calls_this_turn = 0
        self._last_reminder_at_count = -1
        self._lang_drift_streak = 0
        self._force_reminder = False
        self._reminder_extra = None
        self._original_input = None
```
**Depois:**
```python
        # NYX-PROMPT-REINJECT-01: reset zera contadores da sessão.
        self._tool_calls_count = 0
        self._tool_calls_this_turn = 0
        self._last_reminder_at_count = -1
        self._lang_drift_streak = 0
        self._force_reminder = False
        self._reminder_extra = None
        self._original_input = None
        # MEMORY-RECALL-REFRESH-01 (V11): recarrega o bundle de memória e reconstroi
        # o prompt -- o usuario pode ter gravado memória antes do reset; sem isto o
        # recall pos-reset (mesmo processo) usa o bundle stale do boot.
        self._memory_bundle = self._memory.load()
        self._rebuild_system_prompt()
```

---

## Diff esperado (resumo)

```
~ 1 arquivo modificado (loop/_core.py)
+ ~12 linhas líquidas
```

---

## Comandos de verificação (literais, copy-paste)

```bash
# 1. Estatica + acentuacao
python -m ruff check nyx/
python3 ~/.config/zsh/scripts/validar-acentuacao.py --paths nyx/agent/loop/_core.py

# 2. Gauntlet
./run.sh --gauntlet --only rapido

# 3. PROOF RUNTIME-REAL as-user (V11 same-session, processo único):
printf '%s\n%s\n' \
  '{"type":"request","content":"lembra que meu projeto favorito se chama Aurora e usa Rust"}' \
  '{"type":"request","content":"qual e o nome e a linguagem do meu projeto favorito?"}' \
  | NYX_AUTO_APPROVE=1 ./run.sh --headless 2>/dev/null
# ESPERADO: turno 1 grava (write_memory, files_modified>=1); turno 2 a Nyx CITA "Aurora" e "Rust"
#           do bundle recarregado -- não diz que não tem acesso. (Confirmar memória em ~/.nyx/memory/.)
```

---

## Critério binário de aceite (IA executora)

- [ ] `_on_post_tool` recarrega bundle + rebuild após `write_memory` bem-sucedido
- [ ] `reset()` recarrega bundle + rebuild
- [ ] Proof runtime as-user colado: gravar + recall same-session cita a memória (V11 morto)
- [ ] `ruff` limpo, acentuação rc=0, `FAIL_AFTER <= FAIL_BEFORE`
- [ ] Gauntlet `rapido` 100%
- [ ] `SPRINT_ORDER_MASTER.md` marca 402 CONCLUIDA; spec movida para `concluidos/`
- [ ] NÃO commitar; NÃO tocar Checkpoint.md; NÃO mudar a lógica de NyxMemory

---

## Guardrails anti-engodo (obrigatórios)

NÃO marcar concluída se:
- Mudou a lógica de gravação de `NyxMemory` (escopo é só RECARREGAR).
- `_rebuild_system_prompt` não foi chamado (recarregar o bundle sem reconstruir o prompt não tem efeito).
- Proof runtime não colado, ou a Nyx não citou a memória no turno 2.

Se algo falhar: `[SPRINT 402] BLOQUEADA: <motivo 1 linha>`.

---

## Proof-of-work obrigatório (4 passos)

```bash
bash scripts/sprint_invariants.sh > /tmp/inv_before.txt 2>&1
FAIL_BEFORE=$(grep -c "^\[FAIL\]" /tmp/inv_before.txt)
# implementar
bash scripts/sprint_invariants.sh > /tmp/inv_after.txt 2>&1
FAIL_AFTER=$(grep -c "^\[FAIL\]" /tmp/inv_after.txt)
diff /tmp/inv_before.txt /tmp/inv_after.txt
```
Colar: inv_before/inv_after (tail), diff, proof runtime as-user (turnos 1 e 2), `git --no-pager diff --stat`.

---

## Gambiarras específicas desta sprint

- **Recarregar sem reconstruir:** trocar `_memory_bundle` sem `_rebuild_system_prompt()` é no-op (o prompt já foi montado). Os dois juntos.
- **Reload em tool errada:** só `write_memory` dispara o reload (não inflar custo a cada tool).
- **Result None:** `getattr(result, "success", True)` tolera result sem o atributo (não derruba o hook).

---

## Validação humana (checklist do usuário)

```bash
cd /home/andrefarias/Desenvolvimento/Nyx-Code
git --no-pager show --stat HEAD
./run.sh   # turno 1: "lembra que X"; turno 2 (mesma sessão): "o que voce lembra sobre X?"
# ESPERADO: turno 2 cita a memória gravada.
ls dev-journey/06-sprints/concluidos/SPRINT_MEMORY_RECALL_REFRESH_01.md  # existe
```

---

## Riscos

| Risco | Mitigação |
|-------|-----------|
| `load()` lento a cada write_memory infla latência | `load()` lê alguns .md pequenos (cap 8KB); write_memory é raro. Aceitável. |
| reset() reconstrói prompt desnecessariamente | reset() é raro (troca de contexto); custo único. |
| Recall cross-session (novo processo) | Já funciona (o bundle é carregado no `__init__`); esta sprint fecha o same-session. |

---

*"Lembrar é recarregar -- a memória que não volta ao contexto é como se não existisse." -- princípio de execução (dev-journey/02-architecture/DESENHO_CONTRATO_EXECUCAO.md)*
