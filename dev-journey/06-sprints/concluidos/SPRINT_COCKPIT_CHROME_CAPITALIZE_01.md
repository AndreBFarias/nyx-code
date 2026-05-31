# SPRINT 304 — COCKPIT-CHROME-CAPITALIZE-01

## 0. SPEC (machine-readable)

```yaml
sprint:
  id: COCKPIT-CHROME-CAPITALIZE-01
  title: "Capitalizar o chrome do cockpit (header/hint/status do --web)"
  onda: 35
  prioridade: BAIXA
  tipo: Bugfix
  touches:
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/cockpit/static/terminal.html
      reason: "header, hint do footer e textos de setStatus capitalizados"
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/cockpit/static/index.html
      reason: "brand-sub e label de cancelar"
  acceptance_criteria:
    - "header/hint/status capitalizados no --web"
    - "smoke + invariantes 14/14 + gauntlet rapido APROVADO"
```

---

**Status:** CONCLUIDA
**Data criação:** 2026-05-30
**Data conclusão:** 2026-05-30
**Modelo obrigatório:** claude-opus-4-7 (sem subagentes)

---

## Problema

Termos do chrome do cockpit em minúscula (`cockpit / terminal`, `dashboard`, `conectado`, hint do footer, etc.).

## Fix

- `terminal.html`: `Cockpit / Terminal`; link `Dashboard`; status inicial `Conectando...`; footer `Ctrl+C Cancela | Ctrl+D Sai | Redimensione livremente`; `setStatus(... "Conectado")`, `"Desconectado"`, `"Erro"`.
- `index.html`: `Cockpit / Dashboard`; fallback do botão `'Cancelar'` (a FUNÇÃO `cancelar(f.id)` permanece minúscula — só o texto exibido muda).

## Proof-of-work

```
FAIL_BEFORE=0 -> FAIL_AFTER=0 (14/14)   gauntlet --only rapido: 19/19 (100%) APROVADO
```
**--web real (DOM, após cache-bust):** `header .muted = "Cockpit / Terminal"`, `link = "Dashboard"`, `status = "Conectado"`, `footer = "Ctrl+C Cancela | Ctrl+D Sai | Redimensione livremente"`.

## Nota (cache do browser)

O cockpit serve os estáticos com cache do browser: após editar, a 1ª navegação pode exibir a versão antiga em cache. Validado forçando cache-bust (`?nocache=304`). Em uso normal, um reload resolve.

## Critério de aceite

- [x] Header/hint/status capitalizados no `--web` (validado via DOM).
- [x] Smoke + invariantes 14/14 + gauntlet 19/19.

---

*"O cuidado mora nas bordas da interface." -- anônimo*
