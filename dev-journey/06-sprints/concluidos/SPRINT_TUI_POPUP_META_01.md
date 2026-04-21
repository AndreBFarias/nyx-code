# SPRINT TUI-POPUP-META-01 — popup `/` mostra descrição por comando

## 0. SPEC (machine-readable)

```yaml
sprint:
  id: TUI-POPUP-META-01
  title: "Popup de slash commands usa CompleteStyle.COLUMN para renderizar display_meta"
  onda: 22
  bloco: 2.8
  prioridade: MÉDIA
  tipo: Bugfix UX
  dependencias: []
  desbloqueia: [VALIDATE-ONDA-20, TUI-03]

  touches:
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/cli.py
      reason: "CompleteStyle.MULTI_COLUMN (linha 232) ignora display_meta; COLUMN renderiza. Spec TUI-03 pede descrição por comando."
      linhas_alvo: "229-232"

  creates: []
  removes: []

  forbidden:
    - "Alterar display_meta no NyxCompleter (já está correto em completer.py:61/84)"
    - "Duplicar display como f-string com descrição embutida (ruim em MULTI_COLUMN celular estreito)"
    - "Adicionar emoji"

  tests:
    - cmd: "validação visual: popup `/` deve mostrar cada comando com descrição à direita"
      timeout: 60
    - cmd: "./run.sh --gauntlet --only rapido"
      timeout: 120
      esperado: "18/18 APROVADO (sem regressão)"

  acceptance_criteria:
    - "Screenshot do popup `/` mostra `/<cmd>  <descrição>` por linha"
    - "Paths continuam completando (apesar de mudarem para single-column layout)"
    - "FAIL invariantes <= baseline"
```

---

**Status:** CONCLUIDA (commit 94d7327)
**Data criação:** 2026-04-20
**Origem:** VALIDATE-ONDA-20 rodada 1 screenshot `popup_slash_20260420T201723.png` mostra 7 colunas com apenas os nomes dos 47 commands — spec TUI-03 dizia "completer com `display_meta`". Investigação: `completer.py:61` já passa `display_meta=desc[:40]`. O problema é que `CompleteStyle.MULTI_COLUMN` em prompt-toolkit **renderiza apenas o display**, ignorando o meta. Apenas `CompleteStyle.COLUMN` renderiza meta alinhado à direita.
**Modelo obrigatório:** claude-opus-4-7 (sem subagentes)

---

## Fix

```python
# nyx/cli.py:231-232 ANTES
_term_cols = _sh.get_terminal_size(fallback=(80, 24)).columns
_style = CompleteStyle.MULTI_COLUMN if _term_cols >= 100 else CompleteStyle.COLUMN

# DEPOIS
_term_cols = _sh.get_terminal_size(fallback=(80, 24)).columns  # preservado para bottom_toolbar abaixo
_style = CompleteStyle.COLUMN
```

Trade-off aceito: paths também caem em single column. ADR-009 prioriza qualidade da UX (ver descrição do comando) > densidade visual. Paths são completados infrequentemente vs slash commands (entrada principal).

---

## Proof-of-work obrigatório

- Screenshot pós-fix mostrando popup com descrições alinhadas.
- Gauntlet rapido 18/18.

---

## Riscos

| Risco | Mitigação |
|-------|-----------|
| Path completion perde MULTI_COLUMN visual | Trade-off consciente; paths ainda funcionam |
| COLUMN em terminal muito estreito | COLUMN lida melhor que MULTI_COLUMN em estreito |

*"A legenda vale mais que o atalho." — ADR-009 parafraseado*
