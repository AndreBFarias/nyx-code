# SPRINT GAUNTLET-FS-ARBITRARY-01 -- fase de gauntlet para acesso a path arbitrario (regressao do bug #1)

## 0. SPEC (machine-readable)

```yaml
sprint:
  id: GAUNTLET-FS-ARBITRARY-01
  title: "O gauntlet nao testa acesso a path fora da raiz -- o proprio bug #1 nao tinha teste de regressao"
  onda: 45
  bloco: "45 -- Acesso Universal & Autonomia (auditoria 2026-06-24)"
  prioridade: ALTA
  tipo: Teste / Gauntlet (cobertura)
  dependencias: [FS-DISCOVERY-FREE-01]
  desbloqueia: []

  touches:
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/scripts/gauntlet/nyx_gauntlet.py
      reason: "adicionar fase `fs_arbitrary` no padrao da fase e2e_real (F2-01..08, ~linha 2958-3048): invoca ToolRegistry diretamente, zero mocks (ADR-010), contra fixture REAL fora de qualquer raiz permitida."
      linhas_alvo: "PHASE_GROUPS (51-182) + novo metodo _phase_fs_arbitrary; confirmar linhas via grep de e2e_real"
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/run.sh
      reason: "se a lista de fases do --only for explicita em run.sh, registrar `fs_arbitrary` como alvo valido (confirmar; varias fases sao auto-descobertas)."
      linhas_alvo: "bloco de --only/--gauntlet (confirmar)"

  creates: []
  removes: []

  forbidden:
    - "Usar mock/monkeypatch (ADR-010): o fixture e criado no FS real e lido pelas tools reais"
    - "Usar ~/.nyx ou project_root como fixture: precisa ser FORA de todas as raizes permitidas (ex.: /tmp/...) para exercer o caminho de acesso livre"
    - "Deixar lixo: a fase cria e REMOVE o fixture (tmpdir) no teardown"
    - "Marcar PASS sem assertar conteudo (ADR-011): comparar a lista/conteudo retornado com o que foi escrito"
    - "Adicionar emoji ou mencao a IA externa"

  tests:
    - cmd: "bash scripts/sprint_invariants.sh"
      timeout: 180
      esperado: "14/14 PASS"
    - cmd: "./run.sh --gauntlet --only fs_arbitrary"
      timeout: 300
      esperado: "fase PASS com asserts de conteudo (glob/search/list/read fora da raiz) + secret bloqueado"
    - cmd: "./run.sh --gauntlet --only rapido"
      timeout: 300
      esperado: "APROVADO (a fase nova nao quebra a contagem da rapida)"

  acceptance_criteria:
    - "Fase fs_arbitrary criada no padrao e2e_real (ToolRegistry direto, zero mocks)"
    - "Cobre: read_file, glob, search, list_files num dir fora de todas as raizes permitidas, assertando conteudo"
    - "Cobre o caso negativo de seguranca: ler um secret (.ssh/id_rsa) e BLOQUEADO"
    - "Cobre regressao: glob/search/list DENTRO do projeto continuam corretos"
    - "Fixture criado e removido (sem lixo no FS); contagem total de testes do gauntlet sobe coerente"
    - "Invariantes 14/14; ruff/acento OK; spec -> concluidos/"
```

---

**Status:** PENDENTE
**Data criacao:** 2026-06-24
**Origem:** Wave 0 (`AUDIT_2026_06_24.md`, dimensao 5). O gauntlet tem fase `e2e_real` (F2-*) que so usa
paths legitimos do projeto -- o bug #1 (acesso fora da raiz) nunca teve teste. Esta fase e o **teste de
regressao permanente** do bug.
**Modelo obrigatorio:** claude-opus (sem subagentes; implementação direta)

---

## Contexto do projeto (snapshot -- nao referencia)

> - ADR-010 (zero mocks) e ADR-011 (conteudo verificado): a fase cria arquivos reais e compara o retorno
>   das tools com o que foi escrito.
> - A fase `e2e_real` (`nyx_gauntlet.py:2958-3048`) ja chama `ToolRegistry` diretamente e usa
>   `_gauntlet_tmp_dir()` -- bom molde, mas aquele tmp pode cair sob `~/.nyx` (raiz permitida). Esta fase
>   precisa de um dir FORA de project_root/`~/.nyx`/extras para exercer o caminho de acesso livre.
> - Raizes permitidas: `_get_allowed_roots()` em `base.py` = [_ACTIVE_ROOT, ~/.nyx, *extras]. `/tmp/...`
>   nao esta nelas -> ideal para o teste.

---

## Problema

A regressao do bug #1 nao tem rede de seguranca. Se uma sprint futura reintroduzir o filtro
`is_relative_to(project_root)`, nada no gauntlet pega. Tambem nao ha teste do contrato de seguranca (secret
bloqueado no acesso livre).

---

## Solucao proposta

Adicionar `_phase_fs_arbitrary` (registrada em `PHASE_GROUPS`):

1. **setup:** criar `tmpdir = /tmp/nyx_fs_arbitrary_<pid>/` com `sub/a.py` (`print("oi")`) e `b.txt`
   (`alvo-de-busca`).
2. **FS-ARB-01 read_file:** ler `tmpdir/b.txt` -> conteudo == `alvo-de-busca`.
3. **FS-ARB-02 glob:** `glob {pattern:"**/*.py", path:tmpdir}` -> output contem `a.py` (nao "Nenhum
   arquivo").
4. **FS-ARB-03 search:** `search {pattern:"alvo-de-busca", path:tmpdir}` -> 1+ ocorrencia.
5. **FS-ARB-04 list_files:** `list_files {path:tmpdir}` -> lista `sub` e `b.txt`.
6. **FS-ARB-05 secret bloqueado:** `read_file {path:"~/.ssh/id_rsa"}` (ou nome de secret) -> `success ==
   False`, erro de seguranca.
7. **FS-ARB-06 regressao no projeto:** `glob {pattern:"*.py", path:"nyx/agent"}` (relativo) -> retorna
   arquivos do projeto, paths relativos a raiz (formato inalterado).
8. **teardown:** remover `tmpdir`.

Asserts de conteudo em todos (ADR-011). Zero mocks (ADR-010).

---

## Proof-of-work esperado (runtime real)

```bash
bash scripts/sprint_invariants.sh                  # 14/14 PASS
./run.sh --gauntlet --only fs_arbitrary            # FS-ARB-01..06 PASS (asserts de conteudo)
./run.sh --gauntlet --only rapido                  # APROVADO (contagem coerente)
python3 ~/.config/zsh/scripts/validar-acentuacao.py --paths scripts/gauntlet/nyx_gauntlet.py
/home/andrefarias/.local/bin/ruff check scripts/gauntlet/nyx_gauntlet.py
ls /tmp/nyx_fs_arbitrary_* 2>/dev/null            # vazio (teardown removeu o fixture)
# cleanup: pkill -f "nyx/proxy.py"; pkill -f "ollama serve"; nvidia-smi
```

---

## Criterio binario de aceite

- [ ] fase fs_arbitrary com FS-ARB-01..06, asserts de conteudo, zero mocks
- [ ] fixture fora de todas as raizes permitidas (/tmp/...) criado e removido
- [ ] caso negativo (secret) verde
- [ ] regressao dentro do projeto verde
- [ ] gauntlet rapido APROVADO, contagem total coerente
- [ ] invariantes 14/14, ruff/acento OK; spec -> concluidos/

---

## Riscos

| Risco | Mitigacao |
|-------|-----------|
| `/tmp` montado noexec/diferente em algum ambiente | usar `tempfile.mkdtemp()` (respeita TMPDIR) em vez de path fixo |
| Fase falha por dependencia da 370 nao aplicada | dependencia declarada; executar 370 antes (e a fase prova a 370) |
| Lixo no FS se o teste abortar | teardown em finally; nome com pid para rastrear |
| rg/grep ausentes mudam o caminho do search | o teste cobre o resultado, nao o caminho; 370 ja conserta o fallback Python |

---

*"Bug sem teste de regressao volta pela mesma porta na proxima onda." -- anonimo*
