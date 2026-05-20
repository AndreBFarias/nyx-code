## 0. SPEC (machine-readable)

```yaml
sprint:
  id: P5-B
  title: "Configuração -- /config, /env, /permissions, /hooks, /theme"
  touches:
    - path: nyx/agent/commands.py
      reason: "5 novos commands de configuração"
    - path: scripts/gauntlet/nyx_gauntlet.py
      reason: "5 testes novos"
  origin:
    primary: "openclaud/src/commands/config/"
    secondary: "openclaud/src/commands/env/"
  tests:
    - cmd: "./run.sh --gauntlet --only p5_config"
      timeout: 30
  acceptance_criteria:
    - "/config mostra e edita configuração"
    - "/env mostra variáveis de ambiente relevantes"
    - "/permissions mostra níveis de permissão por tool"
    - "/hooks lista hooks registrados"
    - "/theme lista e troca temas"
```

---

# Sprint P5-B -- Commands de Configuração

**Status:** CONCLUIDA (header corrigido em MASTER-CLEANUP-02 2026-05-20; presença em concluidos/ implica CONCLUIDA conforme convenção do projeto)
**Data:** 2026-04-05
**Prioridade:** MÉDIA
**Tipo:** Port (TS -> Python)
**Dependências:** P3-D
**Desbloqueia:** P5-D

---

## Implementação

### /config
- `/config` -- mostra config atual (modelo, porta, proxy)
- `/config key` -- mostra valor de chave específica
- `/config key value` -- define valor

### /env
- `/env` -- mostra variáveis relevantes (OPENAI_*, NYX_*, OLLAMA_*)
- Filtra e formata variáveis de ambiente

### /permissions
- `/permissions` -- lista tools e seus níveis de permissão
- Mostra: auto_approve, confirm_once, always_confirm, deny
- Agrupa por nível

### /hooks
- `/hooks` -- lista hooks registrados (pre e post)
- `/hooks clear` -- remove todos os hooks

### /theme
- `/theme` -- mostra tema atual
- `/theme list` -- lista temas disponíveis
- `/theme nome` -- troca para tema especificado

### Testes Gauntlet

| ID | Nome | Validação |
|----|------|-----------|
| P5C-01 | /config mostra config | Contém "modelo" ou "proxy" |
| P5C-02 | /env mostra variáveis | Contém "OPENAI" ou "NYX" |
| P5C-03 | /permissions lista tools | Contém "read_file" e "auto" |
| P5C-04 | /hooks registrado | Command existe |
| P5C-05 | /theme lista temas | Contém "nyx" ou "dracula" |

## Verificação

- [ ] 5 commands registrados
- [ ] /config lê configuração real
- [ ] /env filtra variáveis corretamente
- [ ] /permissions mostra todos os níveis
- [ ] /theme integra com ThemeManager existente
- [ ] 5 testes Gauntlet passando

---

*"Conhece-te a ti mesmo." -- Sócrates*
