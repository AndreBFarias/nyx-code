# Mapeamento Completo de Features -- Nyx-Code

> **Gerado por `scripts/sbom_sync.py` a partir de REGISTRY.yaml.**
> Não edite este arquivo manualmente; edite REGISTRY.yaml e rode `sbom_sync.py`.

## 1. Infraestrutura (Boot/Lifecycle)

| ID | Feature | Componente | Validação |
|----|---------|------------|-----------|

| I-01 | [?] Boot completo (Ollama + Proxy + TUI) | run.sh | Tempo de boot, todos os componentes respondendo |
| I-02 | [?] Kill de processos anteriores | run.sh | Porta livre antes de iniciar |
| I-03 | [?] Health check Ollama | run.sh | /api/version responde em <30s |
| I-04 | [?] Download automático de modelo | run.sh/install.sh | Modelo ausente -> pull automático |
| I-05 | [?] Warmup do modelo | run.sh | Primeira inferência antes da TUI |
| I-06 | [?] Cleanup ao sair (trap EXIT) | run.sh | Zero processos órfãos após Ctrl+C |
| I-07 | [?] Instalação idempotente | install.sh | Rodar 2x sem quebrar |
| I-08 | [?] Desinstalação limpa | uninstall.sh | Remove tudo, mantém código fonte |
| I-09 | [?] Seleção de modelo (--3b, --4b, --7b) | run.sh | Cada flag carrega modelo correto |
| I-10 | [?] Modo debug (--debug) | run.sh | Logs detalhados ativados |
| I-11 | [?] Modo headless (--headless) | run.sh | Sem banner, sem cores |

## 2. Proxy (Ponte OpenAI <-> Ollama)

| ID | Feature | Componente | Validação |
|----|---------|------------|-----------|

| P-01 | [?] Conversão /v1/chat/completions -> /api/chat | proxy.py | Request chega ao Ollama formato nativo |
| P-02 | [?] Injeção de think=false | proxy.py | Resposta sem reasoning tags |
| P-03 | [?] Injeção de num_gpu e num_ctx | proxy.py | Options corretas no request |
| P-04 | [?] Normalização de content array -> string | proxy.py | Content Anthropic-style convertido |
| P-05 | [?] Conversão de resposta Ollama -> OpenAI | proxy.py | tool_calls no formato OpenAI |
| P-06 | [?] Listagem de modelos (/v1/models) | proxy.py | Retorna modelos do Ollama |
| P-07 | [?] Propagação de tool_calls | proxy.py | Tool calls passam corretamente |
| P-08 | [?] Logging de requests/responses | proxy.py | Cada request logado com modelo, tools, resultado |

## 3. Tool Calling (6 tools)

| ID | Feature | Componente | Validação |
|----|---------|------------|-----------|

| T-01 | [?] Ler arquivo existente | Read | Retorna conteúdo correto |
| T-02 | [?] Ler arquivo inexistente (graceful) | Read | Erro informativo, sem crash |
| T-03 | [?] Criar arquivo novo | Write | Arquivo existe no disco após execução |
| T-04 | [?] Sobrescrever arquivo existente | Write | Conteúdo atualizado |
| T-05 | [?] Editar trecho de arquivo | Edit | SEARCH/REPLACE aplicado corretamente |
| T-06 | [?] Executar comando shell | Bash | Output do comando retornado |
| T-07 | [?] Comando com erro (exit code != 0) | Bash | Stderr retornado, sem crash |
| T-08 | [?] Buscar arquivos por padrão | Glob | Lista de arquivos correta |
| T-09 | [?] Buscar texto em arquivos | Grep | Linhas com match retornadas |
| T-10 | [?] Tool calling em cadeia (Read -> Edit) | Multi | Segundo turno usa resultado do primeiro |

## 4. Qualidade de Resposta

| ID | Feature | Componente | Validação |
|----|---------|------------|-----------|

| Q-01 | [?] Resposta em PT-BR | Idioma | Conteúdo em português |
| Q-02 | [?] Identidade Nyx | Personalidade | Não se identifica como Qwen/outro |
| Q-03 | [?] Concisão | Estilo | Respostas < 200 palavras para perguntas simples |
| Q-04 | [?] Uso proativo de tools | Comportamento | Chama tool em vez de descrever |
| Q-05 | [?] Precisão de argumentos | Tool call | Paths e parâmetros corretos |
| Q-06 | [?] Sem emojis na resposta | Estilo | Zero emojis |
| Q-07 | [?] Sem hallucination de paths | Precisão | Paths existem no projeto real |

## 5. Performance (KPIs)

| ID | Métrica | Unidade | Baseline |
|----|---------|---------|----------|

| K-01 | [?] Tempo de boot (Ollama pronto) | segundos | <30s |
| K-02 | [?] Tempo de warmup | segundos | <90s |
| K-03 | [?] TTFR (Time to First Response) - chat | segundos | <15s |
| K-04 | [?] TTFR - tool call simples | segundos | <20s |
| K-05 | [?] TTFR - tool call com conteúdo (Write) | segundos | <45s |
| K-06 | [?] Tokens por resposta (chat) | tokens | 30-100 |
| K-07 | [?] Tokens por resposta (tool call) | tokens | 200-800 |
| K-08 | [?] VRAM em uso estável | MiB | <2500 |
| K-09 | [?] VRAM pico durante inferência | MiB | <3500 |
| K-10 | [?] Tempo total do gauntlet | minutos | <20min |

## 6. Interface Visual

| ID | Feature | Componente | Validação |
|----|---------|------------|-----------|

| V-01 | [?] Banner ASCII com cores Nyx | run.sh | Cores #00D4AA no terminal |
| V-02 | [?] Mensagens [nyx] coloridas | run.sh | PRIMARY para sistema, GREEN ok, RED erro |
| V-03 | [?] Info de boot (modelo, portas) | run.sh | Modelo e portas exibidos |
| V-04 | [?] Citação de filósofo nos scripts | *.sh, *.py | Presente no fim de cada arquivo |
| V-05 | [?] Temas carregam corretamente (7 entidades) | nyx/themes/ | Cada tema retorna cores válidas |
| V-06 | [?] Fallback Dracula para tema inexistente | nyx/themes/ | Cores Dracula retornadas |
| V-07 | [?] Conversão hex -> ANSI 24-bit | nyx/themes/utils.py | Escape sequences corretas |

## 7. Configuração

| ID | Feature | Componente | Validação |
|----|---------|------------|-----------|

| C-01 | [?] .env carregado pelo run.sh | run.sh | Variáveis sobrescrevem defaults |
| C-02 | [?] NyxSettings carrega .env + CLI args | config/settings.py | Prioridade: CLI > .env > defaults |
| C-03 | [?] .claude/settings.json respeita tema dark | .claude/ | theme=dark, language=pt-BR |
| C-04 | [?] GSD.md guia canônico do projeto | GSD.md | Identidade Nyx aplicada |

## 8. Resiliência

| ID | Feature | Componente | Validação |
|----|---------|------------|-----------|

| R-01 | [?] Ollama cai durante operação | Proxy | Erro informativo, sem hang |
| R-02 | [?] Modelo não existe | run.sh | Pull automático ou erro claro |
| R-03 | [?] Porta já ocupada | run.sh | Kill anterior e retry |
| R-04 | [?] VRAM insuficiente | Proxy | num_gpu reduzido ou erro |
| R-05 | [?] Timeout de inferência | Proxy | Resposta em tempo máximo ou erro |
