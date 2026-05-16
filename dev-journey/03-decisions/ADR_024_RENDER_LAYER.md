# ADR-024 — Render Layer: print() permitido em nyx/agent/output.py

**Status:** ACEITO
**Data:** 2026-04-18
**Contexto da Onda:** 22, Bloco 2, AUDIT-FIX-06

## Contexto

A meta-regra do projeto (GUIDE.md) proíbe `print()` fora de `nyx/cli.py`.
A auditoria externa (AUDIT-EXT-01) apontou 10+ `print()` em
`nyx/agent/output.py`, o que tecnicamente viola a regra.

Porém `output.py` é a **camada de renderização de UI humana** — seu papel
é escrever caracteres ANSI no terminal. Forçar `logging` nela seria
absurdo: logs não renderizam; logs vão para arquivo rotacionado.

## Decisão

`nyx/agent/output.py` é uma **render layer oficial**, com direito a usar
`print()` e escapes ANSI diretamente.

Contrato da render layer:
1. Apenas UI humana (cores, boxes, tabelas, spinners, diff, syntax highlight).
2. Zero lógica de negócio: nenhuma decisão de fluxo, nenhum estado modificado.
3. Zero I/O além do stdout: não lê arquivos, não faz requisição de rede, não
   consulta banco, não persiste.
4. Nenhum consumidor deve esperar retorno útil (render é void).
5. Toda string renderizada deve respeitar PT-BR (ADR-006) e zero emoji (ADR-004).

Outras camadas que **NÃO** são render layer e seguem proibição de `print()`:
- `nyx/agent/tools/*.py` — tools retornam `ActionResult`, quem imprime é a CLI.
- `nyx/agent/services/*.py` — services são infraestrutura.
- `nyx/agent/loop.py`, `parser.py`, etc. — lógica pura.
- `nyx/providers/*.py`, `nyx/proxy.py` — HTTP/rede.

## Consequências

- Positivas: elimina ~30 linhas de indireção (retornar strings só pra cli.py
  imprimir). Mantém output.py testável via captura de stdout.
- Negativas: qualquer arquivo futuro que queira escrever UI direto precisa
  de nova ADR. Isolamento por convenção, não por linter.

## Alternativas consideradas

**Alt A (refator):** output.py retorna strings; cli.py imprime.
- Contra: explode a API de cli.py; adiciona ~50 linhas de copypaste.
- Contra: perda da capacidade de `render_assistant_end()` imprimir linha em
  branco sem transitar por cli.py.
- A favor: linter global não precisaria de exceção.

Rejeitada porque o ganho de pureza não justifica o custo.

## Impacto em regras adjacentes

A regra anti-burla "Nunca `print()` — usar logging" **continua valendo**
para todos os arquivos exceto:
- `nyx/cli.py` (REPL — já permitido).
- `nyx/agent/output.py` (render layer — permitido a partir desta ADR).

Se uma tool for pega usando `print()`, a correção é **retornar via
ActionResult**, não adicionar exceção.

## Referências

- AUDIT-EXT-01 finding A-02.
- GUIDE.md seção "Anti-burla".
- ADR-004 (Zero Emojis), ADR-006 (PT-BR).

*"A exceção que não é nomeada vira regra na prática." -- anônimo*
