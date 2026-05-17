# SPRINT DEPLOY-01B — Fase Gauntlet install (Docker Ubuntu 22.04) + README seção instalação

## 0. SPEC (machine-readable)

```yaml
sprint:
  id: DEPLOY-01B
  title: "Teste Docker Ubuntu 22.04 limpo do install.sh + seção de instalação no README"
  onda: 22
  bloco: 7
  prioridade: ALTA
  tipo: Infra + Docs
  dependencias: [DEPLOY-01A]
  desbloqueia: [DEPLOY-02]

  touches:
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/scripts/gauntlet/nyx_gauntlet.py
      reason: "Adicionar fase 'install' que roda install.sh em container Docker Ubuntu 22.04 limpo"
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/README.md
      reason: "Seção 'Instalação rápida' no topo, com exemplos de uso das flags do install.sh"
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/.gitignore
      reason: "Confirmar que venv/, logs/, .env já estão ignorados (não adicionar se já estão)"

  creates: []
  removes: []

  n_to_n_pairs:
    - descricao: "Flags documentadas no README devem casar com flags implementadas em install.sh"
      paths:
        - /home/andrefarias/Desenvolvimento/Nyx-Code/install.sh
        - /home/andrefarias/Desenvolvimento/Nyx-Code/README.md

  forbidden:
    - "Modificar install.sh (escopo é DEPLOY-01A, já concluída)"
    - "Adicionar fase Gauntlet que não roda contra Docker real (mock = violação ADR-010)"
    - "Emoji no README ou na fase Gauntlet"
    - "Menção a IA em README/fase/commits"
    - "Duplicar documentação de instalação em múltiplos READMEs"
    - "Alterar .gitignore adicionando entradas que já existem"
    - "Executar docker build sem imagem base oficial ubuntu:22.04"
    - "Hardcode de path absoluto da máquina de desenvolvimento no Dockerfile ou fase"

  tests:
    - cmd: "./run.sh --gauntlet --only install"
      timeout: 900
      deve_passar: true
      nota: "Sobe container Ubuntu 22.04, copia repo, roda install.sh, valida smoke"
    - cmd: "grep -c 'install.sh' README.md"
      deve_passar: ">= 3 ocorrências (sinal de seção de instalação presente)"
    - cmd: "./run.sh --gauntlet --only rapido"
      timeout: 300
      deve_passar: true

  acceptance_criteria:
    - "Fase 'install' existe em scripts/gauntlet/nyx_gauntlet.py e roda Docker Ubuntu 22.04 real"
    - "Fase instala docker se ausente ou pula com mensagem clara (não quebrar gauntlet rapido)"
    - "README.md tem seção '## Instalação rápida' no topo antes de seções técnicas"
    - "README lista 4 flags: --no-vision, --no-kitty, --dev, --dry-run"
    - "README menciona distros testadas (Ubuntu 22.04 no Docker + distros do pkg manager)"
    - ".gitignore contém venv/, logs/, .env (confirmar, não duplicar)"
    - "Gauntlet install passa 100% em Docker limpo"
    - "Gauntlet rapido continua passando 100%"
    - "Acentuação PT-BR correta no README"
```

---

**Status:** PENDENTE
**Data criação:** 2026-04-19
**Origem:** divisão de DEPLOY-01. 01A entregou script local; 01B entrega validação Docker + docs.
**Modelo obrigatório:** claude-opus-4-7 (sem subagentes)

---

## Contexto do projeto (snapshot — não referência)

> **ADRs relevantes:**
> - ADR-001 Local First.
> - ADR-004 Zero Emojis.
> - ADR-005 Anonimato.
> - ADR-006 PT-BR.
> - ADR-010 Zero Mocks: fase Docker roda container real, não mock.
> - ADR-013 Integração Obrigatória.
> - ADR-014 Testes via Gauntlet.
> - ADR-020 Testes via run.sh.
>
> **Estado do sistema:**
> - Onda 22, Bloco 7.
> - DEPLOY-01A concluída — `install.sh` existe e é idempotente.
> - Gauntlet tem fases em `scripts/gauntlet/` (reutilizar padrão).
> - README.md existe; precisa de seção de instalação no topo.

---

## Problema

DEPLOY-01A entregou o script, mas:

1. Ninguém validou em VM limpa. Podemos ter dependências implícitas da máquina do dev.
2. Usuário novo abre o repo e não sabe que `install.sh` existe; README não documenta.

---

## Solução proposta

Dois produtos:

1. **Fase Gauntlet `install`** — sobe container Docker `ubuntu:22.04`, copia o repo, roda `install.sh --no-vision --no-kitty` (para caber no runner), valida smoke final.
2. **Seção "Instalação rápida" no README.md** — topo, antes de seções técnicas, com exemplos de uso e distros testadas.

---

## Arquivos alvo (paths absolutos)

### `/home/andrefarias/Desenvolvimento/Nyx-Code/scripts/gauntlet/nyx_gauntlet.py`

**Antes (conceitual):**
```python
PHASES = {
    "rapido": [...],
    "tui": [...],
    ...
}
```

**Depois (conceitual):**
```python
PHASES = {
    "rapido": [...],
    "tui": [...],
    "install": [
        PhaseStep(
            name="docker-available",
            run=_check_docker_available,
        ),
        PhaseStep(
            name="install-sh-in-ubuntu-22-04",
            run=_run_install_in_docker,
        ),
    ],
    ...
}

def _check_docker_available() -> PhaseResult:
    if shutil.which("docker") is None:
        return PhaseResult.skip("docker não disponível — fase install requer docker")
    # ... verificar daemon rodando
    return PhaseResult.ok()

def _run_install_in_docker() -> PhaseResult:
    # Roda:
    # docker run --rm -v $REPO:/app -w /app ubuntu:22.04 bash -c \
    #   "apt-get update && apt-get install -y curl python3 python3-venv && \
    #    ./install.sh --no-vision --no-kitty"
    # Valida exit 0 e smoke final.
    ...
```

**Mudanças:**

- Nova fase `install` no dicionário `PHASES`.
- Helper `_check_docker_available` — SKIP se docker ausente, não FAIL (não bloqueia gauntlet rapido).
- Helper `_run_install_in_docker` — roda container real, valida exit 0.
- Timeout generoso (até 900s para `pip install` + `ollama pull`).

### `/home/andrefarias/Desenvolvimento/Nyx-Code/README.md`

**Antes (conceitual):**
```markdown
# Nyx-Code

(seção atual — técnica, arquitetura, ADRs)
```

**Depois (conceitual):**
```markdown
# Nyx-Code

Agente de código local, 100% offline, Ollama + qwen3:4b.

## Instalação rápida

```bash
git clone <repo> Nyx-Code && cd Nyx-Code
./install.sh                   # instalação completa
./install.sh --no-vision       # sem moondream (sem visão)
./install.sh --no-kitty        # não pergunta sobre kitty
./install.sh --dev             # inclui requirements-dev
./install.sh --dry-run         # mostra o que faria, sem executar
./run.sh                       # sobe o agente
```

**Distros testadas:**
- Ubuntu 22.04 (via Gauntlet fase `install` em Docker)
- Fedora 39 (manual, via `dnf`)
- Arch Linux (manual, via `pacman`)
- openSUSE (via `zypper`)

---

(resto do README técnico atual, sem alteração)
```

**Mudanças:**

- Nova seção `## Instalação rápida` logo abaixo do H1.
- Lista 5 exemplos de invocação.
- Lista distros testadas (honesta: só Ubuntu 22.04 está automatizado; resto é manual).
- Acentuação PT-BR correta.

### `/home/andrefarias/Desenvolvimento/Nyx-Code/.gitignore`

**Antes/Depois:**

- Abrir, verificar presença de `venv/`, `logs/`, `.env`.
- Se presente: não tocar.
- Se ausente: adicionar (raro — o repo já tem gitignore robusto).

---

## Diff esperado (resumo)

```
+ 0 arquivos criados
~ 2-3 arquivos modificados (scripts/gauntlet/nyx_gauntlet.py, README.md, .gitignore opcional)
- 0 arquivos removidos
+ ~80 linhas líquidas (fase) + ~30 (README)
```

---

## Comandos de verificação (literais, copy-paste)

```bash
cd /home/andrefarias/Desenvolvimento/Nyx-Code

# 1. Lint
python -m ruff check scripts/gauntlet/

# 2. Fase existe no dicionário
python -c "from scripts.gauntlet.nyx_gauntlet import PHASES; assert 'install' in PHASES; print('ok')"

# 3. Gauntlet install (demorado — 5 a 15 min dependendo da rede)
./run.sh --gauntlet --only install

# 4. Gauntlet rapido segue verde
./run.sh --gauntlet --only rapido

# 5. README tem seção
grep -n "^## Instalação rápida" README.md
grep -c "install.sh" README.md
# esperado: >= 3

# 6. .gitignore sem duplicatas
sort -u .gitignore > /tmp/gi_sorted
diff .gitignore /tmp/gi_sorted | head
# esperado: vazio (ou diff só de comentários)

# 7. install.sh NÃO foi tocado (escopo 01A)
git diff HEAD~1 HEAD -- install.sh
# esperado: vazio
```

---

## Critério binário de aceite

- [ ] Fase `install` adicionada em `scripts/gauntlet/nyx_gauntlet.py`
- [ ] Fase SKIP elegante se docker ausente (não FAIL)
- [ ] Fase roda `ubuntu:22.04` real (ADR-010, zero mock)
- [ ] `./run.sh --gauntlet --only install` passa em máquina com docker
- [ ] `./run.sh --gauntlet --only rapido` continua passando
- [ ] README.md tem `## Instalação rápida` no topo
- [ ] README lista 4 flags com explicação em PT-BR
- [ ] README lista distros testadas (honesto sobre automação)
- [ ] .gitignore cobre venv/, logs/, .env (sem duplicatas novas)
- [ ] `install.sh` NÃO modificado (diff vazio)
- [ ] `ruff` sem reclamações
- [ ] Zero emoji, zero menção a IA, acentuação PT-BR correta
- [ ] Commit: `feat: fase Gauntlet install + seção instalação no README (DEPLOY-01B)`

---

## Guardrails anti-engodo

**NÃO marque como concluída se:**

- Fase "install" é um `return True` mockado (viola ADR-010).
- Fase roda `bash install.sh` direto na máquina host (não em Docker limpo).
- README documenta flags que não existem em install.sh (quebra N-para-N).
- IA modificou `install.sh` (escopo é 01A).
- .gitignore teve entradas adicionadas que já estavam lá.

---

## Catálogo de gambiarras proibidas

Aplicáveis especialmente:

- #7 **Test só passa com fixture fake**: fase install que "simula" Docker. Proibido.
- #9 **Condicional de skip**: `if os.environ.get("CI"): return True`. Proibido.
- #8 **Grep que não detecta o bug**: `grep "OK"` no output do install.sh quando o container falha silenciosamente. Verificar exit code.
- #4 **Documentação como implementação**: README diz "testado em Ubuntu 22.04" sem que exista a fase Gauntlet correspondente.

---

## Proof-of-work obrigatório

Incluir no relatório:

- `cat /tmp/inv_before.txt | tail -10` + `cat /tmp/inv_after.txt | tail -10` + diff.
- Output completo de `./run.sh --gauntlet --only install` (incluindo `docker run` e saída do install.sh).
- Output de `./run.sh --gauntlet --only rapido`.
- `head -40 README.md` mostrando seção de instalação.
- `git show --stat HEAD`.

---

## Gambiarras específicas desta sprint

1. **Mock de Docker**: fase "checa se docker existe" e retorna OK sem rodar container. Proibido — precisa `docker run` real.
2. **Imagem base custom do dev**: usar `ubuntu:latest` ou imagem local. Proibido — versão pinada `ubuntu:22.04` para reprodutibilidade.
3. **Pular `ollama pull qwen3:4b`**: install dentro do container não precisa do Ollama completo; mas se o install.sh executa FASE 4, ela deve rodar (ou usar `--no-vision` não ajuda aqui — qwen3 é obrigatório). Alternativa: passar env var `NYX_INSTALL_SKIP_PULL=1` se for preciso (documentar) ou aceitar que a fase é longa.
4. **README gigante**: adicionar seções não pedidas "já que estou aqui". Escopo é só "## Instalação rápida".
5. **Tocar install.sh**: "achei um bug, já fiz o fix". Proibido — abrir nova sprint (nenhum débito fica para trás).
6. **Timeout ausente**: fase pode rodar 15 min. Setar `timeout=900` explicitamente na PhaseStep.

---

## Validação humana (checklist do usuário)

```bash
cd /home/andrefarias/Desenvolvimento/Nyx-Code

git log --oneline -1
git show --stat HEAD

head -50 README.md
./run.sh --gauntlet --only install
./run.sh --gauntlet --only rapido

# install.sh não mexeu:
git diff HEAD~1 HEAD -- install.sh
# esperado: vazio

ls dev-journey/06-sprints/concluidos/SPRINT_DEPLOY_01B.md
! ls dev-journey/06-sprints/producao/SPRINT_DEPLOY_01B.md 2>/dev/null
```

---

## Riscos

| Risco | Mitigação |
|-------|-----------|
| Máquina de dev sem docker → gauntlet rapido quebra | Fase SKIP elegante em ausência de docker; não FAIL |
| `ollama pull qwen3:4b` leva 15 min dentro do container | Timeout 900s + considerar `--no-vision` no install dentro do container (qwen3 ainda obrigatório) |
| README fica grande demais | Manter só "Instalação rápida"; detalhes em docs dedicadas |
| Rede do Docker bloqueada em CI | Fase SKIP com mensagem clara se `curl https://ollama.ai` não responde |
| Flags do install.sh renomeadas após 01A | N-para-N: README cita flags; revisar antes do merge |

---

*"O que não pode ser reproduzido num container limpo, não está instalável." -- adaptado do folclore DevOps*
