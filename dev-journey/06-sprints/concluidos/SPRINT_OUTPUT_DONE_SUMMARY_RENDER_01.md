# SPRINT OUTPUT-DONE-SUMMARY-RENDER-01 -- `summary="..."` cru vaza na resposta do usuário

## 0. SPEC (machine-readable)

```yaml
sprint:
  id: OUTPUT-DONE-SUMMARY-RENDER-01
  title: "Resposta user-facing apareceu como `summary=\"Lista vazia` (prefixo `summary=` + aspa sem fechar) em vez de so 'Lista vazia'; o argumento do done() esta vazando cru no render"
  onda: 47
  bloco: "47 -- UX/Input/FS-polish (Onda de Validação 2, 2026-06-25)"
  prioridade: MEDIA
  tipo: Bugfix / Output (render user-facing)
  dependencias: []
  desbloqueia: []

  touches:
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/agent/parser.py
      reason: "o 3b emite done de forma malformada (ex.: `done(summary=\"Lista vazia` sem fechar, ou texto cru `summary=...`); o parser/extrator de done precisa extrair so o VALOR do summary, tolerando aspa nao-fechada e o prefixo `summary=`. Confirmar onde done/summary e parseado."
      linhas_alvo: "extracao de done/summary (grep summary= / done)"
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/agent/loop/_iteration.py
      reason: "se o summary user-facing nasce aqui (done(summary=...)), garantir que o valor exibido seja o texto limpo, nunca o literal `summary=\"...`."
      linhas_alvo: "construcao do summary user-facing (confirmar)"

  creates: []
  removes: []

  forbidden:
    - "Remover o done() ou a feature de summary -- so o RENDER/extracao do valor"
    - "Strip ingenuo que corte conteudo legitimo que por acaso contenha 'summary=' no meio de um texto"
    - "emoji / mencao a IA externa"

  tests:
    - cmd: "teste deterministico: entrada user-facing `summary=\"Lista vazia` -> exibe 'Lista vazia' (sem prefixo, sem aspa pendente)"
      timeout: 60
      esperado: "limpo"
    - cmd: "teste: done(summary=\"texto X\") bem-formado -> exibe 'texto X'; resposta normal sem done -> intacta"
      timeout: 60
      esperado: "os 2 caminhos corretos"
    - cmd: "./run.sh --gauntlet --only rapido && bash scripts/sprint_invariants.sh"
      timeout: 400
      esperado: "verdes"

  acceptance_criteria:
    - "Nenhuma resposta user-facing mostra o literal `summary=` nem aspas pendentes do done()"
    - "Summary bem-formado e malformado (aspa aberta) extraem o texto limpo"
    - "Resposta normal (sem done) intacta; gauntlet rapido + invariantes 14/14; spec -> concluidos/"
```

---

**Status:** CONCLUIDA
**Data criação:** 2026-06-25
**Data conclusão:** 2026-06-25
**Origem:** Onda de Validação 2 (teste as-user, imagem 1). Apos um turno, a resposta da Nyx apareceu como `summary="Lista vazia` (com `summary=` e aspa sem fechar) em vez de "Lista vazia". Primo do 381 (vetor diferente: o argumento do done()).

---

## Problema

Na imagem, o balao da Nyx mostrou `summary="Lista vazia` -- o 3b escreveu um `done(summary="Lista vazia"...)` malformado (provavelmente truncado, sem fechar a aspa) e o render exibiu o literal cru em vez de extrair o texto "Lista vazia". UX quebrada: o usuário ve o formato interno do tool call.

---

## Causa-raiz (hipotese, confirmar)

A extracao do `summary` do done() (no parser e/ou no loop) não trata o caso malformado do 3b (aspa não fechada, prefixo `summary=` cru) e deixa o literal chegar ao render user-facing.

---

## Solucao proposta

1. Investigar (grep `summary=`, `done`, parser de done) onde o valor do summary e extraido para o texto user-facing.
2. Tornar a extracao robusta: capturar o valor apos `summary=` tolerando aspa simples/dupla e aspa nao-fechada (pega ate o fim da linha/string); nunca exibir o prefixo `summary=` nem aspas penduradas.
3. Defesa em profundidade: no render do balao da Nyx, se o texto for exatamente um artefato `summary=...`, extrair o valor.

---

## Proof-of-work esperado

```bash
# teste deterministico dos 2 caminhos (malformado e bem-formado) + resposta normal intacta
./run.sh --gauntlet --only rapido
bash scripts/sprint_invariants.sh
python3 ~/.config/zsh/scripts/validar-acentuacao.py --paths nyx/agent/parser.py nyx/agent/loop/_iteration.py
/home/andrefarias/.local/bin/ruff check nyx/agent/parser.py nyx/agent/loop/_iteration.py
```

---

## Criterio binario de aceite

- [ ] resposta nunca exibe `summary=` cru nem aspa pendente
- [ ] summary malformado e bem-formado extraem texto limpo
- [ ] resposta normal intacta; gauntlet rapido + invariantes 14/14; spec -> concluidos/

---

## Riscos

| Risco | Mitigacao |
|-------|-----------|
| Extracao cortar conteudo legitimo | ancorar no padrão do done()/inicio da resposta, não em qualquer 'summary=' no meio do texto; testar resposta normal |
| 3b variar o formato malformado | cobrir os formatos vistos (aspa aberta, sem aspa) + o caminho de done bem-formado |

---

*"O ator não recita as aspas do roteiro." -- anônimo*
