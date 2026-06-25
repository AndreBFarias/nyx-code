# SPRINT TUI-COPY-ASSISTANT-MARKDOWN-01 -- selecionar/copiar o codigo (Markdown) que a Nyx gera

## 0. SPEC (machine-readable)

```yaml
sprint:
  id: TUI-COPY-ASSISTANT-MARKDOWN-01
  title: "copy-on-select (390) nao alcanca o conteudo do assistant renderizado como Markdown: a API de selecao do Textual so extrai Text/Content, nao o RichVisual/Group do Markdown -> arrastar sobre o codigo da Nyx volta vazio. Era exatamente o 'copiar o codigo' que o dono queria"
  onda: 47
  bloco: "47 -- UX/Input/FS-polish (Onda de Validação 2/3, 2026-06-25)"
  prioridade: ALTA
  tipo: Feature / TUI (clipboard, follow-up da 390)
  dependencias: [TUI-COPY-SELECTION-01]
  desbloqueia: []

  touches:
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/agent/tui/widgets/
      reason: "o ChatMessage/balao do assistant renderiza o conteudo como Markdown (RichVisual/Group), que `Widget.get_selection` nao extrai (so Text/Content). Investigar o widget de mensagem do assistant e como tornar o conteudo (especialmente blocos de codigo) selecionavel/copiavel. Opcoes: (a) manter o texto-fonte (raw markdown / o codigo) acessivel para copia; (b) afordancia por bloco de codigo (cada bloco copiavel); (c) mapear linhas renderizadas->fonte."
      linhas_alvo: "widget ChatMessage do assistant (confirmar via grep Markdown/render)"
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/agent/tui/app.py
      reason: "se a solucao for por afordancia/atalho (ex.: copiar bloco N, ou copiar a ultima resposta inteira em raw), fiar no handler. Reuso do util clipboard.py (xclip/OSC52) da 390."
      linhas_alvo: "handlers de copia (confirmar)"

  creates: []
  removes: []

  forbidden:
    - "Quebrar o copy-on-select de texto comum (roles user/tool) ja entregue na 390"
    - "Quebrar o Ctrl+Y (copia ultimo bloco de codigo) ja existente -- e o fallback atual"
    - "Copiar trecho ERRADO por desalinhamento de offset (o 390 nao fez extracao ingenua justamente por isso) -- a copia tem que devolver o codigo correto, byte-fiel ao que a Nyx gerou"
    - "Reescrever o render Markdown inteiro / perder a formatacao visual do chat sem necessidade"
    - "emoji / mencao a IA externa"

  tests:
    - cmd: "validacao-visual (skill): a Nyx gera um bloco de codigo; selecionar/copiar (ou afordancia) -> `xclip -o -selection clipboard` retorna o codigo EXATO (byte-fiel), sem o markdown de cerca nem desalinhamento"  # noqa-acento (nome canonico do plugin)
      timeout: 240
      esperado: "codigo copiado correto"
    - cmd: "regressao: copy-on-select de texto comum (user/tool) e Ctrl+Y seguem funcionando"
      timeout: 120
      esperado: "390 intacta"
    - cmd: "./run.sh --gauntlet --only rapido && bash scripts/sprint_invariants.sh"
      timeout: 400
      esperado: "verdes"

  acceptance_criteria:
    - "Da pra copiar o codigo que a Nyx gera (no balao Markdown do assistant) e o clipboard recebe o codigo EXATO (byte-fiel)"
    - "copy-on-select de texto comum (390) e Ctrl+Y intactos"
    - "Sem desalinhamento (copia o trecho certo); formatacao visual do chat preservada"
    - "gauntlet rapido + invariantes 14/14; validacao-visual real (skill); spec -> concluidos/"  # noqa-acento (nome canonico do plugin)
```

---

**Status:** CONCLUIDA (2026-06-25, commit 13cc162)
**Data criacao:** 2026-06-25
**Origem:** achado da execução da 390 TUI-COPY-SELECTION-01 (Onda de Validação 2/3). O copy-on-select funciona para texto/roles, mas o conteudo do assistant em Markdown (onde vivem os blocos de codigo) NAO e selecionavel por drag na API do Textual 8.2.7 (`get_selection` so le Text/Content, nao RichVisual/Group). E exatamente o "copiar o codigo" que motivou o pedido do dono. Fallback atual: `Ctrl+Y` copia o ultimo bloco.
**Modelo obrigatorio:** claude-opus (sem subagentes; implementação direta)

---

## Problema

A 390 entregou copy-on-select, mas so para o que o Textual sabe selecionar (Text/Content). O balao do assistant renderiza Markdown como RichVisual/Group -> arrastar sobre o codigo da Nyx retorna vazio. O usuario quer copiar o CODIGO que a Nyx escreve; hoje so via `Ctrl+Y` (ultimo bloco).

---

## Causa-raiz

O conteudo do assistant e renderizado como Markdown (sem correspondencia 1:1 linha-renderizada -> fonte), e a API de selecao do Textual nao extrai esse tipo de visual. Extracao ingenua desalinharia offsets (por isso a 390 nao a fez).

---

## Solucao proposta (investigar e escolher a mais simples que entregue codigo byte-fiel)

O executor deve investigar o widget ChatMessage do assistant e escolher UMA abordagem:
- (A) Guardar o texto-fonte (raw markdown / o codigo gerado) por mensagem e, na copia, devolver o codigo byte-fiel (mapeando a selecao/afordancia para a fonte) -- evita o problema de offset do render.
- (B) Afordancia por bloco de codigo: cada bloco de codigo copiavel (clique/atalho copia aquele bloco) -- alinhado com o Ctrl+Y ja existente, estendido para "qualquer bloco", nao so o ultimo.
- (C) Tornar o conteudo selecionavel como Text quando for codigo puro.
Preferir o que entregue o codigo EXATO com menor complexidade e sem quebrar a 390/Ctrl+Y. Reusar `nyx/agent/clipboard.py` (xclip/OSC52).

---

## Proof-of-work esperado

```bash
# validacao-visual (skill): Nyx gera bloco de codigo -> copiar -> xclip -o -selection clipboard == codigo exato  # noqa-acento (nome canonico do plugin)
./run.sh --gauntlet --only rapido
bash scripts/sprint_invariants.sh
python3 ~/.config/zsh/scripts/validar-acentuacao.py --paths <arquivos tocados>
/home/andrefarias/.local/bin/ruff check <arquivos tocados>
```

---

## Criterio binario de aceite

- [ ] copiar o codigo do balao do assistant -> clipboard com o codigo EXATO (byte-fiel)
- [ ] copy-on-select de texto comum (390) + Ctrl+Y intactos
- [ ] sem desalinhamento; formatacao do chat preservada
- [ ] gauntlet rapido + invariantes 14/14; validacao-visual real; spec -> concluidos/  <!-- noqa-acento (nome canonico do plugin) -->

---

## Riscos

| Risco | Mitigacao |
|-------|-----------|
| Desalinhamento offset render->fonte | guardar o texto-fonte por mensagem e copiar a fonte, nao o render |
| Quebrar a 390/Ctrl+Y | testar regressao dos dois; abordagem aditiva |
| API Textual nao cooperar | abordagem (B) por afordancia/atalho contorna a limitacao de selecao |

---

*"O codigo que a Nyx escreve so vale se voce conseguir leva-lo com voce." -- anonimo*
