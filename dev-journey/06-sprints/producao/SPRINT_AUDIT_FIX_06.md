## 0. SPEC

```yaml
sprint:
  id: AUDIT-FIX-06
  title: "ADR-024 normaliza nyx/agent/output.py como render layer (print permitido)"
  onda: 22
  bloco: 2
  prioridade: ALTA
  tipo: Docs
  dependencias: []
  desbloqueia: []

  creates:
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/dev-journey/03-decisions/ADR_024_RENDER_LAYER.md
      reason: "Oficializa exceção de print() para output.py e explica contrato"

  touches:
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/CLAUDE.md
      reason: "Atualizar seção anti-burla: print() permitido em cli.py E nyx/agent/output.py"

  forbidden:
    - "Relaxar a regra global (continua: print() proibido em tools, services, parser, loop, etc.)"
    - "Aceitar output.py sem contrato: ela DEVE renderizar UI humana, não dados"

  tests:
    - cmd: "test -s dev-journey/03-decisions/ADR_024_RENDER_LAYER.md"
      deve_passar: true

  acceptance_criteria:
    - "ADR-024 criado com status 'aceito' e data"
    - "CLAUDE.md menciona explicitamente nyx/agent/output.py como exceção oficial"
    - "Lista de ADRs no CLAUDE.md vai até ADR-024"
    - "Commit dedicado, sem mudança de código funcional"
```

---

# Sprint AUDIT-FIX-06 — ADR-024: render layer

**Status:** PENDENTE
**Data criação:** 2026-04-18

## Contexto

- ADR-015 (Documentação para continuidade): toda decisão não-óbvia vira ADR.
- CLAUDE.md seção Anti-burla: "Nunca print() — usar logging. `print()` é permitido APENAS no cli.py para output do REPL."
- Finding A-02 do AUDIT-EXT-01: `nyx/agent/output.py` tem 10+ `print()`. É **camada de renderização UI** — não faz sentido forçar `logging` nela.

## Problema

Regra atual é genérica demais. Tecnicamente `output.py` viola a regra, mas isso é falso positivo — o papel dela é exibir UI.

Alternativas discutidas (AUDIT-EXT-01):
- (a) ADR explícita marcando output.py como exceção oficial de render layer.
- (b) Refatorar output.py para retornar strings; cli.py faz print. Mais invasivo, ganho duvidoso.

**Decisão:** (a). Documentar o contrato; deixar o código como está.

## Solução

1. Criar ADR-024 descrevendo o papel da render layer e o contrato dela.
2. Atualizar CLAUDE.md adicionando a exceção explícita.
3. Nenhuma mudança de código produtivo.

## Arquivo a criar: ADR-024

**Path:** `/home/andrefarias/Desenvolvimento/Nyx-Code/dev-journey/03-decisions/ADR_024_RENDER_LAYER.md`

**Conteúdo obrigatório:**

```markdown
# ADR-024 — Render Layer: print() permitido em nyx/agent/output.py

**Status:** ACEITO
**Data:** 2026-04-18
**Contexto da Onda:** 22, Bloco 2, AUDIT-FIX-06

## Contexto

A meta-regra do projeto (CLAUDE.md) proíbe `print()` fora de `nyx/cli.py`.
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
- CLAUDE.md seção "Anti-burla".
- ADR-004 (Zero Emojis), ADR-006 (PT-BR).

*"A exceção que não é nomeada vira regra na prática." -- anônimo*
```

## Mudança em CLAUDE.md

Localizar no CLAUDE.md a linha:
> - **Nunca print()** -- usar logging. `print()` é permitido APENAS no cli.py para output do REPL.

Trocar por:
> - **Nunca print()** -- usar logging. `print()` é permitido APENAS em: (a) `nyx/cli.py` para output do REPL; (b) `nyx/agent/output.py` como render layer oficial (ADR-024). Tools, services, parser, loop, proxy: proibido.

Também na tabela de ADRs (seção "ADRs vigentes"):
- Atualizar contagem: `ADRs | 24 | --`
- Adicionar linha `| 024 | Render Layer (print em output.py) |`

## Diff esperado

```
+ 1 arquivo criado (ADR_024_RENDER_LAYER.md)
~ 1 arquivo modificado (CLAUDE.md, 2 trechos)
```

## Comando de verificação

```bash
cd /home/andrefarias/Desenvolvimento/Nyx-Code
test -s dev-journey/03-decisions/ADR_024_RENDER_LAYER.md && echo "ADR OK"
grep -c "ADR-024\|output.py como render" CLAUDE.md
# esperado: >= 2 (menção na seção anti-burla + tabela ADRs)
```

## Critério binário

- [ ] Arquivo `ADR_024_RENDER_LAYER.md` existe e tem Status=ACEITO
- [ ] CLAUDE.md menciona `nyx/agent/output.py` como exceção
- [ ] Tabela de ADRs no CLAUDE.md lista ADR-024
- [ ] Contagem de ADRs no CLAUDE.md = 24
- [ ] Nenhum arquivo Python tocado
- [ ] Commit: `docs: ADR-024 normaliza output.py como render layer`

## Guardrails anti-engodo

**NÃO marque como concluída se:**
- ADR ficou como "proposto" ou "rascunho" — deve ser "aceito".
- CLAUDE.md não mencionar ADR-024 EM DOIS lugares (anti-burla + tabela).
- A IA aproveitou pra relaxar print() em outros arquivos além de output.py.

## Validação humana

```bash
cat dev-journey/03-decisions/ADR_024_RENDER_LAYER.md | head -20
grep "ADR-024\|render layer" CLAUDE.md
```

---

*"Nomear é também conter." -- Clarice Lispector*
