# SPRINT COCKPIT-04 — Captura de evidência (screenshot) automática por feature

## 0. SPEC (machine-readable)

```yaml
sprint:
  id: COCKPIT-04
  title: "Captura de screenshot do REPL ao fim de cada feature, salvo em dev-journey/07-reports/evidencia/"
  onda: 23
  bloco: 23.3 Cockpit
  prioridade: MÉDIA
  tipo: Feature
  dependencias: [COCKPIT-03]
  desbloqueia: [COCKPIT-05]

  touches:
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/cockpit/server.py
      reason: "Adiciona rota POST /api/screenshot que retorna PNG do canvas xterm"

  creates:
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/dev-journey/07-reports/evidencia/.gitkeep
      reason: "Garantir que dir existe; evidências serão geradas em runtime"
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/cockpit/evidencia.py
      reason: "Helper para salvar PNG e atualizar REGISTRY.yaml com path"

  removes: []

  n_to_n_pairs:
    - descricao: "Path de evidência salvo em REGISTRY.yaml e no GAUNTLET_REPORT — fonte única em REGISTRY"
      paths:
        - /home/andrefarias/Desenvolvimento/Nyx-Code/dev-journey/04-features/REGISTRY.yaml

  forbidden:
    - "Salvar PNG fora de dev-journey/07-reports/evidencia/"
    - "Manter mais de 5 screenshots por feature (rotate, evitar bloat)"
    - "Aceitar PNG > 1 MB (downsample antes)"
    - "Path absoluto hardcoded; usar PROJECT_ROOT"

  tests:
    - cmd: "curl -X POST http://127.0.0.1:11437/api/screenshot -d '{\"feature_id\":\"I-01\"}' -H 'Content-Type: application/json'"
      timeout: 15
      deve_passar: true
      nota: "Retorna {path, size_kb}"
    - cmd: "ls dev-journey/07-reports/evidencia/I-01/*.png 2>/dev/null | wc -l"
      timeout: 5
      deve_passar: true
      nota: "Pelo menos 1 PNG após o test acima"
    - cmd: "bash scripts/sprint_invariants.sh"
      timeout: 60
      deve_passar: "FAIL_AFTER <= FAIL_BEFORE"

  acceptance_criteria:
    - "Rota POST /api/screenshot aceita {feature_id} e salva PNG em evidencia/<id>/<ts>.png"
    - "REGISTRY.yaml atualizado com path da última evidência"
    - "Rotate: máximo 5 PNGs por feature; mais antigos deletados"
    - "PNG < 1 MB cada (downsample/PNG-8 se necessário)"
    - "Browser API toBlob usado no front; backend só armazena"
    - "Chrome MCP consegue rodar gauntlet e capturar evidência via control API"
    - "Acentuação PT-BR; zero emoji"
```

---

**Status:** PENDENTE
**Data criação:** 2026-05-15
**Modelo obrigatório:** claude-opus-4-7 (sem subagentes)

---

# Sprint COCKPIT-04

## Solução

### Frontend (xterm canvas → PNG)

```javascript
async function screenshot(feature_id) {
  const canvas = terminal._core._renderService._renderer._renderLayers[0]._canvas;
  const blob = await new Promise(r => canvas.toBlob(r, 'image/png'));
  const form = new FormData();
  form.append('feature_id', feature_id);
  form.append('img', blob);
  await fetch('/api/screenshot', {method: 'POST', body: form});
}
```

### Backend

```python
@app.post("/api/screenshot")
async def screenshot(feature_id: str = Form(...), img: UploadFile = File(...), request: Request = None):
    _require_loopback(request)
    ts = datetime.utcnow().isoformat().replace(":", "-")
    dest = ROOT / f"dev-journey/07-reports/evidencia/{feature_id}/{ts}.png"
    dest.parent.mkdir(parents=True, exist_ok=True)
    data = await img.read()
    if len(data) > 1024 * 1024:
        raise HTTPException(400, "PNG > 1MB")
    dest.write_bytes(data)
    _rotate(dest.parent, keep=5)
    _update_registry_evidencia(feature_id, str(dest.relative_to(ROOT)))
    return {"path": str(dest.relative_to(ROOT)), "size_kb": len(data) // 1024}
```

## Verificação

```bash
# Manual via Chrome:
# 1. abrir cockpit, clicar Rodar em I-01
# 2. ver botão "Capturar evidência" aparecer ao fim
# 3. clicar — PNG aparece em dev-journey/07-reports/evidencia/I-01/
```

---

*"Evidência sem registro evapora; registro sem evidência mente." -- anônimo*
