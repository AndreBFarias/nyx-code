# ADR-033 — A CADEIA NUNCA QUEBRA NA MÃO DO USUÁRIO

**Status:** ACEITO
**Data:** 2026-06-01
**Onda:** 36 (RESSURREIÇÃO)
**Sprint origem:** TUI-WORKER-CRASH-GUARD-01

## Contexto

O usuário relatou: "o terminal tá fechando do nada" e "travou depois da primeira
pergunta". A auditoria encontrou a causa estrutural: o turno rodava em
`run_worker(...)` SEM `exit_on_error=False`. No Textual o default é
`exit_on_error=True` — qualquer exceção no turno chamava `_handle_exception` e
**encerrava a TUI**. O `_process_turn` não tinha `except`, e o traceback ia para
stderr/devtools, sumindo quando o terminal fechava: um **crash invisível**.

O princípio que o dono cravou:

> "Não devemos chorar pelos crashes de OOM. Se isso rolou, uma cadeia inteira
> falhou."

Ou seja: um OOM (ou qualquer falha transitória) que chega ao usuário como crash
é prova de que a cadeia de resiliência tem um buraco. A infra de OOM no proxy já
absorve o erro (degrada para CPU e responde — ADR-003). O buraco estava na
camada de UI, introduzido na migração para Textual.

## Decisão

**Nenhuma exceção é repassada ao usuário como crash. Toda falha é absorvida,
registrada e explicada — a sessão continua viva.**

Regras concretas:

1. Todo `run_worker` que executa trabalho falível usa `exit_on_error=False`.
2. O corpo do worker (ex.: `_process_turn`) tem `except Exception` que:
   - registra o traceback completo em `~/.nyx/logs/nyx.log` (nunca em stderr
     que some com o terminal);
   - mostra ao usuário uma mensagem honesta (`[falha absorvida] ...`) e segue.
3. Defesa em profundidade: o entrypoint da TUI (`cli.py`) envolve `run_async()`
   em try/except para falhas FORA do turno (mount, layout, driver).
4. Vale para todas as camadas: proxy absorve OOM/erro de modelo (ADR-003); UI
   absorve exceção de turno/render; o usuário só vê uma mensagem clara.

## Consequências

### Positivas
- Fim do "terminal fecha do nada". A TUI sobrevive a qualquer turno ruim.
- Todo crash deixa rastro em `nyx.log` — diagnosticável, nunca mais invisível.

### Negativas / custo aceito
- `except Exception` amplo é normalmente um anti-padrão; aqui é rede de segurança
  DELIBERADA na borda do turno, sempre com log + mensagem (nunca silenciosa,
  respeitando o invariante #4 de `sprint_invariants.sh`).

## Enforcement

- Invariante sugerido: nenhum `run_worker(` em `nyx/agent/tui/` sem
  `exit_on_error=False` (a adicionar em `scripts/sprint_invariants.sh`).
- Validação: harness de teste do Textual com agente que lança exceção deve
  resultar em app vivo + mensagem `[falha absorvida]` + traceback em `nyx.log`.

## Referências
- [[ADR-003]] (VRAM Management) — degradação OOM no proxy (a outra ponta da cadeia).
- [[ADR-032]] (A infra carrega o modelo) — absorver é trabalho de infra.
- [[ADR-001]] (Local First) — boot/recovery nunca propagam exceção.
- Sprint TUI-WORKER-CRASH-GUARD-01 (ONDA-36).

---

*"Erro que chega ao usuário como crash é uma cadeia que desistiu. A infra não desiste."*
