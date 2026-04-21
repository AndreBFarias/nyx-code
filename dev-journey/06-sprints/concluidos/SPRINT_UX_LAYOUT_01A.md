# SPRINT UX-LAYOUT-01A — Banner repaginado (BOX_CHARS + design_tokens + modo compacto)

## 0. SPEC (machine-readable)

```yaml
sprint:
  id: UX-LAYOUT-01A
  title: "_build_banner reescrito consumindo BOX_CHARS e cores de design_tokens, com modo compacto para colunas<80"
  onda: 22
  bloco: 4
  prioridade: ALTA
  tipo: Feature
  dependencias: [UX-DESIGN-01]
  desbloqueia: [UX-LAYOUT-01B]

  touches:
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/cli.py
      reason: "Reescrever _build_banner consumindo design_tokens (BOX_CHARS, cores) e adicionar modo compacto cols<80"

  creates: []
  removes: []

  n_to_n_pairs:
    - descricao: "BOX_CHARS e cores só existem em design_tokens.py — _build_banner consome, nunca redefine"
      paths:
        - /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/themes/design_tokens.py
        - /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/cli.py

  forbidden:
    - "Hex hardcoded em cli.py (vem de design_tokens)"
    - "Adicionar emoji"
    - "Usar 'print()' em modules novos (permitido apenas em cli.py e agent/output.py — ADR-024)"
    - "Menção a Claude/GPT/Anthropic"
    - "Tocar em _bottom_toolbar (escopo de UX-LAYOUT-01B)"
    - "Tocar em render_user_input (paste — migrou para TUI-FIX-07B)"
    - "Quebrar modo estreito (cols<60 deve continuar legível)"

  tests:
    - cmd: "python -c 'from nyx.cli import _build_banner; print(_build_banner(\"qwen3:4b\", 35, \"Nyx-Code\"))'"
      timeout: 30
      deve_passar: true
    - cmd: "./run.sh --gauntlet --only tui"
      timeout: 300
      deve_passar: true
    - cmd: "./run.sh --smoke"
      timeout: 60
      deve_passar: true

  acceptance_criteria:
    - "_build_banner consome BOX_CHARS de design_tokens (╭ ╮ ╰ ╯ ─ │) — renderiza caixa fechada"
    - "Zero hex hardcoded em cli.py (grep '#[0-9A-Fa-f]{6}' em cli.py retorna 0)"
    - "Modo estreito: cols<80 renderiza banner compacto 2-3 linhas; mantém informação essencial (modelo, projeto, rede)"
    - "Modo amplo: cols>=80 renderiza banner completo com linhas de modelo/projeto/rede/memória"
    - "Banner renderiza sem exceção para cols=40, 80, 120 (test harness)"
    - "Gauntlet fase tui passa 100%"
    - "./run.sh --smoke continua PASS"
    - "Acentuação PT-BR correta em tudo novo"
```

---

# Sprint UX-LAYOUT-01A — Banner repaginado

**Status:** CONCLUIDA (commit af0a901)
**Data criação:** 2026-04-19
**Origem:** split de UX-LAYOUT-01 (banner + toolbar + paste) em 2 sprints. Este arquivo cobre **apenas banner**. Toolbar migrou para UX-LAYOUT-01B. Colapso de paste migrou para TUI-FIX-07B.
**Modelo obrigatório:** claude-opus-4-7 (sem subagentes)

---

## Contexto

> ADRs: 001, 004, 005, 006, 013, 014, 020, 023 (design_tokens com BOX_CHARS, NYX_ACCENT, NYX_MUTED, NYX_PURPLE), 024. Python 3.10+, qwen3:4b em 11435, proxy 11436; 34 tools, 47 commands, 10 services. UX-DESIGN-01 CONCLUIDA. UX-LAYOUT-01 original absorvido por UX-LAYOUT-01A (este) e UX-LAYOUT-01B.

---

## Problema

`_build_banner` em `nyx/cli.py` atualmente:

1. Usa hex hardcoded (`#8a2be2`, `#7f7f7f`, etc.) — viola ADR-023.
2. Usa caracteres de caixa soltos, inconsistentes com `BOX_CHARS` canônicos.
3. Não tem modo compacto: em terminais estreitos (cols<80) o banner quebra feio, vai para múltiplas linhas com box desalinhada.

Modelo visual desejado (amplo):

```
  ╭─ Nyx · v1.2.0 ──────────────────────────────── 100% offline ─╮
  │                                                              │
  │   modelo    qwen3:4b          visão    moondream  (cold)     │
  │   projeto   Nyx-Code          tools    35                    │
  │   rede      :11435 ollama  ·  :11436 proxy                   │
  │   memória   3 entradas                                       │
  │                                                              │
  ╰── /help para comandos · Ctrl+D para sair ────────────────────╯
```

Modelo visual desejado (compacto, cols<80):

```
  ╭─ Nyx · qwen3:4b · Nyx-Code ─╮
  │   :11435 ollama · :11436 proxy
  ╰─ /help · Ctrl+D ────────────╯
```

---

## Solução proposta

- Reescrever `_build_banner(model: str, n_tools: int, project: str) -> str` em `cli.py`.
- Consumir `BOX_CHARS`, `NYX_ACCENT`, `NYX_MUTED` de `nyx.themes.design_tokens`.
- Detectar largura via `shutil.get_terminal_size(fallback=(80, 24)).columns` (ou parâmetro `cols`).
- Retornar string única (não chamar `print` dentro da função — `cli.py` imprime onde for apropriado).

---

## Arquivos alvo (paths absolutos)

### `/home/andrefarias/Desenvolvimento/Nyx-Code/nyx/cli.py`

**Antes (conceitual):**
```python
def _build_banner(model: str, n_tools: int, project: str) -> str:
    purple = "\x1b[38;2;138;43;226m"
    reset = "\x1b[0m"
    # monta linhas com hex hardcoded e caracteres ad-hoc
    return ...
```

**Depois:**
```python
def _build_banner(model: str, n_tools: int, project: str, cols: int | None = None) -> str:
    import shutil
    from nyx.themes.design_tokens import BOX_CHARS, NYX_ACCENT, NYX_MUTED, ANSI_RESET, ansi_fg

    if cols is None:
        cols = shutil.get_terminal_size(fallback=(80, 24)).columns

    tl, tr, bl, br = BOX_CHARS["tl"], BOX_CHARS["tr"], BOX_CHARS["bl"], BOX_CHARS["br"]
    h, v = BOX_CHARS["h"], BOX_CHARS["v"]
    accent = ansi_fg(NYX_ACCENT)
    muted = ansi_fg(NYX_MUTED)

    if cols < 80:
        linha1 = f"  {accent}{tl}{h} Nyx · {model} · {project} {h}{tr}{ANSI_RESET}"
        linha2 = f"  {accent}{v}{ANSI_RESET}   {muted}:11435 ollama · :11436 proxy{ANSI_RESET}"
        linha3 = f"  {accent}{bl}{h} {muted}/help · Ctrl+D{accent} {h*14}{br}{ANSI_RESET}"
        return "\n".join([linha1, linha2, linha3])

    largura_interna = cols - 4
    topo = f"  {accent}{tl}{h*2} Nyx · v1.2.0 {h*(largura_interna - 32)} 100% offline {h}{tr}{ANSI_RESET}"
    vazio = f"  {accent}{v}{' '*(largura_interna)}{v}{ANSI_RESET}"
    linha_modelo = f"  {accent}{v}{ANSI_RESET}   modelo    {model:<15} visão    moondream  (cold)".ljust(cols - 1) + f"{accent}{v}{ANSI_RESET}"
    linha_projeto = f"  {accent}{v}{ANSI_RESET}   projeto   {project:<15} tools    {n_tools}".ljust(cols - 1) + f"{accent}{v}{ANSI_RESET}"
    linha_rede = f"  {accent}{v}{ANSI_RESET}   rede      :11435 ollama  ·  :11436 proxy".ljust(cols - 1) + f"{accent}{v}{ANSI_RESET}"
    base = f"  {accent}{bl}{h*2} {muted}/help para comandos · Ctrl+D para sair{accent} {h*(largura_interna - 44)}{br}{ANSI_RESET}"

    return "\n".join([topo, vazio, linha_modelo, linha_projeto, linha_rede, vazio, base])
```

**Mudanças:**
- Importa `BOX_CHARS`, cores e `ansi_fg` de `design_tokens` — zero hex literal na função.
- Detecção de largura com fallback seguro.
- Dois modos (compacto e amplo).
- Retorna string; não imprime.

Se `ansi_fg` ainda não existir em `design_tokens.py`, documentar no relatório e usar diretamente os códigos disponibilizados pelos tokens (paleta D). Nunca introduzir hex novo em `cli.py`.

---

## Diff esperado (resumo)

```
+ 0 arquivos criados
~ 1 arquivo modificado
- 0 arquivos removidos
+ ~45 linhas líquidas (reescrita da função)
```

---

## Comandos de verificação (literais, copy-paste)

```bash
cd /home/andrefarias/Desenvolvimento/Nyx-Code

# 1. Validação estática
python -m ruff check nyx/cli.py

# 2. Zero hex em cli.py
grep -nE '#[0-9A-Fa-f]{6}' nyx/cli.py
# Esperado: zero matches

# 3. Banner importável, cols variáveis
python -c "
from nyx.cli import _build_banner
for cols in (40, 60, 80, 120, 160):
    out = _build_banner('qwen3:4b', 35, 'Nyx-Code', cols=cols)
    assert '╭' in out and '╰' in out, f'falhou em cols={cols}'
    assert 'Nyx' in out and 'qwen3:4b' in out, f'info faltando em cols={cols}'
    print(f'cols={cols}: OK')
"

# 4. Gauntlet
./run.sh --gauntlet --only tui

# 5. Smoke
./run.sh --smoke

# 6. Validação visual
./run.sh
# Esperado: banner renderiza com BOX_CHARS completos, sem '?' ou '[' soltos.
# Reduzir o terminal para < 80 cols e reexecutar: banner compacto aparece.
```

---

## Critério binário de aceite (IA executora)

- [ ] `_build_banner` consome `BOX_CHARS` e cores de `design_tokens` — zero hex em `cli.py`
- [ ] Modo compacto (cols<80) renderiza 2-3 linhas legíveis
- [ ] Modo amplo (cols>=80) renderiza o banner completo (modelo, projeto, rede, memória, rodapé)
- [ ] Função testada para cols=40, 60, 80, 120, 160 sem exceção
- [ ] Gauntlet `--only tui` passa 100%
- [ ] `./run.sh --smoke` continua PASS
- [ ] `ruff` não reclama
- [ ] Nenhuma violação de `forbidden[]`
- [ ] `SPRINT_ORDER_MASTER.md` atualizado com hash
- [ ] Sprint movida para `concluidos/`
- [ ] Commit atômico criado

---

## Guardrails anti-engodo

Não marcar CONCLUIDA se houver hex em `cli.py`; se modo compacto for stub (`if cols<80: pass`); se mexeu em `_bottom_toolbar`/`render_user_input`; se só testou cols=120; se criou constantes de cor redundantes. Reportar `[SPRINT UX-LAYOUT-01A] BLOQUEADA: <motivo>` em falha.

---

## Gambiarras específicas

1. **Hex redefinido localmente.** Criar `_PURPLE = "#8a2be2"` em `cli.py` porque é "mais rápido". Proibido — design_tokens é a fonte única.
2. **Modo compacto stub.** `if cols < 80: return "Nyx"` literal. Proibido — precisa mostrar pelo menos modelo, projeto e portas.
3. **Caracteres de caixa soltos.** Usar `+`, `-`, `|` em vez de `BOX_CHARS`. Proibido — inconsistente com o design system.
4. **Mexer em toolbar/paste.** Fora de escopo (UX-LAYOUT-01B e TUI-FIX-07B).
5. **Criar bloco `ansi_fg` inline.** Se ausente em `design_tokens`, documentar e usar códigos de tokens existentes — não duplicar implementação no cli.py.

---

## Proof-of-work obrigatório (4 passos)

```bash
# PASSO 1 — ANTES
bash scripts/sprint_invariants.sh > /tmp/inv_before.txt 2>&1
FAIL_BEFORE=$(grep -c "^\[FAIL\]" /tmp/inv_before.txt)

# PASSO 2 — implementação

# PASSO 3 — DEPOIS
bash scripts/sprint_invariants.sh > /tmp/inv_after.txt 2>&1
FAIL_AFTER=$(grep -c "^\[FAIL\]" /tmp/inv_after.txt)

# PASSO 4 — FAIL_AFTER <= FAIL_BEFORE; diff colado
```

Colar no relatório: `tail -10` de cada snapshot, `diff`, output literal do test harness (cols=40,60,80,120,160), gauntlet tui, `git show --stat HEAD`. Incluir screenshot (ou descrição textual do output bruto) dos dois modos.

---

## Validação humana (checklist do usuário)

```bash
cd /home/andrefarias/Desenvolvimento/Nyx-Code
git log --oneline -1
git show --stat HEAD

./run.sh
# 1. Banner aparece com BOX_CHARS completos.
# 2. Redimensionar terminal para <80 cols e reexecutar — banner compacto.
# 3. Ctrl+D.

ls dev-journey/06-sprints/concluidos/SPRINT_UX_LAYOUT_01A.md
ls dev-journey/06-sprints/producao/SPRINT_UX_LAYOUT_01A.md  # NÃO deve existir
```

---

## Riscos

| Risco | Mitigação |
|-------|-----------|
| `BOX_CHARS` com nome de chave diferente do assumido (`tl`, `tr`, `bl`, `br`, `h`, `v`) | Conferir `design_tokens.py` antes; se chaves diferirem, adaptar — nunca redefinir |
| Terminal sem suporte a UTF-8 quebra box | TUI-FIX-07A cuida de spinner ASCII; banner pode ser revisitado em sprint futura se necessário — documentar no relatório |
| Cálculo de largura não fecha (off-by-one) | Test harness com múltiplos cols cobre o caso; validar visualmente cols=80 exato |
| Modo compacto corta informação essencial | Manter mínimo: modelo, projeto, portas, atalho |

---

*"A forma segue a função." -- Louis Sullivan*
