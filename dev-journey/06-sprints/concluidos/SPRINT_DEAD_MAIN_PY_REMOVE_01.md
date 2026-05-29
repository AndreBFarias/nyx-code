# SPRINT 262 — DEAD-MAIN-PY-REMOVE-01

## 0. SPEC (machine-readable)

```yaml
sprint:
  id: DEAD-MAIN-PY-REMOVE-01
  title: "Remover main.py vestigial da raiz"
  onda: 31
  prioridade: BAIXA
  tipo: Refactor
  dependencias: []
  desbloqueia: []

  touches:
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/dev-journey/01-getting-started/FOLDER_STRUCTURE.md
      reason: "Linha 65 documenta main.py como esqueleto; remover a linha"
  removes:
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/main.py
      reason: "Esqueleto vestigial; entry real é nyx/__main__.py -> nyx/cli.py:main"

  forbidden:
    - "Tocar nyx/__main__.py ou nyx/cli.py (entry real)"
    - "Tocar pyproject.toml [project.scripts] (aponta para nyx.__main__:main, correto)"

  tests:
    - cmd: "./run.sh --smoke"
      timeout: 10
      deve_passar: true

  acceptance_criteria:
    - "main.py nao existe mais na raiz"
    - "./run.sh --smoke imprime 'boot ok' (entry real intacto)"
    - "python scripts/sync.py exit 0"
    - "invariantes 14/14"
```

---

**Status:** PENDENTE
**Data criação:** 2026-05-26
**Modelo obrigatório:** claude-opus-4-7 (sem subagentes)

---

## Contexto

> GUIDE.md §2 (Simplicidade) + §3 (Cirúrgico): código morto sinalizado deve ser removido quando confirmado sem consumidores.
> ADR-013 (Integração obrigatória): "Nenhum módulo que não é importado por ninguém."

## Problema

`main.py` na raiz é um esqueleto: imprime logs e retorna 0 com o comentário literal "Esqueleto funcional. Agente será implementado no Sprint 2." O entry point real é `nyx/__main__.py -> nyx/cli.py:main()` (e `pyproject.toml` aponta `nyx = "nyx.__main__:main"`).

Débito antigo: `dev-journey/06-sprints/concluidos/SPRINT_06_DOCUMENTACAO_LIMPEZA.md:63` já listava "Remover `main.py` esqueleto (ou adaptar como entry point real)" — nunca executado.

## Verificação de segurança (já feita na auditoria)

- `run.sh` e `install.sh`: **zero** referências a `main.py`.
- `nyx/context/project.py:68`: `main.py` aparece numa lista de heurística de detecção de tipo de projeto (`common_entries`) — **não importa** o arquivo; é só um nome candidato genérico. Não quebra.
- Referências restantes são em docs/specs históricas (não-código).

## Solução

```bash
git rm main.py
```

E remover a linha 65 de `FOLDER_STRUCTURE.md` (`├── main.py    # Entry point Python (esqueleto)`).

## Comandos de verificação

```bash
test ! -f main.py && echo "removido"
./run.sh --smoke                  # boot ok (entry real funciona)
python scripts/sync.py            # exit 0
bash scripts/sprint_invariants.sh # 14/14 (check #12 root sem scratch continua ok)
```

## Critério binário de aceite

- [ ] `main.py` ausente da raiz
- [ ] `./run.sh --smoke` = `boot ok`
- [ ] `sync.py` exit 0
- [ ] `FOLDER_STRUCTURE.md` atualizado
- [ ] invariantes 14/14
- [ ] spec movida `producao/` -> `concluidos/`

## Proof-of-work

`ls main.py` (não existe) + output `./run.sh --smoke` + invariantes antes/depois.

---

*"O que não serve, ocupa." -- provérbio*
