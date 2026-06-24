# SPRINT FS-TOOLDESC-PROMPT-01 -- descricoes de tools + prompt dizem que a Nyx opera em qualquer caminho

## 0. SPEC (machine-readable)

```yaml
sprint:
  id: FS-TOOLDESC-PROMPT-01
  title: "Descricoes dos discovery tools dizem 'padrao: raiz do projeto' e o prompt nao instrui acesso universal -> o 3b nao SABE que pode explorar o FS todo"
  onda: 45
  bloco: "45 -- Acesso Universal & Autonomia (auditoria 2026-06-24)"
  prioridade: MEDIA
  tipo: Bugfix / Prompt & tool schemas (autonomia)
  dependencias: [FS-DISCOVERY-FREE-01]
  desbloqueia: []

  touches:
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/agent/tools/glob_tool.py
      reason: "tool_def parameters.path description (linha 22): 'Diretorio base (padrao: raiz do projeto)' -> esclarecer que aceita QUALQUER caminho absoluto do disco."
      linhas_alvo: "20-24 (tool_def)"
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/agent/tools/list_files.py
      reason: "description path (linha 21) 'Diretorio a listar (padrao: raiz)' -> idem."
      linhas_alvo: "20-23"
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/agent/tools/search.py
      reason: "description path (linha 28) 'Diretorio ou arquivo (padrao: raiz)' -> idem."
      linhas_alvo: "26-30"
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/agent/tools/read_file.py
      reason: "confirmar a description do path; se sugerir restricao a raiz, esclarecer acesso a caminho absoluto."
      linhas_alvo: "tool_def (confirmar via grep)"
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/agent/prompt.py
      reason: "adicionar UMA diretiva concisa: a Nyx pode ler/listar/buscar/operar em qualquer caminho absoluto do disco (acesso universal, ADR-009), nao so na raiz do projeto. CONFIRMAR via grep a linha exata; NAO inchar o prompt compacto (PERF-INFERENCE-01 ~800 tok); CUIDADO: a 361 ja trocou grep_files->search na linha ~106, nao reintroduzir nome de tool inexistente."
      linhas_alvo: "build_system_prompt (full); confirmar linhas"

  creates: []
  removes: []

  forbidden:
    - "Inchar o system prompt compacto (turnos sem tool) -- a diretiva de acesso so faz sentido no prompt FULL (com tools); manter o compacto enxuto"
    - "Citar nome de tool inexistente (ex.: grep_files); usar os nomes reais (search/glob/list_files/read_file)"
    - "Prometer escrita livre: a diretiva e sobre LEITURA/exploracao universal; escrita segue a camada de permissoes"
    - "Adicionar emoji ou mencao a IA externa"

  tests:
    - cmd: "bash scripts/sprint_invariants.sh"
      timeout: 180
      esperado: "14/14 PASS"
    - cmd: "./run.sh --gauntlet --only rapido"
      timeout: 300
      esperado: "APROVADO (19/19)"
    - cmd: "./run.sh --gauntlet --only proxy"
      timeout: 300
      esperado: "APROVADO (think-adaptativo e budget de prompt intactos)"
    - cmd: "probe runtime real (proxy + 3b): 'liste os arquivos em /etc' -> a Nyx chama list_files/glob com /etc e responde com a lista, SEM pedir /sandbox add"
      timeout: 240
      esperado: "o agente exerce acesso universal de forma autonoma"

  acceptance_criteria:
    - "As descricoes de glob/list_files/search/read_file deixam claro que aceitam qualquer caminho absoluto"
    - "O prompt FULL tem uma diretiva concisa de acesso universal (ADR-009), sem nome de tool inexistente"
    - "O prompt compacto NAO cresce (verificar contagem de tokens/linhas antes/depois)"
    - "Runtime real: a Nyx explora um path fora da raiz por conta propria ao ser pedido"
    - "Invariantes 14/14; gauntlet rapido+proxy APROVADO; ruff/acento OK; spec -> concluidos/"
```

---

**Status:** PENDENTE
**Data criacao:** 2026-06-24
**Origem:** Wave 0 (`AUDIT_2026_06_24.md`, secao 2, "segundo eixo: autonomia"). O fix de codigo
(FS-DISCOVERY-FREE-01) torna o acesso POSSIVEL; esta sprint torna o acesso CONHECIDO pelo modelo, para ele
USAR a feature de forma independente.
**Modelo obrigatorio:** claude-opus (sem subagentes; implementação direta)

---

## Contexto do projeto (snapshot -- nao referencia)

> - O qwen2.5-coder:3b age conforme o que o prompt e as descricoes das tools afirmam. Se a description diz
>   "padrao: raiz do projeto" e o prompt nao menciona acesso fora dela, o modelo nao tenta -- mesmo com o
>   codigo ja liberado (apos FS-DISCOVERY-FREE-01).
> - ADR-008/PERF-INFERENCE-01: o prompt compacto (~800 tok) e usado em turnos sem tool; nao deve crescer. A
>   diretiva entra so no prompt FULL.
> - ADR-026/033: a Nyx nunca alucina sucesso; a diretiva nao deve sugerir que ela "ja leu" algo -- so que
>   ela PODE ler qualquer caminho.

---

## Problema

Apos FS-DISCOVERY-FREE-01, o codigo permite explorar todo o disco, mas:
- as descricoes dos tools (`glob`/`list_files`/`search`) dizem "padrao: raiz do projeto", sugerindo limite;
- o system prompt nao diz ao modelo que ele pode operar em caminhos absolutos arbitrarios.

Resultado: o 3b continua agindo "preso" a raiz por falta de informação, e a feature (acesso universal) fica
subutilizada -- o oposto de "saber usar cada feature de forma independente".

---

## Solucao proposta

1. Reescrever as 4 descricoes de path para algo como: *"Diretorio base. Aceita caminho relativo (raiz do
   projeto) OU qualquer caminho absoluto do disco (ex.: /etc, /home/user/outro-projeto)."*
2. Adicionar ao prompt FULL uma linha concisa de acesso universal, por exemplo: *"Voce pode ler, listar e
   buscar em qualquer caminho absoluto do disco -- nao apenas na raiz do projeto. Segredos
   (.ssh/.gnupg/.aws) sao bloqueados; escrita pede confirmacao."*
3. Verificar (grep) e preservar o estado correto pos-361 (sem `grep_files`); usar so nomes reais de tool.

---

## Proof-of-work esperado (runtime real)

```bash
bash scripts/sprint_invariants.sh
./run.sh --gauntlet --only rapido
./run.sh --gauntlet --only proxy
python3 ~/.config/zsh/scripts/validar-acentuacao.py --paths nyx/agent/prompt.py nyx/agent/tools/glob_tool.py nyx/agent/tools/list_files.py nyx/agent/tools/search.py nyx/agent/tools/read_file.py
/home/andrefarias/.local/bin/ruff check nyx/agent/prompt.py nyx/agent/tools/glob_tool.py nyx/agent/tools/list_files.py nyx/agent/tools/search.py nyx/agent/tools/read_file.py
# contar tokens/linhas do prompt COMPACTO antes/depois (deve ser igual)
# runtime real: ./run.sh ; prompt "liste os arquivos em /etc e diga quantos sao"
#   -> a Nyx chama list_files/glob com /etc e responde a contagem (sem pedir /sandbox add)
# cleanup: pkill -f "nyx/proxy.py"; pkill -f "ollama serve"; nvidia-smi
```

---

## Criterio binario de aceite

- [ ] descricoes dos 4 tools esclarecem caminho absoluto
- [ ] prompt FULL tem diretiva de acesso universal (nomes reais de tool)
- [ ] prompt compacto inalterado (contagem antes/depois igual)
- [ ] runtime real: a Nyx explora /etc por conta propria
- [ ] invariantes 14/14, gauntlet rapido+proxy APROVADO, ruff/acento OK; spec -> concluidos/

---

## Riscos

| Risco | Mitigacao |
|-------|-----------|
| Diretiva incha o prompt e degrada o 3b | So no prompt FULL; uma linha; medir antes/depois |
| Modelo passa a "vazar" para fora da raiz sem necessidade | A diretiva diz que PODE, nao que DEVE; o intent classifier ja decide quando usar tool |
| Reintroduzir nome de tool inexistente | grep por `grep_files`/nomes invalidos = 0 antes de fechar |

---

*"Uma porta destrancada que ninguem avisou que abre continua sendo uma parede." -- anonimo*
