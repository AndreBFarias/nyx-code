# SPRINT FS-REMINDER-SYNC-01 -- o reminder reinjetado contradiz o acesso universal (completa a ONDA-45)

## 0. SPEC (machine-readable)

```yaml
sprint:
  id: FS-REMINDER-SYNC-01
  title: "build_reminder (prompt.py:186) reinjeta 'Sandbox: pode tocar apenas {project_root}' todo turno, contradizendo a diretiva de acesso universal (131-134); a linha reinjetada vence e o 3b volta a se limitar a raiz"
  onda: 45
  bloco: "45 -- follow-up da Onda de Validação 1 (2026-06-24)"
  prioridade: ALTA
  tipo: Bugfix / Prompt (completa o bug #1)
  dependencias: [FS-TOOLDESC-PROMPT-01]
  desbloqueia: []

  touches:
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/agent/prompt.py
      reason: "build_reminder linha 186: `- Sandbox: pode tocar apenas {project_root} (e roots extra opt-in).` -- reinjetado periodicamente (NYX-PROMPT-REINJECT-01) e CONTRADIZ a diretiva de acesso universal do prompt principal (131-134). Por ser a instrucao mais recente no contexto, vence; o 3b para de explorar fora da raiz. Reescrever para refletir o acesso universal real do validate_path."
      linhas_alvo: "186 (dentro de build_reminder, lines 177-203)"

  creates: []
  removes: []

  forbidden:
    - "Remover a linha por completo (o reminder DEVE mencionar a politica de acesso; o problema e o texto restritivo, nao a presenca)"
    - "Tornar a linha longa a ponto de inchar o reminder reinjetado (ele aparece varias vezes no contexto do 3b -- manter conciso, 1 linha)"
    - "Mexer no enforcement (validate_path) ou em qualquer outra linha do reminder (350/351/353/354/355 sao de outras sprints, intactas)"
    - "Reintroduzir nome de tool inexistente; emoji; mencao a IA externa"

  tests:
    - cmd: "bash scripts/sprint_invariants.sh"
      timeout: 180
      esperado: "14/14 PASS"
    - cmd: "./run.sh --gauntlet --only rapido"
      timeout: 300
      esperado: "APROVADO"
    - cmd: "./run.sh --gauntlet --only fs_arbitrary"
      timeout: 300
      esperado: "PASS (enforcement intacto)"
    - cmd: "probe runtime real (proxy + 3b): 'liste os arquivos em /etc' apos 2-3 turnos (para o reminder ja ter sido reinjetado) -> a Nyx chama list_files/glob com /etc SEM se recusar nem pedir /sandbox add"
      timeout: 240
      esperado: "o reminder nao mais contradiz; a Nyx explora fora da raiz de forma autonoma"

  acceptance_criteria:
    - "A linha 186 do reminder reflete acesso universal de leitura (coerente com prompt.py:131-134 e com validate_path), nao 'apenas project_root'"
    - "Continua mencionando segredos bloqueados + escrita por confirmacao (1 linha concisa)"
    - "Probe runtime: apos varios turnos, a Nyx ainda explora paths fora da raiz (nao regride a mentalidade de raiz so)"
    - "Invariantes 14/14; gauntlet rapido + fs_arbitrary verdes; ruff/acento OK; spec -> concluidos/"
```

---

**Status:** CONCLUIDA (2026-06-24, commit 0a77bf6)
**Data criacao:** 2026-06-24
**Origem:** Onda de Validacao 1 (pos-ONDA-45), achado #1 (BLOCKER). O fix 370 (codigo) + 371 (prompt principal) liberaram o acesso, mas o reminder reinjetado (`build_reminder`) ainda diz "pode tocar apenas {project_root}" -- e como o reminder reaparece a cada poucos turnos e e a instrucao mais recente, o 3b volta a se limitar a raiz. Provado as-user: probe "liste /etc" pulou a tool / desconfiou em conversa multi-turno. Esta sprint COMPLETA o bug #1 da perspectiva do usuario.
**Modelo obrigatorio:** claude-opus (sem subagentes; implementação direta)

---

## Contexto do projeto (snapshot -- nao referencia)

> - NYX-PROMPT-REINJECT-01: `build_reminder` (prompt.py:155-207) e reinjetado periodicamente no historico para contrariar drift do 3b. Tudo que esta nele e martelado no modelo varias vezes.
> - A diretiva de acesso universal (prompt.py:131-134, sprint 371) vive no prompt PRINCIPAL, que aparece UMA vez no topo. O reminder restritivo (186) aparece DEPOIS e mais vezes -> vence o conflito.
> - validate_path (base.py:182-193) ja libera o FS inteiro por default (so bloqueia secrets). O reminder mente sobre a politica real.

---

## Problema

`prompt.py:186` (dentro de `build_reminder`):

```python
f"- Sandbox: pode tocar apenas {project_root} (e roots extra opt-in).",
```

Contradiz `prompt.py:131-134`:

```
ACESSO UNIVERSAL (ADR-009): read_file, list_files, search e glob aceitam QUALQUER
caminho absoluto do disco (ex.: /etc, /home/user/outro-projeto), não só a raiz do projeto.
```

O 3b recebe as duas; a do reminder e mais recente/repetida -> ele se limita a raiz. A Onda de Validacao 1 provou: probe "liste /etc" pulou a tool ou desconfiou em conversa multi-turno.

---

## Causa-raiz

A politica de acesso foi atualizada em 2 dos 3 lugares (codigo 370, prompt principal 371) mas NAO no reminder reinjetado. Fonte de verdade duplicada e dessincronizada.

---

## Solucao proposta

Reescrever a linha 186 para refletir o acesso universal, coerente com 131-134 e com `validate_path`. Sugestao (ajustar a 1 linha concisa):

```python
f"- Acesso: pode ler/listar/buscar em QUALQUER caminho absoluto do disco (ADR-009), não só {project_root}. Segredos (.ssh/.gnupg/.aws) bloqueados; escrita pede confirmação.",
```

Mantem a referencia ao project_root como base/home, mas deixa claro que a leitura e universal. Conciso (1 linha) para nao inchar o reminder.

---

## Proof-of-work esperado (runtime real)

```bash
bash scripts/sprint_invariants.sh
./run.sh --gauntlet --only rapido
./run.sh --gauntlet --only fs_arbitrary
python3 ~/.config/zsh/scripts/validar-acentuacao.py --paths nyx/agent/prompt.py
/home/andrefarias/.local/bin/ruff check nyx/agent/prompt.py
# runtime: ./run.sh ; conversa de 3-4 turnos, depois "liste os arquivos em /etc e diga quantos sao"
#   -> a Nyx chama list_files/glob com /etc, sem se recusar nem pedir /sandbox add
# cleanup: pkill -f "nyx/proxy.py"; pkill -f "ollama serve"; nvidia-smi
```

---

## Criterio binario de aceite

- [ ] linha 186 reflete acesso universal (coerente com 131-134), nao "apenas project_root"
- [ ] menciona secrets bloqueados + escrita por confirmacao, 1 linha
- [ ] probe runtime: Nyx explora fora da raiz mesmo apos varios turnos
- [ ] invariantes 14/14, gauntlet rapido + fs_arbitrary verdes, ruff/acento OK; spec -> concluidos/

---

## Riscos

| Risco | Mitigacao |
|-------|-----------|
| Inchar o reminder degrada o 3b | 1 linha, substituindo a existente (delta ~0) |
| A alucinacao de resultado (#2 da onda) persistir | Fora de escopo desta sprint -- e capacidade do 3b (ADR-034), registrada como sprint propria; esta sprint so corrige a CONTRADICAO de politica |

---

*"De que adianta destrancar a porta e pendurar um aviso 'proibido entrar' do lado de dentro." -- anonimo*
