# SPRINT 292 — TUI-OUTPUT-CAPITALIZATION-AUDIT-01

## 0. SPEC

```yaml
sprint:
  id: TUI-OUTPUT-CAPITALIZATION-AUDIT-01
  title: "Auditar nyx/agent/output.py::render_footer (achado da SPRINT 287): confirmar se o footer legado precisa da mesma capitalização Ctx/Iter/Lidos/Modif aplicada à toolbar Textual viva, e resolver o achado"
  onda: 34
  prioridade: BAIXA
  tipo: Infra/Auditoria
  dependencias: [TUI-FOOTER-CAPITALIZATION-01]
  desbloqueia: []

  origem: "Achado colateral da SPRINT 287 (TUI-FOOTER-CAPITALIZATION-01): ao capitalizar os labels da toolbar Textual viva (Ctx/Iter/Lidos/Modif), o validador notou que output.py::render_footer renderiza um footer equivalente com labels minúsculos (ctx/iter/lidos/modif) — questão: precisa do mesmo tratamento?"

  touches:
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/agent/output.py
      reason: "Marcar render_footer (docstring) como LEGADO/MORTO, documentando a conclusão da auditoria; nenhuma mudança em código executável."
  creates: []
  removes: []

  forbidden:
    - "Deletar render_footer — GUIDE #3: código morto se menciona, não se deleta"
    - "Capitalizar os labels minúsculos de render_footer — GUIDE #2: função sem chamador é cenário impossível; capitalizar seria polir o inacessível"
    - "Tocar a toolbar viva (toolbar.py) — já capitalizada na 287"
    - "Tocar qualquer outro arquivo além de output.py"
    - "Expandir o escopo para as outras render_* órfãs — registradas como sprint própria (anti-débito)"

  tests:
    - cmd: "./run.sh --smoke"
      timeout: 15
      deve_passar: true
    - cmd: "bash scripts/sprint_invariants.sh"
      timeout: 60
      deve_passar: true

  acceptance_criteria:
    - "render_footer documentado como [LEGADO/MORTO — zero chamadores], superado por toolbar.py (ONDA-32)"
    - "Conclusão registrada na docstring: labels minúsculos são user-invisíveis (sem chamador) → NÃO recebem capitalização da 287"
    - "py_compile output.py OK; nenhuma mudança em código executável"
    - "Achado das demais render_* órfãs registrado como sprint PENDENTE separada"
```

## 1. AUDITORIA (CONCLUIDA — 2026-05-30)

**Símbolo auditado:** `nyx/agent/output.py::render_footer` (def linha 1288).

**Evidência de deadness:**
- `grep -rn "render_footer" nyx/ --include="*.py" | grep -v "def render_footer"` → **zero** ocorrências.
- Sem `__all__`, `getattr(`, `globals()[` em output.py → sem despacho dinâmico.
- É o footer 1-linha do REPL `prompt_toolkit` pré-Textual; substituído pelo widget
  Textual `agent/tui/widgets/toolbar.py` na migração ONDA-32.

**Conclusão:** código morto. Labels minúsculos (`ctx/iter/lidos/modif`) são
user-invisíveis pois a função nunca é chamada → **NÃO** recebem a capitalização
Ctx/Iter/Lidos/Modif aplicada à toolbar viva na SPRINT 287. Por GUIDE #3 a função
**não é deletada**: foi marcada como `[LEGADO/MORTO — zero chamadores]` na docstring,
explicando o veredito para futuros leitores (evita que alguém "conserte" os labels
minúsculos re-descobrindo o mesmo código morto).

**Achado colateral (anti-débito):** a auditoria-irmã das demais `render_*`/`print_*`
de output.py revelou **mais 5 funções de módulo com zero chamadores**:
`render_progress_bar`, `render_tool_card_start`, `render_todo_block`,
`render_tool_card_end`, `render_diff` (todas pré-Textual). NÃO tratadas aqui (fora do
escopo do achado 287, que é só render_footer); registradas como sprint PENDENTE
**INFRA-OUTPUT-DEAD-RENDER-CLUSTER-01** no SPRINT_ORDER_MASTER.md.

**Validação:**
- `python3 -m py_compile nyx/agent/output.py`: OK.
- `validar-acentuacao.py --paths nyx/agent/output.py`: rc 0.
- `git diff`: só docstring de render_footer (zero código executável).
- `./run.sh --smoke`: boot OK.
- `bash scripts/sprint_invariants.sh`: 14/14 (FAIL=0).
- `./run.sh --gauntlet --only rapido`: APROVADO (comportamento inalterado — diff é só docstring).
