# Sprint 3: Interface e Cosmetica

**Objetivo:** Interface terminal customizada da Nyx com identidade visual propria.

---

## 3.1 Interface principal

| # | Modulo | Destino | Descricao |
|---|--------|---------|-----------|
| 1 | App principal | `nyx/interface/app.py` | Entry point da interface, event loop |
| 2 | Chat interativo | `nyx/interface/chat.py` | Input/output de conversas |
| 3 | Output Rich | `nyx/interface/output.py` | Formatacao de codigo, diffs, erros |
| 4 | Streaming | `nyx/interface/streaming.py` | Streaming de respostas em tempo real |
| 5 | Comandos | `nyx/interface/commands.py` | Sistema de slash commands |
| 6 | Completer | `nyx/interface/completer.py` | Tab completion |
| 7 | Confirmacao | `nyx/interface/confirmation.py` | Dialogo S/N para acoes destrutivas |

Port de referencia:
- `rich_output.py` (11.6KB) -> `nyx/interface/output.py`
- `streaming.py` (4KB) -> `nyx/interface/streaming.py`
- `commands.py` + `command_registry.py` (11KB) -> `nyx/interface/commands.py`
- `cli_completer.py` (2.8KB) -> `nyx/interface/completer.py`

---

## 3.2 Identidade visual Nyx

### Paleta de cores

- **Primaria:** Roxo/violeta (MAGENTA `\033[0;35m`)
- **Secundaria:** Cyan para destaques
- **Sucesso:** Verde
- **Erro:** Vermelho
- **Aviso:** Amarelo
- **Fundo:** Escuro (terminal padrao)

### Banner ASCII

Arte da Nyx na inicializacao, estilo entidade Luna.
Dimensoes: ~50 colunas x ~10 linhas.

### Prompt

```
Nyx [qwen-3b] >
```

Formato: nome + modelo ativo + indicador de status.

### Barra de status

```
[||||                ] ctx: 20% | iter: 3/50 | files: 2 | edits: 1 | 12.5s
```

Mesma estrutura que o code agent da Luna, com cores Nyx.

### Caixas diff

```
+-- diff ------------------------------------------+
| --- arquivo.py                                   |
| +++ arquivo.py                                   |
| @@ -10,3 +10,4 @@                                |
|   linha existente                                |
| + linha adicionada                               |
+--------------------------------------------------+
```

Bordas estilizadas com cores Nyx.

### Mensagens de erro

Claras, com sugestoes de correcao:

```
[ERRO] Arquivo nao encontrado: src/main.py
  Caminhos similares: main.py, src/app/main.py
  Use list_files para ver a estrutura do projeto.
```

---

## 3.3 Sistema de comandos

```
/help           - Lista de comandos
/clear          - Limpar historico
/session        - Info da sessao atual
/sessions       - Listar sessoes salvas
/load <id>      - Carregar sessao
/model          - Ver modelo ativo
/model 3b|7b    - Trocar modelo
/debug          - Toggle modo debug
/stats          - Estatisticas da sessao
/undo           - Desfazer ultima acao
/diff           - Git diff
/exit           - Sair
```

---

## 3.4 Polimento

- Historico de comandos com setas (prompt-toolkit)
- Autocomplete de paths, comandos, flags
- Mensagens de erro com contexto e sugestoes
- Help contextual
- Formatacao de codigo com syntax highlighting (Rich)
- Spinners e indicadores de progresso durante operacoes
- Modo silencioso para integracao (sem output decorativo)

---

## Verificacao

- [ ] Interface inicia com banner Nyx e cores proprias
- [ ] Prompt customizado funcional (nome + modelo + status)
- [ ] Barra de status com ctx%, iter, files, tempo
- [ ] Todos os slash commands funcionando
- [ ] Tab completion para paths e comandos
- [ ] Historico de comandos com setas
- [ ] Output de codigo com syntax highlighting
- [ ] Diffs formatados com estilo Nyx
- [ ] Mensagens de erro com sugestoes
- [ ] Animacoes de loading suaves
