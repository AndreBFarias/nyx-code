# PLUGIN_API — Como criar plugins para o Nyx (PLUGINS-01)
> Sistema de plugins instaláveis em `~/.nyx/plugins/`. Cada plugin é uma pasta
> com `manifest.toml` e arquivos Python. Tools e commands são registrados
> via decoradores idênticos aos nativos (`@nyx_command` e a Tool API).

## Estrutura mínima

```
~/.nyx/plugins/
  meu-plugin/
    manifest.toml
    meu-plugin.py
```

## manifest.toml (schema)

```toml
[plugin]
name = "meu-plugin"          # obrigatório
version = "0.1.0"            # obrigatório
description = "Faz X"        # obrigatório
tools = ["minha_tool"]       # opcional
commands = ["meu-cmd"]       # opcional
```

## Comandos

| Comando                  | Efeito                                              |
|--------------------------|-----------------------------------------------------|
| `/plugin list`           | Lista plugins descobertos.                          |
| `/plugin reload`         | Re-descobre + re-importa todos.                     |
| `/plugin install <path>` | Copia pasta para `~/.nyx/plugins/`.                 |
| `/plugin uninstall <n>`  | Remove plugin pelo nome.                            |

## Restrições de AST (segurança)

- Permitido no top-level: import, def, class, assign, docstring.
- Proibido no top-level: chamadas de função soltas, print, subprocess.

Inicialize estado dentro de funções chamadas sob demanda.

## Variáveis de ambiente

- `NYX_PLUGINS_DIR` — override do diretório de plugins (default `~/.nyx/plugins`).

## Limitações MVP (PLUGINS-01)

- Tools de plugins não aparecem automaticamente no ToolRegistry —
  fechamento em PLUGINS-02.
- AST check é conservador; pode rejeitar expressões intencionais raras.

## Referências

- ADR-001 Local First.
- ADR-013 Integração Obrigatória.
- MCP-SERVER-01 (modelo similar via JSON-RPC).
