# SPRINT 245 — UX-COCKPIT-FULLSCREEN-01

## 0. SPEC

```yaml
sprint:
  id: UX-COCKPIT-FULLSCREEN-01
  title: "Terminal cockpit ocupa toda viewport do browser (fullscreen CSS)"
  onda: 31
  prioridade: MÉDIA
  tipo: Feature
  dependencias: [UX-WEB-NO-LOCAL-CLI-01]
  desbloqueia: []

  touches:
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/cockpit/static/terminal.html
      reason: "CSS atual deixa terminal em viewport pequeno (~630x250px). Usuario pediu fullscreen."
  creates: []
  removes: []
```

---

# Sprint 245 — UX-COCKPIT-FULLSCREEN-01

**Status:** PENDENTE
**Data criação:** 2026-05-25

## Contexto

Usuário pediu: "no chrome deixa fullscrean tmb". Captura mostra terminal renderizado em ~630x250 pixels no canto superior esquerdo do browser; resto da viewport vazio.

## Solução

CSS em `terminal.html`:
- `body, html { width: 100vw; height: 100vh; overflow: hidden; margin: 0; }`
- `.xterm-screen { width: 100vw !important; height: calc(100vh - 32px) !important; }` (32px reservados pro header `Nyx cockpit/terminal/dashboard` + status)
- JS: chamar `fitAddon.fit()` (ou similar) após resize do window

## Acceptance

- [ ] Terminal ocupa ~100% da viewport (descontado header)
- [ ] Resize do browser ajusta colunas/linhas do xterm dinamicamente
- [ ] Fonte legível em telas 1080p, 1440p
- [ ] Funciona em Chrome + Firefox

## Proof-of-work

```bash
./run.sh --web &
sleep 15
google-chrome --new-window http://127.0.0.1:11437/static/terminal.html &
sleep 5
# Captura
import -window $(xdotool search --name "Nyx Cockpit" | tail -1) /tmp/fullscreen.png
# Esperado: terminal preenche 1280x720 ou mais
```
