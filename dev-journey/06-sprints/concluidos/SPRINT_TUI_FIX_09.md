# SPRINT TUI-FIX-09 — `/theme` imprime lista de dicts Python crua (viola ADR-024)

## 0. SPEC (machine-readable)

```yaml
sprint:
  id: TUI-FIX-09
  title: "Formatar saída do /theme (e auditar outros commands que retornam list/dict) via render layer"
  onda: 22
  bloco: 2.8
  prioridade: MÉDIA
  tipo: Bugfix
  dependencias: [BUG-PORT-PARSE-01]
  desbloqueia: [VALIDATE-ONDA-20]

  touches:
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/agent/commands/system.py
      reason: "cmd_theme itera list[dict[str, str]] de ThemeManager.list_themes() e faz f'    - {t}' — imprime dict cru"
      linhas_alvo: "136-154"
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/themes/__init__.py
      reason: "list_themes retorna list[dict] — decidir se contrato vira list[ThemeInfo NamedTuple] OU cmd_theme formata o dict. Atual contrato é ok se cmd_theme extrair campos"
      linhas_alvo: "88 (assinatura da função)"

  creates: []
  removes: []

  n_to_n_pairs:
    - descricao: "Auditoria adicional (read-only, sem alteração): commands que retornam list/dict e podem ter o mesmo defeito — /tools, /permissions, /status, /session. Se algum violar, listar como achado colateral, NÃO fixar inline."
      paths:
        - /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/agent/commands/system.py
        - /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/agent/commands/

  forbidden:
    - "Fixar outros commands além de /theme — cada um vira sprint própria (escopo atômico)"
    - "Usar print() dentro de cmd_theme — command retorna str, cli.py chama output.render(...)"
    - "Emitir output via logger — viola ADR-024"
    - "Alterar contrato de ThemeManager.list_themes() para retornar lista de strings — perderia descrição"
    - "Ignorar auditoria read-only dos outros commands — achados viram SPRINT_TUI_FIX_NN.md no protocolo anti-débito"
    - "Adicionar emoji, menção a IA, ou tocar em arquivos fora dos 2 touches"

  tests:
    - cmd: "./run.sh --gauntlet --only rapido"
      timeout: 120
    - cmd: "manual: `/theme` no REPL; saída deve mostrar `id` `name` `description` formatados em linhas, sem chaves `{}` nem aspas Python"
      timeout: 30
    - cmd: "manual: `/theme eris` (carregar tema) e confirmar que mensagem de sucesso é PT-BR limpa"
      timeout: 30

  acceptance_criteria:
    - "`/theme` exibe lista formatada tipo `  - eris: Caos púrpura (Eris)` ou similar — zero `{'id': ...}`"
    - "`/theme list` (alias) idem"
    - "`/theme <id>` retorna mensagem de carregamento sem dict cru"
    - "Auditoria read-only dos outros commands list/dict documentada no relatório: OU todos ok, OU achados materializados como sprints novas"
    - "Gauntlet rapido 100%"
    - "Acentuação PT-BR correta"
```

---

**Status:** CONCLUIDA (2026-04-20) -- cmd_theme extrai id/name/description; achado colateral (load_theme fallback silencioso) materializado como SPRINT_TUI_FIX_10 antes do commit.
**Data criação:** 2026-04-19
**Origem:** achado colateral durante **VALIDATE-ONDA-20** (Rodada 1). Usuário rodou `/theme` e recebeu:
```
  Temas disponíveis:
    - {'id': 'eris', 'name': 'Eris', 'description': 'Caos púrpura...'}
    - {'id': 'juno', 'name': 'Juno', 'description': 'Verde orgânico...'}
```
**Modelo obrigatório:** claude-opus-4-7 (sem subagentes)

---

## Contexto do projeto (snapshot)

> **Especificação original violada:** `SPRINT_TUI_01_HIGIENE.md` (ainda em `producao/`, EM VALIDAÇÃO).
>
> Citação literal da spec TUI-01:
> - "Tool calls formatadas como 'read_file(path)' sem dict cru"
> - "Zero INFO/DEBUG/WARNING no stdout durante REPL"
>
> Gap: o princípio "sem dict cru" foi implementado para tool calls mas não para output de commands. `/theme` viola a higiene.
>
> **ADR-024 (Render Layer):** `print()` permitido apenas em `nyx/cli.py` e `nyx/agent/output.py`. Commands retornam `str` e o REPL (`nyx/cli.py:350`) delega para `render`. Se `str` já contém `{'id': ...}` literal, a render layer não salva — o dict foi materializado em string antes.
>
> **Estado do código:**
> - `nyx/agent/commands/system.py:136-154` — `cmd_theme`.
>   ```python
>   @nyx_command(name="theme", description="Lista ou troca tema de cores", category="sistema")
>   def cmd_theme(args: str, _root: str) -> str:
>       try:
>           from nyx.themes import ThemeManager
>           tm = ThemeManager()
>           args = args.strip()
>           if not args or args == "list":
>               temas = tm.list_themes()
>               lines = ["  Temas disponíveis:"]
>               for t in temas:
>                   lines.append(f"    - {t}")     # <-- BUG: t é dict, f-string chama repr()
>               return "\n".join(lines)
>           theme = tm.load_theme(args)
>           ...
>   ```
> - `nyx/themes/__init__.py:88` — `def list_themes(self) -> list[dict[str, str]]:` (retorna lista de dicts com `id`, `name`, `description`).
>
> **Bug dependente:** BUG-PORT-PARSE-01 precisa estar concluído antes — usuário não consegue testar `/theme` enquanto o REPL vomita `Invalid port` a cada tecla.

---

## Problema

### Sintoma observável

```
nyx> /theme
  Temas disponíveis:
    - {'id': 'eris', 'name': 'Eris', 'description': 'Caos púrpura...'}
    - {'id': 'juno', 'name': 'Juno', 'description': 'Verde orgânico...'}
```

### Causa

`cmd_theme` chama `tm.list_themes()` que retorna `list[dict[str, str]]`. A f-string `f"    - {t}"` invoca `__str__` do `dict` → `{'id': '...', ...}`. Código não extrai os campos.

### Escopo adicional (read-only, obrigatório)

Antes do fix, auditar outros commands que consomem list/dict sem formatação:
```bash
grep -rn 'for.*in.*:$\|return.*\[\|return.*dict' nyx/agent/commands/ --include='*.py'
```

Se achar violação análoga em outro command, **não fixar inline** — materializar sprint nova (TUI-FIX-10, -11, ...) seguindo protocolo anti-débito de BOOT-FIX-01. Reportar no relatório final.

---

## Solução proposta

Reescrever o loop em `cmd_theme` para extrair campos:

```python
for t in temas:
    tid = t.get("id", "?")
    tname = t.get("name", tid)
    tdesc = t.get("description", "").strip()
    if tdesc:
        lines.append(f"    - {tid}: {tname} — {tdesc}")
    else:
        lines.append(f"    - {tid}: {tname}")
```

Não mudar `ThemeManager.list_themes()` — contrato `list[dict]` é legítimo para API interna; a responsabilidade de formatar é de quem exibe (`cmd_theme`).

---

## Diff esperado

```
~ 1 arquivo modificado (cmd_theme em system.py)
~ 0-1 arquivo modificado (themes/__init__.py apenas se adicionar docstring clarificando)
+ ~10 linhas líquidas
```

---

## Comandos de verificação

```bash
# 1. Invariantes ANTES
bash scripts/sprint_invariants.sh > /tmp/inv_before.txt 2>&1

# 2. Auditoria read-only (achados colaterais)
grep -rn 'for.*in.*:$\|return.*\[' nyx/agent/commands/ --include='*.py' | head -30

# 3. Aplicar fix em cmd_theme

# 4. Boot smoke
./run.sh --smoke   # 'boot ok'

# 5. Manual (REPL)
./run.sh
# /theme           → lista formatada, zero chaves
# /theme eris      → mensagem de carregamento limpa
# /theme xxx       → mensagem de não encontrado

# 6. Gauntlet
./run.sh --gauntlet --only rapido

# 7. Invariantes DEPOIS
bash scripts/sprint_invariants.sh > /tmp/inv_after.txt 2>&1
diff /tmp/inv_before.txt /tmp/inv_after.txt
```

---

## Critério binário de aceite

- [ ] `/theme` não exibe `{'id': ...}` no stdout
- [ ] `/theme <id>` carrega e mostra mensagem PT-BR limpa
- [ ] Auditoria read-only documentada no relatório (com achados ou declaração explícita de "nenhum achado adicional")
- [ ] Gauntlet rapido 100%
- [ ] FAIL invariantes não regride; check #13 continua PASS
- [ ] Sprint movida para `concluidos/` com commit `fix: /theme formata campos em vez de imprimir dict cru (TUI-FIX-09)`
- [ ] SPRINT_ORDER_MASTER atualizado

---

## Gambiarras específicas

1. **`ast.literal_eval` no output** — proibido, resolve sintoma, não causa.
2. **Mudar contrato de `list_themes()` para `list[str]`** — perde descrição, quebra callers futuros. Fora de escopo.
3. **Formatar com `pprint` ou `rich.pretty`** — over-engineering para 1 ponto; f-string com campos explícitos basta.
4. **Ignorar auditoria read-only dos outros commands** — viola protocolo anti-débito. `/tools`, `/permissions`, `/session` podem ter padrão similar.

---

## Proof-of-work obrigatório

Formato padrão (SPRINT_TEMPLATE_V2.md). Incluir:

- Transcript literal do REPL antes (com dict) e depois (formatado).
- Saída da auditoria read-only (`grep -rn 'for .* in .*:$'`) + declaração: "X achados materializados como SPRINT_TUI_FIX_YY.md" OU "nenhum achado adicional".
- Checklist de BOOT-FIX-01 (achados colaterais materializados **antes** do commit docs de conclusão).

---

## Validação humana (checklist do usuário)

```bash
./run.sh
# /theme
# saída esperada: linhas formatadas estilo '  - eris: Eris — Caos púrpura...', sem { }
# /theme eris
# saída esperada: 'Tema eris carregado. Primary: #XXXXXX'
# Ctrl+D
```

---

## Riscos

| Risco | Mitigação |
|-------|-----------|
| Outros commands podem ter bug análogo (/tools, /permissions) | Auditoria read-only obrigatória; achados viram sprints novas via protocolo anti-débito |
| Descrição de tema pode conter caracteres que quebram f-string | Usar `.get(key, default)` com fallback, não indexação direta |
| Mudança em `list_themes()` quebra calls externos | Não alterar contrato — apenas o consumidor em `cmd_theme` |

---

*"A higiene é a primeira virtude de quem constrói." -- Ruskin*
