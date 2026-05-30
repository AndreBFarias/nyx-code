# SPRINT 290 — TUI-IMAGE-PASTE-COUNTER-01

## 0. SPEC

```yaml
sprint:
  id: TUI-IMAGE-PASTE-COUNTER-01
  title: "Contador real de imagens coladas no InputWidget: cada paste de [clipboard-image] vira [Image #1], [Image #2], ... (N incremental) em vez do placeholder fixo [Image #?]"
  onda: 34
  prioridade: MEDIA
  tipo: Feature
  dependencias: [TUI-INPUT-TEXTAREA-MULTILINE-01]
  desbloqueia: []

  touches:
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/agent/tui/widgets/input.py
      reason: "Adicionar atributo de instância self._image_count inicializado em __init__; incrementar a cada paste com prefixo [clipboard-image]: e inserir f'[Image #{self._image_count}]' no lugar do placeholder fixo [Image #?]; sincronizar a docstring do módulo (linhas 11, 56-58) e do método paste_text (linhas 143-146) para refletir o contador real."
  creates: []
  removes: []

  forbidden:
    - "Regredir o ghost-completer do slash (sprint 284/286): update_suggestion e o reactive suggestion NÃO são tocados; digitar '/' continua mostrando sugestão dim aceitável por Tab"
    - "Regredir o multiline/submit da sprint 286: o override _on_key (enter=submit / ctrl+j=newline / tab=aceita ghost) NÃO muda; paste_text continua usando self.insert (migrado na 286), só o TEXTO inserido muda"
    - "Regredir o histórico navegável da sprint 289: a sprint 289 vive 100% em app.py; este touch é só input.py, logo o store de histórico não é afetado"
    - "Mudar a assinatura pública de InputWidget.__init__ (slash_completer, on_submit, placeholder, id) — app.py:432 chama paste_text e cli.py instancia com esses kwargs"
    - "Tocar app.py, chat_message.py, banner.py, toolbar.py, nyx.tcss, _core.py, _iteration.py, proxy.py, nyx/cli.py"
    - "Adicionar dependência externa (só textual 8.2.7 já instalado)"
    - "Introduzir hex de cor hardcoded; adicionar emoji ou menção a IA externa"

  tests:
    - cmd: "./run.sh --smoke"
      timeout: 15
      deve_passar: true
    - cmd: "bash scripts/sprint_invariants.sh"
      timeout: 60
      deve_passar: true

  acceptance_criteria:
    - "InputWidget.__init__ inicializa self._image_count = 0"
    - "paste_text com prefixo [clipboard-image]: incrementa o contador e insere [Image #N] com N >= 1 (primeira imagem vira [Image #1], NÃO [Image #?])"
    - "Dois pastes de imagem consecutivos produzem buffer [Image #1][Image #2] (contador incremental, acumulativo na sessão)"
    - "paste_text com texto comum (sem o prefixo) continua inserindo o texto literal via self.insert, sem mexer no contador"
    - "Ghost-completer do slash preservado (anti-regressão 284/286); multiline/submit preservado (anti-regressão 286); histórico navegável preservado (anti-regressão 289 — input.py não toca o store de app.py)"
    - "Nenhuma ocorrência residual do literal [Image #?] em input.py (rg confirma diff)"
    - "smoke boot ok; invariantes 14/14 FAIL=0; gauntlet --only rapido + loop APROVADO; acentuação rc=0"
```

---

## Contexto

A migração ONDA-32 (prompt_toolkit -> Textual) e a reconstrução do `InputWidget` (sprints 202/286) deixaram o paste de imagem com um placeholder FIXO `[Image #?]`: toda imagem colada via Ctrl+V (caminho VISION-02 / `action_paste` em `app.py:418-433`) mostra o mesmo `?`, sem distinguir a 1ª da 2ª. A auditoria ONDA-34 (`~/.claude/plans/redesign-auditoria-da-tender-beacon.md`) cataloga "[Image #N] counter real — DEGRADADO: placeholder fixo [Image #?]"; o `SPRINT_ORDER_MASTER.md` (linha 816) lista "image-counter" entre os itens PENDENTES para IDs 290+, e a própria sprint 286 já registrou "image-counter real" como NÃO-OBJETIVO da onda (spec 286, seção Riscos), explicitando que vira sprint separada — esta. O fix é cirúrgico: um contador de instância no widget.

### Verificação do código real (lição 4 — confirmado via leitura, não suposição)

`nyx/agent/tui/widgets/input.py` (estado no commit base 3dc7018):

- `class InputWidget(TextArea)` (linha 36) — base TextArea desde a sprint 286.
- `__init__` (linhas 67-87): cria `self._slash_full`, chama `super().__init__(...)`, guarda `self._on_submit`. **Não** há `self._image_count` hoje.
- `paste_text` (linhas 140-151), código real verbatim:

  ```python
  def paste_text(self, text: str) -> None:
      ...
      if text.startswith("[clipboard-image]:"):
          self.insert("[Image #?]")
      else:
          self.insert(text)
  ```

  Confirma a auditoria: placeholder FIXO `[Image #?]`. A sprint 286 já migrou `insert_text_at_cursor` -> `self.insert` aqui, então a mudança é SÓ o texto inserido (string fixa -> f-string com contador). `rg -n "insert_text_at_cursor" nyx/agent/tui/widgets/input.py` retorna vazio (confirmado).

- Caller único de `paste_text`: `nyx/agent/tui/app.py:432` (`input_widget.paste_text(text)`, dentro de `action_paste`). `grep -rn "paste_text" --include="*.py" nyx/` retorna exatamente esses 2 sites (definição + caller). O caller passa o texto cru do clipboard; o prefixo `[clipboard-image]:` é convenção interna do paste — esta sprint NÃO toca o caller.

### Semântica do reset do contador (decisão de escopo)

O `self.clear()` que limpa o buffer ocorre no `_on_key` ao submeter (Enter, linha 126). Há duas leituras possíveis:

- **(A) Acumulativo na sessão** — o contador nunca reseta; vive enquanto a instância do `InputWidget` viver (uma instância por sessão da TUI). Cada imagem colada na sessão recebe um N único e monotônico.
- **(B) Reset por turno/submit** — zerar `self._image_count` no `clear()`/submit, fazendo a numeração recomeçar a cada mensagem enviada.

**Decisão: (A) acumulativo na sessão.** Justificativa (GUIDE.md §2 simplicidade): é o mínimo viável — um único atributo inicializado no `__init__` e incrementado no `paste_text`, sem acoplar ao ciclo de submit nem tocar `_on_key`/`clear`. A ideia da auditoria pede apenas "N incremental, não `?`"; numeração monotônica por sessão satisfaz isso e é a interpretação mais simples e suficiente. A opção (B) introduziria acoplamento ao `clear()` (que também é chamado por outros caminhos, ex. recall) sem ganho funcional claro. Se no uso real surgir necessidade de reset por turno, vira sprint nova com ID (MEMORY "Nenhum débito fica para trás") — não absorver implicitamente.

## Escopo (touches autorizados)

- Arquivos a modificar:
  - `/home/andrefarias/Desenvolvimento/Nyx-Code/nyx/agent/tui/widgets/input.py` — (1) inicializar `self._image_count: int = 0` no `__init__`; (2) em `paste_text`, no ramo do prefixo `[clipboard-image]:`, incrementar `self._image_count` e inserir `f"[Image #{self._image_count}]"`; (3) sincronizar as docstrings que ainda descrevem o placeholder fixo (módulo: linha 11 "como `[Image #N]`" já fala N mas o corpo da docstring de classe linhas 56-58 e do método linhas 143-146 dizem `[Image #?]`/"número real calculado por caller externo em sprint futura" — atualizar para refletir o contador interno desta sprint).
- Arquivos a criar: nenhum.
- Arquivos NÃO a tocar: `app.py` (caller de `paste_text`, intocado — a numeração é interna ao widget), `chat_message.py`, `banner.py`, `toolbar.py`, `nyx.tcss`, `nyx/cli.py`, `loop/_core.py`, `loop/_iteration.py`, `proxy.py`.

## Acceptance criteria

1. `rg -n "_image_count" nyx/agent/tui/widgets/input.py` mostra o atributo inicializado em `__init__` e incrementado em `paste_text`.
2. `rg -n "Image #\?" nyx/agent/tui/widgets/input.py` retorna vazio (o literal fixo `[Image #?]` foi removido do código; a docstring pode citá-lo só como referência histórica se necessário, mas sem o placeholder ativo).
3. Instanciar o widget e chamar `paste_text("[clipboard-image]:/tmp/x.png")` duas vezes resulta em buffer (`.text`) == `[Image #1][Image #2]` (contador incremental, primeira imagem == 1).
4. `paste_text("ola mundo")` (texto comum) insere `ola mundo` literal e NÃO altera `self._image_count`.
5. Anti-regressão 284/286: digitar `/` mostra ghost dim, Tab aceita; Enter submete + limpa, Ctrl+J insere newline (não tocamos `_on_key`/`update_suggestion`).
6. Anti-regressão 289: `nyx/agent/tui/app.py` permanece com diff ZERO (o store de histórico não é afetado; `git diff --stat` lista só `input.py`).
7. smoke boot ok; invariantes 14/14 FAIL=0; gauntlet `--only rapido` + loop APROVADO; acentuação rc=0.

## Invariantes a preservar

- **Ghost-completer (sprint 284/286)**: `update_suggestion` e o reactive `suggestion` não são tocados. A mudança é só o texto inserido no ramo de imagem do `paste_text`.
- **Multiline / Enter=submit / Ctrl+J=newline (sprint 286)**: o override `_on_key` (linhas 109-138) permanece intocado; `paste_text` continua delegando a inserção a `self.insert` (migração da 286 preservada).
- **Histórico navegável (sprint 289)**: o store (`_input_history`, `_history_idx`, `_history_draft`) vive em `app.py`; este touch é só `input.py`. `app.py` deve ficar com diff zero.
- **Assinatura pública de `InputWidget.__init__`**: `slash_completer`, `on_submit`, `placeholder`, `id` — não adicionar/remover/reordenar kwargs. O `_image_count` é estado interno, não parâmetro.
- **Check #14 (anti-sanitizer)**: `input.py` NÃO está entre os 7 arquivos protegidos (`nyx/cli.py`, `design_tokens.py`, `output.py`, `banner.py`, `repl_app.py`, `design_tokens_extended.py`, `sprint_invariants.sh`). Sem glifo canônico em risco; mudança não afeta a defesa.
- **Check #6 (zero hex)**: nenhuma cor introduzida; só texto `[Image #N]`.
- **GUIDE.md §2 (simplicidade) e §3 (mudanças cirúrgicas)**: um atributo + uma f-string + sincronização de docstring. Não construir contador global, registry de imagens, nem reset por turno (escopo fora — ver Riscos).
- **MEMORY "Nenhum débito fica para trás"**: se durante a execução aparecer necessidade de reset por turno ou de propagar o N para o índice de imagens (`~/.nyx/image_index.json`, VISION-02), registrar como sprint nova com ID, nunca absorver.

## Plano de implementação

1. Em `input.py` `__init__` (após `self._on_submit = on_submit`, linha 87): adicionar `self._image_count: int = 0` com comentário curto ("contador monotônico de imagens coladas na sessão; vira [Image #N] em paste_text").
2. Em `paste_text` (linhas 140-151): no ramo `if text.startswith("[clipboard-image]:"):`, trocar `self.insert("[Image #?]")` por:
   ```python
   self._image_count += 1
   self.insert(f"[Image #{self._image_count}]")
   ```
   O ramo `else: self.insert(text)` permanece igual.
3. Sincronizar docstrings (mudança de documentação, não de comportamento):
   - Docstring de classe, item `paste_text(text)` (linhas 56-58): trocar "insere placeholder `[Image #?]` (lógica de N delegada ao caller via futura sprint)" por descrição do contador interno (`[Image #N]`, N incremental por sessão).
   - Docstring do método `paste_text` (linhas 143-146): trocar "substituímos pelo placeholder visível `[Image #?]`. O número real é calculado por um caller externo em sprint futura." por "substituímos por `[Image #N]`, onde N é um contador monotônico de instância incrementado a cada imagem colada na sessão (TUI-IMAGE-PASTE-COUNTER-01)."
   - Manter PT-BR acentuado em qualquer texto novo (docstrings em PT-BR já predominam no arquivo).
4. Rodar smoke + invariantes + acentuação. Rodar a validação funcional do método (ver Proof-of-work). Rodar gauntlet `--only rapido` + loop (disciplina OOM: 1 execução).

## Aritmética

Sem meta de redução de linhas (`<NL`). Saldo informativo:

- `input.py`: `+1` linha no `__init__` (atributo) `+1` comentário; no `paste_text` o ramo de imagem passa de 1 linha para 2 (`+1`); sincronização de docstring é reescrita in-place (saldo ~0, pode variar `±1`). Net esperado: `~ +3` a `+4` linhas em `input.py`. Arquivo atual: 155 linhas (verificado) -> projetado ~158-159 linhas. Sem alvo a fechar; aritmética puramente informativa.

## Testes

- Não há suíte pytest cobrindo `InputWidget`: `grep -rln "InputWidget|paste_text|clipboard-image" tests/` retorna vazio (confirmado). Além disso, ADR-014 (testes só via Gauntlet) removeu o `test_input_widget.py` standalone da sprint 202 (ver MASTER entry 202, Erratum 2026-05-25). Portanto NÃO criar arquivo de teste pytest novo.
- Verificação primária funcional: snippet direto/headless (ver Proof-of-work) que instancia o widget e chama `paste_text` 2x — execução manual no proof-of-work, não arquivo commitado.
- Cobertura estrutural: smoke + invariantes + gauntlet `--only rapido` (que exercita o widget via integração, conforme Erratum 202).
- Baseline: `FAIL_BEFORE` = estado atual de `sprint_invariants.sh` (esperado 0). Esperado `FAIL_AFTER` == `FAIL_BEFORE` == 0 (registrar números reais).

## Proof-of-work esperado

- Diff final de `input.py` (touch único).
- **Validação funcional do contador (núcleo da auditoria)** — paste de imagem real depende de clipboard/Ctrl+V/X11 (difícil de injetar via `/control/repl/send` no `--web`); validar por teste direto do método OU via Textual Pilot headless. Opção A (direta, preferida pela simplicidade), executar e colar a saída:
  ```bash
  ./venv/bin/python - <<'PY'
  from nyx.agent.tui.widgets.input import InputWidget
  w = InputWidget()
  assert w._image_count == 0, w._image_count
  # paste de imagem fora de App: self.insert pode exigir contexto;
  # se NoActiveAppError, exercitar a lógica do contador isoladamente
  # confirmando incremento e a f-string [Image #N].
  PY
  ```
  Se `self.insert` exigir App context (precedente sprint 202: `paste_text` fora de App levanta `NoActiveAppError`), usar Textual Pilot headless (`App.run_test()` montando a TUI, focar o `#input`, chamar `paste_text("[clipboard-image]:/tmp/x.png")` 2x e asserir `.text == "[Image #1][Image #2]"`). O executor escolhe o caminho que roda limpo; a meta é comprovar empiricamente: 1º paste -> `[Image #1]`, 2º paste -> `[Image #2]` (contador incrementa, primeira == 1, não `?`), e que `paste_text("texto")` não mexe no contador.
- Runtime real (BRIEF seção `[CORE] Contratos de runtime`):
  - Smoke: `./run.sh --smoke` -> `boot ok`, exit 0.
  - Invariantes: `bash scripts/sprint_invariants.sh` -> 14/14, FAIL=0.
  - Gauntlet: `./run.sh --gauntlet --only rapido` + loop -> APROVADO. **Disciplina OOM (RTX 3050 4GB)**: 1 execução fresca após VRAM livre (BRIEF aceita 1 run de rápido + cruzar com `--only proxy` se aparecer o flake conhecido `INFRA-OOM-PATTERNS-KV-CACHE-01`); sem paralelismo; cleanup de processos/VRAM por PID ao final.
- Validação visual (`--web`): OPCIONAL/best-effort. Como o paste de imagem real depende do clipboard do host (não injetável de forma confiável pelo proxy do cockpit), a validação canônica desta sprint é a funcional acima (método/Pilot). Se viável, um print do `--web` mostrando `[Image #1]`/`[Image #2]` no buffer reforça, mas não é bloqueante.
- Acentuação periférica: `python3 /home/andrefarias/.config/zsh/scripts/validar-acentuacao.py --paths nyx/agent/tui/widgets/input.py` -> rc=0 (varrer também este spec).
- Hipótese verificada (lição 4): `rg -n "paste_text" --include="*.py" nyx/` mostra só `input.py` (def) + `app.py:432` (caller); `rg -n "insert_text_at_cursor" nyx/agent/tui/widgets/input.py` vazio (migração 286 já feita); `rg -n "Image #\?" nyx/agent/tui/widgets/input.py` vazio APÓS o fix.

## Riscos e não-objetivos

- **Risco BAIXO — `self.insert` fora de App context**: chamar `paste_text` num `InputWidget` não montado pode levantar `NoActiveAppError` (precedente sprint 202). Mitigação: validar via Pilot headless (widget montado) em vez de instanciação nua, OU exercitar a lógica do contador de forma isolada. Não é regressão; é só a escolha do harness de prova.
- **Não-objetivo — reset por turno/submit**: a numeração é acumulativa na sessão (decisão A). Reset por mensagem é escopo separado; se pedido, sprint nova com ID.
- **Não-objetivo — propagar o N para o índice de imagens**: a integração do `[Image #N]` com `~/.nyx/image_index.json` / `_expand_images` / `_persist_image_index` (VISION-02, MASTER entry 48) já existe no pipeline do agente e NÃO é tocada aqui; esta sprint só corrige o texto visível no buffer de input. Alinhar o N do buffer com o N do índice de visão, se divergir, é sprint separada.
- **Não-objetivo — tocar o caller `app.py:432`**: a numeração é interna ao widget; o caller continua passando o texto cru do clipboard.

## Referências

- BRIEF: `/home/andrefarias/Desenvolvimento/Nyx-Code/VALIDATOR_BRIEF.md` (Contratos de runtime; flake OOM do gauntlet rápido `INFRA-OOM-PATTERNS-KV-CACHE-01`; lista dos 7 arquivos protegidos do check #14 — `input.py` não está).
- Plano da onda: `~/.claude/plans/redesign-auditoria-da-tender-beacon.md` (item "[Image #N] counter real — DEGRADADO").
- Código real verificado: `nyx/agent/tui/widgets/input.py` linhas 67-87 (`__init__`), 140-151 (`paste_text`); caller `nyx/agent/tui/app.py:418-433` (`action_paste`).
- Precedentes a NÃO regredir: sprint 284 (commit 4fe225f, ghost-completer), sprint 286 (commit 3e31739, TextArea multiline + `insert`), sprint 289 (histórico navegável, vive em app.py).
- Precedente do widget e ADR-014: MASTER entry 202 (TEXTUAL-INPUT-WIDGET-01, cria `paste_text` com `[Image #?]`; Erratum 2026-05-25 removeu o teste standalone por ADR-014).
- MASTER: `dev-journey/06-sprints/SPRINT_ORDER_MASTER.md` (linha 816 lista "image-counter" entre PENDENTES IDs 290+; bloco `MANUAL_OVERRIDE_ONDA_34` linhas 795-818).
- Base estável: commit 3dc7018.
