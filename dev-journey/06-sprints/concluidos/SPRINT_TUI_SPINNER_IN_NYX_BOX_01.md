# SPRINT 227 — TUI-SPINNER-IN-NYX-BOX-01

## 0. SPEC (machine-readable)

```yaml
sprint:
  id: TUI-SPINNER-IN-NYX-BOX-01
  title: "Spinner 'pensando...' renderiza dentro do balão da Nyx (não órfão)"
  onda: 31
  prioridade: MÉDIA
  tipo: Feature
  dependencias: [TUI-NYX-SOFT-BOX-01]
  desbloqueia: []

  touches:
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/agent/output.py
      reason: "NyxSpinner abre box top antes do spinner; primeira tokenização substitui"
      linhas_alvo: "340-417"
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/cli_callbacks.py
      reason: "on_token coordena substituição da linha do spinner pelo conteúdo real"
  creates: []
  removes: []

  forbidden:
    - "Mexer no spinner Braille frames (manter ADR-023 SPINNER_FRAMES)"
    - "Quebrar fallback ASCII (locale não-UTF8)"
    - "Marcar CONCLUIDA antes da S2 (TUI-NYX-SOFT-BOX-01) estar mergeada"
    - "Adicionar emoji"
    - "Mencao a IA proprietaria em codigo/commit"   # noqa-anonimato

  tests:
    - cmd: "./run.sh --smoke"
      timeout: 10
      deve_passar: true
    - cmd: "./run.sh --gauntlet --only rapido"
      timeout: 120
      deve_passar: true

  acceptance_criteria:
    - "'Pensando...' visível imediatamente após Enter, DENTRO do box roxo top"
    - "Spinner anima frames Braille sem cortar borda"
    - "Token streaming substitui linha do spinner suavemente"
    - "Sprint 224 TUI-NYX-SOFT-BOX-01 referenciada como dependência hard"
    - "Smoke boot ok + invariantes 14/14 PASS"
    - "Captura visual em momento 'pensando' mostra box roxo + spinner dentro"
```

---

# Sprint 227 — TUI-SPINNER-IN-NYX-BOX-01

**Status:** PENDENTE
**Data criação:** 2026-05-25
**Modelo obrigatório:** claude-opus-4-7 (sem subagentes)

---

## Contexto do projeto (snapshot)

> **ADRs relevantes:**
> - ADR-023 Design System Paleta D. ADR-027 Identidade Nyx.
>
> **Estado do sistema:**
> - `nyx/agent/output.py:340-417 NyxSpinner` é thread daemon que escreve `\r\x1b[2K  {frame}  {label}` no stderr.
> - Frames: Braille UTF-8 ou ASCII fallback (locale-aware).
> - Atualmente spinner aparece ANTES do `render_assistant_start` (header `◆ Nyx`).
> - Dependência hard: SPRINT 224 TUI-NYX-SOFT-BOX-01 introduz box roxo da Nyx.

---

## Problema

Spinner "pensando..." aparece sem container visual. Após a sprint 224 introduzir o balão roxo da Nyx, o spinner ainda fica órfão (antes do box, ou ignora completamente o box).

Feedback do usuário (2026-05-25): **"o pensando deveria aparecer no que seria o balão de texto da nyx"**.

### Sintoma observável

Imagem 1 do feedback mostra `pensando...` solto no meio da tela, com a tela do terminal anterior visível ao fundo.

---

## Solução proposta

`NyxSpinner.__enter__` abre o box top `╭─ Nyx ─╮` antes de iniciar o spinner. Spinner ocupa linha `│  {frame}  pensando…  │` (com padding mantendo borda). Quando primeiro token chega, `on_token` substitui essa linha via `\r\x1b[2K  │ {primeiro_token...} │` (sem fechar box).

Quando turno completo termina, `render_assistant_end` fecha box `╰─╯` (lógica da S2 224).

---

## Arquivos alvo

### `/home/andrefarias/Desenvolvimento/Nyx-Code/nyx/agent/output.py:340-417`

**Mudança em `NyxSpinner.__enter__`:**

1. Calcular `inner_w = max(label_len + 4, MIN_INNER_W)` (ex.: MIN_INNER_W=24).
2. Emitir top: `╭─ Nyx ─...─╮` em PURPLE.
3. Spinner thread agora escreve `\r\x1b[2K  │ {frame} {label} {pad} │` mantendo borda.
4. Sair do `__exit__` NÃO fecha box (responsabilidade da S2 `render_assistant_end`).

### `/home/andrefarias/Desenvolvimento/Nyx-Code/nyx/cli_callbacks.py`

**Mudança em `on_token`:**

Quando primeiro token chega: emite `\r\x1b[2K  │ {token} ... │` apagando a linha do spinner e iniciando o conteúdo dentro do box. Demais tokens seguem normalmente (sem ANSI \r — apenas append dentro do box).

---

## Diff esperado (resumo)

```
~ 2 arquivos modificados
+ ~40 linhas líquidas
```

---

## Comandos de verificação

```bash
# Smoke
./run.sh --smoke

# REPL interativo com captura no momento "pensando"
./run.sh
# Digitar mensagem que leva >1s:
#   "explique cli.py em poucas frases"
# Capturar durante "pensando":
sleep 0.5; import -window $(xdotool search --name './run.sh' | head -1) /tmp/spinner_in_box.png

# Capturar durante stream:
sleep 2; import -window $(xdotool search --name './run.sh' | head -1) /tmp/streaming_in_box.png

# Invariantes + gauntlet
bash scripts/sprint_invariants.sh
./run.sh --gauntlet --only rapido

# Acentuação
python3 ~/.config/zsh/scripts/validar-acentuacao.py --paths nyx/agent/output.py nyx/cli_callbacks.py
```

---

## Critério binário de aceite

- [ ] Sprint 224 TUI-NYX-SOFT-BOX-01 CONCLUIDA (dependência hard).
- [ ] Captura "pensando": box roxo + spinner dentro.
- [ ] Captura "streaming": box roxo + tokens substituindo a linha do spinner.
- [ ] Fallback ASCII para locale não-UTF8 mantido.
- [ ] Smoke + invariantes + gauntlet OK.
- [ ] Spec movida producao/ → concluidos/.

---

## Proof-of-work

```bash
bash scripts/sprint_invariants.sh > /tmp/inv_before.txt 2>&1
# Edit
bash scripts/sprint_invariants.sh > /tmp/inv_after.txt 2>&1
diff /tmp/inv_before.txt /tmp/inv_after.txt
ls /tmp/spinner_in_box.png /tmp/streaming_in_box.png
```

---

## Riscos

| Risco | Mitigação |
|---|---|
| Substituir linha do spinner por token sem flicker | `\r\x1b[2K` calibrado; testar terminal-by-terminal |
| Terminal sem suporte ANSI completo | Fallback plain (sem box, sem spinner avançado) |
| Aguarda S2 (224) — risco de implementação fora de ordem | Spec marca dependencia hard via `dependencias` |
| Largura do box vs largura do label "pensando..." | MIN_INNER_W=24 cobre todos os labels canônicos |

---

*"Container dá foco. Spinner dentro dele é loop visualizado." — princípio gamedesigner*
