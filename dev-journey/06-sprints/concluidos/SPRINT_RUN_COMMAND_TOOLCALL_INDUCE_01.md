## 0. SPEC (machine-readable)

```yaml
sprint:
  id: RUN-COMMAND-TOOLCALL-INDUCE-01
  title: "run_command ganha few-shot no prompt (como write_memory) -> modelo emite o tool_call em vez de ecoar o comando"
  onda: 48
  prioridade: ALTA
  tipo: Bugfix
  dependencias: [TOOL-GATING-NO-SUPPRESS-01]
  desbloqueia: []

  touches:
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/agent/prompt.py
      reason: "build_system_prompt da few-shot a write_memory mas NAO a run_command; o 3b ecoa o comando como texto"
      linhas_alvo: "105-143"
  creates: []
  removes: []

  forbidden:
    - "Adicionar emoji"
    - "Inflar o prompt compact (build_system_prompt_compact) -- few-shot so no prompt FULL com tools"
    - "Mencao a IA proprietaria"
    - "Quebrar o few-shot existente de write_memory"

  tests:
    - cmd: "./run.sh --gauntlet --only rapido"
      timeout: 300
      deve_passar: true

  acceptance_criteria:
    - "PROOF END-TO-END (par 393+404): 'da um fastfetch e me fala as specs' -> emite tool_use run_command(command~='fastfetch') E apresenta specs REAIS (Ryzen 5 7535HS / RTX 3050 / Pop!_OS)"
    - "Pelo menos 2/3 amostras do mesmo prompt emitem o tool_call (o 3b e estocastico; meta >= 2/3)"
    - "Few-shot de write_memory intacto (regressao: 'lembra que X' ainda chama write_memory)"
    - "Gauntlet --only rapido 100%; ruff limpo; acentuacao rc=0"
```

---

# Sprint RUN-COMMAND-TOOLCALL-INDUCE-01 — run_command ganha few-shot (par da 393)

**Status:** PENDENTE
**Data criação:** 2026-06-26
**Modelo obrigatório:** claude-opus-4-7 (executor-sprint autorizado pelo dono nesta onda)

---

## Contexto do projeto (snapshot)

> **ADRs:** ADR-032 A INFRA CARREGA O MODELO (a infra induz o modelo a agir; "teto do modelo" e atalho proibido), ADR-033 (cadeia nao quebra), ADR-031 (qwen2.5-coder:3b), ADR-006 PT-BR, ADR-014 Gauntlet.
> **Estado (2026-06-26):** ONDA-48. **Esta sprint e o PAR da 393.** A 393 (no working tree, nao commitada) tirou a supressao de tools no intent chat -> a tool `run_command` JA chega ao modelo (provado: tools=0 -> tools=5 no proxy.log). Mas o qwen2.5-coder:3b ECOA o comando como texto ("fastfetch --all -c") em vez de emitir o tool_call (0/3 amostras com tool_use). Causa: `nyx/agent/prompt.py` da few-shot a `write_memory` (que funciona) mas NAO a `run_command`.

---

## Problema

**Achado V01 (2ª camada), provado pelo executor da 393 (2026-06-26).** Com as tools disponiveis no chat, o prompt "da um fastfetch e me fala as specs" produz:
```json
{"type": "response", "summary": "fastfetch --all -c", "files_modified": 0}  // 3/3 amostras, ZERO tool_use
```
O modelo gera o comando CERTO mas como **texto**, sem embrulhar em tool_call. `proxy.log`: `Ollama tool_calls: NONE`, `<- text: fastfetch...`.

Contraste: `write_memory` funciona ("lembra que X" -> chama a tool) porque `prompt.py:112-122` tem **few-shot explicito** dele. `run_command` so aparece listado em `prompt.py:108` ("Executar comando (run_command)") -- sem exemplo de formato. O parser (7 niveis) nao reconhece "fastfetch --all -c" como run_command (e nem deveria adivinhar texto livre).

---

## Solução proposta

Dar a `run_command` o mesmo tratamento de `write_memory`: um **few-shot explicito** no `build_system_prompt` (prompt FULL, com tools) instruindo a embrulhar comandos do sistema em `run_command` e a apresentar a saida real depois. Fix de **indução** (ADR-032), nao de capacidade.

---

## Arquivos alvo (paths absolutos)

### `/home/andrefarias/Desenvolvimento/Nyx-Code/nyx/agent/prompt.py`

# Localização aproximada: logo após o bloco few-shot de write_memory (~linha 122),
# dentro do f-string de build_system_prompt (NAO no compact).
**Antes (âncora -- o bloco write_memory existente):**
```python
Exemplos que NÃO disparam write_memory:
  "você lembra do arquivo X?" (pergunta, não ordem)
  "lembra de rodar o teste" (instrução de ação, não fato a persistir)
  "lembro que ontem..." (relato passado, não pedido)
```

**Depois (adicionar logo após o bloco acima):**
```python
Exemplos que NÃO disparam write_memory:
  "você lembra do arquivo X?" (pergunta, não ordem)
  "lembra de rodar o teste" (instrução de ação, não fato a persistir)
  "lembro que ontem..." (relato passado, não pedido)

DISPARE run_command SEMPRE que o usuário pedir para rodar/executar/dar um
comando ou ferramenta do sistema (fastfetch, ls, git, python, cat, etc.).
NUNCA escreva o comando como texto para o usuário rodar -- CHAME a tool para
EXECUTAR e depois apresente a saída REAL.
Exemplo de disparo OBRIGATÓRIO:
  Usuário: "da um fastfetch e me fala as specs do pc"
  Chame run_command com:
    command="fastfetch"
  Depois apresente a saída real (CPU, GPU, RAM que a tool retornou) -- nunca invente specs.
```

**Mudanças:** few-shot de `run_command` espelhando o de `write_memory`; reforça "execute, não escreva o comando" e "apresente a saída real" (ataca também a alucinação de specs).

---

## Diff esperado (resumo)

```
~ 1 arquivo modificado (nyx/agent/prompt.py)
+ ~10 linhas líquidas (string do few-shot)
```

---

## Comandos de verificação (literais, copy-paste)

```bash
# 1. Static + acentuação
python -m ruff check nyx/
python3 ~/.config/zsh/scripts/validar-acentuacao.py --paths nyx/agent/prompt.py

# 2. PROOF END-TO-END (par 393+404 no working tree). Roda 3 amostras:
for i in 1 2 3; do
  printf '%s\n' '{"type":"request","content":"da um fastfetch e me fala as specs do pc atual"}' \
    | NYX_AUTO_APPROVE=1 ./run.sh --headless 2>/dev/null | grep -E 'tool_use|summary'
done
# ESPERADO: >= 2/3 amostras com {"type":"tool_use","tool":"run_command",...} e specs REAIS
#           (Ryzen 5 7535HS / RTX 3050 / Pop!_OS). COLE as 3 saidas.

# 3. Regressão write_memory (não pode quebrar):
printf '%s\n' '{"type":"request","content":"lembra que eu uso Pop OS 22.04 neste setup"}' \
  | NYX_AUTO_APPROVE=1 ./run.sh --headless 2>/dev/null | grep tool_use
# ESPERADO: {"type":"tool_use","tool":"write_memory",...}

# 4. Gauntlet
./run.sh --gauntlet --only rapido
```

---

## Critério binário de aceite

- [ ] Few-shot de `run_command` adicionado ao prompt FULL (não ao compact)
- [ ] Proof end-to-end: >= 2/3 amostras do fastfetch emitem `run_command` + specs reais (colar as 3 saídas)
- [ ] Regressão: `write_memory` ainda dispara em "lembra que X"
- [ ] ruff limpo, acentuação rc=0, invariantes FAIL_AFTER <= FAIL_BEFORE, gauntlet rapido 100%
- [ ] **393 E 404** marcadas CONCLUIDAS no MASTER; ambas as specs movidas para concluidos/
- [ ] **Commit ÚNICO do par** (393+404): `fix(loop+prompt): 393+404 -- chat recebe tools e run_command vira tool_call (V01)` -- SEM push, SEM menção a IA

---

## Guardrails anti-engodo

NÃO concluir se: o proof end-to-end não foi colado (3 saídas reais); < 2/3 amostras agem; o few-shot foi posto no prompt compact (não tem efeito em turno com tools); quebrou write_memory; gauntlet "passou" sem output. Se < 2/3 mesmo com o few-shot: escalar para enforcement no proxy (espelhar MEMORY-INTENT-ENFORCE para run_command) e reportar como achado para nova sprint -- NÃO marcar concluída com proof fraco. Falha -> `[SPRINT 404] BLOQUEADA: <motivo>`.

---

## Proof-of-work (4 passos)

inv_before -> implementar -> inv_after (<=) -> diff. Como a 393 já está no working tree, o inv_before reflete o estado com a 393 aplicada. Colar tail de ambos + diff + as 3 saídas do proof end-to-end + a saída da regressão write_memory + `git show --stat HEAD` (commit do par).

---

## Riscos

| Risco | Mitigação |
|-------|-----------|
| Few-shot não basta (3b ignora) | Critério aceita >= 2/3 (não 3/3, dado o estocástico). Se < 2/3, escalar para enforcement no proxy (sprint nova) -- não forçar conclusão. |
| Prompt incha (mais tokens no input) | ~10 linhas; o prompt FULL já carrega schema de tools. Trade-off aceito (ADR-009). |
| Modelo passa a chamar run_command demais (até em conversa) | A 393 já dá tools ao chat; a 399 (no-hallucinated-result) e o classifier limitam. Monitorar; o few-shot foca em "pedir para rodar/executar". |

---

*"Mostrar o caminho uma vez vale mais que cobrar o destino dez." -- princípio de indução*
