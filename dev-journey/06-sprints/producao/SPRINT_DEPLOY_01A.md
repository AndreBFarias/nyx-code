# SPRINT DEPLOY-01A — install.sh idempotente (script local, sem Docker, sem README)

## 0. SPEC (machine-readable)

```yaml
sprint:
  id: DEPLOY-01A
  title: "install.sh idempotente com 10 fases (local, sem Docker, sem README — fica em 01B)"
  onda: 22
  bloco: 7
  prioridade: ALTA
  tipo: Infra
  dependencias: [VISION-03]
  desbloqueia: [DEPLOY-01B]

  touches: []

  creates:
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/install.sh
      reason: "Script idempotente de instalação local-first, 10 fases, 4 flags, detecção de distro"

  removes: []

  n_to_n_pairs: []

  forbidden:
    - "Assumir root/sudo sem confirmar (usar sudo só em apt/pacman/dnf/zypper)"
    - "Baixar binários sem verificar origem (Ollama: script oficial apenas)"
    - "Emoji na saída"
    - "Menção a IA em mensagens ou comentários"
    - "--dry-run executar comandos destrutivos (install, pull, chmod)"
    - "Segunda execução reinstalar algo que já está instalado (quebra idempotência)"
    - "Adicionar README ou seção nele (escopo de DEPLOY-01B)"
    - "Adicionar fase install ao Gauntlet (escopo de DEPLOY-01B)"
    - "Path absoluto hardcoded (usar variáveis relativas ao script)"
  tests:
    - cmd: "bash -n install.sh && echo 'sintaxe OK'"
      deve_passar: true
    - cmd: "test -x install.sh"
      deve_passar: true
    - cmd: "./install.sh --help"
      deve_passar: true
    - cmd: "./install.sh --no-vision --no-kitty --dry-run"
      deve_passar: true
      nota: "dry-run não escreve nada; saída lista SKIP/OK esperados"
    - cmd: "./install.sh && ./install.sh"
      deve_passar: true
      nota: "Segunda execução: todas as fases SKIP (exceto chmod e smoke que sempre rodam)"

  acceptance_criteria:
    - "install.sh existe, executável, sintaxe válida (bash -n)"
    - "Flags: --no-vision, --no-kitty, --dev, --dry-run, --help"
    - "Detecta pkg manager: apt / dnf / pacman / zypper"
    - "10 fases numeradas (0-10) com prints PT-BR sem emoji"
    - "Idempotente: duas execuções consecutivas produzem mesma saída (exceto data/hora)"
    - "Exit != 0 em qualquer falha, com mensagem clara em PT-BR"
    - "--dry-run não executa pip install, ollama pull, apt/dnf install, chmod, curl do Ollama"
    - "Acentuação PT-BR correta"
    - "Zero README, zero fase Gauntlet, zero Docker (tudo em 01B)"
```

---

**Status:** PENDENTE
**Data criação:** 2026-04-19
**Origem:** divisão de DEPLOY-01 em duas sprints (script local + Docker/README).
**Modelo obrigatório:** claude-opus-4-7 (sem subagentes)

---

## Contexto do projeto (snapshot — não referência)

> **ADRs relevantes:**
> - ADR-001 Local First: tudo offline.
> - ADR-004 Zero Emojis.
> - ADR-005 Anonimato.
> - ADR-006 PT-BR: acentuação obrigatória.
>
> **Estado do sistema:**
> - Onda 22, Bloco 7 (Deploy).
> - PORT-02 concluída: base Docker existente no repo (para 01B usar).
> - Referência existente: `/home/andrefarias/Desenvolvimento/Luna/install.sh` (755 linhas, produção). Reaproveitar estrutura, adaptar ao Nyx.
> - qwen3:4b (obrigatório) + moondream (opcional, `--no-vision` pula).

---

## Problema

Hoje o setup é manual: criar venv, pip install, instalar Ollama, pull qwen3, etc. Primeira experiência ruim. Falta script idempotente que traga o sistema do zero ao "./run.sh sobe limpo".

---

## Solução proposta

Um `install.sh` em bash puro, com 10 fases numeradas, flags de configuração, detecção de distro, e comportamento SKIP em 2a execução. Sem Docker, sem README, sem Gauntlet — tudo isso fica em 01B.

### Fases

```
FASE 0: Requisitos mínimos (python >= 3.10, detectar distro)
FASE 1: Criar venv (se ausente)
FASE 2: pip install -r requirements.txt (+ dev se --dev)
FASE 3: Instalar Ollama (curl oficial) se ausente
FASE 4: ollama pull qwen3:4b (se não está listado)
FASE 5: ollama pull moondream (se --no-vision NÃO passado, e se não está listado)
FASE 6: Instalar xclip (apt/dnf/pacman/zypper)
FASE 7: Perguntar sobre kitty (se --no-kitty não passado)
FASE 8: Permissões: chmod +x em run.sh, scripts/*.sh, scripts/*.py
FASE 9: Desktop entry (chama scripts/setup_desktop_entry.py se existir, SKIP se não — DEPLOY-02 cria)
FASE 10: Smoke test: import `from nyx.agent.loop import AgentLoop` via venv/bin/python
```

---

## Arquivos alvo (paths absolutos)

### `/home/andrefarias/Desenvolvimento/Nyx-Code/install.sh`

Estrutura-alvo (baseada em `Luna/install.sh`, adaptada):

```bash
#!/usr/bin/env bash
# ==============================================
# Nyx-Code -- Instalação Idempotente
# Rode múltiplas vezes sem efeito colateral
# ==============================================
set -eu

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# --- Cores (zero emoji) ---
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

# --- Flags ---
NO_VISION=0
NO_KITTY=0
DEV_MODE=0
DRY_RUN=0
while [[ $# -gt 0 ]]; do
    case "$1" in
        --no-vision) NO_VISION=1; shift ;;
        --no-kitty)  NO_KITTY=1; shift ;;
        --dev)       DEV_MODE=1; shift ;;
        --dry-run)   DRY_RUN=1; shift ;;
        -h|--help)
            cat <<EOF
Uso: ./install.sh [flags]

Flags:
  --no-vision   Pula pull de moondream (sem visão)
  --no-kitty    Não pergunta sobre kitty
  --dev         Instala requirements-dev.txt
  --dry-run     Mostra o que faria sem executar
  -h, --help    Esta mensagem
EOF
            exit 0 ;;
        *) echo "Flag desconhecida: $1"; exit 1 ;;
    esac
done

# --- Helpers ---
print_header() { ... }
print_step()   { echo -e "${CYAN}[$1/$2]${NC} $3"; }
print_ok()     { echo -e "    ${GREEN}OK${NC} $1"; }
print_skip()   { echo -e "    ${YELLOW}SKIP${NC} $1"; }
print_err()    { echo -e "    ${RED}ERRO${NC} $1"; }

have_cmd() { command -v "$1" &>/dev/null; }
detect_pkg_manager() {
    for pm in apt dnf pacman zypper; do
        if have_cmd "$pm"; then echo "$pm"; return; fi
    done
    echo ""
}
PKG_MANAGER="$(detect_pkg_manager)"
TOTAL=10

print_header

# FASE 0: Requisitos
# FASE 1: venv
# FASE 2: pip install
# FASE 3: Ollama
# FASE 4: qwen3:4b
# FASE 5: moondream (respeita --no-vision)
# FASE 6: xclip (respeita PKG_MANAGER)
# FASE 7: kitty (respeita --no-kitty)
# FASE 8: chmod +x
# FASE 9: desktop entry (SKIP se script ausente)
# FASE 10: smoke (import nyx)

echo ""
echo -e "${GREEN}  Instalação concluída. Rode: ./run.sh${NC}"
echo ""
```

**Regras de idempotência por fase:**

- FASE 1: `[ -d venv ]` → SKIP.
- FASE 2: sempre roda `pip install --quiet` (pip é idempotente; nada baixado em segunda run).
- FASE 3: `have_cmd ollama` → SKIP.
- FASE 4: `ollama list | grep -q 'qwen3:4b'` → SKIP.
- FASE 5: `ollama list | grep -q 'moondream'` → SKIP.
- FASE 6: `have_cmd xclip` → SKIP.
- FASE 7: `have_cmd kitty` → SKIP. Se não tem e `NO_KITTY=0`, perguntar.
- FASE 8: sempre roda chmod (idempotente).
- FASE 9: SKIP se `scripts/setup_desktop_entry.py` ausente; chamar se existir.
- FASE 10: sempre roda (barato).

**Comportamento de `--dry-run`:**

- Qualquer comando que escreva em disco, rede ou sistema é trocado por `print_skip "dry-run"` ou precedido por `[ $DRY_RUN -eq 0 ] && ...`.
- `pip install`, `ollama pull`, `curl .../install.sh | sh`, `sudo apt install`, `chmod +x` — todos pulados.

---

## Diff esperado (resumo)

```
+ 1 arquivo criado (install.sh, ~300 linhas)
~ 0 arquivos modificados
- 0 arquivos removidos
+ ~300 linhas líquidas
```

---

## Comandos de verificação (literais, copy-paste)

```bash
cd /home/andrefarias/Desenvolvimento/Nyx-Code

# 1. Sintaxe
bash -n install.sh && echo "sintaxe OK"

# 2. Executável
test -x install.sh && echo "exec OK"

# 3. Help
./install.sh --help

# 4. Dry-run (não deve criar venv nem pullar nada)
BEFORE=$(md5sum $(find . -maxdepth 2 -type f 2>/dev/null) 2>/dev/null | md5sum)
./install.sh --no-vision --no-kitty --dry-run
AFTER=$(md5sum $(find . -maxdepth 2 -type f 2>/dev/null) 2>/dev/null | md5sum)
[ "$BEFORE" = "$AFTER" ] && echo "dry-run não escreveu" || echo "FALHA: dry-run escreveu"

# 5. Idempotência (em máquina já com ambiente pronto)
./install.sh --no-kitty 2>&1 | tee /tmp/run1.log
./install.sh --no-kitty 2>&1 | tee /tmp/run2.log
# comparar exceto linhas com data:
diff <(grep -v '^\[.*202' /tmp/run1.log) <(grep -v '^\[.*202' /tmp/run2.log)
# esperado: vazio

# 6. Grep sanity
grep -c "emoji\|emoji" install.sh
# esperado: 0 (a string 'emoji' só aparece em comentário negando uso)
```

---

## Critério binário de aceite

- [ ] `install.sh` existe, executável, `bash -n` limpo
- [ ] Flags `--no-vision --no-kitty --dev --dry-run --help` funcionam
- [ ] `--help` imprime texto em PT-BR
- [ ] Detecta apt/dnf/pacman/zypper
- [ ] 10 fases numeradas `[N/10]`
- [ ] Zero emoji em saída e código
- [ ] Zero menção a IA
- [ ] Idempotente: 2 runs consecutivas = mesma saída (sem data)
- [ ] `--dry-run` não escreve em disco, rede ou sistema
- [ ] Exit != 0 com mensagem clara em PT-BR se falha
- [ ] Sem README, sem fase Gauntlet, sem Docker (fica em 01B)
- [ ] Commit: `feat: install.sh idempotente local (DEPLOY-01A)`

---

## Guardrails anti-engodo

**NÃO marque como concluída se:**

- `./install.sh` roda mas não tem output por fase (IA pulou estrutura numerada).
- Segunda execução reinstala algo.
- Aceita `sudo` em tudo sem discriminar o pkg manager.
- `--dry-run` ainda executa `pip install` ou `ollama pull`.
- IA escreveu README ou adicionou fase no Gauntlet (fora do escopo).

---

## Catálogo de gambiarras proibidas

Aplicáveis especialmente:

- #4 **Documentação como implementação**: script só tem `echo "instalaria X"` sem realmente instalar.
- #17 **Silent except**: `2>/dev/null || true` em comandos críticos sem verificar saída.
- #19 **Feature flag falsa**: `--dry-run` declarado mas ignorado em alguma fase.
- #18 **Sleep como fix**: `sleep 5` depois de `ollama pull` para "garantir". Proibido.

---

## Proof-of-work obrigatório

Incluir no relatório final:

- `cat /tmp/inv_before.txt | tail -10` + `cat /tmp/inv_after.txt | tail -10` + diff.
- Output de `bash -n install.sh`.
- Output de `./install.sh --help`.
- Output de `./install.sh --no-vision --no-kitty --dry-run`.
- Output de duas execuções `./install.sh --no-kitty` consecutivas + `diff` dos logs (sem linhas de data).
- `git show --stat HEAD`.

---

## Gambiarras específicas desta sprint

1. **Dry-run quebrado**: flag existe mas fase 2 roda `pip install` sem guard. Fix: toda chamada destrutiva deve ter `[ $DRY_RUN -eq 0 ] && ...`.
2. **Idempotência falsa**: 2a execução imprime "instalando" mas sai rápido porque pip não tem o que fazer — mas a saída muda. Critério é saída idêntica (menos data).
3. **Distro hardcoded**: script assume apt. Fix: função `detect_pkg_manager`, erro claro se nenhum é suportado.
4. **Emoji em cor ANSI**: usar `✓` verde em vez de `OK`. Proibido — `✓` é U+2713, considerado símbolo decorativo; usar apenas `OK`/`SKIP`/`ERRO` em texto.
5. **Expansão de path absoluta**: hardcodar `/home/andrefarias/...` no script. Fix: `SCRIPT_DIR="$(cd "$(dirname ...)" && pwd)"`.
6. **README ou Gauntlet**: IA "aproveita" e começa a escrever README. Fora do escopo. Sprint é rejeitada se commit inclui `README.md` ou `scripts/gauntlet/*`.

---

## Validação humana (checklist do usuário)

```bash
cd /home/andrefarias/Desenvolvimento/Nyx-Code

git log --oneline -1
git show --stat HEAD
# esperado: apenas install.sh + arquivos de sprint (SPRINT_ORDER_MASTER, EXECUTAR_SPRINT, mv da sprint)

bash -n install.sh
./install.sh --help
./install.sh --no-vision --no-kitty --dry-run

# Em máquina atual (já instalada):
./install.sh --no-kitty
# esperado: todas as fases SKIP, sai limpo

ls dev-journey/06-sprints/concluidos/SPRINT_DEPLOY_01A.md
! ls dev-journey/06-sprints/producao/SPRINT_DEPLOY_01A.md 2>/dev/null

# Confirmar que README NÃO foi tocado
git diff HEAD~1 HEAD -- README.md
# esperado: vazio
```

---

## Riscos

| Risco | Mitigação |
|-------|-----------|
| Distro fora das 4 suportadas | `print_err` + exit 1 com instruções manuais |
| Versão Ollama muda formato de `ollama list` | Depender só de `grep -q 'nome:tag'`, não parse estruturado |
| `curl` do Ollama falha por rede | Exit != 0 com mensagem; usuário pode reexecutar |
| Scripts `scripts/setup_desktop_entry.py` ainda não existe (DEPLOY-02) | FASE 9 faz SKIP elegante se ausente |
| IA escreve 500 linhas quando Luna tem 755 | Limite 800 linhas (CLAUDE.md §6); se ultrapassar, extrair helpers |

---

*"Automatizar a instalação é escrever respeito pelo tempo alheio." -- adaptado*
