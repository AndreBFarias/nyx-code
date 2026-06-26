# SPRINT FS-TILDE-EXPAND-01 -- `~` não e expandido; vira caminho relativo colado na raiz do projeto

## 0. SPEC (machine-readable)

```yaml
sprint:
  id: FS-TILDE-EXPAND-01
  title: "validate_path não expande `~`: read_file/glob/list com `~/.bashrc` resolvem para .../Nyx-Code/~/.bashrc (relativo a raiz) e falham; completa o acesso universal (bug #1) para caminhos do home"
  onda: 47
  bloco: "47 -- UX/Input/FS-polish (Onda de validação 2, 2026-06-25)"
  prioridade: ALTA
  tipo: Bugfix / Tools (filesystem)
  dependencias: []
  desbloqueia: []

  touches:
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/agent/tools/base.py
      reason: "validate_path (linhas ~156-201): `raw = Path(file_path.strip())` não chama expanduser; `~/.bashrc` não e is_absolute() -> cai no ramo relativo `(base / raw).resolve()` -> `.../Nyx-Code/~/.bashrc`. Provado na imagem: read_file ~/.bashrc -> 'Arquivo não encontrado: /home/andrefarias/Desenvolvimento/Nyx-Code/~/.bashrc'. O `_resolve` ja usa expanduser, mas o raw do validate_path não. Fix: expanduser no raw antes do is_absolute()."
      linhas_alvo: "159-166 (raw / is_absolute / ramo relativo)"

  creates: []
  removes: []

  forbidden:
    - "Mexer na politica de acesso (free access) ou no bloqueio de secrets -- so a EXPANSAO de ~; `~/.ssh/...` apos expandir deve continuar BLOQUEADO (testar)"
    - "Quebrar caminhos relativos legitimos (ex.: `nyx/agent`) -- expanduser não afeta paths sem ~"
    - "Quebrar caminhos absolutos ja funcionando (/etc, /home/...)"
    - "emoji / mencao a IA externa"

  tests:
    - cmd: "probe ToolRegistry: read_file({'file_path':'~/.bashrc'}) -> le o arquivo real (~/.bashrc), não 'Arquivo não encontrado: .../Nyx-Code/~/.bashrc'"
      timeout: 60
      esperado: "tilde expandido para o home real"
    - cmd: "probe: glob/list_files com path '~' ou '~/algumapasta' -> lista o conteudo real do home"
      timeout: 60
      esperado: "funciona"
    - cmd: "probe NEGATIVO seguranca: read_file('~/.ssh/id_rsa') -> apos expandir, BLOQUEADO (_is_secret_path)"
      timeout: 60
      esperado: "success=False, erro de seguranca"
    - cmd: "./run.sh --gauntlet --only fs_arbitrary && ./run.sh --gauntlet --only rapido"
      timeout: 600
      esperado: "ambos verdes (sem regressao)"
    - cmd: "bash scripts/sprint_invariants.sh"
      timeout: 180
      esperado: "14/14 PASS"

  acceptance_criteria:
    - "`~` e `~/...` sao expandidos para o home real em read/glob/list/search (via validate_path)"
    - "Caminhos relativos e absolutos ja corretos seguem identicos (regressao zero)"
    - "Secret sob `~` (ex.: ~/.ssh) continua bloqueado apos expansao"
    - "fs_arbitrary + rapido verdes; invariantes 14/14; spec -> concluidos/"
```

---

**Status:** CONCLUIDA (2026-06-25, commit df94163)
**Data criação:** 2026-06-25
**Origem:** Onda de validação 2 (teste as-user do dono, imagens). `read_file({'file_path':'~/.bashrc'})` retornou "Arquivo não encontrado: /home/andrefarias/Desenvolvimento/Nyx-Code/~/.bashrc" -- o `~` foi colado na raiz do projeto. Completa o bug #1 (acesso universal) para caminhos do home.
**Implementação:** direta, sem subagentes.

---

## Problema

`nyx/agent/tools/base.py`, `validate_path`:

```python
raw = Path(file_path.strip())
if raw.is_absolute():
    resolved = raw.resolve()
else:
    base = _ACTIVE_ROOT if _ACTIVE_ROOT is not None else _resolve(project_root)
    resolved = (base / raw).resolve()
```

`Path("~/.bashrc").is_absolute()` e False (o `~` não e expandido por `Path()`), entao cai no ramo relativo e vira `<raiz>/~/.bashrc`. O helper `_resolve` ate usa `expanduser()`, mas o `raw` do validate_path não -- inconsistencia. Resultado: qualquer caminho com `~` falha (read/glob/list/search), como o dono viu ao vivo.

---

## Causa-raiz

Falta `expanduser()` no `raw` do `validate_path`. O `~` so e expandido na resolucao da raiz (`_resolve`), não no caminho-alvo recebido.

---

## solução proposta

```python
raw = Path(file_path.strip()).expanduser()
if raw.is_absolute():   # apos expanduser, ~/.bashrc vira /home/user/.bashrc (absoluto)
    ...
```

Assim `~/...` vira absoluto e segue o caminho ja correto (free access + secret-block). Paths sem `~` não mudam.

---

## Proof-of-work esperado

```bash
./venv/bin/python -c "from nyx.agent.tools.read_file import ReadFileTool; import os; print(ReadFileTool().execute({'file_path':'~/.bashrc'}, os.getcwd()))"  # le o real, não .../Nyx-Code/~/.bashrc
./venv/bin/python -c "from nyx.agent.tools.list_files import ListFilesTool; import os; print(ListFilesTool().execute({'path':'~'}, os.getcwd()).output[:200])"  # lista o home
# secret: read_file('~/.ssh/id_rsa') -> success=False (bloqueado apos expandir)
./run.sh --gauntlet --only fs_arbitrary
./run.sh --gauntlet --only rapido
bash scripts/sprint_invariants.sh
python3 ~/.config/zsh/scripts/validar-acentuacao.py --paths nyx/agent/tools/base.py
/home/andrefarias/.local/bin/ruff check nyx/agent/tools/base.py
```

---

## Criterio binario de aceite

- [ ] `~`/`~/...` expandem para o home em read/glob/list/search
- [ ] regressao zero em relativos/absolutos
- [ ] secret sob ~ bloqueado apos expansao
- [ ] fs_arbitrary + rapido verdes; invariantes 14/14; spec -> concluidos/

---

## Riscos

| Risco | Mitigacao |
|-------|-----------|
| expanduser sem HOME definido | Path.expanduser e no-op se ~ não resolve; comportamento atual (relativo) preservado nesse caso |
| ~user (outro usuario) | expanduser cobre ~user tambem; secret-block segue valendo |

---

*"O til e atalho pra casa; ignora-lo e mandar o agente pra um endereco que não existe." -- anonimo*
