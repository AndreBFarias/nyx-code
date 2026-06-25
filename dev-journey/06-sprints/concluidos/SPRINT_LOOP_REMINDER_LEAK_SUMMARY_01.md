# SPRINT LOOP-REMINDER-LEAK-SUMMARY-01 -- bloco <system-reminder> vaza cru na resposta/summary do usuário

## 0. SPEC (machine-readable)

```yaml
sprint:
  id: LOOP-REMINDER-LEAK-SUMMARY-01
  title: "Na Onda de Validação 1 (probe c2), apos varias chamadas de search, o `summary`/resposta user-facing veio com o bloco `<system-reminder>...</system-reminder>` CRU em vez dos resultados -- prompt interno vazando para o usuário"
  onda: 46
  bloco: "46 -- Saneamento de CI & Working Tree + achados da Onda de Validação 1"
  prioridade: MEDIA
  tipo: Bugfix / Loop (output user-facing)
  dependencias: []
  desbloqueia: []

  touches:
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/agent/loop/_iteration.py
      reason: "investigar onde o summary/resposta final e construido (done(summary=...), _build_force_done_summary ~455-489, e o caminho que monta a resposta apos tool_calls). Identificar como o texto do reminder (build_reminder, prompt.py:155) pode acabar no campo user-facing. Adicionar guard que REMOVE qualquer bloco <system-reminder>...</system-reminder> do texto user-facing (defesa em profundidade), alem de corrigir a fonte se identificada. (Onda de Validação 1)"
      linhas_alvo: "construcao de summary/resposta (confirmar via grep system-reminder, _build_force_done_summary, done)"
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/agent/prompt.py
      reason: "build_reminder (155-207) gera o bloco; se a fonte do leak for a reinjeção indo parar no campo de resposta, ajustar aqui. Provavel que o guard de saida em _iteration.py seja suficiente."
      linhas_alvo: "155-207 (se necessario)"

  creates: []
  removes: []

  forbidden:
    - "Parar de reinjetar o reminder (NYX-PROMPT-REINJECT-01 e necessario contra drift do 3b) -- o fix e impedir que ele VAZE para o user-facing, não remove-lo do contexto"
    - "Strip ingenuo que tambem remova conteudo legitimo que contenha '<' '>' (mirar o bloco exato `<system-reminder>...</system-reminder>`)"
    - "Mexer no conteudo do reminder (isso e 373) -- aqui e so o vazamento para a resposta"

  tests:
    - cmd: "teste deterministico: passar uma resposta/summary sintetico contendo um bloco <system-reminder>...</system-reminder> + texto util pelo caminho de construcao do summary -> o output user-facing não contem o bloco, mantem o texto util"
      timeout: 60
      esperado: "bloco removido, conteudo util preservado (testar os 2: com e sem bloco)"
    - cmd: "./run.sh --gauntlet --only rapido"
      timeout: 300
      esperado: "APROVADO (sem regressao no loop)"
    - cmd: "bash scripts/sprint_invariants.sh"
      timeout: 180
      esperado: "14/14 PASS"
    - cmd: "probe runtime (best-effort): repetir o cenario da Onda Val 1 (varias buscas) -> o summary não traz o bloco do reminder"
      timeout: 240
      esperado: "sem vazamento (best-effort dado o nao-determinismo do 3b)"

  acceptance_criteria:
    - "O texto user-facing (resposta/summary) nunca contem o bloco <system-reminder>...</system-reminder>"
    - "Guard deterministico testado nos 2 caminhos (com bloco -> removido; sem bloco -> intacto)"
    - "Reinjeção do reminder no CONTEXTO preservada (não é desligada)"
    - "gauntlet rapido APROVADO; invariantes 14/14; spec -> concluidos/"
```

---

**Status:** CONCLUIDA
**Data criação:** 2026-06-25
**Origem:** Onda de Validação 1 (achado #3, BUG). Probe c2 ("busque ALVO em /tmp/...", com instrução explicita de usar search): apos 3 chamadas de search, o `summary` final foi o bloco `<system-reminder>...</system-reminder>` literal em vez dos resultados da busca.
**Modelo obrigatorio:** modelo principal local, sem subagentes; implementação direta

---

## Problema

Na Onda de Validação 1, num turno com varias buscas, a resposta user-facing (`summary` do done) veio com o bloco `<system-reminder>` cru -- o prompt interno (reinjetado por NYX-PROMPT-REINJECT-01, `build_reminder` em prompt.py:155) vazou para o que o usuário ve. UX quebrada: em vez dos resultados, o usuário recebe instruções internas.

---

## Causa-raiz (hipotese, confirmar)

O `summary`/resposta final e montado a partir de um trecho do histórico/contexto que incluiu o bloco reinjetado, OU o 3b ecoou o reminder e nenhum guard o removeu antes de exibir. A reinjeção e necessaria (contra drift); o que falta e um guard de SAIDA que nunca deixe o bloco chegar ao usuário.

---

## Solucao proposta

1. Investigar (grep `system-reminder`, `_build_force_done_summary`, `done`, `summary`) onde o texto user-facing e produzido e como o bloco pode entrar.
2. Adicionar um guard deterministico que remove `<system-reminder>...</system-reminder>` (regex multilinha, ancorado nas tags exatas) do texto user-facing -- defesa em profundidade, independente da fonte.
3. Se a fonte exata for identificada (ex.: summary derivado do history bruto), corrigir tambem na fonte.
Manter a reinjeção no CONTEXTO intacta.

---

## Proof-of-work esperado

```bash
# teste deterministico do guard (2 caminhos):
#  - input com bloco <system-reminder>X</system-reminder> + "resultado util" -> output = "resultado util" (sem bloco)
#  - input sem bloco -> output identico
./run.sh --gauntlet --only rapido        # APROVADO
bash scripts/sprint_invariants.sh         # 14/14 PASS
python3 ~/.config/zsh/scripts/validar-acentuacao.py --paths nyx/agent/loop/_iteration.py
/home/andrefarias/.local/bin/ruff check nyx/agent/loop/_iteration.py
```

---

## Criterio binario de aceite

- [ ] resposta/summary user-facing nunca contem o bloco do reminder
- [ ] guard testado com bloco (removido) e sem bloco (intacto)
- [ ] reinjeção no contexto preservada
- [ ] gauntlet rapido APROVADO; invariantes 14/14; spec -> concluidos/

---

## Riscos

| Risco | Mitigacao |
|-------|-----------|
| Regex remover conteudo legitimo | ancorar nas tags exatas `<system-reminder>`/`</system-reminder>`; testar caminho sem bloco |
| Não reproduzir o leak em runtime (3b nao-determinístico) | o guard deterministico fecha o vetor independente da reproducao; o teste do guard e a prova principal |

---

*"O bilhete do contrarregra nunca pode aparecer no palco." -- anonimo*
