# SPRINT CD-REPOMAP-REPOINT-01 — /cd deve re-apontar o RepoMap (fix 348 ficou incompleto)

## 0. SPEC (machine-readable)

```yaml
sprint:
  id: CD-REPOMAP-REPOINT-01
  title: "set_project_root (/cd) re-aponta o RepoMap; hoje o 'Mapa do repositório' segue indexando o diretório antigo"
  onda: 44
  bloco: "44 -- auditoria das ondas 36-43 (2026-06-03)"
  prioridade: MÉDIA
  tipo: Bugfix / Core loop
  dependencias: []
  desbloqueia: []

  touches:
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/agent/loop/_core.py
      reason: "set_project_root (linha 228-238) re-aponta _project_root, _tools.project_root e reconstrói o system prompt, mas NÃO re-aponta self._repomap (criado no __init__ linha 134 com o root original). O _rebuild_system_prompt (linha 187-226) chama self._repomap.render(...) que segue indexando o diretório ANTIGO."
      linhas_alvo: "228-238 (set_project_root); 134-136 (criação do RepoMap no __init__); 194-203 (render no _rebuild_system_prompt)"
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/agent/repomap.py
      reason: "Pode precisar de um método público para trocar o root e re-indexar (set_root/rebuild), se a classe não suportar hoje. Verificar o __init__ e build()."
      linhas_alvo: "__init__/build/render (confirmar API de root)"

  creates: []
  removes: []
  n_to_n_pairs: []

  forbidden:
    - "Re-instanciar RepoMap a cada turno (caro; build() indexa o repo). Só no /cd."
    - "Deixar o build() do novo root derrubar o boot/turno se falhar (manter try/except como no __init__ linha 137)"
    - "Adicionar emoji ou menção a IA externa"

  tests:
    - cmd: "bash scripts/sprint_invariants.sh"
      timeout: 180
      esperado: "14/14 PASS"
    - cmd: "probe determinístico: agent.set_project_root(novo); o system prompt (agent._system_prompt) não contém símbolos exclusivos do root antigo"
      timeout: 60
      esperado: "repo_map reflete o novo root após /cd"

  acceptance_criteria:
    - "Após set_project_root(novo), o bloco 'Mapa do repositório' do system prompt indexa o NOVO diretório"
    - "O /cd para outro projeto não deixa símbolos do projeto anterior no prompt"
    - "Falha ao indexar o novo root não derruba o turno (degrada para repo_map vazio)"
    - "Invariantes 14/14, ruff limpo, acento rc=0"
```

---

**Status:** PENDENTE
**Data criação:** 2026-06-03
**Origem:** auditoria das ondas 36-43 (achado A2, severidade MÉDIA). Fix 348 (CD-CONTEXT-REBUILD-01) reconstruiu prompt e tools mas esqueceu o repomap.
**Modelo obrigatório:** claude-opus (sem subagentes)

---

## Contexto do projeto (snapshot — não referência)

> - ADR-032 A infra carrega o modelo: o /cd existe para o modelo escrever no diretório certo; um mapa obsoleto reintroduz o erro de "caminho do dir errado".
> - Sprint 348 (CD-CONTEXT-REBUILD-01, commit `3db78e1`) criou `AgentLoop.set_project_root()` para corrigir o `/cd` que não trocava o root. Mas o fix cobriu prompt + tools, não o RepoMap.
> - O RepoMap (`repomap.py`) injeta no system prompt um índice AST de classes/funções do projeto (bloco "Mapa do repositório"), para o modelo não precisar de list_files+search+read_file.

---

## Problema

`set_project_root` (`_core.py:228-238`):

```python
self._project_root = str(new_root)
self._tools.project_root = str(new_root)
self._rebuild_system_prompt()
```

O `self._repomap` foi criado **uma vez** no `__init__` (`_core.py:134`: `self._repomap = RepoMap(project_root)`), com o root **original**. Após `/cd`, o `_rebuild_system_prompt` chama `self._repomap.render(...)` (`_core.py:197`), que continua servindo o índice do **diretório anterior**. Resultado: depois de um `/cd` para outro projeto (cenário real do E2E: `~/Desenvolvimento/VOID-QRcode-Nyx`), o prompt diz "Diretório: /novo" mas o "Mapa do repositório" lista símbolos de `/antigo` — exatamente a confusão de caminhos que a 348 quis eliminar, reintroduzida por outra porta.

---

## Causa-raiz

O fix 348 tratou os dois consumidores óbvios do root (`_project_root` no prompt e `_tools.project_root` nas tools), mas o `RepoMap` mantém estado próprio do root (índice construído no `build()`) e não foi re-apontado nem re-indexado.

---

## Solução proposta

No `set_project_root`, re-apontar e re-indexar o RepoMap **antes** do `_rebuild_system_prompt`:

```python
self._project_root = str(new_root)
self._tools.project_root = str(new_root)
self._repomap = RepoMap(str(new_root))     # ou self._repomap.set_root(new_root)
try:
    self._repomap.build()
except Exception as e:  # noqa: BLE001 -- indexação não derruba o /cd
    logger.warning("repomap: build pós-/cd falhou: %s", e)
self._rebuild_system_prompt()
```

Se `RepoMap` já tiver um caminho mais barato (re-`build()` no mesmo objeto), preferir. Espelhar o tratamento de exceção do `__init__` (`_core.py:135-138`).

---

## Proof-of-work esperado (runtime real)

```bash
bash scripts/sprint_invariants.sh                       # 14/14 PASS
python3 ~/.config/zsh/scripts/validar-acentuacao.py --paths nyx/agent/loop/_core.py nyx/agent/repomap.py
# probe: criar AgentLoop em dir A com símbolo único Sa; /cd para dir B com símbolo Sb;
#        assert Sb in agent._system_prompt and Sa not in agent._system_prompt
```

---

## Critério binário de aceite

- [ ] Após `/cd` para outro projeto, `agent._system_prompt` reflete o novo repo_map
- [ ] Símbolos exclusivos do root antigo não aparecem mais no prompt
- [ ] Falha de indexação do novo root não derruba o turno
- [ ] Invariantes 14/14, ruff limpo, acento rc=0
- [ ] Spec movida `producao/` → `concluidos/`; MASTER marca CONCLUIDA

---

## Riscos

| Risco | Mitigação |
|-------|-----------|
| `build()` do novo root é lento e trava o /cd | Medir; se relevante, indexar em background/lazy. Aceitável: /cd é raro e o usuário espera troca de contexto |
| Re-instanciar RepoMap perde cache de mtime | Aceitável (cache é por arquivo, reconstrói); ou expor set_root que preserva cache |

---

*"Trocar de sala sem trocar o mapa é continuar perdido com endereço novo." -- anônimo*
