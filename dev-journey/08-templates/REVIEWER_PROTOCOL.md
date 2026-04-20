# Reviewer Protocol — validação de sprints executadas

**Versão:** v1.0 (2026-04-19)
**Público-alvo:** a IA (ou humano) que revisa sprints entregues por outra IA executora.
**Relação com outros documentos:**
- `CLAUDE.md` → regras invioláveis do projeto (código, commit, fluxo).
- `GSD.md` → fluxo humano de abrir nova session e delegar uma sprint.
- `EXECUTAR_SPRINT.md` → prompt pronto para colar na executora.
- `SPRINT_TEMPLATE_V2.md` → formato obrigatório de cada sprint.
- `GAMBIARRAS_POR_SPRINT.md` → bypass-paths típicos por ID.
- **Este arquivo** → o que o reviewer faz DEPOIS que a executora diz "concluída".

---

## 1. Princípio — confiar no output, não na narrativa

A executora pode afirmar "sprint concluída com sucesso" em linguagem persuasiva. O reviewer **não lê narrativa**: lê **evidência bruta**.

- Output colado de `bash scripts/sprint_invariants.sh` (antes e depois).
- Output colado do comando específico da sprint.
- `git show --stat HEAD` do commit.
- Diff dos arquivos tocados.
- Screenshots quando a sprint é visual (banner, toolbar, popup).

**Se faltar qualquer um desses, a sprint volta.** Não negociar.

---

## 2. Checklist binário de aceite

Marcar cada item com sim/não explícito. Três não → rejeitada.

### 2.1 Proof-of-work

- [ ] `FAIL_BEFORE` e `FAIL_AFTER` declarados em números.
- [ ] `FAIL_AFTER <= FAIL_BEFORE` (nunca aumenta).
- [ ] `diff /tmp/inv_before.txt /tmp/inv_after.txt` colado.
- [ ] Se sprint promete fechar invariante X (matriz em `GAMBIARRAS_POR_SPRINT.md`), X saiu de FAIL para OK.
- [ ] Check #13 (`./run.sh --smoke`) continua PASS.

### 2.2 Comando da sprint

- [ ] Output bruto colado (não apenas "passou").
- [ ] Output é compatível com o acceptance_criteria da sprint.
- [ ] Não há asserts afrouxados (`>= 0` onde era `== N`).

### 2.3 Git

- [ ] `git log --oneline -1` mostra commit com mensagem no formato `tipo: descrição PT-BR`.
- [ ] `git show --stat HEAD` tem linhas líquidas compatíveis com escopo (≥ 20 para feature, ≥ 5 para fix trivial).
- [ ] Arquivo da sprint migrou de `producao/` para `concluidos/`.
- [ ] `SPRINT_ORDER_MASTER.md` marca `CONCLUIDA (commit HASH)` com hash verdadeiro.
- [ ] `EXECUTAR_SPRINT.md` aponta para próxima sprint (executora rodou `update_next_sprint.py`).

### 2.4 Conformidade com regras

- [ ] Zero emoji no diff (a regex do invariant #1 já pega — mas reviewer confere pontualmente).
- [ ] Zero menção a Claude/Anthropic/GPT/Gemini/Copilot (invariant #2).
- [ ] Zero `print()` fora de `cli.py` e `output.py` (invariant #3).
- [ ] Acentuação PT-BR correta em tudo novo.
- [ ] Paths absolutos só em `design_tokens` e `settings` (invariant #9).

### 2.5 Guardrails específicos da sprint

- [ ] Nenhum item de `forbidden[]` foi violado (ler a seção yaml da sprint).
- [ ] Nenhuma gambiarra do catálogo específico de `GAMBIARRAS_POR_SPRINT.md §<ID>` foi cometida.

---

## 3. Red flags — quando desconfiar

Estas pistas indicam que a executora cortou caminho. Cada uma exige investigação antes de aceitar.

| Red flag | Investigar |
|----------|-----------|
| Output do comando específico **não foi colado** | Pedir de novo; não aceitar "rodei e passou". |
| Commit com < 5 linhas para uma feature | `git show HEAD` — provavelmente só TODO ou stub. |
| Teste alterado junto com implementação | Conferir se assertion foi afrouxada. |
| `time.sleep(1)` ou `asyncio.sleep(1)` adicionado | Gambiarra para race condition — fix é ordem, não delay. |
| `# noqa` ou `# type: ignore` novo sem especificar regra | Exigir `# noqa: <REGRA>` + comentário adjacente. |
| Arquivo renomeado em vez de deletado (`_compact.py`, `.bak`) | Rename não conta como delete. |
| Imports sem uso no topo de arquivo | Stub sinalizador. Pedir para remover ou justificar. |
| `except Exception: pass` novo | Zero tolerância — exigir logger + motivo. |
| Duração de tool = 0ms sempre | Timer quebrado; tool_cards falsos. |
| Singleton declarado mas caller não atualizado | Cache inútil; mede mesmo que antes. |
| Benchmark com 1 run só | Cache cold engana; exigir mediana de 5. |
| Checkpoint visual marcado sem screenshot | Sprint visual exige imagem anexada. |

---

## 4. Como reproduzir o gauntlet da sprint

Em vez de rodar `./run.sh --gauntlet` completo (caro), rode só a fase relevante:

```bash
./run.sh --gauntlet --only <fase>
```

Fases conhecidas hoje: `rapido`, `tui`, `interface`, `tools`, `commands`, `proxy`, `integracao`, `e2e`. Sprints de visão terão `vision` (pós VISION-01). Sprints de install terão `install` (pós DEPLOY-01B).

Se a fase não existir ainda e a sprint afirma que passa: regressão de integridade — a executora inventou.

---

## 5. Sprints visuais (TUI, banner, popup) — protocolo extra

Screenshots **são obrigatórios** para sprints tocando:

- `_build_banner`, `_bottom_toolbar` em `cli.py`.
- `render_user_input`, `render_tool_card_*`, `nyx_spinner` em `output.py`.
- Popup de slash commands (`completer.py`).
- Qualquer coisa que o usuário **olha** (vs. apenas usa).

Se a executora não anexou screenshot, pedir explicitamente: "anexe screenshot de `./run.sh` mostrando <feature>". Sem imagem → BLOQUEADA.

---

## 6. Achados colaterais — protocolo anti-débito

Durante revisão, o reviewer pode descobrir bugs NÃO cobertos pela sprint atual (ex: VALIDATE-ONDA-20 Rodada 1 expôs BUG-PORT-PARSE-01, TUI-FIX-08, TUI-FIX-09). **Regra explícita do usuário**: "nenhum débito fica para trás".

Protocolo:

1. **Não** aplicar fix inline na sprint atual (quebra escopo atômico).
2. **Materializar** cada achado como `SPRINT_<ID>.md` em `producao/` usando `SPRINT_TEMPLATE_V2.md`.
3. **Adicionar linha PENDENTE** no `SPRINT_ORDER_MASTER.md` com ID sequencial e bloco apropriado.
4. **Commitar** cada sprint nova em commit separado (`docs: cria SPRINT_<ID>.md (achado durante <PARENT>)`).
5. **Atualizar deps** da sprint-mãe se os achados forem pré-requisito para reteste.
6. **Rodar** `python scripts/update_next_sprint.py`.
7. Só então revisar a sprint-mãe novamente.

Ver exemplo em: `dev-journey/07-reports/` após rodada 1 de VALIDATE-ONDA-20.

---

## 7. Quando uma sprint fica BLOQUEADA

Status legítimos: `PENDENTE`, `CONCLUIDA`, `BLOQUEADA`, `DESCARTADA` (decisão explícita de escopo), `ABSORVIDA_POR_<ID>` (escopo fundido em outra sprint).

BLOQUEADA ≠ débito. BLOQUEADA significa que algo precisa acontecer antes — geralmente outra sprint. O reviewer:

- Documenta motivo objetivo em 1 linha no master.
- Cria sprint-desbloqueio se ainda não existe.
- Atualiza `dependencias` da sprint bloqueada para apontar para ela.

---

## 8. ABSORVIDA_POR — quando uma sprint é fundida em outra

Durante reorganização (ex: 2026-04-19, split de TUI-FIX-07 em 07A/07B/07C), a sprint-mãe vira `ABSORVIDA_POR_TUI-FIX-07A, TUI-FIX-07B, TUI-FIX-07C`. Protocolo:

1. Editar header do arquivo da sprint-mãe: `**Status:** ABSORVIDA_POR_<IDs>`.
2. Adicionar seção "Nota de absorção" explicando por quê e para onde cada critério migrou.
3. **Não deletar** o arquivo — fica em `producao/` como referência histórica. Se atrapalhar visualmente, mover para `concluidos/` (decidir caso-a-caso).
4. No master: linha da sprint-mãe atualizada para `ABSORVIDA_POR_<IDs> (commit HASH)`.

---

## 9. Fluxo de revisão — 8 passos

```
1. Abro a conversa da executora.
2. Localizo o bloco de proof-of-work (FAIL_BEFORE, FAIL_AFTER, diff).
3. Rodo independentemente `bash scripts/sprint_invariants.sh` no meu lado para confirmar estado atual.
4. Leio `git log --oneline -5` e `git show --stat HEAD` do último commit.
5. Verifico arquivos movidos entre producao/ e concluidos/.
6. Comparo diff com acceptance_criteria da sprint (cada item checado).
7. Se sprint é visual: exijo screenshot.
8. Aprovo OU aponto o item específico que bloqueia, citando linha do `acceptance_criteria` ou `forbidden[]`.
```

Aprovação explícita: `"Sprint <ID> APROVADA. Próxima: <next_id>."`
Rejeição explícita: `"Sprint <ID> REJEITADA. Motivo: <1 linha objetiva>. Correção: <ação específica>."`

---

## 10. Quando CONFIAR na narrativa

Exceção à regra de §1: sprints de **docs** (tipo `Docs` no yaml, ex: ADR-021-DOC, ADR-022-DOC, DOC-CONSOLIDATE-01) não têm output de código para colar. Nesses casos o reviewer:

- Lê o arquivo novo criado (ADR ou consolidação).
- Confere que Status: ACEITO (ou o que a sprint exigir).
- Confere que CLAUDE.md / outros índices foram atualizados.
- Confere padrão PT-BR, zero emoji, zero IA.
- Aprova com base no conteúdo, não em gauntlet.

---

*"Confiar sem verificar é delegar o próprio discernimento." -- anônimo SRE*
