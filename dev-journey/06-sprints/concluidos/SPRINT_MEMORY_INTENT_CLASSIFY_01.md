# SPRINT MEMORY-INTENT-CLASSIFY-01 — "lembra que X" não grava (intent=chat, cap corta write_memory)

## 0. SPEC (machine-readable)

```yaml
sprint:
  id: MEMORY-INTENT-CLASSIFY-01
  title: "Pedido de memória ('lembra que X') é classificado como chat (tools=[]) e write_memory é cortada pelo cap; memória nunca grava"
  onda: 44
  bloco: "44 -- achado do ESTRESSE FINAL da ONDA-44 (memória não persiste na prática)"
  prioridade: ALTA
  tipo: Bugfix / Core loop
  dependencias: []
  desbloqueia: []

  touches:
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/agent/intent.py
      reason: "classify('lembra que X') retornava 'chat' (wants_save_memory ignorado por classify) -> _select_tools_for_context devolve [] -> modelo não recebe write_memory -> alucina 'lembrado' sem gravar."
      linhas_alvo: "classify (antes do return 'chat' final)"
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/agent/loop/_constants.py
      reason: "TOOL_KEYWORDS não tinha write_memory -> mesmo com intent=tool-needed, a tool não era ativada por keyword."
      linhas_alvo: "TOOL_KEYWORDS"
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/agent/loop/_iteration.py
      reason: "Cap de 5 tools prioriza CORE_TOOLS (8 > 5) -> write_memory (extra) sempre cortada. Prioriza write_memory quando wants_save_memory(last_user)."
      linhas_alvo: "_select_tools_for_context, bloco do cap (len(selected) > 5)"

  creates: []
  removes: []
  n_to_n_pairs: []

  forbidden:
    - "Regredir saudação/chat/leitura (write_memory só entra quando wants_save_memory é True)"
    - "Inflar o payload de turnos que não pedem memória"
    - "Adicionar emoji ou menção a IA externa; sem print()"

  tests:
    - cmd: "bash scripts/sprint_invariants.sh"
      timeout: 180
      esperado: "14/14 PASS"
    - cmd: "probe: classify('lembra que X')=tool-needed; write_memory disponível ao modelo; leitura/saudação intactas"
      timeout: 90
      esperado: "write_memory selecionada só no pedido de memória"
    - cmd: "estresse headless real: 'lembra que X' -> write_memory chamada, files_modified=1, arquivo gravado em ~/.nyx/memory"
      timeout: 340
      esperado: "memória grava de verdade (não alucina)"

  acceptance_criteria:
    - "'lembra que X' (sem path-hint) dispara write_memory e grava o arquivo de memória"
    - "Saudação, chat e leitura não passam a forçar write_memory (regressão zero)"
    - "Invariantes 14/14"
```

---

**Status:** PENDENTE
**Data criação:** 2026-06-03
**Origem:** achado do ESTRESSE FINAL da ONDA-44 (validação da Nyx como usuário-final). O fix 359 (roteamento) está correto mas era inócuo aqui: o modelo nem recebia a tool. Bug pré-existente (não introduzido pela ONDA-44).
**Modelo obrigatório:** claude-opus (sem subagentes)

---

## Problema

No estresse final, "lembra que o banco de dados deste projeto e PostgreSQL" produziu `files_modified: 0` e a Nyx respondeu "Sim, lembrado" SEM gravar (alucinação — sintoma #353). Diagnóstico em 3 camadas:

1. **classify** (`intent.py`): `classify("lembra que X")` = **chat** (o `wants_save_memory` existia mas só era usado pelo proxy, não pelo `classify`). Log: `[loop] intent=chat -> tools=[]`.
2. **TOOL_KEYWORDS** (`_constants.py`): não tinha `write_memory` — mesmo com intent=tool-needed, a tool não seria ativada por keyword.
3. **Cap de 5 tools** (`_iteration.py`): prioriza CORE_TOOLS (8 itens) — `write_memory` (extra) é sempre cortada pelo `[:5]`.

Resultado: o modelo nunca recebe `write_memory` no payload → não pode chamá-la → alucina sucesso. Nem o fix 359 (roteamento) nem o remendo do proxy (MEMORY-INTENT-ENFORCE, gated em intent==tool-needed) salvam, porque o intent é `chat`.

## Solução (aplicada e validada no estresse)

1. `classify`: antes do `return "chat"`, `if wants_save_memory(s): return "tool-needed"`.
2. `TOOL_KEYWORDS`: entrada `write_memory` com keywords de memória (lembra/anota/guarda/memoriza/registra/...).
3. Cap: quando `wants_save_memory(last_user)`, `write_memory` entra primeiro nos 5 (antes de CORE).

## Proof-of-work (runtime real — executado)

```
# Probe determinístico
classify('lembra que X') = tool-needed   (saudação/leitura intactas)
write_memory disponível ao modelo = True -> ['write_memory','read_file','write_file','edit_file','run_command']
leitura 'leia README' NÃO força write_memory -> ['read_file','write_file','edit_file','run_command','glob']
invariantes = 14/14 PASS

# Estresse headless real (CPU, GPU degradada por OOM)
ANTES:  files_modified=0, "Sim, lembrado" (alucinação)
DEPOIS: tool_use write_memory{file=banco_de_dados,content="Usa o PostgreSQL..."} -> files_modified=1
        arquivo ~/.nyx/memory/Nyx-Code-*/banco_de_dados.md criado + MEMORY.md atualizado
```

## Critério binário de aceite

- [x] "lembra que X" grava o arquivo de memória (provado no estresse)
- [x] Saudação/chat/leitura não forçam write_memory (probe)
- [x] Invariantes 14/14
- [ ] Spec movida `producao/` → `concluidos/` (na organização final)

---

*"A infra carrega o modelo: se o usuário pede para lembrar, a memória grava -- não importa o modelo." -- ADR-032 aplicado*
