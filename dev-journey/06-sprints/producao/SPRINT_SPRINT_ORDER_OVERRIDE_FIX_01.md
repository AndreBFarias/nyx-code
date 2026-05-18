# SPRINT SPRINT_ORDER-OVERRIDE-FIX-01 — update_next_sprint.py respeita MANUAL_OVERRIDE

## 0. SPEC

```yaml
sprint:
  id: SPRINT_ORDER-OVERRIDE-FIX-01
  title: "update_next_sprint.py honra bloco MANUAL_OVERRIDE_ONDA_25 do MASTER"
  onda: 25
  bloco: meta (anti-débito, infra de pipeline)
  prioridade: ALTA
  tipo: INFRA
  dependencias: []
  desbloqueia: ["sequência correta da Onda 25 via auto-ponteiro"]
  origem: "Descoberto durante execução de TUI-REDESIGN-25-01 (2026-05-18): após mover spec para concluidos/, ./venv/bin/python scripts/update_next_sprint.py apontou EXECUTAR_SPRINT.md para INFRA-MODEL-AGNOSTIC-01 em vez de TUI-REDESIGN-25-02. O bloco MANUAL_OVERRIDE_ONDA_25 do SPRINT_ORDER_MASTER.md não é interpretado pelo script."

  touches:
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/scripts/update_next_sprint.py
      reason: "Detectar bloco <!-- MANUAL_OVERRIDE_ONDA_25 --> ... <!-- /MANUAL_OVERRIDE_ONDA_25 --> em SPRINT_ORDER_MASTER.md e usar a primeira sprint PENDENTE da Onda 25 (em ordem dos blocos 25.1..25.5) antes de cair na tabela genérica"
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/dev-journey/06-sprints/SPRINT_ORDER_MASTER.md
      reason: "(se necessário) garantir que o bloco MANUAL_OVERRIDE tenha marcadores parseáveis e ordem explícita"

  forbidden:
    - "Hardcode da string 'TUI-REDESIGN-25-XX' no script (ordem deve vir do MASTER)"
    - "Quebrar comportamento legado: sem MANUAL_OVERRIDE, script segue regex existente"

  tests:
    - cmd: "./venv/bin/python scripts/update_next_sprint.py --show 2>&1 | head -3"
      timeout: 5
      deve_passar: "imprime 'próxima sprint: TUI-REDESIGN-25-02' (ou a próxima PENDENTE da Onda 25 conforme MASTER)"
    - cmd: "bash scripts/sprint_invariants.sh"
      timeout: 60
      deve_passar: "14/14"

  acceptance_criteria:
    - "Script lê bloco MANUAL_OVERRIDE_ONDA_25 do MASTER quando presente"
    - "Próxima sprint reportada é a próxima PENDENTE da Onda 25 (na ordem 25.1 → 25.5 dos blocos), não a primeira da tabela legada"
    - "Sem MANUAL_OVERRIDE no MASTER, fallback para regex existente (compat)"
    - "EXECUTAR_SPRINT.md gerado aponta corretamente para 25-02 (validação ao final)"
    - "Smoke + invariantes 14/14"
```

---

# Sprint SPRINT_ORDER-OVERRIDE-FIX-01

**Status:** PENDENTE
**Data criação:** 2026-05-18 (achado colateral durante TUI-REDESIGN-25-01)
**Modelo obrigatório:** claude-opus-4-7

## Contexto

Durante a execução de TUI-REDESIGN-25-01, ao avançar o ponteiro via
`./venv/bin/python scripts/update_next_sprint.py`, o EXECUTAR_SPRINT.md
foi atualizado apontando para `INFRA-MODEL-AGNOSTIC-01` em vez de
`TUI-REDESIGN-25-02`. Isso quebra a sequência canônica da Onda 25
(25-01 → 25-02 → 25-03 → 25-15 → 25-16 → ...).

A causa: o script percorre a tabela legada do MASTER e ignora o bloco
`<!-- MANUAL_OVERRIDE_ONDA_25 -->` que canoniza a ordem da Onda 25
em 5 blocos (25.1 a 25.5).

## Solução proposta

1. Adicionar leitura do bloco `MANUAL_OVERRIDE_ONDA_25` em
   `update_next_sprint.py` antes da regex `ROW_PATTERN`.
2. Se o bloco estiver presente, extrair a ordem canônica (lista de
   IDs) e retornar a primeira que (a) está marcada PENDENTE no MASTER
   ou (b) tem arquivo em `producao/` correspondente.
3. Manter fallback para o comportamento legado quando o bloco não
   existir (preserva projetos sem override).

## Critério binário

- [ ] Script honra MANUAL_OVERRIDE_ONDA_25 quando presente
- [ ] `update_next_sprint.py --show` imprime TUI-REDESIGN-25-02 (com MASTER atual)
- [ ] Fallback legado preservado (sem override → regex tradicional)
- [ ] Smoke + invariantes 14/14
- [ ] Sprint movida → concluidos
- [ ] Commit `feat(SPRINT_ORDER-OVERRIDE-FIX-01): script respeita MANUAL_OVERRIDE`

## Invariantes a preservar

#2 (zero menção IA), #4 (zero except silencioso), #9 (zero path absoluto).

## Anti-débito

- Refactor maior do `update_next_sprint.py` (ex: usar pydantic) fica fora.
- Outros blocos MANUAL_OVERRIDE (Onda 26+) ficam como extensão futura quando aparecerem.

## Verificação

```bash
./venv/bin/python scripts/update_next_sprint.py --show
# esperado: "próxima sprint: TUI-REDESIGN-25-02"

bash scripts/sprint_invariants.sh
./run.sh --smoke
```

## Rollback

`git reset --hard HEAD~1`

---

*"Pipeline sem override é pipeline cego." -- SPRINT_ORDER-OVERRIDE-FIX-01*
