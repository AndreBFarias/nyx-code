# Nyx-Code - Dev Journey

## Estrutura

```
dev-journey/
├── 00-INDEX.md                     # Este arquivo
├── 01-getting-started/
│   ├── STYLE_GUIDE.md              # Identidade visual e UX (paleta Nyx)
│   └── FOLDER_STRUCTURE.md         # Estrutura do projeto
├── 02-architecture/
│   └── DIAGRAMA.md                 # Fluxo completo da arquitetura
├── 03-decisions/
│   ├── ADR_001_LOCAL_FIRST.md      # 100% offline, zero cloud
│   ├── ADR_002_PROXY_THINK_FALSE.md # Proxy injeta think=false
│   ├── ADR_003_VRAM_MANAGEMENT.md  # num_gpu=12 para RTX 3050
│   ├── ADR_004_ZERO_EMOJIS.md      # Estética limpa
│   ├── ADR_005_ANONIMATO.md        # Sem menção a IA
│   ├── ADR_006_PT_BR.md            # Acentuação obrigatória
│   ├── ADR_007_GAUNTLET.md         # Validação via Gauntlet (1 teste/feature)
│   ├── ADR_008_PERFORMANCE_KPIS.md # Métricas de performance obrigatórias
│   └── ADR_009_ACESSO_UNIVERSAL.md # Premium gratuito para hardware limitado
├── 04-features/
│   └── FEATURE_MAP.md              # Mapeamento completo de 62 features
├── 05-guides/
├── 06-sprints/
│   ├── SPRINT_ORDER_MASTER.md      # Ordem de execução (blocos G, P, I, D)
│   ├── producao/                   # Sprints ativas
│   ├── concluidos/                 # Sprints finalizadas
│   └── backlog/                    # Sprints futuras
├── 07-reports/
│   └── gauntlet/                   # Reports do Gauntlet (histórico)
└── 08-templates/
    └── SPRINT_TEMPLATE.md          # Template canônico de sprint
```

## ADRs

| # | Título | Resumo |
|---|--------|--------|
| 001 | Local First | 100% offline, zero cloud |
| 002 | Proxy think=false | Resolve tool calling via conversão de API |
| 003 | VRAM Management | num_gpu=12 para RTX 3050 sem OOM |
| 004 | Zero Emojis | Estética limpa, sem genéricos |
| 005 | Anonimato | Sem menção a IA em commits/código |
| 006 | PT-BR | Acentuação correta obrigatória |
| 007 | Gauntlet | Validação real com 1 teste por feature |
| 008 | Performance KPIs | Métricas obrigatórias em cada execução |
| 009 | Acesso Universal | Premium gratuito para hardware limitado |

## Sprints

Ver `06-sprints/SPRINT_ORDER_MASTER.md` para a ordem completa.

| Bloco | Descrição | Sprints |
|-------|-----------|---------|
| G (Gauntlet) | Framework de validação + testes | G-01 a G-08 |
| P (Port Python) | Independência da TUI atual | P-01 a P-07 |
| I (Integração) | Conexão com projeto Luna | I-01 a I-03 |
| D (DevOps) | CI, hooks, automação | D-01 a D-03 |
