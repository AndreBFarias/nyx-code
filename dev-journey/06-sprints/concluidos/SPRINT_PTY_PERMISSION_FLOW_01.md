# SPRINT PTY-PERMISSION-FLOW-01 — Cockpit UI pra aprovar permissões do PTY

## 0. SPEC

```yaml
sprint:
  id: PTY-PERMISSION-FLOW-01
  title: "Cockpit captura prompts de permissão do PTY e expõe botão Aprovar/Negar"
  onda: 24
  bloco: 24.3 Cockpit
  prioridade: MÉDIA
  tipo: Feature
  dependencias: [COCKPIT-02, NYX-AUTO-APPROVE-01]
  desbloqueia: [VALIDATE-FINAL-01-PARTE-2]
  origem: "Achado real 2026-05-18: PTY no cockpit nao tem canal automatico de resposta para CONFIRM_ONCE. NYX-AUTO-APPROVE-01 resolve o caso CI/automacao; esta sprint cobre o caso humano (ver o prompt e clicar Aprovar)."

  touches:
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/cockpit/static/terminal.html
      reason: "Adicionar overlay/modal quando regex de prompt CONFIRM_ONCE detectada no stream"
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/cockpit/server.py
      reason: "POST /control/repl/permission {answer: yes|no} envia S\\n ou n\\n para o PTY"

  forbidden:
    - "Auto-aprovar sem clique humano"
    - "Persistir resposta padrão entre sessões"

  tests:
    - cmd: "echo 'curl POST /control/repl/permission'"
      timeout: 5
      deve_passar: true

  acceptance_criteria:
    - "Quando PTY emite '[permissão: uma vez]' frontend mostra modal com Aprovar/Negar"
    - "POST /control/repl/permission {answer:'yes'} envia 'S\\n' ao PTY"
    - "POST /control/repl/permission {answer:'no'} envia 'n\\n'"
    - "Modal some quando PTY consome a resposta"
    - "Funciona em uso humano (Chrome) e via curl (automatizacao headless)"
```

---

# Sprint PTY-PERMISSION-FLOW-01

**Status:** CONCLUIDA (2026-05-19)
**Data criação:** 2026-05-18 (achado de uso real via cockpit/REPL)
**Data conclusão:** 2026-05-19
**Modelo obrigatório:** claude-opus-4-7

---

## Contexto

Mesma origem que NYX-AUTO-APPROVE-01 (sessão 2026-05-18). Esta sprint cobre o caso humano: usuário vê prompt de permissão no terminal embedded do cockpit e quer responder via clique, não via texto.

## Solução proposta

### Frontend (terminal.html)

Listener no stream do xterm: regex `/\[permissão: uma vez\]\s+Executar (\w+)\(/` captura o nome da tool. Mostra modal:
```
write_file pede permissão. Aprovar?
[Aprovar uma vez] [Sempre aprovar essa tool] [Negar]
```

Cada botão chama:
```js
fetch("/control/repl/permission", {method:"POST",
  body: JSON.stringify({answer: "yes" | "yes_always" | "no"})});
```

### Backend (server.py)

```python
@app.post("/control/repl/permission")
async def control_repl_permission(payload: dict):
    answer = payload.get("answer")
    if _active_pty is None:
        raise HTTPException(409, "nenhuma sessão PTY ativa")
    if answer == "yes":
        _active_pty.write(b"S\n")
    elif answer == "yes_always":
        _active_pty.write(b"a\n")  # ou whatever o REPL espera para "always"
    elif answer == "no":
        _active_pty.write(b"n\n")
    else:
        raise HTTPException(400, "answer inválido")
    return {"sent": answer}
```

---

## Critério binário

- [ ] Frontend detecta prompt CONFIRM_ONCE e exibe modal
- [ ] POST `/control/repl/permission {answer}` funciona via curl
- [ ] 3 opções: yes, yes_always, no
- [ ] Modal some após resposta
- [ ] Sprint movida `producao/` → `concluidos/`
- [ ] Commit `feat(PTY-PERMISSION-FLOW-01): UI cockpit aprova permissoes do PTY`

---

*"O humano clica; o agente responde. Sem deadlock." -- PTY-PERMISSION-FLOW-01*
