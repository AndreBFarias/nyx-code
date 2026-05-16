# SPRINT COCKPIT-03 — Dashboard de features (62 cards) + gauntlet por feature

## 0. SPEC (machine-readable)

```yaml
sprint:
  id: COCKPIT-03
  title: "Dashboard com 62 features (cards, status verde/amarelo/vermelho) + botão Rodar Gauntlet por feature"
  onda: 23
  bloco: 23.3 Cockpit
  prioridade: ALTA
  tipo: Feature+UX
  dependencias: [COCKPIT-02, SBOM-REGISTRY-02]
  desbloqueia: [COCKPIT-04, UX-COCKPIT-EXPERIENCE-01]

  touches:
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/cockpit/server.py
      reason: "Adiciona rota POST /api/features/{id}/run que dispara gauntlet single-feature"
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/cockpit/static/index.html
      reason: "Layout dashboard + cards + paleta D + tokens"

  creates:
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/cockpit/static/app.js
      reason: "Alpine.js state + HTMX bindings"
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/cockpit/static/app.css
      reason: "Paleta D (turquesa #00D4AA, roxo #9D4EDD); reusa ANSI hex do design_tokens"
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/cockpit/static/htmx.min.js
      reason: "HTMX vendored (ADR-001)"
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/cockpit/static/alpine.min.js
      reason: "Alpine.js vendored"

  removes: []

  n_to_n_pairs:
    - descricao: "Paleta D hex aparece em design_tokens.py e cockpit/static/app.css — fonte única em design_tokens (cockpit lê via /api/tokens)"
      paths:
        - /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/themes/design_tokens.py
        - /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/cockpit/static/app.css

  forbidden:
    - "Hardcoded de hex em app.css (deve vir de /api/tokens que lê design_tokens.py)"
    - "Permitir gauntlet sem confirmar feature_id válido (404 se não existe)"
    - "Spawn gauntlet sem timeout (hard cap 300s)"
    - "CDN remoto para Alpine/HTMX (vendored apenas)"
    - "Adicionar emoji ou menção a IA"

  tests:
    - cmd: "curl -sf http://127.0.0.1:11437/ | grep -c 'Nyx'"
      timeout: 10
      deve_passar: true
    - cmd: "curl -sf http://127.0.0.1:11437/api/tokens | jq '.accent'"
      timeout: 10
      deve_passar: true
      nota: "Retorna '#00D4AA' (paleta D)"
    - cmd: "curl -X POST http://127.0.0.1:11437/api/features/I-01/run"
      timeout: 60
      deve_passar: true
      nota: "Dispara gauntlet single; resposta com job_id"
    - cmd: "bash scripts/sprint_invariants.sh"
      timeout: 60
      deve_passar: "FAIL_AFTER <= FAIL_BEFORE"

  acceptance_criteria:
    - "GET / retorna dashboard HTML com 62 cards"
    - "Cada card mostra: id, descricao, status (badge verde/amarelo/vermelho/cinza), ultimo_teste, kpi"
    - "Card tem botão 'Rodar' que POST em /api/features/{id}/run"
    - "Status do card atualiza em tempo real via WS /stream após gauntlet completar"
    - "Filtros: por categoria, por status — Alpine.js state"
    - "Paleta D aplicada (turquesa principal, roxo em destaques especiais)"
    - "Mobile responsivo (cols 1, 2, 3 conforme width)"
    - "ADR-025 (PROPOSTO): card tem feedback claro de início/fim de gauntlet (juicing)"
    - "Acentuação PT-BR; PT-BR no UI"
```

---

**Status:** PENDENTE
**Data criação:** 2026-05-15
**Modelo obrigatório:** claude-opus-4-7 (sem subagentes)

---

# Sprint COCKPIT-03

## Solução resumida

Dashboard com Alpine.js + HTMX:

```html
<main x-data="dashboard()">
  <header>
    <h1>Nyx Cockpit</h1>
    <span x-text="`${features.length} features · ${verdes} verdes · ${amarelas} amarelas · ${vermelhas} vermelhas · ${desconhecidos} sem teste`"></span>
  </header>
  <section class="filters">
    <select x-model="filtro.categoria">...</select>
    <select x-model="filtro.status">...</select>
  </section>
  <section class="grid">
    <template x-for="f in filtered" :key="f.id">
      <article class="card" :data-status="f.status">
        <h3 x-text="f.id + ' — ' + f.descricao"></h3>
        <span class="badge" x-text="f.status"></span>
        <time x-text="f.ultimo_teste || 'nunca'"></time>
        <button @click="run(f.id)">Rodar</button>
      </article>
    </template>
  </section>
</main>
```

```python
@app.post("/api/features/{feature_id}/run")
async def run_feature(feature_id: str, request: Request):
    _require_loopback(request)
    # Spawn gauntlet single-feature em background, retorna job_id
    job_id = str(uuid.uuid4())
    asyncio.create_task(_run_gauntlet_feature(feature_id, job_id))
    return {"job_id": job_id, "feature_id": feature_id, "status": "iniciado"}
```

## Verificação

```bash
./run.sh --cockpit
# abrir http://127.0.0.1:11437 — ver 62 cards
# clicar 'Rodar' em I-01 — ver status mudar para 'rodando' depois 'verde'
```

---

*"Cada card é um espelho do projeto vivo." -- anônimo*
