## 0. SPEC (machine-readable)

```yaml
sprint:
  id: ANALYZE-VALIDATE-PATH-01
  numero: 425
  title: "analyze passa a resolver o path por validate_path -- fecha o furo de sandbox estrito e o bloqueio de segredos (.ssh/.gnupg/.aws)"
  onda: 48
  prioridade: ALTA
  tipo: Bugfix
  dependencias: []
  desbloqueia: []
  absorve: []

  touches:
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/agent/tools/analyze_tool.py
      reason: "trocar a resolução manual de path (linha 35) por validate_path(file_path, project_root) com try/except ValueError, no mesmo padrão de read_file.py:34-37 -- passa a honrar o bloqueio de segredos (base.py:211-216) e o modo NYX_SANDBOX_STRICT (base.py:207-226), além de expandir ~ como as demais tools de FS"
      linhas_alvo: "9 (import de base), 30-37 (assinatura execute + resolução + guard de existência)"
  creates: []
  removes: []

  forbidden:
    - "Adicionar emoji"
    - "Usar 'print()' fora de cli.py/output.py"
    - "Mencao a IA proprietaria (Claude/Anthropic/GPT/Gemini/Copilot)"  # noqa-anonimato
    - "Tocar nyx/agent/tools/base.py (validate_path/_is_secret_path/_sandbox_strict ja existem e estao corretos)"
    - "Tocar nyx/agent/permissions.py (o auto_approve de analyze e comportamento intencional; a defesa e no path, não na permissao)"
    - "Alterar a logica de analise (_analyze_python/_analyze_generic) -- so a resolucao do path muda"
    - "Alterar as demais tools de FS (read_file/glob/list_files/search ja usam validate_path)"

  tests:
    - cmd: "/home/andrefarias/.local/bin/ruff check nyx/agent/tools/analyze_tool.py"
      deve_passar: true
    - cmd: "bash scripts/sprint_invariants.sh"
      deve_passar: true
    - cmd: "./run.sh --smoke"
      deve_passar: true

  acceptance_criteria:
    - "AC1 (segredo bloqueado): analyze com um path de segredo (.ssh/.gnupg/.aws ou nome de chave privada como id_rsa) devolve ActionResult(success=False) com a mensagem 'Acesso negado por segurança...' de base.py:213-216, SEM ler o arquivo -- mesmo no modo de acesso livre (default)"
    - "AC2 (sandbox estrito): com NYX_SANDBOX_STRICT=1, analyze de um path fora dos roots devolve ActionResult(success=False) com 'Fora dos projetos permitidos... /sandbox add' (base.py:223-226), SEM ler -- analyze deixa de ser uma porta de leitura fora do sandbox"
    - "AC3 (expansao de ~): analyze com file_path começando por '~' resolve via expanduser (base.py:184), igual as demais tools de FS -- '~/.ssh/id_rsa' expande E e bloqueado por segredo, não vira '<root>/~/.ssh/...'"
    - "AC4 (happy-path preservado): analyze de um .py legítimo dentro do projeto continua produzindo o mesmo relatório (imports/classes/funções/linhas); analyze de arquivo inexistente continua devolvendo 'Arquivo não encontrado' com files_read populado"
    - "AC5 (paridade de padrão): a resolução de analyze_tool.py fica byte-equivalente ao contrato de read_file.py:34-37 (path = validate_path(...); except ValueError -> success=False, error=str(e))"
    - "ruff limpo, acentuação rc=0, invariantes FAIL_AFTER <= FAIL_BEFORE, smoke boot ok"
```

---

# Sprint ANALYZE-VALIDATE-PATH-01 — analyze passa a resolver path por validate_path

**Status:** PENDENTE
**Data criação:** 2026-07-12
**Origem:** auditoria de prontidão 2026-07-12 (achado verificado adversarialmente, evidência file:line)

---

## Contexto do projeto (snapshot — não referência)

> **Missão (calibração):** o Nyx-Code faz o pior LLM local (qwen 3b) na pior máquina possível parecer o Claude Code offline. Robustez e segurança pertencem à INFRA, não ao modelo (ADR-032/033/034). O usuário-alvo é leigo e sem hardware bom: uma injeção de prompt que faça a Nyx ler `~/.ssh/id_rsa` não pode depender de o modelo "se comportar" — a barreira tem de estar na camada de tools. <!-- noqa-anonimato -->
>
> **ADRs/invariantes relevantes (inline):**
> - **NYX-FS-ACCESS-FREE-01 (ONDA-37):** por default o acesso ao FS é livre; a defesa em profundidade e que segredos criptográficos notórios (`.ssh`/`.gnupg`/`.aws` e nomes de chave privada) ficam bloqueados MESMO no acesso livre (`nyx/agent/tools/base.py:52-60`, `211-216`). O modo estrito `NYX_SANDBOX_STRICT=1` restaura o bloqueio por raiz (`base.py:207-226`).
> - **ADR-032/033 (a infra enforça, não confia):** a garantia de segurança não é do modelo; é do `validate_path`. Toda tool de leitura de FS tem de passar por ele.
>
> **Estado (2026-07-12):** `qwen2.5-coder:3b`. Ports: Ollama `11435`, proxy `11436`. Tools de FS que JÁ passam por `validate_path`: `read_file.py:35`, `glob_tool.py:43`, `list_files.py:41`, `search.py:51`. A única exceção é `analyze`.

---

## Problema

**Achado (auditoria 2026-07-12, severidade ALTA):** `nyx/agent/tools/analyze_tool.py:35` resolve o path na mão, fora do `validate_path`:

```python
path = Path(file_path) if file_path.startswith("/") else Path(project_root) / file_path
```

Todas as outras tools de FS delegam ao `validate_path` (`read_file.py:35`, `glob_tool.py:43`, `list_files.py:41`, `search.py:51`). O `analyze` não. Isso **pula duas barreiras** que só existem dentro do `validate_path`:

1. **O bloqueio de segredos** (`base.py:211-216`): `if _is_secret_path(resolved): raise ValueError("Acesso negado por segurança...")`. Sem passar por lá, `analyze file_path=~/.ssh/id_rsa` (ou path absoluto `/home/user/.ssh/id_rsa`) lê o arquivo — a garantia da ONDA-37 (defesa em profundidade contra leitura por injeção) fica furada.
2. **O modo estrito** `NYX_SANDBOX_STRICT=1` (`base.py:207-226`): fora do modo estrito, o acesso é livre de qualquer jeito; mas no modo estrito as demais tools bloqueiam paths fora dos roots com a sugestão de `/sandbox add`. O `analyze` não bloqueia — vira uma porta de leitura fora do sandbox.

**Agravante:** `analyze` está no `auto_approve` (`nyx/agent/permissions.py:38`, e o `action_type` é `READ_FILE`, também auto), então roda **sem prompt de confirmação**. A leitura acontece silenciosamente.

**Escopo do dano (honestidade):** a exposição é limitada — `analyze` devolve só métricas e nomes (linhas, imports, classes, funções via AST), não o conteúdo bruto do arquivo. Mas (a) a garantia explícita "leitura por injeção não alcança `~/.ssh`" está furada, e (b) para arquivos de código-fonte de credenciais/config a lista de nomes de funções/classes já é vazamento estrutural.

**Bônus de correção (divergência do briefing — ver Causa-raiz):** o path atual também não expande `~`. Ao adotar `validate_path`, o `~` passa a expandir (`base.py:184`, `expanduser`), alinhando `analyze` ao comportamento das demais tools.

---

## Causa-raiz (verificada no código real)

Investigação linha a linha em 2026-07-12; as evidências do briefing conferem, com uma ressalva:

- `analyze_tool.py:35` — resolução manual confirmada, **exatamente na linha 35**, texto idêntico ao briefing.
- `read_file.py:34-37` — padrão de referência confirmado: `try: path = validate_path(file_path, project_root) except ValueError as e: return ActionResult(success=False, error=str(e))`.
- `base.py:157` `def validate_path`, `base.py:56-60` `_is_secret_path` (intersecta `.parts` com `{.ssh,.gnupg,.aws}` OU `resolved.name in {id_rsa,id_ed25519,id_dsa,id_ecdsa}`), `base.py:211-216` bloqueio de segredo, `base.py:207/223-226` modo estrito — todos confirmados nas linhas citadas pelo briefing.
- `glob_tool.py:43`, `list_files.py:41`, `search.py:51` — uso de `validate_path` confirmado nas linhas exatas.
- `permissions.py` — o briefing referiu `permissions.py:38`; o caminho real e `nyx/agent/permissions.py` (não `nyx/agent/services/permissions.py`), e a linha 38 de fato lista `"analyze"` dentro de `auto_approve`. **Divergência apenas de caminho, não de fato.**

**Divergência material do briefing:** o briefing afirma "o path também não expande `~` (FS-TILDE-EXPAND-01 não se aplica aqui)". Isso é meia-verdade: hoje o `analyze` de fato **não** expande `~` (usa `Path(file_path)` cru). Mas o fix (adotar `validate_path`) **passa a expandir `~`** de graça, porque `validate_path` faz `Path(file_path.strip()).expanduser()` na `base.py:184`. Ou seja, FS-TILDE-EXPAND-01 **passa a se aplicar** após o fix — é um ganho de consistência, registrado como AC3, não um efeito colateral indesejado (as 4 outras tools de FS já se comportam assim).

---

## Solução proposta

Uma única correção cirúrgica em `analyze_tool.py`, copiando o contrato já usado por `read_file`:

1. Importar `validate_path` de `nyx.agent.tools.base` (junto de `RegisteredTool, ToolDef`).
2. Manter o guard de `file_path` vazio (o `validate_path` sobre string vazia resolveria para o root; o guard explícito dá mensagem melhor ao modelo 3b).
3. Trocar a resolução manual da linha 35 por `validate_path(file_path, project_root)` dentro de `try/except ValueError`, devolvendo `ActionResult(success=False, error=str(e))` no erro — idêntico a `read_file.py:34-37`.

Nada mais muda: `_analyze_python`, `_analyze_generic`, o guard de existência e o `files_read` seguem intactos (o `files_read` passa a usar o `path` resolvido, o que é correto).

---

## Arquivos alvo (paths absolutos)

### `/home/andrefarias/Desenvolvimento/Nyx-Code/nyx/agent/tools/analyze_tool.py`

#### Edit 1 — importar validate_path

# Localização: linha 11 (import de base)
**Antes:**
```python
from nyx.agent.tools.base import RegisteredTool, ToolDef
```
**Depois:**
```python
from nyx.agent.tools.base import RegisteredTool, ToolDef, validate_path
```

#### Edit 2 — resolver o path por validate_path (mesmo contrato de read_file.py:34-37)

# Localização: dentro de execute(), a resolução manual (linha 35), logo após o guard de file_path vazio
**Antes:**
```python
        file_path = str(params.get("file_path", "")).strip()
        if not file_path:
            return ActionResult(success=False, error="file_path vazio")

        path = Path(file_path) if file_path.startswith("/") else Path(project_root) / file_path
        if not path.exists():
            return ActionResult(success=False, error=f"Arquivo não encontrado: {file_path}", files_read=[str(path)])
```
**Depois:**
```python
        file_path = str(params.get("file_path", "")).strip()
        if not file_path:
            return ActionResult(success=False, error="file_path vazio")

        # ANALYZE-VALIDATE-PATH-01: resolver via validate_path (igual a read_file/
        # glob/list_files/search). Antes, a resolução manual pulava o bloqueio de
        # segredos (.ssh/.gnupg/.aws) e o modo NYX_SANDBOX_STRICT -- analyze estava
        # em auto_approve, então lia sem prompt fora do sandbox. validate_path
        # também expande ~ (base.py). Defesa em profundidade NYX-FS-ACCESS-FREE-01.
        try:
            path = validate_path(file_path, project_root)
        except ValueError as e:
            return ActionResult(success=False, error=str(e))

        if not path.exists():
            return ActionResult(success=False, error=f"Arquivo não encontrado: {file_path}", files_read=[str(path)])
```

> Nota: com a importação de `validate_path`, o `Path` do módulo (`from pathlib import Path`, linha 6) continua em uso pelos type hints e por `path.suffix`/`path.name` nos métodos de análise — não remover o import de `Path`.

---

## Diff esperado (resumo)

```
~ 1 arquivo modificado (nyx/agent/tools/analyze_tool.py)
+ ~7 linhas líquidas (import estendido + try/except substituindo 1 linha)
```

Sem aritmética de extração: esta sprint não tem meta `arquivo < NNNL`. O único número relevante é o net-add (~7L) num único arquivo; `analyze_tool.py` segue com ~130L.

---

## Comandos de verificação (literais, copy-paste)

```bash
cd /home/andrefarias/Desenvolvimento/Nyx-Code

# 1. Estatica + acentuacao (ruff via binario direto -- ver BRIEF)
/home/andrefarias/.local/bin/ruff check nyx/agent/tools/analyze_tool.py
python3 ~/.config/zsh/scripts/validar-acentuacao.py --paths nyx/agent/tools/analyze_tool.py

# 2. Confirmar a hipotese das ancoras (linhas podem ter deslizado -- reconferir):
rg -n "validate_path|Path\(file_path\)|Path\(project_root\)" nyx/agent/tools/analyze_tool.py
rg -n "validate_path" nyx/agent/tools/read_file.py nyx/agent/tools/glob_tool.py nyx/agent/tools/list_files.py nyx/agent/tools/search.py

# 3. PROOF RUNTIME-REAL sem GPU (analyze e Python puro: ast + read_text, ZERO LLM).
#    Prova AC1 (segredo), AC2 (estrito), AC3 (~ expande e bloqueia), AC4 (happy-path).
./venv/bin/python - <<'PY'
import os, tempfile
from pathlib import Path
from nyx.agent.tools.analyze_tool import AnalyzeTool

t = AnalyzeTool()
root = tempfile.mkdtemp()

# AC4 -- happy path: .py legitimo dentro do root
py = Path(root) / "exemplo.py"
py.write_text("import os\n\nclass A:\n    def m(self):\n        pass\n", encoding="utf-8")
r_ok = t.execute({"file_path": "exemplo.py"}, root)
assert r_ok.success, r_ok
assert "Análise de exemplo.py" in (r_ok.output or ""), r_ok
print("AC4 happy-path OK:", r_ok.output.splitlines()[0])

# AC1 -- segredo bloqueado mesmo no acesso livre (default). Path absoluto sob .ssh.
fake_ssh = Path(tempfile.mkdtemp()) / ".ssh"
fake_ssh.mkdir()
(fake_ssh / "id_rsa").write_text("PRIVATE", encoding="utf-8")
r_secret = t.execute({"file_path": str(fake_ssh / "id_rsa")}, root)
assert not r_secret.success, r_secret
assert "Acesso negado por segurança" in (r_secret.error or ""), r_secret
print("AC1 segredo bloqueado OK:", r_secret.error)

# AC3 -- '~' expande via validate_path (antes ficava literal '<root>/~/...').
#        Aponta para ~/.ssh/id_rsa: expande E cai no bloqueio de segredo.
r_tilde = t.execute({"file_path": "~/.ssh/id_rsa"}, root)
assert not r_tilde.success, r_tilde
assert "Acesso negado por segurança" in (r_tilde.error or ""), r_tilde
print("AC3 til expande e bloqueia OK:", r_tilde.error)

# AC2 -- modo estrito: path fora dos roots e recusado com sugestao /sandbox add.
os.environ["NYX_SANDBOX_STRICT"] = "1"
out = Path(tempfile.mkdtemp()) / "fora.py"
out.write_text("x = 1\n", encoding="utf-8")
r_strict = t.execute({"file_path": str(out)}, root)
os.environ.pop("NYX_SANDBOX_STRICT", None)
assert not r_strict.success, r_strict
assert "Fora dos projetos permitidos" in (r_strict.error or ""), r_strict
assert "/sandbox add" in (r_strict.error or ""), r_strict
print("AC2 sandbox estrito OK:", r_strict.error)

print("TODOS OS ACs RUNTIME OK (sem GPU)")
PY

# 4. Regressao rapida: as demais tools de FS seguem intactas
bash scripts/sprint_invariants.sh   # esperado PASS 14/14 FAIL 0
./run.sh --smoke                     # esperado 'boot ok' exit 0
```

> Nota GPU: os passos 1-3 rodam SEM Ollama/GPU (analyze e Python puro). O smoke boot (passo 4) sobe a stack mínima; se houver contenção de GPU, executar só quando `pgrep -af "Luna.*driver|valida_sprint"` estiver vazio.

---

## Proof-of-work esperado

```bash
bash scripts/sprint_invariants.sh > /tmp/inv_before.txt 2>&1
FAIL_BEFORE=$(grep -c "^\[FAIL\]" /tmp/inv_before.txt)
# implementar
bash scripts/sprint_invariants.sh > /tmp/inv_after.txt 2>&1
FAIL_AFTER=$(grep -c "^\[FAIL\]" /tmp/inv_after.txt)
diff /tmp/inv_before.txt /tmp/inv_after.txt
```
Baseline esperado: `FAIL_BEFORE = 0`, `FAIL_AFTER <= 0`. Colar no proof:
- `inv_before`/`inv_after` (tail) + `diff`.
- Output completo do proof runtime-real (passo 3): os 4 ACs impressos, terminando em `TODOS OS ACs RUNTIME OK (sem GPU)`.
- `rg` do passo 2 (ancoras confirmadas: `validate_path` presente em analyze, ausente o `Path(file_path)`/`Path(project_root)` manual).
- `ruff check` limpo + `validar-acentuacao` rc=0.
- `git --no-pager diff --stat` (1 arquivo, ~7L líquidas).
- `./run.sh --smoke` imprimindo `boot ok`.

**Proof DEFERIDO para GPU exclusiva** (como as specs 403/407): `./run.sh --gauntlet --only rapido` (100%). O gauntlet não exercita `analyze` diretamente e exige GPU exclusiva no RTX 3050 4GB (achado de flake do BRIEF); os ACs desta sprint são 100% cobertos pelo proof runtime-real sem GPU do passo 3. Rodar o gauntlet só quando a GPU estiver livre; não é bloqueante para o mérito da sprint.

---

## Critério binário de aceite (IA executora)

- [ ] `analyze_tool.py` importa `validate_path` de `nyx.agent.tools.base`
- [ ] Resolução manual da linha 35 substituída por `validate_path(file_path, project_root)` dentro de `try/except ValueError -> ActionResult(success=False, error=str(e))`
- [ ] Proof runtime-real colado (passo 3): AC1/AC2/AC3/AC4 todos impressos como OK, sem GPU
- [ ] `_analyze_python`/`_analyze_generic`/guard de existência/`files_read` intactos (happy-path byte-equivalente)
- [ ] `base.py` e `permissions.py` NÃO tocados
- [ ] `ruff` limpo, acentuação rc=0, `FAIL_AFTER <= FAIL_BEFORE`, smoke boot ok
- [ ] `SPRINT_ORDER_MASTER.md` marca 425 CONCLUIDA; spec movida para `concluidos/`
- [ ] NÃO commitar; NÃO tocar Checkpoint.md

Se algo falhar: `[SPRINT 425] BLOQUEADA: <motivo 1 linha>`.

---

## Guardrails anti-engodo (obrigatórios)

NÃO marcar concluída se:
- A resolução ficou com o `Path(file_path) if file_path.startswith("/") else ...` manual (o núcleo do fix é DELEGAR ao `validate_path`).
- O bloqueio de segredo não dispara no proof (AC1) — significa que o `validate_path` não está no caminho.
- O happy-path mudou (analyze de .py legítimo deve produzir o mesmo relatório).
- Tocou `base.py` ou `permissions.py` (fora de escopo — a defesa correta é o path, não a permissão nem a assinatura do validador).
- Removeu o guard de `file_path` vazio ou o import de `Path` (ainda usado por `path.suffix`/`path.name`).
- Proof runtime-real não colado, ou algum AC não imprimiu OK.

---

## Riscos e não-objetivos

| Risco / não-objetivo | Decisão |
|-------|-----------|
| Endurecer o `_is_secret_path` (cobrir `.kube`, `.docker/config.json`, `.netrc`, tokens de nuvem) | **NÃO-OBJETIVO.** É melhoria da lista de segredos em `base.py`, ortogonal a esta sprint. Se o dono quiser ampliar a cobertura, registrar `INFRA-SECRET-PATHS-EXPAND-01` (anti-débito: `feedback_nenhum_debito`). |
| Auditar se OUTRAS tools (fora de FS) resolvem path na mão | Fora de escopo aqui. A auditoria 2026-07-12 apontou só `analyze`; as 4 tools de FS já usam `validate_path` (confirmado). Se surgir outra, sprint própria. |
| Tirar `analyze` do `auto_approve` | Rejeitado: a defesa correta é o `validate_path` (barreira no path), não transformar leitura de análise em ação que pede prompt (pioraria a UX do usuário leigo sem fechar o furo de verdade). |

---

## Fora de escopo (anti-débito)

Nenhum mecanismo adicional identificado nesta investigação. O briefing traz um único achado, de um único mecanismo (resolução de path sem `validate_path`), fechado por completo pelos ACs acima. A única observação registrada é a divergência de tilde (ver Causa-raiz), já absorvida como AC3.

---

## Referências

- BRIEF: `/home/andrefarias/Desenvolvimento/Nyx-Code/VALIDATOR_BRIEF.md`
- Padrão de referência: `nyx/agent/tools/read_file.py:34-37` (validate_path + except ValueError)
- Barreira de segurança: `nyx/agent/tools/base.py:56-60` (`_is_secret_path`), `base.py:207-226` (acesso livre + bloqueio de segredo + modo estrito)
- Invariante de origem: NYX-FS-ACCESS-FREE-01 (ONDA-37, defesa em profundidade)
- Origem do achado: auditoria de prontidão 2026-07-12 (verificado adversarialmente)

---

*"A garantia de segurança não pode depender do modelo se comportar; ela mora na infra. Uma tool de leitura que não passa pelo validate_path é uma porta que ninguém tranca." -- princípio ADR-032/033*
