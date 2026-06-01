# SPRINT ONDA-38-A — UX-QUIT-CARD-POLISH-01

## 0. SPEC (machine-readable)

```yaml
sprint:
  id: UX-QUIT-CARD-POLISH-01
  title: "Polir o card de saída ao fechar o app (capitalização + pontuação + prefixo barra)"
  onda: 38
  prioridade: BAIXA
  tipo: UX
  touches:
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/agent/output.py
      reason: "trocar 'até.' minúsculo por 'Até breve.' nas duas saídas do card (inline L695 e grid L779)"
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/cli.py
      reason: "feedback de salvamento (L617-621): 'Sessão salva:' com dois-pontos + path e dica prefixados por barra vertical"
  acceptance_criteria:
    - "card de saída imprime 'Até breve.' capitalizado com ponto final"
    - "mensagem de salvamento imprime 'Sessão salva:' com dois-pontos"
    - "path da sessão e dica final em linhas prefixadas por barra vertical"
    - "dica final 'Use /resume na próxima abertura para retomar.' capitalizada com ponto"
    - "smoke boot ok + invariantes 14/14"
```

---

**Status:** CONCLUIDA (2026-06-01 — output.py L695/L779 + docstring L719 'até.'->'Até breve.'; cli.py L619-621 'Sessão salva:' + path/dica prefixados por barra vertical + dica capitalizada com ponto; smoke boot ok, invariantes 14/14 (check #14 glifos U+25xx intactos), acentuação exit 0; card real renderizado comprova 'Até breve.')
**Data criação:** 2026-06-01
**Modelo obrigatório:** sem subagentes (Read/Grep/Glob direto)

---

## Contexto

O card de encerramento do app tem microcopy inconsistente com o restante do chrome (que já foi capitalizado em COCKPIT-CHROME-CAPITALIZE-01). Hoje a despedida é "até." em minúsculo, o feedback de salvamento é "sessão salva" sem dois-pontos, e path/dica saem em linhas soltas sem prefixo visual. Sprint cosmética, baixo risco, cirúrgica.

## Escopo (touches autorizados)

- Arquivos a modificar:
  - `/home/andrefarias/Desenvolvimento/Nyx-Code/nyx/agent/output.py` (linhas 695 e 779 — as duas saídas "até." do card; a inline e a grid)
  - `/home/andrefarias/Desenvolvimento/Nyx-Code/nyx/cli.py` (linhas 617-621 — bloco de feedback de salvamento pós `shutdown_repl`)
- Arquivos a criar: nenhum
- Arquivos NÃO a tocar:
  - Os 6 arquivos protegidos do check #14 anti-sanitizer. ATENÇÃO: `nyx/cli.py` e `nyx/agent/output.py` ESTÃO no conjunto protegido (BRIEF "Defesa anti-sanitizer"). Glifos canônicos U+25CB/U+25D0/U+25CF/U+25C6 existentes nesses arquivos devem permanecer intactos. Esta sprint só toca strings de texto PT-BR, nunca os glifos.

## Observação sobre a hipótese original (ajuste do planejador)

Verificação via leitura desmentiu parte da hipótese do coordenador:

- O título da caixa de stats JÁ é "Última Sessão" capitalizado (`output.py:769`). NÃO existe título "sessão" minúsculo a corrigir.
- O rótulo da célula JÁ é "Sessão" capitalizado (`output.py:765` e `output.py:689`).
- A string "até." minúscula real está em `nyx/agent/output.py:695` (variante inline `_render_stats_inline`) e `nyx/agent/output.py:779` (variante grid `render_session_stats_card`), NÃO em `cli.py`.
- O feedback "sessão salva" + path + dica está em `nyx/cli.py:619-621` (dentro do bloco `if saved:`).

O spec abaixo reflete o estado REAL do código.

## Acceptance criteria

1. As duas ocorrências de `"até."` em `output.py` (L695 e L779) passam a `"Até breve."`.
2. Em `cli.py`, a linha 619 passa de `" sessão salva"` para `" Sessão salva:"` (dois-pontos).
3. Em `cli.py`, a linha 620 (path) passa a prefixar o path por uma barra vertical (U+007C) seguida de espaço, p.ex. `"|  {saved.resolve()}"`.
4. Em `cli.py`, a linha 621 (dica) passa a `"|  Use /resume na próxima abertura para retomar."` (capitalizada, com ponto final, prefixada por barra vertical).
5. `./run.sh --smoke` imprime `boot ok` e sai 0.
6. `bash scripts/sprint_invariants.sh` reporta PASS 14/14, FAIL 0.

## Invariantes a preservar

- Check #14 anti-sanitizer: glifos canônicos U+25xx em `cli.py` e `output.py` permanecem. A edição é só em literais de texto PT-BR; rodar o protocolo de regressão do BRIEF antes de marcar concluída.
- Check #4 acentuação PT-BR: "Até breve." e "Use /resume na próxima abertura para retomar." precisam de acento correto em `próxima`.
- GUIDE.md §3 mudanças cirúrgicas: tocar SÓ as 4 linhas citadas, sem reformatar o resto.
- Barra vertical de prefixo deve ser o caractere ASCII U+007C (pipe), NÃO um glifo box-drawing.

## Plano de implementação

1. `output.py:695` — substituir `f"  {ANSI_ACCENT_FG}até.{ANSI_RESET}"` por `f"  {ANSI_ACCENT_FG}Até breve.{ANSI_RESET}"`.
2. `output.py:779` — substituir `f"  {accent}até.{reset}"` por `f"  {accent}Até breve.{reset}"`.
3. Atualizar a docstring-exemplo em `output.py:719` (linha `até.` no bloco de exemplo do layout) para `Até breve.` por coerência visual da documentação.
4. `cli.py:619` — trocar `" sessão salva"` por `" Sessão salva:"`.
5. `cli.py:620` — prefixar o path: `f"  {DIM}|  {saved.resolve()}{NC}"`.
6. `cli.py:621` — `f"  {DIM}|  Use /resume na próxima abertura para retomar.{NC}"`.
7. Rodar protocolo anti-sanitizer (BRIEF) + smoke + invariantes.

## Testes

- Sem teste unitário novo (mudança puramente de microcopy). Baseline: FAIL_BEFORE = 0 (invariantes), esperado FAIL_AFTER = 0 (14/14).

## Proof-of-work esperado

- Diff final das 2 edições em `output.py` (mais a docstring) e 3 edições em `cli.py`.
- Runtime real:
  - Smoke: `./run.sh --smoke` (imprime `boot ok`, exit 0)
  - Invariantes: `bash scripts/sprint_invariants.sh` (PASS 14/14, FAIL 0)
- Validação visual: skill `validacao-visual` capturando o shutdown REAL do app (rodar o app, sair com `/quit`, capturar o card de encerramento), comprovando "Até breve.", "Sessão salva:" e as duas linhas prefixadas por barra vertical. PNG + sha256.
- Acentuação periférica: `python3 /home/andrefarias/.config/zsh/scripts/validar-acentuacao.py --paths nyx/cli.py nyx/agent/output.py` exit 0.
- Hipótese verificada: `rg -n "até\.|Até breve|Sessão salva" nyx/cli.py nyx/agent/output.py`.

## Riscos e não-objetivos

- Não-objetivo: redesenhar o grid 3x2 ou mexer no fallback inline. Só microcopy.
- Risco: tocar acidentalmente os glifos U+25xx no `output.py`. Mitigação: editar apenas as 4 linhas de texto e rodar o protocolo anti-sanitizer.

## Referências

- BRIEF: `/home/andrefarias/Desenvolvimento/Nyx-Code/VALIDATOR_BRIEF.md` (seções "Defesa anti-sanitizer" e "Contratos de runtime")
- Precedente histórico: COCKPIT-CHROME-CAPITALIZE-01 (mesmo espírito de capitalização de chrome)

---

*"O cuidado mora nas bordas da interface."*
