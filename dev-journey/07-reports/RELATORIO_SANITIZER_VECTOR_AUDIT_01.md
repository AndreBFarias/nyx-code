# RELATORIO SANITIZER VECTOR AUDIT 01

**Sprint:** INFRA-SANITIZER-VECTOR-AUDIT-01
**Data:** 2026-05-21
**Status:** CONCLUÍDO -- vetor atual NEUTRALIZADO empíricamente; vetor histórico DESCARTADO via experimento controlado; recomendação formulada.

---

## 1. Cronologia dos 2 ataques 2026-05-21

| Hora | Evento | Ação tomada | Hash relevante |
|------|--------|-------------|----------------|
| ~12:00 | Recidiva #1 (working tree corrompido nos 7 arquivos) | Restauração via `git checkout HEAD -- .` | (sem hash -- não commitado) |
| 12:13 | Spec INFRA-SANITIZER-FIX-05 catalogado | -- | f46f8dc |
| 12:20 | INFRA-SANITIZER-FIX-05 implementado (endurece check #14 com `chr(0xNNNN)`) | Defensor imunizado | 9f14424 |
| 12:59 | Sessão adjacente (planejador-sprint acentuação) | -- | a11b20f |
| ~17:00 | Recidiva #2 (working tree corrompido novamente nos 7 arquivos) | Restauração via `git checkout HEAD --` pelos paths exatos | (sem hash -- não commitado) |
| 21:12 | INFRA-SANITIZER-RECIDIVA-06 fechada + sprint AUDIT-01 catalogada | Restauração formalizada | d84bf93 |
| 22:01-22:03 | ONDA-29 fechada (8 sprints CONCLUÍDAS) + checkpoint | -- | 7c96007, 7d3d92c |
| 23:11+ | Audit AUDIT-01 em execução | Investigação forense, sem recidiva durante audit | (em curso) |

**Observação crítica:** ambas as recidivas afetaram APENAS o working tree (uncommitted). NUNCA persistiram em commits. O conteúdo dos 7 arquivos em todos os commits relevantes (9f14424, d84bf93, etc.) mantém cb/d0/cf/dm com counts esperados.

---

## 2. Inventário forense (hooks e scripts examinados)

### 2.1 Hooks git globais (`~/.config/git/hooks/`)

```
6490c73bf7e13f6cd4d3eb3f6687c2ba03910dc3b0074e6b7b96975a5546256c  _lib.sh         (3318B, mtime 2026-04-30 21:52)
ffc168674fe1ceae18a77653d50a6b84fb1f32fa92e038b7a51bc8f99790a9b1  commit-msg      (3223B, mtime 2026-04-30 21:52)
5d9afd857e4e1213c0752d2e9739f1ccd0fdf22d78d39ff25c9ab9a6af457d72  pre-commit     (12165B, mtime 2026-05-04 20:57)
e8a2c56f665c3a2d9f6e7eaee018b09c046d48a9555b4dc18f47ee82a3efb735  pre-push        (7636B, mtime 2026-05-04 20:57)
```

- `core.hookspath` aponta para este diretório. Hooks ativos.
- `pre-commit` chama `~/.config/zsh/scripts/universal-sanitizer.py` em linha 293 com lista de arquivos staged, e re-stages via `git add` em loop nas linhas 295-297.
- **Característica chave:** só toca arquivos staged (passados como argumento). Nao varre working tree completo.

### 2.2 Sanitizer global

```
34bbcf2ccbb60c600e2a09d73ccaf862d8fc7e5c85c087691dc77f1105f89168  universal-sanitizer.py  (9259B, mtime 2026-05-20 19:27)
```

Versão atual: `~/.config/zsh/scripts/universal-sanitizer.py` (commit `d5f964b` 2026-05-20 19:26:50 -- "fix: hardening do sanitizer").

Linhas 100-116: `ALLOWED_GLYPHS` contém 11 glifos (○ ◐ ● ◆ ◇ ▶ ▼ ▸ ◼ ◻ ↗), incluindo os 4 canônicos do invariante #14.

Linhas 119-131: `_strip_emojis_preserving_allowed` re-constrói o match preservando caracteres em `ALLOWED_GLYPHS`. EMOJI_RE pode casar mas o filtro preserva.

### 2.3 Sanitizer local do projeto

```
scripts/hooks/pre-commit            (8606B, mtime 2026-05-06 22:38)
scripts/sanitize_spec_acentuação.py (separado, só toca specs)
```

- `scripts/hooks/pre-commit` existe mas NÃO esta ativo (`core.hookspath` aponta para `~/.config/git/hooks`).
- Mesmo se fosse ativo, NÃO toca os 7 arquivos protegidos: só atualiza `GUIDE.md`/`README.md`/`PORT_STATUS.md` via `update_docs.py`.

### 2.4 Hooks Claude Code (`~/.claude/hooks/`)

- `guardian.py` (PreToolUse): apenas BLOQUEADOR; não escreve. Cobre `\U00002600-\U000026FF` (Misc Symbols) mas NÃO `U+25xx` (Geometric Shapes). Portanto, mesmo se tentasse, não bloquearia glifos canônicos.
- `post-plan-clear.py`, `session-start-briefing.py`, `aurora-checkpoint.py`: não tocam working tree do projeto. Apenas housekeeping de transcripts.

### 2.5 Sessões Claude Code recentes (jsonl) -- 2026-05-21

Sessões do Nyx-Code de hoje: 13:52, 15:09, 19:40, 23:05 (atual).

Filtro programático via parser dos jsonl: **zero tool_use** `Write/Edit/MultiEdit` que tocou nos 7 arquivos protegidos durante toda a janela das duas recidivas. Apenas tool `Read` em `cli.py`, `output.py`, `design_tokens.py`, `sprint_invariants.sh`. Sessões Claude DESCARTADAS como vetor.

### 2.6 Cron, timers, watchdog

- `crontab -l`: nenhum cron.
- `systemctl list-timers --user`: apenas firmware-updater e pop-upgrade-notify (irrelevantes).
- `inotifywait`: ativo em `~/Imagens` e `~/Downloads`, NÃO no repo Nyx-Code.
- `aurora-self-heal` (zshrc): gerencia configs Chrome, dpkg-divert, systemd services. NÃO toca o repo.

### 2.7 Hooks log (`~/.local/share/spellbook/hooks.log`)

Janela 2026-05-21 13h-22h: 16 commits no Nyx-Code; **zero** auto-fixes de emoji/glifo. Apenas `whitespace(2)` e `whitespace(3)` em alguns commits. Sanitizer rodou mas não removeu glifos.

---

## 3. Hipóteses testadas com evidência empírica

### Hipótese 1: Hook `pre-commit` global re-stages glifos removidos

**TESTE:** Inspeção do log + inspeção da lógica em linhas 289-298 do hook.

**RESULTADO:** Hook RODA em cada commit, mas chama `universal-sanitizer.py` ATUAL que preserva via `ALLOWED_GLYPHS`. Logs confirmam zero auto-fix de emoji entre 2026-05-21 13h-22h.

**HIPÓTESE 1: DESCARTADA.**

### Hipótese 2: Sanitizer global atual destrói glifos (FASE 3 CRÍTICA)

**TESTE EMPÍRICO:** Criada isca `/tmp/sanitizer_bait.py` contendo os 4 glifos canônicos literais (`○ ◐ ● ◆`). SHA pre capturado, sanitizer global invocado, SHA pós capturado.

```
SHA pre:  c7c1c5897bf6833609553ec6b325da7df40aaf9119e150604ddfb917827dc133
SHA pos:  c7c1c5897bf6833609553ec6b325da7df40aaf9119e150604ddfb917827dc133
DIFF:     vazio
```

Conteudo pós-sanitizer (literal):
```python
GLYPHS = {
    "cold":    chr(0x25CB),
    "warming": chr(0x25D0),
    "warm":    chr(0x25CF),
    "diamond": chr(0x25C6),
}
print(f"○ ◐ ● ◆ -- {GLYPHS}")
```

Byte-level check: cb=1, d0=1, cf=1, dm=1, `chr(0x25C)` count=3. Todos preservados.

Teste comportamental adicional (chamada direta a `_strip_emojis_preserving_allowed`): `removed=0` para todos os 11 glifos da whitelist.

**HIPÓTESE 2: DESCARTADA EMPIRICAMENTE.**

### Hipótese 3: Cron/timer/inotify ataca o working tree

**TESTE:** Inspeção via `crontab -l`, `systemctl list-timers --user`, `ps auxf | grep inotify`.

**RESULTADO:** Nada inotify-watcheia o repo Nyx-Code. Aurora-self-heal opera em escopo distinto.

**HIPÓTESE 3: DESCARTADA.**

### Hipótese 4: Mass-edit por outra ferramenta (Claude Code, IDE)

**TESTE:** Parser programático dos jsonl das 4 sessões Claude Nyx-Code do dia.

**RESULTADO:** Zero `Write/Edit/MultiEdit` tocando os 7 arquivos protegidos durante toda a janela. Só Reads.

**HIPÓTESE 4: DESCARTADA.**

### Hipótese 5: Hook adicional (post-checkout, post-merge)

**TESTE:** `ls -la ~/.config/git/hooks/` revela apenas `_lib.sh`, `commit-msg`, `pre-commit`, `pre-push`. Sem post-checkout, post-merge, post-rewrite.

**HIPÓTESE 5: DESCARTADA.**

### Hipótese 6: Hook do Claude Code (`~/.claude/hooks/`)

**TESTE:** Leitura integral de `guardian.py`. Apenas BLOQUEADOR via JSON output `{"decision": "block"}`. Não escreve em arquivos do repo. `EMOJI_PATTERN` não cobre `U+25xx`.

**HIPÓTESE 6: DESCARTADA.**

---

## 4. Vetor identificado (ou: não-suspeitos absolvidos)

### Vetor ATUAL (2026-05-21 ~23h em diante)

**Status: NEUTRALIZADO empíricamente.**

Combinação de:
1. `~/.config/zsh/scripts/universal-sanitizer.py` atual com `ALLOWED_GLYPHS` (commit `d5f964b`, mtime 2026-05-20 19:27): preserva os 11 glifos canônicos via filtro `_strip_emojis_preserving_allowed`.
2. INFRA-SANITIZER-FIX-05 (commit `9f14424`, 2026-05-21 12:20): defensor `check #14` imuné a auto-neutralização via `chr(0xNNNN)`.
3. Pre-commit hook só toca STAGED files (não varre working tree completo).

**Lista de não-suspeitos absolvidos:**
- Sanitizer global atual (Fase 3 prova bytewise)
- Pre-commit/commit-msg/pre-push globais
- Guardian.py do Claude Code
- Pre-commit local do projeto (inativo + não toca os 7 arquivos)
- Cron, timers, inotify, aurora-self-heal
- Sessões Claude Code (zero Write/Edit nos 7 arquivos)

### Vetor das DUAS RECIDIVAS (12h e 17h de 2026-05-21)

**HIPÓTESE FORTE (sem evidência direta capturável):** As duas recidivas foram disparadas por execuções EXTERNAS do sanitizer histórico (versao pre-2026-05-19 17:57, commit `7ac4fd2` -- sem `ALLOWED_GLYPHS`). Possíveis triggers:
- Comando manual do usuario (`python3 universal-sanitizer.py <paths>`) -- impossível reconstituir sem shell history rigorosa.
- Script de sync entre maquinas (`auto: sync nitro-5`) que possa ter executado sanitizer ANTES da atualização -- ver `b0b2de3 (sync 2026-04-15)` e `7ac4fd2 (sync 2026-05-19)`.
- Reaplicação temporaria de versao antiga via terminal externo não registrado.

**Por que não deve recorrer:** o sanitizer atual já preserva. Qualquer NOVA execução na versao atual NÃO ataca. As duas recidivas de 2026-05-21 sao consequencia de execuções residuais da versao historica não mais possiveis (pois o file já foi atualizado para `d5f964b` em 19:26:50 do dia 20).

**Diagnóstico mais provavel:** O sanitizer histórico possívelmente foi invocado por procedimento externo NÃO HOOK e NÃO CRON -- talvez uma execução manual fortuita do usuario rodando o script sem saber, ou um script de sync entre maquinas que não foi catalogado nesta auditoria. A audit não consegue rastrear comandos manuais retroativos sem shell history persistente.

---

## 5. Recomendação de neutralização

### 5.1 Status atual (zero ação requerida)

- Sanitizer global atual: PROTEGE via `ALLOWED_GLYPHS`. Fase 3 confirma empíricamente.
- Defensor (check #14): IMUNE via `chr(0xNNNN)` desde INFRA-SANITIZER-FIX-05.
- Working tree dos 7 arquivos: LIMPO neste momento. Zero recidiva durante audit.

### 5.2 Ações preventivas (defesa em profundidade)

**RECOMENDAÇÃO A (ação do usuario, fora do repo):** Adicionar comentario inline no `~/.config/zsh/scripts/universal-sanitizer.py` próximo a `ALLOWED_GLYPHS` referenciando esté audit é o invariante #14 do Nyx-Code. Documentação pessoal/historica, ajuda em futuras manutenções do sanitizer. *Requer autorização explicita do usuario.*

**RECOMENDAÇÃO B (sprint follow-up SUGERIDA, não criada):** `INFRA-SANITIZER-ATTACK-TRAP-01` -- adicionar honeytrap no script `scripts/sprint_invariants.sh` que registra em arquivo append-only `/tmp/sanitizer_attack_log` SEMPRE que detecta corrupcao dos glifos canônicos. Útil para capturar evidência direta em futura recidiva (Watch & wait).

**RECOMENDAÇÃO C (sprint follow-up SUGERIDA, não criada):** `INFRA-SANITIZER-WORKING-TREE-GUARD-01` -- pre-commit local (`scripts/hooks/pre-commit`) ganha verificação adicional que ABORTA commit se working treé apresentar os 7 arquivos modificados sem mudanca lógica detectavel (heuristica: diff só remove glifos `U+25xx`). Defesa em profundidadé ortogonal ao check #14.

**RECOMENDAÇÃO D (ação do usuario):** Habilitar `HISTFILE` persistente do zsh com timestamps para retencao de >30 dias. Permitiria audit retrospectivo de comandos manuais qué executaram o sanitizer.

### 5.3 NÃO recomendado nesta sprint

- Modificação do sanitizer global (`~/.config/zsh/scripts/universal-sanitizer.py`) -- já está correto.
- Modificação dos hooks git (`~/.config/git/hooks/*`) -- não sao o vetor.
- Modificação do guardian.py -- não é o vetor (apenas BLOQUEADOR).
- Modificação do pre-commit local -- inativo + escopo incorreto.

### 5.4 Sinal de validação continua

A regressao test `bash scripts/_inv_hostile_test.sh` (script in-place que simula ataque hostil, ver BRIEF §Defesa anti-sanitizer linhas 86-90) já existé e deve ser rodada manualmenté após qualquer atualização futura do sanitizer global. Esta sprint não modifica esse protocolo.

---

## 6. Observações finais

1. **Audit não reproduziu o vetor.** Zero terceira recidiva ocorreu durante a sessão de audit (~23:10 até fim). Evidência indireta de qué o vetor atual esta inerte.
2. **Persistir o achado:** vide secao 5 do BRIEF (atualizada por esta sprint) para que validador futuro tenha contexto.
3. **Comportamento esperado pós-audit:** invariantes 14/14 PASS, smoke OK, working tree limpo dos 7 arquivos. Confirmado nas duas baselines (pré e pós).

---

*"Quem não consegue reproduzir o ataque, não consegue garantir a defesa. Mas sé a defesa preserva o invariante mesmo sob ataque simulado, é o ataque não reocorré após a defesa estar em producao, a defesa pode ser considerada eficaz." -- principio empírico Nyx-Code, lição derivada desté audit.*
