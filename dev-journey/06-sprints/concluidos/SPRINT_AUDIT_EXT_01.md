## 0. SPEC (machine-readable)

```yaml
sprint:
  id: AUDIT-EXT-01
  title: "Auditoria externa independente do TUI/Agent"
  onda: 22
  prioridade: CRÍTICA
  tipo: Audit
  dependencias: []
  desbloqueia: [UX-DESIGN-01, AUDIT-FIX-01..NN]

  touches: []
  creates:
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/dev-journey/07-reports/AUDIT_EXT_2026_04_18.md
      reason: "Relatório frio de bugs, más práticas, N-para-N quebrados, violações de ADR"

  forbidden:
    - "Corrigir código durante a auditoria (só catalogar)"
    - "Omitir findings por serem pequenos"

  tests:
    - cmd: "test -s dev-journey/07-reports/AUDIT_EXT_2026_04_18.md"
      deve_passar: true

  acceptance_criteria:
    - "Relatório existe com seções: Críticos, Altos, Dívida, Violações ADR, Oportunidades UX"
    - "Pelo menos 1 finding por seção (exceto se genuinamente vazia)"
    - "Cada finding em CRÍTICO/ALTO vira sprint AUDIT-FIX-NN rascunhada"
    - "Usuário aprova lista de AUDIT-FIX antes de qualquer FIX executar"
```

---

# Sprint AUDIT-EXT-01 — Auditoria externa independente

**Status:** PENDENTE
**Data criação:** 2026-04-18
**Modelo obrigatório:** claude-opus-4-7 (sem subagentes)

---

## Contexto do projeto (snapshot)

Nyx-Code após Onda 21 (`TUI-FIX-01..07` em validação) e antes da Onda 22 (redesign total).
Usuário relatou verbalmente:
1. Layout horrível.
2. Autocomplete não dá sugestão inline.
3. Primeira mensagem enviada "antes do input aparecer" não é processada.
4. Nyx lenta em geral.

Porém o autor do código NÃO tem visão fresca. Esta sprint simula uma IA chegando agora e lendo tudo.

ADRs críticos a validar:
- 001 (local-first) — nenhum endpoint cloud
- 004 (zero emojis) — em código, commit, docs
- 005 (anonimato) — sem "Claude"/"Anthropic"/"OpenAI"
- 006 (PT-BR acentuação) — código e strings de usuário
- 013 (integração obrigatória) — tools/commands/services registrados
- 014 (testes via Gauntlet) — sem pytest solto

---

## Problema

Bugs invisíveis ao autor por vício de contexto. Falta olhar frio antes da refatoração total da Onda 22.

---

## Solução

Ler todo código relevante, listar tudo que está mal, categorizar.

---

## Escopo de leitura obrigatório

### Código
- `/home/andrefarias/Desenvolvimento/Nyx-Code/nyx/cli.py` (722 linhas)
- `/home/andrefarias/Desenvolvimento/Nyx-Code/nyx/agent/**/*.py`
- `/home/andrefarias/Desenvolvimento/Nyx-Code/nyx/interface/**/*.py`
- `/home/andrefarias/Desenvolvimento/Nyx-Code/nyx/providers/**/*.py`
- `/home/andrefarias/Desenvolvimento/Nyx-Code/nyx/proxy.py`
- `/home/andrefarias/Desenvolvimento/Nyx-Code/nyx/context/**/*.py`
- `/home/andrefarias/Desenvolvimento/Nyx-Code/nyx/themes/**/*.py`
- `/home/andrefarias/Desenvolvimento/Nyx-Code/nyx/integration/**/*.py`

### Config
- `pyproject.toml`, `requirements.txt`, `run.sh`

### ADRs
- `dev-journey/03-decisions/ADR_001..021_*.md`

### Git
- `git log -30 --stat` (últimos 30 commits)

---

## Checklist heurístico de busca

- [ ] `print(` fora de `nyx/cli.py` (só `cli.py` pode)
- [ ] `except:` pelado, `except Exception: pass` ou swallow sem log
- [ ] `# TODO` / `# FIXME` inline
- [ ] Path absoluto hardcoded (`/home/`, `/tmp/`, `/usr/`)
- [ ] Função > 80 linhas
- [ ] Arquivo > 500 linhas
- [ ] Arquivo > 800 linhas (violação ADR de limite)
- [ ] Import circular
- [ ] Emoji em código, string, comentário, commit
- [ ] Menção literal a "Claude", "GPT", "Anthropic", "OpenAI" (exceto strings técnicas: `OPENAI_BASE_URL`, `ANTHROPIC_API_KEY` env vars)
- [ ] Falta de acentuação em strings PT-BR ("funcao" em vez de "função", etc.)
- [ ] Constante duplicada entre módulos (hex de cor, versão, porta, timeout)
- [ ] Porta `11435` ou `11436` hardcoded em mais de um arquivo
- [ ] Falha silenciosa: `try: ... except: return None` sem logger.warning
- [ ] Tool no registry sem teste no Gauntlet
- [ ] Command em `commands.py` sem descrição ou help
- [ ] Service importável mas nunca instanciado (código morto)
- [ ] Race / ordem de inicialização suspeita em `cli.py`
- [ ] `on_token` + `render_assistant_end` duplicam saída?
- [ ] Bypass de permissão sobrescreve nível `always_confirm`?
- [ ] Rich Console criado múltiplas vezes?
- [ ] `asyncio.create_task` sem cancelamento ao quit
- [ ] Leituras de disco síncronas no start (`.nyx/memory`, history)
- [ ] Logging com `logger.error` que deveria ser `logger.warning` e vice-versa
- [ ] Strings de erro em inglês (PT-BR obrigatório para UI)
- [ ] Shebang ausente em scripts executáveis
- [ ] `requirements.txt` com versões frouxas (`>=`) em libs instáveis

---

## Entrega

1. **Relatório** em `dev-journey/07-reports/AUDIT_EXT_2026_04_18.md` com seções:

```markdown
# Auditoria Externa — Nyx-Code 2026-04-18

## Sumário executivo
(3-5 bullets)

## Críticos (bloqueia release)
### [C-01] <título curto>
- **Arquivo:** path:linhas
- **Sintoma:** ...
- **Causa:** ...
- **Proposta de fix:** vira sprint AUDIT-FIX-01

## Altos (prioriza na onda)
### [A-01] ...

## Dívida técnica (Onda 23+)
### [D-01] ...

## Violações de ADR
### [V-01] ADR-006 — strings sem acento em X

## Oportunidades de UX (além do que usuário citou)
### [O-01] ...
```

2. **Sprints AUDIT-FIX-NN rascunhadas** em `dev-journey/06-sprints/producao/` para cada item de CRÍTICOS e ALTOS, no formato V2, com prioridade herdada do severity.

3. **SPRINT_ORDER_MASTER.md** atualizado: bloco AUDIT-FIX-* adicionado na Onda 22.

---

## Critério binário de aceite

- [ ] `dev-journey/07-reports/AUDIT_EXT_2026_04_18.md` existe, tamanho > 3 KB
- [ ] Pelo menos 5 findings totais (se não, auditoria é rasa demais — revisar)
- [ ] Cada Crítico e Alto tem sprint rascunhada em `producao/`
- [ ] SPRINT_ORDER_MASTER.md lista novo bloco AUDIT-FIX-*
- [ ] Nenhum código de produção foi modificado nesta sprint (só relatórios e sprint-files)
- [ ] Usuário aprovou lista de AUDIT-FIX antes de qualquer execução

---

## Comando de verificação

```bash
test -s /home/andrefarias/Desenvolvimento/Nyx-Code/dev-journey/07-reports/AUDIT_EXT_2026_04_18.md
ls /home/andrefarias/Desenvolvimento/Nyx-Code/dev-journey/06-sprints/producao/SPRINT_AUDIT_FIX_*.md | wc -l
# deve retornar >= 1
```

---

## Riscos

| Risco | Mitigação |
|-------|-----------|
| Auditoria explode escopo (>30 findings) | Classificar dívida longa; user prioriza |
| IA auditora ignora áreas novas (themes/, interface/) | Checklist de arquivos obrigatório |
| Faltar critério objetivo pra "crítico vs alto" | Definido: crítico = crash ou dados perdidos; alto = UX quebrada; dívida = qualidade futura |

---

*"O olhar frio é o único que vê a casa." -- Sêneca (paráfrase)*
