# SPRINT LANG-PROMPT-ACENT-01 — Acentuação correta no NYX_SYSTEM_PROMPT

## 0. SPEC (machine-readable)

```yaml
sprint:
  id: LANG-PROMPT-ACENT-01
  title: "NYX_SYSTEM_PROMPT em run.sh com acentuacao PT-BR correta (ç, ã, é, í)"
  onda: 23
  bloco: 23.0 Performance
  prioridade: BAIXA
  tipo: Polish
  dependencias: [LANG-ENFORCE-01]
  desbloqueia: []
  origem: "Achado colateral de WARMUP-ON-BOOT-01: validador de acentuacao detectou 'verificacao', 'nao', 'diagnostico', 'tecnico', 'Codigo', 'solucao', 'Diretorio' em run.sh:436-447 (string NYX_SYSTEM_PROMPT)."

  touches:
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/run.sh
      reason: "Linhas 436-447: NYX_SYSTEM_PROMPT com palavras sem acentuacao"

  creates: []
  removes: []
  n_to_n_pairs: []

  forbidden:
    - "Mudar regras do prompt alem da acentuacao"
    - "Tocar codigo fora do bloco NYX_SYSTEM_PROMPT"
    - "Quebrar caracteres unicode no heredoc bash"

  tests:
    - cmd: "python3 ~/.config/zsh/scripts/validar-acentuacao.py --paths /home/andrefarias/Desenvolvimento/Nyx-Code/run.sh"
      deve_passar: "exit 0 (zero violacoes em NYX_SYSTEM_PROMPT)"
    - cmd: "./run.sh --smoke"
      deve_passar: true
    - cmd: "bash scripts/sprint_invariants.sh"
      deve_passar: "FAIL_AFTER <= FAIL_BEFORE"

  acceptance_criteria:
    - "run.sh:436-447 NYX_SYSTEM_PROMPT contem 'verificação', 'não', 'diagnóstico', 'técnico', 'Código', 'solução', 'Diretório'"
    - "Smoke continua passando em <60s"
    - "Codificacao UTF-8 preservada (cat run.sh | file -b stdin == 'UTF-8')"
    - "Zero regressao em gauntlet rapido"
```

---

**Status:** PENDENTE
**Data criação:** 2026-05-17
**Modelo obrigatório:** claude-opus-4-7 (sem subagentes)
**Origem:** achado colateral de WARMUP-ON-BOOT-01

---

# Sprint LANG-PROMPT-ACENT-01

## Contexto

O validador `~/.config/zsh/scripts/validar-acentuacao.py` flagged 4 violações em `run.sh`:

```
run.sh:441: 'verificacao' → 'verificação'
run.sh:446: 'nao' → 'não'
```

E inspeção visual revela mais palavras sem acento na mesma string (`NYX_SYSTEM_PROMPT`):

```bash
NYX_SYSTEM_PROMPT="Sou Nyx. Codificadora. Vivo no terminal.

Regras:
- PT-BR. Frases curtas. Sem emojis. Sem verbosidade.
- Use tools (Read, Write, Edit, Bash, Glob, Grep) para tudo. Nao descreva. Execute.
- Formato: diagnostico -> solucao -> verificacao.
- Tom: tecnico, direto, preciso.
- Acesso total ao sistema de arquivos local.
- Diretorio: $(pwd)

Codigo limpo nao e arte. E higiene.
Ler -> Escrever -> Testar -> Terminar."
```

Palavras alvo: `Nao` → `Não`, `diagnostico` → `diagnóstico`, `solucao` → `solução`, `verificacao` → `verificação`, `tecnico` → `técnico`, `Diretorio` → `Diretório`, `Codigo` → `Código`, `nao` → `não`, `e arte` → `é arte`.

## Por que importa

O `NYX_SYSTEM_PROMPT` é enviado ao modelo (a string vira parte do system prompt da TUI). Modelo aprende a responder no estilo do prompt. Texto sem acentuação induz modelo a responder sem acentos (mesmo que LANG-ENFORCE-01 já corrija via retry, ideal é evitar disparar retry desde o boot).

## Solução

Edit literal substituindo cada palavra pelo equivalente acentuado. Atenção: heredoc bash com aspas duplas preserva UTF-8 sem escape.

## Verificação

```bash
python3 ~/.config/zsh/scripts/validar-acentuacao.py --paths /home/andrefarias/Desenvolvimento/Nyx-Code/run.sh
# Esperado: exit 0, zero violações no bloco NYX_SYSTEM_PROMPT
./run.sh --smoke
# Esperado: boot ok
file -b /home/andrefarias/Desenvolvimento/Nyx-Code/run.sh
# Esperado: "Bourne-Again shell script, ASCII text executable" OU "UTF-8 Unicode text"
```

---

*"Acentuação é higiene de texto, não enfeite." -- ADR-006*
