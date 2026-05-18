# MICROCOPY -- Identidade verbal canônica do Nyx (UX-PROGRESSION-01, ADR-027)

> Microcopy = textinhos de UX (toasts, prompts, errors). Aqui vive a voz
> Nyx: técnica, direta, em PT-BR acentuado. Sem inglês solto, sem
> "ótimo!", sem placeholders genéricos.

## Princípios

1. **PT-BR acentuado** sempre. `Não` nunca `Nao`.
2. **Voz Nyx:** sóbria, técnica, sem floreio. Como uma colega senior
   que economiza palavras.
3. **Verbo no infinitivo** para ações (`Rodar`, `Cancelar`, `Salvar`),
   não imperativo grosseiro (`Rode!`, `Cancele!`).
4. **Erro nomeado, não genérico.** Ex.: `Arquivo não encontrado: foo.py`
   (não `Erro!`).
5. **Sucesso silencioso, falha ruidosa.** Confirmar ações destrutivas;
   confirmar OK só quando não é óbvio.

## Tabela canônica (em construção)

| Contexto | Atual | Proposta | Motivação |
|----------|-------|----------|-----------|
| Boot ok | `boot ok` | `boot ok` | Smoke literal -- não mudar |
| Sessão salva | `[ok] Sessão salva: <path>` | `● sessão salva: <path>` | Glifo verde + minúscula (UX-PROGRESSION-02) |
| Sessão restaurada | `[ok] Sessão restaurada (N entradas)` | `● sessão restaurada (N entradas)` | Mesmo padrão (UX-PROGRESSION-02) |
| Sessão limpa | `[ok] Sessão limpa.` | `● sessão limpa` | Glifo + remover ponto final (UX-PROGRESSION-02) |
| Tutorial primeiro uso | `Tutorial rápido — 30 segundos` | igual | Já em PT-BR + sóbrio |
| Cancel placeholder | `tools em curso só podem ser interrompidas via Ctrl+C` | igual | Explica limitação MVP (UX-AGENCY-02 resolve) |
| Erro generic | `Erro!` | `<contexto>: <causa breve>` | Substituir placeholders |
| Pull modelo | `Baixando moondream (pode demorar)...` | `Baixando moondream (5-15min em rede média)` | Estima tempo |
| Dry-run aviso | `[dry-run] nenhum comando destrutivo executado` | igual | Já claro |
| Saída do REPL | `Adeus` / `Tchau` | `Até.` | Voz Nyx sóbria (ADR-027) |
| Sucesso vazio | `Sucesso!`, `Pronto!`, `Ok!` | `● <ação>` ou contexto específico | Glifo > exclamação genérica |

## Casos proibidos

- `Loading...`, `Saving...`, `Done!`, `Yay!`, `Bye!`, `Goodbye` — inglês ou floreio.
- `Erro!`, `Ops!`, `Algo deu errado`, `Tchau!`, `Adeus` — placeholder sem contexto.
- `Sucesso!`, `Pronto!`, `Ok!`, `Concluído!` isolados — substituir por `● <ação>` ou contexto específico.
- `Não pode fazer isso.` sem dizer por quê.

## Glifos canônicos de estado (invariante #14, NÃO emoji)

- `○` (U+25CB) — cold, vazio, neutro
- `◐` (U+25D0) — warming, em progresso, parcial
- `●` (U+25CF) — warm, sucesso, completo

Usar `●` em vez de `[ok]` quando o feedback é puramente positivo (ex: "● sessão salva"). Manter `[ok]` quando ação é técnica e precisa de tag (ex: "[ok] modelo trocado para X").

## Audit automatizado

`scripts/microcopy_audit.py --check` varre arquivos `nyx/**/*.py` em
busca de literais que casam padrões proibidos (inglês solto em strings
user-facing, placeholders sem contexto).

## Refactor incremental

Esta sprint (UX-PROGRESSION-01) é MVP: cria MICROCOPY.md + audit script
+ marca ADR-027 ACEITO_PARCIAL. **Refactor amplo das mensagens** (varrer
output.py, cli.py, commands/*.py, tools/*.py) fica para UX-PROGRESSION-02.

## Referências

- ADR-006 PT-BR obrigatório.
- ADR-024 Render Layer (output.py).
- ADR-027 Progressão + identidade verbal.
