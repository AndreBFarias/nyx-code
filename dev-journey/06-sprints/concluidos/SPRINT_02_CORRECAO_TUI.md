# Sprint 2: Correção TUI + Ollama

**Objetivo:** Fazer a TUI funcionar de forma estável com o Ollama local
e qwen2.5-coder:3b/7b. O Sprint 1 montou a infraestrutura e a interface carrega,
mas as requests falham com "API Error: fetch failed".

---

## Diagnóstico

### Sintoma
- A interface da TUI carrega corretamente (modelo, endpoint exibidos)
- Ao enviar mensagem, após ~2m30s: "API Error: fetch failed"
- O Ollama responde normalmente via curl (testado e confirmado)

### Causas prováveis

1. **`max_completion_tokens` vs `max_tokens`:**
   O shim envia `max_completion_tokens` (padrão OpenAI). Ollama só suporta `max_tokens`.
   Resultado: Ollama ignora ou rejeita o campo, resposta pode travar.

2. **Tool calling com modelo 3b:**
   A TUI envia todas as tools do Claude Code (Bash, FileRead, FileEdit, etc.)
   na request. O qwen2.5-coder:3b tem suporte limitado a tool calling — pode
   gerar respostas malformadas ou travar.

3. **Timeout do Node.js fetch:**
   O fetch padrão do Node.js tem timeout alto. Com o modelo 3b, a primeira
   inferência com tools pode demorar mais que o esperado, causando "fetch failed".

4. **Streaming incompatível:**
   O shim usa streaming SSE por padrão. O formato de streaming do Ollama
   pode ter diferenças sutis que causam parse errors no shim.

5. **Variáveis de ambiente persistidas:**
   A TUI pode estar lendo configurações salvas de sessões anteriores
   em `~/.claude/` que sobrescrevem as variáveis de ambiente.

---

## Plano de correção

### 2.1 Diagnóstico detalhado
- Rodar nyx com `--debug --debug-file /tmp/nyx_debug.log`
- Capturar a request exata que o shim envia ao Ollama
- Capturar a resposta (ou falta dela) do Ollama
- Verificar se o Ollama crashou ou está processando

### 2.2 Testar API diretamente com formato do shim
Reproduzir exatamente a request que a TUI faz:
```bash
curl -X POST http://127.0.0.1:11435/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "qwen2.5-coder:3b",
    "messages": [{"role":"system","content":"You are a coding assistant"},{"role":"user","content":"olá"}],
    "max_completion_tokens": 2048,
    "stream": true,
    "tools": [{"type":"function","function":{"name":"Bash","description":"Execute bash","parameters":{"type":"object","properties":{"command":{"type":"string"}}}}}]
  }'
```
Testar variações: sem tools, sem stream, com `max_tokens` em vez de `max_completion_tokens`.

### 2.3 Configuração da TUI para Ollama
Opções a explorar:
- `--max-tokens` flag se existir
- `--no-tools` ou `--allowedTools` para limitar tools
- Variáveis de ambiente para desabilitar streaming
- Usar `--dangerously-skip-permissions` para simplificar requests

### 2.4 Patch do shim (se necessário)
Se o problema for no código do shim (`cli.mjs`), criar um patch:
- Wrapper script que intercepta e corrige a request antes de enviar
- Ou: criar um proxy HTTP entre a TUI e o Ollama que traduz campos incompatíveis
- Ou: editar diretamente o `cli.mjs` para corrigir `max_completion_tokens` -> `max_tokens`

### 2.5 Proxy de compatibilidade (alternativa)
Se o patch direto for complexo, criar um proxy Python leve:
```
nyx -> proxy Python (porta 11436) -> Ollama (porta 11435)
```
O proxy:
- Recebe request no formato OpenAI do shim
- Corrige campos incompatíveis (max_completion_tokens, tools, stream_options)
- Encaminha para o Ollama
- Retorna resposta para a TUI

### 2.6 Configuração de timeout
- Aumentar timeout do fetch na TUI (se configurável)
- Ou configurar via variável de ambiente `OPENAI_TIMEOUT`
- O qwen2.5-coder:3b pode levar 30-60s por resposta

### 2.7 Limpeza de configurações persistidas
- Verificar e limpar sessões/configurações em `~/.claude/` que possam interferir
- Garantir que a TUI usa apenas as variáveis de ambiente definidas no run.sh

---

## Atualização do run.sh

Após diagnóstico, atualizar o run.sh com:
- Variáveis de ambiente adicionais necessárias
- Proxy se necessário
- Timeout configurado
- Flags da TUI ajustadas

---

## Verificação

- [ ] `./run.sh --3b` abre interface e responde a "olá" em até 60s
- [ ] `./run.sh --7b` funciona com modelo 7b
- [ ] Tool calling funciona (pedir para ler um arquivo)
- [ ] Streaming funciona (tokens aparecem progressivamente)
- [ ] Encerramento limpo (Ctrl+C para Ollama)
- [ ] Sem erros "fetch failed" ou timeout

---

## Arquivos a modificar

- `run.sh` — variáveis de ambiente, flags, possivelmente proxy
- `.env.example` — novas variáveis de timeout
- Possivelmente: `nyx/proxy.py` — proxy de compatibilidade (se necessário)
- Possivelmente: `reference/dist/cli.mjs` — patch direto (último recurso)
