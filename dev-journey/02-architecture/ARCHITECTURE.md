# Arquitetura Nyx-Code

**Atualizado:** 2026-05-21
**Nota:** este documento descreve a arquitetura conceitual. Para contagens em runtime (tools/commands/services/ADRs) e estado do gate v1.0, ver `dev-journey/08-templates/PROJECT_SNAPSHOT.md` (fonte autoritativa).

---

## Visão geral

```
                     ┌──────────────────────────────────────────┐
                     │              Nyx CLI (nyx/cli.py)         │
                     │  REPL: input -> AgentLoop -> output       │
                     │  Headless: JSON stdin/stdout              │
                     └──────────────────┬───────────────────────┘
                                        │
              ┌─────────────────────────┼─────────────────────────┐
              │                         │                         │
     ┌────────┴────────┐    ┌───────────┴──────────┐   ┌─────────┴────────┐
     │   Commands (67)  │    │   AgentLoop          │   │  Services (15)   │
     │  /help /commit   │    │  nyx/agent/loop/     │   │  tokens, hooks   │
     │  /diff /doctor   │    │  plan-execute-observe │   │  memory, compact │
     └─────────────────┘    └───────────┬──────────┘   └──────────────────┘
                                        │
              ┌─────────────────────────┼─────────────────────────┐
              │                         │                         │
     ┌────────┴────────┐    ┌───────────┴──────────┐   ┌─────────┴────────┐
     │   ActionParser   │    │   ToolRegistry (35)  │   │  ContextBudget   │
     │  7 níveis        │    │  read, write, edit   │   │  4 níveis        │
     │  EXACT->IMPLICIT │    │  bash, glob, search  │   │  compactação     │
     └─────────────────┘    └───────────┬──────────┘   └──────────────────┘
                                        │
              ┌─────────────────────────┼─────────────────────────┐
              │                         │                         │
     ┌────────┴────────┐    ┌───────────┴──────────┐   ┌─────────┴────────┐
     │ PermissionChecker│    │  RepetitionDetector  │   │  StreamingCollect│
     │ auto/confirm/deny│    │  exact/semantic/cycle │   │  token a token   │
     └─────────────────┘    └──────────────────────┘   └──────────────────┘
                                        │
                             ┌──────────┴───────────┐
                             │   Proxy (:11436)      │
                             │   think=false         │
                             │   /v1/ -> /api/chat   │
                             └──────────┬───────────┘
                                        │
                             ┌──────────┴───────────┐
                             │   Ollama (:11435)     │
                             │   qwen2.5-coder:3b    │
                             │   GPU num_gpu=12      │
                             └──────────────────────┘
```

## Fluxo de execução

1. Usuário digita no REPL (ou envia JSON no headless)
2. Se começa com `/` -> `handle_command()` -> retorna texto ou magic string
3. Se texto normal -> `AgentLoop.run(input)`
4. Loop: envia ao LLM com tools + histórico
5. Se LLM retorna `tool_calls` -> verifica permissões -> executa via ToolRegistry
6. Se LLM retorna texto puro -> ActionParser tenta extrair ação (7 níveis)
7. Se `done()` -> salva sessão, retorna resumo
8. Se max_iterations -> force_done

## Parser: 7 níveis de fallback

| Nível | Nome | Exemplo |
|-------|------|---------|
| 1 | EXACT | `ACTION: read_file\nPATH: README.md\n---` |
| 2 | FUNCTION_CALL | `read_file("README.md")` |
| 3 | RELAXED | `action: read_file\npath: readme.md` |
| 4 | BARE_TOOL | `read_file README.md` |
| 5 | CODE_BLOCK | ````python\nprint('ok')\n```` |
| 6 | PATH_INTENT | `Vou ler o arquivo README.md` |
| 7 | IMPLICIT_DONE | `Pronto, tarefa concluída` |

## Permissões: 4 níveis

| Nível | Tools | Comportamento |
|-------|-------|---------------|
| auto_approve | read, glob, search, list, done, analyze, brief | Executa sem perguntar |
| confirm_once | write, edit, create, patch, multi_edit | Pergunta 1x por sessão |
| always_confirm | run_command, repl | Sempre pergunta |
| deny | rm -rf, sudo, .env, .git/ | Bloqueia |

## Compactação: 4 níveis

| Nível | Trigger | Ação |
|-------|---------|------|
| 0 | < 40% budget | Histórico completo |
| 1 | 40-60% | Recentes completos + antigos compactados |
| 2 | 60-85% | Só decisões-chave + contexto de arquivos |
| 3 | > 85% | Truncamento agressivo + aviso |

## Headless Protocol (stdin/stdout JSON)

| Tipo | Input | Output |
|------|-------|--------|
| ping | `{"type":"ping"}` | `{"type":"pong","tools":34}` |
| status | `{"type":"status"}` | `{"type":"status","tools":34,"history":0,...}` |
| tools | `{"type":"tools"}` | `{"type":"tools","list":[...],"count":34}` |
| session | `{"type":"session"}` | `{"type":"session","files_read":0,...}` |
| request | `{"type":"request","content":"..."}` | `{"type":"response","state":"done",...}` |
| reset | `{"type":"reset"}` | `{"type":"ok","message":"Sessão resetada"}` |
| desconhecido | `{"type":"xyz"}` | `{"type":"error","message":"Tipo desconhecido: xyz"}` |

## Origem do código

| Origem | O que veio | Adaptações |
|--------|-----------|-----------|
| OpenClaude TS (`openclaud/src/`) | 40 tools, 98 commands, 35 services | Port 1:1 para Python | <!-- noqa-anonimato --> <!-- noqa-cli-externo -->
| Luna (`Luna/src/skills/code_agent/`) | Parser, loop, session, permissions, etc. | Ajuste de imports, cores, paths |
| Nyx original | Proxy, themes, config, install | Código próprio do projeto |

---

*"Arquitetura é decisão congelada." -- Grady Booch*
