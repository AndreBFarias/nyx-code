# SPRINT CI-NEXTSPRINT-ANONYMITY-01 -- gerador de EXECUTAR_SPRINT.md cita modelo proprietario e o hook anti-IA bloqueia o commit

## 0. SPEC (machine-readable)

```yaml
sprint:
  id: CI-NEXTSPRINT-ANONYMITY-01
  title: "update_next_sprint.py (linhas ~267 e ~277) injeta um literal de nome+versao de modelo proprietario no EXECUTAR_SPRINT.md gerado; o hook anti-IA do projeto bloqueia o commit desse arquivo, deixando-o eternamente como working-tree modificado"
  onda: 46
  bloco: "46 -- Saneamento de CI & Working Tree + achados da Onda de Validação 1"
  prioridade: MEDIA
  tipo: Bugfix / Infra de pipeline (anti-IA)
  dependencias: []
  desbloqueia: []

  touches:
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/scripts/update_next_sprint.py
      reason: "build_prompt() gera, no template do EXECUTAR_SPRINT.md, duas strings com nome+versao de modelo proprietario (linha ~267 'cole em uma session nova de <modelo>' e linha ~277 'Modelo obrigatorio: <modelo>'). Esse literal casa o hook anti-IA/anonimato do projeto, que bloqueia o commit do EXECUTAR_SPRINT.md gerado. Trocar por texto NEUTRO (sem marca/versao)."
      linhas_alvo: "~264-298 (build_prompt); foco nas 2 linhas com o nome de modelo"

  creates: []
  removes: []

  forbidden:
    - "Manter qualquer nome/versao de provedor IA por extenso no texto gerado (e a causa do bug)"
    - "Mudar a SEMANTICA do prompt (continua instruindo: sessao nova, sem subagentes, protocolo anti-gambiarra 10 passos) -- so o nome do modelo vira neutro"
    - "Quebrar o restante do build_prompt (gambiarras-inject, contagem de pendentes, caminho do arquivo)"

  tests:
    - cmd: "grep -niE 'opus|claude|anthropic|gpt|gemini|copilot|[0-9]\\.[0-9]' scripts/update_next_sprint.py"
      timeout: 30
      esperado: "sem nome/versao de modelo proprietario nas strings de template do prompt"
    - cmd: "python scripts/update_next_sprint.py --show (com uma sprint PENDENTE de teste) | grep -i 'modelo'"
      timeout: 30
      esperado: "a linha de modelo aparece NEUTRA (ex.: 'modelo principal local, sem subagentes')"
    - cmd: "simular o hook anti-IA / pre-commit sobre o EXECUTAR_SPRINT.md gerado"
      timeout: 60
      esperado: "o arquivo gerado NAO e mais bloqueado pelo hook (passa limpo)"
    - cmd: "bash scripts/sprint_invariants.sh"
      timeout: 180
      esperado: "14/14 PASS"

  acceptance_criteria:
    - "As 2 strings de template do build_prompt usam texto neutro, sem nome/versao de modelo proprietario"
    - "O EXECUTAR_SPRINT.md gerado passa pelo hook anti-IA (commitavel)"
    - "Semantica do prompt preservada (sessao nova, sem subagentes, 10 passos, ID/arquivo da sprint)"
    - "Invariantes 14/14; spec -> concluidos/"
```

---

**Status:** CONCLUIDA (f63f7ce)
**Data criacao:** 2026-06-24
**Origem:** achado colateral da execução da sprint 370 (ONDA-45) + confirmado nas execuções 371/373: ao rodar `python scripts/update_next_sprint.py`, o `EXECUTAR_SPRINT.md` gerado contem um nome de modelo proprietario e o hook anti-IA bloqueia seu commit, deixando-o sempre como working-tree modificado (auto-regeneravel mas nunca limpo).
**Modelo obrigatorio:** modelo principal local, sem subagentes; implementação direta

---

## Problema

`scripts/update_next_sprint.py`, em `build_prompt()`, gera o template do `EXECUTAR_SPRINT.md` com duas linhas que citam um nome+versao de modelo proprietario (uma no "cole em uma session nova de ..." e outra em "Modelo obrigatorio: ..."). O projeto tem hook anti-IA/anonimato (GUIDE.md #2; tambem refletido no `.github/workflows/anonymity-check.yml`) que bloqueia esse literal. Resultado: toda vez que o pipeline roda `update_next_sprint.py`, o `EXECUTAR_SPRINT.md` gerado nao pode ser commitado -- fica eternamente como ` M` no working tree. Observado em 3 execucoes seguidas (370/371/373).

---

## Causa-raiz

O gerador foi escrito antes do endurecimento do hook anti-IA e cravou o nome do modelo no template. A politica do projeto e citar o papel ("modelo principal local, sem subagentes"), nao a marca.

---

## Solucao proposta

Trocar, nas 2 strings de `build_prompt()`, o nome+versao do modelo por texto NEUTRO equivalente, por exemplo:
- "Copie o bloco abaixo e cole em uma sessao nova do modelo principal (sem subagentes)."
- "Modelo obrigatorio: modelo principal local, sem subagentes."

Preservar todo o resto (protocolo 10 passos, gambiarras-inject, ID/arquivo da sprint, contagem de pendentes). O texto deve passar pelo hook anti-IA.

---

## Proof-of-work esperado

```bash
grep -niE 'opus|claude|anthropic|gpt|gemini|copilot' scripts/update_next_sprint.py   # so em comentarios/regex, nao nas strings do template
# gerar o EXECUTAR_SPRINT.md com uma sprint PENDENTE e checar a linha de modelo neutra:
python scripts/update_next_sprint.py --show | grep -i "modelo"
# rodar o pre-commit/hook anti-IA sobre o EXECUTAR_SPRINT.md gerado -> nao bloqueia
bash scripts/sprint_invariants.sh                                                    # 14/14 PASS
python3 ~/.config/zsh/scripts/validar-acentuacao.py --paths scripts/update_next_sprint.py
/home/andrefarias/.local/bin/ruff check scripts/update_next_sprint.py
```

---

## Criterio binario de aceite

- [ ] template do build_prompt sem nome/versao de modelo proprietario
- [ ] EXECUTAR_SPRINT.md gerado passa pelo hook anti-IA (commitavel)
- [ ] semantica do prompt preservada
- [ ] invariantes 14/14, ruff/acento OK; spec -> concluidos/

---

## Riscos

| Risco | Mitigacao |
|-------|-----------|
| O hook anti-IA tambem barrar o proprio commit desta sprint (a spec menciona o tema) | Esta spec evita literais de marca; usa termos neutros e classes quando precisa citar |
| Texto neutro confundir quem le o EXECUTAR_SPRINT.md | "modelo principal local, sem subagentes" e claro no contexto do projeto (o modelo principal e o cerebro; nao precisa do nome) |

---

*"O guarda da porta nao pode ser o primeiro a ser barrado por ela." -- anonimo*
