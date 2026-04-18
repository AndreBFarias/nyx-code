## 0. SPEC

```yaml
sprint:
  id: VISION-02
  title: "Pipeline [Image #N] -> descrição injetada no contexto do agente + /vision N"
  onda: 22
  bloco: 6
  prioridade: ALTA
  tipo: Feature
  dependencias: [VISION-01]
  desbloqueia: [VISION-03]

  touches:
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/cli.py
      reason: "Novo _expand_images(user_input, image_map) invocado antes de enviar ao AgentLoop"
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/agent/services/vision_service.py
      reason: "Adicionar describe_many(paths) com paralelismo opcional"
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/agent/commands/core.py (ou onde estiver)
      reason: "Novo /vision N que mostra descrição em cache da imagem N"

  forbidden:
    - "Bloquear o event loop esperando descrição (deve ser async ou thread pool)"
    - "Perder referência a image_map quando usuário envia múltiplas imagens"
    - "Modificar a imagem original"

  tests:
    - cmd: "python -c 'from nyx.cli import _expand_images; print(\"ok\")'"
      deve_passar: true
    - cmd: "./run.sh --gauntlet --only vision"
      deve_passar: true

  acceptance_criteria:
    - "_expand_images(text, image_map) substitui cada [Image #N] pela descrição inline"
    - "Se descrição > 200 chars, trunca para primeiras 2 frases + '…'"
    - "VisionService.describe_many(list_of_paths) existe"
    - "/vision N retorna a descrição cacheada da imagem N (ou erro amigável se N não existe)"
    - "Quando moondream ausente: [Image #N] substitui por '[Imagem #N: visão indisponível]' (não crasha)"
    - "Gauntlet vision passa"
    - "Teste manual: colar imagem + 'o que é isto?' → resposta qualitativa sobre a imagem"
```

---

# Sprint VISION-02 — Pipeline de imagens

## Contexto

Dependência: VISION-01 concluída (VisionService pronto).
Cenário: usuário faz Ctrl+V (TUI-FIX-05), buffer recebe `[Image #N]` + `image_map[N] = path`. Agente atual só vê o placeholder.

## Problema

A imagem é capturada mas ignorada. Agent texto-only não consegue descrevê-la.

## Solução

### `nyx/cli.py` — `_expand_images`

```python
def _expand_images(user_input: str, image_map: dict[int, str], vision: "VisionService") -> str:
    """Substitui [Image #N] pela descrição; respeita cache do VisionService."""
    import re
    from pathlib import Path

    def _shorten(desc: str, max_chars: int = 200) -> str:
        if len(desc) <= max_chars:
            return desc
        # primeiras 2 frases ou max_chars
        sentences = desc.split(". ")
        acc = ""
        for s in sentences[:2]:
            if len(acc) + len(s) > max_chars:
                break
            acc += s + ". "
        return (acc.strip() or desc[:max_chars]) + "…"

    def repl(match: re.Match) -> str:
        n = int(match.group(1))
        path = image_map.get(n)
        if not path:
            return f"[Imagem #{n}: referência inválida]"
        desc = vision.describe(Path(path))
        short = _shorten(desc)
        return f"[Imagem #{n}: {short}]"

    return re.sub(r"\[Image #(\d+)\]", repl, user_input)
```

### Onde chamar

Antes de `render_user_input(user_input)` ou antes de `agent.run(...)`:

```python
if image_map:
    from nyx.agent.services.vision_service import VisionService
    vision = VisionService()
    user_input = _expand_images(user_input, image_map, vision)
```

O `render_user_input` renderizado deve mostrar o texto **com** a descrição inline (usuário vê "entendi que é X antes de enviar").

### `VisionService.describe_many`

```python
def describe_many(self, paths: list[Path]) -> list[str]:
    """Descreve múltiplas imagens sequencialmente (cache-friendly).

    Nota: paralelizar não acelera (moondream CPU-bound).
    """
    return [self.describe(p) for p in paths]
```

### Novo comando `/vision N`

```python
@nyx_command(name="vision", description="Mostra descrição da imagem N (ex.: /vision 1)", category="contexto")
def cmd_vision(args: str, _root: str) -> str:
    from pathlib import Path
    from nyx.agent.services.vision_service import VisionService
    n = args.strip()
    if not n.isdigit():
        return "Uso: /vision <numero da imagem>. Ex.: /vision 1"
    n = int(n)
    # image_map vem de cli via session — alternativa: salvar em ~/.nyx/image_index.json
    idx_path = Path.home() / ".nyx" / "image_index.json"
    if not idx_path.exists():
        return "Nenhuma imagem mapeada na sessão."
    import json
    idx = json.loads(idx_path.read_text(encoding="utf-8"))
    path_str = idx.get(str(n))
    if not path_str:
        return f"Imagem #{n} não encontrada no índice."
    v = VisionService()
    desc = v.describe(Path(path_str))
    return f"  [imagem #{n}] {desc}\n  path: {path_str}"
```

**Para o comando acessar `image_map`:** cli.py persiste em `~/.nyx/image_index.json` toda vez que adiciona imagem:

```python
def _persist_image_index(image_map: dict[int, str]) -> None:
    import json
    idx_path = Path.home() / ".nyx" / "image_index.json"
    idx_path.write_text(json.dumps({str(k): v for k, v in image_map.items()}), encoding="utf-8")

# chamar após inserir em image_map (no @kb.add("c-v"))
```

## Comando de verificação

```bash
cd /home/andrefarias/Desenvolvimento/Nyx-Code

# 1. _expand_images importável e funcional
python -c "
from nyx.cli import _expand_images
from nyx.agent.services.vision_service import VisionService
v = VisionService()
if not v.is_available():
    # fallback test
    out = _expand_images('[Image #1] o que é?', {1: '/tmp/notexist.png'}, v)
    assert 'visão indisponível' in out or 'arquivo não encontrado' in out
    print('fallback OK')
else:
    # test com imagem real
    out = _expand_images('[Image #1] descreva', {1: 'assets/nyx-icon.png'}, v)
    assert '[Imagem #1:' in out and len(out) > 30
    print('expansion OK:', out[:100])
"

# 2. /vision N
# (teste manual no REPL)

./run.sh --gauntlet --only vision
```

## Critério binário

- [ ] `_expand_images` existe e substitui `[Image #N]` por descrição inline
- [ ] Truncamento respeita 200 chars
- [ ] `/vision N` existe e lê de `~/.nyx/image_index.json`
- [ ] Imagem persiste no índice quando usuário faz Ctrl+V
- [ ] Quando moondream ausente: expansão substitui por "[Imagem #N: visão indisponível]"
- [ ] Gauntlet vision passa
- [ ] Teste manual: colar print da tela + "o que é?" → Nyx descreve a imagem
- [ ] Commit: `feat: pipeline [Image #N] + /vision N + describe_many`

## Guardrails anti-engodo

**NÃO marque como concluída se:**
- `_expand_images` existe mas não é chamada antes de `agent.run`.
- Teste manual "o que é isto?" retorna "Não sei, não vejo imagens".
- `/vision 1` não achou imagem mesmo depois de Ctrl+V.
- Descrição cacheada não aparece no expand (cache quebrado).

## Validação humana

```bash
./run.sh
# nyx> (Ctrl+V de um screenshot) o que aparece na imagem?
# → Nyx responde descrevendo a imagem (moondream puxou, descreveu, injetou no contexto)
# nyx> /vision 1
# → mostra descrição cacheada + path
```

---

*"A imagem é um pensamento que precisa de palavras emprestadas." -- anônimo*
