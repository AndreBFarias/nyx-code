# SPRINT TUI-COPY-SELECTION-01 -- selecionar texto no chat nao copia (copy-on-select)

## 0. SPEC (machine-readable)

```yaml
sprint:
  id: TUI-COPY-SELECTION-01
  title: "Selecionar texto/codigo no chat (e botao direito) nao copia pro clipboard; implementar copy-on-select (selecionou -> copiou) via clipboard do sistema (xclip/OSC52)"
  onda: 47
  bloco: "47 -- UX/Input/FS-polish (Onda de Validacao 2, 2026-06-25)"  # noqa-acento
  prioridade: MEDIA
  tipo: Feature / TUI (clipboard)
  dependencias: []
  desbloqueia: []

  touches:
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/agent/app.py
      reason: "TUI Textual: a area de conversa precisa permitir selecao de texto e, ao soltar a selecao, copiar para o clipboard do sistema (copy-on-select). Investigar a API de selecao do Textual da versao em uso (TextArea/RichLog/Markdown) e o hook de selecao."
      linhas_alvo: "widget de conversa / on_selection (confirmar API Textual)"
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/agent/services/
      reason: "util de clipboard: xclip (ja dependencia do projeto, instalado pelo install.sh) com fallback OSC52 (funciona via terminal, inclusive remoto). Integrar como service/util."
      linhas_alvo: "novo util clipboard (ou reuso se existir)"

  creates: []
  removes: []

  forbidden:
    - "Quebrar o clique em widgets/scroll da TUI ao habilitar selecao (equilibrar captura de mouse)"
    - "Depender de clipboard que so funciona com X11 sem fallback -- usar OSC52 como fallback portatil"
    - "Trigger de dialog/alerta do navegador (N/A aqui, mas nada de popups bloqueantes)"
    - "emoji / mencao a IA externa"

  tests:
    - cmd: "validacao-visual + runtime: selecionar um trecho de codigo no chat -> `xclip -o -selection clipboard` retorna o trecho"  # noqa-acento
      timeout: 180
      esperado: "selecao copiada (copy-on-select)"
    - cmd: "fallback OSC52: em terminal sem X (ou xclip ausente), a sequencia OSC52 e emitida (verificar via captura/log)"
      timeout: 120
      esperado: "fallback funciona"
    - cmd: "./run.sh --gauntlet --only rapido && bash scripts/sprint_invariants.sh"
      timeout: 400
      esperado: "verdes; scroll/clique da TUI preservados"

  acceptance_criteria:
    - "Selecionar texto no chat copia para o clipboard do sistema automaticamente (copy-on-select)"
    - "xclip usado quando disponivel; fallback OSC52 quando nao"
    - "Scroll/clique/foco da TUI seguem funcionando (selecao nao quebra a interacao)"
    - "gauntlet rapido + invariantes 14/14; validacao-visual no ambiente real (skill); spec -> concluidos/"  # noqa-acento
```

---

**Status:** PENDENTE
**Data criacao:** 2026-06-25
**Origem:** Onda de Validacao 2 (pedido do dono): "o botao direito no texto selecionado nao ta copiando o codigo". Decisao do dono: copy-on-select (selecionou, copiou).  <!-- noqa-acento -->
**Modelo obrigatorio:** modelo principal (sem subagentes; implementacao direta)  <!-- noqa-acento -->

---

## Problema

Selecionar texto/codigo no chat da TUI nao copia para o clipboard (nem por botao direito). O usuario nao consegue extrair codigo que a Nyx produziu. Ergonomia essencial faltando.

---

## Solucao proposta

1. Habilitar selecao de texto na area de conversa (API de selecao do Textual da versao em uso).
2. Ao concluir a selecao, copiar para o clipboard do sistema (copy-on-select): `xclip -selection clipboard` (xclip ja e dependencia, instalado pelo install.sh) com fallback **OSC52** (sequencia de terminal, portatil e funciona remoto/sem X).
3. Equilibrar a captura de mouse para nao quebrar scroll/clique nos widgets.

Nota: esta sprint toca a TUI -> a skill validacao-visual e obrigatoria (pipeline 3-tentativas). E o ponto mais sensivel da leva (selecao+clipboard em TUI dependem da versao do Textual e do terminal) -- se a API de selecao do Textual nao cobrir, documentar e cair para um modo alternativo (ex.: atalho de teclado que copia o ultimo bloco de codigo), registrando como sub-sprint.  <!-- noqa-acento -->

---

## Proof-of-work esperado

```bash
# validacao-visual: selecionar trecho no chat; depois:  # noqa-acento
xclip -o -selection clipboard    # deve retornar o trecho selecionado
./run.sh --gauntlet --only rapido
bash scripts/sprint_invariants.sh
python3 ~/.config/zsh/scripts/validar-acentuacao.py --paths nyx/agent/app.py
/home/andrefarias/.local/bin/ruff check nyx/agent/app.py
```

---

## Criterio binario de aceite

- [ ] selecao no chat copia pro clipboard (copy-on-select), xclip + fallback OSC52
- [ ] scroll/clique/foco da TUI preservados
- [ ] gauntlet rapido + invariantes 14/14; validacao-visual real; spec -> concluidos/  <!-- noqa-acento -->

---

## Riscos

| Risco | Mitigacao |
|-------|-----------|
| API de selecao do Textual limitada na versao em uso | investigar primeiro; se faltar, modo alternativo (atalho copia ultimo bloco) como sub-sprint, sem travar a leva |
| Captura de mouse quebrar scroll | testar scroll/clique apos habilitar selecao; ajustar binding |
| Clipboard nao funcionar headless | OSC52 como fallback portatil; xclip no X11 |

---

*"Codigo que nao da pra copiar e codigo preso atras do vidro." -- anonimo*
