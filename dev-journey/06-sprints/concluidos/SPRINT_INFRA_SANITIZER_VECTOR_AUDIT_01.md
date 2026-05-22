## 0. SPEC (machine-readable)

```yaml
sprint:
  id: INFRA-SANITIZER-VECTOR-AUDIT-01
  title: "Rastrear e neutralizar o vetor que ataca os 7 arquivos protegidos pelo invariante #14"
  onda: 29
  prioridade: CRÍTICA
  tipo: Audit
  dependencias: [INFRA-SANITIZER-RECIDIVA-06, INFRA-SANITIZER-FIX-05]
  desbloqueia: []

  touches:
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/dev-journey/07-reports/RELATORIO_SANITIZER_VECTOR_AUDIT_01.md
      reason: "Relatório de auditoria — paths examinados, vetor identificado, evidência forense"
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/VALIDATOR_BRIEF.md
      reason: "Atualizar seção §[CORE] Defesa anti-sanitizer com a causa raiz identificada (se confirmada)"

  creates:
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/dev-journey/07-reports/RELATORIO_SANITIZER_VECTOR_AUDIT_01.md
      reason: "Documento canônico da investigação"

  out_of_scope_paths:
    - path: ~/.config/git/hooks/pre-commit
      reason: "Hook global do usuário — só inspecionar (read-only), não modificar sem confirmação explícita. Reportar findings."
    - path: ~/.config/zsh/scripts/universal-sanitizer.py
      reason: "Sanitizer global do usuário — só inspecionar (read-only), não modificar. Reportar findings."
    - path: ~/.claude/**
      reason: "Diretório de configuração do Claude Code — fora do repo, não tocar."

  forbidden:
    - "Modificar arquivos em ~/.config/ ou ~/.claude/ sem autorização explícita do usuário"
    - "Aplicar fix definitivo sem antes documentar o vetor no relatório"
    - "Adicionar emoji"
    - "Menção a IA externa em código"

  tests:
    - cmd: "bash scripts/sprint_invariants.sh"
      timeout: 30
      deve_passar: true
    - cmd: "./run.sh --smoke"
      timeout: 60
      deve_passar: true

  acceptance_criteria:
    - "Relatório `RELATORIO_SANITIZER_VECTOR_AUDIT_01.md` criado com seções: (1) Cronologia dos 2 ataques 2026-05-21, (2) Hooks/scripts examinados (com paths, mtimes, sha256), (3) Hipóteses testadas com evidência empírica, (4) Vetor identificado (ou: descartado com lista de não-suspeitos), (5) Recomendação de neutralização"
    - "Se vetor identificado dentro do repo: patch aplicado + invariante regression test rodado 3x"
    - "Se vetor identificado FORA do repo: recomendação documentada + sprint follow-up sugerida (não criada)"
    - "BRIEF §[CORE] Defesa anti-sanitizer atualizado com findings"
    - "Smoke + invariantes 14/14 PASS antes e depois"
```

---

# Sprint INFRA-SANITIZER-VECTOR-AUDIT-01 — Auditoria do vetor de ataque

**Status:** PENDENTE
**Data criação:** 2026-05-21
**Modelo obrigatório:** claude-opus-4-7 (sem subagentes)

---

## Contexto do projeto (snapshot)

> - VALIDATOR_BRIEF.md §[CORE] Defesa anti-sanitizer documenta o vetor histórico de 2026-05-20 que corrompeu 57 arquivos via remoção em massa de glifos Geometric Shapes.
> - INFRA-SANITIZER-FIX-05 (2026-05-21 ~09h) imunizou o defensor (check #14 via `chr(0xNNNN)` em vez de literais).
> - INFRA-SANITIZER-RECIDIVA-06 (2026-05-21 ~17h, commit d84bf93) restaurou 7 arquivos protegidos via `git checkout HEAD --` após ataque #2.
> - **Estado pós-recidiva:** o defensor está imune (check #14 sempre detecta corrupção), mas o vetor de ataque continua ativo. 2 eventos no mesmo dia (2026-05-21 ~12h e ~17h, ambos confirmados por `git status -s` mostrando os 7 paths protegidos como M sem trabalho lógico).

---

## Problema

Apesar de INFRA-SANITIZER-FIX-05 ter endurecido o check #14 (defensor imune a auto-neutralização), os ARQUIVOS protegidos pelo invariante #14 continuam sendo atacados periodicamente. 2 recidivas em 2026-05-21 confirmadas.

**Hipóteses iniciais (ordem decrescente de probabilidade):**

1. **Hook `~/.config/git/hooks/pre-commit`** (mtime 2026-05-04 20:57, 12165 bytes) invoca o sanitizer global e re-stages o arquivo. Mas só dispararia em `git commit` — não explica recidivas durante sessão idle.

2. **Sanitizer global `~/.config/zsh/scripts/universal-sanitizer.py`** (mtime 2026-05-20 19:27, 9259 bytes) — preserva via `ALLOWED_GLYPHS` desde commit `7ac4fd2`. Se versão atual estiver correta, não é o vetor; verificar.

3. **Cron / watchdog / inotify** que dispara o sanitizer em modificação de arquivo.

4. **Mass-edit operation** disparada por outra ferramenta (Claude Code, IDE, editor remoto).

5. **Sanitizer rodando dentro de outro hook git** não-óbvio (post-checkout, post-merge, etc.).

6. **Sanitizer rodando dentro de skill/agent/hook do Claude Code** (`~/.claude/hooks/`).

---

## Solução proposta

Auditoria forense em 5 fases:

### Fase 1: Snapshot do estado atual (READ-ONLY)

```bash
# Hooks git globais
ls -la ~/.config/git/hooks/
sha256sum ~/.config/git/hooks/* | tee /tmp/audit_hooks_sha.txt

# Sanitizer global
sha256sum ~/.config/zsh/scripts/universal-sanitizer.py
stat ~/.config/zsh/scripts/universal-sanitizer.py

# Verificar ALLOWED_GLYPHS presente no source atual
grep -c "ALLOWED_GLYPHS" ~/.config/zsh/scripts/universal-sanitizer.py

# Hooks git locais (.git/hooks/)
ls -la .git/hooks/

# Claude Code hooks
ls -la ~/.claude/hooks/ 2>/dev/null
find ~/.claude -name "*.json" -path "*settings*" 2>/dev/null | head

# Cron entries
crontab -l 2>/dev/null
systemctl list-timers --user 2>/dev/null | head -10

# Watchdog/inotify potencial
ps auxf | grep -E "inotify|watch|fswatch" | grep -v grep
```

### Fase 2: Forense dos ataques

```bash
# Reflog para localizar exatamente o momento dos ataques
git reflog --date=iso | head -40 | tee /tmp/audit_reflog.txt

# Verificar se há working tree corruption agora (recidiva durante audit?)
python3 -c "
from pathlib import Path
for f in ['nyx/cli.py', 'nyx/agent/repl_app.py', 'nyx/agent/banner.py',
         'nyx/agent/output.py', 'nyx/themes/design_tokens.py',
         'nyx/themes/design_tokens_extended.py', 'scripts/sprint_invariants.sh']:
    t = Path(f).read_text()
    cb, d0, cf, dm = chr(0x25CB), chr(0x25D0), chr(0x25CF), chr(0x25C6)
    print(f'{f}: cb={t.count(cb)}, d0={t.count(d0)}, cf={t.count(cf)}, dm={t.count(dm)}')
" | tee /tmp/audit_byte_level.txt

bash scripts/sprint_invariants.sh > /tmp/audit_inv_baseline.txt 2>&1
```

### Fase 3: Teste empírico do sanitizer global (CONTROLADO)

```bash
# Criar arquivo isca contendo todos os 4 glifos canônicos
cat > /tmp/sanitizer_bait.py << 'PYEOF'
GLYPHS = {
    "cold":    chr(0x25CB),
    "warming": chr(0x25D0),
    "warm":    chr(0x25CF),
    "diamond": chr(0x25C6),
}
print(f"○ ◐ ● ◆ -- {GLYPHS}")
PYEOF

sha256sum /tmp/sanitizer_bait.py > /tmp/sanitizer_bait_pre.sha

# Rodar sanitizer global e ver se ele preserva ou destrói os glifos
python3 ~/.config/zsh/scripts/universal-sanitizer.py /tmp/sanitizer_bait.py 2>&1 | tee /tmp/audit_sanitizer_run.txt

sha256sum /tmp/sanitizer_bait.py > /tmp/sanitizer_bait_post.sha
diff /tmp/sanitizer_bait_pre.sha /tmp/sanitizer_bait_post.sha
cat /tmp/sanitizer_bait.py
```

Se o sanitizer global ATUAL preservar os glifos: **descartar hipótese 2**. Vetor está em outro lugar.
Se o sanitizer global ATUAL destruir os glifos: **vetor confirmado**, propor patch com `ALLOWED_GLYPHS`.

### Fase 4: Identificar trigger

Se Fase 3 absolveu o sanitizer global, investigar o que dispara o ataque:

```bash
# Auditar hooks Claude Code
cat ~/.claude/settings.json 2>/dev/null | head -60
find ~/.claude/hooks -type f 2>/dev/null | head
grep -r "sanitiz\|emoji" ~/.claude/ 2>/dev/null | head

# Auditar pre-commit do projeto
cat ~/.config/git/hooks/pre-commit | head -50

# Verificar se hook commit-msg ou pre-push consome glifos
sha256sum ~/.config/git/hooks/{commit-msg,pre-push}
```

### Fase 5: Relatório e recomendação

Consolidar findings em `dev-journey/07-reports/RELATORIO_SANITIZER_VECTOR_AUDIT_01.md` com:

- **Cronologia:** 2 ataques 2026-05-21 (timestamps via reflog/git status histórico).
- **Inventário forense:** sha256 + mtime dos 7-10 suspeitos investigados.
- **Hipótese confirmada/descartada:** com evidência empírica do experimento Fase 3.
- **Vetor identificado** (ou lista de não-suspeitos absolvidos).
- **Recomendação:**
  - Se vetor dentro do repo → patch aplicado nesta sprint.
  - Se vetor em `~/.config/` ou `~/.claude/` → recomendação ao usuário + sprint follow-up sugerida (não criada — autorização explícita necessária).
- Atualizar BRIEF §[CORE] Defesa anti-sanitizer com o achado.

---

## Diff esperado

```
+ 1 arquivo criado (relatório)
~ 1 arquivo modificado (BRIEF)
+ ~150 linhas
```

Possível +1 arquivo se vetor for identificado dentro do repo (patch). Caso contrário, audit-only.

---

## Comandos de verificação

```bash
# 1. Pré-snapshot (Fase 1+2 captura tudo)
bash scripts/sprint_invariants.sh > /tmp/audit_inv_pre.txt

# 2. (Executar Fases 1-5 acima)

# 3. Pós-snapshot
bash scripts/sprint_invariants.sh > /tmp/audit_inv_pos.txt
diff /tmp/audit_inv_pre.txt /tmp/audit_inv_pos.txt   # esperado: vazio

# 4. Relatório existe
test -f dev-journey/07-reports/RELATORIO_SANITIZER_VECTOR_AUDIT_01.md && echo OK

# 5. BRIEF atualizado
grep -i "vector\|vetor\|audit-01" VALIDATOR_BRIEF.md | head

# 6. Smoke
./run.sh --smoke

# 7. Acentuação
python3 ~/.config/zsh/scripts/validar-acentuacao.py --paths \
    dev-journey/07-reports/RELATORIO_SANITIZER_VECTOR_AUDIT_01.md \
    VALIDATOR_BRIEF.md
```

---

## Critério binário de aceite

- [ ] Relatório com as 5 seções obrigatórias criado
- [ ] Fase 3 (experimento sanitizer) executada com sha256 antes/depois capturado
- [ ] Vetor identificado OU lista de não-suspeitos absolvidos (com evidência)
- [ ] Recomendação clara para o usuário (patch dentro do repo OU autorização pra tocar em path global)
- [ ] BRIEF §[CORE] Defesa anti-sanitizer atualizado
- [ ] Smoke + invariantes 14/14 PASS antes e depois
- [ ] Acentuação PT-BR rc=0

---

## Riscos

| Risco | Mitigação |
|-------|-----------|
| Vetor ataca durante audit (terceira recidiva) | Audit começa com baseline invariantes; se mudar durante execução, captura é evidência direta do vetor |
| Sanitizer global atacar /tmp/sanitizer_bait.py via inotify | Se acontecer, é evidência forte e vai aparecer no diff sha256 da Fase 3 |
| Usuário pediu spec mas vetor está fora do repo | Aceitar: audit-only é um resultado válido; sprint follow-up para fix global requer autorização explícita |
| Relatório vazar dados sensíveis (paths absolutos, configs do user) | Apenas paths de hooks/scripts conhecidos; sem credenciais, sem env vars |

---

## Achados colaterais (anti-débito)

Esta sprint é resposta direta a achado colateral catalogado em INFRA-SANITIZER-RECIDIVA-06 (entry 191). Se identificar novos vetores ou padrões durante audit, dispatchar planejador-sprint para sprint-N+1 (não absorver implicitamente).

---

*"Rastrear é a forma mais rigorosa de tirar dúvida." -- princípio anti-débito Nyx-Code.*
