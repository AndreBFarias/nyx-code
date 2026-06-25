# SPRINT INPUT-HISTORY-RECALL-01 -- setinha pra cima recall de mensagens anteriores (navegavel + persistente)

## 0. SPEC (machine-readable)

```yaml
sprint:
  id: INPUT-HISTORY-RECALL-01
  title: "Up/Down no input navegam pelas mensagens anteriores do usuário (como shell/CLI de referência), persistido entre sessões; hoje a setinha pra cima no input vazio não traz nada"
  onda: 47
  bloco: "47 -- UX/Input/FS-polish (Onda de Validação 2, 2026-06-25)"
  prioridade: MEDIA
  tipo: Feature / TUI (input)
  dependencias: []
  desbloqueia: []

  touches:
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/agent/app.py
      reason: "TUI Textual: o widget de input não trata Up/Down para navegar histórico. Adicionar: Up (no input vazio OU no início do texto) recall da mensagem anterior; Up de novo -> mais antiga; Down -> mais recente / volta ao rascunho vazio; Esc limpa. Bindings da TUI. Nota de execução: a TUI real é nyx/agent/tui/app.py (este path nyx/agent/app.py não existe); confirmado por grep _on_input_submit/InputWidget."
      linhas_alvo: "input widget / on_key (confirmar)"
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/agent/services/
      reason: "novo (ou reuso) serviço pequeno de histórico de input persistido em ~/.nyx/input_history (append da mensagem enviada; carrega no boot). Integrar no registry de services (ADR-013)."
      linhas_alvo: "novo service input_history (ou onde fizer sentido)"

  creates:
    - "~/.nyx/input_history (arquivo de histórico, runtime; não versionado)"
  removes: []

  forbidden:
    - "Persistir comandos sensíveis sem necessidade -- guardar só o texto enviado pelo usuário (mensagens/comandos), cap razoável (ex.: últimas 500)"
    - "Quebrar a edição multilinha do input (Up dentro de texto multilinha deve mover cursor; recall só quando faz sentido -- input vazio ou cursor na 1a linha)"
    - "Travar a TUI lendo/escrevendo histórico de forma síncrona pesada (append leve)"
    - "emoji / menção a IA externa"

  tests:
    - cmd: "runtime TUI: enviar 'msg A', 'msg B'; input vazio + Up -> 'msg B'; Up -> 'msg A'; Down -> 'msg B'; Down -> rascunho vazio; Esc -> limpa"
      timeout: 120
      esperado: "navegação correta (skill de validação visual)"
    - cmd: "persistência: reiniciar a Nyx; Up traz 'msg B' (carregado de ~/.nyx/input_history)"
      timeout: 120
      esperado: "persiste entre sessões"
    - cmd: "./run.sh --gauntlet --only rapido && bash scripts/sprint_invariants.sh"
      timeout: 400
      esperado: "verdes; service no registry"

  acceptance_criteria:
    - "Up/Down navegam o histórico de input (input vazio ou cursor na 1a linha); Down volta ao rascunho; Esc limpa"
    - "Histórico persiste em ~/.nyx/input_history entre sessões (cap ~500)"
    - "Edição multilinha do input preservada (Up no meio do texto move cursor)"
    - "Service integrado (ADR-013); gauntlet rapido + invariantes 14/14; spec -> concluidos/"
```

---

**Status:** CONCLUIDA (2026-06-25, commit 28dc573)
**Data criação:** 2026-06-25
**Origem:** Onda de Validação 2 (pedido do dono): "quando apertarmos setinha pra cima no chat, se ele tiver vazio ele traz a mensagem anterior, tipo a feature do CLI de referência". Decisão do dono: navegável + persistente.
**Modelo obrigatório:** claude-opus (sem subagentes; implementação direta)

---

## Problema

A TUI não tem recall de histórico de input por Up/Down nus (a 289 ligou só Ctrl+Up/Down, que o dono não descobria). No CLI de referência, Up no input vazio traz a última mensagem e navega pelas anteriores. Falta essa ergonomia básica.

---

## Solução proposta

1. Service pequeno de histórico (`~/.nyx/input_history`): append do texto enviado; carrega no boot; cap ~500. Integrado no registry (ADR-013).
2. No input da TUI (`nyx/agent/tui/app.py` + `tui/widgets/input.py`): Up (input vazio ou cursor na 1a linha) -> mensagem anterior; navegação Up/Down; Down ao fim volta ao rascunho vazio; Esc limpa. Preservar edição multilinha (Up no meio do texto = mover cursor).

---

## Proof-of-work esperado

```bash
# skill de validação visual: TUI real, sequência Up/Up/Down/Down/Esc após 2 envios
# persistência: reiniciar, Up traz a última
./run.sh --gauntlet --only rapido
bash scripts/sprint_invariants.sh
python3 scripts/sync.py | head -1   # service contado no inventário
python3 ~/.config/zsh/scripts/validar-acentuacao.py --paths nyx/agent/tui/app.py nyx/agent/tui/widgets/input.py nyx/agent/services/input_history.py
/home/andrefarias/.local/bin/ruff check nyx/agent/tui/app.py nyx/agent/tui/widgets/input.py nyx/agent/services/input_history.py
```

---

## Critério binário de aceite

- [x] Up/Down navegam histórico (input vazio / 1a linha); Down volta ao rascunho; Esc limpa
- [x] persiste em ~/.nyx/input_history (cap ~500)
- [x] multilinha preservada
- [x] service no registry; gauntlet rapido + invariantes 14/14; validação visual OK; spec -> concluidos/

---

## Riscos

| Risco | Mitigação |
|-------|-----------|
| Conflito Up com edição multilinha | recall só quando input vazio ou cursor na 1a linha; senão Up move cursor |
| Histórico crescer infinito | cap ~500, append leve |

---

*"A memoria do que voce ja digitou e metade da ergonomia de um REPL." -- anonimo*
