## 0. SPEC (machine-readable)

```yaml
sprint:
  id: TUI-FIX-01
  title: "Banner único, limpo, sem ASCII corrompido"
  touches:
    - path: run.sh
      reason: "Remover função show_banner (ASCII + subtítulo + modelo/ollama/proxy)"
    - path: nyx/cli.py
      reason: "_build_banner vira fonte única; incorporar info modelo/ollama/proxy que estava no shell"
  n_to_n_pairs:
    - "Se _build_banner passa a mostrar ollama/proxy, run.sh não imprime mais essas linhas"
  forbidden:
    - "Deixar qualquer ASCII art decorativo com escapes duplos"
    - "Imprimir banner duas vezes no boot"
    - "Quebrar o auto-tune log ([nyx] Auto-tune: num_gpu=23 ...) — esse é informação útil"
  tests:
    - cmd: "./run.sh --gauntlet --only rapido"
      timeout: 120
    - cmd: "manual: ./run.sh -- contar quantos banners aparecem (esperado: 1)"
      timeout: 30
  acceptance_criteria:
    - "Boot mostra EXATAMENTE um banner (a caixa ╭─╮ do Python)"
    - "Nenhum ASCII art de 'Nyx Code' com caracteres \\\\ ou /_/\\_\\"
    - "Linhas [nyx] Iniciando... permanecem (funcionais, não decorativas)"
    - "A animação '...sintonizando frequencia...' vai embora ou vira 1 linha limpa"
    - "A pergunta 'Abrir no Antigravity?' investigada: se for do Nyx, removida"
    - "Caixa Python mostra: título + modelo + projeto + tools + ollama port + proxy port"
    - "Em terminal <60 cols: degrada pra texto simples '── Nyx v1.2.0 · qwen3:4b · 35 tools ──'"
```

---

# Sprint TUI-FIX-01 -- Banner único e limpo

**Status:** CONCLUIDA (header corrigido em MASTER-CLEANUP-02 2026-05-20; presença em concluidos/ implica CONCLUIDA conforme convenção do projeto)
**Data:** 2026-04-17
**Prioridade:** ALTA
**Tipo:** Fix + UX
**Dependências:** --
**Desbloqueia:** TUI-FIX-02, TUI-FIX-03

---

## Problema / Contexto

Screenshot do usuário mostra DOIS banners executando no boot:

1. **Banner 1** (shell, `run.sh:show_banner`): ASCII art "Nyx Code" de 5 linhas com escapes duplos quebrados + subtítulo "Codificadora. Precisa. Local." + linhas `modelo`, `ollama`, `proxy`
2. **Banner 2** (Python, `nyx/cli.py:_build_banner`): Caixa `╭─╮` compacta com `Nyx -- Code Agent Local v1.2.0 / modelo / projeto / tools / 100% offline`

O ASCII art está corrompido visualmente -- mistura `\\` com `/` em combinações que desalinham em fontes monospace padrão. Os dois banners mostram informação sobreposta (modelo duas vezes).

Claude Code CLI (referência do usuário) usa **um único banner compacto**. ASCII art decorativo é ruído sem valor informacional.

## Implementação

### Fase 1 -- Auditar run.sh

Localizar e remover:
- `show_banner()` inteiro (cerca de linhas 282-310)
- Chamada de `show_banner` no fluxo de boot
- Bloco `...sintonizando frequencia...` se for decorativo (se for função de warmup real, manter mas sem visual art)

Manter:
- `[nyx] Iniciando Ollama...` e linhas funcionais similares
- `[nyx] Modelo: qwen3:4b`, `[nyx] Auto-tune: num_gpu=23`, `[nyx] Modelo pré-carregado`, `[nyx] Iniciando proxy na porta 11436`, `[nyx] Proxy pronto (PID: X)`
- Essas são informação útil, não decoração

### Fase 2 -- Auditar "Abrir no Antigravity?"

Screenshot 8 mostra pergunta "Abrir no Antigravity? (s/N)" antes do boot. Investigar origem:
- Buscar em `run.sh` por `Antigravity`
- Se for do Nyx: remover ou tornar opcional via flag
- Se for de outra camada (profile shell do usuário): não tocar, mas documentar

### Fase 3 -- Enriquecer _build_banner

Incorporar as info que o shell tinha na caixa Python (já que são as únicas relevantes):

```
╭────────────────────────────────────────────╮
│  Nyx -- Code Agent Local v1.2.0            │
│  modelo   qwen3:4b                         │
│  projeto  Nyx-Code                         │
│  tools    35 · 100% offline                │
│  ollama   :11435  ·  proxy  :11436         │
╰────────────────────────────────────────────╯

/help para comandos. Ctrl+D para sair.
```

### Fase 4 -- Fallback terminal estreito

Em `_build_banner`, detectar `shutil.get_terminal_size().columns`. Se <60, renderizar linha simples:

```
── Nyx v1.2.0 · qwen3:4b · 35 tools · 100% offline ──
```

## Verificação

```bash
./run.sh
# Contar banners: deve ser exatamente 1
# Verificar ausência de ASCII "Nyx Code" com \\
# resize -s 24 50; ./run.sh  -- ver fallback
./run.sh --gauntlet --only rapido
```

- [ ] Um banner apenas
- [ ] ASCII quebrado removido
- [ ] `[nyx] Iniciando...` preservado
- [ ] Banner em `<60` cols vira 1 linha
- [ ] Antigravity investigado e resolvido
- [ ] Gauntlet rapido passa

---

*"Menos é mais." -- Mies van der Rohe*
