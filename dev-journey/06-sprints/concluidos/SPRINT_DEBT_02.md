## 0. SPEC

```yaml
sprint:
  id: DEBT-02
  title: "Remover diretório vazio nyx/interface/"
  onda: 22
  bloco: 1
  prioridade: BAIXA
  tipo: Refactor

  removes:
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/interface/
      reason: "Diretório com apenas __init__.py vazio, sem consumidores"

  tests:
    - cmd: "python -c 'import nyx; from nyx.agent.loop import AgentLoop'"
      deve_passar: true

  acceptance_criteria:
    - "nyx/interface/ não existe"
    - "Nenhum import de nyx.interface em lugar algum"
```

---

# Sprint DEBT-02 — Remover `nyx/interface/` vazio

## Contexto

Auditoria externa encontrou `nyx/interface/__init__.py` (0 bytes) e subdir `__pycache__` — código planejado mas nunca escrito. Sem import em lugar algum.

## Solução

```bash
rm -rf /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/interface
```

## Verificação

```bash
grep -rn "from nyx.interface\|import nyx.interface" /home/andrefarias/Desenvolvimento/Nyx-Code/
# vazio
```

## Critério

- [ ] Diretório removido
- [ ] Commit: `chore: remove diretorio vazio nyx/interface/`

*"O que não cresce, ocupa." -- anônimo*
