# Nyx-Code

Agente de código local, 100% Python, com Ollama e qwen2.5-coder.

Projeto standalone que funciona no terminal e integra com a Luna como agente coder da entidade Nyx.

## Instalação

```bash
./install.sh
```

Baixa o binário do Ollama, cria ambiente virtual, instala dependências e baixa os modelos
qwen2.5-coder:3b e 7b para dentro do projeto.

## Uso

```bash
./run.sh          # Inicia com qwen2.5-coder:3b (padrão)
./run.sh --7b     # Inicia com qwen2.5-coder:7b (limite 2.5GB VRAM)
./run.sh --debug  # Modo debug com logs detalhados
```

## Remoção

```bash
./uninstall.sh        # Remove modelos, venv e binário Ollama
./uninstall.sh --full # Remove tudo incluindo .env
```

## Estrutura

```
nyx/
├── agent/       # Loop do agente, parser, sessão
├── tools/       # Ferramentas (read, edit, create, search, bash, git)
├── providers/   # Ollama client, compatibilidade OpenAI
├── context/     # Gerenciamento de contexto e tokens
├── config/      # Configuração centralizada
├── interface/   # Interface terminal customizada
└── integration/ # Protocolo de integração com Luna
```

## Requisitos

- Python 3.10+
- GPU NVIDIA (opcional, melhora performance)
- ~8 GB de espaço em disco (modelos)
