# SPRINT TUI-BOOT-LOG-01 — boot silencioso com 1 linha de status

## 0. SPEC (machine-readable)

```yaml
sprint:
  id: TUI-BOOT-LOG-01
  title: "Mensagens de boot do run.sh vão para logs/boot.log; stdout mostra só 'Pronto'"
  onda: 22
  bloco: 2.8
  prioridade: BAIXA
  tipo: UX polish
  dependencias: []
  desbloqueia: [VALIDATE-ONDA-20, TUI-01]

  touches:
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/run.sh
      reason: "9 linhas [nyx] informativas vazam pro stdout antes da TUI subir. Spec TUI-01 '§silenciados ou reduzidos'."
      linhas_alvo: "28-30 (helpers), 170-412 (sites de boot)"

  creates:
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/logs/boot.log (criado em runtime)

  removes: []

  forbidden:
    - "Silenciar erros/warnings (log_warn) -- bugs devem continuar visíveis"
    - "Silenciar mensagens de shutdown (cleanup) -- usuário precisa saber que encerrou"
    - "Silenciar mensagens do gauntlet ou --smoke -- são saídas do modo de trabalho"
  tests:
    - cmd: "./run.sh --smoke"
      esperado: "boot ok (sem 9 linhas [nyx] pré-banner)"
    - cmd: "abrir TUI em kitty, screenshot banner"
      esperado: "apenas 1 linha [nyx] Pronto (ou silêncio total) antes da caixa ╭─╮"
    - cmd: "./run.sh --gauntlet --only rapido"
      esperado: "18/18 APROVADO"

  acceptance_criteria:
    - "Screenshot banner mostra <= 1 linha [nyx] acima da caixa ╭─╮"
    - "logs/boot.log existe e contém as mensagens detalhadas do boot"
    - "log_warn continua visível em stdout"
    - "Mensagens de shutdown continuam visíveis"
    - "Gauntlet rapido 18/18 + contexto 11/11"
```

---

**Status:** CONCLUIDA (commit 91e27f4)
**Data criação:** 2026-04-20
**Origem:** VALIDATE-ONDA-20 rodada 1 screenshot mostrou 9 linhas `[nyx]` informativas acima do banner (Limpando cache, Iniciando Ollama, Ollama pronto, Modelo, Auto-tune, Pré-carregando modelo, Modelo pré-carregado, Iniciando proxy, Proxy pronto, Iniciando Nyx CLI). Spec TUI-01 pedia "silenciados ou reduzidos".
**Modelo obrigatório:** claude-opus-4-7 (sem subagentes)

---

## Solução

Introduz `log_boot` que escreve em `logs/boot.log` (apenas). Trocar `log_nyx`/`log_ok` de todas as mensagens *do fase de boot* por `log_boot`. No final do boot, imprimir 1 linha `log_ok "Pronto -- Ollama:11435 Proxy:11436 Nyx CLI"`.

`log_warn` e mensagens de erro permanecem visíveis (bugs precisam aparecer). Mensagens de shutdown (`Desconectando`, `Parando Ollama`, `Fim`) permanecem visíveis (usuário precisa saber).

---

## Critério binário de aceite

- [ ] Banner screenshot mostra <= 1 linha [nyx] pré-caixa
- [ ] `cat logs/boot.log` tem as mensagens detalhadas
- [ ] Gauntlet rapido 18/18 + contexto 11/11
- [ ] FAIL invariantes <= baseline

*"O boot silencioso é a corte prestada ao olho: só diga se houver erro." — ergonomia*
