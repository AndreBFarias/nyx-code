# SPRINT 294 — INFRA-BRIEF-ANTISANITIZER-REPL-APP-STALE-01

## 0. SPEC

```yaml
sprint:
  id: INFRA-BRIEF-ANTISANITIZER-REPL-APP-STALE-01
  title: "Sincronizar VALIDATOR_BRIEF.md com a realidade pós-ONDA-32: a seção [CORE] anti-sanitizer e a descrição de tipo referenciam nyx/agent/repl_app.py (removido com a stack prompt_toolkit) e 'prompt_toolkit', deixando o snippet de protocolo de regressão com um Path inexistente que crasharia"
  onda: 34
  prioridade: BAIXA
  tipo: Infra/Doc
  dependencias: [TUI-FOOTER-VRAM-REALTIME-01]
  desbloqueia: []

  origem: "Achado colateral da SPRINT 288 (TUI-FOOTER-VRAM-REALTIME-01): ao revisar o BRIEF o validador notou que o protocolo anti-sanitizer lista 7 arquivos protegidos incluindo nyx/agent/repl_app.py, que não existe mais (removido em TUI-DEFAULT-FLIP-LEGACY-RM-01, ONDA-32). O snippet bash da linha 73 faria Path('nyx/agent/repl_app.py').read_text() crashar."

  touches:
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/VALIDATOR_BRIEF.md
      reason: "Atualizar a descrição de tipo (prompt_toolkit → Textual) e a seção [CORE] anti-sanitizer: remover repl_app.py do snippet runnable (7→6 arquivos), do gatilho do protocolo e da regra de diagnóstico forward-looking; adicionar nota autoritativa que contextualiza as menções históricas pré-ONDA-32 sem reescrever os logs append-only."
  creates: []
  removes: []

  forbidden:
    - "Editar os logs históricos append-only ('Última atualização: ...', L170+) — descrevem estados corretos-para-a-época (repl_app.py existia em 222-228)"
    - "Reescrever a narrativa empírica datada de 2026-05-25 (FAIL=2 222-228) — registro histórico"
    - "Alterar os glifos canônicos U+25xx presentes no BRIEF (anti-sanitizer)"
    - "Forçar git add do BRIEF — está gitignored (.gitignore:83), é memória local do validador, e essa decisão é intencional"
    - "Tocar qualquer arquivo de código (sprint 100% documental)"

  tests:
    - cmd: "bash scripts/sprint_invariants.sh"
      timeout: 60
      deve_passar: true

  acceptance_criteria:
    - "Snippet de protocolo de regressão lista 6 arquivos existentes (sem repl_app.py) e EXECUTA sem crashar"
    - "Descrição de tipo reflete Textual (migrado de prompt_toolkit na ONDA-32)"
    - "Nota autoritativa pós-ONDA-32 presente; menções históricas a 7/5 arquivos e repl_app.py preservadas como registro"
    - "repl_app.py só permanece em contexto histórico (logs L170+ e narrativa datada) e na própria nota explicativa"
```

## 1. PROOF-OF-WORK (CONCLUIDA — 2026-05-30)

> **Nota:** `VALIDATOR_BRIEF.md` é **gitignored** (`.gitignore:83`) — memória local acumulada
> do `/validar-sprint`, intencionalmente fora do repo. O fix é aplicado no disco; o registro
> rastreável da sprint é este spec + a entrada no SPRINT_ORDER_MASTER.md.

**Realidade-fonte:** `scripts/sprint_invariants.sh` (~L263) já documenta:
`"TUI-DEFAULT-FLIP-LEGACY-RM-01 (ONDA-32): repl_app.py removido junto com toda stack
prompt_toolkit -- check do glifo nele saiu daqui."` O check #14 real protege **6 arquivos**:
cli.py, design_tokens.py, output.py, banner.py, design_tokens_extended.py, sprint_invariants.sh.

**Edições no BRIEF (instrucionais/forward-looking apenas):**
- L47 (tipo): `CLI/TUI baseado em prompt_toolkit + Rich` → `TUI baseado em Textual (migrado de
  prompt_toolkit na ONDA-32; widgets em nyx/agent/tui/) + Rich`; render layer ganha `nyx/agent/tui/`.
- Seção anti-sanitizer: nota autoritativa pós-ONDA-32 (7→6, repl_app.py removido) adicionada
  antes do protocolo; gatilho `...output ou repl_app` → `...banner ou output`.
- Snippet runnable: comentário `7 arquivos protegidos` → `6 arquivos protegidos`; `for f in`
  perde `nyx/agent/repl_app.py` (6 paths existentes restantes).
- Regra de diagnóstico L139: `7 arquivos protegidos` → `6 arquivos protegidos (pós-ONDA-32; ver nota)`.

**Preservado (histórico, NÃO tocado):** logs `Última atualização` (L170+) e a narrativa datada
2026-05-25 (FAIL=2 222-228, "5 arquivos ... repl_app.py") — corretos-para-a-época; a nota nova
os contextualiza.

**Validação:**
- **Protocolo de regressão corrigido EXECUTADO** (proof-of-work direto): passo 1 `OK chr presente`;
  passo 2 loop dos 6 arquivos → `OK` em todos, **sem FileNotFoundError** (antes, repl_app.py crashava).
- `bash scripts/sprint_invariants.sh`: 14/14 (FAIL=0).
- Acentuação do BRIEF: rc=1 pré-existente, isolado na L190 (log histórico append-only não tocado);
  nenhuma linha editada por esta sprint introduz ASCII-PT.
- Gauntlet: N/A — sprint 100% documental, zero código/runtime tocado.
