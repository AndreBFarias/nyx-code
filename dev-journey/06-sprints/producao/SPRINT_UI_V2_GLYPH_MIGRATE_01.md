# SPRINT ONDA-38-G — UI-V2-GLYPH-MIGRATE-01

## 0. SPEC (machine-readable)

```yaml
sprint:
  id: UI-V2-GLYPH-MIGRATE-01
  title: "Migrar dingbats desprotegidos dos 3 mockups v2 para geométricos U+25xx allowlisted"
  onda: 38
  prioridade: BAIXA
  tipo: Mecânico
  touches:
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/novo_layout/v2_referencias/nyx-themes.jsx
      reason: "L54 e L55: userPrefix/nyxPrefix com dingbats U+276F e U+2726 -> geométricos"
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/novo_layout/v2_referencias/nyx-session-render.jsx
      reason: "L52, L139, L445, L633: dingbats U+2726/U+2713/U+2715 -> geométricos"
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/novo_layout/v2_referencias/audit.jsx
      reason: "L79: dingbat U+2713 -> geométrico"
  acceptance_criteria:
    - "os 3 .jsx ficam sem dingbats desprotegidos; só glifos geométricos allowlisted"
    - "emoji_guardian.py check no diretório reporta 0 emojis pós-migração"
    - "mapeamento alinhado ao design_tokens / allowlist canônica"
```

---

**Status:** CONCLUIDA (2026-06-01 — 9 dingbats migrados p/ geométricos allowlisted nos 3 .jsx; `emoji_guardian.py check novo_layout/v2_referencias` = "Nenhum emoji encontrado" exit 0; geométricos pré-existentes U+25C6/U+25CF preservados; acentuação exit 0; diff 7/7 linhas)
**Data criação:** 2026-06-01
**Modelo obrigatório:** sem subagentes (Read/Grep/Glob direto)

---

## Contexto

Os 3 mockups de referência em `novo_layout/v2_referencias/` usam dingbats que NÃO estão na allowlist canônica (`/home/andrefarias/.config/zsh/scripts/glyphs_canonicos.py`). Por isso o santuário/emoji_guardian os estripa em cada passagem. A solução é migrar para os geométricos Geometric Shapes (U+25xx) que ESTÃO na allowlist, preservando a semântica visual via o mesmo vocabulário de `design_tokens`. Tipo mecânico/isolado. Os 3 .jsx já foram restaurados ao HEAD pelo coordenador (dingbats de volta), então a migração parte do estado com dingbats presentes.

NOTA DE REDAÇÃO: este spec cita glifos por codepoint+nome, nunca pelo caractere literal, porque o hook guardian.py de escrita bloqueia conteúdo na faixa U+2700-27BF (que inclui os 4 dingbats de origem). O executor, ao editar os .jsx, escreve os geométricos U+25xx (allowlisted e fora da faixa bloqueada).

## Escopo (touches autorizados)

- Arquivos a modificar (todos em `/home/andrefarias/Desenvolvimento/Nyx-Code/novo_layout/v2_referencias/`):
  - `nyx-themes.jsx`
  - `nyx-session-render.jsx`
  - `audit.jsx`
- Arquivos a criar: nenhum
- Arquivos NÃO a tocar: qualquer `.py` do código de produção; os 6 protegidos do check #14. Esta sprint é só nos 3 .jsx de referência.

## Observação sobre a hipótese original (ajuste do planejador — IMPORTANTE)

Verificação via varredura de codepoints nos 3 arquivos confirmou e corrigiu line numbers:

- `nyx-themes.jsx`: dingbats em L54 (U+276F chevron) e L55 (U+2726 estrela). As L26 e L109 JÁ têm U+25C6 (geométrico, já allowlisted) — não tocar. Hipótese citava "L54-55" — confere.
- `nyx-session-render.jsx`: dingbats em L52 (U+2726 x2), L139 (U+2713 + U+2715), L445 (U+2726), L633 (U+2713). Hipótese citava "52,139,445,633" — confere EXATAMENTE.
- `audit.jsx`: dingbat APENAS em L79 (U+2713). As L58 (U+25CF) e L72 (U+25C6) JÁ são geométricos allowlisted — não tocar. Hipótese citava "L79" — confere.

AJUSTE CRÍTICO DE PATH: a hipótese aponta o guardião como `~/.config/zsh/scripts/emoji_guardian.py`, mas esse arquivo NÃO existe. O que existe nesse diretório é só a allowlist `glyphs_canonicos.py`. O `emoji_guardian.py` real (com interface `check`/`clean`) está em:

`/home/andrefarias/Controle de Bordo/.sistema/scripts/emoji_guardian.py`

(interface: `python3 "<path>/emoji_guardian.py" check <diretório>` e `... clean <diretório> --apply`). É esse o binário a usar no proof.

## Mapeamento canônico (origem -> destino)

Todos os destinos estão na allowlist `glyphs_canonicos.py` (verificado):

| Origem (dingbat, faixa bloqueada) | Destino (geométrico, allowlisted) | Semântica |
|---|---|---|
| U+276F (chevron pointing right) | U+25B8 (small right triangle) | Bash/execute |
| U+2726 (black four pointed star) | U+25C6 (diamond filled) | header agente / multi-tool |
| U+2713 (check mark) | U+25CF (circle filled) | ok / warm |
| U+2715 (multiplication x) | U+25CB (circle empty) | cold / fail |

## Acceptance criteria

1. Toda ocorrência de U+276F nos 3 .jsx vira U+25B8.
2. Toda ocorrência de U+2726 vira U+25C6.
3. Toda ocorrência de U+2713 vira U+25CF.
4. Toda ocorrência de U+2715 vira U+25CB.
5. `python3 "/home/andrefarias/Controle de Bordo/.sistema/scripts/emoji_guardian.py" check /home/andrefarias/Desenvolvimento/Nyx-Code/novo_layout/v2_referencias` reporta 0 emojis (os geométricos são allowlisted, não contam).
6. Nenhum geométrico pré-existente (U+25C6/U+25CF nas linhas que já estavam corretas) é alterado.

## Invariantes a preservar

- Allowlist canônica é a FONTE ÚNICA: os 4 destinos (U+25B8/U+25C6/U+25CF/U+25CB) constam de `glyphs_canonicos.py`. Não inventar mapeamento fora dela.
- Semântica visual fiel ao `design_tokens` (BRIEF "Defesa anti-sanitizer": U+25C6 = diamante header, U+25CF = warm/ok, U+25CB = cold, U+25B8 = bash).
- GUIDE.md §3: tocar SÓ as linhas com dingbats; não reformatar o JSX nem alterar as linhas já geométricas.
- Esta sprint NÃO toca o check #14 do `sprint_invariants.sh` (os .jsx não estão no conjunto protegido), mas o resultado torna os mockups imunes ao estripamento futuro.

## Plano de implementação

1. `nyx-themes.jsx`: L54 U+276F -> U+25B8 (userPrefix); L55 U+2726 -> U+25C6 (nyxPrefix). Confirmar via varredura que L26/L109 (U+25C6) ficam intactas.
2. `nyx-session-render.jsx`: L52 (2x U+2726 -> U+25C6); L139 (U+2713 -> U+25CF, U+2715 -> U+25CB); L445 (U+2726 -> U+25C6); L633 (U+2713 -> U+25CF).
3. `audit.jsx`: L79 (U+2713 -> U+25CF). Confirmar L58/L72 intactas.
4. Re-varrer codepoints dos 3 arquivos para confirmar zero dingbat das faixas U+2700-27BF / U+276F-2726 restante.
5. Rodar `emoji_guardian.py check` no diretório.

## Testes

- Sem teste unitário (são mockups .jsx de referência, fora da suíte Python). A prova é o `emoji_guardian.py check` retornando 0 emojis.
- Baseline: emojis ANTES = 8 dingbats desprotegidos (2 em themes + 5 em session-render + 1 em audit), esperado DEPOIS = 0.

## Proof-of-work esperado

- Diff final dos 3 .jsx (substituições de codepoint).
- Verificação do guardião: saída de `python3 "/home/andrefarias/Controle de Bordo/.sistema/scripts/emoji_guardian.py" check /home/andrefarias/Desenvolvimento/Nyx-Code/novo_layout/v2_referencias` mostrando 0 emojis pós-migração.
- Re-varredura de codepoints: comando python que confirma zero codepoint em U+276F/U+2726/U+2713/U+2715 nos 3 arquivos e presença dos geométricos esperados.
- Sanidade visual: confirmar que os arquivos continuam JSX válido (sem quebra de sintaxe pela troca de glifo).
- Acentuação periférica: `python3 /home/andrefarias/.config/zsh/scripts/validar-acentuacao.py --paths novo_layout/v2_referencias/nyx-themes.jsx novo_layout/v2_referencias/nyx-session-render.jsx novo_layout/v2_referencias/audit.jsx` exit 0 (caso haja texto PT-BR nos mockups).
- Hipótese verificada: a varredura de codepoints acima É a verificação de hipótese (line numbers + presença de dingbats).

## Riscos e não-objetivos

- Não-objetivo: migrar glifos de qualquer arquivo fora dos 3 .jsx; alterar o código de produção; alterar a allowlist canônica.
- Risco: o coordenador alerta que os .jsx podem ser re-estripados por execução residual de sanitizer histórico (BRIEF VECTOR-AUDIT-01). Após esta migração, os glifos passam a ser allowlisted, então o sanitizer correto os PRESERVA — esse é justamente o objetivo. Se houver recidiva pós-migração, é vetor histórico (não regressão desta sprint).
- Risco: tocar uma linha geométrica já correta. Mitigação: editar só as linhas listadas e re-varrer codepoints.

## Referências

- BRIEF: `/home/andrefarias/Desenvolvimento/Nyx-Code/VALIDATOR_BRIEF.md` (seção "Defesa anti-sanitizer", VECTOR-AUDIT-01)
- Allowlist canônica: `/home/andrefarias/.config/zsh/scripts/glyphs_canonicos.py`
- Guardião real: `/home/andrefarias/Controle de Bordo/.sistema/scripts/emoji_guardian.py`

---

*"Glifo allowlisted é glifo que sobrevive ao sanitizer."*
