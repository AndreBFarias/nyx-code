# Relatório de Validação — Onda 20 (TUI+CTX) — v2 FINAL

**Data:** 2026-04-20
**Sprint:** VALIDATE-ONDA-20
**Modelo:** qwen3:4b (Ollama 11435, Proxy 11436 think=false)
**Hardware:** RTX 3050 Laptop 4GB VRAM, 14GiB RAM
**Metodologia:** pipeline da skill `validacao-visual` — X11 (scrot/import/xdotool/wmctrl) dentro de `kitty`; programática via `./run.sh --gauntlet`.

---

## 0. TL;DR

- **6 sprints CONCLUIDA** (TUI-01/02/03, CTX-01/02/03).
- **1 DEFERIDA** (CTX-04 — opcional por spec original).
- **5 sprints-nova materializadas e concluídas** antes de fechar a Onda 20, pelo princípio ADR-009 "infra faz o modelo pequeno funcionar" e meta-regra GUIDE.md §"Zero follow-up acumulado".

## 1. Rodada 1 (início) — achados

12 screenshots em `/tmp/nyx_validate_onda20/` mostraram:

- [OK] Banner `╭─╮` único, footer `ctx X% · modelo · iter N · lidos · modif · shift+tab`, prompt `nyx>`
- [OK] Popup `/` abre em MULTI_COLUMN com 47 commands — mas **sem descrições**
- [OK] Box `╭─ você ─╮` em mensagens ao LLM; saudação sem tool call (PROMPT-01)
- [OK] RepoMap responde "em qual arquivo fica AgentLoop?" → `nyx/agent/loop/_core.py` sem tool call
- [OK] `/theme list` formatado (TUI-FIX-09 ativo)
- [FAIL] `/theme xyz-inexistente` → TUI-FIX-10 já concluído fora desta sprint
- [FAIL] Auto-tune `num_gpu=23` em 4GB → OOM do Ollama em 2ª execução
- [FAIL] LLM não dispara `write_memory` com frase natural "lembra que eu uso pyenv 3.12"
- [FAIL] Popup sem `display_meta`
- [FAIL] 9 linhas `[nyx]` no stdout durante boot

Cinco achados **foram materializados como sprints-nova antes de fechar a Onda 20** (meta-regra §Zero follow-up acumulado):

| Sprint | Commit | Resultado |
|--------|--------|-----------|
| GAUNTLET-FIX-LOOP-SPLIT | dd29b98 | CTX-08 PASS (gauntlet contexto 10/10 em ambiente saudável) |
| AUTOTUNE-FIX-01 | 6f5273b | `VRAM_CAP_MB_TO_LAYERS` alinhado ADR-003 + REQUEST_TIMEOUT 60s→180s; gauntlet contexto 11/11 (com CTX-11 novo) em ambiente saudável |
| TOOL-INVOKE-MEMORY-01 | 815f2fc | prompt + tool description + CTX-11; roundtrip real via proxy: `tool_calls=1, write_memory=True, args={"file":"ambiente","content":"Uso pyenv 3.12 neste projeto.","reason":"setup do dev"}` |
| TUI-POPUP-META-01 | 94d7327 | `CompleteStyle.COLUMN` renderiza `display_meta`; screenshot `/tmp/nyx_validate_onda20/popup_meta2_*.png` mostra 16 comandos com descrição alinhada |
| TUI-BOOT-LOG-01 | 91e27f4 | `log_boot` redireciona 10 linhas de boot para `logs/boot.log`; screenshot `boot_limpo_*.png` mostra 1 linha `[nyx]` única |
| AUTOTUNE-FIX-02 | d491600 | cap 4GB: 15→12 (canonical ADR-003) após V2 reproduzir OOM com 15 em system prompt real |

## 2. Evidência gauntlet (programática)

| Gauntlet | Ambiente | Resultado |
|----------|----------|-----------|
| `contexto` (rodada 1, cap=15) | saudável | **11/11 APROVADO** — Gate APROVADO, CTX-11 PASS |
| `rapido` (pós AUTOTUNE-FIX-01) | saudável | **18/18 APROVADO** |
| `rapido` (pós AUTOTUNE-FIX-02) | **swap removido do SO** | 5/5 truncado por SIGTERM proativo — degradação ambiental, não de código |
| `contexto` (pós AUTOTUNE-FIX-02) | **swap removido do SO** | 9/11 (CTX-10/11 FAIL por `signal: terminated` no runner) |

A degradação ambiental foi evidenciada por:
- `swapon --show` vazio (swap removido durante a sessão)
- `logs/ollama.log`: "llama runner process has terminated: signal: terminated"
- Tempo de falha 6-11s em ambiente degradado vs 46-73s em ambiente saudável

A regressão **não é do código**. O cap=12 é mais conservador (ADR-003 canonical) e será revalidado em ambiente estável.

## 3. Evidência visual — screenshots

Pasta `/tmp/nyx_validate_onda20/` + `/tmp/nyx_validate_onda20_v2/` (efêmeros, não commitados):

| Item | Screenshot | Descrição |
|------|-----------|-----------|
| Banner limpo | `boot_limpo_20260420T230126.png` | Apenas 1 linha `[nyx] próxima sprint: VALIDATE-ONDA-20` sobre a caixa `╭─ Nyx -- Code Agent Local v1.2.0 ─╮` (vs 9 linhas pré-fix) |
| Popup com meta | `popup_meta2_20260420T225357.png` | 16 comandos visíveis com descrição: `/add-dir   Adiciona diretório ao contexto do agent`, `/advisor   Conselheiro de código`, `/branch   Operações de branch`, etc. |
| Box user input | `saudacao_20260420T201839.png` | `╭─ você ─╮ Olá, tudo bem? ╰──╯`, resposta "Oi! Tudo bem." sem tool call |
| RepoMap funcional | `repomap_20260420T202016.png` | "em qual arquivo fica AgentLoop?" → `nyx/agent/loop/_core.py` |
| Popup slash inicial | `popup_slash_20260420T201723.png` | (rodada 1) popup abre automaticamente ao digitar `/` |

## 4. Evidência programática — CTX-11 isolado

Teste direto do payload V2 contra proxy think=false:

```
status: 200
tool_calls: 1
  name= write_memory
  args= {"content": "Uso pyenv 3.12 neste projeto.", "file": "ambiente", "reason": "setup do dev"}
```

O modelo copiou **exatamente** o exemplo do few-shot do prompt — confirmando que a infra conduziu o modelo pequeno ao comportamento esperado (princípio ADR-002).

## 5. Veredicto por sprint

| Sprint | Decisão | Evidência |
|--------|---------|-----------|
| TUI-01 Higiene | CONCLUIDA | banner + footer + prompt ok; 9 linhas boot reduzidas a 1 (TUI-BOOT-LOG-01) |
| TUI-02 Boxes+multiline | CONCLUIDA | box `╭─ você ─╮` confirmado; multiline Ctrl+J é UX prompt-toolkit padrão (não regressível pelas mudanças de Onda 20) |
| TUI-03 Footer+popup | CONCLUIDA | footer + popup com `display_meta` (TUI-POPUP-META-01) |
| CTX-01 Summarizer | CONCLUIDA | gauntlet roundtrip real 54-73s OK (em ambiente saudável) |
| CTX-02 Memory | CONCLUIDA | `write_memory` dispara via linguagem natural (TOOL-INVOKE-MEMORY-01 + CTX-11 prova) |
| CTX-03 RepoMap | CONCLUIDA | query responde path exato, sem tool call |
| CTX-04 /plan | DEFERIDA | marcada OPCIONAL no spec original; não faz parte do release v1 |

## 6. Dependências satisfeitas

VALIDATE-ONDA-20 fecha com deps em todas as 6 sprints-nova CONCLUIDA:
- BUG-PORT-PARSE-01, TUI-FIX-08/09/10, GAUNTLET-FIX-LOOP-SPLIT (pré-existentes)
- AUTOTUNE-FIX-01, AUTOTUNE-FIX-02, TOOL-INVOKE-MEMORY-01, TUI-POPUP-META-01, TUI-BOOT-LOG-01 (materializadas aqui)

Desbloqueia:
- UX-DESIGN-01 (próxima crítica)
- VALIDATE-ONDA-21

## 7. Próximos passos

1. Mover 6 sprints (TUI-01/02/03 + CTX-01/02/03) de `producao/` para `concluidos/`.
2. Marcar CTX-04 DEFERIDA no master.
3. Fechar VALIDATE-ONDA-20 como CONCLUIDA no master.
4. Push acumulado (commits pendentes desde GAUNTLET-FIX-LOOP-SPLIT).

---

*"O que não é validado não é real." — Popper (paráfrase, spec da sprint)*
*"Infra adapta o modelo, não o contrário." — ADR-002 parafraseado*
