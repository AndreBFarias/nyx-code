# SPRINT PROJECT-ROOTS-MULTI-01 — Aceitar múltiplos project roots em runtime

## 0. SPEC

```yaml
sprint:
  id: PROJECT-ROOTS-MULTI-01
  title: "Nyx aceita lista de project roots permitidos + /sandbox add/list/remove + /cd <path>"
  onda: 24
  bloco: 24.8 Escopo expandido
  prioridade: ALTA
  tipo: Feature
  dependencias: [AUDIT-01]
  desbloqueia: [uso em projetos multiplos, automacao real]
  origem: "Achado de uso 2026-05-18: usuario tentou ler ~/Desenvolvimento/Protocolo-Mob-Ouroboros/Checkpoint.md via Nyx aberta em Nyx-Code. Preflight bloqueou: 'Fora do projeto Nyx-Code'. Comportamento correto (ADR-009 acesso universal por opt-in), mas inviabiliza projetos complexos que tocam dirs irmaos."

  touches:
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/agent/preflight.py
      reason: "check() aceita lista de allowed_roots em vez de project_root unico"
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/config/settings.py
      reason: "Aceitar NYX_EXTRA_ROOTS (lista CSV) e expor para preflight"
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/cli.py
      reason: "Carregar extra_roots no boot + handler de /sandbox + /cd"
  creates:
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/agent/commands/sandbox.py
      reason: "Slash command /sandbox list/add/remove + /cd <path>"

  forbidden:
    - "Permitir escrita em / ou /etc/ ou /root sem confirmacao explicita"
    - "Persistir extra_roots fora de ~/.nyx/config.toml (precisa ser opt-in)"
    - "Quebrar preflight default (project_root atual continua sempre allowed)"

  tests:
    - cmd: "NYX_EXTRA_ROOTS=/tmp ./run.sh --smoke"
      timeout: 30
      deve_passar: "boot ok"
    - cmd: "echo '/sandbox list' | ./run.sh --headless --no-resume-prompt"
      timeout: 30
      deve_passar: "Lista roots ativos"

  acceptance_criteria:
    - "Preflight aceita lista de allowed_roots (project_root + extra_roots)"
    - "Env NYX_EXTRA_ROOTS=path1,path2 expande lista no boot"
    - "Slash /sandbox list mostra roots ativos"
    - "Slash /sandbox add <path> adiciona em runtime (somente sessao)"
    - "Slash /sandbox remove <path> remove (project_root nao pode ser removido)"
    - "Slash /cd <path> muda project_root corrente da sessao (Nyx-style)"
    - "Escritas em paths fora de allowed_roots permanecem bloqueadas com erro PT-BR actionable"
    - "Audit grep zero hex/IA externa preservado"
    - "Smoke + invariantes 14/14"
```

---

# Sprint PROJECT-ROOTS-MULTI-01

**Status:** CONCLUIDA (header corrigido em MASTER-CLEANUP-02 2026-05-20)  **original:** PENDENTE (humana ou agente)
**Data criação:** 2026-05-18 (achado de uso real)
**Modelo obrigatório:** claude-opus-4-7

---

## Contexto

Cenario real (2026-05-18 ~05:30): usuario rodou `./run.sh --menu`, configurou aesthetic mecha + entity luna, e tentou via Nyx ler arquivo em `~/Desenvolvimento/Protocolo-Mob-Ouroboros/Checkpoint.md` (projeto irmao). Preflight bloqueou:

```
read_file ─── ERRO · 1ms
Fora do projeto Nyx-Code: '/home/andrefarias/Desenvolvimento/Protocolo-Mob-Ouroboros/Checkpoint.md'.
Para acessar outro projeto, inicie o Nyx la.
```

A mensagem orienta corretamente ("inicie o Nyx la") mas isso inviabiliza:
- Refactor cross-project (ex: extrair lib comum)
- Comparar arquitetura entre 2 projetos
- Mover codigo entre projetos
- Usuario rodar 1 Nyx unica gerenciando diversos projetos

Solucao deve preservar a defesa (escritas/exec sandboxed) MAS oferecer caminhos explicitos de opt-in.

## Solucao proposta

### 1. Preflight aceita lista

`nyx/agent/preflight.py::check(name, args, project_root)`:
```python
def check(name, args, project_root, extra_roots=None):
    allowed = [project_root] + (extra_roots or [])
    path = args.get("file_path") or args.get("path")
    if path:
        target = Path(path).resolve()
        if not any(target.is_relative_to(r) for r in allowed):
            return PreflightResult(
                ok=False,
                errors=[f"Fora dos projetos permitidos: '{path}'. "
                        f"Use /sandbox add <path> para autorizar."],
            )
    return PreflightResult(ok=True)
```

### 2. Env + config

`NYX_EXTRA_ROOTS=/home/.../A,/home/.../B` ou `[extra_roots]` em `~/.nyx/config.toml`:
```toml
extra_roots = ["/home/andrefarias/Desenvolvimento/Protocolo-Mob-Ouroboros"]
```

### 3. Slash commands `/sandbox` + `/cd`

```python
@nyx_command(name="sandbox", aliases=["roots"], category="sistema",
             examples=["/sandbox list", "/sandbox add /tmp", "/sandbox remove /tmp"])
def cmd_sandbox(args, root): ...

@nyx_command(name="cd", category="sistema",
             examples=["/cd ~/Desenvolvimento/Protocolo-Mob-Ouroboros"])
def cmd_cd(args, root):
    """Muda project_root corrente; preserva original em extra_roots."""
```

### 4. UX

- Quando preflight bloquear, sugerir comando exato:
  `Bloqueado: '/X/Y'. Para autorizar: /sandbox add /X`
- Banner mostra count de extras: `Nyx-Code (+2 roots)`.

## Critério binário

- [ ] preflight aceita extra_roots
- [ ] NYX_EXTRA_ROOTS funciona
- [ ] /sandbox + /cd registrados
- [ ] Banner reflete count
- [ ] Mensagem actionable em erro
- [ ] Smoke + invariantes 14/14
- [ ] Sprint movida → concluidos/
- [ ] Commit `feat(PROJECT-ROOTS-MULTI-01): multiplos roots + /sandbox + /cd`

---

*"Sandbox que prende vira gaiola; sandbox com chave vira casa." -- PROJECT-ROOTS-MULTI-01*
