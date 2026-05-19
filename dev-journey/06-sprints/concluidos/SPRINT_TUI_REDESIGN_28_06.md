# SPRINT TUI-REDESIGN-28-06 — Banner novo ("$ nyx.code" block ASCII + grid info)

## 0. SPEC

```yaml
sprint:
  id: TUI-REDESIGN-28-06
  title: "Banner de boot vira block ASCII '$nyx.code' + box info 3 linhas (v, offline verde, modelo, projeto, rede, tools, comandos, memória, tipo) com paleta turquesa+roxo+verde"
  onda: 28
  bloco: 28.1 TUI paridade Claude Code
  prioridade: ALTA
  tipo: Visual
  dependencias: [TUI-REDESIGN-28-02]
  desbloqueia: [TUI-REDESIGN-28-07]
  origem: "Mockup novo_banner_ao_iniciar.html + sketch do usuário 2026-05-18 (banner block '$nyx.code' com cursor piscante). PALETA: mantém turquesa #00D4AA + roxo #9D4EDD + verde #4ADE80 (NYX_SUCCESS para '100% offline'). NÃO migra para roxo claro do mockup."

  touches:
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/agent/banner.py
      reason: "Reescrever _build_wide() com: linha 1 vazia + bloco '$ nyx.code▌' (linhas 2-4 simulando block ASCII com underline) + box ╭─...─╮ com 3 linhas de info; preservar _build_compact() simplificado"

  forbidden:
    - "Trocar paleta para roxo claro do mockup (#9b87ff/#c8b4ff) — manter turquesa+roxo+verde da paleta atual"
    - "Remover memory_count/commands_count/session_type da assinatura (callers existentes em cli.py dependem)"
    - "Adicionar emoji ou glyph fora dos permitidos (ADR-004)"

  tests:
    - cmd: "./run.sh --smoke"
      timeout: 60
      deve_passar: "boot ok"
    - cmd: "bash scripts/sprint_invariants.sh | tail -3"
      timeout: 60
      deve_passar: "PASS=14 FAIL=0"
    - cmd: "./venv/bin/python -c 'from nyx.agent.banner import build_banner; print(build_banner(\"qwen2.5-coder:3b\", 35, \"Nyx-Code\"))' | grep -c 'nyx.code'"
      timeout: 10
      deve_passar: ">= 1"
    - cmd: "./venv/bin/python -c 'from nyx.agent.banner import build_banner; print(build_banner(\"qwen2.5-coder:3b\", 35, \"Nyx-Code\"))' | grep -c '100% offline'"
      timeout: 10
      deve_passar: ">= 1"

  acceptance_criteria:
    - "Banner cols>=80: 'block $nyx.code' com '$ ' roxo, 'nyx' primary, '.' roxo, 'code' primary, cursor '▌' roxo"
    - "Box 3 linhas: linha 1 'v1.2.0 ● 100% offline' (● accent, '100% offline' verde NYX_SUCCESS); linha 2 'Modelo X | Projeto Y | Rede :p1/:p2'; linha 3 'Tools N | Comandos M | Memória ativa | Tipo REPL'"
    - "Box usa caracteres ╭─╮│╰╯ accent"
    - "Banner cols<80: versão compact preservada"
    - "Screenshot via 'import -window' confirma layout"
    - "Smoke + invariantes ok"

  proof_of_work:
    - "./venv/bin/python -c 'from nyx.agent.banner import build_banner; out = build_banner(\"qwen2.5-coder:3b\", 35, \"Nyx-Code\"); print(out)' | tee /tmp/banner_28_06.txt"
    - "Verificar /tmp/banner_28_06.txt contém: '$ nyx.code', '100% offline' (esverdeado por ANSI 24-bit), '╭', '│', '╰'"
    - "Screenshot do REPL boot via xdotool+import e arquivar em dev-journey/07-reports/proofs/TUI_28_06/"
```

---

# Sprint TUI-REDESIGN-28-06

**Status:** CONCLUIDA
**Data criação:** 2026-05-18
**Data conclusão:** 2026-05-18
**Modelo obrigatório:** claude-opus-4-7

## Proof-of-work

- Reescrita cirúrgica de `_build_wide()` e `_build_compact()` em `nyx/agent/banner.py`.
- Imports adicionados: `ANSI_PURPLE_FG`, `ANSI_PRIMARY_FG`, `ANSI_SUCCESS_FG` (escopo permitido pelo BRIEF — todos vindos de `nyx.themes.design_tokens`).
- Assinatura de `build_banner()` preservada (callers em `nyx/cli.py:522` intactos).
- Layout wide (cols >= 80): block `$ nyx.code▌` + box `╭─╮│╰╯` com 3 linhas info, largura interna fixa de 66 chars, ports compactados como `:porta1/:porta2` dentro do box.
- Paleta turquesa+roxo+verde preservada (não migrou para `#c8b4ff/#9b87ff` do mockup).
- Render via `./venv/bin/python -c 'from nyx.agent.banner import build_banner; print(build_banner(...))'` em `/tmp/banner_28_06.txt`.
- Visual confirmado em screenshot real do kitty: `/tmp/nyx_tui_banner_28_06_20260518T231443.png` (sha256: `c9a53311eb9ba2e9c182e79f4c5ffc1571f7f781069b7f60d6d21dcda0efcc31`).
- Smoke `./run.sh --smoke` -> boot ok.
- `bash scripts/sprint_invariants.sh` -> PASS 14 / FAIL 0.

## Rollback

`git reset --hard HEAD~1`
