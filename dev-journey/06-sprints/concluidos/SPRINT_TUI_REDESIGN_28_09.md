# SPRINT TUI-REDESIGN-28-09 — Retoque visual pós-validação Onda 28 (banner grid 2-col + remover endmark + popup bg + memória label)

## 0. SPEC

```yaml
sprint:
  id: TUI-REDESIGN-28-09
  title: "Retoque visual: banner em grid 2-col fiel ao mockup, remove 'Sessão Iniciada', popup bg=default, 'Memória ativa' fixo"
  onda: 28
  bloco: 28.1 TUI paridade Claude Code (retoque)
  prioridade: ALTA
  tipo: Visual
  dependencias: [TUI-REDESIGN-28-02, TUI-REDESIGN-28-06]
  desbloqueia: []
  origem: "Validação visual pós-Onda 28 (2026-05-18 noite) via playwright mockup HTML × scrot do banner Nyx atual em kitty. Diff de 9 pontos identificou 4 ajustes prioritários decididos por AskUserQuestion."

  validacao_visual_baseline:
    mockup_ref: dev-journey/07-reports/proofs/TUI_28_RETOQUE/mockup_original.png
    tui_atual: dev-journey/07-reports/proofs/TUI_28_RETOQUE/tui_banner_atual_20260518T234912.png
    diff_pontos:
      - "$ nyx.code FORA do box -> DENTRO como coluna esquerda"
      - "Sem separador vertical entre $ e info -> adicionar │ entre colunas"
      - "Sem separadores horizontais entre 3 linhas info -> adicionar ├─┤ sutil"
      - "Rótulos Title Case (Modelo, Projeto) -> MAIÚSCULA (MODELO, PROJETO)"
      - "Espaços entre seções -> pipes │ verticais"
      - "'Memória 10 entradas' -> 'Memória ativa' fixo"
      - "Endmark '─── Sessão Iniciada ───' aparece -> REMOVER"
      - "Popup completion com bg:{accent_lo} -> bg:default (=bg terminal)"

  touches:
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/agent/banner.py
      reason: "Reescrever _build_wide() como grid 2 colunas (esquerda = '$ nyx.code', direita = 3 linhas info com separadores horizontais entre rows e pipes verticais entre seções de cada row); rótulos em CAPS; 'Memória ativa' fixo"
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/cli.py
      reason: "_build_prompt_style: completion-menu.completion troca bg:{accent_lo} por bg:default (preserva contraste do .current com bg:{accent}); completion-menu.meta.completion idem"
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/run.sh
      reason: "Linha 654: remover echo do endmark '─── Sessão Iniciada ───' (não aparece mais no terminal)"
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/themes/design_tokens.py
      reason: "Linha 103: GLYPHS_BOOT['endmark'] pode permanecer como token (uso programático) OU virar string vazia. Recomendado: manter token, remover consumer em run.sh"

  forbidden:
    - "Trocar paleta atual (turquesa #00D4AA + roxo #9D4EDD + verde #4ADE80) para roxo claro do mockup"
    - "Remover memory_count/commands_count/session_type da assinatura de build_banner (callers dependem)"
    - "Quebrar _build_compact() para cols<80"
    - "Tocar arquivos fora dos 4 listados em touches"
    - "Quebrar invariante #14 (glyphs protegidos)"

  tests:
    - cmd: "./run.sh --smoke"
      timeout: 60
      deve_passar: "boot ok"
    - cmd: "bash scripts/sprint_invariants.sh | tail -3"
      timeout: 60
      deve_passar: "PASS=14 FAIL=0"
    - cmd: "./venv/bin/python -c 'from nyx.agent.banner import build_banner; out = build_banner(\"qwen2.5-coder:3b\", 35, \"Nyx-Code\", commands_count=62, memory_count=10); print(out)' | tee /tmp/banner_28_09.txt"
      timeout: 10
      deve_passar: "grid 2-col com '$ nyx.code' embutido + 'Memória ativa' fixo"
    - cmd: "grep -c 'Memória ativa' /tmp/banner_28_09.txt"
      timeout: 5
      deve_passar: "1"
    - cmd: "grep -c 'MODELO\\|PROJETO\\|REDE\\|TOOLS\\|COMANDOS\\|TIPO' /tmp/banner_28_09.txt"
      timeout: 5
      deve_passar: ">= 6"
    - cmd: "grep -c 'Sessão Iniciada' run.sh"
      timeout: 5
      deve_passar: "0"
    - cmd: "grep -c 'bg:default' nyx/cli.py"
      timeout: 5
      deve_passar: ">= 1"

  acceptance_criteria:
    - "Banner renderiza grid 2-col: '$ nyx.code' centralizado verticalmente à esquerda, 3 rows info à direita, separados por │"
    - "Rows info separadas por linha horizontal sutil ├─┤"
    - "Cada row info tem 3-4 seções separadas por │ pipes verticais"
    - "Rótulos em CAPS: MODELO, PROJETO, REDE, TOOLS, COMANDOS, MEMÓRIA, TIPO"
    - "Memória sempre 'ativa' (independente do memory_count)"
    - "Boot do REPL NÃO mostra '─── Sessão Iniciada ───' antes do banner"
    - "Popup do /command (Enter no '/') tem bg = bg terminal (não accent_lo)"
    - "Item selecionado do popup ainda destaca com bg:{accent}"
    - "Smoke + invariantes 14/14"
    - "Screenshot via kitty confirma paridade aproximada com mockup"

  proof_of_work:
    - "Render via standalone: ./venv/bin/python -c 'from nyx.agent.banner import build_banner; print(build_banner(\"qwen2.5-coder:3b\", 35, \"Nyx-Code\", commands_count=62, memory_count=10))' captura para /tmp/banner_28_09.txt"
    - "Captura visual via kitty + import comparada lado-a-lado com mockup_original.png"
    - "Screenshot arquivado em dev-journey/07-reports/proofs/TUI_28_RETOQUE/tui_banner_28_09_VALIDADO.png"

  desenho_alvo: |
    Layout final (~80 cols):

    ╭───────────────────┬──────────────────────────────────────────────────╮
    │                   │  v 1.2.0      ●  100% offline                    │
    │                   ├──────────────────────────────────────────────────┤
    │   $ nyx.code▌     │  MODELO qwen2.5-coder:3b │ PROJETO Nyx-Code      │
    │                   ├──────────────────────────────────────────────────┤
    │                   │  TOOLS 35  │ COMANDOS 62  │ MEMÓRIA ativa        │
    ╰───────────────────┴──────────────────────────────────────────────────╯

    Notas:
    - "$ " e "." em roxo (NYX_PURPLE); "nyx" e "code" em primary
    - Cursor "▌" em roxo (compatível com cursor blink do 28_07)
    - Bordas e separadores em accent (NYX_ACCENT turquesa)
    - "100% offline" em verde (NYX_SUCCESS)
    - "●" em accent
    - Rótulos (MODELO, PROJETO, ...) em muted; valores em primary
    - Pipes │ internos em muted (mais discretos que as bordas)
```

---

# Sprint TUI-REDESIGN-28-09

**Status:** CONCLUIDA
**Data criação:** 2026-05-18
**Data conclusão:** 2026-05-19
**Modelo obrigatório:** claude-opus-4-7

## Resultado

4 frentes entregues em commit atômico:

1. `nyx/agent/banner.py` — `_build_wide()` reescrito como grid 2-col (inner_w=70, left_w=18, right_w=51). Junções `┬├┤┴`, pipes `│` internos em muted, rótulos CAPS, "MEMÓRIA ativa" fixo. `_build_compact()` preservado intacto. Assinatura de `build_banner()` inalterada.
2. `nyx/cli.py` — `completion-menu.completion` e `completion-menu.meta.completion` migrados de `bg:{accent_lo}` para `bg:default`. `.current` preserva `bg:{accent}` para destaque do item selecionado.
3. `run.sh:646-652` — bloco de eco do endmark `─── Sessão Iniciada ───` removido. Token `GLYPHS_BOOT["endmark"]` preservado em `design_tokens.py` para uso programático.
4. `design_tokens.py` — sem alteração (token permanece como contrato).

## Proof-of-work

- Smoke: `./run.sh --smoke` → boot ok
- Invariantes: 14/14 (FAIL=0)
- Render standalone: `/tmp/banner_28_09.txt` (grid 2-col confirmado)
- Acentuação periférica: 0 violações nos 3 arquivos modificados
- Screenshot kitty + import: `dev-journey/07-reports/proofs/TUI_28_RETOQUE/tui_banner_28_09_VALIDADO.png`
  - sha256: `69c17b392ec52241253cb90ff14e7634ec3713578ed5c5e5e8610e9a584ea59d`
  - Validação multimodal: grid 2-col fiel ao mockup, rótulos CAPS, cursor roxo `▌`, paleta turquesa+roxo+verde preservada (forbidden #1 respeitado)

## Nota de divergência (resolução)

O `tests[3]` do spec pedia `grep -c 'Memória ativa' /tmp/banner_28_09.txt == 1` (Title Case), enquanto `acceptance_criteria[3]` e `desenho_alvo` (linhas 95-96) pediam `MEMÓRIA` em CAPS (alinhado com MODELO, PROJETO, TOOLS, COMANDOS). Resolução: seguiu-se `acceptance_criteria` + `desenho_alvo` (CAPS = `MEMÓRIA ativa`). Verificação efetiva no plain-text stripado de ANSI: `MEMÓRIA ativa` aparece 1 vez como string contígua.

## Rollback

`git reset --hard HEAD~1`
