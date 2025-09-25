# Guia de Contribuição

Obrigado pelo interesse em contribuir com o Nyx-Code.

## Ambiente de Desenvolvimento

```bash
./install.sh          # Configura Ollama, venv e modelos
./run.sh              # Inicia o agente
./run.sh --gauntlet   # Validação completa
```

### Requisitos

- Linux (x86_64)
- Python 3.10+
- GPU NVIDIA (RTX 3050 4GB recomendado)
- ~8 GB de disco (modelos Ollama)

## Fluxo de Trabalho

1. Fork o repositório
2. Crie um branch a partir de `main`
3. Implemente a mudança
4. Valide com `./run.sh --gauntlet`
5. Abra um Pull Request

## Testes

O Nyx-Code usa o framework **Gauntlet** para testes. Não usamos pytest/unittest.

```bash
./run.sh --gauntlet                      # Validação completa
./run.sh --gauntlet --only rapido        # Fases rápidas
./run.sh --gauntlet --only coverage      # Cobertura de componentes
python scripts/sync.py                   # Consistência N-para-N
```

Testes devem ser adicionados ao Gauntlet, nunca como arquivos `test_*.py` soltos.

## Novos Componentes

Para criar novos tools, commands ou services, use o scaffold:

```bash
python scripts/scaffold.py
```

Todo componente deve ser integrado: tools no registry, commands no `commands.py`, services importáveis.

## Convenções

### Código

- Python 3.10+ com type hints
- Logging rotacionado (nunca `print()`, exceto `cli.py` para output do REPL)
- Paths relativos via `Path` (nunca hardcoded)
- Error handling explícito (nunca silent failures)
- Citação de filósofo no fim de cada script

### Commits

```
tipo: descrição imperativa em PT-BR

# Tipos: feat, fix, refactor, docs, test, perf, chore
```

### Regras Obrigatórias

- **PT-BR com acentuação correta** em todo código, docs e commits
- **Zero emojis** em código, commits e documentação
- **Sem menções a IA** (anonimato total)
- **Nunca TODO/FIXME inline** (criar issue no GitHub)
- **Nunca mock** (testes contra infraestrutura real)
- **Nunca except vazio** (sempre `logger.error()` ou `raise`)

### ADRs

Decisões arquiteturais são documentadas em `dev-journey/03-decisions/ADR_*.md`. Consulte os 20 ADRs vigentes antes de propor mudanças estruturais.

## Reportando Bugs

Use o template de issue para bugs. Inclua:

- Descrição clara do problema
- Passos para reproduzir
- Comportamento esperado vs. observado
- Versão do Nyx-Code, Python e SO

## Dúvidas

Abra uma issue com o label `help wanted`.
