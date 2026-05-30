# SPRINT 291 — INFRA-TUI-APP-ACENTO-DOCSTRINGS-01

## 0. SPEC

```yaml
sprint:
  id: INFRA-TUI-APP-ACENTO-DOCSTRINGS-01
  title: "Saneamento de acentuação em comentários e docstrings legados de nyx/agent/tui/app.py: palavras PT-BR escritas em ASCII (balao, cabecalho, posicao, apos, entao, expoe, construido, comeca, faca, proprio, ...) recebem os diacríticos corretos, sem tocar código executável"
  onda: 34
  prioridade: BAIXA
  tipo: Infra/Doc
  dependencias: [TUI-INPUT-HISTORY-NAV-01]
  desbloqueia: []

  origem: "Achado colateral da validação da SPRINT 289 (TUI-INPUT-HISTORY-NAV-01): ao revisar app.py o validador notou docstrings/comentários legados (escritos nas sprints 283 e anteriores) com palavras PT-BR sem acento. O validador automático (validar-acentuacao.py) não os detecta pois usam termos fora da wordlist dele (balao, cabecalho, posicao, etc.). Registrado como sprint própria conforme protocolo anti-débito."

  touches:
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/agent/tui/app.py
      reason: "Corrigir acentuação em 3 blocos de comentário (linhas ~115-130, 236-238, 337) e 3 docstrings (~190-201, 344-358) — apenas diacríticos em palavras PT-BR; zero mudança em código executável, identificadores, strings de runtime ou assinaturas."
  creates: []
  removes: []

  forbidden:
    - "Tocar qualquer linha de código executável de app.py (só comentários e docstrings)"
    - "Alterar identificadores, nomes de variáveis, strings de runtime ou f-strings"
    - "Corrigir grafia não-acentual (ex.: 'mountado' -> 'montado') — fora do escopo desta sprint de acentuação; mantido como está para diff cirúrgico"
    - "Regredir lazy-mount (283), multiline (286) ou histórico (289) — nenhuma linha de lógica é tocada"
    - "Tocar qualquer outro arquivo além de app.py"
    - "Adicionar emoji ou menção a IA externa"

  tests:
    - cmd: "./run.sh --smoke"
      timeout: 15
      deve_passar: true
    - cmd: "bash scripts/sprint_invariants.sh"
      timeout: 60
      deve_passar: true

  acceptance_criteria:
    - "Zero palavras PT-BR em ASCII remanescentes em comentários/docstrings de app.py (varredura ampla rc=1 = nenhum match)"
    - "python3 -m py_compile nyx/agent/tui/app.py OK"
    - "validar-acentuacao.py --paths nyx/agent/tui/app.py rc=0"
    - "git diff mostra apenas linhas de comentário/docstring (17 insertions / 17 deletions, 1:1)"
    - "Nenhuma linha de código executável no diff"
```

## 1. PROOF-OF-WORK (CONCLUIDA — 2026-05-30)

Blocos saneados em `nyx/agent/tui/app.py`:

- **Comentários `__init__` (115-130):** ate→até, entao→então, inicio→início, balao→balão,
  so→só, cabecalho→cabeçalho, visivel→visível, so-tool→só-tool, expoe→expõe,
  publicos→públicos, "e construido"→"é construído", tambem→também.
- **Docstring `_on_input_submit` (190-201):** comeca→começa, "so monta"→"só monta",
  "NÃO e mountado"→"NÃO é mountado", balao→balão, so-tool→só-tool.
- **Comentários `_process_turn`/lazy-mount (236-238):** "balao ... so e criado"→"balão ... só é criado", inicio→início.
- **Comentário guard de turno (337):** faca→faça, balao→balão, proprio→próprio.
- **Docstring `_on_agent_token` (344-358):** lancaria→lançaria, balao→balão, posicao→posição,
  cronologica→cronológica, apos→após, ja→já.

Mantido deliberadamente (fora de escopo acentual): `mountado`/`mountados` (grafia
portunglish, não é questão de acento; diff cirúrgico).

Validação:
- Varredura ampla PT-ASCII em app.py: rc=1 (nenhum match real; só `mountado` permanece).
- `python3 -m py_compile nyx/agent/tui/app.py`: OK.
- `validar-acentuacao.py --paths nyx/agent/tui/app.py`: rc=0.
- `git diff --stat`: app.py 17 insertions(+) / 17 deletions(-) — 1:1, só comentário/docstring.
- `./run.sh --smoke`: boot OK.
- `bash scripts/sprint_invariants.sh`: 14/14 (FAIL=0).
- `./run.sh --gauntlet --only rapido`: APROVADO (comportamento inalterado — diff é só texto).
