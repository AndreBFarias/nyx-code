# SPRINT UX-BUG-02A — Diagnóstico sistemático do race de input-readiness

## 0. SPEC (machine-readable)

```yaml
sprint:
  id: UX-BUG-02A
  title: "Diagnóstico sistemático do race de input no REPL (sem aplicar fix)"
  onda: 22
  bloco: 5
  prioridade: ALTA
  tipo: Bugfix + Diagnóstico
  dependencias: [UX-BUG-01]
  desbloqueia: [UX-BUG-02B, UX-BUG-02C]

  touches: []

  creates:
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/scripts/repro_race_input.sh
      reason: "Script de reprodução controlada do bug (envia stdin imediatamente, confere se é perdido)"
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/dev-journey/07-reports/DIAG_RACE_INPUT.md
      reason: "Relatório com três hipóteses testadas e qual foi confirmada"

  removes: []

  n_to_n_pairs: []

  forbidden:
    - "Aplicar fix inline (fica para 02B/02C)"
    - "Pular hipóteses porque 'já sei a resposta'"
    - "Mockar prompt_toolkit — usar REPL real (ADR-010 Zero Mocks)"
    - "Adicionar emoji na saída do script ou do relatório"
    - "Mencionar IA em commits/relatórios"
    - "Path absoluto hardcoded fora do próprio script de repro"

  tests:
    - cmd: "bash -n scripts/repro_race_input.sh && echo 'sintaxe OK'"
      deve_passar: true
    - cmd: "test -x scripts/repro_race_input.sh"
      deve_passar: true
    - cmd: "bash scripts/repro_race_input.sh"
      deve_passar: "saída termina com [ok] input chegou OU [bug] input perdido — ambos aceitáveis, é diagnóstico"

  acceptance_criteria:
    - "scripts/repro_race_input.sh existe, é executável e tem sintaxe válida"
    - "Três hipóteses testadas com output literal colado em DIAG_RACE_INPUT.md"
    - "Relatório conclui qual hipótese foi confirmada (ou indica 'nenhuma — investigar outras')"
    - "Zero código de produção modificado (git diff nyx/ == vazio)"
    - "Acentuação PT-BR correta em script, relatório, comentários e commit"
    - "Gauntlet rapido continua passando 100%"
```

---

**Status:** PENDENTE
**Data criação:** 2026-04-19
**Origem:** divisão de UX-BUG-02 em três sprints (diagnóstico, estado cold/warm, fix do race).
**Modelo obrigatório:** claude-opus-4-7 (sem subagentes)

---

## Contexto do projeto (snapshot — não referência)

> **ADRs relevantes:**
> - ADR-001 Local First: tudo offline.
> - ADR-004 Zero Emojis.
> - ADR-005 Anonimato.
> - ADR-006 PT-BR: acentuação obrigatória.
> - ADR-010 Zero Mocks: testes contra infra real.
> - ADR-013 Integração Obrigatória.
> - ADR-014 Testes via Gauntlet.
> - ADR-020 Testes via run.sh.
>
> **Estado do sistema:**
> - 2026-04-19, Onda 22, Bloco 5 (Polimento UX).
> - Usuário reportou: "se eu clicar em enviar a mensagem antes de aparecer a tela do input ela não processa".
> - Sprint pai UX-BUG-02 absorveu oportunidade O-03 (indicador cold/warm), mas foi julgada inchada. Esta sprint (02A) cobre só diagnóstico.
> - `skill superpowers:systematic-debugging` é referência metodológica — formular hipóteses, refutar em ordem.

---

## Problema

O usuário reporta perda de input quando envia texto antes do banner terminar de imprimir. Sem diagnóstico sistemático, qualquer fix é chute.

### Sintoma observável

1. Usuário abre `./run.sh`.
2. Durante o print do banner ASCII, digita `oi` e pressiona Enter.
3. Após o prompt aparecer, nada acontece; o texto se perdeu.

### Por que não fixar agora

Três hipóteses plausíveis competem:

1. `prompt_toolkit` só lê stdin quando entra em `await prompt_async()`. Keystrokes anteriores ficam no buffer do tty e são consumidas pelo primeiro prompt — ou não são, dependendo de como o tty está configurado.
2. Warm-up síncrono de `AgentLoop()` (load de 34 tools + memory index + Analytics) atrasa o primeiro prompt. Durante o atraso, o input vai para algum lugar indefinido.
3. `render_user_input` (ou banner) escreve stdout enquanto o prompt ainda não está pronto, e o terminal descarta/reordena bytes.

Aplicar fix sem confirmar causa tende a mascarar o bug em vez de resolver.

---

## Solução proposta

Dividir o trabalho em dois produtos:

1. **Script de reprodução** — `scripts/repro_race_input.sh`. Envia stdin imediatamente após subir o REPL e checa literalmente se o texto chegou ao modelo.
2. **Relatório de diagnóstico** — `dev-journey/07-reports/DIAG_RACE_INPUT.md` com as três hipóteses, comando literal de teste para cada uma, output bruto, e conclusão.

Esta sprint **não toca código de produção**. Quem aplica fix é UX-BUG-02C.

---

## Arquivos alvo (paths absolutos)

### `/home/andrefarias/Desenvolvimento/Nyx-Code/scripts/repro_race_input.sh`

Conteúdo-alvo:

```bash
#!/usr/bin/env bash
# Reproduz race de input-readiness no REPL da Nyx.
# Envia stdin imediatamente após start e verifica se o texto foi consumido.
set -eu

LOG=/tmp/nyx_repro_$(date +%s).log
MARK="oi-pre-banner-$(date +%s)"

(
  sleep 0.1
  printf '%s\n/quit\n' "$MARK"
) | ./run.sh 2>&1 | tee "$LOG" || true

if grep -q "$MARK" "$LOG"; then
  echo "[ok] input chegou (marca: $MARK)"
  exit 0
else
  echo "[bug] input perdido (marca: $MARK)"
  echo "Log completo: $LOG"
  exit 1
fi
```

**Mudanças:** arquivo novo; executável (`chmod +x`); sem emoji; sem menção a IA.

### `/home/andrefarias/Desenvolvimento/Nyx-Code/dev-journey/07-reports/DIAG_RACE_INPUT.md`

Estrutura-alvo:

```markdown
# Diagnóstico — race de input-readiness (UX-BUG-02A)

**Data:** 2026-04-19
**Sprint:** UX-BUG-02A

## Sintoma observado

(descrição literal do comportamento)

## Hipótese 1 — buffer de tty do prompt_toolkit

**Teste:** (comando literal)
**Output:** (colar output bruto)
**Conclusão:** (confirmada | refutada | inconclusiva)

## Hipótese 2 — warm-up síncrono de AgentLoop

**Teste:** ...
**Output:** ...
**Conclusão:** ...

## Hipótese 3 — render_user_input antes do prompt pronto

**Teste:** ...
**Output:** ...
**Conclusão:** ...

## Causa confirmada

(uma linha objetiva — ou "nenhuma confirmada, investigar N")

## Recomendação para UX-BUG-02C

(o que 02C deve fazer dado o diagnóstico)
```

**Mudanças:** arquivo novo; só documentação; sem emoji.

---

## Diff esperado (resumo)

```
+ 2 arquivos criados
~ 0 arquivos modificados
- 0 arquivos removidos
+ ~80 linhas líquidas
```

---

## Comandos de verificação (literais, copy-paste)

```bash
cd /home/andrefarias/Desenvolvimento/Nyx-Code

# 1. Sintaxe do script
bash -n scripts/repro_race_input.sh && echo "sintaxe OK"

# 2. Executável
test -x scripts/repro_race_input.sh && echo "exec OK"

# 3. Rodar o repro (resultado pode ser [ok] ou [bug] — ambos válidos)
bash scripts/repro_race_input.sh

# 4. Relatório existe e tem as três hipóteses
grep -c "^## Hipótese " dev-journey/07-reports/DIAG_RACE_INPUT.md
# esperado: 3

# 5. Zero código de produção tocado
git diff --stat nyx/
# esperado: vazio

# 6. Gauntlet rápido segue verde
./run.sh --gauntlet --only rapido
```

---

## Critério binário de aceite

- [ ] `scripts/repro_race_input.sh` existe, executável, sintaxe OK
- [ ] `dev-journey/07-reports/DIAG_RACE_INPUT.md` tem 3 hipóteses com output bruto
- [ ] Conclusão identifica hipótese confirmada (ou registra "inconclusiva, próxima ação")
- [ ] `git diff --stat nyx/` vazio
- [ ] Gauntlet `--only rapido` passa 100%
- [ ] Sem emoji, sem menção a IA, acentuação PT-BR correta
- [ ] Commit: `docs: diagnóstico do race de input (UX-BUG-02A)`
- [ ] Sprint movida para `concluidos/`

---

## Guardrails anti-engodo

**NÃO marque como concluída se:**

- O relatório diz "confirmada" sem output bruto do teste colado.
- Script de repro apenas ecoa "ok" sem testar de verdade (precisa `grep "$MARK" "$LOG"`).
- Alguma hipótese foi pulada com "é óbvio que não é essa".
- IA aplicou fix em `nyx/cli.py` ou `nyx/agent/loop.py` (isso é 02C, não 02A).

---

## Catálogo de gambiarras proibidas

Ver `dev-journey/08-templates/SPRINT_TEMPLATE_V2.md` seção "Catálogo de gambiarras proibidas (20 padrões)". Aplicáveis a esta sprint em especial:

- #2 **Stub como implementação**: script que retorna `[ok]` fixo sem testar de fato.
- #4 **Documentação como implementação**: relatório diz "hipótese X confirmada" sem evidência.
- #8 **Grep que não detecta o bug**: `grep "oi"` num log cheio de `oi` gerados pelo próprio banner dá falso-positivo. Usar marca única (timestamp).
- #10 **Benchmark sem cronômetro**: se medir latência, colar número real de `time.monotonic()`.

---

## Proof-of-work obrigatório

Formato padrão (ver `SPRINT_TEMPLATE_V2.md` seção "Proof-of-work"). Incluir:

- `cat /tmp/inv_before.txt | tail -10` e `cat /tmp/inv_after.txt | tail -10`.
- Output literal de `bash scripts/repro_race_input.sh`.
- Conteúdo final do `DIAG_RACE_INPUT.md`.
- `git show --stat HEAD`.

---

## Gambiarras específicas desta sprint

1. **Log poluído** — se o banner contém a palavra "oi", `grep "oi"` casa com o banner e declara sucesso falso. Fix: marca única com timestamp (`oi-pre-banner-$(date +%s)`).
2. **Sleep generoso demais no repro** — colocar `sleep 5` antes de mandar input mascara a race. Fix: `sleep 0.1` máximo.
3. **"Testei mentalmente"** — relatório descreve hipótese sem rodar. Fix: cada seção tem bloco `**Output:**` com saída bruta.
4. **Fix premature** — IA abre `nyx/cli.py` e "já que está aqui" reorganiza init. Proibido. Essa é 02C.

---

## Validação humana (checklist do usuário)

```bash
cd /home/andrefarias/Desenvolvimento/Nyx-Code

git log --oneline -1
git show --stat HEAD

# O commit deve tocar APENAS:
#   scripts/repro_race_input.sh
#   dev-journey/07-reports/DIAG_RACE_INPUT.md
#   dev-journey/06-sprints/SPRINT_ORDER_MASTER.md
#   dev-journey/06-sprints/concluidos/SPRINT_UX_BUG_02A.md (movido)
#   EXECUTAR_SPRINT.md

bash scripts/repro_race_input.sh
cat dev-journey/07-reports/DIAG_RACE_INPUT.md | head -40

ls dev-journey/06-sprints/concluidos/SPRINT_UX_BUG_02A.md
! ls dev-journey/06-sprints/producao/SPRINT_UX_BUG_02A.md 2>/dev/null
```

---

## Riscos

| Risco | Mitigação |
|-------|-----------|
| Race é intermitente e não reproduz em CI | Rodar repro 5x localmente; se intermitente, documentar taxa e marcar hipótese como "parcialmente confirmada" |
| Três hipóteses não esgotam causas | Seção "Recomendação" pode abrir nova sprint de investigação (nenhum débito fica para trás) |
| prompt_toolkit já foi removido em sprint futura | Revalidar dependência antes de rodar; se removido, redefinir escopo e avisar usuário |

---

*"O que não pode ser observado não pode ser depurado." -- adaptado de Peter Drucker*
