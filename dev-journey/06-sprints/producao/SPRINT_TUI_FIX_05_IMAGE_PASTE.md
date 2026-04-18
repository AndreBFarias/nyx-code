## 0. SPEC (machine-readable)

```yaml
sprint:
  id: TUI-FIX-05
  title: "Ctrl+V cola imagem do clipboard (Ctrl+Shift+V impossível em xterm)"
  touches:
    - path: nyx/agent/clipboard.py
      reason: "Novo módulo: detecta imagem via xclip, salva em ~/.nyx/pastes/, retorna path"
    - path: nyx/cli.py
      reason: "Keybinding c-v que tenta imagem primeiro, texto depois; inserir [Image #N] no buffer"
    - path: nyx/agent/session.py
      reason: "CodeSession.image_map: dict[int, Path] para mapping [Image #N] -> arquivo"
  n_to_n_pairs:
    - "Se imagem colada, incrementa contador E grava em image_map"
    - "Se xclip não tem imagem, Ctrl+V executa paste de texto normal (não quebrar)"
  forbidden:
    - "Depender de Ctrl+Shift+V (terminal intercepta, app nunca recebe)"
    - "Crashar se xclip não instalado (degradar pra aviso + paste de texto)"
    - "Gravar arquivo fora de ~/.nyx/pastes/"
    - "Enviar imagem pro modelo (qwen3:4b não suporta visão; só metadata)"
  tests:
    - cmd: "./run.sh --gauntlet --only p7"
      timeout: 60
    - cmd: "manual: copiar imagem qualquer (printscreen), abrir Nyx, Ctrl+V; ver [Image #1] no input"
      timeout: 60
  acceptance_criteria:
    - "Ctrl+V: se clipboard tem imagem, salva em ~/.nyx/pastes/YYYY-MM-DD_HHMMSS_N.png e insere [Image #N]"
    - "Ctrl+V sem imagem: paste de texto normal"
    - "xclip não instalado: aviso uma vez, keybind não crasha"
    - "Contador N por sessão (reseta ao sair)"
    - "CodeSession.image_map persiste o mapping pra hover/debug"
    - "Permission check: como é dado do usuário voluntário, não pede confirmação"
    - "Mensagem 'Image #N salva em ~/.nyx/pastes/...' breve no stdout"
```

---

# Sprint TUI-FIX-05 -- Colar imagem via Ctrl+V

**Status:** PENDENTE
**Data:** 2026-04-17
**Prioridade:** MÉDIA
**Tipo:** Feature
**Dependências:** --
**Desbloqueia:** (futuro modelo de visão)

---

## Problema / Contexto

Usuário: "control shift v pra colar imagens não rola também". Investigação revelou que **Ctrl+Shift+V é INTERCEPTADO pelo terminal** (xterm, GNOME Terminal, Konsole) como paste nativo de texto -- a app nunca recebe o keypress. Isso é limitação do protocolo de terminais Unix, não do Nyx.

Alternativa viável: **Ctrl+V simples** + lookup do clipboard via `xclip`. Se xclip tem imagem (`-t image/png`), salvamos; senão, fazemos paste de texto normal.

Modelo atual (qwen3:4b) é text-only. Apenas gravamos arquivo e deixamos placeholder `[Image #N]` pra quando houver modelo de visão.

## Implementação

### Fase 1 -- clipboard.py

```python
# nyx/agent/clipboard.py
import subprocess
import time
from pathlib import Path

PASTES_DIR = Path.home() / ".nyx" / "pastes"

def capture_image() -> Path | None:
    """Retorna path salvo ou None se clipboard não tem imagem."""
    try:
        r = subprocess.run(
            ["xclip", "-selection", "clipboard", "-t", "image/png", "-o"],
            capture_output=True, timeout=2,
        )
        if r.returncode != 0 or not r.stdout:
            return None
        PASTES_DIR.mkdir(parents=True, exist_ok=True)
        ts = time.strftime("%Y-%m-%d_%H%M%S")
        idx = 1
        while (PASTES_DIR / f"{ts}_{idx}.png").exists():
            idx += 1
        path = PASTES_DIR / f"{ts}_{idx}.png"
        path.write_bytes(r.stdout)
        return path
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return None

def capture_text() -> str | None:
    try:
        r = subprocess.run(
            ["xclip", "-selection", "clipboard", "-o"],
            capture_output=True, timeout=2, text=True,
        )
        return r.stdout if r.returncode == 0 else None
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return None
```

### Fase 2 -- Keybinding Ctrl+V

Em `cli.py`:

```python
_image_counter = {"n": 0}
_image_map: dict[int, Path] = {}

@kb.add('c-v')
def _paste(event):
    from nyx.agent.clipboard import capture_image, capture_text
    img_path = capture_image()
    if img_path:
        _image_counter["n"] += 1
        n = _image_counter["n"]
        _image_map[n] = img_path
        event.current_buffer.insert_text(f"[Image #{n}]")
        # Exibir breve feedback (run_in_terminal)
        from prompt_toolkit.application import run_in_terminal
        run_in_terminal(lambda: print(f"  {DIM}Image #{n} -> {img_path}{NC}"))
        return
    text = capture_text()
    if text:
        event.current_buffer.insert_text(text)
```

### Fase 3 -- Mapping persistido

Em `session.py::CodeSession`:

```python
self.image_map: dict[int, str] = {}  # N -> path string
```

No callback `on_submit` (ou equivalente), transferir `_image_map` pra `session.image_map` pra persistência via `persistence.py`.

### Fase 4 -- Detectar ausência de xclip

Na primeira tentativa de `capture_image`, se `FileNotFoundError`, marcar `_xclip_missing = True` e na segunda tentativa nem chamar (poupar timeout).

### Fase 5 -- Teste de regressão

Ctrl+V com clipboard de texto (caso 99% do uso) deve funcionar igual ao default do PromptSession.

## Verificação

```bash
# Instalar xclip se não tem
which xclip || sudo apt install -y xclip

# Copiar imagem (print screen, ou qualquer viewer de imagem -> Copiar)
./run.sh
# Ctrl+V no prompt
# Ver [Image #1] no input
# Ctrl+V de novo com outra imagem
# Ver [Image #2]

# Teste texto normal
echo "texto copiado" | xclip -selection clipboard
# Ctrl+V no prompt -- ver "texto copiado"

# Teste sem xclip
sudo apt remove -y xclip
./run.sh
# Ctrl+V -- não crasha, sem efeito

./run.sh --gauntlet --only p7
```

- [ ] Ctrl+V com imagem: salva e insere placeholder
- [ ] Ctrl+V com texto: paste normal
- [ ] Ctrl+V sem xclip: silencioso (não crasha)
- [ ] `~/.nyx/pastes/` criado automaticamente
- [ ] Counter incrementa por sessão
- [ ] image_map persistido na session
- [ ] Gauntlet p7 passa

---

*"Uma imagem vale mais do que mil palavras, mas mil palavras descrevem uma imagem." -- Confúcio adaptado*
