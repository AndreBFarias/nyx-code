# SPRINT TOOL-SELECT-FILE-VS-DIR-01 -- glob/list num arquivo (e read numa pasta) caem em vazio em vez de fazer o certo

## 0. SPEC (machine-readable)

```yaml
sprint:
  id: TOOL-SELECT-FILE-VS-DIR-01
  title: "Quando o alvo de glob/list_files e um ARQUIVO (ex.: ~/.bashrc), retorna vazio; quando read_file recebe uma PASTA, falha. Tornar as tools espertas: arquivo->le/avisa, pasta->lista/avisa -- mitiga o 3b escolher a tool errada"
  onda: 47
  bloco: "47 -- UX/Input/FS-polish (Onda de Validacao 2, 2026-06-25)"
  prioridade: MEDIA
  tipo: Bugfix / Tools (ergonomia + mitiga ADR-034)
  dependencias: [FS-TILDE-EXPAND-01]
  desbloqueia: []

  touches:
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/agent/tools/glob_tool.py
      reason: "se o `path` resolvido for um ARQUIVO (nao dir), em vez de 'Nenhum arquivo encontrado', retornar mensagem clara ('X e um arquivo, nao uma pasta; use read_file') OU tratar o arquivo como o unico match (decidir o mais util/simples)."
      linhas_alvo: "execute (apos validate_path, checar is_file/is_dir)"
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/agent/tools/list_files.py
      reason: "idem glob: alvo arquivo -> mensagem clara em vez de erro/vazio confuso."
      linhas_alvo: "execute"
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/agent/tools/read_file.py
      reason: "se o `file_path` resolvido for uma PASTA, em vez de erro cru, retornar mensagem clara ('X e uma pasta; use list_files') -- ajuda o 3b a se recuperar."
      linhas_alvo: "execute"

  creates: []
  removes: []

  forbidden:
    - "Auto-trocar a tool silenciosamente de forma surpreendente -- a mensagem deve ser CLARA e o resultado util (o 3b le a mensagem e se corrige); nada de fingir sucesso"
    - "Quebrar o caso normal (glob/list em pasta; read em arquivo) -- regressao zero"
    - "Mexer no validate_path / acesso (e a 386) -- aqui so a logica de is_file vs is_dir nas tools"
    - "emoji / mencao a IA externa"

  tests:
    - cmd: "probe: glob/list_files com path = um arquivo (ex.: ~/.bashrc apos 386) -> mensagem clara util (nao 'Nenhum arquivo encontrado')"
      timeout: 60
      esperado: "mensagem orienta usar read_file (ou le o arquivo)"
    - cmd: "probe: read_file com file_path = uma pasta -> mensagem clara ('e uma pasta; use list_files'), nao erro cru"
      timeout: 60
      esperado: "mensagem orienta"
    - cmd: "probe regressao: glob/list em pasta normal e read em arquivo normal -> identicos a hoje"
      timeout: 60
      esperado: "regressao zero"
    - cmd: "./run.sh --gauntlet --only fs_arbitrary && ./run.sh --gauntlet --only rapido && bash scripts/sprint_invariants.sh"
      timeout: 600
      esperado: "verdes"

  acceptance_criteria:
    - "glob/list num arquivo -> resultado util (mensagem clara ou le o arquivo), nao vazio confuso"
    - "read_file numa pasta -> mensagem clara (use list_files), nao erro cru"
    - "casos normais intactos (regressao zero, fs_arbitrary + rapido verdes)"
    - "invariantes 14/14; spec -> concluidos/"
```

---

**Status:** CONCLUIDA (2026-06-25, commit 48c3f2f)
**Data criacao:** 2026-06-25
**Origem:** Onda de Validacao 2 (teste as-user). "Liste os arquivos da ~/.bashrc" (arquivo) -> glob vazio; perguntas de pasta -> read_file no arquivo errado. Decisao do dono (Q4): expandir ~ + ser esperta arquivo/pasta. A expansao de ~ e a 386; esta sprint e a esperteza arquivo vs pasta.
**Modelo obrigatorio:** modelo principal local (sem subagentes; implementação direta)

---

## Problema

O 3b confunde arquivo e pasta (capacidade limitada, ADR-034): pede glob/list de um arquivo, ou read de uma pasta. Hoje isso vira "Nenhum arquivo encontrado" / erro cru -- sem pista pro modelo se corrigir. A infra pode AJUDAR: detectar is_file vs is_dir e devolver uma mensagem clara (ou fazer o obvio), reduzindo o efeito da escolha errada de tool. (Mitigacao; o teto continua sendo a troca de model -- ONDA do gerenciador.)

---

## Solucao proposta

Apos `validate_path`, em cada tool:
- glob/list_files: se o alvo e arquivo -> mensagem clara ("`X` e um arquivo, nao uma pasta; use read_file para ler o conteudo") (ou retornar o arquivo como unico item -- escolher o mais util sem fingir).
- read_file: se o alvo e pasta -> mensagem clara ("`X` e uma pasta; use list_files para ver o conteudo").
Mensagens claras e honestas (o 3b le e se recupera). Casos normais inalterados.

---

## Proof-of-work esperado

```bash
# probes deterministicos (arquivo em glob/list; pasta em read; casos normais)
./run.sh --gauntlet --only fs_arbitrary
./run.sh --gauntlet --only rapido
bash scripts/sprint_invariants.sh
python3 ~/.config/zsh/scripts/validar-acentuacao.py --paths nyx/agent/tools/glob_tool.py nyx/agent/tools/list_files.py nyx/agent/tools/read_file.py
/home/andrefarias/.local/bin/ruff check nyx/agent/tools/glob_tool.py nyx/agent/tools/list_files.py nyx/agent/tools/read_file.py
```

---

## Criterio binario de aceite

- [ ] glob/list num arquivo -> util (mensagem clara ou le)
- [ ] read numa pasta -> mensagem clara (use list_files)
- [ ] casos normais intactos; fs_arbitrary + rapido verdes; invariantes 14/14; spec -> concluidos/

---

## Riscos

| Risco | Mitigacao |
|-------|-----------|
| Auto-comportamento surpreendente | preferir mensagem clara a auto-troca silenciosa; nunca fingir sucesso (ADR-026/033) |
| Regressao no caso normal | probe de pasta-normal/arquivo-normal antes de fechar |

---

*"Em vez de um beco sem saida, uma placa apontando a rua certa." -- anonimo*
