# SPRINT 265 — CLEANUP-OPENCLAUD-REFS-01

## 0. SPEC (machine-readable)

```yaml
sprint:
  id: CLEANUP-OPENCLAUD-REFS-01
  title: "Trocar exemplos cosméticos que citam o port openclaud<!-- noqa-cli-externo --> abandonado"
  onda: 31
  prioridade: BAIXA
  tipo: Cleanup
  dependencias: []
  desbloqueia: []

  touches:
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/agent/commands/plan.py
      reason: "Exemplo de ajuda do /plan cita openclaud<!-- noqa-cli-externo -->/src/streaming/ (dir gitignored, pode não existir)"
      linhas_alvo: "36"
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/scripts/gauntlet/nyx_gauntlet.py
      reason: "Fixture CTX-10 usa path simulado openclaud<!-- noqa-cli-externo -->/src/streaming/index.ts"
      linhas_alvo: "3990"
  creates: []
  removes: []

  forbidden:
    - "Remover a entrada 'openclaud<!-- noqa-cli-externo -->' da skip-list em nyx/agent/repomap.py:39 (LEGÍTIMA: ignora o dir local)"
    - "Remover/alterar _check_openclaud<!-- noqa-cli-externo -->e_refs em scripts/sync.py (LEGÍTIMO: check de governança anti-port-residual)"
    - "Adicionar emoji / menção a IA externa"

  tests:
    - cmd: "./run.sh --gauntlet --only contexto"
      timeout: 180
      deve_passar: true

  acceptance_criteria:
    - "plan.py exemplo aponta para um path REAL do repo (ex: nyx/agent/streaming.py)"
    - "gauntlet CTX-10 fixture usa path real do repo"
    - "repomap.py skip-list e sync.py check INTACTOS (forbidden)"
    - "gauntlet --only contexto passa (CTX-10 inclusive)"
    - "smoke boot ok + invariantes 14/14"
```

---

**Status:** PENDENTE
**Data criação:** 2026-05-26
**Modelo obrigatório:** claude-opus-4-7 (sem subagentes)

---

## Contexto

> O port TS de referência (`openclaud<!-- noqa-cli-externo -->/`) está no `.gitignore` (0 arquivos rastreados no git). É material local do dev, não versionado. Decisão do usuário (2026-05-26): limpar referências residuais.

## Problema + triagem (auditoria 2026-05-26)

Há 4 referências textuais a `openclaud<!-- noqa-cli-externo -->` no código. **Só 2 devem mudar; as outras 2 são legítimas:**

| Ref | Natureza | Ação |
|---|---|---|
| `nyx/agent/repomap.py:39` | skip-list de dirs ignorados na indexação (junto com `node_modules`, `dist`, `.nyx`) | **MANTER** — remover faria o repomap tentar indexar o dir local (1884 TS) |
| `scripts/sync.py:_check_openclaud<!-- noqa-cli-externo -->e_refs` | check de governança que detecta menções residuais ao port | **MANTER** — feature de qualidade/anonimato |
| `nyx/agent/commands/plan.py:36` | exemplo no `examples=[...]` do `/plan add ler openclaud<!-- noqa-cli-externo -->/src/streaming/` | **TROCAR** por path real |
| `scripts/gauntlet/nyx_gauntlet.py:3990` | fixture CTX-10: `add_tool_call("read_file", {"file_path": "openclaud<!-- noqa-cli-externo -->/src/streaming/index.ts"}, ...)` (path simulado, não lê arquivo) | **TROCAR** por path real |

## Solução

- `plan.py:36`: trocar o exemplo `"/plan add ler openclaud<!-- noqa-cli-externo -->/src/streaming/"` por algo real, ex.: `"/plan add ler nyx/agent/streaming.py"`.
- `gauntlet:3990`: trocar `"openclaud<!-- noqa-cli-externo -->/src/streaming/index.ts"` e o texto do user (`"quero portar o módulo streaming do TS pra Python"`) por um cenário equivalente sobre arquivo real do repo (ex.: `nyx/agent/streaming.py`), preservando a semântica do teste CTX-10 (Summarizer roundtrip — só precisa de um path plausível na string).
- **NÃO tocar** `repomap.py:39` nem `sync.py` (ver forbidden).

## Comandos de verificação

```bash
grep -rn "openclaud<!-- noqa-cli-externo -->" nyx/ scripts/                # repomap.py:39 + sync.py devem PERMANECER; plan.py + gauntlet trocados
/home/andrefarias/.local/bin/ruff check nyx/agent/commands/plan.py scripts/gauntlet/nyx_gauntlet.py
./run.sh --gauntlet --only contexto               # CTX-10 passa com novo path
./run.sh --smoke
python3 ~/.config/zsh/scripts/validar-acentuacao.py --paths nyx/agent/commands/plan.py scripts/gauntlet/nyx_gauntlet.py
```

## Critério binário de aceite

- [ ] `plan.py` e `gauntlet:3990` sem referência a `openclaud<!-- noqa-cli-externo -->`
- [ ] `repomap.py:39` e `sync.py` _check_openclaud<!-- noqa-cli-externo -->e_refs INTACTOS
- [ ] gauntlet `--only contexto` passa (CTX-10)
- [ ] smoke + invariantes 14/14 + ruff + acentuação rc=0
- [ ] spec movida `producao/` -> `concluidos/`

## Proof-of-work

`grep openclaud<!-- noqa-cli-externo -->` (mostrando os 2 que ficaram e 2 que saíram) + output gauntlet `--only contexto` + invariantes.

---

*"Limpar é distinguir o que sustenta do que só sobrou." -- anônimo*
