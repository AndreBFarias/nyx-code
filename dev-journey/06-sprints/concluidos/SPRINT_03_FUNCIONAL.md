# Sprint 3: Tornar o Agente Funcional (COMPLETO)

**Objetivo:** A TUI responde, executa tools, se identifica como Nyx,
e responde em tempo aceitável (< 30s por mensagem simples).

---

## Problemas atuais

1. **Não usa tools** — diz "não posso acessar o sistema de arquivos"
2. **Lento** — 1m44s para "olá", 33s-1m para respostas simples
3. **Identidade errada** — se identifica como "Qwen", não "Nyx"
4. **Reasoning exposto** — mostra raciocínio interno (\boxed{}, "The user greeted...")

---

## Correções

### 3.1 System prompt customizado para Nyx

Usar `--append-system-prompt` com instrução para:
- Identidade: "Você é Nyx, agente de código local"
- Linguagem: PT-BR
- Tools: explicitar que TEM acesso a Bash, Read, Edit, Write, Glob, Grep
- Comportamento: usar tools quando pedido, responder direto sem reasoning exposto

### 3.2 Desabilitar thinking/reasoning

O qwen3 tem modo "thinking" que expõe raciocínio interno.
Usar `--thinking disabled` ou flag equivalente para respostas diretas.

### 3.3 Velocidade

O modelo qwen3:4b com thinking ativado gera ~100+ tokens de raciocínio
antes da resposta real. Desabilitar thinking reduz de 1m44s para ~10-20s.

Se ainda lento: considerar qwen3:1.7b como alternativa rápida.

### 3.4 Verificar execução de tools

Testar que o ciclo funciona:
1. Usuário pede "leia main.py"
2. Modelo chama tool Read
3. Nyx executa a tool
4. Resultado retorna ao modelo
5. Modelo responde com análise

---

## Alterações no run.sh

```bash
node "$SCRIPT_DIR/bin/nyx" \
    --model "$MODEL" \
    --bare \
    --thinking disabled \
    --allowedTools "Bash" "Read" "Edit" "Write" "Glob" "Grep" \
    --dangerously-skip-permissions \
    --append-system-prompt "Você é Nyx, um agente de código local. Responda sempre em PT-BR. Quando o usuário pedir para ler, criar, editar arquivos ou executar comandos, USE as tools disponíveis (Read, Write, Edit, Bash, Glob, Grep). Nunca diga que não pode acessar o sistema de arquivos. Seja direto e conciso."
```

---

## Verificação

- [ ] `./run.sh` — "olá" respondido em < 30s
- [ ] "leia o arquivo main.py" — executa Read e mostra conteúdo
- [ ] "crie um arquivo hello.py com print('Nyx')" — executa Write
- [ ] "quem é você?" — responde "Nyx"
- [ ] Sem \boxed{}, sem reasoning exposto
- [ ] "liste os arquivos" — executa Glob ou Bash(ls)
