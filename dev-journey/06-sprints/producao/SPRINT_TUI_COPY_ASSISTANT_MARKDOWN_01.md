## 0. SPEC (machine-readable)

```yaml
sprint:
  id: TUI-COPY-ASSISTANT-MARKDOWN-01
  numero_master: 448
  title: "Seleção por drag no Markdown assentado do assistant extrai o texto-fonte correto (fecha o copiar-código da 390)"
  onda: 48
  prioridade: MEDIA
  tipo: TUI/UX
  dependencias: [TUI-COPY-SELECTION-01]
  desbloqueia: []

  touches:
    - path: nyx/agent/tui/widgets/chat_message.py
      reason: "sobrescrever get_selection no ChatMessage para o conteudo assistant assentado (render Markdown)"
  creates: []
  removes: []

  forbidden:
    - "Quebrar o copy-on-select da 390 nos roles user/tool/system/assistant-streaming (render Text/Content, ja funcionam)"
    - "Trocar o render Markdown assentado por Text puro (perderia syntax highlight -- regressao visual)"
    - "Remover o atalho Ctrl+Y (action_copy_last_code continua como caminho garantido)"
    - "Extrair ingenuamente de self._content sem mapear offsets (copia o trecho errado -- motivo de a 390 não ter forçado isso)"
    - "Adicionar emoji; mencionar ferramenta de IA"

  acceptance_criteria:
    - "Drag sobre o corpo de uma mensagem assistant ASSENTADA retorna texto nao-vazio via get_selected_text()"
    - "O texto extraído corresponde ao trecho selecionado do _content cru (não desalinhado, não o widget inteiro por seleção parcial)"
    - "Roles user/tool/system e assistant durante streaming seguem selecionaveis como na 390 (regressao zero)"
    - "Prova E2E via Textual Pilot (drag -> get_selected_text -> xclip -o idêntico) + screenshot com a seleção destacada"
```

---

# Sprint TUI-COPY-ASSISTANT-MARKDOWN-01 — copiar o código do assistant por seleção

**Status:** PENDENTE
**Data criação:** 2026-07-20 (promoção do débito registrado na ONDA-47 em 2026-06-25)
**Origem:** achado anti-débito da 390 (TUI-COPY-SELECTION-01): o copy-on-select cobre os roles cujo render é `Text`/`Content`, mas o conteúdo do assistant já ASSENTADO renderiza como `Markdown` (`RichVisual`/`Group`), que `Widget.get_selection` não extrai — selecionar o código formatado da Nyx por drag retorna vazio. Era exatamente o "copiar o código" que o dono pediu; ficou em blockquote da ONDA-47 sem número, invisível ao gerador de fila. Esta spec materializa a pendência com ID.

---

## Contexto do projeto (snapshot)

> **Arquivos reais:** `nyx/agent/tui/widgets/chat_message.py` (classe `ChatMessage(Static)`; o assistant assentado retorna `Group(label, Markdown(self._content))`; o cru vive em `self._content`) e `nyx/agent/tui/app.py` (handler `on_text_selected` da 390: `screen.get_selected_text()` -> `write_text` xclip -> fallback OSC52).
> **Textual 8.2.7:** `Widget.get_selection(selection)` é o ponto de extensão — a base só sabe ler visuais `Text`/`Content`; um widget pode sobrescrever e devolver `(texto, separador)` próprio.
> **Paridade de experiência (missão):** num CLI-agente, copiar o código gerado é gesto de primeira classe; hoje só `Ctrl+Y` (último bloco de código) cobre o caso.

---

## Problema

1. Mensagem assistant assentada (pós-streaming) renderiza `Markdown` para ter syntax highlight — decisão correta da ONDA-32, mantida.
2. `Screen.get_selected_text()` percorre os widgets da seleção chamando `get_selection`; no `ChatMessage` assistant assentado a base retorna `None` (visual não-`Text`) -> seleção "pega" visualmente mas extrai vazio.
3. O render Markdown (cabeçalho "NyxCode", quebras de linha do reflow, syntax highlight) NÃO tem correspondência 1:1 de linhas com `self._content` — extração ingênua do cru desalinha offsets e copia o trecho errado.

## Solução proposta

Sobrescrever `get_selection` no `ChatMessage`, ativo apenas quando o widget está no estado assistant-assentado (render Markdown):

- **Caminho A (mínimo honesto, aceitável como v1):** seleção que toca o widget devolve o `self._content` INTEIRO (com separador `\n`) quando a seleção cobre o widget por completo; para seleção parcial, mapear pelo menos por LINHA visual -> linha do cru via um índice construído no assentamento (`_settle`). Se o mapeamento por linha não for confiável para uma linha específica (linha sintética do render, ex.: cabeçalho), excluí-la da extração em vez de chutar.
- **Caminho B (ideal, se o custo couber na sprint):** manter no assentamento um índice linha-visual->linha-fonte gerado ao renderizar (o `Markdown` do Rich preserva a ordem dos blocos; blocos de código preservam linhas literais), e extrair por offsets com fidelidade de coluna nos blocos de código (o caso de uso real: copiar código byte-fiel, paridade com a 392 do REPL).

A executora decide A ou B ao medir o esforço do índice; o critério de aceite exige no mínimo A com fidelidade por linha nos blocos de código. Em ambos, o handler `on_text_selected` da 390 permanece intocado (ele já usa `get_selected_text()`; o ganho vem por baixo).

## Comandos de verificação (literais)

```bash
# 1. Estática + acentuação
ruff check nyx/agent/tui/widgets/chat_message.py
python ~/.config/zsh/scripts/validar-acentuacao.py nyx/agent/tui/widgets/chat_message.py

# 2. Prova E2E via Textual Pilot (molde da 390): montar app real, mensagem assistant
#    com bloco de código, ASSENTAR (settle), drag por Pilot mouse_down/hover/mouse_up
#    sobre as linhas do código; assert get_selected_text() contém as linhas EXATAS;
#    xclip -o -selection clipboard idêntico; save_screenshot com a seleção destacada.

# 3. Regressão da 390: mesmo teste sobre role user e assistant EM streaming -> segue extraindo.

# 4. Gauntlet rápido + invariantes (protocolo padrão)
./run.sh --gauntlet --only rapido
bash scripts/sprint_invariants.sh
```

## Critério binário de aceite (IA executora)

1. Drag sobre código assentado do assistant -> `get_selected_text()` retorna as linhas do código byte-fiéis (Pilot + xclip -o).
2. Seleção parcial não copia trecho desalinhado (assert do conteúdo, não só não-vazio).
3. Roles da 390 sem regressão (prova no mesmo run).
4. Skill validação-visual executada (toca TUI): screenshot da seleção destacada.
5. Invariantes FAIL_AFTER <= FAIL_BEFORE; ruff e acentuação limpos.

## Não-objetivos (anti-débito)

- **Não** reimplementar o clipboard (390 já resolveu xclip/OSC52).
- **Não** tornar selecionável o cabeçalho/rodapé decorativo do widget (só o conteúdo).
- **Não** mexer no streaming (já é `Text`, já funciona).

---

*"O código que a Nyx escreve só vira código do usuário quando ele consegue copiá-lo."*
