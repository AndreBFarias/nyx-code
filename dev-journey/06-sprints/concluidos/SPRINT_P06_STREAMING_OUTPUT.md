## 0. SPEC (machine-readable)

```yaml
sprint:
  id: P-06
  title: "Streaming + Rich output (token a token, cores, formatação)"
  touches:
    - path: nyx/agent/streaming.py
      reason: "Streaming de tokens do Ollama"
    - path: nyx/agent/output.py
      reason: "Rich output com cores Nyx + formatação markdown"
  acceptance_criteria:
    - "Tokens aparecem um a um no terminal"
    - "Cores Nyx (#00D4AA accent, #E8E8E8 texto)"
    - "Code blocks com syntax highlighting"
    - "Formatação de tool results (path, conteúdo, erro)"
```

---

# Sprint P-06 -- Streaming + Rich Output

**Status:** PENDENTE
**Prioridade:** ALTA
**Tipo:** Feature
**Dependências:** P-01
**Desbloqueia:** P-07

## Referência Luna

- `src/skills/code_agent/streaming.py`: StreamingCollector, callback de tokens
- `src/skills/code_agent/rich_output.py`: formatação Rich com cores da entidade

## Adaptação Nyx

Usar `rich` para:
- Streaming de tokens em tempo real
- Cores Nyx (accent=#00D4AA, primary=#E8E8E8, bg=#2A2C39)
- Syntax highlighting em code blocks
- Painel de tool results (caminho, conteúdo, erros)
- Barra de contexto (budget de tokens)

---

*"A forma segue a função." -- Louis Sullivan*
