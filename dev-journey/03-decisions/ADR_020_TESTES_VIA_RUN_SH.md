# ADR-020: Testes sempre via run.sh

**Data:** 2026-04-05
**Status:** Aceita
**Contexto:** Evitar OOM e garantir infraestrutura ao rodar testes

---

## Decisão

Todos os testes devem ser executados via `./run.sh --gauntlet`, nunca chamando o gauntlet diretamente com python. O run.sh gerencia:

1. Inicializa Ollama com configuração correta (porta 11435, num_gpu)
2. Inicializa Proxy (porta 11436, think=false)
3. Verifica VRAM disponível antes de começar
4. Executa Gauntlet
5. Cleanup de processos ao final

## Motivo

Chamar `python scripts/gauntlet/nyx_gauntlet.py` diretamente pode:
- Causar OOM se Ollama não está configurado corretamente
- Falhar em 36 testes que precisam de Ollama+Proxy
- Deixar processos órfãos

## Uso

```bash
./run.sh --gauntlet                      # Completo (inicia Ollama + Proxy)
./run.sh --gauntlet --only rapido        # Fases rápidas
./run.sh --gauntlet --only p5            # Bloco específico
```

## Regra

- Sprint files devem referenciar `./run.sh --gauntlet --only <fase>`
- Nunca `python scripts/gauntlet/nyx_gauntlet.py` em docs ou CI
- CI usa `./run.sh --gauntlet` (que gerencia tudo)

---

*"A infraestrutura é invisível quando funciona." -- Paul Virilio*
