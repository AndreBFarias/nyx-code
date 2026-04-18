## 0. SPEC

```yaml
sprint:
  id: DEPLOY-02
  title: ".desktop entry + ícone Nyx (assets/nyx-icon.png) + launcher kitty + feedback de sessão salva"
  onda: 22
  bloco: 7
  prioridade: ALTA
  tipo: Feature
  dependencias: [DEPLOY-01]
  desbloqueia: [UX-EXTRA-01]

  creates:
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/scripts/setup_desktop_entry.py
      reason: "Gera ~/.local/share/applications/nyx.desktop + copia ícone"
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/scripts/uninstall_desktop_entry.py
      reason: "Remove desktop entry e ícone (simétrico)"

  touches:
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/install.sh
      reason: "Já chama setup_desktop_entry.py na FASE 9 (DEPLOY-01 deixou stub)"
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/cli.py
      reason: "Feedback visual ao salvar sessão no quit (absorve O-04)"

  absorve:
    - "O-04 (feedback visual ao salvar sessão)"

  forbidden:
    - "Hardcoded path /home/USUARIO — usar $HOME / Path.home()"
    - "Escrever em /usr (root) — só ~/.local/"
    - "Exigir sudo"
    - "Criar .desktop com Exec absoluto incorreto"

  tests:
    - cmd: "python scripts/setup_desktop_entry.py --dry-run"
      deve_passar: true
    - cmd: "test -f assets/nyx-icon.png && echo 'icon OK'"
      deve_passar: true

  acceptance_criteria:
    - "scripts/setup_desktop_entry.py existe e funciona em Ubuntu/Fedora/Arch"
    - "Ícone copiado para ~/.local/share/icons/hicolor/256x256/apps/nyx.png"
    - "Entry em ~/.local/share/applications/nyx.desktop criada"
    - "Exec usa path absoluto do run.sh (derivado do script location, não hardcoded)"
    - "Se kitty ausente: Exec usa $TERMINAL ou gnome-terminal como fallback"
    - "update-desktop-database chamado (se disponível)"
    - "scripts/uninstall_desktop_entry.py remove tudo simetricamente"
    - "cli.py mostra '[ok] sessão salva em ~/.nyx/sessions/<id>/' ao quit (destacado)"
    - "Flag --dry-run não escreve nada"
    - "Teste manual: ícone aparece no launcher do usuário"
```

---

# Sprint DEPLOY-02 — Desktop entry + ícone + feedback

## Contexto

- Usuário quer clicar no ícone e abrir Nyx em kitty.
- `assets/nyx-icon.png` já existe (256x256).
- Referência: Luna/install.sh FASE 8 + src/tools/setup_desktop_entry.py.
- Absorve O-04: feedback visual claro ao salvar sessão.

## Solução

### `scripts/setup_desktop_entry.py` (NOVO)

```python
#!/usr/bin/env python3
"""Setup Desktop Entry para Nyx-Code.

Cria:
- ~/.local/share/icons/hicolor/256x256/apps/nyx.png  (cópia de assets/nyx-icon.png)
- ~/.local/share/applications/nyx.desktop

Chama update-desktop-database se disponível.

Flags:
  --dry-run  mostra o que faria, não escreve
  --uninstall  remove entry e ícone
"""

from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
ICON_SRC = PROJECT_ROOT / "assets" / "nyx-icon.png"
RUN_SH = PROJECT_ROOT / "run.sh"

ICON_DST_DIR = Path.home() / ".local" / "share" / "icons" / "hicolor" / "256x256" / "apps"
ICON_DST = ICON_DST_DIR / "nyx.png"

APPS_DIR = Path.home() / ".local" / "share" / "applications"
DESKTOP_FILE = APPS_DIR / "nyx.desktop"


def detect_terminal_exec() -> str:
    """Retorna comando Exec= para o .desktop preferindo kitty."""
    run_sh = str(RUN_SH)
    if shutil.which("kitty"):
        return f"kitty --class Nyx --title 'Nyx Code Agent' -e {run_sh}"
    term = os.environ.get("TERMINAL", "")
    if term and shutil.which(term):
        return f"{term} -e {run_sh}"
    if shutil.which("gnome-terminal"):
        return f"gnome-terminal -- {run_sh}"
    if shutil.which("konsole"):
        return f"konsole -e {run_sh}"
    if shutil.which("xterm"):
        return f"xterm -e {run_sh}"
    return run_sh  # último recurso


def desktop_contents(exec_line: str) -> str:
    return f"""[Desktop Entry]
Version=1.0
Type=Application
Name=Nyx
GenericName=Code Agent Local
Comment=Agente de codigo offline, 100% local
Exec={exec_line}
Icon=nyx
Terminal=false
Categories=Development;
StartupWMClass=Nyx
"""


def install(dry_run: bool) -> int:
    if not ICON_SRC.is_file():
        print(f"[erro] icone nao encontrado: {ICON_SRC}", file=sys.stderr)
        return 1
    if not RUN_SH.is_file():
        print(f"[erro] run.sh nao encontrado: {RUN_SH}", file=sys.stderr)
        return 1

    print(f"[install] icone: {ICON_SRC} -> {ICON_DST}")
    if not dry_run:
        ICON_DST_DIR.mkdir(parents=True, exist_ok=True)
        shutil.copy2(ICON_SRC, ICON_DST)

    exec_line = detect_terminal_exec()
    content = desktop_contents(exec_line)
    print(f"[install] .desktop: {DESKTOP_FILE}")
    print("[install] Exec: " + exec_line)
    if not dry_run:
        APPS_DIR.mkdir(parents=True, exist_ok=True)
        DESKTOP_FILE.write_text(content, encoding="utf-8")
        DESKTOP_FILE.chmod(0o755)

    if shutil.which("update-desktop-database"):
        if not dry_run:
            subprocess.run(["update-desktop-database", str(APPS_DIR)], check=False)
        print("[install] update-desktop-database chamado")
    else:
        print("[skip] update-desktop-database ausente")

    print("[ok] Nyx instalado no launcher")
    return 0


def uninstall() -> int:
    removed = False
    if DESKTOP_FILE.exists():
        DESKTOP_FILE.unlink()
        removed = True
        print(f"[remove] {DESKTOP_FILE}")
    if ICON_DST.exists():
        ICON_DST.unlink()
        removed = True
        print(f"[remove] {ICON_DST}")
    if not removed:
        print("[skip] nada para remover")
    if shutil.which("update-desktop-database"):
        subprocess.run(["update-desktop-database", str(APPS_DIR)], check=False)
    return 0


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--dry-run", action="store_true")
    p.add_argument("--uninstall", action="store_true")
    args = p.parse_args()
    return uninstall() if args.uninstall else install(args.dry_run)


if __name__ == "__main__":
    sys.exit(main())
```

### `scripts/uninstall_desktop_entry.py`

Trivial: chama `setup_desktop_entry.py --uninstall`.

```python
#!/usr/bin/env python3
"""Remove desktop entry do Nyx."""
import subprocess, sys
sys.exit(subprocess.call([sys.executable, "scripts/setup_desktop_entry.py", "--uninstall"]))
```

### `nyx/cli.py` — feedback ao salvar sessão

No fim de `run_repl` (dentro do bloco de shutdown), substituir:

```python
saved = save_session(agent.session, project_name)
if saved:
    print(f"  {DIM}Sessão salva: {saved.name}{NC}")
```

Por:

```python
from nyx.themes.design_tokens import ANSI_SUCCESS_FG, ANSI_RESET, BULLETS
saved = save_session(agent.session, project_name)
if saved:
    print(f"\n  {ANSI_SUCCESS_FG}{BULLETS['tool_ok']} sessão salva{ANSI_RESET}")
    print(f"  {DIM}  {saved.resolve()}{NC}")
    print(f"  {DIM}  use /resume para retomar nesta janela ou na próxima abertura{NC}")
```

## Comando de verificação

```bash
cd /home/andrefarias/Desenvolvimento/Nyx-Code

# 1. Script sintaxe
python -m py_compile scripts/setup_desktop_entry.py && echo "sintaxe OK"

# 2. Dry run
python scripts/setup_desktop_entry.py --dry-run

# 3. Install real
python scripts/setup_desktop_entry.py
test -f ~/.local/share/applications/nyx.desktop && echo "entry OK"
test -f ~/.local/share/icons/hicolor/256x256/apps/nyx.png && echo "icon OK"

# 4. Conteúdo .desktop
cat ~/.local/share/applications/nyx.desktop | grep "^Exec="
# deve apontar para path absoluto do run.sh

# 5. Feedback de save no quit
./run.sh
# envie uma mensagem, depois Ctrl+D
# esperado: "● sessão salva" em verde + path + dica /resume

# 6. Uninstall
python scripts/setup_desktop_entry.py --uninstall
test ! -f ~/.local/share/applications/nyx.desktop && echo "desinstalado OK"
```

## Critério binário

- [ ] `scripts/setup_desktop_entry.py` e `scripts/uninstall_desktop_entry.py` existem e executáveis
- [ ] `--dry-run` não escreve nada
- [ ] Install real cria `~/.local/share/applications/nyx.desktop` e ícone em hicolor/256x256
- [ ] Exec aponta para path absoluto do `run.sh`
- [ ] Fallback kitty → $TERMINAL → gnome-terminal → konsole → xterm → run.sh nu
- [ ] Uninstall remove ambos
- [ ] cli.py imprime feedback de sessão salva com cor verde + path + dica /resume
- [ ] Teste manual: ícone aparece no launcher do usuário, clica, abre kitty com Nyx rodando
- [ ] Commit: `feat: desktop entry + kitty launcher + feedback de sessao salva`

## Guardrails anti-engodo

**NÃO marque como concluída se:**
- IA deixou `Exec=/home/andre...` hardcoded em vez de derivar do `__file__`.
- Install rodou mas ícone não aparece (faltou `update-desktop-database`).
- Feedback "sessão salva" segue em cinza sem destaque.
- Uninstall deixa arquivos órfãos.

## Validação humana

```bash
# Install
python scripts/setup_desktop_entry.py

# Abrir launcher (rofi, GNOME, KDE) — buscar "Nyx"
# Clicar no ícone — deve abrir kitty com Nyx rodando

# Ctrl+D no Nyx
# → ver feedback verde "● sessão salva ~/.nyx/sessions/..."

# Cleanup
python scripts/setup_desktop_entry.py --uninstall
# → buscar no launcher: não aparece mais
```

## Riscos

| Risco | Mitigação |
|-------|-----------|
| launcher não detecta sem `update-desktop-database` | Chamar se existir; senão usuário faz logout/login |
| WM não respeita StartupWMClass | Aceitável — kitty tem seu próprio class matching |
| Icone baixa resolução em HiDPI | Usar 256x256 é suficiente; escalável |

---

*"O software é tão fácil quanto o clique que o abre." -- anônimo*
