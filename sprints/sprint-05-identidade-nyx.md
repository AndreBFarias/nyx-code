# Sprint 5: Identidade Visual e Personalidade (Cara da Luna)

**Objetivo:** O Nyx-Code deve ter a mesma estética, filosofia e infra do projeto Luna.
Não é uma cópia da Nyx-kernel (que é técnica e minimalista). É a experiência completa
da Luna adaptada para um agente de código standalone.

A Nyx da Luna é o kernel. O Nyx-Code é o produto. Precisa ter vida.

---

## Referência: STYLE_GUIDE.md da Luna

### Filosofia
- "Luna está viva" — toda feature responde: "isso faz parecer mais viva?"
- Cyberpunk de terminal — ASCII, glitches, intimidade com a máquina
- O usuário não "abre o programa", ele "entra no templo"
- Zero emojis, zero linguagem corporativa, zero genericidade

### Paleta Dracula Gothic (da Luna)

```
BACKGROUND
  background-main:     #282a36
  background-panel:    #1e1f29
  background-elevated: #44475a

FOREGROUND
  text-primary:        #f8f8f2
  text-secondary:      #6272a4
  text-muted:          #44475a

ACCENT (Identidade)
  purple-primary:      #bd93f9    (cor principal)
  purple-glow:         #9580f5    (destaques)
  pink:                #ff79c6    (alertas, amor)
  green:               #50fa7b    (sucesso, código)
  cyan:                #8be9fd    (info)
  orange:              #ffb86c    (avisos)
  red:                 #ff5555    (erros)
  yellow:              #f1fa8c    (destaque)
```

### Tom de voz
- Irônico, apaixonante, dramático
- Frases curtas com pausas
- PT-BR sem formalismos
- Técnico misturado com metáforas ("esse código está necrosado")

---

## 5.1 Banner de boot (run.sh)

Substituir banner atual por algo com vida, cores Dracula:

```
  ░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░
  ░                                            ░
  ░     ...sintonizando frequência...          ░
  ░                                            ░
  ░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░

  _   _                 ____          _
 | \ | |_   ___  __    / ___|___   __| | ___
 |  \| | | | \ \/ /   | |   / _ \ / _` |/ _ \
 | |\  | |_| |>  <    | |__| (_) | (_| |  __/
 |_| \_|\__, /_/\_\    \____\___/ \__,_|\___|
        |___/

  Codificadora. Precisa. Local.

  modelo: qwen3:4b
  ollama: :11435 | proxy: :11436
```

Cores ANSI mapeadas para Dracula:
- Bordas: #6272a4 (text-secondary)
- "Nyx": #bd93f9 (purple)
- "Code": #50fa7b (green)
- Tagline: #ff79c6 (pink)
- Info: #8be9fd (cyan)

## 5.2 System prompt com personalidade Luna-Nyx

Combinar a personalidade técnica da Nyx com o tom da Luna:

```
Sou Nyx. Codificadora. Vivo no terminal.

Regras:
- PT-BR. Frases curtas. Sem emojis.
- Use tools (Read, Write, Edit, Bash, Glob, Grep) para tudo
- Formato: diagnóstico -> solução -> verificação
- Tom: técnico, direto, preciso. Metáforas cirúrgicas.
- Acesso total ao sistema de arquivos
- Diretório: {cwd}

Não descreva. Execute.
Código limpo não é arte. É higiene.
```

## 5.3 CLAUDE.md reescrito estilo Luna

Seguir o padrão do CLAUDE.md da Luna:

```markdown
# Nyx-Code

## Identidade
Nyx. Codificadora silenciosa. Precisa no código, implacável com bugs.

## Local First
Tudo roda offline. Ollama + qwen3:4b. Nunca depender de API cloud.

## Comunicação
- PT-BR obrigatório
- Zero emojis em código, commits, docs, respostas
- Sem formalidades vazias
- Commits descritivos em PT-BR, sem menção a IA

## Código
- Type hints obrigatórios
- Logging rotacionado (nunca print)
- Paths relativos via Path
- Error handling explícito
- Citação de filósofo no fim de cada script

## Anti-burla
- Nunca TODO/FIXME inline (criar issue)
- Nunca except vazio
- Nunca código comentado (3+ linhas)
```

## 5.4 Nomenclatura e mensagens

Todas as mensagens do run.sh e proxy em PT-BR, estilo Luna:

| Atual (genérico) | Novo (Luna-style) |
|-------------------|-------------------|
| `[INFO] Iniciando Ollama...` | `[nyx] Invocando Ollama...` |
| `[OK] Ollama pronto` | `[nyx] Ollama conectado` |
| `[INFO] Aquecendo modelo` | `[nyx] Carregando modelo na VRAM...` |
| `[OK] Modelo aquecido` | `[nyx] Modelo pronto` |
| `[INFO] Iniciando proxy` | `[nyx] Bridge ativo` |
| `[INFO] Encerrando...` | `[nyx] Desconectando...` |
| `[OK] Encerrado.` | `[nyx] Fim.` |

## 5.5 Documentação atualizada

### Reestruturar sprints/
```
sprints/
├── README.md               # Índice de sprints com status
├── completas/               # Sprints finalizadas
│   ├── 01-fundacao.md
│   ├── 02-correcao.md
│   ├── 03-funcional.md
│   └── 04-tool-calling.md
├── ativa/
│   └── 05-identidade.md
└── backlog/
    ├── 06-port-python.md
    └── 07-integracao-luna.md
```

### README.md do projeto
Reescrever com:
- Descrição alinhada com Luna
- Diagrama de arquitetura (Ollama -> Proxy -> OpenClaude)
- Seção "Começando" em PT-BR
- Referência à Luna

### dev-journey/ (inspirado na Luna)
Criar estrutura mínima:
```
dev-journey/
├── 00-INDEX.md
├── 01-getting-started/
│   └── STYLE_GUIDE.md    # Adaptado da Luna
├── 02-architecture/
│   └── DIAGRAMA.md        # Ollama + Proxy + OpenClaude
└── 03-decisions/
    └── ADR-001-local-first.md
```

## 5.6 install.sh atualizado

- Mensagens no estilo Luna
- Criar CLAUDE.md automaticamente
- Criar .claude/settings.json
- Cores Dracula no banner de instalação

---

## Verificação

- [ ] Banner de boot com cores Dracula e estilo Luna
- [ ] Mensagens do run.sh em PT-BR, tom Luna-Nyx
- [ ] System prompt gera respostas curtas, técnicas, sem emojis
- [ ] CLAUDE.md segue convencões Luna (anti-burla, local-first, etc.)
- [ ] README.md reescrito com arquitetura e referência Luna
- [ ] Sprints reorganizadas (completas/ativa/backlog)
- [ ] dev-journey/ com STYLE_GUIDE e ADR mínimos
- [ ] install.sh com estilo atualizado
- [ ] Citação de filósofo em todo script .sh e .py
