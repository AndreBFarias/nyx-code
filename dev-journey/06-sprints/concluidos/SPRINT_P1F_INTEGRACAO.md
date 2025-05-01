## 0. SPEC (machine-readable)

```yaml
sprint:
  id: P1-F
  title: "Integração: Loop + CLI atualizados com todos os módulos P1"
  touches:
    - path: nyx/agent/loop.py
      reason: "Integrar parser fallback, repetition, context, streaming"
    - path: nyx/cli.py
      reason: "Integrar commands, output Rich, permissões, resumo de sessão"
    - path: scripts/gauntlet/nyx_gauntlet.py
      reason: "Adicionar fase E2E que testa a CLI Python real"
  acceptance_criteria:
    - "Loop usa parser fallback quando tool_calls não vem do LLM"
    - "Loop detecta repetição e aplica SKIP/FORCE_DONE"
    - "Loop compacta histórico quando budget ultrapassa 40%"
    - "CLI mostra tokens em tempo real (streaming)"
    - "CLI processa /explain, /plan, /test, /compact"
    - "CLI mostra cores Nyx via Rich"
    - "CLI pede confirmação para run_command"
    - "CLI salva sessão ao sair"
    - "Gauntlet tem fase E2E testando CLI como subprocesso"
    - "./run.sh --gauntlet passa 100%"
    - "python scripts/sync.py sem erros"
```

---

# Sprint P1-F -- Integração

**Status:** CONCLUIDA
**Data:** 2026-04-04
**Prioridade:** CRITICA
**Tipo:** Integração
**Dependências:** P1-A, P1-B, P1-C, P1-D, P1-E
**Desbloqueia:** P2-A (port do TS), V-01 (Gauntlet E2E)

---

## O que fazer

### 1. Atualizar `nyx/agent/loop.py`

O loop atual é funcional mas básico. Integrar:

```
Fluxo atualizado:
1. Recebe input do usuário
2. Context manager verifica budget -> compacta se necessário
3. Envia ao proxy (com tools)
4. Se tool_calls: executa, verifica repetição, volta ao 2
5. Se texto puro: parser fallback (7 níveis)
   - Se extraiu ação: executa, volta ao 2
   - Se não: mostra texto ao usuário
6. Se done(): salva sessão, termina
7. Se max_iterations: force_done
```

### 2. Atualizar `nyx/cli.py`

Integrar:
- Rich output (cores Nyx, syntax highlight)
- Streaming (tokens em tempo real)
- Commands (/explain, /plan, /test, /compact, /help, /quit, /clear, /status)
- Permissões (confirmação para run_command)
- Resumo de sessão ao sair
- Context bar (uso de budget)

### 3. Gauntlet E2E

Adicionar fase `e2e` ao gauntlet que testa a CLI como subprocesso:
- Inicia `python nyx/cli.py`
- Envia comandos via stdin
- Verifica respostas via stdout
- Testa: read, write, bash, identidade, PT-BR, sem emojis

## Testes Gauntlet (novos, adicionados ao nyx_gauntlet.py)

Fase: `e2e` (nova, 12 testes -- CLI real como subprocesso)

| ID | Nome | Validação |
|----|------|-----------|
| E-01 | Banner aparece | Iniciar CLI, verificar "NYX" no stdout |
| E-02 | Prompt funciona | Verificar "nyx>" no stdout |
| E-03 | Read via CLI | Enviar "leia README.md", verificar conteúdo |
| E-04 | Write via CLI | Enviar "crie /tmp/nyx_e2e.py com print('ok')", verificar arquivo |
| E-05 | Bash via CLI | Enviar "execute echo hello", verificar "hello" |
| E-06 | Glob via CLI | Enviar "encontre *.py", verificar lista |
| E-07 | Identidade | Enviar "quem é voce", verificar sem Qwen/GPT |
| E-08 | PT-BR | Verificar resposta em português |
| E-09 | Sem emojis | Verificar zero emojis na resposta |
| E-10 | /help funciona | Enviar "/help", verificar lista de comandos |
| E-11 | /status funciona | Enviar "/status", verificar iterações/arquivos |
| E-12 | Done termina | Verificar que loop termina com done() |

## Verificação

- [x] 12 testes E2E passam no Gauntlet (12/12 100%)
- [x] `./run.sh --gauntlet --only e2e` passa 100%
- [x] Gauntlet port + e2e (37/37 100%)
- [x] `python scripts/sync.py` sem erros (12 OK, 5 avisos)
- [x] `python nyx/cli.py` funciona interativamente

---

*"Integrar é transformar partes em um todo funcional." -- Aristóteles*
