# SPRINT INPUT-SLASH-PATH-DISAMBIG-01 -- mensagem iniciando com `/` vira comando mesmo sendo caminho/frase

## 0. SPEC (machine-readable)

```yaml
sprint:
  id: INPUT-SLASH-PATH-DISAMBIG-01
  title: "Mensagem que comeca com `/` e sempre tratada como slash-command; `/home/andrefarias/.config/zsh quantos arquivos...` deu 'Comando desconhecido'. Disambiguar: so e comando se casar comando registrado; caminho/frase cai pra chat"
  onda: 47
  bloco: "47 -- UX/Input/FS-polish (Onda de Validação 2, 2026-06-25)"
  prioridade: ALTA
  tipo: Bugfix / Input routing (REPL + TUI)
  dependencias: []
  desbloqueia: []

  touches:
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/cli.py
      reason: "ponto onde o REPL decide se a entrada e slash-command (input.startswith('/')). Adicionar disambiguacao: e comando SO se o 1o token (sem a barra) casar um comando registrado E não parecer caminho. Senao -> chat (passa ao LLM, com a barra preservada no texto)."
      linhas_alvo: "dispatch de input / startswith('/') (confirmar via grep)"
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/agent/app.py
      reason: "TUI Textual: _dispatch_slash (mesmo gating). Aplicar a mesma disambiguacao do cli.py (fonte compartilhada idealmente)."
      linhas_alvo: "_dispatch_slash (confirmar)"

  creates: []
  removes: []

  forbidden:
    - "Quebrar comandos reais: /help, /commit, /status, /cd, etc. seguem funcionando exatamente igual"
    - "Stripar a barra do texto que vai pro LLM/output quando for chat (o dono quer ver a barra no output)"
    - "Logica gigante -- manter simples: (1) casa comando registrado? (2) senao, parece caminho/frase? -> chat"
    - "emoji / mencao a IA externa"

  tests:
    - cmd: "probe: '/home/andrefarias/.config/zsh quantos arquivos existem aqui?' -> não e 'Comando desconhecido'; vai pro LLM como mensagem (o agente pode entao list_files /home/.../zsh)"
      timeout: 60
      esperado: "tratado como chat"
    - cmd: "probe: '/help' -> abre o help (comando real intacto); '/commit' idem"
      timeout: 60
      esperado: "comandos reais funcionam"
    - cmd: "probe: '/comandoinexistente' (token único, sem cara de caminho) -> mensagem 'Comando desconhecido' + dica /help (comportamento de comando-errado preservado)"
      timeout: 60
      esperado: "bare token desconhecido ainda avisa"
    - cmd: "./run.sh --gauntlet --only rapido && bash scripts/sprint_invariants.sh"
      timeout: 400
      esperado: "verdes"

  acceptance_criteria:
    - "Entrada com `/` so dispara comando se casar comando registrado (1o token)"
    - "Caminho absoluto (`/x/...`), entrada com espaco/varias barras, ou comando inexistente que parece frase -> chat (LLM recebe o texto com a barra)"
    - "Token único desconhecido (cara de comando) -> mantem o aviso 'Comando desconhecido' + /help"
    - "Comandos reais 100% intactos; REPL e TUI consistentes"
    - "gauntlet rapido + invariantes 14/14; spec -> concluidos/"
```

---

**Status:** PENDENTE
**Data criação:** 2026-06-25
**Origem:** Onda de Validação 2 (teste as-user). `/home/andrefarias/.config/zsh quantos arquivos existem aqui?` -> "Comando desconhecido: /home/andrefarias/.config/zsh. Use /help...". Decisao do dono: combinar (a) cai pra chat se não casar comando + (b) heuristica de caminho.
**Modelo obrigatorio:** modelo de capacidade alta (sem subagentes; implementação direta)

---

## Problema

O REPL/TUI trata qualquer entrada que comeca com `/` como slash-command. Um caminho (`/home/...`) ou frase iniciada por `/` cai no dispatcher e vira "Comando desconhecido". Atrito real no uso (o dono perguntou de uma pasta absoluta e a Nyx recusou).

---

## Causa-raiz

O gating e `input.startswith('/')` sem verificar se o conteudo corresponde a um comando registrado nem se parece um caminho.

---

## Solucao proposta (combina decisao 1+2 do dono)

No ponto de dispatch (cli.py e app.py), antes de tratar como comando:
1. Extrair o 1o token (sem a barra). Se casar um **comando registrado** -> executa o comando (comportamento atual).
2. Senao, aplicar heuristica de caminho/frase: se parece caminho absoluto (`/algo/...`, multiplas barras) OU tem espaco (frase) -> **trata como chat** (envia ao LLM com a barra preservada no texto).
3. Senao (token único, sem cara de caminho, sem comando) -> mantem o aviso "Comando desconhecido" + dica /help.

Idealmente extrair a função de decisao para um lugar compartilhado entre cli.py e app.py (evita divergencia REPL/TUI, licao da ONDA-44 357).

---

## Proof-of-work esperado

```bash
# probes deterministicos da função de decisao (casa comando / caminho / frase / bare desconhecido)
./run.sh --gauntlet --only rapido
bash scripts/sprint_invariants.sh
python3 ~/.config/zsh/scripts/validar-acentuacao.py --paths nyx/cli.py nyx/agent/app.py
/home/andrefarias/.local/bin/ruff check nyx/cli.py nyx/agent/app.py
# runtime: subir a Nyx, digitar "/home/andrefarias/.config/zsh quantos arquivos" -> vai pro LLM (não 'Comando desconhecido')
```

---

## Criterio binario de aceite

- [ ] caminho/frase com `/` inicial -> chat (LLM recebe com a barra)
- [ ] comandos registrados intactos (/help, /commit, /cd...)
- [ ] bare token desconhecido -> aviso preservado
- [ ] REPL e TUI consistentes; gauntlet rapido + invariantes 14/14; spec -> concluidos/

---

## Riscos

| Risco | Mitigacao |
|-------|-----------|
| Heuristica classificar comando real como caminho | so vira chat se não casar comando registrado; comando sempre vence |
| Divergencia REPL vs TUI | extrair decisao para fonte unica usada nos dois |

---

*"A barra e do comando quando o comando existe; senao, e do caminho." -- anonimo*
