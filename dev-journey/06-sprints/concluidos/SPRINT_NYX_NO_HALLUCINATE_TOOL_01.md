# SPRINT NYX-NO-HALLUCINATE-TOOL-01 — Bloquear "sucesso" alucinado sem tool real

## 0. SPEC

```yaml
sprint:
  id: NYX-NO-HALLUCINATE-TOOL-01
  title: "AgentLoop rejeita 'Arquivo criado com sucesso' do modelo sem tool call correspondente"
  onda: 24
  bloco: 24.6 Infra resiliente
  prioridade: ALTA
  tipo: Bugfix
  dependencias: []
  desbloqueia: [confianca em automacao]
  origem: "Achado real 2026-05-18 via Playwright + cockpit. Nyx respondeu 'Arquivo criado com sucesso. Certo!' apos eu enviar 'S', mas o arquivo NAO foi criado no filesystem -- modelo alucinou execucao."

  touches:
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/agent/loop/_core.py
      reason: "Antes de marcar SessionState.DONE, validar que ultima tool call retornou sucesso"
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/agent/validator.py
      reason: "post_validate detecta padrao 'criado com sucesso' sem tool_call write/edit precedente -> alerta"

  forbidden:
    - "Quebrar fluxo de chat sem tool (saudacoes, perguntas)"
    - "Negar respostas legitimas (modelo pode dizer 'pronto' apos tool real)"

  tests:
    - cmd: "echo 'tente: peça pra Nyx criar arquivo fora do project root + S pra aprovar permissao. Esperado: Nyx admite preflight bloqueou, nao alucina sucesso'"
      timeout: 60

  acceptance_criteria:
    - "Nyx NUNCA afirma 'criado com sucesso' se ultima tool retornou erro"
    - "post_validate detecta padrao e injeta correcao no contexto"
    - "Validador identifica falsificacao em testes do Gauntlet"
    - "Documentado como gambiarra-do-modelo em GAMBIARRAS_POR_SPRINT.md"
```

---

# Sprint NYX-NO-HALLUCINATE-TOOL-01

**Status:** CONCLUIDA (2026-05-19)
**Data criação:** 2026-05-18 (achado real Playwright)
**Modelo obrigatório:** claude-opus-4-7

---

## Contexto

Cenário (sessao 2026-05-18 ~05:00):

1. Pedi ao Nyx via cockpit: criar arquivo em /tmp (fora do project root).
2. Preflight bloqueou: "Fora do projeto Nyx-Code: '/tmp/...'. Para acessar outro projeto, inicie o Nyx la."
3. Enviei "S" (intentando aprovar permissao, mas o prompt anterior ja tinha fechado).
4. Nyx interpretou "S" como novo prompt e respondeu: **"Arquivo criado com sucesso. Certo!"**
5. ls do filesystem: arquivo NAO existe.

Modelo qwen2.5-coder:3b alucinou execucao. Sem tool_call no turno, mas afirmou sucesso. Falha de confianca grave.

### Sintoma observavel

Screenshot `nyx_internal_pos_S.png`:
```
nyx> S
[voce: S]
:* pensando...
Nyx
Arquivo criado com sucesso. Certo!
```

Sem card "write_file executando" antes. Tool NUNCA foi chamada nesse turno.

## Solucao proposta

3 camadas:

**Nivel 1 -- validator pos-loop:**

Em `nyx/agent/validator.py`, regex contra ultima resposta do assistente:

```python
FORGE_PATTERNS = [
    r"(?i)arquivo criado com sucesso",
    r"(?i)(criado|salvo|escrito) com sucesso",
    r"(?i)pronto[!.,]?\s*$",  # quando ultima tool foi erro/none
]

def post_validate(session, ...):
    last_action = session.last_action_type
    last_text = session.last_assistant_text
    if last_action in (None, ActionType.DONE) and not has_recent_successful_tool(session):
        for p in FORGE_PATTERNS:
            if re.search(p, last_text):
                return ValidationResult(
                    warn=True,
                    message="modelo afirma sucesso sem tool call correspondente",
                )
```

**Nivel 2 -- prompt hardening:**

Adicionar ao system_prompt do Nyx instrucao explicita: "Voce NUNCA afirma que criou/salvou/escreveu arquivo se nao usou tool write_file ou edit_file no turno corrente. Se usuario pediu acao mas preflight bloqueou, explique o motivo sem inventar."

**Nivel 3 -- UI alert no cockpit:**

Se validator.warn=true, banner amarelo "ATENCAO: resposta nao verificada por tool" aparece sobre a caixa do Nyx.

## Criterio binario

- [ ] post_validate detecta padrao FORGE quando sem tool
- [ ] System prompt instrui modelo a nao alucinar
- [ ] Gauntlet adiciona teste Q-X em qualidade
- [ ] Sprint movida -> concluidos
- [ ] Commit `feat(NYX-NO-HALLUCINATE-TOOL-01): rejeita 'sucesso alucinado' sem tool call`

---

*"Modelo que mente sobre execucao mata confianca." -- NYX-NO-HALLUCINATE-TOOL-01*
