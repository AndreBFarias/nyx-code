# SPRINT VISUAL-LAYOUT-02 — Banner 3 modos (compact/wide/neofetch)

## 0. SPEC (machine-readable)

```yaml
sprint:
  id: VISUAL-LAYOUT-02
  title: "Banner ganha modo neofetch (info-rich) coexistindo com compact/wide existentes"
  onda: 24
  bloco: 24.2 Visual Layout
  prioridade: MÉDIA
  tipo: Feature
  dependencias: [VISUAL-LAYOUT-01]
  desbloqueia: []

  touches:
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/agent/banner.py
      reason: "Adicionar função _build_neofetch + dispatcher por NYX_BANNER_MODE"
  creates: []
  removes: []

  n_to_n_pairs:
    - descricao: "NYX_BANNER_MODE documentado em defaults.py e .env.example"
      paths:
        - /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/config/defaults.py
        - /home/andrefarias/Desenvolvimento/Nyx-Code/.env.example

  forbidden:
    - "Emoji no banner"
    - "Menção a IA externa no banner"
    - "Quebrar invariante #14 (glifos canônicos)"
    - "Hardcode de path absoluto fora do permitido"

  tests:
    - cmd: "NYX_BANNER_MODE=neofetch ./run.sh --smoke"
      timeout: 30
      deve_passar: "boot ok"
    - cmd: "bash scripts/sprint_invariants.sh"
      timeout: 60
      deve_passar: "PASS 14, FAIL 0"

  acceptance_criteria:
    - "Função _build_neofetch existe em banner.py"
    - "NYX_BANNER_MODE=neofetch produz banner info-rich (modelo, hostname, terminal, GPU, memória, swap, distro)"
    - "Modos compact e wide preservados (ADR-029 mantido)"
    - "Smoke ok em qualquer modo"
    - "Invariantes 14/14"
```

---

# Sprint VISUAL-LAYOUT-02 — Banner 3 modos

**Status:** PENDENTE
**Data criação:** 2026-05-18
**Modelo obrigatório:** claude-opus-4-7 (sem subagentes)

---

## Contexto

ADR-029 (Layout Parity) estabeleceu banner em 3 linhas (modo `wide`) e variante `compact`. O usuário sinalizou apreço pelo neofetch (mensagem do prompt da sessão 2026-05-18: incluiu output completo do neofetch). Banner "neofetch" agrega informação útil para troubleshooting e estética rica em sessões interativas.

---

## Solução

Adicionar `_build_neofetch(theme)` em `nyx/agent/banner.py` que retorna string multi-linha com:
- Logo ASCII Nyx (turquesa #00D4AA do design_tokens)
- Hostname + distro + kernel
- Shell + terminal
- Tema + cores
- CPU + GPU (via detect_gpu.py)
- RAM + Swap (via /proc/meminfo)
- Disco do home
- Bateria (se laptop)
- Modelo Nyx ativo + porta proxy
- "Spellbook-OS: Sincronizado" (referência ao prompt do usuário)

Dispatcher na função pública `build_banner()`:
```python
mode = os.environ.get("NYX_BANNER_MODE", "wide")
if mode == "compact": return _build_compact(theme)
if mode == "neofetch": return _build_neofetch(theme)
return _build_wide(theme)
```

---

## Arquivos alvo

### `nyx/agent/banner.py`

Adicionar `_build_neofetch(theme: dict) -> str` (~80 linhas). Reusa helpers como `_color()`, `_box_chars()` já existentes.

### `nyx/config/defaults.py`

Adicionar:
```python
NYX_BANNER_MODE = os.environ.get("NYX_BANNER_MODE", "wide")
```

### `.env.example`

```
# Modo do banner: compact | wide (padrão) | neofetch
NYX_BANNER_MODE=wide
```

---

## Comandos de verificação

```bash
# 1. Smoke em cada modo
NYX_BANNER_MODE=compact ./run.sh --smoke
NYX_BANNER_MODE=wide ./run.sh --smoke
NYX_BANNER_MODE=neofetch ./run.sh --smoke

# 2. Capturar banner via scrot (validação humana)
NYX_BANNER_MODE=neofetch ./run.sh &
sleep 3 && scrot -u /tmp/banner_neofetch.png
pkill -f "nyx.cli"

# 3. Invariantes
bash scripts/sprint_invariants.sh | tail -5
```

---

## Critério binário de aceite

- [ ] `_build_neofetch` implementado em `nyx/agent/banner.py`
- [ ] `NYX_BANNER_MODE` em `defaults.py` + `.env.example`
- [ ] Dispatcher na `build_banner()` distingue 3 modos
- [ ] Smoke ok nos 3 modos
- [ ] Invariantes 14/14
- [ ] Banner neofetch mostra: hostname, distro, kernel, shell, terminal, CPU, GPU (se detectada), RAM, swap, disco, modelo Nyx, porta proxy
- [ ] Sprint movida `producao/` → `concluidos/`
- [ ] Commit `feat(VISUAL-LAYOUT-02): banner ganha modo neofetch (compact/wide/neofetch)`

---

## Riscos

| Risco | Mitigação |
|---|---|
| Banner neofetch quebra em terminal estreito (<80 cols) | Fallback para modo `wide` se cols < 100 |
| Detect_gpu.py demora (cold call) | Cache em /tmp; fallback string fixa se >500ms |
| Acentuação PT-BR no banner | Strings literais em PT-BR (ex: "Memória", "Configuração") |

---

*"Identidade visual rica é convite a explorar." — VISUAL-LAYOUT-02*
