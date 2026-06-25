# SPRINT WORKTREE-BASELINES-01 -- baselines/checkpoint do gauntlet poluem o working tree (gitignore + limpeza)

## 0. SPEC (machine-readable)

```yaml
sprint:
  id: WORKTREE-BASELINES-01
  title: "Os artefatos do gauntlet (baselines/*.json + checkpoint.json) sao regenerados a cada run e vivem como modificados/untracked no working tree; o .gitignore cobre `*.md` mas nao os `*.json` -> ruido permanente e risco de commit acidental"
  onda: 46
  bloco: "46 -- Saneamento de CI & Working Tree + achados da Onda de Validação 1"
  prioridade: MEDIA
  tipo: Higiene / Git (working tree)
  dependencias: []
  desbloqueia: []

  touches:
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/.gitignore
      reason: "ja ignora dev-journey/07-reports/gauntlet/*.md mas NAO os artefatos .json (baselines/*.json, checkpoint.json), que sao regenerados a cada gauntlet run. Adicionar os padroes para parar o ruido."
      linhas_alvo: "secao do gauntlet (perto da linha que ignora os *.md)"

  creates: []
  removes: []

  forbidden:
    - "git rm do arquivo no DISCO (so `git rm --cached` para destrackear; o arquivo continua existindo para o gauntlet)"
    - "Ignorar a pasta inteira dev-journey/07-reports/gauntlet/ (perderia READMEs/docs versionados que devam ficar); ignorar so os artefatos regenerados (baselines/*.json, checkpoint.json, e os *.md ja ignorados)"
    - "Apagar o historico de baselines do DISCO (so destrackear; a curadoria de historico de regressao e da ONDA-48 GAUNTLET-REGRESSION-GUARD-01, que criara um arquivo curado proprio)"

  tests:
    - cmd: "git status --short dev-journey/07-reports/gauntlet/"
      timeout: 30
      esperado: "apos o fix + git rm --cached, os baselines/*.json e checkpoint.json NAO aparecem mais como M/??"
    - cmd: "git check-ignore dev-journey/07-reports/gauntlet/baselines/baseline_2026-06-03.json dev-journey/07-reports/gauntlet/checkpoint.json"
      timeout: 30
      esperado: "ambos retornam (estao ignorados)"
    - cmd: "./run.sh --gauntlet --only rapido ; git status --short dev-journey/07-reports/gauntlet/"
      timeout: 300
      esperado: "apos um run, o gauntlet ainda escreve os artefatos no disco, mas o git NAO os mostra (ignorados)"
    - cmd: "bash scripts/sprint_invariants.sh"
      timeout: 180
      esperado: "14/14 PASS (check #12 'root limpo' / working tree mais limpo)"

  acceptance_criteria:
    - ".gitignore cobre dev-journey/07-reports/gauntlet/baselines/*.json e checkpoint.json"
    - "Os artefatos atualmente tracked (ex.: baseline_2026-06-01.json, checkpoint.json) sao destrackeados via `git rm --cached` (continuam no disco)"
    - "Apos um gauntlet run, `git status` nao mostra os artefatos do gauntlet"
    - "Nenhum doc legitimo da pasta foi ignorado por engano"
    - "Invariantes 14/14; spec -> concluidos/"
```

---

**Status:** CONCLUIDA (51791b1)
**Data criacao:** 2026-06-25
**Origem:** Wave 0 (AUDIT_2026_06_24.md, dimensao 6). O `git status` inicial do engajamento mostrava 6 baselines .json untracked + checkpoint.json e baseline_2026-06-01.json modificados; o `.gitignore` cobre so os `*.md` do gauntlet. As execucoes da ONDA-45/46 (que rodam o gauntlet) so aumentaram esse ruido.
**Modelo obrigatorio:** modelo principal local (sem subagentes; implementação direta)

---

## Problema

`dev-journey/07-reports/gauntlet/` acumula artefatos regenerados a cada run do gauntlet: `baselines/baseline_<data>.json` e `checkpoint.json`. O `.gitignore` ignora `dev-journey/07-reports/gauntlet/*.md` (relatorios) mas NAO os `.json`. Resultado: o working tree fica permanentemente sujo com esses arquivos (modificados ou untracked), criando ruido em todo `git status` e risco de commit acidental. Alguns ja estao TRACKED (ex.: `baseline_2026-06-01.json`, `checkpoint.json`).

---

## Causa-raiz

A regra de gitignore do gauntlet cobriu so os `.md` quando os baselines `.json` foram introduzidos depois, sem atualizar o ignore. Parte dos artefatos foi commitada historicamente (ficou tracked).

---

## Solucao proposta

1. Adicionar ao `.gitignore`, na secao do gauntlet:
   ```
   dev-journey/07-reports/gauntlet/baselines/*.json
   dev-journey/07-reports/gauntlet/checkpoint.json
   ```
2. Destrackear os que ja estao no indice (mantendo no disco): `git rm --cached dev-journey/07-reports/gauntlet/checkpoint.json dev-journey/07-reports/gauntlet/baselines/<tracked>.json`.
3. Confirmar que docs legitimos da pasta (se houver) seguem versionados.

Observacao: o historico de regressao de performance (rolling baselines) e responsabilidade da ONDA-48 `GAUNTLET-REGRESSION-GUARD-01`, que criara um arquivo CURADO proprio -- nao depende de versionar cada run bruto.

---

## Proof-of-work esperado

```bash
git status --short dev-journey/07-reports/gauntlet/        # antes: varios M/??
# aplicar gitignore + git rm --cached
git check-ignore dev-journey/07-reports/gauntlet/checkpoint.json dev-journey/07-reports/gauntlet/baselines/baseline_2026-06-03.json
./run.sh --gauntlet --only rapido
git status --short dev-journey/07-reports/gauntlet/        # depois: limpo (artefatos ignorados)
bash scripts/sprint_invariants.sh                          # 14/14 PASS
```

---

## Criterio binario de aceite

- [ ] .gitignore cobre baselines/*.json + checkpoint.json
- [ ] artefatos tracked destrackeados via git rm --cached (continuam no disco)
- [ ] git status limpo na pasta do gauntlet apos um run
- [ ] nenhum doc legitimo ignorado por engano
- [ ] invariantes 14/14; spec -> concluidos/

---

## Riscos

| Risco | Mitigacao |
|-------|-----------|
| Destrackear algo que o dono queria versionar | so baselines/*.json + checkpoint.json (artefatos regeneraveis); confirmar com o dono se houver baseline "marco" a manter (pode ficar via exceção `!baseline_marco.json`) |
| `git rm --cached` apagar do disco | usar SEMPRE `--cached` (nunca `git rm` puro) |

---

## Anti-debito (achado herdado, NAO desta sprint)

`scripts/gauntlet/nyx_gauntlet.py` tem ~5 identificadores Python sem acento (`canonicos`/`invalido`/`canonico`/`padroes`, linhas ~1333/1497/1935/4811/4819) -- pre-existentes, fora do escopo desta sprint. Candidato a `INFRA-GAUNTLET-ACENTO-FIX-01` (ONDA-46/higiene) se o dono quiser drenar.

---

*"Working tree limpo e a diferenca entre 'sei o que mudei' e 'acho que nao mexi nisso'." -- anonimo*
