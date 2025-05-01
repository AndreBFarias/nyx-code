# Sprint 6: Documentação, Limpeza e Organização

**Objetivo:** Documentação completa, sprints organizadas, README profissional,
dev-journey mínimo, e limpeza de arquivos temporários/testes.

---

## 6.1 Reorganizar sprints/

```
sprints/
├── README.md                    # Índice com status de cada sprint
├── completas/
│   ├── 01-fundacao.md
│   ├── 02-correcao-tui.md
│   ├── 03-funcional.md
│   ├── 04-configuração-comandos.md
│   └── 04b-forcar-tool-calling.md
├── ativa/
│   ├── 05-identidade-nyx.md
│   └── 06-documentação-limpeza.md
└── backlog/
    ├── 07-port-python.md
    └── 08-integração-luna.md
```

## 6.2 README.md profissional

Reescrever com:
- Descrição alinhada com estilo Nyx
- Diagrama ASCII da arquitetura:
  ```
  Usuário -> run.sh -> Ollama (:11435) -> GPU
                    -> Proxy  (:11436) -> think=false -> Ollama
                    -> Nyx TUI (TUI) -> Proxy
  ```
- Seção "Começando" (install.sh, run.sh)
- Seção "Arquitetura" (por que proxy, por que num_gpu=12)
- Seção "Sprints" (link para cada uma)
- Referência ao projeto Luna

## 6.3 dev-journey/ mínimo

```
dev-journey/
├── 00-INDEX.md
├── 01-getting-started/
│   ├── STYLE_GUIDE.md          # Adaptado da Luna
│   └── FOLDER_STRUCTURE.md     # Estrutura do projeto
├── 02-architecture/
│   ├── DIAGRAMA.md             # Fluxo completo
│   └── PROXY.md                # Por que o proxy existe
└── 03-decisions/
    ├── ADR-001-local-first.md  # 100% offline
    ├── ADR-002-proxy.md        # think=false via proxy
    └── ADR-003-num-gpu.md      # Por que num_gpu=12
```

## 6.4 Limpar arquivos temporários

- Remover `sprint-04-resultados-e2e.md` (mover dados para doc final)
- Limpar tests/ (manter só os úteis)
- Remover `main.py` esqueleto (ou adaptar como entry point real)
- Remover `nyx/config/` esqueleto se não for usado pelo proxy

## 6.5 Atualizar .gitignore

Garantir que está limpo:
- logs/, sessions/, models/, .nyx_home/
- __pycache__/, *.pyc, venv/
- .env, reference/dist/
- node_modules/, package-lock.json

## 6.6 Atualizar install.sh

- Criar CLAUDE.md automaticamente
- Criar .claude/settings.json
- Mensagens estilo Nyx
- Citação de filósofo no fim

---

## Verificação

- [ ] Sprints organizadas em completas/ativa/backlog
- [ ] README.md com diagrama e seções completas
- [ ] dev-journey/ com STYLE_GUIDE, ADRs e diagramas
- [ ] Arquivos temporários removidos
- [ ] .gitignore atualizado
- [ ] install.sh cria configs automaticamente
