# Desenho arquitetural -- Contrato de Execução (fase raiz da ONDA-48)

**Data:** 2026-06-26
**Autor:** Opus (cérebro), no fechamento das quick wins da ONDA-48.
**Status:** DESENHO (as 7 specs detalhadas saem deste documento, em sessão dedicada).
**Candidato a:** ADR-035 (formalizar quando a primeira sprint da fase raiz fechar).

> Este documento dá a **visão coesa** das sprints 397-403. Elas não são 7 fixes isolados --
> são pedaços de **um mecanismo único ausente** na cadeia. Cada spec detalhada referencia
> este desenho para não divergir.

---

## 1. Tese: 7 bugs, 1 mecanismo ausente

A onda de validação (`AUDIT_VALIDACAO_2026_06_26.md`) achou 15 bugs. As quick wins (393-396)
mataram os 4 visíveis (gating, identidade, vazamentos, banner). Sobrou um **núcleo coeso**: a
cadeia `parser -> loop -> tool -> resposta` **confia cegamente no que o modelo cospe**. Ela:

1. executa um tool_call **sem validar** se está bem-formado (V02: path com crase, content vazio);
2. executa a tool que o modelo escolheu **sem checar** se ela casa o pedido (V03: listar -> write_file);
3. quando o parser **falha** em extrair o tool_call, joga o texto cru como resposta (V07) em vez de executar ou falhar honesto;
4. aceita o modelo **afirmar** "criado/sucesso/listado" **sem** ter chamado a tool no turno (V04, V14);
5. realimenta o **resultado** de uma tool como **conteúdo** da próxima (V06: write recursivo);
6. deixa `write_file` **sobrescrever** um arquivo existente numa edição sequencial (V05).

A validação as-user pós-quick-wins confirmou a tese: a Nyx agora **age** (fastfetch dispara,
cria arquivo no lugar certo), mas **não apresenta** o resultado (rodou fastfetch e divagou sobre
memória; listou e não mostrou os arquivos). **Ação curada pelas quick wins; apresentação e
integridade da execução são este contrato.**

ADR-032 (a infra carrega o modelo) exige que a infra **garanta** o comportamento certo -- não
que confie no 3b. O contrato de execução é como a infra honra isso no ponto de execução.

---

## 2. O fluxo atual e os 4 pontos de intervenção

```
modelo -> content/tool_calls
   |
   +-- [D] parser.parse(content)            nyx/agent/loop/_core.py:446   (fallback quando sem tool_calls nativo)
   |
   +-- _execute_tool_calls(...)             nyx/agent/loop/_iteration.py:199
   |   _execute_parsed_action(...)          nyx/agent/loop/_iteration.py:365
   |        |
   |        +-- [A] (pré-execução)          ANTES de self._tools.execute (linha 309 e 438)
   |        +-- self._tools.execute(name,args)   <-- execução real
   |        +-- [B] (pós-execução)          resultado -> _on_tool_result (linha 336) / vai ao contexto
   |
   +-- [C] guard de done/resposta           _core.py:300-320 (já tem strip + force_done #351)
```

- **[A] Pré-execução** (`_iteration.py` ~309/438, imediatamente antes de `self._tools.execute`):
  validar e, se possível, **sanitizar** o tool_call; ou rejeitar e **re-emitir** com hint.
- **[B] Pós-execução** (logo após `execute`, antes de o resultado ir ao contexto/summary):
  garantir que o resultado seja **apresentado** e **não** realimentado como input.
- **[C] Guard de resposta/done** (`_core.py` guard de saída): bloquear **afirmação sem execução**.
- **[D] Parser-fail** (`_core.py:446`): quando o parser não extrai, **tentar executar** o
  candidato ou **falhar honesto** -- nunca jogar o tool_call cru como resposta.

---

## 3. O contrato: 3 garantias

> "Toda tool executada é bem-formada e pertinente; todo resultado afirmado foi realmente
> produzido; todo resultado produzido é apresentado ao usuário."

### Garantia G1 -- Tool bem-formada e pertinente (ponto A)
Antes de executar: (a) os args casam o schema (path sem lixo de markdown, `content` não-vazio
quando a tool exige, sem comando-shell-como-conteúdo); (b) a tool casa a **intenção** do pedido
(pediu listar/ler -> não é `write_file`/`create_file`). Se malformado: sanitizar o reparável
(strip de crase/aspas no path) ou re-emitir 1x com hint forte (espelhar MEMORY-INTENT-ENFORCE).

### Garantia G2 -- Resultado afirmado = resultado produzido (pontos C, D)
O turno só conclui `done`/sucesso se houve **execução real** coerente com a afirmação. "Arquivo
criado" exige um `write_file`/`edit_file` bem-sucedido no turno (o guard #351 cobre parte disso
-- estender para leitura/listagem/comando). Se o parser falhou e o content é um tool_call cru,
executar o candidato; se não der, mensagem honesta -- nunca o JSON/`tool(args)` cru.

### Garantia G3 -- Resultado produzido é apresentado (ponto B)
O conteúdo que a tool retornou **entra na resposta** ao usuário (a lista de arquivos, a saída do
fastfetch, o trecho lido) -- não some num "concluído" nem é trocado por divagação. E o resultado
de uma tool **nunca** vira `content` de outra (anti-recursão).

---

## 4. Mapa: sprint -> garantia -> ponto -> achado

| Sprint | Garantia | Ponto | Achado | Essência do fix |
|--------|----------|-------|--------|-----------------|
| 397 EXEC-CONTRACT-TOOLCALL-SANITIZE | G1 | A | V02 | sanitizar args (path sem crase/aspas; rejeitar content vazio quando exigido) antes de `execute` |
| 398 EXEC-CONTRACT-TOOL-MATCH | G1 | A | V03 | classificar a intenção do pedido (ler/listar/buscar/escrever/rodar) e rejeitar+re-emitir quando a tool chamada contradiz (listar->write_file) |
| 399 EXEC-CONTRACT-NO-HALLUCINATED-RESULT | G2 | C, D | V04, V07, V14 | done/sucesso só com execução real no turno; parser-fail executa o candidato ou falha honesto (não cospe cru) |
| 400 LOOP-RESULT-NOT-AS-INPUT | G3 | B | V06 | nunca usar o output de uma tool como `content`/arg da próxima (quebra a recursão write->write) |
| 401 SEQ-EDIT-ENFORCE-EDITFILE | G1 | A | V05 | arquivo JÁ existe + intenção de "adicionar/alterar" -> forçar `edit_file` (ou read-before-write); `write_file` cego sobrescreve |
| **402 MEMORY-RECALL-REFRESH** | (satélite) | -- | V11 | `_core.py:145` recarrega `_memory_bundle` após `write_memory`/`reset` -- independente do contrato |
| **403 MODEL-SWAP-REAL-OR-HONEST** | (satélite) | -- | V13 | feature de troca real de model OU resposta honesta -- independente; liga ao roadmap ONDA-49 |

**Núcleo do contrato:** 397, 398, 399, 400, 401 (tocam o fluxo de execução no loop).
**Satélites:** 402 (memória) e 403 (model) são independentes -- podem ir antes/depois sem
acoplar ao contrato.

---

## 5. Ordem de implementação e dependências

1. **399 primeiro** (G2): é a que mais muda a experiência (a Nyx parar de afirmar sem fazer e
   passar a apresentar o resultado). Cobre V04/V07/V14. Estabelece o esqueleto do contrato no
   ponto C/D.
2. **397** (G1 args) e **400** (G3 anti-recursão): pequenas, cirúrgicas, no ponto A/B.
3. **398** (G1 tool-match) e **401** (G1 edit): precisam de um classificador de intenção-de-tool
   leve (reusar `nyx/agent/intent.py`? estender). Mais delicadas -- depois do esqueleto (399).
4. **402** e **403**: satélites, a qualquer momento (402 é trivial: 1 linha em `_core.py`).

Cada sprint mantém o proof-of-work runtime-real: reproduzir o probe as-user do achado e provar
que a Nyx agora age+apresenta. A validação as-user em sessão contínua (como esta onda fez) é o
juiz final -- não o proof isolado.

---

## 6. Princípios invioláveis do contrato

- **Não regex-frágil.** A lição da onda é que adivinhar intenção por dicionário de verbos não
  escala. O contrato valida **estrutura** (args bem-formados, execução real) e usa intenção só
  como sinal de re-emissão, nunca como gate único.
- **Não quebrar o que funciona.** As quick wins, o bloqueio de segredos, o write_memory, a
  cascata OOM seguem intactos. O contrato é uma camada de validação **aditiva**.
- **Enforcement, não confiança** (ADR-032/033). Quando o modelo erra, a infra **corrige ou
  re-emite** -- não repassa o erro ao usuário nem o aceita como sucesso.
- **Honestidade na falha.** Se a infra não consegue garantir, a mensagem ao usuário é clara
  ("não consegui X porque Y") -- nunca um sucesso fabricado nem um formato interno cru.

---

## 7. O que NÃO é o contrato (escopo negativo)

- Não é mudar o modelo nem trocar de placa (ADR-032).
- Não é o gating de tools (393, feito) nem o few-shot (404, feito) -- esses **dão** a ferramenta;
  o contrato garante que a ferramenta **dada** seja usada certo.
- Não é a TUI render (406) -- essa é a borda visual; o contrato é a borda de execução.

---

*"Confiar é barato; garantir é o trabalho. A infra que serve quem não tem A100 garante." -- princípio de execução*
