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

## Regras de capitalização e acentuação

Canonizado em **TUI-REDESIGN-25-01** (Onda 25). Aplica-se a toda string
user-facing (terminal, TUI, dashboard web, prompts, toasts).

### Sentence-case

Sentenças começam com **maiúscula inicial** e terminam com **ponto final**.
Fragmentos (rótulos, opções de menu, badges) permanecem em minúscula sem ponto.

- Sentença completa: `Configure antes de inicializar.`
- Fragmento de menu: `paleta D canônica`
- Toast de sucesso: `configuração salva.` (minúscula é OK quando segue um glifo `●` ou marcador)

**Não usar** Title Case (`Configure Antes De Inicializar`) nem CAIXA ALTA
(`CONFIGURE ANTES DE INICIALIZAR`). Estrangeirismo e gritaria, respectivamente.

### Substantivos próprios preservados

Mantêm grafia original mesmo dentro de sentence-case:

- Nomes de produto/projeto: `Nyx`, `Ollama`, `Claude`, `Linux`, `Python`
- Teclas e atalhos: `Enter`, `Ctrl+D`, `Ctrl+C`, `Shift+Tab`, `REPL`
- IDs técnicos: `ADR-029`, `TUI-REDESIGN-25-01`, `qwen2.5-coder:3b`
- Glifos canônicos (invariante #14): `○`, `◐`, `●`

### Acentuação PT-BR obrigatória

Locale do projeto é `pt_BR.UTF-8`. Toda string user-facing deve usar
acentos completos. Palavras de uso frequente:

| Errado (sem acento) | Correto |
|---|---|
| configuracao | configuração |
| permissoes | permissões |
| padrao | padrão |
| automacao | automação |
| instalacao | instalação |
| canonica | canônica |
| ambar | âmbar |
| rapido | rápido |
| Bem-vinda (genérico) | Bem-vindo (masculino genérico para usuário desconhecido) |
| Nao | Não |

### Escopo: só strings user-facing

**Acentuar:** literais em `say()`, `print()`, `out.write()`, mensagens em
`logger.info()` exibidas ao usuário, prompts em `input()`, textos em
templates HTML/JSX.

**Não acentuar:** comentários técnicos (`# ...`), docstrings internas,
nomes de variáveis, strings de IDs/IDs técnicos, logs de debug interno.
Razão: grep mais robusto em código + compat com terminais sem UTF-8.

### Validação automática

```bash
# Grep cego para palavras críticas:
grep -nE "configuracao|permissoes|padrao|automacao|canonica|ambar|bootar|Bem-vinda" \
  scripts/*.py nyx/**/*.py
# Esperado: 0 hits.

# Validador externo (se disponível):
~/.config/zsh/scripts/validar-acentuacao.py <arquivo>
```

### Anti-débito

Refactor sentence-case amplo (mensagens de erro com call-to-action) está
fora desta sprint — fica para **TUI-REDESIGN-25-11** (escopo dela).
Acentuação em comentários técnicos é não-bloqueante (Onda 26 se reaparecer).

---

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
