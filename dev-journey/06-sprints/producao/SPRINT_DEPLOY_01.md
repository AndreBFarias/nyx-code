## 0. SPEC

```yaml
sprint:
  id: DEPLOY-01
  title: "install.sh idempotente: Ollama + qwen3 + moondream + xclip + kitty (opcional)"
  onda: 22
  bloco: 7
  prioridade: ALTA
  tipo: Infra
  dependencias: [VISION-03]
  desbloqueia: [DEPLOY-02]

  creates:
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/install.sh
      reason: "Script idempotente de instalação local-first"

  touches:
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/README.md
      reason: "Adicionar seção de instalação rápida"
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/.gitignore
      reason: "Garantir que venv/, .env, logs/ ficam ignorados (já estão, revalidar)"

  forbidden:
    - "Assumir root/sudo sem confirmar (usar sudo só em apt/pacman/dnf)"
    - "Baixar binários sem verificar origem (Ollama: script oficial)"
    - "Usar emoji na saída"
    - "Mencionar IA em mensagens"

  tests:
    - cmd: "bash -n install.sh && echo 'sintaxe OK'"
      deve_passar: true
    - cmd: "./install.sh --no-vision --no-kitty --dry-run"
      deve_passar: true
    - cmd: "./install.sh && ./install.sh"
      deve_passar: true
      nota: "Segunda execução deve produzir output SKIP"

  acceptance_criteria:
    - "install.sh existe e é executável"
    - "Flags: --no-vision, --no-kitty, --dev, --dry-run"
    - "Rodar 2x em sequência: segunda exec não reinstala nada (idempotência)"
    - "Fases numeradas (0-10) com prints estilo Luna (PT-BR, sem emoji)"
    - "Falha em qualquer fase sai com exit != 0 e mensagem clara"
    - "Variáveis de ambiente detectadas: apt/dnf/pacman/arch"
    - "Teste Gauntlet (novo) fase install passa em Docker Ubuntu 22.04"
```

---

# Sprint DEPLOY-01 — install.sh idempotente

## Contexto

- ADR-001 Local First — tudo offline.
- ADR-004/005 — zero emoji, zero menção a IA.
- PORT-02 CONCLUIDA — base Docker existe, reutilizar.
- Referência: `/home/andrefarias/Desenvolvimento/Luna/install.sh` (755 linhas, usado em produção pela Luna).

## Problema

Hoje o setup é manual: usuário precisa criar venv, pip install, instalar Ollama, pull qwen3, etc. Primeira experiência ruim.

## Solução

Script `install.sh` no estilo da Luna, com 10 fases numeradas.

### Fases

```
FASE 0: Requisitos mínimos (python≥3.10, detectar distro)
FASE 1: Criar venv (se ausente)
FASE 2: pip install -r requirements.txt
FASE 3: Instalar Ollama (via curl oficial) se ausente
FASE 4: ollama pull qwen3:4b (se não tem)
FASE 5: ollama pull moondream (se não tem e --no-vision NÃO passado)
FASE 6: Instalar xclip (apt/dnf/pacman conforme distro)
FASE 7: Perguntar sobre kitty (se --no-kitty não passado)
       Se sim: instalar kitty via gerenciador
FASE 8: Permissões: chmod +x em run.sh, scripts/*.sh
FASE 9: Gerar desktop entry (chama scripts/setup_desktop_entry.py -- DEPLOY-02)
FASE 10: Smoke test: ./run.sh --headless <<< '{"type":"ping"}' retorna {"type":"pong"}
```

### Estrutura (baseado em Luna/install.sh)

```bash
#!/usr/bin/env bash
# ==============================================
# Nyx-Code -- Instalação Idempotente
# Rode múltiplas vezes sem efeito colateral
# ==============================================
set -eu

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
            echo "Uso: ./install.sh [--no-vision] [--no-kitty] [--dev] [--dry-run]"
            exit 0 ;;
        *) echo "Flag desconhecida: $1"; exit 1 ;;
    esac
done

# --- Helpers ---
print_header() {
    echo ""
    echo -e "${CYAN}  ╭─ Nyx-Code · Instalador ────────────────────╮${NC}"
    echo -e "${CYAN}  │   100% offline · local-first · PT-BR        │${NC}"
    echo -e "${CYAN}  ╰──────────────────────────────────────────────╯${NC}"
    echo ""
}

print_step() { echo -e "${CYAN}[$1/$2]${NC} $3"; }
print_ok()   { echo -e "    ${GREEN}OK${NC} $1"; }
print_skip() { echo -e "    ${YELLOW}SKIP${NC} $1"; }
print_err()  { echo -e "    ${RED}ERRO${NC} $1"; }

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

# FASE 0
print_step 0 $TOTAL "Verificando requisitos..."
if ! have_cmd python3; then
    print_err "Python 3 não encontrado"; exit 1
fi
PY_VER=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
PY_MAJ=${PY_VER%.*}; PY_MIN=${PY_VER#*.}
if [ "$PY_MAJ" -lt 3 ] || { [ "$PY_MAJ" -eq 3 ] && [ "$PY_MIN" -lt 10 ]; }; then
    print_err "Python >= 3.10 necessário (tem $PY_VER)"; exit 1
fi
print_ok "Python $PY_VER"

# FASE 1
print_step 1 $TOTAL "Venv..."
if [ -d venv ]; then
    print_skip "venv já existe"
else
    [ $DRY_RUN -eq 0 ] && python3 -m venv venv
    print_ok "venv criado"
fi

# FASE 2
print_step 2 $TOTAL "Dependências Python..."
if [ $DRY_RUN -eq 0 ]; then
    source venv/bin/activate
    pip install --quiet --upgrade pip
    pip install --quiet -r requirements.txt
    [ $DEV_MODE -eq 1 ] && pip install --quiet -r requirements-dev.txt
fi
print_ok "pip install"

# FASE 3
print_step 3 $TOTAL "Ollama..."
if have_cmd ollama; then
    print_skip "ollama instalado ($(ollama --version 2>&1 | head -1))"
else
    if [ $DRY_RUN -eq 0 ]; then
        curl -fsSL https://ollama.ai/install.sh | sh
    fi
    print_ok "ollama instalado"
fi

# FASE 4
print_step 4 $TOTAL "Modelo qwen3:4b..."
if ollama list 2>/dev/null | grep -q "qwen3:4b"; then
    print_skip "qwen3:4b já pullado"
else
    [ $DRY_RUN -eq 0 ] && ollama pull qwen3:4b
    print_ok "qwen3:4b"
fi

# FASE 5
if [ $NO_VISION -eq 1 ]; then
    print_step 5 $TOTAL "Modelo moondream (visão)..."
    print_skip "--no-vision passado"
else
    print_step 5 $TOTAL "Modelo moondream (visão)..."
    if ollama list 2>/dev/null | grep -q "moondream"; then
        print_skip "moondream já pullado"
    else
        [ $DRY_RUN -eq 0 ] && ollama pull moondream
        print_ok "moondream"
    fi
fi

# FASE 6
print_step 6 $TOTAL "xclip (paste de imagem)..."
if have_cmd xclip; then
    print_skip "xclip ok"
else
    case "$PKG_MANAGER" in
        apt)    [ $DRY_RUN -eq 0 ] && sudo apt update && sudo apt install -y xclip ;;
        dnf)    [ $DRY_RUN -eq 0 ] && sudo dnf install -y xclip ;;
        pacman) [ $DRY_RUN -eq 0 ] && sudo pacman -Sy --noconfirm xclip ;;
        *)      print_err "Distro não suportada para instalar xclip automaticamente"; exit 1 ;;
    esac
    print_ok "xclip"
fi

# FASE 7
if [ $NO_KITTY -eq 1 ]; then
    print_step 7 $TOTAL "Kitty (terminal GPU)..."
    print_skip "--no-kitty passado"
else
    print_step 7 $TOTAL "Kitty (terminal GPU)..."
    if have_cmd kitty; then
        print_skip "kitty já instalado"
    else
        echo "    Kitty oferece melhor experiência visual (GPU-accelerated)."
        read -p "    Instalar kitty? [s/N] " -r REP
        if [[ $REP =~ ^[sSyY] ]]; then
            case "$PKG_MANAGER" in
                apt)    [ $DRY_RUN -eq 0 ] && sudo apt install -y kitty ;;
                dnf)    [ $DRY_RUN -eq 0 ] && sudo dnf install -y kitty ;;
                pacman) [ $DRY_RUN -eq 0 ] && sudo pacman -Sy --noconfirm kitty ;;
                *) print_skip "Distro sem auto-install — rode manualmente" ;;
            esac
            have_cmd kitty && print_ok "kitty" || print_skip "kitty não instalado"
        else
            print_skip "kitty dispensado pelo usuário"
        fi
    fi
fi

# FASE 8
print_step 8 $TOTAL "Permissões..."
[ $DRY_RUN -eq 0 ] && chmod +x run.sh scripts/*.sh scripts/*.py 2>/dev/null || true
print_ok "chmod +x"

# FASE 9
print_step 9 $TOTAL "Desktop entry..."
if [ -f scripts/setup_desktop_entry.py ] && [ $DRY_RUN -eq 0 ]; then
    venv/bin/python scripts/setup_desktop_entry.py && print_ok "entry criado" || print_skip "falhou (seguindo)"
else
    print_skip "scripts/setup_desktop_entry.py ausente (criado em DEPLOY-02)"
fi

# FASE 10
print_step 10 $TOTAL "Smoke test..."
if [ $DRY_RUN -eq 1 ]; then
    print_skip "dry-run — pulando smoke"
else
    # mini teste: importar pacote
    if venv/bin/python -c "from nyx.agent.loop import AgentLoop; print('ok')" &>/dev/null; then
        print_ok "imports OK"
    else
        print_err "import nyx falhou"; exit 1
    fi
fi

echo ""
echo -e "${GREEN}  Instalação concluída. Rode: ./run.sh${NC}"
echo ""
```

### README — seção de instalação

No topo do `README.md`, adicionar:

```markdown
## Instalação rápida

```bash
git clone ... Nyx-Code && cd Nyx-Code
./install.sh                   # completo
./install.sh --no-vision       # sem moondream (mais rápido, sem visão)
./install.sh --no-kitty        # sem kitty
./install.sh --dev             # + requirements-dev
./run.sh
```

Testado em Ubuntu 22.04, Fedora 39, Arch Linux.
```

## Comando de verificação

```bash
cd /home/andrefarias/Desenvolvimento/Nyx-Code

# 1. Sintaxe
bash -n install.sh && echo "sintaxe OK"

# 2. Dry run
./install.sh --no-vision --no-kitty --dry-run

# 3. Help
./install.sh --help

# 4. Idempotência (em Docker ou em máquina já instalada)
./install.sh
./install.sh  # segunda: tudo SKIP

# 5. Executável
test -x install.sh

# 6. Gauntlet (fase install)
./run.sh --gauntlet --only install
```

## Critério binário

- [ ] `install.sh` existe e executável
- [ ] Sintaxe válida (`bash -n`)
- [ ] Flags `--no-vision`, `--no-kitty`, `--dev`, `--dry-run`, `--help` funcionam
- [ ] Idempotente (2a execução: tudo SKIP)
- [ ] Sem emoji, sem menção a IA
- [ ] README tem seção de instalação
- [ ] Smoke test final verifica import
- [ ] Gauntlet install passa
- [ ] Commit: `feat: install.sh idempotente (Ollama + qwen3 + moondream + kitty opcional)`

## Guardrails anti-engodo

**NÃO marque como concluída se:**
- `./install.sh` roda mas não tem output por fase (IA pulou estrutura).
- Segunda execução instala de novo (não é idempotente).
- Aceita `sudo` em tudo sem discriminar.
- Flag `--dry-run` ainda executa comandos destrutivos.

## Validação humana

```bash
# Em VM limpa (Ubuntu 22.04)
./install.sh
./run.sh   # deve subir com os 3 componentes

# Em máquina atual (já instalada)
./install.sh
# esperado: tudo SKIP, sai limpo

./install.sh --help
# esperado: texto de ajuda claro
```

## Riscos

| Risco | Mitigação |
|-------|-----------|
| Distro fora das suportadas | Detectar e pular com msg; usuário instala manualmente |
| Versão Ollama muda formato de output | Não depender do texto; usar `ollama list | grep` |

---

*"Configurar não é instalar: é construir um lar para o código." -- anônimo*
