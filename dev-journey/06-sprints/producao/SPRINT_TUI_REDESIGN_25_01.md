# SPRINT TUI-REDESIGN-25-01 — Capitalização + acentuação em strings user-facing

## 0. SPEC (machine-readable)

```yaml
sprint:
  id: TUI-REDESIGN-25-01
  title: "Capitalização sentence-case + acentuação PT-BR completa em strings user-facing"
  onda: 25
  bloco: 25.1 Fundamentos visuais
  prioridade: ALTA
  tipo: UX
  dependencias: []
  desbloqueia: [TUI-REDESIGN-25-02, restante da Onda 25]
  origem: "Auditoria visual novo_layout/v2_referencias/audit.jsx -- problemas P01 e P09"

  touches:
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/agent/onboarding.py
      reason: "STEPS tuple linhas 21-42: 'Bem-vinda' -> 'Bem-vindo'; corrige acentos"
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/scripts/menu_wizard.py
      reason: "Prompts do wizard: 'configure antes de bootar' -> 'Configure antes de inicializar.'; 'configuracao' -> 'configuração'; 'permissoes' -> 'permissões'; 'padrao' -> 'padrão'; 'automacao' -> 'automação'"
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/dev-journey/05-guides/MICROCOPY.md
      reason: "Documentar regras de capitalização (sentence-case + substantivos próprios preservados)"
  creates: []
  removes: []

  forbidden:
    - "Tocar nos glifos canônicos do invariante #14 (cli.py, design_tokens.py, output.py)"
    - "Adicionar acentos em comentários técnicos de código (só strings user-facing)"
    - "Quebrar invariante #2 (zero menção a IA externa)"

  tests:
    - cmd: "./venv/bin/python scripts/menu_wizard.py < /dev/null 2>&1 | grep -E 'configuração|permissões|padrão' | head -3"
      timeout: 5
      deve_passar: "todas linhas com acento correto"
    - cmd: "bash scripts/sprint_invariants.sh"
      timeout: 60
      deve_passar: "PASS 14, FAIL 0"

  acceptance_criteria:
    - "Wizard --menu mostra 'Configure antes de inicializar' (sentence-case)"
    - "Strings com 'configuração', 'permissões', 'padrão', 'automação' acentuadas"
    - "STEPS de onboarding em sentence-case ('Bem-vindo', não 'BEM-VINDA')"
    - "Substantivos próprios preservados (Enter, Ollama, Nyx, Ctrl+D)"
    - "MICROCOPY.md ganha seção 'Regras de capitalização e acentuação'"
    - "Validador externo de acentuação aprovado (~/.config/zsh/scripts/validar-acentuacao.py se disponível)"
    - "Smoke ok + invariantes 14/14"
```

---

# Sprint TUI-REDESIGN-25-01

**Status:** PENDENTE
**Data criação:** 2026-05-18 (Onda 25)
**Modelo obrigatório:** claude-opus-4-7

---

## Contexto

Auditoria visual de `novo_layout/v2_referencias/audit.jsx` (P01 + P09) flagrou duas dívidas em strings user-facing:

- **P01:** capitalização inconsistente ("configure antes de bootar" mistura imperativo informal com terminologia técnica; deveria ser sentence-case com ponto final).
- **P09:** acentuação parcial ("configuracao", "permissoes", "padrao", "automacao", "instalacao") quando o locale `pt_BR.UTF-8` está ativo e suporta acento.

Esta sprint é o gate de qualidade textual antes da Onda 25 redesenhar layout. Strings ruins minam o trabalho visual posterior.

## Solução proposta

1. Grep por padrões não-acentuados em `scripts/menu_wizard.py` e `nyx/agent/onboarding.py`. Substituir cirurgicamente:
   - `configuracao` → `configuração`
   - `permissoes` → `permissões`
   - `padrao` → `padrão`
   - `automacao` → `automação`
   - `bootar` / `inicializar` (verificar contexto antes)
   - `Bem-vinda` → `Bem-vindo` (genérico) ou ler git config user.name (deixar para 25-04)
2. Sentence-case em prompts: "Configure antes de inicializar." (capital inicial + ponto final).
3. MICROCOPY.md ganha seção com regras canônicas:
   - Sentenças sempre em sentence-case
   - Substantivos próprios preservados (Enter, Ollama, Nyx, Ctrl+D, REPL)
   - Acentos PT-BR obrigatórios em palavras de domínio comum
4. Smoke + invariantes 14/14.

## Critério binário de aceite

- [ ] grep `configuracao\|permissoes\|padrao\|automacao` em scripts/menu_wizard.py retorna 0 hits
- [ ] Mesmo grep em nyx/agent/onboarding.py retorna 0 hits
- [ ] MICROCOPY.md seção "Capitalização e acentuação" presente
- [ ] Smoke ok
- [ ] Invariantes 14/14 (sem regressão)
- [ ] Sprint movida `producao/` → `concluidos/`
- [ ] Commit `feat(TUI-REDESIGN-25-01): capitalizacao + acentuacao em strings user-facing`

## Invariantes a preservar

- #2 (zero menção a IA externa)
- #4 (zero except silencioso)
- #6 (hex só em design_tokens*)
- #14 (glifos canônicos ○ ◐ ●)

## Anti-débito

- Acentuação em comentários técnicos de código fica para Onda 26 (não-bloqueante)
- Refactor de strings de erro com actionable fica para 25-11 (escopo dela)
- Tradução de logs internos fica fora (logs internos em PT-BR já estão OK)

## Verificação

```bash
bash scripts/sprint_invariants.sh > /tmp/inv_before.txt
FAIL_BEFORE=$(grep -c "^\[FAIL\]" /tmp/inv_before.txt)
# implementar
bash scripts/sprint_invariants.sh > /tmp/inv_after.txt
FAIL_AFTER=$(grep -c "^\[FAIL\]" /tmp/inv_after.txt)
[ "$FAIL_AFTER" -le "$FAIL_BEFORE" ] || echo "REGRESSAO"
./run.sh --smoke    # boot ok
grep -E "configuracao|permissoes|padrao|automacao" scripts/menu_wizard.py nyx/agent/onboarding.py || echo "limpo"
```

## Rollback

```bash
git reset --hard HEAD~1
```

---

*"Capitalização e acento são o primeiro respeito à língua." -- TUI-REDESIGN-25-01*
