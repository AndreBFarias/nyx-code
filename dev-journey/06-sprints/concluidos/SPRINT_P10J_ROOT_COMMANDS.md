## 0. SPEC (machine-readable)

```yaml
sprint:
  id: P10-J
  title: "Root commands -- advisor, brief, commit-push-pr, insights, security-review"
  touches:
    - path: nyx/agent/commands.py
      reason: "5 novos commands root"
  origin:
    primary: "openclaud/src/commands/advisor.ts"
  tests:
    - cmd: "./run.sh --gauntlet --only p10_root"
      timeout: 30
```

---

# Sprint P10-J -- Root Commands

**Status:** PENDENTE  **Tipo:** Port  **Deps:** P10-D

## Commands

| Command | OpenClaude | Descrição |
|---------|-----------|-----------|
| /advisor | advisor.ts | Conselheiro: sugere melhorias no código |
| /brief-cmd | brief.ts | Gera brief da sessão (diferente do BriefTool) |
| /commit-push-pr | commit-push-pr.ts | Commit + push + cria PR em um passo |
| /insights | insights.ts | Insights sobre o código/projeto |
| /security-review | security-review.ts | Revisão de segurança automatizada |

---

*"A revisão constante é o preço da excelência." -- Tom Peters*
