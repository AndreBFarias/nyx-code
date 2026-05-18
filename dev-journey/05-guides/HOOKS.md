# HOOKS — Hooks dinâmicos por evento (HOOKS-DYNAMIC-01)

O Nyx lê `~/.nyx/settings.json` para descobrir hooks que rodam em
eventos do REPL/loop. Cada hook é um comando shell (ou `skill:<name>`)
com matcher regex opcional, timeout e flag `block_on_failure`.

## Eventos suportados

| Evento             | Quando dispara                                   | Payload                              |
|--------------------|--------------------------------------------------|--------------------------------------|
| `PreToolUse`       | Antes da execução de uma tool                    | `{tool_name, tool_input}`            |
| `PostToolUse`      | Depois da execução de uma tool                   | `{tool_name, tool_result}`           |
| `UserPromptSubmit` | Quando o usuário envia uma mensagem              | `{content}`                          |
| `Stop`             | Quando o turno do agent termina                  | `{turn_summary}`                     |

## Schema (`~/.nyx/settings.json`)

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "command": "python3 /home/user/.nyx/guard.py",
        "matcher": "write_file|edit_file",
        "timeout": 5,
        "block_on_failure": true
      }
    ],
    "Stop": [
      {
        "command": "skill:my-summary-skill",
        "timeout": 30
      }
    ]
  }
}
```

## Contrato do hook shell

- **Stdin:** JSON com payload do evento.
- **Stdout:** mensagem para log/contexto (até 5 MB).
- **Exit code:** 0 = sucesso; ≠ 0 = falha (se `block_on_failure=true`,
  bloqueia o evento; senão, apenas warning no log).
- **Env limpo:** só `PATH`, `HOME`, `LANG`, `LC_ALL`, `USER`, `SHELL`
  são passados (whitelist). Outras vars (API keys) NÃO são expostas.

## Skill hooks (`skill:<name>`)

Reservado para integração futura com a Skill tool — no MVP, apenas
loga e retorna OK. Será fechado na sprint HOOKS-DYNAMIC-02.

## Timeouts

- Default 30s; máximo 300s. Valores acima do limite são truncados.
- Timeout marca o hook como falho. Comportamento depende de
  `block_on_failure`.

## Boot tolerante

- `~/.nyx/settings.json` ausente: nenhum hook ativo, boot segue.
- JSON malformado: warning no log, hooks desabilitados, boot segue.
- Matcher regex inválido: hook ignorado individualmente; outros seguem.

## Limitações MVP (HOOKS-DYNAMIC-01)

- Hooks ainda não estão amarrados no `ToolRegistry` / `_core.py` — `HookRuntime`
  é instanciável e executável, mas a integração no ciclo de execução fica para
  HOOKS-DYNAMIC-02.
- `skill:` é placeholder.

## Referências

- ADR-001 Local First (hooks são locais).
- ADR-013 Integração Obrigatória.
- MCP-SERVER-01 / PLUGINS-01 (padrão MVP semelhante).
