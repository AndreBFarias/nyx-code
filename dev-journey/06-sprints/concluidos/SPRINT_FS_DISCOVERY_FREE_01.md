# SPRINT FS-DISCOVERY-FREE-01 -- glob/search/list honram a raiz ativa e o acesso livre (bug #1)

## 0. SPEC (machine-readable)

```yaml
sprint:
  id: FS-DISCOVERY-FREE-01
  title: "glob/search filtram o resultado contra o project_root do boot -> fora da pasta padrao retorna vazio; viola ADR-009"
  onda: 45
  bloco: "45 -- Acesso Universal & Autonomia (auditoria 2026-06-24)"
  prioridade: ALTA
  tipo: Bugfix / Tools (acesso a filesystem)
  dependencias: []
  desbloqueia: [GAUNTLET-FS-ARBITRARY-01]

  touches:
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/agent/tools/glob_tool.py
      reason: "linha 36 `project = Path(project_root).resolve()` + linha 40-42 comprehension com `is_relative_to(project)` descartam TODO match fora da raiz do boot. Usa o project_root recebido (boot), nao o _ACTIVE_ROOT que segue /cd. Resultado: glob em /tmp ou /etc volta 'Nenhum arquivo encontrado' mesmo com validate_path liberando."
      linhas_alvo: "27-52 (execute); foco 36, 39-43"
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/agent/tools/search.py
      reason: "linha 36 `root = Path(project_root)` + linha 102 `rel = str(f.relative_to(root))` no _search_walk levantam ValueError fora da raiz (capturado -> success=False). So o caminho rapido rg/grep escapa. Alinhar display relativo a base validada/ativa, com fallback absoluto."
      linhas_alvo: "33-52 (execute), 94-138 (_search_walk), foco 102"
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/agent/tools/list_files.py
      reason: "REFERENCIA do comportamento correto (linha 44 ja tem fallback `... else str(e)`). Alinhar a base de display para get_active_project_root() (coerencia com /cd) sem mudar o comportamento observavel atual."
      linhas_alvo: "26-52, foco 37, 44"

  creates: []
  removes: []

  n_to_n_pairs:
    - descricao: "glob/search/list resolvem o mesmo problema (exibir path relativo a uma base e nao descartar o que validate_path ja liberou). Idealmente um helper unico em base.py (ex.: display_path(resolved, base)) elimina a divergencia das 3 implementacoes."
      paths:
        - /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/agent/tools/base.py
        - /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/agent/tools/glob_tool.py
        - /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/agent/tools/search.py
        - /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/agent/tools/list_files.py

  forbidden:
    - "Quebrar o formato de saida DENTRO do projeto (regressao): glob/search/list devem continuar exibindo paths relativos a raiz quando o alvo esta dentro dela"
    - "Mexer na politica de seguranca: secrets (.ssh/.gnupg/.aws) seguem bloqueados via validate_path/_is_secret_path; nao remover esse bloqueio"
    - "Ligar NYX_SANDBOX_STRICT por default ou alterar a semantica de validate_path (o gating de acesso ja esta correto; o bug e SO no display/filtro dos discovery tools)"
    - "Adicionar emoji ou mencao a IA externa"

  tests:
    - cmd: "bash scripts/sprint_invariants.sh"
      timeout: 180
      esperado: "14/14 PASS"
    - cmd: "./run.sh --gauntlet --only rapido"
      timeout: 300
      esperado: "APROVADO (19/19) -- regressao zero dentro do projeto"
    - cmd: "./run.sh --gauntlet --only fs_arbitrary"
      timeout: 300
      esperado: "fase nova (GAUNTLET-FS-ARBITRARY-01) PASS -- glob/search/list/read em path fora da raiz retornam resultado correto; secret bloqueado"
    - cmd: "probe determinístico via ToolRegistry: GlobTool().execute({pattern:'*', path:'/tmp/<fixture>'}, project_root) -> output lista os arquivos do fixture (nao 'Nenhum arquivo encontrado')"
      timeout: 60
      esperado: "glob/search/list fora da raiz retornam conteudo real; dentro da raiz inalterado"

  acceptance_criteria:
    - "glob com path fora da raiz ativa lista os arquivos reais (nao vazio), exibindo caminho util (relativo a base consultada ou absoluto)"
    - "search com path fora da raiz funciona tambem no fallback Python (sem rg/grep), sem ValueError/success=False"
    - "list_files coerente com /cd (base de display segue _ACTIVE_ROOT)"
    - "DENTRO do projeto: saida identica a hoje (regressao zero, gauntlet rapido APROVADO)"
    - "secret path (.ssh/id_rsa) segue bloqueado em todas as 3 tools"
    - "Invariantes 14/14; ruff/acento OK; spec movida para concluidos/"
```

---

**Status:** PENDENTE
**Data criacao:** 2026-06-24
**Origem:** Wave 0 (`dev-journey/07-reports/AUDIT_2026_06_24.md`, secao 2). Bug #1 relatado pelo dono
("limitado a pasta padrao"), confirmado lendo o codigo. Decisao do dono #2: leitura livre no disco todo +
secrets bloqueados.
**Modelo obrigatorio:** claude-opus (sem subagentes; implementação direta)

---

## Contexto do projeto (snapshot -- nao referencia)

> - **ADR-009 (acesso universal)** ja e politica vigente: a Nyx deve ler/operar em qualquer caminho. O
>   `validate_path` (`base.py:182-193`, ONDA-37 NYX-FS-ACCESS-FREE-01) ja implementa isso por DEFAULT
>   (`NYX_SANDBOX_STRICT` desligado) -- libera qualquer pasta, so bloqueia segredos.
> - O bug NAO e permissao. E que os tools de descoberta foram escritos antes da ONDA-37 e ainda **filtram o
>   resultado** contra `project_root`, contradizendo o `validate_path`.
> - `_ACTIVE_ROOT` (base.py) segue o `/cd` (set_active_project_root); o argumento `project_root` passado ao
>   `execute()` e a raiz do boot, imutavel. glob/search usam o segundo -> incoerentes com `/cd` tambem.

---

## Problema

| Tool | validate_path libera fora da raiz? | exibe/retorna resultado fora da raiz? | causa |
|------|:--:|:--:|---|
| `read_file` | sim | sim | le o path validado direto |
| `list_files` | sim | **sim** | linha 44 tem fallback p/ path absoluto (REFERENCIA) |
| `glob` | sim | **nao** | linha 42 `is_relative_to(project)` descarta tudo fora do boot root |
| `search` | sim | **parcial** | rapido (rg/grep) ok; lento (`_search_walk`) quebra em `relative_to(root)` linha 102 |

`glob_tool.py:36-43`:

```python
project = Path(project_root).resolve()            # raiz do BOOT, nao _ACTIVE_ROOT
matches = sorted(
    str(p.relative_to(project))
    for p in root.glob(pattern)
    if p.is_file() and p.resolve().is_relative_to(project)   # <-- filtro que zera fora da raiz
)
```

Sintoma para o usuario: `read_file /etc/hostname` funciona, mas "liste/busque em /outra/pasta" volta vazio
-> a Nyx parece "presa" na pasta padrao.

---

## Causa-raiz

Os discovery tools aplicam um **segundo gate** (filtro `is_relative_to(project_root_do_boot)`) por cima do
gate ja correto do `validate_path`. Esse segundo gate e residuo pre-ONDA-37 e contradiz o ADR-009. Alem
disso usam a raiz do boot em vez da raiz ativa (`_ACTIVE_ROOT`), o que tambem os torna incoerentes apos
`/cd`.

---

## Solucao proposta

1. **glob_tool.py:** remover o filtro `is_relative_to(project)`. Enumerar dentro do `root` ja validado por
   `validate_path`. Exibir cada match relativo a uma **base de display** = `get_active_project_root()` se o
   match estiver dentro dela, senao caminho absoluto (mesmo idioma do `list_files.py:44`).
2. **search.py (`_search_walk`):** trocar `f.relative_to(root)` por display relativo a base ativa com
   fallback absoluto (helper compartilhado), para o fallback Python funcionar fora da raiz.
3. **list_files.py:** alinhar a base de display a `get_active_project_root()` (coerencia com `/cd`); sem
   mudanca observavel no caso comum.
4. **(maior valor)** extrair `display_path(resolved: Path, base: Path | None) -> str` em `base.py` e usar
   nas 3 tools -- fonte unica, impede nova divergencia.

Seguranca inalterada: o bloqueio de secrets vive em `validate_path`/`_is_secret_path`, que continua sendo
chamado primeiro nas 3 tools.

---

## Proof-of-work esperado (runtime real)

```bash
bash scripts/sprint_invariants.sh                       # 14/14 PASS
./run.sh --gauntlet --only rapido                       # APROVADO (regressao zero dentro do projeto)
./run.sh --gauntlet --only fs_arbitrary                 # GAUNTLET-FS-ARBITRARY-01 PASS (depende de 372)
python3 ~/.config/zsh/scripts/validar-acentuacao.py --paths nyx/agent/tools/glob_tool.py nyx/agent/tools/search.py nyx/agent/tools/list_files.py nyx/agent/tools/base.py
/home/andrefarias/.local/bin/ruff check nyx/agent/tools/glob_tool.py nyx/agent/tools/search.py nyx/agent/tools/list_files.py nyx/agent/tools/base.py
# probe: criar /tmp/nyx_fs_probe/{a.py,b.txt}; GlobTool().execute({"pattern":"*","path":"/tmp/nyx_fs_probe"}, PROJECT_ROOT)
#        -> output contem a.py e b.txt (nao "Nenhum arquivo encontrado")
# cleanup: pkill -f "nyx/proxy.py"; pkill -f "ollama serve"; nvidia-smi
```

Idealmente, runtime real (proxy + 3b): pedir a Nyx "liste os arquivos em /etc e me diga quantos sao" e
confirmar que ela usa `glob`/`list_files` e responde com a contagem, sem pedir `/sandbox add`.

---

## Criterio binario de aceite

- [ ] glob fora da raiz retorna os arquivos reais (probe e fase fs_arbitrary)
- [ ] search fora da raiz funciona inclusive sem rg/grep (fallback Python)
- [ ] list_files coerente com /cd
- [ ] regressao zero dentro do projeto (gauntlet rapido APROVADO)
- [ ] secret bloqueado nas 3 tools
- [ ] invariantes 14/14, ruff/acento OK; spec -> concluidos/

---

## Riscos

| Risco | Mitigacao |
|-------|-----------|
| Remover o filtro abre acesso a algo que nao deveria | Nao: o gate de acesso e o `validate_path` (mantido); o filtro removido so afetava DISPLAY de paths ja liberados |
| Quebrar saida dentro do projeto | Base de display = raiz ativa quando o path esta dentro dela -> string identica a hoje; gauntlet rapido cobre |
| `glob('**')` em raiz enorme (ex.: `/`) trava | Manter o cap de 200 matches ja existente (glob_tool.py:47); search ja capa em 100 |
| Symlink apontando para fora | Fora de escopo desta sprint (gate de symlink e do validate_path); registrar achado se surgir |

---

*"Dois porteiros checando o mesmo cracha, e um deles barra quem o outro ja deixou entrar." -- anonimo*
