## 0. SPEC (machine-readable)

```yaml
sprint:
  id: ONDA48-GATE-FECHAMENTO-01
  numero_master: 449
  title: "Gate de fechamento da ONDA-48: re-run da holistica 7/7 + abertura formal da ONDA-49"
  onda: 48
  prioridade: ALTA
  tipo: Validação/Esteira
  dependencias: ["todas as sprints PENDENTE do bloco ONDA-48 (executar por último)"]
  desbloqueia: [MODEL-NATIVE-TOOLCALL-PIPELINE-01]

  touches:
    - path: dev-journey/06-sprints/SPRINT_ORDER_MASTER.md
      reason: "no PASS: fechar o bloco ONDA-48 e reverter 446/447 para PENDENTE (abre a ONDA-49)"
  creates:
    - path: dev-journey/07-reports/AUDIT_SAIDA_ONDA48.md
      reason: "relatorio do re-run da holistica + veredicto de fechamento da onda"
  removes: []

  forbidden:
    - "Fechar a onda com garantia FAIL sem sprint nova materializada para o gap (regra nenhum debito para tras)"
    - "Validar tool isolada via ToolRegistry e chamar de validação as-user (o erro que a própria ONDA-48 corrige)"
    - "Rodar com outro consumidor de GPU ativo (a holistica exige GPU exclusiva -- nota operacional do bloco)"
    - "Adicionar emoji; mencionar ferramenta de IA"

  acceptance_criteria:
    - "Sessão única contínua ./run.sh --headless, processo único, contexto acumulado: probes T1-T7 do AUDIT_2026_07_12 §2 re-executados"
    - "Veredicto exigido para fechar: 7/7 (T5 passa via 437; T7 passa via 402; sem vazamento de identidade via 440)"
    - "Passada as-user na TUI real (2-3 turnos no ambiente do dono) sem internals crus (426-429/406 em efeito)"
    - "Relatorio AUDIT_SAIDA_ONDA48.md escrito; no PASS a esteira e re-apontada para a ONDA-49"
```

---

# Sprint ONDA48-GATE-FECHAMENTO-01 — a onda só fecha provando no uso real

**Status:** PENDENTE
**Data criação:** 2026-07-20
**Origem:** o modo de falha que PARIU a ONDA-48 foi "gauntlet verde, produto colapsado no uso real" (a ONDA-45 validou a tool isolada e o dono achou a Nyx alucinando na TUI). A fila da ONDA-48 tem 30+ sprints, mas nenhum item final que re-rode a validação holística para provar que a onda cumpriu o que prometeu. Sem gate, o fechamento vira juízo subjetivo da última executora — exatamente o viés de confirmação que o bloco documenta. Esta sprint é o último item da fila e a condição de abertura da ONDA-49.

---

## Contexto do projeto (snapshot)

> **Baseline a bater:** validação holística de 2026-07-12 (`dev-journey/07-reports/AUDIT_2026_07_12.md` §2): 4/5 garantias sustentadas; T5 FAIL (drift de path -> sprint 437), T7 EXPECTED_FAIL (recall stale -> sprint 402) com vazamento de identidade entregue pelo retry (-> sprint 440).
> **ADR-035:** registra as 3 garantias (G1 tool bem-formada, G2 afirmado=produzido, G3 apresentado) e o estado 4/5 — este gate atualiza o estado do ADR ao fechar.
> **Esteira:** 446/447 estão ENFILEIRADA por decisão do dono (2026-07-13, uma onda ativa por vez); revertê-las a PENDENTE é o ato formal de abertura da ONDA-49.

---

## Problema

1. Cada sprint da ONDA-48 prova o próprio fix isolado (proof-of-work por sprint), mas ninguém prova o CONJUNTO sob contexto acumulado — onde os bugs desta onda historicamente nascem (T5 só falhou em sessão contínua).
2. O protocolo das ondas prescreve "onda de validação após cada onda", mas como processo de sessão, não como item da fila — quando a fila esvazia, o `update_next_sprint.py` diz "nenhuma pendente" e nada aponta para a validação.
3. A abertura da ONDA-49 depende de um passo manual documentado só em nota (reverter 446 para PENDENTE) — passo fácil de perder entre sessões.

## Execução (roteiro literal)

1. **Pré-condição:** `update_next_sprint.py` aponta esta sprint como única PENDENTE restante do bloco (todas as demais CONCLUIDA/ABSORVIDA/DESCARTADA com rationale). GPU exclusiva confirmada (`nvidia-smi` sem outro consumidor).
2. **Re-run holístico:** sessão única `./run.sh --headless` (processo único, contexto acumulado, `NYX_OLLAMA_START_TIMEOUT=120`), probes T1-T7 idênticos aos do AUDIT_2026_07_12 §2 (fastfetch / criar / listar / buscar / edição sequencial em `~/Desktop` / write_memory / recall same-session). Registrar por probe: tool correta, resultado real sob `Resultado:`, disco conferido por sha256, PT-BR limpo, zero vazamento de identidade, VRAM antes/depois, `oom_recovery_delta`.
3. **Passada as-user na TUI real:** 2-3 turnos no ambiente do dono (Chrome real via `--web`, protocolo da memória de validação visual) — sem tool_calls crus, sem summary engolido, cancelamento honesto (426/427/428 em efeito).
4. **Adjudicação dos ALTA registrados:** decidir com o dono os 2 follow-ups ALTA de `FOLLOWUPS_REGISTRADOS.md` (`INFRA-SECRET-PATHS-EXPAND-01`, `GAUNTLET-PROD-PARITY-TUNE-01`): promover a spec (evidência já existe nos relatórios) ou deferir com rationale para a ONDA-50/51. Não podem atravessar o fechamento sem decisão.
5. **Veredicto e esteira:**
   - **PASS (7/7 + TUI limpa):** escrever `AUDIT_SAIDA_ONDA48.md`; atualizar ADR-035 (estado 7/7); marcar o bloco ONDA-48 como CONCLUIDA no MASTER; reverter 446 e 447 para PENDENTE (specs + linhas); rodar `python scripts/update_next_sprint.py` e confirmar que aponta a 446.
   - **FAIL em qualquer garantia:** a onda NÃO fecha; cada gap vira sprint nova PENDENTE no próprio bloco (com evidência do re-run), e este gate volta a ser o último da fila.

## Proof-of-work esperado

- `AUDIT_SAIDA_ONDA48.md` com a tabela T1-T7 (antes 4/5 vs agora), evidência literal por probe (paths, sha256, trechos de summary) e o veredicto.
- Screenshot/captura da passada TUI real.
- No PASS: diff do MASTER (bloco fechado + 446/447 PENDENTE) + `EXECUTAR_SPRINT.md` apontando a 446.
- Invariantes 14/14 e VRAM liberada ao fim.

## Critério binário de aceite (IA executora)

1. T1-T7 re-executados em sessão contínua com evidência literal (não narrativa).
2. Fechamento SÓ com 7/7; qualquer FAIL materializou sprint nova antes de parar.
3. Follow-ups ALTA adjudicados com o dono (promovidos ou deferidos com rationale).
4. Esteira re-apontada (446 PENDENTE + gerador conferido) no PASS.

## Não-objetivos (anti-débito)

- **Não** corrigir código aqui: gate mede; gap vira sprint.
- **Não** re-julgar os 2 achados REFUTADOS do AUDIT_2026_07_12 §4 sem fato novo.
- **Não** antecipar o bake-off v2 (447, já enfileirado na ONDA-49).

---

*"Onda que fecha sem prova reabre como bug; o gate é o preço de fechar uma vez só."*
