# SPRINT VALIDATE-FINAL-01 — Validação end-to-end de paridade e release v1.0

## 0. SPEC (machine-readable)

```yaml
sprint:
  id: VALIDATE-FINAL-01
  title: "Validação end-to-end de paridade com CLI de referência e critério de release v1.0"
  onda: 22
  bloco: 9
  prioridade: CRÍTICA
  tipo: Audit
  dependencias: [UX-EXTRA-01, DEPLOY-02, VISION-03, DOC-CONSOLIDATE-01]
  desbloqueia: [tag v1.0]

  touches:
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/dev-journey/06-sprints/SPRINT_ORDER_MASTER.md
      reason: "Marcar Onda 22 como release ready e adicionar linha de aceite final"
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/GUIDE.md
      reason: "Adicionar seção 'v1.0 critérios de aceite' com os 30 itens de paridade e gate de gauntlet 100%"

  creates:
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/dev-journey/07-reports/RELATORIO_VALIDATE_FINAL_01.md
      reason: "Relatório canônico com outputs, screenshots anexados e resultado por checklist"
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/dev-journey/07-reports/CHECKLIST_PARIDADE_CLAUDE_CODE.md
      reason: "Tabela binária de ~30 itens de paridade visual e funcional; arquivo consultado pelo relatório"

  removes: []

  n_to_n_pairs:
    - descricao: "Critério de release v1.0 aparece em GUIDE.md, SPRINT_ORDER_MASTER.md e no relatório; precisam bater"
      paths:
        - /home/andrefarias/Desenvolvimento/Nyx-Code/GUIDE.md
        - /home/andrefarias/Desenvolvimento/Nyx-Code/dev-journey/06-sprints/SPRINT_ORDER_MASTER.md
        - /home/andrefarias/Desenvolvimento/Nyx-Code/dev-journey/07-reports/RELATORIO_VALIDATE_FINAL_01.md

  forbidden:
    - "Declarar sprint concluída após 1 única execução — requer 5 runs de benchmark de start"
    - "Declarar item de paridade OK sem screenshot anexado no relatório"
    - "Validar só o automático (gauntlet) — itens visuais precisam de olho humano registrado"
    - "Pular o install em VM Docker Ubuntu 22.04 limpa — reusar o procedimento de PORT-02"
    - "Marcar tool como exercitada sem log do fluxo natural que a invocou"
    - "Adicionar emoji ou menção a IA em commits e relatórios"
    - "Path absoluto hardcoded fora dos relatórios (onde é necessário para reprodutibilidade)"

  tests:
    - cmd: "./run.sh --gauntlet"
      timeout: 900
      deve_passar: "100% em todas as fases"
    - cmd: "bash scripts/sprint_invariants.sh"
      timeout: 60
      deve_passar: "FAIL_AFTER <= FAIL_BEFORE"
    - cmd: "./run.sh --smoke"
      timeout: 30
      deve_passar: "imprime 'boot ok'"

  acceptance_criteria:
    - "47 comandos executados sem crash — lista completa com status no relatório"
    - "34 tools exercitadas ao menos uma vez via fluxo natural — log de invocação anexado"
    - "30 itens do CHECKLIST_PARIDADE_CLAUDE_CODE.md marcados OK com screenshot"
    - "Install em VM Docker Ubuntu 22.04 limpa sobe sem erro e REPL responde"
    - "Tempo de start (REPL pronto para input) < 1.5s mediana de 5 runs, com números reais colados"
    - "./run.sh --gauntlet passa 100% em todas as fases"
    - "Acentuação PT-BR correta em todo texto novo"
    - "Zero menção a IA em relatórios e commits"
```

---

**Status:** CONCLUIDA (header corrigido em MASTER-CLEANUP-02 2026-05-20; presença em concluidos/ implica CONCLUIDA conforme convenção do projeto)
**Data criação:** 2026-04-19
**Modelo obrigatório:** claude-opus-4-7 (sem subagentes)

---

## Contexto do projeto (snapshot — não referência)

> **ADRs relevantes:**
> - ADR-001 Local First: tudo offline, Ollama 11435, proxy 11436.
> - ADR-004 Zero Emojis.
> - ADR-005 Anonimato.
> - ADR-006 PT-BR acentuação obrigatória.
> - ADR-010 Zero Mocks: install e benchmark em VM real.
> - ADR-013 Integração Obrigatória.
> - ADR-014 Testes via Gauntlet.
> - ADR-020 Testes via run.sh.
> - ADR-023 Design System (deve estar aplicado até aqui).
> - ADR-024 Render Layer.
>
> **Estado do sistema na data da sprint:**
> - Python 3.10+, modelo qwen3:4b, Ollama 11435, proxy 11436.
> - 34 tools, 47 comandos, 10 services, 24 ADRs vigentes.
> - Esta é a última sprint da Onda 22 antes da tag v1.0.
> - `./run.sh --smoke` imprime `boot ok` (check #13 do invariants).
> - Dependências diretas concluídas: UX-EXTRA-01, DEPLOY-02, VISION-03, DOC-CONSOLIDATE-01.

---

## Problema

Nenhuma sprint anterior validou, em conjunto e em um único ciclo, que o agente alcança os critérios declarados de paridade funcional e visual com a CLI de referência que inspirou o projeto. Cada bloco foi validado em isolamento; regressões cruzadas podem passar despercebidas.

Sem esta auditoria final, a tag v1.0 representa risco: um único comando quebrado entre os 47, uma tool não exercitada, um item de paridade visual regredido ou um tempo de start acima do limite inviabilizam a percepção de "é o Claude Code offline de verdade".

### Sintoma observável

Até o momento, não existe:
- Um relatório único consolidando resultado de todos os comandos.
- Um checklist binário de paridade visual/funcional.
- Um benchmark de start com 5 medições reais.
- Uma prova de que o install em VM limpa funciona.

---

## Solução proposta

Executar auditoria em 5 frentes, materializar tudo em `RELATORIO_VALIDATE_FINAL_01.md`, gerar `CHECKLIST_PARIDADE_CLAUDE_CODE.md` como artefato versionado, e só então desbloquear tag v1.0.

### Frente 1 — Comandos (47)

Para cada comando em `nyx/agent/commands/`, invocar no REPL real e capturar:
- Prompt usado.
- Saída (primeiras 10 linhas).
- Status: OK / CRASH / COMPORTAMENTO INESPERADO.

Tabela no relatório com 47 linhas.

### Frente 2 — Tools (34)

Lista de prompts naturais que forçam cada uma das 34 tools a rodar via fluxo normal (sem invocação direta). Exemplo: `list_files` é coberta por "liste os arquivos em nyx/agent/"; `bash_exec` por "rode pwd"; `edit_file` por "adicione comentário no topo de X".

Log de invocação anexado ao relatório (stdout do REPL mostrando a tool chamada).

### Frente 3 — Paridade visual/funcional (30 itens)

Criar `CHECKLIST_PARIDADE_CLAUDE_CODE.md` com tabela:

| # | Item | Resultado | Screenshot |
|---|------|-----------|------------|
| 1 | Banner ASCII aparece no boot | OK/FAIL | screenshot_01.png |
| 2 | Caixas de mensagem com borda consistente | OK/FAIL | ... |
| 3 | Footer com contador de tokens | OK/FAIL | ... |
| 4 | Popup de slash commands ao digitar `/` | OK/FAIL | ... |
| 5 | Colapso de paste grande (>N linhas) | OK/FAIL | ... |
| 6 | Streaming suave (sem stutter) | OK/FAIL | ... |
| 7 | Bypass toggle funcional | OK/FAIL | ... |
| 8 | Paste de imagem reconhecido | OK/FAIL | ... |
| 9 | Sandbox PT-BR (mensagens do sistema em português) | OK/FAIL | ... |
| 10 | Autocomplete reativo a cada tecla | OK/FAIL | ... |
| 11 | Ghost text (sugestão inline) | OK/FAIL | ... |
| 12 | Tool cards com duração em ms/s | OK/FAIL | ... |
| 13 | Evento visual de compactação | OK/FAIL | ... |
| 14 | Memória cross-session persiste | OK/FAIL | ... |
| 15 | /resume recupera última sessão | OK/FAIL | ... |
| 16 | Cursor piscante consistente | OK/FAIL | ... |
| 17 | Quebra de linha em resposta longa | OK/FAIL | ... |
| 18 | Cor de erro distinta da cor de info | OK/FAIL | ... |
| 19 | Feedback imediato ao ENTER | OK/FAIL | ... |
| 20 | Histórico com seta pra cima | OK/FAIL | ... |
| 21 | Ctrl+C cancela sem sair | OK/FAIL | ... |
| 22 | Ctrl+D sai limpo | OK/FAIL | ... |
| 23 | /help lista os 47 comandos | OK/FAIL | ... |
| 24 | Banner respeita largura do terminal | OK/FAIL | ... |
| 25 | Overflow horizontal trunca sem quebrar layout | OK/FAIL | ... |
| 26 | Título do terminal muda pra nome do projeto | OK/FAIL | ... |
| 27 | Model state transitions (cold/warming/warm) visível | OK/FAIL | ... |
| 28 | Replay de sessão read-only funciona | OK/FAIL | ... |
| 29 | /debug session retorna métricas reais | OK/FAIL | ... |
| 30 | Output com paleta D aplicada (design system) | OK/FAIL | ... |

Screenshots numerados vão para `/home/andrefarias/Desenvolvimento/Nyx-Code/assets/validate_final/`.

### Frente 4 — Install em VM limpa

Reusar o procedimento documentado em PORT-02. Passos:

```bash
docker run --rm -it -v $(pwd):/nyx ubuntu:22.04 bash
# dentro do container:
apt-get update && apt-get install -y python3.10 python3.10-venv git curl
cd /nyx
./install.sh        # ou o script equivalente criado em DEPLOY-02
./run.sh --smoke
```

Saída esperada: `boot ok`. Registrar output completo no relatório.

### Frente 5 — Benchmark de start

```bash
for i in 1 2 3 4 5; do
  /usr/bin/time -f "%e" ./run.sh --smoke 2>&1 | tail -1
done
```

Colar os 5 valores no relatório. Calcular mediana. Critério: mediana < 1.5s.

---

## Arquivos alvo (paths absolutos)

### `/home/andrefarias/Desenvolvimento/Nyx-Code/dev-journey/07-reports/RELATORIO_VALIDATE_FINAL_01.md`

Novo arquivo. Seções obrigatórias:

1. Sumário executivo (1 parágrafo).
2. Frente 1 — tabela dos 47 comandos.
3. Frente 2 — tabela das 34 tools.
4. Frente 3 — link para CHECKLIST_PARIDADE.
5. Frente 4 — output do install em VM.
6. Frente 5 — tabela dos 5 runs + mediana.
7. Output do `./run.sh --gauntlet` completo.
8. Conclusão: release ready SIM/NÃO.

### `/home/andrefarias/Desenvolvimento/Nyx-Code/dev-journey/07-reports/CHECKLIST_PARIDADE_CLAUDE_CODE.md`

Novo arquivo com a tabela dos 30 itens acima.

### `/home/andrefarias/Desenvolvimento/Nyx-Code/GUIDE.md`

Adicionar seção nova após "Regras invioláveis":

```markdown
## v1.0 — critérios de aceite

Tag v1.0 só sai quando VALIDATE-FINAL-01 estiver CONCLUIDA com:
- 47/47 comandos OK
- 34/34 tools exercitadas
- 30/30 itens de paridade OK
- Install em VM Ubuntu 22.04 limpa OK
- Start mediana < 1.5s em 5 runs
- Gauntlet 100%
```

### `/home/andrefarias/Desenvolvimento/Nyx-Code/dev-journey/06-sprints/SPRINT_ORDER_MASTER.md`

Adicionar linha final na narrativa da Onda 22 indicando "release ready após VALIDATE-FINAL-01".

---

## Diff esperado

```
+ 2 arquivos criados (relatório + checklist paridade)
~ 2 arquivos modificados (GUIDE.md, SPRINT_ORDER_MASTER.md)
- 0 arquivos removidos
+ ~400 linhas líquidas (a maior parte no relatório)
```

---

## Comandos de verificação

```bash
# PASSO 1 — snapshot ANTES
bash scripts/sprint_invariants.sh > /tmp/inv_before.txt 2>&1
FAIL_BEFORE=$(grep -c "^\[FAIL\]" /tmp/inv_before.txt)

# PASSO 2 — gauntlet completo
./run.sh --gauntlet

# PASSO 3 — benchmark de start (5 runs)
for i in 1 2 3 4 5; do
  /usr/bin/time -f "%e" ./run.sh --smoke 2>&1 | tail -1
done

# PASSO 4 — install em VM Docker
docker run --rm -v $(pwd):/nyx ubuntu:22.04 bash -c \
  "apt-get update && apt-get install -y python3.10 python3.10-venv git curl && cd /nyx && ./install.sh && ./run.sh --smoke"

# PASSO 5 — execução manual dos 47 comandos e 34 tools (registrar no relatório)

# PASSO 6 — snapshot DEPOIS
bash scripts/sprint_invariants.sh > /tmp/inv_after.txt 2>&1
diff /tmp/inv_before.txt /tmp/inv_after.txt
```

---

## Critério binário de aceite

- [ ] RELATORIO_VALIDATE_FINAL_01.md contém as 5 frentes completas
- [ ] CHECKLIST_PARIDADE_CLAUDE_CODE.md tem 30 linhas com OK/FAIL
- [ ] 47 comandos listados no relatório com status
- [ ] 34 tools listadas no relatório com log de invocação
- [ ] 5 tempos de start colados, mediana < 1.5s
- [ ] Output do install em VM Ubuntu 22.04 colado no relatório
- [ ] Gauntlet 100% com output bruto
- [ ] Screenshots em assets/validate_final/ numerados 01..30
- [ ] GUIDE.md tem seção "v1.0 — critérios de aceite"
- [ ] SPRINT_ORDER_MASTER.md marca release ready
- [ ] FAIL_AFTER <= FAIL_BEFORE no sprint_invariants
- [ ] Commit `docs: VALIDATE-FINAL-01 conclui auditoria de release v1.0`
- [ ] Sprint movida para concluidos/

---

## Guardrails anti-engodo

- Rodar o benchmark de start apenas 1 vez e extrapolar é violação. Precisa dos 5 runs colados.
- Marcar item de paridade OK sem screenshot anexado é violação.
- Declarar install em VM OK sem output do comando dentro do container é violação.
- Itens visuais validados só por "achei bonito" sem comparação com referência declarada: violação.
- Se algum item FALHAR, a sprint **não marca CONCLUIDA** — materializa SPRINT de fix com ID novo e devolve ao backlog (protocolo anti-débito).

---

## Gambiarras específicas desta sprint

1. **"Passou na primeira, é bom o bastante".** Benchmark com 1 amostra. Proibido — ruído de warm cache invalida. Exigem-se 5 runs.
2. **Checklist preenchido em lote ("OK em todos").** Cada linha precisa de evidência individual (screenshot ou output).
3. **Install "validado" em máquina própria, não em VM limpa.** Proibido — quebra a premissa de reprodutibilidade em ambiente novo.
4. **Comandos marcados OK sem log de saída.** Cada uma das 47 linhas precisa da saída real capturada.
5. **Tools "exercitadas" via chamada direta (scripts).** Tem que ser via fluxo natural do REPL (prompt leva o modelo a invocar a tool). Senão não é paridade com uso real.
6. **Screenshots de uma execução reaproveitados para itens diferentes.** Cada item do checklist tem screenshot distinto.
7. **Gauntlet "passou" sem colar o output bruto.** Exigência do proof-of-work global.
8. **Aceitar 46/47 comandos OK "porque um quebrou por ambiente".** Sprint é binária. 46 de 47 é FAIL.

Ver também `dev-journey/08-templates/GAMBIARRAS_POR_SPRINT.md` seção VALIDATE-FINAL-01 (se existir — se não, esta seção é a referência).

---

## Proof-of-work obrigatório

Formato padrão (ver SPRINT_TEMPLATE_V2.md seção "Proof-of-work"). Incluir obrigatoriamente:

- `cat /tmp/inv_before.txt | tail -10`, `cat /tmp/inv_after.txt | tail -10`, diff.
- Output dos 5 runs do benchmark de start, com mediana calculada.
- Output bruto do `./run.sh --gauntlet` completo.
- Output do install em VM Docker Ubuntu 22.04.
- Listagem `ls assets/validate_final/` mostrando os 30 screenshots.
- `git show --stat HEAD`.

---

## Validação humana (checklist do usuário)

```bash
cd /home/andrefarias/Desenvolvimento/Nyx-Code

# 1. Conferir relatório
cat dev-journey/07-reports/RELATORIO_VALIDATE_FINAL_01.md | head -80

# 2. Conferir checklist
cat dev-journey/07-reports/CHECKLIST_PARIDADE_CLAUDE_CODE.md

# 3. Conferir screenshots
ls assets/validate_final/ | wc -l    # esperado: 30

# 4. Rodar smoke manual
./run.sh --smoke                     # esperado: boot ok

# 5. Validar arquivos movidos
ls dev-journey/06-sprints/concluidos/SPRINT_VALIDATE_FINAL_01.md    # existe
ls dev-journey/06-sprints/producao/SPRINT_VALIDATE_FINAL_01.md      # NÃO existe
```

---

## Riscos

| Risco | Mitigação |
|-------|-----------|
| Sprint encontra regressão em dependência (UX-EXTRA-01, VISION-03, etc.) | Protocolo anti-débito: materializa sprint de fix com ID novo, não absorve silenciosamente |
| Benchmark de start sofre ruído por variação de Ollama warm-up | 5 runs, usar mediana (não média); se variância > 30%, registrar e investigar |
| Screenshots consomem muito espaço no repo | Usar PNG otimizado, até 200KB cada; considerar git-lfs se ultrapassar |
| Item de paridade subjetivo ("streaming suave") | Definir critério objetivo: sem pausa > 200ms entre tokens durante resposta típica |
| Install em VM falha por rede offline no container | Documentar premissa: rede necessária para apt-get; Ollama dentro da VM é opcional (smoke só valida import) |
| Mediana de start inflada por cold start da GPU | Rodar 1 warm-up antes dos 5 runs medidos; documentar no relatório |

---

*"A prova do pudim está em comê-lo." -- Miguel de Cervantes
