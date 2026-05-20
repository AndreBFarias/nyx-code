# SPRINT GAUNTLET-ACENTUACAO-FIX-01 -- 13 violações pré-existentes em nyx_gauntlet.py

## 0. SPEC

```yaml
sprint:
  id: GAUNTLET-ACENTUACAO-FIX-01
  title: "13 violações pré-existentes de acentuação em scripts/gauntlet/nyx_gauntlet.py"
  onda: 25
  bloco: 25.1 Resiliência do gauntlet (anti-débito de K08-VRAM-RUNNER-ISOLATION-01)
  prioridade: BAIXA
  tipo: Higiene de texto (PT-BR)
  dependencias: [RUFF-CLEAN-NYX-01]  # invariante #10 precisava estar verde
  desbloqueia: [GAUNTLET-TOOLS-DESC-MATCH-01, gauntlet completo gate v1.0]

  touches:
    - path: scripts/gauntlet/nyx_gauntlet.py
      reason: "Acentuar texto livre PT-BR + marcar identificadores técnicos com # noqa-acento"
      blocos:
        - "L116/237: chaves de dict PHASE_ALIASES/PHASE_TIMEOUTS (# noqa-acento)"
        - "L1222: comentário # FASE: SESSAO -> SESSÃO (caps acentuado, segue precedente L1442 RESILIÊNCIA)"
        - "L1238/1243/1259/1267/1281: parâmetro phase='sessao' em _add() (# noqa-acento)"
        - "L1128/1158/1336/1348: texto livre PT-BR (nao -> não)"

  creates: []
  removes: []

  forbidden:
    - "Mexer fora das 13 linhas listadas pelo validar-acentuacao.py"
    - "Mudar IDENTIFICADORES de fase para versão acentuada (quebra PHASE_ALIASES mapping)"
    - "Aplicar --fix automático cego (quebra identificadores)"

  tests:
    - cmd: "validar-acentuacao.py --paths scripts/gauntlet/nyx_gauntlet.py"
      deve_passar: "exit=0 (zero violações)"
    - cmd: "./run.sh --smoke"
      deve_passar: "boot ok"
    - cmd: "bash scripts/sprint_invariants.sh"
      deve_passar: "PASS 14, FAIL 0"
    - cmd: "./run.sh --gauntlet --only rapido"
      deve_passar: "sem regressão vs baseline"
```

---

**Status:** CONCLUIDA
**Data spec:** 2026-05-19 (segunda sessão)
**Data conclusão:** 2026-05-19 (segunda sessão, ~22h30; bloqueada por RUFF-CLEAN-NYX-01 entre 22:24 e 22:38)
**Modelo execução:** claude-opus-4-7

---

## Contexto

Anti-débito materializado durante execução de `K08-VRAM-RUNNER-ISOLATION-01` (2026-05-19). K08 introduziu 176L em `scripts/gauntlet/nyx_gauntlet.py` mas seu escopo autorizado de touches não incluía os blocos com violações pré-existentes. O validador externo `~/.config/zsh/scripts/validar-acentuacao.py` detectou 13 violações nas linhas L116/237/1128/1158/1222/1238/1243/1259/1267/1281/1336/1348.

## Análise por linha

| Linha | Texto original | Tipo | Tratamento |
|------:|---------------|------|-----------|
| 116   | `"sessao": ["sessao"],` | Identificador PHASE_ALIASES | `# noqa-acento` (manter ASCII clean como demais chaves) |
| 237   | `"sessao": 60,` | Identificador PHASE_TIMEOUTS | `# noqa-acento` |
| 1128  | `details="skip: docker nao instalado nesta maquina"` | Texto livre | nao -> não |
| 1158  | `"install.sh em ubuntu:22.04 (skip: daemon nao acessivel)"` | Texto livre | nao -> não |
| 1222  | `# FASE: SESSAO (3 testes -- SESSION-RESUME-01)` | Comentário CAPS | SESSAO -> SESSÃO (precedente L1442 RESILIÊNCIA) |
| 1238  | `self._add("S-01", "persistence imports", "sessao", ...)` | Param `phase` de `_add()` | `# noqa-acento` |
| 1243  | `"sessao",` (multi-line `_add`) | Param `phase` | `# noqa-acento` |
| 1259  | `self._add("S-02", "save_session + index", "sessao", ...)` | Param `phase` | `# noqa-acento` |
| 1267  | `"sessao",` (multi-line `_add`) | Param `phase` | `# noqa-acento` |
| 1281  | `"sessao",` (multi-line `_add`) | Param `phase` | `# noqa-acento` |
| 1336  | `details="skip: moondream nao instalado; ..."` | Texto livre | nao -> não |
| 1348  | `details=f"skip: {image_path} nao existe"` | Texto livre | nao -> não |

## Bloqueio temporário (RUFF-CLEAN-NYX-01)

Edits da ACENTUACAO aplicados às 22:24. Pós-validação revelou invariante #10 (ruff) FAIL — investigação mostrou 58 erros pré-existentes em `nyx/` introduzidos por upgrade silencioso de ruff 0.15.10 -> 0.15.13. Como protocolo do projeto exige 14/14 invariantes para fechar sprint, foi catalogada e executada `RUFF-CLEAN-NYX-01` (anti-débito derivado). Após sua conclusão (22:36), retornei a esta sprint para fechá-la formalmente.

## Proof-of-work runtime

- `validar-acentuacao.py --paths scripts/gauntlet/nyx_gauntlet.py` -> **exit 0** (era 13 violações)
- `./run.sh --smoke` -> `boot ok` antes e depois
- `bash scripts/sprint_invariants.sh` -> **PASS 14 / FAIL 0** (após RUFF-CLEAN-NYX-01 restaurar #10)
- `./run.sh --gauntlet --only rapido` -> 17/18 (P-07 pré-existente, zero regressão)
- `python3 -c "import ast; ast.parse(open('scripts/gauntlet/nyx_gauntlet.py').read())"` -> AST ok

## Não-objetivos (out-of-scope)

- Mudar `"sessao"` para `"sessão"` como identificador (quebra mapping interno; outras 25+ chaves de PHASE_ALIASES seguem ASCII clean — manter consistência).
- Tocar outras violações pré-existentes fora das 13 listadas.
- Renomear PERSISTENCIA -> PERSISTÊNCIA em L1656 (similar a SESSAO) — fora do escopo desta sprint, validar-acentuacao não pegou.

## Referências

- `~/.config/zsh/scripts/validar-acentuacao.py:94` — convenção `# noqa-acento`
- `scripts/gauntlet/nyx_gauntlet.py:1442` — precedente `# FASE: RESILIÊNCIA` (caps acentuado)
- `nyx/agent/lang_check.py:29-40` — outro consumidor de `# noqa-acento`
- `feedback_nenhum_debito.md` — protocolo anti-débito

---

*"Higiene de texto exige distinguir identificador técnico de mensagem ao humano." -- GAUNTLET-ACENTUACAO-FIX-01*
